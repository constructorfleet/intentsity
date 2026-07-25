"""Wake-word capture manager: audio in, labeled clips out.

Owns the per-assistant rolling buffers, the UDP receiver, the MQTT
subscriptions, and clip persistence. Audio handling stays on the event loop;
only WAV writing and database work go to the executor.
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
import voluptuous as vol

from . import db
from .audio import (
    MultiAssistantAudioBuffer,
    clip_filename,
    compute_peaks,
    write_wav,
)
from .const import (
    CONF_BUFFER_DURATION,
    CONF_CHANNELS,
    CONF_MQTT_AUDIO_INFO_TOPIC,
    CONF_MQTT_AUDIO_TOPIC,
    CONF_MQTT_ENABLED,
    CONF_MQTT_EVENT_TOPIC,
    CONF_POST_WAKE_DURATION,
    CONF_PRE_WAKE_DURATION,
    CONF_RETENTION_DAYS,
    CONF_SAMPLE_RATE,
    CONF_SAMPLE_WIDTH,
    CONF_UDP_ASSISTANT_ID,
    CONF_UDP_ENABLED,
    CONF_UDP_PORT,
    DEFAULT_BUFFER_DURATION,
    DEFAULT_CHANNELS,
    DEFAULT_MQTT_AUDIO_INFO_TOPIC,
    DEFAULT_MQTT_AUDIO_TOPIC,
    DEFAULT_MQTT_EVENT_TOPIC,
    DEFAULT_POST_WAKE_DURATION,
    DEFAULT_PRE_WAKE_DURATION,
    DEFAULT_RETENTION_DAYS,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_SAMPLE_WIDTH,
    DEFAULT_UDP_PORT,
    LABEL_BACKGROUND_NOISE,
    LABEL_UNLABELED,
    SIGNAL_CLIP_RECORDED,
)
from .models import (
    AudioFormat,
    AudioInfoMessage,
    Clip,
    WakeEvent,
)
from .udp import UDPAudioReceiver

_LOGGER = logging.getLogger(__name__)


def _topic_assistant_id(topic: str, pattern: str) -> str | None:
    """Extract the assistant ID that matched a single-level `+` wildcard."""
    topic_parts = topic.split("/")
    pattern_parts = pattern.split("/")
    if len(topic_parts) != len(pattern_parts):
        return None
    for topic_part, pattern_part in zip(topic_parts, pattern_parts, strict=True):
        if pattern_part == "+":
            return topic_part
        if pattern_part == "#":
            return topic_part
        if pattern_part != topic_part:
            return None
    return None


class CaptureManager:
    """Coordinates wake-word audio ingest and clip extraction."""

    def __init__(self, hass: HomeAssistant, options: dict) -> None:
        self.hass = hass
        self._options = options
        self._unsubscribes: list = []
        self._receiver: UDPAudioReceiver | None = None
        self.mqtt_connected = False

        self.buffers = MultiAssistantAudioBuffer(
            default_format=AudioFormat(
                sample_rate=options.get(CONF_SAMPLE_RATE, DEFAULT_SAMPLE_RATE),
                sample_width=options.get(CONF_SAMPLE_WIDTH, DEFAULT_SAMPLE_WIDTH),
                channels=options.get(CONF_CHANNELS, DEFAULT_CHANNELS),
            ),
            buffer_duration=options.get(CONF_BUFFER_DURATION, DEFAULT_BUFFER_DURATION),
        )

    # --- Options ----------------------------------------------------------

    @property
    def udp_port(self) -> int:
        return int(self._options.get(CONF_UDP_PORT, DEFAULT_UDP_PORT))

    @property
    def udp_running(self) -> bool:
        return self._receiver is not None and self._receiver.running

    @property
    def pre_duration(self) -> float:
        return float(self._options.get(CONF_PRE_WAKE_DURATION, DEFAULT_PRE_WAKE_DURATION))

    @property
    def post_duration(self) -> float:
        return float(self._options.get(CONF_POST_WAKE_DURATION, DEFAULT_POST_WAKE_DURATION))

    @property
    def retention_days(self) -> int:
        return int(self._options.get(CONF_RETENTION_DAYS, DEFAULT_RETENTION_DAYS))

    # --- Lifecycle --------------------------------------------------------

    async def async_start(self) -> None:
        if self._options.get(CONF_UDP_ENABLED, True):
            self._receiver = UDPAudioReceiver(
                port=self.udp_port,
                audio_callback=self._handle_audio,
                assistant_id=self._options.get(CONF_UDP_ASSISTANT_ID) or None,
            )
            if not await self._receiver.async_start():
                self._receiver = None

        if self._options.get(CONF_MQTT_ENABLED, True):
            await self._async_subscribe_mqtt()

    async def async_stop(self) -> None:
        for unsubscribe in self._unsubscribes:
            unsubscribe()
        self._unsubscribes.clear()
        if self._receiver is not None:
            self._receiver.stop()
            self._receiver = None
        self.mqtt_connected = False

    async def _async_subscribe_mqtt(self) -> None:
        """Subscribe through the mqtt integration, if the user has one set up."""
        try:
            from homeassistant.components import mqtt
        except ImportError:
            return
        if not await mqtt.async_wait_for_mqtt_client(self.hass):
            _LOGGER.debug("MQTT client unavailable; Intentsity is UDP-only")
            return

        audio_topic = self._options.get(CONF_MQTT_AUDIO_TOPIC, DEFAULT_MQTT_AUDIO_TOPIC)
        event_topic = self._options.get(CONF_MQTT_EVENT_TOPIC, DEFAULT_MQTT_EVENT_TOPIC)
        info_topic = self._options.get(CONF_MQTT_AUDIO_INFO_TOPIC, DEFAULT_MQTT_AUDIO_INFO_TOPIC)

        self._unsubscribes.append(
            await mqtt.async_subscribe(
                self.hass,
                audio_topic,
                self._make_mqtt_handler(audio_topic, self._handle_mqtt_audio),
                encoding=None,
            )
        )
        self._unsubscribes.append(
            await mqtt.async_subscribe(
                self.hass,
                event_topic,
                self._make_mqtt_handler(event_topic, self._handle_mqtt_event),
            )
        )
        self._unsubscribes.append(
            await mqtt.async_subscribe(
                self.hass,
                info_topic,
                self._make_mqtt_handler(info_topic, self._handle_mqtt_audio_info),
            )
        )
        self.mqtt_connected = True
        _LOGGER.info(
            "Intentsity subscribed to MQTT topics %s, %s, %s",
            audio_topic,
            event_topic,
            info_topic,
        )

    def _make_mqtt_handler(self, pattern: str, handler):
        @callback
        def _handle(message) -> None:
            assistant_id = _topic_assistant_id(message.topic, pattern)
            if assistant_id is None:
                _LOGGER.debug(
                    "Could not derive assistant ID from topic %s using %s",
                    message.topic,
                    pattern,
                )
                return
            try:
                handler(assistant_id, message.payload)
            except Exception:
                _LOGGER.exception("Error handling MQTT message on %s", message.topic)

        return _handle

    # --- Audio in ---------------------------------------------------------

    @callback
    def _handle_audio(
        self,
        assistant_id: str,
        pcm: bytes,
        audio_format: AudioFormat | None = None,
    ) -> None:
        self.buffers.append(assistant_id, pcm, audio_format)

    @callback
    def _handle_mqtt_audio(self, assistant_id: str, payload) -> None:
        """Accept raw PCM bytes, or base64 text from the ESPHome MQTT path."""
        if isinstance(payload, str):
            try:
                pcm = base64.b64decode(payload, validate=True)
            except (ValueError, TypeError):
                _LOGGER.debug("Discarding non-base64 audio payload for %s", assistant_id)
                return
        else:
            pcm = payload
        self._handle_audio(assistant_id, pcm)

    @callback
    def _handle_mqtt_audio_info(self, assistant_id: str, payload) -> None:
        import json

        if isinstance(payload, bytes):
            payload = payload.decode("utf-8", errors="replace")
        try:
            info = AudioInfoMessage.model_validate(json.loads(payload))
        except (ValueError, vol.Invalid) as exc:
            _LOGGER.warning("Invalid audio_info payload for %s: %s", assistant_id, exc)
            return
        self.buffers.set_format(assistant_id, info.to_format())

    @callback
    def _handle_mqtt_event(self, assistant_id: str, payload) -> None:
        import json

        if isinstance(payload, bytes):
            payload = payload.decode("utf-8", errors="replace")
        try:
            data = json.loads(payload)
        except ValueError:
            _LOGGER.warning("Invalid wake event payload for %s", assistant_id)
            return
        if not isinstance(data, dict):
            return
        # ESPHome's example config publishes {"event": "wake", ...}; anything else
        # on this topic is not a detection.
        if data.get("event") not in (None, "wake"):
            return
        event = WakeEvent(
            assistant_id=assistant_id,
            wake_word=data.get("wake_word") or data.get("model"),
            model=data.get("model"),
            confidence=data.get("confidence"),
            data=data,
        )
        # A device may report format alongside the event; honor it before capture.
        if {"rate", "bits", "channels"} <= data.keys():
            try:
                self.buffers.set_format(
                    assistant_id,
                    AudioInfoMessage(
                        sample_rate=int(data["rate"]),
                        bits_per_sample=int(data["bits"]),
                        channels=int(data["channels"]),
                    ).to_format(),
                )
            except (ValueError, TypeError) as exc:
                _LOGGER.debug("Ignoring bad format in wake event for %s: %s", assistant_id, exc)
        self.hass.async_create_task(self.async_capture_wake_event(event))

    # --- Clip capture -----------------------------------------------------

    async def async_capture_wake_event(self, event: WakeEvent) -> Clip | None:
        """Wait out the post-roll, then persist the surrounding audio as a clip."""
        import asyncio

        assistant_id = event.assistant_id
        pre_duration = event.pre_duration or self.pre_duration
        post_duration = (
            event.post_duration if event.post_duration is not None else self.post_duration
        )

        buffer = self.buffers.get(assistant_id)
        if buffer is None:
            _LOGGER.warning("No audio received yet for assistant %s", assistant_id)
            return None

        if post_duration > 0:
            await asyncio.sleep(post_duration)
            buffer = self.buffers.get(assistant_id)
            if buffer is None:
                return None

        samples = buffer.extract(
            pre_duration=pre_duration,
            post_duration=post_duration,
            # The wait above means the detection is now post_duration in the past.
            trigger_offset=post_duration,
        )
        if samples.shape[0] == 0:
            _LOGGER.warning("Insufficient buffered audio for assistant %s", assistant_id)
            return None

        return await self._async_persist_clip(
            assistant_id=assistant_id,
            samples=samples,
            audio_format=buffer.audio_format,
            label=event.label,
            wake_word=event.wake_word,
            confidence=event.confidence,
            extra={
                "pre_duration": pre_duration,
                "post_duration": post_duration,
                "wake_metadata": event.data,
            },
        )

    async def async_capture_noise(self, assistant_id: str, seconds: float) -> Clip | None:
        """Persist the trailing buffer as a background-noise clip."""
        buffer = self.buffers.get(assistant_id)
        if buffer is None:
            _LOGGER.warning("No audio received yet for assistant %s", assistant_id)
            return None
        samples = buffer.tail(seconds)
        if samples.shape[0] == 0:
            return None
        return await self._async_persist_clip(
            assistant_id=assistant_id,
            samples=samples,
            audio_format=buffer.audio_format,
            label=LABEL_BACKGROUND_NOISE,
            wake_word=None,
            confidence=None,
            extra={"capture": "background_noise", "requested_seconds": seconds},
        )

    async def _async_persist_clip(
        self,
        *,
        assistant_id: str,
        samples,
        audio_format: AudioFormat,
        label: str,
        wake_word: str | None,
        confidence: float | None,
        extra: dict,
    ) -> Clip | None:
        timestamp = datetime.now(UTC)
        filename = clip_filename(timestamp, assistant_id)
        frames = int(samples.shape[0])
        duration = frames / audio_format.sample_rate

        clip = Clip(
            filename=filename,
            timestamp=timestamp,
            label=label or LABEL_UNLABELED,
            assistant_id=assistant_id,
            wake_word=wake_word,
            confidence=confidence,
            duration=round(duration, 4),
            sample_rate=audio_format.sample_rate,
            sample_width=audio_format.sample_width,
            channels=audio_format.channels,
            peaks=compute_peaks(samples),
            data=extra,
        )

        metadata = clip.model_dump(mode="json", exclude={"id", "peaks", "deleted_at"})
        metadata["frames"] = frames

        def _write() -> int:
            write_wav(
                db.get_clips_dir(self.hass) / filename,
                samples,
                audio_format,
                metadata,
            )
            return db.insert_clip(self.hass, clip)

        try:
            clip.id = await self.hass.async_add_executor_job(_write)
        except OSError as exc:
            _LOGGER.error("Failed to write clip %s: %s", filename, exc)
            return None

        _LOGGER.info(
            "Captured clip %s for %s (%.2fs, %s Hz)",
            filename,
            assistant_id,
            duration,
            audio_format.sample_rate,
        )
        async_dispatcher_send(self.hass, SIGNAL_CLIP_RECORDED)
        return clip

    # --- Maintenance ------------------------------------------------------

    async def async_prune(self) -> int:
        """Delete clips past the retention window, if one is configured."""
        if self.retention_days <= 0:
            return 0
        removed = await self.hass.async_add_executor_job(
            db.prune_clips, self.hass, self.retention_days
        )
        if removed:
            _LOGGER.info("Pruned %s clips older than %s days", removed, self.retention_days)
            async_dispatcher_send(self.hass, SIGNAL_CLIP_RECORDED)
        return removed

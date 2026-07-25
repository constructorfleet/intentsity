"""The capture manager: audio in, labeled clips out."""

from __future__ import annotations

import asyncio
import base64
import builtins
from datetime import UTC, datetime, timedelta
import json
import logging
import socket
from typing import Any
from unittest.mock import AsyncMock, patch
import wave

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
import numpy as np
import pytest

from custom_components.intentsity import db
from custom_components.intentsity.capture import CaptureManager, _topic_assistant_id
from custom_components.intentsity.config_flow import DEFAULT_OPTIONS
from custom_components.intentsity.const import (
    CONF_MQTT_ENABLED,
    CONF_POST_WAKE_DURATION,
    CONF_PRE_WAKE_DURATION,
    CONF_RETENTION_DAYS,
    CONF_SAMPLE_RATE,
    CONF_UDP_ASSISTANT_ID,
    CONF_UDP_ENABLED,
    CONF_UDP_PORT,
    LABEL_BACKGROUND_NOISE,
    LABEL_TRUE_POSITIVE,
    SIGNAL_CLIP_RECORDED,
)
from custom_components.intentsity.models import AudioFormat, ClipListRequest, WakeEvent
from custom_components.intentsity.udp import encode_udp_audio_packet

LOGGER_NAME = "custom_components.intentsity.capture"


def _options(**overrides: Any) -> dict:
    """Default options with both transports off, so tests opt in explicitly."""
    options = dict(DEFAULT_OPTIONS)
    options[CONF_UDP_ENABLED] = False
    options[CONF_MQTT_ENABLED] = False
    # Waiting out a real 3s post-roll in every capture test is not worth it; the
    # tests that care about the wait set it back.
    options[CONF_POST_WAKE_DURATION] = 0.0
    options.update(overrides)
    return options


def _pcm(seconds: float, sample_rate: int = 16000) -> bytes:
    """Deterministic 16-bit mono PCM, loud enough for a non-flat envelope."""
    frames = int(seconds * sample_rate)
    return (np.arange(frames) % 4096).astype("<i2").tobytes()


def _all_clips(hass: HomeAssistant):
    return db.fetch_clips_page(hass, ClipListRequest(limit=50))


@pytest.fixture
def manager(hass: HomeAssistant, clean_db: None) -> CaptureManager:
    return CaptureManager(hass, _options())


# --- Topic parsing ---------------------------------------------------------


@pytest.mark.parametrize(
    ("topic", "pattern", "expected"),
    [
        ("assist/debug/kitchen/pcm", "assist/debug/+/pcm", "kitchen"),
        ("assist/debug/kitchen/pcm", "assist/debug/#/x", "kitchen"),
        ("assist/debug/kitchen/pcm", "assist/other/+/pcm", None),
        ("assist/debug/kitchen", "assist/debug/+/pcm", None),
        ("assist/debug/kitchen/pcm", "assist/debug/kitchen/pcm", None),
    ],
)
def test_topic_assistant_id(topic: str, pattern: str, expected: str | None) -> None:
    assert _topic_assistant_id(topic, pattern) == expected


# --- Options ---------------------------------------------------------------


def test_manager_reads_options(hass: HomeAssistant, clean_db: None) -> None:
    manager = CaptureManager(
        hass,
        _options(
            **{
                CONF_UDP_PORT: 7000,
                CONF_PRE_WAKE_DURATION: 1.5,
                CONF_POST_WAKE_DURATION: 0.5,
                CONF_RETENTION_DAYS: 14,
            }
        ),
    )
    assert manager.udp_port == 7000
    assert manager.pre_duration == 1.5
    assert manager.post_duration == 0.5
    assert manager.retention_days == 14
    assert manager.udp_running is False
    assert manager.mqtt_connected is False


def test_manager_falls_back_to_defaults(hass: HomeAssistant, clean_db: None) -> None:
    manager = CaptureManager(hass, {})
    assert manager.udp_port == 6056
    assert manager.pre_duration == 2.0
    assert manager.post_duration == 3.0
    assert manager.retention_days == 0
    assert manager.buffers.format_for("anyone").sample_rate == 16000


# --- Lifecycle -------------------------------------------------------------


async def test_start_binds_udp(hass: HomeAssistant, clean_db: None, socket_enabled: None) -> None:
    manager = CaptureManager(hass, _options(**{CONF_UDP_ENABLED: True, CONF_UDP_PORT: 0}))
    await manager.async_start()
    try:
        assert manager.udp_running is True
    finally:
        await manager.async_stop()
    assert manager.udp_running is False


async def test_start_drops_receiver_when_bind_fails(hass: HomeAssistant, clean_db: None) -> None:
    manager = CaptureManager(hass, _options(**{CONF_UDP_ENABLED: True}))
    with patch(
        "custom_components.intentsity.capture.UDPAudioReceiver.async_start",
        AsyncMock(return_value=False),
    ):
        await manager.async_start()
    assert manager.udp_running is False


async def test_start_passes_configured_assistant_id(hass: HomeAssistant, clean_db: None) -> None:
    manager = CaptureManager(
        hass,
        _options(**{CONF_UDP_ENABLED: True, CONF_UDP_PORT: 0, CONF_UDP_ASSISTANT_ID: "only-one"}),
    )
    with patch(
        "custom_components.intentsity.capture.UDPAudioReceiver.async_start",
        AsyncMock(return_value=True),
    ):
        await manager.async_start()
    assert manager._receiver.assistant_id == "only-one"


async def test_start_subscribes_and_unsubscribes_mqtt(hass: HomeAssistant, clean_db: None) -> None:
    manager = CaptureManager(hass, _options(**{CONF_MQTT_ENABLED: True}))
    subscribed: list[str] = []
    unsubscribed: list[str] = []

    async def _subscribe(_hass, topic, _handler, **_kwargs):
        subscribed.append(topic)
        return lambda: unsubscribed.append(topic)

    with (
        patch(
            "homeassistant.components.mqtt.async_wait_for_mqtt_client",
            AsyncMock(return_value=True),
        ),
        patch("homeassistant.components.mqtt.async_subscribe", _subscribe),
    ):
        await manager.async_start()

    assert manager.mqtt_connected is True
    assert subscribed == [
        "assist/debug/+/pcm",
        "assist/debug/+/events",
        "assist/debug/+/audio_info",
    ]

    await manager.async_stop()
    assert unsubscribed == subscribed
    assert manager.mqtt_connected is False


async def test_start_tolerates_missing_mqtt_client(hass: HomeAssistant, clean_db: None) -> None:
    manager = CaptureManager(hass, _options(**{CONF_MQTT_ENABLED: True}))
    with patch(
        "homeassistant.components.mqtt.async_wait_for_mqtt_client",
        AsyncMock(return_value=False),
    ):
        await manager.async_start()

    assert manager.mqtt_connected is False


async def test_start_tolerates_a_build_without_mqtt(hass: HomeAssistant, clean_db: None) -> None:
    """A Home Assistant install without the mqtt integration still starts up."""
    manager = CaptureManager(hass, _options(**{CONF_MQTT_ENABLED: True}))
    real_import = builtins.__import__

    def _import(name: str, *args: Any, **kwargs: Any):
        if name == "homeassistant.components" and "mqtt" in (args[2] if len(args) > 2 else ()):
            raise ImportError("No module named 'homeassistant.components.mqtt'")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", _import):
        await manager.async_start()

    assert manager.mqtt_connected is False


async def test_stop_is_safe_without_start(manager: CaptureManager) -> None:
    await manager.async_stop()
    assert manager.udp_running is False


# --- Audio in --------------------------------------------------------------


def test_handle_audio_buffers_per_assistant(manager: CaptureManager) -> None:
    manager._handle_audio("kitchen", _pcm(0.1))
    manager._handle_audio("office", _pcm(0.2))
    assert manager.buffers.get("kitchen").frame_count == 1600
    assert manager.buffers.get("office").frame_count == 3200


def test_handle_mqtt_audio_accepts_raw_and_base64(manager: CaptureManager) -> None:
    manager._handle_mqtt_audio("kitchen", _pcm(0.1))
    manager._handle_mqtt_audio("office", base64.b64encode(_pcm(0.1)).decode())

    assert manager.buffers.get("kitchen").frame_count == 1600
    assert manager.buffers.get("office").frame_count == 1600


def test_handle_mqtt_audio_rejects_non_base64_text(manager: CaptureManager) -> None:
    manager._handle_mqtt_audio("kitchen", "definitely not base64 !!!")
    assert manager.buffers.get("kitchen") is None


def test_handle_mqtt_audio_info_sets_format(manager: CaptureManager) -> None:
    manager._handle_mqtt_audio_info(
        "kitchen",
        json.dumps({"sample_rate": 48000, "bits_per_sample": 32, "channels": 2}).encode(),
    )
    audio_format = manager.buffers.format_for("kitchen")
    assert (audio_format.sample_rate, audio_format.sample_width, audio_format.channels) == (
        48000,
        4,
        2,
    )


def test_handle_mqtt_audio_info_rejects_bad_payloads(
    manager: CaptureManager, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
        manager._handle_mqtt_audio_info("kitchen", "{not json")
        manager._handle_mqtt_audio_info(
            "kitchen", json.dumps({"sample_rate": 0, "bits_per_sample": 16, "channels": 1})
        )

    assert caplog.text.count("Invalid audio_info payload") == 2
    assert manager.buffers.format_for("kitchen").sample_rate == 16000


def test_mqtt_handler_derives_assistant_from_topic(manager: CaptureManager) -> None:
    seen: list[tuple] = []
    handler = manager._make_mqtt_handler("assist/debug/+/pcm", lambda *args: seen.append(args))

    class _Message:
        topic = "assist/debug/kitchen/pcm"
        payload = b"\x00\x01"

    handler(_Message())
    assert seen == [("kitchen", b"\x00\x01")]


def test_mqtt_handler_skips_unmatched_topic(manager: CaptureManager) -> None:
    seen: list[tuple] = []
    handler = manager._make_mqtt_handler("assist/debug/+/pcm", lambda *args: seen.append(args))

    class _Message:
        topic = "totally/other"
        payload = b""

    handler(_Message())
    assert seen == []


def test_mqtt_handler_logs_handler_errors(
    manager: CaptureManager, caplog: pytest.LogCaptureFixture
) -> None:
    def _boom(*_args) -> None:
        raise RuntimeError("nope")

    handler = manager._make_mqtt_handler("assist/debug/+/pcm", _boom)

    class _Message:
        topic = "assist/debug/kitchen/pcm"
        payload = b""

    with caplog.at_level(logging.ERROR, logger=LOGGER_NAME):
        handler(_Message())
    assert "Error handling MQTT message" in caplog.text


async def test_udp_datagram_reaches_the_buffer(
    hass: HomeAssistant, clean_db: None, socket_enabled: None
) -> None:
    """End to end over a real socket: a WWD2 datagram lands in the right buffer."""
    manager = CaptureManager(hass, _options(**{CONF_UDP_ENABLED: True, CONF_UDP_PORT: 0}))
    await manager.async_start()
    port = manager._receiver._transport.get_extra_info("socket").getsockname()[1]

    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sender.sendto(
            encode_udp_audio_packet("kitchen", _pcm(0.05), sample_rate=16000),
            ("127.0.0.1", port),
        )
        for _ in range(100):
            await asyncio.sleep(0.01)
            if manager.buffers.get("kitchen") is not None:
                break
    finally:
        sender.close()
        await manager.async_stop()

    assert manager.buffers.get("kitchen").frame_count == 800


# --- Wake events -----------------------------------------------------------


async def test_handle_mqtt_event_captures_a_clip(manager: CaptureManager) -> None:
    manager._handle_audio("kitchen", _pcm(5.0))
    manager._handle_mqtt_event(
        "kitchen",
        json.dumps(
            {
                "event": "wake",
                "wake_word": "okay_nabu",
                "model": "okay_nabu_v2",
                "confidence": 0.88,
                "rate": 16000,
                "bits": 16,
                "channels": 1,
            }
        ),
    )
    await manager.hass.async_block_till_done()

    clips = _all_clips(manager.hass).clips
    assert len(clips) == 1
    assert clips[0].wake_word == "okay_nabu"
    assert clips[0].confidence == 0.88
    assert clips[0].data["wake_metadata"]["model"] == "okay_nabu_v2"


async def test_handle_mqtt_event_falls_back_to_model_name(manager: CaptureManager) -> None:
    manager._handle_audio("kitchen", _pcm(5.0))
    manager._handle_mqtt_event("kitchen", json.dumps({"event": "wake", "model": "hey_jarvis"}))
    await manager.hass.async_block_till_done()

    assert _all_clips(manager.hass).clips[0].wake_word == "hey_jarvis"


async def test_handle_mqtt_event_ignores_other_event_types(manager: CaptureManager) -> None:
    manager._handle_audio("kitchen", _pcm(1.0))
    manager._handle_mqtt_event("kitchen", json.dumps({"event": "heartbeat"}))
    await manager.hass.async_block_till_done()

    assert _all_clips(manager.hass).total == 0


async def test_handle_mqtt_event_rejects_bad_payloads(
    manager: CaptureManager, caplog: pytest.LogCaptureFixture
) -> None:
    manager._handle_audio("kitchen", _pcm(1.0))
    with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
        manager._handle_mqtt_event("kitchen", "{not json")
    assert "Invalid wake event payload" in caplog.text

    # Valid JSON, but an array is not an event.
    manager._handle_mqtt_event("kitchen", b"[1, 2]")
    await manager.hass.async_block_till_done()
    assert _all_clips(manager.hass).total == 0


async def test_handle_mqtt_event_ignores_bad_inline_format(
    manager: CaptureManager, caplog: pytest.LogCaptureFixture
) -> None:
    manager._handle_audio("kitchen", _pcm(1.0))
    with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
        manager._handle_mqtt_event(
            "kitchen",
            json.dumps({"event": "wake", "rate": "fast", "bits": 16, "channels": 1}),
        )
        await manager.hass.async_block_till_done()

    assert "Ignoring bad format in wake event" in caplog.text
    # The buffer keeps the format it already had, so the clip is still written.
    assert manager.buffers.format_for("kitchen").sample_rate == 16000
    assert _all_clips(manager.hass).total == 1


async def test_handle_mqtt_event_adopts_inline_format(manager: CaptureManager) -> None:
    manager._handle_mqtt_event(
        "kitchen", json.dumps({"event": "wake", "rate": 48000, "bits": 32, "channels": 2})
    )
    await manager.hass.async_block_till_done()

    audio_format = manager.buffers.format_for("kitchen")
    assert (audio_format.sample_rate, audio_format.sample_width, audio_format.channels) == (
        48000,
        4,
        2,
    )


async def test_capture_wake_event_writes_wav_row_and_signal(
    manager: CaptureManager, hass: HomeAssistant
) -> None:
    manager._handle_audio("kitchen", _pcm(6.0))
    signals: list[tuple] = []
    async_dispatcher_connect(hass, SIGNAL_CLIP_RECORDED, lambda *args: signals.append(args))

    clip = await manager.async_capture_wake_event(
        WakeEvent(assistant_id="kitchen", wake_word="okay_nabu", pre_duration=2, post_duration=0)
    )
    await hass.async_block_till_done()

    assert clip is not None
    assert clip.id is not None
    assert clip.duration == pytest.approx(2.0)
    assert clip.sample_rate == 16000
    assert len(clip.peaks) == 96
    assert signals == [()]

    path = db.get_clips_dir(hass) / clip.filename
    with wave.open(str(path), "rb") as handle:
        assert handle.getnframes() == 32000
        assert handle.getframerate() == 16000
    metadata = json.loads(path.with_suffix(".json").read_text())
    assert metadata["frames"] == 32000
    assert metadata["wake_word"] == "okay_nabu"
    # The envelope belongs in the database, not in the sidecar.
    assert "peaks" not in metadata

    stored = db.fetch_clip(hass, clip.id)
    assert stored is not None
    assert stored.data["pre_duration"] == 2
    assert stored.data["post_duration"] == 0


async def test_capture_wake_event_waits_out_the_post_roll(manager: CaptureManager) -> None:
    manager._handle_audio("kitchen", _pcm(6.0))
    sleeps: list[float] = []

    async def _sleep(seconds: float) -> None:
        sleeps.append(seconds)

    with patch("asyncio.sleep", _sleep):
        clip = await manager.async_capture_wake_event(
            WakeEvent(assistant_id="kitchen", pre_duration=1, post_duration=2)
        )

    assert sleeps == [2]
    assert clip is not None
    # 1s before the trigger, which the wait left 2s back from the newest frame.
    assert clip.duration == pytest.approx(3.0)


async def test_capture_wake_event_without_audio(
    manager: CaptureManager, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
        assert await manager.async_capture_wake_event(WakeEvent(assistant_id="ghost")) is None
    assert "No audio received yet" in caplog.text


async def test_capture_wake_event_with_an_empty_window(
    manager: CaptureManager, caplog: pytest.LogCaptureFixture
) -> None:
    """A format change during the post-roll clears the buffer, so there is nothing to save."""
    manager._handle_audio("kitchen", _pcm(3.0))

    async def _sleep(_seconds: float) -> None:
        manager.buffers.set_format(
            "kitchen", AudioFormat(sample_rate=48000, sample_width=2, channels=1)
        )

    with patch("asyncio.sleep", _sleep), caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
        clip = await manager.async_capture_wake_event(
            WakeEvent(assistant_id="kitchen", pre_duration=1, post_duration=1)
        )

    assert clip is None
    assert "Insufficient buffered audio" in caplog.text


async def test_capture_wake_event_bails_if_buffer_vanishes(manager: CaptureManager) -> None:
    """A reload between the detection and the end of the post-roll drops the clip."""
    manager._handle_audio("kitchen", _pcm(3.0))

    async def _sleep(_seconds: float) -> None:
        manager.buffers._buffers.clear()

    with patch("asyncio.sleep", _sleep):
        clip = await manager.async_capture_wake_event(
            WakeEvent(assistant_id="kitchen", post_duration=1)
        )

    assert clip is None


async def test_capture_wake_event_uses_configured_durations(
    hass: HomeAssistant, clean_db: None
) -> None:
    manager = CaptureManager(
        hass, _options(**{CONF_PRE_WAKE_DURATION: 1.0, CONF_POST_WAKE_DURATION: 0.0})
    )
    manager._handle_audio("kitchen", _pcm(6.0))

    clip = await manager.async_capture_wake_event(WakeEvent(assistant_id="kitchen"))
    assert clip is not None
    assert clip.duration == pytest.approx(1.0)


async def test_capture_wake_event_keeps_a_preset_label(manager: CaptureManager) -> None:
    manager._handle_audio("kitchen", _pcm(3.0))
    clip = await manager.async_capture_wake_event(
        WakeEvent(assistant_id="kitchen", label=LABEL_TRUE_POSITIVE)
    )
    assert clip is not None
    assert clip.label == LABEL_TRUE_POSITIVE


async def test_capture_wake_event_honors_a_device_format(
    hass: HomeAssistant, clean_db: None
) -> None:
    manager = CaptureManager(hass, _options(**{CONF_SAMPLE_RATE: 48000}))
    manager._handle_audio("kitchen", _pcm(2.0, sample_rate=48000))

    clip = await manager.async_capture_wake_event(WakeEvent(assistant_id="kitchen", pre_duration=1))
    assert clip is not None
    assert clip.sample_rate == 48000
    assert clip.duration == pytest.approx(1.0)


async def test_capture_wake_event_reports_a_write_failure(
    manager: CaptureManager, caplog: pytest.LogCaptureFixture
) -> None:
    manager._handle_audio("kitchen", _pcm(3.0))
    with (
        patch(
            "custom_components.intentsity.capture.write_wav",
            side_effect=OSError("disk full"),
        ),
        caplog.at_level(logging.ERROR, logger=LOGGER_NAME),
    ):
        clip = await manager.async_capture_wake_event(WakeEvent(assistant_id="kitchen"))

    assert clip is None
    assert "Failed to write clip" in caplog.text
    assert _all_clips(manager.hass).total == 0


# --- Noise capture ---------------------------------------------------------


async def test_capture_noise(manager: CaptureManager, hass: HomeAssistant) -> None:
    manager._handle_audio("kitchen", _pcm(6.0))
    clip = await manager.async_capture_noise("kitchen", 3.0)

    assert clip is not None
    assert clip.label == LABEL_BACKGROUND_NOISE
    assert clip.duration == pytest.approx(3.0)
    assert clip.wake_word is None
    assert db.fetch_clip(hass, clip.id).data == {
        "capture": "background_noise",
        "requested_seconds": 3.0,
    }


async def test_capture_noise_without_audio(
    manager: CaptureManager, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
        assert await manager.async_capture_noise("ghost", 3.0) is None
    assert "No audio received yet" in caplog.text


async def test_capture_noise_with_an_empty_buffer(manager: CaptureManager) -> None:
    manager.buffers.ensure("kitchen")
    assert await manager.async_capture_noise("kitchen", 3.0) is None


# --- Maintenance ----------------------------------------------------------


async def test_prune_is_disabled_by_default(manager: CaptureManager, add_clip) -> None:
    add_clip(timestamp=datetime.now(UTC) - timedelta(days=365))
    assert await manager.async_prune() == 0
    assert _all_clips(manager.hass).total == 1


async def test_prune_removes_clips_past_retention(
    hass: HomeAssistant, add_clip, caplog: pytest.LogCaptureFixture
) -> None:
    manager = CaptureManager(hass, _options(**{CONF_RETENTION_DAYS: 7}))
    add_clip(filename="old.wav", timestamp=datetime.now(UTC) - timedelta(days=30))
    add_clip(filename="new.wav", timestamp=datetime.now(UTC))

    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        assert await manager.async_prune() == 1
    assert "Pruned 1 clips" in caplog.text
    assert [clip.filename for clip in _all_clips(hass).clips] == ["new.wav"]


async def test_prune_with_nothing_to_remove(hass: HomeAssistant, add_clip) -> None:
    manager = CaptureManager(hass, _options(**{CONF_RETENTION_DAYS: 7}))
    add_clip(timestamp=datetime.now(UTC))
    assert await manager.async_prune() == 0

"""UDP ingest for the satellite1 `wake_audio_stream` component.

Three packet shapes are accepted, in descending preference:

* **WWD2** — magic, a fixed header carrying assistant-ID length, channels, bits
  per sample, encoding, sample rate, sequence, and payload length; then the
  ASCII assistant ID and PCM. Multi-byte fields are network byte order. This is
  the only shape that survives a UDP proxy with both identity and format intact.
* **WWD1** — assistant-ID framing without format metadata; the configured
  fallback format applies.
* **Raw PCM** — no framing at all; the sender's IP becomes the assistant ID,
  which only distinguishes devices that connect directly.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import logging
import re
import struct

from .models import AudioFormat

_LOGGER = logging.getLogger(__name__)

UDP_PACKET_V1_MAGIC = b"WWD1"
UDP_PACKET_MAGIC = b"WWD2"
UDP_AUDIO_ENCODING_PCM_SIGNED_LE = 1
UDP_PACKET_FIXED_HEADER = struct.Struct("!4sBBBBIIH")
MAX_ASSISTANT_ID_BYTES = 64
ASSISTANT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")

AudioCallback = Callable[[str, bytes, AudioFormat | None], None]


def encode_udp_audio_packet(
    assistant_id: str,
    pcm_data: bytes,
    *,
    sample_rate: int = 16000,
    bits_per_sample: int = 16,
    channels: int = 1,
    encoding: int = UDP_AUDIO_ENCODING_PCM_SIGNED_LE,
    sequence: int = 0,
) -> bytes:
    """Frame PCM and its format so it survives UDP proxies such as Traefik."""
    try:
        encoded_id = assistant_id.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("assistant_id must be ASCII") from exc
    if not 1 <= len(encoded_id) <= MAX_ASSISTANT_ID_BYTES:
        raise ValueError("assistant_id must contain 1 to 64 ASCII bytes")
    if ASSISTANT_ID_PATTERN.fullmatch(assistant_id) is None:
        raise ValueError(
            "assistant_id must start with an alphanumeric character and contain "
            "only letters, numbers, underscores, periods, or hyphens"
        )
    if not pcm_data:
        raise ValueError("pcm_data must not be empty")
    if not 1 <= channels <= 255:
        raise ValueError("channels must be between 1 and 255")
    if bits_per_sample not in (8, 16, 24, 32):
        raise ValueError("bits_per_sample must be 8, 16, 24, or 32")
    if not 1 <= sample_rate <= 0xFFFFFFFF:
        raise ValueError("sample_rate must be between 1 and 4294967295")
    if not 0 <= sequence <= 0xFFFFFFFF:
        raise ValueError("sequence must be between 0 and 4294967295")
    if len(pcm_data) > 0xFFFF:
        raise ValueError("pcm_data exceeds the UDP packet payload limit")
    header = UDP_PACKET_FIXED_HEADER.pack(
        UDP_PACKET_MAGIC,
        len(encoded_id),
        channels,
        bits_per_sample,
        encoding,
        sample_rate,
        sequence,
        len(pcm_data),
    )
    return header + encoded_id + pcm_data


def decode_udp_audio_packet(
    data: bytes,
    fallback_assistant_id: str,
) -> tuple[str, bytes, AudioFormat | None] | None:
    """Decode a framed packet, or treat a non-magic packet as legacy raw PCM.

    Returns None for a packet that claims framing but fails validation.
    """
    if data.startswith(UDP_PACKET_MAGIC):
        if len(data) < UDP_PACKET_FIXED_HEADER.size:
            return None
        (
            _magic,
            id_length,
            channels,
            bits_per_sample,
            encoding,
            sample_rate,
            _sequence,
            payload_length,
        ) = UDP_PACKET_FIXED_HEADER.unpack_from(data)
        header_length = UDP_PACKET_FIXED_HEADER.size + id_length
        if (
            not 1 <= id_length <= MAX_ASSISTANT_ID_BYTES
            or channels == 0
            or bits_per_sample not in (8, 16, 24, 32)
            or sample_rate == 0
            or encoding != UDP_AUDIO_ENCODING_PCM_SIGNED_LE
            or payload_length == 0
            or len(data) != header_length + payload_length
        ):
            return None
        try:
            assistant_id = data[UDP_PACKET_FIXED_HEADER.size : header_length].decode("ascii")
        except UnicodeDecodeError:
            return None
        if ASSISTANT_ID_PATTERN.fullmatch(assistant_id) is None:
            return None
        audio_format = AudioFormat(
            sample_rate=sample_rate,
            sample_width=bits_per_sample // 8,
            channels=channels,
        )
        return assistant_id, data[header_length:], audio_format

    if not data.startswith(UDP_PACKET_V1_MAGIC):
        return fallback_assistant_id, data, None

    if len(data) <= len(UDP_PACKET_V1_MAGIC):
        return None
    id_length = data[len(UDP_PACKET_V1_MAGIC)]
    header_length = len(UDP_PACKET_V1_MAGIC) + 1 + id_length
    if not 1 <= id_length <= MAX_ASSISTANT_ID_BYTES or len(data) <= header_length:
        return None
    try:
        assistant_id = data[len(UDP_PACKET_V1_MAGIC) + 1 : header_length].decode("ascii")
    except UnicodeDecodeError:
        return None
    if ASSISTANT_ID_PATTERN.fullmatch(assistant_id) is None:
        return None
    return assistant_id, data[header_length:], None


class _AudioDatagramProtocol(asyncio.DatagramProtocol):
    """Forwards each datagram to the audio callback on the event loop."""

    def __init__(self, audio_callback: AudioCallback, assistant_id: str | None) -> None:
        self._audio_callback = audio_callback
        self._assistant_id = assistant_id
        self._warned_malformed = False

    def datagram_received(self, data: bytes, addr) -> None:
        if not data:
            return
        fallback_assistant_id = self._assistant_id or addr[0]
        decoded = decode_udp_audio_packet(data, fallback_assistant_id)
        if decoded is None:
            # A misconfigured sender can emit these continuously; warn once.
            if not self._warned_malformed:
                self._warned_malformed = True
                _LOGGER.warning("Ignoring malformed framed UDP audio datagram from %s", addr)
            return
        assistant_id, pcm_data, audio_format = decoded
        # A fixed receiver ID stays an explicit override for single-assistant
        # deployments, even when the sender uses the framed protocol.
        assistant_id = self._assistant_id or assistant_id
        try:
            self._audio_callback(assistant_id, pcm_data, audio_format)
        except Exception:
            _LOGGER.exception("Error handling UDP audio datagram from %s", addr)

    def error_received(self, exc: Exception) -> None:
        _LOGGER.warning("UDP receiver error: %s", exc)


class UDPAudioReceiver:
    """Binds a datagram endpoint on Home Assistant's event loop."""

    def __init__(
        self,
        port: int,
        audio_callback: AudioCallback,
        assistant_id: str | None = None,
        host: str = "0.0.0.0",
    ) -> None:
        self.host = host
        self.port = port
        self.assistant_id = assistant_id or None
        self._audio_callback = audio_callback
        self._transport: asyncio.DatagramTransport | None = None

    @property
    def running(self) -> bool:
        return self._transport is not None

    async def async_start(self) -> bool:
        """Bind the socket. Returns False if the port is unavailable."""
        if self._transport is not None:
            return True
        loop = asyncio.get_running_loop()
        try:
            self._transport, _ = await loop.create_datagram_endpoint(
                lambda: _AudioDatagramProtocol(self._audio_callback, self.assistant_id),
                local_addr=(self.host, self.port),
            )
        except OSError as exc:
            _LOGGER.error(
                "Failed to bind Intentsity UDP audio receiver to %s:%s: %s",
                self.host,
                self.port,
                exc,
            )
            return False
        _LOGGER.info(
            "Intentsity UDP audio receiver listening on %s:%s (assistant_id=%s)",
            self.host,
            self.port,
            self.assistant_id or "<packet or sender IP>",
        )
        return True

    def stop(self) -> None:
        if self._transport is not None:
            self._transport.close()
            self._transport = None

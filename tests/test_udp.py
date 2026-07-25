"""UDP framing, decoding, and the datagram endpoint."""

from __future__ import annotations

import asyncio
import logging
import socket

import numpy as np
import pytest

from custom_components.intentsity.models import AudioFormat
from custom_components.intentsity.udp import (
    MAX_ASSISTANT_ID_BYTES,
    UDP_AUDIO_ENCODING_PCM_SIGNED_LE,
    UDP_PACKET_FIXED_HEADER,
    UDP_PACKET_MAGIC,
    UDP_PACKET_V1_MAGIC,
    UDPAudioReceiver,
    _AudioDatagramProtocol,
    decode_udp_audio_packet,
    encode_udp_audio_packet,
)

PCM = np.arange(64, dtype="<i2").tobytes()


def _free_udp_port() -> int:
    """Grab an ephemeral UDP port, then release it for the receiver to bind."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _v1_packet(assistant_id: bytes, payload: bytes) -> bytes:
    return UDP_PACKET_V1_MAGIC + bytes([len(assistant_id)]) + assistant_id + payload


def test_encode_decode_round_trip() -> None:
    packet = encode_udp_audio_packet(
        "kitchen", PCM, sample_rate=48000, bits_per_sample=32, channels=2, sequence=7
    )
    decoded = decode_udp_audio_packet(packet, "fallback")

    assert decoded is not None
    assistant_id, pcm, audio_format = decoded
    assert assistant_id == "kitchen"
    assert pcm == PCM
    assert audio_format == AudioFormat(sample_rate=48000, sample_width=4, channels=2)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"assistant_id": "kitchén"}, "ASCII"),
        ({"assistant_id": ""}, "1 to 64 ASCII bytes"),
        ({"assistant_id": "k" * (MAX_ASSISTANT_ID_BYTES + 1)}, "1 to 64 ASCII bytes"),
        ({"assistant_id": "_kitchen"}, "alphanumeric"),
        ({"assistant_id": "kitchen sink"}, "alphanumeric"),
        ({"pcm_data": b""}, "must not be empty"),
        ({"channels": 0}, "channels must be"),
        ({"channels": 256}, "channels must be"),
        ({"bits_per_sample": 12}, "bits_per_sample must be"),
        ({"sample_rate": 0}, "sample_rate must be"),
        ({"sequence": -1}, "sequence must be"),
        ({"pcm_data": b"\x00" * (0xFFFF + 1)}, "payload limit"),
    ],
)
def test_encode_rejects_invalid_input(kwargs: dict, match: str) -> None:
    call = {"assistant_id": "kitchen", "pcm_data": PCM, **kwargs}
    positional = (call.pop("assistant_id"), call.pop("pcm_data"))
    with pytest.raises(ValueError, match=match):
        encode_udp_audio_packet(*positional, **call)


def test_decode_raw_pcm_uses_fallback_id() -> None:
    decoded = decode_udp_audio_packet(PCM, "192.0.2.10")
    assert decoded == ("192.0.2.10", PCM, None)


def test_decode_v1_packet() -> None:
    decoded = decode_udp_audio_packet(_v1_packet(b"office", PCM), "fallback")
    assert decoded == ("office", PCM, None)


@pytest.mark.parametrize(
    "packet",
    [
        UDP_PACKET_V1_MAGIC,
        # Declared ID length of zero.
        _v1_packet(b"", PCM),
        # ID present but no PCM after it.
        _v1_packet(b"office", b""),
        # Non-ASCII assistant ID.
        _v1_packet(b"\xff\xfe", PCM),
        # ID that fails the character policy.
        _v1_packet(b"-office", PCM),
        # Declared ID length longer than the datagram.
        UDP_PACKET_V1_MAGIC + bytes([32]) + b"office",
    ],
)
def test_decode_rejects_bad_v1_packets(packet: bytes) -> None:
    assert decode_udp_audio_packet(packet, "fallback") is None


def _v2_packet(
    *,
    id_length: int = 7,
    channels: int = 1,
    bits: int = 16,
    encoding: int = UDP_AUDIO_ENCODING_PCM_SIGNED_LE,
    sample_rate: int = 16000,
    payload_length: int | None = None,
    assistant_id: bytes = b"kitchen",
    payload: bytes = PCM,
) -> bytes:
    header = UDP_PACKET_FIXED_HEADER.pack(
        UDP_PACKET_MAGIC,
        id_length,
        channels,
        bits,
        encoding,
        sample_rate,
        0,
        len(payload) if payload_length is None else payload_length,
    )
    return header + assistant_id + payload


@pytest.mark.parametrize(
    ("packet", "reason"),
    [
        (UDP_PACKET_MAGIC + b"\x00", "truncated header"),
        (_v2_packet(id_length=0, assistant_id=b""), "zero-length id"),
        (_v2_packet(id_length=MAX_ASSISTANT_ID_BYTES + 1), "oversized id"),
        (_v2_packet(channels=0), "zero channels"),
        (_v2_packet(bits=12), "unsupported bit depth"),
        (_v2_packet(sample_rate=0), "zero sample rate"),
        (_v2_packet(encoding=2), "unknown encoding"),
        (_v2_packet(payload=b"", payload_length=0), "empty payload"),
        (_v2_packet(payload_length=len(PCM) + 1), "length mismatch"),
        (_v2_packet(assistant_id=b"\xff" * 7), "non-ascii id"),
        (_v2_packet(assistant_id=b"-itchen"), "invalid id characters"),
    ],
)
def test_decode_rejects_bad_v2_packets(packet: bytes, reason: str) -> None:
    assert decode_udp_audio_packet(packet, "fallback") is None, reason


def test_protocol_forwards_datagram() -> None:
    received: list[tuple] = []
    protocol = _AudioDatagramProtocol(lambda *args: received.append(args), assistant_id=None)
    protocol.datagram_received(encode_udp_audio_packet("kitchen", PCM), ("192.0.2.5", 1234))

    assert received == [
        ("kitchen", PCM, AudioFormat(sample_rate=16000, sample_width=2, channels=1))
    ]


def test_protocol_uses_sender_ip_for_unframed_audio() -> None:
    received: list[tuple] = []
    protocol = _AudioDatagramProtocol(lambda *args: received.append(args), assistant_id=None)
    protocol.datagram_received(PCM, ("192.0.2.5", 1234))

    assert received == [("192.0.2.5", PCM, None)]


def test_protocol_configured_id_overrides_packet() -> None:
    received: list[tuple] = []
    protocol = _AudioDatagramProtocol(
        lambda *args: received.append(args), assistant_id="only-satellite"
    )
    protocol.datagram_received(encode_udp_audio_packet("kitchen", PCM), ("192.0.2.5", 1234))

    assert received[0][0] == "only-satellite"


def test_protocol_ignores_empty_datagram() -> None:
    received: list[tuple] = []
    protocol = _AudioDatagramProtocol(lambda *args: received.append(args), None)
    protocol.datagram_received(b"", ("192.0.2.5", 1234))
    assert received == []


def test_protocol_warns_once_for_malformed_packets(
    caplog: pytest.LogCaptureFixture,
) -> None:
    protocol = _AudioDatagramProtocol(lambda *args: None, None)
    bad = UDP_PACKET_MAGIC + b"\x00"

    with caplog.at_level(logging.WARNING, logger="custom_components.intentsity.udp"):
        protocol.datagram_received(bad, ("192.0.2.5", 1234))
        protocol.datagram_received(bad, ("192.0.2.5", 1234))

    assert caplog.text.count("malformed framed UDP audio datagram") == 1


def test_protocol_swallows_callback_errors(caplog: pytest.LogCaptureFixture) -> None:
    def _boom(*_args) -> None:
        raise RuntimeError("buffer exploded")

    protocol = _AudioDatagramProtocol(_boom, None)
    with caplog.at_level(logging.ERROR, logger="custom_components.intentsity.udp"):
        protocol.datagram_received(PCM, ("192.0.2.5", 1234))

    assert "Error handling UDP audio datagram" in caplog.text


def test_protocol_logs_transport_errors(caplog: pytest.LogCaptureFixture) -> None:
    protocol = _AudioDatagramProtocol(lambda *args: None, None)
    with caplog.at_level(logging.WARNING, logger="custom_components.intentsity.udp"):
        protocol.error_received(OSError("connection refused"))

    assert "UDP receiver error" in caplog.text


async def test_receiver_receives_real_datagram(socket_enabled: None) -> None:
    received: list[tuple] = []
    port = _free_udp_port()
    receiver = UDPAudioReceiver(
        port=port, audio_callback=lambda *args: received.append(args), host="127.0.0.1"
    )

    assert await receiver.async_start() is True
    assert receiver.running is True
    # Starting twice is a no-op rather than a rebind.
    assert await receiver.async_start() is True

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(encode_udp_audio_packet("kitchen", PCM), ("127.0.0.1", port))
        for _ in range(20):
            await asyncio.sleep(0.01)
            if received:
                break
    finally:
        sock.close()
        receiver.stop()

    assert received[0][0] == "kitchen"
    assert receiver.running is False
    receiver.stop()  # idempotent


async def test_receiver_reports_bind_failure(
    socket_enabled: None, caplog: pytest.LogCaptureFixture
) -> None:
    port = _free_udp_port()
    holder = UDPAudioReceiver(port=port, audio_callback=lambda *args: None, host="127.0.0.1")
    assert await holder.async_start() is True

    second = UDPAudioReceiver(port=port, audio_callback=lambda *args: None, host="127.0.0.1")
    try:
        with caplog.at_level(logging.ERROR, logger="custom_components.intentsity.udp"):
            assert await second.async_start() is False
    finally:
        holder.stop()

    assert second.running is False
    assert "Failed to bind" in caplog.text


def test_receiver_normalizes_blank_assistant_id() -> None:
    receiver = UDPAudioReceiver(port=1, audio_callback=lambda *args: None, assistant_id="")
    assert receiver.assistant_id is None

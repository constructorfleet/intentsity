"""Rolling buffer, envelope, and WAV output."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import wave

import numpy as np
import pytest

from custom_components.intentsity.audio import (
    WAVEFORM_POINTS,
    AudioBuffer,
    MultiAssistantAudioBuffer,
    clip_filename,
    compute_peaks,
    dtype_for_width,
    write_wav,
)
from custom_components.intentsity.models import AudioFormat


def test_dtype_for_width() -> None:
    assert dtype_for_width(1) == np.dtype("i1")
    assert dtype_for_width(2) == np.dtype("<i2")
    assert dtype_for_width(4) == np.dtype("<i4")
    with pytest.raises(ValueError, match="Unsupported sample width"):
        dtype_for_width(3)


def test_compute_peaks_normalizes_to_one() -> None:
    samples = np.array([0, 100, -200, 50, 400, -400], dtype="<i2")
    peaks = compute_peaks(samples, points=3)
    assert len(peaks) == 3
    assert max(peaks) == 1.0
    assert all(0.0 <= value <= 1.0 for value in peaks)


def test_compute_peaks_edge_cases() -> None:
    assert compute_peaks(np.array([], dtype="<i2")) == []
    # Digital silence has no ceiling to normalize against.
    assert compute_peaks(np.zeros(10, dtype="<i2"), points=5) == [0.0] * 5
    # Fewer samples than points yields one bucket per sample, not empty buckets.
    assert len(compute_peaks(np.arange(1, 5, dtype="<i2"), points=WAVEFORM_POINTS)) == 4


def test_buffer_append_tracks_frames(audio_format: AudioFormat, make_pcm) -> None:
    buffer = AudioBuffer(audio_format=audio_format, buffer_duration=1.0)
    assert buffer.frame_count == 0
    assert buffer.duration == 0.0
    assert buffer.last_audio_at is None

    buffer.append(make_pcm(800))
    assert buffer.frame_count == 800
    assert buffer.duration == pytest.approx(0.05)
    assert buffer.last_audio_at is not None
    assert buffer.max_frames == 16000


def test_buffer_append_ignores_unusable_payloads(audio_format: AudioFormat, make_pcm) -> None:
    buffer = AudioBuffer(audio_format=audio_format, buffer_duration=1.0)
    buffer.append(b"")
    # A single byte cannot form a 16-bit frame.
    buffer.append(b"\x01")
    assert buffer.frame_count == 0

    # A trailing partial frame is truncated rather than rejected.
    buffer.append(make_pcm(2) + b"\x01")
    assert buffer.frame_count == 2


def test_buffer_trims_oldest_frames(audio_format: AudioFormat) -> None:
    buffer = AudioBuffer(audio_format=audio_format, buffer_duration=1.0)
    for start in range(0, 20000, 4000):
        buffer.append(np.arange(start, start + 4000, dtype="<i2").tobytes())

    assert buffer.frame_count == buffer.max_frames == 16000
    frames = buffer.tail(1.0)
    # The window holds the newest 16000 of the 20000 frames written.
    assert frames[0] == 4000
    assert frames[-1] == 19999


def test_buffer_trim_splits_a_partially_expired_chunk(audio_format: AudioFormat) -> None:
    buffer = AudioBuffer(audio_format=audio_format, buffer_duration=0.5)  # 8000 frames
    buffer.append(np.arange(0, 6000, dtype="<i2").tobytes())
    buffer.append(np.arange(6000, 12000, dtype="<i2").tobytes())

    assert buffer.frame_count == 8000
    frames = buffer.tail(0.5)
    assert frames[0] == 4000


def test_buffer_multichannel_frames_are_grouped() -> None:
    audio_format = AudioFormat(sample_rate=16000, sample_width=2, channels=2)
    buffer = AudioBuffer(audio_format=audio_format, buffer_duration=1.0)
    buffer.append(np.arange(20, dtype="<i2").tobytes())

    assert buffer.frame_count == 10
    frames = buffer.tail(1.0)
    assert frames.shape == (10, 2)


def test_buffer_empty_reads(audio_format: AudioFormat) -> None:
    buffer = AudioBuffer(audio_format=audio_format, buffer_duration=1.0)
    assert buffer.extract(1.0, 1.0).shape[0] == 0
    assert buffer.tail(1.0).shape[0] == 0

    stereo = AudioBuffer(
        audio_format=AudioFormat(sample_rate=16000, sample_width=2, channels=2),
        buffer_duration=1.0,
    )
    assert stereo.tail(1.0).shape == (0, 2)


def test_buffer_extract_window_around_trigger(audio_format: AudioFormat) -> None:
    buffer = AudioBuffer(audio_format=audio_format, buffer_duration=10.0)
    buffer.append(np.arange(0, 16000 * 6, dtype="<i4").astype("<i2").tobytes())

    # Trigger one second back: 2s of pre-roll and 1s of post-roll around it.
    window = buffer.extract(pre_duration=2.0, post_duration=1.0, trigger_offset=1.0)
    assert window.shape[0] == 16000 * 3

    # Asking for more pre-roll than exists clamps at the start of the buffer.
    clamped = buffer.extract(pre_duration=60.0, post_duration=0.0, trigger_offset=0.0)
    assert clamped.shape[0] == buffer.frame_count

    # A window that ends before it starts yields nothing rather than reversing.
    assert buffer.extract(pre_duration=0.0, post_duration=0.0).shape[0] == 0


def test_buffer_repeated_reads_collapse_chunks(audio_format: AudioFormat) -> None:
    buffer = AudioBuffer(audio_format=audio_format, buffer_duration=10.0)
    for _ in range(4):
        buffer.append(np.arange(100, dtype="<i2").tobytes())

    first = buffer.tail(10.0)
    second = buffer.tail(10.0)
    assert first.shape == second.shape == (400,)


def test_buffer_clear_and_reformat(audio_format: AudioFormat, make_pcm) -> None:
    buffer = AudioBuffer(audio_format=audio_format, buffer_duration=1.0)
    buffer.append(make_pcm(100))
    buffer.clear()
    assert buffer.frame_count == 0

    buffer.append(make_pcm(100))
    buffer.reformat(audio_format)
    # Same format: nothing to discard.
    assert buffer.frame_count == 100

    buffer.reformat(AudioFormat(sample_rate=32000, sample_width=2, channels=1))
    assert buffer.frame_count == 0
    assert buffer.audio_format.sample_rate == 32000


def test_multi_assistant_buffer_creates_per_assistant(audio_format: AudioFormat, make_pcm) -> None:
    buffers = MultiAssistantAudioBuffer(default_format=audio_format, buffer_duration=1.0)
    assert buffers.assistant_ids == []
    assert buffers.get("kitchen") is None
    assert buffers.format_for("kitchen") == audio_format

    buffers.append("kitchen", make_pcm(100))
    buffers.append("office", make_pcm(50))
    assert sorted(buffers.assistant_ids) == ["kitchen", "office"]
    assert buffers.get("kitchen").frame_count == 100

    # ensure() is idempotent.
    assert buffers.ensure("kitchen") is buffers.get("kitchen")


def test_multi_assistant_buffer_packet_format_wins(audio_format: AudioFormat, make_pcm) -> None:
    buffers = MultiAssistantAudioBuffer(default_format=audio_format, buffer_duration=1.0)
    declared = AudioFormat(sample_rate=48000, sample_width=4, channels=2)
    buffers.append("kitchen", make_pcm(100), declared)

    assert buffers.format_for("kitchen") == declared
    assert buffers.get("kitchen").audio_format == declared


def test_multi_assistant_buffer_set_format_before_first_audio(
    audio_format: AudioFormat, make_pcm
) -> None:
    buffers = MultiAssistantAudioBuffer(default_format=audio_format, buffer_duration=1.0)
    declared = AudioFormat(sample_rate=8000, sample_width=1, channels=1)
    buffers.set_format("kitchen", declared)

    # A retained audio_info message arrives before any audio; the buffer created
    # later must adopt it instead of the default.
    assert buffers.format_for("kitchen") == declared
    buffers.append("kitchen", make_pcm(10))
    assert buffers.get("kitchen").audio_format == declared


def test_multi_assistant_buffer_clear(audio_format: AudioFormat, make_pcm) -> None:
    buffers = MultiAssistantAudioBuffer(default_format=audio_format, buffer_duration=1.0)
    buffers.append("kitchen", make_pcm(100))
    buffers.append("office", make_pcm(100))

    buffers.clear("kitchen")
    assert buffers.get("kitchen").frame_count == 0
    assert buffers.get("office").frame_count == 100

    buffers.clear("missing")  # no-op
    buffers.clear()
    assert buffers.get("office").frame_count == 0


def test_write_wav_round_trips(tmp_path: Path, audio_format: AudioFormat) -> None:
    samples = np.arange(-500, 500, dtype="<i2")
    path = tmp_path / "nested" / "clip.wav"
    write_wav(path, samples, audio_format, {"assistant_id": "kitchen"})

    with wave.open(str(path), "rb") as handle:
        assert handle.getnchannels() == 1
        assert handle.getsampwidth() == 2
        assert handle.getframerate() == 16000
        assert handle.getnframes() == samples.size
        assert handle.readframes(samples.size) == samples.tobytes()

    assert json.loads(path.with_suffix(".json").read_text()) == {"assistant_id": "kitchen"}


def test_write_wav_without_metadata(tmp_path: Path, audio_format: AudioFormat) -> None:
    path = tmp_path / "clip.wav"
    write_wav(path, np.zeros(8, dtype="<i2"), audio_format)
    assert not path.with_suffix(".json").exists()


def test_clip_filename_is_sortable_and_safe() -> None:
    timestamp = datetime(2026, 3, 1, 12, 30, 45, 123456, tzinfo=UTC)
    assert clip_filename(timestamp, "kitchen") == "20260301_123045_123456_kitchen.wav"
    # Path separators and spaces cannot survive into a filename.
    assert clip_filename(timestamp, "../a b/c") == "20260301_123045_123456_.._a_b_c.wav"

"""Rolling PCM buffers and WAV output for wake-word clip capture.

Audio arrives as datagrams or MQTT payloads at up to 48 kHz, so the buffer
stores whole numpy chunks in a deque and trims by frame count. The add-on this
replaces appended one Python int per sample, which cost roughly a million
interpreter-level operations per second per assistant.
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
import wave

import numpy as np

from .models import AudioFormat

_LOGGER = logging.getLogger(__name__)

# Number of envelope points stored per clip for the panel's waveform.
WAVEFORM_POINTS = 96

_DTYPES: dict[int, np.dtype] = {
    1: np.dtype("i1"),
    2: np.dtype("<i2"),
    4: np.dtype("<i4"),
}


def dtype_for_width(sample_width: int) -> np.dtype:
    """Return the numpy dtype for a PCM sample width in bytes."""
    try:
        return _DTYPES[sample_width]
    except KeyError:
        raise ValueError(f"Unsupported sample width: {sample_width}") from None


def compute_peaks(samples: np.ndarray, points: int = WAVEFORM_POINTS) -> list[float]:
    """Reduce samples to a normalized 0..1 envelope for waveform rendering."""
    if samples.size == 0:
        return []
    magnitude = np.abs(samples.astype(np.float32))
    # Split into `points` near-equal buckets and take each bucket's peak.
    buckets = np.array_split(magnitude, min(points, magnitude.size))
    peaks = np.array([float(bucket.max()) for bucket in buckets if bucket.size])
    ceiling = float(peaks.max())
    if ceiling <= 0:
        return [0.0] * len(peaks)
    return [float(round(value / ceiling, 4)) for value in peaks]


@dataclass
class AudioBuffer:
    """Rolling window of interleaved PCM frames for one assistant."""

    audio_format: AudioFormat
    buffer_duration: float
    _chunks: deque[np.ndarray] = field(default_factory=deque, init=False, repr=False)
    _frames: int = field(default=0, init=False)
    last_audio_at: datetime | None = field(default=None, init=False)

    @property
    def max_frames(self) -> int:
        return max(1, int(self.audio_format.sample_rate * self.buffer_duration))

    @property
    def frame_count(self) -> int:
        return self._frames

    @property
    def duration(self) -> float:
        return self._frames / self.audio_format.sample_rate

    def append(self, pcm: bytes) -> None:
        """Append raw PCM, dropping the oldest frames once the window is full."""
        if not pcm:
            return
        dtype = dtype_for_width(self.audio_format.sample_width)
        channels = self.audio_format.channels
        usable = len(pcm) - (len(pcm) % (dtype.itemsize * channels))
        if usable <= 0:
            return
        samples = np.frombuffer(pcm, dtype=dtype, count=usable // dtype.itemsize)
        if channels > 1:
            samples = samples.reshape(-1, channels)
        # frombuffer views the caller's bytes; copy so the deque owns its memory.
        self._chunks.append(samples.copy())
        self._frames += samples.shape[0]
        self.last_audio_at = datetime.now(UTC)
        self._trim()

    def _trim(self) -> None:
        excess = self._frames - self.max_frames
        while excess > 0 and self._chunks:
            head = self._chunks[0]
            if head.shape[0] <= excess:
                self._chunks.popleft()
                self._frames -= head.shape[0]
                excess -= head.shape[0]
            else:
                self._chunks[0] = head[excess:]
                self._frames -= excess
                excess = 0

    def _frames_array(self) -> np.ndarray:
        if not self._chunks:
            dtype = dtype_for_width(self.audio_format.sample_width)
            shape = (0, self.audio_format.channels) if self.audio_format.channels > 1 else (0,)
            return np.empty(shape, dtype=dtype)
        if len(self._chunks) == 1:
            return self._chunks[0]
        combined = np.concatenate(list(self._chunks))
        # Collapse to one chunk so repeated reads do not re-concatenate.
        self._chunks.clear()
        self._chunks.append(combined)
        return combined

    def extract(
        self,
        pre_duration: float,
        post_duration: float,
        trigger_offset: float = 0.0,
    ) -> np.ndarray:
        """Extract frames around a trigger point.

        `trigger_offset` is how many seconds before the newest frame the trigger
        occurred, so a caller that waited for post-roll audio passes the time it
        waited.
        """
        frames = self._frames_array()
        if frames.shape[0] == 0:
            return frames
        rate = self.audio_format.sample_rate
        trigger = frames.shape[0] - int(trigger_offset * rate)
        start = max(0, trigger - int(pre_duration * rate))
        end = min(frames.shape[0], trigger + int(post_duration * rate))
        if end <= start:
            return frames[:0]
        return frames[start:end]

    def tail(self, duration: float) -> np.ndarray:
        """Extract the newest `duration` seconds."""
        frames = self._frames_array()
        if frames.shape[0] == 0:
            return frames
        wanted = int(duration * self.audio_format.sample_rate)
        return frames[-wanted:] if wanted < frames.shape[0] else frames

    def clear(self) -> None:
        self._chunks.clear()
        self._frames = 0

    def reformat(self, audio_format: AudioFormat) -> None:
        """Adopt a new frame format, discarding buffered audio in the old one."""
        if audio_format == self.audio_format:
            return
        _LOGGER.debug(
            "Audio format changed from %s to %s; clearing buffer",
            self.audio_format,
            audio_format,
        )
        self.audio_format = audio_format
        self.clear()


class MultiAssistantAudioBuffer:
    """One rolling buffer per assistant, created on first audio."""

    def __init__(self, default_format: AudioFormat, buffer_duration: float) -> None:
        self._default_format = default_format
        self._buffer_duration = buffer_duration
        self._buffers: dict[str, AudioBuffer] = {}
        self._configured: dict[str, AudioFormat] = {}
        self._lock = asyncio.Lock()

    @property
    def assistant_ids(self) -> list[str]:
        return list(self._buffers)

    def get(self, assistant_id: str) -> AudioBuffer | None:
        return self._buffers.get(assistant_id)

    def ensure(self, assistant_id: str) -> AudioBuffer:
        buffer = self._buffers.get(assistant_id)
        if buffer is None:
            audio_format = self._configured.get(assistant_id, self._default_format)
            buffer = AudioBuffer(
                audio_format=audio_format,
                buffer_duration=self._buffer_duration,
            )
            self._buffers[assistant_id] = buffer
            _LOGGER.debug(
                "Created audio buffer for %s (%s Hz, %s-bit, %s ch)",
                assistant_id,
                audio_format.sample_rate,
                audio_format.sample_width * 8,
                audio_format.channels,
            )
        return buffer

    def set_format(self, assistant_id: str, audio_format: AudioFormat) -> None:
        """Record a device-reported format, reformatting any live buffer."""
        self._configured[assistant_id] = audio_format
        buffer = self._buffers.get(assistant_id)
        if buffer is not None:
            buffer.reformat(audio_format)

    def append(
        self,
        assistant_id: str,
        pcm: bytes,
        audio_format: AudioFormat | None = None,
    ) -> None:
        """Append PCM for an assistant, adopting a packet-declared format."""
        if audio_format is not None:
            self.set_format(assistant_id, audio_format)
        self.ensure(assistant_id).append(pcm)

    def format_for(self, assistant_id: str) -> AudioFormat:
        buffer = self._buffers.get(assistant_id)
        if buffer is not None:
            return buffer.audio_format
        return self._configured.get(assistant_id, self._default_format)

    def clear(self, assistant_id: str | None = None) -> None:
        if assistant_id is None:
            for buffer in self._buffers.values():
                buffer.clear()
            return
        buffer = self._buffers.get(assistant_id)
        if buffer is not None:
            buffer.clear()


def write_wav(
    path: Path,
    samples: np.ndarray,
    audio_format: AudioFormat,
    metadata: dict | None = None,
) -> None:
    """Write PCM frames to a WAV file plus a companion JSON metadata file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(audio_format.channels)
        wav_file.setsampwidth(audio_format.sample_width)
        wav_file.setframerate(audio_format.sample_rate)
        wav_file.writeframes(samples.tobytes())
    if metadata:
        path.with_suffix(".json").write_text(json.dumps(metadata, indent=2))


def clip_filename(timestamp: datetime, assistant_id: str) -> str:
    """Build a sortable, filesystem-safe clip filename."""
    safe_assistant = "".join(
        char if char.isalnum() or char in "-_." else "_" for char in assistant_id
    )
    stamp = timestamp.strftime("%Y%m%d_%H%M%S_%f")
    return f"{stamp}_{safe_assistant}.wav"

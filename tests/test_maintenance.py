from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import wave

from homeassistant.core import HomeAssistant
import numpy as np

from custom_components.intentsity import db
from custom_components.intentsity.maintenance import repair_misdeclared_clip_sample_rates
from custom_components.intentsity.models import Clip


def _write_wav(path: Path, pcm: bytes, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm)


def _read_wav(path: Path) -> tuple[int, int, bytes]:
    with wave.open(str(path), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        frames = wav_file.getnframes()
        pcm = wav_file.readframes(frames)
    return sample_rate, frames, pcm


def test_repair_misdeclared_clip_sample_rates_dry_run(hass: HomeAssistant, clean_db: None) -> None:
    pcm = np.arange(16000, dtype="<i2").tobytes()
    filename = "legacy.wav"
    db.insert_clip(
        hass,
        Clip(
            filename=filename,
            timestamp=datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            sample_rate=48000,
            sample_width=2,
            channels=1,
            duration=round(16000 / 48000, 4),
        ),
    )
    wav_path = db.get_clips_dir(hass) / filename
    _write_wav(wav_path, pcm, 48000)

    summary = repair_misdeclared_clip_sample_rates(db.get_storage_dir(hass))

    assert summary.scanned == 1
    assert summary.repaired == 1
    sample_rate, frames, repaired_pcm = _read_wav(wav_path)
    assert sample_rate == 48000
    assert frames == 16000
    assert repaired_pcm == pcm
    assert db.fetch_clip(hass, 1).sample_rate == 48000


def test_repair_misdeclared_clip_sample_rates_updates_wav_db_and_sidecar(
    hass: HomeAssistant, clean_db: None
) -> None:
    pcm = np.arange(16000, dtype="<i2").tobytes()
    filename = "legacy.wav"
    db.insert_clip(
        hass,
        Clip(
            filename=filename,
            timestamp=datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            sample_rate=48000,
            sample_width=2,
            channels=1,
            duration=round(16000 / 48000, 4),
        ),
    )
    wav_path = db.get_clips_dir(hass) / filename
    _write_wav(wav_path, pcm, 48000)
    wav_path.with_suffix(".json").write_text(
        json.dumps(
            {
                "filename": filename,
                "sample_rate": 48000,
                "sample_width": 2,
                "channels": 1,
                "duration": round(16000 / 48000, 4),
            }
        )
    )

    summary = repair_misdeclared_clip_sample_rates(
        db.get_storage_dir(hass).parent,
        dry_run=False,
    )

    assert summary.scanned == 1
    assert summary.repaired == 1
    sample_rate, frames, repaired_pcm = _read_wav(wav_path)
    assert sample_rate == 16000
    assert frames == 16000
    assert repaired_pcm == pcm

    clip = db.fetch_clip(hass, 1)
    assert clip.sample_rate == 16000
    assert clip.duration == 1.0
    assert clip.sample_width == 2
    assert clip.channels == 1
    assert len(clip.peaks) == 96

    metadata = json.loads(wav_path.with_suffix(".json").read_text())
    assert metadata["sample_rate"] == 16000
    assert metadata["duration"] == 1.0
    assert metadata["frames"] == 16000


def test_repair_misdeclared_clip_sample_rates_can_target_one_clip(
    hass: HomeAssistant, clean_db: None
) -> None:
    pcm = np.arange(16000, dtype="<i2").tobytes()
    first_id = db.insert_clip(
        hass,
        Clip(
            filename="first.wav",
            timestamp=datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            sample_rate=48000,
            sample_width=2,
            channels=1,
        ),
    )
    second_id = db.insert_clip(
        hass,
        Clip(
            filename="second.wav",
            timestamp=datetime(2026, 3, 1, 12, 1, tzinfo=UTC),
            sample_rate=48000,
            sample_width=2,
            channels=1,
        ),
    )
    _write_wav(db.get_clips_dir(hass) / "first.wav", pcm, 48000)
    _write_wav(db.get_clips_dir(hass) / "second.wav", pcm, 48000)

    summary = repair_misdeclared_clip_sample_rates(
        db.get_storage_dir(hass),
        clip_id=second_id,
        dry_run=False,
    )

    assert summary.scanned == 1
    assert summary.repaired == 1
    assert _read_wav(db.get_clips_dir(hass) / "first.wav")[0] == 48000
    assert _read_wav(db.get_clips_dir(hass) / "second.wav")[0] == 16000
    assert db.fetch_clip(hass, first_id).sample_rate == 48000
    assert db.fetch_clip(hass, second_id).sample_rate == 16000


def test_repair_misdeclared_clip_sample_rates_skips_nonmatching_wav_header(
    hass: HomeAssistant, clean_db: None
) -> None:
    filename = "already-correct.wav"
    db.insert_clip(
        hass,
        Clip(
            filename=filename,
            timestamp=datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            sample_rate=48000,
        ),
    )
    _write_wav(db.get_clips_dir(hass) / filename, np.zeros(16000, dtype="<i2").tobytes(), 16000)

    summary = repair_misdeclared_clip_sample_rates(db.get_storage_dir(hass), dry_run=False)

    assert summary.scanned == 1
    assert summary.repaired == 0
    assert summary.skipped_header_rate == 1

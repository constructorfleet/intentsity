from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
import tempfile
import wave

import numpy as np
import orjson

from .audio import compute_peaks, dtype_for_width
from .const import CLIPS_DIR, DB_NAME, STORAGE_DIR


@dataclass(slots=True)
class ClipRateRepairSummary:
    scanned: int = 0
    repaired: int = 0
    missing_file: int = 0
    skipped_header_rate: int = 0
    skipped_unsupported_format: int = 0


def _storage_dir(config_or_storage_dir: Path) -> Path:
    if (config_or_storage_dir / DB_NAME).is_file():
        return config_or_storage_dir
    return config_or_storage_dir / STORAGE_DIR


def repair_misdeclared_clip_sample_rates(
    config_or_storage_dir: Path,
    *,
    from_rate: int = 48000,
    to_rate: int = 16000,
    dry_run: bool = True,
) -> ClipRateRepairSummary:
    """Repair legacy clips whose WAV header declares the wrong sample rate.

    The legacy bug wrote already-16 kHz PCM into a WAV file marked as 48 kHz,
    which makes playback and training read the audio three times too fast. This
    rewrites the WAV header and row metadata only; it does not resample audio.
    """
    storage_dir = _storage_dir(config_or_storage_dir)
    db_path = storage_dir / DB_NAME
    clips_dir = storage_dir / CLIPS_DIR
    summary = ClipRateRepairSummary()

    if not db_path.is_file():
        return summary

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT id, filename
            FROM clips
            WHERE sample_rate = ?
            ORDER BY id
            """,
            (from_rate,),
        ).fetchall()

        for row in rows:
            summary.scanned += 1
            wav_path = clips_dir / row["filename"]
            if not wav_path.is_file():
                summary.missing_file += 1
                continue

            with wave.open(str(wav_path), "rb") as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                sample_rate = wav_file.getframerate()
                frames = wav_file.getnframes()
                pcm = wav_file.readframes(frames)

            if sample_rate != from_rate:
                summary.skipped_header_rate += 1
                continue

            try:
                dtype = dtype_for_width(sample_width)
            except ValueError:
                summary.skipped_unsupported_format += 1
                continue

            array = np.frombuffer(pcm, dtype=dtype)
            if channels > 1:
                array = array.reshape(-1, channels)
            peaks = compute_peaks(array)
            duration = round(frames / to_rate, 4)

            if dry_run:
                summary.repaired += 1
                continue

            with tempfile.NamedTemporaryFile(
                dir=wav_path.parent,
                prefix=f".{wav_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)

            try:
                with wave.open(str(temp_path), "wb") as wav_file:
                    wav_file.setnchannels(channels)
                    wav_file.setsampwidth(sample_width)
                    wav_file.setframerate(to_rate)
                    wav_file.writeframes(pcm)
                temp_path.replace(wav_path)
            finally:
                temp_path.unlink(missing_ok=True)

            connection.execute(
                """
                UPDATE clips
                SET duration = ?,
                    sample_rate = ?,
                    sample_width = ?,
                    channels = ?,
                    peaks = ?
                WHERE id = ?
                """,
                (
                    duration,
                    to_rate,
                    sample_width,
                    channels,
                    orjson.dumps(peaks).decode() if peaks else None,
                    row["id"],
                ),
            )

            metadata_path = wav_path.with_suffix(".json")
            if metadata_path.is_file():
                metadata = json.loads(metadata_path.read_text())
                metadata.update(
                    {
                        "duration": duration,
                        "sample_rate": to_rate,
                        "sample_width": sample_width,
                        "channels": channels,
                        "frames": frames,
                    }
                )
                metadata_path.write_text(json.dumps(metadata, indent=2))

            summary.repaired += 1

        if not dry_run:
            connection.commit()
    finally:
        connection.close()

    return summary

#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from custom_components.intentsity.maintenance import (  # noqa: E402
    repair_misdeclared_clip_sample_rates,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Repair legacy Intentsity WAV clips whose PCM is 16 kHz but whose "
            "WAV header and DB metadata say 48 kHz."
        )
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Home Assistant config directory, or the config/intentsity storage directory.",
    )
    parser.add_argument("--from-rate", type=int, default=48000)
    parser.add_argument("--to-rate", type=int, default=16000)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Modify WAV files, sidecar JSON, and intentsity.db. Without this, dry-run only.",
    )
    args = parser.parse_args()

    summary = repair_misdeclared_clip_sample_rates(
        args.path,
        from_rate=args.from_rate,
        to_rate=args.to_rate,
        dry_run=not args.write,
    )
    mode = "write" if args.write else "dry-run"
    print(
        f"{mode}: scanned={summary.scanned} repairable={summary.repaired} "
        f"missing_file={summary.missing_file} "
        f"skipped_header_rate={summary.skipped_header_rate} "
        f"skipped_unsupported_format={summary.skipped_unsupported_format}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

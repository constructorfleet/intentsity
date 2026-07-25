"""Timestamp coercion. Rows written by the legacy add-on carry naive strings."""

from __future__ import annotations

from datetime import UTC, datetime

from custom_components.intentsity import utils


def test_parse_timestamp_passthrough_aware() -> None:
    now = datetime.now(UTC)
    assert utils.parse_timestamp(now) is now


def test_parse_timestamp_assumes_utc_for_naive() -> None:
    parsed = utils.parse_timestamp(datetime(2026, 1, 1, 12, 0))
    assert parsed.tzinfo == UTC


def test_parse_timestamp_iso_string() -> None:
    assert utils.parse_timestamp("2026-01-01T00:00:00").isoformat() == "2026-01-01T00:00:00+00:00"
    assert utils.parse_timestamp("2026-01-01T00:00:00+02:00").utcoffset().total_seconds() == 7200


def test_parse_timestamp_falls_back_to_now() -> None:
    for value in ("not-a-date", 1234, None):
        before = datetime.now(UTC)
        parsed = utils.parse_timestamp(value)
        assert before <= parsed <= datetime.now(UTC)
        assert parsed.tzinfo == UTC

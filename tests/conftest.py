"""Shared fixtures.

`pytest-homeassistant-custom-component` supplies the `hass` fixture; everything
here is Intentsity-specific setup on top of it.
"""

from __future__ import annotations

from collections.abc import Callable, Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path
import shutil
import sys

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
import numpy as np
import pytest

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.intentsity import db  # noqa: E402
from custom_components.intentsity.config_flow import DEFAULT_OPTIONS  # noqa: E402
from custom_components.intentsity.const import DOMAIN  # noqa: E402
from custom_components.intentsity.models import AudioFormat, Clip  # noqa: E402


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Let Home Assistant load `custom_components/intentsity` in every test."""
    return


@pytest.fixture(autouse=True)
def isolated_storage(hass: HomeAssistant) -> Generator[None]:
    """Wipe `config/intentsity/` around each test.

    `pytest-homeassistant-custom-component` points every test at the same config
    directory, so a database or clip left behind would leak into the next test.
    """
    storage = db.get_storage_dir(hass)
    shutil.rmtree(storage, ignore_errors=True)
    try:
        yield
    finally:
        db.dispose_client(hass)
        shutil.rmtree(storage, ignore_errors=True)


@pytest.fixture
def clean_db(hass: HomeAssistant) -> Generator[None]:
    """An initialized, empty database for the duration of one test."""
    db.dispose_client(hass)
    db.get_db_path(hass).unlink(missing_ok=True)
    db.init_db(hass)
    try:
        yield
    finally:
        db.dispose_client(hass)


@pytest.fixture
async def assist_pipeline(hass: HomeAssistant) -> None:
    """Set up the dependencies Intentsity declares in its manifest.

    `conversation` needs `homeassistant.exposed_entities`, which the bare test
    harness does not set up, so loading it first keeps `assist_pipeline` — and
    therefore the whole integration — from failing its dependency check.
    """
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "assist_pipeline", {})


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """A config entry with the default capture options, added to hass."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Intentsity",
        data={},
        options=dict(DEFAULT_OPTIONS),
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def audio_format() -> AudioFormat:
    """The microWakeWord format: 16 kHz, 16-bit, mono."""
    return AudioFormat(sample_rate=16000, sample_width=2, channels=1)


@pytest.fixture
def make_pcm() -> Callable[[int, int], bytes]:
    """Build `frames` of deterministic little-endian PCM for one channel."""

    def _make(frames: int, start: int = 0, channels: int = 1) -> bytes:
        return np.arange(start, start + frames * channels, dtype="<i2").tobytes()

    return _make


@pytest.fixture
def add_clip(hass: HomeAssistant, clean_db: None) -> Callable[..., int]:
    """Insert a clip row, defaulting the fields a test does not care about."""
    counter = {"n": 0}
    base = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)

    def _add(**overrides) -> int:
        counter["n"] += 1
        index = counter["n"]
        fields: dict = {
            "filename": f"clip_{index:03d}.wav",
            "timestamp": base + timedelta(minutes=index),
            "assistant_id": "kitchen",
            "duration": 2.0,
            "sample_rate": 16000,
            "sample_width": 2,
            "channels": 1,
        }
        fields.update(overrides)
        return db.insert_clip(hass, Clip(**fields))

    return _add

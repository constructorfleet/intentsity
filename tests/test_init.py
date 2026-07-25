"""Setup, unload, reload, and the pieces `_async_initialize` wires together."""

from __future__ import annotations

import sqlite3
from typing import Any
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.intentsity import (
    PLATFORMS,
    _async_initialize,
    _import_legacy_clips,
    async_setup,
    async_unload_entry,
    db,
)
from custom_components.intentsity.capture import CaptureManager
from custom_components.intentsity.const import (
    AUDIO_KEY,
    CONF_MQTT_ENABLED,
    CONF_RETENTION_DAYS,
    CONF_UDP_ENABLED,
    COORDINATOR_KEY,
    DATA_API_REGISTERED,
    DATA_DB_INITIALIZED,
    DATA_UNSUBSCRIBE,
    DATA_WEBHOOK_ID,
    DOMAIN,
    PANEL_URL_PATH,
)


@pytest.fixture
def quiet_options() -> dict[str, Any]:
    """Options with both transports off, so setup binds no sockets."""
    from custom_components.intentsity.config_flow import DEFAULT_OPTIONS

    return {**DEFAULT_OPTIONS, CONF_UDP_ENABLED: False, CONF_MQTT_ENABLED: False}


@pytest.fixture
async def setup_entry(
    hass: HomeAssistant, assist_pipeline: None, quiet_options: dict[str, Any]
) -> MockConfigEntry:
    """A fully set-up config entry, torn down by `isolated_storage`."""
    entry = MockConfigEntry(domain=DOMAIN, title="Intentsity", data={}, options=quiet_options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_async_setup_is_a_noop(hass: HomeAssistant) -> None:
    assert await async_setup(hass, {}) is True


async def test_setup_entry_wires_everything_up(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    assert setup_entry.state is ConfigEntryState.LOADED

    domain_data = hass.data[DOMAIN]
    assert domain_data[DATA_DB_INITIALIZED] is True
    assert domain_data[DATA_API_REGISTERED] is True
    assert isinstance(domain_data[AUDIO_KEY], CaptureManager)
    assert COORDINATOR_KEY in domain_data
    assert db.get_db_path(hass).is_file()

    # The panel is registered, and the websocket commands with it.
    assert PANEL_URL_PATH in hass.data["frontend_panels"]
    from homeassistant.components import websocket_api

    assert "intentsity/clips/list" in hass.data[websocket_api.const.DOMAIN]

    # A random webhook ID is generated once and persisted on the entry.
    webhook_id = setup_entry.data[DATA_WEBHOOK_ID]
    assert webhook_id
    assert domain_data[DATA_WEBHOOK_ID] == webhook_id
    assert domain_data["webhook_url"] == f"/api/webhook/{webhook_id}"

    assert PLATFORMS == [Platform.SENSOR]
    assert hass.states.get("sensor.uncorrected_assist_chats") is not None
    assert hass.states.get("sensor.unlabeled_wake_clips") is not None


async def test_unload_entry_tears_everything_down(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    manager = hass.data[DOMAIN][AUDIO_KEY]
    webhook_id = setup_entry.data[DATA_WEBHOOK_ID]

    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    await hass.async_block_till_done()

    assert setup_entry.state is ConfigEntryState.NOT_LOADED
    assert DOMAIN not in hass.data
    assert manager.udp_running is False

    from homeassistant.components import webhook

    # Unregistering is idempotent from HA's side, but the ID must be gone.
    assert webhook.async_generate_path(webhook_id) == f"/api/webhook/{webhook_id}"


async def test_unload_entry_stops_the_prune_timer(
    hass: HomeAssistant, assist_pipeline: None, quiet_options: dict[str, Any]
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN, data={}, options={**quiet_options, CONF_RETENTION_DAYS: 7}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    unsubscribes: list[bool] = []
    hass.data[DOMAIN][DATA_UNSUBSCRIBE] = lambda: unsubscribes.append(True)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert unsubscribes == [True]


async def test_prune_is_scheduled_only_with_a_retention_window(
    hass: HomeAssistant, assist_pipeline: None, quiet_options: dict[str, Any]
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=quiet_options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert DATA_UNSUBSCRIBE not in hass.data[DOMAIN]


async def test_prune_timer_runs_the_prune(
    hass: HomeAssistant, assist_pipeline: None, quiet_options: dict[str, Any], add_clip
) -> None:
    from datetime import UTC, datetime, timedelta

    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    from custom_components.intentsity import PRUNE_INTERVAL
    from custom_components.intentsity.models import ClipListRequest

    entry = MockConfigEntry(
        domain=DOMAIN, data={}, options={**quiet_options, CONF_RETENTION_DAYS: 7}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    add_clip(filename="old.wav", timestamp=datetime.now(UTC) - timedelta(days=30))
    async_fire_time_changed(hass, datetime.now(UTC) + PRUNE_INTERVAL + timedelta(minutes=1))
    await hass.async_block_till_done()

    assert db.fetch_clips_page(hass, ClipListRequest(limit=10)).total == 0


async def test_unload_entry_reports_a_platform_failure(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    with patch.object(hass.config_entries, "async_unload_platforms", return_value=False):
        assert await async_unload_entry(hass, setup_entry) is False
    # Nothing was torn down, so the manager is still in place.
    assert AUDIO_KEY in hass.data[DOMAIN]


async def test_unload_entry_tolerates_a_bare_domain(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    # Dispose before dropping the domain data, or the engine outlives its only reference.
    await hass.async_add_executor_job(db.dispose_client, hass)
    hass.data[DOMAIN] = {}

    assert await async_unload_entry(hass, setup_entry) is True
    assert DOMAIN not in hass.data


async def test_options_update_reloads_the_entry(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    first_manager = hass.data[DOMAIN][AUDIO_KEY]

    hass.config_entries.async_update_entry(
        setup_entry, options={**setup_entry.options, CONF_RETENTION_DAYS: 21}
    )
    await hass.async_block_till_done()

    # A fresh manager means capture picked up the new audio settings.
    manager = hass.data[DOMAIN][AUDIO_KEY]
    assert manager is not first_manager
    assert manager.retention_days == 21


async def test_setup_reuses_the_existing_webhook_id(
    hass: HomeAssistant, assist_pipeline: None, quiet_options: dict[str, Any]
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN, data={DATA_WEBHOOK_ID: "already-issued"}, options=quiet_options
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.data[DATA_WEBHOOK_ID] == "already-issued"
    assert hass.data[DOMAIN]["webhook_url"] == "/api/webhook/already-issued"


async def test_webhook_captures_a_wake_event(
    hass: HomeAssistant, setup_entry: MockConfigEntry, hass_client_no_auth
) -> None:
    """A device posting to the webhook path reaches the capture manager."""
    manager = hass.data[DOMAIN][AUDIO_KEY]
    captured: list = []
    manager.async_capture_wake_event = lambda event: captured.append(event) or _noop()

    client = await hass_client_no_auth()
    response = await client.post(
        f"/api/webhook/{setup_entry.data[DATA_WEBHOOK_ID]}",
        json={"assistant_id": "kitchen", "wake_word": "okay_nabu"},
    )
    await hass.async_block_till_done()

    assert response.status == 202
    assert captured[0].assistant_id == "kitchen"


async def _noop() -> None:
    return None


async def test_initialize_registers_the_api_only_once(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    """Frontend, websocket, and view registration are global, so they happen once."""
    with (
        patch("custom_components.intentsity._async_register_webhook"),
        patch("custom_components.intentsity._async_register_frontend") as frontend,
        patch("custom_components.intentsity.websocket.async_register_commands") as commands,
        patch("custom_components.intentsity.intentsity_http.async_register_views") as views,
    ):
        await _async_initialize(hass, setup_entry)

    frontend.assert_not_called()
    commands.assert_not_called()
    views.assert_not_called()


async def test_initialize_reuses_the_database_and_coordinator(
    hass: HomeAssistant, setup_entry: MockConfigEntry
) -> None:
    coordinator = hass.data[DOMAIN][COORDINATOR_KEY]

    with (
        patch("custom_components.intentsity._async_register_webhook"),
        patch.object(db, "init_db") as init_db,
    ):
        await _async_initialize(hass, setup_entry)

    init_db.assert_not_called()
    assert hass.data[DOMAIN][COORDINATOR_KEY] is coordinator


# --- Legacy clip import ---------------------------------------------------


def _write_legacy_db(path, rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.executescript(
            """
            CREATE TABLE clips (
                id INTEGER PRIMARY KEY,
                filename TEXT,
                timestamp TEXT,
                label TEXT,
                assistant_id TEXT,
                deleted INTEGER DEFAULT 0
            );
            """
        )
        connection.executemany("INSERT INTO clips VALUES (?, ?, ?, ?, ?, ?)", rows)
        connection.commit()
    finally:
        connection.close()


@pytest.mark.parametrize("location", ["storage", "clips"])
async def test_import_legacy_clips_from_either_location(
    hass: HomeAssistant, clean_db: None, location: str
) -> None:
    from custom_components.intentsity.models import ClipListRequest

    base = db.get_storage_dir(hass) if location == "storage" else db.get_clips_dir(hass)
    _write_legacy_db(
        base / "clips.db",
        [(1, "legacy.wav", "2026-02-01T10:00:00+00:00", "Positive", "kitchen", 0)],
    )

    await hass.async_add_executor_job(_import_legacy_clips, hass)

    clips = db.fetch_clips_page(hass, ClipListRequest(limit=10)).clips
    assert [(clip.filename, clip.label) for clip in clips] == [("legacy.wav", "tp")]


async def test_import_legacy_clips_without_a_legacy_db(hass: HomeAssistant, clean_db: None) -> None:
    from custom_components.intentsity.models import ClipListRequest

    await hass.async_add_executor_job(_import_legacy_clips, hass)
    assert db.fetch_clips_page(hass, ClipListRequest(limit=10)).total == 0


async def test_import_legacy_clips_logs_an_unexpected_failure(
    hass: HomeAssistant, clean_db: None, caplog: pytest.LogCaptureFixture
) -> None:
    with patch.object(db, "import_legacy_clips", side_effect=RuntimeError("boom")):
        await hass.async_add_executor_job(_import_legacy_clips, hass)

    assert caplog.text.count("Failed to import legacy clips") == 2


async def test_setup_imports_legacy_clips_once(
    hass: HomeAssistant, assist_pipeline: None, quiet_options: dict[str, Any]
) -> None:
    from custom_components.intentsity.models import ClipListRequest

    _write_legacy_db(
        db.get_storage_dir(hass) / "clips.db",
        [(1, "legacy.wav", "2026-02-01T10:00:00+00:00", "Background Noise", "kitchen", 0)],
    )

    entry = MockConfigEntry(domain=DOMAIN, data={}, options=quiet_options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    clips = db.fetch_clips_page(hass, ClipListRequest(limit=10)).clips
    assert [(clip.filename, clip.label) for clip in clips] == [("legacy.wav", "bgnoise")]


# --- YAML setup -----------------------------------------------------------


async def test_yaml_config_schema_accepts_an_empty_block(
    hass: HomeAssistant, assist_pipeline: None
) -> None:
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()

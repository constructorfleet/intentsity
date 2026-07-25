"""Intentsity: wake-word annotation and Assist intent training in one panel.

Both surfaces are observational. Chat logging reads Assist pipeline debug data
and never intercepts the pipeline; audio capture buffers what devices send and
never talks back to them.
"""

from __future__ import annotations

from datetime import timedelta
import logging
from pathlib import Path
from random import randint

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
import voluptuous as vol

from . import db, websocket
from . import http as intentsity_http
from .capture import CaptureManager
from .const import (
    AUDIO_KEY,
    COORDINATOR_KEY,
    DATA_API_REGISTERED,
    DATA_DB_INITIALIZED,
    DATA_UNSUBSCRIBE,
    DATA_WEBHOOK_ID,
    DOMAIN,
    PANEL_URL_PATH,
)
from .coordinator import IntentsityCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {vol.Optional(DOMAIN): vol.Schema({})},
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = [Platform.SENSOR]

PRUNE_INTERVAL = timedelta(hours=12)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    await _async_initialize(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False

    domain_data = hass.data.get(DOMAIN, {})

    manager: CaptureManager | None = domain_data.pop(AUDIO_KEY, None)
    if manager is not None:
        await manager.async_stop()

    webhook_id = domain_data.pop(DATA_WEBHOOK_ID, None)
    if webhook_id:
        from homeassistant.components import webhook

        webhook.async_unregister(hass, webhook_id)

    unsubscribe = domain_data.pop(DATA_UNSUBSCRIBE, None)
    if unsubscribe is not None:
        unsubscribe()

    await hass.async_add_executor_job(db.dispose_client, hass)
    hass.data.pop(DOMAIN, None)
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options change so capture picks up new audio settings."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_initialize(hass: HomeAssistant, entry: ConfigEntry) -> None:
    domain_data = hass.data.setdefault(DOMAIN, {})

    if not domain_data.get(DATA_DB_INITIALIZED, False):
        await hass.async_add_executor_job(db.init_db, hass)
        await hass.async_add_executor_job(_import_legacy_clips, hass)
        domain_data[DATA_DB_INITIALIZED] = True

    if COORDINATOR_KEY not in domain_data:
        coordinator = IntentsityCoordinator(hass)
        domain_data[COORDINATOR_KEY] = coordinator
        await coordinator.async_config_entry_first_refresh()

    manager = CaptureManager(hass, dict(entry.options))
    domain_data[AUDIO_KEY] = manager
    await manager.async_start()

    await _async_register_webhook(hass, entry)

    if not domain_data.get(DATA_API_REGISTERED, False):
        await _async_register_frontend(hass)
        websocket.async_register_commands(hass)
        intentsity_http.async_register_views(hass)
        domain_data[DATA_API_REGISTERED] = True

    if manager.retention_days > 0:

        @callback
        def _schedule_prune(_now) -> None:
            hass.async_create_task(manager.async_prune())

        domain_data[DATA_UNSUBSCRIBE] = async_track_time_interval(
            hass, _schedule_prune, PRUNE_INTERVAL
        )


def _import_legacy_clips(hass: HomeAssistant) -> None:
    """Adopt clips from a previously installed wake-word add-on, if present.

    The add-on wrote to its own /data volume; a user who copies that directory
    into the config folder gets their labels carried over instead of restarting
    annotation from scratch.
    """
    for candidate in (
        db.get_storage_dir(hass) / "clips.db",
        db.get_clips_dir(hass) / "clips.db",
    ):
        try:
            imported = db.import_legacy_clips(hass, candidate)
        except Exception:
            _LOGGER.exception("Failed to import legacy clips from %s", candidate)
            continue
        if imported:
            _LOGGER.info("Imported %s clips from %s", imported, candidate)


async def _async_register_webhook(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register the wake-event webhook and remember its path for the panel."""
    from homeassistant.components import webhook

    webhook_id = entry.data.get(DATA_WEBHOOK_ID)
    if not webhook_id:
        webhook_id = webhook.async_generate_id()
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, DATA_WEBHOOK_ID: webhook_id}
        )

    async def _handle(hass_: HomeAssistant, received_id: str, request):
        return await intentsity_http.async_handle_wake_webhook(hass_, received_id, request)

    webhook.async_register(hass, DOMAIN, "Intentsity wake event", webhook_id, _handle)
    hass.data[DOMAIN][DATA_WEBHOOK_ID] = webhook_id
    hass.data[DOMAIN]["webhook_url"] = webhook.async_generate_path(webhook_id)


async def _async_register_frontend(hass: HomeAssistant) -> None:
    from homeassistant.components.frontend import async_register_built_in_panel

    module_dir = Path(__file__).parent
    version = randint(0, 999999)
    await hass.http.async_register_static_paths(
        [StaticPathConfig("/intentsity_panel.js", str(module_dir / "panel.js"), False)]
    )
    async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title="Intentsity",
        sidebar_icon="mdi:waveform",
        frontend_url_path=PANEL_URL_PATH,
        config={
            "_panel_custom": {
                "name": "intentsity-panel",
                "module_url": f"/intentsity_panel.js?v={version}",
            }
        },
        require_admin=True,
    )

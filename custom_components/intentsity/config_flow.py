"""Config and options flow. A single instance owns both surfaces."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    CONF_BUFFER_DURATION,
    CONF_CHANNELS,
    CONF_MQTT_AUDIO_INFO_TOPIC,
    CONF_MQTT_AUDIO_TOPIC,
    CONF_MQTT_ENABLED,
    CONF_MQTT_EVENT_TOPIC,
    CONF_POST_WAKE_DURATION,
    CONF_PRE_WAKE_DURATION,
    CONF_RETENTION_DAYS,
    CONF_SAMPLE_RATE,
    CONF_SAMPLE_WIDTH,
    CONF_UDP_ASSISTANT_ID,
    CONF_UDP_ENABLED,
    CONF_UDP_PORT,
    DEFAULT_BUFFER_DURATION,
    DEFAULT_CHANNELS,
    DEFAULT_MQTT_AUDIO_INFO_TOPIC,
    DEFAULT_MQTT_AUDIO_TOPIC,
    DEFAULT_MQTT_EVENT_TOPIC,
    DEFAULT_POST_WAKE_DURATION,
    DEFAULT_PRE_WAKE_DURATION,
    DEFAULT_RETENTION_DAYS,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_SAMPLE_WIDTH,
    DEFAULT_UDP_PORT,
    DOMAIN,
)

DEFAULT_OPTIONS: dict[str, Any] = {
    CONF_UDP_ENABLED: True,
    CONF_UDP_PORT: DEFAULT_UDP_PORT,
    CONF_UDP_ASSISTANT_ID: "",
    CONF_BUFFER_DURATION: DEFAULT_BUFFER_DURATION,
    CONF_PRE_WAKE_DURATION: DEFAULT_PRE_WAKE_DURATION,
    CONF_POST_WAKE_DURATION: DEFAULT_POST_WAKE_DURATION,
    CONF_SAMPLE_RATE: DEFAULT_SAMPLE_RATE,
    CONF_SAMPLE_WIDTH: DEFAULT_SAMPLE_WIDTH,
    CONF_CHANNELS: DEFAULT_CHANNELS,
    CONF_MQTT_ENABLED: True,
    CONF_MQTT_AUDIO_TOPIC: DEFAULT_MQTT_AUDIO_TOPIC,
    CONF_MQTT_EVENT_TOPIC: DEFAULT_MQTT_EVENT_TOPIC,
    CONF_MQTT_AUDIO_INFO_TOPIC: DEFAULT_MQTT_AUDIO_INFO_TOPIC,
    CONF_RETENTION_DAYS: DEFAULT_RETENTION_DAYS,
}


def _options_schema(current: dict[str, Any]) -> vol.Schema:
    def value(key: str) -> Any:
        return current.get(key, DEFAULT_OPTIONS[key])

    return vol.Schema(
        {
            vol.Required(CONF_UDP_ENABLED, default=value(CONF_UDP_ENABLED)): bool,
            vol.Required(CONF_UDP_PORT, default=value(CONF_UDP_PORT)): cv.port,
            vol.Optional(CONF_UDP_ASSISTANT_ID, default=value(CONF_UDP_ASSISTANT_ID)): str,
            vol.Required(CONF_BUFFER_DURATION, default=value(CONF_BUFFER_DURATION)): vol.All(
                vol.Coerce(float), vol.Range(min=5, max=300)
            ),
            vol.Required(CONF_PRE_WAKE_DURATION, default=value(CONF_PRE_WAKE_DURATION)): vol.All(
                vol.Coerce(float), vol.Range(min=0.5, max=10)
            ),
            vol.Required(CONF_POST_WAKE_DURATION, default=value(CONF_POST_WAKE_DURATION)): vol.All(
                vol.Coerce(float), vol.Range(min=0, max=30)
            ),
            vol.Required(CONF_SAMPLE_RATE, default=value(CONF_SAMPLE_RATE)): vol.All(
                vol.Coerce(int), vol.Range(min=8000, max=48000)
            ),
            vol.Required(CONF_SAMPLE_WIDTH, default=value(CONF_SAMPLE_WIDTH)): vol.In([1, 2, 4]),
            vol.Required(CONF_CHANNELS, default=value(CONF_CHANNELS)): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=8)
            ),
            vol.Required(CONF_MQTT_ENABLED, default=value(CONF_MQTT_ENABLED)): bool,
            vol.Required(CONF_MQTT_AUDIO_TOPIC, default=value(CONF_MQTT_AUDIO_TOPIC)): str,
            vol.Required(CONF_MQTT_EVENT_TOPIC, default=value(CONF_MQTT_EVENT_TOPIC)): str,
            vol.Required(
                CONF_MQTT_AUDIO_INFO_TOPIC, default=value(CONF_MQTT_AUDIO_INFO_TOPIC)
            ): str,
            vol.Required(CONF_RETENTION_DAYS, default=value(CONF_RETENTION_DAYS)): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=3650)
            ),
        }
    )


class IntentsityConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Intentsity config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

        return self.async_create_entry(title="Intentsity", data={}, options=dict(DEFAULT_OPTIONS))

    async def async_step_import(
        self, import_config: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="Intentsity", data={}, options=dict(DEFAULT_OPTIONS))

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> IntentsityOptionsFlow:
        return IntentsityOptionsFlow()


class IntentsityOptionsFlow(config_entries.OptionsFlow):
    """Audio capture options. Changing any of them reloads the entry."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(dict(self.config_entry.options)),
        )

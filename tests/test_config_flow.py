"""Config and options flow. One instance owns both surfaces."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
import voluptuous as vol

from custom_components.intentsity.config_flow import (
    DEFAULT_OPTIONS,
    IntentsityOptionsFlow,
    _options_schema,
)
from custom_components.intentsity.const import (
    CONF_BUFFER_DURATION,
    CONF_CHANNELS,
    CONF_MQTT_ENABLED,
    CONF_POST_WAKE_DURATION,
    CONF_PRE_WAKE_DURATION,
    CONF_RETENTION_DAYS,
    CONF_SAMPLE_RATE,
    CONF_SAMPLE_WIDTH,
    CONF_UDP_ENABLED,
    CONF_UDP_PORT,
    DOMAIN,
)


async def test_user_flow_shows_a_form_then_creates_the_entry(
    hass: HomeAssistant, assist_pipeline: None
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Intentsity"
    assert result["data"] == {}
    assert result["options"] == DEFAULT_OPTIONS


async def test_user_flow_allows_only_one_instance(
    hass: HomeAssistant, assist_pipeline: None, config_entry: MockConfigEntry
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_import_flow_creates_the_entry(hass: HomeAssistant, assist_pipeline: None) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"] == DEFAULT_OPTIONS


async def test_import_flow_allows_only_one_instance(
    hass: HomeAssistant, assist_pipeline: None, config_entry: MockConfigEntry
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow_round_trip(
    hass: HomeAssistant, assist_pipeline: None, config_entry: MockConfigEntry
) -> None:
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    submitted = {
        **DEFAULT_OPTIONS,
        CONF_UDP_PORT: 7001,
        CONF_PRE_WAKE_DURATION: 1.0,
        CONF_MQTT_ENABLED: False,
        CONF_RETENTION_DAYS: 30,
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=submitted
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_UDP_PORT] == 7001
    assert result["data"][CONF_RETENTION_DAYS] == 30


async def test_options_flow_is_returned_by_the_config_flow(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    from custom_components.intentsity.config_flow import IntentsityConfigFlow

    flow = IntentsityConfigFlow.async_get_options_flow(config_entry)
    assert isinstance(flow, IntentsityOptionsFlow)


def test_options_schema_defaults_to_current_values() -> None:
    schema = _options_schema({CONF_UDP_PORT: 7002, CONF_UDP_ENABLED: False})
    validated = schema({})

    assert validated[CONF_UDP_PORT] == 7002
    assert validated[CONF_UDP_ENABLED] is False
    # Keys the stored options do not have fall back to the shipped defaults.
    assert validated[CONF_BUFFER_DURATION] == DEFAULT_OPTIONS[CONF_BUFFER_DURATION]


def test_options_schema_coerces_numeric_strings() -> None:
    validated = _options_schema({})(
        {CONF_SAMPLE_RATE: "48000", CONF_CHANNELS: "2", CONF_PRE_WAKE_DURATION: "1.5"}
    )
    assert validated[CONF_SAMPLE_RATE] == 48000
    assert validated[CONF_CHANNELS] == 2
    assert validated[CONF_PRE_WAKE_DURATION] == 1.5


@pytest.mark.parametrize(
    "user_input",
    [
        {CONF_UDP_PORT: 0},
        {CONF_UDP_PORT: 70000},
        {CONF_BUFFER_DURATION: 1},
        {CONF_BUFFER_DURATION: 500},
        {CONF_PRE_WAKE_DURATION: 0},
        {CONF_PRE_WAKE_DURATION: 20},
        {CONF_POST_WAKE_DURATION: -1},
        {CONF_POST_WAKE_DURATION: 31},
        {CONF_SAMPLE_RATE: 4000},
        {CONF_SAMPLE_RATE: 96000},
        {CONF_SAMPLE_WIDTH: 3},
        {CONF_CHANNELS: 0},
        {CONF_CHANNELS: 9},
        {CONF_RETENTION_DAYS: -1},
        {CONF_RETENTION_DAYS: 4000},
    ],
)
def test_options_schema_rejects_out_of_range_values(user_input: dict) -> None:
    with pytest.raises(vol.Invalid):
        _options_schema({})(user_input)


def test_default_options_cover_every_schema_key() -> None:
    """`_options_schema` indexes DEFAULT_OPTIONS directly, so a gap would KeyError."""
    keys = {str(key.schema) for key in _options_schema({}).schema}
    assert keys == set(DEFAULT_OPTIONS)

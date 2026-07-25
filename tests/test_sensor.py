"""Review-queue sensors."""

from __future__ import annotations

from homeassistant.components.sensor import SensorStateClass
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.intentsity.const import COORDINATOR_KEY, DOMAIN
from custom_components.intentsity.coordinator import IntentsityCoordinator
from custom_components.intentsity.sensor import (
    UncorrectedChatsSensor,
    UnlabeledClipsSensor,
    async_setup_entry,
)


async def test_async_setup_entry_adds_both_sensors(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    coordinator = IntentsityCoordinator(hass)
    coordinator.data = {"uncorrected_count": 3, "unlabeled_clips": 7}
    hass.data.setdefault(DOMAIN, {})[COORDINATOR_KEY] = coordinator

    added: list = []
    await async_setup_entry(hass, config_entry, lambda entities, _refresh: added.extend(entities))

    assert [type(entity) for entity in added] == [UncorrectedChatsSensor, UnlabeledClipsSensor]
    assert [entity.native_value for entity in added] == [3, 7]


async def test_sensor_attributes(hass: HomeAssistant) -> None:
    coordinator = IntentsityCoordinator(hass)
    chats = UncorrectedChatsSensor(coordinator)
    clips = UnlabeledClipsSensor(coordinator)

    assert chats.unique_id == "intentsity_uncorrected_chats"
    assert chats.name == "Uncorrected Assist Chats"
    assert chats.icon == "mdi:message-alert"
    assert clips.unique_id == "intentsity_unlabeled_clips"
    assert clips.name == "Unlabeled Wake Clips"
    assert clips.icon == "mdi:waveform"
    assert chats.state_class is SensorStateClass.MEASUREMENT


async def test_sensors_read_zero_before_the_first_refresh(hass: HomeAssistant) -> None:
    coordinator = IntentsityCoordinator(hass)
    assert coordinator.data is None
    assert UncorrectedChatsSensor(coordinator).native_value == 0
    assert UnlabeledClipsSensor(coordinator).native_value == 0


async def test_sensors_read_zero_for_a_missing_key(hass: HomeAssistant) -> None:
    coordinator = IntentsityCoordinator(hass)
    coordinator.data = {}
    assert UncorrectedChatsSensor(coordinator).native_value == 0

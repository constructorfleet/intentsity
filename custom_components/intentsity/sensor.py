"""Review-queue sensors for both surfaces."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR_KEY, DOMAIN
from .coordinator import IntentsityCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: IntentsityCoordinator = hass.data[DOMAIN][COORDINATOR_KEY]
    async_add_entities(
        [
            UncorrectedChatsSensor(coordinator),
            UnlabeledClipsSensor(coordinator),
        ],
        True,
    )


class _IntentsityQueueSensor(CoordinatorEntity[IntentsityCoordinator], SensorEntity):
    """Base for count-of-pending-review sensors."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _data_key: str

    @property
    def native_value(self) -> int:
        return int((self.coordinator.data or {}).get(self._data_key, 0))


class UncorrectedChatsSensor(_IntentsityQueueSensor):
    _attr_name = "Uncorrected Assist Chats"
    _attr_unique_id = f"{DOMAIN}_uncorrected_chats"
    _attr_icon = "mdi:message-alert"
    _data_key = "uncorrected_count"


class UnlabeledClipsSensor(_IntentsityQueueSensor):
    _attr_name = "Unlabeled Wake Clips"
    _attr_unique_id = f"{DOMAIN}_unlabeled_clips"
    _attr_icon = "mdi:waveform"
    _data_key = "unlabeled_clips"

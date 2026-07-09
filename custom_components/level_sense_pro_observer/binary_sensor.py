"""Binary sensor entities for Level Sense Pro Observer."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DATA_COORDINATOR,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DOMAIN,
)
from .coordinator import LevelSenseCoordinator


@dataclass(frozen=True, slots=True)
class LevelSenseBinarySensorDescription:
    """Description for a Level Sense binary sensor."""

    key: str
    name: str
    value_fn: Callable[[LevelSenseCoordinator], bool | None]
    icon: str | None = None


BINARY_SENSORS: tuple[LevelSenseBinarySensorDescription, ...] = (
    LevelSenseBinarySensorDescription(
        key="relay_state",
        name="Relay State",
        value_fn=lambda coordinator: coordinator.state.telemetry.relay_state,
        icon="mdi:electric-switch",
    ),
    LevelSenseBinarySensorDescription(
        key="siren_state",
        name="Siren State",
        value_fn=lambda coordinator: coordinator.state.telemetry.siren_state,
        icon="mdi:alarm-light-outline",
    ),
    LevelSenseBinarySensorDescription(
        key="device_state",
        name="Device State",
        value_fn=lambda coordinator: coordinator.state.telemetry.device_state,
        icon="mdi:water-alert-outline",
    ),
    LevelSenseBinarySensorDescription(
        key="alarm_silence",
        name="Alarm Silence",
        value_fn=lambda coordinator: coordinator.state.telemetry.alarm_silence,
        icon="mdi:bell-off-outline",
    ),
    LevelSenseBinarySensorDescription(
        key="debug_mode",
        name="Debug Mode",
        value_fn=lambda coordinator: coordinator.state.telemetry.debug_mode,
        icon="mdi:bug-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Level Sense binary sensor entities."""
    coordinator: LevelSenseCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities = [
        LevelSenseBinarySensor(entry, coordinator, description)
        for description in BINARY_SENSORS
    ]
    async_add_entities(entities)


class LevelSenseBinarySensor(BinarySensorEntity):
    """Level Sense binary sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: LevelSenseCoordinator,
        description: LevelSenseBinarySensorDescription,
    ) -> None:
        """Initialize binary sensor."""
        self._entry = entry
        self._coordinator = coordinator
        self._description = description

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_icon = description.icon

    async def async_added_to_hass(self) -> None:
        """Register coordinator listener."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        """Return binary sensor state."""
        return self._description.value_fn(self._coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return common attributes."""
        state = self._coordinator.state
        stats = state.statistics
        network = state.network

        return {
            "client_ip": network.client_ip,
            "device_id": network.device_id,
            "mac": network.mac,
            "user_agent": network.user_agent,
            "packet_count": stats.packet_count,
            "last_error": stats.last_error,
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
            name=DEVICE_NAME,
        )
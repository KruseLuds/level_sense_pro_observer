"""Sensor entities for Level Sense Pro Observer."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricPotential,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_SHOW_RAW_SENSORS,
    DATA_COORDINATOR,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DOMAIN,
)
from .coordinator import LevelSenseCoordinator


@dataclass(frozen=True, slots=True)
class LevelSenseSensorDescription:
    """Description for a Level Sense sensor."""

    key: str
    name: str
    value_fn: Callable[[LevelSenseCoordinator], Any]
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    native_unit_of_measurement: str | None = None
    icon: str | None = None
    raw: bool = False


def _raw_value(key: str, index: int | None = None) -> Callable[[LevelSenseCoordinator], Any]:
    """Return a raw payload value function."""

    def value_fn(coordinator: LevelSenseCoordinator) -> Any:
        payload = coordinator.state.telemetry.raw_payload
        value = payload.get(key)

        if index is not None:
            if not isinstance(value, list) or len(value) <= index:
                return None
            value = value[index]

        try:
            number = float(value)
            if number.is_integer():
                return int(number)
            return round(number, 3)
        except (TypeError, ValueError):
            return value

    return value_fn


SENSORS: tuple[LevelSenseSensorDescription, ...] = (
    LevelSenseSensorDescription(
        key="temperature",
        name="Temperature",
        value_fn=lambda coordinator: coordinator.state.telemetry.temperature_c,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    LevelSenseSensorDescription(
        key="humidity",
        name="Humidity",
        value_fn=lambda coordinator: coordinator.state.telemetry.humidity,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    LevelSenseSensorDescription(
        key="battery_voltage",
        name="Battery Voltage",
        value_fn=lambda coordinator: coordinator.state.telemetry.battery_voltage,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    LevelSenseSensorDescription(
        key="rssi",
        name="RSSI",
        value_fn=lambda coordinator: coordinator.state.telemetry.rssi,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    ),
    LevelSenseSensorDescription(
        key="runtime",
        name="Runtime",
        value_fn=lambda coordinator: coordinator.state.telemetry.runtime_seconds,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        icon="mdi:timer-outline",
    ),
    LevelSenseSensorDescription(
        key="packet_count",
        name="Packet Count",
        value_fn=lambda coordinator: coordinator.state.statistics.packet_count,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
    ),
    LevelSenseSensorDescription(
        key="last_seen",
        name="Last Seen",
        value_fn=lambda coordinator: coordinator.state.statistics.last_seen,
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-check-outline",
    ),
    LevelSenseSensorDescription(
        key="cloud_status",
        name="Cloud Status",
        value_fn=lambda coordinator: coordinator.state.cloud.status_code,
        icon="mdi:cloud-check-outline",
    ),
    LevelSenseSensorDescription(
        key="cloud_result",
        name="Cloud Result",
        value_fn=lambda coordinator: coordinator.state.cloud.result,
        icon="mdi:cloud-check-variant-outline",
    ),
    LevelSenseSensorDescription(
        key="cloud_has_config_update",
        name="Cloud Has Config Update",
        value_fn=lambda coordinator: coordinator.state.cloud.has_config_update,
        icon="mdi:cloud-sync-outline",
    ),
    LevelSenseSensorDescription(
        key="cloud_latency",
        name="Cloud Latency",
        value_fn=lambda coordinator: coordinator.state.cloud.latency_ms,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="ms",
        icon="mdi:timer-sand",
    ),
)

RAW_SENSORS: tuple[LevelSenseSensorDescription, ...] = (
    LevelSenseSensorDescription("raw_sample_elapsed_ms", "Raw Sample Elapsed MS", _raw_value("sample_elapsed_ms"), native_unit_of_measurement="ms", icon="mdi:timer-outline", raw=True),
    LevelSenseSensorDescription("raw_run_t", "Raw Run T", _raw_value("run_t"), native_unit_of_measurement="s", icon="mdi:timer-outline", raw=True),
    LevelSenseSensorDescription("raw_relay_state", "Raw Relay State", _raw_value("relay_state"), icon="mdi:electric-switch", raw=True),
    LevelSenseSensorDescription("raw_device_state", "Raw Device State", _raw_value("device_state"), icon="mdi:water-alert-outline", raw=True),
    LevelSenseSensorDescription("raw_siren_state", "Raw Siren State", _raw_value("siren_state"), icon="mdi:alarm-light-outline", raw=True),
    LevelSenseSensorDescription("raw_alarm_silence", "Raw Alarm Silence", _raw_value("alarm_silence"), icon="mdi:bell-off-outline", raw=True),
    LevelSenseSensorDescription("raw_cap_sense_1", "Raw Cap Sense 1", _raw_value("cap_sense", 0), icon="mdi:format-list-numbered", raw=True),
    LevelSenseSensorDescription("raw_cap_sense_2", "Raw Cap Sense 2", _raw_value("cap_sense", 1), icon="mdi:format-list-numbered", raw=True),
    LevelSenseSensorDescription("raw_cap_sense_3", "Raw Cap Sense 3", _raw_value("cap_sense", 2), icon="mdi:format-list-numbered", raw=True),
    LevelSenseSensorDescription("raw_cycle_count_1", "Raw Cycle Count 1", _raw_value("cycle_count", 0), icon="mdi:counter", raw=True),
    LevelSenseSensorDescription("raw_cycle_count_2", "Raw Cycle Count 2", _raw_value("cycle_count", 1), icon="mdi:counter", raw=True),
    LevelSenseSensorDescription("raw_cycle_count_3", "Raw Cycle Count 3", _raw_value("cycle_count", 2), icon="mdi:counter", raw=True),
    LevelSenseSensorDescription("raw_tempc_1", "Raw Temperature C 1", _raw_value("tempc", 0), device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfTemperature.CELSIUS, raw=True),
    LevelSenseSensorDescription("raw_tempc_2", "Raw Temperature C 2", _raw_value("tempc", 1), device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfTemperature.CELSIUS, raw=True),
    LevelSenseSensorDescription("raw_tempc_3", "Raw Temperature C 3", _raw_value("tempc", 2), device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfTemperature.CELSIUS, raw=True),
    LevelSenseSensorDescription("raw_rh_1", "Raw Humidity 1", _raw_value("rh", 0), device_class=SensorDeviceClass.HUMIDITY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, raw=True),
    LevelSenseSensorDescription("raw_rh_2", "Raw Humidity 2", _raw_value("rh", 1), device_class=SensorDeviceClass.HUMIDITY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, raw=True),
    LevelSenseSensorDescription("raw_rh_3", "Raw Humidity 3", _raw_value("rh", 2), device_class=SensorDeviceClass.HUMIDITY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, raw=True),
    LevelSenseSensorDescription("raw_battvdc_1", "Raw Battery VDC 1", _raw_value("battvdc", 0), device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, raw=True),
    LevelSenseSensorDescription("raw_battvdc_2", "Raw Battery VDC 2", _raw_value("battvdc", 1), device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, raw=True),
    LevelSenseSensorDescription("raw_battvdc_3", "Raw Battery VDC 3", _raw_value("battvdc", 2), device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, raw=True),
    LevelSenseSensorDescription("raw_input1_1", "Raw Input 1 1", _raw_value("input1", 0), icon="mdi:counter", raw=True),
    LevelSenseSensorDescription("raw_input1_2", "Raw Input 1 2", _raw_value("input1", 1), icon="mdi:counter", raw=True),
    LevelSenseSensorDescription("raw_input1_3", "Raw Input 1 3", _raw_value("input1", 2), icon="mdi:counter", raw=True),
    LevelSenseSensorDescription("raw_input2_1", "Raw Input 2 1", _raw_value("input2", 0), icon="mdi:counter", raw=True),
    LevelSenseSensorDescription("raw_input2_2", "Raw Input 2 2", _raw_value("input2", 1), icon="mdi:counter", raw=True),
    LevelSenseSensorDescription("raw_input2_3", "Raw Input 2 3", _raw_value("input2", 2), icon="mdi:counter", raw=True),
    LevelSenseSensorDescription("raw_rssi_1", "Raw RSSI 1", _raw_value("rssi", 0), device_class=SensorDeviceClass.SIGNAL_STRENGTH, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT, raw=True),
    LevelSenseSensorDescription("raw_rssi_2", "Raw RSSI 2", _raw_value("rssi", 1), device_class=SensorDeviceClass.SIGNAL_STRENGTH, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT, raw=True),
    LevelSenseSensorDescription("raw_rssi_3", "Raw RSSI 3", _raw_value("rssi", 2), device_class=SensorDeviceClass.SIGNAL_STRENGTH, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT, raw=True),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Level Sense sensor entities."""
    coordinator: LevelSenseCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    show_raw_sensors = entry.options.get(
        CONF_SHOW_RAW_SENSORS,
        entry.data.get(CONF_SHOW_RAW_SENSORS, False),
    )

    descriptions = list(SENSORS)
    if show_raw_sensors:
        descriptions.extend(RAW_SENSORS)

    async_add_entities(
        LevelSenseSensor(entry, coordinator, description)
        for description in descriptions
    )


class LevelSenseSensor(SensorEntity):
    """Level Sense sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: LevelSenseCoordinator,
        description: LevelSenseSensorDescription,
    ) -> None:
        """Initialize sensor."""
        self._entry = entry
        self._coordinator = coordinator
        self._description = description

        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
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
    def native_value(self) -> Any:
        """Return native value."""
        return self._description.value_fn(self._coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return common attributes."""
        state = self._coordinator.state
        telemetry = state.telemetry
        stats = state.statistics
        network = state.network
        cloud = state.cloud

        attrs: dict[str, Any] = {
            "client_ip": network.client_ip,
            "device_id": network.device_id,
            "mac": network.mac,
            "user_agent": network.user_agent,
            "packet_count": stats.packet_count,
            "last_error": stats.last_error,
            "unknown_field_count": len(telemetry.unknown_fields),
            "raw_sensor": self._description.raw,
        }

        if stats.first_seen is not None:
            attrs["first_seen"] = stats.first_seen.isoformat()
        if stats.last_seen is not None:
            attrs["last_seen"] = stats.last_seen.isoformat()
        if cloud.last_response_at is not None:
            attrs["last_cloud_response_at"] = cloud.last_response_at.isoformat()

        if self._description.key == "temperature":
            attrs["temperature_raw_c"] = telemetry.temperature_raw_c
            attrs["temperature_raw_f"] = telemetry.temperature_raw_f
            attrs["temperature_corrected_f"] = telemetry.temperature_corrected_f
            attrs["correction_offset_c"] = 3.61

        if self._description.raw:
            attrs["source"] = "raw_payload"

        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
            name=DEVICE_NAME,
        )
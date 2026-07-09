"""Typed runtime data model for Level Sense Pro Observer.

The observer receives raw JSON from the Level Sense Pro, forwards the original
HTTP request to the vendor cloud, and exposes selected values to Home Assistant.

This file defines the integration's internal state model. The rest of the
integration should avoid passing loosely shaped dictionaries around whenever a
structured state object is a better fit.

The model is split into four sections:

* ``DeviceTelemetry`` for parsed device values.
* ``NetworkState`` for metadata from the incoming device request.
* ``CloudState`` for metadata from the vendor cloud response.
* ``StatisticsState`` for observer runtime statistics.

The dataclasses also support serialization and restoration so the integration
can persist the last known state across Home Assistant restarts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


def _dt_to_str(value: datetime | None) -> str | None:
    """Convert a datetime to an ISO string for storage and diagnostics."""
    if value is None:
        return None
    return value.isoformat()


def _dt_from_str(value: Any) -> datetime | None:
    """Convert an ISO string back to a timezone-aware datetime."""
    if not value:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)

    return parsed


@dataclass(slots=True)
class DeviceTelemetry:
    """Parsed telemetry from one observed Level Sense Pro packet.

    The raw device payload is preserved in ``raw_payload`` so diagnostics and
    optional raw sensors can expose every value the device sent, even if the
    integration only promotes a small subset to normal Home Assistant entities.

    ``unknown_fields`` intentionally captures protocol fields that were not
    known at the time this parser was written. That helps detect vendor firmware
    changes without losing information.
    """

    temperature_c: float | None = None
    temperature_raw_c: float | None = None
    temperature_raw_f: float | None = None
    temperature_corrected_f: float | None = None
    humidity: float | None = None
    battery_voltage: float | None = None
    rssi: float | None = None
    sample_elapsed_seconds: float | None = None
    runtime_seconds: int | None = None
    relay_state: bool | None = None
    siren_state: bool | None = None
    device_state: bool | None = None
    alarm_silence: bool | None = None
    debug_mode: bool | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
    unknown_fields: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> DeviceTelemetry:
        """Create telemetry from restored storage data."""
        if not isinstance(data, dict):
            return cls()
        return cls(**{key: data.get(key) for key in cls.__dataclass_fields__})


@dataclass(slots=True)
class NetworkState:
    """Metadata learned from the incoming HTTP request.

    The Level Sense Pro IP address is not configured by the user. It is learned
    passively from the TCP peer address whenever the device connects to the
    proxy. This keeps DHCP changes from requiring integration changes.
    """

    client_ip: str | None = None
    device_id: str | None = None
    mac: str | None = None
    user_agent: str | None = None
    method: str | None = None
    request_path: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> NetworkState:
        """Create network state from restored storage data."""
        if not isinstance(data, dict):
            return cls()
        return cls(**{key: data.get(key) for key in cls.__dataclass_fields__})


@dataclass(slots=True)
class CloudState:
    """Metadata learned from the vendor cloud response."""

    status_code: str | None = None
    status_line: str | None = None
    result: str | None = None
    has_config_update: int | None = None
    body: dict[str, Any] | str | None = None
    latency_ms: float | None = None
    last_response_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> CloudState:
        """Create cloud state from restored storage data."""
        if not isinstance(data, dict):
            return cls()

        return cls(
            status_code=data.get("status_code"),
            status_line=data.get("status_line"),
            result=data.get("result"),
            has_config_update=data.get("has_config_update"),
            body=data.get("body"),
            latency_ms=data.get("latency_ms"),
            last_response_at=_dt_from_str(data.get("last_response_at")),
        )


@dataclass(slots=True)
class StatisticsState:
    """Observer runtime statistics."""

    packet_count: int = 0
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    last_error: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> StatisticsState:
        """Create statistics from restored storage data."""
        if not isinstance(data, dict):
            return cls()

        return cls(
            packet_count=int(data.get("packet_count") or 0),
            first_seen=_dt_from_str(data.get("first_seen")),
            last_seen=_dt_from_str(data.get("last_seen")),
            last_error=data.get("last_error"),
        )


@dataclass(slots=True)
class LevelSenseState:
    """Complete current state for one observed Level Sense Pro."""

    telemetry: DeviceTelemetry = field(default_factory=DeviceTelemetry)
    network: NetworkState = field(default_factory=NetworkState)
    cloud: CloudState = field(default_factory=CloudState)
    statistics: StatisticsState = field(default_factory=StatisticsState)

    def as_dict(self) -> dict[str, Any]:
        """Return a storage and diagnostics friendly dictionary."""
        data = asdict(self)
        data["cloud"]["last_response_at"] = _dt_to_str(self.cloud.last_response_at)
        data["statistics"]["first_seen"] = _dt_to_str(self.statistics.first_seen)
        data["statistics"]["last_seen"] = _dt_to_str(self.statistics.last_seen)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> LevelSenseState:
        """Create complete state from restored storage data."""
        if not isinstance(data, dict):
            return cls()

        return cls(
            telemetry=DeviceTelemetry.from_dict(data.get("telemetry")),
            network=NetworkState.from_dict(data.get("network")),
            cloud=CloudState.from_dict(data.get("cloud")),
            statistics=StatisticsState.from_dict(data.get("statistics")),
        )

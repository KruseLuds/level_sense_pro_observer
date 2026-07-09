"""Diagnostics support for Level Sense Pro Observer.

Diagnostics are intentionally rich because this integration is designed around
observing a protocol rather than replacing a cloud API. A useful diagnostics
file should show what the proxy observed, how DNS was resolved, what the cloud
returned, and which protocol fields are currently unknown.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_DNS_RESOLVER, DATA_RUNTIME, DOMAIN
from .dns import LevelSenseDNSResolver
from .runtime import LevelSenseRuntime


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for one config entry."""
    runtime: LevelSenseRuntime = hass.data[DOMAIN][entry.entry_id][DATA_RUNTIME]
    dns_resolver: LevelSenseDNSResolver | None = hass.data[DOMAIN][entry.entry_id].get(
        DATA_DNS_RESOLVER
    )

    return {
        "entry": {
            "title": entry.title,
            "domain": entry.domain,
            "version": entry.version,
            "data": _redact_entry_data(dict(entry.data)),
            "options": dict(entry.options),
        },
        "dns": dns_resolver.diagnostics() if dns_resolver else {},
        "state": _serialize(runtime.state),
    }


def _redact_entry_data(data: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive config entry values if they are ever added later."""
    redacted = dict(data)

    for key in ("password", "token", "api_key", "secret"):
        if key in redacted:
            redacted[key] = "**REDACTED**"

    return redacted


def _serialize(value: Any) -> Any:
    """Convert dataclasses, datetimes, and containers into JSON-safe values."""
    if isinstance(value, datetime):
        return value.isoformat()

    if hasattr(value, "__dataclass_fields__"):
        return {
            key: _serialize(item)
            for key, item in asdict(value).items()
        }

    if isinstance(value, dict):
        return {
            str(key): _serialize(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_serialize(item) for item in value]

    if isinstance(value, tuple):
        return [_serialize(item) for item in value]

    return value

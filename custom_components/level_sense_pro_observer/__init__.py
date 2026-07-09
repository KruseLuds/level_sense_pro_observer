"""Set up Level Sense Pro Observer.

Level Sense Pro Observer is intentionally a passive Home Assistant integration.
It accepts the HTTP traffic redirected from a Level Sense Pro device, forwards the
traffic to the vendor cloud, and exposes observed telemetry as Home Assistant
entities.

The integration does not poll the device, does not call a vendor API, and does
not modify payloads. The manufacturer's website, notifications, and firmware
behavior should continue to work because the cloud request and response are
forwarded unchanged except for the upstream TCP destination and Host header
handling required by the local DNS rewrite design.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_LISTEN_HOST,
    CONF_LISTEN_PORT,
    CONF_LOG_PAYLOADS,
    CONF_SHOW_RAW_SENSORS,
    CONF_UPSTREAM_HOST,
    CONF_UPSTREAM_HOST_HEADER,
    CONF_UPSTREAM_PORT,
    DATA_COORDINATOR,
    DATA_DNS_RESOLVER,
    DATA_PROXY,
    DATA_RUNTIME,
    DEFAULT_LISTEN_HOST,
    DEFAULT_LISTEN_PORT,
    DEFAULT_UPSTREAM_HOST,
    DEFAULT_UPSTREAM_HOST_HEADER,
    DEFAULT_UPSTREAM_PORT,
    DOMAIN,
)
from .coordinator import LevelSenseCoordinator
from .dns import LevelSenseDNSResolver
from .proxy import LevelSenseProxy
from .runtime import LevelSenseRuntime

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_LISTEN_HOST, default=DEFAULT_LISTEN_HOST): cv.string,
                vol.Optional(CONF_LISTEN_PORT, default=DEFAULT_LISTEN_PORT): cv.port,
                vol.Optional(CONF_UPSTREAM_HOST, default=DEFAULT_UPSTREAM_HOST): cv.string,
                vol.Optional(CONF_UPSTREAM_PORT, default=DEFAULT_UPSTREAM_PORT): cv.port,
                vol.Optional(
                    CONF_UPSTREAM_HOST_HEADER,
                    default=DEFAULT_UPSTREAM_HOST_HEADER,
                ): cv.string,
                vol.Optional(CONF_LOG_PAYLOADS, default=False): cv.boolean,
                vol.Optional(CONF_SHOW_RAW_SENSORS, default=False): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Import YAML configuration into a config entry when present.

    The integration is now a native config-entry integration, but YAML import is
    retained so early testers can migrate without manually recreating settings.
    Once imported, users can remove the YAML block and manage the integration
    through Settings, Devices & services.
    """
    if DOMAIN not in config:
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data=dict(config[DOMAIN]),
        )
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one Level Sense Pro Observer config entry."""
    data = dict(entry.data)
    options = dict(entry.options)

    listen_host = data.get(CONF_LISTEN_HOST, DEFAULT_LISTEN_HOST)
    listen_port = data.get(CONF_LISTEN_PORT, DEFAULT_LISTEN_PORT)
    upstream_host = data.get(CONF_UPSTREAM_HOST, DEFAULT_UPSTREAM_HOST)
    upstream_port = data.get(CONF_UPSTREAM_PORT, DEFAULT_UPSTREAM_PORT)
    upstream_host_header = data.get(
        CONF_UPSTREAM_HOST_HEADER,
        DEFAULT_UPSTREAM_HOST_HEADER,
    )

    log_payloads = options.get(CONF_LOG_PAYLOADS, data.get(CONF_LOG_PAYLOADS, False))
    show_raw_sensors = options.get(
        CONF_SHOW_RAW_SENSORS,
        data.get(CONF_SHOW_RAW_SENSORS, False),
    )

    runtime = LevelSenseRuntime()
    coordinator = LevelSenseCoordinator(hass, runtime, entry.entry_id)
    await coordinator.async_load()

    dns_resolver = LevelSenseDNSResolver(
        hass=hass,
        hostname=upstream_host_header,
        listen_host=listen_host,
    )

    proxy = LevelSenseProxy(
        coordinator=coordinator,
        dns_resolver=dns_resolver,
        listen_host=listen_host,
        listen_port=listen_port,
        upstream_host=upstream_host,
        upstream_port=upstream_port,
        upstream_host_header=upstream_host_header,
        log_payloads=log_payloads,
        show_raw_sensors=show_raw_sensors,
    )

    await proxy.async_start()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_RUNTIME: runtime,
        DATA_COORDINATOR: coordinator,
        DATA_PROXY: proxy,
        DATA_DNS_RESOLVER: dns_resolver,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info(
        "Level Sense Pro Observer started on %s:%s and forwarding to %s:%s with Host header %s",
        listen_host,
        listen_port,
        proxy.connect_host_description,
        upstream_port,
        upstream_host_header,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload one Level Sense Pro Observer config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    domain_data = hass.data.get(DOMAIN, {})
    entry_data = domain_data.pop(entry.entry_id, None)

    if entry_data:
        coordinator: LevelSenseCoordinator | None = entry_data.get(DATA_COORDINATOR)
        if coordinator is not None:
            await coordinator.async_save()

        proxy: LevelSenseProxy | None = entry_data.get(DATA_PROXY)
        if proxy is not None:
            await proxy.async_stop()

    return unload_ok

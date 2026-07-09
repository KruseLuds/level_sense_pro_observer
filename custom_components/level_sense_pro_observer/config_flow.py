"""Config flow for Level Sense Pro Observer.

The config flow stores the listener and cloud-forwarding settings as a native
Home Assistant config entry. The options flow is intentionally reserved for
runtime/diagnostic behavior such as raw payload logging and raw telemetry entity
creation.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_LISTEN_HOST,
    CONF_LISTEN_PORT,
    CONF_LOG_PAYLOADS,
    CONF_SHOW_RAW_SENSORS,
    CONF_UPSTREAM_HOST,
    CONF_UPSTREAM_HOST_HEADER,
    CONF_UPSTREAM_PORT,
    DEFAULT_LISTEN_HOST,
    DEFAULT_LISTEN_PORT,
    DEFAULT_UPSTREAM_HOST,
    DEFAULT_UPSTREAM_HOST_HEADER,
    DEFAULT_UPSTREAM_PORT,
    DOMAIN,
    UNIQUE_ID,
)


def _normalize_input(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize user input before storing it in the config entry."""
    normalized = dict(data)

    normalized[CONF_UPSTREAM_HOST] = str(
        normalized.get(CONF_UPSTREAM_HOST, "")
    ).strip()

    normalized[CONF_UPSTREAM_HOST_HEADER] = str(
        normalized.get(CONF_UPSTREAM_HOST_HEADER, DEFAULT_UPSTREAM_HOST_HEADER)
    ).strip()

    return normalized


def _setup_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return setup schema used by initial setup and YAML import."""
    defaults = defaults or {}

    return vol.Schema(
        {
            vol.Optional(
                CONF_LISTEN_HOST,
                default=defaults.get(CONF_LISTEN_HOST, DEFAULT_LISTEN_HOST),
            ): cv.string,
            vol.Optional(
                CONF_LISTEN_PORT,
                default=defaults.get(CONF_LISTEN_PORT, DEFAULT_LISTEN_PORT),
            ): cv.port,
            vol.Optional(
                CONF_UPSTREAM_HOST_HEADER,
                default=defaults.get(
                    CONF_UPSTREAM_HOST_HEADER,
                    DEFAULT_UPSTREAM_HOST_HEADER,
                ),
            ): cv.string,
            vol.Optional(
                CONF_UPSTREAM_HOST,
                default=defaults.get(CONF_UPSTREAM_HOST, DEFAULT_UPSTREAM_HOST),
            ): cv.string,
            vol.Optional(
                CONF_UPSTREAM_PORT,
                default=defaults.get(CONF_UPSTREAM_PORT, DEFAULT_UPSTREAM_PORT),
            ): cv.port,
            vol.Optional(
                CONF_LOG_PAYLOADS,
                default=defaults.get(CONF_LOG_PAYLOADS, False),
            ): cv.boolean,
            vol.Optional(
                CONF_SHOW_RAW_SENSORS,
                default=defaults.get(CONF_SHOW_RAW_SENSORS, False),
            ): cv.boolean,
        }
    )


def _reconfigure_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return schema for connection settings reconfiguration."""
    defaults = defaults or {}

    return vol.Schema(
        {
            vol.Optional(
                CONF_LISTEN_HOST,
                default=defaults.get(CONF_LISTEN_HOST, DEFAULT_LISTEN_HOST),
            ): cv.string,
            vol.Optional(
                CONF_LISTEN_PORT,
                default=defaults.get(CONF_LISTEN_PORT, DEFAULT_LISTEN_PORT),
            ): cv.port,
            vol.Optional(
                CONF_UPSTREAM_HOST_HEADER,
                default=defaults.get(
                    CONF_UPSTREAM_HOST_HEADER,
                    DEFAULT_UPSTREAM_HOST_HEADER,
                ),
            ): cv.string,
            vol.Optional(
                CONF_UPSTREAM_HOST,
                default=defaults.get(CONF_UPSTREAM_HOST, DEFAULT_UPSTREAM_HOST),
            ): cv.string,
            vol.Optional(
                CONF_UPSTREAM_PORT,
                default=defaults.get(CONF_UPSTREAM_PORT, DEFAULT_UPSTREAM_PORT),
            ): cv.port,
        }
    )


class LevelSenseProObserverConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Level Sense Pro Observer."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle initial UI setup."""
        if user_input is not None:
            await self.async_set_unique_id(UNIQUE_ID)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Level Sense Pro Observer",
                data=_normalize_input(user_input),
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_setup_schema(),
            errors={},
        )

    async def async_step_import(self, import_data: dict[str, Any]):
        """Import YAML configuration into the native config entry model."""
        await self.async_set_unique_id(UNIQUE_ID)
        self._abort_if_unique_id_configured()

        normalized = {
            CONF_LISTEN_HOST: import_data.get(CONF_LISTEN_HOST, DEFAULT_LISTEN_HOST),
            CONF_LISTEN_PORT: import_data.get(CONF_LISTEN_PORT, DEFAULT_LISTEN_PORT),
            CONF_UPSTREAM_HOST_HEADER: import_data.get(
                CONF_UPSTREAM_HOST_HEADER,
                DEFAULT_UPSTREAM_HOST_HEADER,
            ),
            CONF_UPSTREAM_HOST: import_data.get(
                CONF_UPSTREAM_HOST,
                DEFAULT_UPSTREAM_HOST,
            ),
            CONF_UPSTREAM_PORT: import_data.get(
                CONF_UPSTREAM_PORT,
                DEFAULT_UPSTREAM_PORT,
            ),
            CONF_LOG_PAYLOADS: import_data.get(CONF_LOG_PAYLOADS, False),
            CONF_SHOW_RAW_SENSORS: import_data.get(CONF_SHOW_RAW_SENSORS, False),
        }

        return self.async_create_entry(
            title="Level Sense Pro Observer",
            data=_normalize_input(normalized),
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        """Handle reconfiguration of listener and cloud forwarding settings."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if entry is None:
            return self.async_abort(reason="unknown")

        current = dict(entry.data)

        if user_input is not None:
            updated = dict(entry.data)
            updated.update(_normalize_input(user_input))

            return self.async_update_reload_and_abort(
                entry,
                data=updated,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_reconfigure_schema(current),
            errors={},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Create the options flow."""
        return LevelSenseProObserverOptionsFlow()


class LevelSenseProObserverOptionsFlow(config_entries.OptionsFlowWithReload):
    """Handle options and reload automatically after option changes."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage diagnostic and advanced entity options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        entry = self.config_entry
        data = dict(entry.data)
        options = dict(entry.options)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_LOG_PAYLOADS,
                        default=options.get(
                            CONF_LOG_PAYLOADS,
                            data.get(CONF_LOG_PAYLOADS, False),
                        ),
                    ): cv.boolean,
                    vol.Optional(
                        CONF_SHOW_RAW_SENSORS,
                        default=options.get(
                            CONF_SHOW_RAW_SENSORS,
                            data.get(CONF_SHOW_RAW_SENSORS, False),
                        ),
                    ): cv.boolean,
                }
            ),
        )

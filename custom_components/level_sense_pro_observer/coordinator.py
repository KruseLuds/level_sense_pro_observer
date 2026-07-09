"""Push coordinator for Level Sense Pro Observer.

This integration is push-based. The Level Sense Pro sends HTTP requests every
few minutes, and the observer updates Home Assistant when packets arrive.

Home Assistant's polling-oriented ``DataUpdateCoordinator`` is not needed here.
This lightweight coordinator provides the piece we do need: a central place to
notify entities whenever the runtime state changes.

It also persists the runtime state to Home Assistant storage so entities and
diagnostics are meaningful immediately after a restart, before the next device
packet arrives.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .model import LevelSenseState
from .runtime import LevelSenseRuntime

STORAGE_VERSION = 1


class LevelSenseCoordinator:
    """Coordinate runtime state, entity updates, and persistence."""

    def __init__(
        self,
        hass: HomeAssistant,
        runtime: LevelSenseRuntime,
        entry_id: str,
    ) -> None:
        """Initialize the push coordinator."""
        self.hass = hass
        self.runtime = runtime
        self.entry_id = entry_id
        self._listeners: list[Callable[[], None]] = []
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}_runtime_{entry_id}",
        )
        self._save_task_pending = False

    @property
    def state(self) -> LevelSenseState:
        """Return the current runtime state."""
        return self.runtime.state

    async def async_load(self) -> None:
        """Load persisted runtime state from Home Assistant storage."""
        data = await self._store.async_load()
        if isinstance(data, dict):
            self.runtime.restore_state(data)

    async def async_save(self) -> None:
        """Persist runtime state to Home Assistant storage."""
        self._save_task_pending = False
        await self._store.async_save(self.runtime.state.as_dict())

    @callback
    def async_schedule_save(self) -> None:
        """Schedule a state save without queueing duplicate save tasks."""
        if self._save_task_pending:
            return

        self._save_task_pending = True
        self.hass.async_create_task(self.async_save())

    @callback
    def async_add_listener(self, update_callback: Callable[[], None]) -> Callable[[], None]:
        """Add a listener for runtime state updates."""
        self._listeners.append(update_callback)

        @callback
        def remove_listener() -> None:
            if update_callback in self._listeners:
                self._listeners.remove(update_callback)

        return remove_listener

    @callback
    def async_update_from_packet(
        self,
        *,
        client_ip: str,
        method: str,
        request_path: str,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> None:
        """Update state from an observed device packet."""
        self.runtime.update_from_packet(
            client_ip=client_ip,
            method=method,
            request_path=request_path,
            headers=headers,
            payload=payload,
        )
        self._async_notify_listeners()
        self.async_schedule_save()

    @callback
    def async_update_cloud_response(
        self,
        *,
        status_code: str | None,
        status_line: str | None,
        body: dict[str, Any] | str | None,
        latency_ms: float | None,
    ) -> None:
        """Update state from an observed vendor cloud response."""
        self.runtime.update_cloud_response(
            status_code=status_code,
            status_line=status_line,
            body=body,
            latency_ms=latency_ms,
        )
        self._async_notify_listeners()
        self.async_schedule_save()

    @callback
    def async_set_error(self, error: str | None) -> None:
        """Record the latest observer error and notify entities."""
        self.runtime.set_error(error)
        self._async_notify_listeners()
        self.async_schedule_save()

    @callback
    def _async_notify_listeners(self) -> None:
        """Notify all registered entity listeners."""
        for update_callback in list(self._listeners):
            update_callback()

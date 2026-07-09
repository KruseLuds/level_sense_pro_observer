"""Runtime state owner for Level Sense Pro Observer.

``LevelSenseRuntime`` is deliberately independent of Home Assistant. It owns the
current state and knows how to update that state from observed packets and cloud
responses, but it does not create entities, write diagnostics, or open sockets.

That separation keeps the integration easier to test and makes the runtime a
clean boundary between protocol logic and Home Assistant presentation logic.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .model import CloudState, LevelSenseState, NetworkState
from .parser import parse_level_sense_payload


class LevelSenseRuntime:
    """Own the current observed Level Sense Pro state."""

    def __init__(self) -> None:
        """Initialize an empty runtime state."""
        self.state = LevelSenseState()

    def restore_state(self, data: dict[str, Any] | None) -> LevelSenseState:
        """Restore runtime state from Home Assistant storage."""
        self.state = LevelSenseState.from_dict(data)
        return self.state

    def update_from_packet(
        self,
        *,
        client_ip: str,
        method: str,
        request_path: str,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> LevelSenseState:
        """Update runtime state from an observed device packet."""
        now = datetime.now(UTC)

        stats = self.state.statistics
        stats.packet_count += 1
        if stats.first_seen is None:
            stats.first_seen = now
        stats.last_seen = now
        stats.last_error = None

        self.state.network = NetworkState(
            client_ip=client_ip,
            device_id=headers.get("Device-ID") or headers.get("Device-Id"),
            mac=headers.get("MAC") or headers.get("Mac"),
            user_agent=headers.get("User-Agent"),
            method=method,
            request_path=request_path,
        )

        self.state.telemetry = parse_level_sense_payload(payload)

        return self.state

    def update_cloud_response(
        self,
        *,
        status_code: str | None,
        status_line: str | None,
        body: dict[str, Any] | str | None,
        latency_ms: float | None,
    ) -> LevelSenseState:
        """Update runtime state from the vendor cloud response."""
        now = datetime.now(UTC)

        result: str | None = None
        has_config_update: int | None = None

        if isinstance(body, dict):
            raw_result = body.get("result")
            if raw_result is not None:
                result = str(raw_result)

            raw_has_config_update = body.get("has_config_update")
            if raw_has_config_update is not None:
                try:
                    has_config_update = int(raw_has_config_update)
                except (TypeError, ValueError):
                    has_config_update = None

        self.state.cloud = CloudState(
            status_code=status_code,
            status_line=status_line,
            result=result,
            has_config_update=has_config_update,
            body=body,
            latency_ms=latency_ms,
            last_response_at=now,
        )

        return self.state

    def set_error(self, error: str | None) -> LevelSenseState:
        """Record the last observer error."""
        self.state.statistics.last_error = error
        return self.state

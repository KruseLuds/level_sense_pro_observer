"""Level Sense Pro protocol parser.

This module knows about Level Sense Pro payload fields and nothing else.
It does not know about sockets, DNS, Home Assistant entities, config entries,
or diagnostics downloads.

The parser accepts a raw payload dictionary extracted from the device request
and returns a typed ``DeviceTelemetry`` object. Keeping protocol parsing isolated
makes it easier to test and easier to update if future firmware adds fields.
"""

from __future__ import annotations

from typing import Any

from .model import DeviceTelemetry

TEMP_OFFSET_C = 3.61

KNOWN_FIELDS = {
    "sample_elapsed_ms",
    "cap_sense",
    "cycle_count",
    "tempc",
    "rh",
    "battvdc",
    "input1",
    "input2",
    "relay_state",
    "device_state",
    "rssi",
    "siren_state",
    "alarm_silence",
    "debug_mode",
    "run_t",
}


def _to_float(value: Any) -> float | None:
    """Convert a value to float when possible."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _avg_numeric(value: Any) -> float | None:
    """Average a numeric scalar or numeric list.

    The Level Sense Pro often sends three readings for one logical value. The
    normal Home Assistant entity exposes the average while raw sensors and
    diagnostics preserve every individual channel.
    """
    if value is None:
        return None

    if isinstance(value, list):
        nums: list[float] = []
        for item in value:
            num = _to_float(item)
            if num is not None:
                nums.append(num)
        if not nums:
            return None
        return round(sum(nums) / len(nums), 3)

    num = _to_float(value)
    if num is None:
        return None

    return round(num, 3)


def _safe_seconds_from_ms(value: Any) -> float | None:
    """Convert milliseconds to seconds."""
    num = _to_float(value)
    if num is None:
        return None
    return round(num / 1000, 3)


def _safe_seconds(value: Any) -> int | None:
    """Convert a runtime value to whole seconds."""
    num = _to_float(value)
    if num is None:
        return None
    return int(round(num, 0))


def _binary_value(value: Any) -> bool | None:
    """Convert a device boolean-like value to bool.

    The current payload uses integer 0 and 1 values, but this helper tolerates
    common string values in case future firmware changes the representation.
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    num = _to_float(value)
    if num is not None:
        return num != 0

    text = str(value).strip().lower()
    if text in {"on", "true", "yes", "active", "1"}:
        return True
    if text in {"off", "false", "no", "inactive", "0"}:
        return False

    return None


def parse_level_sense_payload(payload: dict[str, Any]) -> DeviceTelemetry:
    """Parse raw Level Sense telemetry into a typed telemetry model."""
    telemetry = DeviceTelemetry()
    telemetry.raw_payload = dict(payload)
    telemetry.unknown_fields = {
        key: value for key, value in payload.items() if key not in KNOWN_FIELDS
    }

    temp_c_avg = _avg_numeric(payload.get("tempc"))
    if temp_c_avg is not None:
        corrected_c = round(temp_c_avg - TEMP_OFFSET_C, 2)
        telemetry.temperature_c = corrected_c
        telemetry.temperature_raw_c = round(temp_c_avg, 2)
        telemetry.temperature_raw_f = round((temp_c_avg * 9 / 5) + 32, 2)
        telemetry.temperature_corrected_f = round((corrected_c * 9 / 5) + 32, 2)

    humidity = _avg_numeric(payload.get("rh"))
    if humidity is not None:
        telemetry.humidity = round(humidity, 2)

    battery_voltage = _avg_numeric(payload.get("battvdc"))
    if battery_voltage is not None:
        telemetry.battery_voltage = round(battery_voltage, 2)

    rssi = _avg_numeric(payload.get("rssi"))
    if rssi is not None:
        telemetry.rssi = round(rssi, 1)

    telemetry.sample_elapsed_seconds = _safe_seconds_from_ms(
        payload.get("sample_elapsed_ms")
    )
    telemetry.runtime_seconds = _safe_seconds(payload.get("run_t"))

    telemetry.relay_state = _binary_value(payload.get("relay_state"))
    telemetry.siren_state = _binary_value(payload.get("siren_state"))
    telemetry.device_state = _binary_value(payload.get("device_state"))
    telemetry.alarm_silence = _binary_value(payload.get("alarm_silence"))
    telemetry.debug_mode = _binary_value(payload.get("debug_mode"))

    return telemetry

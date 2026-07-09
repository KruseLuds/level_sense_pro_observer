# Roadmap

This roadmap describes likely future directions. It does not promise
dates.

## Near term

-   Polish README and installation documentation.
-   Improve diagnostics redaction options.
-   Add screenshots.
-   Prepare HACS metadata.
-   Add GitHub issue templates.

## Future versions

### Multi-device support

Support multiple Level Sense Pro devices through separate runtime state
keyed by device ID or MAC address.

### Dashboard examples

Provide optional Lovelace dashboard examples for:

-   Current sump status.
-   Battery and signal history.
-   Cloud connectivity health.
-   Raw telemetry troubleshooting.

### Historical analysis

Add documented examples for trends and statistics:

-   Battery trend.
-   RSSI trend.
-   Runtime trend.
-   Leak or alarm event history.

### Managed Alert framework integration

Optional alerting using a managed Home Assistant alert framework.

### Generic observer framework

Longer term, the transparent observer pattern could support other IoT
devices that send useful HTTP telemetry to a vendor cloud.

## Under Consideration

-   Generic observer framework for other cloud-connected IoT devices.
-   Enhanced dashboard packages.
-   Additional derived health sensors.

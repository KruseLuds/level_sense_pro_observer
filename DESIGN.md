# Design Notes

Level Sense Pro Observer is built around a transparent observer
architecture.

## Goal

Add rich local Home Assistant monitoring while preserving the
manufacturer's cloud service.

Users should not have to choose between local visibility and cloud
functionality.

## Non-goals

This integration does not aim to:

-   Replace the Level Sense cloud.
-   Disable the mobile app.
-   Modify firmware.
-   Emulate the vendor server.
-   Intercept HTTPS traffic.
-   Change outbound requests or cloud responses.

## Transparent proxy model

The Level Sense Pro sends HTTP requests to `cloud.level-sense.com`. DNS
redirects those requests to Home Assistant. The observer accepts the
HTTP request, extracts useful telemetry, forwards the request to the
real cloud, and returns the cloud response to the device.

## Why not use a cloud API?

A cloud API would require credentials, reverse engineering, rate limit
handling, cloud dependencies, and possible future breakage.

The observer sees the device's own telemetry directly, while still
allowing the cloud to work normally.

## Why not replace the cloud?

Replacing the cloud would risk breaking:

-   Mobile app functionality.
-   Vendor website updates.
-   Cloud alerts.
-   Firmware behavior.
-   Future compatibility.

The observer model avoids that risk.

## Entity model

Default entities are intentionally limited to useful values:

-   Temperature.
-   Humidity.
-   Battery voltage.
-   RSSI.
-   Runtime.
-   Packet count.
-   Last seen.
-   Cloud status.
-   Cloud result.
-   Cloud latency.
-   Device state binary sensors.

Raw channels are available as optional entities, but disabled by
default.

## Runtime model

The integration keeps an in-memory runtime model containing:

-   Telemetry.
-   Network metadata.
-   Cloud response data.
-   Statistics.

That runtime is persisted so Home Assistant can restore the last known
state after restart.

## DNS resolution

The observer must avoid resolving the cloud hostname back to itself. It
first tries system DNS, then falls back to known public resolvers if the
result appears local or private.

## HTTP response handling

The proxy reads upstream cloud responses using HTTP framing rules:

-   `Content-Length`.
-   `Transfer-Encoding: chunked`.

It does not wait for the upstream TCP socket to close. This is important
because HTTP servers may keep connections open.

## Future multi-device support

The current implementation is single-device oriented, but the protocol
includes device identity and MAC metadata. A future version can key
runtime state by device ID or MAC address.

## Design Principles

-   Preserve vendor functionality.
-   Keep the observer transparent.
-   Parse telemetry without modifying payloads.
-   Expose useful entities by default.
-   Keep advanced diagnostics optional.

## Logging

Normal operation is intentionally quiet. Detailed transaction logging is
available through Home Assistant debug logging when deeper
troubleshooting is required.

# Level Sense Pro Observer

![Level Sense Pro Observer](images/banner.png)

**Full Local Visibility. Full Cloud Functionality.**

**The Best of Both Worlds!**

Level Sense Pro Observer is a Home Assistant custom integration that
adds detailed local monitoring for a Level Sense Pro while preserving
the manufacturer's cloud service, website, mobile app, alerts, firmware
behavior, and normal device operation.

It does this by acting as a transparent HTTP observer proxy. The Level
Sense Pro still believes it is talking to `cloud.level-sense.com`. The
observer receives the same traffic, decodes useful telemetry for Home
Assistant, then forwards the original request to the real Level Sense
cloud and returns the cloud response to the device.

The goal is simple:

-   Keep the vendor cloud working.
-   Add rich local Home Assistant entities.
-   Do not modify the device, firmware, cloud payload, or cloud
    response.

## Why This Integration Exists

The Level Sense Pro is an excellent cloud connected sump pump monitoring
system, but it has one limitation for Home Assistant users: all of its
rich telemetry is sent only to the vendor cloud.

**Level Sense Pro Observer** solves that problem without sacrificing any
existing functionality.

Rather than replacing the manufacturer's cloud service, the integration
transparently observes the existing HTTP communication, creates native
Home Assistant entities from the telemetry, and then forwards the
original request to the real Level Sense cloud. The original cloud
response is returned unchanged to the device.

The result is the best of both worlds:

-   Native Level Sense mobile app
-   Vendor website
-   Vendor cloud alerts
-   Firmware updates
-   Native Home Assistant entities
-   Dashboards
-   Automations
-   Long-term history
-   Diagnostics

## Quick Start

1.  Install the custom integration.
2.  Configure a DNS rewrite so `cloud.level-sense.com` resolves to Home
    Assistant.
3.  Add the integration from **Settings → Devices & Services**.
4.  Verify the vendor website and Home Assistant are both updating.

For detailed instructions, see **INSTALL.md** and **NETWORK_SETUP.md**.

## Why an Observer?

Unlike many reverse engineering projects, this integration intentionally
**does not replace the manufacturer's cloud**.

Instead, every request is forwarded to the real cloud while Home
Assistant quietly observes the telemetry locally.

This approach preserves normal device operation while adding powerful
local visibility.

## Capability Comparison

| Capability | Vendor Cloud | Local Replacement | Level Sense Pro Observer |
|---|:---:|:---:|:---:|
| Mobile App | ✅ | ❌ | ✅ |
| Vendor Website | ✅ | ❌ | ✅ |
| Cloud Alerts | ✅ | ❌ | ✅ |
| Firmware Updates | ✅ | ❌ | ✅ |
| Home Assistant Entities | ❌ | ✅ | ✅ |
| Local Automations | ❌ | ✅ | ✅ |
| Local History | ❌ | ✅ | ✅ |
| Diagnostics | ❌ | ✅ | ✅ |
## Project Status

-   Production-ready architecture
-   Actively maintained
-   Native Home Assistant config flow
-   Supports Home Assistant diagnostics
-   Designed to preserve vendor cloud functionality

## Highlights

-   Native Home Assistant config flow.
-   Native Home Assistant device.
-   Native sensor and binary sensor entities.
-   Optional raw telemetry sensors.
-   Downloadable diagnostics.
-   Runtime state persistence after Home Assistant restarts.
-   Automatic cloud DNS resolution that bypasses local DNS rewrites.
-   Transparent forwarding to the Level Sense cloud.
-   Vendor website and cloud alerts continue to work.
-   No TLS interception.
-   No firmware modification.
-   No cloud replacement.

## Architecture

``` text
Level Sense Pro
      |
      | DNS lookup for cloud.level-sense.com
      v
Local DNS rewrite, such as AdGuard Home
      |
      | cloud.level-sense.com -> Home Assistant IP
      v
Home Assistant
Level Sense Pro Observer
      |
      | observe, decode, create HA entities
      | forward original request unchanged except required Host routing
      v
Real Level Sense cloud
      |
      | original cloud response
      v
Level Sense Pro Observer
      |
      | return cloud response to the device
      v
Level Sense Pro
```

The observer is intentionally passive. It watches the traffic and
exposes data to Home Assistant, but it does not attempt to replace the
cloud or control the device.

## Local Home Assistant Entities

### Sensors

| Entity | Description |
|---|---|
| Temperature | Corrected average device temperature |
| Humidity | Average humidity |
| Battery Voltage | Average battery voltage |
| RSSI | Average Wi-Fi signal |
| Runtime | Device-reported runtime |
| Packet Count | Number of observed packets |
| Last Seen | Time of the last device packet |
| Cloud Status | HTTP status returned by the Level Sense cloud |
| Cloud Result | Parsed cloud result, such as `success` |
| Cloud Has Config Update | Cloud configuration update flag |
| Cloud Latency | Time to complete the upstream cloud transaction |
### Binary Sensors

| Entity | Description |
|---|---|
| Relay State | Raw relay state exposed as a binary sensor |
| Siren State | Raw siren state exposed as a binary sensor |
| Device State | Raw device state exposed as a binary sensor |
| Alarm Silence | Alarm silence state |
| Debug Mode | Debug mode when reported by firmware |
### Optional raw telemetry sensors

When enabled, the integration can also create raw entities for each
telemetry channel, such as:

-   Raw temperature channels.
-   Raw humidity channels.
-   Raw battery channels.
-   Raw RSSI channels.
-   Raw capacitive sense channels.
-   Raw inputs.
-   Raw device flags.

Raw sensors are disabled by default because most users only need the
polished entities.

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation and verification
instructions.

## Network setup

A DNS rewrite is required so the Level Sense Pro sends its cloud traffic
to Home Assistant first.

See [NETWORK_SETUP.md](NETWORK_SETUP.md) for AdGuard Home, Pi-hole, and
general DNS rewrite guidance.

## Design philosophy

Level Sense Pro Observer is designed around a simple principle:

**Preserve cloud functionality while adding local visibility.**

This is not a cloud replacement. It is not a firmware modification. It
is not a device emulator. It is a transparent observer.

See [DESIGN.md](DESIGN.md) for the full architecture and rationale.

## Diagnostics

Home Assistant's built-in diagnostics download includes:

-   Integration configuration.
-   Current device telemetry.
-   Network metadata.
-   Cloud response data.
-   DNS resolver state.
-   Packet statistics.
-   Unknown protocol fields.
-   Last raw payload.

This makes troubleshooting easier without requiring packet captures for
normal issues.

## Requirements

-   Home Assistant.
-   A Level Sense Pro that communicates with `cloud.level-sense.com`
    over HTTP.
-   A DNS rewrite tool such as AdGuard Home, Pi-hole, pfSense, OPNsense,
    UniFi DNS, MikroTik, Technitium DNS, or similar.
-   Network routing/firewall rules that allow the Level Sense Pro to
    reach Home Assistant on the configured listen port.

## Important notes

-   This integration currently observes HTTP traffic on port 80.
-   If the vendor moves this device to HTTPS in the future, the
    architecture would need to change.
-   This integration is independent and is not affiliated with, endorsed
    by, or sponsored by Level Sense.
-   Level Sense is a trademark of its respective owner.

## Supported DNS Platforms

Any DNS server capable of rewriting a hostname may be used, including:

-   AdGuard Home
-   Pi-hole
-   Technitium DNS
-   pfSense
-   OPNsense
-   MikroTik
-   UniFi DNS

## What This Integration Does Not Do

-   Replace the Level Sense cloud
-   Modify device firmware
-   Require hardware modifications
-   Intercept HTTPS traffic
-   Require inbound firewall ports
-   Modify telemetry before forwarding it

## Support

When opening an issue, please include:

-   Home Assistant version
-   Integration version
-   Downloaded diagnostics file
-   Relevant Home Assistant log entries
-   A description of the observed behavior

This information usually allows problems to be diagnosed without
requiring packet captures.

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

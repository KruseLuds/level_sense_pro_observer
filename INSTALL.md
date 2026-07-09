# Installation Guide

This guide walks through installing Level Sense Pro Observer and
verifying that both Home Assistant and the Level Sense cloud continue to
work.

## 1. Copy the integration

Copy the integration folder into Home Assistant:

``` text
/config/custom_components/level_sense_pro_observer/
```

The folder should contain files like:

``` text
__init__.py
manifest.json
config_flow.py
const.py
coordinator.py
diagnostics.py
dns.py
model.py
parser.py
proxy.py
runtime.py
sensor.py
binary_sensor.py
strings.json
translations/en.json
brand/icon.png
brand/logo.png
```

## 2. Restart Home Assistant

Restart Home Assistant after copying or updating the files.

## 3. Add the integration

In Home Assistant:

``` text
Settings -> Devices & services -> Add integration -> Level Sense Pro Observer
```

Recommended initial settings:

  Field                          Recommended value
  ------------------------------ -------------------------
  Listen host                    `0.0.0.0`
  Listen port                    `80`
  Cloud hostname                 `cloud.level-sense.com`
  Cloud IP address override      blank
  Cloud port                     `80`
  Log raw payloads               off
  Create raw telemetry sensors   off

Leave the Cloud IP address override blank unless troubleshooting. When
blank, the integration resolves the real cloud address automatically and
bypasses local DNS rewrites.

## 4. Configure DNS rewrite

Configure your DNS server so the Level Sense Pro resolves:

``` text
cloud.level-sense.com
```

to your Home Assistant IP address, for example:

``` text
192.168.0.34
```

See [NETWORK_SETUP.md](NETWORK_SETUP.md) for details.

## 5. Verify the device reaches Home Assistant

After the DNS rewrite is active, wait for the Level Sense Pro to send
its next packet.

Check the Home Assistant log:

``` bash
grep -i "level sense\|proxy error" /config/home-assistant.log | tail -120
```

A healthy startup should show the observer started. Normal packet logs
may be quiet unless debug logging is enabled.

## 6. Verify Home Assistant entities

Expected default entities include:

``` text
sensor.level_sense_pro_temperature
sensor.level_sense_pro_humidity
sensor.level_sense_pro_battery_voltage
sensor.level_sense_pro_rssi
sensor.level_sense_pro_runtime
sensor.level_sense_pro_packet_count
sensor.level_sense_pro_last_seen
sensor.level_sense_pro_cloud_status
sensor.level_sense_pro_cloud_result
sensor.level_sense_pro_cloud_has_config_update
sensor.level_sense_pro_cloud_latency
binary_sensor.level_sense_pro_relay_state
binary_sensor.level_sense_pro_siren_state
binary_sensor.level_sense_pro_device_state
binary_sensor.level_sense_pro_alarm_silence
binary_sensor.level_sense_pro_debug_mode
```

## 7. Verify the vendor cloud still works

Confirm that:

-   The Level Sense website still updates.
-   The mobile app still shows current data.
-   Cloud alerts remain enabled.
-   The Level Sense Pro connection indicator looks normal.

## 8. Optional raw telemetry sensors

To expose raw channels:

``` text
Settings -> Devices & services -> Level Sense Pro Observer -> Configure -> Create raw telemetry sensors
```

Raw entities are useful for debugging and protocol exploration, but they
are not required for normal use.

## 9. Optional raw payload logging

Use this only while troubleshooting:

``` text
Settings -> Devices & services -> Level Sense Pro Observer -> Configure -> Log raw payloads
```

This writes every raw payload to the Home Assistant log.

Turn it off afterward.

## 10. Troubleshooting quick checks

### No entities update

-   Confirm the DNS rewrite points to Home Assistant.
-   Confirm the Level Sense Pro is using that DNS server.
-   Confirm firewall rules allow the device VLAN to reach Home Assistant
    on port 80.
-   Confirm the integration is listening on `0.0.0.0:80`.

### Vendor website stops updating

-   Remove the DNS rewrite to roll back immediately.
-   Confirm Home Assistant can reach the real cloud address.
-   Check `sensor.level_sense_pro_cloud_result`.
-   Check `sensor.level_sense_pro_cloud_status`.

### Raw sensors remain after disabling

Home Assistant may leave previously created entities in the entity
registry as unavailable. That is normal. Delete them manually if
desired.

## Success Checklist

After installation, verify all of the following:

-   [ ] Integration loads without errors.
-   [ ] Packet Counter increases.
-   [ ] Cloud Result reports `success`.
-   [ ] Vendor website updates.
-   [ ] Mobile app updates.
-   [ ] Home Assistant entities update.
-   [ ] Optional raw sensors can be enabled and disabled.

## Next Steps

After installation, consider creating dashboards, automations, long-term
statistics, and alerts using the exposed entities.

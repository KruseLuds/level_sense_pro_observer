# Network Setup

Level Sense Pro Observer depends on one network idea: redirect only the
Level Sense Pro cloud hostname to Home Assistant.

The device still sends normal HTTP requests to `cloud.level-sense.com`.
Your DNS server answers that hostname with the Home Assistant IP
address. The observer receives the request, observes it, forwards it to
the real Level Sense cloud, and returns the real cloud response to the
device.

## Basic flow

``` text
Level Sense Pro
      |
      | asks DNS for cloud.level-sense.com
      v
Local DNS server
      |
      | returns Home Assistant IP
      v
Home Assistant Level Sense Pro Observer
      |
      | resolves real cloud IP using fallback DNS if needed
      v
Level Sense cloud
```

## AdGuard Home example

In AdGuard Home:

``` text
Filters -> DNS rewrites -> Add DNS rewrite
```

Add:

``` text
Domain: cloud.level-sense.com
Answer: 192.168.0.##
```

Replace `192.168.0.##` with your Home Assistant IP address.

## Pi-hole example

In Pi-hole:

``` text
Local DNS -> DNS Records
```

Add:

``` text
cloud.level-sense.com -> 192.168.0.##
```

## pfSense or OPNsense

Use DNS Resolver or DNS Forwarder host overrides:

``` text
Host: cloud
Domain: level-sense.com
IP: 192.168.0.##
```

## UniFi DNS

Use a local DNS record if your UniFi gateway supports it, or point the
Level Sense VLAN to AdGuard Home, Pi-hole, or another DNS server that
can perform the rewrite.

## MikroTik

Add a static DNS entry:

``` text
/ip dns static add name=cloud.level-sense.com address=192.168.0.##
```

## Firewall requirements

The Level Sense Pro must be allowed to connect to Home Assistant on the
configured listen port, usually TCP port 80.

Home Assistant must be allowed to connect outbound to the real Level
Sense cloud on TCP port 80.

## Why automatic cloud DNS resolution is needed

Once local DNS rewrites `cloud.level-sense.com` to Home Assistant, Home
Assistant may also resolve that same hostname back to itself.

To prevent a forwarding loop, the integration detects suspicious local
DNS results and falls back to public DNS resolvers. This lets the device
talk to Home Assistant while Home Assistant still forwards traffic to
the real cloud.

## Rollback

To immediately stop using the observer, remove the DNS rewrite:

``` text
cloud.level-sense.com -> Home Assistant IP
```

The Level Sense Pro will go back to talking directly to the vendor cloud
on its next DNS lookup.

## Verification

After configuring the DNS rewrite:

-   Confirm the Level Sense Pro is using the DNS server you configured.
-   Verify `sensor.level_sense_pro_cloud_result` reports `success`.
-   Verify the vendor website continues updating.
-   Verify Home Assistant receives new packets.

## Typical Home Network

``` text
Level Sense Pro
        |
     DNS Query
        |
   DNS Rewrite
        |
 Home Assistant Observer
        |
   Real Level Sense Cloud
```

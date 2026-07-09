# FAQ

## Does this replace the Level Sense cloud?

No. The integration is designed to preserve the vendor cloud.

## Will the Level Sense website still work?

Yes. Requests are forwarded to the real cloud.

## Will mobile app alerts still work?

Yes, as long as the cloud continues receiving forwarded device updates.

## Does this modify device traffic?

The observer forwards the request payload unchanged. It rewrites the
upstream HTTP Host handling only as needed to forward traffic to the
real cloud.

## Does this require firmware changes?

No.

## Does this require HTTPS interception?

No. The current device traffic observed by this integration is HTTP on
port 80.

## Can I use Pi-hole instead of AdGuard Home?

Yes. Any DNS system that can rewrite `cloud.level-sense.com` to Home
Assistant can work.

## Why is there a Cloud IP override field?

Normally it should be blank. It exists for testing and troubleshooting.
When blank, the integration resolves the real cloud IP automatically.

## Why are raw sensors optional?

The raw payload contains many channels that are useful for debugging but
not needed for normal use. Keeping them optional avoids clutter.

## What if the vendor changes the protocol?

Unknown fields are preserved in diagnostics so protocol changes can be
detected and supported.

## Can I use this with VLANs?

Yes. The Level Sense Pro only needs network access to Home Assistant,
and Home Assistant needs outbound access to the Level Sense cloud.

## Does disabling raw sensors delete them?

No. Existing raw entities may remain in the entity registry as
unavailable until manually removed.

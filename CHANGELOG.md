# Changelog

## 0.4.0

Initial public preview candidate.

### Added

-   Transparent Level Sense Pro HTTP observer proxy.
-   Home Assistant config flow.
-   Home Assistant options flow.
-   Native Home Assistant device registration.
-   Native sensor entities.
-   Native binary sensor entities.
-   Optional raw telemetry sensors.
-   Downloadable diagnostics.
-   Runtime state persistence.
-   Automatic upstream cloud DNS resolution.
-   Fallback DNS handling to avoid local DNS rewrite loops.
-   Cloud response parsing.
-   Chunked HTTP response support.
-   Integration branding support through the `brand` directory.

### Notes

-   The integration preserves vendor cloud functionality.
-   The Level Sense website and cloud alerts should continue to work.
-   This release targets HTTP traffic to `cloud.level-sense.com` on port
    80.

### Changed

-   Automatic upstream DNS resolution now avoids local DNS rewrite
    loops.
-   Improved HTTP response handling for chunked responses.
-   Added integration branding assets.

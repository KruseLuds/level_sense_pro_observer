"""Constants for Level Sense Pro Observer.

This module is intentionally small and boring. It contains stable names,
default values, configuration keys, and Home Assistant data keys that are used
across the integration.

Keeping these values centralized prevents tiny spelling differences from
creating hard-to-find bugs in setup, config flow, diagnostics, entities, DNS
resolution, and the proxy.
"""

DOMAIN = "level_sense_pro_observer"

DEVICE_MANUFACTURER = "Level Sense"
DEVICE_MODEL = "Level Sense Pro"
DEVICE_NAME = "Level Sense Pro"

DEFAULT_LISTEN_HOST = "0.0.0.0"
DEFAULT_LISTEN_PORT = 80

DEFAULT_UPSTREAM_HOST = ""
DEFAULT_UPSTREAM_PORT = 80
DEFAULT_UPSTREAM_HOST_HEADER = "cloud.level-sense.com"

DEFAULT_DNS_CACHE_SECONDS = 3600
DEFAULT_FALLBACK_DNS_SERVERS = ("1.1.1.1", "8.8.8.8")

CONF_LISTEN_HOST = "listen_host"
CONF_LISTEN_PORT = "listen_port"
CONF_UPSTREAM_HOST = "upstream_host"
CONF_UPSTREAM_PORT = "upstream_port"
CONF_UPSTREAM_HOST_HEADER = "upstream_host_header"
CONF_LOG_PAYLOADS = "log_payloads"
CONF_SHOW_RAW_SENSORS = "show_raw_sensors"

DATA_PROXY = "proxy"
DATA_RUNTIME = "runtime"
DATA_COORDINATOR = "coordinator"
DATA_DNS_RESOLVER = "dns_resolver"

UNIQUE_ID = "level_sense_pro_observer_single"

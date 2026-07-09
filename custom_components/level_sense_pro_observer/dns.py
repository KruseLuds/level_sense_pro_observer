"""DNS resolution helper for Level Sense Pro Observer.

The Level Sense Pro is redirected to Home Assistant by a local DNS rewrite.
That means Home Assistant itself may also resolve cloud.level-sense.com back
to Home Assistant.

If the observer used that rewritten address for upstream forwarding, the proxy
would connect back to itself.

This helper avoids that loop:

1. Try normal system DNS first.
2. If the result looks local, private, loopback, or otherwise suspicious,
   try fallback public resolvers.
3. Cache the result so we do not perform DNS lookups for every packet.
4. Expose resolver details through diagnostics.
"""

from __future__ import annotations

import ipaddress
import socket
from datetime import UTC, datetime, timedelta
from functools import partial
from typing import Any

import dns.asyncresolver

from homeassistant.core import HomeAssistant

from .const import DEFAULT_DNS_CACHE_SECONDS, DEFAULT_FALLBACK_DNS_SERVERS


class LevelSenseDNSResolver:
    """Resolve the vendor cloud hostname while avoiding local DNS rewrite loops."""

    def __init__(
        self,
        hass: HomeAssistant,
        hostname: str,
        listen_host: str,
        cache_seconds: int = DEFAULT_DNS_CACHE_SECONDS,
    ) -> None:
        """Initialize the resolver."""
        self.hass = hass
        self.hostname = hostname.strip()
        self.listen_host = listen_host.strip()
        self.cache_seconds = cache_seconds

        self.addresses: list[str] = []
        self.system_addresses: list[str] = []
        self.fallback_addresses: list[str] = []
        self.resolver_used: str | None = None
        self.last_lookup_at: datetime | None = None
        self.last_error: str | None = None
        self.system_resolution_was_suspicious = False

    async def async_get_addresses(self, force_refresh: bool = False) -> list[str]:
        """Return resolved upstream addresses."""
        if not force_refresh and self._cache_valid():
            return list(self.addresses)

        self.last_error = None
        self.system_resolution_was_suspicious = False

        system_addresses = await self._async_resolve_system()
        self.system_addresses = system_addresses

        if system_addresses and not self._addresses_are_suspicious(system_addresses):
            self.addresses = system_addresses
            self.resolver_used = "system"
            self.last_lookup_at = datetime.now(UTC)
            return list(self.addresses)

        if system_addresses:
            self.system_resolution_was_suspicious = True

        fallback_addresses = await self._async_resolve_fallback()
        self.fallback_addresses = fallback_addresses

        if fallback_addresses:
            self.addresses = fallback_addresses
            self.resolver_used = "fallback_public_dns"
            self.last_lookup_at = datetime.now(UTC)
            return list(self.addresses)

        if system_addresses:
            self.addresses = system_addresses
            self.resolver_used = "system_suspicious_fallback_failed"
            self.last_lookup_at = datetime.now(UTC)
            return list(self.addresses)

        self.addresses = []
        self.resolver_used = "failed"
        self.last_lookup_at = datetime.now(UTC)
        return []

    async def _async_resolve_system(self) -> list[str]:
        """Resolve using the Home Assistant host operating system resolver."""
        try:
            result = await self.hass.async_add_executor_job(
                partial(
                    socket.getaddrinfo,
                    self.hostname,
                    None,
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                )
            )
        except Exception as err:
            self.last_error = f"System DNS lookup failed: {err}"
            return []

        addresses: list[str] = []
        for item in result:
            sockaddr = item[4]
            if not sockaddr:
                continue

            address = sockaddr[0]
            if address not in addresses:
                addresses.append(address)

        return addresses

    async def _async_resolve_fallback(self) -> list[str]:
        """Resolve using fallback public DNS resolvers."""
        resolver = dns.asyncresolver.Resolver(configure=False)
        resolver.nameservers = list(DEFAULT_FALLBACK_DNS_SERVERS)
        resolver.lifetime = 5.0
        resolver.timeout = 3.0

        try:
            answers = await resolver.resolve(self.hostname, "A")
        except Exception as err:
            self.last_error = f"Fallback DNS lookup failed: {err}"
            return []

        addresses: list[str] = []
        for answer in answers:
            address = answer.to_text()
            if address not in addresses:
                addresses.append(address)

        return addresses

    def _cache_valid(self) -> bool:
        """Return true when cached DNS results are still fresh."""
        if not self.addresses or self.last_lookup_at is None:
            return False

        return datetime.now(UTC) - self.last_lookup_at < timedelta(
            seconds=self.cache_seconds
        )

    def _addresses_are_suspicious(self, addresses: list[str]) -> bool:
        """Return true if any address looks like a local DNS rewrite."""
        for address in addresses:
            if self._address_is_suspicious(address):
                return True
        return False

    def _address_is_suspicious(self, address: str) -> bool:
        """Return true when one address appears unsafe for upstream forwarding."""
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return False

        if ip.is_loopback or ip.is_link_local or ip.is_private:
            return True

        if self.listen_host not in ("", "0.0.0.0", "::") and address == self.listen_host:
            return True

        return False

    def diagnostics(self) -> dict[str, Any]:
        """Return DNS diagnostics."""
        return {
            "hostname": self.hostname,
            "addresses": list(self.addresses),
            "system_addresses": list(self.system_addresses),
            "fallback_addresses": list(self.fallback_addresses),
            "resolver_used": self.resolver_used,
            "last_lookup_at": self.last_lookup_at.isoformat()
            if self.last_lookup_at
            else None,
            "last_error": self.last_error,
            "system_resolution_was_suspicious": self.system_resolution_was_suspicious,
            "cache_seconds": self.cache_seconds,
            "fallback_dns_servers": list(DEFAULT_FALLBACK_DNS_SERVERS),
        }
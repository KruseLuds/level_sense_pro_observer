"""Transparent HTTP proxy for Level Sense Pro Observer."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from .coordinator import LevelSenseCoordinator
from .dns import LevelSenseDNSResolver

_LOGGER = logging.getLogger(__name__)

MAX_HEADER_BYTES = 65536
READ_TIMEOUT_SECONDS = 20
UPSTREAM_TIMEOUT_SECONDS = 20


class LevelSenseProxy:
    """Transparent HTTP proxy for the Level Sense Pro."""

    def __init__(
        self,
        *,
        coordinator: LevelSenseCoordinator,
        dns_resolver: LevelSenseDNSResolver,
        listen_host: str,
        listen_port: int,
        upstream_host: str,
        upstream_port: int,
        upstream_host_header: str,
        log_payloads: bool,
        show_raw_sensors: bool,
    ) -> None:
        """Initialize the proxy."""
        self.coordinator = coordinator
        self.dns_resolver = dns_resolver
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.upstream_host = upstream_host.strip()
        self.upstream_port = upstream_port
        self.upstream_host_header = upstream_host_header.strip()
        self.log_payloads = log_payloads
        self.show_raw_sensors = show_raw_sensors
        self._server: asyncio.AbstractServer | None = None

    @property
    def connect_host_description(self) -> str:
        """Return a human friendly connection target."""
        if self.upstream_host:
            return self.upstream_host
        return f"{self.upstream_host_header} via DNS resolver"

    async def async_start(self) -> None:
        """Start listening."""
        self._server = await asyncio.start_server(
            self._handle_client,
            self.listen_host,
            self.listen_port,
        )

    async def async_stop(self) -> None:
        """Stop listening."""
        if self._server is None:
            return

        self._server.close()
        await self._server.wait_closed()
        self._server = None

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle one device request."""
        peer = writer.get_extra_info("peername")
        client_ip = peer[0] if peer else "unknown"
        total_started = time.monotonic()

        try:
            raw_request = await asyncio.wait_for(
                self._read_http_request(reader),
                timeout=READ_TIMEOUT_SECONDS,
            )

            if not raw_request:
                writer.close()
                await writer.wait_closed()
                return

            request_line, headers, body = self._split_request(raw_request)
            method, path, _version = request_line.split(" ", 2)

            parsed_url = urlsplit(path)

            _LOGGER.debug(
                "Level Sense HTTP transaction start: client=%s method=%s path=%s request_bytes=%s body_bytes=%s",
                client_ip,
                method,
                parsed_url.path,
                len(raw_request),
                len(body),
            )

            self._observe_request(
                client_ip=client_ip,
                method=method,
                path=path,
                headers=headers,
            )

            upstream_started = time.monotonic()
            raw_response = await self._forward_raw_request(raw_request)
            upstream_ms = round((time.monotonic() - upstream_started) * 1000, 1)

            self._observe_response(raw_response, upstream_ms)

            writer.write(raw_response)
            await writer.drain()

            total_ms = round((time.monotonic() - total_started) * 1000, 1)

            _LOGGER.debug(
                "Level Sense HTTP transaction complete: client=%s method=%s path=%s response_bytes=%s upstream_ms=%s total_ms=%s",
                client_ip,
                method,
                parsed_url.path,
                len(raw_response),
                upstream_ms,
                total_ms,
            )

        except Exception as err:
            self.coordinator.async_set_error(f"{type(err).__name__}: {err!r}")
            _LOGGER.exception(
                "Level Sense proxy error from %s (%s): %r",
                client_ip,
                type(err).__name__,
                err,
            )

            try:
                body = b'{"result":"fail","reason":"level sense pro observer proxy error"}'
                writer.write(
                    b"HTTP/1.1 502 Bad Gateway\r\n"
                    b"Content-Type: application/json\r\n"
                    b"Connection: close\r\n"
                    + f"Content-Length: {len(body)}\r\n".encode()
                    + b"\r\n"
                    + body
                )
                await writer.drain()
            except Exception:
                pass

        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def _read_http_request(self, reader: asyncio.StreamReader) -> bytes:
        """Read one complete HTTP request from the Level Sense device."""
        data = b""

        while b"\r\n\r\n" not in data:
            chunk = await reader.read(4096)
            if not chunk:
                break

            data += chunk

            if len(data) > MAX_HEADER_BYTES:
                raise ValueError("HTTP headers too large")

        if b"\r\n\r\n" not in data:
            return data

        header_part, rest = data.split(b"\r\n\r\n", 1)
        headers_text = header_part.decode("iso-8859-1", errors="replace")
        content_length = 0

        for line in headers_text.split("\r\n")[1:]:
            if line.lower().startswith("content-length:"):
                content_length = int(line.split(":", 1)[1].strip())
                break

        missing = content_length - len(rest)
        if missing > 0:
            data += await reader.readexactly(missing)

        return data

    def _split_request(self, raw_request: bytes) -> tuple[str, dict[str, str], bytes]:
        """Split an HTTP request into request line, headers, and body."""
        header_bytes, _, body = raw_request.partition(b"\r\n\r\n")
        lines = header_bytes.decode("iso-8859-1", errors="replace").split("\r\n")
        request_line = lines[0]
        headers: dict[str, str] = {}

        for line in lines[1:]:
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()

        return request_line, headers, body

    async def _forward_raw_request(self, raw_request: bytes) -> bytes:
        """Forward request unchanged except for the Host header."""
        request_line, headers, body = self._split_request(raw_request)
        method, path, version = request_line.split(" ", 2)

        outbound_lines = [f"{method} {path} {version}"]
        saw_host = False

        for key, value in headers.items():
            if key.lower() == "host":
                outbound_lines.append(f"Host: {self.upstream_host_header}")
                saw_host = True
            else:
                outbound_lines.append(f"{key}: {value}")

        if not saw_host:
            outbound_lines.append(f"Host: {self.upstream_host_header}")

        outbound = "\r\n".join(outbound_lines).encode("iso-8859-1") + b"\r\n\r\n" + body

        upstream_reader, upstream_writer = await self._async_open_upstream_connection()

        try:
            upstream_writer.write(outbound)
            await upstream_writer.drain()

            raw_response = await self._read_http_response(upstream_reader)
            status_line, response_headers, response_body = self._split_response(raw_response)

            _LOGGER.debug(
                "Level Sense upstream response: status=%s content_length=%s transfer_encoding=%s response_bytes=%s body_bytes=%s",
                status_line,
                response_headers.get("content-length", ""),
                response_headers.get("transfer-encoding", ""),
                len(raw_response),
                len(response_body),
            )

            return raw_response

        finally:
            upstream_writer.close()
            try:
                await upstream_writer.wait_closed()
            except Exception:
                pass

    async def _read_http_response(self, reader: asyncio.StreamReader) -> bytes:
        """Read one complete HTTP response using HTTP framing rules."""
        data = b""

        while b"\r\n\r\n" not in data:
            chunk = await asyncio.wait_for(
                reader.read(4096),
                timeout=UPSTREAM_TIMEOUT_SECONDS,
            )
            if not chunk:
                break

            data += chunk

            if len(data) > MAX_HEADER_BYTES:
                raise ValueError("HTTP response headers too large")

        if b"\r\n\r\n" not in data:
            return data

        header_bytes, body = data.split(b"\r\n\r\n", 1)
        header_text = header_bytes.decode("iso-8859-1", errors="replace")
        headers = self._parse_response_headers(header_text)

        transfer_encoding = headers.get("transfer-encoding", "").lower()
        content_length_text = headers.get("content-length")

        if "chunked" in transfer_encoding:
            body = await self._read_chunked_response_body(reader, body)
            return header_bytes + b"\r\n\r\n" + body

        if content_length_text:
            try:
                content_length = int(content_length_text)
            except ValueError:
                content_length = 0

            missing = content_length - len(body)
            if missing > 0:
                body += await asyncio.wait_for(
                    reader.readexactly(missing),
                    timeout=UPSTREAM_TIMEOUT_SECONDS,
                )

            return header_bytes + b"\r\n\r\n" + body

        return header_bytes + b"\r\n\r\n" + body

    async def _read_chunked_response_body(
        self,
        reader: asyncio.StreamReader,
        initial_body: bytes,
    ) -> bytes:
        """Read a complete chunked HTTP response body."""
        body = initial_body

        while not self._chunked_body_complete(body):
            chunk = await asyncio.wait_for(
                reader.read(4096),
                timeout=UPSTREAM_TIMEOUT_SECONDS,
            )

            if not chunk:
                break

            body += chunk

        return body

    def _chunked_body_complete(self, body: bytes) -> bool:
        """Return true if the chunked body contains a terminating zero chunk."""
        pos = 0

        while True:
            line_end = body.find(b"\r\n", pos)
            if line_end == -1:
                return False

            size_line = body[pos:line_end].split(b";", 1)[0].strip()

            try:
                size = int(size_line, 16)
            except ValueError:
                return False

            pos = line_end + 2

            if size == 0:
                return len(body) >= pos + 2

            pos = pos + size + 2

            if len(body) < pos:
                return False

    def _parse_response_headers(self, header_text: str) -> dict[str, str]:
        """Parse HTTP response headers into a lowercase dictionary."""
        headers: dict[str, str] = {}

        lines = header_text.split("\r\n")
        for line in lines[1:]:
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

        return headers

    def _split_response(self, raw_response: bytes) -> tuple[str, dict[str, str], bytes]:
        """Split an HTTP response into status line, headers, and body."""
        header_bytes, _, body = raw_response.partition(b"\r\n\r\n")
        header_text = header_bytes.decode("iso-8859-1", errors="replace")
        lines = header_text.split("\r\n")
        status_line = lines[0] if lines else ""
        headers = self._parse_response_headers(header_text)
        return status_line, headers, body

    async def _async_open_upstream_connection(
        self,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Open a connection to the upstream cloud."""
        if self.upstream_host:
            return await asyncio.wait_for(
                asyncio.open_connection(self.upstream_host, self.upstream_port),
                timeout=UPSTREAM_TIMEOUT_SECONDS,
            )

        addresses = await self.dns_resolver.async_get_addresses()
        errors: list[str] = []

        for address in addresses:
            try:
                _LOGGER.debug(
                    "Level Sense connecting to resolved upstream %s for host %s",
                    address,
                    self.upstream_host_header,
                )
                return await asyncio.wait_for(
                    asyncio.open_connection(address, self.upstream_port),
                    timeout=UPSTREAM_TIMEOUT_SECONDS,
                )
            except Exception as err:
                errors.append(f"{address}: {err!r}")

        refreshed_addresses = await self.dns_resolver.async_get_addresses(force_refresh=True)

        for address in refreshed_addresses:
            try:
                _LOGGER.debug(
                    "Level Sense connecting to refreshed upstream %s for host %s",
                    address,
                    self.upstream_host_header,
                )
                return await asyncio.wait_for(
                    asyncio.open_connection(address, self.upstream_port),
                    timeout=UPSTREAM_TIMEOUT_SECONDS,
                )
            except Exception as err:
                errors.append(f"{address}: {err!r}")

        raise ConnectionError(
            f"Could not connect to upstream {self.upstream_host_header}: {'; '.join(errors)}"
        )

    def _observe_request(
        self,
        *,
        client_ip: str,
        method: str,
        path: str,
        headers: dict[str, str],
    ) -> None:
        """Observe a device request and update the coordinator."""
        parsed_url = urlsplit(path)
        query = parse_qs(parsed_url.query)
        json_values = query.get("json", [])

        if not json_values:
            _LOGGER.info(
                "Level Sense non-telemetry request observed: method=%s path=%s",
                method,
                parsed_url.path,
            )
            return

        raw_json = unquote(json_values[0])

        if self.log_payloads:
            _LOGGER.warning("Level Sense raw JSON: %s", raw_json)

        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError as err:
            self.coordinator.async_set_error(f"JSON decode error: {err}")
            _LOGGER.warning("Could not decode Level Sense JSON: %s", err)
            return

        self.coordinator.async_update_from_packet(
            client_ip=client_ip,
            method=method,
            request_path=parsed_url.path,
            headers=headers,
            payload=payload,
        )

    def _observe_response(self, raw_response: bytes, latency_ms: float | None) -> None:
        """Observe a cloud response and update the coordinator."""
        try:
            status_line, headers, body = self._split_response(raw_response)
            parts = status_line.split(" ")
            status_code = parts[1] if len(parts) > 1 else None

            decoded_body = self._decode_response_body(body, headers)
            body_text = decoded_body.decode("utf-8", errors="replace").strip()

            try:
                parsed_body: dict[str, Any] | str | None = json.loads(body_text)
            except json.JSONDecodeError:
                parsed_body = body_text[:1000]

            self.coordinator.async_update_cloud_response(
                status_code=status_code,
                status_line=status_line,
                body=parsed_body,
                latency_ms=latency_ms,
            )

        except Exception as err:
            _LOGGER.debug("Could not parse Level Sense cloud response: %r", err)

    def _decode_response_body(self, body: bytes, headers: dict[str, str]) -> bytes:
        """Decode response body."""
        if "chunked" in headers.get("transfer-encoding", "").lower():
            return self._decode_chunked_body(body)
        return body

    def _decode_chunked_body(self, body: bytes) -> bytes:
        """Decode HTTP chunked transfer body."""
        decoded = b""
        pos = 0

        while True:
            line_end = body.find(b"\r\n", pos)
            if line_end == -1:
                break

            size_line = body[pos:line_end].split(b";", 1)[0].strip()

            try:
                size = int(size_line, 16)
            except ValueError:
                return body

            pos = line_end + 2

            if size == 0:
                break

            decoded += body[pos : pos + size]
            pos += size + 2

        return decoded
"""HTTP/2 client backed by httpx + h2."""
from __future__ import annotations

import ssl
import time

import httpx

from httpbench.bench.metrics import RequestResult
from httpbench.clients.base import ProtocolClient

__all__ = ["Http2Client"]


class Http2Client(ProtocolClient):
    """HTTP/2-only client (no HTTP/1.1 fallback, so a mislabeled result can't
    silently sneak in if the server doesn't actually negotiate h2 via ALPN).

    httpx opens the TCP+TLS connection lazily on the first request rather than
    exposing a separate "connect" step, so `connect()` here only prepares the
    client - it does not, by itself, measure handshake time. For a fresh
    client, `request()` on the first call captures connection setup *and* the
    first request together. This asymmetry with `Http3Client` (where the QUIC
    handshake is directly measurable) is intentional and documented in
    `docs/protocol-comparison.md`; the `cold_start` scenario is what makes the
    two comparable again, since it always measures "fresh connection to first
    byte" for both protocols.
    """

    name = "HTTP/2"

    def __init__(self, base_url: str, verify: str | bool = True, timeout: float = 15.0) -> None:
        self._base_url = base_url
        # httpx deprecated passing a CA path directly as `verify=`; build an
        # SSLContext ourselves so a str (path to our local trustme CA) still works.
        self._verify: bool | ssl.SSLContext = (
            ssl.create_default_context(cafile=verify) if isinstance(verify, str) else verify
        )
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> float:
        start = time.perf_counter()
        self._client = httpx.AsyncClient(
            http2=True,
            http1=False,
            verify=self._verify,
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
        )
        return time.perf_counter() - start

    async def request(self, path: str, method: str = "GET") -> RequestResult:
        if self._client is None:
            raise RuntimeError("call connect() before request()")

        start = time.perf_counter()
        ttfb: float | None = None
        status: int | None = None
        http_version: str | None = None
        body_len = 0
        error: str | None = None
        try:
            async with self._client.stream(method, path) as response:
                ttfb = time.perf_counter() - start
                status = response.status_code
                http_version = response.http_version
                async for chunk in response.aiter_bytes():
                    body_len += len(chunk)
        except httpx.HTTPError as exc:
            error = f"{type(exc).__name__}: {exc}"

        return RequestResult(
            protocol=self.name,
            scenario="",
            path=path,
            status=status,
            bytes_received=body_len,
            ttfb=ttfb,
            total_time=time.perf_counter() - start,
            http_version=http_version,
            error=error,
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

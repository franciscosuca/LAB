"""Common interface implemented by both the HTTP/2 (httpx) and HTTP/3 (aioquic)
clients, so that benchmark scenarios in `httpbench.bench.scenarios` stay
completely protocol-agnostic - they only ever talk to a `ProtocolClient`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from httpbench.bench.metrics import RequestResult

__all__ = ["ProtocolClient"]


class ProtocolClient(ABC):
    #: Human-readable protocol name, e.g. ``"HTTP/2"`` or ``"HTTP/3"``. Used as
    #: a display label and as the dict key threaded through the CLI/report.
    name: str

    @abstractmethod
    async def connect(self) -> float:
        """Establish the underlying connection.

        Returns elapsed seconds when directly measurable (true for HTTP/3,
        where the QUIC handshake *is* the connection setup), or ``0.0`` when
        it isn't (HTTP/2 over TLS is opened lazily by httpx on first request -
        see `Http2Client` for details).
        """

    @abstractmethod
    async def request(self, path: str, method: str = "GET") -> RequestResult:
        """Perform a single request over the already-established connection."""

    @abstractmethod
    async def close(self) -> None:
        """Tear down the connection and release resources."""

    async def __aenter__(self) -> ProtocolClient:
        await self.connect()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

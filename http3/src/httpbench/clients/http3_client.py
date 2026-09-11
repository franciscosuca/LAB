"""HTTP/3 client backed by aioquic.

aioquic is a low-level, event-driven QUIC/HTTP3 implementation: there is no
`request()`-style convenience API like httpx's. The pattern below (subclassing
`QuicConnectionProtocol`, translating QUIC events into HTTP/3 events via
`H3Connection`, and resolving one `asyncio.Future` per stream when it ends) is
the standard way every aioquic-based HTTP/3 client is built - see aioquic's
own ``examples/http3_client.py`` for the reference implementation this is
adapted from.
"""
from __future__ import annotations

import asyncio
import ssl
import time
from contextlib import AsyncExitStack

from aioquic.asyncio import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import DataReceived, H3Event, HeadersReceived
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent

from httpbench.bench.metrics import RequestResult
from httpbench.clients.base import ProtocolClient

__all__ = ["Http3Client"]


class _StreamState:
    __slots__ = ("events", "start", "ttfb", "waiter")

    def __init__(self, start: float, waiter: asyncio.Future[_StreamState]) -> None:
        self.start = start
        self.ttfb: float | None = None
        self.events: list[H3Event] = []
        self.waiter = waiter


class _H3ClientProtocol(QuicConnectionProtocol):
    """Bridges aioquic's QUIC transport events to HTTP/3 events, and tracks
    per-stream request timing (time-to-first-byte, completion) so several
    requests can be in flight concurrently on the same connection - the whole
    point of HTTP/3 stream multiplexing.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self._http = H3Connection(self._quic)
        self._streams: dict[int, _StreamState] = {}

    def quic_event_received(self, event: QuicEvent) -> None:
        for http_event in self._http.handle_event(event):
            self._handle_h3_event(http_event)

    def _handle_h3_event(self, event: H3Event) -> None:
        if not isinstance(event, (HeadersReceived, DataReceived)):
            return
        state = self._streams.get(event.stream_id)
        if state is None:
            return
        if state.ttfb is None:
            state.ttfb = time.perf_counter() - state.start
        state.events.append(event)
        if event.stream_ended and not state.waiter.done():
            state.waiter.set_result(state)

    def send_request(self, authority: str, path: str, method: str = "GET") -> _StreamState:
        stream_id = self._quic.get_next_available_stream_id()
        waiter: asyncio.Future[_StreamState] = self._loop.create_future()
        state = _StreamState(time.perf_counter(), waiter)
        self._streams[stream_id] = state
        self._http.send_headers(
            stream_id=stream_id,
            headers=[
                (b":method", method.encode()),
                (b":scheme", b"https"),
                (b":authority", authority.encode()),
                (b":path", path.encode()),
            ],
            end_stream=True,
        )
        self.transmit()
        return state


class Http3Client(ProtocolClient):
    """Unlike HTTP/2-over-TLS, the QUIC handshake *is* the connection, so
    `connect()` measures it directly - no lazy-connect asymmetry here.
    """

    name = "HTTP/3"

    def __init__(self, host: str, port: int, verify: str | bool = True, timeout: float = 15.0) -> None:
        self._host = host
        self._port = port
        self._authority = f"{host}:{port}"
        self._timeout = timeout

        config = QuicConfiguration(alpn_protocols=H3_ALPN, is_client=True)
        if verify is False:
            config.verify_mode = ssl.CERT_NONE
        elif isinstance(verify, str):
            config.load_verify_locations(cafile=verify)
        # else: verify is True -> leave cafile/cadata/capath unset, aioquic
        # falls back to the certifi trust store (fine for real public hosts).
        self._config = config

        self._stack: AsyncExitStack | None = None
        self._protocol: _H3ClientProtocol | None = None

    async def connect(self) -> float:
        self._stack = AsyncExitStack()
        start = time.perf_counter()
        self._protocol = await self._stack.enter_async_context(
            connect(self._host, self._port, configuration=self._config, create_protocol=_H3ClientProtocol)
        )
        return time.perf_counter() - start

    async def request(self, path: str, method: str = "GET") -> RequestResult:
        if self._protocol is None:
            raise RuntimeError("call connect() before request()")

        state = self._protocol.send_request(self._authority, path, method)
        status: int | None = None
        body_len = 0
        error: str | None = None
        try:
            await asyncio.wait_for(asyncio.shield(state.waiter), timeout=self._timeout)
            for event in state.events:
                if isinstance(event, HeadersReceived):
                    for name, value in event.headers:
                        if name == b":status":
                            status = int(value.decode())
                elif isinstance(event, DataReceived):
                    body_len += len(event.data)
        except (asyncio.TimeoutError, ConnectionError) as exc:
            error = f"{type(exc).__name__}: {exc}"

        return RequestResult(
            protocol=self.name,
            scenario="",
            path=path,
            status=status,
            bytes_received=body_len,
            ttfb=state.ttfb,
            total_time=time.perf_counter() - state.start,
            http_version="HTTP/3",
            error=error,
        )

    async def close(self) -> None:
        if self._stack is not None:
            await self._stack.aclose()
            self._stack = None
            self._protocol = None

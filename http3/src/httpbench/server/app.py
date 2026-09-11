"""Demo API used as a controlled, repeatable benchmark target.

These endpoints are deliberately boring: they exist to produce predictable
response shapes (fixed sizes, N independent small resources, streamed
chunks, artificial delay) so that observed differences between HTTP/2 and
HTTP/3 come from the transport, not from the application.
"""
from __future__ import annotations

import asyncio
import time

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse
from starlette.routing import Route

# Guardrails so a benchmark run (or a typo) can't make the demo server try to
# allocate gigabytes of memory or block for minutes.
MAX_PAYLOAD_BYTES = 64 * 1024 * 1024
MAX_DELAY_MS = 10_000
MAX_STREAM_CHUNKS = 10_000

INDEX_HTML = """\
<h1>httpbench demo API</h1>
<p>Serves the same handlers over HTTP/1.1 + HTTP/2 (TCP) and HTTP/3 (QUIC/UDP).</p>
<ul>
  <li><code>GET /ping</code> - minimal JSON response, reports the negotiated HTTP version</li>
  <li><code>GET /payload/{size}</code> - returns exactly <code>size</code> bytes</li>
  <li><code>GET /assets/{n}</code> - a small (~500B) JSON resource, indexed by <code>n</code></li>
  <li><code>GET /stream/{chunks}?chunk_size=16384</code> - a chunked/streamed response</li>
  <li><code>GET /delay/{ms}</code> - sleeps server-side before responding</li>
</ul>
"""


async def index(request: Request) -> Response:
    return HTMLResponse(INDEX_HTML)


async def ping(request: Request) -> Response:
    return JSONResponse(
        {
            "ok": True,
            "http_version": request.scope.get("http_version"),
            "server_time": time.time(),
        }
    )


async def payload(request: Request) -> Response:
    size = max(0, min(int(request.path_params["size"]), MAX_PAYLOAD_BYTES))
    return PlainTextResponse(b"x" * size, media_type="application/octet-stream")


async def asset(request: Request) -> Response:
    n = int(request.path_params["n"])
    # Representative of a small page subresource (icon, tiny JSON blob, tracking pixel...).
    return JSONResponse({"asset": n, "padding": "x" * 480})


async def delay(request: Request) -> Response:
    ms = max(0, min(int(request.path_params["ms"]), MAX_DELAY_MS))
    await asyncio.sleep(ms / 1000)
    return JSONResponse({"slept_ms": ms})


async def stream(request: Request) -> Response:
    chunks = max(0, min(int(request.path_params["chunks"]), MAX_STREAM_CHUNKS))
    chunk_size = max(1, min(int(request.query_params.get("chunk_size", 16_384)), MAX_PAYLOAD_BYTES))

    async def body():
        for _ in range(chunks):
            yield b"x" * chunk_size

    return StreamingResponse(body(), media_type="application/octet-stream")


app = Starlette(
    routes=[
        Route("/", index),
        Route("/ping", ping),
        Route("/payload/{size:int}", payload),
        Route("/assets/{n:int}", asset),
        Route("/delay/{ms:int}", delay),
        Route("/stream/{chunks:int}", stream),
    ]
)

"""End-to-end smoke test: spins up the demo server in-process and performs a
real request over each protocol (real QUIC handshake included, not a mock).
Skipped automatically if this environment won't let us bind the sockets we
need (e.g. a sandbox that blocks raw UDP).
"""
from __future__ import annotations

import asyncio
import socket
from pathlib import Path

import pytest

from httpbench.certs import generate_certs
from httpbench.clients.http2_client import Http2Client
from httpbench.clients.http3_client import Http3Client
from httpbench.server import build_config


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def _run(port: int, ca_cert_path: Path, server_cert: Path, server_key: Path) -> tuple[int | None, int | None]:
    from hypercorn.asyncio import serve

    from httpbench.server.app import app as demo_app

    config = build_config("127.0.0.1", port, server_cert, server_key)
    shutdown_event = asyncio.Event()
    task = asyncio.create_task(serve(demo_app, config, shutdown_trigger=shutdown_event.wait))
    await asyncio.sleep(0.3)

    try:
        h2 = Http2Client(f"https://127.0.0.1:{port}", verify=str(ca_cert_path))
        await h2.connect()
        result_h2 = await h2.request("/ping")
        await h2.close()

        h3 = Http3Client("127.0.0.1", port, verify=str(ca_cert_path))
        await h3.connect()
        result_h3 = await h3.request("/ping")
        await h3.close()
    finally:
        shutdown_event.set()
        await task

    return result_h2.status, result_h3.status


def test_end_to_end_ping(tmp_path):
    port = _free_port()
    paths = generate_certs(tmp_path, ["localhost", "127.0.0.1"])

    try:
        status_h2, status_h3 = asyncio.run(_run(port, paths.ca_cert, paths.server_cert, paths.server_key))
    except OSError as exc:
        pytest.skip(f"Could not bind sockets in this environment: {exc}")

    assert status_h2 == 200
    assert status_h3 == 200

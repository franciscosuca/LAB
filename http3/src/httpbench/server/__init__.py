"""Runs the demo API with Hypercorn, bound to both a TCP socket (HTTP/1.1 and
HTTP/2, ALPN-negotiated over TLS) and a UDP socket on the same port number
(HTTP/3 over QUIC). TLS is mandatory for both: HTTP/2 needs it for ALPN and
HTTP/3/QUIC requires TLS 1.3 by specification.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path

from hypercorn.asyncio import serve
from hypercorn.config import Config

from httpbench.server.app import app

__all__ = ["app", "build_config", "run_server"]


def build_config(host: str, port: int, cert_file: Path, key_file: Path) -> Config:
    config = Config()
    bind = f"{host}:{port}"
    config.bind = [bind]  # TCP: HTTP/1.1 + HTTP/2 via ALPN
    config.quic_bind = [bind]  # UDP: HTTP/3 (same port number, different socket/protocol)
    config.certfile = str(cert_file)
    config.keyfile = str(key_file)
    config.alpn_protocols = ["h2", "http/1.1"]
    config.accesslog = None
    config.errorlog = "-"
    return config


async def run_server(
    host: str,
    port: int,
    cert_file: Path,
    key_file: Path,
    shutdown_trigger: Callable[[], Awaitable[object]] | None = None,
) -> None:
    config = build_config(host, port, cert_file, key_file)
    await serve(app, config, shutdown_trigger=shutdown_trigger)

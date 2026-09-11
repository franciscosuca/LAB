"""Benchmark scenarios.

Each scenario is protocol-agnostic: it only calls methods on a
`ProtocolClient`, so the exact same code path drives both the HTTP/2 and
HTTP/3 clients. This is what makes the comparison fair - any difference in
the numbers comes from the transport, not from different client-side logic.
"""
from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass

from httpbench.bench.metrics import RequestResult
from httpbench.clients.base import ProtocolClient

__all__ = ["ScenarioRun", "cold_start", "concurrency", "payload_sweep", "warm_latency"]

ClientFactory = Callable[[], ProtocolClient]


@dataclass
class ScenarioRun:
    name: str
    description: str
    results: list[RequestResult]
    duration_s: float


async def cold_start(factory: ClientFactory, path: str = "/ping", iterations: int = 15) -> ScenarioRun:
    """New connection per request. Highlights handshake cost: TCP+TLS (HTTP/2)
    vs QUIC's combined transport+crypto handshake (HTTP/3).
    """
    results: list[RequestResult] = []
    t0 = time.perf_counter()
    for _ in range(max(1, iterations)):
        start = time.perf_counter()
        client = factory()
        connect_time = 0.0
        try:
            connect_time = await client.connect()
            result = await client.request(path)
        except Exception as exc:  # noqa: BLE001 - a failed connection is data, not a crash
            result = RequestResult(
                protocol=client.name,
                scenario="cold_start",
                path=path,
                status=None,
                bytes_received=0,
                ttfb=None,
                total_time=time.perf_counter() - start,
                error=f"{type(exc).__name__}: {exc}",
            )
        finally:
            await client.close()
        result.scenario = "cold_start"
        result.connect_time = connect_time
        results.append(result)
    return ScenarioRun(
        "cold_start", "New connection per request (handshake + first byte)", results, time.perf_counter() - t0
    )


async def warm_latency(client: ProtocolClient, path: str = "/ping", iterations: int = 200) -> ScenarioRun:
    """Sequential requests over one already-open connection: steady-state latency."""
    results = []
    t0 = time.perf_counter()
    for _ in range(max(1, iterations)):
        result = await client.request(path)
        result.scenario = "warm_latency"
        results.append(result)
    return ScenarioRun("warm_latency", "Sequential requests, connection reused", results, time.perf_counter() - t0)


async def concurrency(client: ProtocolClient, path_template: str = "/assets/{i}", count: int = 30) -> ScenarioRun:
    """Fire `count` requests concurrently over a single connection (multiplexing).

    This is the scenario to pair with `--loss`/`--delay`: it's where HTTP/2's
    transport-level head-of-line blocking (all streams share one TCP byte
    stream) versus HTTP/3's independent QUIC streams becomes visible.
    """
    t0 = time.perf_counter()
    coros = [client.request(path_template.format(i=i)) for i in range(max(1, count))]
    results = list(await asyncio.gather(*coros))
    for result in results:
        result.scenario = "concurrency"
    return ScenarioRun(
        "concurrency", f"{count} concurrent requests, one connection (multiplexing)", results, time.perf_counter() - t0
    )


async def payload_sweep(client: ProtocolClient, sizes: list[int], repeats: int = 3) -> ScenarioRun:
    """Download a range of payload sizes to compare sustained throughput.

    On a fast, low-latency loopback link this is usually the scenario where
    HTTP/2 and HTTP/3 look *most* similar: once a connection is warmed up and
    the transfer is large enough to be bandwidth-bound rather than
    latency-bound, both protocols are limited by the same CPU/memory-copy
    costs rather than by transport framing differences.
    """
    results = []
    t0 = time.perf_counter()
    for size in sizes:
        for _ in range(max(1, repeats)):
            result = await client.request(f"/payload/{size}")
            result.scenario = f"payload_{size}"
            results.append(result)
    return ScenarioRun("payload_sweep", "Downloads across a range of payload sizes", results, time.perf_counter() - t0)

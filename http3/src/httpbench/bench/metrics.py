"""Result data structures and pure-stdlib statistics (no numpy/pandas needed)."""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field

__all__ = ["RequestResult", "ScenarioSummary", "Stats", "percentile"]


@dataclass
class RequestResult:
    """The outcome of a single HTTP request. All durations are in seconds."""

    protocol: str
    scenario: str
    path: str
    status: int | None
    bytes_received: int
    ttfb: float | None  # time to first byte/headers
    total_time: float  # time to full response body
    connect_time: float = 0.0  # connection setup time, when separately measurable (0 for reused connections)
    http_version: str | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.status is not None and 200 <= self.status < 400


def percentile(values: list[float], pct: float) -> float:
    """Linear-interpolated percentile (matches numpy.percentile's default), stdlib-only."""
    if not values:
        return 0.0
    data = sorted(values)
    if len(data) == 1:
        return data[0]
    k = (len(data) - 1) * (pct / 100)
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return data[int(k)]
    return data[lo] * (hi - k) + data[hi] * (k - lo)


@dataclass
class Stats:
    min: float = 0.0
    mean: float = 0.0
    p50: float = 0.0
    p90: float = 0.0
    p99: float = 0.0
    max: float = 0.0

    @classmethod
    def from_values(cls, values: list[float]) -> Stats:
        if not values:
            return cls()
        return cls(
            min=min(values),
            mean=statistics.fmean(values),
            p50=percentile(values, 50),
            p90=percentile(values, 90),
            p99=percentile(values, 99),
            max=max(values),
        )


@dataclass
class ScenarioSummary:
    protocol: str
    scenario: str
    count: int
    errors: int
    duration_s: float
    total_bytes: int
    ttfb_ms: Stats = field(default_factory=Stats)
    total_ms: Stats = field(default_factory=Stats)
    connect_ms: Stats = field(default_factory=Stats)
    throughput_rps: float = 0.0
    throughput_mbps: float = 0.0

    @classmethod
    def from_results(
        cls, protocol: str, scenario: str, results: list[RequestResult], duration_s: float
    ) -> ScenarioSummary:
        ok_results = [r for r in results if r.ok]
        errors = len(results) - len(ok_results)
        total_bytes = sum(r.bytes_received for r in ok_results)

        ttfb_values = [r.ttfb * 1000 for r in ok_results if r.ttfb is not None]
        total_values = [r.total_time * 1000 for r in ok_results]
        connect_values = [r.connect_time * 1000 for r in ok_results if r.connect_time]

        return cls(
            protocol=protocol,
            scenario=scenario,
            count=len(results),
            errors=errors,
            duration_s=duration_s,
            total_bytes=total_bytes,
            ttfb_ms=Stats.from_values(ttfb_values),
            total_ms=Stats.from_values(total_values),
            connect_ms=Stats.from_values(connect_values),
            throughput_rps=(len(ok_results) / duration_s) if duration_s > 0 else 0.0,
            throughput_mbps=(total_bytes * 8 / 1_000_000 / duration_s) if duration_s > 0 else 0.0,
        )

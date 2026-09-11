"""Turn raw `ScenarioRun` results into a Rich console report, JSON/CSV exports,
and (optionally) PNG comparison charts.
"""
from __future__ import annotations

import csv
import dataclasses
import time
from pathlib import Path

from rich.console import Console
from rich.table import Table

from httpbench.bench.metrics import RequestResult, ScenarioSummary
from httpbench.bench.scenarios import ScenarioRun
from httpbench.util import format_size

__all__ = [
    "ResultsByProtocol",
    "expand_scenarios",
    "export_csv",
    "export_json",
    "print_report",
    "save_charts",
    "summarize",
]

console = Console()

# protocol name -> scenario name -> ScenarioRun
ResultsByProtocol = dict[str, dict[str, ScenarioRun]]


def _ordered_union(dicts: list[dict[str, object]]) -> list[str]:
    seen: dict[str, None] = {}
    for d in dicts:
        for key in d:
            seen[key] = None
    return list(seen)


def _expand_payload_sweep(run: ScenarioRun) -> dict[str, ScenarioRun]:
    """`payload_sweep` bundles several payload sizes into one run; splitting it
    by size keeps the report from averaging together, say, 1KB and 1MB
    downloads into one meaningless number.
    """
    groups: dict[str, list[RequestResult]] = {}
    for result in run.results:
        groups.setdefault(result.scenario, []).append(result)

    def size_of(label: str) -> int:
        try:
            return int(label.rsplit("_", 1)[1])
        except (IndexError, ValueError):
            return 0

    expanded = {}
    for label in sorted(groups, key=size_of):
        group = groups[label]
        duration = sum(r.total_time for r in group)  # requests run sequentially within a size
        expanded[label] = ScenarioRun(label, f"Download {format_size(size_of(label))}", group, duration)
    return expanded


def expand_scenarios(all_runs: ResultsByProtocol) -> ResultsByProtocol:
    """Apply per-scenario post-processing (currently: splitting `payload_sweep`
    by size) uniformly across protocols before summarizing/reporting.
    """
    expanded: ResultsByProtocol = {}
    for protocol, scenarios in all_runs.items():
        expanded[protocol] = {}
        for name, run in scenarios.items():
            if name == "payload_sweep":
                expanded[protocol].update(_expand_payload_sweep(run))
            else:
                expanded[protocol][name] = run
    return expanded


def summarize(all_runs: ResultsByProtocol) -> dict[str, dict[str, ScenarioSummary]]:
    summaries: dict[str, dict[str, ScenarioSummary]] = {}
    for protocol, scenarios in all_runs.items():
        summaries[protocol] = {
            name: ScenarioSummary.from_results(protocol, name, run.results, run.duration_s)
            for name, run in scenarios.items()
        }
    return summaries


def print_report(all_runs: ResultsByProtocol) -> dict[str, dict[str, ScenarioSummary]]:
    all_runs = expand_scenarios(all_runs)
    summaries = summarize(all_runs)
    protocols = list(all_runs.keys())
    scenario_names = _ordered_union(list(all_runs.values()))

    for name in scenario_names:
        table = Table(title=f"Scenario: {name}")
        table.add_column("Protocol")
        table.add_column("Requests", justify="right")
        table.add_column("Errors", justify="right")
        table.add_column("TTFB p50", justify="right")
        table.add_column("TTFB p90", justify="right")
        table.add_column("TTFB p99", justify="right")
        table.add_column("Total p50", justify="right")
        table.add_column("Total p99", justify="right")
        table.add_column("Req/s", justify="right")
        table.add_column("Throughput", justify="right")

        for protocol in protocols:
            summary = summaries.get(protocol, {}).get(name)
            if summary is None:
                table.add_row(protocol, "-", "-", "-", "-", "-", "-", "-", "-", "-")
                continue
            table.add_row(
                protocol,
                str(summary.count),
                str(summary.errors),
                f"{summary.ttfb_ms.p50:.1f}ms",
                f"{summary.ttfb_ms.p90:.1f}ms",
                f"{summary.ttfb_ms.p99:.1f}ms",
                f"{summary.total_ms.p50:.1f}ms",
                f"{summary.total_ms.p99:.1f}ms",
                f"{summary.throughput_rps:.1f}",
                f"{summary.throughput_mbps:.2f} Mbps",
            )
        console.print(table)

    _print_takeaways(summaries, scenario_names, protocols)
    return summaries


def _print_takeaways(
    summaries: dict[str, dict[str, ScenarioSummary]], scenario_names: list[str], protocols: list[str]
) -> None:
    if len(protocols) != 2:
        return
    a, b = protocols
    console.print("\n[bold]Takeaways[/bold] (median total time this run - re-run a few times, numbers vary):")
    for name in scenario_names:
        sa = summaries.get(a, {}).get(name)
        sb = summaries.get(b, {}).get(name)
        if not sa or not sb or sa.total_ms.p50 == 0 or sb.total_ms.p50 == 0:
            continue
        if sa.total_ms.p50 < sb.total_ms.p50:
            faster, slower, ratio = a, b, sb.total_ms.p50 / sa.total_ms.p50
        else:
            faster, slower, ratio = b, a, sa.total_ms.p50 / sb.total_ms.p50
        console.print(f"  - {name}: [green]{faster}[/green] was {ratio:.2f}x faster than {slower} at the median")
    console.print(
        "\n[dim]See docs/protocol-comparison.md to map these numbers to the underlying "
        "protocol mechanics (handshakes, head-of-line blocking, congestion control...).[/dim]"
    )


def export_json(
    all_runs: ResultsByProtocol, summaries: dict[str, dict[str, ScenarioSummary]], out_path: Path
) -> None:
    all_runs = expand_scenarios(all_runs)
    payload = {
        "generated_at": time.time(),
        "summaries": {
            protocol: {name: dataclasses.asdict(s) for name, s in scenarios.items()}
            for protocol, scenarios in summaries.items()
        },
        "raw_results": {
            protocol: {name: [dataclasses.asdict(r) for r in run.results] for name, run in scenarios.items()}
            for protocol, scenarios in all_runs.items()
        },
    }
    out_path.write_text(_json_dumps(payload))


def _json_dumps(payload: object) -> str:
    import json

    return json.dumps(payload, indent=2, default=str)


def export_csv(all_runs: ResultsByProtocol, out_path: Path) -> None:
    all_runs = expand_scenarios(all_runs)
    with out_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["protocol", "scenario", "path", "status", "bytes", "ttfb_ms", "total_ms", "connect_ms", "http_version", "error"]
        )
        for scenarios in all_runs.values():
            for run in scenarios.values():
                for r in run.results:
                    writer.writerow(
                        [
                            r.protocol,
                            r.scenario,
                            r.path,
                            r.status,
                            r.bytes_received,
                            None if r.ttfb is None else round(r.ttfb * 1000, 3),
                            round(r.total_time * 1000, 3),
                            round(r.connect_time * 1000, 3),
                            r.http_version,
                            r.error,
                        ]
                    )


def save_charts(
    all_runs: ResultsByProtocol, summaries: dict[str, dict[str, ScenarioSummary]], out_dir: Path
) -> list[Path]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - exercised only without the extra installed
        raise RuntimeError("Charts require matplotlib: pip install 'httpbench[charts]'") from exc

    all_runs = expand_scenarios(all_runs)
    out_dir.mkdir(parents=True, exist_ok=True)
    protocols = list(all_runs.keys())
    scenario_names = _ordered_union(list(all_runs.values()))
    saved: list[Path] = []

    def grouped_bars(ax, categories: list[str], series: dict[str, list[float]], ylabel: str, title: str) -> None:
        width = 0.8 / max(1, len(series))
        x = range(len(categories))
        for i, (label, values) in enumerate(series.items()):
            offset = (i - (len(series) - 1) / 2) * width
            ax.bar([xi + offset for xi in x], values, width=width, label=label)
        ax.set_xticks(list(x))
        ax.set_xticklabels(categories, rotation=20, ha="right")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend()

    # One latency-percentile chart per scenario.
    for name in scenario_names:
        fig, ax = plt.subplots(figsize=(6, 4))
        metrics = ["p50", "p90", "p99"]
        series = {
            protocol: [getattr(summaries[protocol][name].total_ms, m) for m in metrics]
            for protocol in protocols
            if name in summaries.get(protocol, {})
        }
        if series:
            grouped_bars(ax, metrics, series, "Total request time (ms)", f"{name}: latency percentiles")
            fig.tight_layout()
            path = out_dir / f"{name}_latency.png"
            fig.savefig(path)
            saved.append(path)
        plt.close(fig)

    # One throughput chart across all scenarios.
    fig, ax = plt.subplots(figsize=(8, 4))
    series = {
        protocol: [summaries.get(protocol, {}).get(name, ScenarioSummaryZero()).throughput_rps for name in scenario_names]
        for protocol in protocols
    }
    grouped_bars(ax, scenario_names, series, "Requests / second", "Throughput by scenario")
    fig.tight_layout()
    path = out_dir / "throughput.png"
    fig.savefig(path)
    plt.close(fig)
    saved.append(path)

    return saved


class ScenarioSummaryZero:
    """Stand-in with `throughput_rps == 0.0` for scenarios a protocol has no data for."""

    throughput_rps = 0.0

"""Command-line interface for httpbench."""
from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.markup import escape

from httpbench.bench import network_impair, report
from httpbench.bench import scenarios as sc
from httpbench.bench.network_impair import NetworkImpairmentError
from httpbench.certs import cert_paths, generate_certs
from httpbench.clients.base import ProtocolClient
from httpbench.clients.http2_client import Http2Client
from httpbench.clients.http3_client import Http3Client
from httpbench.util import parse_alt_svc_h3_port, parse_size

app = typer.Typer(add_completion=False, no_args_is_help=True, help=__doc__)
console = Console()

DEFAULT_HOSTS = ["localhost", "127.0.0.1", "::1"]
DEFAULT_SCENARIOS = "cold_start,warm_latency,concurrency,payload"
DEFAULT_SIZES = "1KB,100KB,1MB"
VerifyArg = str | bool


# --------------------------------------------------------------------------- #
# certs / serve
# --------------------------------------------------------------------------- #


@app.command()
def certs(
    out_dir: Path = typer.Option(Path("certs"), help="Where to write ca.pem/server.crt/server.key"),
    hosts: str = typer.Option(",".join(DEFAULT_HOSTS), help="Comma-separated SANs for the server cert"),
) -> None:
    """Generate a throwaway local CA + server certificate for the demo server."""
    paths = generate_certs(out_dir, hosts.split(","))
    console.print(f"[green]Wrote[/green] {paths.ca_cert}, {paths.server_cert}, {paths.server_key}")
    console.print(f"Pass [bold]--ca-cert {paths.ca_cert}[/bold] to `httpbench bench` to trust this server.")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(4433),
    certs_dir: Path = typer.Option(Path("certs")),
) -> None:
    """Run the demo API over HTTP/1.1 + HTTP/2 (TCP) and HTTP/3 (QUIC/UDP) on the same port."""
    from httpbench.server import run_server  # local import: keeps hypercorn optional for pure-client use

    paths = cert_paths(certs_dir)
    if not paths.exists():
        console.print(f"[yellow]No certs found in {certs_dir}, generating...[/yellow]")
        paths = generate_certs(certs_dir, DEFAULT_HOSTS)

    console.print(f"[bold]Serving[/bold] on https://{host}:{port} (HTTP/2 over TCP, HTTP/3 over UDP). Ctrl+C to stop.")
    try:
        asyncio.run(run_server(host, port, paths.server_cert, paths.server_key))
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")


# --------------------------------------------------------------------------- #
# shared benchmark driver
# --------------------------------------------------------------------------- #


def _make_factories(host: str, h2_port: int, h3_port: int, verify: VerifyArg, timeout: float) -> dict[str, sc.ClientFactory]:
    return {
        "HTTP/2": lambda: Http2Client(f"https://{host}:{h2_port}", verify=verify, timeout=timeout),
        "HTTP/3": lambda: Http3Client(host, h3_port, verify=verify, timeout=timeout),
    }


async def run_bench(
    host: str,
    h2_port: int,
    h3_port: int,
    verify: VerifyArg,
    protocols: list[str],
    scenario_names: list[str],
    iterations: int,
    concurrency_count: int,
    sizes: list[int],
    timeout: float,
    loss: float = 0.0,
    delay: float = 0.0,
    interface: str = "lo",
) -> report.ResultsByProtocol:
    """Run the requested scenarios for each protocol and return the raw results.

    Each protocol is benchmarked independently and failures are isolated: if
    HTTP/3 can't connect at all (e.g. UDP blocked by a firewall), HTTP/2
    results are still produced and reported instead of the whole run aborting.
    """
    factories = _make_factories(host, h2_port, h3_port, verify, timeout)
    all_runs: report.ResultsByProtocol = {}

    with network_impair.impair(interface=interface, loss_pct=loss, delay_ms=delay):
        for protocol in protocols:
            if protocol not in factories:
                console.print(f"[red]Unknown protocol {protocol!r}, skipping (expected HTTP/2 or HTTP/3)[/red]")
                continue
            console.print(f"\n[bold cyan]== {protocol} ==[/bold cyan]")
            factory = factories[protocol]
            try:
                all_runs[protocol] = await _run_protocol_scenarios(
                    factory, scenario_names, iterations, concurrency_count, sizes
                )
            except Exception as exc:  # noqa: BLE001 - one protocol's failure shouldn't kill the whole run
                console.print(f"[red]{protocol} failed: {escape(f'{type(exc).__name__}: {exc}')}[/red]")

    return all_runs


async def _run_protocol_scenarios(
    factory: sc.ClientFactory,
    scenario_names: list[str],
    iterations: int,
    concurrency_count: int,
    sizes: list[int],
) -> dict[str, sc.ScenarioRun]:
    runs: dict[str, sc.ScenarioRun] = {}

    if "cold_start" in scenario_names:
        console.print("  running cold_start...")
        runs["cold_start"] = await sc.cold_start(factory, iterations=max(5, iterations // 4))

    needs_warm_connection = any(s in scenario_names for s in ("warm_latency", "concurrency", "payload"))
    if not needs_warm_connection:
        return runs

    client: ProtocolClient = factory()
    try:
        await client.connect()
    except Exception as exc:  # noqa: BLE001 - keep whatever runs (e.g. cold_start) already succeeded
        console.print(
            f"[red]  could not open a persistent connection: {escape(f'{type(exc).__name__}: {exc}')}[/red]"
        )
        return runs
    try:
        if "warm_latency" in scenario_names:
            console.print("  running warm_latency...")
            runs["warm_latency"] = await sc.warm_latency(client, iterations=iterations)
        if "concurrency" in scenario_names:
            console.print("  running concurrency...")
            runs["concurrency"] = await sc.concurrency(client, count=concurrency_count)
        if "payload" in scenario_names:
            console.print("  running payload_sweep...")
            runs["payload_sweep"] = await sc.payload_sweep(client, sizes=sizes)
    finally:
        await client.close()

    return runs


async def _discover_h3_port(host: str, h2_port: int, verify: VerifyArg, timeout: float) -> int | None:
    """Mimic what browsers do: read the `Alt-Svc` header off an HTTP/2 response
    to find out which UDP port the server advertises HTTP/3 on.
    """
    try:
        async with httpx.AsyncClient(http2=True, verify=verify, timeout=timeout) as client:
            response = await client.get(f"https://{host}:{h2_port}/")
            return parse_alt_svc_h3_port(response.headers.get("alt-svc"))
    except httpx.HTTPError:
        return None


def _run_or_exit(coro):
    """Run an async CLI action, turning expected user-facing errors (e.g. an
    unsupported --loss/--delay platform) into a clean message instead of a
    full traceback.
    """
    try:
        return asyncio.run(coro)
    except NetworkImpairmentError as exc:
        console.print(f"[red]{escape(str(exc))}[/red]")
        raise typer.Exit(code=1) from None


def _resolve_verify(insecure: bool, ca_cert: Path | None) -> VerifyArg:
    if insecure:
        return False
    if ca_cert:
        return str(ca_cert)
    default_ca = cert_paths(Path("certs")).ca_cert
    if default_ca.exists():
        return str(default_ca)
    return True  # system trust store - correct default for real public hosts


def _save_outputs(all_runs: report.ResultsByProtocol, output: Path, charts: bool) -> None:
    summaries = report.print_report(all_runs)
    output.mkdir(parents=True, exist_ok=True)
    report.export_json(all_runs, summaries, output / "results.json")
    report.export_csv(all_runs, output / "results.csv")
    console.print(f"\nSaved raw results to [bold]{output}/results.json[/bold] and [bold]{output}/results.csv[/bold]")
    if charts:
        try:
            chart_paths = report.save_charts(all_runs, summaries, output)
        except RuntimeError as exc:
            console.print(f"[red]{escape(str(exc))}[/red]")
            raise typer.Exit(code=1) from None
        console.print(f"Saved {len(chart_paths)} chart(s) to [bold]{output}/[/bold]")


# --------------------------------------------------------------------------- #
# bench (against a local demo server or any real HTTP/2+HTTP/3 API)
# --------------------------------------------------------------------------- #


@app.command()
def bench(
    host: str = typer.Option("127.0.0.1", help="Target host - the demo server, or any real API"),
    port: int = typer.Option(4433, help="Used for both HTTP/2 (TCP) and HTTP/3 (UDP) unless overridden"),
    h2_port: int | None = typer.Option(None, help="Override the HTTP/2 (TCP) port"),
    h3_port: int | None = typer.Option(None, help="Override the HTTP/3 (UDP) port"),
    ca_cert: Path | None = typer.Option(None, help="CA cert to trust (defaults to certs/ca.pem if present)"),
    insecure: bool = typer.Option(False, help="Disable certificate verification"),
    protocols: str = typer.Option("HTTP/2,HTTP/3"),
    scenarios: str = typer.Option(DEFAULT_SCENARIOS, help="cold_start,warm_latency,concurrency,payload"),
    iterations: int = typer.Option(50, help="Requests for warm_latency; cold_start uses iterations // 4"),
    concurrency: int = typer.Option(30, help="Concurrent requests for the concurrency scenario"),
    sizes: str = typer.Option(DEFAULT_SIZES, help="Comma-separated payload sizes, e.g. 1KB,100KB,1MB"),
    timeout: float = typer.Option(15.0, help="Per-request timeout in seconds"),
    loss: float = typer.Option(0.0, help="Simulated packet loss percent (Linux tc/netem only, see README)"),
    delay: float = typer.Option(0.0, help="Simulated extra latency in ms (Linux tc/netem only)"),
    interface: str = typer.Option("lo", help="Interface to impair when --loss/--delay is set"),
    output: Path = typer.Option(Path("results")),
    charts: bool = typer.Option(False, help="Also save PNG comparison charts (requires the `charts` extra)"),
    discover_h3: bool = typer.Option(
        True, help="If --h3-port isn't set, discover it from the server's Alt-Svc header"
    ),
) -> None:
    """Run the benchmark suite against `host` for HTTP/2 and HTTP/3 side by side.

    Works against the bundled demo server (`httpbench serve`) or against any
    real API that supports both protocols - just point `--host`/`--port` at it
    and drop `--ca-cert`/`--insecure` (real hosts use publicly-trusted certs).
    """
    verify = _resolve_verify(insecure, ca_cert)
    resolved_h2_port = h2_port or port
    resolved_h3_port = h3_port

    if resolved_h3_port is None and discover_h3:
        console.print("Discovering HTTP/3 port via Alt-Svc...")
        resolved_h3_port = asyncio.run(_discover_h3_port(host, resolved_h2_port, verify, timeout))
        if resolved_h3_port:
            console.print(f"  found h3 on UDP port {resolved_h3_port}")
    resolved_h3_port = resolved_h3_port or port

    console.print(f"Target: h2=https://{host}:{resolved_h2_port}/ (TCP)  h3=https://{host}:{resolved_h3_port}/ (UDP)")

    all_runs = _run_or_exit(
        run_bench(
            host,
            resolved_h2_port,
            resolved_h3_port,
            verify,
            protocols.split(","),
            scenarios.split(","),
            iterations,
            concurrency,
            [parse_size(s) for s in sizes.split(",")],
            timeout,
            loss,
            delay,
            interface,
        )
    )
    if not all_runs:
        console.print("[red]No results for either protocol - see errors above.[/red]")
        raise typer.Exit(code=1)

    _save_outputs(all_runs, output, charts)


# --------------------------------------------------------------------------- #
# quickstart: demo server + benchmark in one shot, no separate terminal needed
# --------------------------------------------------------------------------- #


@app.command()
def quickstart(
    port: int = typer.Option(4433),
    certs_dir: Path = typer.Option(Path("certs")),
    output: Path = typer.Option(Path("results")),
    charts: bool = typer.Option(False, help="Also save PNG comparison charts (requires the `charts` extra)"),
    iterations: int = typer.Option(50),
    concurrency: int = typer.Option(30),
    sizes: str = typer.Option(DEFAULT_SIZES),
    scenarios: str = typer.Option(DEFAULT_SCENARIOS),
) -> None:
    """Start the local demo server, benchmark it, stop it, and print the report - one command."""
    _run_or_exit(_quickstart(port, certs_dir, output, charts, iterations, concurrency, sizes, scenarios))


async def _quickstart(
    port: int,
    certs_dir: Path,
    output: Path,
    charts: bool,
    iterations: int,
    concurrency: int,
    sizes: str,
    scenarios: str,
) -> None:
    from hypercorn.asyncio import serve

    from httpbench.server import build_config
    from httpbench.server.app import app as demo_app

    paths = cert_paths(certs_dir)
    if not paths.exists():
        console.print(f"[yellow]No certs found, generating in {certs_dir}...[/yellow]")
        paths = generate_certs(certs_dir, DEFAULT_HOSTS)

    config = build_config("127.0.0.1", port, paths.server_cert, paths.server_key)
    shutdown_event = asyncio.Event()
    server_task = asyncio.create_task(serve(demo_app, config, shutdown_trigger=shutdown_event.wait))
    await asyncio.sleep(0.3)  # give the sockets a moment to bind before hammering them

    try:
        all_runs = await run_bench(
            "127.0.0.1",
            port,
            port,
            str(paths.ca_cert),
            ["HTTP/2", "HTTP/3"],
            scenarios.split(","),
            iterations,
            concurrency,
            [parse_size(s) for s in sizes.split(",")],
            timeout=15.0,
        )
    finally:
        shutdown_event.set()
        await server_task

    if not all_runs:
        console.print("[red]No results for either protocol - see errors above.[/red]")
        raise typer.Exit(code=1)

    _save_outputs(all_runs, output, charts)


if __name__ == "__main__":
    app()

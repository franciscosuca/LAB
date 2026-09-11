# httpbench: HTTP/2 vs HTTP/3, side by side

A small Python toolkit for **comparing and benchmarking HTTP/2 and HTTP/3
(QUIC)** against the same API, so you can *see* the differences instead of
just reading about them. It includes:

- A **demo API** (Starlette) served over both protocols at once - HTTP/1.1 and
  HTTP/2 over TCP/TLS, HTTP/3 over QUIC/UDP - via Hypercorn, with a
  one-command TLS setup (no browser warnings, no `openssl` incantations).
- A **benchmark CLI** that drives both protocols through an identical set of
  scenarios (cold-start/handshake cost, steady-state latency, concurrent
  multiplexed requests, payload-size sweeps) using the *same* client-side
  logic, so any measured difference comes from the transport, not from the
  benchmark code.
- Optional **simulated packet loss/latency** (Linux `tc netem`) to reproduce
  HTTP/2's transport-level head-of-line blocking versus HTTP/3's independent
  QUIC streams - the effect that's hardest to see on a clean local network.
- A **report**: Rich tables in your terminal, plus JSON/CSV exports and
  optional PNG charts.
- It also works against **any real API** that already speaks HTTP/2 and
  HTTP/3 (not just the bundled demo server) - see
  [Benchmarking a real API](#benchmarking-a-real-api).
- [`docs/protocol-comparison.md`](docs/protocol-comparison.md): a from-scratch
  explanation of *why* HTTP/3 exists, mapped directly onto this project's
  scenarios and metrics.

## Requirements

- Python 3.10-3.13 (tested on 3.12; needs a Python that has an `aioquic`
  wheel available - CPython's 3.14 is very new and may not yet).
- Linux, macOS, or Windows. `--loss`/`--delay` packet-loss simulation is
  Linux-only (see [Simulating packet loss](#simulating-packet-loss-and-latency)).
- Outbound UDP must be allowed for HTTP/3 to work at all - some corporate
  networks/VPNs block or throttle UDP. If HTTP/3 requests time out, see
  [Troubleshooting](#troubleshooting).

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate       # .venv\Scripts\activate on Windows
pip install -e ".[charts]"      # drop `[charts]` to skip the matplotlib dependency
```

This installs the `httpbench` console script (and you can always run it as
`python -m httpbench.cli` instead).

## Quickstart

The fastest way to see real numbers, no separate server terminal needed:

```bash
httpbench quickstart --charts
```

This generates local certs on first run, starts the demo API over both
protocols in-process, benchmarks it, stops the server, and prints a report
like:

```
                              Scenario: cold_start
┏━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┓
┃Protocol ┃ Requests ┃ Errors ┃ TTFB p50 ┃ TTFB p90 ┃ TTFB p99 ┃ Total p50 ┃ Total p99 ┃ Req/s ┃ Throughput ┃
┡━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━┩
│ HTTP/2  │       12 │      0 │    2.1ms │    3.4ms │    3.9ms │     2.3ms │     4.1ms │ 210.4 │  0.06 Mbps │
│ HTTP/3  │       12 │      0 │    3.0ms │    4.2ms │    4.8ms │     3.2ms │     5.0ms │ 156.7 │  0.05 Mbps │
└─────────┴──────────┴────────┴──────────┴──────────┴──────────┴───────────┴───────────┴───────┴────────────┘
...
Takeaways (median total time this run - re-run a few times, numbers vary):
  - cold_start: HTTP/2 was 1.39x faster than HTTP/3 at the median
  - concurrency: HTTP/3 was 1.10x faster than HTTP/2 at the median
```

Numbers above are illustrative, not a claim - on loopback with no induced
loss, differences are small and can go either way run to run (see
[Reading the results honestly](#reading-the-results-honestly)). Run it a few
times, then read on to make the gap actually show up.

## Manual flow (separate server/client, more control)

```bash
# 1. Generate a local CA + server certificate (once)
httpbench certs

# 2. In one terminal: run the demo API over HTTP/2 + HTTP/3
httpbench serve

# 3. In another terminal: benchmark it
httpbench bench --charts
```

`bench` writes `results/results.json`, `results/results.csv`, and (with
`--charts`) `results/*.png`.

## Benchmarking a real API

`bench` isn't tied to the bundled demo server - point it at any host that
serves both protocols on 443 and drop the local-cert options (public hosts
use publicly-trusted certificates, verified against your system trust store
by default):

```bash
httpbench bench --host www.cloudflare.com --port 443 --scenarios cold_start,warm_latency,payload
```

`bench` reads the target's `Alt-Svc` response header to auto-discover the
HTTP/3 UDP port (exactly what browsers do) - override with `--h3-port` if a
server advertises a non-default one. Not every API supports HTTP/3 yet (it's
extremely common behind CDNs like Cloudflare/Fastly/Google, less common on
origin servers you run yourself); check first with
[http3check.net](https://http3check.net/) or:

```bash
httpbench bench --host your-api.example.com --port 443 --protocols HTTP/3 --scenarios cold_start
```

If it errors out, your API doesn't speak HTTP/3 (yet) - use the bundled demo
server to learn the concepts, and see
[docs/protocol-comparison.md](docs/protocol-comparison.md#adding-http3-to-your-own-api)
for how to add HTTP/3 in front of a real API.

## CLI reference

| Command | Purpose |
|---|---|
| `httpbench certs` | Generate a local CA + server certificate (`certs/`) |
| `httpbench serve` | Run the demo API over HTTP/1.1 + HTTP/2 (TCP) and HTTP/3 (UDP) |
| `httpbench bench` | Benchmark HTTP/2 vs HTTP/3 against `--host`/`--port` (demo server or real API) |
| `httpbench quickstart` | `serve` + `bench` in one process, no separate terminal |

Run `httpbench <command> --help` for the full option list. Key `bench`/`quickstart` options:

| Option | Default | Meaning |
|---|---|---|
| `--scenarios` | `cold_start,warm_latency,concurrency,payload` | Which scenarios to run (see below) |
| `--iterations` | `50` | Requests for `warm_latency`; `cold_start` uses `iterations // 4` |
| `--concurrency` | `30` | Concurrent requests for the `concurrency` scenario |
| `--sizes` | `1KB,100KB,1MB` | Payload sizes for the `payload` scenario |
| `--loss` / `--delay` | `0` | Simulated packet loss %% / extra latency ms (Linux only) |
| `--charts` | off | Save PNG comparison charts (needs `pip install -e ".[charts]"`) |
| `--insecure` | off | Skip certificate verification instead of using `--ca-cert` |

### Scenarios

| Scenario | What it measures | What it's meant to reveal |
|---|---|---|
| `cold_start` | Brand-new connection -> first byte, repeated | Handshake cost: TCP+TLS (HTTP/2) vs QUIC's combined transport+crypto handshake (HTTP/3) |
| `warm_latency` | Sequential requests over one already-open connection | Steady-state per-request overhead once the connection is warm |
| `concurrency` | N requests fired concurrently over one connection | Stream multiplexing; pair with `--loss`/`--delay` to see HTTP/2's transport-level head-of-line blocking vs HTTP/3's independent streams |
| `payload` | Downloads across a range of sizes | Sustained throughput once a transfer is large enough to be bandwidth-bound rather than latency-bound |

## Simulating packet loss and latency

The single biggest reason QUIC exists is to fix TCP's head-of-line blocking:
in HTTP/2, all multiplexed streams share one TCP byte stream, so **one lost
packet stalls every stream** until it's retransmitted. HTTP/3's streams are
independent at the QUIC layer, so a lost packet only stalls the stream it
belongs to. On a clean loopback connection with ~0% loss, this difference
mostly disappears - you have to inject loss to see it:

```bash
sudo httpbench bench --scenarios concurrency --loss 3 --delay 40 --concurrency 50
```

This uses `tc netem` on the `lo` interface and is **Linux-only** (needs
`NET_ADMIN`: root, `sudo`, or `--cap-add=NET_ADMIN` in a container). On
macOS/Windows, run this project inside a Linux VM or container, e.g.:

```bash
docker run --rm -it --cap-add=NET_ADMIN -v "$PWD":/app -w /app python:3.12-slim bash -c \
  "apt-get update -qq && apt-get install -y -qq iproute2 >/dev/null && \
   pip install -e . -q && httpbench quickstart --loss 3 --delay 40 --concurrency 50"
```

Compare `--loss 0` against `--loss 3 --delay 40` on the `concurrency`
scenario and watch HTTP/2's p99 latency degrade much faster than HTTP/3's.
See [docs/protocol-comparison.md](docs/protocol-comparison.md) for why.

## Reading the results honestly

- **Loopback is not the internet.** With ~0ms RTT and ~0% loss, most of
  HTTP/3's advantages (faster handshakes on high-latency links, no
  head-of-line blocking on lossy links, connection migration) have nothing to
  bite into. Use `--loss`/`--delay`, or benchmark a real remote host, to see
  them.
- **HTTP/2 `cold_start` isn't perfectly apples-to-apples.** httpx opens the
  TCP+TLS connection lazily on the first request rather than exposing a
  separate "connect" step, so for HTTP/2, `cold_start` measures "new
  connection to first byte" as one number. For HTTP/3, the QUIC handshake
  *is* directly measurable, so you'll also see `connect_ms` broken out
  separately in `results.csv`/`results.json`. The `cold_start` total-time
  column is the fair, comparable number; treat HTTP/3's separate handshake
  number as a bonus data point. See `docs/protocol-comparison.md` for details.
- **QUIC is userspace; TCP is (usually) kernel-space.** Even when HTTP/3
  "wins" on latency, it typically costs more CPU per byte, especially at
  higher throughput. This project doesn't measure CPU usage directly - if you
  care, profile with `py-spy` or `psutil` while running `payload` with large
  sizes.
- **Run more than once.** These are wall-clock benchmarks on shared machines;
  a single run is a data point, not a verdict. `results.csv` has raw
  per-request numbers if you want to do your own statistics across runs.

## Project layout

```
src/httpbench/
├── cli.py                 # Typer CLI: certs, serve, bench, quickstart
├── certs.py                # trustme-based local CA + server cert generation
├── util.py                  # size parsing/formatting, Alt-Svc header parsing
├── server/
│   ├── app.py                # Starlette demo API (ping, payload, assets, stream, delay)
│   └── __init__.py            # Hypercorn wiring: one port, HTTP/2 (TCP) + HTTP/3 (UDP)
├── clients/
│   ├── base.py                # ProtocolClient interface shared by both protocols
│   ├── http2_client.py          # httpx-based HTTP/2 client
│   └── http3_client.py          # aioquic-based HTTP/3 client
└── bench/
    ├── metrics.py                # RequestResult / ScenarioSummary / percentiles
    ├── scenarios.py               # cold_start, warm_latency, concurrency, payload_sweep
    ├── network_impair.py           # optional tc/netem loss+delay injection (Linux)
    └── report.py                   # Rich tables, JSON/CSV export, PNG charts
docs/protocol-comparison.md   # HTTP/2 vs HTTP/3 deep dive, mapped to this project
tests/                        # unit tests (metrics/util) + a real end-to-end smoke test
```

## Troubleshooting

- **`Http3Client` / HTTP/3 requests time out, HTTP/2 works fine**: something
  is blocking UDP (corporate firewall, some VPNs, some public wifi). Try a
  different network, or confirm with `httpbench bench --protocols HTTP/3`
  against a known-good public HTTP/3 host.
- **Certificate verification errors against the demo server**: run
  `httpbench certs` first, and pass `--ca-cert certs/ca.pem` (this is the
  default already if `certs/ca.pem` exists) - or `--insecure` for quick,
  throwaway local testing.
- **`OSError: [Errno 48] Address already in use`**: another process is on
  that port; pick another with `--port`, or stop the other `httpbench serve`.
- **Charts fail with an ImportError**: install the optional extra:
  `pip install -e ".[charts]"`.
- **`--loss`/`--delay` raise `NetworkImpairmentError`**: they require Linux
  and `tc` (iproute2) with `NET_ADMIN` - see
  [Simulating packet loss](#simulating-packet-loss-and-latency).

## Running the tests

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT - see [LICENSE](LICENSE).

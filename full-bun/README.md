# full-bun

Three little projects in one repo:

1. **`bun-service`** — package management, bundling, dev server and
   production runtime handled *entirely* by **Bun 1.4** (no webpack, no
   esbuild-cli, no vite). Uses `bun install`, `Bun.build` (built-in bundler)
   and `Bun.serve` (built-in HTTP server, including native HTML
   entrypoints for on-the-fly dev bundling).
2. **`vite-service`** — the same app (React instead of Preact, same API
   surface), built and served with **Vite** (esbuild pre-bundling +
   Rollup for production, Vite's own dev/preview servers).
3. **`benchmark`** — a Bun script that boots every variant of both
   services, measures **page load time** and **requests/second** for
   each, and prints/save a comparison report.

```
full-bun/
├── bun-service/    Bun-only app (install + bundle + serve)
├── vite-service/   Vite app (install with bun, bundle/serve with vite)
└── benchmark/      load-testing + reporting tool
```

Requires **Bun ≥ 1.4** (`bun upgrade` if you're on an older version).

## Install everything

This is a Bun workspace — one install at the root wires up all three
packages:

```sh
bun install
```

## bun-service

Everything here runs through Bun:

```sh
cd bun-service
bun run dev      # Bun.serve + native HTML import, bundles src/app.tsx on the fly
bun run build    # Bun.build → ./dist (minified, code-split, sourcemaps)
bun run start    # NODE_ENV=production Bun.serve, serves ./dist statically
bun run preview  # build + start in one go
```

Open http://localhost:3001. Endpoints:

- `GET /` — HTML page (Preact) with client-side counter + a fetch call
- `GET /api/hello` — `{ message, runtime, time }`
- `GET /api/health` — `{ status: "ok" }`
- `GET /api/stats` — does a bit of CPU work server-side, for a "real"
  RPS test that isn't just "return a string"

## vite-service

Package management still via `bun install`/`bun add`, but bundling and
serving is 100% Vite (through a tiny custom plugin that adds the same
`/api/*` routes to both the dev server and `vite preview`):

```sh
cd vite-service
bun run dev      # vite dev server (esbuild pre-bundling, HMR)
bun run build    # vite build → ./dist (Rollup)
bun run preview  # vite preview, serves ./dist
bun run start    # vite preview --host --port 4173
```

Open http://localhost:5173. Same endpoints as bun-service:
`/`, `/api/hello`, `/api/health`, `/api/stats`.

## benchmark

Boots each of the 4 server variants (bun-dev, bun-prod, vite-dev,
vite-preview) one at a time on dedicated ports, waits for them to be
healthy, then:

- **Page load test** — fetches `/` once cold (captures any first-hit
  bundling/transpile cost) then N more times warm, reporting
  avg/min/max/p95 wall-clock time and response size.
- **Load test** (via [`autocannon`](https://github.com/mcollina/autocannon))
  — hammers `/`, `/api/hello` and `/api/stats` for a fixed duration with
  many concurrent connections, reporting requests/sec, latency and
  throughput.

Then it prints comparison tables and writes both JSON and Markdown
reports to `benchmark/results/`.

```sh
cd benchmark
bun run bench             # full run: 10s / 50 connections / 30 page-load samples
bun run bench:quick       # fast smoke test: 5s / 20 connections / 10 samples
bun run bench:bun         # only the two bun-service variants
bun run bench:vite        # only the two vite-service variants

# or customize directly:
bun run run.ts --duration 15 --connections 100 --samples 50
```

Or from the repo root:

```sh
bun run bench
bun run bench:quick
```

Results:

- `benchmark/results/latest.json` — raw structured data
- `benchmark/results/latest.md` — human-readable Markdown tables
- `benchmark/results/<timestamp>.json` — one snapshot per run

### How it works

- `benchmark/src/targets.ts` — declares the 4 targets (command, cwd,
  port, optional build step, health-check path).
- `benchmark/src/process-manager.ts` — runs the build (if any) via
  `Bun.spawn`, starts the server, polls the health endpoint until it's
  ready, kills the process afterwards.
- `benchmark/src/page-load.ts` — cold + warm timing via
  `performance.now()` around `fetch`.
- `benchmark/src/load-test.ts` — thin wrapper around `autocannon`.
- `benchmark/src/report.ts` — `console.table` printers + Markdown
  serializer.
- `benchmark/run.ts` — orchestrates all of the above, sequentially, so
  only one server is ever under load at a time (fair comparison, no
  CPU contention between targets).

## Notes on fairness

- Both services expose the exact same routes (`/`, `/api/hello`,
  `/api/health`, `/api/stats`) so the load test hits comparable work.
- Each service is benchmarked in both its "dev" mode (on-the-fly
  bundling: Bun's native HTML-import dev server vs. Vite's dev server)
  and its "production" mode (prebuilt static assets: `Bun.build` output
  served by `Bun.serve` vs. Vite `build` output served by
  `vite preview`), so you can see the cost of dev-mode transpilation
  separately from steady-state serving performance.
- Targets are benchmarked one at a time, never concurrently, to avoid
  one process stealing CPU from another and skewing results.

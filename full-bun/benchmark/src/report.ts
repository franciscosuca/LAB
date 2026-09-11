import type { PageLoadSummary } from "./page-load";
import type { LoadTestSummary } from "./load-test";

export interface TargetResult {
  name: string;
  group: "bun" | "vite";
  pageLoad: PageLoadSummary;
  endpoints: Record<string, LoadTestSummary>;
}

const n = (v: number, d = 1) => v.toFixed(d);

export function printPageLoadTable(results: TargetResult[]) {
  console.log("\n📄 Page load — GET / (ms, lower is better)\n");
  console.table(
    Object.fromEntries(
      results.map((r) => [
        r.name,
        {
          "cold warmup": `${n(r.pageLoad.warmupMs)} ms`,
          avg: `${n(r.pageLoad.avgMs)} ms`,
          min: `${n(r.pageLoad.minMs)} ms`,
          max: `${n(r.pageLoad.maxMs)} ms`,
          p95: `${n(r.pageLoad.p95Ms)} ms`,
          "size (bytes)": r.pageLoad.bytes,
        },
      ]),
    ),
  );
}

export function printLoadTestTables(
  results: TargetResult[],
  endpointLabels: string[],
) {
  for (const label of endpointLabels) {
    console.log(
      `\n🔥 Load test — ${label} (higher req/s & throughput is better, lower latency is better)\n`,
    );
    console.table(
      Object.fromEntries(
        results.map((r) => {
          const s = r.endpoints[label];
          return [
            r.name,
            {
              "req/s": n(s.requestsPerSecond, 0),
              "avg latency": `${n(s.latencyAvgMs)} ms`,
              "p99 latency": `${n(s.latencyP99Ms)} ms`,
              "throughput (Mbps)": n(s.throughputMbps, 2),
              errors: s.errors,
              timeouts: s.timeouts,
              "total requests": s.totalRequests,
            },
          ];
        }),
      ),
    );
  }
}

export function toMarkdown(
  results: TargetResult[],
  endpointLabels: string[],
): string {
  const lines: string[] = [];
  lines.push(`# Benchmark report`, "", `Generated: ${new Date().toISOString()}`, "");

  lines.push("## Page load — GET /", "");
  lines.push(
    "| Service | cold warmup | avg | min | max | p95 | size |",
    "|---|---|---|---|---|---|---|",
  );
  for (const r of results) {
    const p = r.pageLoad;
    lines.push(
      `| ${r.name} | ${n(p.warmupMs)} ms | ${n(p.avgMs)} ms | ${n(p.minMs)} ms | ${n(p.maxMs)} ms | ${n(p.p95Ms)} ms | ${p.bytes} B |`,
    );
  }
  lines.push("");

  for (const label of endpointLabels) {
    lines.push(`## Load test — ${label}`, "");
    lines.push(
      "| Service | req/s | avg latency | p99 latency | throughput (Mbps) | errors | timeouts |",
      "|---|---|---|---|---|---|---|",
    );
    for (const r of results) {
      const s = r.endpoints[label];
      lines.push(
        `| ${r.name} | ${n(s.requestsPerSecond, 0)} | ${n(s.latencyAvgMs)} ms | ${n(s.latencyP99Ms)} ms | ${n(s.throughputMbps, 2)} | ${s.errors} | ${s.timeouts} |`,
      );
    }
    lines.push("");
  }

  return lines.join("\n");
}

export interface PageLoadSummary {
  warmupMs: number; // first request, cold (bundling/transpile may happen here)
  avgMs: number;
  minMs: number;
  maxMs: number;
  p95Ms: number;
  bytes: number;
}

function percentile(sorted: number[], p: number): number {
  const idx = Math.min(
    sorted.length - 1,
    Math.floor((p / 100) * sorted.length),
  );
  return sorted[idx];
}

/**
 * Measures wall-clock time (fetch start -> body fully read) for repeated
 * requests to the same URL: a cold "warmup" request plus N warm samples.
 */
export async function measurePageLoad(
  url: string,
  samples = 30,
): Promise<PageLoadSummary> {
  const warmupStart = performance.now();
  const warmupRes = await fetch(url);
  await warmupRes.arrayBuffer();
  const warmupMs = performance.now() - warmupStart;

  const timings: number[] = [];
  let bytes = 0;

  for (let i = 0; i < samples; i++) {
    const start = performance.now();
    const res = await fetch(url);
    const buf = await res.arrayBuffer();
    timings.push(performance.now() - start);
    bytes = buf.byteLength;
  }

  const sorted = [...timings].sort((a, b) => a - b);

  return {
    warmupMs,
    avgMs: timings.reduce((a, b) => a + b, 0) / timings.length,
    minMs: sorted[0],
    maxMs: sorted[sorted.length - 1],
    p95Ms: percentile(sorted, 95),
    bytes,
  };
}

import autocannon, { type Result } from "autocannon";

export interface LoadTestOptions {
  duration: number; // seconds
  connections: number;
}

export interface LoadTestSummary {
  requestsPerSecond: number;
  latencyAvgMs: number;
  latencyP99Ms: number;
  throughputMbps: number;
  errors: number;
  timeouts: number;
  totalRequests: number;
}

export async function loadTest(
  url: string,
  { duration, connections }: LoadTestOptions,
): Promise<LoadTestSummary> {
  const result: Result = await autocannon({
    url,
    duration,
    connections,
    pipelining: 1,
  });

  return {
    requestsPerSecond: result.requests.average,
    latencyAvgMs: result.latency.average,
    latencyP99Ms: result.latency.p99,
    throughputMbps: (result.throughput.average * 8) / 1_000_000,
    errors: result.errors,
    timeouts: result.timeouts,
    totalRequests: result.requests.total,
  };
}

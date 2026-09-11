import { mkdir } from "node:fs/promises";
import { endpoints, targets } from "./src/targets";
import { runBuild, startServer, stopServer, waitUntilReady } from "./src/process-manager";
import { measurePageLoad } from "./src/page-load";
import { loadTest } from "./src/load-test";
import {
  printLoadTestTables,
  printPageLoadTable,
  toMarkdown,
  type TargetResult,
} from "./src/report";

function parseArgs() {
  const args = Bun.argv.slice(2);
  const get = (flag: string, fallback: string) => {
    const i = args.indexOf(flag);
    return i !== -1 ? args[i + 1] : fallback;
  };
  return {
    duration: Number(get("--duration", "10")),
    connections: Number(get("--connections", "50")),
    samples: Number(get("--samples", "30")),
    only: get("--only", ""), // "bun" | "vite" | ""
  };
}

async function main() {
  const { duration, connections, samples, only } = parseArgs();

  const selected = only
    ? targets.filter((t) => t.group === only)
    : targets;

  console.log(
    `Running benchmark: duration=${duration}s connections=${connections} samples=${samples}\n` +
      `Targets: ${selected.map((t) => t.name).join(", ")}\n`,
  );

  const results: TargetResult[] = [];

  for (const target of selected) {
    console.log(`\n=== ${target.name} ===`);
    await runBuild(target);

    console.log(`  ↳ starting server (${target.startCmd.join(" ")})...`);
    const proc = startServer(target);

    try {
      await waitUntilReady(`${target.url}${target.healthPath}`);
      console.log(`  ↳ ready at ${target.url}`);

      console.log(`  ↳ measuring page load (${samples} samples)...`);
      const pageLoad = await measurePageLoad(target.url + "/", samples);

      const endpointResults: TargetResult["endpoints"] = {};
      for (const ep of endpoints) {
        console.log(`  ↳ load testing ${ep.label}...`);
        endpointResults[ep.label] = await loadTest(target.url + ep.path, {
          duration,
          connections,
        });
      }

      results.push({
        name: target.name,
        group: target.group,
        pageLoad,
        endpoints: endpointResults,
      });
    } finally {
      console.log("  ↳ stopping server");
      await stopServer(proc);
    }
  }

  printPageLoadTable(results);
  printLoadTestTables(
    results,
    endpoints.map((e) => e.label),
  );

  const outDir = new URL("./results", import.meta.url).pathname;
  await mkdir(outDir, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");

  await Bun.write(
    `${outDir}/${stamp}.json`,
    JSON.stringify(results, null, 2),
  );
  await Bun.write(`${outDir}/latest.json`, JSON.stringify(results, null, 2));

  const md = toMarkdown(
    results,
    endpoints.map((e) => e.label),
  );
  await Bun.write(`${outDir}/latest.md`, md);

  console.log(`\n📝 Results saved to benchmark/results/${stamp}.json`);
  console.log(`📝 Latest results also at benchmark/results/latest.{json,md}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

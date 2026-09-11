/**
 * Production bundling with Bun's built-in bundler (Bun.build).
 * No webpack/esbuild/vite involved — just Bun 1.4.
 */
import { rm } from "node:fs/promises";

const outdir = new URL("./dist", import.meta.url).pathname;

await rm(outdir, { recursive: true, force: true });

const result = await Bun.build({
  entrypoints: [new URL("./src/index.html", import.meta.url).pathname],
  outdir,
  target: "browser",
  minify: true,
  sourcemap: "linked",
  splitting: true,
  naming: {
    entry: "[name].[ext]",
    chunk: "assets/[name]-[hash].[ext]",
    asset: "assets/[name]-[hash].[ext]",
  },
});

if (!result.success) {
  console.error("❌ Build failed");
  for (const log of result.logs) console.error(log);
  process.exit(1);
}

for (const artifact of result.outputs) {
  const size = (artifact.size / 1024).toFixed(1);
  console.log(`✓ ${artifact.path.replace(outdir, "dist")}  (${size} kB)`);
}

console.log(`\nBuilt ${result.outputs.length} file(s) with Bun.build → ./dist`);

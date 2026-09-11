import type { Target } from "./targets";

const REPO_ROOT = new URL("../../", import.meta.url).pathname;

export async function runBuild(target: Target) {
  if (!target.buildCmd) return;
  console.log(`  ↳ building (${target.buildCmd.join(" ")})...`);
  const proc = Bun.spawn({
    cmd: target.buildCmd,
    cwd: `${REPO_ROOT}${target.cwd}`,
    stdout: "pipe",
    stderr: "pipe",
  });
  const exitCode = await proc.exited;
  if (exitCode !== 0) {
    const stderr = await new Response(proc.stderr).text();
    throw new Error(`Build failed for ${target.name}:\n${stderr}`);
  }
}

export function startServer(target: Target) {
  return Bun.spawn({
    cmd: target.startCmd,
    cwd: `${REPO_ROOT}${target.cwd}`,
    env: { ...process.env, ...target.env },
    stdout: "pipe",
    stderr: "pipe",
  });
}

export async function waitUntilReady(
  url: string,
  timeoutMs = 15_000,
): Promise<void> {
  const start = Date.now();
  let lastError: unknown;

  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url);
      if (res.ok) return;
    } catch (err) {
      lastError = err;
    }
    await Bun.sleep(150);
  }

  throw new Error(
    `Server at ${url} did not become ready within ${timeoutMs}ms (${lastError})`,
  );
}

export async function stopServer(proc: ReturnType<typeof Bun.spawn>) {
  proc.kill();
  await proc.exited;
}

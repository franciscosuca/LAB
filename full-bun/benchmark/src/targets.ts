export interface Target {
  /** Human readable label used in reports */
  name: string;
  /** Working directory of the service (relative to repo root) */
  cwd: string;
  /** Optional command to build the production bundle before starting */
  buildCmd?: string[];
  /** Command used to start the server */
  startCmd: string[];
  /** Env vars merged with process.env when starting the server */
  env?: Record<string, string>;
  /** Base URL the server will be reachable at */
  url: string;
  /** Path used to detect "server is ready" (should return 2xx fast) */
  healthPath: string;
  /** What kind of bundler/dev-server this represents, for the report */
  group: "bun" | "vite";
}

export const targets: Target[] = [
  {
    name: "bun-service (dev, on-the-fly bundling)",
    cwd: "bun-service",
    startCmd: ["bun", "run", "server.ts"],
    env: { PORT: "3011" },
    url: "http://localhost:3011",
    healthPath: "/api/health",
    group: "bun",
  },
  {
    name: "bun-service (prod, Bun.build output)",
    cwd: "bun-service",
    buildCmd: ["bun", "run", "build.ts"],
    startCmd: ["bun", "run", "server.ts"],
    env: { PORT: "3012", NODE_ENV: "production" },
    url: "http://localhost:3012",
    healthPath: "/api/health",
    group: "bun",
  },
  {
    name: "vite-service (dev server)",
    cwd: "vite-service",
    startCmd: ["bun", "run", "vite", "--port", "5183", "--strictPort"],
    url: "http://localhost:5183",
    healthPath: "/api/health",
    group: "vite",
  },
  {
    name: "vite-service (preview, Vite build output)",
    cwd: "vite-service",
    buildCmd: ["bun", "run", "vite", "build"],
    startCmd: [
      "bun",
      "run",
      "vite",
      "preview",
      "--port",
      "4183",
      "--strictPort",
    ],
    url: "http://localhost:4183",
    healthPath: "/api/health",
    group: "vite",
  },
];

/** Endpoints hit during the load test, present on every target. */
export const endpoints = [
  { path: "/", label: "page (/)" },
  { path: "/api/hello", label: "api (/api/hello)" },
  { path: "/api/stats", label: "api-cpu (/api/stats)" },
];

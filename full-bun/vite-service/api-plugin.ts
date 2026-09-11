import type { Plugin } from "vite";

function json(data: unknown) {
  return JSON.stringify(data);
}

function stats() {
  let x = 0;
  for (let i = 0; i < 5000; i++) x += Math.sqrt(i);
  return x;
}

/**
 * Tiny API middleware so vite-service exposes the same
 * /api/hello, /api/health, /api/stats endpoints as bun-service,
 * for both `vite dev` and `vite preview`.
 */
export function apiPlugin(): Plugin {
  const handle = (req: any, res: any, next: any) => {
    const url = req.url?.split("?")[0];
    res.setHeader("content-type", "application/json; charset=utf-8");

    if (url === "/api/hello") {
      res.end(
        json({
          message: "hello from vite-service",
          runtime: "Vite dev/preview server",
          time: Date.now(),
        }),
      );
      return;
    }

    if (url === "/api/health") {
      res.end(json({ status: "ok", service: "vite-service" }));
      return;
    }

    if (url === "/api/stats") {
      res.end(json({ computed: stats(), service: "vite-service" }));
      return;
    }

    next();
  };

  return {
    name: "vite-service-api",
    configureServer(server) {
      server.middlewares.use(handle);
    },
    configurePreviewServer(server) {
      server.middlewares.use(handle);
    },
  };
}

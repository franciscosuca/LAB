/**
 * Bun-only backend + static/HTML serving, powered entirely by Bun.serve.
 *
 * - dev  : imports src/index.html directly. Bun bundles/transpiles
 *          TSX + CSS on the fly for every request (its built-in dev bundler).
 * - prod : serves the pre-built ./dist folder produced by `bun run build`
 *          (build.ts calls Bun.build, Bun's built-in production bundler).
 */

const isProd = Bun.env.NODE_ENV === "production";
const port = Number(Bun.env.PORT ?? 3001);

function hello() {
  return Response.json({
    message: "hello from bun-service",
    runtime: `Bun ${Bun.version}`,
    time: Date.now(),
  });
}

function health() {
  return Response.json({ status: "ok", service: "bun-service" });
}

// Simulate a bit of real work so RPS numbers reflect more than "return a string".
function stats() {
  let x = 0;
  for (let i = 0; i < 5000; i++) x += Math.sqrt(i);
  return Response.json({ computed: x, service: "bun-service" });
}

if (isProd) {
  const dist = new URL("./dist", import.meta.url).pathname;
  const indexHtml = await Bun.file(`${dist}/index.html`).text();

  Bun.serve({
    port,
    async fetch(req) {
      const url = new URL(req.url);

      if (url.pathname === "/api/hello") return hello();
      if (url.pathname === "/api/health") return health();
      if (url.pathname === "/api/stats") return stats();

      if (url.pathname === "/" || url.pathname === "/index.html") {
        return new Response(indexHtml, {
          headers: { "content-type": "text/html; charset=utf-8" },
        });
      }

      const file = Bun.file(`${dist}${url.pathname}`);
      if (await file.exists()) return new Response(file);

      return new Response("Not found", { status: 404 });
    },
  });

  console.log(`🚀 bun-service (production) → http://localhost:${port}`);
} else {
  // Native HTML import: Bun bundles src/app.tsx + src/style.css on the fly.
  const index = await import("./src/index.html");

  Bun.serve({
    port,
    routes: {
      "/": index.default,
      "/api/hello": { GET: hello },
      "/api/health": { GET: health },
      "/api/stats": { GET: stats },
    },
    development: true,
  });

  console.log(`🚀 bun-service (dev) → http://localhost:${port}`);
}

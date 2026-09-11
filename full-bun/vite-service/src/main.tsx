import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

type Hello = { message: string; runtime: string; time: number };

function App() {
  const [hello, setHello] = useState<Hello | null>(null);
  const [count, setCount] = useState(0);

  useEffect(() => {
    fetch("/api/hello")
      .then((r) => r.json())
      .then(setHello)
      .catch(() => setHello(null));
  }, []);

  return (
    <main>
      <h1>⚡ vite-service</h1>
      <p>
        Bundler/dev server is <code>Vite</code> (Rollup for build, esbuild for
        pre-bundling), API middleware also served through Vite.
      </p>

      <section>
        <h2>API round-trip</h2>
        <pre>{hello ? JSON.stringify(hello, null, 2) : "loading..."}</pre>
      </section>

      <section>
        <h2>Client-side state</h2>
        <button onClick={() => setCount((c) => c + 1)}>
          clicked {count} times
        </button>
      </section>
    </main>
  );
}

createRoot(document.getElementById("app")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

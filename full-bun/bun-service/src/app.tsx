import { render } from "preact";
import { useEffect, useState } from "preact/hooks";

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
      <h1>⚡ bun-service</h1>
      <p>
        Package manager, bundler (<code>Bun.build</code>) and runtime
        (<code>Bun.serve</code>) — all Bun 1.4, no other tools involved.
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

render(<App />, document.getElementById("app")!);

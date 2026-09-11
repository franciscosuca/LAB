"""Optional network impairment (packet loss / extra latency) via Linux `tc netem`.

This is what makes it possible to *see* one of QUIC's headline advantages
instead of just reading about it: HTTP/2 multiplexes streams over a single
TCP connection, so a single lost packet stalls *every* stream on that
connection until it's retransmitted (transport-level head-of-line blocking).
HTTP/3's streams are independent at the QUIC layer, so only the affected
stream stalls - the rest keep flowing. On a clean loopback connection with
~0% loss this difference mostly disappears, which is exactly why this module
exists: it deliberately injects loss/latency so the `concurrency` scenario
can make the effect visible.

Linux-only (shells out to `tc`, part of iproute2) and requires NET_ADMIN
(root/sudo, or `--cap-add=NET_ADMIN` in a container). On macOS/Windows, run
this project inside a Linux VM or container to use `--loss`/`--delay`.
"""
from __future__ import annotations

import contextlib
import platform
import shutil
import subprocess
from collections.abc import Iterator

__all__ = ["NetworkImpairmentError", "impair"]


class NetworkImpairmentError(RuntimeError):
    pass


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise NetworkImpairmentError(
            f"Command failed ({' '.join(cmd)}): {(result.stderr or result.stdout).strip()}"
        )


@contextlib.contextmanager
def impair(interface: str = "lo", loss_pct: float = 0.0, delay_ms: float = 0.0) -> Iterator[None]:
    """Temporarily apply `tc netem` loss/delay to `interface` for the `with` block.

    No-ops (and works on any OS) when both `loss_pct` and `delay_ms` are 0,
    which is the default - so this is always safe to wrap benchmark runs in.
    """
    if loss_pct <= 0 and delay_ms <= 0:
        yield
        return

    if platform.system() != "Linux":
        raise NetworkImpairmentError(
            "--loss/--delay require Linux (tc/netem). Run httpbench inside a Linux VM or "
            "container (e.g. `docker run --cap-add=NET_ADMIN ...`) - see README.md."
        )
    if shutil.which("tc") is None:
        raise NetworkImpairmentError("The `tc` command was not found. Install iproute2.")

    netem_args = []
    if delay_ms > 0:
        netem_args += ["delay", f"{delay_ms}ms"]
    if loss_pct > 0:
        netem_args += ["loss", f"{loss_pct}%"]

    _run(["tc", "qdisc", "add", "dev", interface, "root", "netem", *netem_args])
    try:
        yield
    finally:
        subprocess.run(["tc", "qdisc", "del", "dev", interface, "root"], capture_output=True, check=False)

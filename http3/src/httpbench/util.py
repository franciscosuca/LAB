"""Small stateless helpers shared across the CLI, clients, and reporting code."""
from __future__ import annotations

import re

__all__ = ["format_size", "parse_alt_svc_h3_port", "parse_size"]

_SIZE_UNITS = {
    "B": 1,
    "KB": 1_000,
    "MB": 1_000_000,
    "GB": 1_000_000_000,
    "KIB": 1024,
    "MIB": 1024**2,
    "GIB": 1024**3,
}
_SIZE_RE = re.compile(r"^\s*([\d.]+)\s*([A-Za-z]*)\s*$")


def parse_size(text: str) -> int:
    """Parse a human-friendly size like ``"1KB"``, ``"512"``, or ``"2MiB"`` into bytes."""
    match = _SIZE_RE.match(text)
    if not match:
        raise ValueError(f"Invalid size: {text!r}")
    number, unit = match.groups()
    unit = (unit or "B").upper()
    if unit not in _SIZE_UNITS:
        raise ValueError(f"Unknown size unit {unit!r} in {text!r} (try B, KB, MB, GB, KiB, MiB, GiB)")
    return int(float(number) * _SIZE_UNITS[unit])


def format_size(n: float) -> str:
    """Render a byte count as a short human-readable string (decimal units)."""
    value = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if abs(value) < 1000:
            return f"{value:.0f}{unit}" if unit == "B" else f"{value:.1f}{unit}"
        value /= 1000
    return f"{value:.1f}TB"


def parse_alt_svc_h3_port(header_value: str | None) -> int | None:
    """Extract the first HTTP/3 port advertised in an ``Alt-Svc`` header.

    Browsers use this exact header to discover that a server reachable over
    HTTP/2 also speaks HTTP/3 on some (usually identical) UDP port, e.g.::

        Alt-Svc: h3=":443"; ma=86400, h3-29=":443"

    Returns ``None`` if the header is absent or no ``h3*`` entry is found.
    """
    if not header_value:
        return None
    for entry in header_value.split(","):
        match = re.search(r'(h3[\w-]*)\s*=\s*":(\d+)"', entry.strip())
        if match:
            return int(match.group(2))
    return None

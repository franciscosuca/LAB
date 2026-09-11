"""Generate a throwaway local certificate authority + server certificate.

Both HTTP/2 (over TLS) and HTTP/3 (over QUIC, which mandates TLS 1.3) need a
certificate to run the demo server. `trustme` exists specifically for this
kind of local testing: it creates a private CA in memory and issues a leaf
certificate signed by it. Clients then trust that one CA (via `--ca-cert`)
instead of disabling certificate verification altogether.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import trustme

__all__ = ["CertPaths", "cert_paths", "generate_certs"]


@dataclass(frozen=True)
class CertPaths:
    ca_cert: Path
    server_cert: Path
    server_key: Path

    def exists(self) -> bool:
        return self.ca_cert.exists() and self.server_cert.exists() and self.server_key.exists()


def cert_paths(out_dir: Path) -> CertPaths:
    """Return the (conventional) file paths for a given cert directory, without touching disk."""
    return CertPaths(
        ca_cert=out_dir / "ca.pem",
        server_cert=out_dir / "server.crt",
        server_key=out_dir / "server.key",
    )


def generate_certs(out_dir: Path, hosts: list[str]) -> CertPaths:
    """Generate (overwriting) a local CA and a leaf certificate valid for `hosts`.

    :param out_dir: directory to write ``ca.pem``, ``server.crt``, ``server.key`` into.
    :param hosts: subject alternative names for the server cert, e.g. ``["localhost", "127.0.0.1"]``.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ca = trustme.CA()
    leaf = ca.issue_cert(*hosts)

    paths = cert_paths(out_dir)
    ca.cert_pem.write_to_path(str(paths.ca_cert), append=False)
    leaf.private_key_pem.write_to_path(str(paths.server_key), append=False)
    with paths.server_cert.open("w") as fh:
        for blob in leaf.cert_chain_pems:
            fh.write(blob.bytes().decode())

    return paths

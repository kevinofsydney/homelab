#!/usr/bin/env python3
"""Read-only, unauthenticated endpoint probes; never discover or modify hosts."""
import argparse
import json
import socket
import ssl


def tcp_probe(host, port, timeout):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"check": "tcp", "port": port, "status": "reachable"}
    except OSError as exc:
        return {"check": "tcp", "port": port, "status": "failed", "reason": type(exc).__name__}


def tls_probe(host, port, timeout, ca_file=None):
    try:
        context = ssl.create_default_context(cafile=ca_file)
        with socket.create_connection((host, port), timeout=timeout) as raw:
            with context.wrap_socket(raw, server_hostname=host):
                return {"check": "tls", "port": port, "status": "verified"}
    except (OSError, ValueError) as exc:
        return {"check": "tls", "port": port, "status": "failed", "reason": type(exc).__name__}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proxmox-host", required=True, help="intended address or hostname; no URL")
    parser.add_argument("--ca-file", help="Proxmox public CA PEM obtained over a trusted path")
    parser.add_argument("--qnap-host", help="confirmed NAS address; omitted means not tested")
    parser.add_argument("--timeout", type=float, default=3)
    args = parser.parse_args()
    if not 0 < args.timeout <= 30:
        parser.error("timeout must be greater than zero and at most 30 seconds")
    checks = {
        "proxmox": [tcp_probe(args.proxmox_host, port, args.timeout) for port in (22, 8006)],
        "qnap": [],
    }
    checks["proxmox"].append(tls_probe(args.proxmox_host, 8006, args.timeout, args.ca_file))
    if args.qnap_host:
        checks["qnap"].append(tcp_probe(args.qnap_host, 2049, args.timeout))
    print(json.dumps({"checks": checks, "qnap_tested": bool(args.qnap_host)}, indent=2))
    # Missing NAS inventory is an incomplete preflight, not a successful check.
    return 0 if args.qnap_host and all(
        check["status"] in ("reachable", "verified")
        for group in checks.values() for check in group
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())

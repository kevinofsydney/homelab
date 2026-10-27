#!/usr/bin/env python3
"""Open a trusted guest shell or interactive sign-in without copying credentials."""
import argparse
import ipaddress
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {
    "shell": None,
    "coder": "sudo -iu coder",
    "codex-login": "sudo -iu coder codex login --device-auth",
    "opencode-login": "sudo -iu coder opencode auth login",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", choices=COMMANDS, default="shell")
    parser.add_argument("--config", default=str(ROOT / "config/site.json"))
    args = parser.parse_args()
    try:
        site = json.loads(Path(args.config).read_text())
        observed = site["observed"]
        address = str(ipaddress.ip_address(observed["development_vm_address"]))
        known_hosts = Path(observed["ssh_known_hosts_file"])
        if not known_hosts.is_absolute() or not known_hosts.is_file():
            raise ValueError("set observed.ssh_known_hosts_file to a verified absolute known-hosts file")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Guest connection configuration incomplete: {exc}\n")
    destination = f"devops@[{address}]" if ":" in address else f"devops@{address}"
    command = ["ssh", "-t", "-o", "StrictHostKeyChecking=yes", "-o", f"UserKnownHostsFile={known_hosts}", "--", destination]
    if COMMANDS[args.action]:
        command.append(COMMANDS[args.action])
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Serve the Immich health snapshot on the Tailscale address. GET /status is the only route."""
import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
from pathlib import Path
import sys

STATUS_FILE = Path("/run/immich-status/status.json")
STALE_AFTER_SECONDS = 300
MAX_STATUS_BYTES = 256 * 1024
TAILSCALE_RANGE = ipaddress.ip_network("100.64.0.0/10")


def is_tailscale_address(value):
    try:
        return ipaddress.ip_address(value) in TAILSCALE_RANGE
    except ValueError:
        return False


def read_status(path=STATUS_FILE, now=None):
    """Return a snapshot, reporting overall "stale" so a dead collector cannot look healthy."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    try:
        if path.stat().st_size > MAX_STATUS_BYTES:
            return None
        status = json.loads(path.read_text(encoding="utf-8"))
        age = (now - datetime.datetime.fromisoformat(status["generated_at"])).total_seconds()
    except (OSError, ValueError, KeyError, TypeError):
        return None
    status["age_seconds"] = round(age)
    if age > STALE_AFTER_SECONDS:
        status["overall"] = "stale"
    return status


def make_handler(status_path):
    class StatusHandler(BaseHTTPRequestHandler):
        server_version = "immich-status"
        sys_version = ""
        timeout = 5

        def respond(self, code, payload):
            body = json.dumps(payload, separators=(",", ":")).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path != "/status":
                self.respond(404, {"error": "not_found"})
                return
            status = read_status(status_path)
            if status is None:
                self.respond(503, {"overall": "unavailable"})
            else:
                self.respond(200, status)

        def log_message(self, format, *args):
            pass

    return StatusHandler


def make_server(address, port, status_path=STATUS_FILE):
    return ThreadingHTTPServer((address, port), make_handler(status_path))


def main():
    address = os.environ.get("IMMICH_STATUS_BIND_IP", "")
    if not is_tailscale_address(address):
        sys.exit("IMMICH_STATUS_BIND_IP must be a Tailscale address")
    make_server(address, int(os.environ.get("IMMICH_STATUS_PORT", "2284"))).serve_forever()


if __name__ == "__main__":
    main()

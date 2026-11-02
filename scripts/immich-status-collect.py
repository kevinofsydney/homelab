#!/usr/bin/env python3
"""Write a sanitized Immich health snapshot for the unprivileged status server.

Runs as root from a timer on the Immich VM. Output contains only fixed keys, allow-listed
states and numbers, because an agent reads it: no logs, paths, NAS source or free text.
"""
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.error
import urllib.request

ENV_FILE = Path("/opt/homelab/compose/immich/.env")
API_KEY_FILE = Path("/etc/homelab/immich-status-api-key")
OUTPUT = Path("/run/immich-status/status.json")
API_PORT = 2283
LOW_SPACE_PERCENT = 90
# Friendly name to Compose service name.
CONTAINERS = {
    "server": "immich-server",
    "machine_learning": "immich-machine-learning",
    "cache": "redis",
    "database": "database",
}
REQUIRED_FOR_SERVICE = ("server", "database")
UNIT_STATES = {"active", "activating", "deactivating", "inactive", "failed", "reloading"}
CONTAINER_STATES = {"created", "running", "paused", "restarting", "removing", "exited", "dead"}
HEALTH_STATES = {"healthy", "unhealthy", "starting", "none"}
QUEUE_COUNTS = ("active", "waiting", "delayed", "failed", "paused")


def allowed(value, choices):
    return value if value in choices else "unknown"


def whole_number(value):
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def run(argv, timeout=15):
    """Return stdout, or None on failure. Never wait on a child stuck on a hung NAS."""
    try:
        process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    except OSError:
        return None
    try:
        stdout, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        return None
    return stdout if process.returncode == 0 else None


def fetch_json(path, base_url, api_key=None):
    request = urllib.request.Request(base_url + path, headers={"x-api-key": api_key} if api_key else {})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=10) as response:
            return json.load(response)
    except (OSError, ValueError, urllib.error.URLError):
        return None


def read_settings(path=ENV_FILE):
    """Read only the named keys, so the database password is never loaded."""
    wanted = {"IMMICH_BIND_IP", "IMMICH_NAS_ROOT", "IMMICH_NAS_SOURCE", "IMMICH_LOCAL_ROOT"}
    settings = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key in wanted:
            settings[key] = value.strip()
    return settings


def used_percent(path, runner):
    output = runner(["stat", "-f", "--format=%b %a", str(path)])
    try:
        total, available = (int(part) for part in output.split())
    except (AttributeError, ValueError):
        return None
    return round(100 * (total - available) / total) if total else None


def container_status(service, runner):
    ids = runner([
        "docker", "ps", "-aq",
        "--filter", "label=com.docker.compose.project=immich",
        "--filter", f"label=com.docker.compose.service={service}",
    ])
    if ids is None:
        return {"state": "unknown"}
    if not ids.strip():
        return {"state": "missing"}
    output = runner(["docker", "inspect", ids.split()[0]])
    try:
        record = json.loads(output)[0]
        state = record["State"]
    except (TypeError, ValueError, IndexError, KeyError):
        return {"state": "unknown"}
    health = state.get("Health") or {}
    return {
        "state": allowed(state.get("Status"), CONTAINER_STATES),
        "health": allowed(health.get("Status", "none"), HEALTH_STATES),
        "restart_count": whole_number(record.get("RestartCount")),
        "exit_code": whole_number(state.get("ExitCode")),
        "oom_killed": state.get("OOMKilled") is True,
    }


def nas_status(root, expected_source, runner):
    percent = used_percent(root, runner)
    record = runner(["findmnt", "--mountpoint", str(root), "--noheadings", "--raw", "--output", "SOURCE,FSTYPE"])
    parts = record.strip().splitlines()[-1].split() if record and record.strip() else []
    mounted = len(parts) == 2 and parts[1] in ("nfs", "nfs4")
    return {
        "mounted": mounted,
        "source_matches": mounted and parts[0] == expected_source,
        "responsive": percent is not None,
        "used_percent": percent,
    }


def version_text(version):
    if not isinstance(version, dict):
        return None
    numbers = [whole_number(version.get(part)) for part in ("major", "minor", "patch")]
    return ".".join(str(number) for number in numbers) if None not in numbers else None


def queue_status(base_url, api_key, fetcher):
    if not api_key:
        return "not_configured", None
    queues = fetcher("/api/queues", base_url, api_key)
    if not isinstance(queues, list):
        return "unavailable", None
    summary = {}
    for queue in queues:
        if not isinstance(queue, dict) or not re.fullmatch(r"[A-Za-z]{1,40}", str(queue.get("name"))):
            continue
        statistics = queue.get("statistics") if isinstance(queue.get("statistics"), dict) else {}
        counts = {count: whole_number(statistics.get(count)) for count in QUEUE_COUNTS}
        summary[queue["name"]] = {**counts, "is_paused": queue.get("isPaused") is True}
    return "ok", summary


def find_problems(status):
    problems = []
    if status["startup_service"] != "active":
        problems.append("startup_service_not_active")
    for name, container in status["containers"].items():
        if container["state"] != "running":
            problems.append(f"container_{name}_not_running")
        elif container.get("health") == "unhealthy":
            problems.append(f"container_{name}_unhealthy")
    nas = status["nas"]
    if not nas["mounted"]:
        problems.append("nas_not_mounted")
    elif not nas["source_matches"]:
        problems.append("nas_wrong_source")
    if not nas["responsive"]:
        problems.append("nas_unresponsive")
    if (nas["used_percent"] or 0) >= LOW_SPACE_PERCENT:
        problems.append("nas_low_space")
    if status["ssd"]["used_percent"] is None:
        problems.append("ssd_usage_unknown")
    elif status["ssd"]["used_percent"] >= LOW_SPACE_PERCENT:
        problems.append("ssd_low_space")
    if not status["api"]["reachable"]:
        problems.append("api_unreachable")
    return problems


def overall(status):
    down = not status["api"]["reachable"] or any(
        status["containers"][name]["state"] != "running" for name in REQUIRED_FOR_SERVICE)
    if down:
        return "down"
    return "degraded" if status["problems"] else "ok"


def collect(settings, api_key=None, runner=run, fetcher=fetch_json, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    base_url = f"http://{settings['IMMICH_BIND_IP']}:{API_PORT}"
    unit_state = runner(["systemctl", "show", "--property=ActiveState", "--value", "homelab-immich.service"])
    ping = fetcher("/api/server/ping", base_url)
    queues_state, queues = queue_status(base_url, api_key, fetcher)
    status = {
        "schema": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "startup_service": allowed((unit_state or "").strip(), UNIT_STATES),
        "containers": {name: container_status(service, runner) for name, service in CONTAINERS.items()},
        "nas": nas_status(settings["IMMICH_NAS_ROOT"], settings["IMMICH_NAS_SOURCE"], runner),
        "ssd": {"used_percent": used_percent(settings["IMMICH_LOCAL_ROOT"], runner)},
        "api": {
            "reachable": isinstance(ping, dict) and ping.get("res") == "pong",
            "version": version_text(fetcher("/api/server/version", base_url)),
        },
        "queues_state": queues_state,
        "queues": queues,
    }
    status["problems"] = find_problems(status)
    status["overall"] = overall(status)
    return status


def write_atomically(status, path=OUTPUT):
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".status-")
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(status, handle, separators=(",", ":"))
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def main():
    api_key = API_KEY_FILE.read_text(encoding="utf-8").strip() if API_KEY_FILE.exists() else None
    write_atomically(collect(read_settings(), api_key))


if __name__ == "__main__":
    main()

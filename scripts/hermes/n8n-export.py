#!/usr/bin/env python3
"""Export every n8n workflow visible over MCP to a root-only directory, outside Hermes's reach.

Runs as root from hermes-n8n-export.service. Reads N8N_MCP_TOKEN from the hermes
account's dotenv and the MCP URL from /etc/hermes-n8n-export.conf; never prints the token.
Writes <dir>/<UTC timestamp>/<workflow id>.json and prunes old runs.
"""
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import urllib.request

ENV_FILE = Path("/home/hermes/.hermes/.env")
CONF_FILE = Path("/etc/hermes-n8n-export.conf")
DEST = Path("/var/backups/n8n")
KEEP_RUNS = 30


class Client:
    def __init__(self, url, token):
        self.url, self.token, self.session, self.next_id = url, token, None, 1

    def call(self, method, params=None, notify=False):
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if not notify:
            body["id"] = self.next_id
            self.next_id += 1
        headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        request = urllib.request.Request(self.url, json.dumps(body).encode(), headers)
        with urllib.request.urlopen(request, timeout=120) as response:
            self.session = response.headers.get("Mcp-Session-Id") or self.session
            raw = response.read().decode()
        if notify or not raw.strip():
            return None
        if "data:" in raw:
            raw = [line[5:].strip() for line in raw.splitlines() if line.startswith("data:")][-1]
        reply = json.loads(raw)
        if "error" in reply:
            raise RuntimeError(f"{method}: {reply['error']}")
        return reply["result"]

    def tool(self, name, arguments):
        result = self.call("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            raise RuntimeError(f"{name} failed")
        text = "".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
        return json.loads(text)


def setting(text, key):
    match = re.search(rf"^{key}=(.+)$", text, re.M)
    if not match:
        sys.exit(f"{key} is not configured")
    return match.group(1).strip()


def workflow_list(data):
    if isinstance(data, list):
        return data
    for key in ("data", "workflows", "results"):
        if isinstance(data.get(key), list):
            return data[key]
    return []


def main():
    client = Client(setting(CONF_FILE.read_text(), "N8N_MCP_URL"), setting(ENV_FILE.read_text(), "N8N_MCP_TOKEN"))
    client.call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "homelab-n8n-export", "version": "1"}})
    client.call("notifications/initialized", notify=True)
    workflows = workflow_list(client.tool("search_workflows", {}))
    if not workflows:
        sys.exit("No workflows returned; nothing exported")
    run = DEST / time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    os.umask(0o077)
    run.mkdir(parents=True)
    for workflow in workflows:
        details = client.tool("get_workflow_details", {"workflowId": workflow["id"], "detailLevel": "full"})
        (run / f"{workflow['id']}.json").write_text(json.dumps(details, indent=2, sort_keys=True), encoding="utf-8")
    (run / "index.json").write_text(json.dumps([{"id": w["id"], "name": w.get("name")} for w in workflows], indent=2), encoding="utf-8")
    runs = sorted(p for p in DEST.iterdir() if p.is_dir())
    for old in runs[:-KEEP_RUNS]:
        shutil.rmtree(old)
    print(f"Exported {len(workflows)} workflows to {run}")


if __name__ == "__main__":
    main()

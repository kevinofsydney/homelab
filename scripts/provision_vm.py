#!/usr/bin/env python3
"""Conservative Proxmox clone workflow; plan by default, no external dependencies."""
import argparse
import json
import os
import sys
import time
import re
import ssl
from pathlib import Path
from urllib import parse, request, error

from preflight import load_site


class Proxmox:
    def __init__(self, url, token_id, secret, ca_file=None):
        self.base = url.rstrip("/") + "/api2/json"
        self.auth = f"PVEAPIToken={token_id}={secret}"
        context = ssl.create_default_context(cafile=ca_file)
        self.opener = request.build_opener(request.HTTPSHandler(context=context), NoRedirect())

    def call(self, method, path, params=None):
        payload = parse.urlencode(params).encode() if params and method in ("POST", "PUT") else None
        url = self.base + path
        if params and method == "GET":
            url += "?" + parse.urlencode(params)
        req = request.Request(url, data=payload, method=method, headers={"Authorization": self.auth})
        try:
            with self.opener.open(req, timeout=30) as response:
                return json.load(response)["data"]
        except error.HTTPError as exc:
            raise RuntimeError(f"Proxmox API {method} {path}: HTTP {exc.code}") from exc

    def task(self, node, upid):
        path = f"/nodes/{parse.quote(node)}/tasks/{parse.quote(upid, safe='')}/status"
        for _ in range(120):
            result = self.call("GET", path)
            if result["status"] == "stopped":
                if result.get("exitstatus") != "OK":
                    raise RuntimeError(f"Proxmox task failed: {result.get('exitstatus')}")
                return
            time.sleep(2)
        raise RuntimeError("Proxmox task timed out; inspect task before retrying")


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Proxmox API redirected; check api_url before sending credentials")


def disk_gib(config):
    disk = config.get("scsi0", "")
    match = re.search(r"(?:^|,)size=(\d+(?:\.\d+)?)([KMGTP])(?:,|$)", disk)
    if not match:
        raise RuntimeError("template has no scsi0 size; inspect template before cloning")
    scale = {"K": 1 / (1024 ** 2), "M": 1 / 1024, "G": 1, "T": 1024, "P": 1024 ** 2}
    return float(match[1]) * scale[match[2]]


def provision(api, site):
    p, vm = site["proxmox"], site["development_vm"]
    node = parse.quote(p["node"], safe="")
    vmid = p["vmid"]
    # This API checks the ID across the cluster, including VMs hidden by permissions.
    available = api.call("GET", "/cluster/nextid", {"vmid": vmid})
    if int(available) != vmid:
        raise RuntimeError(f"VMID {vmid} is unavailable; refusing to alter it")
    template = api.call("GET", f"/nodes/{node}/qemu/{p['template_vmid']}/config")
    if not template.get("template") or "cloudinit" not in template.get("ide2", ""):
        raise RuntimeError("source must be a template with an ide2 cloud-init drive")
    if template.get("cicustom") or template.get("hookscript"):
        raise RuntimeError("custom cloud-init or hookscript requires separate template review")
    current = disk_gib(template)
    if current > vm["disk_gb"]:
        raise RuntimeError("template disk exceeds requested disk; refusing shrink")
    key = Path(p["ssh_public_key_file"]).read_text(encoding="utf-8").strip()
    clone = api.call("POST", f"/nodes/{node}/qemu/{p['template_vmid']}/clone", {
        "newid": vmid, "name": p["vm_name"], "full": 1, "storage": p["storage"]
    })
    api.task(p["node"], clone)
    updated = api.call("POST", f"/nodes/{node}/qemu/{vmid}/config", {
        "cores": vm["cores"], "memory": vm["memory_mb"], "net0": f"virtio,bridge={p['bridge']},firewall=1",
        "ciuser": p["ciuser"], "sshkeys": parse.quote(key, safe=""), "ipconfig0": vm["ipconfig0"],
        "agent": "enabled=1", "onboot": 0, "ciupgrade": 0
    })
    if isinstance(updated, str):
        api.task(p["node"], updated)
    if current < vm["disk_gb"]:
        resized = api.call("PUT", f"/nodes/{node}/qemu/{vmid}/resize", {"disk": "scsi0", "size": f"{vm['disk_gb']}G"})
        if isinstance(resized, str):
            api.task(p["node"], resized)
    started = api.call("POST", f"/nodes/{node}/qemu/{vmid}/status/start")
    if isinstance(started, str):
        api.task(p["node"], started)
    print(f"VM {vmid} started. Check console, DHCP lease, SSH and cloud-init status.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/site.json")
    ap.add_argument("--apply", action="store_true", help="create and start the VM")
    ap.add_argument("--ca-file", default=os.getenv("PVE_CA_FILE"), help="trusted Proxmox CA PEM file")
    args = ap.parse_args()
    site = load_site(args.config)
    p, vm = site["proxmox"], site["development_vm"]
    print(f"Clone template {p['template_vmid']} to VM {p['vmid']} ({p['vm_name']}); set {vm['cores']} cores, {vm['memory_mb']} MiB, {vm['disk_gb']} GiB, bridge {p['bridge']}, DHCP; start VM")
    if not args.apply:
        print("PLAN ONLY. No API call or infrastructure change made.")
        return
    token_id, secret = os.getenv("PVE_TOKEN_ID"), os.getenv("PVE_TOKEN_SECRET")
    if not token_id or not secret:
        ap.error("PVE_TOKEN_ID and PVE_TOKEN_SECRET are required for --apply")
    api = Proxmox(p["api_url"], token_id, secret, args.ca_file)
    provision(api, site)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        sys.exit(f"ERROR: {exc}")

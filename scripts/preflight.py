#!/usr/bin/env python3
"""Read-only site configuration and operator-machine preflight."""
import argparse
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def load_site(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for section in ("proxmox", "development_vm", "qnap"):
        if not isinstance(data.get(section), dict):
            raise ValueError(f"missing {section} object")
    p, vm, nas = data["proxmox"], data["development_vm"], data["qnap"]
    for key in ("api_url", "node", "vm_name", "bridge", "storage", "ssh_public_key_file", "ciuser"):
        value = p.get(key)
        if not isinstance(value, str) or not value or "REPLACE" in value:
            raise ValueError(f"set proxmox.{key}")
    for key in ("server", "nfs_export", "mountpoint"):
        value = nas.get(key)
        if not isinstance(value, str) or not value or "REPLACE" in value:
            raise ValueError(f"set qnap.{key}")
    parsed = urlparse(p["api_url"])
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("proxmox.api_url must be an HTTPS origin without credentials")
    if not all(isinstance(p.get(k), int) and p[k] > 0 for k in ("vmid", "template_vmid")):
        raise ValueError("VMIDs must be positive integers")
    if p["vmid"] == p["template_vmid"]:
        raise ValueError("VMID and template VMID must differ")
    if p["ciuser"] != "devops":
        raise ValueError("first milestone requires proxmox.ciuser=devops to match Ansible")
    for key in ("node", "bridge", "storage", "vm_name"):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", p[key]):
            raise ValueError(f"invalid proxmox.{key}")
    if not all(isinstance(vm.get(k), int) and vm[k] > 0 for k in ("cores", "memory_mb", "disk_gb")):
        raise ValueError("development_vm cores, memory_mb and disk_gb must be positive integers")
    if vm.get("ipconfig0") != "ip=dhcp":
        raise ValueError("first milestone requires ipconfig0=ip=dhcp; reserve the lease on your router")
    key_path = Path(p["ssh_public_key_file"]).expanduser()
    if not key_path.is_absolute() or not key_path.is_file():
        raise ValueError("proxmox.ssh_public_key_file must point to an existing absolute public key")
    key = key_path.read_text(encoding="utf-8").strip()
    if not key.startswith(("ssh-ed25519 ", "ssh-rsa ", "ecdsa-sha2-")):
        raise ValueError("SSH public key file does not look like an OpenSSH public key")
    if not nas["mountpoint"].startswith("/mnt/"):
        raise ValueError("QNAP backup mountpoint must be under /mnt")
    if not nas["nfs_export"].startswith("/"):
        raise ValueError("qnap.nfs_export must be an absolute NFS export path")
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "config/site.json"))
    args = ap.parse_args()
    try:
        site = load_site(args.config)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        ap.exit(2, f"Preflight failed: {exc}\n")
    vm = site["development_vm"]
    print("PASS: site configuration and SSH public key")
    print(f"PLAN: development VM {site['proxmox']['vmid']} — {vm['cores']} vCPU, {vm['memory_mb']} MiB RAM, {vm['disk_gb']} GiB disk")
    print("MANUAL: verify BIOS virtualization, 32 GB RAM, SSD health/free capacity, Ethernet and UPS")
    print("MANUAL: verify QNAP free space, dedicated NFS export and account, existing Plex unaffected")
    print("MANUAL: verify Proxmox certificate, backup storage and restore path")
    if os.getenv("PVE_TOKEN_ID") or os.getenv("PVE_TOKEN_SECRET"):
        print("INFO: Proxmox token variables present (not printed)")


if __name__ == "__main__":
    main()

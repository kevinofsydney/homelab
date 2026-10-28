# Homelab topology, resources and addresses

This is a dated reference, not a live inventory. The diagram deliberately uses address placeholders: real addresses remain in ignored `config/site.json`. The local site-specific copy is `.local/homelab-resource-diagram.md`; regenerate and verify its values before using it. Quantities below are configured VM allocations or observed host hardware, not current utilization.

```mermaid
flowchart TB
    Users["Trusted devices: Framework and Titan<br/>LAN addresses: see site inventory"]
    Router["Home router<br/>LAN: router address in site inventory"]
    Tailnet["Tailscale private network"]
    subgraph Dell["Dell OptiPlex 7000 Micro • Proxmox pve1"]
        PVE["Proxmox host<br/>Management: PVE LAN address :8006<br/>6 physical cores / 12 threads<br/>32 GB installed RAM • 512 GB SSD"]
        subgraph Dev["Development VM • VM 100"]
            DevVM["LAN: dev VM address :22<br/>4 vCPU • 8 GiB RAM<br/>100 GiB virtual SSD"]
            DevTools["OpenCode • Codex CLI • Hermes<br/>Same VM address (SSH)<br/>Share dev VM CPU / RAM / disk"]
        end
        subgraph App["Home-services VM • VM 130"]
            AppVM["LAN: application VM address :22<br/>Tailscale: application VM address<br/>2 vCPU • 4 GiB RAM<br/>60 GiB virtual SSD"]
            Paper["Paperless webserver<br/>Tailscale address :8000<br/>Shares app VM CPU / RAM<br/>Local state on VM SSD; documents on QNAP"]
            DB["Paperless PostgreSQL<br/>Internal Docker DNS: db :5432<br/>Shares app VM CPU / RAM / SSD"]
            Broker["Paperless Valkey<br/>Internal Docker DNS: broker :6379<br/>Shares app VM CPU / RAM / SSD"]
            Kuma["Uptime Kuma<br/>Tailscale address :3001<br/>Shares app VM CPU / RAM<br/>Database and configuration on VM SSD"]
        end
    end
    subgraph NAS["QNAP TS-264"]
        QTS["QNAP management<br/>NAS LAN address :443<br/>CPU / RAM: not independently verified<br/>Volume capacity: see site inventory"]
        Plex["Existing Plex<br/>NAS LAN address :32400<br/>Shares QNAP CPU / RAM / storage"]
        Docs["Paperless NFS share<br/>NAS LAN address :2049 (NFSv4)<br/>Documents stored on QNAP volume"]
    end
    Future["Planned: Immich • website • media apps<br/>No service addresses or allocations yet"]
    Users --> Router
    Users --> Tailnet
    Users --> PVE
    Users --> DevVM
    Tailnet --> Paper
    Tailnet --> Kuma
    DevVM --> DevTools
    Paper --> DB
    Paper --> Broker
    Paper --> Docs
    Kuma -. "HTTP monitor when configured" .-> Paper
    Future -. "planned" .-> App
```

- **Not yet drawn (2026-10-28):** VM 101 `hermes-agent` (4 vCPU, 8 GiB, 80 GiB; Hermes, rootless Docker; public egress only) and the QNAP `proxmox-backups` share that receives backups of all three VMs. The Hermes tools shown on the development VM are a dormant install. See the [status handoff](../agents/handoffs/homelab-status-2026-10-28.md).
- Paperless, PostgreSQL, Valkey and Uptime Kuma have **no individual CPU or memory reservation or limit**. All share the home-services VM's 2 vCPUs and 4 GiB RAM with Ubuntu and Docker. Their disk data grows within the VM SSD allocation or the QNAP volume; there are no separate per-service disk quotas configured. Docker-internal DNS names are not LAN addresses and IPs can change.
- Development tools share their VM's 4 vCPUs, 8 GiB RAM and 100 GiB virtual disk. Their SSH access is through the VM; they do not have separate service IPs. Tailscale on that VM last reported `NeedsLogin`.
- VM vCPUs are virtual, not reserved physical cores. Virtual SSD sizes are not guarantees of free physical SSD capacity. The host's CPU, memory and physical SSD are shared across Proxmox and VMs.
- Both VMs were enabled for Proxmox autostart on 2026-10-27 (`onboot: 1`, `startup order=1` for the dev VM and `order=2,up=30` for home-services). A physical host reboot that day started VM 100 then VM 130 automatically, and the guest startup units brought Paperless and Uptime Kuma back without intervention. Guest services still have their own startup behavior, documented in their runbooks.
- The QNAP volume's capacity and free space were supplied by the owner in screenshots and may change. NAS CPU/RAM allocations have not been verified. Existing Plex storage remains untouched.
- The Kuma UI is deployed privately; its initial administrator and HTTP monitor are separate interactive setup steps. It cannot report the application VM's own outage while running on that VM. Planned applications have no verified allocations or addresses. Self-hosted n8n is outside current scope; VM backups to the QNAP are live (see [Proxmox backups](proxmox-backups.md)).

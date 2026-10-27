# Architecture and decisions

## First milestone

One Proxmox host, one Ubuntu 24.04 development VM and private SSH access. The VM starts at 4 vCPU, 8 GiB RAM and 100 GiB SSD. Proxmox and NAS management remain separate from the development VM. Tailscale is configured interactively after SSH is verified. QNAP backups and self-hosted n8n are outside current scope until the operator requests them. No public services are part of this milestone.

## Review of the proposed four-VM allocation

The brief's 10+4+8+4 GiB guest RAM allocation totals 26 GiB, leaving about 6 GiB for Proxmox and all overhead. That is tight for simultaneous Immich ingestion, Paperless OCR and coding jobs. The requested virtual disks total 270 GiB before images, database growth, snapshots and backups; 512 GB can fill quickly. Start with one 8 GiB VM. Add a separate application VM only after measuring host memory, CPU peaks and SSD free space. Limit concurrent photo processing/OCR. Store VM backups on QNAP, not the local SSD. Maintain at least 20% free SSD space as an operational target; trigger review before it falls below that.

## Storage

Databases, indexes and app configuration live on the Dell SSD. QNAP holds bulk originals and backups. NFS is selected for Linux guests with dedicated exports and per-service permissions. A single NAS remains a single failure domain: add an off-NAS encrypted copy of irreplaceable photos, documents and backups before treating this as durable. `docs/storage.md` describes mount gating and recovery.

## Isolation

The interactive development VM is for a trusted operator only. It is not the unattended worker. Future issue jobs run in disposable workers with no management or production route or credentials. A Proxmox token used from the operator's laptop for initial provisioning is never copied into the development VM. The home router may not offer VLAN isolation, so enforce LAN firewall controls before claiming the management zone is isolated; Tailscale ACLs alone are insufficient.

## Deferred components

Paperless is the first Compose stack. Immich, n8n, Audiobookshelf, ebook server, monitoring, Telegram/Hermes, the UFC agent ([rebuild handoff](../agents/handoffs/ufc-hermes-rebuild.md)) and Cloudflare Tunnel need separate release review and service-specific runbooks before activation. Paperless-AI remains optional. The public web app app is a distinct project and requires confirmed the accounting system export format, billing rules and public security testing. NextDNS and QNAP Plex stay as they are. BinaryLane is out of scope.

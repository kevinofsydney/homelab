# Network policy to implement after inspecting the router

No IP addresses or VLAN IDs are assumed. Record actual addresses in ignored `config/site.json` and a private network inventory.

| Source | Destination | Intent |
| --- | --- | --- |
| Trusted operator device | Proxmox and QNAP management | Permit management ports over trusted LAN/Tailscale path only |
| Trusted operator device | Development VM SSH | Permit key-based SSH |
| Development VM `coder` | GitHub and approved AI providers | Permit required outbound HTTPS/DNS only |
| Development VM | Proxmox/QNAP/router management | Deny |
| Paperless app VM | Dedicated QNAP Paperless export | Permit NFS only |
| Paperless app VM | Dedicated QNAP backup export | Permit NFS for reviewed backups |
| Trusted tailnet device | Paperless web port | Permit private app access |
| Public internet | Management, DB, private apps | Deny |

The TP-Link router may not support the required inter-zone rules. Verify its actual features before promising isolation. If it cannot enforce them, use Proxmox guest firewalls and host firewalls with tested allowlists, or a dedicated firewall/VLAN-capable device. Do not turn on a blanket Proxmox firewall before confirming console access and an escape path. Tailscale policy controls tailnet traffic; separate LAN restrictions are necessary.

The future public web app app is the only candidate for public ingress. Its hosting decision remains open. If hosted on the Dell, publish only its HTTPS app origin through a narrowly scoped tunnel, with the admin interface and database kept private. Do not publish until security, backup, permissions and billing export tests pass.

# Access and secrets

- Proxmox and QNAP administration: trusted devices only, MFA where supported, no port forwarding. Prefer a management network or host/router firewall that blocks development workers from management IPs.
- Proxmox API token: use a separate short-lived token for initial VM clone/config/start, scoped to the template, target VM and storage operations needed. Verify exact permissions against the installed Proxmox release. Keep `PVE_TOKEN_ID` and `PVE_TOKEN_SECRET` in the operator shell or secret manager; unset after use. Never place them in `site.json` or a VM.
- SSH: public key at cloud-init, no password or root login after Ansible. Confirm a second working session before applying SSH restrictions. Use a known host key and review any changes.
- Tailscale: join the dev VM interactively, then explicitly restrict SSH to trusted identities in tailnet policy. Review local LAN reachability separately. Do not advertise the management subnet from the dev VM.
- AI CLIs: run only as `coder`, a non-sudo account with no direct SSH login. `devops` is the SSH administration account; it can switch to `coder`, but agents cannot switch back. Sign in interactively through supported login. No copied browser cookies or session tokens. Treat the CLI's shell permission as full access to `coder`. Keep production credentials absent from that user.
- API spend: use provider spending limits, per-job budgets/timeouts and low-privilege keys; do not run unattended tasks on an unrestricted key.
- Paperless: bind only to the chosen Tailscale address. Keep DB/broker internal to Compose. Use a strong secret key and database password in `compose/paperless/.env` mode 0600. Sensitive documents stay local by default; cloud model processing requires explicit opt-in.
- Backups: restrict the dedicated QNAP share, periodically test restores, and keep one encrypted off-NAS copy. Backups may contain user or household data.

Production deployment, running-service upgrades, network/firewall changes, elevated installs and credential changes require explicit approval. See `agents/permissions.md`.

The [crawler and botnet policy](bot-protection.md) defines required controls and acceptance tests before public ingress: keep household services private, authenticate users at the edge, prevent origin bypass, limit abusive workload and test emergency restrictions. These are deployment requirements, not evidence that live protections are active.

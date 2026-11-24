# Self-hosted n8n (planned)

**Status: VM created and staged; n8n not started.** Live progress is in [Deployment evidence](#deployment-evidence). On 2026-11-24 the owner asked to move the cloud n8n workflows to the homelab, after the cloud plan's monthly execution cap became a limit. This README is the deployment plan and runbook. Every step marked **approval** changes running infrastructure, networks, credentials or backups and needs the owner's explicit go-ahead under [`AGENTS.md`](../../AGENTS.md). Nothing here has run yet.

## Design

| Concern | Decision |
| --- | --- |
| Placement | A dedicated VM (next unused ID) cloned from the Ubuntu 24.04 template with `scripts/clone-application-vm.sh`: **2 vCPU, 3 GiB RAM, 40 GiB disk**. Kept apart from Paperless and Immich because it holds Google, model-provider and Telegram credentials. Confirm free host memory first: VMs 100, 101 and 120 have 8 GiB each and VM 130 has 4 GiB. |
| Inbound | **No public ingress.** Nothing on the internet can reach the VM. Telegram updates arrive through the relay below, using outbound polling only. [Bot protection](../../docs/bot-protection.md) therefore does not apply. |
| Outbound | Proxmox VM firewall, same model as Hermes: public internet allowed, every private range and IPv6 rejected, with exceptions only for DNS to the router and NFS to the NAS ([`n8n.fw.example`](../../proxmox/firewall/n8n.fw.example)). Inbound is SSH from the operator device only. |
| Editor, API and MCP | Port 5678 is bound to loopback. It is reached through `tailscale serve` (HTTPS, tailnet only) or an SSH tunnel. Hermes reaches the MCP endpoint through one tailnet grant to this VM's HTTPS port, following the [Immich monitoring](../../docs/immich-monitoring.md) pattern. Turn on two-step login for the n8n owner account. |
| Telegram | `telegram-relay` long-polls Telegram and posts allowed updates (message and button press, owner user ID only) to a local n8n Webhook node with an `x-relay-secret` header. The router workflow's Telegram Trigger is replaced by that Webhook node and a step that unwraps the request body, so downstream nodes keep their expressions. Delivery is at-least-once. |
| Google sign-in | The owner's own Google Cloud OAuth client. Redirect URI is `https://<tailscale name>/rest/oauth2-credential/callback`, which is reachable only from the owner's tailnet devices. The client is set to **In production**, so refresh tokens do not expire after 7 days. |
| Container | Pinned image digest, all capabilities dropped, `no-new-privileges`, environment access from nodes blocked, shell and file nodes excluded, community packages off, 14-day execution pruning, health check, `restart: unless-stopped`. The relay reuses the same image read-only with a 128 MiB limit. |
| Data | SQLite on the VM's SSD (`/srv/n8n/data`). Load is about 4,000 executions a month, far below where n8n recommends PostgreSQL. |
| Secrets | The bot token and relay secret are files in `/opt/homelab/n8n/secrets` (UID 1000, mode 0400), passed as Compose secrets. The n8n encryption key is generated on first start in `/srv/n8n/data/config`. **The owner copies it to a password manager that day.** Service credentials are entered by the owner in the n8n UI only. |
| Backups | `backup-n8n.sh` runs nightly once its timer is enabled. It takes an online SQLite snapshot, runs n8n's workflow export and its encrypted-credential export, and writes checksums to the dedicated QNAP backup export. The encryption key is **never** copied there, so a reader of the share cannot decrypt credentials. The 3-day Proxmox VM backups remain a second layer. |
| Monitoring | Uptime Kuma checks `/healthz` over the tailnet. The health-sweep workflow also pings an external heartbeat service (outbound), so a full homelab outage still alerts the owner. |

### Resource estimate

n8n uses about 300–600 MiB at idle and peaks during transcript and analysis runs. The relay uses under 64 MiB. The Compose limits are 1.5 GiB and 128 MiB, inside a 3 GiB VM. The database should stay under 1 GiB with 14-day pruning.

## Steps

The agent prepares source changes as PRs. The owner runs or approves everything that touches live systems.

1. **Capacity and VM (approval).** Check free host memory and storage. Run `clone-application-vm.sh` in plan mode with `APP_VM_CORES=2 APP_VM_MEMORY_MIB=3072 APP_VM_DISK_GIB=40`, then with `--apply`. Record the VM ID, address and host key in ignored `config/site.json` and `.local/known_hosts`.
2. **Firewall (approval).** Fill `n8n.fw.example` from site inventory and install it as the VM's firewall file. From inside the guest, verify that the router, NAS (except 2049), Proxmox, other VMs, the Tailscale CGNAT range and IPv6 are unreachable, and that public HTTPS works. Repeat after a reboot.
3. **Release review.** The stack is pinned to stable 2.48.8. The cloud instance runs 2.49.5 on the beta track, so before importing production workflows, move to the first stable 2.49.x or later. Read its release notes and security advisories, pin its tag and digest together in `compose.yml` for both services, and check that the image still runs as UID 1000 and ships Node's `fetch`.
4. **Stage (approval).** Add the VM to ignored `hosts.yml` under `automation`, then run `ansible-playbook ansible/playbooks/stage-n8n.yml --check --diff`, then apply. This installs packages and files only.
5. **Tailscale and backup mount (approval).** The owner enrols the VM and tags it. Update tailnet policy: owner devices may reach the VM, and Hermes may reach its HTTPS port only. Enable `tailscale serve` to `http://127.0.0.1:5678`. Create the QNAP backup export for this VM's address and verify the mount with `check-mount.sh`.
6. **Configure.** The owner copies `.env.example` to `.env` (root, 0600) and fills it in. They create the secret files with `openssl rand -hex 32` for the relay secret, and use a **separate test bot's** token until cutover.
7. **Start (approval).** Run `deploy-n8n.sh` in plan mode, then `--apply`. Check that `docker compose ps` is healthy, that `curl -fsS http://127.0.0.1:5678/healthz` succeeds on the VM, and that port 5678 is closed from the LAN.
8. **Owner setup.** Create the owner account, turn on two-step login, and save the encryption key to the password manager. Then create the n8n API key and MCP access, and enter each service credential.
9. **Backup and restore test (approval).** Run `backup-n8n.sh --apply` once. Restore it into a throwaway VM or container using the saved key, and confirm workflows, credentials and data tables. Only then enable the backup timer with `systemctl enable --now n8n-backup.timer`.
10. **Migrate and test.** Import workflows and data tables, rebind credentials and IDs, and test against the test bot. The workflow-side changes are listed below.
11. **Cutover (approval).** Pick a week with no event. Unpublish the cloud schedules and router, re-copy rows that changed in the cloud data tables, and switch the relay to the production bot token. The relay clears the cloud webhook on start. Publish the workflows in dependency order and watch the first full cycle. Keep the cloud account as a fallback until its plan ends.
12. **Monitoring.** Add the Uptime Kuma monitor and the external heartbeat check. Test that both alert.

### Workflow-side changes (separate repository)

- Router: replace the Telegram Trigger with a Webhook node (POST, the `.env` path, header-auth credential for `x-relay-secret`), followed by a step that outputs the request body. The relay already filters senders, but keep the router's own owner check.
- Replace the single community Supadata node with an HTTP Request node, so community packages can stay disabled.
- Workflows that call n8n's own API or MCP use `http://localhost:5678` from inside the container. Execution links sent to Telegram use the Tailscale editor address.
- The health sweep pings the external heartbeat URL, which is stored as a credential, not in workflow code.

## Recovery and upgrades

- **Restore:** a fresh VM from steps 1–7, the latest `COMPLETE` backup, and the encryption key from the password manager. Stop n8n, gunzip `database.sqlite` into `/srv/n8n/data` (owner 1000), and write the key into `config`. Start n8n and check workflows, credentials and data tables before re-enabling schedules. If the key is lost, the database restores but every credential has to be entered again.
- **Upgrade:** back up first. Read the release notes for migrations, pin the new tag and digest for both services, apply, then check health and one representative workflow. Rolling back after a database migration needs the pre-upgrade backup, not only the old image.
- **Security updates:** follow n8n's GitHub security advisories. Patch critical issues promptly, even though the instance has no public ingress.

## Deployment evidence

Record dated evidence for each step here and in [`agents/context.md`](../../agents/context.md).

**2026-11-24 (owner authorized the migration and live changes):**

- **Step 1, done.** VM 140 `n8n` was created with `clone-application-vm.sh`, after the plan check passed (2 vCPU, 3072 MiB, 40 GiB, DHCP). The host had 12 GiB available before the clone. It reuses VM 120's operator keys. Autostart is on (`order=5,up=30`), and the VM is now in the 3-day backup job (retention unchanged).
- **Step 2, done.** The firewall from `n8n.fw.example` was installed as `140.fw` with site values. From inside the guest:
  - TCP to Proxmox 8006, home-services 22, NAS 443, router 80 and `100.100.100.100:53` was blocked
  - NAS 2049 was open
  - `api.telegram.org` and `sheets.googleapis.com` answered over HTTPS
  - IPv6 was blocked

  Not yet re-tested after a reboot.
- **Step 3, partly done.** The image is pinned to stable 2.48.8 by digest. On the VM, the image runs as UID 1000, Node v26 has `fetch`, and `n8n --version` reports 2.48.8. Moving to stable 2.49.x before import is still open.
- **Step 4, done without the backup mount.** The staging roles applied: `application_baseline`, `tailscale_client`, `docker_staged` and `n8n_staged` (`ok=36 changed=16 failed=0`). `qnap_backup_mount` was skipped because the NAS has no export for this VM yet. Docker was then enabled and started.
- **Step 6, partly done.** `.env` exists (root, 0600) with a generated webhook path. The relay secret was generated on the VM (UID 1000, 0400). Still to fill: the tailnet name, the owner's Telegram ID, the NAS backup source and the bot token.
- **Waiting on the owner:**
  - complete the Tailscale login started with `tailscale up --hostname=n8n`
  - create a QNAP NFS export for the backup share, restricted to this VM
  - provide the Telegram user ID and a test bot token

**Not yet verified:** firewall and service behaviour after a reboot, n8n start and owner setup, backups, restore, the relay end to end, and every later step.

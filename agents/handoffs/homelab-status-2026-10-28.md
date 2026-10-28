# Task: homelab status for the next agent

Updated: 2026-10-28
Status: ready for handoff. All work below is merged to `main`; nothing is in flight.
Branch or worktree: none. Work from a fresh worktree off `origin/main` (see "Working practices").
Base/current commit: verify with `git log -1 origin/main`
PR: none open from this session

## Where things stand (live-checked 2026-10-28)

| Machine | State | Docs |
| --- | --- | --- |
| Proxmox host `pve1` (Proxmox 9.2.2) | Key-only SSH; Proxmox firewall on with the host itself unfiltered; all three VMs autostart (order 100 → 130 → 101) | [security review](../../docs/security-review-2026-10-27.md), [dev VM isolation](../../docs/dev-vm-isolation-plan.md) |
| VM 100 `dev` (4 vCPU / 8 GiB / 100 GiB, Ubuntu 26.04.1) | Codex, OpenCode and Node under `coder`. Proxmox firewall blocks it from every private address; on Tailscale as `tag:dev` with no grants. Hermes CLI here is **dormant and must not be activated** (one bot token per process). Codex now uses `workspace-write`, verified in a live ephemeral session (the old sandbox failure's cause is still unknown, todo 13); `coder` can run package maintenance through `/usr/local/sbin/homelab-apt-maintenance`, and has DeepSeek Harness `dsh` installed by hand (todo 14); see [coder capabilities](../../docs/dev-vm-coder-capabilities.md) | [development bootstrap](../../docs/development-bootstrap.md) |
| VM 130 `home-services` (2 vCPU / 4 GiB / 60 GiB, Ubuntu 24.04.5) | Paperless (PostgreSQL, Valkey) and Uptime Kuma, private on Tailscale, healthy; Paperless start is gated on its QNAP NFS mount | [Paperless handoff](paperless-deployment.md), [Uptime Kuma](../../compose/uptime-kuma/README.md) |
| VM 101 `hermes-agent` (4 vCPU / 8 GiB / 80 GiB, Ubuntu 24.04.5) | Hermes v0.22.5 Telegram bot `the Hermes bot`, live 24/7: OpenRouter `deepseek/deepseek-v4.1-flash-1017` ($10/month key), Exa search, rootless Docker sandbox, all 58 n8n MCP tools, fine-grained GitHub token on all repos | [Hermes runbook](../../docs/hermes-runbook.md) (start here for Hermes) |
| QNAP | Shares `paperless` (NFS to VM 130 only) and `proxmox-backups` (NFS to the host only); QTS reachable with a valid certificate through `tailscale serve` on port 8443 | [QNAP access](../../docs/qnap-access.md) |
| Backups | Job `backup-every-3-days` (VMs 100, 101, 130; 02:30; keep 15 ≈ 45 days) to the QNAP; first run 14.4 GB; restore tested; failures alert the owner via `the alerts bot` | [Proxmox backups](../../docs/proxmox-backups.md) |

## Owner decisions in force

- Hermes has **open public egress** (private ranges blocked twice: Proxmox VM firewall plus an in-guest nftables guard), for web search.
- Hermes may use **every n8n MCP tool** on every workflow and data table, with ask-first rules in its `n8n-workflows` skill, which Hermes may edit itself. Hermes has passwordless sudo on VM 101 and runs commands there directly, with approval prompts off (deny list kept). Opening or merging a pull request needs the owner to reply "approve" (the `pr-gate` plugin). `/sysupgrade` in Telegram checks and applies VM package updates, and `/repo` switches the repository Hermes works on (clones into `~/workspaces`); its GitHub token expires 2026-11-27; see the [Hermes runbook](../../docs/hermes-runbook.md). 27 data tables named `RA | …` belong to a retired research agent and are kept as they are; `RA | secrets` is readable by Hermes.
- GitHub: a **fine-grained token on all repositories** (Contents and Pull requests, no Workflows) instead of a GitHub App. Branch protection is unavailable (free plan, private repos), so Hermes is able to push to `main`; the owner chose not to add deny rules for that.
- The owner kept the Hermes "Always" approval for inline scripts (`script execution via -e/-c`).
- Backups every 3 days, expiring after about 45 days, to the QNAP; plain `vzdump`, no Proxmox Backup Server.
- No references to the owner's former employer: its n8n workflows are archived; do not reintroduce its name.

## Remaining work

The canonical list is [open work](../todo.md). Highlights:

- **Action 3, `e1000e` NIC hang** on the host: the likeliest cause of a repeat of the 2026-10-27 outage. Needs approval and a host reboot.
- **Action 4, Paperless NAS-loss test.**
- **Action 12, MagicDNS on Titan:** the owner's DNS screenshot shows no extra `ts.net` split route; a Tailscale internal resolver query from home-services resolved the NAS name. Titan internal Tailscale DNS resolved the NAS name, but Windows `Resolve-DnsName -DnsOnly -NoHostsFile` returned NXDOMAIN. Check Windows DNS policy and Tailscale DNS preference; preserve the hosts-file entries until verified.
- **Action 7, dev VM upgrade leftovers:** obsolete conffiles from the 24.04 → 26.04 upgrade. `/etc/logrotate.d/cloud-init` duplicates `cloud-init-base`, so `logrotate.service` fails and the guest shows `degraded` (seen 2026-10-28; harmless). The earlier GRUB script leftover is already fixed.
- **Action 8, Hermes:** non-owner and group-add tests still pending.
- The owner reports the QNAP Recycle Bin on `proxmox-backups` is off; this has not been independently verified in QTS.
- Not started: Immich and media stacks, the custom UFC agent (only if the owner asks), an off-site copy, an Uptime Kuma heartbeat for "backup never ran".

## Working practices that matter here

- **Shared checkout.** Other agents work in `C:\Users\<user>\Documents\GitHub\homelab` at the same time. Leave it on `main`, and merge or delete branches you create; an agent once left unmerged work on a branch there for hours. Use `git worktree add <temp dir> -b <branch> origin/main` for every change and remove the worktree after merging. Never switch or reset the shared checkout.
- **PRs:** standing authorization to merge after CI (`validate`) passes on the exact head; see root `AGENTS.md`. Infrastructure changes still need explicit owner approval each time.
- **Access from the operator PC (Titan):** root SSH to Proxmox and `devops` SSH to VMs 100 and 130 use the operator key. VM 101 has no Ansible inventory on Titan; this session drove it from the host with `qm guest exec 101 …`, copying files in with `qm guest exec 101 --pass-stdin 1 -- dd of=<path>` (`pvesh … file-write --content "$(cat f)"` drops trailing newlines). Its playbooks in `ansible/playbooks/hermes-*.yml` describe the same changes.
- **Secrets:** never ask for or print them. The owner enters each one: `hermes-secret <name>` on VM 101 (`telegram`, `owner`, `openrouter`, `exa`, `n8n-mcp`, `github`), hidden-input prompts on the host for Proxmox notification secrets. Check secrets by length or by an API identity call only.
- **Browsers:** the Claude desktop built-in browser refuses invalid certificates. QTS works at the NAS's tailnet name on port 8443; the Proxmox UI (self-signed) needs the owner's own browser.
- **Tailscale policy edits:** an agent can load a change into the admin console editor, but the owner must click Save.
- **Windows quoting:** long `bash -c` strings nested through SSH and `qm guest exec` break easily; write a script file and copy it in instead.

## Coordination and approval

No approvals are outstanding from this session. The next infrastructure change (for example the NIC mitigation) needs its own explicit owner approval.

## Host read-only audit and temporary NIC test

On 2026-10-28 the host NVMe SMART overall result passed (critical warning 0, spare 100%, wear 2%, media/data errors 0, 35 C); lifetime counters included 67 unsafe shutdowns and 39 error-log entries, the newest an invalid-field command. BIOS reports 1.11.0 dated 03/08/2023. Approximately 21 GiB of 31 GiB RAM was available, no systemd units were failed, and VMs 100, 130 and 101 were all running with autostart enabled in orders 1, 2 and 3 respectively. The owner confirms there is no UPS. On 2026-10-28 the Dell BIOS `AcPwrRcvry/current_value` reported `On`, configuring startup on AC restoration; physical power-loss recovery and full CPU/RAM diagnostics remain untested.

A historical boot contained repeated `e1000e` hardware-unit-hang messages; none appeared on the current boot during inspection. A temporary test disabled TSO/GSO/GRO on `nic0` with a five-minute systemd rollback timer; new host SSH, firewall and VM checks, a 256 MiB read of an existing QNAP backup, and Paperless/Kuma checks succeeded. The original on/on/on settings were explicitly restored and the timer stopped. This brief test neither proves the mitigation nor survives reboot; no persistent NIC change was made. Plan persistent changes with a robust rollback and console recovery before rebooting.

The dev VM's remaining `python3.12-venv` rc entry is deliberately retained: its purge script deletes shared Python wheel paths which may be used by newer Python versions. Other stale package configuration was backed up and purged, and the duplicate cloud-init logrotate file was backed up and removed. Logrotate and the system are healthy.

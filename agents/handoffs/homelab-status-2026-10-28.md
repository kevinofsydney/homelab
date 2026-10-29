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
| VM 101 `hermes-agent` (4 vCPU / 8 GiB / 80 GiB, Ubuntu 26.04.1) | Hermes v0.22.5 Telegram bot (username in ignored `config/site.json` → `telegram.hermes_bot`), live 24/7: OpenRouter `deepseek/deepseek-v4.1-flash-1017` ($10/month key), Exa search, all 58 n8n MCP tools, fine-grained GitHub token on all repos (expires 2026-11-27). Runs commands directly on the VM as `hermes` with passwordless sudo and approval prompts off (deny list kept); rootless Docker remains for its own use. Telegram commands `/repo` and `/sysupgrade` are Hermes skills. Current repo: `<repo>` | [Hermes runbook](../../docs/hermes-runbook.md) (start here for Hermes) |
| QNAP | Shares `paperless` (NFS to VM 130 only) and `proxmox-backups` (NFS to the host only); QTS reachable with a valid certificate through `tailscale serve` on port 8443 | [QNAP access](../../docs/qnap-access.md) |
| Backups | Job `backup-every-3-days` (VMs 100, 101, 130; 02:30; keep 15 ≈ 45 days) to the QNAP; first run 14.4 GB; restore tested; failures alert the owner via the alerts bot | [Proxmox backups](../../docs/proxmox-backups.md) |

## Owner decisions in force

- Hermes has **open public egress** (private ranges blocked twice: Proxmox VM firewall plus an in-guest nftables guard), for web search.
- **Hermes is meant to be productive, not sandboxed.** The VM is the boundary: it cannot reach the home network (Proxmox firewall plus in-guest guard), it is backed up every 3 days, and its keys are capped or revocable. Inside it Hermes has passwordless sudo, approval prompts off, and manages its own packages (`vm-self-admin` skill). Release upgrades wait for the owner to take a snapshot. Do not reintroduce the Docker sandbox or approval prompts unless the owner asks.
- Hermes owns and edits its skills in `~/.hermes/skills`. The copies under `config/hermes/skills/` are seeds only (`force: false`), so the live skill may be newer.
- **Every pull request needs the owner's "approve"** in Telegram (the `pr-gate` plugin plus a memory rule). It is a workflow check, not a boundary.
- **Pushes to `main` are not blocked**: there is no branch protection on the free plan, and the deny list stops only force-pushes and deletes. The `/repo` skill tells Hermes to work on `hermes/<topic>` branches. On 2026-10-28 the owner chose to leave this as an instruction; a hard block would be a small addition to `pr-gate`.
- Telegram commands are Hermes skills, pinned at the top of the 60-command menu with `platforms.telegram.extra.command_menu.priority`. `/repo` switches the repository (one at a time, cloned into `~/workspaces`); `/sysupgrade` checks and applies package updates. Hermes reserves `/upgrade`. See the [Hermes runbook](../../docs/hermes-runbook.md).
- Hermes may use **every n8n MCP tool** on every workflow and data table, with ask-first rules in its `n8n-workflows` skill. 27 data tables named `RA | …` belong to a retired research agent and are kept as they are; `RA | secrets` is readable by Hermes.
- GitHub: a **fine-grained token on all repositories** (Contents and Pull requests, no Workflows) instead of a GitHub App. It expires 2026-11-27 (todo 15).
- Backups every 3 days, expiring after about 45 days, to the QNAP; plain `vzdump`, no Proxmox Backup Server.
- No references to the owner's former employer: its n8n workflows are archived; do not reintroduce its name.

## Remaining work

The canonical list is [open work](../todo.md). Highlights:

- **Action 3, `e1000e` NIC hang** on the host: the likeliest cause of a repeat of the 2026-10-27 outage. Needs approval and a host reboot.
- **Action 4, Paperless NAS-loss test.**
- **Action 12, MagicDNS on Titan:** the owner's DNS screenshot shows no extra `ts.net` split route; a Tailscale internal resolver query from home-services resolved the NAS name. Titan internal Tailscale DNS resolved the NAS name, but Windows `Resolve-DnsName -DnsOnly -NoHostsFile` returned NXDOMAIN. Titan accepts Tailscale DNS, and its NRPT points to Quad100; its direct Quad100 lookup fails while the same lookup succeeds on home-services. The live `ts.net` route also appears on home-services and is coordinator-supplied according to a Tailscale maintainer; do not assume it is an erroneous user-configured route. Root cause remains open; preserve the hosts-file entries until verified.
- **Action 15, Hermes's GitHub token expires 2026-11-27.** The owner creates a new token; run `hermes-secret github --replace` on VM 101, then restart the gateway.
- **Action 16, delete the Proxmox snapshot `pre-hermes-sudo-20261028`** on VM 101 once Hermes's self-administration has run cleanly for a few days (owner approval).
- **Action 17, owner-side Telegram checks** of the `/repo` buttons and `/sysupgrade`. Both were verified only through the menu API and the Hermes CLI.
- VM 101 was upgraded to Ubuntu 26.04.1 by Hermes on 2026-10-28 (`release-upgrade.service`, finished 08:21 UTC). Checked 2026-10-29: kernel 7.0.0-42, system `running`, no failed units, gateway, rootless Docker and the egress guard active, no pending updates.
- The owner reports the QNAP Recycle Bin on `proxmox-backups` is off; this has not been independently verified in QTS.
- Not started: Immich and media stacks, the custom UFC agent (only if the owner asks), an off-site copy, an Uptime Kuma heartbeat for "backup never ran".

## Working practices that matter here

- **Shared checkout.** Other agents work in `C:\Users\<user>\Documents\GitHub\homelab` at the same time. Leave it on `main`, and merge or delete branches you create; an agent once left unmerged work on a branch there for hours. Use `git worktree add <temp dir> -b <branch> origin/main` for every change and remove the worktree after merging. Never switch or reset the shared checkout.
- **PRs:** standing authorization to merge after CI (`validate`) passes on the exact head; see root `AGENTS.md`. Infrastructure changes still need explicit owner approval each time.
- **Access from the operator PC (Titan):** root SSH to Proxmox and `devops` SSH to VMs 100 and 130 use the operator key. VM 101 has no Ansible inventory on Titan; this session drove it from the host with `qm guest exec 101 …`, copying files in with `qm guest exec 101 --pass-stdin 1 -- dd of=<path>` (`pvesh … file-write --content "$(cat f)"` drops trailing newlines). Its playbooks in `ansible/playbooks/hermes-*.yml` describe the same changes. To run a script, pipe it in with `qm guest exec 101 --timeout N --pass-stdin 1 -- runuser -l hermes -c "bash -s" < script` and read `out-data` from the JSON. Set `XDG_RUNTIME_DIR=/run/user/$(id -u)` before `systemctl --user`. To test a skill or command without messaging the bot as the owner, run `hermes chat -q "/<command> <args>"` as `hermes`; it runs a real agent turn.
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

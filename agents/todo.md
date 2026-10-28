# Open work

Last updated: 2026-10-28. This is the actionable list for any agent picking up the project. It records what is left, why it matters, what evidence closes it and which approval is still missing. State, evidence and history live in [shared context](context.md); service plans live in [the roadmap](../docs/roadmap.md).

Rules for maintaining this file:

- Keep one row per action in the table and a matching detail section below it.
- Move an item to [Closed](#closed) with the commit, PR or observation that proves it, rather than deleting it.
- Never mark something done from a plan, a config file or an agent's own summary. Cite the command output, journal line or test that was actually run.
- Record the approval state honestly. Most items here change running infrastructure and require the owner's explicit approval; see [AGENTS.md](../AGENTS.md) and [permissions](permissions.md).

## Actions

| # | Action | Why it matters | Approval needed | Effort | Status |
| --- | --- | --- | --- | --- | --- |
| 2 | DHCP reservations for VM 100, VM 130 and the host | Autostart and the new Proxmox firewall rules both reference addresses; a shuffled lease silently breaks them | Yes — router change | 15 min | Owner reports reservations made; MACs recorded, router reservations not independently checked |
| 3 | Mitigate the `e1000e` NIC hang on the host | Root cause of the 2026-10-27 outage; recurs under VM load and presents as "the whole homelab vanished" | Yes — host driver/kernel change | ~30 min + reboot | Not started |
| 4 | Paperless NAS-loss and restore test | Last untested failure path in the application stack | Yes — briefly disturbs a running service | ~1 h | Not started |
| 6 | Hardware health, BIOS and UPS audit | Never performed, on a host with two unclean shutdowns | Read-only inspection; changes need approval | ~30 min at the machine | Not started |
| 7 | dev VM package leftovers after the 26.04 upgrade | Cosmetic; avoids confusing later audits | Guest change; low risk | 10 min | Logrotate fixed; one old venv package remains |
| 8 | Hermes Telegram gateway (owner-only) | The owner's chat interface to Hermes | Yes — bot token and a 24/7 service | ~45 min | Running; owner chat verified. Non-owner and group-add tests pending |
| 12 | Fix MagicDNS tailnet-wide (owner console action) | Tailnet device names return NXDOMAIN on Titan even from `tailscale debug resolve`, so `\\<nas>.<tailnet>.ts.net`-style names fail; the NAS access workaround is separate | Yes — owner deletes a split-DNS route in the Tailscale admin console | 5 min | Open; blocked on owner console |
| 13 | Root-cause the codex/bwrap sandbox failure on the dev VM | Original EPERM is no longer reproducible; workspace-write restored and tested, root cause unknown | No — guest-local diagnosis | ~1 h | Open; root cause unknown |

## Detail

### 2. DHCP reservations

Autostart ordering and the dev VM's firewall acceptance now depend on fixed addresses (`<lan-host>` host, `.232` dev, `.124` home-services). A lease change breaks inventory, Ansible and the Tailscale-bound services at the same time.

- Done when: each device holds a reservation in the router, MAC addresses are recorded in the ignored site inventory, and a host reboot shows unchanged addresses.
- 2026-10-27: the owner reported making the reservations. A Proxmox reboot later the same evening kept `.10`, `.124` and `.232`. The MACs (host `nic0`, VM 100 and VM 130 `net0`) are readable from `ip -br link` on the host and `qm config`; record them in the ignored inventory to close this. The QNAP address is still unconfirmed by identity.
- The firewall rules in `proxmox/firewall/` reference these addresses; review them in the same change. On 2026-10-28 the host and all three VM MAC addresses were read from Proxmox and recorded in ignored site inventory. Router reservations are still not independently checked.

### 3. `e1000e` NIC hang

`e1000e 0000:00:1f.6 nic0: Detected Hardware Unit Hang` on the Intel I219-LM preceded the 2026-10-27 host shutdown; an earlier boot is also marked `crash` in `last -x`.

- Evidence to keep: `journalctl -b -1 -p err`, `last -x reboot shutdown`, `ethtool -k nic0`.
- Candidate mitigations: disable the problematic offloads/EEE on `nic0`, or a kernel/firmware change. Choose one, record the rollback, and keep the change minimal.
- Done when: the mitigation survives a reboot and a defined soak period under VM load with no further unit-hang messages — or the owner accepts the risk explicitly.

### 4. Paperless NAS-loss and restore test

Paperless is healthy but has never seen its QNAP export disappear while running.

- Entry point: [Paperless runbook](../compose/paperless/README.md), [deployment handoff](handoffs/paperless-deployment.md).
- Done when: with the export unavailable the service fails closed and logs it (no silent empty document tree); on return, ingest and OCR work again; a restore from the step-1 backup is demonstrated.
- Do not weaken NFS root squashing or the 0700 modes to make the test pass.

### 6. Hardware health, BIOS and UPS audit

Still listed as pending in [shared context](context.md) since the first milestone.

- Done when: CPU/RAM/disk health, BIOS/firmware version and power-loss behaviour are recorded, and the absence or presence of a UPS is documented.

### 7. dev VM package leftovers

- 2026-10-28: verified that the obsolete `/etc/logrotate.d/cloud-init` was byte-identical to the current `cloud-init-base` file, moved it to `/root/obsolete-conffiles/cloud-init-logrotate-20261028`, checked `logrotate -d`, and restarted `logrotate.service`. `Result=success` and `systemctl is-system-running` returned `running`.
- Backed up removed-package configuration and purged `keyboxd`, `networkd-dispatcher`, `pollinate`, `python3.12-minimal` and `sosreport`; the empty stale upgrade marker was moved to `/root/obsolete-conffiles/`.
- `python3.12-venv` remains in `rc` state. Its purge script removes shared `/usr/lib/python-wheels` and `/var/lib/python-wheels`, while newer Python venv packages are installed. Do not purge without reviewing the shared-path effects; document a deliberate keep decision or prove cleanup safe.

### 8. Hermes Telegram gateway

Model (`deepseek/deepseek-v4.1-flash-1017` via OpenRouter, $10/month key limit) and Exa web search already work on VM 101; see the [sandbox plan](../docs/hermes-rootless-sandbox-plan.md).

- Telegram-side guard: disable **Allow Groups** for the bot in BotFather. The pinned gateway applies `TELEGRAM_ALLOWED_USERS` to groups too, and an offline audit accepted an owner callback from a group (see [credential setup](../docs/hermes-credential-setup.md)); keeping the bot out of groups removes that path.
- The owner revokes the old token, enters the new one with `hermes-secret telegram`; `TELEGRAM_ALLOWED_USERS` already holds the owner ID. Never set `GATEWAY_ALLOW_ALL_USERS`.
- Done when: the gateway runs as a supervised service that survives a restart; Telegram `getMe` matches the intended bot; the owner gets a reply in a private chat; a message from another account gets no reply and is logged as unauthorised; adding the bot to a group is refused.

### 13. codex sandbox failure on the dev VM

The previously observed EPERM is not currently reproducible, so its underlying cause is still unknown. On 2026-10-28, `/usr/bin/bwrap` was 0.11.1 and the AppArmor user-namespace restriction remained enabled. Both the PATH-selected Codex 0.165.0 and the pinned-prefix Codex 0.164.0 succeeded with `codex sandbox -- /bin/true`. With an explicit workspace-write policy, both allowed a write inside a disposable workspace and denied a write outside it.

Restored `sandbox_mode = "workspace-write"` while preserving `approval_policy = "on-request"`; the prior private configuration is `/home/coder/.codex/config.toml.pre-workspace-sandbox-20261028`. A real ephemeral Codex 0.165.0 session reported `workspace-write` and successfully ran `/bin/pwd`. The standalone `codex sandbox` command without an explicit policy remained read-only in testing; do not confuse it with an end-to-end workspace-write session. Follow up if EPERM recurs or its cause can be established; do not claim a root cause from the successful retest.

## Closed

Recorded here so a fresh agent does not redo them. Dates are the day the work was verified.

| Item | Evidence |
| --- | --- |
| DeepSeek Harness in the pinned installer | PR #63 pinned dsh 0.2.1-rc.2 and the top-level tarball SHA-512; isolated install and `dsh --version` succeeded. The updated guest installer matched the merged source SHA-256, and its read-only check matched installed versions and launchers. Installed contents and transitive dependencies are not independently hashed. |
| Hermes GitHub access | Fine-grained PAT on all repositories (owner decision; App judged overkill; branch protection unavailable on the free plan). In private scratch repo `hermes-sandbox-test`: Hermes cloned, committed, pushed a branch and opened a PR; force-push to `main` blocked by the deny rule; workflow-file push rejected by GitHub; no token in logs (2026-10-28). See the [sandbox plan](../docs/hermes-rootless-sandbox-plan.md) |
| VM backups and restore test | Job `backup-every-3-days` (VMs 100, 101, 130; every 3 days at 02:30; keep last 15) to NFS storage `qnap-backups` on a dedicated QNAP share; first run OK, 14.4 GB; VM 100 restored to VMID 900 with a new MAC and the link down, booted with its tools present, then destroyed (2026-10-28). Backup warnings and failures alert the owner on Telegram through `the alerts bot`; a forced failure was delivered. See [Proxmox backups](../docs/proxmox-backups.md) |
| QTS with a valid certificate | `tailscale serve --bg --https=8443 https+insecure://127.0.0.1:443` on the QNAP after enabling tailnet HTTPS certificates; Let's Encrypt certificate for the NAS's tailnet name, auto-renewed. See [QNAP access](../docs/qnap-access.md) |
| Hermes n8n MCP connection | 31 of 58 tools on all workflows; `n8n-workflows` skill (root-owned); Hermes read a workflow and ran a pinned test (execution 2214, success); nightly root-only JSON export of all 22 workflows, unreadable by `hermes` (2026-10-28). Importing an export back into n8n is untested. Details in the [sandbox plan](../docs/hermes-rootless-sandbox-plan.md) and [runbook](../docs/hermes-runbook.md) |
| Hermes sandbox access to its own SSH | Guest nftables table `inet hermes_egress` via `hermes-egress.service`: uid 1001 and its sandboxes rejected from private ranges except router DNS; sandbox reached the VM's own SSH before, blocked after; DNS and GitHub still work; survived a VM reboot (2026-10-28). Details in the [sandbox plan](../docs/hermes-rootless-sandbox-plan.md) |
| Hermes reboot recovery and runbook | `qm reboot 101` on 2026-10-28: new boot ID in 21 s, `hermes-gateway` active in 22 s with `NRestarts=0` and `Connected to Telegram`, rootless Docker and the pinned image present, VM firewall rules intact; the owner's next message was logged and answered 3 s later. Runbook: [docs/hermes-runbook.md](../docs/hermes-runbook.md) |
| Proxmox autostart for both guests | `qm set ... --onboot 1 --startup order=...`; host reboot started VM 100 then VM 130 via `pve-guests.service`; guest services recovered (commit `6e9d7ae`) |
| dev VM release upgrade to 26.04.1 LTS | `dpkg --audit` empty, 7.0.0-38 kernel, no pending upgrades; the interrupted run stopped at the upgrader's "remove obsolete packages" prompt |
| dev VM GRUB environment block | Two causes, both fixed on 2026-10-28. (1) The 24.04 SysV script `/etc/init.d/grub-common`, an obsolete conffile after the 26.04 upgrade, raced `grub2-common.service` at every boot; it was backed up to `/root/obsolete-conffiles/` and removed. (2) GRUB writes the block from the bootloader outside the ext4 journal, so a hard or host-level stop can tear it; `/usr/local/sbin/grubenv-ensure-valid` and a `grub2-common.service` drop-in now validate and recreate it ([RCA](../docs/dev-vm-grubenv-rca.md)). Consecutive reboots verified in both sessions; `Result=success` on 2026-10-28 |
| Proxmox SSH key-only | Root key login kept, passwords refused (commit `12dff12`) |
| dev VM management isolation | Proxmox firewall applied with the host unfiltered and VM 100 blocked from private addresses (commits `6c81c70`, `1b9744e`); survived an owner-requested host reboot with the full acceptance set passing again |
| dev VM Tailscale join | Tailnet policy gives tagged devices no grant; dev joined as `tag:dev`; over the tailnet it is blocked from home-services, the NAS and Titan while the owner still reaches it (PR #27) |
| Ubuntu unattended-upgrades on both guests | Installed and scheduled; Tailscale origins added through `Origins-Pattern`; update window retimed to 02:30/03:00 `Australia/Sydney` (commit `7f3c0a8`) |
| Tailscale automatic updates | Repo re-pointed to `resolute` on dev; drop-ins on both guests; `tailscaled` restart proven transparent on home-services |
| Obsolete packages after the release upgrade | `apt autoremove` on dev removed the autoremovable set; `apt-get -s autoremove` now reports 0 |

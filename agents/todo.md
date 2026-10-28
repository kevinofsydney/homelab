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
| 2 | DHCP reservations for VM 100, VM 130 and the host | Autostart and the new Proxmox firewall rules both reference addresses; a shuffled lease silently breaks them | Yes — router change | 15 min | Owner reports reservations made; MACs not yet in ignored inventory |
| 3 | Mitigate the `e1000e` NIC hang on the host | Root cause of the 2026-10-27 outage; recurs under VM load and presents as "the whole homelab vanished" | Yes — host driver/kernel change | ~30 min + reboot | Not started |
| 4 | Paperless NAS-loss and restore test | Last untested failure path in the application stack | Yes — briefly disturbs a running service | ~1 h | Not started |
| 6 | Hardware health, BIOS and UPS audit | Never performed, on a host with two unclean shutdowns | Read-only inspection; changes need approval | ~30 min at the machine | Not started |
| 7 | dev VM package leftovers after the 26.04 upgrade | Cosmetic; avoids confusing later audits | Guest change; low risk | 10 min | Not started |
| 8 | Hermes Telegram gateway (owner-only) | The owner's chat interface to Hermes | Yes — bot token and a 24/7 service | ~45 min | Running; owner chat verified. Non-owner and group-add tests pending |
| 12 | Fix MagicDNS tailnet-wide (owner console action) | Tailnet device names return NXDOMAIN on Titan even from `tailscale debug resolve`, so `\\<nas>.<tailnet>.ts.net`-style names fail; the NAS access workaround is separate | Yes — owner deletes a split-DNS route in the Tailscale admin console | 5 min | Open; blocked on owner console |
| 13 | Root-cause the codex/bwrap sandbox failure on the dev VM | `codex sandbox` fails with EPERM for every command, so codex currently runs unconfined as `coder`; fixing it would restore `workspace-write` | No — guest-local diagnosis | ~1 h | Open; worked around |
| 14 | Add DeepSeek Harness to the pinned CLI installer | A rebuilt dev VM must retain the manually installed `dsh` | No — repo change, `bash -n` and tests | 30 min | Source and guest check completed; deployment verification pending |

## Detail

### 2. DHCP reservations

Autostart ordering and the dev VM's firewall acceptance now depend on fixed addresses (`<lan-host>` host, `.232` dev, `.124` home-services). A lease change breaks inventory, Ansible and the Tailscale-bound services at the same time.

- Done when: each device holds a reservation in the router, MAC addresses are recorded in the ignored site inventory, and a host reboot shows unchanged addresses.
- 2026-10-27: the owner reported making the reservations. A Proxmox reboot later the same evening kept `.10`, `.124` and `.232`. The MACs (host `nic0`, VM 100 and VM 130 `net0`) are readable from `ip -br link` on the host and `qm config`; record them in the ignored inventory to close this. The QNAP address is still unconfirmed by identity.
- The firewall rules in `proxmox/firewall/` reference these addresses; review them in the same change.

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

- 2026-10-28: `/etc/logrotate.d/cloud-init` is an obsolete `cloud-init` conffile that duplicates `cloud-init-base`, so `logrotate.service` fails ("duplicate log entry for /var/log/cloud-init-output.log") and the guest reports `degraded`. Fix as with the GRUB leftover: back it up, remove it, confirm `logrotate` and `systemctl is-system-running`. Check `dpkg-query -W -f='${Conffiles}' <package>` for other `obsolete` entries.
- 7 `rc`-state package configs (`dpkg -l | awk '$1=="rc"'`) and the stale `/var/lib/ubuntu-release-upgrader/release-upgrade-available` marker.
- Done when: `dpkg -l` shows no `rc` entries that are not deliberately kept, and the marker is gone.

### 8. Hermes Telegram gateway

Model (`deepseek/deepseek-v4.1-flash-1017` via OpenRouter, $10/month key limit) and Exa web search already work on VM 101; see the [sandbox plan](../docs/hermes-rootless-sandbox-plan.md).

- Telegram-side guard: disable **Allow Groups** for the bot in BotFather. The pinned gateway applies `TELEGRAM_ALLOWED_USERS` to groups too, and an offline audit accepted an owner callback from a group (see [credential setup](../docs/hermes-credential-setup.md)); keeping the bot out of groups removes that path.
- The owner revokes the old token, enters the new one with `hermes-secret telegram`; `TELEGRAM_ALLOWED_USERS` already holds the owner ID. Never set `GATEWAY_ALLOW_ALL_USERS`.
- Done when: the gateway runs as a supervised service that survives a restart; Telegram `getMe` matches the intended bot; the owner gets a reply in a private chat; a message from another account gets no reply and is logged as unauthorised; adding the bot to a group is refused.

### 13. codex sandbox failure on the dev VM

`codex sandbox -- /bin/true` fails with `Error: Permission denied (os error 13)` for every command, so every model-generated shell command is refused. Ruled out: the AppArmor userns restriction (disabled temporarily, still failed), missing userns support (`unshare -Ur` succeeds when the restriction is off), seccomp on the account, and a broken bubblewrap (`bwrap --dev-bind / / -- <codex> --version` works). An AppArmor `userns` profile for the vendored binaries changed nothing and was removed.

- Workaround in place: `sandbox_mode = "danger-full-access"` and `approval_policy = "on-request"` in `/home/coder/.codex/config.toml`, so commands run unconfined as `coder`. See [the decision record](../docs/dev-vm-coder-capabilities.md).
- Next: capture the failing `bwrap` invocation (strace on `clone3`/`clone`/`execve`, or log the argv bwrap receives) and compare it with the working manual invocation.
- Done when: the cause is identified, `workspace-write` is restored, and one command is observed running under the sandbox.
- Not done from the workaround: the guest is currently running without codex's sandbox.

### 14. DeepSeek Harness in the pinned installer

- `dsh` 0.2.1-rc.2 is installed under `coder`. The installer and manifest now pin its top-level tarball SHA-512; an isolated install succeeded and the new read-only `--check` matched the live VM versions and launchers. The installer update still needs to be merged and installed on the guest. Transitive npm dependencies are not individually pinned by this checksum.
- Done when: the manifest pins `dsh` with a reviewed checksum, the installer installs it, `bash -n` and the tests pass, and a check run on the dev VM reports no change.

## Closed

Recorded here so a fresh agent does not redo them. Dates are the day the work was verified.

| Item | Evidence |
| --- | --- |
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

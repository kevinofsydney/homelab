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
| 2 | DHCP reservations for VM 100, VM 130 and the host | Autostart and the new Proxmox firewall rules both reference addresses; a shuffled lease silently breaks them | Yes — router change | 15 min | Owner confirms all three IP reservations listed; MAC matching not independently checked |
| 3 | Mitigate the `e1000e` NIC hang on the host | NIC hang preceded the 2026-10-27 outage and can make the host unreachable | Yes — host driver/kernel change | ~30 min + reboot | Temporary offload test passed; persistent mitigation and soak pending |
| 4 | Paperless NAS-loss and restore test | Last untested failure path in the application stack | Yes — briefly disturbs a running service | ~1 h | Not started |
| 6 | Hardware health, BIOS and UPS audit | Check hardware and power recovery | Read-only inspection; changes need approval | ~30 min at the machine | Disk and BIOS inspected; no UPS; CPU/RAM diagnostics and physical recovery untested |
| 12 | Fix MagicDNS tailnet-wide (owner console action) | Tailnet device names return NXDOMAIN on Titan even from `tailscale debug resolve`, so `\\<nas>.<tailnet>.ts.net`-style names fail; the NAS access workaround is separate | Owner-side client verification | 5 min | Tailscale internal lookup works on Titan; Windows DNS still fails |
| 13 | Root-cause the codex/bwrap sandbox failure on the dev VM | Original EPERM is no longer reproducible; workspace-write restored and tested, root cause unknown | No — guest-local diagnosis | ~1 h | Open; root cause unknown |
| 15 | Renew Hermes's GitHub token before 2026-11-27 | Hermes loses clone, push and PR access when the fine-grained token expires | Owner creates the token and enters it | 10 min | Not started |
| 16 | Delete VM 101 snapshot `pre-hermes-sudo-20261028` | It is the rollback point for the sudo change; a lingering snapshot grows and pins old disk state | Yes, owner decides when | 2 min | Keep until Hermes self-administration has run cleanly for a few days |
| 17 | Owner-side Telegram check of `/repo` and `/sysupgrade` | Both were verified through `getMyCommands` and `hermes chat -q`, not by tapping in Telegram | No | 5 min | Not started |

## Detail

### 2. DHCP reservations

Autostart ordering and the dev VM's firewall acceptance now depend on fixed addresses (`<lan-host>` host, `.232` dev, `.124` home-services). A lease change breaks inventory, Ansible and the Tailscale-bound services at the same time.

- Done when: each device holds a reservation in the router, MAC addresses are recorded in the ignored site inventory, and a host reboot shows unchanged addresses.
- 2026-10-27: the owner reported making the reservations. A Proxmox reboot later the same evening kept `.10`, `.124` and `.232`. The MACs (host `nic0`, VM 100 and VM 130 `net0`) are readable from `ip -br link` on the host and `qm config`; record them in the ignored inventory to close this. The QNAP address is still unconfirmed by identity.
- The firewall rules in `proxmox/firewall/` reference these addresses; review them in the same change. On 2026-10-28 the host and all three VM MAC addresses were read from Proxmox and recorded in ignored site inventory. The owner confirmed on 2026-10-28 that all three addresses are listed as router reservations. Matching the listed MAC addresses to the observed inventory has not been independently verified.

### 3. `e1000e` NIC hang

`e1000e 0000:00:1f.6 nic0: Detected Hardware Unit Hang` on the Intel I219-LM preceded the 2026-10-27 host shutdown; an earlier boot is also marked `crash` in `last -x`.

- Evidence to keep: `journalctl -b -1 -p err`, `last -x reboot shutdown`, `ethtool -k nic0`.
- Candidate mitigations: disable the problematic offloads/EEE on `nic0`, or a kernel/firmware change. Choose one, record the rollback, and keep the change minimal.
- Done when: the mitigation survives a reboot and a defined soak period under VM load with no further unit-hang messages — or the owner accepts the risk explicitly.
- 2026-10-28: temporarily disabled TSO, GSO and GRO on `nic0` under a five-minute automatic rollback timer. Fresh host SSH, Proxmox firewall and VM checks, a 256 MiB read from an existing QNAP backup, and Paperless/Kuma health checks succeeded. Restored the original on/on/on settings and stopped the timer. This short test does not establish that the hang is fixed; no persistent network change or reboot was performed. Current boot showed no hardware-unit-hang messages; an older boot did.

### 4. Paperless NAS-loss and restore test

Paperless is healthy but has never seen its QNAP export disappear while running.

- Entry point: [Paperless runbook](../compose/paperless/README.md), [deployment handoff](handoffs/paperless-deployment.md).
- Done when: with the export unavailable the service fails closed and logs it (no silent empty document tree); on return, ingest and OCR work again; a restore from the step-1 backup is demonstrated.
- Do not weaken NFS root squashing or the 0700 modes to make the test pass.

### 6. Hardware health, BIOS and UPS audit

Still listed as pending in [shared context](context.md) since the first milestone.

- Done when: CPU/RAM/disk health, BIOS/firmware version and power-loss behaviour are recorded, and the absence or presence of a UPS is documented.
- 2026-10-28: NVMe SMART overall PASSED; critical warning 0, spare 100%, wear 2%, media/data errors 0, temperature 35 C; 67 lifetime unsafe shutdowns and 39 error-log entries. The latest logged error was an invalid-field command, not proof of disk failure. Dell BIOS 1.11.0 dated 03/08/2023; 31 GiB RAM visible, about 21 GiB available; no failed systemd units. All three VMs have `onboot=1`. The owner confirmed there is no UPS. The read-only Dell firmware attribute `AcPwrRcvry/current_value` reported `On` (possible values `Off;On;Last`), so the BIOS is configured to power on after AC is restored; an actual power-loss recovery has not been tested. OS-level checks are not a full CPU/RAM diagnostic.

### 12. MagicDNS on Titan

- 2026-10-28: the owner supplied a DNS-console screenshot showing MagicDNS enabled, the tailnet domain routed to `100.100.100.100`, NextDNS as global resolver, and no additional `ts.net` split-DNS entry visible. The live `ts.net` route has not disappeared: both Titan and home-services report it in coordinator-provided configuration. A [Tailscale maintainer explains](https://github.com/tailscale/tailscale/issues/16558) this route is supplied by the coordination server for shared devices and Funnel. Its presence is not itself evidence of misconfiguration; do not remove it as a presumed fix.
- From home-services, `sudo tailscale dns query` resolved the NAS tailnet name successfully. `tailscale debug resolve` returned NXDOMAIN from the VM's system resolver, which is consistent with this guest having `CorpDNS: false` (it does not accept Tailscale DNS for its system resolver). This does not establish that Titan's DNS is fixed.
- On Titan, `tailscale dns query` resolved the NAS name to its expected tailnet IP, but `Resolve-DnsName -Name <NAS-tailnet-name> -DnsOnly -NoHostsFile` returned DNS name does not exist. The Titan session reports `CorpDNS: true`, MagicDNS enabled, and an effective NRPT `.` rule pointing to Quad100 IPv4/IPv6. Direct Quad100 and `Resolve-DnsName -DnsOnly -NoHostsFile` returned NXDOMAIN. On home-services, both the internal query and a direct Quad100 query returned the expected IP. Root cause is unknown; compare Titan resolver paths, software and network conditions without changing settings, and preserve the hosts-file workaround. Tailscale recommends `Resolve-DnsName` rather than `nslookup` on Windows because the latter bypasses Windows DNS policies.

### 13. codex sandbox failure on the dev VM

The previously observed EPERM is not currently reproducible, so its underlying cause is still unknown. On 2026-10-28, `/usr/bin/bwrap` was 0.11.1 and the AppArmor user-namespace restriction remained enabled. Both the PATH-selected Codex 0.165.0 and the pinned-prefix Codex 0.164.0 succeeded with `codex sandbox -- /bin/true`. With an explicit workspace-write policy, both allowed a write inside a disposable workspace and denied a write outside it.

Restored `sandbox_mode = "workspace-write"` while preserving `approval_policy = "on-request"`; the prior private configuration is `/home/coder/.codex/config.toml.pre-workspace-sandbox-20261028`. A real ephemeral Codex 0.165.0 session reported `workspace-write` and successfully ran `/bin/pwd`. The standalone `codex sandbox` command without an explicit policy remained read-only in testing; do not confuse it with an end-to-end workspace-write session. Follow up if EPERM recurs or its cause can be established; do not claim a root cause from the successful retest.

### 15. Hermes GitHub token

The fine-grained token (all repositories, Contents and Pull requests read/write, no Workflows) reports `github-authentication-token-expiration: 2026-11-27 02:42:03 UTC`.

- Create a replacement with the same scopes in GitHub. Then on VM 101 run `sudo -iu hermes hermes-secret github --replace`, restart the gateway, and check it with an API identity call (never print the token). Revoke the old token.
- Done when: `/repo` lists repositories with the new token and the old one is revoked.

### 16. VM 101 rollback snapshot

`qm listsnapshot 101` shows `pre-hermes-sudo-20261028`, taken before Hermes was given sudo and the Docker sandbox was dropped. Config backups on the VM: `~/.hermes/config.yaml.pre-sudo-20261028`, `.pre-sysupgrade-20261028` and `.pre-repo-20261028`.

- Done when: the owner agrees, `qm delsnapshot 101 pre-hermes-sudo-20261028` succeeds and the next backup run is OK.

### 17. Owner-side Telegram checks

- `/repo` with no argument should show 4 repository buttons plus "Other". Tapping one should clone or update that repository and report back. `/repo <repo>` was verified through `hermes chat -q`: it cloned the repository and wrote the memory line `Current repo: …`.
- `/sysupgrade` should report pending updates and wait for "apply". It has not been run yet.
- If the menu does not show them, reopen the chat. `getMyCommands` lists `/repo` first and `/sysupgrade` second.

## Closed

Recorded here so a fresh agent does not redo them. Dates are the day the work was verified.

| Item | Evidence |
| --- | --- |
| Hermes Telegram gateway access tests | Owner chat and reboot recovery previously verified; on 2026-10-28 the owner reported a second account received no reply and the gateway journal recorded unauthorized-user blocks. The owner also reported Telegram refused to add the bot to a test group; earlier Bot API `getMe` reported `can_join_groups: false`. |
| dev VM package leftovers | On 2026-10-28 the obsolete duplicate cloud-init logrotate conffile was backed up, logrotate succeeded, and `systemctl is-system-running` returned `running`. Five obsolete package configurations and the stale upgrade marker were removed after backup. `python3.12-venv` is deliberately retained in `rc` state because its purge script removes shared Python wheel paths potentially used by newer Python installations. |
| DeepSeek Harness in the pinned installer | PR #63 pinned dsh 0.2.1-rc.2 and the top-level tarball SHA-512; isolated install and `dsh --version` succeeded. The updated guest installer matched the merged source SHA-256, and its read-only check matched installed versions and launchers. Installed contents and transitive dependencies are not independently hashed. |
| Hermes GitHub access | Fine-grained PAT on all repositories (owner decision; App judged overkill; branch protection unavailable on the free plan). In private scratch repo `hermes-sandbox-test`: Hermes cloned, committed, pushed a branch and opened a PR; force-push to `main` blocked by the deny rule; workflow-file push rejected by GitHub; no token in logs (2026-10-28). See the [sandbox plan](../docs/hermes-rootless-sandbox-plan.md) |
| VM backups and restore test | Job `backup-every-3-days` (VMs 100, 101, 130; every 3 days at 02:30; keep last 15) to NFS storage `qnap-backups` on a dedicated QNAP share; first run OK, 14.4 GB; VM 100 restored to VMID 900 with a new MAC and the link down, booted with its tools present, then destroyed (2026-10-28). Backup warnings and failures alert the owner on Telegram through `the alerts bot`; a forced failure was delivered. See [Proxmox backups](../docs/proxmox-backups.md) |
| QTS with a valid certificate | `tailscale serve --bg --https=8443 https+insecure://127.0.0.1:443` on the QNAP after enabling tailnet HTTPS certificates; Let's Encrypt certificate for the NAS's tailnet name, auto-renewed. See [QNAP access](../docs/qnap-access.md) |
| Hermes n8n MCP connection | 31 of 58 tools on all workflows at first, then all 58 by owner decision; `n8n-workflows` skill (now owned and editable by Hermes); Hermes read a workflow and ran a pinned test (execution 2214, success); nightly root-only JSON export of all 22 workflows, unreadable by `hermes` (2026-10-28). Importing an export back into n8n is untested. Details in the [sandbox plan](../docs/hermes-rootless-sandbox-plan.md) and [runbook](../docs/hermes-runbook.md) |
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

# Open work

Last updated: 2026-10-27. This is the actionable list for any agent picking up the project. It records what is left, why it matters, what evidence closes it and which approval is still missing. State, evidence and history live in [shared context](context.md); service plans live in [the roadmap](../docs/roadmap.md).

Rules for maintaining this file:

- Keep one row per action in the table and a matching detail section below it.
- Move an item to [Closed](#closed) with the commit, PR or observation that proves it, rather than deleting it.
- Never mark something done from a plan, a config file or an agent's own summary. Cite the command output, journal line or test that was actually run.
- Record the approval state honestly. Most items here change running infrastructure and require the owner's explicit approval; see [AGENTS.md](../AGENTS.md) and [permissions](permissions.md).

## Actions

| # | Action | Why it matters | Approval needed | Effort | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | VM backups for 100 and 130, plus a restore test | Only unmitigated single point of failure left; the host has already taken two unclean shutdowns and has no validated backup | Yes — host storage and backup job | ~1 h | Not started |
| 2 | DHCP reservations for VM 100, VM 130 and the host | Autostart and the new Proxmox firewall rules both reference addresses; a shuffled lease silently breaks them | Yes — router change | 15 min | Not started |
| 3 | Mitigate the `e1000e` NIC hang on the host | Root cause of the 2026-10-27 outage; recurs under VM load and presents as "the whole homelab vanished" | Yes — host driver/kernel change | ~30 min + reboot | Not started |
| 4 | Paperless NAS-loss and restore test | Last untested failure path in the application stack | Yes — briefly disturbs a running service | ~1 h | Not started |
| 5 | dev VM Tailscale join, gated on a tailnet policy | Tunnel traffic bypasses the Proxmox firewall rules; joining without a policy silently re-opens the isolation work | Yes — guest and tailnet policy change | Policy first, then 10 min | Blocked on policy |
| 6 | Hardware health, BIOS and UPS audit | Never performed, on a host with two unclean shutdowns | Read-only inspection; changes need approval | ~30 min at the machine | Not started |

## Detail

### 1. VM backups and restore test

No validated backup exists for either guest. The 2026-10-27 incident (a release upgrade interrupted by an unclean host shutdown) would have been unrecoverable if the guest disk had been lost.

- Entry point: [disaster recovery](../docs/disaster-recovery.md), [storage](../docs/storage.md). QNAP backups were deferred by the owner, so a local target on the Dell SSD is an acceptable first step.
- Done when: a scheduled `vzdump` completes for VM 100 and VM 130; one VM restores to a **new** VM ID and boots with its services healthy; retention and the target's free-space guard are recorded; the result is in [context](context.md).
- Not done until restored: a completed backup job is not evidence that a restore works.

### 2. DHCP reservations

Autostart ordering and the dev VM's firewall acceptance now depend on fixed addresses (`<lan-host>` host, `.232` dev, `.124` home-services). A lease change breaks inventory, Ansible and the Tailscale-bound services at the same time.

- Done when: each device holds a reservation in the router, MAC addresses are recorded in the ignored site inventory, and a host reboot shows unchanged addresses.
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

### 5. dev VM Tailscale join

The client on `dev` is installed and logged out. The isolation work warns that tunnel traffic bypasses the Proxmox firewall rules, so a tailnet policy must land first.

- Done when: a tailnet policy restricts `dev` to the intended destinations, the client joins, and acceptance tests show the previous isolation still holds for tunnel traffic.
- Cosmetic extras in the same maintenance window: 7 `rc`-state package configs, the stale `/var/lib/ubuntu-release-upgrader/release-upgrade-available` marker.

### 6. Hardware health, BIOS and UPS audit

Still listed as pending in [shared context](context.md) since the first milestone.

- Done when: CPU/RAM/disk health, BIOS/firmware version and power-loss behaviour are recorded, and the absence or presence of a UPS is documented.

## Closed

Recorded here so a fresh agent does not redo them. Dates are the day the work was verified.

| Item | Evidence |
| --- | --- |
| Proxmox autostart for both guests | `qm set ... --onboot 1 --startup order=...`; host reboot started VM 100 then VM 130 via `pve-guests.service`; guest services recovered (commit `6e9d7ae`) |
| dev VM release upgrade to 26.04.1 LTS | `dpkg --audit` empty, 7.0.0-38 kernel, no pending upgrades; the interrupted run stopped at the upgrader's "remove obsolete packages" prompt |
| dev VM GRUB environment block | `grub-editenv` validates, `grub2-common.service` succeeds, guest reports `running` (commit `12dff12`) |
| Proxmox SSH key-only | Root key login kept, passwords refused (commit `12dff12`) |
| dev VM management isolation | Proxmox firewall applied with the host unfiltered and VM 100 blocked from private addresses (commits `6c81c70`, `1b9744e`) |
| Ubuntu unattended-upgrades on both guests | Installed and scheduled; Tailscale origins added through `Origins-Pattern`; update window retimed to 02:30/03:00 `Australia/Sydney` (commit `7f3c0a8`) |
| Tailscale automatic updates | Repo re-pointed to `resolute` on dev; drop-ins on both guests; `tailscaled` restart proven transparent on home-services |
| Obsolete packages after the release upgrade | `apt autoremove` on dev removed the autoremovable set; `apt-get -s autoremove` now reports 0 |

---
name: sysupgrade
description: Check this VM (hermes-agent, VM 101) for package updates and a new Ubuntu release, report them, and apply them after the owner confirms. Invoked by the owner's /sysupgrade command in Telegram (/upgrade is a reserved Hermes alias for /subscription).
---

# /sysupgrade

The owner typed `/sysupgrade`. Check first, report, then wait for the owner's answer before changing anything. Follow the `vm-self-admin` skill for how to run disruptive jobs.

## 1. Check (no changes)

- `sudo apt-get update -qq`, then `apt list --upgradable 2>/dev/null | tail -n +2` for pending packages. Count them and note any security updates (`-security` in the source) and anything that touches the kernel, `systemd`, `docker` or `python3`.
- `lsb_release -ds` for the current release, and `do-release-upgrade -c` for a new one (exit status 0 means one is available).
- `test -f /var/run/reboot-required` and `cat /var/run/reboot-required.pkgs` if it exists.

## 2. Report and ask

Send one short message:

- the number of package updates, with the notable ones named;
- whether a new Ubuntu release is available, and which;
- whether a reboot is already pending.

If there is nothing to do, say so and stop. Otherwise ask: **reply "apply" to install the package updates.** A release upgrade is never part of "apply": offer it separately and follow the release-upgrade steps in `vm-self-admin`, which wait for the owner to take a Proxmox snapshot.

## 3. Apply (only after the owner replies "apply")

1. Run the upgrade detached, because it can restart services you depend on:
   `sudo systemd-run --unit=hermes-upgrade --collect --setenv=DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::=--force-confold full-upgrade`
2. Watch it with `journalctl -u hermes-upgrade -f --no-pager` (or `systemctl status hermes-upgrade`) until it finishes.
3. Report what was upgraded and whether `/var/run/reboot-required` now exists. If a reboot is needed, ask before rebooting: you will be offline for about a minute.

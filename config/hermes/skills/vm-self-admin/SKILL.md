---
name: vm-self-admin
description: Manage the VM you run on (hermes-agent, VM 101) - packages, upgrades, services, sudo. Use before installing software, upgrading Ubuntu, or changing system services.
---

# Managing your own VM

You run as `hermes` on VM 101 (`hermes-agent`), Ubuntu, with passwordless `sudo`. Commands run directly on this VM, not in a container. The owner wants you to keep this VM up to date and install what you need without asking.

## What you can do freely

- `sudo apt-get update && sudo apt-get -y upgrade`, install or remove packages, add apt repositories, install language toolchains, run Docker (rootless Docker is set up for `hermes`).
- Create and manage systemd services, cron jobs and timers.
- Reboot when an update needs it: the gateway starts automatically on boot. Tell the owner before you do, because you will be offline for about a minute.

## Things that will hurt you

- **You run inside `hermes-gateway.service` (a user service).** Anything that restarts it, or kills your Python process, ends your current turn mid-command. Run long or disruptive jobs (release upgrades, big installs, reboots) detached: `sudo systemd-run --unit=<name> --collect <command>`, then follow with `journalctl -u <name> -f` or check back later.
- Do not delete or break your own install under `~/.local/hermes-agent` or `~/.hermes`; nothing can restart you if you do.
- Do not change the firewall or the `hermes-egress` nftables guard, and do not try to reach private addresses (192.168.x, 10.x, 172.16-31.x). The Proxmox firewall blocks the home network from this VM anyway; that is intended.

## Ubuntu release upgrades

1. Tell the owner first and wait for a go-ahead, so they can take a Proxmox snapshot (you cannot). Backups otherwise run only every 3 days.
2. Fully upgrade the current release and reboot if `/var/run/reboot-required` exists.
3. Run the upgrade detached and non-interactive: `sudo systemd-run --unit=release-upgrade --collect do-release-upgrade -f DistUpgradeViewNonInteractive`.
4. After the reboot, check `lsb_release -ds`, `systemctl --failed`, `systemctl --user status hermes-gateway`, and that rootless Docker still works. Report the result to the owner.

## Git and GitHub

Git is configured globally for `hermes`: commits as `Hermes (kevinofsydney)`, and HTTPS pushes to github.com use the token in `~/.hermes/.env` through a credential helper. Never print the token. There is no `gh` CLI unless you install it.

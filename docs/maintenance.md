# Controlled maintenance

Initial deployment and maintenance are separate. Do not turn an issue label, Telegram request or image release into an automatic production update.

For a Paperless update:

1. Record running image digests, Compose config, health and free space. Read upstream release notes and migration warnings.
2. Run `scripts/deploy-paperless.sh` without `--apply` to validate mounts and Compose. Take a Proxmox VM backup and run `scripts/backup-paperless.sh --apply` after approving its brief downtime.
3. Save the old `.env` securely off Git. Change only reviewed image digests in `.env`. Run `scripts/deploy-paperless.sh --apply` after explicit production approval.
4. Check login, document retrieval, OCR queue, logs, storage paths and backup task. Record exact old/new digests.
5. If the new version fails before schema migration, restore the old digests and restart. If the database schema changed, restore the matching SQL/media/data backup in an isolated VM first, then follow the tested recovery procedure; do not blindly downgrade a migrated database.

For the development VM, use versioned CLI installs and preserve previous local package versions until a test run passes. Proxmox and network changes require their own reviewed change plan and a current host backup. Updates may require manual intervention; no script promises a universal rollback.

## Automatic package updates

Both guests use Ubuntu's shipped `unattended-upgrades`, driven by `apt-daily.timer` (index refresh) and `apt-daily-upgrade.timer` (install), with `/etc/apt/apt.conf.d/20auto-upgrades` enabling both. Drop-ins under `/etc/systemd/system/*.timer.d/` retime them to 02:30 and 03:00 `Australia/Sydney`; the guests keep `Etc/UTC` clocks and systemd resolves the timezone name, so the local hour holds across daylight saving.

Origins that are installed automatically:

- Ubuntu release, security and ESM pockets — the package default.
- Tailscale, through `/etc/apt/apt.conf.d/51unattended-upgrades-tailscale`: `o=Tailscale,a=resolute` on the development VM, `o=Tailscale,a=noble` on the application VM.
- **Docker is deliberately excluded.** Engine updates stay a reviewed, manual action on a host running stateful containers.

A `tailscaled` restart during an update is transparent in practice: it was tested on the application VM and the private address, `:8000`/`:3001` bindings, both endpoint responses and all containers were unchanged.

Automatic reboot stays off, so a kernel update leaves `/var/run/reboot-required` for the operator to act on.

Use `Unattended-Upgrade::Origins-Pattern` for additions, never `Allowed-Origins` with `o=…,a=…` entries: the legacy parser expects `Origin:Suite` and crashes the whole updater, silently stopping every automatic update.

Check it without changing anything:

```bash
systemctl list-timers 'apt-daily*'
sudo tail -n 20 /var/log/unattended-upgrades/unattended-upgrades.log
sudo unattended-upgrade --dry-run --debug | grep -i 'allowed origins'
cat /var/run/reboot-required /var/run/reboot-required.pkgs 2>/dev/null
```

Roll back a bad Tailscale release with `sudo apt-get install tailscale=<previous version>` — the upstream repository keeps its history.

This covers guest OS packages only. It does not update Paperless, n8n or any other pinned container image — those follow the application procedure above, which performs the digest review, Compose validation and restore checks that a package upgrade cannot.

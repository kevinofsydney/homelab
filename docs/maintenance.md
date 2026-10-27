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

Both guests use Ubuntu's shipped `unattended-upgrades`, enabled through `apt-daily.timer`, `apt-daily-upgrade.timer` and `/etc/apt/apt.conf.d/20auto-upgrades`. It installs from the release and security pockets only, so third-party repositories such as Docker and Tailscale are never upgraded automatically, and automatic reboot stays off: a kernel update leaves `/var/run/reboot-required` for the operator to act on.

Check it without changing anything:

```bash
systemctl list-timers 'apt-daily*'
sudo tail -n 20 /var/log/unattended-upgrades/unattended-upgrades.log
sudo unattended-upgrade --dry-run
cat /var/run/reboot-required /var/run/reboot-required.pkgs 2>/dev/null
```

This covers guest OS packages only. It does not update Paperless, n8n or any other pinned container image — those follow the application procedure above, which performs the digest review, Compose validation and restore checks that a package upgrade cannot.

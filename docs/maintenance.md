# Controlled maintenance

Initial deployment and maintenance are separate. Do not turn an issue label, Telegram request or image release into an automatic production update.

For a Paperless update:

1. Record running image digests, Compose config, health and free space. Read upstream release notes and migration warnings.
2. Run `scripts/deploy-paperless.sh` without `--apply` to validate mounts and Compose. Take a Proxmox VM backup and run `scripts/backup-paperless.sh --apply` after approving its brief downtime.
3. Save the old `.env` securely off Git. Change only reviewed image digests in `.env`. Run `scripts/deploy-paperless.sh --apply` after explicit production approval.
4. Check login, document retrieval, OCR queue, logs, storage paths and backup task. Record exact old/new digests.
5. If the new version fails before schema migration, restore the old digests and restart. If the database schema changed, restore the matching SQL/media/data backup in an isolated VM first, then follow the tested recovery procedure; do not blindly downgrade a migrated database.

For the development VM, use versioned CLI installs and preserve previous local package versions until a test run passes. Proxmox and network changes require their own reviewed change plan and a current host backup. Updates may require manual intervention; no script promises a universal rollback.

# Restore exercises

The live VM backup job, its evidence and the restore commands are in [Proxmox backups](proxmox-backups.md). A VM 100 restore was exercised on 2026-10-28.

## VM

1. Confirm the Proxmox backup job completed and its artifact exists on the dedicated QNAP share.
2. Restore the development VM to a temporary VMID on an isolated network, with no production credentials.
3. Boot, check cloud-init/SSH, verify Git and CLI binaries, and record elapsed time.
4. Remove the temporary VM only after explicit operator review.

## Paperless

1. Confirm `COMPLETE`, `database.sql.gz`, `media/`, `data/` and `SHA256SUMS` exist in a backup set. Verify the checksum.
2. In an isolated test VM, use the exact reviewed Paperless/PostgreSQL image digests and an empty local PostgreSQL directory.
3. Restore the SQL dump with `psql`, media to a dedicated test NAS path and `data/` to local SSD. Do not overwrite live data.
4. Start the test stack, log in, open random documents, confirm search and export, then document the result.

`scripts/backup-paperless.sh` stops the webserver while dumping the DB and copying media. The backup is unusable until a restore test proves it. Retain configuration and secrets separately in a secure secret store. Confirm retention and off-NAS encrypted copies before production use.

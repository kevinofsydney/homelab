# Host configuration backup

A systemd timer on the [VM backup job's schedule](../../docs/proxmox-backups.md) archives the Proxmox host configuration to `/mnt/pve/qnap-backups/host-config/`, keeping the newest 15. It runs separately from the VM job, so neither can block the other.

Each archive holds `/etc` including `/etc/pve`, `/root`, `/usr/local`, cron spools, a consistent copy of the cluster database (`config.db`), the package selections and `pveversion -v`. It is written as `.partial`, its contents are checked, and only then does it get its final name and older archives get pruned. The script refuses to run unless the target is a mounted NFS export, and never creates the mount point.

**The archives are sensitive and unencrypted.** They contain SSH host keys, the Proxmox CA and stored tokens. They are root-only (mode 0600 in a 0700 directory), on a share exported only to the Proxmox host.

This is a configuration backup, not a disk image. To recover a lost host, reinstall the same Proxmox version, restore the required files from the archive, and restore the VMs from their own backups. Restore `config.db` only with `pve-cluster` stopped.

## Install

Installing or changing this on the host requires the owner's approval.

```bash
install -m 755 homelab-host-config-backup.py /usr/local/sbin/homelab-host-config-backup
install -m 644 homelab-host-config-backup.service homelab-host-config-backup.timer /etc/systemd/system/
systemctl daemon-reload
systemd-analyze verify homelab-host-config-backup.service homelab-host-config-backup.timer
systemctl start homelab-host-config-backup.service
systemctl enable --now homelab-host-config-backup.timer
```

Logs: `journalctl -u homelab-host-config-backup.service`. Stop future runs with `systemctl disable --now homelab-host-config-backup.timer`.

## Limits

- Failures appear only in the journal. The Telegram alerts cover `vzdump` notifications, not this unit.
- Like the VM backups, the archives share one QNAP, and a run is missed if the host is down at 02:30.
- A full restore has not been tested.

Tests: run `python3 test_host_config_backup.py` from this directory.

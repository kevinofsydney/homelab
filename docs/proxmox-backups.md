# Proxmox VM backups

Status: **deployed and restore-tested 2026-10-28** with the owner's approval. Closes todo action 1.

## What is backed up

| Item | Setting |
| --- | --- |
| Job | `backup-every-3-days` (Datacenter → Backup) |
| Guests | VM 100 `dev`, VM 101 `hermes-agent`, VM 130 `home-services`. Template 9000 is not backed up; rebuild it from the Ubuntu image in [the template procedure](../proxmox/template.md) |
| Schedule | `*-*-1/3 02:30`: days 1, 4, 7 … 31 of each month, so two runs can be 1–2 days apart at a month boundary |
| Retention | `keep-last=15`, about 45 days. Proxmox prunes by count, not age |
| Mode | `snapshot` with the QEMU guest agent freezing and thawing guest filesystems; guests keep running |
| Compression | `zstd` |
| Target | Proxmox storage `qnap-backups`: NFS v4.0 export `/proxmox-backups` on the QNAP, mounted at `/mnt/pve/qnap-backups`, content `backup` only. Mount options `vers=4.0,soft` (the QNAP refuses NFS 4.1) |

Paperless documents live on the QNAP's own `paperless` share and are not inside VM 130's disk; the VM backup covers Paperless's database, configuration and search index.

## QNAP share

Created by the owner in QTS on 2026-10-28: shared folder `proxmox-backups` on the existing data volume; NFS host access for the Proxmox host's address only, read/write, `NO_ROOT_SQUASH` (vzdump writes as root), security `sys`. `showmount -e` lists `/proxmox-backups` for the Proxmox host only and `/paperless` for the application VM only. Plex shares were not touched.

On 2026-10-28 the owner reported that the QNAP Recycle Bin is off for this backup share. This is an operator report; it has not been independently verified in QTS.

## Evidence (2026-10-28)

- Test mount from Proxmox: NFS 4.1 refused, 4.0 accepted; root-owned writes; a 512 MB `fsync` write succeeded; 5.4 TB free of 7.8 TB.
- `pvesm add nfs qnap-backups …` → storage active. The previous `storage.cfg` is at `/root/storage.cfg.pre-qnap-backups-20261028` on the host.
- First run (same options as the job): all three guests `OK`, guest-agent freeze/thaw on each, 3 min in total.

  | VM | Archive | Time |
  | --- | --- | --- |
  | 100 | 6.48 GB | 1 min 17 s |
  | 101 | 4.05 GB | 56 s |
  | 130 | 3.91 GB | 58 s |

  About 14.4 GB per run, so 15 kept runs need roughly 216 GB.
- Restore test: `qmrestore` of the VM 100 archive to VMID 900 on `local-lvm` with `--unique 1` (new MAC) took 68 s. `net0` was set `link_down=1` before boot so the copy could not collide with VM 100 on the LAN or tailnet. The guest agent answered about 6 s after start; the copy reported Ubuntu 26.04.1, the `coder` account, Git 2.53.0 and the Codex, OpenCode and Node binaries; its only failed unit was `systemd-networkd-wait-online` (expected with the link down). VM 900 was then stopped and destroyed with its disks; `local-lvm` usage returned to its prior value and VMs 100, 101 and 130 kept running throughout.

## Restore

1. Datacenter → Storage `qnap-backups` → Backups, or `ls /mnt/pve/qnap-backups/dump/`.
2. To test or recover alongside the original: `qmrestore <archive> <unused vmid> --storage local-lvm --unique 1`, then `qm set <vmid> --net0 <net0>,link_down=1` before the first boot.
3. To replace a lost guest: stop or remove the broken one, restore to its original VMID without `--unique`, and start it. For VM 130, confirm the Paperless NFS mount before relying on it.

## Failure alerts (2026-10-28)

- Webhook target `telegram-alerts` (Datacenter → Notifications) posts to the Telegram Bot API `sendMessage` for the owner's chat, using a dedicated bot, `the alerts bot`. The bot token is the target's secret `token`, entered by the owner on the host with hidden input and stored in `/etc/pve/priv/notifications.cfg`; it is not in Git. The message body is only the notification title and severity, which stays within Telegram's length limit; full logs remain in the Proxmox task view.
- Matcher `backup-alerts` sends `type=vzdump` notifications of severity `warning` or `error` to that target, so successful runs stay quiet. The job uses `notification-mode notification-system`. The previous configuration is at `/root/notifications.cfg.pre-telegram-20261028` on the host.
- Evidence: a direct `sendMessage` with the stored token, the built-in target test, and a forced failure (`vzdump 9999`, a VMID that does not exist; the log shows `notified via target telegram-alerts`) all reached the owner's phone, including the message `vzdump backup status (pve1.home.arpa): backup failed [error]`.
- To change the token: `pvesh set /cluster/notifications/endpoints/webhook/telegram-alerts --secret "name=token,value=<base64 token>"`, ideally read with `read -rs` as in the original setup. To revoke: BotFather → the alerts bot → Revoke current token.
- The built-in `mail-to-root` target still fires through the default matcher but bounces, because no email address is set for `root@pam`. It is harmless.
- Not covered: a job that never runs, for example because the host is down at 02:30. An Uptime Kuma push monitor would catch that.

## Limits

- The backups and the Paperless documents share one QNAP. A QNAP failure, fire or theft loses both. An off-site copy of the irreplaceable parts (the Paperless database) is a separate, optional step.

# dev VM: GRUB environment block corruption — RCA and permanent fix

Date: 2026-10-28. Closes action 7 in [open work](../agents/todo.md).

## Symptom

`grub2-common.service` failed at boot, so the guest reported `degraded` and GRUB's `recordfail` fallback was unreliable. Two different failures were observed on consecutive boots: `grub-editenv: error: invalid environment block`, then `No such file` after the unit's `ExecStartPre` deleted an empty file.

## Investigation

- `/etc/default/grub`: `GRUB_DEFAULT=0`, `GRUB_TIMEOUT=0`; the guest is BIOS booted (`grub-pc`).
- `/boot/grub/grub.cfg` line 84 calls `save_env recordfail` from the menu loop, so **the bootloader writes `/boot/grub/grubenv` on every boot** (setting `recordfail=1`), and `grub2-common.service` clears it after a successful boot.
- A temporary capture unit snapshotted the block at shutdown and again at boot *before* `grub2-common.service`. On a clean reboot the two blocks differed by 13 bytes, all inside the `recordfail=1` variable; padding was `0x23` in both, and both parsed.
- No format skew: the block GRUB wrote was accepted by `grub-editenv` 2.14 immediately afterwards. The MBR core differs from the shipped `/boot/grub/i386-pc/core.img`, which is expected because `grub-install` generates it per disk.
- `/boot` is ext4, 4 KiB blocks, `metadata_csum`, clean at inspection.

## Root cause

GRUB writes the 1024-byte environment block **from the bootloader, directly to the block device, outside any ext4 journal transaction**. If the guest stops before that write is durable — a host-level stop, `qm stop`, or the host crash on 2026-10-27 — the block can be left torn, or journal replay can restore an older generation of the containing block. On the following boot userspace then reads an invalid block, and the second failure follows from `ExecStartPre` deleting the resulting empty file.

Both observed failures came after hard or host-level stops. Clean reboots, including the two used for acceptance, never reproduce it, which is why it looked intermittent and unrelated to shutdown cleanliness: the guest can shut down cleanly while an earlier bootloader write was never durable.

## Fix

Two root-owned pieces, no package modifications:

- `/usr/local/sbin/grubenv-ensure-valid` — validates with `grub-editenv list`; if the file is missing, empty or invalid it recreates it with `grub-editenv create` and logs one line to stderr.
- `/etc/systemd/system/grub2-common.service.d/50-homelab-grubenv.conf` — replaces the unit's `ExecStartPre` with that script, subsuming the original `[ -s ... ] || rm -f` test and `mkdir -p`. The unit can no longer fail because of a torn block.

## Verified

- Random bytes written over the block → unit restart succeeded, block recreated, `grub-editenv list` returned 0.
- File deleted → same.
- Two consecutive reboots: `systemctl is-system-running` = `running`, `grub2-common.service` not failed, `grub-editenv list` returned 0.
- Captured pre-fix evidence kept at `/root/grubenv-capture-evidence.txt` on the guest.

## Not fixed

- The durability window itself: GRUB still writes outside the journal on every boot, so a torn block remains possible. The system now repairs it at the next boot instead of staying `degraded`. Removing the window would mean UEFI boot or a bootloader change, which is out of scope.
- A hard stop mid-write can in principle damage other `/boot` content, and there is still no backup of this guest (action 1).

## Rollback

```bash
sudo rm -f /etc/systemd/system/grub2-common.service.d/50-homelab-grubenv.conf /usr/local/sbin/grubenv-ensure-valid
sudo systemctl daemon-reload
```

The unit then returns to its packaged behaviour and will fail again on a torn block.

## Related fix in a parallel session

The same day, a separate session found that the 24.04 SysV script `/etc/init.d/grub-common` (an obsolete `grub-common` conffile after the 26.04 upgrade) still started at boot alongside the native `grub2-common.service`; both rewrote `/boot/grub/grubenv` within milliseconds, which explains failures after clean shutdowns. That script was backed up to `/root/obsolete-conffiles/` and removed. Both fixes are in place and complement each other: one removes the race, the guard above repairs a block torn by a hard stop.

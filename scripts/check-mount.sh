#!/usr/bin/env bash
set -euo pipefail
mountpoint="${1:?usage: check-mount.sh /mount/path server:/export}"
expected_source="${2:?Set the expected NFS server:/export source}"
# Touch the directory to trigger a configured automount before inspecting it.
timeout 15 stat -- "$mountpoint/." >/dev/null
fstype="$(findmnt --mountpoint "$mountpoint" --noheadings --output FSTYPE)"
[[ "$fstype" == nfs || "$fstype" == nfs4 ]] || {
  echo "Required NAS mount unavailable or wrong filesystem: $mountpoint" >&2
  exit 1
}
actual_source="$(findmnt --mountpoint "$mountpoint" --noheadings --output SOURCE)"
[[ "$actual_source" == "$expected_source" ]] || {
  echo "NAS source mismatch at $mountpoint" >&2; exit 1;
}
test -r "$mountpoint" || { echo "NAS mount unreadable: $mountpoint" >&2; exit 1; }

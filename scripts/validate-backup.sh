#!/usr/bin/env bash
# Non-destructive read/write probe on a verified dedicated backup mount.
set -euo pipefail
target="${1:?usage: validate-backup.sh /mounted/backup/path server:/export}"
expected_source="${2:?Set the expected NFS server:/export source}"
"$(dirname "$0")/check-mount.sh" "$target" "$expected_source"
probe="$(mktemp "$target/.backup-probe.XXXXXXXX")"
trap 'rm -f -- "$probe"' EXIT
printf 'homelab-backup-probe\n' > "$probe"
sync "$probe"
test "$(cat "$probe")" = 'homelab-backup-probe'
echo "PASS: backup mount read/write probe. A restore test is still required."

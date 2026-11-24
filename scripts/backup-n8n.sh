#!/usr/bin/env bash
# Nightly online n8n backup to the dedicated QNAP backup export. Plan by default.
#
# Copies a consistent SQLite snapshot (workflows, credentials, data tables, execution history)
# and n8n's own workflow/credential exports. Credentials stay encrypted with the instance
# encryption key, which is deliberately NOT copied: the owner keeps it in a password manager,
# so a reader of the NAS share cannot decrypt the credentials. A restore needs both.
set -euo pipefail
dir=/opt/homelab/n8n
data=/srv/n8n/data
envfile="$dir/.env"
mountpoint=/mnt/qnap-backups
if [[ "${1:-}" != '--apply' ]]; then
  echo "PLAN ONLY: verify $mountpoint is the approved NFS export, snapshot $data/database.sqlite,"
  echo 'export workflows and encrypted credentials, write checksums and a COMPLETE marker.'
  echo 'The encryption key is never copied. Pass --apply after reviewing the destination.'
  exit 0
fi
[[ $(id -u) == 0 ]] || { echo 'Run as root on the n8n VM' >&2; exit 2; }
source_spec=$(sed -n 's/^N8N_BACKUP_SOURCE=//p' "$envfile")
[[ -n "$source_spec" && "$source_spec" != *REPLACE* ]] || { echo "Set N8N_BACKUP_SOURCE in $envfile" >&2; exit 2; }
"$dir/check-mount.sh" "$mountpoint" "$source_spec"
[[ -f "$data/database.sqlite" ]] || { echo "No database at $data/database.sqlite" >&2; exit 2; }

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
dest="$mountpoint/n8n/$stamp"
work="$data/backup-work"
mkdir -p "$dest"
rm -rf -- "$work"
install -d -o 1000 -g 1000 -m 0700 "$work"
trap 'rm -rf -- "$work"' EXIT

# SQLite's online backup API gives a consistent copy while n8n keeps running.
sqlite3 "$data/database.sqlite" ".backup '$work/database.sqlite'"
sqlite3 "$work/database.sqlite" 'PRAGMA integrity_check;' | grep -qx ok \
  || { echo 'Snapshot failed its integrity check' >&2; exit 1; }

compose=(docker compose --project-directory "$dir" --env-file "$envfile" -f "$dir/compose.yml")
"${compose[@]}" exec -T n8n n8n export:workflow --all --output=/home/node/.n8n/backup-work/workflows.json
"${compose[@]}" exec -T n8n n8n export:credentials --all --output=/home/node/.n8n/backup-work/credentials.encrypted.json

gzip -9 "$work/database.sqlite"
cp -- "$work/database.sqlite.gz" "$work/workflows.json" "$work/credentials.encrypted.json" "$dest/"
[[ ! -e "$dest/config" ]] || { echo 'Refusing: encryption key file found in destination' >&2; exit 1; }
(cd "$dest" && sha256sum database.sqlite.gz workflows.json credentials.encrypted.json > SHA256SUMS)
touch "$dest/COMPLETE"
echo "Backup stored at $dest; a restore test is required before relying on it."

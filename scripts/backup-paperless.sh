#!/usr/bin/env bash
# Offline application-consistent DB/media backup. Plan by default.
set -euo pipefail
if [[ "${1:-}" != '--apply' ]]; then
  echo 'PLAN ONLY: verify Paperless media and backup mounts, stop webserver briefly, dump PostgreSQL, copy media/data, restart webserver.'
  echo 'Pass --apply after reviewing the downtime and destination.'
  exit 0
fi
repo="$(cd "$(dirname "$0")/.." && pwd)"
dir="$repo/compose/paperless"
envfile="$dir/.env"
test -f "$envfile" || { echo 'Missing Paperless .env' >&2; exit 2; }
while IFS='=' read -r key value || [[ -n "$key" ]]; do
  value="${value%$'\r'}"
  [[ -z "$key" || "$key" == \#* ]] && continue
  [[ "$key" =~ ^[A-Z][A-Z0-9_]*$ ]] || { echo "Invalid .env key: $key" >&2; exit 2; }
  export "$key=$value"
done < "$envfile"
backup_mount="${PAPERLESS_BACKUP_MOUNT:?Set dedicated NFS backup mount}"
"$repo/scripts/check-mount.sh" "$PAPERLESS_NAS_ROOT" "${PAPERLESS_NAS_SOURCE:?Set expected media NFS source}"
"$repo/scripts/check-mount.sh" "$backup_mount" "${PAPERLESS_BACKUP_SOURCE:?Set expected backup NFS source}"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
dest="$backup_mount/paperless/$stamp"
mkdir -p "$dest"
compose=(docker compose --project-directory "$dir" --env-file "$envfile" -f "$dir/compose.yml")
was_running=false
if "${compose[@]}" ps --status running --services | grep -Fxq webserver; then was_running=true; fi
restore_state() {
  if "$was_running"; then "${compose[@]}" start webserver; fi
}
trap restore_state EXIT
"${compose[@]}" stop webserver
"${compose[@]}" exec -T db sh -c 'exec pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > "$dest/database.sql.gz"
rsync -a -- "$PAPERLESS_NAS_ROOT/media/" "$dest/media/"
rsync -a -- "$PAPERLESS_LOCAL_ROOT/data/" "$dest/data/"
sha256sum "$dest/database.sql.gz" > "$dest/SHA256SUMS"
touch "$dest/COMPLETE"
echo "Backup stored at $dest; perform a restore test before relying on it."

#!/usr/bin/env bash
# Validate by default. --apply requires explicit operator approval.
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
dir="$repo/compose/paperless"
envfile="$dir/.env"
test -f "$envfile" || { echo "Missing $envfile" >&2; exit 2; }
if grep -q REPLACE "$envfile"; then echo 'Replace all .env placeholders' >&2; exit 2; fi
while IFS='=' read -r key value || [[ -n "$key" ]]; do
  value="${value%$'\r'}"
  [[ -z "$key" || "$key" == \#* ]] && continue
  [[ "$key" =~ ^[A-Z][A-Z0-9_]*$ ]] || { echo "Invalid .env key: $key" >&2; exit 2; }
  export "$key=$value"
done < "$envfile"
"$repo/scripts/check-mount.sh" "$PAPERLESS_NAS_ROOT" "${PAPERLESS_NAS_SOURCE:?Set expected NFS source}"
for subdir in media consume export; do
  test -d "$PAPERLESS_NAS_ROOT/$subdir" || { echo "Missing NAS subdirectory: $subdir" >&2; exit 2; }
done
for subdir in postgres valkey data; do
  test -d "$PAPERLESS_LOCAL_ROOT/$subdir" || { echo "Missing local SSD subdirectory: $subdir" >&2; exit 2; }
done
docker compose --project-directory "$dir" --env-file "$envfile" -f "$dir/compose.yml" config --quiet
echo 'PASS: mount, directories and Compose config validated.'
if [[ "${1:-}" != '--apply' ]]; then echo 'PLAN ONLY. Pass --apply after approval.'; exit 0; fi
docker compose --project-directory "$dir" --env-file "$envfile" -f "$dir/compose.yml" up -d
docker compose --project-directory "$dir" --env-file "$envfile" -f "$dir/compose.yml" ps

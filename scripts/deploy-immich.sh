#!/usr/bin/env bash
# Check all dependencies without starting; --apply is an explicit change.
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
dir="$repo/compose/immich"
envfile="$dir/.env"
test -f "$envfile" || { echo 'Missing Immich .env' >&2; exit 2; }
while IFS='=' read -r key value || [[ -n "$key" ]]; do
  value="${value%$'\r'}"
  [[ -z "$key" || "$key" == \#* ]] && continue
  [[ "$key" =~ ^[A-Z][A-Z0-9_]*$ && "$value" != *REPLACE* ]] || { echo "Invalid or placeholder setting: $key" >&2; exit 2; }
  export "$key=$value"
done < "$envfile"
[[ "${IMMICH_UID:-}" =~ ^[1-9][0-9]*$ && "${IMMICH_GID:-}" =~ ^[1-9][0-9]*$ ]] || { echo 'Immich UID and GID must be non-root numeric identities' >&2; exit 2; }
[[ "${DB_PASSWORD:-}" =~ ^[A-Za-z0-9]+$ ]] || { echo 'DB_PASSWORD must be alphanumeric' >&2; exit 2; }
"$repo/scripts/check-mount.sh" "$IMMICH_NAS_ROOT" "${IMMICH_NAS_SOURCE:?Set expected NFS source}"
[[ -d "$IMMICH_NAS_ROOT/library" && ! -L "$IMMICH_NAS_ROOT/library" ]] || { echo 'Missing or unsafe NAS library directory' >&2; exit 1; }
# thumbs is a mount target for the local SSD; encoded-video holds transcodes on the NAS.
for target in thumbs encoded-video; do
  [[ -d "$IMMICH_NAS_ROOT/library/$target" && ! -L "$IMMICH_NAS_ROOT/library/$target" ]] || { echo "Missing or unsafe NAS directory: $target" >&2; exit 1; }
done
python3 - "$IMMICH_BIND_IP" <<'PY'
import ipaddress, json, subprocess, sys
try:
    address = ipaddress.ip_address(sys.argv[1])
    assert address.version == 4 and address in ipaddress.ip_network('100.64.0.0/10')
    status = json.loads(subprocess.check_output(['tailscale', 'status', '--json'], timeout=10))
    assert status.get('BackendState') == 'Running' and str(address) in status.get('TailscaleIPs', [])
except (ValueError, AssertionError, OSError, subprocess.SubprocessError):
    sys.exit('Tailscale is not running with the configured private address')
PY
for path in postgres thumbs model-cache; do
  test -d "$IMMICH_LOCAL_ROOT/$path" || { echo "Missing local directory: $path" >&2; exit 1; }
  fstype="$(findmnt --target "$IMMICH_LOCAL_ROOT/$path" --noheadings --raw --output FSTYPE)"
  [[ "$fstype" == ext4 || "$fstype" == xfs || "$fstype" == btrfs ]] || { echo "Not local storage: $path" >&2; exit 1; }
done
docker compose --project-directory "$dir" --env-file "$envfile" -f "$dir/compose.yml" config --quiet
echo 'PASS: NAS identity, local directories, private bind and Compose configuration.'
if [[ "${1:-}" != '--apply' ]]; then echo 'PLAN ONLY.'; exit 0; fi
docker compose --project-directory "$dir" --env-file "$envfile" -f "$dir/compose.yml" up -d

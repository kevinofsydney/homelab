#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
dir="$repo/compose/uptime-kuma"
envfile="$dir/.env"
test -f "$envfile" || { echo "Missing configuration" >&2; exit 2; }
while IFS='=' read -r key value || [[ -n "$key" ]]; do
  value="${value%$'\r'}"
  [[ -z "$key" || "$key" == \#* ]] && continue
  [[ "$key" =~ ^[A-Z][A-Z0-9_]*$ && "$value" != *REPLACE* ]] || { echo "Invalid or incomplete configuration" >&2; exit 2; }
  export "$key=$value"
done < "$envfile"
python3 - "$KUMA_BIND_IP" <<'PY'
import ipaddress,json,subprocess,sys
try:
    address=ipaddress.ip_address(sys.argv[1])
    if address.version != 4 or address not in ipaddress.ip_network('100.64.0.0/10'):
        raise ValueError('bind must be Tailscale IPv4')
    status=json.loads(subprocess.run(['tailscale','status','--json'],check=True,capture_output=True,text=True,timeout=10).stdout)
    if status.get('BackendState') != 'Running' or str(address) not in status.get('TailscaleIPs',[]):
        raise ValueError('configured Tailscale address is not ready')
except (OSError,ValueError,subprocess.SubprocessError) as exc:
    print(f'Private access not ready: {exc}',file=sys.stderr); sys.exit(1)
PY
test -d "$KUMA_DATA_ROOT" && test ! -L "$KUMA_DATA_ROOT" || { echo 'Missing or invalid SSD data directory' >&2; exit 2; }
fstype="$(findmnt -n -T "$KUMA_DATA_ROOT" -o FSTYPE)"
source="$(findmnt -n -T "$KUMA_DATA_ROOT" -o SOURCE)"
[[ "$fstype" == ext4 && "$source" == /dev/* ]] || { echo 'Kuma data must be on the local ext4 SSD' >&2; exit 2; }
docker compose --project-directory "$dir" --env-file "$envfile" -f "$dir/compose.yml" config --quiet
echo 'PASS: private bind, SSD data and Compose configuration validated.'
if [[ "${1:-}" != --apply ]]; then echo 'PLAN ONLY'; exit 0; fi
docker compose --project-directory "$dir" --env-file "$envfile" -f "$dir/compose.yml" up -d
docker compose --project-directory "$dir" --env-file "$envfile" -f "$dir/compose.yml" ps

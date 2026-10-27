#!/usr/bin/env bash
# Run the existing mount-gated deployment only when its private bind is ready.
set -euo pipefail
root="${PAPERLESS_INSTALL_ROOT:-/opt/homelab}"
envfile="$root/compose/paperless/.env"
# Read only the bind address; never source or print secrets.
python3 - "$envfile" <<'PY'
import ipaddress, json, pathlib, subprocess, sys
try:
    lines = pathlib.Path(sys.argv[1]).read_text().splitlines()
    values = [line.split('=', 1)[1] for line in lines if line.startswith('PAPERLESS_BIND_IP=')]
    if len(values) != 1:
        raise ValueError('expected exactly one private bind address')
    address = ipaddress.ip_address(values[0])
    if address.version != 4 or address not in ipaddress.ip_network('100.64.0.0/10'):
        raise ValueError('private bind address must be a Tailscale IPv4 address')
    result = subprocess.run(['tailscale', 'status', '--json'], check=True, capture_output=True, text=True, timeout=10)
    status = json.loads(result.stdout)
    if status.get('BackendState') != 'Running' or str(address) not in status.get('TailscaleIPs', []):
        raise ValueError('Tailscale is not running with the configured bind address')
except (OSError, ValueError, subprocess.SubprocessError) as exc:
    print(f'Private access not ready: {exc}', file=sys.stderr)
    sys.exit(1)
PY
exec "$root/scripts/deploy-paperless.sh" --apply

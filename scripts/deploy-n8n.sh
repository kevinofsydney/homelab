#!/usr/bin/env bash
# Run as root in the application VM; validation only unless --apply is supplied.
set -euo pipefail
[[ $# -eq 0 || ( $# -eq 1 && "$1" == --apply ) ]] || { echo 'Usage: deploy-n8n.sh [--apply]' >&2; exit 2; }
[[ $(id -u) == 0 ]] || { echo 'Run as root on the application VM' >&2; exit 2; }
root=/srv/n8n/data
compose=/opt/homelab/n8n/compose.yml
[[ -d "$root" && ! -L "$root" && -f "$compose" ]] || { echo 'Expected pre-created local data directory and Compose file' >&2; exit 2; }
fs=$(findmnt -T "$root" -n -o FSTYPE) || exit 2
case "$fs" in ext4|xfs|btrfs) ;; *) echo "Refusing non-local filesystem type: $fs" >&2; exit 2;; esac
docker compose -f "$compose" config --quiet
echo 'PLAN: n8n 2.44.7 with local SSD data, loopback-only port 5678 and no automatic restart.'
[[ "${1:-}" == --apply ]] || { echo 'PLAN ONLY; no containers started.'; exit 0; }
systemctl is-active --quiet docker.service || { echo 'Docker daemon is not running; review network approval first' >&2; exit 2; }
docker compose -f "$compose" up -d
docker compose -f "$compose" ps

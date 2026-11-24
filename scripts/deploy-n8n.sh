#!/usr/bin/env bash
# Run as root on the n8n VM; validation only unless --apply is supplied.
# Refuses to start until the data directory, .env and secret files pass the checks below.
set -euo pipefail
[[ $# -eq 0 || ( $# -eq 1 && "$1" == --apply ) ]] || { echo 'Usage: deploy-n8n.sh [--apply]' >&2; exit 2; }
[[ $(id -u) == 0 ]] || { echo 'Run as root on the n8n VM' >&2; exit 2; }
dir=/opt/homelab/n8n
root=/srv/n8n/data
compose="$dir/compose.yml"
envfile="$dir/.env"
[[ -d "$root" && ! -L "$root" && -f "$compose" && -f "$dir/telegram-relay.mjs" ]] \
  || { echo 'Expected pre-created local data directory, Compose file and relay script' >&2; exit 2; }
fs=$(findmnt -T "$root" -n -o FSTYPE) || exit 2
case "$fs" in ext4|xfs|btrfs) ;; *) echo "Refusing non-local filesystem type: $fs" >&2; exit 2;; esac

[[ -f "$envfile" && ! -L "$envfile" ]] || { echo "Missing $envfile; copy .env.example and fill it" >&2; exit 2; }
[[ $(stat -c '%u %a' "$envfile") == '0 600' ]] || { echo "$envfile must be root-owned with mode 0600" >&2; exit 2; }
if grep -q 'REPLACE' "$envfile"; then echo "$envfile still contains REPLACE placeholders" >&2; exit 2; fi
secrets_dir=$(sed -n 's/^N8N_SECRETS_DIR=//p' "$envfile")
secrets_dir=${secrets_dir:-$dir/secrets}
for name in telegram_bot_token relay_shared_secret; do
  file="$secrets_dir/$name"
  [[ -f "$file" && ! -L "$file" && -s "$file" ]] || { echo "Missing or empty secret file: $file" >&2; exit 2; }
  [[ $(stat -c '%u %a' "$file") == '1000 400' ]] || { echo "$file must be owned by UID 1000 with mode 0400" >&2; exit 2; }
done

docker compose --project-directory "$dir" --env-file "$envfile" -f "$compose" config --quiet
echo 'PLAN: pinned n8n plus Telegram relay; local SSD data, loopback-only port 5678, restart unless-stopped.'
[[ "${1:-}" == --apply ]] || { echo 'PLAN ONLY; no containers started.'; exit 0; }
systemctl is-active --quiet docker.service || { echo 'Docker daemon is not running; review network approval first' >&2; exit 2; }
docker compose --project-directory "$dir" --env-file "$envfile" -f "$compose" up -d
docker compose --project-directory "$dir" --env-file "$envfile" -f "$compose" ps

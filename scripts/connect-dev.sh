#!/usr/bin/env bash
# Usage: connect-dev.sh HOST [IDENTITY_FILE] [--admin]
set -euo pipefail
if [[ $# -lt 1 || $# -gt 3 || ! "$1" =~ ^[a-zA-Z0-9.:_-]+$ || "$1" == -* ]]; then
  echo 'Usage: connect-dev.sh HOST [IDENTITY_FILE] [--admin]' >&2
  exit 2
fi
host=$1
shift
args=(-t -o StrictHostKeyChecking=ask)
admin=0
while (( $# )); do
  if [[ "$1" == --admin ]]; then
    (( admin == 0 )) || exit 2
    admin=1
  elif [[ "$1" != -* && ${identity_set:-0} == 0 ]]; then
    args+=(-i "$1")
    identity_set=1
  else
    echo 'Invalid argument' >&2
    exit 2
  fi
  shift
done
args+=("devops@$host")
if (( ! admin )); then args+=('sudo -iu coder'); fi
exec ssh "${args[@]}"

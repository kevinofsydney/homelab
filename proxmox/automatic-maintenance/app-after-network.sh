#!/bin/sh
set -eu
# Values are site-specific and supplied by the root-owned systemd environment file.
: "${APP_CONTAINER:?}" "${APP_WORKDIR:?}" "${APP_COMPOSE:?}" "${APP_ENVFILE:?}" "${APP_SERVICE:?}" "${APP_PORT:?}"
bind_ip=$(docker inspect --format '{{(index (index .HostConfig.PortBindings "8501/tcp") 0).HostIp}}' "$APP_CONTAINER")
[ -n "$bind_ip" ]
ip -o -4 addr show dev tailscale0 | grep -F -q " $bind_ip/"
if curl --noproxy '*' --fail --silent --max-time 5 "http://$bind_ip:$APP_PORT/" >/dev/null; then
    exit 0
fi
cd "$APP_WORKDIR"
exec docker compose -f "$APP_COMPOSE" --env-file "$APP_ENVFILE" up -d --no-deps --no-build --pull never --force-recreate "$APP_SERVICE"

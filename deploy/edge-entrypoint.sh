#!/bin/sh
set -eu

if [ -s /config/caddy/autosave.json ]; then
  exec caddy run --resume
fi

exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile

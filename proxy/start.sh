#!/usr/bin/env bash
# Start the Burp-equivalent intercepting proxy, chained through the sandbox
# egress proxy. Auth is read from the environment at runtime — NEVER hardcode it.
# Usage: ./start.sh [port]   (default 8080)
set -euo pipefail
cd "$(dirname "$0")"
PORT="${1:-8080}"
if [[ -z "${https_proxy:-}" ]]; then
  echo "ERROR: https_proxy not set in environment" >&2; exit 1
fi
AUTH="${https_proxy#http://}"
AUTH="${AUTH%%@*}"
exec ./venv/bin/mitmdump -p "$PORT" \
  --mode "upstream:http://hatch-egress-proxy:3128" \
  --upstream-auth "$AUTH" \
  --set ssl_insecure=true \
  -s addons/logger.py \
  -s addons/modify.py \
  -s addons/scope.py

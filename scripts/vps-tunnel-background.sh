#!/bin/bash
# Run cloudflared tunnel in background (survives closing Browser Terminal tab).
# Usage on VPS: bash scripts/vps-tunnel-background.sh

set -euo pipefail

CF="/usr/local/bin/cloudflared"
if [ ! -x "$CF" ]; then
  curl -sL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64" -o "$CF"
  chmod +x "$CF"
fi

# Stop old quick tunnels
pkill -f "cloudflared tunnel --url" 2>/dev/null || true
sleep 1

LOG="/var/log/cloudflared-admin.log"
nohup "$CF" tunnel --url http://127.0.0.1:80 >"$LOG" 2>&1 &
sleep 8

URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG" | head -1)
if [ -z "$URL" ]; then
  echo "Tunnel starting — check log: tail -f $LOG"
  tail -20 "$LOG"
  exit 1
fi

echo "Tunnel URL: $URL"
echo "Update laptop .env:"
echo "  VITE_API_PROXY_TARGET=$URL"
echo "  EXPO_PUBLIC_API_URL=$URL"
echo ""
echo "Admin browser: $URL"
echo "Log: tail -f $LOG"

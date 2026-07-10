#!/bin/bash
# Rebuild admin for Cloudflare quick tunnel (or any hostname on port 80).
# Uses relative /api/ URLs — works on tunnel URL without mixed-content errors.
#
# Usage on VPS (tunnel must be running in another terminal):
#   cd ~/Cosmic-Lens-Backend && bash scripts/vps-rebuild-admin-tunnel.sh
#
# Optional: TUNNEL_URL=https://xxx.trycloudflare.com (only for echo at end)

set -euo pipefail

REPO="${REPO:-/root/Cosmic-Lens-Backend}"
ADMIN_ROOT="${ADMIN_ROOT:-/var/www/cosmic-admin}"
TUNNEL_URL="${TUNNEL_URL:-}"

cd "$REPO"

ADMIN_SECRET=$(grep '^ADMIN_SECRET=' artifacts/api-server/.env 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
if [ -z "$ADMIN_SECRET" ]; then
  echo "ERROR: ADMIN_SECRET missing in artifacts/api-server/.env"
  exit 1
fi

echo "=== Build admin (relative API — no VITE_API_BASE) ==="
npm install -g pnpm 2>/dev/null || true
pnpm install
cd artifacts/admin-web
# Empty VITE_API_BASE => fetch("/api/...") same origin (tunnel or IP both work)
export VITE_API_BASE=""
export VITE_ADMIN_SECRET="$ADMIN_SECRET"
pnpm run build

echo "=== Deploy to ${ADMIN_ROOT} ==="
mkdir -p "$ADMIN_ROOT"
rm -rf "${ADMIN_ROOT:?}"/*
cp -a dist/. "$ADMIN_ROOT/"
chown -R www-data:www-data "$ADMIN_ROOT"
chmod -R a+rX "$ADMIN_ROOT"

echo ""
echo "=== Smoke test (localhost nginx) ==="
curl -sf -m 5 http://127.0.0.1/api/healthz && echo " API OK"
CODE=$(curl -sf -m 5 -o /dev/null -w "%{http_code}" -H "X-Admin-Token: ${ADMIN_SECRET}" \
  "http://127.0.0.1/api/admin/ask-questions?page=1&per_page=1")
echo "ask-questions HTTP ${CODE} (expect 200)"

echo ""
echo "DONE. Hard refresh admin in browser (Ctrl+Shift+R)."
if [ -n "$TUNNEL_URL" ]; then
  echo "Open: ${TUNNEL_URL}"
else
  echo "Open your running cloudflared trycloudflare.com URL."
fi

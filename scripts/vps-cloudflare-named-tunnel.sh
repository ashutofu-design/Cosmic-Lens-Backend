#!/bin/bash
# Permanent fixed URL via Cloudflare Named Tunnel (not trycloudflare quick tunnel).
#
# Prerequisites (one-time, ~10 min):
#   1. Free Cloudflare account: https://dash.cloudflare.com/sign-up
#   2. Domain added to Cloudflare (e.g. cosmiclens.app)
#   3. Run this script on VPS Browser Terminal
#
# Result: fixed URL like https://api.cosmiclens.app (never changes on reboot)
#
# Usage:
#   export TUNNEL_HOSTNAME=api.cosmiclens.app   # or admin.cosmiclens.app
#   cd /root/Cosmic-Lens-Backend && bash scripts/vps-cloudflare-named-tunnel.sh

set -euo pipefail

TUNNEL_NAME="${TUNNEL_NAME:-cosmic-lens}"
TUNNEL_HOSTNAME="${TUNNEL_HOSTNAME:-api.cosmiclens.app}"
ORIGIN_URL="${ORIGIN_URL:-http://127.0.0.1:80}"
CF_DIR="/etc/cloudflared"
CF_BIN="/usr/local/bin/cloudflared"
REPO="${REPO:-/root/Cosmic-Lens-Backend}"

echo "=============================================="
echo " Permanent URL: https://${TUNNEL_HOSTNAME}"
echo "=============================================="

if [ ! -x "$CF_BIN" ]; then
  echo "Installing cloudflared..."
  curl -sL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64" -o "$CF_BIN"
  chmod +x "$CF_BIN"
fi

# Stop quick tunnels (random trycloudflare URLs)
pkill -f "cloudflared tunnel --url" 2>/dev/null || true

mkdir -p "$CF_DIR"

if [ ! -f "$CF_DIR/cert.pem" ]; then
  echo ""
  echo "STEP 1 — Login to Cloudflare (opens a link; paste URL in browser if headless):"
  "$CF_BIN" tunnel login
fi

if ! "$CF_BIN" tunnel list 2>/dev/null | grep -q "^${TUNNEL_NAME} "; then
  echo ""
  echo "STEP 2 — Creating tunnel '${TUNNEL_NAME}'..."
  "$CF_BIN" tunnel create "$TUNNEL_NAME"
fi

TUNNEL_ID=$("$CF_BIN" tunnel list 2>/dev/null | awk -v n="$TUNNEL_NAME" '$2 == n {print $1; exit}')
if [ -z "$TUNNEL_ID" ]; then
  echo "ERROR: Could not find tunnel ID for ${TUNNEL_NAME}"
  exit 1
fi

CREDS="$CF_DIR/${TUNNEL_ID}.json"
if [ ! -f "$CREDS" ]; then
  echo "ERROR: Missing $CREDS — re-run: cloudflared tunnel create ${TUNNEL_NAME}"
  exit 1
fi

cat >"$CF_DIR/config.yml" <<EOF
tunnel: ${TUNNEL_ID}
credentials-file: ${CREDS}

ingress:
  - hostname: ${TUNNEL_HOSTNAME}
    service: ${ORIGIN_URL}
  - service: http_status:404
EOF

echo ""
echo "STEP 3 — DNS route (CNAME ${TUNNEL_HOSTNAME} -> tunnel)..."
"$CF_BIN" tunnel route dns "$TUNNEL_NAME" "$TUNNEL_HOSTNAME" || {
  echo "WARN: DNS route failed — add manually in Cloudflare DNS:"
  echo "  CNAME  ${TUNNEL_HOSTNAME%%.*}  ->  ${TUNNEL_ID}.cfargotunnel.com  (proxied)"
}

echo ""
echo "STEP 4 — Install systemd service (auto-start on reboot)..."
"$CF_BIN" service install 2>/dev/null || true
systemctl enable cloudflared 2>/dev/null || true
systemctl restart cloudflared
sleep 3
systemctl is-active cloudflared && echo "cloudflared service: running" || journalctl -u cloudflared -n 20 --no-pager

echo ""
echo "STEP 5 — Rebuild admin (relative /api/ — works on any hostname)..."
if [ -f "$REPO/scripts/vps-rebuild-admin-tunnel.sh" ]; then
  TUNNEL_URL="https://${TUNNEL_HOSTNAME}" bash "$REPO/scripts/vps-rebuild-admin-tunnel.sh" || true
fi

echo ""
echo "=============================================="
echo " DONE — permanent URLs (same forever):"
echo "   Admin:  https://${TUNNEL_HOSTNAME}/"
echo "   API:    https://${TUNNEL_HOSTNAME}/api/healthz"
echo ""
echo " Laptop .env:"
echo "   VITE_API_PROXY_TARGET=https://${TUNNEL_HOSTNAME}"
echo "   EXPO_PUBLIC_API_URL=https://${TUNNEL_HOSTNAME}"
echo "=============================================="

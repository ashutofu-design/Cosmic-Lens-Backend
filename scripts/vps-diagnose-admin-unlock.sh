#!/bin/bash
# Diagnose admin panel-unlock: API → nginx → public HTTPS
# Usage: cd /root/Cosmic-Lens-Backend && bash scripts/vps-diagnose-admin-unlock.sh

set -euo pipefail

ADMIN_DOMAIN="${ADMIN_DOMAIN:-admin.coosmic.icu}"
API_PORT="${API_PORT:-8080}"
DEVICE="abcdef0123456789abcdef0123456789"
BODY='{"device_id":"'"$DEVICE"'","steps":["locate","locate","locate","for","for","for"]}'

echo "=== 1) PM2 API direct (:8080) ==="
curl -sS -m 10 -w "\nHTTP %{http_code}\n" -X POST "http://127.0.0.1:${API_PORT}/api/admin/panel-unlock" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Device-Id: ${DEVICE}" \
  -d "$BODY" || echo "FAIL: API not responding on :8080"

echo ""
echo "=== 2) nginx HTTP + Host: ${ADMIN_DOMAIN} ==="
curl -sS -m 10 -w "\nHTTP %{http_code}\n" -X POST "http://127.0.0.1/api/admin/panel-unlock" \
  -H "Host: ${ADMIN_DOMAIN}" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Device-Id: ${DEVICE}" \
  -d "$BODY" || echo "FAIL: nginx /api proxy broken for ${ADMIN_DOMAIN}"

echo ""
echo "=== 3) Public HTTP (no SSL) ==="
curl -sS -m 10 -w "\nHTTP %{http_code}\n" -X POST "http://${ADMIN_DOMAIN}/api/admin/panel-unlock" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Device-Id: ${DEVICE}" \
  -d "$BODY" || echo "FAIL: HTTP public"

echo ""
echo "=== 4) Public HTTPS (10s timeout) ==="
curl -sS -m 10 -w "\nHTTP %{http_code}\n" -X POST "https://${ADMIN_DOMAIN}/api/admin/panel-unlock" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Device-Id: ${DEVICE}" \
  -d "$BODY" || echo "FAIL/HANG: HTTPS — Cloudflare or SSL issue"

echo ""
echo "=== 5) nginx sites enabled ==="
ls -la /etc/nginx/sites-enabled/ 2>/dev/null || true
echo ""
grep -R "server_name\|location /api" /etc/nginx/sites-enabled/ 2>/dev/null | head -30 || true

echo ""
echo "=== 6) Redis + pm2 ==="
redis-cli ping 2>/dev/null || echo "redis-cli ping failed"
pm2 list 2>/dev/null | head -6 || true

echo ""
echo "DONE — step 1 must show gate_token. If step 2 fails → run: bash scripts/vps-nginx-coosmic-domain.sh"

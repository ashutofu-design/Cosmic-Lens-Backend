#!/bin/bash
# Run ON the VPS (ssh root@187.127.174.55) — checks why phone/laptop cannot reach :8080.
set -euo pipefail

PUBLIC_IP="${PUBLIC_IP:-187.127.174.55}"
PORT="${PORT:-8080}"

echo "=== listen on :${PORT} ==="
ss -ltnp | grep ":${PORT}" || echo "NOT LISTENING"

echo ""
echo "=== local healthz ==="
curl -s -m 5 "http://127.0.0.1:${PORT}/api/healthz" || echo "LOCAL FAIL"

echo ""
echo "=== healthz via public IP (from VPS) ==="
curl -s -m 8 "http://${PUBLIC_IP}:${PORT}/api/healthz" || echo "PUBLIC IP FAIL — Hostinger firewall likely blocking ${PORT}"

echo ""
echo "=== ufw ==="
ufw status 2>/dev/null || echo "ufw not active"

echo ""
echo "=== nginx (443 proxy) ==="
systemctl is-active nginx 2>/dev/null || echo "nginx not running"
curl -s -m 8 -o /dev/null -w "https://api.cosmiclens.app HTTP %{http_code}\n" https://api.cosmiclens.app/api/healthz 2>/dev/null || echo "api.cosmiclens.app not reachable from VPS (DNS/nginx?)"

echo ""
echo "Fix: Hostinger hPanel → VPS → Firewall → allow inbound TCP ${PORT}"
echo "Or: DNS A record api.cosmiclens.app → ${PUBLIC_IP} + nginx proxy to 127.0.0.1:${PORT}"

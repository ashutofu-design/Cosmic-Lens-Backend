#!/bin/bash
# Diagnose why laptop gets ETIMEDOUT despite Hostinger firewall open.
# Run on VPS Browser Terminal.

set -euo pipefail

PUBLIC_IP="${PUBLIC_IP:-187.127.174.55}"

echo "=== 1) Real public IP of this VPS ==="
curl -4 -s --max-time 8 ifconfig.me || curl -4 -s --max-time 8 icanhazip.com || echo "could not detect"
echo ""

echo "=== 2) nginx listening? ==="
ss -tlnp | grep -E ':80|:443|:8080' || true

echo ""
echo "=== 3) ufw (can block even when Hostinger panel is open) ==="
if command -v ufw >/dev/null 2>&1; then
  ufw status verbose || true
else
  echo "ufw not installed"
fi

echo ""
echo "=== 4) iptables INPUT (first 25 lines) ==="
iptables -L INPUT -n --line-numbers 2>/dev/null | head -25 || echo "no iptables"

echo ""
echo "=== 5) Local tests ==="
curl -sf -m 5 http://127.0.0.1:8080/api/healthz && echo " :8080 OK"
curl -sf -m 5 http://127.0.0.1/api/healthz && echo " :80 /api OK"
curl -sf -m 5 -o /dev/null -w "admin :80 HTTP %{http_code}\n" http://127.0.0.1/

echo ""
echo "=== 6) Public IP test FROM this server ==="
curl -sf -m 8 "http://${PUBLIC_IP}/api/healthz" && echo " public :80 OK" || echo " public :80 FAIL from VPS itself"
curl -sf -m 8 "http://${PUBLIC_IP}:8080/api/healthz" && echo " public :8080 OK" || echo " public :8080 FAIL"

echo ""
echo "=== 7) FIX ufw if active (permanent) ==="
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  echo "Opening ufw ports 22,80,443,8080 ..."
  ufw allow 22/tcp || true
  ufw allow 80/tcp || true
  ufw allow 443/tcp || true
  ufw allow 8080/tcp || true
  ufw reload || true
  ufw status numbered || true
fi

echo ""
echo "=== DONE ==="
echo "If step 6 public :80 FAIL -> Hostinger support (edge firewall)."
echo "If step 6 OK but laptop ETIMEDOUT -> your ISP/home router blocks datacenter IP."
echo "Permanent ISP fix: Cloudflare proxy on api.cosmiclens.app (see admin README)."

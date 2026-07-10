#!/bin/bash
# Make Cosmic Lens API reachable from phone/laptop.
# Run on VPS: ssh root@187.127.174.55 'bash -s' < scripts/vps-setup-public-api.sh
set -euo pipefail

PUBLIC_IP="${PUBLIC_IP:-187.127.174.55}"
PORT="${PORT:-8080}"
API_DOMAIN="${API_DOMAIN:-api.cosmiclens.app}"

echo "=== 1. Local API ==="
curl -sf -m 5 "http://127.0.0.1:${PORT}/api/healthz" | head -c 200 || {
  echo "FAIL: cosmic-api not responding locally. Run: pm2 restart cosmic-api"
  exit 1
}
echo ""
echo "Local OK"

echo ""
echo "=== 2. ufw (if installed) ==="
if command -v ufw >/dev/null 2>&1; then
  ufw allow "${PORT}/tcp" || true
  ufw allow 443/tcp || true
  ufw allow 80/tcp || true
  ufw status || true
else
  echo "ufw not found — use Hostinger hPanel → VPS → Firewall → allow TCP ${PORT}"
fi

echo ""
echo "=== 3. Test public IP :${PORT} from this VPS ==="
if curl -sf -m 8 "http://${PUBLIC_IP}:${PORT}/api/healthz" >/dev/null; then
  echo "Public :${PORT} OK — phone should work with http://${PUBLIC_IP}:${PORT}"
else
  echo "Public :${PORT} FAIL"
  echo "→ Open Hostinger hPanel → VPS → Firewall → Inbound → TCP ${PORT} → Accept"
  echo "→ Then retry: curl http://${PUBLIC_IP}:${PORT}/api/healthz"
fi

echo ""
echo "=== 4. nginx + HTTPS (optional, recommended) ==="
if command -v nginx >/dev/null 2>&1; then
  echo "nginx installed"
else
  echo "To install: apt update && apt install -y nginx certbot python3-certbot-nginx"
fi

NGINX_SITE="/etc/nginx/sites-available/cosmic-api"
if [ ! -f "$NGINX_SITE" ]; then
  cat <<EOF | tee "$NGINX_SITE" >/dev/null
server {
    listen 80;
    server_name ${API_DOMAIN};

    location / {
        proxy_pass http://127.0.0.1:${PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
    }
}
EOF
  ln -sf "$NGINX_SITE" "/etc/nginx/sites-enabled/cosmic-api"
  nginx -t && systemctl reload nginx
  echo "nginx site created for ${API_DOMAIN}"
  echo "DNS: add A record ${API_DOMAIN} → ${PUBLIC_IP}"
  echo "SSL: certbot --nginx -d ${API_DOMAIN}"
else
  echo "nginx site already exists: $NGINX_SITE"
fi

echo ""
echo "=== Done ==="

#!/bin/bash
# Permanent fix: VPS firewall + nginx + admin on port 80.
# Run in Hostinger Browser Terminal:
#   cd /root/Cosmic-Lens-Backend && bash scripts/vps-permanent-access-fix.sh

set -euo pipefail

PUBLIC_IP="${PUBLIC_IP:-187.127.174.55}"
API_DOMAIN="${API_DOMAIN:-api.cosmiclens.app}"
ADMIN_ROOT="/var/www/cosmic-admin"
REPO="/root/Cosmic-Lens-Backend"

echo "=============================================="
echo " Cosmic Lens — permanent network + admin fix"
echo "=============================================="

echo ""
echo "=== 1) Local API (pm2) ==="
if curl -sf -m 5 "http://127.0.0.1:8080/api/healthz" >/dev/null; then
  echo "OK: cosmic-api on :8080"
else
  echo "FAIL: pm2 restart cosmic-api"
  pm2 restart cosmic-api --update-env || true
  sleep 3
  curl -sf -m 5 "http://127.0.0.1:8080/api/healthz" || exit 1
fi

echo ""
echo "=== 2) Admin static files ==="
if [ ! -f "$ADMIN_ROOT/index.html" ]; then
  echo "Copying admin dist -> $ADMIN_ROOT"
  mkdir -p "$ADMIN_ROOT"
  cp -a "$REPO/artifacts/admin-web/dist/." "$ADMIN_ROOT/"
  chown -R www-data:www-data "$ADMIN_ROOT"
  chmod -R a+rX "$ADMIN_ROOT"
fi
echo "OK: $ADMIN_ROOT/index.html"

echo ""
echo "=== 3) ufw (server firewall) ==="
if command -v ufw >/dev/null 2>&1; then
  ufw allow 22/tcp comment 'SSH' || true
  ufw allow 80/tcp comment 'HTTP admin+API' || true
  ufw allow 443/tcp comment 'HTTPS API' || true
  ufw allow 8080/tcp comment 'API direct' || true
  ufw --force enable 2>/dev/null || true
  ufw status numbered || true
else
  echo "ufw not installed (OK if Hostinger panel firewall is used)"
fi

echo ""
echo "=== 4) nginx — admin on IP :80 + API on ${API_DOMAIN} ==="
cat >/etc/nginx/sites-available/cosmic-api-ip <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _ ${PUBLIC_IP};

    root ${ADMIN_ROOT};
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
    }

    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

if [ -f /etc/nginx/sites-available/cosmic-api ]; then
  echo "Keeping existing ${API_DOMAIN} nginx site"
else
  cat >/etc/nginx/sites-available/cosmic-api <<EOF
server {
    listen 80;
    server_name ${API_DOMAIN};

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
    }
}
EOF
  ln -sf /etc/nginx/sites-available/cosmic-api /etc/nginx/sites-enabled/cosmic-api
fi

rm -f /etc/nginx/sites-enabled/cosmic-admin
rm -f /etc/nginx/sites-enabled/00-cosmic-admin
ln -sf /etc/nginx/sites-available/cosmic-api-ip /etc/nginx/sites-enabled/00-cosmic-api-ip

nginx -t
systemctl enable nginx
systemctl restart nginx

echo ""
echo "=== 5) Tests on VPS ==="
curl -sf -m 5 "http://127.0.0.1/api/healthz" && echo " :80 /api OK"
curl -sf -m 5 -o /dev/null -w "admin index HTTP %{http_code}\n" "http://127.0.0.1/"
curl -sf -m 5 -H "Host: ${API_DOMAIN}" "http://127.0.0.1/api/healthz" && echo " ${API_DOMAIN} via nginx OK" || true

echo ""
echo "=== 6) Public IP test FROM VPS ==="
if curl -sf -m 8 "http://${PUBLIC_IP}/api/healthz" >/dev/null; then
  echo "OK: public IP :80 reachable"
else
  echo "WARN: public IP :80 not reachable even from VPS loopback routing"
fi

echo ""
echo "=============================================="
echo " YOU MUST DO IN HOSTINGER hPanel (permanent):"
echo "=============================================="
echo "1. hPanel -> VPS -> your server -> Security -> Firewall"
echo "2. Add INBOUND rules (Accept):"
echo "     TCP 22   (SSH)"
echo "     TCP 80   (HTTP — admin + API)"
echo "     TCP 443  (HTTPS — api.cosmiclens.app)"
echo "3. Save. Wait 1-2 minutes."
echo ""
echo "4. DNS (domain registrar):"
echo "     A record  api.cosmiclens.app  ->  ${PUBLIC_IP}"
echo ""
echo "5. SSL on VPS (once DNS works):"
echo "     certbot --nginx -d ${API_DOMAIN}"
echo ""
echo " AFTER firewall + DNS:"
echo "   Admin browser:  http://${PUBLIC_IP}/"
echo "   API:            https://${API_DOMAIN}/api/healthz"
echo "   pnpm dev .env:  VITE_API_PROXY_TARGET=http://${PUBLIC_IP}"
echo "=============================================="

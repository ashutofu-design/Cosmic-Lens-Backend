#!/bin/bash
# Run on VPS — Cosmic Lens admin + Chocochat together (no conflict).
#
#   Chocochat  →  http://srv1708952.hstgr.cloud
#   Cosmic admin  →  http://187.127.174.55
#
# Usage:
#   cd /root/Cosmic-Lens-Backend && bash scripts/vps-nginx-cosmic-and-chocochat.sh

set -euo pipefail

PUBLIC_IP="${PUBLIC_IP:-187.127.174.55}"
HOSTNAME="${HOSTNAME:-srv1708952.hstgr.cloud}"
ADMIN_ROOT="/var/www/cosmic-admin"
CHOCOCHAT_PORT="${CHOCOCHAT_PORT:-8090}"
API_PORT="${API_PORT:-8080}"

echo "=== Cosmic admin + Chocochat nginx (split hostnames) ==="

mkdir -p "$ADMIN_ROOT"
if [ ! -f "$ADMIN_ROOT/index.html" ] && [ -f /root/Cosmic-Lens-Backend/artifacts/admin-web/dist/index.html ]; then
  cp -a /root/Cosmic-Lens-Backend/artifacts/admin-web/dist/. "$ADMIN_ROOT/"
  chown -R www-data:www-data "$ADMIN_ROOT"
  chmod -R a+rX "$ADMIN_ROOT"
fi

echo "=== 1) Chocochat (hostname only) ==="
cat >/etc/nginx/sites-available/chocochat <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${HOSTNAME};

    location / {
        proxy_pass http://127.0.0.1:${CHOCOCHAT_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
    }
}
EOF

echo "=== 2) Cosmic Lens admin + API (IP / default) ==="
cat >/etc/nginx/sites-available/cosmic-admin <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name ${PUBLIC_IP} _;

    root ${ADMIN_ROOT};
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:${API_PORT};
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

rm -f /etc/nginx/sites-enabled/cosmic-admin.bak
rm -f /etc/nginx/sites-enabled/chocochat.bak
rm -f /etc/nginx/sites-enabled/00-cosmic-api-ip
rm -f /etc/nginx/sites-enabled/cosmic-api-ip

ln -sf /etc/nginx/sites-available/chocochat /etc/nginx/sites-enabled/10-chocochat
ln -sf /etc/nginx/sites-available/cosmic-admin /etc/nginx/sites-enabled/20-cosmic-admin

# Keep api.cosmiclens.app HTTPS site if present (port 443 only — no :80 conflict)
if [ -f /etc/nginx/sites-available/cosmic-api ]; then
  ln -sf /etc/nginx/sites-available/cosmic-api /etc/nginx/sites-enabled/30-cosmic-api
fi

nginx -t
systemctl reload nginx

echo ""
echo "=== Tests ==="
curl -sf -m 5 -H "Host: ${HOSTNAME}" http://127.0.0.1/ >/dev/null && echo "Chocochat (${HOSTNAME}): OK" || echo "Chocochat: check pm2 chocochat-api on :${CHOCOCHAT_PORT}"
curl -sf -m 5 http://127.0.0.1/api/healthz && echo "Cosmic API (/api on IP): OK"
curl -sf -m 5 -o /dev/null -w "Cosmic admin (IP): HTTP %{http_code}\n" http://127.0.0.1/

echo ""
echo "DONE"
echo "  Chocochat:     http://${HOSTNAME}"
echo "  Cosmic admin:  http://${PUBLIC_IP}/"
echo "  pnpm dev .env: VITE_API_PROXY_TARGET=http://${PUBLIC_IP}"

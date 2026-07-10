#!/bin/bash
# Hostinger DNS only — serve admin + API on custom domain (no Cloudflare).
#
# Usage on VPS:
#   export ADMIN_DOMAIN=admin.coosmic.icu
#   export API_DOMAIN=api.coosmic.icu
#   cd /root/Cosmic-Lens-Backend && bash scripts/vps-nginx-coosmic-domain.sh

set -euo pipefail

PUBLIC_IP="${PUBLIC_IP:-187.127.174.55}"
ADMIN_DOMAIN="${ADMIN_DOMAIN:-admin.coosmic.icu}"
API_DOMAIN="${API_DOMAIN:-api.coosmic.icu}"
HOSTNAME="${HOSTNAME:-srv1708952.hstgr.cloud}"
ADMIN_ROOT="${ADMIN_ROOT:-/var/www/cosmic-admin}"
API_PORT="${API_PORT:-8080}"
CHOCOCHAT_PORT="${CHOCOCHAT_PORT:-8090}"
REPO="${REPO:-/root/Cosmic-Lens-Backend}"

echo "=== nginx: ${ADMIN_DOMAIN} + ${API_DOMAIN} ==="

mkdir -p "$ADMIN_ROOT"
if [ ! -f "$ADMIN_ROOT/index.html" ] && [ -f "$REPO/artifacts/admin-web/dist/index.html" ]; then
  cp -a "$REPO/artifacts/admin-web/dist/." "$ADMIN_ROOT/"
  chown -R www-data:www-data "$ADMIN_ROOT"
  chmod -R a+rX "$ADMIN_ROOT"
fi

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

cat >/etc/nginx/sites-available/cosmic-admin <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${ADMIN_DOMAIN};

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

cat >/etc/nginx/sites-available/cosmic-api-domain <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${API_DOMAIN};

    location / {
        proxy_pass http://127.0.0.1:${API_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
    }
}
EOF

cat >/etc/nginx/sites-available/cosmic-ip-fallback <<EOF
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

ln -sf /etc/nginx/sites-available/chocochat /etc/nginx/sites-enabled/10-chocochat
ln -sf /etc/nginx/sites-available/cosmic-admin /etc/nginx/sites-enabled/20-cosmic-admin
ln -sf /etc/nginx/sites-available/cosmic-api-domain /etc/nginx/sites-enabled/25-cosmic-api-domain
ln -sf /etc/nginx/sites-available/cosmic-ip-fallback /etc/nginx/sites-enabled/30-cosmic-ip-fallback

nginx -t
systemctl reload nginx

echo ""
echo "=== Tests (localhost) ==="
curl -sf -m 5 -H "Host: ${ADMIN_DOMAIN}" http://127.0.0.1/api/healthz && echo " ${ADMIN_DOMAIN} OK"
curl -sf -m 5 -H "Host: ${API_DOMAIN}" http://127.0.0.1/api/healthz && echo " ${API_DOMAIN} OK"

echo ""
echo "DONE"
echo "  Admin:  http://${ADMIN_DOMAIN}/"
echo "  API:    http://${API_DOMAIN}/api/healthz"

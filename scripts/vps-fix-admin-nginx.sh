#!/bin/bash
# Fix nginx: one port-80 server — admin UI at / + API proxy at /api/
# Paste in Hostinger Browser Terminal.

set -euo pipefail

REPO="/root/Cosmic-Lens-Backend"
ADMIN="$REPO/artifacts/admin-web"
PUBLIC_IP="${PUBLIC_IP:-187.127.174.55}"

ADMIN_SECRET=$(grep '^ADMIN_SECRET=' "$REPO/artifacts/api-server/.env" | cut -d= -f2- | tr -d '"' | tr -d "'")

echo "=== Rebuild admin (correct API base) ==="
cd "$REPO"
npm install -g pnpm 2>/dev/null || true
export VITE_API_BASE="http://${PUBLIC_IP}"
export VITE_ADMIN_SECRET="${ADMIN_SECRET}"
pnpm install
cd artifacts/admin-web
pnpm run build

echo "=== nginx: merge admin + API (single default_server) ==="
rm -f /etc/nginx/sites-enabled/cosmic-admin
rm -f /etc/nginx/sites-enabled/00-cosmic-admin

cat > /etc/nginx/sites-available/cosmic-api-ip <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _ ${PUBLIC_IP};

    root ${ADMIN}/dist;
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

ln -sf /etc/nginx/sites-available/cosmic-api-ip /etc/nginx/sites-enabled/00-cosmic-api-ip
nginx -t
systemctl reload nginx

echo ""
curl -sf -m 5 "http://127.0.0.1/api/healthz" && echo " API OK"
curl -sf -m 5 -o /dev/null -w "admin index HTTP %{http_code}\n" "http://127.0.0.1/"
echo ""
echo "DONE -> http://${PUBLIC_IP}/"

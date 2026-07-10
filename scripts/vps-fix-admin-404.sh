#!/bin/bash
# Fix admin 404: copy dist out of /root + nginx port 80.
# Paste in Hostinger Browser Terminal.

set -euo pipefail

PUBLIC_IP="${PUBLIC_IP:-187.127.174.55}"
SRC="/root/Cosmic-Lens-Backend/artifacts/admin-web/dist"
DEST="/var/www/cosmic-admin"

echo "=== Copy admin dist (nginx cannot read /root) ==="
mkdir -p "$DEST"
rm -rf "${DEST:?}"/*
cp -a "$SRC"/. "$DEST"/
chown -R www-data:www-data "$DEST"
chmod -R a+rX "$DEST"
ls -la "$DEST/index.html"

echo "=== nginx config ==="
cat >/etc/nginx/sites-available/cosmic-api-ip <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _ ${PUBLIC_IP};

    root ${DEST};
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

rm -f /etc/nginx/sites-enabled/cosmic-admin
rm -f /etc/nginx/sites-enabled/00-cosmic-admin
ln -sf /etc/nginx/sites-available/cosmic-api-ip /etc/nginx/sites-enabled/00-cosmic-api-ip

nginx -t
systemctl reload nginx

curl -sf -m 5 http://127.0.0.1/api/healthz && echo " API OK"
curl -sf -m 5 -o /dev/null -w "admin HTTP %{http_code}\n" http://127.0.0.1/
echo "Open: http://${PUBLIC_IP}/"

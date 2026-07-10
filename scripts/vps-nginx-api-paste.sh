#!/bin/bash
# Paste on VPS (already ssh'd in). Sets nginx :443 → API :8080
# Requires DNS: api.cosmiclens.app A → 187.127.174.55
set -euo pipefail

API_DOMAIN="${API_DOMAIN:-api.cosmiclens.app}"
PORT=8080

apt-get update -qq
apt-get install -y nginx certbot python3-certbot-nginx

cat > /etc/nginx/sites-available/cosmic-api <<EOF
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

ln -sf /etc/nginx/sites-available/cosmic-api /etc/nginx/sites-enabled/cosmic-api
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl reload nginx

echo "=== HTTP test (needs DNS first) ==="
curl -s -m 10 -H "Host: ${API_DOMAIN}" "http://127.0.0.1/api/healthz" || true

echo ""
echo "Next steps:"
echo "1. DNS A record: ${API_DOMAIN} → 187.127.174.55 (wait 5-30 min)"
echo "2. SSL: certbot --nginx -d ${API_DOMAIN}"
echo "3. Phone/laptop: curl https://${API_DOMAIN}/api/healthz"
echo "4. Mobile .env: EXPO_PUBLIC_API_URL=https://${API_DOMAIN} then Metro restart"

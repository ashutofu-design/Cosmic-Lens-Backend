#!/bin/bash
# VPS par paste karo — nginx port 80 se API expose (phone :8080 block bypass).
set -euo pipefail

cat > /etc/nginx/sites-available/cosmic-api-ip <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _ 187.127.174.55;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/cosmic-api-ip /etc/nginx/sites-enabled/00-cosmic-api-ip
nginx -t
systemctl reload nginx

echo "=== local :80 test ==="
curl -sf -m 5 "http://127.0.0.1/api/healthz" && echo

echo ""
echo "=== public IP :80 (from VPS) ==="
curl -sf -m 8 "http://187.127.174.55/api/healthz" && echo || echo "FAIL — Hostinger Firewall mein TCP 80 Allow karo"

echo ""
echo "Laptop se: curl -s http://187.127.174.55/api/healthz"
echo "Mobile .env: EXPO_PUBLIC_API_URL=http://187.127.174.55  (Metro restart)"

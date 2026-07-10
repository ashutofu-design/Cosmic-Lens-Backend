#!/bin/bash
# Paste in Hostinger Browser Terminal (VPS) — serve admin panel on port 80.
# Then open from laptop: http://187.127.174.55/
#
# Uses production cosmic-api on :8080 + real Postgres data.

set -euo pipefail

REPO="/root/Cosmic-Lens-Backend"
ADMIN="$REPO/artifacts/admin-web"
API_ENV="$REPO/artifacts/api-server/.env"
PUBLIC_IP="${PUBLIC_IP:-187.127.174.55}"

if [ ! -f "$API_ENV" ]; then
  echo "ERROR: missing $API_ENV"
  exit 1
fi

# shellcheck disable=SC1090
source <(grep -E '^ADMIN_SECRET=' "$API_ENV" | sed 's/^/export /')

if [ -z "${ADMIN_SECRET:-}" ]; then
  echo "ERROR: ADMIN_SECRET empty in $API_ENV"
  exit 1
fi

echo "=== 1) Build admin-web on VPS ==="
cd "$ADMIN"

if ! command -v pnpm >/dev/null 2>&1; then
  npm install -g pnpm 2>/dev/null || true
fi

cat > .env.build <<EOF
VITE_API_BASE=http://${PUBLIC_IP}
VITE_ADMIN_SECRET=${ADMIN_SECRET}
EOF

export VITE_API_BASE="http://${PUBLIC_IP}"
export VITE_ADMIN_SECRET="${ADMIN_SECRET}"

if [ -f package.json ]; then
  pnpm install 2>/dev/null || npm install
  pnpm run build 2>/dev/null || npm run build
else
  echo "ERROR: $ADMIN/package.json missing — git pull first"
  exit 1
fi

if [ ! -f dist/index.html ]; then
  echo "ERROR: build failed — dist/index.html missing"
  exit 1
fi

echo "=== 2) nginx — serve admin + proxy /api -> :8080 ==="
cat > /etc/nginx/sites-available/cosmic-admin <<EOF
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

ln -sf /etc/nginx/sites-available/cosmic-admin /etc/nginx/sites-enabled/00-cosmic-admin
nginx -t
systemctl reload nginx

echo ""
echo "=== 3) Test locally on VPS ==="
curl -sf -m 5 "http://127.0.0.1/api/healthz" && echo " API OK"
curl -sf -m 5 -o /dev/null -w "admin index HTTP %{http_code}\n" "http://127.0.0.1/"

echo ""
echo "DONE. Open in laptop browser:"
echo "  http://${PUBLIC_IP}/"
echo ""
echo "If timeout from laptop: Hostinger hPanel -> VPS -> Firewall -> Allow TCP 80"

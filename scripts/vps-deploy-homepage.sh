#!/bin/bash
# Build + deploy public homepage + admin SPA on VPS (paste in Hostinger Browser Terminal).
#   cd /root/Cosmic-Lens-Backend && bash scripts/vps-deploy-homepage.sh

set -euo pipefail

REPO="${REPO:-/root/Cosmic-Lens-Backend}"
ADMIN_ROOT="${ADMIN_ROOT:-/var/www/cosmic-admin}"

echo "=== Pull latest code ==="
cd "$REPO"
git pull --ff-only || git pull

echo "=== Build admin-web (homepage + /admin) ==="
cd "$REPO/artifacts/admin-web"
ADMIN_SECRET=$(grep '^ADMIN_SECRET=' ../api-server/.env | cut -d= -f2- | tr -d '"' | tr -d "'")
export VITE_API_BASE="${VITE_API_BASE:-https://api.coosmic.icu}"
export VITE_ADMIN_SECRET="$ADMIN_SECRET"
echo "[build] VITE_API_BASE=$VITE_API_BASE"

if command -v pnpm >/dev/null 2>&1; then
  pnpm run build
else
  npm run build
fi

test -f dist/index.html

echo "=== Deploy to ${ADMIN_ROOT} ==="
mkdir -p "$ADMIN_ROOT"
rm -rf "${ADMIN_ROOT:?}"/*
cp -a dist/. "$ADMIN_ROOT/"
chown -R www-data:www-data "$ADMIN_ROOT"
chmod -R a+rX "$ADMIN_ROOT"

echo ""
echo "DONE"
echo "  Homepage: https://admin.coosmic.icu/"
echo "  Admin:    https://admin.coosmic.icu/admin"
echo ""
echo "Phone: close tab completely, reopen https://admin.coosmic.icu/"

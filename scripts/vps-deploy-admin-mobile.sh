#!/bin/bash
# Build + deploy admin to /var/www/cosmic-admin (mobile-friendly build).
# Run on VPS Browser Terminal:
#   cd /root/Cosmic-Lens-Backend && bash scripts/vps-deploy-admin-mobile.sh

set -euo pipefail

REPO="${REPO:-/root/Cosmic-Lens-Backend}"
ADMIN_ROOT="${ADMIN_ROOT:-/var/www/cosmic-admin}"

cd "$REPO/artifacts/admin-web"
ADMIN_SECRET=$(grep '^ADMIN_SECRET=' ../api-server/.env | cut -d= -f2- | tr -d '"' | tr -d "'")
export VITE_API_BASE=""
export VITE_ADMIN_SECRET="$ADMIN_SECRET"

echo "=== Building admin (mobile layout) ==="
pnpm run build

echo "=== Deploying to ${ADMIN_ROOT} ==="
mkdir -p "$ADMIN_ROOT"
rm -rf "${ADMIN_ROOT:?}"/*
cp -a dist/. "$ADMIN_ROOT/"
chown -R www-data:www-data "$ADMIN_ROOT"
chmod -R a+rX "$ADMIN_ROOT"

echo ""
echo "DONE. On phone:"
echo "  1. Close admin tab completely"
echo "  2. Re-open https://admin.coosmic.icu"
echo "  3. You should see ☰ menu (no left icon sidebar)"

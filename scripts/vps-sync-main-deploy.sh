#!/bin/bash
# Sync repo to origin branch, restart API, rebuild admin SPA.
# Run on VPS:
#   cd /root/Cosmic-Lens-Backend && bash scripts/vps-sync-main-deploy.sh main

set -euo pipefail

BRANCH="${1:-main}"
REPO="${REPO:-/root/Cosmic-Lens-Backend}"

cd "$REPO"

cp -a artifacts/api-server/.env /tmp/cosmic-api-env.bak 2>/dev/null || true

git fetch origin
git reset --hard "origin/${BRANCH}"
git log -1 --oneline

test -f artifacts/api-server/instagram_answers.py || {
  echo "MISSING instagram_answers.py"
  exit 1
}

grep -q "Instagram Auto" artifacts/admin-web/src/App.tsx || {
  echo "MISSING Instagram Auto tab in App.tsx"
  exit 1
}

cd artifacts/api-server
find . -name '*.pyc' -delete
pm2 restart cosmic-api --update-env
sleep 5

cd "$REPO"
bash scripts/vps-deploy-admin-mobile.sh

if grep -rl "Instagram Auto" /var/www/cosmic-admin/assets/*.js 2>/dev/null | head -1; then
  echo "OK: Instagram Auto in built admin JS"
else
  echo "WARN: build OK but Instagram Auto string not found in JS (check tab label)"
fi

echo "VPS_DEPLOY_OK"

#!/bin/bash
# Emergency: API down (502) + admin build broken after git clean on VPS.
# Paste in Hostinger Browser Terminal:
#   cd /root/Cosmic-Lens-Backend && bash scripts/vps-emergency-restore-admin.sh

set -euo pipefail

REPO="${REPO:-/root/Cosmic-Lens-Backend}"
ADMIN_ROOT="${ADMIN_ROOT:-/var/www/cosmic-admin}"
BRANCH="${BRANCH:-main}"

cd "$REPO"

echo "=== 1) Sync code from GitHub (NO git clean) ==="
cp -a artifacts/api-server/.env /tmp/cosmic-api-env.bak 2>/dev/null || true
git fetch origin
git reset --hard "origin/${BRANCH}"
git log -1 --oneline

echo "=== 2) Check critical files ==="
MISS=0
for f in \
  artifacts/api-server/lifemap_admin_deliver.py \
  artifacts/api-server/support_chat.py \
  artifacts/api-server/instagram_answers.py \
  artifacts/admin-web/src/PalmistryAnalysisWorkspace.tsx \
  artifacts/admin-web/src/Router.tsx \
  artifacts/admin-web/src/site/PublicHomePage.tsx
do
  if [ -f "$f" ]; then
    echo "  OK $f"
  else
    echo "  MISSING $f"
    MISS=1
  fi
done
if [ "$MISS" -eq 1 ]; then
  echo ""
  echo "ERROR: GitHub main is missing files. On laptop run:"
  echo "  powershell -ExecutionPolicy Bypass -File .\\scripts\\deploy-admin-vps.ps1"
  echo "Then run this script again."
  exit 1
fi

echo "=== 3) Restart API ==="
cd "$REPO/artifacts/api-server"
find . -name '*.pyc' -delete
pm2 restart cosmic-api --update-env || pm2 start ./venv/bin/gunicorn --name cosmic-api -- -w 2 -b 127.0.0.1:8080 flask_app:app
sleep 6
pm2 status cosmic-api

echo "=== 4) API health (local) ==="
curl -sf -m 10 "http://127.0.0.1:8080/api/healthz" && echo " healthz OK" || {
  echo "healthz FAILED - last logs:"
  pm2 logs cosmic-api --lines 40 --nostream
  exit 1
}

echo "=== 5) Rebuild admin UI ==="
cd "$REPO"
bash scripts/vps-deploy-admin-mobile.sh

echo "=== 6) nginx reload ==="
nginx -t && systemctl reload nginx

echo "=== 7) Verify ==="
curl -sf -m 10 -o /dev/null -w "homepage HTTP %{http_code}\n" "http://127.0.0.1/"
grep -l "Instagram Answers" "$ADMIN_ROOT"/assets/*.js 2>/dev/null | head -1 || echo "WARN: Instagram string not in JS"

echo ""
echo "DONE"
echo "  Homepage: https://admin.coosmic.icu/"
echo "  Admin unlock: https://admin.coosmic.icu/help-support  (tap sequence, then /admin)"
echo "  Admin: https://admin.coosmic.icu/admin"

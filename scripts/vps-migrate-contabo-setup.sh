#!/bin/bash
# STEP 2 — Run on NEW Contabo VPS (Ubuntu 22.04) after order + SSH login.
#
#   export CONTABO_PUBLIC_IP=<your-new-ip>
#   export ADMIN_DOMAIN=admin.coosmic.icu
#   export API_DOMAIN=api.coosmic.icu
#   cd /root/Cosmic-Lens-Backend && bash scripts/vps-migrate-contabo-setup.sh
#
# BEFORE running: upload backup from laptop:
#   scp -r C:\\Users\\HP\\Downloads\\cosmic-migration-backup root@NEW_IP:/root/

set -euo pipefail

REPO="${REPO:-/root/Cosmic-Lens-Backend}"
BACKUP_DIR="${BACKUP_DIR:-/root/cosmic-migration-backup}"
API_PORT="${API_PORT:-8080}"
ADMIN_ROOT="${ADMIN_ROOT:-/var/www/cosmic-admin}"
PUBLIC_IP="${CONTABO_PUBLIC_IP:-$(curl -4 -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')}"

echo "=== Contabo setup for Cosmic Lens ==="
echo "Public IP: $PUBLIC_IP"

# ── System packages ─────────────────────────────────────────────────────────
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
  git nginx certbot python3-certbot-nginx \
  postgresql postgresql-contrib redis-server \
  python3-venv python3-pip build-essential \
  libpq-dev curl ca-certificates

if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y -qq nodejs
fi
npm install -g pnpm pm2 2>/dev/null || true

# ── Firewall ────────────────────────────────────────────────────────────────
if command -v ufw >/dev/null 2>&1; then
  ufw allow OpenSSH
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw --force enable || true
fi

# ── Repo ────────────────────────────────────────────────────────────────────
if [ ! -d "$REPO/.git" ]; then
  git clone https://github.com/ashutofu-design/Cosmic-Lens-Backend.git "$REPO"
fi
cd "$REPO"
git fetch origin
git reset --hard origin/main
git log -1 --oneline

# ── Python venv ─────────────────────────────────────────────────────────────
cd "$REPO/artifacts/api-server"
python3 -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

# ── Restore secrets from backup ─────────────────────────────────────────────
if [ -f "$BACKUP_DIR/api-server.env" ]; then
  cp "$BACKUP_DIR/api-server.env" "$REPO/artifacts/api-server/.env"
  chmod 600 "$REPO/artifacts/api-server/.env"
  echo "OK: restored .env"
else
  echo "ERROR: missing $BACKUP_DIR/api-server.env — upload backup first"
  exit 1
fi

if [ -f "$BACKUP_DIR/firebase-key.json" ]; then
  cp "$BACKUP_DIR/firebase-key.json" /root/firebase-key.json
  chmod 600 /root/firebase-key.json
  echo "OK: restored firebase-key.json"
fi

# ── PostgreSQL restore ──────────────────────────────────────────────────────
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='cosmiclens'" | grep -q 1 \
  || sudo -u postgres createdb cosmiclens

DUMP="$(ls -1t "$BACKUP_DIR"/cosmiclens_*.dump 2>/dev/null | head -1 || true)"
if [ -n "$DUMP" ]; then
  echo ">>> Restoring $DUMP ..."
  pg_restore -U postgres -d cosmiclens --clean --if-exists "$DUMP" 2>/dev/null \
    || sudo -u postgres pg_restore -d cosmiclens --clean --if-exists "$DUMP"
  echo "OK: database restored"
else
  echo "WARN: no dump found — fresh empty DB (tables created on first API start)"
fi

# Ensure DATABASE_URL in .env points to local postgres
if ! grep -q '^DATABASE_URL=' "$REPO/artifacts/api-server/.env"; then
  echo 'DATABASE_URL=postgresql://postgres@localhost:5432/cosmiclens' >> "$REPO/artifacts/api-server/.env"
fi

# ── PM2 API ─────────────────────────────────────────────────────────────────
cd "$REPO/artifacts/api-server"
pm2 delete cosmic-api 2>/dev/null || true
PROD=1 PORT="$API_PORT" pm2 start ./start.sh --name cosmic-api --interpreter bash
pm2 save
pm2 startup systemd -u root --hp /root 2>/dev/null || true

sleep 5
curl -sf "http://127.0.0.1:${API_PORT}/api/healthz" && echo " API healthz OK" || {
  echo "ERROR: API not healthy — check: pm2 logs cosmic-api --lines 40"
  exit 1
}

# ── nginx + domains ─────────────────────────────────────────────────────────
cd "$REPO"
export PUBLIC_IP ADMIN_DOMAIN="${ADMIN_DOMAIN:-admin.coosmic.icu}" API_DOMAIN="${API_DOMAIN:-api.coosmic.icu}"
bash scripts/vps-nginx-coosmic-domain.sh

# ── Admin build ─────────────────────────────────────────────────────────────
bash scripts/vps-deploy-admin-mobile.sh

echo ""
echo "=== Contabo setup DONE (DNS not switched yet) ==="
echo "Test with NEW IP before DNS cutover:"
echo "  curl http://${PUBLIC_IP}/api/healthz"
echo ""
echo "Next: point DNS A records to ${PUBLIC_IP}"
echo "  admin.coosmic.icu  -> ${PUBLIC_IP}"
echo "  api.coosmic.icu    -> ${PUBLIC_IP}"
echo "Then: certbot --nginx -d admin.coosmic.icu -d api.coosmic.icu"
echo ""
echo "Laptop deploy:"
echo "  \$env:VPS_HOST = \"root@${PUBLIC_IP}\""

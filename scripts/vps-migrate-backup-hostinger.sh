#!/bin/bash
# STEP 1 — Run on OLD Hostinger VPS before migration.
#   cd /root/Cosmic-Lens-Backend && bash scripts/vps-migrate-backup-hostinger.sh
#
# Creates /root/cosmic-migration-backup/ — download this folder to your laptop.

set -euo pipefail

REPO="${REPO:-/root/Cosmic-Lens-Backend}"
BACKUP_DIR="/root/cosmic-migration-backup"
STAMP="$(date +%Y%m%d-%H%M)"

mkdir -p "$BACKUP_DIR"

echo "=== Cosmic Lens migration backup ($STAMP) ==="

# 1) PostgreSQL
echo ">>> PostgreSQL dump..."
if command -v pg_dump >/dev/null 2>&1; then
  sudo -u postgres pg_dump -Fc cosmiclens -f "$BACKUP_DIR/cosmiclens_${STAMP}.dump" \
    || pg_dump -U postgres -Fc cosmiclens -f "$BACKUP_DIR/cosmiclens_${STAMP}.dump"
  echo "OK: $BACKUP_DIR/cosmiclens_${STAMP}.dump"
else
  echo "WARN: pg_dump not found — export DB manually"
fi

# 2) Secrets
echo ">>> .env + firebase..."
cp "$REPO/artifacts/api-server/.env" "$BACKUP_DIR/api-server.env"
chmod 600 "$BACKUP_DIR/api-server.env"
if [ -f /root/firebase-key.json ]; then
  cp /root/firebase-key.json "$BACKUP_DIR/firebase-key.json"
  chmod 600 "$BACKUP_DIR/firebase-key.json"
fi

# 3) Admin static (optional — can rebuild on Contabo)
if [ -d /var/www/cosmic-admin ]; then
  echo ">>> Admin static tarball..."
  tar -czf "$BACKUP_DIR/cosmic-admin_${STAMP}.tar.gz" -C /var/www cosmic-admin
fi

# 4) PM2 + nginx reference
pm2 list > "$BACKUP_DIR/pm2-list.txt" 2>/dev/null || true
pm2 save 2>/dev/null || true
cp /etc/nginx/sites-enabled/* "$BACKUP_DIR/" 2>/dev/null || true

# 5) Manifest
cat > "$BACKUP_DIR/README.txt" <<EOF
Cosmic Lens Hostinger backup — $STAMP
Download entire folder to laptop:
  scp -r root@187.127.174.55:/root/cosmic-migration-backup .

Files:
  - cosmiclens_*.dump     PostgreSQL (users, orders, ask history)
  - api-server.env        All API secrets (OPENAI, Razorpay, etc.)
  - firebase-key.json     Firebase Admin SDK
  - cosmic-admin_*.tar.gz   Optional admin UI copy
EOF

ls -lah "$BACKUP_DIR"
echo ""
echo "DONE. Download to laptop:"
echo "  scp -r root@187.127.174.55:/root/cosmic-migration-backup C:\\Users\\HP\\Downloads\\"
echo ""
echo "Keep Hostinger running until Contabo is verified."

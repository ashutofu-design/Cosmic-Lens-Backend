#!/bin/bash
# Production launcher for PM2 / systemd (Flask + gunicorn on :8080).
# Firebase key: /root/firebase-key.json (override with FIREBASE_CREDENTIALS_PATH).
set -e
cd "$(dirname "$0")"
if [ -f venv/bin/activate ]; then
  # shellcheck source=/dev/null
  source venv/bin/activate
fi
export PROD=1
export PORT="${PORT:-8080}"
exec ./start.sh

#!/bin/bash
# Cosmic Lens API server starter.
#
#   PROD=1            → gunicorn (production WSGI), 4 workers, gthread
#   default           → Flask dev server (local/Replit dev with debug-friendly errors)
#
# PORT env honored (defaults to 8080).
set -e

PORT="${PORT:-8080}"
# Research-mode bump: lift the anon IP-based daily limit so the
# diagnostic harness (/tmp/research/) can run wide test batches
# without tripping the 402 quota gate. Production deploys override
# via env if needed.
export ANON_DAILY_LIMIT="${ANON_DAILY_LIMIT:-2000}"

# Auto-load Firebase Admin credentials when not already in the environment.
# Priority: FIREBASE_SERVICE_ACCOUNT_JSON → FIREBASE_CREDENTIALS_PATH →
#           /root/firebase-key.json → ./firebase-key.json
if [ -z "${FIREBASE_SERVICE_ACCOUNT_JSON:-}" ]; then
  _FB_KEY=""
  if [ -n "${FIREBASE_CREDENTIALS_PATH:-}" ] && [ -f "${FIREBASE_CREDENTIALS_PATH}" ]; then
    _FB_KEY="${FIREBASE_CREDENTIALS_PATH}"
  elif [ -f "/root/firebase-key.json" ]; then
    _FB_KEY="/root/firebase-key.json"
  elif [ -f "$(dirname "$0")/firebase-key.json" ]; then
    _FB_KEY="$(dirname "$0")/firebase-key.json"
  fi
  if [ -n "$_FB_KEY" ]; then
    export FIREBASE_SERVICE_ACCOUNT_JSON="$(
      python3 -c 'import json, sys; print(json.dumps(json.load(open(sys.argv[1]))))' "$_FB_KEY"
    )"
    echo "[start] Firebase credentials loaded from $_FB_KEY"
  fi
fi

if [ "${PROD:-0}" = "1" ]; then
  echo "[start] PROD=1 → starting gunicorn on :$PORT"
  exec gunicorn \
    --workers "${GUNICORN_WORKERS:-4}" \
    --threads "${GUNICORN_THREADS:-2}" \
    --worker-class gthread \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --bind "0.0.0.0:$PORT" \
    --access-logfile - \
    --error-logfile - \
    flask_app:app
else
  echo "[start] dev mode → Flask dev server on :$PORT (set PROD=1 for gunicorn)"
  exec python3 flask_app.py
fi

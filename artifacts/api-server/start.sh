#!/bin/bash
# Cosmic Lens API server starter.
#
#   PROD=1            → gunicorn (production WSGI), 4 workers, gthread
#   default           → Flask dev server (local/Replit dev with debug-friendly errors)
#
# PORT env honored (defaults to 8080).
set -e

PORT="${PORT:-8080}"

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

#!/bin/bash
# Start Flask API + localtunnel together. localtunnel exposes the API at
# https://cosmiclens-api.loca.lt — a CDN-fronted URL that works on
# Indian cellular carriers (Jio/Airtel) which block *.kirk.replit.dev.

set -e

PORT="${PORT:-8080}"
SUBDOMAIN="cosmiclens-api"

cleanup() {
  echo "[start.sh] shutting down…"
  [ -n "$LT_PID" ] && kill "$LT_PID" 2>/dev/null || true
  [ -n "$FLASK_PID" ] && kill "$FLASK_PID" 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Start Flask in the background.
python3 flask_app.py &
FLASK_PID=$!

# Wait for Flask to bind.
for i in $(seq 1 20); do
  if curl -sf -m 1 "http://127.0.0.1:$PORT/api/healthz" >/dev/null 2>&1; then
    echo "[start.sh] Flask ready on :$PORT"
    break
  fi
  sleep 0.5
done

# Start localtunnel in the background, with auto-reconnect on crash.
(
  while true; do
    echo "[start.sh] starting localtunnel → $SUBDOMAIN.loca.lt"
    lt --port "$PORT" --subdomain "$SUBDOMAIN" 2>&1 | sed 's/^/[lt] /'
    echo "[start.sh] localtunnel exited; retrying in 3s"
    sleep 3
  done
) &
LT_PID=$!

echo "================================================="
echo " API local:  http://localhost:$PORT"
echo " API public: https://$SUBDOMAIN.loca.lt   (works on cellular)"
echo "================================================="

# Wait for Flask to exit, which will trigger cleanup via trap.
wait "$FLASK_PID"

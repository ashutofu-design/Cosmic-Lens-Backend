#!/bin/bash
# Hard-restart cosmic-api on VPS so gunicorn reloads flask_app + ask_scope_gate.
set -euo pipefail

API_DIR="${API_DIR:-/root/Cosmic-Lens-Backend/artifacts/api-server}"
PM2_NAME="${PM2_NAME:-cosmic-api}"

cd "$API_DIR"

echo "=== verify greeting code on disk ==="
grep -n "greeting_shortcut_response" flask_app.py ask_scope_gate.py | head -5
python3 -c "from ask_scope_gate import greeting_shortcut_response as g; print('probe:', g('hi hello','hi')['source'])"

echo "=== clear pyc cache ==="
find "$API_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$API_DIR" -name '*.pyc' -delete 2>/dev/null || true

echo "=== stop pm2 + kill stale gunicorn ==="
pm2 stop "$PM2_NAME" 2>/dev/null || true
sleep 2
pkill -f "gunicorn.*flask_app" 2>/dev/null || true
sleep 1

echo "=== start pm2 ==="
pm2 start "$PM2_NAME" 2>/dev/null || pm2 restart "$PM2_NAME" --update-env
sleep 5

echo "=== curl test ==="
curl -s -X POST "http://127.0.0.1:8080/api/ask/stream" \
  -H "Content-Type: application/json" \
  -d '{"question":"hi hello","lang":"hi"}'
echo

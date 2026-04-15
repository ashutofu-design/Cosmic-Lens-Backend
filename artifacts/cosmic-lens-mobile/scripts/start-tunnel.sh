#!/bin/bash
TUNNEL_URL_FILE="/tmp/expo-tunnel-url"
LOG_FILE="/tmp/expo-raw.log"
LT_LOG="/tmp/lt-api.log"
LT_METRO_LOG="/tmp/lt-metro.log"

> "$TUNNEL_URL_FILE"
> "$LOG_FILE"
> "$LT_LOG"
> "$LT_METRO_LOG"

# Kill any stale tunnel processes from a previous run
pkill -f "lt --port" 2>/dev/null || true
pkill -f "ngrok"     2>/dev/null || true
sleep 2

# ── Step 1: Start localtunnel for Flask API (port 8080) ──────────────────────
echo "[tunnel] Starting public API tunnel on port 8080..."
lt --port 8080 > "$LT_LOG" 2>&1 &
LT_PID=$!

FLASK_API_HOST=""
for i in $(seq 1 20); do
  if grep -q "your url is:" "$LT_LOG" 2>/dev/null; then
    LT_URL=$(grep "your url is:" "$LT_LOG" | grep -oE 'https://[^[:space:]]+' | head -1)
    FLASK_API_HOST=$(echo "$LT_URL" | sed 's|https://||')
    echo "[tunnel] Flask API public URL: $LT_URL"
    break
  fi
  sleep 1
done

if [ -z "$FLASK_API_HOST" ]; then
  echo "[tunnel] WARNING: localtunnel failed, falling back to Replit dev domain"
  FLASK_API_HOST="${REPLIT_DEV_DOMAIN}"
fi

export EXPO_PUBLIC_DOMAIN="$FLASK_API_HOST"
echo "[tunnel] EXPO_PUBLIC_DOMAIN set to: $EXPO_PUBLIC_DOMAIN"

# ── Step 2: Start Metro in LAN/localhost mode ─────────────────────────────────
METRO_PORT="${PORT:-18987}"
echo "[tunnel] Starting Metro on port $METRO_PORT (localhost mode)..."
pnpm exec expo start --localhost --port "$METRO_PORT" --clear 2>&1 > "$LOG_FILE" &
METRO_PID=$!

# Wait for Metro to be ready
echo "[tunnel] Waiting for Metro bundler to start..."
for i in $(seq 1 30); do
  if grep -qE "Metro waiting on|Bundled [0-9]" "$LOG_FILE" 2>/dev/null; then
    echo "[tunnel] Metro is ready"
    break
  fi
  sleep 2
done

# ── Step 3: Start localtunnel for Metro (port 18987) ─────────────────────────
echo "[tunnel] Starting public Metro tunnel on port $METRO_PORT..."
lt --port "$METRO_PORT" > "$LT_METRO_LOG" 2>&1 &
LT_METRO_PID=$!

METRO_PUBLIC_HOST=""
for i in $(seq 1 20); do
  if grep -q "your url is:" "$LT_METRO_LOG" 2>/dev/null; then
    METRO_LT_URL=$(grep "your url is:" "$LT_METRO_LOG" | grep -oE 'https://[^[:space:]]+' | head -1)
    METRO_PUBLIC_HOST=$(echo "$METRO_LT_URL" | sed 's|https://||')
    echo "[tunnel] Metro public URL: $METRO_LT_URL"
    break
  fi
  sleep 1
done

# ── Step 4: Construct exp:// URL and show QR ─────────────────────────────────
if [ -n "$METRO_PUBLIC_HOST" ]; then
  EXPO_URL="exp://${METRO_PUBLIC_HOST}"
else
  # Fallback: use Replit dev domain
  EXPO_URL="exp://${REPLIT_DEV_DOMAIN}"
  echo "[tunnel] WARNING: Metro localtunnel failed, using Replit dev domain"
fi

echo "$EXPO_URL" > "$TUNNEL_URL_FILE"
echo ""
echo "================================================="
echo " EXPO GO:  $EXPO_URL"
echo " API BASE: https://$EXPO_PUBLIC_DOMAIN"
echo " QR PAGE:  https://${REPLIT_DEV_DOMAIN}/qr"
echo "================================================="

cleanup() {
  kill "$METRO_PID" "$LT_METRO_PID" "$LT_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Keep alive
wait "$METRO_PID"

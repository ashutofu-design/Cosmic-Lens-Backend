#!/bin/bash
TUNNEL_URL_FILE="/tmp/expo-tunnel-url"
LOG_FILE="/tmp/expo-raw.log"
LT_LOG="/tmp/lt-api.log"

> "$TUNNEL_URL_FILE"
> "$LOG_FILE"
> "$LT_LOG"

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

# ── Step 2: Start Metro with --tunnel (uses @expo/ngrok) ─────────────────────
METRO_PORT="${PORT:-18987}"
echo "[tunnel] Starting Metro on port $METRO_PORT with --tunnel mode..."
pnpm exec expo start --tunnel --port "$METRO_PORT" --clear 2>&1 | tee "$LOG_FILE" &
METRO_PID=$!

echo "[tunnel] Waiting for Metro tunnel to establish..."
EXPO_URL=""
for i in $(seq 1 60); do
  if grep -qoE 'exp://[a-zA-Z0-9._-]+' "$LOG_FILE" 2>/dev/null; then
    EXPO_URL=$(grep -oE 'exp://[a-zA-Z0-9._-]+' "$LOG_FILE" | head -1)
    echo "[tunnel] Metro tunnel ready: $EXPO_URL"
    break
  fi
  sleep 2
done

if [ -z "$EXPO_URL" ]; then
  echo "[tunnel] WARNING: Could not detect tunnel URL, check Metro logs"
  EXPO_URL="exp://${REPLIT_DEV_DOMAIN}"
fi

echo "$EXPO_URL" > "$TUNNEL_URL_FILE"
echo ""
echo "================================================="
echo " EXPO GO:  $EXPO_URL"
echo " API BASE: https://$EXPO_PUBLIC_DOMAIN"
echo " QR PAGE:  https://${REPLIT_DEV_DOMAIN}/qr"
echo "================================================="

cleanup() {
  kill "$METRO_PID" "$LT_PID" 2>/dev/null || true
}
trap cleanup EXIT

wait "$METRO_PID"

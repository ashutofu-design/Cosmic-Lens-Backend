#!/bin/bash
TUNNEL_URL_FILE="/tmp/expo-tunnel-url"
LOG_FILE="/tmp/expo-raw.log"
LT_LOG="/tmp/lt-api.log"

> "$TUNNEL_URL_FILE"
> "$LOG_FILE"
> "$LT_LOG"

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

# Override EXPO_PUBLIC_DOMAIN with the public Flask API host
export EXPO_PUBLIC_DOMAIN="$FLASK_API_HOST"
echo "[tunnel] EXPO_PUBLIC_DOMAIN set to: $EXPO_PUBLIC_DOMAIN"

# ── Step 2: Watch for Expo tunnel URL ────────────────────────────────────────
(tail -f "$LOG_FILE" | while IFS= read -r line; do
  if echo "$line" | grep -q "Metro waiting on exp://"; then
    URL=$(echo "$line" | grep -oE 'exp://[^[:space:]]+')
    if [ -n "$URL" ]; then
      echo "$URL" > "$TUNNEL_URL_FILE"
      echo ""
      echo "================================================="
      echo " EXPO GO:  $URL"
      echo " API BASE: https://$EXPO_PUBLIC_DOMAIN"
      echo " QR PAGE:  https://${REPLIT_DEV_DOMAIN}/qr"
      echo "================================================="
    fi
  fi
done) &
WATCHER_PID=$!

cleanup() {
  kill "$WATCHER_PID" "$LT_PID" 2>/dev/null || true
}
trap cleanup EXIT

# ── Step 3: Start Expo with ngrok tunnel (clears cache so new domain bakes in)
pnpm exec expo start --tunnel --clear --port "${PORT:-18987}" 2>&1 | tee -a "$LOG_FILE"

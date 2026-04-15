#!/bin/bash
TUNNEL_URL_FILE="/tmp/expo-tunnel-url"
LOG_FILE="/tmp/expo-raw.log"

> "$TUNNEL_URL_FILE"
> "$LOG_FILE"

# Watch log in background and extract tunnel URL
(tail -f "$LOG_FILE" | while IFS= read -r line; do
  if echo "$line" | grep -q "Metro waiting on exp://"; then
    URL=$(echo "$line" | grep -oE 'exp://[^[:space:]]+')
    if [ -n "$URL" ]; then
      echo "$URL" > "$TUNNEL_URL_FILE"
      echo ""
      echo "================================================="
      echo " EXPO GO:  $URL"
      echo " QR PAGE:  https://${REPLIT_DEV_DOMAIN}/qr"
      echo "================================================="
      echo ""
    fi
  fi
done) &
WATCHER_PID=$!

cleanup() {
  kill "$WATCHER_PID" 2>/dev/null || true
}
trap cleanup EXIT

pnpm exec expo start --tunnel --port "${PORT:-18987}" 2>&1 | tee -a "$LOG_FILE"

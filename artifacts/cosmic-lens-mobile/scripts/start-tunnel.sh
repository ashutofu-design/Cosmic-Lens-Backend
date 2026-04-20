#!/bin/bash
TUNNEL_URL_FILE="/tmp/expo-tunnel-url"
LOG_FILE="/tmp/expo-raw.log"
LT_API_LOG="/tmp/lt-api.log"

> "$TUNNEL_URL_FILE"
> "$LOG_FILE"
> "$LT_API_LOG"

# --- API localtunnel (port 8080) ---
# The kirk.replit.dev domain is blocked on Indian cellular (Jio/Airtel),
# so we expose the API via localtunnel for cellular reachability.
API_PORT=8080
API_SUB="cosmiclens-api"
pkill -f "lt --port ${API_PORT}" 2>/dev/null || true
sleep 1

(
  while true; do
    echo "[lt-api] starting tunnel attempt"
    lt --port "${API_PORT}" --subdomain "${API_SUB}" 2>&1 | tee -a "$LT_API_LOG" | sed 's/^/[lt-api] /'
    echo "[lt-api] exited; retrying in 3s" | tee -a "$LT_API_LOG"
    sleep 3
  done
) &
LT_API_PID=$!

PUBLIC_API_URL=""
for i in $(seq 1 20); do
  URL=$(grep -oE 'https://[a-z0-9-]+\.loca\.lt' "$LT_API_LOG" 2>/dev/null | tail -1)
  if [ -n "$URL" ]; then
    if curl -sf -m 3 -H "bypass-tunnel-reminder: true" "$URL/" >/dev/null 2>&1 \
       || curl -sf -m 3 -H "bypass-tunnel-reminder: true" "$URL/api/health" >/dev/null 2>&1; then
      PUBLIC_API_URL="$URL"
      echo "[startup] API tunnel READY: $PUBLIC_API_URL"
      break
    fi
  fi
  sleep 2
done

if [ -z "$PUBLIC_API_URL" ]; then
  PUBLIC_API_URL="https://${API_SUB}.loca.lt"
  echo "[startup] API tunnel health-check failed; using default: $PUBLIC_API_URL"
fi

export EXPO_PUBLIC_API_URL="$PUBLIC_API_URL"
echo "[startup] EXPO_PUBLIC_API_URL=$EXPO_PUBLIC_API_URL"

# --- Metro served via Replit's built-in Expo dev domain ---
# Replit provides a stable HTTPS proxy (REPLIT_EXPO_DEV_DOMAIN) for Metro
# that doesn't require any third-party tunnel. This is far more reliable
# than localtunnel/ngrok which keep failing.
METRO_PORT="${PORT:-18987}"

if [ -n "$REPLIT_EXPO_DEV_DOMAIN" ]; then
  METRO_HOST="$REPLIT_EXPO_DEV_DOMAIN"
elif [ -n "$REPLIT_DEV_DOMAIN" ]; then
  METRO_HOST="$REPLIT_DEV_DOMAIN"
else
  METRO_HOST="localhost:$METRO_PORT"
fi
METRO_PUBLIC_URL="https://$METRO_HOST"

export REACT_NATIVE_PACKAGER_HOSTNAME="$METRO_HOST"
export EXPO_PACKAGER_PROXY_URL="$METRO_PUBLIC_URL"
export EXPO_MANIFEST_PROXY_URL="$METRO_PUBLIC_URL"

echo "[startup] Starting Metro on port $METRO_PORT (public host: $METRO_HOST)..."
pnpm exec expo start --port "$METRO_PORT" --clear 2>&1 | tee "$LOG_FILE" &
METRO_PID=$!

# Wait for Metro to bind locally.
for i in $(seq 1 60); do
  if curl -sf -m 2 "http://localhost:$METRO_PORT/status" >/dev/null 2>&1; then
    echo "[startup] Metro local port up."
    break
  fi
  sleep 1
done

# Verify the public tunnel actually serves Metro.
for i in $(seq 1 20); do
  if curl -sf -m 5 "$METRO_PUBLIC_URL/status" 2>/dev/null \
       | grep -q "packager-status:running"; then
    echo "[startup] Metro public URL READY: $METRO_PUBLIC_URL"
    break
  fi
  sleep 2
done

EXPO_URL="exp://$METRO_HOST"
echo "$EXPO_URL" > "$TUNNEL_URL_FILE"

echo ""
echo "================================================="
echo " EXPO GO:  $EXPO_URL"
echo " API:      $PUBLIC_API_URL"
echo "================================================="

cleanup() {
  kill "$METRO_PID" 2>/dev/null || true
  [ -n "$LT_API_PID" ] && kill "$LT_API_PID" 2>/dev/null || true
}
trap cleanup EXIT

wait "$METRO_PID"

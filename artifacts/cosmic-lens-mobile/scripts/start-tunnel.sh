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

# --- Metro tunnel via Expo's built-in ngrok (--tunnel) ---
# This produces "exp://<hash>-<user>-<port>.exp.direct" URLs that open
# DIRECTLY in Expo Go — no localtunnel "click to continue" interstitial.
METRO_PORT="${PORT:-18987}"

# Configure ngrok authtoken if provided (some versions require it; older
# @expo/ngrok bundle works anonymously).
if [ -n "$NGROK_AUTHTOKEN" ]; then
  mkdir -p ~/.config/ngrok
  if [ ! -f ~/.config/ngrok/ngrok.yml ] || ! grep -q "authtoken:" ~/.config/ngrok/ngrok.yml 2>/dev/null; then
    echo "version: 2" > ~/.config/ngrok/ngrok.yml
    echo "authtoken: $NGROK_AUTHTOKEN" >> ~/.config/ngrok/ngrok.yml
    echo "[startup] Wrote ngrok authtoken config"
  fi
fi

echo "[startup] Starting Metro on port $METRO_PORT with --tunnel (ngrok / exp.direct)..."
# NOTE: --tunnel is incompatible with --offline (tunnel needs the manifest server)
pnpm exec expo start --port "$METRO_PORT" --clear --tunnel 2>&1 | tee "$LOG_FILE" &
METRO_PID=$!

# Wait for local Metro
for i in $(seq 1 60); do
  if curl -sf -m 2 "http://localhost:$METRO_PORT/status" >/dev/null 2>&1; then
    echo "[startup] Metro local port up."
    break
  fi
  sleep 1
done

# Wait for the tunnel URL to appear in the Expo CLI log
EXPO_URL=""
for i in $(seq 1 60); do
  EXPO_URL=$(grep -oE 'exp://[a-z0-9-]+\.exp\.direct(:[0-9]+)?' "$LOG_FILE" 2>/dev/null | tail -1)
  if [ -n "$EXPO_URL" ]; then
    break
  fi
  sleep 2
done

if [ -z "$EXPO_URL" ]; then
  echo "[startup] WARNING: --tunnel URL not detected in Expo logs."
  echo "[startup] Last 30 lines of Expo log:"
  tail -30 "$LOG_FILE"
  EXPO_URL="exp://localhost:$METRO_PORT"
fi

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

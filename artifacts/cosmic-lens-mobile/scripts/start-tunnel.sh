#!/bin/bash
TUNNEL_URL_FILE="/tmp/expo-tunnel-url"
LOG_FILE="/tmp/expo-raw.log"

> "$TUNNEL_URL_FILE"
> "$LOG_FILE"

pkill -f "ngrok" 2>/dev/null || true
sleep 1

REPLIT_API_DOMAIN="${REPLIT_DEV_DOMAIN}"
export EXPO_PUBLIC_DOMAIN="$REPLIT_API_DOMAIN"
echo "[startup] API accessible at: https://$REPLIT_API_DOMAIN"
echo "[startup] No external tunnel needed — using stable Replit domain"

METRO_PORT="${PORT:-18987}"
echo "[startup] Starting Metro on port $METRO_PORT with --tunnel mode..."
pnpm exec expo start --tunnel --port "$METRO_PORT" --clear 2>&1 | tee "$LOG_FILE" &
METRO_PID=$!

echo "[startup] Waiting for Metro tunnel to establish..."
EXPO_URL=""
for i in $(seq 1 45); do
  if curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -qo '"public_url"'; then
    EXPO_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  for t in d.get('tunnels',[]):
    if 'https' in t.get('public_url',''):
      print('exp://' + t['public_url'].replace('https://',''))
      break
except: pass
" 2>/dev/null)
    if [ -n "$EXPO_URL" ]; then
      echo "[startup] Metro tunnel ready: $EXPO_URL"
      break
    fi
  fi
  sleep 2
done

if [ -z "$EXPO_URL" ]; then
  echo "[startup] Tunnel failed — restarting Metro in --tunnel mode (retry)..."
  kill "$METRO_PID" 2>/dev/null || true
  sleep 2
  pnpm exec expo start --tunnel --port "$METRO_PORT" 2>&1 | tee "$LOG_FILE" &
  METRO_PID=$!

  for i in $(seq 1 45); do
    if curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -qo '"public_url"'; then
      EXPO_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  for t in d.get('tunnels',[]):
    if 'https' in t.get('public_url',''):
      print('exp://' + t['public_url'].replace('https://',''))
      break
except: pass
" 2>/dev/null)
      if [ -n "$EXPO_URL" ]; then
        echo "[startup] Metro tunnel ready (retry): $EXPO_URL"
        break
      fi
    fi
    sleep 2
  done
fi

if [ -z "$EXPO_URL" ]; then
  EXPO_URL="exp://${REPLIT_DEV_DOMAIN}"
  echo "[startup] Using fallback: $EXPO_URL"
fi

echo "$EXPO_URL" > "$TUNNEL_URL_FILE"
echo ""
echo "================================================="
echo " EXPO GO:  $EXPO_URL"
echo " API:      https://$REPLIT_API_DOMAIN"
echo "================================================="

cleanup() {
  kill "$METRO_PID" 2>/dev/null || true
}
trap cleanup EXIT

wait "$METRO_PID"

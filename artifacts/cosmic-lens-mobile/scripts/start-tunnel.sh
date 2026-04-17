#!/bin/bash
TUNNEL_URL_FILE="/tmp/expo-tunnel-url"
LOG_FILE="/tmp/expo-raw.log"

> "$TUNNEL_URL_FILE"
> "$LOG_FILE"

pkill -f "ngrok" 2>/dev/null || true
sleep 1

# API is exposed via localtunnel (cosmiclens-api.loca.lt) — that domain is
# configured as the default in lib/apiConfig.ts, so we DO NOT export
# EXPO_PUBLIC_DOMAIN here (which would override it with the kirk.replit.dev
# URL that Indian cellular carriers block).
PUBLIC_API_URL="https://cosmiclens-api.loca.lt"
echo "[startup] API accessible at: $PUBLIC_API_URL"

METRO_PORT="${PORT:-18987}"

# Re-authenticate Expo (best-effort)
node -e "
const https = require('https');
const data = JSON.stringify({ username: 'Satyayatra', password: 'Scorpio@2030' });
const req = https.request({
  hostname: 'api.expo.dev',
  path: '/v2/auth/loginAsync',
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Content-Length': data.length }
}, (res) => {
  let body = '';
  res.on('data', d => body += d);
  res.on('end', () => {
    try {
      const parsed = JSON.parse(body);
      const secret = parsed.data.sessionSecret;
      const fs = require('fs');
      const os = require('os');
      const path = require('path');
      const stateDir = path.join(os.homedir(), '.expo');
      fs.mkdirSync(stateDir, { recursive: true });
      const statePath = path.join(stateDir, 'state.json');
      let state = {};
      try { state = JSON.parse(fs.readFileSync(statePath, 'utf8')); } catch(e) {}
      state.auth = { sessionSecret: secret, userId: 'Satyayatra', username: 'Satyayatra', currentConnection: 'Username-Password-Authentication' };
      fs.writeFileSync(statePath, JSON.stringify(state, null, 2));
      console.log('[auth] Expo session restored');
    } catch(e) { console.log('[auth] skipped'); }
  });
});
req.on('error', () => console.log('[auth] skipped'));
req.write(data);
req.end();
" 2>/dev/null
sleep 2

# Try tunnel mode first (needed for Expo Go on physical devices)
echo "[startup] Starting Metro on port $METRO_PORT with --tunnel mode..."
pnpm exec expo start --tunnel --port "$METRO_PORT" --clear 2>&1 | tee "$LOG_FILE" &
METRO_PID=$!

echo "[startup] Waiting for Metro tunnel to establish..."
EXPO_URL=""
TUNNEL_OK=false
for i in $(seq 1 20); do
  # Check if metro process died
  if ! kill -0 "$METRO_PID" 2>/dev/null; then
    echo "[startup] Metro/tunnel process died, will fall back to LAN mode"
    break
  fi
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
      TUNNEL_OK=true
      break
    fi
  fi
  sleep 2
done

# If tunnel failed, fall back to plain LAN/proxy mode so the iframe preview works
if [ "$TUNNEL_OK" = false ]; then
  echo "[startup] Tunnel unavailable — starting Metro in plain mode (iframe preview will work)..."
  kill "$METRO_PID" 2>/dev/null || true
  pkill -f "ngrok" 2>/dev/null || true
  sleep 2
  pnpm exec expo start --port "$METRO_PORT" --clear 2>&1 | tee "$LOG_FILE" &
  METRO_PID=$!
  # Prefer Replit's dedicated Expo proxy domain — it bypasses workspace auth so
  # Expo Go on a physical phone can reach Metro. Falls back to the regular dev
  # domain only if the Expo-specific one isn't injected (older Repls).
  if [ -n "$REPLIT_EXPO_DEV_DOMAIN" ]; then
    EXPO_URL="exp://${REPLIT_EXPO_DEV_DOMAIN}"
  else
    EXPO_URL="exp://${REPLIT_DEV_DOMAIN}"
  fi
fi

echo "$EXPO_URL" > "$TUNNEL_URL_FILE"
echo ""
echo "================================================="
echo " EXPO GO:  $EXPO_URL"
echo " API:      $PUBLIC_API_URL"
echo "================================================="

cleanup() {
  kill "$METRO_PID" 2>/dev/null || true
}
trap cleanup EXIT

wait "$METRO_PID"

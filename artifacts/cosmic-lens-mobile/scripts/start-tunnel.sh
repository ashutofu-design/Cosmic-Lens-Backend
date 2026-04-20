#!/bin/bash
TUNNEL_URL_FILE="/tmp/expo-tunnel-url"
LOG_FILE="/tmp/expo-raw.log"

> "$TUNNEL_URL_FILE"
> "$LOG_FILE"

pkill -f "ngrok" 2>/dev/null || true
sleep 1

# API is exposed via localtunnel (cosmiclens-api.loca.lt). The kirk.replit.dev
# domain is blocked on Indian cellular carriers (Jio/Airtel), so we spin up
# a localtunnel on the API port (8080) here, with auto-reconnect.
API_PORT=8080
API_SUB="cosmiclens-api"
PUBLIC_API_URL="https://${API_SUB}.loca.lt"

pkill -f "lt --port ${API_PORT}" 2>/dev/null || true

(
  while true; do
    echo "[lt-api] starting tunnel → ${API_SUB}.loca.lt (port ${API_PORT})"
    lt --port "${API_PORT}" --subdomain "${API_SUB}" 2>&1 | sed 's/^/[lt-api] /'
    echo "[lt-api] exited; retrying in 3s"
    sleep 3
  done
) &
LT_API_PID=$!

# Verify API tunnel is reachable
for i in $(seq 1 15); do
  if curl -sf -m 3 -H "bypass-tunnel-reminder: true" \
       "${PUBLIC_API_URL}/api/health" >/dev/null 2>&1 \
     || curl -sf -m 3 -H "bypass-tunnel-reminder: true" \
       "${PUBLIC_API_URL}/" >/dev/null 2>&1; then
    echo "[startup] API tunnel READY: $PUBLIC_API_URL"
    break
  fi
  sleep 2
done

# Force the mobile app to use this tunnel URL (overrides the dev fallback that
# points to kirk.replit.dev which is blocked on Indian cellular).
export EXPO_PUBLIC_API_URL="$PUBLIC_API_URL"
echo "[startup] EXPO_PUBLIC_API_URL=$EXPO_PUBLIC_API_URL"

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

# If Expo's built-in (ngrok) tunnel failed, expose Metro via localtunnel
# instead. The kirk.replit.dev fallback is unusable on Indian cellular
# carriers (Jio/Airtel) which block that domain.
if [ "$TUNNEL_OK" = false ]; then
  echo "[startup] Expo tunnel unavailable — starting Metro in plain mode + localtunnel…"
  kill "$METRO_PID" 2>/dev/null || true
  pkill -f "ngrok" 2>/dev/null || true
  sleep 2
  pnpm exec expo start --port "$METRO_PORT" --clear 2>&1 | tee "$LOG_FILE" &
  METRO_PID=$!

  # Wait for Metro to bind locally.
  for i in $(seq 1 30); do
    if curl -sf -m 1 "http://localhost:$METRO_PORT/status" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  # Start localtunnel on Metro's port, with auto-reconnect.
  METRO_SUB="cosmiclens-metro"
  (
    while true; do
      echo "[lt-metro] starting tunnel → $METRO_SUB.loca.lt"
      lt --port "$METRO_PORT" --subdomain "$METRO_SUB" 2>&1 | sed 's/^/[lt-metro] /'
      echo "[lt-metro] exited; retrying in 3s"
      sleep 3
    done
  ) &
  LT_METRO_PID=$!

  # Verify localtunnel actually came up. We check two things:
  #  1) The lt-metro logs show our requested subdomain was assigned
  #  2) OR /status responds (metro may still be compiling on first hit)
  for i in $(seq 1 30); do
    if grep -q "your url is: https://$METRO_SUB.loca.lt" "$LOG_FILE" 2>/dev/null \
       || curl -sf -m 3 "https://$METRO_SUB.loca.lt/status" \
            -H "bypass-tunnel-reminder: true" 2>/dev/null | grep -q "packager-status:running"; then
      EXPO_URL="exp://$METRO_SUB.loca.lt"
      echo "[startup] Metro localtunnel ready: $EXPO_URL"
      break
    fi
    # Also check for any random subdomain assignment (loca.lt fallback)
    RANDOM_URL=$(grep -oE 'your url is: https://[a-z0-9-]+\.loca\.lt' "$LOG_FILE" 2>/dev/null | tail -1 | sed 's|your url is: https://||')
    if [ -n "$RANDOM_URL" ] && [ "$i" -ge 15 ]; then
      EXPO_URL="exp://$RANDOM_URL"
      echo "[startup] Metro localtunnel ready (random subdomain): $EXPO_URL"
      break
    fi
    sleep 2
  done

  if [ -z "$EXPO_URL" ]; then
    # Last-resort fallback (won't work on cellular but keeps iframe preview alive).
    if [ -n "$REPLIT_EXPO_DEV_DOMAIN" ]; then
      EXPO_URL="exp://${REPLIT_EXPO_DEV_DOMAIN}"
    else
      EXPO_URL="exp://${REPLIT_DEV_DOMAIN}"
    fi
    echo "[startup] WARNING: localtunnel for Metro failed; falling back to: $EXPO_URL"
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
  [ -n "$LT_METRO_PID" ] && kill "$LT_METRO_PID" 2>/dev/null || true
}
trap cleanup EXIT

wait "$METRO_PID"

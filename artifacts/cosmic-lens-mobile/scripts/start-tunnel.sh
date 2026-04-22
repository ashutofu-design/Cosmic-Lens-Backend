#!/bin/bash
TUNNEL_URL_FILE="/tmp/expo-tunnel-url"
LOG_FILE="/tmp/expo-raw.log"
CF_API_LOG="/tmp/cf-api.log"

> "$TUNNEL_URL_FILE"
> "$LOG_FILE"
> "$CF_API_LOG"

# Cloudflare quick tunnel (free, anonymous, very reliable — replaces flaky
# localtunnel / loca.lt which kept returning 502 Bad Gateway and rotating
# subdomains mid-session).
CFD="${HOME}/.local/bin/cloudflared"
if [ ! -x "$CFD" ]; then
  CFD="$(command -v cloudflared || echo cloudflared)"
fi

# --- API tunnel (port 8080) via Cloudflare quick tunnel ---
API_PORT=8080
pkill -f "cloudflared.*localhost:${API_PORT}" 2>/dev/null || true
sleep 1

(
  echo "[cf-api] starting cloudflare tunnel for :${API_PORT}"
  "$CFD" tunnel --no-autoupdate --protocol http2 --url "http://localhost:${API_PORT}" 2>&1 \
    | tee -a "$CF_API_LOG" | sed 's/^/[cf-api] /'
  echo "[cf-api] EXITED — API tunnel dead; restart workflow"
) &
CF_API_PID=$!

PUBLIC_API_URL=""
for i in $(seq 1 30); do
  URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$CF_API_LOG" 2>/dev/null | tail -1)
  if [ -n "$URL" ]; then
    PUBLIC_API_URL="$URL"
    echo "[startup] API tunnel READY: $PUBLIC_API_URL"
    break
  fi
  sleep 1
done

if [ -z "$PUBLIC_API_URL" ]; then
  echo "[startup] cloudflare API tunnel did not publish a URL; aborting"
  tail -20 "$CF_API_LOG"
  exit 1
fi

export EXPO_PUBLIC_API_URL="$PUBLIC_API_URL"
echo "[startup] EXPO_PUBLIC_API_URL=$EXPO_PUBLIC_API_URL"

# --- Metro tunnel via localtunnel (fast bind) ---
METRO_PORT="${PORT:-18987}"
METRO_SUB="cosmiclens-metro"

pkill -f "lt --port ${METRO_PORT}" 2>/dev/null || true
sleep 1
LT_METRO_LOG="/tmp/lt-metro.log"
> "$LT_METRO_LOG"

# IMPORTANT: spawn ONCE (no auto-respawn loop). When the tunnel drops, lt
# would otherwise reconnect with a NEW random subdomain — but Expo CLI has
# already pinned the OLD subdomain into the bundle's asset URLs at startup,
# so subsequent asset fetches go to a dead host ("Unable to download asset").
# A workflow restart is the right way to recover.
(
  echo "[lt-metro] starting tunnel (single attempt, random subdomain)"
  lt --port "${METRO_PORT}" 2>&1 | tee -a "$LT_METRO_LOG" | sed 's/^/[lt-metro] /'
  echo "[lt-metro] EXITED — Metro tunnel is dead; restart the workflow"
) &
LT_METRO_PID=$!

METRO_PUBLIC_URL=""
for i in $(seq 1 30); do
  URL=$(grep -oE 'https://[a-z0-9-]+\.loca\.lt' "$LT_METRO_LOG" 2>/dev/null | tail -1)
  if [ -n "$URL" ]; then
    METRO_PUBLIC_URL="$URL"
    break
  fi
  sleep 1
done

if [ -z "$METRO_PUBLIC_URL" ]; then
  echo "[startup] localtunnel did not publish a URL; aborting"
  exit 1
fi

METRO_HOST="${METRO_PUBLIC_URL#https://}"
echo "[startup] Metro tunnel host: $METRO_HOST"

export REACT_NATIVE_PACKAGER_HOSTNAME="$METRO_HOST"
export EXPO_PACKAGER_PROXY_URL="$METRO_PUBLIC_URL"
export EXPO_MANIFEST_PROXY_URL="$METRO_PUBLIC_URL"

echo "[startup] Starting Metro on port $METRO_PORT (public host: $METRO_HOST)..."
export EXPO_OFFLINE=1
pnpm exec expo start --port "$METRO_PORT" --offline 2>&1 | tee "$LOG_FILE" &
METRO_PID=$!

for i in $(seq 1 60); do
  if curl -sf -m 2 "http://localhost:$METRO_PORT/status" >/dev/null 2>&1; then
    echo "[startup] Metro local port up."
    break
  fi
  sleep 1
done

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

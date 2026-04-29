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
  CFD="$(command -v cloudflared 2>/dev/null || true)"
fi

# Auto-install if not found (Replit env wipes ~/.local/bin between sessions).
if [ -z "$CFD" ] || ! [ -x "$CFD" ]; then
  echo "[startup] cloudflared not found — installing..."
  mkdir -p "${HOME}/.local/bin"
  CFD="${HOME}/.local/bin/cloudflared"
  curl -sSL --fail \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -o "$CFD" && chmod +x "$CFD" || {
      echo "[startup] FATAL: cloudflared install failed"; exit 1;
    }
  echo "[startup] cloudflared installed: $($CFD --version 2>&1 | head -1)"
fi

# --- API tunnel (port 8080) — try Cloudflare first, fall back to localtunnel ---
API_PORT=8080
LT_API_LOG="/tmp/lt-api.log"
> "$LT_API_LOG"
pkill -f "cloudflared.*localhost:${API_PORT}" 2>/dev/null || true
pkill -f "lt --port ${API_PORT}" 2>/dev/null || true
sleep 1

(
  echo "[cf-api] starting cloudflare tunnel for :${API_PORT}"
  "$CFD" tunnel --no-autoupdate --protocol http2 --url "http://localhost:${API_PORT}" 2>&1 \
    | tee -a "$CF_API_LOG" | sed 's/^/[cf-api] /'
  echo "[cf-api] EXITED — cloudflare API tunnel dead"
) &
CF_API_PID=$!

PUBLIC_API_URL=""
# Wait up to 45s for cloudflare to (a) publish a URL, (b) not error, AND
# (c) actually serve a 2xx through the edge. Cloudflare prints the public
# URL ~1s after start but the edge connection often takes 15-30s more to
# register — declaring READY too early causes the mobile app to bake in a
# URL that returns 530/503 for the first ~20s, breaking demo login until
# the user reloads.
for i in $(seq 1 45); do
  URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$CF_API_LOG" 2>/dev/null | tail -1)
  if [ -n "$URL" ]; then
    # Verify cloudflared hasn't shut down (which means tunnel registration failed)
    if grep -q "Tunnel server stopped\|Initiating shutdown\|context deadline exceeded\|unknown error registering" "$CF_API_LOG" 2>/dev/null; then
      echo "[cf-api] tunnel registered URL but connection failed — falling back to localtunnel"
      URL=""
    else
      # Probe through the edge — only mark READY when origin actually responds 200
      HC=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 4 \
            -H 'bypass-tunnel-reminder: true' \
            "${URL}/api/healthz" 2>/dev/null || echo "000")
      if [ "$HC" = "200" ]; then
        PUBLIC_API_URL="$URL"
        echo "[startup] API tunnel READY (cloudflare): $PUBLIC_API_URL (healthz=200 after ${i}s)"
        break
      fi
    fi
  fi
  sleep 1
done

# If cloudflare failed, kill it and fall back to localtunnel
if [ -z "$PUBLIC_API_URL" ]; then
  echo "[startup] cloudflare API tunnel failed; falling back to localtunnel for :${API_PORT}"
  kill "$CF_API_PID" 2>/dev/null || true
  pkill -f "cloudflared.*localhost:${API_PORT}" 2>/dev/null || true
  sleep 1

  (
    echo "[lt-api] starting localtunnel for :${API_PORT}"
    lt --port "${API_PORT}" 2>&1 | tee -a "$LT_API_LOG" | sed 's/^/[lt-api] /'
    echo "[lt-api] EXITED — API tunnel dead; restart workflow"
  ) &
  LT_API_PID=$!

  for i in $(seq 1 30); do
    URL=$(grep -oE 'https://[a-z0-9-]+\.loca\.lt' "$LT_API_LOG" 2>/dev/null | tail -1)
    if [ -n "$URL" ]; then
      PUBLIC_API_URL="$URL"
      echo "[startup] API tunnel READY (localtunnel): $PUBLIC_API_URL"
      break
    fi
    sleep 1
  done
fi

if [ -z "$PUBLIC_API_URL" ]; then
  echo "[startup] BOTH cloudflare AND localtunnel failed for API; aborting"
  echo "--- cf-api log ---"; tail -20 "$CF_API_LOG"
  echo "--- lt-api log ---"; tail -20 "$LT_API_LOG"
  exit 1
fi

export EXPO_PUBLIC_API_URL="$PUBLIC_API_URL"
echo "[startup] EXPO_PUBLIC_API_URL=$EXPO_PUBLIC_API_URL"

# --- Metro tunnel — try Cloudflare quick tunnel first, fall back to localtunnel ---
# localtunnel.me regularly returns HTTP 408 / heavy interstitial pages
# that break Expo's manifest fetch. Cloudflare quick tunnel is free,
# anonymous (no signup), and far more reliable for Expo Go clients.
METRO_PORT="${PORT:-18987}"
CF_METRO_LOG="/tmp/cf-metro.log"
LT_METRO_LOG="/tmp/lt-metro.log"
> "$CF_METRO_LOG"
> "$LT_METRO_LOG"

pkill -f "cloudflared.*localhost:${METRO_PORT}" 2>/dev/null || true
pkill -f "lt --port ${METRO_PORT}" 2>/dev/null || true
sleep 1

# IMPORTANT: spawn tunnels ONCE (no auto-respawn loops). When a tunnel
# drops, an auto-respawn would reconnect with a NEW random subdomain —
# but Expo CLI has already pinned the OLD subdomain into the bundle's
# asset URLs at startup, so subsequent asset fetches go to a dead host
# ("Unable to download asset"). A workflow restart is the right recovery.
(
  echo "[cf-metro] starting cloudflare tunnel for :${METRO_PORT}"
  "$CFD" tunnel --no-autoupdate --protocol http2 --url "http://localhost:${METRO_PORT}" 2>&1 \
    | tee -a "$CF_METRO_LOG" | sed 's/^/[cf-metro] /'
  echo "[cf-metro] EXITED — Metro cloudflare tunnel dead"
) &
CF_METRO_PID=$!

METRO_PUBLIC_URL=""
# Wait up to 30s for cloudflare to publish a URL AND register the edge
# connection (no shutdown errors). We do NOT probe `/status` here because
# Metro itself isn't started yet — that would deadlock.
for i in $(seq 1 30); do
  URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$CF_METRO_LOG" 2>/dev/null | tail -1)
  if [ -n "$URL" ]; then
    if grep -q "Tunnel server stopped\|Initiating shutdown\|context deadline exceeded\|unknown error registering" "$CF_METRO_LOG" 2>/dev/null; then
      echo "[cf-metro] tunnel registered URL but connection failed — falling back to localtunnel"
      URL=""
    else
      # Verify cloudflared has at least one active connection registered
      if grep -q "Registered tunnel connection" "$CF_METRO_LOG" 2>/dev/null; then
        METRO_PUBLIC_URL="$URL"
        echo "[startup] Metro tunnel READY (cloudflare): $METRO_PUBLIC_URL (after ${i}s)"
        break
      fi
    fi
  fi
  sleep 1
done

# If cloudflare failed, kill it and fall back to localtunnel
if [ -z "$METRO_PUBLIC_URL" ]; then
  echo "[startup] cloudflare Metro tunnel failed; falling back to localtunnel for :${METRO_PORT}"
  kill "$CF_METRO_PID" 2>/dev/null || true
  pkill -f "cloudflared.*localhost:${METRO_PORT}" 2>/dev/null || true
  sleep 1

  (
    echo "[lt-metro] starting tunnel (single attempt, random subdomain)"
    lt --port "${METRO_PORT}" 2>&1 | tee -a "$LT_METRO_LOG" | sed 's/^/[lt-metro] /'
    echo "[lt-metro] EXITED — Metro tunnel is dead; restart the workflow"
  ) &
  LT_METRO_PID=$!

  for i in $(seq 1 30); do
    URL=$(grep -oE 'https://[a-z0-9-]+\.loca\.lt' "$LT_METRO_LOG" 2>/dev/null | tail -1)
    if [ -n "$URL" ]; then
      METRO_PUBLIC_URL="$URL"
      echo "[startup] Metro tunnel READY (localtunnel): $METRO_PUBLIC_URL"
      break
    fi
    sleep 1
  done
fi

if [ -z "$METRO_PUBLIC_URL" ]; then
  echo "[startup] BOTH cloudflare AND localtunnel failed for Metro; aborting"
  echo "--- cf-metro log ---"; tail -20 "$CF_METRO_LOG"
  echo "--- lt-metro log ---"; tail -20 "$LT_METRO_LOG"
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

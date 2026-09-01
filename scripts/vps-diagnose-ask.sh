#!/bin/bash
# Ask /api/ask/stream diagnostics — run on VPS Browser Terminal:
#   cd /root/Cosmic-Lens-Backend && bash scripts/vps-diagnose-ask.sh

set -euo pipefail

REPO="${REPO:-/root/Cosmic-Lens-Backend}"
API_PORT="${API_PORT:-8080}"
API_LOCAL="http://127.0.0.1:${API_PORT}"

cd "$REPO"

echo "========== 1) GIT (latest deploy?) =========="
git log -1 --oneline
echo "Expected recent: Fix Ask HTTP 524 / SSE keepalive / app context"
echo ""

echo "========== 2) PM2 =========="
pm2 list | head -20
echo ""

echo "========== 3) HEALTH =========="
curl -sS -m 10 "${API_LOCAL}/api/healthz" | head -c 400
echo ""
echo ""

echo "========== 4) ENV (Ask killswitches) =========="
grep -E '^(RAW_PASSTHROUGH|OPENAI_|MAX_QUESTION)' artifacts/api-server/.env 2>/dev/null | sed 's/=.*/=***masked***/' || echo "(no .env keys matched)"
echo "RAW_PASSTHROUGH_MODE default=1 (ON). Set 0 + restart = legacy Ask path."
echo ""

echo "========== 5) ASK STREAM — greeting (no auth) =========="
curl -sS -m 30 -N -w "\n\nHTTP:%{http_code}\n" -X POST "${API_LOCAL}/api/ask/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream, application/json" \
  -d '{"question":"hi","lang":"english"}' | head -c 1200
echo ""
echo "(401 without headers is EXPECTED)"
echo ""

echo "========== 6) ASK STREAM — user 29 WITH auth (real test) =========="
cd "$REPO/artifacts/api-server"
read -r COSMO_UID API_KEY < <(./venv/bin/python3 -c "
from flask_app import app
from models import User
with app.app_context():
    u = User.query.get(29)
    if not u:
        print('0 none')
    else:
        print(int(u.id), u.api_key or '')
")
if [ "$COSMO_UID" = "0" ] || [ -z "$API_KEY" ]; then
  echo "User 29 not found or no api_key"
else
  echo "Testing as user_id=$COSMO_UID"
  curl -sS -m 120 -N -w "\n\nHTTP:%{http_code}\n" -X POST "${API_LOCAL}/api/ask/stream" \
    -H "Content-Type: application/json" \
    -H "X-User-Id: ${COSMO_UID}" \
    -H "X-API-Key: ${API_KEY}" \
    -d "{\"question\":\"Which job is best for me long term?\",\"lang\":\"english\",\"user_id\":${COSMO_UID}}" | head -c 2500
fi
echo ""
echo ""

echo "========== 7) ASK STREAM — career Q (no kundli, expect 412 or answer) =========="
curl -sS -m 90 -N -w "\n\nHTTP:%{http_code}\n" -X POST "${API_LOCAL}/api/ask/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream, application/json" \
  -d '{"question":"Which job is best for me long term?","lang":"english"}' | head -c 2000
echo ""
echo ""

echo "========== 8) PM2 LOGS (last 60 lines, ask/errors) =========="
pm2 logs cosmic-api --lines 60 --nostream 2>/dev/null | grep -iE 'ask|error|traceback|exception|524|sse|raw_passthrough|worker' | tail -40 || pm2 logs cosmic-api --lines 40 --nostream
echo ""

echo "========== 9) PYTHON import smoke =========="
cd artifacts/api-server
./venv/bin/python3 -c "
from flask_app import app, _ask_stream_sse_with_keepalive
from openai_helper import raw_passthrough_enabled, _detect_question_lang
print('raw_passthrough_enabled=', raw_passthrough_enabled())
print('lang_detect=', _detect_question_lang('Which job is best for me?', 'en'))
print('import_ok')
" 2>&1
echo ""

echo "========== DONE =========="
echo "Send this FULL output to dev. If step 5/6 shows HTTP:500 or empty body, check step 7."
echo "Emergency workaround: echo 'RAW_PASSTHROUGH_MODE=0' >> artifacts/api-server/.env && pm2 restart cosmic-api --update-env"

#!/bin/bash
# Run ON the VPS (bash) — diagnose + fix Ask 500 after deploy.
# Usage: bash ~/Cosmic-Lens-Backend/scripts/vps-fix-ask-500.sh
set -euo pipefail

API_DIR="${API_DIR:-/root/Cosmic-Lens-Backend/artifacts/api-server}"
PM2_NAME="${PM2_NAME:-cosmic-api}"

cd "$API_DIR"

echo "=== 1. Check finalize_ask_out_after_llm (common 500 cause) ==="
if python3 -c "from subscription_helper import finalize_ask_out_after_llm; print('OK:', finalize_ask_out_after_llm)"; then
  echo "subscription_helper OK"
else
  echo "FAIL: subscription_helper.py is old or missing finalize_ask_out_after_llm"
  echo "Fix: git pull OR scp subscription_helper.py from your PC, then re-run this script"
  exit 1
fi

echo ""
echo "=== 2. py_compile key files ==="
python3 -m py_compile openai_helper.py chart_fact_answer.py flask_app.py subscription_helper.py

echo ""
echo "=== 3. chart_fact Mars strength (no HTTP) ==="
python3 -c "
import sys, json
sys.path.insert(0, '.')
from chart_fact_answer import try_deterministic_chart_fact
k = {'planets': [{'name': 'Mars', 'longitude': 10, 'house': 1, 'sign': 'Aries'}], 'ascendant': 'Aries'}
r = try_deterministic_chart_fact('Mars strong hai ya weak?', k, 'hi')
print(json.dumps(r, ensure_ascii=False) if r else 'NONE (LLM path)')
"

echo ""
echo "=== 4. clear pyc cache + hard restart ==="
find "$API_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$API_DIR" -name '*.pyc' -delete 2>/dev/null || true
pm2 stop "$PM2_NAME" 2>/dev/null || true
sleep 2
pkill -f "gunicorn.*flask_app" 2>/dev/null || true
sleep 1
pm2 start "$PM2_NAME" 2>/dev/null || pm2 restart "$PM2_NAME" --update-env
sleep 4

echo ""
echo "=== 5. health ==="
curl -s http://127.0.0.1:8080/api/health
echo ""

echo ""
echo "=== 6. ask/stream Mars strength ==="
curl -s -m 25 -w "\nHTTP:%{http_code}\n" -X POST http://127.0.0.1:8080/api/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question":"Mars strong hai ya weak?","lang":"hi","kundli":{"planets":[{"name":"Mars","longitude":10,"house":1,"sign":"Aries"}],"ascendant":"Aries","moonSign":"Taurus"}}'
echo ""

echo ""
echo "=== 7. last PM2 errors (if still failing) ==="
pm2 logs "$PM2_NAME" --lines 40 --nostream 2>&1 | tail -40

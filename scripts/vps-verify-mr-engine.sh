#!/bin/bash
# Run ON VPS — verify MR static engine is deployed (not legacy slice fallback).
set -euo pipefail

API_DIR="${API_DIR:-/root/Cosmic-Lens-Backend/artifacts/api-server}"
cd "$API_DIR"

echo "=== ask_mr import ==="
python3 -c "from ask_mr import run_mr_static_engine; print('ask_mr OK')"

echo "=== ASK_MR_ENGINE env ==="
grep -E '^ASK_MR_ENGINE=' .env 2>/dev/null || echo "ASK_MR_ENGINE not set (default=1 new engine)"

echo "=== smoke engine (no HTTP) ==="
python3 - <<'PY'
from ask_mr import run_mr_static_engine
k = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Mars", "sign": "Cancer", "house": 8},
    ],
}
r = run_mr_static_engine(k, "love marriage hogi ya arranged?")
assert r.archetype == "love_vs_arranged", r.archetype
txt = r.to_chart_text(question="love marriage hogi ya arranged?")
assert "MR STATIC ENGINE" in txt, "missing MR STATIC ENGINE header"
print("archetype:", r.archetype)
print("verdict:", r.verdict)
print("evidence:", len(r.evidence))
PY

echo "=== recent pm2 MR logs ==="
pm2 logs cosmic-api --lines 30 --nostream 2>/dev/null | grep -E 'MR_ENGINE|MR_LEGACY|ask_mr' | tail -10 || true

echo "Done. Admin panel should show slice_type=mr_engine_v1 and chart header MR STATIC ENGINE."

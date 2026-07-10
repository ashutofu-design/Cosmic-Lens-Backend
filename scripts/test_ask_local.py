#!/usr/bin/env python3
"""Quick local smoke test for ask raw passthrough + chart_fact."""
import json
import sys
from pathlib import Path

API = Path(__file__).resolve().parents[1] / "artifacts" / "api-server"
sys.path.insert(0, str(API))

errors = []

try:
    import py_compile

    py_compile.compile(str(API / "openai_helper.py"), doraise=True)
    py_compile.compile(str(API / "chart_fact_answer.py"), doraise=True)
    print("COMPILE_OK")
except Exception as e:
    errors.append(f"compile: {e}")
    print(f"COMPILE_FAIL: {e}")

try:
    from chart_fact_answer import try_deterministic_chart_fact

    k = {
        "planets": [{"name": "Mars", "longitude": 10, "house": 1, "sign": "Aries"}],
        "ascendant": "Aries",
        "moonSign": "Taurus",
    }
    r = try_deterministic_chart_fact("Mars strong hai ya weak?", k, "hi")
    print("CHART_FACT:", json.dumps(r, ensure_ascii=False))
except Exception as e:
    errors.append(f"chart_fact: {e}")
    import traceback

    traceback.print_exc()

try:
    from openai_helper import raw_passthrough_ask

    k = {
        "planets": [{"name": "Mars", "longitude": 10, "house": 1, "sign": "Aries"}],
        "ascendant": "Aries",
        "moonSign": "Taurus",
    }
    # Will hit chart_fact deterministic path without OpenAI if client is None... 
    # actually raw_passthrough checks client after chart_fact
    r2 = raw_passthrough_ask("Mars strong hai ya weak?", k, "hi")
    print("RAW_PT:", json.dumps({k: r2.get(k) for k in ("text", "source", "topic")}, ensure_ascii=False))
except Exception as e:
    errors.append(f"raw_passthrough: {e}")
    import traceback

    traceback.print_exc()

if errors:
    sys.exit(1)

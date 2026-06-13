#!/usr/bin/env python3
"""Verify marriage_basics import + compute (run on VPS after deploy)."""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    print("=== marriage_basics verify ===", flush=True)

    try:
        from vedic.compat.marriage_basics import compute_marriage_basics
        print("IMPORT: OK", flush=True)
    except Exception as exc:
        print(f"IMPORT: FAIL — {exc}", flush=True)
        traceback.print_exc()
        return 1

    try:
        from vedic.compat.test_marriage_basics import _sample_kundli

        k1 = _sample_kundli("A", "Leo")
        k2 = _sample_kundli("B", "Cancer", moon_h=5)
        out = compute_marriage_basics(
            k1, k2, p1_name="A", p2_name="B", p1_gender="Male", p2_gender="Female",
        )
        print(f"COMPUTE (sample): OK engine={out.get('engine')}", flush=True)
    except Exception as exc:
        print(f"COMPUTE (sample): FAIL — {exc}", flush=True)
        traceback.print_exc()
        return 1

    try:
        from kundli_engine import calculate_kundli

        bd = {
            "name": "Test",
            "day": 15,
            "month": 6,
            "year": 1995,
            "hour": 10,
            "minute": 30,
            "ampm": "AM",
            "lat": 28.6139,
            "lon": 77.209,
            "tz": 5.5,
            "place": "Delhi",
        }
        k = calculate_kundli(bd)
        if not k.get("planets"):
            print("KUNDLI: FAIL — no planets in chart", flush=True)
            return 1
        out2 = compute_marriage_basics(k, k, p1_name="A", p2_name="B")
        json.dumps(out2)
        print(
            f"FULL PIPELINE: OK engine={out2.get('engine')} "
            f"p1={out2['p1']['readiness_score']} couple={out2['couple']['structural_score']}",
            flush=True,
        )
    except Exception as exc:
        print(f"FULL PIPELINE: FAIL — {exc}", flush=True)
        traceback.print_exc()
        return 1

    print("ALL CHECKS PASSED", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""VPS smoke test — run on server after deploy."""
from __future__ import annotations

import json
import sys

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
IDX = {
    "Mesh": 0, "Vrishabh": 1, "Mithun": 2, "Kark": 3, "Simha": 4, "Kanya": 5,
    "Tula": 6, "Vrishchik": 7, "Dhanu": 8, "Makar": 9, "Kumbh": 10, "Meen": 11,
}


def sample_chart() -> dict:
    planets = []
    for name, sign, house in [
        ("Sun", "Tula", 11), ("Moon", "Mithun", 7), ("Mars", "Dhanu", 1),
        ("Mercury", "Vrishchik", 12), ("Jupiter", "Mesh", 5), ("Venus", "Simha", 9),
        ("Saturn", "Mesh", 5), ("Rahu", "Kark", 8), ("Ketu", "Makar", 2),
    ]:
        si = IDX[sign]
        planets.append({"name": name, "sign": SIGNS[si], "house": house})
    return {"ascendant": "Sagittarius", "ascendantDeg": 248.5, "planets": planets}


def main() -> int:
    chart = sample_chart()
    birth = {"dob": "26 Nov 1999"}

    print("1) imports ...")
    from event_timing.marriage.marriage_timing import compute_timing_window
    from event_timing.marriage.marriage_step0 import run_marriage_step0
    from openai_helper import _run_marriage_m17_block

    print("2) compute_timing_window ...")
    result = compute_timing_window(chart, {}, {}, birth)
    print("   verdict:", result.get("verdict"))
    print("   primary_window:", result.get("primary_window"))
    sa = result.get("step_audit") or {}
    print("   step0:", bool(sa.get("step0")), "step0a:", bool(sa.get("step0a")))

    print("3) _run_marriage_m17_block ...")
    block, raw = _run_marriage_m17_block("mera shaadi kab hoga", chart, birth)
    print("   block_len:", len(block or ""))
    print("   has_raw:", bool(raw))
    if not block:
        print("FAIL: empty marriage block")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

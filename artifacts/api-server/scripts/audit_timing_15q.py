#!/usr/bin/env python3
"""Quick audit — 15 timing questions: domain, engine, promise, dual-track."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.timing_router import resolve_timing_domain, run_timing_engine

_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Sun", "house": 10, "sign": "Virgo"},
        {"name": "Moon", "house": 5, "sign": "Aries"},
        {"name": "Mars", "house": 8, "sign": "Cancer"},
        {"name": "Mercury", "house": 5, "sign": "Aries"},
        {"name": "Jupiter", "house": 1, "sign": "Sagittarius"},
        {"name": "Venus", "house": 11, "sign": "Libra"},
        {"name": "Saturn", "house": 3, "sign": "Aquarius"},
        {"name": "Rahu", "house": 11, "sign": "Libra"},
        {"name": "Ketu", "house": 5, "sign": "Aries"},
    ],
    "dashas": [
        {
            "lord": "Sun",
            "start": "2020-01-01",
            "end": "2026-01-01",
            "subDashas": [
                {
                    "lord": "Rahu",
                    "start": "2024-06-01",
                    "end": "2027-02-01",
                    "subDashas": [
                        {"lord": "Jupiter", "start": "2025-01-01", "end": "2025-08-01"},
                        {"lord": "Sun", "start": "2025-08-01", "end": "2026-03-01"},
                    ],
                },
            ],
        },
    ],
}

_KP = {
    "cusps": [
        {"house": 1, "subLord": "Jupiter"},
        {"house": 5, "subLord": "Mercury"},
        {"house": 7, "subLord": "Venus"},
        {"house": 10, "subLord": "Sun"},
        {"house": 11, "subLord": "Rahu"},
    ],
    "significations": {
        "Sun": {"pl": [10], "sl": [10], "sb_houses": [1, 10], "ss_houses": [10]},
        "Rahu": {"pl": [11], "sl": [11], "sb_houses": [5, 11], "ss_houses": [11]},
        "Jupiter": {"pl": [1], "sl": [9], "sb_houses": [1, 5], "ss_houses": [1]},
        "Mercury": {"pl": [5], "sl": [5], "sb_houses": [3, 5], "ss_houses": [5]},
        "Venus": {"pl": [11], "sl": [7], "sb_houses": [7, 11], "ss_houses": [11]},
    },
}

QUESTIONS = [
    ("Shaadi kab hogi?", "marriage", True),
    ("Mera content kab viral hoga?", "fame", True),
    ("Bade log meri help kab karenge?", "network", True),
    ("Guru kab milega?", "spiritual", True),
    ("Promotion kab milega?", "career", True),
    ("Videsh kab jaunga?", "travel", True),
    ("Ghar kab kharidunga?", "property", True),
    ("Bail kab milegi?", "litigation", True),
    ("Bachcha kab hoga?", "children", True),
    ("Lottery kab lagegi?", "universal", True),
    ("Pet dog kab adopt karun?", "universal", True),
    ("Pyaar kab milega?", "love", True),
    ("College admission kab hoga?", "education", True),
    ("Biwi kaisi hogi?", None, False),
    ("Meri kundli kaisi hai?", None, False),
]


def main() -> int:
    ok = 0
    fail = 0
    print("=" * 72)
    print("TIMING AUDIT — 15 questions")
    print("=" * 72)
    for i, (q, exp_dom, exp_timing) in enumerate(QUESTIONS, 1):
        dom, bucket, is_t = resolve_timing_domain(q)
        dom_ok = (exp_dom is None and not is_t) or (dom == exp_dom)
        timing_ok = is_t == exp_timing
        route_ok = dom_ok and timing_ok

        engine_status = "-"
        verdict = "-"
        promise = "-"
        dual = "-"
        if is_t:
            ctx = run_timing_engine(q, _KUNDLI, {}, _KP, None)
            engine_status = ctx.engine_status
            verdict = (ctx.verdict or "-")[:40]
            prom = (ctx.raw or {}).get("promise_check") or {}
            promise = prom.get("level", "-")
            dt = (ctx.raw or {}).get("dual_track") or {}
            dual = dt.get("winner", "-") if dom != "marriage" else "skip"

        status = "PASS" if route_ok and (not is_t or engine_status == "ready") else "FAIL"
        if status == "PASS":
            ok += 1
        else:
            fail += 1

        print(f"\n{i:2}. [{status}] {q}")
        print(f"    route: domain={dom} bucket={bucket} timing={is_t} (exp dom={exp_dom})")
        if is_t:
            print(f"    engine: status={engine_status} verdict={verdict}")
            print(f"    promise={promise} dual_track={dual}")

    print("\n" + "=" * 72)
    print(f"RESULT: {ok} PASS / {fail} FAIL / {len(QUESTIONS)} total")
    print("=" * 72)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

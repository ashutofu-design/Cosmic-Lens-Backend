#!/usr/bin/env python3
"""Audit 10 finance foundation questions against ask_finance routing."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_career.classifier import classify_career_archetype, is_career_static_question
from ask_finance.classifier import classify_finance_archetype, is_finance_static_question
from ask_finance.engine import run_finance_static_engine

K = {
    "ascendant": "Leo",
    "planets": [
        {"name": "Sun", "house": 1, "sign": "Leo", "longitude": 120.0},
        {"name": "Moon", "house": 4, "sign": "Scorpio", "longitude": 220.0},
        {"name": "Mars", "house": 10, "sign": "Taurus", "longitude": 40.0},
        {"name": "Mercury", "house": 2, "sign": "Virgo", "longitude": 160.0},
        {"name": "Jupiter", "house": 5, "sign": "Sagittarius", "longitude": 250.0},
        {"name": "Venus", "house": 3, "sign": "Libra", "longitude": 190.0},
        {"name": "Saturn", "house": 7, "sign": "Aquarius", "longitude": 300.0},
        {"name": "Rahu", "house": 11, "sign": "Gemini", "longitude": 80.0},
        {"name": "Ketu", "house": 5, "sign": "Sagittarius", "longitude": 260.0},
    ],
    "currentDasha": {"maha": "Jupiter", "antar": "Saturn"},
}

QUESTIONS = [
    ("Kya main ameer banne ki potential rakhta hoon?", "wealth_potential", True),
    ("Mera paisa kamaane ka natural tareeka kya hai?", "income_source", True),
    ("Main employee mindset wala hoon ya entrepreneur mindset wala?", "job_vs_business", False),
    ("Main wealth create karne me kitna capable hoon?", "wealth_potential", True),
    ("Main financial discipline me kaisa hoon?", "financial_discipline", True),
    ("Main paisa bachane wala hoon ya kharch karne wala?", "save_vs_spend", True),
    ("Main risk lene wala investor hoon ya conservative?", "investment_risk", True),
    ("Main financial decisions me practical hoon?", "general_finance", True),
    ("Main emotional spending karta hoon?", "spending_personality", True),
    ("Main luxury-oriented hoon?", "spending_personality", True),
]


def main() -> int:
    fails = 0
    print("ask_finance 10-question audit\n")
    for i, (q, expected_arch, finance_scope) in enumerate(QUESTIONS, 1):
        fin_scope = is_finance_static_question(q)
        car_scope = is_career_static_question(q)
        if finance_scope:
            arch = classify_finance_archetype(q)
            scope_ok = fin_scope and not (expected_arch == "job_vs_business")
            route_ok = arch == expected_arch
            verdict = ""
            ev = 0
            if fin_scope:
                r = run_finance_static_engine(K, q, archetype=arch)
                verdict = (r.verdict or "")[:80]
                ev = len(r.evidence or [])
        else:
            arch = classify_career_archetype(q) if car_scope else "OFF_SCOPE"
            scope_ok = (not fin_scope) and car_scope
            route_ok = arch == expected_arch
            verdict = f"career:{arch}"
            ev = 0

        ok = scope_ok and route_ok and (ev >= 3 if finance_scope else car_scope)
        status = "OK" if ok else "FAIL"
        if not ok:
            fails += 1
        print(f"Q{i}: {status} scope_fin={fin_scope} scope_car={car_scope} route={arch} want={expected_arch}")
        print(f"    {q}")
        print(f"    {verdict}")
        print()
    print(f"result: {10 - fails}/10 OK, {fails} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

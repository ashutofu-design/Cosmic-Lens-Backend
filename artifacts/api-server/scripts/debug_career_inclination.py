"""Debug career inclination. Run: .\\venv\\Scripts\\python.exe scripts\\debug_career_inclination.py"""
from __future__ import annotations

import sys

sys.path.insert(0, ".")

from vedic.career_inclination_engine import CareerChart, ScoreLedger, compute_career_inclination
from vedic.career_inclination_engine import (
    _apply_placement_layer,
    _apply_d10_layer,
    _apply_aspect_layer,
    _apply_affliction_layer,
    _normalize_scores,
    _d1_d10_alignment,
)

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def house_for_sign(asc_idx: int, sign: str) -> int:
    si = SIGNS.index(sign)
    return (si - asc_idx) % 12 + 1


def make_planets(asc: str, placements: dict[str, str]) -> list:
    asc_idx = SIGNS.index(asc)
    out = []
    for name, sign in placements.items():
        out.append({"name": name, "sign": sign, "house": house_for_sign(asc_idx, sign)})
    return out


def debug_chart(label: str, asc: str, placements: dict[str, str], d10: dict | None = None) -> None:
    asc_idx = SIGNS.index(asc)
    planets = make_planets(asc, placements)
    kundli = {"ascendant": asc, "planets": planets}
    if d10:
        kundli["divisionalCharts"] = {
            "D10": {
                "planets": [
                    {"name": n, "sign": s, "house": house_for_sign(asc_idx, s)}
                    for n, s in d10.items()
                ]
            }
        }

    chart = CareerChart(planets, asc_idx, kundli)
    ledger = ScoreLedger()
    _apply_placement_layer(chart, ledger)
    d10j, d10b = _apply_d10_layer(chart, ledger)
    _apply_aspect_layer(chart, ledger)
    _apply_affliction_layer(chart, ledger)
    jr, br, _, _ = _normalize_scores(ledger, d10j, d10b)
    total = jr + br
    raw_job_pct = round(jr * 100 / total, 1)
    align, state = _d1_d10_alignment(chart, ledger.job, ledger.business, d10j, d10b)

    r = compute_career_inclination(planets, asc_idx, kundli)
    print(f"\n=== {label} ===")
    print(f"Lagna {asc} | 10L = {chart.lord(10)} | Moon house = {chart.p('Moon', False) and chart.p('Moon')['house']}")
    print(f"Ledger job={ledger.job:.1f} biz={ledger.business:.1f} affliction={ledger.affliction:.1f}")
    print(f"After normalize: job_raw={jr:.1f} biz_raw={br:.1f} => {raw_job_pct}% job (before snap)")
    print(f"D10 job={d10j:.1f} biz={d10b:.1f} | alignment={state}")
    print(f"FINAL: Job {r['job_pct']}% Business {r['business_pct']}% | {r['career_mode']} | {r['confidence']}")
    if abs(r["job_pct"] - 50) <= 1:
        print(">>> SNAPPED TO 50-50 (gap<=6 rule or contradictory shrink)")
    for line in r.get("reasoning_summary", [])[:8]:
        print(" ", line)


if __name__ == "__main__":
    asc = "Sagittarius"
    # Dhanu lagna — Moon Gemini (7th); common Mercury 10L in 10 or 7
    base = {
        "Sun": "Virgo",
        "Moon": "Gemini",
        "Mars": "Scorpio",
        "Mercury": "Virgo",
        "Jupiter": "Sagittarius",
        "Venus": "Libra",
        "Saturn": "Aquarius",
        "Rahu": "Gemini",
        "Ketu": "Sagittarius",
    }
    debug_chart("Dhanu + Moon Gemini + Merc Virgo (10H)", asc, base)
    debug_chart("Merc in Gemini (7H) — 10L in 7", asc, {**base, "Mercury": "Gemini"})
    debug_chart("Only Moon+Rahu 7H business stack", asc, {
        "Sun": "Leo", "Moon": "Gemini", "Mars": "Aries",
        "Mercury": "Virgo", "Jupiter": "Sagittarius", "Venus": "Libra",
        "Saturn": "Capricorn", "Rahu": "Gemini", "Ketu": "Sagittarius",
    })

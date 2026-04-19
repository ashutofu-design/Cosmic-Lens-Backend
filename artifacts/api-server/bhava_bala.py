"""
bhava_bala.py
─────────────
Approximated Bhava Bala (house strength) per BPHS principles.

Components combined per house (1..12):
  1. Bhava-adhipati bala     — strength of the house lord (from PLANET STRENGTHS)
  2. Bhava-occupant bala     — sum of strength of planets occupying the house
                                (benefic occupant adds, malefic subtracts a little)
  3. Bhava-drishti bala      — Jupiter aspect = +30, Mercury/Venus aspect = +15,
                                Saturn aspect = -10, Mars aspect = -10, Rahu = -5
  4. Bhava-digbala-flag      — kendra (1/4/7/10) gets +10 inherent strength

Verdicts: STRONG ≥ 60, MODERATE 30-59, WEAK < 30.

Public API
──────────
    compute_bhava_bala(intel, planet_verdicts, aspects) -> {
        "scores":   {1..12: int},
        "verdicts": {1..12: "STRONG"|"MODERATE"|"WEAK"},
    }
    format_bhava_bala_summary(bb) -> str
"""
from __future__ import annotations
from typing import Any

# Capped weights — no single factor should fully drive a house's rank.
_VERDICT_PTS = {"STRONG": 20, "MODERATE": 10, "WEAK": -5}
_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
_KENDRA   = {1, 4, 7, 10}
_ASPECT_PTS = {"Jupiter": 18, "Venus": 10, "Mercury": 10,
               "Saturn": -8, "Mars": -8, "Rahu": -4, "Ketu": -4,
               "Sun": 0, "Moon": 4}


def compute_bhava_bala(intel: dict,
                       planet_verdicts: dict | None,
                       aspects: dict | None) -> dict[str, Any]:
    if not isinstance(intel, dict):
        return {}
    house_lords = intel.get("house_lords") or []
    dignities   = intel.get("dignities")   or []
    if not house_lords:
        return {}

    # Planet -> verdict string ("STRONG"|"MODERATE"|"WEAK")
    pv: dict[str, str] = {}
    if isinstance(planet_verdicts, dict):
        for p, row in planet_verdicts.items():
            if isinstance(row, dict) and "verdict" in row:
                pv[p] = row["verdict"]

    # Planet -> house from dignities
    house_of: dict[str, int] = {}
    for d in dignities:
        if isinstance(d, dict) and d.get("planet") and isinstance(d.get("house"), int):
            house_of[d["planet"]] = d["house"]

    scores = {h: 0 for h in range(1, 13)}

    # 1. Bhava-adhipati: lord's strength
    for hl in house_lords:
        h = hl.get("house"); lord = hl.get("lord")
        if isinstance(h, int) and lord:
            scores[h] += _VERDICT_PTS.get(pv.get(lord, ""), 0)

    # 2. Occupant bala
    occupants: dict[int, list[str]] = {h: [] for h in range(1, 13)}
    for p, h in house_of.items():
        if 1 <= h <= 12:
            occupants[h].append(p)
    for h, planets in occupants.items():
        for p in planets:
            base = _VERDICT_PTS.get(pv.get(p, ""), 0) // 2  # half weight for occupant
            if p in _MALEFICS:
                base -= 5
            scores[h] += base

    # 3. Drishti bala (from aspects.on_house map)
    on_house = (aspects or {}).get("on_house") or {}
    for h, planets in on_house.items():
        try:
            h_int = int(h)
        except (TypeError, ValueError):
            continue
        if 1 <= h_int <= 12:
            for p in planets:
                scores[h_int] += _ASPECT_PTS.get(p, 0)

    # 4. Kendra inherent boost
    for h in _KENDRA:
        scores[h] += 10

    # Relative ranking: top 3 = STRONG, middle 6 = MODERATE, bottom 3 = WEAK.
    # Absolute scale was too brittle — a weak chart had every house "WEAK"
    # which gave the AI zero differentiation. Relative banding always gives
    # actionable contrast within THIS chart.
    sorted_houses = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    verdicts: dict[int, str] = {}
    for rank, (h, _) in enumerate(sorted_houses):
        if rank < 3:    verdicts[h] = "STRONG"
        elif rank < 9:  verdicts[h] = "MODERATE"
        else:           verdicts[h] = "WEAK"

    return {"scores": scores, "verdicts": verdicts}


def format_bhava_bala_summary(bb: dict) -> str:
    if not bb or "scores" not in bb:
        return "▸ BHAVA BALA: (unavailable)"
    lines = ["▸ BHAVA BALA (house strength composite — lord+occupants+aspects+kendra):"]
    parts = []
    for h in range(1, 13):
        s = bb["scores"][h]
        v = bb["verdicts"][h][:1]
        parts.append(f"H{h}={s:+d}({v})")
    lines.append("   " + "  ".join(parts[:6]))
    lines.append("   " + "  ".join(parts[6:]))
    lines.append("   Legend: RELATIVE rank within THIS chart — S=top-3, M=middle-6, W=bottom-3")
    strong = [h for h in range(1, 13) if bb["verdicts"][h] == "STRONG"]
    weak   = [h for h in range(1, 13) if bb["verdicts"][h] == "WEAK"]
    if strong: lines.append(f"   ▸ STRONGEST bhavas (relative): {', '.join(f'H{h}' for h in strong)}")
    if weak:   lines.append(f"   ▸ WEAKEST bhavas (relative): {', '.join(f'H{h}' for h in weak)}")
    return "\n".join(lines)

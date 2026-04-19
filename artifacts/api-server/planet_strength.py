"""
planet_strength.py
──────────────────
Single deterministic verdict layer for planet strength: STRONG / MODERATE / WEAK
with a one-line human reason. The AI never has to "guess" planet strength again.

Strategy (in priority order):
  1. If full Shadbala (`compute_shadbala`) is available + succeeds → use strength_pct.
  2. Else fallback to a composite score:
        + dignity     (exalted +3, moolatrikona +2, own +2, friend +1, neutral 0,
                       enemy -1, debilitated -3)
        + house        (kendra 1/4/7/10 +1, trikona 5/9 +1, dusthana 6/8/12 -1)
        + combust      -2 (except Sun)
        + retrograde   +1 for non-luminaries (extra power per classical rules)
       Score >= 3 → STRONG, 1..2 → MODERATE, <=0 → WEAK.

Public API:
    verdict_for_planet(planet, intel_dignity_row, shadbala_row=None) -> dict
        → {"verdict": "STRONG"|"MODERATE"|"WEAK", "reason": str, "score": int|float}

    verdict_table(intel_dignities, shadbala=None) -> dict[planet, verdict_dict]
"""

from __future__ import annotations
from typing import Any, Optional


KENDRA  = {1, 4, 7, 10}
TRIKONA = {5, 9}
DUSTHANA = {6, 8, 12}

LUMINARIES = {"Sun", "Moon"}
NODES = {"Rahu", "Ketu"}

# Shadbala band thresholds (strength_pct: percent of required minimum)
SHADBALA_STRONG = 100.0
SHADBALA_MODERATE = 70.0


def _dignity_score(dig: str) -> int:
    return {
        "exalted":       3,
        "moolatrikona":  2,
        "own-sign":      2,
        "friend's-sign": 1,
        "neutral-sign":  0,
        "enemy-sign":   -1,
        "debilitated":  -3,
    }.get((dig or "").strip().lower(), 0)


def _house_score(house: Any) -> int:
    if not isinstance(house, int):
        return 0
    if house in KENDRA or house in TRIKONA:
        return 1
    if house in DUSTHANA:
        return -1
    return 0


def _band_for_pct(pct: float) -> str:
    if pct >= SHADBALA_STRONG:
        return "STRONG"
    if pct >= SHADBALA_MODERATE:
        return "MODERATE"
    return "WEAK"


def verdict_for_planet(planet: str,
                       intel_row: dict,
                       shadbala_row: Optional[dict] = None) -> dict:
    """
    intel_row example (from chart_intelligence.dignities[i]):
      {"planet": "Saturn", "sign": "Aries", "house": 5,
       "dignity": "debilitated", "combust": False, "retro": True, ...}

    shadbala_row example (from compute_shadbala()[planet]):
      {"total": 480.5, "required": 360, "strength_pct": 133.4, ...}
    """
    if planet in NODES:
        # Nodes have no shadbala; give a soft verdict by sign/house only.
        score = _house_score(intel_row.get("house"))
        if intel_row.get("dignity") == "exalted":  score += 2
        if intel_row.get("dignity") == "debilitated": score -= 2
        verdict = "STRONG" if score >= 2 else ("MODERATE" if score >= 1 else "WEAK")
        return {
            "verdict": verdict,
            "reason":  f"{planet} in {intel_row.get('sign','?')} H{intel_row.get('house','?')}",
            "score":   score,
        }

    # 1. Shadbala path (most authoritative)
    if isinstance(shadbala_row, dict):
        pct = shadbala_row.get("strength_pct")
        if isinstance(pct, (int, float)):
            band = _band_for_pct(float(pct))
            return {
                "verdict": band,
                "reason":  f"Shadbala {pct:.0f}% of required strength",
                "score":   round(float(pct), 1),
            }

    # 2. Fallback composite
    dig    = (intel_row.get("dignity") or "").lower()
    house  = intel_row.get("house")
    combust = bool(intel_row.get("combust"))
    retro   = bool(intel_row.get("retro"))

    score = _dignity_score(dig) + _house_score(house)
    if combust and planet != "Sun":
        score -= 2
    if retro and planet not in LUMINARIES and planet not in NODES:
        score += 1

    if score >= 3:
        band = "STRONG"
    elif score >= 1:
        band = "MODERATE"
    else:
        band = "WEAK"

    # Human reason
    bits: list[str] = []
    if dig:
        bits.append(dig)
    if isinstance(house, int):
        if house in KENDRA: bits.append(f"kendra H{house}")
        elif house in TRIKONA: bits.append(f"trikona H{house}")
        elif house in DUSTHANA: bits.append(f"dusthana H{house}")
        else: bits.append(f"H{house}")
    if combust and planet != "Sun":
        bits.append("combust")
    if retro and planet not in LUMINARIES and planet not in NODES:
        bits.append("retro")
    reason = ", ".join(bits) if bits else "insufficient data"

    return {"verdict": band, "reason": reason, "score": score}


def verdict_table(intel_dignities: list,
                  shadbala: Optional[dict] = None) -> dict:
    """
    intel_dignities: list of rows from chart_intelligence analyze_chart().get("dignities")
    shadbala:        dict from shadbala.compute_shadbala() or None
    Returns: {planet_name: verdict_dict}
    """
    out: dict[str, dict] = {}
    for row in intel_dignities or []:
        if not isinstance(row, dict):
            continue
        p = row.get("planet")
        if not p:
            continue
        sb_row = (shadbala or {}).get(p) if isinstance(shadbala, dict) else None
        out[p] = verdict_for_planet(p, row, sb_row)
    return out

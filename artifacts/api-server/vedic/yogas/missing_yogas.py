"""
Sprint 30 / Phase C — Missing classical yogas (gap fill)
Adds Indra yoga + Shoola yoga (Nabhasa Aakriti).
All other Phase C items (200+) already covered in classical_yogas.py +
extra_yogas.py + chart_intelligence.py.
"""
from __future__ import annotations
from typing import Any, Optional

SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
              "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]


def _planet_sign_idx(planets: list, name: str) -> Optional[int]:
    for p in planets:
        if isinstance(p, dict) and p.get("name") == name:
            sn = p.get("sign")
            if isinstance(sn, str) and sn in SIGN_NAMES:
                return SIGN_NAMES.index(sn)
    return None


def _planet_house(planets: list, name: str) -> Optional[int]:
    for p in planets:
        if isinstance(p, dict) and p.get("name") == name:
            h = p.get("house")
            if isinstance(h, int):
                return h
    return None


def _house_of_sign(lagna_idx: int, sign_idx: int) -> int:
    return ((sign_idx - lagna_idx) % 12) + 1


def detect_indra_yoga(planets: list, lagna_idx: int) -> list[dict]:
    """Indra Yoga (BPHS): formed when
       (a) 5th lord is placed in 11th house, AND
       (b) 11th lord is placed in 5th house, AND
       (c) Moon is placed in 5th house from Lagna.
       Bestows fame, leadership, and power over enemies."""
    out = []
    fifth_sign = (lagna_idx + 4) % 12
    eleventh_sign = (lagna_idx + 10) % 12
    fifth_lord = SIGN_LORDS[fifth_sign]
    eleventh_lord = SIGN_LORDS[eleventh_sign]

    fifth_lord_house = _planet_house(planets, fifth_lord)
    eleventh_lord_house = _planet_house(planets, eleventh_lord)
    moon_house = _planet_house(planets, "Moon")

    cond_a = fifth_lord_house == 11
    cond_b = eleventh_lord_house == 5
    cond_c = moon_house == 5

    matches = sum([cond_a, cond_b, cond_c])
    if matches == 3:
        out.append({
            "name": "Indra yoga (full)", "category": "Royal-Power",
            "reason": f"5L({fifth_lord}) in 11H + 11L({eleventh_lord}) in 5H + Moon in 5H — "
                      f"fame, leadership, victory over enemies",
        })
    elif matches == 2:
        out.append({
            "name": "Indra yoga (partial — 2 of 3 conditions)", "category": "Royal-Power",
            "reason": f"Partial: 5L_in_11H={cond_a}, 11L_in_5H={cond_b}, Moon_in_5H={cond_c}",
        })
    return out


def detect_shoola_yoga(planets: list, lagna_idx: int) -> list[dict]:
    """Shoola Yoga (Nabhasa Aakriti): all 7 grahas (Sun..Saturn, no nodes)
       occupy exactly 3 CONSECUTIVE houses → 'trident' shape.
       Per BPHS Ch.36: bestows valor and martial qualities, but quarrelsome
       nature and difficult interpersonal life."""
    out = []
    occupied_houses = set()
    for p in planets:
        if not isinstance(p, dict): continue
        if p.get("name") in ("Rahu", "Ketu"): continue
        h = p.get("house")
        if isinstance(h, int):
            occupied_houses.add(h)
    if len(occupied_houses) != 3:
        return out
    sorted_h = sorted(occupied_houses)
    # Check 3 consecutive (with wrap)
    is_consecutive = (sorted_h[1] == sorted_h[0] + 1 and sorted_h[2] == sorted_h[0] + 2)
    # Or wrap-around (e.g., 11, 12, 1)
    if not is_consecutive:
        wrap = sorted([(h - 1) % 12 for h in sorted_h])
        is_consecutive = (wrap[1] == wrap[0] + 1 and wrap[2] == wrap[0] + 2)
    if is_consecutive:
        out.append({
            "name": "Shoola yoga (Nabhasa Aakriti — Trident)",
            "category": "Nabhasa Aakriti",
            "reason": f"All 7 grahas confined to 3 consecutive houses {sorted_h} — "
                      f"trident formation; valor + quarrelsome nature",
        })
    return out


def detect_missing_yogas(planets: list, lagna_sign_idx: Optional[int]) -> list[dict]:
    if lagna_sign_idx is None or not isinstance(planets, list):
        return []
    out = []
    out.extend(detect_indra_yoga(planets, lagna_sign_idx))
    out.extend(detect_shoola_yoga(planets, lagna_sign_idx))
    return out


def format_missing_yogas_summary(yogas: list[dict]) -> str:
    lines = ["── PHASE C MISSING YOGAS (Sprint 30) ──"]
    if not yogas:
        lines.append("Indra yoga: not present (need 5L→11H + 11L→5H + Moon in 5H)")
        lines.append("Shoola yoga: not present (need all 7 grahas in 3 consecutive houses)")
    else:
        for y in yogas:
            lines.append(f"  ✓ {y['name']} — {y['reason']}")
    return "\n".join(lines)

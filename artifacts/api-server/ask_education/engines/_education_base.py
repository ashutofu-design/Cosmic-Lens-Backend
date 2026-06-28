"""Shared education chart evidence — D1 4H/5H/9H + Mercury/Jupiter/Rahu."""

from __future__ import annotations

from typing import Any

from vedic.love_reality.scoring_core import KundliReader, SIGNS

_BENEFIC_HOUSES = {1, 4, 5, 9, 10, 11}
_DUSTHANA = {6, 8, 12}


def reader(kundli: dict) -> KundliReader:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    return KundliReader(k)


def house_axis(r: KundliReader, house: int, label: str) -> str:
    asc_i = r.asc_index()
    sign = SIGNS[(asc_i + house - 1) % 12] if isinstance(asc_i, int) else "unknown"
    lord = r.house_lord(house)
    pl = r.planet(lord) if lord else None
    occ = r.occupants(house)
    return (
        f"{label}: house {house} sign {sign}; lord {lord or '?'} in house "
        f"{pl.get('house') if pl else '?'} sign {pl.get('sign') if pl else '?'}; "
        f"occupants={occ or 'none'}."
    )


def planet_line(r: KundliReader, name: str, role: str) -> str:
    p = r.planet(name) or {}
    house = p.get("house")
    sign = p.get("sign")
    if not house:
        return f"{name} ({role}): placement not available."
    tone = _house_tone(int(house))
    return f"{name} ({role}): house {house} sign {sign} — {tone}."


def _house_tone(house: int) -> str:
    if house in _BENEFIC_HOUSES:
        return "supportive for learning"
    if house in _DUSTHANA:
        return "needs extra discipline and structured prep"
    return "mixed — effort and guidance decide outcome"


def education_snapshot(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 4, "Basic education foundation (4th house)"),
        house_axis(r, 5, "Intellect/creative learning (5th house)"),
        house_axis(r, 9, "Higher education/dharma learning (9th house)"),
        planet_line(r, "Mercury", "study/skill karaka"),
        planet_line(r, "Jupiter", "wisdom/higher-learning karaka"),
    ]
    rahu = r.planet("Rahu") or {}
    if rahu.get("house"):
        lines.append(
            f"Rahu (foreign/unconventional study): house {rahu.get('house')} "
            f"sign {rahu.get('sign')} — {_house_tone(int(rahu.get('house')))}."
        )
    return lines[:8]


def learning_strength_score(kundli: dict) -> tuple[int, str]:
    """Simple 0-100 score from karaka house quality."""
    r = reader(kundli)
    score = 50
    for planet in ("Mercury", "Jupiter"):
        p = r.planet(planet) or {}
        house = p.get("house")
        if not house:
            continue
        h = int(house)
        if h in {1, 4, 5, 9, 10, 11}:
            score += 12
        elif h in _DUSTHANA:
            score -= 10
    for house in (4, 5, 9):
        occ = r.occupants(house) or []
        if occ:
            score += 4
        lord = r.house_lord(house)
        pl = r.planet(lord) if lord else None
        if pl and int(pl.get("house") or 0) in _BENEFIC_HOUSES:
            score += 5
    score = max(20, min(92, score))
    if score >= 68:
        label = "strong learning support"
    elif score >= 52:
        label = "moderate learning support — consistent effort matters"
    else:
        label = "learning needs structure, coaching and revision discipline"
    return score, label

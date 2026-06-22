"""Shared litigation chart evidence — 6H/8H/12H + Mars/Saturn/Rahu/Mercury."""

from __future__ import annotations

from typing import Any

from vedic.love_reality.scoring_core import KundliReader, SIGNS

_BENEFIC_HOUSES = {1, 3, 5, 9, 10, 11}
_DUSTHANA = {6, 8, 12}
_LITIGATION_HOUSES = {6, 8, 12}

SAFETY_SUMMARY = [
    "STRICT SAFETY: Do NOT predict confinement, death penalty, phansi, pakka andar, guaranteed conviction or win.",
    "Calm practical tone — chart shows legal friction/support only; qualified lawyer essential.",
]


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


def lord_line(r: KundliReader, house: int, label: str) -> str:
    lord = r.house_lord(house)
    if not lord:
        return f"{label}: lord not available."
    pl = r.planet(lord) or {}
    return (
        f"{label} ({lord}): house {pl.get('house') or '?'} sign {pl.get('sign') or '?'} — "
        f"{_house_tone(int(pl.get('house') or 0)) if pl.get('house') else 'mixed placement'}."
    )


def _house_tone(house: int) -> str:
    if house in _LITIGATION_HOUSES:
        return "direct legal/conflict axis linkage"
    if house in _BENEFIC_HOUSES:
        return "supportive for dispute handling and counsel strategy"
    if house == 7:
        return "opponent/public litigation axis — balance both sides"
    return "mixed — verify facts and legal counsel"


def litigation_snapshot(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 6, "Litigation/enemies axis (6th house)"),
        house_axis(r, 8, "Sudden crisis/legal shock axis (8th house)"),
        house_axis(r, 12, "Loss/confinement/legal expense axis (12th house)"),
        lord_line(r, 6, "6th lord litigation tone"),
        lord_line(r, 8, "8th lord crisis/legal shock tone"),
        lord_line(r, 12, "12th lord confinement/expense tone"),
        planet_line(r, "Mars", "conflict/court-fight karaka"),
        planet_line(r, "Saturn", "delay/judgment/legal process karaka"),
        planet_line(r, "Rahu", "complexity/FIR/litigation karaka"),
        planet_line(r, "Mercury", "arguments/documents/advocate karaka"),
        planet_line(r, "Sun", "authority/court/govt axis karaka"),
    ]
    return lines[:12]


def litigation_strength_score(kundli: dict) -> tuple[int, str]:
    r = reader(kundli)
    score = 46
    mars = r.planet("Mars") or {}
    mh = int(mars.get("house") or 0)
    if mh in (6, 10, 11, 3):
        score += 12
    elif mh in (1, 5, 9):
        score += 6
    elif mh in (8, 12):
        score -= 4

    sat = r.planet("Saturn") or {}
    sh = int(sat.get("house") or 0)
    if sh in (6, 8):
        score -= 8
    elif sh in (3, 10, 11):
        score += 4

    rh = int((r.planet("Rahu") or {}).get("house") or 0)
    if rh in (6, 8, 12):
        score -= 6
    elif rh in (3, 10):
        score += 2

    for h in (6, 8):
        lord = r.house_lord(h)
        pl = r.planet(lord) if lord else None
        if pl and int(pl.get("house") or 0) in (1, 3, 5, 9, 10, 11):
            score += 6

    twelfth_lord = r.house_lord(12)
    p12l = r.planet(twelfth_lord) if twelfth_lord else None
    if p12l and int(p12l.get("house") or 0) in (6, 8, 12):
        score -= 5

    score = max(16, min(90, score))
    if score >= 66:
        label = "relatively supportive legal-handling axis"
    elif score >= 50:
        label = "mixed legal axis — patience, documents and counsel both matter"
    else:
        label = "legal friction visible — structured counsel and calm strategy needed"
    return score, label

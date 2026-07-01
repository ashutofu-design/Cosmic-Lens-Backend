"""Shared luck / bhagya chart evidence — D1 5H/9H/11H + Jupiter + Moon."""

from __future__ import annotations

from typing import Any

from vedic.love_reality.scoring_core import KundliReader, SIGNS

_BENEFIC = {1, 4, 5, 9, 10, 11}
_DUSTHANA = {6, 8, 12}
_MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}


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
        f"{label}: H{house} sign {sign}; lord {lord or '?'} in H"
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
    return f"{name} ({role}): H{house} sign {sign} — {tone}."


def _house_tone(house: int) -> str:
    if house in _BENEFIC:
        return "supports fortune/luck themes"
    if house in _DUSTHANA:
        return "needs discipline, patience and remedies"
    return "mixed — effort and timing both matter"


def luck_score(kundli: dict) -> tuple[int, str]:
    r = reader(kundli)
    score = 50

    jup = r.planet("Jupiter") or {}
    jh = jup.get("house")
    if jh:
        h = int(jh)
        if h in _BENEFIC:
            score += 14
        elif h in _DUSTHANA:
            score -= 10

    moon = r.planet("Moon") or {}
    mh = moon.get("house")
    if mh and int(mh) in _BENEFIC:
        score += 6

    for house in (5, 9, 11):
        lord = r.house_lord(house)
        pl = r.planet(lord) if lord else None
        if not pl:
            continue
        lh = pl.get("house")
        if lh and int(lh) in _BENEFIC:
            score += 8
        elif lh and int(lh) in _DUSTHANA:
            score -= 6
        for occ in r.occupants(house) or []:
            if occ in _MALEFICS:
                score -= 4
            elif occ in {"Jupiter", "Venus", "Mercury", "Moon"}:
                score += 3

    score = max(18, min(92, score))
    if score >= 72:
        label = "strong bhagya support"
    elif score >= 55:
        label = "mixed but workable fortune"
    else:
        label = "luck needs effort + remedies"
    return score, label


def fortune_snapshot(kundli: dict, *, focus: str = "overall") -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 9, "Bhagya/dharma axis (9th house)"),
        house_axis(r, 5, "Purva punya / grace axis (5th house)"),
        house_axis(r, 11, "Gains/fulfilment axis (11th house)"),
        planet_line(r, "Jupiter", "bhagya karaka (Guru)"),
        planet_line(r, "Moon", "mind + emotional fortune"),
    ]
    if focus == "career":
        lines.insert(0, house_axis(r, 10, "Career/karma axis (10th house)"))
    elif focus == "love":
        lines.insert(0, house_axis(r, 7, "Partnership axis (7th house)"))
        lines.insert(1, planet_line(r, "Venus", "relationship grace"))
    elif focus == "money":
        lines.insert(0, house_axis(r, 2, "Wealth/resources axis (2nd house)"))
    score, label = luck_score(kundli)
    lines.append(f"Luck index: {score}/100 — {label}.")
    return lines[:9]


def lucky_trait_hints(kundli: dict) -> list[str]:
    r = reader(kundli)
    lord9 = r.house_lord(9)
    pl9 = r.planet(lord9) if lord9 else {}
    jup = r.planet("Jupiter") or {}
    sign9_idx = r.asc_index()
    if isinstance(sign9_idx, int):
        sign9 = SIGNS[(sign9_idx + 8) % 12]
    else:
        sign9 = "?"
    hints = [
        f"9th house sign {sign9} — use its lord {lord9 or '?'} themes for lucky colour/day hints.",
        f"Jupiter H{jup.get('house') or '?'} — primary grace planet for remedies.",
    ]
    if lord9:
        hints.append(f"9L {lord9} in H{pl9.get('house') or '?'} — anchor lucky traits from this planet.")
    return hints

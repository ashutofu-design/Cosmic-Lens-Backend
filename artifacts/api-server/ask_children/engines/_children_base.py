"""Shared children/progeny chart evidence — D1 5H/9H/11H + Jupiter + D7."""

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
        return "supportive for progeny/children themes"
    if house in _DUSTHANA:
        return "needs patience, remedies and specialist guidance"
    return "mixed — effort and timing discipline matter"


def d7_lines(kundli: dict) -> list[str]:
    lines: list[str] = []
    try:
        from divisional_charts import compute_d7, summarize_d7_for_children  # type: ignore

        planets = (kundli or {}).get("planets") or []
        lagna_lon = (kundli or {}).get("ascendantDeg") or (kundli or {}).get("ascendant_lon")
        if not planets or lagna_lon is None:
            return lines
        asc = reader(kundli)
        intel = {"house_lords": [{"house": h, "lord": asc.house_lord(h)} for h in range(1, 13)]}
        d7 = compute_d7(planets, float(lagna_lon))
        s7 = summarize_d7_for_children(d7, intel) if d7 else {}
        if s7.get("5L_d7_sign"):
            lines.append(
                f"D7 Saptamsa: 5L {s7.get('5L')} in {s7['5L_d7_sign']} "
                f"({s7.get('5L_d7_strength')}) — progeny refinement axis."
            )
        if s7.get("jupiter_d7_sign"):
            lines.append(
                f"D7 Jupiter putra-karaka in {s7['jupiter_d7_sign']} "
                f"({s7.get('jupiter_d7_strength')})."
            )
    except Exception:
        pass
    return lines[:2]


def progeny_snapshot(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 5, "Progeny/children axis (5th house)"),
        house_axis(r, 9, "Fortune/dharma for children (9th house)"),
        house_axis(r, 11, "Fulfillment/gains from children (11th house)"),
        planet_line(r, "Jupiter", "putra karaka (Guru)"),
    ]
    lines.extend(d7_lines(kundli))
    return lines[:8]


def progeny_strength_score(kundli: dict) -> tuple[int, str]:
    r = reader(kundli)
    score = 50
    for planet in ("Jupiter",):
        p = r.planet(planet) or {}
        house = p.get("house")
        if not house:
            continue
        h = int(house)
        if h in {1, 4, 5, 9, 10, 11}:
            score += 12
        elif h in _DUSTHANA:
            score -= 10
    lord5 = r.house_lord(5)
    p5l = r.planet(lord5) if lord5 else None
    if p5l and int(p5l.get("house") or 0) in _BENEFIC_HOUSES:
        score += 8
    occ5 = r.occupants(5) or []
    if occ5:
        score += 4
    score = max(18, min(92, score))
    if score >= 68:
        label = "strong progeny support"
    elif score >= 52:
        label = "moderate progeny support — patience and remedies help"
    else:
        label = "progeny needs structured effort, faith and specialist support"
    return score, label

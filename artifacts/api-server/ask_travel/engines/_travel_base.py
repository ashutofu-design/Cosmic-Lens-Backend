"""Shared foreign-travel chart evidence — 3H/9H/12H + karakas + D9."""

from __future__ import annotations

from typing import Any

from vedic.love_reality.scoring_core import KundliReader, SIGNS

_BENEFIC_HOUSES = {1, 3, 5, 9, 10, 11}
_DUSTHANA = {6, 8, 12}
_FOREIGN_HOUSES = {3, 9, 12}


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
    if house in _FOREIGN_HOUSES:
        return "strong foreign/travel linkage"
    if house in _BENEFIC_HOUSES:
        return "supportive for travel themes"
    if house in _DUSTHANA:
        return "needs patience, paperwork and realistic planning"
    if house == 4:
        return "home-anchor — weakens or delays relocation when strong"
    return "mixed — verify documents and practical readiness"


def d9_lines(kundli: dict) -> list[str]:
    lines: list[str] = []
    try:
        from divisional_charts import compute_d9  # type: ignore

        planets = (kundli or {}).get("planets") or []
        lagna_lon = (kundli or {}).get("ascendantDeg") or (kundli or {}).get("ascendant_lon")
        if not planets or lagna_lon is None:
            return lines
        asc = reader(kundli)
        intel = {"house_lords": [{"house": h, "lord": asc.house_lord(h)} for h in range(1, 13)]}
        d9 = compute_d9(planets, float(lagna_lon))
        if not d9:
            return lines
        ninth_lord = next((h.get("lord") for h in intel["house_lords"] if h.get("house") == 9), None)
        twelfth_lord = next((h.get("lord") for h in intel["house_lords"] if h.get("house") == 12), None)
        if ninth_lord and ninth_lord in d9:
            lines.append(
                f"D9 Navamsa: 9L {ninth_lord} in {d9[ninth_lord]['sign']} — "
                "long-distance/dharma travel refinement."
            )
        if twelfth_lord and twelfth_lord in d9:
            lines.append(
                f"D9 Navamsa: 12L {twelfth_lord} in {d9[twelfth_lord]['sign']} — "
                "foreign lands/settlement refinement."
            )
        for planet, role in (("Rahu", "foreign/unconventional axis"), ("Jupiter", "visa-luck/sacred travel")):
            if planet in d9:
                lines.append(f"D9 {planet} ({role}) in {d9[planet]['sign']}.")
    except Exception:
        pass
    return lines[:4]


def travel_snapshot(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 9, "Long-distance/foreign axis (9th house)"),
        house_axis(r, 12, "Foreign lands/settlement axis (12th house)"),
        house_axis(r, 3, "Short travel/courage axis (3rd house)"),
        house_axis(r, 4, "Home anchor (4th house — inverted for relocation)"),
        planet_line(r, "Rahu", "foreign/unconventional travel karaka"),
        planet_line(r, "Jupiter", "visa-luck/sacred travel karaka"),
        planet_line(r, "Moon", "movement/water-travel karaka"),
        planet_line(r, "Mercury", "short trips/communication karaka"),
        planet_line(r, "Saturn", "long arduous travel/immigration karaka"),
    ]
    lines.extend(d9_lines(kundli))
    return lines[:12]


def travel_strength_score(kundli: dict) -> tuple[int, str]:
    r = reader(kundli)
    score = 48
    rahu = r.planet("Rahu") or {}
    rh = int(rahu.get("house") or 0)
    if rh in (3, 9, 12):
        score += 14
    elif rh in (1, 5, 10, 11):
        score += 6
    for h in (9, 12):
        lord = r.house_lord(h)
        pl = r.planet(lord) if lord else None
        if pl and int(pl.get("house") or 0) in (3, 9, 12, 1):
            score += 8
    jup = r.planet("Jupiter") or {}
    if int(jup.get("house") or 0) in (9, 12, 1, 5):
        score += 6
    sat = r.planet("Saturn") or {}
    if int(sat.get("house") or 0) == 12:
        score += 4
    fourth_lord = r.house_lord(4)
    p4l = r.planet(fourth_lord) if fourth_lord else None
    if p4l and int(p4l.get("house") or 0) in (4, 2):
        score -= 6
    score = max(18, min(92, score))
    if score >= 68:
        label = "strong foreign/travel support"
    elif score >= 52:
        label = "moderate foreign/travel support — planning and paperwork matter"
    else:
        label = "foreign/travel needs patience, documents and repeated effort"
    return score, label

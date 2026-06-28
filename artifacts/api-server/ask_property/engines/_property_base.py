"""Shared property/real-estate chart evidence — 4H/2H/11H + karakas + property_static dims."""

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
        return "supportive for property/home themes"
    if house in _DUSTHANA:
        return "needs caution, legal checks and patience"
    return "mixed — planning and verification matter"


def dimension_lines(kundli: dict) -> list[str]:
    lines: list[str] = []
    try:
        from property_static.property_engine import compute_property_facts

        facts = compute_property_facts(kundli if isinstance(kundli, dict) else {})
        dims = (facts or {}).get("dimensions") or {}
        yog = dims.get("yog") or {}
        cap = dims.get("capacity") or {}
        risk = dims.get("risk") or {}
        fit = dims.get("type_fit") or {}
        if yog.get("verdict"):
            lines.append(f"Property yog: {yog['verdict']} — {yog.get('reason', '')}")
        if cap.get("verdict"):
            lines.append(f"Property capacity: {cap['verdict']} — {cap.get('reason', '')}")
        if risk.get("verdict"):
            lines.append(f"Property risk: {risk['verdict']} — {risk.get('reason', '')}")
        if fit.get("best"):
            lines.append(
                f"Type fit: best={fit.get('best')} alt={fit.get('alt')} — {fit.get('reason', '')}"
            )
    except Exception:
        pass
    return lines[:4]


def d4_lines(kundli: dict) -> list[str]:
    lines: list[str] = []
    try:
        from divisional_charts import compute_d4, summarize_d4_for_property  # type: ignore

        planets = (kundli or {}).get("planets") or []
        lagna_lon = (kundli or {}).get("ascendantDeg") or (kundli or {}).get("ascendant_lon")
        if not planets or lagna_lon is None:
            return lines
        asc = reader(kundli)
        intel = {"house_lords": [{"house": h, "lord": asc.house_lord(h)} for h in range(1, 13)]}
        d4 = compute_d4(planets, float(lagna_lon))
        s4 = summarize_d4_for_property(d4, intel) if d4 else {}
        if s4.get("4L_d4_sign"):
            lines.append(
                f"D4 Chaturthamsa: 4L {s4.get('4L')} in {s4['4L_d4_sign']} "
                f"({s4.get('4L_d4_strength')}) — home/property refinement axis."
            )
        if s4.get("mars_d4_sign"):
            lines.append(
                f"D4 Mars land-karaka in {s4['mars_d4_sign']} "
                f"({s4.get('mars_d4_strength')}) — plot/land tone."
            )
        if s4.get("moon_d4_sign"):
            lines.append(
                f"D4 Moon home-karaka in {s4['moon_d4_sign']} "
                f"({s4.get('moon_d4_strength')}) — dwelling/family tone."
            )
        if s4.get("venus_d4_sign"):
            lines.append(
                f"D4 Venus comfort-karaka in {s4['venus_d4_sign']} "
                f"({s4.get('venus_d4_strength')}) — luxury/comfort/size tone."
            )
        if s4.get("property_size_tone"):
            lines.append(f"D4 property-size/style tone: {s4['property_size_tone']}.")
    except Exception:
        pass
    return lines[:5]


def property_snapshot(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 4, "Home/property axis (4th house)"),
        house_axis(r, 2, "Accumulated wealth for assets (2nd house)"),
        house_axis(r, 11, "Gains from property (11th house)"),
        planet_line(r, "Mars", "land/plot karaka"),
        planet_line(r, "Moon", "home/family/ancestral karaka"),
        planet_line(r, "Saturn", "immovable/rental karaka"),
        planet_line(r, "Venus", "comfort/luxury home karaka"),
        planet_line(r, "Jupiter", "wealth growth karaka"),
    ]
    lines.extend(d4_lines(kundli))
    lines.extend(dimension_lines(kundli))
    return lines[:12]


def property_strength_score(kundli: dict) -> tuple[int, str]:
    try:
        from property_static.property_engine import compute_property_facts

        facts = compute_property_facts(kundli if isinstance(kundli, dict) else {})
        dims = (facts or {}).get("dimensions") or {}
        score = 50
        yog = (dims.get("yog") or {}).get("score") or 0
        cap = (dims.get("capacity") or {}).get("score") or 0
        risk = (dims.get("risk") or {}).get("score") or 0
        score += int(yog) * 3
        score += int(cap) * 2
        score -= int(risk) * 2
        score = max(18, min(92, score))
        if score >= 68:
            label = "strong property support"
        elif score >= 52:
            label = "moderate property support — planning helps"
        else:
            label = "property needs structured planning and legal caution"
        return score, label
    except Exception:
        return 50, "moderate property support — planning helps"

"""Shared vehicle chart evidence — 4H/11H/3H + Venus/Mars karakas."""

from __future__ import annotations

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
        return "supportive for vehicle/comfort themes"
    if house in _DUSTHANA:
        return "needs caution, maintenance and insurance discipline"
    return "mixed — practical planning matters"


def dimension_lines(kundli: dict) -> list[str]:
    lines: list[str] = []
    try:
        from vehicle_static.vehicle_engine import compute_vehicle_facts

        facts = compute_vehicle_facts(kundli if isinstance(kundli, dict) else {})
        dims = (facts or {}).get("dimensions") or {}
        for key in ("readiness", "safety", "luxury", "type_choice", "colour", "commercial", "ownership"):
            dim = dims.get(key) or {}
            if key == "type_choice" and dim.get("reason"):
                lines.append(f"Vehicle type: {dim['reason']}")
            elif key == "colour" and dim.get("best"):
                lines.append(
                    f"Colour: best={dim.get('best')} alt={dim.get('alt')} — {dim.get('reason', '')}"
                )
            elif key == "luxury" and dim.get("tier"):
                lines.append(
                    f"Luxury tier: {dim.get('tier')} — {dim.get('reason', '')} ({dim.get('verdict', '')})"
                )
            elif dim.get("verdict"):
                lines.append(f"Vehicle {key}: {dim['verdict']} — {dim.get('reason', '')}")
            elif dim.get("mode"):
                lines.append(f"Vehicle ownership: {dim['mode']} — {dim.get('reason', '')}")
    except Exception:
        pass
    return lines[:7]


def vehicle_snapshot(kundli: dict) -> list[str]:
    r = reader(kundli)
    lines = [
        house_axis(r, 4, "4H vehicle/comfort axis"),
        house_axis(r, 11, "11H gain/fulfilment axis"),
        house_axis(r, 3, "3H commute/short travel axis"),
        planet_line(r, "Venus", "vehicle/luxury karaka"),
        planet_line(r, "Mars", "machinery/vehicle energy karaka"),
    ]
    lines.extend(dimension_lines(kundli))
    return lines


def vehicle_strength_score(kundli: dict) -> tuple[int, str]:
    try:
        from vehicle_static.vehicle_engine import compute_vehicle_facts

        dims = (compute_vehicle_facts(kundli).get("dimensions") or {})
        readiness = dims.get("readiness") or {}
        luxury = dims.get("luxury") or {}
        score = int(readiness.get("score") or 0) + int(luxury.get("score") or 0) + 50
        score = max(0, min(100, score))
        if score >= 68:
            return score, "strong"
        if score >= 52:
            return score, "moderate"
        return score, "needs_planning"
    except Exception:
        return 50, "moderate"

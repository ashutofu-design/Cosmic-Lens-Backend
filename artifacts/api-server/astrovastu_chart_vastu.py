"""
Chart ↔ Vastu bridge — planet-house stress, drishti aspects, direction–bhava grid.
Pure functions; consumed by room_pipeline and severity multiplier.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from astrovastu_rules import (
    DIRECTION_BHAVA_GRID,
    PLANET_HOUSE_STRESS,
    SIGN_LORD,
    get_bhavas_for_direction,
    get_directions_for_bhava,
    get_planet_direction,
)

SIGNS: List[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

DEBILITATION: Dict[str, str] = {
    "Sun": "Libra",
    "Moon": "Scorpio",
    "Mars": "Cancer",
    "Mercury": "Pisces",
    "Jupiter": "Capricorn",
    "Venus": "Virgo",
    "Saturn": "Aries",
}

# Room type → bhava used for lord-placement overlay (classical Astro-Vastu mapping).
ROOM_BHAVA: Dict[str, int] = {
    "kitchen": 4,
    "bedroom": 4,
    "master_bedroom": 4,
    "pooja": 9,
    "pooja_room": 9,
    "study": 5,
    "living": 1,
    "living_room": 1,
    "main_door": 1,
    "entrance": 1,
    "bathroom": 6,
    "toilet": 6,
    "dining": 2,
    "cash_locker": 2,
    "staircase": 3,
}

# Vedic special aspects: planet → offset signs from its position (1-based house distance).
_SPECIAL_ASPECTS: Dict[str, Tuple[int, ...]] = {
    "Mars": (4, 7, 8),
    "Jupiter": (5, 7, 9),
    "Saturn": (3, 7, 10),
    "Rahu": (5, 7, 9),
    "Ketu": (5, 7, 9),
}


def _sign_index(sign: str) -> int:
    s = (sign or "").strip().title()
    try:
        return SIGNS.index(s)
    except ValueError:
        return 0


def house_sign_from_lagna(lagna: str, house: int) -> str:
    return SIGNS[(_sign_index(lagna) + int(house) - 1) % 12]


def _planet_by_name(planets: List[dict], name: str) -> Optional[dict]:
    for p in planets or []:
        if (p.get("name") or "").strip().lower() == name.lower():
            return p
    return None


def _match_stress_condition(planets: List[dict], condition: str) -> bool:
    """Match PLANET_HOUSE_STRESS condition strings against natal placements."""
    c = (condition or "").lower()
    for p in planets or []:
        name = (p.get("name") or "").strip()
        if not name:
            continue
        house = int(p.get("house") or 0)
        sign = (p.get("sign") or "").strip()
        if name.lower() not in c:
            continue
        if "in 1/4/7/10" in c or "kendra" in c:
            if house in (1, 4, 7, 10):
                return True
        if "in 4" in c and house == 4:
            return True
        if "in 12" in c and house == 12:
            return True
        if "weak" in c and "6/8/12" in c:
            if house in (6, 8, 12):
                return True
        if "weak" in c and "6)" in c and house == 6:
            return True
        if "weak" in c and "6/8" in c and house in (6, 8):
            return True
        if "combust" in c and name == "Mercury":
            sun = _planet_by_name(planets, "Sun")
            if sun and abs(float(p.get("longitude") or 0) - float(sun.get("longitude") or 999)) < 12:
                return True
        if deb := DEBILITATION.get(name):
            if sign == deb:
                return True
    return False


def evaluate_chart_stress_hits(
    planets: List[dict],
    _extra: Optional[List[Any]] = None,
) -> List[Dict[str, Any]]:
    """Return active PLANET_HOUSE_STRESS rows for this chart."""
    hits: List[Dict[str, Any]] = []
    for row in PLANET_HOUSE_STRESS:
        if _match_stress_condition(planets, row.get("condition") or ""):
            hits.append(dict(row))
    return hits


def _aspect_target_signs(planet_sign: str, planet_name: str) -> Set[int]:
    """Sign indices aspected by planet from its natal sign."""
    src = _sign_index(planet_sign)
    offsets = _SPECIAL_ASPECTS.get(planet_name, (7,))
    return {(src + off - 1) % 12 for off in offsets}


def aspects_on_bhava(lagna: str, bhava: int, planets: List[dict]) -> List[str]:
    """Planets whose drishti hits the sign occupied by `bhava` from Lagna."""
    target = _sign_index(house_sign_from_lagna(lagna, bhava))
    out: List[str] = []
    for p in planets or []:
        name = (p.get("name") or "").strip()
        ps = (p.get("sign") or "").strip()
        if not name or not ps:
            continue
        if target in _aspect_target_signs(ps, name):
            out.append(name)
    return out


def direction_grid_for_bhava(bhava: int) -> List[str]:
    return get_directions_for_bhava(bhava)


def direction_grid_stress_for_direction(
    lagna: str,
    direction: str,
    planets: List[dict],
) -> List[Dict[str, Any]]:
    """
    Link compass sector → bhavas (DIRECTION_BHAVA_GRID) → malefic aspects on those bhavas.
    """
    bhavas = get_bhavas_for_direction(direction)
    notes: List[Dict[str, Any]] = []
    malefics = {"Saturn", "Mars", "Rahu", "Ketu"}
    for bh in bhavas:
        for asp in aspects_on_bhava(lagna, bh, planets):
            if asp in malefics:
                notes.append({
                    "bhava": bh,
                    "direction": direction,
                    "aspector": asp,
                    "note": f"{asp} aspects your {bh}th-house zone — {direction} sector needs extra care.",
                })
    return notes


def bhava_lord_placement(
    lagna: str,
    bhava: int,
    planets: List[dict],
) -> Optional[Dict[str, Any]]:
    """Lord of `bhava` from Lagna and where that lord sits in D1."""
    if not lagna or not bhava:
        return None
    hs = house_sign_from_lagna(lagna, bhava)
    lord = SIGN_LORD.get(hs)
    if not lord:
        return None
    pl = _planet_by_name(planets, lord)
    placed_sign = (pl.get("sign") or "").strip() if pl else ""
    placed_house = int(pl.get("house") or 0) if pl else 0
    bdir = get_planet_direction(lord) if lord else None
    if placed_sign:
        pdir = get_planet_direction(lord)
        # Placement sign direction: sign lord's natural direction from placed sign ruler
        placed_lord = SIGN_LORD.get(placed_sign)
        placement_direction = get_planet_direction(placed_lord or lord) or pdir
    else:
        placement_direction = bdir
    return {
        "house_sign": hs,
        "lord": lord,
        "placed_sign": placed_sign or None,
        "placed_house": placed_house or None,
        "direction": bdir,
        "placement_direction": placement_direction,
    }


def enrich_chart_vastu_context(
    ctx: Dict[str, Any],
    planets: Optional[List[dict]] = None,
) -> Dict[str, Any]:
    """Attach chart stress hits, aspect notes, and direction-grid overlays to ctx."""
    pl = planets if planets is not None else (ctx.get("planets") or [])
    hits = evaluate_chart_stress_hits(pl, [])
    ctx = dict(ctx)
    ctx["chart_stress_hits"] = hits
    ctx["chart_vastu_active"] = bool(hits) or bool(ctx.get("lagna"))
    lagna = ctx.get("lagna") or ""
    if lagna:
        grid_notes: List[Dict[str, Any]] = []
        for direction in DIRECTION_BHAVA_GRID:
            grid_notes.extend(
                direction_grid_stress_for_direction(lagna, direction, pl)
            )
        ctx["direction_grid_aspects"] = grid_notes
    return ctx

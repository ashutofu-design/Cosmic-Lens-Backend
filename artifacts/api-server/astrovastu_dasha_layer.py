"""
Mahadasha + Antardasha as a single active-timing layer for AstroVastu.
TB2 (MD) and TB2b (AD) both read from this module.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from astrovastu_rules import get_dasha_active_direction, get_planet_direction


def _norm_planet(name: str) -> str:
    n = (name or "").strip()
    if not n:
        return ""
    return n[0].upper() + n[1:].lower() if len(n) > 1 else n.upper()


def active_dasha_lords(ctx: Dict[str, Any]) -> Dict[str, str]:
    """Resolved MD + AD lords from kundli context."""
    md = _norm_planet(ctx.get("current_mahadasha") or "")
    ad = _norm_planet(ctx.get("current_antardasha") or "")
    return {"maha": md, "antar": ad}


def dasha_directions(ctx: Dict[str, Any]) -> List[str]:
    """Distinct compass directions activated by current MD and AD."""
    dirs: List[str] = []
    seen: set[str] = set()
    for lord in active_dasha_lords(ctx).values():
        if not lord:
            continue
        info = get_dasha_active_direction(lord) or {}
        d = (info.get("direction") or get_planet_direction(lord) or "").strip()
        if d and d not in seen:
            seen.add(d)
            dirs.append(d)
    return dirs


def dasha_activation_check(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Whether the combined MD+AD window amplifies chart stress in any direction.
    Used by PRO engine before per-room scoring.
    """
    lords = active_dasha_lords(ctx)
    md, ad = lords.get("maha"), lords.get("antar")
    if not md and not ad:
        return {"active": False, "lords": lords, "directions": [], "amplified_directions": []}

    directions = dasha_directions(ctx)
    stress_dirs: set[str] = set()
    for hit in ctx.get("chart_stress_hits") or []:
        for d in hit.get("amplifies_dosh_in") or []:
            stress_dirs.add(d)

    amplified = [d for d in directions if d in stress_dirs]
    return {
        "active": bool(md or ad),
        "lords": lords,
        "directions": directions,
        "amplified_directions": amplified,
        "note_en": (
            f"Active {md} Mahadasha"
            + (f" with {ad} Antardasha" if ad else "")
            + (
                f" — stress amplified in {', '.join(amplified)}."
                if amplified
                else " — no extra directional stress from chart conditions."
            )
        ),
    }


def mahadasha_direction_check(
    room_type: str,
    direction: str,
    ctx: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Per-room MD+AD overlay: favourable / conflict / neutral vs chosen direction.
    AD is weighted equally with MD (same layer).
    """
    _ = room_type
    d_long = direction
    lords = active_dasha_lords(ctx)
    md, ad = lords.get("maha"), lords.get("antar")
    if not md:
        return {"applies": False, "kind": "neutral"}

    md_info = get_dasha_active_direction(md) or {}
    md_dir = md_info.get("direction") or get_planet_direction(md)
    ad_dir = None
    if ad:
        ad_info = get_dasha_active_direction(ad) or {}
        ad_dir = ad_info.get("direction") or get_planet_direction(ad)

    favour_dirs = {x for x in (md_dir, ad_dir) if x}
    conflict = d_long in favour_dirs
    # Opposite-sector friction when AD lord differs from MD and neither matches room
    OPPOSITE = {
        "North": "South", "South": "North",
        "East": "West", "West": "East",
        "North-East": "South-West", "South-West": "North-East",
        "North-West": "South-East", "South-East": "North-West",
    }
    md_opp = OPPOSITE.get(md_dir or "")
    ad_opp = OPPOSITE.get(ad_dir or "") if ad_dir else None
    is_conflict = (not conflict) and (d_long == md_opp or (ad_opp and d_long == ad_opp))

    if conflict:
        return {
            "applies": True,
            "kind": "favourable",
            "lords": lords,
            "reason_en": (
                f"Your active dasha ({md}"
                + (f"/{ad}" if ad else "")
                + f") favours the {d_long} zone for this period."
            ),
            "reason_hi": (
                f"Chal rahi dasha ({md}"
                + (f"/{ad}" if ad else "")
                + f") is room ke liye {d_long} ko support karti hai."
            ),
        }
    if is_conflict:
        return {
            "applies": True,
            "kind": "conflict",
            "lords": lords,
            "reason_en": (
                f"Active {md}"
                + (f"–{ad}" if ad else "")
                + f" dasha pulls against {d_long} — remedies or shift advised."
            ),
            "reason_hi": (
                f"Chal rahi {md}"
                + (f"–{ad}" if ad else "")
                + f" dasha {d_long} ke virodhi hai — upaay ya sthan badlein."
            ),
        }
    return {
        "applies": True,
        "kind": "neutral",
        "lords": lords,
        "reason_en": f"Active dasha ({md}" + (f"/{ad}" if ad else "") + ") is neutral for this direction.",
        "reason_hi": f"Chal rahi dasha ({md}" + (f"/{ad}" if ad else "") + ") is disha ke liye tatasthya hai.",
    }


def tie_breaker_dasha_notes(ctx: Dict[str, Any], direction: str) -> List[str]:
    """Human-readable reasons for TB2 / TB2b."""
    notes: List[str] = []
    lords = active_dasha_lords(ctx)
    md, ad = lords.get("maha"), lords.get("antar")
    if md:
        info = get_dasha_active_direction(md) or {}
        ddir = info.get("direction") or get_planet_direction(md)
        if ddir == direction:
            notes.append(f"TB2: {md} Mahadasha actively supports {direction}.")
    if ad and ad != md:
        info = get_dasha_active_direction(ad) or {}
        adir = info.get("direction") or get_planet_direction(ad)
        if adir == direction:
            notes.append(f"TB2b: {ad} Antardasha reinforces {direction} this sub-period.")
    return notes

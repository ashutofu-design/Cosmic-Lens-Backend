"""BCP property ages — D1 4th lord placement + aspects (Bhrigu Chakra rule).

Rule (user spec):
  • House where 4L sits → property ages when that house activates (4, 16, 28…).
  • Houses aspected by 4L → same pattern per aspected house number.
  • Planets conjunct 4L → their aspect houses also contribute BCP ages.
  • D1 primary; D9 merged when available.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from event_timing.marriage.bcp_marriage_ages import (
    _activation_ages_for_house,
    _active_house_for_age,
    _future_ages_from_division_block,
    _house_lord,
    _houses_aspected_by_planet,
    _merge_age_priority_lists,
    _planet_house,
    _planet_sign_idx,
    _planets_conjunct_with,
    _priority_ages_from_shared_houses,
)

_CONJUNCT_GRAHAS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


def resolve_property_lagna_si(kundli: dict) -> Optional[int]:
    """Lagna for property BCP — generic + marriage-style fallbacks (ascendantDeg, etc.)."""
    try:
        from event_timing._shared.generic_timing_engine import _lagna_si

        si = _lagna_si(kundli)
        if si is not None:
            return si
    except Exception:
        pass
    try:
        from event_timing.marriage.marriage_engine_v2 import _resolve_lagna_si_from_kundli

        return _resolve_lagna_si_from_kundli(kundli)
    except Exception:
        return None


def _aspect_house_nums(block: Optional[Dict[str, Any]]) -> List[int]:
    if not isinstance(block, dict):
        return []
    out: List[int] = []
    for row in block.get("aspect_houses") or []:
        if isinstance(row, dict):
            h = row.get("house")
            if isinstance(h, int):
                out.append(h)
    return sorted(set(out))


def _conjunct_aspect_entries_4l(
    fourth_lord: str,
    fourth_lord_house: Optional[int],
    planets: List[dict],
    lagna_si: int,
    *,
    division: str = "D1",
    skip_houses: Optional[Set[int]] = None,
) -> List[Dict[str, Any]]:
    if fourth_lord_house is None:
        return []
    skip = set(skip_houses or ())
    conjuncts = _planets_conjunct_with(
        planets, house=fourth_lord_house, exclude=fourth_lord,
    )
    entries: List[Dict[str, Any]] = []
    seen: Set[int] = set(skip)
    for cp in conjuncts:
        cp_si = _planet_sign_idx(planets, cp)
        if cp_si is None:
            continue
        for h in _houses_aspected_by_planet(cp, cp_si, lagna_si):
            if h in seen:
                continue
            seen.add(h)
            entries.append({
                "house": h,
                "ages": _activation_ages_for_house(h),
                "conjunct_planet": cp,
                "label": (
                    f"{division} — {cp} conjunct 4L ({fourth_lord}) aspects {h}H"
                ),
                "type": "conjunct_aspect",
            })
    return entries


def _bcp_4l_linkage_houses(block: Optional[Dict[str, Any]]) -> Set[int]:
    if not isinstance(block, dict):
        return set()
    houses: Set[int] = set()
    ph = block.get("fourth_lord_house")
    if isinstance(ph, int):
        houses.add(ph)
    for ae in block.get("aspect_houses") or []:
        if isinstance(ae, dict):
            h = ae.get("house")
            if isinstance(h, int):
                houses.add(h)
    for ca in block.get("conjunct_aspect_houses") or []:
        if isinstance(ca, dict):
            h = ca.get("house")
            if isinstance(h, int):
                houses.add(h)
    return houses


def compute_bcp_property_for_division(
    planets: List[dict],
    lagna_si: int,
    *,
    division: str = "D1",
    user_age: Optional[int] = None,
) -> Dict[str, Any]:
    """BCP property-age map for one division from 4L placement + aspects."""
    fourth_lord = _house_lord(lagna_si, 4)
    fourth_lord_house = _planet_house(planets, fourth_lord)
    fourth_lord_si = _planet_sign_idx(planets, fourth_lord)

    sources: List[Dict[str, Any]] = []
    placement_ages: List[int] = []
    if fourth_lord_house is not None:
        placement_ages = _activation_ages_for_house(fourth_lord_house)
        sources.append({
            "source": "4th_lord_placement",
            "house": fourth_lord_house,
            "label": f"{division} — 4L ({fourth_lord}) in {fourth_lord_house}H",
            "ages": placement_ages,
        })

    aspect_entries: List[Dict[str, Any]] = []
    if fourth_lord_si is not None:
        skip_h = {fourth_lord_house} if fourth_lord_house is not None else set()
        for h in _houses_aspected_by_planet(fourth_lord, fourth_lord_si, lagna_si):
            if h in skip_h:
                continue
            ages = _activation_ages_for_house(h)
            aspect_entries.append({
                "house": h,
                "ages": ages,
                "label": f"{division} — 4L ({fourth_lord}) aspects {h}H",
            })
        if aspect_entries:
            sources.append({
                "source": "4th_lord_aspects",
                "houses": aspect_entries,
            })

    skip_for_conj: Set[int] = set()
    if fourth_lord_house is not None:
        skip_for_conj.add(fourth_lord_house)
    conjunct_entries = _conjunct_aspect_entries_4l(
        fourth_lord,
        fourth_lord_house,
        planets,
        lagna_si,
        division=division,
        skip_houses=skip_for_conj,
    )
    conjunct_planets = _planets_conjunct_with(
        planets, house=fourth_lord_house, exclude=fourth_lord,
    )
    if conjunct_entries:
        sources.append({
            "source": "4th_lord_conjunct_aspects",
            "houses": conjunct_entries,
            "label": (
                f"{division} — conjunct with 4L ({fourth_lord}): "
                f"{', '.join(conjunct_planets)}"
            ),
        })

    all_ages: Set[int] = set(placement_ages)
    for ae in aspect_entries:
        all_ages.update(ae.get("ages") or [])
    for ce in conjunct_entries:
        all_ages.update(ce.get("ages") or [])

    sorted_all = sorted(all_ages)
    past = [a for a in sorted_all if user_age is not None and a < user_age]
    future = [a for a in sorted_all if user_age is None or a >= user_age]
    next_act = future[0] if future else None

    return {
        "division": division,
        "lagna_sign_idx": lagna_si,
        "fourth_lord": fourth_lord,
        "fourth_lord_house": fourth_lord_house,
        "conjunct_planets": conjunct_planets,
        "placement_ages": placement_ages,
        "aspect_houses": aspect_entries,
        "conjunct_aspect_houses": conjunct_entries,
        "sources": sources,
        "all_property_ages": sorted_all,
        "past_activation_ages": past,
        "future_activation_ages": future,
        "next_activation_age": next_act,
        "future_bcp_ages": future[:6],
        "current_bcp_house": (
            _active_house_for_age(user_age) if user_age is not None else None
        ),
        "reasoning_summary": (
            f"BCP-{division}: 4L {fourth_lord}@{fourth_lord_house}H; "
            f"aspects {_aspect_house_nums({'aspect_houses': aspect_entries}) or '—'}; "
            f"conjunct {conjunct_planets or '—'}; "
            f"ages {sorted_all[:10]}{'…' if len(sorted_all) > 10 else ''}"
        ),
    }


def compute_bcp_property_ages(
    kundli: dict,
    lagna_si: int,
    user_age: Optional[int] = None,
) -> Dict[str, Any]:
    """D1 + D9 BCP for property from 4L placement and aspects."""
    planets = kundli.get("planets") or []
    d1 = compute_bcp_property_for_division(
        planets, lagna_si, division="D1", user_age=user_age,
    )

    d9_block: Optional[Dict[str, Any]] = None
    merged: Set[int] = set(d1.get("all_property_ages") or [])

    try:
        from event_timing.marriage.marriage_step0 import _load_d9_planets

        d9_lagna_si, d9_planets = _load_d9_planets(kundli)
        if isinstance(d9_lagna_si, int) and d9_planets:
            d9_block = compute_bcp_property_for_division(
                d9_planets, d9_lagna_si, division="D9", user_age=user_age,
            )
            merged.update(d9_block.get("all_property_ages") or [])
    except Exception:
        d9_block = None

    sorted_merged = sorted(merged)
    shared_houses = sorted(
        _bcp_4l_linkage_houses(d1) & _bcp_4l_linkage_houses(d9_block),
    )
    shared_priority = _priority_ages_from_shared_houses(shared_houses, user_age, limit=8)
    d1_future = _future_ages_from_division_block(d1, user_age)
    d9_future = _future_ages_from_division_block(d9_block, user_age)
    focus_ages = _merge_age_priority_lists(
        shared_priority,
        _merge_age_priority_lists(d1_future, d9_future, limit=8),
        limit=12,
    )
    future_priority = [
        a for a in focus_ages if user_age is None or a >= user_age
    ]

    return {
        "fourth_lord": d1.get("fourth_lord"),
        "fourth_lord_house": d1.get("fourth_lord_house"),
        "d1_aspect_houses": _aspect_house_nums(d1),
        "d9_aspect_houses": _aspect_house_nums(d9_block),
        "d1_bcp": d1,
        "d9_bcp": d9_block,
        "d1_bcp_ages": d1_future,
        "d9_bcp_ages": d9_future,
        "shared_4l_linkage_houses": shared_houses,
        "shared_house_priority_ages": shared_priority,
        "all_property_ages": sorted_merged,
        "focus_ages": focus_ages,
        "future_priority_ages": future_priority,
        "next_activation_age": future_priority[0] if future_priority else d1.get("next_activation_age"),
        "user_age": user_age,
        "reasoning_summary": d1.get("reasoning_summary", "")
        + (f" | {d9_block.get('reasoning_summary')}" if d9_block else ""),
    }


def bcp_property_admin_lines(bcp: Dict[str, Any] | None) -> List[str]:
    if not isinstance(bcp, dict):
        return []
    lines: List[str] = []
    lord = bcp.get("fourth_lord") or "?"
    sit = bcp.get("fourth_lord_house")
    asp = bcp.get("d1_aspect_houses") or []
    lines.append(
        f"BCP-4L D1: {lord}@{sit}H · aspects {','.join(str(h) for h in asp) or '—'}"
    )
    d1a = bcp.get("d1_bcp_ages") or []
    d9a = bcp.get("d9_bcp_ages") or []
    if d1a:
        lines.append(f"BCP D1 ages: {', '.join(str(a) for a in d1a[:6])}")
    if d9a:
        lines.append(f"BCP D9 ages: {', '.join(str(a) for a in d9a[:6])}")
    focus = bcp.get("focus_ages") or bcp.get("future_priority_ages") or []
    if focus:
        lines.append(f"BCP focus ages: {', '.join(str(a) for a in focus[:6])}")
    return lines


def build_property_step1_bcp(
    bcp: Dict[str, Any],
    user_age: Optional[int] = None,
) -> Dict[str, Any]:
    """Admin Kaal step1 — D1 4L placement + aspect BCP ages."""
    d1_block = bcp.get("d1_bcp") if isinstance(bcp.get("d1_bcp"), dict) else {}
    lord = bcp.get("fourth_lord")
    sit = bcp.get("fourth_lord_house")
    asp = list(bcp.get("d1_aspect_houses") or [])
    d1a = list(bcp.get("d1_bcp_ages") or [])[:8]
    d9a = list(bcp.get("d9_bcp_ages") or [])[:8]
    focus = list(bcp.get("focus_ages") or bcp.get("future_priority_ages") or [])[:8]
    placement_ages = list(d1_block.get("placement_ages") or [])[:8]

    detail_parts = [f"D1 4L {lord or '?'} in {sit or '?'}H"]
    if asp:
        detail_parts.append(f"aspects {','.join(str(h) for h in asp)}")
    if placement_ages:
        detail_parts.append(
            f"placement ages {','.join(str(a) for a in placement_ages[:4])}"
        )
    if d1a:
        detail_parts.append(f"D1 future {','.join(str(a) for a in d1a[:6])}")
    if d9a:
        detail_parts.append(f"D9 future {','.join(str(a) for a in d9a[:4])}")
    if focus:
        detail_parts.append(f"focus {','.join(str(a) for a in focus[:6])}")

    return {
        "name": "BCP — D1 4L placement + aspects (property ages)",
        "status": "DONE" if lord and sit else "PARTIAL",
        "fourth_lord": lord,
        "fourth_lord_house": sit,
        "d1_aspect_houses": asp,
        "d9_aspect_houses": list(bcp.get("d9_aspect_houses") or []),
        "aspect_houses": d1_block.get("aspect_houses") or [],
        "placement_ages": placement_ages,
        "d1_bcp_ages": d1a,
        "d9_bcp_ages": d9a,
        "focus_ages": focus,
        "all_property_ages": list(bcp.get("all_property_ages") or [])[:16],
        "shared_4l_linkage_houses": list(bcp.get("shared_4l_linkage_houses") or []),
        "next_activation_age": bcp.get("next_activation_age"),
        "user_age": user_age if user_age is not None else bcp.get("user_age"),
        "bcp_property_ages": bcp,
        "rule": (
            "4L jahan baithe + jahan aspect kare — us house number ke BCP ages "
            "(h, h+12, h+24…); conjunct graha ke aspect houses bhi."
        ),
        "detail": " · ".join(detail_parts),
    }

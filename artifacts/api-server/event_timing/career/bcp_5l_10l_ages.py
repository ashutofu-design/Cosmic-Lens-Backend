"""BCP ages — 5th-lord + 10th-lord (change/speculation + karma)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from event_timing.career.bcp_career_ages import (
    _activation_ages_for_house,
    _dual_lordship_bcp_entries,
    _house_lord,
    _houses_aspected_by_planet,
    _planet_house,
    _planet_sign_idx,
)

_WEIGHTS = {
    "5th_lord_placement": 5.0, "5th_lord_dual_sign_houses": 3.0, "5th_lord_aspects": 5.0,
    "10th_lord_placement": 4.5, "10th_lord_dual_sign_houses": 3.0, "10th_lord_aspects": 4.5,
}
_CLUSTER_BONUS = 1.5
_CLUSTER_MAX = 3.0


def _lord_sources(planets, lagna_si, house_num, *, division, prefix, label):
    lord = _house_lord(lagna_si, house_num)
    lord_house = _planet_house(planets, lord)
    lord_si = _planet_sign_idx(planets, lord)
    sources, all_ages = [], set()
    pk, dk, ak = f"{prefix}_placement", f"{prefix}_dual_sign_houses", f"{prefix}_aspects"
    if lord_house is not None:
        ages = _activation_ages_for_house(lord_house)
        all_ages.update(ages)
        sources.append({"source": pk, "lord": lord, "house": lord_house,
                        "label": f"{division} — {label} ({lord}) in {lord_house}H", "ages": ages})
    dual = _dual_lordship_bcp_entries(lord, lagna_si, placement_house=lord_house, label_prefix=label)
    if dual:
        sources.append({"source": dk, "lord": lord, "houses": dual})
        for de in dual:
            all_ages.update(de.get("ages") or [])
    asp_rows = []
    if lord_si is not None:
        skip = {lord_house} if lord_house is not None else set()
        skip.update(e["house"] for e in dual)
        for h in _houses_aspected_by_planet(lord, lord_si, lagna_si):
            if h in skip:
                continue
            ages = _activation_ages_for_house(h)
            asp_rows.append({"house": h, "ages": ages, "label": f"{division} — {label} ({lord}) aspects {h}H"})
            all_ages.update(ages)
        if asp_rows:
            sources.append({"source": ak, "lord": lord, "houses": asp_rows})
    return sources, all_ages


def compute_bcp_5l_10l_ages(kundli: dict, lagna_si: int, user_age: Optional[int] = None,
                            birth_dt: Optional[datetime] = None) -> Dict[str, Any]:
    _ = birth_dt
    planets = kundli.get("planets") or []
    s5, a5 = _lord_sources(planets, lagna_si, 5, division="D1", prefix="5th_lord", label="5L")
    s10, a10 = _lord_sources(planets, lagna_si, 10, division="D1", prefix="10th_lord", label="10L")
    all_ages = sorted(a5 | a10)
    fifth_lord, tenth_lord = _house_lord(lagna_si, 5), _house_lord(lagna_si, 10)

    def _asp(src, key):
        return [e for s in src if s.get("source") == key for e in (s.get("houses") or [])]

    d1 = {
        "division": "D1", "fifth_lord": fifth_lord, "fifth_lord_house": _planet_house(planets, fifth_lord),
        "tenth_lord": tenth_lord, "tenth_lord_house": _planet_house(planets, tenth_lord),
        "aspect_houses_5l": _asp(s5, "5th_lord_aspects"),
        "aspect_houses_10l": _asp(s10, "10th_lord_aspects"),
        "sources": s5 + s10, "all_ages": all_ages,
    }
    future_m = [a for a in all_ages if user_age is None or a >= user_age]
    return {
        **{k: d1[k] for k in ("fifth_lord", "fifth_lord_house", "tenth_lord", "tenth_lord_house",
                              "aspect_houses_5l", "aspect_houses_10l", "sources")},
        "d1_bcp": d1, "all_ages": all_ages,
        "future_priority_ages": future_m[:8],
        "next_activation_age": future_m[0] if future_m else None,
        "reasoning_summary": f"BCP-D1: 5L {fifth_lord} · 10L {tenth_lord}; ages {all_ages[:12]}",
    }

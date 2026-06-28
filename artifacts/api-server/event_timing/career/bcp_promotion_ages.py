"""BCP promotion ages — 11th-lord + 10th-lord placement & aspects (labha + karma).

Mirrors job BCP (10L+6L) but promotion axis = 11L (gains) + 10L (recognition).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from event_timing.career.bcp_career_ages import (
    _activation_ages_for_house,
    _active_house_for_age,
    _dual_lordship_bcp_entries,
    _house_lord,
    _houses_aspected_by_planet,
    _planet_house,
    _planet_sign_idx,
)

_BCP_MAX_AGE = 96
_BCP_SOURCE_WEIGHTS = {
    "11th_lord_placement": 5.0,
    "11th_lord_dual_sign_houses": 3.0,
    "11th_lord_aspects": 5.0,
    "10th_lord_placement": 4.5,
    "10th_lord_dual_sign_houses": 3.0,
    "10th_lord_aspects": 4.5,
}
_BCP_CLUSTER_NEIGHBOR_BONUS = 1.5
_BCP_CLUSTER_MAX_BONUS = 3.0


def _lord_bcp_sources(
    planets: List[dict],
    lagna_si: int,
    house_num: int,
    *,
    division: str,
    source_prefix: str,
    label_prefix: str,
) -> Tuple[List[Dict[str, Any]], Set[int]]:
    lord = _house_lord(lagna_si, house_num)
    lord_house = _planet_house(planets, lord)
    lord_si = _planet_sign_idx(planets, lord)
    sources: List[Dict[str, Any]] = []
    all_ages: Set[int] = set()

    placement_key = f"{source_prefix}_placement"
    dual_key = f"{source_prefix}_dual_sign_houses"
    aspect_key = f"{source_prefix}_aspects"

    if lord_house is not None:
        placement_ages = _activation_ages_for_house(lord_house)
        all_ages.update(placement_ages)
        sources.append({
            "source": placement_key,
            "lord": lord,
            "house": lord_house,
            "label": f"{division} — {label_prefix} ({lord}) in {lord_house}H",
            "ages": placement_ages,
        })

    dual_entries = _dual_lordship_bcp_entries(
        lord, lagna_si, placement_house=lord_house, label_prefix=label_prefix,
    )
    if dual_entries:
        sources.append({
            "source": dual_key,
            "lord": lord,
            "houses": dual_entries,
        })
        for de in dual_entries:
            all_ages.update(de.get("ages") or [])

    aspect_entries: List[Dict[str, Any]] = []
    if lord_si is not None:
        skip_h = {lord_house} if lord_house is not None else set()
        skip_h.update(e["house"] for e in dual_entries)
        for h in _houses_aspected_by_planet(lord, lord_si, lagna_si):
            if h in skip_h:
                continue
            ages = _activation_ages_for_house(h)
            aspect_entries.append({
                "house": h,
                "ages": ages,
                "label": f"{division} — {label_prefix} ({lord}) aspects {h}H",
            })
            all_ages.update(ages)
        if aspect_entries:
            sources.append({
                "source": aspect_key,
                "lord": lord,
                "houses": aspect_entries,
            })

    return sources, all_ages


def compute_bcp_promotion_division(
    planets: List[dict],
    lagna_si: int,
    *,
    division: str = "D1",
    user_age: Optional[int] = None,
) -> Dict[str, Any]:
    """BCP promotion ages — 11L + 10L on one division."""
    eleventh_lord = _house_lord(lagna_si, 11)
    tenth_lord = _house_lord(lagna_si, 10)
    eleventh_lord_house = _planet_house(planets, eleventh_lord)
    tenth_lord_house = _planet_house(planets, tenth_lord)

    sources_11, ages_11 = _lord_bcp_sources(
        planets, lagna_si, 11,
        division=division, source_prefix="11th_lord", label_prefix="11L",
    )
    sources_10, ages_10 = _lord_bcp_sources(
        planets, lagna_si, 10,
        division=division, source_prefix="10th_lord", label_prefix="10L",
    )
    sources = sources_11 + sources_10
    all_ages = sorted(ages_11 | ages_10)

    past = [a for a in all_ages if user_age is not None and a < user_age]
    future = [a for a in all_ages if user_age is None or a >= user_age]

    def _aspect_rows(src_list: list, key: str) -> list:
        return [
            e for s in src_list
            if s.get("source") == key
            for e in (s.get("houses") or [])
        ]

    aspect_11 = _aspect_rows(sources_11, "11th_lord_aspects")
    aspect_10 = _aspect_rows(sources_10, "10th_lord_aspects")

    return {
        "division": division,
        "eleventh_lord": eleventh_lord,
        "eleventh_lord_house": eleventh_lord_house,
        "tenth_lord": tenth_lord,
        "tenth_lord_house": tenth_lord_house,
        "aspect_houses_11l": aspect_11,
        "aspect_houses_10l": aspect_10,
        "sources": sources,
        "all_promotion_ages": all_ages,
        "past_activation_ages": past,
        "future_activation_ages": future,
        "next_activation_age": future[0] if future else None,
        "last_passed_bcp_age": past[-1] if past else None,
        "current_bcp_house": (
            _active_house_for_age(user_age) if user_age is not None else None
        ),
        "reasoning_summary": (
            f"BCP-{division}: 11L {eleventh_lord}@{eleventh_lord_house}H; "
            f"10L {tenth_lord}@{tenth_lord_house}H; "
            f"ages {all_ages[:12]}{'…' if len(all_ages) > 12 else ''}"
        ),
    }


def _score_bcp_ages(d1: Dict[str, Any], *, user_age: Optional[int] = None) -> List[Dict[str, Any]]:
    by_age: Dict[int, Dict[str, Any]] = {}
    division = d1.get("division") or "D1"
    for src in d1.get("sources") or []:
        kind = src.get("source")
        weight = _BCP_SOURCE_WEIGHTS.get(kind, 0.0)
        if not weight:
            continue
        if kind and str(kind).endswith("_placement"):
            rows = [{"house": src.get("house"), "ages": src.get("ages") or [], "label": src.get("label")}]
        else:
            rows = src.get("houses") or []
        for row in rows:
            for age in row.get("ages") or []:
                if not isinstance(age, int):
                    continue
                ent = by_age.setdefault(age, {
                    "age": age, "score": 0.0, "rules": set(), "houses": set(),
                })
                ent["score"] += weight
                ent["rules"].add(kind)
                if isinstance(row.get("house"), int):
                    ent["houses"].add(row["house"])

    ages_set = set(by_age)
    for age, row in by_age.items():
        neighbors = sorted(a for a in ages_set if a != age and abs(a - age) <= 1)
        if neighbors:
            row["score"] += min(
                _BCP_CLUSTER_MAX_BONUS,
                len(neighbors) * _BCP_CLUSTER_NEIGHBOR_BONUS,
            )

    out = []
    for row in by_age.values():
        out.append({
            "age": row["age"],
            "score": round(float(row["score"]), 2),
            "rules": sorted(row["rules"]),
            "houses": sorted(row["houses"]),
            "is_future": user_age is None or row["age"] >= user_age,
            "division": division,
        })
    out.sort(key=lambda r: (-r["score"], r["age"]))
    for i, r in enumerate(out, 1):
        r["rank"] = i
    return out


def compute_bcp_promotion_ages(
    kundli: dict,
    lagna_si: int,
    user_age: Optional[int] = None,
    birth_dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    _ = birth_dt
    planets = kundli.get("planets") or []
    d1 = compute_bcp_promotion_division(planets, lagna_si, division="D1", user_age=user_age)
    all_ages = d1.get("all_promotion_ages") or []
    scored = _score_bcp_ages(d1, user_age=user_age)
    priority = [r["age"] for r in scored]
    future_pri = [a for a in priority if user_age is None or a >= user_age]
    future_m = [a for a in all_ages if user_age is None or a >= user_age]

    return {
        "eleventh_lord": d1["eleventh_lord"],
        "eleventh_lord_house": d1["eleventh_lord_house"],
        "tenth_lord": d1["tenth_lord"],
        "tenth_lord_house": d1["tenth_lord_house"],
        "aspect_houses_11l": d1.get("aspect_houses_11l"),
        "aspect_houses_10l": d1.get("aspect_houses_10l"),
        "sources": d1["sources"],
        "d1_bcp": d1,
        "all_promotion_ages": all_ages,
        "bcp_age_scores": scored,
        "priority_promotion_ages": priority,
        "future_priority_ages": future_pri,
        "primary_priority_age": future_pri[0] if future_pri else None,
        "next_activation_age": future_m[0] if future_m else None,
        "reasoning_summary": d1.get("reasoning_summary", ""),
        "timing_mode": _timing_mode(d1, user_age, all_ages),
    }


def _timing_mode(bcp: dict, user_age: Optional[int], all_ages: list) -> str:
    if user_age is None:
        return "standard"
    if user_age in all_ages:
        return "current_bcp_year"
    nxt = bcp.get("next_activation_age")
    if nxt is not None and nxt - user_age <= 2:
        return "upcoming_bcp"
    last = bcp.get("last_passed_bcp_age")
    if last and user_age - last >= 1:
        return "missed_bcp_recent"
    return "standard"


def format_bcp_promotion_age_list(d1: Dict[str, Any]) -> List[Dict[str, Any]]:
    labels = {
        "11th_lord_placement": "11L placement",
        "11th_lord_dual_sign_houses": "11L dual-sign",
        "11th_lord_aspects": "11L aspect",
        "10th_lord_placement": "10L placement",
        "10th_lord_dual_sign_houses": "10L dual-sign",
        "10th_lord_aspects": "10L aspect",
    }
    rows: List[Dict[str, Any]] = []
    div = d1.get("division") or "D1"
    for src in d1.get("sources") or []:
        kind = src.get("source")
        rule = labels.get(kind, kind)
        if kind and str(kind).endswith("_placement"):
            rows.append({"division": div, "rule": rule, "detail": src.get("label"), "ages": src.get("ages") or []})
        else:
            for h in src.get("houses") or []:
                rows.append({"division": div, "rule": rule, "detail": h.get("label"), "ages": h.get("ages") or []})
    return rows

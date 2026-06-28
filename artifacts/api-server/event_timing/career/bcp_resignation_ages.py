"""BCP resignation ages — 12th-lord + 6th-lord placement & aspects (exit + service end)."""

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

_BCP_SOURCE_WEIGHTS = {
    "12th_lord_placement": 5.0,
    "12th_lord_dual_sign_houses": 3.0,
    "12th_lord_aspects": 5.0,
    "6th_lord_placement": 4.0,
    "6th_lord_dual_sign_houses": 2.5,
    "6th_lord_aspects": 4.0,
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
        sources.append({"source": dual_key, "lord": lord, "houses": dual_entries})
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
            sources.append({"source": aspect_key, "lord": lord, "houses": aspect_entries})

    return sources, all_ages


def compute_bcp_resignation_division(
    planets: List[dict],
    lagna_si: int,
    *,
    division: str = "D1",
) -> Dict[str, Any]:
    twelfth_lord = _house_lord(lagna_si, 12)
    sixth_lord = _house_lord(lagna_si, 6)
    sources_12, ages_12 = _lord_bcp_sources(
        planets, lagna_si, 12,
        division=division, source_prefix="12th_lord", label_prefix="12L",
    )
    sources_6, ages_6 = _lord_bcp_sources(
        planets, lagna_si, 6,
        division=division, source_prefix="6th_lord", label_prefix="6L",
    )
    all_ages = sorted(ages_12 | ages_6)

    def _asp_rows(src_list: list, key: str) -> list:
        return [e for s in src_list if s.get("source") == key for e in (s.get("houses") or [])]

    return {
        "division": division,
        "twelfth_lord": twelfth_lord,
        "twelfth_lord_house": _planet_house(planets, twelfth_lord),
        "sixth_lord": sixth_lord,
        "sixth_lord_house": _planet_house(planets, sixth_lord),
        "aspect_houses_12l": _asp_rows(sources_12, "12th_lord_aspects"),
        "aspect_houses_6l": _asp_rows(sources_6, "6th_lord_aspects"),
        "sources": sources_12 + sources_6,
        "all_exit_ages": all_ages,
        "reasoning_summary": (
            f"BCP-{division}: 12L {twelfth_lord} · 6L {sixth_lord}; ages {all_ages[:12]}"
        ),
    }


def _score_bcp_ages(d1: Dict[str, Any], *, user_age: Optional[int] = None) -> List[Dict[str, Any]]:
    by_age: Dict[int, Dict[str, Any]] = {}
    for src in d1.get("sources") or []:
        kind = src.get("source")
        weight = _BCP_SOURCE_WEIGHTS.get(kind, 0.0)
        if not weight:
            continue
        rows = [{"house": src.get("house"), "ages": src.get("ages") or []}] if str(kind).endswith("_placement") else (src.get("houses") or [])
        for row in rows:
            for age in row.get("ages") or []:
                if not isinstance(age, int):
                    continue
                ent = by_age.setdefault(age, {"age": age, "score": 0.0, "rules": set()})
                ent["score"] += weight
                ent["rules"].add(kind)
    ages_set = set(by_age)
    for age, row in by_age.items():
        neighbors = [a for a in ages_set if a != age and abs(a - age) <= 1]
        if neighbors:
            row["score"] += min(_BCP_CLUSTER_MAX_BONUS, len(neighbors) * _BCP_CLUSTER_NEIGHBOR_BONUS)
    out = [{"age": r["age"], "score": round(r["score"], 2), "rules": sorted(r["rules"]),
            "is_future": user_age is None or r["age"] >= user_age} for r in by_age.values()]
    out.sort(key=lambda r: (-r["score"], r["age"]))
    return out


def compute_bcp_resignation_ages(
    kundli: dict,
    lagna_si: int,
    user_age: Optional[int] = None,
    birth_dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    _ = birth_dt
    planets = kundli.get("planets") or []
    d1 = compute_bcp_resignation_division(planets, lagna_si, division="D1")
    all_ages = d1.get("all_exit_ages") or []
    scored = _score_bcp_ages(d1, user_age=user_age)
    priority = [r["age"] for r in scored]
    future_pri = [a for a in priority if user_age is None or a >= user_age]
    future_m = [a for a in all_ages if user_age is None or a >= user_age]
    return {
        "twelfth_lord": d1["twelfth_lord"],
        "twelfth_lord_house": d1["twelfth_lord_house"],
        "sixth_lord": d1["sixth_lord"],
        "sixth_lord_house": d1["sixth_lord_house"],
        "aspect_houses_12l": d1.get("aspect_houses_12l"),
        "aspect_houses_6l": d1.get("aspect_houses_6l"),
        "sources": d1["sources"],
        "d1_bcp": d1,
        "all_exit_ages": all_ages,
        "bcp_age_scores": scored,
        "future_priority_ages": future_pri,
        "next_activation_age": future_m[0] if future_m else None,
        "reasoning_summary": d1.get("reasoning_summary", ""),
    }


def format_bcp_resignation_age_list(d1: Dict[str, Any]) -> List[Dict[str, Any]]:
    labels = {
        "12th_lord_placement": "12L placement",
        "12th_lord_dual_sign_houses": "12L dual-sign",
        "12th_lord_aspects": "12L aspect",
        "6th_lord_placement": "6L placement",
        "6th_lord_dual_sign_houses": "6L dual-sign",
        "6th_lord_aspects": "6L aspect",
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

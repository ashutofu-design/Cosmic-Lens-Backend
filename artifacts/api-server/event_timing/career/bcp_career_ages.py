"""Bhrigu Chakra Paddhati (BCP) — 10th-lord + 6th-lord placement + aspect job ages.

Rules (user spec):
  • House where 10L sits → job/career ages when that HOUSE number activates:
      e.g. 10L in 6H → ages 6, 18, 30, 42…
  • Houses aspected by 10L → same pattern for each aspected house number.
  • House where 6L sits → job/service ages (same BCP cycle).
  • Houses aspected by 6L → same pattern.
  • Dual-sign 10L/6L (Mars/Mercury/Jupiter/Venus/Saturn): har owned rashi
    jis ghar se lagna se aati hai, us ghar ke BCP ages bhi.
  • D1 primary chart (mirrors marriage BCP starting from 7L on D1).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

_SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun",
    5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter",
    9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
_SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_PLANET_OWN_SIGNS: Dict[str, Tuple[int, ...]] = {
    "Mars": (0, 7),
    "Mercury": (2, 5),
    "Jupiter": (8, 11),
    "Venus": (1, 6),
    "Saturn": (9, 10),
}

_BCP_MAX_AGE = 96
_BCP_WINDOW_BOOST = 3.5
_BCP_NEAR_YEAR_BOOST = 2.0
_BCP_MISSED_RECENT_BOOST = 4.0
_BCP_CURRENT_DASHA_BOOST = 5.0
_MISSED_BCP_YEARS_THRESHOLD = 2
_RECENT_HORIZON_DAYS = 365
_BCP_SOURCE_WEIGHTS = {
    "10th_lord_placement": 5.0,
    "10th_lord_dual_sign_houses": 3.0,
    "10th_lord_aspects": 5.0,
    "6th_lord_placement": 4.0,
    "6th_lord_dual_sign_houses": 2.5,
    "6th_lord_aspects": 4.0,
}
_BCP_CLUSTER_NEIGHBOR_BONUS = 1.5
_BCP_CLUSTER_MAX_BONUS = 3.0


def _house_lord(lagna_si: int, house: int) -> str:
    return _SIGN_LORDS[(lagna_si + house - 1) % 12]


def _planet_house(planets: List[dict], pname: str) -> Optional[int]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == pname:
            h = p.get("house")
            if isinstance(h, int) and 1 <= h <= 12:
                return h
    return None


def _planet_sign_idx(planets: List[dict], pname: str) -> Optional[int]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == pname:
            si = p.get("sign_idx")
            if isinstance(si, int):
                return si % 12
            s = p.get("sign")
            if isinstance(s, str) and s in _SIGN_NAMES:
                return _SIGN_NAMES.index(s)
    return None


def _house_from_sign(lagna_si: int, sign_si: int) -> int:
    return (sign_si - lagna_si) % 12 + 1


def _dual_lordship_bcp_entries(
    lord: str,
    lagna_si: int,
    *,
    placement_house: Optional[int] = None,
    label_prefix: str,
) -> List[Dict[str, Any]]:
    owned = _PLANET_OWN_SIGNS.get(lord)
    if not owned:
        return []
    entries: List[Dict[str, Any]] = []
    for sign_si in owned:
        h = _house_from_sign(lagna_si, sign_si)
        if placement_house is not None and h == placement_house:
            continue
        ages = _activation_ages_for_house(h)
        entries.append({
            "house": h,
            "sign": _SIGN_NAMES[sign_si],
            "ages": ages,
            "label": (
                f"{label_prefix} ({lord}) owned sign {_SIGN_NAMES[sign_si]} "
                f"→ {h}H BCP"
            ),
        })
    return entries


def _aspects_target(aspector: str, ap_si: int, target_si: int) -> bool:
    diff = (target_si - ap_si) % 12 + 1
    if diff == 7:
        return True
    if aspector == "Mars" and diff in (4, 8):
        return True
    if aspector == "Jupiter" and diff in (5, 9):
        return True
    if aspector in ("Saturn", "Rahu", "Ketu") and diff in (3, 10):
        return True
    return False


def _houses_aspected_by_planet(
    planet: str, planet_si: int, lagna_si: int,
) -> List[int]:
    out: List[int] = []
    for h in range(1, 13):
        target_si = (lagna_si + h - 1) % 12
        if _aspects_target(planet, planet_si, target_si):
            out.append(h)
    return out


def _activation_ages_for_house(house: int, max_age: int = _BCP_MAX_AGE) -> List[int]:
    if not (1 <= house <= 12):
        return []
    ages: List[int] = []
    a = house
    while a <= max_age:
        ages.append(a)
        a += 12
    return ages


def _active_house_for_age(age: int) -> int:
    if age < 1:
        return 1
    return ((age - 1) % 12) + 1


def _lord_bcp_sources(
    planets: List[dict],
    lagna_si: int,
    house_num: int,
    *,
    division: str,
    source_prefix: str,
    label_prefix: str,
) -> Tuple[List[Dict[str, Any]], Set[int]]:
    """BCP sources for one house lord (placement + dual-sign + aspects)."""
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
            "label": f"{division} — {label_prefix} ({lord}) owned signs → houses",
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


def compute_bcp_for_division(
    planets: List[dict],
    lagna_si: int,
    *,
    division: str = "D1",
    user_age: Optional[int] = None,
) -> Dict[str, Any]:
    """BCP job-age map for one division — 10L + 6L placement and aspects."""
    tenth_lord = _house_lord(lagna_si, 10)
    sixth_lord = _house_lord(lagna_si, 6)
    tenth_lord_house = _planet_house(planets, tenth_lord)
    sixth_lord_house = _planet_house(planets, sixth_lord)

    sources_10, ages_10 = _lord_bcp_sources(
        planets, lagna_si, 10,
        division=division,
        source_prefix="10th_lord",
        label_prefix="10L",
    )
    sources_6, ages_6 = _lord_bcp_sources(
        planets, lagna_si, 6,
        division=division,
        source_prefix="6th_lord",
        label_prefix="6L",
    )
    sources = sources_10 + sources_6
    all_ages = sorted(ages_10 | ages_6)

    past = [a for a in all_ages if user_age is not None and a < user_age]
    future = [a for a in all_ages if user_age is None or a >= user_age]
    next_act = future[0] if future else None
    last_passed = past[-1] if past else None

    upcoming_year_ages: List[int] = []
    if user_age is not None:
        for a in all_ages:
            if user_age <= a <= user_age + 1:
                upcoming_year_ages.append(a)

    dual_10 = [
        e["house"]
        for s in sources_10
        if s.get("source") == "10th_lord_dual_sign_houses"
        for e in (s.get("houses") or [])
    ]
    dual_6 = [
        e["house"]
        for s in sources_6
        if s.get("source") == "6th_lord_dual_sign_houses"
        for e in (s.get("houses") or [])
    ]

    aspect_10 = [
        e for s in sources_10
        if s.get("source") == "10th_lord_aspects"
        for e in (s.get("houses") or [])
    ]
    aspect_6 = [
        e for s in sources_6
        if s.get("source") == "6th_lord_aspects"
        for e in (s.get("houses") or [])
    ]

    return {
        "division": division,
        "lagna_sign_idx": lagna_si,
        "tenth_lord": tenth_lord,
        "tenth_lord_house": tenth_lord_house,
        "sixth_lord": sixth_lord,
        "sixth_lord_house": sixth_lord_house,
        "dual_sign_houses_10l": dual_10,
        "dual_sign_houses_6l": dual_6,
        "aspect_houses_10l": aspect_10,
        "aspect_houses_6l": aspect_6,
        "sources": sources,
        "all_job_ages": all_ages,
        "past_activation_ages": past,
        "future_activation_ages": future,
        "next_activation_age": next_act,
        "last_passed_bcp_age": last_passed,
        "years_since_last_bcp": (
            (user_age - last_passed) if (user_age is not None and last_passed) else None
        ),
        "years_to_next_bcp": (
            (next_act - user_age) if (user_age is not None and next_act is not None) else None
        ),
        "current_bcp_house": (
            _active_house_for_age(user_age) if user_age is not None else None
        ),
        "upcoming_year_bcp_ages": upcoming_year_ages,
        "reasoning_summary": (
            f"BCP-{division}: 10L {tenth_lord}@{tenth_lord_house}H "
            f"(dual {dual_10}, aspects {[e.get('house') for e in aspect_10]}); "
            f"6L {sixth_lord}@{sixth_lord_house}H "
            f"(dual {dual_6}, aspects {[e.get('house') for e in aspect_6]}); "
            f"ages {all_ages[:12]}{'…' if len(all_ages) > 12 else ''}"
        ),
    }


def compute_bcp_career_ages(
    kundli: dict,
    lagna_si: int,
    user_age: Optional[int] = None,
    birth_dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    """D1 BCP job ages from 10L + 6L placement and aspects."""
    _ = birth_dt
    planets = kundli.get("planets") or []
    d1 = compute_bcp_for_division(planets, lagna_si, division="D1", user_age=user_age)
    all_ages = d1.get("all_job_ages") or []
    scored_ages = _score_bcp_ages(d1, user_age=user_age)
    priority_ages = [r["age"] for r in scored_ages]
    future_priority = [a for a in priority_ages if user_age is None or a >= user_age]
    past_m = [a for a in all_ages if user_age is not None and a < user_age]
    future_m = [a for a in all_ages if user_age is None or a >= user_age]

    base = {
        "tenth_lord": d1["tenth_lord"],
        "tenth_lord_house": d1["tenth_lord_house"],
        "sixth_lord": d1["sixth_lord"],
        "sixth_lord_house": d1["sixth_lord_house"],
        "dual_sign_houses_10l": d1.get("dual_sign_houses_10l"),
        "dual_sign_houses_6l": d1.get("dual_sign_houses_6l"),
        "aspect_houses_10l": d1.get("aspect_houses_10l"),
        "aspect_houses_6l": d1.get("aspect_houses_6l"),
        "sources": d1["sources"],
        "d1_bcp": d1,
        "bcp_age_list": format_bcp_age_list(d1),
        "all_job_ages": all_ages,
        "bcp_age_scores": scored_ages,
        "priority_job_ages": priority_ages,
        "future_priority_ages": future_priority,
        "primary_priority_age": future_priority[0] if future_priority else None,
        "past_activation_ages": past_m,
        "future_activation_ages": future_m,
        "next_activation_age": future_m[0] if future_m else None,
        "last_passed_bcp_age": past_m[-1] if past_m else None,
        "years_since_last_bcp": (
            (user_age - past_m[-1]) if (user_age is not None and past_m) else None
        ),
        "years_to_next_bcp": (
            (future_m[0] - user_age) if (user_age is not None and future_m) else None
        ),
        "current_bcp_house": d1.get("current_bcp_house"),
        "upcoming_year_bcp_ages": d1.get("upcoming_year_bcp_ages") or [],
        "reasoning_summary": d1.get("reasoning_summary", ""),
    }
    base.update(resolve_bcp_job_timing_strategy(base, user_age))
    return base


def _iter_bcp_source_hits(block: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(block, dict):
        return []
    division = block.get("division") or "D1"
    hits: List[Dict[str, Any]] = []
    for src in block.get("sources") or []:
        kind = src.get("source")
        weight = _BCP_SOURCE_WEIGHTS.get(kind, 0.0)
        if not weight:
            continue
        if kind.endswith("_placement"):
            rows = [{
                "house": src.get("house"),
                "ages": src.get("ages") or [],
                "label": src.get("label"),
                "lord": src.get("lord"),
            }]
        else:
            rows = src.get("houses") or []
        for row in rows:
            for age in row.get("ages") or []:
                if not isinstance(age, int):
                    continue
                hits.append({
                    "age": age,
                    "division": division,
                    "source": kind,
                    "lord": src.get("lord") or row.get("lord"),
                    "house": row.get("house"),
                    "label": row.get("label"),
                    "weight": weight,
                })
    return hits


def _score_bcp_ages(
    d1: Dict[str, Any],
    *,
    user_age: Optional[int] = None,
) -> List[Dict[str, Any]]:
    by_age: Dict[int, Dict[str, Any]] = {}
    for hit in _iter_bcp_source_hits(d1):
        age = hit["age"]
        row = by_age.setdefault(age, {
            "age": age,
            "score": 0.0,
            "sources": [],
            "rules": set(),
            "lords": set(),
            "houses": set(),
            "cluster_neighbors": [],
        })
        row["score"] += float(hit["weight"])
        row["sources"].append(hit)
        row["rules"].add(hit["source"])
        if hit.get("lord"):
            row["lords"].add(hit["lord"])
        if isinstance(hit.get("house"), int):
            row["houses"].add(hit["house"])

    ages = set(by_age)
    for age, row in by_age.items():
        neighbors = sorted(a for a in ages if a != age and abs(a - age) <= 1)
        if neighbors:
            cluster_bonus = min(
                _BCP_CLUSTER_MAX_BONUS,
                len(neighbors) * _BCP_CLUSTER_NEIGHBOR_BONUS,
            )
            row["score"] += cluster_bonus
            row["cluster_neighbors"] = neighbors

    out: List[Dict[str, Any]] = []
    for row in by_age.values():
        out.append({
            "age": row["age"],
            "score": round(float(row["score"]), 2),
            "rules": sorted(row["rules"]),
            "lords": sorted(row["lords"]),
            "houses": sorted(row["houses"]),
            "cluster_neighbors": row["cluster_neighbors"],
            "is_future": user_age is None or row["age"] >= user_age,
            "sources": row["sources"],
        })
    out.sort(key=lambda r: (-float(r["score"]), r["age"]))
    for idx, row in enumerate(out, start=1):
        row["rank"] = idx
    return out


def format_bcp_age_list(d1: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Human-readable BCP sources → age rows for UI / LLM."""
    rows: List[Dict[str, Any]] = []
    div = d1.get("division") or "D1"
    rule_labels = {
        "10th_lord_placement": "10L placement",
        "10th_lord_dual_sign_houses": "10L dual-sign house",
        "10th_lord_aspects": "10L aspect",
        "6th_lord_placement": "6L placement",
        "6th_lord_dual_sign_houses": "6L dual-sign house",
        "6th_lord_aspects": "6L aspect",
    }
    for src in d1.get("sources") or []:
        kind = src.get("source")
        rule = rule_labels.get(kind, kind)
        if kind and kind.endswith("_placement"):
            rows.append({
                "division": div,
                "rule": rule,
                "detail": src.get("label"),
                "ages": src.get("ages") or [],
            })
        else:
            for h in src.get("houses") or []:
                rows.append({
                    "division": div,
                    "rule": rule,
                    "detail": h.get("label"),
                    "ages": h.get("ages") or [],
                })
    return rows


def resolve_bcp_job_timing_strategy(
    bcp: Dict[str, Any],
    user_age: Optional[int],
) -> Dict[str, Any]:
    """STEP 1 — BCP job ages first; guides dasha scan (mirrors marriage STEP 0A)."""
    if user_age is None:
        return {
            "timing_mode": "standard",
            "search_horizon_days": _RECENT_HORIZON_DAYS,
            "late_urgent_scan": False,
            "prefer_current_dasha": False,
            "bcp_boost_future_only": True,
            "pipeline_order": "bcp_age→10L/6L→significators→dasha→transit",
            "llm_directive": "User age unknown — use dasha+transit for job window.",
        }

    last_passed = bcp.get("last_passed_bcp_age")
    next_act = bcp.get("next_activation_age")
    upcoming = bcp.get("upcoming_year_bcp_ages") or []
    years_since = bcp.get("years_since_last_bcp")
    years_to_next = bcp.get("years_to_next_bcp")

    if user_age in (bcp.get("all_job_ages") or []):
        if next_act is None or user_age >= next_act:
            return {
                "timing_mode": "current_bcp_year",
                "search_horizon_days": _RECENT_HORIZON_DAYS,
                "late_urgent_scan": True,
                "prefer_current_dasha": True,
                "bcp_boost_future_only": False,
                "primary_reference_age": user_age,
                "pipeline_order": "bcp_age→10L/6L→significators→dasha→transit",
                "llm_directive": (
                    f"User abhi BCP job activation age {user_age} par hai — "
                    "current dasha+transit ko primary batao; is saal naukri window strong."
                ),
            }

    if years_to_next is not None and years_to_next <= 2:
        return {
            "timing_mode": "upcoming_bcp",
            "search_horizon_days": max(_RECENT_HORIZON_DAYS, years_to_next * 366),
            "late_urgent_scan": years_to_next <= 1,
            "prefer_current_dasha": False,
            "bcp_boost_future_only": False,
            "primary_reference_age": next_act,
            "pipeline_order": "bcp_age→10L/6L→significators→dasha→transit",
            "llm_directive": (
                f"BCP next job age {next_act} ({years_to_next} saal mein) — "
                "dasha windows is age ke around align karo."
            ),
        }

    if (
        last_passed is not None
        and years_since is not None
        and years_since >= 1
        and (years_to_next is None or years_to_next > _MISSED_BCP_YEARS_THRESHOLD)
    ):
        return {
            "timing_mode": "missed_bcp_recent",
            "search_horizon_days": _RECENT_HORIZON_DAYS,
            "late_urgent_scan": True,
            "prefer_current_dasha": True,
            "bcp_boost_future_only": True,
            "primary_reference_age": last_passed,
            "pipeline_order": "bcp_age→10L/6L→significators→dasha→transit",
            "llm_directive": (
                f"BCP job age {last_passed} guzar chuka (user ab {user_age}). "
                f"Agla BCP age {next_act} abhi door — pehle current/near-term dasha+transit."
            ),
        }

    if upcoming:
        years_to_first = (upcoming[0] - user_age) if user_age is not None else 99
        return {
            "timing_mode": "upcoming_bcp",
            "search_horizon_days": max(_RECENT_HORIZON_DAYS, years_to_first * 366),
            "late_urgent_scan": years_to_first <= 1,
            "prefer_current_dasha": False,
            "bcp_boost_future_only": False,
            "primary_reference_age": upcoming[0],
            "pipeline_order": "bcp_age→10L/6L→significators→dasha→transit",
            "llm_directive": (
                f"BCP job activation age {upcoming[0]} jaldi aa raha — "
                "near-term dasha+transit check karo."
            ),
        }

    return {
        "timing_mode": "standard",
        "search_horizon_days": _RECENT_HORIZON_DAYS,
        "late_urgent_scan": False,
        "prefer_current_dasha": False,
        "bcp_boost_future_only": True,
        "pipeline_order": "bcp_age→10L/6L→significators→dasha→transit",
        "llm_directive": "Standard BCP job ages + dasha+transit merge.",
    }


def _age_span_in_chunk(
    birth_dt: Optional[datetime],
    start: datetime,
    end: datetime,
) -> Tuple[Optional[int], Optional[int]]:
    if birth_dt is None:
        return None, None
    try:
        min_a = max(0, (start.date() - birth_dt.date()).days // 365)
        max_a = max(0, (end.date() - birth_dt.date()).days // 365)
        return min_a, max_a
    except Exception:
        return None, None


def bcp_boost_for_window(
    bcp: Dict[str, Any],
    birth_dt: Optional[datetime],
    start: datetime,
    end: datetime,
    *,
    now: Optional[datetime] = None,
    strategy: Optional[Dict[str, Any]] = None,
) -> Tuple[float, str]:
    strategy = strategy or {}
    mode = strategy.get("timing_mode", "standard")
    ages = set(bcp.get("all_job_ages") or [])
    score_map = {int(r["age"]): r for r in (bcp.get("bcp_age_scores") or []) if isinstance(r.get("age"), int)}
    if not ages:
        return 0.0, ""

    min_a, max_a = _age_span_in_chunk(birth_dt, start, end)
    now = now or datetime.utcnow()

    if mode == "missed_bcp_recent":
        if start > now + timedelta(days=_RECENT_HORIZON_DAYS):
            return 0.0, ""
        if start <= now + timedelta(days=_RECENT_HORIZON_DAYS):
            return _BCP_MISSED_RECENT_BOOST, "missed-BCP → recent 12mo job window"
        return 0.0, ""

    hits: List[int] = []
    if min_a is not None and max_a is not None:
        for a in ages:
            if min_a <= a <= max_a:
                hits.append(a)

    if hits:
        if strategy.get("bcp_boost_future_only") and min_a is not None:
            last_passed = bcp.get("last_passed_bcp_age")
            if last_passed and min_a < last_passed:
                return 0.0, ""
        best_age = max(hits, key=lambda a: (score_map.get(a) or {}).get("score", 0))
        best_score = float((score_map.get(best_age) or {}).get("score", 0.0))
        boost = _BCP_WINDOW_BOOST + min(4.0, best_score * 0.35)
        return round(boost, 2), (
            f"BCP job age hit {hits} in window; priority age {best_age} "
            f"score={round(best_score, 2)}"
        )

    next_a = bcp.get("primary_priority_age") or bcp.get("next_activation_age")
    if next_a is not None and min_a is not None and abs(next_a - min_a) <= 1:
        return _BCP_NEAR_YEAR_BOOST, f"BCP near next job activation age {next_a}"

    return 0.0, ""

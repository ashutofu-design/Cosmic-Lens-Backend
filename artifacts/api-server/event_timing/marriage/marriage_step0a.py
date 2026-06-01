"""STEP 0A — BCP marriage ages + timing entry plan.

Step 0 owns early/late marriage pace. Step 0A owns BCP age generation,
late-chart BCP focus, and the dasha scan plan consumed by later stages.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from event_timing.marriage.bcp_marriage_ages import (
    _active_house_for_age,
    compute_bcp_marriage_ages,
    resolve_late_marriage_bcp_focus,
)
from event_timing.marriage.marriage_step0 import _load_d9_planets


def _bcp_ages_in_range(
    all_ages: List[int],
    user_age: Optional[int],
    years_ahead: int = 5,
) -> List[int]:
    if user_age is None:
        return [a for a in all_ages if a <= years_ahead + 30][:8]
    hi = user_age + years_ahead
    return [a for a in all_ages if user_age <= a <= hi]


def run_marriage_step0a(
    kundli: dict,
    lagna_si: int,
    *,
    combined_pace: str,
    age_ctx: Dict[str, Any],
    user_age: Optional[int] = None,
    birth_dt: Optional[datetime] = None,
    years_ahead: int = 5,
) -> Dict[str, Any]:
    """STEP 0A — BCP list + late-chart focus ages for later dasha ranking."""
    d9_lagna_si, d9_planets = _load_d9_planets(kundli)

    bcp = compute_bcp_marriage_ages(
        kundli,
        lagna_si,
        user_age=user_age,
        birth_dt=birth_dt,
        d9_lagna_si=d9_lagna_si,
        d9_planets=d9_planets if d9_planets else None,
    )
    bcp_strategy = {
        k: bcp.get(k)
        for k in (
            "timing_mode", "search_horizon_days", "late_urgent_scan",
            "prefer_current_dasha", "bcp_boost_future_only",
            "primary_reference_age", "pipeline_order", "llm_directive",
        )
    }

    late_focus = resolve_late_marriage_bcp_focus(
        bcp,
        marriage_pace=combined_pace,
        user_age=user_age,
        years_ahead=max(years_ahead, 8),
    )

    all_bcp = bcp.get("all_marriage_ages") or []
    priority_ages = bcp.get("future_priority_ages") or []
    focus_ages = late_focus.get("focus_ages") or []
    bcp_next_5y = _bcp_ages_in_range(focus_ages or all_bcp, user_age, years_ahead)
    in_bcp_year = bool(user_age is not None and user_age in all_bcp)

    dasha_entry: List[str] = []
    if user_age is not None:
        dasha_entry.append(f"User age {user_age}.")
    dasha_entry.append(late_focus.get("directive", ""))
    if late_focus.get("between_ages"):
        dasha_entry.append(late_focus["between_ages"])
    if bcp.get("bcp_age_list"):
        dasha_entry.append(
            f"Full BCP list (D1+D9 merged): {all_bcp[:16]}"
            f"{'...' if len(all_bcp) > 16 else ''}"
        )

    primary_ref = (
        late_focus.get("primary_age")
        or bcp_strategy.get("primary_reference_age")
        or bcp.get("next_activation_age")
    )
    if primary_ref is not None:
        bcp_strategy["primary_reference_age"] = primary_ref

    # Chart delay is not the same as age-late. Young delayed charts should
    # keep their BCP focus instead of forcing a near-term 12-month scan.
    bcp_urgent = bool(bcp_strategy.get("late_urgent_scan"))
    if (
        bcp_urgent
        and age_ctx.get("delay_vs_late") == "chart_delay"
        and user_age is not None
    ):
        nxt = bcp.get("next_activation_age")
        if nxt is not None and (nxt - user_age) > 2:
            bcp_urgent = False

    dasha_scan = {
        "late_urgent_scan": bool(age_ctx.get("late_urgent_scan") or bcp_urgent),
        "search_horizon_days": int(
            age_ctx.get("search_horizon_days")
            or bcp_strategy.get("search_horizon_days")
            or 365
        ),
        "prefer_current_dasha": bool(
            bcp_strategy.get("prefer_current_dasha")
            or late_focus.get("mode") == "current_bcp_activation"
        ),
        "bcp_boost_future_only": bool(bcp_strategy.get("bcp_boost_future_only")),
        "timing_mode": bcp_strategy.get("timing_mode"),
        "primary_reference_age": primary_ref,
        "bcp_ages_next_years": bcp_next_5y,
        "bcp_focus_ages": focus_ages,
        "bcp_priority_ages": priority_ages[:8],
        "bcp_age_scores": (bcp.get("bcp_age_scores") or [])[:12],
        "late_bcp_focus": late_focus,
        "all_bcp_ages": all_bcp,
        "in_bcp_activation_year": in_bcp_year,
        "current_bcp_house": (
            _active_house_for_age(user_age) if user_age is not None else None
        ),
        "entry_notes": [x for x in dasha_entry if x],
    }

    return {
        "step0a_version": "bcp_d1_d9_focus_v1",
        "bcp_marriage_ages": bcp,
        "bcp_age_scores": bcp.get("bcp_age_scores") or [],
        "bcp_priority_ages": bcp.get("priority_marriage_ages") or [],
        "bcp_future_priority_ages": priority_ages,
        "bcp_age_list": bcp.get("bcp_age_list") or [],
        "bcp_all_ages_sorted": all_bcp,
        "late_bcp_focus": late_focus,
        "bcp_timing_strategy": bcp_strategy,
        "timing_mode": bcp_strategy.get("timing_mode"),
        "dasha_scan_plan": dasha_scan,
        "reasoning_summary": (
            f"STEP0A: BCP ages {all_bcp}; focus {focus_ages}; "
            f"7L dual houses D1={bcp.get('dual_sign_houses_d1')}"
        ),
        "llm_directive": " | ".join(
            filter(None, [
                late_focus.get("directive"),
                bcp_strategy.get("llm_directive"),
            ])
        )[:600],
    }


def annotate_candidates_bcp_ages(
    candidates: List[Dict[str, Any]],
    bcp: Dict[str, Any],
    birth_dt: Optional[datetime],
    *,
    user_age: Optional[int] = None,
) -> None:
    """Tag each dasha chunk with BCP ages it spans."""
    ages = set(bcp.get("all_marriage_ages") or [])
    if not ages or birth_dt is None:
        return
    try:
        from event_timing.marriage.bcp_marriage_ages import _age_span_in_chunk
    except Exception:
        return
    for c in candidates:
        min_a, max_a = _age_span_in_chunk(birth_dt, c["start"], c["end"])
        if min_a is None:
            continue
        hits = sorted(a for a in ages if min_a <= a <= max_a)
        c["bcp_age_hits"] = hits
        if user_age is not None and min_a <= user_age <= max_a:
            c["covers_current_age"] = True

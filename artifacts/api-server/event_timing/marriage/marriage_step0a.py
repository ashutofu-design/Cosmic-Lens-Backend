"""STEP 0A — BCP marriage ages + timing entry plan.

Step 0 owns early/late marriage pace. Step 0A owns BCP age generation,
late-chart BCP focus, and the dasha scan plan consumed by later stages.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from event_timing.marriage.bcp_marriage_ages import (
    _active_house_for_age,
    _near_bcp_activation_ages,
    compute_bcp_marriage_ages,
    resolve_late_marriage_bcp_focus,
)
from event_timing.marriage.marriage_step0 import _load_d9_planets


def _late_urgent_after_chart_delay_guard(
    bcp_urgent: bool,
    *,
    age_ctx: Dict[str, Any],
    user_age: Optional[int],
    bcp: Dict[str, Any],
    bcp_strategy: Dict[str, Any],
    step0_verdict: Optional[str] = None,
) -> bool:
    """Delayed chart + BCP still ahead → skip near-term 12mo urgent scan."""
    if not (
        bcp_urgent
        and user_age is not None
        and (
            age_ctx.get("delay_vs_late") == "chart_delay"
            or (step0_verdict or "") in ("DELAYED", "LATE")
        )
    ):
        return bcp_urgent
    nxt = bcp.get("next_activation_age")
    mode = bcp_strategy.get("timing_mode")
    focus_pri = bcp_strategy.get("primary_reference_age")
    near_focus = (
        isinstance(focus_pri, int)
        and focus_pri > user_age
        and (focus_pri - user_age) <= 2
    )
    near_raw = _near_bcp_activation_ages(bcp, user_age, within_years=2)
    if near_raw or near_focus:
        return False
    if (
        mode == "upcoming_bcp"
        and nxt is not None
        and nxt > user_age
    ):
        return False
    if (
        mode not in ("current_bcp_year", "upcoming_bcp")
        and nxt is not None
        and (nxt - user_age) > 2
    ):
        return False
    return bcp_urgent


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
    step0_verdict: Optional[str] = None,
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
    from event_timing.marriage.bcp_marriage_ages import _bcp_display_ages_from_current

    bcp_next_5y = _bcp_display_ages_from_current(
        shared_priority=list(bcp.get("shared_house_priority_ages") or []),
        focus_ages=focus_ages,
        all_ages=all_bcp,
        user_age=user_age,
        years_ahead=years_ahead,
        limit=4,
    )
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

    # Delayed late chart: near focus age (27) must not stay in missed_bcp_recent
    # (last incidental 24 passed → wrongly boosts next 12mo over BCP 27).
    _focus_pri = late_focus.get("primary_age")
    if (
        (step0_verdict or "") in ("DELAYED", "LATE")
        and user_age is not None
        and isinstance(_focus_pri, int)
        and _focus_pri > user_age
        and (_focus_pri - user_age) <= 3
    ):
        bcp_strategy["timing_mode"] = "upcoming_bcp"
        bcp_strategy["late_urgent_scan"] = False
        bcp_strategy["prefer_current_dasha"] = False
        bcp_strategy["bcp_boost_future_only"] = False
        bcp_strategy["primary_reference_age"] = _focus_pri
        primary_ref = _focus_pri

    bcp_urgent = _late_urgent_after_chart_delay_guard(
        bool(bcp_strategy.get("late_urgent_scan")),
        age_ctx=age_ctx,
        user_age=user_age,
        bcp=bcp,
        bcp_strategy=bcp_strategy,
        step0_verdict=step0_verdict,
    )

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
        "d1_7l_linkage_houses": bcp.get("d1_7l_linkage_houses") or [],
        "d9_7l_linkage_houses": bcp.get("d9_7l_linkage_houses") or [],
        "shared_7l_linkage_houses": bcp.get("shared_7l_linkage_houses") or [],
        "shared_house_priority_ages": bcp.get("shared_house_priority_ages") or [],
        "d1_7l_placement_house": bcp.get("seventh_lord_house"),
        "d1_7l_aspect_houses": [
            h.get("house")
            for h in (bcp.get("aspect_houses") or [])
            if isinstance(h, dict) and isinstance(h.get("house"), int)
        ],
        "d9_7l_placement_house": ((bcp.get("d9_bcp") or {}).get("seventh_lord_house")),
        "d9_7l_aspect_houses": [
            h.get("house")
            for h in ((bcp.get("d9_bcp") or {}).get("aspect_houses") or [])
            if isinstance(h, dict) and isinstance(h.get("house"), int)
        ],
        "d1_seventh_lord": bcp.get("seventh_lord"),
        "d9_seventh_lord": ((bcp.get("d9_bcp") or {}).get("seventh_lord")),
        "bcp_house_display": bcp.get("bcp_admin_display") or {},
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

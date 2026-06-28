"""STEP 1 — BCP job ages from 10L + 6L placement and aspects (D1).

Mirrors marriage `marriage_step0a.py` but for career/job timing:
  • 10th lord jahan baithe + jahan aspect kare → BCP ages
  • 6th lord jahan baithe + jahan aspect kare → BCP ages
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from event_timing.career.bcp_career_ages import compute_bcp_career_ages


def _bcp_ages_in_range(
    all_ages: List[int],
    user_age: Optional[int],
    years_ahead: int = 8,
) -> List[int]:
    if user_age is None:
        return [a for a in all_ages if a <= years_ahead + 30][:10]
    hi = user_age + years_ahead
    return [a for a in all_ages if user_age <= a <= hi]


def run_career_step1_bcp(
    kundli: dict,
    lagna_si: int,
    *,
    user_age: Optional[int] = None,
    birth_dt: Optional[datetime] = None,
    years_ahead: int = 8,
) -> Dict[str, Any]:
    """STEP 1 — BCP job-age list from 10L + 6L for career timing questions."""
    bcp = compute_bcp_career_ages(
        kundli,
        lagna_si,
        user_age=user_age,
        birth_dt=birth_dt,
    )
    bcp_strategy = {
        k: bcp.get(k)
        for k in (
            "timing_mode", "search_horizon_days", "late_urgent_scan",
            "prefer_current_dasha", "bcp_boost_future_only",
            "primary_reference_age", "pipeline_order", "llm_directive",
        )
    }

    all_bcp = bcp.get("all_job_ages") or []
    priority_ages = bcp.get("future_priority_ages") or []
    focus_ages = priority_ages[:6] or (bcp.get("future_activation_ages") or [])[:6]
    bcp_next = _bcp_ages_in_range(focus_ages or all_bcp, user_age, years_ahead)
    in_bcp_year = bool(user_age is not None and user_age in all_bcp)

    tenth_lord = bcp.get("tenth_lord")
    tenth_house = bcp.get("tenth_lord_house")
    sixth_lord = bcp.get("sixth_lord")
    sixth_house = bcp.get("sixth_lord_house")
    aspect_10 = bcp.get("aspect_houses_10l") or []
    aspect_6 = bcp.get("aspect_houses_6l") or []

    areas: List[Dict[str, Any]] = []
    for src in bcp.get("sources") or []:
        kind = str(src.get("source") or "")
        if kind == "10th_lord_placement":
            areas.append({
                "lord": tenth_lord,
                "role": "10L",
                "type": "placement",
                "house": src.get("house"),
                "ages": src.get("ages") or [],
                "label": src.get("label"),
            })
        elif kind == "6th_lord_placement":
            areas.append({
                "lord": sixth_lord,
                "role": "6L",
                "type": "placement",
                "house": src.get("house"),
                "ages": src.get("ages") or [],
                "label": src.get("label"),
            })
        elif kind in ("10th_lord_dual_sign_houses", "6th_lord_dual_sign_houses"):
            role = "10L" if kind.startswith("10") else "6L"
            lord = tenth_lord if role == "10L" else sixth_lord
            for entry in src.get("houses") or []:
                areas.append({
                    "lord": lord,
                    "role": role,
                    "type": "dual_sign",
                    "house": entry.get("house"),
                    "ages": entry.get("ages") or [],
                    "label": entry.get("label"),
                })
        elif kind in ("10th_lord_aspects", "6th_lord_aspects"):
            role = "10L" if kind.startswith("10") else "6L"
            lord = tenth_lord if role == "10L" else sixth_lord
            for entry in src.get("houses") or []:
                areas.append({
                    "lord": lord,
                    "role": role,
                    "type": "aspect",
                    "house": entry.get("house"),
                    "ages": entry.get("ages") or [],
                    "label": entry.get("label"),
                })

    detail_parts = [
        f"10L {tenth_lord} in {tenth_house}H",
        f"6L {sixth_lord} in {sixth_house}H",
    ]
    if aspect_10:
        detail_parts.append(
            f"10L aspects {[e.get('house') for e in aspect_10]}"
        )
    if aspect_6:
        detail_parts.append(
            f"6L aspects {[e.get('house') for e in aspect_6]}"
        )
    detail_parts.append(f"BCP ages {all_bcp[:14]}{'…' if len(all_bcp) > 14 else ''}")

    return {
        "step1_version": "bcp_10l_6l_v1",
        "tenth_lord": tenth_lord,
        "tenth_lord_house": tenth_house,
        "sixth_lord": sixth_lord,
        "sixth_lord_house": sixth_house,
        "aspect_houses_10l": aspect_10,
        "aspect_houses_6l": aspect_6,
        "dual_sign_houses_10l": bcp.get("dual_sign_houses_10l"),
        "dual_sign_houses_6l": bcp.get("dual_sign_houses_6l"),
        "career_areas": areas,
        "bcp_career_ages": bcp,
        "bcp_age_list": bcp.get("bcp_age_list") or [],
        "all_job_ages": all_bcp,
        "bcp_age_scores": (bcp.get("bcp_age_scores") or [])[:12],
        "priority_job_ages": bcp.get("priority_job_ages") or [],
        "future_priority_ages": priority_ages,
        "bcp_focus_ages": focus_ages,
        "bcp_ages_next_years": bcp_next,
        "in_bcp_activation_year": in_bcp_year,
        "current_bcp_house": bcp.get("current_bcp_house"),
        "next_activation_age": bcp.get("next_activation_age"),
        "bcp_timing_strategy": bcp_strategy,
        "timing_mode": bcp_strategy.get("timing_mode"),
        "llm_directive": bcp_strategy.get("llm_directive"),
        "reasoning_summary": bcp.get("reasoning_summary"),
        "detail": " · ".join(detail_parts),
    }

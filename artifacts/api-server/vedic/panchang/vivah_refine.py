"""Refine merged windows to optimal lagna sub-slots (5-minute precision)."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from vedic.panchang.vivah_context import VivahScanContext
from vedic.panchang.vivah_geo import DayGeo
from vedic.panchang.vivah_lagna import evaluate_vivah_lagna


def refine_window_lagna(
    geo: DayGeo,
    window_start: datetime,
    window_end: datetime,
    ctx: VivahScanContext,
    *,
    min_minutes: int = 90,
    step_min: int = 5,
) -> dict[str, Any] | None:
    """
  Find best sub-window of at least min_minutes with highest lagna score
  and allowed lagna for profile.
    """
    profile = ctx.profile
    best: dict[str, Any] | None = None
    duration_needed = timedelta(minutes=min_minutes)
    t = window_start
    while t + duration_needed <= window_end:
        sub_end = t + duration_needed
        scores: list[int] = []
        lagnas: list[str] = []
        veto = False
        tt = t
        while tt < sub_end:
            ev = evaluate_vivah_lagna(
                tt, lat=ctx.lat, lng=ctx.lng, tz_h=ctx.tz_h,
            )
            if ev.get("veto"):
                veto = True
                break
            lag = ev.get("lagna", "")
            if lag and lag not in profile.allowed_lagnas:
                veto = True
                break
            scores.append(int(ev["score"]))
            lagnas.append(lag)
            tt += timedelta(minutes=step_min)
        if not veto and scores:
            avg = sum(scores) / len(scores)
            if best is None or avg > best["lagna_avg"]:
                best = {
                    "start": t,
                    "end": sub_end,
                    "lagna_avg": avg,
                    "lagna": lagnas[len(lagnas) // 2],
                }
        t += timedelta(minutes=step_min)
    return best

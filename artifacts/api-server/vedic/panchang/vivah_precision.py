"""High-precision vivah slot validation: stability, choghadiya, abhijit."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from risk_text_engine import build_choghadiya_schedule

from vedic.panchang.phase_r import compute_phase_r
from vedic.panchang.vivah_geo import DayGeo, local_to_phase_utc

_AUSPICIOUS_CHOG = {"Amrit", "Shubh", "Labh"}
_MIN_STABLE_MINUTES = 90


def _dt_decimal_h(dt: datetime) -> float:
    return dt.hour + dt.minute / 60.0 + dt.second / 3600.0


def _panchang_signature(dt_local: datetime, tz_h: float) -> tuple[str, str, str, str]:
    pr = compute_phase_r(local_to_phase_utc(dt_local, tz_h))
    t = pr.get("r1_tithi") or {}
    n = pr.get("r2_nakshatra") or {}
    k = pr.get("r4_karana") or {}
    y = pr.get("r3_yoga") or {}
    tit = f"{t.get('paksha')}|{t.get('name')}"
    return (tit, n.get("name") or "", k.get("name") or "", y.get("name") or "")


def panchang_stable_through(
    start: datetime,
    end: datetime,
    tz_h: float,
    *,
    step_min: int = 15,
) -> tuple[bool, list[str]]:
    """Tithi + nakshatra must not change; no Bhadra karana inside window."""
    issues: list[str] = []
    mid = start + (end - start) / 2
    s0 = _panchang_signature(start, tz_h)
    sm = _panchang_signature(mid, tz_h)
    s1 = _panchang_signature(end - timedelta(minutes=1), tz_h)
    if s0[0] != sm[0] or sm[0] != s1[0]:
        issues.append("Tithi changes during ceremony window")
    if s0[1] != sm[1] or sm[1] != s1[1]:
        issues.append("Nakshatra changes during ceremony window")
    t = start
    while t < end:
        sig = _panchang_signature(t, tz_h)
        if "vishti" in (sig[2] or "").lower() or "bhadra" in (sig[2] or "").lower():
            issues.append("Bhadra karana inside window")
            break
        t += timedelta(minutes=step_min)
    return (len(issues) == 0, issues)


def choghadiya_covers_window(
    geo: DayGeo,
    start: datetime,
    end: datetime,
) -> tuple[bool, str]:
    """Entire window must fall in Amrit / Shubh / Labh day choghadiya."""
    wd = geo.d.weekday()
    sr = _dt_decimal_h(geo.sunrise)
    ss = _dt_decimal_h(geo.sunset)
    sched = build_choghadiya_schedule(wd, sr, ss)
    a0, a1 = _dt_decimal_h(start), _dt_decimal_h(end)
    for seg in sched:
        if seg.get("period") != "day":
            continue
        if seg.get("quality") != "best":
            continue
        s, e = seg["start_h"], seg["end_h"]
        if s <= a0 and e >= a1:
            return True, seg.get("name", "")
    return False, ""


def overlaps_abhijit(geo: DayGeo, start: datetime, end: datetime) -> bool:
    ab_start = geo.solar_noon - timedelta(minutes=24)
    ab_end = geo.solar_noon + timedelta(minutes=24)
    return start < ab_end and end > ab_start


def precision_slot_bonus(
    geo: DayGeo,
    start: datetime,
    end: datetime,
    tz_h: float,
) -> dict[str, Any]:
    stable, stab_issues = panchang_stable_through(start, end, tz_h)
    chog_ok, chog_name = choghadiya_covers_window(geo, start, end)
    abhijit = overlaps_abhijit(geo, start, end)
    bonus = 0
    flags: list[str] = []
    if stable:
        bonus += 8
        flags.append("stable_panchang")
    if chog_ok:
        bonus += 10
        flags.append(f"choghadiya_{chog_name}")
    if abhijit:
        bonus += 6
        flags.append("abhijit_overlap")
    return {
        "stable": stable,
        "choghadiya_ok": chog_ok,
        "choghadiya": chog_name,
        "abhijit": abhijit,
        "bonus": bonus,
        "issues": stab_issues + ([] if chog_ok else ["Window not fully inside Shubh/Labh/Amrit choghadiya"]),
    }

"""
pratyantar.py
─────────────
Compute the current Vimshottari Pratyantar Dasha (PD) — the sub-period under
the running Antardasha (AD). PDs typically last weeks to a few months and
give month-precision timing for "kab" questions.

Algorithm
─────────
1. AD duration  = MD_years * (AD_lord_years / 120)
2. PD durations within an AD: order starts from the AD lord, then walks the
   standard Vimshottari sequence. Each PD's duration = AD_duration *
   (PD_lord_years / 120).
3. Find which PD slot covers the current date.

Returns the chain of upcoming PDs too (for "kab change hoga" answers).

Public API
──────────
    compute_pratyantar(current_dasha, when=None) -> {
        "current_pd":     {"lord": str, "start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
        "upcoming_pds":   [{lord, start, end}, ...],   # next 3
        "ad_lord":        str,
        "md_lord":        str,
    }
    format_pratyantar_summary(p) -> str

Returns {} if AD start/end missing or unparseable. Never raises.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Optional

# Vimshottari order + years (sum 120)
_VIMS_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars",
               "Rahu", "Jupiter", "Saturn", "Mercury"]
_VIMS_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
               "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
_TOTAL = 120

def _parse_date(s: Any) -> Optional[datetime]:
    """
    Robust ISO-8601 parser preserving time-of-day. Strips trailing 'Z' and
    '+00:00' offsets, accepts plain 'YYYY-MM-DD' fallback. Returns naive
    datetime in UTC reference frame (we don't mix tz-aware with naive `when`).
    """
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None
    # Normalise trailing 'Z' for fromisoformat compatibility (Py 3.11+ handles it,
    # but be defensive for older runtimes).
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
        # Drop tzinfo so all datetime comparisons stay homogeneous.
        return dt.replace(tzinfo=None)
    except Exception:
        pass
    # Fallback: just the date portion
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except Exception:
        return None


def compute_pratyantar(current_dasha: dict, when: Optional[datetime] = None) -> dict[str, Any]:
    if not isinstance(current_dasha, dict):
        return {}
    md_lord = current_dasha.get("maha") or current_dasha.get("mahadasha")
    ad_lord = current_dasha.get("antar") or current_dasha.get("antardasha")
    ad_start = _parse_date(current_dasha.get("startDate") or current_dasha.get("start"))
    ad_end   = _parse_date(current_dasha.get("endDate")   or current_dasha.get("end"))
    if not (md_lord and ad_lord and ad_start and ad_end):
        return {}
    if ad_lord not in _VIMS_YEARS:
        return {}

    ad_duration_seconds = (ad_end - ad_start).total_seconds()
    if ad_duration_seconds <= 0:
        return {}

    # PDs within AD: order starts at AD lord. Keep boundaries as datetime
    # internally — only stringify at the very end.
    start_idx = _VIMS_ORDER.index(ad_lord)
    pds_dt: list[dict] = []
    cursor = ad_start
    for k in range(9):
        pd_lord = _VIMS_ORDER[(start_idx + k) % 9]
        frac = _VIMS_YEARS[pd_lord] / _TOTAL
        pd_end = cursor + timedelta(seconds=ad_duration_seconds * frac)
        pds_dt.append({"lord": pd_lord, "start_dt": cursor, "end_dt": pd_end})
        cursor = pd_end

    when = when or datetime.utcnow()
    if when < ad_start or when >= ad_end:
        # `when` is outside the AD window — be honest, do not invent a "NOW" PD.
        return {
            "current_pd":     None,
            "upcoming_pds":   [],
            "ad_lord":        ad_lord,
            "md_lord":        md_lord,
            "out_of_window":  True,
            "ad_start":       ad_start.strftime("%Y-%m-%d"),
            "ad_end":         ad_end.strftime("%Y-%m-%d"),
        }

    current_pd = None
    upcoming: list[dict] = []
    for pd in pds_dt:
        if pd["start_dt"] <= when < pd["end_dt"] and current_pd is None:
            current_pd = pd
        elif current_pd is not None and len(upcoming) < 3:
            upcoming.append(pd)

    def _ser(pd: dict) -> dict:
        return {"lord": pd["lord"],
                "start": pd["start_dt"].strftime("%Y-%m-%d"),
                "end":   pd["end_dt"].strftime("%Y-%m-%d")}

    return {
        "current_pd":   _ser(current_pd) if current_pd else None,
        "upcoming_pds": [_ser(p) for p in upcoming],
        "ad_lord":      ad_lord,
        "md_lord":      md_lord,
    }


def format_pratyantar_summary(p: dict) -> str:
    if not p:
        return "▸ PRATYANTAR DASHA: (unavailable — needs AD start/end dates)"
    if p.get("out_of_window"):
        return (
            f"▸ PRATYANTAR DASHA (unavailable — current date is outside the "
            f"running AD window {p.get('ad_start')} → {p.get('ad_end')}; "
            f"do NOT invent a current pratyantar)"
        )
    cur = p.get("current_pd")
    if not cur:
        return "▸ PRATYANTAR DASHA: (unavailable)"
    lines = [
        f"▸ PRATYANTAR (sub-period under {p['md_lord']} MD → {p['ad_lord']} AD):",
        f"   ▸ NOW: {cur['lord']} Pratyantar ({cur['start']} → {cur['end']})",
    ]
    if p.get("upcoming_pds"):
        lines.append("   ▸ NEXT pratyantars (month-precision timing windows):")
        for pd in p["upcoming_pds"]:
            lines.append(f"      • {pd['lord']:7s} ({pd['start']} → {pd['end']})")
    return "\n".join(lines)

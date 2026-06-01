"""Marriage age / late / delay context — runs before timing windows are surfaced.

Checks (in order):
  1. User age + gender vs practical marriage floor (e.g. 17 → too young)
  2. Chart late-marriage / delay patterns (Saturn, 7H/7L, KP, Venus…)
  3. Life status: delay (chart) vs late (age band) vs on-time vs too young

Used by marriage_engine_v2.compute_timing_window and LLM LOCKED FACTS block.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Classical indicative bands (Indian urban context)
_THRESHOLDS = {
    "male": {
        "practical_min": 22,
        "on_time_until": 30,   # inclusive: age <= 30 still "on time"
        "late_until": 35,      # 31–35 late band
        "very_late_from": 36,
    },
    "female": {
        "practical_min": 19,
        "on_time_until": 28,
        "late_until": 32,
        "very_late_from": 33,
    },
    "unknown": {
        "practical_min": 22,
        "on_time_until": 30,
        "late_until": 35,
        "very_late_from": 36,
    },
}

_LATE_CHART_KEYWORDS = (
    "saturn", "delay", "debilitated", "denies", "obstacle",
    "8l", "6l", "12l", "rahu in 7", "rahu in 1",
)


def _gender_key(is_female: Optional[bool]) -> str:
    if is_female is True:
        return "female"
    if is_female is False:
        return "male"
    return "unknown"


def _chart_late_from_flags(risk_flags: List[str], kp_csl: str) -> Tuple[bool, List[str]]:
    signals: List[str] = []
    for f in risk_flags or []:
        fl = f.lower()
        if any(k in fl for k in _LATE_CHART_KEYWORDS):
            signals.append(f)
    if kp_csl in ("DENIES", "PARTIAL"):
        signals.append(f"KP 7th cusp sub-lord {kp_csl}")
    chart_late = len(signals) >= 2 or any(
        "denies" in s.lower() or "saturn in 7h" in s.lower()
        for s in signals
    )
    return chart_late, signals[:8]


def assess_marriage_age_context(
    *,
    user_age: Optional[int],
    is_female: Optional[bool],
    risk_flags: Optional[List[str]] = None,
    kp_csl_verdict: str = "UNKNOWN",
    too_young_engine: bool = False,
    min_practical_age: Optional[int] = None,
) -> Dict[str, Any]:
    """Build age/gender/late/delay context for marriage TIMING questions."""
    gkey = _gender_key(is_female)
    th = _THRESHOLDS[gkey]
    practical = min_practical_age if min_practical_age is not None else th["practical_min"]

    gender_label = gkey if gkey != "unknown" else "unknown"
    chart_late, chart_signals = _chart_late_from_flags(
        risk_flags or [], kp_csl_verdict or "UNKNOWN"
    )

    # ── Age band vs gender ───────────────────────────────────────────
    age_band = None
    if user_age is not None:
        if user_age < th["practical_min"]:
            age_band = "BELOW_PRACTICAL"
        elif user_age <= th["on_time_until"]:
            age_band = "ON_TIME"
        elif user_age <= th["late_until"]:
            age_band = "LATE"
        else:
            age_band = "VERY_LATE"

    too_young = too_young_engine or (
        user_age is not None and user_age < practical
    )
    currently_late_by_age = age_band in ("LATE", "VERY_LATE")
    on_time_by_age = age_band == "ON_TIME" or age_band == "BELOW_PRACTICAL"

    # delay = chart postponement; late = age crossed typical band
    if too_young:
        delay_vs_late = "too_young"
        life_status = "TOO_YOUNG"
        timing_appropriate = False
    elif currently_late_by_age and chart_late:
        delay_vs_late = "both"
        life_status = "LATE_BY_AGE_AND_CHART"
        timing_appropriate = True
    elif currently_late_by_age:
        delay_vs_late = "age_late"
        life_status = "LATE_BY_AGE"
        timing_appropriate = True
    elif chart_late and on_time_by_age:
        delay_vs_late = "chart_delay"
        life_status = "DELAY_PATTERN_ON_TIME_AGE"
        timing_appropriate = True
    elif chart_late:
        delay_vs_late = "chart_delay"
        life_status = "DELAY_PATTERN"
        timing_appropriate = True
    else:
        delay_vs_late = "none"
        life_status = "ON_TIME"
        timing_appropriate = True

    # Narrative hints for LLM (Hinglish, deterministic)
    hints: List[str] = []
    if user_age is not None:
        hints.append(f"User ki umar {user_age} saal ({gender_label}).")
    else:
        hints.append("User ki umar chart se confirm nahi — age-neutral tone.")

    if too_young:
        hints.append(
            f"PRACTICAL RULE: {practical}+ saal se pehle marriage timing mat do. "
            f"Dasha/PD agar 6 mahine dikhaaye bhi, near-term shaadi mat bolo — "
            f"padhai/career/maturity pe focus. Sirf post-{practical} long-term hint OK."
        )
    elif delay_vs_late == "chart_delay":
        hints.append(
            "Chart me delay/late-marriage pattern hai par umar abhi typical 'late' "
            "band me nahi — isko DELAY bolo, LATE mat bolo."
        )
    elif delay_vs_late == "age_late":
        hints.append(
            f"Umar ke hisab se user {gender_label} late-marriage band me hai "
            f"({th['on_time_until']+1}–{th['late_until']} ya uske baad) — "
            "tone reassuring: late ≠ denial."
        )
    elif delay_vs_late == "both":
        hints.append(
            "Chart delay + umar bhi late band — dono acknowledge karo; phir "
            "engine ki post-floor windows cite karo."
        )

    if chart_signals:
        hints.append("Chart signals: " + "; ".join(chart_signals[:4]))

    # Late-by-age: scan agle ~12 mahine; AD weak ho to har PD alag check
    late_urgent_scan = bool(currently_late_by_age and timing_appropriate)
    search_horizon_days = 365 if late_urgent_scan else None
    if late_urgent_scan:
        hints.append(
            "LATE-URGENT SCAN: user already late-age band — engine pehle agle "
            "12 mahine ke andar window dhundhega. Agar Antardasha marriage "
            "significator support na kare, har Pratyantardasha (PD) alag check."
        )

    return {
        "user_age": user_age,
        "user_gender": gender_label,
        "gender_thresholds": dict(th),
        "age_band_by_gender": age_band,
        "chart_late_marriage": chart_late,
        "chart_late_signals": chart_signals,
        "currently_late_by_age": currently_late_by_age,
        "delay_vs_late": delay_vs_late,
        "life_status": life_status,
        "timing_appropriate": timing_appropriate,
        "too_young_for_marriage": too_young,
        "min_practical_age": practical,
        "on_time_age_until": th["on_time_until"],
        "late_age_until": th["late_until"],
        "narrative_hints": hints,
        "llm_directive": _llm_directive(
            too_young, delay_vs_late, user_age, practical, gender_label, th,
            late_urgent_scan=late_urgent_scan,
        ),
        "late_urgent_scan": late_urgent_scan,
        "search_horizon_days": search_horizon_days,
    }


def _llm_directive(
    too_young: bool,
    delay_vs_late: str,
    user_age: Optional[int],
    practical: int,
    gender: str,
    th: dict,
    *,
    late_urgent_scan: bool = False,
) -> str:
    if too_young:
        return (
            f"HARD: User {user_age or '?'} saal — marriage-ready nahi. "
            f"Near-term (6 mahine/1 saal) shaadi date STRICTLY FORBIDDEN. "
            f"Pehle growth/career; agar timing do to sirf {practical}+ ke baad."
        )
    if delay_vs_late == "age_late" or late_urgent_scan:
        base = (
            f"User {gender} age {user_age or '?'} — late-marriage band. "
            "Reassure late≠denial. Engine scanned next 12 months; "
            "PD-level windows used when AD does not support."
        )
        if late_urgent_scan:
            return base + " Lead with nearest engine window inside 1 year."
        return base
    if delay_vs_late == "chart_delay":
        return (
            "Chart delay pattern — marriage timing late phase me zyada; "
            "user ko abhi panic mat dilao agar umar on-time band me hai."
        )
    if delay_vs_late == "both":
        return (
            "Chart + age dono late — empathetic tone; engine 12-month PD-scan "
            "mode; cite nearest window within 1 year if present."
        )
    return "Age on-time band — normal marriage timing answer OK."

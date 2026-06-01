"""STEP 0 — early/late marriage tendency (runs BEFORE Step 0A and Steps 1–5).

User mandate:
  • Early vs late marriage: D1 AND D9 both checked.
  • BCP marriage ages live in Step 0A (`marriage_step0a.py`).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from event_timing.marriage.marriage_age_context import assess_marriage_age_context

_SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun",
    5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter",
    9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_OWN_SIGNS = {
    "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
    "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
}
_EXALT = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
          "Jupiter": 3, "Venus": 11, "Saturn": 6}
_DEBIL = {"Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
          "Jupiter": 9, "Venus": 5, "Saturn": 0}
_FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
_ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}
_BENEFICS = {"Moon", "Mercury", "Jupiter", "Venus"}
_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
_EARLY_7L_HOUSES = {1, 5, 7, 9}
_LATE_7L_HOUSES = {6, 8, 12}


def _load_d9_planets(kundli: dict) -> tuple[Optional[int], List[dict]]:
    try:
        from divisional_charts import compute_d9  # type: ignore
    except Exception:
        return None, []
    planets = kundli.get("planets") or []
    lagna_lon = (
        kundli.get("ascendantLon") or kundli.get("ascendantLongitude")
        or kundli.get("lagnaLon") or kundli.get("ascendantDeg")
    )
    try:
        lagna_lon = float(lagna_lon) if lagna_lon is not None else None
    except (TypeError, ValueError):
        lagna_lon = None
    try:
        d9 = compute_d9(planets, lagna_lon=lagna_lon) or {}
    except Exception:
        return None, []
    d9_lagna = (d9.get("_lagna") or {}).get("sign_idx")
    if not isinstance(d9_lagna, int):
        return None, []
    d9_planets: List[dict] = []
    for pname in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
        info = d9.get(pname) or {}
        si = info.get("sign_idx")
        if not isinstance(si, int):
            continue
        d9_planets.append({
            "name": pname,
            "sign_idx": si,
            "house": ((si - d9_lagna) % 12) + 1,
        })
    return d9_lagna, d9_planets


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
            if isinstance(s, str) and s in _SIGNS:
                return _SIGNS.index(s)
    return None


def _planet_record(planets: List[dict], pname: str) -> Optional[dict]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == pname:
            return p
    return None


def _dignity(pname: str, sign_si: Optional[int]) -> str:
    if sign_si is None or pname not in _OWN_SIGNS:
        return "unknown"
    if pname in _EXALT and sign_si == _EXALT[pname]:
        return "exalted"
    if pname in _DEBIL and sign_si == _DEBIL[pname]:
        return "debilitated"
    if sign_si in _OWN_SIGNS.get(pname, set()):
        return "own"
    sign_lord = _SIGN_LORDS.get(sign_si)
    if sign_lord in _FRIENDS.get(pname, set()):
        return "friend"
    if sign_lord in _ENEMIES.get(pname, set()):
        return "enemy"
    return "neutral"


def _is_combust(p: Optional[dict], planets: List[dict]) -> bool:
    if not isinstance(p, dict):
        return False
    if p.get("combust") is True or p.get("isCombust") is True:
        return True
    pname = p.get("name")
    if pname in ("Sun", "Rahu", "Ketu"):
        return False
    # D9 synthetic rows only carry sign_idx; do not infer combustion there.
    if not p.get("sign"):
        return False
    # Fallback when exact combustion is unavailable: same D1 sign as Sun.
    sun_rec = _planet_record(planets, "Sun")
    if not isinstance(sun_rec, dict) or not sun_rec.get("sign"):
        return False
    sun_si = _planet_sign_idx(planets, "Sun")
    p_si = _planet_sign_idx(planets, str(pname or ""))
    return sun_si is not None and p_si is not None and sun_si == p_si


def _is_retrograde(p: Optional[dict]) -> bool:
    if not isinstance(p, dict):
        return False
    return bool(p.get("retrograde") or p.get("isRetrograde") or p.get("retro"))


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


def light_chart_risk_flags(
    kundli: dict,
    lagna_si: int,
    kp_csl_verdict: str = "UNKNOWN",
    *,
    division: str = "D1",
    planets: Optional[List[dict]] = None,
    d9_lagna_si: Optional[int] = None,
) -> List[str]:
    flags: List[str] = []
    planets = planets if planets is not None else (kundli.get("planets") or [])
    h7_si = (lagna_si + 6) % 12
    seventh_lord = _house_lord(lagna_si, 7)
    seventh_lord_si = _planet_sign_idx(planets, seventh_lord)
    sat_si = _planet_sign_idx(planets, "Saturn")
    rahu_si = _planet_sign_idx(planets, "Rahu")
    venus_si = _planet_sign_idx(planets, "Venus")
    prefix = f"{division} "

    h7l_house = _planet_house(planets, seventh_lord)
    seventh_lord_rec = _planet_record(planets, seventh_lord)
    seventh_lord_dignity = _dignity(seventh_lord, seventh_lord_si)
    if h7l_house in _LATE_7L_HOUSES:
        flags.append(f"{prefix}7L ({seventh_lord}) in {h7l_house}H (late-marriage)")
    elif h7l_house in _EARLY_7L_HOUSES:
        flags.append(f"{prefix}7L ({seventh_lord}) in {h7l_house}H (early tendency)")
    if seventh_lord_dignity == "debilitated":
        flags.append(f"{prefix}7L ({seventh_lord}) debilitated")
    elif seventh_lord_dignity == "enemy":
        flags.append(f"{prefix}7L ({seventh_lord}) in enemy sign")
    if _is_combust(seventh_lord_rec, planets):
        flags.append(f"{prefix}7L ({seventh_lord}) combust")
    if _is_retrograde(seventh_lord_rec):
        flags.append(f"{prefix}7L ({seventh_lord}) retrograde")

    if sat_si is not None:
        if sat_si == h7_si:
            flags.append(f"{prefix}Saturn in 7H (delay)")
        elif _aspects_target("Saturn", sat_si, h7_si):
            flags.append(f"{prefix}Saturn aspects 7H (delay)")

    if rahu_si is not None:
        rahu_h = ((rahu_si - lagna_si) % 12) + 1
        if rahu_h in (1, 7):
            flags.append(f"{prefix}Rahu in {rahu_h}H (1-7 axis)")

    venus_rec = _planet_record(planets, "Venus")
    venus_dignity = _dignity("Venus", venus_si)
    if venus_dignity == "debilitated":
        flags.append(f"{prefix}Venus debilitated")
    elif venus_dignity == "enemy":
        flags.append(f"{prefix}Venus in enemy sign")
    if _is_combust(venus_rec, planets):
        flags.append(f"{prefix}Venus combust")

    if division == "D1" and kp_csl_verdict == "DENIES":
        flags.append("7th cusp sub-lord DENIES marriage promise (KP)")
    elif division == "D1" and kp_csl_verdict == "PARTIAL":
        flags.append("7th cusp sub-lord PARTIAL (KP — obstruction)")

    _ = d9_lagna_si
    return flags


def chart_marriage_pace_for_division(
    planets: List[dict],
    lagna_si: int,
    division: str = "D1",
    kp_csl_verdict: str = "UNKNOWN",
    is_female: Optional[bool] = None,
) -> Dict[str, Any]:
    """Early / late / normal for one division."""
    seventh_lord = _house_lord(lagna_si, 7)
    h7l_house = _planet_house(planets, seventh_lord)
    seventh_lord_si = _planet_sign_idx(planets, seventh_lord)
    seventh_lord_rec = _planet_record(planets, seventh_lord)
    score = 0
    signals: List[str] = []

    if h7l_house in _EARLY_7L_HOUSES:
        score += 2
        signals.append(f"{division}: 7L in {h7l_house}H → earlier")
    elif h7l_house in _LATE_7L_HOUSES:
        score -= 2
        signals.append(f"{division}: 7L in {h7l_house}H → later")
    elif h7l_house in (2, 4):
        score -= 1
        signals.append(f"{division}: 7L in {h7l_house}H → mild delay")

    h7l_dignity = _dignity(seventh_lord, seventh_lord_si)
    if h7l_dignity in ("exalted", "own"):
        score += 2
        signals.append(f"{division}: 7L {seventh_lord} {h7l_dignity} → stronger/timely")
    elif h7l_dignity == "friend":
        score += 1
        signals.append(f"{division}: 7L {seventh_lord} in friend sign → support")
    elif h7l_dignity == "debilitated":
        score -= 2
        signals.append(f"{division}: 7L {seventh_lord} debilitated → delay")
    elif h7l_dignity == "enemy":
        score -= 1
        signals.append(f"{division}: 7L {seventh_lord} in enemy sign → friction/delay")

    if _is_combust(seventh_lord_rec, planets):
        score -= 2
        signals.append(f"{division}: 7L {seventh_lord} combust → delay")
    if _is_retrograde(seventh_lord_rec):
        score -= 1
        signals.append(f"{division}: 7L {seventh_lord} retrograde → slower maturation")

    sat_si = _planet_sign_idx(planets, "Saturn")
    h7_si = (lagna_si + 6) % 12
    if sat_si is not None:
        if sat_si == h7_si or _aspects_target("Saturn", sat_si, h7_si):
            score -= 2
            signals.append(f"{division}: Saturn links 7H")

    venus_si = _planet_sign_idx(planets, "Venus")
    if venus_si is not None:
        v_h = ((venus_si - lagna_si) % 12) + 1
        if v_h in (1, 4, 7, 10):
            score += 1
            signals.append(f"{division}: Venus in {v_h}H (support)")
        venus_dignity = _dignity("Venus", venus_si)
        venus_rec = _planet_record(planets, "Venus")
        if venus_dignity in ("exalted", "own"):
            score += 1
            signals.append(f"{division}: Venus {venus_dignity} → relationship support")
        elif venus_dignity == "debilitated":
            score -= 2
            signals.append(f"{division}: Venus debilitated → relationship delay")
        elif venus_dignity == "enemy":
            score -= 1
            signals.append(f"{division}: Venus in enemy sign → relationship friction")
        if _is_combust(venus_rec, planets):
            score -= 1
            signals.append(f"{division}: Venus combust → relationship delay")

    if is_female is not False:
        jup_si = _planet_sign_idx(planets, "Jupiter")
        jup_dignity = _dignity("Jupiter", jup_si)
        if jup_dignity in ("exalted", "own"):
            score += 1
            signals.append(f"{division}: Jupiter {jup_dignity} → spouse-karaka support")
        elif jup_dignity == "debilitated":
            score -= 1
            signals.append(f"{division}: Jupiter debilitated → spouse-karaka weak")
        elif jup_dignity == "enemy":
            score -= 1
            signals.append(f"{division}: Jupiter in enemy sign → spouse-karaka friction")

    benefic_support = 0
    malefic_pressure = 0
    for pname in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
        p_si = _planet_sign_idx(planets, pname)
        if p_si is None:
            continue
        p_house = ((p_si - lagna_si) % 12) + 1
        hits_7h = p_house == 7 or _aspects_target(pname, p_si, h7_si)
        hits_7l = (
            seventh_lord_si is not None
            and pname != seventh_lord
            and (p_si == seventh_lord_si or _aspects_target(pname, p_si, seventh_lord_si))
        )
        if not (hits_7h or hits_7l):
            continue
        if pname in _BENEFICS:
            benefic_support += 1
        elif pname in _MALEFICS and pname != "Saturn":
            malefic_pressure += 1
    if benefic_support:
        boost = min(2, benefic_support)
        score += boost
        signals.append(f"{division}: benefic support to 7H/7L (+{boost})")
    if malefic_pressure:
        penalty = min(2, malefic_pressure)
        score -= penalty
        signals.append(f"{division}: malefic pressure on 7H/7L (-{penalty})")

    if division == "D1":
        if kp_csl_verdict == "DENIES":
            score -= 2
            signals.append("D1: KP 7CSL DENIES")
        elif kp_csl_verdict == "PARTIAL":
            score -= 1
            signals.append("D1: KP 7CSL PARTIAL")

    if score >= 2:
        pace = "EARLY"
    elif score <= -3:
        pace = "VERY_LATE"
    elif score <= -1:
        pace = "LATE"
    else:
        pace = "NORMAL"

    return {
        "division": division,
        "chart_pace": pace,
        "chart_pace_score": score,
        "chart_pace_signals": signals,
        "seventh_lord": seventh_lord,
        "seventh_lord_house": h7l_house,
        "seventh_lord_dignity": h7l_dignity,
    }


def combine_d1_d9_pace(d1: Dict[str, Any], d9: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge D1 + D9 early/late into one verdict."""
    d9 = d9 or {}
    d1p = d1.get("chart_pace", "NORMAL")
    d9p = d9.get("chart_pace", "NORMAL")
    score = int(d1.get("chart_pace_score", 0)) + int(d9.get("chart_pace_score", 0))
    signals = (d1.get("chart_pace_signals") or []) + (d9.get("chart_pace_signals") or [])

    late_set = {"LATE", "VERY_LATE"}
    if d1p in late_set and d9p in late_set:
        combined = "VERY_LATE"
    elif d1p in late_set or d9p in late_set:
        combined = "LATE"
    elif d1p == "EARLY" and d9p in ("EARLY", "NORMAL"):
        combined = "EARLY"
    elif score <= -3:
        combined = "LATE"
    elif score >= 2:
        combined = "EARLY"
    else:
        combined = "NORMAL"

    return {
        "combined_pace": combined,
        "d1_pace": d1p,
        "d9_pace": d9p,
        "combined_score": score,
        "signals": signals,
    }


def _merge_step0_verdict(
    combined_pace: str,
    age_ctx: Dict[str, Any],
) -> str:
    if age_ctx.get("too_young_for_marriage"):
        return "TOO_YOUNG"
    delay = age_ctx.get("delay_vs_late") or "none"
    life = age_ctx.get("life_status") or ""
    if delay == "both" or life == "LATE_BY_AGE_AND_CHART":
        return "LATE"
    if delay == "age_late" or life == "LATE_BY_AGE":
        return "LATE"
    if combined_pace in ("LATE", "VERY_LATE") and delay == "chart_delay":
        return "DELAYED"
    if combined_pace == "EARLY" and delay == "none":
        return "EARLY"
    if combined_pace in ("LATE", "VERY_LATE"):
        return "DELAYED"
    return "ON_TIME"


def run_marriage_step0(
    kundli: dict,
    lagna_si: int,
    *,
    user_age: Optional[int] = None,
    birth_dt: Optional[datetime] = None,
    is_female: Optional[bool] = None,
    kp: Optional[dict] = None,
    min_practical_age: Optional[int] = None,
    years_ahead: int = 5,
) -> Dict[str, Any]:
    """STEP 0 — D1/D9 early-late tendency + age context only."""
    _ = birth_dt, years_ahead  # kept for backward-compatible call signature
    kp_csl_verdict = "UNKNOWN"
    csl_planet = None
    if isinstance(kp, dict) and kp:
        try:
            from event_timing._shared.kp_significator_scan import kp_marriage_cusp_verdict
            csl = kp_marriage_cusp_verdict(kp, 7)
            kp_csl_verdict = csl.get("verdict") or "UNKNOWN"
            csl_planet = csl.get("csl_planet")
        except Exception:
            pass

    d9_lagna_si, d9_planets = _load_d9_planets(kundli)
    d1_planets = kundli.get("planets") or []

    pre_flags = light_chart_risk_flags(
        kundli, lagna_si, kp_csl_verdict, division="D1", planets=d1_planets,
    )
    if d9_lagna_si is not None and d9_planets:
        pre_flags.extend(
            light_chart_risk_flags(
                kundli, d9_lagna_si, kp_csl_verdict,
                division="D9", planets=d9_planets, d9_lagna_si=d9_lagna_si,
            )
        )

    pace_d1 = chart_marriage_pace_for_division(
        d1_planets, lagna_si, "D1", kp_csl_verdict, is_female=is_female,
    )
    pace_d9 = (
        chart_marriage_pace_for_division(
            d9_planets, d9_lagna_si, "D9", kp_csl_verdict, is_female=is_female,
        )
        if d9_lagna_si is not None else None
    )
    pace_combined = combine_d1_d9_pace(pace_d1, pace_d9)

    too_young = bool(
        user_age is not None
        and min_practical_age is not None
        and user_age < min_practical_age
    )
    age_ctx = assess_marriage_age_context(
        user_age=user_age,
        is_female=is_female,
        risk_flags=pre_flags,
        kp_csl_verdict=kp_csl_verdict,
        too_young_engine=too_young,
        min_practical_age=min_practical_age,
    )

    combined_pace = pace_combined["combined_pace"]

    step0_verdict = _merge_step0_verdict(combined_pace, age_ctx)

    step0_tendency = {
        "verdict": step0_verdict,
        "combined_pace": combined_pace,
        "d1_pace": pace_d1.get("chart_pace"),
        "d9_pace": (pace_d9 or {}).get("chart_pace"),
        "age_band": age_ctx.get("age_band_by_gender"),
        "delay_vs_late": age_ctx.get("delay_vs_late"),
        "life_status": age_ctx.get("life_status"),
        "combined_score": pace_combined.get("combined_score"),
    }

    return {
        "step0_version": "early_late_d1_d9_v3",
        "step0_tendency": step0_tendency,
        "user_age": user_age,
        "marriage_pace": {
            "d1": pace_d1,
            "d9": pace_d9,
            "combined": pace_combined,
        },
        "chart_marriage_pace": pace_d1,
        "marriage_age_context": age_ctx,
        "pre_risk_flags": pre_flags,
        "kp_csl_verdict": kp_csl_verdict,
        "kp_csl_planet": csl_planet,
        "reasoning_summary": (
            f"STEP0: pace D1={pace_d1.get('chart_pace')} D9="
            f"{(pace_d9 or {}).get('chart_pace', 'n/a')} → {combined_pace}; "
            f"score={pace_combined.get('combined_score')}"
        ),
        "llm_directive": (age_ctx.get("llm_directive") or "")[:600],
    }


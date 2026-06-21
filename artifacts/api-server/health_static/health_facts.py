"""Health deterministic fact pack — multi-dimensional verdict (non-timing).

Dimensions:
  • overall_vitality   — constitution / energy / immunity tone
  • chronic_tendency   — long-term / 8H / Saturn-Rahu pressure
  • mental_stress      — Moon / 4H / mind-body link
  • surgery_risk_tone  — Mars-Saturn / 6-8 axis caution (NOT muhurat)
  • preventive_risk    — vulnerability zones to monitor
  • recovery_capacity  — resistance + healing support (NOT recovery date)

Public:
  compute_health_facts(kundli) -> dict
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from stock_engine.stock_facts import (
    _DIGNITY_SCORE,
    _aspects,
    _house_lord,
    _planet_by_name,
    _planet_dignity,
    _planets_in_house,
    _sign_idx,
)

_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
_MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
_DUSTHANA = (6, 8, 12)
_KENDRA = (1, 4, 7, 10)


def _tier(verdict: str, strong: bool = False, weak: bool = False) -> str:
    if verdict == "GREEN":
        return "high"
    if verdict == "RED":
        return "none"
    if weak:
        return "low"
    if strong:
        return "moderate"
    return "moderate"


def _verdict_from_score(score: int) -> str:
    if score >= 2:
        return "GREEN"
    if score <= -1:
        return "RED"
    return "YELLOW"


def _lord_state(planets: List[dict], asc_si: int, house: int) -> dict:
    lord = _house_lord(asc_si, house)
    p = _planet_by_name(planets, lord) if lord else None
    lh = (p or {}).get("house") or 0
    dig = _planet_dignity(planets, lord) if lord else "?"
    return {
        "lord": lord or "?",
        "lord_house": lh,
        "lord_dignity": dig,
        "lord_in_dusthana": lh in _DUSTHANA,
    }


def _karaka(planets: List[dict], name: str) -> dict:
    p = _planet_by_name(planets, name)
    if not p:
        return {"name": name, "house": 0, "dignity": "?"}
    return {
        "name": name,
        "house": p.get("house") or 0,
        "dignity": _planet_dignity(planets, name),
    }


def _malefics_in(house: int, planets: List[dict]) -> List[str]:
    return [n for n in _planets_in_house(planets, house) if n in _MALEFICS]


def _benefic_aspect_on_house(planets: List[dict], target_house: int) -> bool:
    for b in _BENEFICS:
        bp = _planet_by_name(planets, b)
        if not bp:
            continue
        bh = bp.get("house") or 0
        if bh == target_house:
            return True
        if _aspects(b, bh, target_house):
            return True
    return False


def _afflicts_moon(planets: List[dict]) -> List[str]:
    moon = _planet_by_name(planets, "Moon")
    if not moon:
        return []
    mh = moon.get("house") or 0
    aff = []
    for m in ("Saturn", "Rahu", "Ketu", "Mars", "Sun"):
        mp = _planet_by_name(planets, m)
        if not mp:
            continue
        m_h = mp.get("house") or 0
        if m_h == mh:
            aff.append(f"{m} conjunct Moon")
        elif _aspects(m, m_h, mh):
            aff.append(f"{m} aspects Moon")
    return aff


def _compute_overall_vitality(
    lord_states: dict,
    karakas: dict,
    vitality_score: int,
    afflictions: List[str],
) -> Tuple[str, str, str, int]:
    score = 0
    if vitality_score >= 70:
        score += 2
    elif vitality_score >= 50:
        score += 1
    else:
        score -= 1

    h1 = lord_states.get("h1") or {}
    if _DIGNITY_SCORE.get(h1.get("lord_dignity", ""), 0) >= 2:
        score += 1
    elif h1.get("lord_in_dusthana"):
        score -= 1

    sun_d = _DIGNITY_SCORE.get((karakas.get("Sun") or {}).get("dignity", ""), 0)
    moon_d = _DIGNITY_SCORE.get((karakas.get("Moon") or {}).get("dignity", ""), 0)
    score += min(1, sun_d // 2) + min(1, moon_d // 2)

    if len(afflictions) >= 3:
        score -= 1

    v = _verdict_from_score(score)
    if v == "GREEN":
        reason = f"Vitality score {vitality_score}/100 with supportive Lagnesh + Sun-Moon base"
    elif v == "RED":
        reason = f"Vitality score {vitality_score}/100 with multiple drain signals on constitution"
    else:
        reason = f"Mixed vitality ({vitality_score}/100) — strong pockets with some weak zones"
    return v, reason, _tier(v), score


def _compute_chronic_tendency(
    lord_states: dict,
    karakas: dict,
    planets: List[dict],
) -> Tuple[str, str, str, int]:
    score = 0
    h8_m = _malefics_in(8, planets)
    if len(h8_m) >= 2:
        score -= 2
    elif h8_m:
        score -= 1

    h8 = lord_states.get("h8") or {}
    if h8.get("lord_in_dusthana"):
        score -= 1
    if _DIGNITY_SCORE.get(h8.get("lord_dignity", ""), 0) >= 2:
        score += 1

    sat_h = (karakas.get("Saturn") or {}).get("house") or 0
    rahu_h = (karakas.get("Rahu") or {}).get("house") or 0
    if sat_h in (1, 6, 8) or rahu_h in (1, 6, 8):
        score -= 1

    v = _verdict_from_score(score)
    if v == "GREEN":
        reason = "Chronic-pressure axis relatively light — maintenance lifestyle enough"
    elif v == "RED":
        reason = "8H/Saturn-Rahu cluster suggests long-term tendency needs active management"
    else:
        reason = "Some chronic-vulnerability signals — lifestyle vigilance helps"
    return v, reason, _tier(v, weak=(v == "RED")), score


def _compute_mental_stress(
    karakas: dict,
    lord_states: dict,
    planets: List[dict],
) -> Tuple[str, str, str, int]:
    score = 0
    moon = karakas.get("Moon") or {}
    moon_d = _DIGNITY_SCORE.get(moon.get("dignity", ""), 0)
    if moon_d >= 2:
        score += 2
    elif moon_d == 0:
        score -= 1

    moon_h = moon.get("house") or 0
    if moon_h in _DUSTHANA:
        score -= 1

    h4 = lord_states.get("h4") or {}
    if h4.get("lord_in_dusthana"):
        score -= 1
    elif _DIGNITY_SCORE.get(h4.get("lord_dignity", ""), 0) >= 2:
        score += 1

    aff = _afflicts_moon(planets)
    score -= min(2, len(aff))

    v = _verdict_from_score(score)
    if v == "GREEN":
        reason = "Moon + 4H relatively calm — emotional resilience supported"
    elif v == "RED":
        reason = "Moon under pressure — stress/anxiety tendency needs active care"
    else:
        reason = "Mixed mind-body pattern — stress spikes possible under pressure"
    return v, reason, _tier(v), score


def _compute_surgery_risk_tone(
    karakas: dict,
    lord_states: dict,
    planets: List[dict],
) -> Tuple[str, str, str, int]:
    score = 0
    mars_h = (karakas.get("Mars") or {}).get("house") or 0
    sat_h = (karakas.get("Saturn") or {}).get("house") or 0

    if mars_h in (1, 6, 8) and sat_h in (1, 6, 8):
        score -= 2
    elif mars_h in (6, 8) or sat_h in (6, 8):
        score -= 1

    h6 = lord_states.get("h6") or {}
    h8 = lord_states.get("h8") or {}
    if h6.get("lord_in_dusthana") or h8.get("lord_in_dusthana"):
        score -= 1

    if _benefic_aspect_on_house(planets, 1):
        score += 1

    v = _verdict_from_score(score)
    if v == "GREEN":
        reason = "Surgical/invasive caution tone low — routine medical guidance enough"
    elif v == "RED":
        reason = "Mars-Saturn + 6-8 pressure — extra caution tone if surgery ever needed"
    else:
        reason = "Moderate surgical-risk tone — second opinion + surgeon choice matter"
    return v, reason, _tier(v), score


def _compute_preventive_risk(
    lord_states: dict,
    planets: List[dict],
) -> Tuple[str, str, str, int]:
    score = 0
    for key in ("h6", "h8", "h12"):
        st = lord_states.get(key) or {}
        lh = st.get("lord_house") or 0
        if lh == 1:
            score -= 1

    if _malefics_in(1, planets):
        score -= 1
    if _malefics_in(6, planets):
        score -= 1

    if _benefic_aspect_on_house(planets, 1):
        score += 1
    if _benefic_aspect_on_house(planets, 5):
        score += 1

    v = _verdict_from_score(score)
    if v == "GREEN":
        reason = "Preventive vulnerability relatively low — routine checkups sufficient"
    elif v == "RED":
        reason = "Multiple risk-zone signals — preventive habits + screenings important"
    else:
        reason = "Some zones to monitor — prevention beats late reaction"
    return v, reason, _tier(v), score


def _compute_recovery_capacity(
    lord_states: dict,
    karakas: dict,
    planets: List[dict],
) -> Tuple[str, str, str, int]:
    score = 0
    h6 = lord_states.get("h6") or {}
    if _DIGNITY_SCORE.get(h6.get("lord_dignity", ""), 0) >= 2:
        score += 2
    elif h6.get("lord_in_dusthana"):
        score -= 1

    jup_h = (karakas.get("Jupiter") or {}).get("house") or 0
    mer_h = (karakas.get("Mercury") or {}).get("house") or 0
    if jup_h in (1, 6, 8) or _aspects("Jupiter", jup_h, 1):
        score += 1
    if mer_h in (1, 6) or _DIGNITY_SCORE.get((karakas.get("Mercury") or {}).get("dignity", ""), 0) >= 1:
        score += 1

    if _malefics_in(6, planets) and not _benefic_aspect_on_house(planets, 6):
        score -= 1

    v = _verdict_from_score(score)
    if v == "GREEN":
        reason = "Recovery resistance supported — doctor compliance + rest work well"
    elif v == "RED":
        reason = "Recovery axis weak — slow healing tendency, extra medical follow-up"
    else:
        reason = "Average recovery capacity — patience + treatment adherence key"
    return v, reason, _tier(v), score


def compute_health_facts(kundli: dict) -> Dict[str, Any]:
    if not isinstance(kundli, dict):
        return {"error": "invalid kundli"}

    planets = kundli.get("planets") or []
    if not planets:
        return {"error": "planets missing"}

    asc = kundli.get("ascendant")
    asc_si = _sign_idx(asc) if isinstance(asc, str) else None
    if asc_si is None:
        for key in ("lagnaSign", "ascendant_sign", "ascendantSignIndex"):
            v = kundli.get(key)
            if isinstance(v, str):
                asc_si = _sign_idx(v)
            elif isinstance(v, int):
                asc_si = int(v) % 12
            if asc_si is not None:
                break
    if asc_si is None:
        return {"error": "lagna missing"}

    lord_states = {
        f"h{hn}": _lord_state(planets, asc_si, hn)
        for hn in (1, 4, 6, 8, 12)
    }
    karakas = {n: _karaka(planets, n) for n in (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
    )}

    vitality_score = 50
    vitality_risk = "Moderate"
    try:
        from vedic.health_vitality_score_v1 import compute_health_vitality_score

        vs = compute_health_vitality_score(kundli)
        vitality_score = int(vs.get("score") or 50)
        vitality_risk = str(vs.get("risk") or "Moderate")
    except Exception:
        pass

    afflictions: List[str] = []
    for hn in (1, 6, 8, 12):
        mal = _malefics_in(hn, planets)
        if mal:
            afflictions.append(f"Malefics in H{hn}: {', '.join(mal)}")
    for key in ("h6", "h8", "h12"):
        st = lord_states.get(key) or {}
        if st.get("lord_in_dusthana"):
            afflictions.append(
                f"H{key[1:]} lord ({st.get('lord')}) in dusthana H{st.get('lord_house')}"
            )
    moon_aff = _afflicts_moon(planets)
    afflictions.extend(moon_aff[:3])

    ov_v, ov_r, ov_t, _ = _compute_overall_vitality(
        lord_states, karakas, vitality_score, afflictions,
    )
    ch_v, ch_r, ch_t, _ = _compute_chronic_tendency(lord_states, karakas, planets)
    ms_v, ms_r, ms_t, _ = _compute_mental_stress(karakas, lord_states, planets)
    sr_v, sr_r, sr_t, _ = _compute_surgery_risk_tone(karakas, lord_states, planets)
    pr_v, pr_r, pr_t, _ = _compute_preventive_risk(lord_states, planets)
    rc_v, rc_r, rc_t, _ = _compute_recovery_capacity(lord_states, karakas, planets)

    dimensions = {
        "overall_vitality": {"verdict": ov_v, "reason": ov_r, "tier": ov_t},
        "chronic_tendency": {"verdict": ch_v, "reason": ch_r, "tier": ch_t},
        "mental_stress": {"verdict": ms_v, "reason": ms_r, "tier": ms_t},
        "surgery_risk_tone": {"verdict": sr_v, "reason": sr_r, "tier": sr_t},
        "preventive_risk": {"verdict": pr_v, "reason": pr_r, "tier": pr_t},
        "recovery_capacity": {"verdict": rc_v, "reason": rc_r, "tier": rc_t},
    }

    sub_flags = {
        "vitality_score": vitality_score,
        "vitality_risk": vitality_risk,
        "moon_afflicted": bool(moon_aff),
        "chronic_pressure": ch_v == "RED",
        "mental_pressure": ms_v == "RED",
        "surgery_caution": sr_v == "RED",
        "immune_weak": ov_v == "RED",
    }

    return {
        "ascendant": asc if isinstance(asc, str) else str(asc_si),
        "asc_si": asc_si,
        "house_lords": lord_states,
        "karakas": karakas,
        "afflictions": afflictions[:8],
        "dimensions": dimensions,
        "sub_flags": sub_flags,
        "vitality_score": vitality_score,
        "vitality_risk": vitality_risk,
    }

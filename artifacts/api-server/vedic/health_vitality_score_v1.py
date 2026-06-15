"""
Life Map Health hero score — health_engine_v1 layers (Tridosha separate).

Vitality 0–100 = D1×40% + D9×30% + KP 6/8/12 CSL×20% + Dasha×10%
Higher score = stronger vitality / lower structural health risk.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from event_timing.health.health_engine_v1 import (
    _SIGNS,
    _compute_age,
    _current_dasha_lords,
    _flatten_dasha_chain,
    _house_lord,
    _parse_dob_dt,
    _sign_idx,
    _step1_d1_filter,
    _step2_d9_verify,
    _step3_kp_layer,
    _step4_rank,
    _step5_dasha_activation,
)

_W_D1, _W_D9, _W_KP, _W_DASHA = 0.40, 0.30, 0.20, 0.10

_DASHA_VITALITY = {
    "Jupiter": 92,
    "Venus": 82,
    "Mercury": 76,
    "Moon": 72,
    "Sun": 68,
    "Mars": 48,
    "Saturn": 42,
    "Rahu": 38,
    "Ketu": 42,
}


def _clamp(n: float, lo: float = 25.0, hi: float = 95.0) -> float:
    return max(lo, min(hi, n))


def _resolve_lagna_si(kundli: dict) -> Optional[int]:
    asc = kundli.get("ascendant")
    lagna_si = _sign_idx(asc) if isinstance(asc, str) else None
    if lagna_si is not None:
        return lagna_si
    for key in ("lagnaSign", "ascendant_sign", "ascendantSign", "ascendantSignIndex"):
        v = kundli.get(key)
        if isinstance(v, str):
            lagna_si = _sign_idx(v)
        elif isinstance(v, int):
            lagna_si = int(v) % 12
        if lagna_si is not None:
            return lagna_si
    return None


def _score_d1_layer(d1_map: Dict[str, Dict[str, Any]]) -> float:
    survivors = [p for p, info in d1_map.items() if info.get("in_filter")]
    if not survivors:
        return 88.0
    loads = [float(d1_map[p]["d1"]) for p in survivors]
    avg_load = sum(loads) / len(loads)
    # Step-1 loads typically 12–50+ for health significators
    vitality = 100.0 - (avg_load / 48.0) * 72.0
    vitality -= min(12.0, len(survivors) * 1.5)
    lagna_lord = None
    return _clamp(vitality)


def _score_d9_layer(d9_scores: Dict[str, float]) -> float:
    if not d9_scores:
        return 58.0
    avg = sum(d9_scores.values()) / len(d9_scores)
    return _clamp((avg / 25.0) * 100.0)


def _score_kp_layer(kp_layer: Dict[str, Any]) -> float:
    score = 72.0
    for key, penalty, bonus in (
        ("verdict_6", 14.0, 10.0),
        ("verdict_8", 14.0, 10.0),
        ("verdict_12", 12.0, 8.0),
    ):
        v = str(kp_layer.get(key) or "")
        if v.endswith("_YES"):
            score -= penalty
        elif v.endswith("_NO"):
            score += bonus
    at_risk = kp_layer.get("at_risk_planets") or []
    score -= min(18.0, len(at_risk) * 5.0)
    if kp_layer.get("active_csl_planets"):
        score -= 8.0
    if not kp_layer.get("csl_6") and not kp_layer.get("csl_8"):
        score = min(score, 62.0)
    return _clamp(score)


def _dasha_lord_vitality(lord: Optional[str]) -> float:
    if not lord:
        return 62.0
    return float(_DASHA_VITALITY.get(str(lord).strip().title(), 60))


def _score_dasha_layer(
    kundli: dict,
    chain: List[Dict[str, Any]],
    ranked: List[Dict[str, Any]],
    lagna_si: int,
    current_dasha: Dict[str, Optional[str]],
    now: datetime,
) -> float:
    windows = _step5_dasha_activation(chain, ranked, lagna_si, now)
    current = next((w for w in windows if w["start"] <= now <= w["end"]), None)
    if current:
        net = float(current.get("score") or 0.0)
        return _clamp(88.0 - net * 5.5)

    cd = kundli.get("currentDasha") or {}
    md = current_dasha.get("md") or cd.get("maha") or cd.get("md")
    ad = current_dasha.get("ad") or cd.get("antar") or cd.get("ad")
    pd = current_dasha.get("pd") or cd.get("pratyantar") or cd.get("pd")
    return _clamp(
        _dasha_lord_vitality(md) * 0.25
        + _dasha_lord_vitality(ad) * 0.50
        + _dasha_lord_vitality(pd) * 0.25
    )


def _risk_from_score(score: int) -> str:
    if score >= 70:
        return "Low"
    if score >= 50:
        return "Moderate"
    return "High"


def _summary_from_score(score: int, risk: str) -> str:
    if risk == "Low":
        return "Aapki health energy strong dikh rahi hai. Routine maintain karein, sab achha rahega."
    if risk == "Moderate":
        return "Health mixed phase mein hai. Sleep, food aur stress management pe dhyan dein — chhoti aadat badi rakshak hoti hai."
    return "Body abhi extra care maang rahi hai. Kuch areas mein dhyan dene se bade issue tale ja sakte hain. Doctor consult zaroori lagey to lein."


def compute_health_vitality_score(kundli: dict) -> Dict[str, Any]:
    """Return Life Map hero vitality score from health_engine_v1 layers."""
    planets = kundli.get("planets") or []
    if not planets:
        return {
            "score": 50,
            "risk": "Moderate",
            "summary": _summary_from_score(50, "Moderate"),
            "engine": "health_vitality_v1",
            "layer_scores": {},
            "error": "planets missing",
        }

    lagna_si = _resolve_lagna_si(kundli)
    if lagna_si is None:
        return {
            "score": 50,
            "risk": "Moderate",
            "summary": _summary_from_score(50, "Moderate"),
            "engine": "health_vitality_v1",
            "layer_scores": {},
            "error": "lagna missing",
        }

    kp = kundli.get("kp") or {}
    now = datetime.utcnow()
    birth_dt = _parse_dob_dt(None, kundli=kundli)
    age = _compute_age(birth_dt, now)

    d1_map = _step1_d1_filter(kundli, lagna_si, user_age=age)
    survivors = {p for p, info in d1_map.items() if info.get("in_filter")}
    d9_scores = _step2_d9_verify(kundli, survivors)
    chain = _flatten_dasha_chain(kundli)
    current_dasha = _current_dasha_lords(chain, now)
    kp_layer = _step3_kp_layer(
        kp,
        lagna_si,
        d1_map=d1_map,
        d9_scores=d9_scores,
        current_dasha=current_dasha,
    )
    ranked = _step4_rank(d1_map, d9_scores, kp, lagna_si, kp_layer=kp_layer)

    d1_s = _score_d1_layer(d1_map)
    d9_s = _score_d9_layer(d9_scores)
    kp_s = _score_kp_layer(kp_layer)
    dasha_s = _score_dasha_layer(kundli, chain, ranked, lagna_si, current_dasha, now)

    raw = d1_s * _W_D1 + d9_s * _W_D9 + kp_s * _W_KP + dasha_s * _W_DASHA
    score = int(round(_clamp(raw)))

    risk = _risk_from_score(score)
    layer_scores = {
        "d1": round(d1_s, 1),
        "d9": round(d9_s, 1),
        "kp_csl": round(kp_s, 1),
        "dasha": round(dasha_s, 1),
        "weights": {"d1": _W_D1, "d9": _W_D9, "kp_csl": _W_KP, "dasha": _W_DASHA},
    }

    return {
        "score": score,
        "risk": risk,
        "summary": _summary_from_score(score, risk),
        "engine": "health_vitality_v1",
        "layer_scores": layer_scores,
        "kp_layer": {
            "csl_6": kp_layer.get("csl_6"),
            "csl_8": kp_layer.get("csl_8"),
            "csl_12": kp_layer.get("csl_12"),
            "verdict_6": kp_layer.get("verdict_6"),
            "verdict_8": kp_layer.get("verdict_8"),
            "verdict_12": kp_layer.get("verdict_12"),
        },
        "dasha_now": {
            "md": current_dasha.get("md"),
            "ad": current_dasha.get("ad"),
            "pd": current_dasha.get("pd"),
        },
        "survivors": sorted(survivors),
    }

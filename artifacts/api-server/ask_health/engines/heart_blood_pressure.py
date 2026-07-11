"""Heart & blood pressure — production static health engine (D1 + D9, no KP/AV/Jaimini)."""

from __future__ import annotations

import re
from typing import Any

from stock_engine.stock_facts import (
    _DIGNITY_SCORE,
    _aspects,
    _planet_by_name,
    _planet_dignity,
    _planets_in_house,
)

from ..types import EngineResult
from ._health_base import (
    affliction_lines,
    dim,
    dim_evidence,
    dusthana_chart_evidence,
    karaka_evidence,
    load_facts,
    lord_evidence,
    sub_flag,
    vitality_line,
)

_DUSTHANA = (6, 8, 12)
_MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}

_HEART_BP_RX = re.compile(
    r"(?ix)(?:\b("
    r"heart|cardiac|cardio|blood\s+pressure|\bbp\b|hypertension|hypotension|"
    r"chest\s+(?:pain|discomfort|pressure|tight)|seene\s+me|circulation|"
    r"hriday|hryday|"
    r"dil\s+ki\s+sehat|dil\s+ka\s+dard|dil\s+me\s+dard|dil\s+ki\s+bimari|"
    r"dil\s+aur\s+bp|dil\s+ki\s+tabiyat|"
    r"दिल|हृदय|ब्लड\s+प्रेशर|रक्तचाप"
    r")\b|"
    r"dil.{0,25}\b(sehat|bp|weak|dard|pain|bimari|tabiyat|pressure)\b)"
)


def detect_heart_blood_pressure_archetype(question: str) -> bool:
    return bool(_HEART_BP_RX.search((question or "").strip()))


def _d9_planet_tier(kundli: dict, pname: str) -> str:
    """D9 dignity tier for heart karakas — strong / weak / neutral / unavailable."""
    d9 = None
    dv = (kundli or {}).get("divisionalCharts") or {}
    d9 = dv.get("D9") or dv.get("d9")
    if not (isinstance(d9, dict) and d9.get("planets")):
        try:
            from divisional_charts import compute_d9

            lagna_lon = (kundli or {}).get("lagnaLongitude") or (kundli or {}).get("lagna_lon")
            d9 = compute_d9((kundli or {}).get("planets") or [], lagna_lon=lagna_lon)
        except Exception:
            return "unavailable"
    if not isinstance(d9, dict) or not d9.get("planets"):
        return "unavailable"
    dig = _planet_dignity(d9.get("planets") or [], pname)
    sc = _DIGNITY_SCORE.get(dig, 0)
    if sc >= 2:
        return "strong"
    if sc <= 0:
        return "weak"
    return "neutral"


def _house_occupants(kundli: dict, house: int) -> list[str]:
    return _planets_in_house((kundli or {}).get("planets") or [], house)


def _is_dusthana_lord(facts: dict, planet: str) -> bool:
    lords = facts.get("house_lords") or {}
    for key in ("h6", "h8", "h12"):
        st = lords.get(key) or {}
        if st.get("lord") == planet:
            return True
    return False


def _benefic_role(facts: dict, kundli: dict, name: str, support_label: str) -> tuple[str, str]:
    """Return (polarity, line) — benefics only protect when functionally supportive."""
    k = (facts.get("karakas") or {}).get(name) or {}
    house = int(k.get("house") or 0)
    dig = k.get("dignity") or "?"
    dig_sc = _DIGNITY_SCORE.get(dig, 0)

    if _is_dusthana_lord(facts, name):
        return (
            "negative",
            f"{name} rules disease house (6/8/12) — {support_label} protection weak",
        )
    if house in _DUSTHANA:
        return (
            "negative",
            f"{name} in dusthana H{house} — {support_label} not clean support",
        )
    if dig_sc <= 0:
        return (
            "negative",
            f"{name} afflicted ({dig}) — {support_label} support limited",
        )
    if dig_sc >= 2 or _aspects(name, house, 4) or house in (1, 4, 5, 9, 10, 11):
        return (
            "positive",
            f"{name} supportive ({dig}, H{house}) — {support_label} protection active",
        )
    return (
        "neutral",
        f"{name} mixed ({dig}, H{house}) — partial {support_label} support",
    )


def _score_heart_bp(facts: dict, kundli: dict) -> tuple[int, list[tuple[str, str]], list[tuple[str, str]]]:
    """Return (score, positive_lines, negative_lines)."""
    pos: list[tuple[str, str]] = []
    neg: list[tuple[str, str]] = []
    score = 0
    planets = (kundli or {}).get("planets") or []

    h4_m = _house_occupants(kundli, 4)
    h6_m = _house_occupants(kundli, 6)
    if h4_m:
        mal4 = [p for p in h4_m if p in _MALEFICS]
        if mal4:
            score -= len(mal4)
            neg.append(("negative", f"Malefics in 4th (heart zone): {', '.join(mal4)}"))
        ben4 = [p for p in h4_m if p in _BENEFICS]
        if ben4:
            score += 1
            pos.append(("positive", f"Benefics in 4th: {', '.join(ben4)}"))

    h4 = (facts.get("house_lords") or {}).get("h4") or {}
    h1 = (facts.get("house_lords") or {}).get("h1") or {}
    sun = (facts.get("karakas") or {}).get("Sun") or {}
    moon = (facts.get("karakas") or {}).get("Moon") or {}
    mars = (facts.get("karakas") or {}).get("Mars") or {}
    sat = (facts.get("karakas") or {}).get("Saturn") or {}

    if _DIGNITY_SCORE.get(h4.get("lord_dignity", ""), 0) >= 2:
        score += 2
        pos.append(("positive", "4th lord strong — chest/heart foundation supported"))
    elif h4.get("lord_in_dusthana"):
        score -= 2
        neg.append(("negative", "4th lord in dusthana — heart zone under structural stress"))

    if _DIGNITY_SCORE.get(h1.get("lord_dignity", ""), 0) >= 2 and not h1.get("lord_in_dusthana"):
        score += 1
        pos.append(("positive", "Lagnesh strong — overall body resilience helps heart recovery"))
    elif h1.get("lord_in_dusthana"):
        score -= 1
        neg.append(("negative", "Lagnesh in dusthana — constitution weak for cardio load"))

    sun_d = _DIGNITY_SCORE.get(sun.get("dignity", ""), 0)
    if sun_d >= 2:
        score += 2
        pos.append(("positive", "Sun (heart karaka) strong — vitality pump supported"))
    elif sun_d <= 0:
        score -= 2
        neg.append(("negative", "Sun weak/afflicted — core heart energy under pressure"))

    moon_d = _DIGNITY_SCORE.get(moon.get("dignity", ""), 0)
    if sub_flag(facts, "moon_afflicted"):
        score -= 2
        neg.append(("negative", "Moon afflicted — stress/BP fluctuation tendency"))
    elif moon_d >= 2:
        score += 1
        pos.append(("positive", "Moon stable — emotional stress less likely to spike BP"))

    mars_h = int(mars.get("house") or 0)
    if mars_h in (1, 4, 6, 8, 12):
        score -= 1
        neg.append(("negative", f"Mars (blood/pressure) in sensitive H{mars_h} — circulation heat"))
    elif mars_h in (3, 6, 10, 11):
        score -= 1
        neg.append(("negative", f"Mars in H{mars_h} — BP/circulation reactivity possible"))

    sat_h = int(sat.get("house") or 0)
    if sat_h in (1, 4, 6, 8):
        score -= 1
        neg.append(("negative", f"Saturn on heart axis H{sat_h} — chronic BP/ blockage tone"))
    if sat_h in (6, 8, 12):
        score -= 1

    for mal in ("Rahu", "Ketu"):
        mk = (facts.get("karakas") or {}).get(mal) or {}
        mh = int(mk.get("house") or 0)
        if mh in (1, 4, 6, 8):
            score -= 1
            neg.append(("negative", f"{mal} in H{mh} — irregular/cardio stress signal"))

    if h6_m:
        score -= min(2, len([p for p in h6_m if p in _MALEFICS]))
        if any(p in _MALEFICS for p in h6_m):
            neg.append(("negative", f"Disease house pressure — malefics in 6th: {', '.join(h6_m)}"))

    for pname, lbl in (("Jupiter", "circulation/wisdom"), ("Venus", "comfort/recovery")):
        pol, line = _benefic_role(facts, kundli, pname, lbl)
        if pol == "positive":
            score += 1
            pos.append((pol, line))
        elif pol == "negative":
            score -= 1
            neg.append((pol, line))

    rc = dim(facts, "recovery_capacity")
    if rc.get("verdict") == "GREEN":
        score += 1
        pos.append(("positive", "Recovery capacity strong — healing response better after stress"))
    elif rc.get("verdict") == "RED":
        score -= 1
        neg.append(("negative", "Recovery axis weak — heart issues may linger without care"))

    return score, pos, neg


def _severity(score: int) -> str:
    if score >= 2:
        return "Low"
    if score <= -2:
        return "High"
    return "Moderate"


def _verdict_from_severity(severity: str) -> tuple[str, str]:
    if severity == "Low":
        return (
            "Heart/BP tone relatively supported — routine lifestyle + annual checkup wise",
            "high",
        )
    if severity == "High":
        return (
            "Heart/BP zone under notable pressure — doctor monitoring important, self-diagnosis mat karo",
            "medium",
        )
    return (
        "Heart/BP mixed pattern — stress, salt/sleep discipline aur checkup help karenge",
        "medium",
    )


def run_heart_blood_pressure(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    score, pos_lines, neg_lines = _score_heart_bp(facts, kundli)
    severity = _severity(score)
    verdict, confidence = _verdict_from_severity(severity)

    evidence: list[str] = ["System focus: Heart & blood pressure"]
    evidence.append(vitality_line(facts))
    evidence.append(lord_evidence(facts, "h1", "Lagna (constitution)"))
    evidence.append(lord_evidence(facts, "h4", "4th house (heart/chest)"))
    evidence.append(karaka_evidence(facts, "Sun", "Heart karaka (Sun)"))
    evidence.append(karaka_evidence(facts, "Moon", "Mind-stress / BP fluctuation (Moon)"))
    evidence.append(karaka_evidence(facts, "Mars", "Blood pressure / circulation (Mars)"))
    evidence.extend(dusthana_chart_evidence(facts))

    h4_occ = _house_occupants(kundli, 4)
    if h4_occ:
        evidence.append(f"Planets in 4th house: {', '.join(h4_occ)}")

    for pname in ("Sun", "Moon", "Mars"):
        tier = _d9_planet_tier(kundli, pname)
        if tier == "unavailable":
            evidence.append(f"D9 check ({pname}): chart unavailable — D1 weight primary")
        elif tier == "strong":
            evidence.append(f"D9 check ({pname}): strong — deeper heart support")
        elif tier == "weak":
            evidence.append(f"D9 check ({pname}): weak — chronic cardio vulnerability signal")
        else:
            evidence.append(f"D9 check ({pname}): neutral/mixed")

    evidence.append(dim_evidence(facts, "preventive_risk", "Cardio preventive tendency"))
    evidence.append(dim_evidence(facts, "mental_stress", "Stress axis (BP link)"))
    evidence.append(dim_evidence(facts, "recovery_capacity", "Recovery/healing capacity"))
    evidence.extend(affliction_lines(facts, limit=4))

    evidence_positive = [ln for _, ln in pos_lines]
    evidence_negative = [ln for _, ln in neg_lines]
    evidence.append(f"Severity score: {severity} (engine score {score:+d})")

    ignore = [
        "disease names",
        "death",
        "cure guarantee",
        "diagnosis",
        "surgery date",
        "dasha",
        "transit",
        "muhurat",
    ]

    return EngineResult(
        archetype="heart_blood_pressure",
        verdict=verdict,
        confidence=confidence,
        word_budget=110 if wants_explain else 95,
        answer_plan=(
            "Heart/BP tendency from curated D1+D9 evidence — NO diagnosis, NO dates. "
            "Dasha/transit only if user explicitly asked timing (handled elsewhere)."
        ),
        summary=[
            "Heart & blood pressure subdomain.",
            "Doctor for symptoms — chart = tendency only.",
            f"Severity: {severity}.",
        ],
        evidence=evidence,
        evidence_positive=evidence_positive,
        evidence_negative=evidence_negative,
        ignore=ignore,
        checks={
            "slice_type": "health_engine_v1",
            "archetype": "heart_blood_pressure",
            "severity": severity,
            "engine_score": score,
            "positive_count": len(evidence_positive),
            "negative_count": len(evidence_negative),
        },
    )

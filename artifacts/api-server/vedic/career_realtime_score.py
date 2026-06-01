"""
Realtime career strength score (0–100).

Combines natal chart (base) + current MD/AD/PD + live transits.
Designed for a single score number that can shift over time.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
EXALT = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
    "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra",
}
DEBIL = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
    "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
}
OWN = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
}

DASHA_CAREER = {
    "Jupiter": 8, "Sun": 7, "Mercury": 6, "Saturn": 5, "Mars": 3,
    "Venus": 2, "Moon": 0, "Rahu": -3, "Ketu": -5,
}


def _find_planet(planets: List[dict], name: str) -> Optional[dict]:
    for p in planets:
        if p.get("name") == name:
            return p
    return None


def _clamp_score(n: float) -> int:
    return int(max(20, min(95, round(n))))


def _trend_summary(score: int) -> Tuple[str, str]:
    if score >= 70:
        return (
            "Good",
            "Career support is strong in the current phase. Steady effort can convert into visible progress.",
        )
    if score >= 50:
        return (
            "Average",
            "Mixed career phase. Progress is possible with patience, planning, and the right timing.",
        )
    return ("Risk", "")


def _score_label(score: int) -> str:
    if score >= 70:
        return "Strong Growth Potential"
    if score >= 50:
        return "Steady Progress Phase"
    return "Build Skills First"


def _natal_component(planets: List[dict], asc_idx: int) -> Tuple[float, List[str]]:
    score = 50.0
    reasons: List[str] = []
    benefics = {"Jupiter", "Venus", "Mercury"}
    sign_10 = SIGNS[(asc_idx + 9) % 12]
    lord_10 = SIGN_LORD[sign_10]

    for p in planets:
        if p.get("house") != 10:
            continue
        nm = p.get("name")
        if nm in benefics:
            score += 6
            reasons.append(f"{nm} in 10th — career support")
        elif nm == "Sun":
            score += 8
            reasons.append("Sun in 10th — authority & visibility")
        elif nm == "Saturn":
            score += 5
            reasons.append("Saturn in 10th — long-term career builder")
        elif nm == "Mars":
            score += 4
        elif nm == "Rahu":
            score += 3
        elif nm == "Ketu":
            score -= 4

    lord_p = _find_planet(planets, lord_10)
    if lord_p:
        lh = int(lord_p.get("house") or 0)
        lsign = lord_p.get("sign") or ""
        if lh in (1, 4, 5, 7, 9, 10, 11):
            score += 7
            reasons.append(f"10th lord {lord_10} in {lh}th — favorable placement")
        elif lh == 6:
            score += 2
            reasons.append(f"10th lord {lord_10} in 6th — service/professional craft")
        elif lh == 8:
            score -= 3
            if lord_10 in ("Mercury", "Saturn", "Jupiter"):
                score += 5
                reasons.append(f"10th lord {lord_10} in 8th — research/finance/specialist path")
            else:
                reasons.append(f"10th lord {lord_10} in 8th — variable career phase")
        elif lh == 12:
            score -= 5
            reasons.append(f"10th lord {lord_10} in 12th — behind-the-scenes or foreign tilt")

        if lord_10 in EXALT and lsign == EXALT[lord_10]:
            score += 6
        elif lord_10 in DEBIL and lsign == DEBIL[lord_10]:
            score -= 6
        elif lsign in OWN.get(lord_10, []):
            score += 4

    for p in planets:
        if p.get("house") == 11 and p.get("name") in benefics.union({"Jupiter"}):
            score += 4
        if p.get("house") == 6 and p.get("name") in ("Mars", "Saturn", "Sun"):
            score += 3
        if p.get("house") == 6 and p.get("name") == "Mercury":
            score += 4
            reasons.append("Mercury in 6th — analyst/consultant profession")

    sat = _find_planet(planets, "Saturn")
    if sat:
        ssg = sat.get("sign", "")
        if ssg == EXALT["Saturn"]:
            score += 5
        elif ssg == DEBIL["Saturn"]:
            score -= 5

    sun = _find_planet(planets, "Sun")
    if sun:
        ssg = sun.get("sign", "")
        if ssg == EXALT["Sun"]:
            score += 4
        elif ssg == DEBIL["Sun"]:
            score -= 4

    moon = _find_planet(planets, "Moon")
    if moon and (moon.get("sign") or "") == DEBIL["Moon"]:
        score -= 1
        reasons.append("Moon debilitated — focus on emotional consistency (timing factor)")

    return score, reasons


def _d10_component(kundli: dict) -> Tuple[float, List[str]]:
    score = 0.0
    reasons: List[str] = []
    d10 = (kundli.get("divisionalCharts") or {}).get("D10") or {}
    benefics = {"Jupiter", "Venus", "Mercury"}
    for p in d10.get("planets") or []:
        if p.get("house") != 10:
            continue
        nm = p.get("name")
        if nm in benefics:
            score += 4
            reasons.append(f"D10: {nm} in 10th — refined career karma")
        elif nm == "Sun":
            score += 5
    return score, reasons


def _dasha_component(cd: dict) -> Tuple[float, List[str], Dict[str, Any]]:
    md = cd.get("maha") or ""
    ad = cd.get("antar") or ""
    pd = cd.get("pratyantar") or ""
    delta = 0.0
    reasons: List[str] = []
    breakdown: Dict[str, Any] = {"md": md, "ad": ad, "pd": pd, "md_pts": 0, "ad_pts": 0, "pd_pts": 0}

    if md in DASHA_CAREER:
        pts = float(DASHA_CAREER[md])
        delta += pts
        breakdown["md_pts"] = pts
        reasons.append(
            f"Mahadasha {md} — {'supportive' if pts >= 0 else 'challenging'} for career ({pts:+.0f})"
        )
    if ad in DASHA_CAREER:
        pts = float(DASHA_CAREER[ad] // 2)
        delta += pts
        breakdown["ad_pts"] = pts
        reasons.append(f"Antardasha {ad} — current sub-period ({pts:+.0f})")
    if pd in DASHA_CAREER:
        pts = float(DASHA_CAREER[pd] // 3)
        delta += pts
        breakdown["pd_pts"] = pts
        reasons.append(f"Pratyantar {pd} — near-term window ({pts:+.0f})")

    end = cd.get("endDate") or ""
    if end:
        breakdown["phase_ends"] = end
    return delta, reasons, breakdown


def _transit_component(asc_idx: int) -> Tuple[float, List[str]]:
    delta = 0.0
    notes: List[str] = []
    try:
        import swisseph as swe

        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        jd_now = swe.julday(*datetime.utcnow().timetuple()[:3], 12.0)

        def _house_for_planet(pid: int) -> int:
            res = swe.calc_ut(jd_now, pid, flags)
            t_lon = res[0][0] % 360
            t_sign = SIGNS[int(t_lon // 30)]
            return ((SIGNS.index(t_sign) - asc_idx + 12) % 12) + 1

        jup_h = _house_for_planet(swe.JUPITER)
        if jup_h in (2, 6, 10, 11):
            delta += 4
            notes.append(f"Jupiter transiting {jup_h}th — growth support active")

        sat_h = _house_for_planet(swe.SATURN)
        if sat_h == 10:
            delta += 2
            notes.append("Saturn transiting 10th — career restructuring / discipline phase")
        elif sat_h in (4, 8, 12):
            delta -= 4
            notes.append(f"Saturn transiting {sat_h}th — slower progress phase")

        rahu_h = _house_for_planet(swe.TRUE_NODE)
        if rahu_h in (10, 11):
            delta += 2
            notes.append(f"Rahu transiting {rahu_h}th — unconventional opportunity phase")
        elif rahu_h in (8, 12):
            delta -= 2
    except Exception:
        pass

    return delta, notes


def apply_commercial_bonus(score: int, commercial_score: int) -> Tuple[int, Optional[str]]:
    if commercial_score >= 22:
        return min(95, score + 5), "Strong commercial-profession chart — specialist careers supported"
    if commercial_score >= 15:
        return min(95, score + 3), "Commercial-profession indicators add career flexibility"
    return score, None


def compute_career_realtime_score(
    planets: List[dict],
    asc_idx: int,
    kundli: Optional[dict] = None,
) -> Dict[str, Any]:
    kundli = kundli or {}
    cd = kundli.get("currentDasha") or {}

    natal, natal_reasons = _natal_component(planets, asc_idx)
    d10_delta, d10_reasons = _d10_component(kundli)
    dasha_delta, dasha_reasons, dasha_breakdown = _dasha_component(cd)
    transit_delta, transit_notes = _transit_component(asc_idx)

    natal_total = natal + d10_delta
    phase_total = dasha_delta + transit_delta
    final = _clamp_score(natal_total + phase_total)

    trend, summary = _trend_summary(final)
    reasons = (natal_reasons + d10_reasons + dasha_reasons)[:8]

    md, ad, pd = dasha_breakdown.get("md"), dasha_breakdown.get("ad"), dasha_breakdown.get("pd")
    parts = [p for p in (md, ad, pd) if p]
    dasha_line = " · ".join(parts) if parts else ""
    end = dasha_breakdown.get("phase_ends") or cd.get("endDate") or ""
    score_context = "Chart + current dasha & transits (updates over time)"
    if dasha_line and end:
        score_context = f"{score_context} · {dasha_line} until {end}"
    elif dasha_line:
        score_context = f"{score_context} · {dasha_line}"

    return {
        "score": final,
        "trend": trend,
        "summary": summary,
        "score_label": _score_label(final),
        "score_context": score_context,
        "reasons": reasons,
        "transit_notes": transit_notes[:4],
        "dasha_breakdown": dasha_breakdown,
        "natal_component": round(natal_total, 1),
        "phase_component": round(phase_total, 1),
    }

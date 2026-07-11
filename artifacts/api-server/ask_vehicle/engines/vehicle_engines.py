from __future__ import annotations

import re

from chart_tone_disclaimers import CHART_TONE_HI, HEURISTIC_HI, MUHURAT_HI

from ..types import EngineResult
from ._vehicle_base import (
    dimension_lines,
    house_axis,
    planet_line,
    reader,
    vehicle_snapshot,
    vehicle_strength_score,
)

_COLOUR_ALIASES = {
    "black": ("black", "kala", "dark"),
    "white": ("white", "safed", "silver", "cream", "pearl"),
    "red": ("red", "lal", "maroon"),
    "blue": ("blue", "navy"),
    "green": ("green", "hara"),
    "yellow": ("yellow", "gold"),
    "grey": ("grey", "gray"),
}


def _themed(
    *,
    archetype: str,
    kundli: dict,
    wants_explain: bool,
    verdict: str,
    summary: list[str],
    ignore: list[str] | None = None,
) -> EngineResult:
    score, label = vehicle_strength_score(kundli)
    evidence = vehicle_snapshot(kundli)
    evidence.append(f"Vehicle strength index {score}/100 — {label}.")
    return EngineResult(
        archetype=archetype,
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan=f"Direct vehicle answer for {archetype.replace('_', ' ')}.",
        summary=summary,
        evidence=evidence[:12],
        ignore=ignore or ["timing", "exact model", "exact price", "accident guarantee"],
        checks={"slice_type": "vehicle_engine_v1", "archetype": archetype, "vehicle_score": score},
    )


def _normalize_colour_token(token: str) -> str:
    t = (token or "").strip().lower()
    for canon, aliases in _COLOUR_ALIASES.items():
        if t == canon or t in aliases:
            return canon
    return t


def _mentioned_colours(question: str) -> list[str]:
    q = (question or "").lower()
    found: list[str] = []
    for canon, aliases in _COLOUR_ALIASES.items():
        if any(re.search(rf"\b{re.escape(alias)}\b", q) for alias in (canon, *aliases)):
            if canon not in found:
                found.append(canon)
    return found


def _chart_colour_pick(kundli: dict) -> tuple[str, str, str]:
    """Return (best, alt, colour_evidence_line)."""
    colour_line = next((d for d in dimension_lines(kundli) if d.startswith("Colour:")), "")
    best, alt = "white", "silver"
    if colour_line and "best=" in colour_line:
        try:
            best = _normalize_colour_token(colour_line.split("best=")[1].split()[0])
            if " alt=" in colour_line:
                alt = _normalize_colour_token(colour_line.split(" alt=")[1].split()[0])
        except Exception:
            pass
    else:
        try:
            from vehicle_static.vehicle_engine import compute_vehicle_facts

            dim = (compute_vehicle_facts(kundli).get("dimensions") or {}).get("colour") or {}
            best = _normalize_colour_token(str(dim.get("best") or best))
            alt = _normalize_colour_token(str(dim.get("alt") or alt))
            colour_line = (
                f"Colour: best={best} alt={alt} — {dim.get('reason', '')}"
                if dim
                else colour_line
            )
        except Exception:
            pass
    return best, alt, colour_line


def _colour_fit_score(choice: str, best: str, alt: str) -> int:
    c = _normalize_colour_token(choice)
    b = _normalize_colour_token(best)
    a = _normalize_colour_token(alt)
    if c == b:
        return 3
    if c == a:
        return 2
    if c in ("white", "silver") and b in ("white", "silver"):
        return 2
    if c in ("black", "grey") and b in ("black", "grey"):
        return 2
    return 1


def run_vehicle_colour(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    best, alt, colour_line = _chart_colour_pick(kundli)
    mentioned = _mentioned_colours(question)

    if len(mentioned) >= 2:
        ranked = sorted(
            mentioned,
            key=lambda c: _colour_fit_score(c, best, alt),
            reverse=True,
        )
        winner = ranked[0]
        loser = ranked[-1]
        verdict = (
            f"Between {mentioned[0]} vs {mentioned[1]}: chart colour axis favours "
            f"{winner} over {loser} — chart best={best}, alt={alt}. "
            f"{winner.title()} zyada aligned; {loser} thoda heavy/off-tone ho sakta hai."
        )
        summary = [
            "QUESTION FOCUS: do colour options compare — pick chart-aligned shade.",
            f"LOCKED_PICK: {winner} (chart best={best}, alt={alt}).",
            CHART_TONE_HI,
        ]
    elif len(mentioned) == 1:
        pick = mentioned[0]
        fit = _colour_fit_score(pick, best, alt)
        if fit >= 2:
            verdict = (
                f"{pick.title()} colour chart ke saath aligned dikhta hai "
                f"(chart best={best}, alt={alt})."
            )
        else:
            verdict = (
                f"{pick.title()} lena possible hai lekin chart tone {best}/{alt} zyada supportive hai — "
                f"{pick} thoda off-axis ho sakta hai."
            )
        summary = [
            "QUESTION FOCUS: single named colour vs chart palette.",
            f"LOCKED_PICK: {best} primary, {alt} alternate.",
            CHART_TONE_HI,
        ]
    elif colour_line:
        verdict = f"Chart colour tone: {best} primary, {alt} alternate — palette supportive"
        summary = [
            "QUESTION FOCUS: gaadi colour — chart aesthetic tone only.",
            f"LOCKED_PICK: {best} primary, {alt} alternate.",
            CHART_TONE_HI,
        ]
    else:
        verdict = f"Colour advisory: {best} primary, {alt} alternate — aesthetic/comfort axis se"
        summary = [
            "QUESTION FOCUS: gaadi colour — chart aesthetic tone only.",
            CHART_TONE_HI,
        ]

    return _themed(
        archetype="vehicle_colour",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict=f"{verdict} | {CHART_TONE_HI}",
        summary=summary,
    )


def run_vehicle_new_used(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    tc = next((d for d in dimension_lines(kundli) if d.startswith("Vehicle type:")), "")
    verdict = tc.replace("Vehicle type: ", "") if tc else "New vs used: chart mixed — budget aur EMI plan decide karega"
    return _themed(
        archetype="vehicle_new_used",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict=f"{verdict} | {HEURISTIC_HI}",
        summary=[
            "QUESTION FOCUS: nayi vs purani / 2W vs 4W — affordability heuristic.",
            HEURISTIC_HI,
        ],
    )


def run_vehicle_safety(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = vehicle_snapshot(kundli)
    evidence.append(planet_line(r, "Mars", "accident/collision tone"))
    evidence.append(planet_line(r, "Rahu", "theft/sudden loss complexity"))
    safety = next((d for d in dimension_lines(kundli) if d.startswith("Vehicle safety:")), "")
    verdict = (
        safety.replace("Vehicle safety: ", "")
        if safety
        else "Safety axis mixed — insurance + disciplined driving essential; no fear guarantee"
    )
    return EngineResult(
        archetype="vehicle_safety",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Safety answer → 8H/4H + Mars/Rahu — caution not alarm.",
        summary=["QUESTION FOCUS: accident/chori/insurance — NEVER guarantee outcome."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed accident", "guaranteed theft", "exact event"],
        checks={"slice_type": "vehicle_engine_v1", "archetype": "vehicle_safety"},
    )


def run_vehicle_luxury(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    lux = next((d for d in dimension_lines(kundli) if d.startswith("Luxury tier:")), "")
    verdict = lux.replace("Luxury tier: ", "") if lux else "Luxury vs budget: mid-range comfortable vehicle zyada aligned"
    return _themed(
        archetype="vehicle_luxury",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict=verdict,
        summary=["QUESTION FOCUS: luxury car sukh — NOT exact brand/model promise."],
    )


def run_vehicle_commercial(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    comm = next((d for d in dimension_lines(kundli) if d.startswith("Vehicle commercial:")), "")
    verdict = comm.replace("Vehicle commercial: ", "") if comm else "Commercial vehicle business mixed — license + cashflow plan pehle"
    return _themed(
        archetype="vehicle_commercial",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict=verdict,
        summary=["QUESTION FOCUS: taxi/truck/commercial — NOT route profit guarantee."],
    )


def run_vehicle_loan(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = vehicle_snapshot(kundli)
    evidence.append(house_axis(r, 6, "6H loan/EMI axis"))
    evidence.append(house_axis(r, 12, "12H expense drain axis"))
    readiness = next((d for d in dimension_lines(kundli) if d.startswith("Vehicle readiness:")), "")
    verdict = (
        "Vehicle loan theme: EMI serviceability + down-payment planning matter most — bank approval practical check"
    )
    if "STRONG" in readiness:
        verdict = "Loan pass tone supportive — readiness strong; phir bhi CIBIL/down-payment verify karein"
    elif "WEAK" in readiness:
        verdict = "Loan me zyada down-payment ya co-applicant plan better — readiness abhi tight"
    return EngineResult(
        archetype="vehicle_loan",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Vehicle loan → 6H/12H + readiness dim.",
        summary=["QUESTION FOCUS: gaadi loan/down-payment — NOT bank approval guarantee."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed approval", "exact EMI"],
        checks={"slice_type": "vehicle_engine_v1", "archetype": "vehicle_loan"},
    )


def run_vehicle_ownership(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    own = next((d for d in dimension_lines(kundli) if d.startswith("Vehicle ownership:")), "")
    verdict = own.replace("Vehicle ownership: ", "") if own else "Self naam practical; company naam tax planning ke liye advisor se confirm"
    return _themed(
        archetype="vehicle_ownership",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict=verdict,
        summary=["QUESTION FOCUS: naam par gaadi — tax/legal advisor for company name."],
        ignore=["timing", "tax guarantee"],
    )


def run_vehicle_ev(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    tc = next((d for d in dimension_lines(kundli) if d.startswith("Vehicle type:")), "")
    verdict = tc if tc else "EV vs fuel: chart se practical commute + charging infra decide karega"
    return _themed(
        archetype="vehicle_ev",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict=f"{verdict} | {HEURISTIC_HI}",
        summary=[
            "QUESTION FOCUS: EV vs petrol/diesel — chart heuristic, charging infra practical.",
            HEURISTIC_HI,
        ],
    )


def run_vehicle_multi(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    score, label = vehicle_strength_score(kundli)
    if score >= 68:
        verdict = "Multiple vehicles ka yog supportive — 11H gain + Venus tone favour extra conveyance"
    elif score >= 52:
        verdict = "Doosri gaadi possible lekin spacing aur budget plan dono zaroori"
    else:
        verdict = "Pehli gaadi stable hone ke baad doosri sochna better — abhi focus ek par"
    return _themed(
        archetype="vehicle_multi",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict=verdict,
        summary=["QUESTION FOCUS: ek se zyada gaadi — NOT exact count guarantee."],
    )


def run_vehicle_festival(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed(
        archetype="vehicle_festival",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict=(
            "Festival purchase: Shukra/Mangal strong hone par Diwali/Dhanteras buying feel supportive — "
            f"exact tithi/muhurat nahi. | {MUHURAT_HI}"
        ),
        summary=[
            "QUESTION FOCUS: festival buying tone — NOT computed panchang.",
            MUHURAT_HI,
        ],
        ignore=["exact date", "exact muhurat minute", "panchang guarantee"],
    )


def run_vehicle_growth(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = vehicle_snapshot(kundli)
    evidence.append(house_axis(r, 10, "10H career/status axis"))
    return _themed(
        archetype="vehicle_growth",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict="Vehicle comfort axis job/business mobility support karta hai — growth ka main driver career dasha hai",
        summary=["QUESTION FOCUS: gaadi se growth — mobility support, not sole success factor."],
    )


def run_vehicle_family_budget(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    readiness = next((d for d in dimension_lines(kundli) if d.startswith("Vehicle readiness:")), "")
    if "WEAK" in readiness:
        verdict = "Abhi thoda ruk kar bachat better — family priorities pehle, gaadi baad me plan karein"
    else:
        verdict = "Gaadi plan family budget ke saath balance ho sakta hai — EMI ko family goals se align rakhein"
    return _themed(
        archetype="vehicle_family_budget",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict=verdict,
        summary=["QUESTION FOCUS: parivaar budget vs gaadi — practical affordability."],
    )


def run_vehicle_vip(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed(
        archetype="vehicle_vip",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict="VIP number optional luxury hai — cosmetic feel; safety/insurance zyada important. | "
        + CHART_TONE_HI,
        summary=["QUESTION FOCUS: fancy plate — cosmetic chart tone only.", CHART_TONE_HI],
    )


def run_vehicle_driving(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    mars = r.planet("Mars") or {}
    merc = r.planet("Mercury") or {}
    h_mars = mars.get("house")
    if h_mars in {1, 3, 10, 11}:
        verdict = "Driving seekhne ka tone supportive — Mars/Mercury placement favour learning with practice"
    else:
        verdict = "Driving seekh sakte ho — thoda practice aur patience; instructor guided start better"
    return _themed(
        archetype="vehicle_driving",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict=verdict,
        summary=["QUESTION FOCUS: driving ease — NOT license date guarantee."],
    )


def run_vehicle_planning(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    readiness = next((d for d in dimension_lines(kundli) if d.startswith("Vehicle readiness:")), "")
    if "STRONG" in readiness:
        months = "6–12"
        band = "readiness strong"
    elif "MODERATE" in readiness:
        months = "12–18"
        band = "readiness moderate"
    else:
        months = "18–24"
        band = "readiness tight"
    return _themed(
        archetype="vehicle_planning",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict=(
            f"Indicative savings window ({band}): gaadi se pehle ~{months} mahine SIP/bachat plan — "
            f"dasha date nahi. | {CHART_TONE_HI}"
        ),
        summary=[
            "QUESTION FOCUS: planning window from readiness band — NOT dasha-derived month count.",
            CHART_TONE_HI,
        ],
        ignore=["exact date", "exact month count guarantee", "dasha month promise"],
    )


def run_general_vehicle(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    score, label = vehicle_strength_score(kundli)
    return _themed(
        archetype="general_vehicle",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict=f"Overall vehicle chart {label} — 4H/Venus/Mars axis se comfort conveyance theme",
        summary=["OPEN vehicle Q — 4H/11H + Venus/Mars snapshot only."],
    )

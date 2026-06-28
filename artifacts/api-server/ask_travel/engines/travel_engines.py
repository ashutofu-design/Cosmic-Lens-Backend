from __future__ import annotations

import re

from ..types import EngineResult
from ._travel_base import planet_line, reader, travel_snapshot, travel_strength_score


def _themed_result(
    *,
    archetype: str,
    kundli: dict,
    wants_explain: bool,
    focus_label: str,
    verdict_strong: str,
    verdict_mixed: str,
    verdict_weak: str,
    summary_lines: list[str],
    ignore: list[str] | None = None,
) -> EngineResult:
    score, label = travel_strength_score(kundli)
    evidence = travel_snapshot(kundli)
    evidence.append(f"{focus_label}: travel strength index {score}/100 — {label}.")
    if score >= 68:
        verdict, confidence = verdict_strong, "high"
    elif score >= 52:
        verdict, confidence = verdict_mixed, "medium"
    else:
        verdict, confidence = verdict_weak, "medium"
    return EngineResult(
        archetype=archetype,
        verdict=verdict,
        confidence=confidence,
        word_budget=95 if wants_explain else 80,
        answer_plan=f"Direct answer for {archetype.replace('_', ' ')} → 9H/12H/3H + Rahu/Jupiter evidence.",
        summary=summary_lines,
        evidence=evidence[:12],
        ignore=ignore or ["timing", "exact date", "guaranteed visa", "exact country name"],
        checks={"slice_type": "travel_engine_v1", "archetype": archetype, "travel_score": score},
    )


def run_travel_yog(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed_result(
        archetype="travel_yog",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Foreign travel yog",
        verdict_strong="Foreign travel yog strong — chart supports abroad movement with realistic paperwork",
        verdict_mixed="Foreign travel yog moderate — abroad possible with patience and document readiness",
        verdict_weak="Foreign travel yog needs effort — build capacity, language/docs before big move",
        summary_lines=[
            "QUESTION FOCUS: videsh yatra/yog — NOT when you will travel.",
            "Do NOT promise exact country or visa outcome.",
        ],
    )


def run_foreign_settlement(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = travel_snapshot(kundli)
    evidence.append(planet_line(r, "Saturn", "long-stay/immigration tone"))
    score, label = travel_strength_score(kundli)
    evidence.append(f"Settlement axis: 12H/9H + Rahu + 4H anchor review — {label}.")
    if score >= 68:
        verdict = "Foreign settlement theme strong — 12H/9H + Rahu support long-stay abroad with planning"
    elif score >= 52:
        verdict = "Foreign settlement possible — legal route, finances and home-anchor both matter"
    else:
        verdict = "Foreign settlement needs structured effort — strengthen 12H/9H before permanent shift"
    return EngineResult(
        archetype="foreign_settlement",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan="Settlement answer → 12H/9H + Rahu + 4H inverted anchor.",
        summary=["QUESTION FOCUS: permanent abroad basna — NOT exact city/country."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed PR", "exact country"],
        checks={"slice_type": "travel_engine_v1", "archetype": "foreign_settlement", "travel_score": score},
    )


def run_visa_theme(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = travel_snapshot(kundli)
    evidence.append(planet_line(r, "Jupiter", "visa-luck/documentation karaka"))
    evidence.append(planet_line(r, "Saturn", "delay/documentation lessons"))
    q = (question or "").lower()
    if re.search(r"(?ix)\b(reject|refus|deny|problem|stuck)\b", q):
        verdict = (
            "Visa theme shows friction — Saturn/Rahu on 9H/12H axis; "
            "documentation patience needed, not hopeless tone"
        )
    else:
        verdict = (
            "Visa theme from chart: Jupiter + 9H/12H support paperwork luck — "
            "indicative only, not guaranteed approval"
        )
    return EngineResult(
        archetype="visa_theme",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan="Visa answer → Jupiter + 9H/12H + Saturn delay tone.",
        summary=["QUESTION FOCUS: visa approve/reject theme — NOT legal advice or exact date."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed visa", "embassy legal advice"],
        checks={"slice_type": "travel_engine_v1", "archetype": "visa_theme"},
    )


def run_relocation_abroad(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = travel_snapshot(kundli)
    evidence.append(planet_line(r, "Moon", "movement/relocation karaka"))
    p4 = house_axis_inverted(r)
    evidence.append(p4)
    score, label = travel_strength_score(kundli)
    evidence.append(f"Relocation review: {label}.")
    verdict = (
        f"Relocation abroad theme {'strong' if score >= 68 else 'moderate' if score >= 52 else 'needs effort'} — "
        "9H/12H movement with 4H home-anchor check"
    )
    return EngineResult(
        archetype="relocation_abroad",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Relocation → 12H shift + 4H uproot + Moon movement.",
        summary=["QUESTION FOCUS: shift/move abroad — NOT exact address."],
        evidence=evidence[:12],
        ignore=["timing", "exact city", "guaranteed move"],
        checks={"slice_type": "travel_engine_v1", "archetype": "relocation_abroad", "travel_score": score},
    )


def house_axis_inverted(r) -> str:
    from ._travel_base import house_axis

    return house_axis(r, 4, "Home anchor check (4th — strong anchor delays relocation)")


def run_return_india(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = travel_snapshot(kundli)
    evidence.append(house_axis_inverted(r))
    score, _ = travel_strength_score(kundli)
    if score >= 68:
        verdict = "Return-to-India theme possible later — strong 4H anchor may pull back from long foreign stay"
    elif score >= 52:
        verdict = "Mixed foreign vs home pull — chart shows both abroad urge and homeland connection"
    else:
        verdict = "Return/home theme relatively easier — 4H anchor stronger than permanent foreign settlement"
    return EngineResult(
        archetype="return_india",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 70,
        answer_plan="Return answer → 4H anchor vs 12H foreign pull.",
        summary=["QUESTION FOCUS: wapas India / no settlement — balanced tone."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed return date"],
        checks={"slice_type": "travel_engine_v1", "archetype": "return_india"},
    )


def run_travel_obstacles(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = travel_snapshot(kundli)
    evidence.append(planet_line(r, "Saturn", "delay/block axis"))
    evidence.append(planet_line(r, "Rahu", "complexity/paperwork axis"))
    evidence.append("Obstacle axis: afflicted 9H/12H or Saturn on travel karakas — patience, not fear.")
    return EngineResult(
        archetype="travel_obstacles",
        verdict="Travel/settlement obstacles visible — chart shows delay/friction; paperwork + patience both needed",
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Obstacle answer → Saturn/Rahu on 9H/12H — practical tone.",
        summary=["QUESTION FOCUS: delay/block — NOT hopeless or alarmist."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed failure"],
        checks={"slice_type": "travel_engine_v1", "archetype": "travel_obstacles"},
    )


def run_short_travel(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed_result(
        archetype="short_travel",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Short foreign trip axis",
        verdict_strong="Short foreign trip theme supportive — 3H/9H + Mercury/Rahu favour travel breaks",
        verdict_mixed="Short trips possible — plan budget, visa type and dates carefully",
        verdict_weak="Short foreign travel needs planning — strengthen 3H courage and documents first",
        summary_lines=["QUESTION FOCUS: trip/vacation abroad — NOT permanent settlement."],
    )


def run_pilgrimage_travel(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = travel_snapshot(kundli)
    evidence.append(planet_line(r, "Jupiter", "dharma/teerth karaka"))
    evidence.append("Pilgrimage axis: 9H + Jupiter — sacred/long journey theme.")
    return EngineResult(
        archetype="pilgrimage_travel",
        verdict="Pilgrimage/dharma yatra theme visible — 9H + Jupiter support sacred long journey",
        confidence="medium",
        word_budget=85 if wants_explain else 70,
        answer_plan="Teerth answer → 9H + Jupiter + 12H distant journey.",
        summary=["QUESTION FOCUS: teerth/dharma yatra — NOT tourism luxury only."],
        evidence=evidence[:12],
        ignore=["timing", "exact tirth date"],
        checks={"slice_type": "travel_engine_v1", "archetype": "pilgrimage_travel"},
    )


def run_passport_travel(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed_result(
        archetype="passport_travel",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Passport/travel capacity",
        verdict_strong="Passport/travel capacity strong — 3H/9H courage + movement karakas supportive",
        verdict_mixed="Passport/travel capacity moderate — documents and timing discipline help",
        verdict_weak="Passport/travel capacity needs care — verify paperwork and avoid rushed applications",
        summary_lines=["QUESTION FOCUS: passport/travel capacity — NOT exact issue date."],
    )


def run_immigration(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = travel_snapshot(kundli)
    evidence.append(planet_line(r, "Saturn", "long immigration process karaka"))
    score, label = travel_strength_score(kundli)
    evidence.append(f"Immigration/PR axis: 12H + Saturn endurance + Rahu foreign link — {label}.")
    verdict = (
        "Immigration/PR theme "
        f"{'strong' if score >= 68 else 'moderate' if score >= 52 else 'needs long effort'} — "
        "12H settlement + Saturn patience; legal counsel essential"
    )
    return EngineResult(
        archetype="immigration",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan="Immigration answer → 12H + Saturn + Rahu; no legal advice.",
        summary=["QUESTION FOCUS: PR/green card/citizenship — NOT immigration lawyer advice."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed PR", "legal advice"],
        checks={"slice_type": "travel_engine_v1", "archetype": "immigration", "travel_score": score},
    )


def run_business_travel(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed_result(
        archetype="business_travel",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Business travel abroad",
        verdict_strong="Business travel abroad supported — Mercury + 3H/9H favour official foreign trips",
        verdict_mixed="Business trips abroad possible — contracts and visa type matter",
        verdict_weak="Business foreign travel needs planning — verify employer sponsorship and docs",
        summary_lines=["QUESTION FOCUS: official/business trip — NOT permanent job abroad."],
    )


def run_travel_risk(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = travel_snapshot(kundli)
    evidence.append(planet_line(r, "Mars", "accident/impulsive travel risk"))
    evidence.append(planet_line(r, "Rahu", "unusual/risky foreign exposure"))
    evidence.append("Risk axis: Mars/Rahu in 3/9/12 — caution tone, not panic.")
    return EngineResult(
        archetype="travel_risk",
        verdict="Foreign travel risk theme visible — Mars/Rahu on travel houses; caution + insurance mindset",
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Risk answer → Mars/Rahu on 3H/9H/12H — safety practical line.",
        summary=["QUESTION FOCUS: travel danger/accident — practical safety, not fear."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed accident"],
        checks={"slice_type": "travel_engine_v1", "archetype": "travel_risk"},
    )


def run_travel_country_fit(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = travel_snapshot(kundli)
    evidence.append(planet_line(r, "Rahu", "foreign-direction/unconventional lands"))
    evidence.append(
        "Country-fit note: use 9H/12H + Rahu/Jupiter D9 tone — "
        "qualitative region/direction only, not exact country name."
    )
    score, label = travel_strength_score(kundli)
    evidence.append(f"Country-direction review: {label}.")
    q = (question or "").lower()
    if re.search(r"(?ix)\b(usa|canada|uk|australia|germany|dubai|europe)\s+ya\b", q):
        verdict = (
            "Country choice from chart: compare 9H/12H + Rahu tone for both options — "
            "indicative lean only, not guaranteed destination"
        )
    else:
        verdict = (
            f"Foreign country direction theme {'clear' if score >= 68 else 'moderate' if score >= 52 else 'mixed'} — "
            "9H/12H + Rahu show travel direction tone, not fixed city/country"
        )
    return EngineResult(
        archetype="travel_country_fit",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan="Country-fit → 9H/12H + Rahu D9 qualitative direction; NO exact country guarantee.",
        summary=[
            "QUESTION FOCUS: kaun sa desh/country — qualitative direction only.",
            "Do NOT name one fixed country as guaranteed outcome.",
        ],
        evidence=evidence[:12],
        ignore=["timing", "exact country name", "guaranteed destination", "city name"],
        checks={"slice_type": "travel_engine_v1", "archetype": "travel_country_fit", "travel_score": score},
    )


def run_general_travel(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    score, label = travel_strength_score(kundli)
    evidence = travel_snapshot(kundli)
    evidence.append(f"Overall foreign/travel reading: {label}.")
    return EngineResult(
        archetype="general_travel",
        verdict=f"Overall foreign/travel theme: {label} — use 9H/12H + Rahu as main lens",
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="General travel → 9H/12H/3H snapshot + D9 if present.",
        summary=["QUESTION FOCUS: broad videsh/travel reading — stay non-timing."],
        evidence=evidence[:12],
        ignore=["timing", "exact country", "guaranteed visa"],
        checks={"slice_type": "travel_engine_v1", "archetype": "general_travel", "travel_score": score},
    )

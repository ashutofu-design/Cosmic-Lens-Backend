from __future__ import annotations

import re

from ..types import EngineResult
from ._litigation_base import (
    SAFETY_SUMMARY,
    litigation_snapshot,
    litigation_strength_score,
    planet_line,
    reader,
)


def _themed_result(
    *,
    archetype: str,
    kundli: dict,
    wants_explain: bool,
    focus_label: str,
    verdict_strong: str,
    verdict_mixed: str,
    verdict_weak: str,
    summary_lines: list[str] | None = None,
    ignore: list[str] | None = None,
) -> EngineResult:
    score, label = litigation_strength_score(kundli)
    evidence = litigation_snapshot(kundli)
    evidence.append(f"{focus_label}: litigation strength index {score}/100 — {label}.")
    if score >= 66:
        verdict, confidence = verdict_strong, "medium"
    elif score >= 50:
        verdict, confidence = verdict_mixed, "medium"
    else:
        verdict, confidence = verdict_weak, "medium"
    summary = list(SAFETY_SUMMARY)
    if summary_lines:
        summary.extend(summary_lines)
    return EngineResult(
        archetype=archetype,
        verdict=verdict,
        confidence=confidence,
        word_budget=95 if wants_explain else 80,
        answer_plan=f"Direct answer for {archetype.replace('_', ' ')} → 6H/8H/12H + Mars/Saturn/Rahu evidence.",
        summary=summary,
        evidence=evidence[:12],
        ignore=ignore or ["timing", "guaranteed win/loss", "confinement prediction", "death penalty", "legal advice"],
        checks={"slice_type": "litigation_engine_v1", "archetype": archetype, "litigation_score": score},
    )


def run_litigation_yog(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed_result(
        archetype="litigation_yog",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Court case / litigation yog",
        verdict_strong="Litigation/court-case theme visible — 6H/8H axis active; calm counsel essential",
        verdict_mixed="Mixed litigation theme — chart shows legal friction possible; facts and lawyer matter most",
        verdict_weak="Legal friction axis visible — chart shows caution themes; avoid panic, use qualified counsel",
        summary_lines=["QUESTION FOCUS: court case yog / mukadma theme — NOT when or guaranteed outcome."],
    )


def run_case_outcome(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = litigation_snapshot(kundli)
    score, label = litigation_strength_score(kundli)
    evidence.append(planet_line(r, "Mars", "fight/court battle tone"))
    evidence.append(planet_line(r, "Saturn", "judgment delay tone"))
    evidence.append(f"Outcome axis review: {label} — indicative only, never guaranteed win/loss.")
    q = (question or "").lower()
    if re.search(r"(?ix)\b(har|lose|loss|against|negative|unfavour|unfavor)\b", q):
        tone = "Legal friction visible on 6H/8H — chart shows challenge themes; strong counsel and patience needed"
    elif score >= 66:
        tone = "Legal-handling axis relatively supportive — 6H/Mars strength; still NO guaranteed win"
    elif score >= 50:
        tone = "Mixed legal outcome axis — chart balanced; documents, facts and counsel decide the real result"
    else:
        tone = "Legal friction axis stronger — Saturn/Rahu on 6H/8H; patience and structured defence essential"
    return EngineResult(
        archetype="case_outcome",
        verdict=tone,
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan="Outcome answer → 6H Mars + Saturn delay — indicative tone only.",
        summary=SAFETY_SUMMARY + ["QUESTION FOCUS: jeet/har tone — NEVER guarantee verdict."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed win", "guaranteed loss", "pakka jeet", "pakka haar"],
        checks={"slice_type": "litigation_engine_v1", "archetype": "case_outcome", "litigation_score": score},
    )


def run_court_delay(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = litigation_snapshot(kundli)
    evidence.append(planet_line(r, "Saturn", "delay/prolonged legal process karaka"))
    evidence.append(planet_line(r, "Rahu", "complexity/extension axis"))
    evidence.append("Delay axis: Saturn/Rahu on 6H/8H/12H — prolonged process theme, not hopeless tone.")
    return EngineResult(
        archetype="court_delay",
        verdict="Court case delay theme visible — Saturn on legal houses shows prolonged process; patience + counsel",
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Delay answer → Saturn/Rahu on 6H/8H — practical patience line.",
        summary=SAFETY_SUMMARY + ["QUESTION FOCUS: case delay/ruka — NOT exact duration."],
        evidence=evidence[:12],
        ignore=["timing", "exact months", "guaranteed quick verdict"],
        checks={"slice_type": "litigation_engine_v1", "archetype": "court_delay"},
    )


def run_bail_theme(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = litigation_snapshot(kundli)
    evidence.append(planet_line(r, "Mercury", "petition/arguments karaka"))
    evidence.append(planet_line(r, "Jupiter", "relief/protection karaka"))
    score, label = litigation_strength_score(kundli)
    evidence.append(f"Bail theme review: {label} — legal counsel essential, not guaranteed bail.")
    q = (question or "").lower()
    if re.search(r"(?ix)\b(deny|reject|nahi|refus)\b", q):
        verdict = "Bail theme shows friction — 8H/Saturn stress on legal axis; advocate strategy critical, not panic"
    elif score >= 66:
        verdict = "Bail theme relatively supportive — Jupiter/Mercury + 6H handling; still court decides, not chart alone"
    else:
        verdict = "Bail theme mixed — 6H/8H friction visible; strong legal petition and calm approach both needed"
    return EngineResult(
        archetype="bail_theme",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan="Bail answer → Mercury petition + Jupiter relief — no guarantee.",
        summary=SAFETY_SUMMARY + ["QUESTION FOCUS: bail/zamanat theme — NOT legal advice or exact date."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed bail", "legal advice"],
        checks={"slice_type": "litigation_engine_v1", "archetype": "bail_theme", "litigation_score": score},
    )


def run_jail_concern(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = litigation_snapshot(kundli)
    evidence.append(planet_line(r, "Saturn", "restriction/process karaka"))
    evidence.append(
        "12H confinement-stress axis review — chart shows legal caution themes only; "
        "NOT a jail prediction or confinement yog."
    )
    return EngineResult(
        archetype="jail_concern",
        verdict=(
            "12H/6H legal-stress axis visible — chart shows caution themes only; "
            "practical legal counsel essential — NOT jail prediction or confinement yog"
        ),
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Jail concern → 12H stress axis with calm non-fear tone ONLY.",
        summary=SAFETY_SUMMARY + [
            "QUESTION FOCUS: jail/custody fear — NEVER predict confinement or use alarmist tone.",
            "Use calm reassurance + lawyer counsel; chart shows stress axis only.",
        ],
        evidence=evidence[:12],
        ignore=["confinement prediction", "death penalty", "guaranteed jail", "pakka andar", "phansi", "timing"],
        checks={"slice_type": "litigation_engine_v1", "archetype": "jail_concern", "no_fear_tone": True},
    )


def run_police_fir(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = litigation_snapshot(kundli)
    evidence.append(planet_line(r, "Rahu", "FIR/police complexity karaka"))
    evidence.append(planet_line(r, "Mars", "conflict/police action axis"))
    evidence.append("Police/FIR axis: Rahu/Mars on 6H/8H — police matter theme, not terror tone.")
    return EngineResult(
        archetype="police_fir",
        verdict="Police/FIR theme visible — Rahu/Mars on 6H/8H show legal-police friction; calm facts + counsel essential",
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="FIR answer → Rahu/Mars 6H/8H — practical counsel line.",
        summary=SAFETY_SUMMARY + ["QUESTION FOCUS: FIR/thana/police case — NOT alarmist tone."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed FIR", "guaranteed arrest", "legal advice"],
        checks={"slice_type": "litigation_engine_v1", "archetype": "police_fir"},
    )


def run_criminal_case(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = litigation_snapshot(kundli)
    evidence.append(planet_line(r, "Mars", "criminal conflict karaka"))
    evidence.append(planet_line(r, "Saturn", "criminal trial delay karaka"))
    score, label = litigation_strength_score(kundli)
    evidence.append(f"Criminal case axis: {label}.")
    return EngineResult(
        archetype="criminal_case",
        verdict=(
            f"Criminal case theme visible — 6H/8H + Mars/Saturn axis active; "
            f"{label}; qualified criminal lawyer essential — no guaranteed outcome"
        ),
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan="Criminal case → 6H/8H Mars/Saturn — calm non-fear tone.",
        summary=SAFETY_SUMMARY + ["QUESTION FOCUS: criminal matter — NOT conviction prediction."],
        evidence=evidence[:12],
        ignore=["guaranteed conviction", "confinement prediction", "death penalty", "timing", "legal advice"],
        checks={"slice_type": "litigation_engine_v1", "archetype": "criminal_case", "litigation_score": score},
    )


def run_civil_litigation(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed_result(
        archetype="civil_litigation",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Civil litigation axis",
        verdict_strong="Civil case theme visible — Mercury/6H support documents and civil dispute handling",
        verdict_mixed="Civil litigation mixed — chart shows both argument strength and procedural delay",
        verdict_weak="Civil case friction visible — Saturn delay on 6H; patience and civil counsel essential",
        summary_lines=["QUESTION FOCUS: civil court/suit — NOT exact decree prediction."],
    )


def run_legal_obstacles(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = litigation_snapshot(kundli)
    evidence.append(planet_line(r, "Saturn", "obstacle/delay karaka"))
    evidence.append(planet_line(r, "Rahu", "complication/obstacle karaka"))
    evidence.append("Obstacle axis: afflicted 6H/8H — friction visible, not hopeless tone.")
    return EngineResult(
        archetype="legal_obstacles",
        verdict="Legal obstacles visible — Saturn/Rahu on 6H/8H show friction; structured counsel + calm strategy needed",
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Obstacles → Saturn/Rahu 6H/8H — practical tone.",
        summary=SAFETY_SUMMARY + ["QUESTION FOCUS: legal problems/rukawat — NOT panic tone."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed failure", "confinement prediction"],
        checks={"slice_type": "litigation_engine_v1", "archetype": "legal_obstacles"},
    )


def run_enemy_case(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = litigation_snapshot(kundli)
    evidence.append(planet_line(r, "Mars", "enemy/conflict karaka"))
    evidence.append("Enemy litigation axis: 6H shatru + Mars conflict — opponent case theme.")
    score, label = litigation_strength_score(kundli)
    evidence.append(f"Enemy case review: {label}.")
    return EngineResult(
        archetype="enemy_case",
        verdict=f"Enemy/opponent case theme visible — 6H shatru axis + Mars; {label}; counsel and evidence strategy key",
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Enemy case → 6H shatru + Mars — balanced tone.",
        summary=SAFETY_SUMMARY + ["QUESTION FOCUS: dushman/shatru case — NOT revenge or guaranteed win."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed win", "guaranteed loss"],
        checks={"slice_type": "litigation_engine_v1", "archetype": "enemy_case", "litigation_score": score},
    )


def run_acquittal_relief(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = litigation_snapshot(kundli)
    evidence.append(planet_line(r, "Jupiter", "relief/protection karaka"))
    score, label = litigation_strength_score(kundli)
    evidence.append(f"Relief/acquittal axis: {label} — hopeful but NOT guaranteed discharge.")
    return EngineResult(
        archetype="acquittal_relief",
        verdict=(
            "Relief/acquittal axis visible — Jupiter + legal-handling strength supportive; "
            "still court decides — no guaranteed bera gari or quash"
        ),
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Acquittal → Jupiter relief + 6H handling — no guarantee.",
        summary=SAFETY_SUMMARY + ["QUESTION FOCUS: acquittal/chhutkara — NOT guaranteed dismissal."],
        evidence=evidence[:12],
        ignore=["guaranteed acquittal", "timing", "legal advice"],
        checks={"slice_type": "litigation_engine_v1", "archetype": "acquittal_relief", "litigation_score": score},
    )


def run_lawyer_support(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = litigation_snapshot(kundli)
    evidence.append(planet_line(r, "Mercury", "advocate/arguments karaka"))
    evidence.append(planet_line(r, "Jupiter", "wise counsel/protection karaka"))
    return EngineResult(
        archetype="lawyer_support",
        verdict="Advocate/counsel support theme — Mercury/Jupiter favour strong legal representation; choose qualified lawyer",
        confidence="medium",
        word_budget=85 if wants_explain else 70,
        answer_plan="Lawyer answer → Mercury/Jupiter — NOT legal advice on which lawyer.",
        summary=SAFETY_SUMMARY + ["QUESTION FOCUS: vakil/advocate support — NOT specific lawyer recommendation."],
        evidence=evidence[:12],
        ignore=["legal advice", "specific lawyer name", "timing"],
        checks={"slice_type": "litigation_engine_v1", "archetype": "lawyer_support"},
    )


def run_family_court(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = litigation_snapshot(kundli)
    evidence.append(planet_line(r, "Venus", "matrimonial/domestic axis karaka"))
    evidence.append("Family court axis: 6H dispute + Venus domestic tone — calm practical counsel.")
    return EngineResult(
        archetype="family_court",
        verdict="Family court/matrimonial case theme — 6H dispute + Venus domestic axis; calm counsel, not fear tone",
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Family court → 6H + Venus — NOT divorce timing or MR spouse nature.",
        summary=SAFETY_SUMMARY + ["QUESTION FOCUS: family court/custody/maintenance case — NOT divorce spouse Q."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed custody", "guaranteed maintenance", "legal advice"],
        checks={"slice_type": "litigation_engine_v1", "archetype": "family_court"},
    )


def run_general_litigation(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed_result(
        archetype="general_litigation",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="General litigation review",
        verdict_strong="General legal/court theme visible — 6H/8H/12H axis active; calm qualified counsel essential",
        verdict_mixed="General litigation theme mixed — chart shows legal friction and handling capacity both",
        verdict_weak="General legal friction visible — Saturn/Rahu on legal houses; patience and counsel critical",
        summary_lines=["QUESTION FOCUS: general court/legal matter — balanced calm tone."],
    )


def run_litigation_remedy(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    from ..remedy import build_litigation_remedy_block

    r = reader(kundli)
    evidence = litigation_snapshot(kundli)
    score, label = litigation_strength_score(kundli)
    block = build_litigation_remedy_block(kundli, question, "litigation_remedy")
    evidence.append(f"Remedy axis review: {label} — 3-tier stack for top litigation grahas.")
    rendered = block.get("rendered") or ""
    if rendered:
        evidence.append("REMEDIES block generated — practical → ayurvedic → BPHS vedic (quote verbatim in reply).")
    checks = {
        "slice_type": "litigation_engine_v1",
        "archetype": "litigation_remedy",
        "litigation_score": score,
        "remedy_available": bool(rendered),
        "remedy_severity": block.get("severity"),
        "remedy_text": rendered,
    }
    return EngineResult(
        archetype="litigation_remedy",
        verdict=(
            "Litigation remedy stack ready — chart shows legal axis themes; "
            "practical lawyer + document steps FIRST, then calm body support, then BPHS vedic last"
        ),
        confidence="medium",
        word_budget=120 if wants_explain else 105,
        answer_plan="Remedy answer → 3-tier stack from remedy engine; quote verbatim; lawyer first.",
        summary=SAFETY_SUMMARY + [
            "QUESTION FOCUS: court case upay/remedy — practical legal action FIRST.",
            "Give practical tier first, ayurvedic second, vedic/BPHS last — never vedic-only.",
            "NEVER promise acquittal/bail/win from remedies alone.",
        ],
        evidence=evidence[:12],
        ignore=["guaranteed win", "guaranteed bail", "confinement prediction", "legal advice substitute"],
        checks=checks,
    )

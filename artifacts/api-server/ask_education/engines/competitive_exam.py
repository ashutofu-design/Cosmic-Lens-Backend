from __future__ import annotations

from ..types import EngineResult
from ._education_base import education_snapshot, learning_strength_score, planet_line, reader


def _exam_style_result(
    *,
    archetype: str,
    question: str,
    kundli: dict,
    wants_explain: bool,
    focus_label: str,
    verdict_strong: str,
    verdict_mixed: str,
    verdict_weak: str,
    summary_lines: list[str],
) -> EngineResult:
    score, label = learning_strength_score(kundli)
    r = reader(kundli)
    merc = r.planet("Mercury") or {}
    jup = r.planet("Jupiter") or {}
    evidence = education_snapshot(kundli)
    evidence.append(
        f"{focus_label}: Mercury H{merc.get('house')} + Jupiter H{jup.get('house')} "
        f"+ 5H intellect axis."
    )
    evidence.append(f"Learning strength index: {score}/100 — {label}.")
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
        word_budget=85 if wants_explain else 70,
        answer_plan=f"Direct answer for {archetype.replace('_', ' ')} → Mercury/Jupiter/5H evidence.",
        summary=summary_lines,
        evidence=evidence[:8],
        ignore=["timing", "exact marks", "exact rank", "muhurat"],
        checks={"slice_type": "education_engine_v1", "archetype": archetype, "learning_score": score},
    )


def run_competitive_exam(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _exam_style_result(
        archetype="competitive_exam",
        question=question,
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Competitive/entrance exam axis",
        verdict_strong="Competitive exam chart strong — NEET/JEE/board-style prep can convert with discipline",
        verdict_mixed="Competitive exam possible — chart mixed; mock tests + weak-topic drill decide rank band",
        verdict_weak="Competitive exam needs structured coaching — chart shows prep-gap; daily targets essential",
        summary_lines=[
            "QUESTION FOCUS: NEET/JEE/CAT/GATE/board/entrance exam — NOT govt job exam.",
            "Do NOT predict exact rank or cutoff.",
        ],
    )

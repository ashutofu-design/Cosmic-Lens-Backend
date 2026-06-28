from __future__ import annotations

from ..types import EngineResult
from ._education_base import education_snapshot, learning_strength_score


def run_general_education(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    score, label = learning_strength_score(kundli)
    evidence = education_snapshot(kundli)
    evidence.append(f"Overall learning index: {score}/100 — {label}.")

    if score >= 68:
        verdict = "Overall education chart strong — learning, exams and growth supported with steady effort"
    elif score >= 52:
        verdict = "Overall education chart mixed — success comes from consistent study rhythm and right guidance"
    else:
        verdict = "Overall education chart needs discipline layer — coaching, revision and small targets help most"

    return EngineResult(
        archetype="general_education",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Answer the exact education Q using 4H/5H/9H + Mercury/Jupiter snapshot.",
        summary=[
            "OPEN education Q — pick relevant houses/karakas only.",
            "No dasha dates, no exact result numbers.",
        ],
        evidence=evidence[:8],
        ignore=["timing", "exact marks", "muhurat"],
        checks={
            "slice_type": "education_engine_v1",
            "archetype": "general_education",
            "open_chart_qa": True,
            "learning_score": score,
        },
    )

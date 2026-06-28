from __future__ import annotations

from ..types import EngineResult
from ._education_base import education_snapshot, learning_strength_score, planet_line, reader


def run_exam_success(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    score, label = learning_strength_score(kundli)
    merc = r.planet("Mercury") or {}
    jup = r.planet("Jupiter") or {}

    evidence = education_snapshot(kundli)
    evidence.append(
        f"Exam axis: Mercury (intellect) H{merc.get('house')} + Jupiter (retention) H{jup.get('house')} "
        f"with 5H intellect link — core exam-support pattern."
    )
    evidence.append(f"Learning strength index: {score}/100 — {label}.")

    if score >= 68:
        verdict = "Exam success potential strong — chart supports clear/pass with disciplined prep"
        confidence = "high"
    elif score >= 52:
        verdict = "Exam success possible — chart mixed; revision, mock tests and focus decide outcome"
        confidence = "medium"
    else:
        verdict = "Exam needs structured coaching — chart shows effort-gap; small daily targets help most"
        confidence = "medium"

    return EngineResult(
        archetype="exam_success",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan="Direct pass/clear/selection answer → Mercury/Jupiter + 5H evidence → one study habit.",
        summary=[
            "QUESTION FOCUS: exam pass/clear/selection/result — NOT exam date.",
            "Do NOT predict exact marks or rank numbers.",
        ],
        evidence=evidence[:8],
        ignore=["timing", "exact marks", "exact rank", "muhurat"],
        checks={"slice_type": "education_engine_v1", "archetype": "exam_success", "learning_score": score},
    )

from __future__ import annotations

from ask_career.types import EngineResult
from ._career_base import career_snapshot, load_inclination


def run_general_career(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    evidence = career_snapshot(kundli, inc)

    return EngineResult(
        archetype="general_career",
        verdict="Open career question — answer from relevant D1/D10 career factors only",
        confidence="medium",
        word_budget=75 if wants_explain else 60,
        answer_plan="Answer exact question from relevant career chart factors → 1–2 reasons.",
        summary=[
            "OPEN career question — pick ONLY factors relevant to what was asked.",
            "Confident pattern voice — no shayad/ho sakta hai.",
            "No planet/house jargon in user reply.",
        ],
        evidence=evidence[:12],
        ignore=["timing dates", "marriage", "exact job title guarantee"],
        checks={
            "slice_type": "career_engine_v1",
            "archetype": "general_career",
            "open_chart_qa": True,
        },
    )

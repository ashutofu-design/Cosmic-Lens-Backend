from __future__ import annotations

import re

from ..types import EngineResult
from ._health_base import (
    affliction_lines,
    dim,
    dim_evidence,
    dusthana_chart_evidence,
    load_facts,
    vitality_line,
)

_ISSUE_NOW_Q = re.compile(
    r"(?ix)(kya\s+kya\s+(?:health\s+|sehat\s+|tabiyat\s+)?(?:issue|problem|dikkat|bimari|disease|rog)|"
    r"(?:health|sehat|tabiyat)\s+(?:issue|problem|dikkat)\s+ho\s+raha|"
    r"(?:issue|problem|dikkat|bimari|disease)\s+ho\s+rahi?)"
)


def run_general_health(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    ov = dim(facts, "overall_vitality")
    ms = dim(facts, "mental_stress")
    ch = dim(facts, "chronic_tendency")
    ov_v = ov.get("verdict", "")

    if ov_v == "GREEN" and ms.get("verdict") != "RED":
        verdict = "Overall health picture supportive — vitality + mind axis reasonable"
        confidence = "medium"
    elif ch.get("verdict") == "RED" or ov_v == "RED":
        verdict = "Overall health mixed-to-weak — chronic/vitality zones pe active care wise"
        confidence = "medium"
    else:
        verdict = "Overall health mixed — prevention + stress care se balance ban sakta hai"
        confidence = "medium"

    evidence = [
        vitality_line(facts),
        dim_evidence(facts, "overall_vitality", "Vitality"),
        dim_evidence(facts, "mental_stress", "Mental stress"),
        dim_evidence(facts, "chronic_tendency", "Chronic tendency"),
        dim_evidence(facts, "preventive_risk", "Preventive risk"),
        dim_evidence(facts, "recovery_capacity", "Recovery capacity"),
        dim_evidence(facts, "surgery_risk_tone", "Surgery caution tone"),
    ]
    evidence.extend(dusthana_chart_evidence(facts))
    evidence.extend(affliction_lines(facts, limit=3))

    issue_now = bool(_ISSUE_NOW_Q.search(question or ""))
    if issue_now:
        answer_plan = (
            "Answer the health troubles/tendencies the user asked about. "
            "Name vulnerability zones, not diagnosed diseases."
        )
        summary = ["No disease diagnosis.", "Answer exact question."]
        word_budget = 105 if wants_explain else 95
    else:
        answer_plan = "Open health Q — pick relevant dimensions from evidence."
        summary = ["6-dim snapshot.", "Doctor for symptoms."]
        word_budget = 100 if wants_explain else 85

    return EngineResult(
        archetype="general_health",
        verdict=verdict,
        confidence=confidence,
        word_budget=word_budget,
        answer_plan=answer_plan,
        summary=summary,
        evidence=evidence[:12],
        ignore=["timing", "disease names", "death", "dates"],
        checks={
            "slice_type": "health_engine_v1",
            "archetype": "general_health",
            "open_chart_qa": True,
            "issue_now_q": issue_now,
            "vitality_v": ov_v,
        },
    )

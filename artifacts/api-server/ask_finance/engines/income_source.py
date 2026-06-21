from __future__ import annotations

import re

from ..types import EngineResult
from ._finance_base import (
    affliction_lines,
    dim,
    dim_evidence,
    income_affinity_lines,
    load_facts,
    lord_evidence,
    sub_flag,
)


def run_income_source(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    d = dim(facts, "income_stability")
    verdict_plain = {"GREEN": "Stable income pattern", "YELLOW": "Mixed income pattern", "RED": "Unstable income pattern"}.get(
        d.get("verdict", ""), "Income pattern from chart"
    )

    evidence = [
        dim_evidence(facts, "income_stability", "Income stability"),
        lord_evidence(facts, "h2", "Wealth flow (2nd house)"),
        lord_evidence(facts, "h10", "Career-earning axis (10th house)"),
        lord_evidence(facts, "h11", "Gains/profit axis (11th house)"),
    ]
    evidence.extend(income_affinity_lines(facts))
    evidence.extend(affliction_lines(facts, limit=2))

    q_lower = (question or "").lower()
    if re.search(r"(?ix)\b(natural\s+tareek|natural\s+way|natural\s+style)\b", q_lower):
        evidence.insert(0, "Answer focus: natural earning style — pick strongest income affinity below")

    biz = sub_flag(facts, "business_friendly")
    if biz:
        evidence.append("Business/self-employed income channel suits better than pure fixed salary")
    else:
        evidence.append("Fixed salary / structured employment income channel suits better")

    return EngineResult(
        archetype="income_source",
        verdict=f"{verdict_plain} — multiple sources possible but one primary style dominates",
        confidence="medium" if d.get("verdict") == "YELLOW" else ("high" if d.get("verdict") == "GREEN" else "low"),
        word_budget=85 if wants_explain else 70,
        answer_plan="Answer income source/style directly → 2 reasons from stability + affinity.",
        summary=["Do NOT quote exact salary figures.", "Answer kaun sa source / stable ya unstable."],
        evidence=evidence[:8],
        ignore=["timing", "exact rupee amount", "stock tips", "lottery"],
        checks={"slice_type": "finance_engine_v1", "archetype": "income_source", "income_v": d.get("verdict")},
    )

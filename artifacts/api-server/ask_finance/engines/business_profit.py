from __future__ import annotations

from ..types import EngineResult
from ._finance_base import (
    dim,
    dim_evidence,
    load_facts,
    lord_evidence,
    sub_flag,
    yogas_line,
)


def run_business_profit(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    biz = sub_flag(facts, "business_friendly")
    wp = dim(facts, "wealth_potential")
    inc = dim(facts, "income_stability")
    q = (question or "").lower()
    partnership_q = "partnership" in q or "partner" in q

    if partnership_q:
        h7 = (facts.get("house_lords") or {}).get("h7") or {}
        if h7.get("lord_in_dusthana"):
            verdict = "Partnership business me risk — partner money disputes possible; clear agreement zaroori"
            confidence = "medium"
        elif biz and wp.get("verdict") != "RED":
            verdict = "Partnership business se profit ka pattern possible — saaf deal + role split se chalega"
            confidence = "medium"
        else:
            verdict = "Partnership thoda sensitive — solo ya trusted family partner better"
            confidence = "low"
    elif biz and wp.get("verdict") in ("GREEN", "YELLOW"):
        verdict = "Business profit ka chart support hai — execution + discipline se paisa aayega"
        confidence = "high" if wp.get("verdict") == "GREEN" else "medium"
    elif inc.get("verdict") == "GREEN" and not biz:
        verdict = "Stable income strong hai par business profit ke liye extra risk appetite chahiye"
        confidence = "medium"
    else:
        verdict = "Business profit mixed — pehle model test karo, bada scale baad me"
        confidence = "low"

    evidence = [
        lord_evidence(facts, "h7", "Business/partnership (7th)"),
        lord_evidence(facts, "h10", "Profession execution (10th)"),
        lord_evidence(facts, "h11", "Profit/gains (11th)"),
        dim_evidence(facts, "wealth_potential", "Wealth from venture"),
        dim_evidence(facts, "income_stability", "Income baseline"),
        yogas_line(facts),
    ]
    if biz:
        evidence.append("Business-friendly flag — self-employment/profit venture suits chart")
    else:
        evidence.append("Business-friendly flag weak — salaried/stable channel primary")

    return EngineResult(
        archetype="business_profit",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan="Business/partnership profit suitability — no exact profit figure.",
        summary=["No guaranteed profit amount.", "Partnership Q → 7th house theme."],
        evidence=evidence[:8],
        ignore=["timing", "exact profit", "stock trading business"],
        checks={"slice_type": "finance_engine_v1", "archetype": "business_profit", "business_friendly": bool(biz)},
    )

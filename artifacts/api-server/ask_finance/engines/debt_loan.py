from __future__ import annotations

from ..types import EngineResult
from ._finance_base import (
    affliction_lines,
    dim,
    dim_evidence,
    load_facts,
    lord_evidence,
    sub_flag,
)


def run_debt_loan(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    debt_high = sub_flag(facts, "debt_burden_high")
    rl = dim(facts, "risk_leak")
    is_stable = dim(facts, "income_stability")

    if debt_high and rl.get("verdict") == "RED":
        verdict = "Loan lena risky — debt burden + leak dono active; pehle existing karz control karo"
        confidence = "high"
    elif debt_high and is_stable.get("verdict") == "GREEN":
        verdict = "Loan service kar sakte ho par debt load rahega — planned EMI only, over-borrow mat karo"
        confidence = "medium"
    elif debt_high:
        verdict = "Loan capacity limited — chhota planned loan OK, bada karz avoid"
        confidence = "medium"
    else:
        verdict = "Loan manageable pattern — discipline ke saath planned borrowing OK"
        confidence = "medium"

    evidence = [
        lord_evidence(facts, "h6", "Debt/service house (6th)"),
        lord_evidence(facts, "h8", "Shared/other's money house (8th)"),
        dim_evidence(facts, "income_stability", "Income to service EMI"),
        dim_evidence(facts, "risk_leak", "Leak makes EMI harder"),
    ]
    if debt_high:
        evidence.append("Debt-burden signal active — 6th lord linked to money houses")
    else:
        evidence.append("Debt-burden signal low — chart does not push heavy borrowing")
    evidence.extend(affliction_lines(facts, limit=2))

    return EngineResult(
        archetype="debt_loan",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan="Loan/karz suitability + repayment capacity — no exact EMI amount.",
        summary=["No guaranteed loan approval.", "Focus debt capacity not timing."],
        evidence=evidence[:8],
        ignore=["timing", "exact EMI", "specific bank/product"],
        checks={
            "slice_type": "finance_engine_v1",
            "archetype": "debt_loan",
            "debt_burden_high": bool(debt_high),
        },
    )

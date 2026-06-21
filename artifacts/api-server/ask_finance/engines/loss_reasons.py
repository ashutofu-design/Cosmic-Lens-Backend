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


def run_loss_reasons(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    rl = dim(facts, "risk_leak")
    sa = dim(facts, "saving_ability")
    wp = dim(facts, "wealth_potential")
    rl_v = rl.get("verdict", "")

    if rl_v == "RED":
        verdict = "Paisa isliye nahi tikta — leak/drain pattern strong (kharcha, debt, ya loss channel active)"
        confidence = "high"
    elif sa.get("verdict") == "RED":
        verdict = "Kamai ho sakti hai par bachat discipline weak — paisa kama ke bhi jama nahi hota"
        confidence = "medium"
    elif wp.get("verdict") == "RED" and rl_v == "YELLOW":
        verdict = "Mega-wealth yog limited + moderate leak — comfort possible par bada dhan slow build hoga"
        confidence = "medium"
    else:
        verdict = "Mixed money picture — income OK par leak control pe focus karo tab paisa badhega"
        confidence = "medium"

    evidence = [
        dim_evidence(facts, "risk_leak", "Primary leak reason"),
        dim_evidence(facts, "saving_ability", "Saving block"),
        dim_evidence(facts, "income_stability", "Income side"),
        dim_evidence(facts, "wealth_potential", "Long-term wealth ceiling"),
        lord_evidence(facts, "h12", "Expense outflow"),
        lord_evidence(facts, "h2", "Wealth retention"),
    ]
    evidence.extend(affliction_lines(facts, limit=4))
    if sub_flag(facts, "leak_active"):
        evidence.append("Leak-active flag — lifestyle, EMI, or hidden expenses check karo pehle")

    return EngineResult(
        archetype="loss_reasons",
        verdict=verdict,
        confidence=confidence,
        word_budget=90 if wants_explain else 75,
        answer_plan="Kyun paisa nahi / problem kya — top 2 chart reasons.",
        summary=["Explain root pattern not blame.", "Actionable: leak control first."],
        evidence=evidence[:8],
        ignore=["timing", "exact loss amount", "stock blame"],
        checks={"slice_type": "finance_engine_v1", "archetype": "loss_reasons", "leak_v": rl_v},
    )

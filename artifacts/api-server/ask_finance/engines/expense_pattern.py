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


def run_expense_pattern(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    rl = dim(facts, "risk_leak")
    sa = dim(facts, "saving_ability")
    v = rl.get("verdict", "")
    verdict_map = {
        "GREEN": "Kharcha control me reh sakta hai — zyada leak nahi",
        "YELLOW": "Kharcha moderate — impulsive spend kabhi-kabhi",
        "RED": "Kharcha zyada / leak strong — paisa jaldi ud jata hai",
    }
    verdict = verdict_map.get(v, "Expense pattern from chart leak signals")

    evidence = [
        dim_evidence(facts, "risk_leak", "Expense/leak signal"),
        dim_evidence(facts, "saving_ability", "Opposite: saving retention"),
        lord_evidence(facts, "h12", "Expense house (12th)"),
        lord_evidence(facts, "h2", "Wealth retention (2nd)"),
    ]
    if sub_flag(facts, "leak_active"):
        evidence.append("Active drain pattern — lifestyle creep, loans, or hidden expenses check karo")
    if sa.get("verdict") == "RED":
        evidence.append("Saving weak + leak strong combo — budget cap aur auto-debit bachat zaroori")
    evidence.extend(affliction_lines(facts, limit=3))

    return EngineResult(
        archetype="expense_pattern",
        verdict=verdict,
        confidence="high" if v == "RED" else "medium",
        word_budget=80 if wants_explain else 65,
        answer_plan="Kharcha kyun zyada / paisa kyun nahi tikta — leak reason.",
        summary=["Explain spending pattern, not investment advice."],
        evidence=evidence[:8],
        ignore=["timing", "exact budget numbers", "stock/crypto"],
        checks={"slice_type": "finance_engine_v1", "archetype": "expense_pattern", "leak_v": v},
    )

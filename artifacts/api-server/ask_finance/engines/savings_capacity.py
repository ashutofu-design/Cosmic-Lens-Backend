from __future__ import annotations

from ..types import EngineResult
from ._finance_base import (
    affliction_lines,
    composite_verdict,
    dim,
    dim_evidence,
    load_facts,
    lord_evidence,
    sub_flag,
)


def run_savings_capacity(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    d = dim(facts, "saving_ability")
    rl = dim(facts, "risk_leak")
    v = d.get("verdict", "")
    verdict_map = {
        "GREEN": "Strong saving capacity — paisa tik sakta hai discipline ke saath",
        "YELLOW": "Moderate saving — kabhi-kabhi bachta hai, discipline chahiye",
        "RED": "Weak saving habit — paisa jaldi nikal jata hai",
    }
    verdict = verdict_map.get(v, composite_verdict(facts, focus="saving capacity"))

    evidence = [
        dim_evidence(facts, "saving_ability", "Saving ability"),
        dim_evidence(facts, "risk_leak", "Leak/drain risk"),
        lord_evidence(facts, "h2", "Savings house (2nd)"),
        lord_evidence(facts, "h12", "Expense/outflow house (12th)"),
    ]
    if sub_flag(facts, "saving_strong"):
        evidence.append("Chart supports retention — automatic SIP/RD style discipline kaam karega")
    if sub_flag(facts, "leak_active"):
        evidence.append("Leak active — pehle unnecessary kharcha band karo, tab bachat badhegi")
    evidence.extend(affliction_lines(facts, limit=2))

    return EngineResult(
        archetype="savings_capacity",
        verdict=verdict,
        confidence="high" if v == "GREEN" else ("low" if v == "RED" else "medium"),
        word_budget=80 if wants_explain else 65,
        answer_plan="Direct bachat hoti ya nahi → saving vs leak reason.",
        summary=["Do NOT promise exact savings amount.", "Focus: capacity to retain money."],
        evidence=evidence[:8],
        ignore=["timing", "exact amount", "investment product names"],
        checks={
            "slice_type": "finance_engine_v1",
            "archetype": "savings_capacity",
            "saving_v": v,
            "leak_v": rl.get("verdict"),
        },
    )

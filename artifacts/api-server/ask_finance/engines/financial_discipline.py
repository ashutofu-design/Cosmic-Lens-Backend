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


def run_financial_discipline(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    sa = dim(facts, "saving_ability")
    rl = dim(facts, "risk_leak")
    sa_v = sa.get("verdict", "")
    rl_v = rl.get("verdict", "")

    if sa_v == "GREEN" and rl_v != "RED":
        verdict = "Financial discipline strong — budget, SIP/RD aur planned kharch chart se suit karta hai"
        confidence = "high"
    elif sa_v == "YELLOW" and rl_v != "RED":
        verdict = "Discipline moderate — system (auto-debit, budget cap) se improve hoga, willpower pe mat chodo"
        confidence = "medium"
    else:
        verdict = "Discipline weak abhi — pehle leak band karo, phir fixed saving rule lagao"
        confidence = "medium"

    sat = (facts.get("karakas") or {}).get("Saturn") or {}
    evidence = [
        dim_evidence(facts, "saving_ability", "Saving discipline axis"),
        dim_evidence(facts, "risk_leak", "Self-control vs impulsive spend"),
        lord_evidence(facts, "h2", "Wealth habit house (2nd)"),
        f"Saturn (structure/discipline karaka) dignity: {sat.get('dignity', '?')}, house H{sat.get('house', '?')}",
    ]
    if sub_flag(facts, "saving_strong"):
        evidence.append("Chart supports structured money habits — routine se discipline badhegi")
    if sub_flag(facts, "leak_active"):
        evidence.append("Leak active — discipline pehle kharch cap se start karo")
    evidence.extend(affliction_lines(facts, limit=2))

    return EngineResult(
        archetype="financial_discipline",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan="Discipline strong/weak/mixed → saving + Saturn reason.",
        summary=["Focus money habits, not career discipline."],
        evidence=evidence[:8],
        ignore=["timing", "exact budget", "investment product names"],
        checks={
            "slice_type": "finance_engine_v1",
            "archetype": "financial_discipline",
            "saving_v": sa_v,
            "leak_v": rl_v,
        },
    )

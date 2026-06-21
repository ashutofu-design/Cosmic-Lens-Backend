from __future__ import annotations

from ..types import EngineResult
from ._finance_base import (
    affliction_lines,
    dim,
    dim_evidence,
    income_affinity_lines,
    load_facts,
    yogas_line,
)


def run_general_finance(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    dims = facts.get("dimensions") or {}
    wp = dims.get("wealth_potential", {}).get("verdict", "")
    inc = dims.get("income_stability", {}).get("verdict", "")
    sa = dims.get("saving_ability", {}).get("verdict", "")
    rl = dims.get("risk_leak", {}).get("verdict", "")

    if wp == "GREEN" and sa == "GREEN" and rl != "RED":
        verdict = "Overall finance picture strong — earn + save dono capacity, leak control rakho"
    elif rl == "RED":
        verdict = "Overall: pehle leak/kharcha control — tab baaki dimensions improve honge"
    elif sa == "RED":
        verdict = "Overall: income ho sakti hai par bachat weak — automatic saving setup zaroori"
    else:
        verdict = "Overall mixed finance picture — saving discipline + leak control pe focus"

    evidence = [
        dim_evidence(facts, "wealth_potential", "Wealth potential"),
        dim_evidence(facts, "income_stability", "Income stability"),
        dim_evidence(facts, "saving_ability", "Saving ability"),
        dim_evidence(facts, "risk_leak", "Risk/leak"),
        yogas_line(facts),
    ]
    evidence.extend(income_affinity_lines(facts))
    evidence.extend(affliction_lines(facts, limit=2))

    return EngineResult(
        archetype="general_finance",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan="4-dimension finance overview — answer user's exact money Q from relevant dims.",
        summary=[
            "OPEN finance Q — pick relevant dimensions only.",
            "4-dim snapshot available in evidence.",
        ],
        evidence=evidence[:10],
        ignore=["timing", "stock tips", "exact amounts"],
        checks={
            "slice_type": "finance_engine_v1",
            "archetype": "general_finance",
            "open_chart_qa": True,
            "wealth_v": wp,
            "income_v": inc,
            "saving_v": sa,
            "leak_v": rl,
        },
    )

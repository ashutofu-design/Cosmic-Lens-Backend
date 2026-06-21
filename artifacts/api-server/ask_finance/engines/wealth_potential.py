from __future__ import annotations

from ..types import EngineResult
from ._finance_base import (
    affliction_lines,
    dim,
    dim_evidence,
    load_facts,
    sub_flag,
    yogas_line,
)


def run_wealth_potential(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    wp = dim(facts, "wealth_potential")
    sa = dim(facts, "saving_ability")
    rl = dim(facts, "risk_leak")
    v = wp.get("verdict", "")

    if v == "GREEN" and sa.get("verdict") != "RED" and rl.get("verdict") != "RED":
        verdict = "Amir/wealthy banne ki capacity strong — discipline se crorepati path realistic (slow build)"
        confidence = "high"
    elif v == "GREEN" and rl.get("verdict") == "RED":
        verdict = "Kamane ki capacity strong par leak active — pehle drain band, tab wealth banegi"
        confidence = "medium"
    elif v == "YELLOW":
        verdict = "Comfortable wealth possible — mega-rich shortcut nahi, steady build se amiri realistic"
        confidence = "medium"
    else:
        verdict = "Mega-wealth yog limited — earned income + saving discipline se stability, lottery shortcut nahi"
        confidence = "medium"

    evidence = [
        dim_evidence(facts, "wealth_potential", "Wealth potential"),
        dim_evidence(facts, "saving_ability", "Retention for riches"),
        dim_evidence(facts, "risk_leak", "Leak blocks riches"),
        yogas_line(facts),
    ]
    if sub_flag(facts, "wealth_strong"):
        evidence.append("Wealth-strong sub-flag — dhan-yog + money houses support long arc")
    evidence.extend(affliction_lines(facts, limit=2))

    return EngineResult(
        archetype="wealth_potential",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan="Amir/rich potential direct answer — no crorepati guarantee date.",
        summary=["No lottery shortcut.", "Wealth = capacity + discipline."],
        evidence=evidence[:8],
        ignore=["timing", "exact net worth", "guaranteed crorepati"],
        checks={"slice_type": "finance_engine_v1", "archetype": "wealth_potential", "wealth_v": v},
    )

from __future__ import annotations

from ..types import EngineResult
from ._finance_base import (
    affliction_lines,
    dim,
    dim_evidence,
    load_facts,
    sub_flag,
)


def run_save_vs_spend(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    sa = dim(facts, "saving_ability")
    rl = dim(facts, "risk_leak")
    sa_v = sa.get("verdict", "")
    rl_v = rl.get("verdict", "")

    if sa_v == "GREEN" and rl_v != "RED":
        verdict = "Zyada saver type — paisa bachane ka pattern strong, kharch control me rehta hai"
        lean = "saver"
    elif rl_v == "RED" or sa_v == "RED":
        verdict = "Zyada spender type — kharch/leak zyada, bachat ke liye discipline chahiye"
        lean = "spender"
    else:
        verdict = "Mixed — kabhi bachate ho kabhi kharch ho jata hai; budget se balance banega"
        lean = "mixed"

    evidence = [
        dim_evidence(facts, "saving_ability", "Saver side (2nd/saving)"),
        dim_evidence(facts, "risk_leak", "Spender/leak side (12th/expense)"),
    ]
    if sub_flag(facts, "saving_strong"):
        evidence.append("Saving-strong flag — automatic bachat habit chart se support hoti hai")
    if sub_flag(facts, "leak_active"):
        evidence.append("Leak-active flag — impulsive ya lifestyle kharch zyada dikhta hai")
    evidence.extend(affliction_lines(facts, limit=2))

    return EngineResult(
        archetype="save_vs_spend",
        verdict=verdict,
        confidence="high" if lean != "mixed" else "medium",
        word_budget=85 if wants_explain else 70,
        answer_plan="Direct saver vs spender answer → saving vs leak evidence.",
        summary=[f"LEAN: {lean} — answer bachane wala ya kharch wala clearly."],
        evidence=evidence[:8],
        ignore=["timing", "exact amount", "stock tips"],
        checks={"slice_type": "finance_engine_v1", "archetype": "save_vs_spend", "lean": lean},
    )

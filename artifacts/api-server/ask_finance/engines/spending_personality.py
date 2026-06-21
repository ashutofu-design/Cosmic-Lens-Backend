from __future__ import annotations

import re

from ..types import EngineResult
from ._finance_base import (
    affliction_lines,
    dim,
    dim_evidence,
    load_facts,
    lord_evidence,
    sub_flag,
)

_LUXURY_Q_RX = re.compile(r"(?ix)\b(luxury|brand|status|show[\s-]?off)\b")
_EMOTIONAL_Q_RX = re.compile(r"(?ix)\b(emotional|mood|impulsive)\b")


def run_spending_personality(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    rl = dim(facts, "risk_leak")
    rl_v = rl.get("verdict", "")
    q = question or ""
    luxury_q = bool(_LUXURY_Q_RX.search(q))
    emotional_q = bool(_EMOTIONAL_Q_RX.search(q))

    venus = (facts.get("karakas") or {}).get("Venus") or {}
    moon = (facts.get("karakas") or {}).get("Moon") or {}

    if luxury_q:
        if venus.get("dignity") in ("exalted", "own", "friend") and rl_v != "RED":
            verdict = "Luxury-oriented pattern hai — comfort/brand spend natural, par budget cap rakho"
            focus = "luxury"
        elif rl_v == "RED":
            verdict = "Luxury taste hai par leak bhi — status spend control karo warna bachat nahi hogi"
            focus = "luxury_leak"
        else:
            verdict = "Thoda luxury comfort pasand hai — planned treats OK, impulsive shopping avoid"
            focus = "luxury_moderate"
    elif emotional_q or rl_v == "RED":
        verdict = "Emotional/impulsive spending ka signal hai — mood pe kharch zyada ho sakta hai"
        focus = "emotional"
    else:
        verdict = "Spending personality mixed — kabhi comfort spend, discipline se balance karo"
        focus = "mixed"

    evidence = [
        dim_evidence(facts, "risk_leak", "Impulsive/lifestyle spend signal"),
        lord_evidence(facts, "h12", "Expense/outflow house (12th)"),
        f"Venus (comfort/luxury) house H{venus.get('house', '?')}, dignity {venus.get('dignity', '?')}",
        f"Moon (mood/emotion spend) house H{moon.get('house', '?')}, dignity {moon.get('dignity', '?')}",
    ]
    if sub_flag(facts, "leak_active"):
        evidence.append("Leak-active — emotional ya luxury spend pe alert rehna hoga")
    evidence.extend(affliction_lines(facts, limit=2))

    return EngineResult(
        archetype="spending_personality",
        verdict=verdict,
        confidence="medium" if focus == "mixed" else "high",
        word_budget=85 if wants_explain else 70,
        answer_plan="Answer emotional OR luxury spending directly from Venus/Moon/leak.",
        summary=[f"FOCUS: {focus}", "No shame — pattern + control tip."],
        evidence=evidence[:8],
        ignore=["timing", "exact spend amount", "brand names"],
        checks={"slice_type": "finance_engine_v1", "archetype": "spending_personality", "focus": focus},
    )

from __future__ import annotations

import re

from ..types import EngineResult
from ._finance_base import (
    dim,
    dim_evidence,
    load_facts,
    lord_evidence,
    sub_flag,
)

_AGGRESSIVE_Q_RX = re.compile(r"(?ix)\b(risk[\s-]?tak|aggressive|high[\s-]?risk)\b")


def run_investment_risk(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    rl = dim(facts, "risk_leak")
    wp = dim(facts, "wealth_potential")
    rl_v = rl.get("verdict", "")
    q = question or ""
    wants_aggressive = bool(_AGGRESSIVE_Q_RX.search(q))

    rahu_h = (facts.get("karakas") or {}).get("Rahu", {}).get("house")
    mars_dig = (facts.get("karakas") or {}).get("Mars", {}).get("dignity", "?")

    if rl_v == "RED":
        verdict = "Conservative investor type — high-risk/speculative invest avoid; FD/debt/SIP style safe"
        style = "conservative"
    elif wp.get("verdict") == "GREEN" and rl_v != "RED" and (wants_aggressive or rahu_h in (3, 6, 11)):
        verdict = "Moderate risk le sakte ho — diversified equity/SIP OK, par satta/F&O avoid"
        style = "moderate_risk"
    elif wants_aggressive and rl_v == "YELLOW":
        verdict = "Thoda risk le sakte ho par controlled — small equity mix, emergency fund pehle"
        style = "moderate_risk"
    else:
        verdict = "Conservative side zyada suit — steady SIP + safe assets primary, speculation second"
        style = "conservative"

    evidence = [
        dim_evidence(facts, "risk_leak", "Risk/leak tolerance"),
        dim_evidence(facts, "wealth_potential", "Wealth-building capacity"),
        lord_evidence(facts, "h5", "Speculation/gain appetite (5th)"),
        lord_evidence(facts, "h11", "Gains from investments (11th)"),
        f"Rahu house H{rahu_h} — speculative/upachaya theme",
        f"Mars (risk drive) dignity: {mars_dig}",
    ]
    if sub_flag(facts, "leak_active"):
        evidence.append("Leak active — aggressive investing se pehle expense control zaroori")

    return EngineResult(
        archetype="investment_risk",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 70,
        answer_plan="Risk-taker vs conservative direct answer — no stock tips.",
        summary=[f"INVESTOR STYLE: {style}", "No specific stock/crypto picks."],
        evidence=evidence[:8],
        ignore=["timing", "stock tips", "crypto picks", "guaranteed returns"],
        checks={"slice_type": "finance_engine_v1", "archetype": "investment_risk", "style": style},
    )

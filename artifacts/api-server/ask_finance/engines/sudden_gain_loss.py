from __future__ import annotations

import re

from ..types import EngineResult
from ._finance_base import (
    affliction_lines,
    dim_evidence,
    load_facts,
    lord_evidence,
    sub_flag,
    yogas_line,
)

_LOSS_Q_RX = re.compile(r"(?ix)\b(loss|nuksan|kharab|gaya|lost|sudden\s*loss)\b")


def run_sudden_gain_loss(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    sudden_yog = sub_flag(facts, "sudden_wealth_yog")
    yogas = facts.get("wealth_yogas") or []
    q = question or ""
    loss_focus = bool(_LOSS_Q_RX.search(q))

    if loss_focus:
        rl_v = (facts.get("dimensions") or {}).get("risk_leak", {}).get("verdict", "")
        if rl_v == "RED":
            verdict = "Sudden loss ka risk zyada — unexpected expense/loss se bachne ke liye emergency fund rakho"
            confidence = "high"
        else:
            verdict = "Sudden big loss ka chart signal moderate — still avoid risky speculation"
            confidence = "medium"
    elif sudden_yog:
        verdict = (
            "Sudden gain ka indication hai — inheritance, settlement, bonus type; "
            "lottery/satta pe mat lagao"
        )
        confidence = "medium"
    else:
        verdict = "Sudden windfall ka chart support kam — earned income + discipline pe focus karo"
        confidence = "medium"

    evidence = [
        yogas_line(facts),
        lord_evidence(facts, "h8", "Sudden events / other's money (8th)"),
        lord_evidence(facts, "h11", "Windfall gains (11th)"),
        dim_evidence(facts, "risk_leak", "Sudden loss / drain risk"),
    ]
    if sudden_yog:
        evidence.append("Sudden-wealth yog flag active — unexpected inflow possible via legal/inheritance channel")
    if "Vipreet-Raja" in yogas:
        evidence.append("Vipreet-Rajyoga — setback ke baad recovery type sudden turnaround")
    rahu_h = (facts.get("karakas") or {}).get("Rahu", {}).get("house")
    if rahu_h in (3, 6, 11):
        evidence.append(f"Rahu in upachaya H{rahu_h} — speculative gain-house position (still not lottery advice)")
    evidence.extend(affliction_lines(facts, limit=2))

    focus = "sudden loss" if loss_focus else "sudden gain"
    return EngineResult(
        archetype="sudden_gain_loss",
        verdict=verdict,
        confidence=confidence,
        word_budget=85 if wants_explain else 70,
        answer_plan=f"Answer {focus} pattern directly — no lottery encouragement.",
        summary=["Never push lottery/satta.", "Distinguish windfall vs earned wealth."],
        evidence=evidence[:8],
        ignore=["timing", "lottery numbers", "guaranteed windfall"],
        checks={
            "slice_type": "finance_engine_v1",
            "archetype": "sudden_gain_loss",
            "sudden_wealth_yog": bool(sudden_yog),
            "focus": focus,
        },
    )

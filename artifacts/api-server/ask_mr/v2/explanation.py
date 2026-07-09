"""Explanation layer — why / why not / strongest / weakest."""
from __future__ import annotations

from .rules.types import FiredRule
from .schema import ExplanationLayer, FactorRef


def build_explanation(
    fired: list[FiredRule],
    *,
    score: int,
) -> ExplanationLayer:
    pos = [f for f in fired if f.polarity == "positive"]
    neg = [f for f in fired if f.polarity == "negative"]

    why = [f.evidence or f.label for f in pos[:3]]
    why_not = [f.evidence or f.label for f in neg[:3]]

    strongest = weakest = None
    if pos:
        best = max(pos, key=lambda f: f.weight)
        strongest = FactorRef(
            module=best.module,
            rule_id=best.rule_id,
            label=best.label,
            weight=best.weight,
            polarity="positive",
        )
    if neg:
        worst = max(neg, key=lambda f: f.weight)
        weakest = FactorRef(
            module=worst.module,
            rule_id=worst.rule_id,
            label=worst.label,
            weight=worst.weight,
            polarity="negative",
        )

    if score >= 72 and not why:
        why.append("Overall chart factors lean supportive")
    if score <= 45 and not why_not:
        why_not.append("Affliction pattern weighs heavier than support")

    return ExplanationLayer(
        why=why,
        why_not=why_not,
        strongest_factor=strongest,
        weakest_factor=weakest,
    )

"""D9 Navamsa module — marriage-promise sub-score."""
from __future__ import annotations

from typing import Any

from .types import ChartModuleResult


def load_d9(kundli: dict, *, engine_id: str) -> ChartModuleResult:
    from ask_mr.engines._person_signals import build_person_signals, pick_notes

    sig = build_person_signals(kundli)
    weak = pick_notes(
        sig,
        ["Navamsa Venus weak", "Navamsa Moon debilitated", "7th lord debilitated"],
        limit=3,
    )
    strong = pick_notes(sig, ["5th lord strong", "Saturn as 7th lord in 7th"], limit=2)

    score = 62
    if strong:
        score += 12 * len(strong)
    if weak:
        score -= 14 * len(weak)
    score = max(0, min(100, score))

    if score >= 72:
        polarity = "positive"
    elif score <= 45:
        polarity = "negative"
    else:
        polarity = "mixed"

    factors: list[dict[str, Any]] = []
    for n in strong:
        factors.append({"id": "D9-SUP", "label": n, "polarity": "positive", "weight": 2})
    for n in weak:
        factors.append({"id": "D9-AFF", "label": n, "polarity": "negative", "weight": 2})

    return ChartModuleResult(
        module_id="d9",
        polarity=polarity,
        score=score,
        factors=factors,
        notes=[f"D9: {n}" for n in weak + strong],
    )

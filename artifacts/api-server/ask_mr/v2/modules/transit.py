"""Transit module — 7th/8th axis stress (best-effort)."""
from __future__ import annotations

from .types import ChartModuleResult


def load_transit(kundli: dict, *, engine_id: str) -> ChartModuleResult:
    tr = (kundli or {}).get("transit") or (kundli or {}).get("transits") or {}
    if not tr:
        return ChartModuleResult(
            module_id="transit",
            loaded=False,
            polarity="neutral",
            score=50,
            notes=["Transit snapshot not on chart payload"],
        )

    stress = 0
    notes: list[str] = []
    for key in ("saturn_on_7th", "rahu_on_7th", "mars_on_7th", "stress_7th"):
        if tr.get(key):
            stress += 1
            notes.append(f"Transit stress: {key}")

    score = max(20, 70 - stress * 18)
    pol = "negative" if stress >= 2 else ("mixed" if stress == 1 else "positive")
    return ChartModuleResult(
        module_id="transit",
        polarity=pol,
        score=score,
        factors=[{"id": "TR-ST", "label": n, "polarity": "negative", "weight": 1} for n in notes],
        notes=notes or ["Transit: no major 7th stress flagged"],
    )

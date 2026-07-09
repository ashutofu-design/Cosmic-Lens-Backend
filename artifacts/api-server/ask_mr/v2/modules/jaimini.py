"""Jaimini module — stub for chara karaka hints."""
from __future__ import annotations

from .types import ChartModuleResult


def load_jaimini(kundli: dict, *, engine_id: str) -> ChartModuleResult:
    j = (kundli or {}).get("jaimini") or {}
    if not j:
        return ChartModuleResult(
            module_id="jaimini",
            loaded=False,
            polarity="neutral",
            score=50,
            notes=["Jaimini snapshot not on chart"],
        )
    ak = str(j.get("atmakaraka") or j.get("ak") or "")
    dk = str(j.get("darakaraka") or j.get("dk") or "")
    return ChartModuleResult(
        module_id="jaimini",
        polarity="neutral",
        score=55,
        factors=[{"id": "JM-AK", "label": f"AK={ak or '?'} DK={dk or '?'}", "polarity": "neutral", "weight": 1}],
        notes=[f"Jaimini AK={ak or '?'} DK={dk or '?'}"],
    )

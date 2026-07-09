"""Dasha module — current MD/AD relationship tone."""
from __future__ import annotations

from typing import Any

from .types import ChartModuleResult

_RELATIONSHIP_LORDS = frozenset({
    "Venus", "Jupiter", "Moon", "Mars", "Saturn", "Rahu", "Ketu",
})


def load_dasha(kundli: dict, *, engine_id: str) -> ChartModuleResult:
    dasha = (kundli or {}).get("dasha") or (kundli or {}).get("vimshottari") or {}
    md = str(dasha.get("mahadasha") or dasha.get("md") or "").strip()
    ad = str(dasha.get("antardasha") or dasha.get("ad") or "").strip()

    if not md and not ad:
        return ChartModuleResult(
            module_id="dasha",
            loaded=False,
            polarity="neutral",
            score=50,
            notes=["Dasha data not present on chart"],
        )

    score = 55
    factors: list[dict[str, Any]] = []
    for lord, tag in ((md, "MD"), (ad, "AD")):
        if not lord:
            continue
        pol = "positive" if lord in ("Venus", "Jupiter", "Moon") else (
            "negative" if lord in ("Rahu", "Ketu", "Saturn") else "mixed"
        )
        w = 2 if pol == "positive" else (-2 if pol == "negative" else 0)
        score += w * 8
        factors.append({
            "id": f"DSH-{tag}",
            "label": f"{tag} {lord}",
            "polarity": pol,
            "weight": abs(w) or 1,
        })

    score = max(0, min(100, score))
    pol = "positive" if score >= 68 else ("negative" if score <= 42 else "mixed")
    return ChartModuleResult(
        module_id="dasha",
        polarity=pol,
        score=score,
        factors=factors,
        notes=[f"Current dasha MD={md or '?'} AD={ad or '?'}"],
    )

"""D1 chart module — wraps person_signals + KundliReader."""
from __future__ import annotations

from typing import Any

from .types import ChartModuleResult


def load_d1(kundli: dict, *, engine_id: str) -> ChartModuleResult:
    from ask_mr.engines._person_signals import build_person_signals
    from vedic.love_reality.scoring_core import KundliReader, risk_band_high_is_good

    k = dict(kundli or {})
    k.setdefault("name", "You")
    sig = build_person_signals(k)
    r = KundliReader(k)
    w = int(sig.affliction_weight or 0)
    base = max(0, min(100, 100 - int(round(w * 1.1))))
    band = risk_band_high_is_good(base)
    if band == "low":
        polarity, score = "negative", base
    elif band == "high":
        polarity, score = "positive", base
    else:
        polarity, score = "mixed", base

    factors: list[dict[str, Any]] = []
    if getattr(sig, "reconnection_yoga", False):
        factors.append({"id": "D1-RECON", "label": "Reconnection yoga", "polarity": "positive", "weight": 2})
    if getattr(sig, "separation_yoga", False):
        factors.append({"id": "D1-SEP", "label": "Separation theme", "polarity": "negative", "weight": 2})
    if getattr(sig, "saturn_on_7th", False):
        factors.append({"id": "D1-SAT7", "label": "Saturn on 7th", "polarity": "negative", "weight": 2})
    if engine_id not in ("commitment", "loyalty_trust") and getattr(sig, "third_person_risk", False):
        factors.append({"id": "D1-TPR", "label": "Third-person risk", "polarity": "negative", "weight": 3})

    lord7 = r.house_lord(7)
    p7l = r.planet(lord7) if lord7 else None
    if lord7 and p7l:
        factors.append({
            "id": "D1-7L",
            "label": f"7th lord {lord7} in house {p7l.get('house')}",
            "polarity": "neutral",
            "weight": 1,
        })

    notes = list(sig.notes or [])[:8]
    return ChartModuleResult(
        module_id="d1",
        polarity=polarity,
        score=score,
        factors=factors,
        notes=notes,
    )

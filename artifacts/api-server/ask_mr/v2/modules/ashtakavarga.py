"""Ashtakavarga module — 7th/5th bindus."""
from __future__ import annotations

from .types import ChartModuleResult


def load_ashtakavarga(kundli: dict, *, engine_id: str) -> ChartModuleResult:
    try:
        from vedic.love_reality.scoring_core import KundliReader, SIGNS

        k = dict(kundli or {})
        r = KundliReader(k)
        asc = k.get("ascendant") or "Aries"
        asc_i = r.sidx(str(asc))
        sav = (kundli or {}).get("ashtakavarga") or (kundli or {}).get("sav") or {}

        bindu7 = None
        if isinstance(sav, dict):
            h7_sign = SIGNS[(asc_i + 6) % 12] if isinstance(asc_i, int) else None
            if h7_sign and h7_sign in sav:
                bindu7 = sav[h7_sign]
            elif sav.get("7") is not None:
                bindu7 = sav.get("7")

        if bindu7 is None:
            return ChartModuleResult(
                module_id="ashtakavarga",
                loaded=False,
                polarity="neutral",
                score=50,
                notes=["SAV bindus not on chart"],
            )

        b = int(bindu7)
        score = min(100, max(0, 40 + b * 5))
        pol = "positive" if b >= 28 else ("negative" if b <= 22 else "mixed")
        return ChartModuleResult(
            module_id="ashtakavarga",
            polarity=pol,
            score=score,
            factors=[{
                "id": "AV-7",
                "label": f"7th house SAV bindus: {b}",
                "polarity": pol,
                "weight": 2,
            }],
            notes=[f"SAV 7th bindus={b}"],
        )
    except Exception as exc:
        return ChartModuleResult(module_id="ashtakavarga", loaded=False, error=str(exc))

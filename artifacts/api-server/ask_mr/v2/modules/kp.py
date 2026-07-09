"""KP module — 7th cusp sub-lord (optional / marriage promise)."""
from __future__ import annotations

from .types import ChartModuleResult


def load_kp(kundli: dict, *, engine_id: str) -> ChartModuleResult:
    try:
        from event_timing._shared.kp_significator_scan import kp_marriage_cusp_verdict

        kp = (kundli or {}).get("kp") or {}
        if not kp:
            return ChartModuleResult(
                module_id="kp",
                loaded=False,
                polarity="neutral",
                score=50,
                notes=["KP data not on chart"],
            )
        v = kp_marriage_cusp_verdict(kp, house=7)
        verdict = str(v.get("verdict") or v.get("label") or "").upper()
        score = int(v.get("score") or 55)
        if "STRONG" in verdict or "SUPPORT" in verdict:
            pol = "positive"
        elif "WEAK" in verdict or "DENY" in verdict:
            pol = "negative"
        else:
            pol = "mixed"
        return ChartModuleResult(
            module_id="kp",
            polarity=pol,
            score=max(0, min(100, score)),
            factors=[{
                "id": "KP-7CSL",
                "label": str(v.get("why") or v.get("summary") or "7th cusp sub-lord"),
                "polarity": pol,
                "weight": 2,
            }],
            notes=[f"KP 7th: {verdict or 'mixed'}"],
        )
    except Exception as exc:
        return ChartModuleResult(
            module_id="kp",
            loaded=False,
            polarity="neutral",
            score=50,
            error=str(exc),
            notes=["KP module unavailable"],
        )

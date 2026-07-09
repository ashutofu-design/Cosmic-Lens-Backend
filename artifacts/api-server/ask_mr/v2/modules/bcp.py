"""BCP marriage linkage module."""
from __future__ import annotations

from .types import ChartModuleResult


def load_bcp(kundli: dict, *, engine_id: str) -> ChartModuleResult:
    try:
        from ask_llm_context_debug import recompute_marriage_bcp_from_kundli

        ctx: dict = {}
        out = recompute_marriage_bcp_from_kundli(ctx, kundli) or {}
        if not out:
            return ChartModuleResult(
                module_id="bcp",
                loaded=False,
                polarity="neutral",
                score=50,
                notes=["BCP linkage not computed"],
            )
        score = int(out.get("score") or out.get("bcp_score") or 55)
        score = max(0, min(100, score))
        pol = "positive" if score >= 68 else ("negative" if score <= 42 else "mixed")
        return ChartModuleResult(
            module_id="bcp",
            polarity=pol,
            score=score,
            factors=[{
                "id": "BCP-LINK",
                "label": str(out.get("summary") or "Marriage BCP linkage"),
                "polarity": pol,
                "weight": 2,
            }],
            notes=[str(out.get("summary") or "BCP evaluated")],
        )
    except Exception as exc:
        return ChartModuleResult(
            module_id="bcp",
            loaded=False,
            polarity="neutral",
            score=50,
            error=str(exc),
            notes=["BCP module unavailable"],
        )

"""General chart — D1 + D9 + dasha when Question DNA domain is general.

No domain engine. LLM reads the pack + Question DNA + Selected JSON blocks.
"""

from __future__ import annotations

from typing import Any

from ask_general_chart.engine import general_chart_slice_meta, run_general_chart_engine


def dna_wants_general_chart(admin: dict[str, Any] | None) -> bool:
    """True only when trusted Question DNA domain is explicitly general."""
    if not isinstance(admin, dict):
        return False
    dna = admin.get("question_dna")
    item: dict[str, Any] = {}
    if isinstance(dna, dict):
        qs = dna.get("questions")
        if isinstance(qs, list) and qs and isinstance(qs[0], dict):
            item = qs[0]
    domain = str(
        item.get("domain")
        or admin.get("routed_domain")
        or admin.get("domain")
        or ""
    ).strip().lower()
    if domain != "general":
        return False
    if admin.get("dna_routing_applied") or str(admin.get("routing_override") or "") == "question_dna":
        return True
    if str(admin.get("intent_source") or "") == "question_dna":
        return True
    try:
        from ask_question_dna import dna_item_trusted_for_routing

        return bool(
            dna_item_trusted_for_routing(
                item,
                dna_source=str((dna or {}).get("source") or "") if isinstance(dna, dict) else "",
            )
        )
    except Exception:
        return bool(item)


__all__ = [
    "dna_wants_general_chart",
    "run_general_chart_engine",
    "general_chart_slice_meta",
]

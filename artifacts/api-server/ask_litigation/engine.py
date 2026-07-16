"""Litigation static — unified litigation_engine_execution_v1 by default."""

from __future__ import annotations

import os

from .classifier import classify_litigation_archetype
from .types import EngineResult


def run_litigation_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
    llm_intent: dict | None = None,
) -> EngineResult:
    if (os.environ.get("ASK_LITIGATION_ENGINE") or "1").strip() == "0":
        raise RuntimeError("ASK_LITIGATION_ENGINE=0 — caller should use legacy litigation path")

    label = (archetype or "").strip().lower() or classify_litigation_archetype(question)
    from ask_unified import build_unified_engine_result

    return build_unified_engine_result(
        domain="litigation",
        kundli=kundli,
        question=question or "",
        archetype=label,
        wants_explain=wants_explain,
        llm_intent=llm_intent,
    )

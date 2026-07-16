"""Vehicle static — unified vehicle_engine_execution_v1 by default."""

from __future__ import annotations

import os

from .classifier import classify_vehicle_archetype
from .types import EngineResult


def run_vehicle_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
    llm_intent: dict | None = None,
) -> EngineResult:
    if (os.environ.get("ASK_VEHICLE_ENGINE") or "1").strip() == "0":
        raise RuntimeError("ASK_VEHICLE_ENGINE=0 — caller should use legacy vehicle path")

    label = (archetype or "").strip().lower() or classify_vehicle_archetype(question)
    from ask_unified import build_unified_engine_result

    return build_unified_engine_result(
        domain="vehicle",
        kundli=kundli,
        question=question or "",
        archetype=label,
        wants_explain=wants_explain,
        llm_intent=llm_intent,
    )

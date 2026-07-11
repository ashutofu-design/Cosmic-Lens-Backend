from __future__ import annotations

from typing import Any

from .phase1_generic import run_phase1_engine_v2


def run_secret_relationship_v2(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    orchestrator_meta: dict[str, Any] | None = None,
):
    return run_phase1_engine_v2(
        "secret_relationship",
        kundli,
        question,
        wants_explain=wants_explain,
        orchestrator_meta=orchestrator_meta,
    )

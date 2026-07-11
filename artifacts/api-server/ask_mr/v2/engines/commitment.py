"""Commitment Engine — v2 reference implementation (thin wrapper over frozen template)."""
from __future__ import annotations

from typing import Any

from ..engine_runner import run_engine_from_spec
from ..schema import EngineOutputV2
from ..specs import get_engine_spec


def run_commitment_v2(
    kundli: dict,
    question: str,
    *,
    session_id: str = "",
    wants_explain: bool = False,
    orchestrator_meta: dict[str, Any] | None = None,
) -> EngineOutputV2:
    spec = get_engine_spec("commitment")
    assert spec is not None
    return run_engine_from_spec(
        spec,
        kundli,
        question,
        session_id=session_id,
        wants_explain=wants_explain,
        orchestrator_meta=orchestrator_meta,
    )

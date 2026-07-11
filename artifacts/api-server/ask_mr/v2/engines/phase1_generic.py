"""Shared v2 runner — all non-reference engines use the same frozen template."""
from __future__ import annotations

from typing import Any

from ..engine_runner import run_engine_from_spec
from ..schema import EngineOutputV2
from ..specs import get_engine_spec


def run_phase1_engine_v2(
    engine_id: str,
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    orchestrator_meta: dict[str, Any] | None = None,
) -> EngineOutputV2:
    eid = engine_id.strip().lower()
    spec = get_engine_spec(eid)
    if spec is None:
        raise ValueError(f"No v2 engine spec for {eid!r}")
    return run_engine_from_spec(
        spec,
        kundli,
        question,
        wants_explain=wants_explain,
        orchestrator_meta=orchestrator_meta,
    )

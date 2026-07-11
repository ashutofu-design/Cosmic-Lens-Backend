"""v2 package exports."""
from __future__ import annotations

import os
from typing import Any

from .adapter import v2_to_engine_result
from .engine_runner import run_engine_from_spec
from .manifest import get_engine_manifest
from .orchestrator import orchestrate
from .registry import FROZEN_ENGINE_IDS
from .schema import EngineOutputV2
from .specs import get_engine_spec

# All 20 frozen relationship engines share the same reference template.
V2_ENGINES = FROZEN_ENGINE_IDS


def v2_enabled_for(engine_id: str) -> bool:
    if (os.environ.get("ASK_MR_ENGINE_V2") or "1").strip() == "0":
        return False
    return (engine_id or "").strip().lower() in V2_ENGINES


def run_engine_v2(
    engine_id: str,
    kundli: dict,
    question: str,
    *,
    session_id: str = "",
    wants_explain: bool = False,
    orchestrator_meta: dict[str, Any] | None = None,
) -> EngineOutputV2 | None:
    spec = get_engine_spec(engine_id)
    if spec is None:
        return None
    return run_engine_from_spec(
        spec,
        kundli,
        question,
        session_id=session_id,
        wants_explain=wants_explain,
        orchestrator_meta=orchestrator_meta,
    )

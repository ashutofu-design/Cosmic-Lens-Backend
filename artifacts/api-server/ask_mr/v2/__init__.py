"""v2 package exports."""
from __future__ import annotations

import os

from .adapter import v2_to_engine_result
from .orchestrator import orchestrate
from .schema import EngineOutputV2

V2_ENGINES = frozenset({"commitment"})


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
) -> EngineOutputV2 | None:
    eid = (engine_id or "").strip().lower()
    if eid == "commitment":
        from .engines.commitment import run_commitment_v2

        return run_commitment_v2(
            kundli,
            question,
            session_id=session_id,
            wants_explain=wants_explain,
        )
    return None

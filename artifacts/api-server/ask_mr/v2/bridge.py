"""v1 ↔ v2 bridge — one line per engine entrypoint."""
from __future__ import annotations

from typing import Any, Callable

from ask_mr.types import EngineResult


def try_run_v2(
    engine_id: str,
    kundli: dict,
    question: str,
    run_v1: Callable[..., EngineResult],
    *,
    wants_explain: bool = False,
    birth: Any = None,
    **kwargs: Any,
) -> EngineResult:
    try:
        from ask_mr.v2 import run_engine_v2, v2_enabled_for
        from ask_mr.v2.adapter import v2_to_engine_result

        eid = (engine_id or "").strip().lower()
        if v2_enabled_for(eid):
            out = run_engine_v2(eid, kundli, question, wants_explain=wants_explain, **kwargs)
            if out is not None:
                return v2_to_engine_result(out)
    except Exception:
        pass
    if birth is not None:
        return run_v1(kundli, question, birth=birth, wants_explain=wants_explain, **kwargs)
    return run_v1(kundli, question, wants_explain=wants_explain, **kwargs)

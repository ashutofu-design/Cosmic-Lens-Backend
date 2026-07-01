from __future__ import annotations

import os

from .classifier import classify_network_archetype
from .types import EngineResult


def run_network_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> EngineResult:
    if (os.environ.get("ASK_NETWORK_ENGINE") or "1").strip() == "0":
        raise RuntimeError("ASK_NETWORK_ENGINE=0 — caller should use legacy path")

    archetype = (archetype or "").strip().lower() or classify_network_archetype(question)

    from .engines.network_engines import (
        run_enmity_in_circle,
        run_friends_support,
        run_general_network,
        run_influential_network,
        run_social_circle_quality,
    )

    dispatch = {
        "social_circle_quality": run_social_circle_quality,
        "friends_support": run_friends_support,
        "enmity_in_circle": run_enmity_in_circle,
        "influential_network": run_influential_network,
        "general_network": run_general_network,
    }
    runner = dispatch.get(archetype, run_general_network)
    return runner(kundli, question, wants_explain=wants_explain)

from __future__ import annotations

import os

from .classifier import classify_luck_archetype
from .types import EngineResult


def run_luck_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> EngineResult:
    if (os.environ.get("ASK_LUCK_ENGINE") or "1").strip() == "0":
        raise RuntimeError("ASK_LUCK_ENGINE=0 — caller should use legacy path")

    archetype = (archetype or "").strip().lower() or classify_luck_archetype(question)

    from .engines.luck_engines import (
        run_career_luck,
        run_general_luck,
        run_love_luck,
        run_luck_strength,
        run_lucky_traits,
        run_money_luck,
        run_overall_luck,
    )

    dispatch = {
        "overall_luck": run_overall_luck,
        "luck_strength": run_luck_strength,
        "career_luck": run_career_luck,
        "love_luck": run_love_luck,
        "money_luck": run_money_luck,
        "lucky_traits": run_lucky_traits,
        "general_luck": run_general_luck,
    }
    runner = dispatch.get(archetype, run_general_luck)
    return runner(kundli, question, wants_explain=wants_explain)

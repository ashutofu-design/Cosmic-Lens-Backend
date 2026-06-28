from __future__ import annotations

import os

from .classifier import classify_travel_archetype
from .types import EngineResult


def run_travel_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> EngineResult:
    if (os.environ.get("ASK_TRAVEL_ENGINE") or "1").strip() == "0":
        raise RuntimeError("ASK_TRAVEL_ENGINE=0 — caller should use legacy travel path")

    archetype = (archetype or "").strip().lower() or classify_travel_archetype(question)

    from .engines.travel_engines import (
        run_business_travel,
        run_foreign_settlement,
        run_general_travel,
        run_immigration,
        run_passport_travel,
        run_pilgrimage_travel,
        run_relocation_abroad,
        run_return_india,
        run_short_travel,
        run_travel_obstacles,
        run_travel_risk,
        run_travel_country_fit,
        run_travel_yog,
        run_visa_theme,
    )

    dispatch = {
        "travel_yog": run_travel_yog,
        "foreign_settlement": run_foreign_settlement,
        "visa_theme": run_visa_theme,
        "relocation_abroad": run_relocation_abroad,
        "return_india": run_return_india,
        "travel_obstacles": run_travel_obstacles,
        "short_travel": run_short_travel,
        "pilgrimage_travel": run_pilgrimage_travel,
        "passport_travel": run_passport_travel,
        "immigration": run_immigration,
        "business_travel": run_business_travel,
        "travel_risk": run_travel_risk,
        "travel_country_fit": run_travel_country_fit,
        "general_travel": run_general_travel,
    }
    runner = dispatch.get(archetype, run_general_travel)
    return runner(kundli, question, wants_explain=wants_explain)

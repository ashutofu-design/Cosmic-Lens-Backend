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
) -> EngineResult:
    if (os.environ.get("ASK_VEHICLE_ENGINE") or "1").strip() == "0":
        raise RuntimeError("ASK_VEHICLE_ENGINE=0 — caller should use legacy vehicle path")

    archetype = (archetype or "").strip().lower() or classify_vehicle_archetype(question)

    from .engines.vehicle_engines import (
        run_general_vehicle,
        run_vehicle_colour,
        run_vehicle_commercial,
        run_vehicle_driving,
        run_vehicle_ev,
        run_vehicle_family_budget,
        run_vehicle_festival,
        run_vehicle_growth,
        run_vehicle_loan,
        run_vehicle_luxury,
        run_vehicle_multi,
        run_vehicle_new_used,
        run_vehicle_ownership,
        run_vehicle_planning,
        run_vehicle_safety,
        run_vehicle_vip,
    )

    dispatch = {
        "vehicle_colour": run_vehicle_colour,
        "vehicle_new_used": run_vehicle_new_used,
        "vehicle_safety": run_vehicle_safety,
        "vehicle_luxury": run_vehicle_luxury,
        "vehicle_commercial": run_vehicle_commercial,
        "vehicle_loan": run_vehicle_loan,
        "vehicle_ownership": run_vehicle_ownership,
        "vehicle_ev": run_vehicle_ev,
        "vehicle_multi": run_vehicle_multi,
        "vehicle_festival": run_vehicle_festival,
        "vehicle_growth": run_vehicle_growth,
        "vehicle_family_budget": run_vehicle_family_budget,
        "vehicle_vip": run_vehicle_vip,
        "vehicle_driving": run_vehicle_driving,
        "vehicle_planning": run_vehicle_planning,
        "general_vehicle": run_general_vehicle,
    }
    runner = dispatch.get(archetype, run_general_vehicle)
    return runner(kundli, question, wants_explain=wants_explain)

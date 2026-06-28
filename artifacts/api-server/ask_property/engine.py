from __future__ import annotations

import os

from .classifier import classify_property_archetype
from .types import EngineResult


def run_property_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> EngineResult:
    if (os.environ.get("ASK_PROPERTY_ENGINE") or "1").strip() == "0":
        raise RuntimeError("ASK_PROPERTY_ENGINE=0 — caller should use legacy property path")

    archetype = (archetype or "").strip().lower() or classify_property_archetype(question)

    from .engines.property_engines import (
        run_general_property,
        run_property_build,
        run_property_buy,
        run_property_capacity,
        run_property_dispute,
        run_property_inherit,
        run_property_land,
        run_property_loan,
        run_property_rent,
        run_property_risk,
        run_property_sell,
        run_property_sale_tax,
        run_property_type_fit,
        run_property_yog,
    )

    dispatch = {
        "property_yog": run_property_yog,
        "property_capacity": run_property_capacity,
        "property_risk": run_property_risk,
        "property_type_fit": run_property_type_fit,
        "property_inherit": run_property_inherit,
        "property_dispute": run_property_dispute,
        "property_rent": run_property_rent,
        "property_build": run_property_build,
        "property_sell": run_property_sell,
        "property_sale_tax": run_property_sale_tax,
        "property_buy": run_property_buy,
        "property_loan": run_property_loan,
        "property_land": run_property_land,
        "general_property": run_general_property,
    }
    runner = dispatch.get(archetype, run_general_property)
    return runner(kundli, question, wants_explain=wants_explain)

from __future__ import annotations

import os

from .classifier import classify_litigation_archetype
from .types import EngineResult


def run_litigation_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> EngineResult:
    if (os.environ.get("ASK_LITIGATION_ENGINE") or "1").strip() == "0":
        raise RuntimeError("ASK_LITIGATION_ENGINE=0 — caller should use legacy litigation path")

    archetype = (archetype or "").strip().lower() or classify_litigation_archetype(question)

    from .engines.litigation_engines import (
        run_acquittal_relief,
        run_bail_theme,
        run_case_outcome,
        run_civil_litigation,
        run_court_delay,
        run_criminal_case,
        run_enemy_case,
        run_family_court,
        run_general_litigation,
        run_jail_concern,
        run_lawyer_support,
        run_legal_obstacles,
        run_litigation_remedy,
        run_litigation_yog,
        run_police_fir,
    )

    dispatch = {
        "litigation_remedy": run_litigation_remedy,
        "litigation_yog": run_litigation_yog,
        "case_outcome": run_case_outcome,
        "court_delay": run_court_delay,
        "bail_theme": run_bail_theme,
        "jail_concern": run_jail_concern,
        "police_fir": run_police_fir,
        "criminal_case": run_criminal_case,
        "civil_litigation": run_civil_litigation,
        "legal_obstacles": run_legal_obstacles,
        "enemy_case": run_enemy_case,
        "acquittal_relief": run_acquittal_relief,
        "lawyer_support": run_lawyer_support,
        "family_court": run_family_court,
        "general_litigation": run_general_litigation,
    }
    runner = dispatch.get(archetype, run_general_litigation)
    result = runner(kundli, question, wants_explain=wants_explain)
    from .remedy import attach_remedy_to_result

    return attach_remedy_to_result(result, kundli, question)

from __future__ import annotations

import os

from .classifier import classify_children_archetype
from .types import EngineResult


def run_children_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> EngineResult:
    if (os.environ.get("ASK_CHILDREN_ENGINE") or "1").strip() == "0":
        raise RuntimeError("ASK_CHILDREN_ENGINE=0 — caller should use legacy children path")

    archetype = (archetype or "").strip().lower() or classify_children_archetype(question)

    from .engines.progeny_engines import (
        run_adoption_path,
        run_child_delay,
        run_child_gender_note,
        run_child_loss_concern,
        run_child_nature,
        run_child_promise,
        run_child_success,
        run_fertility_conception,
        run_general_children,
        run_number_of_children,
        run_parent_child_bond,
        run_pregnancy_wellbeing,
        run_progeny_obstacles,
    )

    dispatch = {
        "child_promise": run_child_promise,
        "fertility_conception": run_fertility_conception,
        "pregnancy_wellbeing": run_pregnancy_wellbeing,
        "child_delay": run_child_delay,
        "child_gender_note": run_child_gender_note,
        "number_of_children": run_number_of_children,
        "child_nature": run_child_nature,
        "parent_child_bond": run_parent_child_bond,
        "child_success": run_child_success,
        "adoption_path": run_adoption_path,
        "child_loss_concern": run_child_loss_concern,
        "progeny_obstacles": run_progeny_obstacles,
        "general_children": run_general_children,
    }
    runner = dispatch.get(archetype, run_general_children)
    return runner(kundli, question, wants_explain=wants_explain)

from __future__ import annotations

import os

from .classifier import classify_education_archetype
from .types import EngineResult


def run_education_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> EngineResult:
    if (os.environ.get("ASK_EDUCATION_ENGINE") or "1").strip() == "0":
        raise RuntimeError("ASK_EDUCATION_ENGINE=0 — caller should use legacy education path")

    archetype = (archetype or "").strip().lower() or classify_education_archetype(question)

    if archetype == "exam_success":
        from .engines.exam_success import run_exam_success
        return run_exam_success(kundli, question, wants_explain=wants_explain)
    if archetype == "competitive_exam":
        from .engines.competitive_exam import run_competitive_exam
        return run_competitive_exam(kundli, question, wants_explain=wants_explain)
    if archetype == "higher_studies":
        from .engines.higher_studies import run_higher_studies
        return run_higher_studies(kundli, question, wants_explain=wants_explain)
    if archetype == "study_field":
        from .engines.study_field import run_study_field
        return run_study_field(kundli, question, wants_explain=wants_explain)
    if archetype == "specialization_path":
        from .engines.specialization_path import run_specialization_path
        return run_specialization_path(kundli, question, wants_explain=wants_explain)
    if archetype == "admission":
        from .engines.admission import run_admission
        return run_admission(kundli, question, wants_explain=wants_explain)
    if archetype == "scholarship":
        from .engines.scholarship import run_scholarship
        return run_scholarship(kundli, question, wants_explain=wants_explain)
    if archetype == "degree_completion":
        from .engines.degree_completion import run_degree_completion
        return run_degree_completion(kundli, question, wants_explain=wants_explain)
    if archetype == "marks_performance":
        from .engines.marks_performance import run_marks_performance
        return run_marks_performance(kundli, question, wants_explain=wants_explain)
    if archetype == "study_focus":
        from .engines.study_focus import run_study_focus
        return run_study_focus(kundli, question, wants_explain=wants_explain)
    if archetype == "learning_ability":
        from .engines.learning_ability import run_learning_ability
        return run_learning_ability(kundli, question, wants_explain=wants_explain)
    if archetype == "coaching_support":
        from .engines.coaching_support import run_coaching_support
        return run_coaching_support(kundli, question, wants_explain=wants_explain)
    if archetype == "education_obstacles":
        from .engines.education_obstacles import run_education_obstacles
        return run_education_obstacles(kundli, question, wants_explain=wants_explain)
    if archetype == "vocational_diploma":
        from .engines.vocational_diploma import run_vocational_diploma
        return run_vocational_diploma(kundli, question, wants_explain=wants_explain)

    from .engines.general_education import run_general_education
    return run_general_education(kundli, question, wants_explain=wants_explain)

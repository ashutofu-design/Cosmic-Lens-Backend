from __future__ import annotations

import os
from typing import Any

from .classifier import classify_career_archetype
from .types import EngineResult


def run_career_static_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> EngineResult:
    if (os.environ.get("ASK_CAREER_ENGINE") or "1").strip() == "0":
        raise RuntimeError("ASK_CAREER_ENGINE=0 — caller should use legacy career path")

    archetype = (archetype or "").strip().lower() or classify_career_archetype(question)

    if archetype == "job_vs_business":
        from .engines.job_vs_business import run_job_vs_business
        return run_job_vs_business(kundli, question, wants_explain=wants_explain)
    if archetype == "sector_fit":
        from .engines.sector_fit import run_sector_fit
        return run_sector_fit(kundli, question, wants_explain=wants_explain)
    if archetype == "career_traits":
        from .engines.career_traits import run_career_traits
        return run_career_traits(kundli, question, wants_explain=wants_explain)
    if archetype == "strengths_skills":
        from .engines.strengths_skills import run_strengths_skills
        return run_strengths_skills(kundli, question, wants_explain=wants_explain)
    if archetype == "entrepreneurship":
        from .engines.entrepreneurship import run_entrepreneurship
        return run_entrepreneurship(kundli, question, wants_explain=wants_explain)
    if archetype == "work_environment":
        from .engines.work_environment import run_work_environment
        return run_work_environment(kundli, question, wants_explain=wants_explain)
    if archetype == "income_wealth":
        from .engines.income_wealth import run_income_wealth
        return run_income_wealth(kundli, question, wants_explain=wants_explain)
    if archetype == "foreign_career":
        from .engines.foreign_career import run_foreign_career
        return run_foreign_career(kundli, question, wants_explain=wants_explain)
    if archetype == "workplace_relations":
        from .engines.workplace_relations import run_workplace_relations
        return run_workplace_relations(kundli, question, wants_explain=wants_explain)
    if archetype == "fame_recognition":
        from .engines.fame_recognition import run_fame_recognition
        return run_fame_recognition(kundli, question, wants_explain=wants_explain)
    if archetype == "creativity_innovation":
        from .engines.creativity_innovation import run_creativity_innovation
        return run_creativity_innovation(kundli, question, wants_explain=wants_explain)
    if archetype == "career_obstacles":
        from .engines.career_obstacles import run_career_obstacles
        return run_career_obstacles(kundli, question, wants_explain=wants_explain)
    if archetype == "education_career":
        from .engines.education_career import run_education_career
        return run_education_career(kundli, question, wants_explain=wants_explain)
    if archetype == "retirement_legacy":
        from .engines.retirement_legacy import run_retirement_legacy
        return run_retirement_legacy(kundli, question, wants_explain=wants_explain)

    from .engines.general_career import run_general_career
    return run_general_career(kundli, question, wants_explain=wants_explain)

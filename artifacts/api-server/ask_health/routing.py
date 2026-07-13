"""Health routing — hard guards only; all other health Qs use D1/D9 chart JSON."""

from __future__ import annotations

from .classifier import classify_health_archetype
from .health_registry import HEALTH_ARCHETYPES, is_health_static_question

__all__ = [
    "HEALTH_ARCHETYPES",
    "classify_health_archetype",
    "health_overrides_career",
    "is_health_static_question",
    "resolve_health_archetype",
]


def health_overrides_career(question: str) -> bool:
    """Health subdomain Qs beat generic career keyword overlap."""
    return bool(is_health_static_question((question or "").strip()))


def resolve_health_archetype(
    question: str,
    *,
    llm_archetype: str | None = None,
    interpretation: str = "",
) -> tuple[str, str]:
    q = (question or "").strip()
    try:
        from chart_fact_answer import is_domain_life_area_interpretation_question

        if is_domain_life_area_interpretation_question(q):
            return "health_engine_execution_v1", "blocked_love_life_interpretation"
    except Exception:
        pass

    arch = classify_health_archetype(q)
    if arch != "health_engine_execution_v1":
        return arch, "hard_guard"

    llm = (llm_archetype or "").strip().lower()
    if llm and llm in HEALTH_ARCHETYPES and llm != "health_engine_execution_v1":
        if llm.startswith("refuse_") or llm == "crisis_redirect":
            return llm, "llm_hard_guard"
        return llm, "llm_archetype"
    return "health_engine_execution_v1", "d1_d9_chart"

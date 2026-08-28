"""General chart static runner — LLM-only path when DNA domain=general."""

from __future__ import annotations

from typing import Any

from ask_mr.types import EngineResult


def run_general_chart_engine(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    llm_intent: dict | None = None,
) -> EngineResult:
    from ask_general_chart.facts import compute_general_chart_execution

    pack = compute_general_chart_execution(
        kundli if isinstance(kundli, dict) else {},
        question=question or "",
        llm_intent=llm_intent,
    )
    result = EngineResult(
        archetype="general_chart",
        verdict="general_chart — D1 + D9 + dasha for LLM study",
        confidence="medium",
        word_budget=95 if wants_explain else 75,
        answer_plan=(
            "Read GENERAL_CHART_ENGINE_EXECUTION_JSON (D1 + D9 + dasha). "
            "Question DNA domain=general — no specialist engine. "
            "Answer the user's exact question from pack facts + QUESTION_PRIORITY_FACTS."
        ),
        summary=[
            "General chart pack: full D1 + D9 + current/upcoming dasha.",
            "Pure LLM narration guided by Question DNA + selected JSON blocks.",
        ],
        evidence=[],
        ignore=["invented placements", "fake dasha dates", "wrong domain engine facts"],
        checks={
            "slice_type": "general_chart_engine_v1",
            "archetype": "general_chart",
            "routing_label": "general_chart",
            "unified_execution": True,
            "domain": "general",
            "general_chart_engine_execution": pack,
            "engine_version": "general_chart_engine_execution_v1",
            "charts_used": pack.get("charts_used") or ["D1", "D9", "DASHA"],
        },
    )
    return result


def general_chart_slice_meta(result: EngineResult) -> dict[str, Any]:
    pos, neg, neu = result._finalize_evidence_split()
    checks = dict(result.checks or {})
    return {
        "slice": "general_chart_engine_v1",
        "topic": "general",
        "archetype": result.archetype,
        "verdict": result.verdict,
        "summary": list(result.summary or []),
        "evidence": list(result.evidence or []),
        "evidence_positive": pos,
        "evidence_negative": neg,
        "evidence_neutral": neu,
        "ignore": list(result.ignore or []),
        "checks": checks,
        "skip_llm": False,
        "word_budget": int(result.word_budget or 75),
        "narrator_mode": "llm_general_chart",
    }

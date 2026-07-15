from __future__ import annotations

import os
from typing import Any

from .classifier import classify_mr_archetype
from .types import EngineResult


def _legacy_slice_enabled() -> bool:
    return (os.environ.get("ASK_MR_ENGINE") or "1").strip() == "0"


def _legacy_archetype_engines_enabled() -> bool:
    """Escape hatch: per-archetype score engines (pre-unified Execution)."""
    return (os.environ.get("ASK_MR_LEGACY_ARCHETYPE_ENGINES") or "").strip().lower() in (
        "1", "true", "yes", "on",
    )


def _resolve_mr_archetype_label(
    question: str,
    archetype: str | None,
) -> str:
    """Classify routing label only — does not run score engines."""
    archetype = (archetype or "").strip().lower()
    try:
        from ask_chart_open_qa import should_use_open_chart_qa

        if should_use_open_chart_qa(question or "", {"mr_archetype": archetype} if archetype else None):
            archetype = "open_chart_qa"
    except Exception:
        pass
    if not archetype:
        archetype = classify_mr_archetype(question)
    try:
        from ask_route_from_understanding import is_native_love_chart_question

        if is_native_love_chart_question(question or "") and archetype in (
            "dating_courtship",
            "chemistry",
            "one_sided_love",
        ):
            archetype = "dating_courtship"
    except Exception:
        pass
    if archetype:
        try:
            from ask_intent_fidelity import archetype_allowed_for_question

            if not archetype_allowed_for_question(question, archetype):
                try:
                    from ask_chart_open_qa import should_use_open_chart_qa

                    if should_use_open_chart_qa(question):
                        archetype = "open_chart_qa"
                    else:
                        archetype = classify_mr_archetype(question)
                except Exception:
                    archetype = classify_mr_archetype(question)
        except Exception:
            pass
    if not archetype:
        archetype = classify_mr_archetype(question) or "general_mr"
    return archetype


def _attach_relationship_engine_execution(
    result: EngineResult,
    kundli: dict,
    *,
    question: str = "",
    llm_intent: dict | None = None,
) -> EngineResult:
    """Persist fixed D1 + D9 relationship chart pack (health-style)."""
    try:
        from relationship_static.relationship_facts import (
            compute_relationship_engine_execution,
        )

        pack = compute_relationship_engine_execution(
            kundli if isinstance(kundli, dict) else {},
            question=question or "",
            routing_label=result.archetype or "",
            llm_intent=llm_intent,
        )
        checks = dict(result.checks or {})
        checks["relationship_engine_execution"] = pack
        checks["d1_relationship_facts"] = pack.get("d1") or {}
        checks["d9_relationship_facts"] = pack.get("d9") or {}
        checks["engine_version"] = "relationship_engine_execution_v1"
        checks["routing_label"] = result.archetype
        result.checks = checks
    except Exception as exc:
        checks = dict(result.checks or {})
        checks["relationship_engine_execution_error"] = str(exc)[:180]
        result.checks = checks
    return result


def _run_legacy_archetype_engines(
    kundli: dict,
    question: str,
    *,
    birth: Any = None,
    wants_explain: bool = False,
    archetype: str,
) -> EngineResult:
    """Pre-unified path: dispatch to 31 archetype score engines / v2."""
    if archetype:
        try:
            from ask_mr.v2 import run_engine_v2, v2_enabled_for
            from ask_mr.v2.adapter import v2_to_engine_result
            from ask_mr.v2.registry import FROZEN_ENGINE_IDS

            if archetype in FROZEN_ENGINE_IDS and v2_enabled_for(archetype):
                out = run_engine_v2(archetype, kundli, question, wants_explain=wants_explain)
                if out is not None:
                    return v2_to_engine_result(out)
        except Exception:
            pass

    if archetype == "open_chart_qa":
        from ask_chart_open_qa import run_open_chart_qa

        return run_open_chart_qa(kundli, question, wants_explain=wants_explain)

    if archetype == "breakup_risk":
        from .engines.breakup_risk import run_breakup_risk

        return run_breakup_risk(kundli, question, wants_explain=wants_explain)

    if archetype == "partner_nature":
        from .engines.partner_nature import run_partner_nature

        return run_partner_nature(kundli, question, birth=birth, wants_explain=wants_explain)

    if archetype == "manglik":
        from .engines.manglik import run_manglik

        return run_manglik(kundli, question, wants_explain=wants_explain)

    if archetype == "love_vs_arranged":
        from .engines.love_vs_arranged import run_love_vs_arranged

        return run_love_vs_arranged(kundli, question, wants_explain=wants_explain)

    if archetype == "loyalty_trust":
        from .engines.loyalty_trust import run_loyalty_trust

        return run_loyalty_trust(kundli, question, wants_explain=wants_explain)

    if archetype == "chemistry":
        from .engines.chemistry import run_chemistry

        return run_chemistry(kundli, question, wants_explain=wants_explain)

    if archetype == "compatibility":
        from .engines.compatibility import run_compatibility

        return run_compatibility(kundli, question, wants_explain=wants_explain)

    if archetype == "commitment":
        from .engines.commitment import run_commitment

        return run_commitment(kundli, question, wants_explain=wants_explain)

    if archetype == "communication":
        from .engines.communication import run_communication

        return run_communication(kundli, question, wants_explain=wants_explain)

    if archetype == "relationship_future":
        from .engines.relationship_future import run_relationship_future

        return run_relationship_future(kundli, question, wants_explain=wants_explain)

    if archetype == "relationship_decisions":
        from .engines.relationship_decisions import run_relationship_decisions

        return run_relationship_decisions(kundli, question, wants_explain=wants_explain)

    if archetype == "toxicity":
        from .engines.toxicity import run_toxicity

        return run_toxicity(kundli, question, wants_explain=wants_explain)

    if archetype == "relationship_remedies":
        from .engines.relationship_remedies import run_relationship_remedies

        return run_relationship_remedies(kundli, question, wants_explain=wants_explain)

    if archetype == "patchup":
        from .engines.patchup import run_patchup

        return run_patchup(kundli, question, wants_explain=wants_explain)

    if archetype == "family_approval":
        from .engines.family_approval import run_family_approval

        return run_family_approval(kundli, question, wants_explain=wants_explain)

    if archetype == "spouse_profession":
        from .engines.spouse_profession import run_spouse_profession

        return run_spouse_profession(kundli, question, wants_explain=wants_explain)

    if archetype == "spouse_wealth":
        from .engines.spouse_wealth import run_spouse_wealth

        return run_spouse_wealth(kundli, question, wants_explain=wants_explain)

    if archetype == "spouse_appearance":
        from .engines.spouse_appearance import run_spouse_appearance

        return run_spouse_appearance(kundli, question, wants_explain=wants_explain)

    if archetype == "children_parenting":
        from .engines.children_parenting import run_children_parenting

        return run_children_parenting(kundli, question, wants_explain=wants_explain)

    if archetype == "karmic_marriage":
        from .engines.karmic_marriage import run_karmic_marriage

        return run_karmic_marriage(kundli, question, wants_explain=wants_explain)

    if archetype == "lifestyle_marriage":
        from .engines.lifestyle_marriage import run_lifestyle_marriage

        return run_lifestyle_marriage(kundli, question, wants_explain=wants_explain)

    if archetype == "dating_courtship":
        from .engines.dating_courtship import run_dating_courtship

        return run_dating_courtship(kundli, question, wants_explain=wants_explain)

    if archetype == "second_marriage":
        from .engines.second_marriage import run_second_marriage

        return run_second_marriage(kundli, question, wants_explain=wants_explain)

    if archetype == "long_distance":
        from .engines.long_distance import run_long_distance

        return run_long_distance(kundli, question, wants_explain=wants_explain)

    if archetype == "one_sided_love":
        from .engines.one_sided_love import run_one_sided_love

        return run_one_sided_love(kundli, question, wants_explain=wants_explain)

    if archetype == "secret_relationship":
        from .engines.secret_relationship import run_secret_relationship

        return run_secret_relationship(kundli, question, wants_explain=wants_explain)

    if archetype == "obsession":
        from .engines.obsession import run_obsession

        return run_obsession(kundli, question, wants_explain=wants_explain)

    if archetype == "emotional_attachment":
        from .engines.emotional_attachment import run_emotional_attachment

        return run_emotional_attachment(kundli, question, wants_explain=wants_explain)

    if archetype == "bed_intimacy":
        from .engines.bed_intimacy import run_bed_intimacy

        return run_bed_intimacy(kundli, question, wants_explain=wants_explain)

    if archetype == "self_worth":
        from .engines.self_worth import run_self_worth

        return run_self_worth(kundli, question, wants_explain=wants_explain)

    from .engines.general_mr import run_general_mr

    return run_general_mr(kundli, question, wants_explain=wants_explain)


def run_mr_static_engine(
    kundli: dict,
    question: str,
    *,
    birth: Any = None,
    wants_explain: bool = False,
    archetype: str | None = None,
    llm_intent: dict | None = None,
) -> EngineResult:
    """MR static engine entrypoint — unified relationship_engine_execution_v1 by default.

    Archetype is a routing label (question focus). Set
    ASK_MR_LEGACY_ARCHETYPE_ENGINES=1 to restore per-archetype score engines.
    Set ASK_MR_ENGINE=0 to force legacy marriage slice upstream.
    """
    if _legacy_slice_enabled():
        raise RuntimeError("ASK_MR_ENGINE=0 — caller should use legacy marriage slice")

    label = _resolve_mr_archetype_label(question, archetype)

    # Open-chart Q&A stays on its dedicated path (locked topic facts).
    if label == "open_chart_qa":
        from ask_chart_open_qa import run_open_chart_qa

        return run_open_chart_qa(kundli, question, wants_explain=wants_explain)

    if _legacy_archetype_engines_enabled():
        result = _run_legacy_archetype_engines(
            kundli,
            question,
            birth=birth,
            wants_explain=wants_explain,
            archetype=label,
        )
        return _attach_relationship_engine_execution(
            result, kundli, question=question or "", llm_intent=llm_intent,
        )

    # Unified path (health-style): one D1+D9 pack; archetype = routing label only.
    result = EngineResult(
        archetype=label,
        verdict="",
        confidence="medium",
        word_budget=85 if wants_explain else 65,
        answer_plan=(
            "Read RELATIONSHIP_ENGINE_EXECUTION_JSON (D1 + D9). "
            f"routing_label={label} is the answer focus only — answer the user's exact "
            "relationship question in warm Hinglish using pack facts, not invented placements."
        ),
        summary=[
            "Unified relationship pack: D1 + D9 axes (7L / Venus / Moon / manglik).",
            f"Routing label (focus): {label}",
        ],
        evidence=[],
        ignore=["exact marriage date", "death prediction", "medical diagnosis"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": label,
            "routing_label": label,
            "unified_execution": True,
        },
    )
    return _attach_relationship_engine_execution(
        result, kundli, question=question or "", llm_intent=llm_intent,
    )


def mr_engine_slice_meta(result: EngineResult) -> dict[str, Any]:
    """Admin/debug slice_meta for MR engine — includes positive/negative evidence split."""
    pos, neg, neu = result._finalize_evidence_split()
    checks = dict(result.checks or {})
    step_audit: dict[str, Any] = {}
    try:
        from ask_mr.pipeline_audit import build_mr_step_audit_from_result

        step_audit = build_mr_step_audit_from_result(result)
    except Exception:
        pass
    meta: dict[str, Any] = {
        "slice": "mr_engine_v1",
        "topic": "marriage_and_relationship",
        "archetype": result.archetype,
        "verdict": result.verdict,
        "summary": list(result.summary or []),
        "evidence": list(result.evidence or []),
        "evidence_positive": pos,
        "evidence_negative": neg,
        "evidence_neutral": neu,
        "ignore": list(result.ignore or []),
        "checks": checks,
        "skip_llm": bool(result.skip_llm),
        "word_budget": int(result.word_budget or 55),
        "narrator_mode": "engine_facts_only",
        "engine_version": checks.get("engine_version") or "mr_engine_v1",
    }
    if step_audit:
        meta["step_audit"] = step_audit
    return meta

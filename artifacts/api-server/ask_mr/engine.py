from __future__ import annotations

import os
from typing import Any

from .classifier import classify_mr_archetype
from .types import EngineResult


def _legacy_slice_enabled() -> bool:
    return (os.environ.get("ASK_MR_ENGINE") or "1").strip() == "0"


def run_mr_static_engine(
    kundli: dict,
    question: str,
    *,
    birth: Any = None,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> EngineResult:
    """MR static engine entrypoint. Set ASK_MR_ENGINE=0 to force legacy slice upstream.

    When `archetype` is provided (e.g. from the LLM-first intent classifier)
    it is used directly instead of the regex `classify_mr_archetype`, letting
    the caller route nuanced questions the regex would mislabel.
    """
    if _legacy_slice_enabled():
        raise RuntimeError("ASK_MR_ENGINE=0 — caller should use legacy marriage slice")

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

        # Native love-yog reads: only bump archetypes already in the dating/romance lane.
        # Promise Qs (general_mr, partner_nature, love-life success) keep classifier choice.
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
        archetype = classify_mr_archetype(question)

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


def mr_engine_slice_meta(result: EngineResult) -> dict[str, Any]:
    """Admin/debug slice_meta for MR engine — includes positive/negative evidence split."""
    pos, neg, neu = result._finalize_evidence_split()
    return {
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
        "checks": dict(result.checks or {}),
        "skip_llm": bool(result.skip_llm),
        "word_budget": int(result.word_budget or 55),
        "narrator_mode": "engine_facts_only",
    }

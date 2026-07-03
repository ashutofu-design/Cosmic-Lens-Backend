"""Cosmic Ask routing policy — engine first, then LLM; off-topic refused.

Order (raw_passthrough):
  1. Scope gate — jyotish / vastu / numerology only (random GK refused)
  2. Hard guards (death, timing clarify)
  3. Pure chart_fact lookup only (lagna/placement one-liner, optional)
  4. Dedicated engine when matched → engine facts + LLM narrator
  5. No engine → FULL LLM (rich chart + question lock) — default, no refusal
"""

from __future__ import annotations

import re
from typing import Any

_COSMIC_DOMAIN_RX = re.compile(
    r"(?ix)\b("
    r"jyotish|astrology|horoscope|kundli|kundali|chart|rashi|lagna|"
    r"nakshatra|dasha|mahadasha|antardasha|graha|planet|transit|gochar|"
    r"vastu|vaastu|numerology|ank\s*shastra|ank\s*vidya|life\s*path\s*number|"
    r"tarot|palmistry|hast\s*rekha|hastrekha|"
    r"gemstone|ratna|muhurat|muhurta|panchang|lal\s*kitab|"
    r"manglik|mangal\s*dosh|kuja\s*dosh|"
    r"mantra|puja|yantra|remedy|upay|parashari|vedic|bhakti|adhyatm|"
    r"spiritual|spirituality|occult|jyotish\s*shastra"
    r")\b",
)

_CONCEPT_SHAPE_RX = re.compile(
    r"(?ix)\b("
    r"kya\s+(?:hai|he|hot[ae]|hota|hote)|matlab|meaning|explain|samjha|"
    r"kaise\s+(?:kaam|help|kare)|kab\s+use|kya\s+farak|difference|"
    r"concept|definition|types?|rules?|se\s+kya|isse\s+kya"
    r")\b",
)


def is_cosmic_domain_question(question: str) -> bool:
    """Astrology / vastu / numerology / related — in-app scope."""
    q = (question or "").strip()
    if not q:
        return False
    if _COSMIC_DOMAIN_RX.search(q):
        return True
    try:
        from domain_splitter import extract_domains, has_astro_anchor

        if extract_domains(q):
            return True
        if has_astro_anchor(q):
            return True
    except Exception:
        pass
    try:
        from chart_fact_answer import needs_llm_chart_answer

        if needs_llm_chart_answer(q):
            return True
    except Exception:
        pass
    return False


def is_cosmic_domain_concept_question(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> bool:
    """In-domain education — no dedicated engine."""
    q = (question or "").strip()
    if not q or not is_cosmic_domain_question(q):
        return False
    try:
        from chart_fact_answer import is_pure_chart_fact_lookup

        if is_pure_chart_fact_lookup(q):
            return False
    except Exception:
        pass
    if _CONCEPT_SHAPE_RX.search(q):
        return True
    dom = str((llm_intent or {}).get("domain") or "").strip().lower()
    if dom in ("spiritual", "vastu", "general", "luck"):
        return True
    try:
        from ask_question_normalize import has_question_intent

        if has_question_intent(q) and len(q.split()) <= 22:
            return True
    except Exception:
        pass
    return False


def build_no_engine_llm_rules(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> str:
    """Prompt lock when no domain engine ran — LLM must understand Q and answer."""
    intent = llm_intent if isinstance(llm_intent, dict) else {}
    lock = (
        str(intent.get("question_meaning") or "").strip()
        or str(intent.get("question_summary") or "").strip()
        or (question or "").strip()
    )
    scope = str(intent.get("question_scope") or "").strip().lower()
    scope_line = f"\nSCOPE TAG: [{scope}]" if scope else ""
    div_line = ""
    try:
        from chart_fact_answer import _detect_divisional

        varga = _detect_divisional(question or "")
        if varga:
            div_line = (
                f"\nDIVISIONAL LOCK: User asked about {varga} — read {varga} from chart block, "
                f"NOT D1 only. Explain what it means for their question; full 3-section answer.\n"
            )
    except Exception:
        pass
    return (
        "\n=== NO ENGINE — FULL LLM (understand question + chart) ===\n"
        f"USER ASKED (lock): {lock[:600]}{scope_line}{div_line}\n"
        "No dedicated engine ran for this question — YOU answer fully.\n"
        "Read the question carefully; answer ONLY what was asked (not a generic lecture).\n"
        "Use chart data for facts; never invent placements, signs, houses, or calendar dates.\n"
        "Warm Hinglish markdown: **The Big Picture** → **Kyun** → **Ab kya karein**.\n"
    )


def no_engine_llm_fallback_eligible(
    question: str,
    llm_intent: dict[str, Any] | None = None,
    *,
    qtype: str = "STATIC",
    checks: dict[str, Any] | None = None,
) -> bool:
    """Always True when no-engine LLM policy is on (see ask_hard_guards.no_engine_llm_enabled)."""
    try:
        from ask_hard_guards import no_engine_llm_enabled

        if no_engine_llm_enabled():
            return bool((question or "").strip())
    except Exception:
        pass
    try:
        from ask_chart_open_qa import open_chart_qa_fallback_eligible

        if open_chart_qa_fallback_eligible(
            question, llm_intent, qtype=qtype, checks=checks,
        ):
            return True
    except Exception:
        pass
    try:
        from ask_hard_guards import universal_chart_llm_fallback_eligible

        return universal_chart_llm_fallback_eligible(
            question, llm_intent, qtype=qtype, checks=checks,
        )
    except Exception:
        pass
    return is_cosmic_domain_concept_question(question, llm_intent)


def build_cosmic_domain_llm_rules(question: str) -> str:
    return build_no_engine_llm_rules(question)


def matches_dedicated_static_engine(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> bool:
    """True when a domain static engine should run — do NOT bypass to direct LLM."""
    q = (question or "").strip()
    if not q:
        return False
    intent = llm_intent if isinstance(llm_intent, dict) else {}
    dom = str(intent.get("routed_domain") or intent.get("domain") or "").strip().lower()
    try:
        from engine_collision_registry import DOMAIN_PRIMARY_ENGINE

        if dom in DOMAIN_PRIMARY_ENGINE:
            return True
    except Exception:
        pass
    _probe: tuple[str, str, bool] = (
        ("ask_marriage_relationship_slice", "is_marriage_relationship_static_question", False),
        ("ask_career.classifier", "is_career_static_question", False),
        ("ask_children.children_registry", "is_children_static_question", False),
        ("ask_health.classifier", "is_health_static_question", False),
        ("ask_finance.finance_registry", "is_finance_static_question", False),
        ("ask_education.education_registry", "is_education_static_question", False),
        ("ask_property.property_registry", "is_property_static_question", False),
        ("ask_vehicle.vehicle_registry", "is_vehicle_static_question", False),
        ("ask_travel.travel_registry", "is_travel_static_question", False),
        ("ask_litigation.litigation_registry", "is_litigation_static_question", False),
        ("ask_luck.luck_registry", "is_luck_static_question", False),
        ("ask_network.network_registry", "is_network_static_question", False),
    )
    for mod_path, fn_name, passes_intent in _probe:
        try:
            import importlib

            fn = getattr(importlib.import_module(mod_path), fn_name)
            if passes_intent:
                if fn(q, intent):
                    return True
            elif fn(q):
                return True
        except Exception:
            continue
    try:
        from ask_gap_dispatch import is_any_gap_static_question

        if is_any_gap_static_question(q, llm_intent=intent):
            return True
    except Exception:
        pass
    return False


def should_bypass_static_engines_for_direct_llm(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Chart/divisional Q with no dedicated engine — skip all static engines → LLM."""
    q = (question or "").strip()
    if not q:
        return False, ""
    if matches_dedicated_static_engine(q, llm_intent):
        return False, ""
    try:
        from chart_fact_answer import (
            _detect_divisional,
            is_pure_chart_fact_lookup,
            needs_llm_chart_answer,
        )

        if is_pure_chart_fact_lookup(q):
            return False, ""
        if _detect_divisional(q):
            return True, "divisional_chart_no_static_engine"
        if needs_llm_chart_answer(q):
            return True, "chart_interpretive_no_static_engine"
    except Exception:
        pass
    dom = str((llm_intent or {}).get("domain") or "").strip().lower()
    if dom == "general":
        try:
            from chart_fact_answer import needs_llm_chart_answer

            if needs_llm_chart_answer(q):
                return True, "general_domain_chart_llm"
        except Exception:
            pass
    return False, ""


def clear_static_engine_flags(flags: dict[str, bool]) -> dict[str, bool]:
    return {k: False for k in (flags or {})}

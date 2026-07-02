"""Cosmic Ask routing policy — engine first, then LLM; off-topic refused.

Order (raw_passthrough):
  1. Scope gate — only jyotish / vastu / numerology / related (no random GK)
  2. Hard guards (death, timing clarify)
  3. Pure chart_fact lookup (placement only, no LLM)
  4. Dedicated engine (static or timing) when matched
  5. No engine → LLM:
       - chart question → open_chart_qa locked facts + LLM
       - in-domain concept (no chart) → LLM from cosmic knowledge + rules
  6. Off-topic / no engine and not in-domain → refuse
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
    r"concept|definition|types?|rules?"
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
    """In-domain education / concept — LLM OK without dedicated engine or chart."""
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


def no_engine_llm_fallback_eligible(
    question: str,
    llm_intent: dict[str, Any] | None = None,
    *,
    qtype: str = "STATIC",
    checks: dict[str, Any] | None = None,
) -> bool:
    """LLM may answer when no domain engine ran."""
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

        if universal_chart_llm_fallback_eligible(
            question, llm_intent, qtype=qtype, checks=checks,
        ):
            return True
    except Exception:
        pass
    return is_cosmic_domain_concept_question(question, llm_intent)


def build_cosmic_domain_llm_rules(question: str) -> str:
    return (
        "\n=== COSMIC DOMAIN (no engine — in-app jyotish/vastu/numerology) ===\n"
        "Answer from established jyotish / vastu / numerology knowledge in plain Hinglish.\n"
        "No invented chart facts — if user needs personal chart, say kundli-based detail chahiye.\n"
        "Stay on topic; refuse off-topic tangents.\n"
        f"USER QUESTION LOCK: {(question or '')[:300]}\n"
    )

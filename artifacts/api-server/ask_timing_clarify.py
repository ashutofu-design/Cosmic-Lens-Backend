"""Deterministic clarifier when a timing question is too vague to pick an engine."""
from __future__ import annotations

import re
from typing import Any, Optional

from ask_question_normalize import prepare_ask_question

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+hoga|kab\s+hogi|kab\s+milega|kab\s+milegi|"
    r"kab\s+lagega|kab\s+lagegi|when|when\s+will|kis\s+(saal|year|mahine|month)|"
    r"kitna\s+time|time\s+lagega|muhurat|timing|dasha|transit|gochar"
    r")\b|(?:कब|कितना\s+समय)"
)

_VAGUE_LIFE_RX = re.compile(
    r"(?ix)\b("
    r"struggle|mushkil|pareshani|pareshaan|dukh|tension|problem|samasya|"
    r"life\s+me|zindagi\s+me|sab\s+theek|set\s+ho\s+jaunga|peace\s+nahi|"
    r"theek\s+hoga|badal\s+jaayega|jaayega|jaayegi|khatam\s+hoga|"
    r"door\s+hogi|kam\s+hogi|mushkilat|pareshani"
    r")\b",
)

_DOMAIN_ANCHOR_RX = re.compile(
    r"(?ix)\b("
    r"job|naukri|career|promotion|office|transfer|business|kaam|"
    r"shaadi|shadi|vivah|marriage|rishta|relationship|biwi|pati|patni|pyaar|love|"
    r"paisa|money|loan|emi|debt|karz|profit|wealth|dhan|"
    r"ghar|flat|plot|property|registry|possession|"
    r"videsh|abroad|visa|travel|settle|"
    r"exam|admission|result|padhai|college|degree|"
    r"bachcha|baby|pregnancy|santan|conceive|"
    r"court|case|bail|verdict|litigation|"
    r"health|sehat|bimari|recovery|surgery|operation|mental|depression|"
    r"guru|deeksha|spiritual|meditation|teerth|occult|jyotish|"
    r"moksha|mukti|liberation|sadhana|dhyan|bhakti|samadhi|"
    r"fame|viral|celebrity|award|recognition|social\s+media|"
    r"dost|friend|network|circle|dushmani|influential|"
    r"lottery|pet|dog|inheritance|virasat|"
    r"theek\s+hoga|recover"
    r")\b",
)

_CLARIFIER_PROMPT = (
    "Kis area ki struggle ki baat kar rahe ho? Timing ke liye mujhe thoda "
    "specific topic chahiye — neeche se choose karo ya apne shabdon me likho:"
)

_TIMING_CLARIFIER_OPTIONS: list[tuple[str, str]] = [
    (
        "career",
        "Career/naukri me struggle kab khatam hogi?",
    ),
    (
        "finance",
        "Paisa/loan ki pareshani kab door hogi?",
    ),
    (
        "marriage",
        "Rishte/shaadi me struggle kab theek hogi?",
    ),
    (
        "health",
        "Sehat/man ki pareshani kab kam hogi?",
    ),
    (
        "love",
        "Pyaar/relationship me struggle kab khatam hogi?",
    ),
]


def has_mapped_timing_domain(
    question: str,
    llm_intent: Optional[dict[str, Any]] = None,
) -> bool:
    """True when a named timing registry owns this Q (skip vague-struggle clarifier)."""
    q = prepare_ask_question((question or "").strip())
    if not q:
        return False
    _checks = (
        ("ask_spiritual.timing_registry", "is_spiritual_timing_question"),
        ("ask_fame.timing_registry", "is_fame_timing_question"),
        ("ask_network.timing_registry", "is_network_timing_question"),
        ("ask_litigation.timing_registry", "is_litigation_timing_question"),
        ("ask_career.timing_registry", "is_career_timing_question"),
        ("ask_love.timing_registry", "is_love_timing_question"),
        ("ask_vehicle.timing_registry", "is_vehicle_timing_question"),
        ("ask_health.timing_registry", "is_health_timing_question"),
        ("ask_property.timing_registry", "is_property_timing_question"),
        ("ask_travel.timing_registry", "is_travel_timing_question"),
        ("ask_finance.timing_registry", "is_finance_timing_question"),
        ("ask_children.timing_registry", "is_children_timing_question"),
        ("ask_education.timing_registry", "is_education_timing_question"),
    )
    for mod_path, fn_name in _checks:
        try:
            mod = __import__(mod_path, fromlist=[fn_name])
            fn = getattr(mod, fn_name)
            if fn(q, llm_intent):
                return True
        except Exception:
            continue
    return False


def needs_timing_domain_clarifier(
    question: str,
    llm_intent: Optional[dict[str, Any]] = None,
) -> bool:
    """True when timing is asked but no domain engine can be chosen safely."""
    q = prepare_ask_question((question or "").strip())
    if not q:
        return False

    try:
        from ask_mr.timing_registry import (
            has_explicit_timing_anchor,
            mr_static_overrides_llm_timing,
        )

        if mr_static_overrides_llm_timing(q, llm_intent):
            return False
        explicit_timing = bool(_TIMING_RX.search(q)) or bool(has_explicit_timing_anchor(q))
    except Exception:
        explicit_timing = bool(_TIMING_RX.search(q))

    # Clarifier only when user actually asked kab/when — not LLM "yog/milega" mis-timing.
    if not explicit_timing:
        return False

    if has_mapped_timing_domain(q, llm_intent):
        return False

    if not _VAGUE_LIFE_RX.search(q):
        return False

    if _DOMAIN_ANCHOR_RX.search(q):
        return False

    # Timing + vague life/struggle wording but no career/marriage/health anchor
    # → must ask user which area (never guess engine from chart-only LLM).
    return True


def maybe_timing_domain_clarifier_result(
    question: str,
    *,
    qtype: str = "TIMING",
    llm_intent: Optional[dict[str, Any]] = None,
    is_timing: bool = False,
) -> Optional[dict[str, Any]]:
    """Return clarifier payload when needed; else None."""
    intent = dict(llm_intent) if isinstance(llm_intent, dict) else {}
    if is_timing:
        intent["is_timing"] = True
    if not needs_timing_domain_clarifier(question, intent or None):
        return None
    return build_timing_domain_clarifier_result(question, qtype=qtype)


def build_timing_domain_clarifier_result(
    question: str,
    *,
    qtype: str = "TIMING",
) -> dict[str, Any]:
    """Ask user which struggle area — no LLM, no engine guess."""
    options = [label for _topic, label in _TIMING_CLARIFIER_OPTIONS]
    return {
        "text": _CLARIFIER_PROMPT,
        "topic": "needs_clarification",
        "question_type": qtype,
        "confidence": 1.0,
        "source": "timing_domain_clarifier",
        "engine_tag": "ans-engine",
        "follow_ups": options[:3],
        "clarification": {
            "prompt": _CLARIFIER_PROMPT,
            "options": options,
        },
    }

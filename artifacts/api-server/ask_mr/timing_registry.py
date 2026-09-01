"""MR static vs love-timing — code overrides LLM is_timing when traits are static."""
from __future__ import annotations

import re
from typing import Any, Optional

try:
    from ask_question_normalize import prepare_ask_question
except Exception:

    def prepare_ask_question(q: str) -> str:  # type: ignore
        return (q or "").strip()

# Outcome/continuation "chalega" (no kab/when) = static prediction, not timing.
_OUTCOME_CHALEGA_STATIC_RX = re.compile(
    r"(?ix)\b("
    r"love\s*life|relationship|rishta|rishte|bond|long[\s-]*term|"
    r"stable|stability|sustain|weak|grow|future|viability|trust|"
    r"distance|online|ldr"
    r")\b"
)

_EXPLICIT_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|when\s+will|"
    r"kis\s+(?:saal|year|mahine|month|din|date)|"
    r"muhurat|timing|dasha|antardasha|mahadasha|transit|gochar|"
    r"kitne\s+saal|date\s+of|"
    r"samay|shubh\s*samay|abhi|chal\s+raha|chalega|"
    r"shubh\s+(?:phase|period|window|time)"
    r")\b"
)

# Legacy broad anchors — do NOT use alone to enable timing (hoga/milega trap).
_BROAD_TIMING_HINT_RX = re.compile(
    r"(?ix)\b(milega|milegi|aayega|aayegi|hoga|hogi)\b"
)

# "hoga kya / kaisa hoga" = trait prediction, not WHEN timing (unless kab also present).
_TRAIT_STATIC_RX = re.compile(
    r"(?ix)\b("
    r"kaisa\s+hoga|kaisi\s+hogi|kaise\s+honge|kaisi\s+rahegi|kaisa\s+rahega|"
    r"dikhne\s+me|dikh\w*\s+me|surat|shakl|good[\s-]?looking|attractive|handsome|beautiful|"
    r"hoga\s+kya|hogi\s+kya|rahega\s+kya|rahegi\s+kya"
    r")\b"
)


def has_explicit_timing_anchor(question: str) -> bool:
    q = prepare_ask_question(question or "")
    if not q:
        return False
    try:
        from ask_love.timing_registry import is_love_static_loyalty_question

        if is_love_static_loyalty_question(q):
            return False
    except Exception:
        pass
    # Chart yog / house analysis ("7th house me yog hai") — not WHEN unless kab/when present.
    if re.search(
        r"(?ix)\b("
        r"yog\s+hai|ka\s+yog|house\s+me|ghar\s+me|"
        r"\d(?:st|nd|rd|th)\s+house|"
        r"sat(?:urn)?\s+mahadasha|rahu|ketu|moon\s+\d"
        r")\b",
        q,
    ) and not re.search(
        r"(?ix)\b(kab|kab\s+tak|when|kis\s+(?:saal|year|mahine|month)|kitne\s+(?:saal|mahine))\b",
        q,
    ):
        return False
    if re.search(r"(?ix)\b(chalega|chalegi)\b", q):
        if not re.search(
            r"(?ix)\b(kab|when|kab\s+tak|kitne\s+(?:saal|mahine))\b",
            q,
        ) and _OUTCOME_CHALEGA_STATIC_RX.search(q):
            return False
    return bool(_EXPLICIT_TIMING_RX.search(q))


def question_requests_timing(
    question: str,
    llm_intent: Optional[dict[str, Any]] = None,
) -> bool:
    """Timing only when kab/when anchor in text, or LLM timing + explicit anchor."""
    q = question or ""
    try:
        if mr_static_overrides_llm_timing(q, llm_intent):
            return False
    except Exception:
        pass
    if has_explicit_timing_anchor(q):
        return True
    if not isinstance(llm_intent, dict) or not llm_intent.get("is_timing"):
        return False
    try:
        from ask_love.timing_registry import llm_says_love_timing

        if llm_says_love_timing(llm_intent):
            return has_explicit_timing_anchor(q)
    except Exception:
        pass
    try:
        from ask_travel.timing_registry import llm_says_travel_timing

        if llm_says_travel_timing(llm_intent):
            return has_explicit_timing_anchor(q)
    except Exception:
        pass
    try:
        from ask_property.timing_registry import llm_says_property_timing

        if llm_says_property_timing(llm_intent):
            return has_explicit_timing_anchor(q)
    except Exception:
        pass
    try:
        from ask_children.timing_registry import llm_says_children_timing

        if llm_says_children_timing(llm_intent):
            return has_explicit_timing_anchor(q)
    except Exception:
        pass
    dom = str(
        llm_intent.get("domain") or llm_intent.get("routed_domain") or ""
    ).strip().lower()
    if dom in ("love", "travel", "property", "children"):
        return has_explicit_timing_anchor(q)
    return False


def clear_timing_without_when_anchor(
    question: str,
    intent: dict[str, Any] | None,
) -> bool:
    """Force is_timing false unless kab/when present. Returns True if repaired."""
    if not isinstance(intent, dict):
        return False
    if question_requests_timing(question, intent):
        return False
    if intent.get("is_timing"):
        intent["is_timing"] = False
        return True
    intent["is_timing"] = False
    return False


def finalize_is_timing_flag(
    question: str,
    is_timing: bool,
    llm_intent: Optional[dict[str, Any]] = None,
) -> bool:
    """Last gate before chart/LLM — no kab/when → never timing."""
    if not question_requests_timing(question, llm_intent):
        if isinstance(llm_intent, dict):
            llm_intent["is_timing"] = False
        return False
    return bool(is_timing)


def is_trait_static_mr_question(question: str) -> bool:
    q = prepare_ask_question(question or "")
    if not q:
        return False
    return bool(_TRAIT_STATIC_RX.search(q))


def is_mr_static_question(question: str) -> bool:
    """True when MR static should run — partner traits, loyalty, appearance, etc."""
    q = prepare_ask_question(question or "")
    if not q:
        return False
    if has_explicit_timing_anchor(q):
        return False
    try:
        from ask_love.timing_registry import is_love_static_loyalty_question

        if is_love_static_loyalty_question(q):
            return True
    except Exception:
        pass
    try:
        from ask_mr.classifier import classify_mr_archetype

        arch = classify_mr_archetype(q)
        if arch and arch != "general_mr":
            return True
    except Exception:
        pass
    try:
        from ask_intent_fidelity import is_partner_relationship_question

        if is_partner_relationship_question(q):
            return True
    except Exception:
        pass
    try:
        from ask_marriage_relationship_slice import is_marriage_relationship_static_question

        if is_marriage_relationship_static_question(q):
            return True
    except Exception:
        pass
    if is_trait_static_mr_question(q) and re.search(
        r"(?ix)\b(partner|spouse|pati|patni|biwi|husband|wife)\b", q
    ):
        return True
    return False


def mr_static_overrides_llm_timing(
    question: str,
    llm_intent: Optional[dict[str, Any]] = None,
) -> bool:
    _ = llm_intent
    return is_mr_static_question(question or "")


def resolve_mr_static_archetype(question: str) -> str | None:
    q = prepare_ask_question(question or "")
    if not q:
        return None
    try:
        from ask_mr.classifier import classify_mr_archetype

        arch = classify_mr_archetype(q)
        return arch if arch else None
    except Exception:
        return None


def repair_llm_intent_mr_static_timing(
    question: str,
    intent: dict[str, Any],
) -> bool:
    """Align is_timing + mr_archetype when MR static wins. Returns True if repaired."""
    if not isinstance(intent, dict):
        return False
    if not mr_static_overrides_llm_timing(question, intent):
        return False
    arch = resolve_mr_static_archetype(question) or str(intent.get("mr_archetype") or "").strip()
    if intent.get("dna_routing_applied"):
        dna_arch = str(
            intent.get("mr_archetype")
            or intent.get("routed_archetype")
            or intent.get("dna_engine_archetype")
            or ""
        ).strip()
        if dna_arch:
            arch = dna_arch
    if not arch:
        arch = "partner_nature"
    intent["is_timing"] = False
    intent["is_decision"] = False
    intent["domain"] = "love"
    intent["mr_archetype"] = arch
    intent.pop("health_archetype", None)
    return True


def is_marriage_timing_question(
    question: str,
    llm_intent: Optional[dict[str, Any]] = None,
) -> bool:
    """Marriage WHEN (shaadi kab) — M17 path, not love timing / MR static."""
    q = prepare_ask_question((question or "").strip())
    if not q:
        return False
    try:
        from ask_marriage_relationship_slice import is_marriage_relationship_static_question

        if is_marriage_relationship_static_question(q) and not has_explicit_timing_anchor(q):
            return False
    except Exception:
        pass
    try:
        from ask_love.timing_registry import _MARRIAGE_OVERRIDE_RX

        if _MARRIAGE_OVERRIDE_RX.search(q):
            return True
    except Exception:
        pass
    if not re.search(
        r"(?ix)\b(shaadi|shadi|marriage|vivah|wedding|biwi|pati|patni)\b|"
        r"(शादी|विवाह|पति|पत्नी)",
        q,
    ):
        return False
    return has_explicit_timing_anchor(q)

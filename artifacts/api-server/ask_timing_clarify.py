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
    r"theek\s+hoga|badal\s+jaayega|khatam\s+hoga|door\s+hogi|kam\s+hogi"
    r")\b",
)

_DOMAIN_ANCHOR_RX = re.compile(
    r"(?ix)\b("
    r"job|naukri|career|promotion|office|transfer|business|kaam|"
    r"shaadi|shadi|vivah|marriage|rishta|biwi|pati|patni|pyaar|love|"
    r"paisa|money|loan|emi|debt|karz|profit|wealth|dhan|"
    r"ghar|flat|plot|property|registry|possession|"
    r"videsh|abroad|visa|travel|settle|"
    r"exam|admission|result|padhai|college|degree|"
    r"bachcha|baby|pregnancy|santan|conceive|"
    r"court|case|bail|verdict|litigation|"
    r"health|sehat|bimari|recovery|surgery|operation|mental|depression|"
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


def needs_timing_domain_clarifier(
    question: str,
    llm_intent: Optional[dict[str, Any]] = None,
) -> bool:
    """True when timing is asked but no domain engine can be chosen safely."""
    q = prepare_ask_question((question or "").strip())
    if not q:
        return False

    is_timing = bool(_TIMING_RX.search(q))
    if isinstance(llm_intent, dict) and llm_intent.get("is_timing"):
        is_timing = True
    if not is_timing:
        return False

    if not _VAGUE_LIFE_RX.search(q):
        return False

    if _DOMAIN_ANCHOR_RX.search(q):
        return False

    try:
        from event_timing.timing_router import resolve_timing_domain

        dom, _bucket, routed_timing = resolve_timing_domain(q, llm_intent)
        if not routed_timing:
            return False
        return dom == "general"
    except Exception:
        return True


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

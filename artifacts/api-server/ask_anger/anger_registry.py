"""Anger / gussa / temperament static scope."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX
from ask_spiritual.spiritual_scope import is_spiritual_topic

ARCHETYPES = frozenset({"anger_temper", "general_anger"})

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"gussa|gusse|anger|angry|temper|rage|chidd|irritat|"
    r"short\s+temper|garam\s+khoon|violent\s+tend"
    r")\b"
)


def is_anger_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q) or TIMING_RX.search(q):
        return False
    if is_spiritual_topic(q):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("anger", "temper") and not llm_intent.get("is_timing"):
            return True
    return True


def detect_anger_archetype(question: str) -> str:
    return "anger_temper"

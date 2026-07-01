"""Charity / daan / punya karma static scope."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX
from ask_spiritual.spiritual_scope import is_spiritual_topic

ARCHETYPES = frozenset({"charity_daan", "punya_karma", "general_charity"})

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"charity|daan|donation|donate|punya|punya\s+karma|seva|philanthrop"
    r")\b"
)
_REMEDY_RX = re.compile(r"(?ix)\b(remedy|ratn|gem|mantra|upay)\b")


def is_charity_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q) or TIMING_RX.search(q):
        return False
    if is_spiritual_topic(q):
        return False
    if _REMEDY_RX.search(q) and not re.search(r"(?ix)\b(daan|charity|donation|punya)\b", q):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("charity", "daan") and not llm_intent.get("is_timing"):
            return True
    return True


def detect_charity_archetype(question: str) -> str:
    q = (question or "").strip()
    if re.search(r"(?ix)\b(punya|karma)\b", q):
        return "punya_karma"
    return "charity_daan"

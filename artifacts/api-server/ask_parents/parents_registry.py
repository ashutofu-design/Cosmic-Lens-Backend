"""Parents / mata-pita static scope (not parent health — see ask_health)."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX

ARCHETYPES = frozenset({"parent_bond", "father_theme", "mother_theme", "general_parents"})

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"parents?|mata|pita|maa|mummy|mom|mother|father|dad|papa|"
    r"mata\s*pita|parents\s*support|ghar\s*wale"
    r")\b"
)
_HEALTH_RX = re.compile(
    r"(?ix)\b(health|sehat|tabiyat|bimari|beemar|bimar|ill|sick|hospital|disease)\b"
)
_FATHER_RX = re.compile(r"(?ix)\b(pita|father|dad|papa)\b")
_MOTHER_RX = re.compile(r"(?ix)\b(mata|maa|mummy|mom|mother)\b")


def is_parents_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q) or TIMING_RX.search(q):
        return False
    if _HEALTH_RX.search(q):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("parents", "family") and not llm_intent.get("is_timing"):
            return True
    return True


def detect_parents_archetype(question: str) -> str:
    q = (question or "").strip()
    if _FATHER_RX.search(q) and not _MOTHER_RX.search(q):
        return "father_theme"
    if _MOTHER_RX.search(q) and not _FATHER_RX.search(q):
        return "mother_theme"
    if re.search(r"(?ix)\b(support|rishta|bond|ladai|blessing)\b", q):
        return "parent_bond"
    return "general_parents"

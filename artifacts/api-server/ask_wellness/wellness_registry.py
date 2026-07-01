"""Food habits / sleep / neend static scope."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX

ARCHETYPES = frozenset({"sleep_neend", "food_habits", "general_wellness"})

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"neend|sleep|insomnia|nind|nightmare\s+sleep|"
    r"food|khana|eating|diet|appetite|digest|pet\s+khana"
    r")\b"
)
_HEALTH_RX = re.compile(r"(?ix)\b(disease|bimari|hospital|doctor|illness)\b")


def is_wellness_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q) or TIMING_RX.search(q):
        return False
    if _HEALTH_RX.search(q):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("wellness", "sleep", "food") and not llm_intent.get("is_timing"):
            return True
    return True


def detect_wellness_archetype(question: str) -> str:
    q = (question or "").strip()
    if re.search(r"(?ix)\b(neend|sleep|insomnia|nind)\b", q):
        return "sleep_neend"
    if re.search(r"(?ix)\b(food|khana|eating|diet|appetite|digest)\b", q):
        return "food_habits"
    return "general_wellness"

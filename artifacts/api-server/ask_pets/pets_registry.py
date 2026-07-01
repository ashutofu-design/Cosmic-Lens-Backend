"""Pets / animals static scope."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX

ARCHETYPES = frozenset({"pet_suitability", "general_pets"})

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"pet|pets|kutta|kutte|billi|cat|dog|puppy|janwar|animal|"
    r"paltu|parrot|bird"
    r")\b"
)


def is_pets_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q) or TIMING_RX.search(q):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("pets", "pet") and not llm_intent.get("is_timing"):
            return True
    return True


def detect_pets_archetype(question: str) -> str:
    q = (question or "").strip()
    if re.search(r"(?ix)\b(rakh|keep|suitable|paal|le\s+lu|lena)\b", q):
        return "pet_suitability"
    return "general_pets"

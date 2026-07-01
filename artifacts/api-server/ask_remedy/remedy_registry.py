"""Remedy / ratn / upay / gemstone static scope."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX

ARCHETYPES = frozenset({"gemstone_ratn", "remedy_upay", "mantra_theme", "general_remedy"})

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"remedy|remedies|upay|upai|ratn|ratna|gemstone|gem|stone|"
    r"mantra|jap|puja|pooja|shanti\s+puja|"
    r"kaun\s+sa\s+ratn|which\s+gem|wear\s+stone"
    r")\b"
)
_CHARITY_ONLY_RX = re.compile(r"(?ix)\b(daan|charity|donation)\b")


def is_remedy_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q) or TIMING_RX.search(q):
        return False
    if _CHARITY_ONLY_RX.search(q) and not re.search(
        r"(?ix)\b(remedy|ratn|gem|mantra|puja|upay)\b", q
    ):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("remedy", "gemstone") and not llm_intent.get("is_timing"):
            return True
    return True


def detect_remedy_archetype(question: str) -> str:
    q = (question or "").strip()
    if re.search(r"(?ix)\b(ratn|ratna|gemstone|gem|stone)\b", q):
        return "gemstone_ratn"
    if re.search(r"(?ix)\b(mantra|jap)\b", q):
        return "mantra_theme"
    if re.search(r"(?ix)\b(upay|remedy|puja|pooja)\b", q):
        return "remedy_upay"
    return "general_remedy"

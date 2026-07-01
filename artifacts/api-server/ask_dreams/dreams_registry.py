"""Dreams / sapne static scope."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX

ARCHETYPES = frozenset({"dream_meaning", "nightmare_theme", "general_dreams"})

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"sapn[ae]|dream|dreams|nightmare|swapn|neend\s+me|sleep\s+dream"
    r")\b"
)


def is_dreams_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q) or TIMING_RX.search(q):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("dreams", "dream") and not llm_intent.get("is_timing"):
            return True
    return True


def detect_dreams_archetype(question: str) -> str:
    q = (question or "").strip()
    if re.search(r"(?ix)\b(nightmare|bura\s+sapna|darawna|afraid)\b", q):
        return "nightmare_theme"
    if re.search(r"(?ix)\b(matlab|meaning|ka\s+matlab|sach)\b", q):
        return "dream_meaning"
    return "general_dreams"

"""Vastu / home direction static scope."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX

ARCHETYPES = frozenset({"vastu_home", "vastu_dosh", "general_vastu"})

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"vastu|vaastu|direction|disha|north\s+facing|south\s+facing|"
    r"east\s+facing|west\s+facing|vastu\s+dosh|energy\s+of\s+home"
    r")\b"
)
_BUY_RX = re.compile(r"(?ix)\b(kharid|buy|purchase|flat|plot|ghar)\b")


def is_vastu_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q) or TIMING_RX.search(q):
        return False
    if _BUY_RX.search(q) and not re.search(r"(?ix)\bvastu\b", q):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("vastu",) and not llm_intent.get("is_timing"):
            return True
    return True


def detect_vastu_archetype(question: str) -> str:
    q = (question or "").strip()
    if re.search(r"(?ix)\b(dosh|problem|rukawat|negative)\b", q):
        return "vastu_dosh"
    return "vastu_home"

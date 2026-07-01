"""General enemies / shatru static (not court litigation, not friend-circle)."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX

ARCHETYPES = frozenset({"enemy_strength", "enemy_harm", "general_enemies"})

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"shatru|shatr|enemy|enemies|dushman|vair|rival|hatred|"
    r"hidden\s+enemy|secret\s+enemy|competitor"
    r")\b"
)
_CIRCLE_RX = re.compile(r"(?ix)\b(circle|dost|friend|network|social)\b")
_COURT_RX = re.compile(r"(?ix)\b(court|case|lawyer|litigation|fir|police\s+case)\b")


def is_enemies_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q) or TIMING_RX.search(q):
        return False
    if _CIRCLE_RX.search(q):
        return False
    if _COURT_RX.search(q):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("enemies", "shatru") and not llm_intent.get("is_timing"):
            return True
    return True


def detect_enemies_archetype(question: str) -> str:
    q = (question or "").strip()
    if re.search(r"(?ix)\b(strong|kamzor|kitne|powerful)\b", q):
        return "enemy_strength"
    if re.search(r"(?ix)\b(nuksan|harm|problem|pareshani)\b", q):
        return "enemy_harm"
    return "general_enemies"

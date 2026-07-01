"""Foreign settlement suitability static (not kab/when)."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX

ARCHETYPES = frozenset({"settlement_suitability", "pr_citizenship_theme", "general_settlement"})

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"settle\s+abroad|settlement|foreign\s+settlement|permanent\s+abroad|"
    r"videsh\s+me\s+bas|videsh\s+basna|videsh\s+me\s+settle|videsh\s+settle|"
    r"abroad\s+life|overseas\s+life|"
    r"pr\b|permanent\s+residen|citizenship|green\s+card|"
    r"foreign\s+citizen|videsh\s+ka\s+naagrik"
    r")\b"
)
_STUDY_RX = re.compile(r"(?ix)\b(study\s+abroad|padhai|college|university|admission)\b")


def is_settlement_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q) or TIMING_RX.search(q):
        return False
    if _STUDY_RX.search(q) and not re.search(r"(?ix)\b(settle|settlement|pr|citizen|basna)\b", q):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("settlement", "foreign_settlement", "immigration") and not llm_intent.get("is_timing"):
            return True
    return True


def detect_settlement_archetype(question: str) -> str:
    q = (question or "").strip()
    if re.search(r"(?ix)\b(pr|citizenship|green\s+card|permanent\s+residen)\b", q):
        return "pr_citizenship_theme"
    if re.search(r"(?ix)\b(suitable|yog|possible|ho\s+sakta|ban\s+sakta)\b", q):
        return "settlement_suitability"
    return "general_settlement"

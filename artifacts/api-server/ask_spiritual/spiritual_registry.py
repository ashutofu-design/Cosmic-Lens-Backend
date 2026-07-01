"""Spiritual / adhyatm / guru static scope (non-timing)."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX

ARCHETYPES = frozenset({
    "spiritual_path",
    "guru_yog",
    "deity_faith",
    "meditation_peace",
    "general_spiritual",
})

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"spiritual|spirituality|adhyatm|adhyatmik|dharma|dharam|moksha|mukti|"
    r"guru|guruji|deeksha|diksha|sadhana|tapasya|meditation|dhyan|bhakti|"
    r"kuldevi|kuldevta|ishta\s+dev|ishta\s+devta|devi|devta|"
    r"occult|mystic|jyotish|mantra|inner\s+peace|shanti|vairagya|"
    r"kundalini|chakra|ketu|12th\s+house|9th\s+house"
    r")\b"
)
_TEERTH_TIMING_RX = re.compile(r"(?ix)\b(teerth|tirth|yatra|pilgrim|kab)\b")


def is_spiritual_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or not _SCOPE_RX.search(q):
        return False
    try:
        from ask_spiritual.timing_registry import is_spiritual_timing_question

        if is_spiritual_timing_question(q, llm_intent):
            return False
    except Exception:
        if TIMING_RX.search(q):
            return False
    if _TEERTH_TIMING_RX.search(q) and TIMING_RX.search(q):
        return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("spiritual", "spirituality", "dharma") and not llm_intent.get("is_timing"):
            return True
    return True


def detect_spiritual_archetype(question: str) -> str:
    q = (question or "").strip()
    if re.search(r"(?ix)\b(kuldevi|kuldevta|ishta\s+dev|devi|devta)\b", q):
        return "deity_faith"
    if re.search(r"(?ix)\b(guru|deeksha|diksha)\b", q):
        return "guru_yog"
    if re.search(r"(?ix)\b(meditation|dhyan|shanti|peace|bechaini)\b", q):
        return "meditation_peace"
    if re.search(r"(?ix)\b(path|yog|moksha|adhyatm)\b", q):
        return "spiritual_path"
    return "general_spiritual"

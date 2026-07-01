"""Spiritual / adhyatm / guru static scope (non-timing)."""

from __future__ import annotations

import re

from ask_gaps_shared import TIMING_RX
from ask_spiritual.spiritual_scope import is_spiritual_topic

ARCHETYPES = frozenset({
    "spiritual_path",
    "guru_yog",
    "deity_faith",
    "meditation_peace",
    "intuition_occult",
    "karma_past_life",
    "moksha_liberation",
    "general_spiritual",
})

_TEERTH_TIMING_RX = re.compile(r"(?ix)\b(teerth|tirth|yatra|pilgrim|kab)\b")


def is_spiritual_static_question(question: str, llm_intent: dict | None = None) -> bool:
    q = (question or "").strip()
    if not q or not is_spiritual_topic(q):
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
    if re.search(
        r"(?ix)\b(karma|karmic|past\s+life|pichle\s+janam|purvajan|pitra|pitru|ancestor|reincarnation)\b",
        q,
    ):
        return "karma_past_life"
    if re.search(
        r"(?ix)\b("
        r"intuition|intuitive|purnanumaan|occult|mystic|tarot|jyotish|astrology|"
        r"psychic|empath|8th\s+house|secret\s+knowledge|hidden\s+knowledge|"
        r"palmistry|numerology|reiki|tantra|prediction|astrologer"
        r")\b",
        q,
    ):
        return "intuition_occult"
    if re.search(r"(?ix)\b(kuldevi|kuldevta|ishta\s+dev|shiv|shiva|krishna|hanuman|bhakti|darshan|bhagwan)\b", q):
        return "deity_faith"
    if re.search(
        r"(?ix)\b(guru|guruji|deeksha|diksha|siddhi|atmakaraka|amatyakaraka|satguru|janeu)\b",
        q,
    ):
        return "guru_yog"
    if re.search(
        r"(?ix)\b(meditation|dhyan|dhyana|shanti|peace|bechaini|anxiety|vipassana|pranayam|sukoon|inner\s+peace)\b",
        q,
    ):
        return "meditation_peace"
    if re.search(r"(?ix)\b(moksha|mukti|sanyas|vairagya|liberation|moksh)\b", q):
        return "moksha_liberation"
    if re.search(
        r"(?ix)\b(awakening|awaken|jagran|jagruti|spiritual\s+path|life\s+purpose|soul\s+mission|transformation)\b",
        q,
    ):
        return "spiritual_path"
    return "general_spiritual"

"""Extract question-writing signals for user Ask profiling (questions only)."""

from __future__ import annotations

import re
from typing import Any

_DEVANAGARI_RX = re.compile(r"[\u0900-\u097F]")
_LATIN_RX = re.compile(r"[A-Za-z]")

_TIMING_RX = re.compile(
    r"(?ix)\b(kab|when|kab\s+tak|kis\s+saal|kitne\s+saal|time|window|period)\b"
)
_WHY_RX = re.compile(r"(?ix)\b(kyun|kyu|why|reason|wajah|kaaran)\b")
_HOW_RX = re.compile(r"(?ix)\b(kaise|how|kese)\b")
_DECISION_RX = re.compile(
    r"(?ix)\b(should\s+i|karun\s+ya|kya\s+karun|job\s+ya|business\s+ya|"
    r"love\s+ya|arrange\s+ya|ya\s+fir)\b"
)
_YESNO_RX = re.compile(
    r"(?ix)\b(hoga\s+ya\s+nahi|hogi\s+ya\s+nahi|milega\s+ya\s+nahi|"
    r"yes\s+or\s+no|haan\s+ya\s+na)\b"
)
_FOLLOWUP_RX = re.compile(
    r"(?ix)\b(aage|agla|uske\s+baad|dusra|next|backup|alternate|aur\s+detail|"
    r"phir\s+se|dobara)\b"
)
_SKEPTIC_RX = re.compile(
    r"(?ix)\b(kaise\s+pata|kaise\s+bataya|sach\s+bol|proof|saboot|"
    r"kya\s+check|how\s+did\s+you\s+know|believe)\b"
)
_EMOTION_ANXIOUS_RX = re.compile(
    r"(?ix)\b(pareshan|tension|dar|afraid|worried|anxiety|umeed\s+nahi|"
    r"hopeless|stress|fear|dukhi|udaas|depressed)\b"
)
_EMOTION_HOPE_RX = re.compile(
    r"(?ix)\b(umeed|hope|positive|accha\s+bata|khush|excited|jaldi)\b"
)
_URGENT_RX = re.compile(
    r"(?ix)\b(jaldi|abhi|turant|urgent|asap|immediately|kitne\s+din)\b"
)
_FORMAL_RX = re.compile(r"(?ix)\b(kripya|please|batayein|bataiye|dhanyavad)\b")
_CASUAL_RX = re.compile(r"(?ix)\b(yaar|bhai|bro|plz|btao|bol\s+de)\b")

_TOPIC_KEYWORDS: dict[str, re.Pattern[str]] = {
    "marriage": re.compile(r"(?ix)\b(shaadi|shadi|marriage|vivah|spouse|husband|wife|pati)\b"),
    "career": re.compile(r"(?ix)\b(career|naukri|job|promotion|business|office)\b"),
    "wealth": re.compile(r"(?ix)\b(paisa|money|wealth|finance|loan|income)\b"),
    "health": re.compile(r"(?ix)\b(health|sehat|bimari|disease|illness)\b"),
    "children": re.compile(r"(?ix)\b(bachcha|child|pregnancy|conceive|santan)\b"),
    "love": re.compile(r"(?ix)\b(love|pyaar|boyfriend|girlfriend|relationship|bf|gf)\b"),
    "property": re.compile(r"(?ix)\b(property|ghar|flat|land|vastu)\b"),
    "travel": re.compile(r"(?ix)\b(travel|abroad|visa|videsh|foreign)\b"),
}


def _word_count(text: str) -> int:
    return len(re.findall(r"[\w\u0900-\u097F]+", text or ""))


def _devanagari_ratio(text: str) -> float:
    if not text:
        return 0.0
    dev = len(_DEVANAGARI_RX.findall(text))
    lat = len(_LATIN_RX.findall(text))
    total = dev + lat
    if total == 0:
        return 0.0
    return round(dev / total, 3)


def _detect_question_types(q: str) -> list[str]:
    types: list[str] = []
    if _TIMING_RX.search(q):
        types.append("timing")
    if _WHY_RX.search(q):
        types.append("why")
    if _HOW_RX.search(q):
        types.append("how")
    if _DECISION_RX.search(q):
        types.append("decision")
    if _YESNO_RX.search(q):
        types.append("yes_no")
    if _FOLLOWUP_RX.search(q):
        types.append("followup")
    if _SKEPTIC_RX.search(q):
        types.append("skeptic")
    if not types:
        types.append("general")
    return types


def _detect_emotion(q: str) -> str:
    if _EMOTION_ANXIOUS_RX.search(q):
        return "anxious"
    if _EMOTION_HOPE_RX.search(q):
        return "hopeful"
    return "neutral"


def _detect_urgency(q: str) -> str:
    return "high" if _URGENT_RX.search(q) else "normal"


def _detect_style(q: str, words: int) -> str:
    if words <= 8:
        return "very_short"
    if words <= 14:
        return "short"
    if words <= 28:
        return "medium"
    return "long"


def _detect_tone(q: str) -> str:
    if _FORMAL_RX.search(q):
        return "formal"
    if _CASUAL_RX.search(q):
        return "casual"
    return "neutral"


def _detect_topics_in_text(q: str) -> list[str]:
    found = [name for name, rx in _TOPIC_KEYWORDS.items() if rx.search(q)]
    return found or []


def extract_question_signals(
    question: str,
    *,
    topic: str = "general",
    answer_source: str | None = None,
) -> dict[str, Any]:
    """Pure function — all signals from question text (+ logged topic)."""
    q = (question or "").strip()
    words = _word_count(q)
    chars = len(q)
    q_lower = q.lower()
    exclam = q.count("!") + q.count("?")
    types = _detect_question_types(q_lower)
    topics_in_q = _detect_topics_in_text(q_lower)
    primary_topic = (topic or "general").strip().lower()
    if primary_topic not in topics_in_q and primary_topic != "general":
        topics_in_q = [primary_topic, *topics_in_q]

    dev_ratio = _devanagari_ratio(q)
    if dev_ratio >= 0.55:
        lang_style = "hindi_heavy"
    elif dev_ratio >= 0.2:
        lang_style = "hinglish"
    else:
        lang_style = "english_heavy"

    return {
        "char_count": chars,
        "word_count": words,
        "style": _detect_style(q, words),
        "tone": _detect_tone(q_lower),
        "lang_style": lang_style,
        "devanagari_ratio": dev_ratio,
        "punctuation_intensity": exclam,
        "question_types": types,
        "emotion": _detect_emotion(q_lower),
        "urgency": _detect_urgency(q_lower),
        "is_skeptic": "skeptic" in types,
        "is_followup": "followup" in types,
        "is_timing": "timing" in types,
        "is_decision": "decision" in types,
        "topics_detected": topics_in_q,
        "logged_topic": primary_topic,
        "has_mera": bool(re.search(r"(?ix)\b(mera|meri|mere|mujhe|my)\b", q_lower)),
        "answer_source": (answer_source or "")[:40],
    }

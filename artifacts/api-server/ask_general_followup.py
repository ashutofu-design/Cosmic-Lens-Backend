"""Generic follow-up helpers — keep the same topic/thread across turns.

Supports Hinglish, English, and Hindi (Devanagari) short follow-ups like
"aur detail do", "tell me more", "और बताओ".
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from ask_question_normalize import prepare_ask_question

# Hinglish + English (Roman script)
_ROMAN_FOLLOWUP_RX = re.compile(
    r"(?ix)\b("
    # more detail / explain
    r"aur\s+(?:thoda\s+)?detail|"
    r"detail\s+m[ae]i?n?\s+batao|"
    r"detail\s+(?:se\s+)?batao|"
    r"aur\s+batao|aur\s+bataiye|"
    r"aur\s+samjha(?:o|iye|na)|"
    r"zyada\s+detail|"
    r"in\s+detail|"
    r"more\s+detail|more\s+details|"
    r"explain\s+more|explain\s+again|"
    r"elaborate|expand|"
    r"tell\s+me\s+more|"
    r"say\s+again|repeat\s+that|"
    r"clarify|clear\s+karo|"
    # again / retry
    r"dobara\s+batao|phir\s+se\s+batao|"
    r"try\s+again|answer\s+again|"
    # not satisfied / unclear
    r"yeh\s+sahi\s+nahi|yeh\s+galat|"
    r"answer\s+sahi\s+nahi|wrong\s+answer|"
    r"not\s+clear|didn['']t\s+understand|don['']t\s+understand|"
    r"samajh\s+nahi\s+aaya|samjh\s+nahi\s+aaya|"
    r"sahi\s+se\s+batao|properly\s+explain|"
    r"not\s+helpful|not\s+satisfied"
    r")\b|"
    r"^\s*(?:aur|phir|dobara|more|again|why|how)\s*\??\s*$"
)

# Hindi (Devanagari) — run on raw text (prepare_ask_question does not romanize)
_DEV_FOLLOWUP_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p) for p in (
        r"और\s*बताओ",
        r"और\s*बताइए",
        r"और\s*विस्तार",
        r"विस्तार\s*से",
        r"विस्तार\s*से\s*बताओ",
        r"फिर\s*से\s*बताओ",
        r"दोबारा\s*बताओ",
        r"समझ\s*नहीं\s*आया",
        r"सही\s*नहीं",
        r"गलत\s*जवाब",
        r"और\s*विवरण",
        r"स्पष्ट\s*कर",
        r"फिर\s*से\s*समझाओ",
    )
)

_TRANSPARENCY_SKIP_RX = re.compile(
    r"(?ix)\b("
    r"kaise\s+(bataya|bata|pata|kaha|bola|nikala|decide|check|maloom)|"
    r"kya\s+(check|dekha|dekhe)|how\s+did\s+you\s+know"
    r")\b|"
    r"कैसे\s*पता|क्या\s*चेक"
)

_VAGUE_PRIOR_RX = re.compile(
    r"(?ix)\b("
    r"mere?\s+(?:bare|baare)\s+(?:me|main)|"
    r"mujhe?\s+(?:baare|bare)\s+(?:me|main)|"
    r"kuch\s+(?:batao|batado|bataiye|bata)|"
    r"life\s+kaisi|kuch\s+achha|something\s+about\s+me|"
    r"tell\s+me\s+about\s+myself|about\s+me"
    r")\b|"
    r"मेरे?\s*बारे\s*में|"
    r"मुझे?\s*बताओ|"
    r"कुछ\s*बताओ"
)


def _normalize_raw(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", (text or "")).split())


def is_generic_followup(question: str) -> bool:
    raw = _normalize_raw(question)
    if not raw:
        return False
    q = prepare_ask_question(raw)
    if _ROMAN_FOLLOWUP_RX.search(q):
        return True
    for rx in _DEV_FOLLOWUP_PATTERNS:
        if rx.search(raw):
            return True
    return False


def extract_prev_user_question(history: Any, current_question: str = "") -> str:
    """Most recent prior USER turn (skip meta/transparency + same-text repeats)."""
    if not isinstance(history, (list, tuple)) or not history:
        return ""
    cur = prepare_ask_question((current_question or "").strip()).lower()
    cur_raw = _normalize_raw(current_question).lower()
    for item in reversed(history):
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        if role not in ("user", "human"):
            continue
        text = str(item.get("text") or item.get("content") or "").strip()
        if not text:
            continue
        norm = prepare_ask_question(text).lower()
        if norm == cur or _normalize_raw(text).lower() == cur_raw:
            continue
        if _TRANSPARENCY_SKIP_RX.search(text):
            continue
        return text
    return ""


def should_skip_general_merge(prev_question: str, current_question: str) -> bool:
    """Avoid attaching to vague priors; avoid cross-domain contamination."""
    cur = prepare_ask_question((current_question or "").strip())
    prv = prepare_ask_question((prev_question or "").strip())
    if not cur or not prv:
        return True
    prv_raw = _normalize_raw(prev_question)
    if _VAGUE_PRIOR_RX.search(prv) or _VAGUE_PRIOR_RX.search(prv_raw):
        return True
    try:
        from ask_intent_fidelity import infer_primary_domain

        cur_dom = infer_primary_domain(cur)
        prv_dom = infer_primary_domain(prv)
        if cur_dom and prv_dom and cur_dom != prv_dom:
            return True
    except Exception:
        pass
    return False


def merge_general_followup_question(prev_question: str, followup: str) -> str:
    p = prepare_ask_question((prev_question or "").strip()) or (prev_question or "").strip()
    f = (followup or "").strip()
    if not p:
        return f
    if not f:
        return p
    # Keep original follow-up wording (Hindi/English) for narrator language cues.
    if f.lower() in p.lower():
        return p
    return f"{p} — user refine: {f}"


def resolve_general_followup_question(question: str, history: Any) -> tuple[str, bool]:
    """Return (effective_question, is_followup)."""
    raw = (question or "").strip()
    if not raw or not is_generic_followup(raw):
        return question, False
    prev = extract_prev_user_question(history, raw)
    if not prev:
        return question, False
    if should_skip_general_merge(prev, raw):
        return question, False
    return merge_general_followup_question(prev, raw), True

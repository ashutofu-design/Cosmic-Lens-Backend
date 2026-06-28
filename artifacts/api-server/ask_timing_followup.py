"""Timing follow-up helpers — refine window / exact month after prior timing answer."""
from __future__ import annotations

import re
from typing import Any

from ask_question_normalize import prepare_ask_question

# "Exact month batao", "kis mahine change hoga" — no mera/meri/career word required.
_TIMING_REFINE_FOLLOWUP_RX = re.compile(
    r"(?ix)"
    r"\b("
    r"exact\s+(month|date|mahina|din|time)|"
    r"precise\s+(month|date|time)|"
    r"kis\s+(mahine|month|saal|date|din)|"
    r"konsa\s+mahina|kaun\s+sa\s+mahina|"
    r"month\s+batao|mahina\s+batao|date\s+batao|"
    r"kitne\s+mahine\s+baad|"
    r"window\s+batao|period\s+batao|timeframe"
    r")\b|"
    r"\b(change|switch|badal|transfer|promotion|job|naukri|career|shaadi|shadi|"
    r"marriage|visa|abroad|exam|result|ghar|property|bail|case)\b"
    r".{0,30}\b(kab|when|hoga|hogi|milega|milegi|aayega|aayegi)\b|"
    r"\b(kab|when)\b.{0,30}\b(change|switch|badal|hoga|hogi|milega|milegi)\b"
)

_TRANSPARENCY_SKIP_RX = re.compile(
    r"(?ix)\b("
    r"kaise\s+(bataya|bata|pata|kaha|bola|nikala|decide|check|maloom)|"
    r"kya\s+(check|dekha|dekhe)|how\s+did\s+you\s+know"
    r")\b"
)

_TIMING_TOPIC_RX = re.compile(
    r"(?ix)\b("
    r"job|naukri|career|promotion|switch|transfer|shaadi|shadi|marriage|"
    r"videsh|abroad|visa|travel|exam|admission|ghar|property|bail|case|"
    r"bachcha|pregnancy|paisa|loan|health|recovery|kab\s+hoga|when\s+will"
    r")\b"
)


def is_timing_refine_followup(question: str) -> bool:
    q = prepare_ask_question((question or "").strip())
    if not q:
        return False
    return bool(_TIMING_REFINE_FOLLOWUP_RX.search(q))


def extract_prev_user_question(history: Any, current_question: str = "") -> str:
    """Most recent prior USER turn that is a real astro ask (not meta follow-up)."""
    if not isinstance(history, (list, tuple)) or not history:
        return ""
    cur = prepare_ask_question((current_question or "").strip()).lower()
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
        if norm == cur:
            continue
        if _TRANSPARENCY_SKIP_RX.search(text):
            continue
        return text
    return ""


def history_has_timing_thread(history: Any) -> bool:
    """True when recent turns discuss a timing/window topic."""
    if not isinstance(history, (list, tuple)):
        return False
    for item in reversed(history[-8:]):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("content") or "")
        if not text:
            continue
        if _TIMING_TOPIC_RX.search(text):
            return True
        low = text.lower()
        if any(k in low for k in ("mahine", "month", "window", "dasha", "4-6", "wait karna")):
            return True
    return False


def merge_timing_followup_question(prev_question: str, refine: str) -> str:
    """Re-run engines on original topic; refine carries the month/window ask."""
    p = prepare_ask_question((prev_question or "").strip())
    r = prepare_ask_question((refine or "").strip())
    if not p:
        return r
    if not r:
        return p
    if r.lower() in p.lower():
        return p
    return f"{p} — user refine: {r}"


_VAGUE_PRIOR_RX = re.compile(
    r"(?ix)\b("
    r"mere?\s+(?:bare|baare)\s+(?:me|main)|"
    r"mujhe?\s+(?:baare|bare)\s+(?:me|main)|"
    r"kuch\s+(?:batao|batado|bataiye|bata)|"
    r"life\s+kaisi|kuch\s+achha|something\s+about\s+me"
    r")\b"
)


def _domain_anchor_hit(question: str) -> bool:
    try:
        from ask_intent_fidelity import infer_primary_domain

        return infer_primary_domain(question) is not None
    except Exception:
        return bool(_TIMING_TOPIC_RX.search(question or ""))


def should_skip_timing_merge(prev_question: str, current_question: str) -> bool:
    """Do not glue a new specific ask onto a vague or different-domain prior turn."""
    cur = prepare_ask_question((current_question or "").strip())
    prv = prepare_ask_question((prev_question or "").strip())
    if not cur or not prv:
        return True
    if _VAGUE_PRIOR_RX.search(prv):
        return True
    try:
        from ask_intent_fidelity import infer_primary_domain

        cur_dom = infer_primary_domain(cur)
        prv_dom = infer_primary_domain(prv)
        if cur_dom and cur_dom != prv_dom:
            return True
        if cur_dom and not prv_dom:
            return True
    except Exception:
        pass
    return False


def resolve_timing_followup_question(
    question: str,
    history: Any,
) -> tuple[str, bool]:
    """Return (effective_question, is_followup)."""
    q = prepare_ask_question((question or "").strip())
    if not q:
        return question, False
    # Only true timing-refine phrases merge with prior turn — never every short reply.
    if not is_timing_refine_followup(q):
        return question, False
    prev = extract_prev_user_question(history, q)
    if not prev:
        return question, False
    if should_skip_timing_merge(prev, q):
        return question, False
    return merge_timing_followup_question(prev, q), True

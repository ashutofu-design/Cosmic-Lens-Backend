"""Known cross-domain keyword collisions — regex must not steal LLM domain."""

from __future__ import annotations

import re

# LLM domain → static engine key (when that domain wins)
DOMAIN_PRIMARY_ENGINE: dict[str, str] = {
    "love": "mr",
    "marriage": "mr",
    "health": "health",
    "career": "career",
    "finance": "finance",
    "education": "education",
    "children": "children",
    "property": "property",
    "vehicle": "vehicle",
    "travel": "travel",
    "litigation": "litigation",
    "luck": "luck",
    "network": "network",
    "friends": "network",
    "social_circle": "network",
}

# When LLM domain is X, these regex-only engines must not run
DOMAIN_MUTEX_CLEAR: dict[str, frozenset[str]] = {
    "love": frozenset({"health", "career", "finance", "education", "property", "vehicle", "travel", "litigation", "luck", "network", "gap"}),
    "marriage": frozenset({"health", "career", "finance", "education", "property", "vehicle", "travel", "litigation", "luck", "network", "gap"}),
    "health": frozenset({"mr", "career", "finance", "education", "property", "vehicle", "travel", "litigation", "luck", "network", "gap"}),
    "career": frozenset({"mr", "health", "children", "property", "vehicle", "travel", "litigation", "luck", "network", "gap"}),
    "finance": frozenset({"mr", "health", "career", "education", "children", "vehicle", "travel", "litigation", "luck", "network", "gap"}),
    "education": frozenset({"mr", "health", "career", "finance", "property", "vehicle", "travel", "litigation", "luck", "network", "gap"}),
    "children": frozenset({"mr", "career", "finance", "education", "property", "vehicle", "travel", "litigation", "luck", "network", "gap"}),
    "property": frozenset({"mr", "health", "career", "finance", "education", "vehicle", "travel", "litigation", "luck", "network", "gap"}),
    "vehicle": frozenset({"mr", "health", "career", "finance", "education", "property", "travel", "litigation", "luck", "network", "gap"}),
    "travel": frozenset({"mr", "health", "career", "finance", "education", "property", "vehicle", "litigation", "luck", "network", "gap"}),
    "litigation": frozenset({"mr", "health", "career", "finance", "education", "property", "vehicle", "travel", "luck", "network", "gap"}),
}

_LOVE_CTX_RX = re.compile(
    r"(?ix)\b(pyaar|pyar|prem|mohabbat|ishq|love|pasand|rishta|partner|crush|"
    r"shaadi|shadi|marriage|boyfriend|girlfriend|husband|wife|bf\b|gf\b)\b"
)


def is_love_relationship_context(text: str) -> bool:
    return bool(_LOVE_CTX_RX.search(text or ""))


def should_suppress_health_for_question(question: str, *, llm_domain: str) -> bool:
    """Emotional 'dil' / love reciprocity — not cardio health."""
    q = (question or "").strip()
    if not q:
        return False
    if llm_domain in ("love", "marriage"):
        return True
    try:
        from ask_health.health_registry import is_love_emotional_dil_question

        if is_love_emotional_dil_question(q):
            return True
    except Exception:
        pass
    if is_love_relationship_context(q) and re.search(
        r"(?ix)\b(dil\s+se|dil\s+me|dil\s+ki|dil\s+lag|jisse\s+pyaar|pyaar\s+karta|"
        r"kya\s+wo\s+bhi|utna\s+hi\s+pyaar)\b",
        q,
    ):
        return True
    return False


def should_force_mr_for_question(question: str, *, llm_domain: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    try:
        from ask_marriage_relationship_slice import is_marriage_relationship_static_question

        is_mr_q = bool(is_marriage_relationship_static_question(q))
    except Exception:
        is_mr_q = is_love_relationship_context(q)
    if llm_domain in ("love", "marriage"):
        return is_mr_q
    try:
        from ask_health.health_registry import is_love_emotional_dil_question

        if is_love_emotional_dil_question(q):
            return is_mr_q
    except Exception:
        pass
    if is_love_relationship_context(q) and re.search(
        r"(?ix)\b(kya\s+wo\s+bhi|utna\s+hi\s+pyaar|dil\s+se)\b",
        q,
    ):
        return is_mr_q
    return False

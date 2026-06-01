"""
AI-only intent routing for legacy ai_ask paths.

Delegates to ask_cosmo.understand_question (single classifier).
No separate regex router and no duplicate mini-LLM call here.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

log = logging.getLogger(__name__)

ROUTES = (
    "simple_fact",
    "dosha_check",
    "transparency",
    "timing",
    "remedy",
    "analysis",
    "general",
    "greeting",
)

_FALLBACK = "analysis"

_CACHE: dict[str, str] = {}
_CACHE_MAX = 512


def _normalize(q: str) -> str:
    return " ".join((q or "").strip().lower().split())[:240]


def _route_from_understanding(u: dict) -> str:
    intent = str(u.get("intent") or "analysis").lower().strip()
    topic = str(u.get("topic") or "general").lower().strip()
    cleaned = str(u.get("cleaned_q") or "").lower()
    subtopic = str(u.get("subtopic") or "").lower()

    if intent == "timing":
        return "timing"
    if intent == "planet":
        return "simple_fact"
    if intent == "problem" and any(
        x in cleaned for x in ("manglik", "dosh", "dosha", "kaal sarp", "pitru")
    ):
        return "dosha_check"
    if any(x in cleaned for x in ("kaise pata", "how do you know", "proof", "source")):
        return "transparency"
    if intent == "decision" and any(
        x in cleaned + subtopic for x in ("upay", "mantra", "jaap", "remedy", "parihara")
    ):
        return "remedy"
    if topic == "general" and intent == "analysis" and any(
        x in cleaned for x in ("kya hota hai", "what is ", "matlab", "meaning")
    ):
        return "general"
    return "analysis"


def classify_intent(
    question: str,
    history: Optional[list] = None,
    client=None,
) -> str:
    q = _normalize(question)
    if not q:
        return _FALLBACK

    if os.environ.get("COSMIC_DISABLE_INTENT_ROUTER", "").strip() == "1":
        return _FALLBACK

    cached = _CACHE.get(q)
    if cached:
        return cached

    try:
        from ask_cosmo import understand_question

        u = understand_question(question, client=client)
        route = _route_from_understanding(u)
        if route not in ROUTES:
            route = _FALLBACK
        if len(_CACHE) >= _CACHE_MAX:
            _CACHE.clear()
        _CACHE[q] = route
        log.info("intent_router(understand_question) %r -> %s", q[:80], route)
        return route
    except Exception as exc:
        log.warning("intent_router failed: %s — fallback %s", exc, _FALLBACK)
        return _FALLBACK

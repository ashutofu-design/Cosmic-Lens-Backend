"""
AI Intent Router for Cosmic Lens.

Replaces brittle regex-based question classification with a tiny
gpt-4o-mini call that classifies each user question into one of a
fixed set of routes. The main answer pipeline then picks the right
prompt template / engine path based on this route.

Routes (8 total):
  simple_fact   — pure chart lookup: rashi/lagna/nakshatra/dasha
  dosha_check   — yes/no dosha question (manglik, kaal sarp, pitru, etc)
  transparency  — "kaise pata / how do you know" follow-ups
  timing        — "kab hogi shaadi/job/promotion" (engine path)
  remedy        — upay / mantra / jaap requests
  analysis      — kyun / kaise / deep interpretation (full pipeline)
  general       — concept / knowledge question, no chart needed
  greeting      — hi / hello / namaste / thanks

Design:
  • SINGLE classifier call, ~200ms latency, ~₹0.01/query
  • Returns a route string, never raises (falls back to "analysis")
  • In-memory cache keyed on (lowercased question) for repeat hits
  • Caller can opt-out via env var COSMIC_DISABLE_INTENT_ROUTER=1
"""

from __future__ import annotations

import logging
import os
from typing import Optional

log = logging.getLogger(__name__)

# Allowed route values — keep in sync with the prompt below and with
# the router branches in openai_helper._build_messages.
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

_FALLBACK = "analysis"  # safest default — full pipeline answers anything

_CACHE: dict[str, str] = {}
_CACHE_MAX = 512

_CLASSIFIER_PROMPT = (
    "You classify a single user question for a Vedic astrology chat app "
    "into EXACTLY ONE route label. Output ONLY the label, nothing else, "
    "no quotes, no explanation.\n\n"
    "ROUTES (pick the SINGLE best match):\n\n"
    "• simple_fact — pure chart lookup; user wants ONE fact about their "
    "own chart (rashi, lagna, ascendant, sun sign, moon sign, nakshatra, "
    "current dasha, mahadasha, antardasha). Short questions like 'mera "
    "rashi kya hai', 'lagna batao', 'kaun sa nakshatra'.\n\n"
    "• dosha_check — yes/no question about a specific dosh in user's own "
    "chart: manglik, kaal sarp, pitru dosh, guru chandal, grahan, "
    "daridra, angarak, shrapit, kemadruma. Examples: 'kya me manglik "
    "hun', 'mujhe kaal sarp dosh hai kya', 'pitru dosh hai mera'.\n\n"
    "• transparency — meta question: how did the system know a chart "
    "fact. Examples: 'tumko kaise pata', 'kaise jaana', 'how do you "
    "know', 'kahan se aaya', 'proof kya hai', 'source kya hai'.\n\n"
    "• timing — 'when' question about a future life event: shaadi/"
    "marriage, job/career change, promotion, baby/child, foreign travel, "
    "house/property, business start, money/wealth gain. Hindi cues: "
    "'kab hogi', 'kab milega', 'kab tak'. English cues: 'when will'.\n\n"
    "• remedy — user explicitly asks for upay, mantra, jaap, ratna/gem, "
    "puja, rudraksha, daan, totka, parihara to fix something.\n\n"
    "• analysis — user wants interpretation, reasoning, personality "
    "reading, relationship/career/health/finance scope, planet effect, "
    "yoga effect, conditional 'agar X hai toh kya'. Generally needs "
    "engine facts + AI interpretation. Default for any chart-based "
    "question that is NOT a pure lookup, dosha check, transparency, "
    "or timing question.\n\n"
    "• general — concept/knowledge question that needs NO personal "
    "chart. Examples: 'manglik kya hota hai', 'rahu ka matlab', "
    "'navagraha kaun se hain', 'difference between rashi and lagna'.\n\n"
    "• greeting — pure social opener with no question: 'hi', 'hello', "
    "'namaste', 'pranam', 'thanks', 'thank you', 'good morning'.\n\n"
    "OUTPUT FORMAT: exactly one of these tokens, lowercase, no quotes:\n"
    "simple_fact | dosha_check | transparency | timing | remedy | "
    "analysis | general | greeting"
)


def _normalize(q: str) -> str:
    return " ".join((q or "").strip().lower().split())[:240]


def classify_intent(
    question: str,
    history: Optional[list] = None,
    client=None,
) -> str:
    """
    Classify a user question into one of the 8 ROUTES.

    Args:
        question: The current user message.
        history: Recent chat turns (used only for short follow-ups).
        client: Optional pre-built OpenAI client. If None, will lazily
                build one via openai_helper._get_client().

    Returns:
        One of ROUTES. On any failure returns _FALLBACK ("analysis").
    """
    q = _normalize(question)
    if not q:
        return _FALLBACK

    # Kill-switch for emergencies / load tests.
    if os.environ.get("COSMIC_DISABLE_INTENT_ROUTER", "").strip() == "1":
        return _FALLBACK

    # Cache hit — same question phrasing was already classified.
    cached = _CACHE.get(q)
    if cached:
        return cached

    # If a follow-up is REALLY short (<= 3 words) and the previous user
    # turn exists, prepend it so the classifier has context. Example:
    # last user said "mera mars kaha hai", now they say "kyun".
    user_msg = question.strip()
    if history and len(question.split()) <= 3:
        prev_user = ""
        for h in reversed(history[-6:]):
            if (h.get("role") == "user") and h.get("content"):
                prev_user = (h.get("content") or "").strip()
                break
        if prev_user:
            user_msg = f"[previous question: {prev_user}]\n[current: {question.strip()}]"

    try:
        if client is None:
            from openai_helper import _get_client  # type: ignore
            client = _get_client()
        if client is None:
            return _FALLBACK

        model = os.environ.get("COSMIC_INTENT_MODEL", "gpt-4o-mini")

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _CLASSIFIER_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.0,
            max_tokens=8,
            timeout=8,
        )
        raw = ""
        try:
            raw = (resp.choices[0].message.content or "").strip().lower()
        except Exception:
            raw = ""

        # Strip stray quotes / punctuation, take first token.
        raw = raw.replace('"', "").replace("'", "").replace("`", "")
        token = raw.split()[0] if raw else ""
        # Some models emit hyphen variants — normalise.
        token = token.replace("-", "_")

        if token in ROUTES:
            _remember(q, token)
            log.info("intent_router classified %r -> %s", q[:80], token)
            return token

        # Soft fuzzy: substring match against route names.
        for r in ROUTES:
            if r in raw:
                _remember(q, r)
                log.info("intent_router fuzzy %r -> %s (raw=%r)", q[:80], r, raw)
                return r

        log.warning("intent_router unknown label %r for %r", raw, q[:80])
        return _FALLBACK
    except Exception as exc:
        log.warning("intent_router failed: %s — falling back to %s", exc, _FALLBACK)
        return _FALLBACK


def _remember(key: str, route: str) -> None:
    if len(_CACHE) >= _CACHE_MAX:
        # Drop one arbitrary entry — simple FIFO-ish behaviour.
        try:
            _CACHE.pop(next(iter(_CACHE)))
        except StopIteration:
            pass
    _CACHE[key] = route

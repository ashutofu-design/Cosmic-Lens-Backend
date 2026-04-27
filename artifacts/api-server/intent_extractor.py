"""
intent_extractor.py — "AI Ear" comprehension layer
====================================================

Reads a user's natural-language astrology question (often vague, story-style,
or multi-intent) and returns a STRUCTURED understanding object that downstream
pipelines (engines, narrator) can consume reliably.

This module is INTENTIONALLY LIGHTWEIGHT and does ZERO astrology reasoning.
It only:
  • detects language (en / hi / hn)
  • detects high-level domain (marriage / stock / love / career / wealth /
    health / general)
  • lists granular intents (max 3) — each with a bucket name and facts
    extracted from the question
  • flags emotional tone (so narrator can soften/strengthen accordingly)
  • flags ask_type (timing / decision / recovery / diagnosis / remedy /
    explanation)
  • returns a confidence score

DESIGN CONSTRAINTS
------------------
- Strict json_schema response (no free text) — model = gpt-4.1-mini
- temperature = 0  — fully deterministic
- 3-second timeout — caller MUST be prepared to fall back to regex routing
- LRU-cached by question text (P5 wires this in)
- Bucket enum is a SUPERSET of all engine bucket names — engines remain the
  source of truth for their own classification; AI Ear is a HINT only

NO FALLBACKS — if OpenAI fails, the function raises IntentExtractionError
and the caller decides whether to fall back to legacy regex routing or
surface the failure.

Brand-safety note: this module NEVER produces user-facing text. Its output
is purely structural metadata.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────────────────────
# BUCKET VOCABULARY  (superset of all engine buckets, kept in sync manually)
# ─────────────────────────────────────────────────────────────────────────────
# Source of truth per engine:
#   marriage_engine    → subtypes: timing | remedy | analysis
#   stock_engine       → real_time | intraday | loss_recovery | career |
#                        partnership | instrument_risk | sector | strategy |
#                        timing | outcome | suitability
#   love_engine        → affair_third_party | breakup_signal | reconciliation |
#                        commitment_fear | one_sided | compatibility |
#                        existing_status | timing | general_love
#   career_engine      → govt_job | foreign_job | promotion | resignation |
#                        business_start | partnership | transfer |
#                        career_setback | new_job_timing | job_change |
#                        career_field_choice | general_career
#   wealth_engine      → salary_growth | business_profit | loan_emi | property |
#                        inheritance | savings_corpus | debt_recovery |
#                        foreign_income | partnership_finance |
#                        sudden_windfall | tax_compliance | general_wealth
#   health_engine      → chronic_illness | acute_illness | surgery_recovery |
#                        mental_health | addiction | parent_health |
#                        reproductive | skin_beauty | longevity |
#                        general_wellness
#
# AI Ear may also propose a few NEW buckets that the wealth engine collapses
# into general_wealth today (per user product spec):
#   wealth_engine new  → expense_leakage | partnership_exit |
#                        business_continuation
#   (these will fall back to general_wealth at the engine until P3 wires them)

DOMAINS = (
    "marriage", "stock", "love", "career", "wealth", "health",
    "remedy", "spiritual", "education", "child", "litigation", "property",
    "vehicle", "vastu", "family", "travel", "general",
)

BUCKETS_BY_DOMAIN: dict[str, tuple[str, ...]] = {
    "marriage": ("timing", "remedy", "analysis", "compatibility", "reconciliation"),
    "stock":    ("real_time", "intraday", "loss_recovery", "career_path",
                 "partnership", "instrument_risk", "sector", "strategy",
                 "timing", "outcome", "suitability"),
    "love":     ("affair_third_party", "breakup_signal", "reconciliation",
                 "commitment_fear", "one_sided", "compatibility",
                 "existing_status", "timing", "general_love"),
    "career":   ("govt_job", "foreign_job", "promotion", "resignation",
                 "business_start", "partnership", "transfer", "career_setback",
                 "new_job_timing", "job_change", "career_field_choice",
                 "general_career"),
    "wealth":   ("salary_growth", "business_profit", "loan_emi", "property",
                 "inheritance", "savings_corpus", "debt_recovery",
                 "foreign_income", "partnership_finance", "sudden_windfall",
                 "tax_compliance", "expense_leakage", "partnership_exit",
                 "business_continuation", "general_wealth"),
    "health":   ("chronic_illness", "acute_illness", "surgery_recovery",
                 "mental_health", "addiction", "parent_health", "reproductive",
                 "skin_beauty", "longevity", "general_wellness"),
    "general":  ("general",),
}

# Flat list for the JSON schema enum (model picks any combination).
ALL_BUCKETS: tuple[str, ...] = tuple(sorted({
    b for buckets in BUCKETS_BY_DOMAIN.values() for b in buckets
}))

ASK_TYPES = (
    "timing",       # "kab hoga"
    "decision",     # "karu ya na karu"
    "recovery",     # "wapas milega"
    "diagnosis",    # "kya chal raha hai"
    "remedy",       # "upay batao"
    "explanation",  # "kp vs vedic kya hai" — concept question
    "outcome",      # "result kya hoga"
    "comparison",   # "X vs Y better"
)

EMOTIONAL_TONES = (
    "anxious", "curious", "desperate", "hopeful", "neutral",
    "conflicted", "grieving", "angry", "skeptical",
)


# ─────────────────────────────────────────────────────────────────────────────
# DATA TYPES
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class IntentFacts:
    """Facts the AI Ear extracts verbatim from the question text — used by
    the narrator to echo user-supplied numbers/dates/people back into the
    answer (mandatory voice rule). All fields are best-effort and may be empty.
    """
    numbers:   list[str] = field(default_factory=list)   # e.g. ["25 lakh", "2 saal"]
    durations: list[str] = field(default_factory=list)   # e.g. ["6 months", "pichle 2 saal"]
    persons:   list[str] = field(default_factory=list)   # e.g. ["partner", "wife", "boss"]
    places:    list[str] = field(default_factory=list)   # e.g. ["bangalore", "abroad"]
    dates:     list[str] = field(default_factory=list)   # e.g. ["jan 2026", "next month"]


@dataclass
class Intent:
    bucket:    str
    facts:     IntentFacts = field(default_factory=IntentFacts)
    summary:   str = ""           # 1-line natural-language paraphrase


@dataclass
class IntentExtraction:
    """Structured output of the AI Ear."""
    language:        str                    # "en" | "hi" | "hn"
    domain:          str                    # one of DOMAINS
    ask_types:       list[str] = field(default_factory=list)
    emotional_tone:  str = "neutral"
    intents:         list[Intent] = field(default_factory=list)
    confidence:      float = 0.0
    latency_ms:      int = 0
    source:          str = "ai_ear"         # "ai_ear" | "regex_fallback"
    raw_question:    str = ""

    def to_log_dict(self) -> dict:
        d = asdict(self)
        # collapse Intent → tight dicts for clean log lines
        d["intents"] = [
            {"bucket": i["bucket"],
             "summary": i.get("summary", ""),
             "facts": {k: v for k, v in i["facts"].items() if v}}
            for i in d["intents"]
        ]
        return d


class IntentExtractionError(RuntimeError):
    """Raised when the AI Ear cannot produce a valid structured extraction
    (model failure, schema violation, or timeout). Caller decides whether to
    fall back to regex routing or surface the failure to the user."""


# ─────────────────────────────────────────────────────────────────────────────
# JSON SCHEMA  (strict — model returns nothing else)
# ─────────────────────────────────────────────────────────────────────────────
_INTENT_SCHEMA = {
    "name": "intent_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "language", "domain", "ask_types", "emotional_tone",
            "intents", "confidence",
        ],
        "properties": {
            "language": {
                "type": "string",
                "enum": ["en", "hi", "hn"],
                "description": "en=English; hi=Hindi (Devanagari); hn=Hinglish (Hindi in Roman script).",
            },
            "domain": {
                "type": "string",
                "enum": list(DOMAINS),
            },
            "ask_types": {
                "type": "array",
                "minItems": 1,
                "maxItems": 4,
                "items": {"type": "string", "enum": list(ASK_TYPES)},
            },
            "emotional_tone": {
                "type": "string",
                "enum": list(EMOTIONAL_TONES),
            },
            "intents": {
                "type": "array",
                "minItems": 1,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["bucket", "summary", "facts"],
                    "properties": {
                        "bucket": {"type": "string", "enum": list(ALL_BUCKETS)},
                        "summary": {
                            "type": "string",
                            "description": "1-line natural-language paraphrase of this intent (≤15 words). Same language as input.",
                        },
                        "facts": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["numbers", "durations", "persons", "places", "dates"],
                            "properties": {
                                "numbers":   {"type": "array", "items": {"type": "string"}, "maxItems": 6},
                                "durations": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
                                "persons":   {"type": "array", "items": {"type": "string"}, "maxItems": 6},
                                "places":    {"type": "array", "items": {"type": "string"}, "maxItems": 6},
                                "dates":     {"type": "array", "items": {"type": "string"}, "maxItems": 6},
                            },
                        },
                    },
                },
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
        },
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT
# ─────────────────────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are an INTENT EXTRACTOR for a Vedic-astrology consultation app. \
Read the user's question (which may be in English, Hindi-Devanagari, or Hinglish — Hindi written in Roman script) \
and produce a STRICT JSON object that classifies what they are asking, NOT an astrology answer.

Rules:
1. LANGUAGE detection — choose ONE:
   - "en" — pure English (no Hindi / Hinglish words at all).
   - "hi" — Hindi written in Devanagari script (e.g. "मेरा प्रमोशन कब होगा").
   - "hn" — Hinglish: ANY Hindi/Urdu word written in Roman script. Treat as "hn" \
if you see ANY of: aaj, aajkal, abhi, hai, hoga, hogi, kab, kaise, kya, kyun, mera, \
meri, nahi, kar, ho raha, chal raha, atka, milega, milegi, batao, chahiye, karu, \
karoon, sahi, theek, accha, achha, wapas, jaldi, thoda, bahut, pichle, baad, alag, \
sab, kuch, sath, paisa, naukri, shaadi, bimar, etc. \
   Default: if mixed Hindi+English in Roman script → "hn", NOT "en".

2. DOMAIN detection — marriage, stock, love, career, wealth, health, remedy, \
spiritual, education, child, litigation, property, vehicle, vastu, family, travel, \
or 'general' (only when no domain clearly applies).

3. ASK_TYPES — what is the user actually asking for? Choose from: \
timing / decision / recovery / diagnosis / remedy / explanation / outcome / comparison. \
One question can have multiple ask_types (e.g. "kab hoga aur kya karu" = [timing, decision]).

4. EMOTIONAL_TONE — choose from: anxious / curious / desperate / hopeful / neutral / \
conflicted / grieving / angry / skeptical. Pick the dominant tone; do not infer beyond \
what the words show. If user uses "atka", "kuch nahi ho raha", "pareshan" → likely "anxious".

5. INTENTS — break the question into up to 3 INTENTS. Each intent has:
   - bucket: the most specific bucket from the allowed enum
   - summary: a ≤15-word paraphrase IN THE SAME LANGUAGE AS THE QUESTION
   - facts: extract VERBATIM strings the user wrote (numbers, durations, persons, \
places, dates). Do NOT invent. If none, return empty arrays.

6. CONFIDENCE: 0.0-1.0. High (>0.8) only when domain + bucket + facts are all clear. \
Low (<0.5) for vague / single-word / off-topic questions.

7. NEVER produce free text outside the JSON schema. NEVER reveal you are an AI.

Bucket selection guide (most specific wins, otherwise general_<domain>):
- 'partnership_exit'     — user is leaving a business partner
- 'expense_leakage'      — kharcha jyada / paisa udta / save nahi ho raha
- 'business_continuation'— akele continue karu / solo entrepreneur
- 'debt_recovery'        — paisa wapas milega / udhaar / loan recovery
- 'breakup_signal'       — relationship ending / alag hone
- 'affair_third_party'   — cheating / dhokha / koi aur
- 'mental_health'        — anxiety / depression / stress / nind nahi aati
- 'general_<domain>'     — fallback when no specific bucket matches
- 'general'              — only when no astrology domain at all (e.g. greetings)

EXAMPLES:
Q: "Aajkal sab kuch atka hua hai, kuch nahi ho raha"
→ language="hn" (Hinglish words: aajkal, atka, ho raha), domain="general", \
ask_types=["diagnosis"], emotional_tone="anxious", \
intents=[{bucket:"general", summary:"Sab kuch atka hua hai, progress nahi"}]

Q: "Mera promotion is saal hoga ya nahi"
→ language="hn", domain="career", ask_types=["timing","outcome"], \
emotional_tone="hopeful", intents=[{bucket:"promotion", \
summary:"Promotion is saal hoga ya nahi", facts:{durations:["is saal"]}}]"""


def _user_prompt(question: str) -> str:
    return f"User question:\n```\n{question.strip()}\n```\n\nReturn ONLY the JSON object."


# ─────────────────────────────────────────────────────────────────────────────
# REGEX FALLBACK (zero-AI safety net used by P5 when AI fails / times out)
# ─────────────────────────────────────────────────────────────────────────────
_LANG_DEV_RX  = re.compile(r"[\u0900-\u097F]")
_HINGLISH_RX  = re.compile(
    r"\b(hai|hain|kya|kaise|kab|kyun|kyu|nahi|nahin|mera|meri|mere|"
    r"karu|karoon|chahiye|batao|bata|jaye|jayega|hoga|hogi|milega|"
    r"sahi|theek|accha|achha|wapis|wapas|abhi|jaldi|thoda|bahut)\b",
    re.IGNORECASE,
)


def _detect_language_regex(question: str) -> str:
    if _LANG_DEV_RX.search(question):
        return "hi"
    if _HINGLISH_RX.search(question):
        return "hn"
    return "en"


def regex_fallback(question: str) -> IntentExtraction:
    """Minimal extraction with NO AI — returns a low-confidence single-intent
    object so the legacy regex pipeline downstream still works. Used by P5
    when AI Ear fails / times out / is disabled."""
    return IntentExtraction(
        language=_detect_language_regex(question),
        domain="general",
        ask_types=["diagnosis"],
        emotional_tone="neutral",
        intents=[Intent(bucket="general", summary=question.strip()[:80])],
        confidence=0.0,
        latency_ms=0,
        source="regex_fallback",
        raw_question=question,
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def extract_intent(question: str,
                   *,
                   timeout_s: float = 15.0,
                   model: Optional[str] = None) -> IntentExtraction:
    """Call the AI Ear and return a parsed IntentExtraction. Raises
    IntentExtractionError on any failure — caller chooses whether to fall
    back via regex_fallback() or to surface the error.
    """
    if not isinstance(question, str) or not question.strip():
        raise IntentExtractionError("empty question")

    # Lazy import to avoid circular dependency with openai_helper.
    try:
        from openai_helper import _get_client  # type: ignore
    except Exception as exc:
        raise IntentExtractionError(f"openai_helper unavailable: {exc}") from exc

    client = _get_client()
    if client is None:
        raise IntentExtractionError("OpenAI client not configured")

    chosen_model = (model
                    or os.environ.get("INTENT_EAR_MODEL")
                    or os.environ.get("OPENAI_MODEL")
                    or "gpt-4.1-mini")

    started = time.time()
    try:
        resp = client.chat.completions.create(
            model=chosen_model,
            temperature=0,
            timeout=timeout_s,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": _user_prompt(question)},
            ],
            response_format={"type": "json_schema", "json_schema": _INTENT_SCHEMA},
        )
    except Exception as exc:
        elapsed = int((time.time() - started) * 1000)
        raise IntentExtractionError(
            f"OpenAI call failed after {elapsed}ms: {type(exc).__name__}: {exc}"
        ) from exc

    elapsed_ms = int((time.time() - started) * 1000)

    try:
        raw_content = (resp.choices[0].message.content or "").strip()
        if not raw_content:
            raise IntentExtractionError("empty response from model")
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise IntentExtractionError(f"invalid JSON: {exc}") from exc
    except Exception as exc:
        raise IntentExtractionError(f"response parse failed: {exc}") from exc

    # Validate + map to dataclass — strict mode means schema is already
    # enforced server-side, but we double-check field presence to fail fast
    # if the schema ever drifts.
    try:
        intents = []
        for it in data.get("intents", []):
            f = it.get("facts", {}) or {}
            intents.append(Intent(
                bucket=it["bucket"],
                summary=it.get("summary", ""),
                facts=IntentFacts(
                    numbers   = list(f.get("numbers",   []) or []),
                    durations = list(f.get("durations", []) or []),
                    persons   = list(f.get("persons",   []) or []),
                    places    = list(f.get("places",    []) or []),
                    dates     = list(f.get("dates",     []) or []),
                ),
            ))

        if not intents:
            raise IntentExtractionError("no intents returned")

        return IntentExtraction(
            language       = data["language"],
            domain         = data["domain"],
            ask_types      = list(data.get("ask_types", []) or []),
            emotional_tone = data.get("emotional_tone", "neutral"),
            intents        = intents,
            confidence     = float(data.get("confidence", 0.0)),
            latency_ms     = elapsed_ms,
            source         = "ai_ear",
            raw_question   = question,
        )
    except KeyError as exc:
        raise IntentExtractionError(f"missing required field {exc}") from exc
    except Exception as exc:
        raise IntentExtractionError(f"validation failed: {exc}") from exc


# ─────────────────────────────────────────────────────────────────────────────
# CACHED ENTRY POINT  (P5 will tune; for P1 we expose a thin LRU wrapper)
# ─────────────────────────────────────────────────────────────────────────────
from functools import lru_cache


@lru_cache(maxsize=1024)
def _cached_extract(normalized_question: str) -> IntentExtraction:
    """Internal cached layer. Key on the normalized question only — facts
    are content-addressed so identical phrasing returns the same object.
    """
    return extract_intent(normalized_question)


def _normalize_question(question: str) -> str:
    """Cheap normalization for cache key: strip + collapse whitespace +
    lowercase. Does NOT strip punctuation — '25 lakh?' and '25 lakh.' may
    have slightly different parses by design."""
    return " ".join(question.strip().lower().split())


def extract_intent_cached(question: str) -> IntentExtraction:
    """Public cached entry point. Returns a deep-copied dataclass so callers
    cannot mutate the cached instance."""
    key = _normalize_question(question)
    if not key:
        raise IntentExtractionError("empty question")
    cached = _cached_extract(key)
    # Return a shallow clone to protect cache from mutation.
    return IntentExtraction(
        language       = cached.language,
        domain         = cached.domain,
        ask_types      = list(cached.ask_types),
        emotional_tone = cached.emotional_tone,
        intents        = [
            Intent(
                bucket=i.bucket,
                summary=i.summary,
                facts=IntentFacts(
                    numbers=list(i.facts.numbers),
                    durations=list(i.facts.durations),
                    persons=list(i.facts.persons),
                    places=list(i.facts.places),
                    dates=list(i.facts.dates),
                ),
            )
            for i in cached.intents
        ],
        confidence  = cached.confidence,
        latency_ms  = cached.latency_ms,
        source      = cached.source,
        raw_question= question,
    )


def cache_clear() -> None:
    _cached_extract.cache_clear()


def cache_info() -> dict:
    info = _cached_extract.cache_info()
    return {
        "hits":     info.hits,
        "misses":   info.misses,
        "currsize": info.currsize,
        "maxsize":  info.maxsize,
    }

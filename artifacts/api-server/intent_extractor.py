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
#   career_timing      → govt_job | foreign_job | promotion | resignation |
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
    "career":   ("govt_job", "promotion", "resignation",
                 "transfer", "career_setback",
                 "job_change", "career_field_choice",
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
# QUESTION SCOPE  (Sprint-25 Fix-E — added to give the supertype router a
# disambiguating signal that captures the *shape* of the ask, not just the
# topic. Maps 1-to-1 to the 5 narrator supertypes downstream.)
# ─────────────────────────────────────────────────────────────────────────────
QUESTION_SCOPES = (
    # ── Chart-inspection family ─────────────────────────────────────────
    "single_planet",          # ONE named planet ("Mars kaisa hai", "Saturn weak hai kya")
                              #   → supertype = PLANET_QUERY
    "multi_planet_or_chart",  # Multiple planets or chart-wide overview
                              # ("kya kya powerful planets", "saare grah strength",
                              #  "mera kundli analysis", "chart mein kya hai",
                              #  "Mars vs Jupiter konsa strong")
                              #   → supertype = GENERAL_ANALYSIS

    # ── Life-area family (a real life domain is the subject) ────────────
    "life_area_problem",      # Distress report — either tied to a specific life area
                              # OR generalized "everything is stuck / nothing is working"
                              # ("paisa nahi ruk raha", "naukri nahi mil rahi",
                              #  "shaadi tut gayi", "tabiyat kharab rehti hai",
                              #  "sab kuch atka hua hai", "kuch bhi sahi nahi ho raha")
                              #   → supertype = PROBLEM_QUERY
    "life_area_timing",       # "kab" question for a life event
                              # ("shaadi kab hogi", "promotion kab milega",
                              #  "ghar kab milega", "loan kab utrega")
                              #   → supertype = TIMING_QUERY
    "life_decision",          # Should I do X or not / X vs Y / kya karu
                              # ("job change karu ya nahi", "ghar khareedu ya rent",
                              #  "is share mein invest karu", "abhi shaadi karu")
                              #   → supertype = DECISION_QUERY
    "life_area_general",      # Open-ended life-area question without distress,
                              # without timing, without decision
                              # ("foreign job ka yog hai kya", "career kaisa rahega",
                              #  "shaadi ka yog hai", "wealth potential batao")
                              #   → supertype = GENERAL_ANALYSIS

    # ── Remedy family ───────────────────────────────────────────────────
    "remedy_request",         # ONLY asking for upay / parihar
                              # ("Saturn ka upay batao", "kya jap karoon")
                              #   → supertype = GENERAL_ANALYSIS

    # ── Off-domain or unclassifiable ────────────────────────────────────
    "off_topic",              # Greeting / non-astrology / out-of-scope
                              #   → caller decides; usually GENERAL_ANALYSIS

    "unknown",                # Model could not classify with confidence
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
    # Sprint-25 Fix-E — captures the SHAPE of the question (not the topic).
    # Maps 1-to-1 to the 5 narrator supertypes downstream. Old extractions
    # default to "unknown" so the supertype router falls back to the
    # ask_types/tone heuristic cleanly.
    question_scope:  str = "unknown"        # one of QUESTION_SCOPES

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
            "language", "domain", "question_scope", "ask_types", "emotional_tone",
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
            "question_scope": {
                "type": "string",
                "enum": list(QUESTION_SCOPES),
                "description": (
                    "The SHAPE of the question (NOT the topic). Pick exactly ONE:\n"
                    " • single_planet — asking about ONE named graha (Mars/Saturn/Rahu/etc.) only\n"
                    " • multi_planet_or_chart — asking about MULTIPLE planets or chart-wide ('kya kya powerful planets', 'all planets', 'kundli analysis', 'Mars vs Jupiter')\n"
                    " • life_area_problem — distress / 'kyon nahi ho raha' in a real life area (paisa/job/shaadi/health)\n"
                    " • life_area_timing — 'kab' question for a life event (shaadi kab, promotion kab)\n"
                    " • life_decision — 'karu ya nahi' / 'X ya Y' decision ask\n"
                    " • life_area_general — open-ended life-area question without distress / timing / decision (foreign job ka yog, career kaisa rahega)\n"
                    " • remedy_request — ONLY asking for upay / parihar\n"
                    " • off_topic — greeting / non-astrology\n"
                    " • unknown — cannot classify with confidence"
                ),
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

3a. QUESTION_SCOPE — pick exactly ONE that captures the SHAPE of the question \
(NOT the topic). This is the MOST IMPORTANT routing signal. Use the decision tree:

   STEP 1: Is the user asking about specific named planets / chart structure?
   - If ONE planet named (Mars/Saturn/Sun/Moon/Mercury/Venus/Jupiter/Rahu/Ketu/lagna lord) \
and the question is about its strength / position / dignity → "single_planet"
   - If MULTIPLE planets, "kya kya / saare / sab / konsa konsa / all" planets, OR \
"chart/kundli mein kya hai", OR "X vs Y compare" between two planets, OR a generic \
"chart analysis / kundli batao" without naming any specific life area → "multi_planet_or_chart"
   - Else continue to STEP 2.

   STEP 2: Is there a specific life area (career/wealth/marriage/health/love/child/etc.) \
OR a generalized distress signal ("sab kuch atka hua", "kuch nahi ho raha", "pareshan")?
   - User reports DISTRESS / "nahi ho raha" / "nahi mil rahi" / "atka hua" / something \
broken — whether tied to a specific area OR general → "life_area_problem"
   - User asks "KAB" / when will this happen → "life_area_timing"
   - User asks "karu ya nahi" / "X ya Y" / should I → "life_decision"
   - User asks "yog hai kya" / "kaisa rahega" / "possibility" / "potential" without \
distress, without timing, without decision → "life_area_general"

   STEP 3: ONLY asking for upay / remedy / parihar → "remedy_request"

   STEP 4: Greeting / non-astrology / cannot tell → "off_topic" or "unknown"

   IMPORTANT: a single named planet inside a multi-area question is still "single_planet" \
ONLY if the WHOLE question is about that planet's strength. \
"Mars career mein kya karega" is "life_area_general" (career), not "single_planet".

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
→ language="hn", domain="general", question_scope="life_area_problem", \
ask_types=["diagnosis"], emotional_tone="anxious", \
intents=[{bucket:"general", summary:"Sab kuch atka hua hai, progress nahi"}]

Q: "Mera promotion is saal hoga ya nahi"
→ language="hn", domain="career", question_scope="life_area_timing", \
ask_types=["timing","outcome"], emotional_tone="hopeful", \
intents=[{bucket:"promotion", summary:"Promotion is saal hoga ya nahi", \
facts:{durations:["is saal"]}}]

Q: "Saturn weak hai ya powerful"
→ language="hn", domain="spiritual", question_scope="single_planet", \
ask_types=["diagnosis","explanation"], emotional_tone="curious", \
intents=[{bucket:"general", summary:"Saturn ki strength batao"}]

Q: "Kya kya powerful planets hain mere chart mein"
→ language="hn", domain="general", question_scope="multi_planet_or_chart", \
ask_types=["diagnosis","explanation"], emotional_tone="curious", \
intents=[{bucket:"general", summary:"Powerful aur weak planets ka overview"}]

Q: "Paisa nahi ruk raha ghar mein"
→ language="hn", domain="wealth", question_scope="life_area_problem", \
ask_types=["diagnosis"], emotional_tone="anxious", \
intents=[{bucket:"expense_leakage", summary:"Paisa save nahi ho raha"}]

Q: "Job change karu ya nahi"
→ language="hn", domain="career", question_scope="life_decision", \
ask_types=["decision"], emotional_tone="conflicted", \
intents=[{bucket:"job_change", summary:"Job change karna chahiye ya nahi"}]

Q: "Saturn ka upay batao"
→ language="hn", domain="remedy", question_scope="remedy_request", \
ask_types=["remedy"], emotional_tone="neutral", \
intents=[{bucket:"general", summary:"Saturn ke liye upay"}]"""


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
        question_scope="unknown",
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
            question_scope = (data.get("question_scope") or "unknown"),
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
        question_scope = getattr(cached, "question_scope", "unknown"),
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

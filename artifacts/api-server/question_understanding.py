"""Sprint-26 — AI-only Question Understanding.

ONE LLM call → {intent, topic, confidence}.
This is the SOLE source of truth for routing every user question.
No regex pipeline, no AI-Ear merge, no multi-source override layers.

Fallback:
    If AI confidence < 0.6 OR the call fails, a minimal regex fires
    purely as a safety-net so the request still lands somewhere sane.

Routing contract:
    intent ∈ {problem, timing, decision, planet, analysis}
    topic  ∈ {finance, career, marriage, love, health, general}

Downstream code maps `intent` → narrator supertype via `supertype_for(intent)`.
Topic carries domain flavour but does NOT pick the engine.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Optional


# ── Allowed values ──────────────────────────────────────────────────────────
INTENTS = ("problem", "timing", "decision", "planet", "analysis")
TOPICS  = ("finance", "career", "marriage", "love", "health", "general")


# ── Prompt ──────────────────────────────────────────────────────────────────
# Sprint-26 base prompt + boundary definitions added after empirical
# evaluation showed the AI confused: (a) planet-status questions naming
# "vargottam"/"exalted"/etc as decisions, (b) "bachhe" (children) as a
# marriage topic, (c) "dosh" (defect) as analysis instead of problem.
# The base structure (input shape, output shape, rules block) is unchanged
# — we only added two short DEFINITIONS sections and three EDGE-CASE
# examples. Output budget (max_tokens=80) is untouched.
_PROMPT_TEMPLATE = (
    "You are a question understanding module.\n\n"
    "Your job is ONLY to understand what the user is asking.\n\n"
    "User question:\n"
    "\"{question}\"\n\n"
    "Return STRICT JSON only:\n\n"
    "{{\n"
    "  \"intent\": \"problem | timing | decision | planet | analysis\",\n"
    "  \"topic\": \"finance | career | marriage | love | health | general\",\n"
    "  \"confidence\": 0.0 to 1.0\n"
    "}}\n\n"
    "INTENT definitions (pick the most specific that fits):\n"
    "- planet   → ANY question that NAMES a graha (Sun, Moon, Mars, Mercury, "
    "Jupiter, Venus, Saturn, Rahu, Ketu / Surya, Chandra, Mangal, Budh, Guru, "
    "Shukra, Shani) — even if phrased as 'X kaisa hai' or 'X mera kaisi hai' "
    "(asking about a single named graha = planet intent, not analysis). "
    "ALSO planet: strong / weak / strongest / weakest / vargottam / exalted "
    "/ debilitated / combust / retrograde status. Words like 'kaunsa planet', "
    "'konsa graha', 'sabse powerful grah' ALWAYS mean planet — NOT decision.\n"
    "- problem  → dosha / dosh / defect / affliction, 'kyun nahi', 'why not', "
    "delay, stuck, suffering, complaint, kharab, bura. 'X dosh hai kya' is "
    "ALWAYS problem — NOT analysis.\n"
    "- timing   → 'when', 'kab', 'kab hoga', 'kitne saal', 'how long', a "
    "future date or period.\n"
    "- decision → 'should I', 'karu ya nahi', 'chahiye', 'sahi hai kya', "
    "choosing between options or asking for a recommendation.\n"
    "- analysis → THREE flavours, all map here:\n"
    "    (a) general overview / lifecycle questions — 'kaisa hai', "
    "'kaisi rahegi', overall theme.\n"
    "    (b) DEFINITIONAL or EXPLANATORY questions — 'X kya hai', "
    "'X ka matlab kya hai', 'X ke baare mein bata', 'X samjhao', "
    "'remedy bata', 'kya farak hai', concept / comparison. CRITICAL: "
    "'X kya hai' / 'what is X' is ALWAYS analysis even when X is a "
    "doshic or problem-flavoured noun (e.g. 'Kaal sarp dosh kya hai', "
    "'Manglik kya hai', 'Pitra dosh kya hai' — all analysis, NOT problem).\n"
    "    (c) CONDITIONAL or IMPLICATION questions — 'X hai to Y ho "
    "jayega?', 'Agar A hai to B hoga?', 'X strong hai to Y automatically "
    "strong?' (even when a graha is named in the condition — the "
    "QUESTION is about the implication, not the planet status).\n"
    "  Also the fallback when none of intent above fits.\n\n"
    "TOPIC definitions (be strict — do NOT bleed across topics):\n"
    "- marriage → ONLY spouse / wedding / partner / vivah / shaadi / "
    "kalatra. Children, parents, family in general → 'general', NOT marriage.\n"
    "- career   → job, business, work, promotion, profession, naukri, kaam.\n"
    "- finance  → money, paisa, wealth, savings, loan, income, dhan.\n"
    "- love     → romantic relationship, girlfriend / boyfriend / crush "
    "(NOT marriage).\n"
    "- health   → illness, body, disease, bimari, sehat.\n"
    "- general  → anything not in the above five (children, parents, life "
    "overview, concepts, planet status without a domain).\n\n"
    "Rules:\n"
    "- Do NOT answer the question\n"
    "- Do NOT explain anything\n"
    "- No extra text, only JSON\n"
    "- Choose the closest intent even if question is vague\n"
    "- Keep it simple and accurate"
)


# ── Minimal regex fallback (only used when AI fails / low conf) ─────────────
# Order matters — first-match wins. Patterns kept short on purpose; this is
# a safety-net, NOT a routing layer.
_FALLBACK_INTENT_RX: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    ("planet",   re.compile(
        r"\b(strong|weak|powerful|kamzor|kamjor|vargottam|"
        r"shakti|balwan|exalt|debilit|planet|grah|graha)\b", re.I)),
    ("timing",   re.compile(
        r"\b(when|kab|kab tak|kitne din|kitne saal|timing|date|year|month|"
        r"saal|mahina|samay)\b", re.I)),
    ("problem",  re.compile(
        r"\b(problem|dosh|dosha|bura|kharab|delay|stuck|why.*not|"
        r"kyun|kyu|nahi ho|nahi mil)\b", re.I)),
    ("decision", re.compile(
        r"\b(should i|kya karu|kya karoon|chahiye|sahi hai|right time|"
        r"karna chahi|sahi rahega)\b", re.I)),
    # 'analysis' is the implicit default
)

_FALLBACK_TOPIC_RX: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    ("marriage", re.compile(
        r"\b(shaadi|shadi|vivah|marriage|spouse|wife|husband|patni|pati)\b", re.I)),
    ("career",   re.compile(
        r"\b(career|naukri|job|business|kaam|work|profession|promotion)\b", re.I)),
    ("finance",  re.compile(
        r"\b(money|paisa|paise|wealth|finance|dhan|loan|kamai|income|salary)\b", re.I)),
    ("health",   re.compile(
        r"\b(health|sehat|swasth|illness|disease|bimari|rog)\b", re.I)),
    ("love",     re.compile(
        r"\b(love|pyaar|pyar|relationship|girlfriend|boyfriend|crush|ishq)\b", re.I)),
)


def _fallback_classify(question: str) -> dict:
    """Last-resort regex classification. Returns confidence=0.5."""
    q = question or ""
    intent = "analysis"
    topic  = "general"
    for name, rx in _FALLBACK_INTENT_RX:
        if rx.search(q):
            intent = name
            break
    for name, rx in _FALLBACK_TOPIC_RX:
        if rx.search(q):
            topic = name
            break
    return {
        "intent":     intent,
        "topic":      topic,
        "confidence": 0.5,
        "source":     "regex_fallback",
    }


# ── Main API ────────────────────────────────────────────────────────────────
def understand_question(question: str,
                        *,
                        client: Any = None,
                        model: Optional[str] = None) -> dict:
    """Single source of truth for question routing.

    Args:
        question: raw user text (1 line to a long paragraph).
        client:   optional pre-built OpenAI client (else we lazy-import).
        model:    optional model override (else env OPENAI_MODEL or 4.1-mini).

    Returns:
        {
          "intent":     one of INTENTS,
          "topic":      one of TOPICS,
          "confidence": float ∈ [0.0, 1.0],
          "source":     "ai" | "ai_low_conf_regex_fallback" |
                        "ai_error_regex_fallback" | "regex_fallback" | "empty",
          "latency_ms": int (when AI was called),
          # plus diagnostic echo when we fell back from AI:
          "ai_intent": ..., "ai_topic": ..., "ai_confidence": ..., "error": ...
        }

    Never raises — the caller can always trust the dict shape.
    """
    q = (question or "").strip()
    if not q:
        return {
            "intent":     "analysis",
            "topic":      "general",
            "confidence": 0.0,
            "source":     "empty",
        }

    if model is None:
        model = os.environ.get("QU_MODEL") or os.environ.get(
            "OPENAI_MODEL", "gpt-4.1-mini")

    # Lazy-import the shared OpenAI client from openai_helper so we don't
    # double-init proxies / API-keys.
    if client is None:
        try:
            from openai_helper import _get_client  # type: ignore
            client = _get_client()
        except Exception:
            client = None

    if client is None:
        return _fallback_classify(q)

    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.1,
            max_tokens=80,
            response_format={"type": "json_object"},
            messages=[
                {"role": "user", "content": _PROMPT_TEMPLATE.format(question=q)}
            ],
        )
        latency_ms = int((time.time() - t0) * 1000)
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)

        intent = (data.get("intent") or "").strip().lower()
        topic  = (data.get("topic")  or "").strip().lower()
        try:
            conf = float(data.get("confidence") or 0.0)
        except (TypeError, ValueError):
            conf = 0.0
        # Clamp
        if conf < 0.0:
            conf = 0.0
        if conf > 1.0:
            conf = 1.0

        # Schema validation — bad enum value = treat as fallback.
        if intent not in INTENTS or topic not in TOPICS:
            fb = _fallback_classify(q)
            fb["source"] = "ai_error_regex_fallback"
            fb["error"] = f"bad enum: intent={intent!r} topic={topic!r}"
            fb["latency_ms"] = latency_ms
            return fb

        # Confidence floor — under 0.6 we still return AI's view but mark it
        # as fallback so any threshold checks downstream can act.
        if conf < 0.6:
            fb = _fallback_classify(q)
            fb["source"] = "ai_low_conf_regex_fallback"
            fb["ai_intent"] = intent
            fb["ai_topic"] = topic
            fb["ai_confidence"] = conf
            fb["latency_ms"] = latency_ms
            return fb

        return {
            "intent":     intent,
            "topic":      topic,
            "confidence": conf,
            "source":     "ai",
            "latency_ms": latency_ms,
        }
    except Exception as exc:
        latency_ms = int((time.time() - t0) * 1000)
        fb = _fallback_classify(q)
        fb["source"] = "ai_error_regex_fallback"
        fb["error"] = str(exc)[:200]
        fb["latency_ms"] = latency_ms
        return fb


# ── intent → narrator supertype mapping ─────────────────────────────────────
# Drives which strict contract block is injected into the system prompt.
# Keys MUST match the canonical supertype identifiers used by
# `_SUPERTYPE_CONTRACT_BLOCKS` and `_validate_supertype_contract` in
# openai_helper.py — i.e. the `*_QUERY` suffix for timing/problem/decision.
_INTENT_TO_SUPERTYPE = {
    "planet":   "STRENGTH_SUMMARY",   # strong/weak/vargottam grounded answer
    "timing":   "TIMING_QUERY",       # when / kab / how-long
    "problem":  "PROBLEM_QUERY",      # dosha / why-not-working
    "decision": "DECISION_QUERY",     # should-I / chahiye / muhurat
    "analysis": "GENERAL_ANALYSIS",   # default narrator
}


def supertype_for(intent: str) -> str:
    """Map AI intent → narrator supertype used by the contract system."""
    return _INTENT_TO_SUPERTYPE.get((intent or "").lower(), "GENERAL_ANALYSIS")

"""
OpenAI helper for Cosmic Lens.

Single entry point: ai_ask(question, kundli, lang, reply_idx) -> dict

The helper builds a domain-locked Vedic astrology prompt, sends the user's
question + their kundli context to OpenAI, and returns a normalised dict
shaped like the rule-based ask_engine output so downstream code does not
need to branch.

Configuration:
- OPENAI_API_KEY  (required)  user-provided secret
- OPENAI_MODEL    (optional)  defaults to "gpt-4o-mini" for cost
- OPENAI_TIMEOUT  (optional)  seconds, defaults to 30
"""

from __future__ import annotations

import json
import os
from typing import Any

# Lazy client so import does not crash if the SDK is missing in dev.
_client = None
_client_err: str | None = None


def _get_client():
    global _client, _client_err
    if _client is not None or _client_err is not None:
        return _client
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        _client_err = "OPENAI_API_KEY missing"
        return None
    try:
        from openai import OpenAI
        timeout = float(os.environ.get("OPENAI_TIMEOUT", "30"))
        _client = OpenAI(api_key=api_key, timeout=timeout)
        return _client
    except Exception as exc:
        _client_err = f"OpenAI SDK init failed: {exc}"
        return None


def is_available() -> bool:
    return _get_client() is not None


# ── Prompt building ───────────────────────────────────────────────────────────

_LANG_NAME = {
    "en": "English", "hi": "Hindi (Devanagari)", "hn": "Hinglish (Hindi in Roman script)",
    "ta": "Tamil", "te": "Telugu", "bn": "Bengali", "mr": "Marathi", "gu": "Gujarati",
    "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi (Gurmukhi)", "or": "Odia",
    "as": "Assamese", "ur": "Urdu", "ne": "Nepali", "sa": "Sanskrit",
    "es": "Spanish", "fr": "French", "de": "German", "pt": "Portuguese",
    "ru": "Russian", "ja": "Japanese", "zh": "Chinese (Simplified)", "ar": "Arabic",
}


def _kundli_summary(kundli: Any) -> str:
    """Compress the kundli dict into a short string the model can use."""
    if not isinstance(kundli, dict):
        return "(no birth chart provided)"
    parts: list[str] = []
    asc = kundli.get("ascendant") or kundli.get("lagna")
    if asc:
        parts.append(f"Lagna: {asc}")
    moon_sign = kundli.get("moonSign") or kundli.get("moon_sign")
    if moon_sign:
        parts.append(f"Moon sign: {moon_sign}")
    nak = kundli.get("nakshatra")
    if nak:
        parts.append(f"Nakshatra: {nak}")
    planets = kundli.get("planets")
    if isinstance(planets, list):
        plist = []
        for p in planets[:9]:
            name  = p.get("name", "")
            sign  = p.get("sign", "")
            house = p.get("house", "")
            retro = " (R)" if p.get("retrograde") else ""
            plist.append(f"{name} in {sign} (H{house}){retro}")
        if plist:
            parts.append("Planets: " + "; ".join(plist))
    return " | ".join(parts) if parts else "(birth chart provided but empty)"


def _build_messages(question: str, kundli: Any, lang: str, reply_idx: int) -> list[dict]:
    lang_name = _LANG_NAME.get(lang, "English")
    chart_str = _kundli_summary(kundli)
    variation = ""
    if reply_idx > 0:
        variation = (
            f" This is reply #{reply_idx + 1} for the same question — give a "
            "different angle or a deeper take, do not repeat the previous wording."
        )

    system = (
        "You are an expert Vedic (Jyotish) astrologer. You ONLY answer questions "
        "related to Vedic astrology, kundli (birth chart) interpretation, planetary "
        "transits, dashas, doshas, remedies, muhurat, gemstones, mantras, and life "
        "guidance grounded in classical Indian astrology (BPHS, Phaladeepika, etc.). "
        "If the user asks something outside this domain, politely steer back to "
        "astrology in one short sentence and suggest an astrology question they can ask. "
        "Never claim to predict exact dates, lottery numbers, or medical/legal outcomes; "
        "always recommend professional advice for serious matters. Keep the tone warm, "
        "respectful, and concise (4–8 short paragraphs max). Use the user's birth chart "
        f"context when relevant. Reply in {lang_name}."
    )

    user = (
        f"Birth chart context:\n{chart_str}\n\n"
        f"User's question:\n{question}\n"
        f"{variation}\n"
        "Return your answer as plain prose (no markdown headings). End with one "
        "short practical remedy or actionable suggestion when appropriate."
    )

    return [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]


# ── Topic classifier (lightweight, keyword-based) ─────────────────────────────

_TOPIC_KW = {
    "marriage":    ["marriage", "shaadi", "spouse", "wife", "husband", "vivah", "partner"],
    "career":      ["career", "job", "naukri", "business", "promotion", "kaam"],
    "finance":     ["money", "wealth", "finance", "paisa", "dhan", "loan", "debt", "investment"],
    "health":      ["health", "illness", "disease", "swasthya", "bimari", "operation"],
    "education":   ["study", "exam", "education", "padhai", "result", "college", "degree"],
    "relationship":["love", "relationship", "girlfriend", "boyfriend", "breakup", "rishta"],
    "travel":      ["travel", "abroad", "videsh", "foreign", "yatra", "visa"],
    "child":       ["child", "santan", "baby", "pregnan", "putra"],
    "remedy":      ["remedy", "upay", "mantra", "puja", "stone", "ratna", "gemstone"],
}


def _classify_topic(question: str) -> str:
    q = (question or "").lower()
    for topic, words in _TOPIC_KW.items():
        if any(w in q for w in words):
            return topic
    return "general"


# ── Public entry point ───────────────────────────────────────────────────────

def ai_ask(question: str, kundli: Any, lang: str = "en", reply_idx: int = 0) -> dict:
    """
    Returns: { text, topic, confidence, source }
    Raises:  RuntimeError on any OpenAI / config failure (caller falls back).
    """
    client = _get_client()
    if client is None:
        raise RuntimeError(_client_err or "OpenAI client not configured")

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    messages = _build_messages(question, kundli, lang, reply_idx)

    try:
        resp = client.chat.completions.create(
            model       = model,
            messages    = messages,
            temperature = 0.8,
            max_tokens  = 700,
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI request failed: {exc}") from exc

    text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    if not text:
        raise RuntimeError("OpenAI returned empty response")

    return {
        "text":       text,
        "topic":      _classify_topic(question),
        "confidence": 0.85,
        "source":     "openai",
    }

"""
Love Compatibility — lightweight AI relationship insight (language layer only).

Scores and astrology reasons are computed deterministically by
``flask_app.love_compatibility``. This module rewrites them into short,
human-readable insight prose. Never invents chart logic.

Toggle: ``LOVE_COMPAT_AI_INSIGHT=1`` (default on when OpenAI is configured)
Model:  ``LOVE_COMPAT_INSIGHT_MODEL`` (default gpt-4o — same tier as Love Reality Pro)
Tokens: ``LOVE_COMPAT_INSIGHT_MAX_TOKENS`` (default 180, hard cap 220)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from collections import OrderedDict
from threading import Lock
from typing import Any

log = logging.getLogger(__name__)

_PROMPT_VERSION = "v3-gpt4o"
_DEFAULT_MODEL = "gpt-4o"
_CACHE_CAP = 512
# Completion budget: target 120–180 tokens; never exceed 220.
_DEFAULT_MAX_TOKENS = 180
_HARD_MAX_TOKENS = 220
# ~4 chars/token → mobile-friendly prose ceiling
_MAX_OUTPUT_CHARS = 900
_cache: OrderedDict[str, str] = OrderedDict()
_cache_lock = Lock()

_NEGATIVE_HINTS = (
    "mismatch", "hostile", "friction", "afflicted", "dusthana", "insecurity",
    "struggles", "distortion", "misunderstanding", "clash", "dosha", "delay",
    "strain", "weak", "challenging", "confusion", "obsession", "detachment",
    "instability", "disappointment", "harsh", "blunt", "risk", "tension",
    "vulnerable", "prosperity strain", "concern",
)
_POSITIVE_HINTS = (
    "harmony", "friendly", "magnetic", "graceful", "clear articulate",
    "nurturing", "durable", "secured", "well-placed", "supporting", "blessings",
    "matched", "strong romantic", "healthy passion", "self-cancels",
    "relationship karma active", "romantic window", "karmic partnership",
    "emotionally grounded", "deep emotional stability", "lasting romantic",
    "polarity chemistry", "warmth in daily",
)

_JARGON_RE = re.compile(
    r"\b("
    r"moon|mars|venus|mercury|jupiter|saturn|rahu|ketu|"
    r"navamsa|d9|d1|dashana|kendra|dusthana|manglik|"
    r"exalted|debilitated|conjunct|trine|aspect(?:s|ing)?|"
    r"\d+(?:st|nd|rd|th)\s+house|house\s+\d+|7th\s+lord|lord\s+of"
    r")\b",
    re.I,
)

_BANNED_PHRASES = (
    "as an ai",
    "it's important to note",
    "in conclusion",
    "remember that",
    "the universe",
    "cosmic alignment",
    "destined soulmates",
    "written in the stars",
    "vibrations",
    "journey together",
)

_SYSTEM = """You are a premium relationship astrologer writing for a mobile couples app.

Rewrite the supplied compatibility FACTS into 2–3 short paragraphs (4 only if essential).

LENGTH (strict)
• Target 120–180 tokens total. Stop when the insight feels complete — do not pad.
• Short sentences. No preamble, no recap, no closing flourish.
• Mobile-friendly: scannable, emotionally intelligent, premium, never rambling.

STYLE
• Psychologically sharp, emotionally real — never cringe, salesy, or generic AI voice.
• Many readers come after breakup, betrayal, or confusion — do not sugarcoat weak charts.
• Relationship-focused: feelings, trust, instability, attachment — not chart mechanics.
• Translate signals into lived experience; never quote technical astrology.
• If score is low: name instability or separation patterns clearly. No fake optimism.

ABSOLUTE RULES
1. Use ONLY facts in the JSON input. Do not invent placements, doshas, planets, or scores.
2. No planet names, house numbers, divisional charts, or jargon
   (no "Moon", "Saturn", "D9", "7th lord", "afflicted", "Navamsa", etc.).
3. Plain paragraphs only — no markdown, bullets, titles, or labels.
4. Separate paragraphs with a single blank line (\\n\\n).
5. Never guarantee outcomes or predict breakup/marriage with certainty."""


def _enabled() -> bool:
    return os.environ.get("LOVE_COMPAT_AI_INSIGHT", "1").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _max_completion_tokens() -> int:
    """Target 120–180; env override clamped to hard cap 220."""
    raw = (os.environ.get("LOVE_COMPAT_INSIGHT_MAX_TOKENS") or "").strip()
    try:
        n = int(raw) if raw else _DEFAULT_MAX_TOKENS
    except ValueError:
        n = _DEFAULT_MAX_TOKENS
    return max(80, min(_HARD_MAX_TOKENS, n))


def _classify_reason(reason: str) -> str:
    low = reason.lower()
    neg = sum(1 for h in _NEGATIVE_HINTS if h in low)
    pos = sum(1 for h in _POSITIVE_HINTS if h in low)
    if neg > pos:
        return "difficult"
    if pos > neg:
        return "positive"
    if any(w in low for w in ("dosha", "afflict", "clash", "strain", "risk", "weak")):
        return "difficult"
    if any(w in low for w in ("harmony", "strong", "support", "blessing", "magnetic")):
        return "positive"
    return "neutral"


def _pick_signals(reasons: list[str], *, kind: str, limit: int = 4) -> list[str]:
    out: list[str] = []
    for r in reasons:
        c = _classify_reason(r)
        if kind == "positive" and c == "positive":
            out.append(r)
        elif kind == "difficult" and c == "difficult":
            out.append(r)
        if len(out) >= limit:
            break
    if len(out) < limit:
        for r in reasons:
            if r in out:
                continue
            c = _classify_reason(r)
            if kind == "positive" and c != "difficult":
                out.append(r)
            elif kind == "difficult" and c == "difficult":
                out.append(r)
            elif kind == "difficult" and c == "neutral" and any(
                w in r.lower() for w in ("dosha", "delay", "friction", "strain")
            ):
                out.append(r)
            if len(out) >= limit:
                break
    return out[:limit]


def _build_payload(
    *,
    score: int,
    breakdown: dict[str, Any],
    reasons: list[str],
) -> dict[str, Any]:
    return {
        "overall_score": score,
        "dimension_scores": {
            "emotional": breakdown.get("emotional"),
            "attraction": breakdown.get("attraction"),
            "communication": breakdown.get("communication"),
            "karmic": breakdown.get("karmic"),
            "stability": breakdown.get("stability"),
            "future_timing": breakdown.get("dasha_transit"),
        },
        "top_positive_signals": _pick_signals(reasons, kind="positive"),
        "top_difficult_signals": _pick_signals(reasons, kind="difficult"),
    }


def _fingerprint(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(f"{_PROMPT_VERSION}|{blob}".encode()).hexdigest()[:24]


def _validate(text: str) -> tuple[bool, str]:
    t = (text or "").strip()
    if len(t) < 80:
        return False, "too_short"
    if len(t) > _MAX_OUTPUT_CHARS:
        return False, "too_long"
    paras = [p.strip() for p in re.split(r"\n\s*\n", t) if p.strip()]
    if len(paras) < 2 or len(paras) > 4:
        return False, "paragraph_count"
    if _JARGON_RE.search(t):
        return False, "jargon"
    low = t.lower()
    for bp in _BANNED_PHRASES:
        if bp in low:
            return False, f"banned:{bp}"
    if re.search(r"^[\s]*[-*•]", t, re.M):
        return False, "markdown_list"
    return True, "ok"


def _sanitize(text: str) -> str:
    t = (text or "").strip()
    t = re.sub(r"^#+\s*", "", t, flags=re.M)
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    if len(t) > _MAX_OUTPUT_CHARS:
        cut = t[:_MAX_OUTPUT_CHARS]
        last_break = cut.rfind("\n\n")
        if last_break > _MAX_OUTPUT_CHARS // 2:
            t = cut[:last_break].strip()
        else:
            t = cut.rsplit(" ", 1)[0].strip()
    return t.strip()


def generate_relationship_insight(
    *,
    score: int,
    breakdown: dict[str, Any],
    reasons: list[str],
) -> str | None:
    """
    Return AI insight prose, or None if disabled/unavailable/invalid (use template fallback).
    Never raises.
    """
    if not _enabled():
        return None

    try:
        payload = _build_payload(score=score, breakdown=breakdown, reasons=reasons)
        key = _fingerprint(payload)

        with _cache_lock:
            if key in _cache:
                return _cache[key]

        try:
            from openai_helper import _get_client  # type: ignore
        except Exception as exc:
            log.warning("[love_compat_insight] openai_helper import failed: %s", exc)
            return None

        client = _get_client()
        if client is None:
            return None

        model = os.environ.get("LOVE_COMPAT_INSIGHT_MODEL", _DEFAULT_MODEL).strip() or _DEFAULT_MODEL
        max_tok = _max_completion_tokens()
        user_content = (
            "Write 2–3 tight relationship insight paragraphs (max ~180 tokens). "
            "Be concise and stop early.\n\n"
            f"<FACTS>\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n</FACTS>"
        )

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": max_tok,
        }
        if not model.lower().startswith("gpt-5"):
            kwargs["temperature"] = 0.55

        resp = client.chat.completions.create(**kwargs)
        raw = _sanitize((resp.choices[0].message.content or "").strip())
        ok, reason = _validate(raw)
        if not ok:
            log.warning("[love_compat_insight] rejected (%s): %.120s", reason, raw)
            return None

        with _cache_lock:
            _cache[key] = raw
            while len(_cache) > _CACHE_CAP:
                _cache.popitem(last=False)

        return raw
    except Exception as exc:
        log.warning("[love_compat_insight] failed: %s", exc)
        return None

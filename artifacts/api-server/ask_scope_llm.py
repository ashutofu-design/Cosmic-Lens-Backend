"""LLM scope classifier — personal astrology vs off-topic / GK.

When regex scope gate cannot confidently allow a question (heavy typos,
mixed Hindi/English/Hinglish), one cheap JSON call decides whether the
user is asking about THEIR chart/life (allow) or something else (block).

Never raises — on failure returns source=llm_unavailable so callers fall
back to the regex verdict unchanged.

Gated by ASK_SCOPE_LLM (default on). Set ASK_SCOPE_LLM=off to disable.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Literal, Optional

ScopeReason = Literal["ok", "off_topic", "general_knowledge", "not_personal"]

_LOW_CONF = 0.62
_TIMEOUT_S = 6

_PROMPT = """You are the scope gate for Cosmic Lens — a Vedic astrology app.
Users type in Hindi, English, or Hinglish, often with spelling mistakes.

Classify the question into exactly ONE category:

1. personal_astro — About THIS user's birth chart or personal life timing/outlook:
   marriage/shaadi, love, career, job, money, health, children, property, travel,
   visa, dasha, planets, houses, lagna, rashi, nakshatra, yog, dosh, remedies,
   muhurat, sade sati, gochar, chart placements, "meri/mera/my" life questions.
   INCLUDE heavily misspelled versions if intent is clearly personal astro.
   Examples: "helth kaisi rahegi", "nokri kb lagegi", "shadi kb hogi",
   "8th house me rahu", "Abhi kaun sa dasha chal raha hai".

2. general_knowledge — Encyclopedia / definition / history, NOT about user's chart:
   "astrology kya hai", "who invented jyotish", "nakshatra ka matlab",
   "what is manglik", "president kaun hai", Wikipedia-style facts.

3. off_topic — Not astrology at all: coding, recipes, sports scores, weather,
   homework, jokes, random chat, shopping, politics news, medical diagnosis
   requests to replace a doctor.

4. greeting — hi, hello, namaste only (no real question).

5. not_personal — Astrology about someone else's chart with no user anchor,
   or too vague to answer ("kuch batao", "life kaisi hai" with zero domain).

Also return "cleaned_question": fix typos and normalize to clear Hinglish/English
(≤20 words). Keep the user's meaning; do not add facts.

Return STRICT JSON only:
{{"category": "personal_astro|general_knowledge|off_topic|greeting|not_personal",
  "cleaned_question": "...",
  "confidence": 0.0-1.0}}

Question: {question}"""


def _scope_llm_mode() -> str:
    return (os.environ.get("ASK_SCOPE_LLM") or "on").strip().lower()


def scope_llm_enabled() -> bool:
    return _scope_llm_mode() not in ("0", "off", "false", "no")


def _error(reason: str, source: str = "llm_error") -> dict:
    return {
        "allowed": False,
        "reason": "not_personal",
        "cleaned_question": "",
        "category": "not_personal",
        "confidence": 0.0,
        "source": source,
        "error": reason[:200],
    }


def _category_to_verdict(category: str) -> tuple[bool, ScopeReason]:
    cat = (category or "").strip().lower()
    if cat in ("personal_astro", "greeting"):
        return True, "ok"
    if cat == "general_knowledge":
        return False, "general_knowledge"
    if cat == "off_topic":
        return False, "off_topic"
    return False, "not_personal"


def classify_ask_scope_llm(
    question: str,
    *,
    client: Any = None,
    model: Optional[str] = None,
) -> dict:
    """Classify scope with one LLM call. Never raises."""
    q = (question or "").strip()
    if not q:
        return _error("empty question", source="llm_unavailable")

    if model is None:
        model = (
            os.environ.get("ASK_SCOPE_MODEL")
            or os.environ.get("ASK_INTENT_MODEL")
            or os.environ.get("QU_MODEL")
            or os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
        )

    if client is None:
        try:
            from openai_helper import _get_client  # type: ignore

            client = _get_client()
        except Exception as exc:
            return _error(f"client import failed: {exc}", source="llm_unavailable")

    if client is None:
        return _error("no OpenAI client", source="llm_unavailable")

    t0 = time.time()
    _create_kwargs = dict(
        model=model,
        temperature=0.0,
        timeout=_TIMEOUT_S,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": _PROMPT.format(question=q)}],
    )
    try:
        try:
            resp = client.chat.completions.create(
                max_completion_tokens=120, **_create_kwargs
            )
        except TypeError:
            resp = client.chat.completions.create(max_tokens=120, **_create_kwargs)
        except Exception as exc:
            _msg = str(exc).lower()
            if ("max_tokens" in _msg and "max_completion_tokens" in _msg) or (
                "use 'max_tokens'" in _msg
            ):
                resp = client.chat.completions.create(max_tokens=120, **_create_kwargs)
            else:
                raise

        latency_ms = int((time.time() - t0) * 1000)
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)
    except Exception as exc:
        fb = _error(str(exc))
        fb["latency_ms"] = int((time.time() - t0) * 1000)
        return fb

    category = str(data.get("category") or "").strip().lower()
    cleaned = str(data.get("cleaned_question") or "").strip()
    try:
        conf = float(data.get("confidence") or 0.0)
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))

    allowed, reason = _category_to_verdict(category)
    source = "llm" if conf >= _LOW_CONF else "llm_low_conf"

    return {
        "allowed": allowed,
        "reason": reason,
        "cleaned_question": cleaned,
        "category": category or "not_personal",
        "confidence": conf,
        "source": source,
        "latency_ms": latency_ms,
    }

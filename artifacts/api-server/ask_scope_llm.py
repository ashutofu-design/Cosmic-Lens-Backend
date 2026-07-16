"""LLM scope classifier — personal cosmic questions vs off-topic / GK.

One cheap JSON call decides whether the user is asking about their chart,
personal life, or spiritual nature. No regex layer interprets question scope.

Never raises — on failure returns source=llm_unavailable so callers can fail
open rather than falsely reject a valid question.

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

DEFAULT: ALLOW (personal_astro) for almost everything related to astrology or life advice.

Classify into exactly ONE category:

1. personal_astro — ALLOW. Any jyotish / cosmic / life question, including:
   kundli, lagna, rashi, gemstone, remedy, dasha, shaadi, career, health, money,
   spirituality, "kisi ka leo lagna pe gemstone", theory like "manglik kya hota hai",
   "astrology kaise kaam karta hai" when user wants practical understanding.
   Examples: "kya me dharmik hun", "leo lagna gemstone", "shadi kab hogi".

2. general_knowledge — Prefer personal_astro instead for astrology topics.
   Only use this for pure encyclopedia unrelated to answering the user in-app
   (e.g. "who is president of india", "wikipedia").

3. off_topic — NOT astrology: coding, recipes, sports scores, weather jokes,
   shopping, politics news, homework with no chart link.

4. greeting — hi, hello, namaste only.

5. not_personal — Almost never. Prefer personal_astro. Use only for empty noise.

Return STRICT JSON only:
{{"category": "personal_astro|general_knowledge|off_topic|greeting|not_personal",
  "cleaned_question": "...",
  "confidence": 0.0-1.0}}

{history}

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


def _history_block(history: Any, max_turns: int = 6) -> str:
    if not isinstance(history, (list, tuple)) or not history:
        return ""
    lines: list[str] = []
    for item in list(history)[-max_turns:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        text = str(item.get("content") or item.get("text") or "").strip()
        if role in ("user", "assistant") and text:
            lines.append(f"{role}: {text[:280]}")
    if not lines:
        return ""
    return "CONVERSATION HISTORY:\n" + "\n".join(lines)


def classify_ask_scope_llm(
    question: str,
    *,
    history: Any = None,
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
        messages=[
            {
                "role": "user",
                "content": _PROMPT.format(
                    question=q,
                    history=_history_block(history),
                ),
            }
        ],
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

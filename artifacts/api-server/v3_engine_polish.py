"""Light 30–40% polish so admin V3 replies feel like Cosmic Intelligence Engine.

Keeps meaning / language / length; removes casual human fillers; slight
analytical tone — never heavy "high English".
"""
from __future__ import annotations

import re
from typing import Any


_SYSTEM = """You are the Cosmic Intelligence Engine text polisher for live chart replies.

Goal: apply ONLY a light 30–40% rewrite so the message feels like a precise
engine output — not a casual human chat — without becoming fancy or academic.

Rules (strict):
1. Keep the SAME language script as the input:
   - Devanagari Hindi → stay Devanagari Hindi
   - Hinglish / Roman Hindi → stay Hinglish
   - English → stay English
2. Keep the SAME meaning, timing, planets, numbers, and verdict. Do NOT add
   new predictions or remove key facts.
3. Keep length within ±20% of the original.
4. Light engine tone only:
   - Trim fillers: yaar, bro, dekho, tension mat lo, don't worry, etc.
   - Slightly clearer / more structured phrasing
   - Prefer calm analytical voice ("dikh raha hai", "signal", "analysis")
5. Do NOT use heavy formal English (no "indicates", "unfold gradually",
   "opportunity remains active", "pursuant", etc.) unless the input was
   already that formal.
6. Never mention AI / LLM / ChatGPT / bot / human admin.
7. Output ONLY the polished reply text — no quotes, no labels, no markdown.
"""


def _looks_devanagari(text: str) -> bool:
    for ch in text or "":
        if "\u0900" <= ch <= "\u097f":
            return True
    return False


def polish_v3_engine_reply(raw: str) -> dict[str, Any]:
    """Return {ok, polished, original, fallback?}."""
    original = (raw or "").strip()
    if not original:
        return {"ok": False, "error": "empty_text"}
    if len(original) > 4000:
        original = original[:4000]

    try:
        from openai_helper import _get_client
    except Exception:
        return {
            "ok": True,
            "polished": original,
            "original": original,
            "fallback": True,
            "error": "openai_import_failed",
        }

    client = _get_client()
    if client is None:
        return {
            "ok": True,
            "polished": original,
            "original": original,
            "fallback": True,
            "error": "openai_unavailable",
        }

    lang_hint = (
        "Input is Devanagari Hindi — polish in Devanagari Hindi only."
        if _looks_devanagari(original)
        else "Keep the same script/language as the input (Hinglish or English)."
    )
    try:
        import os

        model = (
            os.environ.get("V3_POLISH_MODEL")
            or os.environ.get("OPENAI_MODEL")
            or "gpt-4o-mini"
        ).strip()
        resp = client.chat.completions.create(
            model=model,
            temperature=0.35,
            max_tokens=900,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {
                    "role": "user",
                    "content": f"{lang_hint}\n\nAdmin draft to polish:\n{original}",
                },
            ],
        )
        polished = (resp.choices[0].message.content or "").strip()
        polished = polished.strip().strip('"').strip("'").strip()
        # Reject empty / runaway rewrites — fall back to original.
        if not polished:
            polished = original
        elif abs(len(polished) - len(original)) > max(80, int(len(original) * 0.6)):
            # Too aggressive — keep original rather than weird rewrite
            if len(polished) > len(original) * 1.8 or len(polished) < len(original) * 0.4:
                polished = original
        # Strip accidental labels
        polished = re.sub(
            r"^(polished|final|reply|output)\s*[:\-]\s*",
            "",
            polished,
            flags=re.I,
        ).strip()
        return {
            "ok": True,
            "polished": polished or original,
            "original": original,
            "fallback": False,
        }
    except Exception as exc:
        return {
            "ok": True,
            "polished": original,
            "original": original,
            "fallback": True,
            "error": str(exc)[:200],
        }

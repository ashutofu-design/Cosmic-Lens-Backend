"""
narrator_cosmo.hinglishify — zodiac EN→Hinglish scrubber
=========================================================

Phase 2.8.45 — extracted verbatim from openai_helper.py L2491-2568.

When the user asks in Hinglish/Hindi the response should use the Vedic
Sanskrit zodiac names (Mesh / Vrishabh / … / Dhanu / Meen) — NOT the
Western English forms (Aries / Taurus / … / Sagittarius / Pisces). This
applies to ALL paths (single-intent OpenAI, structured wealth cards,
rule-engine fallback) so we run it as a final scrub on the response text.

Public surface:

  _hinglishify_zodiac(text, lang)   — string-level scrub
  hinglishify_response(result, lang) — recursive walk over response payload

  _ZODIAC_EN_TO_HI                  — mapping dict (12 entries)
  _ZODIAC_RX                        — compiled regex matching EN names

The recursive walker covers these payload fields:
  • result["text"]                       — single-shot answer
  • result["cards"][i]["text"]           — multi-intent v2 cards
  • result["cards"][i]["narrative"]      — v2 wealth structured narrative
  • result["cards"][i]["structured"][k]  — empathy_open / human_close /
                                           headline / remedy / note
  • result["cards"][i]["structured"][k]  — what_will_happen / what_to_do /
                                           what_to_avoid (list-of-strings)

All entry points are no-ops when lang ∉ {hn, hi, hinglish} so English-locale
callers get unmodified output. Safe to call with malformed payloads.
"""
from __future__ import annotations

import re

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
_ZODIAC_EN_TO_HI: dict[str, str] = {
    "Aries":       "Mesh",
    "Taurus":      "Vrishabh",
    "Gemini":      "Mithun",
    "Cancer":      "Kark",
    "Leo":         "Simha",
    "Virgo":       "Kanya",
    "Libra":       "Tula",
    "Scorpio":     "Vrishchik",
    "Sagittarius": "Dhanu",
    "Capricorn":   "Makar",
    "Aquarius":    "Kumbh",
    "Pisces":      "Meen",
}
_ZODIAC_RX = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _ZODIAC_EN_TO_HI) + r")\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# STRING-LEVEL SCRUBBER
# ─────────────────────────────────────────────────────────────────────────────
def _hinglishify_zodiac(text: str, lang: str | None) -> str:
    """Replace English zodiac names with Hinglish equivalents in `text`.

    Only fires when the response language is Hinglish (`hn`) or Hindi (`hi`).
    English-locale callers (`en`) get the original Western names. Preserves
    case insensitively (always emits the canonical capitalised Hinglish
    spelling — Cosmic Lens style is title-case for sign names)."""
    if not isinstance(text, str) or not text:
        return text
    eff = (lang or "").strip().lower()
    if eff not in {"hn", "hi", "hinglish"}:
        return text
    def _sub(m):
        key = m.group(1).capitalize()
        return _ZODIAC_EN_TO_HI.get(key, m.group(1))
    return _ZODIAC_RX.sub(_sub, text)


# ─────────────────────────────────────────────────────────────────────────────
# PAYLOAD-LEVEL RECURSIVE WALKER
# ─────────────────────────────────────────────────────────────────────────────
def hinglishify_response(result: dict, lang: str | None) -> dict:
    """Apply `_hinglishify_zodiac` to every user-visible text field on a
    response payload. Mutates and returns the same dict for convenience.

    Covered fields:
      • result["text"]                    — single-shot answer
      • result["cards"][i]["text"]        — multi-intent v2 cards
      • result["cards"][i]["narrative"]   — v2 wealth structured narrative
      • result["cards"][i]["structured"]["empathy_open" | "human_close" |
                                         "headline" | "remedy" | "note" |
                                         "what_will_happen"|"what_to_do"|
                                         "what_to_avoid"]
    Safe to call with non-Hinglish lang (no-op) and with malformed payloads."""
    if not isinstance(result, dict):
        return result
    eff = (lang or "").strip().lower()
    if eff not in {"hn", "hi", "hinglish"}:
        return result
    if isinstance(result.get("text"), str):
        result["text"] = _hinglishify_zodiac(result["text"], eff)
    cards = result.get("cards")
    if isinstance(cards, list):
        for c in cards:
            if not isinstance(c, dict):
                continue
            for k in ("text", "narrative"):
                if isinstance(c.get(k), str):
                    c[k] = _hinglishify_zodiac(c[k], eff)
            s = c.get("structured")
            if isinstance(s, dict):
                for k in ("empathy_open", "human_close", "headline",
                          "remedy", "note"):
                    if isinstance(s.get(k), str):
                        s[k] = _hinglishify_zodiac(s[k], eff)
                for k in ("what_will_happen", "what_to_do", "what_to_avoid"):
                    arr = s.get(k)
                    if isinstance(arr, list):
                        s[k] = [_hinglishify_zodiac(x, eff) if isinstance(x, str) else x
                                for x in arr]
    return result

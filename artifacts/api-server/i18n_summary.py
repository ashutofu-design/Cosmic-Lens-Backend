"""
i18n_summary.py
On-the-fly localization of `*_en` / `*_hi` summary strings produced by
deterministic engines (Business Vastu, Astrovastu Pro) into the user's
selected UI language (24 languages supported by Cosmic Lens mobile).

Strategy:
  - lang == "en"  → copy `*_en` into `*_loc`
  - lang == "hi"  → copy `*_hi` into `*_loc` (fallback to en)
  - lang == "hn"  → translate `*_en` → Hinglish via OpenAI (cached)
  - other 21 langs → translate `*_en` → target lang via OpenAI (cached)

Cache: in-memory thread-safe dict keyed by (lang, sha256(text)). Bounded by
_CACHE_MAX entries; when full, oldest 25% are evicted (FIFO-ish).
Most BV/AVP summary templates recur with only minor f-string variations,
so the cache hit rate is very high after warmup.

Field pairs recognized for auto-localization:
  summary_en  + summary_hi  → summary_loc
  why_en      + why_hi      → why_loc
  reason_en   + reason_hi   → reason_loc
"""

from __future__ import annotations

import hashlib
import os
import threading
from typing import Any, Optional

# ── Language metadata (24 UI languages) ───────────────────────────────────────
LANG_NAMES: dict[str, str] = {
    "en":  "English",
    "hi":  "Hindi (Devanagari script)",
    "hn":  "Hinglish (Hindi vocabulary written in Roman/Latin script using English "
           "letters, e.g. 'Aap ka ghar bahut sundar hai' — common informal style "
           "used in India for SMS/WhatsApp)",
    "bn":  "Bengali",
    "mr":  "Marathi",
    "ta":  "Tamil",
    "te":  "Telugu",
    "gu":  "Gujarati",
    "kn":  "Kannada",
    "ml":  "Malayalam",
    "pa":  "Punjabi (Gurmukhi)",
    "or":  "Odia",
    "as":  "Assamese",
    "zh":  "Chinese (Simplified)",
    "es":  "Spanish",
    "ar":  "Arabic",
    "fr":  "French",
    "pt":  "Portuguese",
    "de":  "German",
    "ru":  "Russian",
    "ja":  "Japanese",
    "id":  "Indonesian",
    "ko":  "Korean",
    "tr":  "Turkish",
}

# ── Translation cache ─────────────────────────────────────────────────────────
_TRANSLATION_CACHE: dict[tuple[str, str], str] = {}
_CACHE_LOCK = threading.Lock()
_CACHE_MAX = 5000


def _cache_key(lang: str, text: str) -> tuple[str, str]:
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return (lang, h)


def _cache_get(lang: str, text: str) -> Optional[str]:
    with _CACHE_LOCK:
        return _TRANSLATION_CACHE.get(_cache_key(lang, text))


def _cache_put(lang: str, text: str, translated: str) -> None:
    with _CACHE_LOCK:
        if len(_TRANSLATION_CACHE) >= _CACHE_MAX:
            # Evict oldest 25% via insertion-order FIFO
            for k in list(_TRANSLATION_CACHE.keys())[: _CACHE_MAX // 4]:
                _TRANSLATION_CACHE.pop(k, None)
        _TRANSLATION_CACHE[_cache_key(lang, text)] = translated


# ── OpenAI translation ───────────────────────────────────────────────────────
def _translate_via_openai(text: str, lang: str) -> Optional[str]:
    """Call OpenAI to translate `text` into `lang`. Returns None on failure."""
    try:
        from openai_helper import _get_client, is_available  # type: ignore
        if not is_available():
            return None
        client = _get_client()
        if client is None:
            return None
    except Exception as exc:
        print(f"[i18n_summary] OpenAI client unavailable: {exc}")
        return None

    target_name = LANG_NAMES.get(lang, lang)

    if lang == "hn":
        prompt = (
            f"Translate the following English text into Hinglish "
            f"(Hindi vocabulary written in Roman/Latin script using English letters, "
            f"e.g. 'Aap ka ghar bahut sundar hai'). "
            f"Keep proper nouns (planet names, Sanskrit/astrology terms in their "
            f"conventional Roman form, directions like NE/SW/N/S/E/W, numbers, dates) "
            f"unchanged. Use natural informal Hinglish.\n\n"
            f"IMPORTANT: Output ONLY the translated text — no quotes, no labels, "
            f"no explanations, no preamble.\n\nText to translate:\n{text}"
        )
    else:
        prompt = (
            f"Translate the following English text into {target_name}. "
            f"Keep proper nouns (planet names, Sanskrit/astrology terms in their "
            f"conventional form, directions like NE/SW/N/S/E/W, numbers, dates) "
            f"unchanged. Use natural, fluent {target_name}.\n\n"
            f"IMPORTANT: Output ONLY the translated text — no quotes, no labels, "
            f"no explanations, no preamble.\n\nText to translate:\n{text}"
        )

    try:
        model = os.environ.get("COSMIC_TRANSLATE_MODEL", "gpt-4o-mini")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1024,
        )
        out = (resp.choices[0].message.content or "").strip()
        # Strip stray surrounding quotes the model sometimes adds
        if len(out) >= 2 and out[0] in ('"', "'") and out[-1] == out[0]:
            out = out[1:-1].strip()
        return out or None
    except Exception as exc:
        print(f"[i18n_summary] OpenAI translate failed lang={lang}: {exc}")
        return None


# ── Public API ───────────────────────────────────────────────────────────────
def localize_text(en: str, hi: Optional[str], lang: str) -> str:
    """Return `en`/`hi` directly for those langs, else translate `en` via OpenAI.
    Cached. Falls back gracefully to `en` on error.
    """
    if not en:
        return en or ""
    lang = (lang or "en").strip().lower()

    if lang == "en":
        return en
    if lang == "hi":
        return hi if (isinstance(hi, str) and hi) else en
    if lang not in LANG_NAMES:
        return en  # unknown lang → English fallback

    cached = _cache_get(lang, en)
    if cached is not None:
        return cached

    translated = _translate_via_openai(en, lang)
    if translated is None:
        # Hard fallback: prefer hi for Indic langs, else en
        return hi if (isinstance(hi, str) and hi) else en

    _cache_put(lang, en, translated)
    return translated


# Field pairs recognized for auto-localization
_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("summary_en", "summary_hi", "summary_loc"),
    ("why_en",     "why_hi",     "why_loc"),
    ("reason_en",  "reason_hi",  "reason_loc"),
)


def localize_response(obj: Any, lang: str) -> Any:
    """Recursively walk `obj`; for any dict containing a recognized `*_en` key,
    add a `*_loc` field with the value localized to `lang`.

    Mutates dicts in place AND returns `obj` for convenience.
    Handles arbitrary nesting (dict/list).
    """
    if obj is None:
        return obj
    lang = (lang or "en").strip().lower()

    if isinstance(obj, dict):
        for en_key, hi_key, loc_key in _PAIRS:
            if en_key in obj and loc_key not in obj:
                en_val = obj.get(en_key)
                hi_val = obj.get(hi_key)
                if isinstance(en_val, str) and en_val:
                    obj[loc_key] = localize_text(
                        en_val,
                        hi_val if isinstance(hi_val, str) else None,
                        lang,
                    )
        for v in obj.values():
            localize_response(v, lang)
    elif isinstance(obj, list):
        for item in obj:
            localize_response(item, lang)

    return obj

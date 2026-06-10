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
import re
import threading
from typing import Any, Optional

# ── Language metadata (English, Hinglish, Hindi only) ─────────────────────────
LANG_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi (Devanagari script)",
    "hn": (
        "Hinglish (Hindi vocabulary written in Roman/Latin script using English "
        "letters, e.g. 'Aap ka ghar bahut sundar hai' — common informal style "
        "used in India for SMS/WhatsApp)"
    ),
}


def coerce_lang(lang: str | None) -> str:
    from app_lang import coerce_app_lang

    return coerce_app_lang(lang)

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


def devanagari_char_count(text: str) -> int:
    return len(re.findall(r"[\u0900-\u097F]", text or ""))


def prose_fully_hindi(text: str) -> bool:
    """True when paragraph is mostly Devanagari (not just 6 stray chars + English)."""
    t = (text or "").strip()
    if len(t) < 16:
        return False
    deva = devanagari_char_count(t)
    if deva < 12:
        return False
    letters = len(re.findall(r"[A-Za-z\u0900-\u097F]", t))
    if letters < 20:
        return deva >= 8
    return (deva / letters) >= 0.32


def prose_fully_hinglish(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 20:
        return False
    if devanagari_char_count(t) >= 8:
        return False
    return bool(re.search(
        r"\b(aap|rishte|kya|hai|hain|nahi|pyar|saath|dono|yeh|aur|mein|main|upay)\b",
        t,
        re.I,
    ))


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
    elif lang == "hi":
        prompt = (
            "Translate the following English text into natural Hindi written in "
            "Devanagari script (देवनागरी). Do NOT use Roman/Latin letters for Hindi "
            "words — partner names, scores, and graha names may stay in Latin.\n"
            "Keep proper nouns (planet names, Sanskrit/astrology terms in their "
            "conventional form, directions like NE/SW/N/S/E/W, numbers, dates) "
            "unchanged. Use fluent, conversational Hindi.\n"
            "Preserve paragraph breaks (blank lines between paragraphs).\n"
            "Do NOT convert prose into bullet lists or one-fact-per-line points.\n\n"
            "IMPORTANT: Output ONLY the translated text — no quotes, no labels, "
            "no explanations, no preamble.\n\nText to translate:\n"
            f"{text}"
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
        if len(text) > 2000:
            max_tokens = 4096
        elif len(text) > 500:
            max_tokens = 2048
        else:
            max_tokens = 1024
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=max_tokens,
        )
        out = (resp.choices[0].message.content or "").strip()
        # Strip stray surrounding quotes the model sometimes adds
        if len(out) >= 2 and out[0] in ('"', "'") and out[-1] == out[0]:
            out = out[1:-1].strip()
        return out or None
    except Exception as exc:
        print(f"[i18n_summary] OpenAI translate failed lang={lang}: {exc}")
        return None


def localize_text_force(text: str, lang: str) -> str:
    """Always translate mixed/partial English — used after LLM for Love Reality hi/hn."""
    raw = (text or "").strip()
    if not raw:
        return text or ""
    lang = coerce_lang(lang)
    if lang == "en":
        return raw
    if lang == "hi" and prose_fully_hindi(raw):
        return raw
    if lang == "hn" and prose_fully_hinglish(raw):
        return raw
    translated = _translate_via_openai(raw, lang)
    if translated and len(translated.strip()) >= max(12, len(raw) // 4):
        _cache_put(lang, raw, translated)
        return translated
    return raw


# ── Public API ───────────────────────────────────────────────────────────────
def localize_text(en: str, hi: Optional[str], lang: str) -> str:
    """Return `en`/`hi` directly for those langs, else translate `en` via OpenAI.
    Cached. Falls back gracefully to `en` on error.
    """
    if not en:
        return en or ""
    lang = (lang or "en").strip().lower()
    from app_lang import coerce_app_lang

    lang = coerce_app_lang(lang)

    if lang == "en":
        return en
    if lang == "hi":
        if isinstance(hi, str) and hi and prose_fully_hindi(hi):
            return hi
        if prose_fully_hindi(en):
            return en
        cached = _cache_get(lang, en)
        if cached is not None and prose_fully_hindi(cached):
            return cached
        translated = _translate_via_openai(en, lang)
        if translated:
            _cache_put(lang, en, translated)
            return translated
        return en
    if lang not in LANG_NAMES:
        return en  # unknown lang → English fallback

    cached = _cache_get(lang, en)
    if cached is not None:
        return cached

    translated = _translate_via_openai(en, lang)
    if translated is None:
        # Only Hindi UI may fall back to Devanagari; Odia/Tamil/etc. must not show Hindi.
        if lang == "hi" and isinstance(hi, str) and hi:
            return hi
        return en

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

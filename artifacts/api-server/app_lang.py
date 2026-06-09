"""Supported Cosmic Lens UI languages (mobile + API)."""

from __future__ import annotations

APP_LANG_CODES = frozenset({"en", "hn", "hi"})


def coerce_app_lang(lang: str | None) -> str:
    """Map legacy/unknown codes to en, hn, or hi."""
    c = (lang or "en").strip().lower()
    if c in ("en", "english"):
        return "en"
    if c in ("hn", "hinglish"):
        return "hn"
    if c in ("hi", "hindi"):
        return "hi"
    return "en"

"""Reply-language hint only. The Support AI understands the question itself."""
from __future__ import annotations

from typing import Any


def detect_lang(text: str, preferred: str | None = None) -> str:
    blob = text or ""
    if any("\u0900" <= ch <= "\u097f" for ch in blob):
        return "hi"
    v = (preferred or "").strip().lower()
    letters = "".join(ch for ch in blob if ch.isalpha())
    if len(letters) >= 8 and letters.isascii():
        hinglish = (
            " kya ",
            " hai ",
            " nahi ",
            " kaise ",
            " kahan ",
            " meri ",
            " kitna ",
            " chahiye ",
            " batao ",
        )
        low = f" {blob.lower()} "
        if any(w in low for w in hinglish):
            return "hn"
        return "en"
    return v if v in ("en", "hn", "hi") else "hn"


def prior_user_texts(history: list[dict[str, Any]] | None) -> list[str]:
    return [
        str(m.get("text") or "").strip()
        for m in (history or [])
        if isinstance(m, dict) and m.get("sender") == "user"
    ][:-1]

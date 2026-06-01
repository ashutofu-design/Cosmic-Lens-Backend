"""Strip Devanagari from Love Reality PDF prose when Noto fonts are not embedded."""
from __future__ import annotations

import re
from typing import Any

from vedic.compat.premium_chapters import CHAPTER_BODY_KEY

_DEVA_RE = re.compile(r"[\u0900-\u097F\u1CD0-\u1CFF\uA8E0-\uA8FF]+")

_CHAPTER_FALLBACK_KEYS = (
    ("love_connection", "love_compatibility"),
    ("breakup", "breakup_chances"),
    ("loyalty", "loyalty_check"),
    ("will_return", "will_return"),
    ("future_outcome", "future_outcome"),
    ("red_flags", "hidden_red_flags"),
)


def has_devanagari(text: str) -> bool:
    return bool(text and _DEVA_RE.search(text))


def strip_devanagari(text: str) -> str:
    if not text:
        return ""
    out = _DEVA_RE.sub(" ", text)
    return re.sub(r"\s+", " ", out).strip()


def _engine_fallback(bundle: dict | None, chapter_key: str) -> str:
    if not bundle:
        return ""
    for ck, bk in _CHAPTER_FALLBACK_KEYS:
        if ck == chapter_key:
            block = bundle.get(bk) or {}
            parts = [
                str(block.get("emotional_summary") or "").strip(),
                " ".join(str(r) for r in (block.get("reasons") or [])[:4]),
            ]
            return strip_devanagari(" ".join(p for p in parts if p))
    return ""


def _sanitize_str(value: str, *, min_len: int = 80, fallback: str = "") -> str:
    cleaned = strip_devanagari(value)
    if len(cleaned) >= min_len:
        return cleaned
    fb = strip_devanagari(fallback)
    if len(fb) >= min_len:
        return fb
    if cleaned:
        return cleaned
    return fb or (
        "This chapter reflects your combined chart signals for this theme. "
        "The reading is written in clear English so it displays correctly in your PDF."
    )


def _walk_strings(obj: Any, bundle: dict | None) -> Any:
    if isinstance(obj, str):
        return _sanitize_str(obj, min_len=40, fallback="")
    if isinstance(obj, list):
        return [_walk_strings(x, bundle) for x in obj]
    if isinstance(obj, dict):
        return {k: _walk_strings(v, bundle) for k, v in obj.items()}
    return obj


def sanitize_love_reality_pro_premium(pro: dict, bundle: dict | None = None) -> dict:
    """Remove Devanagari codepoints; refill thin chapters from engine summaries."""
    if not isinstance(pro, dict):
        return pro or {}
    out = _walk_strings(pro, bundle)
    if not isinstance(out, dict):
        return pro
    chapters = out.get("chapters")
    if not isinstance(chapters, list):
        return out
    for ch in chapters:
        if not isinstance(ch, dict):
            continue
        key = str(ch.get("key") or "").strip().lower()
        body = str(ch.get(CHAPTER_BODY_KEY) or ch.get("full_read") or "").strip()
        fb = _engine_fallback(bundle, key)
        fixed = _sanitize_str(body, min_len=120, fallback=fb)
        ch[CHAPTER_BODY_KEY] = fixed
        if ch.get("full_read"):
            ch["full_read"] = fixed
        gr = str(ch.get("grounding") or "").strip()
        if gr:
            ch["grounding"] = _sanitize_str(gr, min_len=20, fallback=fb[:280])
    for field in ("hidden_truth", "verdict"):
        if out.get(field):
            out[field] = _sanitize_str(str(out[field]), min_len=40, fallback="")
    for list_key in ("special", "damage", "practical"):
        items = out.get(list_key)
        if isinstance(items, list):
            out[list_key] = [
                _sanitize_str(str(x), min_len=12, fallback="")
                for x in items
                if str(x).strip()
            ]
    return out


def polish_content_lang(lang: str) -> str:
    """OpenAI content lane — Roman Hindi, never Devanagari."""
    code = (lang or "en").strip().lower()
    if code == "hi":
        return "hn"
    return code if code in ("en", "hn") else "en"

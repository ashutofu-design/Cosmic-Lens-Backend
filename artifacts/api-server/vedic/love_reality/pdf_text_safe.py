"""Love Reality PDF prose — Devanagari preserved for lang=hi when Noto fonts are bundled."""
from __future__ import annotations

import re
from typing import Any

from vedic.compat.premium_chapters import CHAPTER_BODY_KEY, normalize_pro_pdf_lang

_DEVA_RE = re.compile(r"[\u0900-\u097F\u1CD0-\u1CFF\uA8E0-\uA8FF]+")
_SNAKE_TOKEN_RE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b", re.IGNORECASE)
_KEBAB_TOKEN_RE = re.compile(r"\b[a-z][a-z0-9]*(?:-[a-z0-9]+)+\b", re.IGNORECASE)


def humanize_display_tokens(text: str) -> str:
    if not text:
        return ""

    def _snake_repl(match: re.Match[str]) -> str:
        return match.group(0).replace("_", " ")

    def _kebab_repl(match: re.Match[str]) -> str:
        return match.group(0).replace("-", " ")

    def _clean_inline(chunk: str) -> str:
        chunk = _SNAKE_TOKEN_RE.sub(_snake_repl, chunk)
        chunk = _KEBAB_TOKEN_RE.sub(_kebab_repl, chunk)
        chunk = re.sub(r"[-–—]", " ", chunk)
        return re.sub(r"[ \t]+", " ", chunk).strip()

    if "\n" in text:
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        if len(paras) > 1:
            return "\n\n".join(_clean_inline(p) for p in paras if _clean_inline(p))
    return _clean_inline(text)


def humanize_snake_tokens(text: str) -> str:
    """Back-compat alias."""
    return humanize_display_tokens(text)


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


def polish_content_lang(lang: str) -> str:
    """OpenAI content lane: en | hn (Roman) | hi (Devanagari)."""
    code = normalize_pro_pdf_lang(lang)
    return code if code in ("en", "hn", "hi") else "en"


def love_script_directive(lang: str) -> str:
    """Hard script lock for LLM JSON output."""
    lane = polish_content_lang(lang)
    if lane == "hi":
        return (
            "CRITICAL SCRIPT LOCK — language=hi: सारा narrative JSON देवनागरी हिंदी में लिखो। "
            "Roman/Latin वाक्य मना है (partner names, scores, graha names Latin में रह सकते हैं)।"
        )
    if lane == "hn":
        return (
            "CRITICAL SCRIPT LOCK — language=hn: natural Roman Hinglish ONLY (Latin script). "
            "No Devanagari (क ख म forbidden). No full English paragraphs."
        )
    return "CRITICAL SCRIPT LOCK — language=en: plain conversational English only."


def love_write_script_label(lang: str) -> str:
    lane = polish_content_lang(lang)
    return {
        "en": "plain conversational English",
        "hn": "natural Roman Hinglish (Latin script only)",
        "hi": "natural Hindi in Devanagari script (देवनागरी)",
    }[lane]


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


def _meaningful_paragraph_count(text: str, *, min_words: int = 20) -> int:
    parts = [p.strip() for p in re.split(r"\n\s*\n", (text or "").strip()) if p.strip()]
    return sum(1 for p in parts if len(p.split()) >= min_words)


def _thin_fallback(lang: str) -> str:
    lane = polish_content_lang(lang)
    if lane == "hi":
        return (
            "यह अध्याय आप दोनों के संयुक्त चार्ट संकेतों पर आधारित है — "
            "पढ़ाई स्पष्ट हिंदी में दिखे इसलिए लिखा गया।"
        )
    if lane == "hn":
        return (
            "Yeh chapter aap dono ke combined chart signals par based hai — "
            "reading clear Roman Hinglish me dikhe isliye likha gaya."
        )
    return (
        "This chapter reflects your combined chart signals for this theme. "
        "The reading is written in clear English so it displays correctly in your PDF."
    )


def _sanitize_str(
    value: str,
    *,
    min_len: int = 80,
    fallback: str = "",
    preserve_long_prose: bool = True,
    preserve_devanagari: bool = False,
    lang: str = "en",
) -> str:
    raw = value or ""
    if preserve_devanagari:
        cleaned = humanize_snake_tokens(raw)
    else:
        cleaned = humanize_snake_tokens(strip_devanagari(raw))
    if preserve_long_prose and (
        len(cleaned) >= 500
        or _meaningful_paragraph_count(cleaned, min_words=25) >= 2
    ):
        return cleaned
    if len(cleaned) >= min_len:
        return cleaned
    fb = humanize_snake_tokens(
        strip_devanagari(fallback) if not preserve_devanagari else fallback
    )
    if len(cleaned) < 120 and len(fb) >= min_len:
        return fb
    if cleaned:
        return cleaned
    return fb or _thin_fallback(lang)


def _walk_strings(
    obj: Any,
    bundle: dict | None,
    *,
    preserve_devanagari: bool,
    lang: str,
) -> Any:
    if isinstance(obj, str):
        return _sanitize_str(
            obj,
            min_len=40,
            fallback="",
            preserve_devanagari=preserve_devanagari,
            lang=lang,
        )
    if isinstance(obj, list):
        return [_walk_strings(x, bundle, preserve_devanagari=preserve_devanagari, lang=lang) for x in obj]
    if isinstance(obj, dict):
        return {
            k: _walk_strings(v, bundle, preserve_devanagari=preserve_devanagari, lang=lang)
            for k, v in obj.items()
        }
    return obj


def sanitize_love_reality_pro_premium(
    pro: dict,
    bundle: dict | None = None,
    lang: str = "en",
) -> dict:
    """Refill thin chapters; strip Devanagari only for en/hn lanes (hi keeps देवनागरी)."""
    if not isinstance(pro, dict):
        return pro or {}
    lane = polish_content_lang(lang)
    preserve_deva = lane == "hi"
    out = _walk_strings(pro, bundle, preserve_devanagari=preserve_deva, lang=lane)
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
        if key in ("love_connection", "red_flags") and len(re.findall(r"\b[\w']+\b", body)) >= 50:
            if preserve_deva:
                fixed = humanize_snake_tokens(body)
            else:
                fixed = humanize_snake_tokens(strip_devanagari(body))
        else:
            fixed = _sanitize_str(
                body,
                min_len=120,
                fallback=fb,
                preserve_long_prose=True,
                preserve_devanagari=preserve_deva,
                lang=lane,
            )
        ch[CHAPTER_BODY_KEY] = fixed
        if ch.get("full_read"):
            ch["full_read"] = fixed
        gr = str(ch.get("grounding") or "").strip()
        if gr:
            ch["grounding"] = _sanitize_str(
                gr,
                min_len=20,
                fallback=fb[:280],
                preserve_long_prose=True,
                preserve_devanagari=preserve_deva,
                lang=lane,
            )
    for field in (
        "hidden_truth",
        "verdict",
        "blueprint_reality",
        "red_flags_narrative",
        "dasha_narrative",
        "roadmap_narrative",
        "moon_sync_narrative",
        "remedies_action_narrative",
        "harmony",
    ):
        if out.get(field):
            out[field] = _sanitize_str(
                str(out[field]),
                min_len=40,
                fallback="",
                preserve_long_prose=True,
                preserve_devanagari=preserve_deva,
                lang=lane,
            )
    for list_key in ("special", "damage", "practical"):
        items = out.get(list_key)
        if isinstance(items, list):
            out[list_key] = [
                _sanitize_str(
                    str(x),
                    min_len=80 if list_key == "practical" else 12,
                    fallback="",
                    preserve_long_prose=True,
                    preserve_devanagari=preserve_deva,
                    lang=lane,
                )
                for x in items
                if str(x).strip()
            ]
    return out

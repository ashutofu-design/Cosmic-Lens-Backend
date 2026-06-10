"""Section 08 (Core Root Cause) — Hindi report load gate."""
from __future__ import annotations

import re
from typing import Any

_SECTION8_MIN_WORDS = 80

_ENGINE_FALLBACK_MARKERS = (
    "mercury mismatch",
    "communication style clash",
    "hidden desire axis",
    "12th house):",
)


def _word_count(text: str) -> int:
    return len((text or "").split())


def _root_cause_text(payload: dict[str, Any]) -> str:
    for sec in payload.get("app_sections") or []:
        if not isinstance(sec, dict):
            continue
        if str(sec.get("id") or "").lower() == "root_cause":
            body = str(sec.get("body") or "").strip()
            if body:
                return body
    ctx = payload.get("pdf_context") if isinstance(payload.get("pdf_context"), dict) else {}
    return str(ctx.get("page6_root_cause") or "").strip()


def _breakup_chapter_text(payload: dict[str, Any]) -> str:
    pro = payload.get("pro_premium") if isinstance(payload.get("pro_premium"), dict) else {}
    for ch in pro.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        if str(ch.get("key") or "").strip().lower() == "breakup":
            return str(ch.get("chapter_body") or ch.get("full_read") or "").strip()
    return ""


def section8_hi_load_gate(payload: dict[str, Any]) -> tuple[bool, str]:
    """
    Hindi report loads only when Section 8 has full LLM explanation.
    Returns (ok, exact_reason_hinglish).
    """
    lang = (payload.get("lang") or "").strip().lower()
    if lang != "hi":
        return True, ""

    root = _root_cause_text(payload)
    breakup = _breakup_chapter_text(payload)

    if not breakup:
        if not root:
            return False, (
                "Report load nahi hua — Section 8 (मूल कारण) bilkul khali hai. "
                "LLM ne breakup chapter generate nahi kiya. Niche «Update Report» dabayein."
            )
        return False, (
            "Report load nahi hua — LLM breakup chapter save nahi hua "
            "(sirf engine text mila). Niche «Update Report» dabayein."
        )

    breakup_wc = _word_count(breakup)
    if breakup_wc < _SECTION8_MIN_WORDS:
        return False, (
            f"Report load nahi hua — Section 8 LLM explanation bahut chhota hai "
            f"({breakup_wc} words, kam se kam {_SECTION8_MIN_WORDS} chahiye). "
            "OpenAI poora paragraph nahi likh paya — Update dubara try karein."
        )

    root_wc = _word_count(root)
    if root_wc < _SECTION8_MIN_WORDS:
        return False, (
            f"Report load nahi hua — Section 8 screen text incomplete hai "
            f"({root_wc} words). LLM chapter poora map nahi hua — Update dubara dabayein."
        )

    root_lower = root.lower()
    for marker in _ENGINE_FALLBACK_MARKERS:
        if marker in root_lower and breakup_wc < _SECTION8_MIN_WORDS:
            return False, (
                "Report load nahi hua — Section 8 par purana English engine text aa raha hai, "
                "LLM Hindi explanation nahi. Update Report se fresh LLM chalao."
            )

    try:
        from i18n_summary import prose_fully_hindi

        if not prose_fully_hindi(breakup):
            deva = len(re.findall(r"[\u0900-\u097F]", breakup))
            return False, (
                "Report load nahi hua — Section 8 LLM text abhi poori देवनागरी Hindi nahi hai "
                f"(Devanagari chars: {deva}). Mixed/English lines hain — Update dubara dabayein."
            )
        if not prose_fully_hindi(root):
            return False, (
                "Report load nahi hua — Section 8 display text Hindi me convert nahi hua. "
                "Update Report dubara dabayein."
            )
    except Exception:
        from vedic.love_reality.pdf_text_safe import prose_matches_lang

        if not prose_matches_lang(breakup, "hi") or not prose_matches_lang(root, "hi"):
            return False, (
                "Report load nahi hua — Section 8 Hindi script match nahi karti. "
                "Update Report dubara dabayein."
            )

    return True, ""

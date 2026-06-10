"""Section 4 (उपाय और आगे क्या करें) — Hindi report load gate."""

from __future__ import annotations

import re
from typing import Any

from vedic.love_reality.love_section_polish import remedies_action_hi_ready

_SECTION4_MIN_WORDS = 70

_GENERIC_REC_MARKERS = (
    "हर झगड़े के २४ घंटे",
    "साप्ताहिक २० मिनट",
    "कमज़ोर दशा में अल्टीमेटम",
)


def _word_count(text: str) -> int:
    return len((text or "").split())


def _deva_count(text: str) -> int:
    return len(re.findall(r"[\u0900-\u097F]", text or ""))


def effective_section4_hi_text(payload: dict[str, Any]) -> str:
    canon = str(payload.get("section4_hi_body") or "").strip()
    if canon:
        return canon
    pro = payload.get("pro_premium") if isinstance(payload.get("pro_premium"), dict) else {}
    narr = str(pro.get("remedies_action_narrative") or "").strip()
    if narr:
        return narr
    p1 = payload.get("page1") if isinstance(payload.get("page1"), dict) else {}
    paras = [
        str(p).strip()
        for p in (p1.get("recommendation_paragraphs") or [])
        if str(p).strip()
    ]
    if paras:
        return "\n\n".join(paras)
    for sec in payload.get("app_sections") or []:
        if not isinstance(sec, dict):
            continue
        if str(sec.get("id") or "").lower() == "recommendations":
            return str(sec.get("body") or "").strip()
    return ""


def _looks_generic_fallback(payload: dict[str, Any], body: str) -> bool:
    if _word_count(body) >= _SECTION4_MIN_WORDS and _deva_count(body) >= 20:
        return False
    p1 = payload.get("page1") if isinstance(payload.get("page1"), dict) else {}
    bullets = list(p1.get("recommendations") or [])
    for sec in payload.get("app_sections") or []:
        if isinstance(sec, dict) and str(sec.get("id") or "").lower() == "recommendations":
            bullets = bullets or list(sec.get("bullets") or [])
            break
    bullets = [str(b).strip() for b in bullets if str(b).strip()]
    if not bullets:
        return True
    hits = sum(1 for b in bullets if any(m in b for m in _GENERIC_REC_MARKERS))
    return hits >= min(2, len(bullets))


def section4_hi_load_gate(payload: dict[str, Any] | None) -> tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "Section 4 data missing — Update Report dubara dabayein."
    pro = payload.get("pro_premium") if isinstance(payload.get("pro_premium"), dict) else {}
    llm_meta = (pro.get("_meta") or {}).get("section4_remedies") if isinstance(pro.get("_meta"), dict) else {}
    if isinstance(llm_meta, dict) and llm_meta.get("source") == "failed":
        reason = str(llm_meta.get("reject") or llm_meta.get("reason") or "llm_failed").strip()
        return False, (
            "Report load nahi hua — Section 4 (उपाय) LLM Hindi chapter fail hua "
            f"({reason}). «रिपोर्ट अपडेट करें» dubara dabao — 2–3 min wait."
        )
    if remedies_action_hi_ready(pro):
        return True, ""
    text = effective_section4_hi_text(payload)
    if not text or _looks_generic_fallback(payload, text):
        return False, (
            "Report load nahi hua — Section 4 (उपाय और आगे क्या करें) mein sirf chhoti "
            "generic lines hain, LLM se poora Hindi explanation nahi bana. "
            "«रिपोर्ट अपडेट करें» dabao."
        )
    wc = _word_count(text)
    if wc < _SECTION4_MIN_WORDS:
        return False, (
            f"Report load nahi hua — Section 4 bahut chhota hai ({wc} words, "
            f"kam se kam {_SECTION4_MIN_WORDS} chahiye). Update dubara try karein."
        )
    try:
        from i18n_summary import prose_fully_hindi

        if not prose_fully_hindi(text):
            return False, (
                "Report load nahi hua — Section 4 abhi English/mixed hai, poori देवनागरी "
                f"Hindi nahi (Devanagari={_deva_count(text)}). «रिपोर्ट अपडेट करें» dabao."
            )
    except Exception:
        if _deva_count(text) < 20:
            return False, "Section 4 mein Devanagari Hindi nahi mili — Update dubara dabayein."
    return True, ""

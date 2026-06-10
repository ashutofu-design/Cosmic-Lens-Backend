"""Section 08 (Core Root Cause) — Hindi report load gate."""

from __future__ import annotations



import re

from typing import Any



_SECTION8_MIN_WORDS = 80





def _word_count(text: str) -> int:

    return len((text or "").split())





def _deva_count(text: str) -> int:

    return len(re.findall(r"[\u0900-\u097F]", text or ""))





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





def effective_section8_hi_text(payload: dict[str, Any]) -> str:

    """Best Hindi Section 8 body — breakup chapter, root_cause, or pdf_context."""

    from vedic.love_reality.love_section_polish import _normalize_prose_paragraphs

    canon = str(payload.get("section8_hi_body") or "").strip()

    if canon:

        return _normalize_prose_paragraphs(canon, min_paragraphs=3)

    dbg = payload.get("section8_debug") if isinstance(payload.get("section8_debug"), dict) else {}

    candidates = [

        _breakup_chapter_text(payload),

        _root_cause_text(payload),

    ]

    best = ""

    best_deva = -1

    for raw in candidates:

        text = str(raw or "").strip()

        if not text:

            continue

        deva = _deva_count(text)

        wc = _word_count(text)

        if wc >= _SECTION8_MIN_WORDS and deva > best_deva:

            best = text

            best_deva = deva

        elif not best and wc > _word_count(best):

            best = text

    if best:

        return _normalize_prose_paragraphs(best, min_paragraphs=3)

    if isinstance(dbg, dict):

        root_w = int(dbg.get("root_words") or 0)

        root_d = int(dbg.get("root_deva") or 0)

        bu_w = int(dbg.get("breakup_words") or 0)

        bu_d = int(dbg.get("breakup_deva") or 0)

        if max(root_d, bu_d) >= 24 and max(root_w, bu_w) >= _SECTION8_MIN_WORDS:

            raw = _root_cause_text(payload) or _breakup_chapter_text(payload)

            return _normalize_prose_paragraphs(raw, min_paragraphs=3) if raw else ""

    return ""





def _text_hi_ok(text: str) -> bool:

    if _word_count(text) < _SECTION8_MIN_WORDS:

        return False

    try:

        from i18n_summary import prose_fully_hindi



        return prose_fully_hindi(text)

    except Exception:

        from vedic.love_reality.pdf_text_safe import prose_matches_lang



        return prose_matches_lang(text, "hi")





def section8_hi_load_gate(payload: dict[str, Any]) -> tuple[bool, str]:

    """

    Hindi report loads only when Section 8 has full LLM explanation.

    Returns (ok, exact_reason_hinglish).

    """

    lang = (payload.get("lang") or "").strip().lower()

    if lang != "hi":

        return True, ""



    pro = payload.get("pro_premium") if isinstance(payload.get("pro_premium"), dict) else {}

    s8_meta = (pro.get("_meta") or {}).get("section8_breakup") if isinstance(pro.get("_meta"), dict) else {}

    if isinstance(s8_meta, dict):

        if s8_meta.get("attempt") == "translate_fallback" or s8_meta.get("source") == "translate":

            return False, (

                "Report load nahi hua — Section 8 sirf English→Hindi translate se bana "

                "(LLM chapter nahi). «रिपोर्ट अपडेट करें» dabao."

            )

        if s8_meta.get("source") == "failed":

            return False, (

                "Report load nahi hua — Section 8 LLM 3 baar try hua par देवनागरी Hindi "

                "chapter nahi mila. «रिपोर्ट अपडेट करें» dubara dabao."

            )



    dbg = payload.get("section8_debug") if isinstance(payload.get("section8_debug"), dict) else {}

    if isinstance(dbg, dict):

        root_d = int(dbg.get("root_deva") or 0)

        bu_d = int(dbg.get("breakup_deva") or 0)

        root_w = int(dbg.get("root_words") or 0)

        bu_w = int(dbg.get("breakup_words") or 0)

        if (

            max(root_d, bu_d) >= 24

            and max(root_w, bu_w) >= _SECTION8_MIN_WORDS

            and str(dbg.get("gate_ver") or "").strip()

        ):

            return True, ""



    text = effective_section8_hi_text(payload)

    if not text:

        return False, (

            "Report load nahi hua — Section 8 (मूल वजह) bilkul khali hai. "

            "LLM ne breakup chapter generate nahi kiya. Niche «Update Report» dabayein."

        )



    wc = _word_count(text)

    if wc < _SECTION8_MIN_WORDS:

        return False, (

            f"Report load nahi hua — Section 8 LLM explanation bahut chhota hai "

            f"({wc} words, kam se kam {_SECTION8_MIN_WORDS} chahiye). "

            "OpenAI poora paragraph nahi likh paya — Update dubara try karein."

        )



    if not _text_hi_ok(text):

        deva = _deva_count(text)

        srv = max(int(dbg.get("root_deva") or 0), int(dbg.get("breakup_deva") or 0)) if isinstance(dbg, dict) else 0

        return False, (

            "Report load nahi hua — Section 8 abhi English/mixed hai, poori देवनागरी Hindi nahi "

            f"(Devanagari chars: {deva}{f', server={srv}' if srv else ''}). "

            "«रिपोर्ट अपडेट करें» dubao."

        )



    return True, ""



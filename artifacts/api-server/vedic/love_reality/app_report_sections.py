"""
Complete in-app scroll sections — backfill from LLM, Hindi/Hinglish labels, localize prose.
"""
from __future__ import annotations

import re
from typing import Any

from vedic.love_reality.app_pdf_parity import build_in_app_page_sections
from vedic.love_reality.pdf_page1_data import (
    _localize_page1_dashboard,
    _localize_prose_block,
    localize_love_pdf_context,
)
from vedic.love_reality.pdf_text_safe import polish_content_lang

_ANALYSIS_KEY_BY_TITLE = {
    "emotional": ("emotional", "भावनात्मक", "compatibility"),
    "communication": ("communication", "संवाद", "communication"),
    "trust": ("trust", "विश्वास", "loyalty"),
    "long_term": ("long_term", "long-term", "दीर्घ", "potential"),
}

_METRIC_LABELS: dict[str, dict[str, str]] = {
    "hi": {
        "Love Compatibility": "प्रेम अनुकूलता",
        "Breakup Risk": "ब्रेकअप जोखिम",
        "Loyalty & Trust": "निष्ठा और विश्वास",
        "Reunion Chance": "पुनर्मिलन की संभावना",
        "Love": "प्रेम",
        "Breakup": "ब्रेकअप",
        "Loyalty": "निष्ठा",
        "Return": "वापसी",
    },
    "hn": {
        "Love Compatibility": "Love Compatibility",
        "Breakup Risk": "Breakup Risk",
        "Loyalty & Trust": "Loyalty & Trust",
        "Reunion Chance": "Reunion Chance",
    },
}

_STRENGTH_LABELS_HI = {
    "Emotional magnetism": "भावनात्मक आकर्षण",
    "Shared growth intent": "साझा विकास की इच्छा",
    "Karmic pull": "कर्मिक खिंचाव",
    "Attraction axis": "आकर्षण अक्ष",
}

_CHALLENGE_LABELS_HI = {
    "Communication gaps": "संवाद में अंतर",
    "Trust under stress": "तनाव में विश्वास",
    "Timing misalignment": "समय की बेतालमेल",
    "Conflict escalation": "संघर्ष बढ़ना",
}

_ANALYSIS_TITLES_HI = {
    "emotional": "भावनात्मक अनुकूलता",
    "communication": "संवाद",
    "trust": "विश्वास और निष्ठा",
    "long_term": "दीर्घकालिक संभावना",
}

_ANALYSIS_TITLES_EN = {
    "emotional": "Emotional Compatibility",
    "communication": "Communication",
    "trust": "Trust & Loyalty",
    "long_term": "Long-Term Potential",
}


def _analysis_title(key: str, lang: str) -> str:
    lane = polish_content_lang(lang)
    if lane == "hi":
        return _ANALYSIS_TITLES_HI.get(key, key)
    if lane == "en":
        return _ANALYSIS_TITLES_EN.get(key, key)
    return key


def _chapter_body(pro: dict, key: str) -> str:
    for ch in pro.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        if (ch.get("key") or "").strip().lower() == key:
            return (ch.get("chapter_body") or ch.get("full_read") or "").strip()
    return ""


def _word_count(text: str) -> int:
    return len((text or "").split())


def _deep_analysis_map(pro: dict, *, min_words: int = 55, lang: str = "en") -> dict[str, str]:
    from vedic.love_reality.pdf_text_safe import prose_lane_ok

    out: dict[str, str] = {}
    for row in pro.get("deep_analysis") or []:
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "").strip().lower()
        expl = str(row.get("explanation") or "").strip()
        if key and _word_count(expl) >= min_words and prose_lane_ok(expl, lang):
            out[key] = expl
    return out


def _deep_connection_body_from_analysis(
    analysis_rows: list[dict[str, Any]],
    lang: str = "en",
) -> str:
    from vedic.love_reality.pdf_text_safe import prose_lane_ok

    lines: list[str] = []
    for row in analysis_rows:
        if not isinstance(row, dict):
            continue
        expl = str(row.get("explanation") or "").strip()
        if _word_count(expl) < 40 or not prose_lane_ok(expl, lang):
            continue
        title = str(row.get("title") or "Analysis").strip()
        lines.append(f"{title}\n{expl}")
    return "\n\n".join(lines)


def _deep_analysis_expl_hi_locked(text: str) -> bool:
    raw = str(text or "").strip()
    if _word_count(raw) < 55:
        return False
    try:
        from i18n_summary import prose_fully_hindi

        return prose_fully_hindi(raw)
    except Exception:
        return len(re.findall(r"[\u0900-\u097F]", raw)) >= 24


def _match_analysis_key(title: str) -> str:
    t = (title or "").lower()
    for key, tokens in _ANALYSIS_KEY_BY_TITLE.items():
        if any(tok.lower() in t for tok in tokens):
            return key
    return ""


def _ui_label(label: str, lang: str) -> str:
    if lang == "hi":
        return (
            _METRIC_LABELS.get("hi", {}).get(label)
            or _STRENGTH_LABELS_HI.get(label)
            or _CHALLENGE_LABELS_HI.get(label)
            or label
        )
    return label


def _apply_ui_label_locale(page1: dict[str, Any], lang: str) -> dict[str, Any]:
    if lang not in ("hi", "hn"):
        return page1
    out = dict(page1)
    metrics = []
    for row in out.get("metrics") or []:
        if not isinstance(row, dict):
            continue
        m = dict(row)
        lbl = str(m.get("label") or "")
        if lbl:
            m["label"] = _ui_label(lbl, lang)
        interp = str(m.get("interpretation") or "").strip()
        if interp and lang == "hi":
            m["interpretation"] = _localize_prose_block(interp, lang)
        metrics.append(m)
    if metrics:
        out["metrics"] = metrics

    strengths = []
    for row in out.get("strengths") or []:
        if not isinstance(row, dict):
            continue
        s = dict(row)
        lbl = str(s.get("label") or "")
        if lbl:
            s["label"] = _ui_label(lbl, lang)
        strengths.append(s)
    if strengths:
        out["strengths"] = strengths

    challenges = []
    for row in out.get("challenges") or []:
        if not isinstance(row, dict):
            continue
        c = dict(row)
        lbl = str(c.get("label") or "")
        if lbl:
            c["label"] = _ui_label(lbl, lang)
        challenges.append(c)
    if challenges:
        out["challenges"] = challenges

    da_map = _deep_analysis_map(out.get("_pro_ref") or {}, lang=lang)
    analysis_rows = []
    for row in out.get("analysis") or []:
        if not isinstance(row, dict):
            continue
        a = dict(row)
        akey = _match_analysis_key(str(a.get("title") or ""))
        if akey:
            a["title"] = _analysis_title(akey, lang)
        expl = str(a.get("explanation") or "").strip()
        if len(expl) < 40 and akey and da_map.get(akey):
            a["explanation"] = da_map[akey]
            expl = str(a["explanation"] or "").strip()
        if expl and lang in ("hi", "hn"):
            if lang == "hi" and _deep_analysis_expl_hi_locked(expl):
                a["explanation"] = expl
            else:
                a["explanation"] = _localize_prose_block(expl, lang, force=True)
        analysis_rows.append(a)
    if analysis_rows:
        out["analysis"] = analysis_rows
    out.pop("_pro_ref", None)
    return out


def enrich_page1_and_context(
    page1: dict[str, Any],
    pdf_context: dict[str, Any],
    pro: dict[str, Any],
    lang: str = "en",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fill thin/empty bodies from pro_premium LLM before localize."""
    p1 = dict(page1 or {})
    ctx = dict(pdf_context or {})
    pro = pro if isinstance(pro, dict) else {}
    p1["_pro_ref"] = pro
    da_map = _deep_analysis_map(pro, lang=lang)

    verdict = str(p1.get("verdict") or "").strip()
    if _word_count(verdict) < 18:
        v = str(pro.get("verdict") or "").strip()
        if v:
            p1["verdict"] = v

    rn = str(pro.get("remedies_action_narrative") or "").strip()
    cur_para = " ".join(
        str(p).strip() for p in (p1.get("recommendation_paragraphs") or []) if str(p).strip()
    )
    if rn and _word_count(rn) > _word_count(cur_para):
        if "\n\n" in rn:
            p1["recommendation_paragraphs"] = [p.strip() for p in rn.split("\n\n") if p.strip()]
        else:
            p1["recommendation_paragraphs"] = [rn]
    elif not p1.get("recommendation_paragraphs"):
        if rn:
            p1["recommendation_paragraphs"] = [rn]
        elif lang != "hi" and pro.get("practical"):
            paras = [str(x).strip() for x in pro["practical"] if str(x).strip() and len(str(x)) > 80]
            if paras:
                p1["recommendation_paragraphs"] = paras[:2]

    steps = [str(x).strip() for x in (pro.get("action_steps") or []) if str(x).strip()]
    if steps:
        p1["recommendations"] = steps[:7]
    elif not p1.get("recommendations") and pro.get("practical"):
        p1["recommendations"] = [
            str(x).strip() for x in pro["practical"][:7] if str(x).strip()
        ]

    analysis_out = []
    for row in p1.get("analysis") or []:
        if not isinstance(row, dict):
            continue
        a = dict(row)
        akey = _match_analysis_key(str(a.get("title") or ""))
        if len(str(a.get("explanation") or "").strip()) < 40 and akey and da_map.get(akey):
            a["explanation"] = da_map[akey]
        analysis_out.append(a)
    if analysis_out:
        p1["analysis"] = analysis_out
    elif da_map:
        p1["analysis"] = [
            {
                "title": _analysis_title(k, lang),
                "score": 0,
                "explanation": v,
            }
            for k, v in da_map.items()
        ]

    moon = dict(ctx.get("page5_moon") or {})
    narr = _moon_sync_ready_text(pro, lang)
    if narr:
        moon["body"] = narr
    ctx["page5_moon"] = moon

    breakup_llm = _breakup_ready_text(pro, lang)
    if breakup_llm:
        ctx["page6_root_cause"] = breakup_llm
    else:
        root = str(ctx.get("page6_root_cause") or "").strip()
        if _word_count(root) < 35:
            fb = str(pro.get("red_flags_narrative") or "").strip()
            if fb:
                ctx["page6_root_cause"] = fb

    bp = dict(ctx.get("page2_3_blueprint") or {})
    br = _blueprint_ready_text(pro, lang)
    if br:
        bp["part2"] = br
    ctx["page2_3_blueprint"] = bp

    return p1, ctx


def _llm_hindi_body_locked(text: str, section_id: str) -> bool:
    """Keep full LLM Hindi — force-relocalize shortens Section 7/8 to one-liners."""
    sid = str(section_id or "").lower()
    raw = str(text or "").strip()
    if not raw:
        return False
    try:
        from i18n_summary import prose_fully_hindi

        if not prose_fully_hindi(raw):
            return False
    except Exception:
        if len(re.findall(r"[\u0900-\u097F]", raw)) < 24:
            return False
    wc = _word_count(raw)
    if sid == "moon":
        return wc >= 55
    if sid == "root_cause":
        return wc >= 80
    if sid == "blueprint_vs":
        return wc >= 80
    if sid == "deep_connection":
        return wc >= 200
    if sid == "recommendations":
        return wc >= 80
    return False


def _blueprint_ready_text(pro: dict, lang: str = "en") -> str:
    """Plain-language blueprint LLM — no planet/house dump."""
    from vedic.love_reality.love_section_polish import (
        _blueprint_body_text,
        _blueprint_has_chart_jargon,
        _blueprint_text_hi_ok,
        _prose_paragraph_form_ok,
    )

    body = _blueprint_body_text(pro)
    if (
        _word_count(body) < 80
        or _blueprint_has_chart_jargon(body)
        or not _prose_paragraph_form_ok(body, min_paragraphs=3, min_para_words=18)
    ):
        return ""
    lane = (lang or "en").strip().lower()
    if lane != "hi":
        return body
    if _blueprint_text_hi_ok(body):
        return body
    return ""


def _sync_recommendations_from_llm(
    sections: list[dict[str, Any]],
    page1: dict[str, Any],
    pro: dict[str, Any],
) -> list[dict[str, Any]]:
    """Map LLM remedies_action_narrative → recommendations section."""
    rn = str(pro.get("remedies_action_narrative") or "").strip()
    paras = [str(p).strip() for p in (page1.get("recommendation_paragraphs") or []) if str(p).strip()]
    para_body = "\n\n".join(paras).strip()
    body = rn if _word_count(rn) > _word_count(para_body) else (para_body or rn)
    bullets = [str(x).strip() for x in (pro.get("action_steps") or page1.get("recommendations") or []) if str(x).strip()]
    if not body and not bullets:
        return sections
    out: list[dict[str, Any]] = []
    patched = False
    for row in sections:
        if not isinstance(row, dict):
            continue
        sec = dict(row)
        if str(sec.get("id") or "").lower() == "recommendations":
            if body:
                sec["body"] = body
            if bullets:
                sec["bullets"] = bullets[:7]
            patched = True
        out.append(sec)
    if not patched:
        out.append({
            "id": "recommendations",
            "body": body or None,
            "bullets": bullets[:7] if bullets else None,
        })
    return out


def _sync_deep_connection_from_llm(
    sections: list[dict[str, Any]],
    page1: dict[str, Any],
    pro: dict[str, Any],
    lang: str = "en",
) -> list[dict[str, Any]]:
    """Map LLM deep_analysis → deep_connection section body."""
    da_map = _deep_analysis_map(pro, lang=lang)
    analysis_rows = list(page1.get("analysis") or [])
    if da_map and not analysis_rows:
        analysis_rows = [
            {"title": _analysis_title(k, lang), "explanation": v}
            for k, v in da_map.items()
        ]
    body = _deep_connection_body_from_analysis(analysis_rows, lang)
    if not body and da_map:
        body = _deep_connection_body_from_analysis(
            [{"title": _analysis_title(k, lang), "explanation": v} for k, v in da_map.items()],
            lang,
        )
    if not body:
        return sections
    out: list[dict[str, Any]] = []
    patched = False
    for row in sections:
        if not isinstance(row, dict):
            continue
        sec = dict(row)
        if str(sec.get("id") or "").lower() == "deep_connection":
            sec["body"] = body
            patched = True
        out.append(sec)
    if not patched:
        out.append({"id": "deep_connection", "body": body})
    return out


def _sync_blueprint_from_llm(
    sections: list[dict[str, Any]],
    ctx: dict[str, Any],
    pro: dict[str, Any],
    lang: str = "en",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Map plain Hindi blueprint LLM → Section 5 (blueprint_vs)."""
    text = _blueprint_ready_text(pro, lang)
    if not text:
        return sections, ctx
    ctx_out = dict(ctx or {})
    bp = dict(ctx_out.get("page2_3_blueprint") or {})
    bp["part2"] = text
    ctx_out["page2_3_blueprint"] = bp
    out: list[dict[str, Any]] = []
    patched = False
    for row in sections:
        if not isinstance(row, dict):
            continue
        sec = dict(row)
        if str(sec.get("id") or "").lower() == "blueprint_vs":
            sec["body"] = text
            patched = True
        out.append(sec)
    if not patched:
        out.append({"id": "blueprint_vs", "body": text})
    return out, ctx_out


def _localize_section_row(row: dict[str, Any], lang: str) -> dict[str, Any]:
    out = dict(row)
    force = lang in ("hi", "hn")
    sid = str(out.get("id") or "").lower()
    if out.get("body"):
        raw = str(out["body"]).strip()
        if lang == "hi" and _llm_hindi_body_locked(raw, sid):
            out["body"] = raw
        else:
            out["body"] = _localize_prose_block(raw, lang, force=force)
    bullets = out.get("bullets")
    if isinstance(bullets, list):
        loc_bullets = []
        for b in bullets:
            raw = str(b).strip()
            if not raw:
                continue
            if out.get("id") == "scorecard" and lang == "hi":
                loc_bullets.append(_localize_scorecard_line(raw, lang))
            else:
                loc_bullets.append(_localize_prose_block(raw, lang, force=force))
        out["bullets"] = loc_bullets
    return out


_SCORE_BAND_HI = {
    "Strong": "मजबूत",
    "Mixed": "मिश्रित",
    "Low": "कम",
    "Very low": "बहुत कम",
    "High risk": "जोखिम अधिक",
    "Moderate risk": "मध्यम जोखिम",
    "Lower risk": "कम जोखिम",
    "Emotional resonance across charts": "चार्टों में भावनात्मक मेल",
    "Stress-trigger separation probability": "तनाव से अलग होने की संभावना",
    "Commitment under pressure": "दबाव में प्रतिबद्धता",
    "Return window if separated": "अलग होने पर वापसी की खिड़की",
}


def _localize_scorecard_line(line: str, lang: str) -> str:
    if lang != "hi":
        return line
    out = line
    for en, hi in _METRIC_LABELS["hi"].items():
        out = out.replace(en, hi)
    for en, hi in {**_STRENGTH_LABELS_HI, **_CHALLENGE_LABELS_HI}.items():
        out = out.replace(en, hi)
    for en, hi in _SCORE_BAND_HI.items():
        out = out.replace(en, hi)
    try:
        from i18n_summary import prose_fully_hindi
        if prose_fully_hindi(out):
            return out
    except Exception:
        if re.search(r"[\u0900-\u097F]", out):
            return out
    return _localize_prose_block(out, lang, force=True)


def _moon_sync_ready_text(pro: dict, lang: str = "en") -> str:
    """LLM Moon Sync narrative — not engine one-liner fallback."""
    narr = str(pro.get("moon_sync_narrative") or "").strip()
    if _word_count(narr) < 55:
        return ""
    lane = (lang or "en").strip().lower()
    if lane != "hi":
        return narr
    try:
        from i18n_summary import prose_fully_hindi

        if prose_fully_hindi(narr):
            return narr
    except Exception:
        if len(re.findall(r"[\u0900-\u097F]", narr)) >= 24:
            return narr
    return ""


def _breakup_ready_text(pro: dict, lang: str = "en") -> str:
    """LLM breakup chapter for Section 8 — not thin engine bullet fallback."""
    breakup = _chapter_body(pro, "breakup")
    if _word_count(breakup) < 80:
        return ""
    try:
        from vedic.love_reality.love_section_polish import (
            _prose_paragraph_form_ok,
            _text_looks_like_point_list,
        )

        if _text_looks_like_point_list(breakup):
            return ""
        if not _prose_paragraph_form_ok(breakup, min_paragraphs=3, min_para_words=18):
            return ""
    except Exception:
        pass
    lane = (lang or "en").strip().lower()
    if lane == "hi":
        try:
            from i18n_summary import prose_fully_hindi

            if prose_fully_hindi(breakup):
                return breakup
        except Exception:
            if len(re.findall(r"[\u0900-\u097F]", breakup)) >= 24:
                return breakup
        return ""
    if lane == "hn":
        try:
            from vedic.love_reality.pdf_text_safe import prose_matches_lang

            if prose_matches_lang(breakup, "hn"):
                return breakup
        except Exception:
            pass
        return ""
    return breakup


def _breakup_hi_ready_text(pro: dict) -> str:
    """LLM Hindi breakup chapter — not English engine fallback."""
    return _breakup_ready_text(pro, "hi")


def _sync_moon_from_narrative(
    sections: list[dict[str, Any]],
    ctx: dict[str, Any],
    pro: dict[str, Any],
    lang: str = "en",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Map LLM moon_sync_narrative → Section 7 (moon) — replace engine one-liner."""
    narr = _moon_sync_ready_text(pro, lang)
    if not narr:
        return sections, ctx
    ctx_out = dict(ctx or {})
    moon = dict(ctx_out.get("page5_moon") or {})
    moon["body"] = narr
    ctx_out["page5_moon"] = moon
    out: list[dict[str, Any]] = []
    patched = False
    for row in sections:
        if not isinstance(row, dict):
            continue
        sec = dict(row)
        if str(sec.get("id") or "").lower() == "moon":
            sec["body"] = narr
            patched = True
        out.append(sec)
    if not patched:
        out.append({"id": "moon", "body": narr})
    return out, ctx_out


def _sync_root_cause_from_breakup(
    sections: list[dict[str, Any]],
    ctx: dict[str, Any],
    pro: dict[str, Any],
    lang: str = "en",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Map LLM breakup chapter → Section 8 (root_cause) — always replace English engine text."""
    breakup = _breakup_ready_text(pro, lang)
    if not breakup:
        return sections, ctx
    ctx_out = dict(ctx or {})
    ctx_out["page6_root_cause"] = breakup
    out: list[dict[str, Any]] = []
    patched = False
    for row in sections:
        if not isinstance(row, dict):
            continue
        sec = dict(row)
        if str(sec.get("id") or "").lower() == "root_cause":
            sec["body"] = breakup
            patched = True
        out.append(sec)
    if not patched:
        out.append({"id": "root_cause", "body": breakup})
    return out, ctx_out


def _finalize_hindi_sections(sections: list[dict[str, Any]], lang: str) -> list[dict[str, Any]]:
    """Second pass — force-translate any narrative still mostly English."""
    if lang not in ("hi", "hn"):
        return sections
    try:
        from i18n_summary import prose_fully_hindi, prose_fully_hinglish
    except Exception:
        return sections

    def _needs_force(text: str) -> bool:
        if lang == "hi":
            return not prose_fully_hindi(text)
        return not prose_fully_hinglish(text)

    out_sections: list[dict[str, Any]] = []
    for row in sections:
        if not isinstance(row, dict):
            continue
        sec = dict(row)
        sid = str(sec.get("id") or "").lower()
        body = str(sec.get("body") or "").strip()
        if (
            body
            and sid != "scorecard"
            and not _llm_hindi_body_locked(body, sid)
            and _needs_force(body)
        ):
            sec["body"] = _localize_prose_block(body, lang, force=True)
        bullets = sec.get("bullets")
        if isinstance(bullets, list):
            fixed = []
            for b in bullets:
                raw = str(b).strip()
                if not raw:
                    continue
                if sid == "scorecard" and lang == "hi":
                    fixed.append(_localize_scorecard_line(raw, lang))
                elif _needs_force(raw, sid):
                    fixed.append(_localize_prose_block(raw, lang, force=True))
                else:
                    fixed.append(raw)
            sec["bullets"] = fixed
        out_sections.append(sec)
    return out_sections


_NARRATIVE_SECTION_IDS = frozenset({
    "exec_summary",
    "verdict",
    "recommendations",
    "deep_connection",
    "blueprint_vs",
    "root_cause",
    "moon",
})


def _content_script_from_sections(
    sections: list[dict[str, Any]],
    lane: str,
) -> str:
    """Per-section check — one English paragraph => hi_partial, not full hi."""
    if lane == "en":
        return "en"
    try:
        from i18n_summary import prose_fully_hindi, prose_fully_hinglish
    except Exception:
        return "unknown"

    chunks: list[str] = []
    for row in sections:
        if not isinstance(row, dict):
            continue
        sid = str(row.get("id") or "").lower()
        if sid not in _NARRATIVE_SECTION_IDS:
            continue
        body = str(row.get("body") or "").strip()
        if body:
            chunks.append(body)
        if sid == "recommendations":
            for b in row.get("bullets") or []:
                raw = str(b).strip()
                if raw:
                    chunks.append(raw)

    if not chunks:
        return "en_mismatch" if lane in ("hi", "hn") else "en"

    if lane == "hi":
        ok = sum(1 for t in chunks if prose_fully_hindi(t))
        if ok == len(chunks):
            return "hi"
        if ok > 0:
            return "hi_partial"
        return "en_mismatch"
    if lane == "hn":
        ok = sum(1 for t in chunks if prose_fully_hinglish(t))
        if ok == len(chunks):
            return "hn"
        if ok > 0:
            return "en_mismatch"
        return "en_mismatch"
    return "en"


def build_localized_app_sections(
    page1: dict[str, Any],
    pdf_context: dict[str, Any],
    pro: dict[str, Any],
    lang: str = "en",
) -> tuple[list[dict[str, Any]], str, dict[str, Any], dict[str, Any]]:
    """
    Full in-app sections + content_script (hi | hn | en | en_mismatch).
    Also returns localized page1 and pdf_context for cache/PDF parity.
    """
    lane = (lang or "en").strip().lower()
    if lane not in ("en", "hn", "hi"):
        lane = "en"

    p1, ctx = enrich_page1_and_context(page1, pdf_context, pro, lane)
    ctx = localize_love_pdf_context(ctx, lane)
    p1 = _localize_page1_dashboard(p1, lane)
    p1 = _apply_ui_label_locale(p1, lane)

    sections = build_in_app_page_sections(p1, ctx, lane)
    sections = _sync_recommendations_from_llm(sections, p1, pro)
    sections = _sync_deep_connection_from_llm(sections, p1, pro, lane)
    sections, ctx = _sync_blueprint_from_llm(sections, ctx, pro, lane)
    sections, ctx = _sync_moon_from_narrative(sections, ctx, pro, lane)
    sections, ctx = _sync_root_cause_from_breakup(sections, ctx, pro, lane)
    if lane in ("hn", "hi"):
        sections = [_localize_section_row(s, lane) for s in sections if isinstance(s, dict)]
        sections = _finalize_hindi_sections(sections, lane)
        sections = _finalize_hindi_sections(sections, lane)

    script = _content_script_from_sections(sections, lane)

    return sections, script, p1, ctx

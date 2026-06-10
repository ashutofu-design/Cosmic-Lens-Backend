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


def _chapter_body(pro: dict, key: str) -> str:
    for ch in pro.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        if (ch.get("key") or "").strip().lower() == key:
            return (ch.get("chapter_body") or ch.get("full_read") or "").strip()
    return ""


def _word_count(text: str) -> int:
    return len((text or "").split())


def _deep_analysis_map(pro: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in pro.get("deep_analysis") or []:
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "").strip().lower()
        expl = str(row.get("explanation") or "").strip()
        if key and len(expl) >= 40:
            out[key] = expl
    return out


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

    da_map = _deep_analysis_map(out.get("_pro_ref") or {})
    analysis_rows = []
    for row in out.get("analysis") or []:
        if not isinstance(row, dict):
            continue
        a = dict(row)
        akey = _match_analysis_key(str(a.get("title") or ""))
        if lang == "hi" and akey in _ANALYSIS_TITLES_HI:
            a["title"] = _ANALYSIS_TITLES_HI[akey]
        expl = str(a.get("explanation") or "").strip()
        if len(expl) < 40 and akey and da_map.get(akey):
            a["explanation"] = da_map[akey]
            expl = str(a["explanation"] or "").strip()
        if expl and lang in ("hi", "hn"):
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
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fill thin/empty bodies from pro_premium LLM before localize."""
    p1 = dict(page1 or {})
    ctx = dict(pdf_context or {})
    pro = pro if isinstance(pro, dict) else {}
    p1["_pro_ref"] = pro
    da_map = _deep_analysis_map(pro)

    verdict = str(p1.get("verdict") or "").strip()
    if _word_count(verdict) < 18:
        v = str(pro.get("verdict") or "").strip()
        if v:
            p1["verdict"] = v

    if not p1.get("recommendation_paragraphs"):
        rn = str(pro.get("remedies_action_narrative") or "").strip()
        if rn:
            p1["recommendation_paragraphs"] = [rn]
        elif pro.get("practical"):
            paras = [str(x).strip() for x in pro["practical"] if str(x).strip() and len(str(x)) > 80]
            if paras:
                p1["recommendation_paragraphs"] = paras[:2]

    if not p1.get("recommendations") and pro.get("practical"):
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
                "title": _ANALYSIS_TITLES_HI.get(k, k),
                "score": 0,
                "explanation": v,
            }
            for k, v in da_map.items()
        ]

    moon = dict(ctx.get("page5_moon") or {})
    if _word_count(str(moon.get("body") or "")) < 45:
        narr = str(pro.get("moon_sync_narrative") or "").strip()
        if narr:
            moon["body"] = narr
    ctx["page5_moon"] = moon

    breakup_llm = _chapter_body(pro, "breakup")
    if breakup_llm:
        ctx["page6_root_cause"] = breakup_llm
    else:
        root = str(ctx.get("page6_root_cause") or "").strip()
        if _word_count(root) < 35:
            fb = str(pro.get("red_flags_narrative") or "").strip()
            if fb:
                ctx["page6_root_cause"] = fb

    bp = dict(ctx.get("page2_3_blueprint") or {})
    if _word_count(str(bp.get("part2") or "")) < 40:
        br = str(pro.get("blueprint_reality") or "").strip() or _chapter_body(pro, "love_connection")
        if br:
            bp["part2"] = br
    ctx["page2_3_blueprint"] = bp

    return p1, ctx


def _localize_section_row(row: dict[str, Any], lang: str) -> dict[str, Any]:
    out = dict(row)
    force = lang in ("hi", "hn")
    if out.get("body"):
        out["body"] = _localize_prose_block(str(out["body"]), lang, force=force)
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


def _breakup_hi_ready_text(pro: dict) -> str:
    """LLM Hindi breakup chapter — not English engine fallback."""
    breakup = _chapter_body(pro, "breakup")
    if _word_count(breakup) < 80:
        return ""
    try:
        from i18n_summary import prose_fully_hindi

        if prose_fully_hindi(breakup):
            return breakup
    except Exception:
        if len(re.findall(r"[\u0900-\u097F]", breakup)) >= 24:
            return breakup
    return ""


def _sync_root_cause_from_breakup(
    sections: list[dict[str, Any]],
    ctx: dict[str, Any],
    pro: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Map LLM breakup chapter → Section 8 (root_cause) — always replace English engine text."""
    breakup = _breakup_hi_ready_text(pro)
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
        if body and sid != "scorecard" and _needs_force(body):
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
                elif _needs_force(raw):
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

    p1, ctx = enrich_page1_and_context(page1, pdf_context, pro)
    ctx = localize_love_pdf_context(ctx, lane)
    p1 = _localize_page1_dashboard(p1, lane)
    p1 = _apply_ui_label_locale(p1, lane)

    sections = build_in_app_page_sections(p1, ctx, lane)
    sections, ctx = _sync_root_cause_from_breakup(sections, ctx, pro)
    if lane in ("hn", "hi"):
        sections = [_localize_section_row(s, lane) for s in sections if isinstance(s, dict)]
        sections = _finalize_hindi_sections(sections, lane)
        sections = _finalize_hindi_sections(sections, lane)

    script = _content_script_from_sections(sections, lane)

    return sections, script, p1, ctx

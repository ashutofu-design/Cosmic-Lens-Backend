"""
Build Love Reality Pro page-1 dashboard payload (mirrors React love-reality-report).
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any


def _chapter_body(pro: dict, key: str) -> str:
    for ch in pro.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        if (ch.get("key") or "").strip().lower() == key:
            return (ch.get("chapter_body") or ch.get("full_read") or "").strip()
    return ""


def _short(text: str, max_len: int = 220) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rsplit(" ", 1)[0] + "…"


def _to_concise_bullets(items: list[str], *, max_items: int = 4, max_len: int = 88) -> list[str]:
    """Split long recommendation paragraphs into short, scannable bullet lines."""
    out: list[str] = []
    for item in items:
        raw = str(item or "").strip()
        if not raw:
            continue
        chunks = re.split(r"(?<=[.;!?])\s+|\n+|(?:\s*[-•]\s+)", raw)
        for chunk in chunks:
            line = chunk.strip(" \t-•·")
            if not line or len(line) < 8:
                continue
            if len(line) > max_len:
                line = _short(line, max_len)
            if line in out:
                continue
            out.append(line)
            if len(out) >= max_items:
                return out
    return out[:max_items]


def _llm_summary_text(pro: dict[str, Any], love_narr: str) -> str:
    """Prefer polished LLM prose over raw engine English."""
    for part in (
        love_narr,
        str(pro.get("verdict") or "").strip(),
        str(pro.get("hidden_truth") or "").strip(),
        _chapter_body(pro, "blueprint_reality"),
    ):
        if len((part or "").strip()) >= 40:
            return part.strip()
    return ""


def _insights_from_pro(pro: dict[str, Any], *, max_items: int = 4) -> list[str]:
    out: list[str] = []
    for row in pro.get("deep_analysis") or []:
        if not isinstance(row, dict):
            continue
        expl = str(row.get("explanation") or "").strip()
        if len(expl) >= 24:
            out.append(_short(expl, 120))
        if len(out) >= max_items:
            return out
    for bucket in ("special", "damage", "practical"):
        for item in pro.get(bucket) or []:
            t = str(item or "").strip()
            if len(t) >= 16:
                out.append(_short(t, 120))
            if len(out) >= max_items:
                return out
    return out


def _already_localized(text: str, lang: str) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    try:
        from i18n_summary import prose_fully_hindi, prose_fully_hinglish

        if lang == "hi":
            return prose_fully_hindi(t)
        if lang == "hn":
            return prose_fully_hinglish(t)
    except Exception:
        if lang == "hi":
            return len(re.findall(r"[\u0900-\u097F]", t)) >= 12
        if lang == "hn":
            if re.search(r"[\u0900-\u097F]", t[:400]):
                return True
            return bool(re.search(
                r"\b(aap|rishte|kya|hai|hain|nahi|pyar|saath|dono|yeh|aur|mein|main)\b",
                t,
                re.I,
            ))
    return True


def _localize_prose_block(text: str, lang: str, *, force: bool = False) -> str:
    if lang not in ("hn", "hi"):
        return text
    raw = (text or "").strip()
    if not raw:
        return text
    if not force and _already_localized(raw, lang):
        return text
    try:
        if force:
            from i18n_summary import localize_text_force

            return localize_text_force(raw, lang)
        from i18n_summary import localize_text
    except Exception:
        return text
    return localize_text(raw, None, lang)


def localize_love_pdf_context(ctx: dict[str, Any], lang: str) -> dict[str, Any]:
    """Translate in-app section bodies (Moon Sync, Root Cause, Blueprint) for hn/hi."""
    if lang not in ("hn", "hi") or not isinstance(ctx, dict):
        return ctx
    out = dict(ctx)

    bp = dict(out.get("page2_3_blueprint") or {})
    for key in ("part1", "part2"):
        if not bp.get(key):
            continue
        raw = str(bp[key]).strip()
        if lang == "hi" and key == "part2" and _already_localized(raw, lang) and len(raw.split()) >= 80:
            bp[key] = raw
        else:
            bp[key] = _localize_prose_block(raw, lang)
    out["page2_3_blueprint"] = bp

    moon = dict(out.get("page5_moon") or {})
    if moon.get("body"):
        raw_moon = str(moon["body"]).strip()
        if lang == "hi" and _already_localized(raw_moon, lang) and len(raw_moon.split()) >= 55:
            moon["body"] = raw_moon
        else:
            moon["body"] = _localize_prose_block(raw_moon, lang)
    out["page5_moon"] = moon

    if out.get("page6_root_cause"):
        raw_root = str(out["page6_root_cause"]).strip()
        if lang == "hi" and _already_localized(raw_root, lang) and len(raw_root.split()) >= 80:
            out["page6_root_cause"] = raw_root
        else:
            out["page6_root_cause"] = _localize_prose_block(raw_root, lang)

    loyalty = dict(out.get("page7_loyalty") or {})
    for key in ("body", "summary", "behavior"):
        if loyalty.get(key):
            loyalty[key] = _localize_prose_block(str(loyalty[key]), lang)
    out["page7_loyalty"] = loyalty

    rf = dict(out.get("page8_red_flags") or {})
    if rf.get("body"):
        rf["body"] = _localize_prose_block(str(rf["body"]), lang)
    if isinstance(rf.get("bullets"), list):
        rf["bullets"] = [
            _localize_prose_block(str(b), lang)
            for b in rf["bullets"]
            if str(b).strip()
        ]
    out["page8_red_flags"] = rf

    if out.get("page9_harmony"):
        out["page9_harmony"] = _localize_prose_block(str(out["page9_harmony"]), lang)

    for page_key, body_key in (
        ("page10_dasha", "body"),
        ("page11_roadmap", "body"),
        ("page12_remedies", "body"),
        ("page13_checklist", "body"),
    ):
        block = dict(out.get(page_key) or {})
        if block.get(body_key):
            block[body_key] = _localize_prose_block(str(block[body_key]), lang)
        if isinstance(block.get("bullets"), list):
            block["bullets"] = [
                _localize_prose_block(str(b), lang)
                for b in block["bullets"]
                if str(b).strip()
            ]
        out[page_key] = block

    if out.get("page14_closing"):
        out["page14_closing"] = _localize_prose_block(str(out["page14_closing"]), lang)

    return out


def build_love_reality_page1_data(
    ctx: dict[str, Any],
    bundle: dict[str, Any],
    pro: dict[str, Any],
    p1: dict[str, Any],
    p2: dict[str, Any],
    *,
    lang: str = "en",
    report_id: str | None = None,
) -> dict[str, Any]:
    """Dashboard dict for premium PDF page 1."""
    from vedic.love_reality.pdf_locale import normalize_love_reality_pdf_lang

    lang = normalize_love_reality_pdf_lang(lang)
    localized = lang in ("hn", "hi")
    dash = ctx.get("page1_dashboard") or {}
    scores = dash.get("scores") or []

    def pick(label: str) -> dict | None:
        ll = label.lower()
        for row in scores:
            if ll in str(row.get("label") or "").lower():
                return row
        return None

    def num(row: dict | None) -> int:
        try:
            return int(str((row or {}).get("value") or "0"))
        except (TypeError, ValueError):
            return 0

    dims = {d.get("key"): int(d.get("score") or 0) for d in (ctx.get("page4_dimensions") or [])}
    love = num(pick("Love")) or int(dash.get("love_score") or 0)
    breakup = num(pick("Breakup"))
    loyalty = num(pick("Loyalty"))
    reunion = num(pick("Return"))

    lc = bundle.get("love_compatibility") or {}
    bu = bundle.get("breakup_chances") or {}
    ly = bundle.get("loyalty_check") or {}
    wr = bundle.get("will_return") or {}
    fo = bundle.get("future_outcome") or {}

    love_narr = _chapter_body(pro, "love_connection")
    loyalty_narr = _chapter_body(pro, "loyalty")
    breakup_narr = _chapter_body(pro, "breakup")
    future_narr = _chapter_body(pro, "future_outcome")
    llm_summary = _llm_summary_text(pro, love_narr)

    if localized and llm_summary:
        summary = llm_summary
    else:
        summary = (
            llm_summary
            or dash.get("summary_index")
            or lc.get("emotional_summary")
            or lc.get("insight")
            or "Your charts show a complex bond with strong pull and recurring friction windows."
        )

    snapshot = _short(love_narr or llm_summary or summary, 280)
    ai_bit = _short(pro.get("verdict") or bundle.get("narrative_bridge") or "", 160)
    narrative = snapshot
    if ai_bit and ai_bit not in snapshot:
        narrative = f"{snapshot} {ai_bit}".strip()

    moon = ctx.get("page5_moon") or {}
    insights: list[str] = []
    if localized:
        insights = _insights_from_pro(pro, max_items=4)
    if not insights:
        for r in (lc.get("reasons") or [])[:2]:
            insights.append(str(r).strip())
        if moon.get("shashtashtak"):
            if lang == "hn":
                insights.append(
                    "Moon rhythm mismatch — emotional pace alag hai, stress pe jaldi naam do."
                )
            elif lang == "hi":
                insights.append("चंद्र लय मेल नहीं — भावनात्मक गति अलग है।")
            else:
                insights.append(
                    "Moon rhythm mismatch — emotional pacing differs between partners."
                )
        else:
            if lang == "hn":
                insights.append(
                    "Moon signs smoother rhythm support karte hain jab stress jaldi naam ho."
                )
            elif lang == "hi":
                insights.append("चंद्र संकेत सहज भावनात्मक लय देते हैं।")
            else:
                insights.append(
                    "Moon signs support smoother emotional rhythm when stress is named early."
                )
        for r in (bu.get("reasons") or [])[:1]:
            insights.append(str(r).strip())
        if len(insights) < 4:
            if lang == "hn":
                insights.append(
                    "Jhagda ke 24–48 ghante mein repair karo — chup rehna loyalty ko kam karta hai."
                )
            elif lang == "hi":
                insights.append("झगड़े के २४–४८ घंटे में सुधार करें।")
            else:
                insights.append(
                    "Repair within 24–48 hours after conflict — silence erodes loyalty scores."
                )
    insights = [i for i in insights if i][:4]

    remedies = ctx.get("page12_remedies") or {}
    rem_bullets = remedies.get("bullets") if isinstance(remedies, dict) else []
    checklist = ctx.get("page13_checklist") or {}
    chk_bullets = checklist.get("bullets") if isinstance(checklist, dict) else []
    remedies_narr = str(pro.get("remedies_action_narrative") or "").strip()
    action_steps = [str(x).strip() for x in (pro.get("action_steps") or []) if str(x).strip()]
    practical = [str(p).strip() for p in (pro.get("practical") or []) if str(p).strip()]

    if remedies_narr and len(remedies_narr.split()) >= 55:
        rec_paragraphs = [p.strip() for p in remedies_narr.split("\n\n") if p.strip()]
        if len(rec_paragraphs) == 1:
            rec_paragraphs = [remedies_narr]
        raw_recs = [str(x).strip() for x in action_steps if str(x).strip()]
        recommendations = raw_recs[:7]
    else:
        raw_recs = [str(x).strip() for x in (rem_bullets or chk_bullets or []) if str(x).strip()]
        if practical:
            raw_recs = practical + raw_recs
        rec_paragraphs = practical[:2] if practical and any(len(p) > 100 for p in practical) else []

        if not raw_recs and not rec_paragraphs:
            if lang == "hn":
                raw_recs = [
                    "Har jhagda ke 24 ghante mein repair karo",
                    "Hafte mein 20 minute phone-free check-in",
                    "Dasha down window mein ultimatum mat do — patience rakho",
                ]
            elif lang == "hi":
                raw_recs = [
                    "हर झगड़े के २४ घंटे में सुधार करें",
                    "साप्ताहिक २० मिनट फोन-मुक्त बातचीत",
                    "कमज़ोर दशा में अल्टीमेटम न दें",
                ]
            else:
                raw_recs = [
                    "Repair within 24 hours after any argument",
                    "Weekly 20-minute phone-free check-in",
                    "Avoid ultimatums during strained dasha windows",
                ]
        recommendations = _to_concise_bullets(raw_recs, max_items=7, max_len=90)
    if not rec_paragraphs and remedies_narr:
        rec_paragraphs = [remedies_narr]
    elif not rec_paragraphs and practical:
        rec_paragraphs = practical[:2] if any(len(p) > 100 for p in practical) else []

    verdict_full = (
        (pro.get("verdict") or ctx.get("page14_closing") or "").strip()
        or (
            "आपके चार्ट एक जटिल बंध दिखाते हैं — इस रिपोर्ट को समय-मानचित्र की तरह पढ़ें, अंतिम फैसला नहीं।"
            if lang == "hi"
            else "Your charts show a complex bond — use this report as a timing map, not a final verdict."
        )
    )

    if lang == "hi":
        strengths = [
            {"label": "भावनात्मक आकर्षण", "value": min(100, love + 8)},
            {"label": "साझा विकास की इच्छा", "value": min(100, loyalty)},
            {"label": "कर्मिक खिंचाव", "value": dims.get("karmic") or 62},
            {"label": "आकर्षण अक्ष", "value": dims.get("attraction") or min(100, love)},
        ]
        challenges = [
            {"label": "संवाद में अंतर", "value": min(100, breakup)},
            {"label": "तनाव में विश्वास", "value": min(100, max(0, 100 - loyalty))},
            {"label": "समय की बेतालमेल", "value": min(100, 68 if reunion < 50 else 42)},
            {"label": "संघर्ष बढ़ना", "value": min(100, max(breakup, 100 - loyalty) // 2 + 20)},
        ]
    else:
        strengths = [
            {"label": "Emotional magnetism", "value": min(100, love + 8)},
            {"label": "Shared growth intent", "value": min(100, loyalty)},
            {"label": "Karmic pull", "value": dims.get("karmic") or 62},
            {"label": "Attraction axis", "value": dims.get("attraction") or min(100, love)},
        ]
        challenges = [
            {"label": "Communication gaps", "value": min(100, breakup)},
            {"label": "Trust under stress", "value": min(100, max(0, 100 - loyalty))},
            {"label": "Timing misalignment", "value": min(100, 68 if reunion < 50 else 42)},
            {"label": "Conflict escalation", "value": min(100, max(breakup, 100 - loyalty) // 2 + 20)},
        ]

    llm_da_by_key: dict[str, str] = {}
    llm_da = pro.get("deep_analysis")
    if isinstance(llm_da, list):
        for row in llm_da:
            if not isinstance(row, dict):
                continue
            key = str(row.get("key") or "").strip().lower()
            expl = str(row.get("explanation") or "").strip()
            if key and expl:
                llm_da_by_key[key] = expl

    def analysis(
        key: str,
        title: str,
        score: int,
        body: str,
        fallback: str,
    ) -> dict[str, Any]:
        llm_expl = llm_da_by_key.get(key, "")
        if len(llm_expl.split()) >= 40:
            explanation = llm_expl.strip()
        elif len(llm_expl) >= 40:
            explanation = llm_expl.strip()
        else:
            explanation = _short(body or fallback, 280)
        return {
            "title": title,
            "score": score,
            "explanation": explanation,
        }

    page1 = {
        "report_id": report_id or f"LR-{uuid.uuid4().hex[:8].upper()}",
        "generated_at": datetime.now(timezone.utc).strftime("%d %B %Y · %H:%M UTC"),
        "p1_name": p1.get("name") or "Partner A",
        "p2_name": p2.get("name") or "Partner B",
        "cosmic_score": int(dash.get("love_score") or love),
        "relationship_summary": _short(summary, 220),
        "metrics": (
            [
                {
                    "label": "प्रेम अनुकूलता",
                    "value": love,
                    "interpretation": (pick("Love") or {}).get("band") or "चार्टों में भावनात्मक मेल",
                },
                {
                    "label": "ब्रेकअप जोखिम",
                    "value": breakup,
                    "interpretation": (pick("Breakup") or {}).get("band") or "तनाव से अलग होने की संभावना",
                },
                {
                    "label": "निष्ठा और विश्वास",
                    "value": loyalty,
                    "interpretation": (pick("Loyalty") or {}).get("band") or "दबाव में प्रतिबद्धता",
                },
                {
                    "label": "पुनर्मिलन की संभावना",
                    "value": reunion,
                    "interpretation": (pick("Return") or {}).get("band") or "अलग होने पर वापसी की खिड़की",
                },
            ]
            if lang == "hi"
            else [
                {
                    "label": "Love Compatibility",
                    "value": love,
                    "interpretation": (pick("Love") or {}).get("band") or "Emotional resonance across charts",
                },
                {
                    "label": "Breakup Risk",
                    "value": breakup,
                    "interpretation": (pick("Breakup") or {}).get("band") or "Stress-trigger separation probability",
                },
                {
                    "label": "Loyalty & Trust",
                    "value": loyalty,
                    "interpretation": (pick("Loyalty") or {}).get("band") or "Commitment under pressure",
                },
                {
                    "label": "Reunion Chance",
                    "value": reunion,
                    "interpretation": (pick("Return") or {}).get("band") or "Return window if separated",
                },
            ]
        ),
        "insights_narrative": _short(narrative, 200),
        "key_insights": insights[:3],
        "analysis": (
            [
                analysis(
                    "emotional",
                    "भावनात्मक अनुकूलता",
                    dims.get("emotional") or max(0, min(100, int(love * 0.9))),
                    love_narr,
                    "भावनाएँ गहरी हैं पर गति अलग है — जरूरतें जल्दी साझा करें।",
                ),
                analysis(
                    "communication",
                    "संवाद",
                    dims.get("communication") or max(20, 100 - breakup),
                    breakup_narr,
                    "सीधे और अप्रत्यक्ष अंदाज़ तनाव में टकराते हैं — संवेदनशील विषयों पर शांत स्वर रखें।",
                ),
                analysis(
                    "trust",
                    "विश्वास और निष्ठा",
                    loyalty,
                    loyalty_narr,
                    "निरंतरता से विश्वास बना रहता है; छिपा बोझ खुले संघर्ष से ज्यादा नुकसान करता है।",
                ),
                analysis(
                    "long_term",
                    "दीर्घकालिक संभावना",
                    dims.get("stability") or max(0, min(100, (love + loyalty) // 2)),
                    future_narr,
                    "साझा अनुष्ठानों से चल सकता है — सुधार की आदत नहीं तो चक्र दोहरते हैं।",
                ),
            ]
            if lang == "hi"
            else [
                analysis(
                    "emotional",
                    "Emotional Compatibility",
                    dims.get("emotional") or max(0, min(100, int(love * 0.9))),
                    love_narr,
                    "Feelings run deep but peak at different speeds — name needs early.",
                ),
                analysis(
                    "communication",
                    "Communication",
                    dims.get("communication") or max(20, 100 - breakup),
                    breakup_narr,
                    "Direct vs indirect styles clash under stress — use calm voice for sensitive topics.",
                ),
                analysis(
                    "trust",
                    "Trust & Loyalty",
                    loyalty,
                    loyalty_narr,
                    "Trust holds with consistency; hidden resentment erodes loyalty faster than open conflict.",
                ),
                analysis(
                    "long_term",
                    "Long-Term Potential",
                    dims.get("stability") or max(0, min(100, (love + loyalty) // 2)),
                    future_narr,
                    "Workable with shared rituals — without repair habits, cycles repeat every 6–8 months.",
                ),
            ]
        ),
        "strengths": strengths,
        "challenges": challenges,
        "verdict": verdict_full,
        "recommendations": recommendations,
        "recommendation_paragraphs": rec_paragraphs,
    }
    return _localize_page1_dashboard(page1, lang)


def _localize_page1_dashboard(page1: dict[str, Any], lang: str) -> dict[str, Any]:
    """Roman Hinglish / Devanagari for in-app summary when engine text is still English."""
    if lang not in ("hn", "hi"):
        return page1
    try:
        from i18n_summary import localize_text_force
    except Exception:
        return page1

    out = dict(page1)
    for key in ("relationship_summary", "insights_narrative", "verdict"):
        val = str(out.get(key) or "").strip()
        if val:
            out[key] = _short(localize_text_force(val, lang), 420 if key == "verdict" else 220)

    bullets = []
    for item in out.get("key_insights") or []:
        raw = str(item or "").strip()
        if raw:
            bullets.append(_short(localize_text_force(raw, lang), 120))
    if bullets:
        out["key_insights"] = bullets

    recs = []
    for item in out.get("recommendations") or []:
        raw = str(item or "").strip()
        if not raw:
            continue
        if lang == "hi" and _already_localized(raw, lang):
            recs.append(raw)
        else:
            recs.append(_short(localize_text_force(raw, lang), 160))
    if recs:
        out["recommendations"] = recs

    paras = []
    for item in out.get("recommendation_paragraphs") or []:
        raw = str(item or "").strip()
        if not raw:
            continue
        if lang == "hi" and _already_localized(raw, lang) and len(raw.split()) >= 70:
            paras.append(raw)
        else:
            paras.append(localize_text_force(raw, lang))
    if paras:
        out["recommendation_paragraphs"] = paras

    metrics = []
    for row in out.get("metrics") or []:
        if not isinstance(row, dict):
            continue
        m = dict(row)
        interp = str(m.get("interpretation") or "").strip()
        if interp:
            m["interpretation"] = localize_text_force(interp, lang)
        metrics.append(m)
    if metrics:
        out["metrics"] = metrics

    analysis_rows = []
    for row in out.get("analysis") or []:
        if not isinstance(row, dict):
            continue
        a = dict(row)
        expl = str(a.get("explanation") or "").strip()
        if expl:
            a["explanation"] = _short(localize_text_force(expl, lang), 420)
        analysis_rows.append(a)
    if analysis_rows:
        out["analysis"] = analysis_rows

    return out

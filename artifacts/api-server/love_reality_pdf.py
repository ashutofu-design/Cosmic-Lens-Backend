"""
Love Reality Pro PDF renderer — Milan-style layout, love/partner focus (~14-16 pages).
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from milan_pdf import (
    BRAND_GOLD,
    BRAND_PURPLE,
    TEXT_DARK,
    TEXT_MID,
    TEXT_SOFT,
    CHAPTER_BODY_KEY,
    _chapter_eyebrow,
    _chapter_title_block,
    _ensure_native_pdf_fonts_registered,
    _font_pair,
    _gold_rule,
    _grounding_card,
    _hex,
    _latinize_pdf_plain,
    _on_page,
    _premium_body_multi_paragraph_table,
    _premium_consultation_blocks_page,
    _pro_chapter_pages,
    _pro_final_verdict_page,
    _safe,
    _styles,
)
from vedic.love_reality.chart_facts import enrich_bundle_for_pdf
from vedic.love_reality import pdf_locale as LRL
from vedic.love_reality.pdf_locale import love_reality_pdf_render_lang
from vedic.love_reality.pdf_text_safe import sanitize_love_reality_pro_premium


def _lr_cover_page(s: dict, p1: dict, p2: dict, love_score: int, lang: str) -> list[Any]:
    H_REG, H_BOLD = _font_pair(lang)
    out: list[Any] = []
    out.append(Spacer(1, 10 * mm))
    out.append(
        Paragraph(
            f"<font color='{_hex(BRAND_GOLD)}'><b>COSMIC LENS</b></font>",
            ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=11, leading=15, alignment=TA_CENTER),
        ),
    )
    out.append(_gold_rule(52))
    out.append(Spacer(1, 10))
    out.append(
        Paragraph(
            LRL.cover_title(lang),
            ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=24, leading=30, alignment=TA_CENTER, textColor=BRAND_PURPLE),
        ),
    )
    out.append(
        Paragraph(
            f"<font color='{_hex(TEXT_SOFT)}'>{_safe(LRL.cover_subtitle(lang))}</font>",
            ParagraphStyle("sub", fontName=H_REG, fontSize=11, leading=15, alignment=TA_CENTER, spaceAfter=14),
        ),
    )
    out.append(
        Paragraph(
            f"<b>{_safe(p1.get('name'))}</b><font color='{_hex(TEXT_SOFT)}'>  ·  </font>"
            f"<b>{_safe(p2.get('name'))}</b>",
            ParagraphStyle("names", fontName=H_BOLD, fontSize=22, leading=28, alignment=TA_CENTER),
        ),
    )
    out.append(Spacer(1, 8))
    score_card = Table(
        [[Paragraph(
            f"<b>{love_score}</b><font color='{_hex(TEXT_SOFT)}' size=16> / 100</font>",
            ParagraphStyle("sc", fontName="Helvetica-Bold", fontSize=44, alignment=TA_CENTER, textColor=BRAND_PURPLE),
        )]],
        colWidths=[110 * mm],
    )
    score_card.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
    ]))
    out.append(score_card)
    out.append(
        Paragraph(
            f"<font color='{_hex(TEXT_MID)}'>{LRL.cover_generated_prefix(lang)} "
            f"{datetime.utcnow().strftime('%d %B %Y')}</font>",
            ParagraphStyle("dt", fontName=H_REG, fontSize=10, alignment=TA_CENTER, spaceBefore=12),
        ),
    )
    out.append(PageBreak())
    return out


def _lr_snapshot_page(s: dict, num: int, bundle: dict, pro: dict, lang: str) -> list[Any]:
    lc = bundle.get("love_compatibility") or {}
    score = int(lc.get("score") or 0)
    insight = (lc.get("insight") or "").strip()
    hidden = (pro.get("hidden_truth") or "").strip()
    open_txt = insight or hidden or (
        f"Your love compatibility reads at {score}/100 — a starting lens for the deeper chapters that follow."
    )
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "SNAPSHOT", lang))
    out.extend(_chapter_title_block(LRL.snapshot_title(lang), LRL.snapshot_subtitle(lang), s))
    out.append(_premium_body_multi_paragraph_table(s, open_txt, relax=True))
    out.append(PageBreak())
    return out


def _lr_score_breakdown_page(s: dict, num: int, bundle: dict, love_score: int, lang: str) -> list[Any]:
    lc = bundle.get("love_compatibility") or {}
    ledger = lc.get("score_ledger") or []
    H_REG, _ = _font_pair(lang)
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "SCORE", lang))
    out.extend(_chapter_title_block(LRL.score_breakdown_title(lang), LRL.score_breakdown_subtitle(lang), s))
    if not ledger:
        out.append(
            _premium_body_multi_paragraph_table(
                s,
                LRL.score_ledger_fallback(lang, love_score),
                relax=True,
            )
        )
    else:
        rows: list[list[Any]] = []
        for row in ledger:
            if not isinstance(row, dict):
                continue
            label = _safe(str(row.get("label") or ""))
            delta = row.get("delta")
            note = _safe(str(row.get("note") or ""))
            delta_txt = ""
            if row.get("base") is not None:
                delta_txt = str(int(row["base"]))
            elif delta is not None:
                try:
                    d = float(delta)
                    delta_txt = f"+{int(d)}" if d > 0 else str(int(d))
                except (TypeError, ValueError):
                    delta_txt = str(delta)
            rows.append([
                Paragraph(
                    f"<b>{label}</b><br/><font color='{_hex(TEXT_SOFT)}' size=9>{note}</font>",
                    ParagraphStyle("sl", fontName=H_REG, fontSize=10, leading=13, textColor=TEXT_DARK),
                ),
                Paragraph(
                    f"<b>{delta_txt}</b>" if delta_txt else "—",
                    ParagraphStyle("sd", fontName="Helvetica-Bold", fontSize=11, alignment=TA_CENTER, textColor=BRAND_PURPLE),
                ),
            ])
        tbl = Table(rows, colWidths=[145 * mm, 35 * mm])
        tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -2), 0.25, TEXT_SOFT),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        out.append(tbl)
        out.append(Spacer(1, 10))
        out.append(
            Paragraph(
                f"<b>Final score: {love_score} / 100</b>",
                ParagraphStyle("fin", fontName="Helvetica-Bold", fontSize=14, textColor=BRAND_PURPLE, spaceBefore=6),
            )
        )
    out.append(PageBreak())
    return out


def _lr_chart_snapshot_page(s: dict, num: int, bundle: dict, lang: str) -> list[Any]:
    snap = bundle.get("chart_snapshot") or {}
    lines = snap.get("lines") or []
    body = "\n".join(str(ln) for ln in lines if ln)
    if not body.strip():
        body = LRL.chart_snapshot_fallback(lang)
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "CHART", lang))
    out.extend(_chapter_title_block(LRL.chart_snapshot_title(lang), LRL.chart_snapshot_subtitle(lang), s))
    out.append(_premium_body_multi_paragraph_table(s, body, relax=True))
    bridge = (bundle.get("narrative_bridge") or "").strip()
    if bridge:
        out.append(Spacer(1, 8))
        out.append(_grounding_card(s, _latinize_pdf_plain(bridge, lang), title=LRL.timing_note_title(lang)))
    out.append(PageBreak())
    return out


def _lr_method_note_page(s: dict, num: int, lang: str) -> list[Any]:
    """Transparency note — advanced chart-based analysis (no AI/LLM mention)."""
    H_REG, _ = _font_pair(lang)
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "NOTE", lang))
    out.extend(_chapter_title_block(LRL.method_note_title(lang), "", s))
    out.append(
        _premium_body_multi_paragraph_table(
            s, LRL.method_note_body(lang), relax=True,
        )
    )
    out.append(PageBreak())
    return out


def _lr_closing_page(s: dict, lang: str) -> list[Any]:
    """Love Reality closing — never mentions AI/LLM."""
    H_REG, H_BOLD = _font_pair(lang)
    out: list[Any] = []
    out.append(Spacer(1, 50 * mm))
    out.append(
        Paragraph(
            f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(LRL.closing_thanks(lang))}</b></font>",
            ParagraphStyle(
                "lr_close_h", fontName=H_BOLD, fontSize=26, leading=32,
                alignment=TA_CENTER, spaceAfter=10,
            ),
        ),
    )
    out.append(
        Paragraph(
            f"<font color='{_hex(TEXT_MID)}'>{_safe(LRL.closing_body(lang))}</font>",
            ParagraphStyle(
                "lr_close_b", fontName=H_REG, fontSize=11, leading=17,
                alignment=TA_CENTER, spaceAfter=24,
            ),
        ),
    )
    out.append(Spacer(1, 30 * mm))
    out.append(
        Paragraph(
            f"<font color='{_hex(TEXT_SOFT)}'>{_safe(LRL.closing_footer(lang))}</font>",
            ParagraphStyle(
                "lr_close_meta", fontName=H_REG, fontSize=8, leading=11, alignment=TA_CENTER,
            ),
        ),
    )
    return out


def _lr_hidden_truth_page(s: dict, num: int, text: str, lang: str) -> list[Any]:
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "INSIGHT", lang))
    out.extend(_chapter_title_block(LRL.hidden_truth_title(lang), "", s))
    body = (text or "").strip() or " "
    out.append(_premium_body_multi_paragraph_table(s, body, relax=False))
    out.append(PageBreak())
    return out


def render_love_reality_pro_pdf(payload: dict, lang: str = "en") -> bytes:
    lang = love_reality_pdf_render_lang(lang)
    _ensure_native_pdf_fonts_registered(lang)
    payload = payload or {}
    p1 = payload.get("p1") or {}
    p2 = payload.get("p2") or {}
    bundle = payload.get("engines") or payload
    if isinstance(bundle, dict) and not bundle.get("chart_snapshot"):
        bundle = enrich_bundle_for_pdf(bundle)
    pro = sanitize_love_reality_pro_premium(
        payload.get("pro_premium") or {},
        bundle if isinstance(bundle, dict) else None,
    )
    lc = bundle.get("love_compatibility") or payload.get("love_compatibility") or {}
    love_score = int(lc.get("score") or 0)

    s = _styles(lang)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=f"Love Reality Pro — {p1.get('name', '?')} & {p2.get('name', '?')}",
        author="Cosmic Lens",
    )

    chapters_in = pro.get("chapters") or []
    by_key = {(c.get("key") or "").strip().lower(): c for c in chapters_in if isinstance(c, dict)}

    story: list[Any] = []
    page = 1

    story.extend(_lr_cover_page(s, p1, p2, love_score, lang))
    page += 1

    story.extend(_lr_snapshot_page(s, page, bundle, pro, lang))
    page += 1

    story.extend(_lr_score_breakdown_page(s, page, bundle, love_score, lang))
    page += 1

    story.extend(_lr_chart_snapshot_page(s, page, bundle, lang))
    page += 1

    story.extend(
        _lr_hidden_truth_page(
            s,
            page,
            _latinize_pdf_plain(pro.get("hidden_truth") or "", lang),
            lang,
        )
    )
    page += 1

    placeholder = LRL.chapter_placeholder(lang)
    engine_ground = bundle.get("chapter_groundings") or {}
    for i, (key, eyebrow, title, subtitle) in enumerate(LRL.pro_chapter_rows(lang), start=1):
        ch = dict(by_key.get(key) or {})
        if not ch.get(CHAPTER_BODY_KEY) and not ch.get("full_read"):
            ch[CHAPTER_BODY_KEY] = placeholder
        if not str(ch.get("grounding") or "").strip():
            eg = engine_ground.get(key)
            if eg:
                ch["grounding"] = _latinize_pdf_plain(eg, lang)
        story.extend(_pro_chapter_pages(s, page, page, eyebrow, title, subtitle, ch))
        page += 1

    special = [
        _latinize_pdf_plain(str(b), lang)
        for b in (pro.get("special") or [])
        if b
    ][:3]
    if not special:
        special = ["A genuine emotional pull remains active between you when stress is named early."]
    story.extend(
        _premium_consultation_blocks_page(
            s, page, "STRENGTH", LRL.special_title(lang), "", special,
        )
    )
    page += 1

    damage = [b for b in (pro.get("damage") or []) if b][:2]
    if not damage:
        damage = ["Unspoken resentment can stack if repair is always delayed to the next day."]
    story.extend(
        _premium_consultation_blocks_page(
            s, page, "RISK", LRL.damage_title(lang), "", damage,
        )
    )
    page += 1

    practical = [
        _latinize_pdf_plain(str(p), lang)
        for p in (pro.get("practical") or [])
        if p
    ][:2]
    if not practical:
        practical = ["Daily rhythms matter: who reaches out first after friction shapes the whole bond."]
    story.extend(
        _premium_consultation_blocks_page(
            s, page, "LIFE", LRL.practical_title(lang), "", practical,
        )
    )
    page += 1

    verdict = _latinize_pdf_plain((pro.get("verdict") or "").strip(), lang)
    if not verdict.strip():
        verdict = _latinize_pdf_plain((bundle.get("narrative_bridge") or "").strip(), lang)
    story.extend(
        _pro_final_verdict_page(
            s, page, verdict, love_score, 100,
            p1_name=p1.get("name") or "You",
            p2_name=p2.get("name") or "Partner",
        )
    )
    page += 1
    story.extend(_lr_method_note_page(s, page, lang))
    story.extend(_lr_closing_page(s, lang))

    doc.milan_pdf_lang = lang
    doc.milan_pdf_footer_pro = True
    doc.milan_pdf_footer_center = LRL.footer_label(lang)

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

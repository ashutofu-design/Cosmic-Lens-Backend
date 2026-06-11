"""
Love Reality Pro PDF renderer — 14-page premium layout (v2).
"""
from __future__ import annotations

import io
import logging
import os
from datetime import datetime
from typing import Any

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from milan_pdf import (
    _premium_body_markup,
    BRAND_GOLD,
    BRAND_PURPLE,
    TEXT_DARK,
    TEXT_MID,
    TEXT_SOFT,
    _chapter_eyebrow,
    _chapter_title_block,
    _ensure_native_pdf_fonts_registered,
    _font_pair,
    _gold_rule,
    _hex,
    _latinize_pdf_plain,
    _on_page,
    _pick_body_premium,
    _premium_body_multi_paragraph_table,
    _safe,
    _styles,
)
from vedic.love_reality.pdf_fonts import hindi_font_pair, require_devanagari_fonts
from vedic.love_reality.chart_facts import enrich_bundle_for_pdf
from vedic.love_reality import pdf_locale as LRL
from vedic.love_reality.pdf_data_v2 import build_love_reality_pdf_v2_context
from vedic.love_reality.pdf_page1_data import build_love_reality_page1_data
from vedic.love_reality.pdf_page1_premium import (
    render_deep_analysis_page2_flowables,
    render_premium_page1_flowables,
)
try:
    from vedic.love_reality.pdf_page1_premium import render_verdict_page_flowables
except ImportError:
    render_verdict_page_flowables = None  # type: ignore[assignment,misc]
from vedic.love_reality.pdf_toc import render_love_reality_toc_flowables
from vedic.love_reality.pdf_locale import love_reality_pdf_render_lang
from vedic.love_reality.pdf_text_safe import sanitize_love_reality_pro_premium

_log = logging.getLogger(__name__)

_last_page1_style = "unknown"


def get_last_page1_style() -> str:
    return _last_page1_style


def _love_reality_doc_template(buf: io.BytesIO, title: str, lang: str) -> SimpleDocTemplate:
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=title,
        author="Cosmic Lens",
    )
    doc.milan_pdf_lang = lang
    doc.milan_pdf_footer_pro = True
    doc.milan_pdf_footer_center = LRL.footer_label(lang)
    return doc


def render_love_reality_exec_summary_only_pdf(payload: dict, lang: str = "en") -> bytes:
    """
    Executive summary (Page 1 content) only — same ReportLab auto-pagination as production.
    Used for local preview; content may span multiple PDF pages before deep analysis.
    """
    from vedic.love_reality.pdf_locale import normalize_love_reality_pdf_lang

    payload = payload or {}
    content_lang = normalize_love_reality_pdf_lang(payload.get("pdf_lang") or lang)
    lang = love_reality_pdf_render_lang(content_lang)
    require_devanagari_fonts(content_lang)
    _ensure_native_pdf_fonts_registered(lang)
    if content_lang == "hi":
        reg, bold = hindi_font_pair()
        _log.info("[love_reality_pdf] hindi_font_pair regular=%s bold=%s", reg, bold)
    p1 = payload.get("p1") or {}
    p2 = payload.get("p2") or {}
    bundle = payload.get("engines") or payload
    if isinstance(bundle, dict) and not bundle.get("chart_snapshot"):
        bundle = enrich_bundle_for_pdf(bundle)
    pro = sanitize_love_reality_pro_premium(
        payload.get("pro_premium") or {},
        bundle if isinstance(bundle, dict) else None,
        lang=content_lang,
    )
    ctx = build_love_reality_pdf_v2_context(bundle, pro, p1, p2, lang)
    report_id = str(payload.get("report_id") or "LR-PREVIEW")
    page1_data = build_love_reality_page1_data(
        ctx, bundle, pro, p1, p2, lang=content_lang, report_id=report_id
    )
    story = render_premium_page1_flowables(page1_data, lang=lang)
    story = [f for f in story if not isinstance(f, PageBreak)]

    buf = io.BytesIO()
    title = f"Love Reality Pro — {p1.get('name', '?')} & {p2.get('name', '?')}"
    doc = _love_reality_doc_template(buf, title, lang)
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


def _section_page(
    s: dict,
    page_num: int,
    eyebrow: str,
    title: str,
    subtitle: str,
    body: str,
    *,
    lang: str,
    bullets: list[str] | None = None,
    table_rows: list[list[str]] | None = None,
) -> list[Any]:
    H_REG, H_BOLD = _font_pair(lang)
    out: list[Any] = []
    out.append(_chapter_eyebrow(page_num, eyebrow, lang))
    out.extend(_chapter_title_block(title, subtitle, s))
    text = _latinize_pdf_plain((body or "").strip(), lang)
    if text:
        out.append(_premium_body_multi_paragraph_table(s, text, relax=True))
    if table_rows:
        cells: list[list[Any]] = []
        for row in table_rows:
            c0 = str(row[0] if row else "")
            c1 = str(row[1] if len(row) > 1 else "")
            c2 = str(row[2] if len(row) > 2 else "")
            tbl_bold = ParagraphStyle(
                "tbl_bold",
                parent=_pick_body_premium(c0, s, lang, relax=True),
                fontName=H_BOLD,
            )
            cells.append([
                Paragraph(_safe(c0), tbl_bold),
                Paragraph(
                    _premium_body_markup(c1, lang) or _safe(c1),
                    _pick_body_premium(c1, s, lang, relax=True),
                ),
                Paragraph(
                    _premium_body_markup(c2, lang) or _safe(c2),
                    _pick_body_premium(c2, s, lang, relax=True),
                ),
            ])
        tbl = Table(cells, colWidths=[78 * mm, 28 * mm, 74 * mm])
        tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -2), 0.25, TEXT_SOFT),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        out.append(tbl)
    if bullets:
        out.append(Spacer(1, 6))
        for b in bullets:
            plain = _latinize_pdf_plain(b, lang)
            bullet_style = _pick_body_premium(plain, s, lang, relax=True)
            bullet_style.leftIndent = 8
            bullet_style.spaceAfter = 3
            bullet_mk = _premium_body_markup(f"• {plain}", lang) or f"• {_safe(plain)}"
            out.append(Paragraph(bullet_mk, bullet_style))
    out.append(PageBreak())
    return out


def _verdict_page_fallback(data: dict[str, Any], lang: str) -> list[Any]:
    """Stubs Section 02 when pdf_page1_premium on server is behind love_reality_pdf."""
    verdict = str(data.get("verdict") or "").strip()
    recs = data.get("recommendation_paragraphs") or data.get("recommendations") or []
    if isinstance(recs, list):
        extra = "\n\n".join(str(x) for x in recs if str(x).strip())
        if extra:
            verdict = (verdict + "\n\n" + extra).strip() if verdict else extra
    if not verdict:
        verdict = "Chart-derived compatibility summary for this couple."
    _log.warning("[love_reality_pdf] render_verdict_page_flowables missing — using fallback page")
    return _section_page(
        _styles(lang),
        2,
        "VERDICT",
        "Astrologer's Note",
        "Unified interpretation for this bond",
        verdict,
        lang=lang,
    )


def _cover_dashboard(s: dict, p1: dict, p2: dict, ctx: dict, lang: str) -> list[Any]:
    H_REG, H_BOLD = _font_pair(lang)
    dash = ctx["page1_dashboard"]
    love = dash["love_score"]
    out: list[Any] = []
    out.append(Spacer(1, 8 * mm))
    out.append(
        Paragraph(
            f"<font color='{_hex(BRAND_GOLD)}'>COSMIC LENS</font>",
            ParagraphStyle("brand", fontName=H_BOLD, fontSize=11, leading=15, alignment=TA_CENTER),
        ),
    )
    out.append(_gold_rule(52))
    out.append(
        Paragraph(
            "Love Reality Pro",
            ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=22, leading=28, alignment=TA_CENTER, textColor=BRAND_PURPLE),
        ),
    )
    out.append(
        Paragraph(
            f"{_safe(p1.get('name'))}  ·  {_safe(p2.get('name'))}",
            ParagraphStyle("nm", fontName=H_BOLD, fontSize=18, alignment=TA_CENTER, spaceAfter=10),
        ),
    )
    out.append(
        Paragraph(
            f"{love}<font color='{_hex(TEXT_SOFT)}'> / 100</font>  Cosmic Alignment Index",
            ParagraphStyle("sc", fontName=H_BOLD, fontSize=20, alignment=TA_CENTER, textColor=BRAND_PURPLE),
        ),
    )
    out.append(Spacer(1, 6))
    out.extend(_chapter_title_block(
        "Cosmic Alignment Scorecard",
        "Absolute summary index — all engine scores",
        s,
    ))
    if dash.get("summary_index"):
        out.append(_premium_body_multi_paragraph_table(s, dash["summary_index"], relax=True))
    rows = [[r["label"], r["value"], r["band"]] for r in dash["scores"]]
    cells: list[list[Any]] = []
    for row in rows:
        cells.append([
            Paragraph(_safe(row[0]), ParagraphStyle("c0", fontName=H_BOLD, fontSize=10, textColor=TEXT_DARK)),
            Paragraph(_safe(row[1]), ParagraphStyle("c1", fontName=H_BOLD, fontSize=11, textColor=BRAND_PURPLE, alignment=TA_CENTER)),
            Paragraph(_safe(row[2]), ParagraphStyle("c2", fontName=H_REG, fontSize=9, textColor=TEXT_SOFT)),
        ])
    tbl = Table(cells, colWidths=[78 * mm, 28 * mm, 74 * mm])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, TEXT_SOFT),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    out.append(tbl)
    out.append(
        Paragraph(
            f"<font color='{_hex(TEXT_MID)}'>{datetime.utcnow().strftime('%d %B %Y')}</font>",
            ParagraphStyle("dt", fontName=H_REG, fontSize=9, alignment=TA_CENTER, spaceBefore=10),
        ),
    )
    out.append(PageBreak())
    return out


    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


def render_love_reality_app_mirror_pdf(payload: dict, lang: str = "en") -> bytes:
    """
    WYSIWYG PDF — one section per in-app scroll card (same order, same text).
    Triggered when mobile sends app_sections from buildLoveReportSections().
    """
    from vedic.love_reality.pdf_locale import normalize_love_reality_pdf_lang

    payload = payload or {}
    content_lang = normalize_love_reality_pdf_lang(payload.get("pdf_lang") or lang)
    lang = love_reality_pdf_render_lang(content_lang)
    require_devanagari_fonts(content_lang)
    _ensure_native_pdf_fonts_registered(lang)

    p1 = payload.get("p1") or {}
    p2 = payload.get("p2") or {}
    sections = payload.get("app_sections") or []
    if not isinstance(sections, list):
        sections = []
    scores = payload.get("scores") if isinstance(payload.get("scores"), dict) else {}

    s = _styles(lang)
    H_REG, H_BOLD = _font_pair(lang)
    buf = io.BytesIO()
    doc = _love_reality_doc_template(
        buf,
        f"Love Reality Pro — {p1.get('name', '?')} & {p2.get('name', '?')}",
        lang,
    )
    story: list[Any] = []

    story.append(Spacer(1, 10 * mm))
    story.append(
        Paragraph(
            f"<font color='{_hex(BRAND_GOLD)}'>COSMIC LENS</font>",
            ParagraphStyle("brand", fontName=H_BOLD, fontSize=11, leading=15, alignment=TA_CENTER),
        ),
    )
    story.append(_gold_rule(52))
    story.append(
        Paragraph(
            "Love Reality Pro",
            ParagraphStyle("t", fontName=H_BOLD, fontSize=20, leading=26, alignment=TA_CENTER, textColor=BRAND_PURPLE),
        ),
    )
    story.append(
        Paragraph(
            f"{_safe(p1.get('name'))}  ·  {_safe(p2.get('name'))}",
            ParagraphStyle("nm", fontName=H_BOLD, fontSize=16, alignment=TA_CENTER, spaceAfter=8),
        ),
    )
    if scores:
        score_bits = [
            f"Love {int(scores.get('love') or 0)}",
            f"Breakup {int(scores.get('breakup') or 0)}",
            f"Loyalty {int(scores.get('loyalty') or 0)}",
            f"Return {int(scores.get('return') or 0)}",
            f"Future {int(scores.get('future') or 0)}",
        ]
        story.append(
            Paragraph(
                " · ".join(score_bits),
                ParagraphStyle("sc", fontName=H_REG, fontSize=10, alignment=TA_CENTER, textColor=TEXT_MID),
            ),
        )
    story.append(
        Paragraph(
            f"<font color='{_hex(TEXT_SOFT)}'>{datetime.utcnow().strftime('%d %B %Y')}</font>",
            ParagraphStyle("dt", fontName=H_REG, fontSize=9, alignment=TA_CENTER, spaceBefore=10),
        ),
    )
    story.append(PageBreak())

    for idx, sec in enumerate(sections):
        if not isinstance(sec, dict):
            continue
        title = str(sec.get("title") or "").strip()
        if not title:
            sid = str(sec.get("id") or "").strip()
            title = sid.replace("_", " ").strip().title() if sid else ""
        if not title:
            continue
        body = str(sec.get("body") or "").strip()
        bullets = sec.get("bullets") if isinstance(sec.get("bullets"), list) else None
        table_rows = sec.get("table_rows") or sec.get("tableRows")
        if not isinstance(table_rows, list):
            table_rows = None
        if not body and not bullets and not table_rows:
            continue
        num = idx + 1
        story.extend(_section_page(
            s,
            num,
            f"{num:02d}",
            title,
            str(sec.get("subtitle") or ""),
            body,
            lang=lang,
            bullets=bullets,
            table_rows=table_rows,
        ))

    while story and isinstance(story[-1], PageBreak):
        story.pop()

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            f"<font color='{_hex(TEXT_SOFT)}'>{_safe(LRL.closing_footer(lang))}</font>",
            ParagraphStyle("foot", fontName=H_REG, fontSize=8, leading=11, alignment=TA_CENTER),
        ),
    )

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


def render_love_reality_pro_pdf(payload: dict, lang: str = "en") -> bytes:
    from vedic.love_reality.pdf_locale import normalize_love_reality_pdf_lang

    payload = payload or {}
    app_sections = payload.get("app_sections")
    if isinstance(app_sections, list) and len(app_sections) > 0:
        return render_love_reality_app_mirror_pdf(payload, lang=lang)

    content_lang = normalize_love_reality_pdf_lang(payload.get("pdf_lang") or lang)
    lang = love_reality_pdf_render_lang(content_lang)
    require_devanagari_fonts(content_lang)
    _ensure_native_pdf_fonts_registered(lang)
    if content_lang == "hi":
        reg, bold = hindi_font_pair()
        _log.info("[love_reality_pdf] hindi_font_pair regular=%s bold=%s", reg, bold)
        if reg == "Helvetica":
            _log.error("[love_reality_pdf] hi_render Helvetica_fallback — Devanagari will show as boxes")
    p1 = payload.get("p1") or {}
    p2 = payload.get("p2") or {}
    bundle = payload.get("engines") or payload
    if isinstance(bundle, dict) and not bundle.get("chart_snapshot"):
        bundle = enrich_bundle_for_pdf(bundle)

    client_ctx = payload.get("pdf_context")
    client_page1 = payload.get("page1")
    use_client_layout = isinstance(client_ctx, dict) and bool(client_ctx)

    if use_client_layout:
        pro = payload.get("pro_premium") or {}
        if not isinstance(pro, dict):
            pro = {}
        ctx = client_ctx
    else:
        pro = sanitize_love_reality_pro_premium(
            payload.get("pro_premium") or {},
            bundle if isinstance(bundle, dict) else None,
            lang=content_lang,
        )
        ctx = build_love_reality_pdf_v2_context(bundle, pro, p1, p2, lang)
    if not use_client_layout and content_lang == "hi":
        from milan_pdf import _has_indic

        verdict_sample = str(pro.get("verdict") or "")[:120]
        _log.info(
            "[love_reality_pdf] hi_content verdict_sample=%r has_devanagari=%s",
            verdict_sample,
            _has_indic(verdict_sample),
        )
    s = _styles(lang)

    buf = io.BytesIO()
    doc = _love_reality_doc_template(
        buf,
        f"Love Reality Pro — {p1.get('name', '?')} & {p2.get('name', '?')}",
        lang,
    )

    story: list[Any] = []
    global _last_page1_style

    legacy_page1 = (os.environ.get("LOVE_REALITY_PDF_PAGE1_LEGACY") or "").strip().lower() in (
        "1", "true", "yes",
    )
    report_id = str(payload.get("report_id") or "").strip()

    # §0 Table of contents — always first physical PDF page
    story.extend(
        render_love_reality_toc_flowables(
            p1, p2, report_id=report_id, lang=lang, legacy_page1=legacy_page1,
        )
    )

    # §1 Premium dashboard
    if legacy_page1:
        _last_page1_style = "legacy-scorecard"
        story.extend(_cover_dashboard(s, p1, p2, ctx, lang))
    else:
        _last_page1_style = "premium-dashboard"
        if isinstance(client_page1, dict) and client_page1:
            page1_data = client_page1
        else:
            page1_data = build_love_reality_page1_data(
                ctx, bundle, pro, p1, p2, lang=lang, report_id=report_id or None,
            )
        story.extend(render_premium_page1_flowables(page1_data, lang=lang))
        if render_verdict_page_flowables is not None:
            story.extend(render_verdict_page_flowables(page1_data, lang=lang))
        else:
            story.extend(_verdict_page_fallback(page1_data, lang=lang))
        story.extend(render_deep_analysis_page2_flowables(page1_data, lang=lang))
        _log.info(
            "[love_reality_pdf] page1 renderer=%s report_id=%s",
            _last_page1_style,
            page1_data.get("report_id"),
        )

    bp = ctx["page2_3_blueprint"]
    story.extend(_section_page(
        s, 2, "BLUEPRINT", "Destiny Partner Blueprint (You)",
        "7th house · Upapada · Venus/Jupiter ideal signature",
        bp["part1"], lang=lang,
    ))
    story.extend(_section_page(
        s, 3, "REALITY", "Partner Blueprint vs Reality",
        "How actual partner nature compares to your chart ideal",
        bp["part2"], lang=lang,
    ))

    dim_rows = [
        [d["label"], f"{d['score']}/100", "Love dimension matrix"]
        for d in ctx["page4_dimensions"]
    ]
    story.extend(_section_page(
        s, 4, "DIMENSIONS", "The 5 Love Dimensions Deep-Dive",
        "Emotional · Attraction · Communication · Karmic · Stability",
        "Granular matrices from combined chart synastry — same bars as Basic mode.",
        lang=lang, table_rows=dim_rows,
    ))

    # §2 Triggers & Problems (5–8)
    moon = ctx["page5_moon"]
    moon_body = str(moon.get("body") or "").strip()
    story.extend(_section_page(
        s, 5, "MOON", "Moon Synastry & Emotional Rhythm",
        "Shashtashtak / 6-8 sign emotional alignment check",
        moon_body, lang=lang,
    ))

    story.extend(_section_page(
        s, 6, "ROOT CAUSE", "The Core Root Cause",
        "What is silently breaking you apart — ego, 12th house, Mercury, afflictions",
        ctx["page6_root_cause"], lang=lang,
    ))

    loyalty = ctx["page7_loyalty"]
    loy_rows = [[r["label"], r["value"], r["band"]] for r in loyalty["rows"]]
    story.extend(_section_page(
        s, 7, "LOYALTY", "Loyalty, Trust & Psychological Traits",
        loyalty.get("behavior") or "Behavioral stability dashboard",
        loyalty.get("body") or loyalty.get("summary") or "", lang=lang, table_rows=loy_rows,
    ))

    red_flags = ctx["page8_red_flags"]
    rf_body = red_flags.get("body") if isinstance(red_flags, dict) else ""
    rf_bullets = red_flags.get("bullets") if isinstance(red_flags, dict) else red_flags
    story.extend(_section_page(
        s, 8, "RED FLAGS", "Red Flags Matrix",
        "Core operational friction points",
        rf_body or "Chart-derived warning signals for this couple:",
        lang=lang, bullets=rf_bullets,
    ))

    # §3 Timelines (9–11)
    story.extend(_section_page(
        s, 9, "HARMONY", "The Harmony Formula",
        "Core behavioral shifts required — elemental mix solutions",
        ctx["page9_harmony"], lang=lang,
    ))

    dasha_ctx = ctx["page10_dasha"]
    if isinstance(dasha_ctx, dict):
        dasha_body = dasha_ctx.get("body") or ""
        dasha_lines = dasha_ctx.get("lines") or []
    else:
        dasha_body = ""
        dasha_lines = dasha_ctx if isinstance(dasha_ctx, list) else []
    if not dasha_body.strip():
        dasha_body = "Current and upcoming dasha alignment:"
    story.extend(_section_page(
        s, 10, "DASHA", "Vimshottari Dasha Synchronization",
        "Parallel time cycles for both partners",
        dasha_body,
        lang=lang, bullets=dasha_lines,
    ))

    roadmap_ctx = ctx["page11_roadmap"]
    if isinstance(roadmap_ctx, dict):
        roadmap_body = roadmap_ctx.get("body") or ""
        roadmap = roadmap_ctx.get("rows") or []
    else:
        roadmap_body = ""
        roadmap = roadmap_ctx if isinstance(roadmap_ctx, list) else []
    if not roadmap_body.strip():
        roadmap_body = "Month-by-month arc from Future + Return engines:"
    rm_rows = [
        [
            str(r.get("period") or "—"),
            str(r.get("trend") or "—"),
            str(r.get("note") or "")[:120],
        ]
        for r in roadmap
        if isinstance(r, dict)
    ]
    story.extend(_section_page(
        s, 11, "ROADMAP", "The 1–3 Year Chronological Roadmap",
        "3 months · 12 months · 36 months trend updates",
        roadmap_body,
        lang=lang, table_rows=rm_rows,
    ))

    # §4 Remedies & Close (12–14)
    remedies = ctx["page12_remedies"]
    rem_body = remedies.get("body") if isinstance(remedies, dict) else ""
    rem_bullets = remedies.get("bullets") if isinstance(remedies, dict) else remedies
    story.extend(_section_page(
        s, 12, "UPAY", "Planetary Counter Measures",
        "Customized structural remedies for afflicted planets",
        rem_body or "Personalized upay blocks — chart-balanced actions:",
        lang=lang, bullets=rem_bullets,
    ))

    checklist = ctx["page13_checklist"]
    chk_body = checklist.get("body") if isinstance(checklist, dict) else ""
    chk_bullets = checklist.get("bullets") if isinstance(checklist, dict) else checklist
    story.extend(_section_page(
        s, 13, "ACTION", "Relationship Checklist",
        "Human action plan to break negative astrology patterns",
        chk_body or "Physical communication guidelines for this bond:",
        lang=lang, bullets=chk_bullets,
    ))

    # Page 14 — closing (no page break after)
    H_REG, H_BOLD = _font_pair(lang)
    story.append(_chapter_eyebrow(14, "CLOSE", lang))
    story.extend(_chapter_title_block(
        "Closing Guidance & Security Guardrails",
        "Positive closure · next check-in · disclaimer",
        s,
    ))
    story.append(_premium_body_multi_paragraph_table(
        s, _latinize_pdf_plain(ctx["page14_closing"], lang), relax=True,
    ))
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            f"<font color='{_hex(TEXT_SOFT)}'>{_safe(LRL.closing_footer(lang))}</font>",
            ParagraphStyle("foot", fontName=H_REG, fontSize=8, leading=11, alignment=TA_CENTER),
        ),
    )

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

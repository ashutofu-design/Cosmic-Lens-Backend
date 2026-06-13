"""Founder-authored Love Reality Pro PDF — plain text paragraph → branded PDF."""
from __future__ import annotations

import io
import re
from typing import Any

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from milan_pdf import (
    BRAND_GOLD,
    BRAND_PURPLE,
    TEXT_MID,
    _ensure_native_pdf_fonts_registered,
    _font_pair,
    _latinize_pdf_plain,
    _on_page,
    _premium_body_markup,
    _pick_body_premium,
    _safe,
    _styles,
)
from vedic.love_reality.pdf_locale import love_reality_pdf_render_lang, normalize_love_reality_pdf_lang


def _pdf_lang(code: str) -> str:
    return love_reality_pdf_render_lang(normalize_love_reality_pdf_lang(code))


def _split_paragraphs(text: str) -> list[str]:
    chunks = [p.strip() for p in re.split(r"\n\s*\n+", (text or "").strip()) if p.strip()]
    if chunks:
        return chunks
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    return lines


def render_founder_love_reality_pdf(
    *,
    p1_name: str,
    p2_name: str,
    lang: str,
    body_text: str,
    order_id: str = "",
) -> bytes:
    content_lang = normalize_love_reality_pdf_lang(lang)
    render_lang = _pdf_lang(lang)
    _ensure_native_pdf_fonts_registered(render_lang)
    s = _styles()
    H_REG, H_BOLD = _font_pair(render_lang)

    title = f"Love Reality Pro — {p1_name} & {p2_name}"
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=title,
        author="Cosmic Lens",
    )
    doc.milan_pdf_lang = render_lang
    doc.milan_pdf_footer_pro = True
    doc.milan_pdf_footer_center = "Cosmic Lens · Founder-verified report"

    from reportlab.lib.styles import ParagraphStyle

    eyebrow = ParagraphStyle(
        "lr_founder_eye",
        parent=s["Normal"],
        fontName=H_REG,
        fontSize=9,
        textColor=TEXT_MID,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    h1 = ParagraphStyle(
        "lr_founder_h1",
        parent=s["Normal"],
        fontName=H_BOLD,
        fontSize=18,
        textColor=BRAND_PURPLE,
        alignment=TA_CENTER,
        spaceAfter=6,
        leading=22,
    )
    h2 = ParagraphStyle(
        "lr_founder_h2",
        parent=s["Normal"],
        fontName=H_BOLD,
        fontSize=13,
        textColor=BRAND_GOLD,
        alignment=TA_CENTER,
        spaceAfter=10,
        leading=17,
    )
    meta = ParagraphStyle(
        "lr_founder_meta",
        parent=s["Normal"],
        fontName=H_REG,
        fontSize=8.5,
        textColor=TEXT_MID,
        alignment=TA_CENTER,
        spaceAfter=14,
    )

    story: list[Any] = [
        Spacer(1, 8 * mm),
        Paragraph("COSMIC LENS", eyebrow),
        Paragraph("Love Reality Pro", h1),
        Paragraph(_safe(f"{p1_name} &amp; {p2_name}"), h2),
        Paragraph(
            _safe("Founder-verified relationship report"),
            meta,
        ),
    ]
    if order_id:
        story.append(Paragraph(_safe(f"Order #{order_id[:8]}"), meta))
    story.append(Spacer(1, 4 * mm))

    for para in _split_paragraphs(body_text):
        plain = _latinize_pdf_plain(para, render_lang)
        body_style = _pick_body_premium(plain, s, render_lang, relax=True)
        body_style.alignment = TA_LEFT
        body_style.spaceAfter = 8
        body_style.leading = 15
        markup = _premium_body_markup(plain, render_lang) or _safe(plain)
        story.append(Paragraph(markup, body_style))

    story.append(PageBreak())
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

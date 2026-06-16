"""Founder-authored Love Reality Pro PDF — plain text paragraph → branded PDF."""
from __future__ import annotations

import io
import re
import unicodedata
from typing import Any

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
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
    _pick_body_premium,
    _safe,
    _styles,
)
from vedic.love_reality.pdf_locale import (
    founder_report_meta,
    founder_report_subtitle,
    founder_report_title,
    love_reality_pdf_render_lang,
    normalize_love_reality_pdf_lang,
)


def _pdf_lang(code: str) -> str:
    return love_reality_pdf_render_lang(normalize_love_reality_pdf_lang(code))


def _split_paragraphs(text: str) -> list[str]:
    chunks = [p.strip() for p in re.split(r"\n\s*\n+", (text or "").strip()) if p.strip()]
    if chunks:
        return chunks
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    return lines


def _sanitize_founder_plain(text: str) -> str:
    """Telegram paste-safe plain text for ReportLab (no emoji / broken XML chars)."""
    t = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    t = unicodedata.normalize("NFKC", t)
    kept: list[str] = []
    for ch in t:
        if ch in "\n\t":
            kept.append(ch)
            continue
        cat = unicodedata.category(ch)
        if cat in ("Cs", "Co", "Cf", "Cn"):
            continue
        if ord(ch) > 0xFFFF:
            continue
        kept.append(ch)
    return "".join(kept).strip()


def _founder_body_markup(plain: str) -> str:
    """Simple escaped markup — avoids mixed-font paths that break on long Telegram paste."""
    lines = [ln.strip() for ln in plain.split("\n") if ln.strip()]
    if not lines:
        return _safe(plain)
    return "<br/>".join(_safe(ln).replace("%", "&#37;") for ln in lines)


def _build_story(
    *,
    p1_name: str,
    p2_name: str,
    lang: str,
    body_text: str,
    order_id: str,
) -> tuple[io.BytesIO, SimpleDocTemplate, list[Any]]:
    render_lang = _pdf_lang(lang)
    _ensure_native_pdf_fonts_registered(render_lang)
    s = _styles(render_lang)
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
    doc.milan_pdf_footer_center = founder_report_meta(render_lang)

    eyebrow = ParagraphStyle(
        "lr_founder_eye",
        parent=s["body"],
        fontName=H_REG,
        fontSize=9,
        textColor=TEXT_MID,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    h1 = ParagraphStyle(
        "lr_founder_h1",
        parent=s["body"],
        fontName=H_BOLD,
        fontSize=18,
        textColor=BRAND_PURPLE,
        alignment=TA_CENTER,
        spaceAfter=6,
        leading=22,
    )
    h2 = ParagraphStyle(
        "lr_founder_h2",
        parent=s["body"],
        fontName=H_BOLD,
        fontSize=13,
        textColor=BRAND_GOLD,
        alignment=TA_CENTER,
        spaceAfter=10,
        leading=17,
    )
    meta = ParagraphStyle(
        "lr_founder_meta",
        parent=s["body"],
        fontName=H_REG,
        fontSize=8.5,
        textColor=TEXT_MID,
        alignment=TA_CENTER,
        spaceAfter=14,
    )

    story: list[Any] = [
        Spacer(1, 8 * mm),
        Paragraph("COSMIC LENS", eyebrow),
        Paragraph(_safe(founder_report_title(render_lang)), h1),
        Paragraph(_safe(f"{p1_name} &amp; {p2_name}"), h2),
        Paragraph(_safe(founder_report_subtitle(render_lang)), meta),
    ]
    if order_id:
        story.append(Paragraph(_safe(f"Order #{order_id[:8]}"), meta))
    story.append(Spacer(1, 4 * mm))

    for para in _split_paragraphs(body_text):
        plain = _sanitize_founder_plain(_latinize_pdf_plain(para, render_lang))
        if not plain:
            continue
        body_style = _pick_body_premium(plain, s, render_lang, relax=True)
        body_style.alignment = TA_LEFT
        body_style.spaceAfter = 8
        body_style.leading = 15
        story.append(Paragraph(_founder_body_markup(plain), body_style))

    story.append(PageBreak())
    return buf, doc, story


def render_founder_love_reality_pdf(
    *,
    p1_name: str,
    p2_name: str,
    lang: str,
    body_text: str,
    order_id: str = "",
) -> bytes:
    content_lang = normalize_love_reality_pdf_lang(lang)
    last_exc: Exception | None = None
    for attempt_lang in (content_lang, "en"):
        try:
            buf, doc, story = _build_story(
                p1_name=p1_name,
                p2_name=p2_name,
                lang=attempt_lang,
                body_text=body_text,
                order_id=order_id,
            )
            doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
            return buf.getvalue()
        except Exception as exc:
            last_exc = exc
            if attempt_lang == "en":
                raise
    if last_exc:
        raise last_exc
    raise RuntimeError("founder_pdf_render_failed")
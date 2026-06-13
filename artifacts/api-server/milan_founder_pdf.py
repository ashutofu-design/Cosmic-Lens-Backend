"""Founder-authored Marriage Compatibility Pro PDF — plain text → branded PDF."""
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
from vedic.compat.milan_pdf_locale import pdf_ui_hn, pdf_ui_hi, tx
from vedic.compat.premium_chapters import normalize_pro_pdf_lang


def _pdf_lang(code: str) -> str:
    return normalize_pro_pdf_lang(code)


def _founder_title(lang: str) -> str:
    if pdf_ui_hi(lang):
        return "विवाह अनुकूलता प्रो"
    return tx(lang, "Marriage Compatibility Pro", "Marriage Compatibility Pro")


def _founder_subtitle(lang: str) -> str:
    if pdf_ui_hi(lang):
        return "संस्थापक-सत्यापित विवाह परामर्श"
    return tx(
        lang,
        "Founder-verified marriage consultation",
        "Founder-verified shaadi consultation",
    )


def _founder_meta(lang: str) -> str:
    if pdf_ui_hi(lang):
        return "Cosmic Lens संस्थापक द्वारा · D1/D9 विवाह इंजन"
    return tx(
        lang,
        "Personally prepared by Cosmic Lens · D1/D9 marriage engine",
        "Cosmic Lens founder dwara tayyar · D1/D9 marriage engine",
    )


def _split_paragraphs(text: str) -> list[str]:
    chunks = [p.strip() for p in re.split(r"\n\s*\n+", (text or "").strip()) if p.strip()]
    if chunks:
        return chunks
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]


def _sanitize_founder_plain(text: str) -> str:
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
    lines = [ln.strip() for ln in plain.split("\n") if ln.strip()]
    if not lines:
        return _safe(plain)
    return "<br/>".join(_safe(ln) for ln in lines)


def render_founder_milan_pdf(
    *,
    p1_name: str,
    p2_name: str,
    lang: str,
    body_text: str,
    order_id: str = "",
) -> bytes:
    content_lang = _pdf_lang(lang)
    last_exc: Exception | None = None
    for attempt_lang in (content_lang, "en"):
        try:
            render_lang = attempt_lang
            _ensure_native_pdf_fonts_registered(render_lang)
            s = _styles(render_lang)
            H_REG, H_BOLD = _font_pair(render_lang)

            title = f"Marriage Compatibility Pro — {p1_name} & {p2_name}"
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
            doc.milan_pdf_footer_center = _founder_meta(render_lang)

            eyebrow = ParagraphStyle(
                "milan_founder_eye",
                parent=s["body"],
                fontName=H_REG,
                fontSize=9,
                textColor=TEXT_MID,
                alignment=TA_CENTER,
                spaceAfter=4,
            )
            h1 = ParagraphStyle(
                "milan_founder_h1",
                parent=s["body"],
                fontName=H_BOLD,
                fontSize=18,
                textColor=BRAND_PURPLE,
                alignment=TA_CENTER,
                spaceAfter=6,
                leading=22,
            )
            h2 = ParagraphStyle(
                "milan_founder_h2",
                parent=s["body"],
                fontName=H_BOLD,
                fontSize=13,
                textColor=BRAND_GOLD,
                alignment=TA_CENTER,
                spaceAfter=10,
                leading=17,
            )
            meta = ParagraphStyle(
                "milan_founder_meta",
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
                Paragraph(_safe(_founder_title(render_lang)), h1),
                Paragraph(_safe(f"{p1_name} &amp; {p2_name}"), h2),
                Paragraph(_safe(_founder_subtitle(render_lang)), meta),
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
            doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
            return buf.getvalue()
        except Exception as exc:
            last_exc = exc
            if attempt_lang == "en":
                raise
    if last_exc:
        raise last_exc
    raise RuntimeError("milan_founder_pdf_render_failed")

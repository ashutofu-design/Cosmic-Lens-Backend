"""Generic branded founder PDF — plain text → Cosmic Lens Pro design system.

mystic_theme=True → Universal Pro Report chrome (cover + framed content).
Classic light chrome kept for non-mystic callers.
Paste text is rendered verbatim (no invented TOC / chapters / insights).
"""
from __future__ import annotations

import base64
import io
import re as _re
import unicodedata
from typing import Any, Sequence

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

import cosmic_pro_report_design as pro
from founder_structure import (
    founder_verbatim_markup,
    iter_verbatim_blocks,
    normalize_founder_pages_and_images,
)
from milan_pdf import (
    BRAND_GOLD,
    TEXT_DARK,
    TEXT_MID,
    _ensure_native_pdf_fonts_registered,
    _font_pair,
    _has_indic,
    _hex,
    _latinize_pdf_plain,
    _on_page,
    _pick_body_premium,
    _safe,
    _styles,
)

_DATA_URL_RE = _re.compile(
    r"^data:image/(png|jpeg|jpg|gif|webp);base64,(.+)$",
    _re.IGNORECASE | _re.DOTALL,
)


def _decode_page_image(raw: str | None) -> bytes | None:
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip()
    m = _DATA_URL_RE.match(s)
    b64 = m.group(2) if m else s
    try:
        data = base64.b64decode(b64, validate=False)
    except Exception:
        return None
    if len(data) < 32 or len(data) > 8_000_000:
        return None
    return data


def _flowable_image(raw: str | None, *, max_w: float, max_h: float) -> RLImage | None:
    data = _decode_page_image(raw)
    if not data:
        return None
    try:
        reader = ImageReader(io.BytesIO(data))
        iw, ih = reader.getSize()
        if iw <= 0 or ih <= 0:
            return None
        scale = min(max_w / float(iw), max_h / float(ih), 1.0)
        w, h = iw * scale, ih * scale
        return RLImage(io.BytesIO(data), width=w, height=h)
    except Exception:
        return None


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
    return founder_verbatim_markup(plain, escape_fn=_safe)


def _append_verbatim(
    story: list[Any],
    *,
    body_text: str,
    lang: str,
    base_styles: dict[str, ParagraphStyle],
    body_style: ParagraphStyle,
) -> None:
    for block in iter_verbatim_blocks(body_text):
        plain = _sanitize_founder_plain(_latinize_pdf_plain(block.text, lang))
        if not plain:
            continue
        if _has_indic(plain):
            st = _pick_body_premium(plain, base_styles, lang, relax=True)
            st = ParagraphStyle(
                f"pro_indic_{id(plain)}",
                parent=st,
                textColor=pro.TEXT,
                alignment=TA_LEFT,
                spaceAfter=10,
                leading=17,
                fontSize=11,
            )
            story.append(Paragraph(_founder_body_markup(plain), st))
        else:
            story.append(Paragraph(_founder_body_markup(plain), body_style))


def _build_pro_story(
    *,
    title: str,
    subject: str,
    tagline: str,
    prepared_by: str,
    order_id: str,
    body_text: str,
    pages: Sequence[str] | None,
    page_images: Sequence[str | None] | None,
    lang: str,
    base_styles: dict[str, ParagraphStyle],
) -> list[Any]:
    """Cover (TYPE A) + admin pages as framed content (TYPE D). No invented TOC."""
    s = pro.styles()
    page_list, img_list = normalize_founder_pages_and_images(
        body_text, pages, page_images
    )
    story: list[Any] = []

    story.extend(
        pro.build_cover(
            report_type=title,
            client_name=(subject or "").strip() or "Client",
            prepared_by=prepared_by,
            tagline=tagline or "Personalized Analysis & Guidance",
            order_id=order_id or "",
        )
    )

    max_w = A4[0] - 2 * (pro.FRAME_INSET + 10 * mm)
    max_h = 110 * mm

    for i, page_body in enumerate(page_list):
        story.append(PageBreak())
        if i > 0:
            story.append(
                Paragraph(
                    f"<font color='{pro.hex_str(pro.TEXT_MUTED)}'>"
                    f"COSMIC LENS · {_safe(title)}</font>",
                    s["running"],
                )
            )
            story.append(Spacer(1, 2 * mm))
            story.append(pro.thin_rule(gold=False))
            story.append(Spacer(1, 5 * mm))
        img_raw = img_list[i] if i < len(img_list) else None
        flow = _flowable_image(img_raw, max_w=max_w, max_h=max_h)
        if flow is not None:
            story.append(flow)
            story.append(Spacer(1, 5 * mm))
        _append_verbatim(
            story,
            body_text=page_body,
            lang=lang,
            base_styles=base_styles,
            body_style=s["body"],
        )

    return story


def _pro_on_first(canvas, doc) -> None:
    pro.on_cover_page(canvas, doc)


def _pro_on_later(canvas, doc) -> None:
    pro.on_content_page(canvas, doc)


def render_founder_text_pdf(
    *,
    title: str,
    subject: str,
    subtitle: str = "",
    lang: str = "en",
    body_text: str = "",
    pages: Sequence[str] | None = None,
    page_images: Sequence[str | None] | None = None,
    order_id: str = "",
    footer_center: str | None = None,
    prepared_by: str | None = "Ashutosh Bharadwaj",
    mystic_theme: bool = False,
    cover_tagline: str | None = None,
    toc_items: Sequence[str] | None = None,
) -> bytes:
    """Render a single-subject founder PDF.

    mystic_theme=True → Cosmic Lens Universal Pro Report design.
    pages / page_images: admin-controlled; same index → same PDF content page.
    """
    del toc_items
    render_lang = (lang or "en").strip().lower()
    if render_lang not in ("en", "hn", "hi"):
        render_lang = "en"
    prep = (prepared_by or "").strip() or "Ashutosh Bharadwaj"
    if prep.lower() in ("", "founder", "admin"):
        prep = "Ashutosh Bharadwaj"
    tagline = (cover_tagline if cover_tagline is not None else subtitle or "").strip()
    if not tagline:
        tagline = "Personalized Analysis & Guidance"
    page_list, img_list = normalize_founder_pages_and_images(
        body_text, pages, page_images
    )
    joined = "\n\n".join(page_list)

    last_exc: Exception | None = None
    for attempt_lang in (render_lang, "en"):
        try:
            _ensure_native_pdf_fonts_registered(attempt_lang)
            _H_REG, H_BOLD = _font_pair(attempt_lang)
            buf = io.BytesIO()
            base_styles = _styles(attempt_lang)

            if mystic_theme:
                m = pro.content_margins()
                doc = SimpleDocTemplate(
                    buf,
                    pagesize=A4,
                    **m,
                )
                doc.milan_pdf_lang = attempt_lang
                doc.milan_pdf_footer_center = footer_center or "Cosmic Lens"
                doc.pro_footer_left = (
                    "Cosmic Lens · Powered by Cosmic Intelligence Engine"
                )
                story = _build_pro_story(
                    title=title,
                    subject=(subject or "").strip() or "Client",
                    tagline=tagline,
                    prepared_by=prep,
                    order_id=order_id or "",
                    body_text=joined,
                    pages=page_list,
                    page_images=img_list,
                    lang=attempt_lang,
                    base_styles=base_styles,
                )
                doc.build(
                    story,
                    onFirstPage=_pro_on_first,
                    onLaterPages=_pro_on_later,
                )
                return buf.getvalue()

            # ── Classic light template ──
            doc = SimpleDocTemplate(
                buf,
                pagesize=A4,
                leftMargin=18 * mm,
                rightMargin=18 * mm,
                topMargin=18 * mm,
                bottomMargin=18 * mm,
            )
            if footer_center:
                doc.milan_pdf_footer_center = footer_center
            doc.milan_pdf_lang = attempt_lang
            s = base_styles

            eyebrow = ParagraphStyle(
                "founder_generic_eyebrow",
                parent=s["body"],
                fontName="Helvetica-Bold",
                fontSize=9,
                textColor=BRAND_GOLD,
                alignment=TA_CENTER,
                spaceAfter=4,
                leading=12,
            )
            h1 = ParagraphStyle(
                "founder_generic_h1",
                parent=s["body"],
                fontName="Helvetica-Bold",
                fontSize=16,
                textColor=BRAND_GOLD,
                alignment=TA_CENTER,
                spaceAfter=6,
                leading=20,
            )
            byline_label = ParagraphStyle(
                "founder_generic_byline_label",
                parent=s["body"],
                fontName="Helvetica",
                fontSize=9,
                textColor=TEXT_MID,
                alignment=TA_CENTER,
                spaceAfter=2,
                leading=12,
            )
            byline_name = ParagraphStyle(
                "founder_generic_byline_name",
                parent=s["body"],
                fontName="Helvetica-Bold",
                fontSize=12,
                textColor=BRAND_GOLD,
                alignment=TA_CENTER,
                spaceAfter=10,
                leading=15,
            )
            meta = ParagraphStyle(
                "founder_generic_meta",
                parent=s["body"],
                fontName="Helvetica",
                fontSize=8.5,
                textColor=TEXT_MID,
                alignment=TA_CENTER,
                spaceAfter=14,
            )
            subj = (subject or "").strip() or "Client"
            subj_font = H_BOLD if _has_indic(subj) else "Helvetica-Bold"
            h2 = ParagraphStyle(
                "founder_generic_h2",
                parent=s["body"],
                fontName=subj_font,
                fontSize=13,
                textColor=TEXT_DARK if subj_font.startswith("Helvetica") else BRAND_GOLD,
                alignment=TA_CENTER,
                spaceAfter=8,
                leading=17,
            )

            story: list[Any] = [
                Spacer(1, 8 * mm),
                Paragraph("COSMIC LENS", eyebrow),
                Paragraph(_safe(title), h1),
                Paragraph("Client", byline_label),
                Paragraph(_safe(subj), h2),
                Paragraph("Prepared by", byline_label),
                Paragraph(
                    f"<font color='{_hex(BRAND_GOLD)}'><b>{_safe(prep)}</b></font>",
                    byline_name,
                ),
            ]
            if subtitle:
                story.append(Paragraph(_safe(subtitle), meta))
            if order_id:
                story.append(Paragraph(_safe(f"Order #{order_id[:8]}"), meta))
            story.append(Spacer(1, 4 * mm))

            max_w = A4[0] - 36 * mm
            max_h = 110 * mm

            def _append_classic_page(page_body: str, img_raw: str | None) -> None:
                flow = _flowable_image(img_raw, max_w=max_w, max_h=max_h)
                if flow is not None:
                    story.append(flow)
                    story.append(Spacer(1, 5 * mm))
                for block in iter_verbatim_blocks(page_body):
                    plain = _sanitize_founder_plain(
                        _latinize_pdf_plain(block.text, attempt_lang)
                    )
                    if not plain:
                        continue
                    body_style = _pick_body_premium(plain, s, attempt_lang, relax=True)
                    body_style.alignment = TA_LEFT
                    body_style.spaceAfter = 8
                    body_style.leading = 15
                    story.append(Paragraph(_founder_body_markup(plain), body_style))

            for i, page_body in enumerate(page_list):
                if i > 0:
                    story.append(PageBreak())
                img_raw = img_list[i] if i < len(img_list) else None
                _append_classic_page(page_body, img_raw)

            doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
            return buf.getvalue()
        except Exception as exc:
            last_exc = exc
            if attempt_lang == "en":
                raise
    if last_exc:
        raise last_exc
    raise RuntimeError("founder_text_pdf_render_failed")

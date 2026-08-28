"""Founder-authored Marriage Compatibility Pro PDF — Universal Pro design."""
from __future__ import annotations

import io
import unicodedata
from typing import Any

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

import cosmic_pro_report_design as pro
from founder_structure import (
    founder_verbatim_markup,
    iter_verbatim_blocks,
    normalize_founder_pages_and_images,
)
from founder_text_pdf import _flowable_image
from milan_pdf import (
    _ensure_native_pdf_fonts_registered,
    _has_indic,
    _latinize_pdf_plain,
    _pick_body_premium,
    _safe,
    _styles,
)
from vedic.compat.milan_pdf_locale import tx


def _pdf_lang(code: str) -> str:
    c = (code or "en").strip().lower()
    if c in ("hi", "hn", "en"):
        return "hi" if c == "hi" else ("hn" if c == "hn" else "en")
    return "en"


def _founder_title(lang: str) -> str:
    return tx(lang, "Marriage Compatibility Pro", "Marriage Compatibility Pro")


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


def render_founder_milan_pdf(
    *,
    p1_name: str,
    p2_name: str,
    lang: str,
    body_text: str = "",
    pages: list[str] | None = None,
    page_images: list[str | None] | None = None,
    order_id: str = "",
) -> bytes:
    content_lang = _pdf_lang(lang)
    page_list, img_list = normalize_founder_pages_and_images(
        body_text, pages, page_images
    )
    last_exc: Exception | None = None
    for attempt_lang in (content_lang, "en"):
        try:
            render_lang = attempt_lang
            _ensure_native_pdf_fonts_registered(render_lang)
            base = _styles(render_lang)
            s = pro.styles()
            report_title = _founder_title(render_lang)
            client = f"{p1_name} & {p2_name}"

            buf = io.BytesIO()
            m = pro.content_margins()
            doc = SimpleDocTemplate(buf, pagesize=A4, **m)
            doc.milan_pdf_lang = render_lang
            doc.pro_footer_left = (
                "Cosmic Lens · Powered by Cosmic Intelligence Engine"
            )

            story: list[Any] = []
            story.extend(
                pro.build_cover(
                    report_type=report_title,
                    client_name=client,
                    prepared_by="Ashutosh Bharadwaj",
                    tagline="Personalized Analysis & Guidance",
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
                            f"COSMIC LENS · {_safe(report_title)}</font>",
                            s["running"],
                        )
                    )
                    story.append(Spacer(1, 2 * mm))
                    story.append(pro.thin_rule(gold=False))
                    story.append(Spacer(1, 5 * mm))
                flow = _flowable_image(
                    img_list[i] if i < len(img_list) else None,
                    max_w=max_w,
                    max_h=max_h,
                )
                if flow is not None:
                    story.append(flow)
                    story.append(Spacer(1, 5 * mm))
                for block in iter_verbatim_blocks(page_body):
                    plain = _sanitize_founder_plain(
                        _latinize_pdf_plain(block.text, render_lang)
                    )
                    if not plain:
                        continue
                    if _has_indic(plain):
                        st = _pick_body_premium(plain, base, render_lang, relax=True)
                        st = ParagraphStyle(
                            f"milan_pro_indic_{id(plain)}",
                            parent=st,
                            textColor=pro.TEXT,
                            alignment=TA_LEFT,
                            spaceAfter=10,
                            leading=17,
                            fontSize=11,
                        )
                        story.append(Paragraph(_founder_body_markup(plain), st))
                    else:
                        story.append(Paragraph(_founder_body_markup(plain), s["body"]))

            doc.build(
                story,
                onFirstPage=pro.on_cover_page,
                onLaterPages=pro.on_content_page,
            )
            return buf.getvalue()
        except Exception as exc:
            last_exc = exc
            if attempt_lang == "en":
                raise
    if last_exc:
        raise last_exc
    raise RuntimeError("milan_founder_pdf_render_failed")

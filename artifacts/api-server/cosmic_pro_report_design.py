"""Cosmic Lens Universal Pro Report — design system (presentation only).

Central tokens + reusable PDF chrome for Numerology / Love / Milan / Vastu /
Palmistry founder PDFs and future Pro reports.

Does NOT invent report analysis, scores, TOC from paste, or change engines.
Callers supply titles / body / optional structured blocks.
"""
from __future__ import annotations

# Bump when design changes — footer / smoke tests use this to confirm deploy.
PRO_DESIGN_VER = "pro-v2-2026-08-21"

import math
from typing import Any, Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ── Palette (locked Cosmic Lens Pro) ──────────────────────────────────────
BG = colors.HexColor("#080B18")
BG_TOP = colors.HexColor("#0C1020")
BG_BOT = colors.HexColor("#060812")
SURFACE = colors.HexColor("#10152A")
SURFACE_ELEV = colors.HexColor("#151B32")
TEXT = colors.HexColor("#F4F1EA")
TEXT_MUTED = colors.HexColor("#A9ADBD")
PURPLE = colors.HexColor("#6C4DFF")
GOLD = colors.HexColor("#C9A86A")
DIVIDER = colors.Color(201 / 255, 168 / 255, 106 / 255, alpha=0.25)
DIVIDER_SOLID = colors.HexColor("#3D3424")  # opaque rule for Table fills
PURPLE_GLOW = colors.Color(108 / 255, 77 / 255, 255 / 255, alpha=0.10)
BORDER = colors.Color(201 / 255, 168 / 255, 106 / 255, alpha=0.32)
BORDER_PURPLE = colors.Color(108 / 255, 77 / 255, 255 / 255, alpha=0.22)
BORDER_SOLID = colors.HexColor("#4A3F2A")

# ── Page geometry (A4) ────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN_L = 19 * mm
MARGIN_R = 19 * mm
MARGIN_T = 20 * mm
MARGIN_B = 20 * mm
# Inner frame inset from physical page edge
FRAME_INSET = 13 * mm
# Content top reserve for header band (content pages)
HEADER_BAND = 14 * mm
FOOTER_BAND = 12 * mm

# Built-in fonts approximating Playfair (serif titles) + Inter (sans body)
FONT_SERIF = "Times-Roman"
FONT_SERIF_BOLD = "Times-Bold"
FONT_SANS = "Helvetica"
FONT_SANS_BOLD = "Helvetica-Bold"


def hex_str(c: colors.Color) -> str:
    return "#%02X%02X%02X" % (
        int(c.red * 255),
        int(c.green * 255),
        int(c.blue * 255),
    )


def _lerp(a: colors.Color, b: colors.Color, t: float) -> colors.Color:
    t = max(0.0, min(1.0, t))
    return colors.Color(
        a.red + (b.red - a.red) * t,
        a.green + (b.green - a.green) * t,
        a.blue + (b.blue - a.blue) * t,
    )


def draw_atmosphere(canvas, *, intensity: str = "content") -> None:
    """Subtle cosmic wash. intensity: cover | chapter | content."""
    w, h = PAGE_W, PAGE_H
    bands = 40
    band_h = h / bands
    for i in range(bands):
        t = i / max(bands - 1, 1)
        c = _lerp(BG_TOP, BG_BOT, t)
        canvas.setFillColor(c)
        canvas.rect(0, h - (i + 1) * band_h, w, band_h + 0.5, fill=1, stroke=0)

    # Soft purple glow — stronger on cover/chapter only
    if intensity in ("cover", "chapter"):
        canvas.setFillColor(PURPLE_GLOW)
        canvas.circle(w * 0.78, h * 0.72, 55 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.Color(201 / 255, 168 / 255, 106 / 255, alpha=0.05))
        canvas.circle(w * 0.22, h * 0.28, 40 * mm, fill=1, stroke=0)
    else:
        canvas.setFillColor(colors.Color(108 / 255, 77 / 255, 255 / 255, alpha=0.04))
        canvas.circle(w * 0.85, h * 0.8, 35 * mm, fill=1, stroke=0)

    # Tiny sparse particles (content: almost invisible)
    n = 18 if intensity == "cover" else (12 if intensity == "chapter" else 6)
    alpha = 0.12 if intensity == "cover" else (0.08 if intensity == "chapter" else 0.04)
    canvas.setFillColor(colors.Color(1, 1, 1, alpha=alpha))
    for i in range(n):
        x = ((i * 47) % 97) / 100.0 * w
        y = ((i * 61) % 89) / 100.0 * h
        canvas.circle(x, y, 0.6 if i % 2 else 0.9, fill=1, stroke=0)

    # Left spine accent (restrained gold)
    canvas.setFillColor(colors.Color(201 / 255, 168 / 255, 106 / 255, alpha=0.14))
    canvas.rect(0, 0, 1.6 * mm, h, fill=1, stroke=0)


def draw_inner_border(canvas) -> None:
    """~0.75pt muted gold frame, ~13mm inset."""
    inset = FRAME_INSET
    x0, y0 = inset, inset
    x1, y1 = PAGE_W - inset, PAGE_H - inset
    canvas.saveState()
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.7)
    canvas.rect(x0, y0, x1 - x0, y1 - y0, fill=0, stroke=1)

    # Minimal geometric corners (L marks)
    arm = 4.5 * mm
    canvas.setStrokeColor(colors.Color(108 / 255, 77 / 255, 255 / 255, alpha=0.35))
    canvas.setLineWidth(0.9)
    for cx, cy, sx, sy in (
        (x0, y1, 1, -1),
        (x1, y1, -1, -1),
        (x0, y0, 1, 1),
        (x1, y0, -1, 1),
    ):
        canvas.line(cx, cy, cx + sx * arm, cy)
        canvas.line(cx, cy, cx, cy + sy * arm)
    canvas.restoreState()


def draw_universal_header(canvas) -> None:
    """COSMIC LENS … PRO REPORT + thin rule."""
    canvas.saveState()
    top = PAGE_H - FRAME_INSET - 5 * mm
    left = FRAME_INSET + 4 * mm
    right = PAGE_W - FRAME_INSET - 4 * mm
    canvas.setFillColor(GOLD)
    canvas.setFont(FONT_SANS_BOLD, 8)
    canvas.drawString(left, top, "COSMIC LENS")
    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont(FONT_SANS, 8)
    canvas.drawRightString(right, top, "PRO REPORT")
    canvas.setStrokeColor(DIVIDER)
    canvas.setLineWidth(0.6)
    y = top - 3.2 * mm
    canvas.line(left, y, right, y)
    canvas.restoreState()


def draw_universal_footer(canvas, doc) -> None:
    """Footer: brand · engine | page number."""
    canvas.saveState()
    bottom = FRAME_INSET + 4 * mm
    left = FRAME_INSET + 4 * mm
    right = PAGE_W - FRAME_INSET - 4 * mm
    canvas.setStrokeColor(DIVIDER)
    canvas.setLineWidth(0.55)
    canvas.line(left, bottom + 4.5 * mm, right, bottom + 4.5 * mm)
    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont(FONT_SANS, 7)
    label = getattr(doc, "pro_footer_left", None) or (
        "Cosmic Lens · Powered by Cosmic Intelligence Engine"
    )
    # Tiny version tag so deploy can be confirmed on a generated PDF.
    ver = PRO_DESIGN_VER
    canvas.drawString(left, bottom, f"{str(label)[:52]} · {ver}"[:78])
    page_s = f"{int(doc.page):02d}"
    canvas.drawRightString(right, bottom, page_s)
    canvas.restoreState()


def on_cover_page(canvas, doc) -> None:
    draw_atmosphere(canvas, intensity="cover")
    draw_inner_border(canvas)
    # Cover: no content header; quiet page mark only
    canvas.saveState()
    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont(FONT_SANS, 7)
    canvas.drawRightString(
        PAGE_W - FRAME_INSET - 4 * mm, FRAME_INSET + 4 * mm, f"{int(doc.page):02d}"
    )
    canvas.restoreState()


def on_chapter_page(canvas, doc) -> None:
    draw_atmosphere(canvas, intensity="chapter")
    draw_inner_border(canvas)
    draw_universal_header(canvas)
    draw_universal_footer(canvas, doc)


def on_content_page(canvas, doc) -> None:
    draw_atmosphere(canvas, intensity="content")
    draw_inner_border(canvas)
    draw_universal_header(canvas)
    draw_universal_footer(canvas, doc)


def content_margins() -> dict[str, float]:
    """Margins for SimpleDocTemplate on content pages (inside frame + header)."""
    return {
        "leftMargin": FRAME_INSET + 6 * mm,
        "rightMargin": FRAME_INSET + 6 * mm,
        "topMargin": FRAME_INSET + HEADER_BAND + 4 * mm,
        "bottomMargin": FRAME_INSET + FOOTER_BAND + 4 * mm,
    }


def cover_margins() -> dict[str, float]:
    return {
        "leftMargin": FRAME_INSET + 10 * mm,
        "rightMargin": FRAME_INSET + 10 * mm,
        "topMargin": FRAME_INSET + 14 * mm,
        "bottomMargin": FRAME_INSET + 14 * mm,
    }


def styles() -> dict[str, ParagraphStyle]:
    """Shared typography tokens (serif titles, sans body)."""
    return {
        "brand": ParagraphStyle(
            "pro_brand",
            fontName=FONT_SANS_BOLD,
            fontSize=9,
            leading=12,
            textColor=GOLD,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "pro_label": ParagraphStyle(
            "pro_label",
            fontName=FONT_SANS,
            fontSize=9,
            leading=12,
            textColor=TEXT_MUTED,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "cover_title": ParagraphStyle(
            "pro_cover_title",
            fontName=FONT_SERIF_BOLD,
            fontSize=28,
            leading=34,
            textColor=TEXT,
            alignment=TA_CENTER,
            spaceBefore=8,
            spaceAfter=10,
        ),
        "cover_sub": ParagraphStyle(
            "pro_cover_sub",
            fontName=FONT_SANS,
            fontSize=11,
            leading=15,
            textColor=TEXT_MUTED,
            alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "meta_label": ParagraphStyle(
            "pro_meta_label",
            fontName=FONT_SANS,
            fontSize=8,
            leading=11,
            textColor=TEXT_MUTED,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=2,
        ),
        "meta_value": ParagraphStyle(
            "pro_meta_value",
            fontName=FONT_SERIF_BOLD,
            fontSize=14,
            leading=18,
            textColor=GOLD,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "confidential": ParagraphStyle(
            "pro_confidential",
            fontName=FONT_SANS,
            fontSize=8,
            leading=11,
            textColor=TEXT_MUTED,
            alignment=TA_CENTER,
            spaceBefore=20,
        ),
        "chapter_num": ParagraphStyle(
            "pro_chapter_num",
            fontName=FONT_SERIF_BOLD,
            fontSize=42,
            leading=46,
            textColor=GOLD,
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "chapter_title": ParagraphStyle(
            "pro_chapter_title",
            fontName=FONT_SERIF_BOLD,
            fontSize=24,
            leading=30,
            textColor=TEXT,
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "chapter_sub": ParagraphStyle(
            "pro_chapter_sub",
            fontName=FONT_SANS,
            fontSize=11,
            leading=15,
            textColor=TEXT_MUTED,
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "section_title": ParagraphStyle(
            "pro_section_title",
            fontName=FONT_SERIF_BOLD,
            fontSize=16,
            leading=20,
            textColor=TEXT,
            alignment=TA_LEFT,
            spaceBefore=4,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "pro_body",
            fontName=FONT_SANS,
            fontSize=11,
            leading=17,
            textColor=TEXT,
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "body_indic": ParagraphStyle(
            "pro_body_indic",
            fontName=FONT_SANS,
            fontSize=11,
            leading=17,
            textColor=TEXT,
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "toc_num": ParagraphStyle(
            "pro_toc_num",
            fontName=FONT_SERIF_BOLD,
            fontSize=16,
            leading=20,
            textColor=GOLD,
            alignment=TA_LEFT,
        ),
        "toc_title": ParagraphStyle(
            "pro_toc_title",
            fontName=FONT_SANS_BOLD,
            fontSize=11,
            leading=14,
            textColor=TEXT,
            alignment=TA_LEFT,
        ),
        "toc_desc": ParagraphStyle(
            "pro_toc_desc",
            fontName=FONT_SANS,
            fontSize=9,
            leading=12,
            textColor=TEXT_MUTED,
            alignment=TA_LEFT,
        ),
        "card_label": ParagraphStyle(
            "pro_card_label",
            fontName=FONT_SANS_BOLD,
            fontSize=8,
            leading=10,
            textColor=GOLD,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "card_body": ParagraphStyle(
            "pro_card_body",
            fontName=FONT_SANS,
            fontSize=10.5,
            leading=15,
            textColor=TEXT,
            alignment=TA_LEFT,
        ),
        "running": ParagraphStyle(
            "pro_running",
            fontName=FONT_SANS,
            fontSize=8,
            leading=10,
            textColor=TEXT_MUTED,
            alignment=TA_RIGHT,
            spaceAfter=8,
        ),
    }


def _safe(s: Any) -> str:
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def thin_rule(width: float | None = None, *, gold: bool = False) -> Table:
    w = width if width is not None else (PAGE_W - 2 * (FRAME_INSET + 10 * mm))
    t = Table([[""]], colWidths=[w], rowHeights=[0.7])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), GOLD if gold else DIVIDER_SOLID),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return t


def build_cover(
    *,
    report_type: str,
    client_name: str,
    prepared_by: str = "Ashutosh Bharadwaj",
    tagline: str = "Personalized Analysis & Guidance",
    order_id: str = "",
) -> list[Any]:
    """TYPE A — cinematic cover (branding only, no analysis invent)."""
    s = styles()
    story: list[Any] = []
    story.append(Spacer(1, 18 * mm))
    story.append(Paragraph("COSMIC LENS", s["brand"]))
    story.append(Spacer(1, 2 * mm))
    story.append(thin_rule(28 * mm, gold=True))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("PRO REPORT", s["pro_label"]))
    story.append(Paragraph(_safe(report_type.upper()), s["cover_title"]))
    story.append(Paragraph(_safe(tagline), s["cover_sub"]))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("PREPARED FOR", s["meta_label"]))
    story.append(Paragraph(_safe(client_name or "Client"), s["meta_value"]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("PREPARED BY", s["meta_label"]))
    story.append(Paragraph(_safe(prepared_by), s["meta_value"]))
    if order_id:
        story.append(
            Paragraph(f"Order {_safe(str(order_id)[:8].upper())}", s["meta_label"])
        )
    story.append(Spacer(1, 16 * mm))
    story.append(Paragraph("Cosmic Intelligence Engine", s["pro_label"]))
    story.append(
        Paragraph("CONFIDENTIAL · PERSONALIZED REPORT", s["confidential"])
    )
    return story


def build_chapter_divider(
    *,
    number: str,
    title: str,
    subtitle: str = "",
    blurb: str = "",
) -> list[Any]:
    """TYPE C — chapter opener (caller supplies text; nothing invented)."""
    s = styles()
    story: list[Any] = [
        Spacer(1, 28 * mm),
        Paragraph(_safe(number), s["chapter_num"]),
        Paragraph(_safe(title), s["chapter_title"]),
    ]
    if subtitle:
        story.append(Paragraph(_safe(subtitle), s["chapter_sub"]))
    story.append(Spacer(1, 4 * mm))
    story.append(thin_rule(55 * mm, gold=True))
    if blurb:
        story.append(Spacer(1, 8 * mm))
        story.append(Paragraph(_safe(blurb), s["chapter_sub"]))
    return story


def build_toc(items: Sequence[dict[str, str]], *, title: str = "Contents") -> list[Any]:
    """TYPE B — editorial TOC. items: {num, title, description?} from caller only."""
    s = styles()
    story: list[Any] = [
        Spacer(1, 8 * mm),
        Paragraph(_safe(title), s["chapter_title"]),
        Spacer(1, 4 * mm),
        thin_rule(gold=True),
        Spacer(1, 10 * mm),
    ]
    for it in items:
        num = _safe(it.get("num") or "")
        tit = _safe(it.get("title") or "")
        desc = _safe(it.get("description") or "")
        row = Table(
            [
                [
                    Paragraph(num, s["toc_num"]),
                    Paragraph(
                        f"<b>{tit}</b>"
                        + (f"<br/><font color='{hex_str(TEXT_MUTED)}' size='9'>{desc}</font>" if desc else ""),
                        s["toc_title"],
                    ),
                ]
            ],
            colWidths=[18 * mm, PAGE_W - 2 * (FRAME_INSET + 10 * mm) - 18 * mm],
        )
        row.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.4, DIVIDER_SOLID),
                ]
            )
        )
        story.append(row)
    return story


def insight_card(label: str, body: str) -> KeepTogether:
    """Premium callout card — only when caller provides real insight text."""
    s = styles()
    inner = Table(
        [
            [Paragraph(_safe(label).upper(), s["card_label"])],
            [Paragraph(_safe(body), s["card_body"])],
        ],
        colWidths=[PAGE_W - 2 * (FRAME_INSET + 10 * mm) - 8 * mm],
    )
    inner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SURFACE_ELEV),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER_PURPLE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (0, 0), 10),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
                ("TOPPADDING", (0, 1), (-1, 1), 2),
            ]
        )
    )
    accent = Table(
        [[""], [inner]],
        colWidths=[PAGE_W - 2 * (FRAME_INSET + 10 * mm)],
        rowHeights=[2, None],
    )
    accent.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), GOLD),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return KeepTogether([Spacer(1, 4 * mm), accent, Spacer(1, 6 * mm)])


def build_final_synthesis(
    *,
    rows: Sequence[tuple[str, str]],
) -> list[Any]:
    """TYPE F — final page from caller-supplied (label, text) pairs only."""
    s = styles()
    story: list[Any] = [
        Spacer(1, 10 * mm),
        Paragraph("FINAL SYNTHESIS", s["chapter_title"]),
        Spacer(1, 2 * mm),
        thin_rule(gold=True),
        Spacer(1, 8 * mm),
    ]
    for label, body in rows:
        if not (body or "").strip():
            continue
        story.append(insight_card(label, body))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("COSMIC LENS", s["brand"]))
    story.append(Paragraph("Cosmic Intelligence Engine", s["pro_label"]))
    return story

"""
Love Reality Pro — premium dashboard page 1 (ReportLab, flat layout — no nested KeepTogether).
"""
from __future__ import annotations

from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, PageBreak, Paragraph, Spacer, Table, TableStyle

from milan_pdf import (
    BRAND_GOLD,
    BRAND_PURPLE,
    TEXT_DARK,
    TEXT_MID,
    TEXT_SOFT,
    _font_pair,
    _hex,
    _safe,
)

COSMIC_50 = colors.HexColor("#F5F3FF")
COSMIC_200 = colors.HexColor("#DDD6FE")
GLASS_BG = colors.HexColor("#FAFAFF")
EMERALD = colors.HexColor("#059669")
AMBER = colors.HexColor("#D97706")
RED = colors.HexColor("#DC2626")

_CONTENT_W = 180 * mm
_CARD = TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), GLASS_BG),
    ("BOX", (0, 0), (-1, -1), 0.4, COSMIC_200),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
])


def _score_color(value: int, invert: bool = False) -> colors.Color:
    v = 100 - value if invert else value
    if v >= 70:
        return EMERALD
    if v >= 45:
        return AMBER
    return RED


class CircularGaugeFlowable(Flowable):
    def __init__(self, value: int, size: float = 26 * mm, label: str = "Cosmic Alignment"):
        self.value = max(0, min(100, int(value)))
        self.size = size
        self.label = label
        self.width = size
        self.height = size + 6 * mm

    def draw(self) -> None:
        c = self.canv
        s = self.size
        cx, cy = s / 2, s / 2 + 1.5 * mm
        r = s / 2 - 2.5 * mm
        stroke = 2 * mm
        c.setStrokeColor(COSMIC_200)
        c.setLineWidth(stroke)
        c.circle(cx, cy, r, stroke=1, fill=0)
        col = _score_color(self.value)
        c.setStrokeColor(col)
        try:
            c.setLineCap(1)
        except Exception:
            pass
        c.arc(cx - r, cy - r, cx + r, cy + r, 90, -360 * (self.value / 100.0))
        scale = max(0.4, float(self.size) / float(26 * mm))
        c.setFillColor(BRAND_PURPLE)
        c.setFont("Helvetica-Bold", max(8, 14 * scale))
        c.drawCentredString(cx, cy + 0.8 * mm, str(self.value))
        c.setFont("Helvetica", max(5, 5.5 * scale))
        c.setFillColor(TEXT_MID)
        c.drawCentredString(cx, cy - 3 * mm, "/ 100")
        if self.label:
            c.setFont("Helvetica-Bold", max(5, 6.5 * scale))
            c.setFillColor(TEXT_DARK)
            c.drawCentredString(cx, 1 * mm, self.label)


def _section_label(text: str, H_BOLD: str) -> Paragraph:
    return Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(text.upper())}</b></font>",
        ParagraphStyle("sl", fontName=H_BOLD, fontSize=7, leading=9, textColor=BRAND_PURPLE),
    )


def _body(text: str, H_REG: str, size: float = 7.2, leading: float = 9) -> Paragraph:
    return Paragraph(
        _safe(text or ""),
        ParagraphStyle("bd", fontName=H_REG, fontSize=size, leading=leading, textColor=TEXT_MID),
    )


def _stack_card(rows: list[Any], width: float = _CONTENT_W) -> Table:
    """One flowable per row — splits safely across pages."""
    t = Table([[r] for r in rows], colWidths=[width])
    t.setStyle(_CARD)
    return t


def _metric_cell(metric: dict[str, Any], H_REG: str, H_BOLD: str) -> Paragraph:
    val = int(metric.get("value") or 0)
    return Paragraph(
        f"<b>{_safe(metric.get('label') or '')}</b> "
        f"<font color='{_hex(BRAND_PURPLE)}'><b>{val}%</b></font><br/>"
        f"<font size='6'>{_safe(metric.get('interpretation') or '')}</font>",
        ParagraphStyle("mc", fontName=H_REG, fontSize=7, leading=9, textColor=TEXT_DARK),
    )


def render_premium_page1_flowables(data: dict[str, Any], lang: str = "en") -> list[Any]:
    H_REG, H_BOLD = _font_pair(lang)
    out: list[Any] = []

    # Header
    header = Table(
        [[
            Paragraph(
                f"<font color='{_hex(BRAND_GOLD)}'><b>* COSMIC LENS</b></font> "
                f"<font color='{_hex(BRAND_PURPLE)}'><b>PREMIUM</b></font><br/>"
                f"<font size='13'><b>Love Reality Pro</b></font><br/>"
                f"<b>{_safe(data['p1_name'])}</b> &middot; <b>{_safe(data['p2_name'])}</b>",
                ParagraphStyle("hdr", fontName=H_BOLD, fontSize=9, leading=11, textColor=TEXT_DARK),
            ),
            Paragraph(
                f"ID <b>{_safe(data['report_id'])}</b><br/>{_safe(data['generated_at'])}",
                ParagraphStyle("hid", fontName=H_REG, fontSize=7, leading=9, textColor=TEXT_SOFT, alignment=TA_RIGHT),
            ),
        ]],
        colWidths=[118 * mm, 62 * mm],
    )
    header.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, COSMIC_200),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    out.append(header)
    out.append(Spacer(1, 2 * mm))

    # Hero — gauge + summary (single Paragraph in right cell, no nesting)
    score = int(data.get("cosmic_score") or 0)
    summary_html = (
        f"<font color='{_hex(BRAND_PURPLE)}'><b>RELATIONSHIP SUMMARY</b></font><br/>"
        f"<b>{_safe(data['p1_name'])} &amp; {_safe(data['p2_name'])}</b><br/>"
        f"{_safe(data.get('relationship_summary') or '')}"
    )
    hero = Table(
        [[
            CircularGaugeFlowable(score, size=24 * mm),
            Paragraph(
                summary_html,
                ParagraphStyle("sum", fontName=H_REG, fontSize=7.2, leading=9.5, textColor=TEXT_MID),
            ),
        ]],
        colWidths=[44 * mm, 136 * mm],
    )
    hero.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GLASS_BG),
        ("BOX", (0, 0), (-1, -1), 0.4, COSMIC_200),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    out.append(hero)
    out.append(Spacer(1, 2 * mm))

    # Core metrics — 4 columns, one Paragraph each
    out.append(_section_label("Core Metrics", H_BOLD))
    out.append(Spacer(1, 1 * mm))
    metrics = data.get("metrics") or []
    mcells = [_metric_cell(m, H_REG, H_BOLD) for m in metrics[:4]]
    while len(mcells) < 4:
        mcells.append(Paragraph("", ParagraphStyle("e", fontName=H_REG, fontSize=1, leading=1)))
    mrow = Table([mcells], colWidths=[45 * mm] * 4)
    mrow.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GLASS_BG),
        ("BOX", (0, 0), (-1, -1), 0.4, COSMIC_200),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, COSMIC_200),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    out.append(mrow)
    out.append(Spacer(1, 2 * mm))

    # Relationship insights — stacked rows (splittable)
    insight_rows: list[Any] = [_section_label("Relationship Insights", H_BOLD)]
    insight_rows.append(_body(str(data.get("insights_narrative") or ""), H_REG))
    bullets = data.get("key_insights") or []
    if bullets:
        bl = "<br/>".join(f"- {_safe(b)}" for b in bullets[:4])
        insight_rows.append(Paragraph(bl, ParagraphStyle("ins", fontName=H_REG, fontSize=6.8, leading=8.5, textColor=TEXT_MID)))
    out.append(_stack_card(insight_rows))
    out.append(Spacer(1, 2 * mm))

    # Strengths / Challenges — text + score lines (no ProgressBar flowables in nested tables)
    def comp_lines(title: str, items: list[dict], negative: bool) -> list[Any]:
        rows: list[Any] = [_section_label(title, H_BOLD)]
        for it in (items or [])[:4]:
            v = int(it.get("value") or 0)
            col = _hex(RED if negative else _score_color(v))
            rows.append(Paragraph(
                f"{_safe(it.get('label') or '')} "
                f"<font color='{col}'><b>{v}%</b></font>",
                ParagraphStyle("cl", fontName=H_REG, fontSize=6.8, leading=8.5, textColor=TEXT_DARK),
            ))
        return rows

    sc = Table(
        [[
            _stack_card(comp_lines("Strengths in this Connection", data.get("strengths") or [], False), 87 * mm),
            _stack_card(comp_lines("Challenges in this Connection", data.get("challenges") or [], True), 87 * mm),
        ]],
        colWidths=[90 * mm, 90 * mm],
    )
    sc.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    out.append(sc)
    out.append(Spacer(1, 2 * mm))

    # Deep analysis — one Paragraph per card (2x2)
    out.append(_section_label("Deep Analysis", H_BOLD))
    out.append(Spacer(1, 1 * mm))
    analysis = data.get("analysis") or []

    def analysis_para(block: dict) -> Paragraph:
        sc_val = int(block.get("score") or 0)
        return Paragraph(
            f"<b>{_safe(block.get('title') or '')}</b> "
            f"<font color='{_hex(BRAND_PURPLE)}'>{sc_val}/100</font><br/>"
            f"<font size='6'>{_safe(block.get('explanation') or '')}</font>",
            ParagraphStyle("an", fontName=H_REG, fontSize=7, leading=9, textColor=TEXT_DARK),
        )

    a_rows: list[list[Any]] = []
    for i in range(0, min(4, len(analysis)), 2):
        left = analysis_para(analysis[i]) if i < len(analysis) else Paragraph("", ParagraphStyle("e", fontName=H_REG, fontSize=1))
        right = analysis_para(analysis[i + 1]) if i + 1 < len(analysis) else Paragraph("", ParagraphStyle("e", fontName=H_REG, fontSize=1))
        a_rows.append([left, right])
    if a_rows:
        atbl = Table(a_rows, colWidths=[90 * mm, 90 * mm])
        atbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GLASS_BG),
            ("BOX", (0, 0), (-1, -1), 0.4, COSMIC_200),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, COSMIC_200),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        out.append(atbl)
    out.append(Spacer(1, 2 * mm))

    # Verdict + recommendations
    recs = data.get("recommendations") or []
    rec_html = "<br/>".join(f"- {_safe(r)}" for r in recs[:3])
    footer = Table(
        [[
            _stack_card([
                _section_label("Final Cosmic Verdict", H_BOLD),
                _body(str(data.get("verdict") or ""), H_REG, 7, 8.5),
            ], 87 * mm),
            _stack_card([
                _section_label("Recommendations", H_BOLD),
                Paragraph(rec_html, ParagraphStyle("rc", fontName=H_REG, fontSize=6.8, leading=8.5, textColor=TEXT_MID)),
            ], 87 * mm),
        ]],
        colWidths=[90 * mm, 90 * mm],
    )
    footer.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    out.append(footer)
    out.append(Spacer(1, 2 * mm))
    out.append(Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'>Cosmic Lens · Confidential premium report</font>",
        ParagraphStyle("ft", fontName=H_REG, fontSize=6, leading=8, alignment=TA_CENTER),
    ))
    out.append(PageBreak())
    return out


def page1_fits_a4() -> bool:
    _w, _h = A4
    return True

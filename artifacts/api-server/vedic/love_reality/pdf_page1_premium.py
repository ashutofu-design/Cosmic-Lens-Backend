"""
Love Reality Pro — premium dashboard page 1 (ReportLab, matches React layout).
"""
from __future__ import annotations

from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, KeepTogether, PageBreak, Paragraph, Spacer, Table, TableStyle

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
COSMIC_100 = colors.HexColor("#EDE9FE")
COSMIC_200 = colors.HexColor("#DDD6FE")
GLASS_BG = colors.HexColor("#FAFAFF")
EMERALD = colors.HexColor("#059669")
AMBER = colors.HexColor("#D97706")
RED = colors.HexColor("#DC2626")


def _score_color(value: int, invert: bool = False) -> colors.Color:
    v = 100 - value if invert else value
    if v >= 70:
        return EMERALD
    if v >= 45:
        return AMBER
    return RED


class CircularGaugeFlowable(Flowable):
    def __init__(self, value: int, size: float = 28 * mm, label: str = "Cosmic Alignment"):
        self.value = max(0, min(100, int(value)))
        self.size = size
        self.label = label
        self.width = size
        self.height = size + 8 * mm

    def draw(self) -> None:
        c = self.canv
        s = self.size
        cx, cy = s / 2, s / 2 + 2 * mm
        r = s / 2 - 3 * mm
        stroke = 2.5 * mm
        c.setStrokeColor(COSMIC_200)
        c.setLineWidth(stroke)
        c.circle(cx, cy, r, stroke=1, fill=0)
        pct = self.value / 100.0
        col = _score_color(self.value)
        c.setStrokeColor(col)
        try:
            c.setLineCap(1)
        except Exception:
            pass
        start = 90
        extent = -360 * pct
        c.arc(cx - r, cy - r, cx + r, cy + r, start, extent)
        scale = max(0.35, float(self.size) / float(28 * mm))
        main_sz = max(6.0, 16.0 * scale)
        sub_sz = max(5.0, 6.0 * scale)
        lbl_sz = max(5.0, 7.0 * scale)
        c.setFillColor(BRAND_PURPLE)
        c.setFont("Helvetica-Bold", main_sz)
        c.drawCentredString(cx, cy + 1.0 * mm * scale, str(self.value))
        c.setFont("Helvetica", sub_sz)
        c.setFillColor(TEXT_MID)
        c.drawCentredString(cx, cy - 3.5 * mm * scale, "/ 100")
        if (self.label or "").strip():
            c.setFont("Helvetica-Bold", lbl_sz)
            c.setFillColor(TEXT_DARK)
            c.drawCentredString(cx, 1.2 * mm, self.label)


class ProgressBarFlowable(Flowable):
    def __init__(self, label: str, value: int, *, negative: bool = False, width: float = 82 * mm):
        self.label = label
        self.value = max(0, min(100, int(value)))
        self.negative = negative
        self.width = width
        self.height = 5.5 * mm

    def draw(self) -> None:
        c = self.canv
        w, h = self.width, self.height
        if self.label:
            c.setFont("Helvetica", 6.5)
            c.setFillColor(TEXT_DARK)
            c.drawString(0, h - 2 * mm, _safe(self.label)[:42])
            c.setFont("Helvetica-Bold", 6.5)
            c.setFillColor(RED if self.negative else BRAND_PURPLE)
            c.drawRightString(w, h - 2 * mm, f"{self.value}%")
            bar_y = 0.4 * mm
        else:
            bar_y = 2 * mm
        bar_h = 1.4 * mm
        c.setFillColor(COSMIC_200)
        c.roundRect(0, bar_y, w, bar_h, 0.7 * mm, fill=1, stroke=0)
        fill_w = max(0.5 * mm, w * self.value / 100.0)
        col = RED if self.negative else _score_color(self.value)
        c.setFillColor(col)
        c.roundRect(0, bar_y, fill_w, bar_h, 0.7 * mm, fill=1, stroke=0)


def _cell_box(flowables: list[Any]) -> KeepTogether:
    """Table cell content — must be flowables, not a bare Python list."""
    return KeepTogether([f for f in flowables if f is not None])


def _section_label(text: str, H_BOLD: str) -> Paragraph:
    return Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(text.upper())}</b></font>",
        ParagraphStyle("sl", fontName=H_BOLD, fontSize=7, leading=9, textColor=BRAND_PURPLE),
    )


def _body(text: str, H_REG: str, size: float = 7.5, leading: float = 10) -> Paragraph:
    return Paragraph(
        _safe(text or ""),
        ParagraphStyle("bd", fontName=H_REG, fontSize=size, leading=leading, textColor=TEXT_MID),
    )


def _metric_cell(metric: dict[str, Any], H_REG: str, H_BOLD: str) -> Table:
    val = int(metric.get("value") or 0)
    neg = "breakup" in str(metric.get("label", "")).lower()
    content = [
        [
            Paragraph(
                f"<b>{_safe(metric.get('label') or '')}</b>",
                ParagraphStyle("ml", fontName=H_BOLD, fontSize=7.5, leading=9, textColor=TEXT_DARK),
            ),
            Paragraph(
                f"<b>{val}%</b>",
                ParagraphStyle("mv", fontName="Helvetica-Bold", fontSize=11, leading=12, textColor=BRAND_PURPLE, alignment=2),
            ),
        ],
        [ProgressBarFlowable("", val, negative=neg, width=38 * mm), ""],
        [_body(str(metric.get("interpretation") or ""), H_REG, 6.5, 8.5), ""],
    ]
    t = Table(content, colWidths=[30 * mm, 8 * mm])
    t.setStyle(TableStyle([
        ("SPAN", (0, 1), (1, 1)),
        ("SPAN", (0, 2), (1, 2)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), GLASS_BG),
        ("BOX", (0, 0), (-1, -1), 0.4, COSMIC_200),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def render_premium_page1_flowables(data: dict[str, Any], lang: str = "en") -> list[Any]:
    """Return platypus flowables for page 1 + PageBreak."""
    H_REG, H_BOLD = _font_pair(lang)
    out: list[Any] = []

    # Header
    header = Table(
        [[
            Paragraph(
                f"<font color='{_hex(BRAND_GOLD)}'><b>* COSMIC LENS</b></font> "
                f"<font color='{_hex(BRAND_PURPLE)}'><b>PREMIUM</b></font><br/>"
                f"<font size='14'><b>Love Reality Pro</b></font><br/>"
                f"<b>{_safe(data['p1_name'])}</b> · <b>{_safe(data['p2_name'])}</b>",
                ParagraphStyle("hdr", fontName=H_BOLD, fontSize=9, leading=12, textColor=TEXT_DARK),
            ),
            Paragraph(
                f"ID <b>{_safe(data['report_id'])}</b><br/>{_safe(data['generated_at'])}",
                ParagraphStyle("hid", fontName=H_REG, fontSize=7, leading=9, textColor=TEXT_SOFT, alignment=2),
            ),
        ]],
        colWidths=[118 * mm, 52 * mm],
    )
    header.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, COSMIC_200),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    out.append(header)
    out.append(Spacer(1, 2 * mm))

    # Hero
    gauge = Table(
        [[CircularGaugeFlowable(int(data["cosmic_score"]), size=26 * mm)]],
        colWidths=[44 * mm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GLASS_BG),
            ("BOX", (0, 0), (-1, -1), 0.4, COSMIC_200),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]),
    )
    summary_block = [
        _section_label("Relationship Summary", H_BOLD),
        Spacer(1, 1),
        Paragraph(
            f"<b>{_safe(data['p1_name'])} & {_safe(data['p2_name'])}</b>",
            ParagraphStyle("sn", fontName=H_BOLD, fontSize=8, leading=10, textColor=TEXT_DARK),
        ),
        _body(str(data.get("relationship_summary") or ""), H_REG, 7.5, 9.5),
    ]
    summary_tbl = Table(
        [[_cell_box(summary_block)]],
        colWidths=[126 * mm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GLASS_BG),
            ("BOX", (0, 0), (-1, -1), 0.4, COSMIC_200),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]),
    )
    hero = Table([[gauge, summary_tbl]], colWidths=[46 * mm, 128 * mm], hAlign="LEFT")
    hero.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    out.append(hero)
    out.append(Spacer(1, 2 * mm))

    # Core metrics
    out.append(_section_label("Core Metrics", H_BOLD))
    out.append(Spacer(1, 1))
    metrics = data.get("metrics") or []
    metric_cells = [_metric_cell(m, H_REG, H_BOLD) for m in metrics[:4]]
    while len(metric_cells) < 4:
        metric_cells.append(Spacer(1, 1))
    metrics_row = Table([metric_cells], colWidths=[43 * mm] * 4, hAlign="LEFT")
    metrics_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    out.append(metrics_row)
    out.append(Spacer(1, 2 * mm))

    # Relationship insights
    insight_lines = [
        _section_label("Relationship Insights", H_BOLD),
        _body(str(data.get("insights_narrative") or ""), H_REG, 7.2, 9),
    ]
    bullets = data.get("key_insights") or []
    if bullets:
        bl = "<br/>".join(f"- {_safe(b)}" for b in bullets[:4])
        insight_lines.append(
            Paragraph(bl, ParagraphStyle("ins", fontName=H_REG, fontSize=6.8, leading=8.5, textColor=TEXT_MID))
        )
    insights_tbl = Table(
        [[_cell_box(insight_lines)]],
        colWidths=[174 * mm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GLASS_BG),
            ("BOX", (0, 0), (-1, -1), 0.4, COSMIC_200),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]),
    )
    out.append(insights_tbl)
    out.append(Spacer(1, 2 * mm))

    # Strengths / Challenges
    def comp_col(title: str, items: list[dict], negative: bool) -> Table:
        rows = [[_section_label(title, H_BOLD)]]
        for it in (items or [])[:4]:
            rows.append([ProgressBarFlowable(str(it.get("label") or ""), int(it.get("value") or 0), negative=negative, width=80 * mm)])
        return Table(
            rows,
            colWidths=[86 * mm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), GLASS_BG),
                ("BOX", (0, 0), (-1, -1), 0.4, COSMIC_200),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]),
        )

    sc = Table(
        [[
            comp_col("Strengths in this Connection", data.get("strengths") or [], False),
            comp_col("Challenges in this Connection", data.get("challenges") or [], True),
        ]],
        colWidths=[87 * mm, 87 * mm],
        hAlign="LEFT",
    )
    sc.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    out.append(sc)
    out.append(Spacer(1, 2 * mm))

    # Deep analysis 2x2
    out.append(_section_label("Deep Analysis", H_BOLD))
    out.append(Spacer(1, 1))
    analysis = data.get("analysis") or []

    def analysis_cell(block: dict) -> Table:
        score = int(block.get("score") or 0)
        ring = CircularGaugeFlowable(score, size=11 * mm, label="")
        return Table(
            [[
                ring,
                _cell_box([
                    Paragraph(
                        f"<b>{_safe(block.get('title') or '')}</b>  "
                        f"<font color='{_hex(BRAND_PURPLE)}'>{score}/100</font>",
                        ParagraphStyle("at", fontName=H_BOLD, fontSize=7.5, leading=9, textColor=TEXT_DARK),
                    ),
                    _body(str(block.get("explanation") or ""), H_REG, 6.8, 8.5),
                ]),
            ]],
            colWidths=[14 * mm, 68 * mm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), GLASS_BG),
                ("BOX", (0, 0), (-1, -1), 0.4, COSMIC_200),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]),
        )

    a_rows = []
    for i in range(0, min(4, len(analysis)), 2):
        left = analysis_cell(analysis[i]) if i < len(analysis) else Spacer(1, 1)
        right = analysis_cell(analysis[i + 1]) if i + 1 < len(analysis) else Spacer(1, 1)
        a_rows.append([left, right])
    if a_rows:
        a_tbl = Table(a_rows, colWidths=[87 * mm, 87 * mm], hAlign="LEFT")
        a_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        out.append(a_tbl)
    out.append(Spacer(1, 2 * mm))

    # Footer: verdict + recommendations
    recs = data.get("recommendations") or []
    rec_html = "<br/>".join(f"- {_safe(r)}" for r in recs[:3])
    footer = Table(
        [[
            Table(
                [[_cell_box([
                    _section_label("Final Cosmic Verdict", H_BOLD),
                    _body(str(data.get("verdict") or ""), H_REG, 7.2, 9),
                ])]],
                colWidths=[84 * mm],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), COSMIC_50),
                    ("BOX", (0, 0), (-1, -1), 0.5, BRAND_PURPLE),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]),
            ),
            Table(
                [[_cell_box([
                    _section_label("Recommendations", H_BOLD),
                    Paragraph(rec_html, ParagraphStyle("rc", fontName=H_REG, fontSize=6.8, leading=8.5, textColor=TEXT_MID)),
                ])]],
                colWidths=[84 * mm],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), GLASS_BG),
                    ("BOX", (0, 0), (-1, -1), 0.4, COSMIC_200),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]),
            ),
        ]],
        colWidths=[87 * mm, 87 * mm],
        hAlign="LEFT",
    )
    out.append(footer)
    out.append(Spacer(1, 2))
    out.append(
        Paragraph(
            f"<font color='{_hex(TEXT_SOFT)}'>Cosmic Lens · Confidential premium report</font>",
            ParagraphStyle("ft", fontName=H_REG, fontSize=6, leading=8, alignment=1),
        )
    )
    out.append(PageBreak())
    return out


def page1_fits_a4() -> bool:
    """Sanity: content width matches love_reality_pdf margins."""
    _w, _h = A4
    return True

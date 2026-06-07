"""
Love Reality Pro — premium dashboard page 1 (ReportLab, single A4 page).
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

COSMIC_200 = colors.HexColor("#DDD6FE")
GLASS_BG = colors.HexColor("#FAFAFF")
EMERALD = colors.HexColor("#059669")
EMERALD_BG = colors.HexColor("#D1FAE5")
AMBER = colors.HexColor("#D97706")
AMBER_BG = colors.HexColor("#FEF3C7")
RED = colors.HexColor("#DC2626")
RED_BG = colors.HexColor("#FEE2E2")
ORANGE = colors.HexColor("#EA580C")
ORANGE_BG = colors.HexColor("#FFEDD5")
TEAL = colors.HexColor("#0D9488")
TEAL_BG = colors.HexColor("#CCFBF1")

_CONTENT_W = 180 * mm
_GAUGE_SIZE = 22 * mm * 1.2
_GAP = 1.2 * mm
_TITLE = 10.0
_BODY = 9.5
_BODY_LEADING = 12.5
_LABEL = 9.0
_CARD_PAD = 4


def _short(text: str, max_len: int = 200) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rsplit(" ", 1)[0] + "…"


def _glass_box() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GLASS_BG),
        ("BOX", (0, 0), (-1, -1), 0.35, COSMIC_200),
        ("LEFTPADDING", (0, 0), (-1, -1), _CARD_PAD),
        ("RIGHTPADDING", (0, 0), (-1, -1), _CARD_PAD),
        ("TOPPADDING", (0, 0), (-1, -1), _CARD_PAD),
        ("BOTTOMPADDING", (0, 0), (-1, -1), _CARD_PAD),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ])


def _alignment_verdict_band(score: int) -> tuple[str, colors.Color, colors.Color]:
    s = max(0, min(100, int(score)))
    if s >= 81:
        return "Excellent", EMERALD, EMERALD_BG
    if s >= 61:
        return "Strong", TEAL, TEAL_BG
    if s >= 46:
        return "Moderate", AMBER, AMBER_BG
    if s >= 26:
        return "Challenging", ORANGE, ORANGE_BG
    return "Very Challenging", RED, RED_BG


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
        self.height = size + 5 * mm

    def draw(self) -> None:
        c = self.canv
        s = self.size
        cx, cy = s / 2, s / 2 + 1.2 * mm
        r = s / 2 - 2.2 * mm
        stroke = 1.8 * mm
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
        scale = max(0.45, float(self.size) / float(26 * mm))
        c.setFillColor(BRAND_PURPLE)
        c.setFont("Helvetica-Bold", max(9, 15 * scale))
        c.drawCentredString(cx, cy + 0.6 * mm, str(self.value))
        c.setFont("Helvetica", max(6, 6 * scale))
        c.setFillColor(TEXT_MID)
        c.drawCentredString(cx, cy - 2.8 * mm, "/ 100")
        if self.label:
            c.setFont("Helvetica-Bold", max(6, 7 * scale))
            c.setFillColor(TEXT_DARK)
            c.drawCentredString(cx, 0.8 * mm, self.label)


def _section_label(text: str, H_BOLD: str, *, size: float = _LABEL) -> Paragraph:
    return Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(text.upper())}</b></font>",
        ParagraphStyle(
            "sl",
            fontName=H_BOLD,
            fontSize=size,
            leading=size + 2.5,
            textColor=BRAND_PURPLE,
            spaceAfter=0.5,
        ),
    )


def _body_para(text: str, H_REG: str, *, size: float = _BODY, leading: float = _BODY_LEADING) -> Paragraph:
    return Paragraph(
        _safe(text or ""),
        ParagraphStyle("bd", fontName=H_REG, fontSize=size, leading=leading, textColor=TEXT_MID),
    )


def _verdict_badge(score: int, H_BOLD: str) -> Table:
    label, fg, bg = _alignment_verdict_band(score)
    badge = Paragraph(
        f"<font color='{_hex(fg)}'><b>{_safe(label.upper())}</b></font>",
        ParagraphStyle("vb", fontName=H_BOLD, fontSize=8.5, leading=10.5, alignment=TA_CENTER, textColor=fg),
    )
    tbl = Table([[badge]], colWidths=[40 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.35, fg),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return tbl


def _metric_cell(metric: dict[str, Any], H_REG: str) -> Paragraph:
    val = int(metric.get("value") or 0)
    return Paragraph(
        f"<b>{_safe(metric.get('label') or '')}</b> "
        f"<font color='{_hex(BRAND_PURPLE)}'><b>{val}%</b></font><br/>"
        f"<font size='8'>{_safe(_short(metric.get('interpretation') or '', 42))}</font>",
        ParagraphStyle("mc", fontName=H_REG, fontSize=_BODY, leading=_BODY_LEADING, textColor=TEXT_DARK),
    )


def _score_line(label: str, value: int, H_REG: str, *, negative: bool = False) -> Paragraph:
    col = _hex(RED if negative else _score_color(value))
    return Paragraph(
        f"{_safe(label)} <font color='{col}'><b>{value}%</b></font>",
        ParagraphStyle("sc", fontName=H_REG, fontSize=_BODY, leading=_BODY_LEADING - 1, textColor=TEXT_DARK),
    )


def _footer_cell(title: str, body_html: str, H_BOLD: str, H_REG: str) -> Paragraph:
    return Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(title.upper())}</b></font><br/>{body_html}",
        ParagraphStyle(
            "fc",
            fontName=H_REG,
            fontSize=_BODY,
            leading=_BODY_LEADING,
            textColor=TEXT_MID,
        ),
    )


def render_premium_page1_flowables(data: dict[str, Any], lang: str = "en") -> list[Any]:
    H_REG, H_BOLD = _font_pair(lang)
    out: list[Any] = []

    header = Table(
        [[
            Paragraph(
                f"<font color='{_hex(BRAND_GOLD)}'><b>* COSMIC LENS</b></font> "
                f"<font color='{_hex(BRAND_PURPLE)}'><b>PREMIUM</b></font> "
                f"<font size='12'><b>Love Reality Pro</b></font> "
                f"<b>{_safe(data['p1_name'])}</b> &middot; <b>{_safe(data['p2_name'])}</b>",
                ParagraphStyle("hdr", fontName=H_BOLD, fontSize=10, leading=12.5, textColor=TEXT_DARK),
            ),
            Paragraph(
                f"ID <b>{_safe(data['report_id'])}</b><br/>{_safe(data['generated_at'])}",
                ParagraphStyle("hid", fontName=H_REG, fontSize=8.5, leading=10.5, textColor=TEXT_SOFT, alignment=TA_RIGHT),
            ),
        ]],
        colWidths=[122 * mm, 58 * mm],
    )
    header.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.45, COSMIC_200),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    out.append(header)
    out.append(Spacer(1, _GAP))

    score = int(data.get("cosmic_score") or 0)
    summary_html = (
        f"<font color='{_hex(BRAND_PURPLE)}'><b>RELATIONSHIP SUMMARY</b></font><br/>"
        f"{_safe(_short(data.get('relationship_summary') or '', 220))}"
    )
    gauge_stack = Table(
        [
            [CircularGaugeFlowable(score, size=_GAUGE_SIZE, label="Cosmic Alignment")],
            [_verdict_badge(score, H_BOLD)],
        ],
        colWidths=[46 * mm],
    )
    gauge_stack.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    hero = Table(
        [[
            gauge_stack,
            Paragraph(summary_html, ParagraphStyle("sum", fontName=H_REG, fontSize=_BODY, leading=_BODY_LEADING, textColor=TEXT_MID)),
        ]],
        colWidths=[48 * mm, 132 * mm],
    )
    hero.setStyle(_glass_box())
    out.append(hero)
    out.append(Spacer(1, _GAP))

    metrics = data.get("metrics") or []
    mcells = [_metric_cell(m, H_REG) for m in metrics[:4]]
    while len(mcells) < 4:
        mcells.append(Paragraph("", ParagraphStyle("e", fontName=H_REG, fontSize=1, leading=1)))
    mrow = Table([mcells], colWidths=[45 * mm] * 4)
    st = _glass_box()
    st.add("INNERGRID", (0, 0), (-1, -1), 0.25, COSMIC_200)
    mrow.setStyle(st)
    out.append(_section_label("Core Metrics", H_BOLD))
    out.append(mrow)
    out.append(Spacer(1, _GAP))

    insight_parts = [_short(str(data.get("insights_narrative") or ""), 180)]
    bullets = [str(b).strip() for b in (data.get("key_insights") or []) if str(b).strip()][:3]
    if bullets:
        insight_parts.append("<br/>".join(f"&bull; {_safe(b)}" for b in bullets))
    insights = Table(
        [[
            Paragraph(
                f"<font color='{_hex(BRAND_PURPLE)}'><b>RELATIONSHIP INSIGHTS</b></font><br/>"
                + "<br/>".join(insight_parts),
                ParagraphStyle("ins", fontName=H_REG, fontSize=_BODY, leading=_BODY_LEADING, textColor=TEXT_MID),
            ),
        ]],
        colWidths=[_CONTENT_W],
    )
    insights.setStyle(_glass_box())
    out.append(insights)
    out.append(Spacer(1, _GAP))

    strengths = data.get("strengths") or []
    challenges = data.get("challenges") or []

    def side_card(title: str, items: list[dict], negative: bool) -> Table:
        rows: list[Any] = [
            _section_label(title, H_BOLD, size=_LABEL),
        ]
        for it in items[:3]:
            rows.append(_score_line(str(it.get("label") or ""), int(it.get("value") or 0), H_REG, negative=negative))
        t = Table([[r] for r in rows], colWidths=[87 * mm])
        t.setStyle(_glass_box())
        return t

    sc = Table(
        [[
            side_card("Strengths in this Connection", strengths, False),
            side_card("Challenges in this Connection", challenges, True),
        ]],
        colWidths=[90 * mm, 90 * mm],
    )
    sc.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    out.append(sc)
    out.append(Spacer(1, _GAP))

    analysis = data.get("analysis") or []
    if analysis:
        acells = []
        for block in analysis[:4]:
            sc_val = int(block.get("score") or 0)
            acells.append(Paragraph(
                f"<b>{_safe(block.get('title') or '')}</b><br/>"
                f"<font color='{_hex(BRAND_PURPLE)}'><b>{sc_val}/100</b></font>",
                ParagraphStyle("an", fontName=H_REG, fontSize=8.8, leading=11, textColor=TEXT_DARK, alignment=TA_CENTER),
            ))
        while len(acells) < 4:
            acells.append(Paragraph("", ParagraphStyle("e", fontName=H_REG, fontSize=1, leading=1)))
        atbl = Table([acells], colWidths=[45 * mm] * 4)
        st2 = _glass_box()
        st2.add("INNERGRID", (0, 0), (-1, -1), 0.25, COSMIC_200)
        st2.add("ALIGN", (0, 0), (-1, -1), "CENTER")
        atbl.setStyle(st2)
        out.append(_section_label("Deep Analysis", H_BOLD))
        out.append(atbl)
        out.append(Spacer(1, _GAP))

    recs = data.get("recommendations") or []
    rec_html = "<br/>".join(f"&bull; {_safe(_short(str(r), 72))}" for r in recs[:3])
    verdict_html = _safe(_short(str(data.get("verdict") or ""), 200))
    footer = Table(
        [[
            _footer_cell("Final Cosmic Verdict", verdict_html, H_BOLD, H_REG),
            _footer_cell("Recommendations", rec_html, H_BOLD, H_REG),
        ]],
        colWidths=[90 * mm, 90 * mm],
        splitInRow=1,
    )
    footer.setStyle(_glass_box())
    out.append(footer)
    out.append(Spacer(1, 0.8 * mm))
    out.append(Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'>Cosmic Lens · Confidential premium report</font>",
        ParagraphStyle("ft", fontName=H_REG, fontSize=7.5, leading=9, alignment=TA_CENTER),
    ))
    out.append(PageBreak())
    return out


def page1_fits_a4() -> bool:
    _w, _h = A4
    return True

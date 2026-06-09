"""
Love Reality Pro — premium executive summary (page 1) + deep analysis (page 2).
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
    _pick_body_premium,
    _premium_body_markup,
    _premium_prose_markup,
    _safe,
    _styles,
    register_indic_fonts,
)

COSMIC_200 = colors.HexColor("#DDD6FE")
COSMIC_300 = colors.HexColor("#C4B5FD")
GLASS_BG = colors.HexColor("#F8F7FF")
GLASS_STRONG = colors.HexColor("#F3F0FF")
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
VERDICT_BG = colors.HexColor("#F5F3FF")

_CONTENT_W = 180 * mm
_GAUGE_SIZE = 38 * mm  # hero — ~45% larger than prior compact gauge
_GAP = 2.2 * mm
_SECTION = 12.5
_BODY = 12.5
_BODY_LEADING = 16.5
_METRIC = 12.5
_CARD_PAD = 6
_STRENGTH_ICONS = ("★", "♥", "✦", "◆")
_CHALLENGE_ICONS = ("⚠", "✗", "▼", "◆")


def _short(text: str, max_len: int = 200) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rsplit(" ", 1)[0] + "…"


def _prose_html(text: str, *, max_len: int | None = None) -> str:
    """Preserve LLM paragraph breaks for ReportLab Paragraph."""
    t = (text or "").strip()
    if max_len and len(t) > max_len:
        t = _short(t, max_len)
    parts = [p.strip() for p in t.replace("\r\n", "\n").split("\n\n") if p.strip()]
    if not parts:
        return _safe(t)
    return "<br/><br/>".join(_safe(p.replace("\n", " ")) for p in parts)


def _strong_card(*, accent: bool = False) -> TableStyle:
    bg = GLASS_STRONG if accent else GLASS_BG
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.65, COSMIC_300 if accent else COSMIC_200),
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
    """Hero cosmic alignment gauge."""

    def __init__(self, value: int, size: float = _GAUGE_SIZE, label: str = "Cosmic Alignment"):
        self.value = max(0, min(100, int(value)))
        self.size = size
        self.label = label
        self.width = size
        self.height = size + 4 * mm

    def draw(self) -> None:
        c = self.canv
        s = self.size
        cx, cy = s / 2, s / 2 + 1.5 * mm
        r = s / 2 - 3 * mm
        stroke = 2.6 * mm
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
        scale = max(0.55, float(self.size) / float(38 * mm))
        c.setFillColor(BRAND_PURPLE)
        c.setFont("Helvetica-Bold", max(14, 22 * scale))
        c.drawCentredString(cx, cy + 1.2 * mm, str(self.value))
        c.setFont("Helvetica", max(8, 9 * scale))
        c.setFillColor(TEXT_MID)
        c.drawCentredString(cx, cy - 4 * mm, "/ 100")
        if self.label:
            c.setFont("Helvetica-Bold", max(8, 9.5 * scale))
            c.setFillColor(TEXT_DARK)
            c.drawCentredString(cx, 1.2 * mm, self.label)


class HorizontalProgressBar(Flowable):
    """Scan-friendly progress bar for strengths / challenges."""

    def __init__(
        self,
        value: int,
        width: float,
        *,
        height: float = 3.8 * mm,
        fill: colors.Color,
        track: colors.Color | None = None,
    ):
        self.value = max(0, min(100, int(value)))
        self.width = width
        self.height = height
        self.fill = fill
        self.track = track or COSMIC_200

    def draw(self) -> None:
        c = self.canv
        h = self.height
        w = self.width
        c.setFillColor(self.track)
        c.roundRect(0, 0, w, h, min(h / 2, 1.8 * mm), stroke=0, fill=1)
        fw = max(h, w * (self.value / 100.0))
        if fw > 0:
            c.setFillColor(self.fill)
            c.roundRect(0, 0, fw, h, min(h / 2, 1.8 * mm), stroke=0, fill=1)


def _section_label(text: str, H_BOLD: str, *, size: float = _SECTION) -> Paragraph:
    return Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'>{_safe(text.upper())}</font>",
        ParagraphStyle(
            "sl",
            fontName=H_BOLD,
            fontSize=size,
            leading=size + 3,
            textColor=BRAND_PURPLE,
            spaceAfter=1,
        ),
    )


def _verdict_badge(score: int, H_BOLD: str) -> Table:
    label, fg, bg = _alignment_verdict_band(score)
    badge = Paragraph(
        f"<font color='{_hex(fg)}'>{_safe(label.upper())}</font>",
        ParagraphStyle("vb", fontName=H_BOLD, fontSize=10.5, leading=13, alignment=TA_CENTER, textColor=fg),
    )
    tbl = Table([[badge]], colWidths=[52 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.5, fg),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tbl


def _metric_cell(metric: dict[str, Any], H_REG: str, H_BOLD: str) -> Paragraph:
    val = int(metric.get("value") or 0)
    return Paragraph(
        f"<font name='{H_BOLD}'>{_safe(metric.get('label') or '')}</font><br/>"
        f"<font size='12.5' name='{H_BOLD}'>{val}%</font><br/>"
        f"<font size='12.5' name='{H_REG}'>{_safe(_short(metric.get('interpretation') or '', 38))}</font>",
        ParagraphStyle("mc", fontName=H_REG, fontSize=_METRIC, leading=_BODY_LEADING, textColor=TEXT_DARK),
    )


def _progress_row(
    icon: str,
    label: str,
    value: int,
    H_REG: str,
    H_BOLD: str,
    *,
    negative: bool = False,
) -> Table:
    bar_w = 52 * mm
    fill = RED if negative else _score_color(value)
    pct = Paragraph(
        f"<font color='{_hex(fill)}'>{value}%</font>",
        ParagraphStyle("pv", fontName=H_BOLD, fontSize=_BODY, leading=_BODY_LEADING, alignment=TA_RIGHT, textColor=fill),
    )
    lbl = Paragraph(
        _safe(label),
        ParagraphStyle("pl", fontName=H_REG, fontSize=_BODY, leading=_BODY_LEADING, textColor=TEXT_DARK),
    )
    icon_p = Paragraph(
        f"<font color='{_hex(fill)}'>{icon}</font>",
        ParagraphStyle("pi", fontName=H_BOLD, fontSize=12, leading=12, alignment=TA_CENTER),
    )
    row = Table(
        [[icon_p, lbl, HorizontalProgressBar(value, bar_w, fill=fill), pct]],
        colWidths=[7 * mm, 24 * mm, bar_w, 12 * mm],
    )
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return row


def _side_panel(title: str, items: list[dict], H_REG: str, H_BOLD: str, *, negative: bool) -> Table:
    icons = _CHALLENGE_ICONS if negative else _STRENGTH_ICONS
    rows: list[Any] = [_section_label(title, H_BOLD, size=_BODY)]
    for i, it in enumerate((items or [])[:3]):
        rows.append(_progress_row(
            icons[i % len(icons)],
            str(it.get("label") or ""),
            int(it.get("value") or 0),
            H_REG,
            H_BOLD,
            negative=negative,
        ))
    t = Table([[r] for r in rows], colWidths=[87 * mm])
    t.setStyle(_strong_card())
    return t


def _premium_verdict_card(
    verdict: str,
    score: int,
    H_REG: str,
    H_BOLD: str,
    *,
    hero: bool = False,
    lang: str = "en",
    extra_paragraphs: list[str] | None = None,
) -> Table:
    parts = [verdict.strip()] if str(verdict or "").strip() else []
    for block in extra_paragraphs or []:
        t = str(block).strip()
        if t:
            parts.append(t)
    merged = "\n\n".join(parts)
    body = Paragraph(
        _prose_html(merged, max_len=None if hero else 240, lang=lang),
        ParagraphStyle(
            "vd", fontName=H_REG, fontSize=_BODY, leading=_BODY_LEADING, textColor=TEXT_DARK,
            wordWrap="CJK" if lang == "hi" else "normal",
        ),
    )
    badge = Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'>Overall bond · {score}/100</font>",
        ParagraphStyle("vbd", fontName=H_REG, fontSize=9, leading=11, alignment=TA_RIGHT),
    )
    if lang == "hi":
        note_title = "ज्योतिषी का नोट"
    elif lang == "hn":
        note_title = "Astrologer Ka Note"
    else:
        note_title = "Astrologer's Note"
    title = Paragraph(
        f"<font color='{_hex(BRAND_GOLD)}'>✦</font> "
        f"<font color='{_hex(BRAND_PURPLE)}' name='{H_BOLD}'>{_safe(note_title.upper())}</font>",
        ParagraphStyle("vt", fontName=H_BOLD, fontSize=_BODY, leading=_BODY_LEADING,
                        textColor=BRAND_PURPLE, wordWrap="CJK" if lang == "hi" else "normal"),
    )
    pad = 12 if hero else 6
    tbl = Table([[title], [badge], [body]], colWidths=[_CONTENT_W])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), VERDICT_BG),
        ("BOX", (0, 0), (-1, -1), 1.2 if hero else 1.0, BRAND_PURPLE),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, COSMIC_300),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad if hero else 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad if hero else 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 1), (-1, 1), "RIGHT"),
    ]))
    return tbl


def _recommendations_card(
    recs: list[str],
    H_REG: str,
    H_BOLD: str,
    *,
    hero: bool = False,
    paragraph_mode: bool = False,
    lang: str = "en",
) -> Table:
    items = [str(r).strip() for r in recs if str(r).strip()]
    use_paragraphs = paragraph_mode or (hero and any(len(x) > 100 for x in items))
    if use_paragraphs:
        blocks = [_prose_html(item, lang=lang) for item in items[:3]]
        body_html = "<br/><br/>".join(blocks) if blocks else "—"
    else:
        bullet_max = 110 if hero else 78
        if lang == "hi":
            lines = [
                _premium_body_markup(f"• {_short(str(r), bullet_max)}", lang)
                for r in items[:5]
            ]
        else:
            lines = [f"&bull; {_safe(_short(str(r), bullet_max))}" for r in items[:5]]
        body_html = "<br/>".join(lines) if lines else "—"
    body = Paragraph(
        body_html,
        ParagraphStyle(
            "rc", fontName=H_REG, fontSize=_BODY, leading=_BODY_LEADING,
            textColor=TEXT_DARK if hero else TEXT_MID, leftIndent=6 if hero else 4,
            wordWrap="CJK" if lang == "hi" else "normal",
        ),
    )
    rec_title = "Aage Kya Karein" if lang == "hn" else "What To Do Next"
    title = _section_label(rec_title, H_BOLD, size=_BODY)
    tbl = Table([[title], [body]], colWidths=[_CONTENT_W])
    st = _strong_card(accent=hero)
    if hero:
        st.add("TOPPADDING", (0, 0), (-1, -1), 10)
        st.add("BOTTOMPADDING", (0, 0), (-1, -1), 10)
        st.add("LEFTPADDING", (0, 0), (-1, -1), 10)
        st.add("RIGHTPADDING", (0, 0), (-1, -1), 10)
    tbl.setStyle(st)
    return tbl


def render_premium_page1_flowables(data: dict[str, Any], lang: str = "en") -> list[Any]:
    """Executive summary — single premium dashboard page."""
    if (lang or "").lower() == "hi":
        register_indic_fonts(force=True)
    H_REG, H_BOLD = _font_pair(lang)
    s = _styles(lang)
    out: list[Any] = []

    header = Table(
        [[
            Paragraph(
                f"<font color='{_hex(BRAND_GOLD)}'>✦ COSMIC LENS PREMIUM</font><br/>"
                f"<font size='14' name='{H_BOLD}'>Love Reality Pro</font><br/>"
                f"<font name='{H_BOLD}'>{_safe(data['p1_name'])}</font> &amp; "
                f"<font name='{H_BOLD}'>{_safe(data['p2_name'])}</font>",
                ParagraphStyle("hdr", fontName=H_BOLD, fontSize=11, leading=14, textColor=TEXT_DARK),
            ),
            Paragraph(
                f"ID <font name='{H_BOLD}'>{_safe(data['report_id'])}</font><br/>{_safe(data['generated_at'])}",
                ParagraphStyle("hid", fontName=H_REG, fontSize=10, leading=12.5, textColor=TEXT_SOFT, alignment=TA_RIGHT),
            ),
        ]],
        colWidths=[118 * mm, 62 * mm],
    )
    header.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.6, COSMIC_300),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    out.append(header)
    out.append(Spacer(1, _GAP))

    score = int(data.get("cosmic_score") or 0)
    gauge_block = Table(
        [
            [CircularGaugeFlowable(score, size=_GAUGE_SIZE, label="Cosmic Alignment Score")],
            [Spacer(1, 1.5 * mm)],
            [_verdict_badge(score, H_BOLD)],
        ],
        colWidths=[_CONTENT_W],
    )
    gauge_block.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    summ_plain = _short(data.get("relationship_summary") or "", 260)
    summ_body = _pick_body_premium(summ_plain, s, lang, relax=True)
    summary = Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}' name='{summ_body.fontName}'>RELATIONSHIP SUMMARY</font><br/>"
        f"{_premium_body_markup(summ_plain, lang) or _safe(summ_plain)}",
        summ_body,
    )
    hero = Table([[gauge_block], [summary]], colWidths=[_CONTENT_W])
    hero.setStyle(_strong_card(accent=True))
    out.append(hero)
    out.append(Spacer(1, _GAP))

    metrics = data.get("metrics") or []
    mcells = [_metric_cell(m, H_REG, H_BOLD) for m in metrics[:4]]
    while len(mcells) < 4:
        mcells.append(Paragraph("", ParagraphStyle("e", fontName=H_REG, fontSize=1, leading=1)))
    mrow = Table([mcells], colWidths=[45 * mm] * 4)
    st = _strong_card()
    st.add("INNERGRID", (0, 0), (-1, -1), 0.35, COSMIC_200)
    st.add("ALIGN", (0, 0), (-1, -1), "CENTER")
    mrow.setStyle(st)
    out.append(_section_label("Core Metrics", H_BOLD))
    out.append(Spacer(1, 1 * mm))
    out.append(mrow)
    out.append(Spacer(1, _GAP))

    insight_parts = [_short(str(data.get("insights_narrative") or ""), 220)]
    bullets = [str(b).strip() for b in (data.get("key_insights") or []) if str(b).strip()][:4]
    if bullets:
        insight_parts.append("<br/>".join(f"&bull; {_safe(b)}" for b in bullets))
    insights = Table(
        [[Paragraph(
            f"<font color='{_hex(BRAND_PURPLE)}' name='{H_BOLD}'>RELATIONSHIP INSIGHTS</font><br/>"
            + "<br/>".join(insight_parts),
            ParagraphStyle(
                "ins", fontName=H_REG, fontSize=_BODY, leading=_BODY_LEADING, textColor=TEXT_MID,
                wordWrap="CJK" if lang == "hi" else "normal",
            ),
        )]],
        colWidths=[_CONTENT_W],
    )
    insights.setStyle(_strong_card())
    out.append(insights)
    out.append(Spacer(1, _GAP))

    sc = Table(
        [[
            _side_panel("Strengths in this Connection", data.get("strengths") or [], H_REG, H_BOLD, negative=False),
            _side_panel("Challenges in this Connection", data.get("challenges") or [], H_REG, H_BOLD, negative=True),
        ]],
        colWidths=[90 * mm, 90 * mm],
    )
    sc.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    out.append(sc)
    out.append(PageBreak())
    return out


def render_verdict_page_flowables(data: dict[str, Any], lang: str = "en") -> list[Any]:
    """Dedicated page — one unified astrologer's note (interpretation + guidance in one flow)."""
    if (lang or "").lower() == "hi":
        register_indic_fonts(force=True)
    H_REG, H_BOLD = _font_pair(lang)
    score = int(data.get("cosmic_score") or 0)
    recs = data.get("recommendation_paragraphs") or data.get("recommendations") or []
    if isinstance(recs, str):
        recs = [recs]
    out: list[Any] = []

    out.append(Spacer(1, 3 * mm))
    out.append(
        Paragraph(
            f"<font color='{_hex(TEXT_SOFT)}' name='{H_BOLD}'>02</font> "
            f"<font color='{_hex(BRAND_PURPLE)}' name='{H_BOLD}'>{_safe(data['p1_name'])}</font> &amp; "
            f"<font color='{_hex(BRAND_PURPLE)}' name='{H_BOLD}'>{_safe(data['p2_name'])}</font>",
            ParagraphStyle("vp_h", fontName=H_BOLD, fontSize=_BODY, leading=_BODY_LEADING, textColor=TEXT_DARK),
        )
    )
    out.append(Spacer(1, 2 * mm))
    out.append(_premium_verdict_card(
        str(data.get("verdict") or ""),
        score,
        H_REG,
        H_BOLD,
        hero=True,
        lang=lang,
        extra_paragraphs=[str(x) for x in recs if str(x).strip()],
    ))
    out.append(Spacer(1, 3 * mm))
    out.append(Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'>Cosmic Lens · Confidential premium report</font>",
        ParagraphStyle("ft", fontName=H_REG, fontSize=9, leading=11, alignment=TA_CENTER),
    ))
    out.append(PageBreak())
    return out


def render_deep_analysis_page2_flowables(data: dict[str, Any], lang: str = "en") -> list[Any]:
    """Four dimension deep-dives — page 2 opener."""
    if (lang or "").lower() == "hi":
        register_indic_fonts(force=True)
    H_REG, H_BOLD = _font_pair(lang)
    s = _styles(lang)
    out: list[Any] = []

    out.append(_section_label("Deep Connection Analysis", H_BOLD, size=13))
    out.append(Spacer(1, 1.5 * mm))
    out.append(Paragraph(
        "Detailed compatibility breakdown — emotional rhythm, communication, trust, and long-term potential.",
        ParagraphStyle("da", fontName=H_REG, fontSize=10.5, leading=13, textColor=TEXT_MID),
    ))
    out.append(Spacer(1, _GAP))

    analysis = data.get("analysis") or []

    def block_para(item: dict) -> Paragraph:
        sc_val = int(item.get("score") or 0)
        expl = str(item.get("explanation") or "")
        title = str(item.get("title") or "")
        body_style = _pick_body_premium(expl, s, lang, relax=True)
        return Paragraph(
            f'<font name="{H_BOLD}">{_safe(title)}</font> '
            f'<font color="{_hex(BRAND_PURPLE)}" name="{H_BOLD}">{sc_val}/100</font><br/>'
            f'{_premium_body_markup(expl, lang) or _safe(expl)}',
            body_style,
        )

    rows: list[list[Any]] = []
    for i in range(0, min(4, len(analysis)), 2):
        left = block_para(analysis[i]) if i < len(analysis) else Paragraph("", ParagraphStyle("e", fontName=H_REG, fontSize=1))
        right = block_para(analysis[i + 1]) if i + 1 < len(analysis) else Paragraph("", ParagraphStyle("e", fontName=H_REG, fontSize=1))
        rows.append([left, right])

    if rows:
        grid = Table(rows, colWidths=[90 * mm, 90 * mm])
        st = _strong_card(accent=True)
        st.add("INNERGRID", (0, 0), (-1, -1), 0.35, COSMIC_200)
        grid.setStyle(st)
        out.append(grid)

    out.append(PageBreak())
    return out


def page1_fits_a4() -> bool:
    _w, _h = A4
    return True

"""
pdf_renderer.py — Phase 4.5
Render Business Vastu and AstroVastu PRO reports to a PDF binary using
ReportLab. Bilingual (EN + Hi-Latin) layout, brand-safe footer
("Powered by Advanced Cosmic Intelligence" — never AI/LLM).
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ─────────────────────────────────────────────────────────────────────
# Brand palette (matches mobile app)
# ─────────────────────────────────────────────────────────────────────
BRAND_PURPLE = colors.HexColor("#7C3AED")
BRAND_GOLD   = colors.HexColor("#F5B700")
TEXT_DARK    = colors.HexColor("#0F172A")
TEXT_MID     = colors.HexColor("#475569")
TEXT_SOFT    = colors.HexColor("#94A3B8")
BG_CARD      = colors.HexColor("#F8FAFC")
BORDER       = colors.HexColor("#E2E8F0")

VERDICT_BG = {
    "Ideal":              colors.HexColor("#D1FAE5"),
    "Acceptable":         colors.HexColor("#DBEAFE"),
    "Adjustment Needed":  colors.HexColor("#FEF3C7"),
    "Avoid":              colors.HexColor("#FEE2E2"),
}
VERDICT_FG = {
    "Ideal":              colors.HexColor("#047857"),
    "Acceptable":         colors.HexColor("#1D4ED8"),
    "Adjustment Needed":  colors.HexColor("#B45309"),
    "Avoid":              colors.HexColor("#B91C1C"),
}
GRADE_COLOR = {
    "A": colors.HexColor("#10B981"),
    "B": colors.HexColor("#3B82F6"),
    "C": colors.HexColor("#F59E0B"),
    "D": colors.HexColor("#EF4444"),
}

# ─────────────────────────────────────────────────────────────────────
def _styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title":  ParagraphStyle("title",  parent=base["Title"],
                                 fontSize=22, leading=26, textColor=BRAND_PURPLE,
                                 alignment=TA_LEFT, spaceAfter=4),
        "sub":    ParagraphStyle("sub",    parent=base["Normal"],
                                 fontSize=11, leading=14, textColor=TEXT_MID,
                                 alignment=TA_LEFT, spaceAfter=10),
        "h2":     ParagraphStyle("h2",     parent=base["Heading2"],
                                 fontSize=14, leading=18, textColor=BRAND_PURPLE,
                                 spaceBefore=10, spaceAfter=4),
        "h3":     ParagraphStyle("h3",     parent=base["Heading3"],
                                 fontSize=12, leading=15, textColor=TEXT_DARK,
                                 spaceBefore=8, spaceAfter=2),
        "body":   ParagraphStyle("body",   parent=base["Normal"],
                                 fontSize=10, leading=13, textColor=TEXT_DARK),
        "bodyHi": ParagraphStyle("bodyHi", parent=base["Normal"],
                                 fontSize=9, leading=12, textColor=TEXT_MID),
        "small":  ParagraphStyle("small",  parent=base["Normal"],
                                 fontSize=8, leading=10, textColor=TEXT_SOFT),
        "footer": ParagraphStyle("footer", parent=base["Normal"],
                                 fontSize=8, leading=10, textColor=TEXT_SOFT,
                                 alignment=TA_CENTER),
        "score":  ParagraphStyle("score",  parent=base["Normal"],
                                 fontSize=42, leading=46, textColor=BRAND_PURPLE,
                                 alignment=TA_CENTER),
        "grade":  ParagraphStyle("grade",  parent=base["Normal"],
                                 fontSize=12, leading=14,
                                 alignment=TA_CENTER, textColor=colors.white),
    }


def _safe(s: Any) -> str:
    """Escape & truncate for ReportLab Paragraph."""
    if s is None:
        return ""
    t = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return t


def _on_page(canvas, doc):
    """Draw page header/footer on every page."""
    canvas.saveState()
    w, h = A4
    # Top brand bar
    canvas.setFillColor(BRAND_PURPLE)
    canvas.rect(0, h - 8, w, 8, stroke=0, fill=1)
    # Footer
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(TEXT_SOFT)
    canvas.drawCentredString(w / 2, 12,
                             "Cosmic Lens  ·  Powered by Advanced Cosmic Intelligence  ·  "
                             f"Page {doc.page}")
    canvas.restoreState()


# ─────────────────────────────────────────────────────────────────────
def _score_block(s: ParagraphStyle, score: int, grade: str,
                 summary_en: str, summary_hi: str, label: str) -> Table:
    grade_color = GRADE_COLOR.get(grade, BRAND_PURPLE)
    score_p = Paragraph(f"<b>{score}</b><font size=14 color='#94A3B8'> /100</font>", s["score"])
    grade_p = Paragraph(f"<b>Grade {_safe(grade)}</b>", s["grade"])
    grade_cell = Table([[grade_p]], colWidths=[40 * mm], rowHeights=[18])
    grade_cell.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), grade_color),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    left = Table([[score_p], [grade_cell]], colWidths=[60 * mm])
    left.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    right = Table([
        [Paragraph(f"<b>{_safe(label)}</b>", s["h3"])],
        [Paragraph(_safe(summary_en), s["body"])],
        [Paragraph(_safe(summary_hi), s["bodyHi"])],
    ], colWidths=[110 * mm])
    right.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    outer = Table([[left, right]], colWidths=[60 * mm, 110 * mm])
    outer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return outer


def _counts_row(s: ParagraphStyle, counts: Dict[str, int]) -> Table:
    items = [
        ("Ideal",      counts.get("ideal", 0),             "Ideal"),
        ("Acceptable", counts.get("acceptable", 0),        "Acceptable"),
        ("Adjust",     counts.get("adjustment_needed", 0), "Adjustment Needed"),
        ("Avoid",      counts.get("avoid", 0),             "Avoid"),
    ]
    cells = []
    styles_ = []
    for i, (label, n, k) in enumerate(items):
        cells.append([
            Paragraph(f"<b>{n}</b>", ParagraphStyle("c", parent=s["body"],
                       alignment=TA_CENTER, fontSize=18, leading=20,
                       textColor=VERDICT_FG.get(k, TEXT_DARK))),
            Paragraph(label, ParagraphStyle("cl", parent=s["small"],
                       alignment=TA_CENTER, textColor=VERDICT_FG.get(k, TEXT_MID))),
        ])
        styles_.append(("BACKGROUND", (i, 0), (i, 0), VERDICT_BG.get(k, BG_CARD)))
    # 4 stacked columns: each column is its own mini-table
    pills = []
    col_w = 40 * mm
    for i, c in enumerate(cells):
        t = Table([[c[0]], [c[1]]], colWidths=[col_w])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), VERDICT_BG.get(items[i][2], BG_CARD)),
            ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        pills.append(t)
    row = Table([pills], colWidths=[col_w] * 4)
    row.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    return row


def _section_card(title: str, body_en: str, body_hi: str,
                  s: ParagraphStyle, accent: colors.Color = BRAND_PURPLE) -> Table:
    rows = [[Paragraph(f"<b>{_safe(title)}</b>",
                       ParagraphStyle("ct", parent=s["h3"], textColor=accent))]]
    if body_en:
        rows.append([Paragraph(_safe(body_en), s["body"])])
    if body_hi:
        rows.append([Paragraph(_safe(body_hi), s["bodyHi"])])
    t = Table(rows, colWidths=[170 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
        ("LINEABOVE", (0, 0), (-1, 0), 2, accent),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _priority_table(actions: List[Dict[str, Any]], s: ParagraphStyle) -> Table:
    if not actions:
        return Paragraph("No priority actions — your premise is well-aligned.", s["body"])
    head = ["#", "Room · Direction", "Verdict", "Why (EN / Hi)"]
    data = [head]
    for i, p in enumerate(actions, 1):
        verdict = p.get("verdict", "Acceptable")
        crit = " ★" if p.get("is_critical") else ""
        room_dir = (p.get("room_type", "") or "").replace("_", " ").title() + crit + \
                   "\n" + (p.get("direction", "") or "")
        why = (p.get("why_en") or "") + "\n" + (p.get("why_hi") or "")
        data.append([
            str(i),
            Paragraph(_safe(room_dir).replace("\n", "<br/>"), s["body"]),
            Paragraph(_safe(verdict), ParagraphStyle("v", parent=s["body"],
                       textColor=VERDICT_FG.get(verdict, TEXT_DARK), fontSize=9)),
            Paragraph(_safe(why).replace("\n", "<br/>"), s["body"]),
        ])
    t = Table(data, colWidths=[10 * mm, 40 * mm, 30 * mm, 90 * mm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for r, p in enumerate(actions, 1):
        v = p.get("verdict", "Acceptable")
        bg = VERDICT_BG.get(v, BG_CARD)
        style.append(("BACKGROUND", (2, r), (2, r), bg))
    t.setStyle(TableStyle(style))
    return t


def _rooms_table(rooms: List[Dict[str, Any]], s: ParagraphStyle,
                 with_business: bool) -> Table:
    head = ["Room", "Dir", "Verdict", "Score", "Notes"]
    data = [head]
    for r in rooms:
        notes = []
        if r.get("zone", {}).get("deity"):
            z = r["zone"]
            notes.append(f"Zone: {z.get('planet','')} · {z.get('deity','')} · {z.get('element','')}")
        if with_business and r.get("business_rule", {}).get("applies"):
            br = r["business_rule"]
            if br.get("reason_en"):
                notes.append("Biz: " + br["reason_en"])
        if r.get("mahadasha", {}).get("applies"):
            md = r["mahadasha"]
            if md.get("reason_en"):
                notes.append("Mahadasha: " + md["reason_en"])
        notes_str = "<br/>".join(_safe(n) for n in notes) or "—"
        verdict = r.get("verdict", "Acceptable")
        crit = " ★" if r.get("is_critical") else ""
        data.append([
            Paragraph(_safe((r.get("room_type", "") or "").replace("_", " ").title() + crit), s["body"]),
            _safe(r.get("direction", "")),
            Paragraph(_safe(verdict), ParagraphStyle("v", parent=s["body"],
                       textColor=VERDICT_FG.get(verdict, TEXT_DARK), fontSize=9)),
            str(r.get("score", "—")),
            Paragraph(notes_str, s["body"]),
        ])
    t = Table(data, colWidths=[40 * mm, 14 * mm, 28 * mm, 14 * mm, 74 * mm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, r in enumerate(rooms, 1):
        bg = VERDICT_BG.get(r.get("verdict", "Acceptable"), colors.white)
        style.append(("BACKGROUND", (2, i), (2, i), bg))
    t.setStyle(TableStyle(style))
    return t


# ─────────────────────────────────────────────────────────────────────
# PUBLIC: Business Vastu PDF
# ─────────────────────────────────────────────────────────────────────
def render_business_pdf(report: Dict[str, Any], *,
                        property_name: str = "",
                        user_name: str = "") -> bytes:
    """Render a Business Vastu deep-scan report into a PDF byte string."""
    s = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=22 * mm, bottomMargin=18 * mm,
                            title="Business Vastu Report — Cosmic Lens",
                            author="Cosmic Lens")
    flow: List[Any] = []

    biz = report.get("business_summary", {}) or {}
    biz_type = (biz.get("type") or "Business").title()
    intro = biz.get("intro") or {}

    # ── Header
    flow.append(Paragraph(f"Business Vastu — {_safe(biz_type)}", s["title"]))
    sub = []
    if property_name:
        sub.append(f"Premise: <b>{_safe(property_name)}</b>")
    if user_name:
        sub.append(f"Owner: <b>{_safe(user_name)}</b>")
    sub.append(f"Issued: {datetime.utcnow().strftime('%d %b %Y')}")
    flow.append(Paragraph("  ·  ".join(sub), s["sub"]))

    # ── Score block
    overall = report.get("overall", {}) or {}
    summary = overall.get("summary", {}) or {}
    flow.append(_score_block(s,
                             int(overall.get("score", 0)),
                             overall.get("grade", "C"),
                             summary.get("en", ""),
                             summary.get("hi", ""),
                             "Overall Premise Score"))
    flow.append(Spacer(1, 8))

    # ── Counts row
    flow.append(_counts_row(s, overall.get("counts", {}) or {}))
    flow.append(Spacer(1, 10))

    # ── Business intro
    if intro.get("en") or intro.get("hi"):
        flow.append(_section_card(f"{biz_type} Vastu Brief",
                                  intro.get("en", ""),
                                  intro.get("hi", ""), s))
        flow.append(Spacer(1, 6))

    # ── Mahadasha alert
    md = report.get("mahadasha_alert")
    if md:
        title = f"Owner Mahadasha · {md.get('active_lord','-')} ({md.get('lord_direction','-')})"
        flow.append(_section_card(title,
                                  md.get("summary_en", ""),
                                  md.get("summary_hi", ""), s,
                                  accent=VERDICT_FG["Adjustment Needed"]))
        flow.append(Spacer(1, 6))

    # ── Stakeholder synergy
    stk = report.get("stakeholder")
    if stk and (stk.get("partner_count", 0) or 0) > 0:
        flow.append(_section_card("Stakeholder Synergy",
                                  stk.get("summary_en", ""),
                                  stk.get("summary_hi", ""), s,
                                  accent=VERDICT_FG["Acceptable"]))
        flow.append(Spacer(1, 6))

    # ── Muhurat alignment
    mh = report.get("muhurat") or {}
    if mh.get("applies"):
        flow.append(_section_card(f"Muhurat Alignment · {(mh.get('alignment') or '').upper()}",
                                  mh.get("summary_en", ""),
                                  mh.get("summary_hi", ""), s))
        flow.append(Spacer(1, 6))

    # ── Priority Actions
    flow.append(Paragraph("Priority Actions", s["h2"]))
    flow.append(_priority_table(report.get("priority_actions") or [], s))
    flow.append(Spacer(1, 10))

    # ── Room-by-room
    rooms = report.get("rooms") or []
    if rooms:
        flow.append(PageBreak())
        flow.append(Paragraph("Room-by-room Analysis", s["h2"]))
        flow.append(_rooms_table(rooms, s, with_business=True))
        flow.append(Spacer(1, 10))

    # ── Classical refs
    refs = report.get("classical_summary") or []
    if refs:
        flow.append(Paragraph("Classical References", s["h2"]))
        for r in refs:
            flow.append(Paragraph(f"• {_safe(r)}", s["body"]))
        flow.append(Spacer(1, 6))

    # ── Footer
    _ft = report.get("footer")
    if isinstance(_ft, dict):
        foot = _ft.get("en") or "Powered by Advanced Cosmic Intelligence"
    elif isinstance(_ft, str) and _ft.strip():
        foot = _ft
    else:
        foot = "Powered by Advanced Cosmic Intelligence"
    flow.append(Spacer(1, 14))
    flow.append(Paragraph(_safe(foot), s["footer"]))

    doc.build(flow, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────
# PUBLIC: AstroVastu PRO PDF (residential)
# ─────────────────────────────────────────────────────────────────────
def render_pro_pdf(report: Dict[str, Any], *,
                   property_name: str = "",
                   user_name: str = "") -> bytes:
    """Render an AstroVastu PRO (residential) report into a PDF byte string."""
    s = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=22 * mm, bottomMargin=18 * mm,
                            title="AstroVastu PRO Report — Cosmic Lens",
                            author="Cosmic Lens")
    flow: List[Any] = []

    flow.append(Paragraph("AstroVastu PRO Report", s["title"]))
    sub = []
    if property_name:
        sub.append(f"Property: <b>{_safe(property_name)}</b>")
    if user_name:
        sub.append(f"Owner: <b>{_safe(user_name)}</b>")
    sub.append(f"Issued: {datetime.utcnow().strftime('%d %b %Y')}")
    flow.append(Paragraph("  ·  ".join(sub), s["sub"]))

    overall = report.get("overall", {}) or {}
    summary = overall.get("summary", {}) or {}
    flow.append(_score_block(s,
                             int(overall.get("score", 0)),
                             overall.get("grade", "C"),
                             summary.get("en", ""),
                             summary.get("hi", ""),
                             "Overall Property Score"))
    flow.append(Spacer(1, 8))
    flow.append(_counts_row(s, overall.get("counts", {}) or {}))
    flow.append(Spacer(1, 10))

    ks = report.get("kundli_summary") or {}
    if ks:
        bits = []
        if ks.get("lagna"):     bits.append(f"Lagna: <b>{_safe(ks['lagna'])}</b>")
        if ks.get("mahadasha"): bits.append(f"Mahadasha: <b>{_safe(ks['mahadasha'])}</b>")
        if ks.get("sade_sati"): bits.append("Sade Sati: <b>active</b>")
        if bits:
            flow.append(_section_card("Owner Kundli Snapshot",
                                      "  ·  ".join(bits), "", s))
            flow.append(Spacer(1, 6))

    md = report.get("mahadasha_alert")
    if md:
        title = f"Active Mahadasha · {md.get('active_lord','-')} ({md.get('lord_direction','-')})"
        flow.append(_section_card(title,
                                  md.get("summary_en", ""),
                                  md.get("summary_hi", ""), s,
                                  accent=VERDICT_FG["Adjustment Needed"]))
        flow.append(Spacer(1, 6))

    flow.append(Paragraph("Priority Actions", s["h2"]))
    flow.append(_priority_table(report.get("priority_actions") or [], s))
    flow.append(Spacer(1, 10))

    rooms = report.get("rooms") or []
    if rooms:
        flow.append(PageBreak())
        flow.append(Paragraph("Room-by-room Analysis", s["h2"]))
        flow.append(_rooms_table(rooms, s, with_business=False))
        flow.append(Spacer(1, 10))

    refs = report.get("classical_summary") or []
    if refs:
        flow.append(Paragraph("Classical References", s["h2"]))
        for r in refs:
            flow.append(Paragraph(f"• {_safe(r)}", s["body"]))

    _ft = report.get("footer")
    if isinstance(_ft, dict):
        foot = _ft.get("en") or "Powered by Advanced Cosmic Intelligence"
    elif isinstance(_ft, str) and _ft.strip():
        foot = _ft
    else:
        foot = "Powered by Advanced Cosmic Intelligence"
    flow.append(Spacer(1, 14))
    flow.append(Paragraph(_safe(foot), s["footer"]))

    doc.build(flow, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

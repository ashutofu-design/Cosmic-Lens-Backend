"""
PDF Report Renderer — ₹1499 Face Intelligence Report

Renders the ordered report (from narrator.assemble_report) to a polished
PDF using ReportLab. Emoji-safe (stripped to ASCII tags), Hinglish-tuned
typography, color-coded section headers, and a professional cover page.
"""
from __future__ import annotations
from io import BytesIO
from typing import Dict, List, Any
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, Image, HRFlowable,
)


# ── Color palette (premium maroon + cream) ────────────────────────────────
C_PRIMARY     = HexColor("#7B1F1F")    # deep maroon
C_ACCENT      = HexColor("#C2A878")    # warm gold
C_INK         = HexColor("#2A2418")    # dark warm brown
C_MUTED       = HexColor("#7A7164")    # muted brown
C_BG_TINT     = HexColor("#FAF6EC")    # cream background
C_RULE        = HexColor("#D9CFB7")    # rule line


# ── Emoji stripper (ReportLab core fonts can't render emoji) ──────────────
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F000-\U0001F2FF"
    "]+",
    flags=re.UNICODE,
)


def _safe(text: Any) -> str:
    """Strip emojis + escape XML entities for ReportLab paragraphs."""
    if text is None:
        return ""
    s = str(text)
    s = _EMOJI_RE.sub("", s).strip()
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s


# ── Styles ────────────────────────────────────────────────────────────────
def _styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=34, textColor=C_PRIMARY, alignment=TA_CENTER, leading=40,
            spaceAfter=8,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle", parent=base["Normal"], fontName="Helvetica-Oblique",
            fontSize=14, textColor=C_MUTED, alignment=TA_CENTER, leading=20,
            spaceAfter=18,
        ),
        "cover_name": ParagraphStyle(
            "cover_name", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=22, textColor=C_INK, alignment=TA_CENTER, leading=26,
            spaceBefore=20, spaceAfter=4,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", parent=base["Normal"], fontName="Helvetica",
            fontSize=11, textColor=C_MUTED, alignment=TA_CENTER, leading=16,
        ),
        "cover_archetype": ParagraphStyle(
            "cover_arche", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=18, textColor=C_PRIMARY, alignment=TA_CENTER, leading=22,
            spaceBefore=24,
        ),
        "section_no": ParagraphStyle(
            "section_no", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=11, textColor=C_ACCENT, alignment=TA_LEFT, leading=14,
            spaceAfter=2,
        ),
        "section_title_hi": ParagraphStyle(
            "section_title_hi", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=18, textColor=C_PRIMARY, alignment=TA_LEFT, leading=22,
            spaceAfter=2,
        ),
        "section_title_en": ParagraphStyle(
            "section_title_en", parent=base["Normal"], fontName="Helvetica-Oblique",
            fontSize=10, textColor=C_MUTED, alignment=TA_LEFT, leading=14,
            spaceAfter=10,
        ),
        "field_label": ParagraphStyle(
            "field_label", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=10.5, textColor=C_PRIMARY, alignment=TA_LEFT, leading=14,
            spaceBefore=8, spaceAfter=2,
        ),
        "field_value": ParagraphStyle(
            "field_value", parent=base["Normal"], fontName="Helvetica",
            fontSize=11, textColor=C_INK, alignment=TA_JUSTIFY, leading=16,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["Normal"], fontName="Helvetica",
            fontSize=10.5, textColor=C_INK, alignment=TA_LEFT, leading=15,
            leftIndent=14, bulletIndent=4, spaceAfter=4,
        ),
        "footer": ParagraphStyle(
            "footer", parent=base["Normal"], fontName="Helvetica-Oblique",
            fontSize=8, textColor=C_MUTED, alignment=TA_CENTER, leading=11,
        ),
    }


# ── Page decoration: header bar + page numbers ────────────────────────────
def _on_page(canvas, doc):
    canvas.saveState()
    page_w, page_h = A4

    # Top thin gold bar
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, page_h - 6, page_w, 6, fill=1, stroke=0)

    # Bottom rule + page number + brand
    canvas.setStrokeColor(C_RULE)
    canvas.setLineWidth(0.4)
    canvas.line(15 * mm, 16 * mm, page_w - 15 * mm, 16 * mm)

    canvas.setFont("Helvetica-Oblique", 8)
    canvas.setFillColor(C_MUTED)
    canvas.drawString(15 * mm, 10 * mm, "Cosmic Lens · Face Intelligence Report")
    canvas.drawRightString(page_w - 15 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _on_cover_page(canvas, doc):
    canvas.saveState()
    page_w, page_h = A4

    # Full background tint
    canvas.setFillColor(C_BG_TINT)
    canvas.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # Top gold bar (thicker on cover)
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, page_h - 18, page_w, 18, fill=1, stroke=0)

    # Bottom maroon strip
    canvas.setFillColor(C_PRIMARY)
    canvas.rect(0, 0, page_w, 30, fill=1, stroke=0)

    # Cover footer text
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(white)
    canvas.drawCentredString(page_w / 2, 11, "Cosmic Lens · Vedic Face Intelligence")

    canvas.restoreState()


# ── Section renderers ─────────────────────────────────────────────────────
def _render_field(label: str, value: Any, styles) -> List:
    """Generic key/value renderer."""
    flowables = []
    if isinstance(value, list):
        flowables.append(Paragraph(_safe(label), styles["field_label"]))
        for item in value:
            if isinstance(item, dict):
                # Render each dict-item as inline labelled text
                parts = [f"<b>{_safe(k.replace('_',' ').title())}:</b> {_safe(v)}" for k, v in item.items()]
                flowables.append(Paragraph(" · ".join(parts), styles["bullet"], bulletText="•"))
            else:
                flowables.append(Paragraph(_safe(item), styles["bullet"], bulletText="•"))
    elif isinstance(value, dict):
        flowables.append(Paragraph(_safe(label), styles["field_label"]))
        for k, v in value.items():
            sub_label = k.replace("_", " ").title()
            if isinstance(v, (dict, list)):
                flowables.append(Paragraph(f"<b>{_safe(sub_label)}:</b>", styles["field_value"]))
                flowables.extend(_render_field("", v, styles))
            else:
                flowables.append(
                    Paragraph(f"<b>{_safe(sub_label)}:</b> {_safe(v)}", styles["field_value"])
                )
    else:
        if label:
            flowables.append(Paragraph(_safe(label), styles["field_label"]))
        flowables.append(Paragraph(_safe(value), styles["field_value"]))
    return flowables


def _render_section(sec: Dict, styles) -> List:
    """Render one of the 22 sections."""
    flowables: List = []
    flowables.append(Paragraph(f"SECTION {sec['no']}", styles["section_no"]))
    flowables.append(Paragraph(_safe(sec["title_hi"]), styles["section_title_hi"]))
    flowables.append(Paragraph(_safe(sec["title_en"]), styles["section_title_en"]))
    flowables.append(HRFlowable(width="40%", thickness=1.5, color=C_ACCENT,
                                spaceBefore=2, spaceAfter=10, hAlign="LEFT"))

    content = sec["content"] or {}
    if isinstance(content, dict):
        for k, v in content.items():
            if v is None or v == "" or v == [] or v == {}:
                continue
            label_pretty = k.replace("_hi", "").replace("_en", "").replace("_", " ").strip().title()
            flowables.extend(_render_field(label_pretty, v, styles))
    else:
        flowables.append(Paragraph(_safe(content), styles["field_value"]))

    flowables.append(Spacer(1, 6 * mm))
    return flowables


def _render_cover(cover: Dict, styles) -> List:
    """Cover page — title, subtitle, name, archetype, meta."""
    flowables = []
    flowables.append(Spacer(1, 35 * mm))
    flowables.append(Paragraph(_safe(cover.get("report_title", "Face Intelligence Report")),
                               styles["cover_title"]))
    flowables.append(Paragraph(_safe(cover.get("report_subtitle", "")),
                               styles["cover_subtitle"]))

    flowables.append(HRFlowable(width="50%", thickness=2, color=C_ACCENT,
                                spaceBefore=12, spaceAfter=20, hAlign="CENTER"))

    flowables.append(Paragraph(_safe(cover.get("name", "Insan")), styles["cover_name"]))

    meta_lines = []
    if cover.get("age"):           meta_lines.append(f"Aayu: {cover['age']} saal")
    if cover.get("gender") and cover["gender"] != "U":
        meta_lines.append(f"Linga: {'Pursh' if cover['gender']=='M' else 'Stree'}")
    if cover.get("perceived_age"): meta_lines.append(f"Pratyaksh Aayu: ~{cover['perceived_age']} saal")
    if meta_lines:
        flowables.append(Paragraph(" · ".join(_safe(m) for m in meta_lines), styles["cover_meta"]))

    flowables.append(Spacer(1, 12 * mm))

    flowables.append(Paragraph(f"Tumhara Archetype:", styles["cover_meta"]))
    flowables.append(Paragraph(_safe(cover.get("archetype", "Balanced Soul")),
                               styles["cover_archetype"]))

    flowables.append(Spacer(1, 8 * mm))

    flowables.append(Paragraph(
        f"Mukh Aakar: <b>{_safe(cover.get('face_shape','-')).title()}</b> · "
        f"Tatva: <b>{_safe(cover.get('dominant_element','-'))}</b>" +
        (f" · Varna: <b>{_safe(cover['complexion'])}</b>" if cover.get("complexion") else ""),
        styles["cover_meta"]))

    flowables.append(Spacer(1, 30 * mm))
    flowables.append(HRFlowable(width="30%", thickness=0.6, color=C_RULE,
                                spaceBefore=4, spaceAfter=8, hAlign="CENTER"))
    flowables.append(Paragraph(
        "Yeh report tumhare chehre se nikla hua 100% personalized truth hai.<br/>"
        "21 sections · 9 engines · Vedic Samudrika + Modern Psychology",
        styles["cover_meta"]))

    return flowables


# ── Main entrypoint ───────────────────────────────────────────────────────
def render_pdf(report: Dict) -> bytes:
    """Render the assembled report dict (from narrator.assemble_report) → PDF bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
        title=report.get("cover", {}).get("report_title", "Face Intelligence Report"),
        author="Cosmic Lens",
    )
    styles = _styles()

    story: List = []

    # Cover page
    story.extend(_render_cover(report.get("cover", {}), styles))
    story.append(PageBreak())

    # 22 sections (21 + bonus)
    for sec in report.get("sections", []):
        story.extend(_render_section(sec, styles))

    # Footer disclaimer page
    story.append(PageBreak())
    story.append(Spacer(1, 80 * mm))
    story.append(HRFlowable(width="60%", thickness=1, color=C_ACCENT,
                            spaceBefore=4, spaceAfter=14, hAlign="CENTER"))
    story.append(Paragraph("Disclaimer", styles["section_title_hi"]))
    story.append(Paragraph(_safe(report.get("footer_disclaimer", "")), styles["field_value"]))

    # Build with first-page (cover) decoration vs rest
    doc.build(story, onFirstPage=_on_cover_page, onLaterPages=_on_page)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes

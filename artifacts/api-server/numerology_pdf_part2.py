"""
numerology_pdf_part2.py — Part 2 ("Practical Numerology Tools") PDF.

A separate ₹149 add-on report covering:
  - Mobile Number Analysis
  - Vehicle Number Analysis (optional)
  - House Number Analysis (optional)
  - Name Numerology (Pythagorean + Chaldean side-by-side)
  - Name Correction Suggestions (top 3 with harmony scores)

Pure deterministic engine output rendered to A4 PDF — zero AI.
"""
from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from vedic.numerology import tier_a as _ta

BRAND_PURPLE = colors.HexColor("#5B21B6")
BRAND_GOLD = colors.HexColor("#D97706")
TEXT_DARK = colors.HexColor("#1F2937")
TEXT_MID = colors.HexColor("#4B5563")
TEXT_SOFT = colors.HexColor("#6B7280")


def _styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold",
                             fontSize=22, leading=28, textColor=BRAND_PURPLE,
                             alignment=TA_CENTER, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold",
                             fontSize=15, leading=18, textColor=BRAND_PURPLE,
                             spaceBefore=10, spaceAfter=6),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName="Helvetica-Bold",
                             fontSize=11, leading=14, textColor=TEXT_DARK,
                             spaceBefore=6, spaceAfter=2),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica",
                               fontSize=10, leading=14, textColor=TEXT_DARK),
        "body_mid": ParagraphStyle("body_mid", parent=base["BodyText"], fontName="Helvetica",
                                   fontSize=9.5, leading=13, textColor=TEXT_MID),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName="Helvetica",
                                fontSize=8, leading=10, textColor=TEXT_SOFT),
        "cover_name": ParagraphStyle("cover_name", parent=base["Heading1"],
                                     fontName="Helvetica-Bold", fontSize=28, leading=34,
                                     textColor=TEXT_DARK, alignment=TA_CENTER,
                                     spaceBefore=8, spaceAfter=8),
        "cover_sub": ParagraphStyle("cover_sub", parent=base["BodyText"],
                                    fontName="Helvetica", fontSize=12, leading=16,
                                    textColor=TEXT_MID, alignment=TA_CENTER),
        "tagline": ParagraphStyle("tagline", parent=base["BodyText"],
                                  fontName="Helvetica-Oblique", fontSize=11, leading=14,
                                  textColor=BRAND_GOLD, alignment=TA_CENTER,
                                  spaceAfter=6),
        "page_title": ParagraphStyle("page_title", parent=base["Heading1"],
                                     fontName="Helvetica-Bold", fontSize=18, leading=22,
                                     textColor=BRAND_PURPLE, spaceAfter=6),
    }


def _on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BRAND_GOLD)
    canvas.setLineWidth(0.5)
    canvas.line(15 * mm, 12 * mm, 195 * mm, 12 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TEXT_SOFT)
    canvas.drawString(15 * mm, 8 * mm, "Cosmic Lens — Practical Numerology Tools")
    canvas.drawRightString(195 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _section_title(s, text: str):
    return Paragraph(text, s["page_title"])


def _verdict_color(verdict: str):
    v = (verdict or "").upper()
    if v in ("EXCELLENT", "FAVOURABLE", "GOOD", "EXCELLENT MATCH", "GOOD MATCH"):
        return colors.HexColor("#D4EDDA")
    if v in ("AVOID", "POOR", "CHALLENGING"):
        return colors.HexColor("#F8D7DA")
    if v in ("MIXED", "OK"):
        return colors.HexColor("#FFF3CD")
    return colors.HexColor("#E5E7EB")


def _verdict_box(s, title: str, body: str, verdict: str) -> Table:
    bg = _verdict_color(verdict)
    inner = [
        [Paragraph(f"<b>{title}</b>", ParagraphStyle(
            "vbt", fontName="Helvetica-Bold", fontSize=10.5,
            textColor=TEXT_DARK, leading=14))],
        [Paragraph(body, ParagraphStyle(
            "vbb", fontName="Helvetica", fontSize=9.5,
            textColor=TEXT_DARK, leading=13))],
    ]
    t = Table(inner, colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0, bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, -1), (-1, -1), 0),
    ]))
    return t


# ─── Cover ───────────────────────────────────────────────────────────

def _cover(s, name: str, dob: str) -> List[Any]:
    flow: List[Any] = []
    flow.append(Spacer(1, 30 * mm))
    flow.append(Paragraph("PRACTICAL NUMEROLOGY TOOLS", s["tagline"]))
    flow.append(Spacer(1, 8 * mm))
    flow.append(Paragraph(name, s["cover_name"]))
    flow.append(Paragraph(f"Janma-tithi: {dob}", s["cover_sub"]))
    flow.append(Spacer(1, 18 * mm))

    box_inner = [
        [Paragraph("<b>Is Report Me Aapko Milega:</b>", ParagraphStyle(
            "ct", fontName="Helvetica-Bold", fontSize=12, textColor=TEXT_DARK,
            alignment=TA_CENTER, leading=16))],
        [Paragraph(
            "✓ Mobile Number Analysis (Driver/Conductor verdict)<br/>"
            "✓ Vehicle &amp; House Number check (optional)<br/>"
            "✓ Name Numerology (Pythagorean + Chaldean dono)<br/>"
            "✓ Name Correction — top 3 spelling variants with harmony score<br/>"
            "✓ Practical action steps — what to keep, what to change",
            ParagraphStyle("cb", fontName="Helvetica", fontSize=10.5,
                           textColor=TEXT_MID, alignment=TA_CENTER, leading=16))],
    ]
    bt = Table(box_inner, colWidths=[170 * mm])
    bt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF8E1")),
        ("BOX", (0, 0), (-1, -1), 1, BRAND_GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
    ]))
    flow.append(bt)
    flow.append(Spacer(1, 25 * mm))
    flow.append(Paragraph("Powered by Advanced Cosmic Intelligence",
                          ParagraphStyle("brand", fontName="Helvetica-Oblique",
                                         fontSize=10, textColor=BRAND_PURPLE,
                                         alignment=TA_CENTER)))
    return flow


# ─── Number analysis sections ────────────────────────────────────────

def _number_analysis_block(s, value: str, kind: str,
                           driver: int, conductor: int) -> List[Any]:
    """Render a single number-analysis section."""
    flow: List[Any] = []
    out = _ta.analyze_number_string(value, kind=kind, driver=driver, conductor=conductor)
    if not out.get("ok"):
        return flow

    titles = {
        "mobile":  "Mobile Number Analysis",
        "vehicle": "Vehicle Number Analysis",
        "house":   "House Number Analysis",
    }
    flow.append(Paragraph(titles.get(kind, "Number Analysis"), s["h2"]))

    rows = [
        ["Number entered:", str(out.get("input"))],
        ["Calculation:",    out.get("calculation_chain", "—")],
        ["Reduced to:",     f"{out.get('reduced')} ({out.get('planet') or '—'})"],
        ["Energy:",         out.get("energy", "—")],
        ["Your Driver:",    str(driver)],
        ["Your Conductor:", str(conductor)],
    ]
    t = Table(rows, colWidths=[40 * mm, 140 * mm])
    t.setStyle(TableStyle([
        ("FONTSIZE",    (0, 0), (-1, -1), 9.5),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR",   (0, 0), (0, -1), TEXT_MID),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW",   (0, 0), (-1, -2), 0.3, colors.HexColor("#EEE")),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 4 * mm))

    body = out.get("verdict_reason", "")
    extra = out.get("conductor_note", "")
    if extra:
        body += f"<br/><br/>{extra}"
    flow.append(_verdict_box(
        s,
        f"Verdict: {out.get('verdict')}",
        body,
        out.get("verdict", ""),
    ))
    flow.append(Spacer(1, 3 * mm))

    tip = out.get("tip", "")
    if tip:
        flow.append(Paragraph(f"<b>Practical tip:</b> {tip}", s["body"]))
    flow.append(Spacer(1, 6 * mm))
    return flow


# ─── Name numerology section (Pythagorean + Chaldean) ────────────────

def _name_numerology_section(s, name: str) -> List[Any]:
    """Side-by-side Pythagorean vs Chaldean name analysis."""
    from vedic.numerology.extended import _PYTH, _VOWELS

    flow: List[Any] = []
    flow.append(_section_title(s, "Name Numerology — Dual Alphabet Analysis"))
    flow.append(Paragraph(
        f"Aapka naam: <b>{name}</b><br/>"
        "Pythagorean (modern, spiritual) aur Chaldean (ancient, professional) "
        "dono systems se compute kiya gaya hai.",
        s["body_mid"]))
    flow.append(Spacer(1, 5 * mm))

    letters = "".join(c for c in name.lower() if c.isalpha())
    py_total = sum(_PYTH.get(c, 0) for c in letters)
    py_vow = sum(_PYTH.get(c, 0) for c in letters if c in _VOWELS)
    py_con = sum(_PYTH.get(c, 0) for c in letters if c not in _VOWELS)

    def _r(n: int) -> int:
        n = abs(int(n))
        while n > 9 and n not in (11, 22, 33):
            n = sum(int(d) for d in str(n))
        return n

    cha = _ta.chaldean_name_numbers(name)
    if not cha.get("ok"):
        flow.append(Paragraph("Name analysis unavailable.", s["body"]))
        return flow

    rows = [
        ["", "Pythagorean", "Chaldean"],
        ["Expression (full name)",
         f"{py_total} → {_r(py_total)}",
         f"{cha['expression']['raw']} → {cha['expression']['reduced']}"],
        ["Soul Urge (vowels only)",
         f"{py_vow} → {_r(py_vow)}",
         f"{cha['soul_urge']['raw']} → {cha['soul_urge']['reduced']}"],
        ["Personality (consonants)",
         f"{py_con} → {_r(py_con)}",
         f"{cha['personality']['raw']} → {cha['personality']['reduced']}"],
    ]
    t = Table(rows, colWidths=[60 * mm, 60 * mm, 60 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",   (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 10),
        ("ALIGN",      (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#DDD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F4FF")]),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 5 * mm))

    flow.append(Paragraph("<b>Kab kaunsa use kare?</b>", s["h3"]))
    flow.append(Paragraph(
        "• <b>Pythagorean</b> — spiritual/personal analysis, daily life decisions.<br/>"
        "• <b>Chaldean</b> — business, branding, signature, public name. "
        "Ismein 9 sacred manaa jaata hai isliye absent hai.",
        s["body"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_verdict_box(
        s, "Strict Chaldean Note",
        cha.get("note", ""), "NEUTRAL"))
    return flow


# ─── Name correction section ─────────────────────────────────────────

def _name_correction_section(s, name: str, driver: int, conductor: int) -> List[Any]:
    """Top spelling variants with harmony scores."""
    flow: List[Any] = []
    flow.append(_section_title(s, "Name Correction — Spelling Variants"))
    flow.append(Paragraph(
        "Naam ki spelling thoda badalne se vibration shift hota hai. "
        "Ye variants aapke Driver aur Conductor numbers ke saath harmony "
        "ke aadhar par scored hain (0-100).",
        s["body_mid"]))
    flow.append(Spacer(1, 4 * mm))

    out = _ta.name_correction_suggestions(name, driver, conductor, limit=8)
    if not out.get("ok"):
        flow.append(Paragraph("Name correction unavailable.", s["body"]))
        return flow

    orig = out.get("original") or {}
    flow.append(_verdict_box(
        s,
        f"Current Name: {orig.get('name')} — Score {orig.get('harmony_score')}/100 ({orig.get('verdict')})",
        f"Name number: <b>{orig.get('name_number')}</b> — Driver {driver}, Conductor {conductor} ke saath compatibility.",
        orig.get("verdict", ""),
    ))
    flow.append(Spacer(1, 5 * mm))

    flow.append(Paragraph("<b>Top Suggested Variants:</b>", s["h3"]))
    rows = [["Variant", "Name #", "Score", "Verdict", "Δ vs original"]]
    for sug in (out.get("suggestions") or [])[:8]:
        delta = sug.get("delta", 0)
        delta_str = f"+{delta}" if delta > 0 else (str(delta) if delta < 0 else "—")
        rows.append([
            sug.get("name", ""),
            str(sug.get("name_number", "")),
            f"{sug.get('harmony_score', 0)}/100",
            sug.get("verdict", ""),
            delta_str,
        ])
    t = Table(rows, colWidths=[55 * mm, 25 * mm, 30 * mm, 35 * mm, 35 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9.5),
        ("ALIGN",      (1, 0), (-1, -1), "CENTER"),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#DDD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F4FF")]),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 5 * mm))

    best = out.get("best_improvements") or []
    if best:
        body_lines = ["<b>Sabse strong improvement options:</b><br/>"]
        for b in best:
            body_lines.append(
                f"• <b>{b['name']}</b> — score {b['harmony_score']}/100 "
                f"(+{b['delta_vs_original']} improvement)"
            )
        flow.append(_verdict_box(
            s, "Recommended Action",
            "<br/>".join(body_lines) + "<br/><br/>" + (out.get("note") or ""),
            "EXCELLENT",
        ))
    else:
        flow.append(_verdict_box(
            s, "No correction needed",
            out.get("note", ""), "GOOD",
        ))
    return flow


def _disclaimer(s) -> List[Any]:
    return [
        Spacer(1, 8 * mm),
        Paragraph(
            "<i>This report is for guidance and self-reflection. Numerology is a "
            "supportive tool — final decisions on legal name change, mobile-number "
            "purchase, or property should also consider practical, legal and family "
            "factors. Please consult a qualified astrologer for personalised remedies. "
            "Not legal, medical or financial advice.</i>",
            s["small"]),
    ]


# ─── Public entry ────────────────────────────────────────────────────

def render_part2_pdf(*,
                     name: str,
                     dob: str,
                     mobile: Optional[str],
                     vehicle: Optional[str],
                     house: Optional[str]) -> bytes:
    """Render the Practical Numerology Tools (Part 2) PDF."""
    # Compute Driver + Conductor from dob
    digits = [int(c) for c in dob if c.isdigit()]
    parts = dob.split("-")
    try:
        day = int(parts[2])
    except (IndexError, ValueError):
        day = 0

    def _r(n):
        n = abs(int(n))
        while n > 9:
            n = sum(int(d) for d in str(n))
        return n

    driver = _r(day) if day else 0
    conductor = _r(sum(digits)) if digits else 0

    s = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=18 * mm, bottomMargin=20 * mm,
                            title=f"Practical Numerology — {name}",
                            author="Cosmic Lens")
    story: List[Any] = []
    story += _cover(s, name, dob)
    story.append(PageBreak())

    # Number analysis page (mobile/vehicle/house)
    if mobile or vehicle or house:
        story.append(_section_title(s, "Your Numbers — Vibrational Analysis"))
        story.append(Paragraph(
            f"Aapka Driver Number: <b>{driver}</b> &nbsp;&nbsp; "
            f"Aapka Conductor Number: <b>{conductor}</b><br/>"
            "Niche diye gaye numbers in dono ke saath compare kiye gaye hain.",
            s["body_mid"]))
        story.append(Spacer(1, 4 * mm))
        if mobile:
            story += _number_analysis_block(s, mobile, "mobile", driver, conductor)
        if vehicle:
            story += _number_analysis_block(s, vehicle, "vehicle", driver, conductor)
        if house:
            story += _number_analysis_block(s, house, "house", driver, conductor)
        story.append(PageBreak())

    # Name numerology
    story += _name_numerology_section(s, name)
    story.append(PageBreak())

    # Name correction
    story += _name_correction_section(s, name, driver, conductor)
    story += _disclaimer(s)

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

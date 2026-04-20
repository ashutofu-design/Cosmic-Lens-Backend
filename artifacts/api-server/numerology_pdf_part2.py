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
    """Render a deep number-analysis section: digit-by-digit, last-4, alerts, alternatives."""
    flow: List[Any] = []
    out = _ta.analyze_number_string(value, kind=kind, driver=driver, conductor=conductor)
    if not out.get("ok"):
        return flow

    titles = {
        "mobile":  "Mobile Number — Deep Analysis",
        "vehicle": "Vehicle Number — Deep Analysis",
        "house":   "House Number — Deep Analysis",
    }
    flow.append(Paragraph(titles.get(kind, "Number Analysis"), s["h2"]))

    # ─ Summary table
    rows = [
        ["Number entered:", str(out.get("input"))],
        ["Calculation:",    out.get("calculation_chain", "—")],
        ["Reduced to:",     f"{out.get('reduced')} ({out.get('planet') or '—'})"],
        ["Energy:",         out.get("energy", "—")],
        ["Your Driver:",    f"{driver} ({_planet_for(driver)})"],
        ["Your Conductor:", f"{conductor} ({_planet_for(conductor)})"],
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
        f"Overall Verdict: {out.get('verdict')}",
        body,
        out.get("verdict", ""),
    ))
    flow.append(Spacer(1, 4 * mm))

    # ─ Digit-by-digit breakdown
    db = _ta.digit_breakdown(value)
    if db:
        flow.append(Paragraph("<b>Digit-by-Digit Vibration:</b>", s["h3"]))
        d_rows = [["Digit", "Planet", "Energy / Meaning"]]
        for d in db:
            d_rows.append([str(d["digit"]), d["planet"], d["meaning"]])
        dt = Table(d_rows, colWidths=[18 * mm, 30 * mm, 132 * mm])
        dt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_PURPLE),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ("ALIGN",      (0, 0), (1, -1), "CENTER"),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F4FF")]),
            ("LEFTPADDING",  (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ]))
        flow.append(dt)
        flow.append(Spacer(1, 3 * mm))

    # ─ Last-4 (Cheiro rule, mobile only)
    if kind == "mobile":
        l4 = _ta.last_four_analysis(value)
        if l4.get("ok"):
            flow.append(_verdict_box(
                s, f"Cheiro's Last-4 Rule — {l4.get('last4')}",
                f"Last 4 digits sum = {l4.get('sum')} → reduces to <b>{l4.get('reduced')}</b>. "
                f"{l4.get('note')}",
                "NEUTRAL",
            ))
            flow.append(Spacer(1, 3 * mm))

    # ─ Pattern alerts
    alerts = _ta.repeating_digit_alerts(value)
    if alerts:
        flow.append(Paragraph("<b>Pattern Alerts:</b>", s["h3"]))
        for a in alerts:
            flow.append(Paragraph(a, s["body"]))
        flow.append(Spacer(1, 3 * mm))

    # ─ Practical tip
    tip = out.get("tip", "")
    if tip:
        flow.append(Paragraph(f"<b>Practical Tip:</b> {tip}", s["body"]))
    flow.append(Spacer(1, 4 * mm))

    # ─ Lucky alternatives (mobile/vehicle: where user can swap)
    if kind in ("mobile", "vehicle") and out.get("verdict") in ("AVOID", "NEUTRAL"):
        alts = _ta.lucky_number_alternatives(driver, conductor, base_value=value, count=6)
        if alts:
            flow.append(Paragraph(
                f"<b>Suggested Alternatives</b> — last 1-2 digits change karke ye numbers "
                "aapke liye favourable ban jaayenge:", s["h3"]))
            a_rows = [["Suggested Number", "Sum", "Reduces to", "Matches", "Verdict"]]
            for a in alts:
                a_rows.append([a["number"], str(a["sum"]), str(a["reduced"]),
                               a["matches"], a["verdict"]])
            at = Table(a_rows, colWidths=[55 * mm, 20 * mm, 30 * mm, 40 * mm, 35 * mm])
            at.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_GOLD),
                ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
                ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",   (0, 0), (-1, -1), 9),
                ("ALIGN",      (1, 0), (-1, -1), "CENTER"),
                ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FFFBEB")]),
                ("LEFTPADDING",  (0, 0), (-1, -1), 5),
                ("TOPPADDING",   (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ]))
            flow.append(at)

    flow.append(Spacer(1, 5 * mm))
    return flow


def _planet_for(n: int) -> str:
    PLANETS = {1:"Sun", 2:"Moon", 3:"Jupiter", 4:"Rahu", 5:"Mercury",
               6:"Venus", 7:"Ketu", 8:"Saturn", 9:"Mars"}
    return PLANETS.get(n, "—")


def _driver_conductor_intro(s, name: str, dob: str, driver: int, conductor: int) -> List[Any]:
    """Page 2 — explain user's Driver + Conductor with planets."""
    flow: List[Any] = []
    flow.append(_section_title(s, "Your Number Signature"))
    flow.append(Paragraph(
        f"Har person ke 2 sabse important numbers hote hain — Driver aur Conductor. "
        f"Ye {dob} ki janma-tithi se nikle hain aur aapki har choice — mobile, vehicle, "
        "ghar, naam — inhi ke hisaab se evaluate ki jaani chahiye.",
        s["body"]))
    flow.append(Spacer(1, 6 * mm))

    rows = [
        ["", "Driver (Mulank)", "Conductor (Bhagyank)"],
        ["Number", str(driver), str(conductor)],
        ["Planet", _planet_for(driver), _planet_for(conductor)],
        ["Source", "Birth date (day only)", "Full DOB total reduced"],
        ["Influence", "Daily personality, instant reactions",
         "Long-term fortune, destiny flow"],
        ["Use for", "Quick decisions, daily choices",
         "Investments, career path, marriage"],
    ]
    t = Table(rows, colWidths=[35 * mm, 70 * mm, 75 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",   (0, 1), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR",  (0, 1), (0, -1), TEXT_MID),
        ("BACKGROUND", (1, 1), (-1, 1), colors.HexColor("#FFF4E6")),
        ("FONTNAME",   (1, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",   (1, 1), (-1, 1), 18),
        ("FONTSIZE",   (0, 0), (-1, -1), 10),
        ("ALIGN",      (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#DDD")),
        ("ROWBACKGROUNDS", (0, 2), (-1, -1), [colors.white, colors.HexColor("#F8F4FF")]),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 5 * mm))
    flow.append(_verdict_box(
        s, "How to Read This Report",
        "1. Har number ka analysis aapke Driver aur Conductor ke saath compare karke kiya gaya hai.<br/>"
        "2. Verdict colours: <b>Hara</b> = favourable, <b>Peela</b> = neutral, <b>Laal</b> = avoid.<br/>"
        "3. End me 30-day implementation plan aur signature recommendations.",
        "NEUTRAL",
    ))
    return flow


def _compatibility_matrix_section(s, driver: int) -> List[Any]:
    """Show user's driver vs all 1-9 compatibility."""
    flow: List[Any] = []
    flow.append(_section_title(s, "Number Compatibility Matrix"))
    flow.append(Paragraph(
        f"Aapka Driver Number <b>{driver}</b> ({_planet_for(driver)}) baaki sab numbers "
        "(1-9) ke saath kaisa interact karta hai. Ye knowledge use kare — "
        "partner select karte waqt, business associate chunte waqt, ghar/mobile/vehicle ka "
        "number lete waqt.",
        s["body_mid"]))
    flow.append(Spacer(1, 5 * mm))

    matrix = _ta.compatibility_matrix(driver)
    rows = [["Number", "Planet", "Type", "Score", "Practical Advice"]]
    for m in matrix:
        rows.append([
            str(m["number"]), m["planet"], m["label"],
            f"{m['score']}/100", m["advice"],
        ])
    t = Table(rows, colWidths=[20 * mm, 25 * mm, 25 * mm, 22 * mm, 88 * mm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ALIGN",      (0, 0), (3, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]
    # Color rows by type
    for i, m in enumerate(matrix, start=1):
        bg = _verdict_color({"FRIEND": "GOOD", "TWIN": "EXCELLENT",
                             "ENEMY": "AVOID", "NEUTRAL": "MIXED"}[m["label"]])
        style.append(("BACKGROUND", (0, i), (-1, i), bg))
    t.setStyle(TableStyle(style))
    flow.append(t)
    return flow


def _letter_table_section(s, name: str) -> List[Any]:
    """Page showing per-letter numerology values."""
    flow: List[Any] = []
    flow.append(_section_title(s, "Name — Letter by Letter"))
    flow.append(Paragraph(
        f"<b>{name}</b> — har akshar ki Pythagorean aur Chaldean value. "
        "Vowels (A/E/I/O/U) Soul Urge banate hain (aapki inner desire), "
        "consonants Personality (duniya jo dekhti hai).",
        s["body_mid"]))
    flow.append(Spacer(1, 4 * mm))

    rows = [["Letter", "Type", "Pythagorean", "Chaldean"]]
    for r in _ta.letter_by_letter(name):
        if r["letter"] == " ":
            continue
        rows.append([
            r["letter"],
            "Vowel" if r["vowel"] else "Consonant",
            str(r["pythagorean"]),
            str(r["chaldean"]) if r["chaldean"] else "— (no 9 in Chaldean)",
        ])
    t = Table(rows, colWidths=[25 * mm, 35 * mm, 50 * mm, 70 * mm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",   (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 10),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]
    # Highlight vowel rows
    for i, r in enumerate(rows[1:], start=1):
        if r[1] == "Vowel":
            style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FFF4E6")))
    t.setStyle(TableStyle(style))
    flow.append(t)
    flow.append(Spacer(1, 4 * mm))
    flow.append(Paragraph(
        "<i>Pythagorean (A=1..I=9, J=1..R=9, S=1..Z=8) — modern, used worldwide.<br/>"
        "Chaldean (sound-based, 1-8 only, 9 sacred and absent) — ancient, used by "
        "Cheiro for predictions.</i>",
        s["small"]))
    return flow


def _signature_section(s, name: str, driver: int) -> List[Any]:
    """Initial-letter analysis + signature recommendations."""
    flow: List[Any] = []
    flow.append(_section_title(s, "Signature & Branding Recommendations"))

    sig = _ta.signature_advice(name, driver)
    if not sig.get("ok"):
        return flow

    rows = [
        ["First Letter:", f"{sig['first_letter']} (value {sig['first_letter_value']}, "
                          f"{sig['first_letter_planet']})"],
        ["Initial energy:", sig.get("initial_meaning", "")],
        ["Signature style for Driver:", sig.get("signature_tip", "")],
    ]
    t = Table(rows, colWidths=[55 * mm, 125 * mm])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR",(0, 0), (0, -1), TEXT_MID),
        ("VALIGN",   (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#EEE")),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 5 * mm))

    flow.append(Paragraph("<b>Universal Signature Rules:</b>", s["h3"]))
    for rule in sig.get("general_rules") or []:
        flow.append(Paragraph(f"• {rule}", s["body"]))
    flow.append(Spacer(1, 5 * mm))

    flow.append(_verdict_box(
        s, "Branding Tip",
        "Business naam ya brand name banate waqt — Chaldean number 1, 3, 5 ya 6 ka "
        "expression total target kare. <br/>"
        "<b>Avoid:</b> 8 (Saturn) starting brand names — initial 4-7 saal struggle. "
        "<b>Best:</b> 5 (Mercury) or 3 (Jupiter) for modern businesses.",
        "EXCELLENT",
    ))
    return flow


def _timeline_section(s) -> List[Any]:
    """30-day implementation timeline."""
    flow: List[Any] = []
    flow.append(_section_title(s, "Your 90-Day Implementation Plan"))
    flow.append(Paragraph(
        "Numerology corrections kabhi raat ko nahi badalte — slow rollout zaruri hai. "
        "Yeh schedule follow kare:",
        s["body_mid"]))
    flow.append(Spacer(1, 5 * mm))

    rows = [["Phase", "Action Plan"]]
    for item in _ta.implementation_timeline():
        rows.append([item["phase"], item["action"]])
    t = Table(rows, colWidths=[35 * mm, 145 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",   (0, 1), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR",  (0, 1), (0, -1), BRAND_GOLD),
        ("FONTSIZE",   (0, 0), (-1, -1), 10),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F4FF")]),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 6 * mm))

    flow.append(_verdict_box(
        s, "Final Reminder",
        "Numerology ek powerful supportive tool hai — par effort, integrity aur "
        "consistent action ka koi substitute nahi. Vibration ko apna karne ke baad "
        "kaam karna aur bhi zaruri ho jaata hai. Mehnat + correct vibration = unstoppable.",
        "EXCELLENT",
    ))
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
    # Page 1 — Cover
    story += _cover(s, name, dob)
    story.append(PageBreak())

    # Page 2 — Driver/Conductor intro
    story += _driver_conductor_intro(s, name, dob, driver, conductor)
    story.append(PageBreak())

    # Page 3-5 — Mobile / Vehicle / House deep analysis (one per page break)
    if mobile:
        story += _number_analysis_block(s, mobile, "mobile", driver, conductor)
        story.append(PageBreak())
    if vehicle:
        story += _number_analysis_block(s, vehicle, "vehicle", driver, conductor)
        story.append(PageBreak())
    if house:
        story += _number_analysis_block(s, house, "house", driver, conductor)
        story.append(PageBreak())

    # Page 6 — Number Compatibility Matrix
    story += _compatibility_matrix_section(s, driver)
    story.append(PageBreak())

    # Page 7 — Letter-by-letter table
    story += _letter_table_section(s, name)
    story.append(PageBreak())

    # Page 8 — Pythagorean vs Chaldean summary
    story += _name_numerology_section(s, name)
    story.append(PageBreak())

    # Page 9 — Name correction
    story += _name_correction_section(s, name, driver, conductor)
    story.append(PageBreak())

    # Page 10 — Signature & branding
    story += _signature_section(s, name, driver)
    story.append(PageBreak())

    # Page 11 — 90-day implementation plan
    story += _timeline_section(s)
    story += _disclaimer(s)

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

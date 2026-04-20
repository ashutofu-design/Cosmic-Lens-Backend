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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from vedic.numerology import tier_a as _ta
from vedic.numerology import narratives as _nr

# ── Devanagari font registration (Hindi mode) ──────────────────────────
# Latin (English/Hinglish) keeps Helvetica.  For Hindi narratives we
# register Noto Sans Devanagari from the Nix-managed font store.
_DEVA_REG  = "Helvetica"        # fallback if font missing
_DEVA_BOLD = "Helvetica-Bold"


def _find_devanagari_fonts() -> Optional[tuple]:
    """Locate Noto Sans Devanagari TTFs without scanning all of /nix/store.

    Strategy: single ``os.listdir('/nix/store')`` to find the
    ``noto-fonts-extra`` derivation, then probe a fixed sub-path.
    """
    import os
    candidates: List[str] = []
    # 1) Standard FHS locations (cheap).
    candidates += [
        "/usr/share/fonts/truetype/noto",
        "/usr/share/fonts/noto",
        "/run/current-system/sw/share/fonts/truetype/noto",
    ]
    # 2) Single-shot Nix store lookup — listdir is one syscall.
    try:
        for entry in os.listdir("/nix/store"):
            if "noto-fonts-extra" in entry:
                candidates.append(
                    f"/nix/store/{entry}/share/fonts/truetype/noto"
                )
                break
    except Exception:
        pass
    for d in candidates:
        reg  = os.path.join(d, "NotoSansDevanagari-Medium.ttf")
        bold = os.path.join(d, "NotoSansDevanagari-ExtraBold.ttf")
        if os.path.exists(reg) and os.path.exists(bold):
            return reg, bold
    return None


try:
    _paths = _find_devanagari_fonts()
    if _paths:
        pdfmetrics.registerFont(TTFont("NotoDeva", _paths[0]))
        pdfmetrics.registerFont(TTFont("NotoDeva-Bold", _paths[1]))
        _DEVA_REG  = "NotoDeva"
        _DEVA_BOLD = "NotoDeva-Bold"
except Exception:
    pass

BRAND_PURPLE = colors.HexColor("#5B21B6")
BRAND_GOLD = colors.HexColor("#D97706")
TEXT_DARK = colors.HexColor("#1F2937")
TEXT_MID = colors.HexColor("#4B5563")
TEXT_SOFT = colors.HexColor("#6B7280")


# ─── Language helper ────────────────────────────────────────────────────
# `lang` ∈ {"english", "hindi", "hinglish"}.  Default is hinglish.

def _T(lang: str, en: str, hi: str, hg: str) -> str:
    """Pick string based on selected language."""
    lang = (lang or "hinglish").lower()
    if lang == "english":
        return en
    if lang == "hindi":
        return hi
    return hg


def _explain_card(s, lang: str, title_en: str, title_hi: str, title_hg: str,
                  body_en: str, body_hi: str, body_hg: str,
                  bg="#F0FDF4", border="#15803D") -> Any:
    """Reusable explanation callout block — used in every new section."""
    title = _T(lang, title_en, title_hi, title_hg)
    body  = _T(lang, body_en,  body_hi,  body_hg)
    fname = _DEVA_REG if (lang or "").lower() == "hindi" else "Helvetica"
    para = Paragraph(
        f"<font color='{border}'><b>{title}</b></font><br/><br/>"
        f"<font color='#1F2937'>{body}</font>",
        ParagraphStyle("ec", fontName=fname, fontSize=9.5, leading=14,
                       textColor=colors.HexColor("#1F2937"),
                       leftIndent=4, rightIndent=4))
    t = Table([[para]], colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor(bg)),
        ("BOX",          (0, 0), (-1, -1), 1.2, colors.HexColor(border)),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
    ]))
    return t


def _styles(lang: str = "hinglish") -> Dict[str, ParagraphStyle]:
    """Build paragraph styles.

    Devanagari font (Noto Sans Devanagari) only ships glyphs for Devanagari,
    so we use it ONLY for headings/titles that we author as pure Devanagari
    in Hindi mode.  Body/small/captions stay on Helvetica (Latin) — they
    often contain Hinglish data tables and would render as missing-glyph
    boxes if forced to NotoDeva.
    """
    base = getSampleStyleSheet()
    is_hi = (lang or "").lower() == "hindi"
    H_BOLD = _DEVA_BOLD if is_hi else "Helvetica-Bold"
    H_REG  = _DEVA_REG  if is_hi else "Helvetica"
    return {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=H_BOLD,
                             fontSize=22, leading=28, textColor=BRAND_PURPLE,
                             alignment=TA_CENTER, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=H_BOLD,
                             fontSize=15, leading=18, textColor=BRAND_PURPLE,
                             spaceBefore=10, spaceAfter=6),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName=H_BOLD,
                             fontSize=11, leading=14, textColor=TEXT_DARK,
                             spaceBefore=6, spaceAfter=2),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica",
                               fontSize=10, leading=14, textColor=TEXT_DARK),
        "body_mid": ParagraphStyle("body_mid", parent=base["BodyText"], fontName="Helvetica",
                                   fontSize=9.5, leading=13, textColor=TEXT_MID),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName="Helvetica",
                                fontSize=8, leading=10, textColor=TEXT_SOFT),
        "cover_name": ParagraphStyle("cover_name", parent=base["Heading1"],
                                     fontName=H_BOLD, fontSize=28, leading=34,
                                     textColor=TEXT_DARK, alignment=TA_CENTER,
                                     spaceBefore=8, spaceAfter=8),
        "cover_sub": ParagraphStyle("cover_sub", parent=base["BodyText"],
                                    fontName=H_REG, fontSize=12, leading=16,
                                    textColor=TEXT_MID, alignment=TA_CENTER),
        "tagline": ParagraphStyle("tagline", parent=base["BodyText"],
                                  fontName="Helvetica-Oblique", fontSize=11, leading=14,
                                  textColor=BRAND_GOLD, alignment=TA_CENTER,
                                  spaceAfter=6),
        "page_title": ParagraphStyle("page_title", parent=base["Heading1"],
                                     fontName=H_BOLD, fontSize=18, leading=22,
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
        [Paragraph("<b>Is Premium Report Me Aapko Milega:</b>", ParagraphStyle(
            "ct", fontName="Helvetica-Bold", fontSize=12, textColor=TEXT_DARK,
            alignment=TA_CENTER, leading=16))],
        [Paragraph(
            "✓ <b>Life Blueprint Card</b> — core personality + 2026 focus<br/>"
            "✓ <b>Aap Kaun Ho</b> — 3-paragraph identity story (5 strengths + 5 challenges)<br/>"
            "✓ <b>Career Blueprint</b> — best fields, mistakes, growth timing, money pattern<br/>"
            "✓ <b>Love Pattern</b> — relationship style, breakup triggers, ideal partner<br/>"
            "✓ <b>Health &amp; Dharma</b> — body signals + spiritual path<br/>"
            "✓ <b>Risk Alerts &amp; Golden Periods</b> — kab cautious, kab bada move<br/>"
            "✓ <b>Mobile / Vehicle / House</b> — Why · Impact · Action format me<br/>"
            "✓ <b>Name Numerology</b> + Name Correction (top 3 variants)<br/>"
            "✓ <b>Compatibility Matrix</b>, signature design, 90-day plan",
            ParagraphStyle("cb", fontName="Helvetica", fontSize=10,
                           textColor=TEXT_MID, alignment=TA_CENTER, leading=15))],
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

    # ─ Why · Impact · Action narrative (premium ₹1499 layer)
    reduced = out.get("reduced")
    if isinstance(reduced, int) and 1 <= reduced <= 9:
        flow += _why_impact_action_block(s, kind, reduced)

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


# ─── Premium narrative pages (₹1499 depth) ───────────────────────────

def _premium_card(s, heading: str, body_html: str,
                  bg_color=None, border_color=None) -> Table:
    """Reusable two-row card: heading + body, with brand color frame."""
    bg = bg_color or colors.HexColor("#FAF5FF")
    bd = border_color or BRAND_PURPLE
    inner = [
        [Paragraph(f"<b>{heading}</b>", ParagraphStyle(
            "pcardh", fontName="Helvetica-Bold", fontSize=11,
            textColor=bd, leading=14))],
        [Paragraph(body_html, ParagraphStyle(
            "pcardb", fontName="Helvetica", fontSize=10,
            textColor=TEXT_DARK, leading=14, spaceBefore=2))],
    ]
    t = Table(inner, colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX",        (0, 0), (-1, -1), 0.6, bd),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING",(0, -1), (-1, -1), 8),
    ]))
    return t


def _life_summary_block(s, name: str, driver: int, conductor: int) -> List[Any]:
    """Premium Life Summary card — top of report (instant ₹1499 feel)."""
    flow: List[Any] = []
    summary = _nr.life_summary_block(driver, conductor, name)

    flow.append(Paragraph("⭐ YOUR LIFE BLUEPRINT", s["page_title"]))
    flow.append(Spacer(1, 2 * mm))
    flow.append(Paragraph(
        "<i>Aapki kundli aur janma-tithi ke aadhar par taiyaar — 100% personalized.</i>",
        ParagraphStyle("ls_sub", fontName="Helvetica-Oblique", fontSize=10,
                       textColor=TEXT_SOFT, leading=14, spaceAfter=8)))

    rows = [
        [Paragraph("<b>Core Personality</b>", s["body_mid"]),
         Paragraph(summary["core_personality"], s["body"])],
        [Paragraph("<b>Tagline</b>", s["body_mid"]),
         Paragraph(f"<i>{summary['tagline']}</i>", s["body"])],
        [Paragraph("<b>Primary Planet</b>", s["body_mid"]),
         Paragraph(f"{summary['primary_planet']} (Driver {driver})", s["body"])],
        [Paragraph("<b>Secondary Planet</b>", s["body_mid"]),
         Paragraph(f"{summary['secondary_planet']} (Conductor {conductor})", s["body"])],
        [Paragraph("<b>Biggest Strength</b>", s["body_mid"]),
         Paragraph(f"<font color='#15803D'>✓ {summary['biggest_strength']}</font>", s["body"])],
        [Paragraph("<b>Biggest Challenge</b>", s["body_mid"]),
         Paragraph(f"<font color='#B91C1C'>⚠ {summary['biggest_challenge']}</font>", s["body"])],
        [Paragraph("<b>2026 Focus</b>", s["body_mid"]),
         Paragraph(f"<b>{summary['2026_focus']}</b>", s["body"])],
    ]
    t = Table(rows, colWidths=[42 * mm, 138 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
        ("BOX",            (0, 0), (-1, -1), 1.2, BRAND_GOLD),
        ("INNERGRID",      (0, 0), (-1, -1), 0.3, colors.HexColor("#FCD34D")),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ("TOPPADDING",     (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 7),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 6 * mm))
    flow.append(Paragraph(
        "<i>Yeh page aapke liye 'consultation summary' jaisa hai. Agle pages me har "
        "section ka deep explanation milega — Why, Impact aur Action ke saath.</i>",
        ParagraphStyle("ls_foot", fontName="Helvetica-Oblique", fontSize=9,
                       textColor=TEXT_SOFT, leading=13, alignment=TA_CENTER)))
    return flow


def _life_essence_section(s, driver: int) -> List[Any]:
    """Page: 'Aap Kaun Ho?' — 3-paragraph identity story."""
    flow: List[Any] = []
    n = _nr.narrative_for(driver) or {}
    flow.append(Paragraph("🌟 AAP KAUN HO — Your True Identity", s["page_title"]))
    flow.append(Spacer(1, 2 * mm))
    flow.append(Paragraph(
        f"<i>{n.get('title', '')} — {n.get('tagline', '')}</i>",
        ParagraphStyle("le_sub", fontName="Helvetica-Oblique", fontSize=11,
                       textColor=BRAND_GOLD, leading=15, spaceAfter=8)))
    paras = n.get("life_essence") or []
    for i, para in enumerate(paras, 1):
        flow.append(Paragraph(f"<b>Story {i}:</b>", s["h3"]))
        flow.append(Paragraph(para, s["body"]))
        flow.append(Spacer(1, 4 * mm))

    # Strengths + Challenges side-by-side
    strengths = n.get("strengths") or []
    challenges = n.get("challenges") or []
    if strengths or challenges:
        flow.append(Spacer(1, 3 * mm))
        s_html = "<br/>".join([f"<font color='#15803D'>✓</font> {x}" for x in strengths])
        c_html = "<br/>".join([f"<font color='#B91C1C'>⚠</font> {x}" for x in challenges])
        sc = [[
            _premium_card(s, "5 HIDDEN STRENGTHS", s_html,
                          bg_color=colors.HexColor("#F0FDF4"),
                          border_color=colors.HexColor("#15803D")),
            _premium_card(s, "5 HIDDEN CHALLENGES", c_html,
                          bg_color=colors.HexColor("#FEF2F2"),
                          border_color=colors.HexColor("#B91C1C")),
        ]]
        # Wrap each card in a fixed-width column
        sc_table = Table(sc, colWidths=[88 * mm, 88 * mm])
        sc_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        # Re-render each card with smaller width to fit
        s_card = _premium_card(s, "5 HIDDEN STRENGTHS", s_html,
                               bg_color=colors.HexColor("#F0FDF4"),
                               border_color=colors.HexColor("#15803D"))
        s_card._argW = [88 * mm]
        c_card = _premium_card(s, "5 HIDDEN CHALLENGES", c_html,
                               bg_color=colors.HexColor("#FEF2F2"),
                               border_color=colors.HexColor("#B91C1C"))
        c_card._argW = [88 * mm]
        side = Table([[s_card, c_card]], colWidths=[91 * mm, 91 * mm])
        side.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ]))
        flow.append(side)
    return flow


def _career_blueprint_section(s, driver: int) -> List[Any]:
    """Page: Career Blueprint — fields, mistakes, growth timing."""
    flow: List[Any] = []
    n = _nr.narrative_for(driver) or {}
    flow.append(Paragraph("💼 CAREER BLUEPRINT — Your Professional Path", s["page_title"]))
    flow.append(Spacer(1, 4 * mm))
    paras = n.get("career_pattern") or []
    labels = ["WHY (Aap kis kaam ke liye bane ho)",
              "COMMON MISTAKE (jo aap karte ho)",
              "GROWTH TIMING (kab milega result)"]
    border_colors_seq = [BRAND_PURPLE, colors.HexColor("#B91C1C"), colors.HexColor("#15803D")]
    bg_colors_seq = [colors.HexColor("#FAF5FF"),
                     colors.HexColor("#FEF2F2"),
                     colors.HexColor("#F0FDF4")]
    for i, para in enumerate(paras):
        flow.append(_premium_card(
            s,
            labels[i] if i < len(labels) else f"Insight {i+1}",
            para,
            bg_color=bg_colors_seq[i % 3],
            border_color=border_colors_seq[i % 3],
        ))
        flow.append(Spacer(1, 4 * mm))

    # Money + Health quick cards
    if n.get("money_pattern"):
        flow.append(_premium_card(s, "💰 MONEY PATTERN — Paisa kaise aayega",
                                  n["money_pattern"],
                                  bg_color=colors.HexColor("#FFFBEB"),
                                  border_color=BRAND_GOLD))
        flow.append(Spacer(1, 4 * mm))
    return flow


def _love_pattern_section(s, driver: int) -> List[Any]:
    """Page: Love & Relationship deep-dive."""
    flow: List[Any] = []
    n = _nr.narrative_for(driver) or {}
    flow.append(Paragraph("💕 LOVE PATTERN — Rishton ki Reality", s["page_title"]))
    flow.append(Spacer(1, 4 * mm))
    paras = n.get("love_pattern") or []
    labels = ["LOVE STYLE (Aap pyar me kaise ho)",
              "BREAKUP TRIGGER (rishta kyun tutta hai)",
              "IDEAL PARTNER (kis number wala suit karega)"]
    border_colors_seq = [colors.HexColor("#DB2777"),
                         colors.HexColor("#B91C1C"),
                         colors.HexColor("#15803D")]
    bg_colors_seq = [colors.HexColor("#FDF2F8"),
                     colors.HexColor("#FEF2F2"),
                     colors.HexColor("#F0FDF4")]
    for i, para in enumerate(paras):
        flow.append(_premium_card(
            s,
            labels[i] if i < len(labels) else f"Insight {i+1}",
            para,
            bg_color=bg_colors_seq[i % 3],
            border_color=border_colors_seq[i % 3],
        ))
        flow.append(Spacer(1, 4 * mm))
    return flow


def _wealth_health_spirit_section(s, driver: int) -> List[Any]:
    """Page: Money + Health + Spiritual path combined."""
    flow: List[Any] = []
    n = _nr.narrative_for(driver) or {}
    flow.append(Paragraph("🕉️ HEALTH & DHARMA — Body + Soul", s["page_title"]))
    flow.append(Spacer(1, 4 * mm))

    if n.get("health_pattern"):
        flow.append(_premium_card(s, "🩺 HEALTH PATTERN — Body kya keh rahi hai",
                                  n["health_pattern"],
                                  bg_color=colors.HexColor("#ECFEFF"),
                                  border_color=colors.HexColor("#0E7490")))
        flow.append(Spacer(1, 4 * mm))

    if n.get("spiritual_path"):
        flow.append(_premium_card(s, "🙏 SPIRITUAL PATH — Aapka dharma",
                                  n["spiritual_path"],
                                  bg_color=colors.HexColor("#FEF3C7"),
                                  border_color=BRAND_GOLD))
        flow.append(Spacer(1, 4 * mm))

    return flow


def _risk_alerts_section(s, driver: int) -> List[Any]:
    """Page: Risk Alerts + Golden Opportunity Periods."""
    flow: List[Any] = []
    n = _nr.narrative_for(driver) or {}
    flow.append(Paragraph("⚠️ RISK ALERTS & 🌟 GOLDEN PERIODS", s["page_title"]))
    flow.append(Spacer(1, 4 * mm))

    risks = n.get("risk_alerts") or []
    if risks:
        risk_html = "<br/>".join([f"<font color='#B91C1C'>⚠</font> {r}" for r in risks])
        flow.append(_premium_card(
            s, "5 SPECIFIC RISKS — Inhe Avoid Karein",
            risk_html,
            bg_color=colors.HexColor("#FEF2F2"),
            border_color=colors.HexColor("#B91C1C"),
        ))
        flow.append(Spacer(1, 5 * mm))

    if n.get("golden_periods"):
        flow.append(_premium_card(
            s, "🌟 GOLDEN OPPORTUNITY WINDOW — Inn dino par bada move karein",
            n["golden_periods"],
            bg_color=colors.HexColor("#FFFBEB"),
            border_color=BRAND_GOLD,
        ))
        flow.append(Spacer(1, 5 * mm))

    flow.append(_premium_card(
        s, "📌 EXECUTIVE SUMMARY — Pichle pages ka ek-line saar",
        f"Aap <b>{(n.get('title') or 'Number ' + str(driver))}</b> ho. "
        f"{n.get('tagline', '')} "
        "Apni greatest strength par double-down karein, biggest challenge par awareness "
        "rakhein, aur risk windows me extra cautious. Golden period me bada decision lein.",
        bg_color=colors.HexColor("#F0F9FF"),
        border_color=colors.HexColor("#0369A1"),
    ))
    return flow


def _lucky_colours_section(s, driver: int, vehicle: Optional[str] = None) -> List[Any]:
    """Premium Lucky Colours page — vehicle, dress, business, day-wise."""
    flow: List[Any] = []
    pack = _nr.lucky_colours_pack(driver)

    flow.append(Paragraph("🎨 LUCKY COLOURS — Aapke Liye Specially Picked", s["page_title"]))
    flow.append(Spacer(1, 2 * mm))
    flow.append(Paragraph(
        "<i>Driver number ke planet ke aadhar par chosen — daily life me use karein.</i>",
        ParagraphStyle("lc_sub", fontName="Helvetica-Oblique", fontSize=10,
                       textColor=TEXT_SOFT, leading=14, spaceAfter=8)))

    # Primary / Secondary / Avoid table
    rows = [
        [Paragraph("<b>✓ Primary (most lucky)</b>", s["body_mid"]),
         Paragraph(f"<font color='#15803D'>{', '.join(pack['primary'])}</font>", s["body"])],
        [Paragraph("<b>✓ Secondary (supportive)</b>", s["body_mid"]),
         Paragraph(f"<font color='#0369A1'>{', '.join(pack['secondary'])}</font>", s["body"])],
        [Paragraph("<b>⚠ Avoid (drains energy)</b>", s["body_mid"]),
         Paragraph(f"<font color='#B91C1C'>{', '.join(pack['avoid'])}</font>", s["body"])],
        [Paragraph("<b>💎 Gemstone tone</b>", s["body_mid"]),
         Paragraph(pack["gemstone_tone"], s["body"])],
    ]
    t = Table(rows, colWidths=[55 * mm, 125 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
        ("BOX",            (0, 0), (-1, -1), 1.0, BRAND_GOLD),
        ("INNERGRID",      (0, 0), (-1, -1), 0.3, colors.HexColor("#FCD34D")),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 5 * mm))

    # Vehicle colour card (specially bigger if vehicle was provided)
    veh_heading = "🚗 GADI / VEHICLE COLOUR"
    if vehicle:
        veh_heading += f" — Aapki gadi ({vehicle}) ke liye"
    flow.append(_premium_card(s, veh_heading, pack["vehicle"],
                              bg_color=colors.HexColor("#EFF6FF"),
                              border_color=colors.HexColor("#1D4ED8")))
    flow.append(Spacer(1, 4 * mm))

    # Business / Branding
    flow.append(_premium_card(s, "🏢 BUSINESS / BRAND COLOUR",
                              pack["business"],
                              bg_color=colors.HexColor("#F3E8FF"),
                              border_color=BRAND_PURPLE))
    flow.append(Spacer(1, 4 * mm))

    return flow


def _day_dress_section(s, driver: int) -> List[Any]:
    """Day-wise colour to wear — Mon-Sun planetary table."""
    flow: List[Any] = []
    pack = _nr.lucky_colours_pack(driver)

    flow.append(Paragraph("👕 KIS DIN KAUNSA COLOUR PEHNEIN", s["page_title"]))
    flow.append(Spacer(1, 2 * mm))
    flow.append(Paragraph(
        "<i>Vedic planetary days ke according — har din ka 'power colour' pehno aur "
        "us din ki energy unlock karo.</i>",
        ParagraphStyle("dd_sub", fontName="Helvetica-Oblique", fontSize=10,
                       textColor=TEXT_SOFT, leading=14, spaceAfter=8)))

    header_style = ParagraphStyle("dd_h", fontName="Helvetica-Bold", fontSize=10,
                                  textColor=colors.white, leading=13, alignment=TA_CENTER)
    rows = [[Paragraph("<b>Day</b>", header_style),
             Paragraph("<b>Planet</b>", header_style),
             Paragraph("<b>Colour to Wear</b>", header_style),
             Paragraph("<b>Purpose</b>", header_style)]]
    for d in pack["day_dress"]:
        rows.append([
            Paragraph(f"<b>{d['day']}</b>", s["body_mid"]),
            Paragraph(d["planet"], s["body"]),
            Paragraph(f"<font color='#B45309'><b>{d['colour']}</b></font>", s["body"]),
            Paragraph(d["purpose"], s["small"]),
        ])
    t = Table(rows, colWidths=[24 * mm, 36 * mm, 50 * mm, 70 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
        ("BACKGROUND",     (0, 1), (-1, -1), colors.HexColor("#FFFBEB")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#FFFBEB"), colors.HexColor("#FEF3C7")]),
        ("BOX",            (0, 0), (-1, -1), 0.8, BRAND_GOLD),
        ("INNERGRID",      (0, 0), (-1, -1), 0.3, colors.HexColor("#FCD34D")),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 5 * mm))

    flow.append(_premium_card(
        s, "💡 PRO TIP — How to use this",
        "<b>Roz 7 colours nahi yaad rakhne — sirf important din ka colour focus karein.</b><br/>"
        "• Job interview = us din ke planet ka colour<br/>"
        "• First date = Friday ka White/Pink<br/>"
        "• Court date / govt work = Saturday ka Deep Blue<br/>"
        "• Business launch = Thursday ka Yellow ya Sunday ka Golden<br/>"
        "• Family function = Monday ka White / Friday ka Pink<br/>"
        f"<br/>Aapka personal driver-{driver} ka primary colour bhi MIX kar sakte ho — "
        "white shirt + driver-colour tie/scarf style.",
        bg_color=colors.HexColor("#F0F9FF"),
        border_color=colors.HexColor("#0369A1"),
    ))
    return flow


def _monthly_forecast_section(s, driver: int, conductor: int, year: int = 2026,
                              lang: str = "hinglish") -> List[Any]:
    """12-month personal forecast — month-by-month theme + best dates."""
    flow: List[Any] = []
    pack = _nr.monthly_forecast_pack(driver, conductor, year)

    title = _T(lang,
        f"🗓️ YOUR {year} — 12-MONTH FORECAST",
        f"🗓️ {year} का 12-महीने का भविष्यफल",
        f"🗓️ {year} KA 12-MAHINE KA FORECAST")
    flow.append(Paragraph(title, s["page_title"]))
    flow.append(Spacer(1, 3 * mm))

    # ─── Yeh Kya Hai? — opening explanation ─────────────────────────
    flow.append(_explain_card(s, lang,
        "📖 What is Personal Year & Personal Month?",
        "📖 पर्सनल ईयर और पर्सनल मंथ क्या है?",
        "📖 Personal Year aur Personal Month kya hai?",
        # body
        f"Every year of your life carries a unique number (1-9) called your <b>Personal Year</b>. "
        f"It is calculated as: <b>Driver ({driver}) + Conductor ({conductor}) + Year ({year})</b>, all reduced. "
        f"Your Personal Year for {year} is <b>{pack['personal_year']}</b>. "
        f"This shapes the overall theme — career push, love, change, rest, money, completion. "
        f"<b>Personal Month</b> = Personal Year + month number. Each month has its own energy. "
        f"Use this calendar to <b>plan launches, weddings, travel, investments, and rest periods</b> in advance — "
        f"you stop fighting the wind and start sailing with it.",
        # hindi
        f"आपके जीवन का हर साल एक विशेष संख्या (1-9) रखता है, जिसे <b>Personal Year</b> कहते हैं। "
        f"गणना: <b>Driver ({driver}) + Conductor ({conductor}) + Year ({year})</b>, reduce करके। "
        f"आपका {year} का Personal Year <b>{pack['personal_year']}</b> है। यह पूरे साल की मुख्य ऊर्जा तय करता है — "
        f"करियर, प्रेम, बदलाव, विश्राम, धन, अंत। <b>Personal Month</b> = Personal Year + month number. "
        f"इस calendar से <b>लॉन्च, विवाह, यात्रा, निवेश, विश्राम</b> पहले से प्लान करें — "
        f"आप हवा से लड़ना बंद करके उसके साथ बहना शुरू करते हैं।",
        # hinglish
        f"Aapke jeevan ka har saal ek unique number (1-9) hota hai jise <b>Personal Year</b> kehte hain. "
        f"Calculation: <b>Driver ({driver}) + Conductor ({conductor}) + Year ({year})</b>, reduce karke. "
        f"Aapka {year} ka Personal Year <b>{pack['personal_year']}</b> hai. Yeh poore saal ka theme tay karta hai — "
        f"career push, love, change, rest, money, completion. <b>Personal Month</b> = Personal Year + month number. "
        f"Har mahine ki apni energy hoti hai. Iss calendar se <b>launches, shaadi, travel, investments, aur rest</b> "
        f"pehle se plan karein — aap hawa se ladna band karte ho aur uske saath bahna shuru karte ho.",
        bg="#EFF6FF", border="#1D4ED8"))
    flow.append(Spacer(1, 5 * mm))

    pyear_label = _T(lang, "Personal Year", "पर्सनल ईयर", "Personal Year")
    if (lang or "").lower() == "hindi":
        label_html = (f'<font name="{_DEVA_BOLD}">{pyear_label}:</font> '
                      f"{pack['personal_year']} — <i>{pack['year_theme']}</i>")
    else:
        label_html = (f"<b>{pyear_label}:</b> {pack['personal_year']} — "
                      f"<i>{pack['year_theme']}</i>")
    flow.append(Paragraph(label_html, s["body_mid"]))
    flow.append(Spacer(1, 4 * mm))

    header_style = ParagraphStyle("mf_h", fontName="Helvetica-Bold", fontSize=9,
                                  textColor=colors.white, leading=12, alignment=TA_CENTER)
    rows = [[
        Paragraph("<b>Month</b>", header_style),
        Paragraph("<b>PM</b>", header_style),
        Paragraph("<b>Verdict</b>", header_style),
        Paragraph("<b>Theme</b>", header_style),
        Paragraph("<b>Best Dates</b>", header_style),
    ]]
    VERDICT_BG = {"EXCELLENT": colors.HexColor("#DCFCE7"),
                  "GOOD":      colors.HexColor("#FEF3C7"),
                  "GENTLE":    colors.HexColor("#E0F2FE"),
                  "WORK":      colors.HexColor("#FEE2E2")}

    style_rows = [
        ("BACKGROUND",     (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
        ("BOX",            (0, 0), (-1, -1), 0.8, BRAND_PURPLE),
        ("INNERGRID",      (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",    (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 5),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("FONTSIZE",       (0, 0), (-1, -1), 8),
    ]
    for i, m in enumerate(pack["months"], start=1):
        rows.append([
            Paragraph(f"<b>{m['month']}</b>", s["body_mid"]),
            Paragraph(f"<b>{m['personal_month']}</b>", s["body_mid"]),
            Paragraph(f"<b>{m['verdict']}</b>", s["small"]),
            Paragraph(m["theme"], s["small"]),
            Paragraph(", ".join(str(d) for d in m["best_dates"]), s["small"]),
        ])
        style_rows.append(("BACKGROUND", (0, i), (-1, i),
                          VERDICT_BG.get(m["verdict"], colors.HexColor("#F8FAFC"))))

    t = Table(rows, colWidths=[18 * mm, 12 * mm, 22 * mm, 100 * mm, 28 * mm])
    t.setStyle(TableStyle(style_rows))
    flow.append(t)
    flow.append(Spacer(1, 4 * mm))
    flow.append(Paragraph(
        "<i>PM = Personal Month number. Best Dates = aapke driver ke friend numbers ke days.</i>",
        s["small"]))
    return flow


def _deep_compat_section(s, driver: int, lang: str = "hinglish") -> List[Any]:
    """Love + Marriage + Business compatibility per number 1-9."""
    flow: List[Any] = []
    pack = _nr.deep_compatibility_pack(driver)
    planet = _nr._PLANETS.get(driver, "—")

    title = _T(lang,
        "💑 DEEP COMPATIBILITY — Love · Marriage · Business",
        "💑 गहरी अनुकूलता — प्रेम · विवाह · व्यवसाय",
        "💑 DEEP COMPATIBILITY — Love · Marriage · Business")
    flow.append(Paragraph(title, s["page_title"]))
    flow.append(Spacer(1, 3 * mm))

    flow.append(_explain_card(s, lang,
        "📖 How does this compatibility table work?",
        "📖 यह अनुकूलता तालिका कैसे काम करती है?",
        "📖 Yeh compatibility table kaise kaam karti hai?",
        f"Each number 1-9 is ruled by a planet. Your driver <b>{driver}</b> is ruled by <b>{planet}</b>. "
        f"Vedic astrology has a fixed planet-relationship table: <b>Friend, Neutral, Enemy, Twin</b>. "
        f"Same logic applies to numbers. We score every number on three real-life contexts: "
        f"<b>💕 Love</b> (dating, attraction, chemistry), <b>💍 Marriage</b> (long-term living, family, in-laws), "
        f"and <b>💼 Business</b> (partnership, money, decisions). A high score (80-95) means easy flow. "
        f"Low (20-30) means real friction — possible but needs effort + remedies. "
        f"<b>Use this when</b>: meeting someone serious, evaluating a partner, choosing a business associate, "
        f"or even understanding why your boss/sibling clashes with you.",
        f"प्रत्येक संख्या 1-9 का एक स्वामी ग्रह है। आपके driver <b>{driver}</b> का स्वामी <b>{planet}</b> है। "
        f"वैदिक ज्योतिष में ग्रहों का संबंध तय है: <b>मित्र, समान, शत्रु, स्वयं</b>। यही नियम संख्याओं पर भी लागू होता है। "
        f"हम हर संख्या को 3 क्षेत्रों में स्कोर देते हैं: <b>💕 प्रेम</b> (आकर्षण, केमिस्ट्री), "
        f"<b>💍 विवाह</b> (दीर्घकालिक जीवन, परिवार), और <b>💼 व्यवसाय</b> (साझेदारी, धन)। "
        f"उच्च स्कोर (80-95) = सहज प्रवाह। निम्न (20-30) = घर्षण, उपायों से संभव। "
        f"<b>उपयोग करें</b>: गंभीर मुलाकात, साथी मूल्यांकन, बिज़नेस पार्टनर, बॉस/भाई-बहन के रिश्ते समझने में।",
        f"Har number 1-9 ka ek ruling planet hai. Aapke driver <b>{driver}</b> ka planet <b>{planet}</b> hai. "
        f"Vedic astrology me planet-relationship table fixed hai: <b>Friend, Neutral, Enemy, Twin</b>. "
        f"Yahi logic numbers pe apply hota hai. Hum har number ko 3 real-life contexts me score dete hain: "
        f"<b>💕 Love</b> (dating, attraction, chemistry), <b>💍 Marriage</b> (long-term saath rehna, family, in-laws), "
        f"aur <b>💼 Business</b> (partnership, paisa, decisions). High score (80-95) = easy flow. "
        f"Low (20-30) = real friction — possible hai but effort + remedies chahiye. "
        f"<b>Iska use kab karein</b>: kisi ko seriously milte waqt, partner evaluate karte waqt, business associate chunte waqt, "
        f"ya boss/bhai-behen ke clash ko samajhne ke liye.",
        bg="#EFF6FF", border="#1D4ED8"))
    flow.append(Spacer(1, 5 * mm))

    intro = _T(lang,
        f"Below: how your driver <b>{driver}</b> ({planet}) interacts with each number across 3 life areas.",
        f"नीचे: आपका driver <b>{driver}</b> ({planet}) हर संख्या के साथ 3 क्षेत्रों में कैसा व्यवहार करता है।",
        f"Neeche: aapka driver <b>{driver}</b> ({planet}) baaki har number ke saath 3 life areas me kaisa interact karta hai.")
    flow.append(Paragraph(f"<i>{intro}</i>",
        ParagraphStyle("dc_sub", fontName="Helvetica-Oblique", fontSize=10,
                       textColor=TEXT_SOFT, leading=14, spaceAfter=8)))

    header = ParagraphStyle("dc_h", fontName="Helvetica-Bold", fontSize=10,
                            textColor=colors.white, leading=13, alignment=TA_CENTER)
    rows = [[Paragraph("<b>#</b>", header), Paragraph("<b>Planet</b>", header),
             Paragraph("<b>Type</b>", header), Paragraph("<b>💕 Love</b>", header),
             Paragraph("<b>💍 Marriage</b>", header), Paragraph("<b>💼 Business</b>", header)]]

    LABEL_BG = {"TWIN":   colors.HexColor("#FFFBEB"),
                "FRIEND": colors.HexColor("#DCFCE7"),
                "NEUTRAL":colors.HexColor("#F3F4F6"),
                "ENEMY":  colors.HexColor("#FEE2E2")}

    style_rows = [
        ("BACKGROUND",  (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("BOX",         (0, 0), (-1, -1), 0.8, BRAND_PURPLE),
        ("INNERGRID",   (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",(0, 0), (-1, -1), 4),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]
    for i, r in enumerate(pack["rows"], start=1):
        rows.append([
            Paragraph(f"<b>{r['number']}</b>", s["body_mid"]),
            Paragraph(r["planet"], s["body"]),
            Paragraph(f"<b>{r['label']}</b>", s["small"]),
            Paragraph(f"<b>{r['love']}</b>/100", s["body_mid"]),
            Paragraph(f"<b>{r['marriage']}</b>/100", s["body_mid"]),
            Paragraph(f"<b>{r['business']}</b>/100", s["body_mid"]),
        ])
        style_rows.append(("BACKGROUND", (0, i), (-1, i),
                          LABEL_BG.get(r["label"], colors.white)))
    t = Table(rows, colWidths=[14 * mm, 28 * mm, 26 * mm, 36 * mm, 36 * mm, 36 * mm])
    t.setStyle(TableStyle(style_rows))
    flow.append(t)
    flow.append(Spacer(1, 5 * mm))

    # Top 3 best + worst
    best = ", ".join(f"<b>{r['number']}</b> ({r['planet']})" for r in pack["top3_best"])
    worst = ", ".join(f"<b>{r['number']}</b> ({r['planet']})" for r in pack["top3_worst"])
    flow.append(_premium_card(s, "🏆 TOP 3 BEST MATCHES (har context me strong)", best,
                              bg_color=colors.HexColor("#F0FDF4"),
                              border_color=colors.HexColor("#15803D")))
    flow.append(Spacer(1, 3 * mm))
    flow.append(_premium_card(s, "⛔ TOP 3 WORST MATCHES (extra effort lagega)", worst,
                              bg_color=colors.HexColor("#FEF2F2"),
                              border_color=colors.HexColor("#B91C1C")))
    return flow


def _lucky_numbers_section(s, driver: int, lang: str = "hinglish") -> List[Any]:
    """Lucky numbers, dates, PIN, account, lottery tips."""
    flow: List[Any] = []
    pack = _nr.lucky_numbers_pack(driver)

    title = _T(lang,
        "🔢 LUCKY NUMBERS — Your Personal Power Numbers",
        "🔢 शुभ अंक — आपकी निजी शक्ति संख्याएँ",
        "🔢 LUCKY NUMBERS — Aapke Personal Power Numbers")
    flow.append(Paragraph(title, s["page_title"]))
    flow.append(Spacer(1, 3 * mm))

    flow.append(_explain_card(s, lang,
        "📖 Why do lucky numbers matter?",
        "📖 शुभ अंक क्यों ज़रूरी हैं?",
        "📖 Lucky numbers kyu zaroori hain?",
        "Numbers are not random — they carry vibrations. When you pick a phone number, vehicle plate, "
        "ATM PIN, account number, flat number, or even a wedding date that <b>matches your driver's friends</b>, "
        "the energy flows with you instead of against you. Conversely, repeated exposure to <b>enemy numbers</b> "
        "(in your daily-use objects) creates subtle, persistent friction — slow phone, money leaks, arguments, "
        "missed opportunities. <b>This page is your shopping list.</b> Print it, save it on your phone, share with family. "
        "Whenever you choose a new number for anything — pick from the green list, avoid the red list. "
        "Over years, the cumulative effect is significant.",
        "अंक यादृच्छिक नहीं होते — हर अंक की कंपन (vibration) होती है। जब आप फ़ोन नंबर, वाहन प्लेट, ATM पिन, "
        "खाता संख्या, फ्लैट या विवाह तिथि चुनते समय <b>अपने driver के मित्र अंक</b> चुनते हैं, ऊर्जा आपके साथ बहती है। "
        "इसके विपरीत, दैनिक वस्तुओं में <b>शत्रु अंकों</b> का बार-बार सामना सूक्ष्म लेकिन निरंतर घर्षण पैदा करता है — "
        "धीमा फ़ोन, धन हानि, कलह, खोए हुए अवसर। <b>यह पृष्ठ आपकी ख़रीदारी सूची है।</b> इसे सहेजें, परिवार के साथ साझा करें। "
        "जब भी कोई नया अंक चुनें — हरी सूची से चुनें, लाल सूची से बचें। वर्षों में संचयी प्रभाव बहुत बड़ा होता है।",
        "Numbers random nahi hote — har number ki ek vibration hoti hai. Jab aap phone number, vehicle plate, "
        "ATM PIN, account number, flat number, ya shaadi ki date apne <b>driver ke friend numbers</b> se match karte ho, "
        "energy aapke saath bahti hai. Aur agar daily-use objects me <b>enemy numbers</b> ho to subtle but persistent "
        "friction milti hai — slow phone, paisa leak, arguments, missed opportunities. <b>Yeh page aapki shopping list hai.</b> "
        "Print karein, phone me save karein, family ke saath share karein. Jab bhi naya number chunna ho — green list se chunein, "
        "red list avoid karein. Saalon me cumulative effect bahut bada hota hai.",
        bg="#FFFBEB", border="#B45309"))
    flow.append(Spacer(1, 5 * mm))

    rows = [
        [Paragraph("<b>✓ Lucky single digits</b>", s["body_mid"]),
         Paragraph(f"<font color='#15803D'><b>{', '.join(str(n) for n in pack['single_digit_lucky'])}</b></font>", s["body"])],
        [Paragraph("<b>⚠ Avoid single digits</b>", s["body_mid"]),
         Paragraph(f"<font color='#B91C1C'>{', '.join(str(n) for n in pack['single_digit_avoid']) or '—'}</font>", s["body"])],
        [Paragraph("<b>🌟 Lucky day of week</b>", s["body_mid"]),
         Paragraph(f"<b>{pack['lucky_day']}</b>", s["body"])],
        [Paragraph("<b>📅 Lucky dates of month</b>", s["body_mid"]),
         Paragraph(", ".join(str(d) for d in pack["lucky_dates"]), s["body"])],
        [Paragraph("<b>📅 Avoid these dates</b>", s["body_mid"]),
         Paragraph(f"<font color='#B91C1C'>{', '.join(str(d) for d in pack['unlucky_dates']) or '—'}</font>", s["body"])],
        [Paragraph("<b>🎯 Lucky double-digits</b><br/><font size='8' color='#6B7280'>(PIN/account suffix)</font>", s["body_mid"]),
         Paragraph(", ".join(str(n) for n in pack["lucky_double_digit"]), s["body"])],
    ]
    t = Table(rows, colWidths=[55 * mm, 125 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
        ("BOX",            (0, 0), (-1, -1), 1.0, BRAND_GOLD),
        ("INNERGRID",      (0, 0), (-1, -1), 0.3, colors.HexColor("#FCD34D")),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 5 * mm))

    flow.append(_premium_card(s, "🏧 ATM PIN / Bank Number Tip", pack["atm_pin_tip"],
                              bg_color=colors.HexColor("#EFF6FF"),
                              border_color=colors.HexColor("#1D4ED8")))
    flow.append(Spacer(1, 3 * mm))
    flow.append(_premium_card(s, "🏦 Account / Locker Number Tip", pack["account_tip"],
                              bg_color=colors.HexColor("#F3E8FF"),
                              border_color=BRAND_PURPLE))
    flow.append(Spacer(1, 3 * mm))
    flow.append(_premium_card(s, "🎰 Lottery / Contest Tip", pack["lottery_tip"],
                              bg_color=colors.HexColor("#FFFBEB"),
                              border_color=BRAND_GOLD))
    return flow


def _mantras_section(s, driver: int, lang: str = "hinglish") -> List[Any]:
    """Personalized mantras + remedies (gemstone, yantra, daan)."""
    flow: List[Any] = []
    pack = _nr.mantras_pack(driver)
    planet = pack.get('planet', '')

    title = _T(lang,
        f"📿 MANTRAS & REMEDIES — {planet} Sadhana",
        f"📿 मंत्र और उपाय — {planet} साधना",
        f"📿 MANTRAS & REMEDIES — {planet} Sadhana")
    flow.append(Paragraph(title, s["page_title"]))
    flow.append(Spacer(1, 3 * mm))

    flow.append(_explain_card(s, lang,
        f"📖 Why these {planet} remedies?",
        f"📖 ये {planet} उपाय क्यों?",
        f"📖 Yeh {planet} remedies kyu?",
        f"Your driver number is ruled by <b>{planet}</b>. When this planet is strong, you experience clarity, "
        "energy, and luck. When weak or afflicted (by transits, dasha, or birth chart), you face obstacles, "
        "low mood, repeated failures. The 5 remedies below are the <b>classical Vedic toolkit</b> to strengthen "
        f"{planet}: <b>(1) Mantra</b> — sound vibration that resonates with the planet, "
        "<b>(2) Gemstone</b> — wearable lens that channels the planet's ray, "
        "<b>(3) Yantra</b> — geometric grid placed in your home/office that holds the energy, "
        "<b>(4) Daan</b> — donations that pacify the planet's negative side, "
        "<b>(5) Colour</b> — daily wear to align your aura. "
        "<b>Start with mantra + colour</b> (free, immediate). Then add gemstone (after consultation) and daan. "
        "40 days minimum to feel the shift.",
        f"आपके driver संख्या का स्वामी <b>{planet}</b> है। यह ग्रह बलवान होने पर स्पष्टता, ऊर्जा, भाग्य देता है। "
        "कमज़ोर या पीड़ित होने पर बाधाएँ, उदासी, बार-बार असफलता आती है। नीचे दिए 5 उपाय <b>शास्त्रीय वैदिक उपकरण</b> हैं "
        f"{planet} को बल देने के लिए: <b>(1) मंत्र</b> — ध्वनि कंपन, <b>(2) रत्न</b> — पहनने योग्य लेंस, "
        "<b>(3) यंत्र</b> — ज्यामितीय ग्रिड घर/ऑफ़िस में, <b>(4) दान</b> — ग्रह की नकारात्मक पक्ष शांत करता है, "
        "<b>(5) रंग</b> — आभा को संरेखित करने के लिए। <b>मंत्र + रंग से शुरू करें</b> (निःशुल्क, तुरंत)। "
        "फिर रत्न (परामर्श के बाद) और दान जोड़ें। बदलाव महसूस करने के लिए कम से कम 40 दिन।",
        f"Aapke driver number ka swami <b>{planet}</b> hai. Yeh planet strong hone par clarity, energy, luck deta hai. "
        "Weak ya afflicted hone par (transits, dasha, ya birth chart se) obstacles, low mood, baar-baar failures aate hain. "
        f"Neeche diye 5 remedies <b>classical Vedic toolkit</b> hain {planet} ko strong karne ke liye: "
        "<b>(1) Mantra</b> — sound vibration jo planet ke saath resonate karti hai, "
        "<b>(2) Gemstone</b> — wearable lens jo planet ki ray channel karta hai, "
        "<b>(3) Yantra</b> — geometric grid ghar/office me jo energy hold karta hai, "
        "<b>(4) Daan</b> — donations jo planet ka negative side shaant karte hain, "
        "<b>(5) Colour</b> — daily wear jo aura ko align karta hai. "
        "<b>Mantra + colour se shuru karein</b> (free, immediate). Phir gemstone (consultation ke baad) aur daan add karein. "
        "Shift mehsoos karne ke liye minimum 40 din.",
        bg="#FEF3C7", border="#B45309"))
    flow.append(Spacer(1, 5 * mm))

    flow.append(_premium_card(s, "🕉️ MANTRA (beej + complete)",
                              f"<b>{pack.get('mantra', '—')}</b><br/>"
                              f"<font color='#6B7280' size='9'>Count: {pack.get('count', '—')} | "
                              f"Best time: {pack.get('best_time', '—')}</font>",
                              bg_color=colors.HexColor("#FEF3C7"),
                              border_color=BRAND_GOLD))
    flow.append(Spacer(1, 3 * mm))
    flow.append(_premium_card(s, "💎 GEMSTONE (ratna)", pack.get("stone", "—"),
                              bg_color=colors.HexColor("#F0F9FF"),
                              border_color=colors.HexColor("#0369A1")))
    flow.append(Spacer(1, 3 * mm))
    flow.append(_premium_card(s, "🔯 YANTRA", pack.get("yantra", "—"),
                              bg_color=colors.HexColor("#F3E8FF"),
                              border_color=BRAND_PURPLE))
    flow.append(Spacer(1, 3 * mm))
    flow.append(_premium_card(s, "🪔 DAAN (Charity)", pack.get("daan", "—"),
                              bg_color=colors.HexColor("#FFFBEB"),
                              border_color=colors.HexColor("#B45309")))
    flow.append(Spacer(1, 3 * mm))
    flow.append(_premium_card(s, "👕 COLOUR FOCUS", pack.get("color_focus", "—"),
                              bg_color=colors.HexColor("#FDF2F8"),
                              border_color=colors.HexColor("#DB2777")))
    return flow


def _business_launch_section(s, driver: int, conductor: int, year: int = 2026,
                             lang: str = "hinglish") -> List[Any]:
    """Business launch calculator — best months, name, partners, direction."""
    flow: List[Any] = []
    # Recompute with proper conductor
    forecast = _nr.monthly_forecast_pack(driver, conductor, year)
    pack = _nr.business_launch_pack(driver, year)
    pack["best_launch_months"] = [
        {"month": m["month"], "verdict": m["verdict"]}
        for m in forecast["months"] if m["verdict"] in ("EXCELLENT", "GOOD")
    ][:6]

    title = _T(lang,
        f"🏢 BUSINESS LAUNCH CALCULATOR ({year})",
        f"🏢 व्यवसाय शुभारंभ कैलकुलेटर ({year})",
        f"🏢 BUSINESS LAUNCH CALCULATOR ({year})")
    flow.append(Paragraph(title, s["page_title"]))
    flow.append(Spacer(1, 3 * mm))

    flow.append(_explain_card(s, lang,
        "📖 Why timing & numerology matter for business",
        "📖 व्यवसाय में समय और अंकशास्त्र क्यों मायने रखते हैं",
        "📖 Business me timing aur numerology kyu matter karte hain",
        "Two startups with the same product, same capital, same team can have completely different fates — "
        "the difference is often <b>timing of launch + foundational numbers</b>. In Vedic tradition, the moment "
        "you register your company, sign the lease, or sell the first invoice locks in a 'birth chart' for the venture. "
        "If those moments align with your driver's friendly numbers and planet-friendly days, growth is fluid. "
        "If they clash, you experience constant cash-flow stress, partner disputes, and stagnation despite hard work. "
        "<b>This page gives you a complete launch playbook</b>: which months are green-light, which weekday to sign papers, "
        "what direction your office should face, what numbers your company name should reduce to, and which partner "
        "numbers will multiply your success vs drain it. Use this <b>before</b> launching, not after.",
        "एक ही उत्पाद, एक ही पूँजी, एक ही टीम वाले दो स्टार्टअप का भाग्य बिल्कुल अलग हो सकता है — फ़र्क़ अक्सर "
        "<b>लॉन्च के समय और मूलभूत अंकों</b> में होता है। वैदिक परंपरा में जिस क्षण आप कंपनी रजिस्टर करते हैं, "
        "लीज़ साइन करते हैं, या पहला इनवॉइस बेचते हैं, वह क्षण उद्यम का 'जन्म-कुंडली' लॉक कर देता है। "
        "यदि वे क्षण आपके driver के मित्र अंकों और ग्रह-अनुकूल दिनों से मेल खाते हैं, तो विकास सहज होता है। "
        "अन्यथा निरंतर नकदी तनाव, साझेदार विवाद, और मेहनत के बावजूद ठहराव। "
        "<b>यह पृष्ठ संपूर्ण लॉन्च प्लेबुक देता है</b>: कौन-से महीने हरी झंडी, किस दिन कागज़ साइन करें, "
        "ऑफ़िस की दिशा, कंपनी नाम किस अंक पर रिड्यूस हो, और कौन-से साझेदार अंक सफलता गुणा करेंगे। "
        "इसका उपयोग लॉन्च से <b>पहले</b> करें, बाद में नहीं।",
        "Same product, same capital, same team waale do startups ka bhagya bilkul alag ho sakta hai — fark aksar "
        "<b>launch ki timing + foundational numbers</b> me hota hai. Vedic tradition me jis moment aap company register "
        "karte ho, lease sign karte ho, ya pehla invoice bechte ho — wo moment venture ki 'birth chart' lock kar deta hai. "
        "Agar wo moments aapke driver ke friendly numbers aur planet-friendly days se align hain, growth fluid hoti hai. "
        "Agar clash hai, constant cash-flow stress, partner disputes, mehnat ke bawajood stagnation milti hai. "
        "<b>Yeh page complete launch playbook deta hai</b>: kaun se months green-light hain, kis weekday papers sign karne hain, "
        "office kis direction me face kare, company name kis number pe reduce ho, aur kaun se partner numbers success "
        "multiply karenge vs drain karenge. Iska use launch se <b>pehle</b> karein, baad me nahi.",
        bg="#F0F9FF", border="#0369A1"))
    flow.append(Spacer(1, 5 * mm))

    rows = [
        [Paragraph("<b>📅 Best launch months</b>", s["body_mid"]),
         Paragraph(", ".join(f"<b>{m['month']}</b> ({m['verdict']})"
                            for m in pack["best_launch_months"]) or "—", s["body"])],
        [Paragraph("<b>🗓️ Best registration day</b>", s["body_mid"]),
         Paragraph(f"<b>{pack['registration_day']}</b>", s["body"])],
        [Paragraph("<b>🧭 Office direction</b>", s["body_mid"]),
         Paragraph(f"Sit facing <b>{pack['office_direction']}</b>", s["body"])],
        [Paragraph("<b>🔢 Best company-name numbers</b>", s["body_mid"]),
         Paragraph(", ".join(str(n) for n in pack["best_company_name_numbers"]), s["body"])],
        [Paragraph("<b>🤝 Best partner numbers</b>", s["body_mid"]),
         Paragraph(f"<font color='#15803D'>{', '.join(str(n) for n in pack['best_partner_numbers'])}</font>", s["body"])],
        [Paragraph("<b>⛔ Avoid partner numbers</b>", s["body_mid"]),
         Paragraph(f"<font color='#B91C1C'>{', '.join(str(n) for n in pack['avoid_partner_numbers']) or '—'}</font>", s["body"])],
    ]
    t = Table(rows, colWidths=[55 * mm, 125 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, -1), colors.HexColor("#F0F9FF")),
        ("BOX",            (0, 0), (-1, -1), 1.0, colors.HexColor("#0369A1")),
        ("INNERGRID",      (0, 0), (-1, -1), 0.3, colors.HexColor("#7DD3FC")),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 5 * mm))

    flow.append(_premium_card(s, "💼 NAME TIP", pack["name_tip"],
                              bg_color=colors.HexColor("#FFFBEB"),
                              border_color=BRAND_GOLD))
    flow.append(Spacer(1, 3 * mm))
    flow.append(_premium_card(s, "🎨 LOGO TIP", pack["logo_tip"],
                              bg_color=colors.HexColor("#F3E8FF"),
                              border_color=BRAND_PURPLE))
    flow.append(Spacer(1, 3 * mm))
    flow.append(_premium_card(s, "🧾 FIRST INVOICE TIP", pack["first_invoice_tip"],
                              bg_color=colors.HexColor("#DCFCE7"),
                              border_color=colors.HexColor("#15803D")))
    return flow


def _celebrity_match_section(s, driver: int, lang: str = "hinglish") -> List[Any]:
    """Famous people with same driver number."""
    flow: List[Any] = []
    matches = _nr.celebrity_match_pack(driver)

    title = _T(lang,
        "🌟 CELEBRITY MATCH — Famous People Like You",
        "🌟 सेलिब्रिटी मैच — आपके जैसे प्रसिद्ध व्यक्ति",
        "🌟 CELEBRITY MATCH — Aapke Jaise Famous Log")
    flow.append(Paragraph(title, s["page_title"]))
    flow.append(Spacer(1, 3 * mm))

    flow.append(_explain_card(s, lang,
        "📖 Why look at celebrities with your driver number?",
        "📖 अपने driver अंक वाले सेलिब्रिटीज़ क्यों देखें?",
        "📖 Apne driver number waale celebrities kyu dekhein?",
        f"You share your driver number <b>{driver}</b> with these famous personalities. That doesn't mean your "
        "life will copy theirs — but it does mean your <b>core wiring is similar</b>: the same instinctive strengths, "
        "the same blind spots, the same kind of opportunities that life keeps placing in front of you. Studying their "
        "journey is like reading a manual written by someone with your operating system. Notice <b>three things</b>: "
        "(1) what natural talent they amplified instead of fighting, (2) what setback nearly broke them and how they "
        "responded, (3) what ethical/spiritual practice kept them grounded at the top. You don't need to become them — "
        "you need to recognise the <b>pattern of your own number</b> so you stop apologising for who you are and start "
        "leveraging it. <b>Pick one celebrity</b> from this list, read their biography this month, and journal what "
        "applies to you.",
        f"आप अपना driver अंक <b>{driver}</b> इन प्रसिद्ध व्यक्तियों के साथ साझा करते हैं। इसका अर्थ नहीं कि आपका जीवन "
        "उनकी नकल करेगा — पर इसका अर्थ है कि आपकी <b>मूल बनावट समान है</b>: वही सहज शक्तियाँ, वही अंध-बिंदु, "
        "वही प्रकार के अवसर जो जीवन आपके सामने रखता रहता है। उनकी यात्रा पढ़ना किसी ऐसे व्यक्ति की लिखी मैनुअल पढ़ने जैसा है "
        "जिसका 'ऑपरेटिंग सिस्टम' आपके जैसा है। <b>तीन बातें</b> देखें: (1) किस सहज प्रतिभा को बढ़ाया, उससे लड़े नहीं, "
        "(2) किस झटके ने तोड़ने को था और प्रतिक्रिया कैसी रही, (3) कौन-सी नैतिक/आध्यात्मिक साधना ने शिखर पर भी जमीन से जोड़ रखा। "
        "उनके जैसा बनने की ज़रूरत नहीं — अपने अंक का <b>पैटर्न पहचानने</b> की ज़रूरत है। "
        "<b>एक सेलिब्रिटी चुनें</b>, इस महीने उनकी जीवनी पढ़ें, और जर्नल में लिखें क्या आप पर लागू होता है।",
        f"Aap apna driver number <b>{driver}</b> in famous logon ke saath share karte ho. Iska matlab yeh nahi ki aapki "
        "life unki copy hogi — lekin iska matlab hai aapki <b>core wiring same hai</b>: wahi natural strengths, wahi "
        "blind spots, wahi tarah ke opportunities jo life baar-baar saamne rakhti hai. Inki journey padhna aise hai "
        "jaise koi aapke 'operating system' wala manual likha ho. <b>Teen cheezein dekhein</b>: (1) kis natural talent "
        "ko amplify kiya, usse lade nahi, (2) kis setback ne tod ne ki kosish ki aur response kya tha, (3) kaun si "
        "ethical/spiritual practice ne shikhar par bhi grounded rakha. Inke jaisa banne ki zarurat nahi — apne number "
        "ka <b>pattern recognise</b> karne ki zarurat hai taaki aap apne aap ke liye apologise karna band karein aur "
        "leverage karna shuru karein. <b>Ek celebrity chunein</b>, iss mahine unki biography padhein, journal me likhein "
        "kya aap par apply hota hai.",
        bg="#FFFBEB", border="#B45309"))
    flow.append(Spacer(1, 5 * mm))

    if not matches:
        flow.append(Paragraph("No celebrity matches available for this driver.", s["body"]))
        return flow

    header = ParagraphStyle("cm_h", fontName="Helvetica-Bold", fontSize=10,
                            textColor=colors.white, leading=13, alignment=TA_CENTER)
    rows = [[Paragraph("<b>Name</b>", header),
             Paragraph("<b>Born</b>", header),
             Paragraph("<b>Aap Kya Seekh Sakte Ho</b>", header)]]
    for m in matches:
        rows.append([
            Paragraph(f"<b>{m['name']}</b>", s["body_mid"]),
            Paragraph(m["born"], s["body"]),
            Paragraph(m["lesson"], s["small"]),
        ])
    t = Table(rows, colWidths=[42 * mm, 30 * mm, 108 * mm])
    style_rows = [
        ("BACKGROUND",     (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
        ("BOX",            (0, 0), (-1, -1), 0.8, BRAND_PURPLE),
        ("INNERGRID",      (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#FFFBEB"), colors.HexColor("#FEF3C7")]),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
    ]
    t.setStyle(TableStyle(style_rows))
    flow.append(t)
    flow.append(Spacer(1, 5 * mm))
    flow.append(Paragraph(
        "<i>Lesson: Aap inn celebrities se 'pattern' seekho — exact path nahi. "
        "Same driver hone se aapki natural strengths similar hain.</i>",
        s["small"]))
    return flow


def _why_impact_action_block(s, kind: str, reduced: int) -> List[Any]:
    """Append Why+Impact+Action narrative for a number — used inside each
    mobile/vehicle/house deep-analysis page."""
    flow: List[Any] = []
    pack = _nr.why_impact_action_for_number(reduced, kind)
    if not pack or not pack.get("why"):
        return flow

    flow.append(Spacer(1, 3 * mm))
    flow.append(Paragraph(
        f"<b>📖 Aapke {kind.title()} Number Ka Story</b> "
        f"(Why · Impact · Action format)",
        s["h3"]))

    rows = [
        [Paragraph(f"<b>WHY</b><br/><font size='8' color='#6B7280'>(yeh kyun important hai)</font>",
                   s["body_mid"]),
         Paragraph(pack.get("why", "—"), s["body"])],
        [Paragraph(f"<b>IMPACT</b><br/><font size='8' color='#6B7280'>(aapki life me kya hoga)</font>",
                   s["body_mid"]),
         Paragraph(pack.get("impact", "—"), s["body"])],
        [Paragraph(f"<b>ACTION</b><br/><font size='8' color='#6B7280'>(aap kya karein)</font>",
                   s["body_mid"]),
         Paragraph(pack.get("action", "—"), s["body"])],
    ]
    t = Table(rows, colWidths=[34 * mm, 146 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (0, -1), colors.HexColor("#F3E8FF")),
        ("BACKGROUND",   (1, 0), (1, -1), colors.HexColor("#FAFAFA")),
        ("BOX",          (0, 0), (-1, -1), 0.5, BRAND_PURPLE),
        ("INNERGRID",    (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 3 * mm))
    return flow


# ─── Public entry ────────────────────────────────────────────────────

def render_part2_pdf(*,
                     name: str,
                     dob: str,
                     mobile: Optional[str],
                     vehicle: Optional[str],
                     house: Optional[str],
                     lang: str = "hinglish") -> bytes:
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

    s = _styles(lang)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=18 * mm, bottomMargin=20 * mm,
                            title=f"Life Mastery Report — {name}",
                            author="Cosmic Lens")
    story: List[Any] = []
    # Page 1 — Cover
    story += _cover(s, name, dob)
    story.append(PageBreak())

    # Page 2 — ⭐ LIFE BLUEPRINT (premium summary card — instant ₹1499 feel)
    story += _life_summary_block(s, name, driver, conductor)
    story.append(PageBreak())

    # Page 3 — 🌟 Aap Kaun Ho (3-paragraph identity story + strengths/challenges)
    story += _life_essence_section(s, driver)
    story.append(PageBreak())

    # Page 4 — 💼 Career Blueprint (Why + Mistake + Timing + Money pattern)
    story += _career_blueprint_section(s, driver)
    story.append(PageBreak())

    # Page 5 — 💕 Love Pattern (Style + Triggers + Ideal Partner)
    story += _love_pattern_section(s, driver)
    story.append(PageBreak())

    # Page 6 — 🕉️ Health & Dharma (Body + Spirit)
    story += _wealth_health_spirit_section(s, driver)
    story.append(PageBreak())

    # Page 7 — ⚠️ Risk Alerts + 🌟 Golden Periods + Executive Summary
    story += _risk_alerts_section(s, driver)
    story.append(PageBreak())

    # ─── Part 2 EXTRAS — Lucky Colours + Day-wise Dress + Practical numbers ───
    # Page 8 — 🎨 Lucky Colours (vehicle + business + gemstone tone)
    story += _lucky_colours_section(s, driver, vehicle=vehicle)
    story.append(PageBreak())

    # Page 9 — 👕 Day-wise Dress Colour table (Mon-Sun planetary)
    story += _day_dress_section(s, driver)
    story.append(PageBreak())

    # ─── Premium Tier B sections (₹1499 deep value) ────────────────────
    # Page 10 — 🗓️ 12-Month Forecast (current year)
    from datetime import datetime
    _yr = datetime.now().year
    story += _monthly_forecast_section(s, driver, conductor, year=_yr, lang=lang)
    story.append(PageBreak())

    # Page 11 — 💑 Deep Compatibility (Love/Marriage/Business per number)
    story += _deep_compat_section(s, driver, lang=lang)
    story.append(PageBreak())

    # Page 12 — 🔢 Lucky Numbers (single, double, dates, PIN, lottery)
    story += _lucky_numbers_section(s, driver, lang=lang)
    story.append(PageBreak())

    # Page 13 — 📿 Mantras + Remedies (mantra, gemstone, yantra, daan)
    story += _mantras_section(s, driver, lang=lang)
    story.append(PageBreak())

    # Page 14 — 🏢 Business Launch Calculator
    story += _business_launch_section(s, driver, conductor, year=_yr, lang=lang)
    story.append(PageBreak())

    # Page 15 — 🌟 Celebrity Match (famous people same driver)
    story += _celebrity_match_section(s, driver, lang=lang)
    story.append(PageBreak())

    # Page 16 — Driver/Conductor technical intro
    story += _driver_conductor_intro(s, name, dob, driver, conductor)
    story.append(PageBreak())

    # Page 11-13 — Mobile / Vehicle / House deep analysis (with Why·Impact·Action)
    if mobile:
        story += _number_analysis_block(s, mobile, "mobile", driver, conductor)
        story.append(PageBreak())
    if vehicle:
        story += _number_analysis_block(s, vehicle, "vehicle", driver, conductor)
        story.append(PageBreak())
    if house:
        story += _number_analysis_block(s, house, "house", driver, conductor)
        story.append(PageBreak())

    # Page 14 — Number Compatibility Matrix
    story += _compatibility_matrix_section(s, driver)
    story.append(PageBreak())

    # Page 15 — Letter-by-letter table
    story += _letter_table_section(s, name)
    story.append(PageBreak())

    # Page 16 — Pythagorean vs Chaldean summary
    story += _name_numerology_section(s, name)
    story.append(PageBreak())

    # Page 17 — Name correction
    story += _name_correction_section(s, name, driver, conductor)
    story.append(PageBreak())

    # Page 18 — Signature & branding
    story += _signature_section(s, name, driver)
    story.append(PageBreak())

    # Page 19 — 90-day implementation plan
    story += _timeline_section(s)
    story += _disclaimer(s)

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

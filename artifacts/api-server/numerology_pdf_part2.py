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
                           driver: int, conductor: int,
                           lang: str = "hinglish") -> List[Any]:
    """Render a deep number-analysis section: digit-by-digit, last-4, alerts, alternatives."""
    flow: List[Any] = []
    out = _ta.analyze_number_string(value, kind=kind, driver=driver, conductor=conductor)
    if not out.get("ok"):
        return flow

    titles_en = {"mobile": "Mobile Number — Deep Analysis",
                 "vehicle": "Vehicle Number — Deep Analysis",
                 "house":   "House Number — Deep Analysis"}
    titles_hi = {"mobile": "मोबाइल नंबर — गहन विश्लेषण",
                 "vehicle": "वाहन नंबर — गहन विश्लेषण",
                 "house":   "घर नंबर — गहन विश्लेषण"}
    titles_hg = {"mobile": "Mobile Number — Deep Analysis",
                 "vehicle": "Vehicle Number — Deep Analysis",
                 "house":   "House Number — Deep Analysis"}
    flow.append(Paragraph(_T(lang,
        titles_en.get(kind, "Number Analysis"),
        titles_hi.get(kind, "नंबर विश्लेषण"),
        titles_hg.get(kind, "Number Analysis")), s["h2"]))

    # Per-kind explain card
    why_en = {
        "mobile": ("Your mobile number is the digit-string you carry every minute — every "
                   "call, message and notification flows through its vibration. Numerology "
                   "treats the <b>last 4 digits sum</b> (Cheiro's rule), the <b>full digit "
                   "sum</b> reduced, and the <b>repeating-digit patterns</b> as three "
                   "independent layers. The card below decodes each layer and tells you "
                   "if the number supports your Driver+Conductor or fights it."),
        "vehicle": ("Your vehicle is your daily moving aura — the registration number's "
                    "vibration influences accident-proneness, fuel efficiency, smoothness "
                    "of journeys, and resale luck. The full registration is reduced and "
                    "matched against your Driver/Conductor. Verdict + safer alternatives "
                    "(if needed) follow."),
        "house": ("Your house/flat number is the energy gateway you cross every day. It "
                  "decides the home's <b>peace, prosperity and family health quotient</b>. "
                  "Hard to change, but knowing the vibration helps with remedies — pots, "
                  "colours, name-plate adjustments."),
    }
    why_hi = {
        "mobile": ("आपका मोबाइल नंबर वो अंक-शृंखला है जिसे आप हर पल लिये चलते हैं — हर "
                   "कॉल, संदेश और सूचना उसी कंपन से बहती है। अंक-शास्त्र इसे तीन परतों "
                   "में देखता है: <b>अंतिम 4 अंकों का योग</b> (चीरो नियम), <b>पूर्ण योग</b> "
                   "का संकुचन, और <b>दोहराव-पैटर्न</b>। नीचे का कार्ड हर परत को खोलकर "
                   "बताता है कि नंबर आपके Driver+Conductor का साथ देता है या विरोध।"),
        "vehicle": ("आपका वाहन एक चलती-फिरती आभा है — पंजीकरण-संख्या का कंपन दुर्घटना-"
                    "प्रवृत्ति, ईंधन-दक्षता, यात्रा की सहजता और पुनर्बिक्री-भाग्य पर "
                    "प्रभाव डालता है। पूर्ण नंबर को संकुचित कर आपके Driver/Conductor "
                    "से मिलाया गया है — verdict और सुरक्षित विकल्प नीचे।"),
        "house": ("आपका मकान/फ्लैट नंबर वो ऊर्जा-द्वार है जिसे आप रोज़ लांघते हैं। यह घर "
                  "की <b>शांति, समृद्धि और पारिवारिक स्वास्थ्य</b> तय करता है। बदलना "
                  "कठिन है, पर कंपन जानकर उपाय — कलश, रंग, नेम-प्लेट — किये जा सकते हैं।"),
    }
    why_hg = {
        "mobile": ("Aapka mobile number wo digit-string hai jo aap har minute carry karte "
                   "ho — har call, message, notification usi vibration se flow hota hai. "
                   "Numerology iss number ko 3 independent layers me dekhti hai: <b>last "
                   "4 digits ka sum</b> (Cheiro rule), <b>full sum reduced</b>, aur "
                   "<b>repeating-digit patterns</b>. Neeche card har layer decode karta "
                   "hai aur batata hai number aapke Driver+Conductor ko support karta "
                   "hai ya fight."),
        "vehicle": ("Aapka vehicle ek daily moving aura hai — registration number ka "
                    "vibration accident-prone-ness, fuel efficiency, smoothness of "
                    "journey, aur resale luck par effect daalta hai. Full number reduce "
                    "karke aapke Driver/Conductor se match kiya — verdict + safer "
                    "alternatives (agar zarurat hai) neeche."),
        "house": ("Aapka house/flat number wo energy gateway hai jise aap roz cross karte "
                  "ho. Yeh ghar ki <b>peace, prosperity aur family health</b> tay karta "
                  "hai. Badalna mushkil, par vibration jaan ke remedies — pots, colours, "
                  "name-plate adjustments — kiye ja sakte hain."),
    }
    flow.append(_explain_card(s, lang,
        f"📖 Why does your {kind} number matter?",
        f"📖 आपका {kind} नंबर क्यों मायने रखता है?",
        f"📖 Aapka {kind} number kyun matter karta hai?",
        why_en.get(kind, ""), why_hi.get(kind, ""), why_hg.get(kind, ""),
        bg="#F0F9FF", border="#0369A1"))
    flow.append(Spacer(1, 4 * mm))

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


def _driver_conductor_intro(s, name: str, dob: str, driver: int, conductor: int,
                            lang: str = "hinglish") -> List[Any]:
    """Page 2 — explain user's Driver + Conductor with planets."""
    flow: List[Any] = []
    flow.append(_section_title(s, _T(lang,
        "Your Number Signature",
        "आपका अंक-हस्ताक्षर",
        "Aapka Number Signature")))
    flow.append(Paragraph(_T(lang,
        f"Every person has 2 most important numbers — <b>Driver</b> and <b>Conductor</b>. "
        f"They are derived from your birth-date <b>{dob}</b>, and every choice you make "
        "— mobile, vehicle, house, name — should be evaluated against them.",
        f"हर व्यक्ति के 2 सबसे महत्वपूर्ण नंबर होते हैं — <b>Driver</b> और <b>Conductor</b>। "
        f"ये आपकी जन्म-तिथि <b>{dob}</b> से निकले हैं, और आपका हर चुनाव — मोबाइल, "
        "वाहन, घर, नाम — इन्हीं के अनुसार जांचा जाना चाहिए।",
        f"Har person ke 2 sabse important numbers hote hain — <b>Driver</b> aur "
        f"<b>Conductor</b>. Ye {dob} ki janma-tithi se nikle hain aur aapki har "
        "choice — mobile, vehicle, ghar, naam — inhi ke hisaab se evaluate ki jaani chahiye."),
        s["body"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_explain_card(s, lang,
        "📖 Driver vs Conductor — what's the difference?",
        "📖 Driver बनाम Conductor — अंतर क्या है?",
        "📖 Driver vs Conductor — fark kya hai?",
        "<b>Driver (Mulank)</b> = your birth-DAY only, reduced to 1-9. It rules your "
        "<b>day-to-day personality</b>, instant reactions, what people see in the first "
        "meeting. <b>Conductor (Bhagyank)</b> = the FULL birth-date sum reduced. It "
        "rules your <b>destiny, long-term fortune, marriage and big-money flow</b>. "
        "When both are friendly with each other you have a smooth life; when they "
        "clash, you feel a constant inner tug-of-war. The table below shows yours.",
        "<b>Driver (मूलांक)</b> = केवल आपका जन्म-दिवस, 1-9 तक संकुचित। यह आपकी "
        "<b>दैनिक व्यक्तित्व</b>, तत्काल प्रतिक्रिया, और पहली मुलाकात की छवि तय करता "
        "है। <b>Conductor (भाग्यांक)</b> = पूर्ण जन्म-तिथि का योग संकुचित। यह आपकी "
        "<b>नियति, दीर्घकालिक भाग्य, विवाह और बड़ा धन</b> शासित करता है। जब दोनों "
        "मित्र हों तो जीवन सहज; टकराव हो तो भीतर रस्साकशी अनुभव होती है। नीचे की "
        "तालिका में आपके दोनों दिखाये गये हैं।",
        "<b>Driver (Mulank)</b> = sirf aapka birth-DAY, 1-9 reduce karke. Yeh aapki "
        "<b>day-to-day personality</b>, instant reactions, aur first meeting impression "
        "rule karta hai. <b>Conductor (Bhagyank)</b> = poori birth-date ka sum "
        "reduced. Yeh aapki <b>destiny, long-term fortune, shaadi aur big money</b> "
        "rule karta hai. Jab dono friendly hote hain to life smooth; jab clash karte "
        "hain to ek constant inner tug-of-war feel hota hai. Neeche table me aapke dono.",
        bg="#FAF5FF", border="#5B21B6"))
    flow.append(Spacer(1, 4 * mm))

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


def _compatibility_matrix_section(s, driver: int, lang: str = "hinglish") -> List[Any]:
    """Show user's driver vs all 1-9 compatibility."""
    flow: List[Any] = []
    flow.append(_section_title(s, _T(lang,
        "Number Compatibility Matrix",
        "अंक-संगति तालिका",
        "Number Compatibility Matrix")))
    flow.append(Paragraph(_T(lang,
        f"How your Driver Number <b>{driver}</b> ({_planet_for(driver)}) interacts with "
        "all the other numbers (1-9). Use this knowledge when selecting a partner, "
        "choosing a business associate, or buying a house/mobile/vehicle number.",
        f"आपका Driver नंबर <b>{driver}</b> ({_planet_for(driver)}) बाकी सभी अंकों "
        "(1-9) से कैसे क्रिया करता है। इस ज्ञान का उपयोग करें — साथी चुनते समय, "
        "व्यावसायिक भागीदार चुनते समय, या घर/मोबाइल/वाहन का नंबर लेते समय।",
        f"Aapka Driver Number <b>{driver}</b> ({_planet_for(driver)}) baaki sab numbers "
        "(1-9) ke saath kaisa interact karta hai. Ye knowledge use kare — partner "
        "select karte waqt, business associate chunte waqt, ghar/mobile/vehicle ka "
        "number lete waqt."), s["body_mid"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_explain_card(s, lang,
        "📖 How to read this 1-9 matrix",
        "📖 इस 1-9 तालिका को कैसे पढ़ें",
        "📖 Iss 1-9 matrix ko kaise read karein",
        "Each row = one number from 1 to 9, with its planet and a relationship label: "
        "<b>TWIN</b> = same number, mirror energy. <b>FRIEND</b> = planets are mutually "
        "supportive — natural harmony. <b>NEUTRAL</b> = neither help nor harm. "
        "<b>ENEMY</b> = planetary clash — extra effort needed. The score (0-100) is a "
        "compatibility index. Use it as a <b>quick filter</b>, not a verdict — even "
        "ENEMY pairings can work with conscious adjustment.",
        "हर पंक्ति = 1 से 9 तक का एक अंक, उसका ग्रह और संबंध-लेबल: <b>TWIN</b> = "
        "समान संख्या, दर्पण-ऊर्जा। <b>FRIEND</b> = ग्रह परस्पर सहायक — स्वाभाविक "
        "सामंजस्य। <b>NEUTRAL</b> = न मदद न हानि। <b>ENEMY</b> = ग्रह-टकराव — अधिक "
        "प्रयास आवश्यक। 0-100 स्कोर एक सामंजस्य-सूचकांक है। इसे <b>शीघ्र फ़िल्टर</b> "
        "मानिये, अंतिम निर्णय नहीं — सजग समायोजन से ENEMY जोड़ी भी चल सकती है।",
        "Har row = 1 se 9 tak ka ek number, uska planet aur relationship label: "
        "<b>TWIN</b> = same number, mirror energy. <b>FRIEND</b> = planets mutually "
        "supportive — natural harmony. <b>NEUTRAL</b> = neither help nor harm. "
        "<b>ENEMY</b> = planetary clash — extra effort needed. Score (0-100) ek "
        "compatibility index hai. Isse <b>quick filter</b> ki tarah use karein, final "
        "verdict nahi — conscious adjustment se ENEMY pair bhi chal sakti hai.",
        bg="#FAF5FF", border="#5B21B6"))
    flow.append(Spacer(1, 4 * mm))

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


def _letter_table_section(s, name: str, lang: str = "hinglish") -> List[Any]:
    """Page showing per-letter numerology values."""
    flow: List[Any] = []
    flow.append(_section_title(s, _T(lang,
        "Name — Letter by Letter",
        "नाम — अक्षर दर अक्षर",
        "Name — Letter by Letter")))
    flow.append(Paragraph(_T(lang,
        f"<b>{name}</b> — Pythagorean and Chaldean value of every letter. "
        "Vowels (A/E/I/O/U) form the Soul Urge (your inner desire); consonants "
        "form the Personality (what the world sees).",
        f"<b>{name}</b> — हर अक्षर का Pythagorean और Chaldean मान। स्वर "
        "(A/E/I/O/U) Soul Urge बनाते हैं (आपकी भीतर की इच्छा), व्यंजन Personality "
        "(जो दुनिया देखती है)।",
        f"<b>{name}</b> — har akshar ki Pythagorean aur Chaldean value. "
        "Vowels (A/E/I/O/U) Soul Urge banate hain (aapki inner desire), "
        "consonants Personality (duniya jo dekhti hai)."), s["body_mid"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_explain_card(s, lang,
        "📖 Why does each letter carry a number?",
        "📖 हर अक्षर एक अंक क्यों रखता है?",
        "📖 Har letter ek number kyun rakhta hai?",
        "Letters are sound-vibrations. Sanskrit, Hebrew and Greek alphabets all "
        "assign numerical values to letters because <b>each sound resonates at a "
        "specific frequency</b>. Pythagoras formalised the modern 1-9 system "
        "(A=1, J=1, S=1...). Cheiro restored the older Chaldean sound-system "
        "(1-8 only; 9 is sacred and unwritten). Every name therefore has an "
        "<b>Expression number</b> (full sum), a <b>Soul Urge</b> (vowels only) "
        "and a <b>Personality</b> (consonants only). The table below decodes yours.",
        "अक्षर ध्वनि-कंपन हैं। संस्कृत, हिब्रू और ग्रीक — सभी अंकीय मान देते हैं "
        "क्योंकि <b>प्रत्येक ध्वनि एक विशिष्ट आवृत्ति पर अनुनादित होती है</b>। "
        "पाइथागोरस ने आधुनिक 1-9 प्रणाली बनायी (A=1, J=1, S=1...)। चीरो ने प्राचीन "
        "चाल्डियन ध्वनि-प्रणाली पुनर्जीवित की (केवल 1-8; 9 सम्माननीय और अलिखित)। "
        "हर नाम का अतः एक <b>Expression अंक</b> (पूर्ण योग), एक <b>Soul Urge</b> "
        "(केवल स्वर) और एक <b>Personality</b> (केवल व्यंजन) होता है। नीचे की "
        "तालिका आपके सब डिकोड करती है।",
        "Letters sound-vibrations hain. Sanskrit, Hebrew aur Greek — sab numerical "
        "values dete hain kyunki <b>har sound ek specific frequency par resonate "
        "karta hai</b>. Pythagoras ne modern 1-9 system formalise kiya (A=1, J=1, "
        "S=1...). Cheiro ne ancient Chaldean sound-system revive kiya (sirf 1-8; "
        "9 sacred aur unwritten). Har naam ka isliye ek <b>Expression number</b> "
        "(full sum), ek <b>Soul Urge</b> (sirf vowels) aur ek <b>Personality</b> "
        "(sirf consonants) hota hai. Neeche table aapke sab decode karta hai.",
        bg="#FAF5FF", border="#5B21B6"))
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


def _signature_section(s, name: str, driver: int, lang: str = "hinglish") -> List[Any]:
    """Initial-letter analysis + signature recommendations."""
    flow: List[Any] = []
    flow.append(_section_title(s, _T(lang,
        "Signature & Branding Recommendations",
        "हस्ताक्षर और ब्रांडिंग सुझाव",
        "Signature & Branding Recommendations")))

    sig = _ta.signature_advice(name, driver)
    if not sig.get("ok"):
        return flow

    flow.append(_explain_card(s, lang,
        "📖 Why does your signature shape your success?",
        "📖 हस्ताक्षर सफलता को क्यों आकार देता है?",
        "📖 Signature aapki success ko kaise shape karta hai?",
        "Your signature is the most-repeated motion of your life — every cheque, "
        "contract, document. Graphologists and numerologists agree that a signature "
        "is a <b>frozen affirmation of your subconscious self-image</b>. The first "
        "letter, slope, underline and dot placement each radiate a frequency. A "
        "Driver-aligned signature can <b>open income channels and remove invisible "
        "blocks</b> in months. The card below gives the rules tuned to your number.",
        "हस्ताक्षर आपके जीवन की सबसे अधिक दोहरायी जाने वाली क्रिया है — हर चेक, "
        "अनुबंध, दस्तावेज़। ग्राफोलॉजिस्ट और अंक-शास्त्री सहमत हैं कि हस्ताक्षर एक "
        "<b>अवचेतन आत्म-छवि की जमी हुई पुष्टि</b> है। पहला अक्षर, ढलान, अंडरलाइन "
        "और बिंदु की स्थिति — सब आवृत्तियाँ विकीर्ण करते हैं। Driver-संरेखित "
        "हस्ताक्षर महीनों में <b>आय-स्रोत खोल सकता है और अदृश्य अवरोध हटा सकता है</b>। "
        "नीचे आपके अंक के अनुसार नियम।",
        "Aapka signature jeevan ki sabse zyada repeat hone wali motion hai — har "
        "cheque, contract, document. Graphologists aur numerologists sahmat hain ki "
        "signature ek <b>subconscious self-image ki frozen affirmation</b> hai. "
        "First letter, slope, underline aur dot placement — sab frequencies radiate "
        "karte hain. Driver-aligned signature mahino me <b>income channels khol "
        "sakta hai aur invisible blocks hata sakta hai</b>. Neeche aapke number ke "
        "tuned rules.",
        bg="#F0FDF4", border="#15803D"))
    flow.append(Spacer(1, 4 * mm))

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


def _timeline_section(s, lang: str = "hinglish") -> List[Any]:
    """30-day implementation timeline."""
    flow: List[Any] = []
    flow.append(_section_title(s, _T(lang,
        "Your 90-Day Implementation Plan",
        "आपकी 90-दिवसीय कार्यान्वयन योजना",
        "Aapka 90-Day Implementation Plan")))
    flow.append(Paragraph(_T(lang,
        "Numerology corrections never happen overnight — a slow rollout is essential. "
        "Follow this schedule:",
        "अंक-शास्त्र के सुधार कभी रातों-रात नहीं होते — धीरे-धीरे लागू करना आवश्यक "
        "है। यह अनुसूची अपनाइये:",
        "Numerology corrections kabhi raat ko nahi badalte — slow rollout zaruri hai. "
        "Yeh schedule follow kare:"), s["body_mid"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_explain_card(s, lang,
        "📖 Why a 90-day rollout instead of 'change everything today'?",
        "📖 90-दिन की योजना क्यों, सब आज ही क्यों नहीं?",
        "📖 90-din ka rollout kyun, sab aaj hi kyun nahi?",
        "When you change too many vibrations at once — name spelling + mobile + "
        "vehicle + signature + colours — your subconscious goes into <b>identity "
        "shock</b>. Old patterns clash with new ones, you feel anxious, and the "
        "energy fails to settle. A staged 90-day rollout lets each change "
        "<b>integrate before the next one is layered on</b>. Phase 1 = mindset & "
        "easy wins; Phase 2 = practical (mobile, signature); Phase 3 = identity "
        "(name, brand). This sequence is the difference between a stable upgrade "
        "and a chaotic restart.",
        "जब आप एक साथ बहुत-सी कंपन-तरंगें बदलते हैं — नाम-वर्तनी + मोबाइल + वाहन "
        "+ हस्ताक्षर + रंग — तो अवचेतन <b>पहचान-धक्के</b> में चला जाता है। पुराने "
        "पैटर्न नये से टकराते हैं, बेचैनी होती है, ऊर्जा स्थिर नहीं हो पाती। 90-दिन "
        "की चरणबद्ध योजना हर बदलाव को <b>अगले से पहले एकीकृत होने का समय</b> देती "
        "है। फेज़ 1 = सोच और आसान जीतें; फेज़ 2 = व्यवहारिक (मोबाइल, हस्ताक्षर); "
        "फेज़ 3 = पहचान (नाम, ब्रांड)। यह क्रम स्थिर उन्नयन और अराजक पुनः-शुरुआत "
        "के बीच का अंतर है।",
        "Jab aap ek saath bahut saari vibrations badalte ho — naam-spelling + "
        "mobile + vehicle + signature + colours — to subconscious <b>identity "
        "shock</b> me chala jaata hai. Old patterns naye se clash karte hain, "
        "anxiety hoti hai, energy settle nahi hoti. 90-din ka staged rollout har "
        "change ko <b>agle se pehle integrate hone ka time</b> deta hai. Phase 1 = "
        "mindset & easy wins; Phase 2 = practical (mobile, signature); Phase 3 = "
        "identity (name, brand). Yeh sequence stable upgrade aur chaotic restart "
        "ka difference banata hai.",
        bg="#FFFBEB", border="#B45309"))
    flow.append(Spacer(1, 4 * mm))

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

def _name_numerology_section(s, name: str, lang: str = "hinglish") -> List[Any]:
    """Side-by-side Pythagorean vs Chaldean name analysis."""
    from vedic.numerology.extended import _PYTH, _VOWELS

    flow: List[Any] = []
    flow.append(_section_title(s, _T(lang,
        "Name Numerology — Dual Alphabet Analysis",
        "नाम-अंकशास्त्र — दोहरे वर्णमाला विश्लेषण",
        "Name Numerology — Dual Alphabet Analysis")))
    flow.append(Paragraph(_T(lang,
        f"Your name: <b>{name}</b><br/>Computed in both systems — Pythagorean "
        "(modern, spiritual) and Chaldean (ancient, professional).",
        f"आपका नाम: <b>{name}</b><br/>पाइथागोरियन (आधुनिक, आध्यात्मिक) और "
        "चाल्डियन (प्राचीन, व्यावसायिक) — दोनों प्रणालियों से गणना की गयी।",
        f"Aapka naam: <b>{name}</b><br/>Pythagorean (modern, spiritual) aur "
        "Chaldean (ancient, professional) dono systems se compute kiya gaya hai."),
        s["body_mid"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_explain_card(s, lang,
        "📖 Pythagorean vs Chaldean — which one matters more?",
        "📖 Pythagorean बनाम Chaldean — कौन-सा अधिक मायने रखता है?",
        "📖 Pythagorean vs Chaldean — kaunsa zyada matter karta hai?",
        "Both. They answer different questions. <b>Pythagorean</b> (1-9, sequential A-Z) "
        "is the simpler, modern system — best for <b>personal traits and life path</b>. "
        "<b>Chaldean</b> (1-8 only, 9 sacred & absent, sound-based) is the ancient "
        "system Cheiro used — best for <b>business names, brand reputation, and "
        "public-facing destiny</b>. Big consultations check Chaldean for the brand "
        "and Pythagorean for the founder's personal vibration. Below you see both, "
        "side by side.",
        "दोनों। दोनों अलग-अलग प्रश्नों का उत्तर देते हैं। <b>पाइथागोरियन</b> (1-9, "
        "क्रमिक A-Z) सरल आधुनिक प्रणाली — <b>व्यक्तिगत लक्षण और जीवन-पथ</b> के लिए "
        "श्रेष्ठ। <b>चाल्डियन</b> (केवल 1-8, 9 सम्माननीय और अनुपस्थित, ध्वनि-आधारित) "
        "प्राचीन प्रणाली — चीरो की पसंद — <b>व्यावसायिक नाम, ब्रांड प्रतिष्ठा और "
        "सार्वजनिक नियति</b> के लिए श्रेष्ठ। बड़े परामर्श ब्रांड के लिए चाल्डियन और "
        "संस्थापक के लिए पाइथागोरियन देखते हैं। नीचे दोनों side-by-side।",
        "Dono. Dono alag questions ka jawab dete hain. <b>Pythagorean</b> (1-9, "
        "sequential A-Z) simple modern system — <b>personal traits aur life path</b> "
        "ke liye best. <b>Chaldean</b> (sirf 1-8, 9 sacred aur absent, sound-based) "
        "ancient system jo Cheiro use karta tha — <b>business names, brand "
        "reputation, public-facing destiny</b> ke liye best. Bade consultations brand "
        "ke liye Chaldean aur founder ke liye Pythagorean check karte hain. Neeche "
        "dono side-by-side.",
        bg="#FAF5FF", border="#5B21B6"))
    flow.append(Spacer(1, 4 * mm))

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

def _name_correction_section(s, name: str, driver: int, conductor: int,
                             lang: str = "hinglish") -> List[Any]:
    """Top spelling variants with harmony scores."""
    flow: List[Any] = []
    flow.append(_section_title(s, _T(lang,
        "Name Correction — Spelling Variants",
        "नाम सुधार — वर्तनी विकल्प",
        "Name Correction — Spelling Variants")))
    flow.append(Paragraph(_T(lang,
        "A small change in spelling shifts the vibration. These variants are scored "
        "(0-100) by their harmony with your Driver and Conductor numbers.",
        "नाम की वर्तनी में छोटा-सा परिवर्तन कंपन को बदल देता है। ये विकल्प आपके "
        "Driver और Conductor अंकों के साथ सामंजस्य के आधार पर 0-100 स्कोर किये गये।",
        "Naam ki spelling thoda badalne se vibration shift hota hai. Ye variants "
        "aapke Driver aur Conductor numbers ke saath harmony ke aadhar par scored "
        "hain (0-100)."), s["body_mid"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_explain_card(s, lang,
        "📖 Can a single extra letter really change my life?",
        "📖 क्या एक अतिरिक्त अक्षर वाकई जीवन बदल सकता है?",
        "📖 Ek extra letter kya sach me life badal sakta hai?",
        "Yes — but the mechanism is misunderstood. Adding/removing one letter changes "
        "the <b>name's expression number</b>, which changes how your name <b>sounds "
        "and is written</b> repeatedly across documents, contracts, social media. "
        "Over time the new vibration repeats <b>thousands of times</b> and slowly "
        "rewrites the subconscious. Famous examples: Amitabh Bachchan, Ekta Kapoor, "
        "Ajay Devgn — all corrected spellings. The variants below are <b>ranked by "
        "harmony score</b> — pick a top-3 candidate and apply it gradually (signature "
        "first, then social, then official).",
        "हाँ — पर तंत्र को ग़लत समझा जाता है। एक अक्षर जोड़ना/हटाना नाम के "
        "<b>Expression अंक</b> को बदलता है, जिससे नाम का <b>उच्चारण और लेखन</b> "
        "दस्तावेज़ों, अनुबंधों, सोशल मीडिया पर बार-बार बदल जाता है। समय के साथ नया "
        "कंपन <b>हज़ारों बार</b> दोहराता है और अवचेतन को धीरे-धीरे फिर से लिखता है। "
        "प्रसिद्ध उदाहरण: अमिताभ बच्चन, एकता कपूर, अजय देवगन — सबने वर्तनी सुधारी। "
        "नीचे विकल्प <b>सामंजस्य-स्कोर</b> के क्रम में हैं — शीर्ष-3 में से चुनें और "
        "धीरे-धीरे अपनाएं (पहले हस्ताक्षर, फिर सोशल, फिर आधिकारिक)।",
        "Haan — par mechanism misunderstand hota hai. Ek letter add/remove karne se "
        "naam ka <b>Expression number</b> change hota hai, jisse naam <b>kaise "
        "sound karta aur likha jaata hai</b> wo documents, contracts, social media "
        "par baar-baar shift hota hai. Time ke saath nayi vibration <b>hazaaron baar</b> "
        "repeat hoti hai aur subconscious ko slowly rewrite karti hai. Famous "
        "examples: Amitabh Bachchan, Ekta Kapoor, Ajay Devgn — sabne spelling "
        "correct ki. Neeche variants <b>harmony score</b> ke order me hain — top-3 "
        "candidate chunein aur gradually apply karein (signature first, phir social, "
        "phir official).",
        bg="#F0FDF4", border="#15803D"))
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


def _life_summary_block(s, name: str, driver: int, conductor: int,
                        lang: str = "hinglish") -> List[Any]:
    """Premium Life Summary card — top of report (instant ₹1499 feel)."""
    flow: List[Any] = []
    summary = _nr.life_summary_block(driver, conductor, name)

    flow.append(Paragraph(_T(lang,
        "⭐ YOUR LIFE BLUEPRINT",
        "⭐ आपका जीवन-नक्शा (LIFE BLUEPRINT)",
        "⭐ AAPKA LIFE BLUEPRINT"), s["page_title"]))
    flow.append(Spacer(1, 2 * mm))
    flow.append(Paragraph(_T(lang,
        "<i>Built from your kundli and birth date — 100% personalised.</i>",
        "<i>आपकी कुंडली और जन्म-तिथि के आधार पर तैयार — 100% personalised.</i>",
        "<i>Aapki kundli aur janma-tithi ke aadhar par taiyaar — 100% personalized.</i>"),
        ParagraphStyle("ls_sub", fontName="Helvetica-Oblique", fontSize=10,
                       textColor=TEXT_SOFT, leading=14, spaceAfter=8)))
    flow.append(_explain_card(s, lang,
        "📖 What is this 'Life Blueprint' card?",
        "📖 यह 'जीवन नक्शा' कार्ड क्या है?",
        "📖 Yeh 'Life Blueprint' card kya hai?",
        "Numerology says your <b>Driver number</b> (birth-date day reduced) and <b>Conductor "
        "number</b> (full-date sum reduced) together form the spine of your personality, "
        "your ruling planet, and your destiny pattern. The card below is your one-glance "
        "<b>consultation summary</b> — the five things a numerologist would tell you in "
        "the first five minutes if you walked into their office. Use it as a quick mirror; "
        "the next pages explain each item with the <i>Why · Impact · Action</i> framework.",
        "अंक-शास्त्र कहता है कि आपका <b>Driver number</b> (जन्म दिन का योग) और <b>Conductor "
        "number</b> (पूरी जन्म-तिथि का योग) मिलकर आपके स्वभाव, ग्रह-स्वामी और भाग्य की रेखा "
        "तय करते हैं। नीचे का कार्ड आपके लिए एक-नज़र में <b>परामर्श-सार</b> है — वही पाँच "
        "बातें जो कोई अनुभवी अंक-ज्योतिषी पहले पाँच मिनट में आपको बताता। इसे शीशा मानिये; "
        "अगले पन्ने हर बात को 'क्यों · असर · क्या करें' तरीके से समझाते हैं।",
        "Numerology kehti hai aapka <b>Driver number</b> (birth-date day reduce karke) "
        "aur <b>Conductor number</b> (poori date ka sum reduce karke) milkar aapki "
        "personality, ruling planet aur destiny pattern banate hain. Neeche ka card aapka "
        "<b>one-glance consultation summary</b> hai — wahi 5 baatein jo koi numerologist "
        "office me first 5 minute me bata deta. Isse mirror ki tarah use karein; agle "
        "pages me har point ka <i>Why · Impact · Action</i> framework se deep explanation hai.",
        bg="#FFF7ED", border="#C2410C"))
    flow.append(Spacer(1, 4 * mm))

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


def _life_essence_section(s, driver: int, lang: str = "hinglish") -> List[Any]:
    """Page: 'Aap Kaun Ho?' — 3-paragraph identity story."""
    flow: List[Any] = []
    n = _nr.narrative_for(driver) or {}
    flow.append(Paragraph(_T(lang,
        "🌟 WHO YOU REALLY ARE — Your True Identity",
        "🌟 आप कौन हो — आपकी असली पहचान",
        "🌟 AAP KAUN HO — Your True Identity"), s["page_title"]))
    flow.append(Spacer(1, 2 * mm))
    flow.append(Paragraph(
        f"<i>{n.get('title', '')} — {n.get('tagline', '')}</i>",
        ParagraphStyle("le_sub", fontName="Helvetica-Oblique", fontSize=11,
                       textColor=BRAND_GOLD, leading=15, spaceAfter=8)))
    flow.append(_explain_card(s, lang,
        "📖 Why does your Driver number define your identity?",
        "📖 Driver नंबर आपकी पहचान क्यों तय करता है?",
        "📖 Driver number aapki identity kyun decide karta hai?",
        f"Your Driver number is <b>{driver}</b> — derived from the day you were born. "
        "In Vedic numerology, this single digit carries the imprint of the planet that "
        "ruled the sky on that day, and that planet's signature shapes your <b>core "
        "personality, hidden strengths and recurring blocks</b> for the rest of your life. "
        "The 3 stories below are not horoscope-style guesses — they are the lived patterns "
        "people of your number consistently report. The strengths/challenges grids show "
        "the 5+5 traits you should nurture and the 5 you should consciously guard against.",
        f"आपका Driver नंबर <b>{driver}</b> है — आपके जन्म-दिवस से निकाला गया। "
        "वैदिक अंक-शास्त्र में यह एक अंक उस ग्रह की छाप रखता है जो उस दिन आकाश में "
        "प्रमुख था, और वही ग्रह आपकी <b>मूल पहचान, छुपी शक्तियाँ और बार-बार आने वाली "
        "रुकावटें</b> जीवन-भर के लिए तय करता है। नीचे दी गई 3 कहानियाँ राशिफल जैसी "
        "अटकलें नहीं हैं — ये आपकी संख्या वाले लोगों के बार-बार दिखे पैटर्न हैं। "
        "नीचे की Strengths/Challenges सूचियाँ वो 5+5 गुण दिखाती हैं जिन्हें आपको "
        "बढ़ाना है और 5 कमज़ोरियाँ जिनसे सजग रहना है।",
        f"Aapka Driver number <b>{driver}</b> hai — birth-date day se nikla. "
        "Vedic numerology me yeh ek digit us planet ki imprint rakhta hai jo us din sky "
        "me prominent tha — aur wahi planet aapki <b>core personality, hidden strengths "
        "aur recurring blocks</b> jeevan-bhar ke liye tay karta hai. Neeche 3 stories "
        "horoscope-style guess nahi — yeh aapke number wale logo ke baar-baar dikhe "
        "patterns hain. Neeche ki Strengths/Challenges lists wo 5+5 traits dikhati hain "
        "jo nurture karne hain aur 5 weak points jinse bachna hai.",
        bg="#F5F3FF", border="#5B21B6"))
    flow.append(Spacer(1, 4 * mm))
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


def _career_blueprint_section(s, driver: int, lang: str = "hinglish") -> List[Any]:
    """Page: Career Blueprint — fields, mistakes, growth timing."""
    flow: List[Any] = []
    n = _nr.narrative_for(driver) or {}
    flow.append(Paragraph(_T(lang,
        "💼 CAREER BLUEPRINT — Your Professional Path",
        "💼 करियर ब्लूप्रिंट — आपकी व्यावसायिक राह",
        "💼 CAREER BLUEPRINT — Aapka Professional Path"), s["page_title"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_explain_card(s, lang,
        "📖 How does numerology decide your career?",
        "📖 अंक-शास्त्र आपका करियर कैसे तय करता है?",
        "📖 Numerology aapka career kaise decide karta hai?",
        "Each Driver number is ruled by a planet, and every planet rules certain "
        "<b>professions, work-styles and timing of success</b>. For example, Sun (1) "
        "drives leadership and govt roles; Moon (2) suits people-services and creative "
        "fields; Saturn (8) rules large systems, real estate and slow-but-certain wealth. "
        "The card below tells you <b>which fields fit, the recurring mistake your number "
        "tends to make</b>, and the <b>age windows</b> when your hard work converts to "
        "real result. Use this as a course-correction lens — not a job ad.",
        "हर Driver संख्या किसी ग्रह द्वारा शासित होती है, और हर ग्रह कुछ निश्चित "
        "<b>पेशे, कार्य-शैली और सफलता के समय</b> का स्वामी होता है। उदाहरण: सूर्य (1) "
        "नेतृत्व और सरकारी पदों का स्वामी; चंद्र (2) सेवा और रचनात्मक क्षेत्र; शनि (8) "
        "बड़ी प्रणालियाँ, real estate और धीरे-धीरे आता निश्चित धन। नीचे कार्ड बताता है "
        "<b>कौन से क्षेत्र आपके लिए सही हैं, आपकी संख्या वाले लोग कौन-सी ग़लती बार-बार "
        "करते हैं</b>, और <b>वो आयु-खिड़कियाँ</b> जब मेहनत असली फल देती है। इसे "
        "course-correction के शीशे की तरह देखें — नौकरी विज्ञापन नहीं।",
        "Har Driver number kisi planet se ruled hota hai, aur har planet kuch specific "
        "<b>professions, work-style aur success ka timing</b> rule karta hai. Example: "
        "Sun (1) leadership aur govt roles; Moon (2) people-services aur creative fields; "
        "Saturn (8) bade systems, real estate aur slow-but-certain wealth. Neeche card "
        "batata hai <b>kaunse fields fit hain, aapke number wale kya recurring mistake "
        "karte hain</b>, aur <b>age windows</b> jab mehnat result me convert hoti hai. "
        "Isse course-correction lens ki tarah use karein — job ad nahi.",
        bg="#EFF6FF", border="#1D4ED8"))
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


def _love_pattern_section(s, driver: int, lang: str = "hinglish") -> List[Any]:
    """Page: Love & Relationship deep-dive."""
    flow: List[Any] = []
    n = _nr.narrative_for(driver) or {}
    flow.append(Paragraph(_T(lang,
        "💕 LOVE PATTERN — The Reality of Your Relationships",
        "💕 प्रेम-पैटर्न — रिश्तों की असलियत",
        "💕 LOVE PATTERN — Rishton ki Reality"), s["page_title"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_explain_card(s, lang,
        "📖 Why does numerology have a 'love pattern'?",
        "📖 अंक-शास्त्र में 'प्रेम-पैटर्न' क्यों होता है?",
        "📖 Numerology me 'love pattern' kyun hota hai?",
        "Love is not random chemistry — it is the meeting of two planetary energies. "
        "Your Driver number's planet decides <b>how you express love</b> (passionate / "
        "calm / dramatic / loyal), <b>what triggers a breakup</b>, and <b>which numbers "
        "naturally harmonise with you</b>. The 3 cards below — Love Style, Breakup "
        "Trigger, Ideal Partner Number — are the same patterns thousands of people of "
        "your number consistently report. Knowing them lets you stop blaming the "
        "partner and start fixing the pattern.",
        "प्रेम संयोग नहीं है — यह दो ग्रह-ऊर्जाओं का मिलन है। आपके Driver नंबर का ग्रह "
        "तय करता है <b>आप प्रेम कैसे जताते हैं</b> (जोशीला / शांत / नाटकीय / निष्ठावान), "
        "<b>क्या रिश्ते को तोड़ता है</b>, और <b>कौन से नंबर आपसे स्वाभाविक रूप से मेल "
        "खाते हैं</b>। नीचे की 3 कार्ड्स — Love Style, Breakup Trigger, Ideal Partner — "
        "वही पैटर्न हैं जो आपकी संख्या वाले हज़ारों लोग बार-बार बताते हैं। इन्हें जानकर "
        "आप साथी को दोष देना बंद कर पैटर्न ठीक करना शुरू करते हैं।",
        "Love random chemistry nahi — yeh do planetary energies ka meeting hai. Aapke "
        "Driver number ka planet decide karta hai <b>aap pyar kaise express karte ho</b> "
        "(passionate / calm / dramatic / loyal), <b>kya breakup trigger karta hai</b>, "
        "aur <b>kaunse numbers aapse natural harmony rakhte hain</b>. Neeche ki 3 "
        "cards — Love Style, Breakup Trigger, Ideal Partner — wahi patterns hain jo "
        "aapke number wale hazaaron log baar-baar report karte hain. Inhe jaan ke aap "
        "partner ko blame karna band kar pattern fix karna shuru karte ho.",
        bg="#FDF2F8", border="#BE185D"))
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


def _wealth_health_spirit_section(s, driver: int, lang: str = "hinglish") -> List[Any]:
    """Page: Money + Health + Spiritual path combined."""
    flow: List[Any] = []
    n = _nr.narrative_for(driver) or {}
    flow.append(Paragraph(_T(lang,
        "🕉️ HEALTH & DHARMA — Body + Soul",
        "🕉️ स्वास्थ्य और धर्म — शरीर + आत्मा",
        "🕉️ HEALTH & DHARMA — Body + Soul"), s["page_title"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_explain_card(s, lang,
        "📖 Why combine Health and Dharma on one page?",
        "📖 Health और Dharma एक ही पेज पर क्यों?",
        "📖 Health aur Dharma ek hi page par kyun?",
        "Vedic numerology treats the body as a temple of the soul — what your planet "
        "rules in the body (Sun=heart, Moon=mind, Mars=blood, Saturn=joints) is exactly "
        "what your <b>spiritual practice</b> must strengthen. The Health card below shows "
        "the organs/systems your number must guard and small daily disciplines that pay "
        "off; the Dharma card shows the <b>soul-purpose</b> your number was born to "
        "fulfil — service, art, leadership, teaching, building, healing. Together they "
        "answer: <i>'kis kaam ke liye yeh sharir mila hai?'</i>",
        "वैदिक अंक-शास्त्र शरीर को आत्मा का मंदिर मानता है — आपके ग्रह का शरीर पर शासन "
        "(सूर्य=हृदय, चंद्र=मन, मंगल=रक्त, शनि=जोड़) ठीक वही है जिसे आपकी <b>आध्यात्मिक "
        "साधना</b> मज़बूत करती है। नीचे Health कार्ड वो अंग/तंत्र दिखाता है जिन्हें "
        "बचाना है और छोटी दैनिक आदतें जो लंबे समय में फल देती हैं; Dharma कार्ड वो "
        "<b>आत्म-उद्देश्य</b> बताता है जिसके लिए आपकी संख्या जन्मी है — सेवा, कला, "
        "नेतृत्व, शिक्षण, निर्माण, उपचार। दोनों मिलकर जवाब देते हैं: <i>'किस काम के लिए "
        "यह शरीर मिला है?'</i>",
        "Vedic numerology body ko soul ka mandir maanti hai — aapke planet ka body par "
        "rule (Sun=heart, Moon=mind, Mars=blood, Saturn=joints) wahi hai jise aapki "
        "<b>spiritual practice</b> strengthen karti hai. Neeche Health card wo organs/"
        "systems dikhata hai jinhe guard karna hai aur chhoti daily disciplines jo lambe "
        "samay me fal deti hain; Dharma card wo <b>soul-purpose</b> batata hai jiske "
        "liye aapka number paida hua — service, art, leadership, teaching, building, "
        "healing. Dono milkar jawab dete hain: <i>'kis kaam ke liye yeh sharir mila hai?'</i>",
        bg="#ECFDF5", border="#047857"))
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


def _risk_alerts_section(s, driver: int, lang: str = "hinglish") -> List[Any]:
    """Page: Risk Alerts + Golden Opportunity Periods."""
    flow: List[Any] = []
    n = _nr.narrative_for(driver) or {}
    flow.append(Paragraph(_T(lang,
        "⚠️ RISK ALERTS & 🌟 GOLDEN PERIODS",
        "⚠️ जोखिम चेतावनी और 🌟 स्वर्णिम अवसर",
        "⚠️ RISK ALERTS & 🌟 GOLDEN PERIODS"), s["page_title"]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_explain_card(s, lang,
        "📖 What are 'risk windows' and 'golden periods'?",
        "📖 'जोखिम-समय' और 'स्वर्णिम अवधि' का क्या अर्थ है?",
        "📖 'Risk windows' aur 'golden periods' ka kya matlab?",
        "Every Driver number runs through cycles where its planet's energy is "
        "<b>blocked, debilitated or weak</b> — those are <b>risk windows</b>, the months "
        "when accidents, money loss, legal issues, and ego clashes spike. Conversely "
        "there are months when the planet is <b>exalted and friendly</b> — the "
        "<b>golden window</b>. Same effort gives 3× result. The card below lists 5 "
        "specific risks of your number and the upcoming golden window. Action: postpone "
        "big decisions in risk months, and front-load launches/agreements/marriages in "
        "the golden window.",
        "हर Driver नंबर ऐसे चक्र से गुज़रता है जब उसके ग्रह की ऊर्जा <b>अवरुद्ध, "
        "नीचा या कमज़ोर</b> होती है — ये <b>जोखिम-खिड़कियाँ</b> हैं, वो महीने जब "
        "दुर्घटना, धन-हानि, कानूनी झंझट और अहंकार-टकराव बढ़ते हैं। इसके विपरीत कुछ "
        "महीने ग्रह <b>उच्च और मित्र-स्थिति</b> में होता है — <b>स्वर्णिम खिड़की</b>। "
        "समान मेहनत 3 गुना फल देती है। नीचे का कार्ड आपकी संख्या के 5 विशिष्ट जोखिम "
        "और आगामी स्वर्णिम-खिड़की दिखाता है। क्या करें: जोखिम-मासों में बड़े निर्णय "
        "टालें; स्वर्णिम-खिड़की में लॉन्च/समझौते/विवाह करें।",
        "Har Driver number aise cycles se guzarta hai jab uske planet ki energy "
        "<b>blocked, debilitated ya weak</b> hoti hai — yeh <b>risk windows</b> hain, wo "
        "mahine jab accident, money-loss, legal issue aur ego-clash spike karte hain. "
        "Iske ulta kuch mahine planet <b>exalted aur friendly</b> hota hai — "
        "<b>golden window</b>. Same mehnat 3× result deti hai. Neeche card aapke number "
        "ke 5 specific risks aur upcoming golden window dikhata hai. Action: risk "
        "months me bade decisions postpone karein; golden window me launches/agreements/"
        "shaadi front-load karein.",
        bg="#FEF2F2", border="#991B1B"))
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


def _lucky_colours_section(s, driver: int, vehicle: Optional[str] = None,
                           lang: str = "hinglish") -> List[Any]:
    """Premium Lucky Colours page — vehicle, dress, business, day-wise."""
    flow: List[Any] = []
    pack = _nr.lucky_colours_pack(driver)

    flow.append(Paragraph(_T(lang,
        "🎨 LUCKY COLOURS — Specially Picked for You",
        "🎨 शुभ रंग — आपके लिए विशेष रूप से चुने हुए",
        "🎨 LUCKY COLOURS — Aapke Liye Specially Picked"), s["page_title"]))
    flow.append(Spacer(1, 2 * mm))
    flow.append(Paragraph(_T(lang,
        "<i>Chosen from your Driver number's planet — use them in daily life.</i>",
        "<i>आपके Driver नंबर के ग्रह के आधार पर चुने — दैनिक जीवन में प्रयोग करें।</i>",
        "<i>Driver number ke planet ke aadhar par chosen — daily life me use karein.</i>"),
        ParagraphStyle("lc_sub", fontName="Helvetica-Oblique", fontSize=10,
                       textColor=TEXT_SOFT, leading=14, spaceAfter=8)))
    flow.append(_explain_card(s, lang,
        "📖 Why do colours matter in numerology?",
        "📖 अंक-शास्त्र में रंगों का महत्व क्यों?",
        "📖 Numerology me colours ka importance kyun?",
        "Each planet emits a specific frequency of light — and colours ARE light "
        "frequencies. Wearing the colour of your ruling planet is the simplest, "
        "fastest <b>energy alignment</b> you can do — no mantras, no rituals, just "
        "wear it. Conversely, the 'avoid' colours actively drain your number. The "
        "card below gives <b>Primary, Secondary, Avoid, Gemstone tone, Vehicle and "
        "Brand</b> colours specifically for your number — based on classical "
        "Cheiro / Saint Germain colour-planet mapping.",
        "हर ग्रह एक विशिष्ट प्रकाश-आवृत्ति उत्सर्जित करता है — और रंग प्रकाश की ही "
        "आवृत्तियाँ हैं। अपने स्वामी-ग्रह का रंग पहनना सबसे सरल, सबसे तेज़ "
        "<b>ऊर्जा-संरेखण</b> है — कोई मंत्र नहीं, कोई कर्मकांड नहीं, बस पहनिये। इसके "
        "विपरीत 'avoid' रंग आपकी संख्या को क्षीण करते हैं। नीचे का कार्ड आपकी संख्या "
        "के लिए <b>प्राथमिक, सहायक, अवॉइड, रत्न-छाया, वाहन और ब्रांड</b> रंग देता है "
        "— शास्त्रीय चीरो / सेंट जर्मेन रंग-ग्रह मानचित्र के अनुसार।",
        "Har planet ek specific light frequency emit karta hai — aur colours light "
        "frequencies HI hain. Apne ruling planet ka colour pehnna sabse simple, sabse "
        "fast <b>energy alignment</b> hai — koi mantra nahi, koi ritual nahi, bas "
        "pehno. Iske ulta 'avoid' colours actively aapki number ki energy drain karte "
        "hain. Neeche card aapke number ke liye <b>Primary, Secondary, Avoid, "
        "Gemstone tone, Vehicle aur Brand</b> colours deta hai — classical Cheiro / "
        "Saint Germain colour-planet mapping ke aadhar par.",
        bg="#FFFBEB", border="#B45309"))
    flow.append(Spacer(1, 4 * mm))

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


def _day_dress_section(s, driver: int, lang: str = "hinglish") -> List[Any]:
    """Day-wise colour to wear — Mon-Sun planetary table."""
    flow: List[Any] = []
    pack = _nr.lucky_colours_pack(driver)

    flow.append(Paragraph(_T(lang,
        "👕 WHICH COLOUR TO WEAR ON WHICH DAY",
        "👕 किस दिन कौन-सा रंग पहनें",
        "👕 KIS DIN KAUNSA COLOUR PEHNEIN"), s["page_title"]))
    flow.append(Spacer(1, 2 * mm))
    flow.append(Paragraph(_T(lang,
        "<i>Per the Vedic planetary days — wear each day's 'power colour' to unlock "
        "that day's energy.</i>",
        "<i>वैदिक ग्रह-दिवसों के अनुसार — हर दिन का 'शक्ति-रंग' पहनकर उस दिन की "
        "ऊर्जा खोलिये।</i>",
        "<i>Vedic planetary days ke according — har din ka 'power colour' pehno aur "
        "us din ki energy unlock karo.</i>"),
        ParagraphStyle("dd_sub", fontName="Helvetica-Oblique", fontSize=10,
                       textColor=TEXT_SOFT, leading=14, spaceAfter=8)))
    flow.append(_explain_card(s, lang,
        "📖 Why does the day-of-week colour matter?",
        "📖 दिन-विशेष रंग का महत्व क्यों?",
        "📖 Day-of-week colour ka importance kyun?",
        "Each weekday is ruled by a specific planet — Sunday by Sun, Monday by Moon, "
        "Tuesday by Mars, and so on. Wearing that planet's colour on its day "
        "<b>resonates with the ambient cosmic frequency</b>, making the day's energy "
        "work <i>with</i> you instead of around you. Think of it as choosing the "
        "right radio frequency. The table below combines this with your personal "
        "Driver number — so your everyday outfit becomes a quiet daily upgrade.",
        "हर सप्ताह-दिवस का स्वामी एक विशिष्ट ग्रह है — रविवार सूर्य, सोमवार चंद्र, "
        "मंगलवार मंगल, इत्यादि। उस दिन उसी ग्रह का रंग पहनना <b>उस दिन की "
        "ब्रह्मांडीय आवृत्ति से अनुनाद</b> बनाता है, जिससे दिन की ऊर्जा आपके "
        "<i>साथ</i> काम करती है, न कि आपके आसपास। इसे सही रेडियो-फ्रीक्वेंसी चुनना "
        "मानिये। नीचे की तालिका इसे आपके व्यक्तिगत Driver नंबर से जोड़ती है — "
        "रोज़मर्रा का पहनावा एक मूक दैनिक अपग्रेड बन जाता है।",
        "Har weekday ka swami ek specific planet hai — Sunday=Sun, Monday=Moon, "
        "Tuesday=Mars, etc. Us din wahi planet ka colour pehnna <b>us din ki ambient "
        "cosmic frequency se resonance</b> banata hai, jiske wajah se din ki energy "
        "aapke <i>saath</i> kaam karti hai, na ki around. Ise sahi radio frequency "
        "tune karna samjho. Neeche table iss principle ko aapke personal Driver "
        "number se combine karta hai — daily outfit ek silent daily upgrade ban jaata hai.",
        bg="#F0F9FF", border="#0C4A6E"))
    flow.append(Spacer(1, 4 * mm))

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
    story += _life_summary_block(s, name, driver, conductor, lang=lang)
    story.append(PageBreak())

    # Page 3 — 🌟 Aap Kaun Ho (3-paragraph identity story + strengths/challenges)
    story += _life_essence_section(s, driver, lang=lang)
    story.append(PageBreak())

    # Page 4 — 💼 Career Blueprint (Why + Mistake + Timing + Money pattern)
    story += _career_blueprint_section(s, driver, lang=lang)
    story.append(PageBreak())

    # Page 5 — 💕 Love Pattern (Style + Triggers + Ideal Partner)
    story += _love_pattern_section(s, driver, lang=lang)
    story.append(PageBreak())

    # Page 6 — 🕉️ Health & Dharma (Body + Spirit)
    story += _wealth_health_spirit_section(s, driver, lang=lang)
    story.append(PageBreak())

    # Page 7 — ⚠️ Risk Alerts + 🌟 Golden Periods + Executive Summary
    story += _risk_alerts_section(s, driver, lang=lang)
    story.append(PageBreak())

    # ─── Part 2 EXTRAS — Lucky Colours + Day-wise Dress + Practical numbers ───
    # Page 8 — 🎨 Lucky Colours (vehicle + business + gemstone tone)
    story += _lucky_colours_section(s, driver, vehicle=vehicle, lang=lang)
    story.append(PageBreak())

    # Page 9 — 👕 Day-wise Dress Colour table (Mon-Sun planetary)
    story += _day_dress_section(s, driver, lang=lang)
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
    story += _driver_conductor_intro(s, name, dob, driver, conductor, lang=lang)
    story.append(PageBreak())

    # Page 11-13 — Mobile / Vehicle / House deep analysis (with Why·Impact·Action)
    if mobile:
        story += _number_analysis_block(s, mobile, "mobile", driver, conductor, lang=lang)
        story.append(PageBreak())
    if vehicle:
        story += _number_analysis_block(s, vehicle, "vehicle", driver, conductor, lang=lang)
        story.append(PageBreak())
    if house:
        story += _number_analysis_block(s, house, "house", driver, conductor, lang=lang)
        story.append(PageBreak())

    # Page 14 — Number Compatibility Matrix
    story += _compatibility_matrix_section(s, driver, lang=lang)
    story.append(PageBreak())

    # Page 15 — Letter-by-letter table
    story += _letter_table_section(s, name, lang=lang)
    story.append(PageBreak())

    # Page 16 — Pythagorean vs Chaldean summary
    story += _name_numerology_section(s, name, lang=lang)
    story.append(PageBreak())

    # Page 17 — Name correction
    story += _name_correction_section(s, name, driver, conductor, lang=lang)
    story.append(PageBreak())

    # Page 18 — Signature & branding
    story += _signature_section(s, name, driver, lang=lang)
    story.append(PageBreak())

    # Page 19 — 90-day implementation plan
    story += _timeline_section(s, lang=lang)
    story += _disclaimer(s)

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

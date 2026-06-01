"""
numerology_pdf.py — Sprint 53-N4
Render a comprehensive numerology PDF report for a single native.

Output structure (multi-page A4):
  1. Cover (name, DOB, brand)
  2. Core numbers (Driver/Conductor/Name) + archetypes + compatibility
  3. Lo Shu 3x3 grid + missing/repeated numbers + planes
  4. Life path + Soul Urge + Personality + Expression + master numbers + karmic debt + compound
  5. Personal Year / Month / Day cycles
  6. Pinnacles & Challenges (4+4 with age windows)
  7. Career recommendations (number psychology only)
  8. Financial psychology + productivity rhythm add-ons
  9. Disclaimer + brand footer

Brand rule: "Powered by Advanced Cosmic Intelligence" — never mention AI/LLM.
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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from numerology.core.meanings import (
    NUMBER_PERSONALITY,
    cheiro_compound_fallback,
    get_personality,
)
from numerology.core.sanitize import sanitize_text as _sanitize_text

# ── Devanagari font registration (shared with milan_pdf) ─────────────────
_DEVA_REG  = "Helvetica"
_DEVA_BOLD = "Helvetica-Bold"


def _sync_deva_font_aliases() -> None:
    global _DEVA_REG, _DEVA_BOLD
    try:
        import milan_pdf as _mp

        _mp.register_indic_fonts()
        pair = _mp._INDIC_REGISTERED.get("NotoDeva")
        if pair:
            _DEVA_REG, _DEVA_BOLD = pair
    except Exception:
        pass


_sync_deva_font_aliases()


# ─── Language helpers ───────────────────────────────────────────────────
def _T(lang: str, en: str, hi: str, hg: str) -> str:
    lang = (lang or "hinglish").lower()
    if lang == "english":
        return _sanitize_text(en)
    if lang == "hindi":
        return _sanitize_text(hi)
    return _sanitize_text(hg)


def _explain_card(s, lang: str, title_en: str, title_hi: str, title_hg: str,
                  body_en: str, body_hi: str, body_hg: str,
                  bg="#F0FDF4", border="#15803D"):
    title = _T(lang, title_en, title_hi, title_hg)
    body  = _T(lang, body_en,  body_hi,  body_hg)
    fname = _DEVA_REG if (lang or "").lower() == "hindi" else "Helvetica"
    para = Paragraph(
        f"<font color='{border}'><b>{title}</b></font><br/><br/>"
        f"<font color='#1F2937'>{body}</font>",
        ParagraphStyle("ec_p1", fontName=fname, fontSize=9.5, leading=14,
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

# Brand palette (matches mobile app + existing pdf_renderer)
BRAND_PURPLE = colors.HexColor("#7C3AED")
BRAND_GOLD   = colors.HexColor("#F5B700")
TEXT_DARK    = colors.HexColor("#0F172A")
TEXT_MID     = colors.HexColor("#475569")
TEXT_SOFT    = colors.HexColor("#94A3B8")
BG_CARD      = colors.HexColor("#F8FAFC")
BG_GRID      = colors.HexColor("#FAF5FF")
BORDER       = colors.HexColor("#E2E8F0")
ACCENT_GREEN = colors.HexColor("#047857")
ACCENT_RED   = colors.HexColor("#B91C1C")
ACCENT_AMBER = colors.HexColor("#B45309")


# ─── Helpers ─────────────────────────────────────────────────────────

def _safe(s: Any) -> str:
    if s is None:
        return ""
    return str(s)


def _styles(lang: str = "hinglish") -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    is_hi = (lang or "").lower() == "hindi"
    H_BOLD = _DEVA_BOLD if is_hi else "Helvetica-Bold"
    H_REG  = _DEVA_REG  if is_hi else "Helvetica"
    return {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=H_BOLD,
                              fontSize=22, leading=28, textColor=BRAND_PURPLE,
                              alignment=TA_CENTER, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=H_BOLD,
                              fontSize=14, leading=18, textColor=BRAND_PURPLE,
                              spaceBefore=10, spaceAfter=6),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName=H_BOLD,
                              fontSize=11, leading=14, textColor=TEXT_DARK,
                              spaceBefore=6, spaceAfter=2),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica",
                                fontSize=9.5, leading=13, textColor=TEXT_DARK),
        "body_mid": ParagraphStyle("body_mid", parent=base["BodyText"], fontName="Helvetica",
                                fontSize=9, leading=12, textColor=TEXT_MID),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName="Helvetica",
                                 fontSize=8, leading=10, textColor=TEXT_SOFT),
        "cover_name": ParagraphStyle("cover_name", parent=base["Heading1"],
                                     fontName=H_BOLD, fontSize=28, leading=34,
                                     textColor=TEXT_DARK, alignment=TA_CENTER,
                                     spaceBefore=8, spaceAfter=8),
        "cover_sub": ParagraphStyle("cover_sub", parent=base["BodyText"],
                                    fontName="Helvetica", fontSize=12, leading=16,
                                    textColor=TEXT_MID, alignment=TA_CENTER),
        "big_num": ParagraphStyle("big_num", parent=base["Heading1"],
                                  fontName="Helvetica-Bold", fontSize=44, leading=50,
                                  textColor=BRAND_PURPLE, alignment=TA_CENTER,
                                  spaceBefore=0, spaceAfter=4),
        "headline": ParagraphStyle("headline", parent=base["BodyText"],
                                   fontName="Helvetica-Bold", fontSize=10.5, leading=14,
                                   textColor=BRAND_GOLD, alignment=TA_CENTER,
                                   spaceAfter=4),
        "narrative": ParagraphStyle("narrative", parent=base["BodyText"],
                                    fontName="Helvetica", fontSize=10, leading=15,
                                    textColor=TEXT_DARK, spaceAfter=4,
                                    firstLineIndent=0),
        "callout": ParagraphStyle("callout", parent=base["BodyText"],
                                  fontName="Helvetica-Oblique", fontSize=10, leading=14,
                                  textColor=BRAND_PURPLE, alignment=TA_CENTER),
        "tagline": ParagraphStyle("tagline", parent=base["BodyText"],
                                  fontName="Helvetica-Oblique", fontSize=11, leading=14,
                                  textColor=BRAND_GOLD, alignment=TA_CENTER,
                                  spaceAfter=6),
        "page_title": ParagraphStyle("page_title", parent=base["Heading1"],
                                     fontName="Helvetica-Bold", fontSize=18, leading=22,
                                     textColor=BRAND_PURPLE, spaceAfter=4,
                                     spaceBefore=0),
    }


def _callout_box(s, title: str, body: str, bg_color, text_color=None) -> Table:
    """A coloured callout panel — used for 'Did you know' / quick summaries."""
    if text_color is None:
        text_color = TEXT_DARK
    inner = [
        [Paragraph(f"<b>{title}</b>", ParagraphStyle(
            "cbt", fontName="Helvetica-Bold", fontSize=9.5,
            textColor=text_color, leading=12))],
        [Paragraph(body, ParagraphStyle(
            "cbb", fontName="Helvetica", fontSize=9.5,
            textColor=text_color, leading=13))],
    ]
    t = Table(inner, colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("BOX", (0, 0), (-1, -1), 0, bg_color),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, -1), (-1, -1), 0),
    ]))
    return t


def _on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(TEXT_SOFT)
    canvas.setFont("Helvetica", 7.5)
    footer = "Powered by Advanced Cosmic Intelligence  ·  Cosmic Lens Numerology"
    canvas.drawCentredString(A4[0] / 2, 12 * mm, footer)
    canvas.drawRightString(A4[0] - 15 * mm, 12 * mm, f"Page {doc.page}")
    # Top brand bar
    canvas.setFillColor(BRAND_PURPLE)
    canvas.rect(0, A4[1] - 8 * mm, A4[0], 4 * mm, fill=1, stroke=0)
    canvas.setFillColor(BRAND_GOLD)
    canvas.rect(0, A4[1] - 8 * mm, A4[0], 1 * mm, fill=1, stroke=0)
    canvas.restoreState()


def _label_value_table(rows: List[tuple], col_widths=None) -> Table:
    if col_widths is None:
        col_widths = [55 * mm, 110 * mm]
    t = Table(rows, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9.5),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), TEXT_MID),
        ("TEXTCOLOR", (1, 0), (1, -1), TEXT_DARK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, BORDER),
    ]))
    return t


def _section_title(s, text: str):
    return Paragraph(text, s["h2"])


# ─── Page builders ───────────────────────────────────────────────────

def _cover(s, name: str, dob: str, gender: str | None) -> List[Any]:
    out: List[Any] = [Spacer(1, 28 * mm)]

    # Decorative top brand block (gold border + purple title)
    title_block = Table([
        [Paragraph("✦  NUMEROLOGY  ✦", ParagraphStyle(
            "ct", fontName="Helvetica-Bold", fontSize=26, leading=32,
            textColor=BRAND_PURPLE, alignment=TA_CENTER))],
        [Paragraph("Comprehensive Personal Report", ParagraphStyle(
            "cs", fontName="Helvetica", fontSize=12, leading=15,
            textColor=TEXT_MID, alignment=TA_CENTER))],
    ], colWidths=[180 * mm])
    title_block.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, BRAND_GOLD),
        ("LINEABOVE", (0, 0), (-1, 0), 4, BRAND_PURPLE),
        ("LINEBELOW", (0, -1), (-1, -1), 4, BRAND_PURPLE),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF9FF")),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    out.append(title_block)

    out.append(Spacer(1, 26 * mm))
    out.append(Paragraph(_safe(name) or "—", s["cover_name"]))
    out.append(Spacer(1, 2 * mm))
    sub = f"Date of Birth: {dob}"
    if gender:
        sub += f"  ·  {gender.title()}"
    out.append(Paragraph(sub, s["cover_sub"]))
    out.append(Spacer(1, 18 * mm))

    # Value-prop box ("what's inside") — premium positioning
    value_props = Table([
        [Paragraph(
            "<b>What's inside this report:</b>",
            ParagraphStyle("vt", fontName="Helvetica-Bold", fontSize=11,
                            textColor=BRAND_PURPLE, alignment=TA_CENTER, leading=14))],
        [Paragraph(
            "★  <b>Detailed personality</b> — what your number says about you<br/>"
            "★  <b>Famous people</b> — who shares your numbers<br/>"
            "★  <b>Lo Shu magic-square</b> — your strengths &amp; missing planes<br/>"
            "★  <b>Master numbers + Karmic debt</b> — Cheiro analysis<br/>"
            "★  <b>Personal Year / Month / Day</b> — live timing layer<br/>"
            "★  <b>Pinnacles &amp; Challenges</b> — life-cycle map<br/>"
            "★  <b>Career fit</b> — Driver + Conductor fields<br/>"
            "★  <b>Practical habits</b> — routines, journaling, sleep, budgeting",
            ParagraphStyle("vb", fontName="Helvetica", fontSize=10,
                            textColor=TEXT_DARK, leading=15))],
    ], colWidths=[150 * mm])
    value_props.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAF5FF")),
        ("BOX", (0, 0), (-1, -1), 0.6, BRAND_PURPLE),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
    ]))
    out.append(value_props)

    out.append(Spacer(1, 10 * mm))
    out.append(Paragraph(
        "Powered by <b>Advanced Cosmic Intelligence</b>",
        s["tagline"]))
    out.append(Spacer(1, 2 * mm))
    out.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}",
        ParagraphStyle("g", fontName="Helvetica", fontSize=9,
                       textColor=TEXT_SOFT, alignment=TA_CENTER)))
    return out


def _executive_summary(s, name: str, lang: str,
                       phase_s: dict, extended: dict, practical: dict) -> List[Any]:
    """TL;DR page: identity line + strengths + challenges + timing rhythm + final truth.
    Designed to give the user a 30-second 'this report nails me' moment up front."""
    out: List[Any] = []

    driver = (practical or {}).get("driver") or 0
    conductor = (practical or {}).get("conductor") or 0
    lp = ((extended or {}).get("life_path") or {}).get("life_path", "—")
    karmic = ((extended or {}).get("karmic_debt") or {})
    masters = ((extended or {}).get("master_numbers") or {})

    # Pull personality data (driver + conductor)
    drv_pers = NUMBER_PERSONALITY.get(driver, {}) if driver else {}
    con_pers = NUMBER_PERSONALITY.get(conductor, {}) if conductor else {}
    drv_strengths = list(drv_pers.get("strengths") or [])
    con_strengths = list(con_pers.get("strengths") or [])
    drv_weak = list(drv_pers.get("weaknesses") or [])
    con_weak = list(con_pers.get("weaknesses") or [])

    # Timing snapshot from Personal Year (no lucky catalog)
    try:
        _yr = datetime.now().year
        _py = _personal_year(dob, _yr) if dob else (driver or 1)
        _theme, _peak, _slow, _dates, _, _ = _PY_THEMES.get(_py, _PY_THEMES[1])
    except Exception:
        _theme, _peak, _slow, _dates = "—", "—", "—", "—"

    # ── Title
    out.append(_section_title(s, _T(lang,
        "📋 Your Report at a Glance",
        "📋 आपकी रिपोर्ट एक नज़र में",
        "📋 Aapki Report Ek Nazar Mein")))
    out.append(Spacer(1, 3 * mm))
    out.append(Paragraph(_T(lang,
        "<i>The 30-second snapshot — full depth begins on the next page.</i>",
        "<i>30-सेकंड का स्नैपशॉट — पूर्ण विश्लेषण अगले पृष्ठ से शुरू।</i>",
        "<i>30-second snapshot — poora detail next page se start hota hai.</i>"),
        s["body_mid"]))
    out.append(Spacer(1, 5 * mm))

    # ── Identity line
    identity = _T(lang,
        f"You are <b>Driver-{driver}</b> · <b>Conductor-{conductor}</b> · "
        f"<b>Life-Path-{lp}</b>",
        f"आप हैं <b>Driver-{driver}</b> · <b>Conductor-{conductor}</b> · "
        f"<b>Life-Path-{lp}</b>",
        f"Aap ho <b>Driver-{driver}</b> · <b>Conductor-{conductor}</b> · "
        f"<b>Life-Path-{lp}</b>")
    if masters.get("has_master"):
        identity += _T(lang, "  ·  <b>Master Number active</b>",
                       "  ·  <b>Master Number सक्रिय</b>",
                       "  ·  <b>Master Number active</b>")
    out.append(_callout_box(s,
        _T(lang, "WHO YOU ARE", "आप कौन हैं", "AAP KAUN HO"),
        identity,
        bg_color=colors.HexColor("#EDE9FE")))
    out.append(Spacer(1, 5 * mm))

    # ── 3 Core Strengths
    seen = set()
    strengths_pool: list[str] = []
    for src in (drv_strengths, con_strengths):
        for item in src:
            key = (item or "").strip().lower()[:40]
            if not key or key in seen:
                continue
            seen.add(key)
            strengths_pool.append(item.strip())
    top_strengths = strengths_pool[:3] or [
        _T(lang, "Unique signature emerging from your number combination",
           "आपकी अंक-संरचना से उभरती विशिष्ट पहचान",
           "Aapki number combination se ubharti unique signature")]

    out.append(Paragraph(_T(lang,
        "✨ <b>Top 3 Strengths</b>",
        "✨ <b>शीर्ष 3 शक्तियाँ</b>",
        "✨ <b>Top 3 Strengths</b>"), s["h3"]))
    for st in top_strengths:
        out.append(Paragraph(f"• {st}", s["body"]))
    out.append(Spacer(1, 4 * mm))

    # ── 3 Core Challenges
    seen2 = set()
    weak_pool: list[str] = []
    for src in (drv_weak, con_weak):
        for item in src:
            key = (item or "").strip().lower()[:40]
            if not key or key in seen2:
                continue
            seen2.add(key)
            weak_pool.append(item.strip())
    if karmic.get("has_karmic_debt"):
        for d in (karmic.get("debts") or [])[:1]:
            note = (d.get("meaning") or "").split(";")[0].strip()
            if note:
                weak_pool.insert(0, _T(lang,
                    f"Karmic Debt {d.get('value')}: {note}",
                    f"कर्मिक ऋण {d.get('value')}: {note}",
                    f"Karmic Debt {d.get('value')}: {note}"))
    top_weak = weak_pool[:3] or [
        _T(lang, "Watch for over-reliance on default patterns",
           "डिफ़ॉल्ट पैटर्न पर अति-निर्भरता से सावधान",
           "Default patterns par over-reliance se savdhaan")]

    out.append(Paragraph(_T(lang,
        "⚠️ <b>Top 3 Challenges</b>",
        "⚠️ <b>शीर्ष 3 चुनौतियाँ</b>",
        "⚠️ <b>Top 3 Challenges</b>"), s["h3"]))
    for w in top_weak:
        out.append(Paragraph(f"• {w}", s["body"]))
    out.append(Spacer(1, 5 * mm))

    # ── Timing rhythm (productivity cycles only)
    out.append(Paragraph(_T(lang,
        "🗓️ <b>Your Timing Rhythm</b>",
        "🗓️ <b>आपकी समय-लय</b>",
        "🗓️ <b>Aapki Timing Rhythm</b>"), s["h3"]))
    rhythm_rows = [
        [_T(lang, "Momentum theme", "गति-विषय", "Momentum theme"), _theme],
        [_T(lang, "Decision window", "निर्णय-खिड़की", "Decision window"), _peak],
        [_T(lang, "Reflection period", "चिंतन-अवधि", "Reflection period"), _slow],
        [_T(lang, "Focus dates", "फोकस-तिथियाँ", "Focus dates"), _dates],
    ]
    out.append(_label_value_table(rhythm_rows, col_widths=[55 * mm, 125 * mm]))
    out.append(Spacer(1, 5 * mm))

    # ── Final Truth (tied to driver headline)
    headline = (drv_pers.get("headline") or "").strip()
    title = (drv_pers.get("title") or "").strip()
    if headline:
        truth = _T(lang,
            f"At your core: <b>{title or 'Your archetype'}</b> — {headline}.",
            f"मूल में: <b>{title or 'आपका आर्किटाइप'}</b> — {headline}।",
            f"Core me: <b>{title or 'Aapka archetype'}</b> — {headline}.")
    else:
        truth = _T(lang,
            "Your number combination is your unrepeatable signature — own it.",
            "आपका अंक-संयोजन आपका अद्वितीय हस्ताक्षर है — इसे अपनाइये।",
            "Aapki number combination aapka ek-of-a-kind signature hai — apnao.")
    out.append(_callout_box(s,
        _T(lang, "✦ THE FINAL TRUTH", "✦ अंतिम सत्य", "✦ FINAL TRUTH"),
        truth,
        bg_color=colors.HexColor("#FEF3C7")))

    return out


def _core_numbers(s, ps: dict) -> List[Any]:
    s1 = (ps.get("s1_numbers") or {}) if isinstance(ps, dict) else {}
    out: List[Any] = []
    out.append(_section_title(s, "1. Core Numbers"))
    out.append(Paragraph(
        "Your three primary number-vibrations from birth date and name. "
        "These shape personality, fortune-flow and identity.",
        s["body_mid"]))
    out.append(Spacer(1, 4 * mm))

    label_style = ParagraphStyle(
        "lbl", fontName="Helvetica-Bold", fontSize=10, leading=12,
        textColor=TEXT_DARK, alignment=TA_CENTER)
    badge_style = ParagraphStyle(
        "badge", fontName="Helvetica-Bold", fontSize=42, leading=48,
        textColor=BRAND_PURPLE, alignment=TA_CENTER, spaceBefore=2, spaceAfter=2)
    ruler_style = ParagraphStyle(
        "rul", fontName="Helvetica-Bold", fontSize=9.5, leading=12,
        textColor=BRAND_GOLD, alignment=TA_CENTER)
    nature_style = ParagraphStyle(
        "nat", fontName="Helvetica", fontSize=8.5, leading=11,
        textColor=TEXT_MID, alignment=TA_CENTER)

    def _cell(label, num, archetype, nature):
        return [
            Paragraph(label, label_style),
            Paragraph(_safe(num) or "—", badge_style),
            Paragraph(f"Archetype: {_safe(archetype)}", ruler_style),
            Paragraph(_safe(nature), nature_style),
        ]

    cells = [
        _cell("Driver (Mulank)",
              s1.get("driver_mulank"), s1.get("driver_nature"), s1.get("driver_nature")),
        _cell("Conductor (Bhagyank)",
              s1.get("conductor_bhagyank"), s1.get("conductor_nature"), s1.get("conductor_nature")),
        _cell("Name Number",
              s1.get("name_number"),
              s1.get("name_archetype") or s1.get("name_planet"),
              "Public persona"),
    ]
    t = Table([cells], colWidths=[60 * mm, 60 * mm, 60 * mm], rowHeights=[None])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    out.append(t)
    out.append(Spacer(1, 6 * mm))

    # Compatibility verdict
    verdict = s1.get("compatibility_driver_conductor", "")
    color = ACCENT_GREEN if verdict == "HARMONIOUS" else (
        ACCENT_RED if verdict in ("CONFLICT", "CHALLENGING") else ACCENT_AMBER)
    out.append(Paragraph(
        f"<b>Driver–Conductor Compatibility:</b> "
        f"<font color='{color.hexval()}'><b>{verdict}</b></font>",
        s["body"]))
    out.append(Spacer(1, 3 * mm))

    # Friend / enemy numbers
    friends = ", ".join(str(x) for x in (s1.get("driver_friend_numbers") or []))
    enemies = ", ".join(str(x) for x in (s1.get("driver_enemy_numbers") or []))
    out.append(_label_value_table([
        ("Friend numbers (Driver)", friends or "—"),
        ("Enemy numbers (Driver)", enemies or "—"),
    ]))
    return out


def _lo_shu(s, ex: dict) -> List[Any]:
    grid = (ex.get("lo_shu") or {}) if isinstance(ex, dict) else {}
    out: List[Any] = []
    out.append(_section_title(s, "2. Lo Shu Grid (3×3 Magic Square)"))
    out.append(Paragraph(
        "Each digit in your DOB is mapped onto a 3×3 grid. Repeated numbers "
        "indicate strengths; missing numbers indicate areas to consciously develop.",
        s["body_mid"]))
    out.append(Spacer(1, 4 * mm))

    # Classic Lo Shu layout: top=4,9,2 / mid=3,5,7 / bot=8,1,6
    LO_SHU_LAYOUT = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
    counts = grid.get("counts") or {}
    digit_style = ParagraphStyle("gd", fontName="Helvetica-Bold",
                                  fontSize=22, alignment=TA_CENTER,
                                  textColor=BRAND_PURPLE, leading=24)
    count_style = ParagraphStyle("gc", fontName="Helvetica-Bold",
                                  fontSize=8, alignment=TA_CENTER,
                                  textColor=BRAND_GOLD, leading=10)
    miss_style = ParagraphStyle("gm", fontName="Helvetica",
                                 fontSize=22, alignment=TA_CENTER,
                                 textColor=TEXT_SOFT, leading=24)

    grid_data = []
    for row in LO_SHU_LAYOUT:
        cells = []
        for n in row:
            # counts dict may have str or int keys depending on JSON path
            c = counts.get(n, counts.get(str(n), 0)) or 0
            try:
                c = int(c)
            except (TypeError, ValueError):
                c = 0
            if c == 0:
                cells.append([Paragraph("—", miss_style)])
            elif c == 1:
                cells.append([Paragraph(str(n), digit_style)])
            else:
                # Show digit + small count badge below
                cells.append([
                    Paragraph(str(n), digit_style),
                    Paragraph(f"× {c}", count_style),
                ])
        grid_data.append(cells)
    gt = Table(grid_data, colWidths=[24 * mm] * 3, rowHeights=[24 * mm] * 3,
               hAlign="LEFT")
    gt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_GRID),
        ("BOX", (0, 0), (-1, -1), 1.2, BRAND_PURPLE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BRAND_PURPLE),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    side = []
    side.append(Paragraph(
        f"<b>Present:</b> {', '.join(str(n) for n in grid.get('present_numbers') or []) or '—'}",
        s["body"]))
    side.append(Paragraph(
        f"<b>Missing:</b> {', '.join(str(n) for n in grid.get('missing_numbers') or []) or '—'}",
        s["body"]))
    side.append(Spacer(1, 3 * mm))
    if grid.get("complete_planes"):
        side.append(Paragraph(
            f"<b>Complete planes:</b> {', '.join(grid['complete_planes'])}",
            s["body"]))
    if grid.get("missing_planes"):
        side.append(Paragraph(
            f"<b>Missing planes:</b> {', '.join(grid['missing_planes'])}",
            s["body"]))

    layout = Table([[gt, side]], colWidths=[78 * mm, 100 * mm])
    layout.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    out.append(layout)
    out.append(Spacer(1, 6 * mm))

    # Repeated meanings
    if grid.get("repeated_meanings"):
        out.append(Paragraph("<b>Strengths (repeated digits):</b>", s["h3"]))
        for r in grid["repeated_meanings"]:
            out.append(Paragraph(
                f"• <b>{r.get('number')}</b> ({r.get('count')}×) — {r.get('trait','')}",
                s["body"]))
        out.append(Spacer(1, 3 * mm))

    # Missing meanings
    if grid.get("missing_meanings"):
        out.append(Paragraph("<b>Develop (missing digits):</b>", s["h3"]))
        for r in grid["missing_meanings"]:
            out.append(Paragraph(
                f"• <b>{r.get('number')}</b> — {r.get('missing','')}",
                s["body"]))
    return out


def _identity(s, ex: dict) -> List[Any]:
    out: List[Any] = []
    out.append(_section_title(s, "3. Identity & Karma Numbers"))
    out.append(Paragraph(
        "Life-Path comes from your full DOB. Soul-Urge / Personality / Expression "
        "are derived from your full birth name (Pythagorean alphabet).",
        s["body_mid"]))
    out.append(Spacer(1, 4 * mm))

    lp = (ex.get("life_path") or {}) if isinstance(ex, dict) else {}
    nt = (ex.get("name_triad") or {}) if isinstance(ex, dict) else {}
    mn = (ex.get("master_numbers") or {}) if isinstance(ex, dict) else {}
    kd = (ex.get("karmic_debt") or {}) if isinstance(ex, dict) else {}
    cp = (ex.get("compound") or {}) if isinstance(ex, dict) else {}

    lp_num = lp.get("life_path", "—")
    lp_extra = " (master)" if lp.get("is_master") else ""
    bday = lp.get("birthday_number")
    bday_root = lp.get("birthday_root")
    bday_str = f"{bday} → root {bday_root}" if bday is not None else "—"

    out.append(_label_value_table([
        ("Life-Path Number", f"{lp_num}{lp_extra}"),
        ("Birthday Number", bday_str),
        ("Soul-Urge (vowels)", _safe(nt.get("soul_urge", "—"))),
        ("Personality (consonants)", _safe(nt.get("personality", "—"))),
        ("Expression (full name)", _safe(nt.get("expression", "—"))),
        ("Alphabet system", _safe(nt.get("alphabet", ""))),
    ]))
    out.append(Spacer(1, 4 * mm))

    # Master numbers
    if mn.get("has_master"):
        out.append(Paragraph("<b>Master Numbers Detected:</b>", s["h3"]))
        # Build {number: meaning} from meanings list
        meanings_map = {m.get("number"): m.get("meaning", "")
                        for m in (mn.get("meanings") or []) if isinstance(m, dict)}
        for occ in (mn.get("occurrences") or []):
            if not isinstance(occ, dict):
                continue
            val = occ.get("value")
            src = occ.get("source", "")
            mng = meanings_map.get(val, "")
            out.append(Paragraph(
                f"• <b>{val}</b> ({src}) — {mng}",
                s["body"]))
    else:
        out.append(Paragraph("<b>Master Numbers:</b> none detected.", s["body_mid"]))
    out.append(Spacer(1, 3 * mm))

    # Karmic debt
    if kd.get("has_karmic_debt"):
        out.append(Paragraph("<b>Karmic Debt Numbers:</b>", s["h3"]))
        for k in (kd.get("debts") or []):
            if not isinstance(k, dict):
                continue
            out.append(Paragraph(
                f"• <b>{k.get('value','—')}</b> ({k.get('source','')}) — {k.get('meaning','')}",
                s["body"]))
    else:
        out.append(Paragraph("<b>Karmic Debt:</b> none detected.", s["body_mid"]))
    out.append(Spacer(1, 3 * mm))

    # Compound (Cheiro) — replace placeholder "Reduces normally" with proper fallback
    if cp.get("available"):
        def _cm(num, raw):
            if not raw or raw.strip().lower() in ("reduces normally", "reduces", ""):
                return cheiro_compound_fallback(num) or "—"
            return raw

        dob_n = cp.get("dob_compound")
        nm_n = cp.get("name_compound")
        out.append(Paragraph(
            f"<b>Cheiro Compound (DOB):</b> {dob_n if dob_n is not None else '—'} — "
            f"{_cm(dob_n, cp.get('dob_compound_meaning',''))}",
            s["body"]))
        out.append(Paragraph(
            f"<b>Cheiro Compound (Name):</b> {nm_n if nm_n is not None else '—'} — "
            f"{_cm(nm_n, cp.get('name_compound_meaning',''))}",
            s["body"]))
    return out


# ─── NEW: Detailed personality ("X number wale kaise hote hain") ──────

def _personality_block(s, role: str, num: int) -> List[Any]:
    """Render a deep personality block for one core number (Driver/Conductor/...)."""
    p = get_personality(num)
    out: List[Any] = []
    if not p:
        return out

    # Header band: "Your Driver Number is 5 · The Communicator"
    header = Table([[
        Paragraph(
            f"<font size='11'><b>Your {role} Number is</b></font>  "
            f"<font size='22' color='#F5B700'><b>{num}</b></font>  "
            f"<font size='11'><b>{p['title']}</b></font>",
            ParagraphStyle("ph", fontName="Helvetica", fontSize=11, leading=24,
                            textColor=colors.white))
    ]], colWidths=[180 * mm])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_PURPLE),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    out.append(header)
    out.append(Spacer(1, 1 * mm))
    out.append(Paragraph(p["headline"], s["headline"]))
    out.append(Spacer(1, 2 * mm))

    # Narrative paragraph (the WOW factor — "X number wale kaise hote hain")
    out.append(Paragraph(p["narrative"], s["narrative"]))
    out.append(Spacer(1, 3 * mm))

    # Two-column: Strengths | Weaknesses
    str_lines = "<br/>".join(f"✓  {x}" for x in p["strengths"])
    wk_lines = "<br/>".join(f"✗  {x}" for x in p["weaknesses"])
    sw = Table([[
        [Paragraph("<b>Aapki shaktiyaan (Strengths)</b>",
                   ParagraphStyle("swh", fontName="Helvetica-Bold", fontSize=10,
                                   textColor=ACCENT_GREEN, leading=13)),
         Paragraph(str_lines,
                   ParagraphStyle("swt", fontName="Helvetica", fontSize=9.5,
                                   textColor=TEXT_DARK, leading=14))],
        [Paragraph("<b>Dhyan rakhne wali baatein (Watch-outs)</b>",
                   ParagraphStyle("swh2", fontName="Helvetica-Bold", fontSize=10,
                                   textColor=ACCENT_RED, leading=13)),
         Paragraph(wk_lines,
                   ParagraphStyle("swt2", fontName="Helvetica", fontSize=9.5,
                                   textColor=TEXT_DARK, leading=14))],
    ]], colWidths=[88 * mm, 88 * mm])
    sw.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#ECFDF5")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FEF2F2")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    out.append(sw)
    out.append(Spacer(1, 3 * mm))

    # Famous people callout (huge social proof)
    fam = " ·  ".join(p["famous"])
    out.append(_callout_box(
        s,
        f"⭐  Aap jaise log (Number {num} wale famous personalities):",
        fam,
        colors.HexColor("#FFFBEB"),
        text_color=TEXT_DARK,
    ))
    out.append(Spacer(1, 3 * mm))

    # Career / Love / Health quick rows
    qr = _label_value_table([
        ("Career fit", p["career"]),
        ("Love & relationships", p["love"]),
        ("Wellness & lifestyle", p.get("wellness") or p.get("health", "—")),
        ("Best compatibility", ", ".join(str(x) for x in p["best_match"])),
        ("Avoid pairing with", ", ".join(str(x) for x in p["avoid_match"])),
    ], col_widths=[42 * mm, 138 * mm])
    out.append(qr)
    return out


def _personality_section(s, ps: dict, ex: dict) -> List[Any]:
    """Combined personality section for Driver + Conductor + Life-Path."""
    s1 = (ps.get("s1_numbers") or {}) if isinstance(ps, dict) else {}
    lp = (ex.get("life_path") or {}) if isinstance(ex, dict) else {}

    out: List[Any] = []
    out.append(_section_title(s, "Your Personality Deep-Dive"))
    out.append(Paragraph(
        "Yahan se shuru hota hai aapka asli numerology profile — har core "
        "number ke piche ek complete personality archetype, aur "
        "duniya ke famous log hote hain jo aap jaise hain.",
        s["body_mid"]))
    out.append(Spacer(1, 4 * mm))

    blocks_added = 0
    drv = s1.get("driver_mulank")
    cnd = s1.get("conductor_bhagyank")
    lp_n = lp.get("life_path")

    # Reduce life-path master numbers (11, 22, 33) to single digit for table lookup
    def _reduce(n):
        try:
            n = int(n)
            while n > 9:
                n = sum(int(d) for d in str(n))
            return n
        except (TypeError, ValueError):
            return None

    seen = set()
    for role, num in [("Driver (Mulank)", drv),
                       ("Conductor (Bhagyank)", cnd),
                       ("Life-Path", _reduce(lp_n))]:
        if num is None or num in seen:
            continue
        seen.add(num)
        if blocks_added > 0:
            out.append(Spacer(1, 6 * mm))
            # Page-break the second block to prevent crammed pages
            out.append(PageBreak())
        out += _personality_block(s, role, int(num))
        blocks_added += 1
    return out


# ─── NEW: Detailed remedies ───────────────────────────────────────────

def _remedies_section(s, ps: dict) -> List[Any]:
    """Practical habit stack for Driver and Conductor numbers (no occult remedies)."""
    from numerology.core.pure_numerology import PRACTICAL_CARD_LABELS, affirmations_pack

    s1 = (ps.get("s1_numbers") or {}) if isinstance(ps, dict) else {}
    out: List[Any] = []
    out.append(_section_title(s, "Practical Habits (Driver & Conductor)"))
    out.append(Paragraph(
        "Driver aur Conductor numbers ke liye step-by-step <b>practical habits</b> — "
        "routines, journaling, communication, sleep, budgeting, productivity, aur "
        "emotional awareness — practical behaviour only.",
        s["body_mid"]))
    out.append(Spacer(1, 4 * mm))

    drv = s1.get("driver_mulank")
    cnd = s1.get("conductor_bhagyank")

    rendered = set()
    for role, num in [("Driver", drv), ("Conductor", cnd)]:
        try:
            n = int(num)
        except (TypeError, ValueError):
            continue
        if n in rendered:
            continue
        rendered.add(n)
        p = get_personality(n)
        if not p:
            continue
        pack = affirmations_pack(n)

        out.append(Paragraph(
            f"<b>Habits for {role} Number {n}</b>  "
            f"<font color='#94A3B8'>· {p['title']}</font>",
            s["h3"]))
        rows = [("Affirmation", pack.get("affirmation", "—"))]
        for key, label, _, _ in PRACTICAL_CARD_LABELS:
            rows.append((label, pack.get(key, "—")))
        rows.append(("Daily focus", p.get("daily", "—")))
        out.append(_label_value_table(rows, col_widths=[40 * mm, 140 * mm]))
        out.append(Spacer(1, 5 * mm))

    out.append(_callout_box(
        s,
        "Note — behaviour change, not rituals:",
        "Yeh habits 21–90 din consistently try karein. Medical, legal, ya financial "
        "decisions ke liye qualified professionals se consult karein.",
        colors.HexColor("#F0FDF4"),
        text_color=colors.HexColor("#047857"),
    ))
    return out


def _cycles(s, ex: dict) -> List[Any]:
    pc = (ex.get("personal_cycles") or {}) if isinstance(ex, dict) else {}
    out: List[Any] = []
    out.append(_section_title(s, "4. Personal Cycles (Right Now)"))
    out.append(Paragraph(
        "Your live timing layer — these change yearly, monthly and daily, and "
        "indicate the dominant theme to plan around.",
        s["body_mid"]))
    out.append(Spacer(1, 4 * mm))
    next_y = pc.get("next_year_personal")
    next_y_str = f"  (next year: {next_y})" if next_y is not None else ""
    out.append(_label_value_table([
        ("Personal Year",
         f"{pc.get('personal_year','—')}  ·  {pc.get('personal_year_theme','')}{next_y_str}"),
        ("Personal Month",
         f"{pc.get('personal_month','—')}  ·  {pc.get('personal_month_theme','')}"),
        ("Personal Day",
         f"{pc.get('personal_day','—')}  ·  {pc.get('personal_day_theme','')}"),
        ("Reference date", _safe(pc.get("as_of", ""))),
    ]))
    return out


def _pinnacles(s, pr: dict) -> List[Any]:
    pc = (pr.get("pinnacles_challenges") or {}) if isinstance(pr, dict) else {}
    out: List[Any] = []
    out.append(_section_title(s, "5. Pinnacles & Challenges (Life Cycles)"))
    out.append(Paragraph(
        "Four pinnacles describe the dominant theme of each life-quarter. "
        "Four challenges describe the lesson to master in that same window.",
        s["body_mid"]))
    out.append(Spacer(1, 4 * mm))

    pinnacles = pc.get("pinnacles") or []
    challenges = pc.get("challenges") or []

    if pinnacles:
        out.append(Paragraph("<b>Pinnacles:</b>", s["h3"]))
        rows = [["Cycle", "Period", "#", "Theme"]]
        for p in pinnacles:
            rows.append([
                Paragraph(_safe(p.get("name")), s["body"]),
                Paragraph(_safe(p.get("period")), s["body"]),
                Paragraph(f"<b>{_safe(p.get('number'))}</b>", s["body"]),
                Paragraph(_safe(p.get("theme")), s["body"]),
            ])
        t = Table(rows, colWidths=[28 * mm, 36 * mm, 12 * mm, 102 * mm], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_PURPLE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
            ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        out.append(t)
        out.append(Spacer(1, 5 * mm))

    if challenges:
        out.append(Paragraph("<b>Challenges:</b>", s["h3"]))
        rows = [["Cycle", "Period", "#", "Lesson"]]
        for c in challenges:
            rows.append([
                Paragraph(_safe(c.get("name")), s["body"]),
                Paragraph(_safe(c.get("period")), s["body"]),
                Paragraph(f"<b>{_safe(c.get('number'))}</b>", s["body"]),
                Paragraph(_safe(c.get("theme")), s["body"]),
            ])
        t = Table(rows, colWidths=[28 * mm, 36 * mm, 12 * mm, 102 * mm], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_GOLD),
            ("TEXTCOLOR", (0, 0), (-1, 0), TEXT_DARK),
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
            ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        out.append(t)
    return out


def _career_recommendations(s, pr: dict) -> List[Any]:
    """Career fields from Driver/Conductor number psychology only."""
    out: List[Any] = []
    out.append(_section_title(s, "6. Career Recommendations"))

    cd = pr.get("career_recommendations_driver") or []
    cc = pr.get("career_recommendations_conductor") or []
    if cd or cc:
        out.append(Paragraph(
            "Fields below are filtered by your core numbers — work style and "
            "decision patterns, not birth charts or rituals.",
            s["body_mid"]))
        out.append(Spacer(1, 3 * mm))
        if cd:
            out.append(Paragraph(
                f"<b>By Driver number ({pr.get('driver', '—')}):</b> {', '.join(cd)}",
                s["body"]))
        if cc:
            out.append(Paragraph(
                f"<b>By Conductor number ({pr.get('conductor', '—')}):</b> {', '.join(cc)}",
                s["body"]))
        out.append(Spacer(1, 4 * mm))
    else:
        out.append(Paragraph(
            "Career recommendations will appear when practical profile data is available.",
            s["body_mid"]))
    return out


def _disclaimer(s) -> List[Any]:
    out: List[Any] = [Spacer(1, 6 * mm)]
    out.append(_section_title(s, "Important Notes"))
    out.append(Paragraph(
        "<b>How to use this report.</b> Numerology is a contemplative tool. "
        "Treat the indications here as <i>tendencies and timing windows</i>, "
        "not as guarantees. Combine them with effort, ethical conduct and "
        "professional advice in legal, medical or financial matters.",
        s["body"]))
    out.append(Spacer(1, 3 * mm))
    out.append(Paragraph(
        "<b>Birth-name accuracy.</b> Soul-Urge, Personality and Expression "
        "numbers depend on the exact spelling of your full birth name as "
        "registered. If your name was changed later, results from the new "
        "name reflect the persona you project, not your karmic blueprint.",
        s["body"]))
    out.append(Spacer(1, 3 * mm))
    out.append(Paragraph(
        "<b>Personal cycles.</b> Personal Year, Month, and Day themes shift on each "
        "rollover. Use them as planning windows — not as fixed predictions.",
        s["body"]))
    return out


# ─── Public entry ────────────────────────────────────────────────────

# ─── Tier-A enrichment sections (karmic + passion + maturity + compat) ─────

def _karmic_passion_maturity(s, name: str, dob: str, phase_s: dict, extended: dict) -> List[Any]:
    """One-page deep-dive: Karmic Lessons + Hidden Passion + Maturity Number."""
    from numerology.core import tier_a as _ta

    flow: List[Any] = []
    flow.append(_section_title(s, "Karmic Lessons & Hidden Talents"))
    flow.append(Paragraph(
        "Aapke naam aur janma-tithi se nikle 3 deep insights — jo aapki "
        "long-term growth pattern dikhate hain.",
        s["body_mid"]))
    flow.append(Spacer(1, 5 * mm))

    # 1. Karmic lessons
    klr = _ta.karmic_lessons(name)
    if klr.get("ok"):
        missing = klr.get("missing_numbers") or []
        flow.append(Paragraph("<b>Karmic Lessons</b> — soul ne is janam me ye seekhne aaya hai:",
                              s["h3"]))
        if missing:
            for item in klr.get("lessons") or []:
                flow.append(Paragraph(
                    f"<b>{item['number']}.</b> {item['lesson']}", s["body"]))
        else:
            flow.append(Paragraph(
                "Aapke naam me sabhi 1-9 numbers represent hain — balanced soul, "
                "no specific karmic lesson uthane ki zaroorat.", s["body"]))
        flow.append(Spacer(1, 4 * mm))

    # 2. Hidden Passion
    hpr = _ta.hidden_passion(name)
    if hpr.get("ok"):
        dom = hpr.get("dominant_numbers") or []
        flow.append(Paragraph(
            f"<b>Hidden Passion</b> — Number(s) <b>{', '.join(str(n) for n in dom)}</b> "
            "aapke naam me sabse jyada baar aate hain. Yeh aapke natural talents hain:",
            s["h3"]))
        for item in hpr.get("meanings") or []:
            flow.append(Paragraph(f"<b>{item['number']}.</b> {item['passion']}", s["body"]))
        flow.append(Paragraph(
            "<i>Career, hobbies, business — inhi vibrations ke around build karne se "
            "max success milegi.</i>", s["body_mid"]))
        flow.append(Spacer(1, 4 * mm))

    # 3. Maturity Number
    try:
        # Pull life_path from extended (preferred) else compute
        lp = (extended.get("life_path") or {}).get("number") if isinstance(extended.get("life_path"), dict) else extended.get("life_path")
        ex = (extended.get("expression") or {}).get("number") if isinstance(extended.get("expression"), dict) else extended.get("expression")
        if not lp or not ex:
            # Fallback: compute from dob + name
            from numerology.core.extended import _PYTH
            digits = [int(c) for c in dob if c.isdigit()]
            lp_raw = sum(digits)
            while lp_raw > 9 and lp_raw not in (11, 22, 33):
                lp_raw = sum(int(d) for d in str(lp_raw))
            lp = lp_raw
            letters = "".join(c for c in name.lower() if c.isalpha())
            ex_raw = sum(_PYTH.get(c, 0) for c in letters)
            while ex_raw > 9 and ex_raw not in (11, 22, 33):
                ex_raw = sum(int(d) for d in str(ex_raw))
            ex = ex_raw

        mat = _ta.maturity_number(int(lp or 0), int(ex or 0))
        if mat.get("ok"):
            flow.append(Paragraph("<b>Maturity Number</b> — late-life dominant theme:", s["h3"]))
            flow.append(_callout_box(
                s,
                f"Maturity Number: {mat.get('maturity')} "
                f"({mat.get('archetype') or mat.get('planet') or '—'})",
                f"{mat.get('meaning','')}<br/><br/>"
                f"<i>Activates around age 30-35.</i> Life-path {lp} + Expression {ex} = {mat.get('raw_sum')}.",
                colors.HexColor("#FFF4E6"),
            ))
    except Exception:
        pass

    return flow


def _compatibility_section(s, user_dob: str, partner_dob: str,
                            partner_name: str | None, kind: str) -> List[Any]:
    """Optional compatibility report — only if partner_dob provided."""
    from numerology.core import tier_a as _ta
    flow: List[Any] = []
    out = _ta.compatibility(user_dob, partner_dob, kind=kind)
    if not out.get("ok"):
        return flow

    title = "Compatibility Report — Love" if kind == "love" else "Compatibility Report — Business"
    flow.append(_section_title(s, title))
    pname = partner_name or "Partner"
    flow.append(Paragraph(
        f"Aap ({user_dob}) aur <b>{pname}</b> ({partner_dob}) ke beech ki "
        "vibrational compatibility — Driver, Conductor aur Life-Path par.",
        s["body_mid"]))
    flow.append(Spacer(1, 4 * mm))

    # Overall score callout
    overall = out.get("overall_score", 0)
    verdict = out.get("verdict", "")
    bg = (colors.HexColor("#D4EDDA") if overall >= 60
          else colors.HexColor("#FFF3CD") if overall >= 45
          else colors.HexColor("#F8D7DA"))
    flow.append(_callout_box(
        s,
        f"Overall Compatibility: {overall}/100 — {verdict}",
        out.get("advice", ""),
        bg,
    ))
    flow.append(Spacer(1, 4 * mm))

    # Per-axis breakdown
    rows = [["Axis", "You", "Partner", "Score", "Type"]]
    for axis_name in ("driver", "conductor", "life_path"):
        ax = (out.get("axes") or {}).get(axis_name) or {}
        rows.append([
            axis_name.replace("_", " ").title(),
            str(ax.get("p1", "—")),
            str(ax.get("p2", "—")),
            f"{ax.get('score', 0)}/100",
            ax.get("label", "—"),
        ])
    t = Table(rows, colWidths=[35*mm, 25*mm, 30*mm, 25*mm, 35*mm])
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
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 3 * mm))
    flow.append(Paragraph(
        "<i>Note: Numerology is one indicator among many. Use it alongside "
        "honest conversation, shared values, and professional advice where needed.</i>",
        s["small"]))
    return flow


# ─── NEW Part 1 sections (T105: 5 extra pages for ₹99 value) ───────────

# Per-driver data tables
_DAILY_CLOCK = {
    1: ("5:30 AM", "9 AM – 11 AM (focus block)", "Sunrise — light cardio",
        "Morning — 3-line intention journal", "10:30 PM"),
    2: ("6:00 AM", "7 PM – 9 PM (reflection block)", "6:30 PM — gentle yoga/swim",
        "Evening — mood + energy log", "11:00 PM"),
    3: ("5:45 AM", "10 AM – 12 PM (creative block)", "7 AM — walk + idea capture",
        "Thursday — teach or share one insight", "10:00 PM"),
    4: ("5:15 AM", "6 AM – 8 AM (deep-work block)", "Dawn — long brisk walk",
        "Early AM — checklist + top task", "11:00 PM"),
    5: ("6:00 AM", "11 AM – 1 PM (communication block)", "Sunset — varied cardio",
        "Midday — batch messages/calls", "11:30 PM"),
    6: ("6:30 AM", "4 PM – 6 PM (relationship block)", "Evening — dance/yoga/sports",
        "Dusk — gratitude note to one person", "11:00 PM"),
    7: ("4:30 AM", "4 AM – 6 AM (quiet focus)", "Pre-dawn slow walk",
        "Pre-dawn — silent reading 30 min", "9:30 PM"),
    8: ("5:00 AM", "7 PM – 9 PM (execution block)", "Dawn — strength training",
        "Saturday — money snapshot review", "10:30 PM"),
    9: ("5:30 AM", "6 AM – 8 AM (action block)", "Dawn — high-intensity cardio",
        "Tuesday — anger-trigger journal review", "10:30 PM"),
}

_AUTO_COMPAT = {
    1: ("1, 4, 8 (driven match)", "2 (gentle complement)",
        "6 (luxury vs leadership clash)",
        "4, 8 (executors & builders)", "3 (lacks discipline)"),
    2: ("2, 4, 7 (sensitive match)", "6, 9 (caring complement)",
        "5 (chaos overwhelms)",
        "6, 9 (sales & operations)", "8 (dominator)"),
    3: ("3, 6, 9 (joy match)", "1 (mentor pair)",
        "4 (rigid vs free)",
        "1, 9 (vision & expansion)", "5 (scattered focus)"),
    4: ("1, 5, 7 (stability match)", "8 (long-term builder)",
        "6 (luxury bias clashes)",
        "1, 8 (long-game builders)", "9 (aggressive pace)"),
    5: ("1, 5, 9 (movement match)", "6 (charm complement)",
        "2 (clingy energy)",
        "6, 9 (charm & drive)", "7 (introverted pace)"),
    6: ("3, 6, 9 (love match)", "2 (caring partner)",
        "1 (ego dominates)",
        "2, 9 (people-focused)", "7 (loner mismatch)"),
    7: ("2, 4, 7 (depth match)", "1 (anchoring complement)",
        "5 (surface energy)",
        "4, 8 (research & finance)", "3 (showy distraction)"),
    8: ("4, 8, 1 (power match)", "6 (sensual balance)",
        "9 (volatile clash)",
        "1, 4 (long-term scale)", "2 (over-emotional)"),
    9: ("3, 6, 9 (passion match)", "1 (warrior pair)",
        "8 (clash of titans)",
        "3, 5 (fast pace)", "4 (slow pace mismatch)"),
}

_FINANCIAL_PROFILE = {
    1: (
        "7/10 — Strong when you control terms and keep a 6-month buffer",
        "Ownership = autonomy — prefers sole title, clear equity",
        "Equity & leadership assets; reinvests in scalable income",
        "Moderate-high — needs written downside limits",
        "Security via appreciating assets + income you direct personally",
    ),
    2: (
        "8/10 — Stable with joint planning and documented agreements",
        "Ownership = shared safety — co-ownership OK if roles are explicit",
        "Rental yield, balanced funds, family-backed property",
        "Low-moderate — avoids solo speculation",
        "Security via diversified reserves and partner-aligned deeds",
    ),
    3: (
        "6/10 — Stable when cash-flow is tracked monthly",
        "Ownership = lifestyle stage — values light, social neighbourhoods",
        "Mix of growth funds + work-from-home-friendly home",
        "Moderate — cap discretionary property spend",
        "Security via content/teaching income + moderate leverage",
    ),
    4: (
        "9/10 — Excellent with systems, inspections, fixed-rate debt",
        "Ownership = foundation — slow buys, long hold",
        "Index funds, REITs, boring rentals with positive cash-flow",
        "Low — needs stress-tested EMI scenarios",
        "Security via paid-down principal and repair fund",
    ),
    5: (
        "5/10 — Volatile unless trading rules and caps are enforced",
        "Ownership = flexibility — may prefer rent + invest surplus",
        "Trading accounts, thematic funds, short-lease commercial",
        "High — mandatory cool-off periods on risk",
        "Security via liquid reserves; avoid over-leveraged flips",
    ),
    6: (
        "7/10 — Stable when aesthetics don't override affordability",
        "Ownership = family hub — quality neighbourhood, upkeep budget",
        "Balanced portfolio, home + conservative debt funds",
        "Low-moderate — 48-hour pause on emotional purchases",
        "Security via insured home + steady SIP alongside mortgage",
    ),
    7: (
        "6/10 — Stable with minimalist footprint and low fixed costs",
        "Ownership = sanctuary — privacy over size",
        "Bonds, index ETFs, niche assets you understand deeply",
        "Low — prefers under-leveraged holds",
        "Security via low fixed obligations and long emergency runway",
    ),
    8: (
        "8/10 — Strong with long horizons and professional legal review",
        "Ownership = legacy asset — scale and structure",
        "Real assets, infrastructure, large-cap compounders",
        "Moderate — diversify; avoid over-concentration",
        "Security via staggered maturities and clear legal structure",
    ),
    9: (
        "6/10 — Stable when aggression uses insured, legal structures",
        "Ownership = status + utility — wants clear title",
        "Growth equity, business property, capped high-conviction bets",
        "High — hard stop-loss on leverage",
        "Security via insured assets + separate reserve account",
    ),
}

_PY_THEMES = {
    1: ("New beginnings, leadership, fresh launches",
        "Mar, Sep", "Nov–Dec", "1, 10, 19, 28",
        "Start the project you've delayed", "Don't wait for perfect conditions"),
    2: ("Patience, partnerships, diplomacy",
        "Jun, Aug", "Jan–Feb", "2, 11, 20, 29",
        "Collaborate, find your co-founder", "Don't push hard or rush decisions"),
    3: ("Creativity, expression, social expansion",
        "May, Sep", "Feb", "3, 12, 21, 30",
        "Publish, network, perform", "Don't isolate or self-doubt"),
    4: ("Foundation building, hard work, systems",
        "Apr, Aug", "Sep", "4, 13, 22, 31",
        "Build the system, document everything", "Don't quit when it gets boring"),
    5: ("Change, travel, freedom, new experiences",
        "Mar, Jul, Nov", "Apr", "5, 14, 23",
        "Travel, switch jobs, learn skills", "Don't sign long-term contracts"),
    6: ("Family, duty, healing, home",
        "Jun, Oct", "Jul", "6, 15, 24",
        "Repair relationships, build the home", "Don't take on others' burdens"),
    7: ("Introspection, study, research, retreat",
        "Jul, Nov", "Mar–Apr", "7, 16, 25",
        "Read, retreat, deepen one skill", "Don't launch big public moves"),
    8: ("Power, money, execution, harvest",
        "Aug, Oct", "May", "8, 17, 26",
        "Negotiate raises, close big deals", "Don't ignore health for hustle"),
    9: ("Completion, release, generosity, closure",
        "Sep, Dec", "Jun", "9, 18, 27",
        "Close loops, give back, mentor", "Don't start anything brand new"),
}


def _personal_year(dob: str, year: int) -> int:
    parts = dob.split("-")
    try:
        m, d = int(parts[1]), int(parts[2])
    except (IndexError, ValueError):
        return 0
    n = sum(int(c) for c in str(year)) + m + d
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(c) for c in str(n))
    return n if n <= 9 else (1 + (n - 1) % 9)


def _section_title2(s, text: str):
    return Paragraph(text, s["page_title"])


def _kv_table(rows: List[tuple], col_widths=None) -> Table:
    """Two-column label/value rows with brand styling."""
    cw = col_widths or [55 * mm, 125 * mm]
    t = Table(rows, colWidths=cw)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (0, -1), BG_GRID),
        ("TEXTCOLOR",    (0, 0), (0, -1), BRAND_PURPLE),
        ("FONTNAME",     (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",     (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9.5),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("BOX",          (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEBELOW",    (0, 0), (-1, -2), 0.3, BORDER),
    ]))
    return t


def _year_ahead_section(s, lang: str, dob: str, driver: int) -> List[Any]:
    """Current Personal Year mood-map: theme, peak/slow months, focus dates."""
    flow: List[Any] = []
    yr = datetime.now().year
    py = _personal_year(dob, yr) or driver
    theme, peak, slow, dates, do_, dont = _PY_THEMES.get(py, _PY_THEMES[1])
    flow.append(_section_title2(s, _T(lang,
        f"🗓️ Year Ahead — Personal Year {py} ({yr})",
        f"🗓️ आगामी वर्ष — Personal Year {py} ({yr})",
        f"🗓️ Year Ahead — Personal Year {py} ({yr})")))
    flow.append(Spacer(1, 3 * mm))
    flow.append(_kv_table([
        [_T(lang, "Year Theme", "वर्ष का विषय", "Year Theme"), theme],
        [_T(lang, "Peak Months", "शिखर महीने", "Peak Months"), peak],
        [_T(lang, "Slow Months", "धीमे महीने", "Slow Months"), slow],
        [_T(lang, "Focus Dates", "फोकस-तिथियाँ", "Focus Dates"), dates],
        [_T(lang, "✅ Do This Year", "✅ इस वर्ष करें", "✅ Do This Year"), do_],
        [_T(lang, "❌ Avoid This Year", "❌ इस वर्ष टालें", "❌ Avoid This Year"), dont],
    ]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_explain_card(s, lang,
        f"📖 What is a Personal Year and why does it shift everything?",
        f"📖 Personal Year क्या है और यह सब क्यों बदल देता है?",
        f"📖 Personal Year kya hai aur ye sab kyu badal deta hai?",
        "Your <b>Personal Year</b> is calculated from birth-month + birth-day + "
        "current year — a 1→9 cycle that resets every nine years. Each year has a "
        "<b>momentum theme</b>: aligned actions feel easier; mis-timed pushes create "
        "friction. Use <b>peak months</b> for decisions and launches, <b>slow months</b> "
        "for planning and recovery, and <b>focus dates</b> for signing or key meetings.",
        "<b>Personal Year</b> जन्म-माह + जन्म-तिथि + वर्तमान वर्ष से निकलता है — "
        "हर नौ वर्ष में रीसेट होने वाला 1→9 चक्र। प्रत्येक वर्ष का <b>गति-विषय</b> "
        "होता है: संरेखित कार्य आसान, विरुद्ध कार्य घर्षण। <b>शिखर महीने</b> में "
        "निर्णय/लॉन्च, <b>धीमे महीने</b> में योजना/विश्राम, <b>फोकस-तिथियों</b> पर "
        "हस्ताक्षर या महत्वपूर्ण मीटिंग।",
        "<b>Personal Year</b> birth-month + birth-day + current year se — har 9 saal "
        "me reset hone wala 1→9 cycle. Har year ka <b>momentum theme</b>: aligned kaam "
        "easy, against kaam friction. <b>Peak months</b> me decisions/launch, "
        "<b>slow months</b> me planning/recovery, <b>focus dates</b> par sign ya "
        "key meetings."))
    return flow


def _auto_compat_section(s, lang: str, driver: int) -> List[Any]:
    """Quick compatibility card — best/avoid for marriage and business."""
    flow: List[Any] = []
    best_m, alt_m, avoid_m, best_b, avoid_b = _AUTO_COMPAT.get(driver, _AUTO_COMPAT[1])
    flow.append(_section_title2(s, _T(lang,
        "💑 Quick Compatibility — Marriage & Business",
        "💑 त्वरित अनुकूलता — विवाह और व्यापार",
        "💑 Quick Compatibility — Marriage & Business")))
    flow.append(Paragraph(_T(lang,
        f"Based on your Driver {driver} — these are the numbers most likely to "
        f"create harmony or friction. Check the <b>birth-day</b> of your partner / "
        f"co-founder / boss to predict the chemistry.",
        f"आपके Driver {driver} के आधार पर — ये अंक सामंजस्य या घर्षण उत्पन्न करते हैं। "
        f"साथी / सह-संस्थापक / बॉस की <b>जन्म-तिथि</b> देखें केमिस्ट्री का अनुमान लगाएँ।",
        f"Aapke Driver {driver} ke based — ye numbers harmony ya friction create karte "
        f"hain. Apne partner / co-founder / boss ki <b>birth-day</b> dekho chemistry "
        f"predict karne ke liye."), s["body_mid"]))
    flow.append(Spacer(1, 3 * mm))
    flow.append(_kv_table([
        [_T(lang, "💍 Marriage — Best", "💍 विवाह — सर्वश्रेष्ठ", "💍 Marriage — Best"), best_m],
        [_T(lang, "💍 Marriage — Also Good", "💍 विवाह — अच्छा", "💍 Marriage — Also Good"), alt_m],
        [_T(lang, "💍 Marriage — Avoid", "💍 विवाह — टालें", "💍 Marriage — Avoid"), avoid_m],
        [_T(lang, "🤝 Business — Best", "🤝 व्यापार — सर्वश्रेष्ठ", "🤝 Business — Best"), best_b],
        [_T(lang, "🤝 Business — Avoid", "🤝 व्यापार — टालें", "🤝 Business — Avoid"), avoid_b],
    ]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_explain_card(s, lang,
        "📖 Why number-compatibility predicts relationship friction",
        "📖 अंक-अनुकूलता रिश्तों का घर्षण क्यों भविष्यवाणी करती है",
        "📖 Number-compatibility kyu relationship friction predict karti hai",
        "Two people with <b>compatible Drivers</b> tend to share pace, priorities, "
        "and conflict style — conversations flow, decisions feel mutual. "
        "<b>Incompatible Drivers</b> can still work with clear roles and written "
        "agreements, but daily friction costs more energy. <b>Marriage</b> — check "
        "values and emotional rhythm (Driver). <b>Business</b> — check execution and "
        "risk style (Conductor). Use this card before saying yes — partner, co-founder, "
        "or boss.",
        "<b>संगत Drivers</b> वाले लोग अक्सर गति, प्राथमिकताएँ और संघर्ष-शैली साझा "
        "करते हैं — बातचीत बहती है, निर्णय परस्पर लगते हैं। <b>असंगत Drivers</b> स्पष्ट "
        "भूमिकाओं और लिखित समझौतों से चल सकते हैं, पर दैनिक घर्षण अधिक ऊर्जा लेता है। "
        "<b>विवाह</b> — मूल्य और भावनात्मक लय (Driver)। <b>व्यापार</b> — निष्पादन और "
        "जोखिम शैली (Conductor)। हाँ कहने से पहले यह कार्ड देखें।",
        "Do log jinke <b>compatible Drivers</b> hon, unka pace, priorities aur conflict "
        "style match hota hai — baat-cheet flow karti hai. <b>Incompatible Drivers</b> "
        "clear roles + written agreements se chal sakte hain, par daily friction zyada "
        "energy leti hai. <b>Marriage</b> — values + emotional rhythm (Driver). "
        "<b>Business</b> — execution + risk (Conductor). Haan kehne se pehle ye card "
        "dekho."))
    return flow


def _daily_clock_section(s, lang: str, driver: int) -> List[Any]:
    """24-hour productivity rhythm — habit timing, not planetary hours."""
    flow: List[Any] = []
    wake, peak, ex, med, sleep = _DAILY_CLOCK.get(driver, _DAILY_CLOCK[1])
    flow.append(_section_title2(s, _T(lang,
        "⏰ Daily Productivity Rhythm",
        "⏰ दैनिक उत्पादकता लय",
        "⏰ Daily Productivity Rhythm")))
    flow.append(Paragraph(_T(lang,
        f"Driver {driver} suggests when your focus, movement, and wind-down "
        f"windows tend to work best — use as a routine template, not a ritual rule.",
        f"Driver {driver} बताता है फ़ोकस, गतिविधि और विश्राम की खिड़कियाँ कब "
        f"सबसे अच्छी चलती हैं — दिनचर्या खाका के रूप में, अनुष्ठान नियम नहीं।",
        f"Driver {driver} batata hai focus, movement aur wind-down kab best "
        f"chalti hain — routine template ki tarah, ritual rule nahi."), s["body_mid"]))
    flow.append(Spacer(1, 3 * mm))
    flow.append(_kv_table([
        [_T(lang, "🌅 Wake Up", "🌅 जागें", "🌅 Wake Up"), wake],
        [_T(lang, "⚡ Peak Productivity", "⚡ शिखर उत्पादकता", "⚡ Peak Productivity"), peak],
        [_T(lang, "🏃 Exercise Window", "🏃 व्यायाम समय", "🏃 Exercise Window"), ex],
        [_T(lang, "🧘 Meditation Window", "🧘 ध्यान समय", "🧘 Meditation Window"), med],
        [_T(lang, "🌙 Sleep By", "🌙 सोएँ", "🌙 Sleep By"), sleep],
    ]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_explain_card(s, lang,
        "📖 Why a fixed daily rhythm beats random hustle",
        "📖 निश्चित दिनचर्या यादृच्छिक भागदौड़ से क्यों बेहतर है",
        "📖 Fixed daily rhythm random hustle se kyu better hai",
        "Consistency compounds more than motivation spikes. Block your <b>peak "
        "focus window</b> for deep work, protect sleep, and batch communication "
        "outside that block. Treat this page as a <b>template to test for 21 days</b> — "
        "adjust by 30 minutes if your job schedule demands it.",
        "निरंतरता प्रेरणा की तुलना में अधिक चक्रवृद्धि करती है। <b>शिखर फ़ोकस "
        "खिड़की</b> गहन कार्य के लिए रखें, नींद सुरक्षित रखें, संचार उसके बाहर "
        "बैच करें। इस पृष्ठ को <b>21 दिन के परीक्षण-खाका</b> मानें — नौकरी के अनुसार "
        "30 मिनट समायोजित कर सकते हैं।",
        "Consistency motivation spikes se zyada compound karti hai. <b>Peak focus "
        "window</b> deep work ke liye block karo, sleep protect karo, communication "
        "uske bahar batch karo. Is page ko <b>21 din test template</b> samjho — "
        "job schedule ke hisaab se 30 min adjust kar sakte ho."))
    return flow


def _financial_profile_section(s, lang: str, driver: int) -> List[Any]:
    """Money & property psychology — no chakra or compass concepts."""
    flow: List[Any] = []
    stability, ownership, invest, risk, security = _FINANCIAL_PROFILE.get(
        driver, _FINANCIAL_PROFILE[1])
    flow.append(_section_title2(s, _T(lang,
        "💰 Financial & Ownership Psychology",
        "💰 वित्तीय और स्वामित्व मनोविज्ञान",
        "💰 Financial & Ownership Psychology")))
    flow.append(Paragraph(_T(lang,
        f"Driver {driver} shapes how you earn, own, and tolerate risk — use these "
        f"patterns for budgets, deeds, and investment rules.",
        f"Driver {driver} तय करता है आप कैसे कमाते, स्वामित्व लेते, और जोखिम सहते हैं — "
        f"बजट, दस्तावेज़, और निवेश-नियमों के लिए इन पैटर्न का उपयोग करें।",
        f"Driver {driver} batata hai aap kaise earn, own, aur risk tolerate karte ho — "
        f"budgets, deeds, aur investment rules ke liye ye patterns use karo."),
        s["body_mid"]))
    flow.append(Spacer(1, 3 * mm))
    flow.append(_kv_table([
        [_T(lang, "📊 Financial stability score", "📊 वित्तीय स्थिरता स्कोर",
            "📊 Financial stability score"), stability],
        [_T(lang, "🏠 Ownership psychology", "🏠 स्वामित्व मनोविज्ञान",
            "🏠 Ownership psychology"), ownership],
        [_T(lang, "📈 Investment behavior", "📈 निवेश व्यवहार",
            "📈 Investment behavior"), invest],
        [_T(lang, "⚖️ Risk tolerance", "⚖️ जोखिम सहनशीलता",
            "⚖️ Risk tolerance"), risk],
        [_T(lang, "🔒 Long-term security", "🔒 दीर्घकालिक सुरक्षा",
            "🔒 Long-term security"), security],
    ]))
    flow.append(Spacer(1, 4 * mm))
    flow.append(_explain_card(s, lang,
        "📖 Match money moves to your number psychology",
        "📖 धन-निर्णय अंक-मनोविज्ञान से मिलाएँ",
        "📖 Money moves ko number psychology se match karo",
        "Say yes to income channels and property structures that fit your row above. "
        "When stability score is below 7/10, build cash reserves before upgrading "
        "lifestyle. Pair with the Life Mastery property section for purchase timing "
        "via Personal Year — not compass direction.",
        "ऊपर की पंक्तियों से मेल खाने वाले आय-चैनल और संपत्ति-संरचना को हाँ कहें। "
        "स्थिरता 7/10 से कम हो तो जीवनशैली अपग्रेड से पहले नकदी-रिज़र्व बनाएँ। "
        "ख़रीद-समय के लिए Life Mastery में Personal Year देखें — दिशा नहीं।",
        "Upar ki rows se match hone wale income channels aur property structures "
        "ko haan bolo. Stability 7/10 se kam ho to lifestyle upgrade se pehle cash "
        "reserve banao. Purchase timing ke liye Life Mastery me Personal Year dekho — "
        "compass direction nahi."))
    return flow


def render_numerology_pdf(*,
                          name: str,
                          dob: str,
                          gender: str | None,
                          phase_s: dict,
                          extended: dict,
                          practical: dict,
                          partner_dob: str | None = None,
                          partner_name: str | None = None,
                          compat_kind: str = "love",
                          lang: str = "hinglish") -> bytes:
    """Render a multi-page numerology PDF. Returns the PDF binary.

    Optional partner_dob enables a compatibility section.
    """
    s = _styles(lang)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=18 * mm, bottomMargin=20 * mm,
                            title=f"Soul Blueprint Report — {name}",
                            author="Cosmic Lens")
    story: List[Any] = []
    story += _cover(s, name, dob, gender)
    story.append(PageBreak())

    # ─── Executive Summary (TL;DR — top of report, addresses overwhelm) ───
    try:
        story += _executive_summary(s, name, lang, phase_s, extended, practical)
        story.append(PageBreak())
    except Exception:
        # Never let TL;DR failure block the rest of the report
        pass

    story += _core_numbers(s, phase_s)
    story.append(Spacer(1, 4 * mm))
    story.append(_explain_card(s, lang,
        "📖 Why these 'core numbers' matter most",
        "📖 ये 'मूल अंक' सबसे अधिक क्यों मायने रखते हैं",
        "📖 Ye 'core numbers' sabse zyada kyu matter karte hain",
        "Your <b>Driver</b> (birth-day reduced) shows the role you play <b>by default</b> — "
        "the energy that drives daily decisions. Your <b>Conductor</b> (full DOB reduced) "
        "is the <b>life-purpose layer</b> — the destination behind every decision. "
        "<b>Name number</b> shows how the <b>world receives you</b> (first impression, "
        "branding). When all three align, life feels effortless; when they clash, "
        "you feel pulled in different directions. Read these as the <b>3-axis compass</b> "
        "of your blueprint — every section ahead is downstream of these three numbers.",
        "आपका <b>Driver</b> (जन्म-तिथि कम करके) वह भूमिका है जो आप <b>स्वाभाविक रूप से</b> "
        "निभाते हैं — दैनिक निर्णयों की ऊर्जा। <b>Conductor</b> (पूरी DOB कम करके) "
        "<b>जीवन-उद्देश्य</b> है — हर निर्णय के पीछे की मंज़िल। <b>नाम अंक</b> दिखाता है "
        "<b>दुनिया आपको कैसे देखती है</b> (पहला प्रभाव, ब्रांडिंग)। तीनों सही दिशा में हों "
        "तो जीवन सहज; टकराव हो तो खिंचाव महसूस होता है। इन्हें ब्लूप्रिंट के <b>3-अक्ष कम्पास</b> "
        "की तरह पढ़ें — आगे के सभी खंड इन्हीं तीन अंकों से निकलते हैं।",
        "Aapka <b>Driver</b> (birthday reduced) wo role hai jo aap <b>by default</b> play "
        "karte ho — daily decisions ki energy. <b>Conductor</b> (full DOB reduced) "
        "<b>life-purpose layer</b> hai — har decision ke peeche ki destination. "
        "<b>Name number</b> dikhata hai <b>world aapko kaise receive karti hai</b> "
        "(first impression, branding). Teeno align hon to life effortless; clash ho "
        "to alag-alag direction me kheechte ho. Inhe blueprint ke <b>3-axis compass</b> "
        "ki tarah padho — aage ke saare sections in teen numbers se hi aate hain."))
    story.append(PageBreak())
    story += _personality_section(s, phase_s, extended)
    story.append(Spacer(1, 4 * mm))
    story.append(_explain_card(s, lang,
        "📖 Soul Urge vs Personality vs Expression — what's the difference?",
        "📖 Soul Urge vs Personality vs Expression — अंतर क्या है?",
        "📖 Soul Urge vs Personality vs Expression — fark kya hai?",
        "Three layers of 'who you are': <b>Soul Urge</b> (vowels of name) = your "
        "<b>inner motivation</b>, what your heart actually wants. <b>Personality</b> "
        "(consonants) = the <b>mask others see</b>, your social armor. "
        "<b>Expression</b> (full name) = the <b>tools you have</b> to fulfil the urge. "
        "When all three are similar — you feel authentic. When Soul Urge differs from "
        "Personality — you wear a mask at work. When Expression doesn't match the "
        "Urge — you feel mis-equipped. Use this section to find which layer is "
        "creating internal friction.",
        "'आप कौन हैं' की तीन परतें: <b>Soul Urge</b> (नाम के स्वर) = आपकी <b>आंतरिक प्रेरणा</b>, "
        "जो दिल वास्तव में चाहता है। <b>Personality</b> (व्यंजन) = <b>दूसरों को दिखने वाला मुखौटा</b>, "
        "सामाजिक कवच। <b>Expression</b> (पूरा नाम) = प्रेरणा को पूरा करने के <b>उपकरण</b>। "
        "तीनों समान हों तो आप प्रामाणिक महसूस करते हैं। Soul Urge और Personality अलग हों "
        "तो काम पर मुखौटा पहनते हैं। Expression Urge से मेल न खाए तो साधन-हीन महसूस करते हैं। "
        "इस खंड से पहचानें कि कौन-सी परत आंतरिक टकराव पैदा कर रही है।",
        "Teen layers of 'aap kaun ho': <b>Soul Urge</b> (naam ke vowels) = aapki "
        "<b>inner motivation</b>, dil sach me kya chahta hai. <b>Personality</b> "
        "(consonants) = <b>doosron ko dikhne wala mask</b>, social armor. "
        "<b>Expression</b> (full name) = urge ko poora karne ke <b>tools</b>. "
        "Teeno similar hon to authentic feel hota hai. Soul Urge aur Personality "
        "alag hon to kaam par mask pehente ho. Expression Urge se match na kare "
        "to mis-equipped feel hota hai. Is section se pehchano kaunsi layer "
        "internal friction create kar rahi hai."))
    story.append(PageBreak())
    # NEW: Karmic + Passion + Maturity deep-dive
    story += _karmic_passion_maturity(s, name, dob, phase_s, extended)
    story.append(Spacer(1, 4 * mm))
    story.append(_explain_card(s, lang,
        "📖 Karmic debt, Passion & Maturity — your 3 hidden engines",
        "📖 Karmic ऋण, Passion और Maturity — आपके 3 छिपे इंजन",
        "📖 Karmic debt, Passion aur Maturity — aapke 3 chhupe engines",
        "<b>Karmic numbers</b> (13/14/16/19) flag patterns carried over — they "
        "demand specific lessons (responsibility, freedom-balance, ego-death, "
        "self-reliance respectively) before life flows. <b>Passion number</b> = the "
        "letter that appears <b>most often</b> in your name = the energy you "
        "<b>over-use unconsciously</b> (your default tool). <b>Maturity number</b> "
        "(Driver + Life Path) = the person you <b>truly become after age 35-45</b> — "
        "your second-half identity. Read these together to see what you must "
        "<b>release</b>, what you <b>over-rely on</b>, and what you're <b>growing into</b>.",
        "<b>कर्मिक अंक</b> (13/14/16/19) पुराने पैटर्न दर्शाते हैं — विशेष पाठ माँगते हैं "
        "(ज़िम्मेदारी, स्वतंत्रता-संतुलन, अहंकार-मृत्यु, आत्मनिर्भरता) तभी जीवन प्रवाहित होता है। "
        "<b>Passion अंक</b> = नाम में <b>सबसे अधिक बार आया अक्षर</b> = वह ऊर्जा जिसे आप "
        "<b>अनजाने में अधिक प्रयोग करते हैं</b> (default उपकरण)। <b>Maturity अंक</b> "
        "(Driver + Life Path) = वह व्यक्ति जो आप <b>35-45 की उम्र के बाद वास्तव में बनते हैं</b> — "
        "आपकी दूसरी-छमाही पहचान। साथ पढ़ें यह जानने के लिए कि क्या <b>छोड़ना</b> है, "
        "किस पर <b>अधिक निर्भर</b> हैं, और किसमें <b>विकसित</b> हो रहे हैं।",
        "<b>Karmic numbers</b> (13/14/16/19) carried-over patterns flag karte hain — "
        "specific lessons demand karte hain (responsibility, freedom-balance, "
        "ego-death, self-reliance) tab life flow karti hai. <b>Passion number</b> = "
        "naam me <b>sabse zyada baar aane wala letter</b> = wo energy jo aap "
        "<b>unconsciously over-use karte ho</b> (default tool). <b>Maturity number</b> "
        "(Driver + Life Path) = wo insaan jo aap <b>age 35-45 ke baad sach me bante ho</b> — "
        "aapki second-half identity. Saath padho yeh jaanne ke liye kya <b>release</b> "
        "karna hai, kispar <b>over-rely</b> karte ho, aur kismein <b>grow</b> kar rahe ho."))
    story.append(PageBreak())
    story += _lo_shu(s, extended)
    story.append(Spacer(1, 4 * mm))
    story.append(_explain_card(s, lang,
        "📖 The 3×3 Lo Shu Grid — your DNA on a chessboard",
        "📖 3×3 Lo Shu Grid — शतरंज पर आपका DNA",
        "📖 3×3 Lo Shu Grid — chess board par aapka DNA",
        "Lo Shu Grid (developed in China 4000+ years ago) maps your full DOB into "
        "a <b>3×3 magic square</b>. Numbers that <b>repeat</b> are your superpowers; "
        "numbers <b>missing</b> are your blind-spots. Three <b>arrows</b> emerge: "
        "<b>Mind</b> plane (4-9-2 row, planning ability), <b>Soul</b> plane (3-5-7, "
        "emotional resilience), <b>Practical</b> plane (8-1-6, execution). A complete "
        "row/column/diagonal = a <b>strong success line</b>. Use the grid to "
        "diagnose <b>exactly where</b> you leak energy and which <b>practical habit</b> "
        "strengthens the missing cell.",
        "Lo Shu Grid (4000+ साल पहले चीन में विकसित) आपकी पूरी DOB को <b>3×3 जादुई वर्ग</b> "
        "में मैप करता है। <b>दोहराए</b> गए अंक आपकी महाशक्तियाँ; <b>लुप्त</b> अंक blind-spot। "
        "तीन <b>तीर</b> निकलते हैं: <b>मन</b> समतल (4-9-2 पंक्ति, योजना क्षमता), <b>आत्मा</b> "
        "समतल (3-5-7, भावनात्मक लचीलापन), <b>व्यावहारिक</b> समतल (8-1-6, निष्पादन)। "
        "पूर्ण पंक्ति/स्तंभ/विकर्ण = <b>मज़बूत सफलता-रेखा</b>। ग्रिड से ठीक-ठीक पहचानें "
        "ऊर्जा कहाँ रिसती है और कौन सी <b>व्यावहारिक आदत</b> रिक्त कक्ष मजबूत करती है।",
        "Lo Shu Grid (4000+ saal pehle China me develop hua) aapki poori DOB ko "
        "<b>3×3 magic square</b> me map karta hai. <b>Repeat</b> hone wale numbers "
        "aapki superpowers; <b>missing</b> numbers blind-spots. Teen <b>arrows</b> "
        "nikalte hain: <b>Mind</b> plane (4-9-2 row, planning ability), <b>Soul</b> "
        "plane (3-5-7, emotional resilience), <b>Practical</b> plane (8-1-6, execution). "
        "Complete row/column/diagonal = <b>strong success line</b>. Grid se "
        "diagnose karo <b>exactly kahan</b> energy leak hoti hai aur kaunsi "
        "<b>practical habit</b> missing cell ko strengthen karti hai."))
    story.append(PageBreak())
    story += _identity(s, extended)
    story.append(Spacer(1, 3 * mm))
    story.append(_explain_card(s, lang,
        "📖 Why your Personal Year/Month/Day shifts your timing",
        "📖 आपका Personal Year/Month/Day समय-योजना कैसे बदलता है",
        "📖 Personal Year/Month/Day aapki timing kaise badalti hai",
        "Numerology divides every life into <b>9-year cycles</b>. Each year carries a "
        "specific theme: <b>1</b>=new beginnings, <b>2</b>=patience/partnership, "
        "<b>3</b>=expression/joy, <b>4</b>=hard work/foundation, <b>5</b>=change/travel, "
        "<b>6</b>=family/duty, <b>7</b>=introspection/study, <b>8</b>=power/money, "
        "<b>9</b>=completion/release. Acting <b>against</b> your Personal Year theme "
        "creates friction (a 7-year is for study, not launching a startup). Personal "
        "<b>Month</b> and <b>Day</b> are sub-cycles — use them to time meetings, "
        "negotiations, and big purchases.",
        "अंक-शास्त्र हर जीवन को <b>9-वर्षीय चक्रों</b> में बाँटता है। हर वर्ष का विषय: "
        "<b>1</b>=नई शुरुआत, <b>2</b>=धैर्य/साझेदारी, <b>3</b>=अभिव्यक्ति/आनंद, "
        "<b>4</b>=परिश्रम/नींव, <b>5</b>=बदलाव/यात्रा, <b>6</b>=परिवार/कर्तव्य, "
        "<b>7</b>=आत्म-निरीक्षण/अध्ययन, <b>8</b>=शक्ति/धन, <b>9</b>=समापन/मुक्ति। "
        "Personal Year विषय के <b>विरुद्ध</b> कार्य करना घर्षण पैदा करता है (7-वर्ष "
        "अध्ययन के लिए है, स्टार्टअप के नहीं)। Personal <b>Month</b> और <b>Day</b> "
        "उप-चक्र — मीटिंग, बातचीत, बड़ी खरीद का समय इन्हीं से तय करें।",
        "Numerology har life ko <b>9-saal ke cycles</b> me divide karti hai. Har year "
        "ka specific theme: <b>1</b>=naye shuruaat, <b>2</b>=patience/partnership, "
        "<b>3</b>=expression/joy, <b>4</b>=mehnat/foundation, <b>5</b>=change/travel, "
        "<b>6</b>=family/duty, <b>7</b>=introspection/study, <b>8</b>=power/money, "
        "<b>9</b>=completion/release. Apne Personal Year theme ke <b>against</b> kaam "
        "karna friction create karta hai (7-year study ke liye hai, startup launch "
        "nahi). Personal <b>Month</b> aur <b>Day</b> sub-cycles — meetings, "
        "negotiations, badi purchase ka timing inhi se decide karo."))
    story.append(PageBreak())
    story += _pinnacles(s, practical)
    story.append(Spacer(1, 4 * mm))
    story.append(_explain_card(s, lang,
        "📖 Pinnacles & Challenges — your 4 life-chapters",
        "📖 Pinnacles और Challenges — आपके 4 जीवन-अध्याय",
        "📖 Pinnacles aur Challenges — aapke 4 life-chapters",
        "Life isn't linear — numerology splits it into <b>4 Pinnacle periods</b> "
        "(roughly 0-30, 30-39, 39-48, 48+). Each Pinnacle has a <b>theme</b> "
        "(opportunity that opens) and a paired <b>Challenge</b> (lesson that must "
        "be passed). The first Pinnacle = childhood DNA. Second = career-building "
        "decade. Third = legacy-building. Fourth = wisdom/teaching years. Knowing "
        "your <b>current Pinnacle</b> tells you what doors will open <b>this decade</b>; "
        "knowing your <b>current Challenge</b> tells you what to <b>stop fighting</b> and "
        "start integrating.",
        "जीवन रैखिक नहीं — अंक-शास्त्र इसे <b>4 Pinnacle काल</b> में विभाजित करता है "
        "(लगभग 0-30, 30-39, 39-48, 48+)। प्रत्येक Pinnacle का <b>विषय</b> (खुलने वाला अवसर) "
        "और जुड़ी <b>Challenge</b> (पास करने योग्य पाठ) है। पहला Pinnacle = बचपन का DNA। "
        "दूसरा = करियर-निर्माण दशक। तीसरा = विरासत-निर्माण। चौथा = ज्ञान/शिक्षण वर्ष। "
        "अपनी <b>वर्तमान Pinnacle</b> जानें — पता चलेगा <b>इस दशक</b> कौन से दरवाज़े "
        "खुलेंगे; <b>वर्तमान Challenge</b> बताएगी क्या <b>लड़ना बंद</b> करें और एकीकृत करें।",
        "Life linear nahi — numerology ise <b>4 Pinnacle periods</b> me split karti "
        "hai (roughly 0-30, 30-39, 39-48, 48+). Har Pinnacle ka <b>theme</b> "
        "(opportunity jo khulta hai) aur paired <b>Challenge</b> (lesson jo paas "
        "karna hota hai). First Pinnacle = childhood DNA. Second = career-building "
        "decade. Third = legacy-building. Fourth = wisdom/teaching years. <b>Current "
        "Pinnacle</b> jaano — pata chalega <b>is decade</b> kaunse doors open honge; "
        "<b>current Challenge</b> batayegi kya <b>fight karna band</b> karein aur integrate."))
    story.append(PageBreak())
    story += _career_recommendations(s, practical)
    story.append(Spacer(1, 4 * mm))
    story.append(_explain_card(s, lang,
        "📖 How career picks are chosen",
        "📖 करियर चयन कैसे होते हैं",
        "📖 Career picks kaise choose hote hain",
        "Lists are <b>not generic job boards</b> — they map your Driver and Conductor "
        "numbers to work environments where your natural pace and decision style "
        "fit. Use them to shortlist roles, then validate with skills, market, and "
        "personal goals.",
        "ये सूचियाँ <b>सामान्य नौकरी-बोर्ड नहीं</b> — Driver और Conductor अंकों को "
        "उन कार्य-वातावरण से जोड़ती हैं जहाँ आपकी गति और निर्णय-शैली मेल खाती है। "
        "भूमिका शॉर्टलिस्ट करें, फिर कौशल और लक्ष्य से सत्यापित करें।",
        "Ye lists <b>generic job boards nahi</b> — Driver aur Conductor numbers ko "
        "un work environments se map karti hain jahan aapki pace aur decision style "
        "fit ho. Roles shortlist karo, phir skills aur goals se validate karo."))
    story.append(PageBreak())
    # NEW Part 1 add-ons (year ahead, compat, daily rhythm, financial psychology)
    try:
        _digits_p1 = [int(c) for c in dob if c.isdigit()]
        try:
            _day_p1 = int(dob.split("-")[2])
        except (IndexError, ValueError):
            _day_p1 = 0
        def _r1(n):
            n = abs(int(n))
            while n > 9:
                n = sum(int(d) for d in str(n))
            return n
        _drv1 = _r1(_day_p1) if _day_p1 else 1
    except Exception:
        _drv1 = 1
    story.append(PageBreak())
    story += _year_ahead_section(s, lang, dob, _drv1)
    story.append(PageBreak())
    story += _auto_compat_section(s, lang, _drv1)
    story.append(PageBreak())
    story += _daily_clock_section(s, lang, _drv1)
    story.append(PageBreak())
    story += _financial_profile_section(s, lang, _drv1)
    story.append(PageBreak())
    story += _remedies_section(s, phase_s)
    story.append(Spacer(1, 4 * mm))
    story.append(_explain_card(s, lang,
        "📖 Why these habits work (and how to apply them)",
        "📖 ये आदतें क्यों काम करती हैं (और कैसे करें)",
        "📖 Ye habits kyu kaam karti hain (aur kaise apply karein)",
        "Habits are <b>behaviour correctors</b> — routines, journaling, sleep, and "
        "budgeting reinforce your <b>weakest Lo Shu cell</b>. Pick one habit per "
        "category (routine, reflection, communication, money) and run it for "
        "<b>21 days</b> before judging. Stack slowly — consistency beats intensity.",
        "आदतें <b>व्यवहार-सुधारक</b> हैं — दिनचर्या, जर्नल, नींद, बजट Lo Shu के "
        "<b>कमज़ोर कक्ष</b> को मजबूत करती हैं। प्रत्येक श्रेणी से <b>एक</b> आदत चुनें "
        "और <b>21 दिन</b> निरंतर करें।",
        "Habits <b>behaviour correctors</b> hain — routine, journaling, sleep, budgeting "
        "Lo Shu ke <b>weakest cell</b> ko strengthen karte hain. Har category se "
        "<b>ek</b> habit chuno aur <b>21 din</b> commit karo."))
    # NEW: Optional compatibility section
    if partner_dob:
        story.append(PageBreak())
        story += _compatibility_section(s, dob, partner_dob, partner_name, compat_kind)
    story += _disclaimer(s)
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

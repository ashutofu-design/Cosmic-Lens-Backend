"""
numerology_pdf.py — Sprint 53-N4
Render a comprehensive numerology PDF report for a single native.

Output structure (multi-page A4):
  1. Cover (name, DOB, brand)
  2. Core numbers (Driver/Conductor/Name/Kua) + planet rulers + compatibility
  3. Lo Shu 3x3 grid + missing/repeated numbers + planes
  4. Life path + Soul Urge + Personality + Expression + master numbers + karmic debt + compound
  5. Personal Year / Month / Day cycles
  6. Pinnacles & Challenges (4+4 with age windows)
  7. Career recommendations + Lucky catalog
  8. Direction (vastu) reference
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
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from vedic.numerology.meanings import (
    NUMBER_PERSONALITY,
    cheiro_compound_fallback,
    get_personality,
)

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


def _styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold",
                              fontSize=22, leading=28, textColor=BRAND_PURPLE,
                              alignment=TA_CENTER, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold",
                              fontSize=14, leading=18, textColor=BRAND_PURPLE,
                              spaceBefore=10, spaceAfter=6),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName="Helvetica-Bold",
                              fontSize=11, leading=14, textColor=TEXT_DARK,
                              spaceBefore=6, spaceAfter=2),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica",
                                fontSize=9.5, leading=13, textColor=TEXT_DARK),
        "body_mid": ParagraphStyle("body_mid", parent=base["BodyText"], fontName="Helvetica",
                                fontSize=9, leading=12, textColor=TEXT_MID),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName="Helvetica",
                                 fontSize=8, leading=10, textColor=TEXT_SOFT),
        "cover_name": ParagraphStyle("cover_name", parent=base["Heading1"],
                                     fontName="Helvetica-Bold", fontSize=28, leading=34,
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
            "★  <b>Lucky catalog</b> — gem, color, mantra, day, direction<br/>"
            "★  <b>Detailed remedies</b> — exact how-to with day &amp; count",
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

    def _cell(label, num, planet, nature):
        return [
            Paragraph(label, label_style),
            Paragraph(_safe(num) or "—", badge_style),
            Paragraph(f"Ruler: {_safe(planet)}", ruler_style),
            Paragraph(_safe(nature), nature_style),
        ]

    cells = [
        _cell("Driver (Mulank)",
              s1.get("driver_mulank"), s1.get("driver_planet"), s1.get("driver_nature")),
        _cell("Conductor (Bhagyank)",
              s1.get("conductor_bhagyank"), s1.get("conductor_planet"), s1.get("conductor_nature")),
        _cell("Name Number",
              s1.get("name_number"), s1.get("name_planet"), "Public persona"),
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
        ("Health watch", p["health"]),
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
        "number ke piche ek complete personality, ek ruling planet, aur "
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
    """Concrete how-to remedies for Driver and Conductor numbers."""
    s1 = (ps.get("s1_numbers") or {}) if isinstance(ps, dict) else {}
    out: List[Any] = []
    out.append(_section_title(s, "Detailed Remedies (Exact How-To)"))
    out.append(Paragraph(
        "Niche di gayi hain Driver aur Conductor numbers ke liye step-by-step "
        "remedies — kya karna hai, kab karna hai, kis direction me, kitni baar. "
        "Yeh classical Vedic + Lal Kitab + Cheiro corpus se compile ki gayi hain.",
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
        r = p["remedy"]

        out.append(Paragraph(
            f"<b>Remedy for {role} Number {n}</b>  "
            f"<font color='#94A3B8'>· {p['title']}</font>",
            s["h3"]))
        rows = [
            ("Mantra", r["mantra"]),
            ("Repetition", r["count"]),
            ("Day", r["day"]),
            ("Best time", r["time"]),
            ("Direction", r["direction"]),
            ("Donation items", r["items"]),
            ("Gemstone", r["gem"]),
            ("Daily habit", p["daily"]),
        ]
        out.append(_label_value_table(rows, col_widths=[40 * mm, 140 * mm]))
        out.append(Spacer(1, 5 * mm))

    out.append(_callout_box(
        s,
        "⚠  Important — gemstone disclaimer:",
        "Kabhi bhi gemstone (specially Blue Sapphire / Neelam) bina expert "
        "consultation ke direct na pehne. 3 din test-period zaruri hai. Mantra "
        "aur donation safe hain — bina kisi side-effect ke kar sakte hain.",
        colors.HexColor("#FEF2F2"),
        text_color=ACCENT_RED,
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


def _career_lucky(s, pr: dict) -> List[Any]:
    out: List[Any] = []
    out.append(_section_title(s, "6. Career & Lucky Catalog"))

    cd = pr.get("career_recommendations_driver") or []
    cc = pr.get("career_recommendations_conductor") or []
    if cd or cc:
        out.append(Paragraph("<b>Recommended Career Fields:</b>", s["h3"]))
        if cd:
            out.append(Paragraph(
                f"<b>By Driver number ({pr.get('driver','—')}):</b> {', '.join(cd)}",
                s["body"]))
        if cc:
            out.append(Paragraph(
                f"<b>By Conductor number ({pr.get('conductor','—')}):</b> {', '.join(cc)}",
                s["body"]))
        out.append(Spacer(1, 4 * mm))

    def _lucky_block(title: str, lucky: dict):
        if not isinstance(lucky, dict):
            return
        out.append(Paragraph(f"<b>{title}</b>", s["h3"]))
        rows = []
        for k, v in lucky.items():
            if isinstance(v, list):
                v_str = ", ".join(str(x) for x in v) or "—"
            else:
                v_str = _safe(v)
            label = k.replace("_", " ").title()
            rows.append((label, v_str))
        if rows:
            out.append(_label_value_table(rows, col_widths=[45 * mm, 120 * mm]))
        out.append(Spacer(1, 4 * mm))

    _lucky_block(f"Lucky for Driver ({pr.get('driver','—')})",
                 pr.get("lucky_for_driver") or {})
    _lucky_block(f"Lucky for Conductor ({pr.get('conductor','—')})",
                 pr.get("lucky_for_conductor") or {})
    return out


def _directions_DEPRECATED(s, ps: dict) -> List[Any]:
    dirs = ps.get("s2_directions") or []
    out: List[Any] = []
    if not dirs:
        return out
    out.append(_section_title(s, "7. Direction Map (Vastu reference)"))
    out.append(Paragraph(
        "Each compass direction is ruled by a planet and an element. Use this when "
        "choosing room placement, work-desk facing, or activity zone in your home.",
        s["body_mid"]))
    out.append(Spacer(1, 4 * mm))
    rows = [["Direction", "Ruler", "Element", "Life Domain"]]
    for d in dirs:
        rows.append([
            Paragraph(_safe(d.get("direction")), s["body"]),
            Paragraph(_safe(d.get("ruler")), s["body"]),
            Paragraph(_safe(d.get("element")), s["body"]),
            Paragraph(_safe(d.get("life_domain")), s["body"]),
        ])
    t = Table(rows, colWidths=[30 * mm, 24 * mm, 20 * mm, 104 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    out.append(t)
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
        "<b>Personal cycles.</b> Personal Year/Month/Day shift on each "
        "respective rollover. For deeper cycle work, consult a qualified "
        "numerologist who can correlate transits with your wider chart.",
        s["body"]))
    return out


# ─── Public entry ────────────────────────────────────────────────────

def render_numerology_pdf(*,
                          name: str,
                          dob: str,
                          gender: str | None,
                          phase_s: dict,
                          extended: dict,
                          practical: dict) -> bytes:
    """Render a multi-page numerology PDF. Returns the PDF binary."""
    s = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=18 * mm, bottomMargin=20 * mm,
                            title=f"Numerology Report — {name}",
                            author="Cosmic Lens")
    story: List[Any] = []
    story += _cover(s, name, dob, gender)
    story.append(PageBreak())
    story += _core_numbers(s, phase_s)
    story.append(PageBreak())
    story += _personality_section(s, phase_s, extended)
    story.append(PageBreak())
    story += _lo_shu(s, extended)
    story.append(PageBreak())
    story += _identity(s, extended)
    story.append(Spacer(1, 4 * mm))
    story += _cycles(s, extended)
    story.append(PageBreak())
    story += _pinnacles(s, practical)
    story.append(PageBreak())
    story += _career_lucky(s, practical)
    story.append(PageBreak())
    story += _remedies_section(s, phase_s)
    story += _disclaimer(s)
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

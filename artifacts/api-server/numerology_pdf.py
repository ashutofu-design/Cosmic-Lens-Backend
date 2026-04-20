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

# ─── Tier-A enrichment sections (karmic + passion + maturity + compat) ─────

def _karmic_passion_maturity(s, name: str, dob: str, phase_s: dict, extended: dict) -> List[Any]:
    """One-page deep-dive: Karmic Lessons + Hidden Passion + Maturity Number."""
    from vedic.numerology import tier_a as _ta

    flow: List[Any] = []
    flow.append(_section_title(s, "Karmic Lessons & Hidden Talents"))
    flow.append(Paragraph(
        "Aapke naam aur janma-tithi se nikle 3 deep insights — jo aapki "
        "soul-journey ka blueprint dikhate hain.",
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
            from vedic.numerology.extended import _PYTH
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
                f"Maturity Number: {mat.get('maturity')} ({mat.get('planet') or '—'})",
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
    from vedic.numerology import tier_a as _ta
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
        "<i>Note: Numerology is one indicator. Marriage decisions ke liye "
        "kundli matching (Ashtakoota / Manglik check) bhi karwana zaruri hai.</i>",
        s["small"]))
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
                          compat_kind: str = "love") -> bytes:
    """Render a multi-page numerology PDF. Returns the PDF binary.

    Optional partner_dob enables a compatibility section.
    """
    s = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=18 * mm, bottomMargin=20 * mm,
                            title=f"Soul Blueprint Report — {name}",
                            author="Cosmic Lens")
    story: List[Any] = []
    story += _cover(s, name, dob, gender)
    story.append(PageBreak())

    # ─── NEW: 6 premium narrative pages (deep consultation feel) ───────
    # Compute driver + conductor locally for narrative engine
    try:
        from numerology_pdf_part2 import (
            _styles as _p2_styles,
            _life_summary_block as _p2_blueprint,
            _life_essence_section as _p2_identity,
            _career_blueprint_section as _p2_career,
            _love_pattern_section as _p2_love,
            _wealth_health_spirit_section as _p2_health,
            _risk_alerts_section as _p2_risks,
        )
        _digits = [int(c) for c in dob if c.isdigit()]
        try:
            _day_n = int(dob.split("-")[2])
        except (IndexError, ValueError):
            _day_n = 0

        def _reduce(n: int) -> int:
            n = abs(int(n))
            while n > 9:
                n = sum(int(d) for d in str(n))
            return n

        _driver = _reduce(_day_n) if _day_n else 0
        _conductor = _reduce(sum(_digits)) if _digits else 0

        if _driver:
            _ps = _p2_styles()
            story += _p2_blueprint(_ps, name, _driver, _conductor)
            story.append(PageBreak())
            story += _p2_identity(_ps, _driver)
            story.append(PageBreak())
            story += _p2_career(_ps, _driver)
            story.append(PageBreak())
            story += _p2_love(_ps, _driver)
            story.append(PageBreak())
            story += _p2_health(_ps, _driver)
            story.append(PageBreak())
            story += _p2_risks(_ps, _driver)
            story.append(PageBreak())
    except Exception:
        # If narrative engine unavailable, skip premium pages but keep core report
        pass

    story += _core_numbers(s, phase_s)
    story.append(PageBreak())
    story += _personality_section(s, phase_s, extended)
    story.append(PageBreak())
    # NEW: Karmic + Passion + Maturity deep-dive
    story += _karmic_passion_maturity(s, name, dob, phase_s, extended)
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
    # NEW: Optional compatibility section
    if partner_dob:
        story.append(PageBreak())
        story += _compatibility_section(s, dob, partner_dob, partner_name, compat_kind)
    story += _disclaimer(s)
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

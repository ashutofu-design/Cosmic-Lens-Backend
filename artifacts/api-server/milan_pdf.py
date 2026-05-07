"""
milan_pdf.py — Phase 2.5.11.21 (Kundli Milan PDF)

Renders a Kundli Milan compatibility report (the JSON returned by
`/api/kundli-milan`) into a branded PDF using ReportLab.

Design parity:
  * Brand palette + page chrome match `pdf_renderer.py` and `numerology_pdf.py`.
  * Footer: "Powered by Advanced Cosmic Intelligence" (NEVER mention AI/LLM).
  * Devanagari support via NotoDeva (auto-registered if installed). Latin
    fallback (Helvetica) used for en/hn and any language without a
    registered native font.

Public entry-point:
    render_milan_pdf(payload: dict, lang: str = "en") -> bytes

`payload` must be the dict returned by `/api/kundli-milan` (or have the
same shape) — `p1`, `p2`, `total`, `max`, `percent`, `grade`, `verdict`,
`manglik_dosh`, `koots[]`, `analysis{...}`. The renderer prefers the new
7-section deep schema (`analysis.relationship_snapshot` + 6 sections)
and falls back to the legacy 4-key flat schema when only that is present.
"""

from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ── Brand palette (matches mobile app + sister PDFs) ────────────────────
BRAND_PURPLE = colors.HexColor("#7C3AED")
BRAND_GOLD   = colors.HexColor("#F5B700")
TEXT_DARK    = colors.HexColor("#0F172A")
TEXT_MID     = colors.HexColor("#475569")
TEXT_SOFT    = colors.HexColor("#94A3B8")
BG_CARD      = colors.HexColor("#F8FAFC")
BG_TINT      = colors.HexColor("#FBF9FF")
BORDER       = colors.HexColor("#E2E8F0")
ACCENT_GREEN = colors.HexColor("#047857")
ACCENT_RED   = colors.HexColor("#B91C1C")
ACCENT_AMBER = colors.HexColor("#B45309")
ACCENT_BLUE  = colors.HexColor("#1D4ED8")


# ── Devanagari font registration (best-effort, mirrors numerology_pdf) ──
_DEVA_REG: str | None = None
_DEVA_BOLD: str | None = None


def _find_devanagari_fonts() -> tuple[str, str] | None:
    candidates = [
        "/nix/store/share/fonts/truetype/noto",
        "/usr/share/fonts/truetype/noto",
        "/usr/share/fonts/noto",
    ]
    try:
        # Reuse the same nix-store discovery trick as numerology_pdf.py
        import subprocess
        for line in subprocess.check_output(
            ["ls", "/nix/store"], text=True, stderr=subprocess.DEVNULL
        ).splitlines():
            if "noto-fonts-extra" in line:
                candidates.insert(
                    0, f"/nix/store/{line}/share/fonts/truetype/noto"
                )
                break
    except Exception:
        pass
    for d in candidates:
        reg  = f"{d}/NotoSansDevanagari-Medium.ttf"
        bold = f"{d}/NotoSansDevanagari-ExtraBold.ttf"
        if os.path.exists(reg) and os.path.exists(bold):
            return reg, bold
    return None


try:
    _paths = _find_devanagari_fonts()
    if _paths:
        try:
            pdfmetrics.registerFont(TTFont("NotoDeva", _paths[0]))
            pdfmetrics.registerFont(TTFont("NotoDeva-Bold", _paths[1]))
            _DEVA_REG, _DEVA_BOLD = "NotoDeva", "NotoDeva-Bold"
        except Exception:
            pass
except Exception:
    pass


# Languages whose script is fully covered by Helvetica (Latin).
_LATIN_LANGS = {"en", "hn", "es", "fr", "de", "pt", "id", "tr", "it", "nl"}
# Languages whose script needs the Devanagari font we ship.
_DEVA_LANGS = {"hi", "mr", "ne", "sa"}


def _font_pair(lang: str) -> tuple[str, str]:
    """Return (regular, bold) font names suitable for this language.

    Falls back to Helvetica when the native font isn't registered — text
    will render as boxes for unsupported scripts, but the document will
    still build (no crash). Hindi/Marathi/Sanskrit get NotoDeva when
    available.
    """
    code = (lang or "en").lower()
    if code in _DEVA_LANGS and _DEVA_REG and _DEVA_BOLD:
        return _DEVA_REG, _DEVA_BOLD
    return "Helvetica", "Helvetica-Bold"


# ── HTML escaping (ReportLab Paragraph treats <,>,& as markup) ──────────
def _safe(s: Any) -> str:
    if s is None:
        return ""
    if isinstance(s, (list, tuple)):
        s = ", ".join(_safe(x) for x in s)
    elif isinstance(s, dict):
        s = s.get("text") or s.get("summary") or ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ── Page chrome (header bar + footer) ───────────────────────────────────
def _on_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    # Top brand bar (purple) + thin gold under-stripe
    canvas.setFillColor(BRAND_PURPLE)
    canvas.rect(0, h - 8 * mm, w, 4 * mm, fill=1, stroke=0)
    canvas.setFillColor(BRAND_GOLD)
    canvas.rect(0, h - 8 * mm, w, 1 * mm, fill=1, stroke=0)
    # Footer
    canvas.setFillColor(TEXT_SOFT)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawCentredString(
        w / 2, 12 * mm,
        "Cosmic Lens  ·  Powered by Advanced Cosmic Intelligence  ·  Kundli Milan",
    )
    canvas.drawRightString(w - 15 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


# ── Style sheet ─────────────────────────────────────────────────────────
def _styles(lang: str = "en") -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    H_REG, H_BOLD = _font_pair(lang)
    return {
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], fontName=H_BOLD,
            fontSize=24, leading=30, textColor=BRAND_PURPLE,
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontName=H_BOLD,
            fontSize=14, leading=18, textColor=BRAND_PURPLE,
            spaceBefore=10, spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "h3", parent=base["Heading3"], fontName=H_BOLD,
            fontSize=11.5, leading=15, textColor=TEXT_DARK,
            spaceBefore=6, spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body", parent=base["BodyText"], fontName=H_REG,
            fontSize=10, leading=14.5, textColor=TEXT_DARK,
            spaceAfter=4,
        ),
        "muted": ParagraphStyle(
            "muted", parent=base["BodyText"], fontName=H_REG,
            fontSize=8.5, leading=12, textColor=TEXT_MID,
            spaceAfter=2,
        ),
        "ground": ParagraphStyle(
            "ground", parent=base["BodyText"], fontName=H_REG,
            fontSize=8.5, leading=12, textColor=TEXT_MID,
            spaceAfter=4, leftIndent=4,
        ),
        "score_big": ParagraphStyle(
            "score_big", parent=base["Heading1"], fontName=H_BOLD,
            fontSize=36, leading=42, textColor=BRAND_PURPLE,
            alignment=TA_CENTER,
        ),
        "score_max": ParagraphStyle(
            "score_max", parent=base["BodyText"], fontName=H_REG,
            fontSize=11, leading=14, textColor=TEXT_SOFT,
            alignment=TA_CENTER,
        ),
        "tag_label": ParagraphStyle(
            "tag_label", parent=base["BodyText"], fontName=H_REG,
            fontSize=8, leading=10, textColor=TEXT_MID,
            alignment=TA_CENTER, spaceAfter=2,
        ),
        "tag_value": ParagraphStyle(
            "tag_value", parent=base["BodyText"], fontName=H_BOLD,
            fontSize=10, leading=13, textColor=BRAND_PURPLE,
            alignment=TA_CENTER,
        ),
    }


# ── Builders ────────────────────────────────────────────────────────────
def _cover(s: dict[str, ParagraphStyle], p1: dict, p2: dict,
           total: float, mx: int, grade: dict) -> list[Any]:
    out: list[Any] = [Spacer(1, 30 * mm)]

    # Title bar
    title = Table(
        [[Paragraph("✦  KUNDLI  MILAN  ✦", ParagraphStyle(
            "ct", fontName="Helvetica-Bold", fontSize=26, leading=32,
            textColor=BRAND_PURPLE, alignment=TA_CENTER))],
         [Paragraph("Vedic Compatibility Report", ParagraphStyle(
            "cs", fontName="Helvetica", fontSize=12, leading=15,
            textColor=TEXT_MID, alignment=TA_CENTER))]],
        colWidths=[180 * mm],
    )
    title.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, BRAND_GOLD),
        ("LINEABOVE", (0, 0), (-1, 0), 4, BRAND_PURPLE),
        ("LINEBELOW", (0, -1), (-1, -1), 4, BRAND_PURPLE),
        ("BACKGROUND", (0, 0), (-1, -1), BG_TINT),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    out.append(title)
    out.append(Spacer(1, 18 * mm))

    # Couple names
    names = Paragraph(
        f"<b>{_safe(p1.get('name'))}</b>"
        f"<font color='#94A3B8'>  &nbsp;&  &nbsp;</font>"
        f"<b>{_safe(p2.get('name'))}</b>",
        ParagraphStyle(
            "cn", fontName="Helvetica-Bold", fontSize=20, leading=26,
            textColor=TEXT_DARK, alignment=TA_CENTER,
        ),
    )
    out.append(names)
    out.append(Spacer(1, 14 * mm))

    # Big score
    score_para = Paragraph(
        f"<b>{_safe(total)}</b>"
        f"<font color='#94A3B8' size=18> / {_safe(mx)}</font>",
        s["score_big"],
    )
    out.append(score_para)
    grade_label = (grade or {}).get("label") or ""
    grade_color = (grade or {}).get("color") or "#7C3AED"
    if grade_label:
        gp = Paragraph(
            f"<b>{_safe(grade_label)}</b>",
            ParagraphStyle(
                "gl", fontName="Helvetica-Bold", fontSize=12, leading=16,
                textColor=colors.HexColor(grade_color),
                alignment=TA_CENTER, spaceBefore=4,
            ),
        )
        out.append(gp)
    out.append(Spacer(1, 22 * mm))

    # Date strip
    ds = datetime.utcnow().strftime("%d %B %Y")
    out.append(Paragraph(
        f"Generated on {ds}",
        ParagraphStyle("dt", fontName="Helvetica", fontSize=9,
                       textColor=TEXT_SOFT, alignment=TA_CENTER),
    ))
    out.append(PageBreak())
    return out


def _partner_card(s: dict, p: dict) -> Table:
    rows = [
        [Paragraph(f"<b>{_safe(p.get('name'))}</b>", s["h3"])],
        [Paragraph(
            f"<font color='#475569'>Nakshatra:</font> "
            f"<b>{_safe(p.get('nakshatra'))}</b>"
            + (f" <font color='#94A3B8'>(Pada {_safe(p.get('pada'))})</font>"
               if p.get('pada') else ""),
            s["body"],
        )],
        [Paragraph(
            f"<font color='#475569'>Rashi:</font> "
            f"<b>{_safe(p.get('rashi'))}</b>",
            s["body"],
        )],
    ]
    if p.get("manglik"):
        rows.append([Paragraph(
            "<font color='#B45309'><b>Manglik</b></font>", s["body"],
        )])
    t = Table(rows, colWidths=[85 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), BG_CARD),
        ("BOX",          (0, 0), (-1, -1), 0.6, BORDER),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    return t


def _partners_row(s: dict, p1: dict, p2: dict) -> Table:
    t = Table(
        [[_partner_card(s, p1), _partner_card(s, p2)]],
        colWidths=[90 * mm, 90 * mm],
    )
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _koot_table(s: dict, koots: list[dict]) -> Table:
    head = [
        Paragraph("<b>Koot</b>",   s["body"]),
        Paragraph("<b>Score</b>",  s["body"]),
        Paragraph("<b>Max</b>",    s["body"]),
        Paragraph("<b>Detail</b>", s["body"]),
    ]
    data = [head]
    for k in koots or []:
        score = k.get("score", 0)
        mx    = k.get("max", 0)
        is_dosha    = (score == 0 and mx > 0)
        is_strength = (mx >= 4 and score == mx)
        marker = ""
        marker_color = TEXT_MID
        if is_dosha:
            marker, marker_color = " ⚠ Dosha", ACCENT_RED
        elif is_strength:
            marker, marker_color = " ✓ Strong", ACCENT_GREEN
        detail = f"{_safe(k.get('detail',''))}"
        if marker:
            detail += (
                f" <font color='{marker_color.hexval()[2:]}'>"
                f"<b>{marker}</b></font>"
            )
            detail = detail.replace("color='", "color='#")
        data.append([
            Paragraph(_safe(k.get("label", "?")), s["body"]),
            Paragraph(f"<b>{_safe(score)}</b>", s["body"]),
            Paragraph(_safe(mx), s["muted"]),
            Paragraph(detail, s["body"]),
        ])

    t = Table(data, colWidths=[28 * mm, 18 * mm, 18 * mm, 116 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONT",         (0, 0), (-1, 0), "Helvetica-Bold", 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_CARD]),
        ("BOX",          (0, 0), (-1, -1), 0.6, BORDER),
        ("INNERGRID",    (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    return t


def _snapshot_block(s: dict, snap: dict) -> list[Any]:
    """Render relationship_snapshot {summary, tags{...}}."""
    out: list[Any] = []
    summary = (snap or {}).get("summary") or ""
    tags    = (snap or {}).get("tags") or {}
    if summary:
        para = Paragraph(_safe(summary), s["body"])
        wrap = Table([[para]], colWidths=[180 * mm])
        wrap.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), BG_TINT),
            ("BOX",          (0, 0), (-1, -1), 1, BRAND_GOLD),
            ("LEFTPADDING",  (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING",   (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ]))
        out.append(wrap)
        out.append(Spacer(1, 6))

    if tags:
        def _cell(label: str, value: str) -> Table:
            inner = [
                [Paragraph(_safe(label.upper()), s["tag_label"])],
                [Paragraph(_safe(value), s["tag_value"])],
            ]
            t = Table(inner, colWidths=[58 * mm])
            t.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, -1), colors.white),
                ("BOX",          (0, 0), (-1, -1), 0.6, BORDER),
                ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",   (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
            ]))
            return t
        row = Table([[
            _cell("Emotional Pull",    tags.get("emotional_pull", "—")),
            _cell("Marriage Potential", tags.get("marriage_potential", "—")),
            _cell("Long-term Stability", tags.get("long_term_stability", "—")),
        ]], colWidths=[60 * mm, 60 * mm, 60 * mm])
        row.setStyle(TableStyle([
            ("LEFTPADDING",  (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ]))
        out.append(row)
    return out


_SECTION_TITLES = [
    ("emotional_alignment", "Emotional Alignment"),
    ("trust_loyalty",       "Trust & Loyalty"),
    ("conflict_patterns",   "Conflict Patterns"),
    ("marriage_stability",  "Marriage Stability"),
    ("commitment_strength", "Commitment Strength"),
    ("future_direction",    "Future Direction"),
]


def _section_block(s: dict, title: str, body: str, grounding: str) -> KeepTogether:
    """Render one of the 6 deep-schema sections (text + grounding card)."""
    rows: list[list[Any]] = [
        [Paragraph(f"<b>{_safe(title)}</b>", s["h3"])],
        [Paragraph(_safe(body), s["body"])],
    ]
    if grounding:
        rows.append([Paragraph(
            f"<i>{_safe(grounding)}</i>", s["ground"],
        )])
    t = Table(rows, colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), colors.white),
        ("BOX",          (0, 0), (-1, -1), 0.6, BORDER),
        ("LINEABOVE",    (0, 0), (-1, 0), 3, BRAND_PURPLE),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
    ]))
    return KeepTogether([t, Spacer(1, 6)])


def _legacy_section_block(s: dict, title: str,
                          body: str | list[str]) -> KeepTogether:
    """Fallback renderer when only the old 4-key flat schema is present."""
    if isinstance(body, list):
        bullets = "<br/>".join(f"•  {_safe(x)}" for x in body if x)
        body_html = bullets or "—"
    else:
        body_html = _safe(body) or "—"
    return _section_block(s, title, body_html, "")


def _disclaimer(s: dict) -> Table:
    text = (
        "This compatibility report is intended for guidance and "
        "self-reflection, not as a substitute for personal judgement, "
        "professional counselling, or medical/legal advice. Vedic "
        "compatibility scores reflect classical Ashtakoot principles "
        "and are one input among many for marriage decisions."
    )
    p = Paragraph(_safe(text), ParagraphStyle(
        "dis", fontName="Helvetica", fontSize=8.5, leading=12,
        textColor=TEXT_MID,
    ))
    t = Table([[p]], colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), BG_CARD),
        ("BOX",          (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    return t


# ── Public entry-point ─────────────────────────────────────────────────
def render_milan_pdf(payload: dict, lang: str = "en") -> bytes:
    """Render a /api/kundli-milan response payload to a PDF byte string.

    Always returns valid PDF bytes (never raises on missing/partial fields)
    so the caller can stream the result directly to the client. Prefers
    the new 7-section deep schema in `payload["analysis"]`; falls back to
    the legacy 4-key flat schema when only that exists.
    """
    payload = payload or {}
    p1   = payload.get("p1") or {}
    p2   = payload.get("p2") or {}
    total = payload.get("total", 0)
    mx    = payload.get("max", 36)
    grade = payload.get("grade") or {}
    koots = payload.get("koots") or []
    analysis = payload.get("analysis") or {}

    s = _styles(lang)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=18 * mm,  bottomMargin=18 * mm,
        title=f"Kundli Milan — {p1.get('name','?')} & {p2.get('name','?')}",
        author="Cosmic Lens",
    )
    story: list[Any] = []

    # Page 1 — cover
    story.extend(_cover(s, p1, p2, total, mx, grade))

    # Page 2+ — partners + Ashtakoot table
    story.append(Paragraph("Partners", s["h2"]))
    story.append(_partners_row(s, p1, p2))
    story.append(Spacer(1, 8))
    if payload.get("manglik_dosh"):
        story.append(Paragraph(
            "<font color='#B45309'><b>⚠ Manglik Dosha is present.</b></font> "
            "Cancellation rules and remedies are discussed in the analysis below.",
            s["body"],
        ))
        story.append(Spacer(1, 4))
    story.append(Paragraph("Ashtakoot Guna Milan (8 Koots)", s["h2"]))
    story.append(_koot_table(s, koots))
    story.append(Spacer(1, 8))

    # Snapshot (deep schema only)
    snapshot = analysis.get("relationship_snapshot")
    if isinstance(snapshot, dict):
        story.append(Paragraph("Relationship Snapshot", s["h2"]))
        story.extend(_snapshot_block(s, snapshot))
        story.append(Spacer(1, 8))

    # Deep schema sections — render only those present
    has_deep = any(
        isinstance(analysis.get(k), dict) and "text" in analysis.get(k, {})
        for k, _ in _SECTION_TITLES
    )
    if has_deep:
        story.append(Paragraph("Detailed Analysis", s["h2"]))
        for key, title in _SECTION_TITLES:
            sec = analysis.get(key)
            if not isinstance(sec, dict):
                continue
            body = sec.get("text") or ""
            grounding = sec.get("grounding") or ""
            if not body:
                continue
            story.append(_section_block(s, title, body, grounding))
    else:
        # Legacy 4-key flat schema fallback
        story.append(Paragraph("Detailed Analysis", s["h2"]))
        story.append(_legacy_section_block(
            s, "Compatibility Insight",
            analysis.get("compatibility_insight") or "",
        ))
        story.append(_legacy_section_block(
            s, "Strengths",
            analysis.get("strengths") or [],
        ))
        story.append(_legacy_section_block(
            s, "Challenges",
            analysis.get("challenges") or [],
        ))
        story.append(_legacy_section_block(
            s, "Marriage Outlook",
            analysis.get("marriage_outlook") or "",
        ))

    story.append(Spacer(1, 10))
    story.append(_disclaimer(s))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

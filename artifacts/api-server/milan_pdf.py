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
    """Locate a registerable (regular, bold) pair of Devanagari TTFs.

    We try `glob.glob('/nix/store/*noto-fonts*/share/fonts/truetype/noto')`
    rather than `os.listdir('/nix/store')` because the nix store can hold
    tens of thousands of entries and `listdir` blocks for many seconds.
    Glob's wildcard match completes in milliseconds.
    """
    # /nix/store has tens of thousands of entries; glob with a wildcard
    # scans them all (slow). Use scandir with early break — stop at the
    # first noto-fonts-extra and the first noto-fonts hit.
    nix_extra: list[str] = []
    nix_plain: list[str] = []
    try:
        with os.scandir("/nix/store") as it:
            for e in it:
                n = e.name
                if "noto-fonts-extra" in n and not nix_extra:
                    nix_extra.append(
                        f"{e.path}/share/fonts/truetype/noto"
                    )
                elif "noto-fonts" in n and not nix_plain and "extra" not in n:
                    nix_plain.append(
                        f"{e.path}/share/fonts/truetype/noto"
                    )
                # Break only after `noto-fonts-extra` is found — that
                # family is the one that actually ships the Devanagari
                # TTFs. Plain `noto-fonts` rarely contains them on
                # NixOS; treating it as "good enough" caused Helvetica
                # fallback (■■■ tofu boxes) when scandir order put
                # plain before extra.
                if nix_extra:
                    break
    except Exception:
        pass
    candidates = nix_extra + nix_plain + [
        "/usr/share/fonts/truetype/noto",
        "/usr/share/fonts/noto",
    ]
    # Try the most-common filename pairs in priority order.
    name_pairs = [
        ("NotoSansDevanagari-Medium.ttf",  "NotoSansDevanagari-ExtraBold.ttf"),
        ("NotoSansDevanagari-Regular.ttf", "NotoSansDevanagari-Bold.ttf"),
        ("NotoSansDevanagari-Regular.ttf", "NotoSansDevanagari-ExtraBold.ttf"),
    ]
    for d in candidates:
        for reg_name, bold_name in name_pairs:
            reg  = f"{d}/{reg_name}"
            bold = f"{d}/{bold_name}"
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
def _header_block(s: dict[str, ParagraphStyle], p1: dict, p2: dict,
                  total: float, mx: int, grade: dict,
                  lang: str = "en") -> list[Any]:
    """Compact header at top of page 1.

    No dedicated cover page — content flows continuously below this so
    user just scrolls top-to-bottom. Header carries: title strip + couple
    names + score + grade label + date.
    """
    out: list[Any] = []
    H_REG, H_BOLD = _font_pair(lang)  # localized fonts for partner names

    # Slim title strip
    title = Table(
        [[Paragraph("✦  KUNDLI MILAN  ✦", ParagraphStyle(
            "ct", fontName=H_BOLD, fontSize=18, leading=22,
            textColor=BRAND_PURPLE, alignment=TA_CENTER))]],
        colWidths=[180 * mm],
    )
    title.setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 1.0, BRAND_GOLD),
        ("LINEABOVE",  (0, 0), (-1, 0), 2.5, BRAND_PURPLE),
        ("LINEBELOW",  (0, -1), (-1, -1), 2.5, BRAND_PURPLE),
        ("BACKGROUND", (0, 0), (-1, -1), BG_TINT),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    out.append(title)
    out.append(Spacer(1, 6))

    # Couple names + score in a single row (left: names, right: score)
    grade_label = (grade or {}).get("label") or ""
    grade_color = (grade or {}).get("color") or "#7C3AED"

    names_p = Paragraph(
        f"<b>{_safe(p1.get('name'))}</b>"
        f"<font color='#94A3B8'>  &nbsp;&amp;  &nbsp;</font>"
        f"<b>{_safe(p2.get('name'))}</b>",
        ParagraphStyle(
            "cn", fontName=H_BOLD, fontSize=16, leading=20,
            textColor=TEXT_DARK, alignment=TA_LEFT,
        ),
    )
    sub_p = Paragraph(
        f"<font color='#94A3B8'>Vedic Compatibility Report  ·  "
        f"{datetime.utcnow().strftime('%d %B %Y')}</font>",
        ParagraphStyle("sub", fontName=H_REG, fontSize=9,
                       textColor=TEXT_MID, alignment=TA_LEFT),
    )
    left_cell = Table([[names_p], [sub_p]], colWidths=[110 * mm])
    left_cell.setStyle(TableStyle([
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
    ]))

    score_p = Paragraph(
        f"<b>{_safe(total)}</b>"
        f"<font color='#94A3B8' size=12> / {_safe(mx)}</font>",
        ParagraphStyle("scn", fontName="Helvetica-Bold", fontSize=22,
                       leading=26, textColor=BRAND_PURPLE,
                       alignment=TA_CENTER),
    )
    grade_p = Paragraph(
        f"<b>{_safe(grade_label)}</b>" if grade_label else "",
        ParagraphStyle("gln", fontName="Helvetica-Bold", fontSize=9,
                       leading=12,
                       textColor=colors.HexColor(grade_color),
                       alignment=TA_CENTER),
    )
    right_cell = Table([[score_p], [grade_p]], colWidths=[60 * mm])
    right_cell.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), BG_TINT),
        ("BOX",          (0, 0), (-1, -1), 0.6, BRAND_GOLD),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))

    row = Table([[left_cell, right_cell]],
                colWidths=[115 * mm, 65 * mm])
    row.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    out.append(row)
    out.append(Spacer(1, 10))
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


# ── Premium 12-page Cosmic Relationship Blueprint helpers ─────────────
# Phase 2.5.11.21-C: redesign per attached spec — "emotionally
# intelligent, modern, screenshot-worthy, premium." Pages 9-12 derive
# content deterministically from existing data (no extra LLM calls).

_BG_HERO     = colors.HexColor("#FAF7FF")  # very light purple wash
_BG_DARK_TXT = colors.HexColor("#1E1B3A")  # near-black with a purple bias
_HAIR_GOLD   = colors.HexColor("#E5C97B")
_PILL_BG     = colors.HexColor("#F3EDFF")


def _hex(c: colors.Color) -> str:
    """Return ReportLab Color as `#RRGGBB` for HTML <font color=...>."""
    return "#" + c.hexval()[2:].upper().rjust(6, "0")[-6:]


def _relationship_type_tag(grade: dict, snap: dict, total: float, mx: int,
                           manglik: bool) -> str:
    """Derive a 2-3 word relationship descriptor for the cover page."""
    pct = (float(total) / max(float(mx), 1)) * 100 if mx else 0
    tags = (snap or {}).get("tags") or {}
    pull = (tags.get("emotional_pull") or "").lower()
    stab = (tags.get("long_term_stability") or "").lower()

    if any(w in pull for w in ("high", "strong", "deep", "intense")):
        first = "Emotionally Intense"
    elif "low" in pull or "weak" in pull:
        first = "Quietly Steady"
    else:
        first = "Emotionally Layered"

    if pct >= 75:
        second = "Naturally Harmonious Bond"
    elif pct >= 50:
        if "adjust" in stab or "delay" in stab or manglik:
            second = "Slow-Maturing Bond"
        else:
            second = "Growth-Oriented Bond"
    else:
        second = "Karmic Lesson Bond"
    return f"{first}  •  {second}"


def _relationship_tags(snap: dict, koots: list, manglik: bool) -> list[str]:
    """Up to 3 short emotional descriptor tags for the snapshot page."""
    out: list[str] = []
    snap_tags = (snap or {}).get("tags") or {}
    pull = (snap_tags.get("emotional_pull") or "").lower()
    if any(w in pull for w in ("high", "strong", "deep")):
        out.append("Deep Attachment")
    elif "medium" in pull:
        out.append("Steady Affection")
    else:
        out.append("Quiet Pull")

    gana = next((k for k in (koots or [])
                 if (k.get("key") or "").lower() == "gana"), None)
    if gana and gana.get("score", 0) < gana.get("max", 1):
        out.append("Communication Sensitive")

    stab = (snap_tags.get("long_term_stability") or "").lower()
    if "adjust" in stab or "delay" in stab or manglik:
        out.append("Delayed Stability")
    elif "strong" in stab or "natural" in stab:
        out.append("Naturally Stable")
    else:
        out.append("Growth Through Effort")
    return out[:3]


_KOOT_STRENGTH_LANG = {
    "varna":   "natural ego harmony — neither dominates the other",
    "vashya":  "genuine mutual influence and pull",
    "tara":    "naturally supportive timing for each other",
    "yoni":    "deep physical and instinctive comfort",
    "graha":   "friendly natural temperaments",
    "gana":    "shared inner nature and emotional rhythm",
    "bhakoot": "compatible life-directions and shared goals",
    "nadi":    "complementary biological/emotional energies",
}
_KOOT_DAMAGE_LANG = {
    "varna":   "subtle ego friction — one feels less respected over time",
    "vashya":  "imbalance in who pulls and who follows",
    "tara":    "mistimed moments — wrong words at vulnerable times",
    "yoni":    "mismatched physical or emotional rhythms",
    "graha":   "natural temperament clashes during stress",
    "gana":    "different inner nature — one playful, one serious",
    "bhakoot": "different life-directions creating quiet drift",
    "nadi":    "hidden energetic friction (often health-related)",
}
# Map common koot key/label spellings → canonical lookup keys above.
# Real /api/kundli-milan payloads use `vasya`, `maitri`, `bhakut` etc.
_KOOT_KEY_ALIASES = {
    "vasya":          "vashya",
    "vashya":         "vashya",
    "maitri":         "graha",
    "graha maitri":   "graha",
    "graha":          "graha",
    "bhakut":         "bhakoot",
    "bhakoot":        "bhakoot",
    "bhakuta":        "bhakoot",
    "varna":          "varna",
    "tara":           "tara",
    "yoni":           "yoni",
    "gana":           "gana",
    "nadi":           "nadi",
}


def _canon_koot_key(k: dict) -> str:
    """Resolve a koot dict to a canonical lookup key for the LANG maps.

    Tries the raw `key` first, then the lowercased `label`. Returns ""
    when neither matches a known alias (caller will skip).
    """
    raw = (k.get("key") or "").strip().lower()
    if raw in _KOOT_KEY_ALIASES:
        return _KOOT_KEY_ALIASES[raw]
    label = (k.get("label") or "").strip().lower()
    if label in _KOOT_KEY_ALIASES:
        return _KOOT_KEY_ALIASES[label]
    # last-ditch: first word of label (e.g. "Graha Maitri" → "graha")
    first = label.split()[0] if label else ""
    return _KOOT_KEY_ALIASES.get(first, "")


def _is_manglik(payload: dict) -> bool:
    """Single source of truth for manglik flag across all builders."""
    if not isinstance(payload, dict):
        return False
    if payload.get("manglik_dosh"):
        return True
    p1 = payload.get("p1") or {}
    p2 = payload.get("p2") or {}
    return bool(p1.get("manglik") or p2.get("manglik"))


def _derive_special_bullets(payload: dict) -> list[str]:
    """Bullets for 'What makes this bond special' — top koots + first strength."""
    out: list[str] = []
    koots = payload.get("koots") or []
    strong = [k for k in koots
              if k.get("max", 0) >= 4 and k.get("score", 0) == k.get("max", 0)]
    for k in strong[:3]:
        key = _canon_koot_key(k)
        line = _KOOT_STRENGTH_LANG.get(key)
        if line:
            out.append(f"<b>{_safe(k.get('label', ''))}</b>: {line}.")
    strengths = (payload.get("analysis") or {}).get("strengths") or []
    if isinstance(strengths, list) and strengths:
        first = str(strengths[0]).strip()
        if first:
            out.append(_safe(first[:300]))
    if not out:
        out.append(
            "Even where formal scores are modest, the chart "
            "shows real emotional pull and willingness to grow together."
        )
    return out[:5]


def _derive_damage_bullets(payload: dict) -> list[str]:
    """Bullets for 'What can quietly damage' — doshas + low koots + challenges."""
    out: list[str] = []
    koots = payload.get("koots") or []
    doshas = [k for k in koots
              if k.get("score", 0) == 0 and k.get("max", 0) > 0]
    weak = sorted(
        [k for k in koots
         if k.get("max", 0) >= 4
         and 0 < k.get("score", 0) <= k.get("max", 1) / 2],
        key=lambda k: k.get("score", 0),
    )
    for k in (doshas + weak)[:3]:
        key = _canon_koot_key(k)
        line = _KOOT_DAMAGE_LANG.get(key)
        if line:
            label = "Dosha" if k.get("score", 0) == 0 else "Low score"
            out.append(
                f"<b>{_safe(k.get('label', ''))} ({label})</b>: {line}."
            )
    chal = (payload.get("analysis") or {}).get("challenges") or []
    if isinstance(chal, list) and chal:
        first = str(chal[0]).strip()
        if first:
            out.append(_safe(first[:300]))
    if _is_manglik(payload):
        out.append(
            "<b>Manglik energy</b>: needs careful timing of marriage — "
            "rushing can trigger early friction. Wait for the bond to "
            "settle before major joint commitments."
        )
    if not out:
        out.append(
            "Unspoken expectations and silent withdrawal are the "
            "biggest quiet risks here. Speak early, even when it feels small."
        )
    return out[:5]


def _practical_paragraphs(payload: dict) -> list[str]:
    """Page 11 prose — money, family, lifestyle (derived from score + section)."""
    pct = (float(payload.get("total", 0))
           / max(float(payload.get("max", 36)), 1)) * 100
    paras: list[str] = []
    if pct >= 70:
        paras.append(
            "Day-to-day practical life flows naturally between you. Money "
            "decisions, family pressures, and household responsibilities "
            "tend to be discussed openly rather than fought over silently."
        )
    elif pct >= 50:
        paras.append(
            "Practical life will require conscious teamwork. Money "
            "handling and family pressure can become flashpoints unless "
            "you decide early how to share decisions and where each of "
            "you holds final say."
        )
    else:
        paras.append(
            "Practical life will demand active negotiation. Joint "
            "financial planning, household roles, and family-side "
            "expectations need explicit conversations long before they "
            "become resentments."
        )
    if _is_manglik(payload):
        paras.append(
            "Manglik influence here suggests delaying major joint "
            "commitments — large loans, joint property, business "
            "ventures — until at least one full year after marriage. "
            "Let the bond settle first."
        )
    ms = (payload.get("analysis") or {}).get("marriage_stability") or {}
    if isinstance(ms, dict):
        ms_text = ms.get("text") or ""
    else:
        ms_text = str(ms or "")
    if ms_text:
        paras.append(_safe(ms_text[:420]))
    return paras


def _final_paragraphs(payload: dict) -> list[str]:
    """Page 12 prose — closing wisdom (future_direction + universal close)."""
    paras: list[str] = []
    fd = (payload.get("analysis") or {}).get("future_direction") or {}
    if isinstance(fd, dict):
        fd_text = fd.get("text") or ""
    else:
        fd_text = str(fd or "")
    if fd_text:
        paras.append(_safe(fd_text[:600]))
    paras.append(
        "<b>The deeper truth:</b> this relationship is not defined by "
        "perfection — but by how both of you choose to grow through it. "
        "The chart shows tendencies, never destinies."
    )
    return paras


# ── Premium page builders ───────────────────────────────────────────────
def _gold_rule(width_mm: float = 40) -> Table:
    """A thin gold underline rule used below chapter titles."""
    r = Table([[""]], colWidths=[width_mm * mm], rowHeights=[2.5])
    r.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BRAND_GOLD)]))
    return r


def _cover_page(s: dict, p1: dict, p2: dict, total: float, mx: int,
                grade: dict, snap: dict, manglik: bool,
                lang: str) -> list[Any]:
    """PAGE 1 — premium cover. Brand wordmark + couple + score + type tag."""
    H_REG, H_BOLD = _font_pair(lang)
    out: list[Any] = []
    grade_label = (grade or {}).get("label") or ""
    grade_color = (grade or {}).get("color") or _hex(BRAND_PURPLE)

    out.append(Spacer(1, 18 * mm))

    out.append(Paragraph(
        f"<font color='{_hex(BRAND_GOLD)}'><b>COSMIC LENS</b></font>",
        ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=10,
                       leading=14, alignment=TA_CENTER, spaceAfter=8),
    ))
    out.append(Paragraph(
        "Cosmic Relationship Blueprint",
        ParagraphStyle("hero_title", fontName="Helvetica-Bold", fontSize=22,
                       leading=28, alignment=TA_CENTER,
                       textColor=BRAND_PURPLE, spaceAfter=2),
    ))
    out.append(Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'>A Vedic Relationship "
        f"Intelligence Report</font>",
        ParagraphStyle("hero_sub", fontName="Helvetica", fontSize=10,
                       leading=14, alignment=TA_CENTER, spaceAfter=20),
    ))

    out.append(Spacer(1, 8 * mm))

    out.append(Paragraph(
        f"<b>{_safe(p1.get('name'))}</b>"
        f"<font color='{_hex(TEXT_SOFT)}'>  &nbsp;&amp;  &nbsp;</font>"
        f"<b>{_safe(p2.get('name'))}</b>",
        ParagraphStyle("hero_names", fontName=H_BOLD, fontSize=28,
                       leading=34, alignment=TA_CENTER,
                       textColor=TEXT_DARK, spaceAfter=4),
    ))
    out.append(Paragraph(
        f"<font color='{_hex(TEXT_MID)}'>Generated "
        f"{datetime.utcnow().strftime('%d %B %Y')}</font>",
        ParagraphStyle("hero_date", fontName="Helvetica", fontSize=10,
                       leading=12, alignment=TA_CENTER, spaceAfter=18),
    ))

    out.append(Spacer(1, 8 * mm))

    score_p = Paragraph(
        f"<b>{_safe(total)}</b>"
        f"<font color='{_hex(TEXT_SOFT)}' size=18> / {_safe(mx)}</font>",
        ParagraphStyle("hero_score", fontName="Helvetica-Bold", fontSize=48,
                       leading=56, alignment=TA_CENTER,
                       textColor=BRAND_PURPLE),
    )
    grade_p = Paragraph(
        f"<b>{_safe(grade_label).upper()}</b>" if grade_label else "",
        ParagraphStyle("hero_grade", fontName="Helvetica-Bold", fontSize=11,
                       leading=14, alignment=TA_CENTER,
                       textColor=colors.HexColor(grade_color)),
    )
    card = Table([[score_p], [Spacer(1, 2)], [grade_p]],
                 colWidths=[110 * mm])
    card.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), _BG_HERO),
        ("BOX",          (0, 0), (-1, -1), 1.5, BRAND_GOLD),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 18),
    ]))
    centered = Table([[card]], colWidths=[180 * mm])
    centered.setStyle(TableStyle([
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    out.append(centered)
    out.append(Spacer(1, 16))

    rt = _relationship_type_tag(grade, snap, total, mx, manglik)
    out.append(Paragraph(
        f"<font color='{_hex(TEXT_MID)}'><b>{_safe(rt)}</b></font>",
        ParagraphStyle("hero_tag", fontName="Helvetica-Bold", fontSize=12,
                       leading=18, alignment=TA_CENTER, spaceAfter=10),
    ))

    out.append(Spacer(1, 32 * mm))
    out.append(Paragraph(
        f"<font color='{_hex(BRAND_GOLD)}'><b>"
        f"Powered by Advanced Cosmic Intelligence</b></font>",
        ParagraphStyle("hero_brand", fontName="Helvetica-Bold", fontSize=9,
                       leading=12, alignment=TA_CENTER),
    ))
    out.append(PageBreak())
    return out


def _chapter_eyebrow(num: int, label: str) -> Paragraph:
    return Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'><b>"
        f"CHAPTER {num:02d}  ·  {label.upper()}</b></font>",
        ParagraphStyle("eyebrow", fontName="Helvetica-Bold", fontSize=9,
                       leading=12, spaceAfter=6),
    )


def _chapter_title_block(title: str, subtitle: str) -> list[Any]:
    out: list[Any] = []
    out.append(Paragraph(
        f"<b>{_safe(title)}</b>",
        ParagraphStyle("chap_title", fontName="Helvetica-Bold", fontSize=24,
                       leading=30, textColor=BRAND_PURPLE, spaceAfter=4),
    ))
    out.append(_gold_rule(40))
    out.append(Spacer(1, 8))
    if subtitle:
        out.append(Paragraph(
            f"<font color='{_hex(TEXT_MID)}'><i>{_safe(subtitle)}</i></font>",
            ParagraphStyle("chap_sub", fontName="Helvetica", fontSize=11,
                           leading=15, spaceAfter=14),
        ))
    return out


def _grounding_card(s: dict, grounding: str) -> Table:
    gp = Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'><b>Why we say this →</b></font>  "
        f"<font color='{_hex(TEXT_MID)}'><i>{_safe(grounding)}</i></font>",
        ParagraphStyle("ground_pretty", fontName="Helvetica", fontSize=8.5,
                       leading=12, textColor=TEXT_MID),
    )
    t = Table([[gp]], colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), BG_TINT),
        ("LINEABOVE",    (0, 0), (-1, 0), 0.6, BRAND_GOLD),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
    ]))
    return t


def _chapter_page(s: dict, num: int, eyebrow: str, title: str,
                  subtitle: str, body: str,
                  grounding: str = "") -> list[Any]:
    """One full premium chapter page: eyebrow + title + subtitle + body."""
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, eyebrow))
    out.extend(_chapter_title_block(title, subtitle))
    if body:
        out.append(Paragraph(_safe(body), s["body"]))
        out.append(Spacer(1, 10))
    if grounding:
        out.append(_grounding_card(s, grounding))
    out.append(PageBreak())
    return out


def _bullets_page(s: dict, num: int, eyebrow: str, title: str,
                  subtitle: str, bullets: list[str]) -> list[Any]:
    """Page with a bulleted list (used for Special / Damage pages)."""
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, eyebrow))
    out.extend(_chapter_title_block(title, subtitle))
    for b in bullets or []:
        if not b:
            continue
        body = Paragraph(
            f"<font color='{_hex(BRAND_GOLD)}'><b>◆</b></font>"
            f"&nbsp;&nbsp;{b}",
            ParagraphStyle("bul", fontName=s["body"].fontName, fontSize=10.5,
                           leading=15, textColor=TEXT_DARK,
                           leftIndent=6, spaceAfter=8),
        )
        wrap = Table([[body]], colWidths=[180 * mm])
        wrap.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), colors.white),
            ("LINEBELOW",    (0, 0), (-1, -1), 0.3, BORDER),
            ("LEFTPADDING",  (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING",   (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ]))
        out.append(wrap)
        out.append(Spacer(1, 4))
    out.append(PageBreak())
    return out


def _snapshot_page(s: dict, num: int, snap: dict, koots: list,
                   manglik: bool, total: float, mx: int) -> list[Any]:
    """PAGE 2 — Relationship Snapshot. The most important page."""
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "SNAPSHOT"))
    out.extend(_chapter_title_block(
        "Relationship Snapshot",
        "How this bond actually feels in real life.",
    ))

    summary = (snap or {}).get("summary") or ""
    if summary:
        soul = Paragraph(
            f"<font color='{_hex(TEXT_DARK)}'>"
            f"{_safe(summary)}</font>",
            ParagraphStyle("soul", fontName=s["body"].fontName, fontSize=12.5,
                           leading=18, textColor=TEXT_DARK,
                           alignment=TA_LEFT),
        )
        wrap = Table([[soul]], colWidths=[180 * mm])
        wrap.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), _BG_HERO),
            ("LINEBEFORE",   (0, 0), (0, -1), 3, BRAND_GOLD),
            ("LEFTPADDING",  (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING",   (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 12),
        ]))
        out.append(wrap)
        out.append(Spacer(1, 14))

    # 3 indicator cards
    tags = (snap or {}).get("tags") or {}
    if tags:
        def _ind(label: str, value: str) -> Table:
            t = Table(
                [[Paragraph(_safe(label.upper()), s["tag_label"])],
                 [Paragraph(f"<b>{_safe(value)}</b>", s["tag_value"])]],
                colWidths=[58 * mm],
            )
            t.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, -1), colors.white),
                ("BOX",          (0, 0), (-1, -1), 0.6, BORDER),
                ("LINEABOVE",    (0, 0), (-1, 0), 2, BRAND_PURPLE),
                ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",   (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
            ]))
            return t
        row = Table([[
            _ind("Emotional Pull",     tags.get("emotional_pull",     "—")),
            _ind("Marriage Potential", tags.get("marriage_potential", "—")),
            _ind("Long-term Stability",tags.get("long_term_stability","—")),
        ]], colWidths=[60 * mm, 60 * mm, 60 * mm])
        row.setStyle(TableStyle([
            ("LEFTPADDING",  (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ]))
        out.append(row)
        out.append(Spacer(1, 14))

    # Relationship pill tags
    pill_tags = _relationship_tags(snap, koots, manglik)
    if pill_tags:
        cells = []
        for tag in pill_tags:
            pill = Table(
                [[Paragraph(
                    f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(tag)}</b></font>",
                    ParagraphStyle("pill", fontName="Helvetica-Bold",
                                   fontSize=9.5, leading=12,
                                   alignment=TA_CENTER),
                )]],
                colWidths=[55 * mm],
            )
            pill.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, -1), _PILL_BG),
                ("BOX",          (0, 0), (-1, -1), 0.4, BRAND_PURPLE),
                ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING",   (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
                ("LEFTPADDING",  (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            cells.append(pill)
        # pad to 3 cells
        while len(cells) < 3:
            cells.append(Spacer(1, 1))
        row = Table([cells], colWidths=[60 * mm, 60 * mm, 60 * mm])
        row.setStyle(TableStyle([
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        out.append(row)
        out.append(Spacer(1, 14))

    # Mini Ashtakoot card row — 8 score badges
    if koots:
        badge_cells = []
        for k in koots[:8]:
            sc = k.get("score", 0)
            mx_k = k.get("max", 0)
            color = ACCENT_GREEN if (mx_k and sc == mx_k) else (
                ACCENT_RED if sc == 0 else BRAND_PURPLE
            )
            cell = Table(
                [[Paragraph(
                    f"<font color='{_hex(color)}'><b>{_safe(sc)}</b>"
                    f"<font color='{_hex(TEXT_SOFT)}' size=8>/{_safe(mx_k)}</font></font>",
                    ParagraphStyle("badge_n", fontName="Helvetica-Bold",
                                   fontSize=12, leading=14,
                                   alignment=TA_CENTER))],
                 [Paragraph(
                    f"<font color='{_hex(TEXT_MID)}'>"
                    f"{_safe(k.get('label',''))}</font>",
                    ParagraphStyle("badge_l", fontName="Helvetica",
                                   fontSize=7.5, leading=10,
                                   alignment=TA_CENTER))]],
                colWidths=[20 * mm],
            )
            cell.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, -1), BG_CARD),
                ("BOX",          (0, 0), (-1, -1), 0.4, BORDER),
                ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",   (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
            ]))
            badge_cells.append(cell)
        while len(badge_cells) < 8:
            badge_cells.append(Spacer(1, 1))
        strip = Table([badge_cells],
                      colWidths=[22 * mm] * 8)
        strip.setStyle(TableStyle([
            ("LEFTPADDING",  (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ]))
        out.append(Paragraph(
            f"<font color='{_hex(TEXT_SOFT)}'><b>"
            f"ASHTAKOOT  ·  {_safe(total)} / {_safe(mx)}</b></font>",
            ParagraphStyle("ash_lbl", fontName="Helvetica-Bold", fontSize=8,
                           leading=10, spaceAfter=4),
        ))
        out.append(strip)
        out.append(Spacer(1, 6))

    out.append(Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'><i>Derived from emotional and "
        f"marriage combinations in both charts (Ashtakoot + Vedic "
        f"compatibility analysis).</i></font>",
        ParagraphStyle("snap_note", fontName="Helvetica", fontSize=8.5,
                       leading=12, textColor=TEXT_SOFT),
    ))
    out.append(PageBreak())
    return out


# Chapter map for the 6 deep schema sections (subtitles per spec)
_CHAPTER_MAP = [
    ("emotional_alignment", "EMOTIONAL ALIGNMENT", "Emotional Alignment",
     "How both of you feel, express, and process love."),
    ("trust_loyalty",       "TRUST & LOYALTY",     "Trust & Loyalty",
     "What strengthens trust — and what quietly tests it."),
    ("conflict_patterns",   "CONFLICT PATTERNS",   "Conflict Patterns",
     "How arguments begin, escalate, and resolve between you."),
    ("commitment_strength", "COMMITMENT STRENGTH", "Commitment Strength",
     "Who commits faster, who hesitates, and why."),
    ("marriage_stability",  "MARRIAGE STABILITY",  "Marriage Stability",
     "Long-term potential measured with realism, not absolutes."),
    ("future_direction",    "FUTURE DIRECTION",    "Future Direction",
     "Where this relationship is heading over the next 2–3 years."),
]


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
    manglik = _is_manglik(payload)
    snapshot = analysis.get("relationship_snapshot") \
        if isinstance(analysis.get("relationship_snapshot"), dict) else {}

    # Legacy 4-key fallback shimmed onto the deep-schema shape so the
    # chapter loop below ALWAYS emits exactly 6 pages (P3–P8).
    legacy_fallbacks = {
        "emotional_alignment":  analysis.get("compatibility_insight") or "",
        "trust_loyalty":        " ".join(analysis.get("strengths") or [])
                                if isinstance(analysis.get("strengths"), list)
                                else "",
        "conflict_patterns":    " ".join(analysis.get("challenges") or [])
                                if isinstance(analysis.get("challenges"), list)
                                else "",
        "commitment_strength":  analysis.get("compatibility_insight") or "",
        "marriage_stability":   analysis.get("marriage_outlook") or "",
        "future_direction":     analysis.get("marriage_outlook") or "",
    }
    _PLACEHOLDER = (
        "Detailed analysis for this section was not available for this "
        "chart. The other sections of this report still cover the core "
        "Vedic compatibility findings between both partners."
    )

    story: list[Any] = []

    # ── PAGE 1 — Cover ──────────────────────────────────────────────
    story.extend(_cover_page(
        s, p1, p2, total, mx, grade, snapshot, manglik, lang,
    ))

    # ── PAGE 2 — Relationship Snapshot ──────────────────────────────
    story.extend(_snapshot_page(
        s, 2, snapshot, koots, manglik, total, mx,
    ))

    # ── PAGES 3–8 — always exactly 6 chapter pages ──────────────────
    # Per chapter: prefer deep-schema {text, grounding}; else legacy
    # fallback text; else a deterministic placeholder. Page count is
    # locked at 12 regardless of which schema the LLM polish returned.
    chap_num = 3
    for key, eyebrow, title, subtitle in _CHAPTER_MAP:
        sec = analysis.get(key)
        body = ""
        grounding = ""
        if isinstance(sec, dict):
            body = (sec.get("text") or "").strip()
            grounding = (sec.get("grounding") or "").strip()
        if not body:
            body = (legacy_fallbacks.get(key) or "").strip() or _PLACEHOLDER
        story.extend(_chapter_page(
            s, chap_num, eyebrow, title, subtitle, body, grounding,
        ))
        chap_num += 1

    # ── PAGE 9 — What Makes This Bond Special (derived) ─────────────
    story.extend(_bullets_page(
        s, chap_num, "WHAT MAKES THIS BOND SPECIAL",
        "What Makes This Bond Special",
        "The quiet strengths most couples never realise they have.",
        _derive_special_bullets(payload),
    )); chap_num += 1

    # ── PAGE 10 — What Can Quietly Damage (derived) ─────────────────
    story.extend(_bullets_page(
        s, chap_num, "WHAT CAN QUIETLY DAMAGE THIS RELATIONSHIP",
        "What Can Quietly Damage This Bond",
        "The patterns that create distance — slowly, almost invisibly.",
        _derive_damage_bullets(payload),
    )); chap_num += 1

    # ── PAGE 11 — Practical Life Together (derived) ─────────────────
    practical_paras = _practical_paragraphs(payload)
    story.append(_chapter_eyebrow(chap_num, "PRACTICAL LIFE TOGETHER"))
    story.extend(_chapter_title_block(
        "Practical Life Together",
        "Money, family pressure, and lifestyle compatibility — in real life.",
    ))
    for para in practical_paras:
        story.append(Paragraph(_safe(para), s["body"]))
        story.append(Spacer(1, 8))
    story.append(PageBreak()); chap_num += 1

    # ── PAGE 12 — Final Relationship Outlook (derived) ──────────────
    story.append(_chapter_eyebrow(chap_num, "FINAL RELATIONSHIP OUTLOOK"))
    story.extend(_chapter_title_block(
        "Final Relationship Outlook",
        "A measured, mature reading of where this bond stands.",
    ))
    for para in _final_paragraphs(payload):
        story.append(Paragraph(_safe(para), s["body"]))
        story.append(Spacer(1, 8))
    story.append(Spacer(1, 12))
    story.append(_disclaimer(s))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

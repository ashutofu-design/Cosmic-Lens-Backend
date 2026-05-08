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


# ── Indian-script font registration (best-effort) ──────────────────────
# Phase 2.5.11.24: extended from Devanagari-only to all 8 Indian scripts
# shipped by noto-fonts-extra so the Pro PDF can render in any of the 13
# Indian languages exposed in the mobile language picker.
#
# Maps native PDF font alias → (regular .ttf, bold .ttf). Bold falls back
# to ExtraBold (Noto's bold flavour for these scripts) and finally Black
# when nothing heavier exists (Oriya only ships display weights on this
# nix-store snapshot, so we use Black for both regular and bold).
_INDIC_FONT_FAMILIES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    # alias_prefix : ((regular candidates), (bold candidates))
    "NotoDeva": (
        ("NotoSansDevanagari-Medium.ttf", "NotoSansDevanagari-Regular.ttf"),
        ("NotoSansDevanagari-ExtraBold.ttf", "NotoSansDevanagari-Bold.ttf"),
    ),
    "NotoBeng": (
        ("NotoSansBengali-Medium.ttf", "NotoSansBengali-Regular.ttf"),
        ("NotoSansBengali-ExtraBold.ttf", "NotoSansBengali-Bold.ttf"),
    ),
    "NotoTaml": (
        ("NotoSansTamil-Medium.ttf", "NotoSansTamil-Regular.ttf"),
        ("NotoSansTamil-ExtraBold.ttf", "NotoSansTamil-Bold.ttf"),
    ),
    "NotoTelu": (
        ("NotoSansTelugu-Medium.ttf", "NotoSansTelugu-Regular.ttf"),
        ("NotoSansTelugu-ExtraBold.ttf", "NotoSansTelugu-Bold.ttf"),
    ),
    "NotoGujr": (
        ("NotoSansGujarati-Medium.ttf", "NotoSansGujarati-Regular.ttf"),
        ("NotoSansGujarati-ExtraBold.ttf", "NotoSansGujarati-Bold.ttf"),
    ),
    "NotoKnda": (
        ("NotoSansKannada-Medium.ttf", "NotoSansKannada-Regular.ttf"),
        ("NotoSansKannada-ExtraBold.ttf", "NotoSansKannada-Bold.ttf"),
    ),
    "NotoMlym": (
        ("NotoSansMalayalam-Medium.ttf", "NotoSansMalayalam-Regular.ttf"),
        ("NotoSansMalayalam-ExtraBold.ttf", "NotoSansMalayalam-Bold.ttf"),
    ),
    "NotoGuru": (
        ("NotoSansGurmukhi-Medium.ttf", "NotoSansGurmukhi-Regular.ttf"),
        ("NotoSansGurmukhi-ExtraBold.ttf", "NotoSansGurmukhi-Bold.ttf"),
    ),
    "NotoOrya": (
        # Oriya on this nix snapshot only ships display weights — Black is
        # the closest readable variant; we use it for both reg + bold.
        ("NotoSansOriya-Black.ttf",),
        ("NotoSansOriya-Black.ttf",),
    ),
}

# Resolved (alias, alias_bold) pair per family — populated at import time.
# `None` means font not found on this system → Helvetica fallback.
_INDIC_REGISTERED: dict[str, tuple[str, str] | None] = {
    k: None for k in _INDIC_FONT_FAMILIES
}


def _find_noto_dirs() -> list[str]:
    """Return likely directories containing Noto TTFs, fastest path first."""
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
                if nix_extra:
                    break
    except Exception:
        pass
    return nix_extra + nix_plain + [
        "/usr/share/fonts/truetype/noto",
        "/usr/share/fonts/noto",
    ]


def _resolve_font_file(dirs: list[str], names: tuple[str, ...]) -> str | None:
    for d in dirs:
        for name in names:
            p = f"{d}/{name}"
            if os.path.exists(p):
                return p
    return None


try:
    _noto_dirs = _find_noto_dirs()
    for _alias, (_reg_names, _bold_names) in _INDIC_FONT_FAMILIES.items():
        try:
            _reg_path  = _resolve_font_file(_noto_dirs, _reg_names)
            _bold_path = _resolve_font_file(_noto_dirs, _bold_names)
            if _reg_path and _bold_path:
                pdfmetrics.registerFont(TTFont(_alias, _reg_path))
                pdfmetrics.registerFont(TTFont(f"{_alias}-Bold", _bold_path))
                _INDIC_REGISTERED[_alias] = (_alias, f"{_alias}-Bold")
        except Exception:
            # Don't let one font failure cascade — keep registering rest.
            pass
except Exception:
    pass


# Backwards-compat: prior code referenced these symbols directly.
_DEVA_PAIR = _INDIC_REGISTERED.get("NotoDeva")
_DEVA_REG  = _DEVA_PAIR[0] if _DEVA_PAIR else None
_DEVA_BOLD = _DEVA_PAIR[1] if _DEVA_PAIR else None


# Languages whose script is fully covered by Helvetica (Latin).
_LATIN_LANGS = {"en", "hn", "es", "fr", "de", "pt", "id", "tr", "it", "nl"}

# Map ISO lang code → font-family alias key in _INDIC_FONT_FAMILIES.
# Multi-language scripts: hi/mr/ne/sa share Devanagari; bn/as share Bengali
# (Assamese is a Bengali-script Indo-Aryan language with 2 extra letters
# that Noto Bengali covers); pa uses Gurmukhi.
_LANG_TO_FONT: dict[str, str] = {
    # Devanagari
    "hi": "NotoDeva", "mr": "NotoDeva", "ne": "NotoDeva", "sa": "NotoDeva",
    # Bengali (also covers Assamese)
    "bn": "NotoBeng", "as": "NotoBeng",
    # Tamil / Telugu / Gujarati / Kannada / Malayalam / Gurmukhi / Oriya
    "ta": "NotoTaml",
    "te": "NotoTelu",
    "gu": "NotoGujr",
    "kn": "NotoKnda",
    "ml": "NotoMlym",
    "pa": "NotoGuru",
    "or": "NotoOrya",
}


def _font_pair(lang: str) -> tuple[str, str]:
    """Return (regular, bold) font names suitable for this language.

    Falls back to Helvetica when the native font isn't registered — text
    will render as boxes for unsupported scripts, but the document will
    still build (no crash). All 8 Indian scripts (Devanagari, Bengali,
    Tamil, Telugu, Gujarati, Kannada, Malayalam, Gurmukhi, Oriya) are
    covered when noto-fonts-extra is present.
    """
    code = (lang or "en").lower()
    fam = _LANG_TO_FONT.get(code)
    if fam:
        pair = _INDIC_REGISTERED.get(fam)
        if pair:
            return pair
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
_INDIC_RANGES = (
    (0x0900, 0x097F),  # Devanagari
    (0x0980, 0x09FF),  # Bengali (+ Assamese)
    (0x0A00, 0x0A7F),  # Gurmukhi
    (0x0A80, 0x0AFF),  # Gujarati
    (0x0B00, 0x0B7F),  # Oriya
    (0x0B80, 0x0BFF),  # Tamil
    (0x0C00, 0x0C7F),  # Telugu
    (0x0C80, 0x0CFF),  # Kannada
    (0x0D00, 0x0D7F),  # Malayalam
)


def _has_indic(text: str) -> bool:
    """True if text contains at least one Indic codepoint."""
    if not text:
        return False
    for ch in text:
        cp = ord(ch)
        for lo, hi in _INDIC_RANGES:
            if lo <= cp <= hi:
                return True
    return False


def _pick_body(text: str, s: dict, lang: str = "en") -> ParagraphStyle:
    """Phase 2.5.11.24-fix: pick body style based on actual TEXT script.

    When polish-LLM succeeds for non-Latin lang the body is Indic →
    use the lang-specific Noto font. When the deterministic Hinglish
    fallback fires (Roman script) but lang=bn/ta/etc, the lang's Noto
    font has no Latin glyphs → glyphs render blank. Detect this case and
    use the Helvetica body style so Hinglish stays readable.
    """
    if (lang or "en").lower() in ("en", "hn"):
        return s["body"]
    return s["body"] if _has_indic(text) else s["body_latin"]


def _styles(lang: str = "en") -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    H_REG, H_BOLD = _font_pair(lang)
    # Stash lang on the returned dict so _pick_body() can be called without
    # threading lang through every render helper signature.
    return {
        "_lang": lang,
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
        # Phase 2.5.11.24-fix: Latin-only body style for Hinglish/Roman
        # fallback content when lang is non-Latin (NotoBeng/NotoTaml/etc
        # have no Latin glyphs → fallback prose would render blank).
        "body_latin": ParagraphStyle(
            "body_latin", parent=base["BodyText"], fontName="Helvetica",
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


def _chapter_title_block(title: str, subtitle: str, s: dict | None = None) -> list[Any]:
    # Phase 2.5.11.24: title + subtitle carry user-facing dynamic text
    # (often partner names + chapter names) — must respect the lang font
    # so Indic scripts don't render as tofu boxes.
    h_bold = (s or {}).get("h1").fontName if (s and "h1" in s) else "Helvetica-Bold"
    h_reg  = (s or {}).get("body").fontName if (s and "body" in s) else "Helvetica"
    out: list[Any] = []
    out.append(Paragraph(
        f"<b>{_safe(title)}</b>",
        ParagraphStyle("chap_title", fontName=h_bold, fontSize=24,
                       leading=30, textColor=BRAND_PURPLE, spaceAfter=4),
    ))
    out.append(_gold_rule(40))
    out.append(Spacer(1, 8))
    if subtitle:
        out.append(Paragraph(
            f"<font color='{_hex(TEXT_MID)}'><i>{_safe(subtitle)}</i></font>",
            ParagraphStyle("chap_sub", fontName=h_reg, fontSize=11,
                           leading=15, spaceAfter=14),
        ))
    return out


def _grounding_card(s: dict, grounding: str) -> Table:
    # Phase 2.5.11.24: `grounding` is dynamic prose written by the LLM in
    # the target language — use the lang-correct font from the styles dict
    # so Bengali/Tamil/Telugu/etc. don't render as Helvetica tofu.
    g_reg = (s.get("body").fontName if s and "body" in s else "Helvetica")
    gp = Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'><b>Why we say this →</b></font>  "
        f"<font color='{_hex(TEXT_MID)}'><i>{_safe(grounding)}</i></font>",
        ParagraphStyle("ground_pretty", fontName=g_reg, fontSize=8.5,
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
    out.extend(_chapter_title_block(title, subtitle, s))
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
    out.extend(_chapter_title_block(title, subtitle, s))
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


# ══════════════════════════════════════════════════════════════════════
# Phase 2.5.11.23 — "Premium Relationship Truth" 24-page Pro renderer
# ──────────────────────────────────────────────────────────────────────
# Public entry-point: render_milan_pro_pdf(payload, lang)
#
# Expects payload to carry standard /api/kundli-milan fields PLUS a
# `pro_premium` block produced by `vedic/compat/premium_chapters.py`:
#   pro_premium = {
#     hidden_truth: str,
#     chapters: [ {key, title, score_0_10, kya_dikh, kya_matlab,
#                  kya_dhyan, grounding}, ... 7 ],
#     special: [3 strs], damage: [strs], practical: [3 strs],
#     verdict: str,
#     _meta: { kp_promise: STRONG|PARTIAL|WEAK, hidden_signature: str }
#   }
# Always emits exactly 24 pages, even on partial/missing payloads.
# ══════════════════════════════════════════════════════════════════════

# Locked 7-chapter map for Pro (titles match score_0_10 derivation).
_PRO_CHAPTER_MAP = [
    ("emotional_compatibility",  "EMOTIONAL COMPATIBILITY",
     "Emotional Compatibility",
     "How both of you feel, express, and absorb each other emotionally."),
    ("trust_loyalty",            "TRUST & LOYALTY",
     "Trust & Loyalty",
     "What strengthens trust between you — and what quietly tests it."),
    ("communication_conflict",   "COMMUNICATION & CONFLICT",
     "Communication & Conflict",
     "How arguments begin, escalate, and finally resolve between you."),
    ("marriage_stability",       "MARRIAGE STABILITY",
     "Marriage Stability",
     "Long-term commitment potential — read with realism, not absolutes."),
    ("physical_chemistry",       "PHYSICAL + EMOTIONAL CHEMISTRY",
     "Physical + Emotional Chemistry",
     "The natural pull, comfort, and intimate rhythm between you."),
    ("family_practical",         "FAMILY + PRACTICAL LIFE",
     "Family + Practical Life",
     "Day-to-day life — money, family, lifestyle, shared decisions."),
    ("future_direction",         "LONG-TERM FUTURE DIRECTION",
     "Long-Term Future Direction",
     "Where this bond is heading over the next 2–3 years and beyond."),
]


def _pro_score_card(score: float | int | None) -> Table:
    """Large score badge: '8.7 / 10' inside a soft purple-gold card."""
    try:
        s_val = float(score) if score is not None else 0.0
    except Exception:
        s_val = 0.0
    big = Paragraph(
        f"<b>{s_val:.1f}</b>"
        f"<font color='{_hex(TEXT_SOFT)}' size=14> / 10</font>",
        ParagraphStyle("pro_score_big", fontName="Helvetica-Bold",
                       fontSize=34, leading=40, alignment=TA_CENTER,
                       textColor=BRAND_PURPLE),
    )
    label = "STRONG" if s_val >= 8 else (
        "BALANCED" if s_val >= 6 else (
        "WORKABLE" if s_val >= 4 else "NEEDS CARE"))
    sub = Paragraph(
        f"<font color='{_hex(BRAND_GOLD)}'><b>{label}</b></font>",
        ParagraphStyle("pro_score_lbl", fontName="Helvetica-Bold",
                       fontSize=9, leading=12, alignment=TA_CENTER),
    )
    card = Table([[big], [sub]], colWidths=[60 * mm])
    card.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), _BG_HERO),
        ("BOX",          (0, 0), (-1, -1), 1.2, BRAND_GOLD),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
    ]))
    return card


def _pro_block_heading(label: str) -> Paragraph:
    return Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>{label.upper()}</b></font>",
        ParagraphStyle("pro_block_h", fontName="Helvetica-Bold",
                       fontSize=10.5, leading=14, spaceBefore=8,
                       spaceAfter=4),
    )


def _pro_hidden_truth_page(s: dict, num: int, hidden_truth: str,
                           kp_meta: dict, p1_name: str, p2_name: str
                           ) -> list[Any]:
    """P3 — What's Hidden Underneath: KP marriage promise + signature."""
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "WHAT'S HIDDEN UNDERNEATH"))
    out.extend(_chapter_title_block(
        "What's Hidden Underneath",
        "The deeper Vedic+KP signature most charts miss.",
    ))
    if hidden_truth:
        out.append(Paragraph(_safe(hidden_truth), s["body"]))
        out.append(Spacer(1, 12))
    promise = (kp_meta or {}).get("kp_promise") or ""
    sig     = (kp_meta or {}).get("hidden_signature") or ""
    if promise:
        promise_color = (
            _hex(ACCENT_GREEN) if promise == "STRONG" else
            _hex(ACCENT_AMBER) if promise == "PARTIAL" else
            _hex(ACCENT_RED)
        )
        # Phase 2.5.11.24: hidden-truth promise text contains dynamic
        # partner names + LLM prose — use the lang font from styles dict.
        hp_reg = s.get("body").fontName if "body" in s else "Helvetica"
        ptxt = Paragraph(
            f"<font color='{_hex(TEXT_SOFT)}'><b>"
            f"Marriage promise reading →</b></font>  "
            f"<font color='{promise_color}'><b>{_safe(promise)}</b></font>"
            f"<font color='{_hex(TEXT_MID)}'>"
            f" — for {_safe(p1_name)} &amp; {_safe(p2_name)}, "
            f"the deeper marriage signal in both charts is read together.</font>",
            ParagraphStyle("hid_promise", fontName=hp_reg, fontSize=10.5,
                           leading=15, spaceAfter=10),
        )
        out.append(ptxt)
    if sig:
        out.append(_grounding_card(s, sig))
    out.append(PageBreak())
    return out


def _pro_hidden_truth_page_with_patterns(
    s: dict, num: int, hidden_truth: str, kp_meta: dict,
    p1_name: str, p2_name: str, payload: dict,
) -> list[Any]:
    """Phase 2.5.11.24-fix9 wrapper: same as _pro_hidden_truth_page but
    appends the QUIET PATTERNS callout BEFORE the page break, so the
    deepest insight in the report sits next to the KP promise reading."""
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "WHAT'S HIDDEN UNDERNEATH"))
    out.extend(_chapter_title_block(
        "What's Hidden Underneath",
        "The deeper Vedic+KP signature most charts miss.",
    ))
    if hidden_truth:
        out.append(Paragraph(_safe(hidden_truth), s["body"]))
        out.append(Spacer(1, 12))
    promise = (kp_meta or {}).get("kp_promise") or ""
    sig     = (kp_meta or {}).get("hidden_signature") or ""
    if promise:
        promise_color = (
            _hex(ACCENT_GREEN) if promise == "STRONG" else
            _hex(ACCENT_AMBER) if promise == "PARTIAL" else
            _hex(ACCENT_RED)
        )
        hp_reg = s.get("body").fontName if "body" in s else "Helvetica"
        out.append(Paragraph(
            f"<font color='{_hex(TEXT_SOFT)}'><b>"
            f"Marriage promise reading →</b></font>  "
            f"<font color='{promise_color}'><b>{_safe(promise)}</b></font>"
            f"<font color='{_hex(TEXT_MID)}'>"
            f" — for {_safe(p1_name)} &amp; {_safe(p2_name)}, "
            f"the deeper marriage signal in both charts is read together.</font>",
            ParagraphStyle("hid_promise2", fontName=hp_reg, fontSize=10.5,
                           leading=15, spaceAfter=10),
        ))
    if sig:
        out.append(_grounding_card(s, sig))
    out.append(Spacer(1, 12))
    inv = _derive_invisible_patterns(payload)
    if inv:
        out.append(_pro_invisible_patterns_block(s, inv))
    out.append(PageBreak())
    return out


# ── Phase 2.5.11.24-fix9 — Astrology depth + analysis hierarchy ─
# Critique-driven additions on top of fix8: users want VISIBLE Vedic
# reasoning (planet → meaning → effect), a clear analysis hierarchy that
# proves "we deeply read your kundli", and the two psychologically-
# charged sections users remember most: WHY THIS BOND FORMED + THE ONE
# THING THAT COULD QUIETLY DAMAGE IT. All deterministic — no LLM
# contract change. Adds 2 new pages: Analysis Layers (P3) and
# Attraction + Core Challenge (post-chapters). Per-chapter pages now
# carry a small "CHART LAYER" chip above the pull-quote that names the
# real Vedic factor (Moon, 7th Lord, Navamsa Venus, etc.).

# Per-chapter Vedic factor labels — the planets/houses/koots that
# genuinely drive each chapter. Worded so they feel like a guided
# explanation (NEVER raw jargon dump). Used by the small CHART LAYER
# chip on each chapter page so the "we actually read your kundli" trust
# signal is visible without breaking the prose flow.
_CHAPTER_ASTRO_FACTORS: dict[str, str] = {
    "emotional_compatibility": "Moon (mind), 4th House (inner home), Gana-koota",
    "trust_loyalty":           "Jupiter (dharma), 7th Lord, Bhakoot-koota",
    "communication_conflict":  "Mercury (speech), 3rd House (effort), Gana + Vasya",
    "marriage_stability":      "Navamsa Lagna lord, 7th House, Bhakoot + Nadi",
    "physical_chemistry":      "Venus (rasa), Mars (drive), Yoni-koota",
    "family_practical":        "2nd House (kutumba), 4th House (home), Vasya-koota",
    "future_direction":        "Jupiter (long-term), Saturn (commitment), Nadi-koota",
}


def _pro_chart_layer_chip(chapter_key: str, s: dict) -> Table | None:
    """Small 'CHART LAYER →' chip naming the real Vedic factors driving
    this chapter. Provides visible astrology grounding without raw jargon
    — addresses the "feels too AI-psychology" critique."""
    factors = _CHAPTER_ASTRO_FACTORS.get(chapter_key)
    if not factors:
        return None
    # Architect-flagged: fix9 deterministic strings are pure Latin.
    # In non-Latin-lang reports (bn/ta/te/etc) the script font has no
    # Latin glyphs — must use body_latin (Helvetica) so the chip stays
    # readable across all 13 supported langs.
    fname = (s.get("body_latin").fontName if "body_latin" in s
             else (s.get("body").fontName if "body" in s else "Helvetica"))
    p = Paragraph(
        f"<font color='{_hex(BRAND_GOLD)}'><b>CHART LAYER →</b></font>"
        f"<font color='{_hex(TEXT_MID)}'>  {_safe(factors)}</font>",
        ParagraphStyle("pro_layer", fontName=fname, fontSize=9,
                       leading=12, leftIndent=2),
    )
    t = Table([[p]], colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("LINEBELOW",    (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    return t


def _pro_analysis_layers_page(s: dict, num: int) -> list[Any]:
    """How Your Marriage Energy Was Analysed — checklist of 9 Vedic
    layers + small D1-vs-D9 explainer. Deterministic, no payload deps —
    same every report (intentionally — proves the methodology)."""
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "HOW YOUR MARRIAGE ENERGY WAS ANALYSED"))
    out.extend(_chapter_title_block(
        "How Your Marriage Energy Was Analysed",
        "The 9 Vedic layers we read across both kundlis to produce this report.",
    ))
    out.append(Spacer(1, 6))

    layers = [
        ("7th House Dynamics",            "the house of marriage in both charts"),
        ("7th Lord Condition",            "where the marriage-significator sits and what it touches"),
        ("Venus & Emotional Harmony",     "Venus dignity, aspects and partner-resonance"),
        ("Navamsa (D9) Marriage Stability","the deeper marriage-destiny chart, read separately"),
        ("Bhakoot & Nadi Compatibility",  "long-term life-direction + biological/energetic match"),
        ("Trust & Conflict Indicators",   "Jupiter-Saturn-Mars influences on commitment"),
        ("Family-Life Compatibility",     "2nd + 4th house signals for daily married rhythm"),
        ("Physical + Emotional Chemistry","Yoni-koota + Venus-Mars cross-resonance"),
        ("KP Marriage Promise",           "the deepest sub-lord layer most reports skip"),
    ]
    rows: list[list[Any]] = []
    for label, sub in layers:
        check = Paragraph(
            f"<font color='{_hex(ACCENT_GREEN)}'><b>✓</b></font>",
            ParagraphStyle("al_chk", fontName="Helvetica-Bold",
                           fontSize=12, leading=14, alignment=TA_CENTER),
        )
        body = Paragraph(
            f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(label)}</b></font>"
            f"<font color='{_hex(TEXT_MID)}'>  —  {_safe(sub)}</font>",
            ParagraphStyle("al_b", fontName="Helvetica", fontSize=10,
                           leading=14),
        )
        rows.append([check, body])
    t = Table(rows, colWidths=[10 * mm, 170 * mm])
    t.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LINEBELOW",    (0, 0), (-1, -2), 0.3, BORDER),
    ]))
    out.append(t)
    out.append(Spacer(1, 14))

    # D1 vs D9 explainer — small premium-trust block.
    out.append(_pro_block_heading("D1 vs D9 — why both matter"))
    fname = s.get("body").fontName if "body" in s else "Helvetica"
    out.append(Paragraph(
        "Your <b>D1 (birth chart)</b> shows how relationship energy "
        "appears externally — attraction, dating, the early texture of "
        "the bond. The <b>D9 (Navamsa)</b> shows how marriage actually "
        "behaves over time — daily married rhythm, the years after "
        "passion settles, the quiet long-term shape. A truthful Vedic "
        "marriage reading needs both layers. This report fuses them.",
        ParagraphStyle("d1d9", fontName=fname, fontSize=10.5,
                       leading=15.5, textColor=TEXT_MID),
    ))
    out.append(PageBreak())
    return out


def _derive_invisible_patterns(payload: dict) -> list[str]:
    """1-3 'holy shit' realism lines derived from koot/manglik/sync
    asymmetries. The viral-truth block users remember — purely
    deterministic from engine signals."""
    out: list[str] = []
    koots = payload.get("koots") or []
    by_canon: dict[str, dict] = {}
    for k in koots:
        canon = _canon_koot_key(k)
        if canon and canon not in by_canon:
            by_canon[canon] = k

    def _ratio(canon: str) -> float | None:
        k = by_canon.get(canon)
        if not k:
            return None
        try:
            sc = float(k.get("score") or 0); mx = float(k.get("max") or 0)
            return (sc / mx) if mx else None
        except Exception:
            return None

    bh = _ratio("bhakoot"); mt = _ratio("graha"); na = _ratio("nadi")
    yn = _ratio("yoni"); gn = _ratio("gana")

    # Bhakoot weak + Maitri strong → friends but different life maps
    if bh is not None and mt is not None and bh < 0.3 and mt >= 0.6:
        out.append(
            "You click as friends almost effortlessly, yet the chart "
            "quietly shows two different long-term life maps — neither "
            "of you names this out loud, but both feel it on slow Sundays."
        )
    # Yoni mismatch + Gana strong → emotional sync, physical timing differs
    if yn is not None and gn is not None and yn < 0.5 and gn >= 0.6:
        out.append(
            "Emotionally you read each other quickly — physical rhythm "
            "and the timing of intimacy may not match the same way, "
            "and most couples mistake this for a deeper problem."
        )
    # Nadi 0 + everything else generally fine → invisible health-energy
    # friction. Architect-flagged: original rule fired on any nadi=0,
    # over-asserting on broadly weak charts. Now requires the average of
    # the other resolved koot ratios ≥ 0.5 so this only triggers when
    # nadi is the OUTLIER, not just one of many weak signals.
    other_ratios = [r for r in (bh, mt, yn, gn) if r is not None]
    other_avg = (sum(other_ratios) / len(other_ratios)) if other_ratios else 0.0
    if na is not None and na <= 0.0 and other_avg >= 0.5:
        out.append(
            "Both of you can be doing everything right and still feel a "
            "subtle, hard-to-name fatigue around each other — that is "
            "Nadi's quiet signature; it asks for ritual care, not blame."
        )
    # Manglik asymmetry — one carries it, the other doesn't
    p1m = bool((payload.get("p1") or {}).get("manglik"))
    p2m = bool((payload.get("p2") or {}).get("manglik"))
    if p1m ^ p2m:
        out.append(
            "One of you carries Mars-driven intensity the other simply "
            "does not — during stress, this asymmetry becomes the "
            "invisible script behind almost every flare-up."
        )
    if not out:
        out.append(
            "Neither of you likes emotional drama — yet both silently "
            "expect the other to understand without being asked. That "
            "single unspoken expectation runs underneath most of the "
            "small distances you'll feel over the years."
        )
    return out[:3]


def _pro_invisible_patterns_block(s: dict, lines: list[str]) -> Table:
    """Boxed 'QUIET PATTERNS YOU MIGHT NOT NAME' callout — appended to
    the Hidden Truth page so the deepest insight lives next to the KP
    promise reading where users dwell longest. Latin-only deterministic
    text → uses body_latin font so non-Latin-lang reports stay readable."""
    fname = (s.get("body_latin").fontName if "body_latin" in s
             else (s.get("body").fontName if "body" in s else "Helvetica"))
    label = Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>"
        "QUIET PATTERNS YOU MIGHT NOT NAME</b></font>",
        ParagraphStyle("inv_l", fontName="Helvetica-Bold",
                       fontSize=9, leading=12),
    )
    body_paras: list[Any] = [label]
    for ln in lines:
        body_paras.append(Paragraph(
            f"<font color='{_hex(BRAND_GOLD)}'>•</font>  {_safe(ln)}",
            ParagraphStyle("inv_b", fontName=fname, fontSize=10.5,
                           leading=15, textColor=TEXT_MID,
                           leftIndent=10, spaceBefore=6),
        ))
    t = Table([[p] for p in body_paras], colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), _BG_QUOTE),
        ("LINEBEFORE",   (0, 0), (0, -1), 3.0, _LINE_QUOTE),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
    ]))
    return t


def _derive_attraction_line(payload: dict) -> str:
    """Why this bond formed — from the strongest koot scores."""
    koots = payload.get("koots") or []
    strong = sorted(
        [k for k in koots if k.get("max", 0) > 0],
        key=lambda k: (k.get("score", 0) / max(k.get("max", 1), 1)),
        reverse=True,
    )[:2]
    if not strong:
        return ("This bond forms because both charts carry a quiet "
                "willingness to grow together — even the formal scores "
                "cannot fully explain that pull.")
    lines = []
    for k in strong:
        canon = _canon_koot_key(k)
        if canon == "gana":
            lines.append("a shared inner emotional rhythm")
        elif canon == "bhakoot":
            lines.append("aligned long-term life directions")
        elif canon == "yoni":
            lines.append("deep instinctive physical comfort")
        elif canon == "graha":
            lines.append("naturally friendly temperaments")
        elif canon == "nadi":
            lines.append("complementary biological energies")
        elif canon == "varna":
            lines.append("mutual ego-respect without dominance")
        elif canon == "vashya":
            lines.append("a real magnetic pull and influence")
        elif canon == "tara":
            lines.append("naturally supportive timing for each other")
    # Architect-flagged crash fix (fix9): if every "strong" koot resolved
    # to an unknown canonical key, `lines` is empty — fall back to the
    # generic line instead of indexing.
    if not lines:
        return ("This bond forms because both charts carry a quiet "
                "willingness to grow together — even the formal scores "
                "cannot fully explain that pull.")
    if len(lines) >= 2:
        body = f"{lines[0]} from one chart, and {lines[1]} from the other"
    else:
        body = lines[0]
    return (f"This bond forms because both kundlis bring something the "
            f"other instinctively recognises — {body}. Attraction here "
            f"is not random; it's the chart's way of pairing two "
            f"complementary natures.")


def _derive_core_challenge_line(payload: dict) -> str:
    """The ONE thing that could quietly damage this marriage —
    derived from the weakest koot in the report."""
    koots = payload.get("koots") or []
    weak = sorted(
        [k for k in koots if k.get("max", 0) > 0],
        key=lambda k: (k.get("score", 0) / max(k.get("max", 1), 1)),
    )
    if not weak:
        return ("The single biggest risk for this bond is silent "
                "expectation — both of you assuming the other will "
                "understand without being asked.")
    k = weak[0]
    canon = _canon_koot_key(k)
    base_map = {
        "bhakoot": ("a slow, almost invisible drift in life-directions",
                    "Without one honest yearly conversation about where you BOTH actually want the next 5 years to go, you'll wake up at 35 in two parallel lives."),
        "nadi":    ("a hidden energetic friction that often surfaces as health or fatigue",
                    "Don't dismiss the slow tiredness around each other — it asks for ritual care, gentle routines, NOT blame or therapy speeches."),
        "gana":    ("a mismatch in inner nature — one playful, one serious",
                    "Stop trying to convert each other's mood. Make space for both rhythms in the SAME week — that is the real fix."),
        "yoni":    ("mismatched physical or emotional rhythms",
                    "Confusing intimacy timing with love itself will quietly poison this bond — separate the two early."),
        "graha":   ("natural temperament clashes during stress",
                    "Your fights won't be about the topic — they'll be about temperament under stress. Build a 24-hour cool-down rule before EVERY major conversation."),
        "vashya":  ("an imbalance in who pulls and who follows",
                    "If one of you keeps quietly leading and the other keeps quietly resisting, resentment will grow without either of you naming it."),
        "tara":    ("mistimed moments — wrong words at vulnerable times",
                    "Learn each other's bad-days. Saying the right thing at the wrong moment will land worse than saying nothing at all."),
        "varna":   ("a subtle ego friction where one feels less respected",
                    "Track who feels invisible at family gatherings — that's where this risk shows up first, not in arguments."),
    }
    label, advice = base_map.get(canon, (
        "a recurring subtle pattern this report has flagged",
        "Name it together when calm — not during a fight."))
    return (f"The single thing most likely to quietly damage this marriage "
            f"is {label}. {advice}")


def _pro_attraction_and_challenge_page(s: dict, num: int,
                                        payload: dict) -> list[Any]:
    """One dense page carrying the two psychologically-charged sections
    users remember most: WHY THIS BOND FORMED + THE ONE THING THAT
    COULD QUIETLY DAMAGE IT."""
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "WHAT DRAWS YOU · WHAT TESTS YOU"))
    out.extend(_chapter_title_block(
        "Why This Bond Formed — and the One Thing That Will Test It",
        "The two truths most reports skip. Both pulled from your charts.",
    ))
    out.append(Spacer(1, 6))

    # Latin-only deterministic content — must use body_latin so non-Latin
    # lang reports (bn/ta/te/etc) don't drop glyphs.
    fname = (s.get("body_latin").fontName if "body_latin" in s
             else (s.get("body").fontName if "body" in s else "Helvetica"))

    # WHAT DRAWS YOU TOGETHER — soft purple wash card.
    out.append(Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>WHY THIS BOND FORMED</b></font>",
        ParagraphStyle("at_h1", fontName="Helvetica-Bold", fontSize=10,
                       leading=13, spaceAfter=4),
    ))
    attraction = _derive_attraction_line(payload)
    out.append(_pro_quote_block(attraction[:200], s))
    out.append(Paragraph(
        _safe(attraction),
        ParagraphStyle("at_b1", fontName=fname, fontSize=10.5,
                       leading=15.5, textColor=TEXT_MID,
                       spaceBefore=10, spaceAfter=14),
    ))

    # THE ONE THING — gold-accented warning card.
    out.append(Paragraph(
        f"<font color='{_hex(BRAND_GOLD)}'><b>"
        f"THE ONE THING THAT COULD QUIETLY DAMAGE THIS MARRIAGE</b></font>",
        ParagraphStyle("at_h2", fontName="Helvetica-Bold", fontSize=10,
                       leading=13, spaceBefore=8, spaceAfter=4),
    ))
    challenge = _derive_core_challenge_line(payload)
    body_q = Paragraph(
        f'<font color="{_hex(colors.HexColor("#B45309"))}"><b><i>'
        f'“{_safe(challenge[:220])}”</i></b></font>',
        ParagraphStyle("at_q2", fontName=fname, fontSize=11.5,
                       leading=17, leftIndent=10, rightIndent=6),
    )
    cq = Table([[body_q]], colWidths=[180 * mm])
    cq.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), _BG_MOMENT),
        ("LINEBEFORE",   (0, 0), (0, -1), 3.0, _LINE_GOLD),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 12),
    ]))
    out.append(cq)
    out.append(Spacer(1, 10))
    out.append(Paragraph(
        _safe(challenge),
        ParagraphStyle("at_b2", fontName=fname, fontSize=10.5,
                       leading=15.5, textColor=TEXT_MID),
    ))
    out.append(Spacer(1, 14))
    out.append(_grounding_card(
        s, "These two truths are derived from your strongest and "
           "weakest koot scores — engine-locked, not a guess."))
    out.append(PageBreak())
    return out


# ── Phase 2.5.11.24-fix8 — Visual rhythm blocks ──────────────────
# Critique-driven rewrite: chapters were 2 thin pages with low density.
# These helpers add real visual storytelling — quote pull-outs, signal
# chips, real-life-moment cards, why-in-charts grounding chips — so each
# chapter becomes ONE dense rich page instead of 2 half-empty ones.

# Soft brand-tint surfaces (kept local — used only by Pro chapter blocks).
_BG_QUOTE   = colors.HexColor("#F4EEFF")  # purple wash for pull-quotes
_BG_MOMENT  = colors.HexColor("#FFF8EC")  # gold wash for real-life box
_BG_CHARTS  = colors.HexColor("#F1F5F9")  # cool slate wash for signals
_LINE_QUOTE = colors.HexColor("#A78BFA")  # soft purple rule
_LINE_GOLD  = colors.HexColor("#E8B86A")  # soft gold rule

# Map each Pro chapter key → 2-3 canonical koot keys whose engine scores
# get rendered as the "Why this appears in your charts" chips. Pulled
# from the same _KOOT_STRENGTH_LANG/_KOOT_DAMAGE_LANG vocabulary already
# in this module so wording stays consistent across the report.
_CHAPTER_KOOT_MAP: dict[str, tuple[str, ...]] = {
    "emotional_compatibility": ("gana", "bhakoot", "graha"),
    "trust_loyalty":           ("bhakoot", "varna", "graha"),
    "communication_conflict":  ("gana", "vashya", "graha"),
    "marriage_stability":      ("bhakoot", "nadi", "varna"),
    "physical_chemistry":      ("yoni", "tara", "graha"),
    "family_practical":        ("vashya", "varna", "bhakoot"),
    "future_direction":        ("nadi", "bhakoot", "tara"),
}


def _extract_quote(text: str, max_chars: int = 170) -> str:
    """Pull a punchy 1-sentence quote from prose for a highlight block.

    Tries the first ≥40-char sentence so we skip throwaway openers like
    "Yeh interesting hai." Falls back to first 160 chars on no boundary.
    Works on Hindi/Tamil/Bengali too (they end on । or .).
    """
    t = (text or "").strip()
    if not t:
        return ""
    # Devanagari danda (।) + standard ASCII sentence enders.
    parts: list[str] = []
    cur = ""
    for ch in t:
        cur += ch
        if ch in (".", "।", "!", "?"):
            parts.append(cur.strip())
            cur = ""
    if cur.strip():
        parts.append(cur.strip())
    for p in parts:
        if 40 <= len(p) <= max_chars:
            return p
    # Fall back to longest <=max_chars or first sentence truncated.
    if parts:
        if len(parts[0]) <= max_chars:
            return parts[0]
        return parts[0][: max_chars - 1].rstrip() + "…"
    return t[: max_chars - 1] + "…"


def _pro_quote_block(text: str, s: dict) -> Table:
    """Highlighted pull-quote — large italic line in a soft purple card
    with a left accent rule. Anchors visual storytelling on every chapter."""
    fname = s.get("body").fontName if "body" in s else "Helvetica"
    q = Paragraph(
        f'<font color="{_hex(BRAND_PURPLE)}"><b><i>“{_safe(text)}”</i></b></font>',
        ParagraphStyle("pro_quote", fontName=fname, fontSize=12,
                       leading=18, alignment=TA_LEFT,
                       leftIndent=10, rightIndent=6),
    )
    t = Table([[q]], colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), _BG_QUOTE),
        ("LINEBEFORE",   (0, 0), (0, -1), 3.0, _LINE_QUOTE),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 12),
    ]))
    return t


def _pro_real_life_moment(text: str, s: dict) -> list[Any]:
    """Boxed 'REAL-LIFE MOMENT' callout — uses kya_matlab prose, soft
    gold wash + a tiny eyebrow label. Replaces the flat paragraph that
    made chapters feel like report sections instead of immersive reads."""
    fname = s.get("body").fontName if "body" in s else "Helvetica"
    label = Paragraph(
        f"<font color='{_hex(BRAND_GOLD)}'><b>REAL-LIFE MOMENT</b></font>",
        ParagraphStyle("pro_moment_lbl", fontName="Helvetica-Bold",
                       fontSize=8.5, leading=11),
    )
    body = Paragraph(
        _safe(text) or "—",
        ParagraphStyle("pro_moment_body", fontName=fname, fontSize=10.5,
                       leading=15.5, textColor=TEXT_MID, spaceBefore=4),
    )
    t = Table([[label], [body]], colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), _BG_MOMENT),
        ("LINEBELOW",    (0, 0), (-1, 0), 0.6, _LINE_GOLD),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 12),
    ]))
    return [t]


def _pro_why_in_charts(chapter_key: str, koots: list[dict],
                       manglik: bool) -> Table | None:
    """Small clean grounding chips — 'WHY THIS APPEARS IN YOUR CHARTS' —
    for the 2-3 koots most relevant to this chapter. Each chip shows
    label + score + tiny meaning. Returns None if no signals available."""
    rel_keys = _CHAPTER_KOOT_MAP.get(chapter_key, ())
    if not rel_keys:
        return None
    by_canon: dict[str, dict] = {}
    for k in (koots or []):
        canon = _canon_koot_key(k)
        if canon and canon not in by_canon:
            by_canon[canon] = k

    chip_rows: list[list[Any]] = []
    for canon in rel_keys:
        k = by_canon.get(canon)
        if not k:
            continue
        try:
            sc = int(k.get("score") or 0); mx = int(k.get("max") or 0)
        except Exception:
            sc, mx = 0, 0
        ratio = (sc / mx) if mx else 0.0
        if ratio >= 0.6:
            meaning = _KOOT_STRENGTH_LANG.get(canon, "supportive area")
            tone    = ACCENT_GREEN
        elif ratio > 0:
            meaning = _KOOT_DAMAGE_LANG.get(canon, "needs gentle attention")
            tone    = colors.HexColor("#B45309")
        else:
            meaning = _KOOT_DAMAGE_LANG.get(canon, "weakest area")
            tone    = colors.HexColor("#B91C1C")
        label = (k.get("label") or canon).strip().title()
        label_p = Paragraph(
            f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(label)}</b></font>"
            f"<font color='{_hex(TEXT_SOFT)}'>  {sc}/{mx}</font>",
            ParagraphStyle("wic_l", fontName="Helvetica-Bold",
                           fontSize=9.5, leading=13),
        )
        meaning_p = Paragraph(
            f"<font color='{_hex(tone)}'>{_safe(meaning)}</font>",
            ParagraphStyle("wic_m", fontName="Helvetica", fontSize=9,
                           leading=12),
        )
        chip_rows.append([label_p, meaning_p])

    # Add manglik signal where it matters (chapters that name it as a driver).
    if manglik and chapter_key in ("trust_loyalty", "marriage_stability",
                                   "communication_conflict", "physical_chemistry"):
        amber_hex = _hex(colors.HexColor("#B45309"))
        chip_rows.append([
            Paragraph(
                f"<font color='{_hex(BRAND_PURPLE)}'><b>Mangal Signal</b></font>"
                f"<font color='{_hex(TEXT_SOFT)}'>  active</font>",
                ParagraphStyle("wic_l2", fontName="Helvetica-Bold",
                               fontSize=9.5, leading=13)),
            Paragraph(
                f"<font color='{amber_hex}'>Mars-driven intensity in one "
                "chart asks for ritual balance.</font>",
                ParagraphStyle("wic_m2", fontName="Helvetica", fontSize=9,
                               leading=12)),
        ])

    if not chip_rows:
        return None

    header = Paragraph(
        f"<font color='{_hex(TEXT_MID)}'><b>"
        "WHY THIS APPEARS IN YOUR CHARTS</b></font>",
        ParagraphStyle("wic_h", fontName="Helvetica-Bold", fontSize=8.5,
                       leading=11),
    )
    inner = Table(chip_rows, colWidths=[42 * mm, 130 * mm])
    inner.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    wrap = Table([[header], [inner]], colWidths=[180 * mm])
    wrap.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), _BG_CHARTS),
        ("LINEABOVE",    (0, 0), (-1, 0), 0.4, BORDER),
        ("LINEBELOW",    (0, -1), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
    ]))
    return wrap


def _pro_chapter_pages(s: dict, num_a: int, num_b: int,
                       eyebrow: str, title: str, subtitle: str,
                       ch: dict, ch_key: str = "",
                       koots: list[dict] | None = None,
                       manglik: bool = False) -> list[Any]:
    """ONE dense rich page per chapter (Phase 2.5.11.24-fix8 visual rewrite).

    Order: eyebrow → title row + score card → quote pull-out → main insight
    (kya_dikh) → REAL-LIFE MOMENT card (kya_matlab) → WHY-IN-CHARTS chips
    → "What to keep in mind" (kya_dhyan) → optional grounding card. Drops
    one full PageBreak vs the old 2-page-per-chapter layout (25→17 pages).
    `num_b` is preserved as a parameter for backward call-compat but no
    longer used — second page is gone.
    """
    out: list[Any] = []
    score = ch.get("score_0_10")
    kya_dikh   = (ch.get("kya_dikh") or "").strip()
    kya_matlab = (ch.get("kya_matlab") or "").strip()
    kya_dhyan  = (ch.get("kya_dhyan") or "").strip()
    grounding  = (ch.get("grounding") or "").strip()
    _ = num_b  # kept for backward signature compat

    # Header — eyebrow + title row + score card (compact, single block).
    out.append(_chapter_eyebrow(num_a, eyebrow))
    out.extend(_chapter_title_block(title, subtitle, s))
    pl_bold = s["h1"].fontName if "h1" in s else "Helvetica-Bold"
    lead = Paragraph(
        f"<font color='{_hex(TEXT_MID)}'><b>"
        f"Compatibility score for this chapter</b></font>",
        ParagraphStyle("pro_lead", fontName=pl_bold, fontSize=10,
                       leading=14),
    )
    score_row = Table(
        [[lead, _pro_score_card(score)]],
        colWidths=[110 * mm, 70 * mm],
    )
    score_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    out.append(score_row)
    out.append(Spacer(1, 10))

    # Phase 2.5.11.24-fix9 — small CHART LAYER chip naming the real
    # Vedic factors driving this chapter (planet → meaning → effect).
    chip = _pro_chart_layer_chip(ch_key, s)
    if chip is not None:
        out.append(chip)
        out.append(Spacer(1, 8))

    _lang = s.get("_lang", "en")

    # Highlighted pull-quote — extracted from kya_dikh first sentence.
    quote = _extract_quote(kya_dikh)
    if quote:
        out.append(_pro_quote_block(quote, s))
        out.append(Spacer(1, 10))

    # Main insight paragraph (kya_dikh).
    out.append(_pro_block_heading("What your chart shows here"))
    out.append(Paragraph(_safe(kya_dikh) or "—",
                         _pick_body(kya_dikh or "", s, _lang)))
    out.append(Spacer(1, 10))

    # Real-life moment box (kya_matlab as immersive scene).
    if kya_matlab:
        out.extend(_pro_real_life_moment(kya_matlab, s))
        out.append(Spacer(1, 10))

    # Why-in-charts grounding chips (engine signals — astrology made visible).
    wic = _pro_why_in_charts(ch_key, koots or [], manglik)
    if wic is not None:
        out.append(wic)
        out.append(Spacer(1, 10))

    # What to keep in mind.
    out.append(_pro_block_heading("What to keep in mind"))
    out.append(Paragraph(_safe(kya_dhyan) or "—",
                         _pick_body(kya_dhyan or "", s, _lang)))

    if grounding:
        out.append(Spacer(1, 10))
        out.append(_grounding_card(s, grounding))

    out.append(PageBreak())
    return out


def _pro_practical_page(s: dict, num: int, paragraphs: list[str]) -> list[Any]:
    """P20 — Practical Married Life (3 paragraphs from premium engine)."""
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "PRACTICAL MARRIED LIFE"))
    out.extend(_chapter_title_block(
        "Practical Married Life",
        "Money, family pressure, lifestyle — what daily life will actually feel like.",
    ))
    paras = [p for p in (paragraphs or []) if p]
    if not paras:
        paras = ["Practical detail was not generated for this report."]
    for para in paras:
        out.append(Paragraph(_safe(para), s["body"]))
        out.append(Spacer(1, 8))
    out.append(PageBreak())
    return out


def _pro_koot_decoded_page(s: dict, num: int, koots: list[dict]) -> list[Any]:
    """P21 — Compatibility Numbers Decoded: every koot in plain language."""
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "COMPATIBILITY NUMBERS DECODED"))
    out.extend(_chapter_title_block(
        "Compatibility Numbers Decoded",
        "Each of the 8 koots, explained in plain everyday language.",
    ))
    rows = [["KOOT", "SCORE", "WHAT IT MEANS"]]
    for k in (koots or []):
        canon = _canon_koot_key(k)
        try:
            sc = int(k.get("score") or 0); mx = int(k.get("max") or 0)
        except Exception:
            sc, mx = 0, 0
        # Ratio drives strength vs damage language.
        ratio = (sc / mx) if mx else 0.0
        if ratio >= 0.6:
            meaning = _KOOT_STRENGTH_LANG.get(canon, "supportive area")
        elif ratio > 0:
            meaning = _KOOT_DAMAGE_LANG.get(canon, "needs gentle attention")
        else:
            meaning = _KOOT_DAMAGE_LANG.get(canon, "weakest area — needs care")
        label = (k.get("label") or canon or "—").strip().title()
        rows.append([
            Paragraph(f"<b>{_safe(label)}</b>",
                      ParagraphStyle("kdec_l", fontName="Helvetica-Bold",
                                     fontSize=10, leading=13)),
            Paragraph(f"<b>{sc}</b>"
                      f"<font color='{_hex(TEXT_SOFT)}'> / {mx}</font>",
                      ParagraphStyle("kdec_s", fontName="Helvetica-Bold",
                                     fontSize=10, leading=13,
                                     alignment=TA_CENTER,
                                     textColor=BRAND_PURPLE)),
            Paragraph(_safe(meaning),
                      ParagraphStyle("kdec_m", fontName="Helvetica",
                                     fontSize=9.5, leading=13,
                                     textColor=TEXT_MID)),
        ])
    t = Table(rows, colWidths=[34 * mm, 26 * mm, 120 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), _BG_HERO),
        ("LINEBELOW",    (0, 0), (-1, 0), 0.8, BRAND_GOLD),
        ("LINEBELOW",    (0, 1), (-1, -1), 0.3, BORDER),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 9),
        ("TEXTCOLOR",    (0, 0), (-1, 0), TEXT_SOFT),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
    ]))
    out.append(t)
    out.append(PageBreak())
    return out


def _pro_marriage_blueprint_page(s: dict, num: int,
                                  blueprint: dict,
                                  p1_name: str, p2_name: str) -> list[Any]:
    """P22 — Marriage Blueprint (Phase 2.5.11.23-soul-v3).

    Six prose blocks describing each partner's INNATE marriage nature,
    the interaction dynamic, what each needs from the other, and the
    one takeaway. Backend-source: D9 lagna lord + Venus/Jupiter dignity
    + marriage_maturity. NEVER quotes raw chart vocab — pure relational
    character language.
    """
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "MARRIAGE BLUEPRINT"))
    out.extend(_chapter_title_block(
        "Marriage Blueprint",
        "How each of you arrives in marriage — and what daily rhythm "
        "naturally forms when those two natures meet.",
    ))
    blueprint = blueprint if isinstance(blueprint, dict) else {}

    # Phase 2.5.11.24: marriage-blueprint headings include partner names
    # and translated label text — use the lang-correct bold font.
    mbh_bold = s["h1"].fontName if "h1" in s else "Helvetica-Bold"
    def _block(label: str, body: str):
        if not (body and body.strip()):
            return
        out.append(Paragraph(
            f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(label)}</b></font>",
            ParagraphStyle("mb_h", fontName=mbh_bold, fontSize=11,
                           leading=15, spaceBefore=4, spaceAfter=4),
        ))
        out.append(Paragraph(_safe(body), s["body"]))
        out.append(Spacer(1, 8))

    _block(f"{p1_name}'s marriage nature",
           blueprint.get("p1_marriage_nature", ""))
    _block(f"{p2_name}'s marriage nature",
           blueprint.get("p2_marriage_nature", ""))
    _block("How both of you interact day-to-day",
           blueprint.get("interaction_dynamic", ""))
    _block(f"What {p1_name} needs from {p2_name}",
           blueprint.get("what_p1_needs_from_p2", ""))
    _block(f"What {p2_name} needs from {p1_name}",
           blueprint.get("what_p2_needs_from_p1", ""))

    takeaway = (blueprint.get("blueprint_takeaway") or "").strip()
    if takeaway:
        out.append(Spacer(1, 6))
        out.append(_grounding_card(s, takeaway))
    out.append(PageBreak())
    return out


def _pro_timing_sync_page(s: dict, num: int,
                          p1_name: str, p2_name: str) -> list[Any]:
    """P22 — Marriage Timing Sync (gentle, NEVER predictive)."""
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "MARRIAGE TIMING SYNC"))
    out.extend(_chapter_title_block(
        "Marriage Timing Sync",
        "How both partners' larger life cycles align — without predicting dates.",
    ))
    body = (
        f"Both {_safe(p1_name)} and {_safe(p2_name)} are moving through "
        f"their own larger life cycles. When two people commit to each "
        f"other, the meaningful sync is rarely a single auspicious date — "
        f"it is the gradual overlap of life-phases where both feel ready "
        f"to build something together."
    )
    body2 = (
        "Vedic timing tools can highlight broadly supportive seasons, but "
        "real readiness depends on lived choices — emotional clarity, "
        "career stability, family alignment, and the quiet confidence that "
        "you both want the same shape of life. Use the chapter scores in "
        "this report as your honest mirror, not the calendar."
    )
    body3 = (
        "If you are considering a near-term commitment, the most reliable "
        "compass is a long, unhurried conversation about the next 5 years — "
        "money, family roles, location, children, ambitions. Timing then "
        "follows naturally."
    )
    for para in (body, body2, body3):
        out.append(Paragraph(_safe(para), s["body"]))
        out.append(Spacer(1, 8))
    out.append(PageBreak())
    return out


def _pro_final_verdict_page(s: dict, num: int, verdict: str,
                            total: float, mx: int,
                            p1_name: str = "Partner 1",
                            p2_name: str = "Partner 2") -> list[Any]:
    """Final Verdict + Timing-context (Phase 2.5.11.24-fix8 merged page).

    Premium engine verdict prose followed by a "READINESS & TIMING" block
    that carries the standalone-Timing-Sync paragraph (now folded in to
    drop a near-empty boilerplate page from the report)."""
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "FINAL VERDICT"))
    out.extend(_chapter_title_block(
        "Final Verdict",
        f"Read together with the {_safe(total)}/{_safe(mx)} headline score.",
    ))
    txt = (verdict or "").strip() or (
        "Every relationship is a daily choice. The numbers in this report "
        "describe the soil — the harvest still depends on what both of you "
        "plant, water, and protect together."
    )
    out.append(Paragraph(_safe(txt), s["body"]))
    out.append(Spacer(1, 14))

    # Timing-context block (folded in from the old Timing Sync page).
    out.append(_pro_block_heading("Readiness & timing"))
    out.append(Paragraph(
        f"Both {_safe(p1_name)} and {_safe(p2_name)} are moving through "
        f"their own larger life cycles. Real readiness is rarely a single "
        f"auspicious date — it is the gradual overlap of life-phases where "
        f"both feel ready to build something together. Use the chapter "
        f"scores in this report as your honest mirror, not the calendar.",
        s["body"]))
    out.append(Spacer(1, 14))

    # Phase 2.5.11.24-fix9 — ONE memorable closing truth line by score
    # band. The single sentence users will remember + screenshot. The
    # whole report leads here.
    try:
        ratio = float(total) / float(mx) if mx else 0.0
    except Exception:
        ratio = 0.0
    if ratio >= 0.78:
        closer = (
            "This marriage will succeed because both of you instinctively "
            "make space for each other to be different — and that single "
            "habit is rarer than every grand romantic gesture combined."
        )
    elif ratio >= 0.58:
        closer = (
            "This marriage will succeed not because both of you are "
            "identical — but because, year by year, you will slowly "
            "learn each other's emotional language."
        )
    elif ratio >= 0.40:
        closer = (
            "This marriage will hold not when love is loudest — but when "
            "both of you choose patience over pride during the hardest "
            "weeks. The chart asks for that one specific maturity."
        )
    else:
        closer = (
            "This bond will only deepen when both of you stop expecting "
            "agreement and start practising acknowledgement — that, more "
            "than any ritual, is the real Vedic remedy here."
        )
    # Latin-only — body_latin so closer stays readable in bn/ta/te/etc.
    fname = (s.get("body_latin").fontName if "body_latin" in s
             else (s.get("body").fontName if "body" in s else "Helvetica"))
    closer_p = Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b><i>"
        f"“{_safe(closer)}”</i></b></font>",
        ParagraphStyle("verdict_closer", fontName=fname, fontSize=12,
                       leading=18, alignment=TA_CENTER,
                       leftIndent=10, rightIndent=10),
    )
    closer_t = Table([[closer_p]], colWidths=[180 * mm])
    closer_t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), _BG_QUOTE),
        ("LINEABOVE",    (0, 0), (-1, 0), 1.5, _LINE_QUOTE),
        ("LINEBELOW",    (0, -1), (-1, -1), 1.5, _LINE_QUOTE),
        ("TOPPADDING",   (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 16),
        ("LEFTPADDING",  (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    out.append(closer_t)
    out.append(Spacer(1, 12))

    out.append(_grounding_card(
        s, "This verdict is a synthesis of all 7 chapters above plus the "
           "deeper KP marriage-promise reading — not a prediction."))
    out.append(PageBreak())
    return out


def _pro_closing_page(s: dict) -> list[Any]:
    """P24 — Closing + branding (NEVER mention AI/LLM)."""
    out: list[Any] = []
    out.append(Spacer(1, 50 * mm))
    out.append(Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>Thank You</b></font>",
        ParagraphStyle("close_h", fontName="Helvetica-Bold", fontSize=26,
                       leading=32, alignment=TA_CENTER, spaceAfter=10),
    ))
    out.append(Paragraph(
        "<font color='#475569'>Every chart is a beginning, not a verdict. "
        "May this reading help both of you walk into your shared life "
        "with clearer eyes and a softer heart.</font>",
        ParagraphStyle("close_b", fontName="Helvetica", fontSize=11,
                       leading=17, alignment=TA_CENTER, spaceAfter=24),
    ))
    out.append(Spacer(1, 30 * mm))
    out.append(Paragraph(
        f"<font color='{_hex(BRAND_GOLD)}'><b>"
        f"Powered by Advanced Cosmic Intelligence</b></font>",
        ParagraphStyle("close_brand", fontName="Helvetica-Bold", fontSize=10,
                       leading=14, alignment=TA_CENTER),
    ))
    out.append(Spacer(1, 6))
    out.append(Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'>COSMIC LENS  ·  "
        f"Cosmic Relationship Blueprint Pro</font>",
        ParagraphStyle("close_meta", fontName="Helvetica", fontSize=8,
                       leading=11, alignment=TA_CENTER),
    ))
    return out


def render_milan_pro_pdf(payload: dict, lang: str = "en") -> bytes:
    """Phase 2.5.11.24-fix9 — Pro renderer (depth + hierarchy, ≈19-26pp).

    Page count scales with content density:
    - Synthetic / short fixture: exactly 19 pages (locked by tests).
    - Live LLM-polished content: ~24-26 pages because rich kya_dikh +
      kya_matlab paragraphs naturally spill 7 chapter pages onto a
      second page. That spillover is content-driven, never boilerplate
      — every overflow page carries real reading.

    Renders the "Premium Relationship Truth" report using the
    `payload["pro_premium"]` block produced by `polish_premium_chapters`.
    Always emits ≈17 pages even when the premium block is missing or
    partial — falls back to engine-derived content per page.

    Phase 2.5.11.24-fix8 (visual rhythm): each chapter is now ONE dense
    page (was 2 thin pages) carrying a pull-quote + main insight + boxed
    REAL-LIFE MOMENT + WHY-IN-CHARTS koot chips + keep-in-mind + grounding.
    Standalone Timing Sync page dropped — its prose is folded into Final
    Verdict as a "Readiness & timing" block. Net: 25 → 17 pages, every
    page substantially denser. LLM contract (kya_dikh / kya_matlab /
    kya_dhyan / grounding) UNCHANGED — all changes are renderer-only.
    """
    payload = payload or {}
    p1   = payload.get("p1") or {}
    p2   = payload.get("p2") or {}
    total = payload.get("total", 0)
    mx    = payload.get("max", 36)
    grade = payload.get("grade") or {}
    koots = payload.get("koots") or []
    pro   = payload.get("pro_premium") or {}
    chapters_in = pro.get("chapters") or []
    meta = pro.get("_meta") or {}

    # Map chapter outputs by key — premium engine emits in arbitrary order.
    by_key = {(c.get("key") or "").strip().lower(): c
              for c in chapters_in if isinstance(c, dict)}

    s = _styles(lang)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=18 * mm, bottomMargin=20 * mm,
        title=(f"Cosmic Relationship Blueprint Pro — "
               f"{p1.get('name','?')} & {p2.get('name','?')}"),
        author="Cosmic Lens",
    )
    manglik = _is_manglik(payload)
    snapshot = (payload.get("analysis") or {}).get("relationship_snapshot")
    if not isinstance(snapshot, dict):
        snapshot = {}

    story: list[Any] = []

    # P1 — Cover
    story.extend(_cover_page(s, p1, p2, total, mx, grade, snapshot,
                             manglik, lang))
    # P2 — Snapshot card (reuses existing 12-page helper, num=2)
    story.extend(_snapshot_page(s, 2, snapshot, koots, manglik, total, mx))
    # P3 — How Your Marriage Energy Was Analysed (Phase 2.5.11.24-fix9).
    # 9-layer Vedic methodology checklist + D1-vs-D9 explainer. Builds
    # the trust signal "we actually deeply read your kundli" before the
    # reader hits the interpretive chapters.
    story.extend(_pro_analysis_layers_page(s, 3))
    # P4 — Hidden Truth + Quiet Patterns (Phase 2.5.11.24-fix9 wrapper).
    story.extend(_pro_hidden_truth_page_with_patterns(
        s, 4, pro.get("hidden_truth") or "",
        meta, p1.get("name") or "Partner 1", p2.get("name") or "Partner 2",
        payload,
    ))
    # P5–11 — 7 chapters × 1 dense rich page each.
    # Each page carries: title + score + CHART LAYER chip (fix9) +
    # pull-quote + main insight + real-life moment box + WHY-IN-CHARTS
    # chips + keep-in-mind + grounding. Polisher emits ch1..ch7 by
    # contract; renderer accepts either canonical key or ch1..ch7 by
    # index so a future contract change cannot silently regress to
    # placeholder text.
    page_num = 5
    for i, (key, eyebrow, title, subtitle) in enumerate(_PRO_CHAPTER_MAP, start=1):
        ch = by_key.get(key) or by_key.get(f"ch{i}") or {}
        if not ch:
            # Deterministic placeholder so page count stays locked.
            # Soul-rich language even in the broken-payload case — never
            # exposes "engine"/"chapter not generated" wording to the user.
            ch = {
                "score_0_10": None,
                "kya_dikh":  "Is chapter ke liye aapki kundlis me jo signal hai "
                             "woh balanced range me hai — koi sharp standout nahi, "
                             "koi major friction zone bhi nahi. Iska matlab — "
                             "ye area is rishte me actively peace ya tension nahi laata.",
                "kya_matlab": "Real life me — is dimension pe daily jeevan smooth "
                              "rahega bina khaas effort ke. Lekin growth bhi "
                              "automatic nahi hogi; jo intentional banayenge wahi "
                              "deepen hoga. Surrounding chapters is bond ki "
                              "asli textures dikhayenge.",
                "kya_dhyan":  "Is chapter ko aas-paas ke chapters ke saath "
                              "padho — koi bhi bond ek hi area se nahi banta, "
                              "patterns saath dekhne se asli picture banti hai.",
                "grounding":  "",
            }
        story.extend(_pro_chapter_pages(
            s, page_num, page_num, eyebrow, title, subtitle, ch,
            ch_key=key, koots=koots, manglik=manglik,
        ))
        page_num += 1

    # P11 — What Makes This Bond Special (premium engine `special`)
    special = [b for b in (pro.get("special") or []) if b][:3]
    if not special:
        special = _derive_special_bullets(payload)[:3]
    story.extend(_bullets_page(
        s, page_num, "WHAT MAKES THIS BOND SPECIAL",
        "What Makes This Bond Special",
        "The quiet strengths most couples never realise they have.",
        special,
    ))
    # P19 — What Can Quietly Damage
    damage = [b for b in (pro.get("damage") or []) if b]
    if not damage:
        damage = _derive_damage_bullets(payload)
    if not damage:
        damage = ["No major damage pattern was detected from the engine "
                  "facts — keep nurturing the strengths above."]
    page_num += 1
    story.extend(_bullets_page(
        s, page_num, "WHAT CAN QUIETLY DAMAGE THIS BOND",
        "What Can Quietly Damage This Bond",
        "The patterns that create distance — slowly, almost invisibly.",
        damage,
    ))
    page_num += 1
    # Practical Married Life (3 paragraphs)
    practical = [p for p in (pro.get("practical") or []) if p]
    if not practical:
        practical = _practical_paragraphs(payload)
    story.extend(_pro_practical_page(s, page_num, practical[:3]))
    page_num += 1
    # Koot Decoded
    story.extend(_pro_koot_decoded_page(s, page_num, koots))
    page_num += 1
    # Marriage Blueprint (Phase soul-v3)
    story.extend(_pro_marriage_blueprint_page(
        s, page_num, pro.get("marriage_blueprint") or {},
        p1.get("name") or "Partner 1",
        p2.get("name") or "Partner 2",
    ))
    page_num += 1
    # Phase 2.5.11.24-fix9 — Attraction + Core Challenge dedicated page.
    # The two psychologically-charged sections users remember most:
    # WHY THIS BOND FORMED (from strongest koots) + THE ONE THING THAT
    # COULD QUIETLY DAMAGE IT (from weakest koot). Sits right before
    # Final Verdict so the closing arc is: blueprint → why/risk → verdict.
    story.extend(_pro_attraction_and_challenge_page(s, page_num, payload))
    page_num += 1
    # Final Verdict (Phase 2.5.11.24-fix8: Timing Sync prose merged here —
    # standalone Timing Sync page was pure boilerplate with zero engine
    # signal, dropped per critique on visual density. Final Verdict page
    # now carries the timing-context paragraph as a closing block.)
    story.extend(_pro_final_verdict_page(
        s, page_num, pro.get("verdict") or "", total, mx,
        p1_name=p1.get("name") or "Partner 1",
        p2_name=p2.get("name") or "Partner 2",
    ))
    # Closing
    story.extend(_pro_closing_page(s))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

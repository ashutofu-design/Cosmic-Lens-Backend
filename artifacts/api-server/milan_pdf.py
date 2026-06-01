"""
milan_pdf.py — Phase 2.5.11.21 (Kundli Milan PDF)

Renders a Kundli Milan compatibility report (the JSON returned by
`/api/kundli-milan`) into a branded PDF using ReportLab.

Design parity:
  * Brand palette + page chrome match `pdf_renderer.py` and `numerology_pdf.py`.
  * Running footer: "Cosmic Lens · Kundli Milan" + page number (NEVER mention AI/LLM).
  * Indic scripts: Noto Sans TTFs from `artifacts/api-server/fonts/noto/` (bundled),
    then MILAN_NOTO_FONT_DIR(S), then OS font folders. Native langs **raise**
    `MilanPdfNativeFontUnavailableError` if no fonts register — no silent tofu PDFs.
    Tests only: set MILAN_PDF_RELAX_NATIVE_FONT_REQUIREMENT=1 (see conftest.py).

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
import logging
import math
import os
import re
from datetime import datetime
from typing import Any

_log = logging.getLogger(__name__)

from vedic.compat import milan_pdf_locale as MPL
from vedic.compat.milan_chart_facts import enrich_milan_bundle_for_pdf
from vedic.compat.premium_chapters import (
    CHAPTER_BODY_KEY,
    CHAPTER_SECTION_KEYS,
    _chart_bridge_with_remedy_tail,
)

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
from reportlab.platypus.flowables import Flowable


class MilanPdfNativeFontUnavailableError(RuntimeError):
    """Raised when `lang` maps to an Indic script but no Noto fonts registered."""

    pass


def _native_font_fallback_allowed() -> bool:
    """Allow Helvetica for Indic langs (tofu risk). Tests set this; production should not."""
    v = (os.environ.get("MILAN_PDF_RELAX_NATIVE_FONT_REQUIREMENT") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


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
# Pro compatibility PDF native lane: Hindi (देवनागरी) only — register Noto
# Devanagari for `lang=hi`. Latin lanes (`en`, `hn`) use Helvetica stack.
#
# Maps native PDF font alias → (regular .ttf, bold .ttf). Bold falls back to
# ExtraBold when a dedicated bold file is missing.
_INDIC_FONT_FAMILIES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    # Pro PDF native lane: Hindi (देवनागरी) only — single Noto family.
    "NotoDeva": (
        ("NotoSansDevanagari-Regular.ttf", "NotoSansDevanagari-Medium.ttf"),
        ("NotoSansDevanagari-Bold.ttf", "NotoSansDevanagari-ExtraBold.ttf"),
    ),
}

# Resolved (alias, alias_bold) pair per family — populated by register_indic_fonts().
# `None` means font not found on this system → Helvetica fallback (tofu for Indic).
_INDIC_REGISTERED: dict[str, tuple[str, str] | None] = {
    k: None for k in _INDIC_FONT_FAMILIES
}


def _bundled_fonts_root() -> str:
    """`artifacts/api-server/fonts/` — Noto files live in `fonts/noto/`."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


def _bundled_noto_font_dir() -> str:
    """Bundled Noto drop zone (preferred for Windows + container deploys)."""
    return os.path.join(_bundled_fonts_root(), "noto")


def _legacy_unix_noto_dirs() -> list[str]:
    """NixOS / common Linux paths — scanned after bundled + OS-specific dirs."""
    nix_extra: list[str] = []
    nix_plain: list[str] = []
    try:
        with os.scandir("/nix/store") as it:
            for e in it:
                n = e.name
                if "noto-fonts-extra" in n and not nix_extra:
                    nix_extra.append(f"{e.path}/share/fonts/truetype/noto")
                elif "noto-fonts" in n and not nix_plain and "extra" not in n:
                    nix_plain.append(f"{e.path}/share/fonts/truetype/noto")
                if nix_extra:
                    break
    except Exception:
        pass
    return nix_extra + nix_plain + [
        "/usr/share/fonts/truetype/noto",
        "/usr/share/fonts/noto",
    ]


def _collect_noto_search_dirs() -> list[str]:
    """Ordered font dirs: project `fonts/noto` + `fonts/` first, then env, then OS."""
    seen: set[str] = set()
    out: list[str] = []

    def _add(path: str | None) -> None:
        if not path:
            return
        rp = os.path.abspath(os.path.expandvars(os.path.expanduser(path.strip())))
        if rp in seen:
            return
        if os.path.isdir(rp):
            seen.add(rp)
            out.append(rp)

    _add(_bundled_noto_font_dir())
    _add(_bundled_fonts_root())

    milan_one = (os.environ.get("MILAN_NOTO_FONT_DIR") or "").strip()
    if milan_one:
        _add(milan_one)
    milan_many = os.environ.get("MILAN_NOTO_FONT_DIRS") or ""
    for chunk in milan_many.split(os.pathsep):
        _add(chunk.strip())

    windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot")
    if windir:
        _add(os.path.join(windir, "Fonts"))
    localappdata = os.environ.get("LOCALAPPDATA") or ""
    if localappdata:
        _add(os.path.join(localappdata, "Microsoft", "Windows", "Fonts"))

    home = os.path.expanduser("~")
    _add(os.path.join(home, "Library", "Fonts"))
    _add("/Library/Fonts")

    for u in _legacy_unix_noto_dirs():
        _add(u)

    return out


def _resolve_font_file(dirs: list[str], names: tuple[str, ...]) -> str | None:
    for d in dirs:
        for name in names:
            p = os.path.join(d, name)
            if os.path.isfile(p):
                return p
    return None


def register_indic_fonts(*, force: bool = False) -> None:
    """Register Noto TTFonts with ReportLab (embedded subsets on save).

    Safe to call multiple times. Search order: `fonts/noto/` + `fonts/` next to
    this module, MILAN_NOTO_FONT_DIR / MILAN_NOTO_FONT_DIRS, Windows/macOS
    font folders, then Linux/Nix paths.
    """
    dirs = _collect_noto_search_dirs()
    _log.info(
        "[milan_pdf] indic_font_search_paths count=%s first=%s bundled_noto=%s bundled_root=%s",
        len(dirs),
        dirs[0] if dirs else None,
        _bundled_noto_font_dir(),
        _bundled_fonts_root(),
    )

    reg_names = pdfmetrics.getRegisteredFontNames()

    for alias, (reg_candidates, bold_candidates) in _INDIC_FONT_FAMILIES.items():
        if not force and alias in reg_names:
            if _INDIC_REGISTERED.get(alias) is None:
                _INDIC_REGISTERED[alias] = (alias, f"{alias}-Bold")
            continue

        reg_path = _resolve_font_file(dirs, reg_candidates)
        bold_path = _resolve_font_file(dirs, bold_candidates)
        if not reg_path:
            _log.warning(
                "[milan_pdf] indic_font_missing alias=%s tried_dirs=%s filenames=%s",
                alias,
                len(dirs),
                reg_candidates[:4],
            )
            continue

        bold_use = bold_path or reg_path
        try:
            bold_alias = f"{alias}-Bold"
            pdfmetrics.registerFont(TTFont(alias, reg_path))
            pdfmetrics.registerFont(TTFont(bold_alias, bold_use))
            # Map family so <b>/<i> inside <font name='NotoDeva'> resolve cleanly.
            pdfmetrics.registerFontFamily(
                alias,
                normal=alias,
                bold=bold_alias,
                italic=alias,
                boldItalic=bold_alias,
            )
            _INDIC_REGISTERED[alias] = (alias, bold_alias)
            _log.info(
                "[milan_pdf] indic_font_registered_ok alias=%s regular_path=%s bold_path=%s",
                alias,
                reg_path,
                bold_use,
            )
        except Exception as exc:
            _log.warning(
                "[milan_pdf] indic_font_register_fail alias=%s err=%s",
                alias,
                exc,
                exc_info=False,
            )


register_indic_fonts()


def _normalize_milan_pdf_lang(lang: str | None) -> str:
    """Pro / basic Milan PDF lanes: en | hn | hi only."""
    from vedic.compat.premium_chapters import normalize_pro_pdf_lang

    return normalize_pro_pdf_lang(lang)


# Backwards-compat: prior code referenced these symbols directly.
_DEVA_PAIR = _INDIC_REGISTERED.get("NotoDeva")
_DEVA_REG = _DEVA_PAIR[0] if _DEVA_PAIR else None
_DEVA_BOLD = _DEVA_PAIR[1] if _DEVA_PAIR else None


# Languages whose script is fully covered by Helvetica (Latin).
_LATIN_LANGS = {"en", "hn", "es", "fr", "de", "pt", "id", "tr", "it", "nl"}

_LANG_TO_FONT: dict[str, str] = {
    "hi": "NotoDeva",
}


def _ensure_native_pdf_fonts_registered(lang: str) -> None:
    """Fail fast on native langs if Noto did not register (no silent tofu PDFs)."""
    register_indic_fonts()
    code = (lang or "en").lower()
    if code in _LATIN_LANGS:
        return
    fam = _LANG_TO_FONT.get(code)
    if not fam:
        return
    if _INDIC_REGISTERED.get(fam):
        return
    b_not = _bundled_noto_font_dir()
    b_root = _bundled_fonts_root()
    if _native_font_fallback_allowed():
        _log.warning(
            "[milan_pdf] FALLBACK_ACTIVATED Helvetica lang=%s mapped_family=%s "
            "relax_env=MILAN_PDF_RELAX_NATIVE_FONT_REQUIREMENT is_set "
            "bundled_noto_dir=%s fonts_root=%s",
            code,
            fam,
            b_not,
            b_root,
        )
        return
    _log.error(
        "[milan_pdf] native_font_REQUIRED_MISSING lang=%s mapped_family=%s "
        "bundled_noto_dir=%s fonts_root=%s "
        "fix=python scripts/download_noto_indic_for_milan_pdf.py",
        code,
        fam,
        b_not,
        b_root,
    )
    raise MilanPdfNativeFontUnavailableError(
        f"Milan PDF: native Noto fonts for lang={code!r} (family {fam!r}) are not "
        f"registered. Install .ttf files under {b_not} or set MILAN_NOTO_FONT_DIR. "
        "Run: python scripts/download_noto_indic_for_milan_pdf.py "
        "(from artifacts/api-server). "
        "Dev-only escape: MILAN_PDF_RELAX_NATIVE_FONT_REQUIREMENT=1."
    )


def _log_pdf_font_lane(lang: str) -> None:
    """One INFO line per PDF when native Noto resolved (or Latin lane)."""
    register_indic_fonts()
    code = (lang or "en").lower()
    fam = _LANG_TO_FONT.get(code)
    bundled_ok = os.path.isdir(_bundled_noto_font_dir())
    if fam:
        pair = _INDIC_REGISTERED.get(fam)
        if pair:
            _log.info(
                "[milan_pdf] pdf_render_font_lane lang=%s mapped_family=%s "
                "reportlab_regular_ps=%s reportlab_bold_ps=%s bundled_noto_exists=%s",
                code,
                fam,
                pair[0],
                pair[1],
                bundled_ok,
            )
            return
        return
    _log.info(
        "[milan_pdf] pdf_render_font_lane lang=%s lane=latin_Helvetica bundled_noto_exists=%s",
        code,
        bundled_ok,
    )


def _font_pair(lang: str) -> tuple[str, str]:
    """Return (regular, bold) PostScript names for this language.

    Native-script lanes use registered Noto TTFonts (embedded in PDF).
    Falls back to Helvetica only when both regular+bold could not be loaded.
    """
    code = (lang or "en").lower()
    fam = _LANG_TO_FONT.get(code)
    if fam:
        pair = _INDIC_REGISTERED.get(fam)
        if pair:
            return pair
        if _native_font_fallback_allowed():
            _log.warning(
                "[milan_pdf] pdf_font_pair_fallback_Helvetica lang=%s mapped_family=%s "
                "reason=native_Noto_missing_or_failed_register",
                code,
                fam,
            )
            return "Helvetica", "Helvetica-Bold"
        raise MilanPdfNativeFontUnavailableError(
            f"_font_pair: lang={code!r} family={fam!r} not registered "
            "(should have been caught by _ensure_native_pdf_fonts_registered)."
        )
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


_BR_TAG_RE = re.compile(r"(?i)<br\s*/?>")


def _premium_prose_markup(raw: str) -> str:
    """Escape plain text, then map paragraph breaks to ReportLab `<br/>` tags.

    LLM copy may use `\\n\\n`, raw newlines, or `<br/>`; normalize so the
    PDF gets real vertical air (double break between paragraphs, single
    break inside a paragraph) without treating user `<` as HTML.
    """
    t = (raw or "").strip()
    if not t:
        return ""
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = _BR_TAG_RE.sub("\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    paras = [p.strip() for p in t.split("\n\n") if p.strip()]
    if not paras:
        return ""
    chunks: list[str] = []
    for para in paras:
        lines = [ln.strip() for ln in para.split("\n") if ln.strip()]
        if not lines:
            continue
        chunks.append("<br/>".join(_safe(ln) for ln in lines))
    return "<br/><br/>".join(chunks)


def _split_premium_plain_paragraphs(raw: str) -> list[str]:
    """Same paragraph boundaries as `_premium_prose_markup`, plain text."""
    t = (raw or "").strip()
    if not t:
        return []
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = _BR_TAG_RE.sub("\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return [p.strip() for p in t.split("\n\n") if p.strip()]


def _premium_chapter_dense_segments(plain: str) -> list[str]:
    """Split chapter prose into more stacked PDF paragraphs when the read is short.

    Does not invent text — only re-chunks existing words so `_premium_body_multi_paragraph_table`
    can apply row padding and (with ``relax`` body styles) roomier leading, which helps short
    chapters visually fill an A4 chapter page instead of sitting as one tight block at the top.
    """
    combined = (plain or "").strip()
    if not combined:
        return [""]
    parts = _split_premium_plain_paragraphs(combined)
    if not parts:
        return [combined]
    chunk_cp = 520
    segments: list[str] = []
    for p in parts:
        if len(p) > chunk_cp + 40:
            segments.extend(_chunk_oversized_paragraph(p, max_cp=chunk_cp))
        else:
            segments.append(p)
    guard = 0
    while len(segments) < 4 and guard < 16:
        guard += 1
        idx = max(range(len(segments)), key=lambda i: len(segments[i]))
        longest = segments[idx]
        if len(longest) < 260:
            break
        split_at = max(220, min(420, len(longest) // 2))
        pieces = _chunk_oversized_paragraph(longest, max_cp=split_at)
        if len(pieces) < 2:
            break
        segments[idx : idx + 1] = pieces
    out = [s.strip() for s in segments if s.strip()]
    return out if out else [combined]


def _chunk_oversized_paragraph(text: str, max_cp: int = 720) -> list[str]:
    """Split a single very long paragraph into readable PDF rows (no prose invention)."""
    t = (text or "").strip()
    if len(t) <= max_cp:
        return [t] if t else []
    out: list[str] = []
    start = 0
    n = len(t)
    while start < n:
        end = min(start + max_cp, n)
        if end < n:
            cut = t.rfind(". ", start + 200, end)
            if cut == -1:
                cut = t.rfind(" ", start + 280, end)
            if cut > start:
                end = cut + 1
        chunk = t[start:end].strip()
        if chunk:
            out.append(chunk)
        start = end
    return out


def _premium_body_table(
    markup: str, combined_plain: str, s: dict, *, relax: bool = False,
) -> Table:
    """Premium chapter-style body: padded column + relaxed leading."""
    _lang = s.get("_lang", "en")
    para = Paragraph(markup, _pick_body_premium(combined_plain, s, _lang, relax=relax))
    tbl = Table([[para]], colWidths=[180 * mm])
    tbl.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl


def _premium_body_multi_paragraph_table(
    s: dict, combined_plain: str, *, relax: bool = False,
) -> Table:
    """Render body as **multiple stacked paragraphs** (visual rhythm, not one mega-cell).

    Uses the same paragraph boundaries as `_premium_prose_markup`. Long single
    blobs are chunked by length only — no invented text.
    """
    _lang = s.get("_lang", "en")
    combined_plain = _latinize_pdf_plain(combined_plain, _lang)
    max_chunk = 620 if relax else 900
    parts: list[str] = []
    for block in _split_premium_plain_paragraphs(combined_plain):
        if len(block) > max_chunk:
            parts.extend(_chunk_oversized_paragraph(block, max_cp=max_chunk))
        else:
            parts.append(block)
    if not parts:
        return _premium_body_table(
            _premium_prose_markup(combined_plain) or _safe("—"),
            combined_plain or "—",
            s,
            relax=relax,
        )
    if len(parts) == 1:
        p0 = parts[0]
        return _premium_body_table(
            _premium_prose_markup(p0) or _safe(p0), p0, s, relax=relax,
        )
    rows: list[list[Any]] = []
    style_cmds: list[tuple[Any, ...]] = [
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for i, ptxt in enumerate(parts):
        mk = _premium_prose_markup(ptxt) or _safe(ptxt)
        para = Paragraph(mk, _pick_body_premium(ptxt, s, _lang, relax=relax))
        rows.append([para])
        top_pad = 6 if i == 0 else (12 if relax else 10)
        bot_pad = (12 if relax else 10) if i < len(parts) - 1 else 6
        style_cmds.append(("TOPPADDING", (0, i), (0, i), top_pad))
        style_cmds.append(("BOTTOMPADDING", (0, i), (0, i), bot_pad))
    tbl = Table(rows, colWidths=[180 * mm])
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def _bullet_cluster_table(s: dict, plain: str) -> Table | None:
    """If `plain` contains bullet lines, render as a tight bullet cluster; else None."""
    lines = [ln.strip() for ln in (plain or "").split("\n") if ln.strip()]
    bullets = [ln for ln in lines if ln.startswith(("•", "-", "–"))]
    if len(bullets) < 2:
        return None
    fname = s["body"].fontName if "body" in s else "Helvetica"
    rows: list[list[Any]] = []
    for i, b in enumerate(bullets[:8]):
        clean = b.lstrip("•-–").strip()
        if not clean:
            continue
        rows.append([
            Paragraph(
                f"<font color='{_hex(BRAND_GOLD)}'><b>·</b></font>"
                f"&nbsp;&nbsp;{_safe(clean)}",
                ParagraphStyle(
                    f"prem_bul_cluster_{i}",
                    fontName=fname,
                    fontSize=9.8,
                    leading=14,
                    textColor=TEXT_DARK,
                    leftIndent=2,
                    spaceAfter=4,
                ),
            ),
        ])
    if len(rows) < 2:
        return None
    t = Table(rows, colWidths=[176 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
        ("BOX", (0, 0), (-1, -1), 0.35, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _subsection_soft_rule() -> Table:
    """Subtle horizontal gap between major blocks (layout layering)."""
    t = Table([[""]], colWidths=[180 * mm], rowHeights=[0.01])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.45, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


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
    lg = getattr(doc, "milan_pdf_lang", None) or "en"
    footer_center = getattr(doc, "milan_pdf_footer_center", None)
    if footer_center is None:
        footer_center = (
            MPL.page_footer_center_pro(lg)
            if getattr(doc, "milan_pdf_footer_pro", False)
            else MPL.page_footer_center(lg)
        )
    canvas.drawCentredString(w / 2, 12 * mm, footer_center)
    pw = MPL.page_footer_page_word(lg)
    canvas.drawRightString(w - 15 * mm, 12 * mm, f"{pw} {doc.page}")
    canvas.restoreState()


# ── Style sheet ─────────────────────────────────────────────────────────
_INDIC_RANGES = (
    (0x0900, 0x097F),  # Devanagari (Hindi PDF lane)
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


_DEVA_STRIP_RE = re.compile(r"[\u0900-\u097F\u1CD0-\u1CFF\uA8E0-\uA8FF]+")


def _strip_devanagari_for_latin_pdf(text: str) -> str:
    """Remove Devanagari when Helvetica will render (avoids empty □ boxes)."""
    if not text:
        return ""
    out = _DEVA_STRIP_RE.sub(" ", text)
    return re.sub(r"\s+", " ", out).strip()


def _latinize_pdf_plain(text: str, lang: str) -> str:
    """Keep Indic text only when Noto Devanagari is registered; else Latin-safe."""
    if not text or not _has_indic(text):
        return text or ""
    register_indic_fonts()
    if _INDIC_REGISTERED.get("NotoDeva"):
        return text
    if (lang or "en").lower() in _LATIN_LANGS:
        return _strip_devanagari_for_latin_pdf(text)
    return text


def _pick_body(text: str, s: dict, lang: str = "en") -> ParagraphStyle:
    """Pick body style from actual text script.

    When polish succeeds for `lang=hi`, body uses Devanagari Noto. When
    deterministic Roman fallback fires under `hi`, Devanagari-capable fonts
    lack Latin glyphs → use Helvetica body so labels stay readable.
    """
    if (lang or "en").lower() in ("en", "hn"):
        return s["body"]
    return s["body"] if _has_indic(text) else s["body_latin"]


def _pick_body_premium(
    text: str, s: dict, lang: str = "en", *, relax: bool = False,
) -> ParagraphStyle:
    """Same script logic as `_pick_body`, with roomier leading for long prose."""
    register_indic_fonts()
    if _has_indic(text) and _INDIC_REGISTERED.get("NotoDeva"):
        key = "body_premium_indic_loose" if relax else "body_premium_indic"
        if key in s:
            return s[key]
    if relax:
        if (lang or "en").lower() in ("en", "hn"):
            return s["body_premium_latin_loose"] if _has_indic(text) else s["body_premium_loose"]
        return s["body_premium_loose"] if _has_indic(text) else s["body_premium_latin_loose"]
    if (lang or "en").lower() in ("en", "hn"):
        return s["body_premium_latin"] if _has_indic(text) else s["body_premium"]
    return s["body_premium"] if _has_indic(text) else s["body_premium_latin"]


def _styles(lang: str = "en") -> dict[str, ParagraphStyle]:
    register_indic_fonts()
    base = getSampleStyleSheet()
    H_REG, H_BOLD = _font_pair(lang)
    deva_reg = (_INDIC_REGISTERED.get("NotoDeva") or ("Helvetica", "Helvetica-Bold"))[0]
    deva_bold = (_INDIC_REGISTERED.get("NotoDeva") or ("Helvetica", "Helvetica-Bold"))[1]
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
        # Long-form premium prose (chapters, hidden truth, verdict): more
        # leading + paragraph tail so `<br/><br/>` blocks read as real air.
        "body_premium": ParagraphStyle(
            "body_premium", parent=base["BodyText"], fontName=H_REG,
            fontSize=10.25, leading=15.25, textColor=TEXT_DARK,
            spaceBefore=2, spaceAfter=8,
        ),
        "body_premium_latin": ParagraphStyle(
            "body_premium_latin", parent=base["BodyText"], fontName="Helvetica",
            fontSize=10.25, leading=15.25, textColor=TEXT_DARK,
            spaceBefore=2, spaceAfter=8,
        ),
        # Short premium chapters: slightly larger type + leading so the same
        # word-count occupies more vertical space on A4 (client "fill the page").
        "body_premium_loose": ParagraphStyle(
            "body_premium_loose", parent=base["BodyText"], fontName=H_REG,
            fontSize=10.85, leading=16.6, textColor=TEXT_DARK,
            spaceBefore=3, spaceAfter=11,
        ),
        "body_premium_latin_loose": ParagraphStyle(
            "body_premium_latin_loose", parent=base["BodyText"], fontName="Helvetica",
            fontSize=10.85, leading=16.6, textColor=TEXT_DARK,
            spaceBefore=3, spaceAfter=11,
        ),
        "body_premium_indic": ParagraphStyle(
            "body_premium_indic", parent=base["BodyText"],
            fontName=deva_reg,
            fontSize=10.25, leading=15.25, textColor=TEXT_DARK,
            spaceBefore=2, spaceAfter=8,
        ),
        "body_premium_indic_loose": ParagraphStyle(
            "body_premium_indic_loose", parent=base["BodyText"],
            fontName=deva_reg,
            fontSize=10.85, leading=16.6, textColor=TEXT_DARK,
            spaceBefore=3, spaceAfter=11,
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
        second = "Quiet Weeks, Loud Months"
    elif pct >= 50:
        if "adjust" in stab or "delay" in stab or manglik:
            second = "Slow-Maturing Bond"
        else:
            second = "Warm but Misaligned Weeks"
    else:
        second = "Thin Margin on Paper"
    return f"{first}  •  {second}"


def _cover_score_ratio(total: float, mx: int) -> float:
    try:
        return float(total) / max(float(mx), 1.0)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0



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
        out.append("Tone Clashes First")

    stab = (snap_tags.get("long_term_stability") or "").lower()
    if "adjust" in stab or "delay" in stab or manglik:
        out.append("Delayed Stability")
    elif "strong" in stab or "natural" in stab:
        out.append("Steady Surface Weeks")
    else:
        out.append("Uneven Rhythm")
    return out[:3]


_KOOT_STRENGTH_LANG = {
    "varna":   "social face stays even — who speaks first at gatherings rarely becomes a silent score",
    "vashya":  "one steers small plans, the other follows without a weekly power preamble",
    "tara":    "bad-day timing mis-fires less — apologies land before hurt hardens",
    "yoni":    "instinctive pace of closeness rhymes more than it surprises",
    "graha":   "under stress you still decode each other's mood faster than strangers would",
    "gana":    "fight cadence and 'who needs people after work' annoy less than when this is weak",
    "bhakoot": "money and in-law stress still happens — less of the stuck loop this koot flags when bad",
    "nadi":    "body-weeks and tiredness patterns do not mirror — one crashes while the other catches second wind",
}
_KOOT_DAMAGE_LANG = {
    "varna":   "ego bruises show up as cold courtesy, not raised voices",
    "vashya":  "who leads daily micro-decisions becomes the unnamed argument",
    "tara":    "right sentence, wrong hour — small misses stack as 'you never get me'",
    "yoni":    "touch and irritation spike together — pace mismatch, not lack of care",
    "graha":   "same stress week reads as attack vs shutdown depending who you are",
    "gana":    "one wants noise after work, the other wants a cave — same evening, two needs",
    "bhakoot": "life-direction math quietly diverges — savings, city, parents' expectations",
    "nadi":    "mirrored fatigue weeks — both tired the same Tuesday without blaming a task",
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


def _koot_match_ratio(koots: list, canon: str) -> float | None:
    """``score/max`` for the first koot whose canonical key matches ``canon``."""
    for k in koots or []:
        if _canon_koot_key(k) != canon:
            continue
        mx = float(k.get("max") or 0)
        if mx <= 0:
            return None
        return float(k.get("score") or 0) / mx
    return None


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
            "Even where scores look ordinary on paper, the lived bond "
            "often shows up first in small habits — who texts first after "
            "a freeze, who carries the calendar — before any big declaration."
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
            "<b>Manglik skew</b>: one chart carries a hotter Mars edge — "
            "ignition points cluster around travel, sleep, and who initiates "
            "hard talks after 10 p.m., not around 'fate' headlines."
        )
    if not out:
        out.append(
            "Quiet risk here is the same as most kitchens — unspoken "
            "division of labour and who goes silent first after a bad week; "
            "the chart only maps where that silence likes to sit."
        )
    return out[:5]


def _practical_paragraphs(payload: dict) -> list[str]:
    """Page 11 prose — money, family, lifestyle (derived from score + section)."""
    pct = (float(payload.get("total", 0))
           / max(float(payload.get("max", 36)), 1)) * 100
    paras: list[str] = []
    if pct >= 70:
        paras.append(
            "Practical weeks here often look boring from outside — money "
            "talk, in-laws, chores — because friction surfaces early as "
            "irritation in tone, not as missing love."
        )
    elif pct >= 50:
        paras.append(
            "Household load and family-side pressure tend to find the same "
            "two people on opposite sides of the calendar — who travels for "
            "which festival, who texts the landlord — that is where this "
            "band shows first."
        )
    else:
        paras.append(
            "Lower classical totals usually mean money and extended-family "
            "math stay tense until roles are named plainly — not because "
            "effort is absent, but because assumptions stay unpriced."
        )
    if _is_manglik(payload):
        paras.append(
            "Manglik skew shows up as uneven appetite for big joint bets "
            "early — loans, shared property, one-name-on-paper moves — "
            "one side wants speed, the other wants a season of ordinary "
            "weeks first."
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
        "<b>The deeper read:</b> the chart maps tendencies in tone and "
        "timing — who goes quiet first, who carries which week — not a "
        "grade on character."
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
                lang: str, koots: list | None = None) -> list[Any]:
    """PAGE 1 — Clean client cover: brand, title, attribution, couple, score, mood."""
    H_REG, H_BOLD = _font_pair(lang)
    out: list[Any] = []
    grade_label = (grade or {}).get("label") or ""
    grade_color = (grade or {}).get("color") or _hex(BRAND_PURPLE)

    out.append(Spacer(1, 10 * mm))

    out.append(Paragraph(
        f"<font color='{_hex(BRAND_GOLD)}'><b>COSMIC LENS</b></font>",
        ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=11,
                       leading=15, alignment=TA_CENTER, spaceAfter=6),
    ))
    out.append(_gold_rule(52))
    out.append(Spacer(1, 10))

    out.append(Paragraph(
        MPL.cover_title(lang),
        ParagraphStyle("hero_title", fontName="Helvetica-Bold", fontSize=24,
                       leading=30, alignment=TA_CENTER,
                       textColor=BRAND_PURPLE, spaceAfter=4),
    ))
    out.append(Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'>{_safe(MPL.cover_subtitle(lang))}</font>",
        ParagraphStyle("hero_sub", fontName=H_REG, fontSize=11,
                       leading=15, alignment=TA_CENTER, spaceAfter=10),
    ))

    out.append(Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'>{_safe(MPL.cover_prepared_line(lang))} "
        f"<b>Ashutosh Bharadwaj</b></font>",
        ParagraphStyle("cov_prep", fontName=H_REG, fontSize=9.2,
                       leading=13, alignment=TA_CENTER,
                       textColor=TEXT_SOFT, spaceAfter=4),
    ))
    out.append(Paragraph(
        f"<font color='{_hex(BRAND_GOLD)}'><b>"
        f"{_safe(MPL.cover_powered_line(lang))}</b></font>",
        ParagraphStyle("hero_brand", fontName="Helvetica-Bold", fontSize=9,
                       leading=12, alignment=TA_CENTER, spaceAfter=14),
    ))

    out.append(Spacer(1, 5 * mm))

    out.append(Paragraph(
        f"<b>{_safe(p1.get('name'))}</b>"
        f"<font color='{_hex(TEXT_SOFT)}'>  &nbsp;·&nbsp;  </font>"
        f"<b>{_safe(p2.get('name'))}</b>",
        ParagraphStyle("hero_names", fontName=H_BOLD, fontSize=26,
                       leading=32, alignment=TA_CENTER,
                       textColor=TEXT_DARK, spaceAfter=6),
    ))
    out.append(Paragraph(
        f"<font color='{_hex(TEXT_MID)}'>{_safe(MPL.cover_generated_prefix(lang))} "
        f"{datetime.utcnow().strftime('%d %B %Y')}</font>",
        ParagraphStyle("hero_date", fontName=H_REG, fontSize=10.5,
                       leading=13, alignment=TA_CENTER, spaceAfter=16),
    ))

    score_p = Paragraph(
        f"<b>{_safe(total)}</b>"
        f"<font color='{_hex(TEXT_SOFT)}' size=18> / {_safe(mx)}</font>",
        ParagraphStyle("hero_score", fontName="Helvetica-Bold", fontSize=50,
                       leading=58, alignment=TA_CENTER,
                       textColor=BRAND_PURPLE),
    )
    grade_p = Paragraph(
        f"<b>{_safe(grade_label).upper()}</b>" if grade_label else "",
        ParagraphStyle("hero_grade", fontName="Helvetica-Bold", fontSize=11.5,
                       leading=15, alignment=TA_CENTER,
                       textColor=colors.HexColor(grade_color)),
    )
    card = Table([[score_p], [Spacer(1, 2)], [grade_p]],
                 colWidths=[118 * mm])
    card.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), _BG_HERO),
        ("BOX",          (0, 0), (-1, -1), 1.2, BRAND_GOLD),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 20),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 20),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    centered = Table([[card]], colWidths=[180 * mm])
    centered.setStyle(TableStyle([
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    out.append(centered)
    out.append(Spacer(1, 10))

    rt = _relationship_type_tag(grade, snap, total, mx, manglik)
    out.append(Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'><b>{_safe(rt)}</b></font>",
        ParagraphStyle("hero_tag", fontName="Helvetica-Bold", fontSize=11,
                       leading=16, alignment=TA_CENTER, spaceAfter=0),
    ))

    out.append(PageBreak())
    return out


def _chapter_eyebrow(num: int, label: str, lang: str = "en") -> Paragraph:
    pref = MPL.chapter_prefix(lang)
    lab = label if MPL.pdf_ui_hn(lang) else label.upper()
    return Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'><b>"
        f"{pref} {num:02d}  ·  {lab}</b></font>",
        ParagraphStyle("eyebrow", fontName="Helvetica-Bold", fontSize=9,
                       leading=12, spaceAfter=6),
    )


def _chapter_title_block(title: str, subtitle: str, s: dict | None = None) -> list[Any]:
    # Phase 2.5.11.24: title + subtitle carry user-facing dynamic text
    # (often partner names + chapter names) — must respect the lang font
    # so Indic scripts don't render as tofu boxes.
    lg = str((s or {}).get("_lang") or "en")
    title = _latinize_pdf_plain(title, lg)
    subtitle = _latinize_pdf_plain(subtitle, lg)
    h_bold = (s or {}).get("h1").fontName if (s and "h1" in s) else "Helvetica-Bold"
    h_reg  = (s or {}).get("body").fontName if (s and "body" in s) else "Helvetica"
    if _has_indic(title) or _has_indic(subtitle):
        pair = _INDIC_REGISTERED.get("NotoDeva")
        if pair:
            h_bold, h_reg = pair[1], pair[0]
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


def _premium_chapter_primary_narrative(ch: dict | None) -> str:
    """Single consultation body for premium chapter pages (``chapter_body`` first)."""
    if not isinstance(ch, dict):
        return ""
    cb = str(ch.get(CHAPTER_BODY_KEY) or "").strip()
    if cb:
        return cb
    fr = str(ch.get("full_read") or "").strip()
    if fr:
        return fr
    bits = [str(ch.get(sk) or "").strip() for sk in CHAPTER_SECTION_KEYS if str(ch.get(sk) or "").strip()]
    if bits:
        return "\n\n".join(bits)
    return " ".join(
        x for x in (
            (ch.get("kya_dikh") or "").strip(),
            (ch.get("kya_matlab") or "").strip(),
            (ch.get("kya_dhyan") or "").strip(),
        ) if x
    )


def _premium_compact_bridge_card(
    s: dict,
    title_label: str,
    body: str,
    *,
    max_chars: int = 280,
) -> Table:
    """Compact premium insight strip — not a long essay card."""
    g_reg = (s.get("body").fontName if s and "body" in s else "Helvetica")
    txt = (body or "").strip()
    if len(txt) > max_chars:
        txt = txt[: max_chars - 1].rsplit(" ", 1)[0].strip() + "…"
    gp = Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'><b>{_safe(title_label)}</b></font>  "
        f"<font color='{_hex(TEXT_MID)}'>{_safe(txt)}</font>",
        ParagraphStyle(
            "prem_bridge_compact",
            fontName=g_reg,
            fontSize=7.85,
            leading=11,
            textColor=TEXT_MID,
        ),
    )
    t = Table([[gp]], colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), BG_CARD),
        ("LINEABOVE",    (0, 0), (-1, 0), 0.55, BRAND_GOLD),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    return t


def _chart_note_card(s: dict, snippet: str) -> Table:
    """Short chart-linked insight (top-of-chapter rhythm)."""
    lg = str(s.get("_lang") or "en")
    return _premium_compact_bridge_card(s, MPL.chart_insight_arrow(lg), snippet, max_chars=260)


def _prose_and_bullet_lines(plain: str) -> tuple[str, list[str]]:
    lines = [ln.strip() for ln in (plain or "").split("\n")]
    non_bul = [ln for ln in lines if ln and not ln.startswith(("•", "-", "–"))]
    bul = [ln for ln in lines if ln.startswith(("•", "-", "–"))]
    return "\n\n".join(non_bul), bul


def _grounding_card(
    s: dict,
    grounding: str,
    *,
    title: str | None = None,
    max_body_chars: int | None = None,
    compact: bool = False,
) -> Table:
    # Phase 2.5.11.24: `grounding` is dynamic prose written by the LLM in
    # the target lane — use the styles dict font (`hi` → Noto Devanagari;
    # `en`/`hn` → Latin stack) so Indic grounding never renders as Helvetica tofu.
    lg = str(s.get("_lang") or "en")
    if title is None:
        title = MPL.grounding_why_title(lg)
    g_reg = (s.get("body").fontName if s and "body" in s else "Helvetica")
    body = (grounding or "").strip()
    if max_body_chars is not None and len(body) > max_body_chars:
        body = body[: max_body_chars - 1].rsplit(" ", 1)[0].strip() + "…"
    fs = 7.75 if compact else 8.5
    ld = 11 if compact else 12
    gp = Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'><b>{_safe(title)}</b></font>  "
        f"<font color='{_hex(TEXT_MID)}'><i>{_safe(body)}</i></font>",
        ParagraphStyle(
            "ground_pretty_compact" if compact else "ground_pretty_full",
            fontName=g_reg,
            fontSize=fs,
            leading=ld,
            textColor=TEXT_MID,
        ),
    )
    top_pad, bot_pad = (6, 6) if compact else (8, 8)
    t = Table([[gp]], colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), BG_TINT),
        ("LINEABOVE",    (0, 0), (-1, 0), 0.6, BRAND_GOLD),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), top_pad),
        ("BOTTOMPADDING",(0, 0), (-1, -1), bot_pad),
    ]))
    return t


def _chapter_page(s: dict, num: int, eyebrow: str, title: str,
                  subtitle: str, body: str,
                  grounding: str = "") -> list[Any]:
    """One full premium chapter page: eyebrow + title + subtitle + body."""
    lg = str(s.get("_lang") or "en")
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, eyebrow, lg))
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
    lg = str(s.get("_lang") or "en")
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, eyebrow, lg))
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


def _premium_consultation_blocks_page(
    s: dict,
    num: int,
    eyebrow: str,
    title: str,
    subtitle: str,
    blocks: list[str],
) -> list[Any]:
    """Premium Pro pages for ``special`` / ``damage``: multi-paragraph consultation, not diamond bullets."""
    lg = str(s.get("_lang") or "en")
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, eyebrow, lg))
    out.extend(_chapter_title_block(title, subtitle, s))
    cleaned = [str(b).strip() for b in (blocks or []) if str(b).strip()]
    if not cleaned:
        out.append(
            _premium_body_multi_paragraph_table(
                s,
                MPL.consultation_empty(lg),
                relax=False,
            )
        )
        out.append(PageBreak())
        return out
    for bi, block in enumerate(cleaned):
        out.append(_premium_body_multi_paragraph_table(s, block, relax=False))
        out.append(Spacer(1, 8))
        bt = _bullet_cluster_table(s, block)
        if bt is not None:
            out.append(Spacer(1, 4))
            out.append(bt)
        if bi < len(cleaned) - 1:
            out.append(Spacer(1, 8))
            out.append(_subsection_soft_rule())
            out.append(Spacer(1, 5))
    out.append(PageBreak())
    return out


def _snapshot_clip_plain(text: str, max_chars: int = 500) -> str:
    plain = re.sub(r"\s+", " ", (text or "").strip())
    if len(plain) <= max_chars:
        return plain
    cut = plain[: max_chars - 1].rsplit(" ", 1)[0].strip()
    return (cut or plain[: max_chars]) + "…"


def _snapshot_opening_paragraph(
    snap: dict,
    koots: list,
    manglik: bool,
    total: float,
    mx: int,
    p1: dict,
    p2: dict,
    lang: str = "en",
) -> str:
    """One emotionally intelligent lede — API summary when present, else chart-grounded."""
    raw = str((snap or {}).get("summary") or "").strip()
    if raw:
        return _snapshot_clip_plain(raw, 500)
    n1 = (p1.get("name") or MPL.partner_default(lang, 1)).strip()
    n2 = (p2.get("name") or MPL.partner_default(lang, 2)).strip()
    tags = (snap or {}).get("tags") or {}
    pull = str(tags.get("emotional_pull") or "").strip()
    stab = str(tags.get("long_term_stability") or "").strip()
    mp = str(tags.get("marriage_potential") or "").strip()
    r = _cover_score_ratio(total, mx)
    if MPL.pdf_ui_hn(lang):
        mood_band = "high" if r >= 0.67 else ("mid" if r >= 0.45 else "low")
        tag_bits: list[str] = []
        if pull:
            tag_bits.append(MPL.snap_tag_bit_pull(lang, pull))
        if mp:
            tag_bits.append(MPL.snap_tag_bit_mp(lang, mp))
        if stab:
            tag_bits.append(MPL.snap_tag_bit_stab(lang, stab))
        tag_sentence = (
            " ".join(tag_bits) if tag_bits else MPL.snap_tag_sentence_empty(lang)
        )
        return MPL.snap_opening(lang, n1, n2, mood_band, tag_sentence, manglik)
    mood = (
        "The classical tally sits in a generous band — affection has room to deepen "
        "without every week becoming a referendum on the bond."
        if r >= 0.67
        else (
            "The classical tally sits in a workable middle — love here proves itself "
            "in patience after ordinary stress, not only in peak moments."
            if r >= 0.45
            else (
                "The paper margin is modest — many enduring marriages live here when "
                "both people name rhythms early instead of letting silence archive hurt."
            )
        )
    )
    tag_bits = []
    if pull:
        tag_bits.append(f"Emotional pull reads as {pull.lower()}.")
    if mp:
        tag_bits.append(f"Marriage potential reads as {mp.lower()}.")
    if stab:
        tag_bits.append(f"Long-horizon stability reads as {stab.lower()}.")
    tag_sentence = " ".join(tag_bits) if tag_bits else (
        "The Ashtakoot row and the chapters that follow anchor this reading in "
        "chart-visible habits and lived marriage observation."
    )
    mars = (
        " Mars heat is present on one chart — steadiness grows when storms are "
        "named calmly, not dramatised."
        if manglik
        else ""
    )
    return (
        f"{n1} and {n2}: {mood} {tag_sentence}"
        f"{mars} The sections that follow translate these signals into lived "
        f"marriage observation — tone, timing, and repair — not abstract scores."
    )


def _snapshot_tag_microcopy(tag: str, snap: dict, koots: list, manglik: bool,
                            lang: str = "en") -> str:
    """2–3 lines per snapshot descriptor; chart hooks where the tag implies them."""
    if MPL.pdf_ui_hn(lang):
        return MPL.snap_microcopy_body_hn(tag)
    tags = (snap or {}).get("tags") or {}
    pull_h = str(tags.get("emotional_pull") or "").strip()
    stab_h = str(tags.get("long_term_stability") or "").strip()
    tr = _koot_match_ratio(koots, "tara")
    br = _koot_match_ratio(koots, "bhakoot")
    yr = _koot_match_ratio(koots, "yoni")
    gr = _koot_match_ratio(koots, "gana")

    if tag == "Quiet Pull":
        hook = ""
        if yr is not None and yr < 0.45:
            hook = (
                " Your Yoni ratio supports a pace gap more than a chemistry verdict — "
                "tenderness and irritation can share the same evening."
            )
        elif tr is not None and tr < 0.45:
            hook = (
                " With Tara throttled, the bond often needs calendar-aware repair — "
                "the right sentence lands better on a different hour."
            )
        return (
            "This is rarely coldness; it usually reads as a softer throttle on big "
            "emotional theatre — one of you may warm up slowly after overload, or "
            "show care through consistency before words catch up."
            f"{hook} Naming the pace out loud prevents quiet stories of rejection."
        )

    if tag == "Delayed Stability":
        bits = [
            "Horizon comfort may mature in chapters rather than lightning — common when "
            "timing, life-direction math, or Mars pacing asks for steadier sequencing "
            "before milestones feel obvious on the outside.",
        ]
        if manglik:
            bits.append(
                " Manglik skew adds heat to ignition points — travel, sleep debt, "
                "and who initiates hard talks late night — not a headline fate verdict."
            )
        if br is not None and br < 0.5:
            bits.append(
                " Bhakoot under strain still allows loyalty; it asks for explicit "
                "alignment on city, savings, and parental expectations before they "
                "become silent scorecards."
            )
        elif tr is not None and tr < 0.55:
            bits.append(
                " Tara in a middling lane means repair is learnable — lead with one "
                "soft sentence before the full briefing so the nervous system can follow."
            )
        return " ".join(bits)

    if tag == "Deep Attachment":
        return (
            "The snapshot reads a high emotional charge — affection tends to arrive "
            "with intensity, memory, and a hunger to be mirrored. The work is not "
            "dialing love down; it is keeping pride from hijacking vulnerable hours "
            "when stress stacks."
        )

    if tag == "Steady Affection":
        return (
            "Medium pull is often the unsung marriage band — fewer fireworks, more "
            "repeatable kindness. The bond deepens when micro-bids for connection "
            "(a glance, a check-in) are answered more often than they are postponed."
        )

    if tag == "Tone Clashes First":
        ghook = ""
        if gr is not None and gr < 0.55:
            ghook = (
                " Gana is uneven here — one nervous system may want noise after work "
                "while the other wants a cave; same evening, two legitimate needs."
            )
        return (
            "Friction tends to show up first as tone, tired voice, or timing — before "
            "the actual topic is fully spoken. That pattern is repairable when both "
            "people treat the opening minute of a talk as sacred real estate."
            f"{ghook}"
        )

    if tag == "Steady Surface Weeks":
        return (
            "Day-to-day life can look calm even while deeper planning is still "
            "catching up — useful when you refuse to confuse peaceful weeks with "
            "finished alignment on money, boundaries, or extended family."
        )

    if tag == "Uneven Rhythm":
        return (
            "Good weeks and wobbly weeks may alternate without a dramatic cause — "
            f"often a Tara/Yoni echo when timing and touch do not line up cleanly. "
            f"Pull signal: emotional pull is described as {pull_h or 'mixed'} and "
            f"stability language as {stab_h or 'mixed'} — naming the uneven beat "
            f"prevents catastrophising ordinary human variance."
        )

    return (
        "This shorthand summarises a rhythm in your chart mix — the numbered "
        "chapters later spell out the lived choreography behind the label."
    )


def _snapshot_ashtakoot_lived_meaning(koots: list, total: float, mx: int,
                                      lang: str = "en") -> str:
    """Single paragraph: what the eight scores mean in real weeks (chart-grounded)."""
    if not koots:
        return MPL.snap_ashtakoot_empty_koots(lang)
    st_map = MPL._KOOT_STRENGTH_HN if MPL.pdf_ui_hn(lang) else _KOOT_STRENGTH_LANG
    dmg_map = MPL._KOOT_DAMAGE_HN if MPL.pdf_ui_hn(lang) else _KOOT_DAMAGE_LANG
    r_all = float(total) / max(float(mx), 1.0)
    strong = [
        k for k in koots
        if int(k.get("max") or 0) >= 4 and k.get("score", 0) == k.get("max", 0)
    ]
    dosha = [k for k in koots if k.get("score", 0) == 0 and int(k.get("max") or 0) > 0]
    weak = sorted(
        [
            k for k in koots
            if int(k.get("max") or 0) >= 4
            and 0 < float(k.get("score") or 0) <= float(k.get("max") or 1) / 2
        ],
        key=lambda k: float(k.get("score") or 0),
    )
    pieces = [MPL.snap_ashtakoot_open_piece(lang)]
    if r_all >= 0.72:
        pieces.append(MPL.snap_ashtakoot_high_total(lang))
    elif r_all <= 0.42:
        pieces.append(MPL.snap_ashtakoot_low_total(lang))
    for k in strong[:2]:
        ck = _canon_koot_key(k)
        ln = st_map.get(ck)
        if ln:
            lbl = k.get("label", MPL.koot_label_this(lang))
            pieces.append(MPL.snap_ashtakoot_koot_suffix(lang, str(lbl), ln))
    for k in (dosha[:1] + weak[:1]):
        ck = _canon_koot_key(k)
        ln = dmg_map.get(ck)
        if ln:
            label = k.get("label", MPL.koot_label_this(lang))
            mark = MPL.koot_score_note_dosha(lang) if k.get("score", 0) == 0 else MPL.koot_score_note_low(lang)
            pieces.append(MPL.snap_ashtakoot_damage_suffix(lang, str(label), mark, ln))
    return _snapshot_clip_plain(" ".join(pieces), 560)


def _snapshot_bond_strength_paragraph(payload: dict, lang: str = "en") -> str:
    parts: list[str] = []
    koots = payload.get("koots") or []
    st_map = MPL._KOOT_STRENGTH_HN if MPL.pdf_ui_hn(lang) else _KOOT_STRENGTH_LANG
    strong = [
        k for k in koots
        if int(k.get("max") or 0) >= 4 and k.get("score", 0) == k.get("max", 0)
    ]
    for k in strong[:2]:
        ck = _canon_koot_key(k)
        ln = st_map.get(ck)
        if ln:
            parts.append(f"{k.get('label', '')} ({ln})")
    analysis = payload.get("analysis") or {}
    strengths = analysis.get("strengths") if isinstance(analysis.get("strengths"), list) else []
    for st in strengths[:1]:
        t = str(st).strip()
        if t:
            parts.append(t)
    if not parts:
        parts.append(MPL.snap_bond_strength_fallback(lang))
    body = MPL.snap_bond_strength_wrap(lang, "; ".join(parts))
    return _snapshot_clip_plain(body, 360)


def _snapshot_bond_challenge_paragraph(payload: dict, lang: str = "en") -> str:
    parts: list[str] = []
    koots = payload.get("koots") or []
    dmg_map = MPL._KOOT_DAMAGE_HN if MPL.pdf_ui_hn(lang) else _KOOT_DAMAGE_LANG
    dosha = [k for k in koots if k.get("score", 0) == 0 and int(k.get("max") or 0) > 0]
    weak = sorted(
        [
            k for k in koots
            if int(k.get("max") or 0) >= 4
            and 0 < float(k.get("score") or 0) <= float(k.get("max") or 1) / 2
        ],
        key=lambda k: float(k.get("score") or 0),
    )
    for k in (dosha[:1] + weak[:1]):
        ck = _canon_koot_key(k)
        ln = dmg_map.get(ck)
        if ln:
            parts.append(f"{k.get('label', '')}: {ln}")
    analysis = payload.get("analysis") or {}
    chal = analysis.get("challenges") if isinstance(analysis.get("challenges"), list) else []
    for c in chal[:1]:
        t = str(c).strip()
        if t:
            parts.append(t)
    if _is_manglik(payload):
        parts.append(MPL.snap_bond_challenge_manglik_extra(lang))
    if not parts:
        parts.append(MPL.snap_bond_challenge_fallback(lang))
    body = MPL.snap_bond_challenge_wrap(lang, " ".join(parts))
    return _snapshot_clip_plain(body, 380)


def _snapshot_insight_cell(s: dict, title: str, body: str) -> Table:
    fn = s["body"].fontName
    p = Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(title)}</b></font><br/>"
        f"<font color='{_hex(TEXT_MID)}'>{_safe(body)}</font>",
        ParagraphStyle(
            "snap_ins_cell",
            fontName=fn,
            fontSize=8.65,
            leading=12.6,
            textColor=TEXT_MID,
        ),
    )
    t = Table([[p]], colWidths=[180 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), BG_CARD),
        ("LINEABOVE",    (0, 0), (-1, 0), 0.85, BRAND_GOLD),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
        ("BOX",          (0, 0), (-1, -1), 0.45, BORDER),
    ]))
    return t


def _snapshot_pair_footer(s: dict, left_title: str, left_body: str,
                         right_title: str, right_body: str) -> Table:
    fn = s["body"].fontName
    ps = ParagraphStyle(
        "snap_pair_ft",
        fontName=fn,
        fontSize=8.2,
        leading=11.8,
        textColor=TEXT_MID,
    )
    lp = Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(left_title)}</b></font><br/>"
        f"<font color='{_hex(TEXT_MID)}'>{_safe(left_body)}</font>",
        ps,
    )
    rp = Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(right_title)}</b></font><br/>"
        f"<font color='{_hex(TEXT_MID)}'>{_safe(right_body)}</font>",
        ps,
    )
    t = Table([[lp, rp]], colWidths=[88 * mm, 88 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (0, -1), BG_TINT),
        ("BACKGROUND",   (1, 0), (1, -1), BG_TINT),
        ("BOX",          (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEABOVE",    (0, 0), (-1, 0), 0.85, BRAND_GOLD),
        ("LEFTPADDING",  (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _snapshot_page(
    s: dict,
    num: int,
    snap: dict,
    koots: list,
    manglik: bool,
    total: float,
    mx: int,
    payload: dict | None = None,
) -> list[Any]:
    """PAGE 2 — Relationship Snapshot: premium insight layout (chart-grounded prose)."""
    pl: dict = payload if isinstance(payload, dict) else {}
    p1 = pl.get("p1") or {}
    p2 = pl.get("p2") or {}
    lg = str(s.get("_lang") or "en")
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, MPL.snap_eyebrow(lg), lg))
    out.extend(_chapter_title_block(
        MPL.snap_title(lg),
        MPL.snap_subtitle(lg),
    ))

    open_txt = _snapshot_opening_paragraph(snap, koots, manglik, total, mx, p1, p2, lg)
    out.append(Paragraph(
        _safe(open_txt),
        ParagraphStyle(
            "snap_open",
            fontName=s["body"].fontName,
            fontSize=10.25,
            leading=15,
            textColor=TEXT_DARK,
            spaceAfter=0,
        ),
    ))
    out.append(Spacer(1, 7))

    tags = (snap or {}).get("tags") or {}
    if tags:
        def _ind(label: str, value: str) -> Table:
            t = Table(
                [[Paragraph(_safe(label if MPL.pdf_ui_hn(lg) else label.upper()), s["tag_label"])],
                 [Paragraph(f"<b>{_safe(value)}</b>", s["tag_value"])]],
                colWidths=[58 * mm],
            )
            t.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, -1), colors.white),
                ("BOX",          (0, 0), (-1, -1), 0.6, BORDER),
                ("LINEABOVE",    (0, 0), (-1, 0), 2, BRAND_PURPLE),
                ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",   (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 9),
            ]))
            return t
        row = Table([[
            _ind(MPL.snap_tag_emotional_pull(lg),     tags.get("emotional_pull",     "—")),
            _ind(MPL.snap_tag_marriage_potential(lg), tags.get("marriage_potential", "—")),
            _ind(MPL.snap_tag_long_term(lg), tags.get("long_term_stability", "—")),
        ]], colWidths=[60 * mm, 60 * mm, 60 * mm])
        row.setStyle(TableStyle([
            ("LEFTPADDING",  (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ]))
        out.append(row)
        out.append(Spacer(1, 7))

    pill_tags = _relationship_tags(snap, koots, manglik)
    for tag in pill_tags:
        body = _snapshot_tag_microcopy(tag, snap, koots, manglik, lg)
        title_disp = MPL.snap_pill_title(lg, tag)
        out.append(_snapshot_insight_cell(s, title_disp, body))
        out.append(Spacer(1, 5))

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
                    f"{_safe(k.get('label', ''))}</font>",
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
                ("TOPPADDING",   (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
            ]))
            badge_cells.append(cell)
        while len(badge_cells) < 8:
            badge_cells.append(Spacer(1, 1))
        strip = Table([badge_cells], colWidths=[22 * mm] * 8)
        strip.setStyle(TableStyle([
            ("LEFTPADDING",  (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ]))
        out.append(Paragraph(
            f"<font color='{_hex(TEXT_SOFT)}'><b>"
            f"{MPL.snap_ashtakoot_row_label(lg)}  ·  {_safe(total)} / {_safe(mx)}</b></font>",
            ParagraphStyle("ash_lbl", fontName="Helvetica-Bold", fontSize=8,
                           leading=10, spaceAfter=3),
        ))
        out.append(strip)
        out.append(Spacer(1, 4))
        ash_mean = _snapshot_ashtakoot_lived_meaning(koots, total, mx, lg)
        out.append(Paragraph(
            _safe(ash_mean),
            ParagraphStyle(
                "snap_ash_mean",
                fontName=s["body"].fontName,
                fontSize=8.55,
                leading=12.4,
                textColor=TEXT_MID,
            ),
        ))

    out.append(Spacer(1, 6))
    out.append(_snapshot_pair_footer(
        s,
        MPL.snap_pair_strength_title(lg),
        _snapshot_bond_strength_paragraph(pl, lg),
        MPL.snap_pair_challenge_title(lg),
        _snapshot_bond_challenge_paragraph(pl, lg),
    ))
    out.append(PageBreak())
    return out


# Non-Pro chapter chrome: ``vedic.compat.milan_pdf_locale.basic_chapter_rows``.


# ── Public entry-point ─────────────────────────────────────────────────
def render_milan_pdf(payload: dict, lang: str = "en") -> bytes:
    """Render a /api/kundli-milan response payload to a PDF byte string.

    Always returns valid PDF bytes (never raises on missing/partial fields)
    so the caller can stream the result directly to the client. Prefers
    the new 7-section deep schema in `payload["analysis"]`; falls back to
    the legacy 4-key flat schema when only that exists.
    """
    lang = _normalize_milan_pdf_lang(lang)
    _ensure_native_pdf_fonts_registered(lang)
    _log_pdf_font_lane(lang)
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
    _PLACEHOLDER = MPL.basic_placeholder_section(lang)

    story: list[Any] = []

    # ── PAGE 1 — Cover ──────────────────────────────────────────────
    story.extend(_cover_page(
        s, p1, p2, total, mx, grade, snapshot, manglik, lang, koots,
    ))

    # ── PAGE 2 — Relationship Snapshot ──────────────────────────────
    story.extend(_snapshot_page(
        s, 2, snapshot, koots, manglik, total, mx, payload=payload,
    ))

    # ── PAGES 3–8 — always exactly 6 chapter pages ──────────────────
    # Per chapter: prefer deep-schema {text, grounding}; else legacy
    # fallback text; else a deterministic placeholder. Page count is
    # locked at 12 regardless of which schema the LLM polish returned.
    chap_num = 3
    chapter_rows = MPL.basic_chapter_rows(lang)
    for key, eyebrow, title, subtitle in chapter_rows:
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
        s, chap_num, MPL.special_eyebrow(lang),
        MPL.special_title(lang),
        MPL.basic_bond_special_subtitle(lang),
        _derive_special_bullets(payload),
    )); chap_num += 1

    # ── PAGE 10 — What Can Quietly Damage (derived) ─────────────────
    story.extend(_bullets_page(
        s, chap_num, MPL.basic_damage_eyebrow(lang),
        MPL.damage_title(lang),
        MPL.damage_subtitle(lang),
        _derive_damage_bullets(payload),
    )); chap_num += 1

    # ── PAGE 11 — Practical Life Together (derived) ─────────────────
    practical_paras = _practical_paragraphs(payload)
    story.append(_chapter_eyebrow(chap_num, MPL.basic_practical_eyebrow(lang), lang))
    story.extend(_chapter_title_block(
        MPL.basic_practical_title(lang),
        MPL.basic_practical_subtitle(lang),
    ))
    for para in practical_paras:
        story.append(Paragraph(_safe(para), s["body"]))
        story.append(Spacer(1, 8))
    story.append(PageBreak()); chap_num += 1

    # ── PAGE 12 — Final Relationship Outlook (derived) ──────────────
    story.append(_chapter_eyebrow(chap_num, MPL.basic_final_outlook_eyebrow(lang), lang))
    story.extend(_chapter_title_block(
        MPL.basic_final_outlook_title(lang),
        MPL.basic_final_outlook_subtitle(lang),
    ))
    for para in _final_paragraphs(payload):
        story.append(Paragraph(_safe(para), s["body"]))
        story.append(Spacer(1, 8))
    story.append(Spacer(1, 12))
    story.append(_disclaimer(s))

    doc.milan_pdf_lang = lang
    doc.milan_pdf_footer_pro = False

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════
# Phase 2.5.11.23 — "Premium Relationship Truth" Pro PDF renderer
# ──────────────────────────────────────────────────────────────────────
# Public entry-point: render_milan_pro_pdf(payload, lang)
#
# Expects payload to carry standard /api/kundli-milan fields PLUS a
# `pro_premium` block produced by `vedic/compat/premium_chapters.py`:
#   pro_premium = {
#     hidden_truth: str,
#     chapters: [ {key, title, score_0_10, full_read, grounding}, ... 7 ],
#     special: [3 strs], damage: [strs], practical: [3 strs],
#     verdict: str,
#     _meta: { kp_promise: STRONG|PARTIAL|WEAK, hidden_signature: str }
#   }
# Page count follows the story below (chart page removed — see render body).
# Pro chapter eyebrows/titles/subtitles: ``vedic.compat.milan_pdf_locale.pro_chapter_rows``.
# ══════════════════════════════════════════════════════════════════════


def _pro_hidden_truth_page(s: dict, num: int, hidden_truth: str,
                           kp_meta: dict, p1_name: str, p2_name: str
                           ) -> list[Any]:
    """P3 — What's Hidden Underneath: KP marriage promise + signature."""
    lg = str(s.get("_lang") or "en")
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, MPL.hidden_eyebrow(lg), lg))
    out.extend(_chapter_title_block(
        MPL.hidden_title(lg),
        MPL.hidden_subtitle(lg),
    ))
    if hidden_truth:
        ht = hidden_truth.strip()
        mk = _premium_prose_markup(ht) or _safe(ht)
        out.append(_premium_body_table(mk, ht, s))
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
            f"{_safe(MPL.hidden_promise_label(lg))}</b></font>  "
            f"<font color='{promise_color}'><b>{_safe(promise)}</b></font>"
            f"<font color='{_hex(TEXT_MID)}'>{_safe(MPL.hidden_promise_tail(lg, p1_name, p2_name))}</font>",
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
    appends a few quiet realism lines before the page break, so the
    deepest insight in the report sits next to the KP promise reading."""
    lg = str(s.get("_lang") or "en")
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, MPL.hidden_eyebrow(lg), lg))
    out.extend(_chapter_title_block(
        MPL.hidden_title(lg),
        MPL.hidden_subtitle(lg),
    ))
    if hidden_truth:
        ht = hidden_truth.strip()
        mk = _premium_prose_markup(ht) or _safe(ht)
        out.append(_premium_body_table(mk, ht, s))
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
            f"{_safe(MPL.hidden_promise_label(lg))}</b></font>  "
            f"<font color='{promise_color}'><b>{_safe(promise)}</b></font>"
            f"<font color='{_hex(TEXT_MID)}'>{_safe(MPL.hidden_promise_tail(lg, p1_name, p2_name))}</font>",
            ParagraphStyle("hid_promise2", fontName=hp_reg, fontSize=10.5,
                           leading=15, spaceAfter=10),
        ))
    if sig:
        out.append(_grounding_card(s, sig))
    out.append(Spacer(1, 12))
    inv = _derive_invisible_patterns(payload, lg)
    if inv:
        # Keep the realism lines, but render as continuous prose (no boxed callout).
        fname = (s.get("body_latin").fontName if "body_latin" in s
                 else (s.get("body").fontName if "body" in s else "Helvetica"))
        for ln in inv:
            out.append(Paragraph(
                f"<font color='{_hex(BRAND_GOLD)}'>•</font>  {_safe(ln)}",
                ParagraphStyle(
                    "inv_plain",
                    fontName=fname,
                    fontSize=10.5,
                    leading=15,
                    textColor=TEXT_MID,
                    leftIndent=10,
                    spaceBefore=6,
                ),
            ))
    out.append(PageBreak())
    return out


def _derive_invisible_patterns(payload: dict, lang: str = "en") -> list[str]:
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
        out.append(MPL.invpat_bh_weak_maitri_strong(lang))
    # Yoni mismatch + Gana strong → emotional sync, physical timing differs
    if yn is not None and gn is not None and yn < 0.5 and gn >= 0.6:
        out.append(MPL.invpat_yoni_gana(lang))
    # Nadi 0 + everything else generally fine → invisible health-energy
    # friction. Architect-flagged: original rule fired on any nadi=0,
    # over-asserting on broadly weak charts. Now requires the average of
    # the other resolved koot ratios ≥ 0.5 so this only triggers when
    # nadi is the OUTLIER, not just one of many weak signals.
    other_ratios = [r for r in (bh, mt, yn, gn) if r is not None]
    other_avg = (sum(other_ratios) / len(other_ratios)) if other_ratios else 0.0
    if na is not None and na <= 0.0 and other_avg >= 0.5:
        out.append(MPL.invpat_nadi_outlier(lang))
    # Manglik asymmetry — one carries it, the other doesn't
    p1m = bool((payload.get("p1") or {}).get("manglik"))
    p2m = bool((payload.get("p2") or {}).get("manglik"))
    if p1m ^ p2m:
        out.append(MPL.invpat_manglik_asym(lang))
    if not out:
        out.append(MPL.invpat_default(lang))
    return out[:3]


def _derive_attraction_line(payload: dict, lang: str = "en") -> str:
    """Why this bond formed — from the strongest koot scores."""
    koots = payload.get("koots") or []
    strong = sorted(
        [k for k in koots if k.get("max", 0) > 0],
        key=lambda k: (k.get("score", 0) / max(k.get("max", 1), 1)),
        reverse=True,
    )[:2]
    if not strong:
        if MPL.pdf_ui_hn(lang):
            return MPL.attraction_derived_body_hn([])
        return (
            "This bond forms in the small recognitions first — who fills "
            "water bottles before bed, who notices the other's quiet day — "
            "before any score explains why that matters."
        )
    if MPL.pdf_ui_hn(lang):
        canons = [c for c in (_canon_koot_key(k) for k in strong) if c]
        return MPL.attraction_derived_body_hn(canons)
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
        return (
            "This bond forms in the small recognitions first — who fills "
            "water bottles before bed, who notices the other's quiet day — "
            "before any score explains why that matters."
        )
    if len(lines) >= 2:
        body = f"{lines[0]} from one chart, and {lines[1]} from the other"
    else:
        body = lines[0]
    return (
        f"This bond forms because both kundlis hand each other something "
        f"the other half-remembers from home — {body}. Pull here is less "
        f"'chemistry headline', more repeated ease in the same small rooms."
    )


def _derive_core_challenge_line(payload: dict, lang: str = "en") -> str:
    """The ONE thing that could quietly damage this marriage —
    derived from the weakest koot in the report."""
    koots = payload.get("koots") or []
    weak = sorted(
        [k for k in koots if k.get("max", 0) > 0],
        key=lambda k: (k.get("score", 0) / max(k.get("max", 1), 1)),
    )
    if not weak:
        if MPL.pdf_ui_hn(lang):
            return MPL.core_challenge_fallback_kitchen_hn()
        return (
            "The single biggest risk here is the same unnamed ledger most "
            "kitchens run — who noticed the bill, who carried the apology "
            "last time — until one week both are tired on the same Tuesday."
        )
    k = weak[0]
    canon = _canon_koot_key(k) or ""
    if MPL.pdf_ui_hn(lang):
        return MPL.core_challenge_line_hn(canon if canon else None)
    base_map = {
        "bhakoot": (
            "a slow, almost invisible drift in life-directions",
            "Same calendar year, two different five-year pictures — the gap "
            "shows up first in small money moves, not in dramatic fights.",
        ),
        "nadi": (
            "a hidden energetic friction that often surfaces as health or fatigue",
            "Both tired the same Tuesday, both irritable the same week — "
            "mirrored fatigue reads like attitude until you see the pattern.",
        ),
        "gana": (
            "a mismatch in inner nature — one playful, one serious",
            "One wants noise after work, the other wants a cave — the living "
            "room volume becomes the argument while the real ask stays unnamed.",
        ),
        "yoni": (
            "mismatched physical or emotional rhythms",
            "Touch and irritation spike together — one reads it as rejection, "
            "the other as 'I am just slow today' — same bed, two clocks.",
        ),
        "graha": (
            "natural temperament clashes during stress",
            "Under load, one goes sharp, one goes flat — the fight looks "
            "about the topic but tracks who got sleep.",
        ),
        "vashya": (
            "an imbalance in who pulls and who follows",
            "Micro-decisions pile up on one side while the other drifts late — "
            "resentment sits in the schedule, not in speeches.",
        ),
        "tara": (
            "mistimed moments — wrong words at vulnerable times",
            "Right sentence, wrong hour — the hurt lands as 'you never get me' "
            "even when the intent was soft.",
        ),
        "varna": (
            "a subtle ego friction where one feels less respected",
            "Family-table moments show it first — who gets introduced, who "
            "gets interrupted — before the living room ever argues.",
        ),
    }
    label, advice = base_map.get(canon, (
        "a recurring subtle pattern this report has flagged",
        "It shows up in repetition before it shows up in volume — same "
        "shape, new topic.",
    ))
    return (f"The single thing most likely to quietly damage this marriage "
            f"is {label}. {advice}")


def _pro_attraction_and_challenge_page(s: dict, num: int,
                                        payload: dict) -> list[Any]:
    """One dense page carrying two psychologically-charged truths
    users remember most (rendered as flowing prose, not labeled report sections)."""
    lg = str(s.get("_lang") or "en")
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, MPL.attraction_eyebrow(lg), lg))
    out.extend(_chapter_title_block(
        MPL.attraction_title(lg),
        MPL.attraction_subtitle(lg),
    ))
    out.append(Spacer(1, 6))

    # Latin-only deterministic content — must use body_latin so non-Latin
    # lang reports (bn/ta/te/etc) don't drop glyphs.
    fname = (s.get("body_latin").fontName if "body_latin" in s
             else (s.get("body").fontName if "body" in s else "Helvetica"))
    attraction = _derive_attraction_line(payload, lg)
    challenge = _derive_core_challenge_line(payload, lg)
    # Render as continuous prose (no labeled subsections / quote cards).
    out.append(Paragraph(
        _safe(attraction),
        ParagraphStyle("at_flow1", fontName=fname, fontSize=10.5,
                       leading=15.5, textColor=TEXT_MID,
                       spaceBefore=6, spaceAfter=10),
    ))
    out.append(Paragraph(
        _safe(challenge),
        ParagraphStyle("at_flow2", fontName=fname, fontSize=10.5,
                       leading=15.5, textColor=TEXT_MID,
                       spaceBefore=0, spaceAfter=10),
    ))
    out.append(Spacer(1, 14))
    out.append(_grounding_card(s, MPL.attraction_ground_card(lg)))
    out.append(PageBreak())
    return out


def _pro_chapter_body_markup(ch: dict) -> str:
    """Premium chapter body: one `full_read` block (legacy 3-field merge if absent)."""
    raw = (ch.get("full_read") or "").strip()
    if not raw:
        parts = [
            (ch.get("kya_dikh") or "").strip(),
            (ch.get("kya_matlab") or "").strip(),
            (ch.get("kya_dhyan") or "").strip(),
        ]
        raw = "<br/><br/>".join(_safe(p) for p in parts if p)
    else:
        raw = _premium_prose_markup(raw)
    return raw if raw else _safe("—")


def _pro_chapter_snippet_for_note(grounding: str, limit: int = 200) -> str:
    g = (grounding or "").strip()
    if len(g) <= limit:
        return g
    cut = g[:limit].rsplit(" ", 1)[0].strip()
    return cut + "…"


def _grounding_head_tail_cards(grounding: str) -> tuple[str | None, str]:
    """Split grounding into a short chart-facing head (top strip) + remainder (bottom card).

    When the read is short, returns (None, full) so only one bottom card renders.
    """
    g = (grounding or "").strip()
    if not g:
        return None, ""
    if len(g) <= 160:
        return None, g
    head = ""
    for sep in (". ", "। "):
        idx = g.find(sep)
        if 25 <= idx <= 240:
            head = g[: idx + len(sep)].strip()
            break
    if not head:
        head = _pro_chapter_snippet_for_note(g, 210)
    tail = g[len(head) :].strip()
    if len(tail) < 55:
        return None, g
    return head, tail


def _pro_chapter_pages(
    s: dict,
    num_a: int,
    num_b: int,
    eyebrow: str,
    title: str,
    subtitle: str,
    ch: dict,
) -> list[Any]:
    """Premium chapter: grounding cards + one long-form narrative block (``chapter_body`` / ``full_read``)."""
    lg = str(s.get("_lang") or "en")
    out: list[Any] = []
    score = ch.get("score_0_10")
    _ = num_b

    fname = s["body"].fontName if "body" in s else "Helvetica"
    grounding = _latinize_pdf_plain((ch.get("grounding") or "").strip(), lg)
    g_head, g_rest = _grounding_head_tail_cards(grounding)

    out.append(_chapter_eyebrow(num_a, eyebrow, lg))
    out.extend(_chapter_title_block(title, subtitle, s))

    if score is not None:
        try:
            sv = float(score)
            out.append(
                Paragraph(
                    f"<font color='{_hex(TEXT_SOFT)}'><i>{sv:.1f} / 10</i></font>",
                    ParagraphStyle(
                        "pro_chapter_score_line",
                        fontName=fname,
                        fontSize=9,
                        leading=12,
                        textColor=TEXT_SOFT,
                        spaceAfter=10,
                    ),
                )
            )
        except Exception:
            pass

    if g_head:
        out.append(_chart_note_card(s, g_head))
        out.append(Spacer(1, 7))
        out.append(_subsection_soft_rule())
        out.append(Spacer(1, 4))

    primary = _latinize_pdf_plain(_premium_chapter_primary_narrative(ch).strip(), lg)
    prose, buls = _prose_and_bullet_lines(primary)
    combined_plain = prose.strip() if prose.strip() else primary
    if not combined_plain.strip():
        combined_plain = " "
    parts = _split_premium_plain_paragraphs(combined_plain)
    # Pro PDF: one chapter ≈ one A4 page — when the model returns a short read,
    # re-chunk into more stacked paragraphs + roomier body styles so the page
    # fills vertically without inventing prose.
    target_full_page_chars = 2700
    min_paras_for_fill = 5
    need_page_fill = (
        len(combined_plain) < target_full_page_chars
        or len(parts) < min_paras_for_fill
    )
    if not g_head:
        out.append(Spacer(1, 2))
    if need_page_fill:
        segments = _premium_chapter_dense_segments(combined_plain)
        if len(segments) >= 2:
            mid = max(1, len(segments) // 2)
            a = "\n\n".join(segments[:mid])
            b = "\n\n".join(segments[mid:])
            out.append(_premium_body_multi_paragraph_table(s, a, relax=True))
            out.append(Spacer(1, 11))
            out.append(_subsection_soft_rule())
            out.append(Spacer(1, 6))
            out.append(_premium_body_multi_paragraph_table(s, b, relax=True))
        else:
            out.append(_premium_body_multi_paragraph_table(s, combined_plain, relax=True))
        if len(combined_plain) < 1400:
            out.append(Spacer(1, 12))
    else:
        layout_boost = len(combined_plain) < 1900 or len(parts) < 4
        if layout_boost and len(parts) >= 4:
            mid = max(2, len(parts) // 2)
            a = "\n\n".join(parts[:mid])
            b = "\n\n".join(parts[mid:])
            out.append(_premium_body_multi_paragraph_table(s, a, relax=False))
            out.append(Spacer(1, 10))
            out.append(_subsection_soft_rule())
            out.append(Spacer(1, 5))
            out.append(_premium_body_multi_paragraph_table(s, b, relax=False))
        else:
            out.append(_premium_body_multi_paragraph_table(s, combined_plain, relax=False))
        if layout_boost and len(parts) < 4:
            out.append(Spacer(1, 10))
    if len(buls) >= 2:
        bt = _bullet_cluster_table(s, "\n".join(buls))
        if bt is not None:
            out.append(Spacer(1, 6))
            out.append(bt)

    if g_rest:
        bottom_title = (
            MPL.grounding_obs_title(lg) if g_head else MPL.grounding_why_title(lg)
        )
        out.append(Spacer(1, 10))
        out.append(
            _grounding_card(
                s,
                g_rest,
                title=bottom_title,
                compact=bool(g_head),
                max_body_chars=480 if g_head else None,
            )
        )
    out.append(PageBreak())
    return out


def _pro_practical_page(s: dict, num: int, paragraphs: list[str]) -> list[Any]:
    """P20 — Practical Married Life (three premium ``practical`` blocks; ``\\n\\n`` inside each)."""
    lg = str(s.get("_lang") or "en")
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, MPL.practical_eyebrow(lg), lg))
    out.extend(_chapter_title_block(
        MPL.practical_title(lg),
        MPL.practical_subtitle(lg),
    ))
    blocks = [str(p).strip() for p in (paragraphs or []) if str(p).strip()][:3]
    if not blocks:
        blocks = [MPL.practical_empty_block(lg)]
    for bi, block in enumerate(blocks):
        out.append(_premium_body_multi_paragraph_table(s, block, relax=False))
        out.append(Spacer(1, 8))
        bt = _bullet_cluster_table(s, block)
        if bt is not None:
            out.append(Spacer(1, 4))
            out.append(bt)
        if bi < len(blocks) - 1:
            out.append(Spacer(1, 8))
            out.append(_subsection_soft_rule())
            out.append(Spacer(1, 5))
    out.append(PageBreak())
    return out


def _pro_koot_decoded_page(s: dict, num: int, koots: list[dict]) -> list[Any]:
    """P21 — Compatibility Numbers Decoded: every koot in plain language."""
    lg = str(s.get("_lang") or "en")
    st_map = MPL._KOOT_STRENGTH_HN if MPL.pdf_ui_hn(lg) else _KOOT_STRENGTH_LANG
    dmg_map = MPL._KOOT_DAMAGE_HN if MPL.pdf_ui_hn(lg) else _KOOT_DAMAGE_LANG
    fb_st = MPL.koot_meaning_fallback_strength(lg)
    fb_mid = MPL.koot_meaning_fallback_mid(lg)
    fb_wk = MPL.koot_meaning_fallback_weak(lg)
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, MPL.koot_decoded_eyebrow(lg), lg))
    out.extend(_chapter_title_block(
        MPL.koot_decoded_title(lg),
        MPL.koot_decoded_subtitle(lg),
    ))
    rows = [[
        MPL.koot_table_header_koot(lg),
        MPL.koot_table_header_score(lg),
        MPL.koot_table_header_meaning(lg),
    ]]
    for k in (koots or []):
        canon = _canon_koot_key(k)
        try:
            sc = int(k.get("score") or 0); mx = int(k.get("max") or 0)
        except Exception:
            sc, mx = 0, 0
        # Ratio drives strength vs damage language.
        ratio = (sc / mx) if mx else 0.0
        if ratio >= 0.6:
            meaning = st_map.get(canon, fb_st)
        elif ratio > 0:
            meaning = dmg_map.get(canon, fb_mid)
        else:
            meaning = dmg_map.get(canon, fb_wk)
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


_PLANET_AFFECTION = {
    "mars":    "seedha, protective intensity — pyaar action ke through aata hai",
    "venus":   "narm, sundar warmth — halki choo, chhote pyaare gestures",
    "jupiter": "udaar, bada-dil care — guidance aur saath dene wala pyaar",
    "mercury": "khilandda, witty andaz — words aur jokes hi love-language hain",
    "saturn":  "shaant bharosa-driven pyaar — quietly reliable, dikhawa nahi",
    "sun":     "wafadar, garv-bhara pyaar — sabke saamne visible aur unwavering",
    "moon":    "emotional, palan-poshne wala pyaar — mood mirror, deep sunna",
    "rahu":    "alag-thalag, magnetic intensity — rules todne wali warmth",
    "ketu":    "dhyaan-dhara, almost spiritual saath — chup-chap saath nibhaana",
}

_PLANET_MARRIAGE_MEANING = {
    "mars":    "ek aisi partnership jiske liye lade jaane ka jazba ho — shared mission, shared zameen",
    "venus":   "ek private sanctuary — sundar, comfortable, emotional refinement wala",
    "jupiter": "ek dharmic raasta — shaadi growth aur meaning ka vaahan",
    "mercury": "ek lambi, kabhi khatam na hone wali baatcheet do samajhdaar logon ki",
    "saturn":  "ek lambi-chodi imaarat banane jaisi cheez — patience, duty, dheere bharosa",
    "sun":     "ek identity-anchor — visible commitment jo dono ki pehchaan banti hai",
    "moon":    "ek emotional ghar — safety aur palan-poshan sabse upar",
    "rahu":    "ek transform karne wala bandhan — shaadi naye self ka dwaar",
    "ketu":    "ek halki attachment — saath rehna par pakad nahi, saans lene ki jagah",
}


def _planet_key(name: str | None) -> str:
    return (name or "").strip().lower()


# ── Phase 2.5.11.24-soul-v6 + North-Indian diamond: D1 + D9 chart visualization ─
# True North Indian geometry: canvas-drawn diamond with twelve quadrilateral
# house cells on the ring between outer and inner diamonds (not a 4×4 grid).
# House numbers follow the classical fixed order CCW from top-left (12…11);
# signs rotate from ``ascendant``. ``planets`` = list of {name, sign} dicts.
_SIGN_ORDER = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
               "Libra", "Scorpio", "Sagittarius", "Capricorn",
               "Aquarius", "Pisces"]
_SIGN_INDEX = {s: i for i, s in enumerate(_SIGN_ORDER)}
_SIGN_ABBR = {"Aries": "Ar", "Taurus": "Ta", "Gemini": "Ge",
              "Cancer": "Ca", "Leo": "Le", "Virgo": "Vi", "Libra": "Li",
              "Scorpio": "Sc", "Sagittarius": "Sg", "Capricorn": "Cp",
              "Aquarius": "Aq", "Pisces": "Pi"}
_PLANET_ABBR = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma",
                "Mercury": "Me", "Jupiter": "Ju", "Venus": "Ve",
                "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"}
# Classical North Indian fixed-house topology on the outer diamond:
# L→T→R: 12,1,2,3 · T→R already second segment — use L→T (12,1), T→Rt (2,3);
# Rt→B: 4,5 · B→L: 6,7,8,9 · L→B: 11,10.
_NI_INK = colors.HexColor("#0f172a")
_NI_LINE = colors.HexColor("#334155")
_NI_PAPER = colors.HexColor("#fffdf7")
_NI_LAGNA_STROKE = colors.HexColor("#9a3412")


def _ni_split_polyline(
    vertices: list[tuple[float, float]],
    n_seg: int,
) -> list[tuple[float, float]]:
    """``n_seg`` equal-length segments along open ``vertices`` → ``n_seg+1`` points."""
    if n_seg < 1:
        return [vertices[0], vertices[-1]]
    segs: list[tuple[tuple[float, float], tuple[float, float], float]] = []
    tot = 0.0
    for i in range(len(vertices) - 1):
        a, b = vertices[i], vertices[i + 1]
        le = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append((a, b, le))
        tot += le
    if tot <= 1e-12:
        return [vertices[0]] * (n_seg + 1)
    out: list[tuple[float, float]] = []
    for k in range(n_seg + 1):
        dist = tot * (k / n_seg)
        acc = 0.0
        for a, b, le in segs:
            if acc + le >= dist - 1e-9:
                t = (dist - acc) / le if le > 1e-12 else 0.0
                out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
                break
            acc += le
        else:
            out.append(vertices[-1])
    return out


def _ni_classic_house_quads(
    cx: float,
    cy: float,
    R: float,
    k_inner: float,
) -> list[tuple[int, tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]]]:
    """Twelve bhāvas as quads between outer diamond and inner diamond (northern chart)."""
    L = (cx - R, cy)
    T = (cx, cy + R)
    Rt = (cx + R, cy)
    B = (cx, cy - R)
    ir = R * k_inner
    Li, Ti, Rti, Bi = (cx - ir, cy), (cx, cy + ir), (cx + ir, cy), (cx, cy - ir)
    quads: list[tuple[int, tuple, tuple, tuple, tuple]] = []
    wing_spec: list[
        tuple[list[tuple[float, float]], list[tuple[float, float]], int, tuple[int, ...]]
    ] = [
        ([L, T], [Li, Ti], 2, (12, 1)),
        ([T, Rt], [Ti, Rti], 2, (2, 3)),
        ([Rt, B], [Rti, Bi], 2, (4, 5)),
        ([B, L], [Bi, Li], 4, (6, 7, 8, 9)),
        ([L, B], [Li, Bi], 2, (11, 10)),
    ]
    for och, ich, n, houses in wing_spec:
        o_pts = _ni_split_polyline(och, n)
        i_pts = _ni_split_polyline(ich, n)
        for j in range(n):
            h = houses[j]
            quads.append((h, o_pts[j], o_pts[j + 1], i_pts[j + 1], i_pts[j]))
    return quads

class NorthIndianDiamondChartFlowable(Flowable):
    """Classical North Indian diamond (D-1): twelve bhāvas, inner madhya for chart name."""

    def __init__(
        self,
        planets: list,
        asc_sign: str | None,
        label: str,
        sub_label: str,
        width_mm: float = 88.0,
    ) -> None:
        Flowable.__init__(self)
        self._planets = planets or []
        self._asc_sign = asc_sign
        self._label = (label or "").strip()
        self._sub_label = (sub_label or "").strip()
        self._side = float(width_mm) * mm

    def wrap(self, availWidth, availHeight):
        return self._side, self._side

    def draw(self) -> None:
        canv = self.canv
        w = h = self._side
        cx, cy = w * 0.5, h * 0.5

        asc_norm = (self._asc_sign or "").strip().title()
        asc_idx = _SIGN_INDEX.get(asc_norm)
        by_sign: dict[str, list[str]] = {}
        for p in self._planets:
            if not isinstance(p, dict):
                continue
            sign = (p.get("sign") or "").strip().title()
            name = (p.get("name") or "").strip().title()
            ab = _PLANET_ABBR.get(name)
            if sign and ab:
                by_sign.setdefault(sign, []).append(ab)

        margin = min(w, h) * 0.018
        R = (min(w, h) * 0.5 - margin) * 0.985
        k_inner = 0.385
        k_lab = 0.235

        L = (cx - R, cy)
        T = (cx, cy + R)
        Rt = (cx + R, cy)
        B = (cx, cy - R)

        ir = R * k_inner
        Li, Ti, Rti, Bi = (cx - ir, cy), (cx, cy + ir), (cx + ir, cy), (cx, cy - ir)
        lr = R * k_lab
        Ll, Tl, Rtl, Bl = (cx - lr, cy), (cx, cy + lr), (cx + lr, cy), (cx, cy - lr)

        house_polys = _ni_classic_house_quads(cx, cy, R, k_inner)

        path_bg = canv.beginPath()
        path_bg.moveTo(T[0], T[1])
        path_bg.lineTo(Rt[0], Rt[1])
        path_bg.lineTo(B[0], B[1])
        path_bg.lineTo(L[0], L[1])
        path_bg.close()
        canv.setFillColor(_NI_PAPER)
        canv.drawPath(path_bg, stroke=0, fill=1)

        for house_num, o0, o1, i1, i0 in house_polys:
            hp = canv.beginPath()
            hp.moveTo(o0[0], o0[1])
            hp.lineTo(o1[0], o1[1])
            hp.lineTo(i1[0], i1[1])
            hp.lineTo(i0[0], i0[1])
            hp.close()
            canv.setFillColor(colors.white)
            canv.drawPath(hp, stroke=0, fill=1)
            canv.setStrokeColor(_NI_LINE)
            canv.setLineWidth(0.32)
            canv.drawPath(hp, stroke=1, fill=0)

        path_lab = canv.beginPath()
        path_lab.moveTo(Tl[0], Tl[1])
        path_lab.lineTo(Rtl[0], Rtl[1])
        path_lab.lineTo(Bl[0], Bl[1])
        path_lab.lineTo(Ll[0], Ll[1])
        path_lab.close()
        canv.setFillColor(colors.white)
        canv.drawPath(path_lab, stroke=0, fill=1)
        canv.setStrokeColor(_NI_LINE)
        canv.setLineWidth(0.28)
        canv.drawPath(path_lab, stroke=1, fill=0)

        for house_num, o0, o1, i1, i0 in house_polys:
            if house_num != 1:
                continue
            hp1 = canv.beginPath()
            hp1.moveTo(o0[0], o0[1])
            hp1.lineTo(o1[0], o1[1])
            hp1.lineTo(i1[0], i1[1])
            hp1.lineTo(i0[0], i0[1])
            hp1.close()
            canv.setStrokeColor(_NI_LAGNA_STROKE)
            canv.setLineWidth(1.0)
            canv.drawPath(hp1, stroke=1, fill=0)
            break

        path_out = canv.beginPath()
        path_out.moveTo(T[0], T[1])
        path_out.lineTo(Rt[0], Rt[1])
        path_out.lineTo(B[0], B[1])
        path_out.lineTo(L[0], L[1])
        path_out.close()
        canv.setStrokeColor(_NI_INK)
        canv.setLineWidth(1.02)
        canv.drawPath(path_out, stroke=1, fill=0)

        for house_num, o0, o1, i1, i0 in house_polys:
            tcx = (o0[0] + o1[0]) * 0.5
            tcy = (o0[1] + o1[1]) * 0.5
            icx = (i0[0] + i1[0]) * 0.5
            icy = (i0[1] + i1[1]) * 0.5
            tx, ty = (tcx + icx) * 0.5, (tcy + icy) * 0.5

            sign_name = ""
            if asc_idx is not None:
                sign_name = _SIGN_ORDER[(asc_idx + house_num - 1) % 12]
            sab = _SIGN_ABBR.get(sign_name, "")
            planets_in = " ".join(by_sign.get(sign_name, []))
            lag_txt = " · Lg" if house_num == 1 else ""

            canv.setFont("Helvetica-Bold", 6.5)
            canv.setFillColor(_NI_LINE)
            canv.drawCentredString(tx, ty + 5.2, f"{house_num} {sab}{lag_txt}")

            if planets_in:
                words = planets_in.split()
                canv.setFillColor(_NI_INK)
                if len(words) <= 4:
                    canv.setFont("Helvetica-Bold", 7.15)
                    canv.drawCentredString(tx, ty - 2.2, " ".join(words))
                else:
                    canv.setFont("Helvetica-Bold", 6.25)
                    canv.drawCentredString(tx, ty - 0.8, " ".join(words[:4]))
                    canv.drawCentredString(tx, ty - 6.8, " ".join(words[4:8]))

        canv.setFillColor(_NI_INK)
        canv.setFont("Helvetica-Bold", 8.4)
        canv.drawCentredString(cx, cy + 3.8, self._label.upper())
        canv.setFont("Helvetica", 6.35)
        canv.setFillColor(_NI_LINE)
        canv.drawCentredString(cx, cy - 5.2, self._sub_label)


def _north_indian_diamond_chart(
    planets: list,
    asc_sign: str | None,
    label: str,
    sub_label: str,
    width_mm: float = 88.0,
) -> NorthIndianDiamondChartFlowable:
    """Return a canvas-drawn North Indian diamond chart (not a grid Table)."""
    return NorthIndianDiamondChartFlowable(
        planets, asc_sign, label, sub_label, width_mm,
    )


def _pro_d1_d9_chart_page(s: dict, num: int, k1: dict | None,
                           k2: dict | None) -> list[Any]:
    """Phase 2.5.11.24-soul-v6: visual D1 (Rasi) + D9 (Navamsa) chart
    page for both partners. Side-by-side **North Indian diamond** (fixed
    houses, signs from lagna). Defensive against missing kundli data —
    page renders with empty grids if so, never crashes."""
    lg = str(s.get("_lang") or "en")
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, MPL.charts_eyebrow(lg), lg))
    out.extend(_chapter_title_block(
        MPL.charts_title(lg),
        MPL.charts_subtitle(lg),
        s,
    ))
    for who, kundli in ((MPL.partner_default(lg, 1), k1), (MPL.partner_default(lg, 2), k2)):
        if not isinstance(kundli, dict):
            kundli = {}
        name = (kundli.get("name") or who).strip()
        d1_planets = kundli.get("planets") or []
        d1_asc = kundli.get("ascendant")
        d9 = (kundli.get("divisionalCharts") or {}).get("D9") or {}
        d9_planets = d9.get("planets") if isinstance(d9, dict) else []
        d9_asc = (d9.get("ascendant") if isinstance(d9, dict)
                  else None) or d1_asc
        out.append(Paragraph(
            f"<font color='{_hex(_NI_INK)}'><b>"
            f"{_safe(name.upper())}</b></font>",
            ParagraphStyle("dchart_name", fontName="Helvetica-Bold",
                            fontSize=10.5, leading=14,
                            spaceBefore=6, spaceAfter=3),
        ))
        d1 = _north_indian_diamond_chart(d1_planets, d1_asc, "Rāśi",
                                         "D1", width_mm=88)
        d9c = _north_indian_diamond_chart(d9_planets, d9_asc, "Navāmśa",
                                          "D9", width_mm=88)
        side = Table([[d1, d9c]], colWidths=[91 * mm, 91 * mm])
        side.setStyle(TableStyle([
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        out.append(side)
        out.append(Spacer(1, 3))
    out.append(Spacer(1, 4))
    out.append(Paragraph(
        f"<font color='{_hex(_NI_LINE)}' size='8'>"
        f"{MPL.charts_legend_note(lg)}</font>",
        ParagraphStyle("dchart_legend", fontName="Helvetica",
                        fontSize=8, leading=11, textColor=_NI_LINE,
                        spaceBefore=2),
    ))
    out.append(PageBreak())
    return out


# ── Phase 2.5.11.24-soul-v6: weak-koot practical action strip ─────────
_KOOT_ACTION_LINE = {
    "bhakoot":      "Saal me ek baar — ek shaant evening — agle 5 "
                     "saal ke 3 specific goals saath baith ke likho. "
                     "Yahi single conversation Bhakoot ka asli tod hai.",
    "nadi":         "Subah ke shuru rituals (chai, naashta, walk) "
                     "aaj se planned-together rakho. Yahi physical "
                     "ritual care Nadi ki kami ko balance karta hai.",
    "gana":         "Ek doosre ke mood-shifts ko convert karne ki "
                     "bajaye 'translate' karna seekho — har person ka "
                     "rhythm alag hai, kisi ek ko galat mat samjho.",
    "graha_maitri": "Kisi bhi disagreement me pehle 5 minute sirf "
                     "'main samjha/samjhi' bolo — solution dene se "
                     "pehle. Mental friendship yahin se banti hai.",
    "yoni":         "Pressure-free physical closeness rakho weekly — "
                     "sex ya intimacy expectation ke bina simple touch "
                     "(haath pakadna, gale lagna). Yoni mismatch isi "
                     "tarah balance hota hai.",
    "tara":         "Chhote 'kaisa lag raha hai aaj?' check-ins har "
                     "2-3 din me — ek doosre ka emotional weather "
                     "track karte raho. Tara wellness se bhi kaam "
                     "karta hai.",
    "vashya":       "Decision-making me dono ka equal voice rakho — "
                     "'main bolun aur tu sun le' dynamic se bachna. "
                     "Vashya weak ho to dominance se crack aati hai.",
    "varna":        "Mahine me ek baar koi spiritual ya philosophical "
                     "baat — book, podcast, satsang share karo. Inner "
                     "alignment yahin se banta hai.",
}


def _blueprint_depth_blocks(s: dict, d9: dict | None,
                            p1n: str, p2n: str) -> list[Any]:
    """Phase 2.5.11.24-fix10 — 4 deterministic depth blocks added to the
    Marriage Blueprint page so it grows from 1 page to ~2 pages of real
    D1/D9 translation (addresses the "blueprint is gold, make it longer"
    critique). All blocks are derived from `payload["d9_marriage"]`
    signals (lagna lord, sync.lagna_lord_relation, sync.seven_lord_relation,
    marriage_maturity_0_10) — NEVER quote raw chart vocab. Always emits
    flowables (uses safe defaults when d9 is missing) so tests can lock
    the contract."""
    out: list[Any] = []
    d9 = d9 if isinstance(d9, dict) else {}
    lg = str(s.get("_lang") or "en")
    # Architect-flagged fix10 hardening: nested p1/p2/sync may arrive as
    # lists / strings / None from a malformed payload — type-check each
    # before .get() to keep the renderer crash-free.
    raw_p1, raw_p2, raw_sync = d9.get("p1"), d9.get("p2"), d9.get("sync")
    p1d = raw_p1 if isinstance(raw_p1, dict) else {}
    p2d = raw_p2 if isinstance(raw_p2, dict) else {}
    sync = raw_sync if isinstance(raw_sync, dict) else {}

    # Lagna lord drives AFFECTION STYLE; 7th lord drives MARRIAGE MEANING.
    # Architect-flagged fix10 correctness: previous version used lagna lord
    # for both — now correctly reads `d9_7h_lord` for the 7th-lord block.
    p1_lord = _planet_key(p1d.get("d9_lagna_lord")) or "jupiter"
    p2_lord = _planet_key(p2d.get("d9_lagna_lord")) or "venus"
    p1_7l = _planet_key(p1d.get("d9_7h_lord")) or p1_lord
    p2_7l = _planet_key(p2d.get("d9_7h_lord")) or p2_lord
    # Relation strings: normalize + accept engine-native variants
    # (`friendly`/`hostile` etc) the d9_marriage compute path emits.
    rel_lagna = (str(sync.get("lagna_lord_relation") or "neutral")
                 .strip().lower())
    try:
        m1 = float(p1d.get("marriage_maturity_0_10") or 5.0)
        m2 = float(p2d.get("marriage_maturity_0_10") or 5.0)
    except Exception:
        m1, m2 = 5.0, 5.0
    avg_m = (m1 + m2) / 2.0

    # Latin-only deterministic prose AND headings → body_latin /
    # Helvetica-Bold so non-Latin langs render every label and body line.
    # Architect-flagged: the depth-block heading was previously bound to
    # s["h1"].fontName (script font); now Helvetica-Bold across the board.
    fname = (s.get("body_latin").fontName if "body_latin" in s
             else (s.get("body").fontName if "body" in s else "Helvetica"))
    body_st = ParagraphStyle("bp_dep_body", fontName=fname, fontSize=10.5,
                             leading=15, textColor=TEXT_DARK)
    # Keep the depth content but avoid subsection UI (no divider / eyebrow / mini-headings).

    # 1) What marriage actually means (7th-lord translated — fix10 corrected).
    # Phase soul-v5: rewritten in astrologer-notes voice — first-person
    # observation, lived-practice framing, slightly hesitant. The reader
    # should feel a human astrologer is talking, not an AI summarising.
    p1_mean = _PLANET_MARRIAGE_MEANING.get(p1_7l, _PLANET_MARRIAGE_MEANING["jupiter"])
    p2_mean = _PLANET_MARRIAGE_MEANING.get(p2_7l, _PLANET_MARRIAGE_MEANING["venus"])
    out.append(Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>"
        f"{_safe(MPL.bp_heading_marriage_meaning(lg, str(p1n), str(p2n)))}"
        f"</b></font><br/>"
        f"Jab main yeh dono kundli saath rakhke padhta hoon, mujhe ek "
        f"baat sabse pehle dikhti hai — <b>{_safe(p1n)}</b> ke liye "
        f"shaadi andar se {p1_mean} hai. Aur <b>{_safe(p2n)}</b> ke "
        f"liye yeh {p2_mean} hai. Dono samajh sahi hain. Maine aksar "
        f"dekha hai — actual friction (aur actual magic) inhi do "
        f"definitions ke beech ki chhoti, rozmarra ki jagah me rehti "
        f"hai, jahan dono perfectly overlap nahi karte.",
        body_st))

    # 2) Affection style (lagna-lord translated).
    p1_aff = _PLANET_AFFECTION.get(p1_lord, _PLANET_AFFECTION["jupiter"])
    p2_aff = _PLANET_AFFECTION.get(p2_lord, _PLANET_AFFECTION["venus"])
    if p1_lord == p2_lord:
        aff_line = (
            f"Yeh interesting hai — tum dono pyaar lagbhag ek hi shape "
            f"me dete ho: {p1_aff}. Meri practice me aise jode aksar "
            f"chup-chap ek doosre ko deeply samajh lete hain — par "
            f"khatra yeh hai ki yeh exchange nahi, echo ban jaata hai. "
            f"Kabhi-kabhi koi alag flavour bhi chahiye hota hai."
        )
    else:
        # Phase soul-v6: dropped the `dikhata/dikhati` slash hack — gender-
        # neutral phrasing reads cleaner and credibly human.
        aff_line = (
            f"<b>{_safe(p1n)}</b> ka pyaar aata hai {p1_aff} ke roop "
            f"me. <b>{_safe(p2n)}</b> ka tareeka thoda alag hai — "
            f"{p2_aff}. Aise charts me main hamesha yeh kehta hoon: "
            f"koi zyada pyaar nahi karta, sirf dono ki emotional "
            f"language alag hai. Shuru ke kayi jhagde meri experience "
            f"me sirf translation ki gaadbad hote hain, feeling ki "
            f"kami nahi."
        )
    out.append(Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(MPL.bp_heading_affection(lg))}</b></font><br/>"
        f"{aff_line}",
        body_st,
    ))

    # 3) Conflict instinct (sync.lagna_lord_relation translated).
    # Architect-flagged: must accept engine-native variants — d9_marriage
    # emits `friendly`/`hostile` not just `friend`/`enemy`.
    if rel_lagna in ("friend", "friendly", "great_friend", "mutual_friend",
                     "mutual", "best_friend"):
        conf_line = (
            "Jab jhagda hota hai, tum dono ki natural aadat hoti hai "
            "repair within 24-48 hours — yeh maine kafi clearly dekha "
            "is jodi me. Soft ho jaane ki willingness andar baithi hai. "
            "Ek hi cheez ka dhyan rakhna: isse for-granted mat lena, "
            "warna asli baat unfinished reh jaayegi."
        )
    elif rel_lagna in ("enemy", "hostile", "great_enemy", "mutual_enemy",
                       "worst_enemy", "bitter_enemy"):
        conf_line = (
            "Yeh thoda honestly bolna padega — jab fight shuru hoti "
            "hai, tum dono ki instinct hai apne-apne emotional kamre "
            "me chale jaane ki, aur wait karne ki ki doosra pehle aaye. "
            "Main isko 'cold war' pattern bolta hoon. Aise charts "
            "kayi dekhe hain — yahi ek aadat hai jo is shaadi ko "
            "consciously todni padegi."
        )
    elif rel_lagna in ("own", "swakshetra", "self"):
        conf_line = (
            "Tum dono apni-apni zameen pe khade hoke ladte ho — clear, "
            "principled, position chhodne wale nahi. Mujhe yeh "
            "respect-able lagta hai par yeh bhi kehna padega: aise "
            "jodon ke jhagde loud nahi hote, slow hote hain. Asli kaam "
            "argument jeetna nahi — beech me milna hai, jo mushkil hai."
        )
    else:
        conf_line = (
            "Conflict yahan loud nahi hota — sideways move karta hai. "
            "Chhote-chhote silent withdrawals, badi screaming nahi. "
            "Risk yahi hai ki unsaid hurt chup-chap jamta jaata hai. "
            "Achchi baat — koi bhi shabdon se aasani se chot nahi "
            "pahuncha sakta. Yeh kam log realize karte hain."
        )
    out.append(Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(MPL.bp_heading_conflict(lg))}</b></font><br/>"
        f"{conf_line}",
        body_st,
    ))

    # 4) Daily emotional habit (avg maturity translated).
    if avg_m >= 7.0:
        day_line = (
            "Aam dinon me yeh shaadi calibrated lagti hai — maine kayi "
            "aise jodon me yeh notice kiya hai. Subah ki chai, raat ka "
            "silence, weekend ke errands — chhote rituals chup-chap "
            "wo heavy-lifting karte hain jiska credit aksar grand "
            "gestures le jaate hain. Believe me, yeh chhoti baat lagti "
            "hai par nahi hai."
        )
    elif avg_m >= 4.0:
        day_line = (
            "Most days me ek tum me se emotional thermostat banega/"
            "banegi, doosra/doosri catch up karega/karegi — aur yeh "
            "role har few weeks me chup-chap switch hoga. Maturity "
            "yahan yeh hai ki switch ko notice karo, score mat karo. "
            "Mostly aise jodon me yahi pattern dikhta hai mujhe."
        )
    else:
        day_line = (
            "Honestly bol raha hoon — kayi din tum dono parallel "
            "orbits me chaloge: ek hi kamre me, alag-alag andar ke "
            "duniya me. Yeh coldness nahi hai, yeh chart conscious, "
            "named effort maang raha hai line ko warm rakhne ke liye. "
            "Aam taur pe yeh awareness se hi shuru hota hai."
        )
    out.append(Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(MPL.bp_heading_daily_rhythm(lg))}</b></font><br/>"
        f"{day_line}",
        body_st,
    ))

    return out


def _pro_marriage_blueprint_page(s: dict, num: int,
                                  blueprint: dict,
                                  p1_name: str, p2_name: str,
                                  d9_marriage: dict | None = None) -> list[Any]:
    """P22 — Marriage Blueprint (Phase 2.5.11.23-soul-v3).

    Six prose blocks describing each partner's INNATE marriage nature,
    the interaction dynamic, what each needs from the other, and the
    one takeaway. Backend-source: D9 lagna lord + Venus/Jupiter dignity
    + marriage_maturity. NEVER quotes raw chart vocab — pure relational
    character language.
    """
    lg = str(s.get("_lang") or "en")
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, MPL.blueprint_eyebrow(lg), lg))
    out.extend(_chapter_title_block(
        MPL.blueprint_title(lg),
        MPL.blueprint_subtitle(lg),
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
        mk = _premium_prose_markup(body) or _safe(body.strip())
        out.append(_premium_body_table(mk, body, s))
        out.append(Spacer(1, 8))

    _block(MPL.blueprint_block_p1_nature(lg, p1_name),
           blueprint.get("p1_marriage_nature", ""))
    _block(MPL.blueprint_block_p2_nature(lg, p2_name),
           blueprint.get("p2_marriage_nature", ""))
    _block(MPL.blueprint_block_interaction(lg),
           blueprint.get("interaction_dynamic", ""))
    _block(MPL.blueprint_block_p1_needs(lg, p1_name, p2_name),
           blueprint.get("what_p1_needs_from_p2", ""))
    _block(MPL.blueprint_block_p2_needs(lg, p1_name, p2_name),
           blueprint.get("what_p2_needs_from_p1", ""))

    # Phase 2.5.11.24-fix10 — 4 deterministic depth blocks (D1+D9
    # translation: 7th-lord meaning, affection style, conflict instinct,
    # daily emotional rhythm). Spills the blueprint to ~2 pages so this
    # gold section finally reads as deep as the user wanted.
    out.extend(_blueprint_depth_blocks(s, d9_marriage, p1_name, p2_name))

    takeaway = (blueprint.get("blueprint_takeaway") or "").strip()
    if takeaway:
        out.append(Spacer(1, 6))
        out.append(_grounding_card(s, takeaway))
    out.append(PageBreak())
    return out


def _pro_final_verdict_page(s: dict, num: int, verdict: str,
                            total: float, mx: int,
                            p1_name: str = "Partner 1",
                            p2_name: str = "Partner 2") -> list[Any]:
    """Final Verdict: closing prose in a single continuous flow."""
    lg = str(s.get("_lang") or "en")
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, MPL.verdict_eyebrow(lg), lg))
    out.extend(_chapter_title_block(
        MPL.verdict_title(lg),
        MPL.verdict_subtitle(lg, total, mx),
    ))
    txt = (verdict or "").strip() or MPL.verdict_body_default(lg)
    mk = _premium_prose_markup(txt) or _safe(txt)
    out.append(_premium_body_table(mk, txt, s))
    out.append(Spacer(1, 14))

    # Phase 2.5.11.24-fix9 — ONE memorable closing truth line by score
    # band. The single sentence users will remember + screenshot. The
    # whole report leads here.
    try:
        ratio = float(total) / float(mx) if mx else 0.0
    except Exception:
        ratio = 0.0
    # Phase 2.5.11.24-fix10 — closers: observational, slightly uncomfortable,
    # astrologer-not-coach. English fragments stay Latin-readable for mixed fonts.
    if ratio >= 0.78:
        closer = MPL.verdict_closer_high(lg)
    elif ratio >= 0.40:
        closer = MPL.verdict_closer_mid(lg)
    else:
        closer = MPL.verdict_closer_low(lg)
    # Latin-only — body_latin so closer stays readable in bn/ta/te/etc.
    fname = (s.get("body_latin").fontName if "body_latin" in s
             else (s.get("body").fontName if "body" in s else "Helvetica"))
    out.append(Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b><i>{_safe(closer)}</i></b></font>",
        ParagraphStyle(
            "verdict_closer_plain",
            fontName=fname,
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            leftIndent=10,
            rightIndent=10,
            spaceBefore=10,
            spaceAfter=12,
        ),
    ))

    out.append(_grounding_card(s, MPL.verdict_grounding(lg)))
    out.append(PageBreak())
    return out


def _pro_closing_page(s: dict) -> list[Any]:
    """P24 — Closing + branding (NEVER mention AI/LLM)."""
    lg = str(s.get("_lang") or "en")
    out: list[Any] = []
    out.append(Spacer(1, 50 * mm))
    out.append(Paragraph(
        f"<font color='{_hex(BRAND_PURPLE)}'><b>{_safe(MPL.closing_thanks(lg))}</b></font>",
        ParagraphStyle("close_h", fontName="Helvetica-Bold", fontSize=26,
                       leading=32, alignment=TA_CENTER, spaceAfter=10),
    ))
    out.append(Paragraph(
        f"<font color='#475569'>{_safe(MPL.closing_body(lg))}</font>",
        ParagraphStyle("close_b", fontName="Helvetica", fontSize=11,
                       leading=17, alignment=TA_CENTER, spaceAfter=24),
    ))
    out.append(Spacer(1, 30 * mm))
    out.append(Paragraph(
        f"<font color='{_hex(TEXT_SOFT)}'>{_safe(MPL.closing_footer(lg))}</font>",
        ParagraphStyle("close_meta", fontName="Helvetica", fontSize=8,
                       leading=11, alignment=TA_CENTER),
    ))
    return out


def _mpl_score_breakdown_page(
    s: dict, num: int, payload: dict, total: int, mx: int, lang: str,
) -> list[Any]:
    ledger = payload.get("ashtakoot_ledger") or []
    lg = str(s.get("_lang") or "en")
    H_REG = (s.get("body").fontName if s and "body" in s else "Helvetica")
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "SCORE", lg))
    out.extend(_chapter_title_block(MPL.score_breakdown_title(lg), MPL.score_breakdown_subtitle(lg), s))
    if not ledger:
        out.append(
            _premium_body_multi_paragraph_table(
                s, MPL.score_ledger_fallback(lg, total, mx), relax=True,
            )
        )
    else:
        rows: list[list[Any]] = []
        for row in ledger:
            if not isinstance(row, dict):
                continue
            label = _safe(str(row.get("label") or ""))
            delta = row.get("delta")
            note = _safe(str(row.get("note") or ""))
            delta_txt = ""
            if row.get("base") is not None:
                delta_txt = str(int(row["base"]))
            elif delta is not None:
                try:
                    d = float(delta)
                    delta_txt = f"+{int(d)}" if d > 0 else str(int(d))
                except (TypeError, ValueError):
                    delta_txt = str(delta)
            rows.append([
                Paragraph(
                    f"<b>{label}</b><br/><font color='{_hex(TEXT_SOFT)}' size=9>{note}</font>",
                    ParagraphStyle("mpl_sl", fontName=H_REG, fontSize=10, leading=13, textColor=TEXT_DARK),
                ),
                Paragraph(
                    f"<b>{delta_txt}</b>" if delta_txt else "—",
                    ParagraphStyle(
                        "mpl_sd", fontName="Helvetica-Bold", fontSize=11,
                        alignment=TA_CENTER, textColor=BRAND_PURPLE,
                    ),
                ),
            ])
        tbl = Table(rows, colWidths=[145 * mm, 35 * mm])
        tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -2), 0.25, TEXT_SOFT),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        out.append(tbl)
        out.append(Spacer(1, 10))
        out.append(
            Paragraph(
                f"<b>Total: {total} / {mx}</b>",
                ParagraphStyle(
                    "mpl_fin", fontName="Helvetica-Bold", fontSize=14,
                    textColor=BRAND_PURPLE, spaceBefore=6,
                ),
            )
        )
    out.append(PageBreak())
    return out


def _mpl_chart_snapshot_page(s: dict, num: int, payload: dict, lang: str) -> list[Any]:
    snap = payload.get("chart_snapshot") or {}
    lines = snap.get("lines") or []
    body = "\n".join(str(ln) for ln in lines if ln)
    lg = str(s.get("_lang") or "en")
    if not body.strip():
        body = MPL.chart_snapshot_fallback(lg)
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "CHART", lg))
    out.extend(_chapter_title_block(MPL.chart_snapshot_title(lg), MPL.chart_snapshot_subtitle(lg), s))
    out.append(_premium_body_multi_paragraph_table(s, body, relax=True))
    bridge = (payload.get("narrative_bridge") or "").strip()
    if bridge:
        out.append(Spacer(1, 8))
        out.append(_grounding_card(s, _latinize_pdf_plain(bridge, lg), title=MPL.timing_note_title(lg)))
    out.append(PageBreak())
    return out


def _mpl_method_note_page(s: dict, num: int, lang: str) -> list[Any]:
    lg = str(s.get("_lang") or "en")
    out: list[Any] = []
    out.append(_chapter_eyebrow(num, "NOTE", lg))
    out.extend(_chapter_title_block(MPL.method_note_title(lg), "", s))
    out.append(_premium_body_multi_paragraph_table(s, MPL.method_note_body(lg), relax=True))
    out.append(PageBreak())
    return out


def render_milan_pro_pdf(payload: dict, lang: str = "en") -> bytes:
    """Phase 2.5.11.24-fix9 — Pro renderer (depth + hierarchy, ≈21-28pp).

    Page count scales with content density:
    - Synthetic / short fixture: exactly **21** pages (locked by tests).
    - Live LLM-polished content: ~24-26 pages because dense ``full_read``
      chapter bodies naturally spill 7 chapter pages onto a second page.
      That spillover is content-driven, never boilerplate — every overflow
      page carries real reading.

    Renders the "Premium Relationship Truth" report using the
    `payload["pro_premium"]` block produced by `polish_premium_chapters`.
    Always emits the full Pro structure even when the premium block is missing or
    partial — falls back to engine-derived content per page. (Standalone D1/D9 chart
    page removed — see story assembly below.)

    Premium chapter pages use **p64 layered layout**: named subsection headings,
    multi-paragraph body tables (no single mega-cell), soft dividers, optional
    bullet clusters, compact **Chart insight →** strip plus **Observational notes →**
    / **Why we say this →** grounding cards (split when grounding is long).
    Legacy ``full_read`` uses the same multi-paragraph + rhythm rules.
    Timing context is included as continuous prose on Final Verdict.
    """
    lang = _normalize_milan_pdf_lang(lang)
    _ensure_native_pdf_fonts_registered(lang)
    _log_pdf_font_lane(lang)
    payload = payload or {}
    if not payload.get("chart_snapshot"):
        payload = enrich_milan_bundle_for_pdf(payload, lang=lang)
    p1   = payload.get("p1") or {}
    p2   = payload.get("p2") or {}
    total = int(payload.get("total") or 0)
    mx    = int(payload.get("max") or 36)
    grade = payload.get("grade") or {}
    koots = payload.get("koots") or []
    pro   = payload.get("pro_premium") or {}
    chapters_in = pro.get("chapters") or []
    meta = pro.get("_meta") or {}

    if (os.environ.get("COMPAT_PREMIUM_TRACE") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        _mpl = (
            "[prem_trace] render_milan_pro_pdf "
            f"lang={lang!r} pro_meta_model={meta.get('model')!r} "
            f"pro_meta_version={meta.get('version')!r} "
            f"chapter_rows={len(chapters_in)}"
        )
        print(_mpl, flush=True)
        try:
            _mtp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_prem_trace_last_run.txt")
            with open(_mtp, "a", encoding="utf-8") as _mf:
                _mf.write(_mpl + "\n")
        except Exception:
            pass

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
    story.extend(_cover_page(
        s, p1, p2, total, mx, grade, snapshot, manglik, lang, koots,
    ))
    # P2 — Snapshot card (reuses existing 12-page helper, num=2)
    story.extend(_snapshot_page(
        s, 2, snapshot, koots, manglik, total, mx, payload=payload,
    ))
    page_num = 3
    story.extend(_mpl_score_breakdown_page(s, page_num, payload, total, mx, lang))
    page_num += 1
    story.extend(_mpl_chart_snapshot_page(s, page_num, payload, lang))
    page_num += 1
    # Hidden Truth + Quiet Patterns (D1/D9 chart page removed per product request).
    story.extend(_pro_hidden_truth_page_with_patterns(
        s, page_num, pro.get("hidden_truth") or "",
        meta,
        p1.get("name") or MPL.partner_default(lang, 1),
        p2.get("name") or MPL.partner_default(lang, 2),
        payload,
    ))
    page_num += 1
    # Seven premium chapter pages (title chrome + merged observation prose).
    _placeholder_blob = MPL.pro_placeholder_chapter_blob(lang)
    _chapter_ph = MPL.pro_chapter_placeholder(lang)
    engine_ground = payload.get("chapter_groundings") or {}
    pro_rows = MPL.pro_chapter_rows(lang)
    for i, (key, eyebrow, title, subtitle) in enumerate(pro_rows, start=1):
        ch = dict(by_key.get(key) or by_key.get(f"ch{i}") or {})
        if not ch.get(CHAPTER_BODY_KEY) and not ch.get("full_read"):
            ph = _placeholder_blob if i in (4, 7) else _chapter_ph
            if i in (4, 7):
                ph = _chart_bridge_with_remedy_tail(ph)
            ch = {
                "score_0_10": None,
                CHAPTER_BODY_KEY: ph,
                "full_read": ph,
                "grounding": MPL.pro_placeholder_grounding_bridge(lang),
            }
        if not str(ch.get("grounding") or "").strip():
            eg = engine_ground.get(key)
            if eg:
                ch["grounding"] = _latinize_pdf_plain(eg, lang)
        story.extend(_pro_chapter_pages(
            s, page_num, page_num, eyebrow, title, subtitle, ch,
        ))
        page_num += 1

    # P11 — What Makes This Bond Special (premium engine `special`)
    special = [b for b in (pro.get("special") or []) if b][:3]
    if not special:
        special = _derive_special_bullets(payload)[:3]
    story.extend(_premium_consultation_blocks_page(
        s, page_num, MPL.special_eyebrow(lang),
        MPL.special_title(lang),
        MPL.special_subtitle(lang),
        special,
    ))
    # P19 — What Can Quietly Damage
    damage = [b for b in (pro.get("damage") or []) if b]
    if not damage:
        damage = _derive_damage_bullets(payload)
    if not damage:
        damage = [MPL.damage_engine_fallback_bullet(lang)]
    page_num += 1
    story.extend(_premium_consultation_blocks_page(
        s, page_num, MPL.damage_eyebrow(lang),
        MPL.damage_title(lang),
        MPL.damage_subtitle(lang),
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
    # Marriage Blueprint (Phase soul-v3 + fix10 D1/D9 depth blocks).
    story.extend(_pro_marriage_blueprint_page(
        s, page_num, pro.get("marriage_blueprint") or {},
        p1.get("name") or MPL.partner_default(lang, 1),
        p2.get("name") or MPL.partner_default(lang, 2),
        d9_marriage=payload.get("d9_marriage") or {},
    ))
    page_num += 1
    # Phase 2.5.11.24-fix9 — Attraction + Core Challenge dedicated page.
    # The two psychologically-charged sections users remember most:
    # Two high-signal truths (from strongest vs weakest koots) sit right before
    # Final Verdict so the closing arc is: blueprint → why/risk → verdict.
    story.extend(_pro_attraction_and_challenge_page(s, page_num, payload))
    page_num += 1
    # Final Verdict (Phase 2.5.11.24-fix8: Timing Sync prose merged here —
    # standalone Timing Sync page was pure boilerplate with zero engine
    # signal, dropped per critique on visual density. Final Verdict page
    # now carries the timing-context paragraph as a closing block.)
    verdict = _latinize_pdf_plain((pro.get("verdict") or "").strip(), lang)
    if not verdict.strip():
        verdict = _latinize_pdf_plain((payload.get("narrative_bridge") or "").strip(), lang)
    story.extend(_pro_final_verdict_page(
        s, page_num, verdict, total, mx,
        p1_name=p1.get("name") or MPL.partner_default(lang, 1),
        p2_name=p2.get("name") or MPL.partner_default(lang, 2),
    ))
    page_num += 1
    story.extend(_mpl_method_note_page(s, page_num, lang))
    story.extend(_pro_closing_page(s))

    doc.milan_pdf_lang = lang
    doc.milan_pdf_footer_pro = True

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

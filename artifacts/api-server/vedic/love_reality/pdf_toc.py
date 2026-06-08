"""Love Reality Pro — table of contents (first PDF page)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle

from milan_pdf import BRAND_GOLD, BRAND_PURPLE, TEXT_DARK, TEXT_MID, TEXT_SOFT, _font_pair, _gold_rule, _hex, _safe
from vedic.compat.milan_pdf_locale import pdf_ui_hn


def _toc_entries(lang: str, *, legacy_page1: bool = False) -> list[dict[str, Any]]:
    hn = pdf_ui_hn(lang)
    if legacy_page1:
        sec1 = {
            "title": "Cosmic Alignment Scorecard" if not hn else "Cosmic Alignment Scorecard",
            "items": (
                ["Love score / 100", "Summary index", "All engine scores table"]
                if not hn
                else ["Love score / 100", "Summary index", "Saare engine scores"]
            ),
        }
    else:
        sec1 = {
            "title": (
                "Executive Summary & Cosmic Alignment"
                if not hn
                else "Executive Summary & Cosmic Alignment"
            ),
            "items": (
                [
                    "Relationship Summary & Cosmic Score",
                    "Core Metrics — Love, Breakup, Loyalty, Reunion",
                    "Relationship Insights",
                    "Strengths & Challenges in this Connection",
                ]
                if not hn
                else [
                    "Relationship Summary & Cosmic Score",
                    "Core Metrics — Love, Breakup, Loyalty, Reunion",
                    "Relationship Insights",
                    "Strengths & Challenges",
                ]
            ),
        }
        sec2 = {
            "title": "Final Cosmic Verdict & Recommendations" if not hn else "Final Verdict & Recommendations",
            "items": (
                ["Full cosmic verdict (3+ paragraphs, human advisory voice)", "Planetary remedies + human action plan (2 prose blocks)"]
                if not hn
                else ["Cosmic verdict (3+ paragraphs)", "Upay + action plan (2 prose blocks)"]
            ),
        }

    rest_en = [
        ("Deep Connection Analysis", ["Emotional · Communication · Trust · Long-term"]),
        ("Destiny Partner Blueprint (You)", ["7th house · Upapada · ideal partner signature"]),
        ("Partner Blueprint vs Reality", ["Chart ideal vs actual partner nature"]),
        ("The 5 Love Dimensions Deep-Dive", ["Emotional · Attraction · Communication · Karmic · Stability"]),
        ("Moon Synastry & Emotional Rhythm", ["Moon signs · emotional pacing · 6-8 check"]),
        ("The Core Root Cause", ["What silently strains the bond"]),
        ("Loyalty, Trust & Psychological Traits", ["Commitment under pressure"]),
        ("Red Flags Matrix", ["Chart-derived warning signals"]),
        ("The Harmony Formula", ["Behavioral shifts · elemental balance"]),
        ("Vimshottari Dasha Synchronization", ["Parallel dasha cycles for both"]),
        ("The 1–3 Year Chronological Roadmap", ["3 · 12 · 36 month trend arc"]),
        ("Planetary Counter Measures (Upay)", ["Remedies for afflicted planets"]),
        ("Relationship Checklist", ["Human action plan"]),
        ("Closing Guidance & Disclaimer", ["Next steps · guardrails"]),
    ]
    rest_hn = [
        ("Deep Connection Analysis", ["Emotional · Communication · Trust · Long-term"]),
        ("Destiny Partner Blueprint (You)", ["7th house · Upapada · ideal signature"]),
        ("Partner Blueprint vs Reality", ["Ideal vs actual partner"]),
        ("The 5 Love Dimensions Deep-Dive", ["5 love dimensions matrix"]),
        ("Moon Synastry & Emotional Rhythm", ["Moon · emotional pacing"]),
        ("The Core Root Cause", ["Bond ko silently kya strain karta hai"]),
        ("Loyalty, Trust & Psychological Traits", ["Pressure mein commitment"]),
        ("Red Flags Matrix", ["Warning signals"]),
        ("The Harmony Formula", ["Behavioral shifts"]),
        ("Vimshottari Dasha Synchronization", ["Dono partners ke dasha"]),
        ("The 1–3 Year Chronological Roadmap", ["3 · 12 · 36 month trends"]),
        ("Planetary Counter Measures (Upay)", ["Remedies"]),
        ("Relationship Checklist", ["Action plan"]),
        ("Closing Guidance & Disclaimer", ["Closing · disclaimer"]),
    ]
    rest = rest_hn if hn else rest_en
    out: list[dict[str, Any]] = [sec1]
    if not legacy_page1:
        out.append(sec2)
    for title, items in rest:
        out.append({"title": title, "items": items})
    return out


def render_love_reality_toc_flowables(
    p1: dict[str, Any],
    p2: dict[str, Any],
    *,
    report_id: str = "",
    lang: str = "en",
    legacy_page1: bool = False,
) -> list[Any]:
    """First PDF page — serial list of everything in this report."""
    H_REG, H_BOLD = _font_pair(lang)
    hn = pdf_ui_hn(lang)
    content_w = 180 * mm
    out: list[Any] = []

    out.append(Spacer(1, 2 * mm))
    out.append(
        Paragraph(
            f"<font color='{_hex(BRAND_GOLD)}'><b>✦ COSMIC LENS PREMIUM</b></font>",
            ParagraphStyle("toc_br", fontName=H_BOLD, fontSize=10, leading=13, alignment=TA_CENTER),
        )
    )
    out.append(
        Paragraph(
            "<b>Love Reality Pro</b>",
            ParagraphStyle("toc_t", fontName=H_BOLD, fontSize=16, leading=20, alignment=TA_CENTER, textColor=BRAND_PURPLE),
        )
    )
    out.append(
        Paragraph(
            f"<b>{_safe(p1.get('name'))}</b> &amp; <b>{_safe(p2.get('name'))}</b>",
            ParagraphStyle("toc_nm", fontName=H_BOLD, fontSize=12, leading=15, alignment=TA_CENTER, spaceAfter=2),
        )
    )
    rid = (report_id or "—").strip()
    out.append(
        Paragraph(
            f"<font color='{_hex(TEXT_SOFT)}'>ID {_safe(rid)} · "
            f"{datetime.utcnow().strftime('%d %B %Y')}</font>",
            ParagraphStyle("toc_id", fontName=H_REG, fontSize=8.5, leading=11, alignment=TA_CENTER, spaceAfter=4),
        )
    )
    out.append(_gold_rule(48))
    out.append(Spacer(1, 3 * mm))

    toc_title = "Is Report Mein Kya Milega" if hn else "Report Contents"
    toc_sub = (
        "Neeche serial order mein — poori PDF mein yeh sections aayenge"
        if hn
        else "Everything in this PDF — in reading order"
    )
    out.append(
        Paragraph(
            f"<font color='{_hex(BRAND_PURPLE)}'><b>{toc_title.upper()}</b></font>",
            ParagraphStyle("toc_h", fontName=H_BOLD, fontSize=13, leading=16, alignment=TA_CENTER, spaceAfter=2),
        )
    )
    out.append(
        Paragraph(
            f"<font color='{_hex(TEXT_MID)}'>{toc_sub}</font>",
            ParagraphStyle("toc_sub", fontName=H_REG, fontSize=9, leading=12, alignment=TA_CENTER, spaceAfter=6),
        )
    )

    entries = _toc_entries(lang, legacy_page1=legacy_page1)
    rows: list[list[Any]] = []
    num_style = ParagraphStyle("toc_n", fontName=H_BOLD, fontSize=9.5, leading=12, textColor=BRAND_PURPLE)
    title_style = ParagraphStyle("toc_row_t", fontName=H_BOLD, fontSize=9.5, leading=12, textColor=TEXT_DARK)
    item_style = ParagraphStyle("toc_item", fontName=H_REG, fontSize=8, leading=10.5, textColor=TEXT_MID, leftIndent=10)

    for i, entry in enumerate(entries, start=1):
        title = str(entry.get("title") or "")
        rows.append([
            Paragraph(f"{i:02d}", num_style),
            Paragraph(f"<b>{_safe(title)}</b>", title_style),
        ])
        for sub in entry.get("items") or []:
            rows.append([
                Paragraph("", item_style),
                Paragraph(f"• {_safe(str(sub))}", item_style),
            ])

    tbl = Table(rows, colWidths=[10 * mm, content_w - 10 * mm])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    out.append(tbl)
    out.append(Spacer(1, 4 * mm))
    out.append(
        Paragraph(
            f"<font color='{_hex(TEXT_SOFT)}'>"
            f"{'Agla page se report shuru — scroll karte jao' if hn else 'Report begins on the next page — scroll to read'}"
            f"</font>",
            ParagraphStyle("toc_ft", fontName=H_REG, fontSize=8, leading=10, alignment=TA_CENTER),
        )
    )
    out.append(PageBreak())
    return out

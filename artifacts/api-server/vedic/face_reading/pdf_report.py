"""
PDF Report Renderer — ₹1499 Premium Face Intelligence Report

Renders the assembled report (from narrator.assemble_report) to a polished
multi-page PDF using ReportLab. Features:
  • Tinted cover page with gold accents
  • Table of Contents
  • Per-section: numbered banner, narrative prose intro, structured fields,
    callout boxes for key insights, mini score bars for numeric metrics
  • Premium typography (Hinglish-tuned, justified body, generous leading)
  • Per-page header bar + footer with page numbers
"""
from __future__ import annotations
from io import BytesIO
from typing import Dict, List, Any, Optional
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, HRFlowable, Flowable,
)


# ── Color palette (premium maroon + gold + cream) ─────────────────────────
C_PRIMARY     = HexColor("#7B1F1F")    # deep maroon
C_PRIMARY_DK  = HexColor("#5A1414")    # darker maroon
C_ACCENT      = HexColor("#C2A878")    # warm gold
C_ACCENT_DK   = HexColor("#9C8254")    # dark gold
C_INK         = HexColor("#2A2418")    # dark warm brown
C_MUTED       = HexColor("#7A7164")    # muted brown
C_BG_TINT     = HexColor("#FAF6EC")    # cream background
C_CALLOUT_BG  = HexColor("#FFF4DC")    # warm cream for callouts
C_RULE        = HexColor("#D9CFB7")    # rule line
C_BAR_TRACK   = HexColor("#EDE3CA")    # bar background
C_BAR_FILL    = HexColor("#7B1F1F")    # bar foreground


# ── Emoji stripper (ReportLab core fonts can't render emoji) ──────────────
_EMOJI_RE = re.compile(
    "[" "\U0001F300-\U0001FAFF" "\U00002600-\U000027BF" "\U0001F000-\U0001F2FF" "]+",
    flags=re.UNICODE,
)


def _safe(text: Any) -> str:
    if text is None: return ""
    s = str(text)
    s = _EMOJI_RE.sub("", s).strip()
    s = s.replace("&", "&amp;")
    # Allow our injected <b>...</b> tags but escape stray angle brackets
    # by temporarily protecting <b>/</b> tags
    s = s.replace("<b>", "\x00B\x00").replace("</b>", "\x00b\x00")
    s = s.replace("<", "&lt;").replace(">", "&gt;")
    s = s.replace("\x00B\x00", "<b>").replace("\x00b\x00", "</b>")
    return s


# ── Styles ────────────────────────────────────────────────────────────────
def _styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_kicker": ParagraphStyle(
            "cover_kicker", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=11, textColor=C_ACCENT_DK, alignment=TA_CENTER, leading=14,
            spaceAfter=14,
        ),
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=38, textColor=C_PRIMARY, alignment=TA_CENTER, leading=44,
            spaceAfter=8,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle", parent=base["Normal"], fontName="Helvetica-Oblique",
            fontSize=14, textColor=C_MUTED, alignment=TA_CENTER, leading=20,
            spaceAfter=18,
        ),
        "cover_name": ParagraphStyle(
            "cover_name", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=24, textColor=C_INK, alignment=TA_CENTER, leading=28,
            spaceBefore=20, spaceAfter=4,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", parent=base["Normal"], fontName="Helvetica",
            fontSize=11, textColor=C_MUTED, alignment=TA_CENTER, leading=16,
        ),
        "cover_archetype": ParagraphStyle(
            "cover_arche", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=20, textColor=C_PRIMARY, alignment=TA_CENTER, leading=24,
            spaceBefore=24,
        ),
        "toc_header": ParagraphStyle(
            "toc_header", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=24, textColor=C_PRIMARY, alignment=TA_LEFT, leading=28,
            spaceAfter=18,
        ),
        "toc_row": ParagraphStyle(
            "toc_row", parent=base["Normal"], fontName="Helvetica",
            fontSize=11.5, textColor=C_INK, alignment=TA_LEFT, leading=20,
        ),
        "section_no": ParagraphStyle(
            "section_no", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=10, textColor=white, alignment=TA_LEFT, leading=14,
        ),
        "section_title_hi": ParagraphStyle(
            "section_title_hi", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=20, textColor=C_PRIMARY, alignment=TA_LEFT, leading=24,
            spaceAfter=2,
        ),
        "section_title_en": ParagraphStyle(
            "section_title_en", parent=base["Normal"], fontName="Helvetica-Oblique",
            fontSize=10.5, textColor=C_MUTED, alignment=TA_LEFT, leading=14,
            spaceAfter=10,
        ),
        "narrative": ParagraphStyle(
            "narrative", parent=base["Normal"], fontName="Helvetica",
            fontSize=11, textColor=C_INK, alignment=TA_JUSTIFY, leading=17,
            spaceBefore=4, spaceAfter=10,
            firstLineIndent=10,
        ),
        "field_label": ParagraphStyle(
            "field_label", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=10.5, textColor=C_PRIMARY, alignment=TA_LEFT, leading=14,
            spaceBefore=8, spaceAfter=2,
        ),
        "field_value": ParagraphStyle(
            "field_value", parent=base["Normal"], fontName="Helvetica",
            fontSize=10.5, textColor=C_INK, alignment=TA_JUSTIFY, leading=15,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["Normal"], fontName="Helvetica",
            fontSize=10.5, textColor=C_INK, alignment=TA_LEFT, leading=15,
            leftIndent=14, bulletIndent=4, spaceAfter=4,
        ),
        "callout_label": ParagraphStyle(
            "callout_label", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=9.5, textColor=C_ACCENT_DK, alignment=TA_LEFT, leading=12,
            spaceAfter=2,
        ),
        "callout_text": ParagraphStyle(
            "callout_text", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=12, textColor=C_PRIMARY_DK, alignment=TA_LEFT, leading=16,
        ),
        "score_label": ParagraphStyle(
            "score_label", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=10, textColor=C_INK, alignment=TA_LEFT, leading=12,
        ),
        "score_value": ParagraphStyle(
            "score_value", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=10, textColor=C_PRIMARY, alignment=TA_LEFT, leading=12,
        ),
        "footer": ParagraphStyle(
            "footer", parent=base["Normal"], fontName="Helvetica-Oblique",
            fontSize=8, textColor=C_MUTED, alignment=TA_CENTER, leading=11,
        ),
    }


# ── Custom flowables ──────────────────────────────────────────────────────
class ScoreBar(Flowable):
    """A horizontal score bar: label on left, percentage fill, value on right."""
    def __init__(self, label: str, value: float, max_value: float = 100,
                 width: float = 165*mm, height: float = 7*mm):
        super().__init__()
        self.label = label
        self.value = max(0.0, min(float(max_value), float(value)))
        self.max_value = float(max_value)
        self.width = width
        self.height = height

    def wrap(self, *_):
        return self.width, self.height + 4*mm

    def draw(self):
        c = self.canv
        # Label
        c.setFont("Helvetica-Bold", 9.5)
        c.setFillColor(C_INK)
        c.drawString(0, self.height + 1.5*mm, self.label)
        # Value text on right
        suffix = f"{self.value:.1f}/{int(self.max_value)}" if self.max_value <= 10 else f"{self.value:.0f}/{int(self.max_value)}"
        c.setFillColor(C_PRIMARY)
        c.drawRightString(self.width, self.height + 1.5*mm, suffix)
        # Track
        c.setFillColor(C_BAR_TRACK)
        c.roundRect(0, 0, self.width, self.height, 2, fill=1, stroke=0)
        # Fill
        ratio = self.value / self.max_value if self.max_value else 0
        fill_w = max(2, self.width * ratio)
        c.setFillColor(C_BAR_FILL)
        c.roundRect(0, 0, fill_w, self.height, 2, fill=1, stroke=0)


class SectionBanner(Flowable):
    """A section number chip + maroon underline bar."""
    def __init__(self, section_no: str, width: float = 174*mm):
        super().__init__()
        self.section_no = section_no
        self.width = width
        self.height = 10*mm

    def wrap(self, *_):
        return self.width, self.height + 2*mm

    def draw(self):
        c = self.canv
        # Maroon chip
        chip_w = 22*mm
        c.setFillColor(C_PRIMARY)
        c.roundRect(0, 0, chip_w, self.height, 2, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawCentredString(chip_w/2, self.height/2 - 3, f"SECTION {self.section_no}")
        # Gold underline running across
        c.setFillColor(C_ACCENT)
        c.rect(chip_w + 4*mm, self.height/2 - 0.6, self.width - chip_w - 4*mm, 1.2, fill=1, stroke=0)


def _callout(label: str, text: str, styles) -> Flowable:
    """A highlighted callout box for important insights."""
    cell = [
        [Paragraph(_safe(label).upper(), styles["callout_label"])],
        [Paragraph(_safe(text), styles["callout_text"])],
    ]
    t = Table(cell, colWidths=[174*mm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_CALLOUT_BG),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 9),
        ("LINEBEFORE", (0,0), (0,-1), 3, C_ACCENT),
    ]))
    return t


# ── Page decoration ────────────────────────────────────────────────────────
def _on_page(canvas, doc):
    canvas.saveState()
    page_w, page_h = A4
    # Top thin gold bar
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, page_h - 6, page_w, 6, fill=1, stroke=0)
    # Bottom rule + page number + brand
    canvas.setStrokeColor(C_RULE)
    canvas.setLineWidth(0.4)
    canvas.line(15 * mm, 16 * mm, page_w - 15 * mm, 16 * mm)
    canvas.setFont("Helvetica-Oblique", 8)
    canvas.setFillColor(C_MUTED)
    canvas.drawString(15 * mm, 10 * mm, "Cosmic Lens · Face Intelligence Report")
    canvas.drawRightString(page_w - 15 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _on_cover_page(canvas, doc):
    canvas.saveState()
    page_w, page_h = A4
    # Full background tint
    canvas.setFillColor(C_BG_TINT)
    canvas.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    # Top gold bar (thicker on cover)
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, page_h - 22, page_w, 22, fill=1, stroke=0)
    # Decorative thin maroon line just below gold
    canvas.setFillColor(C_PRIMARY)
    canvas.rect(0, page_h - 26, page_w, 2, fill=1, stroke=0)
    # Bottom maroon strip
    canvas.setFillColor(C_PRIMARY)
    canvas.rect(0, 0, page_w, 32, fill=1, stroke=0)
    # Cover footer text
    canvas.setFont("Helvetica-Bold", 10.5)
    canvas.setFillColor(white)
    canvas.drawCentredString(page_w / 2, 12, "Cosmic Lens · Vedic Face Intelligence")
    canvas.restoreState()


# ── Section content rendering ─────────────────────────────────────────────
# Per-section "callout" mappings: which content keys deserve highlighted boxes
SECTION_CALLOUTS = {
    "section_1_power_summary": [
        ("biggest_strength", "BIGGEST STRENGTH"),
        ("biggest_weakness", "BIGGEST WEAKNESS"),
        ("one_line_truth", "ONE-LINE TRUTH"),
    ],
    "section_2_psychological_type": [],
    "section_4_first_impression": [],
    "section_7_personality_synthesis": [],
    "section_10_red_flags": [],
    "section_18_action_plan": [],
    "section_21_final_truth": [
        ("brutal_truth", "BRUTAL TRUTH"),
        ("must_do", "MUST-DO (NEXT 30 DAYS)"),
        ("closing_truth", "CLOSING"),
    ],
}

# Per-section "score bars" — map from key to (label, max)
SECTION_SCORE_BARS = {
    "section_4_first_impression": [
        ("confidence_out_of_10", "Self-Confidence", 10),
        ("trust_out_of_10",      "Trust",           10),
        ("attraction_out_of_10", "Attraction",      10),
        ("authority_out_of_10",  "Authority",       10),
    ],
    "section_3_mask_vs_real": [
        ("symmetry_score", "Facial Symmetry", 100),
    ],
    "section_9_career_money": [
        ("wealth_score_100", "Wealth Potential", 100),
    ],
    "section_11_attraction_charisma": [
        ("charisma_score_100", "Charisma Score", 100),
    ],
    "section_16_health_scan": [
        ("vitality_score_100", "Vitality",       100),
        ("overall_health_score","Overall Health",100),
    ],
    "bonus_personality_score": [
        ("leadership_10",   "Leadership",   10),
        ("money_10",        "Money",        10),
        ("love_10",         "Love",         10),
        ("health_10",       "Health",       10),
        ("intelligence_10", "Intelligence", 10),
    ],
}

# Keys to render BEFORE callouts/bars (the rest go after)
SECTION_HIDE_KEYS = {
    # keys whose values are already shown in callouts/bars — hide from raw list
    "section_1_power_summary":      {"biggest_strength","biggest_weakness","one_line_truth","summary_paragraph","intro_para","blocks","summary_paragraph_hi","current_life_phase"},
    "section_18_action_plan":       {"intro_para","blocks","behavioural_fix_hi","confidence_improvement_hi","lifestyle_suggestion_hi"},
    "section_19_improvement_hacks": {"intro_para","blocks","hacks_hi"},
    "section_4_first_impression":   {"confidence_out_of_10","trust_out_of_10","attraction_out_of_10","authority_out_of_10"},
    "section_3_mask_vs_real":       {"symmetry_score"},
    "section_9_career_money":       {"wealth_score_100"},
    "section_11_attraction_charisma": {"charisma_score_100"},
    "section_16_health_scan":       {"vitality_score_100","overall_health_score"},
    "section_6_feature_analysis":   {"intro_para","feature_blocks"},
    "section_7_personality_synthesis": {"intro_para","blocks"},
    "section_8_love_relationship_dna": {"intro_para","blocks"},
    "section_14_life_flow":         {"intro_para","blocks"},
    "section_21_final_truth":       {"brutal_truth","must_do","closing_truth"},
    "bonus_personality_score":      {"leadership_10","money_10","love_10","health_10","intelligence_10"},
}


def _try_num(v) -> Optional[float]:
    try: return float(v)
    except (TypeError, ValueError): return None


def _render_field(label: str, value: Any, styles) -> List:
    flowables = []
    if isinstance(value, list):
        if label:
            flowables.append(Paragraph(_safe(label), styles["field_label"]))
        for item in value:
            if isinstance(item, dict):
                parts = [f"<b>{_safe(k.replace('_',' ').title())}:</b> {_safe(v)}" for k, v in item.items()]
                flowables.append(Paragraph(" · ".join(parts), styles["bullet"], bulletText="•"))
            else:
                flowables.append(Paragraph(_safe(item), styles["bullet"], bulletText="•"))
    elif isinstance(value, dict):
        if label:
            flowables.append(Paragraph(_safe(label), styles["field_label"]))
        for k, v in value.items():
            sub_label = k.replace("_", " ").title()
            if isinstance(v, (dict, list)):
                flowables.append(Paragraph(f"<b>{_safe(sub_label)}:</b>", styles["field_value"]))
                flowables.extend(_render_field("", v, styles))
            else:
                flowables.append(Paragraph(f"<b>{_safe(sub_label)}:</b> {_safe(v)}", styles["field_value"]))
    else:
        if label:
            flowables.append(Paragraph(f"<b>{_safe(label)}:</b> {_safe(value)}", styles["field_value"]))
        else:
            flowables.append(Paragraph(_safe(value), styles["field_value"]))
    return flowables


_BAND_COLORS = {
    "low":         HexColor("#B85A3E"),
    "high":        HexColor("#3E7A4F"),
    "medium":      HexColor("#7A6F4D"),
    "balanced":    HexColor("#7A6F4D"),
    "narrow":      HexColor("#B85A3E"),
    "wide":        HexColor("#3E7A4F"),
    "close":       HexColor("#B85A3E"),
    "small":       HexColor("#B85A3E"),
    "large":       HexColor("#3E7A4F"),
    "tall":        HexColor("#3E7A4F"),
    "soft":        HexColor("#7A6F4D"),
    "sharp":       HexColor("#3E7A4F"),
    "info":        HexColor("#7A7164"),
}


def _render_feature_block(block: Dict, styles, idx: int) -> List:
    """Render one of the 7 feature deep-dive blocks (~2 pages)."""
    out: List = []

    # Sub-banner: maroon bar with feature name (white) + gold underline
    name_hi = block.get("feature_name_hi", "")
    name_en = block.get("feature_name_en", "")

    sub_banner_data = [[Paragraph(
        f'<font color="white"><b>{_safe(name_hi)}</b></font>', styles["score_label"]
    )]]
    sb = Table(sub_banner_data, colWidths=[174*mm])
    sb.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_PRIMARY),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    out.append(sb)

    # Gold thin rule
    out.append(HRFlowable(width="100%", thickness=1.2, color=C_ACCENT,
                          spaceBefore=0, spaceAfter=4))
    if name_en:
        out.append(Paragraph(_safe(name_en), styles["section_title_en"]))

    # Samudrika classical reading (callout box)
    cls = block.get("samudrika_class", "")
    phala = block.get("samudrika_phala", "")
    if phala:
        label = f"SAMUDRIKA SHASTRA — {cls}".strip(" —")
        out.append(Spacer(1, 2*mm))
        out.append(_callout(label, phala, styles))

    # Micro-measurements table
    micros = block.get("micro_measurements") or []
    if micros:
        out.append(Spacer(1, 4*mm))
        out.append(Paragraph("Micro-Measurements (real engine data)", styles["field_label"]))
        rows = [["Feature", "Value", "Reading"]]
        for m in micros:
            band = m.get("band", "info")
            color = _BAND_COLORS.get(band, C_INK)
            value_html = f'<font color="#{color.hexval()[2:].rjust(6,"0")}"><b>{_safe(m.get("value_text",""))}</b></font>'
            rows.append([
                Paragraph(f'<b>{_safe(m.get("label",""))}</b>', styles["field_value"]),
                Paragraph(value_html, styles["field_value"]),
                Paragraph(_safe(m.get("meaning_hi","")), styles["field_value"]),
            ])
        t = Table(rows, colWidths=[55*mm, 28*mm, 91*mm], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), C_PRIMARY),
            ("TEXTCOLOR",  (0,0), (-1,0), white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,0), 9.5),
            ("ALIGN",      (0,0), (-1,0), "LEFT"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_BG_TINT, white]),
            ("VALIGN",     (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING",(0,0), (-1,-1), 6),
            ("RIGHTPADDING",(0,0),(-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING",(0,0),(-1,-1), 5),
            ("LINEBELOW",  (0,0), (-1,0), 0.6, C_ACCENT),
            ("BOX",        (0,0), (-1,-1), 0.4, C_RULE),
        ]))
        out.append(t)

    # Five rich prose paragraphs
    paras = [
        ("Personality Meaning",      block.get("personality_meaning")),
        ("Love & Relationship",      block.get("love_implication")),
        ("Career & Decision Style",  block.get("career_decision")),
        ("Stress Response",          block.get("stress_response")),
        ("Improvement Hack",         block.get("improvement_tip")),
    ]
    for label, txt in paras:
        if not txt: continue
        out.append(Spacer(1, 4*mm))
        out.append(Paragraph(_safe(label), styles["field_label"]))
        out.append(Paragraph(_safe(txt), styles["field_value"]))

    # Page break between feature blocks (so each gets its own ~2 pages)
    out.append(PageBreak())
    return out


def _render_section_6_deep(sec: Dict, styles) -> List:
    """Custom renderer for Section 6 — 7-feature deep dive (~14 pages)."""
    flowables: List = []
    flowables.append(SectionBanner(sec["no"]))
    flowables.append(Spacer(1, 4*mm))
    flowables.append(Paragraph(_safe(sec["title_hi"]), styles["section_title_hi"]))
    flowables.append(Paragraph(_safe(sec["title_en"]), styles["section_title_en"]))

    content = sec.get("content") or {}
    intro = content.get("intro_para") or sec.get("narrative") or ""
    if intro:
        flowables.append(Paragraph(_safe(intro), styles["narrative"]))

    # Mini index of the 7 features
    blocks = content.get("feature_blocks") or []
    if blocks:
        flowables.append(Spacer(1, 2*mm))
        flowables.append(Paragraph("Is section me 7 features detail me cover honge:", styles["field_label"]))
        for i, b in enumerate(blocks, 1):
            flowables.append(Paragraph(
                f"{i}. <b>{_safe(b.get('feature_name_hi',''))}</b> — {_safe(b.get('feature_name_en',''))}",
                styles["field_value"]))
        flowables.append(PageBreak())

    for i, b in enumerate(blocks):
        flowables.extend(_render_feature_block(b, styles, i))
    return flowables


_DEEP_BLOCK_SECTIONS = {
    "section_1_power_summary",
    "section_7_personality_synthesis",
    "section_8_love_relationship_dna",
    "section_9_career_money",
    "section_14_life_flow",
    "section_18_action_plan",
    "section_19_improvement_hacks",
    "bonus_personality_score",
}


def _render_deep_block(block: Dict, styles, idx: int) -> List:
    """Render one deep block (heading + key_metric + body + callout + bullets)."""
    out: List = []
    h_hi = block.get("heading_hi", "")
    h_en = block.get("heading_en", "")

    # Sub-banner: maroon bar with block heading
    sub = [[Paragraph(
        f'<font color="white"><b>{idx+1}. {_safe(h_hi)}</b></font>', styles["score_label"]
    )]]
    sb = Table(sub, colWidths=[174*mm])
    sb.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_PRIMARY),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    out.append(sb)
    out.append(HRFlowable(width="100%", thickness=1.2, color=C_ACCENT,
                          spaceBefore=0, spaceAfter=4))
    if h_en:
        out.append(Paragraph(_safe(h_en), styles["section_title_en"]))

    # Key metric pill
    km = block.get("key_metric") or {}
    if km.get("label") and km.get("value") is not None:
        pill = [[
            Paragraph(f'<font color="white"><b>{_safe(km["label"])}</b></font>', styles["field_value"]),
            Paragraph(f'<font color="white"><b>{_safe(km["value"])}</b></font>', styles["field_value"]),
        ]]
        pt = Table(pill, colWidths=[110*mm, 64*mm])
        pt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), HexColor("#3E5C7A")),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("ALIGN", (1,0), (1,0), "RIGHT"),
        ]))
        out.append(Spacer(1, 2*mm))
        out.append(pt)

    # Body (long Hinglish prose)
    body = block.get("body")
    if body:
        out.append(Spacer(1, 3*mm))
        out.append(Paragraph(_safe(body), styles["field_value"]))

    # Bullets
    bullets = block.get("bullets") or []
    for b in bullets:
        out.append(Paragraph(_safe(b), styles["bullet"], bulletText="•"))

    # Callout (insight box)
    co = block.get("callout") or {}
    if co.get("text"):
        out.append(Spacer(1, 3*mm))
        out.append(_callout(co.get("label","INSIGHT"), co.get("text",""), styles))

    out.append(Spacer(1, 6*mm))
    return out


def _render_section_deep(sec: Dict, styles) -> List:
    """Generic renderer for sections 7/8/9/14 — intro_para + blocks[]."""
    out: List = []
    out.append(SectionBanner(sec["no"]))
    out.append(Spacer(1, 4*mm))
    out.append(Paragraph(_safe(sec["title_hi"]), styles["section_title_hi"]))
    out.append(Paragraph(_safe(sec["title_en"]), styles["section_title_en"]))

    content = sec.get("content") or {}
    intro = content.get("intro_para") or sec.get("narrative") or ""
    if intro:
        out.append(Paragraph(_safe(intro), styles["narrative"]))

    blocks = content.get("blocks") or []
    if blocks:
        out.append(Spacer(1, 4*mm))
    for i, b in enumerate(blocks):
        out.extend(_render_deep_block(b, styles, i))

    # Section 9 score bar (wealth) etc.
    bars = SECTION_SCORE_BARS.get(sec.get("key", ""), [])
    if bars:
        for bkey, blabel, bmax in bars:
            bv = _try_num(content.get(bkey))
            if bv is not None:
                out.append(Spacer(1, 2*mm))
                out.append(ScoreBar(blabel, bv, bmax))
    return out


def _render_section(sec: Dict, styles) -> List:
    flowables: List = []
    key = sec.get("key", "")

    # Custom deep renderer for Section 6
    if key == "section_6_feature_analysis":
        return _render_section_6_deep(sec, styles)
    if key in _DEEP_BLOCK_SECTIONS:
        return _render_section_deep(sec, styles)

    # Banner + titles
    flowables.append(SectionBanner(sec["no"]))
    flowables.append(Spacer(1, 4*mm))
    flowables.append(Paragraph(_safe(sec["title_hi"]), styles["section_title_hi"]))
    flowables.append(Paragraph(_safe(sec["title_en"]), styles["section_title_en"]))

    # Narrative prose intro (the premium upgrade)
    narr = (sec.get("narrative") or "").strip()
    if narr:
        flowables.append(Paragraph(_safe(narr), styles["narrative"]))

    content = sec.get("content") or {}
    if not isinstance(content, dict):
        flowables.append(Paragraph(_safe(content), styles["field_value"]))
        flowables.append(Spacer(1, 8*mm))
        return flowables

    # Callouts
    callouts = SECTION_CALLOUTS.get(key, [])
    for ckey, clabel in callouts:
        v = content.get(ckey)
        if v:
            flowables.append(Spacer(1, 2*mm))
            flowables.append(_callout(clabel, v, styles))

    # Score bars
    bars = SECTION_SCORE_BARS.get(key, [])
    if bars:
        flowables.append(Spacer(1, 4*mm))
        for bkey, blabel, bmax in bars:
            bv = _try_num(content.get(bkey))
            if bv is not None:
                flowables.append(ScoreBar(blabel, bv, bmax))
                flowables.append(Spacer(1, 2*mm))

    # Remaining structured fields (skip ones already shown + skip _hi twins
    # whose English version is already rendered with the same value)
    hide = SECTION_HIDE_KEYS.get(key, set())
    has_extra = False
    seen_keys: set = set()
    for k, v in content.items():
        if k in hide:        continue
        if v in (None,"",[],{}): continue
        # Skip a "<base>_hi" key if base key already exists in content
        if k.endswith("_hi"):
            base = k[:-3]
            if base in content and content.get(base) not in (None, "", [], {}):
                continue
        seen_keys.add(k)
        if not has_extra:
            flowables.append(Spacer(1, 3*mm))
            has_extra = True
        label_pretty = k.replace("_hi","").replace("_en","").replace("_"," ").strip().title()
        flowables.extend(_render_field(label_pretty, v, styles))

    flowables.append(Spacer(1, 8*mm))
    return flowables


# ── Cover page ────────────────────────────────────────────────────────────
def _render_cover(cover: Dict, styles) -> List:
    flowables = []
    flowables.append(Spacer(1, 35 * mm))
    flowables.append(Paragraph("PREMIUM REPORT  ·  Rs.1499 EDITION", styles["cover_kicker"]))
    flowables.append(Paragraph(_safe(cover.get("report_title", "Face Intelligence Report")),
                               styles["cover_title"]))
    flowables.append(Paragraph(_safe(cover.get("report_subtitle", "")),
                               styles["cover_subtitle"]))
    flowables.append(HRFlowable(width="50%", thickness=2, color=C_ACCENT,
                                spaceBefore=12, spaceAfter=20, hAlign="CENTER"))
    flowables.append(Paragraph(_safe(cover.get("name", "Insan")), styles["cover_name"]))

    meta_lines = []
    if cover.get("age"):           meta_lines.append(f"Aayu: {cover['age']} saal")
    if cover.get("gender") and cover["gender"] != "U":
        meta_lines.append(f"Linga: {'Pursh' if cover['gender']=='M' else 'Stree'}")
    if cover.get("perceived_age"): meta_lines.append(f"Pratyaksh Aayu: ~{cover['perceived_age']:.0f} saal")
    if meta_lines:
        flowables.append(Paragraph(" · ".join(_safe(m) for m in meta_lines), styles["cover_meta"]))

    flowables.append(Spacer(1, 12 * mm))
    flowables.append(Paragraph("Tumhara Archetype:", styles["cover_meta"]))
    flowables.append(Paragraph(_safe(cover.get("archetype", "Balanced Soul")), styles["cover_archetype"]))
    flowables.append(Spacer(1, 8 * mm))
    flowables.append(Paragraph(
        f"Mukh Aakar: <b>{_safe(cover.get('face_shape','-')).title()}</b> · "
        f"Tatva: <b>{_safe(cover.get('dominant_element','-'))}</b>" +
        (f" · Varna: <b>{_safe(cover['complexion'])}</b>" if cover.get("complexion") else ""),
        styles["cover_meta"]))

    flowables.append(Spacer(1, 35 * mm))
    flowables.append(HRFlowable(width="30%", thickness=0.6, color=C_RULE,
                                spaceBefore=4, spaceAfter=8, hAlign="CENTER"))
    flowables.append(Paragraph(
        "Yeh report tumhare chehre se nikla hua 100% personalized truth hai.<br/>"
        "<b>21 sections · 9 engines · Vedic Samudrika + Modern Psychology</b>",
        styles["cover_meta"]))
    return flowables


# ── Table of Contents ─────────────────────────────────────────────────────
def _render_toc(report: Dict, styles) -> List:
    flowables = []
    flowables.append(Paragraph("Table of Contents", styles["toc_header"]))
    flowables.append(HRFlowable(width="20%", thickness=2, color=C_ACCENT,
                                spaceBefore=2, spaceAfter=14, hAlign="LEFT"))

    rows = []
    for sec in report.get("sections", []):
        no = sec["no"]
        title_hi = sec["title_hi"]
        title_en = sec["title_en"]
        rows.append([
            Paragraph(f"<font color='#7B1F1F'><b>{_safe(no)}</b></font>", styles["toc_row"]),
            Paragraph(f"<b>{_safe(title_hi)}</b>  <font color='#7A7164'>· {_safe(title_en)}</font>",
                      styles["toc_row"]),
        ])
    t = Table(rows, colWidths=[14*mm, 160*mm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("LINEBELOW", (0,0), (-1,-2), 0.3, C_RULE),
    ]))
    flowables.append(t)
    return flowables


# ── Main entrypoint ───────────────────────────────────────────────────────
def render_pdf(report: Dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=22 * mm, bottomMargin=22 * mm,
        title=report.get("cover", {}).get("report_title", "Face Intelligence Report"),
        author="Cosmic Lens",
    )
    styles = _styles()

    story: List = []

    # 1. Cover
    story.extend(_render_cover(report.get("cover", {}), styles))
    story.append(PageBreak())

    # 2. Table of Contents
    story.extend(_render_toc(report, styles))
    story.append(PageBreak())

    # 3. Sections (each may span multiple pages)
    for sec in report.get("sections", []):
        story.extend(_render_section(sec, styles))

    # 4. Disclaimer
    story.append(PageBreak())
    story.append(Spacer(1, 60 * mm))
    story.append(HRFlowable(width="60%", thickness=1, color=C_ACCENT,
                            spaceBefore=4, spaceAfter=14, hAlign="CENTER"))
    story.append(Paragraph("Disclaimer", styles["section_title_hi"]))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(_safe(report.get("footer_disclaimer", "")), styles["field_value"]))

    doc.build(story, onFirstPage=_on_cover_page, onLaterPages=_on_page)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes

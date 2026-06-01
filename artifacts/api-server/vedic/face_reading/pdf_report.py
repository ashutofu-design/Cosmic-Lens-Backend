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
    KeepTogether, HRFlowable, Flowable, Image as RLImage,
)
from reportlab.lib.utils import ImageReader

from .pdf_visuals import (
    make_cover_photo, make_face_map, make_radar_chart, make_score_bars,
)
from .celebrity_match import build_celebrity_section


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
    # Section 20: hide back-compat alias keys so the same partner-line is not printed 2-3 times
    # (consistency_layer mirrors best_match → ideal_partner / best_match_hi for legacy callers).
    "section_20_compatibility":     {"best_match_hi","avoid_match_hi","ideal_partner","avoid_partner"},
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
# ── Synthesis renderer (6-key fusion: fused traits, shock insights,
#    behavior simulation, reasoning, confidence scores, remedies) ─────────
def _synth_banner(label_hi: str, label_en: str, styles) -> List:
    """Banner header for each synthesis sub-section."""
    out: List = []
    cell = [[
        Paragraph(_safe(label_hi), styles["section_title_hi"]),
        Paragraph(_safe(label_en), styles["section_title_en"]),
    ]]
    t = Table(cell, colWidths=[174 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_CALLOUT_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBEFORE", (0, 0), (0, -1), 3, C_PRIMARY),
    ]))
    out.append(t)
    out.append(Spacer(1, 4 * mm))
    return out


def _render_synthesis_pages(synthesis: Dict, styles, skip_shocks: bool = False) -> List:
    """Render the 6-key Final Synthesis Layer across multiple pages.
    If skip_shocks=True, omit shock insights (shown earlier in flow)."""
    if not synthesis or not isinstance(synthesis, dict):
        return []

    flowables: List = []

    # ── Title page ─────────────────────────────────────────────────────────
    flowables.append(Spacer(1, 8 * mm))
    flowables.append(SectionBanner("22"))
    flowables.append(Spacer(1, 4 * mm))
    flowables.append(Paragraph("Antim Sankalan — Cosmic Intelligence Fusion",
                               styles["section_title_hi"]))
    flowables.append(Paragraph("Final Synthesis — 6-Key Cross-Engine Fusion",
                               styles["section_title_en"]))
    flowables.append(Paragraph(
        _safe("Yeh section 8 alag-alag engines ke insights ko ek saath cross-reference "
              "karke wo unique patterns nikaalta hai jo single engine se nahi mil sakte. "
              "Har conclusion ke peeche reasoning aur confidence score bhi diya hai."),
        styles["narrative"]))
    flowables.append(Spacer(1, 6 * mm))

    # ── 1. Fused Traits ────────────────────────────────────────────────────
    fused = synthesis.get("fused_traits") or []
    if fused:
        flowables.extend(_synth_banner(
            "Mishrit Lakshan (Fused Traits)",
            "Multi-engine personality patterns", styles))
        for i, item in enumerate(fused, 1):
            if not isinstance(item, dict):
                continue
            trait = item.get("trait", "")
            summary = item.get("summary", "")
            intensity = item.get("intensity")
            sources = item.get("sources") or []
            flowables.append(Paragraph(
                f"<b>{i}. {_safe(trait)}</b>", styles["field_label"]))
            if summary:
                flowables.append(Paragraph(_safe(summary), styles["field_value"]))
            if isinstance(intensity, (int, float)):
                flowables.append(ScoreBar("Intensity", float(intensity), 100))
            if sources:
                flowables.append(Paragraph(
                    f"<i>Source signals: {_safe(', '.join(map(str, sources)))}</i>",
                    styles["field_value"]))
            flowables.append(Spacer(1, 4 * mm))

    # ── 2. Shock Insights ──────────────────────────────────────────────────
    shocks = (synthesis.get("shock_insights") or []) if not skip_shocks else []
    if shocks:
        flowables.append(Spacer(1, 4 * mm))
        flowables.extend(_synth_banner(
            "Chonkane Wale Sach (Shock Insights)",
            "Surprising hidden patterns", styles))
        for i, item in enumerate(shocks, 1):
            if not isinstance(item, dict):
                continue
            insight = item.get("insight", "")
            category = item.get("category", "")
            if insight:
                flowables.append(_callout(
                    f"INSIGHT {i}" + (f"  ·  {category}" if category else ""),
                    insight, styles))
                flowables.append(Spacer(1, 3 * mm))

    # ── 3. Behavior Simulation ─────────────────────────────────────────────
    sims = synthesis.get("behavior_simulation") or []
    if sims:
        flowables.append(PageBreak())
        flowables.extend(_synth_banner(
            "Vyavhar Pradarshan (Behavior Simulation)",
            "Real-life scenario predictions", styles))
        for i, item in enumerate(sims, 1):
            if not isinstance(item, dict):
                continue
            scenario = item.get("scenario", "")
            prediction = item.get("prediction", "")
            flowables.append(Paragraph(
                f"<b>Scenario {i}: {_safe(scenario)}</b>", styles["field_label"]))
            if prediction:
                flowables.append(Paragraph(_safe(prediction), styles["field_value"]))
            flowables.append(Spacer(1, 5 * mm))

    # ── 4. Reasoning ───────────────────────────────────────────────────────
    reasons = synthesis.get("reasoning") or []
    if reasons:
        flowables.append(Spacer(1, 4 * mm))
        flowables.extend(_synth_banner(
            "Tark (Reasoning Trail)",
            "Why each conclusion was drawn", styles))
        for item in reasons:
            if not isinstance(item, dict):
                continue
            target = item.get("for", "")
            why = item.get("why", "")
            kind = item.get("kind", "")
            flowables.append(Paragraph(
                f"<b>{_safe(target)}</b>" + (f"  <i>({_safe(kind)})</i>" if kind else ""),
                styles["field_label"]))
            if why:
                flowables.append(Paragraph(_safe(why), styles["field_value"]))
            flowables.append(Spacer(1, 3 * mm))

    # ── 5. Confidence Scores ───────────────────────────────────────────────
    confs = synthesis.get("confidence_scores") or []
    if confs:
        flowables.append(PageBreak())
        flowables.extend(_synth_banner(
            "Vishwas Sthar (Confidence Scores)",
            "How sure we are about each finding", styles))
        for item in confs:
            if not isinstance(item, dict):
                continue
            label = item.get("label", "")
            score = item.get("score")
            kind = item.get("kind", "")
            label_disp = (label[:60] + "…") if len(str(label)) > 60 else str(label)
            display = f"{label_disp}" + (f"  ({kind})" if kind else "")
            if isinstance(score, (int, float)):
                flowables.append(ScoreBar(display, float(score), 100))
                flowables.append(Spacer(1, 2 * mm))

    # ── 6. Remedies ────────────────────────────────────────────────────────
    remedies = synthesis.get("remedies") or []
    if remedies:
        flowables.append(PageBreak())
        flowables.extend(_synth_banner(
            "Upay (Personalised Remedies)",
            "Behaviour + habit + environment fixes", styles))
        for i, item in enumerate(remedies, 1):
            if not isinstance(item, dict):
                continue
            area = item.get("area", "")
            cur = item.get("current_score")
            lift = item.get("expected_lift", "")
            behaviour = item.get("behaviour", "")
            habit = item.get("habit", "")
            env = item.get("environment", "")

            head = f"<b>Upay {i}: {_safe(str(area).replace('_', ' ').title())}</b>"
            if isinstance(cur, (int, float)):
                head += f"  ·  Abhi: {cur:.0f}/100"
            flowables.append(Paragraph(head, styles["field_label"]))
            if behaviour:
                flowables.append(Paragraph(
                    f"<b>Behaviour:</b> {_safe(behaviour)}", styles["field_value"]))
            if habit:
                flowables.append(Paragraph(
                    f"<b>Habit:</b> {_safe(habit)}", styles["field_value"]))
            if env:
                flowables.append(Paragraph(
                    f"<b>Environment:</b> {_safe(env)}", styles["field_value"]))
            if lift:
                flowables.append(Paragraph(
                    f"<i>Expected lift: {_safe(lift)}</i>", styles["field_value"]))
            flowables.append(Spacer(1, 5 * mm))

    return flowables


# ── Phase-1 premium upgrade: HOOK COVER (page 1) ─────────────────────────
def _render_hook_cover(hook: Dict, cover: Dict, styles,
                       photo_bytes: Optional[bytes] = None,
                       points_norm: Optional[list] = None) -> List:
    """Premium cover page — identity line + shock + score snapshot.
    Designed for instant emotional connection in 5 seconds."""
    flowables: List = []

    flowables.append(Spacer(1, 6 * mm))
    flowables.append(Paragraph("PREMIUM REPORT  ·  Cosmic Intelligence Edition",
                               styles["cover_kicker"]))
    flowables.append(Paragraph(_safe(cover.get("report_title",
                                               "Face Intelligence Report")),
                               styles["cover_title"]))

    # Photo (smaller — make room for hook content)
    if photo_bytes:
        try:
            png_bytes = make_cover_photo(photo_bytes, points_norm, out_size=420)
            if png_bytes:
                img = RLImage(BytesIO(png_bytes), width=58 * mm, height=58 * mm)
                img.hAlign = "CENTER"
                flowables.append(Spacer(1, 2 * mm))
                flowables.append(img)
        except Exception:
            pass

    flowables.append(Spacer(1, 3 * mm))
    flowables.append(Paragraph(_safe(cover.get("name", "Insan")),
                               styles["cover_name"]))

    # Identity tag (element + archetype)
    elt = hook.get("element", "Balanced")
    arch = hook.get("archetype", "Balanced Soul")
    flowables.append(Paragraph(
        f"<b>{_safe(elt)}</b> tatva  ·  <b>{_safe(arch)}</b> archetype",
        styles["cover_meta"]))
    flowables.append(Spacer(1, 6 * mm))

    # ── HOOK LINE 1: Identity (deep, specific) ──────────────────────
    identity = hook.get("identity_line", "")
    if identity:
        cell = [[Paragraph(_safe(identity), styles["narrative"])]]
        t = Table(cell, colWidths=[170 * mm], hAlign="CENTER")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_CALLOUT_BG),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("LINEBEFORE", (0, 0), (0, -1), 4, C_PRIMARY),
        ]))
        flowables.append(t)
        flowables.append(Spacer(1, 5 * mm))

    # ── HOOK LINE 2: Shock insight ──────────────────────────────────
    shock = hook.get("shock_line", "")
    if shock:
        flowables.append(_callout("ONE SHOCK INSIGHT  ·  shuruaat me hi",
                                  shock, styles))
        flowables.append(Spacer(1, 5 * mm))

    # ── HOOK LINE 3: Score snapshot ─────────────────────────────────
    scores = hook.get("scores") or {}
    if scores:
        flowables.append(Paragraph("Tumhare 3 Core Scores",
                                   styles["field_label"]))
        flowables.append(Spacer(1, 1 * mm))
        for label, key in [("Vitality", "vitality"),
                           ("Charisma", "charisma"),
                           ("Leadership", "leadership")]:
            v = scores.get(key)
            if isinstance(v, (int, float)) and v > 0:
                flowables.append(ScoreBar(label, float(v), 100))
                flowables.append(Spacer(1, 1 * mm))

    flowables.append(Spacer(1, 8 * mm))
    flowables.append(HRFlowable(width="35%", thickness=0.6, color=C_RULE,
                                spaceBefore=2, spaceAfter=4, hAlign="CENTER"))
    flowables.append(Paragraph(
        "<b>22 sections · 9 engines · Vedic Samudrika + Modern Psychology</b><br/>"
        "Page palto — TL;DR agle page pe.",
        styles["cover_meta"]))
    return flowables


# ── Phase-1 premium upgrade: TL;DR PAGE (page 2) ──────────────────────────
def _render_tldr_page(tldr: Dict, styles) -> List:
    """Value-on-skip page — full essence in one page."""
    flowables: List = []
    flowables.append(Spacer(1, 4 * mm))
    flowables.append(Paragraph("TL;DR — Agar Sirf Yeh Padho",
                               styles["section_title_hi"]))
    flowables.append(Paragraph("The 30-Second Read · Skip-Proof Summary",
                               styles["section_title_en"]))
    flowables.append(HRFlowable(width="25%", thickness=2, color=C_ACCENT,
                                spaceBefore=4, spaceAfter=10, hAlign="LEFT"))

    # ── Top 5 personality traits (with bars) ──────────────────────
    traits = tldr.get("top_5_traits") or []
    if traits:
        flowables.append(Paragraph("Top 5 Personality Traits",
                                   styles["field_label"]))
        flowables.append(Spacer(1, 2 * mm))
        for t in traits:
            if not isinstance(t, dict):
                continue
            name = t.get("name", "")
            score = t.get("score", 0)
            tag = t.get("tag", "")
            label = f"{name}  ({tag})"
            flowables.append(ScoreBar(label, float(score), 100))
            flowables.append(Spacer(1, 1 * mm))
        flowables.append(Spacer(1, 4 * mm))

    # ── Top 3 strengths ────────────────────────────────────────────
    strengths = tldr.get("top_3_strengths") or []
    if strengths:
        cell_rows = [[Paragraph(
            "<font color='#7B1F1F'><b>TOP 3 STRENGTHS</b></font>",
            styles["callout_label"])]]
        for i, s in enumerate(strengths, 1):
            cell_rows.append([Paragraph(f"<b>{i}.</b> {_safe(s)}",
                                        styles["callout_text"])])
        t = Table(cell_rows, colWidths=[174 * mm], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F4F0E5")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LINEBEFORE", (0, 0), (0, -1), 3, C_ACCENT),
        ]))
        flowables.append(t)
        flowables.append(Spacer(1, 4 * mm))

    # ── Top 3 weaknesses ───────────────────────────────────────────
    weaknesses = tldr.get("top_3_weaknesses") or []
    if weaknesses:
        cell_rows = [[Paragraph(
            "<font color='#7B1F1F'><b>TOP 3 WEAKNESSES / BLIND SPOTS</b></font>",
            styles["callout_label"])]]
        for i, w in enumerate(weaknesses, 1):
            cell_rows.append([Paragraph(f"<b>{i}.</b> {_safe(w)}",
                                        styles["callout_text"])])
        t = Table(cell_rows, colWidths=[174 * mm], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#FBEEE6")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LINEBEFORE", (0, 0), (0, -1), 3, C_PRIMARY),
        ]))
        flowables.append(t)
        flowables.append(Spacer(1, 5 * mm))

    # ── Life pattern (one line) ────────────────────────────────────
    life = tldr.get("life_pattern", "")
    if life:
        flowables.append(_callout("YOUR LIFE PATTERN  ·  ek line me",
                                  life, styles))

    return flowables


# ── Phase-1 premium upgrade: SHOCK INSIGHTS EARLY (page 8-12) ────────────
def _render_shock_insights_early(synthesis: Dict, styles) -> List:
    """Shock insights moved early in flow for engagement."""
    shocks = (synthesis or {}).get("shock_insights") or []
    if not shocks:
        return []
    confs = {c.get("label", "")[:30]: c.get("score", 70)
             for c in (synthesis.get("confidence_scores") or [])
             if isinstance(c, dict)}

    flowables: List = []
    flowables.append(Spacer(1, 6 * mm))
    flowables.append(Paragraph("Chonkane Wale Sach — Tumhare Bare Me",
                               styles["section_title_hi"]))
    flowables.append(Paragraph("Shock Insights · Things You Probably Didn't Know",
                               styles["section_title_en"]))
    flowables.append(HRFlowable(width="25%", thickness=2, color=C_ACCENT,
                                spaceBefore=4, spaceAfter=10, hAlign="LEFT"))
    flowables.append(Paragraph(
        _safe("Yeh wo patterns hain jo single feature dekh ke nahi pakde ja sakte — "
              "multiple engines mile tab nikle. Shuruaat me hi de raha hoon ki tumhe "
              "report me khinchav ho."),
        styles["narrative"]))
    flowables.append(Spacer(1, 4 * mm))

    for i, item in enumerate(shocks, 1):
        if not isinstance(item, dict):
            continue
        insight = item.get("insight", "")
        category = item.get("category", "")
        # confidence
        conf = 70
        for k, v in confs.items():
            if k and insight and k in insight:
                conf = v; break
        if insight:
            flowables.append(_callout(
                f"INSIGHT {i}  ·  {category or 'general'}  ·  "
                f"Confidence: {conf}%",
                insight, styles))
            flowables.append(Spacer(1, 4 * mm))
    return flowables


# ── Phase-1 premium upgrade: FINAL TRUTH v2 (3+3+1 format) ───────────────
def _render_final_truth_v2(ft2: Dict, styles) -> List:
    """Restructured Final Truth — 3 strengths + 3 risks + 1 direction."""
    if not ft2 or not isinstance(ft2, dict):
        return []
    flowables: List = []
    flowables.append(Spacer(1, 4 * mm))
    flowables.append(SectionBanner("21"))
    flowables.append(Spacer(1, 4 * mm))
    flowables.append(Paragraph("Antim Satya — Brutally Honest",
                               styles["section_title_hi"]))
    flowables.append(Paragraph("The Final Truth · No Sugar Coating",
                               styles["section_title_en"]))
    flowables.append(Spacer(1, 4 * mm))

    # Brutal one-liner at top
    brutal = ft2.get("brutal_truth", "")
    if brutal:
        flowables.append(_callout("BRUTAL TRUTH", brutal, styles))
        flowables.append(Spacer(1, 5 * mm))

    # 3 STRENGTHS
    strengths = ft2.get("strengths") or []
    if strengths:
        flowables.append(Paragraph(
            "<font color='#1B5E20'><b>3 STRENGTHS · TUMHARI TAKAT</b></font>",
            styles["field_label"]))
        for i, s in enumerate(strengths, 1):
            flowables.append(Paragraph(
                f"<b>+{i}.</b> {_safe(s)}", styles["field_value"]))
        flowables.append(Spacer(1, 4 * mm))

    # 3 RISKS
    risks = ft2.get("risks") or []
    if risks:
        flowables.append(Paragraph(
            "<font color='#7B1F1F'><b>3 RISKS · KHATRE KI GHANTI</b></font>",
            styles["field_label"]))
        for i, r in enumerate(risks, 1):
            flowables.append(Paragraph(
                f"<b>−{i}.</b> {_safe(r)}", styles["field_value"]))
        flowables.append(Spacer(1, 5 * mm))

    # 1 DIRECTION
    direction = ft2.get("direction", "")
    if direction:
        cell = [[Paragraph(
            "<font color='#7B1F1F'><b>1 LIFE DIRECTION  ·  Aaj Se Yeh Karna Hai</b></font>",
            styles["callout_label"])],
            [Paragraph(_safe(direction), styles["callout_text"])]]
        t = Table(cell, colWidths=[174 * mm], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F4F0E5")),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("LINEBEFORE", (0, 0), (0, -1), 4, C_PRIMARY),
        ]))
        flowables.append(t)

    return flowables


def _render_cover(cover: Dict, styles,
                  photo_bytes: Optional[bytes] = None,
                  points_norm: Optional[list] = None) -> List:
    flowables = []
    flowables.append(Spacer(1, 14 * mm))
    flowables.append(Paragraph("PREMIUM REPORT  ·  Rs.1499 EDITION", styles["cover_kicker"]))
    flowables.append(Paragraph(_safe(cover.get("report_title", "Face Intelligence Report")),
                               styles["cover_title"]))
    flowables.append(Paragraph(_safe(cover.get("report_subtitle", "")),
                               styles["cover_subtitle"]))
    flowables.append(HRFlowable(width="50%", thickness=2, color=C_ACCENT,
                                spaceBefore=8, spaceAfter=14, hAlign="CENTER"))

    # User photo (square cropped + framed)
    if photo_bytes:
        try:
            png_bytes = make_cover_photo(photo_bytes, points_norm, out_size=480)
            if png_bytes:
                img = RLImage(BytesIO(png_bytes), width=72*mm, height=72*mm)
                img.hAlign = "CENTER"
                flowables.append(img)
                flowables.append(Spacer(1, 6 * mm))
        except Exception:
            pass

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
    n_blocks = cover.get("n_blocks") or 21
    flowables.append(Paragraph(
        "Yeh report tumhare chehre se nikla hua 100% personalized truth hai.<br/>"
        f"<b>{n_blocks} dense blocks · 9 engines · Vedic Samudrika + Modern Psychology</b>",
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


# ── Annotated face map page ───────────────────────────────────────────────
def _render_face_map_page(photo_bytes: bytes, points_norm: list, styles) -> List:
    flowables = []
    flowables.append(Paragraph("Tumhare Chehre Ka Map", styles["section_title_hi"]))
    flowables.append(Paragraph("Face Zone Map · Where Each Reading Comes From",
                               styles["section_title_en"]))
    flowables.append(HRFlowable(width="20%", thickness=2, color=C_ACCENT,
                                spaceBefore=4, spaceAfter=10, hAlign="LEFT"))
    flowables.append(Paragraph(
        "Yeh tumhari actual photo hai jisko face-reading engines ne zone-wise analyze kiya. "
        "Har zone (mastak, aankh, naak, gaal, honth, jabda, thoddi) se alag-alag insights nikle hain — "
        "is map me dekho ki kis area se kya pada gaya hai.",
        styles["narrative"]))
    flowables.append(Spacer(1, 4*mm))
    try:
        png = make_face_map(photo_bytes, points_norm, max_height=820)
        if png:
            img = RLImage(BytesIO(png), width=160*mm, height=180*mm, kind="proportional")
            img.hAlign = "CENTER"
            flowables.append(img)
    except Exception as _e:
        flowables.append(Paragraph(f"<i>Map unavailable: {_safe(str(_e))}</i>", styles["field_value"]))
    flowables.append(Spacer(1, 6*mm))
    flowables.append(Paragraph(
        "<b>Reading guide:</b> Mastak → openness aur soch ka style. "
        "Aankhein → emotional depth aur first impression. "
        "Naak → ambition aur risk-style. "
        "Gaal → warmth aur approachability. "
        "Honth → expression aur extraversion. "
        "Jabdaa → discipline aur leadership. "
        "Thoddi → resolve aur long-term grit.",
        styles["narrative"]))
    return flowables


# ── Visual snapshot page ──────────────────────────────────────────────────
def _render_visual_snapshot_page(engines: Dict, sections: Dict, styles) -> List:
    flowables = []
    flowables.append(Paragraph("Vyaktitva Visual Snapshot", styles["section_title_hi"]))
    flowables.append(Paragraph("Personality at a Glance · Charts",
                               styles["section_title_en"]))
    flowables.append(HRFlowable(width="20%", thickness=2, color=C_ACCENT,
                                spaceBefore=4, spaceAfter=10, hAlign="LEFT"))
    flowables.append(Paragraph(
        "Numbers se zyada kuch nahi bolta. Yeh do charts tumhare pure report ka "
        "<b>visual fingerprint</b> hain — ek polygon shape (Big-5 traits) aur "
        "ek bar-stack (5 premium scores). Inko save kar lo — 6 mahine baad dobara test "
        "karo aur compare karo, growth khud dikhegi.",
        styles["narrative"]))
    flowables.append(Spacer(1, 4*mm))

    # Radar of OCEAN big-5
    try:
        traits = (engines.get("personality") or {}).get("traits") or {}
        radar_in = {
            "O": (traits.get("openness")          or {}).get("score"),
            "C": (traits.get("conscientiousness") or {}).get("score"),
            "E": (traits.get("extraversion")      or {}).get("score"),
            "A": (traits.get("agreeableness")     or {}).get("score"),
            "N": (traits.get("neuroticism")       or {}).get("score"),
        }
        png = make_radar_chart({k: (v if v is not None else 50) for k, v in radar_in.items()})
        img = RLImage(BytesIO(png), width=130*mm, height=130*mm, kind="proportional")
        img.hAlign = "CENTER"
        flowables.append(img)
    except Exception as _e:
        flowables.append(Paragraph(f"<i>Radar unavailable: {_safe(str(_e))}</i>", styles["field_value"]))

    flowables.append(Spacer(1, 6*mm))

    # Score bars
    try:
        bonus = sections.get("bonus_personality_score") or {}
        scores = {k: bonus.get(k) for k in
                  ("leadership_10","intelligence_10","money_10","love_10","health_10")}
        png = make_score_bars(scores)
        img = RLImage(BytesIO(png), width=160*mm, height=110*mm, kind="proportional")
        img.hAlign = "CENTER"
        flowables.append(img)
    except Exception as _e:
        flowables.append(Paragraph(f"<i>Bars unavailable: {_safe(str(_e))}</i>", styles["field_value"]))

    return flowables


# ── Celebrity match page ──────────────────────────────────────────────────
def _render_celebrity_page(engines: Dict, styles) -> List:
    flowables = []
    flowables.append(Paragraph("Mashhoor Hastiyon Se Tulna",
                               styles["section_title_hi"]))
    flowables.append(Paragraph("Celebrity Archetype Match",
                               styles["section_title_en"]))
    flowables.append(HRFlowable(width="20%", thickness=2, color=C_ACCENT,
                                spaceBefore=4, spaceAfter=10, hAlign="LEFT"))

    data = build_celebrity_section(engines.get("personality") or {},
                                   engines.get("samudrika") or {})
    flowables.append(Paragraph(_safe(data["intro_para"]), styles["narrative"]))
    flowables.append(Spacer(1, 6*mm))

    for i, m in enumerate(data["matches"], 1):
        # Mini-card: name + signature trait + why
        rows = [
            [Paragraph(f"<font color='#7B1F1F'><b>#{i}  {_safe(m['name'])}</b></font>",
                       styles["callout_label"])],
            [Paragraph(f"<b>Signature pattern:</b> {_safe(m['signature_trait_hi'])}",
                       styles["field_value"])],
            [Paragraph(_safe(m["why_hi"]), styles["narrative"])],
        ]
        t = Table(rows, colWidths=[170*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), C_CALLOUT_BG),
            ("BOX",        (0,0), (-1,-1), 0.8, C_ACCENT),
            ("LEFTPADDING",(0,0), (-1,-1), 10),
            ("RIGHTPADDING",(0,0),(-1,-1), 10),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ]))
        flowables.append(KeepTogether([t, Spacer(1, 5*mm)]))

    flowables.append(Spacer(1, 4*mm))
    flowables.append(Paragraph(f"<i>{_safe(data['disclaimer_hi'])}</i>",
                               styles["field_value"]))
    return flowables


def _is_12_block_report(report: Dict) -> bool:
    if report.get("report_template_version") == "12_block_v1":
        return True
    secs = report.get("sections") or []
    return bool(secs) and str(secs[0].get("key") or "").startswith("block_")


def _render_block_section(sec: Dict, styles) -> List:
    """12-block layout: narrative-first, no legacy field dump."""
    flowables: List = []
    key = sec.get("key", "")
    if key == "section_6_feature_analysis":
        return _render_section_6_deep(sec, styles)

    flowables.append(SectionBanner(sec["no"]))
    flowables.append(Spacer(1, 4 * mm))
    flowables.append(Paragraph(_safe(sec["title_hi"]), styles["section_title_hi"]))
    flowables.append(Paragraph(_safe(sec["title_en"]), styles["section_title_en"]))
    goal = (sec.get("goal") or "").strip()
    if goal:
        flowables.append(Paragraph(
            f"<i><font color='#7A7164'>{_safe(goal)}</font></i>",
            styles["field_value"],
        ))

    narr = (sec.get("narrative") or "").strip()
    if narr:
        flowables.append(Spacer(1, 2 * mm))
        flowables.append(Paragraph(_safe(narr), styles["narrative"]))

    content = sec.get("content") or {}
    if isinstance(content, dict):
        fs = content.get("final_scores")
        if isinstance(fs, dict) and fs:
            flowables.append(Spacer(1, 3 * mm))
            flowables.append(Paragraph("<b>Score snapshot</b>", styles["callout_label"]))
            for sk, sv in list(fs.items())[:6]:
                if sv is not None:
                    flowables.append(Paragraph(
                        f"{_safe(str(sk).replace('_', ' ').title())}: {_safe(sv)}",
                        styles["field_value"],
                    ))

    flowables.append(Spacer(1, 8 * mm))
    return flowables


def _render_12_block_pdf(report: Dict, styles, story: List) -> None:
    """Linear 12-block story + appendix tables."""
    sections = report.get("sections") or []
    appendix = report.get("appendix_sections") or []
    engines = report.get("engines") or {}
    synthesis = report.get("synthesis") or {}
    ft2 = report.get("final_truth_v2") or {}

    for sec in sections:
        story.extend(_render_block_section(sec, styles))
        story.append(PageBreak())

    if synthesis.get("shock_insights"):
        story.extend(_render_shock_insights_early(synthesis, styles))
        story.append(PageBreak())

    for sec in appendix:
        story.extend(_render_section(sec, styles))
        story.append(PageBreak())

    if ft2:
        story.extend(_render_final_truth_v2(ft2, styles))
        story.append(PageBreak())

    if engines:
        story.extend(_render_celebrity_page(engines, styles))


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

    photo_bytes = report.get("front_image_bytes")
    points_norm = report.get("front_points_norm") or []
    engines     = report.get("engines") or {}
    sections    = report.get("sections", [])
    sections_dict = {s["key"]: s for s in sections}
    synthesis   = report.get("synthesis") or {}
    hook        = report.get("hook") or {}
    tldr        = report.get("tldr") or {}
    ft2         = report.get("final_truth_v2") or {}
    use_12      = _is_12_block_report(report)
    n_blocks    = report.get("sections_count") or (12 if use_12 else 21)
    cover_meta  = dict(report.get("cover") or {})
    cover_meta["n_blocks"] = n_blocks

    def _render_by_key(key: str):
        sec = sections_dict.get(key)
        if sec:
            story.extend(_render_section(sec, styles))

    # ── Page 1 :: HOOK COVER (identity + shock + scores) ─────────────
    if hook:
        story.extend(_render_hook_cover(hook, cover_meta, styles,
                                        photo_bytes=photo_bytes,
                                        points_norm=points_norm))
    else:
        story.extend(_render_cover(cover_meta, styles,
                                   photo_bytes=photo_bytes,
                                   points_norm=points_norm))
    story.append(PageBreak())

    # ── Page 2 :: TL;DR (value-on-skip) ──────────────────────────────
    if tldr:
        story.extend(_render_tldr_page(tldr, styles))
        story.append(PageBreak())

    # ── Page 3 :: Table of Contents ──────────────────────────────────
    story.extend(_render_toc(report, styles))
    story.append(PageBreak())

    # ── Page 4 :: Annotated face map ─────────────────────────────────
    if photo_bytes and points_norm and len(points_norm) > 200:
        story.extend(_render_face_map_page(photo_bytes, points_norm, styles))
        story.append(PageBreak())

    # ── Page 5 :: Visual snapshot ────────────────────────────────────
    if engines:
        _snap_secs = sections_dict
        if use_12:
            _snap_secs = {
                **sections_dict,
                **{
                    a["key"]: a
                    for a in (report.get("appendix_sections") or [])
                    if a.get("key")
                },
            }
        story.extend(_render_visual_snapshot_page(engines, _snap_secs, styles))
        story.append(PageBreak())

    if use_12:
        _render_12_block_pdf(report, styles, story)
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

    # ── PERSONALITY CORE (sections 1, 2, 7) ──────────────────────────
    for k in ("section_1_power_summary",
              "section_2_psychological_type",
              "section_7_personality_synthesis"):
        _render_by_key(k)

    # ── SHOCK INSIGHTS — early engagement (before deep feature dive) ──
    if synthesis.get("shock_insights"):
        story.append(PageBreak())
        story.extend(_render_shock_insights_early(synthesis, styles))

    # ── FEATURE ANALYSIS (section 6) ─────────────────────────────────
    story.append(PageBreak())
    _render_by_key("section_6_feature_analysis")

    # ── BEHAVIOR PATTERNS (3, 11, 12, 13) ────────────────────────────
    for k in ("section_3_mask_vs_real",
              "section_11_attraction_charisma",
              "section_12_decision_style",
              "section_13_archetype",
              "section_4_first_impression"):
        _render_by_key(k)

    # ── LIFE IMPACT (career, love, life flow, age map) ───────────────
    for k in ("section_8_love_relationship_dna",
              "section_9_career_money",
              "section_14_life_flow",
              "section_15_age_wise_map"):
        _render_by_key(k)

    # ── HEALTH + ENERGY ──────────────────────────────────────────────
    _render_by_key("section_16_health_scan")

    # ── VEDIC INSIGHTS (foundation + moles) ──────────────────────────
    for k in ("section_5_core_foundation",
              "section_17_secret_markings"):
        _render_by_key(k)

    # ── REMEDIES / ACTION (action plan, hacks, compatibility, red flags) ──
    for k in ("section_10_red_flags",
              "section_18_action_plan",
              "section_19_improvement_hacks",
              "section_20_compatibility"):
        _render_by_key(k)

    # ── FINAL SYNTHESIS (climax, shocks already shown earlier) ───────
    if synthesis:
        story.append(PageBreak())
        story.extend(_render_synthesis_pages(synthesis, styles, skip_shocks=True))

    # ── CLOSING TRUTH v2 (3 strengths + 3 risks + 1 direction) ───────
    if ft2:
        story.append(PageBreak())
        story.extend(_render_final_truth_v2(ft2, styles))
    else:
        _render_by_key("section_21_final_truth")

    # ── Bonus personality score ──────────────────────────────────────
    _render_by_key("bonus_personality_score")

    # ── Celebrity match ──────────────────────────────────────────────
    if engines:
        story.append(PageBreak())
        story.extend(_render_celebrity_page(engines, styles))

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

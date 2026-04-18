"""
pdf_renderer.py — Phase 4.5
Render Business Vastu and AstroVastu PRO reports to a PDF binary using
ReportLab. Bilingual (EN + Hi-Latin) layout, brand-safe footer
("Powered by Advanced Cosmic Intelligence" — never AI/LLM).
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


# ─────────────────────────────────────────────────────────────────────
# Brand palette (matches mobile app)
# ─────────────────────────────────────────────────────────────────────
BRAND_PURPLE = colors.HexColor("#7C3AED")
BRAND_GOLD   = colors.HexColor("#F5B700")
TEXT_DARK    = colors.HexColor("#0F172A")
TEXT_MID     = colors.HexColor("#475569")
TEXT_SOFT    = colors.HexColor("#94A3B8")
BG_CARD      = colors.HexColor("#F8FAFC")
BORDER       = colors.HexColor("#E2E8F0")

VERDICT_BG = {
    "Ideal":              colors.HexColor("#D1FAE5"),
    "Acceptable":         colors.HexColor("#DBEAFE"),
    "Adjustment Needed":  colors.HexColor("#FEF3C7"),
    "Avoid":              colors.HexColor("#FEE2E2"),
}
VERDICT_FG = {
    "Ideal":              colors.HexColor("#047857"),
    "Acceptable":         colors.HexColor("#1D4ED8"),
    "Adjustment Needed":  colors.HexColor("#B45309"),
    "Avoid":              colors.HexColor("#B91C1C"),
}
GRADE_COLOR = {
    "A": colors.HexColor("#10B981"),
    "B": colors.HexColor("#3B82F6"),
    "C": colors.HexColor("#F59E0B"),
    "D": colors.HexColor("#EF4444"),
}

# ─────────────────────────────────────────────────────────────────────
def _styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title":  ParagraphStyle("title",  parent=base["Title"],
                                 fontSize=22, leading=26, textColor=BRAND_PURPLE,
                                 alignment=TA_LEFT, spaceAfter=4),
        "sub":    ParagraphStyle("sub",    parent=base["Normal"],
                                 fontSize=11, leading=14, textColor=TEXT_MID,
                                 alignment=TA_LEFT, spaceAfter=10),
        "h2":     ParagraphStyle("h2",     parent=base["Heading2"],
                                 fontSize=14, leading=18, textColor=BRAND_PURPLE,
                                 spaceBefore=10, spaceAfter=4),
        "h3":     ParagraphStyle("h3",     parent=base["Heading3"],
                                 fontSize=12, leading=15, textColor=TEXT_DARK,
                                 spaceBefore=8, spaceAfter=2),
        "body":   ParagraphStyle("body",   parent=base["Normal"],
                                 fontSize=10, leading=13, textColor=TEXT_DARK),
        "bodyHi": ParagraphStyle("bodyHi", parent=base["Normal"],
                                 fontSize=9, leading=12, textColor=TEXT_MID),
        "small":  ParagraphStyle("small",  parent=base["Normal"],
                                 fontSize=8, leading=10, textColor=TEXT_SOFT),
        "footer": ParagraphStyle("footer", parent=base["Normal"],
                                 fontSize=8, leading=10, textColor=TEXT_SOFT,
                                 alignment=TA_CENTER),
        "score":  ParagraphStyle("score",  parent=base["Normal"],
                                 fontSize=42, leading=46, textColor=BRAND_PURPLE,
                                 alignment=TA_CENTER),
        "grade":  ParagraphStyle("grade",  parent=base["Normal"],
                                 fontSize=12, leading=14,
                                 alignment=TA_CENTER, textColor=colors.white),
    }


def _safe(s: Any) -> str:
    """Escape & truncate for ReportLab Paragraph."""
    if s is None:
        return ""
    if isinstance(s, dict):
        # Classical-reference shape: {"type":"vastu","source":"Vastu Saar Ch.9"}
        src  = s.get("source") or s.get("text") or s.get("title") or ""
        kind = s.get("type")   or s.get("category") or ""
        if src and kind:
            s = f"{src} ({kind})"
        else:
            s = src or kind or ""
    elif isinstance(s, (list, tuple)):
        s = ", ".join(_safe(x) for x in s)
    t = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return t


def _on_page(canvas, doc):
    """Draw page header/footer on every page."""
    canvas.saveState()
    w, h = A4
    # Top brand bar
    canvas.setFillColor(BRAND_PURPLE)
    canvas.rect(0, h - 8, w, 8, stroke=0, fill=1)
    # Footer
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(TEXT_SOFT)
    canvas.drawCentredString(w / 2, 12,
                             "Cosmic Lens  ·  Powered by Advanced Cosmic Intelligence  ·  "
                             f"Page {doc.page}")
    canvas.restoreState()


# ─────────────────────────────────────────────────────────────────────
def _score_block(s: ParagraphStyle, score: int, grade: str,
                 summary_en: str, summary_hi: str, label: str) -> Table:
    grade_color = GRADE_COLOR.get(grade, BRAND_PURPLE)
    score_p = Paragraph(f"<b>{score}</b><font size=14 color='#94A3B8'> /100</font>", s["score"])
    grade_p = Paragraph(f"<b>Grade {_safe(grade)}</b>", s["grade"])
    grade_cell = Table([[grade_p]], colWidths=[40 * mm], rowHeights=[18])
    grade_cell.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), grade_color),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    left = Table([[score_p], [grade_cell]], colWidths=[60 * mm])
    left.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    right = Table([
        [Paragraph(f"<b>{_safe(label)}</b>", s["h3"])],
        [Paragraph(_safe(summary_en), s["body"])],
        [Paragraph(_safe(summary_hi), s["bodyHi"])],
    ], colWidths=[110 * mm])
    right.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    outer = Table([[left, right]], colWidths=[60 * mm, 110 * mm])
    outer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return outer


def _counts_row(s: ParagraphStyle, counts: Dict[str, int]) -> Table:
    items = [
        ("Ideal",      counts.get("ideal", 0),             "Ideal"),
        ("Acceptable", counts.get("acceptable", 0),        "Acceptable"),
        ("Adjust",     counts.get("adjustment_needed", 0), "Adjustment Needed"),
        ("Avoid",      counts.get("avoid", 0),             "Avoid"),
    ]
    cells = []
    styles_ = []
    for i, (label, n, k) in enumerate(items):
        cells.append([
            Paragraph(f"<b>{n}</b>", ParagraphStyle("c", parent=s["body"],
                       alignment=TA_CENTER, fontSize=18, leading=20,
                       textColor=VERDICT_FG.get(k, TEXT_DARK))),
            Paragraph(label, ParagraphStyle("cl", parent=s["small"],
                       alignment=TA_CENTER, textColor=VERDICT_FG.get(k, TEXT_MID))),
        ])
        styles_.append(("BACKGROUND", (i, 0), (i, 0), VERDICT_BG.get(k, BG_CARD)))
    # 4 stacked columns: each column is its own mini-table
    pills = []
    col_w = 40 * mm
    for i, c in enumerate(cells):
        t = Table([[c[0]], [c[1]]], colWidths=[col_w])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), VERDICT_BG.get(items[i][2], BG_CARD)),
            ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        pills.append(t)
    row = Table([pills], colWidths=[col_w] * 4)
    row.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    return row


def _section_card(title: str, body_en: str, body_hi: str,
                  s: ParagraphStyle, accent: colors.Color = BRAND_PURPLE) -> Table:
    rows = [[Paragraph(f"<b>{_safe(title)}</b>",
                       ParagraphStyle("ct", parent=s["h3"], textColor=accent))]]
    if body_en:
        rows.append([Paragraph(_safe(body_en), s["body"])])
    if body_hi:
        rows.append([Paragraph(_safe(body_hi), s["bodyHi"])])
    t = Table(rows, colWidths=[170 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
        ("LINEABOVE", (0, 0), (-1, 0), 2, accent),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _priority_table(actions: List[Dict[str, Any]], s: ParagraphStyle) -> Table:
    if not actions:
        return Paragraph("No priority actions — your premise is well-aligned.", s["body"])
    head = ["#", "Room · Direction", "Verdict", "Why (EN / Hi)"]
    data = [head]
    for i, p in enumerate(actions, 1):
        verdict = p.get("verdict", "Acceptable")
        crit = " ★" if p.get("is_critical") else ""
        room_dir = (p.get("room_type", "") or "").replace("_", " ").title() + crit + \
                   "\n" + (p.get("direction", "") or "")
        why_en = p.get("why_en") or p.get("why") or ""
        why_hi = p.get("why_hi") or ""
        why = (why_en + ("\n" + why_hi if why_hi else "")).strip()
        data.append([
            str(i),
            Paragraph(_safe(room_dir).replace("\n", "<br/>"), s["body"]),
            Paragraph(_safe(verdict), ParagraphStyle("v", parent=s["body"],
                       textColor=VERDICT_FG.get(verdict, TEXT_DARK), fontSize=9)),
            Paragraph(_safe(why).replace("\n", "<br/>"), s["body"]),
        ])
    t = Table(data, colWidths=[10 * mm, 40 * mm, 30 * mm, 90 * mm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for r, p in enumerate(actions, 1):
        v = p.get("verdict", "Acceptable")
        bg = VERDICT_BG.get(v, BG_CARD)
        style.append(("BACKGROUND", (2, r), (2, r), bg))
    t.setStyle(TableStyle(style))
    return t


def _vision_block(report: Dict[str, Any], s: Dict[str, ParagraphStyle]) -> List[Any]:
    """Render the optional 'Cosmic Vision Findings' section."""
    out: List[Any] = []
    vfp = report.get("vision_floor_plan") or {}
    vrf = report.get("vision_room_findings") or {}
    used = bool(vfp) or bool(vrf.get("rooms_analyzed", 0))
    if not used:
        return out

    out.append(Paragraph("Cosmic Vision Findings", s["h2"]))
    bits: List[str] = []
    if vfp:
        if vfp.get("plot_shape"):
            bits.append(f"Plot shape: <b>{_safe(vfp['plot_shape'])}</b>")
        if vfp.get("main_entrance"):
            bits.append(f"Main entrance: <b>{_safe(vfp['main_entrance'])}</b>")
        rooms_full = vfp.get("rooms_full") or vfp.get("rooms") or []
        if rooms_full:
            bits.append(f"Rooms auto-detected: <b>{len(rooms_full)}</b>")
        conf = vfp.get("confidence")
        if isinstance(conf, int):
            bits.append(f"Detection confidence: <b>{conf}/100</b>")
    if vrf.get("rooms_analyzed"):
        bits.append(f"Room photos analyzed: <b>{vrf['rooms_analyzed']}</b>")
        if vrf.get("applied_score_delta"):
            sd = vrf["applied_score_delta"]
            sign = "+" if sd > 0 else ""
            bits.append(f"Visual score adjustment: <b>{sign}{sd}</b>")
    if bits:
        out.append(Paragraph("  ·  ".join(bits), s["body"]))
        out.append(Spacer(1, 4))

    notes = list(vfp.get("structural_notes") or [])
    if notes:
        out.append(Paragraph("<b>Structural notes from your floor plan:</b>", s["body"]))
        for n in notes[:8]:
            out.append(Paragraph(f"• {_safe(n)}", s["body"]))
        out.append(Spacer(1, 4))

    if vfp.get("scan_inconclusive") and vfp.get("inconclusive_reason"):
        out.append(Paragraph(
            f"<i>Note:</i> {_safe(vfp['inconclusive_reason'])}", s["body"]
        ))
    out.append(Spacer(1, 8))
    return out


def _signature_block(s: Dict[str, ParagraphStyle]) -> List[Any]:
    """Authorized signature: script-style 'sign' + typed name + brand line."""
    out: List[Any] = [Spacer(1, 18)]
    rule = Table([[""]], colWidths=[55 * mm], rowHeights=[0.6])
    rule.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 0.6, BORDER)]))

    label_st = ParagraphStyle("sig_label", parent=s["body"], fontSize=8,
                              textColor=TEXT_SOFT, leading=10, spaceAfter=2)
    sign_st  = ParagraphStyle("sig_script", parent=s["body"],
                              fontName="Helvetica-BoldOblique",
                              fontSize=22, leading=24,
                              textColor=BRAND_PURPLE, spaceAfter=2)
    name_st  = ParagraphStyle("sig_name", parent=s["body"], fontSize=10,
                              fontName="Helvetica-Bold", textColor=TEXT_DARK,
                              leading=12, spaceAfter=1)
    brand_st = ParagraphStyle("sig_brand", parent=s["body"], fontSize=9,
                              textColor=TEXT_SOFT, leading=11)

    cell = [
        Paragraph("Authorized by", label_st),
        Paragraph("<i>Ashutosh Bharadwaj</i>", sign_st),
        rule,
        Paragraph("Ashutosh Bharadwaj", name_st),
        Paragraph("Cosmic Lens · Founder", brand_st),
        Paragraph(f"Digitally signed · {datetime.utcnow().strftime('%d %b %Y')}",
                  ParagraphStyle("sig_date", parent=s["body"], fontSize=7,
                                 textColor=TEXT_SOFT, leading=9)),
    ]
    holder = Table([[cell]], colWidths=[170 * mm], hAlign="RIGHT")
    holder.setStyle(TableStyle([
        ("ALIGN",  (0, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    out.append(holder)
    return out


def _disclosure_block(s: Dict[str, ParagraphStyle], *,
                      is_business: bool = False) -> List[Any]:
    """
    Brand-safe 'What this report does NOT include' section.
    Sets clear expectations so users don't interpret a Vastu/Astro report
    as legal, medical, financial, structural-engineering or guaranteed advice.
    """
    out: List[Any] = []
    out.append(Spacer(1, 10))
    out.append(Paragraph("What this report does NOT include", s["h2"]))
    items_en = [
        "Structural / civil engineering certification — consult a licensed engineer for any construction decision.",
        "Legal, medical, financial or tax advice of any kind.",
        "A guarantee of business profit, marriage outcome, health, or specific life events — Vastu and astrology offer guidance, not certainty.",
        "Approval or compliance with local building codes, RERA norms or municipal regulations.",
        "Replacement for a personal consultation with a qualified Vastu acharya or jyotishi for major life decisions.",
        "Demolition, structural alteration or expensive renovation recommendations — prefer the low-cost remedies listed above first.",
    ]
    if is_business:
        items_en.append(
            "Business strategy, accounting or workforce decisions — these remain the owner's responsibility."
        )
    items_hi = [
        "Structural / civil engineering certification — kisi bhi nirman kary se pehle licensed engineer se salaah lein.",
        "Kisi bhi prakar ki kanooni, medical, financial ya tax salaah.",
        "Vyapar laabh, vivah, swasthya ya jeevan ki ghatnaon ki guarantee nahin — Vastu aur Jyotish margdarshan dete hain, nishchay nahin.",
        "Sthaniya building code, RERA niyam ya municipal niyamon ki anumati nahin.",
        "Bade jeevan nirnayon ke liye yogya Vastu acharya ya jyotishi ki vyaktigat salaah ka vikalp nahin.",
        "Tod-phod ya mahanga renovation suggest nahin karte — pehle upar diye gaye saral upayon ko apnayein.",
    ]
    if is_business:
        items_hi.append(
            "Vyaparik strategy, accounting ya karmchari nirnay vyapari ke apne hain."
        )
    for en, hi in zip(items_en, items_hi):
        out.append(Paragraph(f"• {_safe(en)}", s["body"]))
        out.append(Paragraph(f"<i>{_safe(hi)}</i>", s["body"]))
    out.append(Spacer(1, 4))
    out.append(Paragraph(
        "<i>This report is generated for guidance and self-improvement only. "
        "Cosmic Lens and its team accept no liability for decisions taken on the "
        "basis of this report. By using this report you acknowledge these limits.</i>",
        s["body"]
    ))
    return out


def _rooms_table(rooms: List[Dict[str, Any]], s: ParagraphStyle,
                 with_business: bool) -> Table:
    head = ["Room", "Dir", "Verdict", "Score", "Notes"]
    data = [head]
    for r in rooms:
        notes = []
        if r.get("zone", {}).get("deity"):
            z = r["zone"]
            notes.append(f"Zone: {z.get('planet','')} · {z.get('deity','')} · {z.get('element','')}")
        if with_business and r.get("business_rule", {}).get("applies"):
            br = r["business_rule"]
            if br.get("reason_en"):
                notes.append("Biz: " + br["reason_en"])
        if r.get("mahadasha", {}).get("applies"):
            md = r["mahadasha"]
            if md.get("reason_en"):
                notes.append("Mahadasha: " + md["reason_en"])
        vfs = r.get("visual_findings") or []
        if vfs:
            for vf in vfs[:3]:
                txt = (vf.get("text") or "").strip()
                sev = (vf.get("severity") or "").strip()
                if txt:
                    notes.append(f"Vision ({sev}): {txt}")
        notes_str = "<br/>".join(_safe(n) for n in notes) or "—"
        verdict = r.get("verdict", "Acceptable")
        crit = " ★" if r.get("is_critical") else ""
        data.append([
            Paragraph(_safe((r.get("room_type", "") or "").replace("_", " ").title() + crit), s["body"]),
            _safe(r.get("direction", "")),
            Paragraph(_safe(verdict), ParagraphStyle("v", parent=s["body"],
                       textColor=VERDICT_FG.get(verdict, TEXT_DARK), fontSize=9)),
            str(r.get("score", "—")),
            Paragraph(notes_str, s["body"]),
        ])
    t = Table(data, colWidths=[40 * mm, 14 * mm, 28 * mm, 14 * mm, 74 * mm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, r in enumerate(rooms, 1):
        bg = VERDICT_BG.get(r.get("verdict", "Acceptable"), colors.white)
        style.append(("BACKGROUND", (2, i), (2, i), bg))
    t.setStyle(TableStyle(style))
    return t


# ─────────────────────────────────────────────────────────────────────
# Universal Vastu Remedies Appendix
# Strong classical remedies for when structural shift is not possible.
# Categorised so user finds the right remedy fast.
# ─────────────────────────────────────────────────────────────────────
_UNIVERSAL_REMEDIES: List[Dict[str, Any]] = [
    {
        "title": "Kitchen in wrong direction (N / NE / SW)",
        "ref":   "Vastu Saar Ch.7, Brihat Samhita 53.62",
        "items": [
            "Paste a 4-inch wide YELLOW electrical tape strip on the wall behind the gas stove, floor-to-ceiling — neutralises the wrong-direction Agni dosh.",
            "Place a small COPPER pyramid (3-inch base) on top of the chimney hood; copper amplifies Agni in the right axis.",
            "Always cook FACING EAST — even if the platform is on the wrong wall, the cook's body posture matters most.",
            "Keep a small bowl of ROCK SALT in the SE corner of the kitchen; replace every Saturday.",
            "Hang a SUNRISE painting on the east kitchen wall; do NOT hang any water-element art (waterfall, river) inside kitchen.",
        ],
    },
    {
        "title": "Bathroom / WC in wrong direction (NE / centre / pooja-adjacent)",
        "ref":   "Mansara Shilpa Shastra Ch.9, Vastu Saar",
        "items": [
            "Paste a thick YELLOW tape line on the bathroom door frame (outer side, all 4 sides) — blocks negative energy leak into the home.",
            "Keep a sea-salt bowl inside the bathroom on the floor; replace every 3 days.",
            "Always keep the bathroom door CLOSED when not in use; install a slow self-closer if family forgets.",
            "Place a small mirror on the OUTER side of the bathroom door (facing away from pooja / bedroom) — deflects the dosh outward.",
            "Plant a money-plant in a copper pot inside the bathroom — absorbs the negative water energy.",
            "If WC faces N or E: paint the WC seat lid a deep brown / maroon and always keep it closed.",
        ],
    },
    {
        "title": "Pooja room in wrong direction (S / SW / above bathroom)",
        "ref":   "Brihat Samhita 53.86, Vastu Saar Ch.10",
        "items": [
            "Place a small PYRAMID (clear quartz or copper) under the idol platform — uplifts the energy axis to NE virtually.",
            "Light a desi-ghee diya facing EAST every morning — re-establishes the Brahmasthan link.",
            "Hang a Shree Yantra on the east wall of the pooja space, framed in copper.",
            "Never store anything BELOW the idol platform; keep that area clean & open.",
            "Place a small flowing-water fountain in the actual NE corner of the home (even outside the pooja room) — relays the energy.",
        ],
    },
    {
        "title": "Master bedroom in wrong direction (NE / SE)",
        "ref":   "Vastu Saar Ch.6, Mayamatam Ch.27",
        "items": [
            "Sleep with HEAD pointing SOUTH or EAST only — the body alignment overrides room dosh significantly.",
            "Place a heavy wooden / metal almirah in the SW corner of the bedroom — anchors the heavy zone.",
            "Avoid mirrors facing the bed; if unavoidable, cover with cloth at night.",
            "Hang a pair of love-birds / family photo on the SW wall.",
            "Use earthy tones (beige, light brown, soft pink) for bedroom walls — never bright red or pure white.",
        ],
    },
    {
        "title": "Entrance / main door in wrong direction (S / SW / Vidisha axis)",
        "ref":   "Vastu Saar Ch.4, Brihat Samhita 53.71",
        "items": [
            "Hang a copper Shubh-Labh + Swastik plate on top of the door frame, INSIDE the house.",
            "Place a pair of brass / copper Kuber yantras on either side of the door frame (inside).",
            "Paste a Hanuman-ji tile or sticker on the OUTSIDE of the main door — blocks negative entry.",
            "Never place a shoe rack directly opposite the main door; shift it sideways.",
            "Keep the threshold (dehleez) raised by 1-2 inches with a small wooden / marble strip — classical 'energy speed-breaker'.",
            "Hang a wind-chime (5 or 6 metal rods) just inside the entrance — activates positive vibration.",
        ],
    },
    {
        "title": "Beam over bed / sofa / desk (Tula dosh)",
        "ref":   "Mansara Ch.18",
        "items": [
            "Hang a pair of bamboo flutes (mouth-down) at 45° on the beam — classical Tula-dosh nivaran.",
            "Paint the beam the SAME colour as the ceiling so it visually disappears.",
            "Suspend a false ceiling panel directly under the beam if budget allows.",
            "Avoid sleeping / sitting / working DIRECTLY under the beam — shift the bed / chair by 1-2 feet.",
        ],
    },
    {
        "title": "Mirror facing bed / main door / dining",
        "ref":   "Vastu Saar Ch.11",
        "items": [
            "Cover the mirror with a thin cloth at night, OR shift it to a wall that does NOT reflect bed / door / dining.",
            "If mirror faces main door: it bounces incoming Lakshmi out — relocate or hang a Bagua mirror just outside the door instead.",
            "Always use single-piece mirrors; broken / multi-panel mirrors create Maya dosh.",
        ],
    },
    {
        "title": "Toilet above kitchen / pooja / bedroom (multi-floor)",
        "ref":   "Vastu Saar Ch.9",
        "items": [
            "Paint the toilet floor (the one above) a light yellow shade.",
            "Place a copper sheet (6-inch square) under the WC base.",
            "Hang a Shree Yantra in the room directly below — neutralises the descending negative axis.",
            "Always use the lower-floor room for limited duration (kitchen — short cooking, pooja — short worship).",
        ],
    },
    {
        "title": "Plot / topography dosh (slope wrong, water-tank wrong)",
        "ref":   "Brihat Samhita 53.86–88",
        "items": [
            "Underground water tank MUST be in NE; if it's elsewhere, install a small symbolic copper bowl with water in the actual NE corner daily.",
            "Overhead tank MUST be in SW; if it's in NE/SE, paint it dark blue and add weight (extra concrete cap) to the SW corner of the terrace.",
            "Plot slope should fall toward NE. If it falls SW (Vipreet Vastu): raise the SW boundary by 6-12 inches with extra soil / planters.",
            "Plant TALL heavy trees (neem, mango) in S / SW; light flowering plants only in N / NE.",
        ],
    },
    {
        "title": "Universal everyday remedies (works for almost any dosh)",
        "ref":   "Atharvaveda + classical texts",
        "items": [
            "Burn camphor (kapoor) + loban once a week in every room — purifies stagnant energy.",
            "Sprinkle sea-salt water in all room corners on Saturday evening; mop with rock-salt water on Sundays.",
            "Keep fresh flowers in the NE corner of the living room, replaced every 2 days.",
            "Play Vedic mantras (Gayatri, Mahamrityunjaya) softly for 10 minutes at sunrise.",
            "Avoid clutter under beds, on top of cupboards, behind doors — clutter is the #1 Vastu blocker.",
            "Fix leaking taps and broken items within 7 days — water leaks = wealth leaks (classical).",
        ],
    },
]


def _universal_remedies_block(s: Dict[str, ParagraphStyle]) -> List[Any]:
    """Appendix: classical strong remedies for when structural shift isn't possible."""
    flow: List[Any] = []
    flow.append(PageBreak())
    flow.append(Paragraph("Universal Vastu Remedies (Appendix)", s["h2"]))
    flow.append(Paragraph(
        "<i>When a kitchen, bathroom, pooja, or entrance cannot be physically shifted, "
        "these classical remedies — drawn from Vastu Saar, Brihat Samhita, Mansara Shilpa "
        "Shastra and Mayamatam — neutralise a large portion of the dosh. Apply only those "
        "that match a finding flagged in your report above.</i>",
        s["body"]))
    flow.append(Spacer(1, 8))

    for cat in _UNIVERSAL_REMEDIES:
        flow.append(Paragraph(_safe(cat["title"]), s["h3"]))
        flow.append(Paragraph(
            f"<font color='#7C3AED'>Reference:</font> <i>{_safe(cat['ref'])}</i>",
            s["small"]))
        for item in cat["items"]:
            flow.append(Paragraph(f"• {_safe(item)}", s["body"]))
        flow.append(Spacer(1, 6))

    flow.append(Spacer(1, 4))
    flow.append(Paragraph(
        "<i>Note: Remedies are most effective when combined with daily worship, "
        "cleanliness, and positive intent. Re-scan your premise after applying remedies "
        "for an updated score.</i>",
        s["bodyHi"]))
    flow.append(Spacer(1, 8))
    return flow


# ─────────────────────────────────────────────────────────────────────
# PUBLIC: Business Vastu PDF
# ─────────────────────────────────────────────────────────────────────
def render_business_pdf(report: Dict[str, Any], *,
                        property_name: str = "",
                        user_name: str = "") -> bytes:
    """Render a Business Vastu deep-scan report into a PDF byte string."""
    s = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=22 * mm, bottomMargin=18 * mm,
                            title="Business Vastu Report — Cosmic Lens",
                            author="Cosmic Lens")
    flow: List[Any] = []

    biz = report.get("business_summary", {}) or {}
    biz_type = (biz.get("type") or "Business").title()
    intro = biz.get("intro") or {}

    # ── Header
    flow.append(Paragraph(f"Business Vastu — {_safe(biz_type)}", s["title"]))
    sub = []
    if property_name:
        sub.append(f"Premise: <b>{_safe(property_name)}</b>")
    if user_name:
        sub.append(f"Owner: <b>{_safe(user_name)}</b>")
    sub.append(f"Issued: {datetime.utcnow().strftime('%d %b %Y')}")
    flow.append(Paragraph("  ·  ".join(sub), s["sub"]))

    # ── Score block
    overall = report.get("overall", {}) or {}
    summary = overall.get("summary", {}) or {}
    flow.append(_score_block(s,
                             int(overall.get("score", 0)),
                             overall.get("grade", "C"),
                             summary.get("en", ""),
                             summary.get("hi", ""),
                             "Overall Premise Score"))
    flow.append(Spacer(1, 8))

    # ── Counts row
    flow.append(_counts_row(s, overall.get("counts", {}) or {}))
    flow.append(Spacer(1, 10))

    # ── Business intro
    if intro.get("en") or intro.get("hi"):
        flow.append(_section_card(f"{biz_type} Vastu Brief",
                                  intro.get("en", ""),
                                  intro.get("hi", ""), s))
        flow.append(Spacer(1, 6))

    # ── Mahadasha alert
    md = report.get("mahadasha_alert")
    if md:
        title = f"Owner Mahadasha · {md.get('active_lord','-')} ({md.get('lord_direction','-')})"
        flow.append(_section_card(title,
                                  md.get("summary_en", ""),
                                  md.get("summary_hi", ""), s,
                                  accent=VERDICT_FG["Adjustment Needed"]))
        flow.append(Spacer(1, 6))

    # ── Stakeholder synergy
    stk = report.get("stakeholder")
    if stk and (stk.get("partner_count", 0) or 0) > 0:
        flow.append(_section_card("Stakeholder Synergy",
                                  stk.get("summary_en", ""),
                                  stk.get("summary_hi", ""), s,
                                  accent=VERDICT_FG["Acceptable"]))
        flow.append(Spacer(1, 6))

    # ── Muhurat alignment
    mh = report.get("muhurat") or {}
    if mh.get("applies"):
        flow.append(_section_card(f"Muhurat Alignment · {(mh.get('alignment') or '').upper()}",
                                  mh.get("summary_en", ""),
                                  mh.get("summary_hi", ""), s))
        flow.append(Spacer(1, 6))

    # ── Priority Actions
    flow.append(Paragraph("Priority Actions", s["h2"]))
    flow.append(_priority_table(report.get("priority_actions") or [], s))
    flow.append(Spacer(1, 10))

    # ── Cosmic Vision Findings (Phase 6, optional)
    flow.extend(_vision_block(report, s))

    # ── Room-by-room
    rooms = report.get("rooms") or []
    if rooms:
        flow.append(PageBreak())
        flow.append(Paragraph("Room-by-room Analysis", s["h2"]))
        flow.append(_rooms_table(rooms, s, with_business=True))
        flow.append(Spacer(1, 10))

    # ── Classical refs
    refs = report.get("classical_summary") or []
    if refs:
        flow.append(Paragraph("Classical References", s["h2"]))
        for r in refs:
            flow.append(Paragraph(f"• {_safe(r)}", s["body"]))
        flow.append(Spacer(1, 6))

    # ── Universal Vastu Remedies appendix (always shown — strong remedies
    #    when structural shift isn't possible)
    flow.extend(_universal_remedies_block(s))

    # ── Scope disclosure (what this report is NOT)
    flow.extend(_disclosure_block(s, is_business=True))

    # ── Footer
    _ft = report.get("footer")
    if isinstance(_ft, dict):
        foot = _ft.get("en") or "Powered by Advanced Cosmic Intelligence"
    elif isinstance(_ft, str) and _ft.strip():
        foot = _ft
    else:
        foot = "Powered by Advanced Cosmic Intelligence"
    flow.append(Spacer(1, 14))
    flow.append(Paragraph(_safe(foot), s["footer"]))

    doc.build(flow, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────
# PUBLIC: AstroVastu PRO PDF (residential)
# ─────────────────────────────────────────────────────────────────────
def render_pro_pdf(report: Dict[str, Any], *,
                   property_name: str = "",
                   user_name: str = "") -> bytes:
    """Render an AstroVastu PRO (residential) report into a PDF byte string."""
    s = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=22 * mm, bottomMargin=18 * mm,
                            title="AstroVastu PRO Report — Cosmic Lens",
                            author="Cosmic Lens")
    flow: List[Any] = []

    flow.append(Paragraph("AstroVastu PRO Report", s["title"]))
    sub = []
    if property_name:
        sub.append(f"Property: <b>{_safe(property_name)}</b>")
    if user_name:
        sub.append(f"Owner: <b>{_safe(user_name)}</b>")
    sub.append(f"Issued: {datetime.utcnow().strftime('%d %b %Y')}")
    flow.append(Paragraph("  ·  ".join(sub), s["sub"]))

    overall = report.get("overall", {}) or {}
    summary = overall.get("summary", {}) or {}
    flow.append(_score_block(s,
                             int(overall.get("score", 0)),
                             overall.get("grade", "C"),
                             summary.get("en", ""),
                             summary.get("hi", ""),
                             "Overall Property Score"))
    flow.append(Spacer(1, 8))
    flow.append(_counts_row(s, overall.get("counts", {}) or {}))
    flow.append(Spacer(1, 10))

    ks = report.get("kundli_summary") or {}
    if ks:
        bits = []
        if ks.get("lagna"):     bits.append(f"Lagna: <b>{_safe(ks['lagna'])}</b>")
        if ks.get("mahadasha"): bits.append(f"Mahadasha: <b>{_safe(ks['mahadasha'])}</b>")
        if ks.get("sade_sati"): bits.append("Sade Sati: <b>active</b>")
        if bits:
            flow.append(_section_card("Owner Kundli Snapshot",
                                      "  ·  ".join(bits), "", s))
            flow.append(Spacer(1, 6))

    md = report.get("mahadasha_alert")
    if md:
        title = f"Active Mahadasha · {md.get('active_lord','-')} ({md.get('lord_direction','-')})"
        flow.append(_section_card(title,
                                  md.get("summary_en", ""),
                                  md.get("summary_hi", ""), s,
                                  accent=VERDICT_FG["Adjustment Needed"]))
        flow.append(Spacer(1, 6))

    flow.append(Paragraph("Priority Actions", s["h2"]))
    flow.append(_priority_table(report.get("priority_actions") or [], s))
    flow.append(Spacer(1, 10))

    # ── Cosmic Vision Findings (Phase 6, optional)
    flow.extend(_vision_block(report, s))

    rooms = report.get("rooms") or []
    if rooms:
        flow.append(PageBreak())
        flow.append(Paragraph("Room-by-room Analysis", s["h2"]))
        flow.append(_rooms_table(rooms, s, with_business=False))
        flow.append(Spacer(1, 10))

    refs = report.get("classical_summary") or []
    if refs:
        flow.append(Paragraph("Classical References", s["h2"]))
        for r in refs:
            flow.append(Paragraph(f"• {_safe(r)}", s["body"]))

    # ── Universal Vastu Remedies appendix (always shown — strong remedies
    #    when structural shift isn't possible)
    flow.extend(_universal_remedies_block(s))

    # ── Scope disclosure (what this report is NOT)
    flow.extend(_disclosure_block(s, is_business=False))

    # ── Authorized signature block ──────────────────────────────────────
    flow.extend(_signature_block(s))

    _ft = report.get("footer")
    if isinstance(_ft, dict):
        foot = _ft.get("en") or "Powered by Advanced Cosmic Intelligence"
    elif isinstance(_ft, str) and _ft.strip():
        foot = _ft
    else:
        foot = "Powered by Advanced Cosmic Intelligence"
    flow.append(Spacer(1, 14))
    flow.append(Paragraph(_safe(foot), s["footer"]))

    doc.build(flow, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()

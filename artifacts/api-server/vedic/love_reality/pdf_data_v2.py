"""
Love Reality Pro PDF v2 — structured 14-page data from engine bundle + kundli.
Deterministic chart facts; optional GPT chapter bodies merged at render time.
"""
from __future__ import annotations

from typing import Any

from jaimini import compute_arudha_padas, compute_upapada
from vedic.love_reality.scoring_core import KundliReader, SIGNS

SIGN_ELEMENT = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
}

DIMENSION_LABELS = [
    ("emotional", "Emotional Bond"),
    ("attraction", "Attraction"),
    ("communication", "Communication"),
    ("karmic", "Karmic Link"),
    ("stability", "Stability"),
]


def _chapter_body(pro: dict, key: str) -> str:
    for ch in pro.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        if (ch.get("key") or "").strip().lower() == key:
            return (
                (ch.get("chapter_body") or ch.get("full_read") or "").strip()
            )
    return ""


def _moon_sign_idx(k: dict) -> int | None:
    ms = k.get("moonSign") or k.get("rashi")
    if not ms:
        moon = next((p for p in (k.get("planets") or []) if p.get("name") == "Moon"), None)
        ms = moon.get("sign") if moon else None
    try:
        return SIGNS.index(str(ms))
    except (ValueError, TypeError):
        return None


def _shashtashtak(m1: int | None, m2: int | None) -> bool:
    if m1 is None or m2 is None:
        return False
    d = abs(m1 - m2) % 12
    return d in (5, 7)  # 6th or 8th sign distance


def _partner_blueprint(k_raw: dict, label: str) -> dict[str, Any]:
    k = KundliReader(k_raw)
    h7l = k.house_lord(7)
    p7l = k.planet(h7l)
    ven = k.planet("Venus")
    jup = k.planet("Jupiter")
    merc = k.planet("Mercury")
    occ12 = k.occupants(12)
    arudha = compute_arudha_padas(k_raw.get("planets") or [], k_raw.get("ascendant"))
    ul = compute_upapada(arudha, k_raw.get("planets") or []) if arudha else {}
    lines = [
        f"{label}: Lagna {k_raw.get('ascendant') or '?'}, Moon {k_raw.get('moonSign') or '?'}",
        f"7th house lord {h7l}: {p7l.get('sign') if p7l else '?'} "
        f"(house {p7l.get('house') if p7l else '?'})",
        f"Venus: {ven.get('sign') if ven else '?'} house {ven.get('house') if ven else '?'}",
        f"Jupiter: {jup.get('sign') if jup else '?'} house {jup.get('house') if jup else '?'}",
    ]
    if ul:
        lines.append(
            f"Upapada Lagna (UL): {ul.get('ul_sign')} — lord {ul.get('ul_lord')} "
            f"({ul.get('verdict', 'MIXED')} marriage signature)"
        )
    if occ12:
        lines.append(f"12th house occupants (hidden desires): {', '.join(occ12)}")
    if merc:
        lines.append(
            f"Mercury (communication): {merc.get('sign')} house {merc.get('house')}"
        )
    element = SIGN_ELEMENT.get(str(k_raw.get("moonSign") or ""), "Mixed")
    return {
        "lines": lines,
        "element": element,
        "ul_verdict": ul.get("verdict") if ul else None,
    }


def _score_row(label: str, val: int | None, band: str = "") -> dict[str, str]:
    return {
        "label": label,
        "value": str(val) if val is not None else "—",
        "band": band or "",
    }


def _build_remedies(bundle: dict, pro: dict) -> list[str]:
    out: list[str] = []
    k1 = bundle.get("kundli_p1") or {}
    k2 = bundle.get("kundli_p2") or {}
    r1, r2 = KundliReader(k1), KundliReader(k2)
    for r, name in ((r1, "You"), (r2, "Partner")):
        if r.planet("Venus") and r.dignity("Venus", r.sidx(r.planet("Venus")["sign"])) == -2:
            out.append(f"{name}: Venus debilitated — Friday white-flowers / Lakshmi mantra; avoid harsh speech on Fridays.")
        if r.planet("Moon") and r.dignity("Moon", r.sidx(r.planet("Moon")["sign"])) == -2:
            out.append(f"{name}: Moon debilitated — Monday milk donation; sleep before 10:30 PM on Mondays.")
        if r.occupants(7) and "Saturn" in r.occupants(7):
            out.append(f"{name}: Saturn on 7th — Saturday sesame oil lamp; patience rituals, no ultimatums on Saturdays.")
        if r.occupants(7) and "Mars" in r.occupants(7):
            out.append(f"{name}: Mars on 7th — Tuesday Hanuman chalisa; cool-down before replying in anger.")
    if not out:
        out.append(
            "Joint: Name friction early — one partner initiates repair within 24 hours after any argument."
        )
    return out[:6]


def build_love_reality_pdf_v2_context(
    bundle: dict,
    pro: dict,
    p1: dict,
    p2: dict,
    lang: str = "en",
) -> dict[str, Any]:
    """All page payloads for the 14-page Love Reality Pro layout."""
    lc = bundle.get("love_compatibility") or {}
    bu = bundle.get("breakup_chances") or {}
    ly = bundle.get("loyalty_check") or {}
    wr = bundle.get("will_return") or {}
    fo = bundle.get("future_outcome") or {}
    rf = bundle.get("hidden_red_flags") or {}

    love = int(lc.get("score") or 0)
    breakup = int(bu.get("breakup_score") or bu.get("score") or 0)
    loyalty = int(ly.get("loyalty_score") or ly.get("score") or 0)
    ret = int(wr.get("return_probability") or wr.get("score") or 0)
    future = int(fo.get("future_score") or fo.get("score") or 0)

    dims = (lc.get("breakdown") or {})
    k1 = bundle.get("kundli_p1") or {}
    k2 = bundle.get("kundli_p2") or {}
    m1, m2 = _moon_sign_idx(k1), _moon_sign_idx(k2)
    shash = _shashtashtak(m1, m2)

    p1_bp = _partner_blueprint(k1, p1.get("name") or "You")
    p2_bp = _partner_blueprint(k2, p2.get("name") or "Partner")

    blueprint_p1 = "\n".join(p1_bp["lines"])
    blueprint_p2 = "\n".join(p2_bp["lines"])
    blueprint_compare = (
        f"Destiny blueprint (your chart) vs reality (partner nature):\n\n"
        f"YOUR IDEAL PARTNER SIGNATURE\n{blueprint_p1}\n\n"
        f"PARTNER ACTUAL SIGNATURE\n{blueprint_p2}\n\n"
        f"Element mix: You {p1_bp['element']} · Partner {p2_bp['element']}\n"
        f"Love score {love}/100 validates how closely reality matches the blueprint."
    )
    love_narr = (
        str(pro.get("blueprint_reality") or "").strip()
        or _chapter_body(pro, "love_connection")
        or ""
    )
    if not love_narr or len(love_narr.split()) < 40:
        love_narr = lc.get("emotional_summary") or love_narr

    breakup_narr = _chapter_body(pro, "breakup") or ""
    loyalty_narr = _chapter_body(pro, "loyalty") or ""
    root_parts: list[str] = []
    if breakup_narr:
        root_parts.append(breakup_narr)
    if not root_parts:
        if bu.get("reasons"):
            root_parts.extend(str(r) for r in (bu.get("reasons") or [])[:3])
        if ly.get("reasons"):
            root_parts.extend(str(r) for r in (ly.get("reasons") or [])[:2])
        occ12 = KundliReader(k1).occupants(12) or KundliReader(k2).occupants(12)
        if occ12:
            root_parts.append(f"Hidden desire axis (12th house): {', '.join(set(occ12))} pressure.")
        merc1 = KundliReader(k1).planet("Mercury")
        merc2 = KundliReader(k2).planet("Mercury")
        if merc1 and merc2 and merc1.get("sign") != merc2.get("sign"):
            root_parts.append(
                f"Mercury mismatch — {merc1.get('sign')} vs {merc2.get('sign')}: communication style clash."
            )
    root_cause = "\n\n".join(p for p in root_parts if p) or bu.get("emotional_summary") or ""

    harmony = str(pro.get("harmony") or "").strip()
    if not harmony:
        harmony = _chapter_body(pro, "will_return") or _chapter_body(pro, "future_outcome")
    if not harmony:
        harmony = (
            f"You ({p1_bp['element']}) need emotional pacing; partner ({p2_bp['element']}) "
            f"needs different recharge rhythms. Name stress within 12 hours; "
            f"do not let silence exceed 48 hours during dasha-down windows."
        )

    dasha_lines: list[str] = []
    for side, kraw, nm in (("You", k1, p1.get("name")), ("Partner", k2, p2.get("name"))):
        cd = kraw.get("currentDasha") or {}
        maha, antar = cd.get("maha"), cd.get("antar")
        start, end = cd.get("startDate"), cd.get("endDate")
        if maha:
            line = f"{nm or side}: MD {maha}"
            if antar:
                line += f" · AD {antar}"
            if start and end:
                line += f" ({start} → {end})"
            dasha_lines.append(line)
    if fo.get("next_shift"):
        dasha_lines.append(f"Couple outlook: {fo.get('next_shift')}")

    timeline = fo.get("timeline_flow") or []
    t3 = timeline[1] if len(timeline) > 1 else {}
    roadmap = [
        {
            "period": "Next 3 months",
            "trend": t3.get("trend") or "mixed",
            "note": t3.get("reason") or fo.get("emotional_summary") or "",
        },
        {"period": "Next 12 months", "trend": fo.get("outcome") or "mixed",
         "note": fo.get("current_phase") or ""},
        {"period": "Next 36 months", "trend": wr.get("return_chance") or "mixed",
         "note": wr.get("time_window") or fo.get("outcome") or ""},
    ]

    flags = list(rf.get("reasons") or [])[:8]
    if not flags:
        flags = ["Monitor unspoken resentment — chart shows friction under stress."]
    red_flags_narr = (
        str(pro.get("red_flags_narrative") or "").strip()
        or _chapter_body(pro, "red_flags")
        or ""
    )

    loyalty_rows = []
    pp = ly.get("per_person") or {}
    if pp:
        for side in ("p1", "p2"):
            row = pp.get(side) or {}
            loyalty_rows.append(_score_row(
                row.get("name") or side.upper(),
                int(row.get("score") or 0),
                str(row.get("level") or ""),
            ))
    else:
        loyalty_rows.append(_score_row("Couple loyalty", loyalty, ly.get("risk_level") or ""))

    practical = [str(p).strip() for p in (pro.get("practical") or []) if str(p).strip()]
    remedies_body = practical[0] if practical else ""
    checklist_body = practical[1] if len(practical) > 1 else ""

    checklist = [
        "After any fight: repair within 24 hours — chart shows delay stacks resentment.",
        "No major decisions during Mercury retrograde on communication themes.",
        "Weekly 20-minute check-in without phones — loyalty scores drop when silence grows.",
        "Name the hidden fear (ego / jealousy / distance) once per month — 12th-house pressure.",
        "Track dasha window dates above — avoid ultimatums during AD down-trend.",
    ]
    for item in practical[2:]:
        checklist.append(str(item).strip())

    closing = (pro.get("verdict") or "").strip() or bundle.get("narrative_bridge") or (
        f"Love {love}/100 · Breakup risk {breakup}/100 · Future {future}/100 — "
        "use this report as a timing map, not a verdict of doom."
    )

    return {
        "page1_dashboard": {
            "scores": [
                _score_row("Love Compatibility", love, lc.get("risk_level") or ""),
                _score_row("Breakup Risk", breakup, bu.get("risk_level") or ""),
                _score_row("Loyalty", loyalty, ly.get("risk_level") or ""),
                _score_row("Return Probability", ret, wr.get("return_chance") or ""),
                _score_row("Future Outlook", future, fo.get("risk_level") or ""),
            ],
            "summary_index": lc.get("emotional_summary") or "",
            "love_score": love,
        },
        "page2_3_blueprint": {
            "part1": blueprint_compare,
            "part2": love_narr or blueprint_p2,
        },
        "page4_dimensions": [
            {"label": lbl, "score": int(dims.get(key) or 0), "key": key}
            for key, lbl in DIMENSION_LABELS
        ],
        "page5_moon": {
            "shashtashtak": shash,
            "p1_moon": k1.get("moonSign") or "?",
            "p2_moon": k2.get("moonSign") or "?",
            "body": (
                "Shashtashtak (6-8 sign Moon clash) detected — emotional rhythm out of sync."
                if shash
                else "Moon signs support smoother emotional rhythm — still watch stress triggers."
            ),
            "notes": (lc.get("reasons") or [])[:4],
        },
        "page6_root_cause": root_cause,
        "page7_loyalty": {
            "rows": loyalty_rows,
            "body": loyalty_narr or ly.get("emotional_summary") or "",
            "summary": ly.get("emotional_summary") or "",
            "behavior": ly.get("behavior_type") or "",
        },
        "page8_red_flags": {
            "body": red_flags_narr,
            "bullets": flags,
        },
        "page9_harmony": harmony,
        "page10_dasha": {
            "body": str(pro.get("dasha_narrative") or "").strip(),
            "lines": dasha_lines,
        },
        "page11_roadmap": {
            "body": str(pro.get("roadmap_narrative") or "").strip(),
            "rows": roadmap,
        },
        "page12_remedies": {
            "body": remedies_body,
            "bullets": _build_remedies(bundle, pro),
        },
        "page13_checklist": {
            "body": checklist_body,
            "bullets": checklist[:7],
        },
        "page14_closing": closing,
    }

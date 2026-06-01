"""
Deterministic chart snapshot + score ledger for Love Reality Pro PDF.
No LLM — printed facts anchor the narrative chapters.
"""
from __future__ import annotations

from typing import Any

from vedic.love_reality.scoring_core import KundliReader


def _fmt_deg(p: dict | None) -> str:
    if not p:
        return "—"
    d = p.get("degrees") or p.get("degree")
    if d:
        return str(d)
    lon = p.get("longitude")
    if lon is not None:
        return f"{float(lon):.2f}°"
    return "—"


def _planet_line(k: KundliReader, name: str, *, d9: bool = False) -> str | None:
    p = k.d9(name) if d9 else k.planet(name)
    if not p:
        return None
    sign = p.get("sign") or "?"
    house = p.get("house")
    deg = _fmt_deg(p)
    tag = "D9 " if d9 else ""
    dign = k.dignity(name, k.sidx(sign)) if not d9 else k.dignity(
        name, int(p.get("signIndex", k.sidx(str(sign))))
    )
    dw = k.dignity_word(dign)
    htxt = f", house {house}" if house else ""
    return f"{tag}{name}: {sign} {deg}{htxt} ({dw})"


def _dasha_block(k: KundliReader) -> list[str]:
    cd = k.k.get("currentDasha") or {}
    maha = cd.get("maha")
    antar = cd.get("antar")
    praty = cd.get("pratyantar")
    start = cd.get("startDate") or (k.k.get("currentPhase") or {}).get("start")
    end = cd.get("endDate") or (k.k.get("currentPhase") or {}).get("end")
    lines: list[str] = []
    if maha:
        lines.append(f"Vimshottari MD: {maha}")
    if antar:
        lines.append(f"Antardasha (AD): {antar}")
    if praty:
        lines.append(f"Pratyantar (PD): {praty}")
    if start and end:
        lines.append(f"AD window: {start} → {end}")
    elif start:
        lines.append(f"AD from: {start}")
    return lines


def _aspects_line(k: KundliReader, target: str) -> str | None:
    hits = k.aspects_planet(target)
    if not hits:
        return None
    return f"{target} aspected by: {', '.join(hits)}"


def build_person_chart_lines(k_raw: dict, label: str) -> list[str]:
    k = KundliReader(k_raw)
    lines = [f"── {label}: {k.name} ──"]
    asc = k_raw.get("ascendant") or "?"
    lines.append(f"Ascendant (Lagna): {asc}")
    nk = k_raw.get("nakshatra") or "?"
    pada = k_raw.get("nakshatraPada")
    pada_s = f", pada {pada}" if pada else ""
    lines.append(f"Moon nakshatra: {nk}{pada_s} · Rashi {k_raw.get('moonSign') or '?'}")
    for pl in ("Moon", "Venus"):
        ln = _planet_line(k, pl)
        if ln:
            lines.append(ln)
    h7l = k.house_lord(7)
    p7l = k.planet(h7l)
    if p7l:
        si = k.sidx(p7l["sign"])
        lines.append(
            f"7th lord {h7l}: {p7l['sign']} house {p7l.get('house')} "
            f"({_fmt_deg(p7l)}, {k.dignity_word(k.dignity(h7l, si))})"
        )
    occ7 = k.occupants(7)
    if occ7:
        lines.append(f"Planets in 7th house: {', '.join(occ7)}")
    asp7 = k.aspects_house(7)
    if asp7:
        lines.append(f"Aspects on 7th bhava: {', '.join(asp7)}")
    v9 = _planet_line(k, "Venus", d9=True)
    if v9:
        lines.append(v9)
    masp = _aspects_line(k, "Venus")
    if masp:
        lines.append(masp)
    lines.extend(_dasha_block(k))
    return lines


def build_chart_snapshot(bundle: dict) -> dict[str, Any]:
    """Full appendix payload for PDF."""
    k1 = bundle.get("kundli_p1") or {}
    k2 = bundle.get("kundli_p2") or {}
    p1 = bundle.get("p1") or {}
    p2 = bundle.get("p2") or {}
    lines: list[str] = []
    if k1:
        lines.extend(build_person_chart_lines(k1, p1.get("name") or "Partner A"))
        lines.append("")
    if k2:
        lines.extend(build_person_chart_lines(k2, p2.get("name") or "Partner B"))
    sig = bundle.get("couple_signals") or {}
    syn = sig.get("synastry_notes") or []
    if syn:
        lines.append("── Couple synastry ──")
        for n in syn[:6]:
            lines.append(f"• {n}")
    lc = bundle.get("love_compatibility") or {}
    aff = (lc.get("breakdown") or {}).get("combined_affliction")
    if aff is not None:
        lines.append(f"Combined affliction index: {aff} (chart-weighted)")
    lines.append("Calculations: Swiss Ephemeris, Lahiri ayanamsa, whole-sign houses.")
    return {"lines": lines, "title_key": "chart_snapshot"}


def build_chapter_groundings(bundle: dict) -> dict[str, str]:
    """Engine-written chart bridges when LLM grounding is empty."""
    mapping = {
        "love_connection": ("love_compatibility", "score", "reasons"),
        "breakup": ("breakup_chances", "breakup_score", "reasons"),
        "loyalty": ("loyalty_check", "loyalty_score", "reasons"),
        "will_return": ("will_return", "return_probability", "reasons"),
        "future_outcome": ("future_outcome", "future_score", "reasons"),
        "red_flags": ("hidden_red_flags", "score", "reasons"),
    }
    out: dict[str, str] = {}
    for key, (eng_key, score_key, reasons_key) in mapping.items():
        eng = bundle.get(eng_key) or {}
        sc = eng.get(score_key) or eng.get("score")
        reasons = eng.get(reasons_key) or eng.get("emotional_summary") or ""
        if isinstance(reasons, list):
            top = "; ".join(str(r) for r in reasons[:3])
        else:
            top = str(reasons)
        if sc is not None:
            out[key] = f"Chart score {sc}/100. Basis: {top[:420]}".strip()
        elif top:
            out[key] = f"Chart basis: {top[:480]}".strip()
    return out


def build_narrative_bridge(bundle: dict, lang: str = "en") -> str:
    """Reconcile breakup vs future scores for verdict / consistency."""
    bu = bundle.get("breakup_chances") or {}
    fo = bundle.get("future_outcome") or {}
    lc = bundle.get("love_compatibility") or {}
    b_sc = int(bu.get("breakup_score") or bu.get("score") or 0)
    f_sc = int(fo.get("future_score") or fo.get("score") or 0)
    l_sc = int(lc.get("score") or 0)
    hn = lang in ("hn", "hi")

    parts: list[str] = []
    if b_sc >= 55 and f_sc >= 55:
        if hn:
            parts.append(
                "Breakup pressure chart par active hai (medium–high risk), lekin future score "
                "bhi supportive dikhta hai — yeh contradiction nahi, timing split hai: "
                "pehle friction / near-break window, baad mein repair ya reconnection yogas "
                "agar dono consciously kaam karein."
            )
        else:
            parts.append(
                "Breakup pressure reads active on the chart (medium–high risk), while the future "
                "score is also supportive — this is a timing split, not a contradiction: "
                "friction or near-break windows can precede a repair phase if both partners "
                "engage honestly."
            )
    elif b_sc >= 55 and f_sc < 42:
        if hn:
            parts.append(
                "Breakup aur future dono charts par strain dikhate hain — long-term stability "
                "abhi weak hai; clarity dena fantasy se behtar hai."
            )
        else:
            parts.append(
                "Both breakup pressure and long-term outlook show strain — stability is not "
                "assured without major pattern change."
            )
    elif l_sc < 45 and f_sc >= 58:
        if hn:
            parts.append(
                f"Overall love score {l_sc}/100 neeche hai, lekin future window mixed-positive "
                "hai — attachment zyada hai, peace kam; aage ka phase effort par depend karega."
            )
        else:
            parts.append(
                f"Overall love score is {l_sc}/100 (attachment-heavy), while the future window "
                "leans mixed-positive — growth depends on effort, not autopilot harmony."
            )
    else:
        if hn:
            parts.append(
                f"Love score {l_sc}/100, breakup risk band {b_sc}/100, future outlook {f_sc}/100 — "
                "har chapter apne chart-score par focused hai; overall story in teen readings se banti hai."
            )
        else:
            parts.append(
                f"Love {l_sc}/100, breakup-risk band {b_sc}/100, future outlook {f_sc}/100 — "
                "each chapter reflects its own chart score band within one overall story."
            )
    return " ".join(parts)


def enrich_bundle_for_pdf(bundle: dict) -> dict:
    """Attach chart_snapshot, groundings, narrative_bridge (mutates copy-safe)."""
    out = dict(bundle)
    out["chart_snapshot"] = build_chart_snapshot(out)
    out["chapter_groundings"] = build_chapter_groundings(out)
    out["narrative_bridge"] = build_narrative_bridge(
        out, lang=str((out.get("reader_context") or {}).get("pdf_lang") or "en")
    )
    return out

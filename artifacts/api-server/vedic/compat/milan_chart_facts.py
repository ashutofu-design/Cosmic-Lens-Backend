"""
Deterministic chart snapshot + Ashtakoot ledger for Kundli Milan Pro PDF.
"""
from __future__ import annotations

from typing import Any

from vedic.love_reality.chart_facts import build_person_chart_lines

# PDF chapter key → chapter_scores engine key
PDF_CHAPTER_TO_SCORE_KEY: dict[str, str] = {
    "emotional_compatibility": "ch1",
    "trust_loyalty": "ch2",
    "communication_conflict": "ch3",
    "marriage_stability": "ch4",
    "physical_chemistry": "ch5",
    "family_practical": "ch6",
    "future_direction": "ch7",
}


def build_ashtakoot_ledger(milan: dict) -> list[dict[str, Any]]:
    """Line-by-line guna milan breakdown for PDF score page."""
    koots = milan.get("koots") or []
    mx = int(milan.get("max") or 36)
    ledger: list[dict[str, Any]] = [
        {
            "label": "Ashtakoot (8 koots)",
            "base": 0,
            "note": "Each koot adds gunas toward the headline total",
        },
    ]
    running = 0
    for k in koots:
        if not isinstance(k, dict):
            continue
        sc = k.get("score")
        kmax = k.get("max")
        label = str(k.get("label") or k.get("key") or "Koot").strip()
        try:
            sc_i = int(sc) if sc is not None else 0
        except (TypeError, ValueError):
            sc_i = 0
        running += sc_i
        note = f"contributes {sc_i} guna"
        if kmax is not None:
            note += f" (max {kmax})"
        ledger.append({"label": label, "delta": sc_i, "note": note})
    total = milan.get("total")
    try:
        total_i = int(total) if total is not None else running
    except (TypeError, ValueError):
        total_i = running
    ledger.append({
        "label": "Guna milan total",
        "delta": None,
        "base": total_i,
        "note": f"{total_i} out of {mx} — headline compatibility on the cover",
    })
    return ledger


def build_chart_snapshot(bundle: dict) -> dict[str, Any]:
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
    d9 = bundle.get("d9_marriage") or {}
    sync = d9.get("sync") or {}
    if sync.get("score_0_10") is not None:
        lines.append(f"D9 lagna-lord sync: {sync.get('score_0_10')}/10")
    syn = bundle.get("synastry_7l") or {}
    nr = (syn.get("nakshatra_resonance") or {}).get("count")
    if nr is not None:
        lines.append(f"Nakshatra-lord resonance matches: {nr}")
    kp = bundle.get("kp_couple_promise") or {}
    kv = kp.get("verdict") or kp.get("couple_verdict")
    if kv:
        lines.append(f"KP marriage promise: {kv}")
    total = bundle.get("total")
    mx = bundle.get("max", 36)
    if total is not None:
        lines.append(f"Ashtakoot total: {total} / {mx}")
    lines.append("Calculations: Swiss Ephemeris, Lahiri ayanamsa, whole-sign houses.")
    return {"lines": lines}


def build_chapter_groundings(bundle: dict) -> dict[str, str]:
    cs = bundle.get("chapter_scores") or {}
    chs = cs.get("chapters") if isinstance(cs.get("chapters"), dict) else {}
    out: dict[str, str] = {}
    for pdf_key, ch_key in PDF_CHAPTER_TO_SCORE_KEY.items():
        ch = chs.get(ch_key) or {}
        score = ch.get("score_0_10")
        drivers = ch.get("drivers") or []
        cautions = ch.get("cautions") or []
        parts = [str(x) for x in (drivers[:2] + cautions[:2]) if x]
        top = "; ".join(parts)
        if score is not None:
            line = f"Chapter score {score}/10. Chart basis: {top[:420]}".strip()
        elif top:
            line = f"Chart basis: {top[:480]}".strip()
        else:
            continue
        out[pdf_key] = line
    return out


def build_narrative_bridge(bundle: dict, lang: str = "en") -> str:
    total = int(bundle.get("total") or 0)
    mx = int(bundle.get("max") or 36)
    pct = (total / mx * 100) if mx else 0
    kp = bundle.get("kp_couple_promise") or {}
    kp_v = str(kp.get("verdict") or kp.get("couple_verdict") or "").upper()
    cs = bundle.get("chapter_scores") or {}
    chs = cs.get("chapters") if isinstance(cs.get("chapters"), dict) else {}
    ch4 = (chs.get("ch4") or {}).get("score_0_10")
    ch7 = (chs.get("ch7") or {}).get("score_0_10")
    hn = lang in ("hn", "hi")

    parts: list[str] = []
    if pct >= 65 and kp_v == "WEAK":
        if hn:
            parts.append(
                f"Ashtakoot {total}/{mx} ({round(pct)}%) upar se achha dikhta hai, lekin KP marriage promise "
                "WEAK hai — yeh contradiction nahi: guna milan surface harmony batata hai, "
                "KP 7th cusp chain commitment depth alag measure karti hai."
            )
        else:
            parts.append(
                f"Ashtakoot reads {total}/{mx} ({round(pct)}%) — supportive on the surface — while KP "
                "marriage promise is WEAK. That is a timing-and-commitment split, not a mistake: "
                "guna milan and KP measure different layers of the bond."
            )
    elif pct < 50 and ch7 is not None and float(ch7) >= 7:
        if hn:
            parts.append(
                f"Guna milan {total}/{mx} neeche hai lekin long-term chapter score supportive hai — "
                "short-term friction aur long-term direction alag chapters me padhte hain."
            )
        else:
            parts.append(
                f"Guna milan is modest ({total}/{mx}) while the long-term chapter score is stronger — "
                "near-term friction and later direction are read on separate chart layers."
            )
    elif ch4 is not None and float(ch4) < 4.5 and pct >= 55:
        if hn:
            parts.append(
                f"Overall milan {total}/{mx} theek hai par marriage stability chapter neeche hai — "
                "daily warmth ke baad bhi structural patience test ho sakti hai."
            )
        else:
            parts.append(
                f"Overall milan {total}/{mx} is fair, but marriage stability scores lower — "
                "warmth can show while structural patience is still tested over years."
            )
    else:
        if hn:
            parts.append(
                f"Guna milan {total}/{mx}; har chapter apne chart-score par focused hai — "
                "ek hi headline sab kuch explain nahi karta."
            )
        else:
            parts.append(
                f"Guna milan {total}/{mx}; each chapter reflects its own chart score — "
                "one headline does not explain every layer of the bond."
            )
    return " ".join(parts)


def enrich_milan_bundle_for_pdf(bundle: dict, lang: str = "en") -> dict:
    out = dict(bundle)
    out["ashtakoot_ledger"] = build_ashtakoot_ledger(out)
    out["chart_snapshot"] = build_chart_snapshot(out)
    out["chapter_groundings"] = build_chapter_groundings(out)
    out["narrative_bridge"] = build_narrative_bridge(out, lang=lang)
    return out

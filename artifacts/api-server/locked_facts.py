"""
locked_facts.py
───────────────
Assembles ALL deterministic chart facts into ONE clean structured block that
the AI is forced to MIRROR (never invent counts/names).

Pulls from:
  • chart_intelligence.analyze_chart   → lagna, dignities, house lords,
                                          yogas, mangal-dosh, sade-sati
  • dosh_engine.analyze_doshas         → 9-dosh status + counts
  • shadbala.compute_shadbala          → planet strength % (when computable)
  • planet_strength.verdict_table      → STRONG/MODERATE/WEAK band

Single entry point:
    build_locked_facts(kundli, birth=None) -> str

Returns "" if not enough data.  Never raises.
"""

from __future__ import annotations
from typing import Any, Optional


def _safe(call):
    try:
        return call()
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] {call.__name__ if hasattr(call,'__name__') else 'op'} failed: {exc}")
        return None


def _normalise_planets_for_dosh(kundli: dict) -> list:
    """dosh_engine expects {name, house, longitude, sign, retrograde}."""
    out = []
    for p in (kundli.get("planets") or []):
        if not isinstance(p, dict):
            continue
        out.append({
            "name":       p.get("name"),
            "house":      p.get("house"),
            "longitude":  p.get("longitude"),
            "sign":       p.get("sign"),
            "retrograde": bool(p.get("retrograde")),
        })
    return out


def _normalise_planets_for_shadbala(kundli: dict) -> list:
    """compute_shadbala expects {name, lon, house, retrograde}."""
    out = []
    for p in (kundli.get("planets") or []):
        if not isinstance(p, dict):
            continue
        out.append({
            "name":       p.get("name"),
            "lon":        p.get("longitude"),
            "house":      p.get("house"),
            "retrograde": bool(p.get("retrograde")),
        })
    return out


def _lagna_sign_idx(kundli: dict, intel: dict) -> Optional[int]:
    SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
             "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    name = intel.get("lagna_sign") or kundli.get("ascendant") or kundli.get("lagna")
    if isinstance(name, str):
        try:
            return SIGNS.index(name)
        except ValueError:
            pass
    ad = kundli.get("ascendantDeg") or kundli.get("ascendant_lon")
    if isinstance(ad, (int, float)):
        return int(ad % 360 / 30)
    return None


def _format_yoga_block(yogas: list) -> str:
    if not yogas:
        return "▸ YOGA COUNT: 0\n▸ YOGA LIST: (none of the major classical yogas detected)"
    lines = [f"▸ YOGA COUNT: {len(yogas)}", "▸ YOGA LIST:"]
    for i, y in enumerate(yogas, 1):
        # yoga strings already include short interpretation in chart_intelligence
        lines.append(f"   {i}. {y}")
    return "\n".join(lines)


def _format_dosh_block(dosh: dict) -> str:
    if not isinstance(dosh, dict):
        return "▸ DOSHA DATA: (unavailable)"
    actives = [d for d in dosh.get("dosh_list", []) if d.get("status") == "Active"]
    milds   = [d for d in dosh.get("dosh_list", []) if d.get("status") == "Mild"]
    lines = [
        f"▸ DOSHA COUNT (Active): {len(actives)}",
        f"▸ DOSHA COUNT (Mild):   {len(milds)}",
        f"▸ DOSHA COUNT (None):   {dosh.get('none_count', 0)}",
    ]
    if actives:
        lines.append("▸ ACTIVE DOSHAS:")
        for i, d in enumerate(actives, 1):
            lines.append(f"   {i}. {d.get('name','?')} — {d.get('headline','')}")
    if milds:
        lines.append("▸ MILD DOSHAS:")
        for i, d in enumerate(milds, 1):
            lines.append(f"   {i}. {d.get('name','?')} — {d.get('headline','')}")
    if not actives and not milds:
        lines.append("▸ ACTIVE DOSHAS: (none — chart is dosha-free)")
    return "\n".join(lines)


def _format_strength_block(verdicts: dict, dignities: list) -> str:
    """Tabular planet strength block."""
    if not verdicts:
        return "▸ PLANET STRENGTHS: (unavailable)"
    # Build dignity lookup for sign/house annotations
    sign_house = {row["planet"]: (row.get("sign","?"), row.get("house","?"))
                  for row in (dignities or []) if isinstance(row, dict) and row.get("planet")}
    lines = ["▸ PLANET STRENGTHS:"]
    order = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]
    for p in order:
        v = verdicts.get(p)
        if not v:
            continue
        sign, house = sign_house.get(p, ("?","?"))
        lines.append(f"   {p:<8} {v['verdict']:<8} ({sign} H{house} — {v['reason']})")
    return "\n".join(lines)


def _format_dasha_block(kundli: dict) -> str:
    cd = kundli.get("currentDasha") or {}
    if not isinstance(cd, dict) or not cd:
        return "▸ CURRENT DASHA: (unavailable)"
    md  = cd.get("maha") or cd.get("mahadasha") or cd.get("md") or cd.get("planet")
    ad  = cd.get("antar") or cd.get("antardasha") or cd.get("ad")
    pd_ = cd.get("pratyantar") or cd.get("pd")
    start = cd.get("startDate") or cd.get("start")
    end   = cd.get("endDate") or cd.get("end")
    parts = []
    if md: parts.append(f"{md} Mahadasha")
    if ad: parts.append(f"→ {ad} Antardasha")
    if pd_: parts.append(f"→ {pd_} Pratyantar")
    line = " ".join(parts) if parts else "(unavailable)"
    extra = ""
    if start or end:
        extra = f"\n▸ DASHA WINDOW: {start or '?'} to {end or '?'}"
    return f"▸ CURRENT DASHA: {line}{extra}"


def _format_house_lords(intel: dict) -> str:
    hl = intel.get("house_lords") or []
    if not hl:
        return ""
    items = []
    for h in hl:
        if h.get("lord_in_house"):
            items.append(f"H{h['house']}({h['sign']})→{h['lord']} sits H{h['lord_in_house']}")
        else:
            items.append(f"H{h['house']}({h['sign']})→{h['lord']}")
    return "▸ HOUSE-LORD PLACEMENTS:\n   " + "; ".join(items)


def _format_basics(kundli: dict, intel: dict) -> str:
    parts = []
    if intel.get("lagna_sign"):
        parts.append(f"▸ LAGNA: {intel['lagna_sign']}")
    moon_sign = kundli.get("moonSign") or kundli.get("moon_sign")
    if moon_sign:
        parts.append(f"▸ MOON SIGN (Rashi): {moon_sign}")
    sun_sign = kundli.get("sunSign")
    if sun_sign:
        parts.append(f"▸ SUN SIGN: {sun_sign}")
    nak = kundli.get("nakshatra")
    if nak:
        pada = kundli.get("nakshatraPada")
        line = f"▸ NAKSHATRA: {nak}" + (f" (Pada {pada})" if pada else "")
        parts.append(line)
    if intel.get("sade_sati"):
        parts.append(f"▸ SADE-SATI: {intel['sade_sati']}")
    return "\n".join(parts)


def build_locked_facts(kundli: Any, birth: Any = None) -> str:
    """Assemble the LOCKED FACTS block. Returns "" if kundli is empty."""
    if not isinstance(kundli, dict) or not kundli.get("planets"):
        return ""

    # Lazy imports to avoid circular dependencies and keep test paths light
    try:
        from chart_intelligence import analyze_chart  # type: ignore
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] import chart_intelligence failed: {exc}")
        return ""

    intel = analyze_chart(kundli, birth) or {}
    if not intel:
        return ""

    # Doshas (9-dosh engine)
    dosh = None
    try:
        from dosh_engine import analyze_doshas  # type: ignore
        dosh = analyze_doshas(_normalise_planets_for_dosh(kundli),
                              kundli.get("nakshatra") or "")
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] dosh_engine failed: {exc}")

    # Shadbala (best-effort — needs lagna + lon)
    shadbala = None
    try:
        from shadbala import compute_shadbala  # type: ignore
        lagna_idx = _lagna_sign_idx(kundli, intel)
        if lagna_idx is not None:
            shadbala = compute_shadbala(_normalise_planets_for_shadbala(kundli),
                                        lagna_sign=lagna_idx)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] shadbala failed: {exc}")

    # Planet strength verdicts (uses shadbala if present, else fallback)
    verdicts = {}
    try:
        from planet_strength import verdict_table  # type: ignore
        verdicts = verdict_table(intel.get("dignities") or [], shadbala)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] planet_strength failed: {exc}")

    # Assemble
    sections = [
        "═════════ LOCKED FACTS — MIRROR EXACTLY, NEVER INVENT ═════════",
        _format_basics(kundli, intel),
        _format_yoga_block(intel.get("yogas") or []),
        _format_dosh_block(dosh) if dosh else f"▸ MANGAL-DOSH: {intel.get('mangal_dosh','(unavailable)')}",
        _format_strength_block(verdicts, intel.get("dignities") or []),
        _format_dasha_block(kundli),
        _format_house_lords(intel),
        "════════════════════════════════════════════════════════════════",
    ]
    # Drop empty sections (e.g. no house lords)
    return "\n\n".join(s for s in sections if s and s.strip())

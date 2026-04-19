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


# ── Yoga polarity classifier ────────────────────────────────────────────────
# Tags each detected yoga as POSITIVE / NEGATIVE / NEUTRAL so the AI never
# mistakes a misery-yoga (e.g. Kemadruma) for a "blessing yoga". Matched by
# substring on the yoga name. Extend lists as new detectors are added.
_NEGATIVE_YOGA_KEYWORDS = (
    "Kemadruma", "Daridra", "Shakata", "Visha yoga", "Visha-yoga",
    "Punarphoo", "Kala Sarpa", "Kalasarpa", "Kaal Sarp", "Kaal-Sarp",
    "Guru-Chandala", "Guru Chandal", "Angarak", "Pisach",
)
_NEUTRAL_YOGA_KEYWORDS = (
    "Vipareeta",  # adversity-converts — context-dependent, mark neutral
)


def _yoga_polarity(name: str) -> str:
    s = (name or "")
    if any(k.lower() in s.lower() for k in _NEGATIVE_YOGA_KEYWORDS):
        return "NEGATIVE"
    if any(k.lower() in s.lower() for k in _NEUTRAL_YOGA_KEYWORDS):
        return "NEUTRAL"
    return "POSITIVE"


_POLARITY_TAG = {"POSITIVE": "[+ POSITIVE]", "NEGATIVE": "[− NEGATIVE]", "NEUTRAL": "[~ NEUTRAL]"}


def _format_yoga_block(yogas: list) -> str:
    if not yogas:
        return ("▸ YOGA COUNT: 0\n"
                "▸ POSITIVE YOGAS: 0   NEGATIVE: 0   NEUTRAL: 0\n"
                "▸ YOGA LIST: (none of the major classical yogas detected)")
    pos = neg = neu = 0
    rows = []
    for y in yogas:
        pol = _yoga_polarity(y)
        if pol == "POSITIVE":   pos += 1
        elif pol == "NEGATIVE": neg += 1
        else:                   neu += 1
        rows.append((pol, y))
    # Clean (raw) name = yoga string up to "(" or " yoga" — used for safe
    # name-listing in user-facing replies (Rule B). Polarity tags are for
    # AI internal reasoning ONLY and must never be echoed to the user.
    def _clean(y: str) -> str:
        s = y.split("(")[0].strip()
        return s if s else y
    raw_names = [_clean(y) for _, y in rows]
    lines = [
        f"▸ YOGA COUNT: {len(yogas)}",
        f"▸ POSITIVE YOGAS: {pos}   NEGATIVE: {neg}   NEUTRAL: {neu}",
        f"▸ YOGA NAMES (raw, USE THESE for any 'kaunse yog' answer — NEVER include the [+/−/~] tags below): {', '.join(raw_names)}",
        "▸ YOGA LIST (with polarity tags — POSITIVE=blessing, NEGATIVE=struggle, NEUTRAL=context-dependent. Tags are FOR YOUR REASONING ONLY, do NOT echo to user):",
    ]
    for i, (pol, y) in enumerate(rows, 1):
        lines.append(f"   {i}. {_POLARITY_TAG[pol]} {y}")
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

    # Sprint-2 — Ashtakavarga (Sarvashtakavarga per house)
    av_str = ""
    try:
        from ashtakavarga import compute_ashtakavarga, format_sav_summary  # type: ignore
        lagna_idx = _lagna_sign_idx(kundli, intel)
        # Need sign_idx per planet — use dignity rows
        SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                      "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
        av_planets = []
        for p in (kundli.get("planets") or []):
            if not isinstance(p, dict):
                continue
            sn = p.get("sign")
            si = p.get("sign_idx")
            if si is None and isinstance(sn, str) and sn in SIGN_NAMES:
                si = SIGN_NAMES.index(sn)
            av_planets.append({"name": p.get("name"), "sign_idx": si})
        if lagna_idx is not None:
            av = compute_ashtakavarga(av_planets, lagna_idx)
            av_str = format_sav_summary(av) if av else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] ashtakavarga failed: {exc}")

    # Sprint-2 — Aspects (Graha Drishti)
    asp_str = ""
    asp_obj = None
    try:
        from aspects import compute_aspects, format_aspect_summary  # type: ignore
        asp_obj = compute_aspects(kundli.get("planets") or [], _lagna_sign_idx(kundli, intel))
        asp_str = format_aspect_summary(asp_obj) if asp_obj else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] aspects failed: {exc}")

    # Sprint-3 — Bhava Bala (house strength composite)
    bb_str = ""
    try:
        from bhava_bala import compute_bhava_bala, format_bhava_bala_summary  # type: ignore
        bb = compute_bhava_bala(intel, verdicts, asp_obj)
        bb_str = format_bhava_bala_summary(bb) if bb else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] bhava_bala failed: {exc}")

    # Sprint-3 — Jaimini Karakas
    kk_str = ""
    try:
        from karakas import compute_karakas, format_karakas_summary  # type: ignore
        kk = compute_karakas(kundli.get("planets") or [])
        kk_str = format_karakas_summary(kk) if kk else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] karakas failed: {exc}")

    # Sprint-4 — D9 / D10 divisional charts
    div_str = ""
    try:
        from divisional_charts import compute_d9, compute_d10, format_divisional_summary  # type: ignore
        # Lagna longitude — best effort: try kundli.lagna.longitude or intel
        lagna_lon = None
        lg = kundli.get("lagna") or kundli.get("ascendant")
        if isinstance(lg, dict):
            lagna_lon = lg.get("longitude") or lg.get("lon")
        d9  = compute_d9(kundli.get("planets") or [], lagna_lon)
        d10 = compute_d10(kundli.get("planets") or [], lagna_lon)
        div_str = format_divisional_summary(d9, d10, intel)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] divisional_charts failed: {exc}")

    # Sprint-7 — Jaimini Arudha Padas (A1-A12) + Upapada Lagna (UL)
    jm_str = ""
    try:
        from jaimini import (compute_arudha_padas, compute_upapada,  # type: ignore
                             format_jaimini_summary)
        lagna_sign = kundli.get("ascendant")
        if isinstance(lagna_sign, dict):
            lagna_sign = lagna_sign.get("sign") or lagna_sign.get("name")
        ar = compute_arudha_padas(kundli.get("planets") or [], lagna_sign)
        ul = compute_upapada(ar, kundli.get("planets") or []) if ar else {}
        jm_str = format_jaimini_summary(ar, ul) if ar else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] jaimini failed: {exc}")

    # Sprint-4 — Pratyantar dasha (sub-period under current AD)
    pd_str = ""
    try:
        from pratyantar import compute_pratyantar, format_pratyantar_summary  # type: ignore
        pd = compute_pratyantar(kundli.get("currentDasha") or {})
        pd_str = format_pratyantar_summary(pd) if pd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] pratyantar failed: {exc}")

    # Sprint-6 — KP Cuspal Sub-Lord cross-check (best-effort — needs lat/lon/tz)
    kp_str = ""
    try:
        from kp_locked_facts import compute_kp_summary, format_kp_summary  # type: ignore
        kp_sum = compute_kp_summary(birth, kundli)
        kp_str = format_kp_summary(kp_sum) if kp_sum else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] kp cross-check failed: {exc}")

    # Sprint-5 — Remedies (deterministic, classical) — built BEFORE transits
    # so it can use verdicts/dosh/topic that are already available.
    rem_str = ""
    try:
        from remedies import select_remedies, format_remedies_summary  # type: ignore
        active_doshas = []
        if isinstance(dosh, dict):
            for d in dosh.get("dosh_list", []):
                if d.get("status") in ("Active", "Mild"):
                    active_doshas.append(d.get("name") or "")
        # sade-sati flag from intel if engines added it
        if intel.get("sade_sati_active"):
            active_doshas.append("Sade-Sati")
        topic = (kundli.get("_topic") or "").lower()  # may be set by caller
        # verdicts is {planet: {verdict, reason, score}} — unwrap to {planet: "WEAK"|...}
        verdict_strs = {p: (v.get("verdict") if isinstance(v, dict) else v)
                        for p, v in (verdicts or {}).items()}
        rem = select_remedies(verdict_strs, kundli.get("currentDasha") or {},
                              active_doshas, intel, topic,
                              planet_scores=verdicts)
        rem_str = format_remedies_summary(rem)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] remedies failed: {exc}")

    # Sprint-3 — Transits (Saturn / Jupiter / Rahu vs natal)
    tr_str = ""
    try:
        from transits import compute_transits, format_transit_summary  # type: ignore
        from datetime import datetime
        SIGN_NAMES_TR = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
        moon_sign_str = kundli.get("moonSign") or kundli.get("moon_sign")
        moon_sign_idx = SIGN_NAMES_TR.index(moon_sign_str) if moon_sign_str in SIGN_NAMES_TR else None
        lagna_for_tr = _lagna_sign_idx(kundli, intel)
        # DOB extraction (best-effort) — supports multiple shapes
        dob_dt = None
        if isinstance(birth, dict):
            dob_str = birth.get("date") or birth.get("dob") or birth.get("birthDate")
            if isinstance(dob_str, str) and len(dob_str) >= 10:
                try:
                    dob_dt = datetime.strptime(dob_str[:10], "%Y-%m-%d")
                except Exception:
                    dob_dt = None
            # Sprint-8: also accept {day, month, year, hour, minute} shape
            if dob_dt is None and all(k in birth for k in ("day", "month", "year")):
                try:
                    dob_dt = datetime(
                        int(birth["year"]), int(birth["month"]), int(birth["day"]),
                        int(birth.get("hour") or 0), int(birth.get("minute") or 0)
                    )
                except Exception:
                    dob_dt = None
        if lagna_for_tr is not None:
            tr = compute_transits(lagna_for_tr, moon_sign_idx, dob=dob_dt)
            tr_str = format_transit_summary(tr) if tr else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] transits failed: {exc}")

    # Sprint-8 — Jaimini Chara Dasha (sign-based mahadasha)
    cd_str = ""
    try:
        from chara_dasha import (compute_chara_dasha,  # type: ignore
                                 format_chara_dasha_summary)
        _lg_name = None
        if intel.get("ascendant"):
            _lg_name = intel["ascendant"]
        elif kundli.get("ascendant"):
            asc = kundli["ascendant"]
            _lg_name = asc.get("sign") if isinstance(asc, dict) else asc
        cd = compute_chara_dasha(
            kundli.get("planets") or [], _lg_name, dob_dt
        )
        cd_str = format_chara_dasha_summary(cd) if cd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] chara_dasha failed: {exc}")

    # Assemble
    sections = [
        "═════════ LOCKED FACTS — MIRROR EXACTLY, NEVER INVENT ═════════",
        _format_basics(kundli, intel),
        _format_yoga_block(intel.get("yogas") or []),
        _format_dosh_block(dosh) if dosh else f"▸ MANGAL-DOSH: {intel.get('mangal_dosh','(unavailable)')}",
        _format_strength_block(verdicts, intel.get("dignities") or []),
        av_str,
        bb_str,
        asp_str,
        kk_str,
        div_str,
        tr_str,
        _format_dasha_block(kundli),
        pd_str,
        jm_str,
        cd_str,
        _format_house_lords(intel),
        kp_str,
        rem_str,
        "════════════════════════════════════════════════════════════════",
    ]
    # Drop empty sections (e.g. no house lords)
    return "\n\n".join(s for s in sections if s and s.strip())

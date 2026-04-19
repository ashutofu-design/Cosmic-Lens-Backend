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

    # Sprint-18.5 — Bhava Bala Deep (BPHS 4-fold per house: Adhipati + Digbala
    # + Drishti + Naisargika = 12 × 4 = 48 calculations)
    bbd_str = ""
    try:
        from vedic.strength.bhava_bala_deep import (compute_bhava_bala_deep,  # type: ignore
                                                    format_bhava_bala_deep_summary)
        _sign_to_idx_bb = {"Aries":0,"Taurus":1,"Gemini":2,"Cancer":3,"Leo":4,"Virgo":5,
                           "Libra":6,"Scorpio":7,"Sagittarius":8,"Capricorn":9,
                           "Aquarius":10,"Pisces":11}
        _lg_bb = kundli.get("ascendant") or kundli.get("lagna")
        _lg_sign_bb = _lg_bb.get("sign") if isinstance(_lg_bb, dict) else _lg_bb
        _lg_idx_bb = _sign_to_idx_bb.get(_lg_sign_bb) if isinstance(_lg_sign_bb, str) else None
        bbd = compute_bhava_bala_deep(intel, shadbala, asp_obj, _lg_idx_bb)
        bbd_str = format_bhava_bala_deep_summary(bbd) if bbd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] bhava_bala_deep (Sprint-18.5) failed: {exc}")

    # Sprint-18 placeholder — actual compute moved AFTER all divisional charts
    # so it can read real per-varga sign_idx (architect fix).
    bd_str = ""

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

    # Sprint-9 — D2 Hora + D3 Drekkana + D7 Saptamsa + D12 Dwadasamsa
    extra_div_str = ""
    try:
        from divisional_charts import (compute_d2, compute_d3, compute_d7,  # type: ignore
                                       compute_d12, format_extra_vargas_summary)
        _planets = kundli.get("planets") or []
        d2  = compute_d2(_planets,  lagna_lon)
        d3  = compute_d3(_planets,  lagna_lon)
        d7  = compute_d7(_planets,  lagna_lon)
        d12 = compute_d12(_planets, lagna_lon)
        extra_div_str = format_extra_vargas_summary(d2, d3, d7, d12, intel)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] extra vargas (D2/D3/D7/D12) failed: {exc}")

    # Sprint-10 — D16 Shodasamsa + D20 Vimsamsa + D24 Chaturvimsamsa + D27 Bhamsa
    adv_div_str = ""
    try:
        from divisional_charts import (compute_d16, compute_d20, compute_d24,  # type: ignore
                                       compute_d27, format_advanced_vargas_summary)
        _planets2 = kundli.get("planets") or []
        d16 = compute_d16(_planets2, lagna_lon)
        d20 = compute_d20(_planets2, lagna_lon)
        d24 = compute_d24(_planets2, lagna_lon)
        d27 = compute_d27(_planets2, lagna_lon)
        adv_div_str = format_advanced_vargas_summary(d16, d20, d24, d27, intel)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] advanced vargas (D16/D20/D24/D27) failed: {exc}")

    # Sprint-11 — D30 Trimsamsa + D40 Khavedamsa + D45 Akshavedamsa + D60 Shashtyamsa
    subtle_div_str = ""
    try:
        from divisional_charts import (compute_d30, compute_d40, compute_d45,  # type: ignore
                                       compute_d60, format_subtle_vargas_summary)
        _planets3 = kundli.get("planets") or []
        d30 = compute_d30(_planets3, lagna_lon)
        d40 = compute_d40(_planets3, lagna_lon)
        d45 = compute_d45(_planets3, lagna_lon)
        d60 = compute_d60(_planets3, lagna_lon)
        subtle_div_str = format_subtle_vargas_summary(d30, d40, d45, d60, intel, _planets3)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] subtle vargas (D30/D40/D45/D60) failed: {exc}")

    # Sprint-12 — Per-varga deep: Vargottama matrix + Shadvarga Bala + Varga-lagna-lord
    deep_div_str = ""
    try:
        from divisional_charts import format_varga_deep_summary  # type: ignore
        deep_div_str = format_varga_deep_summary(
            kundli.get("planets") or [], lagna_lon, intel
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] varga deep (Sprint-12) failed: {exc}")

    # Sprint-18 — Extended Bala (BPHS sub-calculations: Saptavargaja, full Kala Bala,
    # Ishta/Kashta Phala, Vimshopaka Bala, Yuddha Bala). Computed AFTER all
    # divisional charts so Saptavargaja/Vimshopaka use REAL per-varga sign_idx.
    try:
        from datetime import datetime as _dtBD
        from vedic.strength.bala_deep import (compute_bala_deep,  # type: ignore
                                              format_bala_deep_summary)
        from divisional_charts import (compute_d2 as _d2f, compute_d3 as _d3f,  # type: ignore
                                       compute_d7 as _d7f, compute_d9 as _d9f,
                                       compute_d10 as _d10f, compute_d12 as _d12f,
                                       compute_d16 as _d16f, compute_d20 as _d20f,
                                       compute_d24 as _d24f, compute_d27 as _d27f,
                                       compute_d30 as _d30f, compute_d40 as _d40f,
                                       compute_d45 as _d45f, compute_d60 as _d60f)

        _planets_bd = kundli.get("planets") or []
        _sign_to_idx = {"Aries":0,"Taurus":1,"Gemini":2,"Cancer":3,"Leo":4,"Virgo":5,
                        "Libra":6,"Scorpio":7,"Sagittarius":8,"Capricorn":9,"Aquarius":10,"Pisces":11}

        # Compute all 15 vargas (D1 from natal sign + 14 divisionals)
        _all_vargas = {
            "D2":  _d2f(_planets_bd,  lagna_lon),
            "D3":  _d3f(_planets_bd,  lagna_lon),
            "D7":  _d7f(_planets_bd,  lagna_lon),
            "D9":  _d9f(_planets_bd,  lagna_lon),
            "D10": _d10f(_planets_bd, lagna_lon),
            "D12": _d12f(_planets_bd, lagna_lon),
            "D16": _d16f(_planets_bd, lagna_lon),
            "D20": _d20f(_planets_bd, lagna_lon),
            "D24": _d24f(_planets_bd, lagna_lon),
            "D27": _d27f(_planets_bd, lagna_lon),
            "D30": _d30f(_planets_bd, lagna_lon),
            "D40": _d40f(_planets_bd, lagna_lon),
            "D45": _d45f(_planets_bd, lagna_lon),
            "D60": _d60f(_planets_bd, lagna_lon),
        }

        _varga_charts = {}
        for _p in _planets_bd:
            _name = _p.get("name")
            if not _name:
                continue
            _d1_si = _sign_to_idx.get(_p.get("sign"))
            entry = {}
            if _d1_si is not None:
                entry["D1"] = _d1_si
            for _vname, _vdict in _all_vargas.items():
                _info = (_vdict or {}).get(_name) if isinstance(_vdict, dict) else None
                if isinstance(_info, dict):
                    _si = _info.get("sign_idx")
                    if _si is None and _info.get("sign"):
                        _si = _sign_to_idx.get(_info["sign"])
                    if _si is not None:
                        entry[_vname] = _si
            if entry:
                _varga_charts[_name] = entry

        # Birth datetime
        _bdt = None
        try:
            _bsrc = birth or {}
            _dob = _bsrc.get("dob") or _bsrc.get("dateOfBirth") or kundli.get("dob")
            _tob = _bsrc.get("tob") or _bsrc.get("timeOfBirth") or kundli.get("time") or "12:00"
            if _dob:
                # Try multiple formats
                for _fmt in ("%Y-%m-%d %H:%M", "%d %b %Y %I:%M %p",
                             "%d %B %Y %I:%M %p", "%Y-%m-%d %I:%M %p"):
                    try:
                        _bdt = _dtBD.strptime(f"{_dob} {_tob}", _fmt)
                        break
                    except ValueError:
                        continue
        except Exception:
            _bdt = None

        _sun_lon = next((p.get("longitude", 0.0) for p in _planets_bd
                         if p.get("name") == "Sun"), 0.0)

        # Pull shadbala totals + per-planet uchhabala/chesta
        _sb_totals, _ub_map, _cb_map = {}, {}, {}
        if shadbala and isinstance(shadbala, dict):
            for _pn, _data in shadbala.items():
                if isinstance(_data, dict):
                    _sb_totals[_pn] = _data.get("total", 0.0)
                    _sthana = _data.get("sthana") or {}
                    if isinstance(_sthana, dict):
                        _ub_map[_pn] = _sthana.get("uchhabala", 30.0)
                    _cb_map[_pn] = _data.get("chesta", 30.0)

        bd = compute_bala_deep(
            planets=_planets_bd,
            varga_charts=_varga_charts,
            birth_dt=_bdt,
            sun_longitude=_sun_lon,
            shadbala_totals=_sb_totals,
            uchhabala_by_planet=_ub_map,
            chesta_by_planet=_cb_map,
        )
        bd_str = format_bala_deep_summary(bd) if bd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] bala_deep (Sprint-18) failed: {exc}")

    # Sprint-19 — Classical yogas mega-detector (Vipreet/Dhana/Negative/KaalSarp/Nabhasa/Pravrajya)
    classical_yogas_str = ""
    try:
        from vedic.yogas.classical_yogas import (detect_classical_yogas,  # type: ignore
                                                 format_classical_yogas_summary)
        _lg_cy = kundli.get("ascendant") or kundli.get("lagna")
        _lg_sign_cy = (_lg_cy.get("sign") if isinstance(_lg_cy, dict) else _lg_cy)
        _sti_cy = {n: i for i, n in enumerate([
            "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
            "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"])}
        _lg_idx_cy = (_sti_cy.get(_lg_sign_cy) if isinstance(_lg_sign_cy, str)
                      else _lg_sign_cy if isinstance(_lg_sign_cy, int) else None)
        _cy = detect_classical_yogas(kundli.get("planets") or [], _lg_idx_cy)
        classical_yogas_str = format_classical_yogas_summary(_cy) if _cy else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] classical yogas (Sprint-19) failed: {exc}")

    # Sprint-19.5 — Extra classical yogas (Saraswati, Brahma/Vishnu/Shiva,
    # Lunar peripheral, Karak-Bhuvan, Aakriti remaining 12, Royal yogas,
    # Amsavatara, Neech-Bhanga 4-rule, BPHS Lord-in-house 60+)
    extra_yogas_str = ""
    try:
        from vedic.yogas.extra_yogas import (detect_extra_yogas,  # type: ignore
                                             format_extra_yogas_summary)
        _ey = detect_extra_yogas(kundli.get("planets") or [], _lg_idx_cy)
        extra_yogas_str = format_extra_yogas_summary(_ey) if _ey else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] extra yogas (Sprint-19.5) failed: {exc}")

    # Sprint-20 — Tier-4 Doshas Deep (Mangal full BPHS, Pitra 3-reasons,
    # Sade-Sati phase, Kantaka Shani, Vish Yog, Karaka Doshas, Grahan, Shrapit)
    deep_doshas_str = ""
    try:
        from vedic.doshas.dosh_deep import (detect_deep_doshas,  # type: ignore
                                            format_deep_doshas_summary)
        # Try to get current Saturn sign for transit-based doshas
        _cur_sat = None
        try:
            from chart_intelligence import _current_saturn_sign  # type: ignore
            _cur_sat = _current_saturn_sign()
        except Exception:
            pass
        _nak = (kundli.get("nakshatra") or
                (kundli.get("moon") or {}).get("nakshatra") or "")
        if isinstance(_nak, dict):
            _nak = _nak.get("name", "")
        _dd = detect_deep_doshas(kundli.get("planets") or [], _lg_idx_cy,
                                 current_saturn_sign=_cur_sat,
                                 nakshatra_name=_nak)
        deep_doshas_str = format_deep_doshas_summary(_dd) if _dd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] deep doshas (Sprint-20) failed: {exc}")

    # Sprint-21 — Tier-5 Extra Dashas (Yogini, Ashtottari, Narayana, Karaka,
    # Naisargika, Tara, Brahma, Yogardha + Pinda/Amshayur longevity)
    extra_dashas_str = ""
    try:
        from vedic.dashas.dasha_extras import (compute_all_extra_dashas,  # type: ignore
                                               format_extra_dashas_summary)
        _ed = compute_all_extra_dashas(kundli)
        extra_dashas_str = format_extra_dashas_summary(_ed) if _ed else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] extra dashas (Sprint-21) failed: {exc}")

    # Sprint-22 — Per-Varga Deep (aspects + ashtakavarga + lagna-lord matrix)
    varga_deep_str = ""
    try:
        from vedic.varga.varga_deep import (compute_varga_deep_all,  # type: ignore
                                            format_varga_deep_summary)
        _vd = compute_varga_deep_all(kundli.get("planets") or [], lagna_lon)
        varga_deep_str = format_varga_deep_summary(_vd) if _vd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] varga deep (Sprint-22) failed: {exc}")

    # Sprint-23 — Tier-7 Ashtakavarga Deep (Trikona/Ekadhipatya Shodhana,
    # Sodhya Pinda, Transit overlay)
    ashtaka_deep_str = ""
    try:
        from vedic.varga.ashtaka_deep import (compute_ashtaka_deep,  # type: ignore
                                              format_ashtaka_deep_summary,
                                              SIGN_NAMES as _SN)
        _lg_ad = kundli.get("ascendant")
        _lg_si = _SN.index(_lg_ad) if isinstance(_lg_ad, str) and _lg_ad in _SN else None
        # Use natal positions as transit-baseline (real transit can be wired later)
        _transits = {p["name"]: _SN.index(p["sign"])
                     for p in (kundli.get("planets") or [])
                     if isinstance(p, dict) and p.get("name") in
                     ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
                     and p.get("sign") in _SN}
        _ad = compute_ashtaka_deep(kundli.get("planets") or [], _lg_si,
                                   transit_signs=_transits)
        ashtaka_deep_str = format_ashtaka_deep_summary(_ad) if _ad else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] ashtaka deep (Sprint-23) failed: {exc}")

    # Sprint-24 — Tier-8 Transit Deep (Saturn 12-house detail, Eclipse axis,
    # Fixed Stars overlap)
    transit_deep_str = ""
    try:
        from vedic.transits.transit_deep import (compute_transit_deep,  # type: ignore
                                                 format_transit_deep_summary)
        _td = compute_transit_deep(kundli)
        transit_deep_str = format_transit_deep_summary(_td) if _td else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] transit deep (Sprint-24) failed: {exc}")

    # Sprint-25 — Tier-9 KP Deep (SSS lords, 4-level significators, RP,
    # 249 horary lookup engine, eclipse pin-point)
    kp_deep_str = ""
    try:
        from vedic.kp.kp_deep import (compute_kp_deep,  # type: ignore
                                       format_kp_deep_summary)
        _kpd = compute_kp_deep(kundli)
        kp_deep_str = format_kp_deep_summary(_kpd) if _kpd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] kp deep (Sprint-25) failed: {exc}")

    # Sprint-26 — Jaimini Rashi Drishti (sign aspects, BPHS Ch.7)
    rashi_drishti_str = ""
    try:
        from vedic.jaimini.rashi_drishti import (compute_rashi_drishti,  # type: ignore
                                                 format_rashi_drishti_summary,
                                                 SIGN_NAMES as _SN_RD)
        _lg_rd = kundli.get("ascendant")
        _lg_si_rd = _SN_RD.index(_lg_rd) if isinstance(_lg_rd, str) and _lg_rd in _SN_RD else None
        _rd = compute_rashi_drishti(kundli.get("planets") or [], _lg_si_rd)
        rashi_drishti_str = format_rashi_drishti_summary(_rd) if _rd else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] rashi drishti (Sprint-26) failed: {exc}")

    # Sprint-27 — Special Lagnas (Sree, Indu, Bhrigu Bindu, Karakamsa)
    special_lagnas_str = ""
    try:
        from vedic.jaimini.special_lagnas import (compute_special_lagnas,  # type: ignore
                                                   format_special_lagnas_summary)
        _sl = compute_special_lagnas(kundli)
        special_lagnas_str = format_special_lagnas_summary(_sl) if _sl else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] special lagnas (Sprint-27) failed: {exc}")

    # Sprint-28 / Phase A2 — Age context (current_age + life-stage + dasha-age window)
    age_context_str = ""
    try:
        from vedic.context.age_context import (compute_age_context,  # type: ignore
                                                format_age_context_summary)
        _ac = compute_age_context(birth or {}, kundli, kundli.get("currentDasha"))
        age_context_str = format_age_context_summary(_ac) if _ac else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] age context (Sprint-28) failed: {exc}")

    # Sprint-29 / Phase B — Full Shadbala sub-bala formatter
    shadbala_full_str = ""
    try:
        from vedic.strength.shadbala_full_format import format_shadbala_full  # type: ignore
        _bd_for_fmt = locals().get("bd") or None
        shadbala_full_str = format_shadbala_full(shadbala, _bd_for_fmt)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] shadbala full format (Sprint-29) failed: {exc}")

    # Sprint-34 / Phase I — KP Advanced (I2 CIL + I5 Marriage)
    kp_phase_i_str = ""
    try:
        from vedic.kp.kp_phase_i import (compute_kp_phase_i,  # type: ignore
                                           format_kp_phase_i_summary)
        _kpi = compute_kp_phase_i(kundli)
        kp_phase_i_str = format_kp_phase_i_summary(_kpi)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] kp phase-I (Sprint-34) failed: {exc}")

    # Sprint-33 / Phase H — Transits & Eclipses (H2/H3/H6/H7/H8 expansion)
    phase_h_str = ""
    try:
        from vedic.transits.phase_h import (compute_phase_h_transits,  # type: ignore
                                              format_phase_h_summary)
        _ph = compute_phase_h_transits(kundli, birth)
        phase_h_str = format_phase_h_summary(_ph)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-H transits (Sprint-33) failed: {exc}")

    # Sprint-32 / Phase F — Per-Varga Full Depth (F3 + F4-expand + F5)
    varga_phase_f_str = ""
    try:
        from vedic.varga.varga_phase_f import (compute_varga_phase_f,  # type: ignore
                                                format_varga_phase_f_summary)
        _cd = (kundli.get("currentDasha") or kundli.get("current_dasha") or {})
        _md = _cd.get("maha") or _cd.get("md") or ""
        _ad = _cd.get("antar") or _cd.get("ad") or ""
        _ll_f = lagna_lon
        if not isinstance(_ll_f, (int, float)):
            _ll_f = (kundli.get("ascendantDeg")
                     or kundli.get("ascendant_deg")
                     or kundli.get("ascendantLongitude"))
        _vf = compute_varga_phase_f(kundli.get("planets") or [],
                                    _ll_f, _md, _ad)
        varga_phase_f_str = format_varga_phase_f_summary(_vf)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-F varga depth (Sprint-32) failed: {exc}")

    # Sprint-31 / Phase E — Tier-5 Dasha gap-fill (7 systems)
    phase_e_dashas_str = ""
    try:
        from vedic.dashas.dasha_phase_e import (compute_all_phase_e_dashas,  # type: ignore
                                                  format_phase_e_summary)
        _ke = dict(kundli)
        _ke["dob"] = _ke.get("dob") or birth.get("dob") or birth.get("date")
        _pe = compute_all_phase_e_dashas(_ke)
        phase_e_dashas_str = format_phase_e_summary(_pe)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] phase-E dashas (Sprint-31) failed: {exc}")

    # Sprint-30 / Phase C — Missing yogas (Indra + Shoola Nabhasa)
    missing_yogas_str = ""
    try:
        from vedic.yogas.missing_yogas import (detect_missing_yogas,  # type: ignore
                                                format_missing_yogas_summary)
        _my = detect_missing_yogas(kundli.get("planets") or [], _lg_idx_cy)
        missing_yogas_str = format_missing_yogas_summary(_my)
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] missing yogas (Sprint-30) failed: {exc}")

    # Sprint-15 — Per-varga yoga / dosha detection
    varga_yogas_str = ""
    try:
        from varga_yogas import (detect_all_varga_yogas,  # type: ignore
                                 format_varga_yogas_summary)
        _lg_vy = kundli.get("ascendant") or kundli.get("lagna")
        _lg_sign_vy = (_lg_vy.get("sign") if isinstance(_lg_vy, dict) else _lg_vy)
        _vy = detect_all_varga_yogas(
            kundli.get("planets") or [], lagna_lon, _lg_sign_vy
        )
        varga_yogas_str = format_varga_yogas_summary(_vy) if _vy else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] varga yogas (Sprint-15) failed: {exc}")

    # Sprint-14 — Sthira Dasha + Niryana Shoola Dasha (extra Jaimini sign-dashas)
    sthira_str = ""
    niryana_str = ""
    try:
        from extra_jaimini_dashas import (compute_sthira_dasha,  # type: ignore
                                          compute_niryana_shoola,
                                          format_sthira_summary,
                                          format_niryana_summary)
        _lg_xj = kundli.get("ascendant") or kundli.get("lagna")
        _lg_sign_xj = (_lg_xj.get("sign") if isinstance(_lg_xj, dict) else _lg_xj)
        _dob_xj = birth if birth else None
        _sth = compute_sthira_dasha(_lg_sign_xj, _dob_xj)
        _nir = compute_niryana_shoola(_lg_sign_xj, _dob_xj)
        sthira_str  = format_sthira_summary(_sth)  if _sth else ""
        niryana_str = format_niryana_summary(_nir) if _nir else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] extra Jaimini dashas (Sprint-14) failed: {exc}")

    # Sprint-13 — Argala / Virodhargala (Jaimini intervention)
    argala_str = ""
    try:
        from argala import compute_argala, format_argala_summary  # type: ignore
        _lg_arg = kundli.get("ascendant") or kundli.get("lagna")
        _lg_sign_arg = (_lg_arg.get("sign") if isinstance(_lg_arg, dict) else _lg_arg)
        _arg = compute_argala(kundli.get("planets") or [], _lg_sign_arg)
        _argala_topic = (kundli.get("_topic") or "general").lower()
        argala_str = format_argala_summary(_arg, topic=_argala_topic) if _arg else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[locked_facts] argala (Sprint-13) failed: {exc}")

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
        bbd_str,
        bd_str,
        asp_str,
        kk_str,
        div_str,
        extra_div_str,
        adv_div_str,
        subtle_div_str,
        deep_div_str,
        classical_yogas_str,
        extra_yogas_str,
        deep_doshas_str,
        extra_dashas_str,
        varga_deep_str,
        ashtaka_deep_str,
        transit_deep_str,
        kp_deep_str,
        rashi_drishti_str,
        special_lagnas_str,
        age_context_str,
        shadbala_full_str,
        missing_yogas_str,
        phase_e_dashas_str,
        varga_phase_f_str,
        phase_h_str,
        kp_phase_i_str,
        varga_yogas_str,
        argala_str,
        sthira_str,
        niryana_str,
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

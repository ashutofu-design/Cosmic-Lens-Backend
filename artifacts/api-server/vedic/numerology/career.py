"""Tier 6 — Career & Profession bundle.

Produces a structured career blueprint by combining:
  • Jaimini Atmakaraka (soul-purpose) + Amatyakaraka (career karaka)
  • 10th house deep analysis (D1: sign, lord, lord-house, occupants)
  • D10 Dashamsha (career chart): ascendant, 10th-of-D10, AmK position in D10
  • Job-vs-Business decision (10th lord + Saturn vs Sun + 7th-lord influence)
  • Best-fit industries (driver vocation ⊕ AK theme ⊕ 10th-lord)
  • Career timing window from current Mahadasha lord vs 10th house
  • Career-change / Rajayoga detection
  • Numerology layer: driver vocation, conductor execution-style, personal-year career timing

Public API:
    compute_career_bundle(kundli, dob, driver, conductor, name) -> dict
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ── Sign / lord tables ────────────────────────────────────────────────
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}
KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}
UPACHAYA_HOUSES = {3, 6, 10, 11}

# ── Driver-number vocation map (numerology layer) ─────────────────────
DRIVER_VOCATION: Dict[int, Dict[str, Any]] = {
    1: {
        "planet": "Sun", "vibration": "Leadership / Authority",
        "keywords": ["government", "executive role", "administration", "jewelry & gold",
                     "premium brands", "top-management consulting"],
        "execution_style": "decisive, top-down, ego-driven (in a positive sense)",
        "best_role": "founder, CEO, head-of-department, government officer",
        "warning": "avoid pure subordinate roles long-term — frustration builds",
    },
    2: {
        "planet": "Moon", "vibration": "Care / Public-service",
        "keywords": ["hospitality", "dairy & beverages", "water-related industries",
                     "healthcare & nursing", "women-targeted brands", "interior design (soft)"],
        "execution_style": "intuitive, people-first, mood-driven",
        "best_role": "co-founder, HR head, hospitality manager, care professional",
        "warning": "avoid high-conflict / heavy-tech roles — emotional drain",
    },
    3: {
        "planet": "Jupiter", "vibration": "Wisdom / Teaching",
        "keywords": ["teaching & academia", "law & legal advisory", "finance & banking",
                     "publishing", "philosophy & religion", "investment advisory"],
        "execution_style": "principle-driven, broad-vision, slightly slow",
        "best_role": "professor, lawyer, financial advisor, content authority, publisher",
        "warning": "avoid mass-execution roles — strategy beats execution",
    },
    4: {
        "planet": "Rahu", "vibration": "Innovation / Foreign / Tech",
        "keywords": ["technology & IT", "foreign trade", "media & advertising",
                     "electricity & aviation", "unconventional ventures", "research"],
        "execution_style": "rule-breaking, sudden-jump, lateral thinker",
        "best_role": "tech-founder, foreign-services, media producer, R&D head",
        "warning": "avoid orthodox traditional sectors — boredom + restlessness",
    },
    5: {
        "planet": "Mercury", "vibration": "Communication / Trade",
        "keywords": ["communication", "media & marketing", "trading & brokerage",
                     "accountancy", "writing & journalism", "stock market"],
        "execution_style": "fast, multi-track, analytical",
        "best_role": "marketer, broker, journalist, content-creator, trader",
        "warning": "avoid slow long-cycle industries — restlessness",
    },
    6: {
        "planet": "Venus", "vibration": "Beauty / Art / Luxury",
        "keywords": ["beauty & cosmetics", "fashion & design", "entertainment & films",
                     "hospitality & weddings", "luxury brands", "fine arts & music"],
        "execution_style": "aesthetic-driven, relationship-led, harmony-seeking",
        "best_role": "designer, artist, brand-builder, wedding-planner, hotelier",
        "warning": "avoid harsh / industrial sectors — discomfort + low output",
    },
    7: {
        "planet": "Ketu", "vibration": "Mysticism / Research / Detachment",
        "keywords": ["spiritual teaching", "research & investigation",
                     "foreign / remote work", "occult & astrology", "IT (mystical / niche)",
                     "writing (deep)"],
        "execution_style": "introspective, monk-like, slow-burn",
        "best_role": "researcher, spiritual teacher, investigator, niche IT specialist",
        "warning": "avoid high-social mass-market roles — exhaustion",
    },
    8: {
        "planet": "Saturn", "vibration": "Discipline / Long-cycle / Justice",
        "keywords": ["heavy industry", "mining & oil", "real-estate", "long-cycle business",
                     "law & justice", "labor & logistics", "iron & steel"],
        "execution_style": "patient, disciplined, karmic-burden-bearing",
        "best_role": "industrialist, judge, real-estate developer, large-scale ops head",
        "warning": "career peaks AFTER 35 — don't quit early; karma demands time",
    },
    9: {
        "planet": "Mars", "vibration": "Action / Engineering / Defense",
        "keywords": ["engineering", "defense & police", "sports & fitness",
                     "surgery & emergency medicine", "construction", "machinery & automobiles"],
        "execution_style": "high-energy, combative, deadline-driven",
        "best_role": "engineer, surgeon, defense officer, athlete, builder",
        "warning": "avoid passive desk-only roles — restless aggression spills out",
    },
}

# ── AK (Atmakaraka) soul-purpose map ──────────────────────────────────
AK_SOUL_PURPOSE: Dict[str, str] = {
    "Sun":     "Leadership, authority, self-realisation through governance / father-figure roles. Soul wants to BE the centre.",
    "Moon":    "Public service, nurturing, emotional intelligence work. Soul wants to FEEL deeply and care for masses.",
    "Mars":    "Action, courage, defence/engineering/sports. Soul wants to FIGHT for something righteous.",
    "Mercury": "Communication, intellect, trade, writing. Soul wants to CONNECT ideas and people.",
    "Jupiter": "Teaching, wisdom, dharma, advisory. Soul wants to GUIDE others toward truth.",
    "Venus":   "Art, beauty, harmony, relationships. Soul wants to CREATE and refine taste.",
    "Saturn":  "Discipline, service to underprivileged, long-haul mastery. Soul wants to ENDURE and transform through patience.",
}

# ── AmK (Amatyakaraka — career karaka) themes ─────────────────────────
AMK_CAREER_THEME: Dict[str, str] = {
    "Sun":     "Governmental, executive, leadership, jewelry, prestige brands, medical (cardiology).",
    "Moon":    "Hospitality, dairy, public-facing, healthcare, water/beverages, women-focused services.",
    "Mars":    "Engineering, real-estate, defence, sports, surgery, automobiles, energy.",
    "Mercury": "Communications, media, trade, accountancy, IT-software, education, brokerage.",
    "Jupiter": "Law, finance, teaching, advisory, publishing, religion-charity, banking.",
    "Venus":   "Art, design, fashion, entertainment, beauty, luxury hotels, wedding industry.",
    "Saturn":  "Mining, heavy industry, oil, judiciary, labor, long-cycle real-estate, agriculture.",
}


def _safe_get(d: Optional[Dict], key: str, default=None):
    return d.get(key, default) if isinstance(d, dict) else default


def _planet_house_d1(planets: List[Dict], asc_sign: str) -> Dict[str, int]:
    """Return {planet_name: house_number} from D1 planets list."""
    if not isinstance(planets, list) or asc_sign not in SIGNS:
        return {}
    asc_idx = SIGNS.index(asc_sign)
    out: Dict[str, int] = {}
    for p in planets:
        if not isinstance(p, dict): continue
        sgn = p.get("sign")
        nm = p.get("name")
        if sgn in SIGNS and nm:
            sidx = SIGNS.index(sgn)
            out[nm] = ((sidx - asc_idx + 12) % 12) + 1
    return out


def _occupants_of_house(planets: List[Dict], asc_sign: str, house_num: int) -> List[str]:
    h = _planet_house_d1(planets, asc_sign)
    return sorted([nm for nm, hn in h.items() if hn == house_num])


def _personal_year(dob: str, year: int) -> int:
    """Numerology Personal Year = sum(month + day + year-digits) reduced strictly to 1-9.

    Matches the canonical reduction rule used in `extended.compute_personal_cycles`
    (keep_master=False) — master numbers are NOT preserved here so all numerology
    layers stay consistent. Returns 1 on parse failure.
    """
    try:
        d = datetime.strptime(dob, "%Y-%m-%d").date()
        s = sum(int(c) for c in f"{d.month:02d}{d.day:02d}{year:04d}")
        while s > 9:
            s = sum(int(c) for c in str(s))
        return s or 9
    except Exception:
        return 1


def _resolve_md_end(kundli: Dict[str, Any], md_lord: str) -> str:
    """Find the TRUE Mahadasha end-date for `md_lord` from kundli['dashas'][].

    `kundli['currentDasha']['endDate']` is actually the current ANTARDASHA end.
    The proper Mahadasha end lives in the dashas[] timeline as the entry whose
    planet matches md_lord and whose date-window contains today.
    """
    try:
        from datetime import datetime as _dt
        today = _dt.now().date()
        for entry in (kundli.get("dashas") or []):
            if entry.get("planet") != md_lord:
                continue
            try:
                start = _dt.strptime(entry.get("startDate", ""), "%Y-%m-%d").date()
                end = _dt.strptime(entry.get("endDate", ""), "%Y-%m-%d").date()
            except Exception:
                continue
            if start <= today <= end:
                return entry.get("endDate", "—")
        # Fallback: first matching MD entry
        for entry in (kundli.get("dashas") or []):
            if entry.get("planet") == md_lord:
                return entry.get("endDate", "—")
    except Exception:
        pass
    return "—"


def _synergy(driver: int, conductor: int) -> str:
    """Re-uses the canonical pair-classification from framing.py."""
    try:
        from vedic.numerology.framing import _synergy_verdict
        return _synergy_verdict(driver, conductor)
    except Exception:
        return "NEUTRAL" if driver != conductor else "FOCUSED"


def compute_career_bundle(kundli: Dict[str, Any], dob: str,
                          driver: int, conductor: int,
                          name: str = "") -> Dict[str, Any]:
    """Produce the Tier 6 Career bundle (always returns a dict; never raises)."""
    out: Dict[str, Any] = {"available": False}
    if not isinstance(kundli, dict):
        return out

    # ── 1. Karakas (AK / AmK) ─────────────────────────────────────
    try:
        from karakas import compute_karakas  # type: ignore
        karakas = compute_karakas(kundli.get("planets", []))
    except Exception:
        karakas = {}
    ak = karakas.get("AK") or "—"
    amk = karakas.get("AmK") or "—"
    ak_details = next((d for d in karakas.get("details", []) if d.get("role") == "AK"), {})
    amk_details = next((d for d in karakas.get("details", []) if d.get("role") == "AmK"), {})

    # ── 2. D1 10th house ──────────────────────────────────────────
    asc = kundli.get("ascendant") or "Aries"
    if asc not in SIGNS:
        asc = "Aries"
    asc_idx = SIGNS.index(asc)
    tenth_sign = SIGNS[(asc_idx + 9) % 12]
    tenth_lord = SIGN_LORD.get(tenth_sign, "—")
    tenth_occ = _occupants_of_house(kundli.get("planets", []), asc, 10)
    p_house = _planet_house_d1(kundli.get("planets", []), asc)
    tenth_lord_house = p_house.get(tenth_lord, 0)

    # ── 3. D10 Dashamsha ──────────────────────────────────────────
    d10 = (kundli.get("divisionalCharts") or {}).get("D10") or {}
    d10_asc = d10.get("ascendant") or "—"
    d10_planets = d10.get("planets", []) or []
    d10_planet_houses = {p.get("name"): p.get("house") for p in d10_planets if isinstance(p, dict)}
    d10_tenth_occ = sorted([p.get("name") for p in d10_planets
                            if isinstance(p, dict) and p.get("house") == 10 and p.get("name")])
    amk_in_d10 = d10_planet_houses.get(amk, None)
    ak_in_d10 = d10_planet_houses.get(ak, None)

    # ── 4. Job-vs-Business decision ────────────────────────────────
    business_score = 0
    job_score = 0
    notes: List[str] = []

    if tenth_lord_house in KENDRA_HOUSES:
        job_score += 2
        notes.append(f"10th-lord {tenth_lord} in kendra (house {tenth_lord_house}) — strong employed-track")
    if tenth_lord_house in TRIKONA_HOUSES:
        job_score += 1
        business_score += 1
        notes.append(f"10th-lord in trikona — favours both prestige employment AND own venture")
    if tenth_lord_house in DUSTHANA_HOUSES:
        business_score += 2
        notes.append(f"10th-lord in dusthana ({tenth_lord_house}) — switching/restructuring/own-venture is healthier")
    if tenth_lord_house in UPACHAYA_HOUSES and tenth_lord_house != 10:
        business_score += 1
        notes.append(f"10th-lord in upachaya ({tenth_lord_house}) — career grows over time, entrepreneur-friendly")

    # 7th-lord influence on 10th = business indication
    seventh_sign = SIGNS[(asc_idx + 6) % 12]
    seventh_lord = SIGN_LORD.get(seventh_sign, "—")
    if seventh_lord in tenth_occ:
        business_score += 2
        notes.append(f"7th-lord {seventh_lord} occupies 10th — classical business yoga")

    # Saturn vs Sun strength → service vs authority
    sun_house = p_house.get("Sun", 0)
    sat_house = p_house.get("Saturn", 0)
    if sun_house in {1, 5, 9, 10, 11}:
        job_score += 1; notes.append("Sun in good house → leadership / govt-style authority favoured")
    if sat_house in {3, 6, 10, 11}:
        business_score += 1; notes.append("Saturn in upachaya → long-cycle business endurance")

    if business_score - job_score >= 2:
        verdict = "BUSINESS"
    elif job_score - business_score >= 2:
        verdict = "JOB / EMPLOYMENT"
    else:
        verdict = "HYBRID (consultancy / job-with-side-venture)"

    job_vs_biz = {
        "verdict": verdict,
        "job_score": job_score,
        "business_score": business_score,
        "notes": notes[:6],
    }

    # ── 5. Best-fit industries (merge driver + AK + 10th-lord) ────
    voc = DRIVER_VOCATION.get(driver, DRIVER_VOCATION[1])
    industries = list(voc["keywords"])
    ak_theme = AK_SOUL_PURPOSE.get(ak, "")
    amk_theme = AMK_CAREER_THEME.get(amk, "")
    if amk_theme:
        # Pull first comma-separated terms as additional industry tags
        extra = [s.strip().rstrip(".") for s in amk_theme.split(",")]
        industries.extend([e for e in extra if e and e not in industries][:4])

    # ── 6. Career timing — current Mahadasha vs 10th house ────────
    cur = (kundli.get("currentDasha") or {})
    md_lord = cur.get("maha") or "—"
    ad_lord = cur.get("antar") or "—"
    ad_end = cur.get("endDate") or "—"
    # currentDasha.endDate is the ANTARDASHA end — pull true Mahadasha end
    # from the dashas[] timeline so labelling is honest.
    md_end = _resolve_md_end(kundli, md_lord) if md_lord != "—" else "—"

    md_house = p_house.get(md_lord, 0)
    timing_verdict = "MIXED"
    timing_note = ""
    if md_house == 10 or md_lord == tenth_lord:
        timing_verdict = "CAREER-PEAK"
        timing_note = (f"Current MD lord {md_lord} sits in 10th house OR is itself the 10th-lord — "
                       f"this is a CAREER-PEAK Mahadasha. Make big moves before {md_end}.")
    elif md_house in {1, 5, 9, 11}:
        timing_verdict = "FAVOURABLE"
        timing_note = (f"Current MD lord {md_lord} in house {md_house} (kendra/trikona/11th) — "
                       f"career trajectory is favourable; ride the momentum, don't switch impulsively.")
    elif md_house in DUSTHANA_HOUSES:
        timing_verdict = "RESTRUCTURING"
        timing_note = (f"Current MD lord {md_lord} in house {md_house} (dusthana) — "
                       f"career feels stuck or under-restructure. Use this period to UPSKILL, "
                       f"avoid major bets until next MD.")
    else:
        timing_verdict = "STEADY-GROWTH"
        timing_note = (f"Current MD lord {md_lord} in house {md_house} — neutral career window; "
                       f"focus on consistent growth, not radical change.")

    # ── 7. Career-change yogas (simplified Rajayoga + obstruction) ─
    rajayoga_pairs: List[str] = []
    fifth_sign = SIGNS[(asc_idx + 4) % 12]
    ninth_sign = SIGNS[(asc_idx + 8) % 12]
    fifth_lord = SIGN_LORD.get(fifth_sign, "—")
    ninth_lord = SIGN_LORD.get(ninth_sign, "—")
    # Kendra-Trikona lord conjunction (simplified: same house)
    for k_lord_label, k_lord in [("10th-lord", tenth_lord)]:
        for t_lord_label, t_lord in [("5th-lord", fifth_lord), ("9th-lord", ninth_lord)]:
            if k_lord != t_lord:
                kh = p_house.get(k_lord, 0); th = p_house.get(t_lord, 0)
                if kh and kh == th:
                    rajayoga_pairs.append(
                        f"{k_lord_label} ({k_lord}) + {t_lord_label} ({t_lord}) conjoined in house {kh} — RAJAYOGA"
                    )
            elif k_lord == t_lord:
                rajayoga_pairs.append(
                    f"{k_lord} rules BOTH {k_lord_label} and {t_lord_label} — natural Rajayoga concentration"
                )

    obstructions: List[str] = []
    if tenth_lord_house in DUSTHANA_HOUSES:
        obstructions.append(f"10th-lord weak (in {tenth_lord_house}) — slow recognition; persistence required")
    if "Saturn" in tenth_occ:
        obstructions.append("Saturn in 10th — delayed but durable career; peak post-35")
    if "Rahu" in tenth_occ:
        obstructions.append("Rahu in 10th — unconventional path, sudden jumps, foreign exposure")

    # ── 8. Numerology layer ───────────────────────────────────────
    py_2026 = _personal_year(dob, 2026)
    py_2027 = _personal_year(dob, 2027)
    py_2028 = _personal_year(dob, 2028)
    PY_THEME = {
        1: "FRESH-START year — launch new venture, change job, reinvent identity",
        2: "PARTNERSHIP year — co-founder talks, alliances, slow patience",
        3: "EXPANSION year — visibility, content, networking, social wins",
        4: "FOUNDATION year — build systems, not flash; ROI later",
        5: "CHANGE year — travel, switch, communication-heavy moves",
        6: "RESPONSIBILITY year — promotions, family-business, leadership",
        7: "INTROSPECTION year — upskill, research, NOT switch impulsively",
        8: "ACHIEVEMENT year — financial peak, big deals, recognition",
        9: "COMPLETION year — close old chapters, prepare next launch",
        11: "MASTERY year — spiritual+material alignment, big visibility",
        22: "MASTER-BUILDER year — build a legacy structure",
    }

    synergy = _synergy(driver, conductor)
    voc_c = DRIVER_VOCATION.get(conductor, voc)

    numerology_layer = {
        "driver_vocation": {
            "driver": driver, "planet": voc["planet"], "vibration": voc["vibration"],
            "best_role": voc["best_role"], "execution_style": voc["execution_style"],
            "warning": voc["warning"],
        },
        "conductor_execution": {
            "conductor": conductor, "planet": voc_c["planet"],
            "execution_style": voc_c["execution_style"],
        },
        "synergy_verdict": synergy,
        "personal_year_timeline": [
            {"year": 2026, "py": py_2026, "theme": PY_THEME.get(py_2026, "—")},
            {"year": 2027, "py": py_2027, "theme": PY_THEME.get(py_2027, "—")},
            {"year": 2028, "py": py_2028, "theme": PY_THEME.get(py_2028, "—")},
        ],
    }

    # ── 9. Synthesis verdict ──────────────────────────────────────
    syn_parts: List[str] = []
    syn_parts.append(f"Driver-{driver} ({voc['planet']}) → natural pull = {voc['vibration']}.")
    if ak != "—":
        syn_parts.append(f"Atmakaraka {ak} → soul wants {AK_SOUL_PURPOSE.get(ak, 'self-realisation').split('.')[0].lower()}.")
    if amk != "—":
        syn_parts.append(f"Amatyakaraka {amk} → ideal career-domain = {AMK_CAREER_THEME.get(amk, '').split(',')[0].lower()}.")
    syn_parts.append(f"10th-house: sign={tenth_sign}, lord={tenth_lord} (in house {tenth_lord_house or '—'}).")
    syn_parts.append(f"Job-vs-Business verdict: {verdict}.")
    syn_parts.append(f"Current Mahadasha ({md_lord}–{ad_lord}) → {timing_verdict}.")
    if rajayoga_pairs:
        syn_parts.append(f"Rajayoga(s) detected: {len(rajayoga_pairs)}.")
    syn_parts.append(f"Personal-Year 2026 = {py_2026} ({PY_THEME.get(py_2026, '—').split(' year')[0]}).")
    synthesis = " ".join(syn_parts)

    out.update({
        "available": True,
        "soul_purpose": {
            "ak_planet": ak,
            "ak_sign": ak_details.get("sign", "—"),
            "ak_deg": ak_details.get("deg_in_sign", 0),
            "ak_in_d10_house": ak_in_d10,
            "ak_theme": AK_SOUL_PURPOSE.get(ak, ""),
        },
        "career_karaka": {
            "amk_planet": amk,
            "amk_sign": amk_details.get("sign", "—"),
            "amk_deg": amk_details.get("deg_in_sign", 0),
            "amk_house_d1": p_house.get(amk, 0),
            "amk_house_d10": amk_in_d10,
            "amk_theme": AMK_CAREER_THEME.get(amk, ""),
        },
        "tenth_house": {
            "sign": tenth_sign,
            "lord": tenth_lord,
            "lord_house": tenth_lord_house,
            "occupants": tenth_occ,
            "occupants_count": len(tenth_occ),
        },
        "dashamsha": {
            "ascendant": d10_asc,
            "tenth_occupants": d10_tenth_occ,
            "amk_in_d10_house": amk_in_d10,
            "ak_in_d10_house": ak_in_d10,
        },
        "job_vs_business": job_vs_biz,
        "best_industries": industries[:10],
        "career_timing": {
            "current_md_lord": md_lord,
            "current_ad_lord": ad_lord,
            "md_lord_house": md_house,
            "md_end_date": md_end,         # true Mahadasha end (from dashas[])
            "ad_end_date": ad_end,         # current Antardasha end (from currentDasha)
            "verdict": timing_verdict,
            "note": timing_note,
        },
        "rajayogas": rajayoga_pairs[:5],
        "obstructions": obstructions[:5],
        "numerology_layer": numerology_layer,
        "synthesis_verdict": synthesis,
    })
    return out

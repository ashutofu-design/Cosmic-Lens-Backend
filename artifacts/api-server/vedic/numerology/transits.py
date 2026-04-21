"""Tier 10 — Transits, Sade-Sati & Yearly Forecast bundle.

Combines:
  • Sade-Sati status (Saturn transit vs natal Moon, 7.5-yr cycle, 3 phases)
  • Saturn Dhaiya / Ashtama-Shani (Saturn over 4th/8th from natal Moon)
  • Jupiter Gochar (current Jupiter sign, 12-house impact from Moon)
  • Rahu-Ketu axis transit (1.5-yr per sign, current house impact)
  • Three-layer Dasha (Maha + Antar + Pratyantar)
  • Numerology Personal Year + Personal Month
  • 12-month theme outlook (transiting Sun thru natal houses)
  • Synthesis verdict

Public API:
    compute_transits_bundle(kundli, dob, driver, conductor, today=None) -> dict
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

try:
    import swisseph as swe  # type: ignore
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    _SWE_OK = True
except Exception:
    _SWE_OK = False

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

# Jupiter Gochar — supportive houses from Moon (classical Saravali)
# Favourable: 2, 5, 7, 9, 11. Difficult: 3, 4, 8, 12. Mixed: 1, 6, 10.
JUPITER_GOCHAR_VERDICT: Dict[int, Tuple[str, str]] = {
    1: ("MIXED", "Jupiter on natal Moon — emotional expansion + weight gain risk; spiritual growth strong"),
    2: ("FAVOURABLE", "Wealth + family harmony + speech-blessings"),
    3: ("DIFFICULT", "Effort doesn't match reward; siblings/short-trips unsettled"),
    4: ("DIFFICULT", "Home/property matters need patience; vehicles/comfort delayed"),
    5: ("FAVOURABLE", "Children, creativity, education, romance — golden window"),
    6: ("MIXED", "Health needs care; debts can resolve; new service-oriented work"),
    7: ("FAVOURABLE", "Marriage, partnerships, business deals favoured"),
    8: ("DIFFICULT", "Hidden challenges, occult-research, in-law tensions; transformation"),
    9: ("FAVOURABLE", "Dharma-blessing, pilgrimage, father-bond strong, higher learning"),
    10: ("MIXED", "Career growth possible but with extra effort; recognition slow"),
    11: ("FAVOURABLE", "Income jumps, gains, large-network expansion, wishes fulfilled"),
    12: ("DIFFICULT", "Foreign-residence/expenses/spiritual-retreat themes; charity favourable"),
}

# Rahu-Ketu axis — house-pair impact (Rahu in N → Ketu in N+6)
RAHU_HOUSE_NOTE: Dict[int, str] = {
    1: "Personality reset; identity crisis pushed toward bold new direction",
    2: "Family/finance disruption; speech becomes amplified or controversial",
    3: "Sudden courage, sibling shifts, communication boom (writing/social media)",
    4: "Mother/home-front instability; relocations or property speculation",
    5: "Romance/children/speculation hot; risk of impulsive choices, gambling",
    6: "Enemy-defeat, debt-resolution, service-sector boom; health-vigilance",
    7: "Partnerships/marriage attract foreigners or unconventional unions",
    8: "Sudden wealth-or-loss windows; deep occult/research pull; surgeries possible",
    9: "Dharma questioned; foreign-travel/higher-learning karma; father karma surfaces",
    10: "Career disruption-or-meteoric-rise; status shift via unconventional means",
    11: "Income jumps via foreign/tech/network; large gains but watch over-extension",
    12: "Foreign-residence, hidden expenses, spiritual-retreat; sleep/dreams intensified",
}

# Driver-number lucky months (year-ahead anchor)
DRIVER_LUCKY_MONTHS: Dict[int, List[int]] = {
    1: [1, 4, 8, 10],  2: [2, 6, 7, 11], 3: [3, 6, 9, 12],
    4: [1, 4, 8, 10],  5: [5, 6, 9, 12], 6: [2, 5, 6, 11],
    7: [1, 7, 11, 12], 8: [3, 8, 10, 12], 9: [3, 9, 10, 11],
}


def _planet_house_d1(planets: List[Dict], asc_sign: str) -> Dict[str, int]:
    if not isinstance(planets, list) or asc_sign not in SIGNS:
        return {}
    asc_idx = SIGNS.index(asc_sign)
    out: Dict[str, int] = {}
    for p in planets:
        if not isinstance(p, dict): continue
        sgn = p.get("sign"); nm = p.get("name")
        if sgn in SIGNS and nm:
            sidx = SIGNS.index(sgn)
            out[nm] = ((sidx - asc_idx + 12) % 12) + 1
    return out


def _planet_sign(planets: List[Dict], name: str) -> Optional[str]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == name:
            return p.get("sign")
    return None


def _sidereal_sign_today(planet_id: int, today: date) -> Optional[str]:
    """Return sidereal sign (Lahiri) of given planet at midnight UT today."""
    if not _SWE_OK:
        return None
    try:
        jd = swe.julday(today.year, today.month, today.day, 0.0)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        result, _ = swe.calc_ut(jd, planet_id, flags)
        lon = result[0] % 360.0
        sidx = int(lon // 30)
        return SIGNS[sidx]
    except Exception:
        return None


def _resolve_md_pd(kundli: Dict, today: date) -> Dict[str, str]:
    """Walk dashas[] → subDashas to find current MD + AD + PD."""
    out = {"md": "—", "ad": "—", "pd": "—",
           "md_end": "—", "ad_end": "—", "pd_end": "—"}
    for md in (kundli.get("dashas") or []):
        try:
            ms = datetime.strptime(md.get("startDate", ""), "%Y-%m-%d").date()
            me = datetime.strptime(md.get("endDate", ""), "%Y-%m-%d").date()
        except Exception:
            continue
        if not (ms <= today <= me):
            continue
        out["md"] = md.get("planet", "—"); out["md_end"] = md.get("endDate", "—")
        for ad in (md.get("subDashas") or []):
            try:
                a_s = datetime.strptime(ad.get("startDate", ""), "%Y-%m-%d").date()
                a_e = datetime.strptime(ad.get("endDate", ""), "%Y-%m-%d").date()
            except Exception:
                continue
            if not (a_s <= today <= a_e):
                continue
            out["ad"] = ad.get("planet", "—"); out["ad_end"] = ad.get("endDate", "—")
            for pd_ in (ad.get("subDashas") or []):
                try:
                    p_s = datetime.strptime(pd_.get("startDate", ""), "%Y-%m-%d").date()
                    p_e = datetime.strptime(pd_.get("endDate", ""), "%Y-%m-%d").date()
                except Exception:
                    continue
                if p_s <= today <= p_e:
                    out["pd"] = pd_.get("planet", "—")
                    out["pd_end"] = pd_.get("endDate", "—")
                    break
            break
        break
    return out


def _personal_year(dob: str, today: date) -> int:
    """Numerology personal year = (DOB-month + DOB-day + current-year) reduced."""
    try:
        d = datetime.strptime(dob, "%Y-%m-%d").date()
    except Exception:
        return 0
    total = d.month + d.day + today.year
    while total > 9:
        total = sum(int(c) for c in str(total))
    return total


def _personal_month(personal_year: int, today: date) -> int:
    total = personal_year + today.month
    while total > 9:
        total = sum(int(c) for c in str(total))
    return total


PERSONAL_YEAR_THEMES: Dict[int, Dict[str, str]] = {
    1: {"theme": "FRESH START", "do": "Launch new venture, change job, take initiative",
        "avoid": "Clinging to old patterns, hesitation"},
    2: {"theme": "PARTNERSHIP & PATIENCE", "do": "Collaborate, deepen bonds, be diplomatic",
        "avoid": "Forcing solo decisions, impatience"},
    3: {"theme": "EXPANSION & CREATIVITY", "do": "Travel, learn, write, social events, marriage",
        "avoid": "Scattering energy, over-spending"},
    4: {"theme": "BUILD FOUNDATIONS", "do": "Buy property, structure routines, save",
        "avoid": "Speculation, sudden moves"},
    5: {"theme": "CHANGE & FREEDOM", "do": "Travel, change residence, network expansion",
        "avoid": "Reckless decisions, impulsive shifts"},
    6: {"theme": "FAMILY & RESPONSIBILITY", "do": "Marriage, children, home renovation, service",
        "avoid": "Sacrificing self entirely, perfectionism"},
    7: {"theme": "INNER WORK & STUDY", "do": "Spirituality, research, retreats, deep learning",
        "avoid": "Major financial risks, public exposure"},
    8: {"theme": "MASTERY & POWER", "do": "Business expansion, real estate, big financial moves",
        "avoid": "Ego clashes, legal disputes"},
    9: {"theme": "COMPLETION & RELEASE", "do": "Wrap up cycles, donate, forgive, prepare next chapter",
        "avoid": "Starting brand-new long-term projects"},
}

PERSONAL_MONTH_FLAVOR: Dict[int, str] = {
    1: "month for new starts and bold action",
    2: "month for cooperation and emotional alignment",
    3: "month for travel, social events, creativity",
    4: "month for hard work and structural building",
    5: "month for change, movement, surprises",
    6: "month for family, home, service",
    7: "month for retreat, study, inner work",
    8: "month for money decisions and authority",
    9: "month for completion and clearing",
}


def _saturn_phase(saturn_sign: str, moon_sign: str) -> Dict[str, Any]:
    """Compute Sade-Sati / Dhaiya status from current Saturn vs natal Moon."""
    if saturn_sign not in SIGNS or moon_sign not in SIGNS:
        return {"active": False, "phase": "—",
                "verdict": "UNKNOWN", "note": "Sign data unavailable"}
    sat_idx = SIGNS.index(saturn_sign)
    moon_idx = SIGNS.index(moon_sign)
    house_from_moon = ((sat_idx - moon_idx + 12) % 12) + 1
    sat_house_relative = ((sat_idx - moon_idx) % 12)  # 0..11

    # Sade-Sati = Saturn in 12th, 1st, 2nd from Moon (sidereal next/curr/prev)
    if sat_house_relative == 11:  # 12th from Moon — Rising phase
        return {"active": True, "phase": "RISING (Phase 1 of 3)",
                "house_from_moon": 12, "verdict": "SADE-SATI ACTIVE",
                "note": "Saturn in 12th from natal Moon — Rising phase. Mental restlessness, "
                        "expenses, sleep-disturbance, foreign matters; first 2.5 years of the 7.5-year cycle."}
    if sat_house_relative == 0:  # On Moon — Peak
        return {"active": True, "phase": "PEAK (Phase 2 of 3)",
                "house_from_moon": 1, "verdict": "SADE-SATI ACTIVE",
                "note": "Saturn directly on natal Moon — Peak phase. Heavy responsibility, "
                        "emotional weight, health-vigilance, identity reshaping; middle 2.5 years."}
    if sat_house_relative == 1:  # 2nd from Moon — Setting
        return {"active": True, "phase": "SETTING (Phase 3 of 3)",
                "house_from_moon": 2, "verdict": "SADE-SATI ACTIVE",
                "note": "Saturn in 2nd from natal Moon — Setting phase. Wealth-tested, family-speech "
                        "matters surface, then begins to release; final 2.5 years."}
    # Dhaiya / Ashtama
    if sat_house_relative == 3:
        return {"active": False, "phase": "ARDHA-ASHTAMA (Dhaiya)",
                "house_from_moon": 4, "verdict": "DHAIYA-I ACTIVE",
                "note": "Saturn in 4th from natal Moon — Half-Ashtama (Dhaiya). 2.5-yr period of "
                        "home/mother/inner-peace tests; smaller cousin of Sade-Sati."}
    if sat_house_relative == 7:
        return {"active": False, "phase": "ASHTAMA-SHANI",
                "house_from_moon": 8, "verdict": "ASHTAMA-SHANI ACTIVE",
                "note": "Saturn in 8th from natal Moon — Ashtama Shani. 2.5-yr period of "
                        "transformation, hidden tests, in-law challenges, occult-pull."}
    return {"active": False, "phase": "CLEAR",
            "house_from_moon": house_from_moon, "verdict": "NO-SADE-SATI",
            "note": f"Saturn currently in House {house_from_moon} from natal Moon — outside Sade-Sati / Dhaiya zones; standard transit period."}


def compute_transits_bundle(kundli: Dict[str, Any], dob: str,
                            driver: int, conductor: int,
                            today: Optional[date] = None) -> Dict[str, Any]:
    """Compute T10 Transits bundle. Hard data gate — never fabricates."""
    out: Dict[str, Any] = {"available": False}
    if not isinstance(kundli, dict):
        out["reason"] = "no kundli"; return out

    asc = kundli.get("ascendant")
    planets = kundli.get("planets", []) or []
    if not asc or asc not in SIGNS:
        out["reason"] = f"ascendant missing/unknown ({asc!r})"; return out
    if not isinstance(planets, list) or len(planets) < 9:
        out["reason"] = "planets list incomplete (<9 grahas)"; return out

    if not _SWE_OK:
        out["reason"] = "pyswisseph not available — transits cannot be computed"; return out

    today = today or date.today()
    asc_idx = SIGNS.index(asc)
    p_house = _planet_house_d1(planets, asc)

    # Natal anchors
    natal_moon_sign = _planet_sign(planets, "Moon")
    natal_sun_sign = _planet_sign(planets, "Sun")
    if not natal_moon_sign:
        out["reason"] = "natal Moon sign missing"; return out

    # ── Live transits ─────────────────────────────────────────────
    sat_sign = _sidereal_sign_today(swe.SATURN, today)
    jup_sign = _sidereal_sign_today(swe.JUPITER, today)
    rah_sign = _sidereal_sign_today(swe.MEAN_NODE, today)
    if not sat_sign or not jup_sign or not rah_sign:
        out["reason"] = "transit calculation failed"; return out
    ket_sign = SIGNS[(SIGNS.index(rah_sign) + 6) % 12]

    # House-from-natal-Moon (for Sade-Sati / Jupiter Gochar from Moon)
    moon_idx = SIGNS.index(natal_moon_sign)
    sat_h_moon = ((SIGNS.index(sat_sign) - moon_idx) % 12) + 1
    jup_h_moon = ((SIGNS.index(jup_sign) - moon_idx) % 12) + 1
    rah_h_moon = ((SIGNS.index(rah_sign) - moon_idx) % 12) + 1

    # House-from-ascendant (for natal-house transit-impact)
    sat_h_lagna = ((SIGNS.index(sat_sign) - asc_idx) % 12) + 1
    jup_h_lagna = ((SIGNS.index(jup_sign) - asc_idx) % 12) + 1
    rah_h_lagna = ((SIGNS.index(rah_sign) - asc_idx) % 12) + 1
    ket_h_lagna = ((SIGNS.index(ket_sign) - asc_idx) % 12) + 1

    # ── 1. Sade-Sati phase ────────────────────────────────────────
    sade = _saturn_phase(sat_sign, natal_moon_sign)
    sade.update({
        "saturn_sign_now": sat_sign,
        "natal_moon_sign": natal_moon_sign,
        "saturn_house_from_lagna": sat_h_lagna,
        "saturn_house_from_moon": sat_h_moon,
    })

    # ── 2. Jupiter Gochar ─────────────────────────────────────────
    jup_verdict, jup_note = JUPITER_GOCHAR_VERDICT.get(jup_h_moon,
                                                       ("MIXED", "Standard transit"))
    jupiter_block = {
        "jupiter_sign_now": jup_sign,
        "jupiter_house_from_lagna": jup_h_lagna,
        "jupiter_house_from_moon": jup_h_moon,
        "verdict": jup_verdict,
        "note": jup_note,
        "year_window_end": today.replace(year=today.year + 1).isoformat(),
    }

    # ── 3. Rahu-Ketu axis ────────────────────────────────────────
    rahu_block = {
        "rahu_sign_now": rah_sign, "ketu_sign_now": ket_sign,
        "rahu_house_from_lagna": rah_h_lagna,
        "ketu_house_from_lagna": ket_h_lagna,
        "rahu_house_from_moon": rah_h_moon,
        "rahu_note": RAHU_HOUSE_NOTE.get(rah_h_lagna, "Standard nodal-transit period"),
        "ketu_note": RAHU_HOUSE_NOTE.get(ket_h_lagna,
                                          "Releasing-karma area — what to detach from"),
    }

    # ── 4. Three-layer dasha ─────────────────────────────────────
    dasha = _resolve_md_pd(kundli, today)
    dasha_block = {
        **dasha,
        "md_house": p_house.get(dasha["md"], 0),
        "ad_house": p_house.get(dasha["ad"], 0),
        "pd_house": p_house.get(dasha["pd"], 0),
    }

    # ── 5. Numerology Personal Year + Month ──────────────────────
    py = _personal_year(dob, today)
    pm = _personal_month(py, today)
    py_meta = PERSONAL_YEAR_THEMES.get(py, PERSONAL_YEAR_THEMES[1])
    pm_meta = PERSONAL_MONTH_FLAVOR.get(pm, "standard month")
    numerology_block = {
        "personal_year": py,
        "personal_year_theme": py_meta["theme"],
        "personal_year_do": py_meta["do"],
        "personal_year_avoid": py_meta["avoid"],
        "personal_month": pm,
        "personal_month_flavor": pm_meta,
        "lucky_months_this_year": DRIVER_LUCKY_MONTHS.get(driver, []),
        "current_year": today.year,
        "current_month_num": today.month,
    }

    # ── 6. 12-month theme outlook ────────────────────────────────
    # Solar transit moves through one rashi/month → month-by-month house transit
    # Natal Sun at start of birth-month gives baseline; we compute month-by-month
    # transiting Sun house-from-Lagna for the next 12 months.
    outlook: List[Dict[str, Any]] = []
    HOUSE_THEME = {
        1: "self-image / health initiatives",
        2: "wealth, family, speech matters",
        3: "courage, siblings, short trips, communications",
        4: "home, mother, real estate, vehicles",
        5: "creativity, children, romance, speculation",
        6: "service, debts, enemies, health-vigilance",
        7: "partnerships, marriage, business deals",
        8: "transformation, occult, hidden matters, in-laws",
        9: "dharma, father, long travel, higher learning",
        10: "career visibility, status, authority",
        11: "income, networks, gains, wishes-fulfilled",
        12: "expenses, foreign-residence, retreat, charity",
    }
    for m_offset in range(12):
        try:
            yr = today.year + ((today.month - 1 + m_offset) // 12)
            mn = ((today.month - 1 + m_offset) % 12) + 1
            d = date(yr, mn, 15)  # mid-month sample
            sun_sign = _sidereal_sign_today(swe.SUN, d)
            if sun_sign:
                sun_h = ((SIGNS.index(sun_sign) - asc_idx) % 12) + 1
                outlook.append({
                    "year": yr, "month": mn,
                    "month_name": d.strftime("%b %Y"),
                    "sun_sign": sun_sign, "sun_house": sun_h,
                    "theme": HOUSE_THEME.get(sun_h, "—"),
                })
        except Exception:
            continue

    # ── 7. Synthesis ─────────────────────────────────────────────
    syn = (
        f"Saturn transit ({sat_sign}, House {sat_h_moon} from Moon): {sade.get('verdict','—')}. "
        f"Jupiter ({jup_sign}, House {jup_h_moon} from Moon): {jup_verdict}. "
        f"Rahu in {rah_sign} (H{rah_h_lagna} from Lagna), Ketu in {ket_sign}. "
        f"Current Dasha: {dasha['md']} → {dasha['ad']} → {dasha['pd']}. "
        f"Personal Year {py} ({py_meta['theme']}), Personal Month {pm}."
    )

    out.update({
        "available": True,
        "as_of_date": today.isoformat(),
        "sade_sati": sade,
        "jupiter_gochar": jupiter_block,
        "rahu_ketu_axis": rahu_block,
        "dasha_layers": dasha_block,
        "numerology_yearly": numerology_block,
        "twelve_month_outlook": outlook,
        "synthesis_verdict": syn,
    })
    return out

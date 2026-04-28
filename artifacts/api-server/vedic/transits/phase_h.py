"""
Sprint 33 / Phase H — Transits & Eclipses (gap fill)
Adds 4 sub-systems missing from existing transit_deep.py:
  H2 Jupiter 12-yr cycle effects (per house from Lagna/Moon)
  H3 Rahu-Ketu 18-month transit effects (per house)
  H6 Saros cycle identification + next/prev eclipse in series
  H7 Pre-natal eclipse points (closest solar+lunar before birth)
  H8 Fixed stars EXPANSION (24 → 56: + 27 nakshatra junction stars + Abhijit + 4 Western royals)
H1 Saturn-through-houses ✅ + H4/H5 Eclipse impact ✅ already in transit_deep.py.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Optional

try:
    import swisseph as swe
    _HAS_SWE = True
except Exception:
    _HAS_SWE = False

SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

# Lahiri ayanamsa for sidereal conversion
def _set_ayanamsa():
    if _HAS_SWE:
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)


# ─── H2: Jupiter through 12 houses (12-yr cycle) ──────────────────────
JUPITER_HOUSE_EFFECTS = {
    1: ("BENEFIC", "Personal growth, optimism, new opportunities, weight gain, expansion of self"),
    2: ("STRONG-BENEFIC", "Wealth gains, family expansion, eloquence, financial windfalls"),
    3: ("MIXED", "Some delays in initiatives, but courage grows; siblings benefit"),
    4: ("CHALLENGING", "Property/home issues, mother's health concerns, mental restlessness"),
    5: ("STRONG-BENEFIC", "Children, learning, romance, creativity blossom; spiritual gains"),
    6: ("MIXED", "Victory over enemies & disease but legal issues possible"),
    7: ("STRONG-BENEFIC", "Marriage opportunities, partnership expansion, fame from spouse"),
    8: ("CHALLENGING", "Hidden losses, occult interests, longevity tests, in-law disputes"),
    9: ("STRONGEST", "Highest dharma, fortune, gurus, foreign travel, religious merit, father benefits"),
    10: ("CHALLENGING", "Career delays, authority conflicts, but long-term reputation building"),
    11: ("STRONG-BENEFIC", "Major income gains, fulfillment of desires, elder sibling benefit, networks expand"),
    12: ("MIXED", "Spiritual retreat, foreign moves, expenses on dharma, moksha karma"),
}


def jupiter_through_houses(jupiter_sign_idx: int, lagna_sign_idx: int,
                            moon_sign_idx: int) -> dict[str, Any]:
    h_lagna = ((jupiter_sign_idx - lagna_sign_idx) % 12) + 1
    h_moon = ((jupiter_sign_idx - moon_sign_idx) % 12) + 1
    v_l, d_l = JUPITER_HOUSE_EFFECTS.get(h_lagna, ("UNKNOWN", ""))
    v_m, d_m = JUPITER_HOUSE_EFFECTS.get(h_moon, ("UNKNOWN", ""))
    return {
        "jupiter_sign": SIGN_NAMES[jupiter_sign_idx],
        "from_lagna": {"house": h_lagna, "verdict": v_l, "detail": d_l},
        "from_moon":  {"house": h_moon, "verdict": v_m, "detail": d_m},
        "is_guru_chandala_zone": h_moon in (6, 8, 12),
        "is_guru_uchcha_zone":   h_moon in (5, 9, 11),
    }


# ─── H3: Rahu-Ketu 18-month transit effects ───────────────────────────
RAHU_HOUSE_EFFECTS = {
    1: ("CRITICAL", "Identity crisis, image change, reckless decisions, foreign attractions"),
    2: ("CHALLENGING", "Wealth obsession, family disputes, speech issues, food disorders"),
    3: ("BENEFIC", "Bold initiatives reward risk; siblings benefit; communication mastery"),
    4: ("CRITICAL", "Property losses, mother's health risk, foreign relocation, mental unrest"),
    5: ("CHALLENGING", "Children's issues, speculation losses, relationship complications"),
    6: ("STRONG-BENEFIC", "Victory over enemies, disease, and litigation; service success"),
    7: ("CRITICAL", "Marriage stress, foreign partnerships, betrayal risk, spouse's health"),
    8: ("CHALLENGING", "Sudden losses or gains, occult interests, transformation through chaos"),
    9: ("CHALLENGING", "Father issues, dharma confusion, foreign religious paths"),
    10: ("STRONG-BENEFIC", "Career boom, foreign work, sudden authority, political rise"),
    11: ("STRONGEST", "Massive gains, fulfilled desires, network expansion, fame"),
    12: ("CHALLENGING", "Hidden losses, foreign isolation, hospital/jail risk, moksha pursuit"),
}
KETU_HOUSE_EFFECTS = {
    1: ("CHALLENGING", "Detachment from self, identity confusion, spiritual isolation"),
    2: ("MIXED", "Detachment from wealth, food restrictions, vagueness in speech"),
    3: ("CRITICAL", "Sibling separation, courage drain, communication blocks"),
    4: ("CHALLENGING", "Home detachment, mother's spiritual journey, vehicle losses"),
    5: ("CRITICAL", "Childbirth issues, romance failures, intelligence blocks"),
    6: ("CHALLENGING", "Hidden enemies, chronic disease, debt accumulation"),
    7: ("CRITICAL", "Marriage breakdown, partner's health, business breakup"),
    8: ("BENEFIC", "Occult mastery, deep transformation, longevity gains"),
    9: ("STRONG-BENEFIC", "Spiritual awakening, guru contact, dharma path clear"),
    10: ("CHALLENGING", "Career loss or transformation, leaving prestige for purpose"),
    11: ("MIXED", "Some gains but losses too; older sibling distance"),
    12: ("STRONG-BENEFIC", "Moksha karma, spiritual ashrams, foreign retreats, liberation"),
}


def rahu_ketu_through_houses(rahu_sign_idx: int, lagna_sign_idx: int,
                              moon_sign_idx: int) -> dict[str, Any]:
    ketu_sign_idx = (rahu_sign_idx + 6) % 12
    rh_lag = ((rahu_sign_idx - lagna_sign_idx) % 12) + 1
    rh_moo = ((rahu_sign_idx - moon_sign_idx) % 12) + 1
    kt_lag = ((ketu_sign_idx - lagna_sign_idx) % 12) + 1
    kt_moo = ((ketu_sign_idx - moon_sign_idx) % 12) + 1
    rv_l, rd_l = RAHU_HOUSE_EFFECTS.get(rh_lag, ("UNKNOWN",""))
    rv_m, rd_m = RAHU_HOUSE_EFFECTS.get(rh_moo, ("UNKNOWN",""))
    kv_l, kd_l = KETU_HOUSE_EFFECTS.get(kt_lag, ("UNKNOWN",""))
    kv_m, kd_m = KETU_HOUSE_EFFECTS.get(kt_moo, ("UNKNOWN",""))
    return {
        "rahu_sign": SIGN_NAMES[rahu_sign_idx],
        "ketu_sign": SIGN_NAMES[ketu_sign_idx],
        "rahu_from_lagna": {"house": rh_lag, "verdict": rv_l, "detail": rd_l},
        "rahu_from_moon":  {"house": rh_moo, "verdict": rv_m, "detail": rd_m},
        "ketu_from_lagna": {"house": kt_lag, "verdict": kv_l, "detail": kd_l},
        "ketu_from_moon":  {"house": kt_moo, "verdict": kv_m, "detail": kd_m},
        "next_axis_shift_months": "~18-month axis (Rahu-Ketu retrograde through zodiac)",
    }


# ─── H6: Saros cycle identifier ───────────────────────────────────────
# Saros = 18 yr 11 day 8 hr cycle of solar/lunar eclipse repeats.
SAROS_DAYS = 18 * 365.25 + 11 + 8/24


def find_recent_eclipses(when: Optional[datetime] = None,
                          back_years: int = 1, fwd_years: int = 1) -> dict[str, Any]:
    """Find solar+lunar eclipses within ±back_years/+fwd_years from `when`.
       Identifies Saros series number for each (NASA-compatible Saros ID is
       complex; we report Saros-cycle interval to next/prev eclipse)."""
    if not _HAS_SWE:
        return {"available": False, "reason": "swisseph unavailable"}
    when = when or datetime.utcnow()
    base_jd = swe.julday(when.year, when.month, when.day,
                          when.hour + when.minute/60.0)

    results = {"solar_back": None, "solar_fwd": None,
               "lunar_back": None, "lunar_fwd": None}
    # Solar eclipse backward
    try:
        ret_back = swe.sol_eclipse_when_glob(base_jd, swe.FLG_SWIEPH, 0, backwards=True)
        jd_back = ret_back[1][0]
        y, m, d, h = swe.revjul(jd_back)
        results["solar_back"] = {"date": f"{int(y):04d}-{int(m):02d}-{int(d):02d}",
                                  "type": _eclipse_type(ret_back[0]),
                                  "days_ago": round((base_jd - jd_back), 1)}
    except Exception:
        pass
    # Solar eclipse forward
    try:
        ret_fwd = swe.sol_eclipse_when_glob(base_jd, swe.FLG_SWIEPH, 0, backwards=False)
        jd_fwd = ret_fwd[1][0]
        y, m, d, h = swe.revjul(jd_fwd)
        results["solar_fwd"] = {"date": f"{int(y):04d}-{int(m):02d}-{int(d):02d}",
                                 "type": _eclipse_type(ret_fwd[0]),
                                 "days_ahead": round((jd_fwd - base_jd), 1)}
    except Exception:
        pass
    # Lunar eclipse backward
    try:
        ret_lb = swe.lun_eclipse_when(base_jd, swe.FLG_SWIEPH, 0, backwards=True)
        jd_lb = ret_lb[1][0]
        y, m, d, h = swe.revjul(jd_lb)
        results["lunar_back"] = {"date": f"{int(y):04d}-{int(m):02d}-{int(d):02d}",
                                  "type": _eclipse_type(ret_lb[0]),
                                  "days_ago": round((base_jd - jd_lb), 1)}
    except Exception:
        pass
    # Lunar eclipse forward
    try:
        ret_lf = swe.lun_eclipse_when(base_jd, swe.FLG_SWIEPH, 0, backwards=False)
        jd_lf = ret_lf[1][0]
        y, m, d, h = swe.revjul(jd_lf)
        results["lunar_fwd"] = {"date": f"{int(y):04d}-{int(m):02d}-{int(d):02d}",
                                 "type": _eclipse_type(ret_lf[0]),
                                 "days_ahead": round((jd_lf - base_jd), 1)}
    except Exception:
        pass
    # Saros sibling eclipse: previous occurrence in same series ≈ current - 1 Saros
    if results["solar_back"]:
        prev_saros_jd = base_jd - SAROS_DAYS
        y, m, d, _ = swe.revjul(prev_saros_jd)
        results["saros_prev_solar"] = (f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
                                        + " (~1 Saros = 18yr 11d earlier)")
    if results["solar_fwd"]:
        next_saros_jd = base_jd + SAROS_DAYS
        y, m, d, _ = swe.revjul(next_saros_jd)
        results["saros_next_solar"] = (f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
                                        + " (~1 Saros = 18yr 11d later)")
    results["available"] = True
    results["evaluated_at"] = when.strftime("%Y-%m-%d")
    return results


def _eclipse_type(flags: int) -> str:
    if not _HAS_SWE: return "?"
    types = []
    if flags & swe.ECL_TOTAL: types.append("Total")
    if flags & swe.ECL_ANNULAR: types.append("Annular")
    if flags & swe.ECL_PARTIAL: types.append("Partial")
    if flags & getattr(swe, "ECL_PENUMBRAL", 0): types.append("Penumbral")
    return "/".join(types) if types else "?"


# ─── H7: Pre-natal eclipse points ────────────────────────────────────
def prenatal_eclipses(birth_dt: datetime) -> dict[str, Any]:
    """Return last solar + lunar eclipse BEFORE birth (sensitive degrees)."""
    if not _HAS_SWE:
        return {"available": False, "reason": "swisseph unavailable"}
    _set_ayanamsa()
    birth_jd = swe.julday(birth_dt.year, birth_dt.month, birth_dt.day,
                           birth_dt.hour + birth_dt.minute/60.0)
    out = {"available": True, "birth": birth_dt.strftime("%Y-%m-%d")}
    # Solar prenatal
    try:
        ret = swe.sol_eclipse_when_glob(birth_jd, swe.FLG_SWIEPH, 0, backwards=True)
        jd_e = ret[1][0]
        y, m, d, h = swe.revjul(jd_e)
        # Sun longitude at eclipse (sidereal)
        sun_lon = swe.calc_ut(jd_e, swe.SUN, swe.FLG_SIDEREAL)[0][0] % 360
        out["solar"] = {
            "date": f"{int(y):04d}-{int(m):02d}-{int(d):02d}",
            "type": _eclipse_type(ret[0]),
            "sensitive_lon": round(sun_lon, 2),
            "sensitive_sign": SIGN_NAMES[int(sun_lon // 30)],
            "days_before_birth": round((birth_jd - jd_e), 1),
        }
    except Exception as e:
        out["solar"] = {"error": str(e)}
    # Lunar prenatal
    try:
        ret = swe.lun_eclipse_when(birth_jd, swe.FLG_SWIEPH, 0, backwards=True)
        jd_e = ret[1][0]
        y, m, d, h = swe.revjul(jd_e)
        moon_lon = swe.calc_ut(jd_e, swe.MOON, swe.FLG_SIDEREAL)[0][0] % 360
        out["lunar"] = {
            "date": f"{int(y):04d}-{int(m):02d}-{int(d):02d}",
            "type": _eclipse_type(ret[0]),
            "sensitive_lon": round(moon_lon, 2),
            "sensitive_sign": SIGN_NAMES[int(moon_lon // 30)],
            "days_before_birth": round((birth_jd - jd_e), 1),
        }
    except Exception as e:
        out["lunar"] = {"error": str(e)}
    return out


# ─── H8: Fixed stars EXPANSION (24 → 56) ──────────────────────────────
# Add 27 nakshatra junction stars (Yogatara) + Abhijit + 4 Western royals
NAKSHATRA_JUNCTION_STARS = [
    # Sidereal longitudes ~ 2026 (Lahiri) — yogatara of each nakshatra
    ("Yogatara-Ashwini",      "Ashwini junction (β Arietis)",   13.20, "Speed, healing, beginnings"),
    ("Yogatara-Bharani",      "Bharani junction (35 Arietis)",  26.20, "Bearing, restraint, transformation"),
    ("Yogatara-Krittika",     "Alcyone (Krittika junction)",    60.02, "Cutting, burning, valor"),
    ("Yogatara-Rohini",       "Aldebaran (Rohini junction)",    69.78, "Growth, sensuality, fame"),
    ("Yogatara-Mrigashira",   "Mrigashira junction (λ Orionis)",83.00, "Searching, gentle, intellectual"),
    ("Yogatara-Ardra",        "Betelgeuse (Ardra junction)",    88.97, "Storm, destruction, renewal"),
    ("Yogatara-Punarvasu",    "Pollux (Punarvasu junction)",    122.83,"Return of light, prosperity"),
    ("Yogatara-Pushya",       "Pushya junction (δ Cancri)",     128.00,"Nourishment, expansion, dharma"),
    ("Yogatara-Ashlesha",     "Ashlesha junction (α Hydrae)",   142.00,"Embrace, serpent power, mysticism"),
    ("Yogatara-Magha",        "Regulus (Magha junction)",       149.94,"Royalty, fame, ancestors"),
    ("Yogatara-P.Phalguni",   "P.Phalguni junction (δ Leo)",    160.00,"Pleasure, marriage, generosity"),
    ("Yogatara-U.Phalguni",   "U.Phalguni junction (β Leo)",    173.00,"Patronage, marriage stability"),
    ("Yogatara-Hasta",        "Hasta junction (δ Corvi)",       186.00,"Hand, skill, manifestation"),
    ("Yogatara-Chitra",       "Spica (Chitra junction)",        203.85,"Beauty, art, divine craft"),
    ("Yogatara-Swati",        "Arcturus (Swati junction)",      204.23,"Independent, scattered, autonomy"),
    ("Yogatara-Vishakha",     "Vishakha junction (α Librae)",   221.50,"Forked goal, determination"),
    ("Yogatara-Anuradha",     "Anuradha junction (δ Scorpii)",  225.00,"Friendship, devotion, success"),
    ("Yogatara-Jyeshtha",     "Antares (Jyeshtha junction)",    249.92,"Eldest, courage, reversal"),
    ("Yogatara-Mula",         "Mula junction (λ Scorpii)",      254.00,"Root, destruction-of-old, foundation"),
    ("Yogatara-P.Ashadha",    "P.Ashadha junction (δ Sgr)",     260.00,"Invincible, early victory"),
    ("Yogatara-U.Ashadha",    "U.Ashadha junction (σ Sgr)",     272.00,"Lasting victory, dharma"),
    ("Yogatara-Shravana",     "Shravana junction (Altair)",     278.50,"Listening, learning, fame"),
    ("Yogatara-Dhanishta",    "Dhanishta junction (β Delphini)",290.00,"Wealth, music, drumming"),
    ("Yogatara-Shatabhisha",  "Shatabhisha junction (γ Aqr)",   307.00,"100 healers, secrecy, healing"),
    ("Yogatara-P.Bhadrapada", "P.Bhadrapada junction (α Peg)",  320.00,"Burning pyre, intensity, sacrifice"),
    ("Yogatara-U.Bhadrapada", "U.Bhadrapada junction (γ Peg)",  333.00,"Serpent of depth, kundalini"),
    ("Yogatara-Revati",       "Revati junction (ζ Piscium)",    355.00,"Wealth, journey-end, completion"),
    # 28th nakshatra (intercalary)
    ("Yogatara-Abhijit",      "Vega (Abhijit junction)",        285.43,"Invincible victory — most auspicious 4 ghati"),
    # 4 additional Western royal/notable stars
    ("Deneb",                 "Tail of Swan",                   5.50,  "Spiritual, philosophical depth"),
    ("Markab",                "Pegasus saddle",                 9.20,  "Travel, momentum, restless wisdom"),
    ("Hamal",                 "Aries head",                     14.95, "Aggression, leadership through force"),
    ("Toliman (α Cen)",       "Foot of Centaur",                250.10,"Friendship reward, neighbor's gain"),
]


def fixed_stars_expanded_overlap(natal_planets: list[dict],
                                  orb: float = 1.0) -> dict[str, Any]:
    """Same logic as transit_deep.fixed_stars_overlap but expanded catalog."""
    overlaps = []
    for star_name, star_class, star_lon, star_meaning in NAKSHATRA_JUNCTION_STARS:
        for p in natal_planets:
            if not isinstance(p, dict): continue
            lon = p.get("longitude")
            if not isinstance(lon, (int, float)): continue
            nm = p.get("name")
            if nm not in ("Sun","Moon","Mars","Mercury","Jupiter","Venus",
                          "Saturn","Rahu","Ketu"): continue
            d = min(abs(lon - star_lon), 360 - abs(lon - star_lon))
            if d <= orb:
                overlaps.append({
                    "planet": nm, "star": star_name,
                    "star_class": star_class,
                    "orb_deg": round(d, 2), "meaning": star_meaning,
                })
    return {
        "available": True,
        "expanded_catalog_size": len(NAKSHATRA_JUNCTION_STARS),
        "orb_used": orb, "overlaps_count": len(overlaps),
        "overlaps": overlaps,
    }


# ─── Master orchestrator ──────────────────────────────────────────────
def compute_phase_h_transits(kundli: dict, birth: dict) -> dict[str, Any]:
    # Sprint-26 Fix-K: defensive None-handling. The legacy callsite passed
    # birth=None for father/spouse charts (no separate birth dict) which
    # crashed the whole phase via 'NoneType.get' on line ~342. The phase
    # can still emit Saros + fixed-stars + transits-from-now without a
    # birth dict; only the prenatal-eclipse calc needs dob/time, and that
    # block already has a `if isinstance(dob, str)` guard.
    birth = birth or {}
    if not _HAS_SWE:
        return {"available": False, "reason": "swisseph unavailable"}
    planets = kundli.get("planets") or []
    lagna_sign = kundli.get("ascendant") or kundli.get("lagna")
    moon_sign = kundli.get("moonSign") or kundli.get("moon_sign")
    if isinstance(lagna_sign, str) and lagna_sign in SIGN_NAMES:
        lagna_si = SIGN_NAMES.index(lagna_sign)
    else: lagna_si = None
    if isinstance(moon_sign, str) and moon_sign in SIGN_NAMES:
        moon_si = SIGN_NAMES.index(moon_sign)
    else: moon_si = None
    out: dict[str, Any] = {"available": True}
    # Need current Jupiter / Rahu positions
    _set_ayanamsa()
    now = datetime.utcnow()
    jd_now = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60.0)
    flags = swe.FLG_SIDEREAL
    try:
        jup_lon = swe.calc_ut(jd_now, swe.JUPITER, flags)[0][0] % 360
        rahu_lon = swe.calc_ut(jd_now, swe.MEAN_NODE, flags)[0][0] % 360
        jup_si = int(jup_lon // 30)
        rahu_si = int(rahu_lon // 30)
        if lagna_si is not None and moon_si is not None:
            out["jupiter_through_houses"] = jupiter_through_houses(jup_si, lagna_si, moon_si)
            out["rahu_ketu_through_houses"] = rahu_ketu_through_houses(rahu_si, lagna_si, moon_si)
    except Exception as e:
        out["transit_calc_error"] = str(e)
    # Saros + recent eclipses
    out["saros_eclipses"] = find_recent_eclipses(now)
    # Pre-natal eclipses
    dob = birth.get("dob") or birth.get("date") or kundli.get("dob")
    btime = birth.get("time") or kundli.get("time") or "12:00"
    if isinstance(dob, str):
        try:
            for fmt in ("%Y-%m-%d","%d-%m-%Y","%d %b %Y","%d %B %Y"):
                try:
                    dob_dt = datetime.strptime(dob, fmt); break
                except Exception: continue
            else: dob_dt = None
            if dob_dt:
                # add time
                try:
                    if isinstance(btime, str) and ":" in btime:
                        hh, mm = btime.split(":")[:2]
                        dob_dt = dob_dt.replace(hour=int(hh), minute=int(mm))
                except Exception: pass
                out["prenatal_eclipses"] = prenatal_eclipses(dob_dt)
        except Exception as e:
            out["prenatal_error"] = str(e)
    # Fixed stars expanded
    out["fixed_stars_expanded"] = fixed_stars_expanded_overlap(planets)
    return out


def format_phase_h_summary(result: dict) -> str:
    if not result or not result.get("available"):
        return f"▸ PHASE H TRANSITS-ECLIPSES: ❌ {result.get('reason','n/a') if result else 'n/a'}"
    lines = ["▸ PHASE H TRANSITS-ECLIPSES (Sprint-33): H2+H3+H6+H7+H8 expansion"]
    # H2 Jupiter
    j = result.get("jupiter_through_houses")
    if j:
        lines.append(f"  ── H2 JUPITER 12-yr cycle (currently {j['jupiter_sign']}) ──")
        lines.append(f"    From Lagna H{j['from_lagna']['house']} → {j['from_lagna']['verdict']}: {j['from_lagna']['detail']}")
        lines.append(f"    From Moon  H{j['from_moon']['house']} → {j['from_moon']['verdict']}: {j['from_moon']['detail']}")
    # H3 Rahu-Ketu
    rk = result.get("rahu_ketu_through_houses")
    if rk:
        lines.append(f"  ── H3 RAHU-KETU 18-month axis (Rahu={rk['rahu_sign']}, Ketu={rk['ketu_sign']}) ──")
        lines.append(f"    Rahu from Lagna H{rk['rahu_from_lagna']['house']} → {rk['rahu_from_lagna']['verdict']}: {rk['rahu_from_lagna']['detail']}")
        lines.append(f"    Rahu from Moon  H{rk['rahu_from_moon']['house']} → {rk['rahu_from_moon']['verdict']}: {rk['rahu_from_moon']['detail']}")
        lines.append(f"    Ketu from Lagna H{rk['ketu_from_lagna']['house']} → {rk['ketu_from_lagna']['verdict']}: {rk['ketu_from_lagna']['detail']}")
        lines.append(f"    Ketu from Moon  H{rk['ketu_from_moon']['house']} → {rk['ketu_from_moon']['verdict']}: {rk['ketu_from_moon']['detail']}")
    # H6 Saros
    s = result.get("saros_eclipses")
    if s and s.get("available"):
        lines.append(f"  ── H6 SAROS / Recent Eclipses ──")
        if s.get("solar_back"): lines.append(f"    Last Solar Eclipse: {s['solar_back']['date']} ({s['solar_back']['type']}, {s['solar_back']['days_ago']}d ago)")
        if s.get("solar_fwd"):  lines.append(f"    Next Solar Eclipse: {s['solar_fwd']['date']} ({s['solar_fwd']['type']}, {s['solar_fwd']['days_ahead']}d ahead)")
        if s.get("lunar_back"): lines.append(f"    Last Lunar Eclipse: {s['lunar_back']['date']} ({s['lunar_back']['type']})")
        if s.get("lunar_fwd"):  lines.append(f"    Next Lunar Eclipse: {s['lunar_fwd']['date']} ({s['lunar_fwd']['type']})")
        if s.get("saros_prev_solar"): lines.append(f"    Saros sibling (prev): {s['saros_prev_solar']}")
        if s.get("saros_next_solar"): lines.append(f"    Saros sibling (next): {s['saros_next_solar']}")
    # H7 Pre-natal
    pe = result.get("prenatal_eclipses")
    if pe and pe.get("available"):
        lines.append(f"  ── H7 PRE-NATAL ECLIPSE POINTS (sensitive degrees) ──")
        sol = pe.get("solar")
        if sol and "date" in sol:
            lines.append(f"    Pre-natal SOLAR: {sol['date']} ({sol['type']}) → sensitive {sol['sensitive_sign']} {sol['sensitive_lon']}° ({sol['days_before_birth']:.0f}d before birth)")
        lun = pe.get("lunar")
        if lun and "date" in lun:
            lines.append(f"    Pre-natal LUNAR: {lun['date']} ({lun['type']}) → sensitive {lun['sensitive_sign']} {lun['sensitive_lon']}° ({lun['days_before_birth']:.0f}d before birth)")
    # H8 Fixed stars expansion
    fx = result.get("fixed_stars_expanded")
    if fx:
        lines.append(f"  ── H8 FIXED STARS EXPANDED ({fx['expanded_catalog_size']} stars: 27 Yogatara + Abhijit + 4 Western) ──")
        if fx.get("overlaps_count"):
            for o in fx["overlaps"][:8]:
                lines.append(f"    ★ {o['planet']} on {o['star']} [{o['orb_deg']}°] — {o['meaning']}")
        else:
            lines.append(f"    No natal planets within 1° orb of expanded star catalog")
    return "\n".join(lines)

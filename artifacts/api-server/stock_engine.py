"""
stock_engine.py — Deterministic stock-market verdict engine (Vedic).

Mirror of marriage_engine.py architecture: pure-Python rule engine that
consumes the already-computed kundli + chart_intelligence + KP outputs
and produces a structured stock-market verdict BEFORE the AI is invoked.
The AI then acts purely as a narrator that converts this verdict into
Hinglish prose — it MUST NOT change verdict, score, timing, strategy,
sectors, or remedy.

Inputs:
    kundli  : dict from kundli_engine.calculate_kundli (has planets, dashas,
              currentDasha, ascendant, moonSign, divisionalCharts D2/D9/D10)
    intel   : dict from chart_intelligence.analyze_chart (has dignities,
              house_lords, yogas, mangal_dosh, sade_sati, lagna_sign)
    kp      : dict from kp_engine.calculate_kp (has cusps, planets,
              significations) — for KP cuspal sub-lord cross-check
    birth   : optional dict — surfaces "gender" if needed for narration
    question: optional raw user text — drives the question classifier
              (suitability / outcome / timing / strategy / sector /
              instrument-risk / career / loss-recovery / partnership /
              real-time). Different categories activate different
              conditional layers (D10, Hora-Lagna, Yogi, Tara/Chandra Bala,
              sector-mapping, prashna).

Output: see assess_stock().__doc__

Logic Framework (2-step):
    A. NATAL PROMISE (Layers 1-15) — does the chart promise stock-wealth at all?
        L1  5th-house deep dive            (weight 18)  ⭐ CORE
        L2  11th-house deep dive           (weight 14)  ⭐ CORE
        L3  KP cuspal sub-lord 2/5/8/11    (weight 12)
        L4  Mercury deep dive              (weight  8)
        L5  8th house (sudden gain/loss)   (weight  7)
        L6  Ashtakavarga 2/5/8/11          (weight  6)
        L7  9th-house bhagya               (weight  5)
        L8  Wealth yogas                   (weight  5)
        L9  Daridra/loss yogas             (weight -5 negative)
        L10 D9 sustained strength          (weight  5)
        L11 2nd-house accumulation         (weight  4)
        L12 Jupiter deep dive              (weight  4)
        L13 Rahu deep dive                 (weight  4)
        L14 D2 Hora wealth chart           (weight  2)
        L15 Moon (trader psychology)       (weight  2)
    B. CURRENT TRIGGER (Layers 16-17) — is that promise ACTIVATED right now?
        L16 Vimshottari MD+AD+PD timing    (weight 10)
        L17 Live Jupiter/Saturn transit    (weight  5)
    C. MODIFIERS — 7 modifiers (±points, no own weight)
        M1  Bhava Bala 2/5/8/11            (±5)
        M2  Shadbala Mercury/Jup/dhanesh   (±5)
        M3  Combust+Retrograde flags       (±5)
        M4  Lagnesh strength               (±3)
        M5  Mahapurusha + Neecha-bhanga    (+5)
        M6  Saturn-Mars angle (volatility) (±3)
        M7  6/8/12 lord influence on 2/5/11 (±3)
    D. CONDITIONAL (only when question type matches)
        C1  D10 Dasamsha (career-trader Q)
        C4  Sector-Planet mapping (sector Q via _recommend_sectors)
NOTE: Live transit (Jupiter & Saturn current sign) attempted via transit_engine
if available — safe-failing.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Optional

# ── Constants ────────────────────────────────────────────────────────────────
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORDS_LIST = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]
SIGN_LORDS = {SIGNS[i]: SIGN_LORDS_LIST[i] for i in range(12)}

DIGNITY_RANK = {
    "debilitated": 0, "enemy-sign": 1, "neutral-sign": 2,
    "friend-sign": 3, "own-sign": 4, "moolatrikona": 5, "exalted": 6,
}
DIGNITY_PTS = {  # used to convert dignity to a ±score component
    "debilitated": -8, "enemy-sign": -4, "neutral-sign": 0,
    "friend-sign": +3, "own-sign": +6, "moolatrikona": +7, "exalted": +8,
}

NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}
TRINE_KENDRA = {1, 4, 5, 7, 9, 10}
DUSTHANA = {6, 8, 12}
WEALTH_HOUSES = {2, 5, 11}
SPECULATION_PROMISE = {2, 5, 11}             # KP rule for 5th cusp
SPECULATION_DENIAL  = {1, 4, 8, 10, 12}
WEALTH_PROMISE      = {2, 6, 10, 11}         # KP rule for 2nd / 11th cusp
WEALTH_DENIAL       = {8, 12}
F_O_PROMISE         = {2, 8, 11}             # KP rule for 8th cusp (sudden)
F_O_DENIAL          = {6, 12}

# Sector → planet mapping (BPHS + traditional Vedic — used for sector questions)
PLANET_SECTORS = {
    "Sun":      ["PSU", "Government", "Energy/Power", "Gold/precious metals"],
    "Moon":     ["FMCG", "Dairy/beverages", "Hospitality", "Water/marine"],
    "Mars":     ["Defence", "Real estate", "Metals/steel", "Energy"],
    "Mercury":  ["IT/software", "Telecom", "Education", "Brokerage/media"],
    "Jupiter":  ["Banking/finance", "Pharma", "Education", "Insurance"],
    "Venus":    ["Auto", "Luxury/jewellery", "Entertainment/media", "Hotels"],
    "Saturn":   ["Mining/oil", "Infrastructure", "Iron/steel", "Agriculture"],
    "Rahu":     ["Crypto/digital", "Biotech", "Foreign stocks", "Electronics/aviation"],
    "Ketu":     ["Spirituality/occult", "Hidden tech", "Pharma research"],
}

# One-line emergency fallback (used only if remedies.py unavailable)
_FALLBACK_REMEDY = (
    'Lakshmi-Narayan ki daily upasana karein, Shukravar ko chandi (silver) ka daan'
)

# Day-name → Hindi vaar (for narration)
_DAY_HI = {
    "Sunday":    "Ravivar",  "Monday":   "Somvar",   "Tuesday":  "Mangalvar",
    "Wednesday": "Budhvar",  "Thursday": "Guruvar",  "Friday":   "Shukravar",
    "Saturday":  "Shanivar",
}

_MONTHS = ["", "January","February","March","April","May","June",
              "July","August","September","October","November","December"]


# ─────────────────────────────────────────────────────────────────────────────
# REMEDY LOOKUP (single source = remedies._REMEDY_TABLE)
# ─────────────────────────────────────────────────────────────────────────────
def _remedy_for_planet(planet: str) -> str:
    """One-line stock-narration remedy from canonical remedies._REMEDY_TABLE."""
    try:
        from remedies import _REMEDY_TABLE  # type: ignore
    except Exception:
        return _FALLBACK_REMEDY
    entry = _REMEDY_TABLE.get(planet)
    if not isinstance(entry, dict):
        return _FALLBACK_REMEDY
    mantra   = entry.get("mantra")  or {}
    charity  = entry.get("charity") or []
    trans    = mantra.get("transliteration") or ""
    count    = mantra.get("count") or 108
    day_en   = (mantra.get("day") or "").split(" ")[0]
    day_hi   = _DAY_HI.get(day_en, day_en or "is din")
    daan     = (charity[0].lower() if charity else "appropriate items")
    if not trans:
        return _FALLBACK_REMEDY
    return (
        f'{day_hi} ({day_en}) ko {count} baar "{trans}" jaap karein, '
        f'{daan} ka daan'
    )


# ─────────────────────────────────────────────────────────────────────────────
# QUESTION CLASSIFIER (10 categories) — drives conditional-layer activation
# ─────────────────────────────────────────────────────────────────────────────
_Q_PATTERNS = [
    # (category, list of regex patterns)
    ("real_time",  [r"\b(yeh|this|abhi|right now)\b.*\b(stock|share|nifty|sensex|symbol|company)\b",
                    r"\b(should i buy|kya khareedu|kya bechu)\b.*\b(stock|share)\b.*\b(now|abhi)\b"]),
    ("intraday",   [r"\b(intraday|day trading|day-trading|aaj|today)\b.*\b(trade|trading|stock|share)\b",
                    r"\b(scalping|scalper)\b"]),
    ("loss_recovery", [r"\b(loss|nuksaan|nuksan|ghata|recover|recovery)\b.*\b(stock|share|trade|market|invest)\b",
                       r"\b(stock|share|trade|market)\b.*\b(loss|nuksaan|recover)"]),
    ("career",     [r"\b(career|profession|kaam|naukri|job)\b.*\b(trader|trading|stock|broker)\b",
                    r"\b(trader|broker|stock|share)\b.*\b(career|profession|ban sakta|ban sakti|future)\b",
                    r"\b(full[- ]time|fulltime)\b.*\b(trader|trading)\b"]),
    ("partnership",[r"\b(partner|partnership|joint|saath|saathi|family)\b.*\b(trade|trading|stock|invest)\b"]),
    ("instrument_risk", [r"\b(crypto|bitcoin|ethereum|dogecoin|nft)\b",
                         r"\b(f&o|fno|futures|options|derivative|leverage|margin|intraday[- ]leverage)\b",
                         r"\b(short[- ]selling|hedging)\b"]),
    ("sector",     [r"\b(kis sector|which sector|sector|industry|kaunsi industry)\b",
                    r"\b(it|pharma|banking|gold|real estate|fmcg|psu|defence|crypto|auto|metal)\b.*\b(invest|stock|sector|sahi|theek)\b"]),
    ("strategy",   [r"\b(long[- ]term|short[- ]term|swing|sip|mutual fund|lump sum|systematic)\b",
                    r"\b(strategy|tarika|tareeka|kaisa kare|kaise invest)\b"]),
    ("timing",     [r"\b(kab|when)\b.*\b(invest|enter|exit|buy|sell|sip|stock|trade|market)\b",
                    r"\b(time|samay|window|period)\b.*\b(invest|trade|stock|market)\b",
                    r"\b(book profit|profit book|sell|exit)\b.*\b(kab|when)\b"]),
    ("outcome",    [r"\b(profit|munafa|gain|loss|nuksaan|loss-profit)\b.*\b(hoga|hogi|milega|milegi|aayega)\b",
                    r"\b(stock|share|trade|invest)\b.*\b(profit|loss|munafa|nuksaan)"]),
    # SUITABILITY = the catch-all default (no pattern needed; assigned if nothing else matches)
]


def classify_stock_question(text: str) -> str:
    """Return one of: real_time | intraday | loss_recovery | career |
    partnership | instrument_risk | sector | strategy | timing | outcome |
    suitability (default).
    Order of patterns matters — most specific first."""
    if not isinstance(text, str) or not text.strip():
        return "suitability"
    s = text.lower().strip()
    for category, pats in _Q_PATTERNS:
        for pat in pats:
            try:
                if re.search(pat, s):
                    return category
            except re.error:
                continue
    return "suitability"


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _sign_idx(sign_name: Any) -> Optional[int]:
    if not isinstance(sign_name, str):
        return None
    try:
        return SIGNS.index(sign_name.strip().capitalize())
    except ValueError:
        return None


def _safe_iso_date(s: Any) -> Optional[datetime]:
    if not isinstance(s, str) or not s:
        return None
    try:
        return datetime.fromisoformat(s.split("T")[0])
    except Exception:
        return None


def _ym_to_human(ym: str) -> str:
    try:
        y, m = (ym or "").split("-")[:2]
        return f"{_MONTHS[int(m)]} {y}"
    except Exception:
        return ym or "?"


def _planet_in_house(pname: str, pmap: dict) -> Optional[int]:
    info = pmap.get(pname) or {}
    h = info.get("house")
    return h if isinstance(h, int) else None


def _planet_dignity(pname: str, dignities: dict) -> dict:
    return dignities.get(pname) or {}


def _significators_of(houses_set: set, sigs: dict) -> set:
    out = set()
    for pname, sig in (sigs or {}).items():
        bag = (set(sig.get("pl") or [])
               | set(sig.get("sb_houses") or [])
               | set(sig.get("ss_houses") or [])
               | set(sig.get("sl") or []))
        if bag & houses_set:
            out.add(pname)
    return out


def _signifies(planet: str, houses_set: set, sigs: dict) -> bool:
    sig = (sigs or {}).get(planet) or {}
    bag = (set(sig.get("pl") or [])
           | set(sig.get("sb_houses") or [])
           | set(sig.get("ss_houses") or [])
           | set(sig.get("sl") or []))
    return bool(bag & houses_set)


# ─────────────────────────────────────────────────────────────────────────────
# LAZY MODULE LOADERS — every helper is best-effort (engine never crashes on
# missing optional inputs; degrades to lower-confidence verdict instead).
# ─────────────────────────────────────────────────────────────────────────────
def _maybe_shadbala(kundli: dict, lagna_sign_idx: Optional[int]) -> dict:
    if lagna_sign_idx is None:
        return {}
    try:
        from shadbala import compute_shadbala
        raw = (kundli or {}).get("planets") or []
        planets = []
        for p in raw:
            if not isinstance(p, dict):
                continue
            lon = p.get("lon", p.get("longitude"))
            if not isinstance(lon, (int, float)):
                continue
            planets.append({**p, "lon": float(lon)})
        moon = next((p for p in planets if p.get("name") == "Moon"), None)
        sun  = next((p for p in planets if p.get("name") == "Sun"),  None)
        moon_sun_angle = (moon["lon"] - sun["lon"]) % 360.0 if (moon and sun) else None
        return compute_shadbala(planets, lagna_sign_idx, moon_sun_angle) or {}
    except Exception as e:
        return {"_error": str(e)}


def _maybe_ashtakavarga(kundli: dict, lagna_sign_idx: Optional[int]) -> dict:
    if lagna_sign_idx is None:
        return {}
    try:
        from ashtakavarga import compute_ashtakavarga
        return compute_ashtakavarga(kundli.get("planets") or [], lagna_sign_idx) or {}
    except Exception as e:
        return {"_error": str(e)}


def _maybe_arudha(kundli: dict) -> dict:
    try:
        from jaimini import compute_arudha_padas  # type: ignore
        lg = kundli.get("ascendant")
        if isinstance(lg, dict):
            lg = lg.get("sign") or lg.get("name")
        return compute_arudha_padas(kundli.get("planets") or [], lg) or {}
    except Exception as e:
        return {"_error": str(e)}


def _maybe_karakas(kundli: dict) -> dict:
    try:
        from karakas import compute_karakas  # type: ignore
        return compute_karakas(kundli.get("planets") or []) or {}
    except Exception as e:
        return {"_error": str(e)}


def _maybe_varga_yogas(kundli: dict, lagna_lon: Optional[float]) -> dict:
    try:
        from varga_yogas import detect_all_varga_yogas  # type: ignore
        return detect_all_varga_yogas(kundli.get("planets") or [], lagna_lon, kundli) or {}
    except Exception as e:
        return {"_error": str(e)}


def _maybe_argala(kundli: dict) -> dict:
    try:
        from argala import compute_argala  # type: ignore
        lg = kundli.get("ascendant")
        if isinstance(lg, dict):
            lg = lg.get("sign") or lg.get("name")
        return compute_argala(kundli.get("planets") or [], lg) or {}
    except Exception as e:
        return {"_error": str(e)}


def _maybe_jupiter_transit(lagna_sign_idx: Optional[int]) -> dict:
    """Jupiter sign-changes over 3 years — reused from transit_engine."""
    if lagna_sign_idx is None:
        return {}
    try:
        from transit_engine import jupiter_sign_changes  # type: ignore
        return {
            "jupiter_changes": jupiter_sign_changes(datetime.utcnow(), years_ahead=3) or [],
        }
    except Exception as e:
        return {"_error": str(e)}


def _maybe_saturn_transit() -> dict:
    """Saturn current sign + ~7-year stay — best-effort via swisseph if available."""
    try:
        import swisseph as swe  # type: ignore
        jd = swe.julday(datetime.utcnow().year,
                        datetime.utcnow().month,
                        datetime.utcnow().day, 0)
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        sat_lon = swe.calc_ut(jd, swe.SATURN, flags)[0][0] % 360.0
        return {
            "saturn_lon":  round(sat_lon, 4),
            "saturn_sign": SIGNS[int(sat_lon // 30) % 12],
            "saturn_sign_idx": int(sat_lon // 30) % 12,
        }
    except Exception as e:
        return {"_error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# DASHA — Vimshottari MD/AD/PD scanner (next favourable wealth-house window)
# ─────────────────────────────────────────────────────────────────────────────
def _next_dasha_window(dashas: list, significators: set,
                       today: datetime,
                       max_years: int = 12) -> Optional[dict]:
    """First (Maha,Antar) future pair where MD or AD planet signifies the
    target houses. Mirror of marriage_engine logic for wealth houses."""
    horizon = today + timedelta(days=365.25 * max_years)
    for md in (dashas or []):
        md_end = _safe_iso_date(md.get("endDate") or "")
        if md_end and md_end < today:
            continue
        for ad in (md.get("subDashas") or []):
            ad_end = _safe_iso_date(ad.get("endDate") or "")
            ad_start = _safe_iso_date(ad.get("startDate") or "")
            if not ad_end or ad_end < today:
                continue
            if ad_start and ad_start > horizon:
                break
            mp = md.get("planet"); ap = ad.get("planet")
            if mp in significators or ap in significators:
                start = (ad.get("startDate") or "")[:7]
                end   = (ad.get("endDate") or "")[:7]
                if mp in significators and ap in significators:
                    why = f"both {mp} (Mahadasha) and {ap} (Antardasha) signify wealth houses 2/5/11"
                elif mp in significators:
                    why = f"{mp} (Mahadasha) signifies wealth houses 2/5/11"
                else:
                    why = f"{ap} (Antardasha) signifies wealth houses 2/5/11"
                return {"dasha": f"{mp}-{ap}", "start": start, "end": end, "reason": why}
    return None


def _next_pratyantar_window(dashas: list, significators: set,
                            today: datetime, max_months: int = 18) -> Optional[dict]:
    """First (MD,AD,PD) future triplet — short-term timing (weeks/days)
    used for swing/intraday questions. Returns None if no PD data present."""
    horizon = today + timedelta(days=30 * max_months)
    for md in (dashas or []):
        for ad in (md.get("subDashas") or []):
            for pd in (ad.get("subSubDashas") or []):
                pd_end = _safe_iso_date(pd.get("endDate") or "")
                pd_start = _safe_iso_date(pd.get("startDate") or "")
                if not pd_end or pd_end < today:
                    continue
                if pd_start and pd_start > horizon:
                    break
                mp, ap, pp = md.get("planet"), ad.get("planet"), pd.get("planet")
                if mp in significators or ap in significators or pp in significators:
                    start = (pd.get("startDate") or "")[:10]
                    end   = (pd.get("endDate") or "")[:10]
                    return {"dasha": f"{mp}-{ap}-{pp}",
                            "start": start, "end": end,
                            "reason": f"PD {pp} (within {mp}-{ap}) signifies wealth houses"}
    return None


# ─────────────────────────────────────────────────────────────────────────────
# DIVISIONAL CHARTS — D9 / D10 / D2 helpers
# ─────────────────────────────────────────────────────────────────────────────
def _planet_in_d_chart(d_chart: dict, planet: str) -> dict:
    if not isinstance(d_chart, dict):
        return {}
    for p in d_chart.get("planets") or []:
        if isinstance(p, dict) and p.get("name") == planet:
            return p
    return {}


def _d9_strength(planet: str, kundli: dict) -> dict:
    """Return {sign, house, vargottama:bool} for a planet in D9."""
    d9 = ((kundli or {}).get("divisionalCharts") or {}).get("D9") or {}
    p9 = _planet_in_d_chart(d9, planet)
    if not p9:
        return {}
    d1 = next((x for x in (kundli.get("planets") or [])
               if isinstance(x, dict) and x.get("name") == planet), {})
    is_varg = (d1.get("sign") and p9.get("sign") and d1["sign"] == p9["sign"])
    sign = p9.get("sign")
    house = p9.get("house")
    sign_lord = SIGN_LORDS.get(sign) if sign else None
    own = (sign_lord == planet)
    return {
        "sign": sign, "house": house,
        "vargottama": bool(is_varg),
        "own_sign_in_d9": bool(own),
        "in_dusthana": (house in DUSTHANA) if isinstance(house, int) else False,
        "in_kendra_trikona": (house in TRINE_KENDRA) if isinstance(house, int) else False,
    }


def _d10_check(kundli: dict, intel: dict) -> dict:
    """Trader-career fit from D10 Dasamsha."""
    d10 = ((kundli or {}).get("divisionalCharts") or {}).get("D10") or {}
    if not d10:
        return {}
    asc_idx = d10.get("ascendantSignIndex")
    if asc_idx is None:
        return {}
    d10_lord_sign = SIGNS[int(asc_idx)]
    pmap10 = {p.get("name"): p for p in (d10.get("planets") or []) if isinstance(p, dict)}
    mer = pmap10.get("Mercury") or {}
    rah = pmap10.get("Rahu") or {}
    jup = pmap10.get("Jupiter") or {}
    return {
        "d10_lagna":     d10_lord_sign,
        "mercury_house": mer.get("house"),
        "mercury_sign":  mer.get("sign"),
        "rahu_house":    rah.get("house"),
        "jupiter_house": jup.get("house"),
        "trader_fit_signal": (
            (mer.get("house") in TRINE_KENDRA) and
            (rah.get("house") in {3, 5, 11})  # Rahu in upachaya from D10 lagna
        ),
    }


def _d2_hora_check(kundli: dict) -> dict:
    """D2 Hora wealth chart — counts planets in Sun's hora vs Moon's hora.
    Wealth gravitates toward whichever hora hosts the most natural benefics
    (BPHS Ch. 7)."""
    d2 = ((kundli or {}).get("divisionalCharts") or {}).get("D2") or {}
    if not d2:
        return {}
    sun_hora_count = 0
    moon_hora_count = 0
    benefic_in_moon = 0
    for p in d2.get("planets") or []:
        if not isinstance(p, dict):
            continue
        sign = p.get("sign")
        # Sun's hora = Leo (Sun own); Moon's hora = Cancer (Moon own).
        # Per BPHS D2 each sign maps to either Sun or Moon hora based on
        # odd/even and degree split. The compute_d2 module already places
        # planets in the correct hora-sign — Cancer = Moon, Leo = Sun.
        if sign == "Leo":
            sun_hora_count += 1
        elif sign == "Cancer":
            moon_hora_count += 1
            if p.get("name") in NATURAL_BENEFICS:
                benefic_in_moon += 1
    return {
        "sun_hora_planets":  sun_hora_count,
        "moon_hora_planets": moon_hora_count,
        "moon_hora_benefics": benefic_in_moon,
        "wealth_orientation": (
            "Lakshmi/Moon-hora — wealth via stable accumulation"
            if moon_hora_count >= sun_hora_count
            else "Vishnu/Sun-hora — wealth via authority/active effort"
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 1 — 5th House Deep Dive (12 sub-checks, weight 18)
# ─────────────────────────────────────────────────────────────────────────────
def _layer_5th_house(intel: dict, kundli: dict, kp_sigs: dict) -> dict:
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    dignities   = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    pmap        = {p.get("name"): p for p in (kundli.get("planets") or [])}
    h5 = house_lords.get(5) or {}
    fifth_lord = h5.get("lord") or ""
    fl_dig_e = dignities.get(fifth_lord) or {}
    fl_dig   = fl_dig_e.get("dignity") or "neutral-sign"
    fl_house = (pmap.get(fifth_lord) or {}).get("house")
    fl_combust = bool(fl_dig_e.get("combust"))
    fl_retro   = bool(fl_dig_e.get("retro"))

    # Occupants of 5th
    occ5 = [d.get("planet") for d in (intel.get("dignities") or [])
            if d.get("house") == 5 and d.get("planet")]
    benefic_in_5 = [p for p in occ5 if p in NATURAL_BENEFICS]
    malefic_in_5 = [p for p in occ5 if p in NATURAL_MALEFICS]

    # 5L ↔ 11L relation (THE classical Speculation Gains Yoga)
    eleventh_lord = (house_lords.get(11) or {}).get("lord") or ""
    el_house = (pmap.get(eleventh_lord) or {}).get("house")
    speculation_yoga = False
    why_yoga = ""
    if fifth_lord and eleventh_lord:
        # Conjunction (same house)
        if fl_house == el_house and fl_house is not None:
            speculation_yoga = True
            why_yoga = (f"5L {fifth_lord} + 11L {eleventh_lord} conjunct in "
                        f"H{fl_house} — Speculation Gains Yoga")
        # Mutual sign exchange (parivartana)
        elif fl_dig_e.get("sign") and (dignities.get(eleventh_lord) or {}).get("sign"):
            fl_sign  = fl_dig_e.get("sign")
            el_sign  = (dignities.get(eleventh_lord) or {}).get("sign")
            if SIGN_LORDS.get(fl_sign) == eleventh_lord and SIGN_LORDS.get(el_sign) == fifth_lord:
                speculation_yoga = True
                why_yoga = (f"5L {fifth_lord} ↔ 11L {eleventh_lord} parivartana — "
                            f"strong Speculation Gains Yoga")

    # KP 5th-cusp sub-lord verdict (cross-check)
    kp5_verdict, kp5_reason = "unknown", ""
    fifth_cusp_sl = ""
    if kp_sigs:
        # signified houses for any planet acting as 5th cusp SL — caller passes us
        # the signification dict only; we re-check against PROMISE/DENIAL sets in
        # the dedicated KP layer. Here we just record placeholder.
        pass

    # 5L in dusthana (6/8/12) = avoid speculation
    fl_in_dusthana = (fl_house in DUSTHANA) if isinstance(fl_house, int) else False
    fl_in_kendra_trikona = (fl_house in TRINE_KENDRA) if isinstance(fl_house, int) else False

    # Aspects on 5th house — Jupiter aspect = wisdom; Saturn = caution; Rahu = risky
    asp_on_5 = []
    for d in (intel.get("dignities") or []):
        if 5 in (d.get("aspects_houses") or []) and d.get("planet"):
            asp_on_5.append(d.get("planet"))
    jup_asp_5 = "Jupiter" in asp_on_5
    sat_asp_5 = "Saturn" in asp_on_5
    rah_asp_5 = "Rahu"   in asp_on_5
    mar_asp_5 = "Mars"   in asp_on_5

    # 5th from Moon (emotional speculation tendency)
    moon = pmap.get("Moon") or {}
    moon_house = moon.get("house")
    moon_5_house = ((moon_house - 1 + 4) % 12 + 1) if isinstance(moon_house, int) else None

    # ── Score this layer (target weight: 18) ─────────────────────────────────
    s = 0
    why_strong, why_weak = [], []

    # 1. 5L dignity
    s += DIGNITY_PTS.get(fl_dig, 0)
    if fl_dig in ("exalted", "moolatrikona", "own-sign"):
        why_strong.append(f"5L {fifth_lord} {fl_dig} — speculation karaka strong")
    elif fl_dig in ("debilitated", "enemy-sign"):
        why_weak.append(f"5L {fifth_lord} {fl_dig} — speculation house weak")

    # 2. 5L placement
    if fl_in_kendra_trikona:
        s += 3; why_strong.append(f"5L {fifth_lord} in kendra/trikona (H{fl_house})")
    elif fl_in_dusthana:
        s -= 5; why_weak.append(f"5L {fifth_lord} in dusthana H{fl_house} — AVOID speculation")

    # 3. Combust / retro
    if fl_combust:
        s -= 3; why_weak.append(f"5L {fifth_lord} combust — judgment errors in speculation")
    if fl_retro:
        s -= 1; why_weak.append(f"5L {fifth_lord} retrograde — speculation reversals")

    # 4. Occupants
    if benefic_in_5:
        s += min(4, 2 * len(benefic_in_5))
        why_strong.append(f"Benefic(s) {benefic_in_5} occupy 5th — favourable for speculation")
    if malefic_in_5:
        # malefic in 5th is bad UNLESS dignified
        bad_malefic = []
        for m in malefic_in_5:
            mdig = (dignities.get(m) or {}).get("dignity")
            if mdig in ("debilitated", "enemy-sign", "neutral-sign"):
                bad_malefic.append(m)
        if bad_malefic:
            s -= min(4, 2 * len(bad_malefic))
            why_weak.append(f"Undignified malefic(s) {bad_malefic} in 5th — speculation losses")

    # 5. Speculation Gains Yoga (5L↔11L)
    if speculation_yoga:
        s += 6; why_strong.append(why_yoga)

    # 6-9. Aspects on 5th
    if jup_asp_5:
        s += 2; why_strong.append("Jupiter aspects 5th — wisdom in speculation")
    if sat_asp_5:
        s -= 1; why_weak.append("Saturn aspects 5th — slow returns / caution")
    if rah_asp_5:
        # Rahu aspect: high-stakes bias, not pure negative
        why_strong.append("Rahu aspects 5th — high-stakes/F&O bias (handle with discipline)")
    if mar_asp_5:
        why_weak.append("Mars aspects 5th — aggressive, impulsive trades")

    # Cap the layer-net contribution near its rubric weight (±18)
    s = max(-18, min(18, s))
    return {
        "fifth_lord":         fifth_lord,
        "fifth_lord_dignity": fl_dig,
        "fifth_lord_house":   fl_house,
        "fifth_lord_combust": fl_combust,
        "fifth_lord_retro":   fl_retro,
        "occupants":          occ5,
        "speculation_gains_yoga": speculation_yoga,
        "speculation_yoga_reason": why_yoga,
        "aspects_on_5th":     asp_on_5,
        "jup_aspect_5":       jup_asp_5,
        "sat_aspect_5":       sat_asp_5,
        "rah_aspect_5":       rah_asp_5,
        "moon_5_house":       moon_5_house,
        "score":              s,
        "why_strong":         why_strong,
        "why_weak":           why_weak,
    }


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2 — 11th House Deep Dive (12 sub-checks, weight 14)
# ─────────────────────────────────────────────────────────────────────────────
def _layer_11th_house(intel: dict, kundli: dict) -> dict:
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    dignities   = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    pmap        = {p.get("name"): p for p in (kundli.get("planets") or [])}
    h11 = house_lords.get(11) or {}
    eleventh_lord = h11.get("lord") or ""
    el_dig_e = dignities.get(eleventh_lord) or {}
    el_dig   = el_dig_e.get("dignity") or "neutral-sign"
    el_house = (pmap.get(eleventh_lord) or {}).get("house")
    el_combust = bool(el_dig_e.get("combust"))
    el_retro   = bool(el_dig_e.get("retro"))

    occ11 = [d.get("planet") for d in (intel.get("dignities") or [])
             if d.get("house") == 11 and d.get("planet")]
    benefic_in_11 = [p for p in occ11 if p in NATURAL_BENEFICS]
    malefic_in_11 = [p for p in occ11 if p in NATURAL_MALEFICS]
    # Malefics IN 11th are GOOD per BPHS upachaya rule (gain from struggle).

    # 11L ↔ 2L relation (Dhana Yoga of accumulation)
    second_lord = (house_lords.get(2) or {}).get("lord") or ""
    sl2_house = (pmap.get(second_lord) or {}).get("house")
    dhana_yoga = False
    why_yoga = ""
    if eleventh_lord and second_lord:
        if el_house == sl2_house and el_house is not None:
            dhana_yoga = True
            why_yoga = (f"11L {eleventh_lord} + 2L {second_lord} conjunct in "
                        f"H{el_house} — Dhana Yoga of accumulation")
        else:
            # Parivartana
            el_sign = el_dig_e.get("sign")
            sl2_sign = (dignities.get(second_lord) or {}).get("sign")
            if el_sign and sl2_sign and SIGN_LORDS.get(el_sign) == second_lord and SIGN_LORDS.get(sl2_sign) == eleventh_lord:
                dhana_yoga = True
                why_yoga = (f"11L {eleventh_lord} ↔ 2L {second_lord} parivartana "
                            f"— powerful Dhana Yoga")

    el_in_dusthana = (el_house in DUSTHANA) if isinstance(el_house, int) else False
    el_in_kendra_trikona = (el_house in TRINE_KENDRA) if isinstance(el_house, int) else False

    asp_on_11 = [d.get("planet") for d in (intel.get("dignities") or [])
                 if 11 in (d.get("aspects_houses") or []) and d.get("planet")]
    jup_asp_11 = "Jupiter" in asp_on_11

    s = 0
    why_strong, why_weak = [], []

    s += DIGNITY_PTS.get(el_dig, 0)
    if el_dig in ("exalted", "moolatrikona", "own-sign"):
        why_strong.append(f"11L {eleventh_lord} {el_dig} — gains-house lord powerful")
    elif el_dig in ("debilitated", "enemy-sign"):
        why_weak.append(f"11L {eleventh_lord} {el_dig} — gains-house weak")

    if el_in_kendra_trikona:
        s += 3; why_strong.append(f"11L {eleventh_lord} in kendra/trikona (H{el_house})")
    elif el_in_dusthana:
        s -= 4; why_weak.append(f"11L {eleventh_lord} in dusthana H{el_house} — gains blocked")

    if el_combust:
        s -= 2; why_weak.append(f"11L {eleventh_lord} combust — gains delayed")

    if benefic_in_11:
        s += min(3, 2 * len(benefic_in_11))
        why_strong.append(f"Benefic(s) {benefic_in_11} in 11th — clean gains")
    if malefic_in_11:
        # Per BPHS, malefics in 11 are an upachaya boost
        s += min(2, 1 * len(malefic_in_11))
        why_strong.append(f"Malefic(s) {malefic_in_11} in 11 (upachaya) — gains via effort/struggle")

    if dhana_yoga:
        s += 5; why_strong.append(why_yoga)
    if jup_asp_11:
        s += 2; why_strong.append("Jupiter aspects 11th — expanded gains potential")

    s = max(-14, min(14, s))
    return {
        "eleventh_lord":         eleventh_lord,
        "eleventh_lord_dignity": el_dig,
        "eleventh_lord_house":   el_house,
        "occupants":             occ11,
        "dhana_yoga_2_11":       dhana_yoga,
        "dhana_yoga_reason":     why_yoga,
        "aspects_on_11th":       asp_on_11,
        "jup_aspect_11":         jup_asp_11,
        "score":                 s,
        "why_strong":            why_strong,
        "why_weak":              why_weak,
    }


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 3 — KP Cuspal Sub-Lord (2/5/8/11 with 4 levels SL/NL/SB/SS, weight 12)
# ─────────────────────────────────────────────────────────────────────────────
def _layer_kp_cuspal(kp: dict) -> dict:
    """KP cuspal sub-lord rule for the four wealth cusps (2, 5, 8, 11).
    Each cusp's sub-lord must signify its event-house set (PROMISE) and not
    only the denial-house set. Returns per-cusp verdict + score.
    """
    if not kp:
        return {"score": 0, "available": False}

    cusps = {c.get("house"): c for c in (kp.get("cusps") or []) if isinstance(c, dict)}
    sigs  = kp.get("significations") or {}

    cusp_targets = {
        2:  (WEALTH_PROMISE,      WEALTH_DENIAL,      "wealth/accumulation"),
        5:  (SPECULATION_PROMISE, SPECULATION_DENIAL, "speculation/share-market"),
        8:  (F_O_PROMISE,         F_O_DENIAL,         "sudden-gain / F&O"),
        11: (WEALTH_PROMISE,      WEALTH_DENIAL,      "gains/profits"),
    }

    by_cusp = {}
    s = 0
    why_strong, why_weak = [], []
    for h, (promise, denial, label) in cusp_targets.items():
        c = cusps.get(h)
        if not c:
            continue
        sb = c.get("sb") or ""
        sb_sig = sigs.get(sb) or {}
        sb_houses = (set(sb_sig.get("sb_houses") or [])
                     | set(sb_sig.get("pl") or [])
                     | set(sb_sig.get("ss_houses") or []))
        promise_hit = sb_houses & promise
        denial_hit  = sb_houses & denial
        if promise_hit:
            verdict = "promised"
            reason  = (f"Cusp {h} ({label}) Sub-Lord {sb} signifies houses "
                       f"{sorted(promise_hit)} (in PROMISE set) — KP CONFIRMS")
            s += 3; why_strong.append(reason)
        elif denial_hit and not promise_hit:
            verdict = "denied"
            reason  = (f"Cusp {h} ({label}) Sub-Lord {sb} signifies only houses "
                       f"{sorted(denial_hit)} (in DENIAL set) — KP DENIES")
            s -= 4; why_weak.append(reason)
        else:
            verdict = "ambiguous"
            reason  = (f"Cusp {h} ({label}) Sub-Lord {sb} signifies "
                       f"{sorted(sb_houses) or 'no clear'} houses — KP ambiguous")
        # 4-level chain for narration
        nl_lord = sb_sig.get("nl_lord") or ""
        ss_lord = sb_sig.get("ss_lord") or ""
        by_cusp[h] = {
            "label":    label,
            "sl":       c.get("sl"),
            "nl":       c.get("nl"),
            "sb":       sb,
            "ss":       c.get("ss"),
            "sb_nl_lord": nl_lord,
            "sb_ss_lord": ss_lord,
            "sb_signifies_houses": sorted(sb_houses),
            "verdict":  verdict,
            "reason":   reason,
        }

    s = max(-12, min(12, s))
    return {
        "available": True,
        "by_cusp":   by_cusp,
        "score":     s,
        "why_strong": why_strong,
        "why_weak":   why_weak,
    }


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 4 — Mercury Deep Dive (THE trader karaka, weight 8)
# ─────────────────────────────────────────────────────────────────────────────
def _layer_mercury(intel: dict, kundli: dict) -> dict:
    dignities = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    pmap = {p.get("name"): p for p in (kundli.get("planets") or [])}
    me = dignities.get("Mercury") or {}
    me_p = pmap.get("Mercury") or {}
    dig = me.get("dignity") or "neutral-sign"
    house = me.get("house")
    combust = bool(me.get("combust"))
    retro   = bool(me.get("retro"))
    aspects = me.get("aspects_houses") or []

    s = 0
    why_strong, why_weak = [], []

    s += DIGNITY_PTS.get(dig, 0) // 2  # half-weight (rubric: max ±8)
    if dig in ("exalted", "moolatrikona", "own-sign"):
        why_strong.append(f"Mercury {dig} — analytical & trading skill native")
    elif dig in ("debilitated", "enemy-sign"):
        why_weak.append(f"Mercury {dig} — judgment/calc errors in trading")

    if isinstance(house, int):
        if house in TRINE_KENDRA:
            s += 2; why_strong.append(f"Mercury in kendra/trikona H{house} — active in life")
        elif house in DUSTHANA:
            s -= 3; why_weak.append(f"Mercury in dusthana H{house} — trader effort blocked")
        if house in WEALTH_HOUSES:
            s += 2; why_strong.append(f"Mercury in wealth-house H{house} — direct trader-money link")

    if combust:
        s -= 3; why_weak.append("Mercury combust by Sun — judgment impaired in trades")
    if retro:
        # Retrograde Mercury can intensify analysis (introvert) but slow execution
        why_weak.append("Mercury retrograde — review trades, slow execution")

    # Mercury aspecting wealth houses
    aspect_wh = [h for h in aspects if h in WEALTH_HOUSES]
    if aspect_wh:
        s += 1; why_strong.append(f"Mercury aspects wealth house(s) {aspect_wh}")

    s = max(-8, min(8, s))
    return {
        "dignity": dig, "house": house, "combust": combust, "retro": retro,
        "score": s, "why_strong": why_strong, "why_weak": why_weak,
    }


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 5 — 8th House (sudden gain/loss + F&O, weight 7)
# ─────────────────────────────────────────────────────────────────────────────
def _layer_8th_house(intel: dict, kundli: dict) -> dict:
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    dignities   = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    pmap        = {p.get("name"): p for p in (kundli.get("planets") or [])}
    h8 = house_lords.get(8) or {}
    eighth_lord = h8.get("lord") or ""
    el_dig_e = dignities.get(eighth_lord) or {}
    el_dig   = el_dig_e.get("dignity") or "neutral-sign"
    el_house = (pmap.get(eighth_lord) or {}).get("house")

    occ8 = [d.get("planet") for d in (intel.get("dignities") or [])
            if d.get("house") == 8 and d.get("planet")]

    s = 0
    why_strong, why_weak = [], []

    # 8L well-placed = sudden gains possible
    if el_dig in ("exalted", "moolatrikona", "own-sign"):
        s += 3; why_strong.append(f"8L {eighth_lord} {el_dig} — sudden-gain potential")
    elif el_dig in ("debilitated", "enemy-sign"):
        s -= 3; why_weak.append(f"8L {eighth_lord} {el_dig} — sudden-LOSS risk in F&O")

    # Rahu in 8 = high-risk speculation; Ketu in 8 = sudden losses
    if "Rahu" in occ8:
        s += 1; why_strong.append("Rahu in 8th — sudden-wealth potential, but high volatility")
    if "Ketu" in occ8:
        s -= 3; why_weak.append("Ketu in 8th — sudden losses risk, AVOID F&O/leverage")

    # Lord of 8 in 11 = wealth via others' money/inheritance
    if isinstance(el_house, int) and el_house == 11:
        s += 2; why_strong.append(f"8L {eighth_lord} in 11th — gain from others' money (margin/options OK with caution)")
    if isinstance(el_house, int) and el_house in (1, 2, 5):
        s -= 2; why_weak.append(f"8L {eighth_lord} in H{el_house} — afflicts self/wealth/speculation")

    s = max(-7, min(7, s))
    return {
        "eighth_lord": eighth_lord, "eighth_lord_dignity": el_dig,
        "eighth_lord_house": el_house, "occupants": occ8,
        "score": s, "why_strong": why_strong, "why_weak": why_weak,
    }


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 6 — Ashtakavarga (weight 6) — BPHS quantitative threshold
# ─────────────────────────────────────────────────────────────────────────────
def _layer_ashtakavarga(av: dict) -> dict:
    if not av or "_error" in av:
        return {"score": 0, "available": False}
    sav = av.get("sav") or []  # 12-element list, 1-indexed offset
    s = 0
    why_strong, why_weak = [], []
    for h in (2, 5, 8, 11):
        try:
            v = int(sav[h - 1])
        except (IndexError, ValueError, TypeError):
            continue
        if v >= 30:
            s += 1; why_strong.append(f"H{h} SAV={v} (≥30) — strong wealth-house power")
        elif v <= 24:
            s -= 1; why_weak.append(f"H{h} SAV={v} (≤24) — weak, results muted")
    # Bonus: BAV of Mercury & Jupiter in their own houses
    bav = av.get("bav") or {}
    for planet in ("Mercury", "Jupiter"):
        bav_arr = bav.get(planet) or []
        for h in (2, 5, 11):
            try:
                if int(bav_arr[h - 1]) >= 5:
                    s += 0.5
            except (IndexError, ValueError, TypeError):
                continue
    s = max(-6, min(6, int(round(s))))
    return {"score": s, "available": True,
            "why_strong": why_strong, "why_weak": why_weak}


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 7 — 9th House Bhagya (luck factor, weight 5)
# ─────────────────────────────────────────────────────────────────────────────
def _layer_9th_house(intel: dict, kundli: dict) -> dict:
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    dignities   = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    pmap        = {p.get("name"): p for p in (kundli.get("planets") or [])}
    h9 = house_lords.get(9) or {}
    ninth_lord = h9.get("lord") or ""
    nl_dig = (dignities.get(ninth_lord) or {}).get("dignity") or "neutral-sign"
    nl_house = (pmap.get(ninth_lord) or {}).get("house")
    occ9 = [d.get("planet") for d in (intel.get("dignities") or [])
            if d.get("house") == 9 and d.get("planet")]

    s = 0
    why_strong, why_weak = [], []
    if nl_dig in ("exalted", "moolatrikona", "own-sign"):
        s += 3; why_strong.append(f"9L {ninth_lord} {nl_dig} — bhagya/luck strong")
    elif nl_dig in ("debilitated", "enemy-sign"):
        s -= 2; why_weak.append(f"9L {ninth_lord} {nl_dig} — luck factor weak in markets")
    if isinstance(nl_house, int) and nl_house in TRINE_KENDRA:
        s += 1
    if "Jupiter" in occ9:
        s += 2; why_strong.append("Jupiter in 9th — divine grace in financial decisions")
    s = max(-5, min(5, s))
    return {"ninth_lord": ninth_lord, "ninth_lord_dignity": nl_dig,
            "occupants": occ9, "score": s,
            "why_strong": why_strong, "why_weak": why_weak}


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 8 — Wealth Yogas (weight 5) | LAYER 9 — Daridra Yogas (weight -5)
# ─────────────────────────────────────────────────────────────────────────────
_WEALTH_YOGA_KEYS = ("lakshmi", "dhana", "chandra-mangal", "chandra mangal",
                     "maha lakshmi", "maha-lakshmi", "vasumati", "saraswati",
                     "amala", "adhi yoga", "dharma-karmadhipati", "raja",
                     "neech-bhanga", "vipareeta-raja",
                     "gajakesari", "budhaditya")
_DARIDRA_KEYS    = ("daridra", "kemadruma", "papa-kartari")


def _layer_wealth_yogas(intel: dict) -> dict:
    yogas = intel.get("yogas") or []
    found = []
    for y in yogas:
        if isinstance(y, str):
            yl = y.lower()
            if any(k in yl for k in _WEALTH_YOGA_KEYS):
                found.append(y)
    s = min(5, 2 * len(found))
    why_strong = [f"Wealth-supportive yoga: {y}" for y in found]
    return {"yogas": found, "score": s, "why_strong": why_strong, "why_weak": []}


def _layer_daridra_yogas(intel: dict) -> dict:
    yogas = intel.get("yogas") or []
    found = []
    for y in yogas:
        if isinstance(y, str):
            yl = y.lower()
            if any(k in yl for k in _DARIDRA_KEYS):
                found.append(y)
    s = -min(5, 3 * len(found))  # NEGATIVE weight
    why_weak = [f"Wealth-blocking yoga: {y}" for y in found]
    return {"yogas": found, "score": s, "why_strong": [], "why_weak": why_weak}


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 10 — D9 Sustained Strength (weight 5)
# LAYER 11 — 2nd House Accumulation (weight 4)
# LAYER 12 — Jupiter Deep Dive (weight 4)
# LAYER 13 — Rahu Deep Dive (weight 4)
# LAYER 14 — D2 Hora (weight 2)
# LAYER 15 — Moon (psychology, weight 2)
# ─────────────────────────────────────────────────────────────────────────────
def _layer_d9(kundli: dict, fifth_lord: str, eleventh_lord: str) -> dict:
    s = 0
    why_strong, why_weak = [], []
    for label, planet in (("5L", fifth_lord), ("11L", eleventh_lord),
                          ("Mercury", "Mercury"), ("Jupiter", "Jupiter"),
                          ("Rahu", "Rahu")):
        if not planet:
            continue
        info = _d9_strength(planet, kundli)
        if not info:
            continue
        if info.get("vargottama"):
            s += 1; why_strong.append(f"{label} {planet} VARGOTTAMA in D9 — double-strong")
        if info.get("own_sign_in_d9"):
            s += 1; why_strong.append(f"{label} {planet} in own sign in D9 — sustained strength")
        if info.get("in_dusthana"):
            s -= 1; why_weak.append(f"{label} {planet} in D9 dusthana H{info.get('house')} — fake D1 strength")
    s = max(-5, min(5, s))
    return {"score": s, "why_strong": why_strong, "why_weak": why_weak}


def _layer_2nd_house(intel: dict, kundli: dict) -> dict:
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    dignities   = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    pmap        = {p.get("name"): p for p in (kundli.get("planets") or [])}
    h2 = house_lords.get(2) or {}
    second_lord = h2.get("lord") or ""
    sl_dig = (dignities.get(second_lord) or {}).get("dignity") or "neutral-sign"
    sl_house = (pmap.get(second_lord) or {}).get("house")
    occ2 = [d.get("planet") for d in (intel.get("dignities") or [])
            if d.get("house") == 2 and d.get("planet")]

    s = 0
    why_strong, why_weak = [], []
    if sl_dig in ("exalted", "moolatrikona", "own-sign"):
        s += 2; why_strong.append(f"2L {second_lord} {sl_dig} — wealth retention strong")
    elif sl_dig in ("debilitated", "enemy-sign"):
        s -= 2; why_weak.append(f"2L {second_lord} {sl_dig} — wealth leaks")
    if isinstance(sl_house, int) and sl_house in DUSTHANA:
        s -= 1; why_weak.append(f"2L in dusthana H{sl_house} — accumulation challenged")
    if any(p in occ2 for p in NATURAL_BENEFICS):
        s += 1; why_strong.append("Benefic in 2nd — clean wealth")
    s = max(-4, min(4, s))
    return {"second_lord": second_lord, "second_lord_dignity": sl_dig,
            "score": s, "why_strong": why_strong, "why_weak": why_weak}


def _layer_jupiter(intel: dict) -> dict:
    j = (intel.get("dignities") or [])
    je = next((d for d in j if d.get("planet") == "Jupiter"), {}) or {}
    dig = je.get("dignity") or "neutral-sign"
    house = je.get("house")
    s = 0
    why_strong, why_weak = [], []
    s += DIGNITY_PTS.get(dig, 0) // 2
    if dig in ("exalted", "moolatrikona", "own-sign"):
        why_strong.append(f"Jupiter {dig} — long-term wealth-wisdom strong")
    elif dig in ("debilitated", "enemy-sign"):
        why_weak.append(f"Jupiter {dig} — long-term decisions weak")
    if isinstance(house, int) and house in WEALTH_HOUSES:
        s += 1; why_strong.append(f"Jupiter in wealth-house H{house}")
    if isinstance(house, int) and house in DUSTHANA:
        s -= 2; why_weak.append(f"Jupiter in dusthana H{house}")
    s = max(-4, min(4, s))
    return {"dignity": dig, "house": house, "score": s,
            "why_strong": why_strong, "why_weak": why_weak}


def _layer_rahu(intel: dict) -> dict:
    j = (intel.get("dignities") or [])
    re_d = next((d for d in j if d.get("planet") == "Rahu"), {}) or {}
    dig = re_d.get("dignity") or "neutral-sign"
    house = re_d.get("house")
    s = 0
    why_strong, why_weak = [], []
    # Rahu in upachaya (3,6,10,11) is GOOD for speculation
    if isinstance(house, int) and house in {3, 6, 10, 11}:
        s += 3; why_strong.append(f"Rahu in upachaya H{house} — speculation/F&O/crypto favoured")
    elif isinstance(house, int) and house == 5:
        s += 2; why_strong.append("Rahu in 5th — speculation peak (handle with discipline)")
    elif isinstance(house, int) and house in {2, 8, 12}:
        s -= 3; why_weak.append(f"Rahu in H{house} — sudden wealth-wipe risk")
    s = max(-4, min(4, s))
    return {"dignity": dig, "house": house, "score": s,
            "why_strong": why_strong, "why_weak": why_weak}


def _layer_d2_hora(d2: dict) -> dict:
    if not d2:
        return {"score": 0, "available": False}
    sun_h = d2.get("sun_hora_planets", 0)
    moon_h = d2.get("moon_hora_planets", 0)
    benefics_in_moon = d2.get("moon_hora_benefics", 0)
    s = 0
    why_strong = []
    if benefics_in_moon >= 2:
        s += 2; why_strong.append(f"{benefics_in_moon} natural benefic(s) in Moon's hora — Lakshmi favours")
    elif moon_h > sun_h:
        s += 1; why_strong.append("Moon's hora dominant — wealth via stable accumulation")
    s = max(-2, min(2, s))
    return {"score": s, "available": True, "why_strong": why_strong, "why_weak": []}


def _layer_moon_psychology(intel: dict, kundli: dict) -> dict:
    j = (intel.get("dignities") or [])
    me = next((d for d in j if d.get("planet") == "Moon"), {}) or {}
    dig = me.get("dignity") or "neutral-sign"
    house = me.get("house")
    sade = (intel.get("sade_sati") or "").lower()
    s = 0
    why_strong, why_weak = [], []
    if dig in ("exalted", "moolatrikona", "own-sign"):
        s += 1; why_strong.append(f"Moon {dig} — stable trader mindset")
    elif dig in ("debilitated", "enemy-sign"):
        s -= 1; why_weak.append(f"Moon {dig} — emotional/panic trades risk")
    if "phase" in sade or "running" in sade:
        s -= 1; why_weak.append(f"Sade Sati ({sade.strip()}) — trade with caution")
    s = max(-2, min(2, s))
    return {"dignity": dig, "house": house, "sade_sati": sade,
            "score": s, "why_strong": why_strong, "why_weak": why_weak}


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 16 — Vimshottari MD/AD/PD timing (weight 10)
# LAYER 17 — Live Jupiter/Saturn transit + Sade Sati (weight 5)
# ─────────────────────────────────────────────────────────────────────────────
def _layer_dasha_timing(kundli: dict, kp_sigs: dict, q_type: str) -> dict:
    """Find next favourable dasha window where a wealth-house signifier is
    active (MD or AD). For short-term/intraday Q's, also try PD."""
    sigs_271 = _significators_of(WEALTH_HOUSES, kp_sigs)
    today = datetime.utcnow()

    # Current dasha activated check
    cur = (kundli.get("currentDasha") or {})
    cur_md, cur_ad = cur.get("maha") or "", cur.get("antar") or ""
    current_supports = bool((cur_md and cur_md in sigs_271)
                            or (cur_ad and cur_ad in sigs_271))

    next_window = _next_dasha_window(kundli.get("dashas") or [], sigs_271, today)
    pd_window = None
    if q_type in ("intraday", "loss_recovery", "real_time"):
        pd_window = _next_pratyantar_window(kundli.get("dashas") or [], sigs_271, today)

    # Score: current activation = +6; future window within 12y = +4
    s = 0
    why_strong, why_weak = [], []
    if current_supports:
        s += 6
        why_strong.append(f"Current Dasha {cur_md}-{cur_ad} signifies wealth houses — window OPEN now")
    elif next_window:
        s += 2
        why_strong.append(f"Next favourable window: {next_window['dasha']} ({next_window['start']} → {next_window['end']})")
    else:
        s -= 4
        why_weak.append("No favourable dasha window in next 12 years — long wait")

    s = max(-10, min(10, s))
    return {
        "current_dasha":   f"{cur_md}-{cur_ad}".strip("-"),
        "current_supports": current_supports,
        "next_window":     next_window,
        "pratyantar_window": pd_window,
        "wealth_significators": sorted(sigs_271),
        "score": s, "why_strong": why_strong, "why_weak": why_weak,
    }


def _layer_transit(jup_t: dict, sat_t: dict, intel: dict, kundli: dict) -> dict:
    """Live Jupiter & Saturn transit over natal 2/5/8/11. Sade Sati flag."""
    pmap = {p.get("name"): p for p in (kundli.get("planets") or [])}
    moon = pmap.get("Moon") or {}
    moon_sign = moon.get("sign")
    moon_idx = _sign_idx(moon_sign)

    s = 0
    why_strong, why_weak = [], []

    # Jupiter current sign vs natal lagna's wealth houses
    asc_sign = (intel.get("lagna_sign") or "").strip().capitalize()
    asc_idx = _sign_idx(asc_sign)
    cur_jup_sign = None
    if jup_t and "_error" not in jup_t and jup_t.get("jupiter_changes"):
        # The most recent change <= today gives current sign.
        today = datetime.utcnow()
        cur = None
        for ch in jup_t["jupiter_changes"]:
            try:
                d = datetime.fromisoformat(ch.get("date") or "")
            except Exception:
                continue
            if d <= today:
                cur = ch
            else:
                break
        if cur:
            cur_jup_sign = cur.get("to_sign") or cur.get("sign")
    if cur_jup_sign and asc_idx is not None:
        jup_idx = _sign_idx(cur_jup_sign)
        if jup_idx is not None:
            jup_house_from_lagna = ((jup_idx - asc_idx) % 12) + 1
            if jup_house_from_lagna in WEALTH_HOUSES:
                s += 3
                why_strong.append(f"Jupiter currently transits H{jup_house_from_lagna} from Lagna — wealth-window OPEN")

    # Saturn current sign vs natal Moon (Sade Sati ±1)
    if sat_t and "_error" not in sat_t and sat_t.get("saturn_sign_idx") is not None and moon_idx is not None:
        sat_idx = sat_t["saturn_sign_idx"]
        # Sade Sati = Saturn in sign 12, sign of Moon, or sign 2 (Moon-relative)
        diff = (sat_idx - moon_idx) % 12
        if diff in (11, 0, 1):  # 12th, same, 2nd from Moon
            phase = {11: "1st (entering)", 0: "2nd (peak)", 1: "3rd (departing)"}[diff]
            s -= 2
            why_weak.append(f"Sade Sati {phase} phase active (Saturn in {sat_t['saturn_sign']}) — invest cautiously")
        # Saturn over natal 8 from lagna = loss-risk
        if asc_idx is not None:
            sat_house_from_lagna = ((sat_idx - asc_idx) % 12) + 1
            if sat_house_from_lagna == 8:
                s -= 2
                why_weak.append("Saturn transits 8th from Lagna — F&O/leverage AVOID")
            elif sat_house_from_lagna in (2, 11):
                s += 1
                why_strong.append(f"Saturn transits H{sat_house_from_lagna} — slow accumulation favoured (long-term)")

    s = max(-5, min(5, s))
    return {
        "jupiter_current_sign": cur_jup_sign,
        "saturn_current_sign":  sat_t.get("saturn_sign") if sat_t else None,
        "score": s, "why_strong": why_strong, "why_weak": why_weak,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MODIFIERS (M1..M8) — small ± adjustments, not main layers
# ─────────────────────────────────────────────────────────────────────────────
def _modifier_bhava_bala(intel: dict, shadbala: dict) -> dict:
    s = 0
    why = []
    try:
        from bhava_bala import compute_bhava_bala  # type: ignore
        # Build planet_verdicts dict from shadbala bands
        pv = {}
        for p, info in (shadbala or {}).items():
            if not isinstance(info, dict):
                continue
            pct = info.get("strength_pct")
            if not isinstance(pct, (int, float)):
                continue
            band = ("STRONG" if pct >= 90 else "MODERATE" if pct >= 70 else "WEAK")
            pv[p] = {"verdict": band}
        bb = compute_bhava_bala(intel, pv, None) or {}
        scores = bb.get("scores") or {}
        for h in (2, 5, 8, 11):
            try:
                v = int(scores.get(h, 0))
            except (ValueError, TypeError):
                continue
            if v >= 25:
                s += 1; why.append(f"H{h} Bhava-Bala strong ({v})")
            elif v <= -10:
                s -= 1; why.append(f"H{h} Bhava-Bala weak ({v})")
    except Exception:
        pass
    s = max(-5, min(5, s))
    return {"score": s, "why": why}


def _modifier_shadbala(shadbala: dict, fifth_lord: str, eleventh_lord: str) -> dict:
    s = 0
    why = []
    targets = {"Mercury", "Jupiter", fifth_lord, eleventh_lord} - {""}
    for p in targets:
        info = (shadbala or {}).get(p)
        if not isinstance(info, dict):
            continue
        pct = info.get("strength_pct")
        if not isinstance(pct, (int, float)):
            continue
        if pct >= 110:
            s += 1; why.append(f"{p} Shadbala very-strong ({pct:.0f}%) — full karyakarta")
        elif pct >= 90:
            pass  # neutral
        elif pct < 50:
            s -= 1; why.append(f"{p} Shadbala very-weak ({pct:.0f}%) — cannot deliver")
    s = max(-5, min(5, s))
    return {"score": s, "why": why}


def _modifier_combust_retro(intel: dict, fifth_lord: str, eleventh_lord: str) -> dict:
    s = 0
    why = []
    dignities = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    for label, planet in (("5L", fifth_lord), ("11L", eleventh_lord),
                          ("Mercury", "Mercury"), ("Jupiter", "Jupiter"),
                          ("Venus", "Venus")):
        d = dignities.get(planet) or {}
        if d.get("combust"):
            s -= 1; why.append(f"{label} {planet} combust — judgment-error penalty")
        if d.get("retro") and planet in (fifth_lord, eleventh_lord):
            s -= 1; why.append(f"{label} {planet} retrograde — wealth-result reversal/delay")
    s = max(-5, min(5, s))
    return {"score": s, "why": why}


def _modifier_lagnesh(intel: dict) -> dict:
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    dignities   = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    h1 = house_lords.get(1) or {}
    lagnesh = h1.get("lord") or ""
    dig = (dignities.get(lagnesh) or {}).get("dignity") or "neutral-sign"
    s = 0
    why = []
    if dig in ("exalted", "moolatrikona", "own-sign"):
        s += 2; why.append(f"Lagnesh {lagnesh} {dig} — wealth-handle capacity strong")
    elif dig in ("debilitated", "enemy-sign"):
        s -= 2; why.append(f"Lagnesh {lagnesh} {dig} — overall capacity weak")
    return {"lagnesh": lagnesh, "lagnesh_dignity": dig,
            "score": max(-3, min(3, s)), "why": why}


def _modifier_mahapurusha(varga_yogas: dict) -> dict:
    s = 0
    why = []
    if not varga_yogas or "_error" in varga_yogas:
        return {"score": 0, "why": []}
    found = []
    for kind in ("pancha_mahapurusha", "raj_yoga", "vipreet_raj_yoga"):
        items = varga_yogas.get(kind) or []
        for it in items:
            if isinstance(it, dict) and (it.get("varga") or "").upper() == "D1":
                found.append(it.get("name") or kind)
    if found:
        s = min(5, len(found) * 2)
        why = [f"Strong yoga: {y}" for y in found]
    return {"score": s, "why": why}


def _modifier_saturn_mars(intel: dict, kundli: dict) -> dict:
    """Saturn-Mars natal angle — opposition/conjunction = high volatility, F&O avoid."""
    pmap = {p.get("name"): p for p in (kundli.get("planets") or [])}
    sat = pmap.get("Saturn") or {}
    mar = pmap.get("Mars") or {}
    sat_lon = sat.get("longitude")
    mar_lon = mar.get("longitude")
    s = 0
    why = []
    if isinstance(sat_lon, (int, float)) and isinstance(mar_lon, (int, float)):
        diff = abs(sat_lon - mar_lon) % 360
        if diff > 180: diff = 360 - diff
        if diff <= 8:
            s -= 2; why.append("Saturn-Mars conjunction (orb ≤ 8°) — high volatility, AVOID F&O/leverage")
        elif abs(diff - 180) <= 8:
            s -= 2; why.append("Saturn-Mars opposition (orb ≤ 8°) — high volatility, AVOID F&O/leverage")
    return {"score": max(-3, min(3, s)), "why": why}


def _modifier_trik_lords(intel: dict) -> dict:
    """6/8/12 lord placement on 2/5/11 — debt-via-stocks warning."""
    house_lords = {h.get("house"): h for h in (intel.get("house_lords") or [])}
    pmap_lords  = {h.get("house"): (h.get("lord_in_house"), h.get("lord"))
                   for h in (intel.get("house_lords") or [])}
    s = 0
    why = []
    for trik in (6, 8, 12):
        info = pmap_lords.get(trik)
        if not info:
            continue
        in_house, lord = info
        if isinstance(in_house, int) and in_house in WEALTH_HOUSES:
            s -= 1
            why.append(f"{trik}L {lord} in H{in_house} — wealth via debt/loss/foreign exposure (caution)")
    return {"score": max(-3, min(3, s)), "why": why}


# ─────────────────────────────────────────────────────────────────────────────
# CONDITIONAL — Sector recommendation (planet-based)
# ─────────────────────────────────────────────────────────────────────────────
def _recommend_sectors(layer_5th: dict, mer: dict, jup: dict, rah: dict,
                       intel: dict) -> list[dict]:
    """Top 3 sectors based on the strongest natal-promise planet(s).
    Each entry: {planet, sectors, why}."""
    candidates = []
    # Score each planet's stock-relevance for this person
    dignities = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    for pname in ("Mercury", "Jupiter", "Rahu", "Venus", "Mars",
                  "Saturn", "Sun", "Moon"):
        d = dignities.get(pname) or {}
        dig = d.get("dignity") or "neutral-sign"
        h = d.get("house")
        score = DIGNITY_PTS.get(dig, 0)
        if isinstance(h, int) and h in TRINE_KENDRA:
            score += 2
        if isinstance(h, int) and h in WEALTH_HOUSES:
            score += 3
        if isinstance(h, int) and h in DUSTHANA:
            score -= 4
        if d.get("combust"):
            score -= 2
        candidates.append((pname, score))
    candidates.sort(key=lambda x: -x[1])
    top3 = []
    for pname, sc in candidates[:3]:
        if sc <= -3:  # too weak — don't recommend that planet's sectors
            continue
        sectors = PLANET_SECTORS.get(pname) or []
        why = (f"{pname} score={sc} — your strongest stock-relevant graha")
        top3.append({"planet": pname, "score": sc, "sectors": sectors, "why": why})
    return top3


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY MAPPING — verdict + planet strengths → recommended approach
# ─────────────────────────────────────────────────────────────────────────────
def _recommend_strategy(score: int, mer: dict, jup: dict, rah: dict,
                        sat_mars_mod: dict, bucket: str = "go_now") -> dict:
    """Locked strategy: long-term / SIP / swing / NO-F&O / NO-crypto.

    The strategy is BUCKET-GATED so it can never contradict the verdict text.
    For `wait` and `avoid` buckets, all active-deployment flags are forced
    OFF and `primary` is rewritten to align with the verdict — even if the
    raw score lands in a band that would otherwise allow swing/intraday.
    """
    # Compute the score-driven baseline first.
    allow_long_term  = jup.get("score", 0) >= 0 or score >= 60
    allow_swing      = mer.get("score", 0) >= 0 and score >= 55
    allow_intraday   = mer.get("score", 0) >= 4 and score >= 70
    # F&O/leverage gating
    allow_fno = (rah.get("score", 0) >= 2
                 and score >= 65
                 and (sat_mars_mod or {}).get("score", 0) >= 0)
    # Crypto
    allow_crypto = (rah.get("score", 0) >= 3 and score >= 60)
    allow_sip    = score >= 30

    if score >= 75:
        primary = "Long-term equity + active swing OK; SIP for compounding"
    elif score >= 60:
        primary = "Long-term equity + SIP-mutual-funds; swing only with discipline"
    elif score >= 45:
        primary = "Only SIP / mutual fund / blue-chip long-term holds"
    elif score >= 30:
        primary = "Avoid direct stocks; FD / gold / sovereign-bonds preferred"
    else:
        primary = "AVOID stock market; clear remedies first, reassess after 6 months"

    # ── Bucket overrides — verdict-aligned, no contradictions ───────────────
    # WAIT bucket: even if score=60-65 (clamped upper edge), the verdict says
    # "fresh capital deploy mat karein". Strategy must mirror that — only
    # existing SIPs may continue, no fresh active positions.
    if bucket == "wait":
        primary = ("Hold current SIPs only — fresh capital deploy mat karein. "
                   "Naye stock / swing / F&O / intraday / crypto STRICTLY na, "
                   "next favourable window ka intezaar karein.")
        allow_long_term = False   # no FRESH long-term entry
        allow_swing     = False
        allow_intraday  = False
        allow_fno       = False
        allow_crypto    = False
        # allow_sip stays as-is (continuing existing SIPs is fine)

    # AVOID bucket: hard stop on every active path; only ultra-conservative
    # parking allowed (FD/gold) — and even SIP is paused.
    elif bucket == "avoid":
        primary = ("AVOID stock market completely — pehle remedies + dheeraj. "
                   "FD / gold / sovereign-bonds tak rakhein. 6 maheene baad "
                   "reassess. F&O / intraday / crypto / swing STRICTLY na.")
        allow_long_term = False
        allow_swing     = False
        allow_intraday  = False
        allow_fno       = False
        allow_crypto    = False
        allow_sip       = False

    # LIMITED bucket: SIP / mutual fund / blue-chip only — block all
    # leverage and speculation regardless of where the raw score landed.
    elif bucket == "limited":
        primary = ("Sirf SIP / mutual fund / blue-chip long-term holds. "
                   "Koi F&O / intraday / swing / crypto nahi — caution mode.")
        # Blue-chip long-term + SIP are explicitly allowed by the verdict text,
        # so force these flags True here even if Jupiter is weak — otherwise
        # primary text and allow_* flags can disagree.
        allow_long_term = True
        allow_sip       = True
        allow_swing     = False
        allow_intraday  = False
        allow_fno       = False
        allow_crypto    = False

    # GO_NOW: keep score-driven flags as-is (already aligned with the
    # "Suitable" verdict text).

    return {
        "primary":      primary,
        "allow_long_term": allow_long_term,
        "allow_sip":      allow_sip,
        "allow_swing":    allow_swing,
        "allow_intraday": allow_intraday,
        "allow_fno":      allow_fno,
        "allow_crypto":   allow_crypto,
        "do_not":         (
            (["F&O / options / futures"] if not allow_fno else []) +
            (["Crypto / NFT / digital assets"] if not allow_crypto else []) +
            (["Intraday / scalping"] if not allow_intraday else []) +
            (["Swing trading"] if not allow_swing else []) +
            (["Margin / leverage trading"] if not allow_fno else [])
        ),
    }


# ═════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY: assess_stock(...)
# ═════════════════════════════════════════════════════════════════════════════
def assess_stock(kundli: dict, intel: dict, kp: dict,
                 birth: Optional[dict] = None,
                 question: str = "") -> dict:
    """Returns deterministic stock-market verdict — see top of file for the
    full layer/weight rubric.

    Output dict keys:
      verdict, score, confidence,
      natal_promise_score, current_trigger_score,
      stock_promised, stock_denied,
      kp_verdict_summary,
      question_type,
      framework_decision,        # "Suitable now" / "Wait until X" / "Limited / low-risk only" / "Avoid + remedies"
      strategy,                  # dict from _recommend_strategy
      sectors,                   # list of {planet, sectors, why}
      next_window, pratyantar_window,
      reasons_strong, reasons_weak, delay_reasons,
      remedy, remedy_for_planet,
      layers, modifiers,
      logic_trace
    """
    intel = intel or {}
    kp    = kp    or {}
    kundli= kundli or {}
    birth = birth or {}
    trace: list[str] = []

    asc_name = (intel.get("lagna_sign") or kundli.get("ascendant") or "")
    if isinstance(asc_name, dict):
        asc_name = asc_name.get("sign") or asc_name.get("name") or ""
    asc_name = (asc_name or "").strip().capitalize()
    lagna_idx = _sign_idx(asc_name)

    q_type = classify_stock_question(question)
    trace.append(f"Question classified as: {q_type}")

    # ── Pre-compute helper modules (best-effort) ─────────────────────────────
    shadbala_d = _maybe_shadbala(kundli, lagna_idx)
    av_d       = _maybe_ashtakavarga(kundli, lagna_idx)
    arudha_d   = _maybe_arudha(kundli)
    karakas_d  = _maybe_karakas(kundli)
    varga_d    = _maybe_varga_yogas(kundli, None)
    argala_d   = _maybe_argala(kundli)
    jup_t      = _maybe_jupiter_transit(lagna_idx)
    sat_t      = _maybe_saturn_transit()
    d2_d       = _d2_hora_check(kundli)

    # ── Natal Promise Layers (1-15) ──────────────────────────────────────────
    L1  = _layer_5th_house(intel, kundli, kp.get("significations") or {})
    L2  = _layer_11th_house(intel, kundli)
    L3  = _layer_kp_cuspal(kp)
    L4  = _layer_mercury(intel, kundli)
    L5  = _layer_8th_house(intel, kundli)
    L6  = _layer_ashtakavarga(av_d)
    L7  = _layer_9th_house(intel, kundli)
    L8  = _layer_wealth_yogas(intel)
    L9  = _layer_daridra_yogas(intel)
    L10 = _layer_d9(kundli, L1.get("fifth_lord", ""), L2.get("eleventh_lord", ""))
    L11 = _layer_2nd_house(intel, kundli)
    L12 = _layer_jupiter(intel)
    L13 = _layer_rahu(intel)
    L14 = _layer_d2_hora(d2_d)
    L15 = _layer_moon_psychology(intel, kundli)

    natal_promise_score = sum([
        L1["score"], L2["score"], L3["score"], L4["score"], L5["score"],
        L6["score"], L7["score"], L8["score"], L9["score"], L10["score"],
        L11["score"], L12["score"], L13["score"], L14["score"], L15["score"],
    ])

    # ── Current Trigger Layers (16-17) ───────────────────────────────────────
    L16 = _layer_dasha_timing(kundli, kp.get("significations") or {}, q_type)
    L17 = _layer_transit(jup_t, sat_t, intel, kundli)
    current_trigger_score = L16["score"] + L17["score"]

    # ── Modifiers ────────────────────────────────────────────────────────────
    M1 = _modifier_bhava_bala(intel, shadbala_d)
    M2 = _modifier_shadbala(shadbala_d, L1.get("fifth_lord", ""), L2.get("eleventh_lord", ""))
    M3 = _modifier_combust_retro(intel, L1.get("fifth_lord", ""), L2.get("eleventh_lord", ""))
    M4 = _modifier_lagnesh(intel)
    M5 = _modifier_mahapurusha(varga_d)
    M6 = _modifier_saturn_mars(intel, kundli)
    M7 = _modifier_trik_lords(intel)
    modifier_score = sum(m["score"] for m in (M1, M2, M3, M4, M5, M6, M7))

    # ── Total + verdict ──────────────────────────────────────────────────────
    raw_score = 50 + natal_promise_score + current_trigger_score + modifier_score
    score = max(0, min(100, int(round(raw_score))))

    # ── Unified 2-step framework + verdict (one canonical decision) ──────────
    # The framework "promise / denied" flag MUST gate the verdict band so the
    # user never sees a contradictory pair like "Suitable now" + "avoid + remedies"
    # or "Avoid" framework + "Highly Suitable" verdict.
    npx = natal_promise_score
    cur = current_trigger_score
    if npx >= 5 and cur >= 0:
        bucket  = "go_now"
        framework = "Suitable now — natal promise present and current window favourable"
        promised, denied = True, False
        # Allow score's full upside; clamp floor so the verdict band stays positive.
        score = max(score, 60)
    elif npx >= 5 and cur < 0:
        bucket  = "wait"
        nw = L16.get("next_window")
        when = (f"{_ym_to_human(nw['start'])} to {_ym_to_human(nw['end'])}"
                if nw else "next favourable dasha")
        framework = (f"Wait until {when} — natal promise yes, but current "
                     "window not aligned")
        promised, denied = True, False
        # Wait-mode: cap at "Suitable" / soft, never "Highly Suitable" right now.
        score = max(45, min(score, 65))
    elif npx < 5 and cur >= 0:
        bucket  = "limited"
        framework = ("Limited opportunity — current window helps but natal "
                     "promise weak; only low-risk SIP / blue-chip")
        promised, denied = False, False
        # Limited: low-risk SIP only — keep score in caution band.
        score = max(30, min(score, 55))
    else:
        bucket  = "avoid"
        framework = "Avoid + remedies first — both natal promise and current trigger weak"
        promised, denied = False, True
        # Hard cap so verdict NEVER reads "Suitable" while framework says avoid.
        score = min(score, 40)

    # Verdict label — derived from the same canonical bucket. Score band is
    # only used as a fine-grain modifier within the bucket's allowed range,
    # so framework + verdict can never disagree.
    if bucket == "go_now":
        verdict = ("Stock market sahi hai — Highly Suitable (long-term + active OK)"
                   if score >= 75 else
                   "Stock market thik hai — Suitable (long-term/SIP yes; "
                   "active trading discipline ke saath)")
    elif bucket == "wait":
        verdict = ("Stock market timing thik nahi — abhi WAIT karein, "
                   "naye trade na lein. Existing SIP continue OK, lekin "
                   "fresh capital deploy mat karein jab tak window khule.")
    elif bucket == "limited":
        verdict = ("Stock market me caution — sirf SIP / mutual fund / "
                   "blue-chip long-term, koi F&O/intraday nahi")
    else:  # avoid
        verdict = ("Stock market avoid karein — pehle remedies + dheeraj, "
                   "6 maheene baad reassess. F&O / intraday / crypto STRICTLY na.")

    # Strategy & sectors — pass `bucket` so strategy stays verdict-aligned
    # (no contradictions between primary text/active flags and verdict bucket).
    strategy = _recommend_strategy(score, L4, L12, L13, M6, bucket=bucket)
    sectors  = _recommend_sectors(L1, L4, L12, L13, intel)

    # Conditional D10 (only for career-trader Q)
    d10_info = {}
    if q_type == "career":
        d10_info = _d10_check(kundli, intel) or {}
        if d10_info:
            trace.append(f"D10 trader-fit signal: {d10_info.get('trader_fit_signal')}")

    # Aggregate reasons
    reasons_strong, reasons_weak = [], []
    for L in (L1, L2, L3, L4, L5, L6, L7, L8, L9, L10, L11, L12, L13, L14, L15, L16, L17):
        reasons_strong.extend(L.get("why_strong") or [])
        reasons_weak.extend(L.get("why_weak") or [])
    for m in (M1, M2, M3, M4, M5, M6, M7):
        for w in m.get("why") or []:
            (reasons_strong if m.get("score", 0) >= 0 else reasons_weak).append(w)

    # Remedy: pick weakest among (5L, 11L, Mercury, Jupiter, Lagnesh)
    candidates = []
    dignities_map = {d.get("planet"): d for d in (intel.get("dignities") or [])}
    for label, p in (("5L", L1.get("fifth_lord", "")),
                     ("11L", L2.get("eleventh_lord", "")),
                     ("Mercury", "Mercury"), ("Jupiter", "Jupiter"),
                     ("Lagnesh", M4.get("lagnesh", ""))):
        if not p: continue
        d = dignities_map.get(p) or {}
        rank = DIGNITY_RANK.get(d.get("dignity") or "neutral-sign", 2) - (3 if d.get("combust") else 0)
        candidates.append((p, rank, label))
    if candidates:
        weakest = min(candidates, key=lambda c: c[1])
        weakest_planet = weakest[0]
    else:
        weakest_planet = "Venus"
    remedy = _remedy_for_planet(weakest_planet) or _FALLBACK_REMEDY

    # Confidence: cross-layer agreement
    npx_dir = 1 if natal_promise_score > 0 else (-1 if natal_promise_score < 0 else 0)
    cur_dir = 1 if current_trigger_score > 0 else (-1 if current_trigger_score < 0 else 0)
    agree_bonus = 0
    if npx_dir == cur_dir and npx_dir != 0:
        agree_bonus = 12
    elif npx_dir == 0 or cur_dir == 0:
        agree_bonus = 5
    data_bonus = 0
    if L3.get("available"):                 data_bonus += 8
    if L6.get("available"):                 data_bonus += 5
    if shadbala_d and "_error" not in shadbala_d: data_bonus += 5
    if jup_t and "_error" not in jup_t:    data_bonus += 3
    if sat_t and "_error" not in sat_t:    data_bonus += 3
    confidence = min(98, 55 + agree_bonus + data_bonus + abs(score - 50) // 6)

    trace.append(f"Natal promise score: {natal_promise_score}")
    trace.append(f"Current trigger score: {current_trigger_score}")
    trace.append(f"Modifier score: {modifier_score}")
    trace.append(f"Final score: {score}/100, confidence {confidence}%")

    # KP summary one-liner
    kp_summary = ""
    if L3.get("available"):
        verdicts = [v.get("verdict") for v in (L3.get("by_cusp") or {}).values()]
        if verdicts.count("promised") >= 3:
            kp_summary = "KP STRONGLY confirms wealth (3+ cusps promised)"
        elif verdicts.count("promised") >= 2:
            kp_summary = "KP confirms wealth (2 cusps promised)"
        elif verdicts.count("denied") >= 2:
            kp_summary = "KP denies — wealth-cusps blocked"
        else:
            kp_summary = "KP ambiguous — mixed cusp signals"

    return {
        "verdict":              verdict,
        "score":                score,
        "confidence":           int(confidence),
        "natal_promise_score":  natal_promise_score,
        "current_trigger_score": current_trigger_score,
        "modifier_score":       modifier_score,
        "stock_promised":       promised,
        "stock_denied":         denied,
        "framework_decision":   framework,
        "kp_verdict_summary":   kp_summary,
        "question_type":        q_type,
        "strategy":             strategy,
        "sectors":              sectors,
        "next_window":          L16.get("next_window"),
        "pratyantar_window":    L16.get("pratyantar_window"),
        "current_dasha":        L16.get("current_dasha"),
        "current_dasha_supports": L16.get("current_supports"),
        "wealth_significators": L16.get("wealth_significators"),
        "fifth_lord":           L1.get("fifth_lord"),
        "fifth_lord_dignity":   L1.get("fifth_lord_dignity"),
        "eleventh_lord":        L2.get("eleventh_lord"),
        "eleventh_lord_dignity":L2.get("eleventh_lord_dignity"),
        "speculation_gains_yoga": L1.get("speculation_gains_yoga"),
        "dhana_yoga_2_11":      L2.get("dhana_yoga_2_11"),
        "kp_by_cusp":           L3.get("by_cusp") or {},
        "d10":                  d10_info,
        "d2_hora":              d2_d,
        "reasons_strong":       reasons_strong[:8],   # cap for narration
        "reasons_weak":         reasons_weak[:6],
        "remedy":               remedy,
        "remedy_for_planet":    weakest_planet,
        "layers": {
            "L1_5th": L1, "L2_11th": L2, "L3_kp": L3, "L4_mercury": L4,
            "L5_8th": L5, "L6_av": L6, "L7_9th": L7, "L8_wealth_yogas": L8,
            "L9_daridra": L9, "L10_d9": L10, "L11_2nd": L11,
            "L12_jupiter": L12, "L13_rahu": L13, "L14_d2": L14, "L15_moon": L15,
            "L16_dasha": L16, "L17_transit": L17,
        },
        "modifiers": {
            "M1_bhava_bala": M1, "M2_shadbala": M2, "M3_combust_retro": M3,
            "M4_lagnesh": M4, "M5_mahapurusha": M5,
            "M6_saturn_mars": M6, "M7_trik_lords": M7,
        },
        "logic_trace":          trace,
    }


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT HELPERS — for openai_helper LOCKED-FACTS prompt block
# ─────────────────────────────────────────────────────────────────────────────
def extract_window_str(v: dict) -> str:
    """Single source of truth for the human-readable timing window string."""
    if not v: return ""
    nw = v.get("next_window") or {}
    if not nw: return ""
    return f"{_ym_to_human(nw.get('start',''))} to {_ym_to_human(nw.get('end',''))}"


def _strategy_line(strat: dict) -> str:
    if not strat: return ""
    do_not = strat.get("do_not") or []
    out = f"  Recommended strategy: {strat.get('primary','')}\n"
    if do_not:
        out += f"  AVOID:               {', '.join(do_not)}\n"
    return out


def _sectors_line(sectors: list) -> str:
    if not sectors: return ""
    bits = []
    for s in sectors[:3]:
        bits.append(f"{s.get('planet','?')}→ {', '.join((s.get('sectors') or [])[:3])}")
    return "  Top sectors:         " + " | ".join(bits) + "\n"


def _engine_json_envelope(v: dict) -> str:
    import json as _json
    nw = v.get("next_window") or {}
    payload = {
        "final_verdict":        v.get("verdict"),
        "score":                v.get("score"),
        "confidence_pct":       v.get("confidence"),
        "natal_promise_score":  v.get("natal_promise_score"),
        "current_trigger_score":v.get("current_trigger_score"),
        "framework_decision":   v.get("framework_decision"),
        "stock_promised":       v.get("stock_promised"),
        "stock_denied":         v.get("stock_denied"),
        "question_type":        v.get("question_type"),
        "kp_verdict_summary":   v.get("kp_verdict_summary"),
        "current_dasha":        v.get("current_dasha"),
        "current_dasha_supports": v.get("current_dasha_supports"),
        "next_dasha_window":    (f"{nw.get('start')} → {nw.get('end')}" if nw else None),
        "must_use_window_str":  extract_window_str(v) or None,
        "fifth_lord":           v.get("fifth_lord"),
        "fifth_lord_dignity":   v.get("fifth_lord_dignity"),
        "eleventh_lord":        v.get("eleventh_lord"),
        "eleventh_lord_dignity":v.get("eleventh_lord_dignity"),
        "speculation_gains_yoga": v.get("speculation_gains_yoga"),
        "dhana_yoga_2_11":      v.get("dhana_yoga_2_11"),
        "strategy_primary":     (v.get("strategy") or {}).get("primary"),
        "do_not":               (v.get("strategy") or {}).get("do_not"),
        "top_sectors":          [s.get("planet") for s in (v.get("sectors") or [])[:3]],
        "remedy_planet":        v.get("remedy_for_planet"),
        "remedy":               v.get("remedy"),
    }
    return (
        "═══ STOCK ENGINE JSON (IMMUTABLE — COPY VALUES VERBATIM) ═══\n"
        + _json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n══════════════════════════════════════════════════════════════\n"
    )


def format_verdict_for_prompt(v: dict) -> str:
    """Render verdict as authoritative locked-facts block for AI narrator prompt."""
    if not v: return ""
    nw = v.get("next_window") or {}
    nw_line = ""
    if nw:
        nw_hr = f"{_ym_to_human(nw.get('start',''))} to {_ym_to_human(nw.get('end',''))}"
        nw_line = (
            f"  Next favourable Dasha window: {nw.get('dasha')} "
            f"({nw.get('start')} → {nw.get('end')}) — {nw.get('reason')}\n"
            f"  >>> NARRATE THIS WINDOW EXACTLY AS: \"{nw_hr}\". "
            f"DO NOT widen, shift, or change these dates. <<<\n"
        )
    else:
        nw_line = ("  Next favourable Dasha window: NOT FOUND in next 12 years\n"
                   "  >>> NARRATE: \"agle 12 saal mein koi spasht prabal wealth-yog window nahi mil raha\" — DO NOT invent dates. <<<\n")

    rs = "\n".join(f"    + {r}" for r in (v.get("reasons_strong") or [])[:6]) or "    (none)"
    rw = "\n".join(f"    - {r}" for r in (v.get("reasons_weak") or [])[:5]) or "    (none)"

    kp_lines = ""
    by_cusp = v.get("kp_by_cusp") or {}
    if by_cusp:
        kp_lines = "  KP CROSS-CHECK (cuspal sub-lord):\n"
        for h in sorted(by_cusp.keys()):
            row = by_cusp[h]
            kp_lines += (
                f"    Cusp {h} ({row.get('label','')}): SL={row.get('sl')} | "
                f"NL={row.get('nl')} | SB={row.get('sb')} | SS={row.get('ss')} | "
                f"signifies {row.get('sb_signifies_houses')} → {row.get('verdict','').upper()}\n"
            )

    return (
        _engine_json_envelope(v) + "\n"
        "════════════════════════════════════════════════════════════════════\n"
        "AUTHORITATIVE STOCK-MARKET VERDICT (deterministically computed by engine)\n"
        "════════════════════════════════════════════════════════════════════\n"
        f"  VERDICT:           {v.get('verdict')}\n"
        f"  Score:             {v.get('score')}/100   (confidence {v.get('confidence')}%)\n"
        f"  Framework:         {v.get('framework_decision')}\n"
        f"  Natal promise:     {v.get('natal_promise_score'):+d}   "
        f"Current trigger: {v.get('current_trigger_score'):+d}   "
        f"Modifiers: {v.get('modifier_score'):+d}\n"
        f"  Question type:     {v.get('question_type')}\n"
        f"  KP summary:        {v.get('kp_verdict_summary')}\n"
        f"  5th lord:          {v.get('fifth_lord')} ({v.get('fifth_lord_dignity')}) — speculation karaka\n"
        f"  11th lord:         {v.get('eleventh_lord')} ({v.get('eleventh_lord_dignity')}) — gains karaka\n"
        f"  Speculation Yoga:  {v.get('speculation_gains_yoga')}    Dhana Yoga 2-11: {v.get('dhana_yoga_2_11')}\n"
        f"  Current Dasha:     {v.get('current_dasha')} (supports wealth = {v.get('current_dasha_supports')})\n"
        f"{kp_lines}"
        f"{nw_line}"
        f"{_strategy_line(v.get('strategy') or {})}"
        f"{_sectors_line(v.get('sectors') or [])}"
        "  Strong supporting factors:\n"
        f"{rs}\n"
        "  Weakening / risk factors:\n"
        f"{rw}\n"
        f"  Recommended remedy planet: {v.get('remedy_for_planet')}\n"
        f"  Recommended remedy:        {v.get('remedy')}\n"
        "════════════════════════════════════════════════════════════════════\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Lang-specific compact final-answer template (mirror of marriage)
# ─────────────────────────────────────────────────────────────────────────────
_LANG_GREETING = {
    "hn": "Seedhi baat —", "hi": "सीधी बात —", "en": "Straight answer —",
}
_LANG_REASON = {"hn": "Vajah", "hi": "वजह", "en": "Reason"}
_LANG_TIMING = {"hn": "Samay", "hi": "समय", "en": "Timing"}
_LANG_STRATEGY = {"hn": "Strategy", "hi": "रणनीति", "en": "Strategy"}
_LANG_SECTORS = {"hn": "Sectors", "hi": "क्षेत्र", "en": "Sectors"}
_LANG_REMEDY = {"hn": "Upay", "hi": "उपाय", "en": "Remedy"}
_LANG_NO_WINDOW = {
    "hn": "Agle 12 saal mein koi prabal wealth-window nahi — long-term SIP discipline rakhein.",
    "hi": "अगले १२ वर्षों में कोई प्रबल धन-योग नहीं — दीर्घकालीन एसआईपी अनुशासन रखें।",
    "en": "No strong wealth window in the next 12 years — maintain long-term SIP discipline.",
}


def format_final_answer(v: dict, lang_code: str = "hn") -> str:
    """Pre-baked, fact-locked answer the AI only polishes for tone."""
    if not v: return ""
    code = lang_code if lang_code in _LANG_GREETING else "hn"
    g  = _LANG_GREETING[code]
    L_R = _LANG_REASON[code]; L_T = _LANG_TIMING[code]
    L_S = _LANG_STRATEGY[code]; L_SE = _LANG_SECTORS[code]
    L_X = _LANG_REMEDY[code]

    verdict = v.get("verdict") or ""
    rs = (v.get("reasons_strong") or [])[:2]
    rw = (v.get("reasons_weak")   or [])[:1]
    bits = []
    if rs: bits.append("; ".join(rs))
    if rw: bits.append(f"weakening: {rw[0]}")
    reason_line = ". ".join(bits) if bits else "—"

    timing = extract_window_str(v) or _LANG_NO_WINDOW[code]
    strategy = (v.get("strategy") or {}).get("primary", "")
    secs = v.get("sectors") or []
    sec_line = " | ".join(
        f"{s.get('planet')}: {', '.join((s.get('sectors') or [])[:2])}"
        for s in secs[:3]
    ) or "—"
    remedy = v.get("remedy") or ""

    return (
        f"{g} {verdict}.\n\n"
        f"{L_R}: 5L {v.get('fifth_lord')}, 11L {v.get('eleventh_lord')}, "
        f"current dasha {v.get('current_dasha')}. {reason_line}.\n\n"
        f"{L_T}: {timing}.\n"
        f"{L_S}: {strategy}.\n"
        f"{L_SE}: {sec_line}.\n\n"
        f"{L_X}: {remedy}."
    )

"""
Daily Energy Score Engine for Cosmic Lens
==========================================

Computes a Vedic-astrology-based "Today's Energy Score" (0-100) using the
following weighted formula:

    Energy =  Dasha          * 30%
            + Moon Transit   * 25%
            + Ashtakavarga   * 20%
            + Tara Bal       * 15%
            + Aspect/Strength* 10%

Each sub-score is independently 0-100 and explained in its own helper.
The engine is pure Python (no DB / network) so it can be unit-tested and
extended easily for premium variants.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]

# Classical benefic / malefic classification.
BENEFICS  = {"Jupiter", "Venus", "Moon", "Mercury"}
MALEFICS  = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

# Sign exaltation / debilitation (sign indices 0=Aries .. 11=Pisces).
EXALTATION = {
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
    "Jupiter": 3, "Venus": 11, "Saturn": 6,
}
DEBILITATION = {
    "Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
    "Jupiter": 9, "Venus": 5, "Saturn": 0,
}

# Own / Mool-trikona signs — planet feels "at home" → strong dignity.
OWN_SIGNS: Dict[str, set] = {
    "Sun":     {4},        # Leo
    "Moon":    {3},        # Cancer
    "Mars":    {0, 7},     # Aries + Scorpio
    "Mercury": {2, 5},     # Gemini + Virgo
    "Jupiter": {8, 11},    # Sagittarius + Pisces
    "Venus":   {1, 6},     # Taurus + Libra
    "Saturn":  {9, 10},    # Capricorn + Aquarius
}

# Yogakaraka planet per ascendant sign (rules both a kendra AND a trikona).
# These planets become exceptionally auspicious during their dasha.
YOGAKARAKA = {
    1: "Saturn",   # Taurus lagna
    3: "Mars",     # Cancer lagna
    4: "Mars",     # Leo lagna
    6: "Saturn",   # Libra lagna
    9: "Venus",    # Capricorn lagna
    10: "Venus",   # Aquarius lagna
}

# Combustion orbs (degrees from Sun) — planet within this becomes weak.
COMBUST_ORB = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0,
    "Jupiter": 11.0, "Venus": 10.0, "Saturn": 15.0,
}

# Tara Bal mapping (0-8 → score)
TARA_SCORES = [60, 85, 35, 80, 45, 88, 30, 75, 95]
TARA_NAMES  = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyak",
               "Sadhana", "Naidhana", "Mitra", "Ati Mitra"]

# Ashtakavarga bindu table — for each planet, list of relative-sign rules
# from each of the 8 sources (Sun, Moon, Mars, Mercury, Jupiter, Venus,
# Saturn, Lagna). Same data as front-end calc to keep parity.
AV_TABLE: Dict[str, List[List[int]]] = {
    "Sun":     [[1,2,4,7,8,9,10,11],[3,6,10,11],[1,2,4,7,8,9,10,11],[3,5,6,9,10,11,12],[5,6,9,11],[6,7,12],[1,2,4,7,8,9,10,11],[3,4,6,10,11,12]],
    "Moon":    [[3,6,7,8,10,11],[1,3,6,7,10,11],[2,3,5,6,9,10,11],[1,3,4,5,7,8,10,11],[1,4,7,8,10,11],[3,4,5,7,9,10,11],[3,5,6,11],[3,6,10,11]],
    "Mars":    [[3,5,6,10,11],[3,6,11],[1,2,4,7,8,10,11],[3,5,6,11],[6,10,11,12],[6,8,11,12],[1,4,7,8,9,10,11],[1,3,6,10,11]],
    "Mercury": [[5,6,9,11,12],[2,4,6,8,10,11],[1,2,4,7,8,9,10,11],[1,3,5,6,9,10,11,12],[6,8,11,12],[1,2,3,4,5,8,9,11],[1,2,4,7,8,9,10,11],[1,2,4,6,8,10,11]],
    "Jupiter": [[1,2,3,4,7,8,9,10,11],[2,5,7,9,11],[1,2,4,7,8,10,11],[1,2,4,5,6,9,10,11],[1,2,3,4,7,8,10,11],[2,5,6,9,10,11],[3,5,6,12],[1,2,4,5,6,7,9,10,11]],
    "Venus":   [[8,11,12],[1,2,3,4,5,8,9,11,12],[3,5,6,9,11,12],[3,5,6,9,11],[5,8,9,10,11],[1,2,3,4,5,8,9,10,11],[3,4,5,8,9,10,11],[1,2,3,4,5,8,9,11]],
    "Saturn":  [[1,2,4,7,8,10,11],[3,6,11],[3,5,6,10,11,12],[6,8,9,10,11,12],[5,6,11,12],[6,11,12],[3,5,6,11],[1,3,4,6,10,11]],
}
AV_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Houses classification for transit + dasha placement scoring.
KENDRA_TRIKONA = {1, 4, 5, 7, 9, 10}   # angular + trine — generally auspicious
NEUTRAL        = {2, 3, 11}
DUSHTHANA      = {6, 8, 12}            # malefic houses


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _today_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _planet_house_lookup(planets: List[Dict[str, Any]]) -> Dict[str, int]:
    """Build {planet_name: house_number} from planet list."""
    out: Dict[str, int] = {}
    for p in planets or []:
        name  = p.get("name") or p.get("planet")
        house = p.get("house")
        if name and isinstance(house, int):
            out[name] = house
    return out


def _planet_sign_lookup(planets: List[Dict[str, Any]],
                       lagna_sign: int) -> Dict[str, int]:
    """Build {planet_name: sign_index_0_to_11}."""
    out: Dict[str, int] = {}
    for p in planets or []:
        name = p.get("name") or p.get("planet")
        if not name:
            continue
        # Prefer explicit sign / signIndex if present.
        sign = p.get("signIndex")
        if sign is None and isinstance(p.get("lon"), (int, float)):
            sign = int(p["lon"] / 30) % 12
        if sign is None and isinstance(p.get("house"), int):
            sign = (lagna_sign + p["house"] - 1) % 12
        if isinstance(sign, int):
            out[name] = sign % 12
    return out


def _classify(planet: str) -> str:
    if planet in BENEFICS: return "benefic"
    if planet in MALEFICS: return "malefic"
    return "neutral"


# ──────────────────────────────────────────────────────────────────────────────
# 1. DASHA SCORE (30%)
# ──────────────────────────────────────────────────────────────────────────────

def _find_active(dashas: List[Dict[str, Any]],
                 today: str) -> Optional[Dict[str, Any]]:
    """Return the dasha entry whose [startDate, endDate) brackets today."""
    if not dashas:
        return None
    for d in dashas:
        s, e = d.get("startDate"), d.get("endDate")
        if s and e and s <= today < e:
            return d
    return None


def _resolve_current_dasha(dashas: List[Dict[str, Any]],
                           today: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Walk MD → AD → PD and return the three active planet names."""
    md = _find_active(dashas, today)
    if not md:
        return (None, None, None)
    ad = _find_active(md.get("subDashas") or [], today)
    pd = _find_active((ad or {}).get("subDashas") or [], today) if ad else None
    return (md.get("planet"), ad.get("planet") if ad else None,
            pd.get("planet") if pd else None)


def _is_combust(planet: str, planets: List[Dict[str, Any]]) -> bool:
    """True if planet is within combustion orb of the Sun."""
    if planet not in COMBUST_ORB:
        return False
    lon_of = {p.get("name"): p.get("lon") for p in planets or []
              if isinstance(p.get("lon"), (int, float))}
    sun = lon_of.get("Sun")
    pl  = lon_of.get(planet)
    if sun is None or pl is None:
        return False
    diff = abs(((pl - sun + 180) % 360) - 180)
    return diff < COMBUST_ORB[planet]


def _score_dasha_planet(planet: str,
                        house: Optional[int],
                        sign: Optional[int],
                        lagna_sign: int,
                        planets: List[Dict[str, Any]]) -> Tuple[int, Dict[str, Any]]:
    """Score a single dasha lord 0-100 with full dignity + yogakaraka + combust."""
    nat = _classify(planet)
    reasons: List[str] = []

    # ── Base score from placement + nature ──────────────────────────
    if house is None:
        base = {"benefic": 70, "malefic": 45, "neutral": 60}[nat]
        reasons.append(f"{nat} (house unknown)")
    elif nat == "benefic":
        if   house in KENDRA_TRIKONA: base = 88; reasons.append("benefic in kendra/trikona")
        elif house in DUSHTHANA:      base = 55; reasons.append("benefic in 6/8/12")
        else:                         base = 72; reasons.append("benefic in 2/3/11")
    elif nat == "malefic":
        if   house in DUSHTHANA:      base = 38; reasons.append("malefic in 6/8/12")
        elif house in KENDRA_TRIKONA: base = 58; reasons.append("malefic in kendra/trikona")
        else:                         base = 48; reasons.append("malefic in 2/3/11")
    else:
        if   house in KENDRA_TRIKONA: base = 72
        elif house in DUSHTHANA:      base = 45
        else:                         base = 60

    # ── Yogakaraka boost (huge factor classically) ──────────────────
    if YOGAKARAKA.get(lagna_sign) == planet:
        base += 12
        reasons.append("YOGAKARAKA for lagna")

    # ── Dignity (sign-based) ────────────────────────────────────────
    if sign is not None:
        if EXALTATION.get(planet) == sign:
            base += 10; reasons.append("exalted")
        elif sign in OWN_SIGNS.get(planet, set()):
            base += 7;  reasons.append("own sign")
        elif DEBILITATION.get(planet) == sign:
            base -= 12; reasons.append("debilitated")

    # ── Combustion penalty ──────────────────────────────────────────
    if _is_combust(planet, planets):
        base -= 8
        reasons.append("combust")

    final = max(5, min(100, base))
    return final, {"reasons": reasons, "base": base}


def compute_dasha_score(kundli: Dict[str, Any],
                        today: str,
                        lagna_sign: int) -> Tuple[float, Dict[str, Any]]:
    """
    Weighted MD/AD/PD score (MD 50%, AD 30%, PD 20%) with dignity, yogakaraka,
    and combustion factored into each lord's individual score.
    """
    dashas = kundli.get("dashas") or kundli.get("chart_data", {}).get("dashas")
    if not dashas:
        return 60.0, {"reason": "no_dasha_data"}

    md, ad, pd = _resolve_current_dasha(dashas, today)
    planets = (kundli.get("planets")
               or kundli.get("chart_data", {}).get("planets") or [])
    houses  = _planet_house_lookup(planets)
    signs   = _planet_sign_lookup(planets, lagna_sign)

    weights = {"md": 0.50, "ad": 0.30, "pd": 0.20}
    detail: Dict[str, Any] = {}
    weighted_sum = 0.0
    weight_total = 0.0

    for label, planet in (("md", md), ("ad", ad), ("pd", pd)):
        if not planet:
            continue
        sc, meta = _score_dasha_planet(planet, houses.get(planet),
                                       signs.get(planet), lagna_sign, planets)
        detail[label] = {
            "planet": planet,
            "house":  houses.get(planet),
            "sign":   signs.get(planet),
            "score":  sc,
            "reasons": meta["reasons"],
        }
        weighted_sum += sc * weights[label]
        weight_total += weights[label]

    if weight_total == 0:
        return 60.0, {"reason": "no_active_period", **detail}
    return weighted_sum / weight_total, detail


# ──────────────────────────────────────────────────────────────────────────────
# 2. MOON TRANSIT SCORE (25%)
# ──────────────────────────────────────────────────────────────────────────────

def compute_moon_transit_score(moon_today_sign: int,
                               lagna_sign: int,
                               birth_moon_sign: Optional[int] = None
                               ) -> Tuple[float, Dict[str, Any]]:
    """
    Lagna-relative house placement + Chandrashtama check.
    Chandrashtama = Moon transits 8th sign from natal Moon → classically
    very inauspicious; overrides the placement score.
    """
    house = ((moon_today_sign - lagna_sign) % 12) + 1
    if house in {1, 5, 9, 10}:    score = 85
    elif house in {4}:            score = 70   # kendra but less
    elif house in {2, 3, 7, 11}:  score = 68
    elif house in {6}:            score = 50
    else:                         score = 40   # 8, 12

    detail: Dict[str, Any] = {"house": house, "moon_sign": moon_today_sign,
                              "chandrashtama": False}

    if birth_moon_sign is not None:
        from_natal = ((moon_today_sign - birth_moon_sign) % 12) + 1
        detail["from_natal_moon"] = from_natal
        if from_natal == 8:
            score = min(score, 25)
            detail["chandrashtama"] = True
        elif from_natal in {1, 3, 6, 7, 10, 11}:
            score += 5   # auspicious placements from janma rashi

    return float(max(0, min(100, score))), detail


# ──────────────────────────────────────────────────────────────────────────────
# 3. ASHTAKAVARGA SCORE (20%)
# ──────────────────────────────────────────────────────────────────────────────

def compute_ashtakavarga_score(planets: List[Dict[str, Any]],
                               lagna_sign: int,
                               moon_today_sign: int) -> Tuple[float, Dict[str, Any]]:
    """Sum of bindus for moon's current sign across 7 grahas + Lagna,
    normalised to 0-100.  Mean total bindus per sign ≈ 28 (max 56)."""
    sign_of = _planet_sign_lookup(planets, lagna_sign)
    # The 8th source is Lagna itself.
    src_signs = [sign_of.get(n, lagna_sign) for n in AV_PLANETS] + [lagna_sign]

    total = 0
    for planet in AV_PLANETS:
        rules = AV_TABLE[planet]
        for c in range(8):
            rel = ((moon_today_sign - src_signs[c]) % 12) + 1
            if rel in rules[c]:
                total += 1

    # Realistic curve: 20 bindus → 0, 30 → 50, 40+ → 100. Matches real-world
    # distribution where moon-sign totals typically range 22-38.
    score = max(0.0, min(100.0, (total - 20) * 5.0))
    return score, {"bindus": total, "max": 56}


# ──────────────────────────────────────────────────────────────────────────────
# 4. TARA BAL SCORE (15%)
# ──────────────────────────────────────────────────────────────────────────────

def compute_tara_score(today_nak_idx: int,
                       birth_nak_idx: int) -> Tuple[float, Dict[str, Any]]:
    if birth_nak_idx < 0:
        return 60.0, {"reason": "no_birth_nakshatra"}
    diff = (today_nak_idx - birth_nak_idx) % 27
    tara = diff % 9
    return float(TARA_SCORES[tara]), {"tara": TARA_NAMES[tara], "tara_idx": tara}


# ──────────────────────────────────────────────────────────────────────────────
# 5. ASPECT + PLANET STRENGTH (10%)
# ──────────────────────────────────────────────────────────────────────────────

def compute_aspect_strength_score(planets: List[Dict[str, Any]],
                                  lagna_sign: int) -> Tuple[float, Dict[str, Any]]:
    """Simple birth-chart strength: benefics in good houses + exaltation - debilitation."""
    base = 50.0
    detail: Dict[str, Any] = {"benefic_kendra": 0, "malefic_dushthana": 0,
                              "exalted": [], "debilitated": []}

    sign_of = _planet_sign_lookup(planets, lagna_sign)
    house_of = _planet_house_lookup(planets)

    for name, house in house_of.items():
        nat = _classify(name)
        if nat == "benefic" and house in KENDRA_TRIKONA:
            base += 4
            detail["benefic_kendra"] += 1
        elif nat == "malefic" and house in DUSHTHANA:
            base -= 4
            detail["malefic_dushthana"] += 1

    for name, sign in sign_of.items():
        if EXALTATION.get(name) == sign:
            base += 6
            detail["exalted"].append(name)
        elif DEBILITATION.get(name) == sign:
            base -= 6
            detail["debilitated"].append(name)

    return max(0.0, min(100.0, base)), detail


# ──────────────────────────────────────────────────────────────────────────────
# CATEGORY + PRESENTATION
# ──────────────────────────────────────────────────────────────────────────────

def _category(score: float) -> Tuple[str, str]:
    """Return (label, color)."""
    if score < 40:  return "Low",       "red"
    if score < 60:  return "Moderate",  "orange"
    if score < 75:  return "Good",      "yellow"
    if score < 90:  return "Strong",    "blue"
    return "Excellent", "green"


def _summary_and_advice(parts: Dict[str, float],
                        details: Dict[str, Any]) -> Tuple[str, str]:
    """Pick the single strongest factor for the summary and a tailored advice."""
    strongest = max(parts.items(), key=lambda kv: kv[1])[0]

    summaries = {
        "dasha": "Aapki current dasha period sahayak hai — planetary cycle aapke favour mein hai.",
        "moon":  "Aaj ka chandra transit aapke ascendant ke liye anukool hai.",
        "av":    "Ashtakavarga bindus strong hain — chandra ke house mein cosmic support active hai.",
        "tara":  f"Tara Bal '{(details.get('tara_detail') or {}).get('tara','—')}' hai — favorable timing.",
        "asp":   "Birth chart ki planetary strength achhi position mein hai aaj.",
    }
    weak_summaries = {
        "dasha": "Dasha period thoda challenging hai — patience aur reflection ka samay.",
        "moon":  "Aaj chandra aapke ascendant ke liye difficult ghar mein hai.",
        "av":    "Ashtakavarga support kam hai — cautious decisions lein.",
        "tara":  f"Tara Bal '{(details.get('tara_detail') or {}).get('tara','—')}' inauspicious hai.",
        "asp":   "Birth chart strength average se kam hai aaj.",
    }

    advices = {
        "dasha": "Dasha lord ko strengthen karne ke liye unke mantra ya daan kareiņ.",
        "moon":  "Chandra ko balance karne ke liye safed cheezein (doodh, chawal) daan karein.",
        "av":    "Aaj important launches avoid karein — passive work ya planning ka din hai.",
        "tara":  "Subah meditation aur Gayatri Mantra se din shuru karein.",
        "asp":   "Apne ishta devta ka smaran karein — aaj inner work se zyada labh hoga.",
    }

    score = parts[strongest]
    if score >= 65:
        return summaries[strongest], advices[strongest]
    return weak_summaries[strongest], advices[strongest]


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────────────────────────────────────

def calculate_energy(user_data: Dict[str, Any],
                     today_moon: Dict[str, Any],
                     date_iso: Optional[str] = None) -> Dict[str, Any]:
    """
    Compute today's energy score for one user.

    user_data:
        - ascendantDeg | lagna_sign     (required)
        - planets: [{name, house, lon, ...}]
        - nakshatra: birth nakshatra name
        - dashas:   nested MD/AD/PD list (from kundli engine)
    today_moon:
        - longitude (sidereal)
        - rashiIndex (0-11)  — optional, derived from longitude
        - nakshatraIndex (0-26) — optional, derived from longitude
    """
    today = date_iso or _today_iso()

    # ── Resolve lagna ─────────────────────────────────────────────────────
    if "ascendantDeg" in user_data:
        lagna_sign = int(user_data["ascendantDeg"] / 30) % 12
    elif "lagna_sign" in user_data:
        lagna_sign = int(user_data["lagna_sign"]) % 12
    else:
        lagna_sign = (user_data.get("chart_data") or {}).get("lagna_sign", 0)

    planets = (user_data.get("planets")
               or (user_data.get("chart_data") or {}).get("planets")
               or [])

    # ── Resolve today's moon position ─────────────────────────────────────
    moon_lon = today_moon.get("longitude")
    moon_sign = today_moon.get("rashiIndex")
    moon_nak  = today_moon.get("nakshatraIndex")
    if moon_sign is None and isinstance(moon_lon, (int, float)):
        moon_sign = int(moon_lon / 30) % 12
    if moon_nak is None and isinstance(moon_lon, (int, float)):
        moon_nak  = int(moon_lon / (360 / 27)) % 27

    if moon_sign is None or moon_nak is None:
        return {"error": "today_moon missing longitude/rashiIndex/nakshatraIndex"}

    # ── Birth nakshatra ──────────────────────────────────────────────────
    birth_nak_name = (user_data.get("nakshatra")
                      or (user_data.get("chart_data") or {}).get("nakshatra"))
    birth_nak_idx  = NAKSHATRAS.index(birth_nak_name) if birth_nak_name in NAKSHATRAS else -1

    # ── Birth Moon sign (for chandrashtama) ──────────────────────────────
    birth_moon_sign: Optional[int] = None
    _sign_map = _planet_sign_lookup(planets, lagna_sign)
    if "Moon" in _sign_map:
        birth_moon_sign = _sign_map["Moon"]

    # ── Components ───────────────────────────────────────────────────────
    dasha_sc,  dasha_d  = compute_dasha_score(user_data, today, lagna_sign)
    moon_sc,   moon_d   = compute_moon_transit_score(moon_sign, lagna_sign, birth_moon_sign)
    av_sc,     av_d     = compute_ashtakavarga_score(planets, lagna_sign, moon_sign)
    tara_sc,   tara_d   = compute_tara_score(moon_nak, birth_nak_idx)
    asp_sc,    asp_d    = compute_aspect_strength_score(planets, lagna_sign)

    # ── Weighted aggregate ───────────────────────────────────────────────
    energy = (dasha_sc * 0.30 + moon_sc * 0.25 + av_sc * 0.20
              + tara_sc * 0.15 + asp_sc * 0.10)
    energy = max(0.0, min(100.0, energy))
    score  = int(round(energy))
    cat, color = _category(energy)

    parts   = {"dasha": dasha_sc, "moon": moon_sc, "av": av_sc,
               "tara": tara_sc,  "asp": asp_sc}
    details = {"dasha_detail": dasha_d, "moon_detail": moon_d,
               "av_detail": av_d, "tara_detail": tara_d,
               "asp_detail": asp_d}
    summary, advice = _summary_and_advice(parts, details)

    return {
        "energy_score": score,
        "category":     cat,
        "color":        color,
        "summary":      summary,
        "advice":       advice,
        "date":         today,
        "components": {
            "dasha":          {"score": round(dasha_sc, 1), "weight": 0.30, **dasha_d},
            "moon_transit":   {"score": round(moon_sc, 1),  "weight": 0.25, **moon_d},
            "ashtakavarga":   {"score": round(av_sc, 1),    "weight": 0.20, **av_d},
            "tara_bal":       {"score": round(tara_sc, 1),  "weight": 0.15, **tara_d},
            "aspect_strength":{"score": round(asp_sc, 1),   "weight": 0.10, **asp_d},
        },
    }

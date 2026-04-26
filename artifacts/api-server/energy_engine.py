"""
Daily Energy Score Engine for Cosmic Lens
==========================================

Computes a Vedic-astrology-based "Today's Energy Score" (0-100) using a
TRANSIT-FIRST design (philosophy: daily score must reflect things that
ACTUALLY change daily — birth-chart static factors are deprioritised).

    Energy =  Moon Transit   * 35%   (where chandra is, lagna-relative + chandrashtama)
            + Tara Bal       * 25%   (today's nakshatra friendship — Moon-driven)
            + Dasha          * 25%   (background mood tilt — months/years constant)
            + Ashtakavarga   * 15%   (cosmic bindus in today's Moon sign)

    [Aspect/Shadbala dropped — birth-chart static, doesn't affect daily mood]

Overlays applied AFTER weighted sum:
    - Saturn overlay  : Sade Sati (-10/-20/-10) or Dhaiyya (-10/-15)
    - Tithi overlay   : Rikta (-5) / Purna (+5)
    - Compression curve: pulls scores >60 down so 75-85 isn't an everyday occurrence

Net effect: 75% of the score is Moon-driven (transit + tara + AV) which
matches Vedic principle that Moon = mind = mood. Dasha provides backdrop tilt.

Summary text is signal-first (chandrashtama / Sade Sati / Naidhana detected
before falling back to score-band defaults) so the description matches what
the user actually feels.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from shadbala import compute_shadbala, apply_shodhana, REQUIRED_MIN

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

# Tara Bal mapping (0-8 → score) — recalibrated 2026-04-25:
# Wider spread so Naidhana truly hurts and Ati Mitra is a rare gift.
# Old: [60, 85, 35, 80, 45, 88, 30, 75, 95]
TARA_SCORES = [50, 78, 25, 72, 40, 82, 18, 70, 92]
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
    # Recalibrated 2026-04-25: compressed upper end + harsher dusthana
    # Old: 85/70/68/50/40 → New: 78/65/60/42/32
    if house in {1, 5, 9, 10}:    score = 78
    elif house in {4}:            score = 65
    elif house in {2, 3, 7, 11}:  score = 60
    elif house in {6}:            score = 42
    else:                         score = 32   # 8, 12

    detail: Dict[str, Any] = {"house": house, "moon_sign": moon_today_sign,
                              "chandrashtama": False}

    if birth_moon_sign is not None:
        from_natal = ((moon_today_sign - birth_moon_sign) % 12) + 1
        detail["from_natal_moon"] = from_natal
        if from_natal == 8:
            score = min(score, 20)   # was 25 — tightened
            detail["chandrashtama"] = True
        elif from_natal in {1, 3, 6, 7, 10, 11}:
            score += 4   # was +5 — slight reduction

    return float(max(0, min(100, score))), detail


# ──────────────────────────────────────────────────────────────────────────────
# 6. SATURN OVERLAY — Sade Sati / Dhaiyya (Kantaka + Ashtam Sani)
# ──────────────────────────────────────────────────────────────────────────────

def compute_saturn_overlay(saturn_today_sign: Optional[int],
                           birth_moon_sign: Optional[int]
                           ) -> Tuple[float, Dict[str, Any]]:
    """
    Apply Saturn-transit overlay relative to natal Moon.
    Returns (delta_to_apply_after_weighted_sum, detail).
    Delta is NEGATIVE (penalty) — added to final energy.

    Sade Sati  = Saturn transits 12th, 1st, or 2nd from natal Moon (~7.5 yrs)
        Phase 1 (12th): -10  (Aarambh — beginning, restlessness)
        Phase 2 (1st):  -20  (Madhya — peak intensity)
        Phase 3 (2nd):  -10  (Antya — closing, financial squeeze)

    Dhaiyya = Saturn transits 4th or 8th from natal Moon (~2.5 yrs each)
        4th (Kantaka Sani): -10  (home/peace disturbance)
        8th (Ashtam Sani):  -15  (health/transformation strain)
    """
    if saturn_today_sign is None or birth_moon_sign is None:
        return 0.0, {"active": False, "reason": "saturn_or_moon_missing"}

    from_natal = ((saturn_today_sign - birth_moon_sign) % 12) + 1
    detail: Dict[str, Any] = {
        "active":         False,
        "phase":          None,
        "saturn_sign":    saturn_today_sign,
        "from_natal_moon": from_natal,
    }

    if from_natal == 12:
        return -10.0, {**detail, "active": True, "phase": "Sade Sati Phase 1 (Aarambh — 12th from Moon)"}
    if from_natal == 1:
        return -20.0, {**detail, "active": True, "phase": "Sade Sati Phase 2 (Madhya — Janma Rashi)"}
    if from_natal == 2:
        return -10.0, {**detail, "active": True, "phase": "Sade Sati Phase 3 (Antya — 2nd from Moon)"}
    if from_natal == 4:
        return -10.0, {**detail, "active": True, "phase": "Kantaka Sani (Saturn in 4th from Moon)"}
    if from_natal == 8:
        return -15.0, {**detail, "active": True, "phase": "Ashtam Sani (Saturn in 8th from Moon)"}

    return 0.0, detail


# ──────────────────────────────────────────────────────────────────────────────
# 7. TITHI OVERLAY — Rikta (-5) / Purna (+5)
# ──────────────────────────────────────────────────────────────────────────────

def compute_tithi_overlay(sun_lon: Optional[float],
                          moon_lon: Optional[float]
                          ) -> Tuple[float, Dict[str, Any]]:
    """
    Compute today's tithi from Sun-Moon angular distance.
    Tithi index 1-30 (1-15 = Shukla Paksha, 16-30 = Krishna Paksha).
    Within either paksha, position 1-15 determines quality.

    Rikta (4, 9, 14): -5    (drains energy, avoid important launches)
    Purna (5, 10, 15): +5   (peak/full days, momentum)
    """
    if sun_lon is None or moon_lon is None:
        return 0.0, {"reason": "sun_or_moon_lon_missing"}

    diff = (moon_lon - sun_lon) % 360.0
    tithi_idx = int(diff / 12.0) + 1                       # 1..30
    paksha_pos = ((tithi_idx - 1) % 15) + 1                # 1..15
    paksha_name = "Shukla" if tithi_idx <= 15 else "Krishna"

    TITHI_NAMES = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
                   "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
                   "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
                   "Purnima/Amavasya"]
    tithi_name = TITHI_NAMES[paksha_pos - 1]

    # ── STEP 4: Special Tithi Expansion (mental-bucket only) ─────────────
    # Ekadashi  (tithi_idx 11 or 26) → +3 mental boost (fasting clarity)
    # Amavasya  (tithi_idx 30)       → -5 mental low   (dark moon introspection)
    # Purnima   (tithi_idx 15)       → +4 mental boost (full moon clarity)
    # These add to mental bucket ONLY — global score logic unchanged.
    mental_extra = 0.0
    special_name: Optional[str] = None
    if tithi_idx in (11, 26):
        mental_extra = 3.0
        special_name = "Ekadashi"
    elif tithi_idx == 30:
        mental_extra = -5.0
        special_name = "Amavasya"
    elif tithi_idx == 15:
        mental_extra = 4.0
        special_name = "Purnima"

    detail = {
        "tithi_idx":     tithi_idx,
        "paksha":        paksha_name,
        "paksha_pos":    paksha_pos,
        "tithi_name":    f"{paksha_name} {tithi_name}",
        "mental_extra":  mental_extra,
        "special":       special_name,
    }

    if paksha_pos in {4, 9, 14}:
        return -5.0, {**detail, "type": "Rikta (drain)"}
    if paksha_pos in {5, 10, 15}:
        return 5.0, {**detail, "type": "Purna (peak)"}
    return 0.0, {**detail, "type": "Neutral"}


# ──────────────────────────────────────────────────────────────────────────────
# STEP 1 — Transit-to-Natal Aspects (sign-based, simple conjunction/opposition)
# ──────────────────────────────────────────────────────────────────────────────

def _angular_separation(a: float, b: float) -> float:
    """Shortest angular distance between two longitudes (0-180°)."""
    d = abs((a - b) % 360.0)
    return d if d <= 180.0 else 360.0 - d


def _aspect_strength(actual_deg: float, exact_deg: float, orb: float) -> float:
    """
    Returns 0.0..1.0 strength based on how close actual is to exact aspect.
    Linear falloff inside the orb; 0 outside.
    """
    diff = abs(actual_deg - exact_deg)
    if diff > orb:
        return 0.0
    return 1.0 - (diff / orb)


def compute_transit_natal_aspects(
    saturn_today_sign: Optional[int],
    mars_today_sign:   Optional[int],
    jupiter_today_sign: Optional[int],
    birth_moon_sign:   Optional[int],
    birth_sun_sign:    Optional[int],
    skip_saturn:       bool = False,
    # v3.2 degree-precision args (optional — fall back to sign-based if missing)
    saturn_today_lon:  Optional[float] = None,
    mars_today_lon:    Optional[float] = None,
    jupiter_today_lon: Optional[float] = None,
    birth_moon_lon:    Optional[float] = None,
    birth_sun_lon:     Optional[float] = None,
) -> Tuple[float, Dict[str, Any]]:
    """
    Step 1 (v3.2): Transit interactions with natal Moon & Sun, now with
    DEGREE-BASED orbs when longitudes are provided. Sign-based fallback
    is preserved for backward compatibility.

    Classical orbs (tightened for Vedic precision):
      - Saturn aspects (3rd/7th/10th/conj) : 8°
      - Mars   aspects (4th/7th/8th/conj)  : 6°
      - Jupiter aspects (5th/7th/9th/conj) : 7°

    Saturn-Moon conjunction skipped (Sade Sati overlay handles it).
    Strength-based scaling: full weight at exact aspect, linear falloff to
    zero at the orb boundary.

    - Transit Saturn  → natal Moon  (opp only)            : up to -12
    - Transit Mars    → natal Moon  (conj or opp)         : up to  -8
    - Transit Jupiter → natal Moon  (conj/trine 120°/240°): up to +10
    - Transit Jupiter → natal Sun   (conj/trine 120°/240°): up to +10
      (Jupiter→Moon and Jupiter→Sun do not stack)
    """
    delta = 0.0
    aspects: List[str] = []
    detail: Dict[str, Any] = {}

    use_degrees = (saturn_today_lon is not None and birth_moon_lon is not None
                   and mars_today_lon is not None and jupiter_today_lon is not None)

    # ── Saturn → natal Moon (opposition only) ────────────────────────────
    if not skip_saturn and saturn_today_sign is not None and birth_moon_sign is not None:
        if use_degrees:
            sep = _angular_separation(saturn_today_lon, birth_moon_lon)
            strength = _aspect_strength(sep, 180.0, 8.0)
            if strength > 0:
                delta -= 12 * strength
                aspects.append("saturn_opposition_natal_moon")
                detail["saturn_orb_deg"] = round(abs(sep - 180.0), 2)
                detail["saturn_strength"] = round(strength, 3)
        else:
            from_natal = ((saturn_today_sign - birth_moon_sign) % 12) + 1
            if from_natal == 7:
                delta -= 12
                aspects.append("saturn_opposition_natal_moon")

    # ── Mars → natal Moon (conjunction or opposition) ────────────────────
    if mars_today_sign is not None and birth_moon_sign is not None:
        if use_degrees:
            sep = _angular_separation(mars_today_lon, birth_moon_lon)
            s_conj = _aspect_strength(sep,   0.0, 6.0)
            s_opp  = _aspect_strength(sep, 180.0, 6.0)
            strength = max(s_conj, s_opp)
            if strength > 0:
                delta -= 8 * strength
                aspects.append("mars_hit_natal_moon")
                detail["mars_strength"] = round(strength, 3)
                detail["mars_kind"] = "conjunction" if s_conj >= s_opp else "opposition"
        else:
            from_natal = ((mars_today_sign - birth_moon_sign) % 12) + 1
            if from_natal in {1, 7}:
                delta -= 8
                aspects.append("mars_hit_natal_moon")

    # ── Jupiter → natal Moon OR natal Sun (conj or trine, cap at +10) ────
    jupiter_support = False
    jupiter_target: Optional[str] = None
    jupiter_strength = 0.0
    if jupiter_today_sign is not None and birth_moon_sign is not None:
        if use_degrees:
            sep = _angular_separation(jupiter_today_lon, birth_moon_lon)
            s_conj = _aspect_strength(sep,   0.0, 7.0)
            s_t1   = _aspect_strength(sep, 120.0, 7.0)
            s_t2   = _aspect_strength(sep, 240.0, 7.0)
            s = max(s_conj, s_t1, s_t2)
            if s > 0:
                jupiter_support = True
                jupiter_target = "Moon"
                jupiter_strength = s
        else:
            from_natal = ((jupiter_today_sign - birth_moon_sign) % 12) + 1
            if from_natal in {1, 5, 9}:
                jupiter_support = True
                jupiter_target = "Moon"
                jupiter_strength = 1.0
    if not jupiter_support and jupiter_today_sign is not None and birth_sun_sign is not None:
        if use_degrees and birth_sun_lon is not None:
            sep = _angular_separation(jupiter_today_lon, birth_sun_lon)
            s_conj = _aspect_strength(sep,   0.0, 7.0)
            s_t1   = _aspect_strength(sep, 120.0, 7.0)
            s_t2   = _aspect_strength(sep, 240.0, 7.0)
            s = max(s_conj, s_t1, s_t2)
            if s > 0:
                jupiter_support = True
                jupiter_target = "Sun"
                jupiter_strength = s
        else:
            from_natal = ((jupiter_today_sign - birth_sun_sign) % 12) + 1
            if from_natal in {1, 5, 9}:
                jupiter_support = True
                jupiter_target = "Sun"
                jupiter_strength = 1.0
    if jupiter_support:
        delta += 10 * jupiter_strength
        aspects.append(f"jupiter_support_natal_{(jupiter_target or '').lower()}")
        detail["jupiter_strength"] = round(jupiter_strength, 3)

    detail["aspects"] = aspects
    detail["delta"]   = delta
    detail["active"]  = bool(aspects)
    detail["mode"]    = "degree" if use_degrees else "sign"
    return delta, detail


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2 — Jupiter & Mars Overlay Layer (lagna-relative house placement)
# ──────────────────────────────────────────────────────────────────────────────

def _house_delta_for_planet(transit_sign: int, ref_sign: int,
                             benefic_houses: set, malefic_houses: set,
                             benefic_score: float, malefic_score: float) -> Tuple[float, int]:
    """
    Returns (delta, house) for a transit planet seen from a reference sign
    (lagna or natal Moon). Used by Step 2 + Step 5 Lagna/Chandra-lagna blend.
    """
    house = ((transit_sign - ref_sign) % 12) + 1
    if house in benefic_houses:
        return benefic_score, house
    if house in malefic_houses:
        return malefic_score, house
    return 0.0, house


def compute_jupiter_mars_overlay(
    jupiter_today_sign: Optional[int],
    mars_today_sign:    Optional[int],
    lagna_sign:         Optional[int],
    birth_moon_sign:    Optional[int],
) -> Tuple[float, Dict[str, Any]]:
    """
    Step 2 (v3.2): Current-transit overlay for Jupiter & Mars, computed
    from BOTH lagna and natal Moon (Chandra lagna), then weighted-blended.

    Classical principle: a transit's effect should be evaluated from both
    the lagna AND the natal Moon. Lagna 60% / Moon 40% per most schools.

    - Jupiter in kendra/trikona (1,4,5,7,9,10): +6 (full)
    - Jupiter in dusthana (6,8,12)           : +2 (muted)
    - Mars    in dusthana (6,8,12)           : -6
    - Mars aspect Moon (same-sign or opp)    : extra -4
    """
    delta = 0.0
    flags: List[str] = []
    detail: Dict[str, Any] = {
        "jupiter_house_lagna": None,
        "jupiter_house_moon":  None,
        "mars_house_lagna":    None,
        "mars_house_moon":     None,
        "mars_aspect_moon":    False,
        "blend":               "lagna_60_moon_40",
        "flags":               flags,
    }

    LAGNA_W = 0.6
    MOON_W  = 0.4

    # ── Jupiter ──────────────────────────────────────────────────────────
    if jupiter_today_sign is not None:
        jup_delta = 0.0
        if lagna_sign is not None:
            d_l, h_l = _house_delta_for_planet(
                jupiter_today_sign, lagna_sign,
                KENDRA_TRIKONA, DUSHTHANA, +6.0, +2.0)
            detail["jupiter_house_lagna"] = h_l
            jup_delta += LAGNA_W * d_l
        if birth_moon_sign is not None:
            d_m, h_m = _house_delta_for_planet(
                jupiter_today_sign, birth_moon_sign,
                KENDRA_TRIKONA, DUSHTHANA, +6.0, +2.0)
            detail["jupiter_house_moon"] = h_m
            jup_delta += MOON_W * d_m
        # Renormalize if only one ref available
        if lagna_sign is None and birth_moon_sign is not None:
            jup_delta = jup_delta / MOON_W
        elif birth_moon_sign is None and lagna_sign is not None:
            jup_delta = jup_delta / LAGNA_W
        if jup_delta >= 4.0:
            flags.append("jupiter_support")
        elif jup_delta > 0:
            flags.append("jupiter_neutral")
        delta += jup_delta

    # ── Mars ─────────────────────────────────────────────────────────────
    if mars_today_sign is not None:
        mars_delta = 0.0
        # Mars dusthana check from both refs
        if lagna_sign is not None:
            d_l, h_l = _house_delta_for_planet(
                mars_today_sign, lagna_sign,
                set(), DUSHTHANA, 0.0, -6.0)
            detail["mars_house_lagna"] = h_l
            mars_delta += LAGNA_W * d_l
        if birth_moon_sign is not None:
            d_m, h_m = _house_delta_for_planet(
                mars_today_sign, birth_moon_sign,
                set(), DUSHTHANA, 0.0, -6.0)
            detail["mars_house_moon"] = h_m
            mars_delta += MOON_W * d_m
        # Renormalize if only one ref available
        if lagna_sign is None and birth_moon_sign is not None:
            mars_delta = mars_delta / MOON_W
        elif birth_moon_sign is None and lagna_sign is not None:
            mars_delta = mars_delta / LAGNA_W
        if mars_delta <= -4.0:
            flags.append("mars_conflict")
        delta += mars_delta

    # Mars aspect natal Moon (extra -4 when same-sign or opposition)
    if mars_today_sign is not None and birth_moon_sign is not None:
        from_natal = ((mars_today_sign - birth_moon_sign) % 12) + 1
        if from_natal in {1, 7}:
            delta -= 4
            detail["mars_aspect_moon"] = True
            if "mars_conflict" not in flags:
                flags.append("mars_conflict")

    detail["delta"] = delta
    return delta, detail


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3 — Choghadiya + Hora (lightweight time-of-day variation)
# ──────────────────────────────────────────────────────────────────────────────

# Mon=0 .. Sun=6  (Python datetime.weekday convention)
_WEEKDAY_LORDS = {
    0: "Moon",     # Monday
    1: "Mars",     # Tuesday
    2: "Mercury",  # Wednesday
    3: "Jupiter",  # Thursday
    4: "Venus",    # Friday
    5: "Saturn",   # Saturday
    6: "Sun",      # Sunday
}

# Chaldean order — planetary horas cycle in this sequence (decreasing speed)
_CHALDEAN = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

# Rahukal segment (1-8) by weekday. Day divided into 8 equal parts from
# sunrise to sunset. Per FIX 3 sunrise/sunset are now seasonal (see below).
_RAHUKAL_SEGMENT = {
    0: 2,  # Mon
    1: 7,  # Tue
    2: 5,  # Wed
    3: 6,  # Thu
    4: 4,  # Fri
    5: 3,  # Sat
    6: 8,  # Sun
}


def _seasonal_sun_times(month: int) -> Tuple[float, float]:
    """
    Lightweight month-based sunrise/sunset fallback (north-Indian latitudes).
    Used only when astronomical computation is not possible (lat/lng missing).
    Returns (sunrise_hour, sunset_hour) as decimal local hours.
    """
    if month in {11, 12, 1}:
        return 6.5, 17.5
    if month in {4, 5, 6}:
        return 5.5, 18.75
    return 6.0, 18.0


def _astronomical_sun_times(date_obj: datetime,
                            lat: float,
                            lon: float,
                            tz_offset: float = 5.5) -> Tuple[float, float]:
    """
    v3.2: NOAA Solar-Position-Algorithm sunrise/sunset (no external API).

    Pure-Python implementation accurate to ~1 minute for civilian use.
    Inputs:
      date_obj  : datetime (local date — only y/m/d used)
      lat, lon  : geographic latitude/longitude in degrees (signed)
      tz_offset : local time-zone offset from UTC in hours (e.g. IST = 5.5)

    Returns (sunrise_hour, sunset_hour) as decimal local hours.
    Falls back to seasonal approximation in polar/error cases.
    """
    import math
    try:
        # Day of year
        n = date_obj.timetuple().tm_yday
        # Fractional year γ in radians
        gamma = (2.0 * math.pi / 365.0) * (n - 1 + (12 - 12) / 24.0)
        # Equation of time (minutes)
        eq_time = 229.18 * (
            0.000075
            + 0.001868 * math.cos(gamma)
            - 0.032077 * math.sin(gamma)
            - 0.014615 * math.cos(2 * gamma)
            - 0.040849 * math.sin(2 * gamma)
        )
        # Solar declination (radians)
        decl = (
            0.006918
            - 0.399912 * math.cos(gamma)
            + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma)
            + 0.000907 * math.sin(2 * gamma)
            - 0.002697 * math.cos(3 * gamma)
            + 0.00148  * math.sin(3 * gamma)
        )
        lat_r = math.radians(lat)
        # Hour angle for sunrise/sunset (zenith = 90.833°, accounts for refraction)
        cos_h = (
            math.cos(math.radians(90.833))
            - math.sin(lat_r) * math.sin(decl)
        ) / (math.cos(lat_r) * math.cos(decl))
        if cos_h > 1 or cos_h < -1:
            # Polar day/night — fall back to seasonal table
            return _seasonal_sun_times(date_obj.month)
        ha = math.degrees(math.acos(cos_h))
        # UTC times in minutes since midnight
        sunrise_utc = 720 - 4 * (lon + ha) - eq_time
        sunset_utc  = 720 - 4 * (lon - ha) - eq_time
        # Convert to local hours
        sunrise_local = (sunrise_utc / 60.0 + tz_offset) % 24
        sunset_local  = (sunset_utc  / 60.0 + tz_offset) % 24
        # Sanity check (sunset should be after sunrise on same day)
        if sunset_local <= sunrise_local or sunset_local - sunrise_local > 18:
            return _seasonal_sun_times(date_obj.month)
        return sunrise_local, sunset_local
    except Exception:
        return _seasonal_sun_times(date_obj.month)


def _current_hora_lord(weekday: int, hour: int, minute: int = 0,
                       sunrise: float = 6.0, sunset: float = 18.0) -> Tuple[str, str]:
    """
    v3.2 CLASSICAL day/night hora system.

    - Day = sunrise → sunset, divided into 12 equal parts (day-horas)
    - Night = sunset → next sunrise (24h - day_length), divided into 12
    - First hora of the day (at sunrise) is ruled by the weekday's lord
    - Subsequent horas cycle through Chaldean order across both day & night

    Returns (lord_name, period) where period ∈ {"day", "night"}.
    """
    current = hour + minute / 60.0
    day_length   = max(0.5, sunset - sunrise)
    night_length = 24.0 - day_length
    day_hora_len   = day_length   / 12.0
    night_hora_len = night_length / 12.0

    day_lord = _WEEKDAY_LORDS[weekday]
    start_idx = _CHALDEAN.index(day_lord)

    if sunrise <= current < sunset:
        idx_in_day = int((current - sunrise) / day_hora_len)
        hora_idx = idx_in_day  # 0-11 day horas
        period = "day"
    elif current >= sunset:
        idx_in_night = int((current - sunset) / night_hora_len)
        hora_idx = 12 + idx_in_night  # 12-23 night horas
        period = "night"
    else:
        # before sunrise → late-night horas of previous day cycle
        idx_in_night = int((current + 24 - sunset) / night_hora_len)
        hora_idx = 12 + idx_in_night
        period = "night"

    lord = _CHALDEAN[(start_idx + hora_idx) % 7]
    return lord, period


def _is_rahukal(weekday: int, hour: int, minute: int = 0,
                sunrise: float = 6.0, sunset: float = 18.0) -> bool:
    """True if local time falls inside today's Rahukal window (sunrise→sunset / 8)."""
    seg = _RAHUKAL_SEGMENT.get(weekday)
    if seg is None:
        return False
    day_length = max(0.1, sunset - sunrise)
    seg_len    = day_length / 8.0
    seg_start  = sunrise + (seg - 1) * seg_len
    seg_end    = seg_start + seg_len
    current    = hour + minute / 60.0
    return seg_start <= current < seg_end


# ─── Full Choghadiya muhurat (v3.2) ─────────────────────────────────────────
# 8 day-choghadiyas + 8 night-choghadiyas. The day-cycle starts with the
# weekday's "first" choghadiya per classical sequence; night cycle is offset.
# Reference: standard Vedic muhurat tables.
_DAY_CHOGHADIYA = {
    0: ["Amrit",  "Kaal",  "Shubh", "Rog",  "Udveg", "Char",  "Labh",  "Amrit"],   # Mon
    1: ["Rog",    "Udveg", "Char",  "Labh", "Amrit", "Kaal",  "Shubh", "Rog"],     # Tue
    2: ["Labh",   "Amrit", "Kaal",  "Shubh","Rog",   "Udveg", "Char",  "Labh"],    # Wed
    3: ["Shubh",  "Rog",   "Udveg", "Char", "Labh",  "Amrit", "Kaal",  "Shubh"],   # Thu
    4: ["Char",   "Labh",  "Amrit", "Kaal", "Shubh", "Rog",   "Udveg", "Char"],    # Fri
    5: ["Kaal",   "Shubh", "Rog",   "Udveg","Char",  "Labh",  "Amrit", "Kaal"],    # Sat
    6: ["Udveg",  "Char",  "Labh",  "Amrit","Kaal",  "Shubh", "Rog",   "Udveg"],   # Sun
}
_NIGHT_CHOGHADIYA = {
    0: ["Char",   "Labh",  "Udveg", "Shubh","Amrit", "Char",  "Rog",   "Kaal"],    # Mon
    1: ["Kaal",   "Labh",  "Udveg", "Shubh","Amrit", "Char",  "Rog",   "Kaal"],    # Tue
    2: ["Rog",    "Kaal",  "Labh",  "Udveg","Shubh", "Amrit", "Char",  "Rog"],     # Wed
    3: ["Amrit",  "Char",  "Rog",   "Kaal", "Labh",  "Udveg", "Shubh", "Amrit"],   # Thu
    4: ["Rog",    "Kaal",  "Labh",  "Udveg","Shubh", "Amrit", "Char",  "Rog"],     # Fri
    5: ["Labh",   "Udveg", "Shubh", "Amrit","Char",  "Rog",   "Kaal",  "Labh"],    # Sat
    6: ["Shubh",  "Amrit", "Char",  "Rog",  "Kaal",  "Labh",  "Udveg", "Shubh"],   # Sun
}
# Choghadiya weights — Amrit best, Kaal worst
_CHOGHADIYA_DELTA = {
    "Amrit": +4, "Shubh": +3, "Labh": +3, "Char":  0,
    "Udveg": -3, "Rog":  -4, "Kaal": -4,
}


def _current_choghadiya(weekday: int, hour: int, minute: int,
                        sunrise: float, sunset: float) -> Tuple[str, str]:
    """
    Returns (choghadiya_name, period) for the given local time.
    period ∈ {"day", "night"}. 8 segments per period.
    """
    current = hour + minute / 60.0
    day_length   = max(0.5, sunset - sunrise)
    night_length = 24.0 - day_length
    if sunrise <= current < sunset:
        seg_len = day_length / 8.0
        idx = min(7, int((current - sunrise) / seg_len))
        return _DAY_CHOGHADIYA[weekday][idx], "day"
    if current >= sunset:
        seg_len = night_length / 8.0
        idx = min(7, int((current - sunset) / seg_len))
        return _NIGHT_CHOGHADIYA[weekday][idx], "night"
    # Before sunrise — last night cycle (prev weekday's night segments)
    prev_wd = (weekday - 1) % 7
    seg_len = night_length / 8.0
    idx = min(7, int((current + 24 - sunset) / seg_len))
    return _NIGHT_CHOGHADIYA[prev_wd][idx], "night"


def compute_choghadiya_hora_overlay(
    now_local: Optional[datetime],
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    tz_offset: float = 5.5,
) -> Tuple[float, Dict[str, Any]]:
    """
    Step 3 (v3.2): Time-of-day quality overlay.

    Components:
      - Rahukal active                 : -6
      - Choghadiya quality             : ±3 / ±4  (full table)
      - Hora lord (day/night unequal)  : ±2  (lighter than choghadiya, additive)

    The choghadiya + hora pair are capped together to ±5 so they don't
    overwhelm transit-based deltas. Rahukal stays separate (it's a hard
    avoid-window in classical practice).

    Uses astronomical sunrise/sunset when lat/lon provided, falls back to
    seasonal table otherwise.
    """
    if now_local is None:
        return 0.0, {"active": False, "reason": "no_local_time"}

    weekday = now_local.weekday()
    hour    = now_local.hour
    minute  = now_local.minute

    # v3.2: per-city astronomical sunrise/sunset when lat/lon available
    if lat is not None and lon is not None:
        sunrise, sunset = _astronomical_sun_times(now_local, lat, lon, tz_offset)
        sun_source = "astronomical"
    else:
        sunrise, sunset = _seasonal_sun_times(now_local.month)
        sun_source = "seasonal_fallback"

    flags: List[str] = []

    # Rahukal (separate component — full -6 weight retained)
    rahukal_delta = 0.0
    rahukal = _is_rahukal(weekday, hour, minute, sunrise, sunset)
    if rahukal:
        rahukal_delta = -6
        flags.append("rahukal")

    # Choghadiya muhurat (full classical table)
    chog_name, chog_period = _current_choghadiya(weekday, hour, minute, sunrise, sunset)
    chog_delta = float(_CHOGHADIYA_DELTA.get(chog_name, 0))
    if chog_delta >= 3:
        flags.append("choghadiya_auspicious")
    elif chog_delta <= -3:
        flags.append("choghadiya_inauspicious")

    # Day/night unequal hora (lighter weight, additive, ±2)
    hora_lord, hora_period = _current_hora_lord(weekday, hour, minute, sunrise, sunset)
    hora_kind: Optional[str] = None
    hora_delta = 0.0
    if hora_lord in {"Saturn", "Mars"}:
        hora_delta = -2
        hora_kind = "malefic"
        flags.append("hora_malefic")
    elif hora_lord in {"Jupiter", "Venus"}:
        hora_delta = +2
        hora_kind = "benefic"
        flags.append("hora_benefic")

    # Cap chog+hora combined to ±5 (avoid double-stacking similar concepts)
    combined = chog_delta + hora_delta
    if combined > 5:
        combined = 5.0
    elif combined < -5:
        combined = -5.0

    delta = rahukal_delta + combined

    return delta, {
        "active":            bool(flags),
        "rahukal":           rahukal,
        "choghadiya":        chog_name,
        "choghadiya_period": chog_period,
        "choghadiya_delta":  chog_delta,
        "hora_lord":         hora_lord,
        "hora_period":       hora_period,
        "hora_kind":         hora_kind,
        "hora_delta":        hora_delta,
        "weekday":           weekday,
        "hour":              hour,
        "sunrise":           round(sunrise, 3),
        "sunset":            round(sunset, 3),
        "sun_source":        sun_source,
        "delta":             delta,
        "flags":             flags,
    }


# ──────────────────────────────────────────────────────────────────────────────
# STEP 5 — Dasha Lord (PD) Current Transit House Check
# ──────────────────────────────────────────────────────────────────────────────

def compute_pd_transit_overlay(
    pd_planet:       Optional[str],
    transit_signs:   Dict[str, int],
    lagna_sign:      Optional[int],
    birth_moon_sign: Optional[int] = None,
) -> Tuple[float, Dict[str, Any]]:
    """
    Step 5 (v3.2): Where is the Pratyantar Dasha lord transiting NOW,
    relative to BOTH lagna AND natal Moon (Chandra lagna). 60/40 blend.

    - PD lord in dusthana (6,8,12)        : -8 (full)
    - PD lord in 1, 5, 9, 10              : +5 (full)
    - else                                :  0
    """
    if not pd_planet or lagna_sign is None:
        return 0.0, {"active": False, "reason": "missing_pd_or_lagna"}
    pd_sign = transit_signs.get(pd_planet) if transit_signs else None
    if pd_sign is None:
        return 0.0, {"active": False, "reason": "no_transit_sign_for_pd_lord",
                     "pd_planet": pd_planet}

    LAGNA_W = 0.6
    MOON_W  = 0.4
    KENDRA_FAV = {1, 5, 9, 10}

    # Score from lagna
    house_lagna = ((pd_sign - lagna_sign) % 12) + 1
    if house_lagna in DUSHTHANA:
        d_lagna, kind_lagna = -8.0, "dusthana"
    elif house_lagna in KENDRA_FAV:
        d_lagna, kind_lagna = +5.0, "kendra_trikona"
    else:
        d_lagna, kind_lagna = 0.0, "neutral"

    # Score from natal Moon (Chandra lagna)
    if birth_moon_sign is not None:
        house_moon = ((pd_sign - birth_moon_sign) % 12) + 1
        if house_moon in DUSHTHANA:
            d_moon, kind_moon = -8.0, "dusthana"
        elif house_moon in KENDRA_FAV:
            d_moon, kind_moon = +5.0, "kendra_trikona"
        else:
            d_moon, kind_moon = 0.0, "neutral"
        delta = LAGNA_W * d_lagna + MOON_W * d_moon
    else:
        house_moon = None
        kind_moon  = None
        delta = d_lagna

    # Pick a representative kind (use the stronger absolute side)
    if birth_moon_sign is not None:
        kind = kind_lagna if abs(d_lagna) >= abs(d_moon) else kind_moon
    else:
        kind = kind_lagna

    return delta, {
        "active":          delta != 0.0,
        "pd_planet":       pd_planet,
        "pd_house_lagna":  house_lagna,
        "pd_house_moon":   house_moon,
        "kind_lagna":      kind_lagna,
        "kind_moon":       kind_moon,
        "kind":            kind,
        "blend":           "lagna_60_moon_40" if birth_moon_sign is not None else "lagna_only",
        "delta":           delta,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 8. COMPRESSION CURVE — pull high scores down so 75-85 isn't every day
# ──────────────────────────────────────────────────────────────────────────────

def _compress_high_end(score: float) -> float:
    """
    Compress upper range so genuinely strong days are rare.
        Score 50 → 50    (untouched)
        Score 60 → 60    (untouched)
        Score 70 → 68    (-2)
        Score 80 → 76    (-4)
        Score 90 → 84    (-6)
        Score 100 → 92   (-8)
    Lower scores untouched — bad days stay bad.
    """
    if score <= 60:
        return score
    return score - (score - 60) * 0.20


# ──────────────────────────────────────────────────────────────────────────────
# 3. ASHTAKAVARGA SCORE (20%)
# ──────────────────────────────────────────────────────────────────────────────

def _build_bhinnashtakavarga(planets: List[Dict[str, Any]],
                             lagna_sign: int) -> Dict[str, List[int]]:
    """
    Build the Bhinnashtakavarga (BAV) matrix: for each graha, a 12-cell row
    giving bindus in each sign 0..11.  Sources: Sun..Saturn + Lagna.
    """
    sign_of = _planet_sign_lookup(planets, lagna_sign)
    src_signs = [sign_of.get(n, lagna_sign) for n in AV_PLANETS] + [lagna_sign]

    bav: Dict[str, List[int]] = {}
    for planet in AV_PLANETS:
        rules = AV_TABLE[planet]
        row = [0] * 12
        for sign in range(12):
            bindus = 0
            for c in range(8):
                rel = ((sign - src_signs[c]) % 12) + 1
                if rel in rules[c]:
                    bindus += 1
            row[sign] = bindus
        bav[planet] = row
    return bav


def compute_ashtakavarga_score(planets: List[Dict[str, Any]],
                               lagna_sign: int,
                               moon_today_sign: int
                               ) -> Tuple[float, Dict[str, Any]]:
    """
    Classical Sarvashtakavarga with Trikona + Ekadhipatya Shodhana applied
    (Parashara's prescribed bindu-reduction) before summing the moon-sign
    column.  The post-Shodhana totals are smaller but astrologically more
    meaningful — they reflect *net* transit support after cancelling out
    redundant bindus.
    """
    # 1. Build raw BAV matrix
    raw_bav = _build_bhinnashtakavarga(planets, lagna_sign)

    # 2. Determine which signs are occupied (for Ekadhipatya)
    sign_of = _planet_sign_lookup(planets, lagna_sign)
    occupied = {s for s in sign_of.values() if isinstance(s, int)}

    # 3. Apply Shodhana
    reduced = apply_shodhana(raw_bav, occupied)

    # 4. Sum moon-sign column across all 7 grahas → Sarva (post-Shodhana)
    raw_total     = sum(raw_bav[p][moon_today_sign]     for p in AV_PLANETS)
    reduced_total = sum(reduced[p][moon_today_sign]     for p in AV_PLANETS)

    # Post-Shodhana totals are typically 0..25.  Calibrated curve:
    #   0 → 10, 8 → 50, 16+ → 100
    score = max(0.0, min(100.0, 10.0 + reduced_total * 5.625))

    return score, {
        "bindus_raw":     raw_total,
        "bindus_reduced": reduced_total,
        "max":            56,
        "shodhana":       True,
    }


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
                                  lagna_sign: int,
                                  moon_sun_angle: Optional[float] = None
                                  ) -> Tuple[float, Dict[str, Any]]:
    """
    Full classical Shadbala-based chart strength.

    Each of the 7 grahas has a computed Shadbala expressed as % of its
    required minimum (Parashara's rupas-required table).  We average the
    percentages (capped at 150%) and map to 0-100.

    Weighted slightly toward the luminaries (Sun + Moon count 1.3×) because
    their strength affects overall day-level vitality most.
    """
    if not planets:
        return 50.0, {"reason": "no_planet_data"}

    shad = compute_shadbala(planets, lagna_sign, moon_sun_angle)
    if not shad:
        return 50.0, {"reason": "shadbala_unavailable"}

    weights = {"Sun": 1.3, "Moon": 1.3,
               "Mars": 1.0, "Mercury": 1.0, "Jupiter": 1.0,
               "Venus": 1.0, "Saturn": 1.0}

    weighted_sum = 0.0
    weight_total = 0.0
    by_planet: Dict[str, Any] = {}
    strong_planets: List[str] = []
    weak_planets:   List[str] = []

    for planet, info in shad.items():
        pct = min(150.0, info["strength_pct"])
        w   = weights.get(planet, 1.0)
        weighted_sum += pct * w
        weight_total += w
        by_planet[planet] = {
            "pct":   info["strength_pct"],
            "total": info["total"],
            "req":   info["required"],
        }
        if info["strength_pct"] >= 100:
            strong_planets.append(planet)
        elif info["strength_pct"] < 70:
            weak_planets.append(planet)

    avg_pct = weighted_sum / weight_total if weight_total else 0.0
    # Map 0..150% → 0..100 score (linear, capped).
    score = max(0.0, min(100.0, avg_pct * 100.0 / 150.0))

    return score, {
        "shadbala_avg_pct": round(avg_pct, 1),
        "strong_planets":   strong_planets,
        "weak_planets":     weak_planets,
        "per_planet":       by_planet,
    }


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


# ──────────────────────────────────────────────────────────────────────────────
# 9. MAHADASHA SANDHI DETECTION (transition penalty)
# ──────────────────────────────────────────────────────────────────────────────

def _detect_md_sandhi(dashas: List[Dict[str, Any]], today: str) -> bool:
    """
    True if today is within ~6 months of the active Mahadasha's start or end.
    The transition between two MDs creates a classically "lost / disoriented"
    period — small penalty applied.
    """
    if not dashas:
        return False
    md = _find_active(dashas, today)
    if not md:
        return False
    s, e = md.get("startDate"), md.get("endDate")
    if not (s and e):
        return False
    try:
        td = datetime.strptime(today, "%Y-%m-%d")
        sd = datetime.strptime(s, "%Y-%m-%d")
        ed = datetime.strptime(e, "%Y-%m-%d")
    except (ValueError, TypeError):
        return False
    six_months_days = 183
    return (td - sd).days < six_months_days or (ed - td).days < six_months_days


def _check_pd_retrograde(pd_planet: Optional[str],
                         planets: List[Dict[str, Any]]) -> Optional[str]:
    """Return the PD lord's name if it is currently retrograde, else None."""
    if not pd_planet:
        return None
    for p in planets or []:
        name = p.get("name") or p.get("planet")
        if name == pd_planet:
            return pd_planet if p.get("retrograde") else None
    return None


# ──────────────────────────────────────────────────────────────────────────────
# 10. BUCKETS (Physical / Mental / Luck) — derived from existing scores
# ──────────────────────────────────────────────────────────────────────────────

def _compute_buckets(moon_sc: float, tara_sc: float, dasha_sc: float,
                     av_sc: float, saturn_delta: float,
                     tithi_delta: float,
                     tithi_mental_extra: float = 0.0) -> Dict[str, Dict[str, Any]]:
    """
    Map existing component scores into 3 user-facing buckets.

    Physical (Shakti) — body/drive/vitality
        Dasha (life-force lord) + Ashtakavarga (cosmic support)
        Saturn overlay drags it down (Sade Sati = heavy body)

    Mental (Shaanti) — mind/clarity/mood
        Moon transit + Tara Bal (mind-related Vedic factors)
        Tithi overlay shifts it (Rikta = mental drain, Purna = clarity)
        STEP 4: Special-tithi mental_extra (Ekadashi/Amavasya/Purnima)
        is added to mental ONLY — never to physical/luck/global.

    Luck (Bhagya) — opportunities/flow/synchronicity
        Ashtakavarga + Dasha (running luck-period)
        Tithi gives subtle bonus, Saturn small drag
    """
    # Saturn (Sade Sati / Dhaiyya) hits BODY hardest — heavy multiplier on physical.
    # Tithi (Rikta/Purna) directly affects MIND — full weight on mental.
    # Both saturn + tithi affect LUCK/flow moderately.
    physical = dasha_sc * 0.50 + av_sc * 0.40 + saturn_delta * 1.2
    mental   = (moon_sc * 0.55 + tara_sc * 0.40 + tithi_delta * 1.0
                + saturn_delta * 0.4 + tithi_mental_extra)
    luck     = av_sc   * 0.45 + dasha_sc * 0.45 + tithi_delta * 0.6 + saturn_delta * 0.7

    def clamp(x: float) -> int:
        return int(round(max(0.0, min(100.0, x))))

    return {
        "physical": {"score": clamp(physical), "label": "Shakti"},
        "mental":   {"score": clamp(mental),   "label": "Shaanti"},
        "luck":     {"score": clamp(luck),     "label": "Bhagya"},
    }


# ──────────────────────────────────────────────────────────────────────────────
# 11. CONFIDENCE LEVEL
# ──────────────────────────────────────────────────────────────────────────────

def _compute_confidence(parts: Dict[str, float],
                        saturn_d: Dict[str, Any],
                        tithi_d: Dict[str, Any],
                        moon_d: Dict[str, Any],
                        tara_d: Dict[str, Any]) -> str:
    """
    Confidence reflects whether signals AGREE.
        high   = all signals point same direction (clean good or clean bad day)
        low    = strong contradiction (e.g. weighted base high but Saturn heavy)
        medium = typical mixed day
    """
    scores = [v for v in parts.values() if isinstance(v, (int, float))]
    avg = sum(scores) / len(scores) if scores else 60.0

    sat_active = bool(saturn_d.get("active"))
    sat_heavy  = sat_active and saturn_d.get("delta", 0) <= -15
    chandrashtama = bool(moon_d.get("chandrashtama"))
    rikta = (tithi_d.get("type") or "").startswith("Rikta")
    purna = (tithi_d.get("type") or "").startswith("Purna")
    bad_tara = tara_d.get("tara") in {"Naidhana", "Vipat"}
    good_tara = tara_d.get("tara") in {"Sampat", "Mitra", "Ati Mitra"}

    neg_signals = sum([sat_heavy, chandrashtama, rikta, bad_tara])
    pos_signals = sum([purna, good_tara])

    # Mixed = strong contradiction
    if neg_signals >= 1 and pos_signals >= 1:
        return "low"
    if avg >= 70 and neg_signals >= 1:
        return "low"
    if avg <= 45 and pos_signals >= 1:
        return "low"

    # Clean alignment
    if neg_signals >= 2 and avg <= 55:
        return "high"
    if pos_signals >= 1 and avg >= 65 and not sat_active:
        return "high"

    return "medium"


# ──────────────────────────────────────────────────────────────────────────────
# 12. ACTIVE FLAGS — structured array for UI
# ──────────────────────────────────────────────────────────────────────────────

def _build_active_flags(saturn_d: Dict[str, Any],
                        tithi_d: Dict[str, Any],
                        moon_d: Dict[str, Any],
                        tara_d: Dict[str, Any],
                        md_sandhi: bool,
                        retrograde_pd: Optional[str],
                        transit_aspects_d: Optional[Dict[str, Any]] = None,
                        jup_mars_d:        Optional[Dict[str, Any]] = None,
                        time_quality_d:    Optional[Dict[str, Any]] = None,
                        pd_transit_d:      Optional[Dict[str, Any]] = None,
                        ) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []

    if saturn_d.get("active"):
        delta = saturn_d.get("delta", 0)
        sev = "high" if delta <= -15 else "medium"
        flags.append({"type": "saturn", "phase": saturn_d.get("phase"),
                      "severity": sev})

    if moon_d.get("chandrashtama"):
        flags.append({"type": "chandrashtama", "severity": "high"})

    tt = (tithi_d.get("type") or "")
    if tt.startswith("Rikta"):
        flags.append({"type": "tithi_rikta",
                      "tithi": tithi_d.get("tithi_name"),
                      "severity": "medium"})
    elif tt.startswith("Purna"):
        flags.append({"type": "tithi_purna",
                      "tithi": tithi_d.get("tithi_name"),
                      "severity": "low"})

    # STEP 4: Special tithi flags (Ekadashi / Amavasya / Purnima)
    special = tithi_d.get("special")
    if special == "Ekadashi":
        flags.append({"type": "tithi_ekadashi",
                      "tithi": tithi_d.get("tithi_name"),
                      "severity": "low"})
    elif special == "Amavasya":
        flags.append({"type": "tithi_amavasya",
                      "tithi": tithi_d.get("tithi_name"),
                      "severity": "medium"})
    elif special == "Purnima":
        flags.append({"type": "tithi_purnima",
                      "tithi": tithi_d.get("tithi_name"),
                      "severity": "low"})

    tn = tara_d.get("tara")
    if tn in {"Naidhana", "Vipat"}:
        flags.append({"type": "tara", "name": tn,
                      "severity": "high" if tn == "Naidhana" else "medium"})

    if md_sandhi:
        flags.append({"type": "md_sandhi", "severity": "medium"})

    if retrograde_pd:
        flags.append({"type": "pd_retrograde", "planet": retrograde_pd,
                      "severity": "low"})

    # STEP 1: Transit-to-natal aspect flags
    if transit_aspects_d:
        for asp in transit_aspects_d.get("aspects") or []:
            if asp == "saturn_opposition_natal_moon":
                flags.append({"type": "saturn_aspect_natal_moon",
                              "aspect": "opposition", "severity": "high"})
            elif asp == "mars_hit_natal_moon":
                flags.append({"type": "mars_aspect_natal_moon",
                              "severity": "high"})
            elif asp.startswith("jupiter_support_natal_"):
                target = asp.replace("jupiter_support_natal_", "")
                flags.append({"type": "jupiter_support_natal",
                              "target": target, "severity": "low"})

    # STEP 2: Jupiter & Mars overlay flags (use lagna-relative house data)
    if jup_mars_d:
        for f in jup_mars_d.get("flags") or []:
            if f == "jupiter_support":
                flags.append({"type": "jupiter_support",
                              "house": jup_mars_d.get("jupiter_house"),
                              "severity": "low"})
            elif f == "jupiter_neutral":
                flags.append({"type": "jupiter_neutral",
                              "house": jup_mars_d.get("jupiter_house"),
                              "severity": "low"})
            elif f == "mars_conflict":
                # Single mars_conflict flag even if both house & aspect fire
                if not any(x.get("type") == "mars_conflict" for x in flags):
                    flags.append({"type": "mars_conflict",
                                  "house": jup_mars_d.get("mars_house"),
                                  "aspect_moon": jup_mars_d.get("mars_aspect_moon"),
                                  "severity": "medium"})

    # STEP 3: Choghadiya / Hora flags
    if time_quality_d and time_quality_d.get("active"):
        if time_quality_d.get("rahukal"):
            flags.append({"type": "rahukal", "severity": "medium"})
        kind = time_quality_d.get("hora_kind")
        if kind in {"benefic", "malefic"}:
            flags.append({"type": "hora",
                          "lord": time_quality_d.get("hora_lord"),
                          "kind": kind,
                          "severity": "low"})

    # STEP 5: PD lord transit house flag
    if pd_transit_d and pd_transit_d.get("active"):
        kind = pd_transit_d.get("kind")
        if kind == "dusthana":
            flags.append({"type": "pd_transit_dusthana",
                          "planet": pd_transit_d.get("pd_planet"),
                          "house":  pd_transit_d.get("pd_house"),
                          "severity": "high"})
        elif kind == "kendra_trikona":
            flags.append({"type": "pd_transit_kendra",
                          "planet": pd_transit_d.get("pd_planet"),
                          "house":  pd_transit_d.get("pd_house"),
                          "severity": "low"})

    return flags


def _summary_and_advice(score: float,
                        parts: Dict[str, float],
                        details: Dict[str, Any]) -> Tuple[str, str]:
    """
    Mood-aware summary builder. Signal-first detection (worst signals win),
    then falls back to score-band defaults. Output language deliberately
    matches the felt-mood at each band so user trust holds.
    """
    moon_d   = details.get("moon_detail")    or {}
    tara_d   = details.get("tara_detail")    or {}
    saturn_d = details.get("saturn_overlay") or {}
    tithi_d  = details.get("tithi_overlay")  or {}

    tara_name = tara_d.get("tara")
    sat_active = bool(saturn_d.get("active"))
    sat_delta  = saturn_d.get("delta", 0) if isinstance(saturn_d, dict) else 0

    # ── PRIORITY 1: Critical signals (override score band) ────────────────
    if moon_d.get("chandrashtama"):
        return ("Aaj Chandrashtama active hai — chandra aapke janma rashi se 8th mein. Mind restless rahega, important decisions postpone karein.",
                "Subah Shiv mantra (Om Namah Shivay 108x), light food, extra rest. Travel/launches kal pe tal do.")

    if sat_active and sat_delta <= -20:
        return ("Sade Sati Madhya peak chal raha hai — heavy, slow, demanding period. Yeh aap actually feel kar rahe honge.",
                "Hanuman Chalisa daily, Saturday black sesame ya mustard oil ka daan, blue/black avoid. Patience hi remedy hai.")

    if sat_active and sat_delta <= -15:
        return (f"⚠️ Ashtam Sani active — Saturn aapke 8th from natal Moon mein. Health/transformation strain feel hoga.",
                "Hanuman ji ka stotra, til/loha daan Saturday ko, oily/heavy food avoid. Body signals seriously lo.")

    if sat_active:
        return (f"⚠️ {saturn_d.get('phase','Saturn')} chal raha — life-phase shift active hai. Background mein bhaari chal raha hoga.",
                "Discipline, simplicity, seva — Saturn yahi maang raha hai. Hanuman Chalisa daily helpful.")

    if tara_name == "Naidhana":
        return ("Naidhana Tara aaj — sabse inauspicious nakshatra friendship. Scattered, low-clarity feel hoga.",
                "Important calls/decisions kal pe tal do. Gayatri Mantra subah, reading/quiet work ke liye din.")

    if tara_name == "Vipat":
        return ("Vipat Tara — chhote-chhote obstacles aane ka din. Patience test hoga.",
                "Subah meditation, Ganesh mantra, schedule mein extra buffer rakho.")

    if (tithi_d.get("type") or "").startswith("Rikta"):
        rikta_extra = ""
        if score < 50:
            rikta_extra = " Aur score bhi low hai — combination heavy hai."
        return (f"Rikta Tithi ({tithi_d.get('tithi_name','—')}) — energy drain wala din classically.{rikta_extra}",
                "Naye launch/important meetings avoid. Routine maintenance + rest day banao.")

    # ── Helper: identify weakest / strongest component for reason text ────
    label_map = {"moon": "Moon transit", "tara": "Tara Bal",
                 "dasha": "Dasha", "av": "Ashtakavarga"}
    parts_sorted = sorted(parts.items(), key=lambda x: x[1])
    weak_label, weak_val = (parts_sorted[0] if parts_sorted else ("moon", 60))
    strong_label, strong_val = (parts_sorted[-1] if parts_sorted else ("moon", 60))

    md_sandhi_active = bool(details.get("md_sandhi"))
    sandhi_note = " Mahadasha sandhi (transition) bhi chal rahi — thodi disorientation feel ho sakti hai." if md_sandhi_active else ""

    # ── PRIORITY 2: Score-band defaults (when no critical signal) ─────────
    if score >= 85:
        return (f"Rare cosmic window — {label_map[strong_label]} ({int(strong_val)}/100) "
                "lead kar raha, chandra + tara + dasha sab align ho rahe. Energy peak pe.",
                "Important launches, conversations, signings ke liye perfect din. Use this — har din nahi milta.")

    if score >= 70:
        return (f"Aaj momentum hai — {label_map[strong_label]} strong support de raha "
                f"({int(strong_val)}/100), productive aur smooth feel hoga.",
                "Important kaam aaj nipta lo. Decisions, calls, exercise — sab favorable.")

    if score >= 55:
        nice_tithi = ""
        if (tithi_d.get("type") or "").startswith("Purna"):
            nice_tithi = f" {tithi_d.get('tithi_name','')} (Purna) ka subtle support hai."
        return (f"Steady neutral day — {label_map[weak_label]} thoda kam hai "
                f"({int(weak_val)}/100), isliye drama nahi magic bhi nahi.{nice_tithi}{sandhi_note}",
                "Apne regular kaam pe focus rakho. Major new commitments avoid, routine continue.")

    if score >= 40:
        return (f"Aaj thoda heavy/slow feel hoga — patience wala din, {label_map[weak_label]} "
                f"down hai ({int(weak_val)}/100), cosmic support kam hai.{sandhi_note}",
                "Light schedule, extra rest, exercise + meditation se reset karo. Bade decisions kal pe tal do.")

    return (f"Low-energy challenging din — {label_map[weak_label]} bahut weak ({int(weak_val)}/100), "
            f"bhari mehsoos hoga, normal hai is alignment ke saath.{sandhi_note}",
            "Aaj rest, journaling, mantra-japa. Self-care din hai — kal naturally better hoga.")


# ──────────────────────────────────────────────────────────────────────────────
# RISK RADAR — predictive, user-friendly risk surfacing layer (v1.0)
# Pure signal-mapping over existing engine output. NO new astrology compute.
# ──────────────────────────────────────────────────────────────────────────────

def compute_risk_radar(energy_result: Dict[str, Any],
                       birth_chart: Dict[str, Any],
                       today_planets: Optional[Dict[str, Dict[str, Any]]] = None
                       ) -> Dict[str, Any]:
    """
    Build a user-friendly Risk Radar (24h + 7d blocks) from existing
    engine signals. NO new astrology computation — pure signal mapping.

    Output schema (Hinglish, no astrology jargon):
      {
        "risk_radar_24h": [{level, title, reason, advice, timing?}],
        "risk_radar_7d":  [{range, level, label, advice}],
        "summary": "..."
      }

    Rules:
      - max 3 risks in 24h radar (severity-ranked)
      - never exposes MD/AD/PD/planet names
      - never uses "danger" / "bad future" language
      - always actionable advice
    """
    components = energy_result.get("components", {}) or {}
    overlays   = energy_result.get("overlays", {}) or {}
    flags      = energy_result.get("active_flags", []) or []

    moon_d     = components.get("moon_transit", {}) or {}
    tara_d     = components.get("tara_bal", {}) or {}
    saturn_d   = overlays.get("saturn", {}) or {}
    tithi_d    = overlays.get("tithi", {}) or {}
    pd_d       = overlays.get("pd_transit", {}) or {}
    jup_mars_d = overlays.get("jupiter_mars", {}) or {}
    time_q_d   = overlays.get("time_quality", {}) or {}

    volatile = bool(overlays.get("volatile_day", False))

    # ── 24h: collect candidate risks with severity scores ────────────────
    candidates: List[Dict[str, Any]] = []

    # Signal: Chandrashtama (Moon in 8th from natal Moon)
    if moon_d.get("chandrashtama"):
        candidates.append({
            "severity": 9, "level": "high",
            "title": "Emotional Instability",
            "reason": "Aaj mann thoda asthir aur sensitive feel ho sakta hai",
            "advice": "Emotional decisions postpone karein, calm rahein",
        })

    # Signal: Tara Bal (Vipat=2, Pratyak=4, Vadha/Naidhana=6)
    tara_idx = tara_d.get("tara_idx", -1)
    if tara_idx == 6:  # worst
        candidates.append({
            "severity": 8, "level": "high",
            "title": "Sensitive Day",
            "reason": "Mood thoda dheere aur reflective hoga aaj",
            "advice": "Important conversations kal ya parso ke liye rakhein",
        })
    elif tara_idx in (2, 4):
        candidates.append({
            "severity": 6, "level": "medium",
            "title": "Mental Drain",
            "reason": "Thakaan aur overthinking zyada ho sakti hai",
            "advice": "Aaj rest aur self-care prioritize karein",
        })

    # Signal: Saturn (Sade Sati / Ashtam / Kantaka)
    saturn_phase = saturn_d.get("phase", "") if saturn_d.get("active") else ""
    if "Madhya" in saturn_phase or "Ashtam" in saturn_phase:
        candidates.append({
            "severity": 8, "level": "high",
            "title": "Pressure Phase",
            "reason": "Andar se thoda heavy aur slow feel ho raha hai",
            "advice": "Patience rakhein, jaldbaazi mat karein — slow chalein",
        })
    elif ("Phase 1" in saturn_phase or "Phase 3" in saturn_phase
          or "Kantaka" in saturn_phase):
        candidates.append({
            "severity": 5, "level": "medium",
            "title": "Pressure Phase",
            "reason": "Background mein thoda burden chal raha hai",
            "advice": "Steady rahein, shortcuts avoid karein",
        })

    # Signal: Mars affliction (negative jupiter_mars overlay)
    jup_mars_delta = jup_mars_d.get("delta", 0) or 0
    mars_house = (jup_mars_d.get("mars_house")
                  or jup_mars_d.get("mars_house_lagna"))
    if jup_mars_delta < -3 or mars_house in (1, 4, 7, 8, 12):
        candidates.append({
            "severity": 7, "level": "medium",
            "title": "Conflict Risk",
            "reason": "Aaj jaldbaazi aur frustration zyada ho sakta hai",
            "advice": "Arguments aur impulsive reactions se bachein",
        })

    # Signal: PD weak (Pratyantar dasha lord struggling)
    pd_delta = pd_d.get("delta", 0) or 0
    if pd_delta <= -4:
        candidates.append({
            "severity": 6, "level": "medium",
            "title": "Delay Risk",
            "reason": "Kaam mein dheere progress hogi aaj",
            "advice": "Important deadlines mein flexibility rakhein",
        })

    # Signal: Tithi drain (Rikta) or Amavasya
    if tithi_d.get("type") == "Rikta (drain)":
        candidates.append({
            "severity": 5, "level": "medium",
            "title": "Low Energy Day",
            "reason": "Body aur mind dono mein energy thodi kam hogi",
            "advice": "Heavy commitments avoid karein, rest pe dhyan dein",
        })
    elif tithi_d.get("tithi_idx") == 30:  # Amavasya
        candidates.append({
            "severity": 6, "level": "medium",
            "title": "Low Energy Day",
            "reason": "Aaj din thoda heavy aur introspective rahega",
            "advice": "Naye kaam shuru mat karein, peace prioritize karein",
        })

    # Signal: Time-quality (Rahukal active or choghadiya inauspicious)
    rahukal_active = bool(time_q_d.get("rahukal")) or "rahukal" in flags
    if rahukal_active:
        candidates.append({
            "severity": 4, "level": "low",
            "title": "Sensitive Time Window",
            "reason": "Din mein kuch ghante thode kam shubh hain",
            "advice": "Rahukal ke samay nayi shuruwat ya important calls avoid karein",
            "timing": "Rahukal active",
        })

    # Signal: Volatile day flag (multiple negative signals stacked)
    if volatile:
        candidates.append({
            "severity": 10, "level": "high",
            "title": "Volatile Day",
            "reason": "Aaj kaafi mixed energy hai — ups aur downs honge",
            "advice": "Sambhal ke chalein, react kam karein, observe zyada",
        })

    # Sort by severity, take top 3
    candidates.sort(key=lambda r: r.get("severity", 0), reverse=True)
    risks_24h = candidates[:3]
    for r in risks_24h:
        r.pop("severity", None)

    # If no risks → positive baseline
    if not risks_24h:
        risks_24h.append({
            "level": "low",
            "title": "Stable Day",
            "reason": "Koi major risk nahi mil raha aaj",
            "advice": "Apne planned kaam smoothly aage badhayein",
        })

    # ── 7-day blocks: Moon nakshatra + Tara projection ────────────────────
    radar_7d = _compute_7d_blocks(birth_chart, today_planets,
                                  saturn_d, jup_mars_d, volatile)

    # Top-line summary (1 line)
    high_count = sum(1 for r in risks_24h if r["level"] == "high")
    if high_count >= 2:
        summary = "Aaj sambhal ke chalein — multiple sensitive signals active hain"
    elif high_count == 1:
        summary = "Aaj ek important area mein extra dhyan zaroori hai"
    elif risks_24h[0].get("level") == "low" and risks_24h[0].get("title") == "Stable Day":
        summary = "Aaj koi major risk nahi — aaram se kaam karein"
    else:
        summary = "Aaj kuch mixed signals hain — important kaam mein savdhaan rahein"

    return {
        "risk_radar_24h": risks_24h,
        "risk_radar_7d":  radar_7d,
        "summary":        summary,
    }


def _compute_7d_blocks(birth_chart: Dict[str, Any],
                       today_planets: Optional[Dict[str, Dict[str, Any]]],
                       saturn_d: Dict[str, Any],
                       jup_mars_d: Dict[str, Any],
                       volatile_today: bool) -> List[Dict[str, Any]]:
    """
    Project Moon position forward 7 days (~13.176°/day) and compute
    Tara nakshatra index per day. Aggregate into 3 blocks (1-2, 3-5, 6-7).
    Persistent malefic transits (Sade Sati, Mars affliction) carry forward
    as baseline pressure.
    """
    # Persistent baseline pressure (whole 7-day window)
    saturn_phase = saturn_d.get("phase", "") if saturn_d.get("active") else ""
    saturn_heavy = ("Madhya" in saturn_phase or "Ashtam" in saturn_phase)
    saturn_mild  = (bool(saturn_phase) and not saturn_heavy)

    jup_mars_delta = jup_mars_d.get("delta", 0) or 0
    mars_house = (jup_mars_d.get("mars_house")
                  or jup_mars_d.get("mars_house_lagna"))
    mars_active = (jup_mars_delta < -3 or mars_house in (1, 4, 7, 8, 12))

    # Birth nakshatra index
    birth_nak = -1
    if birth_chart and isinstance(birth_chart.get("nakshatra"), str):
        try:
            birth_nak = NAKSHATRAS.index(birth_chart["nakshatra"])
        except ValueError:
            birth_nak = -1
    if birth_nak < 0:
        # Try from planets[Moon]
        for p in (birth_chart.get("planets") or []):
            if p.get("name") == "Moon" and isinstance(p.get("longitude"), (int, float)):
                birth_nak = int(p["longitude"] / (360.0 / 27.0)) % 27
                break

    # Today's Moon longitude
    today_moon_lon = None
    if today_planets and isinstance(today_planets.get("Moon"), dict):
        today_moon_lon = today_planets["Moon"].get("longitude")

    # Compute per-day Tara score
    daily_scores: List[float] = []
    if today_moon_lon is not None and birth_nak >= 0:
        for i in range(7):
            proj_lon = (today_moon_lon + i * 13.176) % 360.0
            today_nak = int(proj_lon / (360.0 / 27.0)) % 27
            tara = (today_nak - birth_nak + 27) % 27 % 9
            daily_scores.append(float(TARA_SCORES[tara]))
    else:
        # No data → neutral
        daily_scores = [60.0] * 7

    # Apply persistent pressure to all days
    for i in range(7):
        if saturn_heavy:
            daily_scores[i] -= 12
        elif saturn_mild:
            daily_scores[i] -= 6
        if mars_active:
            daily_scores[i] -= 8
        if i == 0 and volatile_today:
            daily_scores[i] -= 10

    # Block aggregator
    def _block_label(scores: List[float]) -> Dict[str, Any]:
        avg = sum(scores) / max(len(scores), 1)
        weak_days = sum(1 for s in scores if s < 40)
        if avg < 35 or weak_days >= 2:
            return {"level": "high",
                    "label": "Sensitive Window",
                    "advice": "Important decisions postpone karein, rest pe focus"}
        if avg < 50 or weak_days >= 1:
            return {"level": "medium",
                    "label": "Mixed Phase",
                    "advice": "Patience rakhein, react kam karein"}
        if avg >= 70:
            return {"level": "low",
                    "label": "Smooth Phase",
                    "advice": "Naye kaam shuru karne ke liye accha samay"}
        return {"level": "low",
                "label": "Stable Phase",
                "advice": "Normal kaam smoothly chalega"}

    block1 = _block_label(daily_scores[0:2])
    block2 = _block_label(daily_scores[2:5])
    block3 = _block_label(daily_scores[5:7])

    return [
        {"range": "Day 1-2", **block1},
        {"range": "Day 3-5", **block2},
        {"range": "Day 6-7", **block3},
    ]


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────────────────────────────────────

def calculate_energy(user_data: Dict[str, Any],
                     today_moon: Dict[str, Any],
                     date_iso: Optional[str] = None,
                     today_sun: Optional[Dict[str, Any]] = None,
                     today_saturn: Optional[Dict[str, Any]] = None,
                     today_planets: Optional[Dict[str, Dict[str, Any]]] = None,
                     now_local: Optional[datetime] = None,
                     birth_lat: Optional[float] = None,
                     birth_lon: Optional[float] = None,
                     tz_offset: float = 5.5,
                     ) -> Dict[str, Any]:
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
    today_planets (optional, NEW for v3.1 5-step upgrade):
        - dict {planet_name: {longitude, rashiIndex}} for all 7 grahas + Rahu/Ketu
        - powers Steps 1, 2, 5 (transit aspects, Jupiter/Mars overlay, PD transit)
        - falls back to today_sun/today_saturn if not provided
    now_local (optional, NEW for v3.1):
        - local datetime for the user's timezone (default IST)
        - powers Step 3 (Choghadiya + Hora)
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
    # Birth Sun sign (for Step 1 — Jupiter→natal Sun aspect)
    birth_sun_sign: Optional[int] = _sign_map.get("Sun") if "Sun" in _sign_map else None

    # v3.2: birth Moon/Sun longitudes for degree-based aspects (Step 1)
    birth_moon_lon: Optional[float] = None
    birth_sun_lon:  Optional[float] = None
    for _p in planets:
        if not isinstance(_p, dict):
            continue
        nm = _p.get("name")
        ln = _p.get("lon")
        if nm == "Moon" and isinstance(ln, (int, float)):
            birth_moon_lon = float(ln) % 360.0
        elif nm == "Sun" and isinstance(ln, (int, float)):
            birth_sun_lon = float(ln) % 360.0

    # ── Moon-Sun angle at birth (for Paksha Bala inside Shadbala) ────────
    moon_sun_angle: Optional[float] = None
    _lon_map = {p.get("name"): p.get("lon") for p in planets
                if isinstance(p.get("lon"), (int, float))}
    if "Moon" in _lon_map and "Sun" in _lon_map:
        moon_sun_angle = (_lon_map["Moon"] - _lon_map["Sun"]) % 360.0

    # ── Resolve transit longitudes for overlays ──────────────────────────
    sun_today_lon: Optional[float] = (today_sun or {}).get("longitude") if isinstance(today_sun, dict) else None
    sat_today_lon: Optional[float] = (today_saturn or {}).get("longitude") if isinstance(today_saturn, dict) else None
    saturn_sign: Optional[int] = (today_saturn or {}).get("rashiIndex") if isinstance(today_saturn, dict) else None
    if saturn_sign is None and isinstance(sat_today_lon, (int, float)):
        saturn_sign = int(sat_today_lon / 30) % 12

    # ── Build transit_signs dict (preferred from today_planets, fallback) ─
    transit_signs: Dict[str, int] = {}
    if today_planets:
        for pname, pdata in today_planets.items():
            if not isinstance(pdata, dict):
                continue
            sidx = pdata.get("rashiIndex")
            if sidx is None and isinstance(pdata.get("longitude"), (int, float)):
                sidx = int(pdata["longitude"] / 30) % 12
            if isinstance(sidx, int):
                transit_signs[pname] = sidx % 12
    # Backward-compat fallback for callers that didn't pass today_planets
    if "Moon" not in transit_signs and isinstance(moon_sign, int):
        transit_signs["Moon"] = moon_sign
    if "Sun" not in transit_signs and isinstance(today_sun, dict):
        s = today_sun.get("rashiIndex")
        if s is None and isinstance(sun_today_lon, (int, float)):
            s = int(sun_today_lon / 30) % 12
        if isinstance(s, int):
            transit_signs["Sun"] = s
    if "Saturn" not in transit_signs and isinstance(saturn_sign, int):
        transit_signs["Saturn"] = saturn_sign

    mars_sign    = transit_signs.get("Mars")
    jupiter_sign = transit_signs.get("Jupiter")

    # v3.2: degree-precision transit longitudes for aspect engine
    def _planet_lon(name: str) -> Optional[float]:
        if today_planets and isinstance(today_planets.get(name), dict):
            ln = today_planets[name].get("longitude")
            if isinstance(ln, (int, float)):
                return float(ln) % 360.0
        return None
    mars_today_lon    = _planet_lon("Mars")
    jupiter_today_lon = _planet_lon("Jupiter")
    saturn_today_lon  = sat_today_lon if isinstance(sat_today_lon, (int, float)) else _planet_lon("Saturn")

    # ── Components (Aspect/Shadbala dropped — static birth chart) ────────
    dasha_sc,  dasha_d  = compute_dasha_score(user_data, today, lagna_sign)
    moon_sc,   moon_d   = compute_moon_transit_score(moon_sign, lagna_sign, birth_moon_sign)
    av_sc,     av_d     = compute_ashtakavarga_score(planets, lagna_sign, moon_sign)
    tara_sc,   tara_d   = compute_tara_score(moon_nak, birth_nak_idx)

    # ── Weighted aggregate (TRANSIT-FIRST v2 — 2026-04-25) ───────────────
    # 75% of the score is Moon-driven (transit 35 + tara 25 + AV 15) because
    # Vedic principle: Moon = mind = daily mood. Dasha (25%) gives backdrop
    # tilt. Aspect/Shadbala dropped — it's pure birth-chart strength, never
    # changes daily, was a wasted slot.
    base_energy = (moon_sc * 0.35 + tara_sc * 0.25
                   + dasha_sc * 0.25 + av_sc * 0.15)

    # ── Overlays ─────────────────────────────────────────────────────────
    saturn_delta, saturn_d = compute_saturn_overlay(saturn_sign, birth_moon_sign)
    tithi_delta,  tithi_d  = compute_tithi_overlay(sun_today_lon, moon_lon)
    tithi_mental_extra = float(tithi_d.get("mental_extra") or 0.0)  # STEP 4

    # Inject delta into saturn_d so downstream summary/confidence/flags can read it
    saturn_d = {**saturn_d, "delta": saturn_delta}

    # ── Mahadasha Sandhi (transition window penalty) ─────────────────────
    dashas_list = (user_data.get("dashas")
                   or (user_data.get("chart_data") or {}).get("dashas") or [])
    md_sandhi = _detect_md_sandhi(dashas_list, today)
    md_sandhi_delta = -5.0 if md_sandhi else 0.0

    # ── STEP 1: Transit-to-natal aspects ─────────────────────────────────
    # FIX 1: when Sade Sati / Dhaiyya already firing (saturn_d.active),
    # skip the Saturn aspect inside Step 1 to prevent double penalty.
    aspect_delta, transit_aspects_d = compute_transit_natal_aspects(
        saturn_sign, mars_sign, jupiter_sign,
        birth_moon_sign, birth_sun_sign,
        skip_saturn=bool(saturn_d.get("active")),
        # v3.2 degree-precision (auto-falls-back to sign mode if any None)
        saturn_today_lon=saturn_today_lon,
        mars_today_lon=mars_today_lon,
        jupiter_today_lon=jupiter_today_lon,
        birth_moon_lon=birth_moon_lon,
        birth_sun_lon=birth_sun_lon,
    )

    # ── STEP 2: Jupiter & Mars current-transit overlay (Lagna+Moon blend) ─
    jup_mars_delta, jup_mars_d = compute_jupiter_mars_overlay(
        jupiter_sign, mars_sign, lagna_sign, birth_moon_sign,
    )

    # ── STEP 3: Choghadiya + Hora time-of-day overlay (per-city sun-times) ─
    time_quality_delta, time_quality_d = compute_choghadiya_hora_overlay(
        now_local, lat=birth_lat, lon=birth_lon, tz_offset=tz_offset,
    )

    # ── STEP 5: PD lord current-transit house check (Lagna+Moon blend) ───
    pd_planet_for_transit = (dasha_d.get("pd") or {}).get("planet") if isinstance(dasha_d, dict) else None
    pd_transit_delta, pd_transit_d = compute_pd_transit_overlay(
        pd_planet_for_transit, transit_signs, lagna_sign, birth_moon_sign,
    )

    # ── FIX 2: Global negative-stack cap (-35) ───────────────────────────
    # Multiple penalties (Saturn + Mars + Tithi + Rahukal + ...) can crush
    # the score to unrealistic 10-20 range. Sum negative-only deltas; if
    # they exceed -35, scale them proportionally so total negative = -35.
    # Positives are NOT clamped — only the penalty side is bounded.
    overlay_deltas = {
        "saturn":         saturn_delta,
        "tithi":          tithi_delta,
        "md_sandhi":      md_sandhi_delta,
        "aspects":        aspect_delta,
        "jupiter_mars":   jup_mars_delta,
        "time_quality":   time_quality_delta,
        "pd_transit":     pd_transit_delta,
    }
    neg_sum = sum(v for v in overlay_deltas.values() if v < 0)
    pos_sum = sum(v for v in overlay_deltas.values() if v > 0)
    neg_cap_active = False
    if neg_sum < -35.0:
        scale = -35.0 / neg_sum  # neg_sum is negative → scale ∈ (0, 1)
        for k, v in overlay_deltas.items():
            if v < 0:
                overlay_deltas[k] = v * scale
        neg_cap_active = True
        # Re-extract scaled values back to named locals so downstream blocks
        # (response payload, flags) see the post-cap deltas.
        saturn_delta_scaled       = overlay_deltas["saturn"]
        tithi_delta_scaled        = overlay_deltas["tithi"]
        md_sandhi_delta_scaled    = overlay_deltas["md_sandhi"]
        aspect_delta_scaled       = overlay_deltas["aspects"]
        jup_mars_delta_scaled     = overlay_deltas["jupiter_mars"]
        time_quality_delta_scaled = overlay_deltas["time_quality"]
        pd_transit_delta_scaled   = overlay_deltas["pd_transit"]
    else:
        saturn_delta_scaled       = saturn_delta
        tithi_delta_scaled        = tithi_delta
        md_sandhi_delta_scaled    = md_sandhi_delta
        aspect_delta_scaled       = aspect_delta
        jup_mars_delta_scaled     = jup_mars_delta
        time_quality_delta_scaled = time_quality_delta
        pd_transit_delta_scaled   = pd_transit_delta

    raw_energy = (base_energy
                  + saturn_delta_scaled + tithi_delta_scaled + md_sandhi_delta_scaled
                  + aspect_delta_scaled + jup_mars_delta_scaled
                  + time_quality_delta_scaled + pd_transit_delta_scaled)

    # ── Compression curve (pulls high end down) ──────────────────────────
    compressed = _compress_high_end(raw_energy)
    energy = max(0.0, min(100.0, compressed))

    # ── HARD CAP: Sade Sati Madhya peak cannot show as a "good day" ──────
    # Critical trust-rule: if user is in Janma Rashi Saturn transit they
    # ARE feeling heavy — score must reflect that, never break trust.
    # Cap at 59 (NOT 60) so _category() returns "Moderate" not "Good"
    # (boundary is score < 60 → Moderate). 60 itself would still display
    # as "Good" while summary says "heavy", a trust-contradiction.
    # Note: uses ORIGINAL saturn_delta (pre-FIX-2 scaling) so the cap still
    # triggers correctly even when neg-stack scaling diluted the saturn
    # contribution to keep the total above -35.
    sade_sati_madhya = (saturn_d.get("active")
                        and saturn_delta <= -20)
    if sade_sati_madhya:
        energy = min(energy, 59.0)

    score  = int(round(energy))
    cat, color = _category(energy)

    parts   = {"moon": moon_sc, "tara": tara_sc, "dasha": dasha_sc, "av": av_sc}
    details = {"dasha_detail": dasha_d, "moon_detail": moon_d,
               "av_detail": av_d, "tara_detail": tara_d,
               "saturn_overlay": saturn_d, "tithi_overlay": tithi_d,
               "md_sandhi": md_sandhi}
    summary, advice = _summary_and_advice(energy, parts, details)

    # ── PD lord retrograde advisory (appended to advice) ─────────────────
    pd_planet = (dasha_d.get("pd") or {}).get("planet") if isinstance(dasha_d, dict) else None
    retrograde_pd = _check_pd_retrograde(pd_planet, planets)
    if retrograde_pd:
        advice = (advice + f" Note: Pratyantar lord {retrograde_pd} abhi vakri (retrograde) "
                           "hai — results thode delayed mil sakte, patience rakho.")

    # ── Buckets, confidence, flags ───────────────────────────────────────
    # Buckets use ORIGINAL deltas (not Fix-2 scaled) so each bucket reflects
    # true overlay strength even when global cap diluted total raw_energy.
    buckets = _compute_buckets(moon_sc, tara_sc, dasha_sc, av_sc,
                                saturn_delta, tithi_delta,
                                tithi_mental_extra)   # STEP 4: mental-only
    confidence = _compute_confidence(parts, saturn_d, tithi_d, moon_d, tara_d)
    active_flags = _build_active_flags(
        saturn_d, tithi_d, moon_d, tara_d, md_sandhi, retrograde_pd,
        transit_aspects_d=transit_aspects_d,
        jup_mars_d=jup_mars_d,
        time_quality_d=time_quality_d,
        pd_transit_d=pd_transit_d,
    )

    # ── FIX 4: Volatile day detection ────────────────────────────────────
    # Count how many distinct major-negative signals are firing today. If
    # 3 or more stack simultaneously, the day is "unstable" — emit a flag
    # and append a Hinglish stability nudge to the advice.
    neg_signals = []
    if saturn_d.get("active") and saturn_delta <= -10:
        neg_signals.append("saturn_phase")
    if "saturn_opposition_natal_moon" in (transit_aspects_d.get("aspects") or []):
        neg_signals.append("saturn_aspect")
    if "mars_hit_natal_moon" in (transit_aspects_d.get("aspects") or []):
        neg_signals.append("mars_hit_moon")
    if moon_d.get("chandrashtama"):
        neg_signals.append("chandrashtama")
    if (tithi_d.get("type") or "").startswith("Rikta"):
        neg_signals.append("rikta_tithi")
    if tithi_d.get("special") == "amavasya":
        neg_signals.append("amavasya")
    tara_name = (tara_d.get("tara") or "")
    if tara_name in {"Vipat", "Pratyari", "Naidhana"}:
        neg_signals.append(f"tara_{tara_name.lower()}")
    if time_quality_d.get("rahukal"):
        neg_signals.append("rahukal")
    if jup_mars_d.get("mars_aspect_moon") or (
        jup_mars_d.get("mars_house") in {6, 8, 12}
    ):
        neg_signals.append("mars_house_or_aspect")
    if pd_transit_d.get("kind") == "dusthana":
        neg_signals.append("pd_dusthana")
    if md_sandhi:
        neg_signals.append("md_sandhi")

    volatile_day = len(neg_signals) >= 3
    if volatile_day:
        active_flags.append({
            "type":     "volatile_day",
            "severity": "medium",
            "signals":  neg_signals,
        })
        advice = (advice + " Aaj energy unstable ho sakti hai — "
                           "consistency maintain karna important hai.")

    return {
        "energy_score":     score,
        "overall_score":    score,        # alias for new API consumers
        "category":         cat,
        "color":            color,
        "confidence":       confidence,
        "summary":          summary,
        "advice":           advice,
        "date":             today,
        "buckets":          buckets,
        "active_flags":     active_flags,
        "feedback_enabled": True,
        "feedback_adjustment": 0,
        "components": {
            "moon_transit":   {"score": round(moon_sc, 1),  "weight": 0.35, **moon_d},
            "tara_bal":       {"score": round(tara_sc, 1),  "weight": 0.25, **tara_d},
            "dasha":          {"score": round(dasha_sc, 1), "weight": 0.25, **dasha_d},
            "ashtakavarga":   {"score": round(av_sc, 1),    "weight": 0.15, **av_d},
        },
        "overlays": {
            "saturn":            {"delta": saturn_delta, **saturn_d},
            "tithi":             {"delta": tithi_delta,  **tithi_d},
            "md_sandhi":         {"active": md_sandhi, "delta": md_sandhi_delta},
            # STEP 1 — transit aspects to natal Moon/Sun
            "transit_aspects":   {"delta": aspect_delta, **transit_aspects_d},
            # STEP 2 — Jupiter & Mars current-transit overlay
            "jupiter_mars":      {"delta": jup_mars_delta, **jup_mars_d},
            # STEP 3 — Choghadiya / Hora time-of-day quality
            "time_quality":      {"delta": time_quality_delta, **time_quality_d},
            # STEP 5 — PD lord transiting house from lagna
            "pd_transit":        {"delta": pd_transit_delta, **pd_transit_d},
            # FIX 2 — global negative-stack cap meta
            "negative_cap": {
                "active":          neg_cap_active,
                "cap":             -35.0,
                "raw_negative":    round(neg_sum, 2),
                "raw_positive":    round(pos_sum, 2),
            },
            # FIX 4 — volatile-day flag mirrored into overlays for clients
            "volatile_day":      bool(volatile_day),
            "base_score":        round(base_energy, 1),
            "after_overlays":    round(raw_energy, 1),
            "after_compression": round(compressed, 1),
            "after_hard_cap":    score,
        },
    }

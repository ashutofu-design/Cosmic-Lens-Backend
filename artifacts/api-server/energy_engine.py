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

    detail = {
        "tithi_idx":   tithi_idx,
        "paksha":      paksha_name,
        "paksha_pos":  paksha_pos,
        "tithi_name":  f"{paksha_name} {tithi_name}",
    }

    if paksha_pos in {4, 9, 14}:
        return -5.0, {**detail, "type": "Rikta (drain)"}
    if paksha_pos in {5, 10, 15}:
        return 5.0, {**detail, "type": "Purna (peak)"}
    return 0.0, {**detail, "type": "Neutral"}


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

    # ── PRIORITY 2: Score-band defaults (when no critical signal) ─────────
    if score >= 85:
        return ("Rare cosmic window — chandra + tara + dasha sab align ho rahe aaj. Energy peak pe.",
                "Important launches, conversations, signings ke liye perfect din. Use this — har din nahi milta.")

    if score >= 70:
        return ("Aaj momentum hai — productive aur smooth feel hoga. Planetary support strong.",
                "Important kaam aaj nipta lo. Decisions, calls, exercise — sab favorable.")

    if score >= 55:
        nice_tithi = ""
        if (tithi_d.get("type") or "").startswith("Purna"):
            nice_tithi = f" {tithi_d.get('tithi_name','')} (Purna) ka subtle support hai."
        return (f"Steady neutral day — drama nahi, magic bhi nahi.{nice_tithi}",
                "Apne regular kaam pe focus rakho. Major new commitments avoid, routine continue.")

    if score >= 40:
        return ("Aaj thoda heavy/slow feel hoga — patience wala din. Cosmic support kam hai.",
                "Light schedule, extra rest, exercise + meditation se reset karo. Bade decisions kal pe tal do.")

    return ("Low-energy challenging din — bhari mehsoos hoga, normal hai is alignment ke saath.",
            "Aaj rest, journaling, mantra-japa. Self-care din hai — kal naturally better hoga.")


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────────────────────────────────────

def calculate_energy(user_data: Dict[str, Any],
                     today_moon: Dict[str, Any],
                     date_iso: Optional[str] = None,
                     today_sun: Optional[Dict[str, Any]] = None,
                     today_saturn: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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

    raw_energy = base_energy + saturn_delta + tithi_delta

    # ── Compression curve (pulls high end down) ──────────────────────────
    compressed = _compress_high_end(raw_energy)
    energy = max(0.0, min(100.0, compressed))
    score  = int(round(energy))
    cat, color = _category(energy)

    parts   = {"moon": moon_sc, "tara": tara_sc, "dasha": dasha_sc, "av": av_sc}
    details = {"dasha_detail": dasha_d, "moon_detail": moon_d,
               "av_detail": av_d, "tara_detail": tara_d,
               "saturn_overlay": saturn_d, "tithi_overlay": tithi_d}
    summary, advice = _summary_and_advice(energy, parts, details)

    return {
        "energy_score": score,
        "category":     cat,
        "color":        color,
        "summary":      summary,
        "advice":       advice,
        "date":         today,
        "components": {
            "moon_transit":   {"score": round(moon_sc, 1),  "weight": 0.35, **moon_d},
            "tara_bal":       {"score": round(tara_sc, 1),  "weight": 0.25, **tara_d},
            "dasha":          {"score": round(dasha_sc, 1), "weight": 0.25, **dasha_d},
            "ashtakavarga":   {"score": round(av_sc, 1),    "weight": 0.15, **av_d},
        },
        "overlays": {
            "saturn":     {"delta": saturn_delta, **saturn_d},
            "tithi":      {"delta": tithi_delta,  **tithi_d},
            "base_score": round(base_energy, 1),
            "after_overlays": round(raw_energy, 1),
            "after_compression": round(compressed, 1),
        },
    }

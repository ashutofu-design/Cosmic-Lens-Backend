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

def compute_transit_natal_aspects(
    saturn_today_sign: Optional[int],
    mars_today_sign:   Optional[int],
    jupiter_today_sign: Optional[int],
    birth_moon_sign:   Optional[int],
    birth_sun_sign:    Optional[int],
) -> Tuple[float, Dict[str, Any]]:
    """
    Step 1: Basic transit interactions with natal Moon & Sun.

    Sign-based conjunction (1st = same sign) or opposition (7th from natal).
    Saturn-Moon conjunction is intentionally SKIPPED here because Sade Sati
    Madhya overlay already handles that case (would be double-counted).

    - Transit Saturn  → natal Moon  (opposition only): -12
    - Transit Mars    → natal Moon  (conj or opp):     -8
    - Transit Jupiter → natal Moon (conj/trine 1/5/9): +10
    - Transit Jupiter → natal Sun  (conj/trine 1/5/9): +10
      (Jupiter→Moon and Jupiter→Sun do not stack; max +10 from this step)
    """
    delta = 0.0
    aspects: List[str] = []

    # Saturn → natal Moon (opposition only; conjunction handled by Sade Sati)
    if saturn_today_sign is not None and birth_moon_sign is not None:
        from_natal = ((saturn_today_sign - birth_moon_sign) % 12) + 1
        if from_natal == 7:
            delta -= 12
            aspects.append("saturn_opposition_natal_moon")

    # Mars → natal Moon (conjunction OR opposition)
    if mars_today_sign is not None and birth_moon_sign is not None:
        from_natal = ((mars_today_sign - birth_moon_sign) % 12) + 1
        if from_natal in {1, 7}:
            delta -= 8
            aspects.append("mars_hit_natal_moon")

    # Jupiter → natal Moon OR natal Sun (conjunction or trine 5/9). Cap at +10.
    jupiter_support = False
    jupiter_target: Optional[str] = None
    if jupiter_today_sign is not None and birth_moon_sign is not None:
        from_natal = ((jupiter_today_sign - birth_moon_sign) % 12) + 1
        if from_natal in {1, 5, 9}:
            jupiter_support = True
            jupiter_target = "Moon"
    if (not jupiter_support
        and jupiter_today_sign is not None
        and birth_sun_sign is not None):
        from_natal = ((jupiter_today_sign - birth_sun_sign) % 12) + 1
        if from_natal in {1, 5, 9}:
            jupiter_support = True
            jupiter_target = "Sun"
    if jupiter_support:
        delta += 10
        aspects.append(f"jupiter_support_natal_{(jupiter_target or '').lower()}")

    return delta, {
        "aspects": aspects,
        "delta":   delta,
        "active":  bool(aspects),
    }


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2 — Jupiter & Mars Overlay Layer (lagna-relative house placement)
# ──────────────────────────────────────────────────────────────────────────────

def compute_jupiter_mars_overlay(
    jupiter_today_sign: Optional[int],
    mars_today_sign:    Optional[int],
    lagna_sign:         Optional[int],
    birth_moon_sign:    Optional[int],
) -> Tuple[float, Dict[str, Any]]:
    """
    Step 2: Lagna-relative current-transit overlay for Jupiter & Mars.

    - Jupiter in kendra/trikona (1,4,5,7,9,10): +6
    - Jupiter in dusthana       (6,8,12)     : +2 only (still benefic but muted)
    - Mars    in dusthana       (6,8,12)     : -6
    - Mars aspect Moon (same-sign or opposition from natal Moon): extra -4
      (compounds with Step 1's -8 when both fire → Mars-Moon hit can be -12)

    Returns (delta, detail). Flags are stored inside detail['flags'].
    """
    delta = 0.0
    flags: List[str] = []
    detail: Dict[str, Any] = {
        "jupiter_house": None,
        "mars_house":    None,
        "mars_aspect_moon": False,
        "flags": flags,
    }

    # Jupiter house from lagna
    if jupiter_today_sign is not None and lagna_sign is not None:
        jh = ((jupiter_today_sign - lagna_sign) % 12) + 1
        detail["jupiter_house"] = jh
        if jh in KENDRA_TRIKONA:
            delta += 6
            flags.append("jupiter_support")
        elif jh in DUSHTHANA:
            delta += 2
            flags.append("jupiter_neutral")

    # Mars house from lagna
    if mars_today_sign is not None and lagna_sign is not None:
        mh = ((mars_today_sign - lagna_sign) % 12) + 1
        detail["mars_house"] = mh
        if mh in DUSHTHANA:
            delta -= 6
            flags.append("mars_conflict")

    # Mars aspect Moon (extra -4 when same-sign or opposition from natal Moon)
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
# sunrise (assumed 06:00 local) to sunset (assumed 18:00 local) → 1.5 hr each.
_RAHUKAL_SEGMENT = {
    0: 2,  # Mon  : 07:30-09:00
    1: 7,  # Tue  : 15:00-16:30
    2: 5,  # Wed  : 12:00-13:30
    3: 6,  # Thu  : 13:30-15:00
    4: 4,  # Fri  : 10:30-12:00
    5: 3,  # Sat  : 09:00-10:30
    6: 8,  # Sun  : 16:30-18:00
}


def _current_hora_lord(weekday: int, hour: int) -> str:
    """
    Returns the planetary lord of the current hora.

    First hora of the day (starting at assumed sunrise 06:00) is ruled by the
    weekday's lord. Subsequent horas cycle through the Chaldean order.
    """
    day_lord = _WEEKDAY_LORDS[weekday]
    start_idx = _CHALDEAN.index(day_lord)
    hours_since_sunrise = (hour - 6) % 24
    return _CHALDEAN[(start_idx + hours_since_sunrise) % 7]


def _is_rahukal(weekday: int, hour: int, minute: int = 0) -> bool:
    """True if local time falls inside today's Rahukal window."""
    seg = _RAHUKAL_SEGMENT.get(weekday)
    if seg is None:
        return False
    seg_start = 6 + (seg - 1) * 1.5
    seg_end   = seg_start + 1.5
    current   = hour + minute / 60.0
    return seg_start <= current < seg_end


def compute_choghadiya_hora_overlay(
    now_local: Optional[datetime],
) -> Tuple[float, Dict[str, Any]]:
    """
    Step 3: Time-of-day quality overlay (Rahukal + Hora).

    - Rahukal active                 : -6
    - Malefic hora (Saturn/Mars)     : -3
    - Benefic hora (Jupiter/Venus)   : +3

    No-op if now_local is missing.
    """
    if now_local is None:
        return 0.0, {"active": False, "reason": "no_local_time"}

    weekday = now_local.weekday()
    hour    = now_local.hour
    minute  = now_local.minute

    delta = 0.0
    flags: List[str] = []

    rahukal = _is_rahukal(weekday, hour, minute)
    if rahukal:
        delta -= 6
        flags.append("rahukal")

    hora_lord = _current_hora_lord(weekday, hour)
    hora_kind: Optional[str] = None
    if hora_lord in {"Saturn", "Mars"}:
        delta -= 3
        hora_kind = "malefic"
        flags.append("hora_malefic")
    elif hora_lord in {"Jupiter", "Venus"}:
        delta += 3
        hora_kind = "benefic"
        flags.append("hora_benefic")

    return delta, {
        "active":    bool(flags),
        "rahukal":   rahukal,
        "hora_lord": hora_lord,
        "hora_kind": hora_kind,
        "weekday":   weekday,
        "hour":      hour,
        "delta":     delta,
        "flags":     flags,
    }


# ──────────────────────────────────────────────────────────────────────────────
# STEP 5 — Dasha Lord (PD) Current Transit House Check
# ──────────────────────────────────────────────────────────────────────────────

def compute_pd_transit_overlay(
    pd_planet:      Optional[str],
    transit_signs:  Dict[str, int],
    lagna_sign:     Optional[int],
) -> Tuple[float, Dict[str, Any]]:
    """
    Step 5: Where is the Pratyantar Dasha lord transiting RIGHT NOW
    relative to the user's lagna?

    - PD lord in dusthana (6, 8, 12) from lagna : -8
    - PD lord in 1, 5, 9, 10 from lagna         : +5
    - else                                       :  0
    """
    if not pd_planet or lagna_sign is None:
        return 0.0, {"active": False, "reason": "missing_pd_or_lagna"}
    pd_sign = transit_signs.get(pd_planet) if transit_signs else None
    if pd_sign is None:
        return 0.0, {"active": False, "reason": "no_transit_sign_for_pd_lord",
                     "pd_planet": pd_planet}

    pd_house = ((pd_sign - lagna_sign) % 12) + 1

    if pd_house in DUSHTHANA:
        return -8.0, {
            "active":    True,
            "pd_planet": pd_planet,
            "pd_house":  pd_house,
            "kind":      "dusthana",
            "delta":     -8.0,
        }
    if pd_house in {1, 5, 9, 10}:
        return 5.0, {
            "active":    True,
            "pd_planet": pd_planet,
            "pd_house":  pd_house,
            "kind":      "kendra_trikona",
            "delta":     5.0,
        }
    return 0.0, {
        "active":    False,
        "pd_planet": pd_planet,
        "pd_house":  pd_house,
        "kind":      "neutral",
        "delta":     0.0,
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
# PUBLIC API
# ──────────────────────────────────────────────────────────────────────────────

def calculate_energy(user_data: Dict[str, Any],
                     today_moon: Dict[str, Any],
                     date_iso: Optional[str] = None,
                     today_sun: Optional[Dict[str, Any]] = None,
                     today_saturn: Optional[Dict[str, Any]] = None,
                     today_planets: Optional[Dict[str, Dict[str, Any]]] = None,
                     now_local: Optional[datetime] = None,
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
    aspect_delta, transit_aspects_d = compute_transit_natal_aspects(
        saturn_sign, mars_sign, jupiter_sign,
        birth_moon_sign, birth_sun_sign,
    )

    # ── STEP 2: Jupiter & Mars current-transit overlay ───────────────────
    jup_mars_delta, jup_mars_d = compute_jupiter_mars_overlay(
        jupiter_sign, mars_sign, lagna_sign, birth_moon_sign,
    )

    # ── STEP 3: Choghadiya + Hora time-of-day overlay ────────────────────
    time_quality_delta, time_quality_d = compute_choghadiya_hora_overlay(now_local)

    # ── STEP 5: PD lord current-transit house check ──────────────────────
    pd_planet_for_transit = (dasha_d.get("pd") or {}).get("planet") if isinstance(dasha_d, dict) else None
    pd_transit_delta, pd_transit_d = compute_pd_transit_overlay(
        pd_planet_for_transit, transit_signs, lagna_sign,
    )

    raw_energy = (base_energy
                  + saturn_delta + tithi_delta + md_sandhi_delta
                  + aspect_delta + jup_mars_delta
                  + time_quality_delta + pd_transit_delta)

    # ── Compression curve (pulls high end down) ──────────────────────────
    compressed = _compress_high_end(raw_energy)
    energy = max(0.0, min(100.0, compressed))

    # ── HARD CAP: Sade Sati Madhya peak cannot show as a "good day" ──────
    # Critical trust-rule: if user is in Janma Rashi Saturn transit they
    # ARE feeling heavy — score must reflect that, never break trust.
    # Cap at 59 (NOT 60) so _category() returns "Moderate" not "Good"
    # (boundary is score < 60 → Moderate). 60 itself would still display
    # as "Good" while summary says "heavy", a trust-contradiction.
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
            "base_score":        round(base_energy, 1),
            "after_overlays":    round(raw_energy, 1),
            "after_compression": round(compressed, 1),
            "after_hard_cap":    score,
        },
    }

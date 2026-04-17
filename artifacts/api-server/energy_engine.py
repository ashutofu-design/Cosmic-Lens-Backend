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


def _score_dasha_planet(planet: str, house: Optional[int]) -> int:
    """Score a single dasha lord 0-100 based on placement + nature."""
    nat = _classify(planet)
    if house is None:
        # Unknown placement — fall back to nature-only.
        return {"benefic": 70, "malefic": 45, "neutral": 60}[nat]

    if nat == "benefic":
        if house in KENDRA_TRIKONA: return 90       # benefic in best houses
        if house in DUSHTHANA:      return 55       # benefic in dushthana
        return 75                                   # benefic in 2/3/11
    if nat == "malefic":
        if house in DUSHTHANA:      return 38       # malefic in 6/8/12
        if house in KENDRA_TRIKONA: return 60       # malefic in kendra
        return 50                                   # malefic in 2/3/11
    # neutral
    if house in KENDRA_TRIKONA: return 75
    if house in DUSHTHANA:      return 45
    return 60


def compute_dasha_score(kundli: Dict[str, Any],
                        today: str) -> Tuple[float, Dict[str, Any]]:
    """Return (score 0-100, detail dict) for current MD/AD/PD."""
    dashas = kundli.get("dashas") or kundli.get("chart_data", {}).get("dashas")
    if not dashas:
        return 60.0, {"reason": "no_dasha_data", "md": None, "ad": None, "pd": None}

    md, ad, pd = _resolve_current_dasha(dashas, today)
    houses = _planet_house_lookup(kundli.get("planets") or
                                  kundli.get("chart_data", {}).get("planets") or [])

    parts: List[int] = []
    detail: Dict[str, Any] = {}
    for label, planet in (("md", md), ("ad", ad), ("pd", pd)):
        if not planet:
            continue
        sc = _score_dasha_planet(planet, houses.get(planet))
        detail[label] = {"planet": planet, "house": houses.get(planet), "score": sc}
        parts.append(sc)

    if not parts:
        return 60.0, {"reason": "no_active_period", **detail}
    return float(sum(parts) / len(parts)), detail


# ──────────────────────────────────────────────────────────────────────────────
# 2. MOON TRANSIT SCORE (25%)
# ──────────────────────────────────────────────────────────────────────────────

def compute_moon_transit_score(moon_today_sign: int,
                               lagna_sign: int) -> Tuple[float, Dict[str, Any]]:
    house = ((moon_today_sign - lagna_sign) % 12) + 1
    if house in {1, 5, 9, 10}: score = 85
    elif house in {2, 3, 7, 11}: score = 70
    else: score = 42  # 4,6,8,12
    return float(score), {"house": house, "moon_sign": moon_today_sign}


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

    # Normalise: 28 average → 50, 56 max → 100, 0 → 0
    score = max(0.0, min(100.0, (total / 56.0) * 100.0 * 1.6))  # 1.6× boost
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

    # ── Components ───────────────────────────────────────────────────────
    dasha_sc,  dasha_d  = compute_dasha_score(user_data, today)
    moon_sc,   moon_d   = compute_moon_transit_score(moon_sign, lagna_sign)
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

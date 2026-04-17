"""
Shadbala — the classical 6-fold planetary strength computation.

Measured in *virupas* (60 virupas = 1 rupa).  Total Shadbala is the sum of the
six sources of strength; it is then compared against a planet-specific required
minimum to judge whether a planet is "strong" or "weak".

Sources implemented (with what input we actually have available):

    1. Sthana Bala    (positional)   — Uchhabala, Ojayugma, Kendra, Drekkana
    2. Dig Bala       (directional)  — distance from the planet's strong house
    3. Kala Bala      (temporal)     — Paksha Bala (day/night paksha)
    4. Chesta Bala    (motional)     — retrograde boost when available
    5. Naisargika     (natural)      — fixed classical table
    6. Drik Bala      (aspectual)    — benefic aspects +, malefic aspects –

Sources we can only approximate without additional inputs (saptavargaja, abda/
masa/vara/hora, ayanabala) are deliberately skipped and not counted toward the
required minimum — so the resulting "strength %" remains a fair comparison.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple

# Classical exaltation degree (absolute longitude 0-360°).
EXALT_LON = {
    "Sun":      10.0,       # 10° Aries
    "Moon":     33.0,       # 3°  Taurus
    "Mars":     298.0,      # 28° Capricorn
    "Mercury":  165.0,      # 15° Virgo
    "Jupiter":  95.0,       # 5°  Cancer
    "Venus":    357.0,      # 27° Pisces
    "Saturn":   200.0,      # 20° Libra
}

# Dig Bala — direction / house where the planet is at full strength.
DIG_BALA_HOUSE = {
    "Sun": 10, "Mars": 10,
    "Moon": 4, "Venus": 4,
    "Jupiter": 1, "Mercury": 1,
    "Saturn": 7,
}

# Naisargika Bala — fixed natural strength (virupas).
NAISARGIKA = {
    "Sun": 60.0, "Moon": 51.43, "Venus": 42.86, "Jupiter": 34.29,
    "Mercury": 25.71, "Mars": 17.14, "Saturn": 8.57,
}

# Required minimum Shadbala (virupas) to call a planet "strong".
REQUIRED_MIN = {
    "Sun": 390, "Moon": 360, "Mars": 300, "Mercury": 420,
    "Jupiter": 390, "Venus": 330, "Saturn": 300,
}

# Male / Female / Neuter gender grouping used in Drekkana Bala.
DREKKANA_MALE    = {"Sun", "Mars", "Jupiter"}
DREKKANA_NEUTER  = {"Saturn", "Mercury"}
DREKKANA_FEMALE  = {"Moon", "Venus"}

# Ojayugma preferences.
ODD_PREFERRING   = {"Sun", "Mars", "Jupiter"}       # male → odd signs
EVEN_PREFERRING  = {"Moon", "Venus"}                # female → even signs

BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

# Classical Graha Drishti (house aspects, 1-indexed offsets from the planet).
# All planets aspect the 7th. Mars also 4,8; Jupiter 5,9; Saturn 3,10.
SPECIAL_ASPECTS = {
    "Mars":    {4, 7, 8},
    "Jupiter": {5, 7, 9},
    "Saturn":  {3, 7, 10},
}
DEFAULT_ASPECTS = {7}


def _angular_distance(a: float, b: float) -> float:
    """Smallest absolute angular distance between two longitudes (0-180)."""
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


# ─────────────────────────────────────────────────────────────────────────────
# 1. STHANA BALA
# ─────────────────────────────────────────────────────────────────────────────

def _uchhabala(planet: str, lon: float) -> float:
    """
    Exaltation-strength: 60 virupas at exact exaltation point,
    0 at exact debilitation (180° away), linear in between.
    """
    if planet not in EXALT_LON:
        return 0.0
    dist = _angular_distance(lon, EXALT_LON[planet])   # 0..180
    return 60.0 * (180.0 - dist) / 180.0


def _ojayugma(planet: str, sign_idx: int) -> float:
    """15 virupas if placed in a preferred odd/even sign."""
    is_odd = (sign_idx % 2 == 0)       # 0-indexed: 0=Aries (odd), 1=Taurus (even)
    if planet in ODD_PREFERRING  and is_odd:      return 15.0
    if planet in EVEN_PREFERRING and not is_odd:  return 15.0
    return 0.0


def _kendra_bala(house: int) -> float:
    """60 in kendra, 30 in panaphara, 15 in apoklima."""
    if house in {1, 4, 7, 10}:   return 60.0
    if house in {2, 5, 8, 11}:   return 30.0
    return 15.0                   # 3, 6, 9, 12


def _drekkana_bala(planet: str, deg_in_sign: float) -> float:
    """15 virupas if the planet falls in its own-gender drekkana."""
    drek = int(deg_in_sign // 10)   # 0, 1, 2
    if drek == 0 and planet in DREKKANA_MALE:    return 15.0
    if drek == 1 and planet in DREKKANA_NEUTER:  return 15.0
    if drek == 2 and planet in DREKKANA_FEMALE:  return 15.0
    return 0.0


def sthana_bala(planet: str, lon: float, sign_idx: int,
                house: int) -> Tuple[float, Dict[str, float]]:
    deg_in_sign = lon % 30.0
    parts = {
        "uchha":    _uchhabala(planet, lon),
        "oja":      _ojayugma(planet, sign_idx),
        "kendra":   _kendra_bala(house),
        "drekkana": _drekkana_bala(planet, deg_in_sign),
    }
    return sum(parts.values()), parts


# ─────────────────────────────────────────────────────────────────────────────
# 2. DIG BALA
# ─────────────────────────────────────────────────────────────────────────────

def dig_bala(planet: str, house: int) -> float:
    """
    60 virupas when the planet is in its strong house, 0 in the opposite house,
    linear in between (house-distance, not longitude-distance — standard
    Parashari approximation).
    """
    if planet not in DIG_BALA_HOUSE:
        return 0.0
    strong = DIG_BALA_HOUSE[planet]
    # House distance on the zodiac: 0..6 hops.
    diff = abs(house - strong) % 12
    if diff > 6:
        diff = 12 - diff
    return 60.0 * (6 - diff) / 6.0


# ─────────────────────────────────────────────────────────────────────────────
# 3. KALA BALA (Paksha Bala only — the input we reliably have)
# ─────────────────────────────────────────────────────────────────────────────

def paksha_bala(planet: str, moon_sun_angle: Optional[float]) -> float:
    """
    Benefics gain strength in shukla paksha (waxing moon); malefics in krishna.
    Scales linearly with illumination 0..60 virupas.  Malefics' value is simply
    doubled internally per classical rule.

    `moon_sun_angle` = (Moon_lon - Sun_lon) mod 360  (0 = new, 180 = full).
    """
    if moon_sun_angle is None:
        return 0.0
    # Illumination 0..1, peaking at full moon.
    illum = (1 - abs(((moon_sun_angle % 360) - 180) / 180))
    if planet in BENEFICS:
        base = 60.0 * illum              # max at full moon
    elif planet in MALEFICS:
        base = 60.0 * (1 - illum)        # max at new moon
    else:
        return 30.0
    # Moon's paksha bala is doubled classically.
    if planet == "Moon":
        base *= 2
    return min(60.0, base)


# ─────────────────────────────────────────────────────────────────────────────
# 4. CHESTA BALA  (retrograde / motion strength)
# ─────────────────────────────────────────────────────────────────────────────

def chesta_bala(planet: str, is_retrograde: Optional[bool]) -> float:
    """
    Sun and Moon are excluded from Chesta proper (they get Ayanabala / Paksha).
    For others: retrograde → 60, combust/direct stationary → ~30, direct fast → ~15.
    We can only reliably distinguish retrograde when provided.
    """
    if planet in {"Sun", "Moon"} or is_retrograde is None:
        return 30.0      # neutral fallback
    return 60.0 if is_retrograde else 20.0


# ─────────────────────────────────────────────────────────────────────────────
# 5. NAISARGIKA BALA
# ─────────────────────────────────────────────────────────────────────────────

def naisargika_bala(planet: str) -> float:
    return NAISARGIKA.get(planet, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# 6. DRIK BALA
# ─────────────────────────────────────────────────────────────────────────────

def drik_bala(planet: str, house: int,
              planets: List[Dict[str, Any]]) -> float:
    """
    Count benefic aspects (positive) minus malefic aspects (negative) on this
    planet.  Each aspect ± 15 virupas, capped at ±60.
    """
    total = 0.0
    for other in planets:
        other_name = other.get("name")
        other_house = other.get("house")
        if not other_name or other_name == planet or not isinstance(other_house, int):
            continue
        aspects = SPECIAL_ASPECTS.get(other_name, DEFAULT_ASPECTS)
        for offset in aspects:
            aspected_house = ((other_house - 1 + offset - 1) % 12) + 1
            if aspected_house == house:
                total += 15.0 if other_name in BENEFICS else -15.0
                break
    return max(-60.0, min(60.0, total))


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API — total Shadbala per planet
# ─────────────────────────────────────────────────────────────────────────────

def compute_shadbala(planets: List[Dict[str, Any]],
                     lagna_sign: int,
                     moon_sun_angle: Optional[float] = None
                     ) -> Dict[str, Dict[str, Any]]:
    """
    Returns {planet: {total, required, strength_pct, parts: {...}}}.

    Only the seven classical grahas (Sun..Saturn) are evaluated — Rahu/Ketu
    are not subjects of Shadbala in classical Parashari texts.
    """
    out: Dict[str, Dict[str, Any]] = {}

    # Pre-build a {name: dict} index.
    by_name = {p.get("name"): p for p in planets if p.get("name")}

    for planet in REQUIRED_MIN.keys():
        p = by_name.get(planet)
        if not p:
            continue
        lon   = p.get("lon")
        house = p.get("house")
        if not isinstance(lon, (int, float)) or not isinstance(house, int):
            continue

        sign_idx = int(lon / 30) % 12

        sth, sth_parts = sthana_bala(planet, float(lon), sign_idx, house)
        dig = dig_bala(planet, house)
        pak = paksha_bala(planet, moon_sun_angle)
        che = chesta_bala(planet, p.get("retrograde"))
        nai = naisargika_bala(planet)
        dri = drik_bala(planet, house, planets)

        total = sth + dig + pak + che + nai + dri
        required = REQUIRED_MIN[planet]
        strength_pct = round(100.0 * total / required, 1)

        out[planet] = {
            "total":        round(total, 1),
            "required":     required,
            "strength_pct": strength_pct,
            "parts": {
                "sthana":    round(sth, 1),
                "sthana_breakdown": {k: round(v, 1) for k, v in sth_parts.items()},
                "dig":       round(dig, 1),
                "paksha":    round(pak, 1),
                "chesta":    round(che, 1),
                "naisargika":round(nai, 1),
                "drik":      round(dri, 1),
            },
        }
    return out


# ─────────────────────────────────────────────────────────────────────────────
# AV SHODHANA — classical bindu reduction rules
# ─────────────────────────────────────────────────────────────────────────────
# Input: bhinnashtakavarga[planet][sign] (0-indexed 0..11).  Both reductions
# operate on each planet's own AV independently, *before* the rows are summed
# into the Sarvashtakavarga.
# ─────────────────────────────────────────────────────────────────────────────

TRIKONAS = [
    (0, 4, 8),     # Aries, Leo, Sagittarius
    (1, 5, 9),     # Taurus, Virgo, Capricorn
    (2, 6, 10),    # Gemini, Libra, Aquarius
    (3, 7, 11),    # Cancer, Scorpio, Pisces
]

# Signs ruled by each planet (for Ekadhipatya).  Sun and Moon rule only one
# sign each, so they are exempt.
PLANET_RULERSHIP = {
    "Mars":    (0, 7),   # Aries, Scorpio
    "Mercury": (2, 5),   # Gemini, Virgo
    "Jupiter": (8, 11),  # Sagittarius, Pisces
    "Venus":   (1, 6),   # Taurus, Libra
    "Saturn":  (9, 10),  # Capricorn, Aquarius
}


def trikona_shodhana(bav: List[int]) -> List[int]:
    """For each trinal set, subtract the minimum value from all three cells."""
    out = list(bav)
    for tri in TRIKONAS:
        m = min(out[i] for i in tri)
        if m > 0:
            for i in tri:
                out[i] -= m
    return out


def ekadhipatya_shodhana(bav: List[int],
                         planet: str,
                         occupied: set) -> List[int]:
    """
    For the two signs a planet rules:
      - If both are occupied by some planet → no change.
      - If both are empty → keep only the cell with MORE bindus; other = 0.
        (If equal, both become 0.)
      - If one occupied, one empty → empty sign's bindus reduced to
        min(empty, occupied).  If empty ≤ occupied, empty becomes 0.
    """
    pair = PLANET_RULERSHIP.get(planet)
    if not pair:
        return bav
    a, b = pair
    out = list(bav)
    occ_a = a in occupied
    occ_b = b in occupied

    if occ_a and occ_b:
        return out                       # both occupied: untouched

    if (not occ_a) and (not occ_b):
        # Neither occupied — keep the higher cell, zero the lower.
        if out[a] > out[b]:
            out[b] = 0
        elif out[b] > out[a]:
            out[a] = 0
        else:
            out[a] = out[b] = 0
        return out

    # Exactly one occupied.
    empty, occ = (a, b) if not occ_a else (b, a)
    if out[empty] <= out[occ]:
        out[empty] = 0
    else:
        out[empty] -= out[occ]
    return out


def apply_shodhana(bav_by_planet: Dict[str, List[int]],
                   occupied: set) -> Dict[str, List[int]]:
    """Run Trikona then Ekadhipatya Shodhana on every planet's BAV."""
    reduced: Dict[str, List[int]] = {}
    for planet, row in bav_by_planet.items():
        r = trikona_shodhana(row)
        r = ekadhipatya_shodhana(r, planet, occupied)
        reduced[planet] = r
    return reduced

"""
Bala Deep — extended Shadbala sub-calculations beyond what shadbala.py covers.

Implements the missing classical sub-balas (BPHS Ch.27, Saravali Ch.4):

  STHANA BALA (positional) — adds to existing
    1. Saptavargaja Bala — dignity-weighted across 7 vargas
                          (D1, D2, D3, D7, D9, D12, D30)

  KALA BALA (temporal) — extends existing paksha+chesta+naisargika+drik
    2. Nathonnatha Bala  — day/night strength (diurnal vs nocturnal planets)
    3. Tribhaga Bala     — 1/3 of day rulers (Mercury, Sun, Saturn; Jupiter always)
    4. Abda Bala         — Year lord (15 virupas)
    5. Masa Bala         — Month lord (30 virupas)
    6. Vara Bala         — Weekday lord (45 virupas)
    7. Hora Bala         — Hour lord (60 virupas)
    8. Ayana Bala        — solstitial strength (declination-based, simplified)
    9. Yuddha Bala       — planetary war (when 2 planets within 1° in same sign)

  DERIVED FROM SHADBALA
    10. Ishta Phala  — desirable results (sqrt of Uchhabala * Chesta Bala)
    11. Kashta Phala — undesirable results (60 - Ishta)

  VIMSHOPAKA BALA — varga-grouping strengths
    12. Shadvarga    (6 vargas)  — D1, D2, D3, D9, D12, D30
    13. Saptavarga   (7 vargas)  — + D7
    14. Dashavarga   (10 vargas) — + D10, D16, D60
    15. Shodashavarga(16 vargas) — full set

All outputs in *virupas* (60 virupas = 1 rupa) following BPHS conventions.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import math


# ──────────────────────────────────────────────────────────────────────
# Reference tables
# ──────────────────────────────────────────────────────────────────────

# Sign rulers (0=Aries .. 11=Pisces)
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
              "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]

# Exaltation sign index (0-11) for full Saptavargaja dignity
EXALT_SIGN = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
              "Jupiter": 3, "Venus": 11, "Saturn": 6}
DEBIL_SIGN = {"Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
              "Jupiter": 9, "Venus": 5, "Saturn": 0}
OWN_SIGNS = {
    "Sun": [4],
    "Moon": [3],
    "Mars": [0, 7],
    "Mercury": [2, 5],
    "Jupiter": [8, 11],
    "Venus": [1, 6],
    "Saturn": [9, 10],
}

# Naisargika (natural) friendship table (BPHS Ch.3)
NAISARGIKA_FRIENDS = {
    "Sun":     {"friends": ["Moon", "Mars", "Jupiter"], "enemies": ["Venus", "Saturn"], "neutral": ["Mercury"]},
    "Moon":    {"friends": ["Sun", "Mercury"], "enemies": [], "neutral": ["Mars", "Jupiter", "Venus", "Saturn"]},
    "Mars":    {"friends": ["Sun", "Moon", "Jupiter"], "enemies": ["Mercury"], "neutral": ["Venus", "Saturn"]},
    "Mercury": {"friends": ["Sun", "Venus"], "enemies": ["Moon"], "neutral": ["Mars", "Jupiter", "Saturn"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"], "enemies": ["Mercury", "Venus"], "neutral": ["Saturn"]},
    "Venus":   {"friends": ["Mercury", "Saturn"], "enemies": ["Sun", "Moon"], "neutral": ["Mars", "Jupiter"]},
    "Saturn":  {"friends": ["Mercury", "Venus"], "enemies": ["Sun", "Moon", "Mars"], "neutral": ["Jupiter"]},
}

# Diurnal planets (strong by day) — Sun, Jupiter, Venus
# Nocturnal planets (strong by night) — Moon, Mars, Saturn
# Mercury — always
DIURNAL = {"Sun", "Jupiter", "Venus"}
NOCTURNAL = {"Moon", "Mars", "Saturn"}

# Tribhaga Bala — 1st part Mercury, 2nd part Sun, 3rd part Saturn (day);
# at night reverse rules apply. Jupiter always gets 60.
TRIBHAGA_DAY = ["Mercury", "Sun", "Saturn"]
TRIBHAGA_NIGHT = ["Moon", "Venus", "Mars"]

# Vara (weekday) lords — Sun(0)..Saturn(6) by Python weekday
# Python weekday: Mon=0..Sun=6. Vedic vara: Sun=Sunday..Sat=Saturday
WEEKDAY_LORDS = {
    6: "Sun",     # Sunday
    0: "Moon",    # Monday
    1: "Mars",    # Tuesday
    2: "Mercury", # Wednesday
    3: "Jupiter", # Thursday
    4: "Venus",   # Friday
    5: "Saturn",  # Saturday
}

# Hora lords — Chaldean order rotating from day-lord at sunrise
# Day order: Sun, Venus, Mercury, Moon, Saturn, Jupiter, Mars, repeat
CHALDEAN = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]

# Year lords (Abda Bala) — based on Vedic Samvatsara cycle position
# Simplified: lord of the weekday on which Vedic year started
# We approximate using calendar year mod 7

# 7 vargas for Saptavargaja
SAPTAVARGA_NAMES = ["D1", "D2", "D3", "D7", "D9", "D12", "D30"]

# Vimshopaka Bala dignity weights (max virupas in a varga)
# Own=20, Mooltrikona=18, Friend=15, Neutral=10, Enemy=7, Debil=5
DIGNITY_WEIGHT = {
    "exalt": 20.0,
    "mooltrikona": 18.0,
    "own": 20.0,
    "great_friend": 18.0,
    "friend": 15.0,
    "neutral": 10.0,
    "enemy": 7.0,
    "great_enemy": 5.0,
    "debil": 5.0,
}

# Vimshopaka group multipliers (so each group max = 20 virupas total)
VIMSHOPAKA_GROUPS = {
    "shadvarga":     {"vargas": ["D1", "D2", "D3", "D9", "D12", "D30"],
                      "weights": [3.5, 1.0, 1.5, 9.0, 3.0, 2.0]},  # sum = 20
    "saptavarga":    {"vargas": ["D1", "D2", "D3", "D7", "D9", "D12", "D30"],
                      "weights": [5, 2, 3, 2.5, 4.5, 1, 2]},
    "dashavarga":    {"vargas": ["D1", "D2", "D3", "D7", "D9", "D10", "D12", "D16", "D30", "D60"],
                      "weights": [3, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 5]},
    "shodashavarga": {"vargas": ["D1", "D2", "D3", "D7", "D9", "D10", "D12", "D16",
                                 "D20", "D24", "D27", "D30", "D40", "D45", "D60"],
                      # 15 listed (Hora is D2, all others) — total weight 20
                      "weights": [3.5, 1, 1, 0.5, 3, 0.5, 0.5, 2, 0.5, 0.5,
                                  0.5, 1, 0.5, 0.5, 4]},
}


# ──────────────────────────────────────────────────────────────────────
# 1. SAPTAVARGAJA BALA — dignity across 7 vargas
# ──────────────────────────────────────────────────────────────────────

def _dignity_in_sign(planet: str, sign_idx: int) -> str:
    """Return 'exalt', 'own', 'friend', 'neutral', 'enemy', or 'debil'."""
    if planet in EXALT_SIGN and EXALT_SIGN[planet] == sign_idx:
        return "exalt"
    if planet in DEBIL_SIGN and DEBIL_SIGN[planet] == sign_idx:
        return "debil"
    if planet in OWN_SIGNS and sign_idx in OWN_SIGNS[planet]:
        return "own"
    sign_lord = SIGN_LORDS[sign_idx]
    if sign_lord == planet:
        return "own"
    fr = NAISARGIKA_FRIENDS.get(planet, {})
    if sign_lord in fr.get("friends", []):
        return "friend"
    if sign_lord in fr.get("enemies", []):
        return "enemy"
    return "neutral"


def saptavargaja_bala(planet: str, varga_signs: Dict[str, int]) -> float:
    """
    Strength based on dignity in 7 vargas (D1, D2, D3, D7, D9, D12, D30).

    Per BPHS:
      Mooltrikona/Own  → 30 virupas
      Adhimitra (great friend) → 22.5
      Mitra (friend) → 15
      Sama (neutral) → 7.5
      Shatru (enemy) → 3.75
      Adhishatru → 1.875

    Sum across 7 vargas, max ~210 virupas.
    """
    weights = {"exalt": 30, "own": 30, "great_friend": 22.5, "friend": 15.0,
               "neutral": 7.5, "enemy": 3.75, "great_enemy": 1.875, "debil": 1.875}
    total = 0.0
    for vname in SAPTAVARGA_NAMES:
        if vname not in varga_signs:
            continue
        dig = _dignity_in_sign(planet, varga_signs[vname])
        total += weights.get(dig, 7.5)
    return round(total, 2)


# ──────────────────────────────────────────────────────────────────────
# 2-9. KALA BALA sub-components
# ──────────────────────────────────────────────────────────────────────

def nathonnatha_bala(planet: str, is_day_birth: bool) -> float:
    """Day/night strength. Diurnal planets get 60v by day, nocturnal by night."""
    if planet == "Mercury":
        return 60.0
    if is_day_birth and planet in DIURNAL:
        return 60.0
    if not is_day_birth and planet in NOCTURNAL:
        return 60.0
    return 0.0


def tribhaga_bala(planet: str, day_part: int, is_day_birth: bool) -> float:
    """
    Day divided into 3 parts. Part rulers gain 60 virupas.
    Jupiter always gets 60.
    day_part: 1, 2, or 3
    """
    if planet == "Jupiter":
        return 60.0
    table = TRIBHAGA_DAY if is_day_birth else TRIBHAGA_NIGHT
    if 1 <= day_part <= 3 and table[day_part - 1] == planet:
        return 60.0
    return 0.0


def abda_bala(planet: str, year: int) -> float:
    """Year lord gets 15 virupas. Simplified: lord of weekday Jan 1 of birth year."""
    try:
        wd = datetime(year, 1, 1).weekday()
        year_lord = WEEKDAY_LORDS.get(wd, "Sun")
        return 15.0 if planet == year_lord else 0.0
    except Exception:
        return 0.0


def masa_bala(planet: str, year: int, month: int) -> float:
    """Month lord gets 30 virupas. Simplified: lord of weekday of 1st of birth month."""
    try:
        wd = datetime(year, month, 1).weekday()
        month_lord = WEEKDAY_LORDS.get(wd, "Sun")
        return 30.0 if planet == month_lord else 0.0
    except Exception:
        return 0.0


def vara_bala(planet: str, year: int, month: int, day: int) -> float:
    """Weekday lord gets 45 virupas."""
    try:
        wd = datetime(year, month, day).weekday()
        day_lord = WEEKDAY_LORDS.get(wd, "Sun")
        return 45.0 if planet == day_lord else 0.0
    except Exception:
        return 0.0


def hora_bala(planet: str, year: int, month: int, day: int, hour: int) -> float:
    """Hour lord (Chaldean order from day-lord at sunrise) gets 60 virupas."""
    try:
        wd = datetime(year, month, day).weekday()
        day_lord = WEEKDAY_LORDS.get(wd, "Sun")
        start_idx = CHALDEAN.index(day_lord)
        # Hour 0 = day_lord, then rotate Chaldean order
        hour_lord = CHALDEAN[(start_idx + hour) % 7]
        return 60.0 if planet == hour_lord else 0.0
    except Exception:
        return 0.0


def ayana_bala(planet: str, sun_longitude: float) -> float:
    """
    Ayana Bala — solstitial strength based on declination (Kranti).
    BPHS Ch.27. Sun's max declination ±24° at solstices.

    Per-planet preferences (classical):
      Northern declination strong:  Sun, Mars, Jupiter
      Southern declination strong:  Moon, Saturn
      Both strong:                  Mercury, Venus

    Formula: 60 × (1 ± sin(declination)/sin(24°)) / 2  → 0-60v range.
    """
    # Approximate Sun's declination using sayana (tropical) longitude.
    # Ayanamsa ≈ 24° (Lahiri 1990 reference); declination = obliquity*sin(λ)
    sayana_sun = (sun_longitude + 24.0) % 360
    obliquity = 23.45  # earth's axial tilt
    declination = obliquity * math.sin(math.radians(sayana_sun))  # -23.45..+23.45
    norm = declination / 24.0  # -0.977..+0.977

    NORTHERN = {"Sun", "Mars", "Jupiter"}
    SOUTHERN = {"Moon", "Saturn"}
    BOTH = {"Mercury", "Venus"}

    if planet in NORTHERN:
        return round(60.0 * (1.0 + norm) / 2.0, 2)
    if planet in SOUTHERN:
        return round(60.0 * (1.0 - norm) / 2.0, 2)
    if planet in BOTH:
        # always at least mid; absolute deviation boosts further
        return round(30.0 + 30.0 * abs(norm), 2)
    return 0.0


def yuddha_bala(planets: List[Dict[str, Any]],
                shadbala_totals: Dict[str, float]) -> Dict[str, float]:
    """
    Planetary war: when 2 planets within 1° of each other in same sign.
    Winner (higher Shadbala) gains, loser loses by the difference.

    Rahu/Ketu/Sun/Moon excluded from war.
    """
    result = {p.get("name"): 0.0 for p in planets if p.get("name")}
    eligible = [p for p in planets
                if p.get("name") not in {"Sun", "Moon", "Rahu", "Ketu"}
                and p.get("longitude") is not None]

    for i, p1 in enumerate(eligible):
        for p2 in eligible[i + 1:]:
            n1, n2 = p1["name"], p2["name"]
            lon_diff = abs(p1["longitude"] - p2["longitude"])
            lon_diff = min(lon_diff, 360 - lon_diff)
            if lon_diff <= 1.0:
                s1 = shadbala_totals.get(n1, 0.0)
                s2 = shadbala_totals.get(n2, 0.0)
                diff = abs(s1 - s2)
                if s1 > s2:
                    result[n1] = result.get(n1, 0.0) + diff
                    result[n2] = result.get(n2, 0.0) - diff
                else:
                    result[n2] = result.get(n2, 0.0) + diff
                    result[n1] = result.get(n1, 0.0) - diff
    return result


# ──────────────────────────────────────────────────────────────────────
# 10-11. ISHTA + KASHTA PHALA
# ──────────────────────────────────────────────────────────────────────

def ishta_phala(uchhabala: float, chesta_bala: float) -> float:
    """
    Ishta Phala = (Uchhabala × Chesta Bala) / 60  — BPHS Ch.27 sloka 56-57.
    Max 60v when both factors are at full 60.
    """
    return round((max(0.0, uchhabala) * max(0.0, chesta_bala)) / 60.0, 2)


def kashta_phala(uchhabala: float, chesta_bala: float) -> float:
    """Kashta Phala = ((60-Uchhabala) × (60-Chesta Bala)) / 60. Max 60v."""
    return round((max(0.0, 60 - uchhabala) * max(0.0, 60 - chesta_bala)) / 60.0, 2)


# ──────────────────────────────────────────────────────────────────────
# 12-15. VIMSHOPAKA BALA — varga grouping strengths
# ──────────────────────────────────────────────────────────────────────

def vimshopaka_bala(planet: str, varga_signs: Dict[str, int],
                    group: str = "shadvarga") -> float:
    """
    Vimshopaka strength = weighted sum of dignity scores across vargas in group.
    Max ~20 virupas.

    group: 'shadvarga' (6), 'saptavarga' (7), 'dashavarga' (10), 'shodashavarga' (16)
    """
    cfg = VIMSHOPAKA_GROUPS.get(group)
    if not cfg:
        return 0.0
    total = 0.0
    for vname, w in zip(cfg["vargas"], cfg["weights"]):
        if vname not in varga_signs:
            continue
        dig = _dignity_in_sign(planet, varga_signs[vname])
        # normalize dignity to 0-1 scale
        score = DIGNITY_WEIGHT.get(dig, 10.0) / 20.0
        total += w * score
    return round(total, 2)


# ──────────────────────────────────────────────────────────────────────
# Master orchestrator
# ──────────────────────────────────────────────────────────────────────

def compute_bala_deep(planets: List[Dict[str, Any]],
                      varga_charts: Optional[Dict[str, Dict[str, int]]] = None,
                      birth_dt: Optional[datetime] = None,
                      is_day_birth: Optional[bool] = None,
                      day_part: int = 2,
                      shadbala_totals: Optional[Dict[str, float]] = None,
                      uchhabala_by_planet: Optional[Dict[str, float]] = None,
                      chesta_by_planet: Optional[Dict[str, float]] = None,
                      sun_longitude: Optional[float] = None) -> Dict[str, Any]:
    """
    Compute all 9 missing sub-balas + Ishta/Kashta + Vimshopaka.

    varga_charts: {planet_name: {"D1": sign_idx, "D2": ..., "D9": ...}}
    """
    out: Dict[str, Any] = {
        "saptavargaja_bala": {},
        "kala_bala_extended": {},
        "ishta_phala": {},
        "kashta_phala": {},
        "vimshopaka_bala": {},
        "yuddha_bala": {},
    }

    year = birth_dt.year if birth_dt else 2000
    month = birth_dt.month if birth_dt else 1
    day = birth_dt.day if birth_dt else 1
    hour = birth_dt.hour if birth_dt else 12
    is_day = bool(is_day_birth) if is_day_birth is not None else (6 <= hour <= 18)

    # Yuddha Bala (all planets at once)
    if shadbala_totals:
        out["yuddha_bala"] = yuddha_bala(planets, shadbala_totals)

    for p in planets:
        name = p.get("name")
        if not name or name in {"Rahu", "Ketu"}:
            continue

        # Saptavargaja
        if varga_charts and name in varga_charts:
            out["saptavargaja_bala"][name] = saptavargaja_bala(name, varga_charts[name])
            for grp in ["shadvarga", "saptavarga", "dashavarga", "shodashavarga"]:
                out["vimshopaka_bala"].setdefault(name, {})[grp] = \
                    vimshopaka_bala(name, varga_charts[name], grp)

        # Kala Bala extensions
        kb = {
            "nathonnatha": nathonnatha_bala(name, is_day),
            "tribhaga": tribhaga_bala(name, day_part, is_day),
            "abda": abda_bala(name, year),
            "masa": masa_bala(name, year, month),
            "vara": vara_bala(name, year, month, day),
            "hora": hora_bala(name, year, month, day, hour),
            "ayana": ayana_bala(name, sun_longitude or 0.0),
        }
        kb["total_extended"] = round(sum(kb.values()), 2)
        out["kala_bala_extended"][name] = kb

        # Ishta + Kashta
        u = (uchhabala_by_planet or {}).get(name, 30.0)
        c = (chesta_by_planet or {}).get(name, 30.0)
        out["ishta_phala"][name] = ishta_phala(u, c)
        out["kashta_phala"][name] = kashta_phala(u, c)

    return out


def format_bala_deep_summary(bd: Dict[str, Any]) -> str:
    """Format for LOCKED FACTS block."""
    lines = ["▸ EXTENDED BALA (BPHS sub-calculations beyond basic Shadbala):"]

    if bd.get("saptavargaja_bala"):
        top = sorted(bd["saptavargaja_bala"].items(), key=lambda x: -x[1])[:3]
        s = ", ".join(f"{n}={v}v" for n, v in top)
        lines.append(f"   ▸ Saptavargaja Bala (top 3 by varga-dignity): {s}")

    if bd.get("ishta_phala"):
        top_ishta = sorted(bd["ishta_phala"].items(), key=lambda x: -x[1])[:3]
        worst = sorted(bd["kashta_phala"].items(), key=lambda x: -x[1])[:2]
        si = ", ".join(f"{n}={v}v" for n, v in top_ishta)
        sk = ", ".join(f"{n}={v}v" for n, v in worst)
        lines.append(f"   ▸ Ishta Phala (most beneficial): {si}")
        lines.append(f"   ▸ Kashta Phala (most challenging): {sk}")

    if bd.get("vimshopaka_bala"):
        top = sorted(((n, v.get("shodashavarga", 0))
                     for n, v in bd["vimshopaka_bala"].items()),
                     key=lambda x: -x[1])[:3]
        s = ", ".join(f"{n}={v}v" for n, v in top)
        lines.append(f"   ▸ Vimshopaka Bala (Shodashavarga, max 20v): {s}")

    if bd.get("kala_bala_extended"):
        top = sorted(((n, v.get("total_extended", 0))
                     for n, v in bd["kala_bala_extended"].items()),
                     key=lambda x: -x[1])[:3]
        s = ", ".join(f"{n}={v}v" for n, v in top)
        lines.append(f"   ▸ Extended Kala Bala (Nathonnatha+Tribhaga+Abda+Masa+Vara+Hora+Ayana): {s}")

    yb = bd.get("yuddha_bala") or {}
    war_winners = [(n, v) for n, v in yb.items() if v > 0]
    if war_winners:
        s = ", ".join(f"{n} won {round(v,1)}v" for n, v in war_winners)
        lines.append(f"   ▸ Yuddha Bala (Planetary War): {s}")

    return "\n".join(lines)

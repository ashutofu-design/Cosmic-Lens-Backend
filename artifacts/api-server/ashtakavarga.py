"""
ashtakavarga.py
───────────────
Computes Bhinnashtakavarga (BAV — per-planet bindu table) and
Sarvashtakavarga (SAV — sum of all 7 planets' bindus per house).

Source: BPHS Ch. 65–66 (standard Parashari tables).

Each planet "contributes" bindus to certain houses counted from a
reference body (itself, Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn,
Ascendant). The tables below are the classical BPHS contribution tables.

A house with SAV > 30 is considered very strong; 28-30 average; <25 weak.
Total across 12 houses always sums to 337 (cross-check).

Public API
──────────
    compute_ashtakavarga(planets, lagna_sign_idx) -> {
        "bav":   { "Sun": [..12 ints..], ..., "Saturn": [..12 ints..] },
        "sav":   [..12 ints..],          # per house
        "sav_total": 337,
        "verdicts": { house_no(1..12): "VERY STRONG"|"STRONG"|"AVERAGE"|"WEAK" }
    }

Returns {} if input is malformed.
Never raises.
"""
from __future__ import annotations
from typing import Any

# ── BPHS contribution tables ─────────────────────────────────────────────────
# Each entry: planet → reference body → list of house numbers (counted from
# the reference body) where the planet contributes a bindu.
# Source: BPHS, standardised compilation.
_TABLE: dict[str, dict[str, list[int]]] = {
    "Sun": {
        "Sun":     [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon":    [3, 6, 10, 11],
        "Mars":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [5, 6, 9, 11],
        "Venus":   [6, 7, 12],
        "Saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
        "Asc":     [3, 4, 6, 10, 11, 12],
    },
    "Moon": {
        "Sun":     [3, 6, 7, 8, 10, 11],
        "Moon":    [1, 3, 6, 7, 10, 11],
        "Mars":    [2, 3, 5, 6, 9, 10, 11],
        "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter": [1, 4, 7, 8, 10, 11, 12],
        "Venus":   [3, 4, 5, 7, 9, 10, 11],
        "Saturn":  [3, 5, 6, 11],
        "Asc":     [3, 6, 10, 11],
    },
    "Mars": {
        "Sun":     [3, 5, 6, 10, 11],
        "Moon":    [3, 6, 11],
        "Mars":    [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [3, 5, 6, 11],
        "Jupiter": [6, 10, 11, 12],
        "Venus":   [6, 8, 11, 12],
        "Saturn":  [1, 4, 7, 8, 9, 10, 11],
        "Asc":     [1, 3, 6, 10, 11],
    },
    "Mercury": {
        "Sun":     [5, 6, 9, 11, 12],
        "Moon":    [2, 4, 6, 8, 10, 11],
        "Mars":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [6, 8, 11, 12],
        "Venus":   [1, 2, 3, 4, 5, 8, 9, 11],
        "Saturn":  [1, 2, 4, 7, 8, 9, 10, 11],
        "Asc":     [1, 2, 4, 6, 8, 10, 11],
    },
    "Jupiter": {
        "Sun":     [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "Moon":    [2, 5, 7, 9, 11],
        "Mars":    [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
        "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
        "Venus":   [2, 5, 6, 9, 10, 11],
        "Saturn":  [3, 5, 6, 12],
        "Asc":     [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    "Venus": {
        "Sun":     [8, 11, 12],
        "Moon":    [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "Mars":    [3, 5, 6, 9, 11, 12],
        "Mercury": [3, 5, 6, 9, 11],
        "Jupiter": [5, 8, 9, 10, 11],
        "Venus":   [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "Saturn":  [3, 4, 5, 8, 9, 10, 11],
        "Asc":     [1, 2, 3, 4, 5, 8, 9, 11],
    },
    "Saturn": {
        "Sun":     [1, 2, 4, 7, 8, 10, 11],
        "Moon":    [3, 6, 11],
        "Mars":    [3, 5, 6, 10, 11, 12],
        "Mercury": [6, 8, 9, 10, 11, 12],
        "Jupiter": [5, 6, 11, 12],
        "Venus":   [6, 11, 12],
        "Saturn":  [3, 5, 6, 11],
        "Asc":     [1, 3, 4, 6, 10, 11],
    },
}

_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def _house_from_sign(target_sign: int, ref_sign: int) -> int:
    """House number (1..12) of target_sign counted from ref_sign."""
    return ((target_sign - ref_sign) % 12) + 1


def compute_ashtakavarga(planets: list, lagna_sign_idx: int | None) -> dict[str, Any]:
    """
    planets: list of dicts with keys {name, sign} where sign is 0..11 (sign_idx)
             OR a sign name string (will be resolved via _SIGN_NAMES).
    lagna_sign_idx: 0..11 ascendant sign index.

    Returns {} on malformed input.
    """
    if not isinstance(planets, list) or lagna_sign_idx is None:
        return {}

    # Normalise: build {planet_name: sign_idx} including Asc
    SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    sign_of: dict[str, int] = {"Asc": int(lagna_sign_idx) % 12}
    for p in planets:
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        if nm not in _PLANETS:
            continue
        s = p.get("sign_idx")
        if s is None:
            sn = p.get("sign")
            if isinstance(sn, str) and sn in SIGN_NAMES:
                s = SIGN_NAMES.index(sn)
            elif isinstance(sn, int):
                s = sn
        if isinstance(s, int):
            sign_of[nm] = s % 12

    # Need all 7 planets + Asc
    if not all(p in sign_of for p in (*_PLANETS, "Asc")):
        return {}

    # Compute BAV per planet
    bav: dict[str, list[int]] = {p: [0] * 12 for p in _PLANETS}
    for planet in _PLANETS:
        contrib_table = _TABLE[planet]
        for ref_body, good_houses in contrib_table.items():
            ref_sign = sign_of[ref_body]
            for h in good_houses:
                # House h from ref → which sign?
                # Sign that is house h from ref_sign:
                target_sign = (ref_sign + h - 1) % 12
                # House number of that sign from Lagna:
                house_from_lagna = _house_from_sign(target_sign, sign_of["Asc"])
                bav[planet][house_from_lagna - 1] += 1

    # SAV = sum across all 7 planets per house
    sav = [sum(bav[p][h] for p in _PLANETS) for h in range(12)]
    sav_total = sum(sav)

    # Verdicts per house
    verdicts: dict[int, str] = {}
    for i, v in enumerate(sav, 1):
        if v >= 32:   verdicts[i] = "VERY STRONG"
        elif v >= 28: verdicts[i] = "STRONG"
        elif v >= 25: verdicts[i] = "AVERAGE"
        else:         verdicts[i] = "WEAK"

    return {
        "bav":       bav,
        "sav":       sav,
        "sav_total": sav_total,
        "verdicts":  verdicts,
    }


def format_sav_summary(av: dict) -> str:
    """One-line summary block for AI prompt injection."""
    if not av or "sav" not in av:
        return "▸ ASHTAKAVARGA: (unavailable)"
    sav = av["sav"]
    verdicts = av.get("verdicts", {})
    lines = [
        f"▸ SARVASHTAKAVARGA (SAV) per house — total {av.get('sav_total', sum(sav))}/337:",
    ]
    parts = []
    for i in range(1, 13):
        v = sav[i - 1]
        verdict = verdicts.get(i, "")
        parts.append(f"H{i}={v}({verdict[:1]})")
    # Two rows of 6 for readability
    lines.append("   " + "  ".join(parts[:6]))
    lines.append("   " + "  ".join(parts[6:]))
    lines.append("   Legend: V=VeryStrong(32+), S=Strong(28-31), A=Average(25-27), W=Weak(<25)")
    # Highlight notable houses
    very_strong = [i for i in range(1, 13) if verdicts.get(i) == "VERY STRONG"]
    weak        = [i for i in range(1, 13) if verdicts.get(i) == "WEAK"]
    if very_strong:
        lines.append(f"   ▸ VERY STRONG houses: {', '.join(f'H{h}' for h in very_strong)}")
    if weak:
        lines.append(f"   ▸ WEAK houses: {', '.join(f'H{h}' for h in weak)}")
    return "\n".join(lines)

"""
divisional_charts.py
────────────────────
Computes the two highest-value Vargas:

  D9 (Navamsa)  — refines marriage/spouse, dharma, fortune; the 7L's
                  D9 placement is one of THE strongest predictors of
                  marriage quality.
  D10 (Dasamsa) — refines career/profession; the 10L's D10 placement
                  refines what the natal 10H can only sketch.

Vargottama: a planet whose D1 sign == D9 sign — gains exceptional
strength (acts as if exalted in both charts).

Public API
──────────
    compute_d9(planets, lagna_lon=None)  -> {planet: {sign, sign_idx, vargottama}, "lagna_navamsa": "Sign"|None}
    compute_d10(planets, lagna_lon=None) -> {planet: {sign, sign_idx, vargottama}, "lagna_dasamsa": "Sign"|None}
    summarize_divisional(d1_planets, intel) -> dict  # adds AI-friendly verdicts
    format_divisional_summary(d9, d10, intel) -> str

Reference: BPHS Ch. 7 (Vargas) — standard Parashari rules for D9 and D10
seed-sign selection.
"""
from __future__ import annotations
from typing import Any, Optional

_SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
               "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# Sign categories
_MOVABLE = {0, 3, 6, 9}     # Aries, Cancer, Libra, Capricorn
_FIXED   = {1, 4, 7, 10}    # Taurus, Leo, Scorpio, Aquarius
_DUAL    = {2, 5, 8, 11}    # Gemini, Virgo, Sagittarius, Pisces

_LORD_OF = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}


def _sign_idx_from_lon(lon: float) -> int:
    return int(lon / 30.0) % 12


def _navamsa_sign(lon: float) -> int:
    """
    BPHS D9 rule:
        Each sign (30°) divided into 9 navamsas of 3°20' each.
        Movable signs:  navamsa-1 starts from same sign.
        Fixed signs:    navamsa-1 starts from 9th sign from itself.
        Dual signs:     navamsa-1 starts from 5th sign from itself.
        navamsa-N (1..9) → seed_sign + (N-1).
    """
    sign = _sign_idx_from_lon(lon)
    deg_in_sign = lon - sign * 30.0
    n_idx = int(deg_in_sign / (30.0 / 9.0))   # 0..8
    if   sign in _MOVABLE: seed = sign
    elif sign in _FIXED:   seed = (sign + 8) % 12   # 9th from sign
    else:                  seed = (sign + 4) % 12   # 5th from sign
    return (seed + n_idx) % 12


def _dasamsa_sign(lon: float) -> int:
    """
    BPHS D10 rule:
        Each sign divided into 10 parts of 3° each.
        Odd  signs (Aries, Gemini, Leo, ...): part-1 starts from same sign.
        Even signs (Taurus, Cancer, Virgo, ...): part-1 starts from 9th sign.
        part-N (1..10) → seed_sign + (N-1).
    """
    sign = _sign_idx_from_lon(lon)
    deg_in_sign = lon - sign * 30.0
    p_idx = int(deg_in_sign / 3.0)            # 0..9
    if sign % 2 == 0:   # odd-numbered sign in 1-based (Aries=1, idx 0)
        seed = sign
    else:               # even-numbered
        seed = (sign + 8) % 12
    return (seed + p_idx) % 12


def _compute_chart(planets: list, lagna_lon: Optional[float],
                   varga_fn) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for p in planets:
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        lon = p.get("longitude")
        if not nm or not isinstance(lon, (int, float)):
            continue
        d1_sign = _sign_idx_from_lon(float(lon))
        v_sign  = varga_fn(float(lon))
        out[nm] = {
            "sign":       _SIGN_NAMES[v_sign],
            "sign_idx":   v_sign,
            "vargottama": (d1_sign == v_sign),
        }
    if isinstance(lagna_lon, (int, float)):
        out["_lagna"] = {
            "sign":     _SIGN_NAMES[varga_fn(float(lagna_lon))],
            "sign_idx": varga_fn(float(lagna_lon)),
        }
    return out


def compute_d9(planets: list, lagna_lon: Optional[float] = None) -> dict[str, Any]:
    return _compute_chart(planets, lagna_lon, _navamsa_sign)


def compute_d10(planets: list, lagna_lon: Optional[float] = None) -> dict[str, Any]:
    return _compute_chart(planets, lagna_lon, _dasamsa_sign)


# ── AI-friendly summary verdicts ─────────────────────────────────────────────

# Friendship table for "good house" verdict — own/exalt/friend = good,
# debilitation/enemy = bad. Simplified composite check.
_EXALT = {"Sun":0, "Moon":1, "Mars":9, "Mercury":5, "Jupiter":3, "Venus":11, "Saturn":6}
_DEBIL = {"Sun":6, "Moon":7, "Mars":3, "Mercury":11, "Jupiter":9, "Venus":5, "Saturn":0}
_OWN_SIGNS = {
    "Sun":[4], "Moon":[3], "Mars":[0,7], "Mercury":[2,5],
    "Jupiter":[8,11], "Venus":[1,6], "Saturn":[9,10],
}


def _planet_strength_in_varga(planet: str, sign_idx: int) -> str:
    if sign_idx == _EXALT.get(planet, -1): return "EXALTED"
    if sign_idx == _DEBIL.get(planet, -1): return "DEBILITATED"
    if sign_idx in _OWN_SIGNS.get(planet, []): return "OWN-SIGN"
    return "NEUTRAL"


def summarize_d9_for_marriage(d9: dict, intel: dict) -> dict[str, Any]:
    """
    Returns marriage-relevant D9 highlights:
      - 7L_d9: where natal 7L falls in D9 + its strength there
      - venus_d9: Venus position + strength in D9 (universal karaka)
      - vargottamas: list of planets that are vargottama (strong)
    """
    out: dict[str, Any] = {}
    house_lords = intel.get("house_lords") or []
    seventh_lord = next((h.get("lord") for h in house_lords if h.get("house") == 7), None)
    if seventh_lord and seventh_lord in d9:
        out["7L"] = seventh_lord
        out["7L_d9_sign"] = d9[seventh_lord]["sign"]
        out["7L_d9_strength"] = _planet_strength_in_varga(seventh_lord, d9[seventh_lord]["sign_idx"])
    if "Venus" in d9:
        out["venus_d9_sign"] = d9["Venus"]["sign"]
        out["venus_d9_strength"] = _planet_strength_in_varga("Venus", d9["Venus"]["sign_idx"])
    out["vargottama"] = [p for p, info in d9.items()
                         if isinstance(info, dict) and info.get("vargottama") and not p.startswith("_")]
    return out


def summarize_d10_for_career(d10: dict, intel: dict) -> dict[str, Any]:
    out: dict[str, Any] = {}
    house_lords = intel.get("house_lords") or []
    tenth_lord = next((h.get("lord") for h in house_lords if h.get("house") == 10), None)
    if tenth_lord and tenth_lord in d10:
        out["10L"] = tenth_lord
        out["10L_d10_sign"] = d10[tenth_lord]["sign"]
        out["10L_d10_strength"] = _planet_strength_in_varga(tenth_lord, d10[tenth_lord]["sign_idx"])
    if "Sun" in d10:
        out["sun_d10_sign"] = d10["Sun"]["sign"]
        out["sun_d10_strength"] = _planet_strength_in_varga("Sun", d10["Sun"]["sign_idx"])
    if "Saturn" in d10:
        out["saturn_d10_sign"] = d10["Saturn"]["sign"]
        out["saturn_d10_strength"] = _planet_strength_in_varga("Saturn", d10["Saturn"]["sign_idx"])
    out["vargottama"] = [p for p, info in d10.items()
                         if isinstance(info, dict) and info.get("vargottama") and not p.startswith("_")]
    return out


def format_divisional_summary(d9: dict, d10: dict, intel: dict) -> str:
    if not d9 and not d10:
        return "▸ DIVISIONAL CHARTS: (unavailable — need planet longitudes)"
    lines: list[str] = []
    if d9:
        m = summarize_d9_for_marriage(d9, intel)
        lines.append("▸ D9 NAVAMSA (marriage refinement):")
        if "7L" in m:
            lines.append(
                f"   ▸ 7L ({m['7L']}) lands in {m['7L_d9_sign']} in D9 "
                f"— {m['7L_d9_strength']} (strongest signal for marriage quality)"
            )
        else:
            lines.append("   ▸ 7L D9 placement: UNAVAILABLE (do NOT invent — fall back to natal 7L)")
        if "venus_d9_sign" in m:
            lines.append(
                f"   ▸ Venus in D9: {m['venus_d9_sign']} — {m['venus_d9_strength']} "
                "(universal marriage karaka)"
            )
        if m.get("vargottama"):
            lines.append(f"   ▸ Vargottama planets (D1=D9, exceptional strength): "
                         f"{', '.join(m['vargottama'])}")
    if d10:
        c = summarize_d10_for_career(d10, intel)
        lines.append("▸ D10 DASAMSA (career refinement):")
        if "10L" in c:
            lines.append(
                f"   ▸ 10L ({c['10L']}) lands in {c['10L_d10_sign']} in D10 "
                f"— {c['10L_d10_strength']} (strongest signal for career direction)"
            )
        else:
            lines.append("   ▸ 10L D10 placement: UNAVAILABLE (do NOT invent — fall back to natal 10L)")
        if "sun_d10_sign" in c:
            lines.append(
                f"   ▸ Sun in D10: {c['sun_d10_sign']} — {c['sun_d10_strength']} "
                "(authority/recognition karaka)"
            )
        if "saturn_d10_sign" in c:
            lines.append(
                f"   ▸ Saturn in D10: {c['saturn_d10_sign']} — {c['saturn_d10_strength']} "
                "(work-discipline karaka)"
            )
        if c.get("vargottama"):
            lines.append(f"   ▸ Vargottama planets (D1=D10, exceptional career strength): "
                         f"{', '.join(c['vargottama'])}")
    return "\n".join(lines)

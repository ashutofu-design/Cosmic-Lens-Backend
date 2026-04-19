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


# ── Sprint 9 — D2, D3, D7, D12 vargas ───────────────────────────────────────

def _hora_sign(lon: float) -> int:
    """
    BPHS D2 Hora rule:
        Each sign split into 2 halves of 15° each.
        ODD signs (Aries/Gem/Leo/Lib/Sag/Aqu):
            0-15°  → Sun's Hora  (Leo,    idx 4)
            15-30° → Moon's Hora (Cancer, idx 3)
        EVEN signs (Tau/Can/Vir/Sco/Cap/Pis):
            0-15°  → Moon's Hora (Cancer, idx 3)
            15-30° → Sun's Hora  (Leo,    idx 4)
        Used for WEALTH analysis (Sun-Hora = active income, Moon-Hora =
        passive/inherited wealth/comforts).
    """
    sign = _sign_idx_from_lon(lon)
    deg_in_sign = lon - sign * 30.0
    half = 0 if deg_in_sign < 15.0 else 1
    is_odd_sign = (sign % 2 == 0)   # idx 0,2,4... = Aries, Gemini... = ODD
    if is_odd_sign:
        return 4 if half == 0 else 3   # Leo, Cancer
    else:
        return 3 if half == 0 else 4   # Cancer, Leo


def _drekkana_sign(lon: float) -> int:
    """
    BPHS D3 Drekkana rule:
        Each sign divided into 3 parts of 10° each.
        Part-1 (0-10°)  → same sign
        Part-2 (10-20°) → 5th from sign
        Part-3 (20-30°) → 9th from sign
        Used for SIBLINGS (3rd house lord) and BROAD TEMPERAMENT.
    """
    sign = _sign_idx_from_lon(lon)
    deg_in_sign = lon - sign * 30.0
    p_idx = int(deg_in_sign / 10.0)   # 0,1,2
    if   p_idx == 0: return sign
    elif p_idx == 1: return (sign + 4)  % 12   # 5th-from
    else:            return (sign + 8)  % 12   # 9th-from


def _saptamsa_sign(lon: float) -> int:
    """
    BPHS D7 Saptamsa rule:
        Each sign divided into 7 parts of (30/7)° = 4.2857° each.
        ODD signs:  part-1 starts from same sign.
        EVEN signs: part-1 starts from 7th from sign.
        Used for CHILDREN analysis (5th house, putra-karaka Jupiter).
    """
    sign = _sign_idx_from_lon(lon)
    deg_in_sign = lon - sign * 30.0
    p_idx = int(deg_in_sign / (30.0 / 7.0))   # 0..6
    if sign % 2 == 0:   # odd 1-based (Aries, Gemini, ...)
        seed = sign
    else:
        seed = (sign + 6) % 12   # 7th from sign
    return (seed + p_idx) % 12


def _dwadasamsa_sign(lon: float) -> int:
    """
    BPHS D12 Dwadasamsa rule:
        Each sign divided into 12 parts of 2°30' each.
        Part-1 starts from same sign (regardless of odd/even).
        Used for PARENTS analysis (9H = father, 4H = mother).
    """
    sign = _sign_idx_from_lon(lon)
    deg_in_sign = lon - sign * 30.0
    p_idx = int(deg_in_sign / 2.5)   # 0..11
    return (sign + p_idx) % 12


def compute_d2(planets, lagna_lon=None):
    return _compute_chart(planets, lagna_lon, _hora_sign)


def compute_d3(planets, lagna_lon=None):
    return _compute_chart(planets, lagna_lon, _drekkana_sign)


def compute_d7(planets, lagna_lon=None):
    return _compute_chart(planets, lagna_lon, _saptamsa_sign)


def compute_d12(planets, lagna_lon=None):
    return _compute_chart(planets, lagna_lon, _dwadasamsa_sign)


# ── Topic-specific summarizers (Sprint 9) ────────────────────────────────────

def summarize_d2_for_wealth(d2: dict) -> dict[str, Any]:
    """
    Counts how many natal-wealth-relevant planets land in Sun's Hora (Leo)
    vs Moon's Hora (Cancer). Money-significators: Jupiter, Venus, Mercury,
    Moon (and 2L/11L if known).
    """
    wealth_planets = ("Jupiter", "Venus", "Mercury", "Moon", "Sun")
    sun_hora, moon_hora = [], []
    for p in wealth_planets:
        info = d2.get(p)
        if not isinstance(info, dict):
            continue
        if info.get("sign") == "Leo":
            sun_hora.append(p)
        elif info.get("sign") == "Cancer":
            moon_hora.append(p)
    return {
        "sun_hora_planets":  sun_hora,
        "moon_hora_planets": moon_hora,
        "verdict": (
            "ACTIVE-EARNER (more in Sun-Hora)"   if len(sun_hora) > len(moon_hora) else
            "PASSIVE-WEALTH (more in Moon-Hora)" if len(moon_hora) > len(sun_hora) else
            "BALANCED (equal active+passive)"
        ),
    }


def summarize_d3_for_siblings(d3: dict, intel: dict) -> dict[str, Any]:
    """
    3L's D3 placement + Mars D3 (karaka of younger siblings) + Jupiter D3
    (elder siblings).
    """
    out: dict[str, Any] = {}
    house_lords = intel.get("house_lords") or []
    third_lord = next((h.get("lord") for h in house_lords if h.get("house") == 3), None)
    if third_lord and third_lord in d3:
        out["3L"] = third_lord
        out["3L_d3_sign"] = d3[third_lord]["sign"]
        out["3L_d3_strength"] = _planet_strength_in_varga(third_lord, d3[third_lord]["sign_idx"])
    for k, p in (("mars", "Mars"), ("jupiter", "Jupiter")):
        if p in d3:
            out[f"{k}_d3_sign"] = d3[p]["sign"]
            out[f"{k}_d3_strength"] = _planet_strength_in_varga(p, d3[p]["sign_idx"])
    return out


def summarize_d7_for_children(d7: dict, intel: dict) -> dict[str, Any]:
    """
    5L's D7 placement + Jupiter D7 (putra-karaka).
    """
    out: dict[str, Any] = {}
    house_lords = intel.get("house_lords") or []
    fifth_lord = next((h.get("lord") for h in house_lords if h.get("house") == 5), None)
    if fifth_lord and fifth_lord in d7:
        out["5L"] = fifth_lord
        out["5L_d7_sign"] = d7[fifth_lord]["sign"]
        out["5L_d7_strength"] = _planet_strength_in_varga(fifth_lord, d7[fifth_lord]["sign_idx"])
    if "Jupiter" in d7:
        out["jupiter_d7_sign"] = d7["Jupiter"]["sign"]
        out["jupiter_d7_strength"] = _planet_strength_in_varga("Jupiter", d7["Jupiter"]["sign_idx"])
    out["vargottama"] = [p for p, info in d7.items()
                         if isinstance(info, dict) and info.get("vargottama") and not p.startswith("_")]
    return out


def summarize_d12_for_parents(d12: dict, intel: dict) -> dict[str, Any]:
    """
    9L's D12 (father) + 4L's D12 (mother) + Sun (pitru-karaka) + Moon
    (matru-karaka).
    """
    out: dict[str, Any] = {}
    house_lords = intel.get("house_lords") or []
    ninth_lord  = next((h.get("lord") for h in house_lords if h.get("house") == 9), None)
    fourth_lord = next((h.get("lord") for h in house_lords if h.get("house") == 4), None)
    if ninth_lord and ninth_lord in d12:
        out["9L"] = ninth_lord
        out["9L_d12_sign"] = d12[ninth_lord]["sign"]
        out["9L_d12_strength"] = _planet_strength_in_varga(ninth_lord, d12[ninth_lord]["sign_idx"])
    if fourth_lord and fourth_lord in d12:
        out["4L"] = fourth_lord
        out["4L_d12_sign"] = d12[fourth_lord]["sign"]
        out["4L_d12_strength"] = _planet_strength_in_varga(fourth_lord, d12[fourth_lord]["sign_idx"])
    for k, p in (("sun", "Sun"), ("moon", "Moon")):
        if p in d12:
            out[f"{k}_d12_sign"] = d12[p]["sign"]
            out[f"{k}_d12_strength"] = _planet_strength_in_varga(p, d12[p]["sign_idx"])
    return out


def format_extra_vargas_summary(d2, d3, d7, d12, intel: dict) -> str:
    if not any([d2, d3, d7, d12]):
        return ""
    lines: list[str] = []
    if d2:
        w = summarize_d2_for_wealth(d2)
        lines.append("▸ D2 HORA (wealth refinement):")
        lines.append(
            f"   ▸ Sun-Hora (active earnings): {w['sun_hora_planets'] or '(none of the wealth-significators)'}; "
            f"Moon-Hora (passive/inherited): {w['moon_hora_planets'] or '(none)'}"
        )
        lines.append(f"   ▸ Verdict: {w['verdict']}")
    if d3:
        s = summarize_d3_for_siblings(d3, intel)
        lines.append("▸ D3 DREKKANA (siblings/temperament):")
        if "3L" in s:
            lines.append(
                f"   ▸ 3L ({s['3L']}) lands in {s['3L_d3_sign']} in D3 — {s['3L_d3_strength']}"
            )
        if "mars_d3_sign" in s:
            lines.append(f"   ▸ Mars in D3: {s['mars_d3_sign']} — {s['mars_d3_strength']} (younger-sibling karaka)")
        if "jupiter_d3_sign" in s:
            lines.append(f"   ▸ Jupiter in D3: {s['jupiter_d3_sign']} — {s['jupiter_d3_strength']} (elder-sibling karaka)")
    if d7:
        c = summarize_d7_for_children(d7, intel)
        lines.append("▸ D7 SAPTAMSA (children refinement):")
        if "5L" in c:
            lines.append(
                f"   ▸ 5L ({c['5L']}) lands in {c['5L_d7_sign']} in D7 — {c['5L_d7_strength']} "
                "(strongest signal for progeny)"
            )
        if "jupiter_d7_sign" in c:
            lines.append(
                f"   ▸ Jupiter in D7: {c['jupiter_d7_sign']} — {c['jupiter_d7_strength']} "
                "(putra-karaka — universal child indicator)"
            )
        if c.get("vargottama"):
            lines.append(f"   ▸ Vargottama (D1=D7) in this chart: {', '.join(c['vargottama'])}")
    if d12:
        p = summarize_d12_for_parents(d12, intel)
        lines.append("▸ D12 DWADASAMSA (parents refinement):")
        if "9L" in p:
            lines.append(
                f"   ▸ 9L ({p['9L']}) lands in {p['9L_d12_sign']} in D12 — {p['9L_d12_strength']} (father)"
            )
        if "4L" in p:
            lines.append(
                f"   ▸ 4L ({p['4L']}) lands in {p['4L_d12_sign']} in D12 — {p['4L_d12_strength']} (mother)"
            )
        if "sun_d12_sign" in p:
            lines.append(f"   ▸ Sun in D12: {p['sun_d12_sign']} — {p['sun_d12_strength']} (pitru-karaka)")
        if "moon_d12_sign" in p:
            lines.append(f"   ▸ Moon in D12: {p['moon_d12_sign']} — {p['moon_d12_strength']} (matru-karaka)")
    return "\n".join(lines)


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


# ═══════════════════════════════════════════════════════════════════════════
# SPRINT-10 — D16 Shodasamsa, D20 Vimsamsa, D24 Chaturvimsamsa, D27 Bhamsa
# ═══════════════════════════════════════════════════════════════════════════
#
#   D16  → vehicles, conveyances, comforts, luxury (4L, Venus)
#   D20  → spirituality, sadhana, mantra-siddhi, devotion (9L, Jupiter, Ketu)
#   D24  → higher education, learning, knowledge, degrees (4L, 5L, Mercury, Jupiter)
#   D27  → physical strength/weakness, stamina, sports, vitality (lagna lord, Mars, Sun)
#
# Reference: BPHS Ch. 7 (Vargas) — Parashari sign-mapping rules.

# Element groupings used by D27
_FIRE  = {0, 4, 8}    # Aries, Leo, Sagittarius
_EARTH = {1, 5, 9}    # Taurus, Virgo, Capricorn
_AIR   = {2, 6, 10}   # Gemini, Libra, Aquarius
_WATER = {3, 7, 11}   # Cancer, Scorpio, Pisces


def _shodasamsa_sign(lon: float) -> int:
    """D16: 16 parts of 1°52'30" each. Movable→Aries, Fixed→Leo, Dual→Sagittarius (sequential)."""
    sign = _sign_idx_from_lon(lon)
    deg_in_sign = lon - sign * 30.0
    n_idx = int(deg_in_sign / (30.0 / 16.0))   # 0..15
    if   sign in _MOVABLE: seed = 0   # Aries
    elif sign in _FIXED:   seed = 4   # Leo
    else:                  seed = 8   # Sagittarius
    return (seed + n_idx) % 12


def _vimsamsa_sign(lon: float) -> int:
    """D20: 20 parts of 1°30'. Movable→Aries, Fixed→Sagittarius, Dual→Leo (sequential)."""
    sign = _sign_idx_from_lon(lon)
    deg_in_sign = lon - sign * 30.0
    n_idx = int(deg_in_sign / (30.0 / 20.0))   # 0..19
    if   sign in _MOVABLE: seed = 0   # Aries
    elif sign in _FIXED:   seed = 8   # Sagittarius
    else:                  seed = 4   # Leo
    return (seed + n_idx) % 12


def _chaturvimsamsa_sign(lon: float) -> int:
    """D24: 24 parts of 1°15'. Odd→Leo, Even→Cancer (sequential)."""
    sign = _sign_idx_from_lon(lon)
    deg_in_sign = lon - sign * 30.0
    n_idx = int(deg_in_sign / (30.0 / 24.0))   # 0..23
    seed = 4 if (sign % 2 == 0) else 3          # 0-indexed: even idx==odd sign #
    # Standard convention uses 1-based sign numbers; sign idx 0 = Aries (sign #1, ODD).
    # ODD signs (1,3,5,...) → Leo (idx 4); EVEN signs (2,4,...) → Cancer (idx 3).
    seed = 4 if (sign % 2 == 0) else 3
    return (seed + n_idx) % 12


def _bhamsa_sign(lon: float) -> int:
    """D27 (Saptavimshamsa / Nakshatramsa): 27 parts of 1°6'40".
       Fire-signs   → Aries seed,
       Earth-signs  → Cancer seed,
       Air-signs    → Libra seed,
       Water-signs  → Capricorn seed (sequential)."""
    sign = _sign_idx_from_lon(lon)
    deg_in_sign = lon - sign * 30.0
    n_idx = int(deg_in_sign / (30.0 / 27.0))   # 0..26
    if   sign in _FIRE:  seed = 0
    elif sign in _EARTH: seed = 3
    elif sign in _AIR:   seed = 6
    else:                seed = 9
    return (seed + n_idx) % 12


def _build_varga(planets, lagna_lon, mapper, varga_label):
    """Generic builder used by D16/D20/D24/D27. Returns dict planet→{sign,sign_idx,vargottama}."""
    out: dict[str, Any] = {}
    if not planets:
        return out
    for p in planets:
        name = (p.get("name") or "").strip()
        lon  = p.get("longitude") or p.get("lon")
        if not name or lon is None:
            continue
        d_idx = mapper(float(lon))
        d1_idx = _sign_idx_from_lon(float(lon))
        out[name] = {
            "sign": _SIGN_NAMES[d_idx],
            "sign_idx": d_idx,
            "vargottama": (d_idx == d1_idx),
        }
    if lagna_lon is not None:
        try:
            out[f"lagna_{varga_label}"] = _SIGN_NAMES[mapper(float(lagna_lon))]
        except Exception:
            pass
    return out


def compute_d16(planets, lagna_lon=None):
    return _build_varga(planets, lagna_lon, _shodasamsa_sign, "shodasamsa")


def compute_d20(planets, lagna_lon=None):
    return _build_varga(planets, lagna_lon, _vimsamsa_sign, "vimsamsa")


def compute_d24(planets, lagna_lon=None):
    return _build_varga(planets, lagna_lon, _chaturvimsamsa_sign, "chaturvimsamsa")


def compute_d27(planets, lagna_lon=None):
    return _build_varga(planets, lagna_lon, _bhamsa_sign, "bhamsa")


def _planet_d_strength(planet_name: str, d_sign_idx: int) -> str:
    """Reuses the same exalt/debil/own-sign tagging used by other vargas."""
    EXALT = {"Sun":0,"Moon":1,"Mars":9,"Mercury":5,"Jupiter":3,"Venus":11,"Saturn":6}
    DEBIL = {"Sun":6,"Moon":7,"Mars":3,"Mercury":11,"Jupiter":9,"Venus":5,"Saturn":0}
    OWN   = {"Sun":[4],"Moon":[3],"Mars":[0,7],"Mercury":[2,5],
             "Jupiter":[8,11],"Venus":[1,6],"Saturn":[9,10]}
    if EXALT.get(planet_name) == d_sign_idx: return "EXALTED"
    if DEBIL.get(planet_name) == d_sign_idx: return "DEBILITATED"
    if d_sign_idx in OWN.get(planet_name, []): return "OWN-SIGN"
    return "NEUTRAL"


def _lord_of_house(intel, house_num):
    """Returns the lord-planet name for a given natal house.
    Supports two intel shapes:
      - intel['house_lords'] = [{'house':1,'sign':...,'lord':'Jupiter',...}, ...]   (chart_intelligence shape)
      - intel['house_signs'] = {1:'Aries', ...}                                     (alternate shape)
    Falls back to lagna_sign if needed.
    """
    if not intel:
        return None
    try:
        # Preferred — chart_intelligence's house_lords list-of-dicts
        hl = intel.get("house_lords")
        if isinstance(hl, list):
            for row in hl:
                if isinstance(row, dict) and int(row.get("house") or 0) == int(house_num):
                    lord = (row.get("lord") or "").strip()
                    if lord:
                        return lord
        # Alternate — house_signs map
        hs = intel.get("house_signs") or {}
        sign_name = hs.get(str(house_num)) or hs.get(house_num)
        if sign_name and sign_name in _SIGN_NAMES:
            return _LORD_OF.get(_SIGN_NAMES.index(sign_name))
        # Fallback — derive from lagna_sign
        lagna = intel.get("lagna_sign")
        if lagna and lagna in _SIGN_NAMES:
            lagna_idx = _SIGN_NAMES.index(lagna)
            target_sign = (lagna_idx + int(house_num) - 1) % 12
            return _LORD_OF.get(target_sign)
    except Exception:
        pass
    return None


def summarize_d16_for_vehicles(d16, intel):
    """4L D16 + Venus D16 → vehicles/comforts verdict."""
    out = {}
    if not d16: return out
    fourth_lord = _lord_of_house(intel, 4)
    if fourth_lord and fourth_lord in d16:
        info = d16[fourth_lord]
        out["4L"] = fourth_lord
        out["4L_d16_sign"]     = info["sign"]
        out["4L_d16_strength"] = _planet_d_strength(fourth_lord, info["sign_idx"])
    if "Venus" in d16:
        v = d16["Venus"]
        out["venus_d16_sign"]     = v["sign"]
        out["venus_d16_strength"] = _planet_d_strength("Venus", v["sign_idx"])
    return out


def summarize_d20_for_spirituality(d20, intel):
    """9L D20 + Jupiter D20 + Ketu D20 → sadhana / spiritual progress."""
    out = {}
    if not d20: return out
    ninth_lord = _lord_of_house(intel, 9)
    if ninth_lord and ninth_lord in d20:
        info = d20[ninth_lord]
        out["9L"] = ninth_lord
        out["9L_d20_sign"]     = info["sign"]
        out["9L_d20_strength"] = _planet_d_strength(ninth_lord, info["sign_idx"])
    for kk in ("Jupiter", "Ketu"):
        if kk in d20:
            out[f"{kk.lower()}_d20_sign"]     = d20[kk]["sign"]
            out[f"{kk.lower()}_d20_strength"] = _planet_d_strength(kk, d20[kk]["sign_idx"])
    return out


def summarize_d24_for_education(d24, intel):
    """4L + 5L D24 + Mercury + Jupiter D24 → higher learning / degrees."""
    out = {}
    if not d24: return out
    for hn, label in ((4, "4L"), (5, "5L")):
        lord = _lord_of_house(intel, hn)
        if lord and lord in d24:
            out[label] = lord
            out[f"{label}_d24_sign"]     = d24[lord]["sign"]
            out[f"{label}_d24_strength"] = _planet_d_strength(lord, d24[lord]["sign_idx"])
    for kk in ("Mercury", "Jupiter"):
        if kk in d24:
            out[f"{kk.lower()}_d24_sign"]     = d24[kk]["sign"]
            out[f"{kk.lower()}_d24_strength"] = _planet_d_strength(kk, d24[kk]["sign_idx"])
    return out


def summarize_d27_for_strength(d27, intel):
    """Lagna lord D27 + Mars + Sun D27 → physical stamina / vitality."""
    out = {}
    if not d27: return out
    lagna_lord = _lord_of_house(intel, 1)
    if lagna_lord and lagna_lord in d27:
        info = d27[lagna_lord]
        out["lagna_lord"] = lagna_lord
        out["lagna_lord_d27_sign"]     = info["sign"]
        out["lagna_lord_d27_strength"] = _planet_d_strength(lagna_lord, info["sign_idx"])
    for kk in ("Mars", "Sun"):
        if kk in d27:
            out[f"{kk.lower()}_d27_sign"]     = d27[kk]["sign"]
            out[f"{kk.lower()}_d27_strength"] = _planet_d_strength(kk, d27[kk]["sign_idx"])
    return out


def format_advanced_vargas_summary(d16, d20, d24, d27, intel):
    """Compact LOCKED FACTS block for D16/D20/D24/D27."""
    lines = []
    if d16:
        s = summarize_d16_for_vehicles(d16, intel)
        if s.get("4L_d16_sign") or s.get("venus_d16_sign"):
            lines.append("▸ D16 SHODASAMSA (vehicles/comforts):")
            if s.get("4L_d16_sign"):
                lines.append(f"   ▸ 4L ({s['4L']}) lands in {s['4L_d16_sign']} in D16 — {s['4L_d16_strength']}")
            if s.get("venus_d16_sign"):
                lines.append(f"   ▸ Venus in D16: {s['venus_d16_sign']} — {s['venus_d16_strength']} (luxury-karaka)")
    if d20:
        s = summarize_d20_for_spirituality(d20, intel)
        if s.get("9L_d20_sign") or s.get("jupiter_d20_sign") or s.get("ketu_d20_sign"):
            lines.append("▸ D20 VIMSAMSA (spirituality/sadhana):")
            if s.get("9L_d20_sign"):
                lines.append(f"   ▸ 9L ({s['9L']}) lands in {s['9L_d20_sign']} in D20 — {s['9L_d20_strength']}")
            if s.get("jupiter_d20_sign"):
                lines.append(f"   ▸ Jupiter in D20: {s['jupiter_d20_sign']} — {s['jupiter_d20_strength']} (guru-karaka)")
            if s.get("ketu_d20_sign"):
                lines.append(f"   ▸ Ketu in D20: {s['ketu_d20_sign']} — {s['ketu_d20_strength']} (moksha-karaka)")
    if d24:
        s = summarize_d24_for_education(d24, intel)
        if any(s.get(k) for k in ("4L_d24_sign","5L_d24_sign","mercury_d24_sign","jupiter_d24_sign")):
            lines.append("▸ D24 CHATURVIMSAMSA (higher education/learning):")
            if s.get("4L_d24_sign"):
                lines.append(f"   ▸ 4L ({s['4L']}) lands in {s['4L_d24_sign']} in D24 — {s['4L_d24_strength']}")
            if s.get("5L_d24_sign"):
                lines.append(f"   ▸ 5L ({s['5L']}) lands in {s['5L_d24_sign']} in D24 — {s['5L_d24_strength']}")
            if s.get("mercury_d24_sign"):
                lines.append(f"   ▸ Mercury in D24: {s['mercury_d24_sign']} — {s['mercury_d24_strength']} (vidya-karaka)")
            if s.get("jupiter_d24_sign"):
                lines.append(f"   ▸ Jupiter in D24: {s['jupiter_d24_sign']} — {s['jupiter_d24_strength']} (gnan-karaka)")
    if d27:
        s = summarize_d27_for_strength(d27, intel)
        if s.get("lagna_lord_d27_sign") or s.get("mars_d27_sign") or s.get("sun_d27_sign"):
            lines.append("▸ D27 BHAMSA (physical strength/stamina/vitality):")
            if s.get("lagna_lord_d27_sign"):
                lines.append(f"   ▸ Lagna-lord ({s['lagna_lord']}) lands in {s['lagna_lord_d27_sign']} in D27 — {s['lagna_lord_d27_strength']}")
            if s.get("mars_d27_sign"):
                lines.append(f"   ▸ Mars in D27: {s['mars_d27_sign']} — {s['mars_d27_strength']} (energy-karaka)")
            if s.get("sun_d27_sign"):
                lines.append(f"   ▸ Sun in D27: {s['sun_d27_sign']} — {s['sun_d27_strength']} (vitality-karaka)")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# SPRINT-11 — D30 Trimsamsa, D40 Khavedamsa, D45 Akshavedamsa, D60 Shashtyamsa
# ═══════════════════════════════════════════════════════════════════════════
#
#   D30  → misfortune, accidents, moral tendencies (malefic concentration)
#   D40  → maternal legacy / matrilineal karma (4L, Moon)
#   D45  → paternal legacy / patrilineal karma (9L, Sun)
#   D60  → past-life karma, deepest signal (lagna lord, AK / atma karaka)
#
# D60 is rated by Parashara as the MOST important varga — finest resolution
# (0°30' per part). Past-life impressions surface here.
#
# Reference: BPHS Ch. 7 (Vargas) — classical sign-mapping rules.

def _trimsamsa_sign(lon: float) -> int:
    """D30: malefic-only varga.
       ODD signs (Aries idx 0, Gem idx 2, ...): 0-5°→Mars (Aries 0), 5-10°→Saturn (Aquarius 10),
                                                10-18°→Jupiter (Sag 8), 18-25°→Mercury (Gem 2),
                                                25-30°→Venus (Libra 6).
       EVEN signs (Tau idx 1, ...): 0-5°→Venus (Tau 1), 5-12°→Mercury (Vir 5),
                                    12-20°→Jupiter (Pisces 11), 20-25°→Saturn (Cap 9),
                                    25-30°→Mars (Scorpio 7)."""
    sign = _sign_idx_from_lon(lon)
    deg  = lon - sign * 30.0
    is_odd = (sign % 2 == 0)   # 0-indexed: Aries(0)=odd-sign-#1
    if is_odd:
        if deg < 5:    return 0    # Mars→Aries
        if deg < 10:   return 10   # Saturn→Aquarius
        if deg < 18:   return 8    # Jupiter→Sagittarius
        if deg < 25:   return 2    # Mercury→Gemini
        return 6                   # Venus→Libra
    else:
        if deg < 5:    return 1    # Venus→Taurus
        if deg < 12:   return 5    # Mercury→Virgo
        if deg < 20:   return 11   # Jupiter→Pisces
        if deg < 25:   return 9    # Saturn→Capricorn
        return 7                   # Mars→Scorpio


def _khavedamsa_sign(lon: float) -> int:
    """D40: 40 parts of 0°45'. Odd-signs → Aries seed; Even-signs → Libra seed (sequential)."""
    sign = _sign_idx_from_lon(lon)
    deg  = lon - sign * 30.0
    n_idx = int(deg / (30.0 / 40.0))   # 0..39
    seed = 0 if (sign % 2 == 0) else 6  # Aries for odd; Libra for even
    return (seed + n_idx) % 12


def _akshavedamsa_sign(lon: float) -> int:
    """D45: 45 parts of 0°40'. Movable→Aries; Fixed→Leo; Dual→Sagittarius (sequential)."""
    sign = _sign_idx_from_lon(lon)
    deg  = lon - sign * 30.0
    n_idx = int(deg / (30.0 / 45.0))   # 0..44
    if   sign in _MOVABLE: seed = 0
    elif sign in _FIXED:   seed = 4
    else:                  seed = 8
    return (seed + n_idx) % 12


def _shashtyamsa_sign(lon: float) -> int:
    """D60: 60 parts of 0°30'. Sequential from natal sign."""
    sign = _sign_idx_from_lon(lon)
    deg  = lon - sign * 30.0
    n_idx = int(deg / (30.0 / 60.0))   # 0..59
    return (sign + n_idx) % 12


def compute_d30(planets, lagna_lon=None):
    return _build_varga(planets, lagna_lon, _trimsamsa_sign, "trimsamsa")


def compute_d40(planets, lagna_lon=None):
    return _build_varga(planets, lagna_lon, _khavedamsa_sign, "khavedamsa")


def compute_d45(planets, lagna_lon=None):
    return _build_varga(planets, lagna_lon, _akshavedamsa_sign, "akshavedamsa")


def compute_d60(planets, lagna_lon=None):
    return _build_varga(planets, lagna_lon, _shashtyamsa_sign, "shashtyamsa")


def summarize_d30_for_misfortune(d30, intel):
    """Count malefics in malefic D30 signs (Mars/Saturn signs) → misfortune intensity."""
    out = {}
    if not d30: return out
    malefic_signs = {0, 7, 9, 10}   # Aries, Scorpio, Capricorn, Aquarius (Mars+Saturn)
    troubled = []
    for p in ("Mars", "Saturn", "Rahu", "Ketu", "Sun"):
        if p in d30:
            d_idx = d30[p]["sign_idx"]
            out[f"{p.lower()}_d30_sign"]     = d30[p]["sign"]
            out[f"{p.lower()}_d30_strength"] = _planet_d_strength(p, d_idx)
            if d_idx in malefic_signs:
                troubled.append(p)
    out["troubled_planets"] = troubled
    if len(troubled) >= 3:    out["verdict"] = "HIGH-MISFORTUNE-RISK"
    elif len(troubled) == 2:  out["verdict"] = "MODERATE-CAUTION"
    else:                     out["verdict"] = "LOW-RISK"
    return out


def summarize_d40_for_maternal(d40, intel):
    """4L D40 + Moon D40 → maternal legacy / matrilineal karma."""
    out = {}
    if not d40: return out
    fl = _lord_of_house(intel, 4)
    if fl and fl in d40:
        out["4L"] = fl
        out["4L_d40_sign"]     = d40[fl]["sign"]
        out["4L_d40_strength"] = _planet_d_strength(fl, d40[fl]["sign_idx"])
    if "Moon" in d40:
        out["moon_d40_sign"]     = d40["Moon"]["sign"]
        out["moon_d40_strength"] = _planet_d_strength("Moon", d40["Moon"]["sign_idx"])
    return out


def summarize_d45_for_paternal(d45, intel):
    """9L D45 + Sun D45 → paternal legacy / patrilineal karma + general."""
    out = {}
    if not d45: return out
    nl = _lord_of_house(intel, 9)
    if nl and nl in d45:
        out["9L"] = nl
        out["9L_d45_sign"]     = d45[nl]["sign"]
        out["9L_d45_strength"] = _planet_d_strength(nl, d45[nl]["sign_idx"])
    if "Sun" in d45:
        out["sun_d45_sign"]     = d45["Sun"]["sign"]
        out["sun_d45_strength"] = _planet_d_strength("Sun", d45["Sun"]["sign_idx"])
    return out


def _atma_karaka(planets):
    """Highest-degree planet (excluding Rahu/Ketu) — Jaimini Atma Karaka."""
    if not planets: return None
    best = None; best_deg = -1.0
    for p in planets:
        n = (p.get("name") or "").strip()
        if n in ("Rahu", "Ketu", ""): continue
        lon = p.get("longitude") or p.get("lon")
        if lon is None: continue
        deg_in_sign = float(lon) - int(float(lon)/30.0)*30.0
        if deg_in_sign > best_deg:
            best_deg = deg_in_sign; best = n
    return best


def summarize_d60_for_pastlife(d60, intel, planets):
    """Lagna-lord D60 + Atma Karaka D60 → past-life karma signal."""
    out = {}
    if not d60: return out
    ll = _lord_of_house(intel, 1)
    if ll and ll in d60:
        out["lagna_lord"] = ll
        out["lagna_lord_d60_sign"]     = d60[ll]["sign"]
        out["lagna_lord_d60_strength"] = _planet_d_strength(ll, d60[ll]["sign_idx"])
    ak = _atma_karaka(planets)
    if ak and ak in d60:
        out["atma_karaka"] = ak
        out["atma_karaka_d60_sign"]     = d60[ak]["sign"]
        out["atma_karaka_d60_strength"] = _planet_d_strength(ak, d60[ak]["sign_idx"])
    return out


def format_subtle_vargas_summary(d30, d40, d45, d60, intel, planets):
    """Compact LOCKED FACTS block for D30/D40/D45/D60."""
    lines = []
    if d30:
        s = summarize_d30_for_misfortune(d30, intel)
        if s:
            lines.append(f"▸ D30 TRIMSAMSA (misfortune/morality) — verdict: {s.get('verdict','-')}")
            for p in ("Mars","Saturn","Rahu","Ketu","Sun"):
                k = f"{p.lower()}_d30_sign"
                if s.get(k):
                    lines.append(f"   ▸ {p} in D30: {s[k]} — {s[f'{p.lower()}_d30_strength']}")
            if s.get("troubled_planets"):
                lines.append(f"   ▸ Malefic-sign concentration: {', '.join(s['troubled_planets'])}")
    if d40:
        s = summarize_d40_for_maternal(d40, intel)
        if s.get("4L_d40_sign") or s.get("moon_d40_sign"):
            lines.append("▸ D40 KHAVEDAMSA (maternal legacy):")
            if s.get("4L_d40_sign"):
                lines.append(f"   ▸ 4L ({s['4L']}) lands in {s['4L_d40_sign']} in D40 — {s['4L_d40_strength']}")
            if s.get("moon_d40_sign"):
                lines.append(f"   ▸ Moon in D40: {s['moon_d40_sign']} — {s['moon_d40_strength']} (matru-karaka, ancestral)")
    if d45:
        s = summarize_d45_for_paternal(d45, intel)
        if s.get("9L_d45_sign") or s.get("sun_d45_sign"):
            lines.append("▸ D45 AKSHAVEDAMSA (paternal legacy / general):")
            if s.get("9L_d45_sign"):
                lines.append(f"   ▸ 9L ({s['9L']}) lands in {s['9L_d45_sign']} in D45 — {s['9L_d45_strength']}")
            if s.get("sun_d45_sign"):
                lines.append(f"   ▸ Sun in D45: {s['sun_d45_sign']} — {s['sun_d45_strength']} (pitru-karaka, ancestral)")
    if d60:
        s = summarize_d60_for_pastlife(d60, intel, planets)
        if s.get("lagna_lord_d60_sign") or s.get("atma_karaka_d60_sign"):
            lines.append("▸ D60 SHASHTYAMSA (past-life karma — Parashara's most-prized varga):")
            if s.get("lagna_lord_d60_sign"):
                lines.append(f"   ▸ Lagna-lord ({s['lagna_lord']}) lands in {s['lagna_lord_d60_sign']} in D60 — {s['lagna_lord_d60_strength']}")
            if s.get("atma_karaka_d60_sign"):
                lines.append(f"   ▸ Atma Karaka ({s['atma_karaka']}) lands in {s['atma_karaka_d60_sign']} in D60 — {s['atma_karaka_d60_strength']} (soul-signature)")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# SPRINT-12 — Per-varga deep analysis
#   1) Vargottama Matrix    — full table of where each planet is vargottama
#                             across all 15 vargas (D1..D60). Vargottama gives
#                             exceptional strength (Parashara: "as if exalted").
#   2) Shadvarga Bala       — classical 20-point composite strength score per
#                             planet using 6 vargas (D1=6, D2=2, D3=4, D9=5,
#                             D12=2, D30=1) with own/exalt/friend tier weights.
#   3) Varga-Lagna-Lord     — for D9/D10/D24/D60, identifies varga's own
#                             lagna sign + its lord + where the lord sits IN
#                             that varga (overall varga "trustworthiness").
#
# Reference: BPHS Ch. 7 (Vargas) + Ch. 27 (Shadbala / Vimshopaka).
# ═══════════════════════════════════════════════════════════════════════════

# ── Naisargika (natural) friendship table — Friend / Neutral / Enemy ───────
_FRIEND = {
    "Sun":     {"Moon","Mars","Jupiter"},
    "Moon":    {"Sun","Mercury"},
    "Mars":    {"Sun","Moon","Jupiter"},
    "Mercury": {"Sun","Venus"},
    "Jupiter": {"Sun","Moon","Mars"},
    "Venus":   {"Mercury","Saturn"},
    "Saturn":  {"Mercury","Venus"},
}
_NEUTRAL = {
    "Sun":     {"Mercury"},
    "Moon":    {"Mars","Jupiter","Venus","Saturn"},
    "Mars":    {"Venus","Saturn"},
    "Mercury": {"Mars","Jupiter","Saturn"},
    "Jupiter": {"Saturn"},
    "Venus":   {"Mars","Jupiter"},
    "Saturn":  {"Jupiter"},
}
_ENEMY = {
    "Sun":     {"Venus","Saturn"},
    "Moon":    set(),
    "Mars":    {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury","Venus"},
    "Venus":   {"Sun","Moon"},
    "Saturn":  {"Sun","Moon","Mars"},
}

# Shadvarga weights (totals to 20)
_SHADVARGA_WEIGHTS = {"D1": 6, "D2": 2, "D3": 4, "D9": 5, "D12": 2, "D30": 1}


def _planet_in_sign_tier(planet_name: str, sign_idx: int) -> str:
    """Returns one of: OWN, EXALTED, FRIEND, NEUTRAL, ENEMY, DEBILITATED."""
    EXALT = {"Sun":0,"Moon":1,"Mars":9,"Mercury":5,"Jupiter":3,"Venus":11,"Saturn":6}
    DEBIL = {"Sun":6,"Moon":7,"Mars":3,"Mercury":11,"Jupiter":9,"Venus":5,"Saturn":0}
    OWN   = {"Sun":[4],"Moon":[3],"Mars":[0,7],"Mercury":[2,5],
             "Jupiter":[8,11],"Venus":[1,6],"Saturn":[9,10]}
    if EXALT.get(planet_name) == sign_idx: return "EXALTED"
    if DEBIL.get(planet_name) == sign_idx: return "DEBILITATED"
    if sign_idx in OWN.get(planet_name, []): return "OWN"
    sign_lord = _LORD_OF.get(sign_idx)
    if sign_lord and planet_name in _FRIEND:
        if sign_lord in _FRIEND[planet_name]:  return "FRIEND"
        if sign_lord in _NEUTRAL[planet_name]: return "NEUTRAL"
        if sign_lord in _ENEMY[planet_name]:   return "ENEMY"
    return "NEUTRAL"


_TIER_WEIGHT_FACTOR = {
    "EXALTED":     1.00,
    "OWN":         1.00,
    "FRIEND":      0.50,
    "NEUTRAL":     0.25,
    "ENEMY":       0.0625,
    "DEBILITATED": 0.00,
}


def compute_vargottama_matrix(planets, lagna_lon=None):
    """Computes a full vargottama matrix across all 15 vargas.
    Returns: { planet: { 'count': int, 'vargas': [varga_label,...] } }
    A planet is 'truly powerful' if vargottama in 5+ vargas.
    """
    if not planets:
        return {}
    # All varga mappers
    mappers = [
        ("D1",  _sign_idx_from_lon),
        ("D2",  _hora_sign),
        ("D3",  _drekkana_sign),
        ("D7",  _saptamsa_sign),
        ("D9",  _navamsa_sign),
        ("D10", _dasamsa_sign),
        ("D12", _dwadasamsa_sign),
        ("D16", _shodasamsa_sign),
        ("D20", _vimsamsa_sign),
        ("D24", _chaturvimsamsa_sign),
        ("D27", _bhamsa_sign),
        ("D30", _trimsamsa_sign),
        ("D40", _khavedamsa_sign),
        ("D45", _akshavedamsa_sign),
        ("D60", _shashtyamsa_sign),
    ]
    out = {}
    for p in planets:
        n   = (p.get("name") or "").strip()
        lon = p.get("longitude") or p.get("lon")
        if not n or lon is None or n in ("Rahu","Ketu",""):
            continue
        d1_idx = _sign_idx_from_lon(float(lon))
        hits = []
        for label, mapper in mappers:
            try:
                if mapper(float(lon)) == d1_idx:
                    hits.append(label)
            except Exception:
                pass
        if len(hits) >= 2:   # at least D1 + one more is meaningful
            out[n] = {"count": len(hits), "vargas": hits}
    return out


def compute_shadvarga_bala(planets):
    """Shadvarga Bala — classical 20-point composite strength (Parashara).
    Returns: { planet: {'score': float (0-20), 'verdict': str, 'breakdown': {varga: tier} } }
    """
    if not planets:
        return {}
    mappers = {
        "D1":  _sign_idx_from_lon, "D2":  _hora_sign,
        "D3":  _drekkana_sign,    "D9":  _navamsa_sign,
        "D12": _dwadasamsa_sign,  "D30": _trimsamsa_sign,
    }
    out = {}
    for p in planets:
        n   = (p.get("name") or "").strip()
        lon = p.get("longitude") or p.get("lon")
        if not n or lon is None or n in ("Rahu","Ketu",""):
            continue
        score = 0.0
        breakdown = {}
        for vname, mapper in mappers.items():
            try:
                d_idx = mapper(float(lon))
                tier  = _planet_in_sign_tier(n, d_idx)
                w     = _SHADVARGA_WEIGHTS[vname]
                pts   = w * _TIER_WEIGHT_FACTOR[tier]
                score += pts
                breakdown[vname] = tier
            except Exception:
                pass
        score = round(score, 2)
        if   score >= 16: verdict = "VERY-STRONG"
        elif score >= 11: verdict = "STRONG"
        elif score >= 6:  verdict = "MEDIUM"
        elif score >= 3:  verdict = "WEAK"
        else:             verdict = "VERY-WEAK"
        out[n] = {"score": score, "verdict": verdict, "breakdown": breakdown}
    return out


def compute_varga_lagna_lords(planets, lagna_lon, intel):
    """For top-4 vargas (D9/D10/D24/D60): the varga's own lagna-lord placement.
    Returns: { 'D9': {lagna_sign, lord, lord_in_sign, lord_strength}, ... }
    """
    out = {}
    if lagna_lon is None:
        return out
    spec = {
        "D9":  (_navamsa_sign,        "marriage/dharma"),
        "D10": (_dasamsa_sign,        "career"),
        "D24": (_chaturvimsamsa_sign, "education"),
        "D60": (_shashtyamsa_sign,    "past-life karma"),
    }
    # Look up _dasamsa_sign — defined inline if not present
    for vname, (mapper, theme) in spec.items():
        try:
            v_lagna_idx = mapper(float(lagna_lon))
        except Exception:
            continue
        v_lagna_sign = _SIGN_NAMES[v_lagna_idx]
        v_lagna_lord = _LORD_OF.get(v_lagna_idx)
        if not v_lagna_lord:
            continue
        # Find lord's longitude
        lord_lon = None
        for p in (planets or []):
            if (p.get("name") or "").strip() == v_lagna_lord:
                lord_lon = p.get("longitude") or p.get("lon")
                break
        if lord_lon is None:
            continue
        try:
            lord_v_idx = mapper(float(lord_lon))
        except Exception:
            continue
        out[vname] = {
            "theme": theme,
            "lagna_sign": v_lagna_sign,
            "lord": v_lagna_lord,
            "lord_in_sign": _SIGN_NAMES[lord_v_idx],
            "lord_strength": _planet_d_strength(v_lagna_lord, lord_v_idx),
        }
    return out


def format_varga_deep_summary(planets, lagna_lon, intel):
    """Compact LOCKED FACTS block for Sprint-12 deep analysis."""
    lines = []

    # 1) Vargottama matrix — top planets
    vm = compute_vargottama_matrix(planets, lagna_lon)
    if vm:
        lines.append("▸ VARGOTTAMA MATRIX (planets vargottama in multiple vargas — exceptional strength):")
        # Sort by count desc
        ranked = sorted(vm.items(), key=lambda kv: -kv[1]["count"])
        for n, info in ranked[:6]:
            vlist = ", ".join(info["vargas"])
            tag = "EXCEPTIONAL" if info["count"] >= 5 else ("STRONG" if info["count"] >= 3 else "NOTABLE")
            lines.append(f"   ▸ {n}: vargottama in {info['count']} vargas ({vlist}) — {tag}")

    # 2) Shadvarga Bala — composite 20-point score
    sb = compute_shadvarga_bala(planets)
    if sb:
        lines.append("▸ SHADVARGA BALA (composite strength 0-20 across D1+D2+D3+D9+D12+D30):")
        ranked = sorted(sb.items(), key=lambda kv: -kv[1]["score"])
        for n, info in ranked:
            lines.append(f"   ▸ {n}: {info['score']}/20 — {info['verdict']}")

    # 3) Varga-lagna-lord deep dive
    vll = compute_varga_lagna_lords(planets, lagna_lon, intel)
    if vll:
        lines.append("▸ VARGA-LAGNA-LORDS (lord of each varga's own lagna placed IN that varga):")
        for vname, info in vll.items():
            lines.append(
                f"   ▸ {vname} lagna {info['lagna_sign']} → lord {info['lord']} "
                f"in {info['lord_in_sign']} ({info['lord_strength']}) — {info['theme']}"
            )
    return "\n".join(lines)

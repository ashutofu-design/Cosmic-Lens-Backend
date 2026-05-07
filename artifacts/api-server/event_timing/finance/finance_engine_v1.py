"""
event_timing/finance/finance_engine_v1.py
==========================================
COSMIC LENS FINANCE TIMING ENGINE v1.0 — clean build, mirrors
Health v1 / Marriage v2.4 architecture.

Architecture: FILTER → VERIFY → ACTIVATE → TRIGGER (9-step pipeline,
locked May 7 2026 per user spec "finance ka same structure jaise
health/marriage timing kiya he").

  STEP 1   D1 wealth-significator filter            (FILTER)
           - 2L (income/family-wealth), 5L (Lakshmi/speculation),
             9L (luck/dharma money), 11L (gains/fulfilment)
           - 6L (debt — INVERTED: strong 6L = wins debt battle)
           - 8L (sudden gain/loss/inheritance)
           - 12L (LEAK — losses/expenses, malefic-lensed)
           - Occupants of 2/11 (direct wealth lines)
           - Planets ASPECTING the 2nd house (income activation)
           - Karakas: Jupiter (wealth wisdom), Venus (luxury),
             Mercury (commerce), Sun (income authority/PSU),
             Moon (passive/comfort wealth)
  STEP 2   D9 dignity verification                  (VERIFY)
  STEP 3   D2 Hora wealth verification              (VERIFY)
           Parashara: D2 is THE wealth chart. Sun-Hora (Leo) =
           active income; Moon-Hora (Cancer) = passive/inherited.
  STEP 4   Weighted ranking
           D1·30 + D9·20 + D2·25 + KP·15 + karaka·10
  STEP 5   Dasha activation (AD/PD primary; MD low-weight)
           AD=5, PD=6, MD=1. Signed contribution: benefic AD/PD
           lowers stress (= relief).
  STEP 6   Transit triggers
           Jupiter over 2/5/11 (gain/protection),
           Saturn over 2 (income discipline) or 12 (drain warning),
           Rahu over 11 (sudden gain) or 6 (debt warning),
           Sade Sati on 2H/2L (income squeeze)
  STEP 7   Ashtakavarga support
           SAV bindus on 2H (income strength),
           SAV bindus on 11H (gain strength)
  STEP 8   KP cuspal sub lord of 2 & 11 (wealth fulfillment)
  STEP 9   Yoga + hard-guard layer
           Dhana / Lakshmi / Kubera / Gaja-Kesari / Adhi /
           Vipreet-Rajyoga (positive), Daridra / Kemadruma (negative)

Public function:
  compute_finance_window(kundli, intel, kp, birth) -> dict

Output dict (back-compat with health/marriage-style consumers):
  {
    "verdict":              "WEALTH_PROMISED" | "STABLE" |
                            "STRESSED" | "HIGH_LEAK_WINDOW" | "UNKNOWN",
    "band":                 "WEAK" | "MEDIUM" | "STRONG",
    "current_window":       {start_iso, end_iso, severity, triggers[]},
    "next_3_windows":       [{md, ad, pd, score, severity, window,
                              start_iso, end_iso}],
    "protection_windows":   [{md, ad, pd, window, start_iso, end_iso}],
    "affected_areas":       ["income", "savings", "debt", "investing",
                              "expenses", ...],
    "recommendation_tier":  "watchful" | "supportive" |
                            "celebratory" | "consult",
    "top_finance_planets":  [{name, score, d1, d9, d2, kp, karaka,
                               significations[]}],
    "weighted_breakdown":   {planet: {d1, d9, d2, kp, karaka, total}},
    "kp_layer":             {csl_2, csl_11, verdict_2, verdict_11},
    "transits":             {saturn, rahu, ketu, mars, jupiter, sade_sati},
    "ashtakavarga":         {sav_2, sav_11, wealth_band},
    "yogas":                [{name, severity, planets}],
    "risk_flags":           [str],
    "factors":              [str],   # full audit trail
    "llm_directives":       [str],   # FINANCIAL_DISCLAIMER, etc
    "remedies":             {...},   # delegated to remedy engine money topic
    "engine_version":       "v1.0.0",
    "engine_arch":          "FILTER→VERIFY→ACTIVATE→TRIGGER",
  }

Hard guards (per user policy + replit.md):
  - Mandatory financial-disclaimer post-injector
  - NOT_INVESTMENT_ADVICE / NO_GUARANTEED_WEALTH / NO_GUARANTEED_LOSS
  - 3-confirmation rule for `consult` tier (matches money topic)
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

# Thread-local cache for the most recent engine result. Used by the
# locked_facts pipeline (same pattern as health).
_LAST_RESULT = threading.local()


def get_last_finance_result() -> Optional[Dict[str, Any]]:
    """Return the engine result from the most recent
    `compute_finance_window` call on this thread, or None."""
    return getattr(_LAST_RESULT, "value", None)


def _store_last_result(result: Dict[str, Any]) -> None:
    _LAST_RESULT.value = result


def clear_last_finance_result() -> None:
    """Explicit reset between requests (defensive)."""
    if hasattr(_LAST_RESULT, "value"):
        _LAST_RESULT.value = None


# ── External helpers (graceful degradation if unavailable) ──
try:
    from divisional_charts import compute_d9, compute_d2  # type: ignore
except Exception:
    compute_d9 = None  # type: ignore
    compute_d2 = None  # type: ignore

try:
    from ashtakavarga import compute_ashtakavarga  # type: ignore
except Exception:
    compute_ashtakavarga = None  # type: ignore

try:
    import swisseph as swe  # type: ignore
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    _SWE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    _HAS_SWE = True
except Exception:
    _HAS_SWE = False
    swe = None  # type: ignore
    _SWE_FLAGS = 0


# ════════════════════════════════════════════════════════════════════════
# Constants
# ════════════════════════════════════════════════════════════════════════
_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
          "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
_SIGN_IDX = {s: i for i, s in enumerate(_SIGNS)}

_SIGN_LORDS: Dict[int, str] = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun",
    5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter",
    9: "Saturn", 10: "Saturn", 11: "Jupiter",
}

_EXALT: Dict[str, int] = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
                           "Jupiter": 3, "Venus": 11, "Saturn": 6}
_DEBIL: Dict[str, int] = {"Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
                           "Jupiter": 9, "Venus": 5, "Saturn": 0}

_OWN_SIGNS: Dict[str, Set[int]] = {
    "Sun":     {4},
    "Moon":    {3},
    "Mars":    {0, 7},
    "Mercury": {2, 5},
    "Jupiter": {8, 11},
    "Venus":   {1, 6},
    "Saturn":  {9, 10},
}

# Finance-significant houses (per user spec — money/business semantics)
_WEALTH_HOUSES = [2, 5, 9, 11]    # income, Lakshmi, luck, gains
_LEAK_HOUSES   = [6, 8, 12]       # debt, sudden, loss/expense

# Finance-significator weights (Step 4)
_WEIGHT_D1     = 0.30
_WEIGHT_D9     = 0.20
_WEIGHT_D2     = 0.25
_WEIGHT_KP     = 0.15
_WEIGHT_KARAKA = 0.10

# Dasha scores (per user spec: AD/PD lead, MD background)
_DASHA_SCORE_MD = 1
_DASHA_SCORE_AD = 5
_DASHA_SCORE_PD = 6

# Step 1 D1 acceptance threshold
_D1_FILTER_MIN_SCORE = 12.0

# Window selection
_MIN_WINDOW_GAP_DAYS = 45

# Ashtakavarga wealth bands (SAV bindus on 2H + 11H, averaged)
_SAV_WEALTH_WEAK   = 25
_SAV_WEALTH_STRONG = 32

# 3-confirmation rule for `consult` tier (money topic per remedy engine)
_CONFIRMATIONS_FOR_CONSULT = 3

# Vimshottari standard
_VIMS_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
                "Jupiter", "Saturn", "Mercury"]
_VIMS_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
                "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}

_PLANETS_9 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
               "Saturn", "Rahu", "Ketu"]

# Finance-area signification per planet (for `affected_areas`)
_AREA_OF_PLANET: Dict[str, List[str]] = {
    "Sun":     ["income_authority", "psu_govt_income", "leadership_pay"],
    "Moon":    ["passive_income", "comfort_wealth", "fluid_business"],
    "Mars":    ["real_estate", "metals_industry", "debt_aggression"],
    "Mercury": ["business_commerce", "trading", "salary_skill"],
    "Jupiter": ["wisdom_wealth", "advisory_income", "long_savings"],
    "Venus":   ["luxury_income", "creative_money", "vehicles_assets"],
    "Saturn":  ["service_salary", "long_term_assets", "discipline_savings"],
    "Rahu":    ["sudden_gain", "foreign_money", "speculation_crypto"],
    "Ketu":    ["loss_writeoff", "research_grants", "sudden_drain"],
}

# Functional malefics by lagna sign (classical Parashari, finance lens)
_FUNC_MALEFICS: Dict[int, Set[str]] = {
    0:  {"Mercury", "Venus", "Saturn"},      # Aries
    1:  {"Moon", "Jupiter", "Venus"},         # Taurus
    2:  {"Mars", "Jupiter", "Sun"},           # Gemini
    3:  {"Mars", "Mercury", "Venus"},         # Cancer
    4:  {"Mercury", "Venus", "Saturn"},       # Leo
    5:  {"Moon", "Mars", "Jupiter"},          # Virgo
    6:  {"Sun", "Jupiter", "Mars"},           # Libra
    7:  {"Mercury", "Venus", "Saturn"},       # Scorpio
    8:  {"Venus", "Mercury"},                 # Sagittarius
    9:  {"Mars", "Jupiter", "Moon"},          # Capricorn
    10: {"Sun", "Mars", "Jupiter"},           # Aquarius
    11: {"Mercury", "Venus", "Saturn"},       # Pisces
}

# Functional benefics (Yoga karakas + protectors) by lagna sign
_FUNC_BENEFICS: Dict[int, Set[str]] = {
    0:  {"Sun", "Mars", "Jupiter"},
    1:  {"Sun", "Mercury", "Saturn"},
    2:  {"Mercury", "Venus"},
    3:  {"Mars", "Jupiter", "Moon"},
    4:  {"Sun", "Mars", "Jupiter"},
    5:  {"Mercury", "Venus"},
    6:  {"Saturn", "Mercury", "Venus"},
    7:  {"Sun", "Moon", "Jupiter"},
    8:  {"Sun", "Jupiter", "Mars"},
    9:  {"Venus", "Mercury", "Saturn"},
    10: {"Venus", "Mercury", "Saturn"},
    11: {"Moon", "Mars", "Jupiter"},
}


# ════════════════════════════════════════════════════════════════════════
# Low-level helpers (aligned with health_engine_v1 / marriage_engine_v2)
# ════════════════════════════════════════════════════════════════════════
def _sign_idx(name_or_str: Any) -> Optional[int]:
    if isinstance(name_or_str, int):
        return name_or_str % 12
    if isinstance(name_or_str, str):
        return _SIGN_IDX.get(name_or_str)
    return None


def _planet_house(planets: List[dict], pname: str) -> Optional[int]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == pname:
            h = p.get("house")
            if isinstance(h, int):
                return h
    return None


def _planet_sign_idx(planets: List[dict], pname: str) -> Optional[int]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == pname:
            si = p.get("sign_idx")
            if isinstance(si, int):
                return si % 12
            return _sign_idx(p.get("sign"))
    return None


def _house_lord(lagna_si: int, house: int) -> str:
    sign_at_house = (lagna_si + house - 1) % 12
    return _SIGN_LORDS[sign_at_house]


def _house_of_sign(sign_si: int, lagna_si: int) -> int:
    return ((sign_si - lagna_si) % 12) + 1


def _planets_in_house(planets: List[dict], house: int) -> List[str]:
    return [p["name"] for p in (planets or [])
            if isinstance(p, dict) and p.get("house") == house
            and p.get("name") in _PLANETS_9]


def _aspects_house(aspector: str, ap_house: int, target_house: int) -> bool:
    """Standard Parashari aspects."""
    if not (1 <= ap_house <= 12 and 1 <= target_house <= 12):
        return False
    diff = ((target_house - ap_house) % 12) + 1
    if diff == 7:
        return True
    extras = {
        "Mars":    {4, 8},
        "Jupiter": {5, 9},
        "Saturn":  {3, 10},
        "Rahu":    {3, 10},
        "Ketu":    {3, 10},
    }
    return diff in extras.get(aspector, set())


def _kp_cusp(kp: dict, house: int) -> Optional[dict]:
    for c in (kp or {}).get("cusps", []) or []:
        if isinstance(c, dict) and c.get("house") == house:
            return c
    return None


def _planet_signified_houses(kp: dict, planet: str) -> List[int]:
    sig = (kp or {}).get("significations") or {}
    raw = sig.get(planet) or sig.get(planet.lower()) or []
    out: List[int] = []
    for v in raw:
        try:
            h = int(v)
            if 1 <= h <= 12:
                out.append(h)
        except (TypeError, ValueError):
            continue
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 1 — D1 wealth-significator filter
# ════════════════════════════════════════════════════════════════════════
def _step1_d1_filter(kundli: dict, lagna_si: int
                       ) -> Dict[str, Dict[str, Any]]:
    """Identify wealth-significant planets in D1.

    Inclusion (per user spec):
      • 2L  (income/family wealth)        — high weight
      • 11L (gains/fulfilment)             — high weight
      • 5L  (Lakshmi/speculation/poorva)  — medium weight
      • 9L  (luck/dharma money)            — medium weight
      • 6L  (debt/loans)                   — medium weight (inverted role)
      • 8L  (sudden inheritance/loss)      — medium weight
      • 12L (loss/expense LEAK)            — medium-high (drag signal)
      • Occupants of 2/11                  — direct wealth links
      • Planets ASPECTING the 2nd house    — income activation
      • Karakas: Jupiter/Venus/Mercury/Sun/Moon — always considered
    """
    planets = kundli.get("planets") or []
    out: Dict[str, Dict[str, Any]] = {}
    for p in _PLANETS_9:
        out[p] = {"d1": 0.0, "in_filter": False, "links": [],
                   "is_lord_of": [], "occupies": None,
                   "aspects_2": False}

    # Lordship checks
    for h, weight, label in (
        (2,  16.0, "2L (income/family-wealth)"),
        (11, 16.0, "11L (gains/fulfilment)"),
        (5,  10.0, "5L (Lakshmi/speculation)"),
        (9,  10.0, "9L (dharma/luck money)"),
        (6,   8.0, "6L (debt — inverted)"),
        (8,   8.0, "8L (sudden gain/loss)"),
        (12, 12.0, "12L (LEAK/expense)"),
    ):
        lord = _house_lord(lagna_si, h)
        out[lord]["is_lord_of"].append(h)
        out[lord]["d1"] += weight
        out[lord]["links"].append(label)

    # Occupants of 2 / 11 (direct wealth)
    for h in (2, 11):
        for pname in _planets_in_house(planets, h):
            out[pname]["occupies"] = h
            bump = {2: 12.0, 11: 12.0}[h]
            out[pname]["d1"] += bump
            out[pname]["links"].append(f"occupies {h}H (wealth-house)")

    # Occupants of 12 (leak — boost so leak shows up in ranking)
    for pname in _planets_in_house(planets, 12):
        if out[pname]["occupies"] is None:
            out[pname]["occupies"] = 12
        out[pname]["d1"] += 8.0
        out[pname]["links"].append("occupies 12H (LEAK)")

    # Planets ASPECTING the 2nd house (per user spec)
    for pname in _PLANETS_9:
        ap_house = _planet_house(planets, pname)
        if ap_house and _aspects_house(pname, ap_house, 2):
            out[pname]["aspects_2"] = True
            out[pname]["d1"] += 8.0
            out[pname]["links"].append("aspects 2H (income activation)")

    # Primary wealth karakas — always considered (small bonus to survive)
    for karaka, bonus, role in (
        ("Jupiter", 10.0, "wealth-wisdom karaka (Dhana-karaka)"),
        ("Venus",   8.0,  "luxury/asset karaka"),
        ("Mercury", 7.0,  "commerce/trading karaka"),
        ("Sun",     6.0,  "income-authority karaka"),
        ("Moon",    6.0,  "passive/comfort wealth karaka"),
    ):
        out[karaka]["d1"] += bonus
        out[karaka]["links"].append(role)

    # Functional malefic surcharge for lagna (drag on wealth flow)
    fm = _FUNC_MALEFICS.get(lagna_si, set())
    for pname in fm:
        out[pname]["d1"] += 4.0
        out[pname]["links"].append("functional malefic for lagna")

    # Mark survivors
    for pname, info in out.items():
        info["in_filter"] = info["d1"] >= _D1_FILTER_MIN_SCORE

    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 2 — D9 dignity verification
# ════════════════════════════════════════════════════════════════════════
def _step2_d9_verify(kundli: dict, candidates: Set[str]) -> Dict[str, float]:
    """Score each candidate by D9 dignity. Higher D9 dignity → planet
    delivers wealth karma cleanly; debilitated → muddled. Range 0-25.
    """
    out: Dict[str, float] = {p: 0.0 for p in candidates}
    if not candidates:
        return out
    d9 = None
    if compute_d9 is not None:
        try:
            d9 = compute_d9(kundli)
        except Exception:
            d9 = None
    if not d9:
        return {p: 8.0 for p in candidates}
    d9_planets = d9.get("planets") if isinstance(d9, dict) else None
    if not d9_planets:
        return {p: 8.0 for p in candidates}
    for pname in candidates:
        si = _planet_sign_idx(d9_planets, pname)
        if si is None:
            out[pname] = 8.0
            continue
        if pname in _EXALT and si == _EXALT[pname]:
            out[pname] = 25.0
        elif pname in _OWN_SIGNS and si in _OWN_SIGNS[pname]:
            out[pname] = 20.0
        elif pname in _DEBIL and si == _DEBIL[pname]:
            out[pname] = 5.0
        else:
            out[pname] = 12.0
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 3 — D2 Hora wealth verification (Parashara's wealth chart)
# ════════════════════════════════════════════════════════════════════════
def _step3_d2_hora(kundli: dict, candidates: Set[str]) -> Dict[str, float]:
    """D2 Hora is THE wealth chart per Parashara. Each sign is split in
    half: odd-sign 0-15° = Sun-Hora (Leo), 15-30° = Moon-Hora (Cancer);
    reversed for even signs. A wealth-significator landing in Sun-Hora
    or Moon-Hora delivers wealth strongly. Range 0-25.

    Sun-Hora = active income; Moon-Hora = passive/inherited wealth.
    Both are wealth-positive — a planet outside both is wealth-neutral.
    """
    out: Dict[str, float] = {p: 0.0 for p in candidates}
    if not candidates or compute_d2 is None:
        return {p: 8.0 for p in candidates}
    planets_in = kundli.get("planets") or []
    if not planets_in:
        return {p: 8.0 for p in candidates}
    try:
        # divisional_charts.compute_d2 takes raw planet list (with
        # longitude) — try lon/longitude/fullDegree on each item.
        d2 = compute_d2(planets_in, lagna_lon=None)
    except Exception:
        d2 = None
    if not isinstance(d2, dict) or not d2:
        return {p: 8.0 for p in candidates}
    for pname in candidates:
        info = d2.get(pname)
        if not isinstance(info, dict):
            out[pname] = 8.0
            continue
        sign = info.get("sign")
        if sign == "Leo":          # Sun-Hora — active income
            out[pname] = 22.0
        elif sign == "Cancer":     # Moon-Hora — passive wealth
            out[pname] = 18.0
        else:
            # Should never happen for D2 (only 2 possible signs) but
            # defend against schema drift.
            out[pname] = 8.0
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 3.5 — KP layer (cuspal sub lord of 2nd & 11th)
# ════════════════════════════════════════════════════════════════════════
def _step3_5_kp_layer(kp: dict, lagna_si: int) -> Dict[str, Any]:
    """KP cuspal sub lord of 2nd & 11th cusps.
    Verdict rules (KP standard for wealth):
      2 CSL signifies 2/11/9/5 → income YES
      2 CSL signifies 6/8/12   → income blocked / debt
      11 CSL signifies 2/11/5  → gains YES
      11 CSL signifies 6/8/12  → gains blocked / wealth-leak
    """
    out = {"csl_2": None, "csl_11": None,
           "verdict_2": "UNKNOWN", "verdict_11": "UNKNOWN",
           "csl_2_signifies": [], "csl_11_signifies": []}
    if not kp:
        return out
    c2 = _kp_cusp(kp, 2)
    c11 = _kp_cusp(kp, 11)
    if c2:
        csl = c2.get("sl") or c2.get("subLord") or c2.get("sub_lord")
        out["csl_2"] = csl
        if csl:
            sig = _planet_signified_houses(kp, csl)
            out["csl_2_signifies"] = sig
            if any(h in _WEALTH_HOUSES for h in sig):
                out["verdict_2"] = "INCOME_YES"
            elif any(h in _LEAK_HOUSES for h in sig):
                out["verdict_2"] = "INCOME_BLOCKED"
            else:
                out["verdict_2"] = "NEUTRAL"
    if c11:
        csl = c11.get("sl") or c11.get("subLord") or c11.get("sub_lord")
        out["csl_11"] = csl
        if csl:
            sig = _planet_signified_houses(kp, csl)
            out["csl_11_signifies"] = sig
            if any(h in _WEALTH_HOUSES for h in sig):
                out["verdict_11"] = "GAINS_YES"
            elif any(h in _LEAK_HOUSES for h in sig):
                out["verdict_11"] = "GAINS_BLOCKED"
            else:
                out["verdict_11"] = "NEUTRAL"
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 4 — Weighted ranking
# ════════════════════════════════════════════════════════════════════════
def _karaka_score(pname: str, lagna_si: int) -> float:
    """Wealth-karaka score (0-10)."""
    base = {"Jupiter": 8.0, "Venus": 7.0, "Mercury": 6.0,
            "Sun": 5.0, "Moon": 4.0, "Mars": 4.0, "Saturn": 5.0,
            "Rahu": 4.0, "Ketu": 3.0}.get(pname, 0.0)
    # Functional benefic boost (yoga-karaka for lagna)
    if pname in _FUNC_BENEFICS.get(lagna_si, set()):
        base += 2.0
    return min(10.0, base)


def _step4_rank(d1_map: Dict[str, Dict[str, Any]],
                d9_scores: Dict[str, float],
                d2_scores: Dict[str, float],
                kp: dict, lagna_si: int) -> List[Dict[str, Any]]:
    """Rank surviving candidates by weighted score.
    Score = D1·30% + D9·20% + D2·25% + KP·15% + Karaka·10%
    All sub-scores normalized to 0-25 first.
    """
    survivors = [p for p, info in d1_map.items() if info.get("in_filter")]
    if not survivors:
        return []
    raw_d1 = {p: d1_map[p]["d1"] for p in survivors}
    max_d1 = max(raw_d1.values()) or 1.0
    ranked: List[Dict[str, Any]] = []
    for pname in survivors:
        info = d1_map[pname]
        d1 = (raw_d1[pname] / max_d1) * 25.0
        d9 = d9_scores.get(pname, 8.0)
        d2 = d2_scores.get(pname, 8.0)
        # KP signification of wealth/leak
        sig = _planet_signified_houses(kp, pname)
        kp_score = 0.0
        if any(h in _WEALTH_HOUSES for h in sig):
            kp_score = 18.0
        if 2 in sig:
            kp_score += 4.0
        if 11 in sig:
            kp_score += 4.0
        kp_score = min(25.0, kp_score) if kp_score > 0 else 6.0
        karaka = _karaka_score(pname, lagna_si) * 2.5  # scale to 0-25
        total = (d1 * _WEIGHT_D1 + d9 * _WEIGHT_D9 +
                 d2 * _WEIGHT_D2 + kp_score * _WEIGHT_KP +
                 karaka * _WEIGHT_KARAKA)
        ranked.append({
            "name": pname,
            "score": round(total, 2),
            "d1": round(d1, 2), "d9": round(d9, 2),
            "d2": round(d2, 2), "kp": round(kp_score, 2),
            "karaka": round(karaka, 2),
            "links": list(info["links"]),
            "significations": _AREA_OF_PLANET.get(pname, []),
        })
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked


# ════════════════════════════════════════════════════════════════════════
# STEP 5 — Dasha activation (AD/PD primary, MD low-weight)
# ════════════════════════════════════════════════════════════════════════
def _parse_iso(s: Any) -> Optional[datetime]:
    if not s:
        return None
    if isinstance(s, datetime):
        return s
    if isinstance(s, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                return datetime.strptime(s.split("+")[0].split("Z")[0], fmt)
            except (ValueError, TypeError):
                continue
    return None


def _dasha_lord(node: dict) -> Optional[str]:
    for k in ("lord", "planet", "name", "ruler"):
        v = node.get(k)
        if v:
            return v
    return None


def _dasha_start_end(node: dict) -> Tuple[Optional[datetime], Optional[datetime]]:
    s = (node.get("start") or node.get("startDate") or
         node.get("from") or node.get("start_date"))
    e = (node.get("end") or node.get("endDate") or
         node.get("to") or node.get("end_date"))
    return _parse_iso(s), _parse_iso(e)


def _dasha_children(node: dict) -> List[dict]:
    for k in ("subDashas", "antardashas", "ad", "sub_dashas",
              "pratyantar", "pd", "children"):
        v = node.get(k)
        if isinstance(v, list):
            return v
    return []


def _flatten_dasha_chain(kundli: dict) -> List[Dict[str, Any]]:
    """Flatten Vimshottari MD/AD/PD chain. Same shape-tolerance as
    health/marriage engines."""
    out: List[Dict[str, Any]] = []
    dashas = kundli.get("dashas") or []
    if not isinstance(dashas, list):
        return out
    for md in dashas:
        if not isinstance(md, dict):
            continue
        md_lord = _dasha_lord(md)
        ads = _dasha_children(md)
        if not ads:
            ms, me = _dasha_start_end(md)
            if ms and me:
                out.append({"md": md_lord, "ad": None, "pd": None,
                             "start": ms, "end": me})
            continue
        for ad in ads:
            if not isinstance(ad, dict):
                continue
            ad_lord = _dasha_lord(ad)
            pds = _dasha_children(ad)
            if not pds:
                ads_, ade_ = _dasha_start_end(ad)
                if ads_ and ade_:
                    out.append({"md": md_lord, "ad": ad_lord, "pd": None,
                                 "start": ads_, "end": ade_})
                continue
            for pd in pds:
                if not isinstance(pd, dict):
                    continue
                pds_, pde_ = _dasha_start_end(pd)
                if not (pds_ and pde_):
                    continue
                out.append({
                    "md": md_lord, "ad": ad_lord,
                    "pd": _dasha_lord(pd),
                    "start": pds_, "end": pde_,
                })
    return out


def _step5_dasha_activation(chain: List[Dict[str, Any]],
                              ranked: List[Dict[str, Any]],
                              lagna_si: int,
                              now: datetime,
                              horizon_years: int = 10
                              ) -> List[Dict[str, Any]]:
    """Score each upcoming dasha window by wealth-significator activation.

    AD=5, PD=6, MD=1. SIGNED contribution: a benefic AD/PD over a
    leak-period lowers stress (= relief), a malefic / 12L / 6L over
    a wealth period raises stress.

    NOTE on sign convention: we score STRESS / DRAG. High score = window
    of leak/expense/blocked-gains. Low score (or strong relief) = wealth
    flow window. Verdict layer flips this into WEALTH_PROMISED vs
    HIGH_LEAK_WINDOW.
    """
    if not chain or not ranked:
        return []
    score_map = {r["name"]: r["score"] for r in ranked}
    max_score = max(score_map.values()) or 1.0

    # Classify each ranked planet as wealth-bringer or leak-bringer.
    # CRITICAL (architect-fix May 7 2026): "functional malefic for lagna"
    # is intentionally EXCLUDED from leak detection. It is a Step-1
    # ranking modifier only; using it here would flip wealth-promoter
    # planets that happen to be functional malefics (e.g. Saturn = 11L
    # for Aries lagna IS a functional malefic) into leak-lords and force
    # every Aries-lagna chart into HIGH_LEAK_WINDOW. Dasha classification
    # uses ONLY the planet's actual house-lord role + occupation.
    # Conflict resolution: when a planet carries BOTH wealth and leak
    # tags (e.g. Pisces lagna → Saturn = 11L AND 12L), the dominant
    # role wins by tag-count.
    leak_lords: Set[str] = set()
    wealth_lords: Set[str] = set()
    _LEAK_TAGS = ("12L (LEAK", "occupies 12H", "occupies 6H",
                   "6L (debt", "8L (sudden")
    _WEALTH_TAGS = ("2L (income", "11L (gains", "5L (Lakshmi",
                     "9L (dharma", "occupies 2H", "occupies 11H",
                     "wealth-wisdom karaka", "luxury/asset karaka",
                     "commerce/trading karaka",
                     "income-authority karaka",
                     "passive/comfort wealth")
    for r in ranked:
        leak_count = 0
        wealth_count = 0
        for l in r["links"]:
            if any(tag in l for tag in _LEAK_TAGS):
                leak_count += 1
            if any(tag in l for tag in _WEALTH_TAGS):
                wealth_count += 1
        if leak_count and wealth_count:
            # Conflict — assign by which role dominates
            if leak_count > wealth_count:
                leak_lords.add(r["name"])
            else:
                wealth_lords.add(r["name"])
        elif leak_count:
            leak_lords.add(r["name"])
        elif wealth_count:
            wealth_lords.add(r["name"])

    lagna_lord = _house_lord(lagna_si, 1)
    func_benefics = _FUNC_BENEFICS.get(lagna_si, set())
    pure_benefics = ({"Jupiter", "Venus", lagna_lord}
                     | func_benefics | wealth_lords)

    def _sign_for(lord: str) -> int:
        """+1 = adds stress (leak), -1 = relief (wealth flow)."""
        if lord in leak_lords:
            return +1
        if lord in pure_benefics:
            return -1
        return +1 if lord in {"Mars", "Saturn", "Rahu", "Ketu"} else 0

    horizon_end = now + timedelta(days=365 * horizon_years)
    windows: List[Dict[str, Any]] = []
    for w in chain:
        if w["end"] < now or w["start"] > horizon_end:
            continue
        stress = 0.0
        relief = 0.0
        triggers: List[str] = []
        for role, lord, weight in (("MD", w["md"], _DASHA_SCORE_MD),
                                    ("AD", w["ad"], _DASHA_SCORE_AD),
                                    ("PD", w["pd"], _DASHA_SCORE_PD)):
            if not (lord and lord in score_map):
                continue
            rel = score_map[lord] / max_score
            contrib = weight * rel
            sign = _sign_for(lord)
            if sign > 0:
                stress += contrib
                tag = "LEAK_LORD" if lord in leak_lords else "MALEFIC_KARAKA"
                triggers.append(f"{role}={lord}({tag},+{contrib:.2f})")
            elif sign < 0:
                relief += contrib
                tag = "WEALTH_LORD" if lord in wealth_lords else "BENEFIC"
                triggers.append(f"{role}={lord}({tag},-{contrib:.2f})")
            else:
                triggers.append(f"{role}={lord}(NEUTRAL,0)")
        net = max(0.0, stress - relief)
        if net <= 0 and relief == 0:
            continue
        windows.append({
            "md": w["md"], "ad": w["ad"], "pd": w["pd"],
            "start": w["start"], "end": w["end"],
            "score": round(net, 2),
            "stress_raw": round(stress, 2),
            "relief_raw": round(relief, 2),
            "triggers": triggers,
        })
    windows.sort(key=lambda x: (-x["score"], x["start"]))
    return windows


# ════════════════════════════════════════════════════════════════════════
# STEP 6 — Transit triggers
# ════════════════════════════════════════════════════════════════════════
def _planet_sign_at(planet_id: int, when: datetime) -> Optional[int]:
    if not _HAS_SWE:
        return None
    try:
        jd = swe.julday(when.year, when.month, when.day,
                         when.hour + when.minute / 60.0)
        lon = swe.calc_ut(jd, planet_id, _SWE_FLAGS)[0][0]
        return int(lon // 30) % 12
    except Exception:
        return None


def _step6_transits(kundli: dict, lagna_si: int,
                     planets_d1: List[dict],
                     now: datetime) -> Dict[str, Any]:
    """Compute current transit triggers — finance lens."""
    out = {"saturn": None, "rahu": None, "ketu": None,
           "mars": None, "jupiter": None, "sade_sati": None,
           "active_triggers": []}
    if not _HAS_SWE:
        out["note"] = "swisseph unavailable; transit layer skipped"
        return out

    moon_si = _planet_sign_idx(planets_d1, "Moon")
    saturn_si = _planet_sign_at(swe.SATURN, now)
    rahu_si = _planet_sign_at(swe.MEAN_NODE, now)
    ketu_si = (rahu_si + 6) % 12 if rahu_si is not None else None
    mars_si = _planet_sign_at(swe.MARS, now)
    jupiter_si = _planet_sign_at(swe.JUPITER, now)

    def _h(si):
        return _house_of_sign(si, lagna_si) if si is not None else None

    sat_h = _h(saturn_si)
    rahu_h = _h(rahu_si)
    ketu_h = _h(ketu_si)
    mars_h = _h(mars_si)
    jup_h = _h(jupiter_si)

    # Saturn over 2H/12H — income discipline / drain
    if sat_h == 2:
        out["saturn"] = "Saturn transiting 2H — income squeeze / discipline pressure"
        out["active_triggers"].append(("saturn", 2, 0.8))
    elif sat_h == 12:
        out["saturn"] = "Saturn transiting 12H — expense / drain warning"
        out["active_triggers"].append(("saturn", 12, 1.0))
    elif sat_h == 11:
        out["saturn"] = "Saturn transiting 11H — slow but steady gain consolidation"
        out["active_triggers"].append(("saturn_protect", 11, -0.5))

    # Rahu over 11H = sudden gain; over 6H = debt / fraud risk
    if rahu_h == 11:
        out["rahu"] = "Rahu transit on 11H — sudden gains / unconventional income"
        out["active_triggers"].append(("rahu_gain", 11, -0.6))
    elif rahu_h in (6, 8, 12):
        out["rahu"] = f"Rahu transit on {rahu_h}H — debt/fraud/leak risk"
        out["active_triggers"].append(("rahu", rahu_h, 0.9))

    if ketu_h in (2, 8, 12):
        out["ketu"] = f"Ketu transit on {ketu_h}H — sudden writeoff / detachment"
        out["active_triggers"].append(("ketu", ketu_h, 0.7))

    # Mars over 2/8/12 — aggressive expense / sudden loss
    if mars_h in (2, 8, 12):
        out["mars"] = f"Mars transit in {mars_h}H — aggressive expense / impulse spend"
        out["active_triggers"].append(("mars", mars_h, 0.6))

    # Jupiter over 2/5/11 — wealth protection / gain window
    if jup_h in (2, 5, 11):
        out["jupiter"] = f"Jupiter transit in {jup_h}H — wealth-flow protection / gain"
        out["active_triggers"].append(("jupiter_protect", jup_h, -1.0))

    # Sade Sati on Moon (income pressure)
    if moon_si is not None and saturn_si is not None:
        delta = (saturn_si - moon_si) % 12
        if delta == 11:
            out["sade_sati"] = "first_phase (Saturn 12th from Moon)"
            out["active_triggers"].append(("sade_sati", 12, 0.6))
        elif delta == 0:
            out["sade_sati"] = "peak_phase (Saturn over Moon)"
            out["active_triggers"].append(("sade_sati", 1, 1.0))
        elif delta == 1:
            out["sade_sati"] = "exit_phase (Saturn 2nd from Moon)"
            out["active_triggers"].append(("sade_sati", 2, 0.6))
        elif delta in (3, 7):
            out["sade_sati"] = f"dhaiya (Saturn {delta+1}th from Moon)"
            out["active_triggers"].append(("dhaiya", delta + 1, 0.4))

    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 7 — Ashtakavarga support (SAV bindus on 2H + 11H)
# ════════════════════════════════════════════════════════════════════════
def _step7_ashtakavarga(kundli: dict, lagna_si: int) -> Dict[str, Any]:
    out = {"sav_2": None, "sav_11": None, "wealth_band": "UNKNOWN"}
    if compute_ashtakavarga is None:
        return out
    try:
        planets = kundli.get("planets") or []
        av = compute_ashtakavarga(planets, lagna_si)
    except Exception:
        return out
    if not isinstance(av, dict):
        return out
    sav = av.get("sav")
    # Schema: sav is a 12-element list indexed 0..11 by HOUSE-1
    if isinstance(sav, list) and len(sav) == 12:
        out["sav_2"] = sav[1]   # 2nd house
        out["sav_11"] = sav[10]  # 11th house
    if (isinstance(out["sav_2"], (int, float))
            and isinstance(out["sav_11"], (int, float))):
        avg = (out["sav_2"] + out["sav_11"]) / 2.0
        if avg < _SAV_WEALTH_WEAK:
            out["wealth_band"] = "WEAK"
        elif avg >= _SAV_WEALTH_STRONG:
            out["wealth_band"] = "STRONG"
        else:
            out["wealth_band"] = "MEDIUM"
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 9 — Yoga + hard guards
# ════════════════════════════════════════════════════════════════════════
def _detect_yogas(kundli: dict, lagna_si: int,
                   planets: List[dict]) -> List[Dict[str, Any]]:
    """Detect classical wealth-relevant yogas.

    Positive: Dhana / Lakshmi / Kubera / Gaja-Kesari / Adhi /
              Vipreet-Rajyoga
    Negative: Daridra / Kemadruma / Papakartari (Lagna or 2H)
    """
    out: List[Dict[str, Any]] = []

    # ── Dhana Yoga: 2L + 11L conjunction OR mutual aspect ──
    h2_lord = _house_lord(lagna_si, 2)
    h11_lord = _house_lord(lagna_si, 11)
    if h2_lord != h11_lord:
        h2 = _planet_house(planets, h2_lord)
        h11 = _planet_house(planets, h11_lord)
        if h2 and h11:
            if h2 == h11:
                out.append({"name": "Dhana Yoga (2L+11L conjunction)",
                            "severity": "protective",
                            "planets": [h2_lord, h11_lord]})
            elif (_aspects_house(h2_lord, h2, h11)
                  or _aspects_house(h11_lord, h11, h2)):
                out.append({"name": "Dhana Yoga (2L↔11L mutual aspect)",
                            "severity": "protective",
                            "planets": [h2_lord, h11_lord]})

    # ── Lakshmi Yoga: Venus own/exalted + 9L strong ──
    venus_si = _planet_sign_idx(planets, "Venus")
    venus_dignity_ok = (venus_si is not None
                        and (venus_si in _OWN_SIGNS["Venus"]
                             or venus_si == _EXALT["Venus"]))
    h9_lord = _house_lord(lagna_si, 9)
    h9_lord_si = _planet_sign_idx(planets, h9_lord)
    h9_lord_strong = (h9_lord_si is not None
                      and (h9_lord_si in _OWN_SIGNS.get(h9_lord, set())
                           or h9_lord_si == _EXALT.get(h9_lord, -1)))
    if venus_dignity_ok and h9_lord_strong:
        out.append({"name": "Lakshmi Yoga",
                    "severity": "protective",
                    "planets": ["Venus", h9_lord]})

    # ── Gaja-Kesari: Jupiter-Moon kendra (1/4/7/10 from each other) ──
    jup_h = _planet_house(planets, "Jupiter")
    moon_h = _planet_house(planets, "Moon")
    if jup_h and moon_h:
        delta = ((jup_h - moon_h) % 12) + 1
        if delta in (1, 4, 7, 10):
            out.append({"name": "Gaja-Kesari Yoga",
                        "severity": "protective",
                        "planets": ["Jupiter", "Moon"]})

    # ── Kubera Yoga: 2L + 11L + benefic angle ──
    if h2_lord != h11_lord:
        h2 = _planet_house(planets, h2_lord)
        h11 = _planet_house(planets, h11_lord)
        benefic_angle = False
        for benefic in ("Jupiter", "Venus"):
            bh = _planet_house(planets, benefic)
            if bh and h2 and h11 and (bh == h2 or bh == h11
                                       or _aspects_house(benefic, bh, h2)
                                       or _aspects_house(benefic, bh, h11)):
                benefic_angle = True
                break
        if benefic_angle:
            out.append({"name": "Kubera Yoga (2L+11L+benefic)",
                        "severity": "protective",
                        "planets": [h2_lord, h11_lord]})

    # ── Vipreet Rajyoga: STRICT — 6L/8L/12L mutually exchanged or
    # conjunct in dusthana (not just any planet in 6/8/12) ──
    dusthana_lords = [_house_lord(lagna_si, h) for h in (6, 8, 12)]
    dusthana_lord_houses = {l: _planet_house(planets, l)
                             for l in dusthana_lords}
    in_dusthana = [(l, h) for l, h in dusthana_lord_houses.items()
                   if h in (6, 8, 12)]
    if len(in_dusthana) >= 2:
        out.append({"name": "Vipreet Rajyoga (dusthana exchange)",
                    "severity": "protective",
                    "planets": [l for l, _ in in_dusthana]})

    # ── Daridra Yoga: 11L in 6/8/12 OR 2L in 6/8/12 ──
    h11_h = _planet_house(planets, h11_lord)
    h2_h = _planet_house(planets, h2_lord)
    if h11_h in (6, 8, 12):
        out.append({"name": "Daridra Yoga (11L in dusthana)",
                    "severity": "high",
                    "planets": [h11_lord]})
    if h2_h in (6, 8, 12):
        out.append({"name": "Daridra Yoga (2L in dusthana)",
                    "severity": "high",
                    "planets": [h2_lord]})

    # ── Kemadruma: Moon alone (no planets in 2nd or 12th from Moon,
    # excluding Sun/Rahu/Ketu and except when Moon is in kendra) ──
    if moon_h:
        prev_h = ((moon_h - 2) % 12) + 1
        next_h = (moon_h % 12) + 1
        adj_planets = (set(_planets_in_house(planets, prev_h))
                       | set(_planets_in_house(planets, next_h)))
        adj_planets.discard("Sun"); adj_planets.discard("Rahu")
        adj_planets.discard("Ketu")
        moon_in_kendra = moon_h in (1, 4, 7, 10)
        if not adj_planets and not moon_in_kendra:
            out.append({"name": "Kemadruma Yoga (Moon isolated)",
                        "severity": "moderate",
                        "planets": ["Moon"]})

    # ── Papakartari around 2H (income squeezed by malefics) ──
    h1_occ = _planets_in_house(planets, 1)
    h3_occ = _planets_in_house(planets, 3)
    malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    if (set(h1_occ) & malefics) and (set(h3_occ) & malefics):
        out.append({"name": "Papakartari (2H squeezed)",
                    "severity": "moderate",
                    "planets": sorted(set(h1_occ + h3_occ) & malefics)})

    return out


# ════════════════════════════════════════════════════════════════════════
# Helpers — verdict / severity / age
# ════════════════════════════════════════════════════════════════════════
def _parse_dob_dt(birth: Any, kundli: Any = None) -> Optional[datetime]:
    """Reuses marriage v2.4 multi-format parser logic."""
    candidates = []
    for src in (birth, kundli):
        if isinstance(src, dict):
            for k in ("dob", "birth_date", "birthDate", "DOB", "date"):
                v = src.get(k)
                if v:
                    candidates.append(v)
            try:
                d = src.get("day"); m = src.get("month"); y = src.get("year")
                if d and m and y:
                    candidates.append(f"{int(y):04d}-{int(m):02d}-{int(d):02d}")
            except Exception:
                pass
    fmts = ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
            "%d %b %Y", "%d %B %Y", "%d-%b-%Y", "%d-%B-%Y")
    for c in candidates:
        if isinstance(c, datetime):
            return c
        if not isinstance(c, str):
            continue
        s = c.split("T")[0].strip()
        for fmt in fmts:
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
    return None


def _compute_age(birth_dt: Optional[datetime], ref: datetime) -> Optional[int]:
    if not birth_dt:
        return None
    age = ref.year - birth_dt.year - (
        (ref.month, ref.day) < (birth_dt.month, birth_dt.day))
    if 0 <= age <= 120:
        return age
    return None


def _severity_of_window(score: float, transit_load: float) -> str:
    """Map raw stress score to a finance severity tier.

    Tiers (matching money topic in remedy engine):
      celebratory : strong wealth flow, very low stress
      supportive  : positive flow, low stress
      watchful    : moderate stress, action needed
      consult     : serious stress / heavy leak
    """
    s = score + max(0.0, transit_load)
    if s < 2.0:
        return "celebratory"
    if s < 4.5:
        return "supportive"
    if s < 8.0:
        return "watchful"
    return "consult"


def _recommendation_tier(severity: str, confirmations: int,
                          age: Optional[int]) -> str:
    """Map current severity + confirmation count → recommendation tier.
    Uses the 4-tier money/business taxonomy from remedy engine.
    """
    if severity == "consult" and confirmations >= _CONFIRMATIONS_FOR_CONSULT:
        return "consult"
    if severity == "consult":
        return "watchful"
    return severity   # celebratory / supportive / watchful pass through


def _derive_verdict(top_window_score: float,
                     wealth_band: str,
                     yogas: List[Dict[str, Any]],
                     transit_load: float
                     ) -> Tuple[str, str]:
    """Combine top-window stress, ashtakavarga band, yogas and transits
    into a single verdict + band.
    """
    # CRITICAL (architect-fix May 7 2026): old logic let any single
    # `has_high_neg` yoga (e.g. one Daridra ribbon) hard-override verdict
    # to HIGH_LEAK regardless of stress. Now `has_high_neg` only forces
    # HIGH_LEAK when stress is also elevated AND no protective yoga
    # rescues the chart.
    band = wealth_band if wealth_band in {"WEAK", "MEDIUM", "STRONG"} else "MEDIUM"
    has_high_neg = any(y.get("severity") == "high" for y in yogas)
    has_protect = any(y.get("severity") == "protective" for y in yogas)

    s = top_window_score + max(0.0, transit_load)
    if s >= 8.0:
        return "HIGH_LEAK_WINDOW", "WEAK"
    if s >= 4.5 and has_high_neg and not has_protect:
        return "HIGH_LEAK_WINDOW", "WEAK"
    if s >= 4.5:
        verdict = "STRESSED"
        if has_protect:
            verdict = "STABLE"
        return verdict, band
    if has_high_neg and not has_protect:
        return "STRESSED", band
    if has_protect or band == "STRONG":
        return "WEALTH_PROMISED", "STRONG"
    return "STABLE", band


def _affected_areas(top_planets: List[Dict[str, Any]]) -> List[str]:
    seen: List[str] = []
    for p in top_planets[:5]:
        for a in p.get("significations", []):
            if a not in seen:
                seen.append(a)
    return seen[:6]


def _gap_ok(cand: Dict[str, Any], chosen: List[Dict[str, Any]]) -> bool:
    for c in chosen:
        gap = abs((cand["start"] - c["start"]).days)
        if gap < _MIN_WINDOW_GAP_DAYS:
            return False
    return True


def _select_top_3(scored: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chosen: List[Dict[str, Any]] = []
    for w in scored:
        if _gap_ok(w, chosen):
            chosen.append(w)
        if len(chosen) >= 3:
            break
    return chosen


def _format_window(start: datetime, end: datetime) -> str:
    return f"{start.strftime('%b %Y')} → {end.strftime('%b %Y')}"


def _data_sufficiency(kundli: dict, kp: dict) -> Tuple[bool, List[str]]:
    notes: List[str] = []
    ok = True
    if not kundli.get("planets"):
        notes.append("MISSING planets list")
        ok = False
    if not kundli.get("dashas"):
        notes.append("MISSING dasha chain")
    if not kp:
        notes.append("MISSING KP layer (KP weights default to flat)")
    return ok, notes


# ════════════════════════════════════════════════════════════════════════
# Public entry point
# ════════════════════════════════════════════════════════════════════════
def compute_finance_window(kundli: dict, intel: Optional[dict] = None,
                            kp: Optional[dict] = None,
                            birth: Optional[Any] = None) -> dict:
    """Run the full 9-step Finance Timing Engine v1 pipeline.

    Single-exit wrapper that GUARANTEES the thread-local cache is reset
    at entry and populated on EVERY exit path (early-return UNKNOWN
    gates and exceptions). Mirror of `compute_health_window`.
    """
    clear_last_finance_result()
    result: Dict[str, Any]
    try:
        result = _compute_finance_window_impl(kundli, intel, kp, birth)
    except Exception as exc:  # noqa: BLE001
        result = {
            "verdict": "UNKNOWN", "band": "WEAK",
            "factors": [f"ENGINE_EXCEPTION {type(exc).__name__}: {str(exc)[:160]}"],
            "risk_flags": ["ENGINE_EXCEPTION"],
            "engine_version": "v1.0.0",
            "engine_arch": "FILTER→VERIFY→ACTIVATE→TRIGGER",
        }
    _store_last_result(result)
    return result


def _compute_finance_window_impl(kundli: dict,
                                   intel: Optional[dict] = None,
                                   kp: Optional[dict] = None,
                                   birth: Optional[Any] = None) -> dict:
    """Inner implementation — see `compute_finance_window` for contract."""
    if not isinstance(kundli, dict) or not kundli:
        return {"verdict": "UNKNOWN", "band": "WEAK",
                "factors": ["GATE kundli empty"],
                "engine_version": "v1.0.0",
                "engine_arch": "FILTER→VERIFY→ACTIVATE→TRIGGER"}
    kp = kp or kundli.get("kp") or {}
    intel = intel or {}

    # Resolve lagna
    asc = kundli.get("ascendant")
    lagna_si = _sign_idx(asc) if isinstance(asc, str) else None
    if lagna_si is None:
        for key in ("lagnaSign", "ascendant_sign", "ascendantSign"):
            v = kundli.get(key)
            if isinstance(v, str):
                lagna_si = _sign_idx(v)
            elif isinstance(v, int):
                lagna_si = v % 12
            if lagna_si is not None:
                break
    if lagna_si is None:
        return {"verdict": "UNKNOWN", "band": "WEAK",
                "factors": ["GATE lagna_si is None"],
                "engine_version": "v1.0.0",
                "engine_arch": "FILTER→VERIFY→ACTIVATE→TRIGGER"}

    ok, reasons = _data_sufficiency(kundli, kp)
    factors: List[str] = []
    if reasons:
        factors.append(f"DATA_NOTES {reasons}")
    if not ok:
        return {"verdict": "UNKNOWN", "band": "WEAK",
                "risk_flags": reasons, "factors": factors,
                "engine_version": "v1.0.0",
                "engine_arch": "FILTER→VERIFY→ACTIVATE→TRIGGER"}

    now = datetime.utcnow()
    birth_dt = _parse_dob_dt(birth, kundli=kundli)
    age = _compute_age(birth_dt, now)
    factors.append(f"AGE user_age={age} lagna={_SIGNS[lagna_si]}")

    # ── STEP 1 ──
    d1_map = _step1_d1_filter(kundli, lagna_si)
    survivors = {p for p, info in d1_map.items() if info["in_filter"]}
    factors.append(f"STEP1 survivors={sorted(survivors)}")

    # ── STEP 2 ──
    d9_scores = _step2_d9_verify(kundli, survivors)
    factors.append(f"STEP2 D9_scores=" +
                    ",".join(f"{p}:{s:.1f}" for p, s in d9_scores.items()))

    # ── STEP 3 ──
    d2_scores = _step3_d2_hora(kundli, survivors)
    factors.append(f"STEP3 D2_Hora=" +
                    ",".join(f"{p}:{s:.1f}" for p, s in d2_scores.items()))

    # ── STEP 3.5 — KP layer ──
    kp_layer = _step3_5_kp_layer(kp, lagna_si)
    factors.append(f"STEP3.5 KP csl_2={kp_layer['csl_2']}/{kp_layer['verdict_2']} "
                    f"csl_11={kp_layer['csl_11']}/{kp_layer['verdict_11']}")

    # ── STEP 4 — Weighted ranking ──
    ranked = _step4_rank(d1_map, d9_scores, d2_scores, kp, lagna_si)
    factors.append("STEP4 ranked=" +
                    ",".join(f"{r['name']}:{r['score']}" for r in ranked[:5]))

    # ── STEP 5 — Dasha activation ──
    chain = _flatten_dasha_chain(kundli)
    dasha_windows = _step5_dasha_activation(chain, ranked, lagna_si, now)
    factors.append(f"STEP5 dasha_windows_in_horizon={len(dasha_windows)}")

    # ── STEP 6 — Transits ──
    planets_d1 = kundli.get("planets") or []
    transits = _step6_transits(kundli, lagna_si, planets_d1, now)
    transit_load = sum(w for _, _, w in transits.get("active_triggers", []))
    factors.append(f"STEP6 transit_load={transit_load:.2f}")

    # ── STEP 7 — Ashtakavarga ──
    ashta = _step7_ashtakavarga(kundli, lagna_si)
    factors.append(f"STEP7 SAV_2={ashta['sav_2']} SAV_11={ashta['sav_11']} "
                    f"band={ashta['wealth_band']}")

    # ── STEP 9 — Yogas ──
    yogas = _detect_yogas(kundli, lagna_si, planets_d1)
    factors.append(f"STEP9 yogas={[y['name'] for y in yogas]}")

    # ── Window selection + severity ──
    top3 = _select_top_3(dasha_windows)
    formatted_top3: List[Dict[str, Any]] = []
    confirmations_severe = 0
    for w in top3:
        sev = _severity_of_window(w["score"], transit_load)
        if sev == "consult":
            confirmations_severe += 1
        formatted_top3.append({
            "md": w["md"], "ad": w["ad"], "pd": w["pd"],
            "score": w["score"], "severity": sev,
            "window": _format_window(w["start"], w["end"]),
            "start_iso": w["start"].isoformat(),
            "end_iso": w["end"].isoformat(),
            "triggers": w["triggers"],
        })

    # Current window = active dasha now
    current = next((w for w in dasha_windows
                     if w["start"] <= now <= w["end"]), None)
    current_window = None
    if current:
        sev = _severity_of_window(current["score"], transit_load)
        current_window = {
            "md": current["md"], "ad": current["ad"], "pd": current["pd"],
            "start_iso": current["start"].isoformat(),
            "end_iso": current["end"].isoformat(),
            "severity": sev,
            "triggers": current["triggers"],
        }

    # Protection windows = upcoming where Jupiter/Venus/Lagna-lord rules
    lagna_lord = _house_lord(lagna_si, 1)
    benefics = {"Jupiter", "Venus", lagna_lord}
    protection_windows = []
    for w in dasha_windows[:30]:
        if w["ad"] in benefics or w["pd"] in benefics:
            if any(y.get("severity") == "high" for y in yogas):
                continue
            protection_windows.append({
                "md": w["md"], "ad": w["ad"], "pd": w["pd"],
                "window": _format_window(w["start"], w["end"]),
                "start_iso": w["start"].isoformat(),
                "end_iso": w["end"].isoformat(),
            })
        if len(protection_windows) >= 3:
            break

    # Verdict + tier
    top_score = formatted_top3[0]["score"] if formatted_top3 else 0.0
    verdict, band = _derive_verdict(top_score, ashta["wealth_band"],
                                       yogas, transit_load)
    severity_now = (current_window["severity"]
                     if current_window else "supportive")
    rec_tier = _recommendation_tier(severity_now, confirmations_severe, age)
    # Consistency rule (architect-fix May 7 2026): a HIGH_LEAK verdict
    # MUST surface as `consult` tier so the LLM/UI side can't accidentally
    # downgrade the warning.
    if verdict == "HIGH_LEAK_WINDOW":
        rec_tier = "consult"

    # LLM directives (ALWAYS include the financial disclaimer + investment
    # advice guard — per replit.md user policy)
    llm_directives = ["FINANCIAL_DISCLAIMER",
                       "NOT_INVESTMENT_ADVICE",
                       "NO_GUARANTEED_WEALTH",
                       "NO_GUARANTEED_LOSS",
                       f"SEVERITY_TIER:{rec_tier}"]
    if confirmations_severe >= _CONFIRMATIONS_FOR_CONSULT:
        llm_directives.append("CONSULT_TIER")
    llm_directives.append("NO_STOCK_TICKER_NAMING")

    # Risk flags
    risk_flags: List[str] = []
    if ashta["wealth_band"] == "WEAK":
        risk_flags.append("LOW_SAV_WEALTH_BAND")
    if any(y.get("severity") == "high" for y in yogas):
        risk_flags.append("DARIDRA_OR_KEMADRUMA_YOGA")
    if transit_load >= 1.5:
        risk_flags.append("HEAVY_TRANSIT_LOAD")
    if kp_layer.get("verdict_2") == "INCOME_BLOCKED":
        risk_flags.append("KP_2CSL_DUSTHANA")
    if kp_layer.get("verdict_11") == "GAINS_BLOCKED":
        risk_flags.append("KP_11CSL_DUSTHANA")

    # Weighted breakdown (engine audit)
    breakdown = {
        r["name"]: {"d1": r["d1"], "d9": r["d9"], "d2": r["d2"],
                     "kp": r["kp"], "karaka": r["karaka"],
                     "total": r["score"]}
        for r in ranked
    }

    affected = _affected_areas(ranked)
    remedies = _compute_finance_remedies(ranked, affected, rec_tier)
    return {
        "verdict": verdict,
        "band": band,
        "current_window": current_window,
        "next_3_windows": formatted_top3,
        "protection_windows": protection_windows,
        "affected_areas": affected,
        "recommendation_tier": rec_tier,
        "top_finance_planets": ranked[:5],
        "weighted_breakdown": breakdown,
        "kp_layer": kp_layer,
        "transits": transits,
        "ashtakavarga": ashta,
        "yogas": yogas,
        "risk_flags": risk_flags,
        "factors": factors,
        "llm_directives": llm_directives,
        "remedies": remedies,
        "engine_version": "v1.0.0",
        "engine_arch": "FILTER→VERIFY→ACTIVATE→TRIGGER",
    }


# ════════════════════════════════════════════════════════════════════════
# Remedy delegation — money topic (Remedy Engine v1.1)
# ════════════════════════════════════════════════════════════════════════
def _compute_finance_remedies(ranked: Optional[List[Dict[str, Any]]],
                                affected_areas: Optional[List[str]],
                                recommendation_tier: Optional[str]
                                ) -> Dict[str, Any]:
    """DELEGATES to standalone Remedy Engine v1.1 (money topic).

    Money-topic severity tiers in remedy engine:
      watchful / supportive / celebratory / consult — exactly what
      `_recommendation_tier()` emits, so no remap needed.
    """
    try:
        from remedy import get_remedies  # type: ignore
    except Exception:
        return {}
    return get_remedies(
        topic    = "money",
        planets  = ranked or [],
        areas    = affected_areas or [],
        severity = recommendation_tier,
        user_facts    = None,
        duration_days = 21,
    )

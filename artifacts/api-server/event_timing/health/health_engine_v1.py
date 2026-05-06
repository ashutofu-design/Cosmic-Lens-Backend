"""
event_timing/health/health_engine_v1.py
========================================
COSMIC LENS HEALTH TIMING ENGINE v1.0 — clean build, mirrors Marriage v2.4.

Architecture: FILTER → VERIFY → ACTIVATE → TRIGGER (9-step pipeline,
locked by user spec May 6 2026).

  STEP 1   D1 health-significator filter             (FILTER)
           - 1L/6L/8L/12L + 2L/7L marakas
           - Occupants of 6th/8th/12th houses
           - Planets ASPECTING the 6th house
  STEP 2   D9 dignity verification                   (VERIFY)
  STEP 3   D30 (Trimshamsa) disease verification     (VERIFY)
           Parashara: D30 is THE disease/misfortune chart.
  STEP 4   Weighted ranking
           D1·30 + D9·20 + D30·25 + KP·15 + karaka·10
  STEP 5   Dasha activation (AD/PD primary; MD low-weight)
           AD=5, PD=6, MD=1  (per user spec: AD/PD lead, MD background)
  STEP 6   Transit triggers
           Saturn over 1/6/8, Rahu/Ketu over Lagna or Moon,
           Mars over 6/8 (acute), Jupiter over 6 (protective),
           Sade Sati phase
  STEP 7   Ashtakavarga support
           SAV bindus on Lagna (<25 = weak vitality)
           SAV bindus on 6th  (high = better disease-fighting)
  STEP 8   KP cuspal sub lord of 6th & 8th houses
  STEP 9   Yoga + hard-guard layer
           Arishta / Balarishta / Papakartari / age-floor
           (CAFB-health post-injectors stay authoritative for output)

Public function:
  compute_health_window(kundli, intel, kp, birth) -> dict

Output dict (back-compat with marriage-style consumers):
  {
    "verdict":              "STRONG_VITALITY" | "STABLE" | "VULNERABLE" |
                            "HIGH_RISK_WINDOW" | "UNKNOWN",
    "band":                 "WEAK" | "MEDIUM" | "STRONG",
    "current_window":       {start_iso, end_iso, severity, triggers[]},
    "next_3_windows":       [{md, ad, pd, score, severity, window,
                              start_iso, end_iso}],
    "protection_windows":   [{md, ad, pd, window, start_iso, end_iso}],
    "affected_systems":     ["digestive", "respiratory", ...],
    "recommendation_tier":  "monitor" | "preventive" | "consult" |
                            "urgent_consult",
    "top_health_planets":   [{name, score, d1, d9, d30, kp, karaka,
                               significations[]}],
    "weighted_breakdown":   {planet: {d1, d9, d30, kp, karaka, total}},
    "kp_layer":             {csl_6, csl_8, verdict_6, verdict_8},
    "transits":             {saturn, rahu, ketu, mars, jupiter, sade_sati},
    "ashtakavarga":         {sav_lagna, sav_6, vitality_band},
    "yogas":                [{name, severity, planets}],
    "risk_flags":           [str],
    "factors":              [str],   # full audit trail
    "llm_directives":       [str],   # MEDICAL_DISCLAIMER, AGE_GUARD, etc
    "engine_version":       "v1.0.0",
    "engine_arch":          "FILTER→VERIFY→ACTIVATE→TRIGGER",
  }

Hard guards reused from CAFB-health (`health_focus_routing.py`):
  - No death/lifespan prediction below age 25
  - 3-confirmation rule for `urgent_consult` tier
  - Mandatory medical disclaimer post-injector
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

# ── Thread-local cache for the most recent engine result. Used by the
# post-injector pipeline (`health_focus_routing.apply_health_postinjectors`)
# to enforce verbatim verdict citation without recomputing the engine.
# Keyed per-request via Python's threading.local because the Flask app
# uses a per-request worker thread; the cache is reset on every fresh
# `compute_health_window()` call so stale values cannot leak across
# requests.
_LAST_RESULT = threading.local()


# ════════════════════════════════════════════════════════════════════════
# HEALTH REMEDIES — deterministic, classical-source consensus
# ════════════════════════════════════════════════════════════════════════
# BPHS / Phaladeepika / Lal-Kitab consensus + Charaka/Sushruta lifestyle
# (for affected-system layer). Per user policy: every entry MUST carry
# (a) a FREE alternative, (b) a PAID/gemstone option with caveat, and
# (c) the universal "remedies SUPPLEMENT, never substitute action +
# qualified doctor" disclaimer (added by locked_facts + post-injector).
#
# Format kept tight so the LLM cites verbatim under Rule M
# (anti-hallucination remedy quoting). Mantras use Sanskrit with
# Hinglish transliteration for accessibility.

_HEALTH_REMEDIES_BY_PLANET: Dict[str, Dict[str, str]] = {
    "Sun": {
        "day":         "Sunday",
        "mantra":      "Om Hraam Hreem Hraum Sah Suryaya Namah",
        "count":       "108",
        "free":        "Surya namaskar 12 rounds at sunrise + Aditya Hridaya Stotra path",
        "paid":        "Manik (Ruby) 3-5 ct, copper, ring finger — astrologer-fitted",
        "donation":    "Wheat + jaggery to a temple Sunday morning",
        "for_systems": "heart, eyes, vitality, bones",
    },
    "Moon": {
        "day":         "Monday",
        "mantra":      "Om Som Somaya Namah",
        "count":       "108",
        "free":        "Chandra namaskar at moonrise + Shiva Panchakshari japa; cool head water-bath",
        "paid":        "Moti (Pearl) 4-6 ct, silver, ring finger — astrologer-fitted",
        "donation":    "Milk + white rice + white cloth to a needy person Monday",
        "for_systems": "mind, sleep, fluids, digestion, mother",
    },
    "Mars": {
        "day":         "Tuesday",
        "mantra":      "Om Ang Angarakaya Namah",
        "count":       "108",
        "free":        "Hanuman Chalisa daily + Mangal-stotra Tuesday; avoid red meat & spicy on Tuesday",
        "paid":        "Moonga (Red Coral) 6-8 ct, copper, ring finger — TRIAL 3 days first",
        "donation":    "Red lentils (masoor) + red cloth Tuesday",
        "for_systems": "blood, muscles, inflammation, accident-risk, surgery",
    },
    "Mercury": {
        "day":         "Wednesday",
        "mantra":      "Om Bum Budhaya Namah",
        "count":       "108",
        "free":        "Vishnu Sahasranama path + green moong / amla in diet daily",
        "paid":        "Panna (Emerald) 4-6 ct, gold, little finger — TRIAL 3 days first",
        "donation":    "Green moong + green cloth + camphor at a Vishnu temple Wednesday",
        "for_systems": "skin, nervous system, speech, lungs, intellect",
    },
    "Jupiter": {
        "day":         "Thursday",
        "mantra":      "Om Brim Brihaspataye Namah",
        "count":       "108",
        "free":        "Vishnu Sahasranama or Guru-stotra Thursday + turmeric milk at night",
        "paid":        "Pukhraj (Yellow Sapphire) 4-6 ct, gold, index finger — generally safe but get astrologer fit",
        "donation":    "Chana dal + turmeric + yellow cloth Thursday",
        "for_systems": "liver, pancreas, fat metabolism, immunity",
    },
    "Venus": {
        "day":         "Friday",
        "mantra":      "Om Shum Shukraya Namah",
        "count":       "108",
        "free":        "Lakshmi-stotra Friday + cow ghee in food + clean white clothes Friday",
        "paid":        "Heera (Diamond) 0.5-1 ct OR Opal 4-6 ct, silver, middle finger — TRIAL first",
        "donation":    "White sweets + curd + white cloth to a girl Friday",
        "for_systems": "kidneys, reproductive, hormones, eyes, throat",
    },
    "Saturn": {
        "day":         "Saturday",
        "mantra":      "Om Sham Shanaishcharaya Namah",
        "count":       "108",
        "free":        "Hanuman Chalisa Saturday + Shani-stotra + sesame-oil massage; serve elderly",
        "paid":        "Neelam (Blue Sapphire) 4-6 ct, silver/panchdhatu, middle finger — STRICT 3-day TRIAL first; suits don't suit varies sharply",
        "donation":    "Mustard oil + black urad + black cloth + iron at Shani temple Saturday",
        "for_systems": "joints, bones, chronic conditions, teeth, knees, longevity",
    },
    "Rahu": {
        "day":         "Saturday (or Wednesday)",
        "mantra":      "Om Bhram Bhrim Bhraum Sah Rahave Namah",
        "count":       "108",
        "free":        "Durga Saptashati or Bhairav-stotra + avoid taamasic food + keep silver under pillow",
        "paid":        "Gomed (Hessonite) 5-7 ct, silver, middle finger — TRIAL first",
        "donation":    "Black urad + black cloth + coconut Saturday",
        "for_systems": "anxiety, sudden ailments, skin allergies, addiction, mystery diagnoses",
    },
    "Ketu": {
        "day":         "Tuesday (or Saturday)",
        "mantra":      "Om Sram Srim Sraum Sah Ketave Namah",
        "count":       "108",
        "free":        "Ganesh Atharvashirsha + til (sesame) daan + spiritual sadhana / silence",
        "paid":        "Lehsunia (Cat's Eye) 5-7 ct, silver, middle finger — TRIAL first",
        "donation":    "Sesame seeds + multi-coloured cloth + blanket Saturday",
        "for_systems": "auto-immune, infections, mysterious/idiopathic, spine, eyes",
    },
}

# Lifestyle / Ayurveda / pranayama practices keyed by affected-system tag
# from `_affected_systems()`. Used as a SECOND remedy layer so the user
# gets actionable habits, not just mantra+gemstone.
_HEALTH_PRACTICES_BY_SYSTEM: Dict[str, str] = {
    "heart":            "Anulom-vilom 10 min/day + walking 30 min + reduce salt/saturated fat",
    "eyes":             "Trataka (candle gaze) 5 min + screen breaks 20-20-20 rule + triphala water eye-wash",
    "vitality":         "Surya namaskar + ashwagandha (consult vaidya for dose) + 7-8 hr sleep",
    "bones":            "Calcium-rich diet (sesame, ragi) + sun exposure 15 min morning + weight-bearing exercise",
    "mind":             "Bhramari pranayama 10 rounds + 10-min meditation + reduce caffeine",
    "sleep":            "Brahmi/jatamansi at night (vaidya consult) + screen off 1 hr before bed + warm milk",
    "fluids":           "Adequate water (per body) + jeera-saunf-ajwain water + reduce cold drinks",
    "digestion":        "Triphala at night + ginger before meals + eat sitting, slowly",
    "blood":            "Anar/beetroot juice + tulsi water + iron-rich greens (palak, methi)",
    "muscles":          "Light yoga + ashwagandha + warm sesame oil massage twice a week",
    "inflammation":     "Turmeric-pepper-warm-water + omega-3 (flax/walnut) + reduce sugar+maida",
    "accident_risk":    "Hanuman Chalisa daily + Mahamrityunjaya 11x + extra mindfulness driving/sharp tools",
    "liver":            "Bhastrika pranayama + bitter greens (karela, methi) + skip alcohol completely",
    "skin":             "Neem-tulsi water bath + amla daily + reduce night-out fried/oily",
    "nervous":          "Brahmi + abhyanga (oil massage) 2x/week + nadi shodhana pranayama",
    "kidneys":          "Adequate hydration + reduce salt + coriander seed water",
    "reproductive":     "Shatavari (women) / ashwagandha (men) — vaidya consult; pelvic yoga",
    "joints":           "Light weight-bearing + Vata-pacifying diet (warm, oily, cooked) + Mahanarayan oil massage",
    "chronic":          "Same daily routine (dincharya) + Mahamrityunjaya jaap + slow consistent recovery; no shortcuts",
    "anxiety":          "Bhramari + Sheetali pranayama + reduce social-media + grounding walks barefoot on grass",
    "auto-immune":      "Anti-inflammatory diet + stress management + qualified physician monitoring (do NOT self-medicate)",
}


_VALID_TIERS = ("monitor", "preventive", "consult", "urgent_consult")


def _compute_health_remedies(ranked: Optional[List[Dict[str, Any]]],
                              affected_systems: Optional[List[str]],
                              recommendation_tier: Optional[str]) -> Dict[str, Any]:
    """DELEGATES to standalone Remedy Engine v1.0 (May 6 2026).

    Migrated from inline `_HEALTH_REMEDIES_BY_PLANET` /
    `_HEALTH_PRACTICES_BY_SYSTEM` tables to the unified hybrid 3-tier
    engine at `remedy/remedy_engine_v1.py`. The legacy inline tables are
    kept above for back-compat reference but are NO LONGER consulted.

    The new engine returns a richer block (practical/ayurvedic/vedic per
    planet, KPI, cost, conflicts, stack, substitutions) — see
    `remedy.get_remedies` docstring. The shape is a superset of the old
    one, so downstream consumers reading `planet_remedies` / `system_practices`
    / `universal_disclaimer` / `tier_note` continue to work; new fields
    (`stack`, `conflicts`, `doctor_referral_hint`, etc) are additive.
    """
    from remedy import get_remedies  # type: ignore
    return get_remedies(
        topic    = "health",
        planets  = ranked or [],
        areas    = affected_systems or [],
        severity = recommendation_tier,
        # UCML hooks intentionally None here — locked_facts can re-call
        # with user_facts when they're available in that context. Engine
        # output stored on _LAST_RESULT remains the basic personalisation-
        # free result.
        user_facts    = None,
        duration_days = 21,
    )


def get_last_health_result() -> Optional[Dict[str, Any]]:
    """Return the engine result from the most recent `compute_health_window`
    call on this thread, or None if none has run yet (or it was cleared).
    """
    return getattr(_LAST_RESULT, "value", None)


def _store_last_result(result: Dict[str, Any]) -> None:
    _LAST_RESULT.value = result


def clear_last_health_result() -> None:
    """Explicit reset between requests (defensive)."""
    if hasattr(_LAST_RESULT, "value"):
        _LAST_RESULT.value = None

# ── External helpers (graceful degradation if unavailable) ──
try:
    from divisional_charts import compute_d9  # type: ignore
except Exception:
    compute_d9 = None  # type: ignore

try:
    from divisional_charts import compute_d30  # type: ignore
except Exception:
    compute_d30 = None  # type: ignore

try:
    from ashtakavarga import compute_ashtakavarga  # type: ignore
except Exception:
    compute_ashtakavarga = None  # type: ignore

try:
    from pratyantar import compute_pratyantar  # type: ignore
except Exception:
    compute_pratyantar = None  # type: ignore

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

# Health-significant houses (per user spec)
_DUSTHANA  = [6, 8, 12]            # disease/chronic/hospitalization
_VITALITY  = [1]                   # body strength
_MARAKA    = [2, 7]                # life-end markers (low weight, age-gated)

# Health-significator weights (Step 4)
_WEIGHT_D1     = 0.30
_WEIGHT_D9     = 0.20
_WEIGHT_D30    = 0.25
_WEIGHT_KP     = 0.15
_WEIGHT_KARAKA = 0.10

# Dasha scores (per user spec: AD/PD lead, MD background)
_DASHA_SCORE_MD = 1
_DASHA_SCORE_AD = 5
_DASHA_SCORE_PD = 6

# Step 1 D1 acceptance threshold (planets below this filtered out)
_D1_FILTER_MIN_SCORE = 12.0

# Window selection
_MIN_WINDOW_GAP_DAYS = 45

# Ashtakavarga vitality bands (SAV bindus on Lagna)
_SAV_LAGNA_WEAK   = 25
_SAV_LAGNA_STRONG = 32

# 3-confirmation rule for severe tier
_CONFIRMATIONS_FOR_URGENT = 3

# Age floor: no death/lifespan prediction below this age
_DEATH_PREDICTION_MIN_AGE = 25

# Vimshottari standard
_VIMS_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
                "Jupiter", "Saturn", "Mercury"]
_VIMS_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
                "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}

_PLANETS_9 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
               "Saturn", "Rahu", "Ketu"]

# Body-system signification per planet (used for `affected_systems`)
_SYSTEM_OF_PLANET: Dict[str, List[str]] = {
    "Sun":     ["cardio", "musculoskeletal_bones", "vitality", "eyes_right"],
    "Moon":    ["mind", "fluids_blood", "digestive", "eyes_left"],
    "Mars":    ["blood", "muscles", "inflammation", "accident_risk"],
    "Mercury": ["nervous", "skin", "respiratory_speech", "anxiety"],
    "Jupiter": ["liver", "endocrine_metabolism", "fat_diabetes"],
    "Venus":   ["reproductive", "kidney_urinary", "throat", "endocrine"],
    "Saturn":  ["musculoskeletal_joints", "chronic", "depression",
                "respiratory_lungs"],
    "Rahu":    ["undiagnosed", "allergies", "addictions", "skin_mysterious"],
    "Ketu":    ["viral_sudden", "parasites", "scars_surgery", "nervous_obscure"],
}

# Functional malefics by lagna sign (classical Parashari)
# Using simplified consensus list — planets that "do harm" for that lagna.
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
# Low-level helpers (lifted/aligned with marriage_engine_v2 conventions)
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
    """Does `aspector` (sitting in `ap_house`) drishti the `target_house`?
    Standard Parashari aspects: all planets aspect 7th. Mars adds 4,8.
    Jupiter adds 5,9. Saturn adds 3,10. Rahu/Ketu treated like Saturn-style
    (3,7,10) per common KP convention.
    """
    if not (1 <= ap_house <= 12 and 1 <= target_house <= 12):
        return False
    diff = ((target_house - ap_house) % 12) + 1   # 1..12
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
# STEP 1 — D1 health-significator filter
# ════════════════════════════════════════════════════════════════════════
def _step1_d1_filter(kundli: dict, lagna_si: int,
                       user_age: Optional[int] = None
                       ) -> Dict[str, Dict[str, Any]]:
    """Identify health-significant planets in D1.

    Inclusion (per user spec line-by-line):
      • Lagna lord (1L)              — vitality
      • 6L, 8L, 12L                  — disease/chronic/hospitalization
      • 2L, 7L                       — marakas (low weight, age-gated)
      • Occupants of 6/8/12          — direct disease links
      • Planets aspecting the 6th    — disease activation
      • Sun/Moon/Mars/Saturn         — primary health karakas (always considered)

    Each candidate gets a base score; planets above _D1_FILTER_MIN_SCORE
    survive to STEP 2.
    """
    planets = kundli.get("planets") or []
    out: Dict[str, Dict[str, Any]] = {}
    for p in _PLANETS_9:
        out[p] = {"d1": 0.0, "in_filter": False, "links": [],
                   "is_lord_of": [], "occupies": None,
                   "aspects_6": False}

    # Lordship checks
    for h in _VITALITY + _DUSTHANA + _MARAKA:
        lord = _house_lord(lagna_si, h)
        out[lord]["is_lord_of"].append(h)
        if h in _VITALITY:
            out[lord]["d1"] += 18.0
            out[lord]["links"].append(f"Lagna lord (vitality)")
        elif h == 6:
            out[lord]["d1"] += 16.0
            out[lord]["links"].append("6L (disease)")
        elif h == 8:
            out[lord]["d1"] += 18.0
            out[lord]["links"].append("8L (chronic/longevity)")
        elif h == 12:
            out[lord]["d1"] += 14.0
            out[lord]["links"].append("12L (hospitalization)")
        elif h in _MARAKA:
            # Maraka activates only at advanced age (≥55). Below that,
            # 2L/7L should not inflate health-risk scoring (a 30-yr-old
            # whose 2L lights up next month is NOT in a maraka window).
            if user_age is not None and user_age >= 55:
                out[lord]["d1"] += 6.0
                out[lord]["links"].append(f"{h}L (maraka, age-gated)")
            else:
                out[lord]["links"].append(
                    f"{h}L (maraka, dormant — age<55 or unknown)")

    # Occupants of 6/8/12
    for h in _DUSTHANA:
        for pname in _planets_in_house(planets, h):
            out[pname]["occupies"] = h
            bump = {6: 12.0, 8: 14.0, 12: 10.0}[h]
            out[pname]["d1"] += bump
            out[pname]["links"].append(f"occupies {h}H")

    # Planets ASPECTING the 6th house (per user spec)
    for pname in _PLANETS_9:
        ap_house = _planet_house(planets, pname)
        if ap_house and _aspects_house(pname, ap_house, 6):
            out[pname]["aspects_6"] = True
            out[pname]["d1"] += 8.0
            out[pname]["links"].append("aspects 6H")

    # Primary health karakas — always considered (small bonus so they survive)
    for karaka, bonus, role in (
        ("Sun",    6.0, "vitality karaka"),
        ("Moon",   6.0, "mind/blood karaka"),
        ("Mars",   8.0, "blood/accident karaka"),
        ("Saturn", 8.0, "chronic/longevity karaka"),
    ):
        out[karaka]["d1"] += bonus
        out[karaka]["links"].append(role)

    # Functional malefic surcharge for lagna
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
    delivers its health karma cleanly; debilitated → muddled/disrupted.
    Score range 0-25.
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
        # graceful fallback: small flat score
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
# STEP 3 — D30 (Trimshamsa) disease verification
# ════════════════════════════════════════════════════════════════════════
def _step3_d30_verify(kundli: dict, lagna_si: int,
                       candidates: Set[str]) -> Dict[str, float]:
    """D30 (Trimshamsa) is Parashara's dedicated disease/misfortune chart.
    A planet placed in 6/8/12 of D30 is a confirmed disease significator.
    Score range 0-25.
    """
    out: Dict[str, float] = {p: 0.0 for p in candidates}
    if not candidates:
        return out
    d30 = None
    if compute_d30 is not None:
        try:
            d30 = compute_d30(kundli)
        except Exception:
            d30 = None
    if not d30:
        return {p: 8.0 for p in candidates}
    d30_planets = d30.get("planets") if isinstance(d30, dict) else None
    d30_lagna = (d30.get("ascendantSign") or d30.get("ascendant")
                 if isinstance(d30, dict) else None)
    d30_lagna_si = _sign_idx(d30_lagna) if d30_lagna else lagna_si
    if not d30_planets or d30_lagna_si is None:
        return {p: 8.0 for p in candidates}
    for pname in candidates:
        si = _planet_sign_idx(d30_planets, pname)
        if si is None:
            out[pname] = 8.0
            continue
        h = _house_of_sign(si, d30_lagna_si)
        if h in _DUSTHANA:
            out[pname] = 22.0      # confirmed disease significator
        elif h in (1, 4, 7, 10):
            out[pname] = 6.0       # kendras = stable
        elif h in (5, 9):
            out[pname] = 4.0       # trikona = protective
        else:
            out[pname] = 10.0
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 3.5 — KP layer (cuspal sub lord of 6th & 8th)
# ════════════════════════════════════════════════════════════════════════
def _step3_5_kp_layer(kp: dict, lagna_si: int) -> Dict[str, Any]:
    """KP cuspal sub lord of 6th & 8th cusps.
    Verdict rules (KP standard for health):
      6 CSL signifies 6/8/12 → illness yes
      6 CSL signifies 1/5/11 → recovery / good immunity
      8 CSL signifies 6/8/12 → chronic/surgery yes
      8 CSL signifies 1/5/11 → chronic risk low
    """
    out = {"csl_6": None, "csl_8": None,
           "verdict_6": "UNKNOWN", "verdict_8": "UNKNOWN",
           "csl_6_signifies": [], "csl_8_signifies": []}
    if not kp:
        return out
    c6 = _kp_cusp(kp, 6)
    c8 = _kp_cusp(kp, 8)
    if c6:
        csl = c6.get("sl") or c6.get("subLord") or c6.get("sub_lord")
        out["csl_6"] = csl
        if csl:
            sig = _planet_signified_houses(kp, csl)
            out["csl_6_signifies"] = sig
            if any(h in _DUSTHANA for h in sig):
                out["verdict_6"] = "ILLNESS_YES"
            elif any(h in (1, 5, 11) for h in sig):
                out["verdict_6"] = "ILLNESS_NO"
            else:
                out["verdict_6"] = "NEUTRAL"
    if c8:
        csl = c8.get("sl") or c8.get("subLord") or c8.get("sub_lord")
        out["csl_8"] = csl
        if csl:
            sig = _planet_signified_houses(kp, csl)
            out["csl_8_signifies"] = sig
            if any(h in _DUSTHANA for h in sig):
                out["verdict_8"] = "CHRONIC_YES"
            elif any(h in (1, 5, 11) for h in sig):
                out["verdict_8"] = "CHRONIC_NO"
            else:
                out["verdict_8"] = "NEUTRAL"
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 4 — Weighted ranking
# ════════════════════════════════════════════════════════════════════════
def _karaka_score(pname: str, lagna_si: int) -> float:
    """Health-karaka score (0-10)."""
    base = {"Sun": 6.0, "Moon": 5.0, "Mars": 7.0, "Saturn": 8.0,
            "Mercury": 4.0, "Jupiter": 5.0, "Venus": 4.0,
            "Rahu": 5.0, "Ketu": 5.0}.get(pname, 0.0)
    # Functional benefic boost
    if pname in _FUNC_BENEFICS.get(lagna_si, set()):
        base += 2.0
    return min(10.0, base)


def _step4_rank(d1_map: Dict[str, Dict[str, Any]],
                d9_scores: Dict[str, float],
                d30_scores: Dict[str, float],
                kp: dict, lagna_si: int) -> List[Dict[str, Any]]:
    """Rank surviving candidates by weighted score.
    Score = D1·30% + D9·20% + D30·25% + KP·15% + Karaka·10%
    All sub-scores normalized to 0-25 first.

    D1 normalization (architect fix): true min-max scale to 0-25 so
    different high-D1 planets don't collapse to the same clipped value.
    """
    survivors = [p for p, info in d1_map.items() if info.get("in_filter")]
    if not survivors:
        return []
    raw_d1 = {p: d1_map[p]["d1"] for p in survivors}
    max_d1 = max(raw_d1.values()) or 1.0
    ranked: List[Dict[str, Any]] = []
    for pname in survivors:
        info = d1_map[pname]
        # True normalization: scale relative to the strongest candidate
        d1 = (raw_d1[pname] / max_d1) * 25.0
        d9 = d9_scores.get(pname, 8.0)
        d30 = d30_scores.get(pname, 8.0)
        # KP signification of dusthanas
        sig = _planet_signified_houses(kp, pname)
        kp_score = 0.0
        if any(h in _DUSTHANA for h in sig):
            kp_score = 18.0
        if 6 in sig:
            kp_score += 4.0
        if 8 in sig:
            kp_score += 4.0
        kp_score = min(25.0, kp_score) if kp_score > 0 else 6.0
        karaka = _karaka_score(pname, lagna_si) * 2.5  # scale to 0-25
        total = (d1 * _WEIGHT_D1 + d9 * _WEIGHT_D9 +
                 d30 * _WEIGHT_D30 + kp_score * _WEIGHT_KP +
                 karaka * _WEIGHT_KARAKA)
        ranked.append({
            "name": pname,
            "score": round(total, 2),
            "d1": round(d1, 2), "d9": round(d9, 2),
            "d30": round(d30, 2), "kp": round(kp_score, 2),
            "karaka": round(karaka, 2),
            "links": list(info["links"]),
            "significations": _SYSTEM_OF_PLANET.get(pname, []),
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
    """Tolerate multiple shapes: {lord}, {planet}, {name}, {ruler}."""
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
    """Get the next-level dasha list under any common key name."""
    for k in ("subDashas", "antardashas", "ad", "sub_dashas",
              "pratyantar", "pd", "children"):
        v = node.get(k)
        if isinstance(v, list):
            return v
    return []


def _flatten_dasha_chain(kundli: dict) -> List[Dict[str, Any]]:
    """Flatten Vimshottari MD/AD/PD chain into a list of windows.
    Tolerates multiple JSON shapes: {planet,startDate,endDate,subDashas}
    (Cosmic Lens default) AND {lord,start,end,antardashas,pratyantar}
    (legacy/marriage style).
    """
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
            # MD-only window
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
    """Score each upcoming dasha window by health-significator activation.

    AD=5, PD=6, MD=1 (per user spec — MD background, AD/PD primary).

    SIGNED contribution model (architect fix): each lord contributes
    POSITIVE risk if it is a malefic/dusthana significator, NEGATIVE
    risk (= protective relief) if it is a benefic / Lagna lord / yoga
    karaka. A Jupiter-AD over Venus-PD therefore lowers risk severity
    instead of inflating it.
    """
    if not chain or not ranked:
        return []
    score_map = {r["name"]: r["score"] for r in ranked}
    max_score = max(score_map.values()) or 1.0

    # Classify each ranked planet as risk-bearer or protector
    dusthana_lords: Set[str] = set()
    for r in ranked:
        for l in r["links"]:
            if any(tag in l for tag in
                    ("L (disease)", "L (chronic", "L (hospital",
                     "L (maraka", "occupies 6H", "occupies 8H",
                     "occupies 12H", "functional malefic")):
                dusthana_lords.add(r["name"])
                break

    lagna_lord = _house_lord(lagna_si, 1)
    func_benefics = _FUNC_BENEFICS.get(lagna_si, set())
    pure_benefics = {"Jupiter", "Venus", lagna_lord} | func_benefics

    def _sign_for(lord: str) -> int:
        """+1 = adds risk, -1 = relief (protective)."""
        if lord in dusthana_lords:
            return +1
        if lord in pure_benefics:
            return -1
        # Neutral health significator (karaka without disease lordship)
        return +1 if lord in {"Mars", "Saturn", "Rahu", "Ketu"} else 0

    horizon_end = now + timedelta(days=365 * horizon_years)
    windows: List[Dict[str, Any]] = []
    for w in chain:
        if w["end"] < now or w["start"] > horizon_end:
            continue
        risk = 0.0
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
                risk += contrib
                tag = "DUSTHANA" if lord in dusthana_lords else "MALEFIC_KARAKA"
                triggers.append(f"{role}={lord}({tag},+{contrib:.2f})")
            elif sign < 0:
                relief += contrib
                triggers.append(f"{role}={lord}(BENEFIC,-{contrib:.2f})")
            else:
                triggers.append(f"{role}={lord}(NEUTRAL,0)")
        # Net risk = risk - relief (clipped at 0)
        net = max(0.0, risk - relief)
        if net <= 0 and relief == 0:
            continue
        windows.append({
            "md": w["md"], "ad": w["ad"], "pd": w["pd"],
            "start": w["start"], "end": w["end"],
            "score": round(net, 2),
            "risk_raw": round(risk, 2),
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
    """Compute current transit triggers."""
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

    if sat_h in (1, 6, 8):
        out["saturn"] = f"Saturn transiting {sat_h}H — chronic activation"
        out["active_triggers"].append(("saturn", sat_h, 1.0))
    if rahu_h in (1, 6, 8) or (moon_si is not None and rahu_si == moon_si):
        out["rahu"] = f"Rahu transit hits Lagna/Moon/dusthana — undiagnosed/sudden"
        out["active_triggers"].append(("rahu", rahu_h, 0.9))
    if ketu_h in (1, 6, 8) or (moon_si is not None and ketu_si == moon_si):
        out["ketu"] = f"Ketu transit hits Lagna/Moon/dusthana — viral/sudden"
        out["active_triggers"].append(("ketu", ketu_h, 0.9))
    if mars_h in (6, 8):
        out["mars"] = f"Mars transit in {mars_h}H — acute fever/inflammation"
        out["active_triggers"].append(("mars", mars_h, 0.7))
    if jup_h == 6:
        out["jupiter"] = "Jupiter transit in 6H — disease-fighting protection"
        out["active_triggers"].append(("jupiter_protect", 6, -1.0))

    # Sade Sati
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
# STEP 7 — Ashtakavarga support
# ════════════════════════════════════════════════════════════════════════
def _step7_ashtakavarga(kundli: dict, lagna_si: int) -> Dict[str, Any]:
    out = {"sav_lagna": None, "sav_6": None, "vitality_band": "UNKNOWN"}
    if compute_ashtakavarga is None:
        return out
    try:
        av = compute_ashtakavarga(kundli)
    except Exception:
        return out
    if not isinstance(av, dict):
        return out
    sav = av.get("sav") or av.get("sarvashtakavarga") or {}
    # Try sign-keyed access
    lagna_sign = _SIGNS[lagna_si]
    sixth_sign = _SIGNS[(lagna_si + 5) % 12]
    sav_l = sav.get(lagna_sign) or sav.get(str(lagna_si)) or sav.get(lagna_si)
    sav_6 = sav.get(sixth_sign) or sav.get(str((lagna_si + 5) % 12)) \
            or sav.get((lagna_si + 5) % 12)
    out["sav_lagna"] = sav_l
    out["sav_6"] = sav_6
    if isinstance(sav_l, (int, float)):
        if sav_l < _SAV_LAGNA_WEAK:
            out["vitality_band"] = "WEAK"
        elif sav_l >= _SAV_LAGNA_STRONG:
            out["vitality_band"] = "STRONG"
        else:
            out["vitality_band"] = "MEDIUM"
    return out


# ════════════════════════════════════════════════════════════════════════
# STEP 9 — Yoga + hard guards
# ════════════════════════════════════════════════════════════════════════
def _detect_yogas(kundli: dict, lagna_si: int,
                   planets: List[dict]) -> List[Dict[str, Any]]:
    """Detect classical health-relevant yogas."""
    out: List[Dict[str, Any]] = []

    # Papakartari around Lagna
    h12_occ = _planets_in_house(planets, 12)
    h2_occ = _planets_in_house(planets, 2)
    malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    if (set(h12_occ) & malefics) and (set(h2_occ) & malefics):
        out.append({"name": "Papakartari (Lagna)", "severity": "moderate",
                    "planets": sorted(set(h12_occ + h2_occ) & malefics)})

    # Papakartari around Moon
    moon_h = _planet_house(planets, "Moon")
    if moon_h:
        before_h = ((moon_h - 2) % 12) + 1
        after_h = (moon_h % 12) + 1
        before_occ = _planets_in_house(planets, before_h)
        after_occ = _planets_in_house(planets, after_h)
        if (set(before_occ) & malefics) and (set(after_occ) & malefics):
            out.append({"name": "Papakartari (Moon)", "severity": "high",
                        "planets": sorted(
                            set(before_occ + after_occ) & malefics)})

    # Arishta-style: 6L OR 8L conjunct Moon in dusthana
    moon_h = _planet_house(planets, "Moon")
    if moon_h in _DUSTHANA:
        sixth_lord = _house_lord(lagna_si, 6)
        eighth_lord = _house_lord(lagna_si, 8)
        moon_co = [p for p in _planets_in_house(planets, moon_h) if p != "Moon"]
        if sixth_lord in moon_co or eighth_lord in moon_co:
            out.append({"name": "Arishta-suggestion (Moon-6L/8L conjunction in dusthana)",
                        "severity": "high",
                        "planets": ["Moon", sixth_lord, eighth_lord]})

    # Subhakartari (protective) around Lagna
    benefics_pure = {"Jupiter", "Venus", "Mercury"}
    if (set(h12_occ) & benefics_pure) and (set(h2_occ) & benefics_pure):
        out.append({"name": "Subhakartari (Lagna) — protective",
                    "severity": "protective",
                    "planets": sorted(
                        set(h12_occ + h2_occ) & benefics_pure)})

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
            "%d %b %Y", "%d %B %Y", "%d-%b-%Y", "%d-%B-%Y",
            "%b %d %Y", "%B %d %Y", "%b %d, %Y", "%B %d, %Y")
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
    age = ref.year - birth_dt.year
    if (ref.month, ref.day) < (birth_dt.month, birth_dt.day):
        age -= 1
    return max(0, age)


def _severity_of_window(score: float, transit_load: float) -> str:
    combined = score + max(0.0, transit_load)
    if combined >= 9.0:
        return "serious"
    if combined >= 6.0:
        return "moderate"
    if combined >= 3.5:
        return "mild"
    return "stable"


def _recommendation_tier(severity: str, confirmations: int,
                          age: Optional[int]) -> str:
    if severity == "serious" and confirmations >= _CONFIRMATIONS_FOR_URGENT:
        return "urgent_consult"
    if severity == "serious":
        return "consult"
    if severity == "moderate":
        return "preventive"
    return "monitor"


def _derive_verdict(top_window_score: float,
                     ashta_band: str,
                     yogas: List[Dict[str, Any]],
                     transit_load: float) -> Tuple[str, str]:
    has_arishta = any(y["severity"] == "high" for y in yogas)
    has_protect = any(y["severity"] == "protective" for y in yogas)
    if (top_window_score >= 8.0 and has_arishta) or transit_load >= 2.0:
        return ("HIGH_RISK_WINDOW", "WEAK")
    if top_window_score >= 5.0 or ashta_band == "WEAK":
        return ("VULNERABLE", "MEDIUM")
    if has_protect or ashta_band == "STRONG":
        return ("STRONG_VITALITY", "STRONG")
    return ("STABLE", "MEDIUM")


def _affected_systems(top_planets: List[Dict[str, Any]],
                       limit: int = 5) -> List[str]:
    systems: List[str] = []
    for r in top_planets[:4]:
        for s in r.get("significations", []):
            if s not in systems:
                systems.append(s)
    return systems[:limit]


def _gap_ok(cand: Dict[str, Any], chosen: List[Dict[str, Any]]) -> bool:
    for c in chosen:
        if abs((cand["start"] - c["start"]).days) < _MIN_WINDOW_GAP_DAYS:
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
    return f"{start.strftime('%b %Y')} – {end.strftime('%b %Y')}"


def _data_sufficiency(kundli: dict, kp: dict) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    if not (kundli.get("planets")):
        reasons.append("planets list missing")
    if not kundli.get("dashas"):
        reasons.append("dasha chain missing")
    if not (kp or {}).get("cusps"):
        reasons.append("KP cusps missing — KP layer will be partial")
    # KP missing is partial-degrade, not fatal
    return (not any("missing" in r and "KP" not in r for r in reasons),
             reasons)


# ════════════════════════════════════════════════════════════════════════
# Public entry point
# ════════════════════════════════════════════════════════════════════════
def compute_health_window(kundli: dict, intel: Optional[dict] = None,
                           kp: Optional[dict] = None,
                           birth: Optional[Any] = None) -> dict:
    """Run the full 9-step Health Timing Engine v1 pipeline.

    Architect-fix (Phase 2 hardening, May 6 2026): single-exit wrapper
    that GUARANTEES the thread-local cache is reset at entry and
    populated on EVERY exit path (including early-return UNKNOWN gates
    and exceptions). Without this, prior-request results could leak to a
    new request on a reused worker thread (Flask threaded dev / gunicorn
    threaded workers).
    """
    # Clear at entry — defensive against thread reuse + any code path
    # below that might fail to populate cache before returning.
    clear_last_health_result()
    result: Dict[str, Any]
    try:
        result = _compute_health_window_impl(kundli, intel, kp, birth)
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


def _compute_health_window_impl(kundli: dict,
                                  intel: Optional[dict] = None,
                                  kp: Optional[dict] = None,
                                  birth: Optional[Any] = None) -> dict:
    """Inner implementation — see `compute_health_window` for the public
    contract. Do not call directly from outside the engine module; the
    public wrapper handles cache lifecycle."""
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

    # Age (for hard guards + maraka gating)
    now = datetime.utcnow()
    birth_dt = _parse_dob_dt(birth, kundli=kundli)
    age = _compute_age(birth_dt, now)
    factors.append(f"AGE user_age={age} lagna={_SIGNS[lagna_si]}")

    # ── STEP 1 ────────────────────────────────────────────────────────
    d1_map = _step1_d1_filter(kundli, lagna_si, user_age=age)
    survivors = {p for p, info in d1_map.items() if info["in_filter"]}
    factors.append(f"STEP1 survivors={sorted(survivors)}")

    # ── STEP 2 ────────────────────────────────────────────────────────
    d9_scores = _step2_d9_verify(kundli, survivors)
    factors.append(f"STEP2 D9_scores=" +
                    ",".join(f"{p}:{s:.1f}" for p, s in d9_scores.items()))

    # ── STEP 3 ────────────────────────────────────────────────────────
    d30_scores = _step3_d30_verify(kundli, lagna_si, survivors)
    factors.append(f"STEP3 D30_scores=" +
                    ",".join(f"{p}:{s:.1f}" for p, s in d30_scores.items()))

    # ── STEP 3.5 — KP layer ───────────────────────────────────────────
    kp_layer = _step3_5_kp_layer(kp, lagna_si)
    factors.append(f"STEP3.5 KP csl_6={kp_layer['csl_6']}/{kp_layer['verdict_6']} "
                    f"csl_8={kp_layer['csl_8']}/{kp_layer['verdict_8']}")

    # ── STEP 4 — Weighted ranking ─────────────────────────────────────
    ranked = _step4_rank(d1_map, d9_scores, d30_scores, kp, lagna_si)
    factors.append("STEP4 ranked=" +
                    ",".join(f"{r['name']}:{r['score']}" for r in ranked[:5]))

    # ── STEP 5 — Dasha activation ─────────────────────────────────────
    chain = _flatten_dasha_chain(kundli)
    dasha_windows = _step5_dasha_activation(chain, ranked, lagna_si, now)
    factors.append(f"STEP5 dasha_windows_in_horizon={len(dasha_windows)}")

    # ── STEP 6 — Transits ─────────────────────────────────────────────
    planets_d1 = kundli.get("planets") or []
    transits = _step6_transits(kundli, lagna_si, planets_d1, now)
    transit_load = sum(w for _, _, w in transits.get("active_triggers", []))
    factors.append(f"STEP6 transit_load={transit_load:.2f}")

    # ── STEP 7 — Ashtakavarga ─────────────────────────────────────────
    ashta = _step7_ashtakavarga(kundli, lagna_si)
    factors.append(f"STEP7 SAV_lagna={ashta['sav_lagna']} "
                    f"band={ashta['vitality_band']}")

    # ── STEP 9 — Yogas ────────────────────────────────────────────────
    yogas = _detect_yogas(kundli, lagna_si, planets_d1)
    factors.append(f"STEP9 yogas={[y['name'] for y in yogas]}")

    # ── Window selection + severity ───────────────────────────────────
    top3 = _select_top_3(dasha_windows)
    formatted_top3: List[Dict[str, Any]] = []
    confirmations_severe = 0
    for w in top3:
        sev = _severity_of_window(w["score"], transit_load)
        if sev == "serious":
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
            if any(y["severity"] == "high" for y in yogas):
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
    verdict, band = _derive_verdict(top_score, ashta["vitality_band"],
                                       yogas, transit_load)
    severity_now = (current_window["severity"]
                     if current_window else "stable")
    rec_tier = _recommendation_tier(severity_now, confirmations_severe, age)

    # LLM directives (always include the disclaimer + age guard if applicable)
    llm_directives = ["MEDICAL_DISCLAIMER"]
    # Safety-first: if age is unknown OR below floor, enforce age-guard.
    # We never want a death-prediction question slipping through just
    # because DOB parsing failed.
    if age is None or age < _DEATH_PREDICTION_MIN_AGE:
        llm_directives.append("AGE_GUARD_NO_DEATH_PREDICTION")
    llm_directives.append(f"SEVERITY_TIER:{rec_tier}")
    if confirmations_severe >= _CONFIRMATIONS_FOR_URGENT:
        llm_directives.append("URGENT_CONSULT_TIER")
    llm_directives.append("NO_DIAGNOSIS_NAMING")
    llm_directives.append("NO_CURE_GUARANTEE")

    # Risk flags
    risk_flags: List[str] = []
    if ashta["vitality_band"] == "WEAK":
        risk_flags.append("LOW_SAV_LAGNA_VITALITY")
    if any(y["severity"] == "high" for y in yogas):
        risk_flags.append("ARISHTA_OR_PAPAKARTARI_MOON")
    if transit_load >= 1.5:
        risk_flags.append("HEAVY_TRANSIT_LOAD")
    if kp_layer.get("verdict_6") == "ILLNESS_YES":
        risk_flags.append("KP_6CSL_DUSTHANA")
    if kp_layer.get("verdict_8") == "CHRONIC_YES":
        risk_flags.append("KP_8CSL_DUSTHANA")

    # Weighted breakdown (engine audit)
    breakdown = {
        r["name"]: {"d1": r["d1"], "d9": r["d9"], "d30": r["d30"],
                     "kp": r["kp"], "karaka": r["karaka"],
                     "total": r["score"]}
        for r in ranked
    }

    affected = _affected_systems(ranked)
    remedies = _compute_health_remedies(ranked, affected, rec_tier)
    return {
        "verdict": verdict,
        "band": band,
        "current_window": current_window,
        "next_3_windows": formatted_top3,
        "protection_windows": protection_windows,
        "affected_systems": affected,
        "recommendation_tier": rec_tier,
        "top_health_planets": ranked[:5],
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

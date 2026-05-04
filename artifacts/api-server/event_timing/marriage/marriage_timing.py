"""
event_timing/marriage/marriage_timing.py
========================================
VIVAH-7 PROTOCOL — KP-first marriage timing engine.

Phase 2.8.52 (May 2 2026) — full pipeline rewrite per user spec
(see .local/notes/VIVAH-7_protocol.md). Replaces the previous Parashari-
first 5-layer pipeline with a KP-first 7-step pipeline.

Architecture lock (UNCHANGED):
  Engine    = Truth (frozen)
  LLM       = Narrator (this file's output is read-only for LLM)
  Validator = Guard (post-injector, regex-only)

Pipeline (VIVAH-7):
  STEP 0  Late vs Early Tendency       -> adjusts STEP 5 age table
  STEP 1  KP Filter (FIRST GATE)       -> 7CSL + 7C Star Lord verdict
  STEP 2  D1 + D9 Cross-Validation     -> independent confirmation
  STEP 3  Redemption                   -> own 7L / vargottama Venus rescue
  STEP 4  Dasha + Confluence           -> cluster ADs scored with:
            cluster_hit + AD/PD weight (DOMINANT, base 3)
            dasha_lord_strength multiplier (x0.5 - x1.3)
            Jupiter conjunction +2 / aspect +1
            Saturn  conjunction +2 / aspect +1
            Double Transit (Jup+Sat both)  +1
            Ashtakavarga BAV  +/-1
            7H Sarvashtakavarga  +/-0.5
            Mars trigger +1 (with Mars+Saturn conflict flag)
            Dasha Sandhi +1.5 (HIGH WEIGHT)
            Retrograde -0.5 per MD/AD lord
            Eclipse window -> -1 + delay flag
  STEP 5  Reality Filter (age-gate)    -> adjusted by STEP 0 tendency

Priority order (locked):
  Dasha > Sandhi > Transit > Mars > Retrograde

One-line truth (locked):
  "Dasha decide karta hai, Sandhi activate karta hai,
   Mars accelerate karta hai, Retrograde delay karta hai."

Public function:
  compute_timing_window(kundli, intel, kp, birth) -> dict

Output dict shape (backward-compatible + 2 new fields):
  {
    # Existing contract (preserved):
    "verdict":             "PROMISED" | "DELAYED" | "DENIED" | "PREMATURE" | "UNKNOWN",
    "band":                "WEAK" | "MEDIUM" | "STRONG",
    "primary_window":      "August - October 2027",
    "backup_window":       "March - May 2029",
    "key_trigger":         "Venus AD + Jupiter PD + Jupiter on 7H + Sandhi",
    "confluence_strength": "STRONG" | "MODERATE" | "WEAK",
    "ul_outlook":          None,
    "risk_flag":           str | None,
    "risk_flags":          [...],
    "factors":             [...],
    # NEW (additive, optional consumers):
    "top_3_windows":       [{...}, {...}, {...}],
    "step0_tendency":      {"verdict": "LATE"|"EARLY"|"BALANCED",
                            "score":   int,
                            "reasons": [...]},
  }
"""

from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

# ── Module constants (mirrors of dasha/timing engine constants) ────────
_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
          "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
_SIGN_LORDS = {0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun",
               5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter",
               9: "Saturn", 10: "Saturn", 11: "Jupiter"}

# Marriage cluster — classical 7H (spouse) + 2H (kutumba) + 11H (gain)
_MARRIAGE_HOUSES: List[int] = [7, 2, 11]

# Phase 2.8.63 (May 3 2026) — Method A removed.
# Method A's chain-union sets (_KP_PROMISE_HOUSES / _KP_DENY_HOUSES with
# Deny={6,8,12}) have been deleted per user spec. Method B (strict
# sub-lord) is the ONLY KP filter from now on. See _KP_SB_PROMISE_HOUSES
# and _KP_SB_DENY_HOUSES below for the active rule sets.

# Reality Filter age thresholds (BASE — STEP 0 may shift these)
_AGE_HARD_BLOCK = 18      # below this: never predict marriage in <2 yr
_AGE_EARLY_FLAG = 22      # 18-21: flag "practically early"
_AGE_LATE_FLAG = 39       # 39+: flag "late pattern"
_AGE_VERY_LATE = 45       # 45+: flag "compromise/fast-arranged typical"

# STEP 0 tendency shifts (added to base age thresholds)
_AGE_SHIFT_LATE = +3      # LATE tendency: push everything later
_AGE_SHIFT_EARLY = -2     # EARLY tendency: pull everything earlier

# Phase 2.8.77 — URGENCY MODE (FIX U/V/W)
# Trigger: STEP 0 = LATE  AND  current_age >= gender-specific late threshold.
# Effect: window width clamped + nearest-window recency boost.
_URGENCY_AGE_FEMALE = 30          # Female culturally-late floor
_URGENCY_AGE_MALE = 33            # Male culturally-late floor
_URGENCY_WIDTH_MONTHS = 18        # Max window width when urgency mode on
_URGENCY_RECENCY_PENALTY_PER_YEAR = 1.5   # Score -= years_from_now * this (Phase 2.8.79 simplified: 0.5 -> 1.5 strong enough that nearest viable wins on its own; FIX Y removed)

# Cardinal (movable) signs — quick-trigger marriages
_CARDINAL_SIGNS: Set[int] = {0, 3, 6, 9}    # Aries, Cancer, Libra, Capricorn
# Dual signs — multiple/delayed marriages classically
_DUAL_SIGNS: Set[int] = {2, 5, 8, 11}       # Gemini, Virgo, Sag, Pisces
# Fixed signs — stable but slower-trigger
_FIXED_SIGNS: Set[int] = {1, 4, 7, 10}      # Taurus, Leo, Scorpio, Aquarius

# Dusthana houses (avoidance set for karaka placements)
_DUSTHANA: Set[int] = {6, 8, 12}
# Kendra (1, 4, 7, 10) + Trikona (1, 5, 9) — strong houses
_KENDRA_TRIKONA: Set[int] = {1, 4, 5, 7, 9, 10}

# VIVAH-7 score thresholds (STEP 4 window selection)
_WINDOW_MIN_SCORE = 2.5     # below this: discard candidate window
_WINDOW_STRONG_SCORE = 5.0  # at/above this: STRONG confluence band
_WINDOW_MEDIUM_SCORE = 3.5  # at/above this: MODERATE confluence band

# ── STEP 0 hard-coded marriage age bands (gender-aware) ──────────────
# User-locked defaults (Hinglish: "yeh hardcoded rakho taki check kar paaye").
# Tuple = (early_max, normal_max, late_max, very_late_max).
# Anything > very_late_max -> DELAYED-CRITICAL.
_AGE_BANDS_MALE   = (24, 29, 35, 40)
_AGE_BANDS_FEMALE = (22, 27, 33, 38)

def _age_band(age_years: float, gender: str) -> str:
    """Map current age to band per gender. Returns one of:
    EARLY | NORMAL | LATE | VERY_LATE | DELAYED_CRITICAL | UNKNOWN."""
    if age_years is None or age_years < 0:
        return "UNKNOWN"
    g = (gender or "").strip().lower()
    if g in ("f", "female", "woman", "girl"):
        e, n, l, vl = _AGE_BANDS_FEMALE
    elif g in ("m", "male", "man", "boy"):
        e, n, l, vl = _AGE_BANDS_MALE
    else:
        return "UNKNOWN"
    if age_years < e:    return "EARLY"
    if age_years < n:    return "NORMAL"
    if age_years <= l:   return "LATE"
    if age_years <= vl:  return "VERY_LATE"
    return "DELAYED_CRITICAL"

def _compute_current_age(birth: Any) -> Optional[float]:
    """Compute current age in years (decimal) from birth dict."""
    if not isinstance(birth, dict):
        return None
    try:
        y = int(birth.get("year"))
        m = int(birth.get("month"))
        d = int(birth.get("day"))
        bdt = datetime(y, m, d)
        delta = datetime.utcnow() - bdt
        return round(delta.days / 365.2425, 2)
    except Exception:
        return None

def _late_status(age_band: str, step0_verdict: str) -> str:
    """Combine STEP 0 verdict + current age band -> actionable late status.
    Returns one of:
      not_yet           -> tendency LATE but age still pre-late zone
      in_late_window    -> currently in late band, predicted zone aligned
      already_late      -> past late band into very-late
      critical          -> past very-late, delayed-critical
      no_late_tendency  -> STEP 0 said EARLY/BALANCED
      unknown           -> missing gender or age
    """
    if age_band == "UNKNOWN":
        return "unknown"
    if step0_verdict != "LATE":
        return "no_late_tendency"
    if age_band in ("EARLY", "NORMAL"):
        return "not_yet"
    if age_band == "LATE":
        return "in_late_window"
    if age_band == "VERY_LATE":
        return "already_late"
    return "critical"


# Phase 2.8.62 — "marriage nearby" signal.
# When STEP 0 verdict = LATE AND user's current age is already inside the
# LATE / VERY_LATE / DELAYED_CRITICAL band, the marriage is no longer a
# distant possibility — the karmic window is open NOW. UI / narrator can
# use this flag to surface a "shadi nearby hai" message instead of the
# generic "delayed" framing.
_NEARBY_AGE_BANDS: Set[str] = {"LATE", "VERY_LATE", "DELAYED_CRITICAL"}


def _marriage_nearby(age_band: str, step0_verdict: str) -> Tuple[bool, str]:
    """Return (is_nearby, hinglish_reason).

    Trigger: engine says LATE AND user's current age band is already in the
    late zone (LATE / VERY_LATE / DELAYED_CRITICAL). This means the late
    karma is no longer "future" — it's the active window NOW.
    """
    if step0_verdict != "LATE":
        return (False, "")
    if age_band not in _NEARBY_AGE_BANDS:
        return (False, "")
    if age_band == "LATE":
        return (True, "Engine LATE bola aur aap abhi LATE age band me ho — "
                       "shadi nearby hai (active window chal raha hai).")
    if age_band == "VERY_LATE":
        return (True, "Engine LATE bola aur aap VERY_LATE band me ho — "
                       "shadi bahut nearby hai (window peak pe hai).")
    return (True, "Engine LATE bola aur aap delayed-critical zone me ho — "
                   "shadi ki window abhi sabse zyada open hai.")


# ════════════════════════════════════════════════════════════════════════
# SECTION 1 — D9 Navamsha (cross-validation toolset)
# ════════════════════════════════════════════════════════════════════════
def _get_d9_chart(planets: list, lagna_lon: Optional[float] = None) -> dict:
    """Compute D9 (Navamsha) sign placement per planet.

    Bridges -> divisional_charts.compute_d9(planets, lagna_lon)
    Returns: {"planets": {name: {"sign": str, "sign_idx": int,
                                  "vargottama": bool}, ...}}
    Returns {} on any failure (non-fatal).
    """
    try:
        from divisional_charts import compute_d9   # type: ignore
        return compute_d9(planets, lagna_lon=lagna_lon) or {}
    except Exception as exc:
        print(f"[marriage_timing._get_d9_chart] failed: {exc}")
        return {}


# ════════════════════════════════════════════════════════════════════════
# SECTION 2 — KP cusps + sub-lord + significations (STEP 1 toolset)
# ════════════════════════════════════════════════════════════════════════
def _get_kp_cusp(kp: dict, house: int) -> Optional[dict]:
    """Fetch the KP cusp dict for a given house (1-12).

    Bridges -> event_timing.marriage.love_or_arrange._kp_cusp(kp, house)
    Returns the cusp dict (with sl/nl/sb/ss fields) or None.
    """
    try:
        from .love_or_arrange import _kp_cusp   # type: ignore
        return _kp_cusp(kp, house)
    except Exception as exc:
        print(f"[marriage_timing._get_kp_cusp] failed: {exc}")
        return None


def _get_7csl(kp: dict) -> str:
    """Get the 7th cusp sub-lord (KP's single most predictive factor).

    Returns planet name (e.g. "Venus") or "" if unavailable.
    """
    try:
        cusp7 = _get_kp_cusp(kp, 7)
        if not isinstance(cusp7, dict):
            return ""
        return str(cusp7.get("sb") or "").strip()
    except Exception as exc:
        print(f"[marriage_timing._get_7csl] failed: {exc}")
        return ""


def _get_7c_star_lord(kp: dict) -> str:
    """Get the 7th cusp's STAR LORD (nl) — VIVAH-7 STEP 1 cross-check.

    Per spec: 7CSL is FINAL ARBITER, but 7C Star Lord acts as
    independent confirmation. If both denial -> hard DENY. If both
    promise -> hard PROMISE. If split -> MIXED/DELAYED.
    """
    try:
        cusp7 = _get_kp_cusp(kp, 7)
        if not isinstance(cusp7, dict):
            return ""
        return str(cusp7.get("nl") or "").strip()
    except Exception as exc:
        print(f"[marriage_timing._get_7c_star_lord] failed: {exc}")
        return ""


# Phase 2.8.63 (May 3 2026) — Method A helpers REMOVED.
# Deleted: _get_kp_significators, _planet_kp_significations,
#          _kp_planet_verdict, _kp_csl_verdict.
# Reason: per user spec, only Method B (strict sub-lord, Promise={2,7,11},
# Deny={1,6,8,10,12}) is used for the KP gate. See _kp_sublord_filter_planet
# and compute_kp_sublord_marriage_filter below.


# ════════════════════════════════════════════════════════════════════════
# SECTION 2b — ChatGPT-style strict KP Sub-Lord Marriage Filter
# (Phase 2.8.56 — added 2026-05-02 per user spec)
#
# RULE: For each planet, look at its SUB-LORD's BASIC houses (occupation +
# KP cusp ownership). Classify per:
#   Promise = {2, 7, 11}
#   Deny    = {1, 6, 8, 10, 12}
# Phase 2.8.63 (May 3 2026) — this is now the SOLE KP marriage filter.
# The earlier Method A (chain-union, Deny={6,8,12}) has been removed
# entirely per user spec: "Method A pura hatao, Method B hamesha apply karo".
#
# Per user's GOLDEN RULE: "Sub-lord = FINAL DECISION".
# ════════════════════════════════════════════════════════════════════════

# Sub-Lord-strict promise/deny sets (per user spec — note 8 added to deny)
_KP_SB_PROMISE_HOUSES: Set[int] = {2, 7, 11}
_KP_SB_DENY_HOUSES: Set[int] = {1, 6, 8, 10, 12}

_KP_PLANET_NAMES: List[str] = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
]


def _sig_pl(kp: dict, planet: str) -> List[int]:
    """Get a planet's signified houses from kp.significations[planet].pl ONLY.

    Phase 2.8.63 (May 3 2026) — locked data source per user spec:
    KP rules MUST read from chart_data.kp.significations (per-planet `pl`,
    `nl_lord`, `sb_lord`). Never touch kp.planets[] (Vedic-flavoured
    occupation) or kp.cusps[] (sign ownership) for KP marriage decisions.
    """
    if not isinstance(kp, dict) or not planet:
        return []
    sigs = (kp.get("significations") or {})
    entry = sigs.get(planet) if isinstance(sigs, dict) else None
    if not isinstance(entry, dict):
        return []
    pl = entry.get("pl") or []
    return [h for h in pl if isinstance(h, int)]


def _sig_sb_lord(kp: dict, planet: str) -> str:
    """Get a planet's SUB-LORD from kp.significations[planet].sb_lord ONLY."""
    if not isinstance(kp, dict) or not planet:
        return ""
    sigs = (kp.get("significations") or {})
    entry = sigs.get(planet) if isinstance(sigs, dict) else None
    if not isinstance(entry, dict):
        return ""
    return entry.get("sb_lord") or ""


def _sig_nl_lord(kp: dict, planet: str) -> str:
    """Get a planet's STAR-LORD (Nakshatra Lord) from kp.significations[planet].nl_lord ONLY.

    Phase 2.8.70 (May 3 2026) — added for STEP 1 FIX E (NL tie-breaker on MIXED).
    Source: kp_engine writes 'nl_lord' into each significations[planet] entry.
    Same data-purity contract as _sig_sb_lord — never reads kp.planets[] / kp.cusps[].
    """
    if not isinstance(kp, dict) or not planet:
        return ""
    sigs = (kp.get("significations") or {})
    entry = sigs.get(planet) if isinstance(sigs, dict) else None
    if not isinstance(entry, dict):
        return ""
    return entry.get("nl_lord") or ""


def _kp_sublord_filter_planet(kp: dict, planet: str) -> Dict[str, Any]:
    """Apply strict Sub-Lord filter to ONE planet using significations only.

    Returns dict:
      {
        "planet":       "Sun",
        "sub_lord":     "Saturn",
        "sb_houses":    [2, 3],         # = significations[sub_lord].pl
        "promise_hits": [2],
        "deny_hits":    [],
        "verdict":      "STRONG" | "MIXED" | "WEAK" | "UNKNOWN",
        "reason":       "SB Saturn (2,3) -> promise [2]"
      }

    Phase 2.8.63 (May 3 2026) — locked KP data source:
      - Sub-lord planet:    kp.significations[planet].sb_lord
      - Sub-lord's houses:  kp.significations[sb_lord].pl
    Does NOT read kp.planets[] or kp.cusps[]. This guarantees we never
    accidentally mix Vedic whole-sign occupation/ownership into the
    KP marriage gate.

    Verdict rules:
      promise_hits >= 1 and deny_hits == 0   -> STRONG
      promise_hits >= 1 and deny_hits >= 1   -> MIXED
      promise_hits == 0 and deny_hits >= 1   -> WEAK
      both empty                             -> UNKNOWN
    """
    out: Dict[str, Any] = {
        "planet": planet, "sub_lord": None, "sb_houses": [],
        "promise_hits": [], "deny_hits": [],
        "verdict": "UNKNOWN", "reason": "no SB found",
        # Phase 2.8.70 FIX E (added) — NL tie-breaker metadata
        "star_lord": None, "nl_houses": [],
        "nl_promise_hits": [], "nl_deny_hits": [],
        "nl_tiebreak_applied": False,
        "raw_sb_verdict": "UNKNOWN",
    }
    if not isinstance(kp, dict) or not planet:
        return out
    sb = _sig_sb_lord(kp, planet)
    if not sb:
        out["reason"] = f"no sb_lord in significations[{planet}]"
        return out
    sb_houses = sorted(set(_sig_pl(kp, sb)))
    sb_set = set(sb_houses)
    promise = sorted(sb_set & _KP_SB_PROMISE_HOUSES)
    deny = sorted(sb_set & _KP_SB_DENY_HOUSES)

    if promise and not deny:
        verdict = "STRONG"
        reason = f"SB {sb} ({','.join(map(str, sb_houses))}) -> promise {promise}"
    elif promise and deny:
        verdict = "MIXED"
        reason = f"SB {sb} ({','.join(map(str, sb_houses))}) -> promise {promise} but deny {deny}"
    elif deny and not promise:
        verdict = "WEAK"
        reason = f"SB {sb} ({','.join(map(str, sb_houses))}) -> only deny {deny}, no 2/7/11"
    else:
        verdict = "UNKNOWN"
        reason = f"SB {sb} ({','.join(map(str, sb_houses))}) -> no promise no deny"

    # ──────────────────────────────────────────────────────────────────────
    # Phase 2.8.70 FIX E (added 2026-05-03) — STAR LORD (NL) TIE-BREAKER
    #
    # Classical KP hierarchy: SL > NL > planet itself. Sub-Lord is FINAL
    # DECIDER (golden rule preserved), but when SL is itself ambiguous
    # (promise AND deny both present → MIXED), the planet's Star Lord acts
    # as the tie-breaker. This is the only case where NL is allowed to
    # influence the verdict; STRONG / WEAK / UNKNOWN are NEVER touched.
    #
    # Rules (NL ONLY consulted on raw SB verdict == MIXED):
    #   NL only-promise (no deny) → upgrade MIXED → STRONG
    #   NL only-deny (no promise) → downgrade MIXED → WEAK
    #   NL mixed/unknown          → keep MIXED (no flip)
    #
    # Data source: kp.significations[planet].nl_lord, then
    # significations[nl_lord].pl. Same purity contract as SB path.
    # ──────────────────────────────────────────────────────────────────────
    raw_sb_verdict = verdict
    nl = _sig_nl_lord(kp, planet)
    nl_houses: List[int] = []
    nl_promise: List[int] = []
    nl_deny: List[int] = []
    nl_tiebreak_applied = False

    if nl:
        nl_houses = sorted(set(_sig_pl(kp, nl)))
        nl_set = set(nl_houses)
        nl_promise = sorted(nl_set & _KP_SB_PROMISE_HOUSES)
        nl_deny = sorted(nl_set & _KP_SB_DENY_HOUSES)

        if verdict == "MIXED" and nl_houses:
            if nl_promise and not nl_deny:
                verdict = "STRONG"
                reason = (
                    f"{reason}; NL tie-break {nl} ({','.join(map(str, nl_houses))}) "
                    f"-> only promise {nl_promise} -> upgrade to STRONG [2.8.70]"
                )
                nl_tiebreak_applied = True
            elif nl_deny and not nl_promise:
                verdict = "WEAK"
                reason = (
                    f"{reason}; NL tie-break {nl} ({','.join(map(str, nl_houses))}) "
                    f"-> only deny {nl_deny} -> downgrade to WEAK [2.8.70]"
                )
                nl_tiebreak_applied = True
            # NL mixed or empty intersection → no flip, keep MIXED

    out.update({
        "sub_lord": sb,
        "sb_houses": sb_houses,
        "promise_hits": promise,
        "deny_hits": deny,
        "verdict": verdict,
        "reason": reason,
        # FIX E observability fields
        "star_lord": nl or None,
        "nl_houses": nl_houses,
        "nl_promise_hits": nl_promise,
        "nl_deny_hits": nl_deny,
        "nl_tiebreak_applied": nl_tiebreak_applied,
        "raw_sb_verdict": raw_sb_verdict,
    })
    return out


def compute_kp_sublord_marriage_filter(kp: dict) -> Dict[str, Any]:
    """Run strict KP Sub-Lord marriage filter across all 9 planets + final verdict.

    Implements the ChatGPT-validated methodology approved by user 2026-05-02:
      - Sub-Lord = FINAL DECIDER
      - Sub-Lord houses = basic occupation + KP cusp ownership
      - Promise = {2, 7, 11}
      - Deny    = {1, 6, 8, 10, 12}

    Final verdict logic (strict KP per user spec):
      - 7CSL filter result is the PRIMARY decider
      - Consensus of 9 planets adjusts strength

    Returns dict:
      {
        "per_planet":     [{...}, ...],          # 9 entries
        "buckets": {
            "strong":     ["Sun", "Moon", ...],  # STRONG verdict planets
            "mixed":      [...],
            "weak":       [...],
            "unknown":    [...],
        },
        "csl_planet":     "Sun",
        "csl_filter":     {...same shape as per_planet entry...},
        "verdict":        "PROMISED" | "DELAYED" | "DENIED",
        "strength":       "STRONG" | "MEDIUM" | "WEAK",
        "reason":         "2-line plain reason",
      }
    """
    out: Dict[str, Any] = {
        "per_planet": [], "buckets": {"strong": [], "mixed": [], "weak": [], "unknown": []},
        "csl_planet": None, "csl_filter": None,
        "verdict": "UNKNOWN", "strength": "WEAK",
        "reason": "insufficient KP data",
    }
    if not isinstance(kp, dict):
        return out
    try:
        # Per-planet pass
        for pname in _KP_PLANET_NAMES:
            entry = _kp_sublord_filter_planet(kp, pname)
            out["per_planet"].append(entry)
            v = entry.get("verdict") or "UNKNOWN"
            bucket = v.lower()
            if bucket not in out["buckets"]:
                out["buckets"][bucket] = []
            out["buckets"][bucket].append(pname)

        # 7CSL is the FINAL DECIDER (per user golden rule)
        csl = _get_7csl(kp)
        out["csl_planet"] = csl
        if csl:
            csl_entry = _kp_sublord_filter_planet(kp, csl)
            out["csl_filter"] = csl_entry
            csl_v = csl_entry.get("verdict")
        else:
            csl_v = "UNKNOWN"

        strong_n = len(out["buckets"]["strong"])
        mixed_n = len(out["buckets"]["mixed"])
        weak_n = len(out["buckets"]["weak"])

        # FINAL verdict (Sub-Lord priority — 7CSL leads, with contradiction guard)
        # Contradiction guard: even if 7CSL=STRONG, severe disagreement from
        # the 9-planet consensus (majority WEAK) downgrades the call. This
        # prevents over-confident PROMISED when only the 7CSL agrees.
        contradiction = (csl_v == "STRONG" and weak_n >= 5 and strong_n <= 2)

        if csl_v == "STRONG" and contradiction:
            verdict = "DELAYED"
        elif csl_v == "STRONG":
            verdict = "PROMISED"
        elif csl_v == "MIXED":
            verdict = "DELAYED"
        elif csl_v == "WEAK":
            verdict = "DENIED" if weak_n >= 5 else "DELAYED"
        else:
            # csl_v UNKNOWN: insufficient data on the FINAL DECIDER planet.
            # Default to DELAYED (safer than PROMISED, more actionable than UNKNOWN).
            verdict = "DELAYED"

        # Strength (consensus-adjusted)
        if csl_v == "STRONG" and contradiction:
            strength = "WEAK"
        elif csl_v == "STRONG" and strong_n >= 4 and weak_n <= 2:
            strength = "STRONG"
        elif csl_v == "STRONG" and (mixed_n >= 2 or weak_n >= 3):
            strength = "MEDIUM"
        elif csl_v == "MIXED":
            strength = "MEDIUM" if strong_n >= 3 else "WEAK"
        elif csl_v == "WEAK":
            strength = "WEAK"
        else:
            strength = "WEAK"

        # Plain 2-line reason
        sb_summary = (out["csl_filter"] or {}).get("reason") or "n/a"
        reason = (
            f"7CSL {csl} sub-lord filter: {sb_summary}. "
            f"Consensus: {strong_n} strong, {mixed_n} mixed, {weak_n} weak."
        )

        out.update({
            "verdict": verdict, "strength": strength, "reason": reason,
        })
        return out
    except Exception as exc:
        print(f"[marriage_timing.compute_kp_sublord_marriage_filter] failed: {exc}")
        return out


# ════════════════════════════════════════════════════════════════════════
# SECTION 2b — Phase 2.8.67 (May 3 2026): KP CONFIDENCE GATE WRAPPER
#
# ADD-ONLY layer on top of compute_kp_sublord_marriage_filter().
# Solves the "rigid binary kill switch" gap WITHOUT changing KP truth.
#
# Default behavior (birth_time_confidence == "confident") is IDENTICAL
# to before — DENIED hard-stops the timing scan. Nothing changes for
# 99% of users.
#
# When the user (or a future rectification module) explicitly tags the
# birth time as uncertain (birth_time_confidence == "uncertain"), a
# DENIED KP verdict becomes "DENIED_LOW_CONFIDENCE":
#   • timing scan IS allowed to run downstream
#   • final user-facing verdict still leans denial-flavored
#   • LLM narration must include the low-confidence disclaimer
#
# This is the ONLY behavioral change. PROMISED / DELAYED paths are
# untouched regardless of confidence flag.
# ════════════════════════════════════════════════════════════════════════

# Allowed confidence levels (canonical strings)
_BTC_CONFIDENT = "confident"     # default — exact birth time known
_BTC_UNCERTAIN = "uncertain"     # birth time approximate / rectification pending
_BTC_VALID: Set[str] = {_BTC_CONFIDENT, _BTC_UNCERTAIN}


def _normalize_birth_time_confidence(value: Any) -> str:
    """Coerce arbitrary input to one of {confident, uncertain}.

    Defaults to 'confident' so unknown/missing inputs preserve legacy
    hard-gate behavior. Recognized mappings:
      uncertain  ← 'uncertain', 'unknown', 'approx', 'approximate',
                   'low', 'low_confidence', 'uncertain_time', 'rectify',
                   'rectification_pending', 'no', 'false', '0', False
      confident  ← 'confident', 'exact', 'confirmed', 'high',
                   'high_confidence', 'known', 'yes', 'true', '1', True,
                   None, '' (empty)
    Anything else falls through to 'confident' (safe default).
    """
    if value is None:
        return _BTC_CONFIDENT
    if isinstance(value, bool):
        # bool: True = confident, False = uncertain
        return _BTC_CONFIDENT if value else _BTC_UNCERTAIN
    s = str(value).strip().lower()
    if not s:
        return _BTC_CONFIDENT
    if s in _BTC_VALID:
        return s
    if s in {"unknown", "approx", "approximate", "low", "low_confidence",
             "uncertain_time", "rectify", "rectification_pending",
             "no", "false", "0"}:
        return _BTC_UNCERTAIN
    if s in {"exact", "confirmed", "high", "high_confidence", "known",
             "yes", "true", "1"}:
        return _BTC_CONFIDENT
    # Unrecognized — be safe, treat as confident (preserve old behavior)
    return _BTC_CONFIDENT


def extract_birth_time_confidence(birth_data: Any) -> str:
    """Pull birth_time_confidence from a birth_data dict.

    Looks at multiple key spellings to be tolerant of upstream changes:
      birth_time_confidence | btc | time_confidence | tob_confidence

    Returns 'confident' if missing or unrecognized.
    """
    if not isinstance(birth_data, dict):
        return _BTC_CONFIDENT
    for key in ("birth_time_confidence", "btc", "time_confidence",
                "tob_confidence", "birthTimeConfidence"):
        if key in birth_data:
            return _normalize_birth_time_confidence(birth_data.get(key))
    return _BTC_CONFIDENT


def compute_kp_gate_decision(kp: dict,
                              birth_time_confidence: Any = _BTC_CONFIDENT
                              ) -> Dict[str, Any]:
    """Apply the KP gate with birth-time-confidence awareness.

    Wraps compute_kp_sublord_marriage_filter() and decides whether the
    downstream timing scan should run, hard-stop, or run in
    low-confidence mode.

    Args:
      kp: chart_data['kp'] dict (must contain 'significations' + 'cusps')
      birth_time_confidence: 'confident' | 'uncertain' (or any value
        normalized via _normalize_birth_time_confidence)

    Returns dict:
      {
        "kp_filter":          {... raw output of compute_kp_sublord_marriage_filter ...},
        "kp_verdict":         "PROMISED" | "DELAYED" | "DENIED" | "UNKNOWN",
        "kp_strength":        "STRONG" | "MEDIUM" | "WEAK",
        "confidence":         "confident" | "uncertain",
        "gate_action":        "PROCEED" | "HARD_STOP" | "PROCEED_LOW_CONF",
        "final_label":        "PROMISED" | "DELAYED" | "DENIED" | "DENIED_LOW_CONFIDENCE" | "UNKNOWN",
        "allow_timing_scan":  bool,
        "low_confidence_mode": bool,
        "reason":             str,
        "disclaimer":         str | None,   # required for narration if low-conf
      }

    Decision matrix:
      ────────────────────────────────────────────────────────────────
      KP verdict   | confidence  | gate_action       | final_label
      ────────────────────────────────────────────────────────────────
      PROMISED     | confident   | PROCEED           | PROMISED
      PROMISED     | uncertain   | PROCEED           | PROMISED        (no disclaimer)
      DELAYED      | confident   | PROCEED           | DELAYED
      DELAYED      | uncertain   | PROCEED_LOW_CONF  | DELAYED         (with disclaimer)
      DENIED       | confident   | HARD_STOP         | DENIED
      DENIED       | uncertain   | PROCEED_LOW_CONF  | DENIED_LOW_CONFIDENCE
      UNKNOWN      | (any)       | PROCEED_LOW_CONF  | UNKNOWN
      ────────────────────────────────────────────────────────────────
    """
    btc = _normalize_birth_time_confidence(birth_time_confidence)
    # Default skeleton — note that for non-dict / missing KP we fall through
    # to the same UNKNOWN→PROCEED_LOW_CONF branch as the matrix documents,
    # so the matrix and implementation stay in lock-step.
    out: Dict[str, Any] = {
        "kp_filter": {}, "kp_verdict": "UNKNOWN", "kp_strength": "WEAK",
        "confidence": btc,
        "gate_action": "PROCEED_LOW_CONF", "final_label": "UNKNOWN",
        "allow_timing_scan": True, "low_confidence_mode": True,
        "reason": "kp data unavailable → low-confidence proceed",
        "disclaimer": (
            "KP sub-lord data is unavailable for this chart. "
            "Marriage verdict cannot be locked; results below are "
            "heuristic estimates only."
        ),
    }
    if not isinstance(kp, dict):
        return out

    try:
        kp_filter = compute_kp_sublord_marriage_filter(kp)
        out["kp_filter"] = kp_filter
        verdict = kp_filter.get("verdict") or "UNKNOWN"
        strength = kp_filter.get("strength") or "WEAK"
        out["kp_verdict"] = verdict
        out["kp_strength"] = strength

        # Apply decision matrix
        if verdict == "PROMISED":
            gate_action = "PROCEED"
            final_label = "PROMISED"
            allow_scan = True
            low_conf = False
            disclaimer = None
            reason = f"KP gate PROMISED (7CSL strong); confidence={btc}"

        elif verdict == "DELAYED":
            allow_scan = True
            final_label = "DELAYED"
            if btc == _BTC_UNCERTAIN:
                gate_action = "PROCEED_LOW_CONF"
                low_conf = True
                disclaimer = (
                    "Note: birth time confidence is low; KP sub-lord "
                    "results may shift with even a 2-minute correction. "
                    "Treat the timing window as approximate."
                )
                reason = "KP gate DELAYED + uncertain birth time → low-confidence proceed"
            else:
                gate_action = "PROCEED"
                low_conf = False
                disclaimer = None
                reason = "KP gate DELAYED → proceed with delay narrative"

        elif verdict == "DENIED":
            if btc == _BTC_UNCERTAIN:
                # The ONE genuine behavioral change in this phase.
                gate_action = "PROCEED_LOW_CONF"
                final_label = "DENIED_LOW_CONFIDENCE"
                allow_scan = True
                low_conf = True
                disclaimer = (
                    "KP sub-lord analysis indicates denial, BUT the birth "
                    "time is flagged as uncertain. A small (2-3 min) birth-"
                    "time correction can flip this verdict. Showing "
                    "best-effort timing windows for reference only — do "
                    "NOT treat as final until birth-time rectification is "
                    "completed."
                )
                reason = ("KP gate DENIED + uncertain birth time → "
                          "low-confidence fallback timing scan allowed")
            else:
                gate_action = "HARD_STOP"
                final_label = "DENIED"
                allow_scan = False
                low_conf = False
                disclaimer = None
                reason = "KP gate DENIED (confident birth time) → hard stop"

        else:
            # UNKNOWN — insufficient KP data; always low-confidence proceed
            gate_action = "PROCEED_LOW_CONF"
            final_label = "UNKNOWN"
            allow_scan = True
            low_conf = True
            disclaimer = (
                "KP sub-lord data is incomplete for this chart. "
                "Marriage verdict cannot be locked; timing windows below "
                "are heuristic estimates only."
            )
            reason = "KP verdict UNKNOWN → low-confidence proceed"

        out.update({
            "gate_action": gate_action,
            "final_label": final_label,
            "allow_timing_scan": allow_scan,
            "low_confidence_mode": low_conf,
            "reason": reason,
            "disclaimer": disclaimer,
        })
        return out
    except Exception as exc:
        print(f"[marriage_timing.compute_kp_gate_decision] failed: {exc}")
        return out


def apply_birth_time_confidence_to_verdict(verdict: str,
                                             birth_time_confidence: Any = _BTC_CONFIDENT,
                                             ) -> Dict[str, Any]:
    """Lightweight wiring helper for callers that already hold a KP verdict.

    Use this when you already have a KP gate verdict from the live STEP-1
    path (e.g. compute_timing_window's 7CSL + StarLord truth-table) and
    only need the confidence overlay — without re-running the full
    9-planet sub-lord filter.

    Returns the same shape as compute_kp_gate_decision() except
    `kp_filter` is empty (no per-planet detail), and `kp_strength` is
    derived heuristically from the verdict alone.

    This keeps the wiring path safe: existing verdict semantics remain
    the source of truth; only the gate_action / disclaimer layer is new.
    """
    btc = _normalize_birth_time_confidence(birth_time_confidence)
    v = (verdict or "UNKNOWN").upper()
    # Map raw verdict → strength heuristic (only used for downstream display)
    strength = {"PROMISED": "STRONG", "DELAYED": "MEDIUM",
                "DENIED": "WEAK", "UNKNOWN": "WEAK"}.get(v, "WEAK")

    out: Dict[str, Any] = {
        "kp_filter": {},
        "kp_verdict": v,
        "kp_strength": strength,
        "confidence": btc,
        "gate_action": "PROCEED",
        "final_label": v,
        "allow_timing_scan": True,
        "low_confidence_mode": False,
        "reason": "",
        "disclaimer": None,
    }

    if v == "PROMISED":
        out["reason"] = f"KP gate PROMISED; confidence={btc}"
    elif v == "DELAYED":
        if btc == _BTC_UNCERTAIN:
            out["gate_action"] = "PROCEED_LOW_CONF"
            out["low_confidence_mode"] = True
            out["disclaimer"] = (
                "Note: birth time confidence is low; KP sub-lord results "
                "may shift with even a 2-minute correction. Treat the "
                "timing window as approximate."
            )
            out["reason"] = "KP gate DELAYED + uncertain birth time → low-confidence proceed"
        else:
            out["reason"] = "KP gate DELAYED → proceed with delay narrative"
    elif v == "DENIED":
        if btc == _BTC_UNCERTAIN:
            out["gate_action"] = "PROCEED_LOW_CONF"
            out["final_label"] = "DENIED_LOW_CONFIDENCE"
            out["low_confidence_mode"] = True
            out["disclaimer"] = (
                "KP sub-lord analysis indicates denial, BUT the birth "
                "time is flagged as uncertain. A small (2-3 min) birth-"
                "time correction can flip this verdict. Showing best-"
                "effort timing windows for reference only — do NOT treat "
                "as final until birth-time rectification is completed."
            )
            out["reason"] = ("KP gate DENIED + uncertain birth time → "
                             "low-confidence fallback timing scan allowed")
        else:
            out["gate_action"] = "HARD_STOP"
            out["allow_timing_scan"] = False
            out["reason"] = "KP gate DENIED (confident birth time) → hard stop"
    else:
        # UNKNOWN — always low-confidence proceed, regardless of btc
        out["gate_action"] = "PROCEED_LOW_CONF"
        out["low_confidence_mode"] = True
        out["disclaimer"] = (
            "KP sub-lord verdict is incomplete for this chart. "
            "Marriage verdict cannot be locked; timing windows below "
            "are heuristic estimates only."
        )
        out["reason"] = "KP verdict UNKNOWN → low-confidence proceed"

    return out


# ════════════════════════════════════════════════════════════════════════
# SECTION 2c — STEP 2: D1 + D9 link filter (Phase 2.8.64, May 3 2026)
#
# User-locked spec for STEP 2:
#   "STEP 1 me jo planets filter hue (full approval / semi / reject), unka
#    D1 aur D9 dono me 7H aur 7L ke saath connection check karo."
#
# Four standard "links" with 7H / 7L:
#   1. occupation   — planet sits in 7H of that chart
#   2. conjunction  — planet shares 7L's sign (and is not 7L itself)
#   3. aspect       — planet aspects 7H sign OR 7L's sign (special aspects
#                     for Mars/Jupiter/Saturn; everyone else only 7th)
#   4. parivartana  — planet in 7L's owned sign AND 7L in planet's owned
#                     sign (skipped for Rahu/Ketu — no lordship)
#
# Link strength per planet:
#   BOTH   — link present in BOTH D1 and D9   (strongest)
#   D1     — link present only in D1
#   D9     — link present only in D9
#   NONE   — no link in either chart
#
# Final classification matrix (STEP 1 verdict × link strength):
#   STRONG (full approval) + BOTH      -> STRONGEST_PROMISE
#   STRONG                 + D1|D9     -> CONFIRMED_PROMISE
#   STRONG                 + NONE      -> PASSIVE_PROMISE
#   MIXED  (semi)          + BOTH      -> STRONG_CONDITIONAL
#   MIXED                  + D1|D9     -> CONDITIONAL
#   MIXED                  + NONE      -> NEUTRAL
#   WEAK   (reject)        + BOTH      -> STRONGEST_DENIAL
#   WEAK                   + D1|D9     -> ACTIVE_DENIAL
#   WEAK                   + NONE      -> PASSIVE_DENIAL
#
# Final buckets (last filter):
#   APPROVERS    = STRONGEST_PROMISE  + CONFIRMED_PROMISE
#   CONDITIONAL  = STRONG_CONDITIONAL + CONDITIONAL + PASSIVE_PROMISE
#   DENIERS      = STRONGEST_DENIAL   + ACTIVE_DENIAL
#   IGNORE       = NEUTRAL            + PASSIVE_DENIAL
# ════════════════════════════════════════════════════════════════════════

def _planet_owned_signs(planet: str) -> List[int]:
    """Return list of zodiac sign indices ruled by this planet.

    Rahu/Ketu return [] (no lordship in classical scheme).
    """
    if planet in ("", "Rahu", "Ketu"):
        return []
    return [si for si, lord in _SIGN_LORDS.items() if lord == planet]


def _aspects_target(planet: str, p_si: int, target_si: int) -> bool:
    """True if `planet` (sitting in sign `p_si`) aspects `target_si` sign.

    Universal: every planet has 7th aspect. Special aspects:
      Mars    -> 4, 7, 8 (diff 3, 6, 7)
      Jupiter -> 5, 7, 9 (diff 4, 6, 8)
      Saturn  -> 3, 7, 10 (diff 2, 6, 9)
    Rahu/Ketu — conservative: only 7th aspect (no special drishti).
    """
    if p_si is None or target_si is None:
        return False
    diff = (target_si - p_si) % 12
    if diff == 6:
        return True   # universal 7th aspect
    if planet == "Mars":
        return diff in (3, 7)
    if planet == "Jupiter":
        return diff in (4, 8)
    if planet == "Saturn":
        return diff in (2, 9)
    return False


# ──────────────────────────────────────────────────────────────────────
# Phase 2.8.72 (May 3 2026) — FIX #1: WEIGHTED LINK SCORING
#
# Reality of KP/Vedic link strength:
#   parivartana (sign exchange) > conjunction = occupation > aspect (loose)
# Old code treated all 4 link types as equal booleans → aspect-only
# planets bloated the "linked" bucket and inflated approver counts.
#
# Weights and threshold:
#   parivartana = 3   (strongest — full mutual exchange of signs)
#   conjunction = 2   (planet sits with 7L)
#   occupation  = 2   (planet sits in 7H)
#   aspect      = 1   (sign-only aspect — loose without orb)
#
# `linked` now means score >= 2 (i.e. at least one strong link, OR
# the very strong parivartana alone). Aspect-only (score 1) no longer
# counts as a meaningful link. `any_linked` retained for observability.
# ──────────────────────────────────────────────────────────────────────
_LINK_WEIGHTS: Dict[str, int] = {
    "parivartana": 3,
    "conjunction": 2,
    "occupation":  2,
    "aspect":      1,
}
_LINK_THRESHOLD: int = 2


def _planet_link_in_chart(planet: str, p_si: Optional[int], p_house: Optional[int],
                           h7_si: Optional[int],
                           seventh_lord: str,
                           seventh_lord_si: Optional[int]
                           ) -> Dict[str, Any]:
    """Check 4 link types between `planet` and 7H/7L within a single chart.

    Returns dict:
      {"occupation":  bool, "conjunction": bool, "aspect": bool,
       "parivartana": bool, "linked": bool, "any_linked": bool,
       "score": int, "details": [str]}

    Phase 2.8.72 FIX #1: `linked` is now score-based (>= _LINK_THRESHOLD).
    `any_linked` preserves the old "any link present" boolean for
    diagnostic / backward inspection only.
    """
    out: Dict[str, Any] = {
        "occupation": False, "conjunction": False,
        "aspect": False, "parivartana": False,
        "linked": False, "any_linked": False, "score": 0,
        "details": [],
    }
    if p_si is None or h7_si is None:
        return out

    # 1. Occupation — planet sits in 7H
    if p_house == 7:
        out["occupation"] = True
        out["details"].append("occ-7H")
    elif p_si == h7_si:
        # House data missing: fall back to sign-based check
        out["occupation"] = True
        out["details"].append("occ-7H(sign)")

    # 2. Conjunction with 7L — same sign as 7L planet (not 7L itself)
    if (seventh_lord and seventh_lord_si is not None
            and planet != seventh_lord
            and p_si == seventh_lord_si):
        out["conjunction"] = True
        out["details"].append(f"conj-7L({seventh_lord})")

    # 3. Aspect on 7H sign OR 7L's sign
    if not out["occupation"]:
        if _aspects_target(planet, p_si, h7_si):
            out["aspect"] = True
            out["details"].append("asp-7H")
        elif (seventh_lord_si is not None
                and planet != seventh_lord
                and not out["conjunction"]
                and _aspects_target(planet, p_si, seventh_lord_si)):
            out["aspect"] = True
            out["details"].append(f"asp-7L({seventh_lord})")

    # 4. Parivartana with 7L (skip Rahu/Ketu and self-7L case)
    if (seventh_lord and seventh_lord_si is not None
            and planet != seventh_lord
            and planet not in ("Rahu", "Ketu")
            and seventh_lord not in ("Rahu", "Ketu")):
        p_owned = _planet_owned_signs(planet)
        sl_owned = _planet_owned_signs(seventh_lord)
        if p_si in sl_owned and seventh_lord_si in p_owned:
            out["parivartana"] = True
            out["details"].append(f"pari-7L({seventh_lord})")

    # Phase 2.8.72 FIX #1: weighted score replaces equal-weight boolean
    out["any_linked"] = bool(out["occupation"] or out["conjunction"]
                             or out["aspect"] or out["parivartana"])
    out["score"] = sum(_LINK_WEIGHTS[k] for k in _LINK_WEIGHTS if out.get(k))
    out["linked"] = out["score"] >= _LINK_THRESHOLD
    return out


def _d1_planet_state(planets: list, name: str
                      ) -> Tuple[Optional[int], Optional[int]]:
    """Return (sign_idx, house) of `name` from D1 planets list."""
    return (_planet_sign_idx(planets, name), _planet_house_local(planets, name))


def _d9_planet_state(d9_planets_list: list, name: str
                      ) -> Tuple[Optional[int], Optional[int]]:
    """Return (sign_idx, house) of `name` from D9 planets list."""
    if not isinstance(d9_planets_list, list):
        return (None, None)
    for entry in d9_planets_list:
        if not isinstance(entry, dict) or entry.get("name") != name:
            continue
        si = entry.get("signIndex")
        if not isinstance(si, int):
            si = entry.get("sign_idx")
        h = entry.get("house")
        return (si if isinstance(si, int) else None,
                h if isinstance(h, int) else None)
    return (None, None)


# Final classification matrix
# Phase 2.8.72 FIX #3 (May 3 2026): STRONG + NONE downgraded
# PASSIVE_PROMISE → NEUTRAL. Rationale: KP says "promise" but the planet
# has zero meaningful link (score < 2) to 7H/7L in either D1 or D9 →
# execution mechanism missing → not safe to count as a soft promiser.
# Old PASSIVE_PROMISE label kept in _STEP2_FINAL_BUCKET for defensive
# backward-compat (no longer produced by the matrix).
_STEP2_MATRIX: Dict[Tuple[str, str], str] = {
    ("STRONG", "BOTH"):  "STRONGEST_PROMISE",
    ("STRONG", "D1"):    "CONFIRMED_PROMISE",
    ("STRONG", "D9"):    "CONFIRMED_PROMISE",
    ("STRONG", "NONE"):  "NEUTRAL",            # was PASSIVE_PROMISE [2.8.72]
    ("MIXED",  "BOTH"):  "STRONG_CONDITIONAL",
    ("MIXED",  "D1"):    "CONDITIONAL",
    ("MIXED",  "D9"):    "CONDITIONAL",
    ("MIXED",  "NONE"):  "NEUTRAL",
    ("WEAK",   "BOTH"):  "STRONGEST_DENIAL",
    ("WEAK",   "D1"):    "ACTIVE_DENIAL",
    ("WEAK",   "D9"):    "ACTIVE_DENIAL",
    ("WEAK",   "NONE"):  "PASSIVE_DENIAL",
    # UNKNOWN STEP 1 verdict — passthrough
    ("UNKNOWN", "BOTH"): "UNKNOWN",
    ("UNKNOWN", "D1"):   "UNKNOWN",
    ("UNKNOWN", "D9"):   "UNKNOWN",
    ("UNKNOWN", "NONE"): "UNKNOWN",
}

# Final-bucket grouping
_STEP2_FINAL_BUCKET: Dict[str, str] = {
    "STRONGEST_PROMISE":  "approvers",
    "CONFIRMED_PROMISE":  "approvers",
    "STRONG_CONDITIONAL": "conditional",
    "CONDITIONAL":        "conditional",
    "PASSIVE_PROMISE":    "conditional",
    "STRONGEST_DENIAL":   "deniers",
    "ACTIVE_DENIAL":      "deniers",
    "NEUTRAL":            "ignore",
    "PASSIVE_DENIAL":     "ignore",
    "UNKNOWN":            "ignore",
}


def compute_step2_link_filter(kundli: dict, kp: dict
                                ) -> Dict[str, Any]:
    """STEP 2 — re-filter STEP 1 planets via D1 + D9 link to 7H/7L.

    Returns dict:
      {
        "d1": {"lagna_si": 8, "h7_si": 2, "seventh_lord": "Mercury",
               "seventh_lord_si": 9},
        "d9": {"lagna_si": 1, "h7_si": 7, "seventh_lord": "Mars",
               "seventh_lord_si": 4},
        "per_planet": [
          {"planet": "Sun", "step1_verdict": "STRONG",
           "d1_link": {...}, "d9_link": {...},
           "link_strength": "BOTH" | "D1" | "D9" | "NONE",
           "final": "STRONGEST_PROMISE",
           "bucket": "approvers"}, ...
        ],
        "buckets": {
          "approvers":   ["Sun", ...],
          "conditional": [...],
          "deniers":     [...],
          "ignore":      [...],
        },
      }
    """
    out: Dict[str, Any] = {
        "d1": {}, "d9": {},
        "per_planet": [],
        "buckets": {"approvers": [], "conditional": [],
                    "deniers": [], "ignore": []},
    }
    if not isinstance(kundli, dict):
        return out
    try:
        # ---- Pull D1 essentials ----
        planets = kundli.get("planets") or []
        asc_sign = kundli.get("ascendant")
        lagna_si = (_SIGNS.index(asc_sign)
                    if isinstance(asc_sign, str) and asc_sign in _SIGNS
                    else None)
        if lagna_si is None:
            return out
        h7_si = (lagna_si + 6) % 12
        seventh_lord = _SIGN_LORDS.get(h7_si) or ""
        seventh_lord_si = _planet_sign_idx(planets, seventh_lord) if seventh_lord else None

        out["d1"] = {
            "lagna_si": lagna_si, "lagna_sign": _SIGNS[lagna_si],
            "h7_si": h7_si, "h7_sign": _SIGNS[h7_si],
            "seventh_lord": seventh_lord,
            "seventh_lord_si": seventh_lord_si,
            "seventh_lord_sign": _SIGNS[seventh_lord_si] if seventh_lord_si is not None else None,
        }

        # ---- Pull D9 essentials (use kundli.divisionalCharts.D9 — has houses) ----
        dc = kundli.get("divisionalCharts") or {}
        d9 = dc.get("D9") or dc.get("d9") or {}
        d9_planets_list = d9.get("planets") if isinstance(d9, dict) else []
        d9_lagna_si = d9.get("ascendantSignIndex") if isinstance(d9, dict) else None
        if not isinstance(d9_lagna_si, int):
            d9_asc = d9.get("ascendant") if isinstance(d9, dict) else None
            d9_lagna_si = (_SIGNS.index(d9_asc)
                           if isinstance(d9_asc, str) and d9_asc in _SIGNS
                           else None)

        if isinstance(d9_lagna_si, int):
            d9_h7_si = (d9_lagna_si + 6) % 12
            d9_seventh_lord = _SIGN_LORDS.get(d9_h7_si) or ""
            d9_seventh_lord_si, _ = _d9_planet_state(d9_planets_list, d9_seventh_lord)
            out["d9"] = {
                "lagna_si": d9_lagna_si, "lagna_sign": _SIGNS[d9_lagna_si],
                "h7_si": d9_h7_si, "h7_sign": _SIGNS[d9_h7_si],
                "seventh_lord": d9_seventh_lord,
                "seventh_lord_si": d9_seventh_lord_si,
                "seventh_lord_sign": _SIGNS[d9_seventh_lord_si] if d9_seventh_lord_si is not None else None,
            }
        else:
            d9_h7_si = None
            d9_seventh_lord = ""
            d9_seventh_lord_si = None

        # ---- STEP 1 verdicts (Method B per-planet) ----
        step1 = compute_kp_sublord_marriage_filter(kp)
        s1_verdict_by_planet = {e["planet"]: (e.get("verdict") or "UNKNOWN")
                                 for e in (step1.get("per_planet") or [])}

        # ---- For each of the 9 planets: link in D1 + link in D9 ----
        for pname in _KP_PLANET_NAMES:
            s1v = s1_verdict_by_planet.get(pname, "UNKNOWN")

            d1_si, d1_house = _d1_planet_state(planets, pname)
            d1_link = _planet_link_in_chart(
                pname, d1_si, d1_house, h7_si, seventh_lord, seventh_lord_si)

            d9_si, d9_house = _d9_planet_state(d9_planets_list, pname)
            d9_link = _planet_link_in_chart(
                pname, d9_si, d9_house, d9_h7_si,
                d9_seventh_lord, d9_seventh_lord_si)

            d1_linked = d1_link["linked"]
            d9_linked = d9_link["linked"]
            if d1_linked and d9_linked:
                strength = "BOTH"
            elif d1_linked:
                strength = "D1"
            elif d9_linked:
                strength = "D9"
            else:
                strength = "NONE"

            final = _STEP2_MATRIX.get((s1v, strength), "UNKNOWN")
            bucket = _STEP2_FINAL_BUCKET.get(final, "ignore")

            out["per_planet"].append({
                "planet": pname,
                "step1_verdict": s1v,
                "d1_link": d1_link,
                "d9_link": d9_link,
                "link_strength": strength,
                "final": final,
                "bucket": bucket,
            })
            if bucket in out["buckets"]:
                out["buckets"][bucket].append(pname)

        return out
    except Exception as exc:
        print(f"[marriage_timing.compute_step2_link_filter] failed: {exc}")
        return out


# ════════════════════════════════════════════════════════════════════════
# SECTION 3 — Vimshottari MD-AD scanner (STEP 4 base)
# ════════════════════════════════════════════════════════════════════════
def _get_dasha_upcoming(kundli: dict) -> List[dict]:
    """Fetch upcoming MD-AD blocks from kundli.

    Handles three known shapes:
      A) kundli["vimshottari"]["upcoming"]              (already flat)
      B) kundli["upcomingAntars"]                       (already flat)
      C) kundli["dashas"] = [{planet, startDate, endDate, subDashas:[
              {planet, startDate, endDate, subDashas:[PDs]}, ... ]}]
    """
    if not isinstance(kundli, dict):
        return []

    vims = kundli.get("vimshottari") or kundli.get("dasha") or {}
    if isinstance(vims, dict):
        flat = (vims.get("upcoming")
                or vims.get("antardasha_sequence")
                or [])
        if flat and isinstance(flat, list):
            return flat

    flat = (kundli.get("upcomingAntars")
            or kundli.get("upcoming_antars")
            or kundli.get("upcomingDashas")
            or kundli.get("antardashas")
            or [])
    if flat and isinstance(flat, list):
        return flat

    dashas = kundli.get("dashas") or []
    if not isinstance(dashas, list):
        return []
    today = date.today()
    out: List[dict] = []
    for md in dashas:
        if not isinstance(md, dict):
            continue
        md_lord = md.get("planet") or md.get("md_lord")
        if not md_lord:
            continue
        for ad in (md.get("subDashas") or md.get("antar_dashas") or []):
            if not isinstance(ad, dict):
                continue
            ad_lord = ad.get("planet") or ad.get("ad_lord")
            ad_end = ad.get("endDate") or ad.get("end")
            if not (ad_lord and ad_end):
                continue
            try:
                end_d = datetime.strptime(str(ad_end)[:10], "%Y-%m-%d").date()
                if end_d < today - timedelta(days=60):
                    continue
            except Exception:
                pass
            out.append({
                "md_lord": md_lord,
                "ad_lord": ad_lord,
                "start": ad.get("startDate") or ad.get("start"),
                "end": ad_end,
            })
    return out


def _scan_cluster_ads(kundli: dict, target_lords: Set[str],
                      lookback_days: int = 30) -> List[dict]:
    """Find upcoming MD-AD jodis where MD or AD lord is in target_lords.

    Bridges -> vedic.timing.timing_engine._scan_dasha_for_lords
    Returns list of {md, ad, start, end, score} dicts.
    """
    try:
        from vedic.timing.timing_engine import (   # type: ignore
            _scan_dasha_for_lords,
        )
        vims = (kundli.get("vimshottari")
                or kundli.get("dasha")
                or {})
        if not (isinstance(vims, dict) and vims.get("upcoming")):
            upcoming = _get_dasha_upcoming(kundli)
            vims = {"upcoming": upcoming, "current": (vims or {}).get("current") or {}}
        return _scan_dasha_for_lords(vims, target_lords, lookback_days) or []
    except Exception as exc:
        print(f"[marriage_timing._scan_cluster_ads] failed: {exc}")
        return []


def _marriage_target_lords(lagna_sign_idx: int) -> Set[str]:
    """Compute target lords for marriage cluster {7H, 2H, 11H} from lagna.
    Adds Karaka planets (Venus, Jupiter).
    """
    try:
        si = int(lagna_sign_idx) % 12
        lords = {_SIGN_LORDS[(si + h - 1) % 12] for h in _MARRIAGE_HOUSES}
        lords.add("Venus")
        lords.add("Jupiter")
        return lords
    except Exception:
        return {"Venus", "Jupiter"}


# ════════════════════════════════════════════════════════════════════════
# SECTION 4 — PD month-window chain (STEP 4 month precision)
# ════════════════════════════════════════════════════════════════════════
def _project_pds(md_lord: str, ad_lord: str,
                 ad_start: datetime, ad_end: datetime,
                 from_dt: Optional[datetime] = None,
                 months_needed: int = 6) -> List[dict]:
    """Project PD chain inside a given AD."""
    try:
        from vedic.future_engine import _project_pd_chain   # type: ignore
        from_dt = from_dt or datetime.utcnow()
        return _project_pd_chain(md_lord, ad_lord, ad_start, ad_end,
                                 from_dt, months_needed) or []
    except Exception as exc:
        print(f"[marriage_timing._project_pds] failed: {exc}")
        return []


def _get_current_pd(current_dasha: dict,
                    when: Optional[datetime] = None) -> dict:
    """Get the currently-running Pratyantar Dasha info."""
    try:
        from pratyantar import compute_pratyantar   # type: ignore
        return compute_pratyantar(current_dasha, when=when) or {}
    except Exception as exc:
        print(f"[marriage_timing._get_current_pd] failed: {exc}")
        return {}


# ════════════════════════════════════════════════════════════════════════
# SECTION 5 — Jupiter / Saturn / Mars transit ephemeris (STEP 4 confluence)
# ════════════════════════════════════════════════════════════════════════
def _get_transits_at(natal_lagna_si: int, natal_moon_si: Optional[int],
                     when: Optional[datetime] = None) -> dict:
    """Compute Jupiter/Saturn/Mars/Rahu sidereal sign at a given date."""
    try:
        from transits import compute_transits   # type: ignore
        return compute_transits(natal_lagna_si, natal_moon_si,
                                when=when) or {}
    except Exception as exc:
        print(f"[marriage_timing._get_transits_at] failed: {exc}")
        return {}


def _transit_sign_idx(transit_data: dict, planet: str) -> Optional[int]:
    """Extract a transiting planet's sidereal sign index."""
    if not isinstance(transit_data, dict):
        return None
    th = transit_data.get("transit_houses") or {}
    p = th.get(planet) if isinstance(th, dict) else None
    if not isinstance(p, dict):
        p = transit_data.get(planet) or {}
    if not isinstance(p, dict):
        return None
    si = p.get("sign_idx")
    if isinstance(si, int):
        return si % 12
    sign = p.get("sign")
    if isinstance(sign, str) and sign in _SIGNS:
        return _SIGNS.index(sign)
    return None


def _is_jupiter_aspect(jup_si: int, target_si: int) -> bool:
    """Jupiter has 5th, 7th, 9th aspects (counted from itself)."""
    diff = (target_si - jup_si) % 12
    return diff in (4, 6, 8)


def _is_saturn_aspect(sat_si: int, target_si: int) -> bool:
    """Saturn has 3rd, 7th, 10th aspects."""
    diff = (target_si - sat_si) % 12
    return diff in (2, 6, 9)


def _is_mars_aspect(mars_si: int, target_si: int) -> bool:
    """Mars has 4th, 7th, 8th aspects."""
    diff = (target_si - mars_si) % 12
    return diff in (3, 6, 7)


def _jupiter_score_on_7h(transit_data: dict, h7_si: int,
                          venus_si: Optional[int]) -> Tuple[int, str]:
    """+2 conjunction (same sign as 7H or natal Venus), +1 aspect, 0 else."""
    jup_si = _transit_sign_idx(transit_data, "Jupiter")
    if jup_si is None:
        return (0, "")
    if jup_si == h7_si:
        return (2, f"Jupiter conj 7H ({_SIGNS[h7_si]})")
    if venus_si is not None and jup_si == venus_si:
        return (2, f"Jupiter conj natal Venus ({_SIGNS[venus_si]})")
    if _is_jupiter_aspect(jup_si, h7_si):
        return (1, f"Jupiter aspect 7H ({_SIGNS[jup_si]} -> {_SIGNS[h7_si]})")
    return (0, "")


def _saturn_score_on_7h(transit_data: dict, h7_si: int,
                         moon_si: Optional[int]) -> Tuple[int, str]:
    """+2 conjunction (7H or 7th-from-Moon), +1 aspect, 0 else."""
    sat_si = _transit_sign_idx(transit_data, "Saturn")
    if sat_si is None:
        return (0, "")
    if sat_si == h7_si:
        return (2, f"Saturn conj 7H ({_SIGNS[h7_si]})")
    if moon_si is not None:
        seventh_from_moon = (moon_si + 6) % 12
        if sat_si == seventh_from_moon:
            return (2, f"Saturn 7th-from-Moon ({_SIGNS[seventh_from_moon]})")
    if _is_saturn_aspect(sat_si, h7_si):
        return (1, f"Saturn aspect 7H ({_SIGNS[sat_si]} -> {_SIGNS[h7_si]})")
    return (0, "")


def _user_transit_gate_check(transit_data: dict,
                              h7_si: Optional[int],
                              seventh_lord_natal_si: Optional[int]
                              ) -> Tuple[str, str]:
    """Phase 2.8.80 — USER HARD TRANSIT GATE (ADD-ONLY).

    User-spec rule:
      Jupiter PASS = Jupiter in 7H sign OR Jupiter aspects natal 7L position
      Saturn  PASS = Saturn in 7H sign OR Saturn aspects natal 7L position

    Tiers:
      DTT     -> both Jupiter AND Saturn pass  (best, classical Double Transit)
      SINGLE  -> exactly one passes            (acceptable, accept window)
      FAIL    -> neither passes                (reject window, move to next)
    """
    if h7_si is None:
        return ("FAIL", "no 7H sign available")
    jup_si = _transit_sign_idx(transit_data, "Jupiter")
    sat_si = _transit_sign_idx(transit_data, "Saturn")

    jup_pass = False
    jup_why = ""
    if jup_si is not None:
        if jup_si == h7_si:
            jup_pass = True
            jup_why = f"Jup in 7H ({_SIGNS[h7_si]})"
        elif (seventh_lord_natal_si is not None
              and _is_jupiter_aspect(jup_si, seventh_lord_natal_si)):
            jup_pass = True
            jup_why = (f"Jup aspect 7L ({_SIGNS[jup_si]}->"
                       f"{_SIGNS[seventh_lord_natal_si]})")

    sat_pass = False
    sat_why = ""
    if sat_si is not None:
        if sat_si == h7_si:
            sat_pass = True
            sat_why = f"Sat in 7H ({_SIGNS[h7_si]})"
        elif (seventh_lord_natal_si is not None
              and _is_saturn_aspect(sat_si, seventh_lord_natal_si)):
            sat_pass = True
            sat_why = (f"Sat aspect 7L ({_SIGNS[sat_si]}->"
                       f"{_SIGNS[seventh_lord_natal_si]})")

    if jup_pass and sat_pass:
        return ("DTT", f"{jup_why} + {sat_why}")
    if jup_pass:
        return ("SINGLE", jup_why)
    if sat_pass:
        return ("SINGLE", sat_why)
    return ("FAIL", "neither Jup nor Sat on 7H/7L")


def _mars_trigger_check(transit_data: dict, h7_si: int,
                         venus_si: Optional[int],
                         seventh_lord_si: Optional[int]) -> Tuple[bool, str]:
    """Mars trigger: Mars conjunct or aspecting 7H, Venus, or 7L."""
    mars_si = _transit_sign_idx(transit_data, "Mars")
    if mars_si is None:
        return (False, "")
    targets = [("7H", h7_si)]
    if venus_si is not None:
        targets.append(("Venus", venus_si))
    if seventh_lord_si is not None:
        targets.append(("7L", seventh_lord_si))
    for label, t_si in targets:
        if mars_si == t_si:
            return (True, f"Mars conj {label} ({_SIGNS[t_si]})")
        if _is_mars_aspect(mars_si, t_si):
            return (True, f"Mars aspect {label} ({_SIGNS[mars_si]}->{_SIGNS[t_si]})")
    return (False, "")


# ════════════════════════════════════════════════════════════════════════
# SECTION 5b — STRICT DTT helpers (ADD-ONLY: 7H sign + natal 7L sign both
# treated as marriage cluster targets). User-spec rule:
#   "Jupiter aur Saturn ka transit hamesha 7H ya 7L per hona chahiye."
# Single-transit acceptable agar dasha very strong (triple-promiser).
# ════════════════════════════════════════════════════════════════════════
def _jup_sat_marriage_cluster_check(transit_data: dict,
                                     h7_si: Optional[int],
                                     seventh_lord_natal_si: Optional[int]
                                     ) -> Dict[str, Any]:
    """Check Jupiter+Saturn against BOTH 7H sign and natal 7L sign.

    Returns:
      {"jup_hit": bool, "sat_hit": bool, "dtt": bool,
       "jup_detail": str, "sat_detail": str,
       "jup_target": "7H"|"7L"|"", "sat_target": "7H"|"7L"|""}
    """
    out: Dict[str, Any] = {
        "jup_hit": False, "sat_hit": False, "dtt": False,
        "jup_detail": "", "sat_detail": "",
        "jup_target": "", "sat_target": "",
    }
    targets: List[Tuple[str, int]] = []
    if h7_si is not None:
        targets.append(("7H", h7_si))
    if seventh_lord_natal_si is not None and seventh_lord_natal_si != h7_si:
        targets.append(("7L", seventh_lord_natal_si))
    if not targets:
        return out

    jup_si = _transit_sign_idx(transit_data, "Jupiter")
    sat_si = _transit_sign_idx(transit_data, "Saturn")

    if jup_si is not None:
        for label, t_si in targets:
            if jup_si == t_si:
                out["jup_hit"] = True
                out["jup_target"] = label
                out["jup_detail"] = f"Jup OCCUPIES {label} ({_SIGNS[t_si]})"
                break
            if _is_jupiter_aspect(jup_si, t_si):
                out["jup_hit"] = True
                out["jup_target"] = label
                out["jup_detail"] = f"Jup asp {label} ({_SIGNS[jup_si]}->{_SIGNS[t_si]})"
                break

    if sat_si is not None:
        for label, t_si in targets:
            if sat_si == t_si:
                out["sat_hit"] = True
                out["sat_target"] = label
                out["sat_detail"] = f"Sat OCCUPIES {label} ({_SIGNS[t_si]})"
                break
            if _is_saturn_aspect(sat_si, t_si):
                out["sat_hit"] = True
                out["sat_target"] = label
                out["sat_detail"] = f"Sat asp {label} ({_SIGNS[sat_si]}->{_SIGNS[t_si]})"
                break

    out["dtt"] = out["jup_hit"] and out["sat_hit"]
    return out


def _dtt_score_window(start: datetime, end: datetime,
                       lagna_si: int, moon_si: Optional[int],
                       h7_si: Optional[int],
                       seventh_lord_natal_si: Optional[int],
                       samples: int = 5) -> Dict[str, Any]:
    """Sample N points across a window, count DTT and single-transit hits.

    Returns: {"dtt_count": int, "single_count": int, "samples": int,
              "dtt_pct": float, "details": [{"date","jup","sat","dtt"}]}
    """
    if end <= start:
        return {"dtt_count": 0, "single_count": 0, "samples": 0,
                "dtt_pct": 0.0, "details": []}
    span = (end - start).days
    points: List[datetime] = []
    if samples <= 1:
        points.append(start + timedelta(days=span // 2))
    else:
        for i in range(samples):
            f = (i + 0.5) / samples
            points.append(start + timedelta(days=int(span * f)))
    dtt_n = 0
    sng_n = 0
    details: List[Dict[str, Any]] = []
    for d in points:
        try:
            t = _get_transits_at(lagna_si, moon_si, when=d)
        except Exception:
            t = {}
        chk = _jup_sat_marriage_cluster_check(t, h7_si, seventh_lord_natal_si)
        if chk["dtt"]:
            dtt_n += 1
        if chk["jup_hit"] or chk["sat_hit"]:
            sng_n += 1
        details.append({
            "date": d.strftime("%Y-%m-%d"),
            "jup": chk["jup_detail"] or "—",
            "sat": chk["sat_detail"] or "—",
            "dtt": chk["dtt"],
        })
    return {
        "dtt_count": dtt_n,
        "single_count": sng_n,
        "samples": len(points),
        "dtt_pct": round(100.0 * dtt_n / max(1, len(points)), 1),
        "details": details,
    }


def _full_d1_d9_marriage_planet_scan(planets: list,
                                       h7_si: Optional[int],
                                       seventh_lord: Optional[str],
                                       seventh_lord_natal_si: Optional[int],
                                       kundli: dict,
                                       asc_lon: Optional[float]
                                       ) -> Dict[str, Any]:
    """Full 9-planet × {sit_7H, asp_7H, conj_7L, asp_7L} scan in D1 + D9.

    Returns dict with per-planet connections and totals. Used to flag
    promiser/denier planets the engine's STEP 2 (3 hardcoded checks) misses.
    """
    NINE = ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu"]
    out: Dict[str, Any] = {
        "d1": [], "d9": [],
        "d1_promiser_count": 0,
        "d1_denier_count": 0,
        "d9_promiser_count": 0,
        "promisers": [], "deniers": [],
    }
    if h7_si is None:
        return out

    p_by = {p.get("name"): p for p in planets if isinstance(p, dict)}

    def _aspect(planet: str, p_si: int, target_si: int) -> str:
        if (target_si - p_si) % 12 == 6:
            return "7th"
        if planet == "Mars" and (target_si - p_si) % 12 in (3, 7):
            return "4th" if (target_si - p_si) % 12 == 3 else "8th"
        if planet == "Jupiter" and (target_si - p_si) % 12 in (4, 8):
            return "5th" if (target_si - p_si) % 12 == 4 else "9th"
        if planet == "Saturn" and (target_si - p_si) % 12 in (2, 9):
            return "3rd" if (target_si - p_si) % 12 == 2 else "10th"
        return ""

    promisers: List[str] = []
    deniers: List[str] = []

    for nm in NINE:
        p = p_by.get(nm)
        if not p:
            continue
        sg = p.get("sign")
        if sg not in _SIGNS:
            continue
        si = _SIGNS.index(sg)
        sit_7h = (si == h7_si)
        asp_7h = _aspect(nm, si, h7_si) if not sit_7h else ""
        conj_7l = (seventh_lord_natal_si is not None
                   and si == seventh_lord_natal_si and nm != seventh_lord)
        asp_7l = (_aspect(nm, si, seventh_lord_natal_si)
                  if (seventh_lord_natal_si is not None and not conj_7l
                      and si != seventh_lord_natal_si and nm != seventh_lord)
                  else "")
        connects = sit_7h or bool(asp_7h) or conj_7l or bool(asp_7l)
        # Classical denier flag: Mars/Saturn aspect 7H/7L = delay/affliction
        is_denier = (nm in ("Mars", "Saturn")
                     and (sit_7h or asp_7h or conj_7l or asp_7l))
        is_promiser = (nm in ("Jupiter", "Venus", "Moon", "Mercury", "Rahu")
                        and connects)
        if is_promiser:
            promisers.append(nm)
            out["d1_promiser_count"] += 1
        if is_denier:
            deniers.append(nm)
            out["d1_denier_count"] += 1
        out["d1"].append({
            "planet": nm, "sign": sg, "house": p.get("house"),
            "sit_7h": sit_7h, "asp_7h": asp_7h or None,
            "conj_7l": conj_7l, "asp_7l": asp_7l or None,
            "role": "promiser" if is_promiser else (
                "denier" if is_denier else "neutral"),
        })

    # D9 scan — conjunctions only (D9 lagna may not be reliable here)
    try:
        d9 = _get_d9_chart(planets, asc_lon) or {}
        d9p = d9.get("planets") if isinstance(d9.get("planets"), dict) else d9
        if isinstance(d9p, dict):
            d9_merc_sg = (d9p.get(seventh_lord or "") or {}).get("sign") if seventh_lord else None
            d9_merc_si = _SIGNS.index(d9_merc_sg) if d9_merc_sg in _SIGNS else None
            for nm in NINE:
                dp = d9p.get(nm) or {}
                sg = dp.get("sign")
                if sg not in _SIGNS:
                    continue
                si = _SIGNS.index(sg)
                conj_7l_d9 = (d9_merc_si is not None and si == d9_merc_si
                              and nm != seventh_lord)
                if conj_7l_d9 and nm in ("Jupiter", "Venus", "Moon",
                                          "Mercury", "Rahu", "Mars"):
                    if nm not in promisers:
                        promisers.append(nm + "(D9)")
                    out["d9_promiser_count"] += 1
                out["d9"].append({
                    "planet": nm, "sign": sg,
                    "conj_7l_d9": conj_7l_d9,
                })
    except Exception as exc:
        print(f"[marriage_timing._full_d1_d9_marriage_planet_scan D9] failed: {exc}")

    out["promisers"] = promisers
    out["deniers"] = deniers
    return out


def _chronological_dtt_top3_strict(kundli: dict,
                                     target_lords: Set[str],
                                     lagna_si: int,
                                     moon_si: Optional[int],
                                     h7_si: Optional[int],
                                     seventh_lord_natal_si: Optional[int],
                                     min_age_dt: Optional[datetime] = None,
                                     scan_until: Optional[datetime] = None
                                     ) -> List[Dict[str, Any]]:
    """STRICT iterative DTT picker (user-spec rule).

    Iterates promiser ADs/PDs in chronological order. For each promiser PD,
    checks Jup+Sat double transit on 7H sign OR natal 7L sign. Returns
    first 3 windows ranked by DTT score (then chronological). Single-
    transit windows accepted only if dasha is triple-promiser (MD+AD+PD).
    """
    today = datetime.utcnow()
    floor_dt = max(today, min_age_dt) if min_age_dt else today
    ceil_dt = scan_until or datetime(2050, 1, 1)
    if h7_si is None:
        return []

    candidate_ads = _scan_cluster_ads(kundli, target_lords, lookback_days=30)
    candidates: List[Dict[str, Any]] = []
    for ad_blk in candidate_ads:
        md = ad_blk.get("md") or ad_blk.get("md_lord")
        ad = ad_blk.get("ad") or ad_blk.get("ad_lord")
        ad_start = _parse_dt(ad_blk.get("start"))
        ad_end = _parse_dt(ad_blk.get("end"))
        if not (md and ad and ad_start and ad_end):
            continue
        if ad_end < floor_dt or ad_start > ceil_dt:
            continue
        if md not in target_lords and ad not in target_lords:
            continue
        ad_months = max(3, int((ad_end - ad_start).days / 30) + 1)
        from_dt = max(floor_dt, ad_start)
        if from_dt >= ad_end:
            continue
        pds = _project_pds(md, ad, ad_start, ad_end,
                           from_dt=from_dt, months_needed=ad_months)
        for pd_blk in pds:
            ps = pd_blk.get("start"); pe = pd_blk.get("end")
            pl = pd_blk.get("pd")
            if not (isinstance(ps, datetime) and isinstance(pe, datetime)):
                continue
            if pl not in target_lords:
                continue
            if pe < floor_dt or ps > ceil_dt:
                continue
            scan = _dtt_score_window(ps, pe, lagna_si, moon_si,
                                       h7_si, seventh_lord_natal_si, samples=5)
            triple = (1 if md in target_lords else 0) + \
                     (1 if ad in target_lords else 0) + \
                     (1 if pl in target_lords else 0)
            # Acceptance: DTT >= 3/5 OR (single >= 4/5 AND triple == 3)
            accept = (scan["dtt_count"] >= 3) or \
                     (scan["single_count"] >= 4 and triple == 3)
            if not accept:
                continue
            candidates.append({
                "md": md, "ad": ad, "pd": pl,
                "start": ps, "end": pe,
                "window": _format_window(ps, pe),
                "start_iso": ps.strftime("%Y-%m-%d"),
                "end_iso": pe.strftime("%Y-%m-%d"),
                "dtt_count": scan["dtt_count"],
                "single_count": scan["single_count"],
                "samples": scan["samples"],
                "dtt_pct": scan["dtt_pct"],
                "triple_promiser": triple,
                "rule_passed": "DTT" if scan["dtt_count"] >= 3 else "SINGLE+TRIPLE",
                "details": scan["details"],
            })

    # Rank: DTT count desc, then chronological asc
    candidates.sort(key=lambda c: (-c["dtt_count"], -c["triple_promiser"], c["start"]))
    # Dedupe by AD (keep best PD per AD for top-3 spread)
    seen_ads: Set[Tuple[str, str]] = set()
    top3: List[Dict[str, Any]] = []
    for c in candidates:
        key = (c["md"], c["ad"])
        if key in seen_ads and len(top3) >= 1:
            # allow same-AD only if no other ADs left to fill top-3
            continue
        top3.append(c)
        seen_ads.add(key)
        if len(top3) >= 3:
            break
    # Re-sort top-3 chronologically for user-friendly display
    top3.sort(key=lambda c: c["start"])
    return top3


# ════════════════════════════════════════════════════════════════════════
# SECTION 6 — Manglik (STEP 0 / risk flag)
# ════════════════════════════════════════════════════════════════════════
def _get_manglik(planets: list) -> str:
    """Compute Manglik status. Returns: Active|Mild|None|Unknown."""
    try:
        from dosh_engine import _manglik   # type: ignore
        result = _manglik(planets)
        if isinstance(result, tuple) and result:
            return str(result[0] or "Unknown")
        if isinstance(result, str):
            return result
        return "Unknown"
    except Exception as exc:
        print(f"[marriage_timing._get_manglik] failed: {exc}")
        return "Unknown"


# ════════════════════════════════════════════════════════════════════════
# SECTION 7 — Age compute (STEP 5 reality filter)
# ════════════════════════════════════════════════════════════════════════
def _get_current_age(birth: Any, kundli: dict,
                     current_dasha: Optional[dict] = None) -> Optional[int]:
    """Compute current age in years from birth date."""
    try:
        from vedic.context.age_context import (   # type: ignore
            compute_age_context,
        )
        ctx = compute_age_context(birth or {}, kundli or {},
                                  current_dasha=current_dasha)
        if not isinstance(ctx, dict) or not ctx.get("available", True):
            if isinstance(ctx, dict) and "current_age" in ctx:
                return int(ctx["current_age"])
            return None
        for key in ("current_age", "age"):
            if key in ctx:
                try:
                    return int(ctx[key])
                except (TypeError, ValueError):
                    continue
        return None
    except Exception as exc:
        print(f"[marriage_timing._get_current_age] failed: {exc}")
        return None


def _adjusted_age_thresholds(step0_verdict: str) -> Tuple[int, int, int, int]:
    """STEP 5 — return age boundaries shifted by STEP 0 tendency.

    Returns (HARD_BLOCK, EARLY_FLAG, LATE_FLAG, VERY_LATE).
    """
    if step0_verdict == "LATE":
        s = _AGE_SHIFT_LATE
    elif step0_verdict == "EARLY":
        s = _AGE_SHIFT_EARLY
    else:
        s = 0
    return (
        _AGE_HARD_BLOCK,                  # never shifted (legal floor)
        max(_AGE_HARD_BLOCK, _AGE_EARLY_FLAG + s),
        _AGE_LATE_FLAG + s,
        _AGE_VERY_LATE + s,
    )


def _is_urgency_mode(current_age: Optional[float], step0_verdict: str,
                      gender: str) -> bool:
    """Phase 2.8.77 (FIX U): URGENCY mode trigger.

    True ONLY when BOTH conditions hold:
      1) STEP 0 verdict == "LATE"  (chart has late-marriage indication)
      2) current_age >= gender-specific late threshold
         (Female 30+, Male 33+ — classical Indian context)

    When True, downstream STEP 5 will:
      - clamp window width to _URGENCY_WIDTH_MONTHS (18 mo)
      - apply recency penalty so nearest viable window wins ranking
    """
    if step0_verdict != "LATE":
        return False
    if current_age is None:
        return False
    g = (gender or "").strip().lower()
    threshold = _URGENCY_AGE_FEMALE if g.startswith("f") else _URGENCY_AGE_MALE
    try:
        return float(current_age) >= float(threshold)
    except (TypeError, ValueError):
        return False


def _clamp_window_to_months(start, end, max_months: int):
    """Phase 2.8.77 (FIX V): clamp a (start, end) window to <= max_months wide.

    Returns (new_end, was_clamped). Keeps original start; trims end only.
    Uses 30.44 days/month (avg). If already within bound, returns end unchanged.
    """
    from datetime import timedelta
    try:
        actual_days = (end - start).days
    except Exception:
        return end, False
    max_days = int(max_months * 30.44)
    if actual_days <= max_days:
        return end, False
    return start + timedelta(days=max_days), True


def _age_filter_action(age: Optional[float], predicted_age: Optional[float],
                        thresholds: Tuple[int, int, int, int]) -> str:
    """Decide STEP 5 action.

    Phase 2.8.76 (FIX P): Decision is based ONLY on `predicted_age` (the age
    at the time of the predicted window). Current `age` is now informational
    only and is no longer used to BLOCK future windows. A 17-yr-old's
    window at age 24 is valid; only the predicted-age check decides.

    Returns: BLOCK | FLAG_EARLY | OK | FLAG_LATE | FLAG_VERY_LATE | UNKNOWN
    """
    hard_block, early_flag, late_flag, very_late = thresholds
    if predicted_age is None:
        return "UNKNOWN"
    if predicted_age < hard_block:
        # Predicted window itself falls before legal/practical floor -> BLOCK
        return "BLOCK"
    if predicted_age < early_flag:
        return "FLAG_EARLY"
    if predicted_age < late_flag:
        return "OK"
    if predicted_age < very_late:
        return "FLAG_LATE"
    return "FLAG_VERY_LATE"


# ════════════════════════════════════════════════════════════════════════
# SECTION 8 — STEP 0: Late vs Early Tendency Check
# ════════════════════════════════════════════════════════════════════════
def _step0_late_early_tendency(planets: list, intel: dict, kp: dict,
                                lagna_si: Optional[int],
                                h7_si: Optional[int],
                                seventh_lord: Optional[str],
                                venus_si: Optional[int],
                                gender: str = "",
                                current_age: Optional[float] = None) -> dict:
    """STEP 0 — count LATE vs EARLY indicators.

    LATE indicators (4):
      L1: Saturn conjunct or aspecting 7H or 7L (natal)
      L2: 7L in 12H or debilitated
      L3: Venus combust or in dusthana
      L11: Saturn IN 7H natally

    EARLY indicators (4):
      E1: Jupiter conjunct or aspecting 7H or 7L (natal)
      E2: Venus exalted, in own sign, or in 5/7H
      E5: 7H in cardinal sign (quick triggers)
      E6: 7L in kendra/trikona (1/4/5/7/9/10) and not retro

    Gender modifier (G1/G2):
      Men   -> Venus karaka issues weighted +1 LATE
      Women -> Jupiter karaka issues weighted +1 LATE

    Returns:
      {"verdict":"LATE"|"EARLY"|"BALANCED",
       "score": int (positive=LATE, negative=EARLY),
       "reasons": [...]}
    """
    reasons: List[str] = []
    late = 0
    early = 0

    if lagna_si is None or h7_si is None:
        return {"verdict": "BALANCED", "score": 0,
                "late_count": 0, "early_count": 0,
                "reasons": ["STEP 0 skipped: lagna unknown"]}

    seventh_lord_si = _planet_sign_idx(planets, seventh_lord) if seventh_lord else None
    seventh_lord_h = _planet_house_local(planets, seventh_lord) if seventh_lord else None
    seventh_lord_dignity = _planet_dignity(planets, seventh_lord) if seventh_lord else ""
    seventh_lord_retro = (_planet_is_retrograde(planets, seventh_lord)
                          if seventh_lord else False)
    venus_house = _planet_house_local(planets, "Venus")
    venus_dignity = _planet_dignity(planets, "Venus")
    venus_combust = _is_combust_local(planets, "Venus")
    saturn_si = _planet_sign_idx(planets, "Saturn")
    saturn_house = _planet_house_local(planets, "Saturn")
    jup_si = _planet_sign_idx(planets, "Jupiter")
    # Phase 2.8.69 FIX D — hoist Jupiter strength metadata for E1 gating.
    jup_house = _planet_house_local(planets, "Jupiter")
    jup_dignity = _planet_dignity(planets, "Jupiter")
    jup_combust = _is_combust_local(planets, "Jupiter")

    # ── L1 + L11: Saturn affliction on 7H/7L (natal)
    # Phase 2.8.68 FIX A — de-duplicate L1+L11. Saturn-in-7H now scores +2
    # via L11 only; L1 occupation branch is suppressed in that case to
    # prevent the historical double-count (+2 was actually +1+1).
    sat_in_7h = (saturn_house == 7) or (
        saturn_si is not None and saturn_si == h7_si)
    sat_aff_7h_aspect = (saturn_si is not None
                         and not sat_in_7h
                         and _is_saturn_aspect(saturn_si, h7_si))
    sat_aff_7l = (saturn_si is not None and seventh_lord_si is not None
                  and (saturn_si == seventh_lord_si
                       or _is_saturn_aspect(saturn_si, seventh_lord_si)))
    if sat_in_7h:
        # L11 takes the strongest reading; L1 is folded in to avoid double penalty.
        late += 2
        reasons.append("L11: natal Saturn IN 7H (+2 LATE; L1 folded in)")
    elif sat_aff_7h_aspect:
        late += 1
        reasons.append("L1: natal Saturn aspect on 7H (+1 LATE)")
    elif sat_aff_7l:
        late += 1
        reasons.append(f"L1: natal Saturn afflicting 7L {seventh_lord} (+1 LATE)")

    # ── L2: 7L in 12H or debilitated
    if seventh_lord_h == 12:
        late += 1
        reasons.append(f"L2: 7L {seventh_lord} in 12H — withdrawal (+1 LATE)")
    if seventh_lord_dignity == "debilitated":
        late += 1
        reasons.append(f"L2: 7L {seventh_lord} debilitated (+1 LATE)")

    # ── L3: Venus weakness — combust + dusthana + debilitated
    # Phase 2.8.68 FIX B — debilitated Venus now adds a LATE point (was 0
    # before). Total Venus weakness contribution capped at +2 so a triply
    # afflicted Venus doesn't over-bias the verdict.
    venus_late = 0
    if venus_combust:
        venus_late += 1
        reasons.append("L3: Venus combust (+1 LATE)")
    if venus_house in _DUSTHANA:
        venus_late += 1
        reasons.append(f"L3: Venus in {venus_house}H dusthana (+1 LATE)")
    if venus_dignity == "debilitated":
        venus_late += 1
        reasons.append("L3: Venus debilitated (+1 LATE) [NEW 2.8.68]")
    if venus_late > 2:
        reasons.append(f"L3 cap: Venus weakness capped at +2 "
                       f"(raw {venus_late})")
        venus_late = 2
    late += venus_late

    # ── E1: Jupiter aspect/conjunct 7H or 7L
    # Phase 2.8.69 FIX D — gate Jupiter blessing on Jupiter strength.
    # Pehle debilitated/combust Jupiter bhi +1 EARLY deta tha (false
    # optimism). Ab weak Jupiter ka blessing suppress hota hai:
    #   debilitated  → 0 EARLY (blessing weak)
    #   combust      → 0 EARLY (blessing burnt)
    #   dusthana 6/8/12 → +1 EARLY but log warning (compromised)
    #   normal/strong   → +1 EARLY (full blessing)
    jup_aff_7h = jup_si is not None and (
        jup_si == h7_si or _is_jupiter_aspect(jup_si, h7_si))
    jup_aff_7l = (jup_si is not None and seventh_lord_si is not None
                  and (jup_si == seventh_lord_si
                       or _is_jupiter_aspect(jup_si, seventh_lord_si)))
    if jup_aff_7h or jup_aff_7l:
        target = "7H" if jup_aff_7h else f"7L {seventh_lord}"
        if jup_dignity == "debilitated":
            reasons.append(f"E1 (skip): Jupiter aspect/conj {target} but "
                           "Jupiter debilitated — blessing too weak [2.8.69]")
        elif jup_combust:
            reasons.append(f"E1 (skip): Jupiter aspect/conj {target} but "
                           "Jupiter combust — blessing burnt [2.8.69]")
        elif jup_house in _DUSTHANA:
            early += 1
            reasons.append(f"E1: Jupiter aspect/conj {target} (+1 EARLY) "
                           f"— but Jupiter in {jup_house}H dusthana, "
                           "blessing compromised [2.8.69]")
        else:
            early += 1
            reasons.append(f"E1: natal Jupiter aspect/conj {target} "
                           "(+1 EARLY)")

    # ── E2: Venus exalted/own sign or in 5/7H
    if venus_dignity in ("exalted", "own", "moolatrikona"):
        early += 1
        reasons.append(f"E2: Venus {venus_dignity} (+1 EARLY)")
    elif venus_house in {5, 7}:
        early += 1
        reasons.append(f"E2: Venus in {venus_house}H — auspicious karaka (+1 EARLY)")

    # ── E5: 7H sign is cardinal (quick trigger)
    if h7_si in _CARDINAL_SIGNS:
        early += 1
        reasons.append(f"E5: 7H {_SIGNS[h7_si]} cardinal — quick trigger (+1 EARLY)")
    elif h7_si in _DUAL_SIGNS:
        late += 1
        reasons.append(f"E5 (inv): 7H {_SIGNS[h7_si]} dual — delays/multiples (+1 LATE)")

    # ── E6: 7L in kendra/trikona and not retro
    # Phase 2.8.68 FIX C — 7L retrograde now adds +1 LATE independently of
    # house placement (classical Vedic: retrograde 7L = delay signal).
    # Old behavior preserved: kendra/trikona placement still gives EARLY
    # only when not retro.
    if seventh_lord_h in _KENDRA_TRIKONA:
        if not seventh_lord_retro:
            early += 1
            reasons.append(f"E6: 7L {seventh_lord} in {seventh_lord_h}H kendra/trikona (+1 EARLY)")
        else:
            reasons.append(f"E6 (skip): 7L {seventh_lord} in {seventh_lord_h}H but retro — no EARLY")
    if seventh_lord_retro:
        late += 1
        reasons.append(f"L4: 7L {seventh_lord} retrograde — delay signal (+1 LATE) [NEW 2.8.68]")

    # ── Gender modifier (G1/G2)
    g = (gender or "").strip().lower()
    if g in ("m", "male", "man", "boy"):
        if venus_combust or venus_house in _DUSTHANA or venus_dignity == "debilitated":
            late += 1
            reasons.append("G1: male + Venus karaka weak (+1 LATE)")
    elif g in ("f", "female", "woman", "girl"):
        # Phase 2.8.69 — reuse hoisted jup_house / jup_dignity
        if jup_house in _DUSTHANA or jup_dignity == "debilitated":
            late += 1
            reasons.append("G2: female + Jupiter karaka weak (+1 LATE)")

    score = late - early
    if score >= 2:
        verdict = "LATE"
    elif score <= -2:
        verdict = "EARLY"
    else:
        verdict = "BALANCED"

    # ── Age-band overlay (hard-coded thresholds; gender-aware) ─────
    age_band = _age_band(current_age, gender) if current_age is not None else "UNKNOWN"
    late_status = _late_status(age_band, verdict)
    nearby, nearby_reason = _marriage_nearby(age_band, verdict)
    if current_age is not None and age_band != "UNKNOWN":
        reasons.append(f"AGE: current={current_age}y gender={gender or '?'} "
                       f"band={age_band} status={late_status}")
    elif current_age is not None:
        reasons.append(f"AGE: current={current_age}y but gender unknown — "
                       f"band/status skipped")
    if nearby:
        reasons.append(f"NEARBY: {nearby_reason}")

    return {
        "verdict": verdict,
        "score": score,
        "late_count": late,
        "early_count": early,
        "reasons": reasons,
        "current_age": current_age,
        "gender": gender or "",
        "age_band": age_band,
        "late_status": late_status,
        # Phase 2.8.62 — actionable "shadi nearby" signal for UI/narrator.
        "marriage_nearby":        nearby,
        "marriage_nearby_reason": nearby_reason,
        "age_thresholds": {
            "male":   {"early_max": _AGE_BANDS_MALE[0],
                        "normal_max": _AGE_BANDS_MALE[1],
                        "late_max": _AGE_BANDS_MALE[2],
                        "very_late_max": _AGE_BANDS_MALE[3]},
            "female": {"early_max": _AGE_BANDS_FEMALE[0],
                        "normal_max": _AGE_BANDS_FEMALE[1],
                        "late_max": _AGE_BANDS_FEMALE[2],
                        "very_late_max": _AGE_BANDS_FEMALE[3]},
        },
    }


# ════════════════════════════════════════════════════════════════════════
# SECTION 9 — Ashtakavarga bridge (STEP 4 BAV / SAV bonuses)
# ════════════════════════════════════════════════════════════════════════
def _compute_ashtakavarga_for_chart(planets: list,
                                      lagna_si: Optional[int]) -> dict:
    """Bridge -> ashtakavarga.compute_ashtakavarga(planets, lagna_sign_idx).

    Returns full result dict or {} on failure.
    """
    try:
        from ashtakavarga import compute_ashtakavarga   # type: ignore
        return compute_ashtakavarga(planets, lagna_si) or {}
    except Exception as exc:
        print(f"[marriage_timing._compute_ashtakavarga] failed: {exc}")
        return {}


def _bav_bonus(av: dict, planet: str, sign_si: Optional[int]) -> float:
    """BAV bindus of a planet at a given sign.

    Returns:
       +1.0 if bindus >= 5 (strong)
       +0.5 if bindus == 4 (above average)
        0.0 if bindus == 3 (neutral)
       -0.5 if bindus == 2 (weak)
       -1.0 if bindus <= 1 (very weak)
        0.0 if data missing
    """
    if not av or sign_si is None or not planet:
        return 0.0
    bav = av.get("bav") or {}
    arr = bav.get(planet)
    if not (isinstance(arr, list) and 0 <= sign_si < len(arr)):
        return 0.0
    b = int(arr[sign_si])
    if b >= 5:
        return 1.0
    if b == 4:
        return 0.5
    if b == 3:
        return 0.0
    if b == 2:
        return -0.5
    return -1.0


def _sav_bonus(av: dict, sign_si: Optional[int]) -> float:
    """SAV bindus at a given sign.

    Returns:
       +0.5 if SAV >= 30 (strong)
        0.0 if 25-29 (average)
       -0.5 if < 25 (weak)
    """
    if not av or sign_si is None:
        return 0.0
    sav = av.get("sav") or []
    if not (isinstance(sav, list) and 0 <= sign_si < len(sav)):
        return 0.0
    s = int(sav[sign_si])
    if s >= 30:
        return 0.5
    if s >= 25:
        return 0.0
    return -0.5


# ════════════════════════════════════════════════════════════════════════
# SECTION 10 — Eclipse window detection (STEP 4 delay flag)
# ════════════════════════════════════════════════════════════════════════
def _eclipse_in_window(start: datetime, end: datetime,
                        pad_days: int = 10) -> Tuple[bool, str]:
    """True if a solar or lunar eclipse falls within the window
    [start - pad_days, end + pad_days].

    Bridges -> vedic.transits.phase_h.find_recent_eclipses(when=mid).
    Returns (flag, reason_str). Eclipse adds delay/disturbance to
    marriage windows per classical KP (Rahu/Ketu activation).
    """
    try:
        from vedic.transits.phase_h import find_recent_eclipses   # type: ignore
        mid = start + (end - start) / 2
        ec = find_recent_eclipses(when=mid, back_years=1, fwd_years=1) or {}
        if not ec.get("available"):
            return (False, "")
        win_start = start - timedelta(days=pad_days)
        win_end = end + timedelta(days=pad_days)
        for key, label in (("solar_back", "Solar"), ("solar_fwd", "Solar"),
                            ("lunar_back", "Lunar"), ("lunar_fwd", "Lunar")):
            blk = ec.get(key) or {}
            d = blk.get("date")
            if not d:
                continue
            try:
                ed = datetime.strptime(str(d)[:10], "%Y-%m-%d")
            except ValueError:
                continue
            if win_start <= ed <= win_end:
                return (True, f"{label} eclipse {d} within window")
        return (False, "")
    except Exception as exc:
        print(f"[marriage_timing._eclipse_in_window] failed: {exc}")
        return (False, "")


# ════════════════════════════════════════════════════════════════════════
# SECTION 11 — Dasha Sandhi detection (STEP 4 HIGH WEIGHT activation)
# ════════════════════════════════════════════════════════════════════════
def _is_in_md_sandhi(kundli: dict, when: datetime,
                      sandhi_days: int = 183) -> Tuple[bool, str]:
    """True if `when` is within sandhi_days of MD start or end.

    MD sandhi (transition zone) is the HIGHEST-WEIGHT activation factor
    in VIVAH-7 (+1.5 to score). Per classical KSK + experiential patterns,
    marriage and major life events disproportionately fire in MD sandhi
    windows because the karmic transition releases pending karma.
    """
    if not isinstance(kundli, dict):
        return (False, "")
    dashas = kundli.get("dashas") or []
    if not isinstance(dashas, list):
        return (False, "")
    when_d = when.date() if isinstance(when, datetime) else when
    for md in dashas:
        if not isinstance(md, dict):
            continue
        sd = md.get("startDate") or md.get("start")
        ed = md.get("endDate") or md.get("end")
        if not (sd and ed):
            continue
        try:
            sd_d = datetime.strptime(str(sd)[:10], "%Y-%m-%d").date()
            ed_d = datetime.strptime(str(ed)[:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        if sd_d <= when_d <= ed_d:
            from_start = (when_d - sd_d).days
            from_end = (ed_d - when_d).days
            md_lord = md.get("planet") or md.get("md_lord") or "?"
            if from_start <= sandhi_days:
                return (True, f"{md_lord} MD entry sandhi ({from_start}d in)")
            if from_end <= sandhi_days:
                return (True, f"{md_lord} MD exit sandhi ({from_end}d to next)")
            return (False, "")
    return (False, "")


# ════════════════════════════════════════════════════════════════════════
# SECTION 12 — Planet helpers (retrograde, dignity, combust, strength)
# ════════════════════════════════════════════════════════════════════════
def _planet_record(planets: list, name: str) -> Optional[dict]:
    if not name:
        return None
    for p in (planets or []):
        if isinstance(p, dict) and p.get("name") == name:
            return p
    return None


def _planet_sign_idx(planets: list, name: str) -> Optional[int]:
    rec = _planet_record(planets, name)
    if not rec:
        return None
    si = rec.get("sign_idx")
    if isinstance(si, int):
        return si % 12
    sign = rec.get("sign")
    if isinstance(sign, str) and sign in _SIGNS:
        return _SIGNS.index(sign)
    return None


def _planet_house_local(planets: list, name: str) -> Optional[int]:
    rec = _planet_record(planets, name)
    if not rec:
        return None
    h = rec.get("house")
    if isinstance(h, int):
        return h
    return None


def _planet_is_retrograde(planets: list, name: str) -> bool:
    """True if named planet is retrograde (Sun/Moon excluded)."""
    if name in ("Sun", "Moon", "Rahu", "Ketu"):
        return False  # Rahu/Ketu are always retrograde — neutral here
    rec = _planet_record(planets, name)
    if not rec:
        return False
    return bool(rec.get("retrograde") or rec.get("isRetro"))


_EXALT_SIGN: Dict[str, int] = {  # planet -> sign idx of exaltation
    "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3,
    "Venus": 11, "Saturn": 6, "Rahu": 1, "Ketu": 7,
}
_DEBIL_SIGN: Dict[str, int] = {  # planet -> sign idx of debilitation (180° from exalt)
    "Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11, "Jupiter": 9,
    "Venus": 5, "Saturn": 0, "Rahu": 7, "Ketu": 1,
}
_OWN_SIGNS: Dict[str, Set[int]] = {
    "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
    "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
}

def _planet_dignity(planets: list, name: str) -> str:
    """Return dignity: exalted | own | debilitated | neutral | "".

    Prefer raw field if upstream populated; else compute deterministically
    from sign index using classical exalt/debil/own tables.
    """
    rec = _planet_record(planets, name)
    if not rec:
        return ""
    d = rec.get("dignity") or rec.get("dignityState") or ""
    if d:
        return str(d).strip().lower()
    # Fallback: compute from sign
    si = _planet_sign_idx(planets, name)
    if si is None:
        return ""
    if _EXALT_SIGN.get(name) == si:
        return "exalted"
    if _DEBIL_SIGN.get(name) == si:
        return "debilitated"
    if si in _OWN_SIGNS.get(name, set()):
        return "own"
    return "neutral"


def _is_combust_local(planets: list, name: str) -> bool:
    """True if planet is combust (close to Sun)."""
    rec = _planet_record(planets, name)
    if not rec:
        return False
    if rec.get("combust") is True:
        return True
    if rec.get("isCombust") is True:
        return True
    return False


def _dasha_lord_strength(planets: list, lord: str) -> float:
    """Return multiplier 0.5 - 1.3 for a dasha lord based on dignity + retro.

    Per VIVAH-7 STEP 6.2: weak dasha lord can't fire even if dasha is
    "right". Multiplier scales the entire window score.

    Mapping:
      exalted        -> 1.3
      moolatrikona   -> 1.2
      own sign       -> 1.15
      friend         -> 1.05
      neutral / unk  -> 1.0
      enemy          -> 0.85
      debilitated    -> 0.5
    Combust further -0.1, retrograde further -0.05 (floor 0.5).
    """
    if not lord:
        return 1.0
    d = _planet_dignity(planets, lord)
    base_map = {
        "exalted": 1.3, "moolatrikona": 1.2, "own": 1.15,
        "friend": 1.05, "neutral": 1.0, "enemy": 0.85,
        "debilitated": 0.5,
    }
    base = base_map.get(d, 1.0)
    if _is_combust_local(planets, lord):
        base -= 0.1
    if _planet_is_retrograde(planets, lord):
        base -= 0.05
    return max(0.5, min(1.3, base))


# ════════════════════════════════════════════════════════════════════════
# SECTION 12.5 — Window clustering (Phase 2.8.75 FIX J)
# ════════════════════════════════════════════════════════════════════════
def _merge_adjacent_windows(windows: List[dict],
                             gap_days: int = 15) -> List[dict]:
    """Merge candidate windows whose start is within gap_days of the
    previous window's end. Real marriage events cluster — single event
    activates 2-3 adjacent PDs. Without merging, user sees ONE event as
    3 separate predictions.

    Merge rules (ADD-ONLY safe — does NOT touch dasha/planet data):
      - extend `end` to max of cluster
      - keep highest score; that entry's MD/AD/PD becomes primary
      - concat factors with cluster header
      - set merged_count >= 2 for downstream display
    """
    if not windows:
        return []
    if len(windows) < 2:
        out = dict(windows[0])
        out["merged_count"] = 1
        return [out]
    sorted_w = sorted(windows, key=lambda w: w["start"])
    merged: List[dict] = [dict(sorted_w[0])]
    merged[0]["merged_count"] = 1
    for w in sorted_w[1:]:
        last = merged[-1]
        gap = (w["start"] - last["end"]).days
        if gap <= gap_days:
            last["end"] = max(last["end"], w["end"])
            if w["score"] > last["score"]:
                # higher-score window becomes primary
                for k in ("score", "raw_base", "strength_mult",
                           "md", "ad", "pd",
                           "jup", "sat", "double_transit",
                           "mars_trigger", "mars_sat_conflict",
                           "sandhi", "eclipse_flag"):
                    if k in w:
                        last[k] = w[k]
            last["factors"] = (last.get("factors", [])
                               + [f"--- merged with PD {w.get('pd')} "
                                  f"({gap}d gap) ---"]
                               + w.get("factors", []))
            last["merged_count"] = last.get("merged_count", 1) + 1
        else:
            new = dict(w)
            new["merged_count"] = 1
            merged.append(new)
    return merged


# ════════════════════════════════════════════════════════════════════════
# SECTION 13 — Internal utilities
# ════════════════════════════════════════════════════════════════════════
def _parse_dt(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str) and len(value) >= 10:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d"):
            try:
                return datetime.strptime(value[:len(fmt) + 8 if "T" in fmt else len(fmt)], fmt)
            except (ValueError, TypeError):
                continue
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d")
        except Exception:
            return None
    return None


_MONTHS = ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"]


def _format_window(start: datetime, end: datetime) -> str:
    try:
        s_m = _MONTHS[start.month - 1]
        e_m = _MONTHS[end.month - 1]
        if start.year == end.year:
            if start.month == end.month:
                return f"{s_m} {start.year}"
            return f"{s_m} - {e_m} {start.year}"
        return f"{s_m} {start.year} - {e_m} {end.year}"
    except Exception:
        return f"{start} - {end}"


def _extract_birth_year(birth: Any) -> Optional[int]:
    if not isinstance(birth, dict):
        return None
    for k in ("year", "birth_year", "yr"):
        v = birth.get(k)
        if v:
            try:
                return int(v)
            except (TypeError, ValueError):
                pass
    for k in ("date", "dob", "birth_date", "birthDate"):
        v = birth.get(k)
        if isinstance(v, str) and len(v) >= 4:
            try:
                return int(v[:4])
            except ValueError:
                pass
    return None


def _extract_birth_date(birth: Any):
    """Phase 2.8.76 (FIX O): return birth date as datetime.date for
    month-precise age math. Falls back to None if not derivable.

    Tries: explicit y/m/d fields first, then YYYY-MM-DD style strings.
    """
    from datetime import date as _date  # local import to keep top clean
    if not isinstance(birth, dict):
        return None
    # Path 1: explicit y/m/d
    y = None
    for k in ("year", "birth_year", "yr"):
        v = birth.get(k)
        if v:
            try:
                y = int(v); break
            except (TypeError, ValueError):
                pass
    m = None
    for k in ("month", "birth_month", "mon"):
        v = birth.get(k)
        if v:
            try:
                m = int(v); break
            except (TypeError, ValueError):
                pass
    d = None
    for k in ("day", "birth_day", "dd"):
        v = birth.get(k)
        if v:
            try:
                d = int(v); break
            except (TypeError, ValueError):
                pass
    if y and m and d:
        try:
            return _date(y, m, d)
        except ValueError:
            pass
    # Path 2: parse YYYY-MM-DD style string
    for k in ("date", "dob", "birth_date", "birthDate"):
        v = birth.get(k)
        if isinstance(v, str) and len(v) >= 10:
            try:
                return _date(int(v[0:4]), int(v[5:7]), int(v[8:10]))
            except (ValueError, IndexError):
                pass
    return None


def _precise_age_at(birth_date, target_date) -> Optional[float]:
    """Phase 2.8.76 (FIX O): fractional age in years between two dates.

    Returns None if either input missing. Uses 365.25 to absorb leap years.
    """
    if birth_date is None or target_date is None:
        return None
    try:
        delta_days = (target_date - birth_date).days
        return delta_days / 365.25
    except Exception:
        return None


def _extract_gender(birth: Any, intel: dict) -> str:
    """Try multiple sources for devotee's gender."""
    for src in (birth, intel):
        if not isinstance(src, dict):
            continue
        for k in ("gender", "sex", "lingam"):
            v = src.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return ""


# ════════════════════════════════════════════════════════════════════════
# PUBLIC API — VIVAH-7 PROTOCOL ORCHESTRATOR (Phase 2.8.52)
# ════════════════════════════════════════════════════════════════════════
def compute_timing_window(kundli: dict, intel: dict, kp: dict,
                          birth: Optional[Any] = None) -> dict:
    """Run the full VIVAH-7 KP-first marriage-timing pipeline.

    Returns dict (see module docstring for shape). Returns
    {"verdict": "UNKNOWN", "factors": [...]} when inputs are too thin
    (no planets, no lagna_sign, etc.) — never raises.
    """
    factors: List[str] = []

    def _empty(reason: str) -> dict:
        return {
            "verdict": "UNKNOWN", "band": "WEAK",
            "primary_window": None, "backup_window": None,
            "key_trigger": None, "confluence_strength": None,
            "ul_outlook": None,
            "risk_flag": None, "risk_flags": [],
            "factors": [reason],
            "top_3_windows": [],
            "step0_tendency": {"verdict": "BALANCED", "score": 0,
                                "reasons": []},
        }

    # ── Common input extraction ────────────────────────────────────
    if not isinstance(kundli, dict) or not isinstance(intel, dict):
        return _empty("Insufficient input: missing kundli/intel")

    planets = kundli.get("planets") or []
    if not planets:
        return _empty("Insufficient input: empty planets list")

    lagna_lon = kundli.get("lagna_lon")
    if lagna_lon is None:
        for k in ("ascendantDeg", "lagnaDeg", "ascDeg"):
            v = kundli.get(k)
            if isinstance(v, (int, float)):
                lagna_lon = float(v)
                break

    lagna_sign = (intel.get("lagna_sign") or "").strip()
    if not lagna_sign:
        for k in ("ascendant", "ascSign", "lagnaSign", "lagna_sign"):
            v = kundli.get(k)
            if isinstance(v, str) and v.strip() in _SIGNS:
                lagna_sign = v.strip()
                break

    lagna_si = _SIGNS.index(lagna_sign) if lagna_sign in _SIGNS else None
    moon_si = _planet_sign_idx(planets, "Moon")
    venus_si = _planet_sign_idx(planets, "Venus")
    h7_si = ((lagna_si + 6) % 12) if lagna_si is not None else None
    current_dasha = kundli.get("currentDasha") or kundli.get("current_dasha") or {}
    gender = _extract_gender(birth, intel)

    # 7L lord lookup — prefer intel.house_lords; FALLBACK to 7H sign-lord
    # (computed from h7_si via _SIGN_LORDS) when intel is incomplete.
    # This single source-of-truth feeds STEP 0/3/4 + add-on diagnostics.
    seventh_lord = None
    for hl in (intel.get("house_lords") or []):
        if isinstance(hl, dict) and hl.get("house") == 7:
            seventh_lord = hl.get("lord")
            break
    if not seventh_lord and h7_si is not None:
        seventh_lord = _SIGN_LORDS.get(h7_si)  # canonical fallback
    seventh_lord_si = _planet_sign_idx(planets, seventh_lord) if seventh_lord else None
    seventh_lord_house = _planet_house_local(planets, seventh_lord) if seventh_lord else None
    if seventh_lord:
        factors.append(f"7L resolved: {seventh_lord} in "
                       f"{_SIGNS[seventh_lord_si] if seventh_lord_si is not None else '?'}"
                       f" H{seventh_lord_house or '?'}"
                       f"{' [from intel]' if intel.get('house_lords') else ' [fallback from 7H sign-lord]'}")

    # Compute Ashtakavarga ONCE (used many times in STEP 4)
    av = _compute_ashtakavarga_for_chart(planets, lagna_si)

    # ════════════════════════════════════════════════════════════════
    # STEP 0 — Late vs Early Tendency Check
    # ════════════════════════════════════════════════════════════════
    current_age = _compute_current_age(birth)
    step0 = _step0_late_early_tendency(
        planets, intel, kp, lagna_si, h7_si,
        seventh_lord, venus_si, gender, current_age)
    factors.append(f"STEP 0: tendency={step0['verdict']} "
                   f"(LATE={step0['late_count']} EARLY={step0['early_count']} "
                   f"net={step0['score']})")

    # ════════════════════════════════════════════════════════════════
    # STEP 1 — KP Filter (FIRST GATE — sublord = FINAL ARBITER)
    # Phase 2.8.63 (May 3 2026) — user-locked spec:
    #   Method A (chain-union, Deny={6,8,12}) REMOVED entirely.
    #   Method B (strict sub-lord, Promise={2,7,11},
    #             Deny={1,6,8,10,12}) is the ONLY filter from now on.
    # Phase 2.8.71 (May 3 2026) — FIX F: SINGLE SOURCE OF TRUTH.
    #   Old parallel inline verdict logic REMOVED. Now uses canonical
    #   pipeline:
    #     compute_kp_gate_decision()
    #       ├─ compute_kp_sublord_marriage_filter() — 9-planet consensus
    #       │     + contradiction guard + FIX E NL tie-breaker
    #       └─ birth_time_confidence overlay (Phase 2.8.67 NOW LIVE)
    #   Star Lord (cusp NL) cross-check retained for downstream strength
    #   scoring + risk flags, but does NOT alter the unified kp_gate.
    # ════════════════════════════════════════════════════════════════
    btc = extract_birth_time_confidence(birth)
    gate = compute_kp_gate_decision(kp, btc) or {}
    kp_filter_full = gate.get("kp_filter") or {}

    # Pull csl planet + filter from the unified pipeline output (the
    # filter ran ONCE inside compute_kp_gate_decision; no double-compute).
    csl7 = (kp_filter_full.get("csl_planet") or _get_7csl(kp)) or ""
    _csl_fallback = {
        "planet": csl7 or None, "verdict": "UNKNOWN", "sub_lord": None,
        "sb_houses": [], "promise_hits": [], "deny_hits": [],
        "reason": "no 7CSL", "star_lord": None, "nl_houses": [],
        "nl_promise_hits": [], "nl_deny_hits": [],
        "nl_tiebreak_applied": False, "raw_sb_verdict": "UNKNOWN",
    }
    csl_filter = kp_filter_full.get("csl_filter") or _csl_fallback

    # 7C STAR LORD (cusp NL) — independent diagnostic cross-check.
    # NOTE: This is the 7th cusp's Nakshatra Lord (a planet name from
    # cusps[6].nl) — distinct from each planet's own NL used in FIX E.
    # Retained for downstream strength scoring + risk flags only.
    starlord = _get_7c_star_lord(kp)
    _star_fallback = {
        "planet": starlord or None, "verdict": "UNKNOWN", "sub_lord": None,
        "sb_houses": [], "promise_hits": [], "deny_hits": [],
        "reason": "no star lord", "star_lord": None, "nl_houses": [],
        "nl_promise_hits": [], "nl_deny_hits": [],
        "nl_tiebreak_applied": False, "raw_sb_verdict": "UNKNOWN",
    }
    star_filter = (_kp_sublord_filter_planet(kp, starlord)
                   if starlord else _star_fallback)

    # Map Method B per-planet verdicts {STRONG/MIXED/WEAK/UNKNOWN} ->
    # legacy gate vocabulary {PROMISED/MIXED/DENIED/UNKNOWN} for
    # downstream consumers (strength scoring, risk flags).
    def _b_to_gate(v: str) -> str:
        if v == "STRONG":  return "PROMISED"
        if v == "WEAK":    return "DENIED"
        if v == "MIXED":   return "MIXED"
        return "UNKNOWN"

    csl_verdict  = _b_to_gate(csl_filter.get("verdict") or "UNKNOWN")
    star_verdict = _b_to_gate(star_filter.get("verdict") or "UNKNOWN")
    csl_signs    = csl_filter.get("sb_houses") or []
    star_signs   = star_filter.get("sb_houses") or []

    # UNIFIED kp_gate from compute_kp_gate_decision (single source of
    # truth). final_label encodes 9-planet consensus + contradiction
    # guard + birth-time-confidence overlay. Map back to legacy
    # {PROMISED/DENIED/DELAYED/MIXED} vocabulary so downstream
    # combination logic (L2700+) stays untouched.
    _LABEL_TO_GATE = {
        "PROMISED":               "PROMISED",
        "DELAYED":                "DELAYED",
        "DENIED":                 "DENIED",
        "DENIED_LOW_CONFIDENCE":  "DELAYED",  # proceed-but-lean-denial
        "UNKNOWN":                "MIXED",
    }
    final_label = gate.get("final_label") or "UNKNOWN"
    kp_gate = _LABEL_TO_GATE.get(final_label, "MIXED")

    # STEP 1 narration — surfaces FIX E (NL tie-breaker) + Phase 2.8.67
    # confidence fields for LLM transparency.
    _csl_nl_note = (f" [NL tie-break {csl_filter.get('star_lord')} applied]"
                    if csl_filter.get("nl_tiebreak_applied") else "")
    _star_nl_note = (f" [NL tie-break {star_filter.get('star_lord')} applied]"
                     if star_filter.get("nl_tiebreak_applied") else "")
    factors.append(f"STEP 1 KP: 7CSL={csl7 or 'n/a'} SB={csl_filter.get('sub_lord') or 'n/a'} "
                   f"basic_houses={csl_signs} promise={csl_filter.get('promise_hits')} "
                   f"deny={csl_filter.get('deny_hits')} -> {csl_verdict}{_csl_nl_note}")
    factors.append(f"STEP 1 KP: 7C StarLord={starlord or 'n/a'} SB={star_filter.get('sub_lord') or 'n/a'} "
                   f"basic_houses={star_signs} promise={star_filter.get('promise_hits')} "
                   f"deny={star_filter.get('deny_hits')} -> {star_verdict}{_star_nl_note}")
    buckets = (kp_filter_full.get("buckets") or
               {"strong": [], "mixed": [], "weak": [], "unknown": []})
    factors.append(f"STEP 1 KP CONSENSUS: {len(buckets.get('strong',[]))} strong, "
                   f"{len(buckets.get('mixed',[]))} mixed, "
                   f"{len(buckets.get('weak',[]))} weak; "
                   f"strength={gate.get('kp_strength','WEAK')} "
                   f"raw_verdict={gate.get('kp_verdict','UNKNOWN')}")
    factors.append(f"STEP 1 KP CONFIDENCE: btc={btc} "
                   f"action={gate.get('gate_action','PROCEED')} "
                   f"final_label={final_label} "
                   f"allow_scan={gate.get('allow_timing_scan',True)} "
                   f"low_conf={gate.get('low_confidence_mode',False)}")
    if gate.get("disclaimer"):
        factors.append(f"STEP 1 KP DISCLAIMER: {gate['disclaimer']}")
    factors.append(f"STEP 1 KP GATE: {kp_gate}")

    # HARD-STOP wiring (Phase 2.8.71 FIX F) — when birth time is
    # confident AND KP is DENIED, skip the entire downstream scan.
    # Phase 2.8.67's confidence wrapper now actually fires in production.
    if not gate.get("allow_timing_scan", True):
        return {
            "verdict": "DENIED",
            "band": "WEAK",
            "primary_window": None,
            "backup_window": None,
            "key_trigger": None,
            "confluence_strength": None,
            "ul_outlook": None,
            "risk_flag": "KP hard denial",
            "risk_flags": ["KP hard denial"],
            "factors": factors,
            "top_3_windows": [],
            "step0_tendency": {
                "verdict": step0.get("verdict", "BALANCED"),
                "score": step0.get("score", 0),
                "reasons": step0.get("reasons", []),
            },
            "kp_gate_meta": {
                "btc": btc,
                "gate_action": gate.get("gate_action"),
                "final_label": final_label,
                "low_confidence_mode": gate.get("low_confidence_mode", False),
                "disclaimer": gate.get("disclaimer"),
            },
        }

    # ════════════════════════════════════════════════════════════════
    # STEP 2 — D1 + D9 Cross-Validation
    # Phase 2.8.73 (May 3 2026) — FIX H WIRING:
    #   compute_step2_link_filter() now LIVE in production pipeline.
    #   Provides per-planet weighted-link verdicts (FIX G) + buckets
    #   {approvers, conditional, deniers, ignore}. Approver bucket is
    #   used downstream to filter STEP 4 dasha-scan target_lords.
    #   Old inline 3-check (7L/Venus/Manglik dusthana) RETAINED below
    #   as supplementary chart-level signal feeding strength scoring;
    #   does NOT override the new buckets.
    # ════════════════════════════════════════════════════════════════
    try:
        step2 = compute_step2_link_filter(kundli, kp) or {}
    except Exception as exc:
        print(f"[marriage_timing STEP 2 wire] compute_step2_link_filter failed: {exc}")
        step2 = {}
    step2_buckets = step2.get("buckets") or {
        "approvers": [], "conditional": [], "deniers": [], "ignore": []
    }
    approver_planets: Set[str] = set(step2_buckets.get("approvers") or [])
    denier_planets:   Set[str] = set(step2_buckets.get("deniers")   or [])
    factors.append(f"STEP 2 LINK FILTER: approvers={sorted(approver_planets)} "
                   f"deniers={sorted(denier_planets)} "
                   f"conditional={step2_buckets.get('conditional', [])}")

    venus_house = _planet_house_local(planets, "Venus")
    manglik_status = _get_manglik(planets)

    d1_score = 0
    if seventh_lord_house and seventh_lord_house not in _DUSTHANA:
        d1_score += 1
        factors.append(f"STEP 2 D1: 7L ({seventh_lord}) in {seventh_lord_house}H OK")
    else:
        factors.append(f"STEP 2 D1 FLAG: 7L ({seventh_lord}) in {seventh_lord_house}H (dusthana/missing)")

    if venus_house and venus_house not in _DUSTHANA:
        d1_score += 1
        factors.append(f"STEP 2 D1: Venus karaka in {venus_house}H OK")
    else:
        factors.append(f"STEP 2 D1 FLAG: Venus karaka in {venus_house}H (weak)")

    if manglik_status not in ("Active",):
        d1_score += 1
        factors.append(f"STEP 2 D1: Manglik={manglik_status}")
    else:
        factors.append("STEP 2 D1 FLAG: Manglik=Active")

    # D9 Confirmation
    d9 = _get_d9_chart(planets, lagna_lon) if lagna_lon is not None else _get_d9_chart(planets)
    if isinstance(d9, dict) and isinstance(d9.get("planets"), dict):
        d9_planets = d9["planets"]
    else:
        d9_planets = d9 if isinstance(d9, dict) else {}
    if not d9_planets:
        factors.append("STEP 2 D9 NOTE: navamsa unavailable")
    venus_d9_sign = (d9_planets.get("Venus") or {}).get("sign", "")
    seventh_lord_d9_sign = (d9_planets.get(seventh_lord) or {}).get("sign", "") if seventh_lord else ""
    venus_vargottama = bool((d9_planets.get("Venus") or {}).get("vargottama"))

    d9_bonus = 0
    if venus_d9_sign and venus_d9_sign != "Virgo":
        d9_bonus += 1
        factors.append(f"STEP 2 D9: Venus in {venus_d9_sign}"
                       + (" (vargottama)" if venus_vargottama else ""))
    elif venus_d9_sign:
        factors.append(f"STEP 2 D9 FLAG: Venus debilitated in {venus_d9_sign}")
    if seventh_lord_d9_sign:
        d9_bonus += 1
        factors.append(f"STEP 2 D9: 7L ({seventh_lord}) in {seventh_lord_d9_sign}")

    # ════════════════════════════════════════════════════════════════
    # STEP 3 — Redemption (own 7L / vargottama Venus rescue)
    # ════════════════════════════════════════════════════════════════
    redemption = 0
    redemption_reasons: List[str] = []
    # R1: 7L in own sign
    if (seventh_lord and seventh_lord_si is not None
            and _SIGN_LORDS.get(seventh_lord_si) == seventh_lord):
        redemption += 1
        redemption_reasons.append(f"R1: 7L {seventh_lord} in own sign {_SIGNS[seventh_lord_si]} (+1)")
    # R2: Venus vargottama
    if venus_vargottama:
        redemption += 1
        redemption_reasons.append("R2: Venus vargottama in D9 (+1)")
    # R3: 7L in dignity (Phase 2.8.74 FIX I — expanded from "exalted"-only
    # to {exalted, own, moolatrikona}. Catches strong 7L cases previously
    # missed when 7L was in own sign or moolatrikona.)
    seventh_lord_dignity = _planet_dignity(planets, seventh_lord)
    if seventh_lord_dignity in ("exalted", "own", "moolatrikona"):
        redemption += 1
        redemption_reasons.append(
            f"R3: 7L {seventh_lord} {seventh_lord_dignity} (+1)")
    # R4: Strong 7H Sarvashtakavarga (>= 30)
    sav_h7 = _sav_bonus(av, h7_si)
    if sav_h7 > 0:
        redemption += 1
        redemption_reasons.append(f"R4: 7H SAV strong ({_SIGNS[h7_si]}) (+1)")

    # ── Phase 2.8.74 FIX I — Negative weighting (rescue cap, anti-bias)
    # Pure-additive STEP 3 was over-rescuing DENIED charts that had real
    # afflictions. Penalty checks now offset rescue points so chart-level
    # weakness can cancel positives. Floor at 0 prevents underflow into
    # strength scoring (band still computed from non-negative redemption).
    redemption_penalty = 0
    redemption_penalty_reasons: List[str] = []
    # P1: 7L debilitated natally
    if seventh_lord_dignity == "debilitated":
        redemption_penalty += 1
        redemption_penalty_reasons.append(
            f"P1: 7L {seventh_lord} debilitated (-1)")
    # P2: Venus combust
    if _is_combust_local(planets, "Venus"):
        redemption_penalty += 1
        redemption_penalty_reasons.append("P2: Venus combust (-1)")
    # P3: 7H SAV weak (< 25 -> _sav_bonus returns -0.5)
    if sav_h7 < 0:
        redemption_penalty += 1
        redemption_penalty_reasons.append(
            f"P3: 7H SAV weak ({_SIGNS[h7_si]}) (-1)")

    redemption_raw = redemption
    redemption = max(0, redemption_raw - redemption_penalty)

    for r in redemption_reasons:
        factors.append(f"STEP 3 REDEMPTION: {r}")
    for p in redemption_penalty_reasons:
        factors.append(f"STEP 3 PENALTY: {p}")
    if redemption_penalty > 0:
        factors.append(
            f"STEP 3 NET: rescue={redemption_raw} penalty={redemption_penalty}"
            f" -> effective={redemption}")
    if not redemption_reasons and not redemption_penalty_reasons:
        factors.append("STEP 3 REDEMPTION: no rescue or penalty factors")

    # ── Combine STEP 1+2+3 -> final verdict
    # KP is primary, D1+D9 cross-validate, redemption can promote
    parashari_strength = d1_score + d9_bonus  # max 5
    if kp_gate == "PROMISED":
        if parashari_strength >= 2:
            final_verdict = "PROMISED"
        else:
            final_verdict = "DELAYED"
            factors.append("CROSS-VAL: KP says PROMISED but Parashari weak -> DELAYED")
    elif kp_gate == "DENIED":
        if redemption >= 2:
            final_verdict = "DELAYED"
            factors.append(f"REDEMPTION RESCUE: KP DENIED upgraded to DELAYED ({redemption} factors)")
        else:
            final_verdict = "DENIED"
    elif kp_gate == "DELAYED":
        final_verdict = "DELAYED"
        if parashari_strength >= 4 and redemption >= 1:
            final_verdict = "PROMISED"
            factors.append("PROMOTE: strong Parashari + redemption -> PROMISED")
    else:  # MIXED / UNKNOWN
        if parashari_strength >= 3:
            final_verdict = "PROMISED"
        elif parashari_strength >= 2:
            final_verdict = "DELAYED"
        else:
            final_verdict = "DELAYED"

    # Strength band — combines all 3 steps
    csl_pts = {"PROMISED": 2, "MIXED": 1, "UNKNOWN": 0, "DENIED": 0}.get(csl_verdict, 0)
    star_pts = {"PROMISED": 1, "MIXED": 0, "UNKNOWN": 0, "DENIED": 0}.get(star_verdict, 0)
    strength = d1_score + d9_bonus + csl_pts + star_pts + redemption
    # max possible: 3 (D1) + 2 (D9) + 2 (CSL) + 1 (Star) + 4 (Redemp) = 12
    if strength >= 8:
        band = "STRONG"
    elif strength >= 5:
        band = "MEDIUM"
    else:
        band = "WEAK"

    # Risk flags — collect ALL
    risk_flags: List[str] = []
    if manglik_status == "Active":
        risk_flags.append("Manglik")
    if seventh_lord_house in _DUSTHANA:
        risk_flags.append("7L afflicted")
    if d1_score == 0:
        risk_flags.append("Karaka weak")
    if csl_verdict == "DENIED":
        risk_flags.append("KP 7CSL denial")
    if star_verdict == "DENIED":
        risk_flags.append("KP 7C StarLord denial")
    if step0["verdict"] == "LATE":
        risk_flags.append("Late tendency")
    risk_flag: Optional[str] = risk_flags[0] if risk_flags else None

    # Early-exit if denied — skip STEP 4/5
    if final_verdict == "DENIED":
        return {
            "verdict": "DENIED",
            "band": "WEAK",
            "primary_window": None,
            "backup_window": None,
            "key_trigger": None,
            "confluence_strength": None,
            "ul_outlook": None,
            "risk_flag": risk_flag or "Multiple denials",
            "risk_flags": risk_flags or ["Multiple denials"],
            "factors": factors,
            "top_3_windows": [],
            "step0_tendency": step0,
        }

    # ════════════════════════════════════════════════════════════════
    # STEP 4 — Dasha + Confluence (VIVAH-7 weighted scoring)
    # ════════════════════════════════════════════════════════════════
    target_lords = _marriage_target_lords(lagna_si) if lagna_si is not None else {"Venus", "Jupiter"}

    # Phase 2.8.73 FIX H — STEP 2 approver/denier filter on target_lords.
    # Only planets that passed both KP STEP 1 (STRONG/MIXED) AND have
    # meaningful D1/D9 link to 7H/7L survive into the dasha scan.
    # Karaka safety net: Venus/Jupiter retained if they're approvers.
    # Fallback: if no approver overlap, scan raw lords (avoid empty scan).
    raw_target_count = len(target_lords)
    raw_target_snapshot = set(target_lords)
    if approver_planets:
        filtered = set(target_lords) & approver_planets
        for karaka in ("Venus", "Jupiter"):
            if karaka in approver_planets:
                filtered.add(karaka)
        if filtered:
            target_lords = filtered
            factors.append(f"STEP 4 SCAN FILTER: {raw_target_count} raw lords -> "
                           f"{len(target_lords)} approver-filtered "
                           f"({sorted(target_lords)})")
        else:
            factors.append(f"STEP 4 SCAN FILTER: no approver overlap, "
                           f"falling back to raw {raw_target_count} lords")
    else:
        factors.append("STEP 4 SCAN FILTER: STEP 2 produced no approvers, "
                       "scanning raw target lords")

    # Phase 2.8.75 FIX K — SOFT denier weighting (replaces hard-drop).
    # Classical Vedic: Mars/Sat MD/AD CAN trigger marriage (delayed/conflict
    # cases). Hard removal causes false negatives. Instead retain in
    # target_lords but apply 0.7 score multiplier in scoring loop when
    # MD/AD lord itself is a flagged denier.
    denier_in_target: Set[str] = set()
    if denier_planets:
        denier_in_target = ((raw_target_snapshot & denier_planets)
                             - {"Venus", "Jupiter"})
        if denier_in_target:
            factors.append(f"STEP 4 DENIER SOFT-WEIGHT: "
                           f"{sorted(denier_in_target)} retained, "
                           f"x0.7 multiplier when MD/AD")

    # Final safety: ensure target_lords is never empty (engine invariant)
    if not target_lords:
        target_lords = {"Venus", "Jupiter"}
        factors.append("STEP 4 SAFETY: target_lords empty after filters, "
                       "defaulting to {Venus, Jupiter}")

    # Phase 2.8.81 USER PD-LEVEL ALGORITHM (ADD-ONLY):
    # Per user spec — "har AD ke andar har PD individually check karo,
    # favourable PD lord + transit match dono chahiye". Pehle AD-level pre-
    # filter Mars/Rahu/Ketu ADs ko entirely skip karta tha, jisse andar ke
    # favourable PDs (e.g. Mercury PD = 7L inside Mars AD) silently dropped
    # ho jaate the. Ab saare 9 planets ke ADs scan karte hain; PD-level filter
    # niche scan loop mein lagta hai.
    _ALL_DASHA_LORDS = {"Sun", "Moon", "Mars", "Mercury", "Jupiter",
                        "Venus", "Saturn", "Rahu", "Ketu"}
    candidate_ads = _scan_cluster_ads(kundli, _ALL_DASHA_LORDS,
                                      lookback_days=30)
    factors.append(f"STEP 4: target_lords={sorted(target_lords)}, "
                   f"candidate_ADs={len(candidate_ads)} "
                   f"(2.8.81: ALL ADs scanned, PD-level filter active)")

    # Phase 2.8.79 (FIX X, slimmed) — in urgency mode, ensure the currently-
    # running AD is scanned (even if its MD/AD lord isn't a target_lord), so
    # PD-level marriage triggers like Mercury(7L) inside Moon/Mars AD aren't
    # silently dropped. PD scoring gate (>=_WINDOW_MIN_SCORE) still filters.
    if _is_urgency_mode(_get_current_age(birth, kundli, current_dasha),
                        step0["verdict"], gender):
        cd = kundli.get("currentDasha") or {}
        md, ad = cd.get("maha") or cd.get("mahadasha"), cd.get("antar") or cd.get("antardasha")
        s, e = cd.get("startDate") or cd.get("start"), cd.get("endDate") or cd.get("end")
        if md and ad and s and e and not any(
            (a.get("md") or a.get("md_lord")) == md and
            (a.get("ad") or a.get("ad_lord")) == ad for a in candidate_ads
        ):
            candidate_ads.insert(0, {"md_lord": md, "ad_lord": ad, "start": s, "end": e})
            factors.append(f"STEP 4 URGENCY: injected current AD {md}/{ad}")

    today = datetime.utcnow()
    windows: List[dict] = []
    # Phase 2.8.80 USER HARD TRANSIT GATE counters
    gate_dtt_count = 0
    gate_single_count = 0
    gate_fail_count = 0
    # Phase 2.8.81 PD-LEVEL FILTER counter
    pd_filter_skipped = 0

    for ad_blk in candidate_ads:
        md = ad_blk.get("md") or ad_blk.get("md_lord")
        ad = ad_blk.get("ad") or ad_blk.get("ad_lord")
        ad_start = _parse_dt(ad_blk.get("start"))
        ad_end = _parse_dt(ad_blk.get("end"))
        if not (md and ad and ad_start and ad_end):
            continue

        ad_months = max(3, int((ad_end - ad_start).days / 30) + 1)
        from_dt = max(today, ad_start)
        if from_dt >= ad_end:
            continue
        pds = _project_pds(md, ad, ad_start, ad_end,
                           from_dt=from_dt, months_needed=ad_months)

        # Per-dasha-pair pre-computes (don't repeat per PD)
        md_strength = _dasha_lord_strength(planets, md)
        ad_strength = _dasha_lord_strength(planets, ad)
        strength_mult = (md_strength + ad_strength) / 2.0
        md_retro = _planet_is_retrograde(planets, md)
        ad_retro = _planet_is_retrograde(planets, ad)
        md_in_target = md in target_lords
        ad_in_target = ad in target_lords

        for pd_blk in pds:
            pd_start = pd_blk.get("start")
            pd_end = pd_blk.get("end")
            if not (isinstance(pd_start, datetime) and isinstance(pd_end, datetime)):
                continue
            pd_lord = pd_blk.get("pd")
            mid = pd_start + (pd_end - pd_start) / 2

            window_factors: List[str] = []

            # ── A. Hierarchical cluster scoring (Phase 2.8.75 FIX L)
            # Replaces binary cluster_hit + adpd_weight with proper
            # hierarchy: PD > AD > MD. Triple-promiser bonus for full
            # alignment. Per classical Vedic timing precision principle.
            md_pts = 1 if md_in_target else 0
            ad_pts = 2 if ad_in_target else 0
            pd_pts = 3 if pd_lord in target_lords else 0

            # Phase 2.8.81 PD-LEVEL HARD FILTER (ADD-ONLY) — per user spec:
            # "jab tak favourable PD nahi aata, check karte raho". PD lord
            # MUST be in target_lords (Jup/Mer/Sat/Ven by default), warna
            # is window ko skip karo aur next PD pe jao. Yeh AD-level pre-
            # filter ki absence ko compensate karta hai.
            if pd_pts == 0:
                pd_filter_skipped += 1
                continue

            cluster_score = md_pts + ad_pts + pd_pts   # range 0-6
            triple_bonus = 1 if (md_pts and ad_pts and pd_pts) else 0
            if cluster_score > 0:
                tags = []
                if md_pts: tags.append(f"MD={md}")
                if ad_pts: tags.append(f"AD={ad}")
                if pd_pts: tags.append(f"PD={pd_lord}")
                window_factors.append(f"+{cluster_score} cluster ({', '.join(tags)})")
            if triple_bonus:
                window_factors.append("+1 TRIPLE PROMISER bonus (MD+AD+PD all in target)")
            # Backward-compat aliases (downstream consumers expect these)
            cluster_hit = 2 if pd_pts else 1
            adpd_weight = cluster_score   # for diagnostic display

            # ── B. Transits (Jupiter, Saturn, Mars)
            transit = _get_transits_at(lagna_si, moon_si, when=mid) if lagna_si is not None else {}
            jup_score, jup_reason = _jupiter_score_on_7h(transit, h7_si, venus_si) if h7_si is not None else (0, "")
            sat_score, sat_reason = _saturn_score_on_7h(transit, h7_si, moon_si) if h7_si is not None else (0, "")
            if jup_reason:
                window_factors.append(f"+{jup_score} {jup_reason}")
            if sat_reason:
                window_factors.append(f"+{sat_score} {sat_reason}")

            # Double Transit bonus
            double_transit_bonus = 0
            if jup_score > 0 and sat_score > 0:
                double_transit_bonus = 1
                window_factors.append("DOUBLE TRANSIT bonus (+1)")

            # ── B2. Phase 2.8.80 USER HARD TRANSIT GATE (ADD-ONLY)
            # Per user spec: Jup+Sat must be on 7H sign or aspect natal 7L.
            # FAIL -> reject window (move to next favourable dasha).
            # SINGLE -> accept (no extra bonus, existing scores already counted).
            # DTT -> accept + classical double-transit bonus already added above.
            gate_tier, gate_reason = _user_transit_gate_check(
                transit, h7_si, seventh_lord_si)
            if gate_tier == "FAIL":
                gate_fail_count += 1
                continue   # hard reject per user rule, skip to next PD
            # Phase 2.8.81 GATE-BONUS (architect-flagged HIGH fix):
            # Gate accepts on Jup/Sat-aspecting-7L, but legacy
            # _jupiter_score_on_7h / _saturn_score_on_7h only credit 7H
            # contact. Without this bonus, gate-passed-via-7L windows could
            # silently fall below score threshold. Bonus surfaces them.
            gate_bonus = 0.0
            if gate_tier == "DTT":
                gate_dtt_count += 1
                gate_bonus = 1.0
                window_factors.append(f"GATE DTT: {gate_reason} (+1.0)")
            else:
                gate_single_count += 1
                gate_bonus = 0.5
                window_factors.append(f"GATE SINGLE: {gate_reason} (+0.5)")

            # ── C. Mars trigger (+1 activation only) + conflict flag
            mars_trig, mars_reason = _mars_trigger_check(
                transit, h7_si, venus_si, seventh_lord_si) if h7_si is not None else (False, "")
            mars_bonus = 0
            mars_sat_conflict = False
            if mars_trig:
                mars_bonus = 1
                window_factors.append(f"+1 Mars TRIGGER ({mars_reason})")
                if sat_score > 0:
                    # Phase 2.8.75 FIX M — conflict actually neutralizes
                    # mars_bonus (push vs delay cancel each other), not just
                    # a flag. Previously flag was set with no score impact.
                    mars_sat_conflict = True
                    mars_bonus = 0
                    window_factors.append("⚠ Mars+Saturn CONFLICT — Mars bonus neutralized (push vs delay)")

            # ── D. Retrograde penalty (MD/AD lord)
            retro_penalty = 0.0
            if md_retro:
                retro_penalty -= 0.5
                window_factors.append(f"-0.5 MD lord {md} retro")
            if ad_retro:
                retro_penalty -= 0.5
                window_factors.append(f"-0.5 AD lord {ad} retro")

            # ── E. Ashtakavarga BAV (Venus bindus in 7H sign)
            bav_b = _bav_bonus(av, "Venus", h7_si) if h7_si is not None else 0.0
            if bav_b != 0:
                window_factors.append(f"{bav_b:+} Venus BAV in 7H ({_SIGNS[h7_si]})")

            # ── F. SAV in 7H sign
            sav_b = _sav_bonus(av, h7_si) if h7_si is not None else 0.0
            if sav_b != 0:
                window_factors.append(f"{sav_b:+} 7H SAV")

            # ── G. Dasha Sandhi (HIGH WEIGHT +1.5)
            sandhi, sandhi_reason = _is_in_md_sandhi(kundli, mid)
            sandhi_bonus = 0.0
            if sandhi:
                sandhi_bonus = 1.5
                window_factors.append(f"+1.5 SANDHI ACTIVATION ({sandhi_reason})")

            # ── H. Eclipse delay flag
            ecl_flag, ecl_reason = _eclipse_in_window(pd_start, pd_end)
            eclipse_penalty = 0.0
            if ecl_flag:
                eclipse_penalty = -1.0
                window_factors.append(f"-1.0 ECLIPSE DELAY ({ecl_reason})")

            # ── TOTAL (Phase 2.8.75 FIX N — multiplier scope corrected).
            # OLD bug: `score = base * strength_mult` multiplied penalties
            # too. Strong lord (mult=1.3) -> retro -0.5 effectively -0.65.
            # Weak lord (mult=0.5) -> retro -0.25. Counter-intuitive.
            # NEW: strength_mult applies ONLY to positive components.
            # Penalties (retro, eclipse, negative AV) stay additive.
            positive_base = (cluster_score + triple_bonus
                             + jup_score + sat_score
                             + double_transit_bonus
                             + mars_bonus
                             + max(0.0, bav_b) + max(0.0, sav_b)
                             + sandhi_bonus
                             + gate_bonus)   # Phase 2.8.81
            penalties = (retro_penalty
                         + min(0.0, bav_b) + min(0.0, sav_b)
                         + eclipse_penalty)

            # Phase 2.8.75 FIX K — soft denier multiplier
            denier_mult = 1.0
            if md in denier_in_target or ad in denier_in_target:
                denier_mult = 0.7
                window_factors.append(
                    f"x0.7 denier soft-penalty "
                    f"(MD/AD has flagged denier: "
                    f"{sorted(denier_in_target & {md, ad})})")

            score = (positive_base * strength_mult * denier_mult) + penalties
            base = positive_base + penalties   # diagnostic only

            if score >= _WINDOW_MIN_SCORE:
                windows.append({
                    "start": pd_start,
                    "end": pd_end,
                    "score": round(score, 2),
                    "raw_base": round(base, 2),
                    "strength_mult": round(strength_mult, 2),
                    "md": md, "ad": ad, "pd": pd_lord,
                    "jup": jup_score > 0,
                    "sat": sat_score > 0,
                    "double_transit": jup_score > 0 and sat_score > 0,
                    "mars_trigger": mars_trig,
                    "mars_sat_conflict": mars_sat_conflict,
                    "sandhi": sandhi,
                    "eclipse_flag": ecl_flag,
                    "factors": window_factors,
                })

    factors.append(f"STEP 4: {len(windows)} candidate PD windows above threshold "
                   f"({_WINDOW_MIN_SCORE})")
    # Phase 2.8.80 USER HARD TRANSIT GATE summary
    factors.append(
        f"STEP 4 USER GATE: DTT={gate_dtt_count} SINGLE={gate_single_count} "
        f"FAIL={gate_fail_count} (rejected windows where neither Jup nor Sat "
        f"on 7H/7L)")
    # Phase 2.8.81 PD-LEVEL FILTER summary
    factors.append(
        f"STEP 4 PD FILTER: {pd_filter_skipped} PDs skipped "
        f"(PD lord not in target_lords {sorted(target_lords)})")
    if not windows and gate_fail_count > 0:
        factors.append(
            "STEP 4 USER GATE WARNING: ALL candidate windows rejected by "
            "transit gate — no DTT-confirmed marriage window in scan range. "
            "User-spec rule active: dasha + transit BOTH must support.")

    # Phase 2.8.75 FIX J — merge adjacent windows (≤15-day gap = same event)
    pre_merge_count = len(windows)
    windows = _merge_adjacent_windows(windows, gap_days=15)
    if pre_merge_count != len(windows):
        factors.append(f"STEP 4 CLUSTER MERGE: {pre_merge_count} -> "
                       f"{len(windows)} windows (adjacent within 15d merged)")

    # ════════════════════════════════════════════════════════════════
    # STEP 5 — Reality Filter (STEP 0-adjusted age table)
    # Phase 2.8.76 BATCH FIX O/P/Q/R/S/T:
    #   O: month-precise predicted_age (window mid-date vs birth date)
    #   P: BLOCK only on predicted_age (current age informational only)
    #   Q: PREMATURE downgrade extends to DELAYED verdict (not just PROMISED)
    #   R: score penalty for FLAG_LATE (-0.5) and FLAG_VERY_LATE (-1.5)
    #   S: top-3 AD-diversity selection (prefer different ADs within 1.0 score)
    #   T: confluence_strength: WEAK label below MEDIUM (instead of MODERATE)
    # ════════════════════════════════════════════════════════════════
    age = _get_current_age(birth, kundli, current_dasha)
    birth_year = _extract_birth_year(birth)
    birth_date_obj = _extract_birth_date(birth)  # FIX O
    thresholds = _adjusted_age_thresholds(step0["verdict"])
    # Phase 2.8.77 — URGENCY MODE detection (FIX U)
    urgency_mode = _is_urgency_mode(age, step0["verdict"], gender)
    factors.append(f"STEP 5: age={age} birth_year={birth_year} "
                   f"birth_date={birth_date_obj} "
                   f"thresholds={thresholds} (STEP 0 adj for {step0['verdict']})")
    if urgency_mode:
        factors.append(
            f"STEP 5 URGENCY MODE: ON (gender={gender or '?'}, age={age}, "
            f"step0=LATE) -> width clamp {_URGENCY_WIDTH_MONTHS}mo, "
            f"recency penalty {_URGENCY_RECENCY_PENALTY_PER_YEAR}/yr"
        )

    valid_windows: List[dict] = []
    blocked_count = 0
    late_penalty_count = 0
    width_clamped_count = 0
    for w in windows:
        # FIX O: prefer month-precise age via mid-window date; fallback to year-only
        predicted_age: Optional[float] = None
        if birth_date_obj is not None:
            try:
                w_start = w["start"].date() if hasattr(w["start"], "date") else w["start"]
                w_end = w["end"].date() if hasattr(w["end"], "date") else w["end"]
                mid = w_start + (w_end - w_start) / 2
                predicted_age = _precise_age_at(birth_date_obj, mid)
            except Exception:
                predicted_age = None
        if predicted_age is None and birth_year and birth_year > 0:
            predicted_age = float(w["start"].year - birth_year)

        action = (_age_filter_action(age, predicted_age, thresholds)
                  if predicted_age is not None else "OK")
        if action == "BLOCK":  # FIX P: only BLOCK; PUSH_LATER no longer used
            blocked_count += 1
            continue
        # FIX R: score penalty for late windows (still ranked but down-weighted)
        if action == "FLAG_VERY_LATE":
            w["score"] = float(w.get("score", 0)) - 1.5
            late_penalty_count += 1
        elif action == "FLAG_LATE":
            w["score"] = float(w.get("score", 0)) - 0.5
            late_penalty_count += 1
        # Phase 2.8.77 FIX V: clamp window width when urgency mode on
        if urgency_mode:
            new_end, clamped = _clamp_window_to_months(
                w["start"], w["end"], _URGENCY_WIDTH_MONTHS
            )
            if clamped:
                w["original_end"] = w["end"]
                w["end"] = new_end
                w["width_clamped"] = True
                width_clamped_count += 1
        w["age_action"] = action
        w["predicted_age"] = (round(predicted_age, 2)
                              if predicted_age is not None else None)
        valid_windows.append(w)

    factors.append(f"STEP 5: {len(valid_windows)} survived "
                   f"(blocked={blocked_count}, late_penalised={late_penalty_count}"
                   + (f", width_clamped={width_clamped_count}" if urgency_mode else "")
                   + ")")

    # Phase 2.8.77 FIX W: recency penalty when urgency mode (nearest wins ranking)
    if urgency_mode and valid_windows:
        from datetime import date as _date
        today = _date.today()
        recency_applied = 0
        for w in valid_windows:
            try:
                w_start = w["start"].date() if hasattr(w["start"], "date") else w["start"]
                years_from_now = max(0.0, (w_start - today).days / 365.25)
                penalty = years_from_now * _URGENCY_RECENCY_PENALTY_PER_YEAR
                w["score"] = float(w.get("score", 0)) - penalty
                w["recency_penalty"] = round(penalty, 2)
                recency_applied += 1
            except Exception:
                pass
        factors.append(f"STEP 5 URGENCY: applied recency penalty to "
                       f"{recency_applied} windows (nearest preferred)")

    # FIX Q: PREMATURE downgrade for PROMISED *and* DELAYED (both can be premature)
    if windows and not valid_windows and final_verdict in ("PROMISED", "DELAYED"):
        prev_verdict = final_verdict
        final_verdict = "PREMATURE"
        factors.append(f"STEP 5 DOWNGRADE: {prev_verdict} -> PREMATURE (age gate)")
        risk_flag = risk_flag or "Below marriageable age"
        if "Below marriageable age" not in risk_flags:
            risk_flags.insert(0, "Below marriageable age")

    # Sort by (score desc, start asc). In urgency mode, recency penalty above
    # (1.5/yr) is strong enough on its own to push nearest viable to the top.
    valid_windows.sort(key=lambda w: (-float(w.get("score", 0)), w["start"]))

    # FIX S: AD-diversity-aware top 3 selection
    # Greedy: pick highest. For slots 2 and 3, prefer a window with a NEW AD
    # if its score is within 1.0 of the slot's score-rank position. This avoids
    # showing 3 sub-windows of the same AD as "3 options".
    _DIVERSITY_TOLERANCE = 1.0

    def _select_diverse_top3(sorted_ws: List[dict]) -> List[dict]:
        if not sorted_ws:
            return []
        chosen: List[dict] = [sorted_ws[0]]
        used_ads = {sorted_ws[0].get("ad")}
        for slot in range(1, 3):
            if len(chosen) >= len(sorted_ws):
                break
            # Determine the next-best score baseline (the score-rank candidate)
            remaining = [w for w in sorted_ws if w not in chosen]
            if not remaining:
                break
            baseline_score = float(remaining[0].get("score", 0))
            # Find first remaining window with a NEW AD whose score is within
            # tolerance of the baseline.
            diverse_pick = None
            for w in remaining:
                if w.get("ad") not in used_ads:
                    if (baseline_score - float(w.get("score", 0))) <= _DIVERSITY_TOLERANCE:
                        diverse_pick = w
                    break
            pick = diverse_pick if diverse_pick is not None else remaining[0]
            chosen.append(pick)
            used_ads.add(pick.get("ad"))
        return chosen

    top_3 = _select_diverse_top3(valid_windows)
    if top_3 and len({w.get("ad") for w in top_3}) > 1:
        factors.append(f"STEP 5 DIVERSITY: top_3 spans "
                       f"{len({w.get('ad') for w in top_3})} ADs "
                       f"({', '.join(sorted({w.get('ad','?') for w in top_3}))})")

    primary_window = None
    backup_window = None
    key_trigger = None
    confluence_strength = None

    def _trigger_str(w: dict) -> str:
        parts = [f"{w['ad']} AD", f"{w['pd']} PD"]
        if w.get("jup"):
            parts.append("Jupiter on 7H/Venus")
        if w.get("sat"):
            parts.append("Saturn 7th-from-Moon")
        if w.get("double_transit"):
            parts.append("DT")
        if w.get("mars_trigger"):
            parts.append("Mars trigger")
        if w.get("sandhi"):
            parts.append("Sandhi")
        return " + ".join(parts)

    if top_3:
        p = top_3[0]
        primary_window = _format_window(p["start"], p["end"])
        key_trigger = _trigger_str(p)
        # Phase 2.8.76 FIX T: WEAK label allowed below MEDIUM threshold.
        # Downstream consumers (locked_facts, validator) accept Optional[str]
        # so any string label is safe; this prevents weak windows being
        # mislabeled MODERATE and misleading the LLM/UI.
        if p["score"] >= _WINDOW_STRONG_SCORE:
            confluence_strength = "STRONG"
        elif p["score"] >= _WINDOW_MEDIUM_SCORE:
            confluence_strength = "MODERATE"
        else:
            confluence_strength = "WEAK"
        factors.append(f"STEP 4 PRIMARY: {primary_window} score={p['score']} "
                       f"({confluence_strength})")

        # Backup = next window in DIFFERENT AD
        for w in top_3[1:]:
            if w["ad"] != p["ad"]:
                bk_str = _format_window(w["start"], w["end"])
                if bk_str == primary_window:
                    bk_str = f"{bk_str} ({w['ad']} AD)"
                backup_window = bk_str
                factors.append(f"STEP 4 BACKUP: {backup_window} score={w['score']}")
                break
        # If all top 3 share same AD, use 2nd as backup (different month)
        if backup_window is None and len(top_3) >= 2:
            w = top_3[1]
            backup_window = _format_window(w["start"], w["end"])

    # Serialize top_3 to plain dicts (datetimes -> isoformat)
    top_3_serial = []
    for w in top_3:
        top_3_serial.append({
            "window": _format_window(w["start"], w["end"]),
            "start": w["start"].strftime("%Y-%m-%d"),
            "end": w["end"].strftime("%Y-%m-%d"),
            "score": w["score"],
            "md": w["md"], "ad": w["ad"], "pd": w["pd"],
            "trigger": _trigger_str(w),
            "predicted_age": w.get("predicted_age"),
            "age_action": w.get("age_action"),
            "sandhi": w.get("sandhi", False),
            "eclipse_flag": w.get("eclipse_flag", False),
            "mars_sat_conflict": w.get("mars_sat_conflict", False),
            "factors": w.get("factors", []),
        })

    # ════════════════════════════════════════════════════════════════
    # ADD-ONLY (post-merge): two new diagnostic fields per user spec
    #   1. d1_d9_planet_scan      — full 9-planet × {7H/7L} connection scan
    #   2. chronological_top3_strict_dtt — strict DTT (Jup+Sat on 7H or
    #      natal 7L) chronologically-picked top 3 windows
    # These are additive: existing top_3_windows / primary_window remain.
    # ════════════════════════════════════════════════════════════════
    # 7L already resolved canonically at L1641 (with fallback). Reuse.
    sl_natal_si = seventh_lord_si
    sl_name = seventh_lord

    d1_d9_scan: Dict[str, Any] = {}
    chrono_top3: List[Dict[str, Any]] = []
    try:
        asc_lon = kundli.get("ascendantDeg")
        d1_d9_scan = _full_d1_d9_marriage_planet_scan(
            planets, h7_si, sl_name, sl_natal_si, kundli, asc_lon)
    except Exception as exc:
        print(f"[marriage_timing add-on d1_d9_scan] failed: {exc}")

    try:
        if final_verdict != "DENIED" and lagna_si is not None and h7_si is not None:

            # min_age_dt = STEP 0-shifted early threshold age boundary
            min_age_dt = None
            try:
                by = _extract_birth_year(birth) if isinstance(birth, dict) else None
                if by and isinstance(thresholds, (tuple, list)) and len(thresholds) >= 2:
                    early_thr = thresholds[1]
                    if isinstance(early_thr, (int, float)) and early_thr > 0:
                        min_age_dt = datetime(by + int(early_thr), 1, 1)
            except Exception as _exc_age:
                print(f"[marriage_timing add-on min_age_dt] failed: {_exc_age}")

            chrono_top3 = _chronological_dtt_top3_strict(
                kundli, target_lords, lagna_si, moon_si,
                h7_si, sl_natal_si,
                min_age_dt=min_age_dt)
    except Exception as exc:
        print(f"[marriage_timing add-on chronological_top3_strict_dtt] failed: {exc}")

    # Strip non-serializable datetime objects from chrono_top3
    chrono_top3_serial: List[Dict[str, Any]] = []
    for c in chrono_top3:
        c2 = {k: v for k, v in c.items() if k not in ("start", "end")}
        chrono_top3_serial.append(c2)

    result: Dict[str, Any] = {
        "verdict": final_verdict,
        "band": band,
        "primary_window": primary_window,
        "backup_window": backup_window,
        "key_trigger": key_trigger,
        "confluence_strength": confluence_strength,
        "ul_outlook": None,                # Love engine merges this later
        "risk_flag": risk_flag,
        "risk_flags": risk_flags,
        "factors": factors,
        "top_3_windows": top_3_serial,
        "step0_tendency": step0,
        # ADD-ONLY new diagnostic fields:
        "d1_d9_planet_scan": d1_d9_scan,
        "chronological_top3_strict_dtt": chrono_top3_serial,
        # Phase 2.8.73 FIX H — STEP 2 link-filter visibility (debug/LLM)
        "step2_link_filter": {
            "approvers":   sorted(approver_planets),
            "deniers":     sorted(denier_planets),
            "conditional": list(step2_buckets.get("conditional", [])),
            "ignore":      list(step2_buckets.get("ignore", [])),
            "per_planet_summary": [
                {"planet": e.get("planet"),
                 "step1":  e.get("step1_verdict"),
                 "link":   e.get("link_strength"),
                 "final":  e.get("final"),
                 "bucket": e.get("bucket")}
                for e in (step2.get("per_planet") or [])
            ],
        },
    }

    # ── ADD-ONLY: Validator (Guard) report
    try:
        from .validator import validate_marriage_assessment
        result["validator_report"] = validate_marriage_assessment(
            kundli, birth, intel, result)
    except Exception as exc:
        print(f"[marriage_timing add-on validator_report] failed: {exc}")
        result["validator_report"] = {
            "pass": False, "severity": "FAIL",
            "summary": f"validator crashed: {exc}",
            "checks": {}, "mismatches": [], "warnings": [],
        }

    return result

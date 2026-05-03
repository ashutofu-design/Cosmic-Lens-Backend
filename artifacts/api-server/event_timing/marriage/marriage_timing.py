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
    "confluence_strength": "STRONG" | "MODERATE",
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

# KP signification rule — 7CSL signifies these houses -> PROMISED
_KP_PROMISE_HOUSES: Set[int] = {2, 7, 11}
# KP signification rule (VIVAH-7 spec) — 7CSL signifies these -> DENIED
# Spec lock: 6/8/12 (dusthana/separation/loss). NOTE: {1,6,10} is the
# classical "no-marriage / single-life" set; we use {6,8,12} per VIVAH-7
# because for the "kab shaadi hogi" question we treat marriage that
# results in dusthana karma as denial-equivalent (no stable marriage).
_KP_DENY_HOUSES: Set[int] = {6, 8, 12}

# Reality Filter age thresholds (BASE — STEP 0 may shift these)
_AGE_HARD_BLOCK = 18      # below this: never predict marriage in <2 yr
_AGE_EARLY_FLAG = 22      # 18-21: flag "practically early"
_AGE_LATE_FLAG = 39       # 39+: flag "late pattern"
_AGE_VERY_LATE = 45       # 45+: flag "compromise/fast-arranged typical"

# STEP 0 tendency shifts (added to base age thresholds)
_AGE_SHIFT_LATE = +3      # LATE tendency: push everything later
_AGE_SHIFT_EARLY = -2     # EARLY tendency: pull everything earlier

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


def _get_kp_significators(kp: dict, house: int) -> Set[str]:
    """Get planets that signify a given house via KP CCS rules.

    Bridges -> event_timing.marriage.love_or_arrange._kp_significators_of(kp, house)
    Returns set of planet names. Empty set on failure.
    """
    try:
        from .love_or_arrange import (   # type: ignore
            _kp_significators_of,
        )
        result = _kp_significators_of(kp, house)
        return result if isinstance(result, set) else set(result or [])
    except Exception as exc:
        print(f"[marriage_timing._get_kp_significators] failed: {exc}")
        return set()


def _planet_kp_significations(kp: dict, planet: str) -> List[int]:
    """Houses that a given planet signifies (across all 12 houses).

    Used by STEP 1 to evaluate both 7CSL and 7C Star Lord.
    """
    if not planet:
        return []
    out: List[int] = []
    for h in range(1, 13):
        sigs = _get_kp_significators(kp, h)
        if planet in sigs:
            out.append(h)
    return out


def _kp_planet_verdict(kp: dict, planet: str) -> Tuple[str, List[int]]:
    """Return ('PROMISED'|'DENIED'|'MIXED'|'UNKNOWN', signified_houses)
    for a single KP planet (used for both 7CSL and 7C Star Lord).
    """
    if not planet:
        return ("UNKNOWN", [])
    signified = _planet_kp_significations(kp, planet)
    sset = set(signified)
    promise_hits = len(sset & _KP_PROMISE_HOUSES)
    deny_hits = len(sset & _KP_DENY_HOUSES)
    if promise_hits >= 2 and deny_hits == 0:
        return ("PROMISED", signified)
    if deny_hits >= 2 and promise_hits == 0:
        return ("DENIED", signified)
    if promise_hits >= 1 and deny_hits >= 1:
        return ("MIXED", signified)
    if promise_hits >= 1:
        return ("PROMISED", signified)
    if deny_hits >= 1:
        return ("DENIED", signified)
    return ("MIXED", signified)


def _kp_csl_verdict(kp: dict) -> Tuple[str, List[int]]:
    """STEP 1 prep — compute KP 7CSL verdict (single planet, primary)."""
    try:
        return _kp_planet_verdict(kp, _get_7csl(kp))
    except Exception as exc:
        print(f"[marriage_timing._kp_csl_verdict] failed: {exc}")
        return ("UNKNOWN", [])


# ════════════════════════════════════════════════════════════════════════
# SECTION 2b — ChatGPT-style strict KP Sub-Lord Marriage Filter
# (Phase 2.8.56 — added 2026-05-02 per user spec)
#
# RULE: For each planet, look at its SUB-LORD's BASIC houses (occupation +
# KP cusp ownership). Classify per:
#   Promise = {2, 7, 11}
#   Deny    = {1, 6, 8, 10, 12}
# This is STRICTER and CLEANER than the chain-union approach used by
# _kp_planet_verdict above. Both methods coexist (ADD-ONLY).
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


def _planet_basic_houses(kp: dict, planet: str) -> List[int]:
    """Return planet's BASIC signified houses = occupation + KP cusp ownership.

    Used by ChatGPT-style strict Sub-Lord filter (NOT the 4-level CCS chain).
    Returns sorted unique list. Empty list if planet not found.

    For shadow planets (Rahu/Ketu) ownership is empty (no own sign in KP),
    so they only contribute their occupation house.
    """
    if not isinstance(kp, dict) or not planet:
        return []
    out: Set[int] = set()
    # Occupation (where planet sits in KP houses)
    for p in (kp.get("planets") or []):
        if isinstance(p, dict) and p.get("name") == planet:
            h = p.get("house")
            if isinstance(h, int):
                out.add(h)
            break
    # Ownership: any KP cusp whose sign-lord is this planet
    for c in (kp.get("cusps") or []):
        if isinstance(c, dict) and c.get("sl") == planet:
            h = c.get("house")
            if isinstance(h, int):
                out.add(h)
    return sorted(out)


def _kp_sublord_filter_planet(kp: dict, planet: str) -> Dict[str, Any]:
    """Apply strict ChatGPT-style Sub-Lord filter to ONE planet.

    Returns dict:
      {
        "planet":       "Sun",
        "sub_lord":     "Saturn",
        "sb_houses":    [2, 4],
        "promise_hits": [2],
        "deny_hits":    [],
        "verdict":      "STRONG" | "MIXED" | "WEAK" | "UNKNOWN",
        "reason":       "Sub-lord Saturn (2,4) → 2 promise present"
      }

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
    }
    if not isinstance(kp, dict) or not planet:
        return out
    pl = next((p for p in (kp.get("planets") or [])
               if isinstance(p, dict) and p.get("name") == planet), None)
    if not pl:
        return out
    sb = pl.get("sb")
    if not sb:
        return out
    sb_houses = _planet_basic_houses(kp, sb)
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

    out.update({
        "sub_lord": sb,
        "sb_houses": sb_houses,
        "promise_hits": promise,
        "deny_hits": deny,
        "verdict": verdict,
        "reason": reason,
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


def _age_filter_action(age: Optional[int], predicted_age: Optional[int],
                        thresholds: Tuple[int, int, int, int]) -> str:
    """Decide STEP 5 action.

    Returns: BLOCK | PUSH_LATER | FLAG_EARLY | OK | FLAG_LATE | FLAG_VERY_LATE | UNKNOWN
    """
    hard_block, early_flag, late_flag, very_late = thresholds
    if age is None:
        return "UNKNOWN"
    if age < hard_block:
        return "BLOCK"
    if predicted_age is None:
        return "UNKNOWN"
    if predicted_age < hard_block:
        return "PUSH_LATER"
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
                                gender: str = "") -> dict:
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
    venus_house = _planet_house_local(planets, "Venus")
    venus_dignity = _planet_dignity(planets, "Venus")
    venus_combust = _is_combust_local(planets, "Venus")
    saturn_si = _planet_sign_idx(planets, "Saturn")
    saturn_house = _planet_house_local(planets, "Saturn")
    jup_si = _planet_sign_idx(planets, "Jupiter")

    # ── L1: Saturn conjunct or aspecting 7H/7L (natal)
    sat_aff_7h = saturn_si is not None and (
        saturn_si == h7_si or _is_saturn_aspect(saturn_si, h7_si))
    sat_aff_7l = (saturn_si is not None and seventh_lord_si is not None
                  and (saturn_si == seventh_lord_si
                       or _is_saturn_aspect(saturn_si, seventh_lord_si)))
    if sat_aff_7h:
        late += 1
        reasons.append("L1: natal Saturn conjunct/aspect 7H (+1 LATE)")
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

    # ── L3: Venus combust or in dusthana
    if venus_combust:
        late += 1
        reasons.append("L3: Venus combust (+1 LATE)")
    elif venus_house in _DUSTHANA:
        late += 1
        reasons.append(f"L3: Venus in {venus_house}H dusthana (+1 LATE)")

    # ── L11: Saturn IN 7H natally
    if saturn_house == 7:
        late += 1
        reasons.append("L11: natal Saturn IN 7H (+1 LATE)")

    # ── E1: Jupiter aspect/conjunct 7H or 7L
    jup_aff_7h = jup_si is not None and (
        jup_si == h7_si or _is_jupiter_aspect(jup_si, h7_si))
    jup_aff_7l = (jup_si is not None and seventh_lord_si is not None
                  and (jup_si == seventh_lord_si
                       or _is_jupiter_aspect(jup_si, seventh_lord_si)))
    if jup_aff_7h:
        early += 1
        reasons.append("E1: natal Jupiter conjunct/aspect 7H (+1 EARLY)")
    elif jup_aff_7l:
        early += 1
        reasons.append(f"E1: natal Jupiter blessing 7L {seventh_lord} (+1 EARLY)")

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
    if seventh_lord_h in _KENDRA_TRIKONA:
        retro = _planet_is_retrograde(planets, seventh_lord)
        if not retro:
            early += 1
            reasons.append(f"E6: 7L {seventh_lord} in {seventh_lord_h}H kendra/trikona (+1 EARLY)")
        else:
            reasons.append(f"E6 (skip): 7L {seventh_lord} in {seventh_lord_h}H but retro — neutral")

    # ── Gender modifier (G1/G2)
    g = (gender or "").strip().lower()
    if g in ("m", "male", "man", "boy"):
        if venus_combust or venus_house in _DUSTHANA or venus_dignity == "debilitated":
            late += 1
            reasons.append("G1: male + Venus karaka weak (+1 LATE)")
    elif g in ("f", "female", "woman", "girl"):
        jup_house = _planet_house_local(planets, "Jupiter")
        jup_dignity = _planet_dignity(planets, "Jupiter")
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

    return {
        "verdict": verdict,
        "score": score,
        "late_count": late,
        "early_count": early,
        "reasons": reasons,
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


def _planet_dignity(planets: list, name: str) -> str:
    """Return dignity string: exalted | moolatrikona | own | friend |
    neutral | enemy | debilitated | "" (unknown).
    """
    rec = _planet_record(planets, name)
    if not rec:
        return ""
    d = rec.get("dignity") or rec.get("dignityState") or ""
    return str(d).strip().lower()


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
    step0 = _step0_late_early_tendency(
        planets, intel, kp, lagna_si, h7_si,
        seventh_lord, venus_si, gender)
    factors.append(f"STEP 0: tendency={step0['verdict']} "
                   f"(LATE={step0['late_count']} EARLY={step0['early_count']} "
                   f"net={step0['score']})")

    # ════════════════════════════════════════════════════════════════
    # STEP 1 — KP Filter (FIRST GATE — sublord = FINAL ARBITER)
    # ════════════════════════════════════════════════════════════════
    csl7 = _get_7csl(kp)
    starlord = _get_7c_star_lord(kp)
    csl_verdict, csl_signs = _kp_planet_verdict(kp, csl7)
    star_verdict, star_signs = _kp_planet_verdict(kp, starlord) if starlord else ("UNKNOWN", [])

    factors.append(f"STEP 1 KP: 7CSL={csl7 or 'n/a'} -> {csl_verdict} "
                   f"signifies {csl_signs}")
    factors.append(f"STEP 1 KP: 7C StarLord={starlord or 'n/a'} -> "
                   f"{star_verdict} signifies {star_signs}")

    # KP gate decision (sublord dominant, starlord cross-check)
    if csl_verdict == "PROMISED" and star_verdict in ("PROMISED", "MIXED", "UNKNOWN"):
        kp_gate = "PROMISED"
    elif csl_verdict == "DENIED" and star_verdict == "DENIED":
        kp_gate = "DENIED"
    elif csl_verdict == "DENIED" and star_verdict in ("PROMISED", "MIXED"):
        kp_gate = "DELAYED"
    elif csl_verdict == "PROMISED" and star_verdict == "DENIED":
        kp_gate = "DELAYED"
    elif csl_verdict == "MIXED":
        kp_gate = "DELAYED" if star_verdict == "DENIED" else "MIXED"
    else:
        kp_gate = csl_verdict if csl_verdict != "UNKNOWN" else "MIXED"

    factors.append(f"STEP 1 KP GATE: {kp_gate}")

    # ════════════════════════════════════════════════════════════════
    # STEP 2 — D1 + D9 Cross-Validation
    # ════════════════════════════════════════════════════════════════
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
    # R3: 7L exalted natally
    if _planet_dignity(planets, seventh_lord) == "exalted":
        redemption += 1
        redemption_reasons.append(f"R3: 7L {seventh_lord} exalted (+1)")
    # R4: Strong 7H Sarvashtakavarga (>= 30)
    sav_h7 = _sav_bonus(av, h7_si)
    if sav_h7 > 0:
        redemption += 1
        redemption_reasons.append(f"R4: 7H SAV strong ({_SIGNS[h7_si]}) (+1)")

    for r in redemption_reasons:
        factors.append(f"STEP 3 REDEMPTION: {r}")
    if not redemption_reasons:
        factors.append("STEP 3 REDEMPTION: no rescue factors")

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
    candidate_ads = _scan_cluster_ads(kundli, target_lords, lookback_days=30)
    factors.append(f"STEP 4: target_lords={sorted(target_lords)}, "
                   f"candidate_ADs={len(candidate_ads)}")

    today = datetime.utcnow()
    windows: List[dict] = []

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

            # ── A. Cluster hit + AD/PD weight (DOMINANT base)
            cluster_hit = 1
            if pd_lord in target_lords:
                cluster_hit = 2
                window_factors.append(f"PD {pd_lord} in cluster (+1)")
            adpd_weight = 0
            if ad_in_target and pd_lord in target_lords:
                adpd_weight = 3   # DOMINANT: AD+PD both in target
                window_factors.append(f"AD+PD both in target -> DOMINANT (+3)")
            elif md_in_target and ad_in_target:
                adpd_weight = 2
                window_factors.append("MD+AD both in target (+2)")
            elif ad_in_target:
                adpd_weight = 1

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

            # ── C. Mars trigger (+1 activation only) + conflict flag
            mars_trig, mars_reason = _mars_trigger_check(
                transit, h7_si, venus_si, seventh_lord_si) if h7_si is not None else (False, "")
            mars_bonus = 0
            mars_sat_conflict = False
            if mars_trig:
                mars_bonus = 1
                window_factors.append(f"+1 Mars TRIGGER ({mars_reason})")
                if sat_score > 0:
                    mars_sat_conflict = True
                    window_factors.append("⚠ Mars+Saturn CONFLICT (push vs delay)")

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

            # ── TOTAL: base components, then strength multiplier, then eclipse
            base = (cluster_hit + adpd_weight
                    + jup_score + sat_score
                    + double_transit_bonus
                    + mars_bonus
                    + retro_penalty
                    + bav_b + sav_b
                    + sandhi_bonus)
            score = base * strength_mult + eclipse_penalty

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

    # ════════════════════════════════════════════════════════════════
    # STEP 5 — Reality Filter (STEP 0-adjusted age table)
    # ════════════════════════════════════════════════════════════════
    age = _get_current_age(birth, kundli, current_dasha)
    birth_year = _extract_birth_year(birth)
    thresholds = _adjusted_age_thresholds(step0["verdict"])
    factors.append(f"STEP 5: age={age} birth_year={birth_year} "
                   f"thresholds={thresholds} (STEP 0 adj for {step0['verdict']})")

    valid_windows: List[dict] = []
    blocked_count = 0
    for w in windows:
        predicted_year = w["start"].year
        predicted_age = (predicted_year - birth_year) if (birth_year and birth_year > 0) else None
        action = (_age_filter_action(age, predicted_age, thresholds)
                  if predicted_age is not None else "OK")
        if action in ("BLOCK", "PUSH_LATER"):
            blocked_count += 1
            continue
        w["age_action"] = action
        w["predicted_age"] = predicted_age
        valid_windows.append(w)

    factors.append(f"STEP 5: {len(valid_windows)} survived (blocked={blocked_count})")

    # If ALL windows blocked & promised -> PREMATURE downgrade
    if windows and not valid_windows and final_verdict == "PROMISED":
        final_verdict = "PREMATURE"
        factors.append("STEP 5 DOWNGRADE: PROMISED -> PREMATURE (age gate)")
        risk_flag = risk_flag or "Below marriageable age"
        if "Below marriageable age" not in risk_flags:
            risk_flags.insert(0, "Below marriageable age")

    # Sort by (score desc, start asc)
    valid_windows.sort(key=lambda w: (-w["score"], w["start"]))

    # Pick top 3
    top_3 = valid_windows[:3]

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
        # Contract lock: confluence_strength is "STRONG" | "MODERATE" only
        # (legacy consumers downstream do not handle "WEAK"). Below MODERATE
        # we leave it None — the score is still in top_3_windows for
        # consumers who want it.
        if p["score"] >= _WINDOW_STRONG_SCORE:
            confluence_strength = "STRONG"
        elif p["score"] >= _WINDOW_MEDIUM_SCORE:
            confluence_strength = "MODERATE"
        else:
            confluence_strength = "MODERATE"
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

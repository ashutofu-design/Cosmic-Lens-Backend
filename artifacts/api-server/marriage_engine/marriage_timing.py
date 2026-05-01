"""
marriage_engine/marriage_timing.py
==================================
TIMING sub-engine — locked Dasha + Transit window math for marriage.

Phase 2.8.30a — STEP 1: WIRING (toolset bridges)
================================================
This file is the **integration layer** between marriage timing logic and
the existing deterministic helpers scattered across the codebase. Every
wrapper below is a thin lazy-loaded bridge to an EXISTING function so
Step 2 (layer logic) can call clean, named helpers without worrying about
import paths or signature drift.

Architecture lock:
  Engine = Truth (frozen)
  LLM    = Narrator (this file's output is read-only for LLM)
  Validator = Guard (post-injector, regex-only)

Layer plan (Step 2 will populate compute_timing_window):
  Layer 1  D1 Promise check       -> uses _get_manglik + house lords
  Layer 2  D9 Confirmation        -> uses _get_d9_chart
  Layer 3  KP 7CSL Verdict        -> uses _get_7csl + _get_kp_significators
  Layer 4  Triple Confluence      -> uses _scan_cluster_ads + _project_pds
                                     + _get_jupiter_sign_at + _get_saturn_sign_at
  Layer 5  Reality Filter         -> uses _get_current_age

Public function (Step 2 will fill):
  compute_timing_window(kundli, intel, kp, birth) -> dict

Returns dict shape (when populated):
  {
    "verdict":        "PROMISED" | "DELAYED" | "DENIED",
    "band":           "WEAK" | "MEDIUM" | "STRONG",
    "primary_window": "August - October 2027",
    "backup_window":  "March - May 2029",
    "key_trigger":    "Venus AD + Jupiter PD + Jupiter transit on 7H Libra",
    "ul_outlook":     {"sign": "Capricorn", "verdict": "NEUTRAL"},
    "risk_flag":      "Manglik" | "7L afflicted" | "Karaka weak" | None,
    "factors":        [...]   # internal trace, hidden from user
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
# KP signification rule — 7CSL signifies these -> DENIED / single life
_KP_DENY_HOUSES: Set[int] = {1, 6, 10}

# Reality Filter age thresholds (Layer 5)
_AGE_HARD_BLOCK = 18      # below this: never predict marriage in <2 yr
_AGE_EARLY_FLAG = 22      # 18-21: flag "practically early"
_AGE_LATE_FLAG = 39       # 39+: flag "late pattern"
_AGE_VERY_LATE = 45       # 45+: flag "compromise/fast-arranged typical"


# ════════════════════════════════════════════════════════════════════════
# SECTION 1 — D9 Navamsha (Layer 2 toolset)
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
# SECTION 2 — KP cusps + sub-lord + significations (Layer 3 toolset)
# ════════════════════════════════════════════════════════════════════════
def _get_kp_cusp(kp: dict, house: int) -> Optional[dict]:
    """Fetch the KP cusp dict for a given house (1-12).

    Bridges -> marriage_engine.love_or_arrange._kp_cusp(kp, house)
    Returns the cusp dict (with sl/nl/sb/ss fields) or None.
    """
    try:
        from marriage_engine.love_or_arrange import _kp_cusp   # type: ignore
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


def _get_kp_significators(kp: dict, house: int) -> Set[str]:
    """Get planets that signify a given house via KP CCS rules.

    Bridges -> marriage_engine.love_or_arrange._kp_significators_of(kp, house)
    Returns set of planet names. Empty set on failure.
    """
    try:
        from marriage_engine.love_or_arrange import (   # type: ignore
            _kp_significators_of,
        )
        result = _kp_significators_of(kp, house)
        return result if isinstance(result, set) else set(result or [])
    except Exception as exc:
        print(f"[marriage_timing._get_kp_significators] failed: {exc}")
        return set()


def _kp_csl_verdict(kp: dict) -> Tuple[str, List[int]]:
    """Layer 3 prep — compute KP 7CSL verdict signal.

    Returns (verdict, signified_houses):
      verdict in {"PROMISED", "DENIED", "MIXED", "UNKNOWN"}
      signified_houses = list of houses 7CSL is a significator of
    """
    try:
        csl7 = _get_7csl(kp)
        if not csl7:
            return ("UNKNOWN", [])
        # Find which houses csl7 signifies
        signified: List[int] = []
        for h in range(1, 13):
            sigs = _get_kp_significators(kp, h)
            if csl7 in sigs:
                signified.append(h)
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
    except Exception as exc:
        print(f"[marriage_timing._kp_csl_verdict] failed: {exc}")
        return ("UNKNOWN", [])


# ════════════════════════════════════════════════════════════════════════
# SECTION 3 — Vimshottari MD-AD scanner (Layer 4 base)
# ════════════════════════════════════════════════════════════════════════
def _get_dasha_upcoming(kundli: dict) -> List[dict]:
    """Fetch upcoming MD-AD blocks from kundli.

    Tolerant of multiple field names produced upstream by
    kundli_engine.calc_vimshottari_dasha. Returns list of dicts with
    md_lord/ad_lord/start/end fields, or [] if unavailable.
    """
    if not isinstance(kundli, dict):
        return []
    vims = (kundli.get("vimshottari")
            or kundli.get("dasha")
            or {})
    if isinstance(vims, dict):
        upcoming = (vims.get("upcoming")
                    or vims.get("antardasha_sequence")
                    or [])
    else:
        upcoming = []
    if not upcoming:
        upcoming = (kundli.get("upcomingAntars")
                    or kundli.get("upcoming_antars")
                    or kundli.get("upcomingDashas")
                    or kundli.get("antardashas")
                    or [])
    return upcoming if isinstance(upcoming, list) else []


def _scan_cluster_ads(kundli: dict, target_lords: Set[str],
                      lookback_days: int = 30) -> List[dict]:
    """Find upcoming MD-AD jodis where MD or AD lord is in target_lords.

    Bridges -> vedic.timing.timing_engine._scan_dasha_for_lords
    Returns list of {md, ad, start, end, score} dicts (score 2 or 4).
    """
    try:
        from vedic.timing.timing_engine import (   # type: ignore
            _scan_dasha_for_lords,
        )
        vims = (kundli.get("vimshottari")
                or kundli.get("dasha")
                or {})
        # The scanner reads vims["upcoming"]; if our data is in another
        # field, build a thin dict with the right shape.
        if not (isinstance(vims, dict) and vims.get("upcoming")):
            upcoming = _get_dasha_upcoming(kundli)
            vims = {"upcoming": upcoming, "current": (vims or {}).get("current") or {}}
        return _scan_dasha_for_lords(vims, target_lords, lookback_days) or []
    except Exception as exc:
        print(f"[marriage_timing._scan_cluster_ads] failed: {exc}")
        return []


def _marriage_target_lords(lagna_sign_idx: int) -> Set[str]:
    """Compute target lords for marriage cluster {7H, 2H, 11H} from lagna.

    Adds Karaka planets (Venus, Jupiter) — both sexes' karakas are
    always relevant signifiers, gender-specific weighting handled later.
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
# SECTION 4 — PD month-window chain (Layer 4 month precision)
# ════════════════════════════════════════════════════════════════════════
def _project_pds(md_lord: str, ad_lord: str,
                 ad_start: datetime, ad_end: datetime,
                 from_dt: Optional[datetime] = None,
                 months_needed: int = 6) -> List[dict]:
    """Project PD chain inside a given AD (and walk forward if needed).

    Bridges -> vedic.future_engine._project_pd_chain
    Returns list of {md, ad, pd, start, end} dicts.
    """
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
    """Get the currently-running Pratyantar Dasha info.

    Bridges -> pratyantar.compute_pratyantar(current_dasha, when)
    Returns {"current_pd": {...}, "upcoming_pds": [...], "ad_lord": ...,
             "md_lord": ...} or {} on failure.
    """
    try:
        from pratyantar import compute_pratyantar   # type: ignore
        return compute_pratyantar(current_dasha, when=when) or {}
    except Exception as exc:
        print(f"[marriage_timing._get_current_pd] failed: {exc}")
        return {}


# ════════════════════════════════════════════════════════════════════════
# SECTION 5 — Jupiter / Saturn transit ephemeris (Layer 4 confluence)
# ════════════════════════════════════════════════════════════════════════
def _get_transits_at(natal_lagna_si: int, natal_moon_si: Optional[int],
                     when: Optional[datetime] = None) -> dict:
    """Compute Jupiter/Saturn/Rahu sidereal sign at a given date.

    Bridges -> transits.compute_transits(lagna_si, moon_si, when=when)
    Returns dict like {"as_of": "YYYY-MM-DD", "Saturn": {...},
                       "Jupiter": {...}, ...} or {} on failure.
    """
    try:
        from transits import compute_transits   # type: ignore
        return compute_transits(natal_lagna_si, natal_moon_si,
                                when=when) or {}
    except Exception as exc:
        print(f"[marriage_timing._get_transits_at] failed: {exc}")
        return {}


def _jupiter_on_marriage_house(transit_data: dict,
                               natal_7h_sign_idx: int,
                               natal_venus_sign_idx: Optional[int] = None
                               ) -> bool:
    """Check if Jupiter is transiting natal 7H sign or Venus sign.

    Returns True if Jupiter's current sign matches natal 7H or Venus.
    """
    try:
        jup = transit_data.get("Jupiter") or {}
        jup_si = jup.get("sign_idx")
        if jup_si is None:
            return False
        jup_si = int(jup_si) % 12
        if jup_si == int(natal_7h_sign_idx) % 12:
            return True
        if (natal_venus_sign_idx is not None
                and jup_si == int(natal_venus_sign_idx) % 12):
            return True
        return False
    except Exception:
        return False


def _saturn_seventh_from_moon(transit_data: dict,
                              natal_moon_sign_idx: int) -> bool:
    """Check if Saturn is transiting the 7th sign from natal Moon.

    Classical marriage trigger.
    """
    try:
        sat = transit_data.get("Saturn") or {}
        sat_si = sat.get("sign_idx")
        if sat_si is None:
            return False
        sat_si = int(sat_si) % 12
        seventh_from_moon = (int(natal_moon_sign_idx) + 6) % 12
        return sat_si == seventh_from_moon
    except Exception:
        return False


# ════════════════════════════════════════════════════════════════════════
# SECTION 6 — Manglik (Layer 1 risk flag)
# ════════════════════════════════════════════════════════════════════════
def _get_manglik(planets: list) -> str:
    """Compute Manglik status from planet list.

    Bridges -> dosh_engine._manglik(pl) which returns a tuple
    (status, label, desc, remedies, note). We only need the status.
    Returns: "Active" | "Mild" | "None" | "Unknown"
    """
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
# SECTION 7 — Age compute (Layer 5 reality filter)
# ════════════════════════════════════════════════════════════════════════
def _get_current_age(birth: Any, kundli: dict,
                     current_dasha: Optional[dict] = None) -> Optional[int]:
    """Compute current age in years from birth date.

    Bridges -> vedic.context.age_context.compute_age_context(birth, kundli)
    Returns int age or None on failure.
    """
    try:
        from vedic.context.age_context import (   # type: ignore
            compute_age_context,
        )
        ctx = compute_age_context(birth or {}, kundli or {},
                                  current_dasha=current_dasha)
        if not isinstance(ctx, dict) or not ctx.get("available", True):
            # The function returns {"available": False, ...} on parse fail
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


def _age_filter_action(age: Optional[int],
                       predicted_year: Optional[int]) -> str:
    """Decide Reality Filter action based on age + predicted year.

    Returns one of:
      "BLOCK"        -> never predict, age too low
      "PUSH_LATER"   -> predicted window before age 22, push to next valid
      "FLAG_EARLY"   -> predicted age 18-21, allow but soften framing
      "OK"           -> predicted age 22-38, normal output
      "FLAG_LATE"    -> predicted age 39-44, late pattern framing
      "FLAG_VERY_LATE" -> predicted age 45+, compromise/arranged framing
      "UNKNOWN"      -> insufficient data
    """
    if age is None:
        return "UNKNOWN"
    if age < _AGE_HARD_BLOCK:
        return "BLOCK"
    if predicted_year is None:
        return "UNKNOWN"
    try:
        years_ahead = int(predicted_year) - 0   # placeholder; caller knows
        # Caller should pass predicted_age = (predicted_year - birth_year)
        predicted_age = int(predicted_year)
    except Exception:
        return "UNKNOWN"
    if predicted_age < _AGE_HARD_BLOCK:
        return "PUSH_LATER"
    if predicted_age < _AGE_EARLY_FLAG:
        return "FLAG_EARLY"
    if predicted_age < _AGE_LATE_FLAG:
        return "OK"
    if predicted_age < _AGE_VERY_LATE:
        return "FLAG_LATE"
    return "FLAG_VERY_LATE"


# ════════════════════════════════════════════════════════════════════════
# PUBLIC API — STUB (Step 2 will populate with Layer 1-5 orchestration)
# ════════════════════════════════════════════════════════════════════════
def compute_timing_window(kundli: dict, intel: dict, kp: dict,
                          birth: Optional[Any] = None) -> dict:
    """STUB — Step 2 will fill with full 5-layer orchestration.

    Step 2 plan (using only the wrappers above):
      1. Layer 1 (D1 Promise):
           - Manglik = _get_manglik(planets)
           - 7L lord + Karaka condition from kundli
           -> verdict_d1 (PROMISED/DELAYED/DENIED)

      2. Layer 2 (D9 Confirmation):
           - d9 = _get_d9_chart(planets, lagna_lon)
           - Check D9 7L + Karaka condition
           -> adjust verdict_d1 -> verdict_combined

      3. Layer 3 (KP 7CSL):
           - verdict_kp, sigs = _kp_csl_verdict(kp)
           -> independent verdict; combine with verdict_combined

      4. Layer 4 (Triple Confluence — only if verdict != DENIED):
           - target_lords = _marriage_target_lords(lagna_si)
           - candidate_ads = _scan_cluster_ads(kundli, target_lords)
           - For each candidate AD:
               pds = _project_pds(md, ad, ad_start, ad_end, ...)
               for pd in pds:
                 transit = _get_transits_at(lagna_si, moon_si, when=pd_mid)
                 jup_hit = _jupiter_on_marriage_house(transit, h7_si, venus_si)
                 sat_hit = _saturn_seventh_from_moon(transit, moon_si)
                 score = (cluster_hit) + jup_hit + sat_hit
                 if score >= 2: candidate window
           -> primary_window (score=3), backup_window (score=2)

      5. Layer 5 (Reality Filter):
           - age = _get_current_age(birth, kundli, current_dasha)
           - For each candidate window:
               action = _age_filter_action(age, window_year)
               if BLOCK: drop  if PUSH_LATER: skip to next valid AD
               else: keep with framing flag

      6. Output assembler:
           {verdict, band, primary_window, backup_window,
            key_trigger, ul_outlook, risk_flag, factors}
    """
    return {}

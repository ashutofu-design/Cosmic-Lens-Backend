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


def _get_kp_significators(kp: dict, house: int) -> Set[str]:
    """Get planets that signify a given house via KP CCS rules.

    Bridges -> marriage_engine.love_or_arrange._kp_significators_of(kp, house)
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
    """Fetch upcoming MD-AD blocks from kundli, normalised to the shape
    expected by `vedic.timing.timing_engine._scan_dasha_for_lords`.

    Each returned block is `{md_lord, ad_lord, start, end}`.

    Handles three known shapes:
      A) kundli["vimshottari"]["upcoming"]              (already flat)
      B) kundli["upcomingAntars"]                       (already flat)
      C) kundli["dashas"] = [{planet, startDate, endDate, subDashas:[
              {planet, startDate, endDate, subDashas:[PDs]}, ... ]}]
         (real production shape from kundli_engine.calculate_kundli)
    """
    if not isinstance(kundli, dict):
        return []

    # Shape A
    vims = kundli.get("vimshottari") or kundli.get("dasha") or {}
    if isinstance(vims, dict):
        flat = (vims.get("upcoming")
                or vims.get("antardasha_sequence")
                or [])
        if flat and isinstance(flat, list):
            return flat

    # Shape B
    flat = (kundli.get("upcomingAntars")
            or kundli.get("upcoming_antars")
            or kundli.get("upcomingDashas")
            or kundli.get("antardashas")
            or [])
    if flat and isinstance(flat, list):
        return flat

    # Shape C — flatten kundli["dashas"][*].subDashas into AD list
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
            # Filter to upcoming only (lookback handled by scanner)
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


def _transit_sign_idx(transit_data: dict, planet: str) -> Optional[int]:
    """Extract a transiting planet's sidereal sign index from the
    real shape returned by `transits.compute_transits`:
        {"as_of": "...",
         "transit_houses": {"Jupiter": {"sign": "Cancer", "house_from_lagna": 8}, ...}}

    Tolerates legacy/test shapes too:
        {"Jupiter": {"sign_idx": 3}}  or  {"Jupiter": {"sign": "Cancer"}}
    Returns int 0-11 or None.
    """
    if not isinstance(transit_data, dict):
        return None
    # Real production shape
    th = transit_data.get("transit_houses") or {}
    p = th.get(planet) if isinstance(th, dict) else None
    if not isinstance(p, dict):
        # Legacy/flat shape
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


def _jupiter_on_marriage_house(transit_data: dict,
                               natal_7h_sign_idx: int,
                               natal_venus_sign_idx: Optional[int] = None
                               ) -> bool:
    """True if transiting Jupiter's sidereal sign equals natal 7H or natal Venus sign."""
    try:
        jup_si = _transit_sign_idx(transit_data, "Jupiter")
        if jup_si is None:
            return False
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
    """True if transiting Saturn's sidereal sign is the 7th sign from natal Moon."""
    try:
        sat_si = _transit_sign_idx(transit_data, "Saturn")
        if sat_si is None:
            return False
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
# INTERNAL UTILITIES (small inline helpers for the public function)
# ════════════════════════════════════════════════════════════════════════
def _planet_sign_idx(planets: list, name: str) -> Optional[int]:
    """Find a planet's sidereal sign index (0-11) from kundli's planets list."""
    for p in (planets or []):
        if isinstance(p, dict) and p.get("name") == name:
            si = p.get("sign_idx")
            if isinstance(si, int):
                return si % 12
            sign = p.get("sign")
            if isinstance(sign, str) and sign in _SIGNS:
                return _SIGNS.index(sign)
    return None


def _planet_house_local(planets: list, name: str) -> Optional[int]:
    """Find a planet's house (1-12) from kundli's planets list."""
    for p in (planets or []):
        if isinstance(p, dict) and p.get("name") == name:
            h = p.get("house")
            if isinstance(h, int):
                return h
    return None


def _parse_dt(value: Any) -> Optional[datetime]:
    """Parse a date/datetime/string to a datetime object."""
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
    """Format a datetime range as 'August - October 2027'.

    If start and end span different years, render as
    'August 2026 - February 2027'.
    """
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
    """Pull birth year from common birth dict shapes used in this codebase."""
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


# ════════════════════════════════════════════════════════════════════════
# PUBLIC API — Layer 1-5 ORCHESTRATION (Phase 2.8.30a STEP 2)
# ════════════════════════════════════════════════════════════════════════
def compute_timing_window(kundli: dict, intel: dict, kp: dict,
                          birth: Optional[Any] = None) -> dict:
    """Run the full 5-layer marriage-timing pipeline.

    Returns dict (see module docstring for shape). Returns
    {"verdict": "UNKNOWN", "factors": [...]} when inputs are too thin
    (no planets, no lagna_sign, etc.) — never raises.
    """
    factors: List[str] = []

    # ── Common input extraction ────────────────────────────────────
    def _empty(reason: str) -> dict:
        return {"verdict": "UNKNOWN", "band": "WEAK",
                "primary_window": None, "backup_window": None,
                "key_trigger": None, "confluence_strength": None,
                "ul_outlook": None,
                "risk_flag": None, "risk_flags": [],
                "factors": [reason]}

    if not isinstance(kundli, dict) or not isinstance(intel, dict):
        return _empty("Insufficient input: missing kundli/intel")

    planets = kundli.get("planets") or []
    # lagna_lon: prefer explicit, fall back to ascendantDeg from kundli_engine
    lagna_lon = kundli.get("lagna_lon")
    if lagna_lon is None:
        for k in ("ascendantDeg", "lagnaDeg", "ascDeg"):
            v = kundli.get(k)
            if isinstance(v, (int, float)):
                lagna_lon = float(v)
                break
    # lagna_sign: prefer intel, fall back to kundli["ascendant"]
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

    if not planets:
        return _empty("Insufficient input: empty planets list")

    # ── LAYER 1 — D1 Promise check ────────────────────────────────
    seventh_lord = None
    for hl in (intel.get("house_lords") or []):
        if isinstance(hl, dict) and hl.get("house") == 7:
            seventh_lord = hl.get("lord")
            break
    seventh_lord_house = _planet_house_local(planets, seventh_lord) if seventh_lord else None
    venus_house = _planet_house_local(planets, "Venus")
    manglik_status = _get_manglik(planets)

    d1_score = 0
    if seventh_lord_house and seventh_lord_house not in {6, 8, 12}:
        d1_score += 1
        factors.append(f"D1 OK: 7L ({seventh_lord}) in {seventh_lord_house}H")
    else:
        factors.append(f"D1 FLAG: 7L ({seventh_lord}) in {seventh_lord_house}H (dusthana/missing)")

    if venus_house and venus_house not in {6, 8, 12}:
        d1_score += 1
        factors.append(f"D1 OK: Venus karaka in {venus_house}H")
    else:
        factors.append(f"D1 FLAG: Venus karaka in {venus_house}H (weak)")

    if manglik_status not in ("Active",):
        d1_score += 1
        factors.append(f"D1 OK: Manglik={manglik_status}")
    else:
        factors.append("D1 FLAG: Manglik=Active")

    if d1_score >= 2:
        verdict_d1 = "PROMISED"
    elif d1_score == 1:
        verdict_d1 = "DELAYED"
    else:
        verdict_d1 = "DENIED"

    # ── LAYER 2 — D9 Navamsha confirmation ────────────────────────
    d9 = _get_d9_chart(planets, lagna_lon) if lagna_lon is not None else _get_d9_chart(planets)
    # `divisional_charts.compute_d9` returns planets at top level, e.g.
    # {"Sun": {"sign": ..., "sign_idx": ..., "vargottama": ...}, ...,
    #  "_lagna": {...}}. Some implementations nest under "planets".
    if isinstance(d9, dict) and isinstance(d9.get("planets"), dict):
        d9_planets = d9["planets"]
    else:
        d9_planets = d9 if isinstance(d9, dict) else {}
    if not d9_planets:
        factors.append("D9 NOTE: navamsa unavailable — Layer 2 skipped")
    venus_d9_sign = (d9_planets.get("Venus") or {}).get("sign", "")
    seventh_lord_d9_sign = (d9_planets.get(seventh_lord) or {}).get("sign", "") if seventh_lord else ""
    venus_vargottama = bool((d9_planets.get("Venus") or {}).get("vargottama"))

    d9_bonus = 0
    # Venus debilitated in Virgo in D9 weakens; vargottama strengthens
    if venus_d9_sign and venus_d9_sign != "Virgo":
        d9_bonus += 1
        factors.append(f"D9 OK: Venus in {venus_d9_sign}"
                       + (" (vargottama)" if venus_vargottama else ""))
    elif venus_d9_sign:
        factors.append(f"D9 FLAG: Venus debilitated in {venus_d9_sign}")
    if seventh_lord_d9_sign:
        d9_bonus += 1
        factors.append(f"D9 OK: 7L ({seventh_lord}) placed in {seventh_lord_d9_sign}")

    # Combine D1 with D9 (D9 can promote/demote one tier)
    if verdict_d1 == "DENIED" and d9_bonus >= 2:
        verdict_combined = "DELAYED"
    elif verdict_d1 == "DELAYED" and d9_bonus >= 2:
        verdict_combined = "PROMISED"
    elif verdict_d1 == "PROMISED" and d9_bonus == 0:
        verdict_combined = "DELAYED"
    else:
        verdict_combined = verdict_d1

    # ── LAYER 3 — KP 7CSL verdict (independent) ──────────────────
    csl_verdict, csl_signs = _kp_csl_verdict(kp)
    csl7 = _get_7csl(kp)
    factors.append(f"KP: 7CSL={csl7 or 'n/a'} signifies houses {csl_signs} -> {csl_verdict}")

    # Combine with D1+D9
    if csl_verdict == "DENIED" and verdict_combined == "DENIED":
        final_verdict = "DENIED"
    elif csl_verdict == "DENIED":
        final_verdict = "DELAYED"
    elif csl_verdict == "PROMISED" and verdict_combined != "DENIED":
        final_verdict = "PROMISED"
    elif verdict_combined == "DENIED" and csl_verdict == "PROMISED":
        final_verdict = "DELAYED"
    else:
        final_verdict = verdict_combined

    # Strength band — KP UNKNOWN now penalised (was 1 pt freebie -> now 0)
    csl_pts = {"PROMISED": 2, "MIXED": 1, "UNKNOWN": 0, "DENIED": 0}.get(csl_verdict, 0)
    strength = d1_score + d9_bonus + csl_pts   # max 7 (3 D1 + 2 D9 + 2 KP)
    if strength >= 6:
        band = "STRONG"
    elif strength >= 4:
        band = "MEDIUM"
    else:
        band = "WEAK"

    # Risk flags — collect ALL (not just most severe). risk_flag = top one.
    risk_flags: List[str] = []
    if manglik_status == "Active":
        risk_flags.append("Manglik")
    if seventh_lord_house in {6, 8, 12}:
        risk_flags.append("7L afflicted")
    if d1_score == 0:
        risk_flags.append("Karaka weak")
    if csl_verdict == "DENIED":
        risk_flags.append("KP 7CSL denial")
    risk_flag: Optional[str] = risk_flags[0] if risk_flags else None

    # Early-exit if denied — skip Layer 4/5
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
        }

    # ── LAYER 4 — Triple Confluence (Dasha + PD + Transits) ──────
    target_lords = _marriage_target_lords(lagna_si) if lagna_si is not None else {"Venus", "Jupiter"}
    candidate_ads = _scan_cluster_ads(kundli, target_lords, lookback_days=30)
    factors.append(f"L4: target_lords={sorted(target_lords)}, candidate_ADs={len(candidate_ads)}")

    today = datetime.utcnow()
    windows: List[dict] = []

    for ad_blk in candidate_ads:
        md = ad_blk.get("md")
        ad = ad_blk.get("ad")
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

        for pd_blk in pds:
            pd_start = pd_blk.get("start")
            pd_end = pd_blk.get("end")
            if not (isinstance(pd_start, datetime) and isinstance(pd_end, datetime)):
                continue
            mid = pd_start + (pd_end - pd_start) / 2

            # Score: cluster_hit + jup_hit + sat_hit
            cluster_hit = 1
            if pd_blk.get("pd") in target_lords:
                cluster_hit = 2

            transit = _get_transits_at(lagna_si, moon_si, when=mid) if lagna_si is not None else {}
            jup_hit = _jupiter_on_marriage_house(transit, h7_si, venus_si) if h7_si is not None else False
            sat_hit = _saturn_seventh_from_moon(transit, moon_si) if moon_si is not None else False

            score = cluster_hit + (1 if jup_hit else 0) + (1 if sat_hit else 0)
            if score >= 2:
                windows.append({
                    "start": pd_start, "end": pd_end, "score": score,
                    "md": md, "ad": ad, "pd": pd_blk.get("pd"),
                    "jup": jup_hit, "sat": sat_hit,
                })

    factors.append(f"L4: {len(windows)} candidate PD windows after confluence")

    # ── LAYER 5 — Reality Filter (age gate) ──────────────────────
    age = _get_current_age(birth, kundli, current_dasha)
    birth_year = _extract_birth_year(birth)
    if age is not None:
        factors.append(f"L5: current_age={age}, birth_year={birth_year}")

    valid_windows: List[dict] = []
    blocked_count = 0
    for w in windows:
        predicted_year = w["start"].year
        predicted_age = (predicted_year - birth_year) if (birth_year and birth_year > 0) else None
        action = _age_filter_action(age, predicted_age) if predicted_age is not None else "OK"
        if action in ("BLOCK", "PUSH_LATER"):
            blocked_count += 1
            continue
        w["age_action"] = action
        w["predicted_age"] = predicted_age
        valid_windows.append(w)

    factors.append(f"L5: {len(valid_windows)} windows survived (blocked={blocked_count})")

    # If ALL candidate windows were blocked by Layer 5 (and there WERE
    # candidates), downgrade verdict to PREMATURE for trust consistency.
    # Promised marriage exists in the chart, but the engine refuses to
    # quote a window because the user is currently too young.
    if windows and not valid_windows and final_verdict == "PROMISED":
        final_verdict = "PREMATURE"
        factors.append("L5 DOWNGRADE: PROMISED -> PREMATURE (all windows blocked by age gate)")
        risk_flag = risk_flag or "Below marriageable age"
        if "Below marriageable age" not in risk_flags:
            risk_flags.insert(0, "Below marriageable age")

    # Sort by (score desc, start asc) — best scoring + soonest first
    valid_windows.sort(key=lambda w: (-w["score"], w["start"]))

    primary_window = None
    backup_window = None
    key_trigger = None
    confluence_strength = None  # "STRONG" if score>=3 else "MODERATE"

    def _trigger_str(w: dict) -> str:
        parts = [f"{w['ad']} AD", f"{w['pd']} PD"]
        if w["jup"]:
            parts.append("Jupiter on 7H/Venus")
        if w["sat"]:
            parts.append("Saturn 7th-from-Moon")
        return " + ".join(parts)

    if valid_windows:
        p = valid_windows[0]
        primary_window = _format_window(p["start"], p["end"])
        key_trigger = _trigger_str(p)
        confluence_strength = "STRONG" if p["score"] >= 3 else "MODERATE"
        factors.append(f"L4 PRIMARY: {primary_window} (score={p['score']}, "
                       f"{confluence_strength} confluence)")

        # Backup = next valid window in a DIFFERENT AD (so user has a
        # genuinely different timing option, not just a sibling PD).
        for w in valid_windows[1:]:
            if w["ad"] != p["ad"]:
                bk_str = _format_window(w["start"], w["end"])
                # Disambiguate when calendar months overlap with primary
                if bk_str == primary_window:
                    bk_str = f"{bk_str} ({w['ad']} AD)"
                backup_window = bk_str
                factors.append(f"L4 BACKUP: {backup_window} (score={w['score']}, AD={w['ad']})")
                break

    return {
        "verdict": final_verdict,
        "band": band,
        "primary_window": primary_window,
        "backup_window": backup_window,
        "key_trigger": key_trigger,
        "confluence_strength": confluence_strength,
        "ul_outlook": None,   # Love engine's job, merged at narrator layer
        "risk_flag": risk_flag,
        "risk_flags": risk_flags,
        "factors": factors,
    }

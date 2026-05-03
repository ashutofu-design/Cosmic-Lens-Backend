"""Marriage Engine Validator (Guard Layer).

ADD-ONLY module. Independently re-derives canonical facts from the DB
kundli/chart and cross-checks the engine output. Does NOT modify any
existing engine logic. Output appended to assess_marriage return as
`validator_report`.

Architecture role: Engine = Truth (compute), Validator = Guard (verify).

Checks performed:
  C1  Lagna sign + index sanity
  C2  7H sign derivation (lagna + 6) matches engine
  C3  7L planet (lord of 7H sign) + its natal sign present in chart
  C4  KP 7CSL strong/weak presence (informational)
  C5  D1 promiser scan: planets in/aspecting 7H or conjunct 7L (Ven/Jup/
      Mer/Moon/Rahu connections)
  C6  D9 marriage-area scan: planets conjunct 7L in D9
  C7  For each chronological_top3 window: re-run DTT scan independently
      and confirm Jup+Sat hit 7H sign or natal 7L sign as engine claims
  C8  Top-3 chronology: must be sorted by start date ascending
  C9  Verdict band consistency (DELAYED/PROMISED/DENIED vs band)
  C10 Min-age gate: no window earlier than birth_year + early_thr
  C11 SCHEMA: all required output fields present + correct types
  C12 PLANET PARITY: all 9 planets present in chart with valid sign+house
  C13 PRIMARY CROSS-CHECK: primary_window appears in top_3_windows AND
      engine's d1_d9 promisers ⊆ validator-derived promisers
  C14 HELPER SANITY: KP, dasha, ashtakavarga, transits all returned data
  C15 ERROR LEAK: no exception strings or None-where-bool in output dict
  C16 TRANSIT EPHEMERIS: Jupiter+Saturn signs sampled across 30 years —
      every sample valid sign, expected transition cadence (~12mo Jup,
      ~30mo Sat), no missing data
  C17 TRANSIT PARITY: engine's _get_transits_at(today) matches a fresh
      compute_transits() call at the SAME instant (deterministic)
  C18 EPHEMERIS GROUND-TRUTH: direct Swiss Ephemeris spot-checks at 5
      future dates verify compute_transits itself — catches regressions
      in the canonical ephemeris layer, not just wrapper drift
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .marriage_timing import (
    _SIGNS, _SIGN_LORDS,
    _planet_sign_idx, _planet_house_local,
    _get_transits_at, _jup_sat_marriage_cluster_check,
    _dtt_score_window, _extract_birth_year,
    _get_d9_chart, _is_jupiter_aspect, _is_saturn_aspect, _is_mars_aspect,
)


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════
def _safe_si(sign: Optional[str]) -> Optional[int]:
    return _SIGNS.index(sign) if sign in _SIGNS else None


def _planet_by_name(planets: list, name: str) -> Optional[dict]:
    if not isinstance(planets, list) or not name:
        return None
    for p in planets:
        if isinstance(p, dict) and p.get("name") == name:
            return p
    return None


def _seventh_lord_from_chart(planets: list, lagna_si: int
                              ) -> Tuple[Optional[str], Optional[int]]:
    """Independently compute 7L name + natal sign idx from chart only.
    Does NOT rely on intel.house_lords (which can be missing/incomplete).
    """
    if lagna_si is None:
        return (None, None)
    h7_si = (lagna_si + 6) % 12
    sl_name = _SIGN_LORDS.get(h7_si)
    if not sl_name:
        return (None, None)
    sl_natal_si = _planet_sign_idx(planets, sl_name)
    return (sl_name, sl_natal_si)


def _parse_iso(d: Any) -> Optional[datetime]:
    if isinstance(d, datetime):
        return d
    if isinstance(d, str):
        try:
            return datetime.strptime(d[:10], "%Y-%m-%d")
        except Exception:
            return None
    return None


# ════════════════════════════════════════════════════════════════════
# Individual checks
# ════════════════════════════════════════════════════════════════════
def _check_chart_basics(chart: dict, planets: list) -> Dict[str, Any]:
    """C1-C3: lagna, 7H, 7L derivation."""
    lagna_sign = chart.get("ascendant")
    lagna_si = _safe_si(lagna_sign)
    h7_si = ((lagna_si + 6) % 12) if lagna_si is not None else None
    h7_sign = _SIGNS[h7_si] if h7_si is not None else None
    sl_name, sl_natal_si = _seventh_lord_from_chart(planets, lagna_si) \
        if lagna_si is not None else (None, None)
    sl_natal_sign = _SIGNS[sl_natal_si] if sl_natal_si is not None else None
    sl_house = _planet_house_local(planets, sl_name) if sl_name else None
    issues: List[str] = []
    if lagna_si is None:
        issues.append("C1 FAIL: lagna sign not resolvable from chart")
    if h7_si is None:
        issues.append("C2 FAIL: 7H sign not derivable")
    if sl_name is None:
        issues.append("C3 FAIL: 7L planet not derivable from 7H sign")
    if sl_name and sl_natal_si is None:
        issues.append(f"C3 FAIL: 7L {sl_name} not found in chart planets")
    return {
        "lagna_sign": lagna_sign, "lagna_si": lagna_si,
        "h7_sign": h7_sign, "h7_si": h7_si,
        "seventh_lord": sl_name,
        "seventh_lord_natal_sign": sl_natal_sign,
        "seventh_lord_natal_si": sl_natal_si,
        "seventh_lord_house": sl_house,
        "issues": issues,
    }


def _check_d1_promisers_independent(planets: list, h7_si: int,
                                      sl_natal_si: Optional[int],
                                      seventh_lord: Optional[str]
                                      ) -> Dict[str, Any]:
    """C5: independent D1 scan — find every planet connected to 7H or 7L."""
    if h7_si is None:
        return {"connections": [], "promisers": [], "deniers": []}

    NINE = ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu"]
    p_by = {p.get("name"): p for p in planets if isinstance(p, dict)}
    connections: List[Dict[str, Any]] = []
    promisers: List[str] = []
    deniers: List[str] = []

    def _aspect_label(planet: str, p_si: int, t_si: int) -> str:
        diff = (t_si - p_si) % 12
        if diff == 6:
            return "7th"
        if planet == "Mars" and _is_mars_aspect(p_si, t_si):
            return "4th" if diff == 3 else ("8th" if diff == 7 else "")
        if planet == "Jupiter" and _is_jupiter_aspect(p_si, t_si):
            return "5th" if diff == 4 else ("9th" if diff == 8 else "")
        if planet == "Saturn" and _is_saturn_aspect(p_si, t_si):
            return "3rd" if diff == 2 else ("10th" if diff == 9 else "")
        return ""

    for nm in NINE:
        p = p_by.get(nm)
        if not p:
            continue
        sg = p.get("sign")
        si = _safe_si(sg)
        if si is None:
            continue
        sit_7h = (si == h7_si)
        asp_7h = _aspect_label(nm, si, h7_si) if not sit_7h else ""
        conj_7l = (sl_natal_si is not None and si == sl_natal_si
                   and nm != seventh_lord)
        asp_7l = ""
        if (sl_natal_si is not None and not conj_7l
                and si != sl_natal_si and nm != seventh_lord):
            asp_7l = _aspect_label(nm, si, sl_natal_si)

        connected = sit_7h or bool(asp_7h) or conj_7l or bool(asp_7l)
        if not connected:
            continue
        kind = []
        if sit_7h: kind.append("sits 7H")
        if asp_7h: kind.append(f"aspects 7H ({asp_7h})")
        if conj_7l: kind.append(f"conj 7L ({_SIGNS[sl_natal_si]})")
        if asp_7l: kind.append(f"aspects 7L ({asp_7l})")

        is_promiser = nm in ("Jupiter", "Venus", "Moon", "Mercury", "Rahu")
        is_denier = nm in ("Mars", "Saturn")
        connections.append({
            "planet": nm, "sign": sg, "house": p.get("house"),
            "how": ", ".join(kind),
            "role": "promiser" if is_promiser else
                    ("denier" if is_denier else "neutral"),
        })
        if is_promiser:
            promisers.append(nm)
        if is_denier:
            deniers.append(nm)

    return {
        "connections": connections,
        "promisers": promisers,
        "deniers": deniers,
        "promiser_count": len(promisers),
        "denier_count": len(deniers),
    }


def _check_d9_promisers_independent(planets: list, asc_lon: Optional[float],
                                      seventh_lord: Optional[str]
                                      ) -> Dict[str, Any]:
    """C6: D9 conjunctions with 7L. Independent re-run."""
    out: Dict[str, Any] = {"d9_promisers": [], "d9_7l_sign": None,
                           "samples": []}
    if not seventh_lord:
        return out
    try:
        d9 = _get_d9_chart(planets, asc_lon) or {}
        d9p = d9.get("planets") if isinstance(d9.get("planets"), dict) else d9
        if not isinstance(d9p, dict):
            return out
        sl_d9 = (d9p.get(seventh_lord) or {}).get("sign")
        sl_d9_si = _safe_si(sl_d9)
        out["d9_7l_sign"] = sl_d9
        if sl_d9_si is None:
            return out
        for nm in ("Jupiter", "Venus", "Moon", "Mercury", "Rahu", "Mars"):
            if nm == seventh_lord:
                continue
            dp = d9p.get(nm) or {}
            sg = dp.get("sign")
            si = _safe_si(sg)
            out["samples"].append({"planet": nm, "d9_sign": sg})
            if si is not None and si == sl_d9_si:
                out["d9_promisers"].append(f"{nm} conj 7L in D9 ({sg})")
    except Exception as exc:
        out["error"] = f"D9 scan failed: {exc}"
    return out


def _verify_window_dtt(window: Dict[str, Any], lagna_si: int,
                        moon_si: Optional[int], h7_si: int,
                        sl_natal_si: Optional[int]) -> Dict[str, Any]:
    """C7: independently re-run DTT scan for one engine-claimed window."""
    start = _parse_iso(window.get("start") or window.get("start_iso"))
    end = _parse_iso(window.get("end") or window.get("end_iso"))
    if not (start and end and end > start):
        return {"verified": False, "reason": "invalid window dates"}
    scan = _dtt_score_window(start, end, lagna_si, moon_si,
                              h7_si, sl_natal_si, samples=5)
    claimed_dtt = window.get("dtt_count")
    claimed_single = window.get("single_count")
    dtt_match = (claimed_dtt is None or claimed_dtt == scan["dtt_count"])
    sng_match = (claimed_single is None or claimed_single == scan["single_count"])
    rule = window.get("rule_passed")
    rule_holds = True
    if rule == "DTT" and scan["dtt_count"] < 3:
        rule_holds = False
    if rule == "SINGLE+TRIPLE":
        if scan["single_count"] < 4:
            rule_holds = False
        if int(window.get("triple_promiser") or 0) < 3:
            rule_holds = False
    return {
        "verified": dtt_match and sng_match and rule_holds,
        "engine_dtt": claimed_dtt, "verifier_dtt": scan["dtt_count"],
        "engine_single": claimed_single, "verifier_single": scan["single_count"],
        "rule_claimed": rule, "rule_holds": rule_holds,
        "dtt_match": dtt_match, "single_match": sng_match,
        "samples": scan["details"],
    }


_REQUIRED_OUTPUT_FIELDS: Dict[str, type] = {
    "verdict": str, "band": str,
    "factors": list, "risk_flags": list,
    "top_3_windows": list,
    "step0_tendency": dict,
    "d1_d9_planet_scan": dict,
    "chronological_top3_strict_dtt": list,
}
_OPTIONAL_NULLABLE_FIELDS = {
    "primary_window", "backup_window", "key_trigger",
    "confluence_strength", "ul_outlook", "risk_flag",
}
_NINE_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
                  "Venus", "Saturn", "Rahu", "Ketu"]


def _check_schema(engine_output: dict) -> Dict[str, Any]:
    """C11: required fields present with correct types."""
    issues: List[str] = []
    for k, t in _REQUIRED_OUTPUT_FIELDS.items():
        if k not in engine_output:
            issues.append(f"C11 FAIL: missing required field '{k}'")
            continue
        v = engine_output[k]
        if not isinstance(v, t):
            issues.append(f"C11 FAIL: field '{k}' type={type(v).__name__} "
                          f"expected={t.__name__}")
    for k in _OPTIONAL_NULLABLE_FIELDS:
        if k in engine_output:
            v = engine_output[k]
            if v is not None and not isinstance(v, str):
                issues.append(f"C11 FAIL: optional field '{k}' must be str|None, "
                              f"got {type(v).__name__}")
    return {"issues": issues, "field_count": len(engine_output)}


def _check_planet_parity(planets: list) -> Dict[str, Any]:
    """C12: all 9 planets present with valid sign + house."""
    issues: List[str] = []
    found: Dict[str, Dict[str, Any]] = {}
    for p in planets if isinstance(planets, list) else []:
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        if nm in _NINE_PLANETS:
            found[nm] = {"sign": p.get("sign"), "house": p.get("house")}
    for nm in _NINE_PLANETS:
        if nm not in found:
            issues.append(f"C12 FAIL: planet '{nm}' missing from chart")
            continue
        sg = found[nm]["sign"]; ho = found[nm]["house"]
        if sg not in _SIGNS:
            issues.append(f"C12 FAIL: planet '{nm}' has invalid sign={sg!r}")
        if not isinstance(ho, int) or not (1 <= ho <= 12):
            issues.append(f"C12 FAIL: planet '{nm}' has invalid house={ho!r}")
    return {"issues": issues, "found": found}


def _check_primary_crosscheck(engine_output: dict,
                                verifier_d1_promisers: List[str]
                                ) -> Dict[str, Any]:
    """C13: primary_window must appear in top_3_windows OR be None.
    AND engine's d1_d9_scan promisers must be a subset of the validator's
    independent promiser list (engine should never INVENT promisers).
    """
    issues: List[str] = []
    primary = engine_output.get("primary_window")
    top3 = engine_output.get("top_3_windows") or []
    chrono = engine_output.get("chronological_top3_strict_dtt") or []
    if primary:
        windows_set = {w.get("window") for w in top3 if isinstance(w, dict)}
        chrono_set = {w.get("window") for w in chrono if isinstance(w, dict)}
        if primary not in windows_set and primary not in chrono_set:
            issues.append(
                f"C13 FAIL: primary_window {primary!r} not found in "
                f"top_3_windows or chronological_top3_strict_dtt")

    # Compare ONLY D1 promisers (engine tags D9 ones with "(D9)" suffix).
    # Mixing D1 + D9 sets here would falsely flag legitimate D9-only
    # promisers as "invented" by the engine.
    eng_scan = engine_output.get("d1_d9_planet_scan") or {}
    eng_d1_only = {p for p in (eng_scan.get("promisers") or [])
                   if "(D9)" not in p and "(d9)" not in p}
    ver_proms_clean = set(verifier_d1_promisers or [])
    invented = eng_d1_only - ver_proms_clean
    if invented:
        issues.append(
            f"C13 WARN: engine d1_d9_scan reports D1 promisers not seen "
            f"by verifier: {sorted(invented)}")
    eng_proms_clean = eng_d1_only

    return {"issues": issues,
            "primary_in_top3": (primary in {w.get("window") for w in top3}) if primary else None,
            "primary_in_chrono": (primary in {w.get("window") for w in chrono}) if primary else None,
            "engine_promisers": sorted(eng_proms_clean),
            "verifier_promisers": sorted(ver_proms_clean)}


def _check_helper_sanity(chart: dict) -> Dict[str, Any]:
    """C14: critical helpers (KP, dasha, ashtakavarga, transits) returned data."""
    issues: List[str] = []
    kp = chart.get("kp") or chart.get("kp_engine") or {}
    if not isinstance(kp, dict) or not kp:
        issues.append("C14 WARN: chart.kp absent or empty")
    elif not (kp.get("cuspal_sub_lords") or kp.get("cusps")):
        issues.append("C14 WARN: KP block has no cuspal_sub_lords/cusps")

    vims = (chart.get("vimshottari") or chart.get("vimshottari_dasha")
            or chart.get("dashas"))
    if not vims:
        issues.append("C14 FAIL: vimshottari dasha tree absent from chart "
                      "(checked vimshottari/vimshottari_dasha/dashas)")

    cd = chart.get("currentDasha") or chart.get("current_dasha") or {}
    if not cd:
        issues.append("C14 WARN: currentDasha absent from chart")

    # Ashtakavarga is computed on-the-fly in marriage_timing
    # (_compute_ashtakavarga_for_chart). Not required at chart level —
    # informational only.
    av = chart.get("ashtakavarga") or chart.get("ashtakvarga")

    return {
        "issues": issues,
        "kp_present": bool(kp),
        "dasha_present": bool(vims),
        "current_dasha_present": bool(cd),
        "ashtakavarga_chart_level": bool(av),
        "ashtakavarga_note": ("computed on-the-fly inside engine; "
                              "chart-level absence is OK"),
    }


def _check_error_leak(engine_output: dict) -> Dict[str, Any]:
    """C15: scan output strings for exception/error indicators."""
    issues: List[str] = []
    suspect_keywords = ("Traceback", "Exception", "failed:", "<error",
                         "NoneType has no")
    factors = engine_output.get("factors") or []
    for f in factors:
        if not isinstance(f, str):
            continue
        for kw in suspect_keywords:
            if kw in f:
                issues.append(f"C15 WARN: factor leak '{f[:80]}'")
                break
    rf = engine_output.get("risk_flags") or []
    for r in rf:
        if isinstance(r, str) and any(kw in r for kw in suspect_keywords):
            issues.append(f"C15 WARN: risk_flag leak '{r[:80]}'")
    # Booleans should not be None
    for w in (engine_output.get("top_3_windows") or []):
        if isinstance(w, dict):
            for bk in ("sandhi", "eclipse_flag", "mars_sat_conflict"):
                if bk in w and w[bk] is None:
                    issues.append(f"C15 FAIL: top_3 window has None for boolean '{bk}'")
    return {"issues": issues}


def _check_transit_ephemeris_30yr(lagna_si: Optional[int],
                                     moon_si: Optional[int]
                                     ) -> Dict[str, Any]:
    """C16: Sample Jupiter + Saturn transit signs every ~91 days, anchored
    from TODAY for the next 30 years. Verifies ephemeris coverage,
    transition cadence, and FAILS hard on stagnation.
    """
    issues: List[str] = []
    if lagna_si is None:
        return {"issues": ["C16 SKIP: lagna_si missing"],
                "samples": [], "year_table": [], "transitions": {}}

    today = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
    samples: List[Dict[str, Any]] = []
    bad_count = 0
    for q in range(0, 30 * 4):  # 120 quarterly samples from today forward
        when = today + timedelta(days=91 * q)
        try:
            t = _get_transits_at(lagna_si, moon_si, when=when)
        except Exception as exc:
            issues.append(f"C16 FAIL: ephemeris exception at {when.date()}: {exc}")
            bad_count += 1
            continue
        th = t.get("transit_houses") or {}
        jp = (th.get("Jupiter") or {}) if isinstance(th, dict) else {}
        sp = (th.get("Saturn") or {}) if isinstance(th, dict) else {}
        jup_sg = jp.get("sign")
        sat_sg = sp.get("sign")
        jup_ok = jup_sg in _SIGNS
        sat_ok = sat_sg in _SIGNS
        if not jup_ok:
            bad_count += 1
            issues.append(f"C16 FAIL: Jupiter sign invalid at {when.date()}: {jup_sg!r}")
        if not sat_ok:
            bad_count += 1
            issues.append(f"C16 FAIL: Saturn sign invalid at {when.date()}: {sat_sg!r}")
        samples.append({
            "date": when.strftime("%Y-%m-%d"),
            "jupiter": jup_sg, "saturn": sat_sg,
            "jup_house": jp.get("house_from_lagna"),
            "sat_house": sp.get("house_from_lagna"),
        })

    # Detect transitions and build year-by-year table
    jup_transitions: List[Dict[str, str]] = []
    sat_transitions: List[Dict[str, str]] = []
    last_jup = last_sat = None
    for s in samples:
        if s["jupiter"] and s["jupiter"] != last_jup:
            jup_transitions.append({"date": s["date"],
                                     "from": last_jup or "—",
                                     "to": s["jupiter"]})
            last_jup = s["jupiter"]
        if s["saturn"] and s["saturn"] != last_sat:
            sat_transitions.append({"date": s["date"],
                                     "from": last_sat or "—",
                                     "to": s["saturn"]})
            last_sat = s["saturn"]

    # Cadence sanity (Jupiter ~12mo, Saturn ~30mo per sign)
    # NOTE: Jup/Sat retrograde causes back-tracking across sign boundaries
    # (e.g. Cancer->Leo->Cancer->Leo). Count UNIQUE signs visited as a
    # zodiac progression (full 12-sign cycle ≈ 12yr Jup, ≈ 29.5yr Sat).
    def _zodiac_progression(transitions: List[Dict[str, str]]) -> int:
        """Count net zodiac advance: number of NEW signs reached forward."""
        seen: List[str] = []
        for tr in transitions:
            sg = tr["to"]
            if sg in _SIGNS and (not seen or sg != seen[-1]):
                # only add if forward step (next sign in zodiac order)
                if not seen:
                    seen.append(sg)
                else:
                    nxt = _SIGNS[(_SIGNS.index(seen[-1]) + 1) % 12]
                    if sg == nxt:
                        seen.append(sg)
        return len(seen) - 1  # net forward steps

    avg_jup_mo = avg_sat_mo = 0.0
    jup_steps = sat_steps = 0
    if samples:
        span_yrs = (datetime.strptime(samples[-1]["date"], "%Y-%m-%d")
                    - datetime.strptime(samples[0]["date"], "%Y-%m-%d")).days / 365.25
        jup_steps = _zodiac_progression(jup_transitions)
        sat_steps = _zodiac_progression(sat_transitions)
        avg_jup_mo = (span_yrs * 12 / jup_steps) if jup_steps > 0 else 0
        avg_sat_mo = (span_yrs * 12 / sat_steps) if sat_steps > 0 else 0

        # HARD FAIL on stagnation: in 30 years Jupiter MUST advance ≥20 signs
        # (perfect = 30), Saturn MUST advance ≥8 signs (perfect = 12).
        if span_yrs >= 25 and jup_steps < 20:
            issues.append(f"C16 FAIL: Jupiter forward progression only "
                          f"{jup_steps} signs in {span_yrs:.0f}y (expected ≥20) "
                          f"— ephemeris stuck or broken")
        if span_yrs >= 25 and sat_steps < 8:
            issues.append(f"C16 FAIL: Saturn forward progression only "
                          f"{sat_steps} signs in {span_yrs:.0f}y (expected ≥8) "
                          f"— ephemeris stuck or broken")
        if jup_steps > 0 and not (10 <= avg_jup_mo <= 14):
            issues.append(f"C16 WARN: Jupiter avg sign-stay {avg_jup_mo:.1f}mo "
                          f"(expected ~12mo, {jup_steps} forward steps in {span_yrs:.0f}y)")
        if sat_steps > 0 and not (26 <= avg_sat_mo <= 34):
            issues.append(f"C16 WARN: Saturn avg sign-stay {avg_sat_mo:.1f}mo "
                          f"(expected ~30mo, {sat_steps} forward steps in {span_yrs:.0f}y)")

    # Year table (one row per year showing Jup + Sat signs visited)
    year_table: List[Dict[str, Any]] = []
    by_year: Dict[int, Dict[str, set]] = {}
    for s in samples:
        yr = int(s["date"][:4])
        by_year.setdefault(yr, {"jup": set(), "sat": set()})
        if s["jupiter"]: by_year[yr]["jup"].add(s["jupiter"])
        if s["saturn"]:  by_year[yr]["sat"].add(s["saturn"])
    for yr in sorted(by_year.keys()):
        year_table.append({
            "year": yr,
            "jupiter_signs": sorted(by_year[yr]["jup"]),
            "saturn_signs": sorted(by_year[yr]["sat"]),
        })

    window_start = samples[0]["date"] if samples else None
    window_end = samples[-1]["date"] if samples else None
    return {
        "issues": issues,
        "samples_taken": len(samples),
        "bad_samples": bad_count,
        "window_start": window_start,
        "window_end": window_end,
        "window_note": ("rolling 30-year window anchored to today (utcnow); "
                        "advances every time validator runs"),
        "jup_forward_steps": jup_steps,
        "sat_forward_steps": sat_steps,
        "jup_avg_sign_stay_months": round(avg_jup_mo, 1),
        "sat_avg_sign_stay_months": round(avg_sat_mo, 1),
        "jupiter_transitions": jup_transitions,
        "saturn_transitions": sat_transitions,
        "year_table": year_table,
    }


def _check_transit_parity_today(lagna_si: Optional[int],
                                  moon_si: Optional[int]
                                  ) -> Dict[str, Any]:
    """C17: engine's _get_transits_at(when=T) must match a direct
    compute_transits(when=T) call at the SAME deterministic instant.
    Both sign AND house must match. Missing planet entries = FAIL.
    """
    issues: List[str] = []
    out: Dict[str, Any] = {"issues": issues, "compared": {}}
    if lagna_si is None:
        issues.append("C17 SKIP: lagna_si missing")
        return out

    when = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
    try:
        eng = _get_transits_at(lagna_si, moon_si, when=when)
    except Exception as exc:
        issues.append(f"C17 FAIL: engine transit call raised: {exc}")
        return out
    try:
        from transits import compute_transits
        direct = compute_transits(lagna_si, moon_si, when=when) or {}
    except Exception as exc:
        issues.append(f"C17 FAIL: direct compute_transits raised: {exc}")
        return out

    e_th = (eng.get("transit_houses") or {})
    d_th = (direct.get("transit_houses") or {})
    # Only check planets that compute_transits actually returns
    for planet in ("Jupiter", "Saturn", "Rahu"):
        e_entry = e_th.get(planet) or {}
        d_entry = d_th.get(planet) or {}
        if not e_entry:
            issues.append(f"C17 FAIL: {planet} missing from engine transits")
            continue
        if not d_entry:
            issues.append(f"C17 FAIL: {planet} missing from direct ephemeris")
            continue
        e_sg, d_sg = e_entry.get("sign"), d_entry.get("sign")
        e_h, d_h = e_entry.get("house_from_lagna"), d_entry.get("house_from_lagna")
        out["compared"][planet] = {"sign": e_sg, "house": e_h,
                                    "match_sign": e_sg == d_sg,
                                    "match_house": e_h == d_h}
        if e_sg != d_sg:
            issues.append(f"C17 FAIL: {planet} sign engine={e_sg!r} vs direct={d_sg!r}")
        if e_h != d_h:
            issues.append(f"C17 FAIL: {planet} house engine={e_h} vs direct={d_h}")
    return out


def _check_ephemeris_ground_truth(lagna_si: Optional[int]) -> Dict[str, Any]:
    """C18: Direct Swiss Ephemeris spot-checks at 5 future dates.
    This bypasses compute_transits entirely — catches regressions in the
    canonical ephemeris layer itself (not just wrapper drift).

    Compares: compute_transits(when=T).Jupiter.sign vs raw swe.calc_ut at T.
    """
    issues: List[str] = []
    out: Dict[str, Any] = {"issues": issues, "spot_checks": [],
                            "swe_available": False}
    if lagna_si is None:
        issues.append("C18 SKIP: lagna_si missing")
        return out
    try:
        import swisseph as swe  # type: ignore
        from transits import compute_transits, _SIGN_NAMES
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    except Exception as exc:
        issues.append(f"C18 SKIP: Swiss Ephemeris unavailable: {exc}")
        return out
    out["swe_available"] = True

    today = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
    # Spot-check at +0, +2, +5, +10, +20 years
    test_offsets_years = [0, 2, 5, 10, 20]
    bodies = {"Jupiter": swe.JUPITER, "Saturn": swe.SATURN}

    for yr_off in test_offsets_years:
        when = today.replace(year=today.year + yr_off)
        # raw swisseph
        raw_signs: Dict[str, str] = {}
        try:
            jd = swe.julday(when.year, when.month, when.day,
                             when.hour + when.minute / 60.0)
            for name, pid in bodies.items():
                pos, _ = swe.calc_ut(jd, pid, flags)
                lon = float(pos[0]) % 360.0
                raw_signs[name] = _SIGN_NAMES[int(lon / 30.0) % 12]
        except Exception as exc:
            issues.append(f"C18 FAIL: raw swe.calc_ut at {when.date()}: {exc}")
            continue
        # compute_transits
        try:
            ct = compute_transits(lagna_si, lagna_si, when=when) or {}
            ct_th = ct.get("transit_houses") or {}
        except Exception as exc:
            issues.append(f"C18 FAIL: compute_transits at {when.date()}: {exc}")
            continue

        row: Dict[str, Any] = {"date": when.strftime("%Y-%m-%d")}
        for name in bodies:
            raw_sg = raw_signs.get(name)
            ct_sg = (ct_th.get(name) or {}).get("sign")
            row[name] = {"raw_swe": raw_sg, "compute_transits": ct_sg,
                          "match": raw_sg == ct_sg}
            if raw_sg != ct_sg:
                issues.append(f"C18 FAIL: {name} at {when.date()} "
                              f"raw_swe={raw_sg!r} vs compute_transits={ct_sg!r}")
        out["spot_checks"].append(row)
    return out


def _check_chronology_and_age(chrono: List[Dict[str, Any]],
                                birth_year: Optional[int]
                                ) -> Dict[str, Any]:
    """C8 + C10: chronological order + min-age gate."""
    issues: List[str] = []
    last_dt: Optional[datetime] = None
    for w in chrono:
        sd = _parse_iso(w.get("start_iso") or w.get("start"))
        if sd is None:
            issues.append(f"C8 WARN: window {w.get('window')} has no parseable start")
            continue
        if last_dt and sd < last_dt:
            issues.append(f"C8 FAIL: window {w.get('window')} out of chronological order")
        last_dt = sd
        if birth_year:
            age_at = sd.year - birth_year
            if age_at < 18:
                issues.append(f"C10 FAIL: window {w.get('window')} predicts age {age_at} (<18)")
    return {"issues": issues, "ordered": all("C8 FAIL" not in i for i in issues)}


# ════════════════════════════════════════════════════════════════════
# Main entry point
# ════════════════════════════════════════════════════════════════════
def validate_marriage_assessment(chart: dict, birth: Any,
                                   intel: dict,
                                   engine_output: dict) -> Dict[str, Any]:
    """Run all guard checks. Returns a report dict.

    Top-level fields:
      pass:           bool   (all checks passed)
      severity:       "OK" | "WARN" | "FAIL"
      summary:        one-line human-readable
      checks:         {C1..C10: {...}}
      mismatches:     [str]  — engine vs verifier disagreements
      warnings:       [str]
    """
    report: Dict[str, Any] = {
        "pass": True, "severity": "OK", "summary": "",
        "checks": {}, "mismatches": [], "warnings": [],
    }
    if not isinstance(chart, dict):
        return {"pass": False, "severity": "FAIL",
                "summary": "no chart provided", "checks": {},
                "mismatches": [], "warnings": []}

    planets = chart.get("planets") or []
    moon = _planet_by_name(planets, "Moon")
    moon_si = _safe_si(moon.get("sign")) if moon else None
    asc_lon = chart.get("ascendantDeg")

    # ── C1-C3 chart basics
    basics = _check_chart_basics(chart, planets)
    report["checks"]["C1_C3_basics"] = basics
    if basics["issues"]:
        report["mismatches"].extend(basics["issues"])
    lagna_si = basics["lagna_si"]
    h7_si = basics["h7_si"]
    sl_name = basics["seventh_lord"]
    sl_natal_si = basics["seventh_lord_natal_si"]

    # ── C4 KP 7CSL informational
    kp_info = chart.get("kp") or chart.get("kp_engine") or {}
    csl_block = (kp_info.get("cuspal_sub_lords") or {}).get("7") \
                if isinstance(kp_info.get("cuspal_sub_lords"), dict) else None
    report["checks"]["C4_kp_7csl"] = {
        "kp_present": bool(kp_info),
        "cusp7_csl": (csl_block or {}).get("sub_lord") if isinstance(csl_block, dict) else None,
        "verdict": (csl_block or {}).get("verdict") if isinstance(csl_block, dict) else None,
    }

    # ── C5 D1 independent promiser scan
    if h7_si is not None:
        d1_check = _check_d1_promisers_independent(
            planets, h7_si, sl_natal_si, sl_name)
        report["checks"]["C5_d1_promisers"] = d1_check
        # Cross-check vs engine's d1_d9_planet_scan
        eng_scan = engine_output.get("d1_d9_planet_scan") or {}
        eng_proms = set(eng_scan.get("promisers") or [])
        ver_proms = set(d1_check.get("promisers") or [])
        missing_in_engine = ver_proms - eng_proms
        if missing_in_engine:
            report["mismatches"].append(
                f"C5: engine d1_d9_scan missed promisers: {sorted(missing_in_engine)} "
                f"(verifier found: {sorted(ver_proms)})")
    else:
        report["checks"]["C5_d1_promisers"] = {"skipped": "no h7_si"}

    # ── C6 D9 independent scan
    d9_check = _check_d9_promisers_independent(planets, asc_lon, sl_name)
    report["checks"]["C6_d9_promisers"] = d9_check

    # ── C7 verify each chronological_top3 window
    chrono = engine_output.get("chronological_top3_strict_dtt") or []
    win_reports: List[Dict[str, Any]] = []
    if lagna_si is not None and h7_si is not None:
        for w in chrono:
            v = _verify_window_dtt(w, lagna_si, moon_si, h7_si, sl_natal_si)
            v["window"] = w.get("window")
            v["dasha"] = f"{w.get('md')}-{w.get('ad')}-{w.get('pd')}"
            win_reports.append(v)
            if not v.get("verified"):
                report["mismatches"].append(
                    f"C7: window {v['window']} ({v['dasha']}) failed independent DTT verify "
                    f"(engine={v['engine_dtt']}/5 vs verifier={v['verifier_dtt']}/5, "
                    f"rule_holds={v['rule_holds']})")
    report["checks"]["C7_window_verifier"] = win_reports

    # ── C8 + C10 chronology + age gate
    by = _extract_birth_year(birth) if isinstance(birth, dict) else None
    chrono_check = _check_chronology_and_age(chrono, by)
    report["checks"]["C8_C10_chronology_age"] = chrono_check
    if chrono_check["issues"]:
        for it in chrono_check["issues"]:
            if it.startswith("C8 FAIL") or it.startswith("C10 FAIL"):
                report["mismatches"].append(it)
            else:
                report["warnings"].append(it)

    # ── C9 verdict / band consistency
    verdict = engine_output.get("verdict")
    band = engine_output.get("band")
    primary = engine_output.get("primary_window")
    issues_c9: List[str] = []
    if verdict == "DENIED" and chrono:
        issues_c9.append(f"C9 FAIL: verdict=DENIED but {len(chrono)} chrono windows present")
    if verdict in ("PROMISED", "DELAYED") and not primary and not chrono:
        issues_c9.append(f"C9 WARN: verdict={verdict} but no primary_window or chrono windows")
    if band == "DENIED" and verdict != "DENIED":
        issues_c9.append(f"C9 WARN: band=DENIED but verdict={verdict}")
    report["checks"]["C9_verdict_band"] = {
        "verdict": verdict, "band": band, "primary_window": primary,
        "chrono_count": len(chrono), "issues": issues_c9,
    }
    for it in issues_c9:
        if "FAIL" in it:
            report["mismatches"].append(it)
        else:
            report["warnings"].append(it)

    # ── C11 schema
    sch = _check_schema(engine_output)
    report["checks"]["C11_schema"] = sch
    for it in sch["issues"]:
        (report["mismatches"] if "FAIL" in it else report["warnings"]).append(it)

    # ── C12 planet parity
    pp = _check_planet_parity(planets)
    report["checks"]["C12_planet_parity"] = pp
    for it in pp["issues"]:
        report["mismatches"].append(it)

    # ── C13 primary cross-check
    ver_proms = (report["checks"].get("C5_d1_promisers") or {}).get("promisers") or []
    pc = _check_primary_crosscheck(engine_output, ver_proms)
    report["checks"]["C13_primary_crosscheck"] = pc
    for it in pc["issues"]:
        (report["mismatches"] if "FAIL" in it else report["warnings"]).append(it)

    # ── C14 helper sanity
    hs = _check_helper_sanity(chart)
    report["checks"]["C14_helper_sanity"] = hs
    for it in hs["issues"]:
        (report["mismatches"] if "FAIL" in it else report["warnings"]).append(it)

    # ── C15 error leak
    el = _check_error_leak(engine_output)
    report["checks"]["C15_error_leak"] = el
    for it in el["issues"]:
        (report["mismatches"] if "FAIL" in it else report["warnings"]).append(it)

    # ── C16 transit ephemeris 30-year sanity
    te = _check_transit_ephemeris_30yr(lagna_si, moon_si)
    report["checks"]["C16_transit_ephemeris_30yr"] = te
    for it in te["issues"]:
        (report["mismatches"] if "FAIL" in it else report["warnings"]).append(it)

    # ── C17 transit parity today (engine vs direct compute_transits)
    tp = _check_transit_parity_today(lagna_si, moon_si)
    report["checks"]["C17_transit_parity_today"] = tp
    for it in tp["issues"]:
        (report["mismatches"] if "FAIL" in it else report["warnings"]).append(it)

    # ── C18 ephemeris ground-truth (raw Swiss Ephemeris spot-checks)
    eg = _check_ephemeris_ground_truth(lagna_si)
    report["checks"]["C18_ephemeris_ground_truth"] = eg
    for it in eg["issues"]:
        (report["mismatches"] if "FAIL" in it else report["warnings"]).append(it)

    # ── Final roll-up
    if report["mismatches"]:
        report["pass"] = False
        report["severity"] = "FAIL"
        report["summary"] = f"{len(report['mismatches'])} mismatch(es) found"
    elif report["warnings"]:
        report["severity"] = "WARN"
        report["summary"] = f"all checks passed with {len(report['warnings'])} warning(s)"
    else:
        report["summary"] = (
            f"all checks passed: 7H={basics['h7_sign']} "
            f"7L={sl_name} in {basics['seventh_lord_natal_sign']}, "
            f"{len(chrono)} windows verified")
    return report

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
"""

from __future__ import annotations

from datetime import datetime
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

"""User-spec marriage significator pipeline (Steps 1–5).

STEP 1 (D1) / STEP 2 (D9) — name-only marriage linkage (user rule):
  • 7th house occupants
  • planets aspecting 7th house
  • 7th lord name
  • planets conjunct OR aspecting 7th lord

Then merge → KP validate → rank. Imported by marriage_engine_v2 (lazy).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from divisional_charts import compute_d9  # type: ignore
except Exception:
    compute_d9 = None  # type: ignore

try:
    from event_timing._shared.kp_significator_scan import (
        kp_marriage_cusp_verdict,
        kp_marriage_planet_verdict,
    )
except Exception:
    kp_marriage_planet_verdict = None  # type: ignore
    kp_marriage_cusp_verdict = None  # type: ignore

_PLANETS_9 = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]
_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_SIGN_IDX = {s: i for i, s in enumerate(_SIGNS)}
_SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun",
    5: "Mercury", 6: "Venus", 7: "Mars", 8: "Jupiter",
    9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
_OWN_SIGNS: Dict[str, Set[int]] = {
    "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
    "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
}
_FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
_ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}
_EXALT = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5,
          "Jupiter": 3, "Venus": 11, "Saturn": 6}
_DEBIL = {"Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11,
          "Jupiter": 9, "Venus": 5, "Saturn": 0}
_MARRIAGE_HOUSES = [2, 7, 11]
_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
_BENEFICS = {"Moon", "Mercury", "Jupiter", "Venus"}

# Discrete weights (user spec)
_W_D1_7L = 5
_W_D9_7L = 6
_W_D1_IN_7H = 4
_W_D9_IN_7H = 5
_W_D1_ASPECT_7H = 3
_W_D9_ASPECT_7H = 4
_W_D1_WITH_7L = 3
_W_D9_WITH_7L = 4
_W_KP_2711 = 6
_W_BOTH_D1_D9 = 6
_MIN_NATAL_PROMISE = 8  # minimum total on top significator for "promise"
_KP_PROMISE_WEIGHTS = {2: 2.0, 7: 4.0, 11: 2.5}
_KP_NEGATION_WEIGHTS = {1: 1.0, 6: 2.5, 8: 3.0, 10: 1.0, 12: 2.5}
_KP_SECONDARY_PROMISE_WEIGHTS = {"pl": 0.5, "nl": 0.75}
_KP_CSL_BONUS = {"CONFIRMS": 2.0, "PARTIAL": 0.5, "DENIES": -2.0}
_STEP5_KP_AUTHORITY_MULT = 1.35
_STEP5_D9_PRIORITY_MULT = 0.25
_STEP5_D9_PRIORITY_CAP = 3.0
_STEP5_KP_DENY_PENALTY = 4.0
_STEP5_PROTECTED_DENY_PENALTY = 2.0
_MIN_DASHA_TARGET_SCORE = 8.0
_MIN_PROTECTED_TARGET_SCORE = 5.0


def _house_lord(lagna_si: int, house: int) -> str:
    return _SIGN_LORDS[(lagna_si + house - 1) % 12]


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
            s = p.get("sign")
            if isinstance(s, str):
                return _SIGN_IDX.get(s)
    return None


def _planet_record(planets: List[dict], pname: str) -> Optional[dict]:
    for p in planets or []:
        if isinstance(p, dict) and p.get("name") == pname:
            return p
    return None


def _aspects_target(aspector: str, ap_si: int, target_si: int) -> bool:
    diff = (target_si - ap_si) % 12 + 1
    if diff == 7:
        return True
    if aspector == "Mars" and diff in (4, 8):
        return True
    if aspector == "Jupiter" and diff in (5, 9):
        return True
    if aspector == "Saturn" and diff in (3, 10):
        return True
    return False


def _dignity(pname: str, sign_si: Optional[int]) -> str:
    if sign_si is None:
        return "unknown"
    if pname in _EXALT and sign_si == _EXALT[pname]:
        return "exalted"
    if pname in _DEBIL and sign_si == _DEBIL[pname]:
        return "debilitated"
    if sign_si in _OWN_SIGNS.get(pname, set()):
        return "own"
    sign_lord = _SIGN_LORDS.get(sign_si)
    if sign_lord in _FRIENDS.get(pname, set()):
        return "friend"
    if sign_lord in _ENEMIES.get(pname, set()):
        return "enemy"
    return "neutral"


def _is_combust(p: Optional[dict], planets: List[dict]) -> bool:
    if not isinstance(p, dict):
        return False
    if p.get("combust") is True:
        return True
    if p.get("isCombust") is True:
        return True
    if not p.get("sign"):
        return False
    sun_si = _planet_sign_idx(planets, "Sun")
    p_si = _planet_sign_idx(planets, p.get("name", ""))
    if sun_si is None or p_si is None:
        return False
    if p.get("name") in ("Sun", "Rahu", "Ketu"):
        return False
    return p_si == sun_si


def _is_retrograde(p: Optional[dict]) -> bool:
    if not isinstance(p, dict):
        return False
    return bool(p.get("retrograde") or p.get("isRetrograde") or p.get("retro"))


def _conjuncts_in_sign(planets: List[dict], pname: str, target_si: int) -> List[str]:
    out = []
    for p in planets or []:
        n = p.get("name")
        if not n or n == pname:
            continue
        si = _planet_sign_idx(planets, n)
        if si == target_si:
            out.append(n)
    return out


def _load_d9(kundli: dict) -> Tuple[dict, Optional[int], Optional[str]]:
    if compute_d9 is None:
        return {}, None, None
    planets = kundli.get("planets") or []
    lagna_lon = (
        kundli.get("ascendantLon") or kundli.get("ascendantLongitude")
        or kundli.get("lagnaLon") or kundli.get("ascendantDeg")
    )
    try:
        lagna_lon = float(lagna_lon) if lagna_lon is not None else None
    except (TypeError, ValueError):
        lagna_lon = None
    try:
        d9 = compute_d9(planets, lagna_lon=lagna_lon) or {}
    except Exception:
        return {}, None, None
    d9_lagna = (d9.get("_lagna") or {}).get("sign_idx")
    d9_7l = None
    if isinstance(d9_lagna, int):
        d9_7l = _SIGN_LORDS.get((d9_lagna + 6) % 12)
    return d9, d9_lagna, d9_7l


def step2_d9_names(
    planets: List[dict],
    lagna_si: int,
    d9_chart: Optional[dict] = None,
    d9_lagna_si: Optional[int] = None,
) -> Dict[str, Any]:
    """STEP 2 — same four name-only rules on D9 (Navamsha)."""
    return marriage_step_names(
        planets, lagna_si, "D9",
        d9_chart=d9_chart, d9_lagna_si=d9_lagna_si,
    )


def marriage_step_names(
    planets: List[dict],
    lagna_si: int,
    division: str = "D1",
    d9_chart: Optional[dict] = None,
    d9_lagna_si: Optional[int] = None,
) -> Dict[str, Any]:
    """STEP 1 (D1) or STEP 2 (D9) — user rule: return planet names only.

    Returns:
        seventh_lord: str | None
        planets_in_7th_house: list[str]
        planets_aspecting_7th_house: list[str]
        planets_conjunct_or_aspecting_7th_lord: list[str]
        division: "D1" | "D9"
    """
    if division == "D1":
        seventh_lord = _house_lord(lagna_si, 7)
        h7_si = (lagna_si + 6) % 12
        seventh_lord_si = _planet_sign_idx(planets, seventh_lord) if seventh_lord else None

        def _si(pname: str) -> Optional[int]:
            return _planet_sign_idx(planets, pname)

        def _house(pname: str) -> Optional[int]:
            return _planet_house(planets, pname)

    else:
        if not isinstance(d9_lagna_si, int):
            return {
                "seventh_lord": None,
                "planets_in_7th_house": [],
                "planets_aspecting_7th_house": [],
                "planets_conjunct_or_aspecting_7th_lord": [],
                "division": division,
            }
        seventh_lord = _SIGN_LORDS.get((d9_lagna_si + 6) % 12)
        h7_si = (d9_lagna_si + 6) % 12
        seventh_lord_si = (
            (d9_chart.get(seventh_lord) or {}).get("sign_idx")
            if d9_chart and seventh_lord else None
        )

        def _si(pname: str) -> Optional[int]:
            info = (d9_chart or {}).get(pname) or {}
            si = info.get("sign_idx")
            return si if isinstance(si, int) else None

        def _house(pname: str) -> Optional[int]:
            si = _si(pname)
            if si is None:
                return None
            return ((si - d9_lagna_si) % 12) + 1

    in_7h: List[str] = []
    aspect_7h: List[str] = []
    with_7l: List[str] = []

    for pname in _PLANETS_9:
        p_si = _si(pname)
        if p_si is None:
            continue
        p_house = _house(pname)

        if p_house == 7:
            in_7h.append(pname)

        if h7_si is not None and _aspects_target(pname, p_si, h7_si):
            aspect_7h.append(pname)

        if (
            seventh_lord_si is not None
            and pname != seventh_lord
        ):
            if p_si == seventh_lord_si:
                with_7l.append(pname)
            elif _aspects_target(pname, p_si, seventh_lord_si):
                with_7l.append(pname)

    return {
        "seventh_lord": seventh_lord,
        "planets_in_7th_house": in_7h,
        "planets_aspecting_7th_house": aspect_7h,
        "planets_conjunct_or_aspecting_7th_lord": with_7l,
        "division": division,
    }


def format_marriage_step_names(step: Dict[str, Any]) -> str:
    """Human-readable lines for LLM / logs."""
    div = step.get("division") or "D1"
    sl = step.get("seventh_lord") or "—"
    in7 = ", ".join(step.get("planets_in_7th_house") or []) or "—"
    asp7 = ", ".join(step.get("planets_aspecting_7th_house") or []) or "—"
    w7l = ", ".join(step.get("planets_conjunct_or_aspecting_7th_lord") or []) or "—"
    return (
        f"{div} STEP — marriage linkage (names only):\n"
        f"  • 7th lord: {sl}\n"
        f"  • In 7th house: {in7}\n"
        f"  • Aspects 7th house: {asp7}\n"
        f"  • With 7th lord (conjunct/aspect): {w7l}"
    )


def _division_planet_info(
    pname: str,
    division: str,
    *,
    planets: Optional[List[dict]] = None,
    d9_chart: Optional[dict] = None,
) -> Tuple[Optional[int], Optional[dict]]:
    if division == "D9":
        info = (d9_chart or {}).get(pname) or {}
        si = info.get("sign_idx")
        return (si if isinstance(si, int) else None), info if info else None
    planets = planets or []
    return _planet_sign_idx(planets, pname), _planet_record(planets, pname)


def _strength_adjustment(
    pname: str,
    division: str,
    *,
    planets: Optional[List[dict]] = None,
    d9_chart: Optional[dict] = None,
) -> Tuple[float, List[str]]:
    sign_si, rec = _division_planet_info(
        pname, division, planets=planets, d9_chart=d9_chart,
    )
    dignity = _dignity(pname, sign_si)
    adj = 0.0
    notes: List[str] = []

    if dignity in ("exalted", "own"):
        adj += 2.0
        notes.append(f"{division} {dignity}")
    elif dignity == "friend":
        adj += 1.0
        notes.append(f"{division} friend sign")
    elif dignity == "debilitated":
        adj -= 2.0
        notes.append(f"{division} debilitated")
    elif dignity == "enemy":
        adj -= 1.0
        notes.append(f"{division} enemy sign")

    if division == "D1" and _is_combust(rec, planets or []):
        adj -= 2.0
        notes.append("D1 combust")
    if division == "D1" and _is_retrograde(rec):
        adj -= 1.0
        notes.append("D1 retrograde")

    if pname in {"Venus", "Jupiter"}:
        adj += 1.0
        notes.append(f"{pname} natural marriage karaka")
    elif pname in _BENEFICS:
        adj += 0.5
        notes.append(f"{pname} benefic support")
    elif pname in _MALEFICS:
        adj -= 0.5
        notes.append(f"{pname} malefic pressure")

    return adj, notes


def _pool_from_step_names(
    step: Dict[str, Any],
    *,
    planets: Optional[List[dict]] = None,
    lagna_si: Optional[int] = None,
    d9_chart: Optional[dict] = None,
    d9_lagna_si: Optional[int] = None,
) -> Dict[str, Dict[str, Any]]:
    """Convert name-only step into weighted pool for Steps 3–5."""
    _ = lagna_si, d9_lagna_si
    division = step.get("division") or "D1"
    w_7l = _W_D1_7L if division == "D1" else _W_D9_7L
    w_in_7h = _W_D1_IN_7H if division == "D1" else _W_D9_IN_7H
    w_aspect_7h = _W_D1_ASPECT_7H if division == "D1" else _W_D9_ASPECT_7H
    w_with_7l = _W_D1_WITH_7L if division == "D1" else _W_D9_WITH_7L
    pool: Dict[str, Dict[str, Any]] = {}

    def _add(pname: str, points: float, link: str) -> None:
        if not pname:
            return
        if pname not in pool:
            pool[pname] = {
                "points": 0.0,
                "links": [],
                "in_pool": True,
            }
        pool[pname]["points"] = float(pool[pname]["points"]) + points
        if link not in pool[pname]["links"]:
            pool[pname]["links"].append(link)

    sl = step.get("seventh_lord")
    if sl:
        _add(sl, w_7l, f"{division} 7th lord")

    for p in step.get("planets_in_7th_house") or []:
        _add(p, w_in_7h, f"in {division} 7th house")

    for p in step.get("planets_aspecting_7th_house") or []:
        _add(p, w_aspect_7h, f"aspects {division} 7th house")

    for p in step.get("planets_conjunct_or_aspecting_7th_lord") or []:
        _add(p, w_with_7l, f"conjunct/aspects {division} 7th lord")

    for pname, row in pool.items():
        adj, notes = _strength_adjustment(
            pname, division, planets=planets, d9_chart=d9_chart,
        )
        row["base_points"] = round(float(row.get("points", 0.0)), 2)
        row["strength_adjust"] = round(adj, 2)
        row["strength_notes"] = notes
        row["points"] = round(max(0.0, float(row["base_points"]) + adj), 2)

    return pool


def _extract_division(
    planets: List[dict],
    lagna_si: int,
    division: str,
    d9_chart: Optional[dict] = None,
    d9_lagna_si: Optional[int] = None,
) -> Dict[str, Dict[str, Any]]:
    """Build candidate pool from name-only STEP 1/2 rules."""
    step = marriage_step_names(
        planets, lagna_si, division,
        d9_chart=d9_chart, d9_lagna_si=d9_lagna_si,
    )
    return _pool_from_step_names(
        step,
        planets=planets,
        lagna_si=lagna_si,
        d9_chart=d9_chart,
        d9_lagna_si=d9_lagna_si,
    )


def _step3_merge(
    d1_pool: Dict[str, Dict[str, Any]],
    d9_pool: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    all_names = set(d1_pool) | set(d9_pool)
    for pname in all_names:
        in_d1 = pname in d1_pool
        in_d9 = pname in d9_pool
        d1_pts = float((d1_pool.get(pname) or {}).get("points", 0))
        d9_pts = float((d9_pool.get(pname) or {}).get("points", 0))
        both_bonus = _W_BOTH_D1_D9 if (in_d1 and in_d9) else 0
        d1_strength = float((d1_pool.get(pname) or {}).get("strength_adjust", 0))
        d9_strength = float((d9_pool.get(pname) or {}).get("strength_adjust", 0))
        strength_notes = (
            (d1_pool.get(pname) or {}).get("strength_notes", [])
            + (d9_pool.get(pname) or {}).get("strength_notes", [])
        )
        merged[pname] = {
            "d1_points": d1_pts,
            "d9_points": d9_pts,
            "both_divisions": in_d1 and in_d9,
            "both_bonus": both_bonus,
            "d1_strength_adjust": d1_strength,
            "d9_strength_adjust": d9_strength,
            "strength_adjust": round(d1_strength + d9_strength, 2),
            "strength_notes": strength_notes,
            "in_d1": in_d1,
            "in_d9": in_d9,
            "d1_links": (d1_pool.get(pname) or {}).get("links", []),
            "d9_links": (d9_pool.get(pname) or {}).get("links", []),
            "natal_points": round(d1_pts + d9_pts + both_bonus, 2),
        }
    return merged


def _weighted_kp_points(
    verdict_row: Dict[str, Any],
    csl_verdict: str,
) -> Tuple[float, List[str]]:
    """Weighted KP points: SB decides; PL/NL only add small audit support."""
    sb_houses = verdict_row.get("houses_sb") or []
    nl_houses = verdict_row.get("houses_nl") or []
    pl_houses = verdict_row.get("houses_pl") or []
    promise_hits = verdict_row.get("promise_hits") or []
    negation_hits = verdict_row.get("negation_hits") or []
    verdict = verdict_row.get("verdict", "DENIES")

    points = 0.0
    notes: List[str] = []

    for h in promise_hits:
        w = _KP_PROMISE_WEIGHTS.get(h, 0.0)
        points += w
        notes.append(f"SB promise {h}H +{w:g}")

    for h in negation_hits:
        w = _KP_NEGATION_WEIGHTS.get(h, 0.0)
        points -= w
        notes.append(f"SB negation {h}H -{w:g}")

    if verdict == "CONFIRMS" and promise_hits:
        points += 1.5
        notes.append("KP CONFIRMS +1.5")
    elif verdict == "PARTIAL" and promise_hits:
        points += 0.5
        notes.append("KP PARTIAL +0.5")
    elif verdict == "DENIES":
        points = min(points, 0.0)

    # Secondary support only: never approve without SB promise.
    if promise_hits:
        for layer, houses in (("pl", pl_houses), ("nl", nl_houses)):
            sec_hits = sorted(set(houses) & set(_MARRIAGE_HOUSES))
            if not sec_hits:
                continue
            add = min(1.5, len(sec_hits) * _KP_SECONDARY_PROMISE_WEIGHTS[layer])
            points += add
            notes.append(f"{layer.upper()} secondary promise {sec_hits} +{add:g}")

    csl_adj = _KP_CSL_BONUS.get(csl_verdict, 0.0)
    if csl_adj:
        points += csl_adj
        notes.append(f"7CSL {csl_verdict} {csl_adj:+g}")

    if verdict == "DENIES" and not promise_hits:
        points = min(points, 0.0)
    return max(0.0, round(points, 2)), notes


def _step4_kp_validate(
    kp: dict,
    merged: Dict[str, Dict[str, Any]],
    d1_7l: str,
    d9_7l: Optional[str],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """KP Step 4 — Sub-Lord fruit layer (not NL union).

    Marriage promise on a planet = ``sb_houses`` ∩ {2,7,11}.
    Negation on SB layer = {1,6,8,10,12} → PARTIAL or DENIES.
    NL/PL houses are stored for audit only. D1/D9 7L stays in pool when
    KP denies, but does not earn +6 unless SB confirms/partial.
    """
    kp_details: Dict[str, Dict[str, Any]] = {}
    protected = [d1_7l] + ([d9_7l] if d9_7l else [])
    summary: Dict[str, Any] = {
        "kp_available": bool(kp),
        "valid_planets": [],
        "protected_7l": protected,
        "csl_verdict": "UNKNOWN",
        "csl_planet": None,
        "csl_promise_hits": [],
        "csl_negation_hits": [],
        "marriage_supported": False,
        "kp_rule": "sub_lord_sb_houses",
    }

    if not isinstance(kp, dict) or not kp:
        for pname in merged:
            kp_details[pname] = {
                "kp_valid": pname in protected,
                "kp_points": 0,
                "kp_confidence": "low" if pname in protected else "none",
                "star_lord": None,
                "sub_lord": None,
                "domain_hits": [],
                "negation_hits": [],
                "verdict": "UNKNOWN",
                "note": "KP data unavailable — 7L kept on classical rule",
            }
        summary["marriage_supported"] = False
        summary["support_confidence"] = "unknown"
        return kp_details, summary

    csl_block: Dict[str, Any] = {}
    if kp_marriage_cusp_verdict:
        csl_block = kp_marriage_cusp_verdict(kp, 7)
    summary["csl_planet"] = csl_block.get("csl_planet")
    summary["csl_verdict"] = csl_block.get("verdict", "UNKNOWN")
    summary["csl_promise_hits"] = csl_block.get("promise_hits") or []
    summary["csl_negation_hits"] = csl_block.get("negation_hits") or []

    for pname in merged:
        verdict_row: Dict[str, Any] = {}
        if kp_marriage_planet_verdict:
            verdict_row = kp_marriage_planet_verdict(kp, pname)

        promise_hits = verdict_row.get("promise_hits") or []
        negation_hits = verdict_row.get("negation_hits") or []
        verdict = verdict_row.get("verdict", "DENIES")
        sb_valid = bool(verdict_row.get("kp_valid"))
        kp_points, kp_score_notes = _weighted_kp_points(
            verdict_row, summary["csl_verdict"],
        )
        is_7l = pname in protected

        if sb_valid:
            confidence = "high" if verdict == "CONFIRMS" else "medium"
            if negation_hits:
                note = (
                    f"SB signifies promise H{promise_hits} "
                    f"but negation H{negation_hits} (delay/obstruction); "
                    f"weighted KP={kp_points}"
                )
            else:
                note = f"SB clean promise H{promise_hits}; weighted KP={kp_points}"
            summary["valid_planets"].append(pname)
        elif is_7l:
            confidence = "low"
            note = (
                "7th lord protected in natal pool — SB does not promise 2/7/11 "
                f"(SB houses={verdict_row.get('houses_sb') or []}; "
                f"NL audit={verdict_row.get('houses_nl') or []})"
            )
        else:
            confidence = "none"
            note = (
                "KP denies — Sub-Lord does not signify 2/7/11 "
                f"(SB={verdict_row.get('houses_sb') or []}; "
                f"negation={negation_hits or '—'})"
            )

        kp_valid = sb_valid or is_7l

        kp_details[pname] = {
            "kp_valid": kp_valid,
            "kp_points": kp_points,
            "kp_score_notes": kp_score_notes,
            "kp_confidence": confidence,
            "star_lord": verdict_row.get("nl_lord"),
            "sub_lord": verdict_row.get("sb_lord"),
            "domain_hits": promise_hits,
            "negation_hits": negation_hits,
            "houses_sb": verdict_row.get("houses_sb") or [],
            "houses_nl": verdict_row.get("houses_nl") or [],
            "verdict": verdict,
            "note": note,
        }

    summary["marriage_supported"] = (
        len(summary["valid_planets"]) > 0
        or summary["csl_verdict"] in ("CONFIRMS", "PARTIAL")
    )
    summary["support_confidence"] = (
        "high" if summary["csl_verdict"] == "CONFIRMS" and summary["valid_planets"]
        else "medium" if summary["valid_planets"]
        else "low" if summary["csl_verdict"] in ("CONFIRMS", "PARTIAL")
        else "none"
    )
    return kp_details, summary


def _karaka_rank_bonus(pname: str, m: Dict[str, Any]) -> float:
    """Small floor for natural karakas; never enough to overrule KP/dasha alone."""
    if pname == "Venus":
        return 1.5 if float(m.get("natal_points", 0)) > 0 else 0.0
    if pname == "Jupiter":
        return 1.0 if float(m.get("natal_points", 0)) > 0 else 0.0
    return 0.0


def _step5_rank(
    merged: Dict[str, Dict[str, Any]],
    kp_details: Dict[str, Dict[str, Any]],
    d1_7l: Optional[str] = None,
    d9_7l: Optional[str] = None,
) -> List[Dict[str, Any]]:
    ranked: List[Dict[str, Any]] = []
    protected = {p for p in (d1_7l, d9_7l) if p}
    for pname, m in merged.items():
        kd = kp_details.get(pname) or {}
        natal_points = float(m.get("natal_points", 0))
        kp_points = float(kd.get("kp_points", 0))
        d9_points = float(m.get("d9_points", 0))
        kp_verdict = kd.get("verdict")
        d9_priority_bonus = min(
            _STEP5_D9_PRIORITY_CAP,
            d9_points * _STEP5_D9_PRIORITY_MULT,
        )
        karaka_bonus = _karaka_rank_bonus(pname, m)
        kp_deny_penalty = 0.0
        if kp_verdict == "DENIES":
            kp_deny_penalty = (
                _STEP5_PROTECTED_DENY_PENALTY
                if pname in protected else _STEP5_KP_DENY_PENALTY
            )
        total = (
            natal_points
            + kp_points * _STEP5_KP_AUTHORITY_MULT
            + d9_priority_bonus
            + karaka_bonus
            - kp_deny_penalty
        )
        ranked.append({
            "name": pname,
            "score": round(max(0.0, total), 2),
            "d1_points": m.get("d1_points", 0),
            "d9_points": m.get("d9_points", 0),
            "both_divisions": m.get("both_divisions", False),
            "both_bonus": m.get("both_bonus", 0),
            "strength_adjust": m.get("strength_adjust", 0),
            "strength_notes": m.get("strength_notes", []),
            "natal_points": m.get("natal_points", 0),
            "kp_points": kd.get("kp_points", 0),
            "kp_weighted_points": round(kp_points * _STEP5_KP_AUTHORITY_MULT, 2),
            "d9_priority_bonus": round(d9_priority_bonus, 2),
            "karaka_bonus": round(karaka_bonus, 2),
            "kp_deny_penalty": round(kp_deny_penalty, 2),
            "kp_valid": kd.get("kp_valid", False),
            "kp_confidence": kd.get("kp_confidence"),
            "kp_verdict": kp_verdict,
            "star_lord": kd.get("star_lord"),
            "sub_lord": kd.get("sub_lord"),
            "domain_hits": kd.get("domain_hits", []),
            "links": (m.get("d1_links") or []) + (m.get("d9_links") or []),
            "kp_note": kd.get("note"),
        })
    ranked.sort(key=lambda x: -x["score"])
    return ranked


def _is_dasha_target_candidate(
    row: Dict[str, Any],
    *,
    d1_7l: Optional[str],
    d9_7l: Optional[str],
) -> bool:
    name = row.get("name")
    protected = name in {p for p in (d1_7l, d9_7l) if p}
    score = float(row.get("score", 0))
    kp_verdict = row.get("kp_verdict")
    kp_points = float(row.get("kp_points", 0))
    both = bool(row.get("both_divisions"))
    d9_points = float(row.get("d9_points", 0))

    if kp_verdict == "DENIES" and not protected:
        return False
    threshold = (
        _MIN_PROTECTED_TARGET_SCORE
        if protected and kp_verdict != "DENIES"
        else _MIN_DASHA_TARGET_SCORE
    )
    if score < threshold:
        return False
    if kp_points > 0 or both or d9_points >= _W_D9_7L or protected:
        return True
    return False


def run_user_spec_pipeline(
    kundli: dict,
    kp: dict,
    lagna_si: int,
) -> Dict[str, Any]:
    """Run Steps 1–5; return ranked significators + target lords + summaries."""
    planets = kundli.get("planets") or []
    d1_7l = _house_lord(lagna_si, 7)

    step1_d1 = marriage_step_names(planets, lagna_si, "D1")
    d1_pool = _pool_from_step_names(
        step1_d1,
        planets=planets,
        lagna_si=lagna_si,
    )
    d9_chart, d9_lagna_si, d9_7l = _load_d9(kundli)
    step2_d9 = marriage_step_names(
        planets, lagna_si, "D9",
        d9_chart=d9_chart, d9_lagna_si=d9_lagna_si,
    )
    d9_pool = _pool_from_step_names(
        step2_d9,
        planets=planets,
        lagna_si=lagna_si,
        d9_chart=d9_chart,
        d9_lagna_si=d9_lagna_si,
    )

    merged = _step3_merge(d1_pool, d9_pool)
    kp_details, kp_summary = _step4_kp_validate(kp, merged, d1_7l, d9_7l)
    ranked = _step5_rank(merged, kp_details, d1_7l=d1_7l, d9_7l=d9_7l)

    target_lords: Set[str] = set()
    for r in ranked[:6]:
        if _is_dasha_target_candidate(r, d1_7l=d1_7l, d9_7l=d9_7l):
            target_lords.add(r["name"])

    top = ranked[0] if ranked else {}
    natal_promise = bool(ranked) and float(top.get("score", 0)) >= _MIN_NATAL_PROMISE

    reasoning_parts = [
        format_marriage_step_names(step1_d1).replace("\n", " | "),
        format_marriage_step_names(step2_d9).replace("\n", " | "),
        f"D1 7L={d1_7l}, D9 7L={d9_7l or 'n/a'}",
        f"D1 candidates={len(d1_pool)}, D9 candidates={len(d9_pool)}",
        f"KP valid planets={kp_summary.get('valid_planets', [])}",
        f"KP CSL={kp_summary.get('csl_planet')}/{kp_summary.get('csl_verdict')}",
    ]
    if ranked:
        reasoning_parts.append(
            f"Top significator={ranked[0]['name']} (score={ranked[0]['score']})"
        )

    return {
        "step1_d1": step1_d1,
        "step2_d9": step2_d9,
        "d1_pool": d1_pool,
        "d9_pool": d9_pool,
        "merged": merged,
        "kp_details": kp_details,
        "kp_summary": kp_summary,
        "ranked_significators": ranked,
        "target_lords": target_lords,
        "d1_seventh_lord": d1_7l,
        "d9_seventh_lord": d9_7l,
        "natal_promise": natal_promise,
        "reasoning_summary": "; ".join(reasoning_parts),
        "pipeline_version": "user_spec_v3_kp_sub_lord",
    }

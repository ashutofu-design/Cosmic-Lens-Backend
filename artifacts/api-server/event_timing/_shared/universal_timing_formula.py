"""Universal Timing Formula — Steps 0–5 (no BCP, no KP, no age-bar primary).

Marriage uses marriage_engine_v2 separately.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from event_timing._shared.universal_timing_domains import (
    UNIVERSAL_FORMULA_STEP_ORDER,
    UniversalFormulaConfig,
    build_universal_formula_config,
)

try:
    import divisional_charts as _dc  # type: ignore
except Exception:
    _dc = None  # type: ignore

compute_d2 = getattr(_dc, "compute_d2", None)
compute_d4 = getattr(_dc, "compute_d4", None)
compute_d6 = getattr(_dc, "compute_d6", None)
compute_d7 = getattr(_dc, "compute_d7", None)
compute_d9 = getattr(_dc, "compute_d9", None)
compute_d10 = getattr(_dc, "compute_d10", None)
compute_d11 = getattr(_dc, "compute_d11", None)
compute_d20 = getattr(_dc, "compute_d20", None)
compute_d24 = getattr(_dc, "compute_d24", None)
compute_d30 = getattr(_dc, "compute_d30", None)

try:
    from event_timing._shared.double_transit import check_double_transit  # type: ignore
except Exception:
    check_double_transit = None  # type: ignore

from event_timing._shared.generic_timing_engine import (
    DomainTimingConfig,
    MIN_AD_PD_ACTIVATION,
    _activation_score,
    _aspects_house,
    _classify_lords,
    _flatten_dasha_chain,
    _house_lord,
    _lagna_si,
    _norm_lord,
    _planet_house,
    _planets_in_house,
    _step5_windows,
    pick_primary_timing_window,
)

# Re-import missing private helpers
from event_timing._shared import generic_timing_engine as _gte

_PLANETS_9 = _gte._PLANETS_9
_DASHA_MD, _DASHA_AD, _DASHA_PD = _gte._DASHA_MD, _gte._DASHA_AD, _gte._DASHA_PD
_MIN_GAP_DAYS = _gte._MIN_GAP_DAYS

_ENGINE_ARCH = "UNIVERSAL_TIMING_FORMULA_V1"
_ENGINE_VERSION = "utf_v1.0.0"

_DIV_FN = {
    "D2": compute_d2,
    "D4": compute_d4,
    "D6": compute_d6,
    "D7": compute_d7,
    "D9": compute_d9,
    "D10": compute_d10,
    "D11": compute_d11,
    "D20": compute_d20,
    "D24": compute_d24,
    "D30": compute_d30,
}


def _extract_user_age(birth: Any, kundli: dict) -> Optional[int]:
    now = datetime.utcnow()
    for src in (birth, kundli, (kundli or {}).get("birth") if isinstance(kundli, dict) else None):
        if not isinstance(src, dict):
            continue
        y = src.get("year") or src.get("birthYear")
        m = src.get("month") or src.get("birthMonth") or 6
        d = src.get("day") or src.get("birthDay") or 15
        if isinstance(y, int) and 1900 <= y <= 2100:
            try:
                bd = datetime(int(y), int(m), int(d))
                return max(0, now.year - bd.year - ((now.month, now.day) < (bd.month, bd.day)))
            except (TypeError, ValueError):
                return max(0, now.year - int(y))
    return None


def _step0_age_question_gate(
    cfg: UniversalFormulaConfig,
    *,
    user_age: Optional[int],
    question: str,
) -> dict[str, Any]:
    """Step 0 — user age + delay framing (never reject the question)."""
    min_age = cfg.min_practical_age
    q = (question or "").strip()
    detail_parts: list[str] = []
    if user_age is not None:
        detail_parts.append(f"user age {user_age}")
    detail_parts.append(f"practical reference ~{min_age} for {cfg.domain}")
    age_delay_years = 0
    delay_note = ""
    if user_age is None:
        detail_parts.append("age unknown — proceed with dasha scan")
    elif user_age < min_age:
        age_delay_years = int(min_age - user_age)
        delay_note = (
            f"User abhi {user_age} saal — sawal valid hai; timing answer "
            f"DELAY/PREPARE wala hai (~{min_age}+ saal practical window). "
            f"Near dasha (6 mahine/1 saal) ko actionable job/shaadi mat bolo."
        )
        detail_parts.append(f"delay +{age_delay_years} yr to practical age")
    status = "DELAYED" if age_delay_years else "DONE"
    return {
        "name": "User age + question check",
        "status": status,
        "user_age": user_age,
        "min_practical_age": min_age,
        "age_delay_years": age_delay_years,
        "question_valid": True,
        "question": q[:120],
        "delay_note": delay_note,
        "detail": " · ".join(detail_parts) + (f" · {delay_note}" if delay_note else ""),
    }


def _practical_year_floor(
    user_age: Optional[int],
    min_age: int,
    step0: dict,
) -> int:
    """Earliest calendar year for user-facing answer when young."""
    now_y = datetime.utcnow().year
    delay = int(step0.get("age_delay_years") or 0)
    if delay > 0:
        return now_y + delay
    if user_age is not None and user_age < min_age:
        return now_y + int(min_age - user_age)
    return now_y


def _pick_window_from_year_floor(
    matched: list[dict],
    year_floor: int,
) -> Optional[dict]:
    """Prefer first dasha+transit window on/after practical year floor."""
    eligible = []
    for w in matched:
        start = w.get("start")
        if isinstance(start, datetime) and start.year >= year_floor:
            eligible.append(w)
    if eligible:
        return eligible[0]
    for w in matched:
        start = w.get("start")
        if isinstance(start, datetime):
            return w
    return matched[0] if matched else None


def _lagna_lon(kundli: dict) -> Optional[float]:
    for k in ("ascendantDeg", "ascendantLongitude", "lagnaLongitude"):
        v = kundli.get(k)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return None


def _divisional_chart(kundli: dict, tag: str) -> dict:
    fn = _DIV_FN.get(tag)
    if fn is None:
        return {}
    planets = (kundli or {}).get("planets") or []
    try:
        raw = fn(planets, lagna_lon=_lagna_lon(kundli)) or {}
        if not isinstance(raw, dict):
            return {}
        lagna = raw.get("_lagna") if isinstance(raw.get("_lagna"), dict) else {}
        lagna_sign = lagna.get("sign")
        if not lagna_sign:
            lagna_sign = next(
                (v for k, v in raw.items() if str(k).startswith("lagna_") and isinstance(v, str)),
                None,
            )
        if not lagna_sign:
            return {}
        from event_timing._shared.generic_timing_engine import _sign_idx
        lagna_si = _sign_idx(lagna_sign)
        if lagna_si is None:
            return {}
        normalized_planets: list[dict[str, Any]] = []
        for name, info in raw.items():
            if str(name).startswith("_") or str(name).startswith("lagna_") or not isinstance(info, dict):
                continue
            sign_si = info.get("sign_idx")
            if not isinstance(sign_si, int):
                sign_si = _sign_idx(info.get("sign"))
            if sign_si is None:
                continue
            normalized_planets.append({
                "name": str(name),
                "sign": info.get("sign"),
                "sign_idx": sign_si,
                "house": ((sign_si - lagna_si) % 12) + 1,
            })
        return {"ascendant": lagna_sign, "planets": normalized_planets, "raw": raw}
    except Exception:
        return {}


def _step1_target_houses(
    kundli: dict,
    lagna_si: int,
    cfg: UniversalFormulaConfig,
) -> dict[str, Any]:
    """Step 1 — D1 + divisional target house lords."""
    planets = kundli.get("planets") or []
    primary_h = cfg.target_houses[0] if cfg.target_houses else 1
    d1_lord = _house_lord(lagna_si, primary_h)
    d1_occ = _planets_in_house(planets, primary_h)
    d9 = _divisional_chart(kundli, "D9")
    div = _divisional_chart(kundli, cfg.divisional)
    d9_lord = None
    d9_occ: list[str] = []
    div_lord = None
    div_occ: list[str] = []
    if d9.get("planets"):
        d9_lagna = d9.get("ascendant") or d9.get("lagnaSign")
        d9_si = None
        if isinstance(d9_lagna, str):
            from event_timing._shared.generic_timing_engine import _sign_idx
            d9_si = _sign_idx(d9_lagna)
        if d9_si is not None:
            d9_lord = _house_lord(d9_si, primary_h)
            d9_occ = _planets_in_house(d9.get("planets") or [], primary_h)
    if div.get("planets"):
        div_lagna = div.get("ascendant") or div.get("lagnaSign")
        div_si = None
        if isinstance(div_lagna, str):
            from event_timing._shared.generic_timing_engine import _sign_idx
            div_si = _sign_idx(div_lagna)
        if div_si is not None:
            div_lord = _house_lord(div_si, primary_h)
            div_occ = _planets_in_house(div.get("planets") or [], primary_h)
    return {
        "name": f"Target house & lords ({cfg.label})",
        "status": "DONE",
        "target_houses": cfg.target_houses,
        "divisional": cfg.divisional,
        "d1_house_lord": d1_lord,
        "d1_occupants": d1_occ,
        "d9_house_lord": d9_lord,
        "d9_occupants": d9_occ,
        "div_house_lord": div_lord,
        "div_occupants": div_occ,
        "charts_used": ["D1", "D9"] + ([cfg.divisional] if cfg.divisional != "D9" else []),
        "detail": (
            f"D1 {primary_h}H lord {d1_lord}"
            + (f" · in {primary_h}H {', '.join(d1_occ)}" if d1_occ else "")
            + (f" · D9 lord {d9_lord}" if d9_lord else "")
            + (f" · {cfg.divisional} lord {div_lord}" if div_lord else "")
        ),
    }


def _step2_significators(
    kundli: dict,
    lagna_si: int,
    cfg: UniversalFormulaConfig,
    step1: dict,
) -> tuple[list[dict], dict]:
    """Step 2 — 4-category event givers with weights."""
    planets = kundli.get("planets") or []
    primary_h = cfg.target_houses[0] if cfg.target_houses else 1
    house_lord = step1.get("d1_house_lord") or _house_lord(lagna_si, primary_h)
    scores: dict[str, dict[str, Any]] = {
        p: {"name": p, "categories": [], "score": 0.0, "why": []} for p in _PLANETS_9
    }

    if house_lord in scores:
        scores[house_lord]["categories"].append("house_lord")
        scores[house_lord]["score"] += 4.0
        scores[house_lord]["why"].append(f"{primary_h}H lord")

    for pname in _planets_in_house(planets, primary_h):
        if pname in scores:
            scores[pname]["categories"].append("occupant")
            scores[pname]["score"] += 4.0
            scores[pname]["why"].append(f"occupies {primary_h}H")

    for pname in _PLANETS_9:
        ap = _planet_house(planets, pname)
        if ap and (_aspects_house(pname, ap, primary_h) or pname == house_lord):
            if "aspecting" not in scores[pname]["categories"]:
                scores[pname]["categories"].append("aspecting")
                scores[pname]["score"] += 3.0
                scores[pname]["why"].append(f"aspects/touches {primary_h}H axis")

    for karaka in cfg.natural_karakas:
        if karaka in scores and "karaka" not in scores[karaka]["categories"]:
            scores[karaka]["categories"].append("karaka")
            scores[karaka]["score"] += 3.0
            scores[karaka]["why"].append(f"natural karaka ({cfg.domain})")

    ranked = sorted(
        [v for v in scores.values() if v["score"] > 0],
        key=lambda r: (-len(r["categories"]), -r["score"], r["name"]),
    )
    step2 = {
        "name": "Filter valid significators (4 categories)",
        "status": "DONE" if ranked else "PARTIAL",
        "ranked_top": [
            {
                "name": r["name"],
                "score": round(r["score"], 2),
                "categories": r["categories"],
                "why": r["why"][:4],
            }
            for r in ranked[:8]
        ],
        "detail": " · ".join(
            f"{r['name']}({len(r['categories'])}cat,{r['score']})" for r in ranked[:4]
        ) or "no strong significators",
    }
    return ranked, step2


def _to_domain_cfg(cfg: UniversalFormulaConfig) -> DomainTimingConfig:
    """Bridge to dasha window scanner (no KP)."""
    houses = [(h, 12.0, f"{h}H") for h in cfg.target_houses]
    karakas = [(k, 8.0, f"karaka {k}") for k in cfg.natural_karakas[:4]]
    tags = tuple(
        f"{h}H" for h in cfg.target_houses
    ) + tuple(f"{h}L" for h in cfg.target_houses) + tuple(cfg.natural_karakas)
    return DomainTimingConfig(
        domain=cfg.domain,
        engine_version=_ENGINE_VERSION,
        concern_houses=houses,
        karakas=karakas,
        promote_tags=tags,
        double_transit_houses=list(cfg.target_houses),
        min_current_activation=MIN_AD_PD_ACTIVATION,
    )


def _step3_dasha_activation(
    kundli: dict,
    ranked: list[dict],
    cfg: UniversalFormulaConfig,
    now: datetime,
) -> tuple[list[dict], dict, Optional[dict]]:
    """Step 3 — MD broad, AD trigger from top significators, PD micro."""
    dom_cfg = _to_domain_cfg(cfg)
    top_names = {str(r["name"]) for r in ranked[:6]}
    chain = _flatten_dasha_chain(kundli)
    windows = _step5_windows(chain, ranked, dom_cfg, now, horizon_years=12)
    promote, _ = _classify_lords(ranked, dom_cfg)
    score_map = {str(r["name"]): float(r.get("score") or 0) for r in ranked}

    qualified: list[dict] = []
    for w in windows:
        ad = _norm_lord(w.get("ad"))
        pd = _norm_lord(w.get("pd"))
        if ad in top_names or pd in top_names:
            w = dict(w)
            w["ad_trigger"] = ad in top_names
            w["pd_trigger"] = pd in top_names
            w["pd_micro"] = pd
            w["ad_pd_priority"] = (
                "PEAK" if w["ad_trigger"] and w["pd_trigger"]
                else "STRONG" if w["ad_trigger"]
                else "TRIGGER"
            )
            w["activation_score"] = round(_activation_score(w, promote, score_map), 2)
            qualified.append(w)
    priority_rank = {"PEAK": 0, "STRONG": 1, "TRIGGER": 2}
    qualified.sort(
        key=lambda w: (
            priority_rank.get(str(w.get("ad_pd_priority")), 3),
            -float(w.get("activation_score") or 0),
            w.get("start") or datetime.max,
        )
    )
    primary, next_win, timing_source, _ = pick_primary_timing_window(
        qualified, ranked, promote, now, min_ad_pd=MIN_AD_PD_ACTIVATION,
    )
    step3 = {
        "name": "Dasha activation (MD/AD/PD)",
        "status": "DONE" if qualified else "NONE_FOUND",
        "timing_source": timing_source,
        "candidate_windows": qualified[:5],
        "primary_window": primary,
        "next_window": next_win,
        "selection_policy": "AD+PD > AD > PD; MD is background only",
        "top_significators": [r["name"] for r in ranked[:4]],
        "detail": (
            f"AD trigger lords {', '.join(sorted(top_names)[:4])} · "
            f"windows {len(qualified)}"
        ),
    }
    return qualified, step3, primary


def _step4_double_transit(
    kundli: dict,
    lagna_si: int,
    cfg: UniversalFormulaConfig,
    candidates: list[dict],
) -> tuple[list[dict], dict]:
    """Step 4 — Guru + Shani both touch target house/lord."""
    matched: list[dict] = []
    if not check_double_transit:
        step4 = {
            "name": "Double transit lock (Guru + Shani)",
            "status": "UNAVAILABLE",
            "detail": "swisseph unavailable",
        }
        return [dict(w, transit_confirmed=False) for w in candidates[:3]], step4

    planets = kundli.get("planets") or []
    for w in candidates:
        mid = w["start"] + (w["end"] - w["start"]) / 2
        dt = check_double_transit(
            kundli, mid, lagna_si, planets, cfg.target_houses,
        ) or {}
        row = dict(w)
        row["double_transit"] = dt
        row["transit_confirmed"] = bool(dt.get("active"))
        if row["transit_confirmed"]:
            matched.append(row)
    if not matched:
        matched = [dict(w, transit_confirmed=False) for w in candidates[:3]]
    step4 = {
        "name": "Double transit lock (Guru + Shani)",
        "status": "DONE" if any(w.get("transit_confirmed") for w in matched) else "PARTIAL",
        "matched_count": sum(1 for w in matched if w.get("transit_confirmed")),
        "concern_houses": cfg.target_houses,
        "detail": (
            f"{sum(1 for w in matched if w.get('transit_confirmed'))}/"
            f"{len(matched)} windows with Guru+Shani on target"
        ),
    }
    return matched, step4


def _sun_mars_month_lock(
    target_year: int,
    lagna_si: int,
    target_houses: list[int],
    house_lord: str,
) -> Optional[str]:
    """Step 5 — Sun/Mars transit month trigger in winning year."""
    if not check_double_transit:
        return None
    try:
        import swisseph as swe  # type: ignore
    except Exception:
        return None
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    lord_si = None
    for p in _PLANETS_9:
        if p == house_lord:
            break
    for m_idx in range(1, 13):
        when = datetime(target_year, m_idx, 15)
        for pid, pname, aspects in (
            (0, "Sun", (5, 7, 9)),
            (4, "Mars", (4, 7, 8)),
        ):
            try:
                jd = swe.julday(when.year, when.month, when.day, 12.0)
                lon = float(swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]) % 360
                si = int(lon // 30) % 12
                ph = ((si - lagna_si) % 12) + 1
                for th in target_houses:
                    if ph == th:
                        return f"{months[m_idx - 1]} {target_year}"
            except Exception:
                continue
    return f"{target_year}"


def _step5_final_verdict(
    cfg: UniversalFormulaConfig,
    step0: dict,
    matched: list[dict],
    step1: dict,
    lagna_si: int,
    user_age: Optional[int],
) -> dict:
    """Step 5 — final window + month lock (young users → delayed practical window)."""
    year_floor = _practical_year_floor(user_age, cfg.min_practical_age, step0)
    delayed = bool(step0.get("age_delay_years")) or (
        user_age is not None and user_age < cfg.min_practical_age
    )

    best = _pick_window_from_year_floor(matched, year_floor)
    if not best:
        return {
            "name": "Final verdict + month lock",
            "status": "NONE_FOUND",
            "verdict": "LOW_PROBABILITY",
            "band": "WEAK",
            "primary_window": None,
            "strategy": "Abhi chart se clear timing window nahi mila.",
            "detail": "no qualified dasha+transit window",
        }

    start = best.get("start")
    engine_year = start.year if isinstance(start, datetime) else datetime.utcnow().year + 1
    target_year = max(engine_year, year_floor)

    month_year = _sun_mars_month_lock(
        target_year,
        lagna_si,
        cfg.target_houses,
        str(step1.get("d1_house_lord") or ""),
    )
    lords = "/".join(
        x for x in (best.get("md"), best.get("ad"), best.get("pd")) if x
    )
    transit_confirmed = bool(best.get("transit_confirmed"))
    backup = matched[1] if len(matched) > 1 else None
    backup_pw = None
    if backup and isinstance(backup.get("start"), datetime):
        backup_year = max(backup["start"].year, year_floor)
        backup_pw = _sun_mars_month_lock(
            backup_year,
            lagna_si,
            cfg.target_houses,
            str(step1.get("d1_house_lord") or ""),
        )

    age_at_answer = (
        (user_age + (target_year - datetime.utcnow().year))
        if user_age is not None
        else None
    )
    delay_prefix = ""
    if delayed and step0.get("delay_note"):
        delay_prefix = str(step0.get("delay_note")) + " "

    verdict = "DELAYED_WINDOW" if delayed else "FAVOURABLE_WINDOW"
    return {
        "name": "Final verdict + month lock",
        "status": "DONE",
        "verdict": verdict,
        "band": "MEDIUM",
        "primary_window": month_year,
        "backup_window": backup_pw,
        "delayed_for_age": delayed,
        "practical_year_floor": year_floor,
        "age_at_window": age_at_answer,
        "primary_dasha": {
            "lords": lords,
            "start_iso": best.get("start_iso"),
            "end_iso": best.get("end_iso"),
            "window": best.get("window"),
        },
        "sun_mars_trigger_month": month_year,
        "transit_confirmed": transit_confirmed,
        "strategy": (
            delay_prefix
            + f"Window {month_year} — dasha {lords}"
            + (
                " + Guru/Shani double transit."
                if transit_confirmed
                else "; Guru/Shani double-transit confirmation pending."
            )
            + (f" Agla period: {backup_pw}." if backup_pw else "")
        ).strip(),
        "detail": (
            f"dasha {lords} · "
            + ("DT confirmed" if transit_confirmed else "DT not confirmed")
            + f" · month lock {month_year}"
            + (f" · delayed to ~age {age_at_answer}" if delayed and age_at_answer else "")
        ),
    }


def compute_universal_timing(
    kundli: dict,
    domain: str,
    bucket: str = "general",
    birth: Any = None,
    question: str = "",
    intel: Optional[dict] = None,
) -> dict[str, Any]:
    """Run Universal Timing Formula for any non-marriage domain."""
    intel = intel or {}
    cfg = build_universal_formula_config(domain, bucket)
    try:
        from event_timing._shared.timing_eligibility import min_eligible_age

        cfg.min_practical_age = int(min_eligible_age(domain, question or ""))
    except Exception:
        pass
    factors: list[str] = [f"DOMAIN={domain} BUCKET={bucket}"]

    if not isinstance(kundli, dict) or not kundli.get("planets"):
        return {
            "verdict": "UNKNOWN",
            "band": "WEAK",
            "domain": domain,
            "bucket": bucket,
            "factors": ["GATE missing planets"],
            "engine_arch": _ENGINE_ARCH,
            "engine_version": _ENGINE_VERSION,
        }

    lagna_si = _lagna_si(kundli)
    if lagna_si is None:
        return {
            "verdict": "UNKNOWN",
            "band": "WEAK",
            "domain": domain,
            "bucket": bucket,
            "factors": ["GATE missing lagna"],
            "engine_arch": _ENGINE_ARCH,
            "engine_version": _ENGINE_VERSION,
        }

    now = datetime.utcnow()
    user_age = _extract_user_age(birth, kundli)
    step0 = _step0_age_question_gate(cfg, user_age=user_age, question=question)
    factors.append(f"STEP0 {step0.get('status')} age={user_age}")

    step1 = _step1_target_houses(kundli, lagna_si, cfg)
    ranked, step2 = _step2_significators(kundli, lagna_si, cfg, step1)
    for r in ranked:
        r.setdefault("links", r.get("why") or [])
    factors.append(f"STEP2 top={[r['name'] for r in ranked[:3]]}")

    qualified, step3, primary = _step3_dasha_activation(kundli, ranked, cfg, now)
    factors.append(f"STEP3 windows={len(qualified)}")

    matched, step4 = _step4_double_transit(kundli, lagna_si, cfg, qualified)
    factors.append(f"STEP4 DT matched={step4.get('matched_count')}")

    step5 = _step5_final_verdict(cfg, step0, matched, step1, lagna_si, user_age)
    factors.append(f"STEP5 {step5.get('verdict')} pw={step5.get('primary_window')}")

    verdict = str(step5.get("verdict") or "LOW_PROBABILITY")
    band = str(step5.get("band") or "WEAK")
    primary_window = step5.get("primary_window")

    step_audit = {
        "step0": step0,
        "step1": step1,
        "step2": step2,
        "step3": step3,
        "step4": step4,
        "step5": step5,
    }

    cw = primary if isinstance(primary, dict) else (qualified[0] if qualified else None)

    return {
        "verdict": verdict,
        "band": band,
        "domain": domain,
        "bucket": bucket,
        "user_age": user_age,
        "primary_window": primary_window,
        "backup_window": step5.get("backup_window"),
        "current_window": cw,
        "next_3_windows": matched[:3],
        "top_planets": step2.get("ranked_top") or [],
        "timing_source": step3.get("timing_source"),
        "question_valid": step0.get("question_valid", True),
        "step_audit": step_audit,
        "step_order": list(UNIVERSAL_FORMULA_STEP_ORDER),
        "factors": factors,
        "brand_safety_warnings": cfg.brand_safety,
        "strategy": step5.get("strategy") or "",
        "engine_version": _ENGINE_VERSION,
        "engine_arch": _ENGINE_ARCH,
        "engine_id": f"{domain}_utf_v1",
        "question": question,
    }


def format_universal_timing_for_prompt(result: dict, question: str = "") -> str:
    if not isinstance(result, dict) or not result:
        return ""
    from event_timing.formatters import format_engine_window_block
    return format_engine_window_block(
        result,
        str(result.get("domain") or "TIMING").upper(),
        str(result.get("domain") or ""),
        question=question,
    )

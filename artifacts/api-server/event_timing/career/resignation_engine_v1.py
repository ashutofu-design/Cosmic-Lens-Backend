"""Resignation engine v1 — exit axis (12H/6H/8H) + AD/PD-first dasha.

Question modes:
  viability — "kya resign sahi hai?"
  timing    — "resignation kab dunga?"
  both      — mixed

Timing rule: current AD/PD exit support na ho → next supportive window batao.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Optional

from event_timing.career.bcp_resignation_ages import (
    compute_bcp_resignation_ages,
    format_bcp_resignation_age_list,
)
from event_timing.career.govt_job_engine_v1 import (
    _aspect_houses,
    _dasha_lords,
    _divisional_planets,
    _house_lord,
    _is_strong_dignity,
    _parse_iso,
    _planet_dignity,
    _planet_house,
    _sign_lord,
)

_STRONG_DIGNITY = frozenset({"exalted", "own-sign", "moolatrikona", "own sign", "moola-trikona"})
_KENDRA_TRIKONA = frozenset({1, 4, 5, 7, 9, 10, 11})
_DUSTHANA = frozenset({6, 8, 12})
_AV_SMOOTH_MIN = 28
_EXIT_SCAN_YEARS = 8
_SCORE_PD_EXIT = 9
_SCORE_AD_EXIT = 7
_SCORE_PD_FRICTION = 5
_SCORE_AD_FRICTION = 4
_SCORE_MD_EXIT = 2
_SCORE_CONFLUENCE = 4
_MIN_EXIT_CHUNK = 6

_VIMS_ORDER = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]
_VIMS_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

_TIMING_RE = re.compile(
    r"(?i)\b(kab|when|kitne|timing|notice\s*serve|kab\s*du|kab\s*de|kab\s*dun|"
    r"notice\s*period|kab\s*chhod|exit\s*window)\b",
)
_VIABILITY_RE = re.compile(
    r"(?i)\b(sahi|theek|should|right|chahiye|karna|dena|dena\s*sahi|"
    r"quit|chhodun|chhodu|resign\s*karun|kya\s*resign)\b",
)


def detect_resignation_mode(question: str) -> str:
    q = question or ""
    is_timing = bool(_TIMING_RE.search(q))
    is_viability = bool(_VIABILITY_RE.search(q))
    if is_timing and is_viability:
        return "both"
    if is_timing:
        return "timing"
    if is_viability:
        return "viability"
    return "both"


def run_resignation_bcp_parallel(
    kundli: dict,
    lagna_si: int,
    *,
    user_age: Optional[int] = None,
) -> dict:
    bcp = compute_bcp_resignation_ages(kundli, lagna_si, user_age=user_age)
    d1 = bcp.get("d1_bcp") or {}
    areas: list[dict] = []
    for src in bcp.get("sources") or []:
        kind = str(src.get("source") or "")
        role = "12L" if kind.startswith("12") else "6L"
        typ = "placement" if kind.endswith("_placement") else ("dual_sign" if "dual" in kind else "aspect")
        if typ == "placement":
            areas.append({
                "lord": src.get("lord"), "role": role, "type": typ,
                "house": src.get("house"), "ages": src.get("ages") or [],
            })
        else:
            for entry in src.get("houses") or []:
                areas.append({
                    "lord": src.get("lord"), "role": role, "type": typ,
                    "house": entry.get("house"), "ages": entry.get("ages") or [],
                })
    return {
        "bcp_parallel": True,
        "twelfth_lord": bcp.get("twelfth_lord"),
        "twelfth_lord_house": bcp.get("twelfth_lord_house"),
        "sixth_lord": bcp.get("sixth_lord"),
        "sixth_lord_house": bcp.get("sixth_lord_house"),
        "exit_areas": areas,
        "bcp_resignation_ages": bcp,
        "bcp_age_list": format_bcp_resignation_age_list(d1),
        "all_exit_ages": bcp.get("all_exit_ages") or [],
        "future_priority_ages": bcp.get("future_priority_ages") or [],
        "next_activation_age": bcp.get("next_activation_age"),
    }


def _assess_ashtakvarga_resignation(kundli: dict, lagna_si: int) -> dict:
    out: dict = {"tenth_house_sav": None, "twelfth_house_sav": None, "second_house_sav": None,
                 "smooth_exit": None, "financial_risk": False, "why": []}
    if lagna_si < 0:
        return out
    try:
        from ashtakavarga import compute_ashtakavarga  # type: ignore
        av = compute_ashtakavarga(kundli.get("planets") or [], lagna_si) or {}
    except Exception:
        out["why"].append("Ashtakvarga unavailable")
        return out
    sav = av.get("sav") or av.get("SAV")
    if not isinstance(sav, list):
        return out
    si10 = (lagna_si + 9) % 12
    si12 = (lagna_si + 11) % 12
    si2 = (lagna_si + 1) % 12
    s10, s12, s2 = sav[si10], sav[si12], sav[si2]
    out["tenth_house_sav"], out["twelfth_house_sav"], out["second_house_sav"] = s10, s12, s2
    if isinstance(s12, int):
        if s12 >= _AV_SMOOTH_MIN:
            out["why"].append(f"12H SAV={s12} — smooth exit path")
        else:
            out["why"].append(f"12H SAV={s12} — exit may drag / messy")
    if isinstance(s2, int) and s2 < _AV_SMOOTH_MIN:
        out["financial_risk"] = True
        out["why"].append(f"2H SAV={s2} (<{_AV_SMOOTH_MIN}) — resign without buffer risky")
    if isinstance(s10, int) and s10 < _AV_SMOOTH_MIN:
        out["why"].append(f"10H SAV={s10} — career gap risk after exit")
    out["smooth_exit"] = isinstance(s12, int) and s12 >= _AV_SMOOTH_MIN and not out["financial_risk"]
    return out


def assess_resignation_viability(
    kundli: dict,
    intel: dict,
    *,
    lagna_si: int = -1,
    kp_assist: Optional[dict] = None,
) -> dict:
    planets = kundli.get("planets") or []
    d10 = _divisional_planets(kundli, "D10")
    score = 0
    stay_score = 0
    why: list[str] = []
    flags: list[str] = []
    checklist: dict[str, dict] = {}

    twelfth_lord = _house_lord(intel, 12)
    sixth_lord = _house_lord(intel, 6)
    eighth_lord = _house_lord(intel, 8)
    tenth_lord = _house_lord(intel, 10)
    eleventh_lord = _house_lord(intel, 11)
    second_lord = _house_lord(intel, 2)

    tl12_h = _planet_house(planets, twelfth_lord) if twelfth_lord else None
    sl6_h = _planet_house(planets, sixth_lord) if sixth_lord else None
    el8_h = _planet_house(planets, eighth_lord) if eighth_lord else None
    tl10_h = _planet_house(planets, tenth_lord) if tenth_lord else None
    el11_h = _planet_house(planets, eleventh_lord) if eleventh_lord else None
    sl2_h = _planet_house(planets, second_lord) if second_lord else None

    # Step 1 — 12H exit
    s1: list[str] = []
    if tl12_h in _KENDRA_TRIKONA:
        score += 14
        s1.append(f"12L {twelfth_lord} in {tl12_h}H — exit channel open (+14)")
        flags.append("12l_supportive_house")
    elif tl12_h == 12:
        score += 16
        s1.append(f"12L in 12H — strong vyaya/exit signature (+16)")
    checklist["step1_12th_house"] = {"twelfth_lord": twelfth_lord, "house": tl12_h, "why": s1}
    why.extend(s1)

    # Step 2 — 6H friction
    s2: list[str] = []
    sl6_dgn = _planet_dignity(intel, sixth_lord) if sixth_lord else None
    if sl6_dgn in ("debilitated", "enemy-sign"):
        score += 12
        s2.append(f"6L {sixth_lord} {sl6_dgn} — current job dharma fading (+12)")
        flags.append("6l_afflicted")
    elif sl6_h in {6, 8, 12}:
        score += 8
        s2.append(f"6L in {sl6_h}H — service stress high (+8)")
    checklist["step2_6th_house"] = {"sixth_lord": sixth_lord, "house": sl6_h, "why": s2}
    why.extend(s2)

    # Step 3 — 8H break
    s3: list[str] = []
    if el8_h and eighth_lord:
        el8_dgn = _planet_dignity(intel, eighth_lord)
        if el8_h in {8, 12} or el8_dgn in ("debilitated", "enemy-sign"):
            score += 8
            s3.append(f"8L {eighth_lord} in {el8_h}H — sudden break energy (+8)")
            flags.append("8l_break_energy")
    checklist["step3_8th_house"] = {"eighth_lord": eighth_lord, "house": el8_h, "why": s3}
    why.extend(s3)

    # Step 4 — 2H / 10H / 11H post-exit
    s4: list[str] = []
    sl2_dgn = _planet_dignity(intel, second_lord) if second_lord else None
    if sl2_dgn in ("exalted", "own-sign", "moolatrikona") and sl2_h in _KENDRA_TRIKONA:
        stay_score += 14
        s4.append(f"2L {second_lord} strong — financial buffer OK, rush exit avoid (+stay)")
    elif sl2_dgn in ("debilitated", "enemy-sign"):
        score -= 6
        s4.append(f"2L weak — resign without savings risky (-6 exit score)")
        flags.append("2l_weak")

    if tl10_h == 10 and _is_strong_dignity(_planet_dignity(intel, tenth_lord)):
        stay_score += 12
        s4.append("10L strong in 10H — career still climbing, stay lean (+stay)")
    elif tl10_h in {10, 11}:
        score += 6
        s4.append("10L linked to gains axis — exit can upgrade role (+6)")

    if el11_h == 11:
        score += 8
        s4.append("11L in 11H — next gains possible after exit (+8)")

    checklist["step4_post_exit"] = {
        "second_lord": second_lord, "tenth_lord": tenth_lord, "eleventh_lord": eleventh_lord, "why": s4,
    }
    why.extend(s4)

    # Step 5 — Sun / Saturn / Mars
    s5: list[str] = []
    sun_h = _planet_house(planets, "Sun")
    sat_h = _planet_house(planets, "Saturn")
    mars_h = _planet_house(planets, "Mars")
    if sun_h in {6, 10} and _is_strong_dignity(_planet_dignity(intel, "Sun")):
        score += 6
        s5.append(f"Sun in {sun_h}H — authority clash driver (+6)")
    if sat_h in {6, 8, 12}:
        score += 8
        s5.append(f"Saturn in {sat_h}H — burden/patience exhausted (+8)")
    if mars_h in {6, 8, 12}:
        score += 5
        s5.append(f"Mars in {mars_h}H — impulsive exit risk (+5)")
        flags.append("mars_impulse_risk")
    checklist["step5_drivers"] = {"why": s5}
    why.extend(s5)

    # Step 6 — D10
    s6: list[str] = []
    if d10 and twelfth_lord:
        tl12_d10 = _planet_house(d10, twelfth_lord)
        if tl12_d10 in {12, 8, 6}:
            score += 10
            s6.append(f"D10: 12L in {tl12_d10}H — dashamsha confirms exit (+10)")
        elif tl12_d10 in {10, 11}:
            stay_score += 8
            s6.append("D10: 12L in 10/11 — professional rise, don't rush exit (+stay)")
    checklist["step6_d10"] = {"why": s6}
    why.extend(s6)

    if isinstance(kp_assist, dict) and kp_assist.get("score"):
        kp_sc = int(kp_assist.get("score") or 0)
        score += kp_sc
        why.extend((kp_assist.get("why") or [])[:2])

    av = _assess_ashtakvarga_resignation(kundli, lagna_si)
    checklist["step9_ashtakvarga"] = av
    if av.get("financial_risk"):
        score -= 8
        stay_score += 10
        flags.append("av_2h_risk")
    elif av.get("smooth_exit"):
        score += 5
    why.extend((av.get("why") or [])[:2])

    exit_score = max(0, min(100, score))
    net = exit_score - stay_score

    if net >= 35 and not av.get("financial_risk"):
        viability = "window_favourable"
    elif net >= 18:
        viability = "plan_exit_3_6mo"
    elif net >= 5:
        viability = "wait_for_window"
    elif av.get("financial_risk"):
        viability = "stay_financial_risk"
    else:
        viability = "stay_hold"

    return {
        "fired": True,
        "engine": "resignation_engine_v1",
        "exit_score": exit_score,
        "stay_score": stay_score,
        "viability": viability,
        "why": why,
        "flags": flags,
        "checklist": checklist,
        "twelfth_lord": twelfth_lord,
        "sixth_lord": sixth_lord,
        "eighth_lord": eighth_lord,
        "tenth_lord": tenth_lord,
        "eleventh_lord": eleventh_lord,
        "ashtakvarga_gate": av,
        "kp_summary": (kp_assist or {}).get("summary") if isinstance(kp_assist, dict) else None,
    }


def _exit_core_set(viability: dict) -> set[str]:
    core: set[str] = set()
    for key in ("twelfth_lord", "sixth_lord", "eighth_lord"):
        v = viability.get(key)
        if v:
            core.add(str(v))
    return core


def _fmt_dasha_date(dt: Optional[datetime]) -> Optional[str]:
    return dt.strftime("%Y-%m") if isinstance(dt, datetime) else None


def _flatten_exit_dasha_chain(kundli: dict) -> list[dict]:
    out: list[dict] = []
    today = datetime.utcnow()
    horizon = today + timedelta(days=365 * _EXIT_SCAN_YEARS)
    for md_row in kundli.get("dashas") or []:
        if not isinstance(md_row, dict):
            continue
        md = str(md_row.get("planet") or md_row.get("lord") or md_row.get("mahadasha") or "").strip()
        for ad_row in (md_row.get("subDashas") or md_row.get("antardashas") or []):
            if not isinstance(ad_row, dict):
                continue
            ad = str(ad_row.get("planet") or ad_row.get("lord") or ad_row.get("antardasha") or "").strip()
            ad_start = _parse_iso(ad_row.get("startDate") or ad_row.get("start"))
            ad_end = _parse_iso(ad_row.get("endDate") or ad_row.get("end"))
            if not (ad and ad_start and ad_end) or ad_end < today - timedelta(days=30) or ad_start > horizon:
                continue
            pd_list = ad_row.get("subDashas") or ad_row.get("pratyantar_dashas") or []
            if pd_list and isinstance(pd_list, list):
                for pd_row in pd_list:
                    if not isinstance(pd_row, dict):
                        continue
                    pd = str(pd_row.get("planet") or pd_row.get("lord") or pd_row.get("pratyantardasha") or pd_row.get("pratyantar") or "").strip()
                    pd_start = _parse_iso(pd_row.get("startDate") or pd_row.get("start"))
                    pd_end = _parse_iso(pd_row.get("endDate") or pd_row.get("end"))
                    if pd and pd_start and pd_end and pd_end >= today - timedelta(days=30):
                        out.append({"md": md, "ad": ad, "pd": pd, "start": pd_start, "end": pd_end})
            elif ad in _VIMS_ORDER:
                ad_secs = (ad_end - ad_start).total_seconds()
                if ad_secs <= 0:
                    continue
                total = float(sum(_VIMS_YEARS.values()))
                cursor = ad_start
                for k in range(9):
                    pd = _VIMS_ORDER[( _VIMS_ORDER.index(ad) + k) % 9]
                    pd_end = cursor + timedelta(seconds=ad_secs * (_VIMS_YEARS[pd] / total))
                    if pd_end >= today - timedelta(days=30):
                        out.append({"md": md, "ad": ad, "pd": pd, "start": cursor, "end": pd_end})
                    cursor = pd_end
    out.sort(key=lambda c: c["start"])
    return out


def _score_exit_chunk(md: str, ad: str, pd: str, exit_core: set[str]) -> tuple[int, list[str], bool]:
    score = 0
    detail: list[str] = []
    ad, pd, md = ad or "", pd or "", md or ""

    if pd in exit_core:
        score += _SCORE_PD_EXIT
        detail.append(f"PD {pd} (12L/8L/6L exit) +{_SCORE_PD_EXIT}")
    if ad in exit_core:
        score += _SCORE_AD_EXIT
        detail.append(f"AD {ad} (exit lord) +{_SCORE_AD_EXIT}")
    if ad in exit_core and pd in exit_core:
        score += _SCORE_CONFLUENCE
        detail.append(f"AD+PD exit confluence +{_SCORE_CONFLUENCE}")
    if md in exit_core:
        score += _SCORE_MD_EXIT
        detail.append(f"MD {md} (background) +{_SCORE_MD_EXIT}")

    hit = (ad in exit_core) or (pd in exit_core)
    return score, detail, hit


def assess_resignation_timing(
    kundli: dict,
    viability: dict,
    *,
    bcp: Optional[dict] = None,
    mode: str = "both",
) -> dict:
    """Step 7 — AD/PD exit lords; skip current if unsupported."""
    viab = str(viability.get("viability") or "stay_hold")
    if viab == "stay_financial_risk" and mode == "viability":
        return {
            "status": "deferred_financial_risk",
            "message": "2H weak — pehle buffer banao; exit timing secondary.",
            "windows": [],
            "step7_dasha": {"status": "deferred"},
        }

    exit_core = _exit_core_set(viability)
    md, ad, pd = _dasha_lords(kundli)
    current_lords = "/".join(x for x in (md, ad, pd) if x)
    today = datetime.utcnow()

    cur_score, cur_detail, cur_hit = _score_exit_chunk(md, ad, pd, exit_core)
    current_supports = cur_hit and cur_score >= _MIN_EXIT_CHUNK

    ranked: list[dict] = []
    for chunk in _flatten_exit_dasha_chain(kundli):
        sc, det, hit = _score_exit_chunk(
            chunk.get("md", ""), chunk.get("ad", ""), chunk.get("pd", ""), exit_core,
        )
        if not hit or sc < _MIN_EXIT_CHUNK:
            continue
        ranked.append({
            **chunk,
            "score": sc,
            "detail": det,
            "lords": "/".join(x for x in (chunk.get("md"), chunk.get("ad"), chunk.get("pd")) if x),
            "start_label": _fmt_dasha_date(chunk["start"]),
            "end_label": _fmt_dasha_date(chunk["end"]),
        })
    ranked.sort(key=lambda w: (-w["score"], w["start"]))

    recommended: Optional[dict] = None
    timing_source = "none"
    skip_reason = ""

    if current_supports:
        for w in ranked:
            if w["start"] <= today <= w["end"]:
                recommended = w
                timing_source = "current_dasha"
                break
        if recommended is None:
            recommended = {
                "md": md, "ad": ad, "pd": pd,
                "score": cur_score, "detail": cur_detail, "lords": current_lords,
                "start_label": "current", "end_label": "current",
            }
            timing_source = "current_dasha"
    else:
        skip_reason = (
            f"Current dasha {current_lords} exit ko AD/PD level par support nahi karti "
            f"(score {cur_score})."
        )
        for w in ranked:
            if w["end"] < today:
                continue
            recommended = w
            timing_source = "next_dasha"
            break

    directive = ""
    if timing_source == "current_dasha" and recommended:
        directive = (
            f"CURRENT exit window — focus AD/PD {recommended.get('ad')}/{recommended.get('pd')} "
            f"({recommended.get('start_label')}→{recommended.get('end_label')})."
        )
    elif timing_source == "next_dasha" and recommended:
        directive = (
            f"Abhi resign mat bolo — NEXT exit window: {recommended.get('lords')} "
            f"({recommended.get('start_label')}→{recommended.get('end_label')})."
        )
    elif skip_reason:
        directive = skip_reason + " Strong future exit AD/PD abhi scan mein nahi mili."

    windows_out = [{
        "md": w.get("md"), "ad": w.get("ad"), "pd": w.get("pd"),
        "lords": w.get("lords"), "start": w.get("start_label"), "end": w.get("end_label"),
        "score": w.get("score"), "reason": " · ".join(w.get("detail") or []),
    } for w in ranked[:5]]

    return {
        "status": "ready" if recommended else "no_window_found",
        "current_lords": current_lords,
        "current_supports_exit": current_supports,
        "timing_source": timing_source,
        "recommended_window": {
            "lords": recommended.get("lords"),
            "md": recommended.get("md"),
            "ad": recommended.get("ad"),
            "pd": recommended.get("pd"),
            "start": recommended.get("start_label"),
            "end": recommended.get("end_label"),
            "score": recommended.get("score"),
            "reason": " · ".join(recommended.get("detail") or []),
            "timing_source": timing_source,
        } if recommended else None,
        "windows": windows_out,
        "exit_core_lords": sorted(exit_core),
        "bcp_next_ages": list((bcp or {}).get("future_priority_ages") or [])[:6],
        "step7_dasha": {
            "current_lords": current_lords,
            "current_supports_exit": current_supports,
            "ad_pd_priority": True,
            "skip_current_reason": skip_reason or None,
            "timing_source": timing_source,
            "recommended_window": recommended,
        },
        "llm_directive": directive,
    }


def assess_resignation(
    kundli: dict,
    intel: dict,
    *,
    question: str = "",
    lagna_si: int = -1,
    kp: Optional[dict] = None,
    kp_assist_fn: Any = None,
    user_age: Optional[int] = None,
) -> dict:
    mode = detect_resignation_mode(question)
    kp_assist = None
    if callable(kp_assist_fn) and kp:
        try:
            kp_assist = kp_assist_fn(kp)
        except Exception:
            pass

    bcp_block = run_resignation_bcp_parallel(kundli, lagna_si, user_age=user_age) if lagna_si >= 0 else {}
    viability = assess_resignation_viability(
        kundli, intel, lagna_si=lagna_si, kp_assist=kp_assist,
    )
    timing = assess_resignation_timing(
        kundli, viability,
        bcp=bcp_block.get("bcp_resignation_ages") if bcp_block else None,
        mode=mode,
    )

    return {
        "question_mode": mode,
        "bcp_parallel": bcp_block,
        "viability": viability,
        "timing": timing,
        "checklist": viability.get("checklist") or {},
        "resignation_viability": viability.get("viability"),
        "verdict_label": _verdict_label(viability, timing, mode),
        "strategy": _strategy(viability, timing, mode, bcp_block),
    }


def _verdict_label(viability: dict, timing: dict, mode: str) -> str:
    v = viability.get("viability")
    if v == "stay_financial_risk":
        return "RESIGN_STAY_BUFFER_FIRST"
    if v == "stay_hold":
        return "RESIGN_STAY_HOLD"
    if timing.get("current_supports_exit"):
        return "RESIGN_WINDOW_OPEN_NOW"
    if timing.get("timing_source") == "next_dasha":
        return "RESIGN_NEXT_WINDOW"
    if v == "plan_exit_3_6mo":
        return "RESIGN_PLAN_3_6MO"
    return "RESIGN_WAIT"


def _strategy(viability: dict, timing: dict, mode: str, bcp: dict) -> str:
    parts: list[str] = []
    v = viability.get("viability")
    if v == "stay_financial_risk":
        parts.append("Abhi resign risky — 60-90 din ka financial buffer pehle banao.")
    elif v == "stay_hold":
        parts.append("Chart abhi strong stay signal de raha hai — impulsive exit avoid karein.")
    elif v == "plan_exit_3_6mo":
        parts.append("Exit plan 3-6 mahine mein — next role secure karo, phir notice.")
    elif v == "window_favourable":
        parts.append("Exit window favourable — par offer/buffer + clean handover zaroori.")

    if mode in ("timing", "both") and timing.get("llm_directive"):
        parts.append(timing["llm_directive"])
    elif mode == "viability" and not timing.get("current_supports_exit"):
        parts.append("Dasha abhi exit support nahi karti — timing question par next window dekho.")

    nxt = bcp.get("next_activation_age")
    if nxt:
        parts.append(f"(BCP background exit age {nxt}.)")
    return " ".join(parts) if parts else "Mixed signals — plan dono taraf se."


def format_resignation_block_for_prompt(result: dict, question: str = "") -> str:
    if not isinstance(result, dict):
        return ""
    viab = result.get("viability") if isinstance(result.get("viability"), dict) else {}
    timing = result.get("timing") if isinstance(result.get("timing"), dict) else {}
    bcp = result.get("bcp_parallel") or {}
    checklist = viab.get("checklist") or {}
    mode = result.get("question_mode") or "both"

    lines = [
        "=== RESIGNATION ENGINE v1 (LOCKED) ===",
        f"Question mode: {mode}",
        f"Viability: {viab.get('viability')} (exit {viab.get('exit_score')} vs stay {viab.get('stay_score')})",
        f"Verdict: {result.get('verdict_label') or _verdict_label(viab, timing, mode)}",
        "",
        "▸ CLASSICAL EXIT CHECKLIST:",
    ]
    for key, label in (
        ("step1_12th_house", "Step1 — 12H exit"),
        ("step2_6th_house", "Step2 — 6H friction"),
        ("step3_8th_house", "Step3 — 8H break"),
        ("step4_post_exit", "Step4 — 2H/10H/11H post-exit"),
        ("step5_drivers", "Step5 — Sun/Saturn/Mars"),
        ("step6_d10", "Step6 — D10 verify"),
    ):
        block = checklist.get(key) or {}
        for w in (block.get("why") or [])[:2]:
            lines.append(f"  {label}: {w}")

    av = checklist.get("step9_ashtakvarga") or viab.get("ashtakvarga_gate") or {}
    lines.append("  Step9 — Ashtakvarga:")
    for w in (av.get("why") or [])[:2]:
        lines.append(f"    {w}")

    if mode in ("timing", "both"):
        s7 = timing.get("step7_dasha") or {}
        lines.append("  Step7 — Dasha (AD/PD exit lords priority):")
        lines.append(f"    Current: {s7.get('current_lords') or timing.get('current_lords')}")
        lines.append(f"    Current supports exit: {timing.get('current_supports_exit')}")
        rec = timing.get("recommended_window")
        if rec:
            lines.append(
                f"    EXIT WINDOW ({rec.get('timing_source', timing.get('timing_source'))}): "
                f"{rec.get('lords')} {rec.get('start')}→{rec.get('end')}"
            )
        if s7.get("skip_current_reason"):
            lines.append(f"    ⚠ {s7['skip_current_reason']}")

    if bcp:
        lines.append("")
        lines.append("▸ BCP parallel (12L+6L — background only):")
        lines.append(f"  12L@{bcp.get('twelfth_lord_house')}H · 6L@{bcp.get('sixth_lord_house')}H")

    lines.append("")
    if timing.get("llm_directive"):
        lines.append(f"▸ TIMING DIRECTIVE: {timing['llm_directive']}")
    lines.append(f"Strategy: {result.get('strategy') or _strategy(viab, timing, mode, bcp)}")
    lines.append("GUARD: NEVER say 'pakka resign karo' — buffer + offer + clean exit mandatory.")
    lines.append("RULE: Current dasha exit support NAHI → sirf NEXT AD/PD window batao.")
    return "\n".join(lines)

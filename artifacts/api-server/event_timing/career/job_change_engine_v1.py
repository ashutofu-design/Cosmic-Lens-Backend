"""Job-change engine v1 — 3L/5L/9L change + 6L/10L/11L outcome + 5L+10L BCP."""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Optional

from event_timing.career.bcp_5l_10l_ages import compute_bcp_5l_10l_ages
from event_timing.career.govt_job_engine_v1 import (
    _dasha_lords, _house_lord, _parse_iso, _planet_house,
)

_CHANGE_H = frozenset({3, 5, 9, 10, 11})
_SCORE_PD_CHG, _SCORE_AD_CHG = 6, 5
_SCORE_PD_OUT, _SCORE_AD_OUT = 2, 3
_SCORE_CONFL = 2
_MIN_CHUNK = 5
_SCAN_YEARS = 12
_VIMS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
_VY = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
_TIMING_RE = re.compile(r"(?i)\b(kab|when|kitne|timing|switch\s*kab|change\s*kab)\b")


def detect_job_change_mode(q: str) -> str:
    return "timing" if _TIMING_RE.search(q or "") else "general"


def _lord_sets(intel: dict, karakas_d: dict) -> dict:
    third, fifth, ninth = _house_lord(intel, 3), _house_lord(intel, 5), _house_lord(intel, 9)
    sixth, tenth, eleventh = _house_lord(intel, 6), _house_lord(intel, 10), _house_lord(intel, 11)
    change = {x for x in (third, fifth, ninth) if x}
    outcome = {x for x in (sixth, tenth, eleventh) if x}
    return {"change": change, "outcome": outcome, "third_lord": third, "fifth_lord": fifth, "ninth_lord": ninth,
            "tenth_lord": tenth}


def run_job_change_bcp_parallel(kundli: dict, lagna_si: int, *, user_age: Optional[int] = None) -> dict:
    bcp = compute_bcp_5l_10l_ages(kundli, lagna_si, user_age=user_age)
    return {
        "bcp_parallel": True, "fifth_lord": bcp["fifth_lord"], "fifth_lord_house": bcp["fifth_lord_house"],
        "tenth_lord": bcp["tenth_lord"], "tenth_lord_house": bcp["tenth_lord_house"],
        "aspect_houses_5l": bcp.get("aspect_houses_5l"), "aspect_houses_10l": bcp.get("aspect_houses_10l"),
        "all_change_ages": bcp.get("all_ages") or [], "future_priority_ages": bcp.get("future_priority_ages") or [],
        "next_activation_age": bcp.get("next_activation_age"),
    }


def assess_job_change_promise(kundli: dict, intel: dict, *, kp_assist: Optional[dict] = None) -> dict:
    planets = kundli.get("planets") or []
    ls = _lord_sets(intel, {})
    score, why, checklist = 0, [], {}
    for step, lord, label in (
        ("step1_3h", ls["third_lord"], "3H courage"),
        ("step2_5h", ls["fifth_lord"], "5H change"),
        ("step3_9h", ls["ninth_lord"], "9H direction"),
    ):
        h = _planet_house(planets, lord) if lord else None
        s = []
        if h in _CHANGE_H:
            score += 10
            s.append(f"{label}: {lord} in {h}H (+10)")
        checklist[step] = {"lord": lord, "house": h, "why": s}
        why.extend(s)
    tl10 = _planet_house(planets, ls["tenth_lord"]) if ls["tenth_lord"] else None
    if tl10 in {10, 11}:
        score += 8
        why.append(f"10L in {tl10}H — outcome axis ready (+8)")
    if isinstance(kp_assist, dict):
        score += int(kp_assist.get("score") or 0)
        why.extend((kp_assist.get("why") or [])[:2])
    level = "high" if score >= 28 else "moderate" if score >= 14 else "low"
    return {"fired": True, "engine": "job_change_engine_v1", "change_promise_level": level,
            "score": score, "why": why, "checklist": checklist, **ls}


def _flatten(kundli: dict) -> list[dict]:
    out, today = [], datetime.utcnow()
    horizon = today + timedelta(days=365 * _SCAN_YEARS)
    for md_row in kundli.get("dashas") or []:
        if not isinstance(md_row, dict):
            continue
        md = str(md_row.get("planet") or md_row.get("lord") or "").strip()
        for ad_row in (md_row.get("subDashas") or md_row.get("antardashas") or []):
            if not isinstance(ad_row, dict):
                continue
            ad = str(ad_row.get("planet") or ad_row.get("lord") or "").strip()
            ad_start = _parse_iso(ad_row.get("startDate") or ad_row.get("start"))
            ad_end = _parse_iso(ad_row.get("endDate") or ad_row.get("end"))
            if not (ad and ad_start and ad_end) or ad_end < today - timedelta(days=30) or ad_start > horizon:
                continue
            for pd_row in (ad_row.get("subDashas") or ad_row.get("pratyantar_dashas") or []):
                if not isinstance(pd_row, dict):
                    continue
                pd = str(pd_row.get("planet") or pd_row.get("lord") or "").strip()
                pd_start = _parse_iso(pd_row.get("startDate") or pd_row.get("start"))
                pd_end = _parse_iso(pd_row.get("endDate") or pd_row.get("end"))
                if pd and pd_start and pd_end and pd_end >= today - timedelta(days=30):
                    out.append({"md": md, "ad": ad, "pd": pd, "start": pd_start, "end": pd_end})
    out.sort(key=lambda c: c["start"])
    return out


def _score_chunk(ad: str, pd: str, change: set, outcome: set) -> tuple[int, list[str], bool]:
    sc, det = 0, []
    if ad in change:
        sc += _SCORE_AD_CHG; det.append(f"AD {ad} change +{_SCORE_AD_CHG}")
    elif ad in outcome:
        sc += _SCORE_AD_OUT; det.append(f"AD {ad} outcome +{_SCORE_AD_OUT}")
    if pd in change:
        sc += _SCORE_PD_CHG; det.append(f"PD {pd} change +{_SCORE_PD_CHG}")
    elif pd in outcome:
        sc += _SCORE_PD_OUT; det.append(f"PD {pd} outcome +{_SCORE_PD_OUT}")
    if ad in change and pd in change:
        sc += _SCORE_CONFL; det.append(f"AD+PD confluence +{_SCORE_CONFL}")
    hit = (ad in change) or (pd in change)
    if hit and sc < _MIN_CHUNK:
        return 0, [], False
    return sc, det, hit


def assess_job_change_timing(kundli: dict, promise: dict) -> dict:
    change, outcome = promise["change"], promise["outcome"]
    md, ad, pd = _dasha_lords(kundli)
    today = datetime.utcnow()
    cur_sc, cur_det, cur_hit = _score_chunk(ad, pd, change, outcome)
    current_supports = cur_hit and cur_sc >= _MIN_CHUNK
    ranked = []
    for c in _flatten(kundli):
        sc, det, hit = _score_chunk(c["ad"], c["pd"], change, outcome)
        if not hit:
            continue
        ranked.append({**c, "score": sc, "detail": det,
                       "lords": "/".join(x for x in (c["md"], c["ad"], c["pd"]) if x),
                       "start_label": c["start"].strftime("%Y-%m"), "end_label": c["end"].strftime("%Y-%m")})
    ranked.sort(key=lambda w: (-w["score"], w["start"]))
    rec, src, skip = None, "none", ""
    if current_supports:
        for w in ranked:
            if w["start"] <= today <= w["end"]:
                rec, src = w, "current_dasha"; break
        if not rec:
            rec = {"lords": f"{md}/{ad}/{pd}", "ad": ad, "pd": pd, "score": cur_sc, "detail": cur_det,
                   "start_label": "current", "end_label": "current", "timing_source": "current_dasha"}
            src = "current_dasha"
    else:
        skip = f"Current {md}/{ad}/{pd} change lords weak (score {cur_sc})."
        for w in ranked:
            if w["end"] >= today:
                rec, src = w, "next_dasha"; break
    directive = ""
    if src == "current_dasha" and rec:
        directive = f"CURRENT switch window — AD/PD {rec.get('ad')}/{rec.get('pd')}."
    elif src == "next_dasha" and rec:
        directive = f"NEXT switch window: {rec.get('lords')} ({rec.get('start_label')}→{rec.get('end_label')})."
    elif skip:
        directive = skip
    return {"current_supports_change": current_supports, "timing_source": src,
            "recommended_window": rec, "llm_directive": directive}


def assess_job_change(kundli: dict, intel: dict, *, question: str = "", lagna_si: int = -1,
                      kp: Optional[dict] = None, kp_assist_fn: Any = None,
                      user_age: Optional[int] = None) -> dict:
    kp_a = kp_assist_fn(kp) if callable(kp_assist_fn) and kp else None
    bcp = run_job_change_bcp_parallel(kundli, lagna_si, user_age=user_age) if lagna_si >= 0 else {}
    promise = assess_job_change_promise(kundli, intel, kp_assist=kp_a)
    timing = assess_job_change_timing(kundli, promise)
    mode = detect_job_change_mode(question)
    return {"question_mode": mode, "bcp_parallel": bcp, "promise": promise, "timing": timing,
            "change_promise_level": promise.get("change_promise_level"),
            "verdict_label": "JOB_CHANGE_WINDOW_OPEN" if timing.get("current_supports_change") else "JOB_CHANGE_NEXT",
            "strategy": (timing.get("llm_directive") or "") + " Parallel apply + notice plan ready rakho."}


def format_job_change_block_for_prompt(result: dict, question: str = "") -> str:
    p, t = result.get("promise") or {}, result.get("timing") or {}
    lines = ["=== JOB-CHANGE ENGINE v1 (LOCKED) ===", f"Promise: {p.get('change_promise_level')} · Mode: {result.get('question_mode')}"]
    for w in (p.get("why") or [])[:4]:
        lines.append(f"  • {w}")
    if t.get("llm_directive"):
        lines.append(f"▸ TIMING: {t['llm_directive']}")
    lines.append("▸ BCP 5L+10L background only. GUARD: no guaranteed offer.")
    return "\n".join(lines)

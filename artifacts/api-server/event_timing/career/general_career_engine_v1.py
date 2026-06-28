"""General career / job-timing engine v1 — 10L+6L BCP + 10H/6H promise."""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Optional

from event_timing.career.bcp_career_ages import compute_bcp_career_ages
from event_timing.career.govt_job_engine_v1 import (
    _dasha_lords, _house_lord, _is_strong_dignity, _parse_iso, _planet_dignity, _planet_house,
)

_PROMISE_H = frozenset({2, 6, 10, 11})
_SCORE_PD, _SCORE_AD, _SCORE_MD = 9, 7, 2
_MIN = 6
_SCAN = 8
_TIMING_RE = re.compile(r"(?i)\b(kab|when|kitne|timing|naukri\s*kab|job\s*kab|milegi|milega)\b")


def detect_general_career_mode(q: str) -> str:
    return "timing" if _TIMING_RE.search(q or "") else "general"


def run_general_career_bcp_parallel(kundli: dict, lagna_si: int, *, user_age: Optional[int] = None) -> dict:
    bcp = compute_bcp_career_ages(kundli, lagna_si, user_age=user_age)
    return {
        "bcp_parallel": True, "tenth_lord": bcp.get("tenth_lord"), "tenth_lord_house": bcp.get("tenth_lord_house"),
        "sixth_lord": bcp.get("sixth_lord"), "sixth_lord_house": bcp.get("sixth_lord_house"),
        "aspect_houses_10l": bcp.get("aspect_houses_10l"), "aspect_houses_6l": bcp.get("aspect_houses_6l"),
        "all_job_ages": bcp.get("all_job_ages") or [], "future_priority_ages": bcp.get("future_priority_ages") or [],
        "next_activation_age": bcp.get("next_activation_age"),
    }


def assess_general_career_promise(kundli: dict, intel: dict, *, karakas_d: Optional[dict] = None,
                                  kp_assist: Optional[dict] = None) -> dict:
    planets = kundli.get("planets") or []
    tenth_lord, sixth_lord = _house_lord(intel, 10), _house_lord(intel, 6)
    eleventh_lord = _house_lord(intel, 11)
    score, why = 0, []
    for lord, label in ((tenth_lord, "10L"), (sixth_lord, "6L")):
        h = _planet_house(planets, lord) if lord else None
        dgn = _planet_dignity(intel, lord) if lord else None
        if h in _PROMISE_H:
            score += 12
            why.append(f"{label} {lord} in {h}H (+12)")
        if _is_strong_dignity(dgn):
            score += 6
            why.append(f"{label} {lord} strong dignity (+6)")
    if isinstance(kp_assist, dict):
        score += int(kp_assist.get("score") or 0)
        why.extend((kp_assist.get("why") or [])[:2])
    level = "high" if score >= 30 else "moderate" if score >= 16 else "low"
    core = {x for x in (tenth_lord, sixth_lord, eleventh_lord, (karakas_d or {}).get("AmK")) if x}
    return {"fired": True, "engine": "general_career_engine_v1", "job_promise_level": level,
            "score": score, "why": why, "tenth_lord": tenth_lord, "sixth_lord": sixth_lord,
            "career_core": sorted(core)}


def _flatten(kundli: dict) -> list[dict]:
    out, today = [], datetime.utcnow()
    horizon = today + timedelta(days=365 * _SCAN)
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
                pd_end = _parse_iso(pd_row.get("endDate") or pd_row.get("end"))
                pd_start = _parse_iso(pd_row.get("startDate") or pd_row.get("start"))
                if pd and pd_start and pd_end and pd_end >= today - timedelta(days=30):
                    out.append({"md": md, "ad": ad, "pd": pd, "start": pd_start, "end": pd_end})
    out.sort(key=lambda c: c["start"])
    return out


def _score(ad: str, pd: str, core: set) -> tuple[int, bool]:
    sc = 0
    if pd in core:
        sc += _SCORE_PD
    if ad in core:
        sc += _SCORE_AD
    if ad in core and pd in core:
        sc += 3
    return sc, (ad in core) or (pd in core)


def assess_general_career_timing(kundli: dict, promise: dict) -> dict:
    core = set(promise.get("career_core") or [])
    md, ad, pd = _dasha_lords(kundli)
    today = datetime.utcnow()
    cur_sc, cur_hit = _score(ad, pd, core)
    current_supports = cur_hit and cur_sc >= _MIN
    ranked = []
    for c in _flatten(kundli):
        sc, hit = _score(c["ad"], c["pd"], core)
        if not hit or sc < _MIN:
            continue
        ranked.append({**c, "score": sc, "lords": "/".join(x for x in (c["md"], c["ad"], c["pd"]) if x),
                       "start_label": c["start"].strftime("%Y-%m"), "end_label": c["end"].strftime("%Y-%m")})
    ranked.sort(key=lambda w: (-w["score"], w["start"]))
    rec, src = None, "none"
    if current_supports:
        for w in ranked:
            if w["start"] <= today <= w["end"]:
                rec, src = w, "current_dasha"; break
        if not rec:
            rec = {"lords": f"{md}/{ad}/{pd}", "start_label": "current", "end_label": "current"}
            src = "current_dasha"
    else:
        for w in ranked:
            if w["end"] >= today:
                rec, src = w, "next_dasha"; break
    directive = ""
    if src == "current_dasha":
        directive = f"CURRENT job window — AD/PD {ad}/{pd} active."
    elif src == "next_dasha" and rec:
        directive = f"NEXT job window: {rec.get('lords')} ({rec.get('start_label')}→{rec.get('end_label')})."
    else:
        directive = "Current dasha weak — next 10L/6L AD/PD scan karo."
    return {"current_supports_job": current_supports, "timing_source": src,
            "recommended_window": rec, "llm_directive": directive}


def assess_general_career(kundli: dict, intel: dict, *, question: str = "", lagna_si: int = -1,
                          karakas_d: Optional[dict] = None, kp: Optional[dict] = None,
                          kp_assist_fn: Any = None, user_age: Optional[int] = None) -> dict:
    kp_a = kp_assist_fn(kp) if callable(kp_assist_fn) and kp else None
    bcp = run_general_career_bcp_parallel(kundli, lagna_si, user_age=user_age) if lagna_si >= 0 else {}
    promise = assess_general_career_promise(kundli, intel, karakas_d=karakas_d, kp_assist=kp_a)
    timing = assess_general_career_timing(kundli, promise)
    return {"question_mode": detect_general_career_mode(question), "bcp_parallel": bcp,
            "promise": promise, "timing": timing, "job_promise_level": promise.get("job_promise_level"),
            "verdict_label": "JOB_WINDOW_OPEN" if timing.get("current_supports_job") else "JOB_NEXT_WINDOW",
            "strategy": timing.get("llm_directive") or "Prepare + apply in supportive dasha."}


def format_general_career_block_for_prompt(result: dict, question: str = "") -> str:
    p, t = result.get("promise") or {}, result.get("timing") or {}
    lines = ["=== GENERAL CAREER / JOB TIMING ENGINE v1 (LOCKED) ===",
             f"Job promise: {p.get('job_promise_level')} · score {p.get('score')}"]
    for w in (p.get("why") or [])[:3]:
        lines.append(f"  • {w}")
    if t.get("llm_directive"):
        lines.append(f"▸ TIMING: {t['llm_directive']}")
    lines.append("▸ BCP 10L+6L ages — background. GUARD: no invented months.")
    return "\n".join(lines)

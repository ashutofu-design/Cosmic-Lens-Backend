"""Setback / recovery engine v1 — 8H/6H stress + 11H recovery + 8L+11L BCP."""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Optional

from event_timing.career.bcp_setback_ages import compute_bcp_setback_ages
from event_timing.career.govt_job_engine_v1 import (
    _dasha_lords, _house_lord, _parse_iso, _planet_house,
)

_BENEFICS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_DUSTHANA = frozenset({6, 8, 12})
_SCORE_PD, _SCORE_AD = 8, 6
_MIN = 5
_TIMING_RE = re.compile(r"(?i)\b(kab|when|recover|recovery|theek|ubhr|niklega|niklegi)\b")


def detect_setback_mode(q: str) -> str:
    return "timing" if _TIMING_RE.search(q or "") else "general"


def run_setback_bcp_parallel(kundli: dict, lagna_si: int, *, user_age: Optional[int] = None) -> dict:
    bcp = compute_bcp_setback_ages(kundli, lagna_si, user_age=user_age)
    return {
        "bcp_parallel": True, "eighth_lord": bcp["eighth_lord"], "eighth_lord_house": bcp["eighth_lord_house"],
        "eleventh_lord": bcp["eleventh_lord"], "eleventh_lord_house": bcp["eleventh_lord_house"],
        "aspect_houses_8l": bcp.get("aspect_houses_8l"), "aspect_houses_11l": bcp.get("aspect_houses_11l"),
        "all_recovery_ages": bcp.get("all_recovery_ages") or [],
        "future_priority_ages": bcp.get("future_priority_ages") or [],
        "next_activation_age": bcp.get("next_activation_age"),
    }


def assess_setback_recovery(
    kundli: dict, intel: dict, *, t1_d: Optional[dict] = None, jup_t: Optional[dict] = None,
    kp_assist: Optional[dict] = None,
) -> dict:
    planets = kundli.get("planets") or []
    eighth_lord, sixth_lord, eleventh_lord = _house_lord(intel, 8), _house_lord(intel, 6), _house_lord(intel, 11)
    score, why = 0, []

    sade = intel.get("sade_sati") or {}
    if isinstance(sade, dict):
        if not sade.get("active"):
            score += 2; why.append("Sade Sati not active — recovery base (+2)")
        elif str(sade.get("phase") or "").lower() in ("setting", "third"):
            score += 1; why.append("Sade Sati easing (+1)")

    for lord, label in ((eighth_lord, "8L"), (sixth_lord, "6L")):
        h = _planet_house(planets, lord) if lord else None
        if h in _DUSTHANA:
            score -= 4
            why.append(f"{label} in {h}H — setback stress active (-4)")

    el11_h = _planet_house(planets, eleventh_lord) if eleventh_lord else None
    if el11_h in {11, 10, 2}:
        score += 10
        why.append(f"11L in {el11_h}H — recovery gains channel (+10)")

    if isinstance(t1_d, dict):
        nxt = t1_d.get("next_career_window") or {}
        nxt_ad = nxt.get("ad")
        if nxt_ad in _BENEFICS:
            score += 3; why.append(f"Next AD {nxt_ad} benefic — soft recovery (+3)")

    if isinstance(jup_t, dict):
        future = [w for w in (jup_t.get("all_windows") or [])
                  if str(w.get("start") or "") > datetime.utcnow().strftime("%Y-%m-%d")]
        if future:
            score += 2; why.append("Jupiter grace window incoming (+2)")

    if isinstance(kp_assist, dict):
        setback_c, recovery_c = 0, 0
        for info in (kp_assist.get("per_cusp") or {}).values():
            if info.get("polarity") == "-":
                setback_c += int(info.get("score") or 0)
            else:
                recovery_c += int(info.get("score") or 0)
        delta = recovery_c - setback_c
        score += delta
        if delta:
            why.append(f"KP recovery-net {delta:+d}")

    outlook = ("STRONG_RECOVERY" if score >= 5 else "moderate_recovery" if score >= 3
               else "slow_recovery" if score >= 1 else "no_clear_signal")
    core = {x for x in (eleventh_lord, sixth_lord) if x} | _BENEFICS
    return {"fired": True, "engine": "setback_engine_v1", "recovery_outlook": outlook,
            "recovery_score": score, "why": why, "eighth_lord": eighth_lord,
            "eleventh_lord": eleventh_lord, "recovery_core": sorted(core)}


def _flatten(kundli: dict) -> list[dict]:
    out, today = [], datetime.utcnow()
    horizon = today + timedelta(days=365 * 8)
    for md_row in kundli.get("dashas") or []:
        if not isinstance(md_row, dict):
            continue
        md = str(md_row.get("planet") or md_row.get("lord") or "").strip()
        for ad_row in (md_row.get("subDashas") or md_row.get("antardashas") or []):
            if not isinstance(ad_row, dict):
                continue
            ad = str(ad_row.get("planet") or ad_row.get("lord") or "").strip()
            ad_end = _parse_iso(ad_row.get("endDate") or ad_row.get("end"))
            ad_start = _parse_iso(ad_row.get("startDate") or ad_row.get("start"))
            if not (ad and ad_start and ad_end) or ad_end < today - timedelta(days=30):
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


def assess_setback_timing(kundli: dict, recovery: dict) -> dict:
    core = set(recovery.get("recovery_core") or [])
    md, ad, pd = _dasha_lords(kundli)
    today = datetime.utcnow()
    cur_hit = (ad in core) or (pd in core)
    cur_sc = (pd in core) * _SCORE_PD + (ad in core) * _SCORE_AD
    current_supports = cur_hit and cur_sc >= _MIN
    ranked = []
    for c in _flatten(kundli):
        sc = (c["pd"] in core) * _SCORE_PD + (c["ad"] in core) * _SCORE_AD
        if sc < _MIN:
            continue
        ranked.append({**c, "score": sc, "lords": "/".join(x for x in (c["md"], c["ad"], c["pd"]) if x),
                       "start_label": c["start"].strftime("%Y-%m"), "end_label": c["end"].strftime("%Y-%m")})
    ranked.sort(key=lambda w: (-w["score"], w["start"]))
    rec, src = None, "none"
    if current_supports:
        for w in ranked:
            if w["start"] <= today <= w["end"]:
                rec, src = w, "current_dasha"; break
    else:
        for w in ranked:
            if w["end"] >= today:
                rec, src = w, "next_dasha"; break
    directive = ""
    if src == "current_dasha":
        directive = f"Recovery active — AD/PD {ad}/{pd} supportive."
    elif src == "next_dasha" and rec:
        directive = f"Recovery window NEXT: {rec.get('lords')} ({rec.get('start_label')}→{rec.get('end_label')})."
    else:
        directive = "Setback peak — stability + patience; drastic moves avoid."
    return {"current_supports_recovery": current_supports, "timing_source": src,
            "recommended_window": rec, "llm_directive": directive}


def assess_setback(kundli: dict, intel: dict, *, question: str = "", lagna_si: int = -1,
                   t1_d: Optional[dict] = None, jup_t: Optional[dict] = None,
                   kp: Optional[dict] = None, kp_assist_fn: Any = None,
                   user_age: Optional[int] = None) -> dict:
    kp_a = kp_assist_fn(kp) if callable(kp_assist_fn) and kp else None
    bcp = run_setback_bcp_parallel(kundli, lagna_si, user_age=user_age) if lagna_si >= 0 else {}
    recovery = assess_setback_recovery(kundli, intel, t1_d=t1_d, jup_t=jup_t, kp_assist=kp_a)
    timing = assess_setback_timing(kundli, recovery)
    return {"question_mode": detect_setback_mode(question), "bcp_parallel": bcp,
            "recovery": recovery, "timing": timing, "recovery_outlook": recovery.get("recovery_outlook"),
            "verdict_label": "RECOVERY_ACTIVE" if timing.get("current_supports_recovery") else "RECOVERY_NEXT",
            "strategy": timing.get("llm_directive") or "Mental health + financial discipline maintain karo."}


def format_setback_block_for_prompt(result: dict, question: str = "") -> str:
    r, t = result.get("recovery") or {}, result.get("timing") or {}
    lines = ["=== SETBACK / RECOVERY ENGINE v1 (LOCKED) ===",
             f"Outlook: {r.get('recovery_outlook')} · score {r.get('recovery_score')}"]
    for w in (r.get("why") or [])[:4]:
        lines.append(f"  • {w}")
    if t.get("llm_directive"):
        lines.append(f"▸ TIMING: {t['llm_directive']}")
    lines.append("GUARD: no guaranteed turnaround date. Support systems use karo.")
    return "\n".join(lines)

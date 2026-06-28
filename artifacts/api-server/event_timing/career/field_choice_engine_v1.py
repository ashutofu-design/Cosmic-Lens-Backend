"""Field-choice engine v1 — 5H/10H/3H + 5L+10L BCP + planet→field map."""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Optional

from event_timing.career.bcp_5l_10l_ages import compute_bcp_5l_10l_ages
from event_timing.career.govt_job_engine_v1 import (
    _dasha_lords, _house_lord, _parse_iso, _planet_house,
)

_PLANET_FIELDS = {
    "Sun": ["government", "PSU", "leadership", "administration"],
    "Saturn": ["service/corporate job", "construction", "long-term roles"],
    "Mercury": ["IT/software", "accounting", "communications", "banking"],
    "Mars": ["engineering", "military/police", "technical roles"],
    "Jupiter": ["teaching", "law", "advisory/consulting", "finance"],
    "Venus": ["arts", "fashion", "media", "design", "hospitality"],
    "Moon": ["healthcare", "psychology", "public-facing roles"],
    "Rahu": ["technology", "foreign work", "research/science"],
    "Ketu": ["research", "niche specialisations", "IT deep-tech"],
}

_SCORE_PD, _SCORE_AD = 9, 7
_MIN = 6
_TIMING_RE = re.compile(r"(?i)\b(kab|when|start|shuru|enter)\b")


def detect_field_choice_mode(q: str) -> str:
    return "timing" if _TIMING_RE.search(q or "") else "general"


def run_field_choice_bcp_parallel(kundli: dict, lagna_si: int, *, user_age: Optional[int] = None) -> dict:
    bcp = compute_bcp_5l_10l_ages(kundli, lagna_si, user_age=user_age)
    return {
        "bcp_parallel": True, "fifth_lord": bcp["fifth_lord"], "fifth_lord_house": bcp["fifth_lord_house"],
        "tenth_lord": bcp["tenth_lord"], "tenth_lord_house": bcp["tenth_lord_house"],
        "all_field_ages": bcp.get("all_ages") or [], "future_priority_ages": bcp.get("future_priority_ages") or [],
        "next_activation_age": bcp.get("next_activation_age"),
    }


def _rank_fields(intel: dict, kundli: dict, karakas_d: dict) -> dict:
    planets = kundli.get("planets") or []
    candidates: dict[str, int] = {}

    def bump(planet: str, weight: int):
        if planet in _PLANET_FIELDS:
            for field in _PLANET_FIELDS[planet]:
                candidates[field] = candidates.get(field, 0) + weight

    tl = _house_lord(intel, 10)
    fl = _house_lord(intel, 5)
    if tl:
        bump(tl, 4)
    if fl:
        bump(fl, 5)
    amk = (karakas_d or {}).get("AmK")
    if amk:
        bump(amk, 4)
    for p in planets:
        if isinstance(p, dict) and p.get("house") == 10 and p.get("name"):
            bump(p["name"], 3)
    ranked = sorted(candidates.items(), key=lambda kv: -kv[1])[:5]
    return {"top_fields": [{"field": f, "score": s} for f, s in ranked],
            "drivers": {"10L": tl, "5L": fl, "AmK": amk}}


def assess_field_choice_promise(kundli: dict, intel: dict, *, karakas_d: Optional[dict] = None,
                                kp_assist: Optional[dict] = None) -> dict:
    planets = kundli.get("planets") or []
    fifth_lord, tenth_lord, third_lord = _house_lord(intel, 5), _house_lord(intel, 10), _house_lord(intel, 3)
    score, why = 0, []
    for lord, label in ((fifth_lord, "5L passion"), (tenth_lord, "10L karma"), (third_lord, "3L skills")):
        h = _planet_house(planets, lord) if lord else None
        if h in {1, 5, 9, 10, 11}:
            score += 8
            why.append(f"{label} {lord} in {h}H (+8)")
    fields = _rank_fields(intel, kundli, karakas_d or {})
    if fields.get("top_fields"):
        why.append(f"Top field signal: {fields['top_fields'][0].get('field')}")
    if isinstance(kp_assist, dict):
        score += int(kp_assist.get("score") or 0)
    level = "high" if score >= 20 else "moderate" if score >= 10 else "low"
    core = {x for x in (fifth_lord, tenth_lord, third_lord) if x}
    return {"fired": True, "engine": "field_choice_engine_v1", "field_fit_level": level,
            "score": score, "why": why, "field_recommendations": fields,
            "fifth_lord": fifth_lord, "tenth_lord": tenth_lord, "field_core": sorted(core)}


def _flatten(kundli: dict) -> list[dict]:
    out, today = [], datetime.utcnow()
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


def assess_field_choice_timing(kundli: dict, promise: dict) -> dict:
    core = set(promise.get("field_core") or [])
    md, ad, pd = _dasha_lords(kundli)
    today = datetime.utcnow()
    cur_sc = (pd in core) * _SCORE_PD + (ad in core) * _SCORE_AD
    cur_hit = (ad in core) or (pd in core)
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
    fifth = promise.get("fifth_lord")
    directive = ""
    if src == "current_dasha":
        directive = f"Field pivot window — 5L/10L AD/PD active ({ad}/{pd})."
    elif src == "next_dasha" and rec:
        directive = f"NEXT field-entry window: {rec.get('lords')}."
    else:
        directive = f"Build skills now; 5L {fifth} dasha window scan for entry timing."
    return {"current_supports_field": current_supports, "timing_source": src,
            "recommended_window": rec, "llm_directive": directive}


def assess_field_choice(kundli: dict, intel: dict, *, question: str = "", lagna_si: int = -1,
                        karakas_d: Optional[dict] = None, kp: Optional[dict] = None,
                        kp_assist_fn: Any = None, user_age: Optional[int] = None) -> dict:
    kp_a = kp_assist_fn(kp) if callable(kp_assist_fn) and kp else None
    bcp = run_field_choice_bcp_parallel(kundli, lagna_si, user_age=user_age) if lagna_si >= 0 else {}
    promise = assess_field_choice_promise(kundli, intel, karakas_d=karakas_d, kp_assist=kp_a)
    timing = assess_field_choice_timing(kundli, promise)
    return {"question_mode": detect_field_choice_mode(question), "bcp_parallel": bcp,
            "promise": promise, "timing": timing, "field_fit_level": promise.get("field_fit_level"),
            "field_recommendations": promise.get("field_recommendations"),
            "verdict_label": "FIELD_WINDOW_OPEN" if timing.get("current_supports_field") else "FIELD_PREPARE",
            "strategy": timing.get("llm_directive") or "Top fields par skill-build karo."}


def format_field_choice_block_for_prompt(result: dict, question: str = "") -> str:
    p, t = result.get("promise") or {}, result.get("timing") or {}
    fr = p.get("field_recommendations") or {}
    lines = ["=== FIELD-CHOICE ENGINE v1 (LOCKED) ===", f"Fit: {p.get('field_fit_level')}"]
    for f in (fr.get("top_fields") or [])[:3]:
        lines.append(f"  • {f.get('field')} (signal {f.get('score')})")
    if t.get("llm_directive"):
        lines.append(f"▸ TIMING: {t['llm_directive']}")
    lines.append("GUARD: fields are tendencies — passion + market research zaroori.")
    return "\n".join(lines)

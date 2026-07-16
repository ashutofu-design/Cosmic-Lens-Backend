"""Love timing engine v1 — 12 buckets + 5L+7L BCP + AD/PD dasha + Jupiter/Venus transit + D9."""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Optional

from event_timing.love.bcp_love_ages import compute_bcp_love_ages
from event_timing.love.love_transit_layer import (
    assess_d9_love_overlay,
    assess_love_transits,
    merge_transit_directive,
)
from event_timing.career.govt_job_engine_v1 import (
    _dasha_lords, _house_lord, _parse_iso, _planet_dignity, _planet_house,
)

LOVE_TONE_RULES: tuple = (
    "Never encourage breakup or separation; offer perspective only.",
    "Do not label a partner with toxic-trait diagnoses.",
    "Never promise love outcome as certainty; use probability window language.",
    "No third-party identification — cosmic pattern level only.",
)

_ROMANCE_H = frozenset({5, 7, 11})
_LEAK_H = frozenset({6, 8, 12})
_BENEFICS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_SCORE_PD, _SCORE_AD, _SCORE_MD = 9, 7, 2
_MIN = 6
_SCAN = 8

# First-match wins — order matters (reconciliation-end before breakup, discovery before affair).
_BUCKET_RULES: list[tuple[str, re.Pattern]] = [
    ("family_approval", re.compile(
        r"(?ix)\b(parents?|ma\s*baap|ghar\s*wale|family|parivaar|raazi|raazi|"
        r"manzoori|approval|samaaj|societal\s+recognition|opposition\s+door)\b",
    )),
    ("discovery", re.compile(
        r"(?ix)\b(pata\s+chalega|reveal|sach\s+samne|loyalty|dhokha\s+kab|"
        r"cheat\s+kab|hidden|chhip)\b",
    )),
    ("healing", re.compile(
        r"(?ix)\b(healing|doori|distance\s+phase|alag\s+reh|recover|"
        r"thoda\s+door|space\s+le|chhod\s+de\s+rishta)\b",
    )),
    ("stress_phase", re.compile(
        r"(?ix)\b(stressful\s+phase|tough\s+phase|rukawat|rough\s+patch|"
        r"dispute\s+resolve|court\s+case|relationship\s+dispute|galatfehmi\w*|"
        r"misunderstanding\w*)\b",
    )),
    ("reconciliation", re.compile(
        r"(?ix)\b(patchup|patch\s*up|reconcile|wapas|ex\s+wapas|return|"
        r"unblock|no[\s-]?contact|contact\s+kab|dusra\s+chance|second\s+chance|"
        r"vakri\s+shukra|retrograde\s+venus|purana\s+pyaar)\b",
    )),
    ("one_sided", re.compile(
        r"(?ix)\b(one[\s-]?sided|crush|unrequited|notice\s+kare)\b",
    )),
    ("commitment", re.compile(
        r"(?ix)\b(commitment|propose|proposal|serious\s+ho|haan\s+kab|"
        r"rahu.{0,20}commitment|ketu.{0,20}commitment)\b",
    )),
    ("breakup", re.compile(
        r"(?ix)\b(breakup|break\s*up|alag\s+ho|rishta\s+toot|permanent\s+breakup|"
        r"separation\s+ka\s+khatra|breakup\s+ka\s+khatra)\b",
    )),
    ("meeting", re.compile(
        r"(?ix)\b(milna|milenge|mulakat|meet|long\s*distance|ldr|"
        r"enter\s+karega|social\s+circle|circle\s+se\s+bahar|naya\s+insaan)\b",
    )),
    ("affair", re.compile(
        r"(?ix)\b(affair|third\s*party|dhokha|cheat|koi\s+aur|teesra\s+insaan)\b",
    )),
    ("general_love", re.compile(
        r"(?ix)\b(love\s+life|love\s+live|relationship\s+theek|struggle\s+khatam|"
        r"dry\s+spell|single\s+status|soulmate|true\s+love|pehla\s+serious|"
        r"relationship\s+shuru|rishta\s+shuru|naya\s+relationship|favorable\s+dasha)\b",
    )),
    ("timing", re.compile(
        r"(?ix)\b(kab|when|milega|milegi|hoga|hogi|aayega|aayegi|shuru|"
        r"trigger|kis\s+saal|kis\s+mahine|gochar|transit)\b",
    )),
]

_RECONCILE_END_RX = re.compile(
    r"(?ix)(separation|break[\s-]?up|alag|no[\s-]?contact).{0,50}(khatam|khatm|door|end|solve|break\s+ho)",
)

_BUCKET_CORE: dict[str, set[str]] = {
    "timing": {"5L", "7L", "Venus", "Moon", "11L"},
    "reconciliation": {"5L", "7L", "11L", "Venus", "Moon"},
    "one_sided": {"5L", "11L", "Venus", "Moon"},
    "commitment": {"7L", "Venus", "Jupiter", "5L"},
    "breakup": {"8L", "12L", "6L", "Saturn", "Rahu"},
    "meeting": {"5L", "7L", "Venus", "Mercury", "11L"},
    "affair": {"12L", "8L", "Rahu", "Venus", "6L"},
    "general_love": {"5L", "7L", "Venus", "11L", "Jupiter"},
    "family_approval": {"2L", "4L", "7L", "Jupiter", "Venus"},
    "healing": {"12L", "8L", "Moon", "Venus"},
    "stress_phase": {"6L", "8L", "Saturn", "Mars"},
    "discovery": {"8L", "12L", "Rahu", "Venus", "Moon"},
}


def classify_love_timing_bucket(question: str, pre: Optional[str] = None) -> str:
    if pre and pre in _BUCKET_CORE:
        return pre
    q = question or ""
    if _RECONCILE_END_RX.search(q):
        return "reconciliation"
    if re.search(r"(?ix)(khatam|khatm|door).{0,40}(separation|break|alag)\b", q):
        return "reconciliation"
    for name, rx in _BUCKET_RULES:
        if rx.search(q):
            if name == "general_love" and re.search(
                r"(?ix)\b(transit|trigger|gochar)\b", q,
            ):
                return "timing"
            return name
    return "timing"


def _lagna_si(kundli: dict) -> int:
    asc = kundli.get("ascendant") or ""
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    if asc in signs:
        return signs.index(asc)
    return -1


def _lord_labels(intel: dict) -> dict[str, str]:
    return {
        "2L": _house_lord(intel, 2) or "",
        "4L": _house_lord(intel, 4) or "",
        "5L": _house_lord(intel, 5) or "",
        "7L": _house_lord(intel, 7) or "",
        "11L": _house_lord(intel, 11) or "",
        "6L": _house_lord(intel, 6) or "",
        "8L": _house_lord(intel, 8) or "",
        "12L": _house_lord(intel, 12) or "",
    }


def _core_lords(bucket: str, labels: dict[str, str]) -> set[str]:
    core: set[str] = set()
    for tag in _BUCKET_CORE.get(bucket, _BUCKET_CORE["timing"]):
        if tag in labels and labels[tag]:
            core.add(labels[tag])
        elif tag in _BENEFICS or tag in {"Venus", "Moon", "Mars", "Saturn", "Rahu", "Mercury", "Jupiter"}:
            core.add(tag)
    return {x for x in core if x}


def run_love_bcp_parallel(kundli: dict, lagna_si: int, *, user_age: Optional[int] = None) -> dict:
    bcp = compute_bcp_love_ages(kundli, lagna_si, user_age=user_age)
    return {
        "bcp_parallel": True,
        "fifth_lord": bcp["fifth_lord"],
        "fifth_lord_house": bcp["fifth_lord_house"],
        "seventh_lord": bcp["seventh_lord"],
        "seventh_lord_house": bcp["seventh_lord_house"],
        "aspect_houses_5l": bcp.get("aspect_houses_5l"),
        "aspect_houses_7l": bcp.get("aspect_houses_7l"),
        "all_love_ages": bcp.get("all_love_ages") or [],
        "future_priority_ages": bcp.get("future_priority_ages") or [],
        "next_activation_age": bcp.get("next_activation_age"),
    }


def _assess_promise(kundli: dict, intel: dict, bucket: str) -> dict:
    planets = kundli.get("planets") or []
    labels = _lord_labels(intel)
    score, why = 0, []
    for lord, label in ((labels.get("5L"), "5L"), (labels.get("7L"), "7L")):
        if not lord:
            continue
        h = _planet_house(planets, lord)
        if h in _ROMANCE_H:
            score += 12
            why.append(f"{label} {lord} in {h}H — romance axis (+12)")
        dgn = _planet_dignity(intel, lord)
        if dgn in ("exalted", "own-sign", "moolatrikona"):
            score += 5
            why.append(f"{label} strong dignity (+5)")
    venus_h = _planet_house(planets, "Venus")
    if venus_h in _ROMANCE_H:
        score += 10
        why.append(f"Venus in {venus_h}H (+10)")
    if bucket == "breakup":
        for lord in (labels.get("8L"), labels.get("12L")):
            if lord and _planet_house(planets, lord) in _LEAK_H:
                score += 8
                why.append(f"{lord} leak-house — separation stress (+8)")
    elif bucket == "family_approval":
        jup_h = _planet_house(planets, "Jupiter")
        if jup_h in {2, 4, 7, 11}:
            score += 8
            why.append(f"Jupiter in {jup_h}H — family blessing tone (+8)")
        for lord, lbl in ((labels.get("2L"), "2L"), (labels.get("4L"), "4L")):
            if lord and _planet_house(planets, lord) in {4, 7, 11}:
                score += 5
                why.append(f"{lbl} supportive for family consent (+5)")
    elif bucket == "healing":
        moon_h = _planet_house(planets, "Moon")
        if moon_h in {4, 12}:
            score += 6
            why.append(f"Moon in {moon_h}H — emotional recovery channel (+6)")
    elif bucket == "stress_phase":
        sat_h = _planet_house(planets, "Saturn")
        if sat_h in {6, 8, 12}:
            score += 6
            why.append(f"Saturn in {sat_h}H — stress phase active (+6)")
    elif bucket == "discovery":
        rahu_h = _planet_house(planets, "Rahu")
        if rahu_h in {8, 12}:
            score += 8
            why.append(f"Rahu in {rahu_h}H — hidden truth surfacing (+8)")
    elif bucket == "reconciliation":
        if labels.get("11L") and _planet_house(planets, labels["11L"]) in {5, 7, 11}:
            score += 6
            why.append("11L in romance house — reunion channel (+6)")
    level = "high" if score >= 28 else "moderate" if score >= 14 else "low"
    return {"promise_level": level, "score": score, "why": why, "labels": labels}


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
            ad_start = _parse_iso(ad_row.get("startDate") or ad_row.get("start"))
            ad_end = _parse_iso(ad_row.get("endDate") or ad_row.get("end"))
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


def _assess_timing(kundli: dict, bucket: str, labels: dict[str, str]) -> dict:
    core = _core_lords(bucket, labels)
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
        ranked.append({
            **c, "score": sc,
            "lords": "/".join(x for x in (c["md"], c["ad"], c["pd"]) if x),
            "start_label": c["start"].strftime("%Y-%m"),
            "end_label": c["end"].strftime("%Y-%m"),
        })
    ranked.sort(key=lambda w: (-w["score"], w["start"]))
    rec, src = None, "none"
    if current_supports:
        for w in ranked:
            if w["start"] <= today <= w["end"]:
                rec, src = w, "current_dasha"
                break
        if not rec:
            rec = {"lords": f"{md}/{ad}/{pd}", "ad": ad, "pd": pd, "start_label": "current", "end_label": "current"}
            src = "current_dasha"
    else:
        for w in ranked:
            if w["end"] >= today:
                rec, src = w, "next_dasha"
                break
    directive = ""
    if src == "current_dasha":
        directive = f"CURRENT love window — AD/PD {ad}/{pd} supportive for {bucket}."
    elif src == "next_dasha" and rec:
        directive = f"NEXT love window: {rec.get('lords')} ({rec.get('start_label')}→{rec.get('end_label')})."
    else:
        directive = f"Current dasha weak for {bucket} — next 5L/7L/Venus AD/PD scan."
    return {
        "current_supports": current_supports,
        "timing_source": src,
        "recommended_window": rec,
        "llm_directive": directive,
        "current_window": {
            "md": md, "ad": ad, "pd": pd,
            "start_iso": rec.get("start_label") if rec else "current",
            "end_iso": rec.get("end_label") if rec else "current",
        } if rec else {},
    }


def assess_love_timing(
    kundli: dict,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: Optional[str] = None,
    user_age: Optional[int] = None,
) -> dict:
    """Delegate to dasha-first love timing; preserve user_age for eligibility attach."""
    from event_timing.love.love_timing_v1 import compute_love_window

    raw = compute_love_window(kundli, intel, kp, birth, question, bucket=bucket)
    if not isinstance(raw, dict):
        return {"user_age": user_age, "verdict": "UNKNOWN"}
    if user_age is not None:
        raw["user_age"] = user_age
    return raw


def format_love_timing_for_prompt(v: dict, question: str = "") -> str:
    if not isinstance(v, dict) or not v:
        return ""
    lines = [
        "=== LOVE TIMING ENGINE v1 (LOCKED) ===",
        f"Bucket: {v.get('bucket')} · Verdict: {v.get('verdict')} · Band: {v.get('band')}",
    ]
    p = v.get("promise") or {}
    for w in (p.get("why") or [])[:4]:
        lines.append(f"  • {w}")
    t = v.get("timing") or {}
    if t.get("llm_directive"):
        lines.append(f"▸ TIMING: {t['llm_directive']}")
    tr = v.get("transits") or {}
    if tr.get("venus_retrograde_now"):
        lines.append("▸ Vakri Shukra (retrograde Venus) ACTIVE in transit.")
    bcp = v.get("bcp_parallel") or {}
    if bcp:
        lines.append(f"▸ BCP 5L+7L background: 5L@{bcp.get('fifth_lord_house')}H · 7L@{bcp.get('seventh_lord_house')}H")
    d9 = v.get("d9_overlay") or {}
    if d9.get("available") and d9.get("why"):
        lines.append("▸ D9: " + "; ".join(d9["why"][:2]))
    for g in (v.get("brand_safety_warnings") or [])[:4]:
        lines.append(f"  GUARD: {g}")
    lines.append("RULE: current dasha NAHI support → sirf NEXT AD/PD window; transit refines month.")
    return "\n".join(lines)


# Backward compat alias
compute_love_window = assess_love_timing

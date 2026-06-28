"""Love static engine v1 — non-timing love Qs (diagnosis, loyalty, compatibility single-chart)."""
from __future__ import annotations

import re
from typing import Any, Optional

from event_timing.career.govt_job_engine_v1 import (
    _house_lord, _planet_dignity, _planet_house,
)

LOVE_TONE_RULES: tuple = (
    "Never encourage breakup or separation; offer perspective only.",
    "Do not label a partner with toxic-trait diagnoses.",
    "Honour user's emotional state — empathise before chart-talk.",
    "Never promise love-marriage timing as certainty.",
)

_STATIC_RULES: list[tuple[str, re.Pattern]] = [
    ("affair_third_party", re.compile(r"(?ix)\b(affair|dhokha|cheat|third\s*party|koi\s+aur|loyal)\b")),
    ("breakup_signal", re.compile(r"(?ix)\b(breakup|break\s*up|alag|toot|separation|chhod)\b")),
    ("one_sided", re.compile(r"(?ix)\b(one[\s-]?sided|crush|unrequited|pyaar\s+nahi)\b")),
    ("compatibility", re.compile(r"(?ix)\b(compatible|compatibility|match|milta|suit)\b")),
    ("commitment_fear", re.compile(r"(?ix)\b(commitment|darr|afraid|serious\s+nahi)\b")),
    ("existing_status", re.compile(r"(?ix)\b(ab\s+relationship|currently|chal\s+raha|status)\b")),
    ("general_love", re.compile(r"(?ix)\b(love|pyaar|pyar|rishta|relationship)\b")),
]

_TIMING_RX = re.compile(r"(?ix)\b(kab|when|milega|milegi|hoga|hogi|timing)\b")


def classify_love_static_bucket(question: str, pre: Optional[str] = None) -> str:
    if pre and pre in {r[0] for r in _STATIC_RULES}:
        return pre
    q = question or ""
    for name, rx in _STATIC_RULES:
        if rx.search(q):
            return name
    return "general_love"


def assess_love_static(
    kundli: dict,
    intel: dict,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    *,
    pre_classified_bucket: Optional[str] = None,
) -> dict:
    _ = kp, birth
    if _TIMING_RX.search(question or ""):
        from event_timing.love.love_timing_engine_v1 import assess_love_timing
        out = assess_love_timing(kundli, intel, kp, birth, question, bucket=pre_classified_bucket)
        return _timing_as_static_shape(out)

    bucket = classify_love_static_bucket(question, pre_classified_bucket)
    planets = kundli.get("planets") or []
    fifth_lord = _house_lord(intel, 5)
    seventh_lord = _house_lord(intel, 7)
    eleventh_lord = _house_lord(intel, 11)
    eighth_lord = _house_lord(intel, 8)
    twelfth_lord = _house_lord(intel, 12)

    natal, trigger, why = 0, 0, []
    fl5 = _planet_house(planets, fifth_lord) if fifth_lord else None
    fl7 = _planet_house(planets, seventh_lord) if seventh_lord else None
    venus_h = _planet_house(planets, "Venus")
    moon_h = _planet_house(planets, "Moon")
    rahu_h = _planet_house(planets, "Rahu")

    if fl5 in {5, 7, 11}:
        natal += 15
        why.append(f"5L in {fl5}H — romance foundation (+15)")
    if fl7 in {5, 7, 11}:
        natal += 12
        why.append(f"7L in {fl7}H — partnership channel (+12)")
    if venus_h in {5, 7, 11}:
        natal += 14
        why.append(f"Venus in {venus_h}H — attraction strong (+14)")
    elif _planet_dignity(intel, "Venus") in ("debilitated", "enemy-sign"):
        natal -= 6
        why.append("Venus weak — romance friction (-6)")

    if bucket == "breakup_signal":
        if eighth_lord and _planet_house(planets, eighth_lord) in {6, 8, 12}:
            trigger += 10
            why.append("8L dusthana — separation stress active (+10)")
        if twelfth_lord and _planet_house(planets, twelfth_lord) in {8, 12}:
            trigger += 8
    elif bucket == "affair_third_party":
        if rahu_h in {5, 7, 12} or (venus_h and moon_h and abs((venus_h or 0) - (moon_h or 0)) <= 1):
            trigger += 12
            why.append("Rahu/Venus-Moon — hidden/third-party pattern (+12)")
    elif bucket == "one_sided":
        if eleventh_lord and _planet_house(planets, eleventh_lord) == 12:
            trigger += 8
            why.append("11L in 12H — desire unfulfilled tone (+8)")
    elif bucket == "compatibility":
        if fl5 and fl7 and fl5 == fl7:
            natal += 10
            why.append("5L-7L same house — love-marriage link (+10)")

    total = max(0, min(100, natal + trigger))
    if total >= 55:
        verdict = "green_supportive"
    elif total >= 30:
        verdict = "yellow_mixed"
    else:
        verdict = "red_caution"

    return {
        "engine": "love_static_engine_v1",
        "question_type": bucket,
        "verdict": verdict,
        "score": total,
        "natal_promise_score": natal,
        "current_trigger_score": trigger,
        "why": why,
        "window": "",
        "dasha_window": {},
        "strategy": _strategy_for(bucket, verdict),
        "love_tone_rules": list(LOVE_TONE_RULES),
        "fifth_lord": fifth_lord,
        "seventh_lord": seventh_lord,
    }


def _strategy_for(bucket: str, verdict: str) -> str:
    if bucket == "breakup_signal":
        return "Impulsive decision avoid — pehle communication + space; cosmic plane pe healing window dekho."
    if bucket == "one_sided":
        return "Self-worth preserve karo; one-sided ko force mat karo — dasha window mein clarity aati hai."
    if bucket == "affair_third_party":
        return "Direct confrontation se pehle facts gather karo; pattern-level insight lo, blame game nahi."
    if bucket == "compatibility":
        return "Chart tendency batati hai — real life mein values + communication equally zaroori."
    return "Patience + honest communication; timing ke liye alag se kab wala sawal pucho."


def _timing_as_static_shape(timing_out: dict) -> dict:
    t = timing_out.get("timing") or {}
    rec = t.get("recommended_window") or {}
    window = ""
    if rec.get("start_label") and rec.get("end_label"):
        window = f"{rec.get('start_label')} → {rec.get('end_label')}"
    return {
        "engine": "love_timing_engine_v1",
        "question_type": timing_out.get("bucket") or "timing",
        "verdict": timing_out.get("verdict") or "LOVE_WINDOW_MODERATE",
        "score": (timing_out.get("promise") or {}).get("score", 0),
        "natal_promise_score": (timing_out.get("promise") or {}).get("score", 0),
        "current_trigger_score": 0,
        "why": timing_out.get("factors") or [],
        "window": window,
        "dasha_window": t.get("current_window") or {},
        "strategy": timing_out.get("strategy") or t.get("llm_directive") or "",
        "love_tone_rules": timing_out.get("love_tone_rules") or list(LOVE_TONE_RULES),
        "timing_engine": timing_out,
    }


def format_love_static_for_prompt(v: dict, question: str = "") -> str:
    if not v:
        return ""
    lines = [
        "=== LOVE STATIC ENGINE v1 (LOCKED) ===",
        f"Type: {v.get('question_type')} · Verdict: {v.get('verdict')} · Score: {v.get('score')}",
    ]
    for w in (v.get("why") or [])[:5]:
        lines.append(f"  • {w}")
    if v.get("strategy"):
        lines.append(f"▸ Strategy: {v['strategy']}")
    for t in (v.get("love_tone_rules") or [])[:4]:
        lines.append(f"  TONE: {t}")
    return "\n".join(lines)

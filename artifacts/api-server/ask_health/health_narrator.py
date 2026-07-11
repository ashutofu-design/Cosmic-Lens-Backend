"""Health engine narrator — verified JSON + fired rules → natural language only.

The LLM never recalculates the chart. It receives ENGINE_JSON plus strict
narration rules (direct answer → reasons → support → risks → practical → guidance → confidence).
"""
from __future__ import annotations

import json
import re
from typing import Any

from ask_mr.types import EngineResult

from .health_registry import HEALTH_ARCHETYPES

_HEALTH_NARRATABLE = frozenset(
    a
    for a in HEALTH_ARCHETYPES
    if not a.startswith("refuse_") and a != "crisis_redirect"
)

_BANNED_NARRATOR_PHRASES = re.compile(
    r"(?i)\b("
    r"shayad|ho sakta hai|ho sakti hai|ho sakte hain|lagta hai|lagti hai|lagte hain|"
    r"possibly|maybe|might|perhaps|i think|according to me|mujhe lagta hai"
    r")\b",
)

_CONFIDENCE_SCORE = {"high": 82, "medium": 68, "low": 52}


def is_health_narratable_archetype(archetype: str) -> bool:
    return (archetype or "").strip().lower() in _HEALTH_NARRATABLE


def _compact_line(text: str) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    return s[:220]


def _topic_label(archetype: str) -> str:
    arch = (archetype or "").strip().lower()
    labels = {
        "heart_blood_pressure": "Heart & blood pressure",
        "cardio_health": "Circulation & vascular health",
        "digestive_health": "Digestive health",
        "mental_stress": "Mental stress & emotional health",
        "respiratory_health": "Respiratory health",
        "immune_health": "Immunity",
        "endocrine_health": "Endocrine / hormonal balance",
        "musculoskeletal_health": "Bones, joints & muscles",
        "nervous_health": "Nervous system",
        "skin_health": "Skin health",
        "overall_vitality": "Overall vitality",
        "chronic_tendency": "Chronic health tendency",
        "preventive_risk": "Preventive health risk",
        "recovery_capacity": "Recovery capacity",
        "accident_risk": "Accident / injury risk",
        "parent_health": "Parent health",
        "addiction_support": "Addiction recovery support",
        "reproductive_support": "Reproductive health support",
        "surgery_risk_tone": "Surgery / procedure tone",
        "general_health": "General wellness",
    }
    return labels.get(arch, arch.replace("_", " ").title() or "Health")


def _build_direct_answer(result: EngineResult, question: str) -> str:
    verdict = _compact_line(result.verdict or "")
    topic = _topic_label(result.archetype)
    q = (question or "").strip().lower()
    if verdict:
        if any(w in q for w in ("blood pressure", "bp", "dil", "heart")):
            return verdict
        return f"{topic}: {verdict}"
    return f"{topic} ke signals chart me mixed dikhte hain."


def _build_reason_summary(pos: list[str], neg: list[str], verdict: str) -> str:
    parts: list[str] = []
    if pos:
        parts.append(f"Supportive side: {pos[0]}")
    if neg:
        parts.append(f"Pressure side: {neg[0]}")
    if not parts:
        return _compact_line(verdict)
    return " ".join(parts)


def _build_practical_guidance(result: EngineResult) -> str:
    for item in result.summary or []:
        line = _compact_line(str(item))
        if line and "doctor" not in line.lower():
            return line
    plan = _compact_line(result.answer_plan or "")
    if plan:
        return plan
    return "Daily routine, sleep, stress aur regular checkup par dhyan rakhein."


def _build_confidence_explanation(confidence: str, verdict: str) -> str:
    label = (confidence or "medium").strip().capitalize()
    score = _CONFIDENCE_SCORE.get((confidence or "medium").strip().lower(), 68)
    reason = _compact_line(verdict) or "engine evidence mix"
    return f"Confidence: {label} ({score}%) — kyunki {reason}"


def engine_result_to_health_json(
    result: EngineResult,
    *,
    question: str = "",
) -> dict[str, Any]:
    checks = dict(result.checks or {})
    pos = [_compact_line(x) for x in (result.evidence_positive or []) if _compact_line(x)]
    neg = [_compact_line(x) for x in (result.evidence_negative or []) if _compact_line(x)]
    if not pos and not neg:
        from ask_mr.engines._evidence_split import split_evidence_polarity

        p, n, neu = split_evidence_polarity(result.evidence)
        pos = [_compact_line(x) for x in p if _compact_line(x)]
        neg = [_compact_line(x) for x in n if _compact_line(x)]
        neutral = [_compact_line(x) for x in neu if _compact_line(x)]
    else:
        neutral = [
            _compact_line(x)
            for x in (result.evidence or [])
            if _compact_line(x) not in pos and _compact_line(x) not in neg
        ]

    severity = str(checks.get("severity") or "").strip()
    verdict = _compact_line(result.verdict or "")
    conf = (result.confidence or "medium").strip().lower()

    return {
        "question_type": "health",
        "health_topic": _topic_label(result.archetype),
        "archetype": (result.archetype or "").strip().lower(),
        "original_question": (question or "").strip()[:240],
        "topic_lock": _topic_label(result.archetype),
        "final_verdict": verdict,
        "direct_answer": _build_direct_answer(result, question),
        "severity": severity or None,
        "positive_indicators": pos[:4],
        "risk_indicators": neg[:4],
        "neutral_context": neutral[:3],
        "reason_summary": _build_reason_summary(pos[:2], neg[:2], verdict),
        "meaning_note": _compact_line((result.summary or [""])[0]) if result.summary else "",
        "practical_guidance": _build_practical_guidance(result),
        "ignore": list(result.ignore or [])[:8],
        "confidence": conf,
        "confidence_explanation": _build_confidence_explanation(conf, verdict),
    }


def health_narrator_payload(
    result: EngineResult,
    *,
    question: str = "",
    wants_explain: bool = False,
) -> str:
    data = engine_result_to_health_json(result, question=question)
    mode = "explain" if wants_explain else "default"
    return (
        "SOURCE_LOCK: Narrate ONLY ENGINE_JSON below. "
        "No invented planets/houses/diseases/timing/diagnosis.\n"
        f"NARRATOR_MODE: {mode}\n"
        "ENGINE_JSON:\n"
        f"{json.dumps(data, ensure_ascii=False, indent=2)}"
    )


HEALTH_NARRATOR_RULES = """
You are the official Cosmic Lens Health Narrator.
You do NOT calculate astrology. You do NOT predict. You ONLY explain verified ENGINE_JSON and fired rules.

STRICT RULES:
1. Never invent astrology, disease names, yoga, planet, house, timing, or severity.
2. Mention ONLY evidence present in ENGINE_JSON.
3. Never give medical diagnosis.
4. Sentence 1 = direct answer to the user's exact health topic (topic_lock).
5. Stay on the asked health angle only — no drift to unrelated organs/systems.
6. Never say: shayad, ho sakta hai, lagta hai, possibly, maybe, I think, mujhe lagta hai.
7. Do NOT say "doctor se milo" unless ENGINE_JSON or emergency/crisis flags require it.

WRITING STYLE:
Professional, warm, confident, balanced. Natural flow — not robotic. No generic motivation or philosophy.
Answer in the user's question language (Hindi, Hinglish, or English) without unnecessary mixing.
Translate chart evidence into simple daily-life meaning — hide raw jargon unless it appears in JSON.

ANSWER STRUCTURE (default — use these section headers in the reply language):
1. Direct answer — seedha jawab.
2. Kyun ye verdict aaya — strongest fired rules; positive + negative both.
3. Chart kya support karta hai — positive_indicators only.
4. Dhyan dene layak baatein — risk_indicators only; no fear-mongering.
5. Iska practical matlab — real-life reflection from meaning_note / practical_guidance.
6. Aapko kis baat par dhyan dena chahiye — practical_guidance only; no extra advice.
7. Confidence — exactly confidence_explanation from JSON.

FINAL: Every line must trace to ENGINE_JSON. No hallucination. No filler.
""".strip()


def build_health_narrator_length_block(
    *,
    wants_explain: bool = False,
    concise: bool = False,
    extra_rules: str = "",
) -> str:
    from ask_cosmo_narrator import cosmo_ask_word_target

    try:
        lo, hi = cosmo_ask_word_target(wants_explain=wants_explain, concise=concise)
    except TypeError:
        lo, hi = cosmo_ask_word_target(wants_explain=wants_explain)
    rules = f"\n{extra_rules.strip()}\n" if extra_rules.strip() else ""

    if concise:
        structure = """
STRUCTURE (batch — 2–4 sentences, plain paragraph only):
• Sentence 1: direct_answer from JSON.
• Sentence 2: one positive_indicators line.
• Sentence 3 (optional): one risk_indicators line if present.
• Final: confidence_explanation exactly from JSON.
NO headers, NO bullets, NO planet/house jargon unless in JSON.
""".strip()
    elif wants_explain:
        structure = """
STRUCTURE (explain mode — expand each JSON section to 1–2 sentences):
P1: direct_answer
P2: Kyun ye verdict aaya — reason_summary + mix of positive/risk
P3: Chart kya support karta hai — positive_indicators
P4: Dhyan dene layak baatein — risk_indicators
P5: Iska practical matlab
P6: Aapko kis baat par dhyan dena chahiye — practical_guidance
Final line: confidence_explanation — exact from JSON.
""".strip()
    else:
        structure = """
STRUCTURE (default — 7 sections with headers listed in HEALTH_NARRATOR_RULES):
Follow ENGINE_JSON field order. Use ONLY lists provided — do not add factors.
Final line MUST be confidence_explanation from JSON verbatim (light Hinglish polish OK).
""".strip()

    return f"""
{HEALTH_NARRATOR_RULES}

{structure}

LENGTH: {lo}–{hi} words total. Topic: health.{rules}
""".strip()


def validate_health_narrator_output(text: str) -> str:
    """Strip banned hedging phrases from health narrator output."""
    if not text or not str(text).strip():
        return ""
    out = _BANNED_NARRATOR_PHRASES.sub("", str(text))
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\s+([,.;])", r"\1", out)
    return out.strip()

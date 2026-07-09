from __future__ import annotations

import re

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult

_TOXIC_SIGNAL_KEYS = [
    "Mars on 7th",
    "Saturn on 7th",
    "nodes on 7th",
    "Ketu influence on 7th",
    "Moon under Saturn/Rahu",
    "Moon in 8th",
    "Venus-Mars conjunction",
    "obsession, pull, loyalty blur",
    "hidden ties",
    "parallel attention",
    "dual sign under affliction",
    "Venus under nodal pull",
    "12th lord in 7th",
    "12th lord in 5th",
]

_ABUSE_Q = re.compile(r"(?ix)\b(abuse|abusive|violence|maar|peet|hit|hurt)\b")
_CONTROL_Q = re.compile(r"(?ix)\b(control|controlling|possessive|gaslight|manipulat)\b")
_TOXIC_Q = re.compile(r"(?ix)\b(toxic|red\s*flag|unhealthy|toxicity)\b")


def _toxicity_intent(question: str) -> str:
    q = question or ""
    if _ABUSE_Q.search(q):
        return "abuse_risk"
    if _CONTROL_Q.search(q):
        return "control_pattern"
    if _TOXIC_Q.search(q):
        return "toxic_dynamic"
    return "general_toxicity"


def _toxicity_level(sig, signals: list[str], *, abuse_asked: bool = False) -> str:
    n = len(signals)
    w = int(sig.affliction_weight or 0)

    if abuse_asked and (sig.mars_on_7th or n >= 2):
        return "high"
    if sig.emotional_instability and (sig.mars_on_7th or sig.rahu_on_7th_axis):
        return "high"
    if n >= 4 or w >= 36 or sig.venus_mars_conjunct_tight:
        return "high"
    if n >= 2 or w >= 22 or sig.moon_rahu_afflicted:
        return "moderate"
    if n >= 1 or w >= 14:
        return "watch"
    return "low"


def _toxicity_verdict(level: str, intent: str) -> str:
    topic = {
        "abuse_risk": "Toxicity/abuse risk",
        "control_pattern": "Control/manipulation pattern",
        "toxic_dynamic": "Toxic relationship dynamic",
        "general_toxicity": "Toxicity/red-flag pattern",
    }.get(intent, "Toxicity pattern")
    tone = {
        "low": f"{topic}: low-moderate — awareness and boundaries prevent escalation",
        "watch": f"{topic}: watch zone — repeated friction needs calm boundaries",
        "moderate": f"{topic}: moderate — control, jealousy or harsh cycles need direct limits",
        "high": f"{topic}: high — safety, space and support matter; do not normalize harm",
    }
    return tone.get(level, tone["moderate"])


def run_toxicity(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)
    intent = _toxicity_intent(question)
    signals = pick_notes(sig, _TOXIC_SIGNAL_KEYS, limit=6)
    level = _toxicity_level(sig, signals, abuse_asked=(intent == "abuse_risk"))
    verdict = _toxicity_verdict(level, intent)

    evidence: list[str] = []
    for line in signals[:5]:
        evidence.append(f"Toxicity signal: {line}")
    if sig.emotional_instability:
        evidence.append("Emotional volatility pattern — reactions can spike under stress.")
    if sig.rahu_on_7th_axis:
        evidence.append("Unpredictable pull pattern — boundaries and clarity reduce chaos.")
    if not evidence:
        evidence = ["No dominant toxicity driver — still use boundaries and honest talk."]

    summary = [
        "Answer toxicity/red-flag questions with calm direct voice — no victim-blaming.",
        "If abuse risk: prioritize safety, boundaries, and support — not astrology excuses.",
    ]
    if level in ("moderate", "high"):
        summary.append("Name the pattern (control/jealousy/hidden stress) + one boundary action.")

    return EngineResult(
        archetype="toxicity",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 60,
        answer_plan="2–3 sentences: toxicity level → 1–2 reasons → boundary/safety line.",
        summary=summary,
        evidence=evidence[:8],
        ignore=["timing dates/windows", "accusatory blame", "trivializing abuse"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "toxicity",
            "question_intent": intent,
            "toxicity_level": level,
            "emotional_instability": bool(sig.emotional_instability),
            "affliction_weight": int(sig.affliction_weight or 0),
        },
    )

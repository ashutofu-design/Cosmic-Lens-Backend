from __future__ import annotations

import re

from vedic.love_reality.scoring_core import KundliReader, risk_band_high_is_good

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult

_FRICTION_KEYS = [
    "Saturn on 7th",
    "Mars on 7th",
    "Moon under Saturn/Rahu",
    "Mercury debilitated",
    "nodes on 7th",
    "7th lord debilitated",
]
_SUPPORT_KEYS = [
    "5th lord strong",
    "Saturn-Moon link",
]

_SILENCE_Q = re.compile(r"(?ix)\b(silent|silence|khamoshi|baat\s*nahi|not\s*talking|ignore)\b")
_MISUNDERSTAND_Q = re.compile(r"(?ix)\b(misunderstand|galatfehmi|samajh\s*nahi)\b")
_ARGUMENT_Q = re.compile(r"(?ix)\b(argument|jhagda|ladai|fight|conflict)\b")


def _communication_intent(question: str) -> str:
    q = question or ""
    if _SILENCE_Q.search(q):
        return "silence"
    if _MISUNDERSTAND_Q.search(q):
        return "misunderstanding"
    if _ARGUMENT_Q.search(q):
        return "arguments"
    return "general_communication"


def _communication_level(sig, friction: list[str]) -> str:
    w = int(sig.affliction_weight or 0)
    n = len(friction)
    score = max(0, min(100, 100 - int(round(w * 1.15))))
    band = risk_band_high_is_good(score)
    if band in ("high", "very high") or n >= 3 or w >= 32:
        return "strained"
    if n >= 2 or w >= 20 or sig.mars_on_7th:
        return "mixed"
    if n >= 1 or w >= 12:
        return "moderate"
    return "clear"


def _communication_verdict(intent: str, level: str) -> str:
    topic = {
        "silence": "Communication / silence",
        "misunderstanding": "Understanding / misunderstandings",
        "arguments": "Arguments / conflict talk",
        "general_communication": "Relationship communication",
    }.get(intent, "Communication")
    tone = {
        "clear": f"{topic}: generally clear — honest calm talk keeps bond strong",
        "moderate": f"{topic}: workable — patience and listening bridge small gaps",
        "mixed": f"{topic}: mixed — talk hota hai par tone ya timing friction create karti hai",
        "strained": f"{topic}: strained — ego, silence ya harsh words repair habit maangte hain",
    }
    return tone.get(level, tone["mixed"])


def run_communication(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    from .general_mr import _synthesize_communication

    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    sig = build_person_signals(kundli)
    intent = _communication_intent(question)
    friction = pick_notes(sig, _FRICTION_KEYS, limit=4)
    support = pick_notes(sig, _SUPPORT_KEYS, limit=2)
    level = _communication_level(sig, friction)
    verdict = _communication_verdict(intent, level)

    evidence = _synthesize_communication(kundli, sig)
    merc = r.planet("Mercury") or {}
    if merc.get("house"):
        evidence.append(
            f"Mercury in house {merc.get('house')} — how ideas and words flow in the bond."
        )
    if support:
        evidence.insert(0, f"Talk support: {support[0]}")
    for line in friction[:2]:
        evidence.append(f"Talk friction: {line}")
    if not evidence:
        evidence = ["Communication looks balanced — clear respectful talk is the main habit."]

    return EngineResult(
        archetype="communication",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 60,
        answer_plan="2–3 sentences: communication quality → 1–2 reasons → one talk habit.",
        summary=[
            "Answer communication/understanding directly — confident pattern voice.",
            "Suggest calm talk, listening, and pause-before-react — not blame.",
        ],
        evidence=evidence[:8],
        ignore=["timing dates/windows", "breakup unless asked", "spouse profession"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "communication",
            "question_intent": intent,
            "communication_level": level,
            "affliction_weight": int(sig.affliction_weight or 0),
        },
    )

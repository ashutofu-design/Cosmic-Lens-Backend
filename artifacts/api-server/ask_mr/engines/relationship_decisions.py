from __future__ import annotations

import re

from vedic.love_reality.scoring_core import risk_band_high_is_good

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult

_STAY_SUPPORT_KEYS = [
    "5th lord strong",
    "emotional reopening",
    "Saturn as 7th lord in 7th",
    "Moon-Moon supportive",
]
_LEAVE_PRESSURE_KEYS = [
    "Saturn on 7th",
    "Mars on 7th",
    "7th lord in dusthana",
    "7th lord debilitated",
    "separation theme",
    "nodes on 7th",
    "hidden ties",
    "parallel attention",
    "Venus in dusthana",
    "Moon under Saturn/Rahu",
]

_STAY_Q = re.compile(r"(?ix)\b(stay|continue|nibha|try\s+again|ek\s+aur\s+mauka|second\s+chance)\b")
_LEAVE_Q = re.compile(r"(?ix)\b(leave|chhod|move\s+on|break|alag|end\s+it|khatam)\b")
_SUITABILITY_Q = re.compile(r"(?ix)\b(sahi\s+hai|theek\s+hai|right\s+for\s+me|mere\s+liye|should\s+i)\b")


def _decision_intent(question: str) -> str:
    q = question or ""
    if _SUITABILITY_Q.search(q):
        return "suitability_decision"
    if _LEAVE_Q.search(q) and not _STAY_Q.search(q):
        return "leave_consideration"
    if _STAY_Q.search(q):
        return "stay_consideration"
    return "general_decision"


def _decision_posture(sig, support: list[str], pressure: list[str]) -> str:
    w = int(sig.affliction_weight or 0)
    score = max(0, min(100, 100 - int(round(w * 1.2))))
    band = risk_band_high_is_good(score)
    s, p = len(support), len(pressure)

    if getattr(sig, "third_person_risk", False) or getattr(sig, "loyalty_risk_high", False):
        return "pause_and_clarify"
    if band in ("high", "very high") or p >= 3 or w >= 36:
        return "caution_leave"
    if p >= 2 and s == 0:
        return "caution_leave"
    if s >= 2 and p <= 1 and getattr(sig, "reconnection_yoga", False):
        return "lean_stay"
    if p >= 2 or w >= 24:
        return "mixed_weigh"
    if s >= 1 and p <= 1:
        return "lean_stay"
    return "mixed_weigh"


def _decision_verdict(posture: str, intent: str) -> str:
    labels = {
        "lean_stay": "Decision: lean stay/continue — repair and honest talk can work",
        "mixed_weigh": "Decision: mixed — pros and cons balance; clarity before big step",
        "caution_leave": "Decision: caution — friction heavy; boundaries and self-respect first",
        "pause_and_clarify": "Decision: pause and clarify — trust/intent check before stay or leave",
    }
    base = labels.get(posture, labels["mixed_weigh"])
    if intent == "suitability_decision":
        return base.replace("Decision:", "Overall suitability decision:")
    if intent == "leave_consideration":
        return base.replace("Decision:", "Leave/move-on decision:")
    if intent == "stay_consideration":
        return base.replace("Decision:", "Stay/continue decision:")
    return base


def run_relationship_decisions(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)
    intent = _decision_intent(question)
    support = pick_notes(sig, _STAY_SUPPORT_KEYS, limit=3)
    pressure = pick_notes(sig, _LEAVE_PRESSURE_KEYS, limit=5)
    posture = _decision_posture(sig, support, pressure)
    verdict = _decision_verdict(posture, intent)

    evidence: list[str] = []
    for line in support[:2]:
        evidence.append(f"Stay/support factor: {line}")
    for line in pressure[:3]:
        evidence.append(f"Pressure factor: {line}")
    if getattr(sig, "reconnection_yoga", False):
        evidence.insert(0, "Reconnection yoga present — second chance possible with effort.")
    if getattr(sig, "separation_yoga", False):
        evidence.append("Separation theme — weigh self-respect and repeated friction.")
    if not evidence:
        evidence = ["Decision factors balanced — honest self-check and clear talk decide best path."]

    return EngineResult(
        archetype="relationship_decisions",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 65,
        answer_plan="2–3 sentences: stay/leave lean → 1–2 reasons → one decision habit.",
        summary=[
            "Answer stay/leave/suitability decision — supportive but not preachy.",
            "Never command breakup; give chart-weighted lean + clarity step.",
        ],
        evidence=evidence[:8],
        ignore=["timing dates/windows", "marriage date", "accusatory language"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "relationship_decisions",
            "question_intent": intent,
            "decision_posture": posture,
            "affliction_weight": int(sig.affliction_weight or 0),
        },
    )

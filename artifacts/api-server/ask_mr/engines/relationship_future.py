from __future__ import annotations

import re

from vedic.love_reality.scoring_core import KundliReader, risk_band_high_is_good

from ._lordship import lordship_clause
from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult

_GROWTH_KEYS = [
    "5th lord strong",
    "emotional reopening",
    "Saturn as 7th lord in 7th",
    "Moon-Moon supportive",
]
_FRICTION_KEYS = [
    "Saturn on 7th",
    "Mars on 7th",
    "7th lord in dusthana",
    "7th lord debilitated",
    "separation theme",
    "nodes on 7th",
    "Moon under Saturn/Rahu",
]

_OUTLOOK_Q = re.compile(r"(?ix)\b(grow|badhega|strong|mazboot|sustain|tik\s*pa)\b")
_CHALLENGE_OUTLOOK_Q = re.compile(r"(?ix)\b(weak|kamzor|khatam|end|kharab)\b")


def _future_intent(question: str) -> str:
    q = question or ""
    if _CHALLENGE_OUTLOOK_Q.search(q):
        return "caution_outlook"
    if _OUTLOOK_Q.search(q):
        return "growth_outlook"
    return "general_future"


def _future_outlook(sig, growth: list[str], friction: list[str]) -> str:
    w = int(sig.affliction_weight or 0)
    score = max(0, min(100, 100 - int(round(w * 1.1))))
    band = risk_band_high_is_good(score)
    g, f = len(growth), len(friction)

    if getattr(sig, "reconnection_yoga", False) and f <= 1 and band in ("low", "medium"):
        return "promising"
    if band == "low" and f >= 2:
        return "cautious"
    if band in ("high", "very high") or f >= 3 or w >= 34:
        return "strained"
    if f >= 2 or w >= 22:
        return "mixed"
    if g >= 1 and f <= 1:
        return "steady"
    return "moderate"


def _future_verdict(outlook: str, intent: str) -> str:
    labels = {
        "promising": "Relationship future: promising — bond can deepen with steady care and respect",
        "steady": "Relationship future: steady growth possible — routine trust and talk anchor it",
        "moderate": "Relationship future: moderate — ups and downs, effort decides direction",
        "mixed": "Relationship future: mixed — closeness possible par friction points ko address karna padega",
        "cautious": "Relationship future: cautious — patience, boundaries aur repair habits zaroori",
        "strained": "Relationship future: strained pattern — without honest work bond weak ho sakta hai",
    }
    base = labels.get(outlook, labels["moderate"])
    if intent == "caution_outlook":
        return base.replace("Relationship future:", "Relationship future (risk angle):")
    return base


def _synthesize_future(kundli: dict, sig) -> list[str]:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    lines: list[str] = []

    jup = r.planet("Jupiter") or {}
    if jup.get("house") in (1, 4, 7, 9, 11):
        lines.append(
            f"Jupiter in house {jup.get('house')} — long-term faith and growth support the bond"
            f"{lordship_clause(r, 'Jupiter')}."
        )
    ven = r.planet("Venus") or {}
    if ven.get("house") in (1, 4, 7, 9, 11):
        lines.append(
            f"Venus in house {ven.get('house')} — warmth and harmony help future closeness"
            f"{lordship_clause(r, 'Venus')}."
        )
    if getattr(sig, "reconnection_yoga", False):
        lines.append("Reconnection capacity present — repair and emotional reopening are possible.")
    if getattr(sig, "separation_yoga", False):
        lines.append("Separation theme visible — future needs deliberate repair and boundaries.")
    lord7 = r.house_lord(7)
    p7l = r.planet(lord7) if lord7 else None
    if lord7 and p7l:
        lines.append(
            f"7th lord {lord7} in house {p7l.get('house')} — partnership tone shapes the long arc."
        )
    return lines[:5]


def run_relationship_future(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)
    intent = _future_intent(question)
    growth = pick_notes(sig, _GROWTH_KEYS, limit=3)
    friction = pick_notes(sig, _FRICTION_KEYS, limit=4)
    outlook = _future_outlook(sig, growth, friction)
    verdict = _future_verdict(outlook, intent)

    evidence = _synthesize_future(kundli, sig)
    for line in growth[:2]:
        if line not in " ".join(evidence):
            evidence.insert(0, f"Growth marker: {line}")
    for line in friction[:2]:
        evidence.append(f"Future friction: {line}")
    if not evidence:
        evidence = ["Future outlook balanced — daily respect and communication steer the bond."]

    return EngineResult(
        archetype="relationship_future",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 65,
        answer_plan="2–3 sentences: future outlook → 1–2 chart reasons → one growth habit.",
        summary=[
            "Answer NON-TIMING future outlook — no kab/when dates.",
            "Confident pattern voice — state direction (grow/mixed/strained) clearly.",
        ],
        evidence=evidence[:8],
        ignore=["timing dates/windows", "exact month/year predictions", "marriage date"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "relationship_future",
            "question_intent": intent,
            "future_outlook": outlook,
            "affliction_weight": int(sig.affliction_weight or 0),
        },
    )

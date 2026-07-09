from __future__ import annotations

import re

from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult

_REMEDY_MAP: list[tuple[str, str, str]] = [
    ("Saturn on 7th", "Saturday", "Om Sham Shanaishcharaya Namah — 108×; mustard oil daan; patience in talk"),
    ("Mars on 7th", "Tuesday", "Hanuman Chalisa daily; avoid harsh speech; cool-down before arguments"),
    ("Moon under Saturn/Rahu", "Monday", "Om Chandraya Namah — 108×; white items daan; emotional check-ins"),
    ("Venus debilitated", "Friday", "Om Shukraya Namah — 108×; white sweets daan; kindness in affection"),
    ("Venus in dusthana", "Friday", "Lakshmi/Kamala stuti; rose or white flowers Friday; gentle romance habits"),
    ("nodes on 7th", "Saturday", "Maha Mrityunjaya or Shiva mantra — 11×; steady routine reduces chaos"),
    ("7th lord debilitated", "Friday", "Partner-axis prayer Friday evening; honest vows + small seva together"),
    ("hidden ties", "Thursday", "Guru mantra — 108×; transparency journal; cut parallel attention habits"),
    ("5th lord strong", "Thursday", "Thanksgiving prayer to Jupiter; nurture romance with simple weekly dates"),
]

_LOVE_REMEDY_Q = re.compile(r"(?ix)\b(upay|upaay|remedy|remedies|mantra|totka|puja|parikrama)\b")


def _remedy_intent(question: str) -> str:
    q = question or ""
    if re.search(r"(?ix)\b(pyar|pyaar|love|rishta|relationship)\b", q):
        return "love_relationship_remedy"
    if re.search(r"(?ix)\b(shaadi|marriage|vivah|partner)\b", q):
        return "marriage_relationship_remedy"
    return "general_relationship_remedy"


def _pick_remedies(sig) -> list[str]:
    lines: list[str] = []
    friction = pick_notes(sig, [key for key, _, _ in _REMEDY_MAP], limit=6)
    seen: set[str] = set()
    for f in friction:
        if len(lines) >= 4:
            break
        for key, day, remedy in _REMEDY_MAP:
            if key.lower() in f.lower():
                line = f"{day}: {remedy} (for {key})."
                if line not in seen:
                    seen.add(line)
                    lines.append(line)
                break
    if getattr(sig, "reconnection_yoga", False) and len(lines) < 4:
        lines.append("Thursday: Om Gurave Namah — 108×; weekly honest talk rebuilds closeness.")
    if not lines:
        lines = [
            "Friday: Om Shukraya Namah — 108×; small kindness rituals strengthen love bond.",
            "Daily: calm communication habit — remedy without talk rarely sustains.",
        ]
    return lines[:4]


def run_relationship_remedies(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)
    intent = _remedy_intent(question)
    remedies = _pick_remedies(sig)
    verdict = (
        "Relationship remedy: chart friction ke hisaab se simple upay — "
        "mantra + day + one daily habit; consistency matters"
    )

    evidence = remedies[:]
    friction = pick_notes(sig, [key for key, _, _ in _REMEDY_MAP], limit=3)
    for line in friction[:2]:
        evidence.append(f"Target pattern: {line}")

    return EngineResult(
        archetype="relationship_remedies",
        verdict=verdict,
        confidence="medium",
        word_budget=100 if wants_explain else 70,
        answer_plan="2–3 short remedy lines tied to chart friction + one behavior habit.",
        summary=[
            "Give practical classical-lite remedies — mantra, day, daan/habit.",
            "Tie each upay to the friction it addresses; no fabricated gemstone weights.",
        ],
        evidence=evidence[:6],
        ignore=["timing predictions", "fake gemstone prescriptions", "guaranteed miracles"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "relationship_remedies",
            "question_intent": intent,
            "remedy_count": len(remedies),
            "affliction_weight": int(sig.affliction_weight or 0),
        },
    )

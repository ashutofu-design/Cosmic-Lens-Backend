from __future__ import annotations

import re

from ask_career.types import EngineResult
from ._career_base import house_axis, inclination_evidence, load_inclination, reader

_REL_RX = [
    (re.compile(r"(?ix)\b(boss|manager|supervisor|reporting)\b"), "boss"),
    (re.compile(r"(?ix)\b(colleague|coworker|team\s*mate|office\s*politics)\b"), "colleague"),
    (re.compile(r"(?ix)\b(job\s*satisfaction|kaam\s*pasand|enjoy\s*work)\b"), "satisfaction"),
    (re.compile(r"(?ix)\b(workplace|office\s*environment)\b"), "workplace"),
]


def _rel(q: str) -> str:
    for rx, name in _REL_RX:
        if rx.search(q or ""):
            return name
    return "workplace"


def run_workplace_relations(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    r = reader(kundli)
    focus = _rel(question or "")

    evidence = [
        house_axis(r, 6, "Workplace/service axis (6th house)"),
        house_axis(r, 10, "Authority/career axis (10th house)"),
    ]
    evidence.extend(inclination_evidence(inc, limit=3))

    sun = r.planet("Sun") or {}
    sat = r.planet("Saturn") or {}
    if focus == "boss":
        evidence.append(
            f"Boss dynamic: Sun (authority) house {sun.get('house')} + Saturn (senior pressure) house {sat.get('house')} — "
            "how you handle hierarchy and senior expectations."
        )
    elif focus == "colleague":
        evidence.append(
            "Colleague dynamic: 6th house daily-work tone + Mercury communication score — teamwork vs office friction pattern."
        )
    elif focus == "satisfaction":
        aff = float(inc.get("affliction_load") or 0)
        evidence.append(
            f"Job satisfaction: career mode {inc.get('career_mode')} + affliction load {aff} — "
            "fulfillment higher when role matches dominant inclination path."
        )
    else:
        evidence.append("Workplace environment: 6H-10H link sets daily office culture fit.")

    verdict = f"Workplace ({focus}): read from 6th-10th axis + career-mode alignment"

    return EngineResult(
        archetype="workplace_relations",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 60,
        answer_plan="Direct workplace answer → 6H/10H evidence → one habit tip.",
        summary=[f"QUESTION FOCUS: {focus} at work."],
        evidence=evidence[:8],
        ignore=["timing", "marriage"],
        checks={"slice_type": "career_engine_v1", "archetype": "workplace_relations", "focus": focus},
    )

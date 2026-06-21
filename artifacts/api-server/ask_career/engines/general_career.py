from __future__ import annotations

import re

from ask_career.types import EngineResult
from ._career_base import career_snapshot, load_inclination, trait_line

_PERSONALITY_OPEN_RX = re.compile(
    r"(?ix)\b("
    r"practical|analytical|intuitive|ambitious|competitive|responsibility|persuasion|"
    r"execution|detail[\s-]?oriented|big[\s-]?picture|multitasking|specialization|"
    r"office\s+work|field\s+work|backend\s+work|research\s+work|"
    r"core\s+identity|professional\s+banne|naturally|kis\s+type\s+ke\s+work"
    r")\b"
)


def run_general_career(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    evidence = career_snapshot(kundli, inc)
    q = question or ""

    if _PERSONALITY_OPEN_RX.search(q):
        psych = inc.get("psychology") or {}
        ranked = sorted(psych.items(), key=lambda x: -x[1])
        if ranked:
            top = ranked[0]
            evidence.append(
                f"Dominant career psychology: {top[0].replace('_', ' ')} ({top[1]}/100) — shapes natural work style."
            )
        if re.search(r"(?ix)\b(practical|analytical|intuitive)\b", q):
            evidence.append(
                trait_line(
                    inc,
                    "adaptability",
                    high="can balance practical and intuitive sides",
                    low="one mode dominates — pick roles that match your stronger side",
                )
            )
        if re.search(r"(?ix)\b(ambitious|competitive)\b", q):
            evidence.append(
                trait_line(
                    inc,
                    "risk_appetite",
                    high="drive and competitive edge visible",
                    low="steady pace suits — build ambition gradually",
                )
            )
        if inc.get("career_mode"):
            evidence.append(f"Career mode synthesis: {inc.get('career_mode')} — overall professional path tone.")

    return EngineResult(
        archetype="general_career",
        verdict="Open career question — answer from relevant D1/D10 career factors only",
        confidence="medium",
        word_budget=75 if wants_explain else 60,
        answer_plan="Answer exact question from relevant career chart factors → 1–2 reasons.",
        summary=[
            "OPEN career question — pick ONLY factors relevant to what was asked.",
            "Confident pattern voice — no shayad/ho sakta hai.",
            "No planet/house jargon in user reply.",
        ],
        evidence=evidence[:12],
        ignore=["timing dates", "marriage", "exact job title guarantee"],
        checks={
            "slice_type": "career_engine_v1",
            "archetype": "general_career",
            "open_chart_qa": True,
        },
    )

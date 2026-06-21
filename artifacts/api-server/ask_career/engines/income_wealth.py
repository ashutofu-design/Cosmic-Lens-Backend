from __future__ import annotations

import re

from ask_career.types import EngineResult
from ._career_base import house_axis, inclination_evidence, load_inclination, reader

_INCOME_RX = [
    (re.compile(r"(?ix)\b(high[\s-]?income|zyada\s*paisa|rich\s*profession)\b"), "high_income"),
    (re.compile(r"(?ix)\b(passive\s*income)\b"), "passive"),
    (re.compile(r"(?ix)\b(multiple\s*income|extra\s*income\s*source)\b"), "multiple"),
    (re.compile(r"(?ix)\b(investment|invest\s*karna)\b"), "investment"),
    (re.compile(r"(?ix)\b(commission[\s-]?based)\b"), "commission"),
    (re.compile(r"(?ix)\b(freelanc\w*)\b"), "freelance"),
    (re.compile(r"(?ix)\b(salary[\s-]?based|fixed\s*salary)\b"), "salary"),
    (re.compile(r"(?ix)\b(paisa\s*kama|wealth\s*creation|earn\s*money)\b"), "wealth"),
    (re.compile(r"(?ix)\b(entrepreneur.*paisa|business\s*se\s*zyada)\b"), "biz_income"),
]


def _income_focus(q: str) -> str:
    for rx, name in _INCOME_RX:
        if rx.search(q or ""):
            return name
    return "wealth"


def run_income_wealth(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    r = reader(kundli)
    focus = _income_focus(question or "")

    evidence = [
        house_axis(r, 2, "Income axis (2nd house)"),
        house_axis(r, 11, "Gains/profit axis (11th house)"),
    ]
    evidence.extend(inclination_evidence(inc, limit=4))

    biz = int(inc.get("business_pct") or 50)
    job = int(inc.get("job_pct") or 50)
    comm = int(inc.get("commercial_score") or 0)

    notes = {
        "high_income": f"High-income potential: commercial score {comm}/100 + strong 11th-house gains theme.",
        "passive": "Passive income: 11th lord + Venus/Jupiter wealth karakas — royalties/rent/investments over pure salary.",
        "multiple": "Multiple income streams: hybrid career mode + commercial/freelance scores support diversified earning.",
        "investment": "Investment focus: 2nd/11th axis + Jupiter prosperity — wealth grows via assets not only salary.",
        "commission": "Commission-based: Venus-Mercury commercial + sales/marketing subtype suits variable pay models.",
        "freelance": f"Freelancing income: freelance score {inc.get('freelance_score')}/100 — project-based earning pattern.",
        "salary": f"Salary career: job tilt ~{job}% — stable monthly income path primary.",
        "wealth": "Wealth creation: blend 2H income discipline + 11H gains + job/business split for long-term money building.",
        "biz_income": f"Business income tilt: business ~{biz}% — entrepreneurship can outpace salary if execution score supports.",
    }
    evidence.append(notes.get(focus, notes["wealth"]))

    verdict = f"Career wealth ({focus.replace('_', ' ')}): pattern from 2H/11H + inclination money axis"

    return EngineResult(
        archetype="income_wealth",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 70,
        answer_plan="Direct income approach answer → 2 house/inclination reasons → no exact amount.",
        summary=["Do NOT quote exact salary/income figures.", f"QUESTION FOCUS: {focus}."],
        evidence=evidence[:8],
        ignore=["timing", "exact rupee amount", "lottery", "stock tips"],
        checks={"slice_type": "career_engine_v1", "archetype": "income_wealth", "focus": focus},
    )

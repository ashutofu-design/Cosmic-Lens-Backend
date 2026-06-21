from __future__ import annotations

import re

from ask_career.types import EngineResult
from ._career_base import inclination_evidence, load_inclination, trait_line

_SKILL_RX = [
    (re.compile(r"(?ix)\b(strength|strong\s*side|biggest\s*strength|sabse\s+badi\s+strength)\b"), "strength"),
    (re.compile(r"(?ix)\b(weakness|weak\s*side|biggest\s*weakness|sabse\s+badi\s+weakness|kamzor)\b"), "weakness"),
    (re.compile(r"(?ix)\b(skill\s+ko\s+avoid|avoid\s+karna)\b"), "avoid"),
    (re.compile(r"(?ix)\b(skill\s+par\s+focus|focus\s+karna\s+chahiye|valuable\s+skill)\b"), "develop"),
    (re.compile(r"(?ix)\b(hidden\s+talents?|natural\s+talents?)\b"), "natural"),
    (re.compile(r"(?ix)\b(develop|improve|seekhni|seekhna|skill\s*develop)\b"), "develop"),
    (re.compile(r"(?ix)\b(communication|public\s*speaking|problem\s+solving|decision\s+making)\b"), "communication"),
    (re.compile(r"(?ix)\b(technical\s+role|technical)\b"), "technical"),
    (re.compile(r"(?ix)\b(management)\b"), "management"),
    (re.compile(r"(?ix)\b(sales\s*skill)\b"), "communication"),
    (re.compile(r"(?ix)\b(foreign\s*language|language\s*seekh)\b"), "communication"),
]


def _focus(q: str) -> str:
    for rx, name in _SKILL_RX:
        if rx.search(q or ""):
            return name
    return "strength"


def run_strengths_skills(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    focus = _focus(question or "")
    psych = inc.get("psychology") or {}

    ranked = sorted(psych.items(), key=lambda x: -x[1])
    top = ranked[0] if ranked else ("communication", 50)
    low = ranked[-1] if ranked else ("discipline", 50)

    evidence = inclination_evidence(inc, limit=4)
    if focus in ("strength", "natural"):
        evidence.append(f"Biggest strength: {top[0].replace('_', ' ')} ({top[1]}/100) — lean career choices here.")
        evidence.append(trait_line(inc, top[0], high="natural strong zone", low="developing zone"))
        verdict = f"Career strength: {top[0].replace('_', ' ')} — your natural strong zone"
    elif focus == "weakness":
        evidence.append(f"Growth edge: {low[0].replace('_', ' ')} ({low[1]}/100) — build skill/habit here.")
        evidence.append("Weakness is workable — chart shows where deliberate practice helps most.")
        verdict = f"Career growth edge: {low[0].replace('_', ' ')} — improve with focused effort"
    elif focus == "avoid":
        evidence.append(
            f"Skill to de-prioritise: {low[0].replace('_', ' ')} ({low[1]}/100) — not your natural strong zone."
        )
        evidence.append(
            f"Better to build on {top[0].replace('_', ' ')} ({top[1]}/100) where chart support is stronger."
        )
        verdict = f"Skill avoid zone: {low[0].replace('_', ' ')} — lean away from over-investing here"
    else:
        skill = focus if focus in psych else "communication"
        if focus == "develop":
            evidence.append(
                f"Skill development priority: strengthen {low[0].replace('_', ' ')} "
                f"({low[1]}/100) and build on {top[0].replace('_', ' ')} ({top[1]}/100)."
            )
        elif focus == "technical":
            evidence.append(
                "Technical expertise focus: Mercury/engineering subtype + analytical trait scores "
                "support building hard skills in your chart's dominant field."
            )
        elif focus == "management":
            evidence.append(
                "Management skill focus: leadership/structure trait scores show whether to build "
                "people-management skills for your next career step."
            )
        else:
            evidence.append(
                trait_line(
                    inc,
                    skill,
                    high="already strong — refine advanced level",
                    low="worth developing — high ROI skill",
                )
            )
        verdict = f"Skill focus ({focus.replace('_', ' ')}): chart-based development priority"

    return EngineResult(
        archetype="strengths_skills",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 65,
        answer_plan="Direct strength/weakness/skill answer → 2 trait evidence lines → one action tip.",
        summary=[f"QUESTION FOCUS: {focus} — use psychology trait scores only."],
        evidence=evidence[:8],
        ignore=["timing", "marriage", "exact course name"],
        checks={"slice_type": "career_engine_v1", "archetype": "strengths_skills", "focus": focus},
    )

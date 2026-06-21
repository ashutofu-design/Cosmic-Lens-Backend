from __future__ import annotations

import re

from ask_career.types import EngineResult
from ._career_base import house_axis, inclination_evidence, load_inclination, reader


def run_education_career(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    r = reader(kundli)
    merc = r.planet("Mercury") or {}
    jup = r.planet("Jupiter") or {}

    evidence = [
        house_axis(r, 4, "Education/learning foundation (4th house)"),
        house_axis(r, 5, "Intellect/creative study axis (5th house)"),
        house_axis(r, 9, "Higher education/dharma study (9th house)"),
        f"Mercury (study/skill) in house {merc.get('house')} sign {merc.get('sign')}.",
        f"Jupiter (higher learning) in house {jup.get('house')} sign {jup.get('sign')}.",
    ]
    evidence.extend(inclination_evidence(inc, limit=3))
    if re.search(r"(?ix)\b(exam|study|degree|college|university)\b", question or ""):
        evidence.append("Education path: 4H-5H-9H link + Mercury/Jupiter show study field and higher-ed potential.")
    else:
        tags = (inc.get("commercial_subtypes") or []) + (inc.get("job_subtypes") or [])
        evidence.append(f"Skill/education direction aligned to career subtypes: {', '.join(tags[:3]) or inc.get('career_mode')}.")

    verdict = "Education/skills for career: 4H/5H/9H + Mercury/Jupiter + inclination subtypes"

    return EngineResult(
        archetype="education_career",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 65,
        answer_plan="Study field answer → education houses → link to career subtypes.",
        summary=["QUESTION FOCUS: education/skills for career — not school exam dates."],
        evidence=evidence[:8],
        ignore=["timing", "exact exam result"],
        checks={"slice_type": "career_engine_v1", "archetype": "education_career"},
    )

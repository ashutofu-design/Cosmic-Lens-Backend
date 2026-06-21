"""Career milestone questions — promotion, interview, job change, govt exam, side hustle."""
from __future__ import annotations

import re

from ask_career.types import EngineResult
from ._career_base import house_axis, inclination_evidence, load_inclination, reader, trait_line

_FOCUS_RX = [
    (re.compile(r"(?ix)\b(promotion|promote|tarakki|senior|growth\s*fast|career\s*growth)\b"), "promotion"),
    (re.compile(r"(?ix)\b(interview|selection|shortlist|recruiter|hr\s*round)\b"), "interview"),
    (re.compile(r"(?ix)\b(job\s*change|switch\s*job|naukri\s*badlo|company\s*change|career\s*switch)\b"), "job_change"),
    (re.compile(r"(?ix)\b(upsc|ias|ips|ssc|cgl|railway\s*exam|bank\s*exam|govt\s*exam|competitive\s*exam|civil\s*service|pcs|nda|cds)\b"), "govt_exam"),
    (re.compile(r"(?ix)\b(side\s*hustle|part\s*time|extra\s*income|side\s*income|dusra\s*kaam|second\s*job)\b"), "side_hustle"),
]


def _focus(q: str) -> str:
    for rx, name in _FOCUS_RX:
        if rx.search(q or ""):
            return name
    return "promotion"


def run_career_milestones(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    r = reader(kundli)
    focus = _focus(question or "")

    evidence = [
        house_axis(r, 10, "Career execution (10th house)"),
        house_axis(r, 11, "Gains/growth (11th house)"),
    ]
    evidence.extend(inclination_evidence(inc, limit=3, include_job_split=False))
    evidence.append(trait_line(inc, "discipline", high="supports steady progress", low="needs structured effort"))
    evidence.append(trait_line(inc, "communication", high="helps interviews and visibility", low="practice improves outcomes"))

    sun = r.planet("Sun") or {}
    jup = r.planet("Jupiter") or {}
    merc = r.planet("Mercury") or {}
    sat = r.planet("Saturn") or {}

    if focus == "promotion":
        evidence.append(
            f"Promotion signal: Sun authority house {sun.get('house')} + Saturn discipline house {sat.get('house')} — "
            "leadership visibility and consistency matter."
        )
        verdict = "Promotion/growth: chart supports upward movement when role matches career mode"
    elif focus == "interview":
        evidence.append(
            f"Interview signal: Mercury communication house {merc.get('house')} + Jupiter confidence house {jup.get('house')} — "
            "presentation and clarity are key."
        )
        verdict = "Interview/selection: communication + 10H strength indicate selection potential"
    elif focus == "job_change":
        evidence.append(
            f"Job-change signal: Rahu change appetite + 10L movement pattern — "
            f"career mode {inc.get('career_mode')} shows when switch aligns."
        )
        verdict = "Job change: chart supports switch when new role matches dominant inclination path"
    elif focus == "govt_exam":
        evidence.append(
            f"Govt exam signal: Sun-Saturn discipline + Jupiter learning house {jup.get('house')} — "
            "structured prep and persistence are decisive."
        )
        verdict = "Government/competitive exam: discipline + Jupiter-Mercury learning axis supports exam path"
    else:
        evidence.append(
            f"Side income signal: commercial score {inc.get('commercial_score')} + independence trait — "
            "extra income works best in chart-aligned freelance/commerce pockets."
        )
        verdict = "Side hustle/part-time income: viable when aligned with commercial/independent chart pockets"

    return EngineResult(
        archetype="career_milestones",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 70,
        answer_plan=f"Direct answer for {focus} → 10H/11H evidence → one practical note.",
        summary=[
            f"QUESTION FOCUS: {focus.replace('_', ' ')}.",
            "Answer the exact milestone asked — do NOT pivot to job vs business % split.",
        ],
        evidence=evidence[:8],
        ignore=["timing", "marriage", "spouse"],
        checks={"slice_type": "career_engine_v1", "archetype": "career_milestones", "focus": focus},
    )

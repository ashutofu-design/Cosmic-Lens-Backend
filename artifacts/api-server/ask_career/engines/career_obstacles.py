from __future__ import annotations

from ask_career.types import EngineResult
from ._career_base import inclination_evidence, load_inclination


def run_career_obstacles(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    aff = float(inc.get("affliction_load") or 0)
    stab = float(inc.get("stability_penalty") or 0)
    align = str(inc.get("d1_d10_alignment") or "")

    evidence = inclination_evidence(inc, limit=4)
    evidence.append(f"Affliction load {aff} — career friction/delay stress on path.")
    evidence.append(f"Stability penalty {stab} — how much ups-downs affect career continuity.")
    if align and align not in ("aligned", ""):
        evidence.append(f"D1-D10 alignment: {align} — inner nature vs execution chart may need bridging.")
    if aff >= 8:
        evidence.append("Obstacle theme: delays/setbacks possible — persistence and skill upgrades reduce impact.")
    else:
        evidence.append("Obstacle theme: moderate — routine career challenges, not dominant block pattern.")

    verdict = (
        "Career obstacles: elevated friction — patience + skill focus needed"
        if aff >= 8
        else "Career obstacles: manageable — steady effort keeps progress on track"
    )

    return EngineResult(
        archetype="career_obstacles",
        verdict=verdict,
        confidence="medium" if aff >= 8 else "high",
        word_budget=90 if wants_explain else 65,
        answer_plan="Direct obstacle level → affliction evidence → repair habit (skill/network).",
        summary=["Tone hopeful not doom.", "QUESTION FOCUS: career delays/obstacles/challenges."],
        evidence=evidence[:8],
        ignore=["timing dates", "job loss certainty"],
        checks={"slice_type": "career_engine_v1", "archetype": "career_obstacles", "affliction_load": aff},
    )

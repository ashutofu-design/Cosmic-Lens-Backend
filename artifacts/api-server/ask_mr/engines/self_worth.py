from __future__ import annotations

from vedic.love_reality.scoring_core import KundliReader

from ..types import EngineResult


def run_self_worth(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)

    moon = r.planet("Moon")
    venus = r.planet("Venus")
    saturn = r.planet("Saturn")

    fragile = 0
    evidence: list[str] = []

    if moon and r.dignity("Moon", r.sidx(moon["sign"])) <= -2:
        fragile += 2
        evidence.append("Moon debilitated — self-worth can dip under relationship stress.")
    if venus and r.dignity("Venus", r.sidx(venus["sign"])) <= -2:
        fragile += 1
        evidence.append("Venus debilitated — validation-seeking in love may rise under stress.")
    if moon and saturn and r.share_house("Moon", "Saturn"):
        fragile += 1
        evidence.append("Moon–Saturn link — self-criticism or duty can shrink confidence in love.")
    if venus and venus.get("house") in (6, 8, 12):
        fragile += 1
        evidence.append("Venus in challenging house — self-worth may tie too much to partner approval.")

    if fragile >= 3:
        verdict = "Self-worth in relationships: sensitive — boundaries and self-care help"
    elif fragile >= 1:
        verdict = "Self-worth in relationships: mixed — confidence fluctuates under stress"
    else:
        verdict = "Self-worth in relationships: relatively stable — keep mutual respect"

    if not evidence:
        evidence = ["No strong self-worth fragility driver; confidence looks manageable."]

    return EngineResult(
        archetype="self_worth",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 55,
        answer_plan="2–3 sentences: self-worth pattern → reason → empowering boundary advice.",
        summary=["Supportive tone; encourage self-respect, not dependency."],
        evidence=evidence[:6],
        ignore=["timing dates/windows", "partner profession"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "self_worth",
            "fragility_score": fragile,
        },
    )

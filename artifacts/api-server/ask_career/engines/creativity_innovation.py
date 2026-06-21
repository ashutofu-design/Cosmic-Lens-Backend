from __future__ import annotations

from ask_career.types import EngineResult
from ._career_base import inclination_evidence, load_inclination, reader, subtype_hits


def run_creativity_innovation(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    r = reader(kundli)
    ven = r.planet("Venus") or {}
    merc = r.planet("Mercury") or {}
    rahu = r.planet("Rahu") or {}

    evidence = inclination_evidence(inc, limit=4)
    evidence.append(
        f"Creative axis: Venus house {ven.get('house')} + Mercury house {merc.get('house')} — "
        "design/communication/creative expression in work."
    )
    comm_tags = subtype_hits(inc, "comm")
    if comm_tags:
        evidence.append(f"Creative/commercial subtypes: {', '.join(comm_tags)}.")
    if rahu.get("house") in (3, 5, 10, 11):
        evidence.append(
            f"Rahu in house {rahu.get('house')} — innovation/unconventional creative or tech ideas."
        )
    comm = int(inc.get("commercial_score") or 0)
    evidence.append(f"Commercial/creative score {comm}/100 — monetizable creative skill potential.")

    verdict = "Creative/innovation career: Venus-Mercury + commercial subtypes + Rahu innovation tone"

    return EngineResult(
        archetype="creativity_innovation",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 65,
        answer_plan="Direct creative success answer → 2 creative-axis reasons → portfolio habit.",
        summary=["QUESTION FOCUS: creative/innovative career path."],
        evidence=evidence[:8],
        ignore=["timing", "marriage"],
        checks={"slice_type": "career_engine_v1", "archetype": "creativity_innovation"},
    )

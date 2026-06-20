from __future__ import annotations

from ._person_signals import build_person_signals
from ..types import EngineResult


def run_chemistry(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)

    # Simple deterministic read
    if sig.venus_mars_conjunct_tight:
        level = "very strong"
    elif sig.venus_mars_conjunct:
        level = "strong"
    elif sig.venus_afflicted or sig.venus_debil:
        level = "mixed"
    else:
        level = "moderate"

    verdict = f"Chemistry/attraction: {level}"

    evidence: list[str] = []
    for key in (
        "Venus-Mars conjunction",
        "Venus in dusthana",
        "Venus debilitated",
        "Venus under nodal pull",
        "Moon under Saturn/Rahu",
    ):
        for n in sig.notes or []:
            if len(evidence) >= 6:
                break
            if key.lower() in n.lower() and n not in evidence:
                evidence.append(n.replace("You's ", "").replace("You: ", ""))

    if not evidence:
        evidence = ["No strong attraction driver triggered; chemistry looks normal/mixed."]

    return EngineResult(
        archetype="chemistry",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 55,
        answer_plan="2–3 short sentences: chemistry level → 1–2 reasons → soft advice (balance).",
        summary=[
            "Avoid over-promising; chemistry ≠ compatibility.",
        ],
        evidence=evidence,
        ignore=[
            "timing dates/windows",
            "spouse profession",
            "love-vs-arranged",
            "manglik (unless asked)",
        ],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "chemistry",
            "venus_mars_conjunct": bool(sig.venus_mars_conjunct),
            "venus_mars_tight": bool(sig.venus_mars_conjunct_tight),
            "venus_afflicted": bool(sig.venus_afflicted),
        },
    )


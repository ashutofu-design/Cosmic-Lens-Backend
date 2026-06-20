from __future__ import annotations

from ._person_signals import build_person_signals
from ..types import EngineResult


def run_patchup(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)

    # Deterministic: reconnection_yoga is our primary positive lever.
    if sig.reconnection_yoga and not sig.separation_yoga:
        level = "strong"
    elif sig.reconnection_yoga and sig.separation_yoga:
        level = "possible (needs effort)"
    elif sig.separation_yoga:
        level = "weak right now"
    else:
        level = "mixed"

    verdict = f"Patchup/return potential: {level}"

    evidence: list[str] = []
    for key in (
        "5th lord strong",
        "Saturn on 7th",
        "Mars on 7th",
        "Moon under Saturn/Rahu",
        "7th lord in dusthana",
    ):
        for n in sig.notes or []:
            if len(evidence) >= 6:
                break
            if key.lower() in n.lower() and n not in evidence:
                evidence.append(n.replace("You's ", "").replace("You: ", ""))

    if not evidence:
        evidence = ["Signals look mixed; patchup depends more on communication and repair habits."]

    return EngineResult(
        archetype="patchup",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 55,
        answer_plan="2–3 short sentences: patchup potential → 1–2 reasons → 1 practical step.",
        summary=[
            "Encourage repair behaviors; avoid definite timelines.",
        ],
        evidence=evidence,
        ignore=[
            "timing dates/windows",
            "spouse profession",
            "manglik (unless asked)",
        ],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "patchup",
            "reconnection_yoga": bool(sig.reconnection_yoga),
            "separation_yoga": bool(sig.separation_yoga),
        },
    )


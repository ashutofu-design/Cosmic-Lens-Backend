from __future__ import annotations

from ._person_signals import build_person_signals
from ..types import EngineResult


def _trust_level(sig) -> str:
    # Deterministic buckets; not "fate", just risk posture.
    if sig.third_person_risk or sig.venus_mars_conjunct_tight or sig.moon_in_8th:
        return "risky"
    if sig.loyalty_risk_high or sig.venus_mars_conjunct or sig.rahu_on_7th_axis:
        return "unstable"
    return "moderate"


def run_loyalty_trust(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    sig = build_person_signals(kundli)
    level = _trust_level(sig)

    verdict = {
        "moderate": "Trust/loyalty: mostly stable (but communicate clearly)",
        "unstable": "Trust/loyalty: mixed — clarity + boundaries needed",
        "risky": "Trust/loyalty: sensitive — assumptions se bachna hoga",
    }[level]

    evidence: list[str] = []
    # Pull engine-notes that already contain planet+meaning.
    for key in (
        "Venus-Mars conjunction",
        "12th lord in 7th",
        "12th lord in 5th",
        "nodes on 7th",
        "Moon in 8th",
        "Navamsa Moon debilitated",
        "Venus in dusthana",
        "hidden ties",
        "parallel attention",
        "obsession, pull, loyalty blur",
    ):
        for n in sig.notes or []:
            if len(evidence) >= 6:
                break
            if key.lower() in n.lower() and n not in evidence:
                evidence.append(n.replace("You's ", "").replace("You: ", ""))

    if not evidence:
        evidence = ["No strong trust-risk driver triggered; signals look normal/mixed."]

    summary = [
        "Answer loyalty/commitment level directly — confident pattern voice.",
        "NO shayad/ho sakta hai/lagta hai. Avoid accusations; focus on trust + boundaries.",
    ]

    return EngineResult(
        archetype="loyalty_trust",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 55,
        answer_plan="2–3 short sentences: direct trust posture → 1–2 reasons → practical next step.",
        summary=summary,
        evidence=evidence,
        ignore=[
            "timing dates/windows",
            "spouse profession",
            "love-vs-arranged",
            "manglik (unless asked)",
        ],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "loyalty_trust",
            "loyalty_risk_high": bool(sig.loyalty_risk_high),
            "third_person_risk": bool(sig.third_person_risk),
            "venus_mars_tight": bool(sig.venus_mars_conjunct_tight),
            "moon_in_8th": bool(sig.moon_in_8th),
            "rahu_on_7th_axis": bool(sig.rahu_on_7th_axis),
        },
    )


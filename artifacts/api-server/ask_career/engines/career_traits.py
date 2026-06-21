from __future__ import annotations

import re

from ask_career.types import EngineResult
from ._career_base import inclination_evidence, load_inclination, trait_line

_TRAIT_RX: list[tuple[str, re.Pattern[str], str]] = [
    ("leadership", re.compile(r"(?ix)\b(leadership|leader|lead\s*role|authority)\b"), "leadership"),
    ("team", re.compile(r"(?ix)\b(team\s*handle|team\s*player|team\s*work)\b"), "communication"),
    ("independent", re.compile(r"(?ix)\b(independent\s*work|solo|alone|self[\s-]?reliant)\b"), "independence"),
    ("pressure", re.compile(r"(?ix)\b(pressure|stress|deadline|high[\s-]?pressure)\b"), "persistence"),
    ("risk", re.compile(r"(?ix)\b(risk[\s-]?tak|risks?|gamble)\b"), "risk_appetite"),
    ("discipline", re.compile(r"(?ix)\b(disciplin|self[\s-]?control|consistent)\b"), "discipline"),
    ("strategic", re.compile(r"(?ix)\b(strategic|strategy|planner|planning)\b"), "adaptability"),
    ("public", re.compile(r"(?ix)\b(public\s*dealing|client\s*face|people\s*skill)\b"), "communication"),
    ("network", re.compile(r"(?ix)\b(network|connections|contacts)\b"), "communication"),
    ("negotiation", re.compile(r"(?ix)\b(negotiat|deal\s*close|bargain)\b"), "communication"),
    ("entrepreneur", re.compile(r"(?ix)\b(entrepreneur|founder|startup\s*founder)\b"), "independence"),
    ("employee", re.compile(r"(?ix)\b(employee\s*type|job\s*person)\b"), "discipline"),
]


def _detect_trait(q: str) -> str:
    for _label, rx, key in _TRAIT_RX:
        if rx.search(q or ""):
            return key
    if re.search(r"(?ix)\b(natural\s*talent|talent)\b", q):
        return "communication"
    return "leadership"


def run_career_traits(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    trait = _detect_trait(question or "")
    psych = inc.get("psychology") or {}
    score = int(psych.get(trait) or 50)

    high_msgs = {
        "leadership": "strong leadership/authority capacity — can lead teams and decisions",
        "communication": "strong communication/networking — public dealing and talk-based work suit",
        "independence": "strong independence — self-run or founder-style roles suit",
        "risk_appetite": "healthy risk appetite — business/startup moves possible with planning",
        "discipline": "strong discipline — structured long-term career growth supported",
        "persistence": "good pressure handling — can sustain demanding workloads",
        "adaptability": "strategic/adaptive mind — planning and pivoting under change",
        "emotional_stability": "steady emotional base under workplace stress",
        "authority_tolerance": "comfortable with hierarchy and authority channels",
    }
    low_msgs = {
        "leadership": "leadership grows with experience — supportive/ specialist roles first suit",
        "communication": "communication improves with practice — backend/analytical roles may suit first",
        "independence": "team/employer structure may suit better than solo pressure early on",
        "risk_appetite": "conservative risk style — stable job/salary path safer",
        "discipline": "needs external deadlines/systems — build habits gradually",
        "persistence": "pressure sensitive — choose paced roles and clear boundaries",
        "adaptability": "prefers stable routine — deep specialist path may suit",
    }

    evidence = inclination_evidence(inc, limit=3)
    evidence.append(trait_line(inc, trait, high=high_msgs.get(trait, "strong"), low=low_msgs.get(trait, "moderate")))
    if trait != "leadership":
        evidence.append(trait_line(inc, "leadership", high=high_msgs["leadership"], low=low_msgs["leadership"]))
    if inc.get("structure_score") is not None:
        evidence.append(f"Structure score {inc.get('structure_score')}/100 — org/system comfort level.")
    if inc.get("independence_score") is not None:
        evidence.append(f"Independence score {inc.get('independence_score')}/100 — self-run vs employed tilt.")

    verdict = f"Career trait ({trait.replace('_', ' ')}): score {score}/100 — pattern from D1/D10 psychology layer"

    return EngineResult(
        archetype="career_traits",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 65,
        answer_plan="Direct yes/no or level answer → trait score evidence → one habit tip.",
        summary=[f"QUESTION FOCUS: career personality trait — {trait}."],
        evidence=evidence[:8],
        ignore=["timing", "marriage"],
        checks={"slice_type": "career_engine_v1", "archetype": "career_traits", "trait": trait, "score": score},
    )

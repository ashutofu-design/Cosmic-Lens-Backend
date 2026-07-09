from __future__ import annotations

from vedic.love_reality.scoring_core import KundliReader, risk_band_high_is_good

from ._chart_axes import house_axis_evidence, planet_line
from ._person_signals import build_person_signals, pick_notes
from ..types import EngineResult

_COMMIT_NEGATIVE_KEYS = [
    "Saturn on 7th",
    "7th lord in dusthana",
    "7th lord debilitated",
    "Moon under Saturn/Rahu",
    "nodes on 7th",
    "hidden ties",
    "parallel attention",
    "Venus in dusthana",
    "Venus debilitated",
]
_COMMIT_SUPPORT_KEYS = [
    "5th lord strong",
    "Saturn as 7th lord in 7th",
    "Saturn-Moon link",
    "emotional reopening",
]


def _commitment_level(sig, negative: list[str]) -> str:
    w = int(sig.affliction_weight or 0)
    n = len(negative)
    score = max(0, min(100, 100 - int(round(w * 1.1))))
    band = risk_band_high_is_good(score)

    if sig.third_person_risk:
        return "low"
    if band == "low" or n >= 3 or w >= 36:
        return "low"
    if n >= 2 or w >= 24 or sig.saturn_on_7th:
        return "mixed"
    if n >= 1 or w >= 14:
        return "cautious"
    return "ready"


def _commitment_verdict(level: str, angle: str) -> str:
    topic = {
        "commitment_ready": "Commitment readiness",
        "serious_relationship": "Serious relationship intent",
        "casual_relationship": "Casual vs serious intent",
        "time_pass": "Time-pass vs genuine intent",
        "long_term_intent": "Long-term commitment intent",
        "genuine_intent": "Genuine investment",
        "loyalty_intent": "Commitment loyalty",
    }.get(angle, "Commitment intent")
    tone = {
        "ready": f"{topic}: mostly ready — steady talk and consistency strengthen the bond",
        "cautious": f"{topic}: cautious phase — interest hai par clarity aur patience chahiye",
        "mixed": f"{topic}: mixed — ichha hai lekin friction ya distance commitment test karta hai",
        "low": f"{topic}: low / hesitant — boundaries aur honest intent check zaroori",
    }
    return tone.get(level, tone["mixed"])


def run_commitment(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    try:
        from ask_mr.v2 import v2_enabled_for
        from ask_mr.v2.adapter import v2_to_engine_result
        from ask_mr.v2.engines.commitment import run_commitment_v2

        if v2_enabled_for("commitment"):
            out = run_commitment_v2(kundli, question, wants_explain=wants_explain)
            return v2_to_engine_result(out)
    except Exception:
        pass

    from ask_intent_fidelity import infer_partner_commitment_angle

    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    sig = build_person_signals(kundli)
    angle = (infer_partner_commitment_angle(question or "") or "general_commitment").strip().lower()
    negative = pick_notes(sig, _COMMIT_NEGATIVE_KEYS, limit=5)
    support = pick_notes(sig, _COMMIT_SUPPORT_KEYS, limit=2)
    level = _commitment_level(sig, negative)
    verdict = _commitment_verdict(level, angle)

    evidence: list[str] = [
        house_axis_evidence(r, 7, label="Partnership/commitment axis (7th house)"),
    ]
    jup_line = planet_line(r, "Jupiter", role="faith/long-term growth")
    ven_line = planet_line(r, "Venus", role="love/commitment karak")
    if jup_line:
        evidence.append(jup_line)
    if ven_line:
        evidence.append(ven_line)
    if support:
        evidence.insert(0, f"Commitment support: {support[0]}")
    for line in negative[:3]:
        evidence.append(f"Commitment friction: {line}")
    if not evidence:
        evidence = ["Commitment pattern looks balanced — clarity through honest conversation matters."]

    return EngineResult(
        archetype="commitment",
        verdict=verdict,
        confidence="medium",
        word_budget=85 if wants_explain else 60,
        answer_plan="2–3 sentences: commitment level → 1–2 reasons → one clarity habit.",
        summary=[
            "Answer commitment/seriousness directly — no shayad/ho sakta hai.",
            "Focus on intent and consistency, not betrayal accusations.",
        ],
        evidence=evidence[:8],
        ignore=["timing dates/windows", "cheating accusations unless asked", "spouse profession"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "commitment",
            "commitment_level": level,
            "commitment_angle": angle,
            "affliction_weight": int(sig.affliction_weight or 0),
        },
    )

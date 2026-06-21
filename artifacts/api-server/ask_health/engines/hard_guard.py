from __future__ import annotations

from health_focus_routing import ATOMIC_CHECKS

from ..types import EngineResult

_REFUSE_ARCH = {
    "refuse_diagnosis": "REFUSE_DIAGNOSIS",
    "refuse_death": "REFUSE_DEATH",
    "refuse_cure_guarantee": "REFUSE_CURE_GUARANTEE",
    "refuse_timing_decline": "REFUSE_TIMING_DECLINE",
    "refuse_timing_recovery": "REFUSE_TIMING_RECOVERY",
    "refuse_surgery_muhurat": "REFUSE_SURGERY_MUHURAT",
    "crisis_redirect": "CRISIS_REDIRECT",
}


def run_hard_guard(
    kundli: dict,
    question: str,
    *,
    archetype: str,
    wants_explain: bool = False,
) -> EngineResult:
    tag = _REFUSE_ARCH.get(archetype, "REFUSE_DIAGNOSIS")
    msg = ATOMIC_CHECKS.get(tag, ATOMIC_CHECKS["REFUSE_DIAGNOSIS"])
    if tag == "CRISIS_REDIRECT":
        msg = msg.replace("OVERRIDE all other blocks: ", "").strip().strip("'")

    return EngineResult(
        archetype=archetype,
        verdict=msg[:220],
        confidence="high",
        word_budget=90 if wants_explain else 75,
        answer_plan="Deliver refuse/crisis message — NO chart calculation.",
        summary=["Medical ethics guard.", "No diagnosis/death/dates/cure guarantee."],
        evidence=["Hard guard — chart facts skipped for safety."],
        ignore=["chart details", "dasha", "timing"],
        skip_llm=True,
        template_text=msg,
        checks={"slice_type": "health_engine_v1", "archetype": archetype, "hard_guard": tag},
    )

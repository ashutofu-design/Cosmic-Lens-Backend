from __future__ import annotations

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

# User-facing refuse text — clear: cancer/death/diagnosis NOT allowed
_REFUSE_USER_MSG = {
    "refuse_diagnosis": (
        "Specific bimari ka naam chart se batana allowed nahi hai — "
        "na cancer, na diabetes, na koi disease label. "
        "Yeh sirf doctor diagnose karte hain. "
        "Main aapko vitality zones aur general tendency areas bata sakta hoon — "
        "symptoms ke liye doctor se milna zaroori hai."
    ),
    "refuse_death": (
        "Death / mrityu / 'kab marunga' ka jawab dena shastriya etiquette ke khilaf hai. "
        "Main exact end-date ya lifespan predict nahi kar sakta. "
        "Vitality aur care habits bata sakta hoon — "
        "life-death ka final jawab doctor + zindagi ke decisions hain, chart nahi."
    ),
    "refuse_cure_guarantee": (
        "100% cure ya pakka thik hone ka promise dena allowed nahi — "
        "na chart se, na medical ethics se. "
        "Recovery-capacity aur supportive habits bata sakta hoon; "
        "final cure assurance sirf treating doctor de sakte hain."
    ),
    "refuse_timing_decline": (
        "Bimari aane ka exact date predict karna allowed nahi. "
        "Main vulnerability tendency aur preventive zones bata sakta hoon — exact kab nahi."
    ),
    "refuse_timing_recovery": (
        "Recovery ka exact date chart se nahi bataya jata — "
        "body response + doctor treatment pe depend karta hai. "
        "Recovery-capacity bata sakta hoon, date nahi."
    ),
    "refuse_surgery_muhurat": (
        "Operation/surgery ka muhurat ya exact date dena allowed nahi — "
        "surgeon + family decide karte hain. "
        "General caution/support tone bata sakta hoon, date nahi."
    ),
    "crisis_redirect": (
        "Aapke alfaz se lag raha hai aap bahut tough phase me ho. "
        "Please abhi iCall +91-9152987821 ya Vandrevala +91-1860-2662-345 pe baat karo — "
        "ye trained log 24/7 free me sunte hain. Aap akele nahi ho. "
        "Pehle aap safe — chart baad me."
    ),
}


def run_hard_guard(
    kundli: dict,
    question: str,
    *,
    archetype: str,
    wants_explain: bool = False,
) -> EngineResult:
    tag = _REFUSE_ARCH.get(archetype, "REFUSE_DIAGNOSIS")
    msg = _REFUSE_USER_MSG.get(archetype) or _REFUSE_USER_MSG["refuse_diagnosis"]

    return EngineResult(
        archetype=archetype,
        verdict=msg[:280],
        confidence="high",
        word_budget=90 if wants_explain else 75,
        answer_plan="Deliver refuse/crisis message — NO chart calculation.",
        summary=["Medical ethics guard.", "No diagnosis/death/dates/cure guarantee."],
        evidence=["Hard guard — chart facts skipped for safety."],
        ignore=["chart details", "dasha", "timing", "disease names", "death"],
        skip_llm=True,
        template_text=msg,
        checks={"slice_type": "health_engine_v1", "archetype": archetype, "hard_guard": tag},
    )

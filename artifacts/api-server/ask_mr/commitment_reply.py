"""Plain Hinglish partner-commitment replies — no chart jargon for users."""
from __future__ import annotations

from typing import Any


def _trust_level(result: Any) -> str:
    checks = getattr(result, "checks", None) or {}
    level = str(checks.get("trust_level") or "").strip().lower()
    if level in ("moderate", "mixed", "unstable", "risky"):
        return level
    verdict = str(getattr(result, "verdict", "") or "").lower()
    if "high-risk" in verdict or "risky" in verdict:
        return "risky"
    if "sensitive" in verdict or "unstable" in verdict:
        return "unstable"
    if "mixed" in verdict:
        return "mixed"
    return "moderate"


def format_partner_commitment_user_reply(question: str, result: Any) -> str:
    """User-facing commitment answer from engine verdict — never raw house/planet lines."""
    from ask_intent_fidelity import infer_partner_commitment_angle

    angle = infer_partner_commitment_angle(question or "") or "general_commitment"
    level = _trust_level(result)

    # (angle, level) → 2–3 short Hinglish sentences; answer the exact question angle.
    replies: dict[tuple[str, str], str] = {
        ("commitment_ready", "moderate"): (
            "Haan — chart pattern ke hisaab se partner commitment ke liye mostly ready dikhta hai. "
            "Trust stable rehta hai; clear baat se bond strong hota hai."
        ),
        ("commitment_ready", "mixed"): (
            "Thoda mixed — partner commitment ki taraf jaa sakta hai, "
            "lekin kabhi distance ya friction trust ko test karta hai. "
            "Seedha pucho kitna serious woh long-term ke liye hai."
        ),
        ("commitment_ready", "unstable"): (
            "Abhi poora commitment-ready phase nahi dikhta — trust sensitive zone hai. "
            "Clarity aur boundaries ke bina bond weak pad sakta hai; "
            "pehle honest baat karke dekho woh ready hai ya sirf abhi confuse hai."
        ),
        ("commitment_ready", "risky"): (
            "Commitment-ready signal kamzor hai — secrecy ya impulse trust ko blur kar sakta hai. "
            "Bina clear boundaries ke aage mat badho; pehle loyalty aur intent clear karo."
        ),
        ("serious_relationship", "moderate"): (
            "Haan — partner serious long-term relationship ki taraf inclined dikhta hai. "
            "Consistency aur trust se yeh aur clear hota hai."
        ),
        ("serious_relationship", "mixed"): (
            "Serious intent hai lekin thoda hesitant phase bhi dikhta hai. "
            "Open baat se pata chalega woh casual se zyada committed hai ya nahi."
        ),
        ("serious_relationship", "unstable"): (
            "Abhi serious long-term signal weak hai — emotional clarity pehle chahiye. "
            "Boundaries set karke dekho woh genuinely invested hai ya nahi."
        ),
        ("serious_relationship", "risky"): (
            "Serious relationship ka pattern abhi clear nahi — trust risk high dikhta hai. "
            "Secret ya casual vibes ho to seedha confront karo."
        ),
        ("casual_relationship", "moderate"): (
            "Casual / light bond zyada dikhta hai — full commitment abhi front pe nahi. "
            "Agar serious chahiye to expectations clear karo."
        ),
        ("casual_relationship", "mixed"): (
            "Casual aur serious dono signals mix hain — partner confuse ho sakta hai. "
            "Direct sawaal se clarity aayegi."
        ),
        ("casual_relationship", "unstable"): (
            "Casual / time-pass tendency zyada dikhti hai — long-term commitment abhi weak hai. "
            "Agar serious chahiye to jaldi expectations match karo."
        ),
        ("casual_relationship", "risky"): (
            "Casual ya secret pattern strong dikhta hai — serious commitment ke liye abhi safe nahi. "
            "Pehle honesty aur boundaries fix karo."
        ),
        ("time_pass", "moderate"): (
            "Time-pass vibe zyada nahi — partner mein genuine interest dikhta hai. "
            "Phir bhi clear baat se confirm karna better hai."
        ),
        ("time_pass", "mixed"): (
            "Kabhi invested kabhi distant — time-pass ya confusion dono ho sakte hain. "
            "Seedha pucho woh sirf waqt guzar raha hai ya serious hai."
        ),
        ("time_pass", "unstable"): (
            "Time-pass pattern zyada dikhta hai — long-term commitment abhi weak lagta hai. "
            "Agar tum serious ho to jaldi clarity lo."
        ),
        ("time_pass", "risky"): (
            "Sirf time-pass / low-investment signal strong hai — trust mat todo. "
            "Pehle intent clear karo, phir aage badho."
        ),
        ("long_term_intent", "moderate"): (
            "Haan — long-term saath ka intent mostly positive dikhta hai. "
            "Patience aur clear communication se bond grow karta hai."
        ),
        ("long_term_intent", "mixed"): (
            "Long-term intent hai par abhi mixed phase — friction trust test karta hai. "
            "Regular honest baat se picture clear hogi."
        ),
        ("long_term_intent", "unstable"): (
            "Long-term intent abhi weak / sensitive phase me hai. "
            "Boundaries aur clarity ke bina aage mat assume karo."
        ),
        ("long_term_intent", "risky"): (
            "Long-term saath ka signal risky dikhta hai — pehle loyalty clear karo."
        ),
    }

    key = (angle, level)
    if key in replies:
        return replies[key]

    # Angle-only fallback
    angle_defaults = {
        "commitment_ready": replies[("commitment_ready", "mixed")],
        "serious_relationship": replies[("serious_relationship", "mixed")],
        "casual_relationship": replies[("casual_relationship", "mixed")],
        "time_pass": replies[("time_pass", "mixed")],
        "long_term_intent": replies[("long_term_intent", "mixed")],
        "genuine_intent": (
            "Genuine investment mixed phase me dikhta hai — "
            "actions aur consistency se sachchai clear hoti hai."
        ),
        "loyalty_intent": (
            "Loyalty pattern "
            + ("mostly stable dikhta hai." if level == "moderate" else "abhi sensitive / mixed dikhta hai — clear boundaries zaroori hain.")
        ),
    }
    if angle in angle_defaults:
        return angle_defaults[angle]

    # General commitment by trust level only
    general = {
        "moderate": (
            "Partner ke commitment intent mostly stable dikhta hai — "
            "clear baat se bond strong rehta hai."
        ),
        "mixed": (
            "Commitment mixed signal deta hai — ichha hai lekin friction ya distance trust test karta hai. "
            "Seedha baat karke clarity lo."
        ),
        "unstable": (
            "Commitment abhi sensitive phase me hai — clarity aur boundaries ke bina bond weak ho sakta hai. "
            "Honest conversation se picture clear hogi."
        ),
        "risky": (
            "Commitment / trust risk high dikhta hai — secrecy ya impulse se pehle distance rakho "
            "aur intent clear karo."
        ),
    }
    return general.get(level, general["mixed"])


def format_compatibility_user_reply(question: str, result: Any) -> str:
    """Plain couple-compatibility answer — no house/planet jargon."""
    from ask_intent_fidelity import infer_compatibility_angle, is_dyadic_couple_question

    q = (question or "").strip()
    checks = getattr(result, "checks", None) or {}
    intent = str(checks.get("question_intent") or "").strip().lower()
    angle = (infer_compatibility_angle(q) or "").strip().lower()
    if not angle and intent:
        if "mental" in intent:
            angle = "mental_compatibility"
        elif "intellectual" in intent:
            angle = "intellectual_compatibility"
        elif "emotional" in intent or intent == "quality":
            angle = "emotional_compatibility"
        else:
            angle = "general_compatibility"
    if not angle:
        angle = "general_compatibility" if is_dyadic_couple_question(q) else "general_compatibility"

    verdict_l = str(getattr(result, "verdict", "") or "").lower()
    mixed = any(
        w in verdict_l
        for w in ("mixed", "steady expression", "friction", "dip", "distance", "patience", "bridge")
    )

    replies: dict[str, tuple[str, str]] = {
        "emotional_compatibility": (
            "Haan — emotional level par compatibility achhi taraf dikhti hai; caring depth dono ke beech maujood hai.",
            "Haan, emotional compatibility hai lekin thodi sensitive jagah bhi hai — caring depth hai, "
            "bas mood ya distance par steady expression aur clear baat zaroori hai.",
        ),
        "mental_compatibility": (
            "Haan — dimaag ka match mostly theek dikhta hai; soch ka rhythm align ho sakta hai.",
            "Mental compatibility mixed hai — soch alag-alag style ki ho sakti hai, "
            "dialogue aur patience se mel better hota hai.",
        ),
        "intellectual_compatibility": (
            "Haan — ideas aur conversation level par match achha ho sakta hai.",
            "Intellectual compatibility thodi mixed hai — depth ya pace alag ho to plainly explain karna helpful rehta hai.",
        ),
        "general_compatibility": (
            "Haan — overall compatibility positive taraf dikhti hai; bond grow kar sakta hai.",
            "Overall compatibility mixed hai — mel hai lekin communication aur respect daily practice chahiye.",
        ),
    }
    pair = replies.get(angle, replies["general_compatibility"])
    return pair[1] if mixed else pair[0]


def try_llm_narrate_mr_engine(
    question: str,
    engine_result: Any,
    *,
    lang: str = "en",
    llm_intent: dict | None = None,
) -> str | None:
    """Backward-compatible wrapper — use narrate_mr_engine_llm."""
    from ask_mr.engine_narrate import narrate_mr_engine_llm

    return narrate_mr_engine_llm(
        question,
        engine_result,
        lang=lang,
        llm_intent=llm_intent,
        wants_explain=False,
    )

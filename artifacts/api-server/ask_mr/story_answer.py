"""Universal story-style MR answers — direct answer + 3–4 flowing paragraphs."""
from __future__ import annotations

import re
from typing import Any

from ask_mr.v2.registry import FROZEN_ENGINE_IDS

STORY_ANSWER_MAX_WORDS = 140

_BAD_STORY_LLM_RX = re.compile(
    r"(?i)(asli wajah|support karne wale|main aapko|kehna chahungi|kehna chahti|"
    r"shaayad|shayad|motaamtaab|thanda dimaag|humara final verdict|final verdict|"
    r"matlab chances|matlab aise sanket|bina soche samjhe|poori baatein|"
    r"isi wajah se final verdict|likely matlab|likely indicators active|"
    r"parallel attention trust ko test|mukhya sanket|dhyan dene layak|"
    r"the\s+big\s+picture|jo mukhya sanket)"
)

_TEMPLATE_REASON_RX = re.compile(
    r"(?i)(isi wajah se final verdict|chart me.*indicators zyada|chart analysis me)"
)


def looks_like_bad_story_llm_output(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    if _BAD_STORY_LLM_RX.search(t):
        return True
    if len(t.split()) > STORY_ANSWER_MAX_WORDS:
        return True
    return False


def story_llm_output_acceptable(
    text: str,
    narrator_json: dict[str, Any] | None,
    engine: str,
) -> bool:
    if looks_like_bad_story_llm_output(text):
        return False
    if not isinstance(narrator_json, dict):
        return True
    from ask_mr.engine_presenter import presenter_has_only_soft_issues, validate_presenter_output

    ok, issues = validate_presenter_output(text, narrator_json, engine)
    return ok or presenter_has_only_soft_issues(issues)


def _humanize_opening(direct_answer: str, verdict: str, question: str) -> str:
    da = (direct_answer or "").strip()
    if not da:
        return f"Chart ke signals ke hisaab se verdict {verdict} hai."
    da = re.sub(r"\s*—\s*", ". ", da).strip()
    da = re.sub(
        r"(?i)\blikely indicators active hain\b",
        "kaafi active signals dikh rahe hain",
        da,
    )
    if not re.match(r"(?i)^(seedhi|haan|nahi|abhi|chart)", da):
        return f"Seedhi baat — {da[0].lower()}{da[1:]}"
    return da


def _human_why_from_signals(data: dict[str, Any]) -> str:
    strongest = list(data.get("strongest") or data.get("strongest_effects") or [])
    weakest = list(data.get("weakest") or data.get("weakest_effects") or [])
    n_pos = len([x for x in strongest if str(x).strip()])
    n_neg = len([x for x in weakest if str(x).strip()])
    if n_neg and not n_pos:
        return (
            "zyada tar signals challenging direction me hain, jabki supportive signs abhi kam hain"
        )
    if n_neg and n_pos:
        return (
            "kuch supportive signs bhi hain, lekin challenging signals zyada weight le rahe hain"
        )
    if n_pos:
        return "supportive signals zyada dominant dikh rahe hain"
    return "signals mixed ya limited hain — verdict carefully balanced hai"


def _story_picture_paragraph(data: dict[str, Any]) -> str:
    reason = str(data.get("reason_summary") or "").strip()
    strongest_fx = list(data.get("strongest_effects") or data.get("strongest") or [])
    weakest_fx = list(data.get("weakest_effects") or data.get("weakest") or [])

    if reason and not _TEMPLATE_REASON_RX.search(reason):
        core = reason.rstrip(".")
    else:
        core = f"assessment isliye aaya kyunki {_human_why_from_signals(data)}"

    effect_bits: list[str] = []
    for raw in list(weakest_fx)[:1] + list(strongest_fx)[:1]:
        bit = str(raw).strip().rstrip(".")
        if bit and "limited" not in bit.lower() and bit.lower() not in core.lower():
            effect_bits.append(bit)

    if effect_bits:
        return f"Jo picture banti hai woh yeh hai: {core}. {effect_bits[0]}."
    return f"Jo picture banti hai woh yeh hai: {core}."


def _story_advice_paragraph(data: dict[str, Any]) -> str:
    for key in (
        "practical_guidance",
        "meaning_note",
        "transparency_outlook",
        "scorecard_user_note",
        "conditions_line",
    ):
        advice = str(data.get(key) or "").strip()
        if advice:
            if not re.match(r"(?i)^(is|abhi|calm|partner|ye|aap|pattern|rishte)", advice):
                advice = f"Is phase me {advice[0].lower()}{advice[1:]}"
            return advice
    return (
        "Pattern calmly observe karo — facts ke saath phir decision lena behtar rahega."
    )


def _story_confidence_line(data: dict[str, Any]) -> str:
    exp = str(data.get("confidence_explanation") or "").strip()
    if exp:
        return exp
    score = int(data.get("confidence") or 0)
    label = str(data.get("confidence_label") or "Medium")
    return f"Confidence {label} ({score}%) hai."


def render_story_human_answer(
    data: dict[str, Any],
    question: str = "",
    *,
    engine: str = "",
    lang: str = "hn",
) -> str:
    """4-paragraph story answer from locked narrator JSON."""
    eng = (engine or str(data.get("question_type") or "")).strip().lower()
    if eng == "secret_relationship":
        from ask_mr.secret_narrator import render_secret_human_answer

        return render_secret_human_answer(data, question, lang=lang)

    verdict = str(data.get("final_verdict") or data.get("verdict") or "Mixed")
    q = (question or str(data.get("original_question") or "")).strip()
    direct = str(data.get("direct_answer") or "").strip()

    parts = [
        _humanize_opening(direct, verdict, q),
        _story_picture_paragraph(data),
        _story_advice_paragraph(data),
        _story_confidence_line(data),
    ]
    return "\n\n".join(re.sub(r"\s{2,}", " ", p).strip() for p in parts if p)


def engine_result_to_narrator_json(
    engine_result: Any,
    *,
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build narrator JSON for any frozen MR engine."""
    arch = str(getattr(engine_result, "archetype", "") or "").strip().lower()
    q = (question or "").strip()
    dna = None
    if isinstance(llm_intent, dict):
        dna = llm_intent.get("question_dna")
    dna_arg = dna if isinstance(dna, dict) else None

    if arch == "commitment":
        from ask_mr.commitment_narrator import engine_result_to_commitment_json

        return engine_result_to_commitment_json(engine_result, question=q)
    if arch == "patchup":
        from ask_mr.patchup_narrator import engine_result_to_patchup_json

        return engine_result_to_patchup_json(engine_result, question=q)
    if arch == "secret_relationship":
        from ask_mr.secret_narrator import engine_result_to_secret_json

        return engine_result_to_secret_json(
            engine_result, question=q, question_dna=dna_arg
        )
    if arch == "loyalty_trust":
        from ask_mr.loyalty_narrator import engine_result_to_loyalty_json

        return engine_result_to_loyalty_json(engine_result, question=q)
    if arch == "breakup_risk":
        from ask_mr.breakup_narrator import engine_result_to_breakup_json

        return engine_result_to_breakup_json(engine_result, question=q)
    if arch == "compatibility":
        from ask_mr.compatibility_narrator import engine_result_to_compatibility_json

        return engine_result_to_compatibility_json(engine_result, question=q)
    if arch == "partner_nature":
        from ask_mr.partner_nature_narrator import engine_result_to_partner_nature_json

        return engine_result_to_partner_nature_json(
            engine_result, question=q, question_dna=dna_arg
        )
    if arch == "communication":
        from ask_mr.communication_narrator import engine_result_to_communication_json

        return engine_result_to_communication_json(
            engine_result, question=q, question_dna=dna_arg
        )
    if arch == "emotional_attachment":
        from ask_mr.emotional_attachment_narrator import (
            engine_result_to_emotional_attachment_json,
        )

        return engine_result_to_emotional_attachment_json(
            engine_result, question=q, question_dna=dna_arg
        )
    if arch == "family_approval":
        from ask_mr.family_approval_narrator import engine_result_to_family_approval_json

        return engine_result_to_family_approval_json(
            engine_result, question=q, question_dna=dna_arg
        )
    if arch == "long_distance":
        from ask_mr.long_distance_narrator import engine_result_to_long_distance_json

        return engine_result_to_long_distance_json(
            engine_result, question=q, question_dna=dna_arg
        )
    if arch == "toxicity":
        from ask_mr.toxicity_narrator import engine_result_to_toxicity_json

        return engine_result_to_toxicity_json(
            engine_result, question=q, question_dna=dna_arg
        )
    if arch == "chemistry":
        from ask_mr.chemistry_narrator import engine_result_to_chemistry_json

        return engine_result_to_chemistry_json(
            engine_result, question=q, question_dna=dna_arg
        )
    if arch == "bed_intimacy":
        from ask_mr.bed_intimacy_narrator import engine_result_to_bed_intimacy_json

        return engine_result_to_bed_intimacy_json(
            engine_result, question=q, question_dna=dna_arg
        )
    if arch == "karmic_marriage":
        from ask_mr.karmic_marriage_narrator import engine_result_to_karmic_marriage_json

        return engine_result_to_karmic_marriage_json(
            engine_result, question=q, question_dna=dna_arg
        )
    if arch == "relationship_future":
        from ask_mr.relationship_future_narrator import (
            engine_result_to_relationship_future_json,
        )

        return engine_result_to_relationship_future_json(
            engine_result, question=q, question_dna=dna_arg
        )
    if arch == "relationship_decisions":
        from ask_mr.relationship_decisions_narrator import (
            engine_result_to_relationship_decisions_json,
        )

        return engine_result_to_relationship_decisions_json(
            engine_result, question=q, question_dna=dna_arg
        )
    if arch == "relationship_verification":
        from ask_mr.relationship_verification_narrator import (
            engine_result_to_relationship_verification_json,
        )

        return engine_result_to_relationship_verification_json(
            engine_result, question=q, question_dna=dna_arg
        )
    if arch == "relationship_remedies":
        from ask_mr.relationship_remedies_narrator import (
            engine_result_to_relationship_remedies_json,
        )

        return engine_result_to_relationship_remedies_json(
            engine_result, question=q, question_dna=dna_arg
        )
    if arch == "one_sided_love":
        from ask_mr.one_sided_love_narrator import engine_result_to_one_sided_love_json

        return engine_result_to_one_sided_love_json(
            engine_result, question=q, question_dna=dna_arg
        )
    raise ValueError(f"unsupported MR engine archetype: {arch}")


def is_story_engine(archetype: str) -> bool:
    return (archetype or "").strip().lower() in FROZEN_ENGINE_IDS

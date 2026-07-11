"""Universal story-style MR answers — direct answer + 3–4 flowing paragraphs."""
from __future__ import annotations

import re
from typing import Any

from ask_mr.v2.registry import FROZEN_ENGINE_IDS

STORY_ANSWER_MAX_WORDS = 280

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


def _humanize_effects(raw_list: list[str], *, engine: str, limit: int = 3) -> list[str]:
    eng = (engine or "").strip().lower()
    if eng == "secret_relationship":
        from ask_mr.secret_templates import effects_from_evidence

        return effects_from_evidence(raw_list, limit=limit)
    out: list[str] = []
    for raw in raw_list:
        bit = str(raw or "").strip().rstrip(".")
        if bit and bit not in out:
            out.append(bit)
        if len(out) >= limit:
            break
    return out


def _young_astro_opening(direct_answer: str, verdict: str, question: str) -> str:
    da = (direct_answer or "").strip()
    q = (question or "").strip()
    if not da:
        core = f"verdict {verdict} aa raha hai"
    else:
        da = re.sub(r"\s*—\s*", ". ", da).strip()
        da = re.sub(
            r"(?i)\blikely indicators active hain\b",
            "kaafi active signals dikh rahe hain",
            da,
        )
        core = da[0].lower() + da[1:] if da else ""
    if q:
        return (
            f"Dekho, tumne jo sawal pucha — \"{q}\" — maine tumhari kundli check ki. "
            f"Seedhi baat: {core}"
        )
    return f"Dekho, maine tumhari kundli check ki. Seedhi baat: {core}"


def _user_chart_pinpoint(raw: str) -> str:
    """User-facing chart line — keep planet/house/lord, strip internal D1/D9 codes."""
    s = (raw or "").strip().rstrip(".")
    if not s:
        return ""
    s = re.sub(r"(?i)\bd1\s+", "", s)
    s = re.sub(r"(?i)\bd9\s+", "Navamsa me ", s)
    s = re.sub(
        r"(?i)\brelationship\s+axis\b",
        "rishte ka axis (7th/8th/12th link)",
        s,
    )
    return s


def _kundli_chart_paragraph(
    raw_lines: list[str],
    effects: list[str],
    *,
    polarity: str,
) -> str:
    pinpoints = [_user_chart_pinpoint(x) for x in raw_lines if str(x).strip()]
    pinpoints = [p for p in pinpoints if p][:2]
    meanings = [e.rstrip(".") for e in effects if e and "limited" not in e.lower()][:2]

    if polarity == "positive":
        if not pinpoints and not meanings:
            return (
                "Tumhari kundli me supportive ya transparency wale signals abhi kam strong dikh rahe hain. "
                "Iska matlab chart zyada tar challenging direction me lean kar raha hai, "
                "aur positive side abhi utni weight nahi le pa rahi — ye point main clearly isliye bol raha hoon "
                "taaki tum samjho ki picture ek taraf jhuki hui hai."
            )
        intro = (
            "Tumhari kundli me jo supportive chart readings fire hui, unhe main detail me samjhata hoon — "
            "ye sab tumhari personal chart se aaye hain."
        )
    else:
        if not pinpoints and not meanings:
            return (
                "Challenging side me abhi koi dominant red flag clearly highlight nahi ho raha, "
                "lekin overall picture me negative signals ko bhi main read karta hoon taaki answer balanced rahe."
            )
        intro = (
            "Ab challenging side pe — ye chart readings sabse zyada weight le rahi hain, "
            "aur inhi se doubt ya secrecy wala feel aata hai:"
        )

    parts = [intro]
    if pinpoints:
        for i, pinpoint in enumerate(pinpoints):
            meaning = meanings[i] if i < len(meanings) else ""
            if meaning and meaning.lower() not in pinpoint.lower():
                parts.append(f"{pinpoint} — iska matlab daily life me: {meaning}.")
            else:
                parts.append(
                    f"{pinpoint} — yeh tumhari kundli ka fired signal hai, isliye picture is direction me jhuki hai."
                )
    elif meanings:
        lead = meanings[0]
        parts.append(f"Chart me sabse zyada weight is reading ne liya: {lead}.")
        if len(meanings) > 1:
            parts.append(f"Iske saath ek aur challenging reading bhi active hai: {meanings[1]}.")

    if polarity == "positive":
        parts.append(
            "Ye positive signals main isliye explain kar raha hoon taaki tumhe pata chale "
            "chart me sirf doubt wali side nahi, supportive readings bhi hui hain."
        )
    else:
        parts.append(
            "Ye wahi points hain jinke wajah se doubt, tension ya secrecy feel hoti hai — "
            "main inhe alag se isliye batata hoon taaki tum samjho answer kahan se aaya."
        )
    return " ".join(parts)


def _kundli_positive_paragraph(raw_lines: list[str], effects: list[str]) -> str:
    return _kundli_chart_paragraph(raw_lines, effects, polarity="positive")


def _kundli_negative_paragraph(raw_lines: list[str], effects: list[str]) -> str:
    return _kundli_chart_paragraph(raw_lines, effects, polarity="negative")


def _verdict_bridge(verdict: str, data: dict[str, Any]) -> str:
    meaning = str(data.get("meaning_note") or "").strip()
    if meaning and re.search(
        r"(?i)\b(low|possible|likely|high)\s+risk\s+matlab\b|matlab\s+secrecy\s+signals\s+active",
        meaning,
    ):
        meaning = ""
    body = (
        f"Jab main dono sides ko saath me dekhta hoon, overall verdict {verdict} banta hai. "
        f"Yeh maine randomly nahi likha — tumhari kundli ke fired signals ko mila ke yeh conclusion aaya hai."
    )
    if meaning:
        body += f" {meaning}"
    return body


def _young_astro_advice(data: dict[str, Any]) -> str:
    practical = str(data.get("practical_guidance") or "").strip()
    transparency = str(data.get("transparency_outlook") or "").strip()
    meaning = str(data.get("meaning_note") or "").strip()
    extra = str(data.get("scorecard_user_note") or data.get("conditions_line") or "").strip()

    bits: list[str] = []
    if practical:
        bits.append(practical.rstrip("."))
    elif transparency:
        bits.append(transparency.rstrip("."))
    if extra and extra not in bits:
        bits.append(extra.rstrip("."))

    if bits:
        joined = ". ".join(bits)
        return (
            f"Meri advice simple hai: {joined}. "
            f"Jaldi me reaction ya accusation se bachna — pehle pattern dekho, facts note karo, phir baat karna."
        )
    if meaning:
        return (
            f"Meri advice: {meaning.rstrip('.')}. "
            f"Calm approach rakho — chart ne direction di hai, ab tumhe practically handle karna hai."
        )
    return (
        "Meri advice: pattern calmly observe karo, facts jama karo, phir decision lena. "
        "Chart direction de raha hai — tumhe emotionally react karne se pehle practically verify karna helpful rahega."
    )


def _humanize_opening(direct_answer: str, verdict: str, question: str) -> str:
    return _young_astro_opening(direct_answer, verdict, question)


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
    """Young-astrologer story answer with kundli positive/negative pinpoints."""
    eng = (engine or str(data.get("question_type") or "")).strip().lower()
    verdict = str(data.get("final_verdict") or data.get("verdict") or "Mixed")
    q = (question or str(data.get("original_question") or "")).strip()
    direct = str(data.get("direct_answer") or "").strip()

    strongest_raw = list(data.get("strongest") or [])
    weakest_raw = list(data.get("weakest") or [])
    if not strongest_raw:
        strongest_raw = list(data.get("strongest_effects") or [])
    if not weakest_raw:
        weakest_raw = list(data.get("weakest_effects") or [])
    pos_fx = _humanize_effects(strongest_raw, engine=eng, limit=2)
    neg_fx = _humanize_effects(weakest_raw, engine=eng, limit=2)

    if eng == "secret_relationship":
        from ask_mr.secret_narrator import _secret_direct_answer

        level = str(data.get("secret_level") or data.get("secrecy_level") or verdict).strip().lower()
        angle = str(data.get("answer_focus") or data.get("secret_angle") or "general_secrecy")
        opening = (
            f"Dekho, tumne jo sawal pucha — \"{q}\" — maine tumhari kundli check ki. "
            f"{_secret_direct_answer(angle, level, verdict, q)}"
        )
    else:
        opening = _young_astro_opening(direct, verdict, q)

    parts = [
        opening,
        _kundli_positive_paragraph(strongest_raw, pos_fx),
        _kundli_negative_paragraph(weakest_raw, neg_fx),
        _verdict_bridge(verdict, data),
        _young_astro_advice(data),
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

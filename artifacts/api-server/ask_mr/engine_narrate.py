"""MR engine → LLM narrator (robust) + rich plain fallback when API fails."""
from __future__ import annotations

import os
import re
import time
from typing import Any


def _strip_technical_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        s = (line or "").strip()
        if not s:
            continue
        low = s.lower()
        if any(
            x in low
            for x in (
                "house ",
                "h from lagna",
                "rules ",
                "sign ",
                "lord ",
                "occupants",
                "malefics",
                "axis (",
                "karak",
            )
        ):
            continue
        s = re.sub(r"^(trust challenge|trust support|emotional friction):\s*", "", s, flags=re.I)
        if len(s) > 12:
            out.append(s)
    return out[:3]


def _concise_mode() -> bool:
    try:
        from ask_batch_runner import is_batch_concise_mode

        return is_batch_concise_mode()
    except Exception:
        return False


def format_engine_rich_plain(
    question: str,
    result: Any,
    *,
    llm_intent: dict | None = None,
    lang: str = "hi",
    concise: bool | None = None,
) -> str:
    """Human answer without chart jargon — 3-section or short paragraph (batch)."""
    if concise is None:
        concise = _concise_mode()
    from ask_intent_fidelity import (
        infer_breakup_angle,
        infer_communication_angle,
        infer_compatibility_angle,
        infer_emotional_attachment_angle,
        infer_family_approval_angle,
        infer_long_distance_angle,
        infer_chemistry_angle,
        infer_bed_intimacy_angle,
        infer_karmic_marriage_angle,
        infer_relationship_future_angle,
        infer_one_sided_love_angle,
        infer_toxicity_angle,
        infer_loyalty_angle,
        infer_partner_commitment_angle,
        infer_partner_nature_angle,
        infer_reconciliation_angle,
        infer_secret_angle,
    )
    from ask_mr.commitment_reply import (
        format_compatibility_user_reply,
        format_partner_commitment_user_reply,
    )
    from ask_question_understand import narrator_intent_hint

    q = (question or "").strip()
    arch = str(getattr(result, "archetype", "") or "").strip().lower()
    if arch == "loyalty_trust" or infer_loyalty_angle(q):
        try:
            from ask_mr.loyalty_narrator import (
                engine_result_to_loyalty_json,
                render_loyalty_template_answer,
            )

            data = engine_result_to_loyalty_json(result, question=q)
            big = render_loyalty_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif (
        infer_partner_commitment_angle(q)
        or arch == "commitment"
    ):
        try:
            from ask_mr.commitment_narrator import (
                engine_result_to_commitment_json,
                render_commitment_template_answer,
            )

            data = engine_result_to_commitment_json(result, question=q)
            big = render_commitment_template_answer(data, q, lang=lang)
        except Exception:
            from ask_mr.commitment_reply import format_partner_commitment_user_reply

            big = format_partner_commitment_user_reply(q, result)
    elif arch == "breakup_risk" or infer_breakup_angle(q):
        try:
            from ask_mr.breakup_narrator import (
                engine_result_to_breakup_json,
                render_breakup_template_answer,
            )

            data = engine_result_to_breakup_json(result, question=q)
            big = render_breakup_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif infer_reconciliation_angle(q) or arch == "patchup":
        try:
            from ask_mr.patchup_narrator import (
                engine_result_to_patchup_json,
                render_patchup_template_answer,
            )

            data = engine_result_to_patchup_json(result, question=q)
            big = render_patchup_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif arch == "compatibility" or infer_compatibility_angle(q) or str(getattr(result, "checks", {}).get("question_intent") or "").endswith("compatibility"):
        try:
            from ask_mr.compatibility_narrator import (
                engine_result_to_compatibility_json,
                render_compatibility_template_answer,
            )

            data = engine_result_to_compatibility_json(result, question=q)
            big = render_compatibility_template_answer(data, q, lang=lang)
        except Exception:
            from ask_mr.commitment_reply import format_compatibility_user_reply

            big = format_compatibility_user_reply(q, result)
    elif arch == "secret_relationship" or infer_secret_angle(q):
        try:
            from ask_mr.secret_narrator import (
                engine_result_to_secret_json,
                render_secret_template_answer,
            )

            data = engine_result_to_secret_json(result, question=q)
            big = render_secret_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif arch == "partner_nature" or infer_partner_nature_angle(q):
        try:
            from ask_mr.partner_nature_narrator import (
                engine_result_to_partner_nature_json,
                render_partner_nature_template_answer,
            )

            data = engine_result_to_partner_nature_json(result, question=q)
            big = render_partner_nature_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif arch == "communication" or infer_communication_angle(q):
        try:
            from ask_mr.communication_narrator import (
                engine_result_to_communication_json,
                render_communication_template_answer,
            )

            data = engine_result_to_communication_json(result, question=q)
            big = render_communication_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif arch == "emotional_attachment" or infer_emotional_attachment_angle(q):
        try:
            from ask_mr.emotional_attachment_narrator import (
                engine_result_to_emotional_attachment_json,
                render_emotional_attachment_template_answer,
            )

            data = engine_result_to_emotional_attachment_json(result, question=q)
            big = render_emotional_attachment_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif arch == "family_approval" or infer_family_approval_angle(q):
        try:
            from ask_mr.family_approval_narrator import (
                engine_result_to_family_approval_json,
                render_family_approval_template_answer,
            )

            data = engine_result_to_family_approval_json(result, question=q)
            big = render_family_approval_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif arch == "long_distance" or infer_long_distance_angle(q):
        try:
            from ask_mr.long_distance_narrator import (
                engine_result_to_long_distance_json,
                render_long_distance_template_answer,
            )

            data = engine_result_to_long_distance_json(result, question=q)
            big = render_long_distance_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif arch == "toxicity" or infer_toxicity_angle(q):
        try:
            from ask_mr.toxicity_narrator import (
                engine_result_to_toxicity_json,
                render_toxicity_template_answer,
            )

            data = engine_result_to_toxicity_json(result, question=q)
            big = render_toxicity_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif arch == "chemistry" or infer_chemistry_angle(q):
        try:
            from ask_mr.chemistry_narrator import (
                engine_result_to_chemistry_json,
                render_chemistry_template_answer,
            )

            data = engine_result_to_chemistry_json(result, question=q)
            big = render_chemistry_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif arch == "bed_intimacy" or infer_bed_intimacy_angle(q):
        try:
            from ask_mr.bed_intimacy_narrator import (
                engine_result_to_bed_intimacy_json,
                render_bed_intimacy_template_answer,
            )

            data = engine_result_to_bed_intimacy_json(result, question=q)
            big = render_bed_intimacy_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif arch == "karmic_marriage" or infer_karmic_marriage_angle(q):
        try:
            from ask_mr.karmic_marriage_narrator import (
                engine_result_to_karmic_marriage_json,
                render_karmic_marriage_template_answer,
            )

            data = engine_result_to_karmic_marriage_json(result, question=q)
            big = render_karmic_marriage_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif arch == "relationship_future" or infer_relationship_future_angle(q):
        try:
            from ask_mr.relationship_future_narrator import (
                engine_result_to_relationship_future_json,
                render_relationship_future_template_answer,
            )

            data = engine_result_to_relationship_future_json(result, question=q)
            big = render_relationship_future_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif arch == "one_sided_love" or infer_one_sided_love_angle(q):
        try:
            from ask_mr.one_sided_love_narrator import (
                engine_result_to_one_sided_love_json,
                render_one_sided_love_template_answer,
            )

            data = engine_result_to_one_sided_love_json(result, question=q)
            big = render_one_sided_love_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    else:
        big = str(getattr(result, "verdict", "") or "").strip()
        big = re.sub(r"^[A-Za-z /]+:\s*", "", big)

    hint = narrator_intent_hint(q, llm_intent if isinstance(llm_intent, dict) else {})
    focus = ""
    for line in (hint or "").splitlines():
        if "EXACT" in line or "USER ASKED" in line or "compatibility" in line.lower():
            focus = line.strip()
            break

    pos = _strip_technical_lines(list(getattr(result, "evidence_positive", None) or []))
    neg = _strip_technical_lines(list(getattr(result, "evidence_negative", None) or []))
    if not pos and not neg:
        ev = _strip_technical_lines(list(getattr(result, "evidence", None) or []))
        for line in ev:
            if "friction" in line.lower() or "challenge" in line.lower():
                neg.append(line)
            else:
                pos.append(line)

    why_parts: list[str] = []
    if focus:
        why_parts.append(focus.replace("USER ASKED (answer THIS exact concern — do not drift to other topics):", "").strip())
    for line in pos[:2]:
        why_parts.append(f"• {line}")
    for line in neg[:2]:
        why_parts.append(f"• {line}")
    if not why_parts:
        why_parts.append("• Chart pattern mixed signals deta hai — patience aur clear communication se clarity aati hai.")

    practical = [
        "• Seedhi, calm baat karke expectations clear karo.",
        "• Mood ya distance aaye to react karne se pehle ek din ka pause lo.",
        "• Weekly ek honest check-in rakho — chhoti baatein bhi share karo.",
    ]

    if concise:
        extra = ""
        for line in pos[:1] + neg[:1]:
            plain = re.sub(r"^[*•]\s+", "", line).strip()
            if plain and plain.lower() not in big.lower():
                extra = plain
                break
        body = big.strip()
        if extra:
            body = f"{body} {extra}".strip()
        try:
            from ask_cosmo_narrator import enforce_cosmo_engine_answer

            return enforce_cosmo_engine_answer(body, concise=True)
        except Exception:
            return body

    use_hi = (lang or "").strip().lower() in ("hi", "hn") or bool(re.search(r"[\u0900-\u097F]", q))
    if use_hi:
        return (
            f"**मुख्य बात**\n{big}\n\n"
            f"---\n\n"
            f"**क्यों ऐसा लगता है**\n" + "\n".join(why_parts) + "\n\n"
            f"---\n\n"
            f"**अब क्या करें**\n" + "\n".join(practical[:3])
        )
    return (
        f"**The Big Picture**\n{big}\n\n"
        f"---\n\n"
        f"**Kyun aisa lagta hai**\n" + "\n".join(why_parts) + "\n\n"
        f"---\n\n"
        f"**Ab kya karein**\n" + "\n".join(practical[:3])
    )


def narrate_mr_engine_llm(
    question: str,
    engine_result: Any,
    *,
    lang: str = "en",
    llm_intent: dict | None = None,
    wants_explain: bool = False,
) -> str | None:
    """Call OpenAI MR narrator — retries on transient errors."""
    from openai_helper import _get_client, _resolve_response_lang

    client = _get_client()
    if not client:
        return None

    from ask_mr.narrator import (
        build_mr_engine_narrator_system_prompt,
        build_mr_narrator_user_lang_block,
        polish_mr_confident_tone,
    )
    from ask_question_understand import narrator_intent_hint
    from ask_cosmo_narrator import enforce_cosmo_engine_answer

    arch = str(getattr(engine_result, "archetype", "") or "general_mr").strip().lower()
    eff_lang = _resolve_response_lang(question or "", lang, None)
    narrator_json: dict[str, Any] | None = None
    if arch == "commitment":
        from ask_mr.commitment_narrator import (
            commitment_narrator_payload,
            engine_result_to_commitment_json,
            render_commitment_template_answer,
            validate_commitment_narrator_output,
        )

        narrator_json = engine_result_to_commitment_json(engine_result, question=question or "")
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_COMMITMENT_USE_LLM", "").strip().lower() in (
            "1",
            "true",
            "yes",
        ):
            chart_text = commitment_narrator_payload(
                engine_result,
                wants_explain=wants_explain,
                question=question or "",
            )
        else:
            return render_commitment_template_answer(
                narrator_json,
                question or "",
                lang=eff_lang,
            )
    elif arch == "patchup":
        from ask_mr.patchup_narrator import (
            engine_result_to_patchup_json,
            patchup_narrator_payload,
            render_patchup_template_answer,
            validate_patchup_narrator_output,
        )

        narrator_json = engine_result_to_patchup_json(engine_result, question=question or "")
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_PATCHUP_USE_LLM", "").strip().lower() in (
            "1",
            "true",
            "yes",
        ):
            chart_text = patchup_narrator_payload(
                engine_result,
                wants_explain=wants_explain,
                question=question or "",
            )
        else:
            return render_patchup_template_answer(
                narrator_json,
                question or "",
                lang=eff_lang,
            )
    elif arch == "loyalty_trust":
        from ask_mr.loyalty_narrator import (
            engine_result_to_loyalty_json,
            loyalty_narrator_payload,
            render_loyalty_template_answer,
            validate_loyalty_narrator_output,
        )

        narrator_json = engine_result_to_loyalty_json(engine_result, question=question or "")
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_LOYALTY_USE_LLM", "").strip().lower() in (
            "1",
            "true",
            "yes",
        ):
            chart_text = loyalty_narrator_payload(
                engine_result,
                wants_explain=wants_explain,
                question=question or "",
            )
        else:
            return render_loyalty_template_answer(
                narrator_json,
                question or "",
                lang=eff_lang,
            )
    elif arch == "breakup_risk":
        from ask_mr.breakup_narrator import (
            breakup_narrator_payload,
            engine_result_to_breakup_json,
            render_breakup_template_answer,
            validate_breakup_narrator_output,
        )

        narrator_json = engine_result_to_breakup_json(engine_result, question=question or "")
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_BREAKUP_USE_LLM", "").strip().lower() in (
            "1",
            "true",
            "yes",
        ):
            chart_text = breakup_narrator_payload(
                engine_result,
                wants_explain=wants_explain,
                question=question or "",
            )
        else:
            return render_breakup_template_answer(
                narrator_json,
                question or "",
                lang=eff_lang,
            )
    elif arch == "compatibility":
        from ask_mr.compatibility_narrator import (
            compatibility_narrator_payload,
            engine_result_to_compatibility_json,
            render_compatibility_template_answer,
            validate_compatibility_narrator_output,
        )

        narrator_json = engine_result_to_compatibility_json(engine_result, question=question or "")
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_COMPATIBILITY_USE_LLM", "").strip().lower() in (
            "1",
            "true",
            "yes",
        ):
            chart_text = compatibility_narrator_payload(
                engine_result,
                wants_explain=wants_explain,
                question=question or "",
            )
        else:
            return render_compatibility_template_answer(
                narrator_json,
                question or "",
                lang=eff_lang,
            )
    elif arch == "secret_relationship":
        from ask_mr.secret_narrator import (
            engine_result_to_secret_json,
            render_secret_template_answer,
            secret_narrator_payload,
            validate_secret_narrator_output,
        )

        narrator_json = engine_result_to_secret_json(engine_result, question=question or "")
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_SECRET_USE_LLM", "").strip().lower() in ("1", "true", "yes"):
            chart_text = secret_narrator_payload(engine_result, wants_explain=wants_explain, question=question or "")
        else:
            return render_secret_template_answer(narrator_json, question or "", lang=eff_lang)
    elif arch == "partner_nature":
        from ask_mr.partner_nature_narrator import (
            engine_result_to_partner_nature_json,
            partner_nature_engine_narrator_payload,
            render_partner_nature_template_answer,
            validate_partner_nature_narrator_output,
        )

        narrator_json = engine_result_to_partner_nature_json(engine_result, question=question or "")
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_PARTNER_NATURE_USE_LLM", "").strip().lower() in ("1", "true", "yes"):
            chart_text = partner_nature_engine_narrator_payload(
                engine_result, wants_explain=wants_explain, question=question or ""
            )
        else:
            return render_partner_nature_template_answer(narrator_json, question or "", lang=eff_lang)
    elif arch == "communication":
        from ask_mr.communication_narrator import (
            communication_engine_narrator_payload,
            engine_result_to_communication_json,
            render_communication_template_answer,
            validate_communication_narrator_output,
        )

        narrator_json = engine_result_to_communication_json(engine_result, question=question or "")
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_COMMUNICATION_USE_LLM", "").strip().lower() in ("1", "true", "yes"):
            chart_text = communication_engine_narrator_payload(
                engine_result, wants_explain=wants_explain, question=question or ""
            )
        else:
            return render_communication_template_answer(narrator_json, question or "", lang=eff_lang)
    elif arch == "emotional_attachment":
        from ask_mr.emotional_attachment_narrator import (
            emotional_attachment_engine_narrator_payload,
            engine_result_to_emotional_attachment_json,
            render_emotional_attachment_template_answer,
            validate_emotional_attachment_narrator_output,
        )

        narrator_json = engine_result_to_emotional_attachment_json(engine_result, question=question or "")
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_EMOTIONAL_ATTACHMENT_USE_LLM", "").strip().lower() in ("1", "true", "yes"):
            chart_text = emotional_attachment_engine_narrator_payload(
                engine_result, wants_explain=wants_explain, question=question or ""
            )
        else:
            return render_emotional_attachment_template_answer(narrator_json, question or "", lang=eff_lang)
    elif arch == "family_approval":
        from ask_mr.family_approval_narrator import (
            engine_result_to_family_approval_json,
            family_approval_engine_narrator_payload,
            render_family_approval_template_answer,
            validate_family_approval_narrator_output,
        )

        narrator_json = engine_result_to_family_approval_json(engine_result, question=question or "")
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_FAMILY_APPROVAL_USE_LLM", "").strip().lower() in ("1", "true", "yes"):
            chart_text = family_approval_engine_narrator_payload(
                engine_result, wants_explain=wants_explain, question=question or ""
            )
        else:
            return render_family_approval_template_answer(narrator_json, question or "", lang=eff_lang)
    elif arch == "long_distance":
        from ask_mr.long_distance_narrator import (
            engine_result_to_long_distance_json,
            long_distance_engine_narrator_payload,
            render_long_distance_template_answer,
            validate_long_distance_narrator_output,
        )

        narrator_json = engine_result_to_long_distance_json(engine_result, question=question or "")
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_LONG_DISTANCE_USE_LLM", "").strip().lower() in ("1", "true", "yes"):
            chart_text = long_distance_engine_narrator_payload(
                engine_result, wants_explain=wants_explain, question=question or ""
            )
        else:
            return render_long_distance_template_answer(narrator_json, question or "", lang=eff_lang)
    elif arch == "toxicity":
        from ask_mr.toxicity_narrator import (
            engine_result_to_toxicity_json,
            render_toxicity_template_answer,
            toxicity_engine_narrator_payload,
            validate_toxicity_narrator_output,
        )

        narrator_json = engine_result_to_toxicity_json(engine_result, question=question or "")
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_TOXICITY_USE_LLM", "").strip().lower() in ("1", "true", "yes"):
            chart_text = toxicity_engine_narrator_payload(
                engine_result, wants_explain=wants_explain, question=question or ""
            )
        else:
            return render_toxicity_template_answer(narrator_json, question or "", lang=eff_lang)
    elif arch == "chemistry":
        from ask_mr.chemistry_narrator import (
            engine_result_to_chemistry_json,
            chemistry_engine_narrator_payload,
            render_chemistry_template_answer,
            validate_chemistry_narrator_output,
        )

        _chem_dna = None
        if isinstance(llm_intent, dict):
            _chem_dna = llm_intent.get("question_dna")
        narrator_json = engine_result_to_chemistry_json(
            engine_result,
            question=question or "",
            question_dna=_chem_dna if isinstance(_chem_dna, dict) else None,
        )
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_CHEMISTRY_USE_LLM", "").strip().lower() in ("1", "true", "yes"):
            chart_text = chemistry_engine_narrator_payload(
                engine_result,
                wants_explain=wants_explain,
                question=question or "",
                question_dna=_chem_dna if isinstance(_chem_dna, dict) else None,
            )
        else:
            return render_chemistry_template_answer(narrator_json, question or "", lang=eff_lang)
    elif arch == "bed_intimacy":
        from ask_mr.bed_intimacy_narrator import (
            engine_result_to_bed_intimacy_json,
            bed_intimacy_engine_narrator_payload,
            render_bed_intimacy_template_answer,
            validate_bed_intimacy_narrator_output,
        )

        _intim_dna = None
        if isinstance(llm_intent, dict):
            _intim_dna = llm_intent.get("question_dna")
        narrator_json = engine_result_to_bed_intimacy_json(
            engine_result,
            question=question or "",
            question_dna=_intim_dna if isinstance(_intim_dna, dict) else None,
        )
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_BED_INTIMACY_USE_LLM", "").strip().lower() in ("1", "true", "yes"):
            chart_text = bed_intimacy_engine_narrator_payload(
                engine_result,
                wants_explain=wants_explain,
                question=question or "",
                question_dna=_intim_dna if isinstance(_intim_dna, dict) else None,
            )
        else:
            return render_bed_intimacy_template_answer(narrator_json, question or "", lang=eff_lang)
    elif arch == "karmic_marriage":
        from ask_mr.karmic_marriage_narrator import (
            engine_result_to_karmic_marriage_json,
            karmic_marriage_engine_narrator_payload,
            render_karmic_marriage_template_answer,
            validate_karmic_marriage_narrator_output,
        )

        _karm_dna = None
        if isinstance(llm_intent, dict):
            _karm_dna = llm_intent.get("question_dna")
        narrator_json = engine_result_to_karmic_marriage_json(
            engine_result,
            question=question or "",
            question_dna=_karm_dna if isinstance(_karm_dna, dict) else None,
        )
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_KARMIC_MARRIAGE_USE_LLM", "").strip().lower() in ("1", "true", "yes"):
            chart_text = karmic_marriage_engine_narrator_payload(
                engine_result,
                wants_explain=wants_explain,
                question=question or "",
                question_dna=_karm_dna if isinstance(_karm_dna, dict) else None,
            )
        else:
            return render_karmic_marriage_template_answer(narrator_json, question or "", lang=eff_lang)
    elif arch == "relationship_future":
        from ask_mr.relationship_future_narrator import (
            engine_result_to_relationship_future_json,
            relationship_future_engine_narrator_payload,
            render_relationship_future_template_answer,
            validate_relationship_future_narrator_output,
        )

        _rfut_dna = None
        if isinstance(llm_intent, dict):
            _rfut_dna = llm_intent.get("question_dna")
        narrator_json = engine_result_to_relationship_future_json(
            engine_result,
            question=question or "",
            question_dna=_rfut_dna if isinstance(_rfut_dna, dict) else None,
        )
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_RELATIONSHIP_FUTURE_USE_LLM", "").strip().lower() in ("1", "true", "yes"):
            chart_text = relationship_future_engine_narrator_payload(
                engine_result,
                wants_explain=wants_explain,
                question=question or "",
                question_dna=_rfut_dna if isinstance(_rfut_dna, dict) else None,
            )
        else:
            return render_relationship_future_template_answer(narrator_json, question or "", lang=eff_lang)
    elif arch == "one_sided_love":
        from ask_mr.one_sided_love_narrator import (
            engine_result_to_one_sided_love_json,
            one_sided_love_engine_narrator_payload,
            render_one_sided_love_template_answer,
            validate_one_sided_love_narrator_output,
        )

        _os_dna = None
        if isinstance(llm_intent, dict):
            _os_dna = llm_intent.get("question_dna")
        narrator_json = engine_result_to_one_sided_love_json(
            engine_result,
            question=question or "",
            question_dna=_os_dna if isinstance(_os_dna, dict) else None,
        )
        _checks = dict(engine_result.checks or {})
        _checks["narrator_input"] = narrator_json
        _checks["question"] = question or ""
        engine_result.checks = _checks
        if os.environ.get("ASK_ONE_SIDED_LOVE_USE_LLM", "").strip().lower() in ("1", "true", "yes"):
            chart_text = one_sided_love_engine_narrator_payload(
                engine_result,
                wants_explain=wants_explain,
                question=question or "",
                question_dna=_os_dna if isinstance(_os_dna, dict) else None,
            )
        else:
            return render_one_sided_love_template_answer(narrator_json, question or "", lang=eff_lang)
    else:
        chart_text = engine_result.to_narrator_payload()
    intent = narrator_intent_hint(
        question or "",
        llm_intent if isinstance(llm_intent, dict) else {},
    )
    concise = _concise_mode()
    word_budget = int(getattr(engine_result, "word_budget", None) or 85)
    if concise:
        word_budget = min(word_budget, 70)
    system_prompt = build_mr_engine_narrator_system_prompt(
        chart_text=chart_text,
        reply_lang=eff_lang,
        wants_explain=wants_explain,
        archetype=arch,
        word_budget=word_budget,
        user_intent=intent,
        concise=concise,
    )
    user_payload = build_mr_narrator_user_lang_block(eff_lang) + (question or "")
    model = os.environ.get(
        "RAW_PASSTHROUGH_MODEL",
        os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
    )
    if concise:
        max_tok = 140
    else:
        max_tok = 650 if wants_explain else 480
    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_payload},
                ],
                max_tokens=max_tok,
            )
            text = (resp.choices[0].message.content or "").strip()
            if not text:
                return None
            try:
                text = enforce_cosmo_engine_answer(
                    text,
                    wants_explain=wants_explain,
                    concise=concise,
                )
            except TypeError:
                text = enforce_cosmo_engine_answer(
                    text,
                    wants_explain=wants_explain,
                )
                if concise:
                    text = re.sub(r"\*\*[^*]+\*\*", "", text)
                    text = re.sub(r"\n*---+\n*", " ", text)
                    text = re.sub(r"^[*•]\s+", "", text, flags=re.M)
                    text = re.sub(r"\s{2,}", " ", text).strip()
            polished = polish_mr_confident_tone(text)
            if arch == "commitment" and narrator_json:
                ok, issues = validate_commitment_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] commitment validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.commitment_narrator import render_commitment_template_answer

                    return render_commitment_template_answer(
                        narrator_json,
                        question or "",
                        lang=eff_lang,
                    )
            if arch == "patchup" and narrator_json:
                ok, issues = validate_patchup_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] patchup validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.patchup_narrator import render_patchup_template_answer

                    return render_patchup_template_answer(
                        narrator_json,
                        question or "",
                        lang=eff_lang,
                    )
            if arch == "loyalty_trust" and narrator_json:
                ok, issues = validate_loyalty_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] loyalty validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.loyalty_narrator import render_loyalty_template_answer

                    return render_loyalty_template_answer(
                        narrator_json,
                        question or "",
                        lang=eff_lang,
                    )
            if arch == "breakup_risk" and narrator_json:
                ok, issues = validate_breakup_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] breakup validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.breakup_narrator import render_breakup_template_answer

                    return render_breakup_template_answer(
                        narrator_json,
                        question or "",
                        lang=eff_lang,
                    )
            if arch == "compatibility" and narrator_json:
                ok, issues = validate_compatibility_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] compatibility validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.compatibility_narrator import render_compatibility_template_answer

                    return render_compatibility_template_answer(
                        narrator_json,
                        question or "",
                        lang=eff_lang,
                    )
            if arch == "secret_relationship" and narrator_json:
                ok, issues = validate_secret_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] secret validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.secret_narrator import render_secret_template_answer

                    return render_secret_template_answer(narrator_json, question or "", lang=eff_lang)
            if arch == "partner_nature" and narrator_json:
                ok, issues = validate_partner_nature_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] partner_nature validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.partner_nature_narrator import render_partner_nature_template_answer

                    return render_partner_nature_template_answer(
                        narrator_json, question or "", lang=eff_lang
                    )
            if arch == "communication" and narrator_json:
                ok, issues = validate_communication_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] communication validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.communication_narrator import render_communication_template_answer

                    return render_communication_template_answer(
                        narrator_json, question or "", lang=eff_lang
                    )
            if arch == "emotional_attachment" and narrator_json:
                ok, issues = validate_emotional_attachment_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] emotional_attachment validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.emotional_attachment_narrator import render_emotional_attachment_template_answer

                    return render_emotional_attachment_template_answer(
                        narrator_json, question or "", lang=eff_lang
                    )
            if arch == "family_approval" and narrator_json:
                ok, issues = validate_family_approval_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] family_approval validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.family_approval_narrator import render_family_approval_template_answer

                    return render_family_approval_template_answer(
                        narrator_json, question or "", lang=eff_lang
                    )
            if arch == "long_distance" and narrator_json:
                ok, issues = validate_long_distance_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] long_distance validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.long_distance_narrator import render_long_distance_template_answer

                    return render_long_distance_template_answer(
                        narrator_json, question or "", lang=eff_lang
                    )
            if arch == "toxicity" and narrator_json:
                ok, issues = validate_toxicity_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] toxicity validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.toxicity_narrator import render_toxicity_template_answer

                    return render_toxicity_template_answer(
                        narrator_json, question or "", lang=eff_lang
                    )
            if arch == "chemistry" and narrator_json:
                ok, issues = validate_chemistry_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] chemistry validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.chemistry_narrator import render_chemistry_template_answer

                    return render_chemistry_template_answer(
                        narrator_json, question or "", lang=eff_lang
                    )
            if arch == "bed_intimacy" and narrator_json:
                ok, issues = validate_bed_intimacy_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] bed_intimacy validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.bed_intimacy_narrator import render_bed_intimacy_template_answer

                    return render_bed_intimacy_template_answer(
                        narrator_json, question or "", lang=eff_lang
                    )
            if arch == "karmic_marriage" and narrator_json:
                ok, issues = validate_karmic_marriage_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] karmic_marriage validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.karmic_marriage_narrator import render_karmic_marriage_template_answer

                    return render_karmic_marriage_template_answer(
                        narrator_json, question or "", lang=eff_lang
                    )
            if arch == "relationship_future" and narrator_json:
                ok, issues = validate_relationship_future_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] relationship_future validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.relationship_future_narrator import render_relationship_future_template_answer

                    return render_relationship_future_template_answer(
                        narrator_json, question or "", lang=eff_lang
                    )
            if arch == "one_sided_love" and narrator_json:
                ok, issues = validate_one_sided_love_narrator_output(polished or "", narrator_json)
                if not ok:
                    print(
                        f"[engine_narrate] one_sided_love validation failed {issues} — using locked template",
                        flush=True,
                    )
                    from ask_mr.one_sided_love_narrator import render_one_sided_love_template_answer

                    return render_one_sided_love_template_answer(
                        narrator_json, question or "", lang=eff_lang
                    )
            return polished or None
        except Exception as exc:
            last_exc = exc
            low = str(exc).lower()
            transient = any(
                x in low
                for x in ("connection", "timeout", "429", "rate", "temporarily", "overloaded")
            )
            print(
                f"[engine_narrate] attempt={attempt + 1} failed: {exc}",
                flush=True,
            )
            if transient and attempt == 0:
                time.sleep(1.2)
                continue
            break
    if last_exc:
        print(f"[engine_narrate] all attempts failed: {last_exc}", flush=True)
    return None

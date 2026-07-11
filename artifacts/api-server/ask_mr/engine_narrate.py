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
    from ask_intent_fidelity import infer_compatibility_angle, infer_loyalty_angle, infer_partner_commitment_angle, infer_reconciliation_angle
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
    elif infer_reconciliation_angle(q) or str(getattr(result, "archetype", "")) == "patchup":
        try:
            from ask_mr.patchup_narrator import (
                engine_result_to_patchup_json,
                render_patchup_template_answer,
            )

            data = engine_result_to_patchup_json(result, question=q)
            big = render_patchup_template_answer(data, q, lang=lang)
        except Exception:
            big = str(getattr(result, "verdict", "") or "").strip()
    elif infer_compatibility_angle(q) or str(getattr(result, "checks", {}).get("question_intent") or "").endswith("compatibility"):
        big = format_compatibility_user_reply(q, result)
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

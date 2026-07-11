"""MR static answer + recovery — engine facts then LLM narrator (normal Ask flow)."""
from __future__ import annotations

from typing import Any

from ask_mr.story_answer import (
    engine_result_to_narrator_json,
    is_story_engine,
    render_story_human_answer,
    story_llm_output_acceptable,
)


def try_human_presenter_mr_answer(
    engine_result: Any,
    *,
    question: str,
    lang: str = "hn",
    llm_intent: dict | None = None,
) -> dict | None:
    """Story-style presenter answer for all frozen MR engines."""
    from ask_mr.engine_presenter import human_narrator_enabled, present_story_answer_llm

    if not human_narrator_enabled() or engine_result is None:
        return None
    arch = str(getattr(engine_result, "archetype", "") or "").strip().lower()
    if not is_story_engine(arch):
        return None
    q = (question or "").strip()
    if not q:
        return None

    llm_used = False
    narrated: str | None = None
    narrator_json: dict | None = None

    try:
        from ask_mr.engine_narrate import narrate_mr_engine_llm

        narrated = narrate_mr_engine_llm(
            q,
            engine_result,
            lang=lang,
            llm_intent=llm_intent,
            wants_explain=False,
        )
        llm_used = bool(narrated and str(narrated).strip())
    except Exception as exc:
        print(f"[static_answer] human presenter failed: {exc}", flush=True)

    checks = dict(getattr(engine_result, "checks", None) or {})
    narrator_json = checks.get("narrator_input") if isinstance(checks.get("narrator_input"), dict) else None

    try:
        if not isinstance(narrator_json, dict):
            narrator_json = engine_result_to_narrator_json(
                engine_result,
                question=q,
                llm_intent=llm_intent,
            )
    except Exception as exc:
        print(f"[static_answer] narrator json build failed ({arch}): {exc}", flush=True)
        return None

    composed = render_story_human_answer(narrator_json, q, engine=arch, lang=lang)
    llm_candidate = str(narrated).strip() if narrated else ""

    if not story_llm_output_acceptable(llm_candidate, narrator_json, arch):
        direct = present_story_answer_llm(
            narrator_json,
            engine=arch,
            question=q,
            lang=lang,
            llm_intent=llm_intent,
        )
        if direct and story_llm_output_acceptable(direct, narrator_json, arch):
            llm_candidate = direct

    if story_llm_output_acceptable(llm_candidate, narrator_json, arch):
        narrated = llm_candidate
        llm_used = True
    else:
        narrated = composed
        llm_used = False

    if not (narrated and str(narrated).strip()):
        return None

    conf = 0.5
    if isinstance(narrator_json, dict):
        try:
            conf = max(0.15, min(1.0, float(narrator_json.get("confidence") or 48) / 100.0))
        except (TypeError, ValueError):
            pass

    source = f"{arch}_engine_presenter" if llm_used else f"{arch}_engine_story_compose"
    return {
        "text": str(narrated).strip(),
        "topic": "marriage",
        "confidence": conf,
        "source": source,
        "engine_tag": "ans-engine",
        "follow_ups": [],
        "llm_called": llm_used,
        "_presenter_archetype": arch,
        "_narrator_json": narrator_json,
    }


def _locked_template_fallback(
    engine_result: Any,
    question: str,
    *,
    lang: str = "hn",
) -> str | None:
    arch = str(getattr(engine_result, "archetype", "") or "").strip().lower()
    q = (question or "").strip()
    if not is_story_engine(arch):
        return None
    try:
        data = engine_result_to_narrator_json(engine_result, question=q)
        return render_story_human_answer(data, q, engine=arch, lang=lang)
    except Exception as exc:
        print(f"[static_answer] story compose fallback failed: {exc}", flush=True)
    return None


def _plain_mr_fallback(
    question: str,
    engine_result: Any,
    *,
    lang: str = "en",
    llm_intent: dict | None = None,
) -> str | None:
    arch = str(getattr(engine_result, "archetype", "") or "").strip().lower()
    if is_story_engine(arch):
        try:
            data = engine_result_to_narrator_json(
                engine_result,
                question=question or "",
                llm_intent=llm_intent,
            )
            return render_story_human_answer(
                data,
                question or "",
                engine=arch,
                lang=lang,
            )
        except Exception:
            pass
    try:
        from ask_mr.engine_narrate import format_engine_rich_plain

        return format_engine_rich_plain(
            question,
            engine_result,
            llm_intent=llm_intent,
            lang=lang,
        )
    except Exception as exc:
        print(f"[static_answer] rich plain fallback failed: {exc}", flush=True)
        return None


def _text_from_engine_result(
    engine_result: Any,
    question: str = "",
    *,
    lang: str = "en",
    try_llm: bool = True,
    llm_intent: dict | None = None,
    wants_explain: bool = False,
) -> tuple[str | None, bool]:
    """Return (text, llm_used)."""
    if engine_result is None:
        return None, False
    try:
        from ask_mr.narrator import polish_mr_confident_tone, render_template
        from ask_mr.engine_narrate import narrate_mr_engine_llm
        from ask_mr.engine_presenter import human_narrator_enabled

        tpl = render_template(engine_result)
        if tpl:
            return polish_mr_confident_tone(tpl), False

        q = (question or "").strip()
        arch = str(getattr(engine_result, "archetype", "") or "").strip().lower()

        if human_narrator_enabled() and is_story_engine(arch):
            payload = try_human_presenter_mr_answer(
                engine_result,
                question=q,
                lang=lang,
                llm_intent=llm_intent,
            )
            if payload and str(payload.get("text") or "").strip():
                return str(payload["text"]).strip(), bool(payload.get("llm_called"))

        if try_llm and q:
            narrated = narrate_mr_engine_llm(
                q,
                engine_result,
                lang=lang,
                llm_intent=llm_intent,
                wants_explain=wants_explain,
            )
            if narrated:
                return narrated, True

        locked = _locked_template_fallback(engine_result, q, lang=lang)
        if locked:
            return locked, False

        plain = _plain_mr_fallback(q, engine_result, lang=lang, llm_intent=llm_intent)
        return plain, False
    except Exception as exc:
        print(f"[static_answer] text_from_engine failed: {exc}", flush=True)
        return None, False


def _run_mr_engine(
    question: str,
    kundli: dict,
    *,
    birth: Any = None,
) -> Any:
    from ask_mr import run_mr_static_engine
    from ask_intent_fidelity import infer_partner_commitment_angle

    archetype = None
    if infer_partner_commitment_angle(question):
        archetype = "commitment"
    return run_mr_static_engine(
        kundli,
        question,
        birth=birth,
        wants_explain=False,
        archetype=archetype,
    )


def recover_mr_ask_answer(
    question: str,
    kundli: Any,
    *,
    birth: Any = None,
    lang: str = "en",
    engine_result: Any = None,
    llm_intent: dict | None = None,
    wants_explain: bool = False,
) -> dict | None:
    """Engine → LLM narrator recovery (same intent as normal Ask)."""
    q = (question or "").strip()
    if not q or not isinstance(kundli, dict) or not kundli.get("planets"):
        return None
    try:
        from ask_marriage_relationship_slice import is_marriage_relationship_static_question

        if not is_marriage_relationship_static_question(q):
            return None
    except Exception:
        return None

    if engine_result is None:
        try:
            engine_result = _run_mr_engine(q, kundli, birth=birth)
        except Exception as exc:
            print(f"[recover_mr_ask_answer] engine failed: {exc}", flush=True)
            return None

    text, llm_used = _text_from_engine_result(
        engine_result,
        q,
        lang=lang,
        try_llm=True,
        llm_intent=llm_intent,
        wants_explain=wants_explain,
    )
    if not text:
        return None

    from ask_mr.engine import mr_engine_slice_meta

    meta = mr_engine_slice_meta(engine_result)
    return {
        "text": text,
        "topic": "static",
        "confidence": 0.85,
        "source": "mr_engine_then_llm" if llm_used else "mr_engine_recovery",
        "follow_ups": [],
        "engine_tag": "ans-engine",
        "admin_llm_context": meta,
        "llm_called": llm_used,
    }


def mr_static_answer_payload(
    question: str,
    kundli: dict,
    *,
    birth: Any = None,
    lang: str = "en",
    source: str = "mr_engine_then_llm",
    try_llm: bool = True,
    llm_intent: dict | None = None,
    wants_explain: bool = False,
) -> dict:
    from ask_mr.engine import mr_engine_slice_meta

    eng = _run_mr_engine(question, kundli, birth=birth)
    text, llm_used = _text_from_engine_result(
        eng,
        question,
        lang=lang,
        try_llm=try_llm,
        llm_intent=llm_intent,
        wants_explain=wants_explain,
    )
    meta = mr_engine_slice_meta(eng)
    return {
        "text": text or "Chart se pattern mixed dikhta hai — clear baat se clarity aati hai.",
        "topic": "static",
        "confidence": 0.85,
        "source": "mr_engine_then_llm" if llm_used else source,
        "follow_ups": [],
        "engine_tag": "ans-engine",
        "admin_llm_context": meta,
        "llm_called": llm_used,
    }


def mr_static_ask_recovery(
    question: str,
    kundli: Any,
    *,
    birth: Any = None,
    lang: str = "en",
    engine_result: Any = None,
    llm_intent: dict | None = None,
) -> dict | None:
    return recover_mr_ask_answer(
        question,
        kundli,
        birth=birth,
        lang=lang,
        engine_result=engine_result,
        llm_intent=llm_intent,
    )

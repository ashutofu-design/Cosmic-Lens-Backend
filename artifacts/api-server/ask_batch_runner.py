"""Run one Ask question through the same pipeline as /api/ask/stream (non-SSE)."""
from __future__ import annotations

import contextvars
import itertools
import os
from typing import Any

_batch_concise_mode: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "batch_concise_mode", default=False
)


def is_batch_concise_mode() -> bool:
    return bool(_batch_concise_mode.get())


def _maybe_ack(result: dict, question: str, lang: str) -> dict:
    try:
        if isinstance(result, dict) and isinstance(result.get("text"), str) and result["text"].strip():
            from openai_helper import _maybe_inject_multi_intent_ack as _ack

            result = dict(result)
            result["text"] = _ack(
                result["text"],
                question,
                lang=lang,
                req_id="batch_ask",
                path="batch_single",
            )
    except Exception:
        pass
    return result


def _try_static_engines(
    question: str,
    kundli: dict | None,
    birth: Any,
) -> dict | None:
    """Mirror /api/ask/stream static-engine early returns (property/finance/stock)."""
    try:
        _ps_bypass = os.environ.get("PROPERTY_STATIC_BYPASS", "0") == "1"
    except Exception:
        _ps_bypass = False
    if not _ps_bypass:
        try:
            from property_static import handle_property_question as _ps_handle

            _ps = _ps_handle(question, kundli or {}, birth)
            if _ps and _ps.get("text"):
                return {
                    "text": _ps["text"],
                    "topic": "non_timing_property",
                    "confidence": 1.0,
                    "source": (
                        f"property_static[{_ps.get('scope', 'non_timing')}]:"
                        f"{_ps.get('mode', '')}/{_ps.get('route', '')}"
                    ),
                    "follow_ups": [],
                    "engine_tag": "ans-cosmo",
                }
        except Exception:
            pass

    try:
        _fm_bypass = os.environ.get("FINANCE_STATIC_BYPASS", "0") == "1"
        if (os.environ.get("ASK_FINANCE_ENGINE") or "1").strip() != "0":
            _fm_bypass = True
    except Exception:
        _fm_bypass = False
    if not _fm_bypass:
        try:
            from finance_static import handle_finance_money_question as _fm_handle

            _fm = _fm_handle(question, kundli or {}, birth)
            if _fm and _fm.get("text"):
                return {
                    "text": _fm["text"],
                    "topic": "non_timing_finance",
                    "confidence": 1.0,
                    "source": (
                        f"non_timing_finance[{_fm.get('scope', 'non_timing')}]:"
                        f"{_fm.get('mode', '')}/{_fm.get('route', '')}"
                    ),
                    "follow_ups": [],
                    "engine_tag": "ans-cosmo",
                }
        except Exception:
            pass

    try:
        from stock_engine import handle_finance_question as _fin_handle

        _fin = _fin_handle(question, kundli or {}, birth)
        if _fin and _fin.get("text"):
            return {
                "text": _fin["text"],
                "topic": "stock_finance",
                "confidence": 1.0,
                "source": (
                    f"stock_engine[{_fin.get('scope', 'non_timing')}]:"
                    f"{_fin.get('mode', '')}/{_fin.get('route', '')}"
                ),
                "follow_ups": [],
                "engine_tag": "ans-cosmo",
            }
    except Exception:
        pass

    return None


def _mr_engine_only_fallback(
    question: str,
    kundli: dict,
    *,
    birth: Any = None,
    lang: str = "en",
) -> dict:
    from ask_mr.static_answer import mr_static_answer_payload

    return mr_static_answer_payload(question, kundli, birth=birth, lang=lang)


def _is_bad_batch_fallback(result: Any) -> bool:
    """Detect useless rules fallbacks for MR static partner questions."""
    if not isinstance(result, dict):
        return False
    if _is_bad_marriage_timing_fallback(result):
        return True
    text = str(result.get("text") or "").lower()
    topic = str(result.get("topic") or "").strip().lower()
    source = str(result.get("source") or "").strip().lower()
    if source == "rules" and topic in ("general", "marriage"):
        return True
    return any(
        marker in text
        for marker in (
            "transformative period",
            "stay focused on your goals",
            "trust the process and be patient",
            "period of growth and self-reflection",
        )
    )


def _mr_static_batch_answer(
    question: str,
    kundli: Any,
    *,
    birth: Any = None,
    lang: str = "en",
) -> dict:
    q = (question or "").strip()
    if not isinstance(kundli, dict) or not kundli.get("planets"):
        return {
            "text": "Partner commitment answer ke liye kundli zaroori hai — profile chart save karke phir try karein.",
            "topic": "static",
            "confidence": 0.0,
            "source": "batch_kundli_missing",
            "follow_ups": [],
            "engine_tag": "ans-cosmo",
        }
    try:
        return _mr_engine_only_fallback(q, kundli, birth=birth, lang=lang)
    except Exception as exc:
        print(f"[ask/batch] mr_static_batch_answer failed: {exc}", flush=True)
        return {
            "text": "Partner commitment answer abhi generate nahi ho paya — thodi der baad try karein.",
            "topic": "static",
            "confidence": 0.0,
            "source": "mr_engine_error",
            "follow_ups": [],
            "engine_tag": "ans-cosmo",
        }


def _batch_fallback_answer(
    question: str,
    kundli: Any,
    lang: str,
    birth: Any,
    history: list | None,
    preferred_language: str | None,
    reply_idx: int = 0,
) -> dict:
    """Batch fallback — MR static engine, never marriage-timing or generic rules."""
    q = (question or "").strip()
    is_mr_static = False
    try:
        from ask_marriage_relationship_slice import is_marriage_relationship_static_question

        is_mr_static = bool(is_marriage_relationship_static_question(q))
    except Exception as exc:
        print(f"[ask/batch] mr static detect failed: {exc}", flush=True)

    if is_mr_static:
        try:
            from openai_helper import ai_ask, openai_available

            if openai_available() and isinstance(kundli, dict) and kundli.get("planets"):
                try:
                    out = ai_ask(
                        q,
                        kundli,
                        lang,
                        reply_idx,
                        birth=birth,
                        history=history,
                        preferred_language=preferred_language,
                    )
                    if (
                        isinstance(out, dict)
                        and str(out.get("text") or "").strip()
                        and not _is_bad_batch_fallback(out)
                    ):
                        out.setdefault("source", out.get("source") or "ai_fallback")
                        out.setdefault("engine_tag", out.get("engine_tag") or "ans-engine")
                        out.setdefault("topic", out.get("topic") or "static")
                        return out
                except Exception as exc:
                    print(f"[ask/batch] ai_ask fallback failed: {exc}", flush=True)
        except Exception as exc:
            print(f"[ask/batch] openai fallback import failed: {exc}", flush=True)
        return _mr_static_batch_answer(q, kundli, birth=birth, lang=lang)

    from ask_engine import process_ask

    out = process_ask(q, kundli if isinstance(kundli, dict) else None, lang, reply_idx)
    out.setdefault("source", "rules")
    out.setdefault("engine_tag", "ans-cosmo")
    return out


def _is_bad_marriage_timing_fallback(result: Any) -> bool:
    """Detect native marriage-timing fallback accidentally used for static partner Qs."""
    if not isinstance(result, dict):
        return False
    text = str(result.get("text") or "")
    topic = str(result.get("topic") or "").strip().lower()
    source = str(result.get("source") or "").strip().lower()
    haystack = f"{topic}\n{source}\n{text}".lower()
    if topic == "marriage" and "next window" in haystack:
        return True
    return any(
        marker in haystack
        for marker in (
            "marriage promise exists",
            "next window:",
            "dasha ",
            "marriage trigger",
            "ashtakavarga 7th house",
            "sav =",
        )
    )


def _enforce_batch_concise_text(text: str) -> str:
    """Strip 3-section markdown from batch answers — plain short paragraph only."""
    raw = (text or "").strip()
    if not raw:
        return raw
    try:
        from ask_cosmo_narrator import enforce_cosmo_engine_answer

        return enforce_cosmo_engine_answer(raw, concise=True)
    except Exception:
        return raw


def _sanitize_batch_result(
    question: str,
    result: Any,
    kundli: Any,
    birth: Any,
    lang: str,
) -> dict:
    """Never let marriage-timing rules answer MR static batch questions."""
    out = dict(result or {}) if isinstance(result, dict) else {}
    try:
        from ask_marriage_relationship_slice import is_marriage_relationship_static_question

        if (
            is_marriage_relationship_static_question(question or "")
            and _is_bad_batch_fallback(out)
        ):
            print(
                f"[ask/batch] blocked bad rules fallback q={(question or '')[:72]!r}",
                flush=True,
            )
            return _mr_static_batch_answer(question, kundli, birth=birth, lang=lang)
    except Exception as exc:
        print(f"[ask/batch] sanitize skipped: {exc}", flush=True)
    if str(out.get("text") or "").strip():
        out["text"] = _enforce_batch_concise_text(str(out.get("text") or ""))
    return out


def _run_stream_pipeline(
    question: str,
    kundli: Any,
    lang: str,
    birth: Any,
    history: list | None,
    preferred_language: str | None,
    reply_idx: int = 0,
) -> dict:
    from openai_helper import ai_ask, ai_ask_stream, openai_available

    if not openai_available():
        return _batch_fallback_answer(
            question, kundli, lang, birth, history, preferred_language, reply_idx
        )

    try:
        gen = ai_ask_stream(
            question,
            kundli,
            lang,
            reply_idx,
            birth=birth,
            history=history,
            preferred_language=preferred_language,
        )
        first = next(gen)
    except StopIteration:
        first = None
    except Exception:
        first = None
        gen = None

    try:
        if first is None:
            out = ai_ask(
                question,
                kundli,
                lang,
                reply_idx,
                birth=birth,
                history=history,
                preferred_language=preferred_language,
            )
            out.setdefault("source", out.get("source", "ai"))
            out.setdefault("engine_tag", out.get("engine_tag", "ans-cosmo"))
            return _sanitize_batch_result(question, out, kundli, birth, lang)

        if first.get("kind") == "oneshot":
            out = dict(first.get("data") or {})
            out.setdefault("source", out.get("source", "ai"))
            out.setdefault("engine_tag", out.get("engine_tag", "ans-cosmo"))
            return _sanitize_batch_result(question, out, kundli, birth, lang)

        final_evt: dict | None = None
        if gen is not None:
            for evt in itertools.chain([first], gen):
                if evt.get("kind") == "final":
                    final_evt = evt
                    break

        if final_evt is not None:
            # Return full payload so admin_llm_context + engine_trace/checks
            # survive into question_history persistence.
            return _sanitize_batch_result(question, dict(final_evt), kundli, birth, lang)

        out = ai_ask(
            question,
            kundli,
            lang,
            reply_idx,
            birth=birth,
            history=history,
            preferred_language=preferred_language,
        )
        out.setdefault("source", out.get("source", "ai"))
        out.setdefault("engine_tag", out.get("engine_tag", "ans-cosmo"))
        return _sanitize_batch_result(question, out, kundli, birth, lang)
    except Exception as exc:
        print(f"[ask/batch] stream pipeline failed: {exc}", flush=True)
        out = _batch_fallback_answer(
            question, kundli, lang, birth, history, preferred_language, reply_idx
        )
        return _sanitize_batch_result(question, out, kundli, birth, lang)


def run_batch_question(
    *,
    question: str,
    kundli: Any,
    birth: Any,
    lang: str = "en",
    history: list | None = None,
    preferred_language: str | None = None,
    user_id: int | None = None,
) -> dict:
    """One question — same routing/engines as /api/ask/stream."""
    q = (question or "").strip()
    if not q:
        return {
            "text": "",
            "topic": "general",
            "confidence": 0.0,
            "source": "empty_question",
            "follow_ups": [],
            "engine_tag": "ans-cosmo",
        }

    token = _batch_concise_mode.set(True)
    try:
        return _run_batch_question_inner(
            q=q,
            kundli=kundli,
            birth=birth,
            lang=lang,
            history=history,
            preferred_language=preferred_language,
            user_id=user_id,
        )
    finally:
        _batch_concise_mode.reset(token)


def _run_batch_question_inner(
    *,
    q: str,
    kundli: Any,
    birth: Any,
    lang: str,
    history: list | None,
    preferred_language: str | None,
    user_id: int | None,
) -> dict:
    try:
        from ask_question_normalize import prepare_ask_question

        q = prepare_ask_question(q)
    except Exception:
        pass

    # Shortcuts / greetings
    try:
        from shortcuts import resolve_ask_shortcut as _resolve_ask_shortcut

        sc = _resolve_ask_shortcut(q, lang=lang)
    except Exception:
        sc = None
    if not sc:
        try:
            from ask_scope_gate import greeting_shortcut_response as _greet_sc

            sc = _greet_sc(q, lang=lang)
        except Exception:
            sc = None
    if sc:
        return _maybe_ack(dict(sc), q, lang)

    try:
        from ask_language_gate import assess_ask_language, language_refusal_payload

        lv = assess_ask_language(q)
        if not lv.allowed:
            return _maybe_ack(language_refusal_payload(), q, lang)
    except Exception:
        pass

    try:
        from ask_scope_gate import assess_ask_scope, scope_refusal_payload

        sv = assess_ask_scope(q, history)
        if not sv.allowed:
            return _maybe_ack(
                scope_refusal_payload(sv.reason, question=q, lang=lang),
                q,
                lang,
            )
        if getattr(sv, "normalized_question", None):
            q = sv.normalized_question
    except Exception:
        pass

    try:
        from question_length_gate import check_question_length as _qlg_check

        v = _qlg_check(q, lang=lang)
        if getattr(v, "too_long", False):
            return _maybe_ack(v.payload(), q, lang)
    except Exception:
        pass

    try:
        from openai_helper import astro_scope_refusal as _ask_scope_refusal

        hit = _ask_scope_refusal(q, lang, None, history)
        if hit:
            kind, msg = hit
            return _maybe_ack(
                {
                    "text": msg,
                    "topic": "off_topic" if kind == "off_topic" else "ai_meta",
                    "confidence": 1.0,
                    "source": f"scope_guard:{kind}",
                    "follow_ups": [],
                    "engine_tag": "ans-cosmo",
                },
                q,
                lang,
            )
    except Exception:
        pass

    # RAW passthrough parity (same as /api/ask/stream when enabled)
    try:
        from openai_helper import raw_passthrough_ask as _rp_ask
        from openai_helper import raw_passthrough_enabled as _rp_enabled

        if _rp_enabled() and _rp_ask is not None:
            out = _rp_ask(
                q,
                kundli,
                lang,
                birth=birth,
                user_id=user_id,
                history=history,
            )
            return _maybe_ack(out, q, lang)
    except Exception:
        pass

    static = _try_static_engines(q, kundli if isinstance(kundli, dict) else None, birth)
    if static:
        return _maybe_ack(_sanitize_batch_result(q, static, kundli, birth, lang), q, lang)

    try:
        from ask_marriage_relationship_slice import is_marriage_relationship_static_question

        if isinstance(kundli, dict) and is_marriage_relationship_static_question(q):
            out = _run_stream_pipeline(
                q,
                kundli,
                lang,
                birth,
                history,
                preferred_language,
                reply_idx=0,
            )
            out = _sanitize_batch_result(q, out, kundli, birth, lang)
            if not _is_bad_batch_fallback(out):
                return _maybe_ack(out, q, lang)
            return _maybe_ack(_mr_static_batch_answer(q, kundli, birth=birth, lang=lang), q, lang)
    except Exception as exc:
        print(f"[ask/batch] mr-first path skipped: {exc}", flush=True)

    try:
        out = _run_stream_pipeline(
            q,
            kundli,
            lang,
            birth,
            history,
            preferred_language,
            reply_idx=0,
        )
        return _maybe_ack(_sanitize_batch_result(q, out, kundli, birth, lang), q, lang)
    except Exception as exc:
        print(f"[ask/batch] inner pipeline failed: {exc}", flush=True)
        out = _batch_fallback_answer(
            q, kundli, lang, birth, history, preferred_language, reply_idx=0
        )
        return _maybe_ack(_sanitize_batch_result(q, out, kundli, birth, lang), q, lang)


def _cut_child_text(s: str, max_chars: int | None = None) -> str:
    cap = max_chars if max_chars is not None else int(os.environ.get("BATCH_ASK_CHILD_CHARS", "900"))
    s = (s or "").strip()
    if len(s) <= cap:
        return s
    return s[: cap - 1] + "…"


def _batch_item_from_result(idx: int, question: str, result: dict) -> tuple[dict, str]:
    answer_text = str(result.get("text") or "")
    child = {
        "index": idx,
        "question": question,
        "answer": answer_text,
        "topic": result.get("topic"),
        "source": result.get("source"),
        "engine_tag": result.get("engine_tag"),
    }
    if isinstance(result.get("admin_llm_context"), dict):
        child["admin_llm_context"] = result.get("admin_llm_context")
    part = (
        f"### {idx}. {question}\n\n"
        f"Source: {result.get('source')}\nTopic: {result.get('topic')}\nEngine: {result.get('engine_tag')}\n\n"
        f"{_cut_child_text(answer_text)}"
    )
    return child, part


def _fallback_batch_result(
    idx: int,
    question: str,
    exc: Exception | None = None,
    *,
    kundli: Any = None,
    lang: str = "en",
    birth: Any = None,
    history: list | None = None,
    preferred_language: str | None = None,
) -> dict:
    print(f"[ask/batch] item_failed idx={idx} err={exc}", flush=True)
    try:
        return _batch_fallback_answer(
            question,
            kundli,
            lang,
            birth,
            history,
            preferred_language,
            reply_idx=0,
        )
    except Exception:
        return {
            "text": f"Batch item failed (idx {idx}).",
            "topic": "general",
            "confidence": 0.0,
            "source": "batch_item_error",
            "follow_ups": [],
            "engine_tag": "ans-cosmo",
        }


def iter_batch_answers(
    *,
    questions: list[str],
    kundli: Any,
    birth: Any,
    lang: str = "en",
    history: list | None = None,
    preferred_language: str | None = None,
    user_id: int | None = None,
):
    """Yield one batch child at a time (same pipeline as /api/ask/batch)."""
    total = len(questions)
    for idx, q in enumerate(questions, 1):
        print(f"[ask/batch] Q{idx}/{total} q={q[:72]!r}", flush=True)
        try:
            result = run_batch_question(
                question=q,
                kundli=kundli,
                birth=birth,
                lang=lang,
                history=history,
                preferred_language=preferred_language,
                user_id=user_id,
            )
        except Exception as exc:
            result = _fallback_batch_result(
                idx,
                q,
                exc,
                kundli=kundli,
                lang=lang,
                birth=birth,
                history=history,
                preferred_language=preferred_language,
            )
        child, part = _batch_item_from_result(idx, q, result)
        yield {
            "index": idx,
            "total": total,
            "item": child,
            "part": part,
            "admin_llm_context": result.get("admin_llm_context")
            if isinstance(result.get("admin_llm_context"), dict)
            else None,
        }


def build_batch_parent_payload(
    *,
    batch_title: str,
    questions: list[str],
    items: list[dict],
    parts: list[str],
    first_admin_llm_context: dict | None,
    quota_payload: dict,
    plan_payload: str,
) -> dict:
    parent_question_text = f"{batch_title} — {len(questions)} questions"
    parent_text = "\n\n---\n\n".join(parts).strip()
    return {
        "text": parent_text,
        "items": items,
        "topic": "batch",
        "confidence": 1.0,
        "source": "batch_ask",
        "follow_ups": [],
        "engine_tag": "batch-ask",
        "quota": quota_payload,
        "plan": plan_payload,
        "parent_question_text": parent_question_text,
        "first_admin_llm_context": first_admin_llm_context,
    }


def build_batch_admin_context(
    items: list[dict],
    first_admin_llm_context: dict | None,
) -> dict | None:
    """Merge per-question admin traces into one parent admin_llm_context."""
    children: list[dict] = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        child_ctx = it.get("admin_llm_context")
        sm: dict = {}
        checks: dict = {}
        if isinstance(child_ctx, dict):
            sm = child_ctx.get("slice_meta") if isinstance(child_ctx.get("slice_meta"), dict) else {}
            blocks = child_ctx.get("blocks") if isinstance(child_ctx.get("blocks"), dict) else {}
            trace = blocks.get("engine_trace") if isinstance(blocks.get("engine_trace"), dict) else {}
            checks = trace.get("checks") if isinstance(trace.get("checks"), dict) else {}
            if not sm.get("slice"):
                sm = {**sm, "slice": trace.get("engine")}
        children.append(
            {
                "index": it.get("index"),
                "question": it.get("question"),
                "source": it.get("source"),
                "topic": it.get("topic"),
                "engine_tag": it.get("engine_tag"),
                "slice": sm.get("slice"),
                "archetype": sm.get("archetype") or checks.get("archetype"),
                "question_intent": checks.get("question_intent"),
                "compatibility_angle": child_ctx.get("compatibility_angle")
                if isinstance(child_ctx, dict)
                else None,
            }
        )
    if not first_admin_llm_context and not children:
        return None
    merged = dict(first_admin_llm_context or {})
    merged["batch_mode"] = True
    merged["batch_children"] = children
    return merged

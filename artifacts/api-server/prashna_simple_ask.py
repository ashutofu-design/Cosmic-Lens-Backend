"""Prashna Kundli — simple Q&A (separate from Ask Anything).

Personal question → user's D1 + dasha + short LLM paragraph.
General astrology knowledge → knowledge_fast path.
No KP number / horary chart. No raw_passthrough_ask pipeline.
"""
from __future__ import annotations

import os
from typing import Any, Optional


_PERSONAL_SYSTEM = (
    "You answer from the user's birth-chart facts only.\n"
    "Read the user's language (English, Hindi, or Hinglish) and reply in the same language.\n"
    "Give one short simple paragraph that directly answers the question.\n"
    "Do not invent placements missing from the chart facts. No greetings, no lists, no headers.\n"
    "If dasha/timing lines are present, you may use them for WHEN questions; "
    "if they are absent, do not invent dates or dasha periods."
)


def _load_user_kundli(user: Any) -> Optional[dict]:
    try:
        row = getattr(user, "kundli", None)
        raw = getattr(row, "chart_data", None) if row is not None else None
        if not raw:
            return None
        if isinstance(raw, dict):
            return raw
        import json

        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _compact_d1_dasha(kundli: dict, *, include_dasha: bool = False) -> str:
    try:
        from openai_helper import _raw_compact_chart  # type: ignore

        return (
            _raw_compact_chart(
                kundli,
                include_dasha=bool(include_dasha),
                static_dasha_hint=bool(include_dasha),
            )
            or ""
        )
    except Exception as exc:
        print(f"[prashna_simple] compact chart failed: {exc}", flush=True)
        return ""


def _llm_personal_answer(
    question: str,
    chart_text: str,
    *,
    lang: str = "hn",
    is_timing: bool = False,
) -> Optional[str]:
    del lang
    try:
        from openai_helper import _get_client  # type: ignore
    except Exception:
        return None
    client = _get_client()
    if client is None:
        return None
    model = (
        os.environ.get("PRASHNA_SIMPLE_MODEL")
        or os.environ.get("OPENAI_MODEL")
        or "gpt-4.1-mini"
    )
    facts_label = "CHART FACTS (D1 + dasha):" if is_timing else "CHART FACTS (D1):"
    user_content = (
        f"QUESTION:\n{(question or '')[:600]}\n\n"
        f"{facts_label}\n{(chart_text or '')[:4500]}"
    )
    try:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": _PERSONAL_SYSTEM},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.3,
        }
        try:
            resp = client.chat.completions.create(
                **kwargs,
                max_completion_tokens=280,
                timeout=25,
            )
        except TypeError:
            resp = client.chat.completions.create(**kwargs, max_tokens=280)
        text = ((resp.choices[0].message.content or "") if resp.choices else "").strip()
        return text or None
    except Exception as exc:
        print(f"[prashna_simple] personal LLM failed: {exc}", flush=True)
        return None


def ask_prashna_simple(
    question: str,
    *,
    kundli: Optional[dict] = None,
    user: Any = None,
    lang: str = "hn",
    client: Any = None,
) -> dict[str, Any]:
    """Answer one Prashna Kundli question. Never calls Ask Anything pipeline."""
    q = (question or "").strip()
    if not q:
        return {
            "ok": False,
            "error": "question_required",
            "text": "Sawal likhiye.",
            "source": "prashna_simple",
        }

    chart = kundli if isinstance(kundli, dict) and kundli else None
    if chart is None and user is not None:
        chart = _load_user_kundli(user)

    branch = "engine"
    is_timing = False
    try:
        from ask_understand_phase2 import run_understand_phase2

        u = run_understand_phase2(q, client=client, question_raw=q)
        if bool(u.get("ok")):
            branch = str(u.get("branch") or "engine")
            is_timing = bool(u.get("timing")) or str(u.get("question_type") or "") == "timing"
            eff = str(u.get("effective_question") or "").strip()
            if eff:
                q = eff
    except Exception as exc:
        print(f"[prashna_simple] understand skipped: {exc}", flush=True)

    if branch == "knowledge":
        try:
            from ask_knowledge_fast import try_astrology_knowledge_fast_answer

            kf = try_astrology_knowledge_fast_answer(q, lang=lang or "hn", force=True)
            if kf and (kf.get("text") or "").strip():
                return {
                    "ok": True,
                    "text": str(kf["text"]).strip(),
                    "mode": "knowledge",
                    "source": str(kf.get("source") or "knowledge_fast"),
                    "question": q,
                    "timing": False,
                }
        except Exception as exc:
            print(f"[prashna_simple] knowledge failed: {exc}", flush=True)

    if not chart:
        msg = (
            "Personal chart answer ke liye pehle apni kundli save karein. "
            "General jyotish theory ke liye sawal theory style mein poochiye."
            if lang != "en"
            else "Save your birth chart first for a personal answer. "
            "For general Jyotish theory, ask a theory-style question."
        )
        return {
            "ok": False,
            "error": "kundli_required",
            "text": msg,
            "mode": "personal",
            "source": "prashna_simple",
            "question": q,
            "timing": is_timing,
        }

    # D1 always for self; dasha only when Understand says timing.
    chart_text = _compact_d1_dasha(chart, include_dasha=is_timing)
    if not chart_text.strip():
        return {
            "ok": False,
            "error": "chart_empty",
            "text": (
                "Kundli data nahi mil paya. Chart dubara save karke try karein."
                if lang != "en"
                else "Chart data was empty. Please re-save your chart and try again."
            ),
            "mode": "personal",
            "source": "prashna_simple",
            "question": q,
            "timing": is_timing,
        }

    text = _llm_personal_answer(q, chart_text, lang=lang or "hn", is_timing=is_timing)
    if not text:
        return {
            "ok": False,
            "error": "llm_failed",
            "text": (
                "Abhi jawab nahi ban paya. Thodi der baad try karein."
                if lang != "en"
                else "Could not generate an answer right now. Please try again shortly."
            ),
            "mode": "personal",
            "source": "prashna_simple",
            "question": q,
            "timing": is_timing,
        }

    return {
        "ok": True,
        "text": text,
        "mode": "personal",
        "source": "prashna_simple_d1_dasha" if is_timing else "prashna_simple_d1",
        "question": q,
        "timing": is_timing,
    }

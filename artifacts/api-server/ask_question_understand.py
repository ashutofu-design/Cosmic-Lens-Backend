"""Mandatory one-line question understanding — runs for every Ask question."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Optional

_UNDERSTAND_PROMPT = """You read Hindi/Hinglish/English astrology questions.
Return STRICT JSON only:
{"question_summary": "<ONE line plain Hinglish (Roman) — what user wants to know>",
 "understood": true}

Rules for question_summary:
- 12-50 words in ONE line (long multi-part questions: up to 60 words, still one line).
- Cover EVERY sub-part the user asked — do not drop any concern.
- Paraphrase in your own words (not copy-paste only).
- No planet/house/dasha jargon. No answer — only show you understood.
- understood=false only for gibberish / empty / not a real question.

Question:
{question}"""

_TIMEOUT_S = 10


def _summary_is_weak(summary: str, question: str) -> bool:
    s = " ".join((summary or "").split()).strip().lower()
    q = " ".join((question or "").split()).strip().lower()
    if not s or len(s) < 12:
        return True
    if s.startswith("user asked:"):
        return True
    if q and (s == q or q.startswith(s) or s.startswith(q[: min(len(q), len(s))])):
        # Near-verbatim echo — prefer LLM paraphrase for long questions
        return len(q) > 80
    return False


def llm_understand_question(
    question: str,
    *,
    client: Any = None,
    model: Optional[str] = None,
) -> dict[str, Any]:
    """Dedicated cheap LLM call — paraphrase only. Never raises."""
    q = (question or "").strip()
    if not q:
        return {"question_summary": "", "understood": False, "source": "understand_empty"}

    if client is None:
        try:
            from openai_helper import _get_client  # type: ignore

            client = _get_client()
        except Exception as exc:
            return {"question_summary": "", "understood": False, "source": "understand_no_client", "error": str(exc)[:120]}

    if client is None:
        return {"question_summary": "", "understood": False, "source": "understand_no_client"}

    if model is None:
        model = (
            os.environ.get("ASK_UNDERSTAND_MODEL")
            or os.environ.get("ASK_INTENT_MODEL")
            or os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
        )

    t0 = time.time()
    try:
        kwargs = dict(
            model=model,
            temperature=0.1,
            timeout=_TIMEOUT_S,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": _UNDERSTAND_PROMPT.format(question=q)}],
        )
        try:
            resp = client.chat.completions.create(max_completion_tokens=180, **kwargs)
        except TypeError:
            resp = client.chat.completions.create(max_tokens=180, **kwargs)
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)
        summary = str(data.get("question_summary") or "").strip()[:600]
        understood = bool(data.get("understood", True)) and bool(summary)
        return {
            "question_summary": summary,
            "understood": understood,
            "source": "understand_llm",
            "latency_ms": int((time.time() - t0) * 1000),
        }
    except Exception as exc:
        return {
            "question_summary": "",
            "understood": False,
            "source": "understand_error",
            "error": str(exc)[:200],
            "latency_ms": int((time.time() - t0) * 1000),
        }


def ensure_question_understanding(
    question: str,
    intent: dict[str, Any] | None = None,
    *,
    client: Any = None,
    force_llm: bool = False,
) -> dict[str, Any]:
    """Guarantee question_summary + admin understanding lines on every Ask."""
    from ask_intent_fidelity import (
        build_llm_understood_one_liner,
        build_question_understanding_detail,
        summarize_question_one_line,
    )

    q = (question or "").strip()
    out: dict[str, Any] = dict(intent) if isinstance(intent, dict) else {}

    summary = str(out.get("question_summary") or "").strip()
    if force_llm or _summary_is_weak(summary, q):
        extra = llm_understand_question(q, client=client)
        if str(extra.get("question_summary") or "").strip():
            out["question_summary"] = str(extra["question_summary"]).strip()
            out["understanding_source"] = extra.get("source") or "understand_llm"
            if extra.get("latency_ms") is not None:
                out["understand_latency_ms"] = extra["latency_ms"]

    if not str(out.get("question_summary") or "").strip():
        out["question_summary"] = summarize_question_one_line(q, out)
        out.setdefault("understanding_source", "regex_fallback")

    out["interpretation"] = out.get("interpretation") or f'User asked: "{q}"'
    out["question_echo"] = q
    out["question_understood"] = "yes" if q and str(out.get("question_summary") or "").strip() else "no"
    out["understanding_detail"] = build_question_understanding_detail(q, out)
    out["understanding_line"] = build_llm_understood_one_liner(q, out)
    return out


def narrator_intent_hint(question: str, llm_intent: dict[str, Any] | None = None) -> str:
    """Prompt block: LLM must answer this exact understood ask."""
    from ask_intent_fidelity import summarize_question_one_line

    q = (question or "").strip()
    summary = summarize_question_one_line(q, llm_intent)
    if not summary:
        return f'User asked: "{q}"'
    return (
        f"USER ASKED (answer THIS exact concern — do not drift to other topics): "
        f"{summary}"
    )

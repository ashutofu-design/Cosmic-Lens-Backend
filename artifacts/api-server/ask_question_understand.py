"""Mandatory one-line question understanding — runs for every Ask question."""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Optional

_UNDERSTAND_PROMPT = """You read Hindi/Hinglish/English astrology questions WORD BY WORD.
Return STRICT JSON only:
{"question_scope": "<one word>",
 "question_summary": "<ONE line plain Hinglish (Roman)>",
 "understood": true}

question_scope — pick exactly ONE:
love | marriage | partner | couple | career | health | finance | education | children | property | travel | legal | vehicle | spiritual | self | family | general

Scope rules:
- couple = hum/ham dono, dono ke beech, between us (bond of TWO people)
- partner = specific spouse/BF/GF/pati/patni/husband/wife subject
- love = romance/pyaar/attachment without naming a partner person
- marriage = shaadi/vivah/marriage quality or timing
- self = only about native (mera/meri/main/mujhe — NOT partner)
- career = job/naukri/business/promotion
- health = sehat/bimari
- finance = paisa/dhan/wealth/loss
- general = vague or multi-domain overview only

Rules for question_summary:
- Read the FULL question carefully — every clause, every "aur/ya", every contrast (X ya Y).
- If user asks 2–3 things, include ALL in one line (use commas or "aur").
- 15–70 words, ONE line, paraphrase in your own words (not copy-paste only).
- Fix spelling silently (shadii→shaadi, helth→health, nokri→naukri).
- No planet/house/dasha jargon. No answer — only prove you understood.
- understood=false only for gibberish / empty / not a real question.

Question:
{question}"""

_TIMEOUT_S = 12


def _summary_is_weak(summary: str, question: str) -> bool:
    s = " ".join((summary or "").split()).strip().lower()
    q = " ".join((question or "").split()).strip().lower()
    if not s or len(s) < 12:
        return True
    if s.startswith("user asked:"):
        return True
    # Structured regex paraphrase templates — always prefer dedicated understand LLM
    if "user pooch raha hai kya unki kundli me sacha pyaar" in s:
        return True
    if re.match(r"^user ka \w+ se related sawal:", s):
        return True
    # Regex fallback shape: "love: <verbatim question>"
    if re.match(r"^(love|marriage|career|finance|health|education|children|property|travel|litigation|vehicle):\s+", s):
        tail = re.sub(r"^(love|marriage|career|finance|health|education|children|property|travel|litigation|vehicle):\s+", "", s).strip()
        if tail == q or q.startswith(tail) or tail.startswith(q[: min(len(q), len(tail))]):
            return True
    if q and (s == q or q.startswith(s) or s.startswith(q[: min(len(q), len(s))])):
        # Near-verbatim echo — prefer LLM paraphrase for long questions
        return len(q) > 80
    # Long multi-part question but very short summary — re-ask understand LLM
    if q and len(q) > 55:
        q_parts = len(re.findall(r"(?ix)\b(aur|ya|or|and)\b", q))
        if q_parts >= 1 and len(s) < len(q) * 0.45:
            return True
    return False


def _apply_understanding_fields(
    out: dict[str, Any],
    question: str,
    *,
    summary: str,
    scope: str = "",
) -> None:
    from ask_intent_fidelity import (
        format_question_understanding,
        infer_question_scope,
        normalize_question_scope,
        strip_scope_bracket,
    )

    body = strip_scope_bracket(summary)
    sc = normalize_question_scope(scope) if scope else infer_question_scope(question, out)
    out["question_scope"] = sc
    out["question_summary"] = body
    out["question_meaning"] = format_question_understanding(sc, body)


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
            resp = client.chat.completions.create(max_completion_tokens=240, **kwargs)
        except TypeError:
            resp = client.chat.completions.create(max_tokens=240, **kwargs)
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)
        summary = str(data.get("question_summary") or "").strip()[:600]
        scope = str(data.get("question_scope") or "").strip()
        understood = bool(data.get("understood", True)) and bool(summary)
        return {
            "question_summary": summary,
            "question_scope": scope,
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
    question_raw: str = "",
) -> dict[str, Any]:
    """Guarantee question_summary + admin understanding lines on every Ask."""
    from ask_intent_fidelity import (
        build_llm_understood_one_liner,
        build_question_understanding_detail,
        infer_question_scope,
        summarize_question_one_line,
    )

    q = (question or "").strip()
    raw = (question_raw or q).strip()
    out: dict[str, Any] = dict(intent) if isinstance(intent, dict) else {}
    out["question_raw"] = raw
    out["question_normalized"] = q
    out["typo_corrected"] = bool(raw and q and raw.lower() != q.lower())

    summary = str(out.get("question_summary") or "").strip()
    src = str(out.get("understanding_source") or "").strip().lower()
    need_llm = force_llm or src != "understand_llm" or _summary_is_weak(summary, q)
    if need_llm:
        llm_q = q
        if out["typo_corrected"]:
            llm_q = f"{q}\n(Original user text with possible typos: {raw})"
        extra = llm_understand_question(llm_q, client=client)
        if str(extra.get("question_summary") or "").strip():
            _apply_understanding_fields(
                out,
                q,
                summary=str(extra["question_summary"]).strip(),
                scope=str(extra.get("question_scope") or "").strip(),
            )
            out["understanding_source"] = extra.get("source") or "understand_llm"
            if extra.get("latency_ms") is not None:
                out["understand_latency_ms"] = extra["latency_ms"]

    if not str(out.get("question_summary") or "").strip():
        fallback = summarize_question_one_line(q, out, with_scope=False)
        _apply_understanding_fields(
            out,
            q,
            summary=fallback,
            scope=infer_question_scope(q, out),
        )
        out["understanding_source"] = "regex_paraphrase"
    elif not str(out.get("question_meaning") or "").strip():
        _apply_understanding_fields(
            out,
            q,
            summary=str(out.get("question_summary") or "").strip(),
            scope=str(out.get("question_scope") or "").strip(),
        )
    elif not str(out.get("understanding_source") or "").strip():
        out["understanding_source"] = "regex_paraphrase"

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
    summary = summarize_question_one_line(q, llm_intent, with_scope=True)
    if not summary:
        return f'User asked: "{q}"'
    return (
        f"USER ASKED (answer THIS exact concern — do not drift to other topics): "
        f"{summary}"
    )

"""Mandatory question understanding — runs for every Ask question."""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Optional

_UNDERSTAND_PROMPT = """You read Hindi/Hinglish/English astrology questions WORD BY WORD.
Return STRICT JSON only:
{{"question_scope": "<one word>",
 "question_summary": "<explanation text>",
 "understood": true}}

question_scope — pick exactly ONE:
love | marriage | partner | couple | career | health | finance | education | children | property | travel | legal | vehicle | spiritual | self | family | general

Scope rules:
- couple = hum/ham dono, dono ke beech, between us (bond of TWO people)
- partner = specific spouse/BF/GF/pati/patni/husband/wife OR "kis tarah ka partner suit karega"
- love = romance/pyaar/attachment without naming a partner person
- marriage = shaadi/vivah/marriage quality or timing
- self = only about native (mera/meri/main/mujhe — NOT partner)
- career = job/naukri/business/promotion
- health = sehat/bimari/doctor/hospital (NOT partner-fit questions)
- finance = paisa/dhan/wealth/loss
- general = vague or multi-domain overview only

Rules for question_summary — THIS IS THE MAIN TASK:
- Write 2–10 SHORT lines separated by newline (\\n). Plain Hinglish (Roman).
- EXPLAIN what the user wants to know — their intent, subject, and contrast (X ya Y).
- Do NOT repeat, quote, or copy-paste the question. Forbidden: starting with the same words as the question.
- Forbidden: "User ne pucha ki…" / echoing the question back.
- Good pattern:
  Line 1: User kya jaanna chahta hai (core intent)
  Line 2+: kaun sa area (partner/career/self), kis angle se (quality/timing/nature), koi choice/contrast
- Couple / compatibility questions (hamari/hum dono/dono ke beech):
  Name the EXACT angle — personalities | thinking/mindset | values | life goals | expectations |
  emotional | mental | intellectual | general bond. Never mix mental into emotional or vice versa.
- Partner commitment questions (mera partner … serious/casual/loyal/ready/commit):
  Name the EXACT intent — ready for commitment | serious vs casual | long-term | loyal/exclusive |
  time-pass | genuine | effort/responsibility | trust blockers | public vs secret. NOT marriage timing.
- Fix typos silently in your understanding (shadii→shaadi) but do not mention spelling.
- No planet/house/dasha jargon. No astrology answer — only prove you understood the ASK.
- understood=false only for gibberish / empty / not a real question.

Question:
{question}"""

_TIMEOUT_S = 14


def _echoes_question(summary: str, question: str) -> bool:
    """True when summary is mostly a copy of the question — needs real explanation."""
    s = " ".join((summary or "").split()).strip().lower()
    q = " ".join((question or "").split()).strip().lower()
    if not s or not q:
        return True
    if s == q:
        return True
    if len(q) >= 20 and (q in s or s in q):
        return True
    if len(q) >= 12 and (s.startswith(q[: min(len(q), 40)]) or q.startswith(s[: min(len(s), 40)])):
        return True
    q_words = [w for w in re.findall(r"[\w']+", q) if len(w) > 2]
    s_words = set(re.findall(r"[\w']+", s))
    if len(q_words) >= 4:
        overlap = sum(1 for w in q_words if w in s_words) / len(q_words)
        if overlap >= 0.72:
            return True
    return False


def _summary_is_weak(summary: str, question: str) -> bool:
    s = (summary or "").strip()
    q = (question or "").strip()
    if not s or len(s) < 24:
        return True
    if _echoes_question(s, q):
        return True
    if s.startswith("User asked:"):
        return True
    if "user pooch raha hai kya unki kundli me sacha pyaar" in s.lower():
        return True
    if re.match(r"^user ka \w+ se related sawal:", s.lower()):
        return True
    if re.match(
        r"^(love|marriage|career|finance|health|education|children|property|travel|litigation|vehicle):\s+",
        s.lower(),
    ):
        return True
    # Single line with no explanation depth
    if "\n" not in s and len(s) < 50 and len(q) > 30:
        return True
    return False


def _finalize_question_understanding(
    out: dict[str, Any],
    question: str,
    *,
    client: Any = None,
) -> None:
    """Never leave echoed question text as the admin understanding."""
    from ask_intent_fidelity import (
        build_question_explanation_fallback,
        infer_question_scope,
        strip_scope_bracket,
    )

    q = (question or "").strip()
    body = strip_scope_bracket(str(out.get("question_summary") or "")).strip()
    weak = _summary_is_weak(body, q) or _echoes_question(body, q)
    needs_lines = "\n" not in body and len(q) > 35

    if weak or needs_lines:
        extra = llm_understand_question(q, client=client)
        extra_body = strip_scope_bracket(str(extra.get("question_summary") or "")).strip()
        if extra_body and not _echoes_question(extra_body, q) and not _summary_is_weak(extra_body, q):
            _apply_understanding_fields(
                out,
                q,
                summary=extra_body,
                scope=str(extra.get("question_scope") or "").strip(),
            )
            out["understanding_source"] = extra.get("source") or "understand_llm"
            body = extra_body

    body = strip_scope_bracket(str(out.get("question_summary") or "")).strip()
    if _summary_is_weak(body, q) or _echoes_question(body, q) or ("\n" not in body and len(q) > 35):
        fallback = build_question_explanation_fallback(q, out)
        _apply_understanding_fields(
            out,
            q,
            summary=fallback,
            scope=str(out.get("question_scope") or "") or infer_question_scope(q, out),
        )
        src = str(out.get("understanding_source") or "")
        out["understanding_source"] = "explain_repair" if src == "understand_llm" else "regex_explain"

    body = strip_scope_bracket(str(out.get("question_summary") or "")).strip()
    out["question_understood"] = (
        "yes"
        if body and not _echoes_question(body, q) and len(body) >= 24
        else "no"
    )


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
            resp = client.chat.completions.create(max_completion_tokens=520, **kwargs)
        except TypeError:
            resp = client.chat.completions.create(max_tokens=520, **kwargs)
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)
        summary = str(data.get("question_summary") or "").strip().replace("\\n", "\n")[:1800]
        scope = str(data.get("question_scope") or "").strip()
        understood = bool(data.get("understood", True)) and bool(summary) and not _echoes_question(summary, q)
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
        build_question_explanation_fallback,
        build_question_understanding_detail,
        infer_question_scope,
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
        fallback = build_question_explanation_fallback(q, out)
        _apply_understanding_fields(
            out,
            q,
            summary=fallback,
            scope=infer_question_scope(q, out),
        )
        out["understanding_source"] = "regex_explain"
    elif not str(out.get("question_meaning") or "").strip():
        _apply_understanding_fields(
            out,
            q,
            summary=str(out.get("question_summary") or "").strip(),
            scope=str(out.get("question_scope") or "").strip(),
        )
    elif not str(out.get("understanding_source") or "").strip():
        out["understanding_source"] = "regex_paraphrase"

    _finalize_question_understanding(out, q, client=client)

    try:
        from ask_intent_fidelity import infer_compatibility_angle, infer_partner_commitment_angle

        angle = infer_compatibility_angle(q)
        if angle:
            out["compatibility_angle"] = angle
        pc = infer_partner_commitment_angle(q)
        if pc:
            out["partner_commitment_angle"] = pc
    except Exception:
        pass

    out["interpretation"] = out.get("interpretation") or f'User asked: "{q}"'
    out["question_echo"] = q
    out["understanding_detail"] = build_question_understanding_detail(q, out)
    out["understanding_line"] = build_llm_understood_one_liner(q, out)
    return out


def narrator_intent_hint(question: str, llm_intent: dict[str, Any] | None = None) -> str:
    """Prompt block: LLM must answer this exact understood ask."""
    from ask_intent_fidelity import (
        compatibility_angle_label,
        format_question_understanding,
        infer_compatibility_angle,
        infer_partner_commitment_angle,
        infer_question_scope,
        partner_commitment_angle_label,
        strip_scope_bracket,
    )

    q = (question or "").strip()
    li = llm_intent if isinstance(llm_intent, dict) else {}
    body = strip_scope_bracket(str(li.get("question_summary") or "").strip())
    if not body:
        return f'User asked: "{q}"'
    scope = infer_question_scope(q, li)
    summary = format_question_understanding(scope, body)
    angle = str(li.get("compatibility_angle") or "").strip() or infer_compatibility_angle(q)
    hint = (
        f"USER ASKED (answer THIS exact concern — do not drift to other topics):\n"
        f"{summary}"
    )
    if angle:
        hint += (
            f"\n\nEXACT COMPATIBILITY ANGLE: {compatibility_angle_label(angle)}.\n"
            f"Answer ONLY this angle — do NOT answer emotional bond if they asked mental/intellectual, "
            f"and vice versa."
        )
    pc_angle = str(li.get("partner_commitment_angle") or "").strip() or infer_partner_commitment_angle(q)
    if pc_angle:
        hint += (
            f"\n\nEXACT PARTNER COMMITMENT FOCUS: {partner_commitment_angle_label(pc_angle)}.\n"
            f"Answer about PARTNER intent only — do NOT give user marriage timing / dasha windows."
        )
    return hint

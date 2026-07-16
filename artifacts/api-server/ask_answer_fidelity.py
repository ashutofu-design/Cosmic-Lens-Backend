"""Universal post-LLM answer fidelity — verify user got what they asked; retry until pass."""
from __future__ import annotations

import os
import re
from typing import Any, Literal

from ask_intent_fidelity import (
    infer_primary_domain,
    infer_question_scope,
    is_dyadic_couple_question,
    is_partner_relationship_question,
)

AnswerShape = Literal["timing", "yes_no", "which", "compare", "explain", "general"]

_TIMING_Q_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+hoga|kab\s+hogi|when|kis\s+saal|kitne\s+saal|"
    r"timing|muhurat|window|period|date\s+fix"
    r")\b"
)
_TIMING_ANSWER_RX = re.compile(
    r"(?ix)\b("
    r"\d{4}|20[2-9]\d|"
    r"january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec|"
    r"mahadasha|antardasha|pratyantar|dasha|"
    r"\d{1,2}\s*[-–]\s*\d{1,2}|"
    r"\d{4}\s*[-–→]\s*\d{2,4}|"
    r"saal|mahine|months?|weeks?"
    r")\b"
)
_YES_NO_Q_RX = re.compile(
    r"(?ix)\b("
    r"kya|kyaa|suit|suitable|better|acha|achha|achhi|possible|ban\s+sakta|ban\s+sakti|"
    r"milega|milegi|hoga\?|hogi\?|should\s+i|can\s+i|will\s+i"
    r")\b"
)
_YES_NO_ANSWER_RX = re.compile(
    r"(?ix)\b("
    r"haan|han|ji\b|yes|no|nahi|nahin|"
    r"mushkil|difficult|possible|likely|unlikely|"
    r"suitable|unsuitable|better|worse|"
    r"ban\s+sakte|nahi\s+ban|recommend|avoid|wait|ruk|defer|"
    r"milega|nahi\s+milega|hoga|nahi\s+hoga|"
    r"strong|weak|moderate|favourable|unfavourable"
    r")\b"
)
_WHICH_Q_RX = re.compile(
    r"(?ix)\b("
    r"kaun\s+sa|kaun\s+si|kis\s+type|which|konsa|konsi|kya\s+field|kya\s+line|"
    r"best\s+for|sabse\s+acha"
    r")\b"
)
_COMPARE_Q_RX = re.compile(r"(?ix)(\b(?:ya|or|aur)\b|\bvs\.?\b|versus|better\s+or)")
_BANNED_LABEL_RX = re.compile(
    r"(?ix)(seedha\s*jawab\s*:|conclusion\s*:|निष्कर्ष\s*:|verdict\s*:)"
)
_STOPWORDS = frozenset({
    "kya", "kyaa", "kab", "when", "mera", "meri", "mere", "main", "mein", "mujhe",
    "hoga", "hogi", "hai", "the", "and", "for", "with", "about", "from", "that",
    "this", "what", "how", "why", "will", "can", "should",
})


def fidelity_enabled() -> bool:
    # Phase 1: default OFF — narrator output must not be repaired/rewritten.
    return os.environ.get("ANSWER_FIDELITY_ENABLED", "false").strip().lower() in (
        "1", "true", "yes", "on",
    )


def fidelity_max_attempts() -> int:
    try:
        n = int(os.environ.get("ANSWER_FIDELITY_MAX_ATTEMPTS", "3"))
    except Exception:
        n = 3
    return max(1, min(5, n))


def infer_answer_shape(
    question: str,
    llm_intent: dict[str, Any] | None = None,
    *,
    is_timing: bool = False,
) -> AnswerShape:
    li = llm_intent if isinstance(llm_intent, dict) else {}
    q = (question or "").strip()
    if is_timing or bool(li.get("routed_timing")) or _TIMING_Q_RX.search(q):
        return "timing"
    if _WHICH_Q_RX.search(q):
        return "which"
    if _COMPARE_Q_RX.search(q) and not _TIMING_Q_RX.search(q):
        return "compare"
    if _YES_NO_Q_RX.search(q):
        return "yes_no"
    if re.search(r"(?ix)\b(kyun|kyon|why|kaise|how|explain|reason)\b", q):
        return "explain"
    return "general"


def _topic_tokens(question: str) -> list[str]:
    raw = re.findall(r"[a-zA-Z\u0900-\u097F]{4,}", (question or "").lower())
    out: list[str] = []
    for tok in raw:
        if tok in _STOPWORDS:
            continue
        if tok not in out:
            out.append(tok)
    return out[:8]


def _engine_timing_anchors(meta: dict[str, Any]) -> list[str]:
    anchors: list[str] = []
    for key in ("primary_window", "answer_window"):
        v = meta.get(key)
        if v:
            anchors.append(str(v))
    dt = meta.get("dasha_trace") if isinstance(meta.get("dasha_trace"), dict) else {}
    for key in (
        "next_career_start", "next_career_end", "current_lords",
        "promotion_timeline",
    ):
        v = dt.get(key)
        if v:
            anchors.append(str(v))
    periods = meta.get("promotion_periods")
    if isinstance(periods, list):
        anchors.extend(str(p) for p in periods[:3] if p)
    return anchors


def _anchor_in_answer(anchor: str, answer_lower: str) -> bool:
    a = (anchor or "").lower()
    if not a:
        return False
    for yr in re.findall(r"20\d{2}", a):
        if yr in answer_lower:
            return True
    for ym in re.findall(r"20\d{2}-\d{2}", a):
        if ym in answer_lower:
            return True
    for lord in re.findall(r"[A-Za-z]{3,}", a):
        if len(lord) >= 4 and lord.lower() in answer_lower:
            return True
    return False


def _run_domain_verify(
    question: str,
    answer: str,
    meta: dict[str, Any],
    *,
    user_intent: str = "",
) -> list[str]:
    """Delegate to per-domain verify_* when slice is known."""
    slice_id = str(meta.get("slice") or "")
    meta2 = {**meta, "user_intent": user_intent or meta.get("user_intent") or ""}
    issues: list[str] = []
    try:
        if slice_id in ("career_engine_v1", "career_timing_v1"):
            from ask_career.answer_guard import verify_career_answer, verify_career_timing_answer

            if slice_id == "career_timing_v1":
                ok, dom_issues = verify_career_timing_answer(question, answer, meta2)
            else:
                ok, dom_issues = verify_career_answer(question, answer, meta2)
            if not ok:
                issues.extend(dom_issues)
        elif slice_id == "finance_engine_v1":
            from ask_finance.answer_guard import verify_finance_answer

            ok, dom_issues = verify_finance_answer(question, answer, meta2)
            if not ok:
                issues.extend(dom_issues)
        elif slice_id == "health_engine_v1":
            from ask_health.answer_guard import verify_health_answer

            ok, dom_issues = verify_health_answer(question, answer, meta2)
            if not ok:
                issues.extend(dom_issues)
    except Exception:
        pass
    return issues


def verify_answer_fidelity(
    question: str,
    answer: str,
    *,
    llm_intent: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
    user_intent: str = "",
    is_timing: bool = False,
) -> tuple[bool, list[str], float, dict[str, Any]]:
    """
    Rule-based: did the answer match what the user asked?
    Returns (ok, issues, score 0..1, detail).
    """
    text = (answer or "").strip()
    q = (question or "").strip()
    meta = meta if isinstance(meta, dict) else {}
    issues: list[str] = []
    detail: dict[str, Any] = {}

    if not text:
        return False, ["empty_answer"], 0.0, {"shape": "general"}
    if len(text) < 12:
        issues.append("too_short")

    shape = infer_answer_shape(q, llm_intent, is_timing=is_timing)
    detail["shape"] = shape
    detail["scope"] = infer_question_scope(q, llm_intent)
    txt_lower = text.lower()

    if _BANNED_LABEL_RX.search(text):
        issues.append("template_labels")

    issues.extend(_run_domain_verify(q, text, meta, user_intent=user_intent))

    if not is_timing:
        try:
            from ask_mr.timing_registry import has_explicit_timing_anchor

            if not has_explicit_timing_anchor(q) and re.search(
                r"(?ix)\b(20[2-9]\d)\b", text
            ):
                issues.append("static_answer_year_leak")
        except Exception:
            pass

    if shape == "timing":
        anchors = _engine_timing_anchors(meta)
        has_period = bool(_TIMING_ANSWER_RX.search(text))
        has_anchor = any(_anchor_in_answer(a, txt_lower) for a in anchors)
        if not has_period and not has_anchor:
            issues.append("timing_question_no_period")
        if re.search(r"(?ix)\b(bcp\s+age|bcp\s+ages)\b", text):
            issues.append("timing_answer_used_bcp_not_dasha")

    elif shape == "yes_no":
        if not _YES_NO_ANSWER_RX.search(text):
            issues.append("yes_no_question_no_clear_signal")
        try:
            from ask_mr.timing_registry import (
                has_explicit_timing_anchor,
                is_mr_static_question,
            )

            if (
                not is_timing
                and is_mr_static_question(q)
                and not has_explicit_timing_anchor(q)
                and _TIMING_ANSWER_RX.search(text)
            ):
                issues.append("static_promise_year_leak")
        except Exception:
            pass

    elif shape == "which":
        tokens = _topic_tokens(q)
        if tokens and not any(t in txt_lower for t in tokens[:4]):
            issues.append("which_question_topic_missing")

    elif shape == "compare":
        if not (_YES_NO_ANSWER_RX.search(text) or re.search(r"(?ix)\b(job|business|naukri|dhandha)\b", text)):
            issues.append("compare_question_no_pick")

    else:
        tokens = _topic_tokens(q)
        if tokens and not any(t in txt_lower for t in tokens[:3]):
            issues.append("topic_not_addressed")

    scope = detail["scope"]
    if scope == "partner" and is_partner_relationship_question(q):
        if re.search(r"(?ix)\b(apki?\s+sehat|your\s+health|aapki?\s+tabiyat)\b", text):
            if not re.search(r"(?ix)\b(partner|spouse|pati|patni|biwi)\b", text):
                issues.append("partner_question_native_health_drift")
    if scope in ("love", "marriage", "partner", "couple") and infer_primary_domain(q) == "career":
        if re.search(r"(?ix)\b(promotion|naukri|salary|boss)\b", q):
            pass
        elif re.search(r"(?ix)\b(promotion|naukri|salary)\b", text) and not re.search(
            r"(?ix)\b(love|marriage|rishta|partner)\b", q
        ):
            issues.append("domain_drift_career_in_non_career_q")

    checks_run = 6
    fails = len(set(issues))
    score = round(max(0.0, (checks_run - fails) / checks_run), 3)
    ok = len(issues) == 0
    detail["issues"] = list(issues)
    detail["score"] = score
    return ok, issues, score, detail


def _repair_prompt(
    *,
    question: str,
    answer: str,
    issues: list[str],
    shape: str,
    meta: dict[str, Any],
    user_intent: str,
    reply_lang: str,
) -> list[dict[str, str]]:
    lang_note = (
        "Reply in Hinglish (Roman)."
        if (reply_lang or "").lower() in ("hn", "hi-en")
        else "Reply in simple English."
    )
    verdict = str(meta.get("verdict") or "")
    strategy = ""
    if meta.get("summary"):
        strategy = str((meta.get("summary") or [""])[0])
    primary = str(meta.get("primary_window") or meta.get("answer_window") or "")
    shape_rules = {
        "timing": (
            "User asked TIMING (kab/when). Answer MUST include a concrete period "
            "(month/year or dasha lords + window). Use engine PRIMARY window only — "
            "not BCP ages. Do not dodge with only generic advice."
        ),
        "yes_no": (
            "User asked yes/no / suitability. Start with clear haan/nahi / suitable / "
            "not suitable — then one line why."
            + (
                " Do NOT mention calendar years, months, or dasha windows — user asked "
                "promise/yog only, not kab/when."
                if "static_promise_year_leak" in issues
                else ""
            )
        ),
        "which": (
            "User asked WHICH type/field. Name 1-2 specific picks from the question topic."
        ),
        "compare": (
            "User compared two options. Pick one side or explain trade-off clearly."
        ),
        "explain": "Answer the why/how directly in plain language.",
        "general": "Answer exactly what user asked — stay on their topic.",
    }
    if "static_answer_year_leak" in issues or "static_promise_year_leak" in issues:
        shape_rules["yes_no"] = (
            "User asked yes/no / promise (NOT kab/when). "
            "No calendar years or month windows — only tendency from chart."
        )
        shape_rules["general"] = shape_rules["yes_no"]
    user_msg = f"""USER QUESTION (answer THIS exactly):
{question}

What user wants: {user_intent or question}
Answer shape: {shape}
Rule: {shape_rules.get(shape, shape_rules['general'])}

ENGINE VERDICT (do not contradict): {verdict or '—'}
STRATEGY: {strategy or '—'}
PRIMARY TIMING (if timing Q): {primary or '—'}

FAILED CHECKS: {", ".join(issues)}

DRAFT (fix all failed checks):
{answer}

Rewrite in 2-4 short sentences. No template labels (Seedha jawab, Conclusion, Verdict).
{lang_note}"""

    return [
        {
            "role": "system",
            "content": (
                "You fix astrology answers so they match the user's exact question. "
                "Engine facts are locked. Plain language only."
            ),
        },
        {"role": "user", "content": user_msg},
    ]


def guard_answer_with_fidelity_loop(
    client: Any,
    model: str,
    *,
    question: str,
    answer: str,
    llm_intent: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
    user_intent: str = "",
    reply_lang: str = "hn",
    is_timing: bool = False,
) -> tuple[str, dict[str, Any]]:
    """
    Verify answer vs user question; LLM repair loop until pass or max attempts.
    """
    meta = dict(meta or {})
    text = (answer or "").strip()
    max_attempts = fidelity_max_attempts()
    shape = infer_answer_shape(question, llm_intent, is_timing=is_timing)

    out: dict[str, Any] = {
        "guard": "answer_fidelity_v1",
        "shape": shape,
        "attempts": 0,
        "ok": False,
        "issues": [],
        "score": None,
        "repairs": [],
        "max_attempts": max_attempts,
    }

    if not fidelity_enabled():
        out["skipped"] = "env_disabled"
        out["ok"] = True
        return text, out

    if not text or text.startswith("Maaf kijiye"):
        out["skipped"] = "refusal_or_empty"
        out["ok"] = True
        return text, out

    for attempt in range(max_attempts):
        ok, issues, score, detail = verify_answer_fidelity(
            question,
            text,
            llm_intent=llm_intent,
            meta=meta,
            user_intent=user_intent,
            is_timing=is_timing,
        )
        out["attempts"] = attempt + 1
        out["issues"] = issues
        out["score"] = score
        out["detail"] = detail
        if ok:
            out["ok"] = True
            return text, out

        if attempt >= max_attempts - 1:
            break

        try:
            messages = _repair_prompt(
                question=question,
                answer=text,
                issues=issues,
                shape=str(detail.get("shape") or shape),
                meta=meta,
                user_intent=user_intent,
                reply_lang=reply_lang,
            )
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=int(os.environ.get("ANSWER_FIDELITY_MAX_TOKENS", "280")),
            )
            fixed = (resp.choices[0].message.content or "").strip()
            if fixed:
                out["repairs"].append({
                    "attempt": attempt + 1,
                    "issues": list(issues),
                    "chars": len(fixed),
                })
                text = fixed
        except Exception as exc:
            out["repairs"].append({
                "attempt": attempt + 1,
                "error": str(exc)[:120],
            })
            break

    out["ok"] = False
    out["exhausted"] = True
    return text, out

"""Post-LLM guard: career answer must match user question + engine verdict."""
from __future__ import annotations

import re
from typing import Any

_BANNED_LABEL_RX = re.compile(
    r"(?ix)(seedha\s*jawab\s*:|conclusion\s*:|निष्कर्ष\s*:|verdict\s*:)"
)
_PHASED_JOB_BIZ_RX = re.compile(
    r"(?ix)(pehle\s+job|job\s+pehle|phir\s+business|baad\s+me\s+business|experience\s+lekar\s+business)"
)
_JOB_WORD_RX = re.compile(r"(?ix)\b(job|naukri|employment|salary\s*career)\b")
_BIZ_WORD_RX = re.compile(r"(?ix)\b(business|dhandha|vyapaar|self[\s-]?employ|apna\s*kaam)\b")


def verify_career_answer(
    question: str,
    answer: str,
    meta: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Return (ok, issue_codes). Pure Python — no LLM."""
    issues: list[str] = []
    text = (answer or "").strip()
    q = (question or "").strip()
    if not text:
        return False, ["empty_answer"]

    if _BANNED_LABEL_RX.search(text):
        issues.append("template_labels")

    archetype = str(meta.get("archetype") or "")
    verdict = str(meta.get("verdict") or "").lower()
    checks = meta.get("checks") or {}
    job_pct = checks.get("job_pct")
    biz_pct = checks.get("business_pct")

    if archetype == "job_vs_business":
        if not (_JOB_WORD_RX.search(text) or _BIZ_WORD_RX.search(text)):
            issues.append("no_job_or_business_pick")

        employment_strong = (
            "employment path stronger" in verdict
            or (isinstance(job_pct, int) and isinstance(biz_pct, int) and job_pct >= biz_pct + 15)
        )
        business_strong = (
            "business/self-employment path stronger" in verdict
            or (isinstance(job_pct, int) and isinstance(biz_pct, int) and biz_pct >= job_pct + 15)
        )
        hybrid = "hybrid career" in verdict

        if employment_strong and not hybrid and _PHASED_JOB_BIZ_RX.search(text):
            issues.append("invented_phased_path")
        if employment_strong and not hybrid and not _JOB_WORD_RX.search(text):
            issues.append("verdict_job_but_no_job_in_answer")
        if business_strong and not hybrid and not _BIZ_WORD_RX.search(text):
            issues.append("verdict_business_but_no_business_in_answer")

        # User asked A vs B — answer should not dodge both without a lean.
        if re.search(r"(?ix)\b(job|naukri).{0,20}\b(business|dhandha)\b", q) or re.search(
            r"(?ix)\b(business|dhandha).{0,20}\b(job|naukri)\b", q
        ):
            if employment_strong and _BIZ_WORD_RX.search(text) and not _JOB_WORD_RX.search(text):
                issues.append("question_job_vs_biz_mismatch")

    # Generic: question keywords should echo if obvious career pick question.
    if re.search(r"(?ix)\b(suit|better|sahi|achha|achhi)\b", q):
        if len(text.split()) < 8:
            issues.append("too_short_for_suitability_q")

    return (len(issues) == 0, issues)


def repair_career_answer(
    client: Any,
    model: str,
    *,
    question: str,
    draft: str,
    meta: dict[str, Any],
    user_intent: str,
    reply_lang: str,
    issues: list[str],
) -> str:
    """One cheap rewrite when verify_career_answer failed."""
    archetype = meta.get("archetype") or "career"
    verdict = meta.get("verdict") or ""
    evidence = meta.get("evidence") or []
    ev_lines = "\n".join(f"- {e}" for e in evidence[:5])
    lang_note = (
        "Reply in Hindi (Devanagari)."
        if (reply_lang or "").lower() == "hi"
        else "Reply in Hinglish (Roman)."
        if (reply_lang or "").lower() in ("hn", "hi-en")
        else "Reply in simple English."
    )

    user_msg = f"""USER QUESTION (answer THIS exactly):
{question}

What user wants: {user_intent or question}

ENGINE VERDICT (must match — do not contradict):
{verdict}

ENGINE EVIDENCE (use 1-2 lines only, plain words):
{ev_lines}

DRAFT (failed checks: {", ".join(issues)}):
{draft}

Rewrite in 2-3 short sentences.
- Sentence 1: direct answer to user's question (job OR business OR hybrid per VERDICT).
- Sentence 2: WHY from chart evidence in plain life language (career mode / structure / independence).
- If VERDICT says employment stronger: say job/naukri suits — do NOT say "pehle job phir business".
- If VERDICT says hybrid: both viable is OK.
- NO labels: Seedha jawab, Conclusion, Verdict.
{lang_note}"""

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.2,
            max_tokens=160,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You fix astro career answers. Match user question + engine verdict. "
                        "No planet/house jargon. No section labels."
                    ),
                },
                {"role": "user", "content": user_msg},
            ],
        )
        fixed = (resp.choices[0].message.content or "").strip()
        return fixed or draft
    except Exception:
        return draft


def guard_career_answer(
    client: Any,
    model: str,
    *,
    question: str,
    answer: str,
    meta: dict[str, Any],
    user_intent: str = "",
    reply_lang: str = "hn",
) -> tuple[str, dict[str, Any]]:
    """Verify draft; repair once if needed. Returns (final_text, guard_meta)."""
    ok, issues = verify_career_answer(question, answer, meta)
    guard_meta = {"ok": ok, "issues": issues, "repaired": False}
    if ok:
        return answer, guard_meta

    fixed = repair_career_answer(
        client,
        model,
        question=question,
        draft=answer,
        meta=meta,
        user_intent=user_intent,
        reply_lang=reply_lang,
        issues=issues,
    )
    ok2, issues2 = verify_career_answer(question, fixed, meta)
    guard_meta["repaired"] = True
    guard_meta["ok_after_repair"] = ok2
    guard_meta["issues_after_repair"] = issues2
    return (fixed if fixed else answer), guard_meta

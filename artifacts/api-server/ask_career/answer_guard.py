"""Post-LLM guard: career answer must match user question + engine verdict."""
from __future__ import annotations

import re
from typing import Any

from .routing import (
    is_creativity_career_question,
    is_dedicated_job_question,
    is_govt_job_question,
    is_job_vs_business_question,
    is_milestone_question,
    is_specific_sector_suitability_question,
    is_vocational_question,
    is_which_business_question,
)
from .job_registry import JOB_ENGINE_ARCHETYPES

_BANNED_LABEL_RX = re.compile(
    r"(?ix)(seedha\s*jawab\s*:|conclusion\s*:|निष्कर्ष\s*:|verdict\s*:)"
)
_PHASED_JOB_BIZ_RX = re.compile(
    r"(?ix)(pehle\s+job|job\s+pehle|phir\s+business|baad\s+me\s+business|experience\s+lekar\s+business)"
)
_JOB_WORD_RX = re.compile(r"(?ix)\b(job|naukri|employment|salary\s*career)\b")
_BIZ_WORD_RX = re.compile(r"(?ix)\b(business|dhandha|vyapaar|self[\s-]?employ|apna\s*kaam)\b")
_WHICH_BIZ_ANSWER_RX = re.compile(
    r"(?ix)\b("
    r"commerce|trading|partnership|retail|wholesale|consulting|manufacturing|online|"
    r"real\s*estate|food|restaurant|service|public\s*deal|sales|marketing|import|export|"
    r"startup|family\s*business|digital|tech|finance|media|creative|kshetra|sector|"
    r"dhandha|vyapaar|field|line|type|business\s+type|hospitality|cafe|catering|hotel"
    r")\b"
)
_JOB_BIZ_SPLIT_ANSWER_RX = re.compile(
    r"(?ix)(\d+\s*%|~\s*\d+|employment\s+path|job\s+path|naukri\s+zyada|"
    r"job\s+zyada|business\s+scope|employment\s+ya\s+job|structured\s+professional)"
)
_CREATIVITY_ANSWER_RX = re.compile(
    r"(?ix)\b(youtube|youtuber|content|creator|influencer|vlogger|creative|media|ban\s+sakta|suit)\b"
)


def verify_career_answer(
    question: str,
    answer: str,
    meta: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Return (ok, issue_codes). Pure Python — no LLM."""
    issues: list[str] = []
    text = (answer or "").strip()
    q = (question or "").strip()
    user_intent = str(meta.get("user_intent") or "")
    if not text:
        return False, ["empty_answer"]

    if _BANNED_LABEL_RX.search(text):
        issues.append("template_labels")

    archetype = str(meta.get("archetype") or "")
    verdict = str(meta.get("verdict") or "").lower()
    checks = meta.get("checks") or {}
    job_pct = checks.get("job_pct")
    biz_pct = checks.get("business_pct")
    which_biz_q = is_which_business_question(q, user_intent)
    sector_suit_q = is_specific_sector_suitability_question(q, user_intent)
    creativity_q = is_creativity_career_question(q, user_intent)
    vocational_q = is_vocational_question(q, user_intent)
    govt_job_q = is_govt_job_question(q, user_intent)
    dedicated_job_q = is_dedicated_job_question(q, user_intent)
    milestone_q = is_milestone_question(q, user_intent)

    if (govt_job_q or dedicated_job_q) and not which_biz_q and _JOB_BIZ_SPLIT_ANSWER_RX.search(text):
        if not re.search(
            r"(?ix)\b(govt|government|sarkari|doctor|medical|software|it|pilot|ca|lawyer|"
            r"teacher|engineer|bank|army|defence|naukri|job|profession|field|line)\b",
            text,
        ):
            issues.append("dedicated_job_but_job_split_answer")

    if archetype in JOB_ENGINE_ARCHETYPES.union({"govt_job"}) and (govt_job_q or dedicated_job_q):
        if not re.search(
            r"(?ix)\b(govt|government|sarkari|doctor|medical|software|it|pilot|ca|lawyer|"
            r"teacher|engineer|bank|army|defence|naukri|profession|field|line|suit)\b",
            text,
        ):
            issues.append("dedicated_job_no_direct_answer")

    if which_biz_q:
        if archetype == "job_vs_business":
            issues.append("wrong_engine_job_vs_biz_for_which_business")
        if _JOB_BIZ_SPLIT_ANSWER_RX.search(text) and not _WHICH_BIZ_ANSWER_RX.search(text):
            issues.append("which_business_but_job_split_answer")
        if not _WHICH_BIZ_ANSWER_RX.search(text):
            issues.append("no_business_type_named")

    if sector_suit_q and not which_biz_q and not creativity_q and not vocational_q and not milestone_q and not govt_job_q and not dedicated_job_q:
        if _JOB_BIZ_SPLIT_ANSWER_RX.search(text):
            issues.append("sector_suit_but_job_split_answer")

    if archetype == "career_milestones" and milestone_q:
        if _JOB_BIZ_SPLIT_ANSWER_RX.search(text):
            issues.append("milestone_but_job_split_answer")

    if archetype == "vocational_trade" and vocational_q:
        if _JOB_BIZ_SPLIT_ANSWER_RX.search(text) and not re.search(
            r"(?ix)\b(electrician|plumber|mechanic|trade|vocational|skill)\b", text
        ):
            issues.append("vocational_but_job_split_answer")

    if archetype == "sector_fit" and which_biz_q and not _WHICH_BIZ_ANSWER_RX.search(text):
        issues.append("sector_fit_no_type_named")

    if archetype == "creativity_innovation" and creativity_q:
        if _JOB_BIZ_SPLIT_ANSWER_RX.search(text) and not _CREATIVITY_ANSWER_RX.search(text):
            issues.append("creativity_but_job_split_answer")
        if not _CREATIVITY_ANSWER_RX.search(text):
            issues.append("creativity_no_direct_answer")

    if archetype == "job_vs_business" and is_job_vs_business_question(q):
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

        if re.search(r"(?ix)\b(job|naukri).{0,20}\b(business|dhandha)\b", q) or re.search(
            r"(?ix)\b(business|dhandha).{0,20}\b(job|naukri)\b", q
        ):
            if employment_strong and _BIZ_WORD_RX.search(text) and not _JOB_WORD_RX.search(text):
                issues.append("question_job_vs_biz_mismatch")

    if re.search(r"(?ix)\b(suit|better|sahi|achha|achhi)\b", q) and not which_biz_q:
        if len(text.split()) < 8:
            issues.append("too_short_for_suitability_q")

    return (len(issues) == 0, issues)


_TIMING_Q_RX = re.compile(
    r"(?ix)\b(kab|kab\s+hoga|kab\s+hogi|when|kis\s+saal|kitna\s+time|timing|window)\b"
)
_RED_POSITIVE_SWITCH_RX = re.compile(
    r"(?ix)\b("
    r"favourable.*switch|switch.*favourable|good time to switch|abhi switch|switch abhi|"
    r"actively (?:apply|interview)|change kar le|change kar lo|"
    r"green signal|go ahead.*change|interview shuru"
    r")\b"
)
_GREEN_DEFER_RX = re.compile(
    r"(?ix)\b(wait\s+\d|ruk\s+ja|defer|avoid switch|risk hai|stable role)\b"
)
_DASHA_WORD_RX = re.compile(r"(?ix)\b(mahadasha|antardasha|dasha|md\b|ad\b)\b")


def verify_career_timing_answer(
    question: str,
    answer: str,
    meta: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Timing Q: verdict + strategy + dasha must align with engine (no LLM drift)."""
    issues: list[str] = []
    text = (answer or "").strip()
    q = (question or "").strip()
    if not text or not _TIMING_Q_RX.search(q):
        return True, []

    verdict = str(meta.get("verdict") or "").lower()
    strategy = ""
    if meta.get("summary"):
        strategy = str((meta.get("summary") or [""])[0])
    dasha_trace = meta.get("dasha_trace") if isinstance(meta.get("dasha_trace"), dict) else {}

    if verdict == "red_avoid":
        if _RED_POSITIVE_SWITCH_RX.search(text):
            issues.append("red_verdict_but_positive_switch")
        if not _GREEN_DEFER_RX.search(text) and not re.search(
            r"(?ix)\b(ruk|wait|defer|risk|stable|consolidat|patience)\b", text
        ):
            issues.append("red_verdict_missing_wait_signal")
    elif verdict == "green_go":
        if re.search(r"(?ix)\b(abhi switch mat|avoid change|ruk ja|wait karo)\b", text):
            issues.append("green_verdict_but_defer_language")

    if strategy:
        if "4-6" in strategy and not re.search(r"(?ix)\b(4|5|6|char)\s*(-\s*)?(4|5|6|char)?\s*mah", text):
            if not re.search(r"(?ix)\b(mahine|months?)\b", text):
                issues.append("strategy_wait_window_missing")

    lords = str(dasha_trace.get("current_lords") or "")
    if lords and lords != "—":
        parts = [p.strip() for p in lords.replace("/", "-").split("-") if p.strip()]
        md = parts[0] if parts else ""
        if md and md.lower() not in text.lower():
            if not _DASHA_WORD_RX.search(text):
                issues.append("dasha_not_cited_in_answer")

    try:
        from ask_career.timing_reply import window_dates_present_in_text

        aw = meta.get("answer_window") if isinstance(meta.get("answer_window"), dict) else {}
        start = aw.get("start")
        end = aw.get("end")
        if not start and meta.get("primary_window"):
            pw = str(meta.get("primary_window") or "")
            if "→" in pw:
                bits = [b.strip() for b in pw.split("→", 1)]
                start, end = bits[0][:7], bits[1][:7] if len(bits) > 1 else ""
        if (start or end) and not window_dates_present_in_text(text, start, end):
            issues.append("primary_window_missing")
    except Exception:
        pass

    return (len(issues) == 0, issues)


def guard_career_timing_answer(
    client: Any,
    model: str,
    *,
    question: str,
    answer: str,
    meta: dict[str, Any],
    user_intent: str = "",
    reply_lang: str = "hn",
) -> tuple[str, dict[str, Any]]:
    """Verify timing answer vs engine; one repair if drift detected."""
    meta_check = {**(meta or {}), "user_intent": user_intent}
    ok, issues = verify_career_timing_answer(question, answer, meta_check)
    guard_meta = {"ok": ok, "issues": issues, "repaired": False, "guard": "career_timing_v1"}
    if ok:
        return answer, guard_meta

    strategy = str((meta.get("summary") or [""])[0])
    verdict = str(meta.get("verdict") or "")
    dasha = meta.get("dasha_trace") or {}
    timing_ev = meta.get("timing_evidence") or meta.get("evidence") or []
    ev_lines = "\n".join(f"- {e}" for e in timing_ev[:6])
    locked_window = str(meta.get("locked_answer_window") or meta.get("primary_window") or "").strip()
    aw = meta.get("answer_window") if isinstance(meta.get("answer_window"), dict) else {}
    if aw.get("start") or aw.get("end"):
        locked_window = locked_window or f"{aw.get('start')} → {aw.get('end')}"
    lang_note = (
        "Reply in Hinglish (Roman)."
        if (reply_lang or "").lower() in ("hn", "hi-en")
        else "Reply in simple English."
    )
    user_msg = f"""USER QUESTION (timing — when will job change happen):
{question}

ENGINE VERDICT (do NOT change): {verdict}
LOCKED ANSWER WINDOW (user ko YAHIN period bolo — doosra mat banao): {locked_window or '—'}
LOCKED STRATEGY (embed meaning, natural words):
{strategy}

CURRENT DASHA: {dasha.get('current_lords') or '—'}
NEXT CAREER AD: {dasha.get('next_career_ad') or '—'} ({dasha.get('next_career_start')} → {dasha.get('next_career_end')})

TIMING EVIDENCE:
{ev_lines}

DRAFT (fix issues {issues}):
{answer}

{lang_note}
Rewrite in 2-3 sentences. Must match VERDICT. LOCKED ANSWER WINDOW dates must appear naturally.
If red_avoid → say wait/defer, NOT favourable switch.
Mention current dasha lord if given. No template labels."""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You fix career TIMING answers. Engine verdict is locked. "
                        "Do not contradict dasha/strategy."
                    ),
                },
                {"role": "user", "content": user_msg},
            ],
            max_tokens=220,
        )
        fixed = (resp.choices[0].message.content or "").strip()
        ok2, issues2 = verify_career_timing_answer(question, fixed, meta_check)
        guard_meta["repaired"] = True
        guard_meta["ok_after_repair"] = ok2
        guard_meta["issues_after_repair"] = issues2
        if not ok2:
            try:
                from ask_career.timing_reply import compose_promotion_timing_reply

                verdict_stub = {
                    "bucket": meta.get("archetype") or meta_check.get("checks", {}).get("bucket"),
                    "primary_window": meta.get("primary_window"),
                    "promotion_engine": {"timing": {"windows": []}},
                    "timing_window": {
                        "next_career": {
                            "start": aw.get("start"),
                            "end": aw.get("end"),
                            "lords": aw.get("lords"),
                        }
                    },
                }
                if str(verdict_stub.get("bucket") or "") == "promotion":
                    locked = compose_promotion_timing_reply(
                        verdict_stub, question, lang=reply_lang,
                    )
                    if locked:
                        fixed = locked
            except Exception:
                pass
        return (fixed if fixed else answer), guard_meta
    except Exception:
        return answer, guard_meta


def _repair_instructions(
    *,
    archetype: str,
    issues: list[str],
    which_biz_q: bool,
    sector_suit_q: bool,
    creativity_q: bool,
    vocational_q: bool = False,
    milestone_q: bool = False,
    govt_job_q: bool = False,
) -> str:
    if milestone_q or archetype == "career_milestones":
        return (
            "Rewrite in 2-3 short sentences.\n"
            "- Sentence 1: direct answer to promotion/interview/job-change/exam/side-hustle question per VERDICT.\n"
            "- Sentence 2: WHY from chart evidence in plain life language.\n"
            "- Do NOT give job vs business % split.\n"
            "- NO labels: Seedha jawab, Conclusion, Verdict."
        )
    if vocational_q or archetype == "vocational_trade":
        return (
            "Rewrite in 2-3 short sentences.\n"
            "- Sentence 1: direct haan/nahi for the skilled trade asked (electrician, plumber, etc.) per VERDICT.\n"
            "- Sentence 2: WHY from Mars/Saturn/Mercury craft evidence.\n"
            "- Do NOT give job vs business % split.\n"
            "- NO labels: Seedha jawab, Conclusion, Verdict."
        )
    if creativity_q or archetype == "creativity_innovation":
        return (
            "Rewrite in 2-3 short sentences.\n"
            "- Sentence 1: direct haan/nahi — can user become YouTuber/content creator per VERDICT.\n"
            "- Sentence 2: WHY from chart evidence (communication, audience, creative axis).\n"
            "- Do NOT give job vs business % split.\n"
            "- NO labels: Seedha jawab, Conclusion, Verdict."
        )
    if which_biz_q:
        return (
            "Rewrite in 2-3 short sentences.\n"
            "- Sentence 1: name 1-2 BEST business TYPES/FIELDS for the user "
            "(e.g. commerce, partnership/public dealing, trading, consulting) per VERDICT + EVIDENCE.\n"
            "- Sentence 2: WHY from chart evidence in plain life language.\n"
            "- Do NOT give job vs business % split — user asked WHICH business, not job OR business.\n"
            "- NO labels: Seedha jawab, Conclusion, Verdict."
        )
    if govt_job_q or dedicated_job_q or archetype in JOB_ENGINE_ARCHETYPES.union({"govt_job"}):
        return (
            "Rewrite in 2-3 short sentences.\n"
            "- Sentence 1: direct haan/nahi for the SPECIFIC job/profession user asked per VERDICT.\n"
            "- Sentence 2: WHY from chart evidence in plain life language.\n"
            "- Do NOT give job vs business % split. Do NOT promise selection date.\n"
            "- NO labels: Seedha jawab, Conclusion, Verdict."
        )
    if sector_suit_q or archetype == "sector_fit":
        return (
            "Rewrite in 2-3 short sentences.\n"
            "- Sentence 1: direct haan/nahi for the SPECIFIC sector/business user asked "
            "(food business, IT, govt, etc.) per VERDICT.\n"
            "- Sentence 2: WHY from chart evidence in plain life language.\n"
            "- Do NOT give job vs business % split — user did NOT ask job OR business.\n"
            "- NO labels: Seedha jawab, Conclusion, Verdict."
        )
    return (
        "Rewrite in 2-3 short sentences.\n"
        "- Sentence 1: direct answer to user's question (job OR business OR hybrid per VERDICT).\n"
        "- Sentence 2: WHY from chart evidence in plain life language (career mode / structure / independence).\n"
        "- If VERDICT says employment stronger: say job/naukri suits — do NOT say 'pehle job phir business'.\n"
        "- If VERDICT says hybrid: both viable is OK.\n"
        "- NO labels: Seedha jawab, Conclusion, Verdict."
    )


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
    intent = user_intent or str(meta.get("user_intent") or "")
    which_biz_q = is_which_business_question(question, intent)
    sector_suit_q = is_specific_sector_suitability_question(question, intent)
    creativity_q = is_creativity_career_question(question, intent)
    vocational_q = is_vocational_question(question, intent)
    milestone_q = is_milestone_question(question, intent)
    govt_job_q = is_govt_job_question(question, intent)
    dedicated_job_q = is_dedicated_job_question(question, intent)
    lang_note = (
        "Reply in Hindi (Devanagari)."
        if (reply_lang or "").lower() == "hi"
        else "Reply in Hinglish (Roman)."
        if (reply_lang or "").lower() in ("hn", "hi-en")
        else "Reply in simple English."
    )
    body = _repair_instructions(
        archetype=str(archetype),
        issues=issues,
        which_biz_q=which_biz_q,
        sector_suit_q=sector_suit_q,
        creativity_q=creativity_q,
        vocational_q=vocational_q,
        milestone_q=milestone_q,
        govt_job_q=govt_job_q or dedicated_job_q,
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

{body}
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
    if (meta or {}).get("slice") == "career_timing_v1":
        return guard_career_timing_answer(
            client,
            model,
            question=question,
            answer=answer,
            meta=meta,
            user_intent=user_intent,
            reply_lang=reply_lang,
        )
    meta_check = {**(meta or {}), "user_intent": user_intent}
    ok, issues = verify_career_answer(question, answer, meta_check)
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
    ok2, issues2 = verify_career_answer(question, fixed, meta_check)
    guard_meta["repaired"] = True
    guard_meta["ok_after_repair"] = ok2
    guard_meta["issues_after_repair"] = issues2
    return (fixed if fixed else answer), guard_meta

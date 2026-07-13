"""LLM judge — semantic match of health answer vs full Question DNA contract.

Primary gate: did the answer address what the user actually asked (user_wants,
intent, normalized_question)? Secondary: answer_style + answer_approach.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

_JUDGE_JSON_RX = re.compile(r"\{[\s\S]*\}")

_QUESTION_TYPE_HINTS: dict[str, str] = {
    "cause": "User asked WHY — answer must explain reason/cause for the specific situation.",
    "timing": "User asked WHEN — lead with timing window; do not ignore timing ask.",
    "decision": "User asked should I / karu ya nahi — balanced guidance, not random health dump.",
    "current_state": "User asked what is happening NOW — present-state read required.",
    "risk": "User asked about risk/possibility — cautious probability, not certainty.",
    "remedy": "User asked what to do / upay — practical steps expected.",
    "prediction": "User asked what will happen — direct prediction stance on the asked topic.",
    "general": "Answer the specific health topic asked; no unrelated overview.",
}


def health_dna_judge_enabled() -> bool:
    return (os.environ.get("ASK_HEALTH_DNA_JUDGE") or "1").strip() != "0"


def health_dna_judge_model(default: str = "gpt-4.1-mini") -> str:
    return (os.environ.get("ASK_HEALTH_DNA_JUDGE_MODEL") or default).strip() or default


def _parse_judge_json(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        return {}
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError:
        pass
    m = _JUDGE_JSON_RX.search(text)
    if not m:
        return {}
    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError:
        return {}


def _contract_has_signal(contract: dict[str, str], question: str) -> bool:
    if (question or "").strip():
        return True
    return any(str(contract.get(k) or "").strip() for k in (
        "user_wants", "intent", "normalized_question",
        "answer_approach", "answer_style", "question_type",
    ))


def build_health_dna_judge_prompt(
    *,
    question: str,
    answer: str,
    contract: dict[str, str],
) -> str:
    """Build judge user message — exported for tests."""
    style = str(contract.get("answer_style") or "").strip()
    plan = str(contract.get("answer_approach") or "").strip()
    user_wants = str(contract.get("user_wants") or "").strip()
    intent = str(contract.get("intent") or "").strip()
    normalized = str(contract.get("normalized_question") or question or "").strip()
    q_type = str(contract.get("question_type") or "").strip().lower()
    domain = str(contract.get("domain") or "").strip()
    bucket = str(contract.get("bucket") or "").strip()
    type_hint = _QUESTION_TYPE_HINTS.get(q_type, "")

    return f"""You are a strict QA judge for Vedic HEALTH answers. You do NOT predict astrology.
You ONLY check whether the CANDIDATE ANSWER matches what the user asked (Question DNA).

=== PRIMARY — user question alignment (MUST pass all) ===
NORMALIZED QUESTION (what user asked):
{normalized or "—"}

USER INTENT (Question DNA):
{intent or "—"}

USER WANTS (Question DNA — full decode of what user needs):
{user_wants or "—"}

QUESTION TYPE: {q_type or "—"}
{f"TYPE RULE: {type_hint}" if type_hint else ""}

DOMAIN/BUCKET: {domain or "—"} / {bucket or "—"}

RAW USER MESSAGE (reference):
{question.strip() or "—"}

FAIL PRIMARY if:
- Answer does NOT directly address user_wants + intent + normalized_question.
- Answer adds topics user did NOT ask (money/paisa/kharcha, career/job, unrelated 8th/Rahu/chronic
  when user asked a specific cause like travel+health only).
- Answer is a generic health overview when user asked a specific why/how/when question.
- Answer avoids the core question or answers a different question.

=== SECONDARY — style and plan ===
REQUIRED ANSWER STYLE: {style or "—"}
(style: short_2_3_lines = 2-3 sentences; short_paragraph = 4-6 lines; detailed_explain = deeper)

REQUIRED LLM ANSWER PLAN:
{plan or "—"}

FAIL SECONDARY only if clear mismatch with style length or plan structure/tone.

=== CANDIDATE ANSWER ===
{answer.strip()}

OTHER RULES:
- General overview plan → fail planet laundry lists, vitality /100, heavy H1/H8 jargon.
- Surgery/operation risk → pass cautious probability; fail guaranteed yes/no, dates/muhurat.
- Plan forbids remedies → fail upay/mantra content.
- Minor wording differences OK; fail clear off-topic or wrong-question answers.

pass=true ONLY when PRIMARY passes; SECONDARY should pass too when contract specifies style/plan.

Return STRICT JSON only:
{{"pass": true|false, "issues": ["short_code", ...], "fix_hint": "Rewrite hint in 1-3 sentences"}}"""


def llm_judge_health_dna_alignment(
    client: Any,
    model: str,
    *,
    question: str,
    answer: str,
    contract: dict[str, str],
) -> tuple[bool, list[str], str, dict[str, Any]]:
    """
    LLM semantic QA: does answer match full Question DNA (question first, then style/plan)?
    Returns (ok, issue_codes, fix_hint, audit_fragment).
    """
    audit: dict[str, Any] = {"judge": "health_dna_v2", "enabled": True}
    contract = dict(contract or {})

    if not _contract_has_signal(contract, question):
        audit["skipped"] = "no_dna_contract"
        return True, [], "", audit

    if not (answer or "").strip():
        return False, ["dna_judge_empty_answer"], "Write a complete answer.", audit

    judge_model = health_dna_judge_model(model)
    user_msg = build_health_dna_judge_prompt(
        question=question,
        answer=answer,
        contract=contract,
    )

    try:
        resp = client.chat.completions.create(
            model=judge_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You output STRICT JSON only. You judge whether the answer matches "
                        "the user's question (Question DNA). You never rewrite the full answer."
                    ),
                },
                {"role": "user", "content": user_msg},
            ],
            temperature=0.0,
            max_tokens=280,
        )
        raw = (resp.choices[0].message.content or "").strip()
        parsed = _parse_judge_json(raw)
        audit["raw"] = raw[:500]
        audit["parsed"] = parsed
        audit["contract_keys"] = [k for k, v in contract.items() if str(v or "").strip()]
        passed = bool(parsed.get("pass"))
        issues = [
            str(i).strip()
            for i in (parsed.get("issues") or [])
            if str(i).strip()
        ]
        if not passed and not issues:
            issues = ["dna_judge_mismatch"]
        fix_hint = str(parsed.get("fix_hint") or "").strip()
        audit["passed"] = passed
        audit["issues"] = issues
        return passed, issues, fix_hint, audit
    except Exception as exc:
        audit["error"] = str(exc)[:180]
        audit["passed"] = None
        # Judge failure must not block — deterministic rules still apply
        return True, [], "", audit

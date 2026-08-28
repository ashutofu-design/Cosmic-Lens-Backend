"""LLM judge — semantic match of relationship answer vs Question DNA contract.

Primary gate: did the answer address what the user actually asked (user_wants,
intent, normalized_question)? Secondary: answer_style + answer_approach.
Health-parallel for mr_engine_v1 / relationship_engine_execution_v1.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

_JUDGE_JSON_RX = re.compile(r"\{[\s\S]*\}")

_QUESTION_TYPE_HINTS: dict[str, str] = {
    "cause": "User asked WHY — answer must explain reason/cause for the specific relationship situation.",
    "timing": "User asked WHEN — lead with timing; do not ignore timing ask (timing engines handle windows).",
    "decision": "User asked should I / karu ya nahi — balanced guidance, not random relationship dump.",
    "current_state": "User asked what is happening NOW — present-state bond read required.",
    "risk": "User asked about risk/possibility — cautious probability, not certainty.",
    "remedy": "User asked what to do / upay — practical steps expected.",
    "prediction": "User asked what will happen — direct stance on the asked relationship topic.",
    "general": "Answer the specific relationship topic asked; no unrelated overview.",
}


def relationship_dna_judge_enabled() -> bool:
    return (os.environ.get("ASK_MR_DNA_JUDGE") or "0").strip() != "0"


def relationship_dna_judge_model(default: str = "gpt-4.1-mini") -> str:
    return (os.environ.get("ASK_MR_DNA_JUDGE_MODEL") or default).strip() or default


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


def build_relationship_dna_judge_prompt(
    *,
    question: str,
    answer: str,
    contract: dict[str, str],
) -> str:
    style = str(contract.get("answer_style") or "").strip()
    plan = str(contract.get("answer_approach") or "").strip()
    user_wants = str(contract.get("user_wants") or "").strip()
    intent = str(contract.get("intent") or "").strip()
    normalized = str(contract.get("normalized_question") or question or "").strip()
    q_type = str(contract.get("question_type") or "").strip().lower()
    domain = str(contract.get("domain") or "").strip()
    bucket = str(contract.get("bucket") or "").strip()
    type_hint = _QUESTION_TYPE_HINTS.get(q_type, "")

    return f"""You are a strict QA judge for Vedic RELATIONSHIP / LOVE / MARRIAGE answers.
You do NOT predict astrology. You ONLY check whether the CANDIDATE ANSWER matches
what the user asked (Question DNA).

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
- Answer adds topics user did NOT ask (career/job, money/paisa, unrelated health)
  when user asked a specific relationship angle (loyalty / commitment / partner nature).
- Answer is a generic relationship overview when user asked a specific why/how question.
- Answer avoids the core question or answers a different question.
- For non-overview asks: answer has NO chart proof at all (no planet/house/dignity
  cite tied to the reason). Fail with issue "missing_question_proof". Soft overview OK without cites.

=== SECONDARY — style and plan ===
REQUIRED ANSWER STYLE: {style or "—"}
(style: short_2_3_lines = 2-3 sentences; short_paragraph = 4-6 lines; detailed_explain = deeper)

REQUIRED LLM ANSWER PLAN:
{plan or "—"}

FAIL SECONDARY only if clear mismatch with style length or plan structure/tone.

=== CANDIDATE ANSWER ===
{answer.strip()}

OTHER RULES:
- Manglik questions → calm yes/no + soft reason; fail doom absolutism.
- Loyalty / trust → address trust/cheat angle asked; fail unrelated career dump.
- Plan forbids remedies → fail upay/mantra content.
- Minor wording differences OK; fail clear off-topic or wrong-question answers.

pass=true ONLY when PRIMARY passes; SECONDARY should pass too when contract specifies style/plan.

Return STRICT JSON only:
{{"pass": true|false, "issues": ["short_code", ...], "fix_hint": "Rewrite hint in 1-3 sentences"}}"""


def llm_judge_relationship_dna_alignment(
    client: Any,
    model: str,
    *,
    question: str,
    answer: str,
    contract: dict[str, str],
) -> tuple[bool, list[str], str, dict[str, Any]]:
    audit: dict[str, Any] = {"judge": "relationship_dna_v1", "enabled": True}
    contract = dict(contract or {})

    if not _contract_has_signal(contract, question):
        audit["skipped"] = "no_dna_contract"
        return True, [], "", audit

    if not (answer or "").strip():
        return False, ["dna_judge_empty_answer"], "Write a complete answer.", audit

    judge_model = relationship_dna_judge_model(model)
    user_msg = build_relationship_dna_judge_prompt(
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
        return True, [], "", audit


def build_relationship_dna_judge_display(
    question: str,
    answer: str,
    meta: dict[str, Any],
    stored_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from ask_health.answer_validator import _enrich_dna_contract, _resolve_dna_contract

    audit = stored_audit if isinstance(stored_audit, dict) else {}
    contract = _resolve_dna_contract(meta)
    if not contract and question:
        contract = _enrich_dna_contract(dict(meta), question)
    judge_audit = audit.get("dna_judge") if isinstance(audit.get("dna_judge"), dict) else {}
    if not judge_audit and audit.get("judge"):
        judge_audit = audit

    fix_hint = str(audit.get("fix_hint") or "").strip()
    if not fix_hint:
        fix_hint = str((judge_audit.get("parsed") or {}).get("fix_hint") or "").strip()

    passed = judge_audit.get("passed")
    if passed is None:
        passed = audit.get("passed")
    enabled = judge_audit.get(
        "enabled", audit.get("enabled", relationship_dna_judge_enabled())
    )
    issues = list(audit.get("issues") or judge_audit.get("issues") or [])

    contract_summary = dict(audit.get("contract") or {})
    if not contract_summary:
        contract_summary = {
            k: contract[k]
            for k in (
                "normalized_question", "intent", "user_wants", "question_type",
                "domain", "bucket", "answer_style", "answer_approach",
            )
            if contract.get(k)
        }

    judge_version = judge_audit.get("judge") or "relationship_dna_v1"
    judge_notes: list[str] = []
    if passed is None and answer:
        # No stored LLM verdict — free deterministic check so verdict is never "—".
        try:
            from ask_selected_blocks_common import deterministic_dna_judge

            det = deterministic_dna_judge(question or "", answer or "", contract_summary)
            passed = det.get("passed")
            issues = list(det.get("issues") or [])
            judge_notes = list(det.get("notes") or [])
            judge_version = "deterministic_v1 (no LLM)"
        except Exception:
            pass

    return {
        "applies": True,
        "enabled": enabled,
        "passed": passed if passed is not None else True,
        "issues": issues,
        "fix_hint": fix_hint or None,
        "contract": contract_summary,
        "judge_version": judge_version,
        "judge_notes": judge_notes,
        "contract_keys": list(judge_audit.get("contract_keys") or contract_summary.keys()),
        "skipped": judge_audit.get("skipped"),
        "error": judge_audit.get("error"),
        "source": "live_audit" if audit else "recomputed",
    }


def run_relationship_llm_with_dna_judge(
    client: Any,
    *,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    question: str,
    meta: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Narrator LLM + DNA judge. Soft one-shot rewrite if proof missing; never hard-blocks."""
    from ask_health.answer_validator import _enrich_dna_contract
    from ask_mr.answer_guard import guard_relationship_answer

    audit: dict[str, Any] = {
        "mode": "dna_judge_only",
        "enabled": relationship_dna_judge_enabled(),
        "attempts": 1,
        "passed": True,
        "issues": [],
    }

    resp = client.chat.completions.create(
        model=model, messages=messages, max_tokens=max_tokens,
    )
    text = (resp.choices[0].message.content or "").strip()
    text, guard_meta = guard_relationship_answer(question, text, meta)
    audit["guard"] = guard_meta

    contract = _enrich_dna_contract(meta, question)
    audit["contract"] = {
        k: contract[k]
        for k in (
            "normalized_question", "intent", "user_wants", "question_type",
            "domain", "bucket", "answer_style", "answer_approach",
        )
        if contract.get(k)
    }

    try:
        from ask_mr.selected_blocks import build_relationship_selected_blocks

        audit["selected_blocks"] = build_relationship_selected_blocks(
            question, text, meta=meta,
        )
    except Exception as exc:
        audit["selected_blocks"] = {
            "applies": True,
            "source": "relationship_engine_execution",
            "error": str(exc)[:120],
        }

    if relationship_dna_judge_enabled():
        ok_j, j_issues, fix_hint, j_audit = llm_judge_relationship_dna_alignment(
            client,
            model,
            question=question,
            answer=text,
            contract=contract,
        )
        audit["dna_judge"] = j_audit
        audit["passed"] = ok_j if j_audit.get("passed") is not None else True
        audit["issues"] = list(j_issues)
        if fix_hint:
            audit["fix_hint"] = fix_hint

        issues_l = [str(x).lower() for x in j_issues]
        needs_proof = (not ok_j) and any(
            "missing_question_proof" in x or "missing_chart_proof" in x or "no chart proof" in x
            for x in issues_l
        )
        if needs_proof:
            hint = (fix_hint or "").strip() or (
                "Add 1 natural chart proof for the asked question: cite #1 QUESTION_PRIORITY_FACTS "
                "(planet + house/dignity). Keep answer short; no planet dump."
            )
            retry_msgs = list(messages) + [
                {"role": "assistant", "content": text},
                {
                    "role": "user",
                    "content": (
                        "Rewrite: user ke sawal ka 1 natural chart proof add karo "
                        f"(planet + ghar/dignity). Fix: {hint}"
                    ),
                },
            ]
            try:
                resp2 = client.chat.completions.create(
                    model=model, messages=retry_msgs, max_tokens=max_tokens,
                )
                text2 = (resp2.choices[0].message.content or "").strip()
                if text2:
                    text2, guard_meta2 = guard_relationship_answer(question, text2, meta)
                    audit["guard"] = guard_meta2
                    text = text2
                    audit["attempts"] = 2
                    audit["proof_retry"] = True
                    ok2, iss2, hint2, j2 = llm_judge_relationship_dna_alignment(
                        client, model, question=question, answer=text, contract=contract,
                    )
                    audit["dna_judge"] = j2
                    audit["passed"] = ok2 if j2.get("passed") is not None else True
                    audit["issues"] = list(iss2)
                    if hint2:
                        audit["fix_hint"] = hint2
                    try:
                        from ask_mr.selected_blocks import build_relationship_selected_blocks

                        audit["selected_blocks"] = build_relationship_selected_blocks(
                            question, text, meta=meta,
                        )
                    except Exception:
                        pass
            except Exception as exc:
                audit["proof_retry_error"] = str(exc)[:120]
    else:
        audit["dna_judge"] = {"enabled": False, "skipped": "ASK_MR_DNA_JUDGE=0"}

    return text, audit

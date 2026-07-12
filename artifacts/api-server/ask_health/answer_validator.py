"""Health LLM answer validator — question match + JSON facts + retry loop."""

from __future__ import annotations

import os
import re
from typing import Any

from .answer_guard import verify_health_answer
from .chart_proof import (
    answer_cites_chart_proof,
    answer_honest_low_tension,
    chart_support_signals,
    proof_retry_hint,
    validate_chart_proof_requirement,
)
from .classifier import classify_health_archetype

_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
_PLANET_IN_HOUSE_RX = re.compile(
    r"(?ix)\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b"
    r".{0,40}?\b(?:house|ghar|h)\s*(\d{1,2})\b"
)
_SECTION_HEADER_RX = re.compile(
    r"(?ix)(the\s+big\s+picture|kyun\s+aisa|ab\s+kya\s+karein|seedha\s+jawab)"
)
_ACTION_RX = re.compile(
    r"(?ix)\b(karo|karein|rakho|dhyan|rest|doctor|checkup|routine|avoid|kam|zyada|try|follow)\b"
)
_SIMPLE_Q_RX = re.compile(
    r"(?ix)^(mujhse|meri|mera|mujhe|kya\s+karu|kya\s+karein|kaise|kyun|kya\s+ho)\b"
)

_ARCH_ANSWER_HINTS: dict[str, re.Pattern[str]] = {
    "respiratory_health": re.compile(
        r"(?ix)(sardi|thand|khansi|saans|breath|chest|cold|zukam|immune|nose|nin|flu)"
    ),
    "immune_health": re.compile(
        r"(?ix)(immun|baar\s*baar|weak|vitality|rog|tendency|care|rest)"
    ),
    "heart_blood_pressure": re.compile(
        r"(?ix)(bp|blood\s*pressure|heart|dil|circulat|pressure)"
    ),
    "mental_stress": re.compile(r"(?ix)(stress|tension|anxiety|mann|mind|sleep|neend)"),
    "chronic_tendency": re.compile(r"(?ix)(chronic|purani|lamba|baar|tendency|weak)"),
    "digestive_health": re.compile(r"(?ix)(digest|pet|stomach|acidity|gas|liver)"),
    "general_health": re.compile(
        r"(?ix)(sehat|health|tendency|constitution|vitality|weak|strong|care|zone)"
    ),
    "preventive_risk": re.compile(r"(?ix)(risk|tendency|weak|care|monitor|prevent)"),
    "overall_vitality": re.compile(r"(?ix)(vitality|energy|sehat|strong|weak|constitution)"),
}


def health_validator_enabled() -> bool:
    return (os.environ.get("ASK_HEALTH_VALIDATOR") or "1").strip() != "0"


def health_validator_max_retries() -> int:
    try:
        return max(0, min(3, int(os.environ.get("ASK_HEALTH_VALIDATOR_RETRIES", "2"))))
    except (TypeError, ValueError):
        return 2


def _execution_from_meta(meta: dict[str, Any]) -> dict[str, Any]:
    checks = meta.get("checks") if isinstance(meta.get("checks"), dict) else {}
    pack = checks.get("health_engine_execution")
    if isinstance(pack, dict) and pack:
        return pack
    return {
        "d1": checks.get("d1_health_facts") or {},
        "d9": checks.get("d9_health_facts") or {},
    }


def _planet_house_map(execution: dict[str, Any]) -> dict[str, set[int]]:
    out: dict[str, set[int]] = {}
    for chart_key in ("d1", "d9"):
        chart = execution.get(chart_key) if isinstance(execution.get(chart_key), dict) else {}
        if chart.get("error"):
            continue
        for row in chart.get("planets") or []:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip().lower()
            house = int(row.get("house") or 0)
            if name and house:
                out.setdefault(name, set()).add(house)
    return out


def _chart_signs(execution: dict[str, Any]) -> set[str]:
    signs: set[str] = set()
    for chart_key in ("d1", "d9"):
        chart = execution.get(chart_key) if isinstance(execution.get(chart_key), dict) else {}
        asc = str(chart.get("ascendant") or "").strip().lower()
        if asc:
            signs.add(asc)
        for row in chart.get("planets") or []:
            if isinstance(row, dict):
                sign = str(row.get("sign") or "").strip().lower()
                if sign:
                    signs.add(sign)
    return signs


def validate_health_llm_answer(
    question: str,
    answer: str,
    meta: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Return (ok, issue_codes) for release gate."""
    issues: list[str] = []
    text = (answer or "").strip()
    q = (question or "").strip()

    ok_safe, safe_issues = verify_health_answer(q, text, meta)
    if not ok_safe:
        issues.extend(safe_issues)

    if _SECTION_HEADER_RX.search(text):
        issues.append("template_sections")

    archetype = str(meta.get("archetype") or classify_health_archetype(q) or "")
    hint_rx = _ARCH_ANSWER_HINTS.get(archetype) or _ARCH_ANSWER_HINTS.get("general_health")
    if hint_rx and not hint_rx.search(text):
        issues.append("question_drift")

    if re.search(r"(?ix)\bkya\s+kar", q) and not _ACTION_RX.search(text):
        issues.append("missing_action_guidance")

    if _SIMPLE_Q_RX.search(q) and len(text.split()) > 110:
        issues.append("answer_too_long")

    execution = _execution_from_meta(meta)
    planet_houses = _planet_house_map(execution)
    allowed_signs = _chart_signs(execution)

    for name in _PLANET_NAMES:
        if re.search(rf"\b{re.escape(name)}\b", text, re.IGNORECASE):
            if name.lower() not in planet_houses:
                issues.append(f"invented_planet:{name}")

    for match in _PLANET_IN_HOUSE_RX.finditer(text):
        planet = str(match.group(1) or "").strip().lower()
        house = int(match.group(2) or 0)
        houses = planet_houses.get(planet) or set()
        if houses and house not in houses:
            issues.append(f"wrong_house:{match.group(1)}:H{house}")

    for sign in allowed_signs:
        if not sign or len(sign) < 3:
            continue
        sign_title = sign.title()
        if re.search(rf"\b{re.escape(sign_title)}\b", text, re.IGNORECASE):
            continue
    # Signs in answer not in chart (common hallucination)
    for raw_sign in (
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ):
        if re.search(rf"\b{raw_sign}\b", text, re.IGNORECASE):
            if raw_sign.lower() not in allowed_signs:
                issues.append(f"invented_sign:{raw_sign}")
                break

    ok_proof, proof_issues = validate_chart_proof_requirement(q, text, archetype, execution)
    if not ok_proof:
        issues.extend(proof_issues)

    return len(issues) == 0, issues


def build_health_validator_display(
    question: str,
    answer: str,
    meta: dict[str, Any],
    stored_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Structured validator audit for admin observability."""
    ok, issues = validate_health_llm_answer(question, answer, meta)
    text = (answer or "").strip()
    q = (question or "").strip()

    ok_safe, safe_issues = verify_health_answer(q, text, meta)
    tpl_ok = not _SECTION_HEADER_RX.search(text)
    archetype = str(meta.get("archetype") or classify_health_archetype(q) or "")
    hint_rx = _ARCH_ANSWER_HINTS.get(archetype) or _ARCH_ANSWER_HINTS.get("general_health")
    drift_ok = not hint_rx or bool(hint_rx.search(text))
    action_ok = not re.search(r"(?ix)\bkya\s+kar", q) or bool(_ACTION_RX.search(text))
    length_ok = not (_SIMPLE_Q_RX.search(q) and len(text.split()) > 110)
    json_issues = [
        i for i in issues
        if i.startswith(("invented_planet", "wrong_house", "invented_sign"))
    ]
    proof_issues = [i for i in issues if i in (
        "missing_chart_proof", "unsupported_claim_without_proof", "generic_advice_without_proof",
    )]
    execution = _execution_from_meta(meta)
    supported, signals = chart_support_signals(q, archetype, execution)
    has_proof = answer_cites_chart_proof(text, execution)
    honest_low = answer_honest_low_tension(text)

    checks: list[dict[str, Any]] = [
        {
            "id": "safety",
            "label": "Medical safety guard",
            "passed": ok_safe,
            "issues": safe_issues,
        },
        {
            "id": "template_sections",
            "label": "No rigid template headers",
            "passed": tpl_ok,
            "issues": ["template_sections"] if not tpl_ok else [],
        },
        {
            "id": "question_drift",
            "label": "Answer matches question topic",
            "passed": drift_ok,
            "issues": ["question_drift"] if not drift_ok else [],
        },
        {
            "id": "missing_action_guidance",
            "label": "Action guidance (kya karu)",
            "passed": action_ok,
            "issues": ["missing_action_guidance"] if not action_ok else [],
        },
        {
            "id": "answer_too_long",
            "label": "Answer length (simple question)",
            "passed": length_ok,
            "issues": ["answer_too_long"] if not length_ok else [],
        },
        {
            "id": "json_facts",
            "label": "Chart JSON facts (D1 + D9)",
            "passed": not json_issues,
            "issues": json_issues,
        },
        {
            "id": "chart_proof",
            "label": "Chart-backed proof cited",
            "passed": not proof_issues,
            "issues": proof_issues,
            "detail": (
                f"signals={len(signals)} proof={has_proof} honest_low={honest_low}"
                if supported or proof_issues
                else "n/a"
            ),
        },
    ]

    audit = stored_audit if isinstance(stored_audit, dict) else {}
    return {
        "applies": True,
        "enabled": audit.get("enabled", health_validator_enabled()),
        "passed": ok,
        "attempts": int(audit.get("attempts") or 1),
        "final_block": bool(audit.get("final_block")),
        "issues": issues,
        "checks": checks,
        "chart_support_signals": signals[:6],
        "source": "live_audit" if audit else "recomputed",
    }


def build_health_validator_retry_feedback(
    issues: list[str],
    question: str,
    meta: dict[str, Any] | None = None,
) -> str:
    meta = meta or {}
    execution = _execution_from_meta(meta)
    archetype = str(meta.get("archetype") or classify_health_archetype(question) or "")
    _, signals = chart_support_signals(question, archetype, execution)
    lines = [
        "CORRECTION REQUIRED — previous answer failed validation.",
        f"User question: {question.strip()}",
        "Rewrite using ONLY HEALTH_ENGINE_EXECUTION_JSON facts.",
        "Answer ONLY what was asked; no template sections; no invented planets/houses/signs.",
        proof_retry_hint(signals),
        "Issues:",
    ]
    for issue in issues[:8]:
        lines.append(f"- {issue}")
    lines.append("Return the corrected final answer only.")
    return "\n".join(lines)


def run_health_llm_validator_loop(
    client: Any,
    *,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    question: str,
    meta: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Call LLM up to N+1 times until health validator passes."""
    audit: dict[str, Any] = {
        "enabled": True,
        "attempts": 0,
        "passed": False,
        "issues": [],
    }
    if not health_validator_enabled():
        audit["enabled"] = False
        resp = client.chat.completions.create(
            model=model, messages=messages, max_tokens=max_tokens,
        )
        text = (resp.choices[0].message.content or "").strip()
        audit["attempts"] = 1
        audit["passed"] = True
        return text, audit

    thread = list(messages)
    max_retries = health_validator_max_retries()
    text = ""

    for attempt in range(max_retries + 1):
        audit["attempts"] = attempt + 1
        resp = client.chat.completions.create(
            model=model, messages=thread, max_tokens=max_tokens,
        )
        text = (resp.choices[0].message.content or "").strip()
        ok, issues = validate_health_llm_answer(question, text, meta)
        audit["issues"] = issues
        if ok:
            audit["passed"] = True
            return text, audit
        if attempt >= max_retries:
            audit["passed"] = False
            audit["final_block"] = True
            return "", audit
        thread = thread + [
            {"role": "assistant", "content": text},
            {"role": "user", "content": build_health_validator_retry_feedback(issues, question, meta)},
        ]

    audit["passed"] = False
    return text, audit

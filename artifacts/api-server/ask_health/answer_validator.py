"""Health LLM answer validator — question match + JSON facts + retry loop."""

from __future__ import annotations

import os
import re
from typing import Any

from .answer_guard import verify_health_answer
from .chart_proof import (
    answer_cites_chart_proof,
    chart_support_signals,
)
from .classifier import classify_health_archetype
from .dna_judge import health_dna_judge_enabled, llm_judge_health_dna_alignment

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
_FINANCE_TOPIC_RX = re.compile(
    r"(?ix)\b(paisa|paise|kharcha|finance|financial|insurance|expense|money|budget)\b"
)
_CAREER_TOPIC_RX = re.compile(
    r"(?ix)\b(career|naukri|job|promotion|office|salary|boss)\b"
)
_SIMPLE_Q_RX = re.compile(
    r"(?ix)^(mujhse|meri|mera|mujhe|kya\s+karu|kya\s+karein|kaise|kyun|kya\s+ho)\b"
)
_GENERAL_HEALTH_OVERVIEW_Q_RX = re.compile(
    r"(?ix)(health ke bare|health ke baare|meri sehat|mere health|overall health|"
    r"health overview|sehat ke bare|sehat ke baare|health ke baare me|health ke bare me|"
    r"(?:mer[ei]|mujhse)\s+(?:health|sehat)\s+(?:ke\s+)?(?:bare|baare)\s+me)"
)
_SURGERY_RISK_Q_RX = re.compile(
    r"(?ix)(operation|surgery|shastra[\s-]?kriya).{0,50}?"
    r"(padega|pad sak|samna|saamna|zarurat|need|required|risk|chance|possibil|future|kabhi|hoga)"
    r"|"
    r"(padega|pad sak|samna|saamna|zarurat|need|required|risk|chance|possibil|future|kabhi|hoga)"
    r".{0,50}?(operation|surgery|shastra[\s-]?kriya)"
)
_SURGERY_RISK_A_RX = re.compile(
    r"(?ix)(operation|surgery|procedure|medical\s+procedure|doctor|surgeon|hospital|"
    r"risk|chance|possibil|zarurat|padega|pad\s+sakt|medical\s+intervention)"
)
_DEFAULT_OVERVIEW_PLAN = (
    "Provide a general overview of health aspects based on the chart, "
    "focusing on key health indicators without specific predictions or remedies."
)


def health_validator_enabled() -> bool:
    return (os.environ.get("ASK_HEALTH_VALIDATOR") or "1").strip() != "0"


def health_validator_block_on_fail() -> bool:
    """Default OFF — release last LLM draft rather than empty block (mobile needs text)."""
    return (os.environ.get("ASK_HEALTH_VALIDATOR_BLOCK") or "0").strip() == "1"


def health_validator_max_retries() -> int:
    try:
        return max(0, min(3, int(os.environ.get("ASK_HEALTH_VALIDATOR_RETRIES", "3"))))
    except (TypeError, ValueError):
        return 3


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


def _answer_word_limit(meta: dict[str, Any], question: str) -> int | None:
    """Max words for simple/direct health questions (None = no length gate)."""
    if _resolve_dna_contract(meta).get("answer_style"):
        return None
    q = (question or "").strip()
    if not _SIMPLE_Q_RX.search(q):
        return None
    budget = int(meta.get("word_budget") or 0)
    return max(60, min(110, budget if budget > 0 else 80))


_DNA_STYLE_LIMITS: dict[str, dict[str, int]] = {
    "short_2_3_lines": {"min_words": 8, "max_words": 55, "max_sentences": 3},
    "short_paragraph": {"min_words": 28, "max_words": 95, "max_sentences": 6},
    "detailed_explain": {"min_words": 65, "max_words": 220, "max_sentences": 12},
}


_DNA_CONTRACT_KEYS: tuple[str, ...] = (
    "normalized_question",
    "intent",
    "user_wants",
    "question_type",
    "domain",
    "bucket",
    "answer_style",
    "answer_approach",
)


def _resolve_dna_contract(meta: dict[str, Any]) -> dict[str, str]:
    """Question DNA fields used to gate health answers and DNA Judge."""
    out: dict[str, str] = {}
    if not isinstance(meta, dict):
        return out
    for key in _DNA_CONTRACT_KEYS:
        val = str(meta.get(key) or "").strip()
        if val:
            out[key] = val
    item = meta.get("question_dna_item")
    if isinstance(item, dict):
        for key in _DNA_CONTRACT_KEYS:
            val = str(item.get(key) or "").strip()
            if val and key not in out:
                out[key] = val
    qd = meta.get("question_dna")
    if isinstance(qd, dict):
        qs = qd.get("questions")
        if isinstance(qs, list) and qs and isinstance(qs[0], dict):
            for key in _DNA_CONTRACT_KEYS:
                val = str(qs[0].get(key) or "").strip()
                if val and key not in out:
                    out[key] = val
    return out


def should_apply_health_overview_contract(question: str) -> bool:
    """Only true general-overview asks — never travel+health or specific cause asks."""
    q = (question or "").strip()
    if not q:
        return False
    try:
        from engine_collision_registry import should_prioritize_health_over_travel

        if should_prioritize_health_over_travel(q):
            return False
    except Exception:
        pass
    if re.search(r"(?ix)\b(kyun|kyon|why|kaise|how|kya\s+karu|kya\s+karein)\b", q):
        return False
    return _is_general_health_overview_question(q)


def _is_general_health_overview_question(question: str) -> bool:
    return bool(_GENERAL_HEALTH_OVERVIEW_Q_RX.search(question or ""))


def _is_surgery_risk_question(question: str) -> bool:
    return bool(_SURGERY_RISK_Q_RX.search(question or ""))


def _enrich_dna_contract(meta: dict[str, Any], question: str) -> dict[str, str]:
    """Fill overview contract only for true general-overview asks; preserve Question DNA otherwise."""
    contract = _resolve_dna_contract(meta)
    if not contract.get("normalized_question"):
        contract["normalized_question"] = (question or "").strip()
    if should_apply_health_overview_contract(question):
        contract["answer_approach"] = _DEFAULT_OVERVIEW_PLAN
        contract.setdefault("answer_style", "short_paragraph")
        if not contract.get("user_wants"):
            contract["user_wants"] = "User wants a general overview of their health."
    for key, val in contract.items():
        if val:
            meta[key] = val
    return contract


def _should_skip_chart_proof(meta: dict[str, Any], question: str) -> bool:
    contract = _resolve_dna_contract(meta)
    if _is_general_overview_plan(contract.get("answer_approach", "")):
        return True
    if _is_general_health_overview_question(question):
        return True
    return False


def validate_unasked_topics(question: str, answer: str) -> tuple[bool, list[str]]:
    """Block finance/career drift when user did not ask for those topics."""
    issues: list[str] = []
    q = (question or "").strip()
    text = (answer or "").strip()
    if not text:
        return True, issues
    if _FINANCE_TOPIC_RX.search(text) and not _FINANCE_TOPIC_RX.search(q):
        issues.append("unasked_finance")
    if _CAREER_TOPIC_RX.search(text) and not _CAREER_TOPIC_RX.search(q):
        issues.append("unasked_career")
    return len(issues) == 0, issues


def _issues_after_judge_pass(issues: list[str]) -> list[str]:
    """Judge PASS = DNA style/plan OK; drop soft alignment issues only."""
    soft_exact = frozenset({
        "answer_too_long",
        "missing_action_guidance",
    })
    kept: list[str] = []
    for issue in issues:
        if issue.startswith(("dna_style_", "dna_plan_", "dna_judge:")):
            continue
        if issue in soft_exact:
            continue
        kept.append(issue)
    return kept


def _sentence_count(text: str) -> int:
    parts = [p.strip() for p in re.split(r"[.!?।]+", text or "") if p.strip()]
    return len(parts) if parts else (1 if (text or "").strip() else 0)


def validate_dna_answer_style(answer: str, meta: dict[str, Any]) -> tuple[bool, list[str]]:
    contract = _resolve_dna_contract(meta)
    style = str(contract.get("answer_style") or "").strip().lower().replace(" ", "_").replace("-", "_")
    if not style or style not in _DNA_STYLE_LIMITS:
        return True, []
    limits = _DNA_STYLE_LIMITS[style]
    words = len((answer or "").split())
    sentences = _sentence_count(answer or "")
    issues: list[str] = []
    if words > limits["max_words"]:
        issues.append(f"dna_style_too_long:{style}")
    if words < limits["min_words"]:
        issues.append(f"dna_style_too_short:{style}")
    if sentences > limits["max_sentences"]:
        issues.append(f"dna_style_too_many_sentences:{style}")
    return len(issues) == 0, issues


_GENERAL_OVERVIEW_PLAN_RX = re.compile(
    r"(?ix)(general overview|overall health|key health indicator|"
    r"health aspect|without specific prediction|without.*remed|"
    r"long[- ]term health tendenc)"
)
_TECHNICAL_JARGON_RX = re.compile(
    r"(?ix)(vitality\s*score|\d+\s*/\s*100|recovery\s+capacity|"
    r"enemy\s+sign|malefic|aspect\s+kar|H\d+\b|immunity\s+issues|"
    r"chronic\s+aur|vitality\s+low\s*\()"
)


def _is_general_overview_plan(plan: str) -> bool:
    return bool(_GENERAL_OVERVIEW_PLAN_RX.search(plan or ""))


def _planet_house_citation_count(text: str) -> int:
    return len(
        re.findall(
            r"(?ix)\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b"
            r".{0,40}(?:ghar|house|H\s*\d|\d(?:st|nd|rd|th)\s+ghar)",
            text or "",
        )
    )


def _validate_general_overview_answer(text: str) -> tuple[bool, list[str]]:
    """General overview plan — soft lifestyle tone, not planet-by-planet breakdown."""
    issues: list[str] = []
    if _TECHNICAL_JARGON_RX.search(text):
        issues.append("dna_plan_too_technical")
    if _planet_house_citation_count(text) >= 2:
        issues.append("dna_plan_too_detailed_breakdown")
    if not re.search(
        r"(?ix)(foundation|overall|tendenc|stress|energy|digestion|balance|"
        r"routine|neend|sleep|exercise|dhyan|sehat|health|wellness|beneficial|"
        r"long[- ]term|kundli)",
        text,
    ):
        issues.append("dna_plan_missing_overview_tone")
    if re.search(r"(?ix)(remedy|upay|mantra|puja|daan|path)\b", text):
        issues.append("dna_plan_has_remedies")
    return len(issues) == 0, issues


def validate_dna_answer_plan(answer: str, meta: dict[str, Any]) -> tuple[bool, list[str]]:
    """Regex fallback when LLM DNA judge is off. Primary plan check = dna_judge."""
    if health_dna_judge_enabled():
        return True, []
    contract = _resolve_dna_contract(meta)
    plan = str(contract.get("answer_approach") or "").strip()
    if not plan:
        return True, []
    text = (answer or "").strip()
    if not text:
        return False, ["dna_plan_empty_answer"]
    plan_l = plan.lower()
    issues: list[str] = []

    if _is_general_overview_plan(plan_l):
        ok_ov, ov_issues = _validate_general_overview_answer(text)
        if not ok_ov:
            issues.extend(ov_issues)
        return len(issues) == 0, issues

    if re.search(r"(?ix)(present[- ]state|what is happening now|abhi)", plan_l):
        if not re.search(r"(?ix)(abhi|filhal|currently|chal\s*raha|present|haal|dikh(ta|ti|raha|rahi))", text):
            issues.append("dna_plan_present_state")

    if re.search(r"(?ix)(timing|dasha|transit|window|lead with timing)", plan_l):
        if not re.search(r"(?ix)(dasha|transit|window|saal|mahina|month|period|samay|phase|kab|timing)", text):
            issues.append("dna_plan_timing_lead")

    if re.search(r"(?ix)(cautious|avoid absolute|non-alarmist|gentle)", plan_l):
        if re.search(r"(?ix)(pakka|100%|definitely|guarantee|zaroor\s+hoga|bilkul\s+hoga)", text):
            issues.append("dna_plan_too_absolute")

    if re.search(r"(?ix)(balanced|pros/cons|yes/no unless)", plan_l):
        if re.search(r"(?ix)^(haan|nahi|yes|no)[.!]?\s*$", text.strip(), re.I):
            issues.append("dna_plan_not_balanced")

    if re.search(r"(?ix)(planet\s*\+\s*ghar\s+proof|planet\s*\+\s*ghar\s+cite|cite\s+planet|proof\s+mandatory)", plan_l):
        execution = _execution_from_meta(meta)
        if execution and not answer_cites_chart_proof(text, execution):
            issues.append("dna_plan_missing_chart_cite")

    if re.search(r"(?ix)(2[-–]4 short|short sentence|2-3 line)", plan_l):
        words = len(text.split())
        if words > 60 or _sentence_count(text) > 4:
            issues.append("dna_plan_length_mismatch")

    user_wants = str(contract.get("user_wants") or "").lower()
    if user_wants and re.search(r"(?ix)(health|sehat|vitality|wellness)", user_wants):
        if not re.search(r"(?ix)(health|sehat|vitality|chart|sharir|body|rog|immune|stress)", text):
            issues.append("dna_plan_user_wants_miss")

    return len(issues) == 0, issues


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

    if re.search(r"(?ix)\bkya\s+kar", q) and not _ACTION_RX.search(text):
        issues.append("missing_action_guidance")

    word_limit = _answer_word_limit(meta, q)
    if word_limit is not None and len(text.split()) > word_limit:
        issues.append("answer_too_long")

    ok_topics, topic_issues = validate_unasked_topics(q, text)
    if not ok_topics:
        issues.extend(topic_issues)

    execution = _execution_from_meta(meta)
    planet_houses = _planet_house_map(execution)
    allowed_signs = _chart_signs(execution)

    # Only enforce chart-fact JSON when execution pack is present — empty
    # execution used to mark every planet/sign mention as hallucinated.
    if planet_houses:
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

    if allowed_signs:
        for raw_sign in (
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        ):
            if re.search(rf"\b{raw_sign}\b", text, re.IGNORECASE):
                if raw_sign.lower() not in allowed_signs:
                    issues.append(f"invented_sign:{raw_sign}")
                    break

    if not health_dna_judge_enabled():
        ok_style, style_issues = validate_dna_answer_style(text, meta)
        if not ok_style:
            issues.extend(style_issues)

        ok_plan, plan_issues = validate_dna_answer_plan(text, meta)
        if not ok_plan:
            issues.extend(plan_issues)

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
    action_ok = not re.search(r"(?ix)\bkya\s+kar", q) or bool(_ACTION_RX.search(text))
    length_ok = True
    word_limit = _answer_word_limit(meta, q)
    if word_limit is not None:
        length_ok = len(text.split()) <= word_limit
    topics_ok, topic_issues = validate_unasked_topics(q, text)
    dna_contract = _resolve_dna_contract(meta)
    style_ok, style_issues = validate_dna_answer_style(text, meta)
    plan_ok, plan_issues = validate_dna_answer_plan(text, meta)
    json_issues = [
        i for i in issues
        if i.startswith(("invented_planet", "wrong_house", "invented_sign"))
    ]
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
            "id": "unasked_topics",
            "label": "No unasked finance/career drift",
            "passed": topics_ok,
            "issues": topic_issues,
        },
        {
            "id": "dna_answer_style",
            "label": "Matches Question DNA Answer Style",
            "passed": style_ok,
            "issues": style_issues,
            "detail": dna_contract.get("answer_style") or "—",
        },
        {
            "id": "dna_answer_plan",
            "label": "Matches Question DNA LLM Answer Plan",
            "passed": plan_ok,
            "issues": plan_issues,
            "detail": (dna_contract.get("answer_approach") or "—")[:160],
        },
        {
            "id": "json_facts",
            "label": "Chart JSON facts (D1 + D9)",
            "passed": not json_issues,
            "issues": json_issues,
        },
    ]

    audit = stored_audit if isinstance(stored_audit, dict) else {}
    judge_audit = audit.get("dna_judge") if isinstance(audit.get("dna_judge"), dict) else {}
    judge_passed = judge_audit.get("passed") if judge_audit.get("enabled") else None
    judge_fix_hint = str((judge_audit.get("parsed") or {}).get("fix_hint") or "").strip()

    display_checks = list(checks)
    if judge_passed is not None:
        display_checks = [
            c for c in display_checks
            if c.get("id") not in ("dna_answer_style", "dna_answer_plan")
        ]
        display_checks.insert(0, {
            "id": "dna_llm_judge",
            "label": "Question DNA LLM Judge",
            "passed": bool(judge_passed),
            "issues": list(judge_audit.get("issues") or []),
            "detail": judge_fix_hint[:200] if judge_fix_hint else "—",
        })
        if judge_passed is False:
            ok = False

    return {
        "applies": True,
        "enabled": audit.get("enabled", health_validator_enabled()),
        "passed": ok,
        "attempts": int(audit.get("attempts") or 1),
        "final_block": bool(audit.get("final_block")),
        "released_anyway": bool(audit.get("released_anyway")),
        "final_issues": list(audit.get("final_issues") or []),
        "issues": issues,
        "checks": display_checks,
        "source": "live_audit" if audit else "recomputed",
        "dna_judge": {
            "enabled": bool(judge_audit.get("enabled")),
            "passed": judge_passed,
            "issues": list(judge_audit.get("issues") or []),
            "fix_hint": judge_fix_hint or None,
            "skipped": judge_audit.get("skipped"),
        },
    }


def build_health_validator_retry_feedback(
    issues: list[str],
    question: str,
    meta: dict[str, Any] | None = None,
) -> str:
    meta = meta or {}
    dna_contract = _resolve_dna_contract(meta)
    issue_hints = {
        "disease_name": "Specific disease naam mat likho — vulnerability zones batao.",
        "surgery_muhurat": "Operation/surgery ka date ya muhurat mat do — sirf cautious probability + doctor advice.",
        "surgery_date_leak": "Surgery date/muhurat leak mat karo — probability only, surgeon clearance mandatory.",
        "unsolicited_timing": "User ne exact timing nahi puchi — month/year/date hatao.",
        "missing_action_guidance": "Practical steps add karo (rest, doctor, routine).",
        "answer_too_long": (
            "Jawab bahut lamba hai — 2-4 chhote sentences (max ~60-80 words). "
            "Sirf user ke sawal ka direct jawab; extra topics mat add karo."
        ),
        "unasked_finance": (
            "User ne paisa/kharcha/finance nahi pucha — money/insurance/expense hatao; "
            "sirf health/travel angle rakho."
        ),
        "unasked_career": (
            "User ne career/job nahi pucha — promotion/office/career mention hatao."
        ),
        "dna_style_too_long": "Question DNA Answer Style ke hisaab se jawab chhota karo (style limit exceed).",
        "dna_style_too_short": "Question DNA Answer Style ke hisaab se thoda detail badhao.",
        "dna_style_too_many_sentences": "Question DNA Answer Style ke hisaab se kam sentences likho.",
        "dna_plan_present_state": "LLM Answer Plan ke mutabiq present-state / abhi wala read do.",
        "dna_plan_timing_lead": "LLM Answer Plan ke mutabiq pehle timing window (dasha/transit) batao.",
        "dna_plan_too_absolute": "LLM Answer Plan cautious hai — pakka/guarantee wording hatao.",
        "dna_plan_not_balanced": "LLM Answer Plan balanced guidance maangta hai — sirf haan/nahi mat do.",
        "dna_plan_missing_chart_cite": (
            "LLM Answer Plan explicitly planet+ghar proof maangta hai — ek light cite add karo "
            "ya plain language me chart anchor rakho."
        ),
        "dna_plan_length_mismatch": "LLM Answer Plan short answer maangta hai — lamba mat likho.",
        "dna_plan_user_wants_miss": "User wants (Question DNA) cover nahi hua — user_wants ke mutabiq jawab do.",
        "dna_plan_too_technical": (
            "LLM Answer Plan = general overview. Vitality score /100, H1/H8, enemy sign, "
            "aspect laundry-list MAT likho. Soft overview do: stress, energy, digestion, routine."
        ),
        "dna_plan_too_detailed_breakdown": (
            "Planet+ghar ki list mat do. 1 soft theme enough — overall health foundation, "
            "stress/energy balance, lifestyle tips. Example tone: 'overall health foundation theek, "
            "stress aur energy par dhyan dena zaroori'."
        ),
        "dna_plan_missing_overview_tone": (
            "General overview chahiye — foundation/tendencies + lifestyle (routine, neend, exercise). "
            "Medical diagnosis ya remedy mat do."
        ),
        "dna_plan_has_remedies": "LLM Answer Plan remedies forbid karta hai — upay/mantra hatao.",
        "dna_judge": "Question DNA LLM judge — answer style/plan semantic match fail.",
        "dna_judge_mismatch": "Answer Style ya LLM Answer Plan se clearly match nahi ho raha.",
    }
    lines = [
        "CORRECTION REQUIRED — previous answer failed validation.",
        f"User question: {question.strip()}",
    ]
    if dna_contract.get("normalized_question"):
        lines.append(f"Normalized question (MUST answer this): {dna_contract['normalized_question']}")
    if dna_contract.get("intent"):
        lines.append(f"User intent (Question DNA): {dna_contract['intent']}")
    if dna_contract.get("user_wants"):
        lines.append(f"User wants: {dna_contract['user_wants']}")
    if dna_contract.get("question_type"):
        lines.append(f"Question type: {dna_contract['question_type']}")
    if dna_contract.get("answer_style"):
        lines.append(f"Question DNA Answer Style (MUST match): {dna_contract['answer_style']}")
    if dna_contract.get("answer_approach"):
        lines.append(f"Question DNA LLM Answer Plan (MUST follow): {dna_contract['answer_approach']}")
    judge_hint = str(meta.get("dna_judge_hint") or "").strip()
    if judge_hint:
        lines.append(f"DNA Judge fix hint: {judge_hint}")
    lines.extend([
        "Rewrite using ONLY HEALTH_ENGINE_EXECUTION_JSON facts.",
        "Answer ONLY what was asked — no template sections; no invented planets/houses/signs.",
        "Pick relevant JSON facts for THIS question only; light proof (max 1 point); no planet+ghar list.",
        "Issues:",
    ])
    if "disease_name" in issues:
        lines.insert(
            5,
            "NEVER name specific diseases (diabetes, cancer, asthma, TB). Use chart zones only.",
        )
    for issue in issues[:8]:
        lines.append(f"- {issue}")
        hint = issue_hints.get(issue.split(":")[0])
        if hint:
            lines.append(f"  → {hint}")
    lines.append("Return the corrected final answer only.")
    return "\n".join(lines)


def _build_overview_final_repair_prompt(question: str, contract: dict[str, str]) -> str:
    return f"""FINAL REWRITE — previous attempts failed validation.

USER QUESTION: {question.strip()}
USER WANTS: {contract.get("user_wants") or "General health overview"}
ANSWER STYLE: {contract.get("answer_style") or "short_paragraph"}
ANSWER PLAN: {contract.get("answer_approach") or _DEFAULT_OVERVIEW_PLAN}

Write ONE soft health overview paragraph (4-6 sentences, Hinglish):
- Overall health foundation / long-term tendencies
- Stress, energy, digestion or balance themes (pick 1-2)
- Healthy routine, sleep, exercise tip
- End: tendencies only, not medical diagnosis
- NO vitality score /100, NO planet+ghar list, NO remedies, NO disease names

Return ONLY the final answer paragraph."""


def _build_surgery_final_repair_prompt(
    question: str,
    contract: dict[str, str],
    signals: list[str],
) -> str:
    signal_text = "; ".join(signals[:3]) if signals else "No strong surgery-specific signal in JSON."
    return f"""FINAL REWRITE — previous surgery-risk attempts failed validation.

USER QUESTION: {question.strip()}
USER WANTS: {contract.get("user_wants") or "User asks whether operation/surgery may be needed in future."}
ANSWER STYLE: {contract.get("answer_style") or "short_paragraph"}
ANSWER PLAN: {contract.get("answer_approach") or "Give cautious probability, not certainty."}
HEALTH_ENGINE_EXECUTION_JSON SIGNALS: {signal_text}

Write ONE cautious Hinglish paragraph (4-6 sentences):
- Directly answer operation/surgery possibility as probability only, never certainty
- Use one natural chart proof from the JSON signals if available
- No date, no muhurat, no month/year, no specific disease name
- Do not say surgery is guaranteed or impossible
- Add doctor/checkup advice
- End with: this is not medical diagnosis

Return ONLY the final answer paragraph."""


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
    _enrich_dna_contract(meta, question)

    for attempt in range(max_retries + 1):
        audit["attempts"] = attempt + 1
        resp = client.chat.completions.create(
            model=model, messages=thread, max_tokens=max_tokens,
        )
        text = (resp.choices[0].message.content or "").strip()
        ok, issues = validate_health_llm_answer(question, text, meta)
        contract = _enrich_dna_contract(meta, question)
        ok_j = True
        if health_dna_judge_enabled() and (
            contract.get("user_wants")
            or contract.get("intent")
            or contract.get("normalized_question")
            or contract.get("answer_style")
            or contract.get("answer_approach")
            or contract.get("question_type")
        ):
            ok_j, j_issues, judge_hint, j_audit = llm_judge_health_dna_alignment(
                client,
                model,
                question=question,
                answer=text,
                contract=contract,
            )
            audit["dna_judge"] = j_audit
            if judge_hint:
                meta["dna_judge_hint"] = judge_hint
            if ok_j:
                issues = _issues_after_judge_pass(issues)
            else:
                issues.extend([f"dna_judge:{i}" for i in j_issues])
        ok = len(issues) == 0
        audit["issues"] = issues
        if ok:
            audit["passed"] = True
            return text, audit
        if attempt >= max_retries:
            # Last-chance overview repair for general health asks
            if _should_skip_chart_proof(meta, question):
                try:
                    repair_resp = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "Health astrology narrator. Plain Hinglish."},
                            {"role": "user", "content": _build_overview_final_repair_prompt(question, contract)},
                        ],
                        temperature=0.2,
                        max_tokens=max_tokens,
                    )
                    repaired = (repair_resp.choices[0].message.content or "").strip()
                    if repaired:
                        ok_r, issues_r = validate_health_llm_answer(question, repaired, meta)
                        ok_j_r = True
                        if health_dna_judge_enabled():
                            ok_j_r, j_issues_r, _, j_audit_r = llm_judge_health_dna_alignment(
                                client, model, question=question, answer=repaired, contract=contract,
                            )
                            audit["dna_judge"] = j_audit_r
                            if ok_j_r:
                                issues_r = _issues_after_judge_pass(issues_r)
                            else:
                                issues_r.extend([f"dna_judge:{i}" for i in j_issues_r])
                        if len(issues_r) == 0:
                            audit["passed"] = True
                            audit["final_repair"] = "overview_rewrite"
                            return repaired, audit
                        text = repaired
                        issues = issues_r
                except Exception as exc:
                    audit["final_repair_error"] = str(exc)[:120]

            if _is_surgery_risk_question(question):
                try:
                    _, repair_signals = chart_support_signals(
                        question,
                        str(meta.get("archetype") or classify_health_archetype(question) or ""),
                        _execution_from_meta(meta),
                    )
                    repair_resp = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "Health astrology narrator. Plain Hinglish. Medical-safe."},
                            {
                                "role": "user",
                                "content": _build_surgery_final_repair_prompt(question, contract, repair_signals),
                            },
                        ],
                        temperature=0.2,
                        max_tokens=max_tokens,
                    )
                    repaired = (repair_resp.choices[0].message.content or "").strip()
                    if repaired:
                        ok_r, issues_r = validate_health_llm_answer(question, repaired, meta)
                        ok_j_r = True
                        if health_dna_judge_enabled():
                            ok_j_r, j_issues_r, _, j_audit_r = llm_judge_health_dna_alignment(
                                client, model, question=question, answer=repaired, contract=contract,
                            )
                            audit["dna_judge"] = j_audit_r
                            if ok_j_r:
                                issues_r = _issues_after_judge_pass(issues_r)
                            else:
                                issues_r.extend([f"dna_judge:{i}" for i in j_issues_r])
                        if len(issues_r) == 0:
                            audit["passed"] = True
                            audit["final_repair"] = "surgery_risk_rewrite"
                            return repaired, audit
                        text = repaired
                        issues = issues_r
                except Exception as exc:
                    audit["final_repair_error"] = str(exc)[:120]

            audit["passed"] = False
            audit["final_issues"] = list(issues)
            if health_validator_block_on_fail():
                audit["final_block"] = True
                audit["released_anyway"] = False
                audit["blocked_answer_preview"] = text[:240] if text else ""
                return "", audit
            audit["released_anyway"] = bool(text)
            audit["final_block"] = not bool(text)
            return text, audit
        thread = thread + [
            {"role": "assistant", "content": text},
            {"role": "user", "content": build_health_validator_retry_feedback(issues, question, meta)},
        ]

    audit["passed"] = False
    return text, audit

"""Post-LLM guard: relationship answer stays chart-safe (health-style soft repair)."""

from __future__ import annotations

import re
from typing import Any

_BANNED_LABEL_RX = re.compile(
    r"(?ix)("
    r"seedha\s*jawab\s*:|"
    r"conclusion\s*:|"
    r"निष्कर्ष\s*:|"
    r"verdict\s*:|"
    r"big\s*picture\s*:|"
    r"kyun\s+aisa\s*:|"
    r"ab\s+kya\s+karein\s*:"
    r")"
)

_EXACT_DATE_GUARANTEE_RX = re.compile(
    r"(?ix)\b("
    r"exact\s+(?:marriage\s+)?date|"
    r"shaadi\s+(?:ki\s+)?tarikh\s+\d|"
    r"wedding\s+on\s+\d|"
    r"100\s*(?:%|percent)\s+(?:shaadi|marriage|breakup)|"
    r"pakka\s+\d{1,2}\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
    r")\b"
)

_DEATH_PRED_RX = re.compile(
    r"(?ix)\b("
    r"you will die|mar\s+jao?ge|maut\s+(aa\s+)?jaye?gi|"
    r"kab\s+mar(?:oge|ungi|unga)|mrityu\s+tarikh"
    r")\b"
)

# Unsolicited calendar/year when user did not ask WHEN
_UNSOLICITED_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"20\d{2}|"
    r"january|february|march|april|may|june|july|august|"
    r"september|october|november|december|"
    r"shaadi\s+ho\s+jayegi\s+(?:is|agle)\s+(?:mahine|saal)|"
    r"exact\s+week|exact\s+month"
    r")\b"
)


def _question_wants_timing(question: str, meta: dict[str, Any]) -> bool:
    q = question or ""
    try:
        from ask_mr.timing_registry import question_requests_timing

        if question_requests_timing(q, meta.get("llm_intent") if isinstance(meta, dict) else None):
            return True
    except Exception:
        pass
    if re.search(r"(?ix)\b(kab|when|kis\s+saal|timing|dasha|muhurat)\b", q):
        return True
    checks = meta.get("checks") if isinstance(meta, dict) else None
    if isinstance(checks, dict):
        ee = checks.get("relationship_engine_execution")
        if isinstance(ee, dict) and isinstance(ee.get("dasha_timing_compact"), dict):
            return True
    return False


def verify_relationship_answer(
    question: str,
    answer: str,
    meta: dict[str, Any],
) -> tuple[bool, list[str]]:
    issues: list[str] = []
    text = (answer or "").strip()
    if not text:
        return False, ["empty_answer"]
    if _BANNED_LABEL_RX.search(text):
        issues.append("template_labels")
    if _DEATH_PRED_RX.search(text):
        issues.append("death_prediction")
    if _EXACT_DATE_GUARANTEE_RX.search(text):
        issues.append("exact_date_guarantee")
    if not _question_wants_timing(question, meta) and _UNSOLICITED_TIMING_RX.search(text):
        issues.append("unsolicited_timing")
    return len(issues) == 0, issues


def guard_relationship_answer(
    question: str,
    answer: str,
    meta: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Soft repair only — never hard-blocks the answer."""
    ok, issues = verify_relationship_answer(question, answer, meta)
    guard_meta: dict[str, Any] = {"ok": ok, "issues": issues, "repaired": False}
    text = (answer or "").strip()
    if ok:
        return text, guard_meta

    if "template_labels" in issues:
        text = _BANNED_LABEL_RX.sub("", text).strip()
        guard_meta["repaired"] = True

    if "death_prediction" in issues:
        text = _DEATH_PRED_RX.sub("", text).strip()
        guard_meta["repaired"] = True

    if "exact_date_guarantee" in issues:
        text = _EXACT_DATE_GUARANTEE_RX.sub("", text).strip()
        guard_meta["repaired"] = True

    # Soft note only — do not strip year strings aggressively (risk of mangling prose)
    if "unsolicited_timing" in issues and not guard_meta.get("repaired"):
        guard_meta["warn"] = "unsolicited_timing"
        # Still mark ok_after soft pass if only this soft issue
        guard_meta["ok"] = True

    if not text:
        text = (
            "Chart pe relationship signals mixed dikhte hain — "
            "clear baat aur patience se rishta sambhal sakte ho."
        )
        guard_meta["repaired"] = True

    # Re-check after repairs (except soft unsolicited_timing warn-only)
    ok2, issues2 = verify_relationship_answer(question, text, meta)
    hard = [i for i in issues2 if i != "unsolicited_timing"]
    guard_meta["ok"] = len(hard) == 0
    guard_meta["issues"] = issues2 if issues2 else issues
    return text, guard_meta

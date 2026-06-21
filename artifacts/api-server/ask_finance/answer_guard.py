"""Post-LLM guard: finance answer must match question + engine verdict."""

from __future__ import annotations

import re
from typing import Any

_BANNED_LABEL_RX = re.compile(
    r"(?ix)(seedha\s*jawab\s*:|conclusion\s*:|निष्कर्ष\s*:|verdict\s*:)"
)
_LOTTERY_PUSH_RX = re.compile(
    r"(?ix)\b(lottery\s*try|ticket\s*lagao|satta\s*lagao|jackpot\s*milega)\b"
)
_STOCK_TIP_RX = re.compile(
    r"(?ix)\b(buy\s*this\s*stock|nifty\s*tip|intraday\s*tip|share\s*recommend)\b"
)
_TIMING_DATE_RX = re.compile(
    r"(?ix)\b(\d{4}|january|february|march|april|may|june|july|august|"
    r"september|october|november|december|muhurat\s*on)\b"
)


def verify_finance_answer(
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
    if _LOTTERY_PUSH_RX.search(text):
        issues.append("lottery_push")
    if _STOCK_TIP_RX.search(text):
        issues.append("stock_tip")
    archetype = str(meta.get("archetype") or "")
    if archetype != "sudden_gain_loss" and _LOTTERY_PUSH_RX.search(text):
        issues.append("lottery_off_topic")
    q = (question or "").lower()
    if "kab" not in q and "when" not in q and _TIMING_DATE_RX.search(text):
        issues.append("unsolicited_timing")
    return len(issues) == 0, issues


def guard_finance_answer(
    question: str,
    answer: str,
    meta: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    ok, issues = verify_finance_answer(question, answer, meta)
    guard_meta = {"ok": ok, "issues": issues, "repaired": False}
    text = (answer or "").strip()
    if ok:
        return text, guard_meta
    if "template_labels" in issues:
        text = _BANNED_LABEL_RX.sub("", text).strip()
        guard_meta["repaired"] = True
    return text, guard_meta

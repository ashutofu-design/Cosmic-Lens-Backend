from __future__ import annotations

import re
from typing import Any


def guard_children_answer(
    question: str,
    answer: str,
    meta: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    text = (answer or "").strip()
    issues: list[str] = []

    if re.search(r"(?ix)\b(seedha\s+jawab|conclusion:)\b", text):
        issues.append("decision_template_label")
        text = re.sub(r"(?ix)\bseedha\s+jawab\s*:\s*", "", text)
        text = re.sub(r"(?ix)\bconclusion\s*:\s*", "", text).strip()

    if re.search(r"(?ix)\b(kab|when|muhurat|dasha|202[4-9])\b", text):
        issues.append("timing_leak")
        text = re.sub(
            r"(?ix)\b(kab|when|muhurat|dasha).*$",
            "",
            text,
            count=1,
        ).strip()

    if re.search(r"(?ix)\b(guaranteed\s+boy|guaranteed\s+girl|pakka\s+ladka|pakka\s+ladki)\b", text):
        issues.append("gender_guarantee")
        text = re.sub(
            r"(?ix)\b(guaranteed\s+boy|guaranteed\s+girl|pakka\s+ladka|pakka\s+ladki)\b",
            "gender uncertain from chart alone",
            text,
        ).strip()

    if re.search(r"(?ix)\b(exactly\s+\d+\s+child|\d+\s+bachch?[ae]\s+fixed)\b", text):
        issues.append("exact_count")
        text = re.sub(
            r"(?ix)\b(exactly\s+\d+\s+child|\d+\s+bachch?[ae]\s+fixed)\b",
            "",
            text,
        ).strip()

    ok = not issues or len(issues) <= 1
    return text, {
        "ok": ok,
        "ok_after_repair": ok,
        "repaired": bool(issues),
        "issues": issues,
    }

from __future__ import annotations

import re
from typing import Any


def guard_education_answer(
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

    ignore = [str(x).lower() for x in (meta.get("ignore") or [])]
    if any("exact marks" in x or "exact rank" in x for x in ignore):
        if re.search(r"(?ix)\b(\d{1,3}\s*%\s*|\brank\s+\d+\b|\b\d+\s*marks\b)", text):
            issues.append("fabricated_number")
            text = re.sub(r"(?ix)\b(\d{1,3}\s*%|\brank\s+\d+|\d+\s*marks)\b", "", text).strip()

    ok = not issues or len(issues) == 1
    return text, {
        "ok": ok,
        "ok_after_repair": ok,
        "repaired": bool(issues),
        "issues": issues,
    }

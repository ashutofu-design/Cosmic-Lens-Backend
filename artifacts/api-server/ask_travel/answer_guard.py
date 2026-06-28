from __future__ import annotations

import re
from typing import Any


def guard_travel_answer(
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

    if re.search(r"(?ix)\b(kab|when|muhurat|202[4-9]|dasha\s+se)\b", text):
        issues.append("timing_leak")
        text = re.sub(
            r"(?ix)\b(kab|when|muhurat).*$",
            "",
            text,
            count=1,
        ).strip()

    if re.search(r"(?ix)\b(guaranteed\s+visa|pakka\s+visa|100%\s+visa|fixed\s+country|"
                 r"pakka\s+(?:usa|uk|canada|country|desh))\b", text):
        issues.append("guarantee_leak")
        text = re.sub(
            r"(?ix)\b(guaranteed\s+visa|pakka\s+visa|100%\s+visa|fixed\s+country)\b",
            "indicative only from chart",
            text,
        ).strip()

    ok = not issues or len(issues) <= 1
    return text, {
        "ok": ok,
        "ok_after_repair": ok,
        "repaired": bool(issues),
        "issues": issues,
    }

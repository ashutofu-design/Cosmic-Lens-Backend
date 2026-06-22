from __future__ import annotations

import re
from typing import Any


_FEAR_RX = re.compile(
    r"(?ix)\b("
    r"jail\s+yog|prison\s+yog|death\s+penalty|phansi|faansi|hanging|"
    r"pakka\s+(?:jail|andar|qaid|conviction|jeet|haar)|"
    r"100%\s+(?:jail|conviction|jeet|haar|win|loss)|"
    r"guaranteed\s+(?:jail|conviction|win|loss|bail|acquittal)|"
    r"fixed\s+(?:jail|conviction|verdict)|"
    r"maut\s+ki\s+saza|saza\s+e\s+maut|"
    r"pakka\s+andar|andar\s+pakka"
    r")\b"
)


def guard_litigation_answer(
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

    if re.search(r"(?ix)\b(kab|when|muhurat|202[4-9]|dasha\s+se|verdict\s+date)\b", text):
        issues.append("timing_leak")
        text = re.sub(
            r"(?ix)\b(kab|when|muhurat).*$",
            "",
            text,
            count=1,
        ).strip()

    if _FEAR_RX.search(text):
        issues.append("fear_language")
        text = re.sub(
            r"(?ix)\b(jail\s+yog|prison\s+yog|death\s+penalty|phansi|faansi|hanging|"
            r"pakka\s+(?:jail|andar|qaid|conviction|jeet|haar)|"
            r"100%\s+(?:jail|conviction|jeet|haar|win|loss)|"
            r"guaranteed\s+(?:jail|conviction|win|loss|bail|acquittal)|"
            r"maut\s+ki\s+saza|saza\s+e\s+maut|pakka\s+andar|andar\s+pakka)\b",
            "chart shows legal caution themes only — qualified lawyer essential",
            text,
        ).strip()

    if re.search(r"(?ix)\b(guaranteed\s+win|pakka\s+jeet|100%\s+jeet|fixed\s+verdict)\b", text):
        issues.append("guarantee_leak")
        text = re.sub(
            r"(?ix)\b(guaranteed\s+win|pakka\s+jeet|100%\s+jeet|fixed\s+verdict)\b",
            "indicative legal axis only — court decides the real outcome",
            text,
        ).strip()

    ok = not issues or len(issues) <= 1
    return text, {
        "ok": ok,
        "ok_after_repair": ok,
        "repaired": bool(issues),
        "issues": issues,
    }

from __future__ import annotations

import re
from typing import Any

_GENDER_CLAIM_RX = re.compile(
    r"(?ix)\b("
    r"guaranteed\s+boy|guaranteed\s+girl|pakka\s+ladka|pakka\s+ladki|"
    r"ladka\s+hone\s+ki\s+sambhavna|ladki\s+hone\s+ki\s+sambhavna|"
    r"ladka\s+(?:zyada|more)|ladki\s+(?:zyada|more)|"
    r"(?:boy|girl)\s+(?:more\s+)?likely|"
    r"isliye\s+ladka|isliye\s+ladki|"
    r"beta\s+hoga|beti\s+hogi|putra\s+hoga|putri\s+hogi|"
    r"male\s+child|female\s+child|"
    r"bachcha?\s+ladka|bachcha?\s+ladki"
    r")\b"
)

_GENDER_UNCERTAIN = (
    "Chart se ladka/ladki confirm nahi hota — gender uncertain; healthy progeny pe focus."
)


def guard_children_answer(
    question: str,
    answer: str,
    meta: dict[str, Any],
    *,
    is_timing: bool = False,
) -> tuple[str, dict[str, Any]]:
    text = (answer or "").strip()
    issues: list[str] = []

    if re.search(r"(?ix)\b(seedha\s+jawab|conclusion:)\b", text):
        issues.append("decision_template_label")
        text = re.sub(r"(?ix)\bseedha\s+jawab\s*:\s*", "", text)
        text = re.sub(r"(?ix)\bconclusion\s*:\s*", "", text).strip()

    # Timing leak scrub only for STATIC children answers — not timing Qs.
    if not is_timing and re.search(r"(?ix)\b(kab|when|muhurat|dasha|202[4-9])\b", text):
        issues.append("timing_leak")
        text = re.sub(
            r"(?ix)\b(kab|when|muhurat|dasha).*$",
            "",
            text,
            count=1,
        ).strip()

    if _GENDER_CLAIM_RX.search(text):
        issues.append("gender_claim")
        # Drop gender-claim sentences; keep timing/other content.
        parts = re.split(r"(?<=[.!?।])\s+", text)
        kept = [p for p in parts if p and not _GENDER_CLAIM_RX.search(p)]
        text = " ".join(kept).strip()
        q = (question or "").lower()
        if re.search(r"(?ix)\b(ladka|ladki|beta|beti|boy|girl|gender|putra|putri)\b", q):
            if _GENDER_UNCERTAIN.lower() not in text.lower():
                text = (text + " " + _GENDER_UNCERTAIN).strip()
        if not text:
            text = _GENDER_UNCERTAIN

    if re.search(r"(?ix)\b(exactly\s+\d+\s+child|\d+\s+bachch?[ae]\s+fixed)\b", text):
        issues.append("exact_count")
        text = re.sub(
            r"(?ix)\b(exactly\s+\d+\s+child|\d+\s+bachch?[ae]\s+fixed)\b",
            "",
            text,
        ).strip()

    ok = not issues or (set(issues) <= {"decision_template_label"})
    return text, {
        "ok": ok,
        "ok_after_repair": ok,
        "repaired": bool(issues),
        "issues": issues,
    }

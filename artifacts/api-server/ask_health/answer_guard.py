"""Post-LLM guard: health answer must stay medical-safe."""

from __future__ import annotations

import re
from typing import Any

_BANNED_LABEL_RX = re.compile(
    r"(?ix)(seedha\s*jawab\s*:|conclusion\s*:|निष्कर्ष\s*:|verdict\s*:)"
)
_DISEASE_NAME_RX = re.compile(
    r"(?ix)\b("
    r"diabetes|cancer|tumor|tumour|hiv|aids|tuberculosis|tb\b|"
    r"arthritis|asthma|epilepsy|parkinson|schizophrenia|"
    r"मधुमेह|कैंसर|ट्यूमर"
    r")\b"
)
_DEATH_PRED_RX = re.compile(
    r"(?ix)\b("
    r"you will die|mar\s+jao?ge|maut\s+(aa\s+)?jaye?gi|life\s+ends|"
    r"exact\s+death|mrityu\s+tarikh"
    r")\b"
)
_CURE_GUARANTEE_RX = re.compile(
    r"(?ix)\b("
    r"100\s*(?:%|percent)\s+(cure|thik|recover|theek)|"
    r"guaranteed\s+cure|pakka\s+thik\s+ho\s+jao?ge|definitely\s+cure"
    r")\b"
)
_TIMING_DATE_RX = re.compile(
    r"(?ix)\b("
    r"\d{4}|january|february|march|april|may|june|july|august|"
    r"september|october|november|december|"
    r"kab\s+thik|recovery\s+on|operation\s+on\s+\d"
    r")\b"
)
_SURGERY_MUHURAT_RX = re.compile(
    r"(?ix)\b(operation|surgery)\s+(muhurat|date|on\s+\d|kab\s+karwau)\b"
)


def verify_health_answer(
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
    if _DISEASE_NAME_RX.search(text):
        issues.append("disease_name")
    if _DEATH_PRED_RX.search(text):
        issues.append("death_prediction")
    if _CURE_GUARANTEE_RX.search(text):
        issues.append("cure_guarantee")
    if _SURGERY_MUHURAT_RX.search(text):
        issues.append("surgery_muhurat")
    archetype = str(meta.get("archetype") or "")
    q = (question or "").lower()
    if "kab" not in q and "when" not in q and _TIMING_DATE_RX.search(text):
        issues.append("unsolicited_timing")
    if archetype == "surgery_risk_tone" and _SURGERY_MUHURAT_RX.search(text):
        issues.append("surgery_date_leak")
    return len(issues) == 0, issues


def guard_health_answer(
    question: str,
    answer: str,
    meta: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    ok, issues = verify_health_answer(question, answer, meta)
    guard_meta = {"ok": ok, "issues": issues, "repaired": False}
    text = (answer or "").strip()
    if ok:
        return text, guard_meta
    if "template_labels" in issues:
        text = _BANNED_LABEL_RX.sub("", text).strip()
        guard_meta["repaired"] = True
    if "disease_name" in issues:
        text = _DISEASE_NAME_RX.sub("health zone", text)
        guard_meta["repaired"] = True
    return text, guard_meta

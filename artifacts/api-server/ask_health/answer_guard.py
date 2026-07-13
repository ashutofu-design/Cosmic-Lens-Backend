"""Post-LLM guard: health answer must stay medical-safe."""

from __future__ import annotations

import re
from typing import Any

_BANNED_LABEL_RX = re.compile(
    r"(?ix)(seedha\s*jawab\s*:|conclusion\s*:|निष्कर्ष\s*:|verdict\s*:)"
)
_DISEASE_NAME_RX = re.compile(
    r"(?ix)\b("
    r"diabetes|cancer|kanser|carcinoma|tumor|tumour|tumors|"
    r"hiv|aids|tuberculosis|\btb\b|"
    r"arthritis|asthma|asthama|epilepsy|parkinson|schizophrenia|"
    r"leukemia|leukaemia|lymphoma|"
    r"मधुमेह|कैंसर|ट्यूमर|एचआईवी|अस्थमा"
    r")\b"
)


def _normalize_disease_token(token: str) -> str:
    t = (token or "").strip().lower()
    if t == "asthama":
        return "asthma"
    return t


def _disease_tokens_in(text: str) -> set[str]:
    return {_normalize_disease_token(m.group(1)) for m in _DISEASE_NAME_RX.finditer(text or "")}


_DEATH_PRED_RX = re.compile(
    r"(?ix)\b("
    r"you will die|mar\s+jao?ge|mar\s+jaoge|maut\s+(aa\s+)?jaye?gi|"
    r"life\s+ends|exact\s+death|mrityu\s+tarikh|death\s+in\s+\d|"
    r"kab\s+mar(?:oge|ungi|unga)|lifespan\s+is|life\s+expectancy\s+is|"
    r"umar\s+\d+\s+saal|kitne\s+saal\s+jioge"
    r")\b"
)
_CURE_GUARANTEE_RX = re.compile(
    r"(?ix)\b("
    r"100\s*(?:%|percent)\s+(cure|thik|recover|theek)|"
    r"guaranteed\s+cure|pakka\s+thik\s+ho\s+jao?ge|definitely\s+cure|"
    r"cancer\s+thik\s+ho\s+jaye?ga|diabetes\s+cure\s+ho\s+jaye?ga"
    r")\b"
)
_TIMING_DATE_RX = re.compile(
    r"(?ix)\b("
    r"\d{4}|january|february|march|april|may|june|july|august|"
    r"september|october|november|december|"
    r"kab\s+thik|recovery\s+on|operation\s+on\s+\d|"
    r"kab\s+mar|death\s+in|mrityu\s+\d"
    r")\b"
)
_SURGERY_MUHURAT_RX = re.compile(
    r"(?ix)\b(operation|surgery)\s+(muhurat|date|on\s+\d|kab\s+karwau)\b"
)

_REFUSE_SNIPPET = (
    "Specific bimari ya death timing chart se allowed nahi — "
    "doctor se consult karein; main sirf general tendency bata sakta hoon."
)


def verify_health_answer(
    question: str,
    answer: str,
    meta: dict[str, Any],
) -> tuple[bool, list[str]]:
    issues: list[str] = []
    text = (answer or "").strip()
    q = (question or "").lower()
    if not text:
        return False, ["empty_answer"]
    if _BANNED_LABEL_RX.search(text):
        issues.append("template_labels")
    answer_diseases = _disease_tokens_in(text)
    question_diseases = _disease_tokens_in(q)
    if answer_diseases and not answer_diseases.issubset(question_diseases):
        issues.append("disease_name")
    if _DEATH_PRED_RX.search(text):
        issues.append("death_prediction")
    if _CURE_GUARANTEE_RX.search(text):
        issues.append("cure_guarantee")
    if _SURGERY_MUHURAT_RX.search(text):
        issues.append("surgery_muhurat")
    archetype = str(meta.get("archetype") or "")
    if "kab" not in q and "when" not in q and _TIMING_DATE_RX.search(text):
        issues.append("unsolicited_timing")
    if archetype == "surgery_risk_tone" and _SURGERY_MUHURAT_RX.search(text):
        issues.append("surgery_date_leak")
    hard = str((meta.get("checks") or {}).get("hard_guard") or "")
    if hard.startswith("REFUSE_") and _DISEASE_NAME_RX.search(text):
        issues.append("refuse_leak_disease")
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
    if "disease_name" in issues or "death_prediction" in issues or "cure_guarantee" in issues:
        text = _DISEASE_NAME_RX.sub("health zone", text)
        text = _DEATH_PRED_RX.sub("", text).strip()
        text = _CURE_GUARANTEE_RX.sub("", text).strip()
        if not text or len(text) < 40:
            text = _REFUSE_SNIPPET
        guard_meta["repaired"] = True
    return text, guard_meta

"""Numerology Ask registry — name correction / harmony questions."""
from __future__ import annotations

import re
from typing import Any

_NUMEROLOGY_RX = re.compile(
    r"(?ix)\b("
    r"numerolog\w*|ank\s*shastra|ank\s*vidya|name\s*correction|naam\s*badal|"
    r"naam\s*change|spelling|name\s*change|expression\s*number|"
    r"driver|conductor|life\s*path|name\s*number"
    r")\b",
)

_NAME_CHANGE_RX = re.compile(
    r"(?ix)\b(naam|name)\b.{0,50}\b("
    r"sahi|theek|change|badal|badl|correction|spelling|harmony|match"
    r")\b",
)

_NAME_HE_RX = re.compile(
    r"(?ix)(?:mere?\s+)?(?:name|naam)\s+"
    r"([a-z][a-z\s'.-]{2,80}?)"
    r"\s+(?:he|hai|hain|hu|hun)\b",
)

_DOB_RX = re.compile(r"(?ix)\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b")


def _dob_from_birth(birth: Any) -> str | None:
    if not isinstance(birth, dict):
        return None
    y = birth.get("year") or birth.get("birth_year")
    m = birth.get("month") or birth.get("birth_month")
    d = birth.get("day") or birth.get("birth_day")
    if y is None or m is None or d is None:
        dob = birth.get("dob") or birth.get("date_of_birth")
        if isinstance(dob, str) and _DOB_RX.search(dob):
            return extract_dob_from_question(dob)
        return None
    try:
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    except (TypeError, ValueError):
        return None


def extract_dob_from_question(question: str, *, birth: Any = None) -> str | None:
    q = (question or "").strip()
    m = _DOB_RX.search(q)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= d <= 31 and 1 <= mo <= 12 and 1900 <= y <= 2100:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    return _dob_from_birth(birth)


def extract_name_from_question(
    question: str,
    *,
    birth: Any = None,
    kundli: dict | None = None,
) -> str | None:
    q = (question or "").strip()
    m = _NAME_HE_RX.search(q)
    if m:
        name = " ".join(m.group(1).split())
        if len(name) >= 3:
            return name.title()
    for src in (kundli, birth):
        if not isinstance(src, dict):
            continue
        for key in ("name", "full_name", "display_name", "user_name"):
            val = src.get(key)
            if isinstance(val, str) and len(val.strip()) >= 3:
                return val.strip().title()
    return None


def is_numerology_name_question(
    question: str,
    *,
    birth: Any = None,
    kundli: dict | None = None,
    llm_intent: dict[str, Any] | None = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    dom = str((llm_intent or {}).get("domain") or "").strip().lower()
    topic_hit = bool(_NUMEROLOGY_RX.search(q) or _NAME_CHANGE_RX.search(q))
    if dom == "numerology":
        topic_hit = True
    if not topic_hit:
        return False
    name = extract_name_from_question(q, birth=birth, kundli=kundli)
    dob = extract_dob_from_question(q, birth=birth)
    return bool(name and dob)


def classify_numerology_archetype(question: str) -> str:
    q = (question or "").lower()
    if _NAME_CHANGE_RX.search(q) or re.search(r"(?ix)\b(change|badal|correction|sahi)\b", q):
        return "name_correction"
    return "name_harmony"

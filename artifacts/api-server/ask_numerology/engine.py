"""Numerology name engine — deterministic Driver/Conductor harmony (tier_a)."""
from __future__ import annotations

from typing import Any

from ask_mr.types import EngineResult

from .numerology_registry import (
    classify_numerology_archetype,
    extract_dob_from_question,
    extract_name_from_question,
)


def _driver_conductor(dob_yyyy_mm_dd: str) -> tuple[int, int]:
    from numerology.core.tier_a import _conductor_from_dob, _driver_from_dob

    return _driver_from_dob(dob_yyyy_mm_dd), _conductor_from_dob(dob_yyyy_mm_dd)


def run_numerology_name_engine(
    question: str,
    *,
    birth: Any = None,
    kundli: dict | None = None,
    wants_explain: bool = False,
    archetype: str | None = None,
) -> EngineResult:
    arch = (archetype or classify_numerology_archetype(question)).strip().lower()
    name = extract_name_from_question(question, birth=birth, kundli=kundli) or ""
    dob = extract_dob_from_question(question, birth=birth) or ""
    driver, conductor = _driver_conductor(dob)
    if not name or not driver:
        raise ValueError("numerology name engine requires name and valid dob")

    from numerology.core.tier_a import name_correction_suggestions

    out = name_correction_suggestions(name, driver, conductor)
    if not out.get("ok"):
        raise ValueError(out.get("error") or "name_correction failed")

    orig = out.get("original") or {}
    harmony = int(orig.get("harmony_score") or 0)
    name_num = int(orig.get("name_number") or 0)
    verdict_label = str(orig.get("verdict") or "")
    improvements = list(out.get("best_improvements") or [])

    if harmony >= 60 and not improvements:
        verdict = (
            f"Naam '{orig.get('name', name)}' numerology se aligned hai — "
            f"Driver {driver}, Conductor {conductor}, Name# {name_num}, "
            f"harmony {harmony}/100 ({verdict_label}). Change ki zarurat nahi."
        )
        locked = f"KEEP — {orig.get('name', name)} (harmony {harmony}/100)"
    elif improvements:
        top = improvements[0]
        verdict = (
            f"Current naam harmony {harmony}/100 ({verdict_label}) — thoda improve ho sakta hai. "
            f"Top spelling variant: '{top.get('name')}' "
            f"(Name# {top.get('name_number')}, score {top.get('harmony_score')}/100, "
            f"+{top.get('delta_vs_original')} vs original)."
        )
        locked = f"TRY — {top.get('name')} (harmony {top.get('harmony_score')}/100)"
    else:
        verdict = (
            f"Naam '{orig.get('name', name)}' — Driver {driver}, Conductor {conductor}, "
            f"Name# {name_num}, harmony {harmony}/100 ({verdict_label}). "
            f"Legal naam same rakh sakte ho; social/business spelling optional tweak."
        )
        locked = f"REVIEW — harmony {harmony}/100"

    evidence = [
        f"DOB {dob} → Driver (Mulank) {driver}, Conductor (Bhagyank) {conductor}.",
        f"Name '{orig.get('name', name)}' → Expression/Name number {name_num}.",
        f"Harmony score {harmony}/100 — verdict {verdict_label}.",
        str(out.get("note") or ""),
    ]
    for item in improvements[:2]:
        evidence.append(
            f"Variant '{item.get('name')}' → Name# {item.get('name_number')}, "
            f"score {item.get('harmony_score')}/100 (+{item.get('delta_vs_original')})."
        )

    return EngineResult(
        archetype=arch,
        verdict=verdict,
        confidence="high" if harmony >= 60 else "medium",
        word_budget=100 if wants_explain else 85,
        answer_plan="Numerology name harmony — Driver/Conductor + spelling variants only.",
        summary=[
            "QUESTION FOCUS: naam numerology sahi hai ya change — locked tier_a harmony.",
            f"LOCKED_PICK: {locked}",
            "Chart/kundli mix mat karo — sirf naam+DOB numerology facts.",
        ],
        evidence=[e for e in evidence if e][:10],
        ignore=["nakshatra", "tithi", "kundli lagna", "legal name change mandate"],
        checks={
            "slice_type": "numerology_engine_v1",
            "archetype": arch,
            "driver": driver,
            "conductor": conductor,
            "name_number": name_num,
            "harmony_score": harmony,
            "dob": dob,
            "name": orig.get("name", name),
        },
    )


def numerology_engine_slice_meta(result: EngineResult) -> dict[str, Any]:
    return {
        "slice": "numerology_engine_v1",
        "topic": "numerology",
        "archetype": result.archetype,
        "verdict": result.verdict,
        "summary": list(result.summary or []),
        "evidence": list(result.evidence or []),
        "ignore": list(result.ignore or []),
        "checks": dict(result.checks or {}),
        "skip_llm": bool(result.skip_llm),
        "word_budget": int(result.word_budget or 85),
        "narrator_mode": "engine_facts_only",
    }

"""Litigation remedy attachment — 3-tier stack via remedy engine v1."""

from __future__ import annotations

import re
from typing import Any

from remedy import get_remedies, render_for_locked_facts

from .engines._litigation_base import litigation_strength_score, reader

_REMEDY_RX = re.compile(
    r"(?ix)\b("
    r"upay|upaay|upaya|remedy|remedies|solution|mantra|puja|pooja|daan|donation|"
    r"totka|parihar|nivaran|shanti|gemstone|ratna|pukhraj|neelam|moonga|"
    r"kya\s+karun|kya\s+karna|kya\s+karein|what\s+should\s+i\s+do|"
    r"bachne\s+ke\s+liye|case\s+se\s+bach|nazar\s+utar|dosh\s+ka\s+upay|"
    r"problem\s+ka\s+upay|upay\s+kya|remedy\s+kya|solution\s+kya|"
    r"kaise\s+bache|kaise\s+nikle|nikalne\s+ka\s+upay|chhutkara\s+upay|"
    r"parihar\s+kya|shanti\s+ke\s+liye|mantra\s+kya|puja\s+kya"
    r")\b"
)

_STRONG_LITIGATION_RX = re.compile(
    r"(?ix)\b("
    r"mukadma|mukadama|court|case|kanoon|legal|litigation|"
    r"law\s*suit|lawsuit|dispute|fir|police|thana|jail|prison|bail|zamanat|"
    r"criminal|civil|advocate|vakil|lawyer|hearing|verdict|acquittal"
    r")\b"
)

_ARCHETYPE_AREAS: dict[str, list[str]] = {
    "litigation_remedy": ["legal_documents", "advocate_strategy", "legal_stress"],
    "litigation_yog": ["legal_documents", "conflict_calm", "advocate_strategy"],
    "case_outcome": ["advocate_strategy", "legal_documents", "conflict_calm"],
    "court_delay": ["delay_patience", "advocate_strategy", "legal_documents"],
    "bail_theme": ["bail_support", "legal_documents", "advocate_strategy"],
    "jail_concern": ["bail_support", "criminal_defence", "legal_stress"],
    "police_fir": ["police_fir", "legal_documents", "criminal_defence"],
    "criminal_case": ["criminal_defence", "legal_documents", "conflict_calm"],
    "civil_litigation": ["civil_dispute", "legal_documents", "advocate_strategy"],
    "legal_obstacles": ["delay_patience", "legal_stress", "advocate_strategy"],
    "enemy_case": ["conflict_calm", "advocate_strategy", "legal_documents"],
    "acquittal_relief": ["acquittal_relief", "advocate_strategy", "legal_documents"],
    "lawyer_support": ["advocate_strategy", "legal_documents", "legal_stress"],
    "family_court": ["family_court", "legal_documents", "advocate_strategy"],
    "general_litigation": ["legal_documents", "court_attendance", "advocate_strategy"],
}

_HIGH_STRESS_ARCHETYPES = frozenset({
    "jail_concern", "criminal_case", "police_fir", "bail_theme",
})

_ACTIVE_ARCHETYPES = frozenset({
    "case_outcome", "court_delay", "acquittal_relief", "enemy_case",
    "legal_obstacles", "family_court", "civil_litigation",
})


def is_litigation_remedy_question(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q or not _REMEDY_RX.search(q):
        return False
    return bool(_STRONG_LITIGATION_RX.search(q)) or bool(
        re.search(r"(?ix)\b(court|case|mukadma|legal|fir|bail|jail|kanooni)\b", q)
    )


def pick_remedy_planets(kundli: dict) -> list[dict[str, Any]]:
    r = reader(kundli)
    weights = {
        "Mars": 14,
        "Saturn": 13,
        "Rahu": 12,
        "Mercury": 10,
        "Jupiter": 9,
        "Sun": 7,
        "Moon": 6,
        "Venus": 5,
        "Ketu": 5,
    }
    scored: list[dict[str, Any]] = []
    for name, base in weights.items():
        p = r.planet(name) or {}
        house = int(p.get("house") or 0)
        score = float(base)
        if house in (6, 8, 12):
            score += 10
        elif house in (1, 3, 10, 11):
            score += 4
        elif house == 7:
            score += 3
        scored.append({"name": name, "score": score})
    scored.sort(key=lambda x: -x["score"])
    return scored[:3]


def pick_remedy_severity(archetype: str, kundli: dict) -> str:
    if archetype in _HIGH_STRESS_ARCHETYPES:
        return "high_stress"
    if archetype in _ACTIVE_ARCHETYPES:
        return "active_case"
    score, _ = litigation_strength_score(kundli)
    if score < 50:
        return "consult"
    return "watchful"


def pick_remedy_areas(archetype: str) -> list[str]:
    return list(_ARCHETYPE_AREAS.get(archetype, _ARCHETYPE_AREAS["general_litigation"]))


def build_litigation_remedy_block(
    kundli: dict,
    question: str,
    archetype: str,
    *,
    duration_days: int = 21,
) -> dict[str, Any]:
    planets = pick_remedy_planets(kundli)
    areas = pick_remedy_areas(archetype)
    severity = pick_remedy_severity(archetype, kundli)
    result = get_remedies(
        "litigation",
        planets=planets,
        areas=areas,
        severity=severity,
        duration_days=duration_days,
    )
    rendered = render_for_locked_facts(result)
    return {
        "result": result,
        "rendered": rendered,
        "severity": severity,
        "planets": planets,
        "areas": areas,
    }


def attach_remedy_to_result(result, kundli: dict, question: str):
    """Attach 3-tier remedy block when user asked for upay/remedy."""
    if not is_litigation_remedy_question(question):
        return result
    if (result.checks or {}).get("remedy_text"):
        return result
    block = build_litigation_remedy_block(
        kundli,
        question,
        result.archetype,
    )
    if not block.get("rendered"):
        return result
    checks = dict(result.checks or {})
    checks["remedy_available"] = True
    checks["remedy_severity"] = block["severity"]
    checks["remedy_text"] = block["rendered"]
    result.checks = checks
    summary = list(result.summary or [])
    summary.append("REMEDY MODE: user asked upay — give practical FIRST, ayurvedic second, vedic last.")
    summary.append("Quote remedy lines verbatim from REMEDIES block; never invent mantras/gems.")
    result.summary = summary
    evidence = list(result.evidence or [])
    evidence.append(
        "Remedy stack attached — 3-tier (practical → ayurvedic → BPHS vedic) for top litigation grahas."
    )
    result.evidence = evidence[:12]
    if result.archetype != "litigation_remedy":
        result.word_budget = max(int(result.word_budget or 80), 110)
    return result

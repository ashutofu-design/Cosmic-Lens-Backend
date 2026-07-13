"""Question-aware health JSON blocks — what LLM should pick + what answer used."""

from __future__ import annotations

import re
from typing import Any

_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

_TRAVEL_RX = re.compile(
    r"(?ix)\b(travel|yatra|trip|tour|safar|videsh|abroad|flight|journey)\b"
)
_STRESS_RX = re.compile(
    r"(?ix)\b(stress|anxiety|tension|mann|mental|depression|neend|sleep|anxiety)\b"
)
_SURGERY_RX = re.compile(
    r"(?ix)\b(operation|surgery|shastra[\s-]?kriya|hospital)\b"
)
_RESP_RX = re.compile(
    r"(?ix)\b(thand|thandi|sardi|cold|khansi|saans|breath|chest|zukam|flu|allerg)\b"
)
_CHRONIC_RX = re.compile(
    r"(?ix)\b(chronic|lambi|bahar\s+nahi|baar\s+baar|recurring|persistent)\b"
)
_OVERVIEW_RX = re.compile(
    r"(?ix)(health ke bare|health ke baare|meri sehat|mere health|overall health|"
    r"health overview|sehat ke bare)"
)
_HOUSE_RX = re.compile(
    r"(?ix)\b(?:(?:(\d{1,2})(?:st|nd|rd|th)?)\s*(?:ghar|house)|(?:ghar|house|h)\s*(\d{1,2})|"
    r"h\s*(\d{1,2}))\b"
)
_PLANET_IN_HOUSE_RX = re.compile(
    r"(?ix)\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b"
    r".{0,40}?(?:(?:ghar|house|h)\s*(\d{1,2})|(\d{1,2})(?:st|nd|rd|th)?\s*(?:ghar|house))"
)


def classify_health_question_focus(question: str) -> str:
    q = (question or "").strip()
    if not q:
        return "general_health"
    if _TRAVEL_RX.search(q) and re.search(
        r"(?ix)\b(health|sehat|issue|problem|bimari|beemar|sick|tabiyat|immunity)\b", q
    ):
        return "travel_health"
    if _SURGERY_RX.search(q):
        return "surgery_risk"
    if _STRESS_RX.search(q):
        return "mental_stress"
    if _RESP_RX.search(q):
        return "respiratory"
    if _CHRONIC_RX.search(q):
        return "chronic"
    if _OVERVIEW_RX.search(q):
        return "overview"
    if re.search(r"(?ix)\b(kyun|kyon|why|kaise|how)\b", q):
        return "cause"
    return "general_health"


_FOCUS_BLOCKS: dict[str, list[dict[str, str]]] = {
    "travel_health": [
        {"id": "d1.house_lords.h6", "label": "D1 6th lord (disease/health issues)", "why": "Travel pe illness → 6th"},
        {"id": "d1.house_lords.h9", "label": "D1 9th lord (travel/far journeys)", "why": "Travel axis"},
        {"id": "d1.house_lords.h3", "label": "D1 3rd lord (short travel)", "why": "Safar / local trips"},
        {"id": "d1.house_lords.h12", "label": "D1 12th lord (foreign/hospital)", "why": "Videsh / hospital tone"},
        {"id": "d1.planets@3,6,9,12", "label": "Planets in 3rd/6th/9th/12th", "why": "Travel-health link houses"},
        {"id": "d1.afflictions", "label": "Afflictions (dusthana)", "why": "Pressure signals"},
        {"id": "d1.dimensions.preventive_risk", "label": "Preventive risk dimension", "why": "Why issues recur"},
        {"id": "d1.dimensions.chronic_tendency", "label": "Chronic tendency dimension", "why": "Repeat pattern"},
    ],
    "surgery_risk": [
        {"id": "d1.house_lords.h6", "label": "D1 6th lord", "why": "Illness / medical care"},
        {"id": "d1.house_lords.h8", "label": "D1 8th lord", "why": "Surgery / chronic"},
        {"id": "d1.planets@Mars,Saturn", "label": "Mars / Saturn", "why": "Surgery & cut themes"},
        {"id": "d1.dimensions.surgery_risk_tone", "label": "Surgery risk dimension", "why": "Primary"},
        {"id": "d1.afflictions", "label": "Afflictions", "why": "Pressure signals"},
    ],
    "mental_stress": [
        {"id": "d1.planets@Moon", "label": "Moon", "why": "Mind / emotion"},
        {"id": "d1.house_lords.h4", "label": "D1 4th lord", "why": "Mental peace"},
        {"id": "d1.house_lords.h6", "label": "D1 6th lord", "why": "Stress / diseases"},
        {"id": "d1.dimensions.mental_stress", "label": "Mental stress dimension", "why": "Primary"},
        {"id": "d1.sub_flags", "label": "Sub flags (moon_afflicted)", "why": "Mind pressure flags"},
    ],
    "respiratory": [
        {"id": "d1.house_lords.h6", "label": "D1 6th lord", "why": "Illness zone"},
        {"id": "d1.planets@Moon,Saturn,Venus", "label": "Moon / Saturn / Venus", "why": "Cold / lungs tone"},
        {"id": "d1.afflictions", "label": "Afflictions", "why": "H6/H8 pressure"},
        {"id": "d1.dimensions.preventive_risk", "label": "Preventive risk", "why": "Tendency"},
    ],
    "chronic": [
        {"id": "d1.house_lords.h8", "label": "D1 8th lord", "why": "Chronic axis"},
        {"id": "d1.house_lords.h6", "label": "D1 6th lord", "why": "Disease"},
        {"id": "d1.dimensions.chronic_tendency", "label": "Chronic tendency", "why": "Primary"},
        {"id": "d1.afflictions", "label": "Afflictions", "why": "Dusthana pressure"},
    ],
    "overview": [
        {"id": "d1.dimensions.overall_vitality", "label": "Overall vitality", "why": "Overview foundation"},
        {"id": "d1.dimensions.mental_stress", "label": "Mental stress", "why": "Energy / mind"},
        {"id": "d1.dimensions.chronic_tendency", "label": "Chronic tendency", "why": "Long-term"},
        {"id": "d1.sub_flags", "label": "Sub flags", "why": "Soft overview signals"},
        {"id": "d1.lagnesh", "label": "Lagnesh", "why": "Body foundation"},
    ],
    "cause": [
        {"id": "d1.house_lords.h6", "label": "D1 6th lord", "why": "Why illness"},
        {"id": "d1.afflictions", "label": "Afflictions", "why": "Cause signals"},
        {"id": "d1.dimensions", "label": "Health dimensions", "why": "Relevant why"},
        {"id": "d1.planets", "label": "Relevant planets", "why": "Chart proof for kyun"},
    ],
    "general_health": [
        {"id": "d1.health_houses", "label": "Health houses (1/6/8/12)", "why": "Core health pack"},
        {"id": "d1.house_lords.h6", "label": "D1 6th lord", "why": "Disease axis"},
        {"id": "d1.afflictions", "label": "Afflictions", "why": "Pressure"},
        {"id": "d1.dimensions", "label": "Dimensions snapshot", "why": "General read"},
        {"id": "d1.lagnesh", "label": "Lagnesh", "why": "Body"},
    ],
}


def expected_blocks_for_question(question: str) -> tuple[str, list[dict[str, str]]]:
    focus = classify_health_question_focus(question)
    blocks = list(_FOCUS_BLOCKS.get(focus) or _FOCUS_BLOCKS["general_health"])
    return focus, blocks


def _houses_in_answer(answer: str) -> list[int]:
    found: set[int] = set()
    for m in _HOUSE_RX.finditer(answer or ""):
        for g in m.groups():
            if g:
                h = int(g)
                if 1 <= h <= 12:
                    found.add(h)
    return sorted(found)


def _planets_in_answer(answer: str) -> list[str]:
    out: list[str] = []
    text = answer or ""
    for name in _PLANET_NAMES:
        if re.search(rf"\b{re.escape(name)}\b", text, re.I):
            out.append(name)
    return out


def _planet_house_cites(answer: str) -> list[str]:
    cites: list[str] = []
    for m in _PLANET_IN_HOUSE_RX.finditer(answer or ""):
        planet = m.group(1)
        house = m.group(2) or m.group(3)
        if planet and house:
            cites.append(f"{planet} H{int(house)}")
    return cites


def used_blocks_from_answer(answer: str) -> dict[str, Any]:
    """Detect chart blocks the answer actually referenced."""
    text = (answer or "").strip()
    houses = _houses_in_answer(text)
    planets = _planets_in_answer(text)
    cites = _planet_house_cites(text)
    used: list[dict[str, str]] = []
    if cites:
        used.append({
            "id": "answer.planet_house_cites",
            "label": "Planet + house cites",
            "detail": ", ".join(cites),
        })
    if planets and not cites:
        used.append({
            "id": "answer.planets",
            "label": "Planets named",
            "detail": ", ".join(planets),
        })
    if houses:
        used.append({
            "id": "answer.houses",
            "label": "Houses referenced",
            "detail": ", ".join(f"H{h}" for h in houses),
        })
    dim_hits = []
    for key, words in (
        ("overall_vitality", r"(?ix)vitality|energy|foundation"),
        ("mental_stress", r"(?ix)stress|mann|mental|tension|neend"),
        ("chronic_tendency", r"(?ix)chronic|lambi|baar\s+baar"),
        ("preventive_risk", r"(?ix)immunity|prevent|recurr"),
        ("surgery_risk_tone", r"(?ix)operation|surgery|procedure"),
        ("recovery_capacity", r"(?ix)recover|recovery|heal"),
    ):
        if re.search(words, text):
            dim_hits.append(key)
    if dim_hits:
        used.append({
            "id": "answer.dimensions",
            "label": "Dimension themes in answer",
            "detail": ", ".join(dim_hits),
        })
    if not used and text:
        used.append({
            "id": "answer.plain_language",
            "label": "Plain-language answer (no explicit planet/house cite)",
            "detail": "LLM may have used JSON internally without naming charts",
        })
    return {
        "planets": planets,
        "houses": houses,
        "planet_house_cites": cites,
        "dimension_themes": dim_hits,
        "blocks": used,
    }


def build_health_selected_blocks(
    question: str,
    answer: str = "",
    *,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Admin step-4 payload: expected vs used JSON blocks for this health question."""
    focus, expected = expected_blocks_for_question(question)
    used = used_blocks_from_answer(answer)
    contract = {}
    if isinstance(meta, dict):
        for key in ("user_wants", "intent", "normalized_question", "question_type"):
            val = str(meta.get(key) or "").strip()
            if val:
                contract[key] = val

    expected_ids = {b["id"] for b in expected}
    used_houses = set(used.get("houses") or [])
    overlap_notes: list[str] = []
    if focus == "travel_health":
        travel_hs = {3, 6, 9, 12}
        hit = sorted(used_houses & travel_hs)
        if hit:
            overlap_notes.append(
                f"Answer touched travel-health houses: {', '.join(f'H{h}' for h in hit)}"
            )
        elif used.get("blocks") and (used.get("blocks") or [{}])[0].get("id") == "answer.plain_language":
            overlap_notes.append(
                "Answer stayed plain language — no explicit 3/6/9/12 house cite visible"
            )

    return {
        "applies": True,
        "focus": focus,
        "focus_label": {
            "travel_health": "Travel + health (6th↔9th link)",
            "surgery_risk": "Surgery / operation risk",
            "mental_stress": "Mental stress / mind",
            "respiratory": "Cold / respiratory",
            "chronic": "Chronic tendency",
            "overview": "General health overview",
            "cause": "Cause / why (kyun)",
            "general_health": "General health",
        }.get(focus, focus),
        "expected_blocks": expected,
        "used_in_answer": used,
        "overlap_notes": overlap_notes,
        "contract": contract,
        "expected_block_ids": sorted(expected_ids),
    }

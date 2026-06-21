"""Body-system subdomain engines — digestive, cardio, nervous, etc."""

from __future__ import annotations

import re

from ..types import EngineResult
from ._health_base import (
    affliction_lines,
    dim,
    dim_evidence,
    karaka_evidence,
    load_facts,
    lord_evidence,
    vitality_line,
)

_SYSTEM_SPECS: dict[str, dict] = {
    "digestive_health": {
        "label": "Digestive / stomach zone",
        "karakas": [("Mercury", "Digestion karaka"), ("Sun", "Digestive fire")],
        "houses": [("h5", "5th house (digestion region)")],
        "dim": "preventive_risk",
        "verdict_green": "Digestive zone relatively stable — regular meals + hydration help",
        "verdict_yellow": "Digestive zone mixed — acidity/gas tendency possible under stress",
        "verdict_red": "Digestive zone sensitive — meal timing aur light food discipline wise",
    },
    "cardio_health": {
        "label": "Heart / circulation zone",
        "karakas": [("Sun", "Heart karaka"), ("Jupiter", "Circulation support")],
        "houses": [("h4", "4th house (chest cavity)")],
        "dim": "preventive_risk",
        "verdict_green": "Cardio-energy tone supported — routine checkup enough",
        "verdict_yellow": "Cardio zone mixed — stress + lifestyle balance important",
        "verdict_red": "Cardio zone needs care — doctor consult if symptoms, no self-diagnosis",
    },
    "nervous_health": {
        "label": "Nerves / brain-body link",
        "karakas": [("Mercury", "Nerves"), ("Moon", "Mind-body link")],
        "houses": [("h3", "3rd house (communication/nerves)")],
        "dim": "mental_stress",
        "verdict_green": "Nervous system tone relatively calm",
        "verdict_yellow": "Nervous sensitivity mixed — rest + stress control help",
        "verdict_red": "Nervous system under pressure — sleep routine + doctor if persistent",
    },
    "musculoskeletal_health": {
        "label": "Bones / joints / muscles",
        "karakas": [("Mars", "Muscles"), ("Saturn", "Bones/joints")],
        "houses": [("h6", "6th house (acute pain axis)")],
        "dim": "chronic_tendency",
        "verdict_green": "Musculoskeletal tone reasonable — movement + posture help",
        "verdict_yellow": "Stiffness/weakness tendency possible — gentle exercise wise",
        "verdict_red": "Chronic stiffness tendency — physiotherapy/doctor if pain persists",
    },
    "skin_health": {
        "label": "Skin / surface body",
        "karakas": [("Mercury", "Skin karaka"), ("Moon", "Hydration/complexion")],
        "houses": [("h6", "6th house (surface issues)")],
        "dim": "preventive_risk",
        "verdict_green": "Skin vitality tone okay — hydration + sun protection help",
        "verdict_yellow": "Skin sensitivity mixed — allergy triggers watch karo",
        "verdict_red": "Skin zone sensitive — dermatologist if recurring issues",
    },
    "endocrine_health": {
        "label": "Hormone / metabolism zone",
        "karakas": [("Sun", "Vitality core"), ("Jupiter", "Metabolism")],
        "houses": [("h5", "5th house (metabolic fire)")],
        "dim": "chronic_tendency",
        "verdict_green": "Metabolic tone stable — routine lifestyle enough",
        "verdict_yellow": "Metabolic/hormone zone mixed — weight/sleep balance matter",
        "verdict_red": "Endocrine tendency zone active — endocrinologist if symptoms",
    },
    "respiratory_health": {
        "label": "Breath / lungs zone",
        "karakas": [("Mercury", "Breath channel"), ("Moon", "Mucous/fluid")],
        "houses": [("h3", "3rd house (breath)")],
        "dim": "preventive_risk",
        "verdict_green": "Respiratory tone okay — clean air + breathing habits help",
        "verdict_yellow": "Breath zone mixed — pollution/allergy triggers avoid karo",
        "verdict_red": "Respiratory sensitivity tone — pulmonologist if breath issues",
    },
    "immune_health": {
        "label": "Immunity / resistance",
        "karakas": [("Sun", "Core vitality"), ("Mars", "Defence energy")],
        "houses": [("h1", "Lagnesh constitution")],
        "dim": "overall_vitality",
        "verdict_green": "Immunity/resistance tone strong — routine care enough",
        "verdict_yellow": "Immunity mixed — sleep + nutrition boost help",
        "verdict_red": "Immunity weak tone — frequent rest + doctor if often unwell",
    },
}

_SYSTEM_DETECT: list[tuple[str, re.Pattern[str]]] = [
    ("digestive_health", re.compile(
        r"(?ix)\b(digest(?:ion|ive)?|pet\s+dard|stomach|acidity|gas|"
        r"intestine|aant|appetite|bhook|hazme|hajma|liver|jigar|kidney|gurda)\b")),
    ("cardio_health", re.compile(
        r"(?ix)\b(heart|dil\b|cardiac|cardio|blood\s+pressure|\bbp\b|"
        r"hypertension|chest\s+(pain|discomfort)|seene\s+me)\b")),
    ("nervous_health", re.compile(
        r"(?ix)\b(nerve|nerves|nervous|neurolog|jhanjhanahat|tingling|"
        r"numbness|sunn\s+pad|brain|dimag|cognitive)\b")),
    ("musculoskeletal_health", re.compile(
        r"(?ix)\b(joint|jod|jodo|knee|ghutna|back\s*pain|kamar|bone|haddi|"
        r"spine|reedh|muscle|maans|cramp|akadan|stiffness|orthop)\b")),
    ("skin_health", re.compile(
        r"(?ix)\b(skin|chamdi|twacha|rash|acne|pimple|muhase|eczema|daag)\b")),
    ("endocrine_health", re.compile(
        r"(?ix)\b(thyroid|hormone|hormonal|sugar\s+level|metabolism|"
        r"weight\s+(gain|loss)|wajan|motapa|pcod|pcos|endocrin)\b")),
    ("respiratory_health", re.compile(
        r"(?ix)\b(breath|breathing|saans|saans\s+phool|lung|phephra|"
        r"cough|khansi|cold|sardi|zukam|chest\s+infect|nasal|nose\s+block)\b")),
    ("immune_health", re.compile(
        r"(?ix)\b(immunity|immune|baar\s*baar\s+(beemar|bimar|sick)|"
        r"jaldi\s+jaldi\s+(beemar|bimar|sick)|frequently\s+(sick|ill)|"
        r"rog\s*pratirodh|resistance)\b")),
]


def detect_system_archetype(question: str) -> str | None:
    q = (question or "").strip()
    if not q:
        return None
    for arch, rx in _SYSTEM_DETECT:
        if rx.search(q):
            return arch
    return None


def run_system_health(
    kundli: dict,
    question: str,
    *,
    archetype: str,
    wants_explain: bool = False,
) -> EngineResult:
    spec = _SYSTEM_SPECS.get(archetype) or _SYSTEM_SPECS["digestive_health"]
    facts = load_facts(kundli)
    if facts.get("error"):
        raise ValueError(facts["error"])

    dim_key = spec["dim"]
    d = dim(facts, dim_key)
    v = d.get("verdict", "YELLOW")
    if v == "GREEN":
        verdict = spec["verdict_green"]
        confidence = "high"
    elif v == "RED":
        verdict = spec["verdict_red"]
        confidence = "medium"
    else:
        verdict = spec["verdict_yellow"]
        confidence = "medium"

    evidence = [f"System focus: {spec['label']}", vitality_line(facts)]
    for hk, lbl in spec.get("houses", []):
        if hk in (facts.get("house_lords") or {}):
            evidence.append(lord_evidence(facts, hk, lbl))
        elif hk == "h3":
            evidence.append("3rd house (breath/nerves) — check chart 3L placement")
        elif hk == "h5":
            evidence.append("5th house axis — check chart 5L for digestion/metabolism")
    for pname, plbl in spec.get("karakas", []):
        evidence.append(karaka_evidence(facts, pname, plbl))
    evidence.append(dim_evidence(facts, dim_key, "Related health dimension"))
    evidence.extend(affliction_lines(facts, limit=2))

    return EngineResult(
        archetype=archetype,
        verdict=verdict,
        confidence=confidence,
        word_budget=95 if wants_explain else 80,
        answer_plan=f"Answer {spec['label']} tendency — NO disease names, NO dates.",
        summary=["Body-system subdomain.", "Doctor for symptoms — chart = tendency only."],
        evidence=evidence[:8],
        ignore=["disease names", "death", "timing", "cure guarantee", "diagnosis"],
        checks={
            "slice_type": "health_engine_v1",
            "archetype": archetype,
            "system": archetype.replace("_health", ""),
            "dim_v": v,
        },
    )

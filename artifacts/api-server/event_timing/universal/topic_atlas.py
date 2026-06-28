"""Topic → houses/karakas atlas for universal timing fallback (no dedicated engine)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from event_timing._shared.generic_timing_engine import DomainTimingConfig


@dataclass
class TopicAtlasEntry:
    topic_id: str
    label: str
    pattern: re.Pattern[str]
    concern_houses: list[tuple[int, float, str]]
    leak_houses: list[tuple[int, float, str]] = field(default_factory=list)
    karakas: list[tuple[str, float, str]] = field(default_factory=list)
    kp_cusps: list[int] = field(default_factory=list)
    weight: float = 1.0


def _rx(p: str) -> re.Pattern[str]:
    return re.compile(p, re.IGNORECASE | re.VERBOSE)


# Themes WITHOUT a dedicated timing engine — keyword routed only.
TOPIC_ATLAS: list[TopicAtlasEntry] = [
    TopicAtlasEntry(
        "lottery_speculation",
        "Lottery / speculation / windfall",
        _rx(r"\b(lottery|lottary|jackpot|gambling|casino|satta|matka|"
            r"speculation|windfall|lucky\s+draw|prize\s+money)\b"),
        concern_houses=[
            (5, 14.0, "5H (speculation / risk-reward)"),
            (11, 16.0, "11H (gains / fulfillment of desire)"),
            (2, 10.0, "2H (accumulated wealth)"),
        ],
        leak_houses=[(6, 8.0, "6L (loss / debt drag)"), (8, 8.0, "8L (sudden loss)")],
        karakas=[("Jupiter", 10.0, "luck karaka"), ("Rahu", 12.0, "sudden gain karaka")],
        kp_cusps=[2, 5, 11],
    ),
    TopicAtlasEntry(
        "pet_animal",
        "Pet / animal adoption",
        _rx(r"\b(pet|dog|cat|puppy|kitten|animal|parrot|horse|"
            r"adopt\s+pet|pet\s+adopt)\b"),
        concern_houses=[
            (6, 14.0, "6H (small animals / service pets)"),
            (11, 12.0, "11H (fulfillment / companion gain)"),
            (4, 10.0, "4H (home comfort)"),
        ],
        leak_houses=[(8, 6.0, "8L (sudden separation)"), (12, 6.0, "12L (loss)")],
        karakas=[("Mercury", 10.0, "small creatures"), ("Moon", 8.0, "bond/comfort")],
        kp_cusps=[4, 6, 11],
    ),
    TopicAtlasEntry(
        "sibling_family",
        "Sibling / family harmony",
        _rx(r"\b(bhai|behen|sibling|brother|sister|bhai\s+behen|"
            r"family\s+harmony|parivaar|ghar\s+me\s+shanti|"
            r"rishtedar|relative|cousin|mama|mami|chacha)\b"),
        concern_houses=[
            (3, 16.0, "3H (siblings / close kin)"),
            (4, 12.0, "4H (home / family peace)"),
            (11, 10.0, "11H (support network)"),
        ],
        leak_houses=[(6, 10.0, "6L (domestic conflict)"), (8, 6.0, "8L (family stress)")],
        karakas=[("Mars", 10.0, "sibling karaka"), ("Moon", 10.0, "family mind")],
        kp_cusps=[3, 4, 11],
    ),
    TopicAtlasEntry(
        "inheritance_legacy",
        "Inheritance / legacy / ancestral property",
        _rx(r"\b(inheritance|virasat|will|probate|ancestral|"
            r"legacy|heritage|waris|warasat)\b"),
        concern_houses=[
            (8, 16.0, "8H (inheritance / sudden legacy)"),
            (9, 12.0, "9H (fortune / dharma legacy)"),
            (4, 10.0, "4H (ancestral property link)"),
        ],
        leak_houses=[(6, 8.0, "6L (dispute)"), (12, 6.0, "12L (loss/drain)")],
        karakas=[("Saturn", 10.0, "legacy karaka"), ("Jupiter", 10.0, "fortune")],
        kp_cusps=[4, 8, 9],
    ),
    TopicAtlasEntry(
        "surgery_procedure",
        "Surgery / medical procedure timing",
        _rx(r"\b(surgery|operation|surgical|procedure|transplant|"
            r"admission\s+hospital|hospitalization)\b"),
        concern_houses=[
            (6, 16.0, "6H (disease / hospital)"),
            (8, 14.0, "8H (surgery / crisis)"),
            (1, 10.0, "1H (vitality recovery)"),
        ],
        leak_houses=[(12, 8.0, "12L (hospitalization drain)"), (8, 6.0, "8L risk")],
        karakas=[("Mars", 10.0, "surgery karaka"), ("Saturn", 8.0, "chronic/chronic delay")],
        kp_cusps=[1, 6, 8],
    ),
    TopicAtlasEntry(
        "legal_document",
        "Document / registration / certificate (non-court)",
        _rx(r"\b(document|registration|certificate|license|licence|"
            r"paperwork|stamp\s+duty|notary|affidavit)\b"),
        concern_houses=[
            (3, 14.0, "3H (documents / communication)"),
            (9, 12.0, "9H (legal-dharma paperwork)"),
            (11, 10.0, "11H (fulfillment)"),
        ],
        leak_houses=[(6, 8.0, "6L (bureaucratic obstacle)"), (8, 6.0, "8L (delay)")],
        karakas=[("Mercury", 14.0, "documents karaka"), ("Jupiter", 8.0, "lawful approval")],
        kp_cusps=[3, 9, 11],
    ),
    TopicAtlasEntry(
        "creative_project",
        "Creative project / hobby launch",
        _rx(r"\b(hobby|creative\s+project|art\s+project|music\s+album|"
            r"book\s+publish|painting|sculpture|craft)\b"),
        concern_houses=[
            (5, 16.0, "5H (creativity)"),
            (3, 10.0, "3H (skill / hands)"),
            (11, 12.0, "11H (gain from talent)"),
        ],
        leak_houses=[(6, 8.0, "6L (competition)"), (12, 6.0, "12L (self-doubt drain)")],
        karakas=[("Venus", 12.0, "arts karaka"), ("Mercury", 10.0, "skill")],
        kp_cusps=[3, 5, 11],
    ),
]

_GENERAL_FALLBACK = TopicAtlasEntry(
    "general_life_event",
    "General life-event timing (fallback)",
    _rx(r"(?!)"),  # never matches — used as default merge base
    concern_houses=[
        (1, 12.0, "1H (self / initiative)"),
        (9, 10.0, "9H (fortune / dharma)"),
        (10, 12.0, "10H (outcome / karma)"),
        (11, 10.0, "11H (fulfillment / gains)"),
    ],
    leak_houses=[
        (6, 8.0, "6L (obstacles)"),
        (8, 8.0, "8L (sudden blocks)"),
        (12, 6.0, "12L (delay / loss)"),
    ],
    karakas=[
        ("Sun", 10.0, "authority / vitality"),
        ("Moon", 8.0, "mind / mood"),
        ("Jupiter", 10.0, "grace / expansion"),
        ("Mercury", 8.0, "communication / skill"),
    ],
    kp_cusps=[1, 9, 10, 11],
)


def score_topics(question: str) -> list[tuple[float, TopicAtlasEntry]]:
    q = question or ""
    scored: list[tuple[float, TopicAtlasEntry]] = []
    for entry in TOPIC_ATLAS:
        if entry.pattern.search(q):
            scored.append((entry.weight, entry))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def classify_universal_bucket(question: str) -> str:
    scored = score_topics(question)
    if scored:
        return scored[0][1].topic_id
    return _GENERAL_FALLBACK.topic_id


def _merge_entries(entries: list[TopicAtlasEntry]) -> dict[str, Any]:
    """Merge atlas entries into one dynamic config payload."""
    if not entries:
        entries = [_GENERAL_FALLBACK]

    concern: dict[int, tuple[float, str]] = {}
    leak: dict[int, tuple[float, str]] = {}
    karaka: dict[str, tuple[float, str]] = {}
    kp: set[int] = set()
    labels: list[str] = []

    for entry in entries:
        labels.append(entry.label)
        for h, w, lbl in entry.concern_houses:
            prev = concern.get(h)
            concern[h] = (max(prev[0], w) if prev else w, lbl)
        for h, w, lbl in entry.leak_houses:
            prev = leak.get(h)
            leak[h] = (max(prev[0], w) if prev else w, lbl)
        for name, w, lbl in entry.karakas:
            prev = karaka.get(name)
            karaka[name] = (max(prev[0], w) if prev else w, lbl)
        kp.update(entry.kp_cusps)

    concern_houses = [(h, concern[h][0], concern[h][1]) for h in sorted(concern)]
    leak_houses = [(h, leak[h][0], leak[h][1]) for h in sorted(leak)]
    karakas = [(n, karaka[n][0], karaka[n][1]) for n in karaka]
    kp_cusps = sorted(kp)[:6]

    promote = set()
    for h, _, _ in concern_houses:
        promote.update((f"{h}L", f"{h}H"))
    for name, _, _ in karakas:
        promote.add(name)

    obstruct = set()
    for h, _, _ in leak_houses:
        obstruct.update((f"{h}L", f"{h}H"))

    return {
        "topic_ids": [e.topic_id for e in entries],
        "topic_labels": labels,
        "concern_houses": concern_houses,
        "leak_houses": leak_houses,
        "karakas": karakas,
        "kp_cusps": kp_cusps or list(_GENERAL_FALLBACK.kp_cusps),
        "promote_tags": tuple(sorted(promote)),
        "obstruct_tags": tuple(sorted(obstruct)),
        "double_transit_houses": [h for h, _, _ in concern_houses[:2]],
    }


def build_dynamic_config(question: str) -> tuple[DomainTimingConfig, dict[str, Any]]:
    scored = score_topics(question)
    picked = [e for _, e in scored[:2]]
    if not picked:
        picked = [_GENERAL_FALLBACK]
    merged = _merge_entries(picked)

    cfg = DomainTimingConfig(
        domain="universal",
        engine_version="universal_timing_v1.0",
        concern_houses=merged["concern_houses"],
        leak_houses=merged["leak_houses"],
        karakas=merged["karakas"],
        kp_cusps=merged["kp_cusps"],
        promote_tags=merged["promote_tags"],
        obstruct_tags=merged["obstruct_tags"],
        double_transit_houses=merged["double_transit_houses"],
        promised_label="UNIVERSAL_WINDOW_STRONG",
        favourable_label="UNIVERSAL_WINDOW_MODERATE",
        caution_label="UNIVERSAL_DELAY",
        defer_label="UNIVERSAL_LOW_READINESS",
        brand_safety=[
            "Universal fallback — no dedicated engine; window = readiness only.",
            "Cite houses/lords from factors below — exact date invent mat karo.",
            "Low confidence vs domain-specific engines — humble tone rakho.",
            "Clinical/legal/medical actions ke liye professional advice alag se.",
        ],
        llm_directives=[
            "UNIVERSAL_FALLBACK_MODE",
            "NO_INVENTED_DATES",
            "CITE_ENGINE_FACTORS_ONLY",
            "HUMBLE_PROBABILITY",
        ],
    )
    merged["bucket"] = classify_universal_bucket(question)
    return cfg, merged


# Domains with a dedicated elif branch in timing_router.run_timing_engine.
DOMAINS_WITH_DEDICATED_ENGINE: frozenset[str] = frozenset({
    "career",
    "travel",
    "marriage",
    "property",
    "vehicle",
    "foreign_education",
    "education",
    "litigation",
    "love",
    "finance",
    "health",
    "children",
    "spiritual",
    "fame",
    "network",
})

from __future__ import annotations

from ..types import EngineResult
from ._network_base import circle_snapshot, network_score, reader


def _network_result(
    *,
    archetype: str,
    kundli: dict,
    wants_explain: bool,
    verdict_high: str,
    verdict_mid: str,
    verdict_low: str,
    summary: list[str],
    ignore: list[str] | None = None,
) -> EngineResult:
    score, label = network_score(kundli)
    evidence = circle_snapshot(kundli)
    if score >= 72:
        verdict, confidence = verdict_high, "high"
    elif score >= 55:
        verdict, confidence = verdict_mid, "medium"
    else:
        verdict, confidence = verdict_low, "medium"
    return EngineResult(
        archetype=archetype,
        verdict=verdict,
        confidence=confidence,
        word_budget=95 if wants_explain else 85,
        answer_plan=(
            f"Answer {archetype.replace('_', ' ')} ONLY from 11H occupants + 11L + "
            "Mars + Mercury evidence — NOT Moon/Sun unless they sit in 11H."
        ),
        summary=summary,
        evidence=evidence,
        ignore=ignore or ["invented friend names", "exact friend count", "gossip"],
        checks={
            "slice_type": "network_engine_v1",
            "archetype": archetype,
            "network_score": score,
            "network_label": label,
            "open_chart_qa": True,
        },
    )


def run_social_circle_quality(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
) -> EngineResult:
    return _network_result(
        archetype="social_circle_quality",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict_high="Social circle overall supportive — 11H + Mars/Mercury tone favourable",
        verdict_mid="Social circle mixed — achhe dost hain par kabhi friction ya distance bhi",
        verdict_low="Social circle me careful rehna — chart selective trust + boundaries suggest karta hai",
        summary=[
            "QUESTION FOCUS: social circle good/bad — NOT kab/when.",
            "MUST cite 11H sign/lord/occupants + Mars + Mercury.",
            "Do NOT answer from generic Moon/Sun unless they are IN 11H.",
        ],
    )


def run_friends_support(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
) -> EngineResult:
    return _network_result(
        archetype="friends_support",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict_high="Friends/support system strong — 11H gains axis + helpful planet tone",
        verdict_mid="Friends help mil sakti hai par consistently nahi — chart mixed support",
        verdict_low="Support system weak tone — rely on self + few trusted people",
        summary=["QUESTION FOCUS: friends' support/help — use 11H + 11L + Mars."],
    )


def run_enmity_in_circle(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
) -> EngineResult:
    score, label = network_score(kundli)
    evidence = circle_snapshot(kundli)
    r = reader(kundli)
    mars = r.planet("Mars") or {}
    if score <= 54 or int(mars.get("house") or 0) in (6, 8, 12):
        verdict = "Circle me rivalry/tension tone — Mars + malefic 11H link caution"
        confidence = "medium"
    else:
        verdict = "Major enmity tone weak — friction possible but overall circle manageable"
        confidence = "medium"
    return EngineResult(
        archetype="enmity_in_circle",
        verdict=verdict,
        confidence=confidence,
        word_budget=90 if wants_explain else 80,
        answer_plan="Enmity Q → 11H occupants + Mars placement + Saturn/Rahu if in 11H.",
        summary=["QUESTION FOCUS: enemies/rivalry in circle — practical boundaries line."],
        evidence=evidence,
        ignore=["naming enemies", "revenge advice"],
        checks={
            "slice_type": "network_engine_v1",
            "archetype": "enmity_in_circle",
            "network_score": score,
        },
    )


def run_influential_network(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
) -> EngineResult:
    return _network_result(
        archetype="influential_network",
        kundli=kundli,
        wants_explain=wants_explain,
        verdict_high="Influential/bade log connections possible — 11H + strong 11L support",
        verdict_mid="Network me kuch helpful contacts hain par effort se build karna padega",
        verdict_low="VIP network abhi limited — chart self-made networking pe focus",
        summary=["QUESTION FOCUS: powerful contacts / social capital — 11H + 10H link ok briefly."],
    )


def run_general_network(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
) -> EngineResult:
    return run_social_circle_quality(kundli, question, wants_explain=wants_explain)

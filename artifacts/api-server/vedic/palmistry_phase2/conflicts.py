"""Contradiction detection and priority-aware evidence fusion."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

TENSION_PATTERN_VERSION = "1.0"
TENSION_PATTERNS = (
    {
        "pattern_id": "commitment_independence_tension",
        "left": {"domain": "marriage", "categories": {"union", "commitment", "union_line_observation"}},
        "right": {"domain": "personality", "categories": {"independence"}},
        "interpretation": "Reliable measurements support both commitment symbolism and independence symbolism; traditional palmistry treats this as a mixed tension, not a deterministic outcome.",
    },
)


def resolve_domain(
    signals: list[dict[str, Any]], strong_threshold: float, *,
    require_multiple_families: bool = False,
) -> dict[str, Any]:
    positive = [item for item in signals if item["signed_score"] > 0]
    negative = [item for item in signals if item["signed_score"] < 0]
    support = sum(item["weighted_score"] for item in positive)
    contradict = sum(item["weighted_score"] for item in negative)
    total = support + contradict
    net = support - contradict
    maximum_source_confidence = max(
        (item["propagated_confidence"] for item in signals), default=0.0
    )
    families = sorted({item["family"] for item in signals})
    mixed = bool(positive and negative and min(support, contradict) >= .20 * max(support, contradict))
    if mixed:
        balance = min(support, contradict) / max(support, contradict)
        confidence = min(maximum_source_confidence, balance * min(1.0, total))
    else:
        confidence = min(
            maximum_source_confidence,
            (abs(net) / total if total else 0.0) * min(1.0, total),
        )
    if not signals:
        classification = "insufficient"
    elif mixed:
        classification = "mixed"
    elif confidence >= strong_threshold and len(families) >= 2:
        classification = "strong"
    elif require_multiple_families and len(families) < 2:
        classification = "weak"
    elif confidence >= .60:
        classification = "moderate"
    else:
        classification = "weak"
    conflicts = []
    by_category: dict[str, list[dict]] = defaultdict(list)
    for signal in signals:
        by_category[signal["category"]].append(signal)
    for category, items in by_category.items():
        if any(item["polarity"] > 0 for item in items) and any(item["polarity"] < 0 for item in items):
            conflicts.append({
                "category": category,
                "supporting_rule_ids": [item["rule_id"] for item in items if item["polarity"] > 0],
                "contradictory_rule_ids": [item["rule_id"] for item in items if item["polarity"] < 0],
                "resolution": "mixed_signal_preserved",
            })
    if positive and negative and not conflicts:
        conflicts.append({
            "category": "cross_category_domain_conflict",
            "supporting_rule_ids": [item["rule_id"] for item in positive],
            "contradictory_rule_ids": [item["rule_id"] for item in negative],
            "resolution": "mixed_signal_preserved",
        })
    supporting = positive if net >= 0 else negative
    conclusion_items = signals if mixed else supporting
    conclusion_evidence = [
        {
            "feature_path": evidence["feature_path"],
            "raw_measurement": evidence["raw_value"],
            "signal": item["signal"],
            "source_confidence": evidence["source_confidence"],
            "propagated_confidence": item["propagated_confidence"],
            "rule_ids": [item["rule_id"]],
        }
        for item in conclusion_items
        for evidence in item["evidence"]
    ]
    interpretations = list(
        dict.fromkeys(item["interpretation"] for item in conclusion_items)
    )
    conclusion = {
        "conclusion": (
            ("Mixed traditional signals: " if mixed else "") + " ".join(interpretations)
            if interpretations
            else "Insufficient reliable measured evidence."
        ),
        "interpretation": interpretations,
        "confidence": round(confidence, 4),
        "classification": classification,
        "evidence": conclusion_evidence,
        "rule_ids": list(
            dict.fromkeys(item["rule_id"] for item in conclusion_items)
        ),
    }
    return {
        "classification": classification,
        "confidence": round(confidence, 4),
        "mixed_signal": mixed,
        "normalized_score": round(net / total, 4) if total else 0.0,
        "normalized_internal_score": round((net / total + 1) / 2, 4) if total else 0.5,
        "score_metadata": {"visibility": "internal_only", "not_a_probability": True},
        "feature_families": families,
        "positive_evidence": positive,
        "negative_evidence": negative,
        "supporting_evidence": supporting,
        "contradictory_evidence": negative if net >= 0 else positive,
        "contradictions": conflicts,
        "conclusion": conclusion,
    }


def detect_cross_domain_tensions(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tensions = []
    for pattern in TENSION_PATTERNS:
        left = [
            item for item in signals
            if item["domain"] == pattern["left"]["domain"]
            and item["category"] in pattern["left"]["categories"]
            and item["polarity"] > 0
        ]
        right = [
            item for item in signals
            if item["domain"] == pattern["right"]["domain"]
            and item["category"] in pattern["right"]["categories"]
            and item["polarity"] > 0
        ]
        if not left or not right:
            continue
        evidence = [
            {
                "domain": item["domain"], "category": item["category"],
                "rule_id": item["rule_id"], "confidence": item["propagated_confidence"],
                "feature_paths": [entry["feature_path"] for entry in item["evidence"]],
            }
            for item in left + right
        ]
        tensions.append({
            "pattern_version": TENSION_PATTERN_VERSION,
            "pattern_id": pattern["pattern_id"],
            "classification": "mixed_tension",
            "interpretation": pattern["interpretation"],
            "confidence": round(min(item["propagated_confidence"] for item in left + right), 4),
            "evidence": evidence,
        })
    return tensions

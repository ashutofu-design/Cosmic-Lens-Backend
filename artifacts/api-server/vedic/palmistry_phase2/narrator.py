"""Grounded narration interfaces; narrators receive structured analysis only."""
from __future__ import annotations

from typing import Any, Protocol

DISCLAIMER = (
    "This is a traditional palmistry interpretation, not a scientific assessment. "
    "Confidence reflects source measurement quality and rule agreement, not certainty. "
    "It does not diagnose health, predict lifespan, promise wealth, or determine future events or dates."
)
FORBIDDEN = ("you are diagnosed", "you have a disease", "you will die", "death date", "guaranteed wealth", "will become rich", "exactly on")


class StructuredNarrator(Protocol):
    def narrate(self, analysis: dict[str, Any]) -> dict[str, Any]: ...


class DeterministicSafeNarrator:
    """Template narrator that can only copy conclusions already in the analysis."""

    def narrate(self, analysis: dict[str, Any]) -> dict[str, Any]:
        sections = {
            "Overall Palm Profile": _domain_statements(analysis, tuple(analysis["domains"])),
            "Personality": _domain_statements(analysis, ("personality",)),
            "Emotional & Relationship Nature": _domain_statements(analysis, ("love_relationships",)),
            "Love/Marriage": _domain_statements(analysis, ("love_relationships", "marriage")),
            "Career": _domain_statements(analysis, ("career", "recognition_success")),
            "Money": _domain_statements(analysis, ("money",)),
            "Strengths": _signal_statements(analysis, polarity=1),
            "Challenges": _signal_statements(analysis, polarity=-1),
            "Important Patterns": [
                {
                    "text": item["interpretation"],
                    "rule_ids": [entry["rule_id"] for entry in item["evidence"]],
                    "confidence": item["confidence"],
                    "source": "cross_domain_tensions",
                }
                for item in analysis.get("cross_domain_tensions", [])
            ],
            "Traditional Palmistry Guidance": _domain_statements(
                analysis, tuple(analysis["domains"]), limit=1
            ),
            "Confidence & Limitations": [{
                "text": DISCLAIMER,
                "rule_ids": [],
                "confidence": analysis.get("input_scan_confidence", 0.0),
                "source": "disclaimer",
            }],
        }
        text = "\n".join(
            f"{heading}: " + " ".join(item["text"] for item in statements)
            for heading, statements in sections.items() if statements
        )
        lowered = text.lower()
        if any(term in lowered for term in FORBIDDEN):
            raise ValueError("Narrator produced forbidden deterministic or medical language.")
        return {
            "narrator": "deterministic_safe/1.0",
            "grounded_only": True,
            "sections": sections,
            "text": text,
            "disclaimer": DISCLAIMER,
        }


def _domain_statements(
    analysis: dict[str, Any], domain_names: tuple[str, ...], *, limit: int = 2
) -> list[dict[str, Any]]:
    statements = []
    seen = set()
    for name in domain_names:
        conclusion = analysis["domains"][name].get("conclusion", {})
        for text in conclusion.get("interpretation", []):
            if text in seen:
                continue
            seen.add(text)
            statements.append({
                "text": text,
                "rule_ids": conclusion.get("rule_ids", []),
                "confidence": conclusion.get("confidence", 0.0),
                "source": f"domains.{name}.conclusion",
            })
            if len(statements) >= limit:
                return statements
    return statements


def _signal_statements(analysis: dict[str, Any], *, polarity: int) -> list[dict[str, Any]]:
    return [
        {
            "text": item["interpretation"],
            "rule_ids": [item["rule_id"]],
            "confidence": item["propagated_confidence"],
            "source": "single_feature_signals",
        }
        for item in analysis.get("single_feature_signals", [])
        if item["polarity"] == polarity
    ][:3]

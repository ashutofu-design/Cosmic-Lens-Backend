from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EngineResult:
    """Deterministic engine output for MR non-timing questions."""

    archetype: str
    verdict: str
    confidence: str = "medium"  # low | medium | high
    summary: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    ignore: list[str] = field(default_factory=list)
    answer_plan: str = ""
    word_budget: int = 55
    skip_llm: bool = False
    template_text: str = ""
    checks: dict[str, Any] = field(default_factory=dict)

    def to_narrator_payload(self) -> str:
        """Compact facts block for LLM narrator (minimal tokens)."""
        lines = [
            f"ARCHETYPE: {self.archetype}",
            "TONE: confident pattern voice (hai/hote hain/rehta hai). NO shayad/ho sakta hai/lagta hai.",
            f"VERDICT: {self.verdict}",
            f"CONFIDENCE: {self.confidence}",
        ]
        checks = self.checks or {}
        if checks.get("love_score") is not None:
            lines.append(
                f"SCORES: love={checks.get('love_score')} arrange={checks.get('arrange_score')}"
            )
        if self.evidence:
            lines.append("EVIDENCE (use 2–4 only, plain language):")
            lines.extend(f"- {e}" for e in self.evidence[:6])
        return "\n".join(lines)

    def to_chart_text(self, *, question: str) -> str:
        """Full admin/debug block (includes question + narrator rules)."""
        lines: list[str] = []
        lines.append("=== MR STATIC ENGINE (non-timing) — facts for narrator only ===")
        lines.append(f"QUESTION: {question.strip()[:220]}")
        lines.append(self.to_narrator_payload())
        lines.append(f"WORD_BUDGET: {int(self.word_budget)}")
        if self.answer_plan:
            lines.append(f"ANSWER_PLAN: {self.answer_plan}")
        if self.summary:
            lines.append("SUMMARY:")
            lines.extend(f"- {s}" for s in self.summary[:4])
        if self.ignore:
            lines.append("IGNORE:")
            lines.extend(f"- {x}" for x in self.ignore[:8])
        return "\n".join(lines)


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

    def to_chart_text(self, *, question: str) -> str:
        lines: list[str] = []
        lines.append("=== MR STATIC ENGINE (non-timing) — facts for narrator only ===")
        lines.append(f"ARCHETYPE: {self.archetype}")
        lines.append(f"QUESTION: {question.strip()[:220]}")
        lines.append(f"VERDICT: {self.verdict}")
        lines.append(f"CONFIDENCE: {self.confidence}")
        lines.append(f"WORD_BUDGET: {int(self.word_budget)}")
        if self.answer_plan:
            lines.append(f"ANSWER_PLAN: {self.answer_plan}")
        if self.summary:
            lines.append("")
            lines.append("SUMMARY (use 1–2 points only):")
            lines.extend(f"- {s}" for s in self.summary[:6])
        if self.evidence:
            lines.append("")
            lines.append("EVIDENCE (use 2–4 lines only; do not invent new reasons):")
            lines.extend(f"- {e}" for e in self.evidence[:10])
        if self.ignore:
            lines.append("")
            lines.append("IGNORE (unless user asked explicitly):")
            lines.extend(f"- {x}" for x in self.ignore[:12])
        lines.append("")
        lines.append("NARRATOR RULES (STRICT):")
        lines.append("- You are NOT calculating chart placements. Use only the facts above.")
        lines.append("- Reply in plain Hinglish. No house numbers, no planet names, no D9 words.")
        lines.append("- Use soft language: ho sakta hai / lagta hai / shayad. Never 100% claims.")
        lines.append("- Keep it human: no bullets/labels in final user reply.")
        return "\n".join(lines)


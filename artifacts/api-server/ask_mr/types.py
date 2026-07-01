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

    def _narrator_tone_block(self) -> str:
        conf = (self.confidence or "medium").strip().lower()
        verdict_l = (self.verdict or "").lower()
        mixed = any(
            w in verdict_l
            for w in ("mixed", "kamzor", "patience", "dheere", "early", "abhi ", "needs ")
        )
        if conf == "high" and not mixed:
            return (
                "TONE: confident pattern voice (hai/hote hain/rehta hai). "
                "NO shayad/ho sakta hai/lagta hai."
            )
        if conf == "low" or mixed:
            return (
                "TONE: balanced — mirror VERDICT strength exactly. "
                "Do NOT upgrade to strong/pakka/guaranteed/acha balance/poori tarah. "
                "If VERDICT says mixed/patience/early/kamzor → open with qualified haan "
                "(e.g. 'Haan, yog dikhte hain lekin abhi mixed/gradual phase hai'). "
                "NO shayad/ho sakta hai/lagta hai."
            )
        return (
            "TONE: measured — VERDICT is the ceiling. "
            "Do NOT oversell: banned words = strong, acha balance, pakka, guarantee, "
            "poori tarah, confirmed awakening. "
            "State VERDICT in plain Hinglish first, then one reason. "
            "NO shayad/ho sakta hai/lagta hai."
        )

    def to_narrator_payload(self) -> str:
        """Compact facts block for LLM narrator (minimal tokens)."""
        lines = [
            f"ARCHETYPE: {self.archetype}",
            self._narrator_tone_block(),
            f"VERDICT: {self.verdict}",
            f"CONFIDENCE: {self.confidence}",
            (
                "NARRATOR_LOCK: Sentence 1 = VERDICT tone (not stronger). "
                "CONFIDENCE=medium/low → never sound more bullish than VERDICT."
            ),
        ]
        checks = self.checks or {}
        if checks.get("love_score") is not None:
            lines.append(
                f"SCORES: love={checks.get('love_score')} arrange={checks.get('arrange_score')}"
            )
        if checks.get("love_pct") is not None:
            lines.append(
                f"PERCENT: love~{checks.get('love_pct')}% arrange~{checks.get('arrange_pct')}%"
            )
        if self.evidence:
            if checks.get("open_chart_qa"):
                # Open question, no fixed engine — give the LLM the full D1 picture
                # and let it pick the factors relevant to the exact question.
                lines.append(
                    "D1 RELATIONSHIP CHART (use ONLY the factors relevant to the question; "
                    "ignore the rest, plain language):"
                )
                lines.extend(f"- {e}" for e in self.evidence[:12])
            else:
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


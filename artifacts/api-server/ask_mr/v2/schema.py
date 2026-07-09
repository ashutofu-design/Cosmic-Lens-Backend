"""Shared JSON schema — EngineOutputV2 (Architecture Freeze v1)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class FactorRef:
    module: str
    rule_id: str
    label: str
    weight: float = 0.0
    polarity: str = "neutral"  # positive | negative | neutral


@dataclass
class ExplanationLayer:
    why: list[str] = field(default_factory=list)
    why_not: list[str] = field(default_factory=list)
    strongest_factor: FactorRef | None = None
    weakest_factor: FactorRef | None = None


@dataclass
class ContradictionReport:
    detected: bool = False
    pattern: str = ""  # e.g. strong_promise_temporary_stress
    summary: str = ""
    module_polarity: dict[str, str] = field(default_factory=dict)


@dataclass
class EngineMemorySnapshot:
    previously_fired_rules: list[str] = field(default_factory=list)
    previous_confidence: str = ""
    previous_evidence: list[str] = field(default_factory=list)
    previous_scorecard: dict[str, int] = field(default_factory=dict)


@dataclass
class TimingBlock:
    applicable: bool = False
    windows: list[dict[str, Any]] = field(default_factory=list)
    trigger_planets: list[str] = field(default_factory=list)


@dataclass
class VerdictBlock:
    level: str = ""
    headline: str = ""
    confidence: str = "medium"


@dataclass
class EngineOutputV2:
    engine_id: str
    engine_version: str = "v2"
    question_intent: str = ""
    mode: str = "static"  # static | timing | couple
    modules_used: list[str] = field(default_factory=list)
    verdict: VerdictBlock = field(default_factory=VerdictBlock)
    scorecard: dict[str, int] = field(default_factory=dict)
    evidence: dict[str, list[str]] = field(default_factory=lambda: {
        "positive": [],
        "negative": [],
        "neutral": [],
    })
    rules_fired: list[dict[str, Any]] = field(default_factory=list)
    contradiction: ContradictionReport = field(default_factory=ContradictionReport)
    explanation: ExplanationLayer = field(default_factory=ExplanationLayer)
    memory: EngineMemorySnapshot = field(default_factory=EngineMemorySnapshot)
    timing: TimingBlock = field(default_factory=TimingBlock)
    checks: dict[str, Any] = field(default_factory=dict)
    narrator_plan: str = ""
    ignore: list[str] = field(default_factory=list)
    orchestrator: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json_ready(self) -> dict[str, Any]:
        """JSON-serializable dict for API / admin debug."""
        d = self.to_dict()
        if self.explanation.strongest_factor:
            d["explanation"]["strongest_factor"] = asdict(self.explanation.strongest_factor)
        if self.explanation.weakest_factor:
            d["explanation"]["weakest_factor"] = asdict(self.explanation.weakest_factor)
        return d

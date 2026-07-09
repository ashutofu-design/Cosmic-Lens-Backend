"""Rule types for v2 engines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class EngineRule:
    rule_id: str
    module: str
    priority: int  # lower = higher priority
    polarity: str  # positive | negative | neutral
    weight: float
    label: str
    condition: Callable[[Any, dict], bool]
    evidence: Callable[[Any, dict], str] | None = None


@dataclass
class FiredRule:
    rule_id: str
    module: str
    priority: int
    polarity: str
    weight: float
    label: str
    evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "module": self.module,
            "priority": self.priority,
            "polarity": self.polarity,
            "weight": self.weight,
            "note": self.evidence or self.label,
        }

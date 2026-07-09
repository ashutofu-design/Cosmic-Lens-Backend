"""Chart module bundle types."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChartModuleResult:
    module_id: str
    loaded: bool = True
    polarity: str = "neutral"  # positive | negative | mixed | neutral
    score: int = 50  # 0-100 module-level sub-score
    factors: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    error: str = ""


@dataclass
class ModuleBundle:
    engine_id: str
    modules_requested: list[str] = field(default_factory=list)
    modules: dict[str, ChartModuleResult] = field(default_factory=dict)

    def get(self, module_id: str) -> ChartModuleResult | None:
        return self.modules.get(module_id)

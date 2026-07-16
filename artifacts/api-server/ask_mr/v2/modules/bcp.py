"""BCP marriage linkage module."""
from __future__ import annotations

from .types import ChartModuleResult


def load_bcp(kundli: dict, *, engine_id: str) -> ChartModuleResult:
    # MR v2 covers general relationship themes. Marriage timing has its own
    # dedicated BCP pipeline; loading marriage BCP here leaks it into loyalty,
    # breakup, commitment, and other non-marriage questions.
    return ChartModuleResult(
        module_id="bcp",
        loaded=False,
        polarity="neutral",
        score=50,
        notes=["BCP restricted to dedicated marriage/baby timing engines"],
    )

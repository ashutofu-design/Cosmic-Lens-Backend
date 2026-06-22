"""Universal event-timing pipeline — same step order for every domain.

Architecture (user mandate):
  UNDERSTAND → FILTER → VERIFY → KP → RANK → DASHA → TRANSIT → WINDOW → GUARD

Each domain engine implements these stages with domain-specific houses/lords.
Double-transit (Jupiter+Saturn on concern axis) is COMPULSORY for fructification
checks — see event_timing._shared.double_transit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class PipelineStage(str, Enum):
    UNDERSTAND = "understand"       # user demand + bucket + tense + age context
    FILTER = "filter"               # D1 significators / topic houses
    VERIFY = "verify"               # D9/D10/D4/D7 divisional confirmation
    KP = "kp"                       # cusp sub-lord + significator chain
    RANK = "rank"                   # weighted score + top planets/lords
    DASHA = "dasha"                 # MD/AD/PD activation scan
    TRANSIT = "transit"             # Jupiter/Saturn/Rahu + double-transit
    WINDOW = "window"               # merge dasha ∩ transit → date range
    GUARD = "guard"                 # brand-safety + age + no-guarantee rules


STANDARD_PIPELINE: tuple[PipelineStage, ...] = (
    PipelineStage.UNDERSTAND,
    PipelineStage.FILTER,
    PipelineStage.VERIFY,
    PipelineStage.KP,
    PipelineStage.RANK,
    PipelineStage.DASHA,
    PipelineStage.TRANSIT,
    PipelineStage.WINDOW,
    PipelineStage.GUARD,
)


@dataclass
class TimingDemand:
    """What the user actually wants — engine must answer THIS, not generic chart."""
    domain: str
    bucket: str
    is_timing: bool
    tense: str = "future"           # future | present | general
    user_age: Optional[int] = None
    emotional_tone: str = "neutral"
    wants_explain: bool = False
    question_focus: str = ""        # one-line interpretation
    defer_to: Optional[str] = None  # another domain if mis-route


@dataclass
class PipelineContext:
    question: str
    demand: TimingDemand
    kundli: dict
    intel: dict = field(default_factory=dict)
    kp: dict = field(default_factory=dict)
    birth: Any = None
    stages_done: list[str] = field(default_factory=list)
    factors: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    windows: list[dict] = field(default_factory=list)
    verdict: str = ""
    confidence: int = 0
    engine_id: str = ""
    engine_status: str = "pending"  # ready | partial | stub | deferred
    raw: dict = field(default_factory=dict)


def stage_label(stage: PipelineStage) -> str:
    labels = {
        PipelineStage.UNDERSTAND: "STEP0 — User demand + age/context",
        PipelineStage.FILTER: "STEP1 — D1 significator filter",
        PipelineStage.VERIFY: "STEP2 — Divisional verify (D9/D10/D4/…)",
        PipelineStage.KP: "STEP3 — KP cusp + significator",
        PipelineStage.RANK: "STEP4 — Weighted ranking",
        PipelineStage.DASHA: "STEP5 — Dasha activation (MD/AD/PD)",
        PipelineStage.TRANSIT: "STEP6 — Transit + double-transit (J+S)",
        PipelineStage.WINDOW: "STEP7 — Window merge (dasha ∩ transit)",
        PipelineStage.GUARD: "STEP8 — Brand-safety + no-guarantee",
    }
    return labels.get(stage, stage.value)

"""Frozen engine template — only rules, matrix, and output labels differ per engine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .rules.types import EngineRule
from .schema import EngineOutputV2
from .versioning import DEFAULT_ENGINE_VERSION, SCHEMA_VERSION, default_rules_version

RulesFactory = Callable[[], list[EngineRule]]
ContextBuilder = Callable[[str, dict, Any], dict[str, Any]]
IntentResolver = Callable[[str], str]
LevelResolver = Callable[[int, bool, str, dict[str, Any]], str]
HeadlineResolver = Callable[[str, str, dict[str, Any]], str]
ConfidenceResolver = Callable[[int, bool], str]
ChecksBuilder = Callable[[str, int, str, Any, dict[str, Any]], dict[str, Any]]
PostProcessor = Callable[[EngineOutputV2, dict, Any], EngineOutputV2]


@dataclass(frozen=True)
class EngineSpec:
    """Reference-engine template: shared pipeline, per-engine astrology + labels."""

    engine_id: str
    rule_prefix: str
    base_score: int
    levels: tuple[tuple[int, str], ...]
    headlines: dict[str, str]
    engine_version: str = DEFAULT_ENGINE_VERSION
    rules_version: str = ""
    schema_version: str = SCHEMA_VERSION
    rules_factory: RulesFactory | None = None
    positive_signal_keys: tuple[str, ...] = ()
    negative_signal_keys: tuple[str, ...] = ()
    resolve_intent: IntentResolver | None = None
    build_context: ContextBuilder | None = None
    resolve_level: LevelResolver | None = None
    resolve_headline: HeadlineResolver | None = None
    resolve_confidence: ConfidenceResolver | None = None
    build_checks: ChecksBuilder | None = None
    post_process: PostProcessor | None = None
    narrator_plan: str = "2–3 sentences: verdict → strongest factor → practical next step"
    ignore: tuple[str, ...] = (
        "timing dates unless asked",
        "spouse profession",
        "manglik unless asked",
    )
    apply_contradiction_penalty: bool = True
    contradiction_penalty: int = 8
    contradiction_floor: int = 48

    def __post_init__(self) -> None:
        if not self.rules_version:
            object.__setattr__(
                self,
                "rules_version",
                default_rules_version(self.rule_prefix),
            )

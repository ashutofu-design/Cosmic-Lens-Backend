"""Independent domain-engine registry for Face Reading Phase 2."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .conflicts import resolve_domain
from .rules import DOMAINS


@dataclass(frozen=True)
class DomainEngine:
    domain: str
    categories: tuple[str, ...]

    def analyze(
        self,
        signals: list[dict[str, Any]],
        strong_threshold: float,
        supported_categories: set[str] | None = None,
    ) -> dict[str, Any]:
        domain_signals = [
            item for item in signals if item["domain"] == self.domain
        ]
        resolved = resolve_domain(
            domain_signals, strong_threshold,
            require_multiple_families=True,
        )
        resolved["status"] = (
            "supported" if domain_signals else "insufficient_data"
        )
        resolved["categories"] = {}
        for category in self.categories:
            category_signals = [
                item for item in domain_signals
                if item["category"] == category
            ]
            category_result = resolve_domain(
                category_signals, strong_threshold
            )
            category_result["status"] = (
                "supported" if category_signals
                else (
                    "insufficient_data"
                    if supported_categories is None
                    or category in supported_categories
                    else "not_supported_by_ruleset"
                )
            )
            category_result["supported_by_selected_system"] = (
                supported_categories is None
                or category in supported_categories
            )
            resolved["categories"][category] = category_result
        return resolved


DOMAIN_ENGINES = {
    name: DomainEngine(name, categories)
    for name, categories in DOMAINS.items()
}


def analyze_domains(
    signals: list[dict[str, Any]],
    strong_threshold: float,
    supported_categories: dict[str, set[str]] | None = None,
) -> dict[str, dict[str, Any]]:
    return {
        name: engine.analyze(
            signals, strong_threshold,
            (supported_categories or {}).get(name)
            if supported_categories is not None else None,
        )
        for name, engine in DOMAIN_ENGINES.items()
    }

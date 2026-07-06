"""Domain targets for Universal Timing Formula (Steps 1–5) — marriage excluded."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from event_timing.domain_specs import get_domain_spec

# Minimum age before timing answer is considered practical (Step 0).
MIN_PRACTICAL_AGE: dict[str, int] = {
    "children": 20,
    "career": 18,
    "education": 14,
    "foreign_education": 16,
    "travel": 18,
    "property": 21,
    "vehicle": 18,
    "finance": 18,
    "health": 12,
    "love": 18,
    "litigation": 18,
    "spiritual": 16,
    "fame": 16,
    "network": 14,
    "universal": 16,
}

# D-chart used per domain for Step 1 (divisional house/lord verify).
DOMAIN_DIVISIONAL: dict[str, str] = {
    "career": "D10",
    "love": "D9",
    "travel": "D9",
    "property": "D4",
    "vehicle": "D4",
    "finance": "D2",
    "health": "D30",
    "children": "D7",
    "education": "D24",
    "foreign_education": "D9",
    "litigation": "D6",
    "spiritual": "D9",
    "fame": "D10",
    "network": "D11",
    "universal": "D9",
}


@dataclass
class UniversalFormulaConfig:
    domain: str
    bucket: str
    label: str
    target_houses: list[int]
    natural_karakas: list[str]
    divisional: str
    min_practical_age: int
    brand_safety: list[str] = field(default_factory=list)


def build_universal_formula_config(domain: str, bucket: str = "general") -> UniversalFormulaConfig:
    spec = get_domain_spec(domain)
    houses = [int(h) for h in (spec.get("houses") or [1]) if isinstance(h, (int, float))]
    karakas = [str(k) for k in (spec.get("karakas") or []) if k]
    return UniversalFormulaConfig(
        domain=domain,
        bucket=bucket or "general",
        label=str(spec.get("label") or domain),
        target_houses=houses or [1],
        natural_karakas=karakas,
        divisional=DOMAIN_DIVISIONAL.get(domain, "D9"),
        min_practical_age=int(MIN_PRACTICAL_AGE.get(domain, 16)),
        brand_safety=list(spec.get("guards") or spec.get("brand_safety_warnings") or [])[:6],
    )


UNIVERSAL_FORMULA_DOMAINS: frozenset[str] = frozenset({
    "career", "love", "travel", "property", "vehicle", "finance", "health",
    "children", "education", "foreign_education", "litigation", "spiritual",
    "fame", "network", "universal",
})

UNIVERSAL_FORMULA_STEP_ORDER: tuple[str, ...] = (
    "step0", "step1", "step2", "step3", "step4", "step5",
)

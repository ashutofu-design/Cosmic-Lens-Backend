"""Commitment engine rules — reference rule set for v2."""
from __future__ import annotations

from typing import Any

from ..modules.types import ModuleBundle
from ..rules.types import EngineRule


def _mod_score(bundle: ModuleBundle, mod: str, threshold: int, op: str) -> bool:
    m = bundle.modules.get(mod)
    if not m or not m.loaded:
        return False
    if op == "gte":
        return m.score >= threshold
    if op == "lte":
        return m.score <= threshold
    return False


def _has_factor(bundle: ModuleBundle, mod: str, polarity: str) -> bool:
    m = bundle.modules.get(mod)
    if not m:
        return False
    return m.polarity == polarity


def commitment_rules() -> list[EngineRule]:
    return [
        EngineRule(
            rule_id="COM-D1-READY",
            module="d1",
            priority=10,
            polarity="positive",
            weight=2.5,
            label="D1 commitment axis supportive",
            condition=lambda b, c: _mod_score(b, "d1", 68, "gte"),
            evidence=lambda b, c: "D1 partnership axis supports long-term intent",
        ),
        EngineRule(
            rule_id="COM-D1-FRICTION",
            module="d1",
            priority=10,
            polarity="negative",
            weight=2.5,
            label="D1 friction on commitment",
            condition=lambda b, c: _mod_score(b, "d1", 45, "lte"),
            evidence=lambda b, c: "D1 friction slows commitment readiness",
        ),
        EngineRule(
            rule_id="COM-D9-STRONG",
            module="d9",
            priority=20,
            polarity="positive",
            weight=2.0,
            label="D9 marriage promise strong",
            condition=lambda b, c: _mod_score(b, "d9", 70, "gte"),
            evidence=lambda b, c: "D9 Navamsa supports marriage/commitment promise",
        ),
        EngineRule(
            rule_id="COM-D9-WEAK",
            module="d9",
            priority=20,
            polarity="negative",
            weight=2.0,
            label="D9 marriage promise weak",
            condition=lambda b, c: _mod_score(b, "d9", 48, "lte"),
            evidence=lambda b, c: "D9 weakness needs patience before full commitment",
        ),
        EngineRule(
            rule_id="COM-DSH-BENEFIC",
            module="dasha",
            priority=40,
            polarity="positive",
            weight=1.5,
            label="Benefic dasha supports commitment",
            condition=lambda b, c: _has_factor(b, "dasha", "positive"),
            evidence=lambda b, c: "Current dasha supports seriousness and follow-through",
        ),
        EngineRule(
            rule_id="COM-TR-STRESS",
            module="transit",
            priority=50,
            polarity="negative",
            weight=1.5,
            label="Transit stress on bond",
            condition=lambda b, c: _has_factor(b, "transit", "negative"),
            evidence=lambda b, c: "Transit phase adds temporary commitment stress",
        ),
        EngineRule(
            rule_id="COM-KP-SUPPORT",
            module="kp",
            priority=60,
            polarity="positive",
            weight=1.2,
            label="KP 7th cusp supportive",
            condition=lambda b, c: _has_factor(b, "kp", "positive"),
            evidence=lambda b, c: "KP 7th cusp sub-lord links to commitment gain",
        ),
        EngineRule(
            rule_id="COM-TPR-RISK",
            module="d1",
            priority=5,
            polarity="negative",
            weight=3.0,
            label="Third-person risk blocks commitment clarity",
            condition=lambda b, c: bool(c.get("third_person_risk")),
            evidence=lambda b, c: "Third-person / parallel attention risk — clarify intent first",
        ),
    ]

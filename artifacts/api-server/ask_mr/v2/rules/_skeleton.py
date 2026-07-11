"""D1/D9/Transit rule skeleton — used until per-engine deep rules land."""
from __future__ import annotations

from typing import Any

from .types import EngineRule


def _has_sig(ctx: dict[str, Any], attr: str) -> bool:
    sig = ctx.get("sig")
    return bool(getattr(sig, attr, False))


def _note_contains(ctx: dict[str, Any], key: str) -> bool:
    sig = ctx.get("sig")
    return any(key.lower() in str(n).lower() for n in (getattr(sig, "notes", []) or []))


def build_skeleton_rules(
    *,
    rule_prefix: str,
    positive_signal_keys: tuple[str, ...] = (),
    negative_signal_keys: tuple[str, ...] = (),
) -> list[EngineRule]:
    prefix = rule_prefix.strip().upper()
    rules: list[EngineRule] = [
        EngineRule(
            rule_id=f"{prefix}-001",
            module="d1",
            priority=10,
            polarity="positive",
            weight=2.0,
            label="D1 promise/support is strong",
            condition=lambda b, c: bool(b.get("d1") and b.get("d1").score >= 68),
            evidence=lambda b, c: "D1 relationship axis gives support",
        ),
        EngineRule(
            rule_id=f"{prefix}-002",
            module="d1",
            priority=10,
            polarity="negative",
            weight=2.0,
            label="D1 relationship friction is active",
            condition=lambda b, c: bool(b.get("d1") and b.get("d1").score <= 45),
            evidence=lambda b, c: "D1 relationship axis shows friction",
        ),
        EngineRule(
            rule_id=f"{prefix}-003",
            module="d9",
            priority=20,
            polarity="positive",
            weight=1.8,
            label="D9 supports relationship sustainment",
            condition=lambda b, c: bool(b.get("d9") and b.get("d9").score >= 70),
            evidence=lambda b, c: "D9/Navamsa supports the relationship promise",
        ),
        EngineRule(
            rule_id=f"{prefix}-004",
            module="d9",
            priority=20,
            polarity="negative",
            weight=1.8,
            label="D9 needs caution",
            condition=lambda b, c: bool(b.get("d9") and b.get("d9").score <= 48),
            evidence=lambda b, c: "D9/Navamsa shows sustainment weakness",
        ),
        EngineRule(
            rule_id=f"{prefix}-005",
            module="transit",
            priority=50,
            polarity="negative",
            weight=1.2,
            label="Transit stress is active",
            condition=lambda b, c: bool(b.get("transit") and b.get("transit").polarity == "negative"),
            evidence=lambda b, c: "Current transit adds temporary relationship stress",
        ),
    ]
    idx = 6
    for key in positive_signal_keys:
        rule_key = str(key)
        rules.append(EngineRule(
            rule_id=f"{prefix}-{idx:03d}",
            module="d1",
            priority=12,
            polarity="positive",
            weight=2.0,
            label=rule_key.replace("_", " "),
            condition=lambda b, c, k=rule_key: _has_sig(c, k) or _note_contains(c, k),
            evidence=lambda b, c, k=rule_key: f"Support factor: {k.replace('_', ' ')}",
        ))
        idx += 1
    for key in negative_signal_keys:
        rule_key = str(key)
        rules.append(EngineRule(
            rule_id=f"{prefix}-{idx:03d}",
            module="d1",
            priority=8 if rule_key in ("third_person_risk", "separation_yoga") else 12,
            polarity="negative",
            weight=2.4,
            label=rule_key.replace("_", " "),
            condition=lambda b, c, k=rule_key: _has_sig(c, k) or _note_contains(c, k),
            evidence=lambda b, c, k=rule_key: f"Friction factor: {k.replace('_', ' ')}",
        ))
        idx += 1
    return rules

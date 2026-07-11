"""Engine capability manifests and health metadata.

Architecture Freeze v1 rule: routers should prefer this manifest over
hardcoded assumptions about engine mode/module support.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

from .module_registry import ENGINE_MODULE_MATRIX
from .registry import FROZEN_ENGINE_IDS

EngineMode = Literal["static", "timing", "couple"]


@dataclass(frozen=True)
class EngineHealth:
    coverage: str
    supported_questions: tuple[str, ...]
    unsupported_questions: tuple[str, ...]
    fallback_engine: str


@dataclass(frozen=True)
class EngineCapabilityManifest:
    engine_id: str
    version: str
    supports: tuple[EngineMode, ...]
    needs: tuple[str, ...]
    optional: tuple[str, ...] = ()
    never_uses: tuple[str, ...] = ()
    health: EngineHealth = field(default_factory=lambda: EngineHealth(
        coverage="unknown",
        supported_questions=(),
        unsupported_questions=(),
        fallback_engine="general_mr",
    ))

    def to_dict(self) -> dict:
        return asdict(self)


ENGINE_MANIFESTS: dict[str, EngineCapabilityManifest] = {
    "commitment": EngineCapabilityManifest(
        engine_id="commitment",
        version="2.0",
        supports=("static", "timing"),
        needs=("d1", "d9", "dasha", "transit", "kp", "ashtakavarga"),
        optional=("jaimini", "bcp"),
        never_uses=("d10",),
        health=EngineHealth(
            coverage="reference",
            supported_questions=(
                "commitment readiness",
                "serious vs casual intent",
                "time-pass / genuine intent",
                "long-term relationship intent",
                "static shaadi-intent questions",
            ),
            unsupported_questions=(
                "breakup / divorce risk",
                "third-person affair proof",
                "physical intimacy",
                "partner profession",
            ),
            fallback_engine="relationship_future",
        ),
    ),
    "loyalty_trust": EngineCapabilityManifest(
        engine_id="loyalty_trust",
        version="2.0",
        supports=("static", "timing"),
        needs=("d1", "d9", "dasha", "transit", "kp", "ashtakavarga"),
        optional=("jaimini", "bcp"),
        never_uses=("d10",),
        health=EngineHealth(
            coverage="template_v2",
            supported_questions=("loyalty", "trust", "cheating", "betrayal"),
            unsupported_questions=("commitment readiness", "family approval"),
            fallback_engine="commitment",
        ),
    ),
    "compatibility": EngineCapabilityManifest(
        engine_id="compatibility",
        version="2.0-planned",
        supports=("static", "timing", "couple"),
        needs=("d1", "d9", "ashtakavarga"),
        optional=("kp", "dasha", "transit", "bcp"),
        never_uses=("d10", "jaimini"),
        health=EngineHealth(
            coverage="planned_phase1",
            supported_questions=("gun milan", "overall match", "emotional/mental compatibility"),
            unsupported_questions=("breakup risk", "partner career"),
            fallback_engine="relationship_future",
        ),
    ),
    "breakup_risk": EngineCapabilityManifest(
        engine_id="breakup_risk",
        version="2.0-planned",
        supports=("static", "timing"),
        needs=("d1", "d9", "dasha", "transit", "kp", "ashtakavarga"),
        optional=("jaimini", "bcp"),
        never_uses=("d10",),
        health=EngineHealth(
            coverage="planned_phase1",
            supported_questions=("breakup risk", "separation", "divorce risk"),
            unsupported_questions=("patch-up possibility", "partner nature"),
            fallback_engine="relationship_decisions",
        ),
    ),
    "patchup": EngineCapabilityManifest(
        engine_id="patchup",
        version="2.0-planned",
        supports=("static", "timing"),
        needs=("d1", "d9", "dasha", "transit", "kp", "ashtakavarga"),
        optional=("jaimini", "bcp"),
        never_uses=("d10",),
        health=EngineHealth(
            coverage="planned_phase1",
            supported_questions=("patch-up", "ex return", "reconciliation", "second chance"),
            unsupported_questions=("new relationship promise", "spouse profession"),
            fallback_engine="relationship_future",
        ),
    ),
    "relationship_remedies": EngineCapabilityManifest(
        engine_id="relationship_remedies",
        version="2.0",
        supports=("static", "timing"),
        needs=("d1", "d9", "dasha", "ashtakavarga", "bcp"),
        optional=("transit", "jaimini"),
        never_uses=("d10", "expensive_gemstone_prescription"),
        health=EngineHealth(
            coverage="template_v2",
            supported_questions=("relationship upay", "love mantra", "patch-up remedy"),
            unsupported_questions=("guaranteed miracle", "expensive gemstone prescription without proof"),
            fallback_engine="relationship_future",
        ),
    ),
}


def _manifest_from_matrix(engine_id: str) -> EngineCapabilityManifest:
    row = ENGINE_MODULE_MATRIX.get(engine_id, {})
    needs = tuple(m for m, flag in row.items() if flag == "always")
    optional = tuple(m for m, flag in row.items() if flag in ("optional", "timing"))
    never = tuple(m for m, flag in row.items() if flag == "never")
    supports: tuple[EngineMode, ...] = ("static", "timing")
    if engine_id == "compatibility":
        supports = ("static", "timing", "couple")
    return EngineCapabilityManifest(
        engine_id=engine_id,
        version="2.0",
        supports=supports,
        needs=needs or ("d1",),
        optional=optional,
        never_uses=never + ("d10",),
        health=EngineHealth(
            coverage="template_v2",
            supported_questions=(f"{engine_id.replace('_', ' ')} questions",),
            unsupported_questions=("spouse profession", "guaranteed predictions"),
            fallback_engine="relationship_future",
        ),
    )


for _eid in FROZEN_ENGINE_IDS:
    if _eid not in ENGINE_MANIFESTS:
        ENGINE_MANIFESTS[_eid] = _manifest_from_matrix(_eid)

# Bump migrated Phase 1 engines to v2 coverage label
for _eid in ("compatibility", "breakup_risk", "patchup"):
    m = ENGINE_MANIFESTS.get(_eid)
    if m and m.health.coverage.startswith("planned"):
        ENGINE_MANIFESTS[_eid] = EngineCapabilityManifest(
            engine_id=m.engine_id,
            version="2.0",
            supports=m.supports,
            needs=m.needs,
            optional=m.optional,
            never_uses=m.never_uses,
            health=EngineHealth(
                coverage="template_v2",
                supported_questions=m.health.supported_questions,
                unsupported_questions=m.health.unsupported_questions,
                fallback_engine=m.health.fallback_engine,
            ),
        )


def get_engine_manifest(engine_id: str) -> EngineCapabilityManifest | None:
    return ENGINE_MANIFESTS.get((engine_id or "").strip().lower())


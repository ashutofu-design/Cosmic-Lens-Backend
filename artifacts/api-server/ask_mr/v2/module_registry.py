"""Central module matrix — single source for which chart modules each engine loads."""
from __future__ import annotations

import re
from typing import Literal

ModuleFlag = Literal["always", "never", "timing", "optional"]

CHART_MODULES = (
    "d1",
    "d9",
    "dasha",
    "transit",
    "kp",
    "ashtakavarga",
    "jaimini",
    "bcp",
)

# engine_id → module_id → load flag
ENGINE_MODULE_MATRIX: dict[str, dict[str, ModuleFlag]] = {
    "loyalty_trust": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "always",
        "kp": "always", "ashtakavarga": "always", "jaimini": "timing", "bcp": "timing",
    },
    "commitment": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "always",
        "kp": "always", "ashtakavarga": "always", "jaimini": "timing", "bcp": "timing",
    },
    "compatibility": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "optional", "ashtakavarga": "always", "jaimini": "never", "bcp": "timing",
    },
    "partner_nature": {
        "d1": "always", "d9": "always", "dasha": "never", "transit": "never",
        "kp": "never", "ashtakavarga": "never", "jaimini": "always", "bcp": "never",
    },
    "communication": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "never", "ashtakavarga": "always", "jaimini": "never", "bcp": "never",
    },
    "emotional_attachment": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "never", "ashtakavarga": "always", "jaimini": "timing", "bcp": "never",
    },
    "secret_relationship": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "always",
        "kp": "always", "ashtakavarga": "always", "jaimini": "timing", "bcp": "timing",
    },
    "breakup_risk": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "always",
        "kp": "always", "ashtakavarga": "always", "jaimini": "timing", "bcp": "timing",
    },
    "patchup": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "always",
        "kp": "always", "ashtakavarga": "always", "jaimini": "timing", "bcp": "timing",
    },
    "family_approval": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "never", "ashtakavarga": "never", "jaimini": "never", "bcp": "always",
    },
    "long_distance": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "always",
        "kp": "timing", "ashtakavarga": "never", "jaimini": "never", "bcp": "never",
    },
    "toxicity": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "never", "ashtakavarga": "always", "jaimini": "timing", "bcp": "never",
    },
    "one_sided_love": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "always", "ashtakavarga": "never", "jaimini": "never", "bcp": "never",
    },
    "chemistry": {
        "d1": "always", "d9": "always", "dasha": "never", "transit": "never",
        "kp": "never", "ashtakavarga": "never", "jaimini": "never", "bcp": "never",
    },
    "bed_intimacy": {
        "d1": "always", "d9": "always", "dasha": "never", "transit": "never",
        "kp": "never", "ashtakavarga": "never", "jaimini": "never", "bcp": "never",
    },
    "karmic_marriage": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "timing",
        "kp": "always", "ashtakavarga": "never", "jaimini": "always", "bcp": "timing",
    },
    "relationship_future": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "timing", "ashtakavarga": "always", "jaimini": "timing", "bcp": "never",
    },
    "relationship_decisions": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "always",
        "kp": "always", "ashtakavarga": "always", "jaimini": "timing", "bcp": "timing",
    },
    "relationship_verification": {
        "d1": "always", "d9": "always", "dasha": "timing", "transit": "timing",
        "kp": "always", "ashtakavarga": "always", "jaimini": "timing", "bcp": "timing",
    },
    "relationship_remedies": {
        "d1": "always", "d9": "always", "dasha": "always", "transit": "timing",
        "kp": "never", "ashtakavarga": "always", "jaimini": "timing", "bcp": "always",
    },
}

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|kis\s+(saal|year|mahine|month)|milega|milegi|"
    r"dasha|antardasha|mahadasha|transit|gochar|window|phase|samay|timing"
    r")\b"
)


def question_has_timing_trigger(question: str) -> bool:
    return bool(_TIMING_RX.search(question or ""))


def modules_for_engine(engine_id: str, question: str) -> list[str]:
    """Resolve which modules to load for this engine + question."""
    eid = (engine_id or "").strip().lower()
    row = ENGINE_MODULE_MATRIX.get(eid)
    if not row:
        return ["d1"]
    timing = question_has_timing_trigger(question)
    out: list[str] = []
    for mod in CHART_MODULES:
        flag = row.get(mod, "never")
        if flag == "always":
            out.append(mod)
        elif flag == "optional":
            out.append(mod)
        elif flag == "timing" and timing:
            out.append(mod)
    return out


def modules_for_engine_static(engine_id: str) -> list[str]:
    """Always-on modules for an engine (ignores timing triggers)."""
    row = ENGINE_MODULE_MATRIX.get((engine_id or "").strip().lower(), {})
    return [mod for mod in CHART_MODULES if row.get(mod) == "always"]

"""Engine memory — per session + engine_id."""
from __future__ import annotations

from typing import Any

from .schema import EngineMemorySnapshot, EngineOutputV2

_STORE: dict[str, EngineMemorySnapshot] = {}


def _key(session_id: str, engine_id: str) -> str:
    return f"{session_id.strip()}::{engine_id.strip().lower()}"


def load_memory(session_id: str, engine_id: str) -> EngineMemorySnapshot:
    if not session_id:
        return EngineMemorySnapshot()
    return _STORE.get(_key(session_id, engine_id), EngineMemorySnapshot())


def save_memory(session_id: str, output: EngineOutputV2) -> None:
    if not session_id:
        return
    snap = EngineMemorySnapshot(
        previously_fired_rules=[r.get("rule_id", "") for r in output.rules_fired if r.get("rule_id")],
        previous_confidence=output.verdict.confidence,
        previous_evidence=(
            output.evidence.get("positive", [])[:3]
            + output.evidence.get("negative", [])[:2]
        ),
        previous_scorecard=dict(output.scorecard),
    )
    _STORE[_key(session_id, output.engine_id)] = snap


def merge_with_memory(output: EngineOutputV2, memory: EngineMemorySnapshot) -> EngineOutputV2:
    """Attach prior snapshot; reuse rules if same theme re-asked."""
    output.memory = memory
    if not memory.previously_fired_rules:
        return output
    # Boost confidence slightly when same rules refire
    refire = sum(
        1 for r in output.rules_fired if r.get("rule_id") in memory.previously_fired_rules
    )
    if refire >= 2 and output.verdict.confidence == "medium":
        output.verdict.confidence = "high"
        output.checks["memory_refire_count"] = refire
    return output


def clear_memory_store() -> None:
    """Test helper."""
    _STORE.clear()

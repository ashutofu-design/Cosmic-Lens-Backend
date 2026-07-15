"""Ask: Marriage/Relationship non-timing engine.

Default (health-style): one unified ``relationship_engine_execution_v1`` pack
(D1 + D9). Archetypes are routing labels only.

Rollback:
  - ASK_MR_LEGACY_ARCHETYPE_ENGINES=1 → old per-archetype score engines
  - ASK_MR_ENGINE=0 → force legacy ask_marriage_relationship_slice upstream
  - If the engine raises, openai_helper auto-falls back to legacy slice
"""

from .engine import run_mr_static_engine
from .types import EngineResult

__all__ = ["EngineResult", "run_mr_static_engine"]


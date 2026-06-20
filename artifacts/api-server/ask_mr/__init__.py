"""Ask: Marriage/Relationship non-timing engine.

Engine computes deterministic signals + evidence lines.
LLM is used only as a narrator (language + warmth), not as a chart calculator.

Rollback / fallback:
  - Set ASK_MR_ENGINE=0 to force legacy ask_marriage_relationship_slice.
  - If the new engine raises, openai_helper auto-falls back to legacy slice.
  - Simple yes/no (manglik without explain) can skip LLM via template_text.
"""

from .engine import run_mr_static_engine
from .types import EngineResult

__all__ = ["EngineResult", "run_mr_static_engine"]


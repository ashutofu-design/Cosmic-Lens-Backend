"""Ask: Finance non-timing engine — deterministic evidence + LLM narrator."""

from .engine import run_finance_static_engine
from .types import EngineResult

__all__ = ["EngineResult", "run_finance_static_engine"]

"""Finance / Stock Market Y2 architecture.

Engine = deterministic facts (ZERO LLM inference)
Cache  = chart_norm + MD-AD key, TTL = next AD change
LLM    = only narrative polish (60-80 words), never invents facts

Public API:
  handle_finance_question(question, kundli, birth) -> dict | None
"""
from stock_engine.stock_replies import handle_finance_question  # noqa: F401

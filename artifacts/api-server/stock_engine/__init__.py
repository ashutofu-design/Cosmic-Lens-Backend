"""Stock Market Engine — Y2 architecture.

╔═══════════════════════════════════════════════════════════════╗
║  SCOPE: NON-TIMING engine                                     ║
║  ───────────────────────────────────────────────────────────  ║
║  This engine answers WHAT / WHY / WHICH questions about       ║
║  stocks, trading, investing and money behaviour, based on     ║
║  the user's natal chart + current dasha state.                ║
║                                                               ║
║  HANDLES (non-timing):                                        ║
║    • Verdict      — trading vs swing vs long-term, sector     ║
║    • Reasons      — why repeated loss, leak, blockage         ║
║    • Capacity     — risk, rich potential, full-time trader    ║
║    • Comparison   — business + market, intraday vs swing      ║
║                                                               ║
║  DOES NOT HANDLE (timing — separate engines):                 ║
║    • "Kab paisa aayega" / "When will I profit"                ║
║    • Specific date / muhurat / event prediction               ║
║    • Daily / weekly / monthly market forecast                 ║
║    • Transit-based event timing                               ║
║                                                               ║
║  → If user asks anything other than timing about money/       ║
║    stocks, this engine calculates the answer.                 ║
║  → Timing questions fall through to the timing pipeline.      ║
╚═══════════════════════════════════════════════════════════════╝

Architecture:
  Engine = deterministic facts (ZERO LLM inference)
  Cache  = chart_norm + MD-AD key, TTL = next AD change
  LLM    = only narrative polish (60-80 words), never invents facts

Public API:
  handle_finance_question(question, kundli, birth) -> dict | None

Engine scope tag (exposed in every response): "non_timing"
"""
SCOPE = "non_timing"

from stock_engine.stock_replies import handle_finance_question  # noqa: F401, E402

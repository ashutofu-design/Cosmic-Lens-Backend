"""Finance Engine — Y2 architecture (sister module to stock_engine).

╔═══════════════════════════════════════════════════════════════╗
║  SCOPE: NON-TIMING engine                                     ║
║  ───────────────────────────────────────────────────────────  ║
║  General money / wealth questions — NOT stock-market.         ║
║  Based on user's natal chart + current dasha state.           ║
║                                                               ║
║  HANDLES (non-timing):                                        ║
║    • Wealth potential       — amir banunga? rich-yog hai?     ║
║    • Income stability       — kaun sa source, salary/business ║
║    • Saving ability         — bachat hoti / nahi, kitni       ║
║    • Risk / leak            — paisa tikta nahi, kharcha jyada ║
║    • Loan & debt            — karz le sakta? clear kab?       ║
║    • Business profit        — partnership safe? profit aayega ║
║    • Sudden wealth          — lottery / inheritance / windfall║
║    • Dhana yoga audit       — kaun-kaun se rich-yog active    ║
║                                                               ║
║  DOES NOT HANDLE (timing — separate engines):                 ║
║    • "Kab paisa aayega" / muhurat / specific date             ║
║    • Daily/weekly/monthly money forecast                      ║
║    • Transit-based event timing                               ║
║                                                               ║
║  DOES NOT HANDLE (stock-specific — stock_engine handles):     ║
║    • Stock-market verdict, intraday/swing/long-term split     ║
║    • Specific sector pick, F&O, crypto, mutual funds          ║
║    • Trading strategy, full-time trader question              ║
║                                                               ║
║  → Stock engine fires FIRST in flask_app pipeline.            ║
║    Finance engine fires only if stock returned None AND       ║
║    is_finance_question matched a non-stock money keyword.     ║
╚═══════════════════════════════════════════════════════════════╝

Architecture (mirrors stock_engine):
  Engine = deterministic facts (ZERO LLM inference)
  Cache  = chart_norm + MD-AD key, TTL = next AD change
  LLM    = only narrative polish (60-80 words), never invents facts

Multi-dimensional verdict (per user spec):
  • wealth_potential   — long-arc richness capacity
  • income_stability   — month-on-month income reliability
  • saving_ability     — capacity to retain what is earned
  • risk_leak          — drain/blockage signal strength

Public API:
  handle_finance_money_question(question, kundli, birth) -> dict | None

Engine scope tag (exposed in every response): "non_timing"
"""
SCOPE = "non_timing"

from finance_engine.finance_replies import handle_finance_money_question  # noqa: F401, E402

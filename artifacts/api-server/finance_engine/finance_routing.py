"""Finance question router (general money — NOT stock-market).

Pure regex-based classifier. Maps user question to one of:
  - WARNING:<key>     -> return locked warning template (0 LLM)
  - DIRECT:<route>    -> format engine facts directly (0 LLM)
  - NARRATIVE:<route> -> engine facts + 60-80w LLM polish

NO LLM is used here. Pure rule-based dispatch.

EXCLUSION FIRST: this engine MUST NOT handle stock-market questions.
A hard guard rejects anything mentioning stock/share/trading/intraday/
swing/equity/sector/NSE/BSE/F&O/crypto/mutual-fund/SIP/portfolio etc.
Those go to stock_engine.
"""
from __future__ import annotations
import re
from typing import Tuple

# ── HARD EXCLUSION — stock terms always defer to stock_engine ───────
_STOCK_EXCLUDE_RX = re.compile(
    r"\b(stock|stocks?|share[\s-]*market|share-market|equity|"
    r"intraday|day[\s-]*trade|day[\s-]*trading|swing[\s-]*trade|"
    r"trading|trader|f\&o|nifty|sensex|"
    r"mutual[\s-]*fund|sip|nse|bse|portfolio|"
    r"crypto|bitcoin|ethereum|"
    r"sector\s+(pick|recommendation|invest|stock))\b",
    re.IGNORECASE
)

# ── HARD EXCLUSION — TIMING questions defer to timing engine ────────
# Per user directive: "non_timing_finance" — ANY money-related Q comes
# here UNLESS it's a timing Q (kab/when/which year/dasha period etc.).
# Timing engine owns those; we don't double-handle.
_TIMING_EXCLUDE_RX = re.compile(
    r"\b("
    r"kab|kab\s+tak|kab\s+(milega|hoga|hogi|aayega|aayegi)|"
    r"when|when\s+will|by\s+when|"
    r"kis\s+(saal|year|mahine|month|date|tarikh|samay|time)|"
    r"kaun[\s-]?se\s+(saal|year|mahine|month)|"
    r"\d{4}\s+me|"                  # "2026 me", "2027 me"
    r"(this|next|coming|aane[\s-]?wala)\s+(year|month|saal|mahina)|"
    r"is\s+(saal|mahine)|agle\s+(saal|mahine)|"
    r"dasha\s+(kab|me|change|period|timing|chal\s+rahi)|"
    r"antar(?:dasha)?\s+(kab|me|period|timing|chal\s+rahi)|"
    r"mahadasha\s+(kab|me|period|timing)|"
    r"transit\s+(kab|me|effect|period)|"
    r"gochar\s+(kab|me|effect)|"
    r"period\s+(of|kab|when)|"
    r"date\s+(bata|tell|of)|"
    r"timing\s+(bata|tell|kya)"
    r")\b",
    re.IGNORECASE
)


# ── WARNINGS — checked FIRST (highest priority) ─────────────────────
_WARN_PATTERNS = [
    # GUARANTEE_AMOUNT — exact rupee/amount predict
    (r"(kitne\s+(rupee|rupaye|lakh|crore|paise)\s+(milenge|aayenge|kamaunga)|"
     r"exactly\s+(kitna|how\s+much)\s+(paisa|paise|money|amount)|"
     r"exact\s+(amount|rupee|rupaye)\s+(milega|aayega))",
     "GUARANTEE_AMOUNT"),
    # LOTTERY_NUMBER — specific lottery/satta numbers
    (r"(lottery\s+(number|ticket|pick)|satta\s+(number|pick|matka)|"
     r"jackpot\s+number|lucky\s+number\s+(lottery|satta)|"
     r"kaun\s*sa\s+(lottery|number)\s+(lagau|leu))",
     "LOTTERY_NUMBER"),
    # DEBT_TRAP — using loan to pay loan
    (r"(loan\s+se\s+loan|emi\s+ke\s+liye\s+(loan|udhaar)|"
     r"credit\s*card\s+se\s+emi|naya\s+loan\s+(le\s+ke|le\s+kar)\s+(purana|emi)|"
     r"dusra\s+loan\s+le\s+ke\s+(emi|chukana))",
     "DEBT_TRAP"),
    # GET_RICH_QUICK — schemes / overnight wealth
    (r"(jaldi\s+ameer|jaldi\s+rich|raato\s*[-\s]?raat\s+(paisa|ameer)|"
     r"overnight\s+(rich|wealthy)|mlm|ponzi|"
     r"crorepati\s+(jaldi|kab\s+banunga\s+jaldi))",
     "GET_RICH_QUICK"),
    # FRIENDS_LOAN — verbal loans to/from friends
    (r"(dost\s+ko\s+(paisa|paise)\s+(de|dena|udhaar)|"
     r"family\s+se\s+(paisa|paise|udhaar)\s+(le|lena|liya)|"
     r"friend\s+(loan|udhaar)|"
     r"udhaar\s+(diya|liya)\s+(dost|family|friend))",
     "FRIENDS_LOAN"),
]

# ── DIRECT (pure engine, no LLM) ────────────────────────────────────
_DIRECT_PATTERNS = [
    # Multi-dim wealth verdict — primary route
    (r"(wealth\s+potential|amir\s+banunga|amir\s+ban\s+sakta|"
     r"rich\s+banunga|crorepati\s+banunga|"
     r"mera\s+(dhan|wealth|paisa)\s+(yog|status|kaisa)|"
     r"financial\s+(verdict|analysis|status|condition)|"
     r"meri\s+(financial|paisa|paise)\s+(condition|halat|status))",
     "wealth_verdict"),
    # Sudden wealth check (lottery yog HAA/NA — no number)
    (r"(sudden\s+wealth|achanak\s+paisa|windfall|"
     r"lottery\s+(yog|jeet|milega)|inheritance|virasat|"
     r"sasur(?:al)?\s+se\s+paisa|"
     r"unexpected\s+(money|paisa))",
     "sudden_wealth"),
    # Dhana yoga audit
    (r"(dhana?\s+yog[a]?|wealth\s+yoga|"
     r"(rich|amir)\s+yog\s+(hai|chart\s+me)|"
     r"lakshmi\s+yog|kubera\s+yog|gaja[\s-]?kesari|adhi\s+yog|"
     r"chart\s+me\s+(rich|amir|dhana?)\s+(yog|combination))",
     "dhana_yoga_check"),
]

# ── NARRATIVE (engine + LLM polish) ─────────────────────────────────
_NARRATIVE_PATTERNS = [
    # SAVING — saving capacity / why no saving
    (r"(saving\s+(nahi|nhi|kyun|kaisi|hoti|hogi)|"
     r"bachat\s+(nahi|kyun|hoti|hogi)|"
     r"kitn[ai]\s+(save|bachat)|"
     r"save\s+nahi\s+kar\s+pa|"
     r"savings\s+(zero|low|build))",
     "saving_capacity"),
    # EXPENSE pattern — kharcha
    (r"(kharcha\s+(jyada|control|kabu|nahi\s+ruk)|"
     r"expense\s+(control|too\s+much|out\s+of\s+control)|"
     r"paisa\s+kharch\s+ho\s+jata|"
     r"jeb\s+khali|fizul\s+kharch)",
     "expense_pattern"),
    # LOAN / DEBT advisory
    (r"(loan\s+(le\s+sak|milega|chukana|repay)|"
     r"karz\s+(clear|chukana|kaise|kab)|"
     r"emi\s+(bojh|chukana|kaise)|"
     r"debt\s+(clear|free|kaise))",
     "loan_debt"),
    # INCOME source / what work
    (r"(income\s+source|kaun\s*sa\s+(income|kaam|work)|"
     r"salary\s+(vs|ya)\s+business|"
     r"job\s+(vs|ya)\s+(business|kaarobaar)|"
     r"main\s+(salary|job)\s+karu\s+ya|"
     r"(business|kaam)\s+(achha|sahi)\s+rahega)",
     "income_source"),
    # BUSINESS profit
    (r"(business\s+(profit|fayda|chalega|aayega)|"
     r"partnership\s+(safe|sahi|achhi)|"
     r"apna\s+kaam\s+(start|shuru|chalega)|"
     r"startup\s+(idea|profit|chalega))",
     "business_profit"),
    # LOSS / leak generic finance
    (r"(paisa\s+nahi\s+tikta|paisa\s+ud\s+jata|"
     r"paisa\s+kharch\s+ho\s+jata|"
     r"wealth\s+leak|money\s+drain|paisa\s+(haath\s+se\s+nikal|udta))",
     "loss_reasons"),
]

# ── Finance topic detection (gate) — NON-stock money keywords ───────
# BROAD — per user directive: any money/wealth word qualifies.
_FINANCE_TOPIC_RX = re.compile(
    r"\b(paisa|paise|paiso|dhan|dhana|wealth|money|"
    r"saving|savings|bachat|"
    r"kharcha|kharch|expense|expenses|fizul|"
    r"loan|karz|kar(?:j|z)a|udhaar|debt|emi|"
    r"income|salary|kamai|earnings|earning|kamana|kamai|"
    r"business(?!\s*market)|kaarobaar|startup|partnership|"
    r"lottery|jackpot|inheritance|virasat|windfall|"
    r"rich|ameer|amir|crorepati|garib|gareeb|poor|"
    r"lakshmi|kubera|"
    r"financial|finance(?!\s*market)|"
    r"property|real[\s-]*estate|jameen|zameen|plot|"
    r"gold|sona|jewellery|jewelry|"
    r"mindset|abundance|prosperity|samriddhi"
    r")\b",
    re.IGNORECASE
)


def is_finance_question(question: str) -> bool:
    """True if the question is about general (NON-TIMING) money AND not stock.

    Three guards in order:
      1. Stock terms        -> stock_engine handles it (return False)
      2. Timing terms       -> timing engine handles it (return False)
      3. Finance keyword    -> we own it (return True)
    """
    if not isinstance(question, str) or not question.strip():
        return False
    if _STOCK_EXCLUDE_RX.search(question):
        return False  # stock_engine territory
    if _TIMING_EXCLUDE_RX.search(question):
        return False  # timing engine territory
    return bool(_FINANCE_TOPIC_RX.search(question))


def route_finance_question(question: str) -> Tuple[str, str]:
    """Returns (mode, route_id) where mode in
    {WARNING, DIRECT, NARRATIVE, HYBRID}.

    Catch-all fallback (per user directive "har finance Q yahan se"):
      ('HYBRID', 'general_finance_overview') — DIRECT 4-dim picture
      + short LLM narrative line. Used when no specific pattern fires.
    """
    q = (question or "").lower()

    for pat, key in _WARN_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return ("WARNING", key)

    for pat, route in _DIRECT_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return ("DIRECT", route)

    for pat, route in _NARRATIVE_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return ("NARRATIVE", route)

    # Catch-all — broad finance Q with no specific match.
    return ("HYBRID", "general_finance_overview")

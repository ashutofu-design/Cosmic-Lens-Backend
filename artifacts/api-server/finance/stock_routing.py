"""Phase 2.10.7 — Stock question router.

Pure regex-based classifier. Maps user question to one of:
  - WARNING:<key>     -> return locked warning template (0 LLM)
  - DIRECT:<route>    -> format engine facts directly (0 LLM)
  - NARRATIVE:<route> -> engine facts + 60-80w LLM polish

NO LLM is used here. Pure rule-based dispatch.
"""
from __future__ import annotations
import re
from typing import Tuple

# ── WARNINGS — checked FIRST (highest priority) ─────────────────────
_WARN_PATTERNS = [
    # QUICK_MONEY
    (r"(jaldi\s+paisa|jaldi\s+ameer|quick\s+money|quick\s+paisa|"
     r"jaldi\s+rich|fast\s+money|raato\s*[-\s]?raat)",
     "QUICK_MONEY"),
    # RISK
    (r"(risk\s+lena|barbaadi|barbad|risk\s+sahi|big\s+risk|"
     r"sab\s+paisa\s+laga|all\s*[-\s]?in)",
     "RISK"),
    # TIPS
    (r"(tip\s+pe|tips?\s+(le|follow|ke\s+hisaab)|whatsapp\s+(tip|group)|"
     r"telegram\s+(tip|channel|group)|free\s+advice|"
     r"kisi\s+ke\s+(kehne|advice|tip))",
     "TIPS"),
    # LEVERAGE
    (r"(loan\s+le\s*(ke|kar)|udhaar\s+le|leverage|margin\s+(trading|use)|"
     r"borrow.*invest|credit\s+card.*invest|"
     r"loan.*invest|invest.*loan)",
     "LEVERAGE"),
    # EMOTIONAL
    (r"(fear\s+se|greed\s+se|emotion\s+pe|panic\s+sell|panic\s+buy|"
     r"darr\s*(ke|me)\s+sell|lalach\s+me\s+(buy|kharid))",
     "EMOTIONAL"),
]

# ── DIRECT (pure engine, no LLM) ────────────────────────────────────
_DIRECT_PATTERNS = [
    # Q3: suitable hai ya nahi (overall verdict)
    (r"(stock.*suitable|market.*suitable|stock.*sahi\s+hai|"
     r"market.*sahi\s+hai|stock\s+market\s+(mere|mera)\s+(liye|liye\s+sahi))",
     "verdict_only"),
    # Q21: konsa grah success deta hai
    (r"(konsa\s+grah|kaunsa\s+grah|kaun\s*sa\s+grah|which\s+planet).*"
     r"(stock|market|trading|invest|success|fayda|paisa)",
     "top_dhana_karakas"),
    # Q23: 5H/8H/H5/H8 strong zaruri kya
    (r"(5(th|\s*ghar|\s*house)|h5|panchma|"
     r"8(th|\s*ghar|\s*house)|h8|ashtama).*(strong|zaruri|important)",
     "h5_h8_strength"),
    # Q24: speculative gains kundli me
    (r"(speculative\s+gains?|speculation.*kundli|kundli.*speculation|"
     r"satta.*kundli|kundli.*satta|jua.*kundli)",
     "speculation_yogas"),
    # Q25: dasha change pe financial
    (r"(dasha\s+(change|badle|badle).*financial|"
     r"financial.*dasha\s+(change|badle)|next\s+dasha.*(money|finance|paisa))",
     "next_dasha_money"),
]

# ── NARRATIVE (engine + LLM polish) ─────────────────────────────────
_NARRATIVE_PATTERNS = [
    # Q1: paisa tikta nahi
    (r"(paisa\s+(tikta|rukta|tikti|rukti|nikal\s+jata)|"
     r"paisa\s+nahi\s+tikta|paisa\s+ud\s+jata|wealth\s+leak|"
     r"savings\s+nahi\s+ho|save\s+nahi\s+kar|"
     r"tikta\s+(nahi|kyun)|rukta\s+(nahi|kyun))",
     "leak_facts"),
    # Q2: trading ya long-term
    (r"(trading.*ya.*(long\s*[-\s]?term|investment|invest|long\s+invest)|"
     r"(long\s*[-\s]?term|investment|long\s+invest).*ya.*trading|"
     r"trader.*ya.*investor|investor.*ya.*trader)",
     "trading_vs_longterm"),
    # Q5: risk le sakta
    (r"(risk\s+le\s+sakt|risk\s+capacity|safe\s+rehna\s+better|"
     r"high\s+risk\s+(achha|sahi))",
     "risk_capacity"),
    # Q11: bar bar loss
    (r"(bar\s*[-\s]?bar\s+loss|loss\s+(hi\s+)?(ho|hota)|repeated\s+loss|"
     r"har\s+(baar|trade).*loss|loss\s+kyun)",
     "loss_reasons"),
    # Q12: financial blockage
    (r"(financial\s+blockage|blockage|paisa\s+block|"
     r"money\s+blocked|wealth\s+block)",
     "blockage_check"),
    # Q13: intraday avoid
    (r"(intraday|day\s+trading|day\s*[-\s]?trade)",
     "intraday_check"),
    # Q14: paisa aata par rukta nahi (variant of Q1)
    (r"(aata\s+(hai\s+)?par.*rukta\s+nahi|aata.*tikta\s+nahi|"
     r"income\s+hai\s+par|kamai\s+(hai|hoti)\s+par)",
     "leak_facts"),
    # Q15: kis grah ke karan loss
    (r"(kis\s+grah|konsa\s+grah|kaunsa\s+grah).*(loss|nuksaan|haani)|"
     r"(rahu|mars|saturn|ketu).*(loss|karan|wajah)",
     "loss_planets"),
    # Q16: rich ban sakta
    (r"(rich\s+ban|ameer\s+ban|crorepati|rich\s+kab|wealth.*kund?li|"
     r"(stock|market).*rich)",
     "rich_potential"),
    # Q17: trading vs investing success
    (r"(trading.*ya.*investing|investing.*ya.*trading).*(success|kaun\s+zyada)|"
     r"(trading|investing).*(success.*kaun|kaun.*success)",
     "trading_vs_longterm"),
    # Q18: konsa sector
    (r"(konsa\s+sector|kaunsa\s+sector|which\s+sector|sector.*(better|sahi)|"
     r"\b(it|banking|crypto|pharma|fmcg|auto|metal)\b.*(stock|invest|sahi))",
     "sector_recommendation"),
    # Q19: business + market dono
    (r"(business.*(aur|\\+|and)\s+(market|stock|trading)|"
     r"(market|stock|trading).*(aur|\\+|and)\s+business|"
     r"business.*market.*dono)",
     "business_plus_market"),
    # Q20: full-time trader
    (r"(full[-\s]?time\s+(trader|trading)|trading.*career|"
     r"trader\s+banu|professional\s+trader|job\s+chhod.*trade)",
     "fulltime_trader"),
    # Q22: rahu strong trading
    (r"(rahu\s+strong.*(trading|fayda|profit)|"
     r"rahu.*trading.*(fayda|achha|profit))",
     "rahu_trading"),
]

# ── Stock topic detection (gate) ────────────────────────────────────
_STOCK_TOPIC_RX = re.compile(
    r"\b(stock|stocks?|share\s*market|share-market|equity|"
    r"trading|trader|trade\s+(karu|karna)|"
    r"invest(ment|ing|or)?|crypto|bitcoin|"
    r"nifty|sensex|f&o|mutual\s+fund|sip|"
    r"satta|speculation|speculative|"
    r"dhana|paisa\s+(kamana|banana|laga|tikta|rukta)|"
    r"sector|nse|bse|portfolio|intraday|day\s*trade|"
    r"finance|financial|loss|profit\s+(kab|kaise)|"
    r"financial\s+blockage|wealth\s+leak)\b",
    re.IGNORECASE
)


def is_stock_question(question: str) -> bool:
    if not isinstance(question, str) or not question.strip():
        return False
    return bool(_STOCK_TOPIC_RX.search(question))


def route_stock_question(question: str) -> Tuple[str, str]:
    """Returns (mode, route_id) where mode in {WARNING, DIRECT, NARRATIVE}.

    Falls back to NARRATIVE:verdict_summary for stock questions that
    don't match any specific pattern.
    """
    q = (question or "").lower()

    # 1. WARNINGS first (highest priority)
    for pat, key in _WARN_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return ("WARNING", key)

    # 2. DIRECT (pure engine)
    for pat, route in _DIRECT_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return ("DIRECT", route)

    # 3. NARRATIVE (engine + LLM)
    for pat, route in _NARRATIVE_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return ("NARRATIVE", route)

    # 4. Fallback: verdict summary (DIRECT, no LLM cost)
    return ("DIRECT", "verdict_only")

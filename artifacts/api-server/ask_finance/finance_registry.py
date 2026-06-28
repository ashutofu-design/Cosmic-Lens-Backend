"""Finance topic registry — scope keywords + archetype detection."""

from __future__ import annotations

import re

from finance_static.finance_routing import is_finance_question

FINANCE_ARCHETYPES = frozenset({
    "income_source",
    "savings_capacity",
    "save_vs_spend",
    "expense_pattern",
    "spending_personality",
    "financial_discipline",
    "investment_risk",
    "debt_loan",
    "property_money",
    "sudden_gain_loss",
    "business_profit",
    "loss_reasons",
    "wealth_potential",
    "dhana_yoga",
    "general_finance",
})

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|when\s+will|kis\s+(saal|year|mahine|month)|"
    r"\d{4}\s+me|dasha|antardasha|mahadasha|transit|gochar|muhurat|timing|"
    r"date\s+fix|exact\s+date"
    r")\b"
)

# Employee vs entrepreneur mindset → career (job_vs_business), not finance
_CAREER_MONEY_MINDSET_RX = re.compile(
    r"(?ix)\b("
    r"employee\s+mindset|entrepreneur\s+mindset|"
    r"employee\s+.*\b(ya|or)\b.*\b(entrepreneur|business)\b|"
    r"entrepreneur\s+.*\b(ya|or)\b.*\b(employee|job|naukri)\b"
    r")\b"
)

_JOB_VS_BIZ_FINANCE_EXCL_RX = re.compile(
    r"(?ix)\b("
    r"salary\s+karu\s+ya|job\s+karu\s+ya|naukri\s+ya\s+business|"
    r"salary\s+\w+\s+ya\s+business|job\s+\w+\s+ya\s+business|"
    r"job\s*vs\s*business|business\s*vs\s*job"
    r")\b"
)

_KITNA_PAISA_RX = re.compile(
    r"(?ix)\b("
    r"mere?\s+paas\s+.{0,25}(paisa|paise|money)|"
    r"paas\s+.{0,20}(kitna|kitne)\s+(paisa|paise)|"
    r"(paisa|paise|money)\s+kitna|"
    r"kitna\s+(paisa|paise|money|paiso)\s*(hoga|hogi|hai|rahega|rahegi)?|"
    r"kitne\s+paise"
    r")\b"
)

_SAVE_VS_SPEND_RX = re.compile(
    r"(?ix)\b("
    r"bachane\s+wala\s+.*\b(ya|or)\b.*\b(kharch|spend)|"
    r"kharch\s+.*\b(ya|or)\b.*\b(bach|save)|"
    r"bachat\s+.*\b(ya|or)\b.*\b(kharch|spend)|"
    r"save\s+.*\b(ya|or)\b.*\b(spend|spend)|"
    r"saver\s+.*\b(ya|or)\b.*\bspender|spender\s+.*\b(ya|or)\b.*\b(saver|bach)"
    r")\b"
)

_SPENDING_PERSONALITY_RX = re.compile(
    r"(?ix)\b("
    r"emotional\s+spend\w*|impulsive\s+spend\w*|impulsive\s+shop\w*|mood\s+spend\w*|"
    r"luxury[\s-]?oriented|luxury\s+lover|luxury\s+spend\w*|"
    r"brand\s+oriented|brand\s+pe\s+.{0,15}kharch|show[\s-]?off\s+spend\w*|shopping\s+addict|"
    r"comfort\s+spend\w*|status\s+spend\w*|shauk\s+se\s+kharch"
    r")\b"
)

_INVESTMENT_RISK_RX = re.compile(
    r"(?ix)\b("
    r"risk[\s-]?taking\s+investor|investor\s+.*\b(ya|or)\b.*\b(conservative|safe)|"
    r"conservative\s+.*\b(ya|or)\b.*\b(investor|risk)|"
    r"aggressive\s+invest\w*|safe\s+investor|high[\s-]?risk\s+invest|"
    r"risk\s+l(?:ena|ene)\s+wala\s+investor|conservative\s+investor|"
    r"investment\s+risk|investment\s+me\s+risk|invest\s+.*\b(ya|or)\b.*\b(conservative|safe)|"
    r"invest\s+me\s+risk|investment\s+me\s+risk"
    r")\b"
)

_DISCIPLINE_RX = re.compile(
    r"(?ix)\b("
    r"financial\s+discipline|money\s+discipline|paisa\s+discipline|"
    r"financially\s+disciplined|discipline\s+me\s+kaisa|"
    r"budget\s+discipline|saving\s+discipline|budget\s+ban\w*|"
    r"paisa\s+discipline\s+weak|discipline\s+strong"
    r")\b"
)

_INCOME_RX = re.compile(
    r"(?ix)\b("
    r"income|kamai|kama\s*sakta|kamaane|kama\s*ne\s*ka|salary|tankhwah|"
    r"earning|earn\s*money|paisa\s*kahan\s*se|income\s*source|"
    r"natural\s+tareek|natural\s+way|natural\s+style|"
    r"multiple\s*income|passive\s*income|freelanc\w*|commission|"
    r"side\s*income|extra\s*income|monthly\s*income|fixed\s*income|"
    r"business\s*se\s*income|job\s*se\s*income|paisa\s*kama"
    r")\b"
)

_SAVINGS_RX = re.compile(
    r"(?ix)\b("
    r"saving|savings|bachat|bach\s*pata|save\s*kar|kitni\s*bachat|"
    r"paisa\s*bach\w*|money\s*save|saving\s*capacity|retain|tik\s*pata|"
    r"paisa\s*tik\w*|paisa\s*rukt\w*|accumulate|jama\s*kar|"
    r"\bfd\b|fixed\s+deposit|health\s+ke\s+liye\s+(?:fd|bachat|saving)"
    r")\b"
)

_EXPENSE_RX = re.compile(
    r"(?ix)\b("
    r"kharcha|kharch|expense|spend|spending|leak|drain|"
    r"paisa\s*nahi\s*tik\w*|tikta\s*nahi|ud\s*jata|kharab\s*kharch|"
    r"paisa\s*kyun\s*nahi\s*tik\w*|kyun\s*nahi\s*tik\w*|"
    r"haath\s+me\s+nahi\s+rukt\w*|jeb\s+khali|"
    r"impulsive\s*spend|overspend|wasteful|paisa\s*gaya"
    r")\b"
)

_DEBT_RX = re.compile(
    r"(?ix)\b("
    r"loan|karz|emi|udhar|debt|borrow|lender|credit\s*card|"
    r"loan\s*lena|loan\s*le\s*sakta|karz\s*chuk|debt\s*free|"
    r"interest|repay|installment|mortgage"
    r")\b"
)

_PROPERTY_RX = re.compile(
    r"(?ix)\b("
    r"property|real\s*estate|flat|plot|ghar\s*khareed\w*|house\s*buy|"
    r"home\s*loan|property\s*purchase|land\s*buy|apartment|"
    r"construction\s*money|own\s*house|ghar\s*ban\w*|property\s*money"
    r")\b"
)

_SUDDEN_RX = re.compile(
    r"(?ix)\b("
    r"sudden|achanak|windfall|lottery|inheritance|virasat|"
    r"unexpected\s*(gain|loss|money|wealth)|satta|jackpot|"
    r"bonus\s*windfall|legal\s*settlement|sudden\s*loss|"
    r"big\s*loss|paisa\s*achanak|wealth\s*shock"
    r")\b"
)

_BUSINESS_PROFIT_RX = re.compile(
    r"(?ix)\b("
    r"business\s*profit|partnership\s*(money|profit|safe)|"
    r"dhandha\s*profit|vyapaar\s*profit|profit\s*aayega|"
    r"business\s*se\s*paisa|partnership\s*business|"
    r"joint\s*venture|business\s*income|"
    r"apna\s+kaam\s+chalega|startup\s+se\s+paisa|startup\s+profit"
    r")\b"
)

_LOSS_RX = re.compile(
    r"(?ix)\b("
    r"loss|nuksan|kharab\s*ho\s*gaya|paisa\s*kyun\s*nahi|"
    r"why\s*no\s*money|money\s*problem|financial\s*problem|"
    r"paisa\s*problem|garib\s*kyun|wealth\s*block|paisa\s*nahi\s*"
    r")\b"
)

_WEALTH_RX = re.compile(
    r"(?ix)\b("
    r"amir|ameer|rich|wealthy|crorepati|millionaire|wealth\s*potential|"
    r"wealth\s*creat|create\s*wealth|dhan\s*ban|paisa\s*ban|money\s*grow|"
    r"financial\s*success|prosper|affluent|dhani|maldar|"
    r"banne\s*ki\s*potential|wealth\s*capable|kitna\s*capable"
    r")\b"
)

_WEALTH_NOT_YOG_RX = re.compile(r"(?ix)\b(yog\w*|yoga)\b")

_DHANA_YOGA_RX = re.compile(
    r"(?ix)\b("
    r"dhana\s*yog\w*|dhan\s*yog\w*|lakshmi\s*yog\w*|kubera|wealth\s*yog|"
    r"rich\s*yog|dhan\s*yoga|money\s*yog|chart\s+me\s+rich\s+yog"
    r")\b"
)

_SPOUSE_MONEY_RX = re.compile(
    r"(?ix)\b("
    r"(spouse|partner|wife|husband|pati|patni)\b.{0,30}\b("
    r"paisa|money|wealth|income|salary|finance|bachat|rich|garib"
    r")\b"
    r")\b"
)


def is_finance_static_question(question: str) -> bool:
    q = (question or "").strip()
    if not q or _TIMING_RX.search(q):
        return False
    try:
        from ask_property.property_registry import is_property_static_question

        if is_property_static_question(q):
            return False
    except Exception:
        pass
    if _SPOUSE_MONEY_RX.search(q):
        return False
    if _CAREER_MONEY_MINDSET_RX.search(q):
        return False
    if _JOB_VS_BIZ_FINANCE_EXCL_RX.search(q):
        return False
    if detect_finance_archetype(q):
        return True
    return bool(is_finance_question(q))


def detect_finance_archetype(question: str) -> str | None:
    q = (question or "").strip().lower()
    if not q:
        return None
    if _CAREER_MONEY_MINDSET_RX.search(q):
        return None
    if _KITNA_PAISA_RX.search(q):
        return "wealth_potential"
    if _SAVE_VS_SPEND_RX.search(q):
        return "save_vs_spend"
    if _SPENDING_PERSONALITY_RX.search(q):
        return "spending_personality"
    if _INVESTMENT_RISK_RX.search(q):
        return "investment_risk"
    if _DISCIPLINE_RX.search(q):
        return "financial_discipline"
    if _SUDDEN_RX.search(q):
        return "sudden_gain_loss"
    if _DEBT_RX.search(q):
        return "debt_loan"
    if _PROPERTY_RX.search(q):
        try:
            from ask_property.property_registry import (  # type: ignore
                is_property_money_only_question,
                is_property_static_question,
            )

            if is_property_static_question(q) and not is_property_money_only_question(q):
                return None
        except Exception:
            pass
        return "property_money"
    if _SAVINGS_RX.search(q):
        return "savings_capacity"
    if _EXPENSE_RX.search(q):
        return "expense_pattern"
    if _INCOME_RX.search(q):
        return "income_source"
    if _BUSINESS_PROFIT_RX.search(q):
        return "business_profit"
    if _LOSS_RX.search(q):
        return "loss_reasons"
    if _DHANA_YOGA_RX.search(q):
        return "dhana_yoga"
    if _WEALTH_RX.search(q) and not (_WEALTH_NOT_YOG_RX.search(q) and _DHANA_YOGA_RX.search(q)):
        return "wealth_potential"
    return None

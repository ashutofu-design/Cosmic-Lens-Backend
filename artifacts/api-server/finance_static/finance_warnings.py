"""Locked warning templates for finance engine (5 warnings).

These are LITERAL strings. LLM never sees them, never modifies them.
Returned verbatim when the question matches a warning trigger.
"""
from __future__ import annotations
from typing import Dict

WARN_GUARANTEE_AMOUNT = (
    "Beta, koi bhi jyotish exact rupee/amount predict nahi kar sakta — "
    "'X lakh kab milenge' yeh science nahi, andaaza hai. Kundli sirf "
    "capacity, source aur direction batati hai, exact ginti nahi. "
    "Effort + planning + chart ka right yog — teeno mil ke result aata hai."
    "\n\nFinal: Capacity dekho, exact amount nahi."
)

WARN_LOTTERY_NUMBER = (
    "Lottery number, gambling pick, satta pick — yeh kundli nahi batati. "
    "H8/Rahu se sudden wealth ka YOG dikh sakta hai (haan/na), par koi "
    "specific number ya ticket batana — yeh fake jyotish ka kaam hai. "
    "Apna paisa lottery me lagana = chart se zyada Rahu pe trust."
    "\n\nFinal: Yog ho sakta hai, number nahi."
)

WARN_DEBT_TRAP = (
    "EMI bharne ke liye dusra loan lena, ya credit card se EMI chukana — "
    "yeh debt trap hai. Kundli me H6 (rin) sabhi ke chart me hota hai, "
    "lekin uska solution discipline + budget cut hai, naya loan nahi. "
    "Pehle expense audit karo, fir restructuring sochona — ek expert se."
    "\n\nFinal: Loan se loan mat chukao."
)

WARN_GET_RICH_QUICK = (
    "'Jaldi ameer banna' — yeh chart ka sawaal nahi, mindset ka problem hai. "
    "Real wealth slow + steady banti hai (Saturn quality), na ki overnight. "
    "MLM, ponzi schemes, unrealistic schemes — sab Rahu illusion hain. "
    "Kundli me dhan-yog hai bhi to wo discipline + time se hi paktaa hai."
    "\n\nFinal: Slow paisa = real paisa."
)

WARN_FRIENDS_LOAN = (
    "Dost / family ko paisa udhaar dena ya unse lena — yeh sirf rishtey "
    "kharaab karta hai, chart kuch bhi kahe. Likhit agreement + interest "
    "rate clear ho to thik hai, varna mat karo. Wapas na aaye to relationship "
    "+ paisa dono jate hain."
    "\n\nFinal: Verbal udhaar = double loss."
)

WARNINGS: Dict[str, str] = {
    "GUARANTEE_AMOUNT": WARN_GUARANTEE_AMOUNT,
    "LOTTERY_NUMBER":   WARN_LOTTERY_NUMBER,
    "DEBT_TRAP":        WARN_DEBT_TRAP,
    "GET_RICH_QUICK":   WARN_GET_RICH_QUICK,
    "FRIENDS_LOAN":     WARN_FRIENDS_LOAN,
}

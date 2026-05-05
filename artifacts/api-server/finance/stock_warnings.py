"""Phase 2.10.7 — Locked warning templates (5 warnings).

These are LITERAL strings. LLM never sees them, never modifies them.
Returned verbatim when the question matches a warning trigger.
"""
from __future__ import annotations
from typing import Dict

WARN_QUICK_MONEY = (
    "Beta, jaldi paisa kamane ki soch sabse bada nuksaan kar sakti hai. "
    "Jyotish me bhi aur reality me bhi — short-cut wealth nahi tikta. "
    "Aapki kundli ka jo bhi yog ho, slow + steady plan banao. "
    "Quick paisa scheme, get-rich-quick — STRICT NO."
    "\n\nFinal: Jaldi paisa nahi, sahi paisa banao."
)

WARN_RISK = (
    "Risk lena ya nahi — yeh aapki kundli ke H5 (speculation), Rahu, "
    "aur current dasha pe depend karta hai, instinct pe nahi. "
    "Agar engine ne RED_AVOID ya YELLOW_WAIT bola hai to bada risk mat lo. "
    "Capital ka 10-15% se zyada kabhi speculation me mat dalo."
    "\n\nFinal: Chart-based risk lo, gut-feeling pe nahi."
)

WARN_TIPS = (
    "Tip-based trading sabse bada loss ka source hai. "
    "WhatsApp tip, Telegram channel, free advice — yeh sab "
    "Rahu ka jaal hai. Aapki apni research + chart-based timing hi sahi hai. "
    "Kisi aur ke tip pe paisa lagana = blind trading."
    "\n\nFinal: Tip nahi, research + chart pe trust karo."
)

WARN_LEVERAGE = (
    "Loan le ke ya margin/leverage use kar ke invest karna — "
    "yeh aapki kundli ka H6 (rin/debt) aur H8 (sudden loss) "
    "ko activate karta hai. Loss double hota hai, profit nahi. "
    "Sirf apne saved capital se invest karo, kabhi udhaar le ke nahi."
    "\n\nFinal: Sirf apna paisa lagao, udhaar nahi."
)

WARN_EMOTIONAL = (
    "Fear se sell, greed se buy — yeh do emotion sabse bada loss "
    "karwate hain. Moon (mind) jab afflicted ho to emotional trading "
    "increase hota hai. Plan banao pehle, fir execute karo. "
    "Daily P&L mat dekho — weekly/monthly review karo."
    "\n\nFinal: Plan se trade karo, emotion se nahi."
)

WARNINGS: Dict[str, str] = {
    "QUICK_MONEY": WARN_QUICK_MONEY,
    "RISK": WARN_RISK,
    "TIPS": WARN_TIPS,
    "LEVERAGE": WARN_LEVERAGE,
    "EMOTIONAL": WARN_EMOTIONAL,
}

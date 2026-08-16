"""Fix spelling, then name the topic. The model answers; this only prepares the question."""
from __future__ import annotations

import re

# Spelling only — not answers.
_FIXES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"realationship|relatonship|relatianship|relashionship", re.I), "relationship"),
    (re.compile(r"numerlogy|numarology|numerolgy|numerlog", re.I), "numerology"),
    (re.compile(r"transcation|transaktion", re.I), "transaction"),
    (re.compile(r"paymnet|payement", re.I), "payment"),
    (re.compile(r"kundlee|kundaly", re.I), "kundli"),
    (re.compile(r"astrovastu|astro vastu", re.I), "astrovastu"),
]


def normalize(text: str) -> str:
    out = text or ""
    for pat, repl in _FIXES:
        out = pat.sub(repl, out)
    return out.strip()


def topic(text: str) -> str:
    """One category label for the answerer. Not an answer."""
    t = normalize(text).lower()
    if re.search(r"cosmo|user\s*id|userid", t):
        return "identity"
    if re.search(r"wallet|transaction|payment|order|razorpay|upi|gst|invoice", t):
        return "payment"
    if re.search(r"login|otp|google|logout|crash|hang|update\s*app", t):
        return "account_access"
    if re.search(r"relationship|love\s*realit|breakup|loyalty|couple", t):
        return "love_reality"
    if re.search(r"milan|guna|ashtakoot", t):
        return "kundli_milan"
    if re.search(r"numerology|life\s*path|life\s*mastery", t):
        return "numerology"
    if re.search(r"vastu|floor\s*plan", t):
        return "astrovastu"
    if re.search(r"\bv3\b|live\s*chat|cosmic\s*guide", t):
        return "v3_live"
    if re.search(r"ask\s*(pack|tab|question)|cosmic\s*pack", t):
        return "ask_v1"
    if re.search(r"pdf|my\s*reports?|report", t):
        return "reports"
    if re.search(r"\bcareer\b", t):
        return "career"
    if re.search(r"\bhealth\b", t):
        return "health"
    if re.search(r"\bfinance\b", t):
        return "finance"
    if re.search(r"founder|panchang|planet|gemstone|refer|language|theme", t):
        return "more_profile"
    return "app_howto"

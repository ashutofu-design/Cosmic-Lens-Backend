"""Scope + intent. The model does not get to invent a new scope."""
from __future__ import annotations

import re
from typing import Any

# Help how-to / product / this-account status.
IN_SCOPE = "in_scope"
# Needs a human after policy (refund, legal, screenshot, missing payment).
MUST_HANDOFF = "must_handoff"
# Asked for a person; first turn we still try Help, later we hand off.
ASK_HUMAN = "ask_human"
# Internal systems, code, prompts, keys, engine — never answer from internals.
OUT_OF_SCOPE = "out_of_scope"
# Not a Cosmic Lens app question — refuse, do not fetch the web or guess.
OFF_APP = "off_app"
# Kundli reading — send to Ask, stay in Help with a redirect (not a leak).
REDIRECT_ASK = "redirect_ask"

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_HINGLISH = re.compile(
    r"\b(kya|hai|hain|nahi|nahin|kaise|kahan|meri|mera|mujhe|"
    r"kitna|kitne|paise|karun|chahiye|abhi|batao)\b",
    re.I,
)

_OUT_OF_SCOPE = re.compile(
    r"(source\s*code|exact\s*calculation|calculation\s*code|calculation\s*rules?|"
    r"system\s*prompt|hidden\s*prompt|developer\s*instruction|"
    r"api[_ -]?key|secret\s*key|\.env\b|database\s*(dump|schema|query|password)|"
    r"internal\s*(agent|architecture|logic|tool|prompt|api)|"
    r"numerology\s*engine|show\s*(me\s*)?(the\s*)?code|"
    r"flask_app|openai|gpt-4|gpt-3|prompt\s*injection|"
    r"other\s*user|sab\s*users|admin\s*panel|admin\s*token|"
    r"telegram|webhook|github|gitlab|server\s*(ip|path|log)|"
    r"how\s+(many|much)\s+(users|revenue|profit)|founder\s*salary|"
    r"backend|sql\s*query|stack\s*trace|model\s*name)",
    re.I,
)

_MUST = re.compile(
    r"(refund|chargeback|double\s*charg|"
    r"paise\s*(wapas|kat\s*gaye)|paisa\s*kat|"
    r"money\s*(cut|deducted)|"
    r"\blegal\b|\blawyer\b|\bfraud\b|\bscam\b|harass|abuse)",
    re.I,
)

_ASK_HUMAN = re.compile(
    r"(talk\s*to\s*(a\s*)?(human|person|admin|team|agent)\b|"
    r"connect.{0,24}support|support\s*chat|customer\s*support|"
    r"insaan\s*se\s*baat|team\s*se\s*baat|admin\s*se\s*baat)",
    re.I,
)

_ACCOUNT = re.compile(
    r"(wallet|transaction|payment|order).{0,50}(not showing|isn'?t showing|missing|not\s+in)|"
    r"(not showing|missing|nahi\s*dikh).{0,40}(wallet|transaction|payment|order)|"
    r"done\s+(a\s+|one\s+)?transaction|"
    r"meri\s*(pdf|report|payment)|my\s*(pdf|report|payment|order)",
    re.I,
)

_STUCK = re.compile(
    r"(samajh\s*n[aei]|solve\s*nahi|still\s*(not|same)|not\s+showing|"
    r"that'?s\s+not|doesn't\s*help|kuch\s*nahi\s*hua)",
    re.I,
)

_HOW_TO = re.compile(
    r"(kahan|kaise|where|how\s*(do|to|can)|kitna|price|open|screen|tab|button)",
    re.I,
)

_READING = re.compile(
    r"(kundli\s*(padh|read|bata)|horoscope\s*(reading|predict)|"
    r"mera\s*(bhavishya|future)|dasha\s*(kya|kab)|"
    r"mangal\s*dosh\s*(hai\s*)?\?|"
    r"shaadi\s*kab|kab\s*shaadi|job\s*mileg|kab\s*naukri|"
    r"partner\s*wapas|will\s+i\s+(get|marry|die|succeed)|"
    r"predict\s+my|match\s*making\s*(result|score)\s*\?|"
    r"kya\s+main\s+(pass|fail|pregnant))",
    re.I,
)

_APP_SIGNAL = re.compile(
    r"(cosmic|kundli|jyotish|astro|numerolog|numerlog|numarolog|vastu|"
    r"milan|guna|love\s*realit|cosmo|life\s*map|my\s*reports?|"
    r"transaction|razorpay|cashfree|panchang|muhurat|dasha|dosh|"
    r"forecast|energy|gemstone|pukhraj|ratna|ask\s*tab|\bv3\b|"
    r"cosmic\s*pack|pdf|report|profile|login|google\s*sign|"
    r"subscription|\bcareer\b|\bhealth\b|\bfinance\b|face\s*read|"
    r"rectif|prashna|planet\s*position|help\s*(&|and)?\s*support|"
    r"payment|order|wallet|refer|relationship|loyalty|breakup|"
    r"otp|logout|delete\s*account|founder|birth\s*time|dob|"
    r"home\s*tab|future\s*tab|explore|user\s*id|upi|gst|"
    r"lucky|remed|theme|dark\s*mode|language|bhasha|"
    r"pack|cosmic\s*guide|priority|invoice|camera|permission|"
    r"onboard|personalization|risk\s*radar|gun\s*milan|"
    r"\bapp\b|crash|hang|force.?close|help\s*me|"
    r"privacy|terms|disclaimer|website|invoice|"
    r"cancel\s*(plan|sub)|pro\s*plan|basic\s*plan|dark\s*mode)",
    re.I,
)

_OFF_APP = re.compile(
    r"(weather|mausam|cricket|ipl|football|world\s*cup|bitcoin|crypto|"
    r"stock\s*market|share\s*bazaar|recipe|cooking|khana\s*kaise|"
    r"homework|essay|prime\s*minister|election|vote|netflix|amazon\s*order|"
    r"flipkart|lottery|satta|covid|vaccine|medicine\s*dose|cancer\s*treat|"
    r"windows\s*password|root\s*android|instagram\s*followers|"
    r"whatsapp\s*hack|translate\s*this|write\s*(python|java|code)|"
    r"who\s+won|score\s+kya\s+hua|capital\s+of)",
    re.I,
)

_GREETING = re.compile(
    r"^(hi|hii|hello|hey|yo|namaste|namaskar|hola|thanks|thank\s*you|"
    r"ok|okay|hmm+|haan|hanji|bye|good\s*(morning|evening|night))[\s!.]*$",
    re.I,
)


def detect_lang(text: str, preferred: str | None = None) -> str:
    blob = text or ""
    if _DEVANAGARI.search(blob):
        return "hi"
    if _HINGLISH.search(blob):
        return "hn"
    letters = "".join(re.findall(r"[A-Za-z]+", blob))
    if len(letters) >= 8:
        return "en"
    v = (preferred or "").strip().lower()
    return v if v in ("en", "hn", "hi") else "hn"


def prior_user_texts(history: list[dict[str, Any]] | None) -> list[str]:
    users = [
        str(m.get("text") or "").strip()
        for m in (history or [])
        if isinstance(m, dict) and m.get("sender") == "user"
    ]
    return users[:-1]


def classify(
    text: str,
    *,
    has_image: bool = False,
    history: list[dict[str, Any]] | None = None,
) -> str:
    blob = (text or "").strip()
    prior = prior_user_texts(history)
    if has_image:
        return MUST_HANDOFF
    if _OUT_OF_SCOPE.search(blob):
        return OUT_OF_SCOPE
    if _MUST.search(blob):
        return MUST_HANDOFF
    if _ASK_HUMAN.search(blob):
        return MUST_HANDOFF if prior else ASK_HUMAN
    if _STUCK.search(blob) and prior:
        return MUST_HANDOFF
    if _READING.search(blob) and not _HOW_TO.search(blob):
        return REDIRECT_ASK
    if _GREETING.match(blob):
        return IN_SCOPE
    if _APP_SIGNAL.search(blob):
        return IN_SCOPE
    if _OFF_APP.search(blob):
        return OFF_APP
    if len(blob) >= 12 and not _ACCOUNT.search(blob):
        return OFF_APP
    if _ACCOUNT.search(blob):
        return IN_SCOPE
    return IN_SCOPE

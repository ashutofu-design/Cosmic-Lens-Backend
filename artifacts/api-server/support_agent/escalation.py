"""Handoff policy — code decides, not the model."""
from __future__ import annotations

from support_agent.knowledge import pick

HANDOFF = {
    "en": "I can’t fully resolve this here. A team member will join this chat shortly — please wait, they’ll reply here.",
    "hn": "Yeh yahan poora solve nahi ho paaya. Team member abhi is chat mein aayenge — thoda wait kariye, yahin reply aayega.",
    "hi": "यह यहाँ पूरा हल नहीं हो पाया। टीम सदस्य जल्द इस चैट में आएंगे — कृपया प्रतीक्षा करें।",
}

OUT_OF_SCOPE = {
    "en": "I can’t share internal system details, code, or private data. I only help with the Cosmic Lens app — payments, My Reports, Profile, and how-to.",
    "hn": "Internal system details, code, ya private data share nahi kar sakte. Sirf Cosmic Lens app how-to: payments, My Reports, Profile.",
    "hi": "आंतरिक सिस्टम, कोड या निजी डेटा यहाँ नहीं दे सकते। केवल Cosmic Lens ऐप हाउ-टू।",
}

OFF_APP = {
    "en": "I only help with the Cosmic Lens app — Home, Life Map, Ask, Future, My Reports, payments, and Profile. I can’t answer questions outside the app.",
    "hn": "Main sirf Cosmic Lens app pe help karta hoon — Home, Life Map, Ask, Future, My Reports, payments, Profile. App ke bahar ke sawaal nahi le sakta.",
    "hi": "मैं केवल Cosmic Lens ऐप पर मदद करता हूँ। ऐप के बाहर के सवाल नहीं ले सकता।",
}

HELP_FIRST = {
    "en": "I can help with this account first — payments, PDFs, login, COSMO ID. Tell me the issue. If I cannot solve it after checking, a team member will join.",
    "hn": "Pehle is account pe help kar sakta hoon — payment, PDF, login, COSMO ID. Issue batao. Check ke baad solve na ho to team join karegi.",
    "hi": "पहले इस खाते पर मदद कर सकता हूँ — पेमेंट, PDF, लॉगिन। समस्या बताएं।",
}

REDIRECT_ASK = {
    "en": "Chart and kundli readings are on the Ask tab, not this Help chat. I can still help with app how-to: payments, My Reports, Profile.",
    "hn": "Kundli reading Ask tab pe hai, is Help chat pe nahi. App how-to yahan: payments, My Reports, Profile.",
    "hi": "कुंडली रीडिंग Ask टैब पर है। यहाँ ऐप हाउ-टू: पेमेंट, माई रिपोर्ट्स, प्रोफ़ाइल।",
}


def handoff_reply(lang: str) -> str:
    return pick(HANDOFF, lang)


def out_of_scope_reply(lang: str) -> str:
    return pick(OUT_OF_SCOPE, lang)


def help_first_reply(lang: str) -> str:
    return pick(HELP_FIRST, lang)


def redirect_ask_reply(lang: str) -> str:
    return pick(REDIRECT_ASK, lang)


def off_app_reply(lang: str) -> str:
    return pick(OFF_APP, lang)

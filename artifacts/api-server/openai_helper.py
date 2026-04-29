"""
OpenAI helper for Cosmic Lens.

Single entry point: ai_ask(question, kundli, lang, reply_idx) -> dict

The helper builds a domain-locked Vedic astrology prompt, sends the user's
question + their kundli context to OpenAI, and returns a normalised dict
shaped like the rule-based ask_engine output so downstream code does not
need to branch.

Configuration:
- OPENAI_API_KEY  (required)  user-provided secret
- OPENAI_MODEL    (optional)  defaults to "gpt-4.1-mini" (smarter than 4o-mini, slightly higher cost)
- OPENAI_TIMEOUT  (optional)  seconds, defaults to 30
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Optional

# Lazy KP/transit calculators — only loaded when needed so test paths don't
# need swisseph configured.
def _kp_calc():
    from kp_engine import calculate_kp  # type: ignore
    return calculate_kp


def _swe():
    import swisseph as swe  # type: ignore
    return swe


def _chart_intel():
    """Lazy-load chart_intelligence to keep test paths import-light."""
    from chart_intelligence import analyze_chart, format_intelligence  # type: ignore
    return analyze_chart, format_intelligence


def _marriage_engine():
    """Lazy-load deterministic marriage verdict engine."""
    from marriage_engine import assess_marriage, format_verdict_for_prompt  # type: ignore
    return assess_marriage, format_verdict_for_prompt


def _stock_engine():
    """Lazy-load deterministic stock-market verdict engine."""
    from stock_engine import (assess_stock,                     # type: ignore
                              format_verdict_for_prompt as _fmt_stock,
                              extract_window_str as _stock_window_str,
                              classify_stock_question)
    return assess_stock, _fmt_stock, _stock_window_str, classify_stock_question


# Stock-question gate (regex). Triggers stock_engine ONLY when the question
# is genuinely about share-market / trading / investing — not for generic
# wealth/loan/property finance questions that the engine isn't designed for.
_STOCK_QUESTION_RX = __import__("re").compile(
    # Anchored stock vocabulary only. Bare "bazar" / "व्यापार" are NOT here
    # because they false-trigger generic business-and-market questions; we
    # require explicit share/stock/equity/fund/trading anchors instead.
    r"(?:\b(stocks?|shares?|nifty|sensex|share[- ]?market|stock[- ]?market|"
    r"trading|trader|broker(age)?|equity|equities|portfolio|demat|"
    r"intraday|swing|scalping|fno|futures?|options?|derivative|"
    r"crypto|bitcoin|ethereum|dogecoin|nft|"
    # NOTE: SIP / mutual-funds / lump-sum / generic invest* DELIBERATELY
    # REMOVED from stock vocab. Those are long-term wealth instruments
    # (handled by wealth_engine), not active trading. Active-trading
    # anchors above (stocks/shares/intraday/F&O/etc.) still route here.
    r"share[- ]?bazar|stock[- ]?bazar|shaire[- ]?bazaar|shaire[- ]?bazar|"
    # Trading-context bigrams that are unambiguously stock-market
    # (not generic life-finance). DELIBERATELY EXCLUDED because they
    # false-trigger on non-stock contexts:
    #   • "risk management" (life/health/work)
    #   • "capital protection" (insurance/savings)
    #   • bare "market mein aau/jaau/jaana" (sabzi/local market)
    # The kept set requires a stock-trading-specific noun phrase or
    # an explicit re-entry verb ("dobara/wapas/wapsi") that civilians
    # don't use for sabzi-market visits.
    r"profit[- ]?booking|stop[- ]?loss|trailing[- ]?stop|"
    r"risk[- ]?reward|position[- ]?sizing|"
    r"max(?:imum)?[- ]?drawdown|hedging|"
    r"average[- ]?down|margin[- ]?call|wealth[- ]?window|"
    r"dhan[- ]?yog|dhana[- ]?yog)\b"
    r"|f&o|F&O"
    # Market re-entry / wapsi phrasings — unambiguous trading lingo.
    # "dobara market" (returning to market after exit) and
    # "market mein wapsi/wapas/wapis/return" are trading-specific;
    # nobody uses these for sabzi-market or local-market trips.
    r"|\bdobara\s+market\b"
    r"|\bmarket\s+(?:me|mein|m[ae])\s+(?:wapsi|wapas|wapis|return)\b"
    # "paisa lagana" (to deploy capital) — narrow trading verb that's
    # almost always about investing/trading. Allow inflections.
    r"|\bpaisa\s+(?:laga(?:na|u|ye|yi|ya)?|lagaa(?:na|u|ye|yi|ya)?|"
    r"lag\s+(?:gaya|gayi))\b"
    r"|शेयर|शेयर बाज़ार|निवेश)",
    __import__("re").IGNORECASE,
)


# Wealth-instrument override (NARROWED). Matches ONLY explicit long-term
# wealth-INSTRUMENT names (SIP / MF / PPF / NPS / FD / RD / insurance /
# sovereign-gold / bonds). DELIBERATELY excludes generic words like
# "savings", "kharcha", "expense", "corpus" — those would over-block
# legitimate stock queries like "intraday trading expense kitna hai".
# Generic savings/kharcha vocabulary still routes to wealth via
# `_WEALTH_QUESTION_RX` directly; it just doesn't suppress stock here.
_WEALTH_INSTRUMENT_STRICT_RX = __import__("re").compile(
    r"\b(?:sip|sips|mutual[- ]?funds?|\bmf\b|\bmfs\b|"
    r"ppf|nps|nsc|kvp|elss|"
    r"\bfd\b|\bfds\b|fixed[- ]?deposit|fixed[- ]?deposits|"
    r"\brd\b|\brds\b|recurring[- ]?deposit|"
    r"insurance|life[- ]?insurance|term[- ]?insurance|health[- ]?insurance|"
    r"sovereign[- ]?gold|gold[- ]?bond)\b",
    __import__("re").IGNORECASE,
)

# Strong stock anchors. If ANY of these explicitly appear, the question is
# a real stock-trading question — even when SIP/MF is also mentioned (e.g.
# "share market vs SIP — kahan invest karu" → user genuinely wants both
# compared, route to stock since stock has the comparison framework).
_STRONG_STOCK_ANCHOR_RX = __import__("re").compile(
    r"\b(?:stocks?|shares?|nifty|sensex|share[- ]?market|stock[- ]?market|"
    r"intraday|swing|scalping|fno|futures?|options?|derivative|"
    r"equity|equities|portfolio|demat|trading|trader|broker(?:age)?|"
    r"crypto|bitcoin|ethereum)\b|f&o|F&O",
    __import__("re").IGNORECASE,
)


def _is_stock_question(text: str) -> bool:
    """True iff text matches the stock trigger gate AND is not over-ridden
    by a wealth-instrument-only context. Override fires only when the user
    explicitly names a wealth instrument (SIP/MF/PPF/etc.) AND no strong
    stock anchor (intraday/nifty/share market/etc.) coexists. This keeps
    'SIP mein paisa lagana?' routed to wealth, while 'share market vs SIP
    kya behtar?' stays with stock."""
    if not isinstance(text, str) or not text.strip():
        return False
    if not _STOCK_QUESTION_RX.search(text):
        return False
    # Stock RX matched → check for the wealth-instrument override
    if (_WEALTH_INSTRUMENT_STRICT_RX.search(text)
            and not _STRONG_STOCK_ANCHOR_RX.search(text)):
        return False
    return True


def _love_engine():
    """Lazy-load deterministic love & relationship verdict engine."""
    from love_engine import (assess_love,                       # type: ignore
                              format_verdict_for_prompt as _fmt_love,
                              extract_window_str as _love_window_str,
                              classify_love_question)
    return assess_love, _fmt_love, _love_window_str, classify_love_question


# Love-question gate. Triggers love_engine ONLY when question is genuinely
# about romance / relationship — NOT about marriage (marriage_engine wins
# the routing collision via _MARRIAGE_OVERRIDE_RX below).
_LOVE_QUESTION_RX = __import__("re").compile(
    r"(?:\b(love|pyaar|pyar|crush|ishq|mohabbat|romance|romantic|"
    r"dating|girlfriend|boyfriend|gf|bf|partner|rishta|rishtey|relation|"
    r"relationship|breakup|break[- ]?up|patch[- ]?up|reunion|reconcil|"
    r"chakkar|chakar|affair|cheating|cheater|cheated|dhokha|dhoka|"
    r"dhokhha|dhoke|bewafai|be-wafai|wafa|infidel|infidelity|"
    r"unfaithful|disloyal|"
    r"soulmate|jeevansathi|sathi|saathi|"
    r"propose|izhaar|izhar|long[- ]?distance|ldr|"
    r"one[- ]?sided|ekta-?rafa|ektarafa|"
    r"compat(?:ible|ibility)|jodi|joodi)\b"
    r"|प्यार|प्रेम|रिश्ता|ब्रेकअप|गर्लफ्रेंड|बॉयफ्रेंड|"
    r"धोखा|बेवफा|बेवफाई|चक्कर|किसी और|अफेयर|एफेयर|"
    r"प्रेमी|प्रेमिका|साथी|जीवनसाथी)",
    __import__("re").IGNORECASE,
)

# Marriage keywords that override love routing — if the user mentions
# shaadi/vivah/spouse, it's a marriage question (even with love vocabulary
# like "love marriage kab hogi"), so marriage_engine handles it.
_MARRIAGE_OVERRIDE_RX = __import__("re").compile(
    r"(?:\b(shaadi|shadi|marriage|marry|married|vivaah|vivah|"
    r"wife|husband|spouse|biwi|pati|patni|dulhan|dulha|"
    r"engagement|engaged|sagai|mangni|"
    r"saptam|kalatra)\b"
    r"|शादी|विवाह|पति|पत्नी|दूल्हा|दुल्हन)",
    __import__("re").IGNORECASE,
)


def _is_love_question(text: str) -> bool:
    """True iff text matches love trigger AND not the marriage-override gate.
    Marriage routing has priority — questions like 'love marriage kab hogi'
    go to marriage_engine, not love_engine."""
    if not isinstance(text, str) or not text.strip():
        return False
    if _MARRIAGE_OVERRIDE_RX.search(text):
        return False
    return bool(_LOVE_QUESTION_RX.search(text))


def _career_engine():
    """Lazy-load deterministic career & profession verdict engine."""
    from career_engine import (assess_career,                    # type: ignore
                                format_verdict_for_prompt as _fmt_career,
                                classify_career_question)
    return assess_career, _fmt_career, classify_career_question


# Career-question gate. Triggers career_engine when question is genuinely
# about job / career / promotion / business / transfer / govt-exam — but
# NOT when stock-market or marriage routing already wins. Order in the
# orchestrator below: marriage > stock > love > career > general.
_CAREER_QUESTION_RX = __import__("re").compile(
    r"(?:\b(career|job|jobs|naukri|naukari|nokri|nokari|naukariya|"
    r"profession|professional|kaam|kaamkaaj|kam|"
    r"promotion|promote|promoted|appraisal|increment|hike|raise|"
    r"transfer|posting|relocation|relocate|deputation|secondment|"
    r"resign|resignation|quit|"
    r"interview|placement|joining|offer letter|offer-letter|joining-letter|"
    r"office|boss|manager|colleague|workplace|company|firm|organization|organisation|"
    r"govt|government|sarkari|sarkar|civil[- ]?services|"
    r"upsc|ssc|ibps|rbi|psc|tnpsc|mpsc|uppsc|bpsc|"
    r"ias|ips|irs|ifs|"
    r"foreign job|foreign[- ]?job|abroad|videsh|paradesh|onsite|"
    r"freelance|freelancer|freelancing|consult(?:ing|ant|ancy)?|"
    r"business|vyapar|vyapaar|vyaapar|dhanda|"
    r"startup|start[- ]?up|entrepreneur(?:ship)?|founder|co[- ]?founder|"
    r"partnership|joint[- ]?venture|jv|"
    r"setback|fired|laid[- ]?off|layoff|terminated|sacked|"
    r"unemployed|berojgar|berozgar|bekar|bekaar|"
    r"salary|stipend|wage|earnings|pay[- ]?package|ctc|"
    r"field|line|sector|industry|stream|specialisation|specialization)\b"
    r"|नौकरी|काम|करियर|कैरियर|पेशा|व्यापार|व्यवसाय|धंधा|"
    r"प्रमोशन|तरक्की|तबादला|ट्रांसफर|पोस्टिंग|"
    r"सरकारी|सरकार|इंटरव्यू|बॉस|ऑफिस|"
    r"साझेदार|साझेदारी|पार्टनरशिप|स्टार्टअप)",
    __import__("re").IGNORECASE,
)

# Stock-market vocabulary that should NOT trigger career_engine even if
# career keywords (business / venture) are also present — e.g.
# "share business kaisa rahega" must go to stock_engine.
#
# Bare "equity/share/shares" is INTENTIONALLY excluded because it collides
# with legitimate career queries like "startup partnership equity split"
# or "share business start karu". We require an unambiguous trading-context
# anchor (nifty/sensex/share[- ]market/trading/demat/broker/etc.) OR an
# explicit instrument that has no career meaning (intraday/fno/options/
# crypto/sip). Pure "equity"/"share" without these anchors stays in career.
_CAREER_STOCK_OVERRIDE_RX = __import__("re").compile(
    r"\b(nifty|sensex|share[- ]?market|stock[- ]?market|share[- ]?bazar|"
    r"stock[- ]?bazar|shaire[- ]?bazaar|shaire[- ]?bazar|"
    r"trading|trader|broker(age)?|demat|"
    r"intraday|swing|scalping|fno|f&o|futures?|options?|derivative|"
    r"crypto|bitcoin|ethereum|dogecoin|nft|mutual[- ]?funds?|sip|lump[- ]?sum)\b"
    r"|शेयर बाज़ार|शेयर बाजार",
    __import__("re").IGNORECASE,
)


def _is_career_question(text: str) -> bool:
    """True iff text matches career trigger AND not marriage/stock overrides.
    Routing priority above career: marriage > stock > love. So this gate
    only needs to defend against stock-market false-positives explicitly
    (the higher engines already short-circuit before this is checked)."""
    if not isinstance(text, str) or not text.strip():
        return False
    if _CAREER_STOCK_OVERRIDE_RX.search(text):
        return False
    return bool(_CAREER_QUESTION_RX.search(text))


def _health_engine():
    """Lazy-load deterministic health & vitality verdict engine."""
    from health_engine import (assess_health,                    # type: ignore
                                format_verdict_for_prompt as _fmt_health,
                                classify_health_question)
    return assess_health, _fmt_health, classify_health_question


# Health-question gate. Triggers health_engine when question is genuinely
# about wellness / illness / surgery / mental-health / addiction / parent-
# health / longevity. Routing priority above health:
#   marriage > stock > love > career > health > general.
# This gate fires LAST among the topical engines, so we only need to defend
# against false positives that look medical but actually belong to a
# higher-priority bucket — e.g. "career stress" (career), "share market
# tension" (stock), "rishta tension" (relationship/love), "santaan / IVF
# / pregnancy" (child timing — handled in marriage/general flow).
_HEALTH_QUESTION_RX = __import__("re").compile(
    r"(?:\b("
    r"health|healthy|healthcare|"
    r"swasthya|swasth|swaasthya|sehat|sehet|sehatmand|tabiyat|tabeeyat|tabiat|"
    r"illness|sickness|sick|unwell|"
    r"disease|diseased|"
    r"bimari|bimaari|beemar|beemari|beemaari|bimaar|"
    r"rog|rogi|rogon|rogi|"
    r"treatment|treat|cure|cured|curing|heal|healed|healing|"
    r"theek|theekh|teek|theeke|achha[- ]?ho|thik|"
    r"infection|infections|infected|infect|infectious|"
    r"viral|virus|bacterial|bacteria|fungal|sankraman|"
    r"flu|influenza|cold|cough|khansi|jukam|"
    r"medicine|medicines|medication|medicational|dawai|dawaai|davai|davaai|"
    r"hospital|hospitals|aspataal|aspatal|"
    r"doctor|doctors|physician|specialist|consultation|"
    r"operation|operations|surgery|surgeries|surgical|"
    r"chronic|acute|sub[- ]?acute|"
    r"recovery|recover|recovering|recovered|"
    r"symptoms|symptom|lakshan|lakshana|"
    r"diagnosis|diagnose|diagnosed|"
    r"depression|depressed|"
    r"anxiety|anxious|panic|panic[- ]?attack|"
    r"stress|stressful|tension|tensed|"
    r"mental|mental[- ]?health|manasik|maanasik|"
    r"sleep|sleeping|insomnia|nind|neend|"
    r"suicide|suicidal|self[- ]?harm|self[- ]?injur(?:y|ies)|"
    r"atmahatya|aatmhatya|aatm[- ]?hatya|atmhatya|"
    r"khudkushi|khud[- ]?kushi|"
    r"jaan[- ]?dena|jaan[- ]?dene|jeena nahi|jeena nahin|"
    r"marna chahta|marna chahti|end[- ]?my[- ]?life|kill[- ]?myself|"
    r"longevity|aayu|ayu|aayush|ayush|jeevankaal|lifespan|life[- ]?span|"
    r"umar|umra|umer|umr|jeevan|"
    r"vitality|stamina|immunity|energy[- ]?levels?|weakness|kamzori|"
    r"khoon|blood|"
    r"addiction|addicted|addict|"
    r"nasha|nashe|nashaa|sharab|sharaab|daru|daaru|"
    r"cigarette|cigarettes|smoking|smoke|smoker|tobacco|tambaku|"
    r"drug|drugs|"
    r"injury|injuries|injured|chot|chot[- ]?lagna|accident|accidents|"
    r"durghatna|haadsa|haadasa|"
    r"fever|bukhar|bukhaar|"
    r"diabetes|sugar|madhumeh|"
    r"blood[- ]?pressure|bp|hypertension|"
    r"cancer|tumor|tumour|"
    r"heart|hriday|hridaya|cardiac|"
    r"kidney|gurda|liver|jigar|lung|fefda|stomach|pet|"
    r"eye|eyes|aankh|aankhein|"
    r"ear|ears|kaan|"
    r"skin|tvacha|tvacaa|chamdi|"
    r"thyroid|asthma|migraine|arthritis|joint[- ]?pain|"
    r"reproductive|fertility|infertility|infertile|"
    r"pcos|pcod|menstrual|menstruation|periods|period|"
    r"sperm|sperm[- ]?count|semen|virya|veerya|"
    r"conceive|conceiving|conception|"
    r"pregnancy|pregnant|garbh|garbhdharan|garbhavastha|"
    r"santan|santaan|aulad|aulaad|baby[- ]?planning|ivf|iui|"
    r"maa[- ]?ki[- ]?tabiyat|papa[- ]?ki[- ]?tabiyat|"
    r"parent[- ]?health|parents[- ]?health|"
    r"father[- ]?health|mother[- ]?health|"
    r"pita[- ]?ki[- ]?tabiyat|mata[- ]?ki[- ]?tabiyat"
    r")\b)"
    r"|स्वास्थ्य|स्वस्थ|सेहत|बीमारी|बीमार|रोग|दवा|दवाई|अस्पताल|"
    r"डॉक्टर|ऑपरेशन|सर्जरी|उपचार|इलाज|"
    r"लक्षण|जांच|निदान|"
    r"अवसाद|डिप्रेशन|चिंता|घबराहट|तनाव|"
    r"मानसिक|दिमागी|"
    r"नींद|अनिद्रा|"
    r"आयु|जीवनकाल|"
    r"नशा|शराब|सिगरेट|धूम्रपान|तंबाकू|"
    r"चोट|दुर्घटना|हादसा|"
    r"बुखार|मधुमेह|कैंसर|दिल|गुर्दा|जिगर|पेट|"
    r"आंख|कान|त्वचा|दर्द|तबियत|तबीयत",
    __import__("re").IGNORECASE,
)


def _is_health_question(text: str) -> bool:
    """True iff text matches health trigger AND no higher-priority engine
    (marriage / stock / love / career) would have already short-circuited
    this turn. Higher-priority gates are applied UPSTREAM in
    `_build_messages`, so by the time we reach the health block we only
    need to confirm the text genuinely smells health-related.
    Note: standalone 'stress'/'tension' words are intentionally INCLUDED
    here. The career engine claims them only when career keywords are
    also present — health gate fires after career has been ruled out, so
    a leftover 'stress' here is genuinely mental-health territory."""
    if not isinstance(text, str) or not text.strip():
        return False
    return bool(_HEALTH_QUESTION_RX.search(text))


def _wealth_engine():
    """Lazy-load deterministic wealth & finance verdict engine."""
    from wealth_engine import (assess_wealth,                    # type: ignore
                                format_verdict_for_prompt as _fmt_wealth,
                                classify_wealth_question)
    return assess_wealth, _fmt_wealth, classify_wealth_question


# Wealth-question gate. Triggers wealth_engine when question is genuinely
# about salary / business profit / loan / property / inheritance / savings
# / sudden windfall / debt-recovery / partnership-finance. Routing priority
# above wealth: marriage > stock > love > career. Wealth fires AFTER stock
# so it must NOT swallow share/equity/SIP/intraday/F&O — those belong to
# stock_engine. Bare "paisa" / "money" alone are NOT here because they
# false-trigger generic chats; we require explicit dhana/wealth/loan/
# property/inheritance/savings/salary/business-profit anchors instead.
_WEALTH_QUESTION_RX = __import__("re").compile(
    r"(?:\b("
    # core wealth vocabulary
    r"wealth|wealthy|prosper(?:ity|ous)?|"
    r"dhana?[- ]?yog|dhanyog|dhana|dhan|"
    r"lakshmi[- ]?yog|laxmi[- ]?yog|maha[- ]?lakshmi|"
    r"finance|financial|finances|financially|"
    r"income|incomes|earning|earnings|kamai|kamaai|kamaaee|"
    r"salary|salaries|tankhwah|tankhah|vetan|"
    r"savings?|saving|bachat|jamapunji|"
    r"corpus|net[- ]?worth|"
    # business profit (NOT business in general — that's career)
    r"business[- ]?profit|business[- ]?income|business[- ]?earning|"
    r"profit|profits|profitable|munafa|munafaa|labh|laabh|"
    r"loss|losses|nuksan|nuksaan|haani|"
    # loan / debt / EMI / credit
    r"loan|loans|karz|karza|karzaa|qarz|qarza|udhaar|udhar|"
    r"emi|emis|installment|kisht|"
    r"debt|debts|borrow(?:ing)?|borrowed|"
    r"home[- ]?loan|car[- ]?loan|personal[- ]?loan|education[- ]?loan|"
    r"credit[- ]?card|credit[- ]?score|cibil|"
    # property / real estate
    r"property|properties|propert(?:y|ies)|"
    r"real[- ]?estate|realestate|"
    r"makaan|makan|"
    # ghar lena / ghar lene / ghar liya / ghar lega … and khareedna /
    # khareedne / khareedi inflections — Hinglish verbs conjugate by
    # vowel ending, so we match the shared prefix `ghar[- ]?(le|khar)`
    # plus a short word-character suffix.
    r"ghar[- ]?(?:le|liy|leg|lej|leke|kharee?d|kha?r[iy]?d)\w*|"
    r"flat|plot|plots|land[- ]?purchase|land[- ]?buy|zameen|zamin|"
    r"house[- ]?buy|house[- ]?purchase|"
    r"house[- ]?(?:le|liy|leg|leke)\w*|"
    # inheritance / legacy
    r"inheritance|inherit|inherited|heir|"
    r"virasat|viraasat|paitrak|pitrarjit|"
    r"will[- ]?money|ancestral[- ]?property|paternal[- ]?property|"
    # sudden gain / windfall / lottery (engine ALWAYS softens these)
    r"sudden[- ]?gain|sudden[- ]?gains|sudden[- ]?money|"
    r"sudden[- ]?profit|sudden[- ]?profits|"
    r"windfall|windfalls|"
    r"lottery|jackpot|kbc|satta|matka|"
    r"unexpected[- ]?money|unexpected[- ]?gain|unexpected[- ]?gains|"
    r"unexpected[- ]?profit|unexpected[- ]?windfall|"
    r"lucky[- ]?break|lucky[- ]?breaks|lucky[- ]?money|"
    r"achanak[- ]?paisa|achanak[- ]?dhan|achanak[- ]?fayda|"
    r"achanak[- ]?labh|achanak[- ]?munafa|"
    # debt recovery / outstanding
    r"debt[- ]?recovery|recover[- ]?money|paisa[- ]?wapas|"
    r"udhaar[- ]?wapas|paisa[- ]?milega|"
    # generic finance + timeframe ("agle X mahine paisa kaisa", "next 6 months
    # finance kaisa", "mere paise kaise rahenge", etc.)
    r"paise?\s+kaise|paisa\s+kaisa|paise?\s+kaise\s+rahenge|"
    r"paisa\s+\w*\s+aayega|paise?\s+\w*\s+aayenge|"
    r"agle\s+\d*\s*(?:mahine|month|months|saal|year)\s+\w*\s*(?:paisa|paise|finance|dhan|kamai|income|earning)|"
    r"(?:paisa|paise|finance|dhan|kamai|income|earning)\s+\w*\s*agle\s+\d*\s*(?:mahine|month|months|saal|year)|"
    r"next\s+\d*\s*(?:month|months|year|years)\s+\w*\s*(?:finance|paisa|paise|wealth|money|earning|income)|"
    r"(?:finance|paisa|paise|wealth|money|earning|income)\s+\w*\s*next\s+\d*\s*(?:month|months|year|years)|"
    r"aane\s+wal[ae]\s+\d*\s*(?:mahine|month|months|saal|year)\s+\w*\s*(?:paisa|paise|finance|dhan|kamai|income|earning|wealth|money)|"
    r"agle\s+\d*\s*(?:mahine|month|months|saal|year).{0,40}(?:finance|paisa|paise|dhan|kamai|income|wealth|money)|"
    r"(?:finance|paisa|paise|dhan|kamai|income|wealth|money).{0,40}agle\s+\d*\s*(?:mahine|month|months|saal|year)|"
    r"aane\s+wal[ae].{0,40}(?:finance|paisa|paise|dhan|kamai|income|wealth|money)|"
    r"(?:finance|paisa|paise|dhan|kamai|income|wealth|money).{0,40}aane\s+wal[ae]|"
    # debt-recovery / outstanding payments — wider Hinglish coverage
    r"paisa[- ]?\w*[- ]?wapas|paisa\s+\w*\s+wapas|"
    r"paisa[- ]?\w*[- ]?milega|paisa\s+\w*\s+milega|"
    r"paisa\s+(?:kab\s+)?(?:wapas|recover|milega|return)|"
    r"diya[- ]?hua[- ]?paisa|diya[- ]?gaya[- ]?paisa|"
    r"udhaar[- ]?\w*[- ]?milega|udhaar\s+\w*\s+milega|"
    r"recover[- ]?(?:hoga|honga|hogi|kar|karna|krna)|"
    r"recovery[- ]?(?:kab|hoga|honga|window)|"
    r"outstanding[- ]?(?:payment|amount|balance|dues|due)?|"
    r"payment[- ]?\w*[- ]?clear|clear\s+\w*\s+payment|"
    r"pending[- ]?(?:payment|dues|amount)|"
    r"due[- ]?(?:clear|recover|payment)|bakaya[- ]?\w*[- ]?(?:clear|wasool|wapas)|"
    r"wasool[- ]?(?:hoga|honga|kab)|wasooli|"
    r"logo[- ]?se\s+\w*\s+paisa|logon[- ]?se\s+\w*\s+paisa|"
    # foreign income / NRI remittance (wealth-flavoured, not foreign-travel)
    r"foreign[- ]?income|nri[- ]?income|remittance|remittances|"
    r"dollar[- ]?income|forex[- ]?income|"
    # partnership finance
    r"partnership[- ]?finance|partnership[- ]?profit|partner[- ]?ka[- ]?paisa|"
    r"joint[- ]?venture|joint[- ]?ventures|jv[- ]?profit|jv[- ]?investment|"
    r"co[- ]?founder|co[- ]?promoter|saanjhedaari|sanjhedari|"
    r"partnership[- ]?(?:munafa|labh|gain)|"
    # generic investment / mutual-fund / SIP / FD vocabulary — these
    # OVERLAP with stock_engine vocabulary (which fires upstream first
    # via priority chain), so the wealth ENGINE will rarely fire on
    # them. They are added here so the downstream wealth POST-PROCESSOR
    # (CA cite + SEBI line + placeholder strip) still recognises these
    # as wealth-flavoured questions and injects the mandatory
    # SEBI-registered advisor disclaimer that stock_engine itself
    # does not emit.
    r"invest|investing|investment|investments|investor|investors|"
    r"mutual[- ]?fund|mutual[- ]?funds|"
    r"\bsip\b|\bsips\b|systematic[- ]?investment[- ]?plan|"
    r"\bfd\b|\bfds\b|fixed[- ]?deposit|fixed[- ]?deposits|"
    r"\bmf\b|\bmfs\b|"
    r"\bppf\b|\bnps\b|\bnsc\b|\bkvp\b|\belss\b|"
    r"insurance|policy[- ]?lena|life[- ]?insurance|term[- ]?insurance|"
    r"health[- ]?insurance|"
    r"recurring[- ]?deposit|\brd\b|\brds\b|"
    r"bond|bonds|debenture|debentures|"
    r"gold[- ]?investment|gold[- ]?bond|sovereign[- ]?gold|"
    r"crypto|bitcoin|ethereum|altcoin|cryptocurrency|"
    # explicit "kahan invest karu" / "paisa kahan lagaun" Hinglish forms
    r"paisa[- ]?lagao|paisa[- ]?lagana|paisa[- ]?lagaun|"
    r"paise[- ]?lagao|paise[- ]?lagana|paise[- ]?lagaun|"
    r"kahan[- ]?invest|kahan[- ]?lagaun|kaha[- ]?lagaun|"
    r"nivesh|nivesh[- ]?karna|"

    # dhana karaka / vimshottari finance phrasings
    r"dhana[- ]?karaka|dhan[- ]?karak|"
    r"financial[- ]?freedom|financial[- ]?stability|"
    r"financially[- ]?stable|paise[- ]?ki[- ]?tangi|tangi|"
    r"paise[- ]?ki[- ]?problem|paise[- ]?ki[- ]?dikkat|"
    # Savings / bachat / kharcha — Hinglish lifestyle-finance vocabulary.
    # Examples that previously slipped through:
    #   "pichle saal se paisa nahi bach pa raha"
    #   "savings kab build hogi"
    #   "kharcha control nahi ho raha"
    #   "fizool kharch ho jata hai"
    r"savings?|saving[- ]?(?:kab|kaise|build|grow)|"
    r"\bbachat\b|\bbachao\b|\bbachana\b|\bbachayi\b|\bbache(?:gi|ga|ge)?\b|"
    r"paise?\s+(?:nahi|nhi|nah[ie])\s+bach|"
    r"paise?\s+bach(?:[- ]?nahi|[- ]?paa|[- ]?na|na|ta|ti|te)?|"
    r"\bbach\s+pa(?:[- ]?raha|[- ]?rahi|[- ]?rha|[- ]?rhi)\b|"
    r"\bkharch[ae]?\b|\bkharcha\b|\bkharchey?\b|kharche?[- ]?(?:control|jyada|zyada|extra|fizool)|"
    r"\bexpense(?:s)?\b|expense[- ]?(?:control|management)|"
    r"fizool[- ]?(?:kharch|kharcha|kharche|paisa|paise)|"
    r"faaltu[- ]?(?:kharch|kharcha|kharche|paisa|paise)|"
    r"corpus|emergency[- ]?fund|retirement[- ]?fund|retirement[- ]?corpus|"
    r"budget|budgeting|monthly[- ]?budget"
    r")\b)"
    # Devanagari anchors
    r"|धन|धनयोग|दौलत|संपत्ति|सम्पत्ति|"
    r"लक्ष्मी|आय|कमाई|वेतन|तनख्वाह|बचत|"
    r"मुनाफ़ा|मुनाफा|लाभ|हानि|नुकसान|"
    r"क़र्ज़|कर्ज|कर्ज़ा|उधार|ईएमआई|किश्त|"
    r"मकान|ज़मीन|जमीन|प्रॉपर्टी|"
    r"विरासत|पैतृक|"
    r"लॉटरी|जैकपॉट|अचानक धन",
    __import__("re").IGNORECASE,
)


def _is_wealth_question(text: str) -> bool:
    """True iff text matches wealth trigger AND no higher-priority engine
    (marriage / stock / love / career / health) has already claimed this
    turn. Higher-priority gates are applied UPSTREAM in `_build_messages`,
    so by the time we reach the wealth block we only need to confirm the
    text genuinely smells wealth/finance-related.
    Note: stock-market vocabulary (share/equity/SIP/intraday/F&O/nifty)
    is intentionally EXCLUDED from this gate — those belong to
    stock_engine which fires earlier in the priority chain."""
    if not isinstance(text, str) or not text.strip():
        return False
    return bool(_WEALTH_QUESTION_RX.search(text))


class WealthStructuredError(RuntimeError):
    """Raised when the wealth structured-output path fails after retries.
    Distinguished from generic OpenAI failures so /api/ask can return a
    typed 503 instead of silently falling back to the rule-engine
    (which would emit free-text and violate the no-fallback contract)."""


# ─────────────────────────────────────────────────────────────────────────────
# WEALTH STRUCTURED OUTPUT — JSON-schema mode (UX transformation)
# ─────────────────────────────────────────────────────────────────────────────
# Replaces the verbose narrator prose with strict JSON via OpenAI
# response_format=json_schema (strict=True). Mobile UI gets a scannable
# verdict card; legacy `text` field is populated by a deterministic
# JSON→Hinglish formatter for backward-compat.
# - temperature=0.0 (mirror marriage path)
# - max 2 retries on parse / validation failure
# - NO free-text fallback (per spec)
# - Engine logic UNTOUCHED — this is purely the AI output layer.
_WEALTH_VERDICT_TAG_MAP = {
    "green_go":     "🟢 GO",
    "yellow_wait":  "🟡 WAIT",
    "slow_burn":    "🟠 SLOW",
    "red_avoid":    "🔴 CAUTION",
}

_WEALTH_STRUCTURED_JSON_SCHEMA: dict = {
    "name": "wealth_structured_verdict",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["verdict", "empathy_open", "headline",
                     "recovery_outlook", "timeline",
                     "what_will_happen", "what_to_do",
                     "what_to_avoid", "remedy", "human_close", "note"],
        "properties": {
            "verdict": {
                "type": "object",
                "additionalProperties": False,
                "required": ["tag", "score", "confidence"],
                "properties": {
                    "tag": {
                        "type": "string",
                        "enum": ["🟢 GO", "🟡 WAIT", "🟠 SLOW", "🔴 CAUTION"],
                    },
                    "score":      {"type": "integer", "minimum": 0, "maximum": 100},
                    "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                },
            },
            "empathy_open": {
                "type": "string",
                "description": (
                    "Single-sentence Hinglish opener that ACKNOWLEDGES the user's "
                    "specific emotional concern from the question. ≤25 words. "
                    "MUST follow the EMOTIONAL TREATMENT DIRECTIVE's `OPENING LINE` "
                    "rule below — match the detected tone (anxious / hopeful / "
                    "grieving / etc.). NO banned cliché phrases."
                ),
            },
            "headline": {
                "type": "string",
                "description": "Hinglish summary, decision-oriented, ≤15 words.",
            },
            "recovery_outlook": {
                "type": "string",
                "description": (
                    "Sprint-26 Fix-Q. Single-line Hinglish recovery insight. "
                    "MUST be a non-empty string when the user's question "
                    "explicitly asks about RECOVERY (recover / wapas / "
                    "milega / vasool / loss-cover) — populate ONLY in that "
                    "case. Format: '<label>: <1-line reason from locked "
                    "facts>'. Allowed labels: PARTIAL, FULL, SLOW, UNLIKELY. "
                    "≤25 words. Use the locked timing window + verdict score "
                    "+ top cosmic factors as evidence — do NOT promise a "
                    "rupee amount, do NOT predict bankruptcy. When the "
                    "question has NO recovery sub-ask, emit empty string. "
                    "Example: 'PARTIAL: Jupiter–Saturn period (Jun 2026 "
                    "onwards) mein gradual recovery dikh raha hai, full "
                    "vapsi 2-3 cycles le sakti hai.'"
                ),
            },
            "timeline": {
                "type": "object",
                "additionalProperties": False,
                "required": ["current", "next"],
                "properties": {
                    "current": {"type": "string"},
                    "next":    {"type": "string"},
                },
            },
            "what_will_happen": {
                "type": "array",
                "items": {"type": "string"},
            },
            "what_to_do": {
                "type": "array",
                "items": {"type": "string"},
            },
            "what_to_avoid": {
                "type": "array",
                "items": {"type": "string"},
            },
            "remedy": {"type": "string"},
            "human_close": {
                "type": "string",
                "description": (
                    "Single-sentence Hinglish closer that REFRAMES the situation "
                    "(phase, not sentence; discipline, not saza; signal, not "
                    "strategy — depending on detected tone) and offers QUIET "
                    "agency / hope. ≤25 words. MUST follow the EMOTIONAL "
                    "TREATMENT DIRECTIVE's `CLOSING LINE` rule below. NO banned "
                    "cliché phrases. This is SEPARATE from the advisor `note`."
                ),
            },
            "note":   {
                "type": "string",
                "description": (
                    "MUST mention CA / SEBI-registered financial advisor "
                    "consult in Hinglish (≤ 20 words). This is a strict "
                    "brand-safety contract — do not omit."
                ),
            },
        },
    },
}


def _ym_human_w(ym: str) -> str:
    """'2025-07' → 'Jul 2025'. Empty/invalid → ''."""
    try:
        if not ym:
            return ""
        parts = ym.split("-")
        if len(parts) < 2:
            return ""
        y, m = parts[0], parts[1]
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return f"{months[int(m) - 1]} {y}"
    except Exception:
        return ""


def _build_wealth_structured_system_prompt(verdict_obj: dict,
                                           emotional_tone: str = "neutral",
                                           intent_domain: str = "wealth",
                                           ask_types: list | None = None,
                                           narrator_lang: str = "hn",
                                           has_recovery_subask: bool = False) -> str:
    """Compact narrator-locked prompt for wealth structured-output mode.
    Replaces the 100+ line verbose WEALTH NARRATOR OVERRIDE with a focused
    facts-only prompt that fits in ~40 lines and demands strict JSON.

    Phase 2 (Apr 2026): now also injects the EMOTIONAL TREATMENT DIRECTIVE
    derived from `(emotional_tone × intent_domain)` so the LLM populates
    `empathy_open` and `human_close` in the right human voice for the user's
    current mood — anxious vs hopeful vs grieving etc.
    """
    bucket  = verdict_obj.get("bucket", "general_wealth")
    tense   = verdict_obj.get("tense", "general")
    verdict = verdict_obj.get("verdict", "yellow_wait")
    score   = verdict_obj.get("score", 0)
    conf    = verdict_obj.get("confidence", 0)
    tag     = _WEALTH_VERDICT_TAG_MAP.get(verdict, "🟡 WAIT")

    # Top 3 reasons — prefer ⭐ MANDATORY layer signals
    reasons = verdict_obj.get("reasons") or []
    top = [r for r in reasons if "⭐" in r or "MANDATORY" in r
           or "Vargottama" in r or "Parivartana" in r
           or "Vipareeta" in r or "Dhana Yoga" in r or "Lakshmi" in r][:3]
    if not top:
        top = reasons[:3]

    # Window strings (server-side formatted so AI just copies)
    tw  = verdict_obj.get("timing_window") or {}
    cur = tw.get("current") or {}
    nxt = tw.get("next") or {}
    cur_label = ""
    if cur.get("start") and cur.get("end"):
        s = _ym_human_w(str(cur.get("start"))[:7])
        e = _ym_human_w(str(cur.get("end"))[:7])
        if s and e:
            cur_label = f"{s} – {e} ({cur.get('md')}–{cur.get('ad')})"
    nxt_label = ""
    if nxt.get("start") and nxt.get("end"):
        s = _ym_human_w(str(nxt.get("start"))[:7])
        e = _ym_human_w(str(nxt.get("end"))[:7])
        if s and e:
            nxt_label = f"{s} – {e} ({nxt.get('md')}–{nxt.get('ad')})"

    strategy = (verdict_obj.get("strategy") or "").strip()
    rem_obj  = verdict_obj.get("remedy") or {}
    rem      = (rem_obj.get("remedy_text") or "").strip() if isinstance(rem_obj, dict) else ""

    bucket_hint = {
        "investment_return":   "investments market risk; SEBI-registered advisor mandatory.",
        "business_profit":     "business cycles ke risk acknowledge karein.",
        "sudden_windfall":     "NEVER endorse lottery/satta — frame as bonus/arrears only.",
        "loan_clearance":      "EMI continue + bank ke saath transparent communication.",
        "property_purchase":   "RERA-registered + legal title + CA-vetted budget.",
        "inheritance_timing":  "empathy, NEVER predict elder's death, NEVER promise amount.",
        "partnership_finance": "written agreement + CA + legal advisor.",
        "salary_growth":       "salary band relative — never promise specific % or package.",
        "debt_recovery":       "patience + legal/CA channel for recovery.",
        "savings_capacity":    "discipline + auto-debit SIP/RD; no get-rich claim.",
        "foreign_income":      "FEMA + DTAA compliance + remittance via legal channel.",
        "general_wealth":      "general financial discipline + advisor consult.",
    }.get(bucket, "general financial discipline + advisor consult.")

    parts = []
    parts.append(
        "You are the Cosmic Intelligence narrator. Output STRICT JSON ONLY "
        "matching the provided schema. NO prose, NO markdown, NO commentary "
        "outside the JSON object."
    )
    parts.append("")
    parts.append("════ LOCKED FACTS (use VERBATIM, no invention) ════")
    parts.append(f"Bucket:         {bucket}")
    parts.append(f"Question tense: {tense}")
    parts.append(f"Verdict tag:    {tag}")
    parts.append(f"Score:          {score}")
    parts.append(f"Confidence:     {conf}")
    parts.append(f"Current window: {cur_label or '(engine silent — emit empty string)'}")
    parts.append(f"Next window:    {nxt_label or '(engine silent — emit empty string)'}")
    parts.append("Top cosmic factors:")
    for r in top:
        parts.append(f"   • {r}")
    if strategy:
        parts.append(f"Strategy: {strategy}")
    if rem:
        parts.append(f"Remedy:   {rem}")
    parts.append(f"Bucket-specific safety: {bucket_hint}")
    parts.append("")
    parts.append("════ OUTPUT RULES ════")
    parts.append(
        "1. `verdict.tag` MUST equal the locked tag above. "
        "`verdict.score` and `verdict.confidence` MUST equal the locked "
        "numbers above (integer, no rounding)."
    )
    parts.append(
        "2. `headline` ≤ 15 words, Hinglish, decision-oriented (no Sanskrit "
        "jargon dump). Tense framing — PRESENT: 'abhi …', FUTURE: 'aane "
        "wale time mein …', PAST: retrospective."
    )
    parts.append(
        "2a. `empathy_open` ≤ 25 words, single sentence. MUST acknowledge "
        "the user's specific concern (echo a noun/situation from the "
        "question, not a paraphrase of the verdict). Follow the OPENING "
        "LINE rule from the EMOTIONAL TREATMENT DIRECTIVE below."
    )
    parts.append(
        "2b. `human_close` ≤ 25 words, single sentence. MUST be SEPARATE "
        "from `note` (which is the advisor disclaimer). MUST follow the "
        "CLOSING LINE rule from the EMOTIONAL TREATMENT DIRECTIVE below — "
        "reframe / agency / quiet hope, depending on tone. NO 'sab theek "
        "ho jaayega', NO 'tension mat lo'."
    )
    parts.append(
        "3. `timeline.current` and `timeline.next` MUST equal the locked "
        "window strings above (or empty string if engine was silent). "
        "NO date invention."
    )
    parts.append(
        "4. `what_will_happen` 1–3 bullets, each ≤ 10 words, derived from "
        "the top cosmic factors above (paraphrased to plain Hinglish)."
    )
    parts.append(
        "5. `what_to_do` 1–3 bullets, each ≤ 10 words, actionable Hinglish."
    )
    parts.append(
        "6. `what_to_avoid` 1–3 bullets, each ≤ 10 words."
    )
    parts.append(
        "7. `remedy` ≤ 20 words, copy from locked Remedy if present, else "
        "'Thursday ko Jupiter mantra (108×) karein'."
    )
    parts.append(
        "8. `note` MUST mention CA / SEBI-registered financial advisor "
        "consult in Hinglish (≤ 20 words)."
    )
    # Sprint-26 Fix-Q — Recovery sub-ask handling. The user's question carried
    # an explicit RECOVERY ask (e.g. "paisa recover hoga ya nahi") in addition
    # to the primary decision/problem ask. The schema's `recovery_outlook`
    # field MUST be populated with a labelled 1-line insight; otherwise the
    # secondary intent gets dropped from the answer.
    if has_recovery_subask:
        parts.append(
            "9. RECOVERY SUB-ASK DETECTED. `recovery_outlook` MUST be a "
            "non-empty single-line Hinglish string in the format "
            "'<LABEL>: <reason>'. Allowed labels: PARTIAL, FULL, SLOW, "
            "UNLIKELY. Pick the label by reading the LOCKED FACTS — the "
            "verdict tag, score (0-100), confidence, and timing window are "
            "your evidence. Mapping guide: 🟢 GO + score≥70 → FULL or "
            "PARTIAL; 🟡 WAIT + score 40-69 → PARTIAL or SLOW; 🟠 SLOW → "
            "SLOW; 🔴 CAUTION + score<40 → UNLIKELY or SLOW. Reason MUST "
            "cite the next-better window (or current window's exit point) "
            "from the locked timing strings — NO date invention, NO rupee "
            "amounts, NO bankruptcy prediction. ≤25 words total."
        )
    else:
        parts.append(
            "9. NO RECOVERY SUB-ASK. `recovery_outlook` MUST be the empty "
            "string \"\"."
        )
    parts.append("")
    parts.append("════ ABSOLUTE PROHIBITIONS ════")
    parts.append("• NEVER predict specific rupee amounts (lakh / crore / package).")
    parts.append("• NEVER predict bankruptcy / kangaal / barbaad — soften to 'extra-savitree phase'.")
    parts.append("• NEVER advise loan-default / EMI-skip / tax-evasion / GST-fraud.")
    parts.append("• NEVER endorse lottery / satta / matka / KBC / jackpot.")
    parts.append("• NEVER reveal AI / LLM / GPT — brand voice is 'Powered by Advanced Cosmic Intelligence'.")
    parts.append("• NEVER invent dates not present in the locked window strings.")
    # ── EMOTIONAL TREATMENT DIRECTIVE — Phase 2 (cross-engine playbook) ──
    try:
        from treatment_playbook import (
            build_treatment_directive,
            canonical_tone,
            canonical_domain,
        )
        parts.append("")
        parts.append(build_treatment_directive(
            tone      = canonical_tone(emotional_tone),
            domain    = canonical_domain(intent_domain) or "wealth",
            ask_types = ask_types or [],
            lang      = narrator_lang or "hn",
        ))
    except Exception as exc:
        # Don't silently strip the directive — log loudly + use a minimal
        # built-in fallback so empathy_open / human_close still get
        # SOMETHING to anchor against (instead of free-form clichés).
        import traceback as _tb_mod
        print(f"[treatment_playbook] LOAD FAILED: {exc!r} — using fallback")
        print(_tb_mod.format_exc())
        parts.append("")
        parts.append("════ EMOTIONAL TREATMENT (minimal fallback) ════")
        parts.append("• empathy_open: ONE line acknowledging the user's "
                     "specific situation in their words. NO clichés "
                     "(no 'main samajh sakta hoon', no 'tension mat lo', "
                     "no 'sab theek ho jaayega', no 'Beta,').")
        parts.append("• human_close: ONE line reframing the engine facts "
                     "into a concrete next step or perspective shift. "
                     "Do NOT repeat the advisor cite from `note`.")
        parts.append("• Both fields ≤ 25 words. Single sentence each.")
    return "\n".join(parts)


def _format_wealth_structured_payload(payload: dict) -> str:
    """Deterministic JSON → short Hinglish text formatter. Populates the
    legacy `text` field for backward-compat with the current chat bubble
    while the new `structured` field carries the raw JSON for richer
    rendering when the mobile UI is upgraded."""
    if not isinstance(payload, dict):
        return ""
    v        = payload.get("verdict") or {}
    tag      = v.get("tag", "")
    score    = v.get("score", "")
    conf     = v.get("confidence", "")
    empathy_open = (payload.get("empathy_open") or "").strip()
    headline = (payload.get("headline") or "").strip()
    recovery_outlook = (payload.get("recovery_outlook") or "").strip()
    tl       = payload.get("timeline") or {}
    cur      = (tl.get("current") or "").strip()
    nxt      = (tl.get("next")    or "").strip()
    will     = payload.get("what_will_happen") or []
    do       = payload.get("what_to_do")        or []
    avoid    = payload.get("what_to_avoid")     or []
    remedy   = (payload.get("remedy") or "").strip()
    human_close = (payload.get("human_close") or "").strip()
    note     = (payload.get("note")   or "").strip()

    lines: list[str] = []
    head = tag
    if score != "":
        head += f"  •  Score {score}/100"
    if conf != "":
        head += f"  •  Confidence {conf}%"
    lines.append(head)
    # Phase 2: empathy_open line (italic in markdown clients)
    if empathy_open:
        lines.append("")
        lines.append(empathy_open)
    if headline:
        lines.append("")
        lines.append(headline)
    # Sprint-26 Fix-Q — Recovery line renders BEFORE the timing window so the
    # output reads Verdict → Recovery → Timing (the user's required structure
    # for decision-plus-recovery questions). When the question had no
    # recovery sub-ask, the field is empty string and we skip silently.
    if recovery_outlook:
        lines.append("")
        lines.append(f"💰 Recovery: {recovery_outlook}")
    if cur or nxt:
        lines.append("")
        if cur:
            lines.append(f"📅 Window: {cur}")
        if nxt:
            lines.append(f"   ➜ Better: {nxt}")
    if will:
        lines.append("")
        lines.append("Kya hoga:")
        for x in will[:3]:
            lines.append(f"  • {x}")
    if do:
        lines.append("")
        lines.append("Kya karein:")
        for x in do[:3]:
            lines.append(f"  • {x}")
    if avoid:
        lines.append("")
        lines.append("Kya na karein:")
        for x in avoid[:3]:
            lines.append(f"  • {x}")
    if remedy:
        lines.append("")
        lines.append(f"🕉  Upay: {remedy}")
    # Phase 2: human_close line BEFORE the advisor disclaimer
    if human_close:
        lines.append("")
        lines.append(human_close)
    if note:
        lines.append("")
        lines.append(f"ℹ  {note}")
    return "\n".join(lines).strip()


def _validate_wealth_payload(payload: dict,
                             locked: dict,
                             *,
                             has_recovery_subask: bool = False
                             ) -> tuple[bool, str]:
    """Strict sanity check. Returns (ok, reason). Used by the retry loop
    to reject drift even when OpenAI's strict json_schema accepts the
    response as schema-valid.

    Sprint-26 Fix-Q (post-architect-review): added optional
    `has_recovery_subask` keyword to enforce deterministic Recovery
    semantics — when the user asked about recovery the field MUST be
    populated with a labelled one-liner; when they did NOT, the field
    MUST be empty so an LLM hallucination cannot inject a Recovery
    line into a question that did not request it.
    """
    import re as _re_w
    if not isinstance(payload, dict):
        return False, "not a dict"
    v = payload.get("verdict")
    if not isinstance(v, dict):
        return False, "verdict object missing"
    locked_tag = _WEALTH_VERDICT_TAG_MAP.get(
        locked.get("verdict", ""), "🟡 WAIT")
    if v.get("tag") != locked_tag:
        return False, f"verdict.tag drift (got {v.get('tag')!r}, expected {locked_tag!r})"
    try:
        if int(v.get("score", -1)) != int(locked.get("score", 0)):
            return False, "verdict.score drift"
        if int(v.get("confidence", -1)) != int(locked.get("confidence", 0)):
            return False, "verdict.confidence drift"
    except (TypeError, ValueError):
        return False, "verdict score/confidence non-integer"
    headline = payload.get("headline")
    if not isinstance(headline, str) or not headline.strip():
        return False, "headline empty"
    if len(headline.split()) > 15:
        return False, f"headline too long ({len(headline.split())} words; strict limit 15)"
    # ── Phase 2: empathy_open + human_close validation ─────────────────────
    # If the playbook can't be imported we DO NOT silently allow clichés
    # through — fall back to a small inline ban list instead.
    try:
        from treatment_playbook import is_banned_empathy as _is_banned
    except Exception as _exc:
        print(f"[treatment_playbook] VALIDATOR LOAD FAILED: {_exc!r} — using inline ban list")
        _INLINE_BAN = (
            "main samajh sakta hoon", "i understand your pain",
            "tension mat lo", "tension mat lijiye", "chinta mat karo",
            "sab theek ho jaayega", "sab acha hoga", "sab achha hoga",
            "as an ai", "as a language model", "beta,", "beta ,",
            "khush rahein", "positive raho", "be positive",
        )
        def _is_banned(t: str) -> tuple[bool, str]:
            tl = (t or "").lower()
            for ph in _INLINE_BAN:
                if ph in tl:
                    return True, ph
            return False, ""
    # Single-sentence enforcement — empathy_open + human_close are each
    # supposed to be ONE punchy line, never a paragraph.
    _SENT_END_RX = _re_w.compile(r"[.!?।]")
    for empathy_field, label, max_words in (
        ("empathy_open", "empathy_open", 28),   # +3 words slack over schema 25
        ("human_close",  "human_close",  28),
    ):
        val = payload.get(empathy_field)
        if not isinstance(val, str) or not val.strip():
            return False, f"{label} empty"
        wc = len(val.split())
        if wc > max_words:
            return False, f"{label} too long ({wc} words; soft limit {max_words})"
        # Count terminating punctuation; allow exactly one (or zero if no end mark).
        end_marks = len(_SENT_END_RX.findall(val.rstrip()))
        if end_marks > 1:
            return False, f"{label} must be a single sentence (found {end_marks} sentence-end marks)"
        banned, phrase = _is_banned(val)
        if banned:
            return False, f"{label} contains banned cliché: {phrase!r}"
    # human_close MUST NOT just repeat the advisor cite — they're separate
    hc_low = (payload.get("human_close") or "").lower()
    if _re_w.search(
            r"\b(CA|chartered\s+accountant|SEBI[- ]registered|"
            r"financial\s+advisor|financial\s+planner|tax\s+consultant)\b",
            hc_low, _re_w.IGNORECASE):
        return False, "human_close should NOT contain advisor cite (note field handles that)"
    for k in ("what_will_happen", "what_to_do", "what_to_avoid"):
        arr = payload.get(k) or []
        if not isinstance(arr, list) or not arr:
            return False, f"{k} empty"
        if len(arr) > 3:
            return False, f"{k} > 3 bullets"
        for b in arr:
            if not isinstance(b, str):
                return False, f"{k} non-string bullet"
            if len(b.split()) > 10:
                return False, f"{k} bullet > 10 words ({len(b.split())})"
    note_str = payload.get("note") or ""
    if not isinstance(note_str, str) or not note_str.strip():
        return False, "note empty"
    if not _re_w.search(
            r"\b(CA|chartered\s+accountant|"
            r"SEBI[- ]registered|"
            r"financial\s+advisor|financial\s+planner|"
            r"tax\s+consultant|"
            r"vittiy[a-z]*\s+salahkar)\b",
            note_str, _re_w.IGNORECASE):
        return False, "note missing CA / SEBI-registered advisor cite"
    blob = " ".join([
        (payload.get("empathy_open") or ""),   # Phase 2: also scan empathy
        (payload.get("headline") or ""),
        " ".join(payload.get("what_will_happen") or []),
        " ".join(payload.get("what_to_do") or []),
        " ".join(payload.get("what_to_avoid") or []),
        (payload.get("remedy") or ""),
        (payload.get("human_close") or ""),    # Phase 2: also scan close
        (payload.get("note") or ""),
    ]).lower()
    if _re_w.search(r"\b\d+\s*(?:lakh|crore|cr|lac)\b", blob):
        return False, "specific rupee amount leaked"
    if _re_w.search(
            r"\b(kangaal|barbaad|bankruptcy|lottery|satta|matka|jackpot|kbc)\b",
            blob):
        return False, "prohibited brand-safety word leaked"
    if _re_w.search(r"\b(llm|gpt|chatgpt|openai|chatbot)\b", blob):
        return False, "AI/LLM mention leaked"
    # ── Sprint-26 Fix-Q (post-architect-review) — recovery_outlook gate ──
    # Deterministic post-validation closes the LLM drift hole that the
    # strict-json-schema layer cannot enforce on its own:
    #   • when has_recovery_subask=True  → field MUST be non-empty AND
    #     must lead with one of the four prescribed labels;
    #   • when has_recovery_subask=False → field MUST be empty so the
    #     model cannot hallucinate a Recovery line into a question that
    #     did not ask for one.
    # The retry loop in the caller will regenerate the response when
    # this returns False.
    recovery_raw = (payload.get("recovery_outlook") or "")
    recovery_str = recovery_raw.strip() if isinstance(recovery_raw, str) else ""
    if has_recovery_subask:
        if not recovery_str:
            return False, "recovery_outlook empty but recovery sub-ask present"
        if not _re_w.match(
                r"^(PARTIAL|FULL|SLOW|UNLIKELY)\s*[:\-]",
                recovery_str, _re_w.IGNORECASE):
            return False, (
                "recovery_outlook must start with one of "
                "PARTIAL|FULL|SLOW|UNLIKELY label, got "
                f"{recovery_str[:30]!r}")
        if len(recovery_str.split()) > 30:
            return False, (
                f"recovery_outlook too long "
                f"({len(recovery_str.split())} words; soft limit 30)")
        # Re-scan the recovery line for the same brand-safety bans we
        # apply to other fields (rupee amounts + bankruptcy vocab).
        rec_low = recovery_str.lower()
        if _re_w.search(r"\b\d+\s*(?:lakh|crore|cr|lac)\b", rec_low):
            return False, "recovery_outlook leaked specific rupee amount"
        if _re_w.search(
                r"\b(kangaal|barbaad|bankruptcy|lottery|satta|matka|jackpot|kbc)\b",
                rec_low):
            return False, "recovery_outlook leaked prohibited brand-safety word"
    else:
        if recovery_str:
            return False, (
                "recovery_outlook populated but no recovery sub-ask in "
                "question — drop the field to prevent hallucinated "
                "Recovery line")
    return True, "ok"


# Lazy client so import does not crash if the SDK is missing in dev.
_client = None
_client_err: str | None = None


def _get_client():
    global _client, _client_err
    if _client is not None or _client_err is not None:
        return _client
    # Prefer the Replit AI Integrations proxy when provisioned — no user
    # API key / billing required, charges go to Replit credits. Fall back
    # to a user-supplied OPENAI_API_KEY if the proxy is not configured.
    proxy_base = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "").strip()
    proxy_key  = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "").strip()
    user_key   = os.environ.get("OPENAI_API_KEY", "").strip()
    if proxy_base and proxy_key:
        api_key  = proxy_key
        base_url = proxy_base
        source   = "replit-proxy"
    elif user_key:
        api_key  = user_key
        base_url = None
        source   = "user-key"
    else:
        _client_err = "OPENAI_API_KEY / AI_INTEGRATIONS_OPENAI_BASE_URL missing"
        return None
    try:
        from openai import OpenAI
        timeout = float(os.environ.get("OPENAI_TIMEOUT", "30"))
        kwargs = {"api_key": api_key, "timeout": timeout}
        if base_url:
            kwargs["base_url"] = base_url
        _client = OpenAI(**kwargs)
        try:
            print(f"[openai_helper] OpenAI client initialised via {source}",
                  flush=True)
        except Exception:
            pass
        return _client
    except Exception as exc:
        _client_err = f"OpenAI SDK init failed: {exc}"
        return None


def is_available() -> bool:
    return _get_client() is not None


# ── Prompt building ───────────────────────────────────────────────────────────

_LANG_NAME = {
    "en": "English", "hi": "Hindi (Devanagari)", "hn": "Hinglish (Hindi in Roman script)",
    "ta": "Tamil", "te": "Telugu", "bn": "Bengali", "mr": "Marathi", "gu": "Gujarati",
    "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi (Gurmukhi)", "or": "Odia",
    "as": "Assamese", "ur": "Urdu", "ne": "Nepali", "sa": "Sanskrit",
    "es": "Spanish", "fr": "French", "de": "German", "pt": "Portuguese",
    "ru": "Russian", "ja": "Japanese", "zh": "Chinese (Simplified)", "ar": "Arabic",
}


def _kundli_summary(kundli: Any, birth: Any = None) -> str:
    """Compress the kundli dict into a rich string the model can reason over."""
    parts: list[str] = []

    # Birth context (from birthData fallback even if kundli is missing fields)
    if isinstance(birth, dict):
        dob = birth.get("dob") or birth.get("date")
        tm  = birth.get("time")
        pl  = birth.get("place") or birth.get("placeName") or birth.get("city")
        gen = birth.get("gender")
        nm  = birth.get("name")
        bits = []
        if nm:  bits.append(f"Name: {nm}")
        if dob: bits.append(f"DOB: {dob}")
        if tm:  bits.append(f"Time: {tm}")
        if pl:  bits.append(f"Place: {pl}")
        if gen: bits.append(f"Gender: {gen}")
        if bits:
            parts.append("Birth: " + ", ".join(bits))

    if not isinstance(kundli, dict):
        return " | ".join(parts) if parts else "(no birth chart provided)"

    asc = kundli.get("ascendant") or kundli.get("lagna")
    if asc:
        deg = kundli.get("ascendantDeg")
        parts.append(f"Lagna: {asc}" + (f" {deg:.2f}°" if isinstance(deg, (int, float)) else ""))
    moon_sign = kundli.get("moonSign") or kundli.get("moon_sign")
    if moon_sign:
        parts.append(f"Moon sign (Rashi): {moon_sign}")
    sun_sign = kundli.get("sunSign")
    if sun_sign:
        parts.append(f"Sun sign: {sun_sign}")
    nak = kundli.get("nakshatra")
    if nak:
        pada = kundli.get("nakshatraPada")
        ruler = kundli.get("nakshatraRuler")
        nbits = nak + (f" pada-{pada}" if pada else "")
        if ruler:
            nbits += f" (lord: {ruler})"
        parts.append(f"Nakshatra: {nbits}")

    # Vimshottari Dasha — single most important field for timing predictions
    cd = kundli.get("currentDasha")
    if isinstance(cd, dict):
        maha   = cd.get("maha")
        antar  = cd.get("antar")
        ends   = cd.get("endDate")
        starts = cd.get("startDate")
        if maha or antar:
            line = "Current Dasha: "
            line += f"{maha or '?'} Mahadasha"
            if antar:
                line += f" / {antar} Antardasha"
            if starts and ends:
                line += f" ({starts} → {ends})"
            parts.append(line)
    db = kundli.get("dashaBalance")
    if isinstance(db, (int, float)) and db > 0:
        parts.append(f"Dasha balance at birth: {db:.2f} years")

    # Planets in houses + rashi + nakshatra + retrograde
    planets = kundli.get("planets")
    if isinstance(planets, list) and planets:
        plist = []
        for p in planets[:9]:
            if not isinstance(p, dict):
                continue
            name = p.get("name", "")
            sign = p.get("sign") or p.get("rashi") or ""
            house = p.get("house", "")
            nakp  = p.get("nakshatra")
            retro = " (R)" if p.get("retrograde") else ""
            chunk = f"{name} in {sign} H{house}{retro}"
            if nakp:
                chunk += f" [nak {nakp}]"
            plist.append(chunk)
        if plist:
            parts.append("Planets: " + "; ".join(plist))

    return " | ".join(parts) if parts else "(birth chart provided but empty)"


# ── Topic-specific KP/Parashari focus block ──────────────────────────────────

_TOPIC_FOCUS = {
    "marriage": (
        "FOCUS — vivah/marriage: 99% accuracy mandatory. Follow this PRIORITIZED LOGIC strictly, in order.\n"
        "\n"
        "PRIORITIZED LOGIC STEPS (apply in this exact order, then synthesize):\n"
        "\n"
        "1) DENIAL CHECK (KP) — FIRST: Look at the 7th cusp Sub-Lord in the KP block above. "
        "   If it signifies ONLY houses 1, 6, 10 (and NOT 2, 7, or 11) → marriage faces significant DENIAL or long delays. "
        "   Say so plainly. If it signifies 2/7/11 (any of them, in PL/NL/SB) → marriage is PROMISED, proceed.\n"
        "\n"
        "2) TIMING (Vimshottari Dasha): Marriage can ONLY happen during the Mahadasha/Antardasha of planets that "
        "   signify houses 2, 7, or 11. Check the current DBA against the 'Planetary significators' table. "
        "   If the current dasha lord IS a 2/7/11 significator → window is open NOW. "
        "   If NOT, scan the upcoming Antardashas and name the next favourable one.\n"
        "\n"
        "3) TRIGGER (Live Transits): A confident 'Clear Verdict with timing' is only valid if Jupiter is currently "
        "   transiting OR aspecting the natal 1st, 5th, or 7th house/lord (from Lagna AND Moon). "
        "   No Jupiter trigger → say timing is approximate, expect a 1-2 year shift.\n"
        "\n"
        "4) DELAY FACTORS: If Saturn aspects/occupies the 7th house OR 7th lord, OR if 'Mangal-dosh' is flagged "
        "   in the intelligence block, OR if user is in 'Sade-Sati' → ADD 1.5 to 2 years to the predicted timeline. "
        "   Marriage usually after age 28 in such charts. Mention this delay openly, not as bad news.\n"
        "\n"
        "5) DOSHA CHECK: If 'Mangal-dosh present' is in the intelligence block, check if any cancellation is also listed "
        "   (Mars in own/exalt sign, aspected by Jupiter, Moon in kendra giving neech-bhanga, etc). "
        "   State clearly: 'dosh hai par cancel ho raha hai' OR 'dosh active hai, isliye delay'.\n"
        "\n"
        "SUPPORTING REFERENCES (cite naturally only when relevant):\n"
        "• 7th house & lord = kalatra-bhava (BPHS Ch.80). Venus = kalatra-karaka for men, Jupiter = pati-karaka for women.\n"
        "• 2nd (kutumb), 4th (domestic sukh), 8th (mangalya/bond longevity), 11th (desire fulfillment) — supporting houses.\n"
        "• Vivah-yogas: 7L+Venus together, 2L+7L+11L combo, Lagna-lord aspecting 7H. Denial-yogas: 7L combust, Venus debilitated without neech-bhanga.\n"
        "• Classics: Phaladeepika Ch.10, Saravali Ch.36, Jataka Parijata Ch.13, KP Reader Vol.VI, Prashna Marga Ch.18.\n"
        "\n"
        "MARRIAGE-SPECIFIC RESPONSE FORMAT (overrides default — strictly 3 paragraphs, 100-140 words, Hinglish):\n"
        "• Para 1 (Empathy + Base, 1-2 sentences): Start with 'Pranam'. Acknowledge their concern. Mention strongest 7th-house factor "
        "  using the format: 'Aapka Saptamesh (7th Lord) [Planet] [House] mein baitha hai...'.\n"
        "• Para 2 (Technical Evidence, 2 sentences): Explain KP connection or Dasha logic in plain words. Use 'KP chart ke anusar...' "
        "  or 'Dasha ka prabhav...'. Mention the denial/promise verdict from step 1, current dasha lord from step 2, "
        "  and any delay factor from step 4.\n"
        "• Para 3 (Verdict + Remedy, 2 sentences): Give a tight YEAR-RANGE (e.g. '2026 ke madhya se 2027 ke shuruat tak'). "
        "  End with ONE specific remedy chosen for the 7th-lord placement (mantra+count+day OR donation).\n"
        "Tone: calm, professional, scholarly — Acharya ji style, not chatty.\n"
        "If essential data missing, politely ask user to complete profile — never invent."
    ),
    "career": (
        "FOCUS — career/job/business: Apply systematically:\n"
        "• 10th house & lord (karma-bhava) — strength, occupants, aspects.\n"
        "• Sun (raj-karaka — govt/authority), Saturn (karma-karaka — discipline/service), "
        "Mercury (vyapaar-karaka — commerce/communication), Mars (technical/military/sports/competition).\n"
        "• 6th (service, competition, debt-from-work), 2nd (income/savings), 11th (gains/promotion).\n"
        "• Amatya-karaka (2nd highest degree planet, Jaimini) shows profession nature.\n"
        "• Raja-yogas: kendra-trikona lord conjunction, exchange (parivartana), Vipareeta-Raja-yoga (6/8/12 lords mutual).\n"
        "• Current Dasha lord — if it rules/occupies 2/6/10/11 → growth phase. If it rules 8/12 → instability/transfer/loss.\n"
        "• Saturn transit over 10th house = career karma activation.\n"
        "• For business specifically: 7th house (partnerships), Mercury+Jupiter strength, Lakshmi-yoga.\n"
        "• Cite: BPHS Ch.34 (Karma-bhava), Phaladeepika Ch.6, Uttara Kalamrita."
    ),
    "finance": (
        "FOCUS — dhan/wealth: Apply ALL these:\n"
        "• 2nd house (sanchita-dhana — accumulated), 11th (labha — gains/income), 5th (purva-punya wealth/speculation), "
        "9th (bhagya-dhana — fortune-given).\n"
        "• Jupiter (dhana-karaka), Venus (bhog & luxury), Mercury (commerce/trading).\n"
        "• Dhana-yogas: 2L+11L conjunction/aspect, 5L+9L (Lakshmi-yoga), 9L+11L mutual, exchange between 2/5/9/11 lords.\n"
        "• Daridra-yogas (poverty): 2L or 11L in 6/8/12, Lagna-lord weak.\n"
        "• For loans/debt: 6th house, Saturn-Mars on 2/11.\n"
        "• For speculation/stocks/lottery: 5th house & lord, Jupiter-Mercury combo, but warn 8/12 affliction = loss.\n"
        "• Current Dasha lord ruling 2/5/9/11 = wealth period.\n"
        "• Cite: BPHS Ch.32 (Dhana-bhava), Saravali Ch.33."
    ),
    "health": (
        "FOCUS — swasthya: Apply ALL these:\n"
        "• Lagna & Lagna-lord (vital strength), Moon (mental/fluid), Sun (vitality/heart/eyes), Mars (blood/muscle/inflammation), "
        "Saturn (chronic/bones/joints/longevity), Rahu (mystery illness/poison), Ketu (sudden/surgery).\n"
        "• 6th (acute disease/infection), 8th (chronic/surgery/longevity), 12th (hospitalisation/sleep/loss).\n"
        "• Body-part assignment by sign: Mesh=head, Vrish=throat, Mithun=lungs/arms, Karka=chest, Simh=heart/spine, "
        "Kanya=intestine, Tula=kidney, Vrishchik=reproductive, Dhanu=hips/thighs, Makar=knees, Kumbh=calves, Meen=feet.\n"
        "• Affliction = malefic conjunction/aspect to Lagna or relevant house.\n"
        "• Current Dasha lord afflicting Lagna/6/8/12 = health-attention period.\n"
        "• MANDATORY: always say 'qualified doctor se zaroor consult karein — jyotish margdarshan deti hai, diagnosis nahi'.\n"
        "• Cite: BPHS Ch.41 (Aristha — disease yogas), Phaladeepika Ch.12, Maharishi Charaka."
    ),
    "child": (
        "FOCUS — santan/child:\n"
        "• 5th house & lord (putra-bhava), Jupiter (putra-karaka), 9th (santati continuation).\n"
        "• Saptamsha (D-7) conceptually for children.\n"
        "• Putra-dosh / Bhrigu-dosh patterns: 5th lord in 6/8/12, Rahu/Saturn in 5H, malefic aspect on 5L.\n"
        "• For conception delay: also check 2nd (kutumb), Moon-Jupiter relation.\n"
        "• Current Dasha-Antar of 5L, Jupiter, or 9L = conception window.\n"
        "• Always be COMPASSIONATE — couples asking this are emotionally vulnerable. Recommend medical consult parallel to remedies.\n"
        "• Cite: BPHS Ch.37 (Putra-bhava), Jataka Parijata Ch.10, Saravali Ch.30."
    ),
    "education": (
        "FOCUS — vidya/exam:\n"
        "• 4th (basic schooling/comfort), 5th (intellect/buddhi/competitive), 9th (higher/dharmic learning), 2nd (memory/speech).\n"
        "• Mercury (buddhi-karaka), Jupiter (vidya/wisdom/teacher), Sun (focus/willpower).\n"
        "• Saraswati-yoga: Mercury+Venus+Jupiter in kendra/trikona.\n"
        "• For exams specifically: current transit of Jupiter/Mercury over 5/9, Dasha-Antar of 4L/5L/9L/Mercury/Jupiter.\n"
        "• For competitive (UPSC/NEET/JEE etc.): also 6th (vijay over competition), 10th (selection/posting).\n"
        "• Combust Mercury or Mercury-Saturn = slow/struggle but eventual depth.\n"
        "• Cite: BPHS Ch.35, Phaladeepika Ch.6."
    ),
    "travel": (
        "FOCUS — yatra/foreign:\n"
        "• 3rd (short journeys/courage), 9th (long/dharmic/foreign), 12th (videsh-vaas — settlement abroad).\n"
        "• Rahu (foreign lands/unconventional), Moon (movement), Mercury (commerce travel).\n"
        "• Foreign settlement yog: 12L in good house, 9L+12L connection, Rahu in 9/12, Lagna-lord in 12.\n"
        "• Visa/passport stuck: 12L afflicted, Rahu-Saturn on 9/12.\n"
        "• Current Dasha lord ruling 3/9/12 = travel period.\n"
        "• Cite: BPHS Ch.39, Phaladeepika Ch.7."
    ),
    "relationship": (
        "FOCUS — pyaar/relationship (pre-marriage):\n"
        "• 5th house (romance/affair) & lord, 7th (committed bond), 11th (friend-circle/desire-fulfilment).\n"
        "• Venus (love-karaka for men), Mars (love-karaka for women).\n"
        "• Moon's nakshatra-lord & sign = emotional template.\n"
        "• Love-marriage yogas: 5L+7L conjunction/exchange, Venus+Mars conjunction, Rahu+Venus = unconventional union.\n"
        "• Breakup signals: 7L in 6/8/12, Saturn-Rahu on 5/7, current dasha of 6L or 8L.\n"
        "• Inter-caste/family-opposition: Rahu involvement with 7H/Venus.\n"
        "• Be empathetic — many devotees are heartbroken when they ask this."
    ),
    "litigation": (
        "FOCUS — court case/legal:\n"
        "• 6th (vijay over enemy/case), 8th (sudden reversal/chronic case), 12th (jail/exit), 11th (gain from case).\n"
        "• Mars (energy to fight), Saturn (delay/chronic), Mercury (paperwork/argument), Jupiter (judge/dharma).\n"
        "• 6L stronger than 7L = win; 7L stronger = opponent wins; 6L+7L equal = settlement.\n"
        "• Current Dasha lord — if ruling 6/11 = win-window; if ruling 7/8/12 = adverse.\n"
        "• Always advise consulting a qualified vakil — jyotish only shows trend, not legal advice.\n"
        "• Cite: BPHS Ch.36 (Shatru-bhava), Prashna Marga Ch.13."
    ),
    "property": (
        "FOCUS — property/ghar:\n"
        "• 4th house & lord (sukh-sthan — home/land/vehicle), Mars (real estate karaka), Venus (luxury/vehicle), Mercury (paperwork/registration).\n"
        "• Buying yog: 4L strong + dasha of 4L/Mars/Venus, Jupiter transit over 4H.\n"
        "• Disputes: 4L+8L involvement, Rahu in 4H = unclear title.\n"
        "• Selling: 4L in 3/12, weak 4L period.\n"
        "• Cite: BPHS Ch.31 (Sukha-bhava), Phaladeepika Ch.9."
    ),
    "vehicle": (
        "FOCUS — vahan: 4th house (vahan-sthan), Venus (vahan-karaka), Mars (engine/movement). "
        "Buying yog: 4L+Venus dasha, Jupiter transit on 4H. Accident risk: 8L on 4H, Mars-Saturn affliction. "
        "Cite: BPHS Ch.31."
    ),
    "vastu": (
        "FOCUS — vastu: refer to direction-element mapping (NE=water/Ishan, SE=fire/Agni, SW=earth/Nairutya, NW=air/Vayavya). "
        "Suggest specific room placements per Mayamatam/Manasara. For deeper scan recommend in-app Vastu Drishti or AstroVastu PRO."
    ),
    "remedy": (
        "FOCUS — upay: identify the SPECIFIC most-afflicted/weak planet causing the problem from the chart, then prescribe ONE classical remedy:\n"
        "• Mantra (Vedic moolmantra OR Beej-mantra), exact count (108 / 1008 / 11000 / 125000), specific day & hora.\n"
        "• Donation (daan) — what, to whom, which day (planet's day).\n"
        "• Fast (vrat) — which day, what to eat/avoid.\n"
        "• Gemstone — ONLY if dasha favours that planet AND the planet is functional benefic; else skip and suggest substitute.\n"
        "• Rudraksha mukhi for the planet, yantra, kavach.\n"
        "• Lal Kitab totka if pattern matches.\n"
        "• Cite source: BPHS Shanti-adhyay, Lal Kitab, Mantra Maharnava, regional Pandit-tradition."
    ),
    "spiritual": (
        "FOCUS — moksha/spiritual: 9th (dharma), 12th (moksha-sthan), Jupiter (guru/wisdom), Ketu (renunciation/jnana). "
        "Moksha-yogas: 12L in 9, Ketu in 12, Jupiter+Ketu, Saturn in 12 with Jupiter aspect. "
        "Suggest a sadhana matching the strongest of these planets. Cite: BPHS Ch.40, Brihat Jataka."
    ),
    "family": (
        "FOCUS — parivar: 4th (mother/home), 9th (father), 3rd (siblings), 11th (elder sibling), 5th (children). "
        "Affliction to these = family discord. Look at corresponding karakas: Moon (mother), Sun (father), Mars (siblings)."
    ),
    # ── UNIVERSAL fallback — any question that doesn't match a known topic ──
    "general": (
        "FOCUS — universal life-reading (use this when the question doesn't fit a single bhava). Apply systematically:\n"
        "\n"
        "A) FRAMING — first identify what the devotee is really asking:\n"
        "• Re-read the full question carefully. List EVERY distinct sub-question or concern in order.\n"
        "• Map each sub-question to the bhava(s) it touches (e.g. 'will I be happy and successful?' → 1H/5H/9H/10H/11H).\n"
        "• If the question is philosophical/karmic, lean on 5H (purva-punya), 9H (dharma), 12H (moksha), Jupiter & Ketu.\n"
        "• If the question is timing-based ('kab', 'when', 'how soon'), centre the answer on current Mahadasha+Antardasha.\n"
        "\n"
        "B) CORE CHART READING — always cover these foundations:\n"
        "• Lagna (1H) + Lagna lord — overall vitality, body, personality.\n"
        "• Moon — sign, nakshatra, house, aspects (mind, emotion, public life).\n"
        "• Sun — soul, father, authority.\n"
        "• Yogayakaraka or strongest planet → its house/dasha = peak life area.\n"
        "• Most afflicted house/planet → area of life-lesson / suffering.\n"
        "• Active Mahadasha+Antardasha — ALWAYS reference what the running lord rules + occupies.\n"
        "• Jaimini chara-karakas if relevant (AK=self, AmK=career, BK=siblings, MK=mother, PK=children, GK=challenges, DK=spouse).\n"
        "• Major yogas present in chart (Raja, Dhana, Vipareeta-Raja, Gajakesari, Pancha-mahapurusha, Neech-bhanga).\n"
        "\n"
        "C) MULTI-PART QUESTION RULE: If the devotee asked 2+ distinct things, address EACH in its own short paragraph in the order asked. Never skip a sub-question. Use a soft connector ('Aur dusri baat aapne pucha...' / 'Now coming to your second concern...').\n"
        "\n"
        "D) KP CROSS-CHECK: Use the KP block if provided — match the running DBA against significators of the relevant houses for each sub-question. Confirm or qualify the Vedic verdict.\n"
        "\n"
        "E) GOCHAR: Note any major slow-planet transit (Jupiter, Saturn, Rahu/Ketu) currently activating a relevant natal house — explain its CURRENT influence on the matter.\n"
        "\n"
        "F) HUMAN-FRIENDLY DELIVERY:\n"
        "• Open with empathy — name what the devotee seems to be feeling beneath the question.\n"
        "• Use the devotee's actual words back to them once, so they feel heard.\n"
        "• Translate every Sanskrit term inline ('Shukra (Venus) aapke...' / 'Saade-sati — yaani Shani ka 7.5 saal ka phase...').\n"
        "• No jargon dump. No lecture. Conversational tone, like sitting across the table.\n"
        "• End with ONE remedy targeted at the WEAKEST significator across all sub-questions identified.\n"
        "• Cite classical sources naturally ('jaisa BPHS me Maharishi Parashar kehte hain...') — never list them as a bibliography.\n"
        "\n"
        "G) Cite (combine as relevant): BPHS, Phaladeepika, Saravali, Jataka Parijata, Brihat Jataka, Uttara Kalamrita, Krishnamurti Reader, Prashna Marga, Lal Kitab."
    ),
}


def _focus_block(topic: str) -> str:
    return _TOPIC_FOCUS.get(topic, "")


# ── KP (Krishnamurti Paddhati) cross-verification context ────────────────────

_KP_PLANET_FROM_LON_CACHE: dict = {}


def _kp_context(birth: Any, topic: str) -> str:
    """
    Compute KP cusps + significators from birthData and return a compact text
    block focussed on the houses relevant to the question topic. Returns empty
    string on any failure (best-effort enrichment).
    """
    if not isinstance(birth, dict):
        return ""
    required = ("day", "month", "year", "hour", "minute", "ampm", "lat", "lon", "tz")
    if not all(k in birth and birth[k] is not None for k in required):
        return ""

    try:
        kp = _kp_calc()(birth)
    except Exception:
        return ""

    # Topic → which houses to surface
    topic_houses = {
        "marriage":     [2, 7, 11],
        "relationship": [5, 7, 11],
        "career":       [2, 6, 10, 11],
        "finance":      [2, 5, 9, 11],
        "health":       [1, 6, 8, 12],
        "child":        [2, 5, 11],
        "education":    [4, 5, 9],
        "travel":       [3, 9, 12],
        "litigation":   [6, 8, 11],
        "property":     [4, 11],
        "vehicle":      [4],
        "spiritual":    [9, 12],
        "family":       [3, 4, 9, 11],
        "general":      [1, 5, 7, 9, 10, 11],
    }.get(topic, [1, 5, 7, 9, 10, 11])

    cusps   = {c["house"]: c for c in kp.get("cusps", [])}
    sigs    = kp.get("significations", {})

    lines: list[str] = ["KP (Krishnamurti Paddhati) cross-check:"]

    # Cusp sub-lord verdict for each focus house
    for h in topic_houses:
        c = cusps.get(h)
        if not c:
            continue
        sb_lord = c.get("sb")
        sb_sig  = sigs.get(sb_lord, {})
        sb_houses = sorted(set(sb_sig.get("pl", []) + sb_sig.get("sb_houses", [])))
        lines.append(
            f"  • H{h} cusp: SL={c.get('sl')}, NL={c.get('nl')}, "
            f"Sub-Lord={sb_lord}, Sub-Sub={c.get('ss')}; "
            f"Sub-Lord {sb_lord} signifies houses {sb_houses}"
        )

    # KP significator summary for ALL planets — relevant for DBA matching
    lines.append("  Planetary significators (PL = occupied + owned houses):")
    for p in kp.get("planets", []):
        name = p.get("name")
        sig  = sigs.get(name, {})
        pl   = sig.get("pl", [])
        nl_h = sig.get("sl", [])  # houses ruled by nakshatra-lord
        sb_h = sig.get("sb_houses", [])
        lines.append(
            f"    {name} (H{p.get('house')}, NL={p.get('nl')}, SB={p.get('sb')}): "
            f"PL={pl}, NL-houses={nl_h}, SB-houses={sb_h}"
        )

    # Topic-specific KP verdict guidance
    if topic == "marriage":
        lines.append(
            "  KP MARRIAGE RULE (Krishnamurti Reader VI): If the 7th cusp Sub-Lord "
            "is a significator of houses 2, 7, or 11 (in PL, SB-houses, or NL-houses), "
            "marriage is PROMISED. If the Sub-Lord signifies primarily 1, 6, 10, or 12 "
            "(houses negating marriage), it is DENIED or heavily delayed. "
            "Timing: marriage occurs in the joint period (Dasha-Bhukti-Antar) when ALL THREE "
            "lords are significators of 2/7/11. Cross-verify the Vedic verdict with this KP rule."
        )
    elif topic == "child":
        lines.append(
            "  KP CHILD RULE: 5th cusp Sub-Lord must signify 2/5/11 for child promised; "
            "if it signifies 1/4/10/12 it is denied. Timing in joint period of 5L+11L+Jupiter significators."
        )
    elif topic == "career":
        lines.append(
            "  KP CAREER RULE: 10th cusp Sub-Lord signifying 2/6/10/11 = strong career; "
            "joint period of 2/6/10/11 significators = job change/promotion."
        )
    elif topic == "litigation":
        lines.append(
            "  KP LITIGATION RULE: 6th cusp SL signifying 6/11 → win; signifying 7/8/12 → loss/settlement."
        )

    return "\n".join(lines)


# ── Current planetary transits (today, sidereal Lahiri) ─────────────────────

_SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _transit_context() -> str:
    """Current sidereal positions of the 9 grahas — for transit (gochar) reasoning."""
    try:
        swe = _swe()
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        now = datetime.now(timezone.utc)
        ut_dec = now.hour + now.minute / 60.0 + now.second / 3600.0
        jd = swe.julday(now.year, now.month, now.day, ut_dec)
        flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
        bodies = [
            ("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS),
            ("Mercury", swe.MERCURY), ("Jupiter", swe.JUPITER),
            ("Venus", swe.VENUS), ("Saturn", swe.SATURN),
        ]
        lines = [f"Current transits (today, sidereal Lahiri, UTC {now:%Y-%m-%d %H:%M}):"]
        for name, pid in bodies:
            res, _ = swe.calc_ut(jd, pid, flags)
            lon = res[0] % 360
            sign = _SIGN_NAMES[int(lon / 30)]
            speed = res[3]
            retro = " (R)" if speed < 0 else ""
            lines.append(f"  {name}: {lon:5.2f}° {sign}{retro}")
        # Rahu/Ketu
        rres, _ = swe.calc_ut(jd, swe.MEAN_NODE, flags)
        rlon = rres[0] % 360
        klon = (rlon + 180) % 360
        lines.append(f"  Rahu: {rlon:5.2f}° {_SIGN_NAMES[int(rlon/30)]}")
        lines.append(f"  Ketu: {klon:5.2f}° {_SIGN_NAMES[int(klon/30)]}")
        return "\n".join(lines)
    except Exception:
        return ""


def _summarise_history(history: list) -> tuple[str, dict]:
    """
    Returns (compact_summary, behavior_signals).
    behavior_signals: { topic_counts, repeats, last_topic, total_user_turns }
    """
    if not isinstance(history, list) or not history:
        return "", {"topic_counts": {}, "repeats": 0, "last_topic": None, "total_user_turns": 0}

    user_qs: list[str] = []
    topics: list[str]  = []
    for m in history:
        if not isinstance(m, dict):
            continue
        role = (m.get("role") or "").lower()
        text = (m.get("text") or "").strip()
        if not text:
            continue
        if role == "user":
            user_qs.append(text)
            topics.append(_classify_topic(text))

    # Repeat-question detection: same topic asked >1 time, OR near-duplicate text.
    topic_counts: dict[str, int] = {}
    for t in topics:
        topic_counts[t] = topic_counts.get(t, 0) + 1
    repeats = sum(1 for c in topic_counts.values() if c > 1)

    return "", {
        "topic_counts": topic_counts,
        "repeats": repeats,
        "last_topic": topics[-1] if topics else None,
        "total_user_turns": len(user_qs),
        "recent_user_qs": user_qs[-3:],  # for in-prompt reference
    }


# ── Auto language detection from the question text ───────────────────────────

# Common Roman-Hindi (Hinglish) tokens — if any appear, treat the question as
# Hindi-leaning. Kept conservative: only words that are unambiguously Hindi
# (not English homographs).
_HINGLISH_TOKENS = {
    "kab", "kya", "kyon", "kyun", "kaise", "kaun", "kahan", "kitna", "kitne",
    "hai", "hain", "ho", "hoga", "hogi", "hoyega", "hua", "hui", "tha", "thi", "the",
    "mai", "main", "mei", "mein", "me",
    "mera", "meri", "mere", "mujhe", "mujhko", "humara", "humari", "hamara",
    "aap", "aapka", "aapki", "aapke", "tum", "tera", "teri", "tumhara",
    "acharya", "ji", "beta", "guruji", "panditji", "maharaj",
    "shaadi", "shadi", "vivah", "biwi", "pati", "patni", "rishta",
    "naukri", "naukari", "kaam", "paisa", "paise", "dhan", "santaan", "santan", "bachcha",
    "swasthya", "bimari", "tabiyat", "padhai", "pyaar", "pyar", "rishtey",
    "upay", "upaay", "mantra", "puja", "daan", "vrat", "totka",
    "batao", "bataiye", "bataenge", "kijiye", "karke", "karna",
    "karu", "karoon", "karunga", "karungi", "karenge", "karna",
    "jau", "jaun", "jaunga", "jaungi", "jaye", "jaayega", "jaayegi",
    "ruk", "rukna", "ruke", "rukoon",
    "soch", "socha", "sochna", "raha", "rahi", "rahe", "rahega", "rahegi",
    "lega", "legi", "lega", "milega", "milegi", "milti", "milta",
    "nahi", "nahin", "haan", "han", "bilkul", "thoda", "bahut", "zyada", "kam",
    "kundli", "rashi", "nakshatra", "dasha", "graha", "yog", "dosh", "manglik",
    "maa", "pita", "papa", "mummy", "bhai", "behan", "didi", "ghar", "gharwale",
    "abhi", "kabhi", "phir", "fir", "pehle", "baad", "se", "tak", "ya", "aur",
    "kr", "krna", "hojayegi", "hojayega", "lagta", "lagti", "lagte",
}


def _detect_question_lang(question: str, fallback: str) -> str:
    """
    Returns:
      'hi' → Devanagari script (pure Hindi)
      'hn' → Roman-Hindi (Hinglish — Hindi words written in English letters)
      'en' → English
      Other Indian-script lang codes pass through from `fallback`.
    """
    q = (question or "").strip()
    if not q:
        return fallback or "en"

    # Devanagari Unicode range = pure Hindi
    for ch in q:
        if "\u0900" <= ch <= "\u097F":
            return "hi"

    # Other Indian scripts → respect the explicit `lang` param so we don't
    # mis-route a Tamil/Bengali/etc. question to English.
    if (fallback or "").lower() in {"ta", "te", "kn", "ml", "bn", "mr", "gu", "pa", "or", "as"}:
        return fallback

    # Hinglish (Roman-Hindi) detection — tokenise on word boundaries
    import re
    tokens = re.findall(r"[a-zA-Z]+", q.lower())
    if not tokens:
        return fallback or "en"

    hinglish_hits = sum(1 for t in tokens if t in _HINGLISH_TOKENS)
    # ≥1 Hinglish token AND ≥10% of tokens, OR ≥2 absolute hits → Hinglish.
    # Tighter threshold catches short prompts like "Mai abhi job switch karu ya ruk jau?"
    if hinglish_hits >= 2:
        return "hn"
    if hinglish_hits >= 1 and (hinglish_hits / max(1, len(tokens))) >= 0.10:
        return "hn"

    # If the user explicitly chose 'hi' or 'hn' in app settings, honor it
    # rather than collapsing to English.
    fb = (fallback or "").lower()
    if fb in {"hi", "hn"}:
        return fb
    return "en"


# ─────────────────────────────────────────────────────────────────────────────
# HINGLISH-FIRST ZODIAC NAME POST-PROCESSOR
# When the user asks in Hinglish/Hindi the response should use the Vedic
# Sanskrit zodiac names (Mesh / Vrishabh / … / Dhanu / Meen) — NOT the
# Western English forms (Aries / Taurus / … / Sagittarius / Pisces). This
# applies to ALL paths (single-intent OpenAI, structured wealth cards,
# rule-engine fallback) so we run it as a final scrub on the response text.
# ─────────────────────────────────────────────────────────────────────────────
_ZODIAC_EN_TO_HI: dict[str, str] = {
    "Aries":       "Mesh",
    "Taurus":      "Vrishabh",
    "Gemini":      "Mithun",
    "Cancer":      "Kark",
    "Leo":         "Simha",
    "Virgo":       "Kanya",
    "Libra":       "Tula",
    "Scorpio":     "Vrishchik",
    "Sagittarius": "Dhanu",
    "Capricorn":   "Makar",
    "Aquarius":    "Kumbh",
    "Pisces":      "Meen",
}
_ZODIAC_RX = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _ZODIAC_EN_TO_HI) + r")\b",
    re.IGNORECASE,
)


def _hinglishify_zodiac(text: str, lang: str | None) -> str:
    """Replace English zodiac names with Hinglish equivalents in `text`.

    Only fires when the response language is Hinglish (`hn`) or Hindi (`hi`).
    English-locale callers (`en`) get the original Western names. Preserves
    case insensitively (always emits the canonical capitalised Hinglish
    spelling — Cosmic Lens style is title-case for sign names)."""
    if not isinstance(text, str) or not text:
        return text
    eff = (lang or "").strip().lower()
    if eff not in {"hn", "hi", "hinglish"}:
        return text
    def _sub(m):
        key = m.group(1).capitalize()
        return _ZODIAC_EN_TO_HI.get(key, m.group(1))
    return _ZODIAC_RX.sub(_sub, text)


def hinglishify_response(result: dict, lang: str | None) -> dict:
    """Apply `_hinglishify_zodiac` to every user-visible text field on a
    response payload. Mutates and returns the same dict for convenience.

    Covered fields:
      • result["text"]                    — single-shot answer
      • result["cards"][i]["text"]        — multi-intent v2 cards
      • result["cards"][i]["narrative"]   — v2 wealth structured narrative
      • result["cards"][i]["structured"]["empathy_open" | "human_close" |
                                         "headline" | "remedy" | "note" |
                                         "what_will_happen"|"what_to_do"|
                                         "what_to_avoid"]
    Safe to call with non-Hinglish lang (no-op) and with malformed payloads."""
    if not isinstance(result, dict):
        return result
    eff = (lang or "").strip().lower()
    if eff not in {"hn", "hi", "hinglish"}:
        return result
    if isinstance(result.get("text"), str):
        result["text"] = _hinglishify_zodiac(result["text"], eff)
    cards = result.get("cards")
    if isinstance(cards, list):
        for c in cards:
            if not isinstance(c, dict):
                continue
            for k in ("text", "narrative"):
                if isinstance(c.get(k), str):
                    c[k] = _hinglishify_zodiac(c[k], eff)
            s = c.get("structured")
            if isinstance(s, dict):
                for k in ("empathy_open", "human_close", "headline",
                          "remedy", "note"):
                    if isinstance(s.get(k), str):
                        s[k] = _hinglishify_zodiac(s[k], eff)
                for k in ("what_will_happen", "what_to_do", "what_to_avoid"):
                    arr = s.get(k)
                    if isinstance(arr, list):
                        s[k] = [_hinglishify_zodiac(x, eff) if isinstance(x, str) else x
                                for x in arr]
    return result


def _resolve_response_lang(question: str, lang: str,
                           preferred_language: Optional[str]) -> str:
    """
    Final language decision per the Language Intelligence spec:
      1. user.preferred_language    (highest — sticky personal pref)
      2. detected language of the question (per-message smart match)
      3. app default language `lang`        (lowest — fallback)
    """
    pl = (preferred_language or "").strip().lower()
    if pl in {"en", "hi", "hn"}:
        return pl
    return _detect_question_lang(question, lang)


def _strict_lang_block(code: str) -> str:
    """Hard, non-negotiable per-language enforcement block injected as the
    very first thing the model sees inside the user-turn payload. Per spec:
    consistency MUST hold for the entire reply; no mid-response switching."""
    if code == "hi":
        return (
            "════════════════════ LANGUAGE LOCK — हिन्दी ════════════════════\n"
            "Reply ENTIRELY in pure Hindi (Devanagari script — देवनागरी).\n"
            "  • Every sentence must be Hindi. No Hinglish (no Roman script).\n"
            "  • No English words except proper nouns (names, places).\n"
            "  • Sanskrit terms (Saptamesh, Karaka, Mahadasha) stay in Devanagari.\n"
            "  • Numbers may be either Devanagari (१-९) or Western (1-9).\n"
            "  • The ENTIRE response from first word to last must stay in Hindi —\n"
            "    NEVER switch language mid-response. This is non-negotiable.\n"
            "═══════════════════════════════════════════════════════════════\n\n"
        )
    if code == "hn":
        return (
            "═════════════════ LANGUAGE LOCK — HINGLISH ═════════════════\n"
            "Reply ENTIRELY in Hinglish (Hindi words written in English/Roman script).\n"
            "  • Natural conversational Hinglish — clear, expert tone (NOT guru\n"
            "    style): e.g. \"Aapki kundli mein Saturn 7th house mein hai...\".\n"
            "  • NO Devanagari script anywhere. NO pure-English-only paragraphs.\n"
            "  • Astrology terms in Roman: Saptamesh, Karaka, Mahadasha, Sade-Sati.\n"
            "  • Even if the devotee wrote the question in Devanagari Hindi or\n"
            "    pure English, you MUST still reply in Hinglish — this is the\n"
            "    devotee's chosen preference.\n"
            "  • The ENTIRE response stays in Hinglish — never switch mid-reply.\n"
            "═══════════════════════════════════════════════════════════════\n\n"
        )
    # default: English
    return (
        "═════════════════ LANGUAGE LOCK — ENGLISH ═════════════════\n"
        "Reply ENTIRELY in clear, natural English.\n"
        "  • No Hindi/Hinglish words mixed in. Use English equivalents:\n"
        "    \"7th lord\" not \"Saptamesh\", \"main period\" not \"Mahadasha\",\n"
        "    \"7-and-a-half year Saturn cycle\" not \"Sade-Sati\".\n"
        "  • Sanskrit names of yogas/planets are allowed (e.g. \"Mangal Dosha\",\n"
        "    \"Gajakesari Yoga\") but ALWAYS followed by a brief English meaning.\n"
        "  • Even if the devotee wrote the question in Hindi or Hinglish, you\n"
        "    MUST still reply in English — this is the devotee's chosen preference.\n"
        "  • The ENTIRE response stays in English — never switch mid-reply.\n"
        "═══════════════════════════════════════════════════════════════\n\n"
    )


def _build_messages(
    question: str,
    kundli: Any,
    lang: str,
    reply_idx: int,
    birth: Any = None,
    topic: str = "general",
    history: list | None = None,
    preferred_language: Optional[str] = None,
    mode: str = "astro",
    out_meta: dict | None = None,
    marriage_subtype: str = "timing",
) -> list[dict]:
    # ── LANGUAGE INTELLIGENCE — sticky preference > detection > fallback ─────
    detected = _resolve_response_lang(question, lang, preferred_language)
    lang_name = _LANG_NAME.get(detected, "English")

    # ── GENERAL MODE — HUMAN STYLE prompt, no chart, no scaffolding ─────────
    # Concept / comparison / knowledge questions. Clean ChatGPT-style answers
    # with bullets allowed when helpful. No guru tone, no Beta/Pranam, no
    # kundli reference, no forced remedy.
    if mode == "general":
        sys_general = (
            "SYSTEM PROMPT — STRICT RESPONSE CONTROL (MANDATORY)\n\n"
            "You are NOT allowed to answer freely. You MUST follow this exact\n"
            "structure. Any deviation = WRONG answer.\n\n"
            "REQUIRED STRUCTURE (in this exact order):\n\n"
            "  1. FIRST LINE: must begin with the literal text\n"
            "     `Simple samjho — ` followed by the core idea in ONE sentence.\n\n"
            "  2. EXPLANATION: 1 to 2 short lines max. No long paragraphs.\n\n"
            "  3. BULLETS: ONLY if genuinely needed (comparison / 2+ items /\n"
            "     listy concept). 2 to 4 bullets max, 1 line each, bold the\n"
            "     key term: `- **Term**: short note`. Otherwise SKIP bullets\n"
            "     entirely — do NOT pad.\n\n"
            "  4. LAST LINE: must begin with the literal text `Final: ` and\n"
            "     give the one-line takeaway / verdict.\n\n"
            "STRICT RULES:\n"
            "  • Total length 50–120 words. NEVER more.\n"
            "  • NO long paragraphs. NO textbook tone. NO ### headers.\n"
            "  • NO kundli / chart / planet / dasha / rashi / remedy reference.\n"
            "  • NO guru tone. NO \"Beta\", \"Pranam\", \"I understand\".\n"
            "  • Stay human, simple, confident.\n\n"
            "EXAMPLE (correct shape):\n"
            "  Simple samjho — Saturn discipline aur delay ka planet hai.\n"
            "  Yeh hard work aur patience sikhata hai, lekin shortcut nahi deta.\n"
            "\n"
            "  - **Discipline**: rules aur structure ka karak.\n"
            "  - **Delay**: result milne mein time leta hai.\n"
            "\n"
            "  Final: Saturn slow but solid growth ka planet hai.\n\n"
            "BANNED PHRASES: Pranam, Beta, Beta Q, Dekhiye beta, I sense your,\n"
            "  I understand your, As an AI, based on your chart.\n"
            "BANNED HEDGING: maybe, possible, likely, chances, ho sakta hai,\n"
            "  shayad, sambhavna, I think, perhaps, around (for dates).\n\n"
            "THIS STRUCTURE IS MANDATORY — NOT OPTIONAL.\n"
            f"REPLY ENTIRELY IN: {lang_name}."
        )
        msgs: list[dict] = [{"role": "system", "content": sys_general}]
        # Attach last 6 conversation turns (text-only) for context continuity.
        for h in (history or [])[-6:]:
            r = h.get("role")
            t = h.get("content") or h.get("text") or ""
            if r in ("user", "assistant") and t:
                msgs.append({"role": r, "content": t})
        msgs.append({"role": "user", "content": question})
        return msgs

    # ── AI INTENT ROUTER ─────────────────────────────────────────────────────
    # A tiny gpt-4o-mini call classifies the question into one of 8 routes.
    # We use it only for astro mode (general mode is already handled above).
    # On any failure the router returns "analysis" → falls through to the
    # full pipeline, so the regex-based _is_chart_fact_question() also stays
    # as a hard safety net for the simple/dosha/transparency cases.
    intent_route: str = ""
    if mode == "astro":
        try:
            from intent_router import classify_intent  # type: ignore
            intent_route = classify_intent(question, history=history, client=_get_client())
            if isinstance(out_meta, dict):
                out_meta["intent_route"] = intent_route
        except Exception as _exc:
            intent_route = ""

    # Greeting → tiny warm reply, no chart, no scaffolding.
    if mode == "astro" and intent_route == "greeting":
        sys_greet = (
            "You are a warm Vedic astrologer chatting with a returning user. "
            "Reply to their greeting in ONE short, friendly sentence. NO "
            "chart reference, NO planet talk, NO advice. Just a human, warm "
            "acknowledgement. Optionally add ONE short sentence inviting "
            "them to ask their question. Maximum 2 sentences total.\n"
            "BANNED: Pranam, Beta, Dekhiye beta, As an AI, I sense.\n"
            f"REPLY ENTIRELY IN: {lang_name}."
        )
        msgs = [{"role": "system", "content": sys_greet}]
        for h in (history or [])[-4:]:
            r = h.get("role")
            t = h.get("content") or h.get("text") or ""
            if r in ("user", "assistant") and t:
                msgs.append({"role": r, "content": t})
        msgs.append({"role": "user", "content": question})
        return msgs

    # General concept question (no chart needed) — re-use the strict
    # general-mode prompt path by recursing once with mode="general".
    if mode == "astro" and intent_route == "general":
        return _build_messages(
            question=question, kundli=kundli, lang=lang, reply_idx=reply_idx,
            birth=birth, topic=topic, history=history,
            preferred_language=preferred_language, mode="general",
            out_meta=out_meta, marriage_subtype=marriage_subtype,
        )

    # ── SIMPLE CHART-FACT MINIMAL PROMPT ─────────────────────────────────────
    # For pure lookup questions ("mera rashi kya hai", "lagna batao", etc.)
    # we strip ALL noise (focus / KP / transit / intel / behavior / narrator)
    # and use a tight 2-3 sentence prompt. Same model, same flow — just clean.
    # This is the ONLY way to reliably stop the AI from padding with houses,
    # dasha implications, and "Isliye dhyan dena zaroori hai" closers.
    _route_is_minimal = intent_route in ("simple_fact", "dosha_check", "transparency")
    if mode == "astro" and (_route_is_minimal or _is_chart_fact_question(question)):
        chart_only = _kundli_summary(kundli, birth)

        # ── Dosha pre-compute (deterministic) ─────────────────────────────
        # If question is about a specific dosha, run the engine and inject
        # the verdict so AI doesn't have to "calculate" — just narrates.
        dosha_facts = ""
        try:
            if isinstance(kundli, dict) and kundli.get("planets"):
                from dosh_engine import analyze_doshas  # type: ignore
                _d = analyze_doshas(
                    kundli.get("planets") or [],
                    (kundli.get("nakshatra") or "") if isinstance(kundli, dict) else "",
                )
                _dosh_lines = []
                for d in (_d.get("dosh_list") or []):
                    _dosh_lines.append(
                        f"  • {d.get('name','')}: {d.get('status','')} "
                        f"— {d.get('headline','')} ({d.get('planet_note','')})"
                    )
                if _dosh_lines:
                    dosha_facts = (
                        "\n\nLOCKED DOSHA ANALYSIS (computed by engine — use "
                        "these EXACT verdicts, do not recompute or override):\n"
                        + "\n".join(_dosh_lines)
                    )
        except Exception as exc:
            print(f"[openai_helper] dosh pre-compute failed: {exc}")

        sys_minimal = (
            "You are Acharya Vidyasagar, a warm modern Vedic astrologer who "
            "chats like a knowledgeable friend.\n\n"
            f"REPLY ENTIRELY IN: {lang_name}.\n\n"
            "The user asked a SIMPLE direct question (chart fact OR a dosha "
            "yes/no). Reply in EXACTLY 2-3 short sentences. NO MORE.\n\n"
            "FORMAT (strict):\n"
            "  CASE A — Chart fact (rashi / lagna / nakshatra / dasha / "
            "gana / yoni / etc.):\n"
            "    • Sentence 1: state the fact directly (e.g. \"Aapki Rashi "
            "Gemini hai.\").\n"
            "    • Sentence 2: ONE natural personality / nature line.\n"
            "    • STOP.\n\n"
            "  CASE C — \"How do you know\" / transparency follow-up "
            "(\"tumko kaise pata\", \"kaise jaana\", \"how do you know\"):\n"
            "    • Sentence 1: state the SOURCE plainly — \"Aapki janm "
            "date, time, aur place se planets calculate hote hain.\"\n"
            "    • Sentence 2: state the SPECIFIC fact from the chart — "
            "e.g. \"Aapka Mars Capricorn 22° pe hai aur Lagna Libra hai, "
            "isliye Mars 4th house mein baitha hai.\"\n"
            "    • STOP. NO dasha, NO advice, NO remedy.\n\n"
            "  CASE B — Dosha yes/no (\"kya me manglik hun\", \"kaal sarp "
            "hai\", \"pitru dosh\"):\n"
            "    • Sentence 1: clear YES or NO using the LOCKED DOSHA "
            "ANALYSIS below — e.g. \"Haan, aap manglik hain.\" OR \"Nahi, "
            "aap manglik nahi hain.\" Use the engine's status: 'Active' = "
            "haan / strong; 'Mild' = haan / partial; 'None' = nahi.\n"
            "    • Sentence 2: ONE plain reason line stating WHY (the "
            "exact planet placement from the engine — e.g. \"Mars aapke "
            "Lagna mein baitha hai.\").\n"
            "    • Sentence 3 (optional): if the dosh is Mild, ONE soft "
            "reassurance line. Otherwise STOP after sentence 2.\n\n"
            "ABSOLUTELY BANNED in this reply:\n"
            "  ✗ Current dasha mention (unless the user asked about dasha)\n"
            "  ✗ Marriage advice / partner advice (unless user asked)\n"
            "  ✗ Remedies / mantras / jaap (unless user asked for remedy)\n"
            "  ✗ Closing sermons (\"Isliye dhyan dena zaroori hai\", "
            "\"Aapko ek achhe partner ki talash karni hogi\")\n"
            "  ✗ \"Pranam\", \"Beta\", \"Dekhiye\", greetings, headers, "
            "bullets\n"
            "  ✗ Multi-paragraph replies (max 3 short sentences total)\n\n"
            "If the user wants a remedy or deeper analysis, they will ask "
            "in the next turn. Do NOT volunteer it here.\n\n"
            f"CHART:\n{chart_only}"
            f"{dosha_facts}"
        )
        return [
            {"role": "system", "content": sys_minimal},
            {"role": "user",   "content": question},
        ]

    chart_str = _kundli_summary(kundli, birth)
    # Pre-computed chart intelligence — dignities, yogas, mangal-dosh,
    # sade-sati, house-lord placements, aspects. The AI now interprets
    # known facts instead of deriving them itself (single biggest accuracy
    # unlock for the Ask flow).
    intel_str = ""
    intel_obj = None
    try:
        analyze_chart, format_intelligence = _chart_intel()
        intel_obj = analyze_chart(kundli, birth)
        if intel_obj:
            intel_str = format_intelligence(intel_obj)
    except Exception as exc:
        print(f"[openai_helper] chart_intelligence failed: {exc}")

    # ── LOCKED FACTS (Sprint 1) ──────────────────────────────────────────────
    # One assembled, structured block with EXPLICIT counts and named lists for
    # yogas, doshas, planet strengths, dasha. The AI is instructed (rules
    # below) to MIRROR these values verbatim — never invent counts/names.
    locked_facts_str = ""
    engine_status = {"ok": [], "skipped": [], "failed": [], "overall": "empty"}
    try:
        from locked_facts import (build_locked_facts,  # type: ignore
                                   get_last_engine_status,
                                   _finalise_engine_status)
        locked_facts_str = build_locked_facts(kundli, birth) or ""
        # Sprint-26 Fix-K: capture which phases ran/failed so the
        # downstream timing-validator can soften when the engine
        # genuinely had no timing data to provide. We stash the
        # status into out_meta — the caller (which holds req_id)
        # is responsible for tracing it.
        try:
            _finalise_engine_status()
        except Exception:
            pass
        engine_status = get_last_engine_status()
    except Exception as exc:
        print(f"[openai_helper] locked_facts failed: {exc}")
    if isinstance(out_meta, dict):
        out_meta["engine_status"] = engine_status

    # ── Sprint-52 RAG: classical knowledge retrieval (OPINION questions only) ─
    # Timing questions get ZERO RAG (engine block already gives the answer).
    # Opinion questions ("job vs business?", "career kya?", "nature kaisa?")
    # get top-5 chunks from vedic/knowledge/*.md to ground reasoning.
    # NOTE: RAG embeddings use OpenAI's text-embedding-3-small endpoint, which
    # the Replit AI Integrations proxy does NOT support — it falls back to the
    # raw OPENAI_API_KEY. When that key hits its quota (429), we suppress the
    # noisy stack trace because RAG is purely additive (the engine + chat path
    # remain fully functional via the proxy).
    rag_context_str = ""
    try:
        from vedic.validator.timing_validator import is_timing_question  # type: ignore
        if question and not is_timing_question(question):
            from vedic.rag.retriever import retrieve_and_format  # type: ignore
            rag_context_str = retrieve_and_format(question, k=5, max_chars=3500)
    except Exception as exc:  # noqa: BLE001
        _msg = str(exc)
        if "insufficient_quota" in _msg or "429" in _msg or "rate_limit" in _msg.lower():
            # One-line warn — known limitation; not a bug to chase
            print("[openai_helper] rag retrieval skipped (embeddings quota — non-essential)")
        else:
            print(f"[openai_helper] rag retrieval failed: {exc}")
    if rag_context_str:
        locked_facts_str = locked_facts_str + "\n\n" + rag_context_str

    # ── DETERMINISTIC MARRIAGE VERDICT ────────────────────────────────────────
    # For topic == "marriage", we compute the verdict in pure Python BEFORE
    # the AI is invoked. The AI is then forbidden from changing verdict /
    # score / timeline / remedy — it is only a narrator.
    marriage_verdict_block = ""
    marriage_verdict_obj   = None
    marriage_facts         : dict | None = None  # locked facts for narration
    marriage_use_alt       = False # constraint-aware: use next_alt_window
    if topic == "marriage" and isinstance(kundli, dict) and kundli.get("planets"):
        try:
            kp_dict = None
            try:
                kp_dict = _kp_calc()(birth) if isinstance(birth, dict) else None
            except Exception as exc:
                print(f"[openai_helper] kp calc for marriage failed: {exc}")
            assess_marriage, format_verdict_for_prompt = _marriage_engine()
            marriage_verdict_obj = assess_marriage(kundli, intel_obj or {}, kp_dict or {}, birth)
            if marriage_verdict_obj:
                marriage_verdict_block = format_verdict_for_prompt(marriage_verdict_obj)
                # Sprint-7: append Jaimini Upapada line so MARRIAGE NARRATOR
                # mode (which supersedes Rules 2-6) still sees it as ground truth.
                try:
                    from jaimini import (compute_arudha_padas,  # type: ignore
                                         compute_upapada)
                    _lg = kundli.get("ascendant")
                    if isinstance(_lg, dict):
                        _lg = _lg.get("sign") or _lg.get("name")
                    _ar = compute_arudha_padas(kundli.get("planets") or [], _lg)
                    _ul = compute_upapada(_ar, kundli.get("planets") or []) if _ar else {}
                    if _ul:
                        ul_line = (
                            f"  Jaimini Upapada (UL=A12): {_ul['ul_sign']} — "
                            f"lord {_ul['ul_lord']} in {_ul.get('ul_lord_in') or '?'} "
                            f"({_ul.get('ul_lord_house') or '?'}th from UL); "
                            f"2nd-from-UL={_ul['second_from_ul']} "
                            f"(occ: {', '.join(_ul['occupants_2nd']) or 'none'}); "
                            f"12th-from-UL={_ul['twelfth_from_ul']} "
                            f"(occ: {', '.join(_ul['occupants_12th']) or 'none'}); "
                            f"VERDICT: {_ul['verdict']}\n"
                            "  >>> NARRATE THIS UL VERDICT IN ONE NATURAL SENTENCE — "
                            "MANDATORY THIS TURN. Pull the exact UL sign, UL-lord, "
                            "and verdict tag (STABLE/STRAINED/MIXED/NEUTRAL). <<<\n"
                        )
                        # Insert just before the trailing ════ line of the block
                        marker = "════════════════════════════════════════════════════════════════════\n"
                        if marriage_verdict_block.endswith(marker):
                            marriage_verdict_block = (
                                marriage_verdict_block[:-len(marker)]
                                + ul_line + marker
                            )
                        else:
                            marriage_verdict_block += ul_line
                except Exception as _exc:
                    print(f"[openai_helper] jaimini UL inject failed: {_exc}")
                marriage_use_alt = _detect_marriage_constraint(question, history or [])
                # Build a CLEAN facts payload — values only, no template,
                # no jargon labels, no "Pranam beta". The AI receives
                # these as locked data and writes its own natural reply.
                from marriage_engine import (extract_window_str,
                                             extract_alt_window_str)
                v = marriage_verdict_obj
                # Sprint-7: also compute Jaimini Upapada signature for the
                # narrator path (which bypasses LOCKED FACTS / Rule O reminders).
                _ul_facts = {}
                try:
                    from jaimini import (compute_arudha_padas,  # type: ignore
                                         compute_upapada)
                    _lg = kundli.get("ascendant")
                    if isinstance(_lg, dict):
                        _lg = _lg.get("sign") or _lg.get("name")
                    _ar = compute_arudha_padas(kundli.get("planets") or [], _lg)
                    _ul = compute_upapada(_ar, kundli.get("planets") or []) if _ar else {}
                    if _ul:
                        # Distil verdict tag (first 1-2 words before " — ")
                        verdict_full = _ul.get("verdict", "")
                        verdict_tag = "NEUTRAL"
                        for tag in ("STABLE", "STRAINED", "MIXED", "NEUTRAL"):
                            if tag in verdict_full:
                                verdict_tag = tag
                                break
                        _ul_facts = {
                            "ul_sign":         _ul.get("ul_sign", ""),
                            "ul_lord":         _ul.get("ul_lord", ""),
                            "ul_lord_in":      _ul.get("ul_lord_in") or "",
                            "ul_lord_house":   _ul.get("ul_lord_house"),
                            "second_from_ul":  _ul.get("second_from_ul", ""),
                            "occupants_2nd":   ", ".join(_ul.get("occupants_2nd") or []) or "none",
                            "twelfth_from_ul": _ul.get("twelfth_from_ul", ""),
                            "occupants_12th":  ", ".join(_ul.get("occupants_12th") or []) or "none",
                            "occupants_ul":    ", ".join(_ul.get("occupants_ul") or []) or "none",
                            "verdict_tag":     verdict_tag,
                            "verdict_full":    verdict_full,
                        }
                except Exception as _exc:
                    print(f"[openai_helper] jaimini for narrator failed: {_exc}")

                marriage_facts = {
                    "verdict":         (v.get("verdict") or "").strip(),
                    "window_str":      extract_window_str(v) or "",
                    "alt_window_str":  extract_alt_window_str(v) or "",
                    "current_dasha":   (v.get("current_dasha") or "").strip(),
                    "seventh_lord":    (v.get("seventh_lord") or "").strip(),
                    "karaka":          (v.get("karaka") or "").strip(),
                    "remedy":          (v.get("remedy") or "").strip(),
                    "score":            v.get("score"),
                    "kp_verdict":      (v.get("kp_verdict") or "").strip(),
                    "marriage_promised": v.get("marriage_promised"),
                    "marriage_denied":   v.get("marriage_denied"),
                    "delay":             v.get("delay"),
                    "jaimini":           _ul_facts,
                }
                print(f"[openai_helper] marriage verdict: "
                      f"verdict='{marriage_facts['verdict']}' "
                      f"score={marriage_facts['score']} "
                      f"kp={marriage_facts['kp_verdict']} "
                      f"use_alt={marriage_use_alt} "
                      f"window='{marriage_facts['window_str']}' "
                      f"alt='{marriage_facts['alt_window_str']}'")
        except Exception as exc:
            print(f"[openai_helper] marriage_engine failed: {exc}")

    # ── DETERMINISTIC STOCK-MARKET VERDICT ────────────────────────────────────
    # For topic == "finance" + stock-keyword question, we compute the verdict
    # in pure Python BEFORE the AI is invoked. The AI is then forbidden from
    # changing verdict / score / window / strategy / sectors / remedy — it is
    # only a narrator. Mirror of marriage_engine integration above.
    stock_verdict_block = ""
    stock_verdict_obj   = None
    stock_window_str    = ""
    if (topic in ("finance", "general", "wealth", "career")
            and not marriage_verdict_block
            and isinstance(kundli, dict) and kundli.get("planets")
            and _is_stock_question(question)):
        try:
            kp_dict_s = None
            try:
                # Reuse the marriage-path KP if we already computed it; else fresh.
                kp_dict_s = locals().get("kp_dict")
                if not kp_dict_s and isinstance(birth, dict):
                    kp_dict_s = _kp_calc()(birth)
            except Exception as exc:
                print(f"[openai_helper] kp calc for stock failed: {exc}")
            assess_stock, fmt_stock, stock_window_fn, classify_stock_q = _stock_engine()
            # Sprint-25 Fix-B: surface AI Ear bucket when domain matches.
            _stock_pre_bucket = _ai_ear_bucket_for(out_meta, "stock")
            stock_verdict_obj = assess_stock(
                kundli, intel_obj or {}, kp_dict_s or {}, birth, question,
                pre_classified_bucket=_stock_pre_bucket)
            if stock_verdict_obj:
                stock_verdict_block = fmt_stock(stock_verdict_obj)
                stock_window_str    = stock_window_fn(stock_verdict_obj) or ""
                if isinstance(out_meta, dict):
                    out_meta["stock_verdict_obj"]   = stock_verdict_obj
                    out_meta["stock_question_type"] = stock_verdict_obj.get("question_type")
                    out_meta["stock_window_str"]    = stock_window_str
                print(f"[openai_helper] stock_engine OK → "
                      f"q_type='{stock_verdict_obj.get('question_type')}' "
                      f"verdict='{stock_verdict_obj.get('verdict','')[:60]}' "
                      f"score={stock_verdict_obj.get('score')} "
                      f"npx={stock_verdict_obj.get('natal_promise_score')} "
                      f"trig={stock_verdict_obj.get('current_trigger_score')} "
                      f"window='{stock_window_str}'")
        except Exception as exc:
            print(f"[openai_helper] stock_engine failed: {exc}")

    # ── DETERMINISTIC LOVE & RELATIONSHIP VERDICT ─────────────────────────────
    # For love-keyword questions (non-marriage, non-stock), compute deterministic
    # verdict via love_engine. AI becomes pure narrator with brand-safety guards
    # for affair / breakup / one_sided buckets. Mirror of marriage/stock.
    love_verdict_block = ""
    love_verdict_obj   = None
    love_window_str    = ""
    if (topic in ("relationship", "general")
            and not marriage_verdict_block
            and not stock_verdict_block
            and isinstance(kundli, dict) and kundli.get("planets")
            and _is_love_question(question)):
        try:
            kp_dict_l = locals().get("kp_dict") or locals().get("kp_dict_s")
            try:
                if not kp_dict_l and isinstance(birth, dict):
                    kp_dict_l = _kp_calc()(birth)
            except Exception as exc:
                print(f"[openai_helper] kp calc for love failed: {exc}")
            assess_love, fmt_love, love_window_fn, _classify_love_q = _love_engine()
            _love_pre_bucket = _ai_ear_bucket_for(out_meta, "love")
            love_verdict_obj = assess_love(
                kundli, intel_obj or {}, kp_dict_l or {}, birth, question,
                pre_classified_bucket=_love_pre_bucket)
            if love_verdict_obj:
                love_verdict_block = fmt_love(love_verdict_obj)
                love_window_str    = love_window_fn(love_verdict_obj) or ""
                if isinstance(out_meta, dict):
                    out_meta["love_verdict_obj"]   = love_verdict_obj
                    out_meta["love_question_type"] = love_verdict_obj.get("question_type")
                    out_meta["love_window_str"]    = love_window_str
                print(f"[openai_helper] love_engine OK → "
                      f"q_type='{love_verdict_obj.get('question_type')}' "
                      f"verdict='{love_verdict_obj.get('verdict','')[:60]}' "
                      f"score={love_verdict_obj.get('score')} "
                      f"npx={love_verdict_obj.get('natal_promise_score')} "
                      f"trig={love_verdict_obj.get('current_trigger_score')} "
                      f"window='{love_window_str}'")
        except Exception as exc:
            print(f"[openai_helper] love_engine failed: {exc}")

    # ── DETERMINISTIC CAREER & PROFESSION VERDICT ─────────────────────────────
    # For career-keyword questions (job/promotion/transfer/govt-job/business/
    # partnership/setback), compute deterministic verdict via career_engine.
    # Routing priority above career: marriage > stock > love. AI becomes
    # pure narrator with brand-safety guards for govt-job / business-start /
    # resignation / partnership softening. Mirror of marriage/stock/love.
    career_verdict_block = ""
    career_verdict_obj   = None
    if (topic in ("career", "general")
            and not marriage_verdict_block
            and not stock_verdict_block
            and not love_verdict_block
            and isinstance(kundli, dict) and kundli.get("planets")
            and _is_career_question(question)):
        try:
            kp_dict_c = (locals().get("kp_dict")
                         or locals().get("kp_dict_s")
                         or locals().get("kp_dict_l"))
            try:
                if not kp_dict_c and isinstance(birth, dict):
                    kp_dict_c = _kp_calc()(birth)
            except Exception as exc:
                print(f"[openai_helper] kp calc for career failed: {exc}")
            assess_career, fmt_career, _classify_career_q = _career_engine()
            _career_pre_bucket = _ai_ear_bucket_for(out_meta, "career")
            career_verdict_obj = assess_career(
                kundli, intel_obj or {}, kp_dict_c or {}, birth, question,
                pre_classified_bucket=_career_pre_bucket)
            if career_verdict_obj:
                career_verdict_block = fmt_career(career_verdict_obj, question)
                if isinstance(out_meta, dict):
                    out_meta["career_verdict_obj"]   = career_verdict_obj
                    out_meta["career_question_type"] = career_verdict_obj.get("bucket")
                print(f"[openai_helper] career_engine OK → "
                      f"bucket='{career_verdict_obj.get('bucket')}' "
                      f"tense='{career_verdict_obj.get('tense')}' "
                      f"verdict='{career_verdict_obj.get('verdict','')[:60]}' "
                      f"score={career_verdict_obj.get('score')} "
                      f"conf={career_verdict_obj.get('confidence')}")
        except Exception as exc:
            print(f"[openai_helper] career_engine failed: {exc}")

    # ── DETERMINISTIC WEALTH & FINANCE VERDICT ────────────────────────────────
    # For wealth/finance-keyword questions (salary / business profit / loan /
    # property / inheritance / savings / sudden-windfall / debt-recovery /
    # foreign-income / partnership-finance / general dhana), compute
    # deterministic verdict via wealth_engine. Routing priority above wealth:
    # marriage > stock > love > career. Wealth must NOT swallow stock/share/
    # SIP/equity/intraday/F&O — those belong to stock_engine which fires
    # earlier. AI becomes pure narrator with STRICT brand-safety guards
    # (NEVER predict rupee amounts, NEVER predict bankruptcy, NEVER advise
    # loan-skip / EMI-default / tax-evasion, NEVER endorse lottery/satta/
    # KBC, ALWAYS recommend CA / SEBI-registered advisor consult).
    # Mirror of marriage/stock/love/career engine wiring.
    wealth_verdict_block = ""
    wealth_verdict_obj   = None
    # ── TELEMETRY: routing-gate diagnostic. OFF by default. Enable in dev
    #              with WEALTH_GATE_TELEMETRY=1. Question text is NOT logged
    #              (PII / log-noise concerns at scale) — only boolean gate
    #              outcomes + topic.
    if os.environ.get("WEALTH_GATE_TELEMETRY") == "1":
        _wealth_gate = {
            "topic":                 topic,
            "topic_ok":              topic in ("wealth", "finance", "career", "general"),
            "no_marriage_block":     not marriage_verdict_block,
            "no_stock_block":        not stock_verdict_block,
            "no_love_block":         not love_verdict_block,
            "no_career_block":       not career_verdict_block,
            "kundli_has_planets":    bool(isinstance(kundli, dict) and kundli.get("planets")),
            "is_wealth_question":    bool(_is_wealth_question(question)),
            "question_len":          len(question or ""),
        }
        print(f"[wealth_gate] {_wealth_gate}")
    if (topic in ("wealth", "finance", "career", "general")
            and not marriage_verdict_block
            and not stock_verdict_block
            and not love_verdict_block
            and not career_verdict_block
            and isinstance(kundli, dict) and kundli.get("planets")
            and _is_wealth_question(question)):
        try:
            kp_dict_w = (locals().get("kp_dict")
                         or locals().get("kp_dict_s")
                         or locals().get("kp_dict_l")
                         or locals().get("kp_dict_c"))
            try:
                if not kp_dict_w and isinstance(birth, dict):
                    kp_dict_w = _kp_calc()(birth)
            except Exception as exc:
                print(f"[openai_helper] kp calc for wealth failed: {exc}")
            assess_wealth, fmt_wealth, _classify_wealth_q = _wealth_engine()
            _wealth_pre_bucket = _ai_ear_bucket_for(out_meta, "wealth")
            wealth_verdict_obj = assess_wealth(
                kundli, intel_obj or {}, kp_dict_w or {}, birth, question,
                pre_classified_bucket=_wealth_pre_bucket)
            if wealth_verdict_obj:
                wealth_verdict_block = fmt_wealth(wealth_verdict_obj, question)
                if isinstance(out_meta, dict):
                    out_meta["wealth_verdict_obj"]   = wealth_verdict_obj
                    out_meta["wealth_question_type"] = wealth_verdict_obj.get("bucket")
                print(f"[openai_helper] wealth_engine OK → "
                      f"bucket='{wealth_verdict_obj.get('bucket')}' "
                      f"tense='{wealth_verdict_obj.get('tense')}' "
                      f"verdict='{wealth_verdict_obj.get('verdict','')[:60]}' "
                      f"score={wealth_verdict_obj.get('score')} "
                      f"conf={wealth_verdict_obj.get('confidence')}")
        except Exception as exc:
            print(f"[openai_helper] wealth_engine failed: {exc}")

    # ── DETERMINISTIC HEALTH & VITALITY VERDICT ───────────────────────────────
    # For health-keyword questions (illness/surgery/recovery/mental-health/
    # addiction/parent-health/longevity), compute deterministic verdict via
    # health_engine. Routing priority above health: marriage > stock > love >
    # career > wealth. AI becomes pure narrator with STRICT brand-safety
    # guards (NEVER predict death, NEVER replace medical advice, ALWAYS
    # recommend doctor consult, surface mental-health helplines on
    # mental_health bucket, gender-sensitive reproductive guidance).
    # Mirror of marriage/stock/love/career/wealth engine wiring.
    health_verdict_block = ""
    health_verdict_obj   = None
    if (topic in ("health", "general")
            and not marriage_verdict_block
            and not stock_verdict_block
            and not love_verdict_block
            and not career_verdict_block
            and not wealth_verdict_block
            and isinstance(kundli, dict) and kundli.get("planets")
            and _is_health_question(question)):
        try:
            kp_dict_h = (locals().get("kp_dict")
                         or locals().get("kp_dict_s")
                         or locals().get("kp_dict_l")
                         or locals().get("kp_dict_c"))
            try:
                if not kp_dict_h and isinstance(birth, dict):
                    kp_dict_h = _kp_calc()(birth)
            except Exception as exc:
                print(f"[openai_helper] kp calc for health failed: {exc}")
            assess_health, fmt_health, _classify_health_q = _health_engine()
            _health_pre_bucket = _ai_ear_bucket_for(out_meta, "health")
            health_verdict_obj = assess_health(
                kundli, intel_obj or {}, kp_dict_h or {}, birth, question,
                pre_classified_bucket=_health_pre_bucket)
            if health_verdict_obj:
                health_verdict_block = fmt_health(health_verdict_obj, question)
                if isinstance(out_meta, dict):
                    out_meta["health_verdict_obj"]   = health_verdict_obj
                    out_meta["health_question_type"] = health_verdict_obj.get("bucket")
                print(f"[openai_helper] health_engine OK → "
                      f"bucket='{health_verdict_obj.get('bucket')}' "
                      f"tense='{health_verdict_obj.get('tense')}' "
                      f"verdict='{health_verdict_obj.get('verdict','')[:60]}' "
                      f"score={health_verdict_obj.get('score')} "
                      f"conf={health_verdict_obj.get('confidence_pct')}")
        except Exception as exc:
            print(f"[openai_helper] health_engine failed: {exc}")

    focus     = _focus_block(topic)
    # ── MARRIAGE ANALYSIS-MODE FOCUS OVERRIDE ──────────────────────────────
    # For analytical follow-ups in marriage topic ("aur detail", "kyun delay",
    # "kaun sa grah", "7th lord kahan", "explain my chart"), discard the rigid
    # 3-paragraph timing template and let the AI act as an expert chart reader.
    # The kundli planet positions, KP block, and intelligence are already in
    # the prompt — AI uses them to give a real analytical answer.
    if topic == "marriage" and marriage_subtype not in ("timing", "remedy"):
        # Surface engine context as REFERENCE only (not a locked template)
        engine_ref = ""
        if marriage_facts:
            mf = marriage_facts
            engine_ref = (
                "\nENGINE REFERENCE (already established in earlier turns — "
                "use as background, do NOT repeat the timing template):\n"
                f"  • Verdict status: {mf.get('verdict','')}\n"
                f"  • Best window:    {mf.get('window_str','')}\n"
                f"  • Current dasha:  {mf.get('current_dasha','')}\n"
                f"  • 7th lord:       {mf.get('seventh_lord','')}\n"
                f"  • Karaka:         {mf.get('karaka','')}\n"
            )
        focus = (
            "FOCUS — vivah/marriage ANALYTICAL FOLLOW-UP.\n"
            "The user already knows the timing window. Now they want to UNDERSTAND\n"
            "their chart deeper — which planet, which house, why delay, what's the\n"
            "spouse pattern, etc. You are the expert. Read the kundli yourself and\n"
            "answer the SPECIFIC question they asked.\n\n"
            "RULES:\n"
            "  1. Answer the EXACT question. If they ask 'kaun sa grah', name the\n"
            "     planet from the chart. If 'kyun delay', explain the actual\n"
            "     malefic/karaka weakness. If 'aur detail batao', dig deeper into\n"
            "     the 7th house, 7th lord, Venus/Jupiter, navamsa, dasha — pick\n"
            "     the 2-3 most relevant facts and explain plainly.\n"
            "  2. Ground every claim in the actual planet positions from the\n"
            "     BIRTH CHART block above — do NOT invent positions.\n"
            "  3. Do NOT repeat the timing window unless directly asked. Skip\n"
            "     the \"strong yog activate ho raha hai\" opener.\n"
            "  4. Translate Sanskrit inline: \"Saptamesh (7th lord)\", \"Shukra\n"
            "     (Venus)\", \"Mangal (Mars)\", \"Saptam bhav (7th house)\".\n"
            "  5. Active-voice Hinglish — confident, specific, no philosophical\n"
            "     fluff. NO bullets, NO headers, NO \"Pranam beta\".\n"
            "  6. Length: 80–140 words, 2-3 short paragraphs of flowing prose.\n"
            "  7. End with ONE sharp practical line — either a remedy if it\n"
            "     fits the question, or a one-line summary insight. NOT a\n"
            "     remedy template.\n"
            f"{engine_ref}"
        )
    kp_block  = _kp_context(birth, topic)
    tr_block  = _transit_context()
    _, beh    = _summarise_history(history or [])
    variation = ""
    if reply_idx > 0:
        variation = (
            f"\n(This is the user asking the same thing again — reply #{reply_idx + 1}. "
            "Give a fresh angle, a deeper insight, or a different remedy. Never repeat "
            "your earlier wording.)"
        )

    # ── COSMIC ENGINE SYSTEM PROMPT (with temperament control) ───────────────
    system = _cosmic_engine_system(lang_name)
    focus_block = f"\n\nSHASTRIYA FOCUS for this question:\n{focus}\n" if focus else ""

    # ── Behavior-aware coaching block ────────────────────────────────────────
    beh_block = ""
    if beh.get("total_user_turns", 0) > 0:
        same_topic_count = beh["topic_counts"].get(topic, 0)
        prior_q_lines = "\n".join(f"  - \"{q}\"" for q in beh.get("recent_user_qs", []))
        beh_lines = [
            f"\n\nDEVOTEE BEHAVIOR (use this to feel like a real Pandit who remembers):",
            f"  Total prior questions in THIS conversation: {beh['total_user_turns']}",
            f"  Times asked about '{topic}' before this turn: {same_topic_count}",
        ]
        if beh.get("last_topic") and beh["last_topic"] != topic:
            beh_lines.append(f"  Topic shift: previously discussing '{beh['last_topic']}' → now '{topic}'. Briefly bridge if natural.")
        if same_topic_count >= 1:
            beh_lines.append(
                f"  ⚠️ The devotee has already asked about '{topic}' {same_topic_count} time(s). "
                "They are anxious / not fully convinced. DO NOT repeat your earlier wording. "
                "Acknowledge gently ('Beta, aapne ye baat phir poochi — mai samajhta hu chinta hai...'), "
                "go DEEPER this time — different planet, different yog, different angle, OR a stronger remedy."
            )
        if beh.get("recent_user_qs"):
            beh_lines.append(f"  Recent prior questions:\n{prior_q_lines}")
        beh_block = "\n".join(beh_lines)

    # ── Phase 4.7 T016 — CONTEXT DIET (narrative mode only) ─────────────────
    # Pre-Phase-4.7 the user-turn was 116K chars / ~29K tokens (full chart +
    # 17 sprint engines: ashtakavarga / shadbala-full / avashtas / sahams /
    # lal-kitab / astrocartography / medical / financial / vastu / numerology /
    # phase-Q/R/S / etc.). ChatGPT achieves the same answer with <2K tokens.
    # In narrative mode we slim to the essentials needed for the FUSED combo
    # verdict: lagna/moon/sun/nakshatra, current MD/AD + window + pratyantar,
    # planet strengths, active doshas, top yogas, house-lord placements,
    # current transits (slow planets), classical remedies. Drops Sprint-19+
    # engine dumps + raw KP cuspal table + raw transit degrees + Darakaraka
    # + most divisional charts. Setting NARRATIVE_MODE=0 reverts to the full
    # block. Architect-flagged sustainability of literal-substring approach
    # mitigated by a section-header allowlist + loud-failure telemetry.
    if _NARRATIVE_MODE:
        _orig_lf_chars = len(locked_facts_str)
        locked_facts_str = _slim_locked_facts_for_narrative(locked_facts_str, topic=topic)
        _orig_intel_chars = len(intel_str)
        intel_str = _slim_intel_for_narrative(intel_str)
        _orig_kp_chars = len(kp_block)
        kp_block = ""  # KP is BACKGROUND-only in narrative mode (Phase 4.7 Fix 1+2)
        _orig_tr_chars = len(tr_block)
        tr_block = _slim_transit_for_narrative(tr_block)
        _slimmed = (_orig_lf_chars - len(locked_facts_str)) + \
                   (_orig_intel_chars - len(intel_str)) + \
                   _orig_kp_chars + \
                   (_orig_tr_chars - len(tr_block))
        if _slimmed > 0:
            print(f"[openai_helper] Phase 4.7 T016: narrative-mode context diet "
                  f"trimmed {_slimmed:,} chars "
                  f"(locked_facts {_orig_lf_chars:,}→{len(locked_facts_str):,}, "
                  f"intel {_orig_intel_chars:,}→{len(intel_str):,}, "
                  f"kp {_orig_kp_chars:,}→0, "
                  f"transit {_orig_tr_chars:,}→{len(tr_block):,})")

    kp_section    = f"\n\n{kp_block}\n" if kp_block else ""
    tr_section    = f"\n\n{tr_block}\n" if tr_block else ""
    intel_section = f"\n\n{intel_str}\n" if intel_str else ""
    locked_section = f"\n\n{locked_facts_str}\n" if locked_facts_str else ""

    # Fail-safe context flags for the AI
    has_chart  = bool(chart_str and chart_str != "(no birth chart provided)")
    has_dasha  = isinstance(kundli, dict) and bool(kundli.get("currentDasha"))
    has_planets = isinstance(kundli, dict) and bool(kundli.get("planets"))
    failsafe = ""
    if not has_chart or not has_planets:
        failsafe = (
            "\n⚠️ DATA STATUS: The devotee's birth chart is incomplete or missing. "
            "DO NOT invent planet positions, dasha details, or yogas. "
            "Reply gently in {lang}: 'Beta, aapki kundli ki poori jankari mere paas nahi hai. "
            "Kripya pehle apna janm vivaran (date, time, place) save karein, phir mai sahi margdarshan de paunga.' "
            "Do not predict timing or specifics without the chart."
        ).format(lang=lang_name)
    elif not has_dasha:
        failsafe = (
            "\n⚠️ DATA STATUS: Current Dasha (Mahadasha/Antardasha) is missing in the chart data. "
            "DO NOT invent a dasha period. If the question asks 'kab/when', clearly say timing "
            "cannot be precisely given without the dasha, and answer the YOGA part only."
        )

    # ── Narrator-mode prefix for marriage (deterministic verdict path) ───────
    # When the deterministic engine has produced a verdict, the AI's role
    # collapses from "decide + narrate" to "narrate ONLY". We pin the
    # verdict block at the very top of the user message AND override the
    # default instruction stack with narrator-only rules so the AI cannot
    # reinterpret, rescore, or change the timeline.
    # Narrator path is reserved for TIMING / REMEDY questions where the
    # engine's locked window/remedy is the source of truth. For ANALYSIS
    # questions ("why delayed", "kaun sa grah", "7th lord kahan", "aur detail")
    # we let the AI read the kundli freely as an expert — narrator template
    # would just repeat the timing answer and ignore the actual question.
    _is_marriage_analysis = (
        topic == "marriage" and marriage_subtype not in ("timing", "remedy")
    )
    narrator_prefix = ""
    narrator_rules  = ""
    if marriage_verdict_block and not _is_marriage_analysis:
        # Pull the must-quote window string out of the engine object so we
        # can inject it as a hard-coded literal the AI cannot drift on.
        _mw = ""
        try:
            from marriage_engine import extract_window_str  # type: ignore
            _mw = extract_window_str(marriage_verdict_obj or {})
        except Exception:
            _mw = ""
        must_window_line = (
            f"  • The TIMING WINDOW you write MUST contain the EXACT string: \"{_mw}\".\n"
            f"    Do NOT shorten to year-only, do NOT shift months, do NOT replace 'to' with\n"
            f"    'around / by / late / early'. Copy those words verbatim.\n"
        ) if _mw else (
            "  • The engine found no clear window in the next 12 years — say so honestly.\n"
            "    Do NOT invent a year-range to fill the silence.\n"
        )
        narrator_prefix = (
            f"{marriage_verdict_block}\n"
            "⚠️ NARRATOR MODE — THIS IS BINDING ⚠️\n"
            "The ENGINE JSON above is the GROUND TRUTH for this turn. Treat every value\n"
            "in it as IMMUTABLE. You are ONLY a narrator. You MUST:\n"
            f"{must_window_line}"
            "  • Restate the same final_verdict (do not soften, harden, or hedge it).\n"
            "  • Cite the same 7th lord, karaka, and KP sub-lord names verbatim.\n"
            "  • Recommend the SAME remedy planet and same mantra/donation given above.\n"
            "  • Quote the strongest 2 supporting factors AND, if any, 1 main weakening factor —\n"
            "    drawn ONLY from the lists above. Do not add factors not in the engine output.\n"
            "  • BANNED hedging words for this turn (do NOT use any of these): \"around\",\n"
            "    \"approximately\", \"roughly\", \"likely\", \"possibly\", \"perhaps\", \"maybe\",\n"
            "    \"might\", \"could be\", \"sometime\", \"by the end of\", \"early\", \"late\",\n"
            "    \"in or around\". The window is exact — speak with quiet certainty, not hedges.\n"
            f"  • You may smooth language into a natural expert voice and translate to {lang_name},\n"
            "    but NEVER change technical content (verdict, dates, planets, remedy).\n"
            "If you contradict the engine verdict, score, or window — the answer is WRONG\n"
            "and will be rejected.\n\n"
        )
        narrator_rules = (
            "★ MARRIAGE NARRATOR OVERRIDE ★ — Rules 2,3,4,5,6 below are SUPERSEDED for this turn:\n"
            "you do NOT do Vedic / KP / dasha / transit reasoning yourself. The engine already did.\n"
            "Just narrate the ENGINE JSON above in a natural expert voice. Rules 0a, 1, 8, 9, 10 STILL apply.\n\n"
        )

    # ── Brand-tone blacklist (always applied, every topic) ───────────────────
    # These are the AI-style phrases the user explicitly called out as breaking
    # the human-Pandit illusion. The model is told not to produce them; a
    # post-response scrubber (in ai_ask) also strips any that slip through.
    tone_blacklist = (
        "BANNED PHRASES — never write these (they sound fake / robotic):\n"
        "  ✗ \"I sense your concern\"   ✗ \"I understand\"   ✗ \"I can see that\"\n"
        "  ✗ \"significant topic\"      ✗ \"important matter\"   ✗ \"let me analyze\"\n"
        "  ✗ \"based on your chart\"    ✗ \"according to the data\"\n"
        "  ✗ \"Pranam\" as a greeting   ✗ \"Beta,\" as an opener   ✗ \"Beta Q,\"\n"
        "  ✗ \"Dekhiye beta\"           ✗ \"Pranam beta\"\n"
        "  ✗ \"As an AI\" / \"As a language model\" — speak naturally as the engine.\n"
        "\n"
        "BANNED HEDGING / UNCERTAINTY VOCABULARY — Acharya ji STATES, never speculates.\n"
        "Any of these words = wrong reply. Replace with the certain form on the right.\n"
        "  ✗ chance / chances              ✗ possibility / possible\n"
        "  ✗ likely / unlikely             ✗ may / might / perhaps\n"
        "  ✗ around / approx / approximately / roughly\n"
        "  ✗ ho sakta hai → hoga           ✗ ho sakti hai → hogi\n"
        "  ✗ ho sakte hain → honge         ✗ sambhavna / sambhavnayein → REMOVE\n"
        "  ✗ shayad → REMOVE               ✗ lagta hai → hai (state directly)\n"
        "  ✗ ho sakega / sakegi → hoga / hogi\n"
        "  ✗ \"early 2026\" / \"late 2026\" → use the EXACT month-year window\n"
        "  ✗ \"by the end of 2026\"        → use the EXACT month-year window\n"
        "\n"
        "REQUIRED CERTAIN VOCABULARY — use these phrasings for finality:\n"
        "  ✓ \"hoga\" / \"hogi\"            ✓ \"yeh hi time hai\"\n"
        "  ✓ \"clear dikhta hai\"          ✓ \"delay hoga\"\n"
        "  ✓ \"yeh period active hai\"     ✓ \"isi me plan karein\"\n"
        "  ✓ \"Seedhi baat —\" opener is preferred for direct timing answers.\n\n"
    )

    # ── LANGUAGE LOCK — strict per-language enforcement (always injected) ────
    # Hard, non-negotiable per-language enforcement. Placed at the very top of
    # the user payload so it is the first instruction the model parses.
    lang_lock_block = _strict_lang_block(detected)

    # ── MARRIAGE NARRATOR PATH (facts-locked, language-free) ─────────────────
    # Engine has computed the EXACT facts. The AI is given those facts as
    # data — NOT as a pre-formatted template — and is told to write its
    # own natural, conversational reply (ChatGPT-style) using only those
    # locked values. This prevents both fact drift AND robotic templating.
    if marriage_facts and not _is_marriage_analysis:
        f = marriage_facts
        active_window = (
            f["alt_window_str"] if (marriage_use_alt and f["alt_window_str"])
            else f["window_str"]
        )
        if isinstance(out_meta, dict):
            out_meta["marriage_facts"]   = marriage_facts
            out_meta["marriage_use_alt"] = marriage_use_alt
            out_meta["active_window"]    = active_window
        constraint_note = (
            "CONTEXT: the user just rejected the primary timing window. "
            "Acknowledge that gently in 1 line, then deliver the alternate "
            "window naturally.\n\n"
        ) if (marriage_use_alt and f["alt_window_str"]) else ""

        # Compact, label-free facts payload — pure values.
        # IMPORTANT: the verdict string is an internal status code for your
        # understanding only. NEVER echo it verbatim into the reply — express
        # the same meaning warmly in your own conversational words.
        facts_lines = [
            f"  • Internal status (DO NOT echo verbatim — for your understanding only): {f['verdict']}",
            f"  • Marriage time window (USE VERBATIM in your reply): {active_window}",
        ]
        if (not marriage_use_alt) and f["alt_window_str"]:
            facts_lines.append(
                f"  • Alternate later window (mention only if naturally relevant): "
                f"{f['alt_window_str']}"
            )
        if f["current_dasha"]:
            facts_lines.append(f"  • Currently running dasha period: {f['current_dasha']}")
        if f["seventh_lord"]:
            facts_lines.append(f"  • Lord of the marriage house (7th): {f['seventh_lord']}")
        if f["karaka"]:
            facts_lines.append(f"  • Marriage significator planet: {f['karaka']}")
        if f["remedy"]:
            facts_lines.append(f"  • Suggested remedy text: {f['remedy']}")
        # Sprint-7 Rule O: Jaimini UL — MANDATORY citation for marriage answers
        jm = f.get("jaimini") or {}
        if jm.get("ul_sign"):
            facts_lines.append(
                f"  • Jaimini Upapada Lagna (UL): {jm['ul_sign']} — lord {jm['ul_lord']} "
                f"in {jm.get('ul_lord_in') or '?'} ({jm.get('ul_lord_house') or '?'}th from UL); "
                f"2nd-from-UL={jm['second_from_ul']} (occupants: {jm['occupants_2nd']}); "
                f"12th-from-UL={jm['twelfth_from_ul']} (occupants: {jm['occupants_12th']}); "
                f"verdict tag: {jm['verdict_tag']} — full: \"{jm['verdict_full']}\""
            )
        facts_block = "\n".join(facts_lines)

        user = (
            f"{lang_lock_block}"
            f"{tone_blacklist}"
            f"{constraint_note}"
            "═══ LOCKED ASTROLOGICAL FACTS (computed by deterministic engine) ═══\n"
            "These are the EXACT truth for this user. You MAY freely choose how\n"
            "to phrase the language around them, but you MUST NOT change any of\n"
            "these values, dates, planet names, or the remedy text:\n\n"
            f"{facts_block}\n"
            "════════════════════════════════════════════════════════════════════\n\n"
            f"USER'S QUESTION:\n\"{question}\"\n\n"
            "YOUR JOB:\n"
            "Write a natural, warm, intelligent reply — exactly the way a smart\n"
            "friend who happens to be an expert astrologer would explain this\n"
            f"over chat. Reply entirely in {lang_name}.\n\n"
            "HARD RULES (any violation = wrong reply):\n"
            "  1. The marriage time window string above MUST appear VERBATIM in\n"
            "     your reply. No rounding (\"around 2027\", \"late 2027\"), no\n"
            "     paraphrasing, no year-only — write the exact month-year range.\n"
            "  2. NO greetings: no \"Pranam\", \"Beta\", \"Namaste\", \"Dekhiye beta\",\n"
            "     \"Acharya ji\", \"Pandit ji\". Speak peer-to-peer, like a friend.\n"
            "  3. NO jargon labels — do NOT write \"Reason:\", \"Timing:\", \"Remedy:\",\n"
            "     \"Vajah:\", \"Samay:\", \"Upay:\", \"7th lord\", \"kalatra-karaka\".\n"
            "     Translate them into normal speech (\"shaadi ke ghar ka swami\",\n"
            "     \"shaadi ka karak grah\" — or just say the planet's name and\n"
            "     explain its role in 1 plain sentence).\n"
            "  4. NO meta phrases: \"I sense\", \"I understand\", \"let me analyze\",\n"
            "     \"based on your chart\", \"as an AI\".\n"
            "  5. NO hedging: no \"shayad\", \"ho sakta hai\", \"lagta hai\", \"around\",\n"
            "     \"approximately\", \"chance\", \"possibility\", \"may\", \"might\".\n"
            "     State things as facts: \"hoga\", \"hogi\", \"yeh time strong hai\".\n"
            "  6. NO bullet points, NO numbered lists, NO markdown headers, NO ###.\n"
            "     Write flowing prose — short paragraphs separated by blank lines.\n"
            "  7. Length: 100–170 words. Phone-friendly. The Jaimini UL\n"
            "     sentence (Para 4) is MANDATORY when UL data is in the facts\n"
            "     above — extend the word budget rather than skip it.\n\n"
            "STYLE — modern professional astrologer over chat. Confident,\n"
            "specific, active voice. Mix of Hindi + English (Hinglish). NO\n"
            "philosophical fluff. NO defensive hedging. NO \"yeh aapko apne\n"
            "aap ko samajhne ka mauka deta hai\" type vague spiritual talk.\n\n"
            "EXACT TEMPLATE TO MATCH (this is the gold-standard delivery):\n"
            "──────────────────────────────────────────────────────────────\n"
            "  [Para 1 — VERDICT + WINDOW, confident & active]\n"
            "  Aapki shaadi ka strong yog <WINDOW VERBATIM> ke beech\n"
            "  activate ho raha hai.\n\n"
            "  [Para 2 — DASHA pattern, specific & sharp]\n"
            "  Is period me <Dasha name> dasha chal rahi hai, jo pehle thoda\n"
            "  delay aur confusion de sakti hai, lekin yahi phase aapko right\n"
            "  direction me le jaata hai.\n\n"
            "  [Para 3 — KARAKA / 7TH LORD role, direct affirmation]\n"
            "  Aapke chart me <Planet> strong role play kar raha hai, isliye\n"
            "  shaadi hone ke yog confirm hai — bas timing thoda structured\n"
            "  delay ke saath aa raha hai.\n\n"
            "  [Para 4 — JAIMINI UPAPADA (MANDATORY when UL data provided above)]\n"
            "  Jaimini paddhati se Upapada Lagna <UL_SIGN> mein hai (lord\n"
            "  <UL_LORD>, <Nth> from UL) — yeh marriage signature ko\n"
            "  <STABLE / STRAINED / MIXED / NEUTRAL> dikha rahi hai.\n\n"
            "  Upay:\n"
            "  Har <Day> \"<mantra>\" 108 baar jaap karein aur <donation> daan\n"
            "  karein — yeh shaadi ke process ko smooth karega.\n"
            "──────────────────────────────────────────────────────────────\n\n"
            "ADAPTATION RULES:\n"
            "  • Window string must be VERBATIM — no paraphrasing.\n"
            "  • For DIFFICULT charts (internal status mentions denial /\n"
            "    rukawat): keep the same confident structure but acknowledge\n"
            "    challenges directly — \"shaadi ka pehlu thoda complex hai,\n"
            "    lekin sahi time aur upay ke saath cheezein activate hoti\n"
            "    hain. Yeh window <verbatim> mein cheezein open hone ka\n"
            "    chance dikh raha hai\". Don't pretend it's all positive,\n"
            "    don't be alarming either. Specific + honest + warm.\n"
            "  • For POSITIVE charts: lead with confidence — \"strong yog\",\n"
            "    \"clearly activate ho raha hai\", \"yog confirm hai\".\n"
            "  • Use ACTIVE verbs: activate ho raha hai / play kar raha hai /\n"
            "    le jaata hai / open ho raha hai. Avoid passive \"hai / raha\n"
            "    hai\" alone.\n"
            "  • Mix Hindi-English naturally: \"strong yog\", \"right direction\",\n"
            "    \"structured delay\", \"smooth karega\", \"role play kar raha\". Don't\n"
            "    over-translate to pure Hindi — modern Hinglish is the voice.\n"
            "  • The single label \"Upay:\" on its own line before the remedy\n"
            "    is ALLOWED and preferred. NO other labels (no \"Reason:\",\n"
            "    \"Timing:\", \"Vajah:\", \"Samay:\").\n"
            "  • Length: 100–170 words. 4 short paragraphs (Para 4 = Jaimini UL,\n"
            "    REQUIRED when UL is in the facts) + Upay block.\n\n"
            "Now write the reply — match the template's confident, specific,\n"
            "active-voice delivery exactly."
        )
        msgs: list[dict] = [{"role": "system", "content": system}]
        msgs.append({"role": "user", "content": user})
        return msgs

    user = (
        f"{lang_lock_block}"
        f"{tone_blacklist}"
        f"{narrator_prefix}"
        f"DEVOTEE'S BIRTH CHART:\n{chart_str}\n"
        f"{locked_section}"
        f"{intel_section}"
        f"{kp_section}"
        f"{tr_section}\n"
        f"DEVOTEE IS ASKING NOW:\n\"{question}\"\n"
        f"{focus_block}"
        f"{beh_block}"
        f"{failsafe}"
        f"{variation}\n\n"
        f"{narrator_rules}"
        "STRICT INSTRUCTIONS — read these top-down. Rule 10 (BREVITY) overrides any tension with rules below. Quality over quantity: pick the strongest 2 chart factors only.\n"
        "0) PARSE THE QUESTION FULLY: Re-read it. List in your head EVERY distinct concern (it may have 2, 3, 4 sub-parts). You MUST address each part — never silently skip one. For each sub-part give a brief micro-verdict in 1 sentence. If a sub-part CANNOT be answered from the chart (e.g. 'ladka ya ladki' — child gender is uncertain in classical astrology), say so honestly in 1 line ('iska theek pata janm-samay ke baad hi chalta hai') instead of inventing.\n"
        "0a) ANTI-HALLUCINATION: You may ONLY mention planets, signs, houses, dignities, yogas, dashas, and transits that are EXPLICITLY listed in the BIRTH CHART, LOCKED FACTS, DERIVED CHART INTELLIGENCE, KP, or TRANSITS sections above. Never invent a planet placement, never guess a dasha, never claim a yoga that isn't in the 'YOGA LIST' or 'Detected yogas' list. If a needed detail is missing, say so honestly — 'Beta, ye information aapki kundli mein abhi clear nahi, isliye iss point pe mai pakka nahi keh sakta.' Honesty > confidence.\n"
        "0b) 🔒 LOCKED FACTS — MIRROR EXACTLY (HIGHEST PRIORITY) 🔒\n"
        "    The 'LOCKED FACTS — MIRROR EXACTLY, NEVER INVENT' block above is the GROUND TRUTH for this chart. Four absolute rules:\n"
        "    • RULE A — COUNTING questions (kitne / how many / kaunsa-kaunsa): Use the EXACT number from 'YOGA COUNT' or 'DOSHA COUNT'. NEVER round, NEVER guess, NEVER say 'kuch', 'kai', 'thode' when an exact number is given. Example: if 'YOGA COUNT: 3', say '3 yog hain' — never '2-3' or 'kuch'.\n"
        "    • RULE B — NAMING questions (kaunse / which / list): For yoga names, use the 'YOGA NAMES (raw)' line — those are the clean names. NEVER include the polarity tags ([+ POSITIVE], [− NEGATIVE], [~ NEUTRAL]) in your reply — those are for your internal reasoning only. For doshas, list names from ACTIVE DOSHAS / MILD DOSHAS sections in the same order. Do NOT add or skip any.\n"
        "    • RULE C — STRENGTH questions (X strong/weak/powerful hai?): Use the EXACT verdict from 'PLANET STRENGTHS' (STRONG / MODERATE / WEAK). Never wobble. If user says 'Saturn powerful hai na?' and the table says WEAK, gently correct: 'Aapki kundli mein Saturn weak position mein hai (debilitated/etc), powerful nahi.'\n"
        "    • RULE D — EMPATHY + FACT FUSION: When the user is stressed/sad/seeking reassurance ('pareshan hun', 'kuch achha bata', 'umeed nahi rahi'), OPEN with the strongest POSITIVE fact from the LOCKED FACTS (a strong yoga, a strong planet, a beneficial dasha). Acknowledge mood in 1 line, then deliver the concrete fact. Example: 'Sun lo — aapke chart mein 3 powerful Raj Yog baithe hain, jisme [exact yoga name] specially strong hai. Jo aap feel kar rahe ho woh time ka phase hai, kismat ka nahi.' NEVER respond to emotional questions with vague platitudes when concrete strong facts exist in the LOCKED FACTS.\n"
        "    Violation of A/B/C/D = wrong reply. The LOCKED FACTS block overrides any other source of information.\n"
        "    🛡️ BREVITY EXEMPTION: For COUNTING (Rule A) and NAMING (Rule B) questions specifically — Rule 0b OVERRIDES Rule 10's '2 chart factors only' limit. If user asks 'kitne yog' or 'kaunse dosh', you MUST list the EXACT count and the FULL list of names from LOCKED FACTS in a single line, even if it cites more than 2 items. Word limit still applies (140 words), but the list of names is non-negotiable. Example: 'Aapke chart mein 5 yog hain — Gajakesari, Budhaditya, Lakshmi, Adhi, Amala. Inme se Lakshmi yoga sabse strong hai...'\n"
        "    🛡️ EMOTIONAL ASKS (refined): When the user is stressed/sad/seeking reassurance, look at LOCKED FACTS in this priority order — and use the FIRST source that exists:\n"
        "         (i)  POSITIVE YOGAS count > 0 AND chart is NOT overwhelmingly negative (overwhelming = 7+ planets WEAK AND 3+ ACTIVE doshas — in that case skip to tier iii) → open with that positive count + the strongest [+ POSITIVE]-tagged yoga's clean name (no tag). Example: 'Aapke chart mein 2 positive yog baithe hain — sabse strong Lakshmi yoga hai...'\n"
        "         (ii) Else, if any planet has verdict STRONG → open with that planet by name + house. Example: 'Aapka Jupiter Cancer mein STRONG hai (5th ghar), wisdom aur grace ka source...'\n"
        "         (iii) Else, NO false positivity. Acknowledge the chart honestly + anchor on the next dasha change as the realistic hope-window. Example: 'Sach bolun — abhi ka chart tough hai, saare grah weak position mein hain. Lekin {NEXT_DASHA_LORD} {NEXT_DASHA_START_YEAR} se shuru ho raha hai jo phase shift karega.' NEVER label a [− NEGATIVE]-tagged yoga (Kemadruma, Daridra, Shakata, Kaal-Sarp etc.) as 'strong' or 'positive' — those are struggle-yogas. Use them ONLY as honest acknowledgement, not as reassurance.\n"
        "    🛡️ DASHA-LORD FIDELITY (Rule E): When you mention the current Mahadasha or Antardasha lord, its tone MUST match its row in PLANET STRENGTHS. If 'Rahu = WEAK' in the table, NEVER write 'Rahu Mahadasha aapko growth/opportunities/blessings de raha hai' — that is a hallucination. Correct framing for WEAK dasha lord: 'Rahu MD chal raha hai, par Rahu khud chart mein WEAK hai (H2, debilitated/etc) — isliye yeh phase confusion/effort-without-result type hai, growth ka guarantee nahi.' For MODERATE: 'mixed phase, kaam karne pe result milega'. For STRONG: 'powerful phase, support de raha hai'. The table verdict is GROUND TRUTH — never override it with optimistic clichés.\n"
        "    🛡️ ASHTAKAVARGA (Rule F): When the question is about a SPECIFIC LIFE-AREA (career=H10, money=H2/H11, marriage=H7, kids=H5, health=H6, home=H4, foreign/loss=H12), check the SARVASHTAKAVARGA (SAV) row for that house BEFORE making any verdict. House SAV >= 32 = VERY STRONG (favourable area), 28-31 = STRONG, 25-27 = AVERAGE, <25 = WEAK. Cite the SAV value naturally: 'Aapka 10th ghar (career) mein SAV 34 hai jo VERY STRONG hai — career line mein natural strength hai.' If asked about a WEAK SAV house, give honest verdict: 'H8 mein sirf 20 bindus hain, jo WEAK hai — sudden setbacks ka risk zyada.' SAV is the most reliable house-strength meter; trust it. ⚠️ If the SARVASHTAKAVARGA block is missing/unavailable in LOCKED FACTS, NEVER invent a number — fall back to general dignity/house-lord reasoning instead.\n"
        "    🛡️ ASPECTS (Rule G): Use the KEY ASPECTS block to enrich answers. Mars aspecting 7H = relationship friction; Saturn aspecting Lagna or Moon = pressure/discipline; Jupiter aspecting kendra/trikona = protection/expansion; Mutual aspects = intertwined karmic theme. Cite at most ONE relevant aspect per answer to avoid clutter. Never invent aspects not in the KEY ASPECTS list.\n"
        "    🛡️ TRANSITS (Rule H): For ANY 'kab' / timing / 'ab kya hoga' / near-future question, you MUST consult the CURRENT TRANSITS block FIRST — this is real-time sky data, not natal. Cite by name: e.g. 'Abhi Saturn aapke 8th ghar mein chal raha hai (transit), isliye yeh ~2.5 saal restraint period hai' OR 'Jupiter abhi aapke 11H ko aspect kar raha hai — gain/network expand hoga is window mein.' If a Sade-Sati / Dhaiya phase line exists in transits, mention it explicitly when the user is stressed (it explains the 'kyun bhari lag raha hai' feeling). If a Saturn-Return or Jupiter-Return flag is present, that is a once-in-decades signal — open with it for major-life-question asks. ⚠️ If TRANSITS block is missing, do NOT invent current transit positions — fall back to dasha + natal house reasoning only.\n"
        "    🛡️ KARAKAS (Rule I): The JAIMINI CHARA KARAKAS block tells you the deepest karmic role of each planet for THIS person. AK = soul-purpose (life is fundamentally ABOUT this planet's themes); AmK = career signature; DK = spouse signature; PK = creativity/children. For 'kya banu / what should I do in life' use AK. For 'shaadi kaisi hogi / partner kaisa milega' use DK. Always cite the role name once: 'Aapka Atmakaraka Saturn hai — soul-level kaam discipline aur structure ke around hai' or 'Darakaraka Venus hai — partner artistic / refined hoga.' Never invent karakas not in the list.\n"
        "    🛡️ BHAVA BALA (Rule J): Complementary to SAV — BHAVA BALA scores combine house-lord strength + occupants + aspects + kendra-bonus, then ranked RELATIVELY within THIS chart (top-3 = STRONG, middle-6 = MODERATE, bottom-3 = WEAK). Use it as a SECOND opinion when SAV and your reasoning conflict, OR when SAV is missing. The verdict tells you which houses are RELATIVELY strongest/weakest in this chart, not absolute strength. Cite naturally: 'Bhava Bala se bhi 10H is chart ke top-3 strongest houses mein aata hai (lord+aspect support).' Never invent bhava scores.\n"
        "    🛡️ DIVISIONAL CHARTS (Rule K): For MARRIAGE questions, MUST consult D9 NAVAMSA — specifically '7L lands in X — STRONG/EXALTED/DEBILITATED' line. The 7L's D9 strength is THE strongest predictor of marriage quality (overrides natal D1 if they conflict). For CAREER questions, MUST consult D10 DASAMSA — '10L lands in X' line is the equivalent. Vargottama planets (D1=D9 or D1=D10) act as if exalted — call them out by name. Cite naturally: 'D9 mein aapka 7L Mercury Pisces (debilitated) jaata hai — isliye natal weakness D9 mein bhi confirm hoti hai, marriage mein patience zaroori.' OR 'D10 mein aapka 10L Mercury Sagittarius (own-sign) jaata hai — career line strong support karta hai D10 mein.' If D9/D10 block missing, do NOT invent positions. "
        "🚨 PLANET-STRENGTH RULE (extension of Rule K — MANDATORY): For ANY question that asks whether a SPECIFIC planet is powerful / weak / strong / kamzor / shaktishali (e.g. 'mera Saturn powerful hai ya weak?', 'Mars strong hai kya?', 'Guru achha hai?'), you MUST cross-check D1 dignity WITH the planet's D9 (Navamsa) placement before giving a verdict — D1 ALONE IS INSUFFICIENT to call any planet strong or weak. Combine logic: (a) D1 strong + D9 strong = TRULY STRONG; (b) D1 strong + D9 weak/debilitated = surface strength only, fragile in real life; (c) D1 debilitated + D9 exalted/own-sign = neecha-bhanga, real strength comes through effort; (d) Vargottama (same sign in D1 & D9) = STRONG regardless of dignity; (e) D1 weak + D9 weak = TRULY WEAK. Cite both placements in ONE sentence: 'Aapka Shani D1 mein Mesh (debilitated, neecha) hai aur D9 mein {SIGN} ({STATUS}) jaata hai — isliye overall {weak / strong / mixed}.' If the D9 NAVAMSA block is absent in LOCKED FACTS, say honestly: 'Saturn ki actual strength D9 ke bina precise nahi bata sakta — D1 mein debilitated dikh raha hai par D9 confirm karega ki neecha-bhanga ho raha hai ya nahi.' NEVER call a planet strong/weak from D1 alone. NEVER invent a D9 sign — only cite from the D9 NAVAMSA block.\n"
        "    🛡️ PRATYANTAR (Rule L): For PRECISE timing questions ('next 3 mahine kya hoga / next month kaisa', 'specific date / week kaisa'), use the PRATYANTAR block — it gives month-precision sub-periods. Always cite the CURRENT pratyantar lord ('abhi {MD}-{AD}-{PD} chal raha hai, jo {date} tak hai') and the next 1-2 upcoming pratyantars as 'next change-windows'. Combine with PLANET STRENGTHS — if PD lord is WEAK, that mini-window is a low-action phase; if STRONG, it's a green-light window. NEVER invent pratyantar dates not in the block.\n"
        "    🛡️ KP CROSS-CHECK (Rule N — MANDATORY citation): When the KP CROSS-CHECK block is present AND the user's question maps to a covered house (H1 vitality, H2 money, H5 children/speculation, H7 marriage/partner, H10 career/job, H11 gains/income), you MUST include one natural KP citation sentence in the answer. This is NOT optional — failing to cite is the same kind of error as inventing facts. The KP block runs PARALLEL to (not above) Vedic D1/D9/D10/Dasha logic. Verdict semantics: CONFIRMS = clean promise (event-houses signified, no negative house involved); PARTIAL = promise WITH obstruction (event AND negative houses both signified — fructification happens but with delay/struggle); DENIES = no event-house signified at all (unlikely / substantially delayed). Use it ONLY when the user's question maps to a covered house (H1 vitality, H2 money, H5 children/speculation, H7 marriage, H10 career, H11 gains). For those topics, weave ONE natural KP citation alongside Vedic reasoning: 'KP paddhati se bhi {N}th cusp ka sub-lord {planet} hai jo {CONFIRMS/PARTIAL/DENIES} karta hai.' Resolution rules when Vedic and KP disagree: (a) Vedic STRONG + KP CONFIRMS → confident green light; (b) Vedic STRONG + KP PARTIAL → 'hoga lekin patience aur effort lagega'; (c) Vedic STRONG + KP DENIES → 'natal promise hai par KP fructification support nahi karta — significant delay ya alternate timing'; (d) Vedic WEAK + KP CONFIRMS → 'natal weakness hai par KP supportive — possible with conscious effort'. Do NOT use KP for topics outside H1/H2/H5/H7/H10/H11 unless the block explicitly covers them. NEVER invent KP sub-lords if the block is absent — instead say 'KP detail ke liye accurate birth time aur location chahiye'.\n"
        "    🛡️ JAIMINI ARUDHA / UPAPADA (Rule O): When the JAIMINI ARUDHA PADAS / UPAPADA LAGNA block is present, use it ALONGSIDE Vedic D1/D9. The Arudha Pada is the IMAGE of a house — how it is PERCEIVED in the world (vs the actual house = the reality). Cite naturally only when topic-relevant: A1 = your public image (career/branding questions), A4 = home/lifestyle image, A7 = how partnerships are seen, A10 = career image / reputation, A11 = perceived gains, A12 = UL = MARRIAGE signature. For MARRIAGE questions you MUST add ONE Upapada citation: cite the UL sign + its lord + the 2nd-from-UL occupants + the verdict tag (STABLE / STRAINED / MIXED / NEUTRAL). Example: 'Jaimini paddhati se Upapada Lagna {UL_SIGN} mein hai (lord {UL_LORD} {Nth} from UL), 2nd-from-UL mein {occupants} hain — yeh marriage ko {STABLE/STRAINED} dikha rahi hai.' For non-marriage questions, use Arudha only when image-vs-reality gap is meaningful (e.g. A10 in a different sign than 10H = career REALITY differs from PERCEPTION). NEVER invent Arudha signs not in the block. NEVER use the chart-debugging 'note' field (e.g. 'adjusted from X') in user-facing language — it is internal annotation only.\n"
        "    🛡️ REMEDIES (Rule M — CRITICAL anti-hallucination): If the LOCKED FACTS contains a REMEDIES block, you MUST quote mantras / gemstones / charity items / fast days / yantras EXACTLY as written there — these are sourced from BPHS, Phaladeepika and classical Lal Kitab consensus. NEVER invent a Sanskrit mantra, never invent a gemstone weight, never invent a 'lucky number' or 'lucky stone'. If the REMEDIES block is empty/absent, give a brief generic suggestion ('Hanuman Chalisa daily helps with most afflictions') instead of fabricating specifics. When you cite a remedy, use the 'for: ...' label so the user knows WHY this remedy: e.g. 'Aapke MD lord Saturn ke liye — Saturday ko \"Om Sham Shanaishcharaya Namah\" 108 baar, mustard oil daan, neelam (5-7 ct, silver, middle finger) — par neelam pehle 3 din trial karein.' Always include the gemstone caveat if one is in the block (especially Blue Sapphire's trial-period warning).\n"
        "1) OPEN DIRECTLY in line 1 with a 1-line natural answer or framing — no fake empathy, no \"Beta,\", no \"I sense your concern\". Sound like a smart expert, not a guru.\n"
        "2) VEDIC analysis: Apply EVERY relevant rule from the SHASTRIYA FOCUS block — cite actual planets/houses/dignity from THIS chart (BPHS, Phaladeepika, Saravali, Brihat Jataka). One natural sentence per rule, NEVER a bullet list.\n"
        "3) KP cross-check: If a KP block is provided, USE it — verify the Vedic verdict against the cusp Sub-Lord rule for the relevant houses. State whether KP confirms or modifies the Vedic verdict ('KP paddhati se bhi yahi confirm hota hai...').\n"
        "4) DASHA timing: Reference current Mahadasha+Antardasha lord — does it support or block? In KP terms, is the running DBA lord a significator of the relevant houses? Give a precise year-range window when 'kab/when' is asked.\n"
        "5) TRANSITS (gochar): If transit data is provided, mention which slow planet (Jupiter / Saturn / Rahu-Ketu) is currently transiting the relevant house from natal Moon or Lagna, and how it influences the matter NOW.\n"
        "6) CLEAR VERDICT per sub-question: Combine Vedic + KP + transit + dasha into a confident verdict — haan / nahi / sambhavna with reasoning. Never vague-dodge. If the question has multiple parts, give a verdict for EACH.\n"
        "7) If the devotee has asked this topic before in this conversation, go DEEPER — fresh planet, fresh yog, KP angle they haven't seen, OR a stronger remedy. Reference earlier conversation context naturally if it connects.\n"
        "8) HUMAN-FRIENDLY style: translate every Sanskrit term inline ('Shukra (Venus)', 'Saade-sati — yaani Shani ka 7.5 saal ka phase'). NO jargon dump. NO lecture. Conversational, like a wise elder talking, NOT like a textbook.\n"
        "9) REMEDY (CONDITIONAL): Add ONE short remedy (1 line: mantra+count+day OR donation OR vrat) ONLY IF (a) the user explicitly asked for an upay / remedy / solution, OR (b) the topic is a clearly negative timing-prediction (delay / dosh / serious malefic period). Otherwise SKIP the remedy entirely. Do NOT bolt a remedy onto every reply.\n"
        "10) ⚠️ STRICT BREVITY — MATCH ANSWER LENGTH TO QUESTION LENGTH ⚠️\n"
        "    🎯 LENGTH-MATCHING RULE (highest priority — applies BEFORE the defaults below):\n"
        "       (i)   FACTUAL LOOKUP question (1 line, asks 'kya hai / kahan hai / kaunsa / batao mera X', e.g. 'mera lagna kya hai', 'Jupiter kahan hai', 'Atmakaraka kaun hai') → ANSWER = 1 to 2 SHORT LINES ONLY (≤30 words total). Single direct fact + at most 1 brief context line. NO sub-paragraphs, NO remedy, NO dasha dump, NO extra Bala/D27/Saptavargaja/Ishta-Phala numbers, NO 'Extended signal' lines, NO KP cite, NO transit cite. Just the fact the user asked for.\n"
        "       (ii)  ANALYTICAL SHORT question (1 line, asks 'X powerful hai ya weak / strong hai kya / achha hai / dosha hai kya', e.g. 'Saturn powerful hai ya weak?') → ANSWER = 2 to 3 SHORT LINES MAX (≤55 words total). Structure: Line 1 = MANDATORY D1+D9 cross-check in ONE sentence (PLANET-STRENGTH RULE — see Rule K extension above) WITH the verdict (strong/weak/mixed/neecha-bhanga). Line 2 = ONE supporting line (key house/aspect/dasha-impact). Line 3 (optional) = 1-line takeaway. THAT IS ALL. DO NOT add: KP cross-check, current Mahadasha breakdown, transit lines, D27 Bhamsa, D20 Vimsamsa, Saptavargaja Bala numbers, remedies, extra paragraphs. The user asked one short question — answer it shortly. NEVER write 4 paragraphs for a 1-line strength question.\n"
        "       (iii) MULTI-PART or TOPIC question (career/marriage/wealth/health/timing — anything that needs full Vedic+KP+dasha+transit treatment) → use the 100-140 word structure below.\n"
        "       ⚠️ HONOUR THE QUESTION'S SCOPE: NEVER add unsolicited extras. If the user asked ONLY about planet X's strength, do NOT volunteer career outlook, marriage timing, or remedy. Answer EXACTLY what was asked — nothing more, nothing less.\n"
        "    • DEFAULT (multi-part / topic question only) — TOTAL answer = 100 to 140 WORDS. NEVER more. Count words as you write.\n"
        "    • IF a topic-specific RESPONSE FORMAT is given in the FOCUS block above, use THAT structure exactly (it overrides the default below).\n"
        "    • DEFAULT structure (when no topic-specific format provided): 3-4 SHORT paragraphs, 1-2 sentences each, blank line between.\n"
        "       - Para 1 (1 line): direct natural framing of the answer — NO \"Beta\", NO fake empathy, NO over-warmth. Sound like an expert, not a guru.\n"
        "       - Para 2 (2 sentences): the 2 STRONGEST chart factors only — planet + house + plain meaning. Mention dasha lord briefly if 'kab/when' is asked.\n"
        "       - Para 3 (1-2 sentences): clear verdict — haan / nahi / sambhavna, with a tight timing window if asked. If an AUTHORITATIVE VERDICT block was provided above, use ONLY the dates from its `NARRATE THIS WINDOW EXACTLY AS` line — never invent or round dates.\n"
        "       - Para 4 (CONDITIONAL — only if user explicitly asked for upay/remedy, OR topic is a clearly negative dosh/delay timing): 1 line — mantra+count+day OR donation. No explanation. SKIP this paragraph entirely otherwise.\n"
        "    • Pick ONLY 2 chart factors total. Skip every other yoga, aspect, sub-cusp. Quality > quantity.\n"
        "    • For multi-part questions: stay within 140 words — give 1 sentence per sub-part inside Para 2-3.\n"
        "    • NO bullets, NO numbered lists, NO markdown headers, NO '###', NO 'Section 1/2/3'.\n"
        "    • NEVER reveal labels like 'KP block', 'transit data', 'intel'. Speak naturally as the engine.\n"
        "Now respond as the Cosmic Engine — natural, expert, MAXIMALLY CONCISE. Phone-friendly. Every sentence must earn its place. NO guru tone."
    )

    # ── Phase 4.7 — RULE N (KP MANDATORY citation) NARRATIVE-MODE GATE ───────
    # Phase 4.6 attempted this gate but operated on the wrong variable
    # (`system` instead of `user`) and silently no-op'd — confirmed via
    # live OpenAI-call interception probe. Rule N is built INSIDE the
    # `user` block at line ~2926, so we must patch `user`. We also fail
    # LOUDLY (print warning) if the literal drifts, so future regressions
    # are caught immediately instead of silently passing.
    if _NARRATIVE_MODE:
        _rule_n_mandatory_lead = (
            "🛡️ KP CROSS-CHECK (Rule N — MANDATORY citation): When the KP "
            "CROSS-CHECK block is present AND the user's question maps to a "
            "covered house (H1 vitality, H2 money, H5 children/speculation, "
            "H7 marriage/partner, H10 career/job, H11 gains/income), you "
            "MUST include one natural KP citation sentence in the answer. "
            "This is NOT optional — failing to cite is the same kind of "
            "error as inventing facts."
        )
        _rule_n_advisory_lead = (
            "🛡️ KP CROSS-CHECK (Rule N — NARRATIVE-MODE: ADVISORY only): "
            "The KP CROSS-CHECK block is BACKGROUND data the engine uses to "
            "compute the verdict. In narrative mode the user-facing answer "
            "is a 3-5 sentence FUSED combo verdict, NOT a method comparison. "
            "Cite KP in user-facing text ONLY when KP and Vedic verdicts "
            "DISAGREE on direction (CONFIRMS vs DENIES) — then ONE short "
            "clause is OK to flag the conflict ('Vedic side strong hai par "
            "KP delay dikha raha hai'). Otherwise OMIT the KP citation; "
            "translate the cosmic combination into human meaning instead."
        )
        # Phase 4.7 — also strip the body imperative example phrase that
        # surfaced "KP paddhati se bhi {N}th cusp ka sub-lord {planet}…"
        # in user-facing answers (the exact line the user flagged).
        _rule_n_body_imperative = (
            "For those topics, weave ONE natural KP citation alongside "
            "Vedic reasoning: 'KP paddhati se bhi {N}th cusp ka sub-lord "
            "{planet} hai jo {CONFIRMS/PARTIAL/DENIES} karta hai.'"
        )
        _rule_n_body_advisory = (
            "In narrative mode, do NOT surface the technical KP cusp / "
            "sub-lord phrasing in the user-facing answer. The KP block "
            "is BACKGROUND only; let the verdict speak through human "
            "language."
        )

        if _rule_n_mandatory_lead in user:
            user = user.replace(_rule_n_mandatory_lead, _rule_n_advisory_lead)
        elif "🛡️ KP CROSS-CHECK (Rule N — MANDATORY citation)" in user:
            # Literal drifted — fail loudly so we catch this regression.
            print("[openai_helper] ⚠️ Phase 4.7: Rule N MANDATORY lead "
                  "literal mismatch — gate did not fire. Source drifted; "
                  "update _rule_n_mandatory_lead to match line ~2926.")

        if _rule_n_body_imperative in user:
            user = user.replace(_rule_n_body_imperative, _rule_n_body_advisory)

        # Phase 4.7 — Rule 3 (line ~2931 in STRICT INSTRUCTIONS) also seeds
        # the user with the same surface-citation template. Soften it.
        _rule3_kp_imperative = (
            "3) KP cross-check: If a KP block is provided, USE it — verify "
            "the Vedic verdict against the cusp Sub-Lord rule for the "
            "relevant houses. State whether KP confirms or modifies the "
            "Vedic verdict ('KP paddhati se bhi yahi confirm hota hai...')."
        )
        _rule3_kp_advisory = (
            "3) KP cross-check (BACKGROUND ONLY in narrative mode): the "
            "engine has already cross-checked the Vedic verdict against "
            "KP. Use the agreement to gain confidence in your fused combo "
            "verdict, but do NOT name 'KP paddhati', 'cusp', or 'sub-lord' "
            "in the user-facing reply."
        )
        if _rule3_kp_imperative in user:
            user = user.replace(_rule3_kp_imperative, _rule3_kp_advisory)

        # ── Phase 4.7 T016 — DROP DEAD-CODE RULE PARAGRAPHS ─────────────
        # Rules F (ASHTAKAVARGA), G (ASPECTS), I (KARAKAS), J (BHAVA BALA),
        # K (DIVISIONAL CHARTS / D9 / D10), O (JAIMINI ARUDHA / UPAPADA)
        # all teach the model how to cite specific data blocks. In
        # narrative mode the corresponding data blocks (SARVASHTAKAVARGA,
        # KEY ASPECTS, JAIMINI CHARA KARAKAS, BHAVA BALA, divisional
        # charts, JAIMINI ARUDHA PADAS) are removed by
        # `_slim_locked_facts_for_narrative`. Keeping the rules creates
        # TWO problems: (a) wastes ~3K chars of prompt, (b) bias toward
        # enumeration / made-up numbers because the rules contain example
        # citations like "Aapka 10th ghar mein SAV 34 hai jo VERY STRONG
        # hai..." that the model may try to match. Drop them line-by-line
        # to keep narrative shape clean. Rules H (TRANSITS) and L
        # (PRATYANTAR) are retained — those data blocks are kept by the
        # diet. Rule M (REMEDIES) is retained. Rule O is retained for
        # love/marriage topic since UPAPADA LAGNA stays in the diet.
        _rule_prefixes_to_drop = (
            "    🛡️ ASHTAKAVARGA (Rule F):",
            "    🛡️ ASPECTS (Rule G):",
            "    🛡️ KARAKAS (Rule I):",
            "    🛡️ BHAVA BALA (Rule J):",
            "    🛡️ DIVISIONAL CHARTS (Rule K):",
        )
        if topic not in ("love", "marriage"):
            _rule_prefixes_to_drop = _rule_prefixes_to_drop + (
                "    🛡️ JAIMINI ARUDHA / UPAPADA (Rule O):",
            )
        _orig_rule_chars = len(user)
        _kept_lines = []
        _matched_prefixes = set()
        for _line in user.split("\n"):
            for _p in _rule_prefixes_to_drop:
                if _line.startswith(_p):
                    _matched_prefixes.add(_p)
                    break
            else:
                _kept_lines.append(_line)
                continue
        user = "\n".join(_kept_lines)
        _rule_chars_dropped = _orig_rule_chars - len(user)
        if _rule_chars_dropped > 0:
            print(f"[openai_helper] Phase 4.7 T016: dropped {_rule_chars_dropped:,} "
                  f"chars of dead-code rule paragraphs (Rules F/G/I/J/K"
                  f"{'/O' if topic not in ('love','marriage') else ''}) "
                  f"from user turn (data blocks they reference are slimmed out).")
        # ── DRIFT DETECTION (architect-flagged parity with Rule N gate) ──
        # If a prefix never matched but a recognisable substring still appears
        # in `user`, the source has drifted (text reindented, emoji changed,
        # rule renamed). Warn loudly so the next CI / live probe surfaces it.
        _missed = []
        for _p in _rule_prefixes_to_drop:
            if _p in _matched_prefixes:
                continue
            # Strip the leading 4 spaces + emoji to get a robust substring
            _needle = _p.split("(")[0].strip().split()[-1]  # e.g. "ASHTAKAVARGA"
            if _needle and _needle in user:
                _missed.append((_p, _needle))
        if _missed:
            print(f"[openai_helper] ⚠️ Phase 4.7 T016 DRIFT WARNING: "
                  f"{len(_missed)} dead-rule prefix(es) did not strip but "
                  f"their keyword still appears in user turn — source likely "
                  f"drifted. Update _rule_prefixes_to_drop literals: "
                  f"{[m[0][:40] + '...' for m in _missed]}")

        # ── Phase 4.8 T018 — NARRATIVE-MODE HARD OUTPUT CAP ─────────────
        # User-reported (Apr 28, 2026): even after the input diet + dead-
        # rule strip, the model's actual ANSWER was 8-10 lines with full
        # dasha breakdowns, pratyantar date ranges, Manglik-dosh asides,
        # and the actual verdict buried at the end. The existing Rule 10
        # BREVITY default is "100-140 words, 3-4 short paragraphs" — which
        # is the EXACT shape the model produced and which violates the
        # narrative-mode contract (3-5 sentences total, FUSED combo
        # verdict, no enumeration). We replace Rule 10 entirely in
        # narrative mode with a HARD CAP: 1-2 sentences, [VERDICT] →
        # [1 reason] format, NEVER mention dates/dasha-names/pratyantar/
        # antardasha/KP/divisional charts in user-facing text.
        _rule10_old_default = (
            "    • DEFAULT (multi-part / topic question only) — TOTAL "
            "answer = 100 to 140 WORDS. NEVER more. Count words as you "
            "write.\n"
        )
        # Phase 4.9 T023 — adaptive depth: pick the cap based on the
        # user's question intent (Tier 1/2/3). Tier 3 leaves Rule 10
        # untouched so technical Qs (KP / houses / dasha breakdown)
        # get the full 100-140 word answer.
        _phase49_tier = _question_depth_tier(question or "")
        _rule10_tier1_cap = (
            "    • NARRATIVE-MODE HARD CAP (Tier 1 — simple Q) — TOTAL "
            "answer = 1 to 2 SHORT SENTENCES (≤200 chars total). Format: "
            "[VERDICT in plain Hindi/Hinglish] → [1 short reason]. "
            "Example: 'Love ho sakta hai, lekin Mars ki impulsiveness "
            "aur Rahu ki confusion ki wajah se yeh zyada tar temporary "
            "rahega.' That is the ENTIRE answer. NEVER write a 3-paragraph "
            "explanation. NEVER mention dates, year ranges, "
            "Mahadasha/Antardasha/Pratyantar names, KP, divisional "
            "charts, or dosha names unless the user asked about them by "
            "name. The verdict + 1 reason IS the whole reply.\n"
        )
        _rule10_tier2_cap = (
            "    • NARRATIVE-MODE DETAILED ANSWER (Tier 2 — user said "
            "'kaise/why/explain/detail') — TOTAL answer = 3 to 5 SHORT "
            "SENTENCES (≤500 chars total). Simple human explanation. "
            "Basic astrology terms allowed (planet names like Mars / "
            "Rahu / Jupiter, current dasha by lord names). NEVER include "
            "ISO date ranges (2026-02-18 etc.), pratyantar / sookshma "
            "names, KP technicals, or divisional chart names UNLESS the "
            "user asked about them by name. Stay conversational, no "
            "bullet lists, no headings.\n"
        )
        if _phase49_tier == "technical":
            # Tier 3 → leave Rule 10 alone (full technical answer).
            print("[openai_helper] Phase 4.9 T023: tier=technical — "
                  "leaving Rule 10 default (100-140 WORDS) intact for "
                  "full technical answer.")
        elif _rule10_old_default in user:
            _chosen = (_rule10_tier2_cap if _phase49_tier == "detailed"
                       else _rule10_tier1_cap)
            user = user.replace(_rule10_old_default, _chosen)
            print(f"[openai_helper] Phase 4.9 T023: tier={_phase49_tier} — "
                  f"replaced Rule 10 100-140w default with "
                  f"{'TIER-2 DETAILED (3-5 sentences, ≤500 chars)' if _phase49_tier == 'detailed' else 'TIER-1 HARD CAP (1-2 sentences, ≤200 chars)'}.")
        elif "100 to 140 WORDS" in user:
            print("[openai_helper] ⚠️ Phase 4.9 T023: Rule 10 default literal "
                  "drifted — '100 to 140 WORDS' present but not in expected "
                  "form. Update _rule10_old_default to match line ~2978.")

    # Build full conversation: system → prior turns → current user turn.
    msgs: list[dict] = [{"role": "system", "content": system}]
    if isinstance(history, list):
        for m in history[-10:]:
            if not isinstance(m, dict):
                continue
            role = (m.get("role") or "").lower()
            text = (m.get("text") or "").strip()
            if not text or role not in ("user", "assistant"):
                continue
            # Trim long assistant turns to keep context budget sane
            if role == "assistant" and len(text) > 1200:
                text = text[:1200] + "…"
            msgs.append({"role": role, "content": text})

    # ── High-priority second system message: pin the deterministic verdict ───
    # Placed RIGHT BEFORE the user turn so it is the freshest instruction the
    # model sees. This is the strongest lever to stop the AI from inventing
    # a year-range different from what marriage_engine computed.
    if marriage_verdict_block and _NARRATIVE_MODE:
        # Phase 4.6 — narrative-mode marriage override. Mirror of wealth
        # Phase 4.5 pattern: keep engine facts as background ground truth
        # so dates/lords/score don't get invented, but DROP the
        # "narrate verbatim / verdict text as the spine / Upapada cite"
        # rules that produced the heavy report shape.
        msgs.append({
            "role": "system",
            "content": (
                "MARRIAGE FACTS (engine-locked ground truth — narrate as a "
                "fused combo verdict, do NOT enumerate):\n"
                "  • Use the window dates, dasha lord names, house numbers, "
                "and verdict direction (PROMISED / DENIED / DELAYED) EXACTLY "
                "as printed below — no rounding, no swapping, no day-precision "
                "invention.\n"
                "  • Do NOT contradict the engine's marriage_promised / "
                "marriage_denied flag — frame the narrative consistent with it.\n"
                "  • Do NOT echo printed score / bullets / 'Verdict:' / 'Reason:' "
                "/ 'Timing:' headers verbatim — your output shape is set by "
                "the QUESTION TYPE: NARRATIVE_ANSWER contract above.\n"
                "  • Do NOT surface 'Upapada Lagna {SIGN}', 'D9 navamsa 7L "
                "{planet}', 'KP cuspal sub-lord on H7' as user-facing text. "
                "These are background facts the engine uses to compute the "
                "verdict — translate them into the human meaning instead.\n"
                "  • Speak as Cosmic Intelligence — never AI / LLM / GPT / "
                "model.\n\n"
                + marriage_verdict_block
            ),
        })
    elif marriage_verdict_block:
        msgs.append({
            "role": "system",
            "content": (
                "TURN-LEVEL OVERRIDE — MARRIAGE NARRATOR MODE.\n"
                "The following verdict was computed by the deterministic shastriya engine. "
                "It is the GROUND TRUTH for this turn. You MUST narrate using these exact "
                "values. The dates, dasha names, planet names, score, and remedy are NOT "
                "negotiable — copy them verbatim into your reply. Specifically: when stating "
                "the timing window, use ONLY the date string given on the line that begins "
                "with '>>> NARRATE THIS WINDOW EXACTLY AS:'. Do not round to year-only, do "
                "not shift to a different year, do not blend with surrounding dasha periods.\n\n"
                + marriage_verdict_block
            ),
        })

    # NOTE: the STOCK NARRATOR override is appended LAST (just before the user
    # turn) — see the bottom of this function — so it is the freshest system
    # instruction the model sees and recency bias keeps the lock authoritative.

    # ── Final reminders (recency-bias citation pin) ──────────────────────────
    # The main system prompt has 14 rules; under gpt-4o-mini the model
    # sometimes drops the MANDATORY-citation ones (KP, Remedies, D9/D10) when
    # the question is plain topic-driven phrasing. We re-pin only those 4
    # critical ones here as the LAST instruction the model sees, so recency
    # bias makes them stick. Tailor by topic + only mention blocks that are
    # actually present in the LOCKED FACTS for this turn.
    reminder_lines: list[str] = []
    lf = locked_facts_str or ""

    # Sprint-7 Rule O — Jaimini Upapada (PIN FIRST for marriage so recency wins)
    has_jaimini = "UPAPADA LAGNA" in lf
    if topic == "marriage" and has_jaimini:
        reminder_lines.append(
            "• 🚨 JAIMINI UL CITATION IS MANDATORY THIS TURN (Rule O — pinned first). "
            "Pull EXACT values from the 'UPAPADA LAGNA' sub-section: UL sign, UL-lord + "
            "its house-from-UL, verdict tag (STABLE/STRAINED/MIXED/NEUTRAL). Weave ONE "
            "natural sentence: 'Jaimini paddhati se Upapada {ul_sign} mein hai (lord "
            "{ul_lord} {Nth} from UL) — marriage signature {VERDICT}.' If 12th-from-UL "
            "has occupants (Ketu/Saturn/Rahu = separation tendency) or UL-lord is in "
            "6/8/12 from UL, mention that nuance in the same sentence. Marriage answers "
            "may use up to 160 words THIS TURN to fit all 4 mandatory citations (D9 + UL "
            "+ KP + dasha) — extend, do NOT skip Jaimini."
        )

    # Sprint-9 Rule Q — Topic-specific vargas (D2/D3/D7/D12)
    has_d2  = "D2 HORA" in lf
    has_d3  = "D3 DREKKANA" in lf
    has_d7  = "D7 SAPTAMSA" in lf
    has_d12 = "D12 DWADASAMSA" in lf
    if topic == "child" and has_d7:
        reminder_lines.append(
            "• 👶 D7 SAPTAMSA citation is MANDATORY (Rule Q): for any progeny "
            "question, weave ONE sentence using the EXACT 5L D7 placement and "
            "Jupiter's D7 placement from the 'D7 SAPTAMSA' block: "
            "'D7 mein 5L {planet} {sign} mein {strength} hai, Jupiter (putra-karaka) "
            "{sign} mein {strength} hai — children prospects {strong/medium/weak}.'"
        )
    if topic == "finance" and has_d2:
        reminder_lines.append(
            "• 💰 D2 HORA citation is MANDATORY (Rule Q): for any wealth/money "
            "question, weave the verdict line from the D2 HORA block — name "
            "which significators (Jupiter/Venus/Mercury/Moon/Sun) sit in Sun-Hora "
            "(active income) vs Moon-Hora (passive/inherited) and the verdict tag "
            "(ACTIVE-EARNER / PASSIVE-WEALTH / BALANCED)."
        )
    if has_d12:
        # D12 cited only if user mentions parents
        reminder_lines.append(
            "• 👨‍👩‍ D12 DWADASAMSA citation is MANDATORY (Rule Q) ONLY IF user "
            "mentions parents/maa/papa/mata/pita/father/mother in their question. "
            "Use 9L (father) or 4L (mother) D12 placement from the block. Skip otherwise."
        )
    if has_d3:
        # D3 cited only if user mentions siblings
        reminder_lines.append(
            "• 👯 D3 DREKKANA citation is MANDATORY (Rule Q) ONLY IF user mentions "
            "siblings/bhai/behan/brother/sister in their question. Use 3L D3 + Mars/Jupiter "
            "D3 placements. Skip otherwise."
        )

    # Sprint-10 Rule R — Advanced topic-specific vargas (D16/D20/D24/D27)
    has_d16 = "D16 SHODASAMSA" in lf
    has_d20 = "D20 VIMSAMSA"   in lf
    has_d24 = "D24 CHATURVIMSAMSA" in lf
    has_d27 = "D27 BHAMSA"     in lf
    if has_d16:
        reminder_lines.append(
            "• 🚗 D16 SHODASAMSA citation is MANDATORY (Rule R) ONLY IF user "
            "mentions vehicle/car/bike/gaadi/luxury/comfort/conveyance. Use 4L D16 "
            "and Venus D16 placements from the 'D16 SHODASAMSA' block. Skip otherwise."
        )
    if has_d20:
        reminder_lines.append(
            "• 🕉️ D20 VIMSAMSA citation is MANDATORY (Rule R) ONLY IF user mentions "
            "spirituality/sadhana/mantra/devotion/bhakti/meditation/dharma/moksha. "
            "Use 9L D20 + Jupiter + Ketu placements. Skip otherwise."
        )
    if has_d24:
        reminder_lines.append(
            "• 🎓 D24 CHATURVIMSAMSA citation is MANDATORY (Rule R) ONLY IF user "
            "mentions education/study/college/exam/degree/learning/PhD/research. "
            "Use 4L+5L D24 + Mercury + Jupiter placements. Skip otherwise."
        )
    if has_d27:
        reminder_lines.append(
            "• 💪 D27 BHAMSA citation is MANDATORY (Rule R) ONLY IF user mentions "
            "health/stamina/strength/sports/fitness/energy/vitality. Use lagna-lord "
            "D27 + Mars + Sun placements. Skip otherwise."
        )

    # Sprint-11 Rule S — Subtle vargas (D30/D40/D45/D60)
    has_d30 = "D30 TRIMSAMSA"     in lf
    has_d40 = "D40 KHAVEDAMSA"    in lf
    has_d45 = "D45 AKSHAVEDAMSA"  in lf
    has_d60 = "D60 SHASHTYAMSA"   in lf
    if has_d30:
        reminder_lines.append(
            "• ⚠️ D30 TRIMSAMSA citation is MANDATORY (Rule S) ONLY IF user mentions "
            "accident/misfortune/danger/risk/dushman/enemy/litigation/court/dispute. "
            "Use the verdict tag (HIGH-MISFORTUNE-RISK / MODERATE-CAUTION / LOW-RISK) "
            "and named malefic-sign planets. Skip otherwise."
        )
    if has_d40:
        reminder_lines.append(
            "• 🤱 D40 KHAVEDAMSA citation is MANDATORY (Rule S) ONLY IF user mentions "
            "maa/mother/maternal/nani/mami/matrilineal/maa-side. Use 4L D40 + Moon D40. "
            "Skip otherwise."
        )
    if has_d45:
        reminder_lines.append(
            "• 👨 D45 AKSHAVEDAMSA citation is MANDATORY (Rule S) ONLY IF user mentions "
            "papa/father/paternal/dada/chacha/patrilineal/baap-side. Use 9L D45 + Sun D45. "
            "Skip otherwise."
        )
    if has_d60:
        reminder_lines.append(
            "• 🕉️ D60 SHASHTYAMSA citation is MANDATORY (Rule S) ONLY IF user asks about "
            "past life / pichla janam / karma / soul / atma / why-me / destiny / "
            "purpose-of-life / what-is-my-purpose. Use lagna-lord D60 + Atma Karaka D60 "
            "(Parashara's most-prized varga). Skip otherwise."
        )

    # Sprint-18 Rule X — Extended Bala (Saptavargaja / Ishta-Kashta / Vimshopaka / Yuddha)
    if "EXTENDED BALA" in lf:
        reminder_lines.append(
            "• ⚖️ EXTENDED BALA citation (Rule X): for STRENGTH / capability / "
            "'kitna strong hai X planet' / 'why is my career stuck' / 'why is "
            "marriage delayed' style questions, you MUST cite ONE of: "
            "(a) Saptavargaja Bala — dignity across 7 vargas (max 210v), "
            "(b) Ishta Phala — desirable results yield (max 60v), "
            "(c) Kashta Phala — undesirable results yield (max 60v), "
            "(d) Vimshopaka Bala (Shodashavarga max 20v) — overall varga strength, "
            "(e) Yuddha Bala — planetary war winner/loser. "
            "Use the SINGLE most-relevant figure with planet name + virupa value. "
            "Skip on greetings / short-talk."
        )

    # Sprint-18.5 Rule X+ — Bhava Bala Deep (4-fold per house)
    if "BHAVA BALA DEEP" in lf:
        reminder_lines.append(
            "• 🏠 BHAVA BALA DEEP citation (Rule X+): for HOUSE-strength / "
            "'mera 7th ghar / 10th house weak hai' / 'kyun ye area "
            "strong/weak hai' style questions, you MUST cite the relevant "
            "house's TOTAL bhava bala / required ratio (e.g., 'H7=386v vs "
            "required 425v, ratio 0.91x = MODERATE') and identify which of "
            "the 4 components (Adhipati lord-strength, Digbala house-type, "
            "Drishti aspects, Naisargika lord-natural) is dragging it down. "
            "Skip on greetings / non-house questions."
        )

    # Sprint-19 Rule Y — Classical Yogas Mega (Vipreet/Dhana/KaalSarp/Nabhasa/Pravrajya)
    if "CLASSICAL YOGAS" in lf:
        reminder_lines.append(
            "• 🔱 CLASSICAL YOGAS citation (Rule Y): the LOCKED FACTS contain "
            "the Sprint-19 Classical Yogas block (Named Vipreet — "
            "Harsha/Sarala/Vimala; 10+ Dhana yogas by lord-pairs; Negative — "
            "Daridra/Guru-Chandal/Shakat/Vish/Angarak/Pitra-dosh; Kaal Sarp "
            "12 variants — Anant/Kulik/Vasuki/Shankhpal/Padma/Mahapadma/"
            "Takshak/Karkotak/Shankhachood/Ghatak/Vishdhar/Sheshnag; Nabhasa "
            "Sankhya 7 — Vallaki/Damaru/Pasha/Kedara/Soola/Yuga/Gola; "
            "Nabhasa Ashraya 3 — Rajju/Musala/Nala; Nabhasa Dala 2 — "
            "Kamala-Dala/Mala-Dala; Nabhasa Aakriti subset — "
            "Gada/Shakata/Pakshi/Vajra/Yava/Kamala/Vapi/Sarpa; Pravrajya — "
            "Sannyasa variants by leading planet). When user asks about "
            "wealth/dhana/dauloth/paisa, you MUST cite at least ONE Dhana "
            "yoga from the block (with the specific lord-pair). When user "
            "asks about Kaal Sarp / sarp dosh / snake-yoga / 'mera kaal "
            "sarp hai kya', you MUST cite the EXACT variant name (e.g., "
            "'Anant Kaal Sarp — Rahu in H1') if present, OR confirm 'no "
            "Kaal Sarp detected' if absent. When user asks about renunciation"
            " / sannyasa / spiritual-detachment, cite Pravrajya yoga. NEVER "
            "invent yogas not in the block. The polarity icons (✅/⚠️/◐) "
            "indicate POSITIVE/NEGATIVE/MIXED — preserve that tone."
        )

    # Sprint-15 Rule W — Per-varga yogas (Pancha Mahapurusha / Raj / Vipreet)
    if "PER-VARGA YOGAS" in lf:
        reminder_lines.append(
            "• 🌟 PER-VARGA YOGAS reinforcement (Rule W): if the LOCKED FACTS "
            "list a Pancha Mahapurusha (Ruchaka/Bhadra/Hamsa/Malavya/Sasa), "
            "Raj Yoga or Vipreet Raj Yoga in any varga (D1/D9/D10/D24/D60), "
            "you MUST cite at least the SINGLE most-relevant yoga to the "
            "topic in one short clause. Mahapurusha = lifelong elevation; "
            "Raj Yoga = power/status rise; Vipreet Raj = adversity → "
            "unexpected rise. Use yoga name + varga + key planet."
        )

    # Sprint-14 Rule V — Sthira Dasha + Niryana Shoola Dasha
    has_sthira = "STHIRA DASHA" in lf
    has_niryana = "NIRYANA SHOOLA" in lf
    if has_sthira or has_niryana:
        reminder_lines.append(
            "• 🔆 STHIRA / NIRYANA SHOOLA DASHA reinforcement (Rule V): for "
            "TIMING questions (kab, when, future windows), if the answer cites "
            "Vimshottari or Chara Dasha, ALSO cite Sthira Dasha (life-stability "
            "layer, 96-yr cycle) and/or Niryana Shoola Dasha (longevity / "
            "life-direction, 108-yr cycle) as a third cross-check — only when "
            "they reinforce or modify the timing window. Skip for non-timing Qs."
        )

    # Sprint-13 Rule U — Argala / Virodhargala intervention
    if "ARGALA / VIRODHARGALA" in lf:
        reminder_lines.append(
            "• ⚖️ ARGALA / VIRODHARGALA reinforcement (Rule U): when answering "
            "marriage/career/finance/child/health questions, if the relevant "
            "house has STRONG-BENEFIC or STRONG-MALEFIC argala in the LOCKED "
            "FACTS, weave ONE short clause about it — e.g., '7th house pe "
            "Jupiter ka benefic argala hai (relationship support)' or "
            "'10th house pe malefic argala (career obstacles)'. Skip if NEUTRAL."
        )

    # Sprint-12 Rule T — Per-varga deep signals (Vargottama matrix + Shadvarga Bala)
    has_vargottama = "VARGOTTAMA MATRIX" in lf
    has_shadvarga  = "SHADVARGA BALA"    in lf
    if has_vargottama or has_shadvarga:
        reminder_lines.append(
            "• 🔱 VARGOTTAMA / SHADVARGA BALA reinforcement (Rule T): when you mention "
            "a SPECIFIC planet by name in your answer, if that planet appears in the "
            "'VARGOTTAMA MATRIX' block with 5+ vargas OR has Shadvarga Bala ≥16 (VERY-STRONG) "
            "OR ≤5 (VERY-WEAK), weave ONE short clause about that signal — e.g., "
            "'Mars vargottama in 6 vargas (exceptional strength)' or 'Saturn Shadvarga "
            "Bala 4/20 (very weak — limits houses it owns)'. Use sparingly — max 2 such clauses."
        )

    # Sprint-8 Rule P — Chara Dasha cross-check for TIMING questions
    has_chara = "JAIMINI CHARA DASHA" in lf
    timing_topics = {"marriage", "career", "finance", "child", "general"}
    if has_chara and topic in timing_topics:
        reminder_lines.append(
            "• 🕐 CHARA DASHA cross-check (Rule P) is MANDATORY when the user is asking "
            "about TIMING (kab / when / next-period). Pull the CURRENT Chara MD + AD from "
            "the 'JAIMINI CHARA DASHA' block and weave ONE natural sentence comparing it "
            "to Vimshottari: 'Chara Dasha mein abhi {SIGN} MD ({lord}) chal raha hai "
            "({start}→{end}), Vimshottari ke {VimMD-AD} ke saath {AGREE/DISAGREE} hai — "
            "isliye yeh window {high-confidence/mixed-signal} hai.' If the question is "
            "purely analysis (no timing), Chara citation is optional."
        )

    # KP (Rule N) — mandatory citation for covered topics when block exists
    has_kp = "KP CROSS-CHECK" in lf
    # Topics matching covered houses (per _classify_topic labels):
    #   marriage→H7, relationship→H7, career→H10, finance→H2/H11,
    #   child→H5, health→H1, general→any (let model pick)
    kp_topics = {"marriage", "relationship", "career", "finance",
                 "child", "health", "general"}
    if has_kp and topic in kp_topics:
        if _NARRATIVE_MODE:
            # Phase 4.7 — soft advisory only. The original MANDATORY language
            # was the loudest competing signal vs the 3-5 sentence narrative
            # contract and was the primary cause of the user-reported "ek dam
            # bekar" KP-paddhati surface citations.
            reminder_lines.append(
                "• KP cite is OPTIONAL — only if KP and Vedic verdicts "
                "DISAGREE on direction (CONFIRMS vs DENIES), then ONE "
                "short clause to flag the conflict. Otherwise OMIT — the "
                "user-facing reply is a 3-5 sentence FUSED combo verdict, "
                "not a method comparison. The KP block is BACKGROUND."
            )
        else:
            reminder_lines.append(
                "• KP citation is MANDATORY this turn. Find the relevant house in the "
                "'KP CROSS-CHECK' block (H7=marriage, H10=career, H2/H11=money, H5=children, "
                "H1=health/vitality) and weave ONE natural sentence: 'KP paddhati se bhi "
                "{N}th cusp ka sub-lord {planet} hai jo {CONFIRMS/PARTIAL/DENIES} karta hai.' "
                "Skipping this is a hallucination-class error."
            )

    # Remedies (Rule M) — quote verbatim, never invent
    has_rem = "REMEDIES" in lf and "MANTRA:" in lf
    if has_rem:
        reminder_lines.append(
            "• If you cite ANY remedy this turn, copy the mantra / gemstone / charity / "
            "fast-day / yantra VERBATIM from the REMEDIES block above. Use the 'for: ...' "
            "label so the user knows WHY. NEVER invent a Sanskrit mantra (e.g. do NOT "
            "write 'Om Shum Shukraya Namah' if it is not in the block) and NEVER invent "
            "carat weights or 'lucky stones'. If the needed planet has no remedy listed, "
            "fall back to 'Hanuman Chalisa daily' — do NOT fabricate."
        )

    # D9 / D10 (Rule K) — mandatory consultation for marriage/career
    has_d9  = "D9 NAVAMSA" in lf or "NAVAMSA" in lf
    has_d10 = "D10 DASAMSA" in lf or "DASAMSA" in lf
    if topic == "marriage" and has_d9:
        if _NARRATIVE_MODE:
            # Phase 4.7 — engine still uses D9 internally; user-facing
            # reply doesn't need to namedrop "D9 mein 7L Mercury Pisces".
            reminder_lines.append(
                "• Marriage question: D9 verdict is BACKGROUND — let it "
                "shape your direction (stable / strained) but do NOT "
                "name-drop 'D9 mein 7L X' in the user-facing combo reply."
            )
        else:
            reminder_lines.append(
                "• Marriage question: you MUST cite the 7L's D9 placement from the "
                "DIVISIONAL CHARTS block (one line, e.g. 'D9 mein 7L Mercury Pisces "
                "debilitated jaata hai — natal weakness D9 mein bhi confirm hoti hai')."
            )
    if topic == "career" and has_d10:
        if _NARRATIVE_MODE:
            reminder_lines.append(
                "• Career question: D10 verdict is BACKGROUND — let it "
                "shape your direction (support / friction) but do NOT "
                "name-drop 'D10 mein 10L X' in the user-facing combo reply."
            )
        else:
            reminder_lines.append(
                "• Career question: you MUST cite the 10L's D10 placement from the "
                "DIVISIONAL CHARTS block (one line, e.g. 'D10 mein 10L Mercury Sagittarius "
                "own-sign mein jaata hai — career line strong support karta hai D10 mein')."
            )

    if reminder_lines:
        if _NARRATIVE_MODE:
            # Phase 4.7 — softer trailer. The original "MANDATORY citations
            # sit ABOVE the brevity rule — trim prose, NOT the citations"
            # was the loudest recency-bias contradiction vs the narrative
            # contract. Reverse priority: shape > cite.
            _trailer = (
                "\n\nThese reminders are ADVISORY — they only fire if "
                "they fit the 3-5 sentence FUSED combo verdict shape. "
                "If a citation can't be woven naturally into ≤2 short "
                "sentences, OMIT it. Narrative shape > raw citation count."
            )
        else:
            _trailer = (
                "\n\nThese are MANDATORY citations for this turn. They sit ABOVE "
                "the brevity rule — if Rule 10 (140-word cap) and these reminders "
                "conflict, trim the prose, NOT the citations."
            )
        msgs.append({
            "role": "system",
            "content": (
                "🔔 FINAL REMINDERS — read these LAST before composing your reply:\n"
                + "\n".join(reminder_lines)
                + _trailer
            ),
        })

    # ── STOCK NARRATOR TURN-LEVEL OVERRIDE ───────────────────────────────────
    # Appended LAST (just before the user turn) so recency bias keeps the lock
    # authoritative. AI is reduced to NARRATOR — every fact (verdict bucket,
    # window, score, dasha, planet names, remedy) is pre-decided by
    # stock_engine.py and MUST be copied verbatim.
    if stock_verdict_block:
        msgs.append({
            "role": "system",
            "content": (
                "🔒 STOCK NARRATOR OVERRIDE — this turn is a stock-market / "
                "trading / investment question. The cosmic engine has already "
                "computed the verdict, score, timing window, dasha context, "
                "and remedy for you. You are NOT analysing — you are NARRATING "
                "a locked verdict in warm Hinglish.\n\n"
                "ABSOLUTE RULES (these override every other instruction this turn):\n"
                "  1. The verdict bucket (go_now / wait / limited / avoid) is "
                "FINAL. Do NOT contradict it, do NOT hedge it into the "
                "opposite bucket, do NOT add 'lekin actually…' reversals.\n"
                "  2. Copy the timing window string EXACTLY as printed on the "
                "line beginning '>>> NARRATE THIS WINDOW EXACTLY AS:'. No "
                "rounding, no shifting, no blending with neighbouring dashas.\n"
                "  3. Copy the score, the dasha-lord names, and the remedy "
                "verbatim. No paraphrasing of numbers or planet names.\n"
                "  4. NEVER reveal AI / LLM / GPT / model — brand voice is "
                "'Powered by Advanced Cosmic Intelligence'. Speak as the "
                "cosmic intelligence, never as a chatbot.\n"
                "  5. NO fake/random fallbacks. If the engine block below is "
                "silent on a detail, do NOT invent it — stick to what is "
                "printed.\n\n"
                + stock_verdict_block
            ),
        })

    # ── LOVE NARRATOR TURN-LEVEL OVERRIDE ─────────────────────────────────────
    # Appended LAST (just before the user turn) so recency bias keeps the lock
    # authoritative. Mirror of stock override + extra brand-safety guards for
    # affair / breakup / one_sided buckets surfaced by love_engine in the
    # `brand_safety_warnings` array of the JSON envelope.
    if love_verdict_block and _NARRATIVE_MODE:
        # Phase 4.6 — narrative-mode love override. Mirror of wealth Phase 4.5
        # pattern: keep engine facts as background ground truth so dates/lords/
        # bucket don't get invented, but DROP the "narrate verbatim / verdict
        # text as the spine / KP cuspal cross-check / D9 7L / Upapada surface
        # citation" rules that produced the heavy report shape (the user
        # screenshot showed: "KP paddhati se bhi 7th ghar ka sub-lord Sun..."
        # which was exactly this heavy override forcing technical jargon).
        msgs.append({
            "role": "system",
            "content": (
                "LOVE FACTS (engine-locked ground truth — narrate as a fused "
                "combo verdict, do NOT enumerate, do NOT pivot to marriage):\n"
                "  • Use the verdict bucket (green / yellow_wait / slow_burn / "
                "red_avoid), the timing window dates, dasha lord names, and "
                "Venus/5L/7L positions EXACTLY as printed below — no rounding, "
                "no swapping, no day-precision invention.\n"
                "  • Do NOT contradict the verdict bucket — frame the answer "
                "consistent with it (e.g. yellow_wait → 'love ho sakta hai par "
                "patience aur clarity ke bina tikega nehi').\n"
                "  • Do NOT echo printed score / 'Verdict:' / 'Reason:' / "
                "'Timing:' headers verbatim — your output shape is set by the "
                "QUESTION TYPE: NARRATIVE_ANSWER contract above.\n"
                "  • Do NOT surface 'KP paddhati', 'cuspal sub-lord', "
                "'KP cross-check', 'D9 navamsa 7L', 'Upapada Lagna', "
                "'Darakaraka', 'Vimshottari', or 'Jaimini' as user-facing text. "
                "These are background facts the engine uses to compute the "
                "verdict — translate them into the human meaning instead.\n"
                "  • TOPIC FIDELITY — this is a LOVE question (attraction / "
                "connection / stability of CURRENT or near-term relations). "
                "Do NOT pivot to MARRIAGE analysis (shaadi promise, marriage "
                "delay, marriage denial) unless the user explicitly used "
                "marriage / shaadi / vivah vocabulary.\n"
                "  • Brand-safety guards (still active for affair / breakup / "
                "one_sided buckets):\n"
                "      - affair_third_party → NEVER accuse partner; describe "
                "cosmic patterns only.\n"
                "      - breakup_signal → soften; pair separation with healing "
                "window; never say 'definite breakup hoga'.\n"
                "      - one_sided → preserve self-worth; frame as 'mutual "
                "cosmic resonance abhi weak hai', never 'wo tumhe pasand "
                "nahi karta'.\n"
                "  • Speak as Cosmic Intelligence — never AI / LLM / GPT / "
                "model.\n\n"
                + love_verdict_block
            ),
        })
    elif love_verdict_block:
        msgs.append({
            "role": "system",
            "content": (
                "🔒 LOVE NARRATOR OVERRIDE — this turn is a love / relationship / "
                "romance question. The cosmic engine has already computed the "
                "verdict bucket, score, timing window, Venus/5L/7L lords, "
                "Darakaraka, Upapada, KP cuspal cross-check, D9 Navamsa "
                "overlay, and remedy for you. You are NOT analysing — you "
                "are NARRATING a locked verdict in warm Hinglish.\n\n"
                "ABSOLUTE RULES (these override every other instruction this turn):\n"
                "  1. The verdict bucket (green / yellow_wait / slow_burn / "
                "red_avoid) is FINAL. Do NOT contradict it, do NOT hedge it "
                "into the opposite bucket, do NOT add 'lekin actually…' "
                "reversals. Use the verdict text as the spine of your reply.\n"
                "  2. Copy the timing window string EXACTLY as printed on the "
                "line beginning '>>> NARRATE THIS WINDOW EXACTLY AS:'. No "
                "rounding, no shifting, no blending.\n"
                "  3. Copy score, dasha-lord names, 5th-lord, 7th-lord, Venus "
                "house/dignity, Darakaraka name+persona, and remedy VERBATIM. "
                "No paraphrasing of numbers or planet names.\n"
                "  4. NEVER reveal AI / LLM / GPT / model — brand voice is "
                "'Powered by Advanced Cosmic Intelligence'. Speak as the "
                "cosmic intelligence, never as a chatbot.\n"
                "  5. NO fake/random fallbacks. If the engine block is silent "
                "on a detail, do NOT invent it.\n\n"
                "  6. TENSE-AWARE FRAMING (mandatory) — read the "
                "'Question tense:' line in the verdict block:\n"
                "     • PRESENT  → headline must reference CURRENT Dasha "
                "lords + active transit. Do NOT lead with 'agle X mahine "
                "mein…' for a 'abhi/aaj/currently/right now/chal raha hai' "
                "question.\n"
                "     • FUTURE   → headline must reference next dasha "
                "window + upcoming Jupiter/Rahu transits. Do NOT lead "
                "with 'abhi to…' for a 'kab/will/karega/hoga' question.\n"
                "     • GENERAL  → balance both naturally.\n"
                "  7. BRAND-SAFETY GUARDS (mandatory for these question_type "
                "buckets):\n"
                "     • affair_third_party → NEVER accuse the partner of "
                "cheating (regardless of tense). Describe cosmic patterns "
                "only ('Venus-Rahu axis', '12L in 7H' etc.). For PRESENT "
                "tense: frame as 'abhi cosmic plane pe X pattern active hai'. "
                "For FUTURE tense: frame as 'agle X mahine mein Y window pe "
                "trust pattern test hoga'. Recommend self-introspection + "
                "open communication + (high signal only) trust-rebuilding.\n"
                "     • breakup_signal → soften language; pair every "
                "separation indicator with a healing window + remedy. NEVER "
                "say 'definite breakup hoga' — say 'cosmic plane pe distance "
                "signal hai, lekin healing window agle X mahine khulega'.\n"
                "     • one_sided → preserve self-worth. Frame as 'mutual "
                "cosmic resonance abhi weak hai' not 'wo tumhe pasand nahi "
                "karta'. NEVER make the user feel rejected as a person.\n"
                "  7. If `brand_safety_warnings` array in the JSON envelope "
                "is non-empty, internalise EACH warning as an absolute "
                "constraint for this turn.\n\n"
                + love_verdict_block
            ),
        })

    # ── CAREER NARRATOR TURN-LEVEL OVERRIDE ───────────────────────────────────
    # Appended LAST after love so recency bias keeps the lock authoritative.
    # Mirror of stock/love narrator overrides + brand-safety guards for
    # govt-job (no fake selection-date promise), business-start (no random
    # capital-loss prediction), resignation (soften — never tell user to
    # quit definitively), and partnership (always recommend written agreement).
    if career_verdict_block and _NARRATIVE_MODE:
        # Phase 4.6 — narrative-mode career override. Mirror of wealth/love
        # pattern: keep engine facts as background ground truth, drop the
        # heavy "narrate verbatim / D10 dasamsha / Sade Sati / KP cusp"
        # surface citations.
        msgs.append({
            "role": "system",
            "content": (
                "CAREER FACTS (engine-locked ground truth — narrate as a fused "
                "combo verdict, do NOT enumerate, do NOT pivot to other "
                "topics):\n"
                "  • Use the verdict bucket (govt_job / promotion / resignation "
                "/ business_start / partnership / transfer / career_setback / "
                "general_career), the verdict status (green_go / yellow_wait / "
                "slow_burn / red_avoid), the timing window dates, and dasha/"
                "10L/Amatya-Karaka names EXACTLY as printed below — no "
                "rounding, no swapping, no day-precision invention.\n"
                "  • Do NOT contradict the verdict bucket / status — frame "
                "the answer consistent with it.\n"
                "  • Do NOT echo printed score / 'Verdict:' / 'Reason:' / "
                "'Timing:' headers verbatim — your output shape is set by the "
                "QUESTION TYPE: NARRATIVE_ANSWER contract above.\n"
                "  • Do NOT surface 'D10 dasamsha', 'Sade Sati phase on 10L', "
                "'KP cuspal sub-lord on H10', 'Amatya Karaka {planet}', "
                "'Mahapurusha yoga', or 'Vimshottari' as user-facing text. "
                "Translate them into human meaning instead.\n"
                "  • TOPIC FIDELITY — this is a CAREER question (job / "
                "promotion / switch / boss / business). Do NOT pivot to "
                "marriage, finance, or relationship.\n"
                "  • Brand-safety guards (still active for sensitive buckets):\n"
                "      - govt_job → frame as 'window favourable hai, mehnat "
                "test hogi'; never promise selection on a specific date.\n"
                "      - business_start → never predict 'capital loss' or "
                "'business band' as definite; recommend small-scale pilot "
                "when score < 25.\n"
                "      - resignation → never tell user to quit definitively; "
                "always pair green with 'written next-offer hath mein hone "
                "ke baad'.\n"
                "      - partnership → always recommend WRITTEN agreement.\n"
                "      - career_setback → preserve self-worth.\n"
                "  • Speak as Cosmic Intelligence — never AI / LLM / GPT / "
                "model.\n\n"
                + career_verdict_block
            ),
        })
    elif career_verdict_block:
        msgs.append({
            "role": "system",
            "content": (
                "🔒 CAREER NARRATOR OVERRIDE — this turn is a career / job / "
                "profession / business question. The cosmic engine has already "
                "computed the verdict bucket (govt_job / foreign_job / "
                "promotion / resignation / business_start / partnership / "
                "transfer / career_setback / new_job_timing / job_change / "
                "career_field_choice / general_career), the verdict status "
                "(green_go / yellow_wait / slow_burn / red_avoid), the score, "
                "the timing window via Vimshottari + Saturn + Jupiter+Yogini "
                "transits, the 10th lord / D10 / KP cuspal cross-check, the "
                "Amatya-Karaka, the Mahapurusha & Raj/Dhana Yogas, the Sade "
                "Sati phase, and the remedy for you. You are NOT analysing — "
                "you are NARRATING a locked verdict in warm Hinglish.\n\n"
                "ABSOLUTE RULES (these override every other instruction this turn):\n"
                "  1. The verdict bucket and verdict status are FINAL. Do NOT "
                "contradict, do NOT hedge into the opposite bucket, do NOT "
                "add 'lekin actually…' reversals. Use the verdict text as the "
                "spine of your reply.\n"
                "  2. Copy timing windows (Vimshottari Maha-Antar, Saturn "
                "transit window, Jupiter transit window) EXACTLY as printed "
                "in the locked block. No rounding, no shifting, no blending.\n"
                "  3. Copy score, dasha-lord names, 10th-lord, Amatya-Karaka, "
                "house numbers, Mahapurusha yoga names, and remedy VERBATIM. "
                "No paraphrasing of numbers or planet names.\n"
                "  4. NEVER reveal AI / LLM / GPT / model — brand voice is "
                "'Powered by Advanced Cosmic Intelligence'. Speak as the "
                "cosmic intelligence, never as a chatbot.\n"
                "  5. NO fake/random fallbacks. If the engine is silent on a "
                "specific date or company name, do NOT invent it. Vague "
                "phrases like 'jaldi mil jayegi' without a window are "
                "FORBIDDEN — only narrate what the engine produced.\n"
                "  6. TENSE-AWARE FRAMING (mandatory) — read the "
                "'QUESTION TENSE:' line in the verdict block:\n"
                "     • PRESENT  → headline references CURRENT Maha-Antar-"
                "Pratyantar lords + active Saturn/Jupiter transit. Do NOT "
                "lead with 'agle X mahine mein…' for a 'abhi/aaj/currently/"
                "right now/chal raha hai' question.\n"
                "     • FUTURE   → headline references next dasha window + "
                "upcoming Saturn/Jupiter transits. Do NOT lead with "
                "'abhi to…' for a 'kab/will/karega/hoga/milega' question.\n"
                "     • GENERAL  → balance both naturally.\n"
                "  7. BRAND-SAFETY GUARDS (mandatory for these buckets):\n"
                "     • govt_job → NEVER promise selection on a specific date. "
                "Frame as 'agle X mahine ka window favourable hai — "
                "tayari + form-fill on time'. Always pair with effort: "
                "'cosmic window khulta hai, par mehnat aapki test hogi'.\n"
                "     • business_start → NEVER predict 'capital loss hoga' or "
                "'business band hoga' as a definite outcome. Frame "
                "red_avoid / slow_burn as 'abhi natal promise weak hai, "
                "X mahine ke baad activation window'. ALWAYS recommend "
                "small-scale pilot first when score < 25.\n"
                "     • resignation → NEVER tell the user to quit definitively. "
                "Even on green_go, frame as 'cosmic window resign-friendly "
                "hai LEKIN written next-offer hath mein hone ke baad hi "
                "step lein'. red_avoid → 'abhi resign mat karein, X mahine "
                "ruk jaayein'.\n"
                "     • partnership → ALWAYS recommend WRITTEN agreement + "
                "exit clause + profit-share clarity, regardless of verdict. "
                "Frame green as 'partnership favourable hai par paper-work "
                "first'. red as 'partnership friction signal hai — solo "
                "ya silent-investor model better'.\n"
                "     • career_setback → preserve self-worth. Frame as "
                "'cosmic plane pe transit pressure hai, aapki capability "
                "mein doubt nahi'. Pair every setback line with a healing "
                "window + remedy.\n"
                "     • foreign_job → frame timing as 'window' not "
                "'guarantee'. NEVER promise a specific country or visa.\n"
                "  8. If `brand_safety_warnings` array in the verdict block "
                "is non-empty, internalise EACH warning as an absolute "
                "constraint for this turn.\n"
                "  9. DATE-PRECISION LOCK — the engine emits dates in "
                "month-year resolution ONLY (e.g. 'Jul 2025 → Jun 2026'). "
                "You MUST cite dates in the SAME resolution as printed. "
                "FORBIDDEN: inventing specific day numbers like "
                "'2025-07-25' or '15 July 2025' or '25/07/2025' when the "
                "engine only gave you 'Jul 2025'. Just write 'Jul 2025 "
                "se Jun 2026 ka window' or 'July 2025 → June 2026'. "
                "ZERO day-precision unless the engine itself printed a "
                "day number.\n\n"
                + career_verdict_block
            ),
        })

    # ── WEALTH NARRATOR TURN-LEVEL OVERRIDE ───────────────────────────────────
    # Appended LAST after career so recency bias keeps the lock authoritative.
    # Mirror of stock/love/career narrator overrides + STRICT brand-safety
    # guards specific to financial content: NEVER predict rupee amounts,
    # NEVER predict bankruptcy, NEVER advise loan-skip / EMI-default /
    # tax-evasion, NEVER endorse lottery / satta / KBC / matka, ALWAYS
    # recommend qualified CA / SEBI-registered financial advisor consult,
    # surface SEBI line on high-risk investment buckets.
    if wealth_verdict_block and _NARRATIVE_MODE:
        # Phase 4.5 — narrative-mode wealth override. Keep the engine's
        # locked facts (window, lord, score, bucket) flowing as ground
        # truth so the AI grounds dates correctly, but DROP the V→R→T
        # framing rules and Rule #10's "MANDATORY CA / SEBI cite" — both
        # of which forced the legacy template + disclaimer suffix that
        # narrative mode is explicitly killing.
        msgs.append({
            "role": "system",
            "content": (
                "WEALTH FACTS (engine-locked ground truth — narrate, do "
                "not invent):\n"
                "  • Use the window dates, planet names, house numbers, "
                "and bucket label EXACTLY as printed below — no rounding, "
                "no swapping, no day-precision invention.\n"
                "  • Do NOT contradict the verdict status (green_go / "
                "yellow_wait / slow_burn / red_avoid) — frame the answer "
                "consistent with it.\n"
                "  • Do NOT echo the printed score badge / bullets / "
                "headers / 'Karo:' / 'Avoid:' / 'Upay:' lines verbatim. "
                "Use them as facts only — your narrative shape is set "
                "by the QUESTION TYPE: NARRATIVE_ANSWER contract.\n"
                "  • Do NOT append any 'CA / SEBI-registered advisor se "
                "consult karein' / 'qualified financial advisor' / "
                "'tax consultant' phrasing. The platform handles "
                "advisor-cite separately when needed.\n"
                "  • Speak as Cosmic Intelligence — never AI / LLM / "
                "GPT / model.\n\n"
                + wealth_verdict_block
            ),
        })
    elif wealth_verdict_block:
        msgs.append({
            "role": "system",
            "content": (
                "🔒 WEALTH NARRATOR OVERRIDE — this turn is a wealth / "
                "finance / salary / business-profit / loan / property / "
                "inheritance / savings / sudden-windfall / debt-recovery / "
                "foreign-income / partnership-finance / general-dhana "
                "question. The cosmic engine has already computed the "
                "verdict bucket (salary_growth / business_profit / "
                "loan_clearance / property_purchase / investment_return / "
                "inheritance_timing / debt_recovery / sudden_windfall / "
                "savings_capacity / foreign_income / partnership_finance / "
                "general_wealth), the verdict status (green_go / yellow_wait "
                "/ slow_burn / red_avoid), the score, the timing window via "
                "Vimshottari + Jupiter / Saturn transits, the 2H/5H/8H/9H/"
                "11H cross-check, the D9 + D2 (Hora) + D11 (Labha-amsa) "
                "divisional overlay, the KP cuspal sub-lord on cusps "
                "2/5/11, the Atmakaraka + Dhana Karaka (Jaimini), the "
                "Lakshmi / Dhana / Maha-Lakshmi / Vipareeta-Raja yogas, "
                "the Sade Sati phase on 2L/11L, and the remedy for you. "
                "You are NOT advising — you are NARRATING a locked verdict "
                "in warm Hinglish.\n\n"
                "ABSOLUTE RULES (these override every other instruction this turn):\n"
                "  1. The verdict bucket and verdict status are FINAL. Do NOT "
                "contradict, do NOT hedge into the opposite bucket, do NOT "
                "add 'lekin actually…' reversals. Use the verdict text as "
                "the spine of your reply.\n"
                "  2. Copy timing windows (Vimshottari Maha-Antar, Jupiter "
                "transit window, Saturn transit window) EXACTLY as printed "
                "in the locked block. No rounding, no shifting, no "
                "blending.\n"
                "  3. Copy score, dasha-lord names, lagnesh, Atmakaraka, "
                "Dhana Karaka, house numbers, yoga names, and remedy "
                "VERBATIM. No paraphrasing of numbers or planet names.\n"
                "  4. NEVER reveal AI / LLM / GPT / model — brand voice is "
                "'Powered by Advanced Cosmic Intelligence'. Speak as the "
                "cosmic intelligence, never as a chatbot.\n"
                "  5. NO fake/random fallbacks. If the engine is silent on "
                "a specific date or amount, do NOT invent it. Vague "
                "phrases like 'lakhpati ban jaaoge' without a window are "
                "FORBIDDEN — only narrate what the engine produced.\n"
                "  6. TENSE-AWARE FRAMING (mandatory) — read the "
                "'QUESTION TENSE:' line in the verdict block:\n"
                "     • PRESENT  → headline references CURRENT Maha-Antar-"
                "Pratyantar (e.g. 'abhi Saturn-Mercury-Venus chal raha hai').\n"
                "     • FUTURE   → headline references the NEXT favourable "
                "wealth window from `▸ Wealth window:` line.\n"
                "     • PAST     → frame retrospectively without inventing "
                "a future date.\n"
                "  7. ❌ ABSOLUTE FINANCIAL BRAND-SAFETY (hard prohibitions):\n"
                "     • NEVER predict a SPECIFIC rupee amount or wealth "
                "figure — FORBIDDEN: '50 lakh milega', '2 crore kamaaoge', "
                "'15 lakh ki property', '₹1 crore networth', 'monthly "
                "₹2 lakh income'. Use ONLY relative language: 'income mein "
                "vridhi', 'savings strong', 'property scope strong', "
                "'corpus build hoga', 'salary jump'.\n"
                "     • NEVER predict bankruptcy / 'kangaal ho jaaoge' / "
                "'barbaad ho jaaoge' / 'sab kuch lut jaayega' / 'sadak par "
                "aa jaaoge' — soften every red verdict to 'extra-savitree "
                "phase', 'corpus protect karein', 'expansion ke liye wait'.\n"
                "     • NEVER advise loan-default / EMI-skip / tax-evasion / "
                "GST-fraud / under-invoicing / black-money / havala / "
                "any illegal financial behaviour — engine NEVER endorses "
                "fraud.\n"
                "     • NEVER predict lottery / satta / matka / KBC / "
                "jackpot win — engine NEVER endorses gambling.\n"
                "     • Bucket-aware framing:\n"
                "       - loan_clearance → frame as 'loan close hone ka "
                "natural cosmic window — discipline + EMI continue + bank "
                "ke saath transparent communication'.\n"
                "       - property_purchase → 'cosmic window favourable — "
                "RERA-registered property, legal title verification, CA-"
                "vetted budget zaroor karein'.\n"
                "       - investment_return → 'investments market risk ke "
                "adheen hain — SEBI-registered advisor + diversification "
                "essential'.\n"
                "       - inheritance_timing → frame with empathy, NEVER "
                "promise specific amount, NEVER predict elder's death; "
                "frame as 'paitrak sampatti / virasat ka cosmic timing'.\n"
                "       - sudden_windfall → ALWAYS soften — 'sudden-money "
                "yog dikh raha hai (bonus / arrears / past-due / "
                "professional opportunity), NOT lottery/satta'. Engine "
                "NEVER endorses gambling-route windfall.\n"
                "  8. If `brand_safety_warnings` array in the verdict block "
                "is non-empty, internalise EACH warning as an absolute "
                "constraint for this turn.\n"
                "  9. DATE-PRECISION LOCK — the engine emits dates in "
                "month-year resolution ONLY (e.g. 'Jul 2025 → Jun 2026'). "
                "You MUST cite dates in the SAME resolution as printed. "
                "FORBIDDEN: inventing specific day numbers like "
                "'2025-07-25' or '15 July 2025' or '25/07/2025' when the "
                "engine only gave you 'Jul 2025'. Just write 'Jul 2025 "
                "se Jun 2026 ka window' or 'July 2025 → June 2026'. "
                "ZERO day-precision unless the engine itself printed a "
                "day number.\n"
                " 10. MANDATORY FINANCIAL-ADVISOR CITATION — every wealth "
                "reply MUST contain at least ONE explicit advisor-cite "
                "phrase (examples: 'qualified CA se consult karein', "
                "'SEBI-registered financial advisor se baat karein', "
                "'tax consultant ki guidance lein', 'financial planner ki "
                "salaah zaroor lein'). This is non-negotiable. The "
                "engine's brand_safety_warnings already include this — "
                "narrate it visibly.\n\n"
                + wealth_verdict_block
            ),
        })

    # ── HEALTH NARRATOR TURN-LEVEL OVERRIDE ───────────────────────────────────
    # Appended LAST after career so recency bias keeps the lock authoritative.
    # Mirror of stock/love/career narrator overrides + STRICT brand-safety
    # guards specific to medical content: NEVER predict death, NEVER replace
    # medical advice, NEVER tell user to skip surgery, NEVER blame chart for
    # addiction, ALWAYS recommend doctor consultation, surface mental-health
    # helplines on mental_health bucket, gender-sensitive reproductive
    # guidance.
    if health_verdict_block and _NARRATIVE_MODE:
        # Phase 4.6 — narrative-mode health override. Mirror of wealth/love/
        # career pattern: keep engine facts as background, drop the heavy
        # "narrate verbatim / D6/D8 dasamsha / KP cusp on H6" surface
        # citations. CRISIS-SAFETY (mental-health helpline + qualified-doctor
        # cite for serious buckets) IS PRESERVED — it flows through
        # _CRISIS_MARKER_RX which already protects helpline/suicide/self-
        # harm/Hinglish-crisis tokens from the disclaimer-strip pass.
        msgs.append({
            "role": "system",
            "content": (
                "HEALTH FACTS (engine-locked ground truth — narrate as a fused "
                "combo verdict, do NOT enumerate, do NOT pivot to other "
                "topics):\n"
                "  • Use the verdict bucket (chronic_illness / acute_illness "
                "/ mental_health / surgery_timing / recovery_timing / "
                "longevity_general / injury_accident / addiction / "
                "female_reproductive / male_reproductive / parent_health / "
                "general_wellness), the verdict status (green_go / yellow_wait "
                "/ slow_burn / red_avoid), the timing window dates, and "
                "dasha/6L/8L/karaka names EXACTLY as printed below — no "
                "rounding, no swapping, no day-precision invention.\n"
                "  • Do NOT contradict the verdict bucket / status — frame "
                "the answer consistent with it.\n"
                "  • Do NOT echo printed score / 'Verdict:' / 'Reason:' / "
                "'Timing:' headers verbatim — your output shape is set by the "
                "QUESTION TYPE: NARRATIVE_ANSWER contract above.\n"
                "  • Do NOT surface 'D6 shashthamsha', 'D8 ashtamsha', "
                "'KP cuspal sub-lord on H6/H8', 'Maraka grah {planet}' as "
                "user-facing text. Translate them into human meaning.\n"
                "  • TOPIC FIDELITY — this is a HEALTH question (body / "
                "wellness / illness / surgery / mental health). Do NOT "
                "pivot to career, finance, or relationship.\n"
                "  • CRISIS-SAFETY (mandatory, never strip):\n"
                "      - mental_health bucket → MUST include qualified-"
                "doctor / mental-health-helpline cite verbatim. The crisis-"
                "marker guard preserves these from any post-processing.\n"
                "      - surgery_timing → never tell user to skip surgery; "
                "frame as 'window favourable hai par MD se confirm karein'.\n"
                "      - addiction → preserve self-worth; never blame chart "
                "for addiction; recommend professional support.\n"
                "      - longevity_general → never predict death / specific "
                "year-of-death.\n"
                "  • Speak as Cosmic Intelligence — never AI / LLM / GPT / "
                "model.\n\n"
                + health_verdict_block
            ),
        })
    elif health_verdict_block:
        msgs.append({
            "role": "system",
            "content": (
                "🔒 HEALTH NARRATOR OVERRIDE — this turn is a health / "
                "wellness / illness / surgery / mental-health / addiction / "
                "parent-health / longevity question. The cosmic engine has "
                "already computed the verdict bucket (chronic_illness / "
                "acute_illness / mental_health / surgery_timing / "
                "recovery_timing / longevity_general / injury_accident / "
                "addiction / female_reproductive / male_reproductive / "
                "parent_health / general_wellness), the verdict status "
                "(green_go / yellow_wait / slow_burn / red_avoid), the "
                "score, the timing window via Vimshottari + Saturn / Mars / "
                "Jupiter / Rahu-Ketu transits, the 6th-8th-12th house cross-"
                "check, the D9 + D6 (Shashtiamsa) + D30 (Trimsamsa) "
                "divisional overlay, the KP cuspal sub-lord on cusps "
                "1/6/8/12, the Atmakaraka, the Arishta / Ayushkara yogas, "
                "the Sade Sati phase, and the remedy for you. You are NOT "
                "diagnosing — you are NARRATING a locked verdict in warm "
                "Hinglish.\n\n"
                "ABSOLUTE RULES (these override every other instruction this turn):\n"
                "  1. The verdict bucket and verdict status are FINAL. Do NOT "
                "contradict, do NOT hedge into the opposite bucket, do NOT "
                "add 'lekin actually…' reversals. Use the verdict text as "
                "the spine of your reply.\n"
                "  2. Copy timing windows (Vimshottari Maha-Antar, Saturn "
                "transit window, Jupiter/Mars/Rahu-Ketu transit windows) "
                "EXACTLY as printed in the locked block. No rounding, no "
                "shifting, no blending.\n"
                "  3. Copy score, dasha-lord names, lagnesh, Atmakaraka, "
                "house numbers, yoga names, body-area names, and remedy "
                "VERBATIM. No paraphrasing of numbers or planet names.\n"
                "  4. NEVER reveal AI / LLM / GPT / model — brand voice is "
                "'Powered by Advanced Cosmic Intelligence'. Speak as the "
                "cosmic intelligence, never as a chatbot.\n"
                "  5. NO fake/random fallbacks. If the engine is silent on a "
                "specific date or symptom, do NOT invent it. Vague phrases "
                "like 'jaldi theek ho jaayenge' without a window are "
                "FORBIDDEN — only narrate what the engine produced.\n"
                "  6. TENSE-AWARE FRAMING (mandatory) — read the "
                "'QUESTION TENSE:' line in the verdict block:\n"
                "     • PRESENT  → headline references CURRENT Maha-Antar-"
                "Pratyantar lords + active Saturn/Mars transit. Do NOT "
                "lead with 'agle X mahine mein…' for a 'abhi/aaj/currently/"
                "right now/chal raha hai' question.\n"
                "     • FUTURE   → headline references next dasha window + "
                "upcoming Saturn/Jupiter/Mars transits. Do NOT lead with "
                "'abhi to…' for a 'kab/will/karega/hoga/rahega' question.\n"
                "     • GENERAL  → balance both naturally.\n"
                "  7. STRICT MEDICAL BRAND-SAFETY GUARDS (mandatory always):\n"
                "     • NEVER predict death, NEVER predict 'aap ki mrityu', "
                "NEVER predict 'X saal tak life hai'. Even on longevity_"
                "general bucket, frame as 'cosmic vitality strong/medium/"
                "needs care', NEVER as a death timeline. ZERO TOLERANCE.\n"
                "     • NEVER replace medical advice. Cosmic insight is "
                "complementary, NOT a substitute for diagnosis or "
                "treatment. Every reply MUST end with or contain a clear "
                "doctor-consultation line.\n"
                "     • NEVER tell the user to skip surgery, stop medicine, "
                "discontinue treatment, or delay hospital visit. Even on "
                "red_avoid surgery_timing, frame as 'agar surgery urgent "
                "hai to doctor ki advice manein, cosmic window sirf "
                "supplementary timing reference hai'.\n"
                "     • NEVER blame the chart for addiction. Addiction is a "
                "treatable condition. Frame as 'natal pattern indicates "
                "vulnerability — recovery window favourable hai if you "
                "engage professional help'. Recommend rehab / therapist / "
                "support group, never 'mantra ki wajah se chhoot jayega'.\n"
                "     • mental_health bucket → ALWAYS surface India helplines "
                "verbatim from the engine block (iCall 9152987821, "
                "Vandrevala Foundation 1860-2662-345). NEVER replace these "
                "with mantra-only advice.\n"
                "     • female_reproductive / male_reproductive → use "
                "respectful, non-judgemental language. NEVER moralise. "
                "NEVER promise IVF success or pregnancy on a specific "
                "date. Always pair with 'gynec/urologist consultation '\n"
                "       'parallel chalti rahe'.\n"
                "     • parent_health → frame with empathy, NEVER predict "
                "parent's death, NEVER frame as inevitable. Encourage "
                "user to ensure parent has medical care + family support.\n"
                "     • surgery_timing → green_go ≠ 'definitely safe'. "
                "Always frame as 'cosmic window favourable — proceed only "
                "with surgeon's clearance'. red_avoid ≠ 'cancel surgery'. "
                "Frame as 'cosmic window mein resistance hai — if elective, "
                "consider rescheduling AFTER discussion with doctor; if "
                "urgent, doctor's call final hai'.\n"
                "  8. If `brand_safety_warnings` array in the verdict block "
                "is non-empty, internalise EACH warning as an absolute "
                "constraint for this turn.\n"
                "  9. DATE-PRECISION LOCK — the engine emits dates in "
                "month-year resolution ONLY (e.g. 'Jul 2025 → Jun 2026'). "
                "You MUST cite dates in the SAME resolution as printed. "
                "FORBIDDEN: inventing specific day numbers like "
                "'2025-07-25' or '15 July 2025' or '25/07/2025' when the "
                "engine only gave you 'Jul 2025'. Just write 'Jul 2025 "
                "se Jun 2026 ka window' or 'July 2025 → June 2026'. "
                "ZERO day-precision unless the engine itself printed a "
                "day number.\n"
                " 10. MANDATORY DOCTOR-CONSULT CITATION — every health "
                "reply MUST contain at least ONE explicit doctor-"
                "consultation phrase (examples: 'doctor se consult karein', "
                "'physician se baat karein', 'medical advice zaroor lein', "
                "'qualified doctor ki guidance lein'). This is non-"
                "negotiable. The engine's brand_safety_warnings already "
                "include this — narrate it visibly.\n\n"
                + health_verdict_block
            ),
        })

    msgs.append({"role": "user", "content": user})
    return msgs


# ── Topic classifier (lightweight, keyword-based) ─────────────────────────────

_TOPIC_KW = {
    "marriage":    ["marriage", "shaadi", "shadi", "spouse", "wife", "husband", "vivah", "partner",
                    "biwi", "pati", "patni", "dulhan", "dulha", "vivaah", "rishta-shadi", "engagement",
                    "sagai", "mangni", "kalatra", "saptam"],
    "career":      ["career", "job", "naukri", "naukari", "business", "vyapar", "vyapaar", "promotion",
                    "kaam", "office", "boss", "salary", "transfer", "dhanda", "interview", "resign",
                    "switch", "freelance", "startup"],
    "finance":     ["money", "wealth", "finance", "paisa", "paise", "dhan", "loan", "debt", "karz",
                    "investment", "invest", "investor", "investing", "share", "shares", "stock",
                    "stocks", "property", "lottery", "income", "tax", "loss", "profit", "savings",
                    "fixed deposit", "mutual fund", "mutual funds", "sip", "lumpsum", "crypto",
                    "bitcoin", "ethereum", "trading", "trader", "intraday", "swing", "scalping",
                    "f&o", "fno", "futures", "options", "derivative", "derivatives", "equity",
                    "equities", "portfolio", "demat", "broker", "brokerage", "nifty", "sensex",
                    "share market", "stock market", "share bazar", "stock bazar", "shaire bazar",
                    "shaire bazaar", "bazar", "sector"],
    "health":      ["health", "illness", "disease", "swasthya", "bimari", "operation", "surgery",
                    "doctor", "hospital", "rog", "kasht", "dard", "pain", "tabiyat", "fever",
                    "diabetes", "blood pressure", "bp", "cancer", "heart", "depression", "anxiety",
                    "mental health", "stress"],
    "education":   ["study", "exam", "education", "padhai", "result", "college", "degree", "school",
                    "vidya", "graduation", "phd", "masters", "ias", "upsc", "neet", "jee", "gate",
                    "competitive", "scholarship", "admission"],
    "relationship":["love", "relationship", "girlfriend", "boyfriend", "gf", "bf", "breakup",
                    "break-up", "patch-up", "patchup", "rishta", "rishtey", "pyaar", "pyar",
                    "ishq", "mohabbat", "romance", "romantic", "ladka", "ladki", "dating",
                    "crush", "ex", "love marriage", "inter-caste", "family opposition",
                    "affair", "cheating", "dhokha", "bewafai", "chakkar",
                    "soulmate", "jeevansathi", "sathi", "saathi",
                    "propose", "izhaar", "izhar", "long-distance", "long distance", "ldr",
                    "one-sided", "one sided", "ektarafa",
                    "compatible", "compatibility", "jodi", "reconciliation", "reunion"],
    "travel":      ["travel", "abroad", "videsh", "foreign", "yatra", "visa", "passport", "trip",
                    "settlement", "usa", "u.s.", "canada", "uk", "u.k.", "australia", "germany",
                    "dubai", "migrate", "immigration", "tirth", "pilgrimage"],
    "child":       ["child", "santan", "santaan", "baby", "pregnan", "putra", "putri", "beti", "beta",
                    "garbh", "ivf", "infertility", "adoption", "miscarriage", "delivery"],
    "litigation":  ["court", "case", "mukadma", "lawsuit", "legal", "vakil", "lawyer", "police",
                    "fir", "jail", "bail", "judgement", "decision", "appeal", "divorce case",
                    "property dispute"],
    "property":    ["house", "ghar", "makaan", "property", "plot", "flat", "land", "zameen",
                    "real estate", "construction", "naya ghar", "purchase", "selling house"],
    "vehicle":     ["car", "bike", "vehicle", "gaadi", "scooter", "motorcycle", "vahan"],
    "vastu":       ["vastu", "ghar ka vastu", "office vastu", "direction", "disha", "puja room",
                    "kitchen", "bedroom direction", "main door", "entrance"],
    "remedy":      ["remedy", "upay", "upaay", "mantra", "puja", "stone", "ratna", "gemstone",
                    "donation", "daan", "vrat", "fasting", "totka", "yantra", "rudraksha", "ritual",
                    "havan", "abhishek"],
    "spiritual":   ["moksha", "spiritual", "guru", "deeksha", "meditation", "dhyan", "tapasya",
                    "purpose of life", "destiny", "karma", "previous birth", "purva janma"],
    "family":      ["family", "parivar", "parents", "mata", "pita", "father", "mother", "bhai",
                    "behan", "in-laws", "sasural", "saas", "sasur"],
}

# Devanagari (Hindi-script) keywords per topic — matched separately so we
# don't have to lowercase non-Latin text. Substring matching is safe here
# because each entry is itself a meaningful Hindi word.
_TOPIC_KW_DEV = {
    "marriage":    ["शादी", "विवाह", "पति", "पत्नी", "जीवनसाथी", "सगाई", "मंगनी", "दूल्हा", "दुल्हन"],
    "career":      ["नौकरी", "करियर", "व्यापार", "व्यवसाय", "काम", "धंधा", "तरक्की", "प्रमोशन", "ट्रांसफर", "इंटरव्यू"],
    "finance":     ["पैसा", "पैसे", "धन", "कर्ज", "क़र्ज़", "लोन", "आय", "नुकसान", "मुनाफा", "संपत्ति", "लक्ष्मी"],
    "health":      ["स्वास्थ्य", "बीमारी", "रोग", "दर्द", "पेट", "तबीयत", "बुखार", "ऑपरेशन", "अस्पताल", "तनाव", "नींद"],
    "education":   ["पढ़ाई", "विद्या", "परीक्षा", "रिज़ल्ट", "रिजल्ट", "कॉलेज", "स्कूल", "डिग्री", "एडमिशन"],
    "relationship":["प्यार", "प्रेम", "रिश्ता", "रिश्ते", "लड़का", "लड़की", "ब्रेकअप", "गर्लफ्रेंड", "बॉयफ्रेंड"],
    "travel":      ["यात्रा", "विदेश", "विसा", "वीज़ा", "पासपोर्ट", "तीर्थ", "प्रवास"],
    "child":       ["संतान", "बच्चा", "बच्ची", "पुत्र", "पुत्री", "गर्भ", "गर्भावस्था", "बेटा", "बेटी"],
    "litigation":  ["कोर्ट", "मुकदमा", "केस", "वकील", "पुलिस", "जेल", "तलाक"],
    "property":    ["घर", "मकान", "ज़मीन", "जमीन", "प्लॉट", "फ्लैट", "संपत्ति"],
    "vehicle":     ["गाड़ी", "वाहन", "बाइक", "स्कूटर"],
    "vastu":       ["वास्तु", "दिशा", "रसोई", "बेडरूम", "मुख्य द्वार", "पूजा घर"],
    "remedy":      ["उपाय", "मंत्र", "पूजा", "रत्न", "दान", "व्रत", "हवन", "टोटका", "यंत्र", "रुद्राक्ष"],
    "spiritual":   ["मोक्ष", "आध्यात्मिक", "गुरु", "ध्यान", "तपस्या", "कर्म", "पूर्व जन्म"],
    "family":      ["परिवार", "माता", "पिता", "भाई", "बहन", "ससुराल", "सास", "ससुर"],
}


def _token_budget_for(topic: str, question: str) -> int:
    """
    Cost-optimization: dynamic max_tokens by question complexity.

    Heavy topics (marriage/career/finance/child) need ALL mandatory citations
    (D9 + KP + Vimshottari + Jaimini UL + Chara) → 380 tokens.

    Medium topics (relationship/health/general timing) → 280 tokens.

    Light topics (greeting/remedy quick-ask/concept Q) → 180 tokens.

    Single-word factual ("aaj kya din hai", "om kya hai") → 120 tokens.

    Returns max_tokens cap. Reduces avg cost ~30-40% vs flat 380.
    """
    q = (question or "").strip().lower()
    word_count = len(q.split())

    # Ultra-short factual / greeting
    if word_count <= 4 and not any(
        k in q for k in ("kab", "kyun", "kaise", "kaisi", "when", "why", "how")
    ):
        return 120

    # Heavy = full BPHS analysis with 4-5 mandatory citations
    if topic in ("marriage", "career", "finance", "child"):
        return 380

    # Medium = single-paddhati answer
    if topic in ("relationship", "health", "remedy"):
        return 240

    # General concept / unknown
    return 200


# ── Fix-A: AI Ear → topic mapping ────────────────────────────────────────────
# AI Ear's `domain` vocabulary (intent_extractor.DOMAINS) is broader than the
# legacy `_classify_topic` regex vocabulary (_TOPIC_KW.keys()). This map
# collapses AI Ear domains down to the topic value the rest of the pipeline
# (engine routing, prompt builders, brevity guards) reads.
#
# When AI Ear succeeds with high confidence we trust this mapping over the
# regex topic classifier — the LLM has actually understood the sentence,
# while the regex only counts keyword hits.
# ── Sprint-25 Fix-B: AI-Ear bucket trust contract ──────────────────────────
# Each engine has its own bucket vocabulary. When AI Ear's domain matches
# the engine AND its primary intent has a bucket from that engine's vocab,
# we hand the bucket to the engine and skip the engine's regex classifier.
# Confidence floor + env gate both apply; failure = silent fall-through to
# regex.
_AI_EAR_TOPIC_TO_DOMAINS: dict[str, tuple[str, ...]] = {
    "stock":    ("stock",),
    "wealth":   ("wealth",),
    "love":     ("love",),
    "career":   ("career",),
    "health":   ("health",),
    "marriage": ("marriage",),
}


# Sprint-25 Fix-F: AI Ear marriage bucket → engine subtype map. AI Ear emits
# 5 marriage buckets (timing|remedy|analysis|compatibility|reconciliation);
# the marriage engine has 4 subtypes (timing|remedy|analysis|general).
_MARRIAGE_BUCKET_TO_SUBTYPE: dict[str, str] = {
    "timing":         "timing",
    "remedy":         "remedy",
    "analysis":       "analysis",
    "compatibility":  "analysis",   # compatibility is a flavor of analysis
    "reconciliation": "analysis",   # reconciliation is also analytical
}


def _ai_ear_bucket_for(out_meta: dict | None,
                       engine_key: str,
                       conf_floor: float = 0.70) -> str | None:
    """Return the AI Ear primary bucket for `engine_key` (one of: stock, love,
    career, wealth, health) when the extraction is confident AND the AI
    Ear's domain matches the engine. Returns None on any miss — the engine
    will then fall back to its regex classifier (existing behaviour).

    Engines internally validate the returned bucket against their own
    vocabulary (`_VALID_*_BUCKETS`) so unknown / cross-domain buckets are
    rejected one more time downstream.
    """
    if os.environ.get("ENGINE_BUCKET_TRUST", "1") == "0":
        return None
    if not isinstance(out_meta, dict):
        return None
    extraction = out_meta.get("intent_extraction")
    if not isinstance(extraction, dict):
        return None
    try:
        if float(extraction.get("confidence") or 0.0) < conf_floor:
            return None
    except (TypeError, ValueError):
        return None
    if (extraction.get("source") or "ai_ear") != "ai_ear":
        return None
    ear_domain = (extraction.get("domain") or "").strip().lower()
    expected_domains = _AI_EAR_TOPIC_TO_DOMAINS.get(engine_key, ())
    if ear_domain not in expected_domains:
        return None
    intents = extraction.get("intents") or []
    if not intents or not isinstance(intents[0], dict):
        return None
    bucket = (intents[0].get("bucket") or "").strip().lower()
    return bucket or None


_AI_EAR_DOMAIN_TO_TOPIC: dict[str, str] = {
    "marriage":   "marriage",
    "stock":      "finance",     # stock engine is gated under topic=finance
    "wealth":     "finance",     # wealth engine is gated under topic=finance
    "love":       "relationship",
    "career":     "career",
    "health":     "health",
    "remedy":     "remedy",
    "spiritual":  "spiritual",
    "education":  "education",
    "child":      "child",
    "litigation": "litigation",
    "property":   "property",
    "vehicle":    "vehicle",
    "vastu":      "vastu",
    "family":     "family",
    "travel":     "travel",
    "general":    "general",
}


def _classify_topic(question: str) -> str:
    """
    Topic classifier with multi-topic detection.
    - Score each topic by number of distinct keyword matches in the question.
    - If 2+ topics score ≥ 1, return 'general' so the universal multi-part
      focus block + broad KP house set are used (devotee asked about more
      than one area at once).
    - Otherwise return the single highest-scoring topic.
    """
    q_raw = (question or "")
    q = q_raw.lower()
    if not q.strip():
        return "general"

    import re
    scores: dict[str, int] = {}
    for topic, words in _TOPIC_KW.items():
        hits = 0
        for w in words:
            # Word-boundary match for short keywords (≤4 chars) to avoid
            # false positives like "us" inside "business". Longer keywords
            # use plain substring match (faster + handles hyphenation).
            if len(w) <= 4:
                if re.search(r"\b" + re.escape(w) + r"\b", q):
                    hits += 1
            else:
                if w in q:
                    hits += 1
        if hits > 0:
            scores[topic] = hits

    # Devanagari pass — substring match is safe for full Hindi words.
    for topic, words in _TOPIC_KW_DEV.items():
        hits = 0
        for w in words:
            if w in q_raw:
                hits += 1
        if hits > 0:
            scores[topic] = scores.get(topic, 0) + hits

    if not scores:
        return "general"

    # Multiple distinct topics touched → universal/general handling.
    if len(scores) >= 2:
        return "general"

    return next(iter(scores))


# ── ASTRO vs GENERAL mode classifier ─────────────────────────────────────────
# Routes the question into one of two pipelines:
#   "astro"   → personal life-event prediction (uses chart + deterministic
#               engines + narrator scaffolding). Default.
#   "general" → concept / comparison / explanation question. AI answers from
#               its own knowledge; no chart, no scaffolding, ChatGPT-style.
# Heuristic: GENERAL only if a concept signal is present AND no personal
# pronoun / future-tense / timing signal is present. Otherwise ASTRO.
_GENERAL_CONCEPT_SIGNALS = (
    # English / Hinglish concept words
    "what is", "what are", "what's", "explain", "explanation",
    "difference between", "difference b/w", "what is the difference",
    " vs ", " v/s ", " versus ", "compare ", "comparison",
    "how does", "how do ", "how works", "how it works", "meaning of",
    "definition of", "types of", "list of", "examples of", "kinds of",
    # Hinglish concept words
    "kya hai", "kya hota", "kya hoti", "kya hote", "kya matlab",
    "matlab kya", "samjhao", "samjhaiye", "samjha do", "samjhna hai",
    "antar kya", "fark kya", "kya antar", "kya fark", "kaun se",
    "kitne prakar", "kitne type", "ke prakar", "ke type",
    "kaise kaam", "kaise work",
    # Knowledge / origin / authorship / history questions (general, not personal)
    "kisne likha", "kisne banaya", "kisne banayi", "kisne banaai",
    "kisne banai", "kisne bani", "kisne shuru",
    "kis ne likha", "kis ne banaya", "kis ne banayi", "kis ne banai",
    "kaun ne likha", "kaun ne banaya", "kaun ne banayi",
    "kisne diya", "kisne khoja", "kisne discover", "kisne invent",
    "kaise bani", "kaise bana", "kaise shuru hua",
    "kab shuru", "kab bana", "kab likha", "kab aaya", "kahan se aaya",
    "kahan se shuru", "history kya", "history of ", "history",
    "itihas kya", "itihas", "ka itihas", "ki history",
    "origin of", "founder of", "who wrote", "who made", "who created",
    "who founded", "who discovered", "who invented", "when did",
    "when was", "where did", "where does", "where is the origin",
    # Devanagari concept words
    "क्या है", "क्या होता", "क्या होती", "क्या मतलब", "मतलब क्या",
    "अंतर क्या", "फर्क क्या", "क्या अंतर", "क्या फर्क",
    "समझाओ", "समझाइये", "समझाइए", "कैसे काम",
    # Devanagari knowledge/origin/authorship
    "किसने लिखा", "किसने बनाया", "किसने शुरू", "कौन ने लिखा",
    "किसने दिया", "किसने खोजा",
    "कब शुरू", "कब बना", "कब लिखा", "कब आया",
    "कहां से", "कहाँ से", "इतिहास क्या",
)

# Personal life-event signals — if ANY appear, we treat as astro even when
# concept words are present (e.g. "meri shaadi kab hogi" — concept word "kab"
# but personal predict).
_PERSONAL_PREDICT_SIGNALS = (
    # personal pronouns
    "mera ", "meri ", "mere ", "mujhe", "mujhko", "mujh ko", "humara",
    "hamari", "hamare", "hamein", "humein",
    "my ", "mine ", "i will", "i am", "i have", "will i ", "for me",
    "should i", "can i ", "am i ",
    # Devanagari personal
    "मेरा", "मेरी", "मेरे", "मुझे", "मुझको", "हमारा", "हमारी", "हमें",
    # personal life-events / timing markers (predictive intent)
    "kab hoga", "kab hogi", "kab honge", "kab milega", "kab milegi",
    "kab aayega", "kab aayegi", "kab tak", "kab shaadi", "kab vivah",
    "kaisa rahega", "kaisi rahegi", "kaise rahega",
    "when will", "when do i", "when can i",
    "कब होगा", "कब होगी", "कब मिलेगा", "कब मिलेगी", "कब तक", "कब शादी",
)


_COSMIC_ENGINE_SYSTEM_TEMPLATE = """ROLE:
You are an Advanced Cosmic Intelligence Engine.
You are NOT an AI assistant.
You speak like a real expert — natural, clear, confident.

------------------------------------------
MODEL TEMPERAMENT (STRICT BEHAVIOR CONTROL)
------------------------------------------

- Keep responses stable, not random
- Avoid creativity beyond given data
- Maintain consistency across same questions

Behavior rules:
- No over-explaining
- No dramatic tone
- No unnecessary expansion
- No repetition

Think → controlled, precise, human-like

------------------------------------------
MODE SWITCH (CRITICAL)
------------------------------------------

You operate in TWO MODES:

1. ASTRO MODE (when backend data is provided)
2. GENERAL MODE (when no backend data is provided)

------------------------------------------
ASTRO MODE (STRICT)
------------------------------------------

If structured backend data is given:

Input will include:
- verdict
- timeline
- reasons[]
- remedy

RULES:
- Do NOT create astrology logic
- Do NOT modify facts or dates
- Do NOT guess anything

You ONLY convert result into natural human explanation

FORMAT:
1. Direct answer
2. Reason (2–3 lines)
3. Timeline
4. Optional advice

CONFIDENCE:
- Speak with certainty
- Example: "shaadi hogi"
- NOT: "ho sakti hai"

STRICT BAN WORDS:
- maybe / possible / likely / chances
- ho sakta hai / shayad / sambhavna
- "based on your chart"
- "I think"

------------------------------------------
GENERAL MODE (NO BACKEND DATA)
------------------------------------------

If no backend data:

- Answer like ChatGPT
- Use logic + knowledge
- Be helpful and clear

STYLE:
- Simple explanation
- Balanced comparison
- Clear conclusion

------------------------------------------
TONE (VERY IMPORTANT)
------------------------------------------

- Natural human tone
- Friendly but not emotional
- Expert but not robotic

DO NOT:
- Use "Pranam"
- Use fake sympathy
- Over-praise user

USE:
- "Seedhi baat"
- "Simple samjho"
- "Clear difference yeh hai"

------------------------------------------
LANGUAGE CONTROL
------------------------------------------

- Match user language:
  Hindi → Hindi
  Hinglish → Hinglish
  English → English

- If user preference given → override

REPLY ENTIRELY IN: {lang_name}.

------------------------------------------
CONSISTENCY LOCK
------------------------------------------

- Same question → same answer
- No contradiction
- No randomness

------------------------------------------
OUTPUT CONTROL — JUDGE THE QUESTION
------------------------------------------

You are smart. READ the user's question and decide reply length + depth
yourself. Match the answer to what was actually asked. NEVER pad simple
questions with unrequested dasha / houses / remedies. NEVER under-answer
big life questions.

Calibration guide (NOT rigid rules — use judgment):

  • Simple chart-fact lookup
    ("mera rashi kya hai", "lagna batao", "current dasha kya hai",
     "nakshatra kya hai", "moon sign batao")
    → 2-3 sentences. State the fact + ONE natural personality/nature line.
    → NO houses, NO dasha breakdown, NO remedy, NO affirmation.

  • Short follow-up / clarification
    ("aur batao", "matlab kya hai", "iska reason kya hai")
    → 3-5 sentences. Go one layer deeper on the SAME thread. Don't restart.

  • Real analytical question
    ("kyun ho raha hai", "kaun sa grah responsible", "7th lord kahan",
     "career mein kya scope hai")
    → 1-2 short paragraphs (60-120 words). Specific, grounded in the chart.

  • Big life question
    ("meri zindagi kaisi rahegi", "shaadi kaisi rahegi", "career path")
    → 2-3 paragraphs (120-180 words). Full analytical depth.

Rules that ALWAYS hold regardless of length:
  - No long lectures, no padding, no repetition
  - Active voice, confident, no hedging
  - If a remedy doesn't fit the question, DON'T add one

------------------------------------------
HARD SAFETY
------------------------------------------

If backend data exists:
→ NEVER override it

If backend data does NOT exist:
→ Answer normally

------------------------------------------
FINAL BEHAVIOR

You behave like:
- A real expert
- Calm, controlled, and precise
- Smart like ChatGPT
- Accurate like a calculation engine

Never break character.

==========================================
🚨 PRE-REPLY CHECK (MANDATORY — RUN BEFORE WRITING)
==========================================

Before you type a single word, ask yourself:

  "What did the user ACTUALLY ask?"

Then write ONLY what answers that exact question. Nothing more.

HARD RULES (these override every other instruction in this prompt,
INCLUDING any FOCUS / KP / TRANSIT / INTEL block below):

1. If the user asked a SIMPLE FACT LOOKUP — e.g. "mera rashi kya hai",
   "lagna batao", "nakshatra", "current dasha", "moon sign", "gana",
   "yoni", "tatva", "varna" — your reply MUST be 2-3 sentences ONLY.
   • Sentence 1: state the fact directly from the chart.
   • Sentence 2: ONE line of natural personality / nature about it.
   • STOP. Do NOT add house analysis. Do NOT add dasha implications.
     Do NOT add "isliye dhyan dena zaroori hai". Do NOT add a remedy.
     Do NOT add an "Isliye..." closing line. Just fact + flavor. Done.

2. If the user asked a SHORT FOLLOW-UP ("aur batao", "matlab",
   "kyun", "iska reason"), reply in 3-5 sentences going ONE layer
   deeper on the same thread. Don't restart the whole reading.

3. NEVER dump the kundli. The chart, KP, transit, and intelligence
   blocks below are REFERENCE for you to look things up. They are NOT
   a checklist of things you must mention. Mention only what answers
   the user's actual question.

4. NEVER add a remedy unless the user asked for one OR the question is
   clearly a problem they want solved. A "what is my X" question does
   NOT need a remedy.

5. The FOCUS block below describes the topic — but length and depth
   are decided HERE, not there. If the FOCUS block says "3 paragraphs"
   but the user asked a simple fact, IGNORE the focus block's length
   and use rule 1 above.

If you violate these rules, you are wrong even if the astrology is right.
"""


def _cosmic_engine_system(lang_name: str) -> str:
    return _COSMIC_ENGINE_SYSTEM_TEMPLATE.format(lang_name=lang_name)


_GENERAL_LEAK_PATTERNS = [
    re.compile(r"\b(aap?ki|aap?ke|aap?ka|tumhari|tumhare|tumhara)\s+(kundli|janam|chart|rashi|nakshatra|lagna|ascendant|mahadasha|antardasha|dasha|gochar|jaap|graha|jyotish)", re.I),
    re.compile(r"\byour\s+(kundli|chart|birth\s*chart|natal\s*chart|moon\s+sign|sun\s+sign|ascendant|rashi|nakshatra|mahadasha|dasha|horoscope)", re.I),
    re.compile(r"\b(aapk[ie]|tumhare)\s+(saatv[ei]?n|saptam|7th|8th|10th|11th|5th|2nd)\s+(house|bhav|ghar)", re.I),
    re.compile(r"\b(based on your|according to your|as per your)\s+(chart|kundli|horoscope|birth)", re.I),
    re.compile(r"\b\d{2,5}\s*(times|baar|jaap)\b.*(mantra|gayatri|hanuman|maha\s*mrityunjaya|om)", re.I),
    re.compile(r"\b(donate|daan\s+kar[ei]?n|vrat\s+rakh[ei]?n)\b.*\b(shanivar|mangalvar|guruvar|monday|saturday)", re.I),
    re.compile(r"\bremedy\s*[:\-—]\s*", re.I),
    re.compile(r"\bupay\s*[:\-—]\s*", re.I),
]


_SIMPLE_SAMJHO_RE = re.compile(r"^\s*simple\s+samjho\s*[—\-:]", re.I)
_FINAL_LINE_RE    = re.compile(r"(^|\n)\s*final\s*[:\-—]", re.I)


def _general_reply_violates_structure(text: str) -> bool:
    """True if the general-mode reply does NOT start with 'Simple samjho — '
    OR does NOT contain a 'Final: ...' closing line. Triggers a regenerate."""
    if not text:
        return True
    if not _SIMPLE_SAMJHO_RE.search(text):
        return True
    if not _FINAL_LINE_RE.search(text):
        return True
    return False


def _general_reply_leaks_chart(text: str) -> bool:
    """True if a general-mode reply illegally references the user's personal
    chart, dasha, rashi, or pushes a forced remedy. Triggers a regenerate."""
    if not text:
        return False
    for rgx in _GENERAL_LEAK_PATTERNS:
        if rgx.search(text):
            return True
    return False


# ── Marriage narrator validator ──────────────────────────────────────────────
# After the AI writes its natural marriage reply, we must verify it actually
# echoed the deterministic engine's window string verbatim. If the AI rounded
# ("around 2027"), shifted the year, or dropped the window entirely → regen
# with a hard-override prompt.
_MARRIAGE_BANNED_LABELS = re.compile(
    r"\b(reason|timing|remedy|vajah|samay|7th\s*lord|kalatra[-\s]?karaka)\s*[:\-—]",
    re.I,
)
_MARRIAGE_BANNED_GREETINGS = re.compile(
    r"\b(pranam|namaste|dekhiye\s+beta|acharya\s+ji|pandit\s+ji|beta\s*[,!])",
    re.I,
)


def _marriage_reply_violates(text: str, locked_window: str) -> tuple[bool, str]:
    """Validate AI's marriage narration against locked engine facts.

    Returns (violated, reason). Triggers a single regenerate when True.
    """
    if not text:
        return True, "empty"
    if locked_window:
        # Window must appear verbatim — case/whitespace tolerant only.
        norm_t = re.sub(r"\s+", " ", text).lower()
        norm_w = re.sub(r"\s+", " ", locked_window).lower()
        if norm_w not in norm_t:
            return True, f"missing_window:{locked_window!r}"
    if _MARRIAGE_BANNED_LABELS.search(text):
        return True, "jargon_label"
    if _MARRIAGE_BANNED_GREETINGS.search(text):
        return True, "guru_greeting"
    return False, ""


_SIMPLE_DEFINITION_HEAD = (
    "kya hai", "kya hota hai", "kya hoti hai", "kya hote hain",
    "kya matlab", "matlab kya", "kise kehte", "kya kehte",
    "what is", "what's", "what are", "meaning of", "definition of",
    "क्या है", "क्या होता है", "क्या होती है", "क्या मतलब",
)
_EXPLAIN_SIGNALS = (
    "kaise", "difference", "antar", "fark", " vs ", " v/s ", " versus ",
    "compare", "explain", "samjhao", "samjhaiye", "samjha do",
    "kisne", "kis ne", "kaun ne", "kab shuru", "kab bana", "kab likha",
    "history", "itihas", "origin", "founder", "kahan se", "कहां से", "कहाँ से",
    "kitne prakar", "kitne type", "ke prakar", "ke type", "types of",
    "list of", "examples of", "kinds of", "how does", "how do ", "how works",
    "किसने", "कौन ने", "अंतर", "फर्क", "इतिहास", "समझाओ", "समझाइ",
)


def _classify_general_submode(question: str) -> str:
    """Classify a general-mode question as 'simple' (short definition) or
    'explain' (concept / comparison / how / origin). Used to pick the
    response format inside the Human Style prompt."""
    if not question:
        return "explain"
    q = question.lower().strip()
    # Strong "explain" signals win — even "X kya hai" can be explain-worthy if
    # it asks comparison or origin alongside.
    if any(s in q for s in _EXPLAIN_SIGNALS):
        return "explain"
    # Very short definition asks → simple. Threshold: ≤ 6 words AND contains
    # a definition opener like "kya hai" / "what is".
    word_count = len(q.split())
    if word_count <= 7 and any(s in q for s in _SIMPLE_DEFINITION_HEAD):
        return "simple"
    return "explain"


def _classify_mode_with_reason(question: str) -> tuple[str, str]:
    """Returns (mode, human-readable-reason). mode is 'astro' or 'general'."""
    if not question:
        return ("astro", "empty question → default astro")
    q_raw = question
    q = question.lower()
    matched_concept  = [s for s in _GENERAL_CONCEPT_SIGNALS if s in q or s in q_raw]
    matched_personal = [s for s in _PERSONAL_PREDICT_SIGNALS if s in q or s in q_raw]
    if matched_concept and not matched_personal:
        return ("general", f"concept signal(s) matched={matched_concept[:3]} "
                           f"AND no personal signals")
    if matched_personal:
        return ("astro", f"personal signal(s) matched={matched_personal[:3]} "
                         f"(concept matched={matched_concept[:3]})")
    return ("astro", "no general signals → default astro")


def _classify_mode(question: str) -> str:
    """Returns 'astro' or 'general'."""
    if not question:
        return "astro"
    q_raw = question
    q = question.lower()
    has_concept  = any(s in q for s in _GENERAL_CONCEPT_SIGNALS) or \
                   any(s in q_raw for s in _GENERAL_CONCEPT_SIGNALS)
    has_personal = any(s in q for s in _PERSONAL_PREDICT_SIGNALS) or \
                   any(s in q_raw for s in _PERSONAL_PREDICT_SIGNALS)
    if has_concept and not has_personal:
        return "general"
    return "astro"


# ── Public entry point ───────────────────────────────────────────────────────

# ── Brand-safety pre-LLM guard ───────────────────────────────────────────────
# Strict ASTROLOGY-ONLY policy: this app refuses every off-topic question
# (programming help, recipes, math, weather, news, translation, general
# knowledge, entertainment, etc.) BEFORE calling the LLM. Cheap, deterministic,
# never leaks chart data and never burns OpenAI tokens on out-of-scope asks.
#
# Add a new pattern here when a real off-topic class shows up in production.
# Keep patterns tight — false positives silently refuse genuine astrology
# questions, which is the worst UX failure mode for the Ask screen.
_BRAND_UNSAFE_PATTERNS = [
    # ── Sports / matches ────────────────────────────────────────────────────
    r"\b(match|cricket|ipl|world cup|t20|odi|football|fifa|nba|tournament)\b.*\b(jeet|win|kaun|who|result|score)",
    r"\b(jeet|win|kaun|who).*\b(match|cricket|ipl|world cup|t20|odi)\b",
    r"\b(india|pakistan|australia|england|sri lanka|new zealand|south africa)\s+(vs|v|versus)\s+\w+",
    # ── Elections / politics predictions ────────────────────────────────────
    r"\b(election|chunav|vote|poll).*\b(jeet|win|kaun|who|result)",
    r"\b(modi|rahul|kejriwal|trump|biden|putin|xi jinping).*\b(jeet|win|election|kab|when)",
    # ── Lottery / gambling / market predictions ─────────────────────────────
    r"\b(lottery|jackpot|satta|matka|powerball|teer|kbc)\b",
    r"\b(stock|share|crypto|bitcoin|nifty|sensex|forex|dogecoin|ethereum)\b.*(price|prediction|tomorrow|kal|target|buy|sell)",
    # ── Generic fortune-telling about others ────────────────────────────────
    r"\bkaun (jeet|haar|marega|janega)",
    r"\bwho will (win|lose|die)",
    # ── Programming / code / tech help ──────────────────────────────────────
    r"\b(python|javascript|typescript|java|c\+\+|c#|golang|rust|kotlin|swift|php|ruby|html|css|sql)\b",
    r"\b(code|coding|program|programming|debug|compile|syntax|algorithm|api|library|framework|github|stackoverflow|leetcode)\b",
    r"\b(function|class|method|variable|loop|array|object|array)\s+(likh|likho|banao|create|write)",
    r"\b(install|download|setup|configure)\s+(app|software|package|library|module|npm|pip|apk)",
    # ── Recipes / cooking ───────────────────────────────────────────────────
    # Note: do NOT match a bare "kaise banaye" — it's used in genuine astro
    # asks like "kundli kaise banaye" / "yantra kaise banaye". Also do NOT
    # match a bare "kitchen" — kitchen direction/placement is core vastu.
    # Always pair with a food/cooking context.
    r"\b(recipe|nuskha|cooking)\b",
    r"\b(biryani|pulao|paneer|dal|sabzi|roti|paratha|samosa|chai|coffee|cake|cookie|pizza|burger|pasta|maggi|noodles|halwa|kheer|rasgulla|gulab jamun|jalebi|laddu)\b.*\b(recipe|kaise|banao|banaye|banaaye|vidhi|ingredients?|samagri|content)",
    r"\b(khaana|khana|food|breakfast|lunch|dinner|nashta)\b.*\b(kaise|recipe|banao|banaye|banaaye|ingredients?|samagri)",
    r"\bkitchen\b.*\b(recipe|kaise banaye|kaise banaaye|cook|cooking|dish|ingredients?)\b",
    # ingredients/samagri tied to a dish/cooking verb in either order — covers
    # "ingredients for biryani", "biryani ingredients", "samagri for cake" etc.
    # Anchored to a food noun or cook verb so it doesn't catch puja-samagri /
    # havan-samagri (those are astro/remedy in scope).
    r"\bingredients?\b.*\b(biryani|pulao|paneer|dal|sabzi|roti|paratha|samosa|chai|coffee|cake|cookie|pizza|burger|pasta|maggi|noodles|halwa|kheer|rasgulla|gulab jamun|jalebi|laddu|khaana|khana|food|dish|recipe|cook)",
    r"\b(biryani|pulao|paneer|dal|sabzi|roti|paratha|samosa|cake|cookie|pizza|burger|pasta|maggi|noodles|halwa|kheer|rasgulla|gulab jamun|jalebi|laddu)\s+ingredients?\b",
    # ── Math / arithmetic / calculation ─────────────────────────────────────
    # Sprint-26 Fix-N: tightened to require a math context word AND restricted
    # operator class (no `-` / `x`) — the original pattern false-matched
    # extremely common Hindi duration phrases like "8-10 mahine", "2-3 din",
    # "5x growth", "5x weak". Now we only fire on real arithmetic asks.
    # Operator class: + * / × only (NEVER `-` or `x` — too ambiguous).
    # Anchored with a math verb / equals sign within ±20 chars.
    r"\b\d+\s*[\+\*\/×]\s*\d+\b.*?(=|\bcalculate\b|\bsolve\b|\bbarabar\b|\bjawab\b|\buttar\b|\banswer\b)",
    r"(=|\bcalculate\b|\bsolve\b|\bbarabar\b|\bjawab\b|\buttar\b|\banswer\b).{0,30}\b\d+\s*[\+\*\/×]\s*\d+\b",
    r"\b(calculate|calculator|solve)\b.*\b(equation|sum|problem|math)",
    r"\b(percentage|percent|prozent)\s+(of|nikalo|nikalna|kya hota)",
    r"\b(square root|cube root|factorial|integral|derivative)\b",
    # ── Translation / language tasks ────────────────────────────────────────
    r"\b(translate|translation|anuvad|tarjuma)\b",
    r"\b(in english|in hindi|english me kya|hindi me kya)\s+(bolte|kehte|kahte|kahenge|likhte)",
    # ── Weather / current temperature ───────────────────────────────────────
    r"\b(weather|mausam|temperature|barish|baarish|rain|snow|humidity|forecast aaj)\b",
    # ── News / current affairs ──────────────────────────────────────────────
    r"\b(news|khabar|samachar|breaking news|headlines|latest news)\b",
    # ── General-knowledge / encyclopedia look-ups ───────────────────────────
    r"\b(capital|rajdhani)\s+(of|ki|ka|hai)\b",
    r"\b(distance|duri|दूरी)\s+(between|se|ke beech)\b",
    r"\b(population|jansankhya|abadi)\s+(of|ki|ka)\b",
    r"\b(prime minister|pradhan mantri|president|rashtrapati|chief minister)\s+(of|ka|ki|kaun)",
    r"\b(highest|tallest|largest|biggest|smallest|sabse bada|sabse uncha|sabse chhota)\s+(mountain|river|country|city|building|tree|animal)",
    # ── Entertainment / movies / songs ──────────────────────────────────────
    r"\b(movie|film|netflix|prime video|hotstar|imdb|rotten tomatoes|trailer)\b",
    r"\b(song|gana|lyrics|spotify|youtube music|playlist|album|singer)\b.*\b(suggest|recommend|batao|name)",
    r"\b(joke|chutkula|funny|hasao|hasayie)\b",
    # ── App / device / phone tech support ───────────────────────────────────
    r"\b(iphone|android|samsung|whatsapp|instagram|facebook|gmail|chrome|wifi|bluetooth)\b.*\b(kaise|how to|problem|issue|setup|install|fix)",
    # ── Writing / composition help ──────────────────────────────────────────
    r"\b(write|likh|likho|create|compose)\s+(a|an|me|ek|mere liye)?\s*(poem|essay|story|email|letter|kahani|kavita|patr|nibandh|paragraph|article|blog)",
    # ── Generic search-engine style queries ─────────────────────────────────
    r"\bwikipedia\b",
    r"\bgoogle\s+(search|me|kar|karke|karo)\b",
    # ── Medical diagnosis / prescription (we do astrological remedies only) ─
    # Note: do NOT block bare "treatment for" / "symptoms of" — they're used
    # in genuine astro asks like "treatment for mangal dosh", "symptoms of
    # sade sati". Pair with a clinical noun (medicine/tablet/prescription/
    # disease name) to avoid false positives on astro remedy / dosh queries.
    r"\b(prescription|prescribe|dosage)\b",
    r"\b(medicine|tablet|capsule|injection|antibiotic|painkiller)\s+(name|naam|recommend|suggest|kaun|kaunsi|kya|dosage)",
    r"\b(symptoms?\s+of|treatment\s+for)\s+(diabetes|cancer|fever|covid|cold|flu|tb|asthma|hypertension|bp|migraine|allergy|arthritis|thyroid|pcos)",
    r"\b(dawai ka naam|tablet ka naam|kaun si dawai|kaunsi dava)\b",
]
_BRAND_UNSAFE_RE = [re.compile(p, re.IGNORECASE) for p in _BRAND_UNSAFE_PATTERNS]


def _is_brand_unsafe(question: str) -> bool:
    if not question:
        return False
    return any(rx.search(question) for rx in _BRAND_UNSAFE_RE)


_BRAND_SAFE_REDIRECT = {
    "en": ("Beta, this guide answers only jyotish (astrology) questions — your kundli, dasha, "
           "marriage, career, health, finance, family, vastu, remedies, and life-path matters. "
           "Cooking, coding, weather, news, sports, exam answers, translations and similar topics "
           "are outside this scope. Please ask me an astrology question from your own life and I'll guide you with full heart."),
    "hi": ("बेटा, यह मार्गदर्शिका केवल ज्योतिष से जुड़े प्रश्नों का उत्तर देती है — आपकी कुंडली, दशा, "
           "विवाह, करियर, स्वास्थ्य, धन, परिवार, वास्तु, उपाय और जीवन-पथ के विषय। "
           "खाना बनाना, कोडिंग, मौसम, समाचार, खेल, परीक्षा-उत्तर, अनुवाद आदि इसके दायरे में नहीं आते। "
           "कृपया अपने जीवन से जुड़ा कोई ज्योतिष प्रश्न पूछिए — मैं पूरे मन से मार्गदर्शन करूँगा।"),
    "hn": ("Beta, yeh guide sirf jyotish (astrology) ke prashno ka uttar deti hai — aapki kundli, dasha, "
           "shaadi, career, swasthya, dhan, parivar, vastu, upay aur jeevan-path ke vishay. "
           "Khaana banana, coding, mausam, news, khel, exam-uttar, translation jaisi cheezein iske dayre "
           "mein nahi aati. Kripya apne jeevan se judi koi jyotish se sambandhit prashn poochein — "
           "main poore mann se margdarshan karunga."),
}


# ── Constraint detector ─────────────────────────────────────────────────────
# When a devotee rejects the primary marriage window, we must hand back the
# pre-computed ALT window — never let the AI invent a new year. Triggers:
#   "yeh time nahi chahiye"   "is window mein nahi"   "next year batao"
#   "is date ke baad batao"   "uske baad"            "after this"
#   "dusra time"              "another window"        "agla window"
#   "iske alawa"              "skip this"             "not this"
_MARRIAGE_CONSTRAINT_PATTERNS = [
    re.compile(r"\b(yeh|is|iss)\s+(time|window|date|saal|year|month|month|mahine)\s+(nahi|not|avoid|skip)", re.I),
    re.compile(r"\b(time|window|date|year|saal)\s+(nahi|not)\s+chahi", re.I),
    # Month-name-year + "nahi chahi" e.g. "November 2026 nahi chahiye"
    re.compile(r"\b(?:january|february|march|april|may|june|july|august|"
               r"september|october|november|december)\s+\d{4}\s+(nahi|not)\b", re.I),
    re.compile(r"\b(next|aagla|agla)\s+(year|saal|window|month)\b", re.I),
    re.compile(r"\b(uske|iske|is\s+ke)\s+baad\b", re.I),
    re.compile(r"\bafter\s+(this|that|november|october|december|january|2025|2026|2027)\b", re.I),
    re.compile(r"\b(dusra|doosra|another|alternate|alag|other)\s+(time|window|date|saal|year)\b", re.I),
    re.compile(r"\b(show|give|batao|dikha)\s+(an?\s+)?alternate\s+(window|time|date)\b", re.I),
    re.compile(r"\balternate\s+(time|window|date)\s+(bhi\s+)?(batao|chahiye)\b", re.I),
    re.compile(r"\b(skip|avoid)\s+(this|yeh|is)\b", re.I),
    re.compile(r"\biske\s+alawa\b", re.I),
    re.compile(r"\bnot\s+this\s+(window|time|date|year)\b", re.I),
]

def _detect_marriage_constraint(question: str, history: list) -> bool:
    """Did the devotee just reject the engine's primary window?

    We check the current question text (strongest signal). History is
    inspected lightly only when the current Q is a short follow-up like
    "uske baad?" — those need context to confirm intent.
    """
    q = (question or "").strip()
    if not q:
        return False
    for rx in _MARRIAGE_CONSTRAINT_PATTERNS:
        if rx.search(q):
            return True
    return False


# ── GENERIC FOLLOWUP DETECTION ────────────────────────────────────────────────
# Short, topic-less prompts like "aur detail mein batao" / "iska upay batao" /
# "aur batao" / "explain more" don't contain marriage keywords, so the topic
# classifier returns "general" and we lose the marriage flow. When such a
# generic followup is detected AND the previous assistant turn was about
# marriage, we sticky-inherit the topic so the deterministic engine + template
# fire again.
_GENERIC_FOLLOWUP_PATTERNS = [
    re.compile(p, re.I) for p in (
        # "more detail" asks
        r"\baur\s+(?:thoda\s+)?detail\b",
        r"\bdetail\s+m[ae]i?n?\s+batao\b",
        r"\bdetail\s+(?:se\s+)?batao\b",
        r"\bzyada\s+detail\b",
        r"\bin\s+detail\b",
        r"\bmore\s+detail",
        r"\bexplain\s+more\b",
        r"\belaborate\b",
        r"\btell\s+me\s+more\b",
        # "tell me more / again"
        r"\baur\s+batao\b",
        r"\baur\s+bataiye\b",
        r"\bphir\s+se\s+batao\b",
        r"\bdobara\s+batao\b",
        # remedy followups
        r"\biska\s+upay\b",
        r"\bupay\s+batao\b",
        r"\bremedy\s+batao\b",
        r"\bkoi\s+upay\b",
        # "what about..." / "and...?"
        r"^\s*aur\s*\??\s*$",
        r"^\s*phir\s*\??\s*$",
        r"^\s*kyun\s*\??\s*$",
        r"^\s*kaise\s*\??\s*$",
    )
]
_DEV_FOLLOWUP_PATTERNS = [
    re.compile(p) for p in (
        r"और\s*विस्तार",          # aur vistar
        r"विस्तार\s*से\s*बताओ",   # vistar se batao
        r"और\s*बताओ",             # aur batao
        r"उपाय\s*बताओ",           # upay batao
        r"फिर\s*से\s*बताओ",       # phir se batao
    )
]


def _is_generic_followup(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    # Very short prompts (≤6 tokens) are usually followups; check patterns.
    for rx in _GENERIC_FOLLOWUP_PATTERNS:
        if rx.search(q):
            return True
    for rx in _DEV_FOLLOWUP_PATTERNS:
        if rx.search(q):
            return True
    return False


# ── MARRIAGE SUBTYPE CLASSIFIER ──────────────────────────────────────────────
# Within the marriage topic, distinguish what KIND of question the user asked:
#   "timing"   → "kab hogi" / "when" / window / date / age / year — REQUIRES
#                deterministic engine output (locked window verbatim).
#   "remedy"   → "upay batao" / "remedy" — narrator path is fine (engine
#                provides remedy + window context).
#   "analysis" → "kyun delay" / "kaun sa grah" / "7th lord kahan" / "aur
#                detail" / "explain my chart" — AI is the expert; let it read
#                the kundli freely and answer analytically. NO rigid template.
_MARRIAGE_REMEDY_RE = re.compile(
    r"\b(upay|upaay|remedy|totka|jaap|mantra|daan|vrat|puja|paath)\b"
    r"|उपाय|मंत्र|दान|व्रत|पूजा",
    re.I,
)
_MARRIAGE_TIMING_RE = re.compile(
    r"\b(kab|kabhi|when|date|window|samay|saal|year|years|month|months|"
    r"mahina|mahine|umar|umr|age|timing)\b"
    r"|कब|समय|साल|वर्ष|महीन|उम्र",
    re.I,
)
_MARRIAGE_ANALYSIS_RE = re.compile(
    r"\b(detail|details|kyun|kyon|why|kaun(?:\s*sa)?|which|kis|kaisa|kaisi|"
    r"kaise|how|explain|elaborate|samjha(?:o|iye|do)?|batao\s+(?:kyun|kaise)|"
    r"saptam(?:esh)?|7th\s*(?:lord|house|bhav)|kalatra|venus|shukra|jupiter|"
    r"guru|mars|mangal|saturn|shani|grah|graha|planet|chart|kundli|kundali|"
    r"house|bhav|lord|swami|nakshatra|rashi|dasha|antardasha|spouse|life\s*partner|"
    r"shaadi\s*kaisi|jeevan\s*saathi|patni|pati|biwi)\b"
    r"|क्यों|कौन|कैसे|समझाओ|समझाइए|ग्रह|घर|भाव|स्वामी|सप्तम|शुक्र|गुरु|मंगल|शनि|दशा|पत्नी|पति",
    re.I,
)


# ── SIMPLE CHART-FACT DETECTOR ───────────────────────────────────────────────
# When the user asks a pure lookup ("mera rashi kya hai", "lagna batao",
# "current dasha", "nakshatra"), the prompt's many sections (focus, KP,
# transit, intel, behavior) overpower any "be brief" instruction and force
# 4-paragraph replies. The detector lets us strip ALL of that noise and use
# a minimal prompt for these specific cases, so the AI naturally answers in
# 2-3 sentences. Same model call, same flow — just less noise.
_CHART_FACT_PATTERNS = [
    re.compile(p, re.I) for p in (
        r"\bmer[ai]\s+(?:rashi|raashi|rasi|moon\s*sign|sun\s*sign|chandra\s*rashi|surya\s*rashi)\b",
        r"\b(rashi|raashi|moon\s*sign|sun\s*sign)\s+(?:kya|kaun(?:\s*si)?|batao|bataiye|hai|he|kahiye|tell|what)\b",
        r"\bwhat(?:'s|\s+is)\s+my\s+(?:rashi|moon\s*sign|sun\s*sign|zodiac|sign)\b",
        r"\bmer[ai]\s+(?:lagn[ae]?|ascendant|rising\s*sign)\b",
        r"\b(lagn[ae]?|ascendant|rising\s*sign)\s+(?:kya|kaun(?:\s*si)?|batao|bataiye|hai|he|tell|what)\b",
        r"\bwhat(?:'s|\s+is)\s+my\s+(?:lagna|ascendant|rising\s*sign)\b",
        r"\bmer[ai]\s+(?:nakshatra|nakshatr|janm\s*nakshatra|birth\s*star)\b",
        r"\b(nakshatra|nakshatr|birth\s*star)\s+(?:kya|kaun(?:\s*sa)?|batao|bataiye|hai|he|tell|what)\b",
        r"\bwhat(?:'s|\s+is)\s+my\s+(?:nakshatra|birth\s*star)\b",
        r"\bmer[ai]\s+(?:dasha|mahadasha|antardasha|current\s+dasha)\b",
        r"\b(?:current|abhi|abhi\s+kaunsi)\s+(?:dasha|mahadasha)\b",
        r"\b(?:dasha|mahadasha)\s+(?:kya|kaun(?:\s*si)?|chal\s+rahi|hai|he|batao)\b",
        r"\bmer[ai]\s+(?:gana|gan|yoni|tatv[ae]|tatva|nadi|varna)\b",
        # ── DOSHA YES/NO questions ─────────────────────────────────────────
        # "kya me manglik hun", "manglik hai", "mangal dosh hai", "kaal sarp",
        # "pitru dosh", "guru chandal", "grahan dosh" etc.
        r"\b(?:kya|kya\s+me|kya\s+main)\s+manglik\b",
        r"\bme\s+manglik\s+hu(?:n|m)?\b",
        r"\bmain\s+manglik\s+hu(?:n|m)?\b",
        r"\b(?:mujhe|mer[ai])\s+(?:manglik|mangal\s*dosh)\b",
        r"\b(?:manglik|mangal\s*dosh)\s+(?:hai|he|hu(?:n|m)?|hain)\b",
        r"\b(?:kaal\s*sarp|kalsarp|kaalsarp)\s+(?:dosh|hai|he)\b",
        r"\b(?:mujhe|mer[ai])\s+(?:kaal\s*sarp|kalsarp|kaalsarp)\b",
        r"\b(?:pitr[ua]|pitra)\s+dosh\s+(?:hai|he)\b",
        r"\b(?:mujhe|mer[ai])\s+(?:pitr[ua]|pitra)\s+dosh\b",
        r"\b(?:guru\s*chandal|grahan|daridra|angarak|shrapit|kemadruma)\s+(?:dosh|yog)?\s*(?:hai|he)?\b",
        r"\b(?:mujhe|mer[ai])\s+(?:guru\s*chandal|grahan|daridra|angarak|shrapit|kemadruma)\b",
        r"\bdosh\s+(?:hai|he|kaun\s*sa)\b",
        # ── TRANSPARENCY / "how do you know" follow-ups ───────────────────
        # User asks how AI derived a chart fact: "tumko kaise pata", "kaise
        # jaana", "kahan se aaya", "kaise samjha", "how do you know", etc.
        # These are short clarifying follow-ups — answer in 1-2 sentences
        # explaining the source (birth date/time/place + planet calc).
        r"\b(?:tumko|tujhe|aapko|tumhe)\s+kaise\s+pata\b",
        r"\bkaise\s+(?:pata|jaana|jaane|jaante|samjha|samjhe|samjhi|maloom)\b",
        r"\bkahan\s+se\s+(?:aaya|pata|jaana|jaane)\b",
        r"\bhow\s+do\s+you\s+know\b",
        r"\bhow\s+did\s+you\s+(?:know|find|figure)\b",
        r"\bproof\s+kya\s+hai\b",
        r"\bsource\s+(?:kya|kaha)\b",
    )
]
_CHART_FACT_DEV_PATTERNS = [
    re.compile(p) for p in (
        r"मेरी\s*राशि", r"राशि\s*क्या",
        r"मेरा\s*लग्न", r"लग्न\s*क्या",
        r"मेरा\s*नक्षत्र", r"नक्षत्र\s*क्या",
        r"मेरी\s*दशा", r"कौन\s*सी\s*दशा",
        r"मांगलिक", r"मंगल\s*दोष", r"काल\s*सर्प", r"पितृ\s*दोष",
    )
]


def _is_chart_fact_question(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    # Allow up to 14 words — meta follow-ups like "tumko kaise pata mera
    # mars 1st house me he" run 10-12 words and are still simple lookups.
    if len(q.split()) > 14:
        return False
    for rx in _CHART_FACT_PATTERNS:
        if rx.search(q):
            return True
    for rx in _CHART_FACT_DEV_PATTERNS:
        if rx.search(q):
            return True
    return False


def _classify_marriage_subtype(question: str,
                               pre_classified_bucket: str | None = None) -> str:
    """Return 'timing' / 'remedy' / 'analysis' / 'general'.

    Sprint-25 Fix-F: When `pre_classified_bucket` is supplied (AI Ear handoff)
    AND it is in `_MARRIAGE_BUCKET_TO_SUBTYPE`, that mapping is trusted and
    the regex below is skipped. Falls back to regex on any miss / mismatch.
    """
    if pre_classified_bucket:
        mapped = _MARRIAGE_BUCKET_TO_SUBTYPE.get(pre_classified_bucket.strip().lower())
        if mapped:
            return mapped
    q = (question or "").strip()
    if not q:
        return "general"
    # Remedy first (most specific intent)
    if _MARRIAGE_REMEDY_RE.search(q):
        return "remedy"
    # Analysis next — covers "why/which/explain/detail/planet name" etc.
    if _MARRIAGE_ANALYSIS_RE.search(q):
        return "analysis"
    # Timing words (kab/when/year)
    if _MARRIAGE_TIMING_RE.search(q):
        return "timing"
    return "general"


# ─────────────────────────────────────────────────────────────────────────────
# QUESTION-INTENT CLASSIFIER (Sprint-23)
# ─────────────────────────────────────────────────────────────────────────────
# Single source of truth for "what TYPE of question did the user ask?"
# Returns a structured intent dict consumed by:
#   - ai_ask trace (logged as 2c.QUESTION_INTENT)
#   - ai_ask response payload (returned as `question_intent`)
#   - brevity post-trim guard (replaces the older _is_short_planet_strength_q
#     standalone regex — that flag is now derived from this classifier)
#
# Intent vocabulary (15 canonical categories — keep this list in sync with
# downstream UI consumers and any analytics dashboards keyed on `intent`):
#   planet_strength    : "Mars powerful ya weak", "Shani strong hai?"
#   planet_position    : "Mars kahan hai?", "Sun kis sign mein hai?"
#   planet_in_house    : "Saturn kis house mein hai?"
#   planet_combo       : "Mars-Saturn combo", "Sun aur Moon ka relation"
#                        (also: ambiguous multi-planet strength asks)
#   lagna_lookup       : "Mera lagna kya hai?"
#   moon_sign_lookup   : "Mera chandra rashi / moon sign / janma rashi?"
#   sun_sign_lookup    : "Surya rashi / Sun sign kya hai?"
#   nakshatra_lookup   : "Mera nakshatra kya hai?"
#   house_lookup       : "5th house mein kya hai?"
#   dasha_current      : "Abhi kaunsa dasha chal raha hai?"
#   dasha_when         : "Saturn dasha kab aayegi?"
#   yoga_check         : "Raj yoga hai kya?", "Gaja-Kesari yoga hai?"
#   timing_when        : "Shaadi kab hogi?", "Job kab milegi?" (no chart-fact)
#   comparison         : "Saturn vs Jupiter", "Mars zyada strong ya Saturn?"
#   analysis_general   : "Meri kundli kaisi hai?" / fallback
# ─────────────────────────────────────────────────────────────────────────────

_PLANET_TOKENS = {
    "sun":     ["sun", "surya", "suraj", "ravi", "soma"],
    "moon":    ["moon", "chandra", "chand", "chandrama", "chandr"],
    "mars":    ["mars", "mangal", "mangala", "mangla", "kuja"],
    "mercury": ["mercury", "budh", "budha"],
    "jupiter": ["jupiter", "guru", "brihaspati", "brahaspati", "vrihaspati", "brihspati"],
    "venus":   ["venus", "shukra", "shukr"],
    "saturn":  ["saturn", "shani", "sani", "shanidev", "shaneswar"],
    "rahu":    ["rahu"],
    "ketu":    ["ketu"],
}
_HOUSE_RE = re.compile(
    r"\b(\d+)(?:st|nd|rd|th)?\s*(?:house|ghar|bhav|bhava)\b"
    r"|\b(?:lagna|first|pehla|pehle)\s*(?:house|ghar|bhav|bhava)\b"
    r"|\b(saptam|panchm|dasham|chaturth|navam|tritiy|ashtam|labh|dhanu?)\s*(?:bhav|ghar)\b",
    re.I,
)
_STRENGTH_RE = re.compile(
    r"\b("
    r"strong|strength|weak|weakness|powerful|power|"
    r"debilitat(?:ed|ion)?|exalt(?:ed|ation)?|"
    r"takat(?:vaar|war|var)?|takatvar|kamzor|kamjor|majboot|mazboot|dum|bal|"
    r"shaktishali|shakti|"
    r"neech|neecha|uchch|ucch|uchcha|"
    r"good|bad|achha|achchha|accha|kharab|kharaab|"
    r"favourable|favorable|"
    r"kaisa|kaisi|kaise"
    r")\b",
    re.I,
)
_POSITION_RE = re.compile(
    r"\b(kahan|kahaan|kaha|kis\s*(?:sign|rashi|house|ghar|bhav)|"
    r"which\s*(?:sign|house|rashi|placement)|placement|placed|sthit|baitha)\b",
    re.I,
)
_HOUSE_LOOKUP_RE = re.compile(
    r"\b(?:kya|what|kaunse?|which|konsa)\b.{0,20}\b(?:planet|graha|house|ghar|bhav)\b",
    re.I,
)
_LAGNA_RE     = re.compile(r"\b(lagna|ascendant|ascending|udaya|first\s*house\s*sign)\b", re.I)
# Sun-sign explicit (must contain Sun-token + rashi/sign keyword) — checked BEFORE moon
_SUN_SIGN_RE  = re.compile(r"\b(surya\s*rashi|sun\s*sign|ravi\s*rashi|suraj\s*rashi)\b", re.I)
# Moon-sign explicit. Bare "rashi/raashi" defaults to moon-sign (Vedic convention:
# "rashi" alone = janma-rashi = Moon sign) but ONLY checked AFTER sun-sign so
# "surya rashi" doesn't get hijacked.
_MOON_SIGN_RE = re.compile(r"\b(chandra\s*rashi|moon\s*sign|janma\s*rashi|janam\s*rashi|rashi|raashi)\b", re.I)
_NAKSHATRA_RE = re.compile(r"\b(nakshatra|nakshatr|janma\s*nakshatra|birth\s*star)\b", re.I)
_DASHA_RE     = re.compile(r"\b(dasha|dasa|antardasha|antar\s*dasha|mahadasha|maha\s*dasha|pratyantar)\b", re.I)
_DASHA_NOW_RE = re.compile(r"\b(abhi|currently|current|now|chal\s*rah[ai]|running|active)\b", re.I)
_DASHA_WHEN_RE= re.compile(r"\b(kab|when|kaunse?\s*(?:saal|year)|kis\s*saal)\b", re.I)
_YOGA_RE      = re.compile(
    r"\b(yoga|yog|raja\s*yoga|gaja[\s-]*kesari|kesari|"
    r"neecha[\s-]*bhanga|panch\s*mahapurush|hamsa|malavya|ruchaka|sasha|bhadra|"
    r"vipreet|vipreeta|kemadruma|kalathra|vish|shakata|chandala|guru[\s-]*chandala)\b",
    re.I,
)
_TIMING_WHEN_RE = re.compile(r"\b(kab|when|timing|saal|year|month|mahina)\b", re.I)
_COMPARISON_RE  = re.compile(
    r"\b(vs\.?|versus|ya\s+(?!weak\b)(?!kamzor\b)|or\s+(?!weak\b)|zyada|"
    r"jyada|kaunsa|konsa|which\s+(?:is\s+)?(?:more|stronger|better))\b",
    re.I,
)
_COMBO_RE       = re.compile(r"\b(combo|combination|sambandh|relation|conjunction|yuti|together|saath|aspect|drishti)\b", re.I)


def _detect_planets(q: str) -> list[str]:
    """Return canonical planet names (Sun/Moon/...) found in question."""
    ql = " " + (q or "").lower() + " "
    found = []
    for canonical, aliases in _PLANET_TOKENS.items():
        for a in aliases:
            if re.search(r"\b" + re.escape(a) + r"\b", ql):
                found.append(canonical.capitalize())
                break
    return found


def _detect_houses(q: str) -> list[str]:
    """Return house tokens (e.g. '5', '7', 'lagna') found in question."""
    out: list[str] = []
    for m in _HOUSE_RE.finditer(q or ""):
        num = m.group(1)
        if num:
            out.append(num)
        else:
            out.append("lagna" if "lagna" in m.group(0).lower() or "first" in m.group(0).lower() or "pehl" in m.group(0).lower() else "named")
    return out


def _classify_ask_intent(question: str, lang: str = "hn") -> dict:
    """
    Returns {intent, subjects, scope, confidence, reasons, word_count}.

    `intent`     : one of the vocabulary tags above
    `subjects`   : list — planet names + house numbers detected
    `scope`      : 'single_planet' | 'multi_planet' | 'house' | 'lagna' |
                   'moon_sign' | 'sun_sign' | 'nakshatra' | 'dasha' |
                   'yoga' | 'timing' | 'general'
    `confidence` : 0.0–1.0 (heuristic — high when keywords match cleanly)
    `reasons`    : list[str] — human-readable why this intent was chosen
    `word_count` : len(question.split())
    """
    q = (question or "").strip()
    if not q:
        return {
            "intent": "analysis_general", "subjects": [], "scope": "general",
            "confidence": 0.0, "reasons": ["empty question"], "word_count": 0,
        }

    wc = len(q.split())
    planets = _detect_planets(q)
    houses  = _detect_houses(q)
    reasons: list[str] = []

    has_strength    = bool(_STRENGTH_RE.search(q))
    has_position    = bool(_POSITION_RE.search(q))
    has_house_tok   = bool(houses)
    has_lagna       = bool(_LAGNA_RE.search(q))
    has_moon_sign   = bool(_MOON_SIGN_RE.search(q))
    has_sun_sign    = bool(_SUN_SIGN_RE.search(q))
    has_nakshatra   = bool(_NAKSHATRA_RE.search(q))
    has_dasha       = bool(_DASHA_RE.search(q))
    has_dasha_when  = bool(_DASHA_WHEN_RE.search(q))
    has_dasha_now   = bool(_DASHA_NOW_RE.search(q))
    has_yoga        = bool(_YOGA_RE.search(q))
    has_timing_when = bool(_TIMING_WHEN_RE.search(q))
    has_comparison  = bool(_COMPARISON_RE.search(q))
    has_combo       = bool(_COMBO_RE.search(q))

    # Most specific → least specific routing.
    # 1. Lagna lookup (no other strong signal, just "lagna kya hai")
    if has_lagna and not has_strength and not has_position and not has_house_tok:
        reasons.append("lagna keyword without strength/position")
        return {"intent": "lagna_lookup", "subjects": ["Lagna"], "scope": "lagna",
                "confidence": 0.95, "reasons": reasons, "word_count": wc}

    # 2. Sun-sign / Moon-sign / Nakshatra explicit lookups.
    # Sun-sign MUST be checked before moon-sign because _MOON_SIGN_RE
    # accepts bare "rashi/raashi" (Vedic convention: rashi alone = janma-rashi
    # = Moon sign), which would otherwise hijack "surya rashi kya hai".
    if has_nakshatra and not planets:
        reasons.append("nakshatra keyword")
        return {"intent": "nakshatra_lookup", "subjects": ["Nakshatra"], "scope": "nakshatra",
                "confidence": 0.95, "reasons": reasons, "word_count": wc}
    if has_sun_sign and not has_strength:
        reasons.append("sun-sign keyword (explicit Sun token + sign keyword)")
        return {"intent": "sun_sign_lookup", "subjects": ["Sun"], "scope": "sun_sign",
                "confidence": 0.92, "reasons": reasons, "word_count": wc}
    if has_moon_sign and not has_strength:
        reasons.append("moon-sign keyword (rashi/raashi defaults to janma-rashi=Moon)")
        return {"intent": "moon_sign_lookup", "subjects": ["Moon"], "scope": "moon_sign",
                "confidence": 0.92, "reasons": reasons, "word_count": wc}

    # 3. Dasha questions
    if has_dasha:
        if has_dasha_when and not has_dasha_now:
            reasons.append("dasha + when")
            return {"intent": "dasha_when", "subjects": planets or ["Dasha"], "scope": "dasha",
                    "confidence": 0.90, "reasons": reasons, "word_count": wc}
        reasons.append("dasha keyword (current/lookup)")
        return {"intent": "dasha_current", "subjects": planets or ["Dasha"], "scope": "dasha",
                "confidence": 0.92, "reasons": reasons, "word_count": wc}

    # 4. Yoga check
    if has_yoga:
        reasons.append("yoga keyword")
        return {"intent": "yoga_check", "subjects": planets or ["Yoga"], "scope": "yoga",
                "confidence": 0.90, "reasons": reasons, "word_count": wc}

    # 5. Comparison ("Saturn vs Jupiter", "Mars zyada strong ya Saturn")
    if has_comparison and len(planets) >= 2:
        reasons.append(f"comparison keyword + {len(planets)} planets")
        return {"intent": "comparison", "subjects": planets, "scope": "multi_planet",
                "confidence": 0.93, "reasons": reasons, "word_count": wc}

    # 6. Combo / conjunction / aspect between 2+ planets
    if has_combo and len(planets) >= 2:
        reasons.append(f"combo/aspect keyword + {len(planets)} planets")
        return {"intent": "planet_combo", "subjects": planets, "scope": "multi_planet",
                "confidence": 0.90, "reasons": reasons, "word_count": wc}

    # 7. Single-planet strength (most common) — short Q with EXACTLY ONE
    # planet + strength word. Multi-planet strength asks ("Mars Jupiter strong
    # hai kya") fall through to step 5 (comparison) or step 6 (combo) above
    # if they have those signals; otherwise step 12 / fallback.
    if len(planets) == 1 and has_strength and wc <= 14:
        reasons.append(f"single planet ({planets[0]}) + strength keyword + short ({wc}w)")
        return {"intent": "planet_strength", "subjects": planets, "scope": "single_planet",
                "confidence": 0.95, "reasons": reasons, "word_count": wc}
    # 7b. Multi-planet strength without comparison/combo cue → analytical
    # (e.g. "Mars Jupiter strong hai" ambiguous). Tag as planet_combo so it
    # gets multi-subject treatment, lower confidence.
    if len(planets) >= 2 and has_strength:
        reasons.append(f"multi planets ({planets}) + strength but no comparison/combo cue")
        return {"intent": "planet_combo", "subjects": planets, "scope": "multi_planet",
                "confidence": 0.70, "reasons": reasons, "word_count": wc}

    # 8. Planet-in-house ("Saturn kis house mein hai" / "Mars 5th mein kya")
    if planets and (has_house_tok or has_position) and not has_strength:
        reasons.append(f"planet ({planets[0]}) + position/house keyword")
        scope = "single_planet" if len(planets) == 1 else "multi_planet"
        return {"intent": "planet_in_house" if has_house_tok else "planet_position",
                "subjects": planets + houses, "scope": scope,
                "confidence": 0.90, "reasons": reasons, "word_count": wc}

    # 9. Position only ("Mars kahan hai")
    if planets and has_position:
        reasons.append(f"planet ({planets[0]}) + position keyword")
        return {"intent": "planet_position", "subjects": planets[:1], "scope": "single_planet",
                "confidence": 0.88, "reasons": reasons, "word_count": wc}

    # 10. House lookup ("5th house mein kya hai")
    if has_house_tok and not planets:
        reasons.append(f"house token ({houses[0]}) without planet")
        return {"intent": "house_lookup", "subjects": houses, "scope": "house",
                "confidence": 0.88, "reasons": reasons, "word_count": wc}
    if _HOUSE_LOOKUP_RE.search(q) and not planets:
        reasons.append("'kya/what + house/planet' pattern")
        return {"intent": "house_lookup", "subjects": houses or ["house"], "scope": "house",
                "confidence": 0.80, "reasons": reasons, "word_count": wc}

    # 11. Generic timing ("kab hoga") — no chart-only-fact, will route to engine timing
    if has_timing_when and not planets and not has_dasha:
        reasons.append("generic 'kab/when' without planet/dasha")
        return {"intent": "timing_when", "subjects": [], "scope": "timing",
                "confidence": 0.75, "reasons": reasons, "word_count": wc}

    # 12. Single planet only, no strength keyword → analytical question about planet
    if planets and len(planets) == 1:
        reasons.append(f"single planet ({planets[0]}) mention, no strength/position keyword")
        return {"intent": "planet_position", "subjects": planets, "scope": "single_planet",
                "confidence": 0.65, "reasons": reasons, "word_count": wc}

    # 13. Fallback
    reasons.append("no specific signal — defaulting to general analysis")
    return {"intent": "analysis_general", "subjects": planets + houses, "scope": "general",
            "confidence": 0.50, "reasons": reasons, "word_count": wc}


def _intent_is_short_strength(intent_dict: dict) -> bool:
    """
    Replaces the old standalone _is_short_planet_strength_q regex.
    Used by the brevity post-trim guard to decide whether to enforce
    strict 3-sentence cap + drop off-topic sentences.
    """
    if not isinstance(intent_dict, dict):
        return False
    return (
        intent_dict.get("intent") == "planet_strength"
        and intent_dict.get("scope") == "single_planet"
        and (intent_dict.get("word_count") or 0) <= 14
    )


def _last_assistant_topic_was_marriage(history: list) -> bool:
    for h in reversed(history or []):
        if (h or {}).get("role") == "assistant":
            prev = ((h.get("content") or h.get("text") or "")).lower()
            if any(k in prev for k in (
                "vivah", "shaadi", "shadi", "marriage",
                "विवाह", "शादी", "spouse", "wife", "husband",
                "kalatra", "saptam",
            )):
                return True
            # Only inspect the most recent assistant turn.
            return False
    return False


_TONE_SCRUB_PATTERNS = [
    # (regex, replacement)  — case-insensitive, applied once per response.
    (re.compile(r"\bI sense your concern[.,]?\s*", re.I), ""),
    (re.compile(r"\bI understand[.,]?\s*",          re.I), ""),
    (re.compile(r"\bI can see that\b",              re.I), "Aapki kundli mein"),
    (re.compile(r"\bsignificant topic\b",           re.I), "important question"),
    (re.compile(r"\bbased on your chart[.,]?\s*",   re.I), ""),
    (re.compile(r"\baccording to the data[.,]?\s*", re.I), ""),
    (re.compile(r"\blet me analyze\b[.,]?\s*",      re.I), ""),
    (re.compile(r"^\s*Pranam[.,]?\s*",              re.I), "Beta, "),
    (re.compile(r"\bAs an AI\b[^.]*\.",             re.I), ""),
    (re.compile(r"\bAs a language model\b[^.]*\.",  re.I), ""),

    # ── HEDGE / UNCERTAINTY → CERTAINTY (Hinglish + Hindi) ─────────────────
    # Generalised verb-stem swap: ANY "<stem> sakta hai / sakti hai / sakte
    # hain / sakega / sakegi" → certain future. Stem is preserved.
    # Examples caught: ho/pa/mil/nikal/de/le/ja/aa/dikh/ban/badh/ghat/kar
    # sakta hai → kar gives "karega", etc.
    (re.compile(r"\b(\w+)\s+sakte\s+hain\b",        re.I), r"\1enge"),
    (re.compile(r"\b(\w+)\s+sakti\s+hain\b",        re.I), r"\1engi"),
    (re.compile(r"\b(\w+)\s+sakta\s+hai\b",         re.I), r"\1ega"),
    (re.compile(r"\b(\w+)\s+sakti\s+hai\b",         re.I), r"\1egi"),
    (re.compile(r"\b(\w+)\s+sakega\b",              re.I), r"\1ega"),
    (re.compile(r"\b(\w+)\s+sakegi\b",              re.I), r"\1egi"),
    (re.compile(r"\bsambhavnaye?in?\b",             re.I), "yog"),
    (re.compile(r"\bsambhavna\b",                   re.I), "yog"),
    (re.compile(r"\bshayad\s+",                     re.I), ""),
    (re.compile(r"\blagta\s+hai\b",                 re.I), "hai"),
    # Devanagari hedges
    (re.compile(r"हो सकता है"),                       "होगा"),
    (re.compile(r"हो सकती है"),                       "होगी"),
    (re.compile(r"हो सकते हैं"),                      "होंगे"),
    (re.compile(r"शायद\s*",                          re.U), ""),
    (re.compile(r"संभावना"),                          "योग"),
    # English hedges
    (re.compile(r"\baround\s+(?=\w)",               re.I), ""),
    (re.compile(r"\bapproximately\s+",              re.I), ""),
    (re.compile(r"\bapprox\.?\s+",                  re.I), ""),
    (re.compile(r"\broughly\s+",                    re.I), ""),
    (re.compile(r"\bperhaps\s+",                    re.I), ""),
    (re.compile(r"\bpossibly\s+",                   re.I), ""),
    (re.compile(r"\bquite\s+possibly\s+",           re.I), ""),
    (re.compile(r"\bmight\s+be\b",                  re.I), "is"),
    (re.compile(r"\bmay\s+be\b",                    re.I), "is"),
    (re.compile(r"\bis\s+likely\s+to\b",            re.I), "will"),
    (re.compile(r"\bwill\s+likely\b",               re.I), "will"),
    (re.compile(r"\blikely\s+",                     re.I), ""),
    (re.compile(r"\bunlikely\s+",                   re.I), "not "),
    (re.compile(r"\bthere\s+is\s+a\s+(strong\s+|good\s+)?chance\s+(that\s+)?", re.I), ""),
    (re.compile(r"\bthere'?s\s+a\s+(strong\s+|good\s+)?chance\s+(that\s+)?",   re.I), ""),
    # Soften timing fuzz: "by the end of 2026" / "early 2026" / "late 2026"
    (re.compile(r"\bby\s+the\s+end\s+of\s+",        re.I), ""),
    (re.compile(r"\bin\s+early\s+(?=\d{4})",        re.I), "in "),
    (re.compile(r"\bin\s+late\s+(?=\d{4})",         re.I), "in "),
    (re.compile(r"\bearly\s+(?=\d{4})",             re.I), ""),
    (re.compile(r"\blate\s+(?=\d{4})",              re.I), ""),
]


_NARRATIVE_DISCLAIMER_SENT_RX = re.compile(
    # Match ONLY the narrow suffix-boilerplate disclaimer sentences the
    # legacy V→R→T template appended verbatim. We deliberately require
    # the consult/advisor/professional CTA pair to fire — bare mentions
    # of "doctor", "CA", or "advisor" inside legitimate astro narration
    # (e.g. "Saturn ke prabhav se career mein aap doctor ban sakte ho",
    # "advisor banne ka yog hai", "CA ka kaam start kar sakte ho") will
    # NOT match because they don't contain the imperative consult phrase.
    # Note: ALL inner character classes use [^.!?\n] (NOT [\w\s/.\-]) so
    # the regex CANNOT cross sentence boundaries. Earlier draft included
    # `.` in inner classes which let one match span 2-3 sentences and
    # delete legitimate trailing prose.
    r"[^.!?\n]*\b("
    # Boilerplate 1: CA/SEBI/tax advisor + consult/salah CTA in same sentence.
    r"(?:CA|SEBI[-\s]registered|qualified|financial|tax)[^.!?\n]*?"
    r"(?:advisor|consultant|professional)[^.!?\n]{0,80}?"
    r"(?:consult|salah|salaah|raay|baat|guidance)\b[^.!?\n]{0,40}"
    r"(?:karein|lein|karna|zaroori|chahiye|recommended|must)?"
    # Boilerplate 2: medical-disclaimer suffix (doctor + consult CTA).
    r"|(?:qualified|certified|licensed|registered)?\s*"
    r"(?:doctor|physician|medical\s+professional)\b[^.!?\n]{0,80}?"
    r"(?:consult|salah|salaah|baat|milein|milna|advice)\b[^.!?\n]{0,40}"
    r"(?:karein|lein|karna|zaroori|chahiye|recommended|must)?"
    # Boilerplate 3: explicit "consult <a> CA/doctor/SEBI advisor" pattern.
    r"|consult[^.!?\n]{0,40}?"
    r"(?:CA|SEBI[-\s]registered\s+advisor|financial\s+advisor|"
    r"qualified\s+doctor|physician|medical\s+professional)\b"
    # Boilerplate 4: bare "CA" + IMPERATIVE consult/salah CTA (legacy
    # Rule #10 short form). The imperative verb (karein/lein/le lein/
    # chahiye/zaroori) is the discriminator — career mentions like
    # "CA ka practice", "CA ban sakte ho", "CA ka kaam" don't carry it.
    r"|\bCA\b[^.!?\n]{0,30}?"
    r"(?:se\s+)?(?:consult|salah|salaah|guidance|raay)\s+"
    r"(?:karein|lein|le\s+lein|karna\s+(?:chahiye|zaroori))\b"
    # Boilerplate 5: "financial planner" + salah/consult + IMPERATIVE
    # CTA. Imperative verb is MANDATORY (no `?`) to prevent stripping
    # narrative sentences like "financial planner ki salaah se long-term
    # discipline bana paoge" — those are predictions, not disclaimers.
    r"|financial\s+planner[^.!?\n]{0,40}?"
    r"(?:salaah|salah|guidance|advice|consult)\b"
    r"[^.!?\n]{0,30}"
    r"(?:karein|lein|le\s+lein|chahiye|zaroori|zaroor|recommended|must)\b"
    r")[^.!?\n]*[.!?]?",
    re.IGNORECASE,
)


# Crisis / mental-health markers — when ANY of these appear in the text,
# the disclaimer-strip is skipped entirely because the doctor-cite + helpline
# block injected by the health crisis safety net is mandatory and must
# survive intact (architect Round 4 finding).
_CRISIS_MARKER_RX = re.compile(
    r"("
    # Helpline / brand markers (use \b for word boundary safety).
    r"\bhelpline\b"
    r"|\biCall\b"
    r"|\b9152987821\b"
    r"|\bVandrevala\b"
    r"|\b1860[-\s]?2662[-\s]?345\b"
    # Self-harm / suicide variants — `suicid` as STEM (not bounded) so
    # suicide / suicidal / suicidality / suicides all match. Architect
    # Round 5: bare `suicid\b` only matched the rare token "suicid",
    # missing real-world variants.
    r"|\bself[\-\s]?harm\b"
    r"|suicid(?:e|al|ality|es)?\b"
    # Hindi/Hinglish crisis phrases.
    r"|\bkhud[\-\s]?ko[\-\s]?nuksaan\b"
    r"|\bjaan[\-\s]?lena\b"
    r"|\bjeena\s+nahi\s+chahta\b"
    r"|\bmarne\s+ka\s+(?:man|mann|dil)\b"
    # Safety-block sentinels (any of these implies the crisis injector
    # already fired upstream — preserve verbatim).
    r"|\baap\s+akele\s+nahi\s+hain\b"
    r"|\bmental\s+health\s+support\b"
    r"|\bcrisis\s+helpline\b"
    r")",
    re.IGNORECASE,
)


def _strip_narrative_disclaimers(text: str) -> str:
    """Phase 4.5 — narrative-mode safety net.

    Even with the unified narrative contract installed (which forbids any
    'CA / SEBI advisor', 'qualified doctor', 'consult' disclaimer suffix),
    the model occasionally bakes one in — particularly on wealth/health
    turns where the per-topic narrator override historically mandated it.
    This post-strip removes those sentences as a defense-in-depth measure
    so the user's narrative answer stays clean. Idempotent and safe to
    run on already-clean text (regex matches nothing → returns unchanged).

    CRISIS GUARD (architect Round 4): if the text contains any crisis /
    mental-health marker (helpline number, "aap akele nahi hain", Vandrevala,
    iCall, suicid*, self-harm, etc.), the strip is skipped entirely. The
    health crisis safety injector treats the doctor-cite + helpline block
    as non-negotiable, and the strip would otherwise remove the doctor
    line — leaving the user with a partial safety message.
    """
    if not text:
        return text
    if _CRISIS_MARKER_RX.search(text):
        # Crisis path — preserve all disclaimer / safety language verbatim.
        return text
    out = _NARRATIVE_DISCLAIMER_SENT_RX.sub("", text)
    # Collapse the punctuation/whitespace artefacts the strip leaves behind.
    out = re.sub(r"\s*;\s*\.", ".", out)         # "; ." → "."
    out = re.sub(r"\s*,\s*\.", ".", out)         # ", ." → "."
    out = re.sub(r"\s+([,.;:!?])", r"\1", out)   # " ." → "."
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    # Drop now-empty lines / paragraphs.
    out = "\n".join(ln.rstrip() for ln in out.splitlines()
                    if ln.strip() not in ("", ".", ";", ",", "—"))
    return out.strip()


def _scrub_brand_tone(text: str) -> str:
    """Strip AI-style phrases that break the human-Pandit illusion."""
    if not text:
        return text
    out = text
    for rx, repl in _TONE_SCRUB_PATTERNS:
        out = rx.sub(repl, out)
    # Phase 4.5: in narrative mode, also strip any leftover disclaimer
    # sentences the AI may have added against the contract. Cheap regex,
    # runs only when the flag is on.
    if _NARRATIVE_MODE:
        out = _strip_narrative_disclaimers(out)
    # Collapse double spaces / orphan punctuation introduced by removals.
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"\n{3,}",   "\n\n", out)
    out = re.sub(r"^[ \t,;.]+", "",  out)
    return out.strip()


def _has_required_window(text: str, must_window_str: str) -> bool:
    """True iff the AI output literally contains the engine's window string."""
    if not must_window_str:
        return True   # nothing to enforce
    return must_window_str.lower() in (text or "").lower()


_FOLLOW_UPS_BY_TOPIC = {
    "marriage": {
        "hn": ["Iska upay batao", "Alternate time bhi batao", "Mangal dosh hai kya?"],
        "hi": ["इसका उपाय बताइए", "वैकल्पिक समय बताइए", "क्या मंगल दोष है?"],
        "en": ["Suggest a remedy", "Show an alternate window", "Do I have manglik dosha?"],
    },
    "career": {
        "hn": ["Job change ka time?", "Promotion kab hogi?", "Best career field batao"],
        "hi": ["नौकरी बदलने का समय?", "पदोन्नति कब?", "सर्वश्रेष्ठ क्षेत्र बताइए"],
        "en": ["When to switch jobs?", "Next promotion timing?", "Best career field for me"],
    },
    "finance": {
        "hn": ["Dhan-yog kab khulta hai?", "Loan/karz kab utrega?", "Investment ka shubh time?"],
        "hi": ["धन-योग कब खुलेगा?", "कर्ज़ कब उतरेगा?", "निवेश का शुभ समय?"],
        "en": ["When does my wealth-yoga open?", "When will I be debt-free?", "Auspicious time to invest?"],
    },
    "health": {
        "hn": ["Swasthya ka upay batao", "Kis ang mein dosh hai?", "Aushadhi ke liye shubh din?"],
        "hi": ["स्वास्थ्य का उपाय बताइए", "किस अंग में दोष है?", "औषधि का शुभ दिन?"],
        "en": ["Suggest a health remedy", "Which body area is afflicted?", "Auspicious day to start treatment?"],
    },
    "education": {
        "hn": ["Padhai mein safalta kab?", "Foreign study ka yog?", "Vidya ka upay batao"],
        "hi": ["पढ़ाई में सफलता कब?", "विदेश अध्ययन का योग?", "विद्या का उपाय?"],
        "en": ["When will I succeed in studies?", "Foreign study yoga?", "Remedy for studies"],
    },
    "general": {
        "hn": ["Aur detail mein batao", "Iska upay batao", "Aaj ka muhurat?"],
        "hi": ["और विस्तार से बताइए", "इसका उपाय बताइए", "आज का मुहूर्त?"],
        "en": ["Tell me in more detail", "Suggest a remedy", "What's today's muhurat?"],
    },
}

def _derive_follow_ups(topic: str, lang: str) -> list[str]:
    """Return 3 short, deterministic follow-up suggestion chips for the
    given topic + reply language. Falls back to general topic and Hinglish
    if either key is unknown. Pure-Python, zero LLM cost."""
    key = (topic or "general").lower()
    if key not in _FOLLOW_UPS_BY_TOPIC:
        key = "general"
    by_lang = _FOLLOW_UPS_BY_TOPIC[key]
    eff = lang if lang in by_lang else "hn"
    return list(by_lang.get(eff) or by_lang["hn"])[:3]


# ─────────────────────────────────────────────────────────────────────────────
# SUPERTYPE LAYER  (Sprint-24)
# Maps the 15 fine-grained question_intent tags from _classify_ask_intent()
# into 5 narrator-facing supertypes that drive the strict response-rule
# contract injected as the LAST system message in every astro turn.
#
# Vocabulary (per user spec):
#   PLANET_QUERY      → chart inspection ("mera Mars kaisa hai")
#                       → ONLY explain strength, D1+D9 only,
#                         NO dasha, NO future, NO advice.
#   PROBLEM_QUERY     → "why is X happening" ("paisa nahi ruk raha")
#                       → MUST include dasha + house activation.
#   TIMING_QUERY      → "kab improve hoga" → mention dasha transition.
#   DECISION_QUERY    → "X karu ya nahi" → clear YES/NO/WAIT + 1-2 reasons.
#   GENERAL_ANALYSIS  → balanced overview, short.
#
# Detection order is most-specific → least-specific. Decision and Problem
# patterns are LANGUAGE-AGNOSTIC (English + Hinglish + Devanagari).

_DECISION_RX = re.compile(
    # "X karu ya nahi" / "X karna chahiye" / "should I X" / "decide kya" /
    # "X karu kya" / "X le lu kya" — Hinglish prefers the trailing "kya"
    # form for short decision asks.
    r"\b(?:karu(?:\s*ya\s*na|\s*ya\s*nahi|\s*kya|n)?|karna\s*chahiye|"
    r"karni\s*chahiye|karein\s*ya|karen\s*ya|"
    r"chahiye\s*ya\s*nahi|chahiye\s*ya\s*na|"
    r"lena\s*chahiye|leni\s*chahiye|dena\s*chahiye|deni\s*chahiye|"
    r"le\s*lu(?:n)?\s*kya|le\s*lo\s*kya|"
    r"lagaun(?:\s*ya|\s*kya)?|lagayein|"
    r"jaun\s*(?:ya|kya)|jana\s*chahiye|"
    r"chodun(?:\s*ya|\s*kya)?|chod\s*du(?:\s*kya)?|chhodu|chhodun|"
    r"badlun(?:\s*kya)?|badlaun|switch\s*karu(?:\s*kya)?|"
    r"buy\s*or\s*not|sell\s*or\s*not|"
    r"buy\s*karu\s*kya|sell\s*karu\s*kya|"
    r"should\s+(?:i|we|he|she|they)\b|"
    r"shall\s+i\b|"
    r"yes\s*ya\s*no|haan\s*ya\s*na|haan\s*ya\s*naa|"
    r"karna\s*sahi|karna\s*theek|"
    r"decide\s*kya|decision\s*kya|"
    r"acha\s*hai\s*ya\s*nahi|achha\s*hai\s*ya\s*nahi|"
    r"sahi\s*hai\s*ya\s*nahi|theek\s*hai\s*ya\s*nahi)\b"
    r"|करूं|करूँ\s*क्या|करना\s*चाहिए|चाहिए\s*या\s*नहीं|या\s*नहीं|"
    r"छोड़ूं|छोड़ूँ\s*क्या|बदलूं|बदलूँ\s*क्या|ले\s*लूँ\s*क्या",
    re.IGNORECASE,
)

_PROBLEM_RX = re.compile(
    # "X nahi ho raha" / "X nahi mil raha" / "X nahi ruk raha" / "problem"
    r"\b(?:problem|dikkat|dikkkat|issue|trouble|samasya|samasyaa|"
    r"pareshani|pareshaani|pareshan|tension|stress|"
    r"nahi\s+ho\s*raha|nahi\s+ho\s*rahi|nahi\s+ho\s*rahe|"
    r"nahi\s+mil\s*raha|nahi\s+mil\s*rahi|nahi\s+mil\s*rahe|"
    r"nahi\s+ruk\s*raha|nahi\s+ruk\s*rahi|nahi\s+ruk\s*rahe|"
    r"nahi\s+chal\s*raha|nahi\s+chal\s*rahi|"
    r"nahi\s+lag\s*raha|nahi\s+lag\s*rahi|"
    r"nahi\s+ban\s*raha|nahi\s+ban\s*rahi|"
    r"nahi\s+aa\s*raha|nahi\s+aa\s*rahi|"
    r"nahi\s+hota|nahi\s+hoti|nahi\s+hote|"
    r"kyu(?:n|\s)*nahi|kyun\s+nahi|kyon\s+nahi|why\s+not|"
    r"kyu(?:n|\s)*ho\s*raha|kyun\s+ho\s*raha|"
    r"stuck|fail(?:ed|ing)?|blocked|atak\s*gaya|atki\s*hai|atke|"
    r"rok\s*raha|rok\s*rahi|ruk(?:a|i)?\s*hua|"
    r"hamesha\s+(?:problem|dikkat|fail|atak)|"
    r"baar\s*baar\s+(?:fail|problem|dikkat|atak)|"
    r"loss\s+ho\s*raha|loss\s+ho\s*rahi|"
    r"galat\s+ho\s*raha|galat\s+ho\s*rahi)\b"
    r"|समस्या|परेशानी|दिक्कत|नहीं\s*हो\s*रहा|नहीं\s*मिल\s*रहा|"
    r"नहीं\s*रुक\s*रहा|क्यों\s*नहीं|अटक",
    re.IGNORECASE,
)


# Map of fine-grained intent → default supertype (overridden by problem/
# decision/timing detectors that fire first below).
_INTENT_TO_SUPERTYPE = {
    # Chart-inspection asks → PLANET_QUERY
    "planet_strength":    "PLANET_QUERY",
    "planet_position":    "PLANET_QUERY",
    "planet_in_house":    "PLANET_QUERY",
    "planet_combo":       "PLANET_QUERY",
    "comparison":         "PLANET_QUERY",
    "lagna_lookup":       "PLANET_QUERY",
    "moon_sign_lookup":   "PLANET_QUERY",
    "sun_sign_lookup":    "PLANET_QUERY",
    "nakshatra_lookup":   "PLANET_QUERY",
    "house_lookup":       "PLANET_QUERY",
    "yoga_check":         "PLANET_QUERY",
    # Timing asks → TIMING_QUERY
    "dasha_when":         "TIMING_QUERY",
    "dasha_current":      "TIMING_QUERY",
    "timing_when":        "TIMING_QUERY",
    # Catch-all
    "analysis_general":   "GENERAL_ANALYSIS",
}


# ── Fix-C: AI Ear → supertype direct mapping ─────────────────────────────────
# AI Ear's `ask_types` + `emotional_tone` + `domain` already capture the
# semantic intent of the question much more reliably than a regex on the raw
# text. When AI Ear succeeds with high confidence, we let it pick the
# supertype directly and skip the regex-based `_classify_supertype` below.
# Sprint-25 Fix-C2: chart-wide / multi-planet sweep markers. When ANY of
# these appear, a single-planet PLANET_QUERY contract is wrong — the user
# wants a chart overview, so we route to GENERAL_ANALYSIS instead.
_MULTI_PLANET_SWEEP_RX = re.compile(
    r"\b("
    r"kya[-\s]*kya|"
    r"saare|sabhi|sab\s+(?:planet|grah)|"
    r"konsa[-\s]*konsa|kaun[-\s]*kaun|"
    r"powerful\s+planets?\s+(?:he|hai|hain)|weak\s+planets?\s+(?:he|hai|hain)|"
    r"all\s+(?:my\s+)?planets?|every\s+planet|"
    r"list\s+(?:of\s+)?(?:my\s+)?planets?|"
    r"strong\s+(?:and|aur|or)\s+weak|powerful\s+(?:and|aur|or)\s+weak|"
    r"(?:kundli|chart)\s+(?:me|mein)\s+(?:kya|konsa|kaun|kitne)"
    r")\b",
    re.IGNORECASE,
)


def _is_multi_planet_sweep(question_text: str | None) -> bool:
    """True when the question asks for a chart-wide planet overview rather
    than a single-planet inspection. Keeps the AI Ear supertype mapper from
    forcing PLANET_QUERY on multi-planet sweeps like 'kya kya powerful
    planets he kya weak planets he batao'."""
    if not isinstance(question_text, str) or not question_text.strip():
        return False
    return bool(_MULTI_PLANET_SWEEP_RX.search(question_text))


# Sprint-25 Fix-E: canonical scope → supertype map. Each scope value emitted
# by the AI Ear corresponds to exactly ONE narrator supertype contract. This
# replaces the old ask_types/tone/bucket heuristic chain (kept as fallback
# for legacy extractions where question_scope=='unknown').
_SCOPE_TO_SUPERTYPE: dict[str, tuple[str, float]] = {
    "single_planet":          ("PLANET_QUERY",     0.95),
    "multi_planet_or_chart":  ("GENERAL_ANALYSIS", 0.95),
    "life_area_problem":      ("PROBLEM_QUERY",    0.95),
    "life_area_timing":       ("TIMING_QUERY",     0.95),
    "life_decision":          ("DECISION_QUERY",   0.95),
    "life_area_general":      ("GENERAL_ANALYSIS", 0.85),
    "remedy_request":         ("GENERAL_ANALYSIS", 0.80),
    "off_topic":              ("GENERAL_ANALYSIS", 0.60),
}


def _supertype_from_ai_ear(extraction, question_text: str | None = None) -> dict | None:
    """Map an AI Ear IntentExtraction object → supertype dict.

    PRIMARY signal (Sprint-25 Fix-E): the AI Ear's `question_scope` field
    deterministically picks the supertype via `_SCOPE_TO_SUPERTYPE`. This
    is the source of truth — no regex post-processing needed.

    FALLBACK signal: when scope == "unknown" (cache miss / older extraction
    schema), the legacy ask_types/tone/bucket heuristic decides.

    Returns None if extraction is missing, low-confidence, or both signals
    are inconclusive — caller then falls back to the regex
    `_classify_supertype`.
    """
    if not extraction or getattr(extraction, "source", "") != "ai_ear":
        return None
    conf = float(getattr(extraction, "confidence", 0.0) or 0.0)
    if conf < 0.70:
        return None

    # ── PRIMARY: question_scope ─────────────────────────────────────────
    scope = (getattr(extraction, "question_scope", "") or "unknown").strip().lower()
    mapped = _SCOPE_TO_SUPERTYPE.get(scope)
    if mapped:
        st, st_conf = mapped
        return {
            "supertype":  st,
            "confidence": st_conf,
            "reasons":    [f"AI Ear question_scope='{scope}' → {st}"],
            "source":     "ai_ear_scope",
        }

    # ── FALLBACK: legacy ask_types/tone heuristic (scope=='unknown') ────
    asks = set(getattr(extraction, "ask_types", []) or [])
    tone = (getattr(extraction, "emotional_tone", "") or "").lower()
    domain = (getattr(extraction, "domain", "") or "").lower()
    # Primary bucket — first intent's bucket name (model-emitted vocab).
    _intents = getattr(extraction, "intents", []) or []
    primary_bucket = ""
    if _intents:
        _b = getattr(_intents[0], "bucket", None) or (
            _intents[0].get("bucket") if isinstance(_intents[0], dict) else None
        )
        primary_bucket = (_b or "").lower()

    # 1. DECISION — explicit decision ask wins regardless of other signals.
    if "decision" in asks:
        return {
            "supertype": "DECISION_QUERY", "confidence": 0.92,
            "reasons":   [f"AI Ear ask_types={sorted(asks)} contains 'decision'"],
            "source":    "ai_ear",
        }

    # 2. PROBLEM — diagnosis ask MUST be paired with distress tone. A bare
    #    "diagnosis" ask without distress is usually chart inspection
    #    ("Foreign job ka yog hai kya") and should fall through to the
    #    PLANET / regex layer instead. The regex `_PROBLEM_RX` already
    #    catches explicit "nahi ho raha" / "kyon nahi" framings.
    if "diagnosis" in asks and tone in (
        "anxious", "desperate", "conflicted", "grieving", "angry"
    ):
        return {
            "supertype": "PROBLEM_QUERY", "confidence": 0.88,
            "reasons":   [f"AI Ear ask_types={sorted(asks)} + tone={tone}"],
            "source":    "ai_ear",
        }

    # 3. TIMING — explicit "kab" ask.
    if "timing" in asks:
        return {
            "supertype": "TIMING_QUERY", "confidence": 0.92,
            "reasons":   [f"AI Ear ask_types={sorted(asks)} contains 'timing'"],
            "source":    "ai_ear",
        }

    # 4. PLANET — explanation / comparison ask under the chart-inspection
    #    domain (general / no specific life-area). This catches "Mars kaisa
    #    hai", "Saturn vs Jupiter strong kaun", "lagna kya hai" etc.
    #
    #    VETO when the question is a chart-wide multi-planet sweep
    #    ("kya kya powerful planets", "saare grah", "all planets") OR when
    #    AI Ear's primary bucket is itself a chart-overview signal
    #    ("analysis" / "general"). PLANET_QUERY is single-planet — using
    #    it for sweeps gives a contract-locked single-planet answer that
    #    ignores the rest of the chart.
    if (("explanation" in asks or "comparison" in asks)
            and domain in ("general", "")
            and not _is_multi_planet_sweep(question_text)
            and primary_bucket not in ("analysis", "general", "")):
        return {
            "supertype": "PLANET_QUERY", "confidence": 0.85,
            "reasons":   [
                f"AI Ear ask_types={sorted(asks)} + domain={domain}"
                f" + bucket={primary_bucket or 'none'}"
            ],
            "source":    "ai_ear",
        }

    # 5. OUTCOME without explicit timing — asking "kaisa rahega" without
    #    a date. Treat as GENERAL_ANALYSIS (a balanced overview).
    if "outcome" in asks and "timing" not in asks:
        return {
            "supertype": "GENERAL_ANALYSIS", "confidence": 0.75,
            "reasons":   [f"AI Ear ask_types={sorted(asks)} (outcome only)"],
            "source":    "ai_ear",
        }

    # 6. Recovery ("wapas milega") behaves like TIMING when conf is high.
    if "recovery" in asks:
        return {
            "supertype": "TIMING_QUERY", "confidence": 0.85,
            "reasons":   [f"AI Ear ask_types={sorted(asks)} (recovery → timing)"],
            "source":    "ai_ear",
        }

    # 7. Remedy-only ask without other signals → GENERAL.
    if "remedy" in asks and len(asks) == 1:
        return {
            "supertype": "GENERAL_ANALYSIS", "confidence": 0.75,
            "reasons":   [f"AI Ear ask_types={sorted(asks)} (remedy only)"],
            "source":    "ai_ear",
        }

    # Ambiguous — let regex layer try.
    return None


def _classify_supertype(question: str, question_intent: dict | None = None) -> dict:
    """Map a user question + already-computed fine-grained question_intent to
    one of 5 narrator supertypes that drive the strict response-rule contract.

    Detection priority (most-specific first):
      1. DECISION_QUERY   — "X karu ya nahi", "should I X"
      2. PROBLEM_QUERY    — "X nahi ho raha", "kyon nahi", "problem"
      3. TIMING_QUERY     — fine intent ∈ {dasha_when, dasha_current, timing_when}
      4. PLANET_QUERY     — fine intent matches one of the chart-inspection set
      5. GENERAL_ANALYSIS — fallback

    Returns: {supertype, confidence, reasons, source_intent}
    """
    q = (question or "").strip()
    intent = (question_intent or {}).get("intent") or "analysis_general"
    reasons: list[str] = []

    if not q:
        return {
            "supertype": "GENERAL_ANALYSIS", "confidence": 0.0,
            "reasons": ["empty question"], "source_intent": intent,
        }

    # 1. DECISION first — most pragmatic signal, user wants a verdict.
    if _DECISION_RX.search(q):
        reasons.append("decision pattern matched (X karu ya nahi / should I)")
        return {
            "supertype": "DECISION_QUERY", "confidence": 0.92,
            "reasons": reasons, "source_intent": intent,
        }

    # 2. PROBLEM — "why is this happening" framing.
    if _PROBLEM_RX.search(q):
        reasons.append("problem pattern matched (nahi ho raha / kyon / dikkat)")
        return {
            "supertype": "PROBLEM_QUERY", "confidence": 0.90,
            "reasons": reasons, "source_intent": intent,
        }

    # 3. TIMING — fine intent already detected dasha_when / timing_when /
    #    dasha_current. We trust the fine classifier here.
    if intent in ("dasha_when", "dasha_current", "timing_when"):
        reasons.append(f"fine intent='{intent}' → timing")
        return {
            "supertype": "TIMING_QUERY", "confidence": 0.93,
            "reasons": reasons, "source_intent": intent,
        }

    # 4. PLANET — chart-inspection asks.
    mapped = _INTENT_TO_SUPERTYPE.get(intent)
    if mapped == "PLANET_QUERY":
        reasons.append(f"fine intent='{intent}' → planet inspection")
        return {
            "supertype": "PLANET_QUERY", "confidence": 0.90,
            "reasons": reasons, "source_intent": intent,
        }

    # 5. Default
    reasons.append(f"fine intent='{intent}' → general analysis fallback")
    return {
        "supertype": "GENERAL_ANALYSIS", "confidence": 0.55,
        "reasons": reasons, "source_intent": intent,
    }


# Per-supertype STRICT contract block. Injected as the LAST system message in
# the OpenAI call so it gets recency-lock priority over every earlier system
# msg (chart, brand voice, engine verdict). Wording is intentionally short and
# imperative — long contracts get partially ignored by the model.
# ── Sprint-26 Step 1 (Apr 28 2026) — UNIFIED NARRATOR BASE PROMPT ───────────
# Until now, each supertype owned a fully self-contained string in
# `_SUPERTYPE_CONTRACT_BLOCKS` — six near-duplicate scaffolds with the same
# divider lines and the same "use only engine facts / don't switch topic"
# rules pasted into each. That's the "scattered wiring" the user flagged:
# changing one universal rule meant editing six places.
#
# Step 1 of the unification migration extracts ONLY the genuinely-universal
# rules (those that appear verbatim in 3+ supertypes) into one header that
# every contract gets prepended with. Per-supertype BODIES keep all of their
# original type-specific rules — we are NOT re-tuning behavior, just
# de-duplicating the shared scaffolding.
#
# Out of scope for Step 1 (deliberately untouched):
#   • Domain-specific NARRATOR OVERRIDES (WEALTH/HEALTH/CAREER/LOVE/STOCK/
#     MARRIAGE) which live in separate code paths — Step 3.
#   • Wealth structured-output JSON schema + prompt — Step 3.
#   • Validators / brand-safety guards — Step 3 (kept as safety layer).
#
# Public API preserved: `_build_supertype_contract(supertype)` is still the
# single entry point, so the install site at line 6670 needs no change.
_NARRATOR_UNIVERSAL_HEADER: str = (
    "════════════════════════════════════════════════════════════════════\n"
    "COSMIC INTELLIGENCE — UNIFIED NARRATOR CONTRACT\n"
    "════════════════════════════════════════════════════════════════════\n"
    "UNIVERSAL RULES (apply to EVERY answer regardless of question type):\n"
    "  • Use ONLY engine-provided / locked-fact data — never invent dasha\n"
    "    names, dates, house lords, planet positions, or transit windows\n"
    "    that are absent from the LOCKED FACTS block above.\n"
    "  • DO NOT switch to topics the user did NOT ask about (no career when\n"
    "    user asked finance, no marriage when user asked health, etc.).\n"
    "  • Tone: asli astrologer, plain Hinglish, confident not preachy.\n"
    "    No 'as an AI', 'main samajh sakta hoon', no LLM-speak.\n"
    "  • Open with the answer — no throat-clearing, no preamble, no generic\n"
    "    philosophy ('har dasha mein ups-downs hote hain').\n"
    "════════════════════════════════════════════════════════════════════\n"
)


# ── Sprint-26 Step 2 (Apr 28 2026) — OUTPUT DISCIPLINE LAYER ────────────────
# Step 1 cleaned up the SCAFFOLDING (one base prompt, one builder, no copy-
# paste of universal rules). Step 2 adds the actual OUTPUT DISCIPLINE on top
# — the rules that govern how the LLM should *shape* its answer regardless of
# topic: length default, decisive tone, anti-bloat, arrow-style format,
# no-repetition. These were either missing or were buried inside individual
# supertype bodies in inconsistent wording.
#
# Design choice — why a SEPARATE constant (not merged into the header):
#   • Keeps Step 2's contribution surgically visible in the file. If we ever
#     need to roll back output-discipline tuning without losing Step 1's
#     deduplication, we delete this block alone.
#   • The two layers serve different purposes: header = "stay truthful",
#     discipline = "stay tight". They tune independently.
#
# Type-body precedence: a per-supertype body MAY relax the default length
# (e.g. GENERAL_ANALYSIS sets 4–6 lines for V→R→T) or tighten it (e.g.
# PLANET_QUERY sets 1–2 lines). The "default" wording below makes that
# precedence explicit so the model knows to honour the body when the two
# disagree.
#
# Out of scope (deferred to Step 3 per the user's "step by step" directive):
#   • Semantic-duplicate validator (post-hoc detection of repeated points
#     using embedding similarity) — belongs in the validator/safety layer.
#   • Hedge-language hard-block validator (regex on 'shayad', 'maybe',
#     'ho sakta hai' as the FINAL verdict) — belongs in the validator layer.
#   • Splitting DASHA / DOSHA / MATCH / TRANSIT into their own supertype
#     routes — a routing-engine change, not a narrator-prompt change.
_NARRATOR_OUTPUT_DISCIPLINE: str = (
    "OUTPUT DISCIPLINE (default rules — type-specific body may override):\n"
    "  • DEFAULT length: 1–3 short lines. Type body may extend this cap\n"
    "    (e.g. GENERAL_ANALYSIS allows 4–6 lines for the V→R→T structure)\n"
    "    or tighten it further. NEVER pad beyond what the body sets.\n"
    "  • One concept → one verdict. NEVER restate the same point in different\n"
    "    words across consecutive lines. If two sentences mean the same thing,\n"
    "    delete the weaker one.\n"
    "  • Decisive tone. Use HAI / HOGA / NAHI HOGA / RUKO / KARO. The hedge\n"
    "    ban applies to the FIRST-LINE verdict ONLY: 'shayad', 'maybe',\n"
    "    'ho sakta hai', 'might', 'depends on you' MUST NOT appear as the\n"
    "    conclusion the user reads first. Inside reasoning lines, bounded\n"
    "    uncertainty is allowed when timing is INFERRED (next AD lord change,\n"
    "    transit window) rather than read off a locked date — say so\n"
    "    explicitly ('approx', '~', 'aas-paas') so the user knows it's an\n"
    "    estimate and not invented.\n"
    "  • Arrow-style format for CAUSAL explanation (planet/house → effect).\n"
    "    Use it when the answer is 'X causes Y'. Examples:\n"
    "      ▸ Timing:  \"Jupiter MD end → Saturn MD shuru, control phase.\"\n"
    "      ▸ Finance: \"2H lord Saturn debilitated → savings rukne mein dikkat.\"\n"
    "      ▸ Career:  \"10H lord weak + Mars 6H → boss-clash, switch ka pressure.\"\n"
    "    Reserve plain prose for non-causal contexts (STRENGTH bucket lines,\n"
    "    structured V→R→T paragraphs where the body explicitly asks for it).\n"
    "    Do NOT force arrow-style into a single-line bucket answer.\n"
    "  • Anti-bloat — assume the user knows the system:\n"
    "      ▸ DO NOT define astrology terms ('antardasha matlab sub-period…',\n"
    "        'mahadasha is the major period of…') — the user already knows.\n"
    "      ▸ DO NOT explain Vedic basics, planet karakas, or house meanings\n"
    "        from scratch. Cite them only when they directly drive the verdict.\n"
    # ── Sprint-26 Step 2 — METHOD-NAME-DROP RULE WITHHELD ───────────────────
    # An earlier draft of this discipline included a bullet banning casual
    # name-drops of KP / Vimshottari / Parashari / Jaimini unless the method
    # choice changed the verdict. Live regression revealed it directly
    # contradicted Rule N (`openai_helper.py` ~line 2926) which MANDATES a
    # KP citation for finance/career/marriage topics ("you MUST include one
    # natural KP citation sentence... failing to cite is the same kind of
    # error as inventing facts"). The model correctly followed the louder
    # "MUST" instruction. Reconciling the two — either tightening Rule N to
    # "cite ONLY when KP and Vedic disagree" or removing Rule N entirely —
    # is a deliberate Step-3 task (cross-cutting rule unification across the
    # scattered domain prompts) and NOT something Step 2 should do silently.
    # Logged in replit.md for Step 3.
    "      ▸ DO NOT add philosophical filler ('har dasha mein ups-downs hote\n"
    "        hain', 'patience aur disciplined approach') unless the user\n"
    "        directly asked for guidance.\n"
    "════════════════════════════════════════════════════════════════════\n"
)


# ── Sprint-26 Step 4 Phase 1 (Apr 28 2026) — SAFE NARRATION LAYER ───────────
# User feedback after Step 2: "Tumne khud catch kiya — narrator might fabricate
# explanation to be helpful. Yeh sabse dangerous line hai. System unsafe state
# mein hai." User asked for hard guardrails: refuse rather than hallucinate
# when key signals are missing, ask one clarification line when domain is
# ambiguous, never invent dates.
#
# Phase 1 is the PROMPT-SIDE layer — three explicit rules the model reads and
# (mostly) obeys. Phase 2 will add the deterministic Python-side pre-LLM gate
# that checks locked_facts for required signals before calling OpenAI and
# short-circuits to a template when missing. Phase 1 first because:
#   1. It is a string addition — same surgical pattern as Steps 1 and 2.
#   2. If the LLM mostly obeys, Phase 2 may not be needed for low-stakes calls
#      and we ship a safer system today.
#   3. If the LLM ignores (the way it ignored METHOD-name-drop because Rule N
#      had a louder MUST), Phase 2 becomes the natural escalation with real
#      live evidence to justify it.
#
# Three rules:
#   GUARD-1: DATA-PRESENCE — refuse if dasha block missing/partial, instead
#            of fabricating a "good MD bad AD" explanation.
#   GUARD-2: DOMAIN-AMBIGUITY — when topic was tagged 'general' AND the
#            question described a sustained problem pattern, open with ONE
#            short clarifying line so the answer is precise instead of vague.
#   GUARD-3: NO FAKE DATES — when the user asked WHEN and locked facts have
#            no specific end-date, use temporary-phase language (Hinglish:
#            "phase temporary hai", "exact date locked nahi hai") rather
#            than inventing a month/year.
#
# Order in the contract: header → discipline → SAFE_FALLBACK → body → footer.
# Safe-fallback sits BEFORE the body so a body that says "always cite a date"
# (e.g. TIMING_QUERY) reads the body LAST and still wins on conflict — but
# the body is type-specific guidance, while the safe-fallback is a refusal
# trigger that overrides answer attempts. To resolve, the safe-fallback rules
# are phrased as preconditions ("IF data missing THEN refuse"), not as
# always-on overrides. They co-exist with type bodies cleanly.
_NARRATOR_SAFE_FALLBACK: str = (
    "SAFE NARRATION GUARDRAILS (refusal > hallucination — when in doubt, stop):\n"
    "  • GUARD-1 — DATA PRESENCE. Before answering ANY 'why is this happening'\n"
    "    or contradiction question, scan the LOCKED FACTS block for an\n"
    "    explicit CURRENT MAHADASHA line AND CURRENT ANTARDASHA line with\n"
    "    start–end dates. If EITHER is missing or partial, REFUSE rather than\n"
    "    invent. Use exactly:\n"
    "      \"Iss question ka honest answer dene ke liye aapki current dasha\n"
    "       aur transit context confirm karna padega. Birth time aur place\n"
    "       exact share kar sakte ho? Tab actual reason aur kab tak chalega\n"
    "       woh precise bata dunga.\"\n"
    "    NEVER fabricate a 'good MD bad AD' explanation when the dasha block\n"
    "    is absent or incomplete. This is the single most dangerous failure\n"
    "    mode for an astrology system.\n"
    "  • GUARD-2 — DOMAIN AMBIGUITY (PRE-FLIGHT CHECK BEFORE FIRST SENTENCE).\n"
    "    BEFORE writing ANY answer, run this two-line preflight in your head:\n"
    "      Q1: Did the user describe a sustained-problem pattern?\n"
    "          Triggers: 'problem hi problem', 'sab kuch ulta', '8–10\n"
    "          mahine se', 'kuch theek nahi', 'contradiction', 'paradox',\n"
    "          a 'kyun' question about a recurring negative state.\n"
    "          → SUSTAINED_PROBLEM = true / false\n"
    "      Q2: Did the user EXPLICITLY name a life-area anywhere in the\n"
    "          question text? Anchors: career / job / kaam, paisa / money\n"
    "          / finance / wealth, rishtey / relationship / marriage /\n"
    "          shaadi, sehat / health / body, ghar / home / property,\n"
    "          child / santaan, study / education / exam.\n"
    "          → DOMAIN_ANCHOR = true / false\n"
    "    IF SUSTAINED_PROBLEM=true AND DOMAIN_ANCHOR=false:\n"
    "      → Line 1 of your output MUST be exactly (verbatim):\n"
    "          \"Problem kis area mein zyada hai — career, paisa, rishtey,\n"
    "           ya sehat? Specific area pakad lu, fir actual reason aur\n"
    "           exit timing precise bata sakta hu.\"\n"
    "      → NO domain nouns, NO house-specific KP/Vedic inference,\n"
    "        NO 'relationship/career/finance/health' assumption may appear\n"
    "        BEFORE this line. Silently picking a domain from a KP cusp\n"
    "        signal or planet placement is FORBIDDEN in this branch.\n"
    "      → THIS RULE OVERRIDES the discipline-layer rule 'Open with the\n"
    "        answer — no preamble'. In this branch the clarifying question\n"
    "        IS the answer; stopping there is the safest move.\n"
    "      → If you choose to add more after Line 1, you MAY add ONE short\n"
    "        general-scan sentence flagged as 'general scan, domain-specific\n"
    "        deeper read alag se du' — but you MUST NOT cite a specific\n"
    "        house's promise/denial as if it were the user's actual issue.\n"
    "    IF SUSTAINED_PROBLEM=false OR DOMAIN_ANCHOR=true: skip GUARD-2 and\n"
    "    answer normally per the body rules below.\n"
    "  • GUARD-3 — NO FAKE DATES, EVER. If the user asked 'kab tak' / 'when'\n"
    "    AND the LOCKED FACTS do NOT contain an explicit end-date for the\n"
    "    relevant AD or a transit exit-date for the relevant graha, you\n"
    "    MUST NOT invent a month / year / window. Use:\n"
    "      \"Yeh phase temporary hai — exact end-date next transit ya dasha\n"
    "       shift par depend karta hai. Locked facts mein abhi exact boundary\n"
    "       nahi hai, isse aage date pin karne ke liye chart re-cast chahiye.\"\n"
    "    Bounded-uncertainty wording ('approx', '~', 'aas-paas', '±1 mahina')\n"
    "    is allowed ONLY when the AD or transit IS present in locked facts\n"
    "    but the day-level boundary is fuzzy. NEVER invent a date that is\n"
    "    not anchored to a fact already in the block above.\n"
    "════════════════════════════════════════════════════════════════════\n"
)


# Per-supertype BODIES — only the type-specific rules. The universal header
# AND the output-discipline layer above are added by
# `_build_unified_narrator_contract`; the closing divider is added below.
_NARRATOR_TYPE_BODIES: dict[str, str] = {
    "PLANET_QUERY": (
        "QUESTION TYPE: PLANET_QUERY\n"
        "User asked about a PLANET / CHART INSPECTION ('Mars kaisa hai' style).\n"
        "MUST do:\n"
        "  • Explain ONLY the planet's strength (D1 + D9 cross-check if D9 line\n"
        "    is present in locked facts).\n"
        # Sprint-26 Step 1 (post-architect-review patch) — restored the
        # explicit brevity cap. The architect flagged that the universal
        # tone rule ("asli astrologer, plain Hinglish") was weaker than the
        # original PLANET-specific "Stay short" wording; without an explicit
        # ceiling here the model could pad a planet-only answer.
        "  • Stay short — max 1–2 lines. One planet, one verdict, done.\n"
        "MUST NOT do:\n"
        "  • DO NOT mention dasha or any planetary period.\n"
        "  • DO NOT predict the future or give timing windows.\n"
        "  • DO NOT give advice, remedy, upay, or 'kya karein'.\n"
        "  • DO NOT over-answer. If the user asked about ONE planet, talk about\n"
        "    that ONE planet only.\n"
    ),
    "PROBLEM_QUERY": (
        "QUESTION TYPE: PROBLEM_QUERY\n"
        "User is reporting a PROBLEM ('paisa nahi ruk raha' style) and wants\n"
        "to know WHY it is happening.\n"
        "MUST do:\n"
        "  • Explain WHY the problem is happening — be real and specific.\n"
        "  • MUST cite the running dasha/antardasha AND the activated house\n"
        "    (or its lord) that is creating the friction. Both are mandatory.\n"
        "MUST NOT do:\n"
        "  • DO NOT give a generic motivational answer.\n"
        "  • DO NOT promise quick fixes — diagnose the cause, that's the job.\n"
    ),
    "TIMING_QUERY": (
        "QUESTION TYPE: TIMING_QUERY\n"
        "User asked WHEN something will happen / improve.\n"
        "MUST do:\n"
        "  • Answer the WHEN clearly — give the dasha transition date or the\n"
        "    next favourable window from locked facts.\n"
        "  • Mention which mahadasha/antardasha is changing and to what.\n"
        "  • Keep the explanation SHORT — date + one-line cause is enough.\n"
        "FALLBACK (Sprint-26 Fix-K) — when engine timing data is incomplete:\n"
        "  • If the LOCKED FACTS block does NOT include a topic-specific\n"
        "    'WINDOW:' line for the user's question, INFER the next\n"
        "    favourable window from the dasha sequence + transit context\n"
        "    that IS available in the kundli (current MD/AD with their\n"
        "    end-dates, the next AD lord, ongoing transits).\n"
        "  • State your reasoning explicitly so it is auditable, e.g.\n"
        "    'Jupiter Mahadasha / Rahu Antardasha 2024-01-29 → 2026-06-22\n"
        "     ke baad Jupiter MD / Saturn AD shuru hogi — control phase\n"
        "     wahi se start hoga'.\n"
        "MUST NOT do:\n"
        "  • DO NOT pad with unrelated chart analysis.\n"
        "  • DO NOT add advice unless explicitly asked.\n"
    ),
    "DECISION_QUERY": (
        "QUESTION TYPE: DECISION_QUERY\n"
        "User asked for a DECISION ('karu ya nahi' / 'should I' style).\n"
        "MUST do:\n"
        "  • Open with a CLEAR direction: HAAN / NAA / RUKO  (YES / NO / WAIT).\n"
        "  • Back it with 1–2 specific reasons drawn from locked facts —\n"
        "    name the dasha or planet that drove the call.\n"
        "  • Keep the whole answer tight and confident.\n"
        "MUST NOT do:\n"
        "  • DO NOT hedge with 'depends on you' / 'as per your wish'.\n"
        "  • DO NOT list every possible factor — pick the strongest 1–2.\n"
    ),
    "GENERAL_ANALYSIS": (
        "QUESTION TYPE: GENERAL_ANALYSIS\n"
        "User asked an open analysis question — usually a WHY + WHEN combo\n"
        "('kyun ho raha hai aur kab tak chalega').\n"
        "\n"
        "MANDATORY OUTPUT STRUCTURE — Verdict → Reason → [Recovery?] → Timing\n"
        "  1. VERDICT (1 line): Direct answer to the user's core ask. State\n"
        "     the conclusion first — do NOT bury it under analysis.\n"
        "     Examples:\n"
        "       \"Seedhi baat — Rahu hi main reason hai, akela nahi par primary.\"\n"
        "       \"Seedhi baat — yeh sirf dasha nahi, transit Saturn bhi push kar raha hai.\"\n"
        "  2. REASON (1–2 lines): Cite the SPECIFIC dasha + ONE relevant\n"
        "     house (or its lord) that drives the verdict. Name the planet\n"
        "     and what it is doing — not a textbook description.\n"
        "  2b. RECOVERY (1 line, CONDITIONAL — Sprint-26 Fix-Q):\n"
        "     INSERT this line ONLY when the user's question explicitly\n"
        "     asks about recovery — vocabulary triggers: 'recover',\n"
        "     'wapas aayega/milega', 'vasool', 'paisa wapas', 'nuksan\n"
        "     bharega/cover', 'recoup'. When triggered, format MUST be:\n"
        "       \"💰 Recovery: <LABEL>: <1-line reason>\"\n"
        "     LABEL ∈ {PARTIAL, FULL, SLOW, UNLIKELY}. Reason cites the\n"
        "     locked dasha window or transit shift — NO rupee amount,\n"
        "     NO bankruptcy prediction. ≤25 words. SKIP this line entirely\n"
        "     when no recovery sub-ask is present.\n"
        "  3. TIMING (1 line): Give the next inflection date from locked\n"
        "     facts (AD end-date, MD transition, or transit shift). One date,\n"
        "     not a range of speculations.\n"
        "\n"
        "FOCUS DISCIPLINE — surgical, not exhaustive:\n"
        "  • Houses to mention by topic (default allow-list — strict):\n"
        "      finance → 2H, 11H ONLY (12H is a LOSS-house, gated below).\n"
        "      career  → 10H, 6H (work-effort), 11H ONLY.\n"
        "      marriage → 7H, 5H (love), 2H (family) ONLY.\n"
        "      health  → 1H (lagna), 6H, 8H ONLY.\n"
        "  • Loss / dushtana houses (6H, 8H, 12H) are OFF-limits for finance,\n"
        "    career, marriage UNLESS the user's question explicitly mentions\n"
        "    loan, karz, EMI, loss, theft, hospital, sudden event, divorce,\n"
        "    accident, or similar adverse trigger word.\n"
        "  • Multi-domain questions (e.g. finance + career, marriage + health):\n"
        "    use ONLY the PRIMARY topic's allow-list. Do NOT take a union.\n"
        "    Primary topic is the FIRST one mentioned in the user's question.\n"
        "  • Dasha depth: cite MD lord + current AD lord + AD end-date. STOP.\n"
        "    NO Pratyantar dasha, NO Sookshma, NO nakshatra dispositor chains\n"
        "    UNLESS the user explicitly asked for 'detail mein' / 'depth mein'\n"
        "    / 'exact muhurat'. In that case length cap is relaxed to ~150 words.\n"
        "  • Planets: name at most 3 — the dasha lord(s) + the most relevant\n"
        "    karaka (Jupiter for wealth, Venus for relationships, Saturn for\n"
        "    delays, Mars for action). Skip the others.\n"
        "\n"
        "MUST do:\n"
        "  • Open with the Verdict line.\n"
        "  • Default length: 4–6 short lines (≤80 words). Tight, not bloated.\n"
        "    Relaxed to ~150 words ONLY when user asked 'detail mein' / 'depth\n"
        "    mein' / 'exact muhurat' explicitly.\n"
        "\n"
        "MUST NOT do:\n"
        "  • DO NOT dump every chart fact, every house, every planet.\n"
        "  • DO NOT introduce 6H/8H/12H/dushtana houses for non-loss topics.\n"
        "  • DO NOT add Pratyantar / Sookshma / nakshatra-lord chains by default.\n"
        "  • DO NOT add upay / remedy unless the user asked for it.\n"
    ),
    "STRENGTH_SUMMARY": (
        "QUESTION TYPE: STRENGTH_SUMMARY\n"
        "User asked which planets are strong / weak / vargottam in their chart.\n"
        "Locked facts already contain the authoritative buckets:\n"
        "  ▸ STRENGTH BUCKETS — STRONG: ... | MODERATE: ... | WEAK: ...\n"
        "  ▸ VARGOTTAM (D1 sign == D9 sign): ...\n"
        "MUST do:\n"
        "  • Answer in EXACTLY 1–2 short Hinglish lines, nothing more.\n"
        "  • Use this exact format pattern:\n"
        "      \"Apke strong planets <X, Y, Z> hain. Weak planets <A, B> hain.\"\n"
        "    (Hinglish, comma-separated, no bullets, no headings.)\n"
        "  • Pull planet names ONLY from the STRENGTH BUCKETS line above.\n"
        "    Strong line → only STRONG bucket. Weak line → only WEAK bucket.\n"
        "  • If a bucket is empty, say e.g. \"koi planet strong nahi hai\" —\n"
        "    DO NOT borrow from another bucket.\n"
        "  • If you mention 'vargottam', the planet name MUST appear in the\n"
        "    VARGOTTAM list above. If list says (none), DO NOT use the word.\n"
        "MUST NOT do:\n"
        "  • DO NOT add a long narrative, dasha, advice, remedy, or upay.\n"
        "  • DO NOT add caveats / hedges (\"lekin yaad rakho...\" etc.).\n"
        "  • DO NOT invent vargottam, exalted, debilitated labels not in facts.\n"
        "  • DO NOT mention more than 2 lines total.\n"
    ),
}


# ── Sprint-26 Step 1 — Backwards-compatibility alias ────────────────────────
# Old name kept so any external import / inspect paths continue to work, but
# it now points at the new bodies-only dict (without the per-block headers
# and footers that the unified header/footer adds back). Anything that
# read the dict directly for STRING content will see SHORTER strings now —
# that's intentional and surfaces accidental direct-reads at startup.
_SUPERTYPE_CONTRACT_BLOCKS = _NARRATOR_TYPE_BODIES


# Closing divider that wraps every contract — matches the universal header
# style so the model sees one clean bracket pair per turn.
_NARRATOR_UNIVERSAL_FOOTER: str = (
    "════════════════════════════════════════════════════════════════════\n"
)


# ── Phase 4.5 — NARRATIVE NARRATOR BODY ─────────────────────────────────────
# When `_NARRATIVE_MODE` is on, this single body REPLACES every per-supertype
# body in `_NARRATOR_TYPE_BODIES`. The contract is intentionally short and
# voice-first so the model writes a 3-5 sentence flowing answer instead of
# the structured V→R→T template. Length-cap + tone discipline come from
# `_NARRATOR_OUTPUT_DISCIPLINE` (already prepended); safe-fallback rules
# from `_NARRATOR_SAFE_FALLBACK` still apply (refuse if data missing).
_NARRATIVE_NARRATOR_BODY: str = (
    "QUESTION TYPE: NARRATIVE_ANSWER\n"
    "Write a SHORT flowing Hinglish narrative — like an experienced\n"
    "astrologer talking directly to the user. NOT a report, NOT a template.\n"
    "\n"
    "REASONING METHOD — MD-AD-PD COMBINATION (mandatory):\n"
    "  Step 1: Identify the 3 active dasha planets — Mahadasha lord (MD),\n"
    "          Antardasha lord (AD), Pratyantar dasha lord (PD if present).\n"
    "  Step 2: Read each planet's POSITION from locked facts — house, sign,\n"
    "          retrograde, conjunction.\n"
    "  Step 3: Tag each planet's NATURE for the user's topic —\n"
    "          growth-giver / confusion-creator / aggressive-fast / slow-stable\n"
    "          / loss-trigger.\n"
    "  Step 4: COMBINE the 3 tags into ONE result — stable / mixed / volatile /\n"
    "          unstable. The combination IS the answer; never decide from one\n"
    "          planet alone.\n"
    "  Step 5: STABILITY CHECK — paisa rukega ya flow karega? Consistency hai\n"
    "          ya ups-downs? Health steady hai ya fluctuating? (topic-aware).\n"
    "  Step 6: NEAR-TERM TIMING — when does the next active-planet change\n"
    "          (next AD or PD shift) and what does that flip the combo to?\n"
    "          Use month-precision when AD/PD end-date is within 18 months,\n"
    "          else year-precision.\n"
    "\n"
    "OUTPUT SHAPE — strict:\n"
    "  • 3-5 sentences, ONE flowing paragraph.\n"
    "  • Reference at least 2 of {MD lord, AD lord, PD lord} BY NAME and\n"
    "    describe their COMBINED nature (e.g. 'Jupiter growth dena chahta\n"
    "    hai, par Rahu confusion create kar raha hai').\n"
    "  • Give ONE near-term inflection date in the user's natural phrasing\n"
    "    ('mid-June ke baad', 'Sep 2027 se', 'antardasha change hone ke\n"
    "    baad'). Pull the actual date from locked AD/PD end-dates — never\n"
    "    invent.\n"
    "  • Voice: direct, conversational, 'tum/aap' — no hedging, no\n"
    "    motivational fluff, no 'depends on you'.\n"
    "\n"
    "PHASE 4.6 — COMBO-FUSION DISCIPLINE (the BIG difference between\n"
    "narrative and report):\n"
    "  • SENTENCE 1 must FUSE the active planets into ONE combined verdict.\n"
    "    DO NOT enumerate planet-by-planet — that is a report, not a\n"
    "    narrative.\n"
    "    BAD (enumeration / report):\n"
    "      'Jupiter MD chal raha hai, Jupiter weak hai. Rahu AD chal\n"
    "       raha hai, Rahu bhi weak hai. Mars PD chal raha hai, Mars\n"
    "       energy de raha hai.'\n"
    "    GOOD (fused combo verdict):\n"
    "      'Tumhari current Jupiter–Rahu–Mars phase mein attraction aur\n"
    "       connection ke chances definitely hain, lekin Rahu confusion\n"
    "       aur Mars impulsiveness ki wajah se relationship stable\n"
    "       rehna mushkil ho sakta hai — love ho sakta hai, par clarity\n"
    "       aur patience ke bina tikega nehi.'\n"
    "    Notice: planets are joined with em-dash or '+' or 'aur'; their\n"
    "    natures are blended into ONE combined effect; the verdict is\n"
    "    direct and decisive.\n"
    "  • TOPIC FIDELITY — answer the user's ACTUAL question. Do NOT\n"
    "    pivot:\n"
    "      LOVE  question → talk attraction / connection / stability /\n"
    "                       clarity of CURRENT or near-term relations.\n"
    "                       NEVER drift to marriage promise / denial /\n"
    "                       delay / Upapada / shaadi yoga unless the\n"
    "                       user explicitly asked about marriage.\n"
    "      CAREER question → talk job / promotion / switch / boss-clash.\n"
    "                       NEVER drift to marriage or finance.\n"
    "      WEALTH question → talk income / savings / property / debt.\n"
    "                       NEVER drift to relationship.\n"
    "      MARRIAGE question → talk shaadi promise / timing / partner.\n"
    "                       NEVER pivot to general love-compatibility.\n"
    "  • NO PREAMBLE. Sentence 1 = the verdict + the active planets.\n"
    "    Banned openers: 'Seedhi baat —', 'Dekho —', 'Ek baat batata hu',\n"
    "    'Sun lo —', 'Bhai —'.\n"
    "  • NO METHOD-NAME-DROP in user-facing text. These are background\n"
    "    facts the engine uses; the user does NOT need to read them:\n"
    "      ✗ 'KP paddhati se bhi 7th cusp ka sub-lord …'\n"
    "      ✗ 'Cuspal sub-lord Sun marriage delay dikhata hai'\n"
    "      ✗ 'D9 navamsa mein 7L Mercury debilitated jaata hai'\n"
    "      ✗ 'Vimshottari + KP cross-check confirm karta hai'\n"
    "      ✗ 'Upapada Lagna Cancer mein hai'\n"
    "      ✗ 'Darakaraka Venus signature dikhata hai'\n"
    "      ✗ 'Jaimini paddhati se …'\n"
    "    EXCEPTION: cite KP / D9 / Upapada ONLY if the engine's KP and\n"
    "    Vedic verdicts DISAGREE on direction — then ONE short clause is\n"
    "    OK to flag the conflict. Otherwise omit.\n"
    "  • NO HOUSE-NUMEROLOGY DUMP unless the user explicitly named a\n"
    "    house. Do not write '7th ghar / 5th house / 11H aspect' as a\n"
    "    surface explanation; translate it to the human meaning instead\n"
    "    ('partnership area', 'romance area', 'gains area').\n"
    "\n"
    "MUST NOT (these will be auto-stripped — don't write them at all):\n"
    "  • NO score badges (🟡 WAIT 57/100 / 🟢 GO / 🔴 CAUTION).\n"
    "  • NO 'Verdict:' / 'Reason:' / 'Timing:' / 'Recovery:' headers.\n"
    "  • NO 'Window: …' or '➜ Better: …' lines.\n"
    "  • NO 'Kya hoga / Kya karein / Kya na karein' bullet sections.\n"
    "  • NO bullet points or emoji headers anywhere.\n"
    "  • NO upay / remedy / mantra line (🕉) unless user explicitly asked.\n"
    "  • NO 'Qualified doctor se consult karein' / 'CA / SEBI-registered\n"
    "    advisor' disclaimer suffix — these will be appended only if needed.\n"
    "  • NO defining astrology terms ('antardasha matlab sub-period…').\n"
    "\n"
    "CORE RULE (yaad rakhna):\n"
    "  Active planets ka COMBINATION hi final result deta hai —\n"
    "  single planet kabhi decision nahi deta. Aur narrative ka matlab\n"
    "  hai FUSED verdict, list nahi.\n"
)


def _build_unified_narrator_contract(supertype: str,
                                     *,
                                     has_recovery_subask: bool = False) -> str:
    """Sprint-26 Step 1 — single source of truth for the narrator contract.
    Combines the universal header, the per-supertype body, and the closing
    footer. Falls back to GENERAL_ANALYSIS body when an unknown supertype
    is passed (preserves the old `_build_supertype_contract` semantics).

    `has_recovery_subask` is read-through metadata that future steps can
    use to conditionally trim the GENERAL_ANALYSIS Recovery clause out of
    the prompt entirely when no recovery sub-ask was detected. For now we
    keep the conditional clause inline with explicit "SKIP when not asked"
    guard wording (same as before Step 1) so behavior stays byte-equivalent
    for the LLM — the parameter is plumbed for Step 2 use.

    Phase 4.5 (Apr 28, 2026): when `_NARRATIVE_MODE` is on, the per-
    supertype body is REPLACED with `_NARRATIVE_NARRATOR_BODY` regardless
    of `supertype`. The universal header / output-discipline / safe-
    fallback layers stay intact so truthfulness + refuse-on-missing-data
    + no-domain-inference guards remain enforced.
    """
    if _NARRATIVE_MODE:
        body = _NARRATIVE_NARRATOR_BODY
    else:
        body = _NARRATOR_TYPE_BODIES.get(
            supertype, _NARRATOR_TYPE_BODIES["GENERAL_ANALYSIS"]
        )
    # Sprint-26 Step 2 — output-discipline layer is injected between the
    # truthfulness header (Step 1) and the type-specific body. This puts the
    # length/tone/format defaults BEFORE the body so the body's overrides
    # (e.g. PLANET_QUERY's tighter "1–2 lines" or GENERAL_ANALYSIS's looser
    # "4–6 lines") win on conflict — the model honours the most-recent rule
    # for the active supertype.
    #
    # Sprint-26 Step 4 Phase 1 — safe-narration guardrails (refusal,
    # clarification, no-fake-dates) sit between the discipline layer and the
    # type body. They are PRECONDITION rules ("IF data missing THEN refuse"),
    # not blanket overrides, so they coexist with type bodies cleanly while
    # still being read before the body's positive instructions.
    return (
        _NARRATOR_UNIVERSAL_HEADER
        + _NARRATOR_OUTPUT_DISCIPLINE
        + _NARRATOR_SAFE_FALLBACK
        + body
        + _NARRATOR_UNIVERSAL_FOOTER
    )


# ── Sprint-26 Step 4 Phase 2 (Apr 28 2026) — DETERMINISTIC SAFE-NARRATION GATE
# Phase 1 (prompt-side _NARRATOR_SAFE_FALLBACK) confirmed the LLM cannot be
# trusted to refuse / clarify reliably — even verbatim-MUST + explicit
# discipline override + ban on domain inference, the model still inferred
# domain from KP cusp signals. Phase 2 makes GUARD-2 deterministic by
# short-circuiting BEFORE the LLM call.
#
# Why pre-LLM short-circuit (not post-LLM validator):
#   1. The supertype retry validator enforces "must mention dasha + timing"
#      for GENERAL_ANALYSIS — a clarification answer would be marked deficient
#      and the retry would force a domain answer, undoing the gate.
#   2. Skipping the LLM call also saves tokens on every gated request.
#   3. Trace + metrics are explicit (single 2g.SAFE_NARRATION_GATE event).
#
# GUARD-1 (data-presence refusal) and GUARD-3 (no fake dates) are NOT yet
# moved to Python-side. GUARD-3 works fine prompt-only (verified live).
# GUARD-1 needs a locked-facts dasha-presence inspector that requires
# probing the kundli/build_meta structure — separate Phase-3 task. The
# prompt-side rule remains as the soft layer until then.
def _safe_narration_gate(qu: dict,
                         qu_intent: str,
                         mode: str,
                         topic: str,
                         topic_source: str,
                         question_intent: dict | None,
                         question_supertype: dict | None,
                         req_id: str) -> dict | None:
    """Returns a complete response dict when the gate fires (caller MUST
    return immediately without calling the LLM) or None when normal flow
    should continue.

    GUARD-2 (DOMAIN CLARIFICATION) trigger:
      - qu['clarification_needed'] is True (= sustained_problem_pattern AND
        NOT domain_anchor_found, computed deterministically by
        question_understanding.py).
      - intent is analysis or problem (planet/timing/decision questions
        have a clear ask — clarification would be wrong UX).
      - mode is NOT 'general' (concept questions are not personal-domain).
    """
    if not qu.get("clarification_needed"):
        return None
    if qu_intent not in ("analysis", "problem"):
        return None
    if mode == "general":
        return None

    _trace(req_id, "2g.SAFE_NARRATION_GATE", {
        "guard":                       "GUARD-2_DOMAIN_CLARIFICATION",
        "sustained_problem_pattern":   True,
        "domain_anchor_found":         False,
        "intent":                      qu_intent,
        "mode":                        mode,
        "topic":                       topic,
        "outcome":                     "short_circuit_no_llm_call",
    })

    # Verbatim clarification text — same wording as the prompt-side GUARD-2
    # so behaviour is consistent whether the gate fires or the LLM does.
    clarify_text = (
        "Problem kis area mein zyada hai — career, paisa, rishtey, ya sehat? "
        "Specific area pakad lu, fir actual reason aur exit timing precise "
        "bata sakta hu."
    )

    return {
        "text":               clarify_text,
        "topic":              topic,
        "topic_source":       topic_source,
        "confidence":         float(qu.get("confidence") or 0.0),
        "source":             "safe_narration_gate_v2_domain_clarification",
        "follow_ups":         [],
        "question_intent":    question_intent,
        "question_supertype": question_supertype,
        "intent_extraction":  None,
    }


# ── Sprint-26 Step 4 Phase 3 (Apr 28 2026) — POST_LOGIC_CHECK ───────────────
# User's post-Phase-2 verdict: gate fixed input-side fabrication, but the LLM
# still has free hand on output-side. Existing validators are FORMAT-level
# only (dasha-word mention, timing-token presence, semantic dup). Truth-level
# claims (CURRENT MD planet name, CURRENT AD planet name, planet-in-house
# placements) are unchecked — model can confidently say "aap abhi Saturn MD
# mein hain" when actual is Jupiter MD, and validators wave it through.
#
# Phase 3 adds a TRUTH validator that runs AFTER the LLM call (and AFTER the
# supertype-contract retry). On mismatch: ONE corrective retry with the
# actual values injected as a system message (Option C — hybrid). If retry
# still mismatches → hard refusal template. Every correction event is
# explicitly traced — NO silent corrections (per user instruction).
#
# Scope (MVP):
#   - dasha_md_mismatch: response names a "current" Mahadasha that is NOT
#     the actual current MD from kundli['dashas'] tree (or currentDasha).
#   - dasha_ad_mismatch: same for Antardasha.
#   - planet_house_mismatch: response says "X in Nth house" but actual house
#     is different.
# Out of scope (Phase 4): transit verification (needs live ephemeris), KP
# sub-lord claims, yoga/dosha presence claims, numeric strength claims.
#
# Conservative-flag policy: dasha checks only fire when the response uses a
# present-tense temporal anchor ("abhi", "currently", "chal raha", "running",
# "present") — references to past/future MDs (e.g. "Saturn MD 2055 ke baad")
# are intentionally not flagged.

_POST_LOGIC_REFUSAL_TEXT = (
    "Mujhe abhi data inspect karne mein chhoti si discrepancy mil rahi hai — "
    "sahi answer dene ke liye birth time aur place ek baar dobara confirm "
    "kar do, ya thodi der baad try karo. Galat baat bolna nahi chahta."
)

# Phase 4.4 (Apr 28, 2026) — defensive timeout for VALIDATOR RETRY calls only.
# The primary generation (sync) and primary stream call use the OpenAI client's
# default timeout (60s). Validator retries (supertype + POST_LOGIC + lookup_engine)
# happen invisibly AFTER the user has already seen the first attempt; if the
# retry hangs, the SSE stream stays open with no `done` event → UI freeze.
# Cap retry calls at 12s so a slow OpenAI can't hold a session open
# indefinitely. On timeout, the existing retry-error refusal path fires.
# Override via env: VALIDATOR_RETRY_TIMEOUT_S=<float>.
try:
    _VALIDATOR_RETRY_TIMEOUT_S = float(
        os.environ.get("VALIDATOR_RETRY_TIMEOUT_S", "12.0")
    )
except (TypeError, ValueError):
    _VALIDATOR_RETRY_TIMEOUT_S = 12.0

# ── Phase 4.5 (Apr 28, 2026) — NARRATIVE MODE ──────────────────────────────
# Kills the V→R→T template (verdict badges, score 0-100, "Kya hoga / Kya
# karein / Kya na karein" bullet sections, upay suffix, CA/SEBI + medical
# disclaimer suffixes) across every supertype. Replaces it with a single
# 3-5 sentence Hinglish narrative grounded in the MD-AD-PD active-planet
# combination. The user's core rule:
#   "Active planets ka combination hi final result deta hai —
#    single planet kabhi decision nahi deta."
# Set NARRATIVE_MODE=0 to instantly revert to the legacy V→R→T contract +
# structured formatters + disclaimer injectors. Default ON. Fact-validators
# from Phase 4.4 (POST_LOGIC + lookup_engine) stay live in narrative mode —
# only FORMAT-validators + post-formatters get bypassed.
_NARRATIVE_MODE = os.environ.get("NARRATIVE_MODE", "1") != "0"


# ────────────────────────────────────────────────────────────────────────────
# Phase 4.7 T016 — CONTEXT DIET HELPERS (narrative mode only)
# ────────────────────────────────────────────────────────────────────────────
# Pre-Phase-4.7 the user-turn was 116K chars / ~29K tokens (full chart + 17
# sprint engines). ChatGPT achieves the same answer with <2K tokens. These
# slimmers strip everything not needed for the FUSED 3-5 sentence combo
# verdict shape that Phase 4.5/4.6/4.7 enforce. They ONLY run when
# `_NARRATIVE_MODE` is True; setting NARRATIVE_MODE=0 reverts to the full
# 116K block. The fact-validators (POST_LOGIC + lookup_engine from Phase 4.4)
# do NOT depend on these blocks being in the prompt — they re-derive from the
# kundli object, so slimming the prompt does not weaken correctness.

# Section-header allowlist for `locked_facts_str`. Lines must start with these
# EXACT prefixes (top-level "▸ " — column 0, no leading whitespace). Indented
# sub-lines under a kept header pass through; any other "▸ " or "── " section
# header is dropped along with its sub-lines.
_LF_KEEP_PREFIXES = (
    "▸ LAGNA:",
    "▸ MOON SIGN",
    "▸ SUN SIGN:",
    "▸ NAKSHATRA:",
    "▸ SADE-SATI:",
    "▸ YOGA COUNT:",
    "▸ POSITIVE YOGAS:",
    "▸ YOGA NAMES (raw,",
    "▸ DOSHA COUNT (Active):",
    "▸ ACTIVE DOSHAS:",
    "▸ MILD DOSHAS:",
    "▸ PLANET STRENGTHS:",
    "▸ VARGOTTAM (",  # NB: "(" disambiguates from "▸ VARGOTTAMA MATRIX"
    "▸ STRENGTH BUCKETS",
    "▸ CURRENT TRANSITS",
    "▸ CURRENT DASHA:",
    # Phase 4.8 T017 — DROPPED: "▸ DASHA WINDOW:" + "▸ PRATYANTAR"
    # These leak date ranges like "Moon Pratyantar (2026-02-18 se
    # 2026-05-01)" that the model dutifully recites in narrative-mode
    # answers, blowing the 1-2 sentence budget. CURRENT DASHA gives
    # MD-AD lord names which is the only timing signal needed for a
    # FUSED verdict; user can ask "kab" follow-up to get the window.
    "▸ HOUSE-LORD PLACEMENTS:",
    "▸ REMEDIES (classical",
)

# Topic-conditional additions (BACKGROUND-only, no name-drop required).
_LF_KEEP_BY_TOPIC = {
    "marriage": ("▸ UPAPADA LAGNA",),
    "love":     ("▸ UPAPADA LAGNA",),
}


def _slim_locked_facts_for_narrative(s: str, topic: str = "") -> str:
    """Phase 4.7 T016: drop heavy Sprint-19+ engine dumps from the
    LOCKED FACTS block. Keep only the core allowlist needed for the FUSED
    combo verdict. Reverts to identity if `s` is empty or has no header
    structure.

    Args:
        s: full locked_facts_str (~95K chars typical, 17 engine dumps)
        topic: question topic (love/marriage/career/health/...) — selects
            topic-specific additions from `_LF_KEEP_BY_TOPIC`

    Returns:
        slimmed string with only allowlisted ▸ sections + their sub-lines.
        Typical reduction: 95K → ~3K chars.
    """
    if not s:
        return s
    extra = _LF_KEEP_BY_TOPIC.get(topic or "", ())
    keep_prefixes = _LF_KEEP_PREFIXES + extra
    keep = True  # before any section header, default to keep (catches preamble)
    out_lines = []
    for line in s.splitlines():
        # Top-level section opener = column-0 ▸ / ── / ═══ (NOT indented)
        is_section_marker = (
            line.startswith("▸ ") or
            line.startswith("── ") or
            line.startswith("═")
        )
        if is_section_marker:
            if line.startswith("═"):
                # Always keep the framing ═══ separators
                keep = True
                out_lines.append(line)
                continue
            if line.startswith("── "):
                # Sprint-19+ engine sub-blocks — drop all in narrative mode
                keep = False
                continue
            # ▸ section header — keep iff allowlisted
            if any(line.startswith(p) for p in keep_prefixes):
                keep = True
                out_lines.append(line)
            else:
                keep = False
            continue
        # Non-section line (blank / indented sub-line / preamble) — emit only
        # when in a kept section
        if keep:
            out_lines.append(line)
    out = "\n".join(out_lines)
    # Collapse 3+ consecutive blank lines down to 2 (dropped sections leave
    # blank gaps)
    while "\n\n\n\n" in out:
        out = out.replace("\n\n\n\n", "\n\n\n")
    return out


def _slim_intel_for_narrative(s: str) -> str:
    """Phase 4.7 T016: keep the structural intel (planet status / house-lord
    placements / detected yogas / dosh / sade-sati) but drop the raw
    'Current transits today, sidereal Lahiri' degree dump — that data is
    redundant with the slim transit block, and the raw degrees are noise
    for narrative-mode answers.
    """
    if not s:
        return s
    out_lines = []
    drop_until_blank = False
    for line in s.splitlines():
        if line.strip().startswith("Current transits"):
            drop_until_blank = True
            continue
        if drop_until_blank:
            if line.strip() == "":
                drop_until_blank = False
            continue
        out_lines.append(line)
    return "\n".join(out_lines).rstrip() + ("\n" if out_lines else "")


def _slim_transit_for_narrative(s: str) -> str:
    """Phase 4.7 T016: drop the standalone transit block ENTIRELY in
    narrative mode. Locked-facts allowlist already retains the
    `▸ CURRENT TRANSITS (as of YYYY-MM-DD):` summary (slow-planet
    sign + house mapping from natal), which is the only transit signal
    needed for a 3-5 sentence FUSED verdict. The standalone block
    leaks raw degree numbers ("Jupiter: 84.38° Gemini") + a
    "sidereal Lahiri, UTC ..." technical header that biases the model
    toward enumeration / pseudo-precision instead of human language.
    """
    if not s:
        return s
    return ""


# Phase 4.2 (Apr 28, 2026) — engine honesty refusal.
# Fired when a PRIMARY engine phase (chart-intel / dasha / lagna / dosh /
# verdicts) failed to compute. Replaces the pre-Phase-4.2 Sprint-26 Fix-K
# silent bypass which let the AI's invented timing pass through whenever
# `engine_status.overall == "empty"`. The new stance: engine failure on a
# primary phase = real backend bug → refuse honestly, never guess.
_ENGINE_HONESTY_REFUSAL_TEXT = (
    "Abhi engine se kundli ka core data calculate karne mein technical issue "
    "aa raha hai — sahi answer dene ke liye thodi der baad try karo. Galat "
    "date ya prediction nahi dena chahta."
)

# Phase 4.2 — warning footer for OPTIONAL-phase failures (Sprint-33+
# transits/tajik/sahams/special-lagnas). Main answer survives, but user
# is told some advanced calculations are temporarily unavailable so they
# don't trust transit/varshaphala-derived claims that aren't in the answer.
_ENGINE_WARN_FOOTER_MARKER = "ⓘ Note:"
_ENGINE_WARN_FOOTER_TEXT = (
    "\n\nⓘ Note: kuch advanced calculations (transits/varshaphala/sahams) "
    "abhi available nahi hain — main answer affected nahi hai."
)


def _engine_honesty_check(engine_status, qu=None):
    """Phase 4.2 — decide whether to REFUSE, WARN, or take no action based
    on engine_status. Pure function. Kill-switch: env var ENGINE_HONESTY=0
    reverts to Phase 4.1 behavior (no refuse, no warn).

    Returns: {refuse: bool, warn: bool, failed_phases: list[str],
              optional_failed: list[str], reason: str}

    Decision matrix (per Apr 28 2026 user clarification — kundli always
    present, so primary failure = backend bug, not data gap):
      | Condition                                  | Verdict       |
      | any PRIMARY phase in `failed`              | REFUSE        |
      | only OPTIONAL phases in `failed`/skipped   | WARN          |
      | all phases ok                              | NO ACTION     |
    """
    import os as _os_eh
    if _os_eh.getenv("ENGINE_HONESTY", "1").strip() == "0":
        return {"refuse": False, "warn": False, "failed_phases": [],
                "optional_failed": [], "reason": "kill_switch_off"}
    if not isinstance(engine_status, dict):
        return {"refuse": False, "warn": False, "failed_phases": [],
                "optional_failed": [], "reason": "no_status"}
    try:
        from locked_facts import _is_primary_phase  # type: ignore
    except Exception:
        return {"refuse": False, "warn": False, "failed_phases": [],
                "optional_failed": [], "reason": "import_failed"}
    failed_entries = engine_status.get("failed") or []
    skipped_entries = engine_status.get("skipped") or []
    primary_failed = []
    optional_failed = []
    for e in failed_entries:
        if not isinstance(e, dict):
            continue
        ph = e.get("phase", "")
        if _is_primary_phase(ph):
            primary_failed.append(ph)
        else:
            optional_failed.append(ph)
    # OPTIONAL skipped phases also contribute to warn (e.g. transits skipped
    # due to upstream issue) — but PRIMARY skipped is treated like failed
    # because kundli is guaranteed present so a skip here = bug.
    for e in skipped_entries:
        if not isinstance(e, dict):
            continue
        ph = e.get("phase", "")
        if _is_primary_phase(ph):
            primary_failed.append(ph)
        else:
            optional_failed.append(ph)
    if primary_failed:
        return {"refuse": True, "warn": False,
                "failed_phases": primary_failed,
                "optional_failed": optional_failed,
                "reason": "primary_phase_failed"}
    if optional_failed:
        return {"refuse": False, "warn": True,
                "failed_phases": [],
                "optional_failed": optional_failed,
                "reason": "optional_phase_failed"}
    return {"refuse": False, "warn": False, "failed_phases": [],
            "optional_failed": [], "reason": "all_ok"}

_PL_SYNONYMS = {
    "surya": "sun",       "ravi": "sun",
    "chandra": "moon",    "chandrama": "moon",
    "mangal": "mars",     "kuja": "mars",
    "budh": "mercury",    "buddha": "mercury",
    "guru": "jupiter",    "brihaspati": "jupiter", "brhaspati": "jupiter",
    "shukra": "venus",    "shukr": "venus",
    "shani": "saturn",    "shanaiscara": "saturn",
}
_PL_CANON = ("sun","moon","mars","mercury","jupiter","venus","saturn",
             "rahu","ketu")
_PL_ALT = "|".join(list(_PL_CANON) + list(_PL_SYNONYMS.keys()))

_TRUTH_MD_RX = __import__("re").compile(
    rf"\b({_PL_ALT})\s+(?:(?:ki|ka|ke|'s)\s+)?"
    r"(?:maha[\s\-]?dasha|mahadasa|m\.?d\.?)\b",
    __import__("re").IGNORECASE,
)
_TRUTH_AD_RX = __import__("re").compile(
    rf"\b({_PL_ALT})\s+(?:(?:ki|ka|ke|'s)\s+)?"
    r"(?:antar[\s\-]?dasha|antardasa|bhukti|a\.?d\.?)\b",
    __import__("re").IGNORECASE,
)
# Phase 4.3 — inverted-syntax recall ("Mahadasha Saturn ki chal rahi" /
# "Antardasha Rahu ka", "MD Saturn", "Bhukti Rahu"). The original
# Phase 3 regexes only caught "<planet> <dasha-word>" form, so common
# Hinglish phrasing slipped through. Architect Phase-4 backlog item.
#
# Architect Phase-4.3-review fix #2 (revised): split the trailing tail into
# two precision tiers. Path A (direct strong verb) accepts hai/is/chal*
# right after the planet. Path B (possessive ki/ka/'s) is weaker on its own
# — phrases like "Mahadasha Jupiter ki details samjho" or "Mahadasha
# Jupiter ki wajah se pressure hai" should NOT register as current-MD
# claims. So Path B additionally requires a `chal*` motion verb within ~3
# tokens (the genuine "X ki chal rahi hai" shape).
#
# - "Mahadasha Saturn ki chal rahi hai." → fires (Path B: ki + chal)
# - "Antardasha Venus hai abhi."         → fires (Path A: direct hai)
# - "Mahadasha Jupiter ki details samjho." → no fire (Path B: no chal)
# - "Mahadasha Jupiter ki wajah se pressure hai." → no fire (no chal)
# - "Mahadasha Saturn ke yog ban rahe."  → no fire (ke not in tail set)
_TRUTH_MD_INVERTED_RX = __import__("re").compile(
    rf"\b(?:maha[\s\-]?dasha|mahadasa|m\.?d\.?)\s+({_PL_ALT})\s+"
    r"(?:"
        # Path A: direct strong present-claim verb
        r"(?:hai|is|chal\w*|chal\s*rah[aiy]?)"
        r"|"
        # Path B: possessive + (≤3 words filler) + motion verb (chal*)
        r"(?:ki|ka|'s)\s+(?:\w+\s+){0,3}chal\w*"
    r")\b",
    __import__("re").IGNORECASE,
)
_TRUTH_AD_INVERTED_RX = __import__("re").compile(
    rf"\b(?:antar[\s\-]?dasha|antardasa|bhukti|a\.?d\.?)\s+({_PL_ALT})\s+"
    r"(?:"
        r"(?:hai|is|chal\w*|chal\s*rah[aiy]?)"
        r"|"
        r"(?:ki|ka|'s)\s+(?:\w+\s+){0,3}chal\w*"
    r")\b",
    __import__("re").IGNORECASE,
)
_TRUTH_PLANET_HOUSE_RX = __import__("re").compile(
    rf"\b({_PL_ALT})\s+(?:in\s+|is\s+in\s+|sits?\s+in\s+|"
    r"placed\s+in\s+|hai\s+|ke\s+)?"
    r"(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)?\s+"
    r"(?:house|ghar|bhava|bhav)\b",
    __import__("re").IGNORECASE,
)
_TRUTH_HOUSE_PLANET_RX = __import__("re").compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:house|ghar|bhava|bhav)\s+"
    r"(?:mein|me|main|m[ae]\b|in)\s+"
    rf"({_PL_ALT})\b",
    __import__("re").IGNORECASE,
)
_NEGATION_NEAR_RX = __import__("re").compile(
    r"\b(nahi+n?|nahin|nai+|naa|not\b|never|kabhi\s+nahi|abhi\s+nahi|"
    r"khatam|khatm|finished|over|past|past\s+ho|wasn'?t|wasnt|wasn'?t)\b",
    __import__("re").IGNORECASE,
)

_TRUTH_PRESENT_RX = __import__("re").compile(
    r"\b(abhi|currently|chal\s*rah[aiy]|running|present|"
    r"now|aaj\s*kal|active|ongoing)\b",
    __import__("re").IGNORECASE,
)

# ── Phase 4.1 — extended truth-validator coverage ───────────────────────────
# Lookup tables local to truth-facts (small constants; kept here so the
# truth-facts block is self-contained and not order-dependent on the
# legacy _SIGN_RULER_M defined later in the module).
_TF_SIGNS_LC: tuple[str, ...] = (
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
)
_TF_SIGN_INDEX_LC: dict[str, int] = {s: i for i, s in enumerate(_TF_SIGNS_LC)}
_TF_SIGN_RULER_LC: dict[str, str] = {
    "aries": "mars",        "taurus": "venus",     "gemini": "mercury",
    "cancer": "moon",       "leo": "sun",          "virgo": "mercury",
    "libra": "venus",       "scorpio": "mars",     "sagittarius": "jupiter",
    "capricorn": "saturn",  "aquarius": "saturn",  "pisces": "jupiter",
}
# Sanskrit / Hinglish sign aliases → canonical lowercase English.
_TF_SIGN_ALIASES_LC: dict[str, str] = {
    "mesh": "aries", "mesha": "aries",
    "vrish": "taurus", "vrishabh": "taurus", "vrishabha": "taurus", "vrushabh": "taurus",
    "mithun": "gemini", "mithuna": "gemini",
    "kark": "cancer", "karka": "cancer", "karkat": "cancer", "karkata": "cancer",
    "simha": "leo", "sinh": "leo", "singh": "leo",
    "kanya": "virgo",
    "tula": "libra", "tul": "libra",
    "vrishchik": "scorpio", "vrischik": "scorpio", "vrishchika": "scorpio",
    "dhanu": "sagittarius", "dhanusha": "sagittarius", "dhanus": "sagittarius",
    "makar": "capricorn", "makara": "capricorn",
    "kumbh": "aquarius", "kumbha": "aquarius",
    "meen": "pisces", "meena": "pisces", "meenam": "pisces",
}


def _tf_canon_sign(s: Any) -> str:
    """Canonicalise sign name to lowercase English. Empty if unknown."""
    if not s:
        return ""
    n = str(s).strip().lower()
    n = _TF_SIGN_ALIASES_LC.get(n, n)
    return n if n in _TF_SIGN_INDEX_LC else ""


# Phase 4.1 — extended claim-detection regexes.
# All patterns are scoped so that incidental textbook-style references
# ("Saturn rules Capricorn") don't trip them; only chart-anchored
# assertions about the user's own chart should match.

# "Nth house ka swami/lord X" or "X is the Nth lord"
_TRUTH_HOUSE_LORD_RX = __import__("re").compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:house|ghar|bhava|bhav)\s+"
    r"(?:k[ae]\s+)?(?:swami|lord|malik|adhipati|owner)\s+"
    rf"(?:hai\s+|is\s+)?({_PL_ALT})\b",
    __import__("re").IGNORECASE,
)
_TRUTH_LORD_HOUSE_RX = __import__("re").compile(
    rf"\b({_PL_ALT})\s+(?:hai\s+|is\s+)?"
    r"(\d{1,2})(?:st|nd|rd|th)?\s+(?:house|ghar|bhava|bhav)\s+"
    r"(?:k[ae]\s+)?(?:swami|lord|malik|adhipati|owner)",
    __import__("re").IGNORECASE,
)

# Sign-name regex (English + Hinglish aliases)
_TF_SIGN_NAMES_RX_FRAG = (
    "aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|"
    "sagittarius|capricorn|aquarius|pisces|"
    "mesh|mesha|vrish|vrishabh|vrishabha|vrushabh|"
    "mithun|mithuna|kark|karka|karkat|karkata|"
    "simha|sinh|singh|kanya|tula|tul|vrishchik|vrischik|vrishchika|"
    "dhanu|dhanusha|dhanus|makar|makara|kumbh|kumbha|meen|meena|meenam"
)

# "X in <sign>" / "X is in <sign>" / "X hai <sign>" / "X placed in <sign>"
_TRUTH_PLANET_SIGN_RX_A = __import__("re").compile(
    rf"\b({_PL_ALT})\s+(?:is\s+in\s+|in\s+|hai\s+|placed\s+in\s+|sits?\s+in\s+|ke\s+)"
    rf"({_TF_SIGN_NAMES_RX_FRAG})\b",
    __import__("re").IGNORECASE,
)
# "X <sign> rashi/sign/mein" — explicit suffix anchor
_TRUTH_PLANET_SIGN_RX_B = __import__("re").compile(
    rf"\b({_PL_ALT})\s+({_TF_SIGN_NAMES_RX_FRAG})\s+"
    r"(?:rashi|sign|mein|me|main)\b",
    __import__("re").IGNORECASE,
)

# "X retrograde hai / is retrograde / vakri"
_TRUTH_RETROGRADE_RX = __import__("re").compile(
    rf"\b({_PL_ALT})\s+(?:is\s+|hai\s+)?"
    r"(?:retrograde|retro\b|vakri)\b",
    __import__("re").IGNORECASE,
)

# "manglik" / "mangal dosh(a)" / "mars dosha" — fact-class marker
_TRUTH_MANGLIK_RX = __import__("re").compile(
    r"\b(manglik|mangal\s+dosh[ai]?|mangalik|mars\s+dosha?)\b",
    __import__("re").IGNORECASE,
)

# ── Phase 4.3 — NAKSHATRA truth constants + regexes ──────────────────────────
# 27 canonical nakshatras + common Hinglish / spelling variants. Engine emits
# Title-Case canonical via kundli["nakshatra"] (Moon) and planets[].nakshatra
# (per planet). All variants normalize back to the canonical form.
_NAK_CANON: tuple[str, ...] = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)
# Variant → canonical Title-Case name. Includes spelling variants and
# space-stripped forms for the multi-word nakshatras.
_NAK_VARIANTS_LC: dict[str, str] = {
    # singletons
    "ashwini": "Ashwini", "ashvini": "Ashwini", "asvini": "Ashwini",
    "bharani": "Bharani",
    "krittika": "Krittika", "krithika": "Krittika", "kritika": "Krittika",
    "krttika": "Krittika",
    "rohini": "Rohini",
    "mrigashira": "Mrigashira", "mrigshira": "Mrigashira",
    "mrigasira": "Mrigashira", "mrugashira": "Mrigashira",
    "ardra": "Ardra", "aardra": "Ardra", "arudra": "Ardra",
    "punarvasu": "Punarvasu", "punervasu": "Punarvasu",
    "pushya": "Pushya", "pushyami": "Pushya",
    "ashlesha": "Ashlesha", "aslesha": "Ashlesha", "ashleysha": "Ashlesha",
    "magha": "Magha", "makha": "Magha",
    "hasta": "Hasta", "hast": "Hasta",
    "chitra": "Chitra", "chitta": "Chitra",
    "swati": "Swati", "svati": "Swati", "swathi": "Swati",
    "vishakha": "Vishakha", "vishaka": "Vishakha", "visakha": "Vishakha",
    "anuradha": "Anuradha", "anushada": "Anuradha",
    "jyeshtha": "Jyeshtha", "jyeshta": "Jyeshtha", "jyeshtah": "Jyeshtha",
    "jyestha": "Jyeshtha",
    "mula": "Mula", "moola": "Mula", "mool": "Mula",
    "shravana": "Shravana", "sravana": "Shravana", "shravan": "Shravana",
    "dhanishta": "Dhanishta", "dhanishtha": "Dhanishta",
    "dhanista": "Dhanishta",
    "shatabhisha": "Shatabhisha", "satabhisha": "Shatabhisha",
    "shatabhishak": "Shatabhisha", "shatataraka": "Shatabhisha",
    "revati": "Revati",
    # multi-word — spaceless and hyphenated variants
    "purvaphalguni": "Purva Phalguni", "purva phalguni": "Purva Phalguni",
    "purva-phalguni": "Purva Phalguni", "poorvaphalguni": "Purva Phalguni",
    "uttaraphalguni": "Uttara Phalguni", "uttara phalguni": "Uttara Phalguni",
    "uttara-phalguni": "Uttara Phalguni",
    "purvaashadha": "Purva Ashadha", "purva ashadha": "Purva Ashadha",
    "purva-ashadha": "Purva Ashadha", "poorvashadha": "Purva Ashadha",
    "purvashadha": "Purva Ashadha",
    "uttaraashadha": "Uttara Ashadha", "uttara ashadha": "Uttara Ashadha",
    "uttara-ashadha": "Uttara Ashadha", "uttarashadha": "Uttara Ashadha",
    "purvabhadrapada": "Purva Bhadrapada", "purva bhadrapada": "Purva Bhadrapada",
    "purva-bhadrapada": "Purva Bhadrapada", "poorvabhadrapada": "Purva Bhadrapada",
    "uttarabhadrapada": "Uttara Bhadrapada", "uttara bhadrapada": "Uttara Bhadrapada",
    "uttara-bhadrapada": "Uttara Bhadrapada", "uttarabhadra": "Uttara Bhadrapada",
}
# Pre-populate the canonical form itself (lowercased) so direct matches work.
for _c in _NAK_CANON:
    _NAK_VARIANTS_LC.setdefault(_c.lower(), _c)


def _norm_nakshatra(s: Any) -> str:
    """Canonicalise nakshatra name to Title-Case canonical (e.g. 'krittika'
    → 'Krittika', 'purvaphalguni' → 'Purva Phalguni'). Empty if unknown."""
    if not s:
        return ""
    n = str(s).strip().lower()
    # Collapse multiple internal spaces
    n = " ".join(n.split())
    # Try direct lookup
    if n in _NAK_VARIANTS_LC:
        return _NAK_VARIANTS_LC[n]
    # Try spaceless lookup (handles "purva phalguni" → "purvaphalguni")
    n_spaceless = n.replace(" ", "").replace("-", "")
    return _NAK_VARIANTS_LC.get(n_spaceless, "")


# Regex fragment alternation — sorted by length DESC so longer multi-word
# variants match before their substring siblings (e.g. "purva phalguni" wins
# over "phalguni"). Includes literal spaces and hyphens.
_NAK_NAMES_SORTED = sorted(_NAK_VARIANTS_LC.keys(), key=len, reverse=True)
_NAK_NAMES_RX_FRAG = "|".join(
    __import__("re").escape(n) for n in _NAK_NAMES_SORTED
)

# AI claims: "(aapka|aapki|tumhara|your)\s+nakshatra\s+(is|hai)?\s+<NAK>"
# Subject defaults to MOON (user's birth nakshatra) for generic possessive.
_TRUTH_NAKSHATRA_USER_RX = __import__("re").compile(
    r"\b(?:aap?ka|aap?ki|tumhara|tumhari|your|mera|meri|mer[ae])\s+"
    r"(?:janm\s+)?nakshatra\s+(?:is\s+|hai\s+|=\s*)?"
    rf"({_NAK_NAMES_RX_FRAG})\b",
    __import__("re").IGNORECASE,
)
# AI claims: "Moon's nakshatra is <NAK>" / "Chandra ka nakshatra <NAK>" /
# "<planet>'s nakshatra <NAK>"
_TRUTH_NAKSHATRA_PLANET_RX = __import__("re").compile(
    rf"\b({_PL_ALT})(?:'s|\s+ka|\s+ki)?\s+nakshatra\s+"
    r"(?:is\s+|hai\s+|=\s*)?"
    rf"({_NAK_NAMES_RX_FRAG})\b",
    __import__("re").IGNORECASE,
)
# AI claims: "nakshatra <NAK> hai" / "nakshatra is <NAK>" — bare assertion,
# defaults to MOON subject.
_TRUTH_NAKSHATRA_BARE_RX = __import__("re").compile(
    rf"\bnakshatra\s+(?:is\s+|=\s*)?({_NAK_NAMES_RX_FRAG})\s+"
    r"(?:hai|is)\b",
    __import__("re").IGNORECASE,
)
# Pada claim — pada N where N is 1..4. Patterns:
#   "pada 2", "2nd pada", "pada is 2", "<NAK> ke 3 pada", "pada 4 hai"
_TRUTH_PADA_RX = __import__("re").compile(
    r"\bpada\s+(?:is\s+|hai\s+|=\s*)?([1-4])\b",
    __import__("re").IGNORECASE,
)
_TRUTH_PADA_ORDINAL_RX = __import__("re").compile(
    r"\b([1-4])(?:st|nd|rd|th)?\s+pada\b",
    __import__("re").IGNORECASE,
)

# Phase 4.1 — when a "X Nth house" planet-house regex match is followed
# closely by "swami/lord/malik/...", it's a LORD-OF-HOUSE claim, not an
# IN-HOUSE claim. Suppress the planet-house violation in that case.
_TRUTH_LORDISH_TAIL_RX = __import__("re").compile(
    r"^\s*(?:k[ae]\s+)?(?:swami|lord|malik|adhipati|owner)\b",
    __import__("re").IGNORECASE,
)


def _tf_negated_after(text: str, end: int, max_chars: int = 30) -> bool:
    """Phase-4.1 clause-bounded negation guard for chart-fact claims.

    Scans `text` starting at `end` for up to `max_chars`, but STOPS at the
    first clause-boundary marker (`.`, `,`, `;`, ` aur `, ` and `, ` lekin `,
    ` but `, newline). Returns True if a negation token appears in that
    bounded slice. Tighter than the raw 60-char tail used for dasha/planet-
    house (those rarely co-occur with unrelated negations).
    """
    if end >= len(text):
        return False
    tail = text[end: end + max_chars + 30]  # small look-ahead for boundary
    # Clause boundaries
    import re as _re
    bm = _re.search(r"[.,;\n]| aur | and | lekin | but | par ", tail,
                    _re.IGNORECASE)
    cut = bm.start() if bm else min(max_chars, len(tail))
    cut = min(cut, max_chars)
    return bool(_NEGATION_NEAR_RX.search(tail[:cut]))


# ── Phase 4.4 — LOOKUP_ENGINE constants (lagna + dasha-end-date) ────────────
# Extends POST_LOGIC with two detector families that close the remaining
# "engine-lookable" gap left by Phase 4.1/4.3:
#   1. lagna_mismatch       — AI states a wrong ascendant sign
#   2. dasha_end_year_mismatch — AI states a wrong end-year for the CURRENT MD
# (planet-house, planet-sign, retrograde, manglik, nakshatra, pada, MD, AD
# are already covered in Phase 4.1/4.3 above.) Both detectors are
# conservative: explicit value mismatch only, negation-aware, and
# disambiguated against the truth's CURRENT MD planet so future-Mahadasha
# descriptions don't false-fire.
# Phase 4.4 — sign variant map for lagna detection. Built FROM the
# canonical _TF_SIGN_ALIASES_LC table so we stay in lock-step with the
# rest of the engine's sign canonicalization (Brish/Vrush/Singh/Karkat
# /Meenam etc. all flow through automatically). English canonical names
# are added explicitly so they self-map.
_SIGN_VARIANT_LC: dict[str, str] = {
    s: s for s in _TF_SIGNS_LC
}
_SIGN_VARIANT_LC.update(_TF_SIGN_ALIASES_LC)
# Architect-recommended extras: regional spellings not in the engine
# alias table but plausible in user-facing copy.
_SIGN_VARIANT_LC.update({
    "brish": "taurus", "brishabh": "taurus", "vrush": "taurus",
})
# Sort by length DESC so longer variants match before their prefixes
# (e.g. "vrishchika" before "vrish") in the regex alternation.
_SIGN_VARIANTS_RX_FRAG = "|".join(
    sorted(_SIGN_VARIANT_LC.keys(), key=len, reverse=True)
)
# Forward: "Aapki lagna Aries hai" / "ascendant is Mesh" / "lagna Aries hai"
_TRUTH_LAGNA_FWD_RX = __import__("re").compile(
    r"\b(?:aap?k[aieo]\s+|tumhari\s+|your\s+|mer[aieo]\s+)?"
    r"(?:lagna|ascendant|asc\b|first\s+house)\s+"
    r"(?:rashi\s+)?(?:is\s+|hai\s+|=\s*)?"
    rf"({_SIGN_VARIANTS_RX_FRAG})\b",
    __import__("re").IGNORECASE,
)
# Inverted: "Aries lagna" / "Mesh ascendant"
_TRUTH_LAGNA_INV_RX = __import__("re").compile(
    rf"\b({_SIGN_VARIANTS_RX_FRAG})\s+(?:lagna|ascendant|asc\b)\b",
    __import__("re").IGNORECASE,
)
# Dasha end-year claims — planet-anchored only. We deliberately do NOT
# match bare "Mahadasha 2039 tak" because that's ambiguous with future-MD
# descriptions (e.g. "phir Mercury Mahadasha 2056 tak chalegi"). The
# planet-anchored form lets us cross-check against truth.current_md.planet:
# we only fire when the AI is talking about the CURRENT MD's end year.
# Tempered gap that disallows another dasha token from "bridging"
# adjacent MD clauses. Architect-found FP: "Saturn Mahadasha ke baad
# Mercury Mahadasha 2056 tak chalegi." used to match planet=Saturn,
# year=2056. The gap now refuses to consume a second mahadasha/dasha/MD
# word, so once the next dasha clause begins the FWD pattern no longer
# extends through it.
_DASHA_GAP_TEMPERED = (
    r"(?:(?!\b(?:mahadasha|maha\s*dasha|dasha|md)\b)[^.\n]){0,60}?"
)
# Forward: "Saturn Mahadasha 2039 tak", "Saturn dasha 2039 me khatam"
_TRUTH_DASHA_END_FWD_RX = __import__("re").compile(
    rf"\b({_PL_ALT})\s+(?:ki\s+|ka\s+|of\s+)?"
    r"(?:mahadasha|maha\s*dasha|dasha|MD)\b"
    + _DASHA_GAP_TEMPERED +
    r"\b(\d{4})\s+"
    r"(?:tak|me\s+khatam|me\s+complete|until|ends?\s+in|"
    r"end\s+ho|khatam\s+ho|complete\s+ho|samapt|chalegi|chalega|hogi|hoga)\b",
    __import__("re").IGNORECASE,
)
# Inverted: "Mahadasha Saturn ki 2039 tak chalegi"
_TRUTH_DASHA_END_INV_RX = __import__("re").compile(
    r"\b(?:mahadasha|maha\s*dasha|dasha|MD)\s+"
    rf"({_PL_ALT})\s+(?:ki\s+|ka\s+)?"
    + _DASHA_GAP_TEMPERED +
    r"\b(\d{4})\s+"
    r"(?:tak|me\s+khatam|me\s+complete|until|ends?\s+in|"
    r"end\s+ho|khatam\s+ho|complete\s+ho|samapt|chalegi|chalega|hogi|hoga)\b",
    __import__("re").IGNORECASE,
)
# English leading-keyword form: "Saturn Mahadasha ends in 2055" / "until 2055"
# (keyword appears BEFORE the year, not after — separate from the FWD/INV
# Hinglish patterns where the keyword trails the year as in "2039 tak").
_TRUTH_DASHA_END_EN_RX = __import__("re").compile(
    rf"\b({_PL_ALT})\s+(?:ki\s+|ka\s+|of\s+)?"
    r"(?:mahadasha|maha\s*dasha|dasha|MD)\b"
    + _DASHA_GAP_TEMPERED +
    r"\b(?:ends?\s+in|will\s+end\s+in|expires?\s+in|"
    r"runs?\s+(?:un)?til|completes?\s+in|finishes?\s+in|"
    r"until|till)\s+(\d{4})\b",
    __import__("re").IGNORECASE,
)


def _norm_planet_lc(name: str) -> str:
    """LOWERCASE canonical planet name. Distinct from _norm_planet_name
    (defined later in this module for legacy code) which returns Title-
    Case. POST_LOGIC_CHECK uses lowercase consistently for set-membership
    and dict-key comparisons against planet_house map.
    """
    n = (name or "").lower().strip()
    return _PL_SYNONYMS.get(n, n)


def _build_truth_facts(kundli: dict) -> dict:
    """Extract authoritative facts from kundli for POST_LOGIC_CHECK.

    Returns:
        {
          "planet_house":   {planet_lc: house_int},
          "planet_sign":    {planet_lc: sign_lc}      # Phase 4.1
          "retrograde":     set[planet_lc]            # Phase 4.1
          "house_lord":     {1..12: planet_lc}        # Phase 4.1
          "manglik":        bool | None               # Phase 4.1
          "nakshatra":      {planet_lc: nak_canonical} # Phase 4.3
          "nakshatra_pada": {planet_lc: int 1..4}     # Phase 4.3
          "current_md":     {"planet": str, ...} | None,
          "current_ad":     {"planet": str, ...} | None,
          "current_pd":     {"planet": str, ...} | None,  # Phase 4.5
        }
    """
    out: dict = {
        "planet_house":   {},
        "planet_sign":    {},
        "retrograde":     set(),
        "house_lord":     {},
        "manglik":        None,
        "nakshatra":      {},
        "nakshatra_pada": {},
        "current_md":     None,
        "current_ad":     None,
        # Phase 4.5 — Pratyantar dasha (3rd active planet). Required by the
        # narrative-mode MD-AD-PD combo prompt so the AI can reason from a
        # 3-planet combination instead of single-planet citation. Extracted
        # from the dasha-tree's third level (subDashas → subDashas) when
        # `currentDasha` shortcut omits it.
        "current_pd":     None,
        # Phase 4.4 — ascendant carried as a sentinel so _post_logic_check
        # can validate lagna claims without changing the function signature.
        "_lagna":         "",
    }
    if not isinstance(kundli, dict):
        return out
    # Phase 4.4 — capture ascendant. Handles both string ("Aries") and
    # dict ({"sign": "Aries"}) shapes that exist across the codebase.
    # Uses _tf_canon_sign (defined above) so Sanskrit/Hinglish kundli
    # values (Mesh/Vrishabh/etc.) canonicalize to lowercase English the
    # detector can compare against directly. Architect-followup: when
    # ascendant is a truthy dict that LACKS .sign, fall back to the
    # top-level "lagna" field rather than silently disabling validation.
    def _extract_sign(v):
        if isinstance(v, dict):
            return v.get("sign") or ""
        return v or ""
    _asc_str = _extract_sign(kundli.get("ascendant"))
    if not _asc_str:
        _asc_str = _extract_sign(kundli.get("lagna"))
    _asc_canon = _tf_canon_sign(_asc_str) if _asc_str else ""
    if _asc_canon:
        out["_lagna"] = _asc_canon

    # Planet → house / sign / retrograde maps. Architect-required: canonicalize
    # via _norm_planet_lc so non-canonical kundli labels (e.g. "Surya",
    # "Shani") map to the same keys the regex matchers will produce.
    planets = kundli.get("planets") or []
    _planet_iter = []
    if isinstance(planets, list):
        for p in planets:
            if isinstance(p, dict):
                _planet_iter.append(
                    (_norm_planet_lc(p.get("name") or ""), p)
                )
    elif isinstance(planets, dict):
        for k, v in planets.items():
            if isinstance(v, dict):
                _planet_iter.append((_norm_planet_lc(k or ""), v))

    for nm, p in _planet_iter:
        if not nm:
            continue
        h = p.get("house")
        if isinstance(h, int) and 1 <= h <= 12:
            out["planet_house"][nm] = h
        sg = _tf_canon_sign(p.get("sign"))
        if sg:
            out["planet_sign"][nm] = sg
        # retrograde: skip Rahu/Ketu (always retrograde by convention; chart
        # data may or may not flag them — validating them yields noise).
        if nm not in ("rahu", "ketu"):
            r = p.get("retrograde")
            if r is True:
                out["retrograde"].add(nm)
        # Phase 4.3 — per-planet nakshatra + pada (engine may emit either).
        nak_canon = _norm_nakshatra(p.get("nakshatra"))
        if nak_canon:
            out["nakshatra"][nm] = nak_canon
        pada_raw = p.get("nakshatraPada") or p.get("pada")
        try:
            pada_int = int(pada_raw) if pada_raw is not None else None
        except (TypeError, ValueError):
            pada_int = None
        if isinstance(pada_int, int) and 1 <= pada_int <= 4:
            out["nakshatra_pada"][nm] = pada_int

    # Phase 4.3 — Moon nakshatra + pada from top-level kundli fields. This is
    # the user's birth nakshatra ("janm nakshatra"). Engine emits these even
    # when planets[].nakshatra is absent for Moon, so always check both.
    moon_nak = _norm_nakshatra(kundli.get("nakshatra"))
    if moon_nak and "moon" not in out["nakshatra"]:
        out["nakshatra"]["moon"] = moon_nak
    moon_pada_raw = kundli.get("nakshatraPada")
    try:
        moon_pada = int(moon_pada_raw) if moon_pada_raw is not None else None
    except (TypeError, ValueError):
        moon_pada = None
    if isinstance(moon_pada, int) and 1 <= moon_pada <= 4 and \
            "moon" not in out["nakshatra_pada"]:
        out["nakshatra_pada"]["moon"] = moon_pada

    # House lord map via lagna + whole-sign sign-ruler chain.
    asc = kundli.get("ascendant") or kundli.get("lagna") or {}
    asc_sign_raw = asc.get("sign") if isinstance(asc, dict) else asc
    asc_sign = _tf_canon_sign(asc_sign_raw)
    asc_idx = _TF_SIGN_INDEX_LC.get(asc_sign)
    if asc_idx is not None:
        for hi in range(1, 13):
            sign_at = _TF_SIGNS_LC[(asc_idx + hi - 1) % 12]
            ruler = _TF_SIGN_RULER_LC.get(sign_at)
            if ruler:
                out["house_lord"][hi] = ruler

    # Manglik (from-lagna rule): Mars in 1, 2, 4, 7, 8, or 12 from lagna.
    # Conservative MVP — only this one rule (not Moon/Venus variants).
    mars_h = out["planet_house"].get("mars")
    if isinstance(mars_h, int) and 1 <= mars_h <= 12:
        out["manglik"] = mars_h in (1, 2, 4, 7, 8, 12)

    # Current MD/AD — try precomputed first, fall back to dasha-tree traversal
    # by today's date.
    cur = kundli.get("currentDasha") or kundli.get("currentPhase") or {}
    if isinstance(cur, dict):
        for md_key in ("mahadasha", "md", "MD", "maha"):
            md = cur.get(md_key)
            if isinstance(md, dict) and md.get("planet"):
                out["current_md"] = {
                    "planet": (md.get("planet") or "").lower(),
                    "start":  md.get("startDate") or md.get("start"),
                    "end":    md.get("endDate")   or md.get("end"),
                }
                break
        for ad_key in ("antardasha", "ad", "AD", "antar", "bhukti"):
            ad = cur.get(ad_key)
            if isinstance(ad, dict) and ad.get("planet"):
                out["current_ad"] = {
                    "planet": (ad.get("planet") or "").lower(),
                    "start":  ad.get("startDate") or ad.get("start"),
                    "end":    ad.get("endDate")   or ad.get("end"),
                }
                break

    # Always walk the dasha tree to capture PD (Phase 4.5 narrative-mode
    # combo) — the `currentDasha` shortcut typically omits Pratyantar even
    # when MD+AD are populated. We also use the same walk to backfill MD/AD
    # if the shortcut was empty (legacy behaviour).
    from datetime import datetime
    today = datetime.utcnow().strftime("%Y-%m-%d")
    dashas = kundli.get("dashas") or kundli.get("dasha") or []
    if isinstance(dashas, list):
        for md in dashas:
            if not isinstance(md, dict):
                continue
            md_s = md.get("startDate") or "9999-99-99"
            md_e = md.get("endDate")   or "0000-00-00"
            if md_s <= today <= md_e:
                if not out["current_md"]:
                    out["current_md"] = {
                        "planet": (md.get("planet") or "").lower(),
                        "start":  md.get("startDate"),
                        "end":    md.get("endDate"),
                    }
                for ad in (md.get("subDashas") or []):
                    if not isinstance(ad, dict):
                        continue
                    ad_s = ad.get("startDate") or "9999-99-99"
                    ad_e = ad.get("endDate")   or "0000-00-00"
                    if ad_s <= today <= ad_e:
                        if not out["current_ad"]:
                            out["current_ad"] = {
                                "planet": (ad.get("planet") or "").lower(),
                                "start":  ad.get("startDate"),
                                "end":    ad.get("endDate"),
                            }
                        # Phase 4.5 — walk one level deeper for PD.
                        for pd in (ad.get("subDashas") or []):
                            if not isinstance(pd, dict):
                                continue
                            pd_s = pd.get("startDate") or "9999-99-99"
                            pd_e = pd.get("endDate")   or "0000-00-00"
                            if pd_s <= today <= pd_e:
                                if not out["current_pd"]:
                                    out["current_pd"] = {
                                        "planet": (pd.get("planet") or "").lower(),
                                        "start":  pd.get("startDate"),
                                        "end":    pd.get("endDate"),
                                    }
                                break
                        break
                break

    return out


def _post_logic_check(text: str, truth: dict) -> list[dict]:
    """Returns a list of structured violations. Empty list = clean.

    Each violation is a dict with at least {kind, severity, ...detail}.
    """
    violations: list[dict] = []
    if not text or not isinstance(truth, dict):
        return violations

    # ─── DASHA CLAIMS ──────────────────────────────────────────────────────
    has_present_anchor = bool(_TRUTH_PRESENT_RX.search(text))

    if has_present_anchor:
        cur_md = (truth.get("current_md") or {}).get("planet")
        cur_ad = (truth.get("current_ad") or {}).get("planet")

        # Architect-required (Phase-3 v2): suppress claims that are NEGATED
        # in their immediate context. e.g. "Jupiter mahadasha active nahi
        # hai" must NOT count as a claim that Jupiter is current MD. We
        # look for a negation token within the next ~50 chars of the
        # match — narrow window keeps recall high for genuine claims.
        def _claimed_planets(*rxs):
            """Phase 4.3 — accept multiple regexes (e.g. forward + inverted
            syntax). Each regex must put the planet name in group(1)."""
            out = set()
            for rx in rxs:
                for m in rx.finditer(text):
                    tail = text[m.end(): m.end() + 60]
                    if _NEGATION_NEAR_RX.search(tail):
                        continue
                    out.add(_norm_planet_lc(m.group(1)))
            return out

        md_claimed = _claimed_planets(_TRUTH_MD_RX, _TRUTH_MD_INVERTED_RX)
        ad_claimed = _claimed_planets(_TRUTH_AD_RX, _TRUTH_AD_INVERTED_RX)

        if cur_md and md_claimed and cur_md not in md_claimed:
            violations.append({
                "kind":           "dasha_md_mismatch",
                "claimed":        sorted(md_claimed),
                "actual_current": cur_md,
                "severity":       "high",
            })
        if cur_ad and ad_claimed and cur_ad not in ad_claimed:
            violations.append({
                "kind":           "dasha_ad_mismatch",
                "claimed":        sorted(ad_claimed),
                "actual_current": cur_ad,
                "severity":       "high",
            })

    # ─── PLANET-HOUSE CLAIMS ───────────────────────────────────────────────
    ph = truth.get("planet_house") or {}
    seen_pairs: set = set()

    for m in _TRUTH_PLANET_HOUSE_RX.finditer(text):
        try:
            pname = _norm_planet_lc(m.group(1))
            house = int(m.group(2))
        except (TypeError, ValueError):
            continue
        if not (1 <= house <= 12):
            continue
        # Phase 4.1 — if "ka swami / lord / malik" follows the matched
        # "X Nth house" span, it's a LORD-OF-HOUSE statement, not an
        # IN-HOUSE statement. Skip; the house-lord check below handles it.
        if _TRUTH_LORDISH_TAIL_RX.match(text[m.end(): m.end() + 30]):
            continue
        actual = ph.get(pname)
        if actual is None or actual == house:
            continue
        key = ("PH", pname, house)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        violations.append({
            "kind":          "planet_house_mismatch",
            "planet":        pname,
            "claimed_house": house,
            "actual_house":  actual,
            "severity":      "high",
        })

    for m in _TRUTH_HOUSE_PLANET_RX.finditer(text):
        try:
            house = int(m.group(1))
            pname = _norm_planet_lc(m.group(2))
        except (TypeError, ValueError):
            continue
        if not (1 <= house <= 12):
            continue
        if _TRUTH_LORDISH_TAIL_RX.match(text[m.end(): m.end() + 30]):
            continue
        actual = ph.get(pname)
        if actual is None or actual == house:
            continue
        key = ("PH", pname, house)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        violations.append({
            "kind":          "planet_house_mismatch",
            "planet":        pname,
            "claimed_house": house,
            "actual_house":  actual,
            "severity":      "high",
        })

    # ─── PHASE 4.1 — HOUSE-LORD CLAIMS ─────────────────────────────────────
    hl = truth.get("house_lord") or {}
    seen_lord: set = set()

    def _check_house_lord(house_num: int, pname: str):
        if not (1 <= house_num <= 12):
            return
        actual = hl.get(house_num)
        if not actual or actual == pname:
            return
        key = ("HL", house_num, pname)
        if key in seen_lord:
            return
        seen_lord.add(key)
        violations.append({
            "kind":           "house_lord_mismatch",
            "house":          house_num,
            "claimed_lord":   pname,
            "actual_lord":    actual,
            "severity":       "high",
        })

    for m in _TRUTH_HOUSE_LORD_RX.finditer(text):
        try:
            h = int(m.group(1)); pn = _norm_planet_lc(m.group(2))
        except (TypeError, ValueError):
            continue
        # clause-bounded negation guard: "Nth house ka swami X nahi hai"
        if _tf_negated_after(text, m.end()):
            continue
        _check_house_lord(h, pn)

    for m in _TRUTH_LORD_HOUSE_RX.finditer(text):
        try:
            pn = _norm_planet_lc(m.group(1)); h = int(m.group(2))
        except (TypeError, ValueError):
            continue
        if _tf_negated_after(text, m.end()):
            continue
        _check_house_lord(h, pn)

    # ─── PHASE 4.1 — PLANET-SIGN CLAIMS ────────────────────────────────────
    ps = truth.get("planet_sign") or {}
    seen_sign: set = set()

    def _check_planet_sign(pname: str, sign_lc: str):
        if not pname or not sign_lc:
            return
        actual = ps.get(pname)
        if not actual or actual == sign_lc:
            return
        key = ("PS", pname, sign_lc)
        if key in seen_sign:
            return
        seen_sign.add(key)
        violations.append({
            "kind":           "planet_sign_mismatch",
            "planet":         pname,
            "claimed_sign":   sign_lc,
            "actual_sign":    actual,
            "severity":       "high",
        })

    for rx in (_TRUTH_PLANET_SIGN_RX_A, _TRUTH_PLANET_SIGN_RX_B):
        for m in rx.finditer(text):
            if _tf_negated_after(text, m.end()):
                continue
            pn = _norm_planet_lc(m.group(1))
            sg = _tf_canon_sign(m.group(2))
            _check_planet_sign(pn, sg)

    # ─── PHASE 4.1 — RETROGRADE CLAIMS ─────────────────────────────────────
    # Polarity-aware: "Saturn retrograde hai" (no negation) asserts retro=True;
    # "Saturn retrograde nahi hai" asserts retro=False.
    retro_set = truth.get("retrograde") or set()
    ph_known = truth.get("planet_house") or {}
    seen_retro: set = set()
    for m in _TRUTH_RETROGRADE_RX.finditer(text):
        pn = _norm_planet_lc(m.group(1))
        if not pn or pn in ("rahu", "ketu"):
            continue
        if pn not in ph_known:
            # planet not in our chart at all — can't validate
            continue
        is_negated = _tf_negated_after(text, m.end())
        claimed = not is_negated
        actual = pn in retro_set
        if claimed == actual:
            continue
        key = ("RG", pn, claimed)
        if key in seen_retro:
            continue
        seen_retro.add(key)
        violations.append({
            "kind":      "retrograde_mismatch",
            "planet":    pn,
            "claimed":   claimed,
            "actual":    actual,
            "severity":  "high",
        })

    # ─── PHASE 4.1 — MANGLIK CLAIMS ────────────────────────────────────────
    # Polarity-aware: emit on the FIRST mismatched assertion in the
    # response. Architect-required fix: an early truthy assertion (e.g.
    # "Aap manglik hain") must NOT short-circuit the scan — a later
    # contradictory clause ("…lekin actually nahi hain") would otherwise
    # be missed. We continue iterating past truthy matches and only emit
    # (and break) on the first observed mismatch.
    actual_manglik = truth.get("manglik")
    if isinstance(actual_manglik, bool):
        for m in _TRUTH_MANGLIK_RX.finditer(text):
            # Hinglish: "manglik nahi hai" — negation is always after
            # the noun. Clause-bounded so unrelated downstream negations
            # ("manglik hai. lekin yoga nahi") don't flip polarity.
            is_negated = _tf_negated_after(text, m.end())
            claimed = not is_negated
            if claimed == actual_manglik:
                continue  # this clause matches truth — keep scanning
            violations.append({
                "kind":      "manglik_mismatch",
                "claimed":   claimed,
                "actual":    actual_manglik,
                "severity":  "high",
            })
            break  # first mismatch is sufficient (one violation per response)

    # ─── PHASE 4.3 — NAKSHATRA CLAIMS ──────────────────────────────────────
    # AI invents janm-nakshatra freely. Three claim shapes:
    #   1. "aapka nakshatra Bharani hai"  → subject = MOON (user)
    #   2. "Moon's nakshatra is Bharani" / "Chandra ka nakshatra Bharani"
    #        → subject = explicit planet
    #   3. "nakshatra Bharani hai"  → bare, defaults to MOON
    nak_truth = truth.get("nakshatra") or {}
    seen_nak: set = set()

    def _check_nakshatra(planet_lc: str, claimed_nak: str):
        if not planet_lc or not claimed_nak:
            return
        actual = nak_truth.get(planet_lc)
        if not actual or actual == claimed_nak:
            return
        key = ("NK", planet_lc, claimed_nak)
        if key in seen_nak:
            return
        seen_nak.add(key)
        violations.append({
            "kind":              "nakshatra_mismatch",
            "planet":            planet_lc,
            "claimed_nakshatra": claimed_nak,
            "actual_nakshatra":  actual,
            "severity":          "high",
        })

    # Form 1 — possessive ("aapka/your nakshatra <NAK>") → Moon
    for m in _TRUTH_NAKSHATRA_USER_RX.finditer(text):
        if _tf_negated_after(text, m.end()):
            continue
        nak = _norm_nakshatra(m.group(1))
        _check_nakshatra("moon", nak)

    # Form 2 — explicit planet ("<planet>'s/ka nakshatra <NAK>"). Track
    # spans so the bare-form (Form 3) below can skip overlapping matches
    # — otherwise "Saturn ka nakshatra Chitra hai" would also fire Form 3
    # and falsely accuse the Moon nakshatra.
    form2_spans: list[tuple[int, int]] = []
    for m in _TRUTH_NAKSHATRA_PLANET_RX.finditer(text):
        form2_spans.append((m.start(), m.end()))
        if _tf_negated_after(text, m.end()):
            continue
        pn = _norm_planet_lc(m.group(1))
        # Hinglish "Chandra" maps to "moon" via _PL_SYNONYMS; trust _norm.
        nak = _norm_nakshatra(m.group(2))
        _check_nakshatra(pn, nak)

    # Form 3 — bare ("nakshatra <NAK> hai") → defaults to Moon. Skip if
    # the match falls inside a Form 2 span (already attributed to a planet).
    for m in _TRUTH_NAKSHATRA_BARE_RX.finditer(text):
        # Form 3's match starts at the "nakshatra" token; if Form 2 already
        # covers that token (planet+possessive+nakshatra...), skip.
        if any(s <= m.start() < e for s, e in form2_spans):
            continue
        if _tf_negated_after(text, m.end()):
            continue
        nak = _norm_nakshatra(m.group(1))
        _check_nakshatra("moon", nak)

    # ─── PHASE 4.3 — NAKSHATRA PADA CLAIMS ─────────────────────────────────
    # Pada is always tied to a nakshatra; in birth-chart context the default
    # subject is Moon (janm-nakshatra pada). But "Saturn ka pada 3 hai" or
    # "Rahu pada 1 mein" mention pada of OTHER planets — those must NOT be
    # validated against Moon's pada (would yield high-severity false-pos).
    #
    # Architect Phase-4.3-review fix: only fire when the pada claim is
    # anchored to Moon-context. We require either:
    #   (a) a Moon-context anchor (aapka/your/tumhara/janm/moon/chandra/
    #       nakshatra) within ~40 chars BEFORE the pada token, AND
    #   (b) NO non-Moon planet name in the prior ~25 chars (which would
    #       indicate a planet-specific pada claim we cannot validate yet).
    pada_truth = truth.get("nakshatra_pada") or {}
    actual_moon_pada = pada_truth.get("moon")
    if isinstance(actual_moon_pada, int):
        seen_pada: set = set()
        import re as _re_pada
        _MOON_PADA_ANCHOR_RX = _re_pada.compile(
            r"\b(aap?ka|aap?ki|tumhara|tumhari|your|mera|meri|mer[ae]|"
            r"janm|moon|chandra|chandr|nakshatra)\b",
            _re_pada.IGNORECASE,
        )
        # Other planets (anything except moon/chandra). Used to disqualify
        # the claim when, e.g., "Saturn ka pada 3" appears.
        _OTHER_PLANET_RX = _re_pada.compile(
            r"\b(sun|surya|ravi|mars|mangal|kuja|mercury|budh|budha|"
            r"jupiter|brihaspati|guru|venus|shukra|sukra|saturn|shani|"
            r"sani|rahu|ketu)\b",
            _re_pada.IGNORECASE,
        )

        def _check_pada(claimed: int, mstart: int, mend: int):
            if not (1 <= claimed <= 4) or claimed == actual_moon_pada:
                return
            if claimed in seen_pada:
                return
            # Disqualify FIRST if a non-Moon planet appears in the lookbehind
            # window — that's a planet-specific claim we cannot validate
            # against Moon's pada. Architect Phase-4.3 re-review: widen veto
            # window from 25 → 40 chars to match anchor-window symmetry.
            # Catches multi-clause cases like "Saturn ka nakshatra Chitra
            # mein aapka 1st pada hai" (Saturn appears 38 chars before pada
            # token — beyond old 25-char window).
            veto_start = max(0, mstart - 40)
            veto_window = text[veto_start:mstart]
            if _OTHER_PLANET_RX.search(veto_window):
                return
            # Moon-context anchor must appear within ±40 chars of the pada
            # match. Allowing trailing anchor too ("Pada 4 hai aapka") so we
            # don't miss Hinglish word-order variants where the possessive
            # follows the pada noun.
            lookbehind_start = max(0, mstart - 40)
            lookahead_end = min(len(text), mend + 40)
            window = text[lookbehind_start:mstart] + text[mend:lookahead_end]
            if not _MOON_PADA_ANCHOR_RX.search(window):
                return  # no Moon-context — can't safely attribute to Moon
            seen_pada.add(claimed)
            violations.append({
                "kind":         "nakshatra_pada_mismatch",
                "planet":       "moon",
                "claimed_pada": claimed,
                "actual_pada":  actual_moon_pada,
                "severity":     "high",
            })

        for rx in (_TRUTH_PADA_RX, _TRUTH_PADA_ORDINAL_RX):
            for m in rx.finditer(text):
                if _tf_negated_after(text, m.end()):
                    continue
                try:
                    pd = int(m.group(1))
                except (TypeError, ValueError):
                    continue
                _check_pada(pd, m.start(), m.end())

    # ─── PHASE 4.4 — LAGNA / ASCENDANT CLAIMS (lookup_engine extension) ────
    # Off-by-default-disable via env (LOOKUP_ENGINE=0). On by default.
    _lookup_engine_enabled = (
        os.environ.get("LOOKUP_ENGINE", "1") != "0"
    )
    if _lookup_engine_enabled:
        # Resolve actual ascendant — kundli passes through truth via the
        # caller; truth itself doesn't store it, so we accept it from a
        # back-channel the caller stuffs in (`_truth_ascendant`) OR fall
        # back to the legacy field used elsewhere. _build_truth_facts
        # callers always have kundli in scope — to keep this function's
        # signature unchanged, we read the ascendant from a sentinel key
        # we attach in _build_truth_facts going forward.
        asc_raw = ((truth.get("_lagna") or "")
                   if isinstance(truth, dict) else "")
        if isinstance(asc_raw, str) and asc_raw.strip():
            asc_canon = _SIGN_VARIANT_LC.get(
                asc_raw.strip().lower(), asc_raw.strip().lower()
            )
            for rx in (_TRUTH_LAGNA_FWD_RX, _TRUTH_LAGNA_INV_RX):
                _seen_lagna = False
                for m in rx.finditer(text):
                    if _seen_lagna:
                        break
                    tail = text[m.end(): m.end() + 60]
                    if _NEGATION_NEAR_RX.search(tail):
                        continue
                    claimed_raw = (m.group(1) or "").lower()
                    claimed_canon = _SIGN_VARIANT_LC.get(
                        claimed_raw, claimed_raw)
                    if claimed_canon and claimed_canon != asc_canon:
                        violations.append({
                            "kind":          "lagna_mismatch",
                            "claimed_lagna": claimed_canon,
                            "actual_lagna":  asc_canon,
                            "severity":      "high",
                        })
                        _seen_lagna = True

        # ─── PHASE 4.4 — DASHA END-YEAR CLAIMS (lookup_engine extension) ───
        cur_md = (truth.get("current_md") or {}) if isinstance(truth, dict) else {}
        md_planet = (cur_md.get("planet") or "").lower() if cur_md else ""
        md_end = cur_md.get("end") if cur_md else None
        md_end_year: int | None = None
        if isinstance(md_end, str) and len(md_end) >= 4:
            try:
                md_end_year = int(md_end[:4])
            except (TypeError, ValueError):
                md_end_year = None
        if md_planet and md_end_year:
            _seen_end_year = False
            for rx in (_TRUTH_DASHA_END_FWD_RX,
                       _TRUTH_DASHA_END_INV_RX,
                       _TRUTH_DASHA_END_EN_RX):
                if _seen_end_year:
                    break
                for m in rx.finditer(text):
                    if _seen_end_year:
                        break
                    tail = text[m.end(): m.end() + 60]
                    if _NEGATION_NEAR_RX.search(tail):
                        continue
                    claimed_planet = _norm_planet_lc(m.group(1) or "")
                    # Only fire when AI is talking about the CURRENT MD's
                    # end year — if the named planet is some OTHER MD
                    # (past or future), the year may be legitimately
                    # different and we must not false-fire.
                    if claimed_planet != md_planet:
                        continue
                    try:
                        claimed_year = int(m.group(2))
                    except (TypeError, ValueError):
                        continue
                    # ±1-year slack — dashas straddle calendar years and
                    # ayanamsa choice can shift end-dates by months.
                    if abs(claimed_year - md_end_year) > 1:
                        violations.append({
                            "kind":         "dasha_end_year_mismatch",
                            "claimed_year": claimed_year,
                            "actual_year":  md_end_year,
                            "actual_md":    md_planet.title(),
                            "severity":     "high",
                        })
                        _seen_end_year = True

    return violations


def _post_logic_correction_msg(violations: list[dict], truth: dict) -> str:
    """Build the corrective system message for the POST_LOGIC retry."""
    lines = [
        "⚠️ FACTUAL CORRECTION REQUIRED — your previous answer named WRONG "
        "chart facts. Regenerate using ONLY these correct values. Keep the "
        "same topic, tone, and length — just fix the facts:",
    ]
    for v in violations:
        if v["kind"] == "dasha_md_mismatch":
            md = truth.get("current_md") or {}
            lines.append(
                f"  • CURRENT Mahadasha is "
                f"{(md.get('planet') or '?').title()} "
                f"({md.get('start','?')} → {md.get('end','?')}). You named "
                f"{', '.join(p.title() for p in v['claimed'])} as current. FIX IT."
            )
        elif v["kind"] == "dasha_ad_mismatch":
            ad = truth.get("current_ad") or {}
            lines.append(
                f"  • CURRENT Antardasha is "
                f"{(ad.get('planet') or '?').title()} "
                f"({ad.get('start','?')} → {ad.get('end','?')}). You named "
                f"{', '.join(p.title() for p in v['claimed'])} as current. FIX IT."
            )
        elif v["kind"] == "planet_house_mismatch":
            lines.append(
                f"  • {v['planet'].title()} is in house "
                f"{v['actual_house']}, NOT house {v['claimed_house']}. FIX IT."
            )
        elif v["kind"] == "house_lord_mismatch":
            lines.append(
                f"  • {v['house']}th house ka swami (lord) is "
                f"{v['actual_lord'].title()}, NOT {v['claimed_lord'].title()}. "
                f"FIX IT."
            )
        elif v["kind"] == "planet_sign_mismatch":
            lines.append(
                f"  • {v['planet'].title()} is in sign "
                f"{v['actual_sign'].title()}, NOT {v['claimed_sign'].title()}. "
                f"FIX IT."
            )
        elif v["kind"] == "retrograde_mismatch":
            state = "retrograde" if v["actual"] else "NOT retrograde"
            lines.append(
                f"  • {v['planet'].title()} is {state} in this chart. "
                f"FIX IT."
            )
        elif v["kind"] == "manglik_mismatch":
            verdict = "manglik" if v["actual"] else "NOT manglik"
            lines.append(
                f"  • Per Mars-from-lagna rule, the user is {verdict}. "
                f"FIX IT."
            )
        elif v["kind"] == "lagna_mismatch":
            lines.append(
                f"  • Aapki Lagna (Ascendant) is "
                f"{v['actual_lagna'].title()}, NOT "
                f"{v['claimed_lagna'].title()}. FIX IT."
            )
        elif v["kind"] == "dasha_end_year_mismatch":
            lines.append(
                f"  • {v['actual_md']} Mahadasha (current) ends in "
                f"{v['actual_year']}, NOT {v['claimed_year']}. FIX IT."
            )
    lines.append(
        "Do NOT add new claims, do NOT change topic. Only correct the "
        "factual mistakes above."
    )
    return "\n".join(lines)


def _build_supertype_contract(supertype: str,
                              *,
                              has_recovery_subask: bool = False) -> str:
    """Public entry point — preserved for the install site at line 6670.
    Now a thin shim over `_build_unified_narrator_contract`. The
    `has_recovery_subask` kwarg is forwarded so consumers (the install
    site) can pass `question_intent['has_recovery_subask']` through
    without any further wiring."""
    return _build_unified_narrator_contract(
        supertype, has_recovery_subask=has_recovery_subask
    )


_ASK_DEBUG = os.environ.get("ASK_DEBUG", "1") not in ("0", "false", "False", "")


def _short_id() -> str:
    import uuid
    return uuid.uuid4().hex[:8]


def _trace(req_id: str, step: str, info: Any) -> None:
    """Unified per-request debug trace. Set env ASK_DEBUG=0 to silence."""
    if not _ASK_DEBUG:
        return
    try:
        if isinstance(info, str):
            body = info
        else:
            import json as _json
            body = _json.dumps(info, ensure_ascii=False, default=str)
    except Exception:
        body = repr(info)
    if len(body) > 1200:
        body = body[:1200] + f"...(+{len(body)-1200} chars)"
    print(f"[ask:{req_id}] {step}: {body}", flush=True)


# ── Fix-D: SUPERTYPE CONTRACT VALIDATOR + 1-RETRY ───────────────────────────
# Detects hard violations of the per-supertype contract injected at the LAST
# system message (Sprint-24). When a violation is detected and retry budget
# remains, we re-call the model ONCE with explicit corrective feedback.
#
# Returns a list of human-readable violation strings — empty list = clean.
import re as _re_validator
_DASHA_MENTION_RX = _re_validator.compile(
    r"\b(dasha|mahadasha|antardasha|antar\s*dasha|maha\s*dasha|"
    r"pratyantar|sookshma|vimshottari)\b|दशा|महादशा|अन्तर्दशा",
    _re_validator.IGNORECASE,
)
_FUTURE_TIMING_RX = _re_validator.compile(
    r"\b(?:20\d{2}|19\d{2})\b|"
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
    r"(?:uary|ruary|ch|il|ne|ly|ust|tember|ober|ember)?\b|"
    r"\b(?:kab|when|next|after|baad|jaldi|soon|upcoming|coming|"
    r"aane\s*wala|aayega|aayegi|hoga|hogi)\b",
    _re_validator.IGNORECASE,
)
_ADVICE_RX = _re_validator.compile(
    r"\b(upay|remedy|jaap|mantra|donate|daan|wear|pehnen|chadhayen|"
    r"chadhaiye|bhog|fast|vrat|puja|पूजा|उपाय|जाप)\b|"
    r"\b(?:should|chahiye|karein|kariye|do this|kar lo|kar lijiye)\b",
    _re_validator.IGNORECASE,
)
_HOUSE_MENTION_RX = _re_validator.compile(
    r"\b(?:1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|12th)\b|"
    r"\b(?:bhava|bhav|house|भाव)\b|"
    r"\b(?:lagna|lord)\b",
    _re_validator.IGNORECASE,
)
_DECISION_OPENER_RX = _re_validator.compile(
    r"^\s*[*_>•\-\"'`(]*\s*"  # markdown / quote leaders
    r"(?:haan|haa|han|naa|na|nahi|nahin|ruko|ruk\s*jao|wait|"
    r"yes|no|hold|abhi\s*nahi|abhi\s*na|kar\s*lo|mat\s*karo|"
    r"sahi\s*hai|theek\s*hai|achha\s*hai|jaayiye|chalega|"
    r"go\s*ahead|don'?t)\b",
    _re_validator.IGNORECASE,
)

# Sprint-25 Fix-H: planet & house counters used by GENERAL_ANALYSIS validator.
# Each tuple = canonical English name → regex of accepted spellings (Vedic +
# English + Devanagari). One *match* per planet contributes 1 to the distinct
# count regardless of how many times the planet is named.
_PLANET_PATTERNS: tuple[tuple[str, str], ...] = (
    ("sun",     r"\b(?:sun|surya|soorya|ravi)\b|सूर्य|रवि"),
    ("moon",    r"\b(?:moon|chandra|chandr|chand)\b|चंद्र|चन्द्र"),
    ("mars",    r"\b(?:mars|mangal|mangala|kuja|bhauma)\b|मंगल"),
    ("mercury", r"\b(?:mercury|budh|budha|budhh)\b|बुध"),
    ("jupiter", r"\b(?:jupiter|guru|brihaspati|brihaspat|jeev|jeeva)\b|गुरु|बृहस्पति"),
    ("venus",   r"\b(?:venus|shukra|shukr|sukra)\b|शुक्र"),
    ("saturn",  r"\b(?:saturn|shani|shanaishchara|shanaishchar)\b|शनि"),
    ("rahu",    r"\b(?:rahu)\b|राहु"),
    ("ketu",    r"\b(?:ketu)\b|केतु"),
)
_PLANET_RX_COMPILED: tuple[tuple[str, "_re_validator.Pattern"], ...] = tuple(
    (name, _re_validator.compile(pat, _re_validator.IGNORECASE))
    for name, pat in _PLANET_PATTERNS
)

# Distinct house tokens. We bucket by ordinal so "1st" and "lagna" both
# count toward house #1 (no double-credit). "house" / "bhava" alone (no
# ordinal) is NOT counted — too ambiguous.
_HOUSE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("1",  r"\b(?:1st|first|prathama|pratham|lagna|ascendant)\b"),
    ("2",  r"\b(?:2nd|second|dwitiya|dvitiya|dhana)\b"),
    ("3",  r"\b(?:3rd|third|tritiya|sahaja)\b"),
    ("4",  r"\b(?:4th|fourth|chaturth|chaturtha|sukha)\b"),
    ("5",  r"\b(?:5th|fifth|panchama|pancham|putra)\b"),
    ("6",  r"\b(?:6th|sixth|shashtha|shashta|ari|ripu)\b"),
    ("7",  r"\b(?:7th|seventh|saptama|saptam|kalatra|yuvati)\b"),
    ("8",  r"\b(?:8th|eighth|ashtama|ashtam|randhra|ayu)\b"),
    ("9",  r"\b(?:9th|ninth|navama|navam|dharma|bhagya)\b"),
    ("10", r"\b(?:10th|tenth|dasama|dasam|karma|rajya)\b"),
    ("11", r"\b(?:11th|eleventh|labha|aaya)\b"),
    ("12", r"\b(?:12th|twelfth|dvadasha|dvadasa|vyaya|moksha)\b"),
)
_HOUSE_RX_COMPILED: tuple[tuple[str, "_re_validator.Pattern"], ...] = tuple(
    (num, _re_validator.compile(pat, _re_validator.IGNORECASE))
    for num, pat in _HOUSE_PATTERNS
)

# ── Sprint-25 Fix-J: STRENGTH_SUMMARY detector ──────────────────────────────
# Triggers when the user asks "which planets are strong / weak / powerful /
# vargottam in my chart" — Hinglish + English. We bind a strength keyword to
# a planet/grah keyword within ~30 chars in either order so generic mentions
# of "strong" don't false-fire.
_STRENGTH_KEYWORDS = (
    r"strong|weak|powerful|kamzor|kamjor|kamjore|kamzore|"
    r"shaktishaali|shaktishali|balwaan|balwan|balavan|"
    r"achch?h?e|achch?h?a|kharab|bekaar|bekar|"
    r"vargottam|vargottama"
)
_PLANET_KEYWORDS = r"planet|planets|grah|graha|grahon|grahaon|grahas"
_STRENGTH_SUMMARY_RX = _re_validator.compile(
    rf"\b(?:{_STRENGTH_KEYWORDS})\b[^\n]{{0,30}}\b(?:{_PLANET_KEYWORDS})\b"
    rf"|"
    rf"\b(?:{_PLANET_KEYWORDS})\b[^\n]{{0,30}}\b(?:{_STRENGTH_KEYWORDS})\b",
    _re_validator.IGNORECASE,
)


def _is_strength_summary_question(question: str) -> bool:
    if not question:
        return False
    return bool(_STRENGTH_SUMMARY_RX.search(question))


# Vargottam-claim parser: catches "Moon vargottam hai" / "vargottama Moon" etc.
# Used by the STRENGTH_SUMMARY validator to enforce that any planet labelled
# vargottam is in the precomputed list.
_VARGOTTAM_NEAR_PLANET_RX = _re_validator.compile(
    rf"(?:vargottam|vargottama)\b[^\n]{{0,40}}?\b({_PLANET_KEYWORDS}|"
    rf"sun|surya|moon|chandra|mars|mangal|mercury|budh|jupiter|guru|"
    rf"venus|shukra|saturn|shani|rahu|ketu)\b"
    rf"|"
    rf"\b(sun|surya|moon|chandra|mars|mangal|mercury|budh|jupiter|guru|"
    rf"venus|shukra|saturn|shani|rahu|ketu)\b[^\n]{{0,40}}?(?:vargottam|vargottama)\b",
    _re_validator.IGNORECASE,
)


def _count_distinct_planets(text: str) -> int:
    """Number of DISTINCT planets named in the text (max 9)."""
    if not text:
        return 0
    return sum(1 for _name, rx in _PLANET_RX_COMPILED if rx.search(text))


def _count_distinct_houses(text: str) -> int:
    """Number of DISTINCT houses named in the text (max 12)."""
    if not text:
        return 0
    return sum(1 for _num, rx in _HOUSE_RX_COMPILED if rx.search(text))


def _validate_supertype_contract(text: str, supertype: str,
                                 kundli: Any = None) -> list[str]:
    """Hard-violation check against the strict per-supertype response contract.

    Returns a list of violation strings. Empty list = answer is contract-clean.
    Soft style issues are NOT flagged here — only the rules that are spelled
    out as "MUST" / "MUST NOT" in `_SUPERTYPE_CONTRACT_BLOCKS`.

    Phase 4.5 (Apr 28, 2026) — NARRATIVE_MODE bypass:
    The per-supertype contracts encode the V→R→T template (e.g.
    PLANET_QUERY forbids dasha mentions, GENERAL_ANALYSIS requires
    "Verdict / Reason / Timing" sections, etc.). Narrative mode runs a
    UNIFIED narrative contract instead, so the per-supertype FORMAT
    checks would fire false-positives on intentionally-different output.
    Fact correctness is still enforced by `_post_logic_check` (Phase 4.1)
    and `_lookup_engine` detectors (Phase 4.4) which sit downstream.
    """
    if _NARRATIVE_MODE:
        return []
    if not text or not supertype:
        return []
    t = text.strip()
    violations: list[str] = []

    if supertype == "PLANET_QUERY":
        # MUST NOT mention dasha
        if _DASHA_MENTION_RX.search(t):
            violations.append(
                "PLANET_QUERY: response mentioned dasha/antardasha — "
                "contract forbids any planetary period reference."
            )
        # MUST NOT predict future / timing
        if _FUTURE_TIMING_RX.search(t):
            violations.append(
                "PLANET_QUERY: response contained future/timing tokens — "
                "contract forbids any timing prediction."
            )
        # MUST NOT give advice / remedy
        if _ADVICE_RX.search(t):
            violations.append(
                "PLANET_QUERY: response contained advice / remedy / upay — "
                "contract forbids 'kya karein' style guidance."
            )

    elif supertype == "PROBLEM_QUERY":
        # MUST cite dasha
        if not _DASHA_MENTION_RX.search(t):
            violations.append(
                "PROBLEM_QUERY: response missing dasha citation — "
                "contract requires naming the running mahadasha/antardasha."
            )
        # MUST cite house / bhava
        if not _HOUSE_MENTION_RX.search(t):
            violations.append(
                "PROBLEM_QUERY: response missing house/bhava citation — "
                "contract requires naming the activated house or its lord."
            )

    elif supertype == "TIMING_QUERY":
        # MUST give a year/month/timing token
        _has_year  = bool(_re_validator.search(r"\b(19|20)\d{2}\b", t))
        _has_month = bool(_re_validator.search(
            r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
            r"(?:uary|ruary|ch|il|ne|ly|ust|tember|ober|ember)?\b",
            t, _re_validator.IGNORECASE
        ))
        _has_dasha_window = bool(_DASHA_MENTION_RX.search(t))
        if not (_has_year or _has_month or _has_dasha_window):
            violations.append(
                "TIMING_QUERY: response missing concrete WHEN — needs a year, "
                "month, or dasha-transition window."
            )

    elif supertype == "DECISION_QUERY":
        # MUST open with a clear direction marker (within first 90 chars).
        _opener_window = t[:90]
        if not _DECISION_OPENER_RX.search(_opener_window):
            violations.append(
                "DECISION_QUERY: response did not open with a clear "
                "HAAN/NAA/RUKO (YES/NO/WAIT) verdict."
            )

    elif supertype == "GENERAL_ANALYSIS":
        # Sprint-26 Fix-P: legacy "≥3 planets OR ≥3 houses" sweep requirement
        # was REMOVED. The new V→R→T contract intentionally caps at 3 planets
        # and one focal house — keeping the old check would force regenerate
        # loops back to the old dump-style answer. Replaced with structure +
        # dasha-citation checks aligned with the new contract.
        #
        # 1. Must cite a dasha (MD or AD) — REASON line requires it.
        # 2. Must include a TIMING token (year, month, or "tak"/"se" window)
        #    — TIMING line requires a single inflection date.
        # 3. Soft length advisory: log when output exceeds the relaxed cap
        #    (~150 words) but do NOT regenerate; the prompt itself nudges the
        #    AI toward 4-6 lines and over-runs are recoverable noise, not
        #    contract breaks.
        if not _DASHA_MENTION_RX.search(t):
            violations.append(
                "GENERAL_ANALYSIS: response missing dasha citation — "
                "V→R→T contract requires the REASON line to name the "
                "running mahadasha or antardasha."
            )
        _has_year_ga = bool(_re_validator.search(r"\b(19|20)\d{2}\b", t))
        _has_window_ga = bool(_re_validator.search(
            r"\b(tak|se|until|after|before|baad|pehle)\b",
            t, _re_validator.IGNORECASE
        ))
        if not (_has_year_ga or _has_window_ga):
            violations.append(
                "GENERAL_ANALYSIS: response missing timing inflection — "
                "V→R→T contract requires the TIMING line to name a year "
                "or window marker (tak/se/baad)."
            )

    elif supertype == "STRENGTH_SUMMARY":
        # Sprint-25 Fix-J — three checks:
        #   1. Length: must be ≤ 60 words (1–2 lines).
        #   2. Vargottam: any planet labelled vargottam MUST be in the
        #      precomputed vargottam list.
        #   3. Strong/weak buckets: planets named on the "strong" line MUST
        #      be in the STRONG bucket; planets on the "weak" line MUST be
        #      in the WEAK bucket. Cross-bucket bleed = violation.
        # Length check
        _wc = len(t.split())
        if _wc > 60:
            violations.append(
                f"STRENGTH_SUMMARY: answer is {_wc} words — contract requires "
                "1–2 short lines (≤60 words)."
            )

        # Pull deterministic facts (cheap — cached on kundli)
        _facts = {}
        if kundli is not None:
            try:
                from locked_facts import compute_strength_facts  # type: ignore
                _facts = compute_strength_facts(kundli) or {}
            except Exception:
                _facts = {}

        _vargottam_set = {p.lower() for p in (_facts.get("vargottam") or [])}
        _strong_set    = {p.lower() for p in (_facts.get("strong")    or [])}
        _weak_set      = {p.lower() for p in (_facts.get("weak")      or [])}
        _moderate_set  = {p.lower() for p in (_facts.get("moderate")  or [])}

        # Map any spelling → canonical planet name (lowercase)
        _SPELL_TO_CANON = {
            "sun":"sun","surya":"sun","soorya":"sun","ravi":"sun",
            "moon":"moon","chandra":"moon","chand":"moon","chandr":"moon",
            "mars":"mars","mangal":"mars","mangala":"mars","kuja":"mars",
            "mercury":"mercury","budh":"mercury","budha":"mercury",
            "jupiter":"jupiter","guru":"jupiter","brihaspati":"jupiter",
            "venus":"venus","shukra":"venus","sukra":"venus",
            "saturn":"saturn","shani":"saturn",
            "rahu":"rahu","ketu":"ketu",
        }

        def _canon(name: str) -> str:
            return _SPELL_TO_CANON.get((name or "").lower().strip(), "")

        # 2. Vargottam claim check (only when facts are available)
        if _facts:
            for m in _VARGOTTAM_NEAR_PLANET_RX.finditer(t):
                # group(1) = planet word in first alternative
                # group(2) = planet word in second alternative
                _word = (m.group(1) or m.group(2) or "").lower()
                _can = _canon(_word)
                if not _can:
                    continue  # not a real planet (e.g. "planets" generic)
                if _can not in _vargottam_set:
                    violations.append(
                        f"STRENGTH_SUMMARY: claimed '{_can.title()} vargottam' "
                        f"but vargottam list is "
                        f"{sorted(p.title() for p in _vargottam_set) or '(none)'}."
                    )

        # 3. Strong / weak bucket integrity
        if _facts and (_strong_set or _weak_set or _moderate_set):
            # Find lines containing strong / weak labels and extract planet
            # tokens from each.
            _line_rx = _re_validator.compile(
                r"\b(strong|powerful|shaktishaali|shaktishali|balwan|"
                r"weak|kamzor|kamjor|kamjore|kamzore|bekaar|bekar)\b"
                r"[^\.\n]*",
                _re_validator.IGNORECASE,
            )
            for seg in _line_rx.finditer(t):
                seg_text = seg.group(0)
                kind = (seg.group(1) or "").lower()
                is_strong_seg = kind in {
                    "strong","powerful","shaktishaali","shaktishali","balwan"
                }
                is_weak_seg = kind in {
                    "weak","kamzor","kamjor","kamjore","kamzore","bekaar","bekar"
                }
                if not (is_strong_seg or is_weak_seg):
                    continue
                # Extract planet names in this segment
                claimed: list[str] = []
                for _name, _rx in _PLANET_RX_COMPILED:
                    if _rx.search(seg_text):
                        claimed.append(_name)
                if not claimed:
                    continue
                if is_strong_seg:
                    bad = [c for c in claimed if c not in _strong_set]
                    if bad:
                        violations.append(
                            "STRENGTH_SUMMARY: 'strong' line names "
                            f"{[b.title() for b in bad]} but STRONG bucket is "
                            f"{sorted(p.title() for p in _strong_set) or '(none)'}."
                        )
                if is_weak_seg:
                    bad = [c for c in claimed if c not in _weak_set]
                    if bad:
                        violations.append(
                            "STRENGTH_SUMMARY: 'weak' line names "
                            f"{[b.title() for b in bad]} but WEAK bucket is "
                            f"{sorted(p.title() for p in _weak_set) or '(none)'}."
                        )

    return violations


def _retry_feedback_for(supertype: str, violations: list[str]) -> str:
    """Build the corrective system message appended on the retry round."""
    lines = "\n".join(f"  • {v}" for v in violations)
    return (
        "════════════════════════════════════════════════════════════════════\n"
        "CONTRACT VIOLATION DETECTED — REGENERATE\n"
        "════════════════════════════════════════════════════════════════════\n"
        f"Your previous answer broke the {supertype} contract on:\n"
        f"{lines}\n\n"
        "Re-read the STRICT NARRATOR CONTRACT block above. Produce a NEW "
        "answer that obeys EVERY MUST and MUST NOT rule for this question "
        "type. Do not re-explain the violation — just emit the corrected "
        "answer.\n"
        "════════════════════════════════════════════════════════════════════\n"
    )


# ── Sprint-26 Fix-M — Cross-Domain Root-Cause Helper ───────────────────────
# When the user asks a dual-domain question with an explicit "is this the
# same root cause or different" framing (cross_domain_root_cause=True),
# we compute a small deterministic block that the AI can cite to answer
# the comparison directly — without psychology guessing.
#
# Pure interpretation: which planets actually touch BOTH domain house-sets
# (by placement OR ownership) and whether the current MD/AD lord lands in
# either domain. The AI uses this block (no inference layer added here).

_SIGNS_M = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_SIGN_INDEX_M = {s: i for i, s in enumerate(_SIGNS_M)}
_SIGN_RULER_M = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn",
    "Aquarius": "Saturn", "Pisces": "Jupiter",
}
# Houses each domain primarily reads. Kept narrow on purpose — we don't
# want noise from co-located houses that aren't actually the user's ask.
_DOMAIN_HOUSES_M = {
    "finance":  [2, 11, 12],
    "career":   [6, 10],
    "marriage": [7, 8],
    "love":     [5, 7],
    "health":   [1, 6, 8],
    "general":  [1],
}


def _norm_planet_name(n: Any) -> str:
    if not n:
        return ""
    s = str(n).strip()
    # Map common Sanskrit aliases to canonical English names
    aliases = {
        "surya": "Sun", "ravi": "Sun",
        "chandra": "Moon", "soma": "Moon",
        "mangal": "Mars", "kuja": "Mars",
        "budh": "Mercury", "budha": "Mercury",
        "guru": "Jupiter", "brihaspati": "Jupiter",
        "shukra": "Venus",
        "shani": "Saturn",
    }
    return aliases.get(s.lower(), s.capitalize())


def _compute_cross_domain_facts(kundli: Any, topics: list[str]) -> dict:
    """Return {text, summary} or {text:'', summary:{}} when not applicable."""
    empty = {"text": "", "summary": {}}
    if not isinstance(kundli, dict) or not topics or len(topics) < 2:
        return empty
    planets = kundli.get("planets") or []
    if not planets:
        return empty

    # Lagna/asc sign (for whole-sign house-lord computation)
    asc = kundli.get("ascendant") or kundli.get("lagna") or {}
    asc_sign = asc.get("sign") if isinstance(asc, dict) else asc
    asc_idx = _SIGN_INDEX_M.get(str(asc_sign or "").strip().capitalize())

    # planet → placed-house
    planet_house: dict[str, int] = {}
    for p in planets:
        if not isinstance(p, dict):
            continue
        nm = _norm_planet_name(p.get("name") or p.get("planet"))
        h = p.get("house")
        try:
            h = int(h) if h is not None else None
        except (TypeError, ValueError):
            h = None
        if nm and h:
            planet_house[nm] = h

    # planet → houses-owned (whole-sign from lagna)
    planet_owns: dict[str, list[int]] = {}
    if asc_idx is not None:
        for hi in range(1, 13):
            sign_at = _SIGNS_M[(asc_idx + hi - 1) % 12]
            ruler = _SIGN_RULER_M.get(sign_at)
            if ruler:
                planet_owns.setdefault(ruler, []).append(hi)

    d1, d2 = topics[0], topics[1]
    h1 = set(_DOMAIN_HOUSES_M.get(d1, []))
    h2 = set(_DOMAIN_HOUSES_M.get(d2, []))
    if not h1 or not h2:
        return empty

    # Common planets: those whose placement OR ownership touches both sets
    common: list[dict] = []
    for pl in sorted(set(planet_house) | set(planet_owns)):
        owns = planet_owns.get(pl, [])
        ph = planet_house.get(pl)
        owns_d1 = sorted(h for h in owns if h in h1)
        owns_d2 = sorted(h for h in owns if h in h2)
        sits_d1 = ph in h1
        sits_d2 = ph in h2
        touches_d1 = bool(owns_d1) or sits_d1
        touches_d2 = bool(owns_d2) or sits_d2
        if touches_d1 and touches_d2:
            reasons = []
            if sits_d1:
                reasons.append(f"sits H{ph}({d1})")
            if sits_d2 and not sits_d1:
                reasons.append(f"sits H{ph}({d2})")
            if owns_d1:
                reasons.append(f"owns {','.join(f'H{h}' for h in owns_d1)}({d1})")
            if owns_d2:
                reasons.append(f"owns {','.join(f'H{h}' for h in owns_d2)}({d2})")
            common.append({"planet": pl, "reasons": reasons})

    # Current MD / AD lords + which domain houses they touch
    cd = kundli.get("currentDasha") or {}
    md_raw = cd.get("maha") or cd.get("mahadasha") or cd.get("md") or cd.get("planet") if isinstance(cd, dict) else None
    ad_raw = cd.get("antar") or cd.get("antardasha") or cd.get("ad") if isinstance(cd, dict) else None
    md = _norm_planet_name(md_raw)
    ad = _norm_planet_name(ad_raw)

    def _lord_touch(planet: str) -> dict:
        if not planet:
            return {}
        ph = planet_house.get(planet)
        owns = planet_owns.get(planet, [])
        touches = []
        if ph in h1 or any(h in h1 for h in owns):
            touches.append(d1)
        if ph in h2 or any(h in h2 for h in owns):
            touches.append(d2)
        return {"planet": planet, "house": ph, "owns": owns, "touches": touches}

    md_info = _lord_touch(md)
    ad_info = _lord_touch(ad)

    md_both = md_info.get("touches", []) and len(md_info.get("touches") or []) == 2
    ad_both = ad_info.get("touches", []) and len(ad_info.get("touches") or []) == 2

    if md_both or ad_both:
        verdict = "SAME_ROOT_CAUSE"
        verdict_line = (
            f"Same dasha lord affects BOTH domains → likely SAME root cause "
            f"({md if md_both else ad} = current "
            f"{'MD' if md_both else 'AD'} lord touches both)"
        )
    elif common:
        verdict = "PARTIAL_OVERLAP"
        verdict_line = (
            f"Shared planet(s) — {', '.join(c['planet'] for c in common[:3])} — "
            f"touch both domains → PARTIAL common cause (planet linkage but "
            f"not via the active dasha)"
        )
    else:
        verdict = "SEPARATE_CAUSES"
        verdict_line = (
            "No shared planet/dasha touches both domain houses → likely "
            "SEPARATE causes (each domain runs on independent karakas)"
        )

    lines = ["▸ CROSS-DOMAIN ROOT-CAUSE CHECK (engine-computed, no guessing):"]
    h1_str = ",".join(f"H{h}" for h in sorted(h1))
    h2_str = ",".join(f"H{h}" for h in sorted(h2))
    lines.append(f"   Domains tested: {d1} ({h1_str}) + {d2} ({h2_str})")
    if common:
        per = "; ".join(f"{c['planet']} ({', '.join(c['reasons'])})"
                       for c in common[:5])
        lines.append(f"   Common planets touching BOTH: {per}")
    else:
        lines.append("   Common planets touching BOTH: NONE")
    if md and md_info.get("house"):
        ti = " + ".join(md_info.get("touches") or []) or "neither domain directly"
        lines.append(f"   Current MD lord {md} sits H{md_info['house']} → touches {ti}")
    if ad and ad_info.get("house"):
        ti = " + ".join(ad_info.get("touches") or []) or "neither domain directly"
        lines.append(f"   Current AD lord {ad} sits H{ad_info['house']} → touches {ti}")
    lines.append(f"   VERDICT: {verdict_line}")

    return {
        "text": "\n".join(lines),
        "summary": {
            "domains":       [d1, d2],
            "common":        [c["planet"] for c in common],
            "md_touches":    md_info.get("touches") or [],
            "ad_touches":    ad_info.get("touches") or [],
            "verdict":       verdict,
        },
    }


# ── Phase 4.8 T019 — narrative-mode post-process truncator ────────────────
# Public for unit-testing. Idempotent: short already-disciplined replies
# (≤2 sentences, ≤280 chars, no dates/pratyantar) pass through unchanged.
_PHASE48_TIMING_KEYWORDS = (
    "kab", "when", "date", "timeline", "kitna time",
    "kitne time", "kitne din", "kitne mahine", "kitne saal",
    "samay", "samaya", "muhurat", "muhurta", "year",
    "month", "din", "saal", "window", "tak", "ke baad",
    "schedule", "deadline",
)


def _phase48_is_timing_question(question: str) -> bool:
    """True if the user's question is asking about WHEN/timing — in
    which case dates in the answer ARE the answer and must survive."""
    if not isinstance(question, str):
        return False
    q = question.lower()
    return any(k in q for k in _PHASE48_TIMING_KEYWORDS)


# ── Phase 4.9 T022 — Adaptive depth classifier ────────────────────────────
# Replaces Phase 4.8's flat 1-2 sentence cap with intent-driven depth.
#   "simple"    → default; yes/no, short advice → 1-2 sentences
#   "detailed"  → user said kaise/why/explain/detail → 3-5 sentences
#   "technical" → user explicitly asked KP/houses/dasha breakdown/sublord
#                 → no truncation, full technical answer allowed.
# Order matters: technical takes precedence (check first), then detailed,
# else simple. Hindi + English keywords supported.

# ARCHITECT-FIX: word-boundary regex (not substring) so single tokens
# like 'bhava' / 'varga' / 'kp' don't false-positive inside longer
# unrelated words (e.g., 'bhavana', 'vargas' inside random text).
# Keys that legitimately span multiple tokens (e.g., 'sub lord',
# 'antardasha breakdown', 'd-9', '7th house') are matched via the
# composite pattern below using `\b` anchors and explicit separators.
import re as _re_phase49

_PHASE49_TIER3_PATTERN = _re_phase49.compile(
    r"(?ix)"
    r"\b("
    # KP system + sublord (KP must be a standalone token)
    r"kp|k\.p\.|krishnamurti|krishnamoorthi|"
    r"sub[\s\-]?lord|sublord|cuspal|cusp|"
    # Divisional / vargas (full word only)
    r"divisional|varga|vargas|navamsa|navamsha|"
    r"dasamsa|dashamsa|saptamsa|saptamsha|"
    r"d[\s\-]?9|d[\s\-]?10|d[\s\-]?7|"
    # Houses (numeric ordinal forms)
    r"house\s+number|"
    r"\d+(?:st|nd|rd|th)\s+house|"
    r"bhava|bhavas|"
    # Deep dasha breakdown (only when user explicitly says 'breakdown'
    # — generic 'dasha' alone is NOT Tier 3).
    r"(?:antardasha|antar\s*dasha|dasha)\s+breakdown|"
    r"pratyantar|pratyantardasha|"
    r"sookshma|sukshma|prana\s+dasha|"
    # Technical chart elements
    r"ascendant\s+lord|lagnesh|yogakaraka|atmakaraka"
    r")\b"
)

_PHASE49_TIER2_PATTERN = _re_phase49.compile(
    r"(?ix)"
    r"\b("
    # English explainers
    r"detail|details|explain|explanation|why|how|"
    r"in[\s\-]?depth|step[\s\-]?by[\s\-]?step|"
    r"elaborate|describe|"
    # Hindi/Hinglish explainers (word-bounded to avoid 'samjhao' inside
    # an unrelated phrase still being valid; these are real explainers).
    r"kaise|kyun|kyon|kyo|"
    r"samjhao|samjhaiye|samjha|"
    r"vistaar|vistar|"
    r"puri\s+baat|puri\s+detail"
    r")\b"
)


def _question_depth_tier(question: str) -> str:
    """Phase 4.9 T022 — classify user question into one of three depth
    tiers: 'simple' | 'detailed' | 'technical'. Pure, deterministic,
    case-insensitive, word-boundary safe (no false-positive substring
    matches like 'kp' inside 'okay' or 'bhava' inside 'bhavana').
    Returns 'simple' for empty/non-string input."""
    if not isinstance(question, str) or not question.strip():
        return "simple"
    # Tier 3 first (highest precedence): user explicitly named a
    # technical concept. They want the full breakdown.
    if _PHASE49_TIER3_PATTERN.search(question):
        return "technical"
    # Tier 2: explainer/why-type question. Short paragraph allowed.
    if _PHASE49_TIER2_PATTERN.search(question):
        return "detailed"
    # Tier 1: default, terse verdict + 1 reason.
    return "simple"


# ── Phase 5.0 (Apr 28 2026) — MINIMAL ASK PROMPT ────────────────────────────
# Replaces the entire Phase 4.x prompt assembly (UNIFIED NARRATOR CONTRACT,
# supertype contracts, multi-system messages, KP forcing, heavy locked_facts
# dump) with a 2-message prompt: 1 short system + 1 user msg containing a
# ~500-char chart summary + the question. The 3 critical guards still fire
# downstream: TIMING_VALIDATOR, POST_LOGIC_CHECK, and the Phase 4.9 truncator.
#
# Reversible via env flag `PHASE50_MINIMAL_PROMPT` (default "1" = ON).
# Set to "0" to fall back to the legacy Phase 4.x heavy path.

_PHASE50_SIGN_LORDS = {
    "aries": "Mars", "taurus": "Venus", "gemini": "Mercury",
    "cancer": "Moon", "leo": "Sun", "virgo": "Mercury",
    "libra": "Venus", "scorpio": "Mars", "sagittarius": "Jupiter",
    "capricorn": "Saturn", "aquarius": "Saturn", "pisces": "Jupiter",
}


def _phase50_mini_chart_summary(kundli: Any) -> str:
    """Phase 5.0 T028 — compact (~500 char) chart summary for the Ask
    minimal prompt. Includes Lagna+lord, Moon+nakshatra+pada, Sun,
    current MD/AD by lord names ONLY (no dates — TIMING_VALIDATOR
    enforces no date-invention), and a planet-in-house list.

    Pure, defensive — never raises on malformed input.
    """
    if not isinstance(kundli, dict):
        return ""

    lines: list[str] = []

    # ── Lagna + lord ────────────────────────────────────────────────────
    asc = (kundli.get("ascendant") or "").strip()
    if asc:
        lord = _PHASE50_SIGN_LORDS.get(asc.lower(), "")
        lines.append(f"Lagna: {asc}" + (f" (lord {lord})" if lord else ""))

    # ── Moon + nakshatra + pada ─────────────────────────────────────────
    moon = (kundli.get("moonSign") or "").strip()
    nak = (kundli.get("nakshatra") or "").strip()
    nak_pada = kundli.get("nakshatraPada")
    nak_ruler = (kundli.get("nakshatraRuler") or "").strip()
    if moon:
        moon_line = f"Moon: {moon}"
        if nak:
            moon_line += f" ({nak}"
            if nak_pada:
                moon_line += f" pada {nak_pada}"
            if nak_ruler:
                moon_line += f", ruler {nak_ruler}"
            moon_line += ")"
        lines.append(moon_line)

    # ── Sun ─────────────────────────────────────────────────────────────
    sun = (kundli.get("sunSign") or "").strip()
    if sun:
        lines.append(f"Sun: {sun}")

    # ── Current dasha (lord names ONLY — no dates) ──────────────────────
    cd = kundli.get("currentDasha") or {}
    if isinstance(cd, dict):
        md = (cd.get("maha") or cd.get("mahaDasha") or "").strip()
        ad = (cd.get("antar") or cd.get("antarDasha") or "").strip()
        if md or ad:
            lines.append(f"Current Dasha: {md or '?'} MD / {ad or '?'} AD")

    # ── Planets in houses (one line per house, grouped) ─────────────────
    planets = kundli.get("planets")
    by_house: dict[int, list[str]] = {}
    if isinstance(planets, list):
        for p in planets:
            if not isinstance(p, dict):
                continue
            name = (p.get("name") or "").strip()
            house = p.get("house")
            sign = (p.get("sign") or "").strip()
            retro = bool(p.get("retrograde"))
            if name and isinstance(house, int):
                tag = name + (f"({sign[:3]})" if sign else "") + ("[R]" if retro else "")
                by_house.setdefault(house, []).append(tag)
    elif isinstance(planets, dict):
        for name, p in planets.items():
            if not isinstance(p, dict):
                continue
            house = p.get("house")
            sign = (p.get("sign") or "").strip()
            retro = bool(p.get("retrograde"))
            if isinstance(house, int):
                tag = str(name) + (f"({sign[:3]})" if sign else "") + ("[R]" if retro else "")
                by_house.setdefault(house, []).append(tag)

    if by_house:
        house_parts = []
        for h in sorted(by_house.keys()):
            house_parts.append(f"{h}H: {' '.join(by_house[h])}")
        lines.append("Planets: " + " | ".join(house_parts))

    # ── Divisional charts (D9 Navamsha, D10 Dashamsha) ──────────────────
    # Users frequently ask about D9 (marriage) and D10 (career) placements.
    # Without this, the model hallucinates D9/D10 positions from D1 data.
    # Compact format: "D10 (Dashamsha — career): asc=Sign | Sun=Sign(Hh) ..."
    dcharts = kundli.get("divisionalCharts") or {}
    if isinstance(dcharts, dict):
        for dkey, dlabel in (("D9", "D9 (Navamsha — marriage)"),
                             ("D10", "D10 (Dashamsha — career)")):
            d = dcharts.get(dkey)
            if not isinstance(d, dict):
                continue
            d_asc = (d.get("ascendant") or "").strip()
            d_planets = d.get("planets")
            if not d_asc and not d_planets:
                continue
            parts = [dlabel + ":"]
            if d_asc:
                parts.append(f"asc={d_asc}")
            d_pairs = []
            if isinstance(d_planets, list):
                for p in d_planets:
                    if not isinstance(p, dict):
                        continue
                    pname = (p.get("name") or "").strip()
                    psign = (p.get("sign") or "").strip()
                    phouse = p.get("house")
                    if pname and psign:
                        h_tag = f"({phouse}H)" if isinstance(phouse, int) else ""
                        d_pairs.append(f"{pname}={psign}{h_tag}")
            elif isinstance(d_planets, dict):
                for pname, p in d_planets.items():
                    if not isinstance(p, dict):
                        continue
                    psign = (p.get("sign") or "").strip()
                    phouse = p.get("house")
                    if psign:
                        h_tag = f"({phouse}H)" if isinstance(phouse, int) else ""
                        d_pairs.append(f"{pname}={psign}{h_tag}")
            if d_pairs:
                parts.append(" | ".join(d_pairs))
            lines.append(" ".join(parts))

    return "\n".join(lines)


# Phase 5.0 Final Strip (Apr 28 2026): tier-aware length hints REMOVED.
# The user's directive — "tier hacks jo prompt ke andar likhe hain" — explicitly
# bans length-control text inside the prompt. The model now decides answer
# length naturally from the question. Constant kept as an empty dict for
# backward compatibility with anything still importing it; do NOT re-introduce
# tier hints here.
_PHASE50_TIER_HINT: dict[str, str] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5.3 — Topic-specific classical-rule checklists
# ─────────────────────────────────────────────────────────────────────────────
# When the user asks a topic that has well-known classical Vedic rules
# (marriage, career, wealth, health), inject a SHORT checklist into the
# user message so the model walks through each rule using the kundli data
# BEFORE giving the verdict — instead of grabbing one indicator and
# jumping to a confident conclusion.
#
# This is reasoning guidance, NOT post-validation. The model still answers
# in the lean ChatGPT style; it just thinks more carefully first.

_PHASE53_TOPIC_RULES: dict[str, str] = {
    "marriage": (
        "RULES_TO_CHECK (marriage — love vs arrange, timing, compatibility):\n"
        "Walk through each silently using the FULL_KUNDLI_JSON, then weigh "
        "BOTH sides before answering. Do NOT decide from a single indicator.\n\n"
        "STEP 1 — MANDATORY D9 (NAVAMSHA) CHECK (do this FIRST, never skip):\n"
        "  • D9 lagna and D9 lagna lord — overall marital strength.\n"
        "  • D9 7th house — sign, occupants, aspects.\n"
        "  • D9 7th lord — sign (own/exalted/debilitated/friendly), house, "
        "afflictions.\n"
        "  • D9 Venus — sign, house, dignity (Venus is THE marriage karaka, "
        "and D9 is THE marriage chart).\n"
        "  • Vargottama check — is Venus, 7th lord, or lagna lord in the "
        "SAME sign in D1 and D9? If yes, that planet is extremely strong "
        "and DOUBLES its result.\n"
        "  • Dignity-change check — is Venus or 7th lord exalted in D1 but "
        "debilitated in D9 (or vice versa)? D9 wins for the final fruit.\n"
        "  • If D9 7th lord is debilitated, combust, or in 6/8/12 with no "
        "neecha-bhanga → marital obstacles even if D1 looks fine.\n\n"
        "STEP 2 — LOVE-MARRIAGE indicators (count how many fire, in BOTH "
        "D1 and D9):\n"
        "  1. 5th lord ↔ 7th lord connection (conjunction, mutual aspect, "
        "exchange, OR D9 link — D9 link is the strongest confirmation).\n"
        "  2. Venus connected to 5th house, 7th house, or their lords — "
        "especially with Rahu, Mars, or Mercury.\n"
        "  3. Rahu in 5th OR 7th house, OR Rahu with 7th lord.\n"
        "  4. Mars-Venus conjunction or mutual aspect.\n"
        "  5. 5H-7H-11H lords mutually linked.\n"
        "  6. Lagna lord ↔ 7th lord exchange or aspect.\n"
        "  7. Moon-Venus close conjunction or mutual aspect.\n\n"
        "STEP 3 — ARRANGE-MARRIAGE indicators:\n"
        "  1. 7th lord well-placed (own/exalted/friendly sign) WITHOUT any "
        "5th-lord connection.\n"
        "  2. Jupiter or Saturn primary aspect on 7th house (no Venus-Rahu "
        "involvement).\n"
        "  3. 7th house ruled by traditional planet (Sun/Moon/Jupiter) "
        "with no afflictions.\n"
        "  4. Strong dispositor of 7th lord but no 5th-7th cross-link.\n\n"
        "STEP 4 — CRITICAL DISCRIMINATORS:\n"
        "  • Manglik / Kuja dosha: Mars in 1/4/7/8/12 from Lagna OR Moon.\n"
        "  • Saturn-Venus or Saturn on 7th = delays, often arrange tendency.\n"
        "  • RAHU in 8TH HOUSE = sudden events / obstacles in marriage — "
        "NOT a love-marriage confirmation. Treat with caution.\n"
        "  • Ketu on 7th lord = detachment, not love.\n"
        "  • Combust 7th lord (within ~6° of Sun) = weakened marriage karaka.\n\n"
        "VERDICT RULE: D9 is the deciding chart. If D1 says love but D9 "
        "Venus/7th-lord is weak/afflicted, lean towards arrange or "
        "delays. If both D1 and D9 confirm same direction with ≥3 "
        "indicators and no major affliction → confident verdict. If D1 "
        "and D9 disagree → say 'mixed — D1 shows X but D9 shows Y' "
        "and explain briefly. NEVER give a confident verdict without "
        "completing the D9 check."
    ),
    "career": (
        "RULES_TO_CHECK (career — direction, success, timing):\n"
        "Walk through each silently using the FULL_KUNDLI_JSON before "
        "answering.\n\n"
        "STEP 1 — MANDATORY D10 + D9 CHECK (do this FIRST):\n"
        "  • D10 (Dashamsha) is THE career chart — check D10 lagna, D10 "
        "lagna lord, D10 10th house, D10 10th lord, D10 Sun (career karaka).\n"
        "  • D9 confirmation — D9 lagna lord (overall life strength), D9 "
        "10th lord. A weak D9 weakens ALL D1 promises including career.\n"
        "  • Vargottama check — is the 10th lord, lagna lord, or Sun in "
        "the same sign in D1 and D10 (or D1 and D9)? If yes, very strong "
        "career signal.\n"
        "  • Dignity-change check — strong in D1 but weak in D10/D9 = "
        "result will under-deliver. Weak in D1 but strong in D10/D9 = "
        "neecha-bhanga, much better outcome than D1 suggests.\n\n"
        "STEP 2 — D1 CORE CHECKS:\n"
        "  1. 10th house lord — sign, house, dignity, aspects.\n"
        "  2. 10th house occupants (any planet here = strong influence).\n"
        "  3. Lagna lord ↔ 10th lord connection.\n"
        "  4. Atmakaraka (highest-degree planet) — career direction clue.\n"
        "  5. Sun (govt/authority), Saturn (service/discipline), Mercury "
        "(business/communication), Jupiter (teaching/advisory) — which is "
        "strongest, in BOTH D1 and D10?\n"
        "  6. Current Mahadasha + Antardasha lord — does it own/aspect "
        "the 10th house in D1 AND D10?\n"
        "  7. 6th house (service/competition) and 11th house (gains).\n\n"
        "VERDICT RULE: D10 + D9 win over D1 for the FINAL career outcome. "
        "If D1 shows strong career but D10 lord is debilitated/afflicted "
        "with no neecha-bhanga → career will under-deliver. If indicators "
        "across D1, D9, D10 are mixed, say so honestly."
    ),
    "wealth": (
        "RULES_TO_CHECK (wealth, money, finance):\n"
        "Walk through each silently using the FULL_KUNDLI_JSON before "
        "answering.\n\n"
        "STEP 1 — MANDATORY D9 CHECK (do this FIRST):\n"
        "  • D9 lagna and D9 lagna lord — overall life strength affects "
        "wealth delivery.\n"
        "  • D9 Jupiter (wealth karaka) — sign, house, dignity. A weak "
        "D9 Jupiter weakens ALL dhana yogas in D1.\n"
        "  • D9 2nd lord and D9 11th lord — actual wealth fruit.\n"
        "  • Vargottama check on Jupiter, 2nd lord, 11th lord — same "
        "sign in D1 and D9 = very strong wealth indicator.\n"
        "  • Dignity-change check — wealth lords debilitated in D9 = "
        "promise of D1 dhana yoga will not fully materialize.\n\n"
        "STEP 2 — D1 CORE CHECKS:\n"
        "  1. 2nd house (accumulated wealth) and its lord.\n"
        "  2. 11th house (gains) and its lord.\n"
        "  3. 5th house (speculation, sudden gains) and its lord.\n"
        "  4. Dhana yogas: 2H-5H, 2H-9H, 2H-11H, 5H-9H, 5H-11H, 9H-11H "
        "lord connections — count active yogas.\n"
        "  5. Jupiter (wealth karaka) and Venus (luxury) — dignity and "
        "house placement, in BOTH D1 and D9.\n"
        "  6. Dispositor of 2nd lord and 11th lord.\n"
        "  7. 6H-8H-12H (loss houses) afflictions to wealth lords.\n"
        "  8. Current dasha lord — does it own/aspect wealth houses in "
        "D1 AND D9?\n\n"
        "VERDICT RULE: Count active dhana yogas in D1, then verify in D9. "
        "If D9 confirms → strong wealth promise. If D9 contradicts → say "
        "'D1 shows yogas but D9 weakens delivery'. Be honest about mixed "
        "signals."
    ),
    "health": (
        "RULES_TO_CHECK (health, illness, recovery):\n"
        "Walk through each silently using the FULL_KUNDLI_JSON before "
        "answering.\n\n"
        "STEP 1 — MANDATORY D9 + D30 CHECK (do this FIRST):\n"
        "  • D9 lagna lord — overall vitality and life-force strength.\n"
        "  • D30 (Trimsamsha) — the dedicated health/disease chart. "
        "Check D30 lagna lord and Mars/Saturn placements (these signify "
        "specific diseases).\n"
        "  • D9 lagna lord debilitated/combust/in 6-8-12 = weakened "
        "constitution beyond what D1 shows.\n"
        "  • Vargottama lagna lord = strong constitution and recovery "
        "ability.\n\n"
        "STEP 2 — D1 CORE CHECKS:\n"
        "  1. Lagna and Lagna lord — dignity, afflictions.\n"
        "  2. 6th house (illness), 8th house (chronic), 12th house "
        "(hospitalization) — occupants, lords, aspects.\n"
        "  3. Sun (vitality) and Moon (mind/fluids) condition in D1 AND D9.\n"
        "  4. Malefic aspects on Lagna or Lagna lord.\n"
        "  5. Current dasha lord — benefic or malefic for health?\n"
        "  6. Specific organ rule: house signifies body part (e.g. 4H "
        "chest, 5H stomach, 6H intestine).\n\n"
        "VERDICT RULE: Health is sensitive — never alarm. If indicators "
        "show strain, suggest consulting a physician AND offer the "
        "astrological context briefly. Do NOT diagnose. Use D9/D30 to "
        "confirm whether D1 affliction will actually manifest."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5.5 — Deterministic LOVE-vs-ARRANGE engine (verdict-lock)
# ─────────────────────────────────────────────────────────────────────────────
# User feedback: same kundli was producing different verdicts (love vs
# arrange) across requests because the LLM was DECIDING the verdict from
# FULL_KUNDLI_JSON + classical-rule checklist. LLMs are non-deterministic —
# verdict stability requires a Python-computed verdict, with the LLM only
# EXPRESSING / explaining it.
#
# Architecture:
#   Kundli → Engine → FIXED VERDICT → LLM (only narrates) → Output
#
# This module:
#   1. Detects "love vs arrange" question pattern (Hinglish + English).
#   2. Computes a classical-rule weighted score using D1 + D9.
#   3. Locks the verdict + headline reasons into the prompt as an
#      AUTHORITATIVE_ENGINE_VERDICT block — LLM is told to express it
#      verbatim in the user's language, NOT to re-analyze or contradict.
#   4. Result is deterministic for the same kundli.

_PHASE55_SIGNS_ORDER = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_PHASE55_SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}
_PHASE55_SIGN_IDX = {s: i for i, s in enumerate(_PHASE55_SIGNS_ORDER)}


def _phase55_history_was_love_vs_arrange(history: list | None) -> bool:
    """Inspect the most recent assistant turn in the conversation
    history for love-vs-arrange context.

    A turn counts as love-vs-arrange context when it contains ANY of
    the love or arrange tokens used by the engine's verdict text — i.e.
    the assistant has just delivered a love-vs-arrange answer in the
    previous turn. Used by the detector to engage the lock on bare
    follow-ups like "kaise check kiya?" / "explain karo" / "kyun?"
    that would otherwise miss because they contain no love/arrange
    keyword themselves.

    Conservative: only inspects the MOST recent assistant turn (not
    older history). If the user has changed topics in between, the
    follow-up will not hijack the previous love-vs-arrange context.
    """
    if not isinstance(history, list) or not history:
        return False
    for h in reversed(history):
        if (h or {}).get("role") == "assistant":
            prev = ((h.get("content") or h.get("text") or "")).lower()
            tokens = (
                "love marriage", "arrange marriage", "arranged marriage",
                "love ya arrange", "love or arrange",
                "leaning_love", "leaning_arrange",
                "clear_love", "clear_arrange",
                "thoda zyada jhukav",   # signature wording from leaning text
                "love ki taraf", "arrange ki taraf",
                "pyaar se shaadi", "prem vivah",
            )
            if any(tok in prev for tok in tokens):
                return True
            # Inspect only the most recent assistant turn.
            return False
    return False


def _phase55_is_love_vs_arrange_question(
    question: str,
    history: list | None = None,
) -> bool:
    """True iff the question is a love-vs-arrange marriage decision query
    OR a follow-up asking the engine to EXPLAIN that decision.

    Three trigger paths:

    1. Direct compare: BOTH a love token AND an arrange token appear
       (e.g. "love ya arrange?", "love marriage or arranged?").

    2. Explain-mode follow-up (in-question): ONE of (love | arrange)
       tokens appears together with a marriage word AND an explanation
       trigger ("kyun / kaise / why / how / explain / reason / detail /
       samjhao"). This catches "kaise check kiya love marriage hoga
       explain karo".

    3. Context-memory follow-up: the question itself contains NO
       love/arrange tokens, but the previous assistant turn (in
       `history`) was a love-vs-arrange answer AND the question carries
       an explanation trigger. This catches bare follow-ups like
       "kaise check kiya?" / "kyun?" / "explain karo" that ChatGPT-
       style users type after seeing a verdict. Without this path,
       string-match-only detection misses the entire follow-up class.

    Conservative — bare "love marriage hoga?" without an explain
    trigger does NOT fire (normal forward-looking question), and
    history-based context only triggers when the previous turn was
    actually about love-vs-arrange (not, say, a career answer).
    """
    if not question or not isinstance(question, str):
        return False
    s = question.lower()
    has_love = bool(re.search(r"\b(love|pyaar|pyar|prem|romance)\b", s))
    has_arr  = bool(re.search(r"\barrang", s))
    has_explain = bool(re.search(
        r"\b(why|how|explain|reason|detail|samjha|kyu|kais|batao detail)",
        s))

    # Path 1 — direct comparison
    if has_love and has_arr:
        return True

    # Path 2 — explain-mode follow-up with love/arrange + marriage word
    if has_love or has_arr:
        has_marriage = bool(re.search(
            r"\b(marriage|shaadi|shadi|shaddi|vivah|biyah|byah)\b", s))
        if has_marriage and has_explain:
            return True

    # Path 3 — context-memory: bare follow-up after a love-vs-arrange answer
    if has_explain and _phase55_history_was_love_vs_arrange(history):
        return True

    return False


def _p55_planet(plist: list, name: str) -> dict | None:
    for p in (plist or []):
        if (p.get("name") or "").strip() == name:
            return p
    return None


def _p55_house_lord(lagna_sign: str, house_num: int) -> str | None:
    li = _PHASE55_SIGN_IDX.get(lagna_sign)
    if li is None:
        return None
    target_idx = (li + house_num - 1) % 12
    return _PHASE55_SIGN_LORDS.get(_PHASE55_SIGNS_ORDER[target_idx])


def _p55_same_sign(plist: list, p1: str, p2: str) -> bool:
    a = _p55_planet(plist, p1); b = _p55_planet(plist, p2)
    if not a or not b: return False
    return a.get("sign") == b.get("sign")


def _p55_same_house(plist: list, p1: str, p2: str) -> bool:
    a = _p55_planet(plist, p1); b = _p55_planet(plist, p2)
    if not a or not b: return False
    return a.get("house") == b.get("house")


def _p55_planet_house(plist: list, name: str) -> int | None:
    p = _p55_planet(plist, name)
    return p.get("house") if p else None


def _p55_planet_sign(plist: list, name: str) -> str | None:
    p = _p55_planet(plist, name)
    return p.get("sign") if p else None


def _phase55_safe_compute_kp_summary(kundli: Any) -> dict:
    """Phase 5.5h — safe wrapper around `kp_locked_facts.compute_kp_summary`.

    Lazy-imports to avoid any startup-time circular-import surprises and
    swallows ANY exception (returns ``{}``). KP enrichment is best-effort
    and must NEVER break the LvA path. Returns ``{}`` when:
      • lat/lon/tz missing on the kundli payload (most common case)
      • pyswisseph raises (corrupt birth data)
      • module import fails for any reason
    """
    if not isinstance(kundli, dict):
        return {}
    try:
        from kp_locked_facts import compute_kp_summary  # type: ignore
    except Exception:
        return {}
    try:
        out = compute_kp_summary(None, kundli)
        return out if isinstance(out, dict) else {}
    except Exception:
        return {}


def _phase55_kp_facts_for_marriage(kp_summary: Any) -> dict | None:
    """Phase 5.5h — adapter from `compute_kp_summary` output to the
    Phase 5.5g `kp_facts` contract used by the LvA locked verdict block.

    INPUT shape (from kp_locked_facts.compute_kp_summary):
      {
        "houses": {
          1:  {cusp_sign, cusp_deg, sub_lord, verdict, signifies, obstructs},
          5:  {...},
          7:  {...},
          10: {...},
          11: {...},
        },
        "ayanamsa": float,
      }
      May also be ``{}`` when geo data is missing.

    OUTPUT shape (consumed by `_phase55_format_kp_explanation_block`):
      {
        "csl_5":  {"sign": str, "lord": str, "connected_houses": list[int]},
        "csl_7":  {...},
        "csl_11": {...},
      }
      OR ``None`` when no usable CSLs are present.

    `connected_houses` is the union of the engine's ``signifies`` (event-house
    overlaps for that cusp) and ``obstructs`` (negative-house overlaps). The
    LLM applies the LvA narration rules from the locked-block prompt to
    interpret the houses. The engine's own classical KP verdict
    (CONFIRMS/PARTIAL/DENIES) is intentionally NOT surfaced here — KP in
    the LvA block is ADDITIVE flavour, not a parallel verdict, per the
    user's explicit instruction. The authoritative call remains the LvA
    ratio-ladder verdict computed earlier in this engine.

    Marriage-relevant cusps mapped:
      • 5th  — love, romance, courtship  →  csl_5
      • 7th  — marriage, partnership     →  csl_7
      • 11th — fulfilment of desires     →  csl_11
    """
    if not isinstance(kp_summary, dict):
        return None
    houses = kp_summary.get("houses")
    if not isinstance(houses, dict):
        return None

    out: dict[str, dict] = {}
    for cusp_h, csl_key in ((5, "csl_5"), (7, "csl_7"), (11, "csl_11")):
        info = houses.get(cusp_h)
        if not isinstance(info, dict):
            continue
        sub_lord  = info.get("sub_lord")
        cusp_sign = info.get("cusp_sign")
        if not isinstance(sub_lord, str) or not sub_lord:
            continue
        if not isinstance(cusp_sign, str) or not cusp_sign:
            continue

        connected: set[int] = set()
        for k in ("signifies", "obstructs"):
            seq = info.get(k) or []
            if isinstance(seq, (list, tuple, set)):
                for x in seq:
                    if isinstance(x, int) and 1 <= x <= 12:
                        connected.add(x)
                    elif isinstance(x, float) and x == int(x) and 1 <= int(x) <= 12:
                        connected.add(int(x))

        out[csl_key] = {
            "sign":              cusp_sign,
            "lord":              sub_lord,
            "connected_houses":  sorted(connected),
        }

    return out or None


def _phase55_compute_love_vs_arrange(kundli: Any) -> dict | None:
    """Deterministic love-vs-arrange verdict from classical rules.

    Uses D1 (kundli['planets']) + D9 (kundli['divisionalCharts']['D9']).
    Returns None if kundli is missing required data — caller falls back
    to the LLM-only path.

    Returns:
      {
        'verdict':        'love_likely' | 'arrange_likely' | 'mixed',
        'confidence':     0.55 .. 0.92,
        'love_score':     int,
        'arrange_score':  int,
        'reasons_love':   list[str],
        'reasons_arrange': list[str],
        'verdict_text_hi': str  (Hinglish 1-line verdict)
      }
    """
    if not isinstance(kundli, dict):
        return None
    plist_d1 = kundli.get("planets") or []
    if not plist_d1:
        return None
    lagna = (kundli.get("ascendant") or "").strip().capitalize()
    if lagna not in _PHASE55_SIGN_IDX:
        return None

    fifth_lord    = _p55_house_lord(lagna, 5)
    seventh_lord  = _p55_house_lord(lagna, 7)

    d9 = ((kundli.get("divisionalCharts") or {}).get("D9") or {})
    plist_d9 = d9.get("planets") or []

    love_score = 0
    arrange_score = 0
    reasons_love: list[str] = []
    reasons_arrange: list[str] = []

    # ── LOVE INDICATORS ──────────────────────────────────────────────────

    # 1. 5th lord ↔ 7th lord connection in D1 (same sign or same house)
    if fifth_lord and seventh_lord and fifth_lord != seventh_lord:
        if _p55_same_sign(plist_d1, fifth_lord, seventh_lord):
            love_score += 4
            reasons_love.append(
                f"5th lord ({fifth_lord}) and 7th lord ({seventh_lord}) "
                f"in same sign in D1 (very strong love-marriage indicator)"
            )
        elif _p55_same_house(plist_d1, fifth_lord, seventh_lord):
            love_score += 3
            reasons_love.append(
                f"5th lord ({fifth_lord}) and 7th lord ({seventh_lord}) "
                f"in same house in D1"
            )

    # 2. Same connection in D9 (Navamsha — D9 is the deciding chart)
    if plist_d9 and fifth_lord and seventh_lord and fifth_lord != seventh_lord:
        if _p55_same_sign(plist_d9, fifth_lord, seventh_lord):
            love_score += 4
            reasons_love.append(
                f"5L ↔ 7L conjunct in D9 Navamsha (deep-chart confirmation)"
            )
        elif _p55_same_house(plist_d9, fifth_lord, seventh_lord):
            love_score += 3
            reasons_love.append("5L ↔ 7L same house in D9 Navamsha")

    # 3. Venus in 5H or 7H (D1) — love karaka in romance/partnership house
    venus_h = _p55_planet_house(plist_d1, "Venus")
    if venus_h in (5, 7):
        love_score += 2
        reasons_love.append(f"Venus in {venus_h}H of D1 supports love marriage")

    # 4. Rahu in 5H or 7H — unconventional bond / love marriage
    rahu_h = _p55_planet_house(plist_d1, "Rahu")
    if rahu_h in (5, 7):
        love_score += 3
        reasons_love.append(
            f"Rahu in {rahu_h}H of D1 — unconventional bond / love marriage"
        )

    # 5. Mars-Venus same sign or same house (D1)
    if _p55_same_sign(plist_d1, "Mars", "Venus"):
        love_score += 2
        reasons_love.append("Mars-Venus conjunct in D1 — passionate attraction")
    elif _p55_same_house(plist_d1, "Mars", "Venus"):
        love_score += 2
        reasons_love.append("Mars-Venus same house in D1 — attraction signal")

    # 6. 5th lord = Venus or Mars (natural love-nature ruler)
    if fifth_lord in ("Venus", "Mars"):
        love_score += 1
        reasons_love.append(f"5th lord is {fifth_lord} (natural love-nature ruler)")

    # 7. D9 Venus dignity
    venus_d9_sign = _p55_planet_sign(plist_d9, "Venus")
    if venus_d9_sign in ("Taurus", "Libra"):
        love_score += 2
        reasons_love.append(
            f"D9 Venus in own sign {venus_d9_sign} (deep love nature)"
        )
    elif venus_d9_sign == "Pisces":
        love_score += 3
        reasons_love.append("D9 Venus exalted in Pisces (sublime love bond)")

    # ── ARRANGE INDICATORS / OBSTACLES ───────────────────────────────────

    # 1. Manglik dosha — Mars in 1/4/7/8/12 from lagna
    mars_h = _p55_planet_house(plist_d1, "Mars")
    if mars_h in (1, 4, 7, 8, 12):
        arrange_score += 2
        reasons_arrange.append(
            f"Manglik dosha (Mars in {mars_h}H) — delays / typically arrange"
        )

    # 2. Saturn-Venus conjunction = delays
    if _p55_same_sign(plist_d1, "Saturn", "Venus"):
        arrange_score += 2
        reasons_arrange.append(
            "Saturn-Venus conjunct — delays, structured (arrange) marriage"
        )

    # 3. Saturn in 7H — delays / arrange tendency
    sat_h = _p55_planet_house(plist_d1, "Saturn")
    if sat_h == 7:
        arrange_score += 2
        reasons_arrange.append(
            "Saturn in 7H — delays, traditional/arrange marriage"
        )

    # 4. Rahu in 8H — sudden events / OBSTACLES (NOT a love indicator)
    if rahu_h == 8:
        arrange_score += 2
        reasons_arrange.append(
            "Rahu in 8H — obstacles / sudden events in marriage (not love)"
        )

    # 5. Ketu in 7H — detachment, often arrange
    ketu_h = _p55_planet_house(plist_d1, "Ketu")
    if ketu_h == 7:
        arrange_score += 2
        reasons_arrange.append("Ketu in 7H — detachment in partnership")

    # 6. D9 Venus debilitated (Virgo) = surface attraction only
    if venus_d9_sign == "Virgo":
        arrange_score += 2
        reasons_arrange.append(
            "D9 Venus debilitated in Virgo — surface attraction only"
        )

    # 7. D9 7th lord in dusthana (6/8/12) — partner friction
    if seventh_lord and plist_d9:
        s7_d9_h = _p55_planet_house(plist_d9, seventh_lord)
        if s7_d9_h in (6, 8, 12):
            arrange_score += 2
            reasons_arrange.append(
                f"D9 7th lord ({seventh_lord}) in dusthana {s7_d9_h}H "
                f"— partner friction"
            )

    # ── VERDICT ──────────────────────────────────────────────────────────

    diff = love_score - arrange_score
    total = love_score + arrange_score
    if total == 0:
        verdict = "mixed"
        confidence = 0.55
    elif diff >= 4:
        verdict = "love_likely"
        confidence = min(0.92, 0.55 + (diff / max(total, 1)) * 0.4)
    elif diff <= -4:
        verdict = "arrange_likely"
        confidence = min(0.92, 0.55 + (-diff / max(total, 1)) * 0.4)
    else:
        verdict = "mixed"
        confidence = 0.55

    # Phase 5.5 architect-review fix: evidence floor. Even with diff>=4,
    # if total evidence is sparse (e.g. 4 vs 0) the high-confidence verdict
    # is fragile — a single counter-indicator the engine doesn't yet check
    # would flip it. Require total>=6 for a directional call; otherwise
    # downgrade to `mixed` with low confidence so the LLM can present it
    # honestly as inconclusive.
    if verdict in ("love_likely", "arrange_likely") and total < 6:
        verdict = "mixed"
        confidence = 0.55

    if verdict == "love_likely":
        verdict_text = "Aapki kundli mein love marriage ke chances zyada hain."
    elif verdict == "arrange_likely":
        verdict_text = "Aapki kundli mein arrange marriage ke chances zyada hain."
    else:
        verdict_text = (
            "Aapki kundli mein love aur arrange dono ke mixed sanket hain — "
            "ek taraf clear nahi jhukti."
        )

    # ── Phase 5.5e (Apr 29 2026) — CONFIDENCE-RATIO VERDICT LADDER ────────
    # Phase 5.5b used absolute diff thresholds (`diff >= 4` → clear,
    # `1..3` → leaning). The flaw: a 5-vs-4 chart and an 8-vs-4 chart
    # both became "leaning" with identical UX text, even though their
    # actual evidence concentration is wildly different (11% vs 33% of
    # total tilt).
    #
    # Phase 5.5e replaces the absolute-diff ladder with a confidence
    # ratio (`|diff| / total`) so the public verdict reflects how
    # CONCENTRATED the engine's evidence is, not just which side has
    # more points. This is the "Hybrid Plan" — keep all 14 rules
    # (accuracy intact) but tighten the math behind the public label
    # (clarity improved + overconfidence on near-ties eliminated).
    #
    #   total < 6                  → inconclusive (evidence floor — same)
    #   confidence_ratio == 0.0    → inconclusive (perfect tie — same)
    #   confidence_ratio >= 0.50   → CLEAR direction
    #   confidence_ratio >= 0.20   → LEANING direction
    #   confidence_ratio <  0.20   → inconclusive (essentially tied)
    #
    # Worked examples:
    #   5L vs 4A  → conf=1/9 =0.111 → inconclusive (was leaning_love)
    #   6L vs 4A  → conf=2/10=0.20  → leaning_love
    #   8L vs 3A  → conf=5/11=0.454 → leaning_love (was clear_love)
    #   2L vs 10A → conf=8/12=0.667 → clear_arrange
    #
    # The 5v4 case becoming inconclusive is the explicit fix — that
    # was the architect's noted overconfidence on close calls. Internal
    # `verdict` field stays as-is (diff>=4 cutoff) for diagnostic
    # parity with prior phases.
    diff_abs = abs(love_score - arrange_score)
    higher_is_love = love_score > arrange_score
    confidence_ratio = (diff_abs / total) if total > 0 else 0.0

    # ── Phase 5.5f (Apr 29 2026) — DIRECTIONAL INCONCLUSIVE WORDING ────
    # Phase 5.5e correctly downgraded near-ties (ratio < 0.20) from
    # leaning to inconclusive — engine math is honest. But the UX text
    # was too flat: "dono taraf strong indication nahi hai" felt like
    # "system kuch bola hi nahi" when the chart did have a tiny tilt
    # (e.g. 5L vs 4A — love is genuinely the higher side, just by 1).
    #
    # Fix: keep the engine ladder unchanged, but split the inconclusive
    # branch into two wordings:
    #   • TRUE TIE  (ratio == 0 OR total < 6) → neutral text (no
    #     direction to mention honestly)
    #   • LOW-CONF TILT (0 < ratio < 0.20)    → directional text that
    #     acknowledges the tilt + strong "no confirmation" caveat
    # Verdict label `inconclusive` stays the same in both cases — only
    # the human-facing sentence differs. Engine accuracy + public clarity.
    if total < 6 or confidence_ratio == 0.0:
        verdict_public = "inconclusive"
        verdict_text_public = (
            "Aapki kundli mein dono taraf strong indication nahi hai — "
            "situation aur paristithi par depend karega."
        )
    elif confidence_ratio >= 0.50:
        if higher_is_love:
            verdict_public = "clear_love"
            verdict_text_public = "Aapki kundli mein clear love marriage yog hai."
        else:
            verdict_public = "clear_arrange"
            verdict_text_public = "Aapki kundli mein clear arrange marriage yog hai."
    elif confidence_ratio >= 0.20:
        if higher_is_love:
            verdict_public = "leaning_love"
            verdict_text_public = (
                "Aapki kundli mein love marriage ki taraf thoda zyada "
                "jhukav hai, lekin dono possibilities open hain."
            )
        else:
            verdict_public = "leaning_arrange"
            verdict_text_public = (
                "Aapki kundli mein arrange marriage ki taraf thoda zyada "
                "jhukav hai, lekin dono possibilities open hain."
            )
    else:
        # confidence_ratio in (0.0, 0.20) — engine evidence is too
        # diffuse to call a side cleanly, but there IS a small tilt
        # (diff_abs >= 1) that we can honestly mention with a strong
        # caveat. Phase 5.5f UX upgrade — Phase 5.5e math kept intact.
        verdict_public = "inconclusive"
        if higher_is_love:
            verdict_text_public = (
                "Love marriage ki taraf thoda jhukav hai, lekin strong "
                "confirmation nahi — situation par depend karega."
            )
        else:
            verdict_text_public = (
                "Arrange marriage ki taraf thoda jhukav hai, lekin strong "
                "confirmation nahi — situation par depend karega."
            )

    return {
        "verdict":              verdict,                # internal (diagnostic)
        "confidence":           round(confidence, 2),
        "confidence_ratio":     round(confidence_ratio, 3),  # Phase 5.5e
        "love_score":           love_score,
        "arrange_score":        arrange_score,
        "reasons_love":         reasons_love[:5],
        "reasons_arrange":      reasons_arrange[:5],
        "verdict_text_hi":      verdict_text,           # internal text (legacy)
        "verdict_public":       verdict_public,         # UX verdict
        "verdict_text_public":  verdict_text_public,    # UX headline (this is
                                                        # what the LLM narrates)
        # ── Phase 5.5g/5.5h — KP cuspal-sublord facts (LIVE) ──
        # Phase 5.5g shipped scaffolding; Phase 5.5h activates it by
        # reusing the existing `kp_locked_facts.compute_kp_summary`
        # pipeline (Placidus cusps + sub-lord chain via pyswisseph,
        # already in production for the heavy-prompt KP CROSS-CHECK
        # path). The adapter `_phase55_kp_facts_for_marriage` maps
        # H5/H7/H11 → csl_5/csl_7/csl_11. Returns None when birth
        # geo (lat/lon/tz) is missing — locked block then emits no
        # KP section, preserving the no-hallucination guarantee.
        "kp_facts":             _phase55_kp_facts_for_marriage(
                                    _phase55_safe_compute_kp_summary(kundli)),
    }


def _phase55_format_locked_verdict_block(
    v: dict,
    explain_mode: bool = False,
) -> str:
    """Render the engine verdict as a LOCKED authoritative block for the prompt.

    Tells the LLM: this is the verdict, your only job is to express it
    briefly. NO re-analysis, NO contradicting, NO flipping.

    The HEADLINE comes from `verdict_text_public` (Phase 5.5b UX layer)
    which always gives a directional answer (clear / leaning /
    inconclusive) — never the engineering "mixed" word that confuses
    users asking "love ya arrange?".

    When `explain_mode=True` (the user's question contains kyun / why /
    kaise / how / explain / reason / detail / samjhao alongside a
    love-or-arrange marriage word), the instruction is FLIPPED from
    "do not list reasons" to "MUST list 3-5 of the engine reasons in
    plain language". Without this, the model defaults to the cautious
    1-2 sentence headline even on direct "explain" follow-ups.
    """
    if not isinstance(v, dict):
        return ""
    rs_love = "\n".join(f"  + {r}" for r in (v.get("reasons_love") or [])) or "  (none)"
    rs_arr  = "\n".join(f"  - {r}" for r in (v.get("reasons_arrange") or [])) or "  (none)"
    # Prefer the public/UX headline; fall back to legacy text for safety.
    headline = v.get("verdict_text_public") or v.get("verdict_text_hi") or ""

    if explain_mode:
        instruction = (
            "INSTRUCTION (CRITICAL — EXPLAIN MODE): A deterministic Vedic-"
            "rules engine has already computed the verdict from the user's "
            "D1 + D9 charts. The user has explicitly asked HOW / WHY the "
            "verdict was reached, so you MUST now expand the answer:\n"
            "  1. State the HEADLINE in the user's language as the FIRST "
            "sentence — do NOT contradict, change, or soften the direction.\n"
            "  2. Then list 3-5 of the strongest reasons from REASONS_LOVE "
            "and REASONS_ARRANGE above, translated into plain Hindi/"
            "Hinglish/English (whichever matches the user's language). "
            "Use the side that matches the headline as the dominant set "
            "(love side for clear_love/leaning_love, arrange side for "
            "clear_arrange/leaning_arrange).\n"
            "  3. Keep each reason 1 short line. Total response: 4-7 short "
            "sentences. Do NOT add the raw score numbers (e.g. '5 vs 4'). "
            "Do NOT invent extra reasons not in the lists above. Do NOT "
            "re-derive from the kundli — the engine has already done that."
        )
    else:
        instruction = (
            "INSTRUCTION (CRITICAL): A deterministic Vedic-rules engine has "
            "already computed this verdict from the user's D1 + D9 charts. "
            "Your ONLY job is to express the HEADLINE in the user's "
            "language (Hindi/Hinglish/English) in 1-2 short sentences. The "
            "HEADLINE already gives a clear direction (clear / leaning / "
            "situation-dependent) — keep that direction; do NOT soften it "
            "back to 'mixed' or 'dono possibilities'. Do NOT add score "
            "numbers. Do NOT list the reasons unless the user explicitly "
            "asks 'kyun' / 'why' / 'reason batao' / 'explain' / 'detail "
            "mein batao' / 'how'. Do NOT contradict the verdict. Do NOT "
            "re-derive it from the kundli — the engine has already done "
            "that work."
        )

    # ── Phase 5.5g — optional KP explanation layer ──
    # Only emitted when the engine return dict carries actual KP cuspal-
    # sublord facts (kp_facts is non-empty). Hard guard prevents the LLM
    # from being told "use KP rules" when no real KP data exists, which
    # would invite CSL hallucination — exactly the Phase 5.0 violation.
    kp_block = _phase55_format_kp_explanation_block(v.get("kp_facts"))

    return (
        "AUTHORITATIVE_ENGINE_VERDICT (locked — DO NOT change, contradict, "
        "or recompute):\n"
        f"  VERDICT: {v.get('verdict_public') or v.get('verdict')}\n"
        f"  LOVE_SCORE: {v.get('love_score')}    "
        f"ARRANGE_SCORE: {v.get('arrange_score')}\n"
        f"  HEADLINE: {headline}\n"
        f"  REASONS_LOVE:\n{rs_love}\n"
        f"  REASONS_ARRANGE:\n{rs_arr}\n"
        + (kp_block if kp_block else "")
        + "\n"
        + instruction
    )


def _phase55_format_kp_explanation_block(kp_facts: Any) -> str:
    """Phase 5.5g — render the KP (Krishnamurti Paddhati) narration block.

    Returns "" (empty string) when `kp_facts` is None / empty / not a dict.
    This is a HARD guard: without real CSL facts the prompt section is
    omitted entirely so the LLM never gets told "use KP" without data
    (which would invite CSL hallucination).

    Expected `kp_facts` shape (when populated by chart provider or a
    future CSL extractor):
        {
            "csl_5":  {"sign": "Leo",    "lord": "Sun",
                       "connected_houses": [5, 7, 11]},
            "csl_7":  {"sign": "Aqua",   "lord": "Saturn",
                       "connected_houses": [2, 7, 11]},
            "csl_11": {"sign": "Sag",    "lord": "Jupiter",
                       "connected_houses": [5, 11]},
        }

    Interpretation rules embedded in the prompt (per user spec):
      - 5th CSL  → love / romance
      - 7th CSL  → marriage
      - 11th CSL → fulfillment / success
      - Connected to {5, 7, 11} → supports love → marriage
      - Connected to {6, 8, 12} → obstacles, denial, conversion
      - Connected to {2, 7, 11} on 7th CSL → marriage materializes

    The LLM is NEVER asked to compute KP — only to explain what the
    engine has computed. The KP facts feed into the existing
    AUTHORITATIVE_ENGINE_VERDICT lock — verdict cannot be recomputed
    or contradicted by the KP narration.
    """
    if not kp_facts or not isinstance(kp_facts, dict):
        return ""

    def _fmt_csl(label: str, key: str) -> str:
        c = kp_facts.get(key)
        if not isinstance(c, dict):
            return f"  {label}: (not provided)"
        sign = c.get("sign") or "?"
        lord = c.get("lord") or "?"
        houses = c.get("connected_houses") or []
        houses_s = ",".join(str(h) for h in houses) if houses else "(none)"
        return f"  {label}: {sign} (lord {lord}) → connected houses: {houses_s}"

    facts_lines = "\n".join([
        _fmt_csl("CSL_5  (love)",        "csl_5"),
        _fmt_csl("CSL_7  (marriage)",    "csl_7"),
        _fmt_csl("CSL_11 (fulfillment)", "csl_11"),
    ])

    return (
        "\n\nKP_FACTS (engine-computed cuspal sublords — DO NOT recompute):\n"
        f"{facts_lines}\n\n"
        "KP_EXPLANATION_GUIDE (use ONLY these classical KP rules to "
        "support — never to override — the verdict above):\n"
        "  - 5th CSL connects to {5, 7, 11}  → supports love → marriage\n"
        "  - 5th CSL connects to {6, 8, 12}  → obstacles / denial of love\n"
        "  - 7th CSL connects to {2, 7, 11}  → marriage materializes\n"
        "  - 11th CSL supports              → desired outcome fulfilled\n"
        "  - 6/8/12 dominate                → delays, breaks, conversion\n"
        "INSTRUCTION (KP layer — additive, NOT decisional):\n"
        "  • The verdict above is FINAL. KP must NOT change or flip it.\n"
        "  • In HEADLINE-ONLY mode (when the user did NOT ask kyun / why "
        "/ explain / detail / how), do NOT mention KP at all — keep the "
        "headline pure.\n"
        "  • In EXPLAIN mode (when the user asks 'kyun' / 'why' / "
        "'reason batao' / 'detail mein samjhao' / 'kaise' / 'how'), you "
        "MUST cite KP at least once alongside the Vedic reasons — using "
        "ONLY the KP_FACTS above. One natural sentence is enough. "
        "Example: \"KP paddhati me bhi 5th CSL Venus Taurus mein hai aur "
        "houses 5/8/10 se connected hai, jo love marriage ko support "
        "karta hai par 8th house ki involvement se thoda obstacle bhi "
        "deta hai.\" Citation MUST name the cusp number (5th/7th/11th), "
        "the sign and lord exactly as printed in KP_FACTS, and at least "
        "one of the connected houses — verbatim from the data above.\n"
        "  • If the KP_FACTS lines say '(not provided)' for a CSL, do "
        "NOT mention that CSL at all. Do NOT invent KP facts. Do NOT "
        "reason from planet positions to derive CSLs yourself."
    )


def _phase55_is_explain_mode_question(question: str) -> bool:
    """True iff the question explicitly asks WHY/HOW/EXPLAIN the verdict.

    Used by the builder to flip the locked-block instruction from
    "express headline only" to "headline + 3-5 reasons". Mirrors the
    explain-trigger regex in `_phase55_is_love_vs_arrange_question`.
    """
    if not question or not isinstance(question, str):
        return False
    s = question.lower()
    return bool(re.search(
        r"\b(why|how|explain|reason|detail|samjha|kyu|kais|batao detail)",
        s,
    ))


def _phase53_topic_rules(topic: str | None) -> str:
    """Return the topic-specific classical-rules checklist or empty string.

    The returned block is wrapped with an explicit OUTPUT INSTRUCTION
    so the model treats the entire rule walk-through as INTERNAL reasoning
    and outputs only a brief verdict — unless the user explicitly asks for
    an explanation. This prevents over-explaining on simple questions.

    Defensive: unknown topic → empty (no checklist injected, model uses
    the general ChatGPT-style guidance only).
    """
    if not topic or not isinstance(topic, str):
        return ""
    body = _PHASE53_TOPIC_RULES.get(topic.strip().lower(), "")
    if not body:
        return ""
    return (
        body +
        "\n\nOUTPUT INSTRUCTION (CRITICAL): All of the above is INTERNAL "
        "reasoning to help you arrive at the correct verdict. After "
        "silently walking through the rules, OUTPUT only the final verdict "
        "in 1-2 short sentences. Do NOT list the rules, planet positions, "
        "D9 / divisional-chart details, indicator counts, or step-by-step "
        "analysis in the visible response. Expand into reasoning ONLY if "
        "the user explicitly asks 'kyun' / 'why' / 'reason batao' / "
        "'explain' / 'detail mein batao' / 'how' or similar."
    )


def _phase50_build_minimal_messages(
    question: str,
    kundli: Any,
    lang: str = "hn",
    tier: str | None = None,
    extra_facts: str = "",
    topic: str | None = None,
    history: list | None = None,
) -> list[dict]:
    """Phase 5.0 T029 — build the 2-message minimal Ask prompt.

    Returns [system, user]:
      • system: short astrologer role + hard guard against invented
        dasha/dates + language match.
      • user: mini chart summary + optional engine-verdict fact line +
        question + tier-aware length hint.

    No supertype contracts, no UNIFIED NARRATOR preamble, no Rule 1-N,
    no KP forcing, no multi-system messages.
    """
    # `tier` is intentionally accepted but unused in the Final Strip path:
    # tier-based length hints have been removed from the prompt. Argument
    # kept so existing callers (and tests) need no signature change, and so
    # we can re-introduce a tier-aware behaviour later via env flag without
    # another callsite churn.
    _ = tier

    chart_summary = _phase50_mini_chart_summary(kundli)

    # Language: a single soft mirroring instruction folded into the system
    # message. No length, no format, no rules — model decides naturally.
    if lang == "hn":
        lang_hint = " Reply in the same Hindi/Hinglish style as the question."
    elif lang == "en":
        lang_hint = " Reply in English."
    else:
        lang_hint = " Match the user's language."

    # ── Phase 5.5 — DETERMINISTIC LOVE-vs-ARRANGE LOCK (computed early) ──
    # Detect/compute the lock BEFORE we build the system message so the
    # system message itself can be swapped to a "narrate-only" variant.
    # Architect-review (Phase 5.5) flagged that the default system message
    # tells the model "use D9 to ARRIVE at the right verdict" — when a
    # locked verdict is provided in the user message, that instruction
    # contradicts the lock and re-creates the verdict-flipping risk.
    #
    # Detector keys off the question text (not topic) so a mis-routed
    # love-vs-arrange question still gets the lock.
    locked_verdict = None
    if _phase55_is_love_vs_arrange_question(question or "", history=history):
        locked_verdict = _phase55_compute_love_vs_arrange(kundli)

    if locked_verdict:
        # Lock-mode system message: short, single instruction, NO
        # "compute your own verdict" language. The authoritative engine
        # block in the user message is the source of truth.
        system_msg = (
            "You are a Vedic astrology assistant.\n\n"
            "VERDICT-LOCK MODE: A deterministic Vedic-rules engine has "
            "ALREADY computed the verdict for this question from the "
            "user's D1 + D9 charts. The verdict is provided in the user "
            "message under AUTHORITATIVE_ENGINE_VERDICT.\n\n"
            "Your ONLY job:\n"
            "- Express the engine's HEADLINE in the user's language in "
            "1-2 short sentences.\n"
            "- Do NOT recompute, contradict, or flip the verdict.\n"
            "- Do NOT mention scores, indicator counts, or 'engine'.\n"
            "- Do NOT list the reasons unless the user explicitly asks "
            "'kyun' / 'why' / 'reason batao' / 'explain' / 'detail mein "
            "batao' / 'how'.\n"
            "- Speak like a human astrologer, not a report." + lang_hint
        )
    else:
        system_msg = (
            "You are a Vedic astrology assistant.\n\n"
            "You have access to the user's kundli (planets, houses, current "
            "dasha, AND all divisional charts D1-D60 in FULL_KUNDLI_JSON).\n"
            "Use it internally to think.\n\n"
            "OUTPUT STYLE — answer only what is asked:\n\n"
            "- Give a clear and direct answer.\n"
            "- For a simple yes/no or A-vs-B question: reply with the verdict "
            "briefly in a single short response. Do NOT add reasoning, planet "
            "names, house numbers, D9/D10/D30 details, or astrological "
            "breakdown unless the user explicitly asks 'kyun', 'reason "
            "batao', 'explain', 'detail mein batao', 'how', or similar.\n"
            "- Only expand into a detailed analysis when the user asks for "
            "explanation or technical reasoning.\n"
            "- If a clear answer is possible, do not avoid it.\n"
            "- Focus only on what the user asked. Do not stay vague or "
            "neutral. Speak like a human, not a report.\n\n"
            "CLASSICAL RULE — MANDATORY D9 (NAVAMSHA) CHECK (INTERNAL ONLY):\n"
            "For ANY prediction or life-event question (marriage, career, "
            "wealth, children, foreign travel, spiritual growth, etc.), you "
            "MUST consult the D9 chart SILENTLY before forming your verdict. "
            "D9 is the 'phaladayak' (fruit-giving) chart. Rules to apply "
            "INTERNALLY (do not narrate them in the answer unless the user "
            "asks for reasoning):\n"
            "  1. Planet STRONG in D1 but WEAK in D9 → result under-delivers.\n"
            "  2. Planet WEAK in D1 but STRONG in D9 (own/exalted/Vargottama) "
            "→ neecha-bhanga, much better than D1 suggests.\n"
            "  3. VARGOTTAMA (same sign in D1 and D9) = doubles the result.\n"
            "  4. Always silently check D9 position of: (a) the topic karaka "
            "(Venus=marriage, Sun=career, Jupiter=wealth/children, "
            "Moon=mind, Mercury=business, Saturn=longevity), (b) the "
            "relevant house lord, (c) D9 lagna and lagna lord.\n"
            "  5. If D1 and D9 disagree, D9 wins for the FINAL outcome.\n"
            "Use this D9 check to ARRIVE at the right verdict. Then output "
            "ONLY the verdict (1-2 sentences) — keep all this reasoning "
            "internal unless the user asks 'why' or 'explain'." + lang_hint
        )

    user_parts = []
    if chart_summary:
        user_parts.append("CHART (quick reference):\n" + chart_summary)

    # Phase 5.2 — Pass the FULL kundli object as raw JSON so the model
    # can answer ANY chart question (D1-D60 divisional charts, full
    # 120-year Vimshottari dasha sequence with dates, transits, yogas,
    # KP sub-lords, ashtakavarga, shadbala, doshas — anything the
    # kundli engine produced). The model is told to look here for any
    # detail not in the quick-reference summary.
    #
    # Phase 5.5 architect-review: when the verdict-lock is active we
    # OMIT FULL_KUNDLI_JSON entirely. Without the raw chart, the model
    # has no material from which to recompute its own verdict — it has
    # only the locked engine output to express. The mini chart summary
    # remains so the model can still say "Aapki Sagittarius lagna mein…"
    # if it wants natural framing, but cannot flip the conclusion.
    if not locked_verdict:
        try:
            if isinstance(kundli, dict) and kundli:
                kundli_json = json.dumps(kundli, ensure_ascii=False, separators=(",", ":"))
                user_parts.append(
                    "FULL_KUNDLI_JSON (authoritative — use this for ANY "
                    "chart detail not in the quick reference above; do NOT "
                    "invent anything outside this object):\n" + kundli_json
                )
        except Exception:
            # Defensive — never fail the prompt build over JSON serialisation.
            pass

    if extra_facts and isinstance(extra_facts, str) and extra_facts.strip():
        user_parts.append("FACTS:\n" + extra_facts.strip())

    if locked_verdict:
        # Lock-mode: ONLY the locked verdict block — no rule checklist,
        # no FULL_KUNDLI_JSON. The system message has been swapped to
        # the narrate-only variant above. Phase 5.5c: detect explain-mode
        # and flip the block's instruction so the model lists the engine
        # reasons instead of just the headline.
        explain_mode = _phase55_is_explain_mode_question(question or "")
        user_parts.append(_phase55_format_locked_verdict_block(
            locked_verdict, explain_mode=explain_mode,
        ))
    else:
        # Phase 5.3 — inject topic-specific classical-rule checklist when
        # the detected topic has well-known Vedic rules (marriage / career
        # / wealth / health). Forces step-by-step rule walking instead of
        # one-indicator confidence. Empty for unknown topics — falls back
        # to general guidance.
        rules_block = _phase53_topic_rules(topic)
        if rules_block:
            user_parts.append(rules_block)

    user_parts.append("QUESTION:\n" + (question or "").strip())

    return [
        {"role": "system", "content": system_msg},
        {"role": "user",   "content": "\n\n".join(user_parts)},
    ]


def _phase50_extract_verdict_facts(build_meta: Any) -> str:
    """Phase 5.0 Final Strip — single shared extractor for engine verdicts.

    Returns a newline-joined facts block (≤6 short lines, possibly empty)
    extracted from the marriage/wealth/love/career/health/stock verdict
    objects on `build_meta`. Used by both ai_ask and ai_ask_stream so the
    minimal-prompt path has exactly ONE source of truth for verdict-fact
    forwarding (no sync/stream drift).
    """
    parts: list[str] = []
    bm = build_meta or {}
    if not isinstance(bm, dict):
        return ""

    # Marriage verdict: multi-line block → first non-empty line only.
    mv = (bm.get("marriage_verdict_block") or "").strip()
    if mv:
        first = next((ln for ln in mv.splitlines() if ln.strip()), "")
        if first:
            parts.append(f"Marriage verdict: {first.strip()}")

    # Wealth verdict object: 1-line summary with optional bucket tag.
    wv = bm.get("wealth_verdict_obj")
    if isinstance(wv, dict):
        v = (wv.get("verdict") or "").strip()
        b = (wv.get("bucket")  or "").strip()
        if v:
            parts.append(f"Wealth verdict: {v}" + (f" ({b})" if b else ""))

    # Other domain verdicts — 1 line each.
    for key, label in [
        ("love_verdict_obj",   "Love verdict"),
        ("career_verdict_obj", "Career verdict"),
        ("health_verdict_obj", "Health verdict"),
        ("stock_verdict_obj",  "Stock verdict"),
    ]:
        o = bm.get(key)
        if isinstance(o, dict):
            v = (o.get("verdict") or o.get("summary") or "").strip()
            if v:
                parts.append(f"{label}: {v}")

    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5.6 — Yoga registry activation (deterministic detection → narration)
# ─────────────────────────────────────────────────────────────────────────────
# Wires the existing yoga detectors (vedic.yogas.classical_yogas,
# vedic.yogas.extra_yogas, vedic.yogas.missing_yogas, chart_intelligence.
# _detect_yogas) into the Phase 5.0 minimal-prompt path. Before Phase 5.6,
# yoga detection ran only in the heavy-prompt LOCKED FACTS pipeline — when
# Phase 5.0 stripped that pipeline (default ON), yoga questions like
# "kitne dhan yog hain?" got vague hallucinated answers because the LLM
# had no yoga facts to cite.
#
# Architecture: same lock pattern as Phase 5.5h KP — engine = source of
# truth, LLM = narrator only. Detector output is injected as an explicit
# YOGA_FACTS block in the user message with citation requirements.
# ─────────────────────────────────────────────────────────────────────────────

# Sign-name → 0-based index mapping (mirrors classical_yogas / extra_yogas).
_PHASE56_SIGN_IDX = {
    "Aries": 0, "Taurus": 1, "Gemini": 2, "Cancer": 3,
    "Leo": 4, "Virgo": 5, "Libra": 6, "Scorpio": 7,
    "Sagittarius": 8, "Capricorn": 9, "Aquarius": 10, "Pisces": 11,
}

# Question-trigger regex: fires when user asks about yogas in any form.
# Compiled once at import. Covers Hindi/Hinglish/English variants.
import re as _re_p56
_PHASE56_YOGA_QUESTION_RE = _re_p56.compile(
    r"\byog[aeo]?s?\b|"                     # yog/yoga/yoge/yogas
    r"\bdhan[- ]?yog|\bdhana[- ]?yog|"      # dhan-yog
    r"\braj[- ]?yog|\brajyog|"              # raj-yog
    r"\blakshmi[- ]?yog|\blaxmi[- ]?yog|"   # lakshmi-yog
    r"\bgaja[- ]?kesari|\bgajakesari|"
    r"\bparivartan|\bparivartana|"
    r"\bpanch[- ]?mahapurush|"
    r"\bvipreet|\bvipareet|"
    r"\bkaal[- ]?sarp|\bkaalsarp|"
    r"\bnabhasa|\bnabhas|"
    r"\bchandra[- ]?mangal|"
    r"\bbudh[- ]?aditya|\bbudhaditya|"
    r"\bmaha[- ]?bhagya|\bmahabhagya|"
    r"\bsaraswati[- ]?yog|"
    r"\bkemadruma|"
    r"\bneech[- ]?bhanga|\bneecha[- ]?bhanga|"
    r"\bdaridra|"
    r"\bguru[- ]?chandal|"
    r"\bsanyas[- ]?yog|\bsannyasa|\bpravrajya|"
    r"\bamala[- ]?yog|"
    r"\badhi[- ]?yog|"
    r"\bsunapha|\banapha|\bdurdhura",
    _re_p56.IGNORECASE,
)

# Mapping from raw detector category → user-facing bucket.
# Detectors emit varied category strings (Dhana/Status/Karaka/Lord-Placement/
# Negative/Nabhasa Sankhya/etc.); we collapse them to the 8 buckets the
# user spec named (dhan/raj/marriage/career/spiritual/negative/nabhasa/special).
_PHASE56_CATEGORY_MAP = {
    # Wealth-bucket
    "Dhana":            ["Dhan"],
    "Wealth-Extras":    ["Dhan"],
    "Lunar-Peripheral": ["Dhan"],
    # Status / fortune (often both dhan AND raj)
    "Status":           ["Dhan", "Raj"],
    # Power / authority
    "Vipreet":          ["Raj"],
    "Pancha-Mahapurusha": ["Raj"],
    "Royal":            ["Raj"],
    "Trinity":          ["Raj"],
    "Neech-Bhanga":     ["Raj"],
    "Aux-Status":       ["Raj"],
    # Negative / arishta
    "Negative":         ["Negative"],
    # Nabhasa (chart-pattern) yogas
    "Nabhasa Sankhya":  ["Nabhasa"],
    "Nabhasa Ashraya":  ["Nabhasa"],
    "Nabhasa Dala":     ["Nabhasa"],
    "Nabhasa Aakriti":  ["Nabhasa"],
    # Spiritual
    "Pravrajya":        ["Spiritual"],
    "Amsavatara":       ["Spiritual"],
    # Special / placement
    "Karaka":           ["Special"],
    "Lord-Placement":   ["Special"],
}

# Question-text → category narrowing. When user explicitly asks about
# a single category, filter the output to just that bucket (otherwise
# show all positive yogas).
_PHASE56_CATEGORY_TRIGGERS = [
    ("Dhan",      _re_p56.compile(r"\bdhan|\bwealth|\bpaisa|\bmoney|\blakshmi|\blaxmi|\bkuber|\bdhana", _re_p56.IGNORECASE)),
    ("Raj",       _re_p56.compile(r"\braj[- ]?yog|\brajyog|\bpower|\bstatus|\bfame|\bpanch[- ]?mahapurush|\bvipreet|\bvipareet", _re_p56.IGNORECASE)),
    ("Marriage",  _re_p56.compile(r"\bmarriage|\bvivah|\bshadi|\bshaadi|\bspouse|\bpati|\bpatni", _re_p56.IGNORECASE)),
    ("Career",    _re_p56.compile(r"\bcareer|\bnaukri|\bnokri|\bjob|\bbusiness|\bvyapar", _re_p56.IGNORECASE)),
    ("Spiritual", _re_p56.compile(r"\bspiritual|\bmoksha|\bsanyas|\bsannyasa|\bpravrajya|\btapasvi", _re_p56.IGNORECASE)),
    ("Negative",  _re_p56.compile(r"\bnegative|\bdosh|\bdaridra|\bgaribi|\bkemadruma|\bguru[- ]?chandal|\bshakat|\bvish[- ]?yog", _re_p56.IGNORECASE)),
    ("Nabhasa",   _re_p56.compile(r"\bnabhasa|\bnabhas|\bmala|\bveena|\byupa|\bsamudra|\bkamala|\bdamaru|\bgada|\bsakata|\bchakra", _re_p56.IGNORECASE)),
]


def _phase56_is_yoga_question(question: Any) -> bool:
    """Return True if the user's question is asking about yogas.

    Defensive against non-string input. Used as the gate for whether
    to compute + inject yoga facts into the minimal-prompt user message.
    """
    if not isinstance(question, str) or not question.strip():
        return False
    return bool(_PHASE56_YOGA_QUESTION_RE.search(question))


def _phase56_question_yoga_category(question: Any) -> str | None:
    """Narrow the yoga response to a single category if the user asked
    about a specific one (e.g. "kitne dhan yog hain?" → "Dhan").

    Returns None when the question is generic ("kitne yog hain?") so
    the formatter shows ALL positive yogas. First trigger wins (priority
    is encoded in the order of `_PHASE56_CATEGORY_TRIGGERS`).
    """
    if not isinstance(question, str) or not question.strip():
        return None
    for cat, pattern in _PHASE56_CATEGORY_TRIGGERS:
        if pattern.search(question):
            return cat
    return None


def _phase56_classify_yoga(yoga: dict) -> list[str]:
    """Map a detector-emitted yoga dict to one or more user-facing
    category buckets. Unknown raw categories fall through to "Special"
    so they still surface (rather than disappear) in the output.
    """
    if not isinstance(yoga, dict):
        return []
    raw_cat = yoga.get("category") or ""
    if not isinstance(raw_cat, str):
        return ["Special"]
    return _PHASE56_CATEGORY_MAP.get(raw_cat, ["Special"])


def _phase56_compute_yoga_facts(kundli: Any) -> dict:
    """Phase 5.6 orchestrator — calls the existing yoga detectors,
    dedupes by canonical name, classifies, and returns a structured
    facts dict ready for formatter consumption.

    OUTPUT shape:
        {
            "total":     int,             # total positive + negative + mixed
            "positive":  int,
            "negative":  int,
            "mixed":     int,
            "by_bucket": {bucket: [yoga_dict, ...]},  # 8 user-facing buckets
            "all":       [yoga_dict, ...],            # deduped, normalised
        }

    Returns empty-default dict on any failure, missing planets, or
    missing lagna — callers must treat empty `all` as "no yoga data".
    Best-effort: never raises. Detector-level exceptions are swallowed
    and logged via stderr for ops visibility.
    """
    empty = {
        "total": 0, "positive": 0, "negative": 0, "mixed": 0,
        "by_bucket": {}, "all": [],
    }
    if not isinstance(kundli, dict):
        return empty
    planets = kundli.get("planets") or []
    if not planets:
        return empty
    asc = kundli.get("ascendant") or kundli.get("lagna")
    asc_sign = asc.get("sign") if isinstance(asc, dict) else asc
    lagna_idx = _PHASE56_SIGN_IDX.get(asc_sign) if isinstance(asc_sign, str) else (
        asc_sign if isinstance(asc_sign, int) and 0 <= asc_sign <= 11 else None
    )
    if lagna_idx is None:
        return empty

    raw: list[dict] = []

    # Detector 1: classical_yogas (dhana/vipreet/negative/kaal-sarp/
    # nabhasa/pravrajya). Returns list[dict] with name/category/polarity/
    # detail keys.
    try:
        from vedic.yogas.classical_yogas import detect_classical_yogas as _dcy
        raw.extend(_dcy(planets, lagna_idx) or [])
    except Exception as _exc:
        print(f"[phase56] classical_yogas failed: {_exc}")

    # Detector 2: extra_yogas (status/karaka/neech-bhanga/lord-placement/
    # trinity/royal/wealth-extras/lunar-peripheral/aux-status/amsavatara).
    try:
        from vedic.yogas.extra_yogas import detect_extra_yogas as _dey
        raw.extend(_dey(planets, lagna_idx) or [])
    except Exception as _exc:
        print(f"[phase56] extra_yogas failed: {_exc}")

    # Detector 3: missing_yogas (indra/shoola — fills gaps).
    try:
        from vedic.yogas.missing_yogas import detect_missing_yogas as _dmy
        raw.extend(_dmy(planets, lagna_idx) or [])
    except Exception as _exc:
        print(f"[phase56] missing_yogas failed: {_exc}")

    # Detector 4: chart_intelligence._detect_yogas — returns list[str]
    # with a different shape; adapt to dict form. Adds Gajakesari,
    # Pancha-Mahapurusha, Budhaditya, Chandra-Mangal, Saraswati, Adhi,
    # Amala, Dharma-Karmadhipati that aren't in the other modules.
    try:
        pmap: dict[str, dict] = {}
        for p in planets:
            if not isinstance(p, dict):
                continue
            name = p.get("name")
            sign = p.get("sign")
            si = _PHASE56_SIGN_IDX.get(sign) if isinstance(sign, str) else None
            if not name or si is None:
                continue
            try:
                deg_in_sign = float(p.get("longitude", 0)) % 30
            except Exception:
                deg_in_sign = 0.0
            pmap[name] = {
                "sign_idx": si,
                "house": p.get("house"),
                "deg_in_sign": deg_in_sign,
            }
        if pmap:
            from chart_intelligence import _detect_yogas as _ciy
            ci_list = _ciy(pmap, lagna_idx) or []
            for s in ci_list:
                if not isinstance(s, str) or not s.strip():
                    continue
                # String shape: "Yoga name (detail...)" — split on first paren.
                first_paren = s.find("(")
                if first_paren > 0:
                    name = s[:first_paren].strip()
                    detail = s[first_paren + 1:].rstrip(")").strip()
                else:
                    name = s.strip()
                    detail = ""
                # Heuristic categorisation by name keywords.
                low = name.lower()
                if "neech" in low or "raja" in low or "gajakesari" in low \
                        or "ruchaka" in low or "bhadra" in low or "hamsa" in low \
                        or "malavya" in low or "sasa" in low or "vipareeta" in low \
                        or "vipreet" in low or "amala" in low or "dharma" in low \
                        or "chamara" in low or "akhanda" in low:
                    raw_cat = "Pancha-Mahapurusha" if any(k in low for k in
                        ("ruchaka", "bhadra", "hamsa", "malavya", "sasa")) else "Royal"
                elif "kemadruma" in low or "shakat" in low or "guru-chandal" in low:
                    raw_cat = "Negative"
                elif "lakshmi" in low or "saraswati" in low or "adhi" in low \
                        or "budhaditya" in low or "chandra-mangal" in low:
                    raw_cat = "Status"
                else:
                    raw_cat = "Special"
                pol = "NEGATIVE" if raw_cat == "Negative" else "POSITIVE"
                raw.append({
                    "name": name, "category": raw_cat,
                    "polarity": pol, "detail": detail,
                    "_source": "chart_intelligence",
                })
    except Exception as _exc:
        print(f"[phase56] chart_intelligence._detect_yogas failed: {_exc}")

    # Dedupe by canonical (case-insensitive, whitespace-collapsed) name.
    seen: set[str] = set()
    deduped: list[dict] = []
    for y in raw:
        if not isinstance(y, dict):
            continue
        name = (y.get("name") or "").strip()
        if not name:
            continue
        key = " ".join(name.lower().split())
        if key in seen:
            continue
        seen.add(key)
        # Defensive copy; ensure required fields present.
        y_clean = {
            "name":     name,
            "category": y.get("category") or "Special",
            "polarity": (y.get("polarity") or "POSITIVE").upper(),
            "detail":   (y.get("detail") or "").strip(),
            "buckets":  _phase56_classify_yoga(y),
        }
        deduped.append(y_clean)

    # Aggregate by bucket + polarity.
    by_bucket: dict[str, list[dict]] = {}
    pos = neg = mix = 0
    for y in deduped:
        for b in y["buckets"]:
            by_bucket.setdefault(b, []).append(y)
        p = y["polarity"]
        if p == "POSITIVE":
            pos += 1
        elif p == "NEGATIVE":
            neg += 1
        else:
            mix += 1

    return {
        "total":     len(deduped),
        "positive":  pos,
        "negative":  neg,
        "mixed":     mix,
        "by_bucket": by_bucket,
        "all":       deduped,
    }


def _phase56_format_yoga_facts_block(
    facts: Any,
    question: str = "",
    history: list | None = None,  # noqa: ARG001 — reserved for context-memory
) -> str:
    """Format yoga facts as a locked block for the minimal-prompt user
    message. Returns "" when no yogas detected so the message stays clean.

    Output shape (when facts are present):

        YOGA_FACTS (deterministic detection from your D1 chart, do NOT recompute):
        Total positive yogas: 11 | negative: 4 | mixed: 1
        Filtered for: Dhan + Raj

        DHAN (4):
        • Mahabhagya yoga (male signature) — Sun, Moon, Lagna all in odd signs
        • Dhana yoga (9L+11L parivartana) — Sun↔Venus sign exchange
        ...

        INSTRUCTION (additive, NOT decisional):
        - Cite the count and yoga names verbatim from above
        - Do NOT invent yoga names not in this list
        - If user asked "kitne" / "how many" → give the count
        - If user asked names / list → list them
        - If a yoga is NOT in the list, do NOT claim it is present

    The instruction follows the same lock semantics as Phase 5.5h KP:
    additive narration, never decisional.
    """
    if not isinstance(facts, dict) or not facts.get("all"):
        return ""

    q_cat = _phase56_question_yoga_category(question)
    by_bucket: dict[str, list[dict]] = facts.get("by_bucket") or {}

    # Decide which buckets to show.
    if q_cat and q_cat in by_bucket and by_bucket[q_cat]:
        buckets_to_show = [q_cat]
        filter_label = q_cat
    else:
        # Generic question: show all buckets that have positive yogas,
        # ordered by importance.
        priority = ["Dhan", "Raj", "Marriage", "Career", "Spiritual",
                    "Special", "Nabhasa", "Negative"]
        buckets_to_show = [b for b in priority
                           if b in by_bucket and by_bucket[b]]
        filter_label = None

    if not buckets_to_show:
        return ""

    lines: list[str] = [
        "YOGA_FACTS (deterministic detection from your D1 chart, do NOT recompute):",
        f"Total positive yogas: {facts.get('positive', 0)} | "
        f"negative: {facts.get('negative', 0)} | "
        f"mixed: {facts.get('mixed', 0)}",
    ]
    if filter_label:
        lines.append(f"Filtered for: {filter_label} category only")
    lines.append("")

    for b in buckets_to_show:
        items = by_bucket.get(b) or []
        if not items:
            continue
        # Sort: positive first, then mixed, then negative.
        order = {"POSITIVE": 0, "MIXED": 1, "NEGATIVE": 2}
        items_sorted = sorted(items, key=lambda y: order.get(y.get("polarity"), 3))
        lines.append(f"{b.upper()} ({len(items_sorted)}):")
        for y in items_sorted[:8]:
            tag = {"POSITIVE": "✓", "NEGATIVE": "✗", "MIXED": "◐"}.get(
                y.get("polarity"), "•")
            detail = y.get("detail") or ""
            if len(detail) > 90:
                detail = detail[:87] + "..."
            line = f"  {tag} {y.get('name', '?')}"
            if detail:
                line += f" — {detail}"
            lines.append(line)
        if len(items_sorted) > 8:
            lines.append(f"  … (+{len(items_sorted) - 8} more in this category)")
        lines.append("")

    lines.extend([
        "INSTRUCTION (yoga layer — additive, NOT decisional):",
        "- Cite the count and yoga names VERBATIM from the YOGA_FACTS above.",
        "- If the user asked 'kitne' / 'how many', state the count clearly.",
        "- If the user asked for names or a list, list them (do NOT skip).",
        "- Do NOT invent yoga names that are NOT in YOGA_FACTS above.",
        "- Do NOT claim a yoga is present if it is not in the list.",
        "- Keep the explanation concise and grounded in the listed yogas.",
    ])

    return "\n".join(lines)


def _phase50_install_minimal_messages(
    question: str,
    kundli: Any,
    lang: str,
    build_meta: Any,
    req_id: str,
    path_label: str = "",
    topic: str | None = None,
    history: list | None = None,
) -> tuple[list[dict], dict]:
    """Phase 5.0 Final Strip — unified gate body for ai_ask + ai_ask_stream.

    Performs the full minimal-prompt installation atomically:
      1. Extract engine verdict facts from `build_meta` (shared logic).
      2. Phase 5.6 — append yoga facts when question is yoga-related.
      3. Build the 2-message minimal prompt.
      4. Emit the `[openai_helper] Phase 5.0:` console line + the
         `2x.PHASE50_MINIMAL_ACTIVE` trace event.
      5. Return (messages, telemetry) for the caller to assign.

    `path_label` is appended to the trace event key (e.g. "(stream)") so
    sync vs stream paths remain distinguishable in the trace; callers
    pass "" for sync and "(stream)" for the stream path.
    """
    facts = _phase50_extract_verdict_facts(build_meta)

    # Phase 5.6 — yoga facts injection (only when question matches).
    yoga_block = ""
    yoga_telemetry = {"yoga_active": False}
    if _phase56_is_yoga_question(question):
        try:
            yoga_facts = _phase56_compute_yoga_facts(kundli)
            yoga_block = _phase56_format_yoga_facts_block(
                yoga_facts, question=question or "", history=history,
            )
            if yoga_block:
                yoga_telemetry = {
                    "yoga_active":   True,
                    "yoga_total":    yoga_facts.get("total", 0),
                    "yoga_positive": yoga_facts.get("positive", 0),
                    "yoga_negative": yoga_facts.get("negative", 0),
                    "yoga_q_cat":    _phase56_question_yoga_category(question),
                }
                facts = (facts + "\n\n" + yoga_block) if facts else yoga_block
        except Exception as _exc:
            # Yoga injection is best-effort — never break the Ask path.
            print(f"[openai_helper] Phase 5.6 yoga injection failed: {_exc}")

    facts_lines = len([ln for ln in facts.splitlines() if ln.strip()]) if facts else 0
    messages = _phase50_build_minimal_messages(
        question or "", kundli, lang=lang,
        tier=None, extra_facts=facts, topic=topic,
        history=history,
    )
    try:
        user_chars = len(messages[1]["content"])
    except Exception:
        user_chars = 0
    print(
        f"[openai_helper] Phase 5.0{path_label}: minimal-prompt active — "
        f"user_chars={user_chars} facts_lines={facts_lines} "
        f"yoga_active={yoga_telemetry['yoga_active']} "
        f"(heavy assembly bypassed)"
    )
    telemetry = {
        "user_chars":    user_chars,
        "facts_lines":   facts_lines,
        "message_count": len(messages),
        "roles":         [m["role"] for m in messages],
        **yoga_telemetry,
    }
    _trace(req_id, f"2x.PHASE50_MINIMAL_ACTIVE{path_label}", telemetry)
    return messages, telemetry


def _phase50_minimal_prompt_enabled() -> bool:
    """Read the env flag once per call. Default ON ("1")."""
    import os as _os_p50
    return _os_p50.environ.get("PHASE50_MINIMAL_PROMPT", "1") != "0"


# ── Phase 5.1 — TOTAL STRIP ─────────────────────────────────────────────────
# When PHASE51_BARE_PROMPT=1 (default), the Ask path runs ONLY:
#   1. engine compute (kundli + verdicts via existing _build_messages call)
#   2. Phase 5.0 minimal-prompt assembly (system + user, ~500-char chart)
#   3. ONE OpenAI chat.completions.create call
#   4. RAW model output → returned as `text` (no mutation, no validators)
#
# Everything else in the post-response chain is BYPASSED via early-return:
#   - SUPERTYPE_CONTRACT validator + retry        (was already inert)
#   - POST_LOGIC_CHECK (date/dasha hallucination guard)
#   - TIMING_VALIDATOR (timing-claim authorisation)
#   - JARGON_INJECT (Sanskrit jargon back-injection)
#   - HEALTH_BRAND_SAFETY (CA/SEBI medical disclaimer)
#   - VALIDATORS framework + RAW_AI_REGEN
#   - MARRIAGE_VALIDATOR + RAW_AI_REGEN(marriage)
#   - WEALTH_BRAND_SAFETY (SEBI investment disclaimer)
#   - SCRUBBER (brand-tone style rewriter)         (was already skipped)
#   - phase48 TRUNCATOR (tier/format controller)   (was already skipped)
#   - GLOBAL_PH_STRIP (placeholder `[…]` strip)
#   - POST_LOGIC_CHECK_POST_TIMING (second-pass guard)
#   - ENGINE_WARNING_INJECTED footer
#   - FOLLOW_UPS chip generation                   (returns [])
#
# Reversibility: setting PHASE51_BARE_PROMPT=0 restores the Phase 5.0 path
# (which itself can be reverted via PHASE50_MINIMAL_PROMPT=0). Both flags
# are independent. Default cascade: 5.1 ON → 5.0 ON → engines + minimal +
# raw output, no validators of any kind.
def _phase51_bare_prompt_enabled() -> bool:
    """Read the env flag once per call. Default ON ("1")."""
    import os as _os_p51
    return _os_p51.environ.get("PHASE51_BARE_PROMPT", "1") != "0"


def _phase48_narrative_truncate(text: str, question: str,
                                tier: str | None = None) -> str:
    """Phase 4.8 T019 + Phase 4.9 T024 — tier-aware narrative truncator.

    Tier behaviour:
      • 'simple'    (default): ≤2 sentences, ≤280 chars; non-timing Qs
                     also drop date / pratyantar / antardasha sentences.
      • 'detailed': ≤5 sentences, ≤600 chars; strip date ranges only,
                     keep planet/dasha-name explanations.
      • 'technical': pass-through (returns text unchanged) so KP /
                     dasha-breakdown / houses answers survive intact.

    `tier` is computed from `question` via `_question_depth_tier` when
    not supplied. Idempotent on already-conformant input.
    """
    import re as _reN

    if not isinstance(text, str) or not text.strip():
        return text

    if tier is None:
        tier = _question_depth_tier(question)

    # ── Tier 3: pass-through. User asked for the full technical answer. ──
    if tier == "technical":
        return text

    is_timing = _phase48_is_timing_question(question)

    # Per-tier caps.
    if tier == "detailed":
        max_sents = 5
        max_chars = 600
        # Detailed answers may legitimately mention dasha lord names
        # ("Mars antardasha mein…") so we DO NOT drop sentences just
        # because they reference a sub-period — only ISO date ranges
        # are stripped.
        drop_pratyantar_sentences = False
    else:  # 'simple'
        max_sents = 2
        max_chars = 280
        drop_pratyantar_sentences = True

    # ── Step 2: TIMING FILTER (only if NOT a timing question) ──
    if not is_timing:
        date_rx = _reN.compile(
            r"\(?\b\d{4}-\d{2}-\d{2}(?:\s+se\s+\d{4}-\d{2}-\d{2})?\)?"
            r"|\b(?:January|February|March|April|May|June|July|"
            r"August|September|October|November|December|"
            r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
            r"\s+\d{4}\b"
            r"|\b\d{4}\s+(?:tak|se|ke\s+baad|mein|me|ko)\b"
        )
        pratyantar_sent_rx = _reN.compile(
            r"(?i)\b("
            # Architect-flagged spelling variants:
            #   antardasha / antardasa (without 'h') / antar dasha / antar-dasha
            #   pratyantar / pratyantardasha (full word)
            r"pratyantar(?:dasha)?|"
            r"antardash[ae]|antar\s*dash[ae]|antar-dash[ae]|"
            r"sookshma|sukshma|"
            r"mahadasha\s+\w+\s+(?:aur|and)\s+\w+\s+antardash[ae]|"
            r"\d{4}-\d{2}-\d{2}"
            r")\b"
        )
        raw_sents = [
            s.strip() for s in
            _reN.split(r"(?<=[.!?।])\s+", text)
            if s.strip()
        ]
        kept = []
        for s in raw_sents:
            if drop_pratyantar_sentences and pratyantar_sent_rx.search(s):
                continue
            stripped = date_rx.sub("", s).strip()
            stripped = _reN.sub(r"\s{2,}", " ", stripped)
            stripped = _reN.sub(r"\(\s*\)|\[\s*\]", "", stripped).strip()
            if len(stripped.split()) >= 3:
                kept.append(stripped)
        if kept:
            text = " ".join(kept)

    # ── Step 3: HARD LENGTH CUT — first N sentences max (per tier) ──
    final_sents = [
        s.strip() for s in
        _reN.split(r"(?<=[.!?।])\s+", text)
        if s.strip()
    ]
    if len(final_sents) > max_sents:
        text = " ".join(final_sents[:max_sents])
        if text and text[-1] not in ".!?।":
            text = text + "."

    # ── Step 4: HARD CHAR CAP — per tier ──
    if len(text) > max_chars:
        cut = text[:max_chars]
        last_punct = max(
            cut.rfind("."), cut.rfind("!"),
            cut.rfind("?"), cut.rfind("।"),
        )
        if last_punct > 80:
            text = cut[:last_punct + 1]
        else:
            text = cut.rstrip() + "…"

    return text


def ai_ask(question: str, kundli: Any, lang: str = "en", reply_idx: int = 0,
           birth: Any = None, history: list | None = None,
           preferred_language: Optional[str] = None) -> dict:
    """
    Returns: { text, topic, confidence, source, follow_ups }
    Raises:  RuntimeError on any OpenAI / config failure (caller falls back).
    """
    req_id = _short_id()
    has_planets_in = isinstance(kundli, dict) and bool(kundli.get("planets"))
    has_dasha_in   = isinstance(kundli, dict) and bool(kundli.get("currentDasha"))
    _trace(req_id, "1.RAW_INPUT", {
        "question": question,
        "lang_param": lang,
        "preferred_language": preferred_language,
        "reply_idx": reply_idx,
        "history_len": len(history or []),
        "history_last_roles": [h.get("role") for h in (history or [])[-4:]],
        "kundli.has_planets": has_planets_in,
        "kundli.has_dasha":   has_dasha_in,
        "kundli.planet_count": len((kundli or {}).get("planets") or []) if has_planets_in else 0,
        "birth.has_coords":   isinstance(birth, dict) and birth.get("lat") is not None,
    })

    # ── Sprint-26: AI-ONLY Question Understanding (single source of truth) ───
    # ONE classifier call → {intent, topic, confidence}. No regex pipeline,
    # no AI-Ear merge, no override layers. Replaces the entire Sprint-23/24/25
    # multi-source understanding stack. Falls back to a minimal regex ONLY
    # when AI confidence < 0.6 OR the call itself errors (safety-net).
    from question_understanding import (
        understand_question, supertype_for, has_recovery_subask,
    )
    _qu = understand_question(question)
    # Sprint-26 Fix-Q — deterministic recovery sub-ask detector. Adds a
    # boolean flag to the understanding dict so downstream wealth structured
    # output and the GENERAL_ANALYSIS narrator contract can demand a Recovery
    # line in the answer when the user explicitly asked about it. Does NOT
    # add a new INTENTS enum value (which would ripple into supertype/router
    # changes) — it's a sibling flag the relevant consumers read.
    _qu["has_recovery_subask"] = has_recovery_subask(question)
    _trace(req_id, "1.UNDERSTANDING", _qu)
    # Phase 4.1 Fix-P — surface classifier sanity-layer override decisions
    # as a separate, easy-to-grep telemetry event. Fires only when the
    # override actually changed the intent (override metadata is set by
    # _apply_classifier_sanity_layer in question_understanding.py).
    if _qu.get("intent_overridden_from"):
        _trace(req_id, "1b.CLASSIFIER_OVERRIDE", {
            "from":   _qu.get("intent_overridden_from"),
            "to":     _qu.get("intent"),
            "reason": _qu.get("intent_override_reason"),
            "phase":  _qu.get("intent_override_phase"),
            "ai_confidence": _qu.get("confidence"),
        })

    _qu_intent = (_qu.get("intent") or "analysis").lower()
    _qu_topic  = (_qu.get("topic")  or "general").lower()
    _qu_conf   = float(_qu.get("confidence") or 0.0)
    _qu_source = _qu.get("source") or "ai"

    # Sprint-26 Fix-M — multi-intent priority + multi-domain awareness.
    # Default everything to single-element lists so any code that doesn't
    # understand the new fields still works.
    _qu_intents_ranked = _qu.get("intents_ranked") or [_qu_intent]
    _qu_topics_all     = _qu.get("topics_all")     or [_qu_topic]
    _qu_hidden_intent  = _qu.get("hidden_intent")  # None when no hidden layer
    _qu_cross_domain   = bool(_qu.get("cross_domain_root_cause")) and len(_qu_topics_all) >= 2

    # Legacy-shape question_intent so the response payload + brevity guards
    # continue to work without touching downstream code.
    question_intent = {
        "intent":     f"{_qu_intent}_general",  # legacy compound label
        "subjects":   [],
        "scope":      "general",
        "confidence": _qu_conf,
        "source":     _qu_source,
        "raw_intent": _qu_intent,
        "raw_topic":  _qu_topic,
        # Sprint-26 Fix-M — multi-intent diagnostics
        "intents_ranked":          _qu_intents_ranked,
        "topics_all":              _qu_topics_all,
        "hidden_intent":           _qu_hidden_intent,
        "cross_domain_root_cause": _qu_cross_domain,
        # Sprint-26 Fix-Q — recovery sub-ask flag (forwarded to wealth
        # structured-output prompt + GENERAL_ANALYSIS narrator contract).
        "has_recovery_subask":     bool(_qu.get("has_recovery_subask")),
    }
    _trace(req_id, "1b.QUESTION_INTENT", question_intent)
    if len(_qu_intents_ranked) > 1 or len(_qu_topics_all) > 1 or _qu_hidden_intent or _qu_cross_domain:
        _trace(req_id, "1c.MULTI_INTENT", {
            "primary":    _qu_intents_ranked[0] if _qu_intents_ranked else _qu_intent,
            "secondary":  _qu_intents_ranked[1] if len(_qu_intents_ranked) > 1 else None,
            "tertiary":   _qu_intents_ranked[2] if len(_qu_intents_ranked) > 2 else None,
            "domains":    _qu_topics_all,
            "hidden":     _qu_hidden_intent,
            "cross_domain_root_cause": _qu_cross_domain,
        })

    # ── Brand-safety: refuse off-topic / fortune-telling questions WITHOUT
    # calling the LLM at all. Cheap, deterministic, never leaks chart data.
    if _is_brand_unsafe(question):
        eff_lang = _resolve_response_lang(question, lang, preferred_language)
        msg = _BRAND_SAFE_REDIRECT.get(eff_lang) or _BRAND_SAFE_REDIRECT["hn"]
        return {
            "text":       msg,
            "topic":      "off_topic",
            "topic_source": "brand_guard",
            "confidence": 1.0,
            "source":     "brand_guard",
            "follow_ups": _derive_follow_ups("general", _resolve_response_lang(question, lang, preferred_language)),
            "question_intent": question_intent,
            "question_supertype": {
                "supertype":     supertype_for(_qu_intent),
                "confidence":    _qu_conf,
                "source":        _qu_source,
                "source_intent": _qu_intent,
            },
            "intent_extraction": None,
        }

    # ── Fail-safe: if no kundli planets at all AND this is a personal
    # prediction question (astro mode), never call the LLM. The spec demands
    # "DO NOT GUESS" — invented planet positions are the worst possible
    # failure mode for an astrology app's credibility. General-mode concept
    # questions ("kp vs vedic kya hai") don't need a chart and skip this.
    has_planets = isinstance(kundli, dict) and bool(kundli.get("planets"))
    # Sprint-26: mode is derived from the AI understanding result. A pure
    # concept question (intent=analysis + topic=general) doesn't need a chart;
    # everything else does.
    _early_mode = "general" if (_qu_intent == "analysis" and _qu_topic == "general") else "astro"
    _early_reason = f"qu intent={_qu_intent} topic={_qu_topic}"
    # Sprint-26 Fix-O — Personal-chart override: if the user named a personal
    # chart anchor ("mera dasha", "meri kundli", "mera lagna", "mere chart",
    # "meri birth", planet possessives, Devanagari forms), they are asking
    # about THEIR chart, not a generic concept. Force mode=astro so the
    # chart pipeline runs and the narrator can cite real MD/AD/lord names
    # from the kundli — even if the AI classifier marked topic=general.
    if _early_mode == "general":
        try:
            from question_understanding import is_personal_chart_question
            if is_personal_chart_question(question):
                _early_mode = "astro"
                _early_reason = (f"qu intent={_qu_intent} topic={_qu_topic} "
                                 f"→ FORCED astro (personal-chart anchor "
                                 f"in question, Fix-O)")
                _trace(req_id, "2.MODE_DETECT.personal_chart_override", {
                    "rule": "Sprint-26 Fix-O",
                    "reason": "personal possessive next to chart noun",
                })
        except Exception:
            pass
    if not has_planets and _early_mode == "astro":
        _trace(req_id, "2.MODE_DETECT",
               {"mode": _early_mode, "reason": _early_reason,
                "next": "no_chart_failsafe (no planets + astro mode)"})
        eff_lang = _resolve_response_lang(question, lang, preferred_language)
        no_chart_msg = {
            "en": ("Beta, your full birth-chart isn't with me yet — without it I cannot honestly predict timing or specifics. "
                   "Please save your birth details (date, exact time, and place) first; once I can see your kundli, I will guide you with full clarity."),
            "hi": ("बेटा, अभी मेरे पास आपकी पूरी जन्म-कुंडली नहीं है — इसके बिना मैं ईमानदारी से कोई समय या विशेष भविष्यवाणी नहीं कर सकता। "
                   "कृपया पहले अपना जन्म विवरण (तिथि, सही समय और स्थान) सहेजें; जैसे ही मैं आपकी कुंडली देख सकूँगा, पूरी स्पष्टता से मार्गदर्शन दूँगा।"),
            "hn": ("Beta, abhi mere paas aapki poori janm-kundli nahi hai — iske bina mai imaandari se koi timing ya specific bhavishyavani nahi kar sakta. "
                   "Kripya pehle apna janm vivran (date, sahi samay, aur sthan) save karein; jaise hi mai aapki kundli dekh paunga, poori spashtata se margdarshan dunga."),
        }.get(eff_lang) or ("Beta, abhi mere paas aapki poori janm-kundli nahi hai — iske bina mai imaandari se koi timing ya specific bhavishyavani nahi kar sakta. "
                            "Kripya pehle apna janm vivran (date, sahi samay, aur sthan) save karein; jaise hi mai aapki kundli dekh paunga, poori spashtata se margdarshan dunga.")
        _t = _qu_topic
        return {
            "text":       no_chart_msg,
            "topic":      _t,
            "topic_source": "no_chart_failsafe",
            "confidence": 0.0,
            "source":     "no_chart_failsafe",
            "follow_ups": _derive_follow_ups(_t, eff_lang),
            "question_intent": question_intent,
            "question_supertype": {
                "supertype":     supertype_for(_qu_intent),
                "confidence":    _qu_conf,
                "source":        _qu_source,
                "source_intent": _qu_intent,
            },
            "intent_extraction": None,
        }

    client = _get_client()
    if client is None:
        raise RuntimeError(_client_err or "OpenAI client not configured")

    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

    # ── Sprint-26: Routing derived from the SINGLE understanding result ──────
    # All previous regex / AI-Ear / supertype-override layers are removed.
    # `_qu_intent` and `_qu_topic` (set above) are the ONLY routing inputs.
    topic = _qu_topic
    mode  = _early_mode  # already derived from _qu above
    _topic_source = _qu_source

    # ── TOPIC STICKINESS for marriage follow-ups (multi-turn context only) ──
    # NOT question understanding — this is conversation context. Constraint
    # follow-ups ("uske baad batao", "iska upay batao") don't carry topic
    # keywords; we look at the previous assistant turn to keep marriage
    # threads sticky so the baked-answer path keeps firing.
    try:
        if topic != "marriage" and (
            _detect_marriage_constraint(question, history or [])
            or (_is_generic_followup(question)
                and _last_assistant_topic_was_marriage(history or []))
        ):
            for h in reversed(history or []):
                if (h.get("role") == "assistant"):
                    prev = ((h.get("content") or h.get("text") or "")).lower()
                    if any(k in prev for k in
                           ("vivah", "shaadi", "shadi", "marriage",
                            "विवाह", "शादी", "spouse", "wife", "husband")):
                        topic = "marriage"
                        _topic_source = "stickiness"
                        print("[ai_ask] topic stickiness: forced topic=marriage")
                        break
    except Exception as exc:
        print(f"[ai_ask] topic-stickiness check failed: {exc}")

    # General-mode concept questions never need a chart-bound topic.
    if mode == "general":
        topic = "general"

    # ── Phase 5.5d (Apr 29 2026) — CONTEXT-MEMORY MODE OVERRIDE ─────────────
    # Bare follow-ups like "kaise check kiya?" / "explain karo" / "kyun?"
    # carry no domain anchor, so the AI Ear classifies them as
    # mode=general — which BYPASSES the entire chart pipeline (and the
    # Phase 5.5 lock with it). Detect the case where the previous
    # assistant turn delivered a love-vs-arrange verdict AND the current
    # question is a bare explain trigger; force mode=astro + topic=marriage
    # so the lock engages with full engine reasoning.
    #
    # Narrowly scoped — only fires when the history-based path (Path 3 of
    # the Phase 5.5d detector) is the trigger; explicit love/arrange
    # questions are unaffected. No-op if mode is already astro.
    if (mode != "astro"
            and _phase55_history_was_love_vs_arrange(history)
            and _phase55_is_love_vs_arrange_question(question or "",
                                                     history=history)):
        print("[ai_ask] Phase 5.5d context override: "
              "forcing mode=astro topic=marriage (LvA follow-up)")
        mode = "astro"
        topic = "marriage"
        _topic_source = "phase55d_context_memory"
        _early_reason = (
            "phase55d context-memory: bare follow-up after love-vs-arrange"
        )

    _trace(req_id, "2.MODE_DETECT", {
        "mode": mode, "topic": topic, "topic_source": _topic_source,
        "reason": _early_reason,
    })

    # Marriage subtype (timing / remedy / analysis) — sub-classifier kept
    # because it drives a different narrator template, not the engine choice.
    marriage_subtype = (
        _classify_marriage_subtype(question) if topic == "marriage" else "timing"
    )
    _trace(req_id, "2.MODE_DETECT.subtype", {
        "topic": topic, "marriage_subtype": marriage_subtype,
    })

    # ── Supertype: derived directly from the AI intent ──────────────────────
    question_supertype = {
        "supertype":     supertype_for(_qu_intent),
        "confidence":    _qu_conf,
        "source":        _qu_source,
        "source_intent": _qu_intent,
    }
    build_meta: dict = {
        "question_intent":     question_intent,
        "question_supertype":  question_supertype,
        "intent_extraction":   None,   # legacy field; AI-Ear is gone
        "topic":               topic,
        "topic_source":        _topic_source,
        "understanding":       _qu,
    }
    _trace(req_id, "2d.QUESTION_SUPERTYPE", {
        "supertype":     question_supertype["supertype"],
        "confidence":    question_supertype["confidence"],
        "source":        question_supertype["source"],
        "source_intent": question_supertype["source_intent"],
    })

    # Single canonical telemetry line — same shape as before so metrics work.
    _trace(req_id, "2.UNDERSTANDING_TELEMETRY", {
        "intent":         _qu_intent,
        "topic":          topic,
        "supertype":      question_supertype["supertype"],
        "confidence":     _qu_conf,
        "source":         _qu_source,
        "topic_source":   _topic_source,
        "mode":           mode,
        "latency_ms":     _qu.get("latency_ms"),
    })

    # ── Sprint-26 Step 4 Phase 2 — Safe-Narration Gate (deterministic) ─────
    # Fires BEFORE _build_messages so the LLM is never called for gated
    # responses. Currently implements GUARD-2 (domain clarification when
    # the question describes a sustained problem with no domain anchor).
    _gate_response = _safe_narration_gate(
        _qu, _qu_intent, mode, topic, _topic_source,
        question_intent, question_supertype, req_id,
    )
    if _gate_response is not None:
        return _gate_response

    messages = _build_messages(
        question, kundli, lang, reply_idx,
        birth=birth, topic=topic, history=history,
        preferred_language=preferred_language,
        mode=mode,
        out_meta=build_meta,
        marriage_subtype=marriage_subtype,
    )

    # Sprint-26 Fix-K: trace engine status (populated by _build_messages
    # via out_meta) so we can see which phases ran/failed and reason
    # about the smart-validator decision downstream.
    _engine_status = (build_meta or {}).get("engine_status") or {}
    _trace(req_id, "2b.ENGINE_STATUS", {
        "overall": _engine_status.get("overall"),
        "ok_count": len(_engine_status.get("ok") or []),
        "skipped_count": len(_engine_status.get("skipped") or []),
        "failed_count": len(_engine_status.get("failed") or []),
        "failed": [e.get("phase") for e in (_engine_status.get("failed") or [])],
        "skipped": [e.get("phase") for e in (_engine_status.get("skipped") or [])],
    })

    # ── Phase 5.0 (Apr 28 2026) — MINIMAL ASK PROMPT GATE ───────────────────
    # When PHASE50_MINIMAL_PROMPT=1 (default), discard the heavy multi-system
    # `messages` list built above and replace it with a 2-message minimal
    # prompt. The expensive engines still ran (their facts flow into the
    # `extra_facts` line), but the LLM never sees:
    #   • UNIFIED NARRATOR CONTRACT preamble
    #   • Per-supertype contract (GENERAL_ANALYSIS / TIMING / ...)
    #   • Heavy Rule 1-N + KP forcing + locked_facts dump
    #   • Multiple system prompts
    # Downstream guards still fire: TIMING_VALIDATOR, POST_LOGIC_CHECK,
    # phase48-trim (Phase 4.9 truncator). One-line revert by setting the
    # env flag to "0".
    _phase50_active = False
    if mode == "astro" and _phase50_minimal_prompt_enabled():
        # Single-call install — verdict-fact extraction, message build,
        # and telemetry all live in `_phase50_install_minimal_messages`
        # so the stream path uses identical logic (no sync/stream drift).
        messages, _ = _phase50_install_minimal_messages(
            question or "", kundli, lang, build_meta, req_id, path_label="",
            topic=topic, history=history,
        )
        _phase50_active = True

    # ── Sprint-26 Fix-M — Cross-Domain Root-Cause Block ─────────────────────
    # When the user asks a dual-domain "same reason or different" question,
    # compute the deterministic cross-domain check and APPEND it to the
    # system prompt so the AI can answer the comparison without guessing.
    # Phase 5.0: skipped when minimal-prompt path is active (no system msg
    # to append to; verdict facts already flow via extra_facts).
    if (not _phase50_active) and _qu_cross_domain and isinstance(kundli, dict) and kundli.get("planets"):
        try:
            _xd = _compute_cross_domain_facts(kundli, _qu_topics_all)
            if _xd.get("text") and messages and isinstance(messages[0], dict):
                _xd_block = (
                    "\n\n════ CROSS-DOMAIN ROOT-CAUSE CHECK (engine-verified) ════\n"
                    f"{_xd['text']}\n"
                    "Use this block VERBATIM to answer 'ek hi reason hai ya alag'. "
                    "Do NOT invent psychological / behavioural causes — cite ONLY "
                    "what the engine verdict says above.\n"
                    "═══════════════════════════════════════════════════════════"
                )
                messages[0]["content"] = (messages[0].get("content") or "") + _xd_block
                _trace(req_id, "2c.CROSS_DOMAIN_FACTS", _xd.get("summary") or {})
        except Exception as _xd_exc:
            _trace(req_id, "2c.CROSS_DOMAIN_FAILED", {"error": str(_xd_exc)[:200]})

    # ── WEALTH STRUCTURED-OUTPUT REWRITE ─────────────────────────────────────
    # When the wealth verdict engine produced a verdict_obj, we strip the
    # verbose ~100-line WEALTH NARRATOR OVERRIDE that _build_messages
    # appended and replace it with the short structured-output prompt.
    # The model is then forced into JSON-schema mode (see _call_once below).
    _wealth_obj = (build_meta or {}).get("wealth_verdict_obj")
    _wealth_structured_payload: dict | None = None
    # Phase 4.5 NARRATIVE_MODE: bypass the wealth json_schema structured-
    # output path entirely. That path forces the model to emit a fixed
    # `{verdict, headline, what_will_happen, what_to_do, what_to_avoid,
    # remedy, note}` JSON which `_format_wealth_structured_payload` then
    # renders into the V→R→T template (Score badge / 📅 Window / Kya hoga
    # bullets / 🕉 Upay / CA-SEBI cite). When NARRATIVE_MODE is on, we
    # skip the prompt install AND the json_schema call so the unified
    # narrative contract (`_NARRATIVE_NARRATOR_BODY`) drives the answer.
    # The wealth engine still runs and its verdict facts (window, lord,
    # bucket) flow into `truth_facts` for the AI to ground on.
    # Phase 5.0: minimal-prompt path bypasses ALL contract installs
    # (including the wealth json_schema structured-output prompt).
    _use_wealth_structured_path = (
        isinstance(_wealth_obj, dict) and bool(_wealth_obj)
        and not _NARRATIVE_MODE
        and not _phase50_active
    )
    if _use_wealth_structured_path:
        messages = [
            m for m in messages
            if not (m.get("role") == "system"
                    and "WEALTH NARRATOR OVERRIDE" in (m.get("content") or ""))
        ]
        # ── Phase 2: pull AI Ear's emotional_tone + domain + ask_types so
        #            the wealth structured prompt can inject the EMOTIONAL
        #            TREATMENT DIRECTIVE for empathy_open / human_close.
        _ear = (build_meta or {}).get("intent_extraction") or {}
        _wealth_tone   = (_ear.get("emotional_tone") or "neutral")
        _wealth_domain = (_ear.get("domain")         or "wealth")
        _wealth_asks   = list(_ear.get("ask_types")  or [])
        _wealth_lang   = (_ear.get("language")       or "hn")
        # Sprint-26 Fix-Q — propagate recovery sub-ask flag so the prompt
        # builder demands a `recovery_outlook` line when the user asked it.
        _wealth_recovery = bool(question_intent.get("has_recovery_subask"))
        messages.append({
            "role":    "system",
            "content": _build_wealth_structured_system_prompt(
                _wealth_obj,
                emotional_tone = _wealth_tone,
                intent_domain  = _wealth_domain,
                ask_types      = _wealth_asks,
                narrator_lang  = _wealth_lang,
                has_recovery_subask = _wealth_recovery,
            ),
        })
        _trace(req_id, "2c.WEALTH_STRUCTURED_PROMPT_INSTALLED", {
            "bucket":  _wealth_obj.get("bucket"),
            "tense":   _wealth_obj.get("tense"),
            "verdict": _wealth_obj.get("verdict"),
            "score":   _wealth_obj.get("score"),
            "tone":    _wealth_tone,
            "domain":  _wealth_domain,
            "has_recovery_subask": _wealth_recovery,
        })

    # ── Sprint-24: STRICT NARRATOR CONTRACT (per supertype) ─────────────────
    # Inject the per-supertype response-rules block as the LAST system msg
    # so it gets recency-lock priority over every earlier system message
    # (chart, brand voice, engine verdict).
    #
    # SKIP CONDITIONS (each owns its own strict prompt — adding a second
    # contract creates a "prompt battle" that produces inconsistent output):
    #   • mode == "general" — concept-explainer pipeline, no chart/engine.
    #   • _wealth_obj present — wealth path forces response_format=json_schema
    #     (line ~5562). Appending a free-text MUST/MUST-NOT contract right
    #     before a JSON-schema call risks schema violations or the model
    #     dropping required fields trying to satisfy the prose contract.
    #   • topic == "marriage" with marriage_verdict_block present — the
    #     MARRIAGE NARRATOR mode already injects its own detailed
    #     UL/templates/MUST rules; a second contract dilutes them.
    _skip_contract_reason = ""
    if _phase50_active:
        # Phase 5.0: minimal-prompt path owns the entire prompt — no
        # contract install, no narrator preamble, no per-supertype rules.
        _skip_contract_reason = "phase50 minimal-prompt path"
    elif mode != "astro":
        _skip_contract_reason = "mode=general (no chart pipeline)"
    elif _use_wealth_structured_path:
        # Only skip the supertype contract when the json_schema wealth path
        # is actually about to fire. In NARRATIVE_MODE we WANT the unified
        # narrative contract installed even on wealth questions.
        _skip_contract_reason = "wealth structured-output (json_schema mode)"
    elif (topic == "marriage"
          and (build_meta or {}).get("marriage_verdict_block")
          and not _NARRATIVE_MODE):
        # Phase 4.5: marriage narrator mode also overrides the prompt with
        # its own V→R→T contract. Let the narrative contract take over in
        # narrative mode so marriage answers get the same flowing format.
        _skip_contract_reason = "marriage narrator mode owns the prompt"

    if not _skip_contract_reason:
        _supertype_tag = (question_supertype or {}).get("supertype") or "GENERAL_ANALYSIS"
        try:
            # Sprint-26 Step 1 — unified narrator contract. Forward the
            # recovery sub-ask flag so the contract builder can route it to
            # any future conditional sections (currently the GENERAL_ANALYSIS
            # Recovery clause is inline; Step 2 may trim it dynamically).
            messages.append({
                "role":    "system",
                "content": _build_supertype_contract(
                    _supertype_tag,
                    has_recovery_subask=bool(
                        question_intent.get("has_recovery_subask")
                    ),
                ),
            })
            _trace(req_id, "2e.SUPERTYPE_CONTRACT_INSTALLED", {
                "supertype": _supertype_tag,
                "position":  len(messages) - 1,
                "has_recovery_subask": bool(
                    question_intent.get("has_recovery_subask")
                ),
            })
        except Exception as _sup_exc:
            _trace(req_id, "2e.SUPERTYPE_CONTRACT_FAIL",
                   {"error": str(_sup_exc)[:200]})
    else:
        _trace(req_id, "2e.SUPERTYPE_CONTRACT_SKIPPED",
               {"reason": _skip_contract_reason,
                "supertype": (question_supertype or {}).get("supertype")})

    # ── Mode/topic-aware sampling ────────────────────────────────────────────
    # Marriage astro AND wealth structured both use deterministic verdict
    # engines — AI is narrator only. Force temp=0.0 to lock outputs.
    if (mode == "astro" and topic == "marriage") or _wealth_obj:
        temperature       = 0.0
        presence_penalty  = 0.0
        frequency_penalty = 0.0
    else:
        temperature       = 0.3
        presence_penalty  = 0.2
        frequency_penalty = 0.2

    # ── Step 3: PROMPT trace — what we actually send to the model ────────────
    _trace(req_id, "3.PROMPT", {
        "model": model, "temperature": temperature,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty,
        "message_count": len(messages),
        "roles": [m["role"] for m in messages],
        "system_preview": (messages[0]["content"][:600] if messages else ""),
        "user_preview":   (messages[-1]["content"][:400] if messages else ""),
        "kundli_injected_in_prompt": (
            mode == "astro"
            and any("BIRTH CHART" in (m.get("content") or "")
                    or "kundli" in (m.get("content") or "").lower()
                    for m in messages)
        ),
        "wealth_structured": bool(_wealth_obj),
    })

    def _call_once(timeout: float | None = None) -> str:
        # Phase 4.4: validator retry sites pass `timeout=_VALIDATOR_RETRY_TIMEOUT_S`
        # so a slow OpenAI retry can never hold an SSE stream open. Primary
        # generation passes timeout=None (uses client default).
        _create_kw = dict(
            model            = model,
            messages         = messages,
            temperature      = temperature,
            top_p            = 1,
            max_tokens       = _token_budget_for(topic, question),
            presence_penalty = presence_penalty,
            frequency_penalty= frequency_penalty,
        )
        if timeout is not None:
            _create_kw["timeout"] = timeout
        try:
            r = client.chat.completions.create(**_create_kw)
        except Exception as exc:
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc
        t = (r.choices[0].message.content or "").strip() if r.choices else ""
        if not t:
            raise RuntimeError("OpenAI returned empty response")
        return t

    if _use_wealth_structured_path:
        # Wealth structured-output path: json_schema (strict=True), temp=0.0,
        # max 2 retries on parse / validation failure. NO free-text fallback.
        import json as _json_w
        _last_exc: Exception | None = None
        _payload: dict | None = None
        for _attempt in range(2):
            try:
                # JSON schema needs more headroom than prose — Hinglish
                # bullets + remedy + note can run 1200+ tokens easily.
                _wealth_max_tokens = max(1800, _token_budget_for(topic, question))
                _resp_w = client.chat.completions.create(
                    model            = model,
                    messages         = messages,
                    temperature      = 0.0,
                    top_p            = 1,
                    max_tokens       = _wealth_max_tokens,
                    response_format  = {
                        "type":        "json_schema",
                        "json_schema": _WEALTH_STRUCTURED_JSON_SCHEMA,
                    },
                )
            except Exception as _exc_w:
                _last_exc = _exc_w
                _trace(req_id,
                       f"3a.WEALTH_JSON_REQ_FAIL_attempt{_attempt+1}",
                       str(_exc_w))
                _payload = None
                continue
            _raw_w = (_resp_w.choices[0].message.content or "").strip() \
                if _resp_w.choices else ""
            if not _raw_w:
                _last_exc = RuntimeError("empty wealth structured response")
                _trace(req_id,
                       f"3a.WEALTH_JSON_EMPTY_attempt{_attempt+1}", "")
                _payload = None
                continue
            try:
                _payload = _json_w.loads(_raw_w)
            except Exception as _exc_p:
                _last_exc = _exc_p
                _trace(req_id,
                       f"3a.WEALTH_JSON_PARSE_FAIL_attempt{_attempt+1}",
                       {"err": str(_exc_p), "raw_preview": _raw_w[:300]})
                _payload = None
                continue
            # Sprint-26 Fix-Q (post-architect-review): pass the recovery
            # sub-ask flag so the validator can enforce both directions —
            # required-when-asked AND empty-when-not-asked.
            ok_v, why_v = _validate_wealth_payload(
                _payload, _wealth_obj,
                has_recovery_subask=bool(question_intent.get("has_recovery_subask")),
            )
            if not ok_v:
                _last_exc = RuntimeError(f"validation failed: {why_v}")
                _trace(req_id,
                       f"3a.WEALTH_JSON_VALIDATE_FAIL_attempt{_attempt+1}",
                       {"reason": why_v})
                _payload = None
                continue
            break
        if _payload is None:
            raise WealthStructuredError(
                "wealth structured generation failed after 2 attempts: "
                f"{_last_exc}"
            )
        _wealth_structured_payload = _payload
        text = _format_wealth_structured_payload(_payload)
        _trace(req_id, "4.WEALTH_STRUCTURED_OK", {
            "tag":            _payload.get("verdict", {}).get("tag"),
            "headline_words": len((_payload.get("headline") or "").split()),
            "will_n":         len(_payload.get("what_will_happen") or []),
            "do_n":           len(_payload.get("what_to_do") or []),
            "avoid_n":        len(_payload.get("what_to_avoid") or []),
        })
    else:
        text = _call_once()
        _trace(req_id, "4.RAW_AI_RESPONSE", text)

        # ── Phase 5.1 — TOTAL STRIP early-return ──────────────────────────────
        # When PHASE51_BARE_PROMPT=1 (default), bypass ALL post-response
        # validators / mutators / footer-injectors / follow-up generation and
        # return the model's raw text verbatim. See `_phase51_bare_prompt_
        # enabled` for the full list of bypassed stages.
        if _phase50_active and _phase51_bare_prompt_enabled():
            _trace(req_id, "5.PHASE51_BARE_RETURN", {
                "raw_chars": len(text or ""),
                "bypassed": [
                    "supertype_contract_validator", "post_logic_check",
                    "timing_validator", "jargon_inject", "health_brand_safety",
                    "validators_framework", "marriage_validator",
                    "wealth_brand_safety", "scrubber", "phase48_truncator",
                    "global_ph_strip", "post_logic_check_post_timing",
                    "engine_warning_footer", "follow_ups",
                ],
            })
            _result_bare = {
                "text":              text,
                "topic":             topic,
                "topic_source":      (build_meta or {}).get("topic_source") or "regex",
                "confidence":        _qu_conf,
                "source":            "openai_bare",
                "follow_ups":        [],
                "question_intent":   question_intent,
                "question_supertype": question_supertype,
                "intent_extraction": (build_meta or {}).get("intent_extraction"),
            }
            return _result_bare

        # ── Fix-D: SUPERTYPE CONTRACT VALIDATOR + 1-RETRY ────────────────────
        # The strict per-supertype contract was injected as the LAST system
        # message above (Sprint-24). Sometimes the model partially ignores
        # MUST/MUST-NOT rules — we catch hard violations here and re-prompt
        # ONCE with corrective feedback. Cap = 1 retry (avoid runaway cost).
        # Skipped when the contract was not installed (mode=general, wealth
        # structured, marriage narrator) — those have their own validators.
        try:
            _supertype_validator_enabled = (
                os.environ.get("SUPERTYPE_VALIDATOR", "1") != "0"
            )
            if (_supertype_validator_enabled
                    and not _skip_contract_reason
                    and isinstance(question_supertype, dict)):
                _sup_tag = question_supertype.get("supertype") or "GENERAL_ANALYSIS"
                _violations = _validate_supertype_contract(text, _sup_tag, kundli=kundli)
                if _violations:
                    _trace(req_id, "4z.SUPERTYPE_CONTRACT_VIOLATION", {
                        "supertype":      _sup_tag,
                        "violation_count": len(_violations),
                        "violations":     _violations,
                        "first_attempt_preview": text[:240],
                    })
                    # Append corrective feedback as a NEW LAST system msg so
                    # it gets recency-lock priority on the retry call.
                    messages.append({
                        "role":    "system",
                        "content": _retry_feedback_for(_sup_tag, _violations),
                    })
                    try:
                        # Phase 4.4: bounded retry timeout — see _VALIDATOR_RETRY_TIMEOUT_S.
                        _retry_text = _call_once(timeout=_VALIDATOR_RETRY_TIMEOUT_S)
                        _retry_violations = _validate_supertype_contract(
                            _retry_text, _sup_tag, kundli=kundli
                        )
                        _trace(req_id, "4z.SUPERTYPE_CONTRACT_RETRY", {
                            "supertype":           _sup_tag,
                            "retry_violations":    _retry_violations,
                            "retry_clean":         not _retry_violations,
                            "retry_preview":       _retry_text[:240],
                        })
                        # Accept retry if it has FEWER violations than the
                        # first attempt (even if not perfectly clean — it's
                        # at least closer to the contract).
                        if len(_retry_violations) < len(_violations):
                            text = _retry_text
                            _trace(req_id, "4z.SUPERTYPE_CONTRACT_ACCEPTED",
                                   {"reason": "retry was closer to contract"})
                        else:
                            _trace(req_id, "4z.SUPERTYPE_CONTRACT_KEPT_FIRST",
                                   {"reason": "retry not better than first"})
                    except Exception as _retry_exc:
                        _trace(req_id, "4z.SUPERTYPE_CONTRACT_RETRY_FAIL",
                               {"error": str(_retry_exc)[:200]})
                else:
                    _trace(req_id, "4z.SUPERTYPE_CONTRACT_CLEAN",
                           {"supertype": _sup_tag})
        except Exception as _val_exc:
            _trace(req_id, "4z.SUPERTYPE_CONTRACT_VALIDATOR_ERR",
                   {"error": str(_val_exc)[:200]})

        # ── Sprint-26 Step 4 Phase 3 — POST_LOGIC_CHECK (TRUTH validator) ─
        # Hybrid (Option C): if claims mismatch kundli ground truth, fire
        # ONE corrective retry with actual values injected. If retry STILL
        # mismatches → hard refusal template. NO silent corrections —
        # every check + retry + accept/refuse is traced.
        try:
            _post_logic_enabled = (
                os.environ.get("POST_LOGIC_CHECK", "1") != "0"
            )
            if _post_logic_enabled and isinstance(kundli, dict):
                _truth = _build_truth_facts(kundli)
                _truth_violations = _post_logic_check(text, _truth)
                if _truth_violations:
                    _trace(req_id, "2v.POST_LOGIC_CHECK_VIOLATION", {
                        "violation_count": len(_truth_violations),
                        "violations":      _truth_violations,
                        "truth_md":        (_truth.get("current_md") or {}).get("planet"),
                        "truth_ad":        (_truth.get("current_ad") or {}).get("planet"),
                        "first_attempt_preview": text[:240],
                    })
                    # Inject corrective system message + retry once.
                    messages.append({
                        "role":    "system",
                        "content": _post_logic_correction_msg(
                            _truth_violations, _truth),
                    })
                    try:
                        # Phase 4.4: bounded retry timeout — see _VALIDATOR_RETRY_TIMEOUT_S.
                        _pl_retry_text = _call_once(timeout=_VALIDATOR_RETRY_TIMEOUT_S)
                        _pl_retry_violations = _post_logic_check(
                            _pl_retry_text, _truth)
                        _trace(req_id, "2v.POST_LOGIC_CHECK_RETRY", {
                            "retry_violations":    _pl_retry_violations,
                            "retry_clean":         not _pl_retry_violations,
                            "retry_preview":       _pl_retry_text[:240],
                        })
                        if not _pl_retry_violations:
                            text = _pl_retry_text
                            _trace(req_id, "2v.POST_LOGIC_CHECK_ACCEPTED",
                                   {"reason": "retry clean — facts corrected",
                                    "correction_applied": True})
                        else:
                            # Architect-required strict-terminal (Phase-3 v2,
                            # Option C contract): ANY non-zero residual
                            # violation → refusal. Removed the previous
                            # PARTIAL-accept branch, which architect flagged
                            # as serving still-violating text and breaking
                            # the no-silent-correction guarantee.
                            text = _POST_LOGIC_REFUSAL_TEXT
                            _trace(req_id, "2v.POST_LOGIC_CHECK_REFUSAL", {
                                "reason": ("retry clean" if False
                                           else "retry left residual violations"),
                                "residual_violation_count": len(_pl_retry_violations),
                                "first_violations": _truth_violations,
                                "retry_violations": _pl_retry_violations,
                                "reduced_count":   len(_truth_violations)
                                                   - len(_pl_retry_violations),
                                "served_text": "_POST_LOGIC_REFUSAL_TEXT",
                            })
                    except Exception as _pl_retry_exc:
                        # Architect-required: retry-error MUST also refuse —
                        # cannot fall through and ship the first violating
                        # answer. Refusal preferred over the known-bad text.
                        text = _POST_LOGIC_REFUSAL_TEXT
                        _trace(req_id, "2v.POST_LOGIC_CHECK_RETRY_ERR", {
                            "error": str(_pl_retry_exc)[:200],
                            "first_violations": _truth_violations,
                            "served_text": "_POST_LOGIC_REFUSAL_TEXT",
                            "reason": "retry call errored — refusing rather "
                                      "than serving first violating text",
                        })
                else:
                    _trace(req_id, "2v.POST_LOGIC_CHECK_CLEAN", {
                        "truth_md": (_truth.get("current_md") or {}).get("planet"),
                        "truth_ad": (_truth.get("current_ad") or {}).get("planet"),
                    })
        except Exception as _pl_exc:
            _trace(req_id, "2v.POST_LOGIC_CHECK_ERR",
                   {"error": str(_pl_exc)[:200]})

    # ── Sprint-51 TIMING VALIDATOR — hard anti-hallucination layer ──────────
    # If the question is a "kab/when" timing question, the AI is FORBIDDEN
    # from inventing any date/year/month/dasha not present in the engine's
    # locked facts. Any invented token is scrubbed and replaced with the
    # engine's authoritative window.
    try:
        from vedic.validator.timing_validator import enforce_timing_lock  # type: ignore
        _facts_blob = "\n".join(
            (m.get("content") or "") for m in messages if m.get("role") == "system"
        )
        _engine_window = ""
        # Best-effort extract of the topic-specific engine window line.
        # We require the line to look like an actual heading
        # ("X window:" or "X-WINDOW:") emitted by an engine — NOT a free-
        # text bullet that happens to mention "window". Topic keyword
        # match is case-insensitive.
        import re as _re_winscan
        _heading_rx = _re_winscan.compile(
            r"(marriage|child|career|promotion|wealth|foreign|property|"
            r"health|illness|recovery|surgery|longevity)"
            r"[\s\-]+window\s*:",
            _re_winscan.IGNORECASE,
        )
        for _line in _facts_blob.splitlines():
            if _heading_rx.search(_line):
                _engine_window = _line.strip(); break
        _lock = enforce_timing_lock(question or "", text, _facts_blob, _engine_window)
        # Sprint-26 Fix-K — SMART VALIDATOR (FIX 1): if the engine layer
        # genuinely failed to produce any timing data (overall ∈
        # {empty, partial} AND no authorised tokens were found), the
        # validator's "every AI date is invented" verdict is a FALSE
        # POSITIVE — it has no ground truth to verify against. In that
        # case we TRUST the AI's reasoning over the engine's silence and
        # let the text pass unchanged. Golden rule: engine absence ≠ AI
        # hallucination. We trace the bypass so it's fully observable.
        _eng = (build_meta or {}).get("engine_status") or {}
        _engine_overall = _eng.get("overall", "ok")
        _val = _lock.get("validation") or {}
        _no_authorised = not (_val.get("authorised_tokens") or [])
        # Sprint-26 Fix-K (architect-tightened): only soften when the
        # engine produced ZERO phase output. "partial" means at least
        # one phase succeeded — authoritative timing facts may exist
        # even if some other phase failed, so we must NOT bypass the
        # validator there. Tightening here protects against true AI
        # hallucinations that would otherwise sneak through.
        _engine_unavailable = (_engine_overall == "empty")
        # Sprint-26 Fix-M: extend the soften gate for two routing cases the
        # original Fix-K didn't cover. In both, the validator's per-topic
        # token bucket is the wrong yardstick — but engine FACTS (LOCKED
        # FACTS dasha block + transits) ARE present, so we should trust
        # the AI's quoting of them.
        #   (a) PRIMARY intent is `analysis` (e.g. "ek hi reason ya alag")
        #       — the validator was designed for pure timing questions;
        #       analysis questions legitimately quote dasha dates as part
        #       of their reasoning. authorised_tokens=[] here means the
        #       analysis path simply didn't surface its tokens, NOT that
        #       the AI hallucinated.
        #   (b) cross_domain_root_cause is True — the validator only reads
        #       one topic's bucket, so dual-domain answers always look
        #       "unauthorised" by definition.
        _primary_intent = (_qu_intents_ranked[0] if _qu_intents_ranked else _qu_intent)
        _is_analysis_primary = (_primary_intent == "analysis")
        # Sprint-26 Fix-N: WHY-leading questions ("kyun", "why",
        # "contradiction", "mismatch") almost always need to quote MD/AD
        # lord names + dates to explain the root cause — the strict
        # validator's per-topic bucket doesn't cover this reasoning path,
        # so it strips the very tokens the user needs to see. Soften.
        try:
            from question_understanding import _WHY_LEADING_RX as _why_rx
            _why_leading = bool(_why_rx.search(question or ""))
        except Exception:
            _why_leading = False
        _multi_intent_softens = (_is_analysis_primary
                                 or _qu_cross_domain
                                 or _why_leading)
        # Phase 4.2 (Apr 28, 2026) — engine honesty check INVERTS the old
        # Sprint-26 Fix-K silent bypass. Per user-clarified gating constraint
        # ("ask section bina kundli ke khulta hi nahi"), birth time/date is
        # GUARANTEED present, so engine_overall == "empty" + missing primary
        # phase = real backend bug, NOT a legitimate data gap. We refuse
        # honestly instead of letting the AI's invented timing pass through.
        # Fix-M softening (analysis_primary / cross_domain / why_leading)
        # is preserved unchanged below — those are validator-bucket
        # mismatches, not engine failures.
        try:
            _hon = _engine_honesty_check(_eng, qu=locals().get("_qu"))
        except Exception as _hon_exc:  # noqa: BLE001
            _trace(req_id, "4a.ENGINE_HONESTY_ERR", str(_hon_exc))
            _hon = {"refuse": False, "warn": False,
                    "failed_phases": [], "optional_failed": [],
                    "reason": "honesty_check_exception"}
        if (not _lock["ok"]
                and _val.get("is_timing")
                and _no_authorised
                and _hon.get("refuse")):
            # PRIMARY phase failed/skipped → honest refusal. NOTE: we
            # intentionally DO NOT require `_engine_unavailable` here —
            # if any primary phase failed, overall=="partial" (because
            # other primary phases ok'd), but the chart is still
            # corrupt enough that timing answers are unsafe. Architect
            # caught this gating bug in Phase 4.2 review (Apr 28 2026).
            _trace(req_id, "4a.TIMING_VALIDATOR_HONEST_REFUSAL", {
                "reason": "primary_phase_failed",
                "engine_overall": _engine_overall,
                "failed_primary": _hon.get("failed_phases", []),
                "engine_failed_all": [
                    e.get("phase") for e in _eng.get("failed", [])
                ],
                "rejected_tokens": _val.get("invented_tokens", []),
                "served_text": "_ENGINE_HONESTY_REFUSAL_TEXT",
                "rule": "engine primary failure → honest refusal "
                        "(Phase 4.2)",
            })
            text = _ENGINE_HONESTY_REFUSAL_TEXT
        elif (not _lock["ok"]
                and _val.get("is_timing")
                and _no_authorised
                and _engine_unavailable):
            # Engine empty but no primary failure recorded — could be
            # kill-switch off (ENGINE_HONESTY=0) OR pre-Phase-4.2
            # untracked state. Preserve legacy Fix-K silent bypass for
            # backwards compat / emergency rollback.
            _trace(req_id, "4a.TIMING_VALIDATOR_SOFTENED", {
                "reason": "engine_unavailable_trust_ai",
                "engine_overall": _engine_overall,
                "engine_failed": [
                    e.get("phase") for e in _eng.get("failed", [])
                ],
                "rejected_tokens": _val.get("invented_tokens", []),
                "honesty_reason": _hon.get("reason"),
                "rule": "engine absence ≠ AI hallucination "
                        "(Sprint-26 Fix-K, kill-switch active)",
            })
            # Leave `text` untouched — AI's answer survives.
        elif (not _lock["ok"]
                and _val.get("is_timing")
                and _no_authorised
                and _multi_intent_softens):
            _trace(req_id, "4a.TIMING_VALIDATOR_SOFTENED", {
                "reason": "multi_intent_or_analysis_primary",
                "primary_intent":          _primary_intent,
                "cross_domain_root_cause": _qu_cross_domain,
                "domains":                 _qu_topics_all,
                "rejected_tokens":         _val.get("invented_tokens", []),
                "rule": "validator-bucket per-topic mismatch "
                        "(Sprint-26 Fix-M)",
            })
            # Leave `text` untouched — AI's answer survives.
        elif not _lock["ok"]:
            _trace(req_id, "4a.TIMING_VALIDATOR_REJECT", _val)
            text = _lock["safe_text"]
        else:
            _trace(req_id, "4a.TIMING_VALIDATOR_OK", _val)
    except Exception as _exc:  # noqa: BLE001
        _trace(req_id, "4a.TIMING_VALIDATOR_ERR", str(_exc))

    # ── Sprint-25 Fix-J: skip ALL deterministic post-injectors when the
    # supertype is STRENGTH_SUMMARY. The contract requires 1–2 short lines —
    # appending D27 Bhamsa, Extended Bala, KP cross-checks, varga injects,
    # etc. would blow the length budget and bury the bucket-grounded answer.
    _skip_post_injects = (
        isinstance(question_supertype, dict)
        and question_supertype.get("supertype") == "STRENGTH_SUMMARY"
    )
    if _skip_post_injects:
        _trace(req_id, "4b.POST_INJECT_SKIP",
               {"reason": "supertype=STRENGTH_SUMMARY (1–2 line contract)"})

    # ── Sprint-26 Fix-L: SIMPLIFY NARRATOR — suppress verbose Jaimini/varga
    # bolt-ons by default. User feedback: "Brain perfect chal raha hai, bas
    # bolne ka style thoda simplify karna hai". The AI's first 3-4 paragraphs
    # already deliver the answer (verdict + dasha rationale + KP/transit
    # support); appending D2 Hora active-earner verdict + Sthira Dasha
    # (Jaimini stability layer) + Niryana Shoola Dasha (longevity) + Argala
    # (Jaimini intervention) + Chara Dasha cross-check + Upapada (marriage
    # signature) + Saptavargaja Bala numerics + D27 Bhamsa as 5–8 separate
    # paragraphs of Sanskrit terminology buries the actual answer in jargon
    # that a normal user can't parse. We default-suppress these "advanced"
    # injectors and re-enable them ONLY when the user explicitly asks for
    # those layers (e.g. "Argala kya hai", "Jaimini paddhati batao", "Chara
    # dasha bata", "varga depth", "deep analysis", "Bhamsa", "Saptavargaja").
    # Topic-specific injectors that ONLY fire when the question is about
    # parents (D12) or siblings (D3) or higher-education (D24) are kept
    # because they directly answer those questions.
    import re as _re_jargon
    _q_lower_jargon = (question or "").lower()
    _user_asked_for_depth = bool(_re_jargon.search(
        r"\b(argala|chara\s*dasha|sthira\s*dasha|niryana|shoola|"
        r"upapada|jaimini|hora|bhamsa|saptavargaja|ishta\s*phala|"
        r"kashta\s*phala|vimshopaka|yuddha\s*bala|extended\s*bala|"
        r"varga|divisional|deep\s*analysis|"
        r"detailed\s*chart|complete\s*reading|full\s*analysis|"
        r"vistar(\s*se|\s*me|\s*mein)?|gehrai|deep\s*dive|"
        r"technical|advanced|elaborate|in[\-\s]?depth|"
        r"detail\s*(me|mein|se)|thoda\s*detail|"
        r"poora?\s*(chart|reading|analysis|kundli)|"
        r"poori\s*(reading|analysis|kundli))\b",
        _q_lower_jargon
    ))
    _skip_verbose_jargon = not _user_asked_for_depth
    if _skip_verbose_jargon:
        _trace(req_id, "4b.JARGON_INJECT_SKIP",
               {"reason": "user did not request depth — keeping answer simple",
                "rule": "Sprint-26 Fix-L SIMPLIFY NARRATOR"})

    # ── HEALTH BRAND-SAFETY POST-PROCESSOR (deterministic, last line) ───────
    # The health engine + narrator override already mandate (a) doctor-consult
    # citation in every reply and (b) mental-health helplines on the
    # mental_health bucket. Despite the system message being explicit, the
    # narrator occasionally drops these. We fix that deterministically here:
    # if the verdict block was active for this turn AND the AI's reply does
    # NOT contain a doctor cite, we APPEND a single mandatory line. For the
    # mental_health bucket we additionally append the Indian crisis helpline
    # numbers if they are missing. This guarantees ZERO regressions on the
    # NO_DOCTOR_CITE / NO_HELPLINE bench checks without re-prompting OpenAI.
    try:
        _hv = (build_meta or {}).get("health_verdict_obj")
        # Routing-collision guard: if a HIGHER-priority engine fired (marriage,
        # stock, love, career), DO NOT inject the health doctor/helpline
        # boilerplate even if the question contains a generic health-flavoured
        # word (e.g. "career stress", "share market tension", "rishta tension").
        # The fallback below is intended ONLY for genuinely health-routed
        # questions that simply did not trigger the health engine output (e.g.
        # concept-mode "Insomnia ka karan kya hai?"). Higher engines have their
        # own brand-safety contracts.
        _bm = (build_meta or {})
        _higher_engine_fired = bool(
            _bm.get("marriage_facts")
            or _bm.get("stock_verdict_obj")
            or _bm.get("love_verdict_obj")
            or _bm.get("career_verdict_obj")
        )
        # Crisis override: explicit suicidal / self-harm phrasing ALWAYS earns
        # helpline + doctor cite, regardless of which engine fired upstream.
        # This is a non-negotiable safety net.
        _crisis_rx = __import__("re").compile(
            r"\b(suicid(?:e|al)|self[- ]?harm|self[- ]?injur(?:y|ies)|"
            r"atmahatya|aatmhatya|aatm[- ]?hatya|atmhatya|"
            r"khudkushi|khud[- ]?kushi|"
            r"jaan[- ]?dena|jaan[- ]?dene|jeena nahi|jeena nahin|"
            r"marna chahta|marna chahti|"
            r"end[- ]?my[- ]?life|kill[- ]?myself)\b",
            __import__("re").IGNORECASE,
        )
        _crisis_q = bool(_crisis_rx.search(question or ""))
        # Fallback: even when health engine did NOT fire (e.g. concept-mode
        # question routed to general/concept flow), if the question is health-
        # related AND no higher-priority engine claimed it, we still owe the
        # user (a) doctor-cite and (b) mental-health helpline.
        _is_health_q_text = bool(_is_health_question(question or ""))
        _bucket_fallback = None
        if (not _hv and _is_health_q_text
                and not _higher_engine_fired):
            _ql = (question or "").lower()
            _mental_kw = ("depress", "anxiety", "panic", "stress", "tension",
                          "manasik", "maanasik", "mental", "insomnia",
                          "nind", "neend", "sleep", "suicid", "self harm",
                          "self-harm", "atmahatya", "khudkushi", "shanti",
                          "jaan dena", "jaan dene", "marna chahta",
                          "end my life", "kill myself")
            _bucket_fallback = ("mental_health"
                                if any(k in _ql for k in _mental_kw)
                                else "general_wellness")
        # Crisis ALWAYS forces mental_health bucket (overrides everything).
        if _crisis_q:
            _bucket_fallback = "mental_health"
        # Sprint-25 Fix-J / Sprint-26 architect-fix: STRENGTH_SUMMARY contract
        # demands 1–2 short lines (≤60 words). Appending the doctor-cite or
        # bucket-fallback boilerplate would blow that budget. We skip the
        # gentle health appender for STRENGTH_SUMMARY UNLESS the question is a
        # crisis (suicide / self-harm) — crisis is non-negotiable and always
        # gets the helpline + doctor cite regardless of supertype.
        if _skip_post_injects and not _crisis_q:
            _trace(req_id, "4a2.HEALTH_BRAND_SAFETY_SKIP",
                   {"reason": "supertype=STRENGTH_SUMMARY (1–2 line contract)"})
        elif _hv or _bucket_fallback:
            import re as _re_health
            _doctor_rx = _re_health.compile(
                r"\b(doctor|physician|specialist|gynec|gynae|cardiolog|"
                r"neurolog|psychiatrist|psycholog|therapist|counsell?or|"
                r"medical advice|medical consultation|qualified medical|"
                r"vaidya|chikitsak|chikitsa|aspataal|hospital)\b",
                _re_health.IGNORECASE,
            )
            _helpline_rx = _re_health.compile(
                r"(iCall|9152987821|Vandrevala|1860[- ]?2662[- ]?345)",
                _re_health.IGNORECASE,
            )
            _doctor_line = (
                "\n\nQualified doctor se zaroor consult karein — "
                "cosmic guidance medical diagnosis ya treatment ka "
                "vikalp nahi hai."
            )
            _helpline_line = (
                "\n\nMental health support ke liye free helplines: "
                "iCall (9152987821) aur Vandrevala Foundation "
                "(1860-2662-345). Aap akele nahi hain."
            )
            _bucket = (_hv.get("bucket") if _hv else _bucket_fallback)
            _added = []
            # SAFETY-NET: strip any timing-validator placeholders that may
            # have leaked through ([engine: dasha not cited] / [engine:
            # window pending] / [engine: year/month ...]). These come from
            # vedic/validator/timing_validator.py when an engine returned
            # a verdict but no usable window — they MUST never reach the
            # user. Replace with neutral fillers that still make sense.
            _ph_rx = _re_health.compile(
                r"\[engine:\s*(?:dasha not cited|window pending|"
                r"year[^\]]*|month[^\]]*)\]",
                _re_health.IGNORECASE,
            )
            if _ph_rx.search(text or ""):
                _stripped = _ph_rx.sub("", text or "")
                # Collapse double-spaces / empty parens left behind.
                _stripped = _re_health.sub(
                    r"\(\s*se\s*\)", "", _stripped)
                _stripped = _re_health.sub(
                    r"\s+", " ", _stripped)
                _stripped = _re_health.sub(
                    r"\s+([,.;!?])", r"\1", _stripped)
                # Drop any line that became meaningless after the strip
                # (e.g. "dasha ke dasha () mein chal raha hai" → kill).
                _kept_lines = []
                _bad_line_rx = _re_health.compile(
                    r"^\s*(?:dasha\s+ke\s+dasha|"
                    r"engine\s+data\s+insufficient).*$",
                    _re_health.IGNORECASE,
                )
                for _ln in _stripped.splitlines():
                    if _bad_line_rx.search(_ln):
                        continue
                    _kept_lines.append(_ln)
                text = "\n".join(_kept_lines)
                _added.append("ph_strip")
            # Phase 4.5 NARRATIVE_MODE: skip the boilerplate doctor cite
            # in narrative mode UNLESS the question contains crisis phrasing
            # (suicide / self-harm) — those always earn the cite + helpline
            # regardless of mode, as a non-negotiable safety net.
            _suppress_doctor_cite = (
                _NARRATIVE_MODE
                and not _crisis_q
                and _bucket != "mental_health"
            )
            if not _doctor_rx.search(text or "") and not _suppress_doctor_cite:
                text = (text or "").rstrip() + _doctor_line
                _added.append("doctor_cite")
            if (_bucket == "mental_health"
                    and not _helpline_rx.search(text)):
                text = text.rstrip() + _helpline_line
                _added.append("helpline")
            if _added:
                _trace(req_id, "4a2.HEALTH_BRAND_SAFETY_INJECTED",
                       {"bucket": _bucket, "added": _added,
                        "src": "engine" if _hv else "fallback"})
            else:
                _trace(req_id, "4a2.HEALTH_BRAND_SAFETY_OK",
                       {"bucket": _bucket,
                        "src": "engine" if _hv else "fallback"})
    except Exception as _exc:  # noqa: BLE001
        _trace(req_id, "4a2.HEALTH_BRAND_SAFETY_ERR", str(_exc))

    # ── WEALTH BRAND-SAFETY POST-PROCESSOR — MOVED BELOW REGEN PATHS ──
    # The wealth brand-safety injection (CA cite + SEBI line + engine-
    # placeholder strip) used to live HERE, between the health post-
    # processor and the general-mode validator. That placement was
    # broken because both the general-mode validator (mode == "general")
    # and the marriage narrator validator (topic == "marriage") can
    # trigger ONE auto-regen via `text = _call_once()`, which silently
    # CLOBBERED the freshly-injected CA cite — leaving the final reply
    # with NO advisor disclaimer and unstripped `[engine: …]` tokens.
    # The block now runs at the very end (right before the Tone
    # scrubber), so it always operates on the FINAL post-regen text.
    # Search for "WEALTH BRAND-SAFETY POST-PROCESSOR (final position)"
    # below.

    # ── General-mode validators (chart-leak + strict structure) ──────────────
    # Two independent checks for general (non-astro) replies:
    #   (a) chart leak — references to user's kundli/planets/dasha/remedy
    #   (b) structure violation — missing "Simple samjho — " opener OR
    #       missing "Final: ..." closing line
    # Either failure triggers ONE regenerate with a hard-override prompt that
    # restates whichever rule was broken.
    if mode == "general":
        leaks  = _general_reply_leaks_chart(text)
        broken = _general_reply_violates_structure(text)
        _trace(req_id, "4b.VALIDATORS",
               {"chart_leak": leaks, "structure_violation": broken,
                "regenerate": bool(leaks or broken)})
        if leaks or broken:
            why = []
            if leaks:  why.append("chart-leak")
            if broken: why.append("structure-violation")
            override_lines = ["\n\n=== HARD OVERRIDE — REGENERATE ==="]
            if leaks:
                override_lines.append(
                    "Previous attempt referenced the user's kundli / chart /\n"
                    "planets / dasha / remedy. THIS IS BANNED for a general\n"
                    "question. Answer ONLY the concept itself — no astrology\n"
                    "personalisation. DO NOT use: 'aapki kundli', 'your chart',\n"
                    "'your Sun/Moon', 'aapke 7th house', 'mahadasha',\n"
                    "'aapki rashi', mantra+count+day, donation upay, or any\n"
                    "planet from the user's chart."
                )
            if broken:
                override_lines.append(
                    "Previous attempt VIOLATED the mandatory structure.\n"
                    "MANDATORY: line 1 MUST start with the literal text\n"
                    "  `Simple samjho — `\n"
                    "and the last line MUST start with the literal text\n"
                    "  `Final: `\n"
                    "Total length 50–120 words. Bullets only if needed."
                )
            messages = list(messages)
            messages[0] = {
                "role": "system",
                "content": messages[0]["content"] + "\n".join(override_lines),
            }
            text = _call_once()
            _trace(req_id, "4c.RAW_AI_REGEN", text)

    # ── Marriage narrator validator — verifies AI echoed locked window verbatim
    # and didn't relapse into jargon labels or guru greetings. ONE auto-regen.
    # Phase 4.5 NARRATIVE_MODE: skip this validator. Its "no Reason:/Timing:/
    # Remedy:" clause is enforced by the new narrative contract already, and
    # its "exact verbatim window" requirement conflicts with the narrative-
    # mode preference for natural near-term phrasing ("mid-June ke baad").
    if (not _NARRATIVE_MODE
            and mode == "astro" and topic == "marriage"
            and build_meta.get("marriage_facts")):
        active_w = build_meta.get("active_window") or ""
        violated, why_m = _marriage_reply_violates(text, active_w)
        _trace(req_id, "4b.MARRIAGE_VALIDATOR",
               {"violated": violated, "reason": why_m,
                "locked_window": active_w})
        if violated:
            override = (
                "\n\n=== HARD OVERRIDE — REGENERATE (marriage narrator) ===\n"
                "Previous attempt violated the marriage narration rules.\n"
                f"Failure: {why_m}\n"
                f"You MUST include the EXACT phrase \"{active_w}\" verbatim "
                "in your reply (no rounding, no paraphrasing).\n"
                "You MUST NOT use the labels Reason:/Timing:/Remedy:/Vajah:/"
                "Samay:/Upay:/7th lord/kalatra-karaka.\n"
                "You MUST NOT open with Pranam/Beta/Namaste/Dekhiye beta/"
                "Acharya ji/Pandit ji.\n"
                "Write 80–140 words of natural flowing prose, peer-to-peer, "
                "ChatGPT-style. No bullets, no headers."
            )
            messages = list(messages)
            messages[0] = {"role": "system",
                           "content": messages[0]["content"] + override}
            text = _call_once()
            _trace(req_id, "4c.RAW_AI_REGEN(marriage)", text)

    # ── WEALTH BRAND-SAFETY POST-PROCESSOR (final position) ─────────────────
    # Runs AFTER both the general-mode validator regen and the marriage
    # narrator regen so any `text = _call_once()` clobber upstream is
    # safely overwritten with the deterministic CA cite + (high-risk
    # buckets) SEBI line + engine-placeholder strip. The wealth engine +
    # narrator override already mandate the same content, but the model
    # occasionally drops it; this guarantees ZERO regressions on the
    # NO_FINADVISOR_CITE / NO_SEBI_LINE bench checks without re-prompting.
    try:
        _wv = (build_meta or {}).get("wealth_verdict_obj")
        _bm_w = (build_meta or {})
        # Routing-collision guard: only TRUE-overlap engines that already
        # own a CA / SEBI-registered advisor cite contract should suppress
        # the wealth post-processor. None currently do — marriage / love
        # are non-financial; stock and career DO involve money but neither
        # injects an advisor cite of their own. So we only suppress when
        # marriage or love claimed the turn (those are explicitly NOT
        # financial-advice flavoured), and let wealth's safety-net fire
        # alongside stock and career.
        # - stock excluded: real-estate questions like "Real estate
        #   investment ka cosmic window?" get hijacked by stock_engine
        #   on the "investment" keyword, but stock engine has NO CA /
        #   SEBI cite of its own — wealth must still inject.
        # - career excluded: salary / business / partnership / promotion
        #   questions legitimately overlap wealth and career engine does
        #   not inject advisor cites either.
        # Routing-collision guard removed: the gate `_is_wealth_q_text`
        # below is already strict (regex matches only finance-flavoured
        # vocabulary), so even when marriage / love engine claimed the
        # turn upstream we still owe the user the CA / SEBI advisor
        # disclaimer when the question itself is finance-y (e.g.
        # "Partner ke saath finance kaisa rahega?" routes to love but
        # explicitly asks about finance — over-adding the cite is far
        # safer than missing it).
        _higher_engine_fired_w = False
        # Fallback: even when wealth engine did NOT fire (e.g. concept-mode
        # finance question routed to general/concept flow, or marriage /
        # love engine claimed a finance-flavoured question), if the
        # question is wealth-related we still owe the user (a) advisor
        # cite and (b) SEBI line on investment-flavoured questions.
        _is_wealth_q_text = bool(_is_wealth_question(question or ""))
        _bucket_fallback_w = None
        _HIGH_RISK_W = {
            "investment_return", "business_profit", "sudden_windfall",
            "partnership_finance", "general_wealth",
        }
        if (not _wv and _is_wealth_q_text
                and not _higher_engine_fired_w):
            _ql = (question or "").lower()
            _invest_kw = ("invest", "stock", "share", "sip", "mutual",
                          "equity", "trading", "intraday", "lottery",
                          "windfall", "jackpot", "kbc", "satta", "matka",
                          "achanak", "sudden", "business profit",
                          "munafa", "partnership")
            _bucket_fallback_w = (
                "investment_return"
                if any(k in _ql for k in _invest_kw)
                else "general_wealth"
            )
        if _wv or _bucket_fallback_w:
            import re as _re_wealth
            # NOTE: each alternative is wrapped in its own \b…\b so we don't
            # hit the trailing-\s\b mismatch that broke "qualified CA\n\n…"
            # (\s ate the newline, then \b couldn't follow at \n→\n).
            _advisor_rx = _re_wealth.compile(
                r"(?:"
                r"\bCA\b|\bC\.A\.|\bC\.A\b|"
                r"\bchartered\s+accountant\b|\bchartered[- ]accountant\b|"
                r"\bfinancial\s+advisor\b|\bfinancial[- ]advisor\b|"
                r"\bfinancial\s+planner\b|\bfinancial[- ]planner\b|"
                r"\bSEBI[- ]registered\b|\bSEBI\s+registered\b|"
                r"\btax\s+consultant\b|\btax[- ]consultant\b|"
                r"\bqualified\s+financial\b|"
                r"\bvittiy[a-z]*\s+salahkar\b|\bvitt\s+salahkar\b"
                r")",
                _re_wealth.IGNORECASE,
            )
            _sebi_rx = _re_wealth.compile(
                r"(sebi[- ]registered|sebi\s+registered|"
                r"market\s+risk|"
                r"scheme\s+document|scheme[- ]document|"
                r"diversification)",
                _re_wealth.IGNORECASE,
            )
            _advisor_line = (
                "\n\nQualified CA / SEBI-registered financial advisor se "
                "zaroor consult karein — cosmic guidance investment, tax "
                "planning ya loan decision ka vikalp nahi hai."
            )
            _sebi_line = (
                "\n\nInvestments market risk ke adheen hain — scheme "
                "documents carefully padein, SEBI-registered advisor se "
                "consult karein, diversification + risk-tolerance match "
                "karein."
            )
            _bucket_w = (_wv.get("bucket") if _wv else _bucket_fallback_w)
            _added_w = []
            # SAFETY-NET: strip any timing-validator placeholders that may
            # have leaked through. Mirror of the health post-processor.
            _ph_rx_w = _re_wealth.compile(
                r"\[engine:\s*(?:dasha not cited|window pending|"
                r"year[^\]]*|month[^\]]*)\]",
                _re_wealth.IGNORECASE,
            )
            if _ph_rx_w.search(text or ""):
                _stripped = _ph_rx_w.sub("", text or "")
                _stripped = _re_wealth.sub(
                    r"\(\s*se\s*\)", "", _stripped)
                _stripped = _re_wealth.sub(
                    r"\s+", " ", _stripped)
                _stripped = _re_wealth.sub(
                    r"\s+([,.;!?])", r"\1", _stripped)
                _ph_kept_lines = []
                _ph_bad_rx_w = _re_wealth.compile(
                    r"^\s*(?:dasha\s+ke\s+dasha|"
                    r"engine\s+data\s+insufficient).*$",
                    _re_wealth.IGNORECASE,
                )
                for _ln in _stripped.splitlines():
                    if _ph_bad_rx_w.search(_ln):
                        continue
                    _ph_kept_lines.append(_ln)
                text = "\n".join(_ph_kept_lines)
                _added_w.append("ph_strip")
            # ALWAYS-ON prompt-template leak scrubber — runs regardless of
            # whether `[engine: …]` placeholders were present, because the
            # model occasionally echoes the system-prompt's tense bullet
            # ("FUTURE → headline references the NEXT favourable wealth
            # window from `▸ Wealth window:` line.") verbatim into normal
            # replies that didn't trip the timing validator.
            _leak_line_rx_w = _re_wealth.compile(
                r"^\s*(?:.*headline\s+references\s+the\s+next|"
                r".*favourable\s+wealth\s+window\s+from|"
                r".*authoritative\s+window\s*:\s*future\s*[→>]).*$",
                _re_wealth.IGNORECASE,
            )
            _leak_inline_rx_w = _re_wealth.compile(
                r"\s*authoritative\s+window\s*:\s*future\s*[→>][^.\n]*"
                r"(?:wealth\s+window\s*:?[^.\n]*)?\.?",
                _re_wealth.IGNORECASE,
            )
            if (_leak_line_rx_w.search(text or "")
                    or _leak_inline_rx_w.search(text or "")):
                _leak_kept = []
                for _ln in (text or "").splitlines():
                    if _leak_line_rx_w.search(_ln):
                        continue
                    _ln = _leak_inline_rx_w.sub("", _ln)
                    _leak_kept.append(_ln)
                text = "\n".join(_leak_kept)
                if "ph_strip" not in _added_w:
                    _added_w.append("leak_strip")
            # Phase 4.5 NARRATIVE_MODE: skip the boilerplate CA / SEBI
            # advisor disclaimer in narrative mode (user explicitly asked
            # for clean narrative). The wealth engine still runs and feeds
            # ground-truth verdict + window facts to the AI; only the
            # appended disclaimer suffix is suppressed.
            if not _advisor_rx.search(text or "") and not _NARRATIVE_MODE:
                text = (text or "").rstrip() + _advisor_line
                _added_w.append("advisor_cite")
            if (_bucket_w in _HIGH_RISK_W
                    and not _sebi_rx.search(text)
                    and not _NARRATIVE_MODE):
                text = text.rstrip() + _sebi_line
                _added_w.append("sebi_line")
            if _added_w:
                _trace(req_id, "4a3.WEALTH_BRAND_SAFETY_INJECTED",
                       {"bucket": _bucket_w, "added": _added_w,
                        "src": "engine" if _wv else "fallback"})
            else:
                _trace(req_id, "4a3.WEALTH_BRAND_SAFETY_OK",
                       {"bucket": _bucket_w,
                        "src": "engine" if _wv else "fallback"})
    except Exception as _exc:  # noqa: BLE001
        _trace(req_id, "4a3.WEALTH_BRAND_SAFETY_ERR", str(_exc))

    # ── Tone scrubber — strip any blacklisted AI-style phrases.
    # Phase 5.0 Final Strip: skipped when the minimal-prompt path is active.
    # The scrubber is a STYLE controller (rewrites tone/phrasing); user spec
    # explicitly bans style-modifying validators. Hallucination guards
    # (TIMING_VALIDATOR + POST_LOGIC_CHECK) remain — those are correctness,
    # not style.
    if not _phase50_active:
        pre_scrub = text
        text = _scrub_brand_tone(text)
        if pre_scrub != text:
            _trace(req_id, "4d.SCRUBBER_CHANGED", {
                "before_preview": pre_scrub[:200],
                "after_preview":  text[:200],
            })
    else:
        _trace(req_id, "4d.SCRUBBER_SKIPPED", {
            "reason": "phase50 minimal-prompt path — style validators disabled",
        })
    if not text:
        raise RuntimeError("OpenAI returned empty response after scrub")

    # Derive confidence from data completeness — high (0.95) if planets +
    # dasha + birth coords all present (KP usable), medium (0.75) if planets
    # only, low (0.55) if just birth fields without a chart.
    has_planets = isinstance(kundli, dict) and bool(kundli.get("planets"))
    has_dasha   = isinstance(kundli, dict) and bool(kundli.get("currentDasha"))
    has_coords  = isinstance(birth, dict) and birth.get("lat") is not None and birth.get("lon") is not None
    if has_planets and has_dasha and has_coords:
        confidence = 0.95
    elif has_planets and has_dasha:
        confidence = 0.85
    elif has_planets:
        confidence = 0.75
    else:
        confidence = 0.55

    eff_lang = _resolve_response_lang(question, lang, preferred_language)

    # Sprint-7 Rule O — DETERMINISTIC UPAPADA INJECTION (last-resort).
    # If topic == "marriage" and the model dropped the Jaimini citation,
    # append one engine-generated sentence so Rule O is satisfied 100%.
    # Phase 4.5: skipped in narrative mode — the unified narrative contract
    # forbids mandatory engine-appended technical paragraphs (breaks the
    # 3-5 sentence flowing-paragraph shape).
    if (topic == "marriage"
            and not _NARRATIVE_MODE
            and isinstance(kundli, dict) and kundli.get("planets")):
        try:
            import re as _re
            if not _re.search(r"(?i)upapada|jaimini", text or ""):
                from jaimini import (compute_arudha_padas,  # type: ignore
                                     compute_upapada)
                _lg = kundli.get("ascendant")
                if isinstance(_lg, dict):
                    _lg = _lg.get("sign") or _lg.get("name")
                _ar = compute_arudha_padas(kundli.get("planets") or [], _lg)
                _ul = compute_upapada(_ar, kundli.get("planets") or []) if _ar else {}
                if _ul:
                    tag = "NEUTRAL"
                    for t in ("STABLE", "STRAINED", "MIXED", "NEUTRAL"):
                        if t in _ul.get("verdict", ""):
                            tag = t
                            break
                    tag_hi = {
                        "STABLE":   "stable hai",
                        "STRAINED": "strain dikha rahi hai",
                        "MIXED":    "mixed hai (kuch achha, kuch challenge)",
                        "NEUTRAL":  "neutral hai (koi prabal signal nahi)",
                    }[tag]
                    extra_nuance = ""
                    if (_ul.get("ul_lord_house") or 0) in (6, 8, 12):
                        extra_nuance = (f" (UL-lord {_ul['ul_lord']} dusthana "
                                        f"{_ul['ul_lord_house']}th from UL — "
                                        f"thodi caution)")
                    elif _ul.get("occupants_12th") and any(
                        p in ("Ketu", "Saturn", "Rahu")
                        for p in _ul["occupants_12th"]
                    ):
                        sep_pl = ", ".join(_ul["occupants_12th"])
                        extra_nuance = (f" (12th-from-UL mein {sep_pl} — "
                                        f"separation tendency)")
                    ul_sentence = (
                        f"\n\nJaimini paddhati se Upapada Lagna "
                        f"{_ul['ul_sign']} mein hai (lord {_ul['ul_lord']}) — "
                        f"yeh marriage signature {tag_hi}{extra_nuance}."
                    )
                    text = (text or "").rstrip() + ul_sentence
        except Exception as _exc:
            print(f"[ai_ask] UL post-inject failed: {_exc}")

    # Sprint-9 Rule Q — DETERMINISTIC topic-specific varga post-injectors.
    # D7 for child Q, D2 for finance Q, D12 if parents mentioned, D3 if siblings.
    if isinstance(kundli, dict) and kundli.get("planets") and not _skip_post_injects:
        try:
            import re as _re
            from divisional_charts import (compute_d2, compute_d3, compute_d7,  # type: ignore
                                           compute_d12,
                                           summarize_d2_for_wealth,
                                           summarize_d3_for_siblings,
                                           summarize_d7_for_children,
                                           summarize_d12_for_parents)
            _planets_q = kundli.get("planets") or []
            _lg_q = kundli.get("lagna") or kundli.get("ascendant")
            _lagna_lon = _lg_q.get("longitude") or _lg_q.get("lon") if isinstance(_lg_q, dict) else None
            _intel_q = {}
            try:
                from chart_intelligence import analyze_chart  # type: ignore
                _intel_q = analyze_chart(kundli, birth) or {}
            except Exception:
                pass
            _q_lower = (question or "").lower()

            # D7 — children (topic OR child-keyword in question)
            _is_child_q = bool(_re.search(
                r"\b(bachh?e?|bachch?[aeio]+|baby|babies|child|children|"
                r"kids?|santaan|santan|putra|aulad|aulaad|"
                r"pregnancy|pregnant|conceive|conception|garbh)\b", _q_lower
            ))
            if (topic == "child" or _is_child_q) and not _re.search(
                r"(?i)\bd[\-\s]?7\b|saptam(sa|sha|amsa)", text or ""
            ):
                _d7 = compute_d7(_planets_q, _lagna_lon)
                _s7 = summarize_d7_for_children(_d7, _intel_q) if _d7 else {}
                if _s7.get("5L_d7_sign") or _s7.get("jupiter_d7_sign"):
                    parts = []
                    if _s7.get("5L_d7_sign"):
                        parts.append(
                            f"5L {_s7['5L']} {_s7['5L_d7_sign']} ({_s7['5L_d7_strength']})"
                        )
                    if _s7.get("jupiter_d7_sign"):
                        parts.append(
                            f"Jupiter putra-karaka {_s7['jupiter_d7_sign']} "
                            f"({_s7['jupiter_d7_strength']})"
                        )
                    text = (text or "").rstrip() + (
                        f"\n\nD7 Saptamsa (children refinement) mein "
                        f"{', '.join(parts)} — yeh progeny prospects ka "
                        f"core indicator hai."
                    )

            # D2 — finance/wealth
            if topic == "finance" and not _skip_verbose_jargon and not _re.search(
                r"(?i)\bd[\-\s]?2\b|\bhora\b", text or ""
            ):
                _d2 = compute_d2(_planets_q, _lagna_lon)
                _s2 = summarize_d2_for_wealth(_d2) if _d2 else {}
                if _s2.get("verdict") and not _wealth_structured_payload:
                    sun_p  = ", ".join(_s2.get("sun_hora_planets")  or []) or "koi nahi"
                    moon_p = ", ".join(_s2.get("moon_hora_planets") or []) or "koi nahi"
                    text = (text or "").rstrip() + (
                        f"\n\nD2 Hora (wealth refinement) mein Sun-Hora "
                        f"(active income) ke planets: {sun_p}; Moon-Hora "
                        f"(passive/inherited): {moon_p} — verdict {_s2['verdict']}."
                    )

            # D12 — parents (only if question mentions parents)
            _is_parent_q = bool(_re.search(
                r"\b(maa|mata|maata|papa|pita|pitaji|parent|parents|"
                r"father|fathers|mother|mothers|baap|baba|"
                r"mumm?y|daddy|mom|moms|dad|dads|maaji|mataji)\b", _q_lower
            ))
            if _is_parent_q and not _re.search(
                r"(?i)\bd[\-\s]?12\b|dwadasam(sa|sha)|dwadashamsha", text or ""
            ):
                _d12 = compute_d12(_planets_q, _lagna_lon)
                _s12 = summarize_d12_for_parents(_d12, _intel_q) if _d12 else {}
                parts = []
                if _s12.get("9L_d12_sign"):
                    parts.append(f"9L {_s12['9L']} {_s12['9L_d12_sign']} (father, {_s12['9L_d12_strength']})")
                if _s12.get("4L_d12_sign"):
                    parts.append(f"4L {_s12['4L']} {_s12['4L_d12_sign']} (mother, {_s12['4L_d12_strength']})")
                if parts:
                    text = (text or "").rstrip() + (
                        f"\n\nD12 Dwadasamsa (parents refinement) mein "
                        f"{', '.join(parts)} — yeh maa/papa ke saath "
                        f"relationship aur unka well-being indicate karta hai."
                    )

            # D3 — siblings (only if question mentions siblings)
            _is_sib_q = bool(_re.search(
                r"\b(bhai|bhaiya|behan|bahan|behen|brother|brothers|"
                r"sister|sisters|sibling|siblings|saheli|bhai-behan)\b",
                _q_lower
            ))
            if _is_sib_q and not _re.search(
                r"(?i)\bd[\-\s]?3\b|drekk?an[ah]?", text or ""
            ):
                _d3 = compute_d3(_planets_q, _lagna_lon)
                _s3 = summarize_d3_for_siblings(_d3, _intel_q) if _d3 else {}
                parts = []
                if _s3.get("3L_d3_sign"):
                    parts.append(f"3L {_s3['3L']} {_s3['3L_d3_sign']} ({_s3['3L_d3_strength']})")
                if _s3.get("mars_d3_sign"):
                    parts.append(f"Mars (younger-sibling karaka) {_s3['mars_d3_sign']}")
                if _s3.get("jupiter_d3_sign"):
                    parts.append(f"Jupiter (elder-sibling karaka) {_s3['jupiter_d3_sign']}")
                if parts:
                    text = (text or "").rstrip() + (
                        f"\n\nD3 Drekkana (siblings refinement) mein "
                        f"{', '.join(parts)} — yeh bhai-behan se relations "
                        f"ka core signal hai."
                    )
        except Exception as _exc:
            print(f"[ai_ask] vargas (D2/D3/D7/D12) post-inject failed: {_exc}")

    # Sprint-10 Rule R — DETERMINISTIC advanced varga post-injectors.
    # D16 vehicle/comfort, D20 spirituality, D24 education, D27 health/stamina.
    # ──────────────────────────────────────────────────────────────────────────
    # Sprint-22 GUARD (planet-strength brevity): Skip ALL advanced-varga
    # injectors when the user asks a SHORT, SINGLE-PLANET strength question
    # (e.g. "Saturn powerful hai ya weak?", "Mera Guru strong hai kya?").
    # For those Qs, the prompt's PLANET-STRENGTH RULE (Rule K extension)
    # already requires the model to cite D1+D9 cleanly — bolt-on D16/D20/D24/
    # D27 lines just inflate the answer with unrelated dimensions the user
    # did not ask for. Brevity per user directive: 1-line Q → 2-3 line A.
    # Sprint-23: derive from unified Question-Intent classifier (build_meta).
    # Falls back to False if intent missing for any reason.
    _is_short_planet_strength_q = _intent_is_short_strength(
        (build_meta or {}).get("question_intent") or {}
    )

    if (
        isinstance(kundli, dict)
        and kundli.get("planets")
        and not _is_short_planet_strength_q
        and not _skip_post_injects
    ):
        try:
            import re as _re2
            from divisional_charts import (compute_d16, compute_d20, compute_d24,  # type: ignore
                                           compute_d27,
                                           summarize_d16_for_vehicles,
                                           summarize_d20_for_spirituality,
                                           summarize_d24_for_education,
                                           summarize_d27_for_strength)
            _planets_q2 = kundli.get("planets") or []
            _lg_q2 = kundli.get("lagna") or kundli.get("ascendant")
            _lagna_lon2 = _lg_q2.get("longitude") or _lg_q2.get("lon") if isinstance(_lg_q2, dict) else None
            _intel_q2 = {}
            try:
                from chart_intelligence import analyze_chart  # type: ignore
                _intel_q2 = analyze_chart(kundli, birth) or {}
            except Exception:
                pass
            _q_low2 = (question or "").lower()

            # D16 — vehicle/comfort
            _is_vehicle_q = bool(_re2.search(
                r"\b(vehicle|vehicles|car|cars|bike|bikes|gaadi|gadi|"
                r"luxury|comfort|comforts|conveyance|sukh|aaram|"
                r"automobile|scooter|truck|house|ghar|makaan|property)\b",
                _q_low2
            ))
            if _is_vehicle_q and not _re2.search(
                r"(?i)\bd[\-\s]?16\b|shodasamsa|shodashamsha", text or ""
            ):
                _d16 = compute_d16(_planets_q2, _lagna_lon2)
                _s16 = summarize_d16_for_vehicles(_d16, _intel_q2) if _d16 else {}
                parts = []
                if _s16.get("4L_d16_sign"):
                    parts.append(f"4L {_s16['4L']} {_s16['4L_d16_sign']} ({_s16['4L_d16_strength']})")
                if _s16.get("venus_d16_sign"):
                    parts.append(f"Venus (luxury-karaka) {_s16['venus_d16_sign']} ({_s16['venus_d16_strength']})")
                if parts:
                    text = (text or "").rstrip() + (
                        f"\n\nD16 Shodasamsa (vehicles/comforts refinement) mein "
                        f"{', '.join(parts)} — yeh gaadi, ghar aur material comforts "
                        f"ka core indicator hai."
                    )

            # D20 — spirituality
            _is_spirit_q = bool(_re2.search(
                r"\b(spirit|spiritual|spirituality|sadhana|saadhana|mantra|"
                r"jaap|japa|devotion|bhakti|meditation|dharm|dharma|moksha|"
                r"guru|deeksha|diksha|temple|mandir|pooja|puja|worship)\b",
                _q_low2
            ))
            if _is_spirit_q and not _re2.search(
                r"(?i)\bd[\-\s]?20\b|vimsamsa|vimshamsha", text or ""
            ):
                _d20 = compute_d20(_planets_q2, _lagna_lon2)
                _s20 = summarize_d20_for_spirituality(_d20, _intel_q2) if _d20 else {}
                parts = []
                if _s20.get("9L_d20_sign"):
                    parts.append(f"9L {_s20['9L']} {_s20['9L_d20_sign']} ({_s20['9L_d20_strength']})")
                if _s20.get("jupiter_d20_sign"):
                    parts.append(f"Jupiter (guru-karaka) {_s20['jupiter_d20_sign']}")
                if _s20.get("ketu_d20_sign"):
                    parts.append(f"Ketu (moksha-karaka) {_s20['ketu_d20_sign']}")
                if parts:
                    text = (text or "").rstrip() + (
                        f"\n\nD20 Vimsamsa (spirituality refinement) mein "
                        f"{', '.join(parts)} — yeh sadhana aur dharmic progress "
                        f"ka core signal hai."
                    )

            # D24 — education
            _is_edu_q = bool(_re2.search(
                r"\b(education|study|studies|college|university|exam|exams|"
                r"degree|degrees|learning|learn|phd|research|school|"
                r"padhai|padhaai|vidya|gyaan|gyan|knowledge|"
                r"upsc|gate|cat|neet|mba|btech|engineer)\b",
                _q_low2
            ))
            if _is_edu_q and not _re2.search(
                r"(?i)\bd[\-\s]?24\b|chaturvims|chaturvims?ha|siddhamsa", text or ""
            ):
                _d24 = compute_d24(_planets_q2, _lagna_lon2)
                _s24 = summarize_d24_for_education(_d24, _intel_q2) if _d24 else {}
                parts = []
                if _s24.get("4L_d24_sign"):
                    parts.append(f"4L {_s24['4L']} {_s24['4L_d24_sign']} ({_s24['4L_d24_strength']})")
                if _s24.get("5L_d24_sign"):
                    parts.append(f"5L {_s24['5L']} {_s24['5L_d24_sign']} ({_s24['5L_d24_strength']})")
                if _s24.get("mercury_d24_sign"):
                    parts.append(f"Mercury (vidya-karaka) {_s24['mercury_d24_sign']}")
                if _s24.get("jupiter_d24_sign"):
                    parts.append(f"Jupiter (gnan-karaka) {_s24['jupiter_d24_sign']}")
                if parts:
                    text = (text or "").rstrip() + (
                        f"\n\nD24 Chaturvimsamsa (higher-education refinement) mein "
                        f"{', '.join(parts)} — yeh degrees, exams aur deep learning "
                        f"ka core indicator hai."
                    )

            # D27 — health/stamina
            _is_health_q = bool(_re2.search(
                r"\b(health|stamina|strength|sports|fitness|energy|vitality|"
                r"sehat|sharir|body|sickness|illness|disease|bimari|"
                r"weak|weakness|immunity|workout|gym|athletic|game|games)\b",
                _q_low2
            ))
            if _is_health_q and not _skip_verbose_jargon and not _re2.search(
                r"(?i)\bd[\-\s]?27\b|bhamsa|saptavims|nakshatramsa", text or ""
            ):
                _d27 = compute_d27(_planets_q2, _lagna_lon2)
                _s27 = summarize_d27_for_strength(_d27, _intel_q2) if _d27 else {}
                parts = []
                if _s27.get("lagna_lord_d27_sign"):
                    parts.append(f"lagna-lord {_s27['lagna_lord']} {_s27['lagna_lord_d27_sign']} ({_s27['lagna_lord_d27_strength']})")
                if _s27.get("mars_d27_sign"):
                    parts.append(f"Mars (energy-karaka) {_s27['mars_d27_sign']}")
                if _s27.get("sun_d27_sign"):
                    parts.append(f"Sun (vitality-karaka) {_s27['sun_d27_sign']}")
                if parts:
                    text = (text or "").rstrip() + (
                        f"\n\nD27 Bhamsa (physical strength refinement) mein "
                        f"{', '.join(parts)} — yeh stamina, vitality aur "
                        f"physical resilience ka core signal hai."
                    )
        except Exception as _exc:
            print(f"[ai_ask] advanced vargas (D16/D20/D24/D27) post-inject failed: {_exc}")

    # Sprint-11 Rule S — DETERMINISTIC subtle varga post-injectors.
    # D30 misfortune, D40 maternal, D45 paternal, D60 past-life karma.
    # Sprint-22 brevity guard: skip when short single-planet strength Q
    # (D30 fires on 'weak' keyword and pollutes the answer).
    if (
        isinstance(kundli, dict)
        and kundli.get("planets")
        and not _is_short_planet_strength_q
        and not _skip_post_injects
    ):
        try:
            import re as _re3
            from divisional_charts import (compute_d30, compute_d40, compute_d45,  # type: ignore
                                           compute_d60,
                                           summarize_d30_for_misfortune,
                                           summarize_d40_for_maternal,
                                           summarize_d45_for_paternal,
                                           summarize_d60_for_pastlife)
            _planets_q3 = kundli.get("planets") or []
            _lg_q3 = kundli.get("lagna") or kundli.get("ascendant")
            _lagna_lon3 = _lg_q3.get("longitude") or _lg_q3.get("lon") if isinstance(_lg_q3, dict) else None
            _intel_q3 = {}
            try:
                from chart_intelligence import analyze_chart  # type: ignore
                _intel_q3 = analyze_chart(kundli, birth) or {}
            except Exception:
                pass
            _q_low3 = (question or "").lower()

            # D30 — misfortune/accidents
            _is_misfortune_q = bool(_re3.search(
                r"\b(accident|accidents|misfortune|danger|dangerous|risk|risks|"
                r"dushman|enemy|enemies|litigation|court|case|dispute|disputes|"
                r"loss|losses|setback|attack|fraud|cheating|theft)\b",
                _q_low3
            ))
            if _is_misfortune_q and not _re3.search(
                r"(?i)\bd[\-\s]?30\b|trimsam(sa|sha)", text or ""
            ):
                _d30 = compute_d30(_planets_q3, _lagna_lon3)
                _s30 = summarize_d30_for_misfortune(_d30, _intel_q3) if _d30 else {}
                if _s30.get("verdict"):
                    troubled = ", ".join(_s30.get("troubled_planets") or []) or "koi nahi"
                    text = (text or "").rstrip() + (
                        f"\n\nD30 Trimsamsa (misfortune refinement) mein verdict "
                        f"{_s30['verdict']}, malefic-sign mein concentrated planets: "
                        f"{troubled} — yeh accident/dushmani/loss ke risk ka core signal hai."
                    )

            # D40 — maternal legacy
            _is_maternal_q = bool(_re3.search(
                r"\b(maa|maaji|mother|mothers|maternal|nani|naani|mami|maami|"
                r"matrilineal|maa-side|mom|mommy|matru|maatra)\b",
                _q_low3
            ))
            if _is_maternal_q and not _re3.search(
                r"(?i)\bd[\-\s]?40\b|khavedamsa|svavedamsa", text or ""
            ):
                _d40 = compute_d40(_planets_q3, _lagna_lon3)
                _s40 = summarize_d40_for_maternal(_d40, _intel_q3) if _d40 else {}
                parts = []
                if _s40.get("4L_d40_sign"):
                    parts.append(f"4L {_s40['4L']} {_s40['4L_d40_sign']} ({_s40['4L_d40_strength']})")
                if _s40.get("moon_d40_sign"):
                    parts.append(f"Moon (matru-karaka) {_s40['moon_d40_sign']} ({_s40['moon_d40_strength']})")
                if parts:
                    text = (text or "").rstrip() + (
                        f"\n\nD40 Khavedamsa (maternal-legacy refinement) mein "
                        f"{', '.join(parts)} — yeh maa aur matrilineal karma "
                        f"ka core signal hai."
                    )

            # D45 — paternal legacy
            _is_paternal_q = bool(_re3.search(
                r"\b(papa|papaji|father|fathers|paternal|dada|daada|chacha|chaacha|"
                r"patrilineal|baap|baba|baap-side|dad|daddy|pitru|paitra|pita)\b",
                _q_low3
            ))
            if _is_paternal_q and not _re3.search(
                r"(?i)\bd[\-\s]?45\b|akshavedamsa", text or ""
            ):
                _d45 = compute_d45(_planets_q3, _lagna_lon3)
                _s45 = summarize_d45_for_paternal(_d45, _intel_q3) if _d45 else {}
                parts = []
                if _s45.get("9L_d45_sign"):
                    parts.append(f"9L {_s45['9L']} {_s45['9L_d45_sign']} ({_s45['9L_d45_strength']})")
                if _s45.get("sun_d45_sign"):
                    parts.append(f"Sun (pitru-karaka) {_s45['sun_d45_sign']} ({_s45['sun_d45_strength']})")
                if parts:
                    text = (text or "").rstrip() + (
                        f"\n\nD45 Akshavedamsa (paternal-legacy refinement) mein "
                        f"{', '.join(parts)} — yeh papa aur patrilineal karma "
                        f"ka core signal hai."
                    )

            # D60 — past-life karma
            _is_karma_q = bool(_re3.search(
                r"\b(past[\s\-]?life|pichla[\s\-]?janam|karma|karam|prarabdh|"
                r"soul|atma|aatma|why[\s\-]?me|destiny|niyati|"
                r"purpose[\s\-]?of[\s\-]?life|life[\s\-]?purpose|jeevan[\s\-]?ka[\s\-]?uddeshya)\b",
                _q_low3
            ))
            if _is_karma_q and not _re3.search(
                r"(?i)\bd[\-\s]?60\b|shashtyamsa|shastiamsa", text or ""
            ):
                _d60 = compute_d60(_planets_q3, _lagna_lon3)
                _s60 = summarize_d60_for_pastlife(_d60, _intel_q3, _planets_q3) if _d60 else {}
                parts = []
                if _s60.get("lagna_lord_d60_sign"):
                    parts.append(f"lagna-lord {_s60['lagna_lord']} {_s60['lagna_lord_d60_sign']} ({_s60['lagna_lord_d60_strength']})")
                if _s60.get("atma_karaka_d60_sign"):
                    parts.append(f"Atma Karaka {_s60['atma_karaka']} {_s60['atma_karaka_d60_sign']} ({_s60['atma_karaka_d60_strength']})")
                if parts:
                    text = (text or "").rstrip() + (
                        f"\n\nD60 Shashtyamsa (past-life karma — Parashara's most-prized "
                        f"varga) mein {', '.join(parts)} — yeh aapke aatma ke deepest "
                        f"karma signature ka core signal hai."
                    )
        except Exception as _exc:
            print(f"[ai_ask] subtle vargas (D30/D40/D45/D60) post-inject failed: {_exc}")

    # Sprint-12 Rule T — DETERMINISTIC Vargottama / Shadvarga Bala reinforcement.
    # If model mentioned a specific planet by name AND that planet is exceptional
    # (vargottama in 5+ vargas) OR very-strong/very-weak in Shadvarga Bala,
    # append one short clause naming that signal. Skip if already cited.
    if isinstance(kundli, dict) and kundli.get("planets") and not _skip_post_injects:
        try:
            import re as _re4
            from divisional_charts import (compute_vargottama_matrix,  # type: ignore
                                           compute_shadvarga_bala)
            _planets_q4 = kundli.get("planets") or []
            _lg_q4 = kundli.get("lagna") or kundli.get("ascendant")
            _lagna_lon4 = _lg_q4.get("longitude") or _lg_q4.get("lon") if isinstance(_lg_q4, dict) else None
            _vm = compute_vargottama_matrix(_planets_q4, _lagna_lon4) or {}
            _sb = compute_shadvarga_bala(_planets_q4) or {}

            # Already cited?
            already_vm = bool(_re4.search(r"(?i)vargottam", text or ""))
            already_sb = bool(_re4.search(r"(?i)shadvarga|shad[\s\-]?bala", text or ""))

            clauses = []
            # Vargottama clause — pick top planet that is mentioned in answer with 5+ vargas
            if not already_vm:
                for n, info in sorted(_vm.items(), key=lambda kv: -kv[1]["count"]):
                    if info["count"] >= 5 and _re4.search(rf"\b{n}\b", text or ""):
                        clauses.append(
                            f"{n} vargottama in {info['count']} vargas "
                            f"(exceptional natural strength)"
                        )
                        break
            # Shadvarga clause — pick a mentioned planet that is VERY-STRONG or VERY-WEAK
            if not already_sb:
                for n, info in _sb.items():
                    if info["verdict"] in ("VERY-STRONG", "VERY-WEAK") \
                       and _re4.search(rf"\b{n}\b", text or ""):
                        clauses.append(
                            f"{n} Shadvarga Bala {info['score']}/20 ({info['verdict']})"
                        )
                        break

            if clauses and not _wealth_structured_payload:
                text = (text or "").rstrip() + (
                    f"\n\nDeep-strength signal: "
                    + "; ".join(clauses) + "."
                )
        except Exception as _exc:
            print(f"[ai_ask] varga deep (Sprint-12) post-inject failed: {_exc}")

    # Sprint-15 Rule W — DETERMINISTIC PER-VARGA YOGA INJECTION (last-resort).
    # If detected yogas are present and not cited, append the single most-relevant
    # one (priority: Pancha Mahapurusha > Raj > Vipreet).
    if isinstance(kundli, dict) and kundli.get("planets") and not _skip_post_injects:
        try:
            import re as _reVY
            already_cited = bool(_reVY.search(
                r"(?i)mahapurusha|ruchaka|bhadra|hamsa|malavya|sasa|"
                r"raj\s*yoga|vipreet",
                text or ""
            ))
            if not already_cited:
                from varga_yogas import detect_all_varga_yogas  # type: ignore
                _lgVY = kundli.get("ascendant") or kundli.get("lagna")
                _lonVY = (_lgVY.get("longitude") or _lgVY.get("lon")
                          if isinstance(_lgVY, dict) else None)
                _vy = detect_all_varga_yogas(
                    kundli.get("planets") or [], _lonVY
                ) or {}
                pick = None
                if _vy.get("pancha_mahapurusha"):
                    y = _vy["pancha_mahapurusha"][0]
                    pick = (
                        f"{y['yoga']} ({y['planet']} {y['via']} in "
                        f"{y['sign']}, H{y['house']} of {y['varga']}) — "
                        f"lifelong elevation in this planet's domain"
                    )
                elif _vy.get("raj_yoga"):
                    y = _vy["raj_yoga"][0]
                    pick = (
                        f"Raj Yoga ({', '.join(y['planets'])} conjunct in "
                        f"{y['sign']}, H{y['house']} of {y['varga']}) — "
                        f"power & status rise"
                    )
                elif _vy.get("vipreet_raj_yoga"):
                    y = _vy["vipreet_raj_yoga"][0]
                    pick = (
                        f"Vipreet Raj Yoga ({', '.join(y['planets'])} in "
                        f"{y['sign']}, H{y['house']} of {y['varga']}) — "
                        f"adversity transforms into unexpected rise"
                    )
                if pick:
                    text = (text or "").rstrip() + (
                        f"\n\nClassical yoga signal: {pick}."
                    )
        except Exception as _exc:
            print(f"[ai_ask] Varga-yoga post-inject failed: {_exc}")

    # Sprint-18 Rule X — DETERMINISTIC EXTENDED BALA INJECTION (last-resort).
    # If question is strength/capability-flavored and the answer doesn't already
    # cite Saptavargaja / Ishta / Kashta / Vimshopaka / Yuddha, append the
    # single most-relevant figure from the LOCKED FACTS computation.
    if (
        isinstance(kundli, dict)
        and kundli.get("planets")
        and not _is_short_planet_strength_q  # Sprint-22 brevity guard
        and not _skip_post_injects  # Sprint-25 Fix-J STRENGTH_SUMMARY guard
        and not _skip_verbose_jargon  # Sprint-26 Fix-L SIMPLIFY NARRATOR guard
    ):
        try:
            import re as _reBX
            _qBX = (question or "").lower()
            _is_strength = bool(_reBX.search(
                r"\b(strong|strength|weak|kamzor|powerful|capable|"
                r"capacity|kitna|ability|why.*stuck|why.*delayed|"
                r"why.*not\s*working|kyun\s*nahi|career|marriage|"
                r"shaadi|naukri|success|growth|bala)\b",
                _qBX
            ))
            already_cited = bool(_reBX.search(
                r"(?i)saptavargaja|ishta\s*phala|kashta\s*phala|"
                r"vimshopaka|yuddha\s*bala|extended\s*bala",
                text or ""
            ))
            if _is_strength and not already_cited:
                from datetime import datetime as _dtBX
                from vedic.strength.bala_deep import compute_bala_deep  # type: ignore
                _sti = {"Aries":0,"Taurus":1,"Gemini":2,"Cancer":3,"Leo":4,
                        "Virgo":5,"Libra":6,"Scorpio":7,"Sagittarius":8,
                        "Capricorn":9,"Aquarius":10,"Pisces":11}
                _vc = {}
                for _p in (kundli.get("planets") or []):
                    _n = _p.get("name")
                    _si = _sti.get(_p.get("sign"))
                    if _n and _si is not None:
                        _vc[_n] = {v: _si for v in
                            ["D1","D2","D3","D7","D9","D10","D12","D16",
                             "D20","D24","D27","D30","D40","D45","D60"]}
                _bdt = None
                try:
                    if birth and birth.get("dob"):
                        _bdt = _dtBX.strptime(
                            f"{birth['dob']} {birth.get('tob','12:00')}"[:16],
                            "%Y-%m-%d %H:%M")
                except Exception:
                    pass
                _slon = next((p.get("longitude", 0.0)
                              for p in (kundli.get("planets") or [])
                              if p.get("name") == "Sun"), 0.0)
                _bd_inj = compute_bala_deep(
                    planets=kundli.get("planets") or [],
                    varga_charts=_vc,
                    birth_dt=_bdt,
                    sun_longitude=_slon,
                )
                # Pick most relevant: if Q mentions specific planet, use that;
                # else top Ishta or top Saptavargaja
                pick = None
                planet_names = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]
                mentioned = next((pn for pn in planet_names
                                  if _reBX.search(rf"\b{pn}\b", text or "", _reBX.I)
                                  or _reBX.search(rf"\b{pn}\b", _qBX, _reBX.I)),
                                 None)
                if mentioned:
                    sv = (_bd_inj.get("saptavargaja_bala") or {}).get(mentioned)
                    iph = (_bd_inj.get("ishta_phala") or {}).get(mentioned)
                    kph = (_bd_inj.get("kashta_phala") or {}).get(mentioned)
                    if sv is not None and iph is not None:
                        pick = (f"{mentioned} Saptavargaja Bala {sv}/210v, "
                                f"Ishta Phala {iph}v vs Kashta {kph}v")
                if not pick:
                    iph_map = _bd_inj.get("ishta_phala") or {}
                    if iph_map:
                        top = max(iph_map.items(), key=lambda x: x[1])
                        pick = f"strongest Ishta Phala: {top[0]} {top[1]}v (most beneficial yield)"
                if pick:
                    text = (text or "").rstrip() + (
                        f"\n\nExtended Bala signal: {pick}."
                    )
        except Exception as _exc:
            print(f"[ai_ask] Extended Bala (Sprint-18) post-inject failed: {_exc}")

    # Sprint-18.5 Rule X+ — DETERMINISTIC BHAVA BALA DEEP INJECTION (last-resort).
    # If user mentions a specific house and answer doesn't cite its 4-fold balance,
    # append the relevant H#'s breakdown.
    if isinstance(kundli, dict) and kundli.get("planets") and not _skip_post_injects:
        try:
            import re as _reBH
            _qBH = (question or "").lower()
            # Hindi ordinal → number mapping
            _hindi_ordinals = {
                "pehla": 1, "pehlay": 1, "pratham": 1,
                "doosra": 2, "dusra": 2, "dvitiya": 2,
                "teesra": 3, "tisra": 3, "tritiya": 3,
                "chautha": 4, "chotha": 4, "chaturth": 4,
                "panchwa": 5, "paanchva": 5, "panchama": 5, "pancham": 5,
                "chhatha": 6, "shastha": 6, "shashtam": 6,
                "saatva": 7, "satwa": 7, "saptam": 7, "saptama": 7,
                "aathva": 8, "ashtam": 8, "ashtama": 8,
                "navwa": 9, "navam": 9, "navama": 9,
                "daswa": 10, "dasham": 10, "dashama": 10,
                "gyarawa": 11, "ekadash": 11, "ekadasha": 11,
                "barahwa": 12, "dwadash": 12, "dwadasha": 12,
            }
            _h_num = None
            # Pattern 1: digit BEFORE house word — "7th house", "10th ghar", "5 bhava"
            _m1 = _reBH.search(
                r"(?:^|[\s])(\d{1,2})(?:st|nd|rd|th)?\s*(?:house|ghar|bhava|bhav)\b",
                _qBH
            )
            # Pattern 2: digit AFTER house word — "house 7", "ghar 10"
            _m2 = _reBH.search(
                r"\b(?:house|ghar|bhava|bhav)\s+(\d{1,2})\b", _qBH
            )
            # Pattern 3: short form "h7"
            _m3 = _reBH.search(r"\bh(\d{1,2})\b", _qBH)
            # Pattern 4: Hindi ordinal + house word — "saatva ghar", "chautha bhava"
            _m4 = None
            for _ord, _num in _hindi_ordinals.items():
                if _reBH.search(rf"\b{_ord}\s*(?:ghar|bhava|bhav|house)\b", _qBH):
                    _m4 = _num
                    break
            for _g in (_m1, _m2, _m3):
                if _g:
                    try:
                        _h_num = int(_g.group(1))
                        break
                    except (TypeError, ValueError):
                        continue
            if _h_num is None and _m4 is not None:
                _h_num = _m4
            already_cited_bbd = bool(_reBH.search(
                r"(?i)bhava\s*bala|adhipati\s*bala|bhava\s*dig|drishti\s*bala|bhava\s*deep",
                text or ""
            ))
            if _h_num is not None and not already_cited_bbd:
                if _h_num and 1 <= _h_num <= 12:
                    from vedic.strength.bhava_bala_deep import compute_bhava_bala_deep  # type: ignore
                    _intel_bh = None
                    try:
                        from chart_intelligence import analyze_chart  # type: ignore
                        _intel_bh = analyze_chart(kundli)
                    except Exception:
                        _intel_bh = None
                    _sb_bh = None
                    try:
                        from shadbala import compute_shadbala  # type: ignore
                        _planets_norm = [{"name": p["name"],
                                          "lon": p.get("longitude", 0),
                                          "house": p.get("house", 1),
                                          "retrograde": p.get("retrograde", False)}
                                         for p in (kundli.get("planets") or [])]
                        _sb_bh = compute_shadbala(_planets_norm, lagna_house=1)
                    except Exception:
                        _sb_bh = None
                    # Lagna fallback for derive-from-lagna path
                    _lg_post = kundli.get("ascendant") or kundli.get("lagna")
                    _lg_sign_post = (_lg_post.get("sign")
                                     if isinstance(_lg_post, dict) else _lg_post)
                    _sti_post = {"Aries":0,"Taurus":1,"Gemini":2,"Cancer":3,"Leo":4,
                                 "Virgo":5,"Libra":6,"Scorpio":7,"Sagittarius":8,
                                 "Capricorn":9,"Aquarius":10,"Pisces":11}
                    _lg_idx_post = (_sti_post.get(_lg_sign_post)
                                    if isinstance(_lg_sign_post, str) else None)
                    bbd_inj = compute_bhava_bala_deep(
                        _intel_bh, _sb_bh, None, _lg_idx_post
                    ) or {}
                    h_info = (bbd_inj.get("houses") or {}).get(_h_num)
                    if h_info:
                        weakest_comp = min(
                            [("Adhipati(lord-Shadbala)", h_info["adhipati_bala"] / 500.0),
                             ("Digbala(house-type)", h_info["dig_bala"] / 60.0),
                             ("Drishti(aspects)", (h_info["drishti_bala"] + 120) / 240.0),
                             ("Naisargika(lord-natural)", h_info["naisargika"] / 60.0)],
                            key=lambda x: x[1]
                        )[0]
                        text = (text or "").rstrip() + (
                            f"\n\nBhava Bala Deep signal: H{_h_num} (lord "
                            f"{h_info.get('lord','?')}) total {h_info['total']}v "
                            f"vs required {h_info['required']}v "
                            f"(ratio {h_info['ratio']}x = {h_info['verdict']}). "
                            f"Weakest component: {weakest_comp}."
                        )
        except Exception as _exc:
            print(f"[ai_ask] Bhava Bala Deep (Sprint-18.5) post-inject failed: {_exc}")

    # Sprint-19 Rule Y — DETERMINISTIC CLASSICAL YOGAS INJECTION (anti-hallucination).
    # If user asks about Kaal Sarp / Dhana / Vipreet / Pravrajya / Nabhasa and the
    # answer either invents a yoga not in our detector OR fails to confirm absence,
    # surgically strip the false claim and append the correct deterministic verdict.
    if isinstance(kundli, dict) and kundli.get("planets") and not _skip_post_injects:
        try:
            import re as _reCY
            _qCY = (question or "").lower()

            from vedic.yogas.classical_yogas import detect_classical_yogas  # type: ignore
            _lgCY = kundli.get("ascendant") or kundli.get("lagna")
            _lgsCY = _lgCY.get("sign") if isinstance(_lgCY, dict) else _lgCY
            _stiCY = {"Aries":0,"Taurus":1,"Gemini":2,"Cancer":3,"Leo":4,
                      "Virgo":5,"Libra":6,"Scorpio":7,"Sagittarius":8,
                      "Capricorn":9,"Aquarius":10,"Pisces":11}
            _lgiCY = (_stiCY.get(_lgsCY) if isinstance(_lgsCY, str)
                      else _lgsCY if isinstance(_lgsCY, int) else None)
            _yogas = detect_classical_yogas(kundli.get("planets") or [], _lgiCY)

            # ── Kaal Sarp anti-hallucination ────────────────────────────
            _is_kaalsarp_q = bool(_reCY.search(
                r"(?i)kaal\s*sarp|kaalsarp|kal\s*sarp|sarp\s*dosh|"
                r"snake\s*yog|naag\s*dosh", _qCY))
            if _is_kaalsarp_q:
                _ks_entries = [y for y in _yogas if y.get("category") == "Kaal Sarp"]
                _ks_actual = next(
                    (y for y in _ks_entries
                     if "yoga" in y.get("name", "").lower()
                     and "status" not in y.get("name", "").lower()),
                    None
                )
                # Detect AI's claim of Kaal Sarp (positive form, NOT preceded by negation)
                _ans_claims_ks = bool(_reCY.search(
                    r"(?i)(kaal\s*sarp|sarp\s*dosh)\s*"
                    r"(?!.{0,30}(nahi|nahin|not|no\b|never|absent))"
                    r"[^.\n]{0,40}(hai\b|present|yes|haan|mild|partial|"
                    r"detected|exists|banaa|bana)", text or ""))
                # Robust denial detection — covers many phrasings (single (?i) at start)
                _ans_denies_ks = bool(_reCY.search(
                    r"(?i)((kaal\s*sarp|sarp\s*dosh)[^.\n]{0,60}"
                    r"(nahi|nahin|not\s+(present|detected|there|formed)|"
                    r"no\s+(kaal|sarp)|absent|none|na\s+ho))|"
                    r"((not|no|absent|nahi|nahin)[^.\n]{0,30}"
                    r"(kaal\s*sarp|sarp\s*dosh))", text or ""))

                if _ks_actual:
                    # Yoga IS present — ensure exact variant cited
                    _variant = _reCY.search(
                        r"\(([^)]+)\s+variant\)", _ks_actual.get("name", "")
                    )
                    _vname = _variant.group(1) if _variant else "unspecified"
                    if not _reCY.search(rf"(?i){_reCY.escape(_vname)}", text or ""):
                        text = (text or "") + (
                            f"\n\n📌 Deterministic Kaal Sarp signal: "
                            f"**{_ks_actual['name']}** PRESENT — "
                            f"{_ks_actual.get('detail','')}"
                        )
                else:
                    # Yoga is NOT present — strip any false-positive sentences
                    if _ans_claims_ks and not _ans_denies_ks:
                        # Surgical strip: remove sentences that falsely claim Kaal Sarp
                        _sentences = _reCY.split(r"(?<=[.!?])\s+", text or "")
                        _kept = []
                        for _s in _sentences:
                            if _reCY.search(
                                r"(?i)(kaal\s*sarp|sarp\s*dosh)[^.\n]{0,40}"
                                r"(hai|present|yes|haan|mild|partial|detected|"
                                r"exists|banaa|bana)", _s
                            ):
                                continue   # drop the false claim
                            _kept.append(_s)
                        text = " ".join(_kept).strip()
                        # Append the deterministic truth
                        _absent_entry = next(
                            (y for y in _ks_entries if "NOT" in y.get("name", "")),
                            None
                        )
                        _detail = (_absent_entry.get("detail", "")
                                   if _absent_entry
                                   else "all 7 planets not enclosed by Rahu↔Ketu axis")
                        text = text + (
                            f"\n\n📌 Deterministic Kaal Sarp check: "
                            f"**NOT PRESENT** — {_detail}. "
                            "Aapke chart mein Kaal Sarp dosh nahi hai."
                        )
                    elif not _ans_claims_ks and not _ans_denies_ks:
                        # Answer didn't address it at all — append clear absence
                        text = (text or "") + (
                            "\n\n📌 Deterministic Kaal Sarp check: "
                            "**NOT PRESENT** — aapke chart mein Kaal Sarp "
                            "configuration nahi hai (planets Rahu↔Ketu axis "
                            "ke beech enclosed nahi hain)."
                        )

            # ── Dhana yoga anti-hallucination ───────────────────────────
            _is_dhana_q = bool(_reCY.search(
                r"(?i)dhana?\s*yog|wealth\s*yog|paisa\s*yog|"
                r"daulat|samriddhi|prosperity", _qCY))
            if _is_dhana_q:
                _dhana_list = [y for y in _yogas if y.get("category") == "Dhana"]
                _ans_cites_dhana = bool(_reCY.search(
                    r"(?i)dhana?\s*yog", text or ""))
                if _dhana_list and not _ans_cites_dhana:
                    _top = _dhana_list[0]
                    text = (text or "") + (
                        f"\n\n📌 Deterministic Dhana signal: "
                        f"**{_top['name']}** — {_top.get('detail','')}"
                    )
                elif not _dhana_list and _ans_cites_dhana:
                    text = (text or "") + (
                        "\n\n📌 Deterministic Dhana check: koi pre-defined "
                        "Dhana yoga (1L+2L/5L/9L/11L type lord-pair) "
                        "detect nahi hua. Wealth ke liye general planetary "
                        "strength + dasha period dekhna padega."
                    )

            # ── Vipreet Raja anti-hallucination ─────────────────────────
            _is_vipreet_q = bool(_reCY.search(
                r"(?i)vipreet|vipareet|harsha|sarala|vimala", _qCY))
            if _is_vipreet_q:
                _vip_list = [y for y in _yogas if y.get("category") == "Vipreet Raja"]
                _ans_cites_vip = bool(_reCY.search(
                    r"(?i)harsha|sarala|vimala", text or ""))
                if _vip_list and not _ans_cites_vip:
                    _top = _vip_list[0]
                    text = (text or "") + (
                        f"\n\n📌 Deterministic Vipreet signal: "
                        f"**{_top['name']}** — {_top.get('detail','')}"
                    )
                elif not _vip_list:
                    text = (text or "") + (
                        "\n\n📌 Deterministic Vipreet check: aapke chart mein "
                        "Harsha (6L), Sarala (8L), ya Vimala (12L) "
                        "konfiguration nahi hai — none of the dusthana lords "
                        "are placed in 6/8/12 houses."
                    )
        except Exception as _excCY:
            print(f"[ai_ask] Classical Yogas (Sprint-19) post-inject failed: {_excCY}")

    # Sprint-14 Rule V — DETERMINISTIC STHIRA + NIRYANA SHOOLA INJECTION
    # For timing questions, append a one-line cross-check from each dasha if not
    # already cited. Only fires if the question is timing-flavored.
    if isinstance(kundli, dict) and kundli.get("planets") and not _skip_post_injects:
        try:
            import re as _reSN
            _qSN = (question or "").lower()
            _is_timing = bool(_reSN.search(
                r"\b(kab|when|next|kitne|future|samay|window|period|"
                r"upcoming|coming|aane|aayega|aayegi|hoga|hogi|"
                r"shaadi|marriage|career|naukri|promotion|child|santaan)\b",
                _qSN
            ))
            if _is_timing:
                from extra_jaimini_dashas import (compute_sthira_dasha,  # type: ignore
                                                  compute_niryana_shoola)
                _lgSN = kundli.get("ascendant") or kundli.get("lagna")
                _lgsSN = _lgSN.get("sign") if isinstance(_lgSN, dict) else _lgSN
                _dobSN = birth if birth else None
                # Sthira
                if (not _skip_verbose_jargon
                        and not _reSN.search(r"(?i)sthira", text or "")
                        and not _wealth_structured_payload):
                    _sth = compute_sthira_dasha(_lgsSN, _dobSN) or {}
                    _md = _sth.get("current_md") or {}
                    if _md.get("sign"):
                        text = (text or "").rstrip() + (
                            f"\n\nSthira Dasha (Jaimini stability layer) — "
                            f"abhi {_md['sign']} MD ({_md['length_years']} yrs, "
                            f"{_md['start']}→{_md['end']}, "
                            f"{_md.get('years_elapsed','?')}/"
                            f"{_md['length_years']} elapsed) — "
                            f"life-stability theme is colored by "
                            f"{_md['sign']}."
                        )
                # Niryana Shoola
                if (not _skip_verbose_jargon
                        and not _reSN.search(r"(?i)niryana|shoola", text or "")
                        and not _wealth_structured_payload):
                    _nir = compute_niryana_shoola(_lgsSN, _dobSN) or {}
                    _mdN = _nir.get("current_md") or {}
                    if _mdN.get("sign"):
                        text = (text or "").rstrip() + (
                            f"\n\nNiryana Shoola Dasha (longevity / "
                            f"life-direction) — abhi {_mdN['sign']} MD "
                            f"(9 yrs, {_mdN['start']}→{_mdN['end']}, "
                            f"{_mdN.get('years_elapsed','?')}/9 elapsed)."
                        )
        except Exception as _exc:
            print(f"[ai_ask] Sthira/Niryana post-inject failed: {_exc}")

    # Sprint-13 Rule U — DETERMINISTIC ARGALA INJECTION (last-resort).
    # If the answer concerns marriage/career/finance/child/health and a relevant
    # house has STRONG-BENEFIC or STRONG-MALEFIC argala, append a single clause.
    if isinstance(kundli, dict) and kundli.get("planets") and not _skip_post_injects:
        try:
            import re as _reAR
            _qAR = (question or "").lower()
            _topic_houses_AR = {
                "marriage":  [7, 2],
                "career":    [10, 6],
                "finance":   [2, 11],
                "child":     [5, 9],
                "health":    [1, 6],
            }
            _kw_topic = None
            if topic in _topic_houses_AR:
                _kw_topic = topic
            else:
                if _reAR.search(r"(shaadi|shadi|vivah|marriage|spouse|partner|patni|pati|rishta)", _qAR):
                    _kw_topic = "marriage"
                elif _reAR.search(r"(career|naukri|job|business|kaam|promotion|kaam-kaaj)", _qAR):
                    _kw_topic = "career"
                elif _reAR.search(r"(paisa|wealth|finance|dhan|money|earning|income|kamai)", _qAR):
                    _kw_topic = "finance"
                elif _reAR.search(r"(child|santaan|baby|pregnan|garbh|aulaad)", _qAR):
                    _kw_topic = "child"
                elif _reAR.search(r"(health|bimari|swasth|disease|rog|illness)", _qAR):
                    _kw_topic = "health"
            if (_kw_topic and not _skip_verbose_jargon
                    and not _reAR.search(r"(?i)argala", text or "")):
                from argala import compute_argala  # type: ignore
                _lgAR = kundli.get("ascendant") or kundli.get("lagna")
                _lgsAR = _lgAR.get("sign") if isinstance(_lgAR, dict) else _lgAR
                _arg = compute_argala(kundli.get("planets") or [], _lgsAR)
                _hh = _topic_houses_AR[_kw_topic][0]
                _info = (_arg or {}).get(_hh) or {}
                _ov = _info.get("overall") or "NEUTRAL"
                if _ov in ("STRONG-BENEFIC", "STRONG-MALEFIC", "MIXED"):
                    # find the strongest contributing slot
                    _bits = []
                    for sig in (_info.get("argala_signals") or []):
                        if sig["planets_argala"]:
                            _bits.append(
                                f"{sig['slot']}-house se "
                                f"{', '.join(sig['planets_argala'])} "
                                f"({sig['verdict']})"
                            )
                    _join = "; ".join(_bits[:2]) if _bits else _ov
                    text = (text or "").rstrip() + (
                        f"\n\nArgala (Jaimini intervention) — "
                        f"H{_hh} ({_info.get('house_sign','')}) overall "
                        f"{_ov}: {_join}."
                    )
        except Exception as _exc:
            print(f"[ai_ask] Argala post-inject failed: {_exc}")

    # Sprint-7 Rule O — DETERMINISTIC UPAPADA LAGNA INJECTION (last-resort).
    # Marriage answers MUST cite UL + UL-lord placement. If model skipped it,
    # append a one-line UL signature so Rule O is satisfied 100%.
    if isinstance(kundli, dict) and kundli.get("planets") and not _skip_post_injects:
        try:
            import re as _reUL
            _qUL = (question or "").lower()
            _is_marriage_q = (
                topic == "marriage"
                or bool(_reUL.search(
                    r"(shaadi|shadi|vivah|marriage|spouse|partner|"
                    r"husband|wife|patni|pati|life\s*partner|"
                    r"jeevan\s*sathi|relationship|rishta)",
                    _qUL
                ))
            )
            if (_is_marriage_q and not _skip_verbose_jargon
                    and not _reUL.search(r"(?i)upapada|\bUL\b", text or "")):
                from jaimini import compute_arudha_padas, compute_upapada  # type: ignore
                _lgUL = kundli.get("ascendant") or kundli.get("lagna")
                _lgsign_UL = _lgUL.get("sign") if isinstance(_lgUL, dict) else _lgUL
                _ar = compute_arudha_padas(kundli.get("planets") or [], _lgsign_UL)
                _up = compute_upapada(_ar, kundli.get("planets") or [])
                if _up and _up.get("ul_sign"):
                    _occ_2nd = _up.get("occupants_2nd") or []
                    _occ_part = (
                        f", 2nd-from-UL ({_up['second_from_ul']}) mein "
                        + ", ".join(_occ_2nd)
                        if _occ_2nd else
                        f", 2nd-from-UL ({_up['second_from_ul']}) khaali"
                    )
                    _ul_lord_part = (
                        f"; UL-lord {_up['ul_lord']} {_up['ul_lord_in']} mein "
                        f"({_up['ul_lord_house']}th from UL)"
                        if _up.get("ul_lord_in") else ""
                    )
                    text = (text or "").rstrip() + (
                        f"\n\nUpapada Lagna (Jaimini marriage signature): "
                        f"UL {_up['ul_sign']}{_ul_lord_part}{_occ_part}. "
                        f"Verdict — {_up.get('verdict','')}."
                    )
        except Exception as _exc:
            print(f"[ai_ask] Upapada post-inject failed: {_exc}")

    # Sprint-8 Rule P — DETERMINISTIC CHARA DASHA INJECTION (last-resort).
    # Append a Chara MD/AD line for marriage answers OR any timing question
    # ("kab", "when", "next", "kitne saal", etc.) so Rule P is satisfied 100%.
    if isinstance(kundli, dict) and kundli.get("planets") and not _skip_post_injects:
        try:
            import re as _re
            _q_lower = (question or "").lower()
            _is_timing_q = bool(_re.search(
                r"\b(kab|when|next|kitne|future|samay|window|period|"
                r"upcoming|coming|aane|aayega|aayegi|hoga|hogi)\b",
                _q_lower
            ))
            _need_chara = (
                topic in ("marriage", "career", "finance", "child")
                or (_is_timing_q and topic != "remedy")
            )
            if (_need_chara and not _skip_verbose_jargon
                    and not _re.search(r"(?i)chara dasha", text or "")):
                from chara_dasha import compute_chara_dasha  # type: ignore
                _lg2 = kundli.get("ascendant")
                if isinstance(_lg2, dict):
                    _lg2 = _lg2.get("sign") or _lg2.get("name")
                _dob = None
                if isinstance(birth, dict):
                    _dob = birth.get("date") or birth.get("dob") or birth
                _cd = compute_chara_dasha(
                    kundli.get("planets") or [], _lg2, _dob
                )
                _md = _cd.get("current_md") if _cd else None
                _ad = _cd.get("current_ad") if _cd else None
                if _md and not _wealth_structured_payload:
                    _ad_part = (
                        f", AD {_ad['sign']} ({_ad['lord']}) {_ad['start']}→{_ad['end']}"
                        if _ad else ""
                    )
                    chara_sentence = (
                        f"\n\nChara Dasha (Jaimini timing) mein abhi "
                        f"{_md['sign']} MD chal raha hai (lord {_md['lord']}, "
                        f"{_md['start']}→{_md['end']}, "
                        f"{_md.get('years_elapsed','?')}/{_md['length_years']} "
                        f"years elapsed{_ad_part}) — yeh Vimshottari ke saath "
                        f"cross-check ke liye use karein: dono dasha agar "
                        f"same theme dikhayein toh window high-confidence hai."
                    )
                    text = (text or "").rstrip() + chara_sentence
        except Exception as _exc:
            print(f"[ai_ask] Chara post-inject failed: {_exc}")

    # ── Sprint-22 STRICT BREVITY POST-TRIM ─────────────────────────────────────
    # User explicitly directed: "Question ek line ka he ans maximum 2-3 line ka
    # hona chahiye … Jo pucha Wahi ans doge". The model frequently still adds
    # unsolicited Mahadasha / Antardasha / transit / Manglik-dosh / aspect /
    # KP lines on short single-planet strength questions even though the
    # prompt forbids it. This deterministic trim runs ONLY when the question
    # is a short-single-planet-strength ask and rips out the off-topic tail.
    if _is_short_planet_strength_q and isinstance(text, str) and text.strip():
        try:
            import re as _reTrim
            # Split into sentences while preserving punctuation.
            _raw_paras = [p.strip() for p in text.split("\n") if p.strip()]
            _sents: list[str] = []
            for _p in _raw_paras:
                _sents.extend(
                    s.strip() for s in _reTrim.split(r"(?<=[.!?।])\s+", _p)
                    if s.strip()
                )

            # OFF-TOPIC pattern → drop these sentences entirely.
            _OFF_TOPIC_RX = _reTrim.compile(
                r"(?i)\b("
                r"mahadasha|antardasha|antar\s*dasha|pratyantar|"
                r"\bdasha\b|dasha\s+lord|"
                r"transit(?:ing)?|gochar|"
                r"manglik|mangal\s*dosh|kuja\s*dosh|"
                r"sade\s*sati|sadhe\s*sati|saade\s*sati|"
                r"ashtakavarga|ashtak\s*varga|sav\b|bhinnashtaka|"
                r"\bkp\b|cusp|sub[\s\-]*lord|"
                r"jaimini|arudha|upapada|chara\s*karaka|atmakaraka|"
                r"shadbala|saptavargaja|ishta\s*phala|kashta\s*phala|"
                r"vimshopaka|yuddha\s*bala|bhava\s*bala|"
                r"vrishchika|kemadruma|daridra|shakata|kaal\s*sarp|"
                r"remedy|upay|mantra|jaap|donate|daan|gemstone|"
                r"d1[06]|d2[047]|d3\d|d40|d45|d60|"
                r"chaturvimsamsa|trimsamsa|shashtyamsa|"
                r"vimsamsa|bhamsa|drekkana|saptamsa|hora|dwadasamsa|"
                r"2nd\s+house|3rd\s+house|4th\s+house|5th\s+house|"
                r"6th\s+house|7th\s+house|8th\s+house|9th\s+house|"
                r"10th\s+house|11th\s+house|12th\s+house"
                r")\b"
            )
            # ON-TOPIC anchor — must mention at least one of these to be kept.
            _ON_TOPIC_RX = _reTrim.compile(
                r"(?i)\b("
                r"d1\b|d9\b|navamsa|vargottama|neecha[\s\-]*bhanga|"
                r"exalted|debilitated|own[\s\-]*sign|own\s*house|"
                r"uchcha|neech|swarashi|moolatrikona|friendly|enemy|"
                r"strong|weak|moderate|powerful|kamzor|kamjor|shaktishali|"
                r"shakti|takat|takatwar|takatvar|good|achha|achchha|accha|"
                r"sun|surya|suraj|moon|chandra|chand|mars|mangal|mangala|"
                r"mercury|budh|budha|jupiter|guru|brihaspati|brahaspati|"
                r"venus|shukra|shukr|saturn|shani|sani|rahu|ketu|"
                r"mesh|vrishabh|mithun|kark|simha|kanya|tula|"
                r"vrischik|vrishchik|dhanu|makar|kumbh|meen|"
                r"aries|taurus|gemini|cancer|leo|virgo|libra|"
                r"scorpio|sagittarius|capricorn|aquarius|pisces"
                r")\b"
            )

            _kept: list[str] = []
            for _s in _sents:
                if _OFF_TOPIC_RX.search(_s):
                    continue
                if _ON_TOPIC_RX.search(_s):
                    _kept.append(_s)
            # Keep at most 3 sentences (user directive: "max 2-3 line").
            _kept = _kept[:3]
            if _kept:
                _new_text = " ".join(_kept).strip()
                # Make sure the trim didn't accidentally nuke the entire reply.
                if len(_new_text.split()) >= 8:
                    if _new_text != text.strip():
                        print(
                            f"[ai_ask][brevity-trim] short-planet-strength Q: "
                            f"{len(text.split())}w → {len(_new_text.split())}w "
                            f"({len(_sents)} sents → {len(_kept)} kept)"
                        )
                        text = _new_text
        except Exception as _exc:
            print(f"[ai_ask] brevity post-trim failed: {_exc}")

    # ── Phase 4.8 T019 — NARRATIVE-MODE POST-PROCESS TRUNCATOR ─────────────
    # User-reported (Apr 28, 2026, post-T017+T018): even after dropping
    # PRATYANTAR/DASHA WINDOW from the input AND replacing Rule 10 with
    # a 1-2 sentence HARD CAP, the model still emitted 6-8 line answers
    # with date ranges ("2026-06-22 tak"), pratyantar names ("Moon
    # Pratyantar", "Mars Pratyantar"), and full dasha breakdowns —
    # because the model has 28K tokens of training-bias toward
    # "explain your reasoning". The only reliable fix is post-generation
    # discipline: strip dates+sub-period jargon BEFORE the user sees it,
    # then truncate to first 2 sentences.
    #
    # Four controls (per user spec):
    #   1. Intent lock — only fires for narrative mode (decision queries)
    #   2. Timing filter — IF question doesn't contain {kab/when/date/
    #      timeline/kitna time/date kya/timing}, strip date patterns +
    #      pratyantar/antardasha mentions from the answer.
    #   3. Hard length cut — keep first 2 meaningful sentences max.
    #   4. Format enforcer — preserve [VERDICT] → [reason] shape.
    # Phase 5.0 Final Strip: the truncator is a TIER+FORMAT controller — it
    # caps to N sentences/chars based on the question tier and strips date
    # ranges per format rules. User spec ("tier hacks jo prompt ke andar
    # likhe hain" + "format wale validators") bans these in the minimal
    # path. Hallucination guards (TIMING_VALIDATOR + POST_LOGIC_CHECK)
    # remain active above. NOTE: TIMING_VALIDATOR already invalidates
    # invented date tokens, so the truncator's date-strip is redundant in
    # the minimal path; trusting the model + the validator is the new contract.
    if _NARRATIVE_MODE and not _phase50_active and isinstance(text, str) and text.strip():
        try:
            _trimmed = _phase48_narrative_truncate(text, question or "")
            if _trimmed != text:
                _orig_lines = len([l for l in text.split("\n") if l.strip()])
                _new_lines = len([l for l in _trimmed.split("\n") if l.strip()])
                # Architect-flagged: include timing_q in telemetry so a
                # production "missing dates" complaint can be debugged
                # by checking whether the question was classified as
                # timing (in which case dates SHOULD have survived).
                _is_timing_q = _phase48_is_timing_question(question or "")
                print(f"[ai_ask][phase48-trim] NARRATIVE_MODE truncate: "
                      f"{len(text)}c/{_orig_lines}l → "
                      f"{len(_trimmed)}c/{_new_lines}l "
                      f"(timing_q={_is_timing_q})")
                text = _trimmed
        except Exception as _exc:
            print(f"[ai_ask] Phase 4.8 T019 narrative truncator failed: {_exc}")
    elif _phase50_active and _NARRATIVE_MODE:
        _trace(req_id, "phase48.TRUNCATOR_SKIPPED", {
            "reason": "phase50 minimal-prompt path — format/tier validators disabled",
            "raw_chars": len(text) if isinstance(text, str) else 0,
        })

    # ── GLOBAL PLACEHOLDER STRIP (unconditional final scrub) ────────────────
    # Sprint-26 brutal-test surfaced a real bug: the timing-validator
    # placeholders ([engine: dasha not cited] / [engine: window pending] /
    # [engine: year/month ...]) leak through to user-facing text whenever
    # neither the HEALTH nor WEALTH brand-safety post-processor fires (e.g.
    # general-topic PROBLEM_QUERY answers). Those gated scrubbers at
    # lines ~6515 (health) and ~6755 (wealth) duplicate the same regex but
    # only run when their respective verdict objects are present. We keep
    # those in place (they also do bucket-specific cite injection) but add
    # this UNCONDITIONAL global strip as the very last text mutation, so no
    # supertype can leak placeholders to the user.
    #
    # Sprint-26 hard-test (20 questions) follow-up: simple bracket strip is
    # not enough — the AI sometimes emits TEMPLATE SKELETONS like
    # "tab hoga jab dasha khatam hogi aur dasha shuru hogi" (two bare "dasha"
    # tokens with no planet / MD / AD name to ground them) or
    # " ke baad dasha shuru hogi" (orphan leading-particle line, the leading
    # space is the residue of a stripped "[Planet]" placeholder). Both are
    # useless to the user and look broken. Extended this scrub to:
    #   (a) drop sentences with 2+ bare "dasha" tokens AND no planet /
    #       Mahadasha / Antardasha / Pratyantardasha / MD/AD/PD anchor in
    #       the same sentence, and
    #   (b) drop lines whose only content begins with whitespace + a Hindi
    #       connective particle (ke/ka/ki/me/mein/se/tak/ko) — these are
    #       always template-fragment leftovers.
    try:
        import re as _re_global_ph

        _global_ph_rx = _re_global_ph.compile(
            r"\[engine:\s*(?:dasha not cited|window pending|"
            r"year[^\]]*|month[^\]]*)\]",
            _re_global_ph.IGNORECASE,
        )
        # Anchors that legitimise a bare "dasha" token in a sentence.
        # Architect-recommended expansion: include bhukti / vimshottari /
        # yogini / char / hyphenated antar-dasha / spaced pratyantar dasha /
        # Devanagari महादशा / अंतरदशा / प्रत्यंतर forms.
        _dasha_anchor_rx = _re_global_ph.compile(
            r"\b(?:jupiter|saturn|mars|mercury|venus|sun|moon|rahu|ketu|"
            r"surya|chandra|mangal|budh|guru|shukra|shani|"
            r"mahadasha|antardasha|pratyantardasha|"
            r"antar[\s\-]dasha|pratyantar[\s\-]dasha|"
            r"bhukti|vimshottari|yogini|char[\s\-]dasha|"
            r"\bmd\b|\bad\b|\bpd\b)|"
            r"महादशा|अंतरदशा|अन्तर्दशा|प्रत्यंतर|प्रत्यन्तर",
            _re_global_ph.IGNORECASE,
        )
        _bare_dasha_rx = _re_global_ph.compile(r"\bdasha\b", _re_global_ph.IGNORECASE)
        # Verb pattern that distinguishes a TEMPLATE skeleton (fill-in
        # expectation that never happened) from a legitimate Vedic concept
        # explanation. Skeletons say "<dasha> khatam/shuru/chal raha/weak/
        # strong hai/hogi"; concept lines say "<dasha> badalta hai" /
        # "<dasha> ka concept hai" / "<dasha> mein sub-dasha hoti hai".
        _skeleton_verb_rx = _re_global_ph.compile(
            r"\b(?:khatam|shuru|chal\s+raha|chal\s+rahi|weak|strong|"
            r"weak\s+hai|strong\s+hai|chal\s+raha\s+hai|chal\s+rahi\s+hai)\b",
            _re_global_ph.IGNORECASE,
        )
        # Orphan leading-particle line — only drop SHORT lines (≤8 words),
        # because legitimate wrapped continuation lines are usually longer.
        _orphan_lead_rx = _re_global_ph.compile(
            r"^\s+(?:ke|ka|ki|me|mein|se|tak|ko)\s",
            _re_global_ph.IGNORECASE,
        )
        _bad_line_rx = _re_global_ph.compile(
            r"^\s*(?:dasha\s+ke\s+dasha|"
            r"engine\s+data\s+insufficient|"
            r"⚐\s*Note:\s*precise\s+dates).*$",
            _re_global_ph.IGNORECASE,
        )

        if text:
            _changed = False
            # Snapshot the pre-scrub text so we can rollback if our scrub
            # accidentally destroys too much (worst-case: AI generated
            # all-template-skeleton output and every sentence gets dropped,
            # leaving an empty response — empty is worse than ugly).
            _pre_scrub_text = text
            _pre_scrub_word_count = len(text.split())
            # DEBUG: dump full pre-scrub text so we can show user exactly
            # what AI generated before any post-processing.
            _trace(req_id, "4y.AI_RAW_PRE_SCRUB",
                   {"text": text, "word_count": _pre_scrub_word_count})

            # Sprint-26 Fix-K (FIX 4) — MINIMAL SCRUB:
            # Steps (2) sentence-line drops and (3) template-skeleton drops
            # were band-aids for placeholder-injection that the smart
            # validator (FIX 1) now PREVENTS at the source. Keeping them
            # here would over-correct and risk dropping legitimate AI
            # narration. We now do ONLY:
            #   (1) Strip [engine: ...] placeholder brackets if any
            #       leak through (e.g. when validator legitimately
            #       rejects with engine_overall=ok).
            #   (2) Drop the ⚐ "engine data insufficient" notice line —
            #       still emitted by enforce_timing_lock when it does run.
            # The aggressive sentence/skeleton scrubs are GONE.
            if _global_ph_rx.search(text):
                text = _global_ph_rx.sub("", text)
                # Collapse empty parens / repeated whitespace / orphan punct
                # left behind by the strip.
                text = _re_global_ph.sub(r"\(\s*se\s*\)", "", text)
                text = _re_global_ph.sub(r"\(\s*\)", "", text)
                text = _re_global_ph.sub(r"\s+([,.;!?])", r"\1", text)
                text = _re_global_ph.sub(r"[ \t]+", " ", text)
                _changed = True

            # (2) Only drop the "⚐ Note: precise dates ONLY..." notice
            # line emitted by enforce_timing_lock. Everything else stays.
            _kept_lines = []
            for _ln in text.splitlines():
                if _bad_line_rx.search(_ln):
                    _changed = True
                    continue
                _kept_lines.append(_ln)
            text = "\n".join(_kept_lines).strip()

            # (4) ROLLBACK GUARD — if the scrub has destroyed too much of
            # the original content (e.g. AI generated all-template text and
            # every sentence got dropped), restore the pre-scrub text. An
            # ugly answer is materially better for the user than an empty
            # one. Architect-corrected thresholds:
            #   * Always rollback if scrubbed text is empty.
            #   * Only enforce the 30-word ABSOLUTE floor when the original
            #     was substantial (>50 words). Short originals can produce
            #     legitimately short answers — don't punish them.
            #   * Enforce 30% RELATIVE floor only when original >50 words.
            # CRITICAL safety: when rolling back, ALWAYS re-strip the
            # `[engine: ...]` bracket placeholders first — restoring raw
            # pre-scrub text would re-leak internal markers and defeat the
            # scrub's primary objective. Skeleton residue in the rolled-
            # back text is acceptable (it's just ugly text) but bracket
            # placeholders MUST never reach the user.
            if _changed:
                _post_word_count = len(text.split())
                _is_empty = not text
                _too_short_absolute = (
                    _pre_scrub_word_count > 50
                    and _post_word_count < 30
                )
                _too_short_relative = (
                    _pre_scrub_word_count > 50
                    and _post_word_count
                    < max(30, int(_pre_scrub_word_count * 0.30))
                )
                if _is_empty or _too_short_absolute or _too_short_relative:
                    # Safe rollback: re-strip bracket placeholders from
                    # pre-scrub text so we never re-leak them.
                    _safe_rollback = _global_ph_rx.sub("", _pre_scrub_text)
                    _safe_rollback = _re_global_ph.sub(
                        r"\(\s*se\s*\)", "", _safe_rollback)
                    _safe_rollback = _re_global_ph.sub(
                        r"\(\s*\)", "", _safe_rollback)
                    _safe_rollback = _re_global_ph.sub(
                        r"\s+([,.;!?])", r"\1", _safe_rollback)
                    _safe_rollback = _re_global_ph.sub(
                        r"[ \t]+", " ", _safe_rollback)
                    _trace(req_id, "4z.GLOBAL_PH_STRIP_ROLLBACK", {
                        "reason": "scrub removed too much content — "
                                  "restoring bracket-stripped pre-scrub "
                                  "text (skeleton residue acceptable, "
                                  "placeholders never re-leaked)",
                        "trigger": ("empty" if _is_empty
                                    else "abs_floor" if _too_short_absolute
                                    else "rel_floor"),
                        "pre_words": _pre_scrub_word_count,
                        "post_words": _post_word_count,
                        "rollback_words": len(_safe_rollback.split()),
                    })
                    text = _safe_rollback.strip()
                else:
                    _trace(req_id, "4z.GLOBAL_PH_STRIP",
                           {"reason": "unconditional final scrub of "
                                      "[engine: ...] placeholders + "
                                      "template-skeleton sentences + "
                                      "orphan leading-particle lines",
                            "pre_words": _pre_scrub_word_count,
                            "post_words": _post_word_count})
    except Exception as _ph_exc:  # noqa: BLE001
        _trace(req_id, "4z.GLOBAL_PH_STRIP_ERR", str(_ph_exc))

    follow_ups = _derive_follow_ups(topic, eff_lang)
    # ── Sprint-26 Step 4 Phase 3 v2 — POST_LOGIC SAFETY RE-CHECK ───────
    # Architect-required final guarantee: downstream validators (timing,
    # scrub, GLOBAL_PH_STRIP, jargon-inject) can rewrite the text after
    # POST_LOGIC_CHECK ran. A rewrite could (in theory) re-introduce a
    # truth violation. This is a CHEAP no-retry re-check: if the served
    # text still has any high-severity violation, refuse. Skips when
    # text is already the refusal template (idempotent) or when the
    # check is disabled by env.
    try:
        if (text and text.strip() != _POST_LOGIC_REFUSAL_TEXT.strip()
                and os.environ.get("POST_LOGIC_CHECK", "1") != "0"
                and isinstance(kundli, dict)):
            _safety_truth = _build_truth_facts(kundli)
            _safety_violations = _post_logic_check(text, _safety_truth)
            if _safety_violations:
                _trace(req_id, "2v.POST_LOGIC_CHECK_POST_TIMING_REFUSAL", {
                    "reason": "downstream validators left/introduced truth "
                              "violations in served text — refusing",
                    "residual_violations": _safety_violations,
                    "served_text": "_POST_LOGIC_REFUSAL_TEXT",
                })
                text = _POST_LOGIC_REFUSAL_TEXT
            else:
                _trace(req_id, "2v.POST_LOGIC_CHECK_POST_TIMING_CLEAN", {
                    "stage": "post-timing-final-safety"
                })
    except Exception as _safety_exc:
        _trace(req_id, "2v.POST_LOGIC_CHECK_POST_TIMING_ERR",
               {"error": str(_safety_exc)[:200]})

    # Phase 4.2 (Apr 28, 2026) — engine warning footer for OPTIONAL-phase
    # failures. If only Sprint-33+ optional phases (transits/tajik/sahams/
    # special-lagnas) failed/skipped, the main answer survives but we surface
    # the gap to the user transparently. Skip if (a) text is already a
    # refusal template, (b) footer marker already present (idempotency).
    try:
        if (text
                and isinstance(text, str)
                and text.strip() != _ENGINE_HONESTY_REFUSAL_TEXT.strip()
                and text.strip() != _POST_LOGIC_REFUSAL_TEXT.strip()
                and _ENGINE_WARN_FOOTER_MARKER not in text):
            _hon_warn = _engine_honesty_check(
                (build_meta or {}).get("engine_status") or {},
                qu=locals().get("_qu"),
            )
            if _hon_warn.get("warn"):
                text = text.rstrip() + _ENGINE_WARN_FOOTER_TEXT
                _trace(req_id, "4c.ENGINE_WARNING_INJECTED", {
                    "path": "oneshot",
                    "optional_failed": _hon_warn.get("optional_failed", []),
                    "reason": _hon_warn.get("reason"),
                })
    except Exception as _warn_exc:  # noqa: BLE001
        _trace(req_id, "4c.ENGINE_WARNING_ERR", str(_warn_exc)[:200])

    _trace(req_id, "5.FINAL_OUTPUT", text)
    _trace(req_id, "6.FOLLOW_UPS", {
        "topic": topic, "lang": eff_lang, "items": follow_ups,
        "behavior": "follow-up chips are deterministic per (topic, lang); "
                    "the NEXT user turn is reclassified independently — "
                    "mode does NOT inherit from this turn",
    })
    _result = {
        "text":       text,
        "topic":      topic,
        "topic_source": (build_meta or {}).get("topic_source") or "regex",
        "confidence": confidence,
        "source":     "openai",
        "follow_ups": follow_ups,
        "question_intent": question_intent,
        "question_supertype": question_supertype,
        "intent_extraction": (build_meta or {}).get("intent_extraction"),
    }
    if _wealth_structured_payload is not None:
        _result["structured"] = _wealth_structured_payload
    return _result


# ── Streaming variant ────────────────────────────────────────────────────────
# ai_ask_stream() yields dict events for the Flask SSE route to forward.
#   {"kind": "oneshot", "data": {...}}   — non-streamable (brand_guard /
#                                          no_chart / marriage); send as JSON.
#   {"kind": "delta",   "text": "..."}   — incremental token chunk.
#   {"kind": "final",   "text": "...", "topic": "...", "confidence": x.x,
#                       "follow_ups": [...], "source": "openai_stream"}
# The marriage path stays one-shot deterministic (no faux-stream); brand
# guard and no-chart fail-safes likewise. Everything else streams.
def ai_ask_stream(question: str, kundli: Any, lang: str = "en", reply_idx: int = 0,
                  birth: Any = None, history: list | None = None,
                  preferred_language: Optional[str] = None):
    req_id = _short_id()
    _trace(req_id, "1.RAW_INPUT(stream)", {
        "question": question, "lang_param": lang,
        "preferred_language": preferred_language, "reply_idx": reply_idx,
        "history_len": len(history or []),
        "kundli.has_planets": isinstance(kundli, dict) and bool(kundli.get("planets")),
        "kundli.has_dasha":   isinstance(kundli, dict) and bool(kundli.get("currentDasha")),
    })
    # Brand-safety gate — non-streamable.
    if _is_brand_unsafe(question):
        _trace(req_id, "2.MODE_DETECT", {"path": "brand_guard → oneshot"})
        yield {"kind": "oneshot",
               "data": ai_ask(question, kundli, lang, reply_idx, birth=birth,
                              history=history, preferred_language=preferred_language)}
        return

    # No chart — non-streamable fail-safe.
    has_planets = isinstance(kundli, dict) and bool(kundli.get("planets"))
    if not has_planets:
        _trace(req_id, "2.MODE_DETECT", {"path": "no_chart_failsafe → oneshot"})
        yield {"kind": "oneshot",
               "data": ai_ask(question, kundli, lang, reply_idx, birth=birth,
                              history=history, preferred_language=preferred_language)}
        return

    # Sprint-26: SINGLE AI understanding call — same source of truth as ai_ask.
    from question_understanding import understand_question, supertype_for
    _qu = understand_question(question)
    # Phase 4.1 Fix-P — telemetry parity with ai_ask (non-stream) for the
    # classifier sanity-layer override decision. Stream path does not yet
    # run POST_LOGIC (Phase 4.4 backlog), but it benefits from the same
    # classifier correction since `understand_question` is shared.
    if _qu.get("intent_overridden_from"):
        _trace(req_id, "1b.CLASSIFIER_OVERRIDE", {
            "from":   _qu.get("intent_overridden_from"),
            "to":     _qu.get("intent"),
            "reason": _qu.get("intent_override_reason"),
            "phase":  _qu.get("intent_override_phase"),
            "ai_confidence": _qu.get("confidence"),
            "path":   "stream",
        })
    _qu_intent = (_qu.get("intent") or "analysis").lower()
    _qu_topic  = (_qu.get("topic")  or "general").lower()
    topic = _qu_topic
    mode  = "general" if (_qu_intent == "analysis" and _qu_topic == "general") else "astro"
    _mode_reason = f"qu intent={_qu_intent} topic={_qu_topic}"
    # Sprint-26 Fix-O — Personal-chart override (mirror of ai_ask path).
    if mode == "general":
        try:
            from question_understanding import is_personal_chart_question
            if is_personal_chart_question(question):
                mode = "astro"
                _mode_reason += " → FORCED astro (personal-chart anchor, Fix-O)"
                _trace(req_id, "2.MODE_DETECT.personal_chart_override(stream)", {
                    "rule": "Sprint-26 Fix-O",
                    "reason": "personal possessive next to chart noun",
                })
        except Exception:
            pass
    # Phase 5.5d (Apr 29 2026) — context-memory override mirror of ai_ask
    # path. Bare follow-ups after a love-vs-arrange answer must engage the
    # chart pipeline so the lock fires; see ai_ask for full rationale.
    if (mode != "astro"
            and _phase55_history_was_love_vs_arrange(history)
            and _phase55_is_love_vs_arrange_question(question or "",
                                                     history=history)):
        print("[ai_ask_stream] Phase 5.5d context override: "
              "forcing mode=astro topic=marriage (LvA follow-up)")
        mode = "astro"
        topic = "marriage"
        _mode_reason += " → FORCED astro (Phase 5.5d context-memory)"
    _trace(req_id, "1.UNDERSTANDING(stream)", _qu)
    _trace(req_id, "2.MODE_DETECT", {
        "mode": mode, "topic": topic, "reason": _mode_reason,
    })

    try:
        if mode == "astro" and topic != "marriage" and (
            _detect_marriage_constraint(question, history or [])
            or (_is_generic_followup(question)
                and _last_assistant_topic_was_marriage(history or []))
        ):
            for h in reversed(history or []):
                if h.get("role") == "assistant":
                    prev = ((h.get("content") or h.get("text") or "")).lower()
                    if any(k in prev for k in
                           ("vivah", "shaadi", "shadi", "marriage",
                            "विवाह", "शादी", "spouse", "wife", "husband",
                            "kalatra", "saptam")):
                        topic = "marriage"
                        break
    except Exception as exc:
        print(f"[ai_ask_stream] topic-stickiness check failed: {exc}")

    # General mode forces topic=general (concept question, no chart).
    # Route through ai_ask (oneshot) so the chart-leak validator runs —
    # streaming a general reply token-by-token bypasses post-response
    # validation and lets the model leak the user's kundli into a
    # concept question (which is exactly what we must prevent).
    if mode == "general":
        topic = "general"
        _trace(req_id, "2b.ROUTE", "general → ai_ask oneshot (validators run)")
        yield {"kind": "oneshot",
               "data": ai_ask(question, kundli, lang, reply_idx, birth=birth,
                              history=history, preferred_language=preferred_language)}
        return

    # Marriage astro path — deterministic engine; one-shot to preserve
    # fact-locked window echoing. Streaming a baked answer adds no value.
    if mode == "astro" and topic == "marriage":
        _trace(req_id, "2b.ROUTE", "astro+marriage → ai_ask oneshot "
                                    "(deterministic engine)")
        yield {"kind": "oneshot",
               "data": ai_ask(question, kundli, lang, reply_idx, birth=birth,
                              history=history, preferred_language=preferred_language)}
        return

    # ── Sprint-26 Step 4 Phase 2 — Safe-Narration Gate (stream variant) ────
    # When the deterministic gate would fire (sustained-problem pattern AND
    # no domain anchor), delegate to ai_ask oneshot so the gate runs in a
    # single place. Streaming a clarification adds no value; a 1-line ask
    # is shorter than the stream protocol overhead anyway.
    if (_qu.get("clarification_needed")
            and _qu_intent in ("analysis", "problem")
            and mode != "general"):
        _trace(req_id, "2b.ROUTE", "safe_narration_gate → ai_ask oneshot")
        yield {"kind": "oneshot",
               "data": ai_ask(question, kundli, lang, reply_idx, birth=birth,
                              history=history, preferred_language=preferred_language)}
        return

    client = _get_client()
    if client is None:
        raise RuntimeError(_client_err or "OpenAI client not configured")

    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    # Streaming path is only used for non-marriage astro turns (marriage and
    # general both branch to ai_ask oneshot above), so we don't need the
    # marriage facts meta here — but we still pass an empty out_meta for
    # forward-compat / parity with ai_ask.
    build_meta_stream: dict = {}
    # Sprint-25 Fix-F: streaming variant — pass AI Ear marriage bucket when
    # available (build_meta_stream is empty here, so the helper returns None
    # and we fall back to regex; future stream-side AI Ear work will populate).
    _mar_pre_bucket_stream = _ai_ear_bucket_for(build_meta_stream, "marriage")
    marriage_subtype_stream = (
        _classify_marriage_subtype(question, _mar_pre_bucket_stream)
        if topic == "marriage" else "timing"
    )
    _trace(req_id, "2.MODE_DETECT.subtype(stream)", {
        "topic": topic, "marriage_subtype": marriage_subtype_stream,
    })
    messages = _build_messages(
        question, kundli, lang, reply_idx,
        birth=birth, topic=topic, history=history,
        preferred_language=preferred_language,
        mode=mode,
        out_meta=build_meta_stream,
        marriage_subtype=marriage_subtype_stream,
    )

    # ── Phase 5.0 (Apr 28 2026) — STREAM-PATH MINIMAL ASK PROMPT GATE ──
    # Same flag + behaviour as ai_ask: discard the heavy `messages` list
    # and replace with the 2-message minimal prompt. Engine verdicts still
    # flow as a single fact line. Stream chunking, brand-safety gates and
    # the Phase 4.9 truncator (T025) all still fire downstream.
    _phase50_active_stream = False
    if mode == "astro" and _phase50_minimal_prompt_enabled():
        # Identical install logic as ai_ask — `(stream)` label keeps the
        # trace key distinguishable. No more sync/stream code drift.
        messages, _ = _phase50_install_minimal_messages(
            question or "", kundli, lang, build_meta_stream, req_id,
            path_label="(stream)", topic=topic, history=history,
        )
        _phase50_active_stream = True

    # ── Phase 4.5 — STREAM-PATH NARRATIVE CONTRACT INSTALL ─────────────
    # The sync `ai_ask_v2` path installs the unified narrator contract as
    # the LAST system message (~line 8466). The stream path historically
    # didn't, relying instead on per-topic narrator overrides inside
    # `_build_messages`. In NARRATIVE_MODE we MUST install the unified
    # narrative contract here too, otherwise stream answers retain the
    # legacy multi-paragraph + advisor-cite shape while sync answers get
    # the clean 3-5 sentence narrative — sync/stream parity violation.
    # Gated to narrative mode only so legacy-mode behavior is unchanged.
    # Phase 5.0: ALSO skipped when minimal-prompt path is active.
    if _NARRATIVE_MODE and not _phase50_active_stream:
        # Derive supertype HERE (sync path computes it upstream and packs
        # it into a dict; stream path historically derived it ~110 lines
        # later for the post-completion validator). We need it BEFORE the
        # OpenAI call so the contract is in the prompt — derive once,
        # reuse below.
        try:
            _question_supertype = {
                "supertype":     supertype_for(_qu_intent),
                "confidence":    float(_qu.get("confidence") or 0.0),
                "source":        _qu.get("source") or "ai",
                "source_intent": _qu_intent,
            }
            _supertype_tag_stream = (
                _question_supertype.get("supertype") or "GENERAL_ANALYSIS"
            )
            messages.append({
                "role":    "system",
                "content": _build_supertype_contract(
                    _supertype_tag_stream,
                    has_recovery_subask=bool(
                        _qu.get("has_recovery_subask")
                    ),
                ),
            })
            _trace(req_id, "2e.SUPERTYPE_CONTRACT_INSTALLED(stream)", {
                "supertype":      _supertype_tag_stream,
                "position":       len(messages) - 1,
                "narrative_mode": True,
            })
        except Exception as _sup_exc_s:
            _trace(req_id, "2e.SUPERTYPE_CONTRACT_FAIL(stream)",
                   {"error": str(_sup_exc_s)[:200]})
            # In narrative mode the contract is structural, not optional —
            # surface the failure loudly so it gets caught in dev.
            _question_supertype = None
            _supertype_tag_stream = "GENERAL_ANALYSIS"

    _trace(req_id, "3.PROMPT(stream)", {
        "model": model, "message_count": len(messages),
        "roles": [m["role"] for m in messages],
        "system_preview": (messages[0]["content"][:600] if messages else ""),
        "user_preview":   (messages[-1]["content"][:400] if messages else ""),
        "kundli_injected_in_prompt": any(
            "BIRTH CHART" in (m.get("content") or "")
            or "kundli" in (m.get("content") or "").lower()
            for m in messages),
    })

    raw_chunks: list[str] = []
    try:
        stream = client.chat.completions.create(
            model            = model,
            messages         = messages,
            temperature      = 0.3,
            top_p            = 1,
            max_tokens       = _token_budget_for(topic, question),
            presence_penalty = 0.2,
            frequency_penalty= 0.2,
            stream           = True,
        )
        for chunk in stream:
            try:
                delta = chunk.choices[0].delta.content if chunk.choices else None
            except Exception:
                delta = None
            if delta:
                raw_chunks.append(delta)
                yield {"kind": "delta", "text": delta}
    except Exception as exc:
        raise RuntimeError(f"OpenAI stream failed: {exc}") from exc

    raw_text = ("".join(raw_chunks)).strip()
    if not raw_text:
        raise RuntimeError("OpenAI returned empty stream")
    _trace(req_id, "4.RAW_AI_RESPONSE(stream)", raw_text)

    # ── Phase 5.1 — TOTAL STRIP early-return (stream parity) ──────────────
    # Mirrors the sync `ai_ask` early-return: when PHASE51_BARE_PROMPT=1
    # (default), bypass ALL stream-side post-response validators / mutators
    # / footer-injectors / follow-up generation and yield the raw stream
    # text as the final event. Deltas have already been yielded above as
    # they arrived; the mobile client swaps deltas with `final.text` on
    # `done`, so this single yield is what reaches the user.
    if _phase50_active_stream and _phase51_bare_prompt_enabled():
        _trace(req_id, "5.PHASE51_BARE_RETURN(stream)", {
            "raw_chars": len(raw_text or ""),
            "bypassed": [
                "supertype_contract_validator", "post_logic_check",
                "timing_validator", "jargon_inject", "health_brand_safety",
                "validators_framework", "marriage_validator",
                "wealth_brand_safety", "scrubber", "phase48_truncator",
                "global_ph_strip", "post_logic_check_post_timing",
                "engine_warning_footer", "follow_ups",
            ],
        })
        yield {
            "kind":                  "final",
            "text":                  raw_text,
            "topic":                 topic,
            "confidence":            float((_qu or {}).get("confidence") or 0.0),
            "source":                "openai_stream_bare",
            "follow_ups":            [],
            "replaced_by_validator": False,
        }
        return

    # Phase 5.0 Final Strip: stream-side scrubber gated identically to sync
    # path. STYLE rewriting is removed in the minimal-prompt mode; only
    # correctness validators survive.
    if not _phase50_active_stream:
        final_text = _scrub_brand_tone(raw_text)
        if raw_text != final_text:
            _trace(req_id, "4d.SCRUBBER_CHANGED(stream)", {
                "before_preview": raw_text[:200],
                "after_preview":  final_text[:200],
            })
    else:
        final_text = raw_text
        _trace(req_id, "4d.SCRUBBER_SKIPPED(stream)", {
            "reason": "phase50 minimal-prompt path — style validators disabled",
        })
    if not final_text:
        raise RuntimeError("OpenAI returned empty after scrub")

    # ── Phase 4.4 — STREAM-PATH POST_LOGIC + SUPERTYPE PARITY ─────────────
    # Mirrors the sync ai_ask validator chain (~lines 8240-8370). Streaming
    # cannot abort tokens mid-flight, but mobile clients already swap the
    # accumulated stream text with `final.text` on `done`, so a refusal /
    # retry substitution here is automatically reflected in the UI.
    # `replaced_by_validator` is added to the final SSE event for telemetry
    # so the client can log the substitution (no UI change required).
    replaced_by_validator = False

    def _stream_retry_call(extra_messages: list) -> str:
        """Non-streaming retry. The user has already seen the first attempt
        as streamed deltas; the corrective retry runs invisibly and the
        result lands in the `final` event (mobile swaps automatically).

        Phase 4.4: bounded by `_VALIDATOR_RETRY_TIMEOUT_S` (default 12s)
        — a slow OpenAI retry must NEVER hold the SSE stream open. On
        timeout the OpenAI client raises, the caller's except path fires,
        and the existing retry-error refusal substitution kicks in.
        """
        retry_msgs = list(messages) + list(extra_messages)
        resp = client.chat.completions.create(
            model             = model,
            messages          = retry_msgs,
            temperature       = 0.3,
            top_p             = 1,
            max_tokens        = _token_budget_for(topic, question),
            presence_penalty  = 0.2,
            frequency_penalty = 0.2,
            stream            = False,
            timeout           = _VALIDATOR_RETRY_TIMEOUT_S,
        )
        return ((resp.choices[0].message.content or "").strip()
                if resp.choices else "")

    # ── Supertype contract validator ─────────────────────────────────────
    try:
        _supertype_validator_enabled = (
            os.environ.get("SUPERTYPE_VALIDATOR", "1") != "0"
        )
        # Stream path doesn't compute question_supertype upfront — derive
        # it from the shared _qu now (cheap; same source as sync path).
        # NOTE: supertype_for(intent: str) -> str. Sync path wraps it in a
        # dict ({"supertype": ..., "confidence": ...}) before passing
        # downstream — mirror that shape exactly.
        # Phase 4.5: in narrative mode the upstream contract-install block
        # already derived this dict; reuse it to avoid double-derivation.
        if not (
            _NARRATIVE_MODE
            and isinstance(locals().get("_question_supertype"), dict)
        ):
            _question_supertype = {
                "supertype":     supertype_for(_qu_intent),
                "confidence":    float(_qu.get("confidence") or 0.0),
                "source":        _qu.get("source") or "ai",
                "source_intent": _qu_intent,
            }
        if (_supertype_validator_enabled
                and isinstance(_question_supertype, dict)):
            _sup_tag = _question_supertype.get("supertype") or "GENERAL_ANALYSIS"
            _violations = _validate_supertype_contract(
                final_text, _sup_tag, kundli=kundli
            )
            if _violations:
                _trace(req_id, "4z.SUPERTYPE_CONTRACT_VIOLATION(stream)", {
                    "supertype":             _sup_tag,
                    "violation_count":       len(_violations),
                    "violations":            _violations,
                    "first_attempt_preview": final_text[:240],
                })
                try:
                    _retry_text = _stream_retry_call([{
                        "role":    "system",
                        "content": _retry_feedback_for(_sup_tag, _violations),
                    }])
                    _retry_violations = _validate_supertype_contract(
                        _retry_text, _sup_tag, kundli=kundli
                    )
                    _trace(req_id, "4z.SUPERTYPE_CONTRACT_RETRY(stream)", {
                        "supertype":        _sup_tag,
                        "retry_violations": _retry_violations,
                        "retry_clean":      not _retry_violations,
                        "retry_preview":    _retry_text[:240],
                    })
                    # Same accept-if-better-than-first heuristic as sync path.
                    if len(_retry_violations) < len(_violations):
                        final_text = _scrub_brand_tone(_retry_text)
                        replaced_by_validator = True
                        _trace(req_id, "4z.SUPERTYPE_CONTRACT_ACCEPTED(stream)",
                               {"reason": "retry was closer to contract"})
                    else:
                        _trace(req_id, "4z.SUPERTYPE_CONTRACT_KEPT_FIRST(stream)",
                               {"reason": "retry not better than first"})
                except Exception as _retry_exc:
                    _trace(req_id, "4z.SUPERTYPE_CONTRACT_RETRY_FAIL(stream)",
                           {"error": str(_retry_exc)[:200]})
            else:
                _trace(req_id, "4z.SUPERTYPE_CONTRACT_CLEAN(stream)",
                       {"supertype": _sup_tag})
    except Exception as _val_exc:
        _trace(req_id, "4z.SUPERTYPE_CONTRACT_VALIDATOR_ERR(stream)",
               {"error": str(_val_exc)[:200]})

    # ── POST_LOGIC_CHECK (truth validator) ───────────────────────────────
    # Strict-terminal: ANY non-zero residual violation after one retry → 
    # hard refusal. Mirrors sync path Architect-required Phase-3 v2 contract.
    try:
        _post_logic_enabled = (
            os.environ.get("POST_LOGIC_CHECK", "1") != "0"
        )
        if _post_logic_enabled and isinstance(kundli, dict):
            _truth = _build_truth_facts(kundli)
            _truth_violations = _post_logic_check(final_text, _truth)
            if _truth_violations:
                _trace(req_id, "2v.POST_LOGIC_CHECK_VIOLATION(stream)", {
                    "violation_count": len(_truth_violations),
                    "violations":      _truth_violations,
                    "truth_md":        (_truth.get("current_md") or {}).get("planet"),
                })
                try:
                    _pl_retry_text = _stream_retry_call([{
                        "role":    "system",
                        "content": _post_logic_correction_msg(
                            _truth_violations, _truth),
                    }])
                    _pl_retry_violations = _post_logic_check(
                        _pl_retry_text, _truth
                    )
                    _trace(req_id, "2v.POST_LOGIC_CHECK_RETRY(stream)", {
                        "retry_violations": _pl_retry_violations,
                        "retry_clean":      not _pl_retry_violations,
                        "retry_preview":    _pl_retry_text[:240],
                    })
                    if not _pl_retry_violations:
                        final_text = _scrub_brand_tone(_pl_retry_text)
                        replaced_by_validator = True
                        _trace(req_id, "2v.POST_LOGIC_CHECK_ACCEPTED(stream)",
                               {"reason":              "retry clean — facts corrected",
                                "correction_applied": True})
                    else:
                        # Strict-terminal refusal.
                        final_text = _POST_LOGIC_REFUSAL_TEXT
                        replaced_by_validator = True
                        _trace(req_id, "2v.POST_LOGIC_CHECK_REFUSAL(stream)", {
                            "reason":                 "retry left residual violations",
                            "residual_violation_count": len(_pl_retry_violations),
                            "first_violations":       _truth_violations,
                            "retry_violations":       _pl_retry_violations,
                            "reduced_count":          len(_truth_violations)
                                                      - len(_pl_retry_violations),
                            "served_text":            "_POST_LOGIC_REFUSAL_TEXT",
                        })
                except Exception as _pl_retry_exc:
                    # Retry-error MUST also refuse — never serve first
                    # violating text (architect-required parity).
                    final_text = _POST_LOGIC_REFUSAL_TEXT
                    replaced_by_validator = True
                    _trace(req_id, "2v.POST_LOGIC_CHECK_RETRY_ERR(stream)", {
                        "error":            str(_pl_retry_exc)[:200],
                        "first_violations": _truth_violations,
                        "served_text":      "_POST_LOGIC_REFUSAL_TEXT",
                        "reason":           "retry call errored — refusing rather "
                                            "than serving first violating text",
                    })
            else:
                _trace(req_id, "2v.POST_LOGIC_CHECK_CLEAN(stream)", {
                    "truth_md": (_truth.get("current_md") or {}).get("planet"),
                    "truth_ad": (_truth.get("current_ad") or {}).get("planet"),
                })
    except Exception as _pl_exc:
        _trace(req_id, "2v.POST_LOGIC_CHECK_ERR(stream)",
               {"error": str(_pl_exc)[:200]})

    has_dasha  = isinstance(kundli, dict) and bool(kundli.get("currentDasha"))
    has_coords = isinstance(birth, dict) and birth.get("lat") is not None and birth.get("lon") is not None
    if has_planets and has_dasha and has_coords:
        confidence = 0.95
    elif has_planets and has_dasha:
        confidence = 0.85
    elif has_planets:
        confidence = 0.75
    else:
        confidence = 0.55

    eff_lang = _resolve_response_lang(question, lang, preferred_language)
    follow_ups = _derive_follow_ups(topic, eff_lang)

    # Phase 4.9 T025 — wire the adaptive-depth truncator into the
    # streaming endpoint. Last session shipped T019 only into ai_ask
    # (oneshot path), so /api/ask/stream — which the mobile client
    # uses for typewriter UX — was bypassing all output discipline.
    # Same idempotency guards as oneshot: skip if narrative mode is
    # off, refusal text, or empty.
    #
    # ARCHITECT-FIX (Phase 4.9 review): truncator MUST run BEFORE the
    # engine-warn-footer block, otherwise the truncator's char-cap can
    # clip the appended footer mid-string. Order: truncate → footer.
    # Phase 5.0 Final Strip: same gate as sync path. Stream truncator is a
    # tier+format controller; banned in the minimal-prompt mode. Sync/stream
    # parity preserved (both gate on the same flag).
    try:
        if (_NARRATIVE_MODE
                and not _phase50_active_stream
                and isinstance(final_text, str)
                and final_text.strip()
                and final_text.strip() != _ENGINE_HONESTY_REFUSAL_TEXT.strip()
                and final_text.strip() != _POST_LOGIC_REFUSAL_TEXT.strip()):
            _stream_tier = _question_depth_tier(question or "")
            _trimmed_s = _phase48_narrative_truncate(
                final_text, question or "", tier=_stream_tier,
            )
            if _trimmed_s != final_text:
                _is_timing_q_s = _phase48_is_timing_question(question or "")
                print(f"[ai_ask_stream][phase49-trim] NARRATIVE_MODE "
                      f"truncate: {len(final_text)}c → {len(_trimmed_s)}c "
                      f"(tier={_stream_tier}, timing_q={_is_timing_q_s})")
                final_text = _trimmed_s
        elif _phase50_active_stream and _NARRATIVE_MODE:
            _trace(req_id, "phase48.TRUNCATOR_SKIPPED(stream)", {
                "reason": "phase50 minimal-prompt path — format/tier validators disabled",
                "raw_chars": len(final_text) if isinstance(final_text, str) else 0,
            })
    except Exception as _trim_exc_s:  # noqa: BLE001
        print(f"[ai_ask_stream] Phase 4.9 T025 stream truncator "
              f"failed: {_trim_exc_s}")

    # Phase 4.2 — stream-path engine warning footer parity. Refusal cannot
    # cleanly abort a stream mid-flight (deferred to Phase 4.4 backlog), but
    # the warn footer for OPTIONAL-phase failures CAN be appended after the
    # stream completes. Same idempotency guards as oneshot path.
    # NOTE: this runs AFTER the Phase 4.9 truncator above so the footer is
    # never clipped by the per-tier char cap.
    try:
        if (final_text
                and isinstance(final_text, str)
                and final_text.strip() != _ENGINE_HONESTY_REFUSAL_TEXT.strip()
                and final_text.strip() != _POST_LOGIC_REFUSAL_TEXT.strip()
                and _ENGINE_WARN_FOOTER_MARKER not in final_text):
            _hon_warn_s = _engine_honesty_check(
                (build_meta_stream or {}).get("engine_status") or {},
                qu=locals().get("_qu"),
            )
            if _hon_warn_s.get("warn"):
                final_text = final_text.rstrip() + _ENGINE_WARN_FOOTER_TEXT
                _trace(req_id, "4c.ENGINE_WARNING_INJECTED", {
                    "path": "stream",
                    "optional_failed": _hon_warn_s.get("optional_failed", []),
                    "reason": _hon_warn_s.get("reason"),
                })
    except Exception as _warn_exc_s:  # noqa: BLE001
        _trace(req_id, "4c.ENGINE_WARNING_ERR",
               f"stream:{str(_warn_exc_s)[:180]}")

    _trace(req_id, "5.FINAL_OUTPUT(stream)", final_text)
    _trace(req_id, "6.FOLLOW_UPS(stream)", {
        "topic": topic, "lang": eff_lang, "items": follow_ups,
        "behavior": "follow-up chips are deterministic per (topic, lang); "
                    "the NEXT user turn is reclassified independently — "
                    "mode does NOT inherit from this turn",
    })
    yield {
        "kind":                  "final",
        "text":                  final_text,
        "topic":                 topic,
        "confidence":            confidence,
        "source":                "openai_stream",
        "follow_ups":            follow_ups,
        # Phase 4.4 — true when POST_LOGIC / supertype validator overrode the
        # streamed text (retry accepted OR refusal substituted). Mobile
        # already swaps streamed deltas with final.text on `done`, so this
        # flag is purely telemetry — clients can log substitutions but no
        # rendering change is required.
        "replaced_by_validator": replaced_by_validator,
    }


# ── Vastu Drishti Scan (vision) ──────────────────────────────────────────────

_VASTU_LANG_HINT = {
    "hn": "Hinglish (Hindi written in Roman script, mixed naturally with English words)",
    "hi": "Hindi (Devanagari script)",
    "en": "English",
    "ta": "Tamil", "te": "Telugu", "kn": "Kannada", "ml": "Malayalam",
    "mr": "Marathi", "gu": "Gujarati", "bn": "Bengali", "pa": "Punjabi",
    "or": "Odia", "as": "Assamese", "ur": "Urdu",
}


from vastu_rules import format_rules_for_prompt, heading_to_direction, DIRECTIONS


# JSON schema for strict structured output. OpenAI strict mode requires every
# property listed in `required` and `additionalProperties: false`.
_VASTU_JSON_SCHEMA: dict = {
    "name": "vastu_scan_result",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "scan_inconclusive", "inconclusive_reason",
            "room_detected", "compliance_score", "energy_status",
            "direction_basis", "camera_facing_direction",
            "observations", "dosh", "remedies",
            "energy_forecast", "confidence",
        ],
        "properties": {
            "scan_inconclusive":      {"type": "boolean"},
            "inconclusive_reason":    {"type": "string"},
            "room_detected":          {"type": "string"},
            "compliance_score":       {"type": "integer", "minimum": 0, "maximum": 100},
            "energy_status":          {"type": "string", "enum": ["Excellent", "Optimal", "Mild Disturbance", "Moderate Dosh", "Significant Dosh"]},
            "direction_basis":        {"type": "string", "enum": ["magnetometer", "visual_inference", "assumed"]},
            "camera_facing_direction":{"type": "string"},
            "observations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["text", "direction", "severity", "classical_rule_ref"],
                    "properties": {
                        "text":               {"type": "string"},
                        "direction":          {"type": "string"},
                        "severity":           {"type": "string", "enum": ["positive", "neutral", "warning", "critical"]},
                        "classical_rule_ref": {"type": "string"},
                    },
                },
            },
            "dosh": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "description", "classical_source", "severity"],
                    "properties": {
                        "name":             {"type": "string"},
                        "description":      {"type": "string"},
                        "classical_source": {"type": "string"},
                        "severity":         {"type": "string", "enum": ["minor", "moderate", "major"]},
                    },
                },
            },
            "remedies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["action", "priority", "classical_source"],
                    "properties": {
                        "action":           {"type": "string"},
                        "priority":         {"type": "string", "enum": ["high", "medium", "low"]},
                        "classical_source": {"type": "string"},
                    },
                },
            },
            "energy_forecast": {"type": "string"},
            "confidence":      {"type": "integer", "minimum": 0, "maximum": 100},
        },
    },
}


def _vastu_messages(
    image_data_url: str,
    room_type: str,
    lang: str,
    heading_deg: float | None,
) -> list[dict]:
    lang_name = _VASTU_LANG_HINT.get(lang, "English")
    room_label = (room_type or "room").strip().lower()

    rules_block = format_rules_for_prompt(room_label)

    # Direction context — single biggest accuracy lever.
    if heading_deg is not None:
        cam_dir_code = heading_to_direction(heading_deg)
        cam_dir_full = DIRECTIONS.get(cam_dir_code, {}).get("name", cam_dir_code)
        direction_block = (
            f"=== REAL DEVICE DIRECTION (from device magnetometer) ===\n"
            f"  Camera was facing: {heading_deg:.1f}° (compass) → {cam_dir_code} ({cam_dir_full})\n"
            f"  This means: the wall in front of the camera is on the {cam_dir_full} side of the room.\n"
            f"  Use this as ABSOLUTE GROUND TRUTH for all directional inferences in this scan.\n"
            f"  direction_basis MUST be set to \"magnetometer\".\n"
        )
        basis_hint = '"magnetometer"'
    else:
        direction_block = (
            f"=== DEVICE DIRECTION ===\n"
            f"  Magnetometer reading was NOT provided.\n"
            f"  You may infer direction from visible cues (window light, shadow angle, sun position).\n"
            f"  Set direction_basis to EXACTLY one of:\n"
            f"    - \"visual_inference\"  if you have at least one reliable visible cue.\n"
            f"    - \"assumed\"           if no reliable cue exists (then state assumption clearly).\n"
        )
        basis_hint = '"visual_inference" OR "assumed" (pick exactly one)'

    system = f"""You are the COSMIC VASTU DRISHTI ENGINE v3.0 — an advanced spatial-energy analysis system that combines classical Vastu Shastra (Brihat Samhita, Mayamatam, Manasara, Samarangana Sutradhara) with real device sensor data and computer vision to produce highly accurate Vastu compliance reports.

You are NOT a generic chatbot or assistant. You are a precision scanning system that:
  • Reads photographs of rooms with expert-level visual analysis
  • Cross-references everything observed against an injected classical Vastu rule database
  • Cites the exact classical text or rule for every observation, dosh, and remedy
  • Reports its own confidence level honestly
  • Never invents observations not visible in the photo
  • Never invents classical citations — only uses sources from the injected rule database

ABSOLUTE OUTPUT RULES:

1. You MUST return a single JSON object matching the strict schema. No prose outside JSON.
2. NEVER mention "AI", "ChatGPT", "GPT", "OpenAI", "language model" anywhere in the JSON values. You are the "Cosmic Vastu Drishti Engine".
3. All free-text fields ("text", "description", "action", "energy_forecast", "inconclusive_reason") must be written in: {lang_name}. Field NAMES stay English. Enum values stay English. Classical source citations stay in their original form (e.g. "Brihat Samhita 53.42").
4. EVERY observation, dosh, and remedy MUST cite a classical_rule_ref or classical_source from the injected rule database below. Do NOT invent sources. If you cannot map an observation to a rule, omit it.
5. compliance_score (0-100): Calculate by starting at 100, deducting 12 for each major dosh, 6 for each moderate, 3 for each minor. Floor at 30 unless the room is uninhabitable. (Backend will recompute deterministically using this same formula — keep your math consistent so narrative and number stay aligned.)
6. confidence (0-100): Honestly report your confidence. Lower it sharply if image is dim, blurry, partial, or if direction_basis is "assumed".
7. If image is unclear, too dark, or not a room interior: set scan_inconclusive=true, fill inconclusive_reason in {lang_name}, and return empty arrays for observations/dosh/remedies. Do NOT fabricate analysis.
8. direction_basis MUST be: "{basis_hint}" (based on whether magnetometer data was provided). camera_facing_direction is the human-readable name (e.g. "North-East").
9. observations: 3-6 items. SPECIFIC things visible in the photo (bed position, mirror placement, window direction, clutter, color, etc.) tagged with direction and severity. classical_rule_ref must reference rule IDs like "G3" or "R2" from the injected rule database, OR a direct citation like "Brihat Samhita 53.42".
10. dosh: 0-4 items. Real Vastu doshas detected, each with severity grading.
11. remedies: 2-5 items. Practical actions the user can do this week. Cite the classical source for the remedy.
12. energy_forecast: 1-2 sentences in {lang_name} predicting the energy shift after applying remedies. Frame as energy alignment, not medical/legal/financial guarantee.

{direction_block}

=== INJECTED CLASSICAL VASTU RULE DATABASE ===
You MUST reason ONLY from these rules. Do not invent additional rules or citations.

{rules_block}

=== END OF RULES ===

Now perform the scan and return the strict JSON object."""

    user_content = [
        {
            "type": "text",
            "text": (
                f"Room type input (user-declared): {room_label}\n"
                f"Heading data: "
                + (f"{heading_deg:.1f}° (real magnetometer reading)" if heading_deg is not None else "not provided")
                + "\n\nInitiate full Cosmic Vastu Drishti scan on the attached image. "
                "Return the strict JSON object per schema."
            ),
        },
        {
            "type": "image_url",
            "image_url": {"url": image_data_url, "detail": "high"},
        },
    ]

    return [
        {"role": "system", "content": system},
        {"role": "user",   "content": user_content},
    ]


# ── Deep Scan (Phase 2) — multi-photo 4-wall guided capture ───────────────────
# Schema extends single-photo schema with per-wall analyses + spatial map.
_VASTU_DEEP_JSON_SCHEMA: dict = {
    "name": "vastu_deep_scan_result",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "scan_inconclusive", "inconclusive_reason",
            "room_detected", "compliance_score", "energy_status",
            "wall_analyses", "spatial_map",
            "observations", "dosh", "remedies",
            "energy_forecast", "confidence",
            "photo_count_used",
        ],
        "properties": {
            "scan_inconclusive":   {"type": "boolean"},
            "inconclusive_reason": {"type": "string"},
            "room_detected":       {"type": "string"},
            "compliance_score":    {"type": "integer", "minimum": 0, "maximum": 100},
            "energy_status":       {"type": "string", "enum": ["Excellent", "Optimal", "Mild Disturbance", "Moderate Dosh", "Significant Dosh"]},
            "photo_count_used":    {"type": "integer", "minimum": 0, "maximum": 8},
            "wall_analyses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["wall_direction", "wall_heading_deg", "elements_detected", "wall_status", "wall_compliance", "notes"],
                    "properties": {
                        "wall_direction":   {"type": "string"},
                        "wall_heading_deg": {"type": "number"},
                        "elements_detected":{"type": "array", "items": {"type": "string"}},
                        "wall_status":      {"type": "string", "enum": ["auspicious", "neutral", "concern", "dosh"]},
                        "wall_compliance":  {"type": "integer", "minimum": 0, "maximum": 100},
                        "notes":            {"type": "string"},
                    },
                },
            },
            "spatial_map": {
                "type": "object",
                "additionalProperties": False,
                "required": ["bed_or_seating", "main_door", "brahmasthan", "ne_corner", "sw_corner", "se_corner", "nw_corner"],
                "properties": {
                    "bed_or_seating": {"type": "string"},
                    "main_door":      {"type": "string"},
                    "brahmasthan":    {"type": "string"},
                    "ne_corner":      {"type": "string"},
                    "sw_corner":      {"type": "string"},
                    "se_corner":      {"type": "string"},
                    "nw_corner":      {"type": "string"},
                },
            },
            "observations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["text", "direction", "severity", "classical_rule_ref"],
                    "properties": {
                        "text":               {"type": "string"},
                        "direction":          {"type": "string"},
                        "severity":           {"type": "string", "enum": ["positive", "neutral", "warning", "critical"]},
                        "classical_rule_ref": {"type": "string"},
                    },
                },
            },
            "dosh": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "description", "classical_source", "severity"],
                    "properties": {
                        "name":             {"type": "string"},
                        "description":      {"type": "string"},
                        "classical_source": {"type": "string"},
                        "severity":         {"type": "string", "enum": ["minor", "moderate", "major"]},
                    },
                },
            },
            "remedies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["action", "priority", "classical_source"],
                    "properties": {
                        "action":           {"type": "string"},
                        "priority":         {"type": "string", "enum": ["high", "medium", "low"]},
                        "classical_source": {"type": "string"},
                    },
                },
            },
            "energy_forecast": {"type": "string"},
            "confidence":      {"type": "integer", "minimum": 0, "maximum": 100},
        },
    },
}


def _vastu_deep_messages(
    photos: list[dict],
    room_type: str,
    lang: str,
    floor_plan_url: str | None,
) -> list[dict]:
    """
    photos: list of {"image_data_url": str, "heading_deg": float, "label": str}
            each pre-validated.
    floor_plan_url: optional top-down floor plan image data URL.
    """
    lang_name = _VASTU_LANG_HINT.get(lang, "English")
    room_label = (room_type or "room").strip().lower()
    rules_block = format_rules_for_prompt(room_label)

    photo_descriptors: list[str] = []
    for i, p in enumerate(photos, 1):
        h    = p["heading_deg"]
        code = heading_to_direction(h)
        full = DIRECTIONS.get(code, {}).get("name", code)
        photo_descriptors.append(
            f"  PHOTO {i}: facing {full} ({code}) at {h:.1f}° compass — captures the {full} wall of the room."
        )

    has_floor = floor_plan_url is not None
    n = len(photos)

    system = f"""You are the COSMIC VASTU DRISHTI ENGINE v3.0 — DEEP SCAN MODE.

This is a MULTI-PHOTO spatial-energy analysis. You will receive {n} interior photographs of the same room, each captured at a specific compass heading (the camera was facing that direction at capture time). {('Plus ONE top-down floor plan image.' if has_floor else 'No floor plan provided.')}

Your job: build a complete spatial map of the room by combining all photos, then apply classical Vastu Shastra to every wall, every corner, and every detected element.

ABSOLUTE OUTPUT RULES:

1. Return a single JSON object matching the strict schema. No prose outside JSON.
2. NEVER mention "AI", "ChatGPT", "GPT", "OpenAI", "language model" anywhere.
3. All free-text fields written in: {lang_name}. Field names, enum values, and classical citations stay in their original form.
4. EVERY observation, dosh, and remedy MUST cite a rule from the injected database. Do not invent sources.
5. compliance_score: backend will recompute deterministically from dosh severities (12/6/3 deduction). Keep your score consistent with this formula.
6. confidence (0-100): self-report honestly. Boost if all 4 walls captured with magnetometer headings; lower if photos are dim/partial.
7. wall_analyses: produce EXACTLY {n} entries — one per photo, in the same order. wall_heading_deg must match the heading provided for that photo. wall_compliance is per-wall 0-100. wall_status enum must be one of: auspicious / neutral / concern / dosh.
   IMPORTANT — heading interpretation: provided headings are RAW DEVICE MAGNETIC compass readings (no declination correction, no building-axis offset). Real buildings often sit a few degrees off true magnetic north. Treat each heading as the dominant cardinal direction (snap to nearest of N/E/S/W when within ~25°), and use visible architectural cues (window placement, sun-light direction, door positions) to corroborate. If the user's heading clearly contradicts the visible scene, mention this in the wall's notes but proceed with the dominant cardinal guess.
8. spatial_map: synthesize across ALL photos. For each field, give a one-line factual statement (e.g. bed_or_seating: "Bed positioned along South wall, head pointing South — auspicious per Brihat Samhita 53.45"). If you cannot determine a field with confidence, say "not clearly visible in provided photos".
9. observations (3-8 items): the most important global observations across the whole room.
10. dosh (0-5): real Vastu doshas with severity grading.
11. remedies (3-7): practical actions — be specific to what was actually observed.
12. energy_forecast: 1-2 sentences in {lang_name}, framed as energy alignment (no medical/legal/financial guarantees).
13. photo_count_used: must equal {n}.
14. If photos are too unclear to analyze: scan_inconclusive=true, fill inconclusive_reason in {lang_name}, return empty arrays for wall_analyses/observations/dosh/remedies and an empty-string spatial_map fields.

=== PHOTO INVENTORY (in order they will appear) ===
{chr(10).join(photo_descriptors)}
{('  PHOTO ' + str(n+1) + ': top-down FLOOR PLAN of the room.' if has_floor else '')}

=== INJECTED CLASSICAL VASTU RULE DATABASE ===
{rules_block}

=== END OF RULES ===

Now perform the deep scan and return the strict JSON object."""

    # User message: text + interleaved photos
    user_content: list[dict] = [
        {
            "type": "text",
            "text": (
                f"Room type (user-declared): {room_label}\n"
                f"Photos: {n} directional + {'1 floor plan' if has_floor else 'no floor plan'}\n"
                f"All headings are REAL device magnetometer readings.\n\n"
                f"Photos follow in order:"
            ),
        },
    ]
    for i, p in enumerate(photos, 1):
        h    = p["heading_deg"]
        code = heading_to_direction(h)
        full = DIRECTIONS.get(code, {}).get("name", code)
        user_content.append({
            "type": "text",
            "text": f"--- PHOTO {i}/{n} — facing {full} wall ({code}, heading {h:.1f}°) ---",
        })
        user_content.append({
            "type": "image_url",
            "image_url": {"url": p["image_data_url"], "detail": "high"},
        })
    if floor_plan_url:
        user_content.append({"type": "text", "text": f"--- PHOTO {n+1}/{n+1} — TOP-DOWN FLOOR PLAN (no heading) ---"})
        user_content.append({"type": "image_url", "image_url": {"url": floor_plan_url, "detail": "high"}})

    user_content.append({
        "type": "text",
        "text": "Now perform the full DEEP SCAN. Build the spatial map by cross-referencing all photos. Return the strict JSON object.",
    })

    return [
        {"role": "system", "content": system},
        {"role": "user",   "content": user_content},
    ]


def vastu_deep_scan(
    photos: list[dict],
    room_type: str = "room",
    lang: str = "en",
    floor_plan_url: str | None = None,
) -> dict:
    """
    Multi-photo Vastu deep scan.

    Args:
      photos: list of dicts, each with keys:
        - image_data_url: str (data URL or https URL, required)
        - heading_deg:    float 0-360 (required, real magnetometer reading)
        - label:          str (optional human-readable label, e.g. "north_wall")
      room_type:      e.g. "bedroom"
      lang:           language code
      floor_plan_url: optional top-down floor plan image

    Returns parsed dict matching _VASTU_DEEP_JSON_SCHEMA.
    Raises RuntimeError on config / OpenAI failure.
    """
    client = _get_client()
    if client is None:
        raise RuntimeError(_client_err or "OpenAI client not configured")
    if not photos:
        raise RuntimeError("at least one photo is required")
    if len(photos) > 6:
        raise RuntimeError("maximum 6 directional photos supported")

    # Validate each photo entry
    norm: list[dict] = []
    for i, p in enumerate(photos):
        url = (p.get("image_data_url") or p.get("image") or "").strip()
        if not url:
            raise RuntimeError(f"photo {i+1}: image is required")
        h = p.get("heading_deg")
        if h is None:
            raise RuntimeError(f"photo {i+1}: heading_deg is required (real magnetometer reading)")
        try:
            h = float(h) % 360.0
        except (TypeError, ValueError):
            raise RuntimeError(f"photo {i+1}: heading_deg must be a number")
        norm.append({"image_data_url": url, "heading_deg": h, "label": p.get("label", f"photo_{i+1}")})

    model = os.environ.get("OPENAI_VISION_MODEL", "gpt-4o")
    messages = _vastu_deep_messages(norm, room_type, lang, floor_plan_url)

    try:
        resp = client.chat.completions.create(
            model           = model,
            messages        = messages,
            temperature     = 0.4,
            max_tokens      = 3000,
            response_format = {"type": "json_schema", "json_schema": _VASTU_DEEP_JSON_SCHEMA},
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI deep-scan request failed: {exc}") from exc

    raw = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    if not raw:
        raise RuntimeError("OpenAI returned empty deep-scan response")

    try:
        parsed = json.loads(raw)
    except Exception as exc:
        raise RuntimeError(f"OpenAI returned non-JSON deep-scan response: {exc}") from exc

    parsed = _post_process_score(parsed)
    parsed["room"]   = room_type
    parsed["source"] = "openai-deep"
    parsed["model"]  = model
    parsed["photos_input_count"] = len(norm)
    parsed["floor_plan_provided"] = floor_plan_url is not None

    return parsed


def _post_process_score(parsed: dict) -> dict:
    """
    ALWAYS recompute compliance_score deterministically from dosh severities so
    the score is fully auditable and reproducible across identical scans.
    No dosh => clean room => 100.
    Original LLM-suggested score is preserved in `compliance_score_llm` for
    transparency and tuning.
    """
    dosh = parsed.get("dosh") or []
    deductions = 0
    for d in dosh:
        sev = (d.get("severity") or "").lower()
        if   sev == "major":    deductions += 12
        elif sev == "moderate": deductions += 6
        elif sev == "minor":    deductions += 3

    computed = max(30, 100 - deductions) if dosh else 100
    parsed["compliance_score_llm"]    = parsed.get("compliance_score")
    parsed["compliance_score"]        = computed
    parsed["compliance_score_method"] = (
        "rule-based: 100 - 12*major - 6*moderate - 3*minor (floor 30); 100 if zero dosh"
    )
    return parsed


def vastu_scan(
    image_data_url: str,
    room_type: str = "room",
    lang: str = "en",
    heading_deg: float | None = None,
) -> dict:
    """
    Analyze a room photograph for Vastu compliance with injected classical rules.

    Args:
      image_data_url:  data URL ("data:image/jpeg;base64,...") OR https URL
      room_type:       e.g. "bedroom", "kitchen", "pooja room", "living room"
      lang:            language code ("hn", "hi", "en", etc.)
      heading_deg:     compass heading in degrees (0-360) the camera was facing
                       at scan time — REAL device sensor data. Optional but
                       dramatically improves accuracy when provided.

    Returns parsed dict with strict JSON schema fields. See _VASTU_JSON_SCHEMA.
    Raises RuntimeError on OpenAI / config failure.
    """
    client = _get_client()
    if client is None:
        raise RuntimeError(_client_err or "OpenAI client not configured")
    if not image_data_url:
        raise RuntimeError("image is required")

    # Phase 1 upgrade: full GPT-4o (much better vision than mini).
    # Override via env var if needed.
    model = os.environ.get("OPENAI_VISION_MODEL", "gpt-4o")
    messages = _vastu_messages(image_data_url, room_type, lang, heading_deg)

    try:
        resp = client.chat.completions.create(
            model           = model,
            messages        = messages,
            temperature     = 0.4,    # lower = more deterministic, less hallucination
            max_tokens      = 1800,
            response_format = {"type": "json_schema", "json_schema": _VASTU_JSON_SCHEMA},
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI vision request failed: {exc}") from exc

    raw = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    if not raw:
        raise RuntimeError("OpenAI returned empty Vastu response")

    try:
        parsed = json.loads(raw)
    except Exception as exc:
        raise RuntimeError(f"OpenAI returned non-JSON Vastu response: {exc}") from exc

    parsed = _post_process_score(parsed)
    parsed["room"]   = room_type
    parsed["source"] = "openai"
    parsed["model"]  = model
    if heading_deg is not None:
        parsed["heading_deg_input"] = heading_deg

    return parsed


# ─────────────────────────────────────────────────────────────────────────────
# COSMIC VISION ENGINE — floor-plan extraction + room visual analysis
# (Phase 6: powers AstroVastu PRO + Business Vastu paid tiers)
# All user-facing text is branded as "Cosmic Intelligence Engine".
# Engine remains source of truth for verdicts; vision provides INPUT extraction
# and environmental observations only.
# ─────────────────────────────────────────────────────────────────────────────

_FLOOR_PLAN_LAYOUT_SCHEMA = {
    "name": "FloorPlanLayout",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "rooms", "structural_notes", "plot_shape",
            "main_entrance_direction", "confidence", "scan_inconclusive",
            "inconclusive_reason",
        ],
        "properties": {
            "rooms": {
                "type": "array",
                "minItems": 0,
                "maxItems": 30,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["room_type", "direction", "position_grid", "notes"],
                    "properties": {
                        "room_type": {
                            "type": "string",
                            "description": "canonical lowercase: master_bedroom, bedroom, kitchen, pooja_room, living_room, dining, bathroom, toilet, study, store, balcony, staircase, entrance, office, cabin, reception, conference, workstation, store_room, billing, cash_counter, factory_floor, warehouse, godown, machine_room, raw_material, finished_goods, etc."
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["N","NE","E","SE","S","SW","W","NW","center"]
                        },
                        "position_grid": {
                            "type": "string",
                            "description": "approx grid cell, e.g. 'top-left', 'center', 'bottom-right'"
                        },
                        "notes": {"type": "string"}
                    }
                }
            },
            "structural_notes": {
                "type": "array",
                "maxItems": 10,
                "items": {"type": "string"}
            },
            "plot_shape": {
                "type": "string",
                "description": "rectangular / square / irregular / L-shaped / other"
            },
            "main_entrance_direction": {
                "type": "string",
                "enum": ["N","NE","E","SE","S","SW","W","NW","unknown"]
            },
            "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
            "scan_inconclusive": {"type": "boolean"},
            "inconclusive_reason": {"type": "string"}
        }
    }
}


_ROOM_VISUAL_SCHEMA = {
    "name": "RoomVisualFindings",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["room_identity_match", "detected_room_type",
                     "identity_features_seen",
                     "visual_findings", "score_delta", "confidence",
                     "scan_inconclusive", "inconclusive_reason"],
        "properties": {
            "room_identity_match": {
                "type": "boolean",
                "description": "True ONLY if the photo clearly shows the user-declared room_type. "
                               "Look for the room's defining features (kitchen=stove/sink/counter, "
                               "bathroom=WC/shower/tiles, pooja=idols/diya, bedroom=bed, "
                               "office=desk/chairs, factory=machinery, shop=counter/shelves)."
            },
            "detected_room_type": {
                "type": "string",
                "description": "Your honest classification of what room this photo actually shows "
                               "(kitchen/bathroom/pooja/bedroom/livingroom/office/factory/shop/"
                               "outdoor/unclear). Use 'unclear' if you cannot tell."
            },
            "identity_features_seen": {
                "type": "array",
                "minItems": 0, "maxItems": 6,
                "items": {"type": "string"},
                "description": "Concrete features you can see (e.g. 'gas stove', 'sink with tap', "
                               "'toilet seat'). Empty array if photo too unclear."
            },
            "visual_findings": {
                "type": "array",
                "minItems": 0,
                "maxItems": 8,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["text", "severity", "category"],
                    "properties": {
                        "text": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["positive", "neutral", "minor", "moderate", "major"]
                        },
                        "category": {
                            "type": "string",
                            "enum": [
                                "clutter", "mirror", "beam", "color",
                                "electronics", "idol", "furniture", "lighting",
                                "plant", "water", "fire", "storage", "general"
                            ]
                        }
                    }
                }
            },
            "score_delta": {
                "type": "integer", "minimum": -15, "maximum": 10,
                "description": "net adjustment to room compliance score from visual environment"
            },
            "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
            "scan_inconclusive": {"type": "boolean"},
            "inconclusive_reason": {"type": "string"}
        }
    }
}


def extract_floor_plan_layout(
    image_data_url: str,
    business_type: str | None = None,
    lang: str = "en",
) -> dict:
    """
    Extract structured room layout from a top-down floor plan image (PNG data URL).

    Returns dict per _FLOOR_PLAN_LAYOUT_SCHEMA. Raises RuntimeError on config /
    OpenAI failure. Branded as Cosmic Intelligence Engine — never mentions AI/GPT.
    """
    client = _get_client()
    if client is None:
        raise RuntimeError(_client_err or "Cosmic Intelligence Engine not configured")
    if not image_data_url or not isinstance(image_data_url, str):
        raise RuntimeError("floor plan image is required")

    model = os.environ.get("OPENAI_VISION_MODEL", "gpt-4o")
    lang_name = _LANG_NAME.get(lang, "English")
    btype = (business_type or "").strip().lower() or "residential"

    system = (
        "You are the COSMIC VISION ENGINE — Floor Plan Spatial Analyzer.\n\n"
        "Your job: examine ONE top-down floor plan image and extract every "
        "identifiable room, its cardinal direction, and structural notes "
        "relevant to Vastu Shastra.\n\n"
        "ABSOLUTE RULES:\n"
        "1. Output ONLY the strict JSON object — no prose.\n"
        "2. NEVER mention 'AI', 'GPT', 'OpenAI', 'language model'. You are "
        "the Cosmic Intelligence Engine.\n"
        f"3. The property type is: {btype}. Identify rooms appropriate to it.\n"
        "4. Direction = the cardinal/intercardinal zone where the room SITS "
        "within the plot, assuming North is at the TOP of the floor plan "
        "unless an explicit compass arrow shows otherwise. Use 9-cell logic: "
        "NW | N | NE / W | center | E / SW | S | SE.\n"
        "5. Use canonical lowercase room_type tokens (see schema description).\n"
        "6. structural_notes (0-10 lines): things like 'kitchen and toilet "
        "share a wall', 'staircase passes through center', 'plot is L-shaped'.\n"
        "7. confidence (0-100): be honest. If the plan is blurry, hand-drawn "
        "without labels, or you cannot determine room functions reliably, "
        "set scan_inconclusive=true with a reason.\n"
        f"8. structural_notes / inconclusive_reason text in: {lang_name}. "
        "Field names, enums, room_type tokens stay original.\n"
    )
    user_content = [
        {"type": "text", "text": (
            f"Property type: {btype}. Identify all rooms with their direction "
            "(9-cell zone) within the plot. Return strict JSON."
        )},
        {"type": "image_url", "image_url": {"url": image_data_url, "detail": "high"}},
    ]

    try:
        resp = client.chat.completions.create(
            model           = model,
            messages        = [
                {"role": "system", "content": system},
                {"role": "user",   "content": user_content},
            ],
            temperature     = 0.2,
            max_tokens      = 2000,
            response_format = {"type": "json_schema", "json_schema": _FLOOR_PLAN_LAYOUT_SCHEMA},
        )
    except Exception as exc:
        raise RuntimeError(f"Cosmic Intelligence Engine request failed: {exc}") from exc

    raw = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    if not raw:
        raise RuntimeError("Cosmic Intelligence Engine returned empty response")
    try:
        parsed = json.loads(raw)
    except Exception as exc:
        raise RuntimeError(f"Cosmic Intelligence Engine returned non-JSON: {exc}") from exc

    parsed["source"] = "cosmic-vision-floor-plan"
    parsed["model"]  = model
    return parsed


def analyze_room_visuals(
    image_data_url: str,
    room_type: str,
    heading_deg: float | None = None,
    lang: str = "en",
) -> dict:
    """
    Analyze ONE room photograph for visual environmental Vastu observations
    (clutter, mirror placement, beam, electronics, idol orientation, color, etc.).

    Returns dict per _ROOM_VISUAL_SCHEMA. score_delta is BOUNDED to [-15, +10].
    Branded — never mentions AI.
    """
    client = _get_client()
    if client is None:
        raise RuntimeError(_client_err or "Cosmic Intelligence Engine not configured")
    if not image_data_url:
        raise RuntimeError("room photo is required")

    model = os.environ.get("OPENAI_VISION_MODEL", "gpt-4o")
    lang_name = _LANG_NAME.get(lang, "English")
    rt = (room_type or "room").strip().lower()
    heading_str = f"{heading_deg:.1f}°" if isinstance(heading_deg, (int, float)) else "unknown"

    system = (
        "You are the COSMIC VISION ENGINE — Room Environment Analyzer.\n\n"
        "STEP 1 — ROOM IDENTITY VERIFICATION (CRITICAL & STRICT):\n"
        f"The user declared this photo is of a '{rt}'. BEFORE any analysis, "
        "you MUST verify the photo actually shows that type of room by looking "
        "for its defining features. Be STRICT — when in doubt, REJECT.\n"
        "  • kitchen → gas stove / chulha / chimney / sink / counter / utensils\n"
        "  • bathroom → WC / commode / shower / bathtub / wall tiles / tap\n"
        "  • pooja → idols / diya / agarbatti stand / mandir cabinet / bell\n"
        "  • bedroom → bed / mattress / pillows / wardrobe / dressing table\n"
        "  • hall / livingroom → sofa / coffee table / TV unit / large seating area\n"
        "  • office / cabin → desk / office chair / computer / files / cabin partition\n"
        "  • factory → machinery / conveyors / raw material storage / industrial floor\n"
        "  • shop → display shelves / counter / cash register / merchandise\n"
        "  • entrance → main door / threshold / shoe rack / nameplate\n\n"
        "DECISION RULES — be conservative:\n"
        "  • room_identity_match=TRUE only if you see at least 2 of the room's "
        f"defining features clearly, OR the overall scene is unambiguously a {rt}.\n"
        "  • Single ambiguous object (e.g. just a wall, just a tap) is NOT enough.\n"
        "  • If the photo is a different room → room_identity_match=FALSE, set "
        "detected_room_type to what you actually see (e.g. 'bedroom').\n"
        "  • If photo is too far / too close / too dark / blurry / cropped wrong "
        "to confirm the room → room_identity_match=FALSE, detected_room_type='unclear', "
        "and write inconclusive_reason in {lang_name} explaining EXACTLY what's wrong "
        "(e.g. 'photo bahut paas se li gayi hai, room ka context nahi dikh raha' OR "
        "'photo bahut door se li gayi hai, defining features pehchaane nahi ja sake' "
        "OR 'roshni kam hai, room features clear nahi').\n"
        "  • If photo is not a room interior at all (selfie, outdoor, food, screenshot) "
        "→ room_identity_match=FALSE, detected_room_type='outdoor' or 'unclear', "
        "with a clear inconclusive_reason.\n\n"
        "When room_identity_match=FALSE: return EMPTY visual_findings, score_delta=0, "
        "scan_inconclusive=true. Confidence MUST drop below 50.\n\n"
        "STEP 2 — VASTU ANALYSIS (only if room_identity_match=true):\n"
        "Surface VISUAL ENVIRONMENTAL observations relevant to Vastu Shastra (clutter, "
        "mirror placement, exposed beams, sharp colors, large electronics, "
        "idol orientation, water/fire elements, broken items, etc.).\n\n"
        "ABSOLUTE RULES:\n"
        "1. Output ONLY the strict JSON object — no prose.\n"
        "2. NEVER mention 'AI', 'GPT', 'OpenAI', 'language model'. You are "
        "the Cosmic Intelligence Engine.\n"
        "3. Do NOT make verdicts on the room layout/direction — that is handled "
        "by the classical engine. Focus on what is VISIBLE in the photo.\n"
        "4. visual_findings: 0-8 specific items (EMPTY if room_identity_match=false). severity = "
        "positive | neutral | minor | moderate | major.\n"
        "5. score_delta: small integer in [-15, +10] reflecting net "
        "environmental impact. Be conservative — classical rules dominate. "
        "MUST be 0 if room_identity_match=false.\n"
        "6. confidence (0-100): be honest. If photo is blurry / dark / not a "
        "room, set scan_inconclusive=true with a reason and empty findings.\n"
        f"7. text / inconclusive_reason in: {lang_name}. Enums stay original.\n"
        "8. Be specific — say 'mirror on south wall facing bed' not 'mirror present'.\n"
    )
    user_content = [
        {"type": "text", "text": (
            f"Room type (user-declared): {rt}\n"
            f"Camera heading at capture: {heading_str}\n"
            "Return strict JSON with visual environmental findings only."
        )},
        {"type": "image_url", "image_url": {"url": image_data_url, "detail": "high"}},
    ]

    try:
        resp = client.chat.completions.create(
            model           = model,
            messages        = [
                {"role": "system", "content": system},
                {"role": "user",   "content": user_content},
            ],
            temperature     = 0.3,
            max_tokens      = 1500,
            response_format = {"type": "json_schema", "json_schema": _ROOM_VISUAL_SCHEMA},
        )
    except Exception as exc:
        raise RuntimeError(f"Cosmic Intelligence Engine request failed: {exc}") from exc

    raw = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    if not raw:
        raise RuntimeError("Cosmic Intelligence Engine returned empty response")
    try:
        parsed = json.loads(raw)
    except Exception as exc:
        raise RuntimeError(f"Cosmic Intelligence Engine returned non-JSON: {exc}") from exc

    # Hard-clamp score_delta defensively
    sd = parsed.get("score_delta", 0)
    try:
        sd = int(sd)
    except Exception:
        sd = 0
    parsed["score_delta"] = max(-15, min(10, sd))

    parsed["source"]    = "cosmic-vision-room"
    parsed["model"]     = model
    parsed["room_type"] = rt
    if heading_deg is not None:
        parsed["heading_deg_input"] = float(heading_deg)
    return parsed


# ═════════════════════════════════════════════════════════════════════════════
# AI ASK V2 — multi-intent orchestrator (P2)
# ═════════════════════════════════════════════════════════════════════════════
# Wraps ai_ask() with an AI Ear front-end that can split a single user message
# into up to 3 focused sub-questions and run them in parallel. Returns either:
#
#   • Backward-compat single-shape (when AI Ear failed, only 1 intent, or
#     non-astro mode) — caller sees the existing ai_ask() response unchanged.
#
#   • Multi-card shape (when ≥2 intents detected):
#         {
#           "response_schema": "v2",
#           "cards": [ { intent_label, text, topic, confidence, source,
#                        follow_ups, ... }, ... ],
#           "trimmed_count": <int>,
#           "intent_extraction": {language, domain, ask_types, ...},
#           "text":  <legacy combined string for old clients>,
#           "topic": <primary domain>,
#           "follow_ups": [...],
#           "confidence": <avg>,
#           "source": "ai_v2_multi"
#         }
#
# Engines remain UNTOUCHED — each card runs the full deterministic chain on
# its own focused question. Concurrency: ThreadPoolExecutor with max 3 workers
# (matches max intents). OpenAI client is thread-safe.
#
# Per-card failure handling:
#   • WealthStructuredError per card → that card returns a typed failure shape;
#     other cards still render. Caller (Flask) decides 503 only if ALL cards
#     failed. (For P2 we surface per-card failure inline.)
#   • Generic Exception per card → that card carries error: "..." and source:
#     "card_failed"; siblings unaffected.

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional as _Optional


def _v2_should_split(intent_extraction) -> bool:
    """Decide whether to enter multi-card mode. Single-intent extractions
    fall through to the legacy ai_ask() path for full backward-compat."""
    if not intent_extraction or intent_extraction.source != "ai_ear":
        return False
    if not intent_extraction.intents or len(intent_extraction.intents) < 2:
        return False
    # Confidence floor — if AI Ear is uncertain, prefer single-engine path.
    if (intent_extraction.confidence or 0.0) < 0.55:
        return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# STRUCTURED WEALTH → V2 CARD (Phase 1: direct prescription-style mapping)
# ─────────────────────────────────────────────────────────────────────────────
# When ai_ask() runs the wealth structured-output path it attaches the
# validated JSON payload at result["structured"]. The legacy text field carries
# a pre-formatted bullet view for older clients.
#
# Without this helper, _v2_run_card hands raw_engine_text (the bullet view) to
# narrator_v2.compose_card_narrative which rewrites everything into a generic
# 50-80w "Dekho na… dheere clear hogi" paragraph — washing out every specific
# date, action, and threshold the engine + structured prompt worked to lock in.
#
# This helper builds the v2 card SHAPE (verdict_tag / narrative / remedy_line /
# advisor_line) deterministically from the structured payload — no second LLM
# call. The narrative stitches headline + timeline pivot + first what_to_do
# action so users get the asli-astrologer prescription voice the engine intends.
#
# Feature-flagged via STRUCTURED_NARRATOR_ENABLED (default "1"). Set to "0" to
# fall back to the legacy narrator_v2 wrap.

# Map structured-payload short tags → narrator_v2 canonical tag enum
# (mobile UI matches the long form).
_STRUCT_TAG_TO_V2 = {
    "🟢 GO":      "🟢 GREEN GO",
    "🟡 WAIT":    "🟡 WAIT",
    "🟠 SLOW":    "🟠 SLOW BURN",
    "🔴 CAUTION": "🔴 RED FLAG",
}


# Strip the trailing "(Planet–Planet)" / "(Planet-Planet)" annotation that
# the engine appends to dasha window labels. Brand voice forbids planet
# names in the narrative — the user-facing window should stay date-only.
# Example:
#   "Jul 2024 – Mar 2026 (Shukra–Budh)"  →  "Jul 2024 – Mar 2026"
_DASHA_PLANET_TAIL_RX = re.compile(
    r"\s*\([^)]*(?:Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|"
    r"Surya|Chandra|Mangal|Budh|Buddha|Guru|Brihaspati|Shukra|Shukr|"
    r"Shani|Sani)[^)]*\)\s*$",
    re.IGNORECASE,
)


def _strip_planet_annotation(window_str: str) -> str:
    """Remove the '(Planet–Planet)' suffix from a dasha-window label.
    Returns the bare date span. Safe on already-clean strings."""
    if not window_str:
        return ""
    return _DASHA_PLANET_TAIL_RX.sub("", window_str).strip()


def _stitch_structured_narrative(payload: dict) -> str:
    """Compose Hinglish prose from the structured payload fields.

    Pure deterministic — no LLM. Now (Phase 2) uses the EMPATHY SANDWICH
    pattern: empathy_open → engine facts (headline / timing / actions) →
    human_close. The middle stays fact-locked; the outer two lines carry
    the human voice tuned by the EMOTIONAL TREATMENT DIRECTIVE upstream.
    """
    if not isinstance(payload, dict):
        return ""

    empathy_open = (payload.get("empathy_open") or "").strip().rstrip(".")
    headline = (payload.get("headline") or "").strip().rstrip(".")
    tl       = payload.get("timeline") or {}
    # Strip planet-name dasha annotation so brand voice stays clean.
    cur      = _strip_planet_annotation((tl.get("current") or "").strip())
    nxt      = _strip_planet_annotation((tl.get("next")    or "").strip())
    do_arr    = payload.get("what_to_do")    or []
    avoid_arr = payload.get("what_to_avoid") or []
    will_arr  = payload.get("what_will_happen") or []
    human_close = (payload.get("human_close") or "").strip().rstrip(".")

    do_first    = (do_arr[0]    if do_arr    else "").strip().rstrip(".")
    avoid_first = (avoid_arr[0] if avoid_arr else "").strip().rstrip(".")
    will_first  = (will_arr[0]  if will_arr  else "").strip().rstrip(".")

    parts: list[str] = []

    # ── EMPATHY OPEN — first sentence anchors the human voice ──
    if empathy_open:
        parts.append(empathy_open + ".")

    # ── ENGINE FACTS (middle, fact-locked) ──
    # Lead — the engine's decision-oriented headline
    if headline:
        parts.append(headline + ".")

    # What is happening / will happen — adds the "asli astrologer feel"
    if will_first:
        parts.append(f"{will_first.capitalize()}.")

    # Timing pivot — specific date the engine locked
    if cur and nxt:
        parts.append(f"Abhi window {cur} ka chal raha hai — {nxt} ke baad shift hoga.")
    elif nxt:
        parts.append(f"{nxt} ke baad window better hota jaayega.")
    elif cur:
        parts.append(f"Abhi {cur} ka window active hai.")

    # Concrete next action — engine's top recommendation, verbatim
    if do_first:
        parts.append(f"Karo: {do_first}.")

    # Optional guardrail
    if avoid_first:
        parts.append(f"Avoid: {avoid_first}.")

    # ── HUMAN CLOSE — final sentence carries the reframe / agency ──
    if human_close:
        parts.append(human_close + ".")

    narrative = " ".join(parts).strip()
    # Schema floor is 80 chars; if too short (rare), fall back to headline
    # repeated with a soft closure
    if len(narrative) < 80 and headline:
        narrative = (
            f"{headline}. Window dheere shift hoga, disciplined approach se "
            f"raasta khulta jaayega."
        )
    return narrative


def _card_from_structured_wealth_payload(
    payload: dict,
    *,
    intent_label: str,
    intent_bucket: str,
    intent_summary: str,
    raw_topic: str,
    raw_confidence: float,
    raw_followups: list,
    legacy_text: str,
) -> dict:
    """Build a v2 card dict directly from the wealth structured payload.

    Bypasses narrator_v2 entirely — the structured payload is already
    fact-locked + brand-safety-validated upstream by _validate_wealth_payload.
    Output shape mirrors the existing ai_v2_narrator success-path return
    so the mobile client doesn't need any change.
    """
    v_obj = payload.get("verdict") or {}
    short_tag = (v_obj.get("tag") or "").strip()
    verdict_tag = _STRUCT_TAG_TO_V2.get(short_tag, "🟡 WAIT")

    narrative    = _stitch_structured_narrative(payload)
    remedy_line  = (payload.get("remedy") or "").strip()
    advisor_line = (payload.get("note")   or "").strip()

    # Build the same display text format the narrator path uses (tag +
    # narrative + remedy + advisor). Legacy text (the bullet view) is
    # preserved for older clients via a separate field.
    final_text = f"{verdict_tag}\n\n{narrative}"
    if remedy_line:
        final_text += f"\n\n🕉  Upay: {remedy_line}"
    if advisor_line:
        final_text += f"\n\nℹ  {advisor_line}"

    return {
        "intent_label":    intent_label,
        "intent_bucket":   intent_bucket,
        "intent_summary":  intent_summary,
        "verdict_tag":     verdict_tag,
        "narrative":       narrative,
        "remedy_line":     remedy_line,
        "advisor_line":    advisor_line,
        "text":            final_text,
        "topic":           raw_topic,
        "confidence":      raw_confidence,
        "source":          "ai_v2_wealth_structured",
        "follow_ups":      raw_followups,
        "structured":      payload,        # forward to client for rich UI
        "legacy_bullets":  legacy_text,    # bullet-style fallback view
    }


def _v2_run_card(intent_summary: str,
                 kundli: Any,
                 lang: str,
                 reply_idx: int,
                 birth: Any,
                 history: list | None,
                 preferred_language: _Optional[str],
                 intent_label: str,
                 intent_bucket: str,
                 intent_facts: dict,
                 emotional_tone: str,
                 narrator_lang: str,
                 intent_domain: str = "") -> dict:
    """Run ai_ask for ONE intent + (optionally) reshape into the
    conversational diagnostic card via narrator_v2 (P3).
    Catches per-card exceptions so siblings can still render."""
    raw_engine_text = ""
    raw_topic       = "general"
    raw_source      = "ai"
    raw_followups: list[str] = []
    raw_confidence  = 0.5

    try:
        result = ai_ask(
            intent_summary, kundli, lang, reply_idx,
            birth=birth, history=history,
            preferred_language=preferred_language,
        )
        if not isinstance(result, dict):
            result = {"text": str(result), "source": "ai"}
        raw_engine_text = (result.get("text") or "").strip()
        raw_topic       = result.get("topic") or "general"
        raw_source      = result.get("source") or "ai"
        raw_followups   = list(result.get("follow_ups") or [])
        raw_confidence  = float(result.get("confidence") or 0.5)
    except Exception as exc:
        err_type = type(exc).__name__
        return {
            "intent_label":   intent_label,
            "intent_bucket":  intent_bucket,
            "intent_summary": intent_summary,
            "text": (
                "Cosmic Intelligence ko is intent par abhi answer generate "
                "karne mein dikkat aa rahi hai. Kripya thodi der baad dobara "
                "try karein."
            ),
            "topic":      "general",
            "confidence": 0.0,
            "source":     "card_failed",
            "follow_ups": [],
            "error":      f"{err_type}: {str(exc)[:200]}",
        }

    # ── Deterministic-fail-safe BYPASS ─────────────────────────────────────
    # If the engine's deterministic safety net fired (no-chart fail-safe,
    # brand-safety block, off-topic refusal, etc.), the user MUST see that
    # exact text — never let the conversational narrator soften it.
    _DETERMINISTIC_SOURCES = {
        "no_chart_failsafe",
        "brand_safety",
        "brand_safety_block",
        "off_topic",
        "rules",
        "wealth_structured_unavailable",
    }
    if raw_source in _DETERMINISTIC_SOURCES:
        return {
            "intent_label":   intent_label,
            "intent_bucket":  intent_bucket,
            "intent_summary": intent_summary,
            "text":           raw_engine_text or "(empty)",
            "topic":          raw_topic,
            "confidence":     raw_confidence,
            "source":         raw_source,
            "follow_ups":     raw_followups,
        }

    # ── Phase 1: STRUCTURED WEALTH SHORT-CIRCUIT ───────────────────────────
    # When the wealth engine ran the JSON-schema strict path, the validated
    # payload is on result["structured"]. Render the v2 card directly from it
    # — bypassing narrator_v2 — so the user sees the engine's specific
    # headline + timeline.next date + concrete action verbatim, instead of a
    # generic 50-80w "Dekho na… dheere clear hogi" rewrite.
    #
    # GATE — must be ALL of:
    #   (a) feature flag on (STRUCTURED_NARRATOR_ENABLED != "0", default on)
    #   (b) result["structured"] is a non-empty dict
    #   (c) payload matches the WEALTH structured schema shape (so future
    #       engines emitting their own structured payloads — e.g. career or
    #       health — are NOT silently rendered as wealth cards). The shape
    #       check requires verdict.tag, timeline (current|next), what_to_do
    #       list, and the CA/SEBI advisor `note` (wealth-mandatory cite).
    _struct_payload = result.get("structured") if isinstance(result, dict) else None

    def _looks_like_wealth_payload(p: dict) -> bool:
        if not isinstance(p, dict):
            return False
        v = p.get("verdict")
        if not isinstance(v, dict) or not v.get("tag"):
            return False
        tl = p.get("timeline")
        if not isinstance(tl, dict) or not (tl.get("current") or tl.get("next")):
            return False
        wd = p.get("what_to_do")
        if not isinstance(wd, list):
            return False
        if not isinstance(p.get("note"), str):
            return False
        return True

    # Phase 4.5 NARRATIVE_MODE: bypass the structured wealth payload short-
    # circuit entirely. The structured renderer would emit a "Verdict tag /
    # Window / Karo / Avoid / 🕉 Upay / CA-SEBI cite" card which is exactly
    # the V→R→T template the user asked us to kill. Letting the legacy
    # narrator path serve `raw_engine_text` keeps the AI's clean Hinglish
    # narrative answer (which the wealth verdict block fed as ground-truth).
    if (not _NARRATIVE_MODE
            and os.environ.get("STRUCTURED_NARRATOR_ENABLED", "1") != "0"
            and isinstance(_struct_payload, dict)
            and _struct_payload
            and _looks_like_wealth_payload(_struct_payload)):
        try:
            print(
                f"[ai_ask_v2] structured wealth path used → "
                f"tag={(_struct_payload.get('verdict') or {}).get('tag')!r} "
                f"bucket={intent_bucket!r}",
                flush=True,
            )
            return _card_from_structured_wealth_payload(
                _struct_payload,
                intent_label    = intent_label,
                intent_bucket   = intent_bucket,
                intent_summary  = intent_summary,
                raw_topic       = raw_topic,
                raw_confidence  = raw_confidence,
                raw_followups   = raw_followups,
                legacy_text     = raw_engine_text,
            )
        except Exception as exc:
            # Structured-render failure → fall through to legacy narrator
            # so the user still sees something. Logged so we can investigate.
            print(
                f"[ai_ask_v2] structured wealth render failed → narrator_v2 "
                f"fallback ({type(exc).__name__}: {exc})",
                flush=True,
            )

    # ── P3: AI Mouth — reshape into conversational diagnostic card ─────────
    if os.environ.get("NARRATOR_V2_ENABLED", "1") != "0":
        try:
            from narrator_v2 import (  # local import
                compose_card_narrative,
                NarratorV2Error,
            )
            try:
                card = compose_card_narrative(
                    intent_summary  = intent_summary,
                    intent_bucket   = intent_bucket,
                    intent_facts    = intent_facts or {},
                    raw_engine_text = raw_engine_text,
                    language        = narrator_lang,
                    emotional_tone  = emotional_tone,
                    intent_domain   = intent_domain,
                )
                client_card = card.to_client_dict()
                # Compose final card payload for the client.
                final_text = (
                    f"{client_card['verdict_tag']}\n\n"
                    f"{client_card['narrative']}"
                )
                if client_card.get("remedy_line"):
                    final_text += f"\n\n{client_card['remedy_line']}"
                if client_card.get("advisor_line"):
                    final_text += f"\n\n{client_card['advisor_line']}"
                return {
                    "intent_label":   intent_label,
                    "intent_bucket":  intent_bucket,
                    "intent_summary": intent_summary,
                    "verdict_tag":    client_card["verdict_tag"],
                    "narrative":      client_card["narrative"],
                    "remedy_line":    client_card.get("remedy_line", ""),
                    "advisor_line":   client_card.get("advisor_line", ""),
                    "text":           final_text,
                    "topic":          raw_topic,
                    "confidence":     raw_confidence,
                    "source":         "ai_v2_narrator",
                    "follow_ups":     raw_followups,
                    "narrator_latency_ms": card.latency_ms,
                }
            except NarratorV2Error as nexc:
                # Narrator failed — fall back to raw engine text so user
                # still sees something. Mark source so caller can detect.
                print(f"[ai_ask_v2] narrator_v2 failed → raw engine text "
                      f"({nexc})", flush=True)
        except Exception as outer:
            print(f"[ai_ask_v2] narrator_v2 outer error: {outer}", flush=True)

    # Fallback: return the raw engine text as a non-conversational card.
    return {
        "intent_label":   intent_label,
        "intent_bucket":  intent_bucket,
        "intent_summary": intent_summary,
        "text":           raw_engine_text or "(empty)",
        "topic":          raw_topic,
        "confidence":     raw_confidence,
        "source":         raw_source,
        "follow_ups":     raw_followups,
    }


def ai_ask_v2(question: str,
              kundli: Any,
              lang: str = "en",
              reply_idx: int = 0,
              birth: Any = None,
              history: list | None = None,
              preferred_language: _Optional[str] = None) -> dict:
    """Sprint-26: thin passthrough to ai_ask().

    Historically this fanned out into multi-intent cards driven by the AI Ear
    extractor. The AI Ear has been removed (replaced by the single-shot
    `understand_question` classifier inside ai_ask), so multi-intent fan-out
    no longer exists. We keep this entry point so flask_app.py and any
    older callers continue to work — it just delegates to ai_ask() and
    returns the single-shape result.
    """
    return ai_ask(
        question, kundli, lang, reply_idx,
        birth=birth, history=history,
        preferred_language=preferred_language,
    )

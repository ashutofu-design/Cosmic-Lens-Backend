"""
wealth_engine.py — Deterministic Wealth & Finance verdict engine (Vedic / KP).

Mirror of career_timing.py + stock_engine.py + love_engine.py + marriage_engine.py
+ health_engine.py architecture (CLE format): pure-Python rule engine that
consumes the already-computed kundli + chart_intelligence + KP outputs and
produces a structured WEALTH verdict BEFORE the AI is invoked. The AI then acts
purely as a NARRATOR that converts this verdict into Hinglish prose — it MUST
NOT change verdict, score, timing window, strategy, or remedy. Brand-safety
guards are HARD STOPS — narrator MUST honour every guard (no specific rupee
amount, no lottery/jackpot promise, no "kangaal/barbaad" prediction, no
"loan band kar do" / "EMI skip kar do" advice, ALWAYS recommend qualified
CA / SEBI-registered financial-advisor consult, SEBI risk disclaimer for
investment / sudden-windfall buckets).

Inputs:
    kundli  : dict from kundli_engine.calculate_kundli (has planets, dashas,
              currentDasha, ascendant, moonSign, divisionalCharts D2/D9/D11)
    intel   : dict from chart_intelligence.analyze_chart (has dignities,
              house_lords, yogas, mangal_dosh, sade_sati, lagna_sign)
    kp      : dict from kp_engine.calculate_kp (has cusps, planets,
              significations) — for KP cuspal sub-lord cross-check on
              cusps 2 (saved money), 5 (sudden gains / poorva-punya),
              11 (income / labha)
    birth   : optional dict with at least "gender", "dob" so dasha + transit
              calculations are correct
    question: raw user text — drives the 12-bucket question classifier
              (salary_growth / business_profit / loan_clearance /
              property_purchase / investment_return / inheritance_timing /
              debt_recovery / sudden_windfall / savings_capacity /
              foreign_income / partnership_finance / general_wealth).

Output: see assess_wealth().__doc__

CLE Format Logic Framework (10 standard steps, mirror of health_engine):
    Step 1  — Question Type Detection (12-bucket classifier) + Tense Detector
    Step 2  — 2-Step Verdict Framework (natal_promise + current_trigger → bucket)
    Step 3  — Layer Stacking (25 layers + D9 + D2 Hora + D11 Labha + KP
              mandatory + Jupiter dhana karaka mandatory + Jaimini DK
              mandatory)
    Step 4  — Bucket-Gated Strategy (no contradictions allowed)
    Step 5  — Timing Window (Vimshottari + Jupiter/Saturn transits + KP)
    Step 6  — Remedy Selection (weakest dhana planet → mantra/donation)
    Step 7  — Confidence Calibration (cross-system agreement)
    Step 8  — Format-for-Prompt (locked Hinglish verdict block)
    Step 9  — AI Narrator Override (turn-level rules in openai_helper)
    Step 10 — Brand-Safety Guards (rupee-amount promise / lottery promise /
              bankruptcy prediction / loan-skip advice / SEBI disclaimer for
              investment & sudden-windfall — STRICT softening)

Layer rubric (canonical CLE table — wealth-specific):
    A. NATAL PROMISE  (Layers 1-15)
        L1  2nd house + 2L (kutumb dhana / saved money)  (weight 16)  ⭐ CORE
        L2  11th house + 11L (gains / income / labha)    (weight 16)  ⭐ CORE
        L3  5th house + 5L (poorva-punya / sudden gains) (weight 10)
        L4  9th house + 9L (bhagya / fortune)             (weight 10)
        L5  4th house + 4L (property / vehicle / comfort) (weight  8)
        L6  8th house + 8L (inheritance / joint funds)    (weight  6)
        L7  12th house + 12L (expenses / foreign income)  (weight  6)
        L8  6th house + 6L (loans / EMI / debts NEG)      (weight  8)  ⭐ CORE-NEG
        L9  Jupiter (dhana karaka)                         (weight 12)  ⭐ MANDATORY
        L10 Venus (luxury / comfort karaka)                (weight  6)
        L11 Mercury (business / trade karaka)              (weight  6)
        L12 Moon (cash flow karaka)                        (weight  5)
        L13 Sun (govt / authority income karaka)           (weight  5)
        L14 Dhana Karaka (Jaimini DK) + Atmakaraka          (weight 10)  ⭐ MANDATORY
        L15 Lagna-Bhava cross-aspect for 2H/11H            (weight  4)
    B. DIVISIONAL + KP (Layers 16-19)
        L16 D9 Navamsa overlay (sustained wealth)          (weight 10)  ⭐ MANDATORY
        L17 D2 Hora (WEALTH D-chart — Sun-Hora vs          (weight 14)  ⭐ MANDATORY
            Moon-Hora classification of wealth planets)
        L18 D11 Labha-amsa (gains-specific D-chart)        (weight 12)  ⭐ MANDATORY
        L19 KP cuspal sub-lord 2/5/11                       (weight 12)  ⭐ MANDATORY
    C. STRENGTH (Layers 20-22)
        L20 Ashtakavarga 2H/11H BAV                         (weight  5)
        L21 Shadbala (2L, 11L, Jupiter)                     (weight  5)
        L22 Bhava Bala (2/5/9/11)                           (weight  4)
    D. YOGAS (Layers 23-25)
        L23 Lakshmi + Dhana + Maha-Lakshmi + Raj +          (weight  8 +)
            Vipareeta-Raja (positive money yogas)
        L24 Daridra + Kemadruma + Anti-Dhana yogas          (weight  6 -)
        L25 Sade Sati on 2L/11L (saved-money pressure)      (weight  5  ±)
    E. TRIGGERS — is the natal promise activated NOW?
        T1  Vimshottari MD+AD+PD on 2/5/9/11 lords          (weight 12)
        T2  Jupiter transit on 2H / 5H / 11H                 (weight  7)
        T3  Saturn transit on 2H / 11H (saved-money)         (weight  5)
    F. MODIFIERS — 8 modifiers (±points, no own weight)
        M1  2L / 11L combust                                 (±5)
        M2  2L / 11L retrograde                              (±3)
        M3  Malefic aspects on 2H / 11H                       (±5)
        M4  Jupiter / Venus dignity                            (±4)
        M5  Vargottama lift for 2L / 11L                       (+4)
        M6  Parivartana exchange between dhana lords           (+5)
        M7  Neecha-bhanga of 2L or 11L                         (+4)
        M8  Sade Sati on 2L or 11L                              (-5)
    G. CONDITIONALS (only when question type matches)
        C1  Loan-clear timing (6L + 8H + Saturn deep-dive)
            — fires for q_type == "loan_clearance" or "debt_recovery"
        C2  Property-buy timing (4H + Mars + Venus + Jupiter transit)
            — fires for q_type == "property_purchase"
        C3  Investment-return (5H + 9H + 11H + KP sub-lord)
            — fires for q_type == "investment_return"
            — STRICT brand safety: SEBI disclaimer
        C4  Inheritance timing (8H + Jupiter + 11L)
            — fires for q_type == "inheritance_timing"
        C5  Sudden-windfall (5H + Rahu/Jupiter trigger)
            — fires for q_type == "sudden_windfall"
            — STRICT brand safety: NO lottery promise, NO rupee amount
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Optional

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORDS_LIST = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]
SIGN_LORDS = {SIGNS[i]: SIGN_LORDS_LIST[i] for i in range(12)}

DIGNITY_RANK = {
    "debilitated": 0, "enemy-sign": 1, "neutral-sign": 2,
    "friend-sign": 3, "own-sign": 4, "moolatrikona": 5, "exalted": 6,
}
DIGNITY_PTS = {
    "debilitated": -8, "enemy-sign": -4, "neutral-sign": 0,
    "friend-sign": +3, "own-sign": +6, "moolatrikona": +7, "exalted": +8,
}

NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}

# Wealth-relevant houses
WEALTH_HOUSES_PRIMARY = {2, 11}            # saved money + gains  ⭐ CORE
WEALTH_HOUSES_SECONDARY = {5, 9}           # sudden gains + bhagya
WEALTH_HOUSES_TERTIARY = {4, 8, 12}        # property + inheritance + foreign
WEALTH_DEBT_HOUSES = {6, 8}                # debts/loans (negative for wealth)
DUSHTANA = {6, 8, 12}
KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}

# Planet → wealth-domain mapping (for narration, not prediction)
PLANET_WEALTH = {
    "Jupiter": "primary dhana karaka — wisdom-led wealth, stable savings, "
               "long-term growth, dharmic income",
    "Venus":   "luxury, comfort, vehicles, jewellery, partnerships, "
               "creative-arts income",
    "Mercury": "business, trade, commerce, communication-based income, "
               "intellectual property",
    "Moon":    "cash flow, daily liquidity, public-facing income, "
               "real-estate rental",
    "Sun":     "govt / authority income, salary growth, recognition-based "
               "earnings",
    "Mars":    "real-estate purchase energy, property disputes, hard-asset "
               "ventures",
    "Saturn":  "long-term savings, structured EMIs, slow-but-steady wealth, "
               "labour income",
    "Rahu":    "speculative gains, foreign income, sudden windfall, "
               "unconventional sources",
    "Ketu":    "spiritual detachment from money, unexpected losses or "
               "sudden inheritance",
}

# Jaimini DK is normally "Darakaraka" (spouse). For wealth karaka the
# correct Jaimini significator is the planet with the LOWEST navamsa
# longitude after AK/AmK/etc — but "Dhana Karaka" is also a colloquial
# alias used in some texts for the wealth-significating planet derived
# from chara karakas. We use Jupiter as primary natural karaka and
# cross-check with the 7-planet Jaimini chara-karaka table from
# karakas.py (BK = Bhratri-karaka often signifies effort/income).
JAIMINI_WEALTH_ROLES = ("AK", "AmK", "BK")  # soul, mind, effort/income

_DAY_HI = {
    "Sunday":    "Ravivar",  "Monday":   "Somvar",   "Tuesday":  "Mangalvar",
    "Wednesday": "Budhvar",  "Thursday": "Guruvar",  "Friday":   "Shukravar",
    "Saturday":  "Shanivar",
}
_MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _ym_to_human(ym: str) -> str:
    """Convert 'YYYY-MM' to 'Mmm YYYY' for narration."""
    if not isinstance(ym, str) or len(ym) < 7:
        return ym or ""
    try:
        y, m = ym.split("-")[:2]
        mi = int(m)
        if 1 <= mi <= 12:
            return f"{_MONTH_NAMES[mi - 1]} {y}"
    except (ValueError, IndexError):
        pass
    return ym


# ─────────────────────────────────────────────────────────────────────────────
# QUESTION CLASSIFIER — 12 buckets
# ─────────────────────────────────────────────────────────────────────────────
# Ordered most-specific → most-general. First match wins.
_Q_PATTERNS: list[tuple[str, list[str]]] = [
    # ── INHERITANCE ── (most specific — must come BEFORE general property)
    ("inheritance_timing", [
        r"\b(inheritance|inherited|inherit|heir|heirship|virasat|viraasat|"
        r"wirasat|wasiyat|will|legacy|baap[- ]?dada|pita[- ]?ji|"
        r"ancestral property|paitrik|paitruk|paitrik sampatti|"
        r"family wealth|family inheritance|maternal property|nani|dadi|"
        r"after death|expire ke baad|guzar jaane ke baad)\b",
        r"\b(विरासत|वसीयत|पैतृक|पैत्रिक संपत्ति|बाप[- ]?दादा)\b",
    ]),
    # ── DEBT RECOVERY ── (someone owes ME money — must come BEFORE
    # loan_clearance because both share udhaar/karz vocabulary; debt_recovery
    # is the MORE specific direction-of-money case)
    ("debt_recovery", [
        r"\b(udhaar diya|udhar diya|paisa diya|paise diye|loan diya|"
        r"diya hua paisa|diya hua udhaar|diya hua udhar|"
        r"unhone return nahi kiya|return nahi kar raha|return nahi kar rahi|"
        r"wapas nahi kiya|wapas nahi kar raha|wapas nahi kar rahi|"
        r"recover paisa|recover money|paisa wapas|paisa vapas|"
        r"due paisa|outstanding amount|stuck money|"
        r"udhaar wapas|udhar wapas|udhaar vapas|udhar vapas)\b",
        r"\b(maine|mene|me ne|maine to|hum ne|humne)\b.*\b("
        r"udhaar|udhar|paisa|paise|loan)\b.*\b(diya|diye|de chuka|de chuki)\b",
        r"\b(मेरा पैसा|उधार दिया|वापस|बकाया)\b.*\b(कब|कैसे|मिलेगा)\b",
    ]),
    # ── LOAN CLEARANCE ── (specific — debt-out timing)
    ("loan_clearance", [
        r"\b(loan|loans)\b.*\b(clear|clearance|repay|repayment|payoff|pay[- ]?off|"
        r"khatam|khatm|chukana|chukna|chukane|nipta|niptana|finish|free|done|"
        r"close|closure)\b",
        r"\b(emi|e\.m\.i|equated monthly|monthly installment)\b.*\b("
        r"khatam|khatm|chukana|finish|free|done|close|kab|when)\b",
        r"\b(debt|debts|karz|karza|karzaa|karzdaar|udhaar|udhar|udhari|"
        r"kuldevta ka karz)\b.*\b(clear|repay|khatam|chukana|free|done|kab|when|"
        r"mukti|relief)\b",
        r"\b(home loan|housing loan|car loan|vehicle loan|education loan|"
        r"personal loan|business loan|mortgage)\b.*\b(kab|when|clear|repay|"
        r"khatam|chukana|finish)\b",
        r"\b(कर्ज|कर्जा|उधार|ऋण|EMI)\b.*\b(कब|खत्म|चुकाना|मुक्ति|बंद)\b",
    ]),
    # ── PROPERTY PURCHASE ──
    ("property_purchase", [
        r"\b(property|properties|ghar|makaan|makan|flat|apartment|villa|"
        r"plot|jameen|jamin|zameen|zameene|land|land plot|building|"
        r"bungalow|house|home|new house|naya ghar|"
        r"real[- ]?estate|real estate|realty)\b.*\b("
        r"kab|when|kharid|kharidna|kharide|buy|buying|purchase|purchasing|"
        r"book|booking|invest|loan|emi|finance|plan|chahiye|chahta|chahti|"
        r"banwana|banana|construct|construction)\b",
        r"\b(naya ghar|new home|naya makaan|new flat)\b.*\b("
        r"kab|when|milega|milegi|hoga)\b",
        r"\b(vehicle|car|gaadi|gaadi kab|naya gaadi|naya vehicle|"
        r"new car|nayi gaadi|two[- ]?wheeler|bike|scooter)\b.*\b("
        r"kab|when|kharid|kharidna|buy|buying|purchase|finance|loan)\b",
        r"\b(संपत्ति|जायदाद|जमीन|जमीन|मकान|घर|फ्लैट|प्लॉट|गाड़ी)\b.*\b("
        r"कब|खरीद|खरीदना|बुक|लोन|EMI)\b",
    ]),
    # ── INVESTMENT RETURN ──
    # NOTE: must NOT collide with stock-engine (share/SIP/equity/mutual fund).
    # Stock engine is HIGHER priority — it has its own gate. This bucket is
    # for generic "investment" / "FD / RD / PPF / NPS / gold investment /
    # crypto generic" / "kahan paisa lagaau" only when user has NOT named
    # share/stock terms.
    ("investment_return", [
        r"\b(fd|fixed deposit|rd|recurring deposit|ppf|nps|elss|"
        r"sukanya samriddhi|kisan vikas patra|nsc|"
        r"national savings certificate|chit fund|chit funds|"
        r"gold scheme|gold investment|sone mein invest|"
        r"insurance plan|ulip|endowment plan|money[- ]?back plan|"
        r"sip plan general|mutual fund general)\b",
        r"\b(invest|investment|investments|nivesh|nivesh kahaan|kahaan invest|"
        r"kahan paisa|kahan invest|where to invest|"
        r"invest kar(?:un|na|na chahta|na chahti)|"
        r"invest karne ka best|best investment)\b",
        r"\b(return|returns|munafa|munaafa|fayda|labh)\b.*\b("
        r"investment|nivesh|fd|rd|ppf|sip|mutual fund|"
        r"gold scheme|insurance plan|nps|elss)\b",
        # Reverse direction: investment-vehicle word first, then return/profit
        r"\b(fd|rd|ppf|sip|nps|elss|mutual fund|gold scheme|insurance plan|"
        r"nivesh|investment)\b.*\b(return|returns|profit|munafa|munaafa|"
        r"fayda|labh|kab|when|milega|milegi|hoga|hogi|expected|expect|"
        r"acha|achha|achchha|good|best)\b",
        r"\b(निवेश|एफडी|आरडी|पीपीएफ|सोना|गोल्ड)\b.*\b(कब|कहाँ|कितना|return)\b",
    ]),
    # ── SUDDEN WINDFALL ── (lottery / unexpected gain / inheritance windfall)
    ("sudden_windfall", [
        r"\b(lottery|lottery winner|jackpot|jack[- ]?pot|"
        r"sudden money|sudden gain|sudden wealth|sudden windfall|"
        r"unexpected money|unexpected gain|unexpected wealth|"
        r"surprise money|surprise gain|"
        r"achanak paisa|achaanak paisa|achanak dhan|achaanak dhan|"
        r"achanak wealth|sudden mein paisa|"
        r"luck money|kismat se paisa|kismat ka paisa|"
        r"satta|satta king|matka|kbc|kaun banega crorepati|"
        r"prize money|crorepati|millionaire bann|"
        r"bonus|big bonus|incentive|incentive bumper|special incentive|"
        r"surprise inheritance|sudden inheritance)\b",
        r"\b(लॉटरी|जैकपॉट|अचानक धन|अचानक पैसा|किस्मत|बंपर)\b",
    ]),
    # ── FOREIGN INCOME ──
    ("foreign_income", [
        r"\b(foreign income|videshi income|foreign money|videshi paisa|"
        r"foreign earning|videsh se kamai|videsh ki kamai|"
        r"videsh mein kamai|abroad income|overseas income|nri income|"
        r"dollar income|euro income|pound income|"
        r"foreign business|export business|export[- ]?import|"
        r"foreign client|videshi client|usa client|us client|"
        r"foreign job income|onsite|onsite payment|onsite ka paisa|"
        r"remittance|nri remittance|fcnr|nri account)\b",
        r"\b(videsh|abroad|foreign|usa|america|canada|uk|gulf|dubai)\b.*\b("
        r"income|paisa|earning|kamai|kamayi|salary|business)\b",
        r"\b(विदेश|विदेशी|डॉलर|यूरो|एनआरआई|FCNR)\b.*\b(पैसा|कमाई|आमदनी|आय)\b",
    ]),
    # ── PARTNERSHIP FINANCE ──
    ("partnership_finance", [
        r"\b(partnership|partner|partners|business partner|"
        r"joint venture|jv|joint business|saajha|saajhedaari|saajhedari|"
        r"sahyog|sahayog|sahyogi|"
        r"firm partnership|llp|limited liability|"
        r"profit sharing|profit share|share in business|"
        r"partner ke saath|partner se|partner ka)\b",
        r"\b(साझेदारी|पार्टनरशिप|पार्टनर|जॉइंट वेंचर)\b",
    ]),
    # ── BUSINESS PROFIT ──
    # Must come AFTER career_timing has handled "business start".
    # This is for ONGOING business profit / loss / cash-flow questions.
    ("business_profit", [
        r"\b(business)\b.*\b(profit|munafa|munaafa|fayda|labh|"
        r"loss|nuksaan|nuksan|"
        r"income|earning|kamai|kamayi|"
        r"chal raha|chalega|chalegi|"
        r"growth|grow|expand|expansion|scale|scaling)\b",
        r"\b(dhanda|dhandha|kaam|udyog|vyapaar|vyaapar|business)\b.*\b("
        r"badhega|badhegi|chalega|chalegi|profit|labh|fayda|munafa|"
        r"barbaad|band|fail|loss|kab|when)\b",
        r"\b(shop|dukaan|dukan|store)\b.*\b("
        r"chalegi|chalega|profit|labh|fayda|kab|kamai|earning)\b",
        r"\b(startup|start[- ]?up|venture)\b.*\b("
        r"profit|munafa|labh|growth|chalega|kamai|when|kab)\b",
        r"\b(व्यापार|व्यवसाय|दुकान|धंधा)\b.*\b(कब|कैसे|लाभ|मुनाफा|आय|कमाई)\b",
    ]),
    # ── SAVINGS CAPACITY ──
    ("savings_capacity", [
        r"\b(savings|saving|save money|save karna|save karu|"
        r"bachat|bachaat|bachana|bachat ki|saving rate|"
        r"emergency fund|emergency saving|rainy day fund|"
        r"financial cushion|financial security|financial freedom|"
        r"financial independence|fire movement|fire goal|"
        r"retirement saving|retirement plan|retirement fund|"
        r"corpus|corpus building|wealth corpus|"
        r"money management|paisa manage|paise manage|paisa kaise manage)\b",
        r"\b(paisa|paise|dhan|dhanya)\b.*\b(save|bachat|bachao|"
        r"jamaa|jamana|jodna)\b",
        r"\b(बचत|जमा|सेविंग|वित्तीय सुरक्षा|रिटायरमेंट)\b",
    ]),
    # ── SALARY GROWTH ──
    # Must come AFTER career_timing (which handles new_job/promotion).
    # This is for raw "salary increase / increment / hike / appraisal" Qs
    # that are about MONEY not job-change.
    ("salary_growth", [
        r"\b(salary|salary growth|salary increase|salary hike|"
        r"salary increment|increment|hike|appraisal|appraisal cycle|"
        r"raise|pay raise|pay hike|"
        r"vetan|vetan badhna|vetan badhega|vetan vridhi|"
        r"package|ctc|in[- ]?hand salary|take home salary)\b",
        r"\b(salary|vetan|package|ctc)\b.*\b("
        r"badhega|badhegi|kab|when|increase|hike|growth|increment)\b",
        r"\b(वेतन|तनख्वाह|सैलरी|पैकेज|वेतन वृद्धि|प्रमोशन)\b.*\b(कब|बढ़ेगा|बढ़ेगी)\b",
    ]),
    # ── GENERAL WEALTH ── (catch-all)
    ("general_wealth", [
        r"\b(wealth|dhana|dhan|laxmi|lakshmi|lakshmi yog|lakshmi yoga|"
        r"dhana yog|dhana yoga|dhan yog|dhan yoga|maa lakshmi|"
        r"riches|rich|prosperity|prosperous|amir|ameer|ameeri|"
        r"financial|financially|finance|"
        r"paisa|paise|paisa kab|paise kab|kab paisa|kab paise|"
        r"money|kab money|monetary|"
        r"income|kamai|kamayi|"
        r"crorepati|millionaire|billionaire|"
        r"kismat ka paisa|bhagya ka paisa|"
        r"financial growth|financial future|financial condition|"
        r"financial situation|economic condition|paisa lautega|"
        r"lakshmi prapti|dhan prapti|samriddhi)\b",
        r"\b(पैसा|पैसे|धन|लक्ष्मी|समृद्धि|आय|आमदनी|कमाई|वित्तीय|"
        r"धनवान|अमीर|करोड़पति)\b",
    ]),
]


# Sprint-25 Fix-B: AI-Ear-trusted wealth bucket vocabulary. AI Ear's
# vocabulary diverges from the engine's legacy bucket names in 3 places —
# without normalization the bucket-specific conditionals (C1/C2/C4) and
# `sudden_windfall` clamp would silently miss when AI Ear sets the bucket.
# These aliases keep the engine's downstream logic intact.
_VALID_WEALTH_BUCKETS = frozenset({
    "salary_growth", "business_profit", "loan_emi", "loan_clearance",
    "property", "property_purchase",
    "inheritance", "inheritance_timing",
    "savings_corpus", "debt_recovery", "foreign_income",
    "partnership_finance", "investment_return",
    "sudden_windfall", "tax_compliance",
    "expense_leakage", "partnership_exit", "business_continuation",
    "general_wealth",
})
_WEALTH_BUCKET_ALIASES = {
    "loan_emi":     "loan_clearance",     # C1 conditional + debt-recovery cluster
    "property":     "property_purchase",  # C2 conditional
    "inheritance":  "inheritance_timing", # C4 conditional
}


def classify_wealth_question(question: str,
                             pre_classified_bucket: str | None = None) -> str:
    """Return one of the 12 wealth buckets for the question text.
    First match wins; falls back to 'general_wealth' if no match. The
    classifier is INTENTIONALLY broad — the wealth gate in
    `openai_helper.py` decides whether the engine fires at all (priority:
    marriage > stock > love > career > wealth > health > general).
    Stock-share-SIP-equity-intraday questions are HIGHER priority and
    are routed to `stock_engine.py` upstream — they will not reach this
    classifier.

    When `pre_classified_bucket` (Sprint-25 AI-Ear handoff) is in the
    engine's known vocabulary, return it directly — bypassing regex.
    """
    if pre_classified_bucket and pre_classified_bucket in _VALID_WEALTH_BUCKETS:
        # Normalize AI Ear's vocab to legacy bucket names so the downstream
        # bucket-keyed conditionals (C1/C2/C4) and clamps fire correctly.
        return _WEALTH_BUCKET_ALIASES.get(pre_classified_bucket, pre_classified_bucket)
    if not isinstance(question, str) or not question.strip():
        return "general_wealth"
    s = question.lower().strip()
    for bucket, patterns in _Q_PATTERNS:
        for pat in patterns:
            try:
                if re.search(pat, s, re.IGNORECASE):
                    return bucket
            except re.error:
                continue
    return "general_wealth"


# ─────────────────────────────────────────────────────────────────────────────
# TENSE DETECTOR — future / present / general
# ─────────────────────────────────────────────────────────────────────────────
_TENSE_PRESENT_RX = re.compile(
    r"\b(abhi|aaj|aaj kal|aajkal|currently|right now|"
    r"chal raha|chal rahi|kar raha|kar rahi|ho raha|ho rahi|"
    r"de raha|de rahi|mil raha|mil rahi|"
    r"is time|is samay|filhal|filhaal|fir bhi|abhi tak|"
    r"present|presently|at present|in present|at the moment|"
    r"current|currently|chalu hai|chal rahi hai)\b",
    re.IGNORECASE,
)
_TENSE_FUTURE_RX = re.compile(
    r"\b(kab|when|kab tak|kab hoga|kab hogi|kab milega|kab milegi|"
    r"hoga|hogi|hone|honge|aayegi|aayega|niklega|niklegi|"
    r"future|aane wala|aane wali|aane waali|"
    r"agle|agla|next|coming|coming up|upcoming|"
    r"baad mein|baad me|after|afterwards|later|"
    r"is saal|is mahine|next month|next year|agle saal|agle mahine|"
    r"jaldi|soon|shortly|"
    r"will|would|going to|about to|"
    r"upay|remedy|kya karna chahiye|what should i do|"
    r"timing|window)\b",
    re.IGNORECASE,
)


def detect_question_tense(text: str) -> str:
    """Return 'future' / 'present' / 'general'. Used by the narrator to
    frame the timing window correctly per question tense (mirror of
    health_engine.detect_question_tense)."""
    if not isinstance(text, str) or not text.strip():
        return "general"
    s = text.lower().strip()
    has_present = bool(_TENSE_PRESENT_RX.search(s))
    has_future = bool(_TENSE_FUTURE_RX.search(s))
    if has_present and not has_future:
        return "present"
    if has_future and not has_present:
        return "future"
    if has_present and has_future:
        if re.search(r"\b(abhi|aaj kal|aajkal|currently|right now|now|"
                     r"chal raha|kar raha|ho raha|de raha|mil raha)\b", s):
            return "present"
        return "future"
    return "general"


# ─────────────────────────────────────────────────────────────────────────────
# BRAND-SAFETY WARNINGS  (HARD STOPS for the narrator)
# ─────────────────────────────────────────────────────────────────────────────
# Buckets where a SEBI-style "investments are subject to market risk"
# disclaimer line is REQUIRED (high-risk financial decisions).
_HIGH_RISK_BUCKETS = {
    "investment_return",
    "sudden_windfall",
    "business_profit",
    "partnership_finance",
}


def _brand_safety_warnings(bucket: str) -> list[str]:
    """Return the list of bucket-specific brand-safety guards the narrator
    is contractually bound to honour. The deterministic post-processor in
    `openai_helper.py` enforces (a) and (b) below as hard last-line
    fallbacks; the rest are negative constraints the LLM must NOT violate."""
    universal = [
        # (a) UNIVERSAL — every wealth reply
        "Qualified CA / SEBI-registered financial advisor se zaroor "
        "consult karein — cosmic guidance investment, tax planning ya "
        "loan decision ka vikalp nahi hai.",
        "NEVER predict a specific rupee amount (e.g. '50 lakh milega', "
        "'2 crore kamaaoge', '15 lakh ki property') — emit only relative "
        "language ('income mein vridhi', 'savings strong', 'property "
        "scope strong').",
        "NEVER predict bankruptcy / 'kangaal ho jaoge' / 'barbaad ho "
        "jaaoge' / 'sab kuch lut jaayega' — soften every red verdict to "
        "'extra-savitree period', 'corpus protect karein', 'expansion "
        "ke liye wait karein'.",
        "NEVER tell user to skip EMI, default on loan, stop tax payment, "
        "evade GST, or commit any financial-fraud action — engine NEVER "
        "advises illegal financial behaviour.",
        "NEVER predict lottery / satta / KBC / matka / jackpot win — these "
        "are gambling and engine NEVER endorses them.",
    ]
    bucket_specific = {
        "salary_growth": [
            "NEVER promise a specific increment % or specific package "
            "amount — emit only relative language.",
            "If verdict is red_avoid, suggest 'agla appraisal cycle wait "
            "karein, current role mein value-add increase karein', NEVER "
            "'job chod do' (career_timing handles job-change).",
        ],
        "business_profit": [
            "NEVER predict business closure / 'dhandha band ho jaayega' — "
            "soften to 'cash flow tight rahega, expansion 6-12 months "
            "wait karein'.",
            "Add SEBI-style line: 'Business decisions market risk ke "
            "adheen hain — qualified business advisor ki salah lein.'",
        ],
        "loan_clearance": [
            "NEVER tell user to default on EMI or skip payment.",
            "NEVER promise exact loan-clear date — emit window only.",
            "If verdict slow_burn / red_avoid, suggest 'pre-payment "
            "strategy ya refinancing options' — NEVER 'loan cancel kar "
            "do' or 'EMI band kar do'.",
        ],
        "property_purchase": [
            "NEVER promise a specific rupee value of the property.",
            "NEVER endorse a specific builder, project, or city without "
            "user-supplied data.",
            "Always recommend RERA-registered project + legal title check.",
        ],
        "investment_return": [
            "MANDATORY SEBI disclaimer line: 'Investments market risk ke "
            "adheen hain — scheme documents carefully padein.'",
            "NEVER promise a specific return % — emit only relative "
            "language.",
            "NEVER endorse a specific stock / mutual-fund scheme / crypto "
            "coin (stock_engine has its own routing).",
        ],
        "inheritance_timing": [
            "NEVER predict the death of a family member — engine NEVER "
            "predicts death.",
            "Soften to 'paitrik sampatti ka transition window' / "
            "'ancestral wealth activation period'.",
            "NEVER tell user to 'hurry up' on inheritance disputes.",
        ],
        "debt_recovery": [
            "NEVER tell user to use coercion / threat / illegal collection "
            "tactics.",
            "Always recommend legal-recourse (notice / court / arbitration) "
            "over personal pressure.",
        ],
        "sudden_windfall": [
            "MANDATORY SEBI-style line + gambling disclaimer: 'Sudden "
            "windfall ka cosmic indication hai par lottery, satta, ya "
            "speculation par bharosa nahi karein — ethical earning yog "
            "primary hain.'",
            "NEVER promise a specific date for the windfall.",
            "NEVER promise a specific amount.",
        ],
        "savings_capacity": [
            "Encourage SIP / RD / PPF / FD building, NEVER promise specific "
            "corpus size.",
        ],
        "foreign_income": [
            "Mention FEMA / NRI compliance if foreign-source income is "
            "discussed; NEVER advise tax evasion or unreported "
            "remittance.",
        ],
        "partnership_finance": [
            "ALWAYS recommend a written, legally-vetted partnership "
            "agreement (LLP / partnership deed).",
            "NEVER tell user to 'trust verbally' or 'paperwork later'.",
        ],
        "general_wealth": [],
    }
    return universal + bucket_specific.get(bucket, [])


# ─────────────────────────────────────────────────────────────────────────────
# COMMON HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _sign_idx(name: str) -> int:
    """Return 0..11 sign index for sign name; -1 if unknown."""
    if not isinstance(name, str):
        return -1
    n = name.strip().capitalize()
    return SIGNS.index(n) if n in SIGNS else -1


def _norm(name: str) -> str:
    return (name or "").strip().capitalize()


def _planet_house(planets: list, planet_name: str) -> Optional[int]:
    for p in (planets or []):
        if isinstance(p, dict) and p.get("name") == planet_name:
            h = p.get("house")
            if isinstance(h, int):
                return h
    return None


def _planet_sign(planets: list, planet_name: str) -> Optional[str]:
    for p in (planets or []):
        if isinstance(p, dict) and p.get("name") == planet_name:
            return p.get("sign")
    return None


def _planet_lon(planets: list, planet_name: str) -> Optional[float]:
    for p in (planets or []):
        if isinstance(p, dict) and p.get("name") == planet_name:
            for k in ("longitude", "lon", "fullDegree", "absoluteDegree"):
                v = p.get(k)
                if isinstance(v, (int, float)):
                    return float(v) % 360.0
    return None


def _is_retrograde(planets: list, planet_name: str) -> bool:
    for p in (planets or []):
        if isinstance(p, dict) and p.get("name") == planet_name:
            return bool(p.get("retrograde") or p.get("isRetro"))
    return False


def _is_combust(planets: list, planet_name: str,
                threshold_deg: float = 8.0) -> bool:
    if planet_name == "Sun":
        return False
    sun_lon = _planet_lon(planets, "Sun")
    p_lon = _planet_lon(planets, planet_name)
    if sun_lon is None or p_lon is None:
        return False
    diff = abs(sun_lon - p_lon)
    if diff > 180:
        diff = 360 - diff
    return diff < threshold_deg


def _house_lord(intel: dict, house_num: int) -> Optional[str]:
    """Return the lord-planet for a house number from intel.house_lords.
    Tolerates BOTH shapes: dict {"1": "Sun", ...} and the chart_intelligence
    list-of-dict shape [{"house": 1, "lord": "Sun", ...}, ...]."""
    if not isinstance(intel, dict):
        return None
    hl = intel.get("house_lords")
    if isinstance(hl, list):
        for h in hl:
            if isinstance(h, dict) and (
                    h.get("house") == house_num
                    or h.get("house") == str(house_num)
                    or str(h.get("house")) == str(house_num)):
                lord = h.get("lord")
                return lord if isinstance(lord, str) else None
        return None
    if isinstance(hl, dict):
        v = hl.get(str(house_num)) or hl.get(house_num)
        return v if isinstance(v, str) else None
    return None


def _planet_dignity(intel: dict, planet_name: str) -> Optional[str]:
    """Return dignity string for a planet from intel.dignities.
    Tolerates BOTH shapes: dict and list-of-dict (mirror of health_engine).
    """
    if not isinstance(intel, dict):
        return None
    dgn = intel.get("dignities")
    if isinstance(dgn, list):
        for d in dgn:
            if isinstance(d, dict) and d.get("planet") == planet_name:
                v = d.get("status") or d.get("dignity")
                return v if isinstance(v, str) else None
        return None
    if isinstance(dgn, dict):
        v = dgn.get(planet_name)
        return v if isinstance(v, str) else None
    return None


def _aspect_houses(planet_name: str, planet_house_num: int) -> set[int]:
    """Return the set of house numbers a planet aspects from its current house.
    All planets aspect 7H from self. Mars aspects 4 + 7 + 8. Jupiter aspects
    5 + 7 + 9. Saturn aspects 3 + 7 + 10. Rahu/Ketu have full aspects on 5,
    7, 9 (Vedic standard). Sun/Moon/Mercury/Venus only aspect 7H."""
    if not isinstance(planet_house_num, int) or not (1 <= planet_house_num <= 12):
        return set()

    def _h(offset: int) -> int:
        return ((planet_house_num - 1 + offset) % 12) + 1

    base = {_h(6)}  # 7th aspect (offset 6)
    if planet_name == "Mars":
        return base | {_h(3), _h(7)}  # 4th, 8th
    if planet_name == "Jupiter":
        return base | {_h(4), _h(8)}  # 5th, 9th
    if planet_name == "Saturn":
        return base | {_h(2), _h(9)}  # 3rd, 10th
    if planet_name in ("Rahu", "Ketu"):
        return base | {_h(4), _h(8)}  # 5th, 9th (per Lal Kitab + KP)
    return base


def _planets_aspecting_house(planets: list, target_house: int) -> list[str]:
    out = []
    for p in (planets or []):
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        h = p.get("house")
        if not isinstance(h, int):
            continue
        if target_house in _aspect_houses(nm, h):
            out.append(nm)
    return out


def _dasha_lords(kundli: dict) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (Mahadasha lord, Antardasha lord, Pratyantar lord) tolerating
    multiple key naming conventions used across the codebase. Mirrors
    health_engine._dasha_lords / career_timing._dasha_lords."""
    if not isinstance(kundli, dict):
        return None, None, None
    md = ad = pd = None
    cd = kundli.get("currentDasha") or {}
    if isinstance(cd, dict):
        for k in ("mahadasha", "maha", "MD", "md_lord", "mahadashaLord"):
            v = cd.get(k)
            if isinstance(v, str) and v.strip():
                md = v.strip()
                break
        for k in ("antardasha", "antar", "AD", "ad_lord", "antardashaLord"):
            v = cd.get(k)
            if isinstance(v, str) and v.strip():
                ad = v.strip()
                break
        for k in ("pratyantar", "pratyantardasha", "PD", "pd_lord",
                  "pratyantarLord"):
            v = cd.get(k)
            if isinstance(v, str) and v.strip():
                pd = v.strip()
                break
    # Fallback: parse currentPhase.name = "MD – AD" if MD/AD missing
    if (not md or not ad) and isinstance(kundli.get("currentPhase"), dict):
        nm = (kundli["currentPhase"].get("name") or "").strip()
        if "–" in nm or "-" in nm or "/" in nm:
            sep = "–" if "–" in nm else ("-" if "-" in nm else "/")
            parts = [x.strip() for x in nm.split(sep) if x.strip()]
            if len(parts) >= 1 and not md:
                md = parts[0].split()[0] if parts[0] else None
            if len(parts) >= 2 and not ad:
                ad = parts[1].split()[0] if parts[1] else None
    # PD fallback: walk dashas tree
    if not pd and isinstance(kundli.get("dashas"), list) and md and ad:
        try:
            for dm in kundli["dashas"]:
                if not isinstance(dm, dict):
                    continue
                if dm.get("planet") != md:
                    continue
                for da in (dm.get("subDashas") or []):
                    if not isinstance(da, dict):
                        continue
                    if da.get("planet") != ad:
                        continue
                    for dp in (da.get("subDashas") or []):
                        if isinstance(dp, dict) and dp.get("active"):
                            pd = dp.get("planet")
                            break
        except Exception:
            pass
    return md, ad, pd


def _planet_significates_houses(kp: dict, planet_name: str) -> set[int]:
    """Return the set of house numbers a planet significates per KP.
    Reads from kp.significations[planet] when available; tolerates both
    {planet: [houses]} and {planet: {houses: [...]}} shapes."""
    if not isinstance(kp, dict):
        return set()
    sig = kp.get("significations") or {}
    v = sig.get(planet_name)
    if isinstance(v, list):
        return {int(h) for h in v if isinstance(h, int)}
    if isinstance(v, dict):
        hs = v.get("houses") or []
        if isinstance(hs, list):
            return {int(h) for h in hs if isinstance(h, int)}
    return set()


# ─────────────────────────────────────────────────────────────────────────────
# LAZY LOADERS — reuse already-installed modules; never crash if missing
# ─────────────────────────────────────────────────────────────────────────────
def _maybe_shadbala(kundli: dict, lagna_idx: int) -> dict:
    try:
        from shadbala import compute_shadbala  # type: ignore
        return compute_shadbala(kundli, lagna_idx) or {}
    except Exception:
        return {}


def _maybe_ashtakavarga(kundli: dict, lagna_idx: int) -> dict:
    try:
        from ashtakavarga import compute_ashtakavarga  # type: ignore
        return compute_ashtakavarga(kundli, lagna_idx) or {}
    except Exception:
        return {}


def _maybe_bhava_bala(intel: dict, shadbala_d: dict) -> dict:
    try:
        from bhava_bala import compute_bhava_bala  # type: ignore
        return compute_bhava_bala(intel, shadbala_d) or {}
    except Exception:
        return {}


def _maybe_karakas(kundli: dict) -> dict:
    """Return the Jaimini chara karakas dict {AK, AmK, BK, MK, PK, GK, DK}.
    For wealth analysis we use AK (soul-vitality colours wealth karma),
    AmK (mind-strategy directs how money is earned), and BK (effort/income
    significator — Bhratri-karaka in Jaimini's wealth-cluster reading)."""
    try:
        from karakas import compute_karakas  # type: ignore
        return compute_karakas(kundli.get("planets") or []) or {}
    except Exception:
        return {}


def _maybe_argala(kundli: dict) -> dict:
    try:
        from argala import compute_argala  # type: ignore
        return compute_argala(kundli.get("planets") or []) or {}
    except Exception:
        return {}


def _maybe_varga_yogas(kundli: dict, lagna_lon: Optional[float]) -> dict:
    try:
        from yogas import detect_yogas  # type: ignore
        return detect_yogas(kundli.get("planets") or [], lagna_lon) or {}
    except Exception:
        return {}


def _maybe_jupiter_transit(lagna_sign_idx: int,
                           moon_sign_idx: Optional[int]) -> dict:
    """Live Jupiter transit windows for next 3 years over wealth-trigger signs.
    For wealth, support houses from lagna are 2 (saved money), 5 (sudden gains),
    11 (income). Reuses transit_engine's jupiter_sign_changes."""
    try:
        from transit_engine import jupiter_sign_changes  # type: ignore
        SIGNS_LOCAL = SIGNS
        start = datetime.utcnow()
        target_offsets = {1, 4, 10}  # 2nd, 5th, 11th (0-indexed)
        targets: dict[int, list[str]] = {}
        for off in target_offsets:
            s_l = (lagna_sign_idx + off) % 12
            targets.setdefault(s_l, []).append(f"L{off + 1}")
            if moon_sign_idx is not None and moon_sign_idx >= 0:
                s_m = (moon_sign_idx + off) % 12
                targets.setdefault(s_m, []).append(f"M{off + 1}")
        windows = jupiter_sign_changes(
            start, start + timedelta(days=3 * 365 + 30))
        out_active: list[dict] = []
        out_upcoming: list[dict] = []
        now = start
        for w in (windows or []):
            try:
                s_idx = SIGNS_LOCAL.index(w.get("sign"))
            except (ValueError, TypeError):
                continue
            if s_idx not in targets:
                continue
            sd = w.get("startDate")
            ed = w.get("endDate")
            if isinstance(sd, str):
                try:
                    sd_dt = datetime.fromisoformat(sd[:10])
                except ValueError:
                    continue
            else:
                continue
            if isinstance(ed, str):
                try:
                    ed_dt = datetime.fromisoformat(ed[:10])
                except ValueError:
                    continue
            else:
                continue
            entry = {
                "sign": w.get("sign"),
                "houses_from_lagna_moon": targets[s_idx],
                "start": sd_dt.strftime("%Y-%m"),
                "end": ed_dt.strftime("%Y-%m"),
            }
            if sd_dt <= now <= ed_dt:
                out_active.append(entry)
            elif sd_dt > now:
                out_upcoming.append(entry)
        return {"active": out_active, "upcoming": out_upcoming[:3]}
    except Exception:
        return {}


def _maybe_saturn_transit_wealth(lagna_sign_idx: int,
                                 moon_sign_idx: Optional[int]) -> dict:
    """Live Saturn transit windows for next 3 years over wealth-pressure signs.
    For wealth, the pressure houses from lagna are 2 (saved money) and 11
    (income reduction). Reuses transit_engine's saturn_sign_changes."""
    try:
        from transit_engine import saturn_sign_changes  # type: ignore
        SIGNS_LOCAL = SIGNS
        start = datetime.utcnow()
        target_offsets = {1, 10}  # 2nd, 11th (0-indexed: 1, 10)
        targets: dict[int, list[str]] = {}
        for off in target_offsets:
            s_l = (lagna_sign_idx + off) % 12
            targets.setdefault(s_l, []).append(f"L{off + 1}")
            if moon_sign_idx is not None and moon_sign_idx >= 0:
                s_m = (moon_sign_idx + off) % 12
                targets.setdefault(s_m, []).append(f"M{off + 1}")
        windows = saturn_sign_changes(
            start, start + timedelta(days=3 * 365 + 30))
        out_active: list[dict] = []
        out_upcoming: list[dict] = []
        now = start
        for w in (windows or []):
            try:
                s_idx = SIGNS_LOCAL.index(w.get("sign"))
            except (ValueError, TypeError):
                continue
            if s_idx not in targets:
                continue
            sd = w.get("startDate")
            ed = w.get("endDate")
            if isinstance(sd, str):
                try:
                    sd_dt = datetime.fromisoformat(sd[:10])
                except ValueError:
                    continue
            else:
                continue
            if isinstance(ed, str):
                try:
                    ed_dt = datetime.fromisoformat(ed[:10])
                except ValueError:
                    continue
            else:
                continue
            entry = {
                "sign": w.get("sign"),
                "houses_from_lagna_moon": targets[s_idx],
                "start": sd_dt.strftime("%Y-%m"),
                "end": ed_dt.strftime("%Y-%m"),
            }
            if sd_dt <= now <= ed_dt:
                out_active.append(entry)
            elif sd_dt > now:
                out_upcoming.append(entry)
        return {"active": out_active, "upcoming": out_upcoming[:3]}
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# DIVISIONAL CHART HELPERS — D2 Hora + D11 Labha-amsa (computed inline if
# kundli.divisionalCharts.D2 / D11 are absent). Reuses the proven
# chart_intelligence shapes wherever possible.
# ─────────────────────────────────────────────────────────────────────────────
def _d2_hora(planets: list) -> dict:
    """Compute D2 Hora chart classification for each planet.
    D2 Hora is a 2-fold division of every sign:
        Odd signs (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius):
            0°-15°   → Sun-Hora (active wealth, govt, authority)
            15°-30°  → Moon-Hora (passive wealth, public, savings)
        Even signs (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces):
            0°-15°   → Moon-Hora
            15°-30°  → Sun-Hora
    Wealth Karaka Jupiter, Venus, and the dhana-lords falling into a strong
    hora (own hora ⇒ Sun-Hora for Sun, Moon-Hora for Moon, friendly hora
    for benefics) is a strong wealth-promise indicator.
    Returns: {"planets": {<name>: <"Sun-Hora"|"Moon-Hora">},
              "wealth_planets_in_strong_hora": [...]}
    """
    out = {"planets": {}, "wealth_planets_in_strong_hora": []}
    for p in (planets or []):
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        if nm in ("Rahu", "Ketu"):
            continue  # nodes have no hora classification
        s_name = p.get("sign")
        s_idx = _sign_idx(s_name) if s_name else -1
        if s_idx < 0:
            continue
        # planet longitude within sign
        lon = None
        for k in ("degree", "degInSign", "longitudeInSign", "deg"):
            v = p.get(k)
            if isinstance(v, (int, float)) and 0 <= v < 30:
                lon = float(v)
                break
        if lon is None:
            full = _planet_lon(planets, nm)
            if full is None:
                continue
            lon = full % 30.0
        is_odd_sign = (s_idx % 2 == 0)  # 0,2,4,... = Aries, Gemini, ... (odd)
        first_half = lon < 15.0
        if is_odd_sign:
            hora = "Sun-Hora" if first_half else "Moon-Hora"
        else:
            hora = "Moon-Hora" if first_half else "Sun-Hora"
        out["planets"][nm] = hora
    # Wealth karakas in strong hora
    for wp in ("Jupiter", "Venus", "Mercury", "Moon", "Sun"):
        h = out["planets"].get(wp)
        if not h:
            continue
        # Sun is strong in Sun-Hora; Moon strong in Moon-Hora; Jupiter/Venus/
        # Mercury are benefic → Moon-Hora is supportive (passive wealth);
        # but for visible/active wealth Jupiter prefers Sun-Hora as it gives
        # active dharma-money. We accept either as 'strong' for wealth-karma.
        if (wp == "Sun" and h == "Sun-Hora") or \
           (wp == "Moon" and h == "Moon-Hora") or \
           (wp in ("Jupiter", "Venus", "Mercury") and h in ("Sun-Hora", "Moon-Hora")):
            out["wealth_planets_in_strong_hora"].append(f"{wp}({h})")
    return out


def _d11_labha(planets: list, lagna_lon: Optional[float]) -> dict:
    """Compute D11 Labha-amsa chart positions.
    D11 = each 30° sign divided into 11 equal parts of ≈ 2.727° each. The
    11th-from-lagna sign of D11 is the gains-house. We compute the D11 sign
    of every planet and report which planets land in the D11 11H from D11
    lagna — those are the LABHA-RICH planets (gains promise).
    Returns: {"planets": {<name>: <D11 sign>},
              "lagna_sign": <D11 lagna sign>,
              "gains_house_sign": <D11 11H sign>,
              "labha_planets": [planets in D11 11H]}
    """
    out = {"planets": {}, "lagna_sign": None,
           "gains_house_sign": None, "labha_planets": []}

    def _d11_sign_for(absolute_lon: float) -> Optional[str]:
        if not isinstance(absolute_lon, (int, float)):
            return None
        s_idx = int(absolute_lon // 30) % 12
        within = absolute_lon - s_idx * 30
        # Each sign yields 11 amsas of 30/11° starting from same sign
        # for odd signs and from 9th sign for even signs (Brihat Parashara).
        amsa_size = 30.0 / 11.0
        amsa_idx = int(within // amsa_size)
        if amsa_idx > 10:
            amsa_idx = 10
        is_odd_sign = (s_idx % 2 == 0)
        start_sign = s_idx if is_odd_sign else (s_idx + 8) % 12
        d11_idx = (start_sign + amsa_idx) % 12
        return SIGNS[d11_idx]

    if isinstance(lagna_lon, (int, float)):
        out["lagna_sign"] = _d11_sign_for(float(lagna_lon))
    for p in (planets or []):
        if not isinstance(p, dict):
            continue
        nm = p.get("name")
        full = _planet_lon(planets, nm)
        if full is None:
            continue
        sign_d11 = _d11_sign_for(full)
        if sign_d11:
            out["planets"][nm] = sign_d11

    # 11H from D11-lagna sign
    if out["lagna_sign"]:
        try:
            lag_idx = SIGNS.index(out["lagna_sign"])
            gains_idx = (lag_idx + 10) % 12
            out["gains_house_sign"] = SIGNS[gains_idx]
            for nm, sg in out["planets"].items():
                if sg == out["gains_house_sign"]:
                    out["labha_planets"].append(nm)
        except (ValueError, IndexError):
            pass
    return out


def _maybe_d_charts(kundli: dict) -> dict:
    """Return D9, D2 Hora, D11 Labha-amsa overlays for the wealth engine.
    Tries kundli.divisionalCharts first; falls back to inline computation
    using planet longitudes."""
    out = {"D9": {}, "D2": {}, "D11": {}}
    div = kundli.get("divisionalCharts") if isinstance(kundli, dict) else None
    planets = kundli.get("planets") or []
    lagna_lon = kundli.get("ascendantDeg")
    # D9
    if isinstance(div, dict) and isinstance(div.get("D9"), dict):
        out["D9"] = div["D9"]
    else:
        try:
            from divisional import compute_d9  # type: ignore
            out["D9"] = compute_d9(planets, lagna_lon) or {}
        except Exception:
            out["D9"] = {}
    # D2 Hora — always inline (cheap)
    out["D2"] = _d2_hora(planets)
    # D11 Labha — inline (cheap)
    out["D11"] = _d11_labha(planets, lagna_lon)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# DIGNITY + VARGOTTAMA HELPERS  (used by all layers)
# ─────────────────────────────────────────────────────────────────────────────
def _dignity_pts(dignity: Optional[str]) -> int:
    if not dignity:
        return 0
    return DIGNITY_PTS.get(dignity, 0)


def _vargottama(planet_name: str, natal_planets: list,
                varga_planets: list) -> bool:
    """Vargottama = same sign in natal D1 + given divisional chart."""
    n_sign = _planet_sign(natal_planets, planet_name)
    v_sign = _planet_sign(varga_planets, planet_name)
    if not n_sign or not v_sign:
        return False
    return _norm(n_sign) == _norm(v_sign)


# ─────────────────────────────────────────────────────────────────────────────
# A. NATAL PROMISE LAYERS  (L1 – L15)
# ─────────────────────────────────────────────────────────────────────────────

def _layer_second_house(intel: dict, kundli: dict) -> dict:
    """L1 — 2H + 2L deep dive. Saved money / kutumb dhana / family wealth.
    CORE wealth layer. 2H is the PRIMARY accumulated-wealth significator —
    cash savings, jewellery, fixed deposits, family corpus."""
    weight = 16
    score = 0
    why = []
    planets = kundli.get("planets") or []

    second_lord = _house_lord(intel, 2)
    if not second_lord:
        return {"layer": "L1_second_house", "score": 0,
                "why": ["2L unknown"], "weight": weight}

    l2_house = _planet_house(planets, second_lord)
    l2_dignity = _planet_dignity(intel, second_lord)

    # 2L in trikona/kendra/own (2 or 11) = strong saved-money promise
    if l2_house in TRIKONA:
        score += 6
        why.append(f"2L ({second_lord}) in {l2_house}H (trikona) → "
                   f"+6 saved-money promise")
    elif l2_house in (2, 11):
        score += 5
        why.append(f"2L ({second_lord}) in {l2_house}H (own/labha) → "
                   f"+5 saved-money promise")
    elif l2_house in KENDRA:
        score += 3
        why.append(f"2L ({second_lord}) in {l2_house}H (kendra) → +3")
    elif l2_house in DUSHTANA:
        # 2L in dushtana = weakness in saved-money UNLESS 6/8/12 exchange
        # creates Vipareeta-Raja yoga (handled in L23).
        score -= 4
        why.append(f"2L ({second_lord}) in {l2_house}H (dushtana) → "
                   f"−4 saved-money leak (check Vipareeta-Raja)")

    # Dignity of 2L
    dp = _dignity_pts(l2_dignity)
    if dp:
        score += dp
        why.append(f"2L ({second_lord}) {l2_dignity} → {dp:+d}")

    # Combust / Retrograde of 2L
    if _is_combust(planets, second_lord):
        score -= 3
        why.append(f"2L ({second_lord}) combust → −3")
    if _is_retrograde(planets, second_lord):
        # Retro 2L = re-saving / repeat income; mildly positive for wealth
        score += 1
        why.append(f"2L ({second_lord}) retrograde → +1 (re-saving)")

    # Planets in 2H — benefics support saved-money
    pl_in_2 = [p["name"] for p in planets
               if isinstance(p, dict) and p.get("house") == 2
               and p.get("name") in (NATURAL_BENEFICS | NATURAL_MALEFICS)]
    benefics_in_2 = [p for p in pl_in_2 if p in NATURAL_BENEFICS]
    malefics_in_2 = [p for p in pl_in_2 if p in NATURAL_MALEFICS]
    if "Jupiter" in benefics_in_2:
        score += 4
        why.append("Jupiter in 2H → +4 dhana-karaka in own seat")
    if "Venus" in benefics_in_2 and "Jupiter" not in benefics_in_2:
        score += 3
        why.append("Venus in 2H → +3 luxury saved-wealth")
    if benefics_in_2 and "Jupiter" not in benefics_in_2:
        score += 2 * (len(benefics_in_2) - (1 if "Venus" in benefics_in_2 else 0))
        if score > 0 and len(benefics_in_2) > 1:
            why.append(f"Other benefics in 2H: {','.join(benefics_in_2)}")
    if malefics_in_2:
        if "Saturn" in malefics_in_2:
            # Saturn in 2H = slow but steady; not always negative
            score -= 1
            why.append("Saturn in 2H → −1 (slow saved-money, "
                       "possible family-burden)")
        if "Mars" in malefics_in_2:
            score -= 3
            why.append("Mars in 2H → −3 (kutumb dispute / sudden expense)")
        if "Rahu" in malefics_in_2:
            score -= 2
            why.append("Rahu in 2H → −2 (unconventional / risky savings)")
        if "Ketu" in malefics_in_2:
            score -= 2
            why.append("Ketu in 2H → −2 (detached from saved-money)")

    # Aspects on 2H
    aspecting = _planets_aspecting_house(planets, 2)
    if "Jupiter" in aspecting:
        score += 3
        why.append("Jupiter aspects 2H → +3 dhana-karaka grace")
    if "Saturn" in aspecting and "Jupiter" not in aspecting:
        score -= 2
        why.append("Saturn aspects 2H → −2 saved-money pressure")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L1_second_house", "score": score, "weight": weight,
        "why": why,
        "second_lord": second_lord, "l2_house": l2_house,
        "l2_dignity": l2_dignity,
    }


def _layer_eleventh_house(intel: dict, kundli: dict) -> dict:
    """L2 — 11H + 11L deep dive. Gains / income / labha. CORE.

    11H is the PRIMARY income/gains significator — salary, business profit,
    fulfilment of desires. Strong 11H = consistent income inflow. Strong 11L
    placed well = the gains-promise has a vehicle."""
    weight = 16
    score = 0
    why = []
    planets = kundli.get("planets") or []

    eleventh_lord = _house_lord(intel, 11)
    if not eleventh_lord:
        return {"layer": "L2_eleventh_house", "score": 0,
                "why": ["11L unknown"], "weight": weight}

    l11_house = _planet_house(planets, eleventh_lord)
    l11_dignity = _planet_dignity(intel, eleventh_lord)

    if l11_house in TRIKONA:
        score += 6
        why.append(f"11L ({eleventh_lord}) in {l11_house}H (trikona) → "
                   f"+6 income promise (laxmi-bhagya yoga support)")
    elif l11_house in (2, 11):
        score += 5
        why.append(f"11L ({eleventh_lord}) in {l11_house}H → +5 own labha-stana")
    elif l11_house in KENDRA:
        score += 3
        why.append(f"11L ({eleventh_lord}) in {l11_house}H (kendra) → +3")
    elif l11_house in DUSHTANA:
        score -= 4
        why.append(f"11L ({eleventh_lord}) in {l11_house}H (dushtana) → "
                   f"−4 gains-leak (check Vipareeta-Raja)")

    dp = _dignity_pts(l11_dignity)
    if dp:
        score += dp
        why.append(f"11L ({eleventh_lord}) {l11_dignity} → {dp:+d}")

    if _is_combust(planets, eleventh_lord):
        score -= 3
        why.append(f"11L ({eleventh_lord}) combust → −3 income obscured")
    if _is_retrograde(planets, eleventh_lord):
        score += 2
        why.append(f"11L ({eleventh_lord}) retro → +2 (recurring income)")

    pl_in_11 = [p["name"] for p in planets
                if isinstance(p, dict) and p.get("house") == 11]
    # ANY planet in 11H is generally positive (Vedic principle: labha-bhava
    # is the only house where every planet — even malefics — gives gains).
    if pl_in_11:
        natural_kins_in_11 = [p for p in pl_in_11
                              if p in (NATURAL_BENEFICS | NATURAL_MALEFICS)]
        score += min(6, 2 * len(natural_kins_in_11))
        why.append(f"{len(natural_kins_in_11)} planet(s) in 11H "
                   f"({','.join(natural_kins_in_11)}) → "
                   f"+{min(6, 2 * len(natural_kins_in_11))} "
                   f"(every planet gives in labha)")
        # Jupiter in 11H = exceptionally strong dhana yoga
        if "Jupiter" in pl_in_11:
            score += 2
            why.append("Jupiter in 11H → +2 maha-dhana-yoga component")

    aspecting_11 = _planets_aspecting_house(planets, 11)
    if "Jupiter" in aspecting_11:
        score += 3
        why.append("Jupiter aspects 11H → +3 gains amplification")
    # Even Saturn aspect on 11H is supportive (own house for Saturn is 11)
    if "Saturn" in aspecting_11:
        score += 2
        why.append("Saturn aspects 11H (own house) → +2 sustained labha")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L2_eleventh_house", "score": score, "weight": weight,
        "why": why,
        "eleventh_lord": eleventh_lord, "l11_house": l11_house,
        "l11_dignity": l11_dignity,
    }


def _layer_fifth_house(intel: dict, kundli: dict) -> dict:
    """L3 — 5H + 5L. Poorva-punya / past-life merit / sudden / speculative
    gains, intelligence-based income, children-related wealth."""
    weight = 10
    score = 0
    why = []
    planets = kundli.get("planets") or []

    fifth_lord = _house_lord(intel, 5)
    if not fifth_lord:
        return {"layer": "L3_fifth_house", "score": 0,
                "why": ["5L unknown"], "weight": weight}

    l5_house = _planet_house(planets, fifth_lord)
    l5_dignity = _planet_dignity(intel, fifth_lord)

    if l5_house in TRIKONA or l5_house in (2, 11):
        score += 4
        why.append(f"5L ({fifth_lord}) in {l5_house}H → "
                   f"+4 poorva-punya activates wealth")
    elif l5_house in KENDRA:
        score += 2
        why.append(f"5L ({fifth_lord}) in {l5_house}H (kendra) → +2")
    elif l5_house in DUSHTANA:
        score -= 3
        why.append(f"5L ({fifth_lord}) in {l5_house}H (dushtana) → "
                   f"−3 poorva-punya blocked")

    dp = _dignity_pts(l5_dignity)
    if dp:
        score += dp // 2
        why.append(f"5L ({fifth_lord}) {l5_dignity} → {dp // 2:+d}")

    pl_in_5 = [p["name"] for p in planets
               if isinstance(p, dict) and p.get("house") == 5]
    benefics_in_5 = [p for p in pl_in_5 if p in NATURAL_BENEFICS]
    if "Jupiter" in benefics_in_5:
        score += 3
        why.append("Jupiter in 5H → +3 sudden-gain via wisdom")
    if "Venus" in benefics_in_5:
        score += 2
        why.append("Venus in 5H → +2 creative-income / gaming")
    if "Rahu" in pl_in_5:
        # Rahu in 5H = speculative gains BUT erratic
        score += 1
        why.append("Rahu in 5H → +1 (speculative gain potential, erratic)")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L3_fifth_house", "score": score, "weight": weight,
        "why": why, "fifth_lord": fifth_lord, "l5_house": l5_house,
    }


def _layer_ninth_house(intel: dict, kundli: dict) -> dict:
    """L4 — 9H + 9L. Bhagya / fortune / dharmic wealth / father's wealth /
    higher learning income."""
    weight = 10
    score = 0
    why = []
    planets = kundli.get("planets") or []

    ninth_lord = _house_lord(intel, 9)
    if not ninth_lord:
        return {"layer": "L4_ninth_house", "score": 0,
                "why": ["9L unknown"], "weight": weight}

    l9_house = _planet_house(planets, ninth_lord)
    l9_dignity = _planet_dignity(intel, ninth_lord)

    if l9_house in TRIKONA or l9_house in (2, 11):
        score += 5
        why.append(f"9L ({ninth_lord}) in {l9_house}H → "
                   f"+5 bhagya activates wealth")
    elif l9_house in KENDRA:
        score += 3
        why.append(f"9L ({ninth_lord}) in {l9_house}H (kendra) → +3 bhagya")
    elif l9_house in DUSHTANA:
        score -= 3
        why.append(f"9L ({ninth_lord}) in {l9_house}H (dushtana) → "
                   f"−3 bhagya blocked")

    dp = _dignity_pts(l9_dignity)
    if dp:
        score += dp // 2
        why.append(f"9L ({ninth_lord}) {l9_dignity} → {dp // 2:+d}")

    pl_in_9 = [p["name"] for p in planets
               if isinstance(p, dict) and p.get("house") == 9]
    if "Jupiter" in pl_in_9:
        score += 4
        why.append("Jupiter in 9H → +4 (Jupiter in own/dharma house)")
    if "Sun" in pl_in_9:
        score += 1
        why.append("Sun in 9H → +1 (paternal-bhagya support)")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L4_ninth_house", "score": score, "weight": weight,
        "why": why, "ninth_lord": ninth_lord, "l9_house": l9_house,
    }


def _layer_fourth_house(intel: dict, kundli: dict) -> dict:
    """L5 — 4H + 4L. Property / vehicle / fixed assets / mother's wealth /
    domestic comfort."""
    weight = 8
    score = 0
    why = []
    planets = kundli.get("planets") or []

    fourth_lord = _house_lord(intel, 4)
    if not fourth_lord:
        return {"layer": "L5_fourth_house", "score": 0,
                "why": ["4L unknown"], "weight": weight}

    l4_house = _planet_house(planets, fourth_lord)
    l4_dignity = _planet_dignity(intel, fourth_lord)

    if l4_house in (TRIKONA | KENDRA | {2, 11}):
        score += 4
        why.append(f"4L ({fourth_lord}) in {l4_house}H → "
                   f"+4 property/comfort promise")
    elif l4_house in DUSHTANA:
        score -= 3
        why.append(f"4L ({fourth_lord}) in {l4_house}H (dushtana) → −3")

    dp = _dignity_pts(l4_dignity)
    if dp:
        score += dp // 2
        why.append(f"4L ({fourth_lord}) {l4_dignity} → {dp // 2:+d}")

    pl_in_4 = [p["name"] for p in planets
               if isinstance(p, dict) and p.get("house") == 4]
    if "Venus" in pl_in_4:
        score += 2
        why.append("Venus in 4H → +2 (luxury-comfort, vehicles)")
    if "Mars" in pl_in_4:
        score -= 2
        why.append("Mars in 4H → −2 (property dispute / domestic friction)")
    if "Moon" in pl_in_4:
        score += 2
        why.append("Moon in 4H → +2 (Moon in own bhava — comfort)")
    if "Saturn" in pl_in_4:
        score -= 1
        why.append("Saturn in 4H → −1 (delayed property acquisition)")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L5_fourth_house", "score": score, "weight": weight,
        "why": why, "fourth_lord": fourth_lord, "l4_house": l4_house,
    }


def _layer_eighth_house_wealth(intel: dict, kundli: dict) -> dict:
    """L6 — 8H + 8L. Inheritance / joint funds / spouse's wealth / hidden
    money / sudden financial events. Mixed signature: 8H is dushtana
    classically but Jupiter / Saturn here can give sustained inheritance
    timing and Vipareeta-Raja-Yoga (handled in L23)."""
    weight = 6
    score = 0
    why = []
    planets = kundli.get("planets") or []

    eighth_lord = _house_lord(intel, 8)
    if not eighth_lord:
        return {"layer": "L6_eighth_house_wealth", "score": 0,
                "why": ["8L unknown"], "weight": weight}

    l8_house = _planet_house(planets, eighth_lord)
    l8_dignity = _planet_dignity(intel, eighth_lord)

    # 8L in dushtana from itself (i.e. 6H or 12H) = Vipareeta-Raja-Yoga
    # giver = wealth via crisis-resolution.
    if l8_house in (6, 12):
        score += 4
        why.append(f"8L ({eighth_lord}) in {l8_house}H → +4 "
                   f"Vipareeta-Raja-Yoga component (wealth via crisis)")
    elif l8_house in (2, 11):
        score += 3
        why.append(f"8L ({eighth_lord}) in {l8_house}H → +3 "
                   f"(inheritance flows into dhana/labha)")
    elif l8_house in TRIKONA:
        score += 1
        why.append(f"8L ({eighth_lord}) in {l8_house}H → +1")
    elif l8_house in KENDRA and l8_house != 1:
        score += 1
        why.append(f"8L ({eighth_lord}) in {l8_house}H (kendra) → +1")

    pl_in_8 = [p["name"] for p in planets
               if isinstance(p, dict) and p.get("house") == 8]
    if "Jupiter" in pl_in_8:
        score += 2
        why.append("Jupiter in 8H → +2 (sustained inheritance / "
                   "research-based hidden gains)")
    if "Venus" in pl_in_8:
        score -= 1
        why.append("Venus in 8H → −1 (luxury wasted in dushtana)")
    if "Rahu" in pl_in_8:
        score += 1
        why.append("Rahu in 8H → +1 (sudden windfall potential)")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L6_eighth_house_wealth", "score": score, "weight": weight,
        "why": why, "eighth_lord": eighth_lord, "l8_house": l8_house,
    }


def _layer_twelfth_house_wealth(intel: dict, kundli: dict) -> dict:
    """L7 — 12H + 12L. Expenses / loss / foreign income / charity. Strong
    12L in dhana houses = foreign-source income; weak 12L = expense leak."""
    weight = 6
    score = 0
    why = []
    planets = kundli.get("planets") or []

    twelfth_lord = _house_lord(intel, 12)
    if not twelfth_lord:
        return {"layer": "L7_twelfth_house_wealth", "score": 0,
                "why": ["12L unknown"], "weight": weight}

    l12_house = _planet_house(planets, twelfth_lord)
    l12_dignity = _planet_dignity(intel, twelfth_lord)

    # 12L in 11H or 2H = foreign-source income (gain from abroad)
    if l12_house == 11:
        score += 4
        why.append(f"12L ({twelfth_lord}) in 11H → +4 foreign-income yoga")
    elif l12_house == 2:
        score += 3
        why.append(f"12L ({twelfth_lord}) in 2H → +3 expense converts to "
                   f"saved-money (charity/saving cycle)")
    elif l12_house in (6, 8):
        # 12L in 6/8 = Vipareeta-style cancellation (good)
        score += 2
        why.append(f"12L ({twelfth_lord}) in {l12_house}H → +2 "
                   f"(loss-of-loss cancellation)")
    elif l12_house in (1, 5, 9):
        score -= 3
        why.append(f"12L ({twelfth_lord}) in {l12_house}H → "
                   f"−3 expense affects body/punya/bhagya")

    pl_in_12 = [p["name"] for p in planets
                if isinstance(p, dict) and p.get("house") == 12]
    if "Saturn" in pl_in_12:
        score -= 1
        why.append("Saturn in 12H → −1 (chronic expense pressure)")
    if "Rahu" in pl_in_12:
        score += 2
        why.append("Rahu in 12H → +2 foreign-source / unconventional income")
    if "Venus" in pl_in_12:
        score += 1
        why.append("Venus in 12H → +1 (Venus in own house — comforts in bed/"
                   "foreign luxuries)")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L7_twelfth_house_wealth", "score": score, "weight": weight,
        "why": why, "twelfth_lord": twelfth_lord, "l12_house": l12_house,
    }


def _layer_sixth_house_wealth(intel: dict, kundli: dict) -> dict:
    """L8 — 6H + 6L. Loans / EMI / debts / disputes / daily-grind income.
    CORE-NEG layer for wealth: a strong 6H = strong debt-management AND
    strong service-income; a weak/afflicted 6H pressing 2H/11H = wealth
    leak via unpaid loans. Net score is calibrated so that VIPAREETA pattern
    on 6L (i.e. 6L in 8/12) gives a positive — wealth from debt-resolution
    work."""
    weight = 8
    score = 0
    why = []
    planets = kundli.get("planets") or []

    sixth_lord = _house_lord(intel, 6)
    if not sixth_lord:
        return {"layer": "L8_sixth_house_wealth", "score": 0,
                "why": ["6L unknown"], "weight": weight}

    l6_house = _planet_house(planets, sixth_lord)
    l6_dignity = _planet_dignity(intel, sixth_lord)

    # 6L in dushtana (8H or 12H) = Vipareeta cancellation (wealth from
    # debt-resolution / service businesses)
    if l6_house in (8, 12):
        score += 5
        why.append(f"6L ({sixth_lord}) in {l6_house}H → +5 "
                   f"Vipareeta-Raja-Yoga (debt cancels itself)")
    elif l6_house == 6:
        # 6L in own house = strong loan-management AND strong daily income
        score += 3
        why.append(f"6L ({sixth_lord}) in 6H (own) → +3 (controlled debt, "
                   f"strong service income)")
    elif l6_house in (2, 11):
        # 6L in dhana houses = debt seeking out money (NEG)
        score -= 4
        why.append(f"6L ({sixth_lord}) in {l6_house}H → −4 "
                   f"(debt drains saved-money / income)")
    elif l6_house in TRIKONA:
        score -= 3
        why.append(f"6L ({sixth_lord}) in {l6_house}H (trikona) → "
                   f"−3 (debt attaches to bhagya/punya)")

    # Aspects from 6L on 2H / 11H
    if l6_house and isinstance(l6_house, int):
        sixth_lord_aspects = _aspect_houses(sixth_lord, l6_house)
        if 2 in sixth_lord_aspects or 11 in sixth_lord_aspects:
            score -= 2
            why.append(f"6L ({sixth_lord}) aspects 2H/11H → −2 "
                       f"(debt pressure on dhana)")

    pl_in_6 = [p["name"] for p in planets
               if isinstance(p, dict) and p.get("house") == 6]
    # Saturn / Mars / Rahu in 6H = STRONG against debt/enemies (own house)
    if "Saturn" in pl_in_6:
        score += 3
        why.append("Saturn in 6H → +3 (Saturn in own house — controlled debt)")
    if "Mars" in pl_in_6:
        score += 2
        why.append("Mars in 6H → +2 (Mars in own house — wins debt disputes)")
    if "Jupiter" in pl_in_6:
        score -= 2
        why.append("Jupiter in 6H → −2 (Jupiter wasted in dushtana, "
                   "expanding debts)")
    if "Venus" in pl_in_6:
        score -= 1
        why.append("Venus in 6H → −1 (luxury expenses become debt)")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L8_sixth_house_wealth", "score": score, "weight": weight,
        "why": why,
        "sixth_lord": sixth_lord, "l6_house": l6_house,
        "l6_dignity": l6_dignity,
    }


def _layer_jupiter_dhana_karaka(intel: dict, kundli: dict) -> dict:
    """L9 — Jupiter as PRIMARY dhana karaka. MANDATORY layer.
    Jupiter is the natural significator of wealth, wisdom, dharma, savings,
    children, expansion. Strong well-placed Jupiter = the entire wealth
    pattern has dharmic fuel. Afflicted Jupiter = wealth comes with conflict /
    moral compromise / loss."""
    weight = 12
    score = 0
    why = []
    planets = kundli.get("planets") or []

    jup_house = _planet_house(planets, "Jupiter")
    jup_dignity = _planet_dignity(intel, "Jupiter")
    jup_sign = _planet_sign(planets, "Jupiter")

    if jup_house is None:
        return {"layer": "L9_jupiter_dhana_karaka", "score": 0,
                "why": ["Jupiter house unknown"], "weight": weight}

    # House placement
    if jup_house in (TRIKONA | {2, 5, 9, 11}):
        score += 6
        why.append(f"Jupiter in {jup_house}H (dhana/trikona) → "
                   f"+6 dhana-karaka activated")
    elif jup_house in KENDRA:
        score += 4
        why.append(f"Jupiter in {jup_house}H (kendra) → +4 dhana-grace")
    elif jup_house in DUSHTANA:
        if jup_house == 8:
            # Jupiter in 8 is mixed (research/inheritance) — handled in L6
            score -= 1
            why.append("Jupiter in 8H → −1 (wealth via research/legacy delays)")
        else:
            score -= 3
            why.append(f"Jupiter in {jup_house}H (dushtana) → "
                       f"−3 dhana-karaka stressed")

    # Dignity
    dp = _dignity_pts(jup_dignity)
    if dp:
        score += dp // 2
        why.append(f"Jupiter {jup_dignity} → {dp // 2:+d}")

    # Combust / Retro
    if _is_combust(planets, "Jupiter"):
        score -= 3
        why.append("Jupiter combust → −3 (dhana-karaka obscured by Sun)")
    if _is_retrograde(planets, "Jupiter"):
        score += 2
        why.append("Jupiter retrograde → +2 (deeper dharmic-wealth karma)")

    # Aspects: Jupiter aspects 2H or 11H from anywhere = strong support
    jup_aspects = _aspect_houses("Jupiter", jup_house)
    boost_houses = jup_aspects & {2, 5, 9, 11}
    if boost_houses:
        score += 3
        why.append(f"Jupiter aspects {sorted(boost_houses)} → "
                   f"+3 dhana houses graced")

    # Conjunctions
    jup_conj = [p["name"] for p in planets
                if isinstance(p, dict) and p.get("house") == jup_house
                and p.get("name") != "Jupiter"
                and p.get("name") in (NATURAL_BENEFICS | NATURAL_MALEFICS)]
    if "Venus" in jup_conj:
        # Guru-Shukra conjunction = controversial (rivals) but for wealth
        # the combined benefic energy is mildly positive UNLESS in dushtana.
        if jup_house not in DUSHTANA:
            score += 1
            why.append("Jupiter-Venus conjunction (out of dushtana) → +1 "
                       "luxury+wisdom synergy")
    if "Saturn" in jup_conj:
        score -= 1
        why.append("Jupiter-Saturn conjunction → −1 "
                   "(slow expansion, conservative wealth)")
    if "Rahu" in jup_conj:
        score -= 2
        why.append("Jupiter-Rahu conjunction (Guru-Chandala) → −2 "
                   "(unethical-wealth temptation)")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L9_jupiter_dhana_karaka", "score": score, "weight": weight,
        "why": why,
        "jup_house": jup_house, "jup_sign": jup_sign,
        "jup_dignity": jup_dignity,
    }


def _layer_venus_luxury(intel: dict, kundli: dict) -> dict:
    """L10 — Venus as luxury / vehicles / partnerships / creative-arts
    income karaka."""
    weight = 6
    score = 0
    why = []
    planets = kundli.get("planets") or []

    ven_house = _planet_house(planets, "Venus")
    ven_dignity = _planet_dignity(intel, "Venus")
    if ven_house is None:
        return {"layer": "L10_venus_luxury", "score": 0,
                "why": ["Venus house unknown"], "weight": weight}

    if ven_house in (TRIKONA | KENDRA | {2, 11}):
        score += 3
        why.append(f"Venus in {ven_house}H → +3 luxury-income promise")
    elif ven_house in DUSHTANA:
        score -= 2
        why.append(f"Venus in {ven_house}H (dushtana) → −2 luxury blocked")

    dp = _dignity_pts(ven_dignity)
    if dp:
        score += dp // 2
        why.append(f"Venus {ven_dignity} → {dp // 2:+d}")

    if _is_combust(planets, "Venus"):
        score -= 2
        why.append("Venus combust → −2")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L10_venus_luxury", "score": score, "weight": weight,
        "why": why, "ven_house": ven_house, "ven_dignity": ven_dignity,
    }


def _layer_mercury_business(intel: dict, kundli: dict) -> dict:
    """L11 — Mercury as business / trade / commerce / IP-income karaka."""
    weight = 6
    score = 0
    why = []
    planets = kundli.get("planets") or []

    mer_house = _planet_house(planets, "Mercury")
    mer_dignity = _planet_dignity(intel, "Mercury")
    if mer_house is None:
        return {"layer": "L11_mercury_business", "score": 0,
                "why": ["Mercury house unknown"], "weight": weight}

    if mer_house in (TRIKONA | KENDRA | {2, 11}):
        score += 3
        why.append(f"Mercury in {mer_house}H → +3 business-income promise")
    elif mer_house in DUSHTANA:
        if mer_house == 6:
            # Mercury in 6 = own house → service business strength
            score += 2
            why.append("Mercury in 6H (own) → +2 service-business strength")
        else:
            score -= 2
            why.append(f"Mercury in {mer_house}H (dushtana) → −2")

    dp = _dignity_pts(mer_dignity)
    if dp:
        score += dp // 2
        why.append(f"Mercury {mer_dignity} → {dp // 2:+d}")

    if _is_combust(planets, "Mercury"):
        score -= 2
        why.append("Mercury combust → −2 (business communication obscured)")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L11_mercury_business", "score": score, "weight": weight,
        "why": why, "mer_house": mer_house, "mer_dignity": mer_dignity,
    }


def _layer_moon_cashflow(intel: dict, kundli: dict) -> dict:
    """L12 — Moon as cash-flow / liquidity / public-facing income karaka."""
    weight = 5
    score = 0
    why = []
    planets = kundli.get("planets") or []

    moon_house = _planet_house(planets, "Moon")
    moon_dignity = _planet_dignity(intel, "Moon")
    if moon_house is None:
        return {"layer": "L12_moon_cashflow", "score": 0,
                "why": ["Moon house unknown"], "weight": weight}

    if moon_house in (TRIKONA | KENDRA | {2, 11}):
        score += 3
        why.append(f"Moon in {moon_house}H → +3 cash-flow promise")
    elif moon_house in DUSHTANA:
        score -= 2
        why.append(f"Moon in {moon_house}H (dushtana) → −2 liquidity stress")

    dp = _dignity_pts(moon_dignity)
    if dp:
        score += dp // 2
        why.append(f"Moon {moon_dignity} → {dp // 2:+d}")

    # Kemadruma check (no planet in 2nd or 12th from Moon, except nodes/Sun)
    moon_h = moon_house
    second_from_moon = ((moon_h - 1 + 1) % 12) + 1
    twelfth_from_moon = ((moon_h - 1 - 1) % 12) + 1
    has_neighbour = False
    for p in planets:
        if not isinstance(p, dict):
            continue
        if p.get("name") in ("Moon", "Sun", "Rahu", "Ketu"):
            continue
        if p.get("house") in (second_from_moon, twelfth_from_moon):
            has_neighbour = True
            break
    if not has_neighbour:
        score -= 2
        why.append("Kemadruma yoga (Moon isolated) → −2 cash-flow erratic")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L12_moon_cashflow", "score": score, "weight": weight,
        "why": why, "moon_house": moon_house,
    }


def _layer_sun_authority_income(intel: dict, kundli: dict) -> dict:
    """L13 — Sun as govt / authority / salary-recognition income karaka."""
    weight = 5
    score = 0
    why = []
    planets = kundli.get("planets") or []

    sun_house = _planet_house(planets, "Sun")
    sun_dignity = _planet_dignity(intel, "Sun")
    if sun_house is None:
        return {"layer": "L13_sun_authority_income", "score": 0,
                "why": ["Sun house unknown"], "weight": weight}

    if sun_house in (10, 11, 1, 5, 9):
        score += 3
        why.append(f"Sun in {sun_house}H → +3 govt/authority-income promise")
    elif sun_house in DUSHTANA:
        score -= 2
        why.append(f"Sun in {sun_house}H → −2 authority-income blocked")

    dp = _dignity_pts(sun_dignity)
    if dp:
        score += dp // 2
        why.append(f"Sun {sun_dignity} → {dp // 2:+d}")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L13_sun_authority_income", "score": score, "weight": weight,
        "why": why, "sun_house": sun_house,
    }


def _layer_jaimini_dhana_karaka(karakas_d: dict, intel: dict,
                                kundli: dict) -> dict:
    """L14 — Jaimini Atmakaraka (AK) + Amatyakaraka (AmK) + Bhratri-karaka
    (BK) cluster for wealth significance. MANDATORY.

    In Jaimini system the `Dhana Karaka` is colloquially identified with the
    BK (income/effort significator) but the canonical wealth-cluster reading
    uses AK (soul-direction of wealth karma) + AmK (mind-strategy of how
    money is earned) + BK. We score this triplet by summing dignity + house
    placement of all three relative to wealth houses {2, 5, 9, 11}."""
    weight = 10
    score = 0
    why = []
    if not karakas_d:
        return {"layer": "L14_jaimini_dhana_karaka", "score": 0,
                "why": ["karakas unavailable"], "weight": weight}

    planets = kundli.get("planets") or []
    triplet = []
    for role in ("AK", "AmK", "BK"):
        node = karakas_d.get(role) or karakas_d.get(
            {"AK": "Atmakaraka", "AmK": "Amatyakaraka", "BK": "Bhratrikaraka"}
            .get(role, "")) or {}
        if isinstance(node, dict):
            pl = node.get("planet") or node.get("name")
        else:
            pl = node
        if pl:
            triplet.append((role, pl))

    if not triplet:
        return {"layer": "L14_jaimini_dhana_karaka", "score": 0,
                "why": ["AK/AmK/BK not identified"], "weight": weight}

    for role, pl in triplet:
        h = _planet_house(planets, pl)
        d = _planet_dignity(intel, pl)
        if h in {2, 5, 9, 11}:
            score += 2
            why.append(f"{role} ({pl}) in {h}H (dhana house) → +2")
        elif h in KENDRA:
            score += 1
            why.append(f"{role} ({pl}) in {h}H (kendra) → +1")
        elif h in (6, 8, 12):
            score -= 2
            why.append(f"{role} ({pl}) in {h}H (dushtana) → −2")

        dp = _dignity_pts(d)
        if dp:
            score += dp // 3
            why.append(f"{role} ({pl}) {d} → {dp // 3:+d}")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L14_jaimini_dhana_karaka", "score": score, "weight": weight,
        "why": why,
        "triplet": [(r, p) for r, p in triplet],
    }


def _layer_lagna_bhava_aspect_wealth(intel: dict, kundli: dict) -> dict:
    """L15 — Lagna-Bhava cross-aspect for wealth. How planets in
    1/2/11 cross-aspect each other and the 2H/11H axis."""
    weight = 4
    score = 0
    why = []
    planets = kundli.get("planets") or []

    pl_in_2 = [p["name"] for p in planets
               if isinstance(p, dict) and p.get("house") == 2]
    pl_in_11 = [p["name"] for p in planets
                if isinstance(p, dict) and p.get("house") == 11]
    # 2H ↔ 8H opposition
    pl_in_8 = [p["name"] for p in planets
               if isinstance(p, dict) and p.get("house") == 8]
    if pl_in_2 and pl_in_8:
        if any(n in NATURAL_MALEFICS for n in pl_in_8):
            score -= 2
            why.append("Malefic in 8H aspects 2H → −2 saved-money pressure")

    # 5H ↔ 11H axis (poorva-punya ↔ labha) — benefics on either side amplify
    pl_in_5 = [p["name"] for p in planets
               if isinstance(p, dict) and p.get("house") == 5]
    if (any(p in NATURAL_BENEFICS for p in pl_in_5) and
            any(p in NATURAL_BENEFICS for p in pl_in_11)):
        score += 2
        why.append("Benefics on 5/11 axis → +2 punya-labha harmony")

    # Mutual 2H ↔ 11H exchange (handled fully in M6 Parivartana modifier;
    # we only note presence here)
    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)
    if second_lord and eleventh_lord:
        l2h = _planet_house(planets, second_lord)
        l11h = _planet_house(planets, eleventh_lord)
        if l2h == 11 and l11h == 2:
            score += 3
            why.append(f"2L↔11L Parivartana ({second_lord}↔{eleventh_lord}) "
                       f"detected → +3 (full credit in M6)")

    if not why:
        why.append("No major lagna-bhava cross-aspect for wealth")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L15_lagna_bhava_aspect_wealth", "score": score,
        "weight": weight, "why": why,
    }


# ─────────────────────────────────────────────────────────────────────────────
# B. DIVISIONAL + KP LAYERS  (L16 – L19)
# ─────────────────────────────────────────────────────────────────────────────

def _layer_d9_overlay_wealth(kundli: dict, intel: dict,
                             karakas_d: dict) -> dict:
    """L16 — D9 Navamsa overlay for wealth. Sustained wealth cross-check.
    Jupiter / 2L / 11L vargottama in D9 = sustained dhana promise."""
    weight = 10
    score = 0
    why = []
    dc = _maybe_d_charts(kundli)
    d9 = dc.get("D9") or []
    if not d9:
        return {"layer": "L16_d9_overlay_wealth", "score": 0,
                "why": ["D9 unavailable"], "weight": weight}

    natal = kundli.get("planets") or []
    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)

    # Jupiter vargottama
    if _vargottama("Jupiter", natal, d9):
        score += 4
        why.append("Jupiter vargottama in D9 → +4 sustained dhana karaka")
    # 2L vargottama
    if second_lord and _vargottama(second_lord, natal, d9):
        score += 3
        why.append(f"2L ({second_lord}) vargottama in D9 → "
                   f"+3 sustained saved-money")
    # 11L vargottama
    if eleventh_lord and _vargottama(eleventh_lord, natal, d9):
        score += 3
        why.append(f"11L ({eleventh_lord}) vargottama in D9 → "
                   f"+3 sustained gains")

    # AK in D9 — soul-aligned wealth
    ak = karakas_d.get("AK") or karakas_d.get("Atmakaraka") or {}
    ak_planet = ak.get("planet") if isinstance(ak, dict) else ak
    if ak_planet and _vargottama(ak_planet, natal, d9):
        score += 2
        why.append(f"AK ({ak_planet}) vargottama in D9 → +2")

    # Jupiter in D9 — sign quality
    d9_jup_sign = _planet_sign(d9, "Jupiter")
    if d9_jup_sign:
        ldn = SIGN_LORDS.get(_norm(d9_jup_sign))
        if ldn == "Jupiter":
            score += 2
            why.append("Jupiter in own sign in D9 → +2")
        elif ldn in NATURAL_BENEFICS:
            score += 1
            why.append(f"Jupiter in benefic sign of {ldn} in D9 → +1")
        elif ldn in NATURAL_MALEFICS:
            score -= 1
            why.append(f"Jupiter in malefic sign of {ldn} in D9 → −1")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L16_d9_overlay_wealth", "score": score, "weight": weight,
        "why": why,
    }


def _layer_d2_hora_overlay(kundli: dict, intel: dict) -> dict:
    """L17 — D2 Hora overlay. THE wealth D-chart. MANDATORY.

    D2 Hora classifies every planet into Sun-Hora (active, govt, authority
    wealth) or Moon-Hora (passive, public, family-savings wealth). Wealth
    karakas (Jupiter, Venus, Mercury, Moon, Sun) falling into a strong
    hora gives sustained wealth promise. Lagnesh + 2L + 11L hora is the
    most sensitive readout.
    """
    weight = 14
    score = 0
    why = []
    dc = _maybe_d_charts(kundli)
    d2 = dc.get("D2") or {}
    if not d2 or not d2.get("planets"):
        return {"layer": "L17_d2_hora_overlay", "score": 0,
                "why": ["D2 Hora unavailable"], "weight": weight}

    horas = d2.get("planets") or {}
    strong = d2.get("wealth_planets_in_strong_hora") or []
    if strong:
        score += min(8, 2 * len(strong))
        why.append(f"Wealth planets in strong hora: "
                   f"{','.join(strong)} → +{min(8, 2 * len(strong))}")

    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)
    lagnesh = _house_lord(intel, 1)

    for role, lord in (("Lagnesh", lagnesh), ("2L", second_lord),
                       ("11L", eleventh_lord)):
        if not lord:
            continue
        h = horas.get(lord)
        if not h:
            continue
        # Sun-Hora gives "active money" energy; Moon-Hora gives "saved money"
        # energy. For wealth purposes both are supportive but skewed:
        #   2L  prefers Moon-Hora (savings nature)
        #   11L prefers Sun-Hora (income / inflow nature)
        if role == "2L" and h == "Moon-Hora":
            score += 3
            why.append(f"2L ({lord}) in Moon-Hora → +3 (savings flavour)")
        elif role == "2L" and h == "Sun-Hora":
            score += 1
            why.append(f"2L ({lord}) in Sun-Hora → +1 (active saved-money)")
        elif role == "11L" and h == "Sun-Hora":
            score += 3
            why.append(f"11L ({lord}) in Sun-Hora → +3 (active income flow)")
        elif role == "11L" and h == "Moon-Hora":
            score += 1
            why.append(f"11L ({lord}) in Moon-Hora → +1 (passive income)")
        elif role == "Lagnesh":
            score += 1
            why.append(f"Lagnesh ({lord}) in {h} → +1 (wealth-self karma)")

    # Jupiter hora → mandatory mention (dhana karaka)
    jh = horas.get("Jupiter")
    if jh:
        # Jupiter in either hora is positive — Sun-Hora = active dharmic
        # earning; Moon-Hora = passive blessings
        score += 2
        why.append(f"Jupiter (dhana karaka) in {jh} → +2 dhana grace")

    if not why:
        why.append("D2 Hora data inconclusive")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L17_d2_hora_overlay", "score": score, "weight": weight,
        "why": why,
        "horas": horas,
    }


def _layer_d11_labha_overlay(kundli: dict, intel: dict) -> dict:
    """L18 — D11 Labha-amsa overlay. Gains-specific D-chart. MANDATORY.

    D11 is the divisional chart for gains and fulfilment of desires. Planets
    landing in the D11-11H from D11-lagna are the LABHA-RICH planets — they
    bring concrete gains. Jupiter / 11L / 2L in the D11 11H = strong
    gains-promise."""
    weight = 12
    score = 0
    why = []
    dc = _maybe_d_charts(kundli)
    d11 = dc.get("D11") or {}
    labha = d11.get("labha_planets") or []
    if not d11 or not d11.get("planets"):
        return {"layer": "L18_d11_labha_overlay", "score": 0,
                "why": ["D11 Labha-amsa unavailable"], "weight": weight}

    if labha:
        score += min(6, 2 * len(labha))
        why.append(f"D11 11H has {len(labha)} planet(s) "
                   f"({','.join(labha)}) → +{min(6, 2 * len(labha))}")

    if "Jupiter" in labha:
        score += 3
        why.append("Jupiter in D11 11H → +3 (dhana karaka in labha)")

    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)
    if second_lord and second_lord in labha:
        score += 2
        why.append(f"2L ({second_lord}) in D11 11H → +2")
    if eleventh_lord and eleventh_lord in labha:
        score += 2
        why.append(f"11L ({eleventh_lord}) in D11 11H → +2")

    # D11 lagna sign quality
    d11_lag = d11.get("lagna_sign")
    if d11_lag:
        ld = SIGN_LORDS.get(_norm(d11_lag))
        if ld == "Jupiter":
            score += 2
            why.append("D11 lagna in Jupiter sign → +2 dhana-fortified")
        elif ld in NATURAL_BENEFICS:
            score += 1
            why.append(f"D11 lagna in benefic sign of {ld} → +1")

    if not why:
        why.append("D11 Labha-amsa data inconclusive")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L18_d11_labha_overlay", "score": score, "weight": weight,
        "why": why,
        "labha_planets": labha,
        "d11_lagna_sign": d11_lag,
    }


def _layer_kp_csl_wealth(kp: dict) -> dict:
    """L19 — KP cuspal sub-lord 2/5/11. MANDATORY.

    KP rule for wealth:
      - 2H CSL signifying 2/5/9/11 → strong saved-money flow
      - 2H CSL signifying 6/8/12 → saved-money leak / unexpected expenses
      - 5H CSL signifying 2/9/11 → poorva-punya activates wealth
      - 5H CSL signifying 6/8/12 → punya blocked
      - 11H CSL signifying 2/5/9/11 → income flowing
      - 11H CSL signifying 6/8/12 → income obstructed
    """
    weight = 12
    score = 0
    why = []
    if not kp:
        return {"layer": "L19_kp_csl_wealth", "score": 0,
                "why": ["KP unavailable"], "weight": weight}

    cusps = kp.get("cusps") or []

    def _csl_for(house_num: int) -> Optional[str]:
        for c in cusps:
            if isinstance(c, dict) and c.get("house") == house_num:
                return c.get("subLord") or c.get("sub_lord") or c.get("sl")
        return None

    csl_2 = _csl_for(2)
    csl_5 = _csl_for(5)
    csl_11 = _csl_for(11)

    if csl_2:
        sigs_2 = _planet_significates_houses(kp, csl_2)
        good = sigs_2 & {2, 5, 9, 11}
        bad = sigs_2 & {6, 8, 12}
        if good and not bad:
            score += 4
            why.append(f"KP 2H CSL ({csl_2}) signifies {sorted(good)} → "
                       f"+4 saved-money flow")
        elif bad and not good:
            score -= 4
            why.append(f"KP 2H CSL ({csl_2}) signifies {sorted(bad)} → "
                       f"−4 saved-money leak")

    if csl_5:
        sigs_5 = _planet_significates_houses(kp, csl_5)
        punya = sigs_5 & {2, 9, 11}
        block = sigs_5 & {6, 8, 12}
        if punya and not block:
            score += 3
            why.append(f"KP 5H CSL ({csl_5}) → punya activates {sorted(punya)}")
        elif block and not punya:
            score -= 3
            why.append(f"KP 5H CSL ({csl_5}) → punya blocked {sorted(block)}")

    if csl_11:
        sigs_11 = _planet_significates_houses(kp, csl_11)
        flow = sigs_11 & {2, 5, 9, 11}
        block = sigs_11 & {6, 8, 12}
        if flow and not block:
            score += 4
            why.append(f"KP 11H CSL ({csl_11}) → income flow {sorted(flow)}")
        elif block and not flow:
            score -= 4
            why.append(f"KP 11H CSL ({csl_11}) → income obstructed "
                       f"{sorted(block)}")

    if not why:
        why.append("KP CSL data inconclusive for wealth houses 2/5/11")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L19_kp_csl_wealth", "score": score, "weight": weight,
        "why": why,
        "csl_2": csl_2, "csl_5": csl_5, "csl_11": csl_11,
    }


# ─────────────────────────────────────────────────────────────────────────────
# C. STRENGTH LAYERS  (L20 – L22)
# ─────────────────────────────────────────────────────────────────────────────

def _layer_ashtakavarga_wealth(av: dict) -> dict:
    """L20 — Ashtakavarga BAV for 2H / 11H."""
    weight = 5
    score = 0
    why = []
    if not av:
        return {"layer": "L20_ashtakavarga_wealth", "score": 0,
                "why": ["ashtakavarga unavailable"], "weight": weight}
    bav = av.get("bhinna") or av.get("bav") or {}

    def _h_total(h: int) -> Optional[float]:
        v = bav.get(str(h)) or bav.get(h)
        if isinstance(v, dict):
            v = v.get("total")
        return v if isinstance(v, (int, float)) else None

    h2 = _h_total(2)
    h11 = _h_total(11)

    if h2 is not None:
        if h2 >= 30:
            score += 3
            why.append(f"AV 2H BAV={h2} → +3 strong saved-money")
        elif h2 < 25:
            score -= 2
            why.append(f"AV 2H BAV={h2} → −2 weak saved-money")
    if h11 is not None:
        if h11 >= 30:
            score += 3
            why.append(f"AV 11H BAV={h11} → +3 strong gains")
        elif h11 < 25:
            score -= 2
            why.append(f"AV 11H BAV={h11} → −2 weak gains")

    score = max(-weight, min(weight, score))
    return {"layer": "L20_ashtakavarga_wealth", "score": score,
            "weight": weight, "why": why}


def _layer_shadbala_wealth(sb: dict, intel: dict) -> dict:
    """L21 — Shadbala for 2L, 11L, Jupiter."""
    weight = 5
    score = 0
    why = []
    if not sb:
        return {"layer": "L21_shadbala_wealth", "score": 0,
                "why": ["shadbala unavailable"], "weight": weight}

    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)
    targets = [second_lord, eleventh_lord, "Jupiter"]
    for pl in targets:
        if not pl:
            continue
        v = sb.get(pl)
        if isinstance(v, dict):
            v = v.get("total") or v.get("rupas") or v.get("score")
        if isinstance(v, (int, float)):
            if v >= 7:
                score += 2
                why.append(f"Shadbala {pl}={v:.1f} → +2 strong")
            elif v < 5:
                score -= 2
                why.append(f"Shadbala {pl}={v:.1f} → −2 weak")

    score = max(-weight, min(weight, score))
    return {"layer": "L21_shadbala_wealth", "score": score,
            "weight": weight, "why": why}


def _layer_bhava_bala_wealth(bb: dict) -> dict:
    """L22 — Bhava Bala for 2 / 5 / 9 / 11."""
    weight = 4
    score = 0
    why = []
    if not bb:
        return {"layer": "L22_bhava_bala_wealth", "score": 0,
                "why": ["bhava bala unavailable"], "weight": weight}

    for h in (2, 5, 9, 11):
        v = bb.get(str(h)) or bb.get(h) or {}
        if isinstance(v, dict):
            v = v.get("total") or v.get("rupas")
        if isinstance(v, (int, float)):
            if v >= 7:
                score += 1
                why.append(f"Bhava Bala {h}H={v:.1f} → +1")
            elif v < 5:
                score -= 1
                why.append(f"Bhava Bala {h}H={v:.1f} → −1")

    score = max(-weight, min(weight, score))
    return {"layer": "L22_bhava_bala_wealth", "score": score,
            "weight": weight, "why": why}


# ─────────────────────────────────────────────────────────────────────────────
# D. YOGA LAYERS  (L23 – L25)
# ─────────────────────────────────────────────────────────────────────────────

def _layer_dhana_yogas(yogas_d: dict, intel: dict, kundli: dict) -> dict:
    """L23 — Dhana Yogas (Lakshmi + Maha-Lakshmi + Dhana + Raja-Yoga +
    Vipareeta-Raja-Yoga). All POSITIVE wealth yogas."""
    weight = 8
    score = 0
    why = []
    planets = kundli.get("planets") or []

    # Dhana Yoga: lord of dhana house (2/5/9/11) connects to another
    # dhana lord by mutual aspect or conjunction
    dhana_lords = {h: _house_lord(intel, h) for h in (2, 5, 9, 11)}
    dhana_lords = {h: lord for h, lord in dhana_lords.items() if lord}
    dhana_pairs = []
    for h1, l1 in dhana_lords.items():
        for h2, l2 in dhana_lords.items():
            if h1 >= h2 or l1 == l2:
                continue
            l1_h = _planet_house(planets, l1)
            l2_h = _planet_house(planets, l2)
            if l1_h is None or l2_h is None:
                continue
            # Conjunction
            if l1_h == l2_h:
                dhana_pairs.append(f"{l1}+{l2}@{l1_h}H ({h1}L+{h2}L conj)")
                continue
            # Mutual aspect — both must aspect each other's house
            if (l2_h in _aspect_houses(l1, l1_h) and
                    l1_h in _aspect_houses(l2, l2_h)):
                dhana_pairs.append(f"{l1}↔{l2} ({h1}L↔{h2}L mutual aspect)")
    if dhana_pairs:
        bonus = min(6, 2 * len(dhana_pairs))
        score += bonus
        why.append(f"{len(dhana_pairs)} Dhana Yoga(s): "
                   f"{'; '.join(dhana_pairs[:3])} → +{bonus}")

    # Lakshmi Yoga: 9L exalted + Venus in own/exalted in kendra/trikona
    ninth_lord = _house_lord(intel, 9)
    if ninth_lord:
        n9_dig = _planet_dignity(intel, ninth_lord)
        ven_dig = _planet_dignity(intel, "Venus")
        ven_h = _planet_house(planets, "Venus")
        if (n9_dig in ("exalted", "own-sign", "moolatrikona") and
                ven_dig in ("exalted", "own-sign", "moolatrikona") and
                ven_h in (KENDRA | TRIKONA)):
            score += 4
            why.append(f"Lakshmi Yoga (9L {ninth_lord} {n9_dig} + "
                       f"Venus {ven_dig} in {ven_h}H) → +4")

    # Maha-Lakshmi indicator: Jupiter in 2H/5H/9H/11H exalted/own
    jup_h = _planet_house(planets, "Jupiter")
    jup_d = _planet_dignity(intel, "Jupiter")
    if (jup_h in {2, 5, 9, 11} and
            jup_d in ("exalted", "own-sign", "moolatrikona")):
        score += 3
        why.append(f"Maha-Lakshmi indicator (Jupiter {jup_d} in "
                   f"{jup_h}H dhana house) → +3")

    # Vipareeta-Raja-Yoga: 6L/8L/12L in another dushtana
    for hd in (6, 8, 12):
        ld = _house_lord(intel, hd)
        if not ld:
            continue
        ldh = _planet_house(planets, ld)
        if ldh in (6, 8, 12) and ldh != hd:
            score += 2
            why.append(f"Vipareeta-Raja-Yoga ({hd}L {ld} in {ldh}H) → +2 "
                       "wealth-via-crisis-resolution")
            break  # one is enough — don't double-count

    # Yogas dict from upstream
    if isinstance(yogas_d, dict):
        for k in ("lakshmi_yoga", "dhana_yoga", "maha_lakshmi_yoga",
                  "raja_yoga", "vipareeta_raja_yoga", "neecha_bhanga"):
            if yogas_d.get(k):
                score += 1
                why.append(f"Upstream yoga: {k} present → +1")

    if not why:
        why.append("No major dhana yogas detected")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L23_dhana_yogas", "score": score, "weight": weight,
        "why": why,
    }


def _layer_daridra_yogas(yogas_d: dict, intel: dict, kundli: dict) -> dict:
    """L24 — Daridra / Kemadruma / Anti-Dhana yogas. NEGATIVE."""
    weight = 6
    score = 0
    why = []
    planets = kundli.get("planets") or []

    # Daridra Yoga: 11L in dushtana from lagna (poverty / income blockage)
    eleventh_lord = _house_lord(intel, 11)
    if eleventh_lord:
        h = _planet_house(planets, eleventh_lord)
        if h in DUSHTANA:
            score -= 3
            why.append(f"Daridra Yoga: 11L ({eleventh_lord}) in {h}H "
                       f"(dushtana) → −3")

    # 2L debilitated
    second_lord = _house_lord(intel, 2)
    if second_lord and _planet_dignity(intel, second_lord) == "debilitated":
        score -= 3
        why.append(f"2L ({second_lord}) debilitated → −3 saved-money "
                   f"karma weak")

    # Jupiter debilitated AND in dushtana
    jup_h = _planet_house(planets, "Jupiter")
    jup_d = _planet_dignity(intel, "Jupiter")
    if jup_d == "debilitated" and jup_h in DUSHTANA:
        score -= 3
        why.append(f"Jupiter debilitated in {jup_h}H → −3 dhana-karaka "
                   f"deeply afflicted")

    # Kemadruma indicator (Moon isolation) — counted in L12 too but smaller
    moon_h = _planet_house(planets, "Moon")
    if moon_h:
        snd = ((moon_h - 1 + 1) % 12) + 1
        twf = ((moon_h - 1 - 1) % 12) + 1
        has_neighbour = False
        for p in planets:
            if not isinstance(p, dict):
                continue
            if p.get("name") in ("Moon", "Sun", "Rahu", "Ketu"):
                continue
            if p.get("house") in (snd, twf):
                has_neighbour = True
                break
        if not has_neighbour:
            score -= 1
            why.append("Kemadruma echo (Moon isolated) → −1 cash-flow weak")

    # Yogas dict from upstream
    if isinstance(yogas_d, dict):
        for k in ("daridra_yoga", "kemadruma_yoga", "anti_dhana_yoga"):
            if yogas_d.get(k):
                score -= 2
                why.append(f"Upstream yoga: {k} present → −2")

    if not why:
        why.append("No major daridra yogas detected")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L24_daridra_yogas", "score": score, "weight": weight,
        "why": why,
    }


def _layer_sade_sati_wealth(intel: dict, kundli: dict) -> dict:
    """L25 — Sade Sati on 2L / 11L. Saturn pressure on dhana lords slows
    wealth accumulation but builds long-term discipline (±)."""
    weight = 5
    score = 0
    why = []

    # Read sade-sati flag from intel (chart_intelligence emits sade_sati dict)
    ss = intel.get("sade_sati") if isinstance(intel, dict) else None
    in_ss = False
    if isinstance(ss, dict):
        in_ss = bool(ss.get("active") or ss.get("inSadeSati") or
                     ss.get("isActive"))
    elif isinstance(ss, bool):
        in_ss = ss
    if not in_ss:
        return {"layer": "L25_sade_sati_wealth", "score": 0,
                "why": ["Not in Sade Sati"], "weight": weight}

    # In sade-sati
    score -= 2
    why.append("Sade Sati active → −2 saved-money pressure (general)")

    # If 2L or 11L is Saturn or in Capricorn/Aquarius, additional pressure
    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)
    for role, lord in (("2L", second_lord), ("11L", eleventh_lord)):
        if not lord:
            continue
        if lord == "Saturn":
            score -= 2
            why.append(f"{role} is Saturn under sade-sati → "
                       f"−2 dhana-lord under pressure")
        else:
            sg = _planet_sign(kundli.get("planets") or [], lord)
            if sg in ("Capricorn", "Aquarius"):
                score -= 1
                why.append(f"{role} ({lord}) in Saturn sign during sade-sati → −1")

    # Discipline credit — if Jupiter is also strong (well-placed dhana karaka)
    jup_h = _planet_house(kundli.get("planets") or [], "Jupiter")
    jup_d = _planet_dignity(intel, "Jupiter")
    if jup_h in (KENDRA | TRIKONA | {2, 11}) and jup_d in (
            "exalted", "own-sign", "moolatrikona", "friend-sign"):
        score += 2
        why.append("Jupiter strong → +2 (discipline credit during sade-sati)")

    score = max(-weight, min(weight, score))
    return {
        "layer": "L25_sade_sati_wealth", "score": score, "weight": weight,
        "why": why,
        "in_sade_sati": in_ss,
    }


# ─────────────────────────────────────────────────────────────────────────────
# E. TRIGGERS  (T1 – T3)
# ─────────────────────────────────────────────────────────────────────────────

def _trigger_vimshottari_wealth(kundli: dict, intel: dict,
                                karakas_d: dict) -> dict:
    """T1 — Vimshottari MD+AD+PD on wealth lords (2L/5L/9L/11L) +
    Jupiter (dhana karaka) + Jaimini AmK (mind-strategy of money)."""
    weight = 12
    score = 0
    why = []
    md, ad, pd = _dasha_lords(kundli)
    planets = kundli.get("planets") or []

    if not md and not ad:
        return {"layer": "T1_vimshottari_wealth", "score": 0,
                "why": ["dasha lords unknown"], "weight": weight}

    second_lord = _house_lord(intel, 2)
    fifth_lord = _house_lord(intel, 5)
    ninth_lord = _house_lord(intel, 9)
    eleventh_lord = _house_lord(intel, 11)
    sixth_lord = _house_lord(intel, 6)
    eighth_lord = _house_lord(intel, 8)
    twelfth_lord = _house_lord(intel, 12)

    amk = karakas_d.get("AmK") or karakas_d.get("Amatyakaraka") or {}
    amk_planet = amk.get("planet") if isinstance(amk, dict) else amk
    bk = karakas_d.get("BK") or karakas_d.get("Bhratrikaraka") or {}
    bk_planet = bk.get("planet") if isinstance(bk, dict) else bk

    dhana_lords = {second_lord, fifth_lord, ninth_lord,
                   eleventh_lord} - {None, ""}
    debt_lords = {sixth_lord, eighth_lord, twelfth_lord} - {None, ""}

    def _eval(role: str, planet: str, weight_factor: float):
        nonlocal score
        if not planet:
            return
        h = _planet_house(planets, planet)
        dgn = _planet_dignity(intel, planet)

        # Dhana lord active = strong wealth-trigger
        if planet in dhana_lords:
            label = []
            if planet == second_lord: label.append("2L")
            if planet == fifth_lord: label.append("5L")
            if planet == ninth_lord: label.append("9L")
            if planet == eleventh_lord: label.append("11L")
            tag = "+".join(label)
            if dgn in ("exalted", "moolatrikona", "own-sign"):
                score += int(4 * weight_factor)
                why.append(f"{role} {planet}={tag} strong → "
                           f"{int(4*weight_factor):+d}")
            elif dgn == "debilitated":
                score -= int(2 * weight_factor)
                why.append(f"{role} {planet}={tag} debilitated → "
                           f"{-int(2*weight_factor):+d}")
            else:
                score += int(2 * weight_factor)
                why.append(f"{role} {planet}={tag} active → "
                           f"{int(2*weight_factor):+d}")
        # Jupiter active = dhana-karaka window
        elif planet == "Jupiter":
            if dgn in ("exalted", "moolatrikona", "own-sign"):
                score += int(3 * weight_factor)
                why.append(f"{role} Jupiter (dhana karaka) strong → "
                           f"{int(3*weight_factor):+d}")
            elif dgn == "debilitated":
                score -= int(2 * weight_factor)
                why.append(f"{role} Jupiter debilitated → "
                           f"{-int(2*weight_factor):+d}")
            else:
                score += int(2 * weight_factor)
                why.append(f"{role} Jupiter (dhana karaka) → "
                           f"{int(2*weight_factor):+d}")
        # Jaimini AmK = how money is earned
        elif planet == amk_planet and amk_planet:
            score += int(2 * weight_factor)
            why.append(f"{role} {planet}=AmK (career-money strategy) → "
                       f"{int(2*weight_factor):+d}")
        elif planet == bk_planet and bk_planet:
            score += int(1 * weight_factor)
            why.append(f"{role} {planet}=BK (effort-income) → "
                       f"{int(1*weight_factor):+d}")
        # Debt-lords active = wealth-pressure window
        elif planet in debt_lords:
            score -= int(3 * weight_factor)
            why.append(f"{role} {planet}=debt-lord active → "
                       f"{-int(3*weight_factor):+d}")
        elif planet in NATURAL_BENEFICS:
            if h in (KENDRA | TRIKONA | {2, 11}):
                score += int(1 * weight_factor)
                why.append(f"{role} {planet} (benefic) in {h}H → "
                           f"{int(1*weight_factor):+d}")
        elif planet in NATURAL_MALEFICS:
            if h in DUSHTANA:
                # Vipareeta echo: malefic in dushtana during own dasha
                score += int(1 * weight_factor)
                why.append(f"{role} {planet} (malefic) in {h}H dushtana → "
                           f"{int(1*weight_factor):+d} vipareeta echo")
            else:
                score -= int(1 * weight_factor)
                why.append(f"{role} {planet} (malefic) → "
                           f"{-int(1*weight_factor):+d}")

    if md: _eval("MD", md, 1.0)
    if ad: _eval("AD", ad, 0.7)
    if pd: _eval("PD", pd, 0.4)

    score = max(-weight, min(weight, score))
    return {
        "layer": "T1_vimshottari_wealth", "score": score, "weight": weight,
        "why": why,
        "md": md, "ad": ad, "pd": pd,
    }


def _trigger_jupiter_transit_wealth(jup_t: dict, intel: dict,
                                    kundli: dict) -> dict:
    """T2 — Jupiter transit on 2H/5H/9H/11H + transit aspects to dhana lords.

    Jupiter transit is the SINGLE most reliable wealth-window indicator —
    Guru-Gochar over dhana houses gives the actual receiving period."""
    weight = 7
    score = 0
    why = []
    if not jup_t:
        return {"layer": "T2_jupiter_transit_wealth", "score": 0,
                "why": ["jupiter transit data unavailable"], "weight": weight}

    house = jup_t.get("jupiter_house_from_lagna")
    if house in (2, 11):
        score += 5
        why.append(f"Jupiter transiting {house}H (CORE dhana) → "
                   f"+5 strong wealth-window")
    elif house in (5, 9):
        score += 4
        why.append(f"Jupiter transiting {house}H (poorva-punya/bhagya) → "
                   f"+4 wealth-promise activated")
    elif house in (1, 4, 7, 10):
        score += 2
        why.append(f"Jupiter transiting {house}H (kendra) → "
                   f"+2 supportive grace")
    elif house in (6, 8, 12):
        score -= 2
        why.append(f"Jupiter transiting {house}H (dushtana) → "
                   f"−2 expansion blocked")

    # Jupiter transit on Moon (Sade-Sati equivalent for Jupiter — guru-chandala
    # if conjunct Rahu)
    moon_h = _planet_house(kundli.get("planets") or [], "Moon")
    if (jup_t.get("jupiter_house_from_moon") == 1 and
            jup_t.get("conjunct_rahu")):
        score -= 3
        why.append("Jupiter transit conjoined with Rahu (Guru-Chandala) → "
                   "−3 ethical-money pressure")

    # Aspects to 2L / 11L
    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)
    aspecting = jup_t.get("aspecting_planets") or []
    if isinstance(aspecting, list):
        if second_lord and second_lord in aspecting:
            score += 2
            why.append(f"Jupiter transit aspects 2L ({second_lord}) → "
                       f"+2 saved-money grace")
        if eleventh_lord and eleventh_lord in aspecting:
            score += 2
            why.append(f"Jupiter transit aspects 11L ({eleventh_lord}) → "
                       f"+2 income grace")

    if not why:
        why.append(f"Jupiter neutral position ({jup_t.get('jupiter_sign')})")

    score = max(-weight, min(weight, score))
    return {
        "layer": "T2_jupiter_transit_wealth", "score": score, "weight": weight,
        "why": why,
    }


def _trigger_saturn_transit_wealth(saturn_t: dict, intel: dict,
                                   kundli: dict) -> dict:
    """T3 — Saturn transit on 2H/11H + sade-sati on Moon (cash-flow stress)
    + Saturn transit on dhana lords (slow but steady restructuring window)."""
    weight = 6
    score = 0
    why = []
    if not saturn_t:
        return {"layer": "T3_saturn_transit_wealth", "score": 0,
                "why": ["saturn transit data unavailable"], "weight": weight}

    house = saturn_t.get("saturn_house_from_lagna")
    if house == 2:
        score -= 3
        why.append("Saturn transiting 2H → −3 saved-money under restructure")
    elif house == 11:
        # Saturn in 11H (own house in transit) is mixed — slow but
        # consolidating gains
        score += 2
        why.append("Saturn transiting 11H (own) → +2 slow consolidation of gains")
    elif house in (5, 9):
        score -= 2
        why.append(f"Saturn transiting {house}H → −2 punya/bhagya delays")
    elif house in (6, 8, 12):
        score -= 1
        why.append(f"Saturn transiting {house}H → −1 (debt/crisis backdrop)")

    phase = saturn_t.get("sade_sati_phase")
    if phase == "peak":
        score -= 3
        why.append("Saturn sade-sati PEAK over Moon → −3 cash-flow stress")
    elif phase in ("rising", "setting"):
        score -= 1
        why.append(f"Saturn sade-sati {phase} → −1 cash-flow caution")
    elif phase == "ashtama":
        score -= 2
        why.append("Ashtama Shani over Moon → −2 hidden-money stress")
    elif phase == "kantaka":
        score -= 1
        why.append("Kantaka Shani over Moon → −1 daily-grind expense")

    # Saturn transit aspect on 2L / 11L
    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)
    aspecting = saturn_t.get("aspecting_planets") or []
    if isinstance(aspecting, list):
        if second_lord and second_lord in aspecting:
            score -= 1
            why.append(f"Saturn transit aspects 2L ({second_lord}) → "
                       f"−1 saved-money discipline")
        if eleventh_lord and eleventh_lord in aspecting:
            score -= 1
            why.append(f"Saturn transit aspects 11L ({eleventh_lord}) → "
                       f"−1 income slow")

    if not why:
        why.append(f"Saturn neutral position ({saturn_t.get('saturn_sign')})")

    score = max(-weight, min(weight, score))
    return {
        "layer": "T3_saturn_transit_wealth", "score": score, "weight": weight,
        "why": why,
    }


# ─────────────────────────────────────────────────────────────────────────────
# F. MODIFIERS  (M1 – M8)
# ─────────────────────────────────────────────────────────────────────────────

def _modifier_combust_wealth(intel: dict, kundli: dict) -> dict:
    """M1 — Combustion of 2L / 11L / Jupiter / Venus (dhana karakas)."""
    delta = 0
    why = []
    planets = kundli.get("planets") or []
    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)
    for pl in (second_lord, eleventh_lord, "Jupiter", "Venus"):
        if pl and _is_combust(planets, pl):
            delta -= 2
            why.append(f"{pl} combust → −2 dhana significator obscured")
    return {"mod": "M1_combust_wealth", "delta": delta, "why": why}


def _modifier_retrograde_wealth(intel: dict, kundli: dict) -> dict:
    """M2 — Retrograde of 2L / 11L (recurring income/savings karma) +
    retrograde of debt lords (re-emerging debt). Generally mildly POS for
    dhana lords (re-saving / repeat income), NEG for debt lords."""
    delta = 0
    why = []
    planets = kundli.get("planets") or []
    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)
    sixth_lord = _house_lord(intel, 6)
    eighth_lord = _house_lord(intel, 8)
    for pl in (second_lord, eleventh_lord):
        if pl and _is_retrograde(planets, pl):
            delta += 1
            why.append(f"{pl} (dhana lord) retrograde → +1 (recurring)")
    for pl in (sixth_lord, eighth_lord):
        if pl and _is_retrograde(planets, pl):
            delta -= 1
            why.append(f"{pl} (debt lord) retrograde → −1 (re-emerging)")
    return {"mod": "M2_retrograde_wealth", "delta": delta, "why": why}


def _modifier_malefic_aspects_wealth(intel: dict, kundli: dict) -> dict:
    """M3 — Malefic / benefic aspects on 2H / 11H."""
    delta = 0
    why = []
    planets = kundli.get("planets") or []
    for h in (2, 11):
        aspecting = _planets_aspecting_house(planets, h)
        bad = [p for p in aspecting if p in ("Saturn", "Mars", "Rahu", "Ketu")]
        good = [p for p in aspecting if p in ("Jupiter", "Venus", "Mercury")]
        # Saturn aspect on 11H is supportive (own house) — exclude from bad
        if h == 11 and "Saturn" in bad:
            bad.remove("Saturn")
            good.append("Saturn")  # promote to supportive
        if bad:
            delta -= len(bad)
            why.append(f"{','.join(bad)} aspect {h}H → {-len(bad):+d}")
        if good:
            delta += len(good)
            why.append(f"{','.join(good)} aspect {h}H → {+len(good):+d}")
    return {"mod": "M3_malefic_aspects_wealth", "delta": delta, "why": why}


def _modifier_dignity_jupiter_venus(intel: dict) -> dict:
    """M4 — Dignity of Jupiter (dhana karaka) + Venus (luxury karaka)
    counted as a global multiplier on the wealth verdict."""
    delta = 0
    why = []
    for pl in ("Jupiter", "Venus"):
        dgn = _planet_dignity(intel, pl)
        if dgn in ("exalted", "moolatrikona"):
            delta += 2
            why.append(f"{pl} {dgn} → +2 wealth-karaka full strength")
        elif dgn == "own-sign":
            delta += 1
            why.append(f"{pl} own-sign → +1")
        elif dgn == "debilitated":
            delta -= 2
            why.append(f"{pl} debilitated → −2 wealth-karaka weakened")
        elif dgn == "enemy-sign":
            delta -= 1
            why.append(f"{pl} enemy-sign → −1")
    return {"mod": "M4_dignity_jup_ven", "delta": delta, "why": why}


def _modifier_vargottama_lift(kundli: dict, intel: dict) -> dict:
    """M5 — Vargottama lift for Jupiter / 2L / 11L (already counted in
    L16; modifier surfaces a small extra recognition for narrator)."""
    delta = 0
    why = []
    natal = kundli.get("planets") or []
    dc = _maybe_d_charts(kundli)
    d9 = dc.get("D9") or []
    if not d9:
        return {"mod": "M5_vargottama_lift", "delta": 0, "why": []}
    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)
    targets = [("Jupiter", "Jupiter"), ("2L", second_lord),
               ("11L", eleventh_lord)]
    for label, pl in targets:
        if pl and _vargottama(pl, natal, d9):
            delta += 1
            why.append(f"{label} ({pl}) vargottama → +1 sustained")
    return {"mod": "M5_vargottama_lift", "delta": delta, "why": why}


def _modifier_parivartana_dhana(intel: dict, kundli: dict) -> dict:
    """M6 — Parivartana (mutual exchange) between dhana-house lords.
    The 2L↔11L exchange is the strongest wealth-yoga; 5L↔11L is also famous
    (poorva-punya ↔ labha)."""
    delta = 0
    why = []
    planets = kundli.get("planets") or []
    pairs_to_check = [
        (2, 11), (5, 11), (2, 5), (9, 11), (2, 9),
    ]
    seen = set()
    for h1, h2 in pairs_to_check:
        l1 = _house_lord(intel, h1)
        l2 = _house_lord(intel, h2)
        if not l1 or not l2:
            continue
        # Lord1 in house2 AND lord2 in house1
        if (_planet_house(planets, l1) == h2 and
                _planet_house(planets, l2) == h1):
            key = tuple(sorted([h1, h2]))
            if key in seen:
                continue
            seen.add(key)
            delta += 2
            why.append(f"Parivartana {h1}L↔{h2}L ({l1}↔{l2}) → +2 dhana yoga")
    return {"mod": "M6_parivartana_dhana", "delta": delta, "why": why}


def _modifier_neecha_bhanga_dhana(intel: dict, kundli: dict) -> dict:
    """M7 — Neecha-bhanga cancellation for debilitated wealth karakas
    (Jupiter / Venus / Mercury / dhana lords). When the debilitation cancels,
    the wealth promise is restored."""
    delta = 0
    why = []
    planets = kundli.get("planets") or []
    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)
    targets = ["Jupiter", "Venus", "Mercury", second_lord, eleventh_lord]
    targets = [t for t in targets if t]
    seen = set()
    for pl in targets:
        if pl in seen:
            continue
        seen.add(pl)
        if _planet_dignity(intel, pl) != "debilitated":
            continue
        sign = _planet_sign(planets, pl)
        if not sign:
            continue
        # Classic neecha-bhanga rules:
        # (a) Lord of debilitation sign is in kendra from lagna or Moon
        # (b) Exaltation lord of that sign is in kendra from lagna or Moon
        deb_sign_lord = SIGN_LORDS.get(_norm(sign))
        if not deb_sign_lord:
            continue
        deb_sign_lord_h = _planet_house(planets, deb_sign_lord)
        if deb_sign_lord_h in KENDRA:
            delta += 2
            why.append(f"Neecha-bhanga: {pl} debilitated, but "
                       f"{deb_sign_lord} (sign-lord) in {deb_sign_lord_h}H "
                       f"kendra → +2 promise restored")
            continue
        # Exaltation-lord check. Direct planet → lord-of-exaltation-sign
        # mapping (Sun exalts in Aries → Mars, Moon in Taurus → Venus, etc.)
        # Replaces the previously-undefined EXALTED_PLANETS lookup.
        _EXALT_SIGN_LORD = {
            "Sun":     "Mars",      # Aries
            "Moon":    "Venus",     # Taurus
            "Mars":    "Saturn",    # Capricorn
            "Mercury": "Mercury",   # Virgo (own sign)
            "Jupiter": "Moon",      # Cancer
            "Venus":   "Jupiter",   # Pisces
            "Saturn":  "Venus",     # Libra
        }
        exalt_lord = _EXALT_SIGN_LORD.get(pl)
        if exalt_lord:
            ex_h = _planet_house(planets, exalt_lord)
            if ex_h in KENDRA:
                delta += 2
                why.append(f"Neecha-bhanga: {pl} debilitated, exalt-lord "
                           f"{exalt_lord} in {ex_h}H kendra → +2")
    return {"mod": "M7_neecha_bhanga_dhana", "delta": delta, "why": why}


def _modifier_sade_sati_dhana_lords(intel: dict, kundli: dict) -> dict:
    """M8 — Sade Sati specifically pressing 2L / 11L (cash-flow + savings)."""
    delta = 0
    why = []
    ss = intel.get("sade_sati") if isinstance(intel, dict) else None
    in_ss = False
    if isinstance(ss, dict):
        in_ss = bool(ss.get("active") or ss.get("inSadeSati") or
                     ss.get("isActive"))
    elif isinstance(ss, bool):
        in_ss = ss
    if not in_ss:
        return {"mod": "M8_sade_sati_dhana_lords", "delta": 0, "why": []}
    planets = kundli.get("planets") or []
    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)
    for role, lord in (("2L", second_lord), ("11L", eleventh_lord)):
        if not lord:
            continue
        sg = _planet_sign(planets, lord)
        if sg in ("Capricorn", "Aquarius"):
            delta -= 1
            why.append(f"Sade-sati pressing {role} ({lord} in {sg}) → −1")
    return {"mod": "M8_sade_sati_dhana_lords", "delta": delta, "why": why}


# ─────────────────────────────────────────────────────────────────────────────
# G. CONDITIONAL MICRO-LAYERS  (C1 – C5, bucket-gated)
# ─────────────────────────────────────────────────────────────────────────────

def _conditional_loan_clear(intel: dict, kundli: dict,
                            saturn_t: dict) -> dict:
    """C1 — Loan-clearance / debt-recovery readiness.
    Strong 6L (own/exalted) + Saturn supportive + 8H not afflicted +
    Jupiter aspect on 6H = clear-debt window."""
    score = 0
    why = []
    planets = kundli.get("planets") or []

    sixth_lord = _house_lord(intel, 6)
    if sixth_lord:
        l6h = _planet_house(planets, sixth_lord)
        l6d = _planet_dignity(intel, sixth_lord)
        # 6L in own sign / exalted = strong against debts
        if l6d in ("exalted", "moolatrikona", "own-sign"):
            score += 3
            why.append(f"6L ({sixth_lord}) {l6d} → +3 debt-management strength")
        # 6L in 8/12 = vipareeta debt-clearance
        if l6h in (8, 12):
            score += 2
            why.append(f"6L ({sixth_lord}) in {l6h}H → +2 vipareeta debt-clear")

    # Jupiter aspect on 6H (debt-dissolving grace)
    if "Jupiter" in _planets_aspecting_house(planets, 6):
        score += 2
        why.append("Jupiter aspects 6H → +2 debt-dissolving grace")

    # Saturn transit supportive (in 11H or own sign in transit)
    if saturn_t:
        sh = saturn_t.get("saturn_house_from_lagna")
        if sh == 11:
            score += 1
            why.append("Saturn transit 11H → +1 sustained loan-clearance window")
        elif sh in (2, 8):
            score -= 1
            why.append(f"Saturn transit {sh}H → −1 (debt friction)")

    # 8L afflicted (in 6 or aspected by malefics) = inheritance/joint-fund
    # complication — adverse for fresh loan-clear timing
    eighth_lord = _house_lord(intel, 8)
    if eighth_lord:
        l8h = _planet_house(planets, eighth_lord)
        if l8h == 6:
            score += 2
            why.append(f"8L ({eighth_lord}) in 6H → +2 (Vipareeta — "
                       f"debts cancel themselves)")

    why.append("⚠ ENGINE RULE: NEVER advise EMI default / loan skip — "
               "always recommend re-financing / pre-payment strategy.")

    return {"cond": "C1_loan_clear", "score": score, "why": why}


def _conditional_property_buy(intel: dict, kundli: dict,
                              jup_t: dict) -> dict:
    """C2 — Property purchase readiness.
    Strong 4H + 4L + Mars (real-estate karaka) + Venus (vehicle/luxury karaka)
    + Jupiter transit on 4H/11H = property-buy window."""
    score = 0
    why = []
    planets = kundli.get("planets") or []

    fourth_lord = _house_lord(intel, 4)
    if fourth_lord:
        l4h = _planet_house(planets, fourth_lord)
        l4d = _planet_dignity(intel, fourth_lord)
        if l4h in (TRIKONA | KENDRA | {2, 11}):
            score += 2
            why.append(f"4L ({fourth_lord}) in {l4h}H → +2 property promise")
        if l4d in ("exalted", "moolatrikona", "own-sign"):
            score += 2
            why.append(f"4L ({fourth_lord}) {l4d} → +2 strong asset karma")

    # Mars in 4H or aspecting 4H = real-estate karaka active
    mars_h = _planet_house(planets, "Mars")
    if mars_h == 4:
        score += 1
        why.append("Mars in 4H → +1 (real-estate karaka in own bhava sense)")
    elif "Mars" in _planets_aspecting_house(planets, 4):
        score += 1
        why.append("Mars aspects 4H → +1 real-estate activation")

    # Venus in 4H = luxury / vehicle support
    if _planet_house(planets, "Venus") == 4:
        score += 1
        why.append("Venus in 4H → +1 luxury/vehicle yoga")

    # Jupiter transit on 4H or 11H
    if jup_t:
        jh = jup_t.get("jupiter_house_from_lagna")
        if jh == 4:
            score += 2
            why.append("Jupiter transit 4H → +2 property-grace window")
        elif jh == 11:
            score += 1
            why.append("Jupiter transit 11H → +1 wealth-flow supports purchase")

    why.append("⚠ ENGINE RULE: Always recommend RERA-registered project "
               "+ legal title check; NEVER endorse a specific builder.")

    return {"cond": "C2_property_buy", "score": score, "why": why}


def _conditional_investment_return(intel: dict, kundli: dict,
                                   kp: dict) -> dict:
    """C3 — Investment return / equity / mutual-fund timing.
    5H (speculation/punya) + 9H (bhagya) + 11H (gains) cusp sub-lords
    in KP determine actual return-window."""
    score = 0
    why = []
    planets = kundli.get("planets") or []

    fifth_lord = _house_lord(intel, 5)
    ninth_lord = _house_lord(intel, 9)
    eleventh_lord = _house_lord(intel, 11)

    # 5L–9L–11L axis well-placed
    strong_count = 0
    for role, lord in (("5L", fifth_lord), ("9L", ninth_lord),
                       ("11L", eleventh_lord)):
        if not lord:
            continue
        h = _planet_house(planets, lord)
        d = _planet_dignity(intel, lord)
        if h in (KENDRA | TRIKONA | {2, 11}) and d in (
                "exalted", "moolatrikona", "own-sign", "friend-sign"):
            strong_count += 1
            why.append(f"{role} ({lord}) in {h}H {d} → strong axis link")
    if strong_count >= 2:
        score += 3
        why.append(f"5-9-11 axis: {strong_count}/3 strong → +3 return karma")

    # Jupiter aspect on 5H or 11H
    if "Jupiter" in _planets_aspecting_house(planets, 5):
        score += 1
        why.append("Jupiter aspects 5H → +1 wisdom-based return")
    if "Jupiter" in _planets_aspecting_house(planets, 11):
        score += 1
        why.append("Jupiter aspects 11H → +1 expansion of gains")

    # KP CSL of 11H signifying 2/5/9/11
    if kp:
        cusps = kp.get("cusps") or []
        csl_11 = None
        for c in cusps:
            if isinstance(c, dict) and c.get("house") == 11:
                csl_11 = (c.get("subLord") or c.get("sub_lord") or
                          c.get("sl"))
                break
        if csl_11:
            sigs = _planet_significates_houses(kp, csl_11)
            if sigs & {2, 5, 9, 11}:
                score += 2
                why.append(f"KP 11H CSL ({csl_11}) signifies dhana houses → "
                           f"+2 return-window cosmic-cleared")
            elif sigs & {6, 8, 12}:
                score -= 2
                why.append(f"KP 11H CSL ({csl_11}) signifies dushtana → "
                           f"−2 return-window blocked")

    # Rahu in 5H = speculative win potential (volatile)
    if _planet_house(planets, "Rahu") == 5:
        score += 1
        why.append("Rahu in 5H → +1 (speculative — volatile)")

    why.append("⚠ ENGINE RULE: SEBI disclaimer MANDATORY; NEVER endorse "
               "specific stock/MF/crypto; emit only relative return language.")

    return {"cond": "C3_investment_return", "score": score, "why": why}


def _conditional_inheritance(intel: dict, kundli: dict,
                             karakas_d: dict) -> dict:
    """C4 — Inheritance / joint-funds / spouse-wealth timing.
    Strong 8H + Jupiter in/aspecting 8H + 8L well-placed + Mars not afflicting
    8L (mars in 8L's house = property dispute)."""
    score = 0
    why = []
    planets = kundli.get("planets") or []

    eighth_lord = _house_lord(intel, 8)
    if eighth_lord:
        l8h = _planet_house(planets, eighth_lord)
        l8d = _planet_dignity(intel, eighth_lord)
        if l8h in (2, 11):
            score += 3
            why.append(f"8L ({eighth_lord}) in {l8h}H → +3 inheritance flows "
                       f"into dhana/labha")
        elif l8h in (6, 12):
            score += 2
            why.append(f"8L ({eighth_lord}) in {l8h}H → +2 vipareeta")
        if l8d in ("exalted", "moolatrikona", "own-sign"):
            score += 2
            why.append(f"8L ({eighth_lord}) {l8d} → +2 strong inheritance karma")

    # Jupiter in or aspecting 8H
    if _planet_house(planets, "Jupiter") == 8:
        score += 2
        why.append("Jupiter in 8H → +2 sustained inheritance")
    elif "Jupiter" in _planets_aspecting_house(planets, 8):
        score += 1
        why.append("Jupiter aspects 8H → +1 inheritance grace")

    # Mars affliction (sibling/spouse-side disputes)
    if eighth_lord:
        l8h = _planet_house(planets, eighth_lord)
        mars_h = _planet_house(planets, "Mars")
        if mars_h == l8h:
            score -= 2
            why.append(f"Mars conjunct 8L ({eighth_lord}) → "
                       f"−2 inheritance/property dispute risk")

    why.append("⚠ ENGINE RULE: NEVER predict death of any relative or "
               "specific inheritance amount — emit qualitative timing only.")

    return {"cond": "C4_inheritance", "score": score, "why": why}


def _conditional_sudden_windfall(intel: dict, kundli: dict,
                                 kp: dict) -> dict:
    """C5 — Sudden windfall / lottery / unexpected income.
    Engine is STRICTLY anti-lottery — this conditional ONLY assesses karmic
    capacity for unexpected income (e.g. bonus, inheritance shock,
    unexpected client) NOT lottery/satta/jackpot.

    Strong 5H + Rahu/Jupiter trigger + Vipareeta yoga link."""
    score = 0
    why = []
    planets = kundli.get("planets") or []

    fifth_lord = _house_lord(intel, 5)
    if fifth_lord:
        l5h = _planet_house(planets, fifth_lord)
        l5d = _planet_dignity(intel, fifth_lord)
        if l5h in (TRIKONA | {2, 11}) and l5d in (
                "exalted", "moolatrikona", "own-sign", "friend-sign"):
            score += 2
            why.append(f"5L ({fifth_lord}) in {l5h}H {l5d} → +2 punya-driven "
                       f"unexpected gains")

    # Jupiter in 5H = sudden grace
    if _planet_house(planets, "Jupiter") == 5:
        score += 2
        why.append("Jupiter in 5H → +2 dharmic-windfall karma")

    # Rahu in 5H or 11H = unexpected gains potential
    rahu_h = _planet_house(planets, "Rahu")
    if rahu_h in (5, 11):
        score += 2
        why.append(f"Rahu in {rahu_h}H → +2 unconventional windfall potential")

    # Vipareeta link: 6L in 8 or 12 (one is enough)
    sixth_lord = _house_lord(intel, 6)
    eighth_lord = _house_lord(intel, 8)
    twelfth_lord = _house_lord(intel, 12)
    for role, lord in (("6L", sixth_lord), ("8L", eighth_lord),
                       ("12L", twelfth_lord)):
        if not lord:
            continue
        h = _planet_house(planets, lord)
        if h in (6, 8, 12) and h != intel.get("lagna_sign", 0):
            # Just needs to be in dushtana different from native house
            score += 1
            why.append(f"Vipareeta link: {role} ({lord}) in {h}H → +1")
            break

    # KP 5H CSL signifying 2/11
    if kp:
        cusps = kp.get("cusps") or []
        csl_5 = None
        for c in cusps:
            if isinstance(c, dict) and c.get("house") == 5:
                csl_5 = c.get("subLord") or c.get("sub_lord") or c.get("sl")
                break
        if csl_5:
            sigs = _planet_significates_houses(kp, csl_5)
            if sigs & {2, 11}:
                score += 1
                why.append(f"KP 5H CSL ({csl_5}) signifies dhana → "
                           f"+1 unexpected-income trigger")

    why.append("⚠ ENGINE RULE: NEVER endorse lottery / satta / KBC / matka / "
               "jackpot. Sudden-windfall = unexpected legitimate income only "
               "(bonus, inheritance, surprise client, royalty).")

    return {"cond": "C5_sudden_windfall", "score": score, "why": why}


# ─────────────────────────────────────────────────────────────────────────────
# REMEDY BUNDLES — wealth focus
# ─────────────────────────────────────────────────────────────────────────────
_REMEDY_BY_PLANET_WEALTH = {
    "Sun": {
        "mantra":    "Om Suryaya Namah (108x daily, Sunday morning at sunrise)",
        "donation":  "Wheat, jaggery, copper coin to needy on Sundays",
        "lifestyle": "Govt/authority work focus; offer water to Sun daily; "
                     "father-respect (his blessings strengthen wealth karma).",
    },
    "Moon": {
        "mantra":    "Om Chandraya Namah (108x daily, Monday)",
        "donation":  "Rice, milk, white cloth, silver to needy on Mondays",
        "lifestyle": "Liquid-cash discipline; mother-respect; Monday fast "
                     "improves cash-flow karma.",
    },
    "Mars": {
        "mantra":    "Om Mangalaya Namah (108x daily, Tuesday morning) + "
                     "Hanuman Chalisa Tuesday/Saturday",
        "donation":  "Red lentils (masoor), copper, jaggery on Tuesdays",
        "lifestyle": "Property/real-estate work suits; sibling-respect; "
                     "avoid impulsive financial decisions during Mars retro.",
    },
    "Mercury": {
        "mantra":    "Om Budhaya Namah (108x daily, Wednesday)",
        "donation":  "Green moong dal, green cloth, books on Wednesdays",
        "lifestyle": "Business / trade / writing-income focus; daily ledger "
                     "maintenance; Wed fast improves business karma.",
    },
    "Jupiter": {
        "mantra":    "Om Brihaspataye Namah (108x daily, Thursday) + "
                     "Vishnu Sahasranama path",
        "donation":  "Yellow chana dal, turmeric, books, gold to "
                     "Brahmins/teachers on Thursdays",
        "lifestyle": "Dharmic earning ONLY (no shortcut/illegal money); "
                     "guru-respect; Thursday fast amplifies dhana-karaka grace.",
    },
    "Venus": {
        "mantra":    "Om Shukraya Namah (108x daily, Friday) + Lakshmi "
                     "Ashtakam Friday evening",
        "donation":  "Sugar, rice, white cloth, perfume to women on Fridays",
        "lifestyle": "Luxury-business suits; spouse-respect (spouse's "
                     "support amplifies wealth); Friday Lakshmi-puja.",
    },
    "Saturn": {
        "mantra":    "Om Shanaye Namah (108x daily, Saturday evening) + "
                     "Hanuman Chalisa",
        "donation":  "Black sesame (til), iron, mustard oil, black cloth "
                     "to needy on Saturdays",
        "lifestyle": "Hard-work + patience model wealth (no shortcut); "
                     "elder-respect; consistent saving discipline; "
                     "Sat evening Shani temple visit.",
    },
    "Rahu": {
        "mantra":    "Om Rahave Namah (108x daily) + Durga Saptashati path",
        "donation":  "Mixed grains, blue/black cloth, mustard oil to needy",
        "lifestyle": "Avoid speculation/gambling/get-rich-quick schemes; "
                     "ethical business only; foreign-source income suits.",
    },
    "Ketu": {
        "mantra":    "Om Ketave Namah (108x daily) + Ganesha Atharvashirsha",
        "donation":  "Multi-coloured cloth, blanket, sesame oil to needy",
        "lifestyle": "Detachment from money-anxiety; avoid impulsive "
                     "spending; spiritual/research-line income suits.",
    },
}


def _select_wealth_remedy(intel: dict, kundli: dict, karakas_d: dict,
                          layers: dict) -> dict:
    """Choose weakest dhana-related planet (2L, 11L, Jupiter, Venus, AmK,
    Lagnesh) and return its remedy bundle."""
    candidates = []
    second_lord = _house_lord(intel, 2)
    eleventh_lord = _house_lord(intel, 11)
    lagnesh = _house_lord(intel, 1)
    amk = karakas_d.get("AmK") or karakas_d.get("Amatyakaraka") or {}
    amk_planet = amk.get("planet") if isinstance(amk, dict) else amk

    for c in (second_lord, eleventh_lord, "Jupiter", "Venus",
              amk_planet, lagnesh):
        if c and c not in candidates:
            candidates.append(c)

    weakest = None
    weakest_rank = 999
    planets = kundli.get("planets") or []
    for pl in candidates:
        dgn = _planet_dignity(intel, pl)
        rank = DIGNITY_RANK.get(dgn, 2)
        penalty = 0
        if _is_combust(planets, pl):
            penalty += 1
        if _is_retrograde(planets, pl):
            # Retro on dhana planet = +ve in our scoring, but for remedy
            # selection treat as neutral (don't reduce rank)
            penalty -= 0
        adj = rank - penalty
        if adj < weakest_rank:
            weakest_rank = adj
            weakest = pl

    if not weakest:
        return {"remedy_planet": None,
                "remedy_text": "Weekly Lakshmi puja (Friday evening) + "
                               "monthly donation to needy + ethical-earning "
                               "discipline.",
                "details": {}}

    bundle = _REMEDY_BY_PLANET_WEALTH.get(weakest, {})
    text = (f"Strengthen {weakest} (your weakest dhana-significator): "
            f"{bundle.get('mantra','')}. "
            f"{bundle.get('lifestyle','')}.")
    return {
        "remedy_planet": weakest,
        "remedy_text":   text,
        "details":       bundle,
    }


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY + TIMING WINDOW + VERDICT FORMAT
# ─────────────────────────────────────────────────────────────────────────────

_VERDICT_HI = {
    "green_go":    "GREEN — Supportive wealth window, disciplined accumulation strategy execute karein",
    "yellow_wait": "YELLOW — Mixed signals, CA / financial-advisor consult karein, conservative approach",
    "slow_burn":   "SLOW BURN — Long-term wealth promise, patience + consistent saving zaroori",
    "red_avoid":   "RED — High-risk wealth window, defer major financial decisions, corpus protect karein",
}

_BUCKET_HI = {
    "salary_growth":       "Salary / Increment Growth",
    "business_profit":     "Business Profit / Revenue",
    "loan_clearance":      "Loan / Debt Clearance",
    "property_purchase":   "Property / Real-estate Buy",
    "investment_return":   "Investment Returns",
    "inheritance_timing":  "Inheritance / Joint-fund Timing",
    "debt_recovery":       "Debt Recovery (money owed to you)",
    "sudden_windfall":     "Unexpected Income (bonus/legitimate windfall)",
    "savings_capacity":    "Savings Capacity",
    "foreign_income":      "Foreign / Overseas Income",
    "partnership_finance": "Partnership / Joint Finance",
    "general_wealth":      "General Wealth / Dhana",
}


def _strategy_for_wealth(bucket: str, verdict: str) -> str:
    """One-line bucket-x-verdict Hinglish action."""
    if verdict == "green_go":
        base = {
            "salary_growth":       "Increment / appraisal cycle ka favourable window — performance metrics document karein, manager se 1-on-1 karein, market-rate research kar ke ask karein.",
            "business_profit":     "Revenue expansion ka strong window — new client outreach, pricing review, cash-flow forecasting tighten karein.",
            "loan_clearance":      "Loan-pre-payment ka favourable phase — extra EMI / lump-sum payment se principal reduce karein, refinancing options explore karein.",
            "property_purchase":   "Property-buy ka supportive window — RERA-registered project shortlist karein, legal title check, pre-approved loan EMI calculator se affordability confirm karein.",
            "investment_return":   "Investment / SIP ka constructive window — diversified portfolio (equity-debt-gold-real-estate) maintain karein, SEBI-registered advisor se asset allocation review karwa lein.",
            "inheritance_timing":  "Inheritance / joint-fund ka activation window — legal documentation tight rakhein, family communication transparent rakhein, taxation planning kar lein.",
            "debt_recovery":       "Money recovery ka strong window — written reminders, mediator/lawyer involvement, settlement-discount negotiation explore karein.",
            "sudden_windfall":     "Unexpected legitimate income (bonus/royalty/surprise client) ka window — immediate emergency-fund top-up + tax-efficient investment.",
            "savings_capacity":    "Savings discipline ka best phase — auto-debit SIP setup, expense tracking app, 50-30-20 rule (needs-wants-savings) follow karein.",
            "foreign_income":      "Overseas income / freelance / remote-work window — payment-gateway optimisation, FEMA compliance, NRE/NRO account setup if applicable.",
            "partnership_finance": "Partnership / joint-venture ka constructive window — written agreement, profit-share clarity, exit clause define karein pehle.",
            "general_wealth":      "Wealth-building ka supportive window — emergency fund (6 months expense), term insurance, health insurance, SIP discipline parallel run karein.",
        }
        return base.get(bucket,
                        "Cosmic wealth window supportive — disciplined "
                        "saving + qualified CA consult maintain karein.")
    if verdict == "yellow_wait":
        return ("Mixed signals — major financial decision se pehle qualified "
                "CA / SEBI-registered advisor se consult karein. Conservative "
                "approach, emergency fund top-up, debt-reduction prioritise karein.")
    if verdict == "slow_burn":
        return ("Long-term wealth promise hai but timing slow hai — "
                "consistent SIP, patience, and 3-5 year horizon zaroori. "
                "Quick-rich expectation rakh kar mat chalein. Disciplined "
                "saving + ethical earning compound karega.")
    if verdict == "red_avoid":
        return ("Currently high-risk wealth window hai — major investment, "
                "new loan, big property buy, business expansion defer karein. "
                "Existing corpus protect karein, expenses cut karein, "
                "emergency fund top-up karein. Yeh barbadi nahi — yeh "
                "extra-savitree period hai jab reset ke baad strong return aata hai.")
    return ("CA / financial-advisor se consult karein, disciplined saving + "
            "ethical earning pe focus karein.")


def _build_wealth_timing_window(kundli: dict, intel: dict,
                                jup_t: dict, sat_t: dict) -> dict:
    """Construct timing window dict from current dasha + Jupiter/Saturn
    transits. Mirror of health's _build_timing_window with wealth framing."""
    md, ad, pd = _dasha_lords(kundli)
    cur_start = ""
    cur_end = ""
    cd = kundli.get("currentDasha") or {}
    cur_start = (cd.get("startDate") or cd.get("start") or "")[:10]
    cur_end = (cd.get("endDate") or cd.get("end") or "")[:10]
    if not cur_start or not cur_end:
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).date().isoformat()
            for top in (kundli.get("dashas") or []):
                if top.get("planet") != md:
                    continue
                for sub in (top.get("subDashas") or []):
                    if sub.get("planet") != ad:
                        continue
                    if (str(sub.get("startDate", "")) <= now <=
                            str(sub.get("endDate", "9999"))):
                        cur_start = str(sub.get("startDate", ""))[:10]
                        cur_end = str(sub.get("endDate", ""))[:10]
                        break
                break
        except Exception:
            pass

    nxt_md, nxt_ad, nxt_start, nxt_end, why_nxt = "", "", "", "", ""
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).date().isoformat()
        seen_current = False
        for top in (kundli.get("dashas") or []):
            for sub in (top.get("subDashas") or []):
                s = str(sub.get("startDate", ""))[:10]
                e = str(sub.get("endDate", ""))[:10]
                if not s or not e:
                    continue
                if not seen_current and s <= now <= e:
                    seen_current = True
                    continue
                if seen_current and s > now:
                    nxt_md = top.get("planet")
                    nxt_ad = sub.get("planet")
                    nxt_start = s
                    nxt_end = e
                    why_nxt = (f"Next AD: {nxt_md}/{nxt_ad} "
                               f"({_ym_to_human(s[:7])} → "
                               f"{_ym_to_human(e[:7])})")
                    break
            if nxt_ad:
                break
    except Exception:
        pass

    # Wealth-specific window: jupiter / saturn transit highlight
    risk_str = ""
    risk_reason = ""
    if jup_t:
        jh = jup_t.get("jupiter_house_from_lagna")
        if jh in (2, 11):
            risk_str = f"Jupiter transit {jh}H (active now)"
            risk_reason = ("Wealth-grace window — accumulation / "
                           "income amplification phase.")
        elif jh in (5, 9):
            risk_str = f"Jupiter transit {jh}H (active now)"
            risk_reason = "Bhagya / poorva-punya activation for wealth."
    if not risk_str and sat_t:
        if sat_t.get("sade_sati_phase") in ("peak", "ashtama"):
            risk_str = f"Saturn {sat_t.get('sade_sati_phase')} (active now)"
            risk_reason = ("Cash-flow restructure window — savings "
                           "discipline ka extra zoor.")
        elif sat_t.get("saturn_house_from_lagna") == 2:
            risk_str = "Saturn transit 2H (active now)"
            risk_reason = "Saved-money under restructure — cut wasteful expenses."

    return {
        "current": {
            "md": md, "ad": ad, "pd": pd,
            "start": cur_start, "end": cur_end,
            "lords": f"{md}/{ad}" if (md and ad) else (md or ad or ""),
        },
        "next": {
            "md": nxt_md, "ad": nxt_ad,
            "start": nxt_start, "end": nxt_end,
            "why": why_nxt,
        },
        "risk": {"window_str": risk_str, "reason": risk_reason},
    }


# ─────────────────────────────────────────────────────────────────────────────
# ASSESS_WEALTH — main orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def assess_wealth(kundli: dict,
                  intel: dict,
                  kp: Optional[dict] = None,
                  birth: Optional[dict] = None,
                  question: str = "",
                  pre_classified_bucket: str | None = None) -> dict:
    """Full deterministic wealth verdict. Returns dict with:
      bucket            — one of 12 wealth buckets
      tense             — future / present / general
      verdict           — green_go / yellow_wait / slow_burn / red_avoid
      score, confidence — 0-100
      score_breakdown   — layer/trigger/modifier/cond split
      strategy          — Hinglish action verbatim
      timing_window     — { current, next, risk }
      remedy            — weakest-planet remedy bundle
      brand_safety_warnings — list of bullets narrator MUST honour
      layers/triggers/modifiers/conditionals — full audit trail
    """
    bucket = classify_wealth_question(question, pre_classified_bucket)
    tense  = detect_question_tense(question)
    intel = intel or {}
    kp = kp or {}
    birth = birth or {}

    asc = kundli.get("ascendant") or {}
    lagna_sign = (asc.get("sign") if isinstance(asc, dict) else None) or \
                 intel.get("lagna_sign")
    lagna_idx = _sign_idx(lagna_sign) if lagna_sign else 0
    if lagna_idx < 0:
        lagna_idx = 0
    moon_sign = kundli.get("moonSign") or _planet_sign(
        kundli.get("planets") or [], "Moon")
    moon_idx = _sign_idx(moon_sign) if moon_sign else -1

    # Lazy-load helpers
    sb = _maybe_shadbala(kundli, lagna_idx)
    av = _maybe_ashtakavarga(kundli, lagna_idx)
    bb = _maybe_bhava_bala(intel, sb)
    karakas_d = _maybe_karakas(kundli)
    yogas_d = _maybe_varga_yogas(
        kundli, _planet_lon(kundli.get("planets") or [], "Asc"))
    jup_t = _maybe_jupiter_transit(
        lagna_idx, moon_idx if moon_idx >= 0 else None)
    sat_t = _maybe_saturn_transit_wealth(
        lagna_idx, moon_idx if moon_idx >= 0 else None)

    # ── A. Natal layers (L1-L15) ────────────────────────────────────────────
    L = {}
    L["L1"]  = _layer_second_house(intel, kundli)
    L["L2"]  = _layer_eleventh_house(intel, kundli)
    L["L3"]  = _layer_fifth_house(intel, kundli)
    L["L4"]  = _layer_ninth_house(intel, kundli)
    L["L5"]  = _layer_fourth_house(intel, kundli)
    L["L6"]  = _layer_eighth_house_wealth(intel, kundli)
    L["L7"]  = _layer_twelfth_house_wealth(intel, kundli)
    L["L8"]  = _layer_sixth_house_wealth(intel, kundli)
    L["L9"]  = _layer_jupiter_dhana_karaka(intel, kundli)
    L["L10"] = _layer_venus_luxury(intel, kundli)
    L["L11"] = _layer_mercury_business(intel, kundli)
    L["L12"] = _layer_moon_cashflow(intel, kundli)
    L["L13"] = _layer_sun_authority_income(intel, kundli)
    L["L14"] = _layer_jaimini_dhana_karaka(karakas_d, intel, kundli)
    L["L15"] = _layer_lagna_bhava_aspect_wealth(intel, kundli)

    # ── B. Divisional + KP (L16-L19) ────────────────────────────────────────
    L["L16"] = _layer_d9_overlay_wealth(kundli, intel, karakas_d)
    L["L17"] = _layer_d2_hora_overlay(kundli, intel)
    L["L18"] = _layer_d11_labha_overlay(kundli, intel)
    L["L19"] = _layer_kp_csl_wealth(kp)

    # ── C. Strength (L20-L22) ───────────────────────────────────────────────
    L["L20"] = _layer_ashtakavarga_wealth(av)
    L["L21"] = _layer_shadbala_wealth(sb, intel)
    L["L22"] = _layer_bhava_bala_wealth(bb)

    # ── D. Yogas (L23-L25) ──────────────────────────────────────────────────
    L["L23"] = _layer_dhana_yogas(yogas_d, intel, kundli)
    L["L24"] = _layer_daridra_yogas(yogas_d, intel, kundli)
    L["L25"] = _layer_sade_sati_wealth(intel, kundli)

    layer_score = sum(L[k].get("score", 0) for k in L)

    # ── E. Triggers ─────────────────────────────────────────────────────────
    T = {}
    T["T1"] = _trigger_vimshottari_wealth(kundli, intel, karakas_d)
    T["T2"] = _trigger_jupiter_transit_wealth(jup_t, intel, kundli)
    T["T3"] = _trigger_saturn_transit_wealth(sat_t, intel, kundli)
    trigger_score = sum(T[k].get("score", 0) for k in T)

    # ── F. Modifiers ────────────────────────────────────────────────────────
    M = {}
    M["M1"] = _modifier_combust_wealth(intel, kundli)
    M["M2"] = _modifier_retrograde_wealth(intel, kundli)
    M["M3"] = _modifier_malefic_aspects_wealth(intel, kundli)
    M["M4"] = _modifier_dignity_jupiter_venus(intel)
    M["M5"] = _modifier_vargottama_lift(kundli, intel)
    M["M6"] = _modifier_parivartana_dhana(intel, kundli)
    M["M7"] = _modifier_neecha_bhanga_dhana(intel, kundli)
    M["M8"] = _modifier_sade_sati_dhana_lords(intel, kundli)
    modifier_delta = sum(m.get("delta", 0) for m in M.values())

    # ── G. Conditionals (only those matching bucket) ────────────────────────
    conditionals = {}
    if bucket in ("loan_clearance", "debt_recovery"):
        conditionals["C1"] = _conditional_loan_clear(intel, kundli, sat_t)
    if bucket == "property_purchase":
        conditionals["C2"] = _conditional_property_buy(intel, kundli, jup_t)
    if bucket in ("investment_return", "partnership_finance"):
        conditionals["C3"] = _conditional_investment_return(
            intel, kundli, kp)
    if bucket == "inheritance_timing":
        conditionals["C4"] = _conditional_inheritance(
            intel, kundli, karakas_d)
    if bucket == "sudden_windfall":
        conditionals["C5"] = _conditional_sudden_windfall(intel, kundli, kp)
    cond_bonus = sum(c.get("score", 0) for c in conditionals.values())

    # ── Total score (weighted, normalised to 0-100) ─────────────────────────
    raw = layer_score + trigger_score + modifier_delta + cond_bonus
    # Layer max ≈ 209 (computed)
    # Trigger max ≈ 12+7+6 = 25
    LAYER_MAX = 209
    TRIGGER_MAX = 25
    normalised = 50 + (raw / (LAYER_MAX + TRIGGER_MAX) * 50)
    total_score = int(max(0, min(100, normalised)))

    # ── Verdict resolution ──────────────────────────────────────────────────
    trigger_active = trigger_score > 2
    if total_score >= 65 and trigger_active:
        verdict = "green_go"
    elif total_score >= 55:
        verdict = "yellow_wait"
    elif total_score >= 40:
        verdict = "slow_burn"
    else:
        verdict = "red_avoid"
    # Tense override: PRESENT + weak trigger → yellow not green
    if tense == "present" and trigger_score < 3 and verdict == "green_go":
        verdict = "yellow_wait"
    # Bucket-specific clamps
    if bucket == "sudden_windfall":
        # Never red — protect brand from "no windfall ever" doom
        if verdict == "red_avoid":
            verdict = "slow_burn"

    # Confidence
    agreement_signals = 0
    if L["L19"].get("score", 0) != 0: agreement_signals += 1   # KP active
    if L["L16"].get("score", 0) != 0: agreement_signals += 1   # D9 active
    if L["L17"].get("score", 0) != 0: agreement_signals += 1   # D2 Hora
    if L["L18"].get("score", 0) != 0: agreement_signals += 1   # D11 Labha
    if T["T1"].get("score", 0) != 0:  agreement_signals += 1   # Dasha active
    if av: agreement_signals += 1
    if sb: agreement_signals += 1
    confidence = min(95, 55 + agreement_signals * 6)

    # ── Strategy ────────────────────────────────────────────────────────────
    strategy = _strategy_for_wealth(bucket, verdict)

    # ── Timing window ───────────────────────────────────────────────────────
    timing_window = _build_wealth_timing_window(kundli, intel, jup_t, sat_t)

    # ── Remedy ──────────────────────────────────────────────────────────────
    remedy = _select_wealth_remedy(intel, kundli, karakas_d, L)

    # ── Top concerns + supportive ───────────────────────────────────────────
    layer_planet_signals = []
    for k, ld in L.items():
        if ld.get("score", 0) <= -3:
            layer_planet_signals.append(
                (ld.get("score", 0), k, ld.get("layer", k)))
    layer_planet_signals.sort()
    top_concerns = [{"layer": s[2], "score": s[0]}
                    for s in layer_planet_signals[:3]]

    layer_supportive = []
    for k, ld in L.items():
        if ld.get("score", 0) >= 4:
            layer_supportive.append(
                (ld.get("score", 0), k, ld.get("layer", k)))
    layer_supportive.sort(reverse=True)
    top_supportive = [{"layer": s[2], "score": s[0]}
                      for s in layer_supportive[:3]]

    # ── Brand-safety warnings (bucket-driven + verdict-driven) ──────────────
    warnings = list(_brand_safety_warnings(bucket))
    if verdict == "red_avoid":
        warnings.append(
            "Currently major financial decisions (new loan, big investment, "
            "property buy, business expansion) defer karein. Existing corpus "
            "protect karein — yeh extra-savitree phase hai, barbadi nahi."
        )
    if bucket in _HIGH_RISK_BUCKETS:
        warnings.append(
            "Investments market risk ke adheen hain — scheme documents "
            "carefully padein, SEBI-registered advisor se consult karein, "
            "diversification + risk-tolerance match karein."
        )
    warnings = warnings[:8]

    # ── Reasons audit (top facts) ───────────────────────────────────────────
    reasons = []
    for k in L:
        for w in (L[k].get("why") or []):
            reasons.append(w)
    for k in T:
        for w in (T[k].get("why") or []):
            reasons.append(w)
    for k, c in conditionals.items():
        for w in (c.get("why") or []):
            reasons.append(w)
    for k, m in M.items():
        for w in (m.get("why") or []):
            reasons.append(w)

    return {
        "bucket":               bucket,
        "tense":                tense,
        "verdict":              verdict,
        "score":                total_score,
        "confidence":           confidence,
        "score_breakdown": {
            "layer_score":      layer_score,
            "trigger_score":    trigger_score,
            "modifier_delta":   modifier_delta,
            "cond_bonus":       cond_bonus,
        },
        "strategy":             strategy,
        "timing_window":        timing_window,
        "remedy":               remedy,
        "top_concerns":         top_concerns,
        "top_supportive":       top_supportive,
        "brand_safety_warnings": warnings,
        "layers":               L,
        "triggers":             T,
        "modifiers":            M,
        "conditionals":         conditionals,
        "reasons":              reasons,
    }


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT VERDICT FOR PROMPT — narrator-locked block
# ─────────────────────────────────────────────────────────────────────────────

def format_verdict_for_prompt(v: dict, question: str = "") -> str:
    """Build the LOCKED-FACTS block that the AI narrator MUST embed verbatim
    (no wording changes, no number changes, no verdict changes).
    Brand-safety bullets at the bottom are MANDATORY for the narrator to honour."""
    if not isinstance(v, dict):
        return "(wealth verdict unavailable)"

    bucket = v.get("bucket", "general_wealth")
    tense  = v.get("tense", "general")
    verdict = v.get("verdict", "yellow_wait")
    score = v.get("score", 0)
    confidence = v.get("confidence", 0)

    bucket_hi = _BUCKET_HI.get(bucket, bucket)
    verdict_hi = _VERDICT_HI.get(verdict, verdict)

    lines = []
    lines.append("════════════════════════════════════════════════════════════")
    lines.append("⭐ COSMIC WEALTH VERDICT — LOCKED FACTS (do NOT modify)")
    lines.append("════════════════════════════════════════════════════════════")
    lines.append(f"▸ QUESTION TYPE: {bucket_hi}  ({bucket})")
    lines.append(f"▸ QUESTION TENSE: {tense.upper()}")
    lines.append(f"▸ VERDICT: {verdict_hi}")
    lines.append(f"▸ COSMIC SCORE: {score}  |  CONFIDENCE: {confidence}%")
    lines.append("")

    # Score breakdown
    sb = v.get("score_breakdown") or {}
    if sb:
        lines.append("▸ SCORE BREAKDOWN:")
        lines.append(f"   • Natal layers (25): {sb.get('layer_score',0):+d}")
        lines.append(f"   • Trigger layers (3): {sb.get('trigger_score',0):+d}")
        lines.append(f"   • Modifiers (8): {sb.get('modifier_delta',0):+d}")
        lines.append(f"   • Conditionals: {sb.get('cond_bonus',0):+d}")
        lines.append("")

    # Top reasons
    reasons = v.get("reasons") or []
    top_reasons = [r for r in reasons if "⭐" in r or "Vargottama" in r
                   or "MANDATORY" in r or "vargottama" in r
                   or "Parivartana" in r or "Vipareeta" in r
                   or "Dhana Yoga" in r or "Lakshmi" in r][:5]
    if not top_reasons:
        top_reasons = reasons[:5]
    if top_reasons:
        lines.append("▸ TOP COSMIC FACTORS:")
        for r in top_reasons:
            lines.append(f"   • {r}")
        lines.append("")

    # Timing window — narrator MUST cite the heading line verbatim
    tw = v.get("timing_window") or {}
    cur = tw.get("current") or {}
    nxt = tw.get("next") or {}
    risk = tw.get("risk") or {}

    if cur.get("md") and cur.get("ad"):
        cur_s_h = _ym_to_human(str(cur.get("start") or "")[:7])
        cur_e_h = _ym_to_human(str(cur.get("end") or "")[:7])
        # CRITICAL: heading regex `(marriage|career|...|wealth) window:` —
        # MUST emit lower-case "wealth window:" so validator detects it.
        if cur_s_h and cur_e_h:
            lines.append(
                f"▸ Wealth window: {cur_s_h} → {cur_e_h} — "
                f"{cur.get('md')} Mahadasha / {cur.get('ad')} Antardasha"
            )
        else:
            lines.append(
                f"▸ Wealth window: {cur.get('md')} Mahadasha / "
                f"{cur.get('ad')} Antardasha (active now)"
            )
        # Aliases narrator can echo (dhana/loan/property/inheritance)
        lines.append(
            f"   (alias: dhana window / loan window / property window / "
            f"inheritance window — same dates)"
        )

    if nxt.get("md") and nxt.get("ad"):
        nxt_s_h = _ym_to_human(str(nxt.get("start") or "")[:7])
        nxt_e_h = _ym_to_human(str(nxt.get("end") or "")[:7])
        lines.append(
            f"▸ Next wealth window: {nxt_s_h} → {nxt_e_h} — "
            f"{nxt.get('md')} Mahadasha / {nxt.get('ad')} Antardasha"
        )

    if risk.get("window_str"):
        lines.append(
            f"▸ Active wealth event: {risk.get('window_str')} — "
            f"{risk.get('reason','')}"
        )
    lines.append("")

    # Strategy (verbatim)
    strat = v.get("strategy") or ""
    if strat:
        lines.append("▸ STRATEGY (use VERBATIM in answer):")
        lines.append(f"   « {strat} »")
        lines.append("")

    # Remedy
    rem = v.get("remedy") or {}
    if rem.get("remedy_text"):
        lines.append(f"▸ REMEDY: {rem.get('remedy_text')}")
        lines.append("")

    # Brand safety warnings
    warnings = v.get("brand_safety_warnings") or []
    if warnings:
        lines.append("▸ BRAND-SAFETY GUARDS (narrator MUST honour as caveats):")
        for w in warnings:
            lines.append(f"   • {w}")
        lines.append("")

    lines.append("════════════════════════════════════════════════════════════")
    lines.append("⛔ NARRATOR RULES (WEALTH — STRICT):")
    lines.append("   1. Do NOT change verdict, score, confidence, lords, or windows.")
    lines.append("   2. NEVER predict a specific rupee amount (₹X lakh / ₹X crore "
                 "/ X% return / specific package) — even if user asks. "
                 "Decline + redirect to qualitative band.")
    lines.append("   3. NEVER predict bankruptcy, 'kangaal ho jaoge', 'sab "
                 "kuch lut jaayega' — soften red verdict to 'extra-savitree "
                 "period, corpus protect karein'.")
    lines.append("   4. NEVER advise EMI default, loan skip, GST evasion, "
                 "tax fraud, or any illegal financial behaviour.")
    lines.append("   5. NEVER endorse lottery / satta / KBC / matka / jackpot — "
                 "engine NEVER promises gambling wins.")
    lines.append("   6. ALWAYS recommend qualified CA / SEBI-registered "
                 "financial advisor consult — cosmic guidance is not a "
                 "vikalp for professional financial advice.")
    lines.append("   7. For investment/business/partnership/windfall buckets — "
                 "MANDATORY SEBI-style line: 'Investments market risk ke "
                 "adheen hain.'")
    lines.append("   8. Frame in TENSE detected above (PRESENT → 'abhi/aaj kal'; "
                 "FUTURE → 'aage chal kar').")
    lines.append("   9. Use 'Cosmic Intelligence' / 'cosmic signature' — "
                 "NEVER 'AI/LLM'.")
    lines.append("  10. Embed STRATEGY text verbatim (translate keywords only "
                 "if needed).")
    lines.append("  11. Honour ALL brand-safety bullets above as caveats.")
    lines.append("  12. Hinglish-first — natural code-mix preferred over pure "
                 "Hindi or pure English.")
    lines.append("════════════════════════════════════════════════════════════")

    return "\n".join(lines)


def format_final_answer(v: dict, question: str = "") -> str:
    """Compact pre-baked Hinglish answer for fallback when narrator
    unavailable."""
    if not isinstance(v, dict):
        return ("Cosmic Intelligence se wealth guidance abhi available nahi hai.")
    bucket = v.get("bucket", "general_wealth")
    verdict = v.get("verdict", "yellow_wait")
    score = v.get("score", 0)
    bucket_hi = _BUCKET_HI.get(bucket, bucket)
    verdict_hi = _VERDICT_HI.get(verdict, verdict)
    strat = v.get("strategy") or ""
    rem = v.get("remedy") or {}
    rem_text = rem.get("remedy_text") or ""
    tw = v.get("timing_window") or {}
    cur = tw.get("current") or {}
    win_line = ""
    if cur.get("md") and cur.get("ad"):
        s_h = _ym_to_human(str(cur.get("start") or "")[:7])
        e_h = _ym_to_human(str(cur.get("end") or "")[:7])
        if s_h and e_h:
            win_line = (f"Wealth window: {s_h} → {e_h} — "
                        f"{cur.get('md')} Mahadasha / "
                        f"{cur.get('ad')} Antardasha.")

    parts = [
        f"💰 Cosmic Wealth View ({bucket_hi}):",
        f"Verdict: {verdict_hi}  •  Score: {score}/100.",
        win_line,
        strat,
        f"Remedy: {rem_text}" if rem_text else "",
        ("⚠ Yeh guidance qualified CA / SEBI-registered financial advisor "
         "ki salah ka VIKALP NAHI hai — major financial decision se pehle "
         "professional consult zaroor karein."),
    ]
    return "\n\n".join([p for p in parts if p])


# ─────────────────────────────────────────────────────────────────────────────
# T3 boundary — wiring (T4) + bench (T5) come next.
# ─────────────────────────────────────────────────────────────────────────────

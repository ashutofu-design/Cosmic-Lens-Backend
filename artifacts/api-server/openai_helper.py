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
    r"mutual[- ]?funds?|sip|lump[- ]?sum|invest(or|ing|ment)|"
    r"share[- ]?bazar|stock[- ]?bazar|shaire[- ]?bazaar|shaire[- ]?bazar)\b"
    r"|f&o|F&O"
    r"|शेयर|शेयर बाज़ार|निवेश)",
    __import__("re").IGNORECASE,
)


def _is_stock_question(text: str) -> bool:
    """True iff text matches the stock-engine trigger gate."""
    if not isinstance(text, str) or not text.strip():
        return False
    return bool(_STOCK_QUESTION_RX.search(text))


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


# Lazy client so import does not crash if the SDK is missing in dev.
_client = None
_client_err: str | None = None


def _get_client():
    global _client, _client_err
    if _client is not None or _client_err is not None:
        return _client
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        _client_err = "OPENAI_API_KEY missing"
        return None
    try:
        from openai import OpenAI
        timeout = float(os.environ.get("OPENAI_TIMEOUT", "30"))
        _client = OpenAI(api_key=api_key, timeout=timeout)
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
    try:
        from locked_facts import build_locked_facts  # type: ignore
        locked_facts_str = build_locked_facts(kundli, birth) or ""
    except Exception as exc:
        print(f"[openai_helper] locked_facts failed: {exc}")

    # ── Sprint-52 RAG: classical knowledge retrieval (OPINION questions only) ─
    # Timing questions get ZERO RAG (engine block already gives the answer).
    # Opinion questions ("job vs business?", "career kya?", "nature kaisa?")
    # get top-5 chunks from vedic/knowledge/*.md to ground reasoning.
    rag_context_str = ""
    try:
        from vedic.validator.timing_validator import is_timing_question  # type: ignore
        if question and not is_timing_question(question):
            from vedic.rag.retriever import retrieve_and_format  # type: ignore
            rag_context_str = retrieve_and_format(question, k=5, max_chars=3500)
    except Exception as exc:  # noqa: BLE001
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
    if (topic in ("finance", "general")
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
            stock_verdict_obj = assess_stock(
                kundli, intel_obj or {}, kp_dict_s or {}, birth, question)
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
            love_verdict_obj = assess_love(
                kundli, intel_obj or {}, kp_dict_l or {}, birth, question)
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
        "    🛡️ DIVISIONAL CHARTS (Rule K): For MARRIAGE questions, MUST consult D9 NAVAMSA — specifically '7L lands in X — STRONG/EXALTED/DEBILITATED' line. The 7L's D9 strength is THE strongest predictor of marriage quality (overrides natal D1 if they conflict). For CAREER questions, MUST consult D10 DASAMSA — '10L lands in X' line is the equivalent. Vargottama planets (D1=D9 or D1=D10) act as if exalted — call them out by name. Cite naturally: 'D9 mein aapka 7L Mercury Pisces (debilitated) jaata hai — isliye natal weakness D9 mein bhi confirm hoti hai, marriage mein patience zaroori.' OR 'D10 mein aapka 10L Mercury Sagittarius (own-sign) jaata hai — career line strong support karta hai D10 mein.' If D9/D10 block missing, do NOT invent positions.\n"
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
        "10) ⚠️ STRICT BREVITY — HARD LIMIT ⚠️\n"
        "    • TOTAL answer = 100 to 140 WORDS. NEVER more. Count words as you write.\n"
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
    if marriage_verdict_block:
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
        reminder_lines.append(
            "• Marriage question: you MUST cite the 7L's D9 placement from the "
            "DIVISIONAL CHARTS block (one line, e.g. 'D9 mein 7L Mercury Pisces "
            "debilitated jaata hai — natal weakness D9 mein bhi confirm hoti hai')."
        )
    if topic == "career" and has_d10:
        reminder_lines.append(
            "• Career question: you MUST cite the 10L's D10 placement from the "
            "DIVISIONAL CHARTS block (one line, e.g. 'D10 mein 10L Mercury Sagittarius "
            "own-sign mein jaata hai — career line strong support karta hai D10 mein')."
        )

    if reminder_lines:
        msgs.append({
            "role": "system",
            "content": (
                "🔔 FINAL REMINDERS — read these LAST before composing your reply:\n"
                + "\n".join(reminder_lines)
                + "\n\nThese are MANDATORY citations for this turn. They sit ABOVE "
                  "the brevity rule — if Rule 10 (140-word cap) and these reminders "
                  "conflict, trim the prose, NOT the citations."
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
    if love_verdict_block:
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
    r"\b\d+\s*[\+\-\*\/×x]\s*\d+\b",
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


def _classify_marriage_subtype(question: str) -> str:
    """Return 'timing' / 'remedy' / 'analysis' / 'general'."""
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


def _scrub_brand_tone(text: str) -> str:
    """Strip AI-style phrases that break the human-Pandit illusion."""
    if not text:
        return text
    out = text
    for rx, repl in _TONE_SCRUB_PATTERNS:
        out = rx.sub(repl, out)
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
    # ── Brand-safety: refuse off-topic / fortune-telling questions WITHOUT
    # calling the LLM at all. Cheap, deterministic, never leaks chart data.
    if _is_brand_unsafe(question):
        eff_lang = _resolve_response_lang(question, lang, preferred_language)
        msg = _BRAND_SAFE_REDIRECT.get(eff_lang) or _BRAND_SAFE_REDIRECT["hn"]
        return {
            "text":       msg,
            "topic":      "off_topic",
            "confidence": 1.0,
            "source":     "brand_guard",
            "follow_ups": _derive_follow_ups("general", _resolve_response_lang(question, lang, preferred_language)),
        }

    # ── Fail-safe: if no kundli planets at all AND this is a personal
    # prediction question (astro mode), never call the LLM. The spec demands
    # "DO NOT GUESS" — invented planet positions are the worst possible
    # failure mode for an astrology app's credibility. General-mode concept
    # questions ("kp vs vedic kya hai") don't need a chart and skip this.
    has_planets = isinstance(kundli, dict) and bool(kundli.get("planets"))
    _early_mode, _early_reason = _classify_mode_with_reason(question)
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
        _t = _classify_topic(question)
        return {
            "text":       no_chart_msg,
            "topic":      _t,
            "confidence": 0.0,
            "source":     "no_chart_failsafe",
            "follow_ups": _derive_follow_ups(_t, eff_lang),
        }

    client = _get_client()
    if client is None:
        raise RuntimeError(_client_err or "OpenAI client not configured")

    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")

    topic = _classify_topic(question)
    mode, mode_reason = _classify_mode_with_reason(question)
    _trace(req_id, "2.MODE_DETECT", {
        "mode": mode, "topic": topic, "reason": mode_reason,
        "follow_up_inherits_mode": False,
        "note": "mode is RECLASSIFIED every turn from current question only — "
                "history influences ONLY marriage topic-stickiness below",
    })

    # ── TOPIC STICKINESS for marriage follow-ups ─────────────────────────────
    # Constraint follow-ups like "uske baad batao" / "dusra time chahiye" AND
    # generic followups like "aur detail mein batao" / "iska upay batao" don't
    # contain marriage keywords, so the classifier returns "general" and the
    # baked-answer path never fires — letting the AI hallucinate a fake date.
    # Force topic="marriage" when (a) constraint OR generic followup detected
    # AND (b) the prior assistant turn talked about vivah/shaadi/marriage.
    try:
        if topic != "marriage" and (
            _detect_marriage_constraint(question, history or [])
            or (_is_generic_followup(question)
                and _last_assistant_topic_was_marriage(history or []))
        ):
            for h in reversed(history or []):
                if (h.get("role") == "assistant"):
                    # Mobile client sends history as {role, text}; older callers
                    # may send {role, content}. Accept either to avoid silently
                    # missing the topic-stickiness signal on a follow-up.
                    prev = ((h.get("content") or h.get("text") or "")).lower()
                    if any(k in prev for k in
                           ("vivah", "shaadi", "shadi", "marriage",
                            "विवाह", "शादी", "spouse", "wife", "husband")):
                        topic = "marriage"
                        print("[ai_ask] topic stickiness: forced topic=marriage "
                              "(constraint detected on follow-up)")
                        break
    except Exception as exc:
        print(f"[ai_ask] topic-stickiness check failed: {exc}")

    # Marriage stickiness only matters in astro mode. In general mode, the
    # user is asking a concept/comparison question — no chart, no narrator.
    if mode == "general":
        topic = "general"

    # Marriage subtype: timing / remedy / analysis. Drives whether the locked
    # narrator template fires (timing/remedy) or AI does free chart analysis
    # (analysis). Only relevant when topic == marriage; harmless otherwise.
    marriage_subtype = (
        _classify_marriage_subtype(question) if topic == "marriage" else "timing"
    )
    _trace(req_id, "2.MODE_DETECT.subtype", {
        "topic": topic, "marriage_subtype": marriage_subtype,
    })

    build_meta: dict = {}
    messages = _build_messages(
        question, kundli, lang, reply_idx,
        birth=birth, topic=topic, history=history,
        preferred_language=preferred_language,
        mode=mode,
        out_meta=build_meta,
        marriage_subtype=marriage_subtype,
    )

    # ── Mode/topic-aware sampling ────────────────────────────────────────────
    # Marriage astro uses a deterministic verdict engine — AI is narrator only.
    if mode == "astro" and topic == "marriage":
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
    })

    def _call_once() -> str:
        try:
            r = client.chat.completions.create(
                model            = model,
                messages         = messages,
                temperature      = temperature,
                top_p            = 1,
                max_tokens       = _token_budget_for(topic, question),
                presence_penalty = presence_penalty,
                frequency_penalty= frequency_penalty,
            )
        except Exception as exc:
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc
        t = (r.choices[0].message.content or "").strip() if r.choices else ""
        if not t:
            raise RuntimeError("OpenAI returned empty response")
        return t

    text = _call_once()
    _trace(req_id, "4.RAW_AI_RESPONSE", text)

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
        # Best-effort extract of the topic-specific engine window line
        for _line in _facts_blob.splitlines():
            if "window:" in _line and any(t in _line for t in
                ("Marriage","Child","Career","Promotion","Wealth","Foreign","Property")):
                _engine_window = _line.strip(); break
        _lock = enforce_timing_lock(question or "", text, _facts_blob, _engine_window)
        if not _lock["ok"]:
            _trace(req_id, "4a.TIMING_VALIDATOR_REJECT", _lock["validation"])
            text = _lock["safe_text"]
        else:
            _trace(req_id, "4a.TIMING_VALIDATOR_OK", _lock["validation"])
    except Exception as _exc:  # noqa: BLE001
        _trace(req_id, "4a.TIMING_VALIDATOR_ERR", str(_exc))

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
    if (mode == "astro" and topic == "marriage"
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

    # ── Tone scrubber (always) — strip any blacklisted AI-style phrases.
    pre_scrub = text
    text = _scrub_brand_tone(text)
    if pre_scrub != text:
        _trace(req_id, "4d.SCRUBBER_CHANGED", {
            "before_preview": pre_scrub[:200],
            "after_preview":  text[:200],
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
    if topic == "marriage" and isinstance(kundli, dict) and kundli.get("planets"):
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
    if isinstance(kundli, dict) and kundli.get("planets"):
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
            if topic == "finance" and not _re.search(
                r"(?i)\bd[\-\s]?2\b|\bhora\b", text or ""
            ):
                _d2 = compute_d2(_planets_q, _lagna_lon)
                _s2 = summarize_d2_for_wealth(_d2) if _d2 else {}
                if _s2.get("verdict"):
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
    if isinstance(kundli, dict) and kundli.get("planets"):
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
            if _is_health_q and not _re2.search(
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
    if isinstance(kundli, dict) and kundli.get("planets"):
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
    if isinstance(kundli, dict) and kundli.get("planets"):
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

            if clauses:
                text = (text or "").rstrip() + (
                    f"\n\nDeep-strength signal: "
                    + "; ".join(clauses) + "."
                )
        except Exception as _exc:
            print(f"[ai_ask] varga deep (Sprint-12) post-inject failed: {_exc}")

    # Sprint-15 Rule W — DETERMINISTIC PER-VARGA YOGA INJECTION (last-resort).
    # If detected yogas are present and not cited, append the single most-relevant
    # one (priority: Pancha Mahapurusha > Raj > Vipreet).
    if isinstance(kundli, dict) and kundli.get("planets"):
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
    if isinstance(kundli, dict) and kundli.get("planets"):
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
    if isinstance(kundli, dict) and kundli.get("planets"):
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
    if isinstance(kundli, dict) and kundli.get("planets"):
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
    if isinstance(kundli, dict) and kundli.get("planets"):
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
                if not _reSN.search(r"(?i)sthira", text or ""):
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
                if not _reSN.search(r"(?i)niryana|shoola", text or ""):
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
    if isinstance(kundli, dict) and kundli.get("planets"):
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
            if _kw_topic and not _reAR.search(r"(?i)argala", text or ""):
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
    if isinstance(kundli, dict) and kundli.get("planets"):
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
            if _is_marriage_q and not _reUL.search(r"(?i)upapada|\bUL\b", text or ""):
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
    if isinstance(kundli, dict) and kundli.get("planets"):
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
            if _need_chara and not _re.search(r"(?i)chara dasha", text or ""):
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
                if _md:
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

    follow_ups = _derive_follow_ups(topic, eff_lang)
    _trace(req_id, "5.FINAL_OUTPUT", text)
    _trace(req_id, "6.FOLLOW_UPS", {
        "topic": topic, "lang": eff_lang, "items": follow_ups,
        "behavior": "follow-up chips are deterministic per (topic, lang); "
                    "the NEXT user turn is reclassified independently — "
                    "mode does NOT inherit from this turn",
    })
    return {
        "text":       text,
        "topic":      topic,
        "confidence": confidence,
        "source":     "openai",
        "follow_ups": follow_ups,
    }


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

    # Mode + topic classification — same logic as ai_ask.
    topic = _classify_topic(question)
    mode, mode_reason = _classify_mode_with_reason(question)
    _trace(req_id, "2.MODE_DETECT", {
        "mode": mode, "topic": topic, "reason": mode_reason,
        "follow_up_inherits_mode": False,
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

    client = _get_client()
    if client is None:
        raise RuntimeError(_client_err or "OpenAI client not configured")

    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    # Streaming path is only used for non-marriage astro turns (marriage and
    # general both branch to ai_ask oneshot above), so we don't need the
    # marriage facts meta here — but we still pass an empty out_meta for
    # forward-compat / parity with ai_ask.
    build_meta_stream: dict = {}
    marriage_subtype_stream = (
        _classify_marriage_subtype(question) if topic == "marriage" else "timing"
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

    final_text = _scrub_brand_tone(raw_text)
    if raw_text != final_text:
        _trace(req_id, "4d.SCRUBBER_CHANGED(stream)", {
            "before_preview": raw_text[:200],
            "after_preview":  final_text[:200],
        })
    if not final_text:
        raise RuntimeError("OpenAI returned empty after scrub")

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
    _trace(req_id, "5.FINAL_OUTPUT(stream)", final_text)
    _trace(req_id, "6.FOLLOW_UPS(stream)", {
        "topic": topic, "lang": eff_lang, "items": follow_ups,
        "behavior": "follow-up chips are deterministic per (topic, lang); "
                    "the NEXT user turn is reclassified independently — "
                    "mode does NOT inherit from this turn",
    })
    yield {
        "kind":       "final",
        "text":       final_text,
        "topic":      topic,
        "confidence": confidence,
        "source":     "openai_stream",
        "follow_ups": follow_ups,
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

"""
OpenAI helper for Cosmic Lens.

Single entry point: ai_ask(question, kundli, lang, reply_idx) -> dict

The helper builds a domain-locked Vedic astrology prompt, sends the user's
question + their kundli context to OpenAI, and returns a normalised dict
shaped like the rule-based ask_engine output so downstream code does not
need to branch.

Configuration:
- OPENAI_API_KEY  (required)  user-provided secret
- OPENAI_MODEL    (optional)  defaults to "gpt-4o-mini" for cost
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

    # ── DETERMINISTIC MARRIAGE VERDICT ────────────────────────────────────────
    # For topic == "marriage", we compute the verdict in pure Python BEFORE
    # the AI is invoked. The AI is then forbidden from changing verdict /
    # score / timeline / remedy — it is only a narrator.
    marriage_verdict_block = ""
    marriage_verdict_obj   = None
    marriage_baked_answer  = ""   # pre-composed final answer (Step A)
    marriage_use_alt       = False # constraint-aware: use next_alt_window (Step B)
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
                # ── Constraint detection: did the devotee reject the primary
                # window? ("yeh time nahi chahiye / next year batao / is date
                # ke baad / uske baad / dusra time / not this window …")
                marriage_use_alt = _detect_marriage_constraint(question, history or [])
                # Build the pre-baked answer in the resolved language; AI's
                # job collapses to "polish wording, do not change facts".
                from marriage_engine import format_final_answer  # type: ignore
                marriage_baked_answer = format_final_answer(
                    marriage_verdict_obj, lang_code=detected,
                    use_alt=marriage_use_alt,
                )
                print(f"[openai_helper] marriage verdict: "
                      f"verdict='{marriage_verdict_obj.get('verdict')}' "
                      f"score={marriage_verdict_obj.get('score')} "
                      f"kp={marriage_verdict_obj.get('kp_verdict')} "
                      f"use_alt={marriage_use_alt} "
                      f"window={marriage_verdict_obj.get('next_window')} "
                      f"alt_window={marriage_verdict_obj.get('next_alt_window')}")
        except Exception as exc:
            print(f"[openai_helper] marriage_engine failed: {exc}")

    focus     = _focus_block(topic)
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
    narrator_prefix = ""
    narrator_rules  = ""
    if marriage_verdict_block:
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

    # ── SINGLE-CALL MARRIAGE PATH ────────────────────────────────────────────
    # When we have a baked answer, the AI is reduced to a TONE polisher.
    # No chart context, no STRICT INSTRUCTIONS, no narrator override — the
    # facts are already final. This eliminates the validator-retry loop
    # because the model only has 4 short paragraphs to rephrase.
    if marriage_baked_answer:
        constraint_note = (
            "CONTEXT: the devotee just rejected the primary timing window. "
            "Acknowledge that gently in line 1, then deliver the next window from the answer below.\n\n"
        ) if marriage_use_alt else ""
        user = (
            f"{lang_lock_block}"
            f"{tone_blacklist}"
            f"{constraint_note}"
            "═══ FINAL ANSWER (you may ONLY polish wording for warm tone) ═══\n"
            f"{marriage_baked_answer}\n"
            "═════════════════════════════════════════════════════════════════\n\n"
            "STRICT POLISH RULES — read top-down. Violating ANY rule = wrong reply:\n"
            "  1. DO NOT change any verdict word, planet name, dasha name, date, year,\n"
            "     month, or remedy text. Copy them VERBATIM into your reply.\n"
            "  2. You MAY: smooth the phrasing into a natural expert voice; merge labels\n"
            "     (Vajah/Samay/Upay) into flowing sentences; translate non-fact words\n"
            f"    to the user's language ({lang_name}). NO guru/Pandit opener.\n"
            "  3. NO bullet points, NO numbered lists, NO markdown headers.\n"
            "  4. Total length 90–130 words across 3 short paragraphs.\n"
            "  5. NEVER write any of these phrases: \"I sense your concern\",\n"
            "     \"I understand\", \"based on your chart\", \"let me analyze\", \"Pranam\",\n"
            "     \"Beta\", \"Beta Q\", \"Dekhiye beta\", \"As an AI\". Speak naturally.\n"
            "  6. NEVER use hedging / uncertainty words. Acharya ji STATES, never speculates.\n"
            "     ✗ FORBIDDEN: chance, chances, possibility, possible, likely, unlikely,\n"
            "       may, might, perhaps, around, approx, approximately, roughly, early,\n"
            "       late, by the end of, ho sakta hai, ho sakti hai, ho sakte hain,\n"
            "       sambhavna, sambhavnayein, shayad, lagta hai, ho sakega, ho sakegi.\n"
            "     ✓ REQUIRED forms: \"hoga\", \"hogi\", \"honge\", \"yeh hi time hai\",\n"
            "       \"clear dikhta hai\", \"delay hoga\", \"yeh period active hai\",\n"
            "       \"isi me plan karein\".\n"
            "     The dates above are EXACT month-year — say them VERBATIM, never\n"
            "     reduce them to \"around 2026\" or \"late 2026\".\n"
            "  7. STYLE: open with \"Seedhi baat —\" or a direct factual line, then state the timing\n"
            "     as a fact. Three short paragraphs: (1) verdict + window, (2) reason\n"
            "     in 1–2 lines, (3) remedy in 1 line. Total 90–130 words.\n"
            f"\nDEVOTEE'S QUESTION (for tone matching only — do NOT re-answer it):\n\"{question}\"\n"
        )
        msgs: list[dict] = [{"role": "system", "content": system}]
        msgs.append({"role": "user", "content": user})
        return msgs

    user = (
        f"{lang_lock_block}"
        f"{tone_blacklist}"
        f"{narrator_prefix}"
        f"DEVOTEE'S BIRTH CHART:\n{chart_str}\n"
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
        "0a) ANTI-HALLUCINATION: You may ONLY mention planets, signs, houses, dignities, yogas, dashas, and transits that are EXPLICITLY listed in the BIRTH CHART, DERIVED CHART INTELLIGENCE, KP, or TRANSITS sections above. Never invent a planet placement, never guess a dasha, never claim a yoga that isn't in the 'Detected yogas' list. If a needed detail is missing, say so honestly — 'Beta, ye information aapki kundli mein abhi clear nahi, isliye iss point pe mai pakka nahi keh sakta.' Honesty > confidence.\n"
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
                    "investment", "share", "stock", "property", "lottery", "income", "tax", "loss",
                    "profit", "savings", "fixed deposit", "mutual fund", "crypto"],
    "health":      ["health", "illness", "disease", "swasthya", "bimari", "operation", "surgery",
                    "doctor", "hospital", "rog", "kasht", "dard", "pain", "tabiyat", "fever",
                    "diabetes", "blood pressure", "bp", "cancer", "heart", "depression", "anxiety",
                    "mental health", "stress"],
    "education":   ["study", "exam", "education", "padhai", "result", "college", "degree", "school",
                    "vidya", "graduation", "phd", "masters", "ias", "upsc", "neet", "jee", "gate",
                    "competitive", "scholarship", "admission"],
    "relationship":["love", "relationship", "girlfriend", "boyfriend", "breakup", "rishta", "rishtey",
                    "pyaar", "pyar", "ladka", "ladki", "dating", "crush", "ex", "love marriage",
                    "inter-caste", "family opposition"],
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
OUTPUT CONTROL
------------------------------------------

- Short paragraphs
- 80–120 words
- No long lecture
- No repetition

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

Never break character."""


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
# Hard refuse list: questions about external events the app must never engage
# with — sports/election/lottery/news predictions and similar fortune-telling.
_BRAND_UNSAFE_PATTERNS = [
    # sports / matches
    r"\b(match|cricket|ipl|world cup|t20|odi|football|fifa|nba|tournament)\b.*\b(jeet|win|kaun|who|result|score)",
    r"\b(jeet|win|kaun|who).*\b(match|cricket|ipl|world cup|t20|odi)\b",
    r"\b(india|pakistan|australia|england|sri lanka|new zealand|south africa)\s+(vs|v|versus)\s+\w+",
    # elections
    r"\b(election|chunav|vote|poll).*\b(jeet|win|kaun|who|result)",
    r"\b(modi|rahul|kejriwal|trump|biden).*\b(jeet|win|election)",
    # lottery / gambling
    r"\b(lottery|lucky number|jackpot|satta|matka|powerball)\b",
    r"\b(stock|share|crypto|bitcoin).*(price|prediction|tomorrow|kal)",
    # generic fortune-telling about others
    r"\bkaun (jeet|haar|marega|janega)",
    r"\bwho will (win|lose|die)",
]
_BRAND_UNSAFE_RE = [re.compile(p, re.IGNORECASE) for p in _BRAND_UNSAFE_PATTERNS]


def _is_brand_unsafe(question: str) -> bool:
    if not question:
        return False
    return any(rx.search(question) for rx in _BRAND_UNSAFE_RE)


_BRAND_SAFE_REDIRECT = {
    "en": ("Beta, jyotish is a guide to your own life-path — predicting match results, election outcomes, "
           "stock prices, or other external events is not what these classics teach. "
           "Please ask me about your marriage, career, health, family, or any matter from your own life — I'll guide you with full heart."),
    "hi": ("बेटा, ज्योतिष आपके अपने जीवन-पथ का मार्गदर्शन है — मैच, चुनाव, शेयर बाज़ार या बाहरी घटनाओं की भविष्यवाणी इसका कार्य नहीं। "
           "कृपया अपनी शादी, करियर, स्वास्थ्य, परिवार या जीवन से जुड़ा कोई प्रश्न पूछिए — मैं पूरे मन से उत्तर दूँगा।"),
    "hn": ("Beta, jyotish aapke khud ke jeevan-path ka margdarshan hai — match, election, stock-price, ya "
           "kisi bhi bahar ki ghatna ki bhavishyavani iska kaam nahi. "
           "Kripya apni shaadi, career, swasthya, parivar, ya jeevan se judi koi baat poochhein — main poore mann se uttar dunga."),
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

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    topic = _classify_topic(question)
    mode, mode_reason = _classify_mode_with_reason(question)
    _trace(req_id, "2.MODE_DETECT", {
        "mode": mode, "topic": topic, "reason": mode_reason,
        "follow_up_inherits_mode": False,
        "note": "mode is RECLASSIFIED every turn from current question only — "
                "history influences ONLY marriage topic-stickiness below",
    })

    # ── TOPIC STICKINESS for marriage follow-ups ─────────────────────────────
    # Constraint follow-ups like "uske baad batao" / "dusra time chahiye" don't
    # contain marriage keywords, so the classifier returns "general" and the
    # baked-answer path never fires — letting the AI hallucinate a fake date.
    # Force topic="marriage" when (a) constraint detected AND (b) the prior
    # assistant turn talked about vivah/shaadi/marriage timing.
    try:
        if topic != "marriage" and _detect_marriage_constraint(question, history or []):
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

    messages = _build_messages(
        question, kundli, lang, reply_idx,
        birth=birth, topic=topic, history=history,
        preferred_language=preferred_language,
        mode=mode,
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
                max_tokens       = 280,
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

    # ── Tone scrubber (always) — strip any blacklisted AI-style phrases.
    # The single-call marriage path uses a pre-baked, fact-locked answer from
    # marriage_engine.format_final_answer(), so no validator retry is needed:
    # the model is only polishing wording, not deciding facts.
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
        if mode == "astro" and topic != "marriage" and _detect_marriage_constraint(question, history or []):
            for h in reversed(history or []):
                if h.get("role") == "assistant":
                    prev = ((h.get("content") or h.get("text") or "")).lower()
                    if any(k in prev for k in
                           ("vivah", "shaadi", "shadi", "marriage",
                            "विवाह", "शादी", "spouse", "wife", "husband")):
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

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    messages = _build_messages(
        question, kundli, lang, reply_idx,
        birth=birth, topic=topic, history=history,
        preferred_language=preferred_language,
        mode=mode,
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
            max_tokens       = 280,
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
# All user-facing text is branded as "Cosmic Vision Engine".
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
    OpenAI failure. Branded as Cosmic Vision Engine — never mentions AI/GPT.
    """
    client = _get_client()
    if client is None:
        raise RuntimeError(_client_err or "Cosmic Vision Engine not configured")
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
        "the Cosmic Vision Engine.\n"
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
        raise RuntimeError(f"Cosmic Vision Engine request failed: {exc}") from exc

    raw = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    if not raw:
        raise RuntimeError("Cosmic Vision Engine returned empty response")
    try:
        parsed = json.loads(raw)
    except Exception as exc:
        raise RuntimeError(f"Cosmic Vision Engine returned non-JSON: {exc}") from exc

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
        raise RuntimeError(_client_err or "Cosmic Vision Engine not configured")
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
        "the Cosmic Vision Engine.\n"
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
        raise RuntimeError(f"Cosmic Vision Engine request failed: {exc}") from exc

    raw = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    if not raw:
        raise RuntimeError("Cosmic Vision Engine returned empty response")
    try:
        parsed = json.loads(raw)
    except Exception as exc:
        raise RuntimeError(f"Cosmic Vision Engine returned non-JSON: {exc}") from exc

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

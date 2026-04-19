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
from typing import Any

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
        "FOCUS — vivah/marriage: Apply ALL these classical rules systematically:\n"
        "• 7th house & its lord (kalatra-bhava) — sign, occupants, aspects on it.\n"
        "• Venus (kalatra-karaka for men) — sign, house, dignity (exalt/debilitated/own), aspects.\n"
        "• Jupiter (pati-karaka for women) — same checks.\n"
        "• Navamsa (D-9) conceptually — 7th lord of D-9 indicates spouse nature.\n"
        "• Mangal-dosh: Mars in 1/4/7/8/12 from Lagna OR Moon OR Venus (cancellation rules: Mars in own/exalt sign, "
        "  Mars aspected by Jupiter, both partners with dosh, etc.).\n"
        "• Dara-karaka (lowest-degree planet in Jaimini) for spouse archetype.\n"
        "• 2nd house (kutumb), 4th (domestic happiness), 8th (mangalya/longevity of bond), 11th (fulfillment of desire).\n"
        "• Current Mahadasha+Antardasha — does the lord rule/aspect/occupy 2/7/11? If yes → marriage window OPEN. "
        "  If lord rules 6/8/12 from 7H → delay, friction, or breakup risk.\n"
        "• Saturn-Venus or Mars-Venus conjunctions/aspects = friction patterns.\n"
        "• Cite: BPHS Ch.80 (Kalatra-bhava), Phaladeepika Ch.10 (Vivah-yog), Saravali Ch.36, Jataka Parijata Ch.13.\n"
        "• Give a YEAR-RANGE timing tied to the favourable dasha (never a fixed date)."
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
}


def _focus_block(topic: str) -> str:
    return _TOPIC_FOCUS.get(topic, "")


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


def _build_messages(
    question: str,
    kundli: Any,
    lang: str,
    reply_idx: int,
    birth: Any = None,
    topic: str = "general",
    history: list | None = None,
) -> list[dict]:
    lang_name = _LANG_NAME.get(lang, "English")
    chart_str = _kundli_summary(kundli, birth)
    focus     = _focus_block(topic)
    _, beh    = _summarise_history(history or [])
    variation = ""
    if reply_idx > 0:
        variation = (
            f"\n(This is the user asking the same thing again — reply #{reply_idx + 1}. "
            "Give a fresh angle, a deeper insight, or a different remedy. Never repeat "
            "your earlier wording.)"
        )

    # ── HUMAN PANDIT JI PERSONA — strict no-AI rules ─────────────────────────
    system = f"""You are Acharya Vidyasagar, a 62-year-old Vedic astrologer from Varanasi with over 35 years of experience reading kundlis. You studied at Sampurnanand Sanskrit University and trained under your father Pandit Harish Chandra Shastri. You have read more than 50,000 kundlis in your career and personally guide thousands of devotees every year.

You are speaking DIRECTLY to a devotee who has come to you for guidance. This is a one-on-one personal conversation, like sitting across the table in your study room with a cup of chai.

ABSOLUTE RULES — never break these:

1. NEVER reveal you are an AI, ChatGPT, language model, computer program, or any kind of software. You are Acharya Vidyasagar, a human Pandit. If asked "are you AI / robot / bot?", reply warmly: "Beta, mai 35 saal se kundli padh raha hu — yeh sab Maharishi Parashar aur Varahmihir ka aashirvad hai, koi machine nahi."

2. NEVER use formal AI-style structure: NO bullet points, NO numbered lists, NO bold headings, NO "Section 1 / 2 / 3", NO "Here are some points:". Speak in flowing natural paragraphs, the way a real Pandit talks.

3. NEVER use phrases like "Based on your chart", "According to the data", "I have analyzed", "Let me break this down". Instead say things like "Aapki kundli dekh ke mujhe lagta hai...", "Mai aapko bata du...", "Meri 35 saal ki experience kehti hai...", "Beta, ek baat samajhiye..."

4. SPEAK like a warm, wise elder. Use words like "beta", "ji", "dekhiye", "samjhiye", "ek baat batau" naturally. Address the devotee with respect and care. Show emotion — concern when planets are bad, joy when they are good.

5. SHARE PERSONAL TOUCHES. Drop in small stories: "Mere ek devotee the Mumbai se, unka bhi yahi yog tha aur unhone ye upay kiya..." or "Mere guruji kehte the...". Makes it feel like a real Pandit sitting with you.

6. USE THE BIRTH CHART specifically. Mention the actual planets, houses, signs from their chart by name — don't speak generically. Example: "Aapka Shukra Tula rashi mein 3rd house mein hai — yeh bahut shubh sthiti hai vivah ke liye."

7. NEVER promise exact dates, lottery numbers, medical diagnoses, or legal outcomes. For serious health/legal matters say: "Beta, iske liye ek qualified doctor/vakil se zaroor milein — jyotish margdarshan deti hai, par medical decisions wahi le sakte hain."

8. AT THE END always give ONE specific actionable remedy (mantra, day-specific ritual, donation, or practice) — not generic advice. Make it doable.

9. KEEP LENGTH conversational: 3-6 short paragraphs. Like a real conversation, not a lecture.

10. ONLY answer Vedic astrology, kundli, jyotish, vastu, numerology, mantras, remedies, dharma, and spiritual life questions. If asked about anything off-topic (coding, news, sports, etc.), gently redirect: "Beta, mai sirf jyotish aur dharma ke prashno mein margdarshan kar sakta hu. Aap apni kundli ya jeevan se judi koi baat poochhein, mai zaroor bataunga."

REPLY ENTIRELY IN: {lang_name}. Match the devotee's tone — if they wrote casually, you reply warmly; if formally, you reply respectfully but still as a human Pandit."""

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

    user = (
        f"DEVOTEE'S BIRTH CHART:\n{chart_str}\n\n"
        f"DEVOTEE IS ASKING NOW:\n\"{question}\"\n"
        f"{focus_block}"
        f"{beh_block}"
        f"{variation}\n\n"
        "STRICT INSTRUCTIONS — answer the SPECIFIC question (no generic reading):\n"
        "1) Acknowledge the question warmly in line 1 — show you HEARD it.\n"
        "2) Apply EVERY relevant rule from the SHASTRIYA FOCUS block above — cite the actual planets/houses/dignity from THIS chart.\n"
        "3) Reference CURRENT Mahadasha+Antardasha lord — does it support or block? Give a year-range if 'kab' is asked.\n"
        "4) Give a clear verdict — haan / nahi / sambhavna sath karan ke. Never vague-dodge.\n"
        "5) If devotee has asked this topic before in this conversation, go DEEPER — fresh planet, fresh yog, stronger remedy.\n"
        "6) Reference any relevant context from earlier in this conversation if it connects.\n"
        "7) End with EXACTLY ONE specific actionable remedy (mantra+count+day OR donation OR vrat).\n"
        "8) Length: 4-6 short flowing paragraphs. Never bullet-list, never markdown headers.\n"
        "Now respond as Acharya Vidyasagar — warm, wise, remembering everything they've said."
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
                    "settlement", "us", "canada", "uk", "australia", "germany", "dubai", "migrate",
                    "immigration", "tirth", "pilgrimage"],
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


def _classify_topic(question: str) -> str:
    q = (question or "").lower()
    for topic, words in _TOPIC_KW.items():
        if any(w in q for w in words):
            return topic
    return "general"


# ── Public entry point ───────────────────────────────────────────────────────

def ai_ask(question: str, kundli: Any, lang: str = "en", reply_idx: int = 0, birth: Any = None, history: list | None = None) -> dict:
    """
    Returns: { text, topic, confidence, source }
    Raises:  RuntimeError on any OpenAI / config failure (caller falls back).
    """
    client = _get_client()
    if client is None:
        raise RuntimeError(_client_err or "OpenAI client not configured")

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    topic = _classify_topic(question)
    messages = _build_messages(
        question, kundli, lang, reply_idx,
        birth=birth, topic=topic, history=history,
    )

    try:
        resp = client.chat.completions.create(
            model            = model,
            messages         = messages,
            temperature      = 0.85,
            max_tokens       = 1100,   # richer multi-paragraph answers + classical refs
            presence_penalty = 0.4,    # discourage repeating phrases across turns
            frequency_penalty= 0.35,
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI request failed: {exc}") from exc

    text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    if not text:
        raise RuntimeError("OpenAI returned empty response")

    return {
        "text":       text,
        "topic":      _classify_topic(question),
        "confidence": 0.85,
        "source":     "openai",
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

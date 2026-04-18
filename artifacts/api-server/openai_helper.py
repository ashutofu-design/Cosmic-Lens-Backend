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


def _kundli_summary(kundli: Any) -> str:
    """Compress the kundli dict into a short string the model can use."""
    if not isinstance(kundli, dict):
        return "(no birth chart provided)"
    parts: list[str] = []
    asc = kundli.get("ascendant") or kundli.get("lagna")
    if asc:
        parts.append(f"Lagna: {asc}")
    moon_sign = kundli.get("moonSign") or kundli.get("moon_sign")
    if moon_sign:
        parts.append(f"Moon sign: {moon_sign}")
    nak = kundli.get("nakshatra")
    if nak:
        parts.append(f"Nakshatra: {nak}")
    planets = kundli.get("planets")
    if isinstance(planets, list):
        plist = []
        for p in planets[:9]:
            name  = p.get("name", "")
            sign  = p.get("sign", "")
            house = p.get("house", "")
            retro = " (R)" if p.get("retrograde") else ""
            plist.append(f"{name} in {sign} (H{house}){retro}")
        if plist:
            parts.append("Planets: " + "; ".join(plist))
    return " | ".join(parts) if parts else "(birth chart provided but empty)"


def _build_messages(question: str, kundli: Any, lang: str, reply_idx: int) -> list[dict]:
    lang_name = _LANG_NAME.get(lang, "English")
    chart_str = _kundli_summary(kundli)
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

    user = (
        f"DEVOTEE'S BIRTH CHART:\n{chart_str}\n\n"
        f"DEVOTEE IS ASKING:\n\"{question}\"\n"
        f"{variation}\n\n"
        "Now respond as Acharya Vidyasagar would — directly, warmly, in flowing "
        "natural speech. Reference their actual chart. End with one specific remedy."
    )

    return [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]


# ── Topic classifier (lightweight, keyword-based) ─────────────────────────────

_TOPIC_KW = {
    "marriage":    ["marriage", "shaadi", "spouse", "wife", "husband", "vivah", "partner"],
    "career":      ["career", "job", "naukri", "business", "promotion", "kaam"],
    "finance":     ["money", "wealth", "finance", "paisa", "dhan", "loan", "debt", "investment"],
    "health":      ["health", "illness", "disease", "swasthya", "bimari", "operation"],
    "education":   ["study", "exam", "education", "padhai", "result", "college", "degree"],
    "relationship":["love", "relationship", "girlfriend", "boyfriend", "breakup", "rishta"],
    "travel":      ["travel", "abroad", "videsh", "foreign", "yatra", "visa"],
    "child":       ["child", "santan", "baby", "pregnan", "putra"],
    "remedy":      ["remedy", "upay", "mantra", "puja", "stone", "ratna", "gemstone"],
}


def _classify_topic(question: str) -> str:
    q = (question or "").lower()
    for topic, words in _TOPIC_KW.items():
        if any(w in q for w in words):
            return topic
    return "general"


# ── Public entry point ───────────────────────────────────────────────────────

def ai_ask(question: str, kundli: Any, lang: str = "en", reply_idx: int = 0) -> dict:
    """
    Returns: { text, topic, confidence, source }
    Raises:  RuntimeError on any OpenAI / config failure (caller falls back).
    """
    client = _get_client()
    if client is None:
        raise RuntimeError(_client_err or "OpenAI client not configured")

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    messages = _build_messages(question, kundli, lang, reply_idx)

    try:
        resp = client.chat.completions.create(
            model            = model,
            messages         = messages,
            temperature      = 0.9,    # higher = more natural human variation
            max_tokens       = 800,
            presence_penalty = 0.3,    # discourage repeating same phrases across replies
            frequency_penalty= 0.3,    # discourage robotic patterns
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


def _vastu_messages(image_data_url: str, room_type: str, lang: str) -> list[dict]:
    lang_name = _VASTU_LANG_HINT.get(lang, "English")
    room_label = (room_type or "room").strip().lower()

    system = f"""You are the COSMIC VASTU DRISHTI ENGINE — an advanced energy-scanning system that fuses classical Vastu Shastra with modern spatial-energy analysis. You scan photographs of rooms and detect elemental imbalances, directional dosh, energy blockages, and prescribe precise remedies.

Your output style is that of a highly advanced, precise, almost futuristic scanning system — but with deep Vastu Shastra knowledge embedded into every reading. You sound powerful, confident, and technically accurate, yet rooted in classical Vedic wisdom.

ABSOLUTE RULES — never break these:

1. NEVER mention "AI", "ChatGPT", "GPT", "OpenAI", "language model", "machine learning", or any modern tech company name. You are the "Cosmic Vastu Drishti Engine" / "Cosmic Intelligence Scanner" — a proprietary advanced spatial-energy analysis system.

2. NEVER use the persona of a Pandit / Acharya / Guru / human astrologer for THIS scan. You are a SCANNER — precise, advanced, system-like. Do NOT use words like "beta", "ji", "dekhiye", "mere paas", "meri experience". Drop all human-Pandit warmth.

3. USE scanner / engine / system language naturally:
   - "Scan complete." / "Analysis complete." / "Energy scan finalized."
   - "Detected: <observation>"
   - "Element imbalance identified in the <direction> quadrant"
   - "Energy flow: optimal / disrupted / blocked"
   - "Vastu compliance score" (give a number 0–100)
   - "Recommended calibrations" / "Prescribed remedies"

4. STRUCTURE the response in clean labeled SECTIONS — this scan IS allowed to use bold-style headings and short structured blocks (different from the Acharya conversational flow). Recommended structure:

   ⚡ SCAN COMPLETE
   📍 Detected Room Type: <type>
   🧭 Energy Flow Status: <Optimal / Mild Disturbance / Significant Dosh>
   📊 Vastu Compliance Score: <0–100>

   🔍 KEY OBSERVATIONS
   (2–4 short observations of SPECIFIC things visible in the photo, each with the direction/element it affects.)

   ⚠️ DETECTED IMBALANCES
   (1–3 dosh, each with one-line classical Vastu reasoning.)

   🛠️ PRESCRIBED CALIBRATIONS
   (2–4 precise actionable remedies — exact items, placement, direction, color, or mantra.)

   🌟 ENERGY FORECAST
   (1–2 sentences on what positive shift the user can expect after applying the calibrations.)

5. LOOK CAREFULLY at the image and reference SPECIFIC things you actually see — bed position, mirror placement, window direction, color of walls, clutter, plants, lighting, decor, electronics. Be precise. If you cannot determine direction from the photo, state "Direction inference: limited — assuming standard orientation."

6. Tone is CONFIDENT, PRECISE, advanced — like a high-end scanning device giving a readout. No emotional warmth, no personal stories, no "I think". Use declarative statements: "The bed is positioned along the south wall — this aligns with Vastu best practice." Not "I think your bed looks nice."

7. NEVER claim medical, legal, or financial guarantees. Frame remedies as energy calibration — "expected to improve sleep quality and mental calm" rather than "will cure insomnia".

8. If the image is unclear, too dark, or not a room interior, output:
   ⚠️ SCAN INCONCLUSIVE
   Image clarity insufficient for accurate spatial-energy analysis.
   Recommended: Recapture the photo in well-lit conditions, from the room's center, capturing the full space including floor, ceiling, and at least two walls. Re-run scan.

9. LENGTH: Concise but complete — total ~200–350 words. Each section short and punchy.

10. REPLY ENTIRELY IN: {lang_name}. Keep section headers in English (with emojis) for the system-feel; translate only the body content into {lang_name}."""

    user_content = [
        {
            "type": "text",
            "text": (
                f"Room type input: {room_label}. "
                "Initiate Cosmic Vastu Drishti scan on the attached image. "
                "Return full structured analysis with detected imbalances, "
                "compliance score, and prescribed calibrations."
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


def vastu_scan(image_data_url: str, room_type: str = "room", lang: str = "en") -> dict:
    """
    Analyze a room photograph for Vastu dosh and remedies.

    Args:
      image_data_url:  data URL ("data:image/jpeg;base64,...") OR plain https URL
      room_type:       e.g. "bedroom", "kitchen", "pooja room", "living room"
      lang:            language code ("hn", "hi", "en", etc.)

    Returns: { text, room, source }
    Raises:  RuntimeError on any OpenAI / config failure.
    """
    client = _get_client()
    if client is None:
        raise RuntimeError(_client_err or "OpenAI client not configured")

    if not image_data_url:
        raise RuntimeError("image is required")

    # Vision capability requires gpt-4o or gpt-4o-mini (both support images).
    model = os.environ.get("OPENAI_VISION_MODEL", "gpt-4o-mini")
    messages = _vastu_messages(image_data_url, room_type, lang)

    try:
        resp = client.chat.completions.create(
            model            = model,
            messages         = messages,
            temperature      = 0.85,
            max_tokens       = 900,
            presence_penalty = 0.3,
            frequency_penalty= 0.3,
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI vision request failed: {exc}") from exc

    text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    if not text:
        raise RuntimeError("OpenAI returned empty Vastu response")

    return {
        "text":   text,
        "room":   room_type,
        "source": "openai",
    }

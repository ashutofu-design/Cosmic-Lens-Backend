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

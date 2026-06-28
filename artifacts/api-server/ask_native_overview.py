"""Route 'mere bare me kuch batao' to native chart overview — not MR/in-laws."""
from __future__ import annotations

import re

_NATIVE_PERSONAL_RX = re.compile(
    r"(?ix)\b(mer[eie]|mujhe|mujhko|main|mein|my|myself|i)\b"
)

_NATIVE_OVERVIEW_RX = re.compile(
    r"(?ix)"
    r"(?:"
    r"\bmere?\s+(?:bare|baare|bar[eé])\s+(?:me|main)\b"
    r"|\bmer[eie]\s+(?:baare|bare|bar[eé])\s+(?:me|main)\b"
    r"|\babout\s+(?:me|myself)\b"
    r"|\btell\s+(?:me\s+)?about\s+(?:me|myself)\b"
    r"|\bmujhe?\s+(?:baare|bare)\s+(?:me|main)\b"
    r"|\b(?:mer[eie]|mujhe)\s+(?:ke\s+)?(?:baare|bare)\s+(?:me|main)\b"
    r"|\b(?:mer[eie]|mujhe)\b.{0,20}\bkuch\s+(?:batao|batado|bataiye|bata)\b"
    r"|\bkuch\s+(?:batao|batado|bataiye|bata)\b.{0,20}\b(?:mer[eie]|mujhe)\b"
    r"|\bmeri?\s+personality\b|\bmy\s+personality\b"
    r"|\bmain\s+kaisa\s+(?:hu|hun|hoon|hai)\b"
    r"|\bmera\s+swabhav\b|\bmeri?\s+nature\b"
    r"|\bwho\s+am\s+i\b"
    r")"
)

# If a concrete life/chart topic is named, it is NOT a generic "about me" ask.
_DOMAIN_SPECIFIC_RX = re.compile(
    r"(?ix)\b("
    r"shaadi|shadi|marriage|vivah|love|pyaar|"
    r"partner|spouse|pati|patni|biwi|bf|gf|"
    r"career|naukri|job|business|"
    r"health|sehat|tabiyat|swasth|"
    r"paisa|money|finance|wealth|"
    r"bachcha|child|pregnancy|"
    r"property|ghar|flat|vastu|"
    r"visa|abroad|videsh|travel|"
    r"dasha|mahadasha|antardasha|gochar|sade\s*sati|"
    r"lagna|rashi|nakshatra|kundli|"
    r"saas|sasur|sasural|in[\s-]?law|"
    r"planet|grah|house|bhav|yog|dosh|dosha|remedy|upay"
    r")\b"
)

NATIVE_OVERVIEW_NARRATOR_RULE = (
    "\n\n=== NATIVE CHART OVERVIEW (user asked about THEMSELVES) ===\n"
    "The user wants a brief overview about THEMSELVES from their birth chart — "
    "NOT about spouse, partner, in-laws, sasural, marriage, or anyone else.\n"
    "Cover 3-4 short paragraphs: (1) Lagna/ascendant personality tone, "
    "(2) Moon sign emotional nature, (3) one strong planet or yoga highlight, "
    "(4) current Mahadasha/Antardasha phase in plain words.\n"
    "Do NOT mention in-laws, spouse family, sasural, partner nature, or 7th/8th "
    "house marriage axes unless the user explicitly asked about marriage.\n"
    "End with one warm line inviting a specific follow-up (career, shaadi, health, paisa).\n"
)


def native_overview_interpretation() -> str:
    return (
        "User wants a general birth-chart overview about themselves "
        "(personality, emotional nature, strengths, current dasha phase)."
    )


def is_native_overview_question(question: str) -> bool:
    from ask_question_normalize import prepare_ask_question

    q = prepare_ask_question((question or "").strip())
    if not q or len(q.split()) > 18:
        return False
    if not _NATIVE_PERSONAL_RX.search(q):
        return False
    if not _NATIVE_OVERVIEW_RX.search(q):
        return False
    if _DOMAIN_SPECIFIC_RX.search(q):
        return False
    return True

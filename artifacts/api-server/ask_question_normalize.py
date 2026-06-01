"""
Prepare user Ask questions for classification and AI.

Handles common Hinglish spelling mistakes, repeated letters, and verb typos
so scope gate + engines understand intent — not only lagna-specific fixes.
"""
from __future__ import annotations

import re
import unicodedata

# ── Canonical replacements (pattern → replacement), order matters ───────────
_WORD_FIXES: list[tuple[re.Pattern[str], str]] = [
    # Astro chart vocabulary
    (re.compile(r"\blagn+a+\b", re.I), "lagna"),
    (re.compile(r"\blagan+\b", re.I), "lagna"),
    (re.compile(r"\blagn\b", re.I), "lagna"),
    (re.compile(r"\braa?sh+i?\b", re.I), "rashi"),
    (re.compile(r"\brasii\b", re.I), "rashi"),
    (re.compile(r"\bnakshatr+a?\b", re.I), "nakshatra"),
    (re.compile(r"\bnakchatr+a?\b", re.I), "nakshatra"),
    (re.compile(r"\bkundl+i+\b", re.I), "kundli"),
    (re.compile(r"\bkundal+i+\b", re.I), "kundli"),
    (re.compile(r"\bdas+h+a?\b", re.I), "dasha"),
    (re.compile(r"\bdas+a\b", re.I), "dasha"),
    (re.compile(r"\bmahadas+h+a?\b", re.I), "mahadasha"),
    (re.compile(r"\bantardas+h+a?\b", re.I), "antardasha"),
    (re.compile(r"\bgo+char+\b", re.I), "gochar"),
    (re.compile(r"\bmuhur+a?t+\b", re.I), "muhurat"),
    (re.compile(r"\bnavam+sh+a?\b", re.I), "navamsa"),
    (re.compile(r"\bmang+l+ik+\b", re.I), "manglik"),
    (re.compile(r"\bmang+al\s*dosh+\b", re.I), "mangal dosh"),
    (re.compile(r"\bkaal\s*sarp+\b", re.I), "kaal sarp"),
    (re.compile(r"\bkalsarp+\b", re.I), "kaal sarp"),
    # Life domains (personal questions)
    (re.compile(r"\bshadi\b", re.I), "shaadi"),
    (re.compile(r"\bsha+di+\b", re.I), "shaadi"),
    (re.compile(r"\bshad+i\b", re.I), "shaadi"),
    (re.compile(r"\bshaadii+\b", re.I), "shaadi"),
    (re.compile(r"\bviv+ah+\b", re.I), "vivah"),
    (re.compile(r"\bbiy+ah+\b", re.I), "vivah"),
    (re.compile(r"\bnau+kri+\b", re.I), "naukri"),
    (re.compile(r"\bnok+ri+\b", re.I), "naukri"),
    (re.compile(r"\bcarr+eer+\b", re.I), "career"),
    (re.compile(r"\bpa+i+sa+\b", re.I), "paisa"),
    (re.compile(r"\bpais+e+\b", re.I), "paise"),
    (re.compile(r"\bbus+iness+\b", re.I), "business"),
    (re.compile(r"\bse+h+at+\b", re.I), "sehat"),
    (re.compile(r"\bbach+ch+a+\b", re.I), "bachcha"),
    (re.compile(r"\bbach+he+\b", re.I), "bachche"),
    (re.compile(r"\bpy+a+ar+\b", re.I), "pyaar"),
    (re.compile(r"\bpre+m+\b", re.I), "prem"),
    (re.compile(r"\bhus+b+and+\b", re.I), "husband"),
    (re.compile(r"\bwif+e+\b", re.I), "wife"),
    (re.compile(r"\bpart+n+er+\b", re.I), "partner"),
    (re.compile(r"\bluc+k+\b", re.I), "luck"),
    (re.compile(r"\bbhag+y+a+\b", re.I), "bhagya"),
    (re.compile(r"\bfut+ure+\b", re.I), "future"),
    (re.compile(r"\bprop+ert+y+\b", re.I), "property"),
    (re.compile(r"\bgh+ar+\b", re.I), "ghar"),
    (re.compile(r"\bvides+h+\b", re.I), "videsh"),
    (re.compile(r"\babr+oad+\b", re.I), "abroad"),
    # Planets (common misspellings)
    (re.compile(r"\bsh+an+i+\b", re.I), "shani"),
    (re.compile(r"\bshuk+r+a+\b", re.I), "shukra"),
    (re.compile(r"\bbru?has+pati+\b", re.I), "guru"),
    (re.compile(r"\bchan+d+r+a+\b", re.I), "chandra"),
    (re.compile(r"\bchan+d+\b", re.I), "chand"),
    (re.compile(r"\bsur+y+a+\b", re.I), "surya"),
    (re.compile(r"\bmang+al+\b", re.I), "mangal"),
    (re.compile(r"\bbud+h+\b", re.I), "budh"),
]

# Hinglish verb / question-word typos
_VERB_FIXES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(kya|kaun|kab|kaise|kaisa|kaisi|kahan|kyun)\s+he\b", re.I), r"\1 hai"),
    (re.compile(r"\b(kya|kaun|kab)\s+ho\b", re.I), r"\1 hai"),
    (re.compile(r"\b(he|ho|h|haii|haai)\s*$", re.I), "hai"),
    (re.compile(r"\bhogaa+\b", re.I), "hoga"),
    (re.compile(r"\bhogiii+\b", re.I), "hogi"),
    (re.compile(r"\b(batao|bataiye|bataye|btao|btyo)\b", re.I), "batao"),
    (re.compile(r"\bmilegaa+\b", re.I), "milega"),
    (re.compile(r"\bmilegii+\b", re.I), "milegi"),
]

# Personal + life/astro — allow scope gate when anchors are typo'd
_LIFE_ASTRO_TOPIC_RX = re.compile(
    r"(?ix)\b("
    r"lagna|ascendant|rashi|nakshatra|kundli|chart|horoscope|dasha|gochar|"
    r"yog|dosh|dosha|manglik|muhurat|"
    r"shaadi|shadi|marriage|vivah|love|pyaar|partner|bf|gf|husband|wife|pati|"
    r"career|naukri|job|business|paisa|money|wealth|finance|"
    r"health|sehat|disease|illness|"
    r"child|bachcha|pregnancy|"
    r"property|ghar|flat|vastu|"
    r"visa|abroad|videsh|travel|"
    r"luck|bhagya|future|timing|"
    r"sun|moon|mars|mangal|mercury|budh|jupiter|guru|venus|shukra|saturn|shani|rahu|ketu"
    r")\b",
)

_PERSONAL_RX = re.compile(
    r"(?ix)\b("
    r"mera|meri|mere|mujhe|mujhko|mujh|main|mein|my|mine|"
    r"hamara|hamari|apna|apni|apne|"
    r"will\s+i|should\s+i|am\s+i|"
    r"shaadi\s+hogi|naukri\s+lagegi"
    r")\b",
)

_QUESTION_SHAPE_RX = re.compile(
    r"(?ix)\b(kya|kaun|kab|kaise|kaisa|when|what|how|why|should|will|hoga|hogi|milega|batao)\b",
)


def _collapse_repeated_letters(text: str) -> str:
    """lagnaa → lagna, shaadii → shaadi (max 2 same letters in a row)."""
    return re.sub(r"([a-zA-Z\u0900-\u097F])\1{2,}", r"\1\1", text)


def prepare_ask_question(question: str) -> str:
    """
    Normalize user question for gates, classifiers, and LLM.
    Original casing is not preserved (Hinglish matching is case-insensitive).
    """
    q = unicodedata.normalize("NFKC", (question or ""))
    q = " ".join(q.split())
    if not q:
        return q

    q = _collapse_repeated_letters(q)

    for rx, repl in _WORD_FIXES:
        q = rx.sub(repl, q)

    for rx, repl in _VERB_FIXES:
        q = rx.sub(repl, q)

    # kyahe / kabse glued words
    q = re.sub(r"\bkyahe\b", "kya hai", q, flags=re.I)
    q = re.sub(r"\bkabse\b", "kab se", q, flags=re.I)
    q = re.sub(r"\bkaisehe\b", "kaise hai", q, flags=re.I)

    return " ".join(q.split())


# Back-compat alias
normalize_ask_typos = prepare_ask_question


def looks_like_personal_life_question(question: str) -> bool:
    """True when typos may hide astro/life intent but question is clearly personal."""
    q = prepare_ask_question(question)
    if not q or len(q.split()) > 22:
        return False
    if not _PERSONAL_RX.search(q):
        return False
    if _LIFE_ASTRO_TOPIC_RX.search(q):
        return True
    if _QUESTION_SHAPE_RX.search(q) and len(q.split()) <= 14:
        return True
    return False

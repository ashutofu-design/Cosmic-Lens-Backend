"""
Prepare user Ask questions for classification and AI.

Handles common Hinglish spelling mistakes, repeated letters, and verb typos
so scope gate + engines understand intent — not only lagna-specific fixes.
"""
from __future__ import annotations

import difflib
import os
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
    (re.compile(r"\bcarrer+\b", re.I), "career"),
    (re.compile(r"\bpa+i+sa+\b", re.I), "paisa"),
    (re.compile(r"\bpais+e+\b", re.I), "paise"),
    (re.compile(r"\bbus+iness+\b", re.I), "business"),
    (re.compile(r"\bse+h+at+\b", re.I), "sehat"),
    (re.compile(r"\bhel+th+\b", re.I), "health"),
    (re.compile(r"\bheath+\b", re.I), "health"),
    (re.compile(r"\bhealt+h+\b", re.I), "health"),
    (re.compile(r"\btab+iat+\b", re.I), "tabiyat"),
    (re.compile(r"\btab+iyat+\b", re.I), "tabiyat"),
    (re.compile(r"\bswast+h+ya+\b", re.I), "swasthya"),
    (re.compile(r"\bswast+h+\b", re.I), "swasth"),
    (re.compile(r"\bqu+est+ion+\b", re.I), "question"),
    (re.compile(r"\bqust+ion+\b", re.I), "question"),
    (re.compile(r"\bqustn+\b", re.I), "question"),
    (re.compile(r"\bkb\b", re.I), "kab"),
    (re.compile(r"\bhlt\b", re.I), "health"),
    (re.compile(r"\bshdi\b", re.I), "shadi"),
    (re.compile(r"\bnat+a+o\b", re.I), "batao"),
    (re.compile(r"\bnat+ao\b", re.I), "batao"),
    (re.compile(r"\bbach+ch+a+\b", re.I), "bachcha"),
    (re.compile(r"\bbach+he+\b", re.I), "bachche"),
    (re.compile(r"\bpy+a+ar+\b", re.I), "pyaar"),
    (re.compile(r"\bpre+m+\b", re.I), "prem"),
    (re.compile(r"\bhus+b+and+\b", re.I), "husband"),
    (re.compile(r"\bwif+e+\b", re.I), "wife"),
    (re.compile(r"\bpart+n+er+\b", re.I), "partner"),
    (re.compile(r"\breal+ationship+\b", re.I), "relationship"),
    (re.compile(r"\brelat+ionship+\b", re.I), "relationship"),
    (re.compile(r"\brelat+ionshp+\b", re.I), "relationship"),
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
    (re.compile(r"\b(kya|kaun|kab|kaisa|kaisi)\s+ho\b", re.I), r"\1 hai"),
    (re.compile(r"\b(kaisa|kaisi|kaise)\s+he\b", re.I), r"\1 hai"),
    (re.compile(r"\b(he|ho|h|haii|haai)\s*$", re.I), "hai"),
    (re.compile(r"\bhogaa+\b", re.I), "hoga"),
    (re.compile(r"\bhogiii+\b", re.I), "hogi"),
    (re.compile(r"\brahegaa+\b", re.I), "rahega"),
    (re.compile(r"\brahegii+\b", re.I), "rahegi"),
    (re.compile(r"\bhogii+\b", re.I), "hogi"),
    (re.compile(r"\bmilegaa+\b", re.I), "milega"),
    (re.compile(r"\bmilegii+\b", re.I), "milegi"),
    (re.compile(r"\bhog\s*$", re.I), "hoga"),
    (re.compile(r"\bhogi\s*$", re.I), "hogi"),
    # Keyboard typos near hoga (hogq, hogw, hogx, …)
    (re.compile(r"\bhog[qwxzc]\b", re.I), "hoga"),
    (re.compile(r"\bhog[qwxzc]\s*$", re.I), "hoga"),
    (re.compile(r"\b(batao|bataiye|bataye|btao|btyo|bataoo)\b", re.I), "batao"),
    (re.compile(r"\b(samjhao|smjhao|samjhaoo|explain)\b", re.I), "samjhao"),
]

# Personal + life/astro — allow scope gate when anchors are typo'd
try:
    from ask_career.sector_registry import CAREER_SCOPE_EXTRA as _CAREER_SCOPE_EXTRA
except Exception:
    _CAREER_SCOPE_EXTRA = (
        r"youtuber|youtube|food|restaurant|pilot|actor|electrician|promotion|interview"
    )

_LIFE_ASTRO_TOPIC_RX = re.compile(
    r"(?ix)\b("
    r"lagna|ascendant|rashi|nakshatra|kundli|chart|horoscope|dasha|gochar|"
    r"yog|dosh|dosha|manglik|muhurat|"
    r"shaadi|shadi|marriage|vivah|love|pyaar|partner|bf|gf|husband|wife|pati|"
    r"career|naukri|job|business|paisa|money|wealth|finance|"
    r"health|sehat|tabiyat|swasth|swasthya|disease|illness|"
    r"child|bachcha|pregnancy|"
    r"property|ghar|flat|vastu|"
    r"visa|abroad|videsh|travel|"
    r"luck|bhagya|future|timing|"
    rf"{_CAREER_SCOPE_EXTRA}|"
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
    r"(?ix)\b("
    r"kya|kaun|kaunsa|kaunsi|kab|kaise|kaisa|kaisi|kahan|kyun|kyu|"
    r"when|what|how|why|should|will|where|which|kis|kitna|kitni|"
    r"hoga|hogi|milega|milegi|aayega|aayegi|rahega|rahegi|"
    r"hai|he|chal\s*rah|effect|result|prabhav|asar|"
    r"possible|likely|batao|samjhao|theek|sahi|achha|accha|delay|"
    r"ban\s+sakta|ban\s+sakti|ban\s+paunga|ban\s+paungi|banna"
    r")\b",
)

_IMPLICIT_ASK_TOPIC_RX = re.compile(
    r"(?ix)\b("
    r"lagna|ascendant|rashi|nakshatra|kundli|chart|horoscope|"
    r"dasha|mahadasha|antardasha|gochar|yog|yoga|dosh|dosha|manglik|muhurat|"
    r"sade\s*sati|kaal\s*sarp|"
    r"shaadi|shadi|marriage|vivah|love|pyaar|partner|bf|gf|husband|wife|pati|"
    r"career|naukri|job|business|paisa|money|wealth|finance|"
    r"health|sehat|tabiyat|swasth|swasthya|child|bachcha|pregnancy|"
    r"property|ghar|flat|vastu|visa|abroad|videsh|travel|"
    r"luck|bhagya|future|timing|"
    rf"{_CAREER_SCOPE_EXTRA}|"
    r"sun|moon|mars|mangal|mercury|budh|jupiter|guru|venus|shukra|saturn|shani|rahu|ketu|"
    r"house|bhav|bhaav|lord|swami|"
    r"navamsa|navamsha|d9|d7|d10|d12|divisional"
    r")\b",
)

_TIMING_ONLY_RX = re.compile(
    r"(?ix)"
    r"\b(shaadi|shadi|marriage|naukri|career|paisa|health|bachcha|visa|abroad)\b"
    r".{0,15}\b(kab|when)\b|"
    r"\b(kab|when)\b.{0,15}\b(shaadi|shadi|marriage|naukri|career|paisa|health|bachcha|visa|abroad)\b"
)


def _collapse_repeated_letters(text: str) -> str:
    """lagnaa → lagna, shaadii → shaadi (max 2 same letters in a row)."""
    return re.sub(r"([a-zA-Z\u0900-\u097F])\1{2,}", r"\1\1", text)


# Tokens we never fuzzy-correct (possessives, grammar, question words).
_FUZZY_SKIP: frozenset[str] = frozenset(
    {
        "hai", "hoga", "hogi", "honge", "tha", "thi", "the", "he", "ho",
        "mera", "meri", "mere", "mujhe", "mujhko", "main", "mein", "my", "mine",
        "kya", "kab", "kaise", "kaisa", "kaisi", "kahan", "kyun", "kyu", "kis",
        "kitna", "kitni", "kaun", "kaunsa", "kaunsi", "ko", "ke", "ki", "ka",
        "se", "me", "par", "pe", "ya", "aur", "bhi", "nahi", "na", "agar",
        "when", "what", "how", "why", "where", "which", "will", "should",
        "the", "and", "for", "are", "was", "has", "had", "can", "would",
    }
)


def _build_fuzzy_vocab() -> tuple[str, ...]:
    """Roman-script astro/life words for difflib typo repair."""
    words: set[str] = {
        "lagna", "ascendant", "rashi", "nakshatra", "kundli", "chart", "horoscope",
        "dasha", "mahadasha", "antardasha", "gochar", "muhurat", "navamsa",
        "manglik", "yog", "dosh", "dosha", "remedy", "remedies", "upay",
        "shaadi", "shadi", "marriage", "vivah", "love", "pyaar", "partner",
        "career", "naukri", "job", "business", "promotion", "interview",
        "paisa", "paise", "money", "wealth", "finance", "income", "savings",
        "health", "sehat", "tabiyat", "swasthya", "illness", "disease",
        "child", "bachcha", "pregnancy", "property", "ghar", "flat", "vastu",
        "visa", "abroad", "videsh", "travel", "litigation", "court",
        "shani", "saturn", "rahu", "ketu", "jupiter", "guru", "venus", "shukra",
        "mars", "mangal", "mercury", "budh", "moon", "chandra", "sun", "surya",
        "house", "bhav", "bhaav", "lord", "exalted", "debilitated", "retrograde",
        "future", "timing", "luck", "bhagya", "sade", "sati", "transit",
    }
    try:
        from domain_splitter import _DOMAIN_KEYWORDS  # type: ignore

        for kws in _DOMAIN_KEYWORDS.values():
            for phrase in kws:
                for token in phrase.lower().split():
                    if len(token) >= 4 and token.isascii():
                        words.add(token)
    except Exception:
        pass
    return tuple(sorted(words))


_FUZZY_VOCAB: tuple[str, ...] | None = None


def _fuzzy_vocab() -> tuple[str, ...]:
    global _FUZZY_VOCAB
    if _FUZZY_VOCAB is None:
        _FUZZY_VOCAB = _build_fuzzy_vocab()
    return _FUZZY_VOCAB


def _fuzzy_repair_tokens(text: str) -> str:
    """Repair heavy typos against astro/life vocabulary (after regex fixes)."""
    if (os.environ.get("ASK_FUZZY_NORMALIZE") or "on").strip().lower() in (
        "0", "off", "false", "no",
    ):
        return text
    vocab = _fuzzy_vocab()
    out: list[str] = []
    for raw in text.split():
        low = raw.lower()
        if len(low) < 4 or low in _FUZZY_SKIP or not low.isascii():
            out.append(raw)
            continue
        if low in vocab:
            out.append(low)
            continue
        match = difflib.get_close_matches(low, vocab, n=1, cutoff=0.82)
        if match:
            out.append(match[0])
        else:
            out.append(raw)
    return " ".join(out)


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

    # kyahe / kabse glued words + common keyboard typos
    q = re.sub(r"\bkyahe\b", "kya hai", q, flags=re.I)
    q = re.sub(r"\bkabse\b", "kab se", q, flags=re.I)
    q = re.sub(r"\bkaisehe\b", "kaise hai", q, flags=re.I)
    q = re.sub(r"\bkaisihe\b", "kaisi hai", q, flags=re.I)
    q = re.sub(r"\bkaisahe\b", "kaisa hai", q, flags=re.I)
    q = re.sub(r"\bmera\s+pass\s+paisa\b", "mere paas paisa", q, flags=re.I)
    q = re.sub(r"\bmeri\s+pass\s+paisa\b", "mere paas paisa", q, flags=re.I)
    q = re.sub(r"\bpass\s+paisa\b", "paas paisa", q, flags=re.I)
    q = re.sub(r"\bmera\s+paas\b", "mere paas", q, flags=re.I)
    # Strip stray punctuation glue (health??, career!!!)
    q = re.sub(r"([?\!\.]){2,}", r"\1", q)
    q = q.strip(" ?!.,")

    q = _fuzzy_repair_tokens(q)

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


def looks_like_implicit_ask(question: str) -> bool:
    """True for Ask-screen questions that omit mera/meri but are clearly chart/life asks."""
    q = prepare_ask_question(question)
    if not q or len(q.split()) > 30:
        return False
    if not _IMPLICIT_ASK_TOPIC_RX.search(q):
        return False
    if _QUESTION_SHAPE_RX.search(q):
        return True
    return bool(_TIMING_ONLY_RX.search(q))


def has_question_intent(question: str) -> bool:
    q = prepare_ask_question(question)
    return bool(_QUESTION_SHAPE_RX.search(q)) if q else False

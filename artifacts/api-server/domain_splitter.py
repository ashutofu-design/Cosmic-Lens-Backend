"""
domain_splitter.py — P1.2.10 (B1)
==================================
Deterministic regex-based domain extractor for the multi-intent splitter.

Public API
----------
    from domain_splitter import (
        extract_domains, is_jyotish_anchored, DomainHit, DOMAIN_LABELS,
    )

    hits = extract_domains("ghar lene ka yog kab aur shaadi ka bhi")
    # → [DomainHit(name="property", ...), DomainHit(name="marriage", ...)]

Design notes
------------
- ENGINE-FIRST: pure regex, no LLM. Same Q = same hits, fully deterministic.
- Word-boundary strict to avoid substring traps (e.g. "rajaani" must not
  match "naani"; "bharosa" must not match "rosa"). All patterns use `\b`.
- Hinglish-first vocabulary; English synonyms included.
- Confidence = count of distinct keyword hits per domain (capped at 3).
- Used by: intent_splitter (B1 acknowledge), brand_guard escape hatch.
- Killswitch: env DOMAIN_SPLITTER=off → extract_domains returns [].
"""
from __future__ import annotations

import os
import re
from typing import Dict, List, Optional


# ── Configuration ───────────────────────────────────────────────────────────
def _env_on(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() not in ("0", "off", "false", "no", "")


SPLITTER_ENABLED: bool = _env_on("DOMAIN_SPLITTER", True)


# ── Domain → keyword list ───────────────────────────────────────────────────
# Each keyword is a literal token (case-insensitive). Multi-word phrases use
# `\s+` allowance via _phrase(). Order within a domain doesn't matter.
#
# CRITICAL: keep these tight. False positives in domain_splitter cascade into:
#   1. brand_guard escape hatch firing on non-jyotish Qs (off-topic leak)
#   2. multi-intent splitter wrongly splitting a single-intent Q
#
# The comments next to each domain show what user-facing label appears in the
# B1 acknowledge line (DOMAIN_LABELS dict below).
# Architect-tightened (P1.2.10 review):
#   - removed `house` from property (chart-house asks like "7th house me venus")
#   - removed bare `shani` from dasha (planet name appears in many natal asks)
#   - removed bare `transit/gochar` from dasha (too generic — only `mahadasha/
#     antardasha/saade saati` etc. are unambiguous dasha words)
#   - removed `business` and bare `share/shares` from finance (overlap with
#     career-business and chart-house "share" / brand-guard share-trading)
#   - removed bare `travel` from travel (too generic English word)
#   - removed bare `kaam/work` from career (too generic)
#   - removed bare `case/law/court` from legal (too overloaded)
_DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    # property / housing / real estate
    "property": [
        "ghar", "makaan", "makan", "property", "real estate", "plot",
        "flat", "zameen", "apartment", "housing", "real-estate",
        "ghar lena", "property lena", "ghar lene", "ghar kab",
    ],
    # marriage / spouse / relationship
    "marriage": [
        "shaadi", "shadi", "vivah", "vivaah", "marriage", "patni", "pati",
        "biwi", "husband", "wife", "spouse", "partner", "rishta",
        "kundli match", "kundli milan", "milan",
        "love marriage", "arranged marriage", "girlfriend", "boyfriend",
        "sagai", "engagement",
    ],
    # career / job / work — must be employment-specific (not bare "kaam")
    "career": [
        "job", "naukri", "naukari", "career", "kaam-kaaj",
        "boss", "salary", "promotion", "interview", "company",
        "employment", "business job", "transfer order",
        "job change", "career change", "naukri change",
    ],
    # finance / money / wealth (Gap-2 widened: bare "business/dukaan" added back
    # since they consistently denote finance-domain in this app's user base).
    "finance": [
        "paisa", "paise", "money", "wealth", "dhan", "income", "saving",
        "savings", "loan", "debt", "karza", "kharcha", "kharch", "expense",
        "investment", "invest", "investing", "share market", "stock market",
        "stocks", "trade", "trading", "earning", "kamai",
        "profit", "loss", "muafa", "nuksan", "amir", "ameer",
        "business loss", "business growth", "intraday",
        "business", "dukaan", "dukan", "shop", "venture",
        "startup", "freelance income",
    ],
    # health / wellness / illness
    "health": [
        "health", "swasthya", "bimari", "bimaari", "illness", "rog",
        "sickness", "tabiyat", "tabiyyat", "sehat", "dard", "pain",
        "headache", "sar dard", "neend", "sleep", "insomnia", "stress",
        "tension", "anxiety", "depression", "weak", "kamzor", "kamzori",
        "thakaan", "thakavat", "fatigue",
    ],
    # education / studies / exams
    "education": [
        "padhai", "padhaai", "studies", "study", "exam", "exams",
        "education", "school", "college", "university", "degree",
        "course", "result", "marks", "rank", "competitive exam",
        "neet", "jee", "upsc", "ssc", "ielts", "gate", "cat exam",
    ],
    # family / parents / siblings / children
    "family": [
        "maa", "maa-baap", "papa", "father", "mother", "bhai", "behen",
        "behan", "brother", "sister", "parivar", "family", "beta",
        "beti", "child", "santaan", "santan", "putra", "putri",
        "daughter", "son", "kids", "bachche", "bacche",
    ],
    # vastu / directional / home setup
    "vastu": [
        "vastu", "vaastu", "disha", "bedroom", "ghar ki disha",
        "puja room", "puja-room", "mandir room", "main door",
        "kitchen direction", "bed direction",
    ],
    # dasha / planetary periods (Gap-2 widened: "gochar" added — it's a pure
    # astro-Sanskrit word for transit, no overload risk).
    "dasha": [
        "dasha", "mahadasha", "antardasha", "pratyantar",
        "rahu kaal", "shani saade saati", "saade saati", "sade sati",
        "dhaiya", "shani dasha", "rahu dasha", "guru dasha",
        "shani period", "rahu period", "guru period",
        "gochar", "vimshottari", "yogini dasha",
    ],
    # remedies / upay / spiritual practice
    "remedies": [
        "upay", "remedy", "remedies", "totka", "pooja", "puja", "havan",
        "yantra", "mantra", "japa", "rudraksha", "ratna", "gemstone",
        "kavach", "vrat", "donation", "daan",
    ],
    # travel / abroad / migration — bare "travel" removed
    "travel": [
        "videsh", "videsh yatra", "abroad", "foreign settlement",
        "yatra", "visa", "immigration", "migration", "settlement abroad",
        "settle abroad", "us visa", "canada visa", "uk visa",
    ],
    # legal / litigation — bare "case/court/law" removed
    "legal": [
        "court case", "kanoon", "kanooni", "kanooni mamla", "lawsuit",
        "muqadma", "muqaddma", "fir", "vakil", "lawyer",
        "judgment", "judgement", "police case",
    ],
}


# ── Explicit astro-anchor lexicon (used by brand-guard escape) ──────────────
# These are pure-jyotish words that cannot belong to any non-astro topic.
# Brand-guard escape requires either >=2 domain hits OR >=1 explicit anchor.
_ASTRO_ANCHOR_PATTERNS: List[re.Pattern] = [
    re.compile(r"\blagn+a+\b", re.IGNORECASE),
    re.compile(r"\blagan+\b", re.IGNORECASE),
    re.compile(r"\bshadi\b", re.IGNORECASE),
    re.compile(r"\bsha+di+\b", re.IGNORECASE),
] + [
    re.compile(rf"\b{p}\b", re.IGNORECASE)
    for p in (
        "kundli", "kundali", "janam patri", "janam-patri", "horoscope",
        "shaadi", "vivah", "vivaah", "marriage",
        "rashi", "raashi", "navamsa", "navamsh",
        "bhava", "bhav", "nakshatra", "nakshatr",
        "graha", "grah dosha", "yog", "dosh", "dosha",
        "jyotish", "astrology", "astrologer",
        "mahadasha", "antardasha", "saade saati", "sade sati",
        "kal sarp", "kalsarp", "mangal dosh", "manglik",
        "navagraha", "panchang", "panchaang",
        "rashifal", "raashifal", "varshphal",
        "guru chandal", "vish yog", "raj yog", "raj-yog",
    )
]


def has_astro_anchor(question: str) -> bool:
    """True if question contains an unambiguous jyotish-anchor word."""
    if not question:
        return False
    return any(rx.search(question) for rx in _ASTRO_ANCHOR_PATTERNS)


# ── User-facing labels (what appears in B1 acknowledge line) ────────────────
DOMAIN_LABELS: Dict[str, Dict[str, str]] = {
    # Hinglish (default)
    "hinglish": {
        "property":  "ghar/property",
        "marriage":  "shaadi",
        "career":    "job/career",
        "finance":   "paisa/business",
        "health":    "health",
        "education": "padhai",
        "family":    "parivar",
        "vastu":     "vastu",
        "dasha":     "dasha",
        "remedies":  "upay",
        "travel":    "videsh",
        "legal":     "kanooni mamla",
    },
    # English
    "en": {
        "property":  "property",
        "marriage":  "marriage",
        "career":    "career",
        "finance":   "money/business",
        "health":    "health",
        "education": "studies",
        "family":    "family",
        "vastu":     "vastu",
        "dasha":     "dasha",
        "remedies":  "remedies",
        "travel":    "travel/abroad",
        "legal":     "legal matter",
    },
    # Hindi
    "hi": {
        "property":  "ghar",
        "marriage":  "vivaah",
        "career":    "naukri",
        "finance":   "dhan",
        "health":    "swasthya",
        "education": "shiksha",
        "family":    "parivar",
        "vastu":     "vastu",
        "dasha":     "dasha",
        "remedies":  "upay",
        "travel":    "videsh-yatra",
        "legal":     "kanooni mamla",
    },
}


# ── Compile patterns once (word-boundary strict) ────────────────────────────
def _compile_keyword(kw: str) -> re.Pattern:
    """Compile a keyword as a word-bounded, whitespace-tolerant pattern."""
    parts = kw.strip().split()
    if not parts:
        return re.compile(r"(?!x)x")  # never matches
    escaped = r"\s+".join(re.escape(p) for p in parts)
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


_DOMAIN_PATTERNS: Dict[str, List[re.Pattern]] = {
    name: [_compile_keyword(k) for k in kws]
    for name, kws in _DOMAIN_KEYWORDS.items()
}


# ── DomainHit ───────────────────────────────────────────────────────────────
class DomainHit:
    """One domain match with its hit-keywords list and confidence score."""

    __slots__ = ("name", "keywords", "first_pos", "confidence")

    def __init__(self, name: str, keywords: List[str], first_pos: int,
                 confidence: int):
        self.name = name
        self.keywords = keywords
        self.first_pos = first_pos
        self.confidence = confidence

    def __repr__(self) -> str:
        return (f"DomainHit(name={self.name!r}, kws={self.keywords!r}, "
                f"pos={self.first_pos}, conf={self.confidence})")

    def to_dict(self) -> dict:
        return {
            "name":       self.name,
            "keywords":   self.keywords,
            "first_pos":  self.first_pos,
            "confidence": self.confidence,
        }


# ── Public API ──────────────────────────────────────────────────────────────
def extract_domains(question: str) -> List[DomainHit]:
    """
    Scan `question` for jyotish domains. Returns list sorted by:
      1. confidence DESC
      2. first_pos ASC (earlier mention wins ties)

    Killswitch: DOMAIN_SPLITTER=off → returns [].
    """
    if not SPLITTER_ENABLED or not question:
        return []

    q = question.strip()
    if not q:
        return []

    hits: List[DomainHit] = []
    for domain, patterns in _DOMAIN_PATTERNS.items():
        matched_kws: List[str] = []
        first_pos: Optional[int] = None
        for pat in patterns:
            m = pat.search(q)
            if m:
                matched_kws.append(pat.pattern)
                if first_pos is None or m.start() < first_pos:
                    first_pos = m.start()
        if matched_kws:
            # Confidence cap at 3 — beyond that adds no signal
            conf = min(len(matched_kws), 3)
            hits.append(DomainHit(
                name=domain,
                keywords=matched_kws,
                first_pos=first_pos if first_pos is not None else 0,
                confidence=conf,
            ))

    # Sort: confidence desc, first_pos asc
    hits.sort(key=lambda h: (-h.confidence, h.first_pos))
    # P1.2.10 Gap-2 conflict guard: suppress weak-only finance hits when a
    # stronger career signal co-occurs (architect-flagged regression on
    # `business job kab milegi`, `startup job switch`, `dukaan promotion`).
    hits = _apply_conflict_guards(hits)
    return hits


# Tokens whose finance-domain match is AMBIGUOUS — they often appear in
# career-context phrases. If a domain's only matched keywords are all in this
# set AND a competing domain has a non-weak hit, the weak domain is dropped.
_FINANCE_WEAK_TOKENS = {
    "business", "dukaan", "dukan", "shop", "venture",
    "startup", "freelance income",
}
# Career markers that, when present, override weak finance hits.
_CAREER_STRONG_MARKERS = re.compile(
    r"\b(job|naukri|naukari|promotion|interview|salary|"
    r"boss|company|appointment|transfer order|"
    r"job change|career change|naukri change)\b",
    re.IGNORECASE,
)


def _apply_conflict_guards(hits: List[DomainHit]) -> List[DomainHit]:
    """Drop low-signal hits that conflict with stronger co-occurring hits.

    Currently handles:
      • finance-vs-career: weak-only finance + strong career marker → drop finance.
    """
    if not hits or len(hits) < 2:
        return hits
    by_name = {h.name: h for h in hits}
    fin = by_name.get("finance")
    car = by_name.get("career")
    if fin and car:
        # Are ALL of finance's matched kws in the weak-set?
        # Pattern strings are stored as `\b...\b` regex source — strip bounds.
        def _norm(p: str) -> str:
            return p.replace(r"\b", "").lower()
        fin_kws_norm = {_norm(p) for p in fin.keywords}
        if fin_kws_norm and fin_kws_norm.issubset(_FINANCE_WEAK_TOKENS):
            # Drop finance — career wins this collision
            hits = [h for h in hits if h.name != "finance"]
    return hits




def is_jyotish_anchored(question: str) -> bool:
    """
    DEPRECATED for safety-critical use. True if question hits >=1 jyotish
    domain. Retained for backwards compatibility only — too lenient for
    brand-guard escape gating. Use is_jyotish_anchored_strict() instead.
    """
    return len(extract_domains(question)) >= 1


def is_jyotish_anchored_strict(question: str) -> bool:
    """
    STRICT anchor for brand-guard escape (P1.2.10 architect-tightened).
    True only when EITHER:
      (a) question contains an explicit astro-anchor word (kundli/dasha/
          yog/rashi/lagna/jyotish/...), OR
      (b) question hits >=2 distinct jyotish DOMAINS (genuine hybrid).
    A single domain hit (e.g. bare "share market kal buy or sell") is NOT
    enough — that's exactly what the negative-list is meant to catch.
    """
    if not question:
        return False
    if has_astro_anchor(question):
        return True
    return len(extract_domains(question)) >= 2


def is_enabled() -> bool:
    """True if DOMAIN_SPLITTER killswitch is on (default ON)."""
    return SPLITTER_ENABLED

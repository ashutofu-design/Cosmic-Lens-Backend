"""
health_focus_routing.py — health guards, scope gate, post-injectors.

The composable HEALTH FOCUS LLM prompt (atomic ACTION/SYSTEM/INTENT blocks,
ANSWER STYLE rules) was permanently removed 2026-07-12. Health answers now
use ask_health engine + generic MR narrator only.

This module retains:
  • Hard-guard detection (CRISIS + death/lifespan only)
  • is_health_question scope gate
  • Medical disclaimer + forbidden-vocab post-injectors
"""
from __future__ import annotations
import os as _os
import re as _re
from typing import Optional, Tuple


# ── KILLSWITCH HELPERS ────────────────────────────────────────────────
def _chart_slice_enabled() -> bool:
    """True UNLESS HEALTH_CHART_SLICE explicitly disables. Default ON."""
    val = _os.environ.get("HEALTH_CHART_SLICE", "").strip().lower()
    return val not in ("0", "false", "no", "off")


def _disclaimer_enabled() -> bool:
    """True UNLESS HEALTH_DISCLAIMER explicitly disables. Default ON."""
    val = _os.environ.get("HEALTH_DISCLAIMER", "").strip().lower()
    return val not in ("0", "false", "no", "off")


# ── HARD-GUARD PATTERNS (ported from health_static.health_routing) ───
# Order matters: CRISIS first (highest priority, overrides everything),
# then DEATH, then DIAGNOSIS_DEMAND, then TIMING variants, then CURE.
_CRISIS_RX = _re.compile(
    r"(suicide|khud[\s-]?kushi|atm[\s-]?hatya|atmhatya|"
    r"khatam\s+kar\s+(lu|du|dunga|loon)|"
    r"jeena\s+nahi\s+chahta|marna\s+chahta|mujhe\s+marna\s+hai|"
    r"end\s+(my\s+)?life|kill\s+(myself|me)|"
    r"kisi\s+ko\s+maar|kisi\s+ko\s+mar\s+du|kill\s+(him|her|them|someone)|"
    r"khud\s+ko\s+nuksan|self[\s-]?harm|hurt\s+myself)",
    _re.IGNORECASE,
)

_DEATH_RX = _re.compile(
    r"(kab\s+marunga|kab\s+marungi|kab\s+mar(?:enge|ogi|ogi)|"
    r"death\s+kab|maut\s+kab|mrityu\s+kab|"
    r"kab\s+(meri|mera)\s+(maut|death|mrityu)|"
    r"meri\s+death\s+(kab|kaise|hogi)|"
    r"(?:mera|meri|my)\s+death\b|"
    r"\bdeath\b.{0,24}\b(kab|when|hoga|hogi|honge|milega|pata)\b|"
    r"\b(maut|mrityu)\b.{0,24}\b(kab|when|hoga|hogi|honge)\b|"
    r"life\s+span|life\s+expectancy|lifespan|how\s+long\s+will\s+i\s+live|"
    r"kitne\s+saal\s+jiyu(?:nga|ngi)?|kitni\s+umar|umar\s+kitni|aayu\s+kitni|"
    r"longevity|when\s+will\s+i\s+die|when\s+do\s+i\s+die|"
    r"kab\s+tak\s+(zinda|alive|jiunga|jiyungi)|"
    r"mrityu\s+(kab|samay|tarikh|hogi)|"
    r"mar\s+ja(?:unga|ungi|oge)\s+kab|"
    r"alpayu|madhyayu|deerghayu|"
    r"jaan\s+bachegi|"
    r"मृत्यु|कब\s+मरूँ|कब\s+मरूंग|कब\s+मरungi|आयु|उम्र)",
    _re.IGNORECASE,
)

_DIAGNOSIS_DEMAND_RX = _re.compile(
    r"(mujhe\s+kya\s+(bimari|disease|illness)\s+(hai|hogi)|"
    r"kaun\s*si\s+(bimari|disease|illness)\s+(hai|hogi|hai\s+mujhe)|"
    r"mujhe\s+kaun\s*si\s+(bimari|disease|illness)|"
    r"(?:mujhse|mujhe|mere).{0,20}kya\s+kya\s+(?:bimari|disease|rog|illness)\s+ho\s+sak|"
    r"kya\s+kya\s+(?:bimari|disease|rog|illness)\s+ho\s+sak|"
    r"diagnose\s+me|diagnose\s+my\s+disease|diagnos\w*\s+(my\s+)?(disease|illness|condition)|"
    r"illness\s+name\s+from\s+(chart|kundli)|"
    r"tell\s+me\s+my\s+illness\s+name|"
    r"chart\s+se\s+(bimari|disease|illness)\s+(bata|tell|name|diagnos)|"
    r"chart\s+se\s+bata.{0,30}(bimari|disease|illness)|"
    r"chart\s+(me|mein)\s+(bimari|disease|illness)\s+(bata|name|kya|diagnos)|"
    r"from\s+chart.{0,20}(diagnos|disease|illness)|"
    r"am\s+i\s+having\s+(diabetes|cancer|tumor|tumour|hiv|aids))",
    _re.IGNORECASE,
)

# Specific disease-name prediction/diagnosis — NEVER answer (cancer, diabetes, etc.)
_DISEASE_NAME_DEMAND_RX = _re.compile(
    r"(?ix)"
    r"(?:\b(?:mujhe|mere|meri|do\s+i\s+have|am\s+i\s+having|will\s+i\s+get)\b.{0,40}\b(?:"
    r"cancer|kanser|tumor|tumour|carcinoma|diabetes|madhumeh|sugar\s+disease|"
    r"hiv|aids|tuberculosis|\btb\b|parkinson|epilepsy|schizophrenia|"
    r"leukemia|leukaemia|lymphoma|कैंसर|मधुमेह|ट्यूमर"
    r")\b)|"
    r"(?:\b(?:"
    r"cancer|kanser|tumor|tumour|diabetes|hiv|aids|कैंसर|मधुमेह|ट्यूमर"
    r")\b.{0,40}\b(?:hai|hoga|ho\s+sakta|ho\s+sakti|lagta|chart|kundli|mujhe|mera|meri)\b)|"
    r"(?:\bchart\b.{0,30}\b(?:cancer|kanser|tumor|tumour|diabetes|hiv|aids|कैंसर)\b)|"
    r"(?:क्या\s*)?मुझे.{0,25}(?:कैंसर|मधुमेह|ट्यूमर)"
)

_TIMING_DECLINE_RX = _re.compile(
    r"(kab\s+(beemar|bimar|sick|ill)\s+(honga|hungi|ho\s+jaunga)|"
    r"when\s+will\s+i\s+(fall\s+ill|get\s+sick|become\s+ill)|"
    r"bimari\s+(kab|kis\s+saal|kis\s+mahine)|"
    r"illness\s+kab|"
    r"disease\s+(kab|when)|"
    r"health\s+(kab\s+kharab|when\s+will\s+(deteriorate|fail))|"
    r"mujhe\s+kab\s+(bimari|disease|illness))",
    _re.IGNORECASE,
)

_TIMING_RECOVERY_RX = _re.compile(
    r"(kab\s+(thik|theek|swasth|healthy)\s+(honga|hungi|ho\s+jaunga|hounga)|"
    r"when\s+will\s+i\s+(recover|heal|get\s+better)|"
    r"recovery\s+(date|kab|when)|"
    r"thik\s+hone\s+ka\s+date|"
    r"cure\s+(kab|when|date)|"
    r"bimari\s+(kab\s+jayegi|kab\s+thik|exit\s+date))",
    _re.IGNORECASE,
)

_TIMING_SURGERY_RX = _re.compile(
    r"(operation\s+(kab|date|muhurat|kis\s+din)|"
    r"surgery\s+(kab|date|muhurat|when)|"
    r"best\s+date\s+for\s+(my\s+)?surgery|"
    r"surgery\s+date|"
    r"shastra[\s-]?kriya\s+kab|"
    r"muhurat\s+(operation|surgery))",
    _re.IGNORECASE,
)

_CURE_GUARANTEE_RX = _re.compile(
    r"(guarantee\s+(thik|cure|swasth|recover)|guaranteed\s+cure|guaranteed?\s+cure|"
    r"100\s*(?:%|percent|prcnt|pct)\s+(thik|cure|recover|theek)|"
    r"will\s+i\s+be\s+cured\s+100|"
    r"(cancer|diabetes|tumou?r|hiv|aids)\s+(thik\s+ho|pakka\s+thik|cure|theek)|"
    r"pakka\s+thik\s+ho\s+jayega|"
    r"(cancer|diabetes)\s+pakka\s+thik)",
    _re.IGNORECASE,
)


def detect_hard_guard(question: str) -> Optional[str]:
    """Only block crisis/self-harm and death/lifespan asks — all other health Qs answer."""
    if not isinstance(question, str) or not question.strip():
        return None
    if _CRISIS_RX.search(question):
        return "CRISIS_REDIRECT"
    if _DEATH_RX.search(question):
        return "REFUSE_DEATH"
    return None


# ── SENSITIVE bucket detection (extra-soft tone signal) ───────────────
_SENSITIVE_BUCKETS = (
    ("mental_health", _re.compile(
        r"\b(stress|anxiety|depression|tension|"
        r"mental|man\s+ashaant|udas|udaasi|chinta|"
        r"mood|ghabrahat|panic|insomnia|neend|sleep)\b",
        _re.IGNORECASE)),
    ("reproductive", _re.compile(
        r"\b(infertility|santaan|santan|baby|pregnancy|conceive|"
        r"miscarriage|garbh|bachcha\s+(nahi|hone)|fertility)\b",
        _re.IGNORECASE)),
    ("parent_health", _re.compile(
        r"\b(papa|mummy|mother|father|maa|pita|parent[s]?)\s+"
        r"(ki\s+|ke\s+|ka\s+)?(health|sehat|bimari|illness|tabiyat)",
        _re.IGNORECASE)),
    ("addiction", _re.compile(
        r"\b(addiction|nasha|alcohol|sharab|smoking|cigarette|"
        r"drug[s]?|tambaku|tobacco|gutka|substance\s+abuse)\b",
        _re.IGNORECASE)),
)


def detect_sensitive_bucket(question: str) -> Optional[str]:
    """Returns sensitive-bucket name if Q matches one, else None."""
    if not isinstance(question, str):
        return None
    for name, rx in _SENSITIVE_BUCKETS:
        if rx.search(question):
            return name
    return None


_NAMED_CONDITION_RX = _re.compile(
    r"(?ix)\b("
    r"asthma|asthama|diabetes|madhumeh|thyroid|thairoid|arthritis|epilepsy|"
    r"pcod|pcos|hypertension|migraine|allergy|tuberculosis|\btb\b|"
    r"cancer|kanser|tumor|tumour|hiv|aids|parkinson|schizophrenia|"
    r"कैंसर|मधुमेह|ट्यूमर|अस्थमा"
    r")\b"
)

# ── HEALTH-TOPIC GATE (port from health_static.health_routing) ────────
_HEALTH_TOPIC_RX = _re.compile(
    r"\b("
    r"health|sehat|swasthya|swasth|tabiyat|tabiyyat|"
    r"body|sharir|sharirik|"
    r"beemar|bimar|bimari|illness|disease|sick|"
    r"rog|rogi|"
    r"vitality|immunity|stamina|energy|"
    r"strength|weak|kamzor|kamzori|"
    r"recovery|recover|cure|thik|theek|"
    r"doctor|hospital|treatment|medicine|dawai|dava|therapy|"
    r"surgery|operation|specialist|diagnos|"
    r"chronic|long[\s-]?term|lambi|purani|"
    r"stress|anxiety|depression|mental|"
    r"man|mood|tension|chinta|"
    r"ashaant|udas|udaasi|pareshan|bechain[ai]?|ghabrahat|"
    r"neend|sleep|insomnia|"
    r"miracle|dua|chamatkar|"
    r"ajeeb|ajib|uneasy|weird|strange|unsettled|"
    r"khali\s*sa|khaali\s*sa|theek\s*nahi\s*lagta|"
    r"sardi|zukam|jukam|khansi|kha?ansi|cold|cough|fever|"
    r"bukhar|jukham|gala|throat|"
    r"pet|stomach|acidity|gas|digest|"
    r"sirdard|headache|migraine|"
    r"thakan|fatigue|tiredness|kamzori|weakness|"
    r"accident|injury|chot|durghatna|"
    r"neurolog|neurological|nerve|nerves|sensitivity|"
    r"infertility|santaan|santan|fertility|pregnancy|conceive|"
    r"addiction|nasha|sharab|smoking|"
    r"arishta|balarishta|vipreet[\s-]?recovery|"
    r"swasthya|aarogya|arogya|"
    r"asthma|asthama|diabetes|thyroid|arthritis|epilepsy|pcod|pcos|"
    r"hypertension|migraine|allergy"
    r")\b",
    _re.IGNORECASE,
)

# Animal/pet absolute-non-health context.
_ABSOLUTE_NON_HEALTH_RX = _re.compile(
    r"\b(kutta|kuttiya|kutti|kutte|billi|billiy|billiyon|dog|cat|janwar|"
    r"animal|puppy|kitten|paalt(u|oo))\b",
    _re.IGNORECASE,
)

# Devanagari health vocabulary — enables Hindi questions in scope gate
_HINDI_HEALTH_RX = _re.compile(
    r"(सेहत|स्वास्थ्य|स्वस्थ|बीमार|बिमार|तबीय|शरीर|मानस|मानसिक|तनाव|चिंता|"
    r"पेट|दिल|सांस|त्वचा|प्रतिरक्ष|ऊर्जा|शल्य|ऑपरेशन|मृत्यु|कैंसर|"
    r"गर्भ|माता|पिता|नश|आयु|उम्र|ट्यूमर|मधुमेह|नस|दुर्घटना|चोट|"
    r"नींद|अस्थि|जोड़|थायराइड|हार्मोन|खांसी|सर्दी|ठीक|क्षमता|प्रवृत्ति|"
    r"समस्या|दर्द|ताकत|अच्छी|कमजोरी|हृदय|पाचन|लंबी|जोखिम|संभावना|लत)",
)

_AMBIGUOUS_HEALTH_TOKENS_RX = _re.compile(
    r"\b(weakness|kamzori|kamzor|thakan|tiredness|fatigue|"
    r"pet|cold|cough|strange|weird|unsettled)\b",
    _re.IGNORECASE,
)

_STRONG_HEALTH_RX = _re.compile(
    r"\b(body|sharir|sharirik|sehat|tabiyat|swasthya|swasth|"
    r"health|bimari|bimar|beemar|illness|medical|disease|"
    r"stomach|acidity|digestion|digest|sirdard|headache|migraine|"
    r"sardi|zukam|jukam|fever|bukhar|"
    r"immunity|stamina|recovery|chronic|"
    r"stress|anxiety|depression|insomnia|"
    r"ghabrahat|bechain[ai]?|"
    r"man|mood|mental|"
    r"neend|sleep|"
    r"ajeeb\s+(sa|si)?\s*feel|"
    r"gala\s*kharab|"
    r"khansi|throat)\b",
    _re.IGNORECASE,
)

_NON_HEALTH_CTX_RX = _re.compile(
    r"\b(career|kaa?riyar|business|job|office|kaam(?!\s*nahi)|naukri|"
    r"spiritual|aatmik|aatma\b|atma\b|sadhana|dhyan(?!\s+dena)|"
    r"relationship|rishta|partner|love|pyaar|"
    r"financial|paisa|paise|money|wealth|dhan|"
    r"willpower|will\s*power|determination|motivation)\b",
    _re.IGNORECASE,
)


def is_health_question(question: str) -> bool:
    """True if Q is about general health AND not pure-finance/career/etc.
    Mirrors health_static.health_routing.is_health_question logic."""
    if not isinstance(question, str) or not question.strip():
        return False
    # 1. Absolute non-health context wins (pet animals)
    if _ABSOLUTE_NON_HEALTH_RX.search(question):
        return False
    # 2. Hard-guard patterns ALWAYS owned by health (so refuse fires)
    if detect_hard_guard(question) is not None:
        return True
    # 2a. User named a specific condition (e.g. "kya mujhse asthma hai")
    if _NAMED_CONDITION_RX.search(question):
        return True
    # 2b. Devanagari health words
    if _HINDI_HEALTH_RX.search(question):
        return True
    # 3. Health topic keyword present?
    if not _HEALTH_TOPIC_RX.search(question):
        return False
    # 4. Ambiguous-only context guard
    if (_AMBIGUOUS_HEALTH_TOKENS_RX.search(question)
            and not _STRONG_HEALTH_RX.search(question)
            and _NON_HEALTH_CTX_RX.search(question)):
        return False
    return True


def build_health_focus(question: str = "") -> str:
    """Permanently disabled — composable HEALTH FOCUS LLM prompt removed."""
    return ""


# ── CHART SLICER (drop dasha sections for STATIC/QUALITY) ─────────────
# Health STATIC_VITALITY / QUALITY_TENDENCY answers don't need dasha
# tree (Sec 4), upcoming dasha (Sec 5), gochar (Sec 8), or
# dasha+transit overlay (Sec 9). Trim BEFORE LLM call → cleaner prompt
# + fewer dasha-leaks. NO-OP when hard-guard is TIMING (refuse blocks
# need full chart available) — actually NO-OP for TIMING never applies
# since timing is refused; we slice for ALL non-refuse health Qs.

_DASHA_SECTION_NUMS = frozenset({"4", "5", "8", "9"})
_SECTION_BOUNDARY_RX = _re.compile(r'(?=^## \d+\.)', _re.MULTILINE)
_SECTION_NUM_RX = _re.compile(r'^## (\d+)\.')


def trim_dasha_sections(chart_block: str, question: str) -> Tuple[str, int]:
    """Drop dasha/transit sections from chart-context for health Qs.
    Returns (trimmed_block, sections_dropped). Defensive NO-OP on
    pattern mismatch or empty input."""
    if not isinstance(chart_block, str) or not chart_block.strip():
        return chart_block, 0
    if not _chart_slice_enabled():
        return chart_block, 0
    parts = _SECTION_BOUNDARY_RX.split(chart_block)
    if len(parts) <= 1:
        return chart_block, 0
    kept = []
    dropped = 0
    for p in parts:
        m = _SECTION_NUM_RX.match(p)
        if m and m.group(1) in _DASHA_SECTION_NUMS:
            dropped += 1
            continue
        kept.append(p)
    if dropped == 0:
        return chart_block, 0
    return ''.join(kept).rstrip() + '\n', dropped


# ── POST-INJECTORS ────────────────────────────────────────────────────
# H3.P1 — mandatory medical disclaimer (always-on for health answers).
_DISCLAIMER_LINE = (
    "\n\n_⚕️ Yeh chart-based insight hai, medical advice nahi. "
    "Kisi bhi health concern ke liye qualified doctor se zaroor milein._"
)

# Specialised disclaimers for sensitive buckets
_SENSITIVE_DISCLAIMERS = {
    "mental_health": (
        "\n\n_💚 Agar aap distress me ho — iCall +91-9152987821 "
        "ya Vandrevala +91-1860-2662-345 (24/7 free helpline) pe baat karo. "
        "Yeh chart-based insight hai, professional therapy nahi._"
    ),
    "reproductive": (
        "\n\n_⚕️ Yeh chart-based energetic-tendency hai, fertility advice nahi. "
        "Kisi qualified gynaecologist / fertility-specialist se zaroor milein._"
    ),
    "parent_health": (
        "\n\n_⚕️ Yeh chart-based supportive insight hai. Parent ki tabiyat ke "
        "liye immediate doctor consult primary hai — chart sirf ek dimension hai._"
    ),
    "addiction": (
        "\n\n_💚 Addiction recovery ke liye AA/NA support groups + qualified "
        "counsellor primary path hain. Chart sirf ek perspective deta hai. "
        "Bhai akele mat ladho — help leni strength hai._"
    ),
}

# H3.P2 — strip forbidden vocabulary from answer body
_DISEASE_NAME_RX = _re.compile(
    r"\b(diabetes|cancer|tumour|tumor|hiv|aids|"
    r"alzheimer|parkinson|hepatitis|tuberculosis|tb\b|"
    r"leukemia|leukaemia|lymphoma|carcinoma|sarcoma)\b",
    _re.IGNORECASE,
)

_CURE_GUARANTEE_OUTPUT_RX = _re.compile(
    r"\b(100\s*%\s+(?:cure|thik|recover|theek)|"
    r"guaranteed?\s+(?:cure|recovery|thik|theek)|"
    r"definitely\s+(?:thik|theek|cure|recover))\b",
    _re.IGNORECASE,
)


def strip_forbidden_vocab(text: str) -> Tuple[str, int]:
    """Replace forbidden disease names + cure-guarantee phrasings with
    safe alternatives. Returns (cleaned_text, replacements_made)."""
    if not isinstance(text, str) or not text.strip():
        return text, 0
    count = 0
    new = text

    def _disease_repl(m: _re.Match) -> str:
        nonlocal count
        count += 1
        return "specific condition"

    new = _DISEASE_NAME_RX.sub(_disease_repl, new)

    def _cure_repl(m: _re.Match) -> str:
        nonlocal count
        count += 1
        return "supportive recovery-tendency"

    new = _CURE_GUARANTEE_OUTPUT_RX.sub(_cure_repl, new)
    return new, count


def inject_medical_disclaimer(answer_text: str, question: str) -> str:
    """H3.P1 post-injector — append the mandatory medical disclaimer
    (sensitive-bucket-specific if applicable) to the answer body.
    Idempotent: skips if disclaimer marker already present.

    Killswitch: HEALTH_DISCLAIMER=0/false/no/off → NO-OP.
    """
    if not _disclaimer_enabled():
        return answer_text
    if not isinstance(answer_text, str):
        return answer_text
    # Idempotency check (look for the unique marker emoji + key phrase)
    if ("⚕️ Yeh chart-based" in answer_text
            or "💚 Agar aap distress" in answer_text
            or "💚 Addiction recovery" in answer_text):
        return answer_text
    bucket = detect_sensitive_bucket(question)
    disc = _SENSITIVE_DISCLAIMERS.get(bucket, _DISCLAIMER_LINE)
    return (answer_text or "").rstrip() + disc


def inject_health_engine_verdict(answer_text: str,
                                   question: str = "") -> str:
    """Deterministic Health Engine v1 post-injector.

    If the most recent `compute_health_window()` produced a verdict on
    this thread (stashed by `health_engine_v1.get_last_health_result()`),
    enforce a `👉 Final:` line near the end of the answer carrying the
    engine verdict + recommendation tier verbatim. This is the safety
    net for cases where the LLM either skips the verdict or paraphrases
    it (mirrors the Marriage NARRATOR-MODE enforcement).

    Idempotent: if the engine line already appears, no change. If no
    engine result is cached (engine wasn't run for this Q), no-op.
    Killswitch: HEALTH_DISCLAIMER off → no-op (same env as the rest of
    the H3 post-injector pipeline).
    """
    if not answer_text:
        return answer_text or ""
    if not _disclaimer_enabled():
        return answer_text
    try:
        from event_timing.health.health_engine_v1 import (  # type: ignore
            get_last_health_result,
        )
    except Exception:
        return answer_text
    res = get_last_health_result()
    if not isinstance(res, dict) or not res.get("verdict"):
        return answer_text
    verdict = str(res.get("verdict") or "").strip()
    tier = str(res.get("recommendation_tier") or "").strip()
    if not verdict:
        return answer_text
    # Architect-fix: never inject for UNKNOWN gates (data missing /
    # engine exception) — those should fall through to the LLM's own
    # framing rather than nailing a generic "saaf reading nahi" line
    # onto every answer where the engine couldn't compute.
    if verdict == "UNKNOWN":
        return answer_text
    # Idempotency — bail if our exact tag already present
    tag = "[engine: health-v1]"
    if tag in answer_text:
        return answer_text
    # Architect-fix: if the LLM already produced a "👉 Final:" line, strip
    # it so the engine line becomes the authoritative final (avoid
    # duplicate finals stacking).
    body = answer_text
    try:
        import re as _re
        body = _re.sub(r"(?m)^\s*👉\s*Final:.*(?:\n|$)", "", body).rstrip()
    except Exception:
        body = answer_text
    # Gentle, non-clinical phrasing (CAFB-health translation rules).
    verdict_label = {
        "STRONG_VITALITY":   "swasthya bal majboot dikh raha hai",
        "STABLE":            "swasthya stable lag raha hai",
        "VULNERABLE":        "swasthya pe abhi extra dhyan ki zarurat hai",
        "HIGH_RISK_WINDOW":  "swasthya ko abhi sambhal ke chalna chahiye",
        "UNKNOWN":           "swasthya ki saaf reading nahi mil rahi",
    }.get(verdict, verdict.lower())
    tier_label = {
        "monitor":         "rozmarra ki monitoring kafi hai",
        "preventive":      "preventive habits + routine check-up rakhein",
        "consult":         "ek bar professional doctor se baat kar lijiye",
        "urgent_consult":  "jaldi kisi qualified doctor se mil lijiye",
    }.get(tier, tier)
    line = f"\n\n👉 Final: {verdict_label} — {tier_label}. {tag}"
    return body.rstrip() + line


def apply_health_postinjectors(answer_text: str, question: str) -> str:
    """Convenience: run all health post-injectors in correct order.
    1. strip_forbidden_vocab (clean body)
    2. inject_health_engine_verdict (engine-fact citation safety net)
    3. inject_medical_disclaimer (append safety footer)
    """
    cleaned, _ = strip_forbidden_vocab(answer_text)
    cleaned = inject_health_engine_verdict(cleaned, question)
    return inject_medical_disclaimer(cleaned, question)


# ── PUBLIC API SUMMARY ────────────────────────────────────────────────
__all__ = [
    "build_health_focus",
    "detect_hard_guard",
    "detect_sensitive_bucket",
    "is_health_question",
    "trim_dasha_sections",
    "strip_forbidden_vocab",
    "inject_medical_disclaimer",
    "inject_health_engine_verdict",
    "apply_health_postinjectors",
]

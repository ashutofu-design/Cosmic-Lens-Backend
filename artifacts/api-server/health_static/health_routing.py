"""Health question router (NON-TIMING general health).

Pure regex-based classifier. Maps user question to one of:
  - WARNING:<key>      -> return locked warning template (0 LLM)
  - DIRECT:<route>     -> format engine facts directly (0 LLM)
  - NARRATIVE:<route>  -> engine facts + 60-80w LLM polish
  - HYBRID:<route>     -> DIRECT 5-dim picture + short LLM narrative

NO LLM is used here. Pure rule-based dispatch.

EXCLUSION FIRST:
  1. TIMING Qs ("kab beemar honga", "kab thik honga", "operation kab")
     are routed to WARNING templates (timing_health_decline /
     timing_recovery / timing_surgery) — health engine refuses to
     predict timing, gently redirects to consult doctor.
  2. DEATH / longevity Qs ("kab marunga", "death kab") → WARNING
     (death_prediction_blocked) — hard refusal.
  3. Generic mental-health crisis phrases ("suicide", "khatam") →
     WARNING (crisis_redirect) — show helpline + urge professional help.

Sensitive buckets (mental_health / reproductive / parent_health /
addiction) flagged separately so reply layer can soften tone further.
"""
from __future__ import annotations
import re
from typing import Tuple

# ── HARD WARNINGS — checked FIRST (highest priority) ────────────────
# These BYPASS the topic gate so even loosely-phrased questions land
# on the locked safe-template.
_WARN_PATTERNS = [
    # CRISIS — suicide / self-harm phrasing → helpline redirect
    (r"(suicide|khud[\s-]?kushi|atm[\s-]?hatya|atmhatya|"
     r"khatam\s+kar\s+(lu|du|dunga|loon)|"
     r"jeena\s+nahi\s+chahta|marna\s+chahta|"
     r"end\s+(my\s+)?life|kill\s+(myself|me))",
     "CRISIS_REDIRECT"),
    # DEATH / longevity prediction
    (r"(kab\s+marunga|kab\s+marungi|kab\s+(meri|mera)\s+(maut|death|mrityu)|"
     r"meri\s+death\s+(kab|kaise)|life\s+span|kitne\s+saal\s+jiyu(?:nga|ngi)?|"
     r"umar\s+kitni|longevity|when\s+will\s+i\s+die|"
     r"kab\s+tak\s+(zinda|alive|jiunga|jiyungi)|"
     r"mrityu\s+(kab|samay|tarikh))",
     "DEATH_PREDICTION_BLOCKED"),
    # DIAGNOSIS demand — checked BEFORE timing so "kaun si bimari hai"
    # routes to diagnosis-refusal not timing-refusal (architect H2 fix).
    (r"(mujhe\s+kya\s+(bimari|disease|illness)\s+hai|"
     r"kaun\s*si\s+(bimari|disease|illness)\s+(hai|hogi|hai\s+mujhe)|"
     r"mujhe\s+kaun\s*si\s+(bimari|disease|illness)|"
     r"diagnose\s+me|"
     r"chart\s+se\s+(bimari|disease|illness)\s+(bata|tell|name)|"
     r"chart\s+se\s+bata.{0,30}(bimari|disease|illness)|"
     r"chart\s+(me|mein)\s+(bimari|disease|illness)\s+(bata|name|kya))",
     "DIAGNOSIS_DEMAND"),
    # TIMING — kab beemar honga / health decline date
    # (Removed "kaun si" alternation — that is diagnosis-demand, handled above.)
    (r"(kab\s+(beemar|bimar|sick|ill)\s+(honga|hungi|ho\s+jaunga)|"
     r"bimari\s+(kab|kis\s+saal|kis\s+mahine)|"
     r"disease\s+(kab|when)|"
     r"health\s+(kab\s+kharab|when\s+will\s+(deteriorate|fail))|"
     r"mujhe\s+kab\s+(bimari|disease|illness))",
     "TIMING_HEALTH_DECLINE"),
    # TIMING — recovery / cure date
    (r"(kab\s+(thik|theek|swasth|healthy)\s+(honga|hungi|ho\s+jaunga|hounga)|"
     r"recovery\s+(date|kab|when)|"
     r"cure\s+(kab|when|date)|"
     r"bimari\s+(kab\s+jayegi|kab\s+thik|exit\s+date))",
     "TIMING_RECOVERY"),
    # TIMING — operation / surgery muhurat
    (r"(operation\s+(kab|date|muhurat|kis\s+din)|"
     r"surgery\s+(kab|date|muhurat|when)|"
     r"shastra[\s-]?kriya\s+kab|"
     r"muhurat\s+(operation|surgery))",
     "TIMING_SURGERY"),
    # CURE GUARANTEE — "will my cancer cure", "guarantee thik hounga"
    (r"(guarantee\s+(thik|cure|swasth)|"
     r"100\s*%\s+(thik|cure|recover)|"
     r"(cancer|diabetes|tumour|tumor|hiv|aids)\s+(thik\s+ho|cure|theek))",
     "CURE_GUARANTEE_BLOCKED"),
]

# ── DIRECT (pure engine, no LLM) ────────────────────────────────────
_DIRECT_PATTERNS = [
    # Multi-dim vitality verdict — primary route
    (r"(vitality|body\s+strength|immunity\s+(check|kaisi|level)|"
     r"meri\s+(health|sehat|swasthya)\s+(kaisi|kaisa|status|condition)|"
     r"health\s+(verdict|analysis|status|picture|report)|"
     r"overall\s+health|sehat\s+kaisi)",
     "vitality_check"),
    # Phase H2.5 — broad TENDENCY / FUTURE-RISK overview Qs.
    # User intent: "kaun-kaun se issues" / "future me kya tendencies"
    # / "aage chal ke kya risk" → wants multi-dim picture, NOT a
    # narrow disease_risk close-up. Route to vitality_check (full
    # 5-dim Truth block) so Tendency-issues block has all dims to
    # draw from.
    (r"(kaun[\s-]?kaun\s+(se|si)?\s*(health|swasthya|sehat|bimari|issues?|problems?|tendency|tendencies)|"
     r"(future|aage|aane\s+wale|aage\s+chal\s+ke)\s+.{0,40}(health|swasthya|sehat|issues?|problems?|tendency|tendencies|risk|bimari)|"
     r"health\s+tendenc(y|ies)|tendency\s+of\s+(health|illness|issues?)|"
     r"kya[\s-]?kya\s+(health|issues?|problems?|bimari|tendency|tendencies)|"
     r"kis[\s-]?kis\s+(health|bimari|issues?)|"
     r"(probable|possible|likely)\s+health\s+(issues?|problems?|risks?)|"
     r"health\s+risk\s+(profile|areas?|zones?))",
     "vitality_check"),
    # Yoga audit (Arishta / Balarishta / Vipreet recovery)
    (r"(health\s+yog|arishta|balarishta|"
     r"vipreet\s+(recovery|health)|"
     r"chart\s+me\s+(health|swasthya)\s+(yog|combination))",
     "yoga_check"),
]

# ── NARRATIVE (engine + LLM polish) ─────────────────────────────────
_NARRATIVE_PATTERNS = [
    # DISEASE risk — recurring illness, low immunity
    (r"(baar[\s-]?baar\s+(beemar|bimar|sick|ill)|"
     r"jaldi[\s-]?jaldi\s+(beemar|bimar|sick)|"
     r"immunity\s+(weak|kam|kharab|low)|"
     r"recover\s+(slow|nahi|nhi)|"
     r"recovery\s+(slow|kam|weak)|"
     r"rog[\s-]?pratirodh|"
     r"frequently\s+(sick|ill|getting\s+sick))",
     "disease_risk"),
    # CHRONIC risk — long-term illness susceptibility
    (r"(chronic|long[\s-]?term\s+(illness|problem|bimari)|"
     r"lambi\s+bimari|"
     r"purani\s+bimari|"
     r"genetic\s+(disease|risk|history)|"
     r"family\s+history\s+(disease|illness)|"
     r"hereditary)",
     "chronic_risk"),
    # MENTAL health — stress, anxiety, depression, mind peace
    (r"(stress|tension|anxiety|depression|"
     r"mental\s+(health|peace|stress|state)|"
     r"man\s+(ashaant|udas|thik\s+nahi|pareshan|bechain)|"
     r"mood\s+(off|swing|low|depressed)|"
     r"udaasi|chinta|ghabrahat|"
     r"neend\s+nahi|insomnia|sleep\s+(problem|nahi))",
     "mental_health"),
    # ACCIDENT risk — sudden injury / physical harm
    (r"(accident\s+(risk|chance|hoga|honga|ka\s+yog)|"
     r"injury\s+(risk|chance|hoga)|"
     r"chot\s+(lagne|ka\s+yog|risk)|"
     r"physical\s+(harm|safety|injury)|"
     r"durghatna)",
     "accident_risk"),
]

# ── Sensitive bucket detection (extra-soft tone) ────────────────────
_SENSITIVE_BUCKETS = [
    ("mental_health",
     re.compile(r"(stress|anxiety|depression|tension|"
                r"mental|man\s+ashaant|udas|udaasi|chinta|"
                r"mood|ghabrahat|panic|insomnia|neend|sleep)",
                re.IGNORECASE)),
    ("reproductive",
     re.compile(r"(infertility|santaan|santan|baby|pregnancy|conceive|"
                r"miscarriage|garbh|bachcha\s+(nahi|hone)|fertility)",
                re.IGNORECASE)),
    ("parent_health",
     re.compile(r"(papa|mummy|mother|father|maa|pita|parent[s]?)\s+"
                r"(ki\s+|ke\s+|ka\s+)?(health|sehat|bimari|illness|tabiyat)",
                re.IGNORECASE)),
    ("addiction",
     re.compile(r"(addiction|nasha|alcohol|sharab|smoking|cigarette|"
                r"drug[s]?|tambaku|tobacco|gutka|substance\s+abuse)",
                re.IGNORECASE)),
]


def detect_sensitive_bucket(question: str) -> str | None:
    """Returns sensitive-bucket name if Q matches one, else None.
    Reply layer uses this to soften tone + add bucket-specific
    disclaimer (mental → helpline; repro → fertility specialist; etc.)."""
    if not isinstance(question, str):
        return None
    for name, rx in _SENSITIVE_BUCKETS:
        if rx.search(question):
            return name
    return None


# ── Health topic detection (gate) — broad health keywords ───────────
_HEALTH_TOPIC_RX = re.compile(
    r"\b("
    # Generic health words
    r"health|sehat|swasthya|swasth|tabiyat|"
    r"body|sharir|sharirik|"
    # Illness / disease (generic)
    r"beemar|bimar|bimari|illness|disease|sick|"
    r"rog|rogi|"
    # Vitality / immunity
    r"vitality|immunity|stamina|energy|"
    r"strength|weak|kamzor|kamzori|"
    # Recovery
    r"recovery|recover|cure|thik|theek|swasth|"
    # Chronic / long-term
    r"chronic|long[\s-]?term|lambi|purani|"
    # Mental
    r"stress|anxiety|depression|mental|"
    r"man|mood|tension|chinta|"
    r"ashaant|udas|udaasi|pareshan|bechain[ai]?|ghabrahat|"
    r"neend|sleep|insomnia|"
    # H2.7.18 — vague-discomfort vocabulary
    r"ajeeb|ajib|uneasy|weird|strange|unsettled|"
    r"khali\s*sa|khaali\s*sa|theek\s*nahi\s*lagta|"
    # H2.7.19 — common ailment vocab
    r"sardi|zukam|jukam|khansi|kha?ansi|cold|cough|fever|"
    r"bukhar|jukham|gala|throat|"
    r"pet|stomach|acidity|gas|digest|"
    r"sirdard|headache|migraine|"
    r"thakan|fatigue|tiredness|kamzori|weakness|"
    # Accident
    r"accident|injury|chot|durghatna|"
    # Reproductive
    r"infertility|santaan|santan|fertility|pregnancy|conceive|"
    # Sensitive sub-topics
    r"addiction|nasha|sharab|smoking|"
    # Yogas + classical
    r"arishta|balarishta|vipreet[\s-]?recovery|"
    # Direct verbs
    r"swasthya|aarogya|arogya"
    r")\b",
    re.IGNORECASE,
)


# H2.7.19 — Context guards for AMBIGUOUS health tokens.
# Tokens like "weakness/kamzori/thakan/pet/cold" can appear in
# career/spiritual/business/relationship/animal contexts and should
# NOT be routed to health engine in those cases.
_AMBIGUOUS_HEALTH_TOKENS_RX = re.compile(
    r"\b(weakness|kamzori|kamzor|thakan|tiredness|fatigue|"
    r"pet|cold|cough|strange|weird|unsettled)\b",
    re.IGNORECASE,
)
# Strong-health signals — if any present, ambiguous-token guard is
# bypassed (user clearly means body health).
_STRONG_HEALTH_RX = re.compile(
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
    re.IGNORECASE,
)
# Non-health metaphor contexts.
_NON_HEALTH_CTX_RX = re.compile(
    r"\b(career|kaa?riyar|business|job|office|kaam(?!\s*nahi)|naukri|"
    r"spiritual|aatmik|aatma\b|atma\b|sadhana|dhyan(?!\s+dena)|"
    r"relationship|rishta|partner|love|pyaar|"
    r"financial|paisa|paise|money|wealth|dhan|"
    r"willpower|will\s*power|determination|motivation|"
    r"kutta|billi|dog\b|cat\b|animal|janwar)\b",
    re.IGNORECASE,
)


def _is_ambiguous_only_match(question: str) -> bool:
    """True if Q matches health regex ONLY via ambiguous tokens
    (no strong health signal anywhere)."""
    if not _AMBIGUOUS_HEALTH_TOKENS_RX.search(question):
        return False
    return not _STRONG_HEALTH_RX.search(question)


# H2.7.19 — ABSOLUTE non-health context (animal/pet) — wins even
# over strong health signals like "bimar/sick", because "Mera pet
# bimar hai, kutta" is clearly about an animal, not the user.
_ABSOLUTE_NON_HEALTH_RX = re.compile(
    r"\b(kutta|kuttiya|billi|dog|cat|janwar|"
    r"animal|puppy|kitten|paalt(u|oo))\b",
    re.IGNORECASE,
)


def is_health_question(question: str) -> bool:
    """True if Q is about general health AND not pure-finance/marriage/etc.

    Guard order (H2.7.19):
      1. ABSOLUTE non-health context (animal/pet words) → False, even
         if strong health words present (user is asking about their
         pet animal, not themselves).
      2. WARNING patterns (incl. timing/death/diagnosis demands) →
         ALWAYS handled by us so the safe template fires.
      3. Health topic keyword present → we own it.
      4. Context guard: if match is ONLY via ambiguous tokens
         (weakness/kamzori/thakan/pet/cold) AND a non-health context
         word is present → False (let other engines handle).
      5. Otherwise False (caller continues to other engines).
    """
    if not isinstance(question, str) or not question.strip():
        return False
    # 1. Absolute non-health context wins (pet animals)
    if _ABSOLUTE_NON_HEALTH_RX.search(question):
        return False
    # 2. WARNING patterns bypass the topic gate
    for pat, _key in _WARN_PATTERNS:
        if re.search(pat, question, re.IGNORECASE):
            return True
    if not _HEALTH_TOPIC_RX.search(question):
        return False
    # 4. Ambiguous-only context guard
    if _is_ambiguous_only_match(question) and \
       _NON_HEALTH_CTX_RX.search(question):
        return False
    return True


def route_health_question(question: str) -> Tuple[str, str]:
    """Returns (mode, route_id). Modes: WARNING | DIRECT | NARRATIVE | HYBRID.

    Catch-all fallback (per user directive — broad ownership):
      ('HYBRID', 'general_health_overview') — DIRECT 5-dim picture +
      short LLM narrative line. Used when no specific pattern fires.
    """
    q = (question or "").lower()

    for pat, key in _WARN_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return ("WARNING", key)

    for pat, route in _DIRECT_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return ("DIRECT", route)

    for pat, route in _NARRATIVE_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return ("NARRATIVE", route)

    return ("HYBRID", "general_health_overview")

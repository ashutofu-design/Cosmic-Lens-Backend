"""
User Context Memory Layer (UCML) — Phase 1
============================================

Silent, deterministic memory module. The ENGINE (this file) reads/writes
PostgreSQL user_facts / user_behavior / user_personality tables. The LLM
NEVER touches the DB directly — it only receives a curated enrichment
bundle assembled here, injected as silent prompt context.

Public surface (engine-facing):

    upsert_fact(user_id, key, value, confidence, source_ref)
        — Insert-or-update one atomic fact. Idempotent.

    extract_and_store_facts(user_id, question_text, source_ref)
        — Run the regex fact-extractor on a question and persist any
          high-confidence facts found. Fire-and-forget; failures swallowed.

    load_bundle(user_id)
        — Build the silent enrichment bundle (L1+L2+L3 + realtime context).
          Returns a dict; engine injects relevant slices into prompt.

    inject_into_prompt(bundle, base_prompt)
        — Prepend a SILENT context block to base_prompt. The block is
          marked SYSTEM-ONLY so the LLM treats it as private context and
          never recites it back to the user.

Design locks (per user spec):
  • Silent enrichment, never confession.  LLM must NEVER tell the user
    "you mentioned X before".
  • Engine is the brain, LLM is the language polisher.
  • Free: pure regex + DB; no per-call LLM cost.
  • Universal: applies to every user from question #1.
  • Self-correcting: every new question refines existing facts.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from database import db
from models import UserFact, UserBehavior, UserPersonality, UserQuestion


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# Below this confidence, facts are used silently for routing/scoring only —
# they never appear in user-facing output.
_CONF_FLOOR_USER_FACING = 0.85

# Hard bounds on stored values (mirrors column widths in models.py)
_MAX_FACT_VALUE_LEN = 200


# ─────────────────────────────────────────────────────────────────────────────
# L1 — Regex fact extractor (50 atomic keys)
#
# Each rule is (fact_key, fact_value, confidence, regex_pattern). The pattern
# is matched against the lowercased question text. First match wins per key.
# Rules ordered most-specific → most-general so granular signals beat broad.
# ─────────────────────────────────────────────────────────────────────────────

_FACT_RULES: List[Tuple[str, str, float, str]] = [
    # ── Family / relationship signals ────────────────────────────────────
    ("marital_status", "married",    0.97,
        r"\b(meri\s+(patni|biwi|wife)|mere\s+(pati|husband)|"
        r"mere\s+(sasur(al)?|saas)|shaadi-?shuda|"
        r"meri\s+wife|mera\s+husband)\b"),
    ("marital_status", "divorced",   0.95,
        r"\b(talaq|divorce[ds]?|separation|alag\s+ho\s+gay[ae])\b"),
    ("marital_status", "widowed",    0.95,
        r"\b(widow(er|ed)?|vidhwa|late\s+(husband|wife|pati|patni))\b"),
    ("marital_status", "engaged",    0.90,
        r"\b(engag(ed|ement)|sagai|mangni)\b"),
    ("marital_status", "single",     0.85,
        r"\b(kunwar[ae]?|single\s+hoon|abhi\s+tak\s+shaadi\s+nahi)\b"),

    ("has_children",   "true",       0.98,
        r"\b(mere\s+(bachhe|bachche|bete|beti|kids|child(ren)?|baby)|"
        r"mera\s+(beta|son)|meri\s+beti|"
        r"hamare\s+(bachhe|bachche))\b"),
    ("child_gender",   "son",        0.95,
        r"\b(mere\s+(bete|son)|mera\s+(beta|son))\b"),
    ("child_gender",   "daughter",   0.95,
        r"\b(meri\s+(beti|daughter)|mere\s+ladk[iy]a?)\b"),

    ("is_parent",      "true",       0.96,
        r"\b(parent|parenting|father|mother|maa\s+hoon|papa\s+hoon|"
        r"mere\s+(bete|beti|bachhe))\b"),

    # ── Profession hints (FIRST-PERSON ONLY — guards against "doctor ne
    #     bola..." or "mera beta doctor banna chahta" mis-tagging) ───────
    ("profession_hint", "tech_it",    0.88,
        r"\b(i\s+am\s+(a\s+)?(software|developer|engineer|programmer)|"
        r"i'?m\s+(a\s+)?(software|developer|engineer|programmer)|"
        r"main\s+(software|developer|engineer|programmer)|"
        r"mai\s+(software|developer|engineer|programmer)|"
        r"mera\s+job\s+(it|tech|software)|my\s+job\s+is\s+(it|tech|software))\b"),
    ("profession_hint", "medical",    0.88,
        r"\b(i\s+am\s+(a\s+)?(doctor|nurse|surgeon|dentist|physician)|"
        r"i'?m\s+(a\s+)?(doctor|nurse|surgeon|dentist|physician)|"
        r"main\s+(doctor|nurse|surgeon|dentist)\s+(hoon|hu|hun)|"
        r"mai\s+(doctor|nurse|surgeon|dentist)\s+(hoon|hu|hun))\b"),
    ("profession_hint", "teaching",   0.88,
        r"\b(i\s+am\s+(a\s+)?(teacher|professor|tutor)|"
        r"i'?m\s+(a\s+)?(teacher|professor|tutor)|"
        r"main\s+(teacher|professor|tutor)\s+(hoon|hu|hun)|"
        r"mai\s+(teacher|professor|tutor)\s+(hoon|hu|hun))\b"),
    ("profession_hint", "business",   0.88,
        r"\b(main\s+business\s+(karta|karti)\s+(hoon|hu|hun)|"
        r"i\s+(run|own|have)\s+(a\s+)?(business|company|startup)|"
        r"apna\s+(business|kaam)\s+(karta|karti)\s+(hoon|hu|hun)|"
        r"i\s+am\s+(an?\s+)?entrepreneur|self[\s-]employed)\b"),
    ("profession_hint", "govt",       0.88,
        r"\b(i\s+(have|am\s+in)\s+(a\s+)?(government|govt)\s+job|"
        r"main\s+(government|sarkari)\s+naukri|"
        r"meri\s+sarkari\s+naukri|i'?m\s+(an?\s+)?(ias|ips|civil\s+servant))\b"),
    ("profession_hint", "student",    0.92,
        r"\b(i\s+am\s+(a\s+)?student|i'?m\s+(a\s+)?student|"
        r"main\s+student\s+(hoon|hu|hun)|"
        r"mai\s+student\s+(hoon|hu|hun)|"
        r"padhai\s+kar\s+rah[ai]\s+(hoon|hu|hun)|"
        r"college\s+mein\s+(hoon|hu|hun))\b"),
    ("profession_hint", "homemaker",  0.88,
        r"\b(i\s+am\s+(a\s+)?(housewife|homemaker)|"
        r"i'?m\s+(a\s+)?(housewife|homemaker)|"
        r"main\s+(housewife|homemaker|grihini)\s+(hoon|hu|hun)|"
        r"mai\s+(housewife|homemaker|grihini)\s+(hoon|hu|hun))\b"),

    # ── Location signals (city level) ────────────────────────────────────
    ("location_city",  "mumbai",     0.90,
        r"\b(mumbai|bombay|navi\s+mumbai|thane)\b"),
    ("location_city",  "delhi",      0.90,
        r"\b(delhi|new\s+delhi|gurgaon|gurugram|noida)\b"),
    ("location_city",  "bangalore",  0.90,
        r"\b(bangalore|bengaluru)\b"),
    ("location_city",  "pune",       0.90,
        r"\b(pune|poona)\b"),
    ("location_city",  "hyderabad",  0.90,
        r"\b(hyderabad|secunderabad)\b"),
    ("location_city",  "chennai",    0.90,
        r"\b(chennai|madras)\b"),
    ("location_city",  "kolkata",    0.90,
        r"\b(kolkata|calcutta)\b"),

    # ── Concern / topic obsessions (recurrent themes) ────────────────────
    ("health_concern", "immunity",   0.90,
        r"\b(immunity|sardi-?khansi|baar-?baar\s+bimar|infection)\b"),
    ("health_concern", "mental",     0.90,
        r"\b(depress|anxiety|tension|stress|mental\s+health|"
        r"neend\s+nahi\s+aati)\b"),
    ("health_concern", "chronic",    0.85,
        r"\b(diabetes|sugar|bp|blood\s+pressure|thyroid|asthma)\b"),
    ("health_concern", "weight",     0.85,
        r"\b(weight|wajan|motapa|obesity|patla\s+hona)\b"),

    ("career_concern", "job_change", 0.90,
        r"\b(job\s+change|naukri\s+(badal|chhod)|switch\s+karna|"
        r"resign|new\s+role)\b"),
    ("career_concern", "promotion",  0.85,
        r"\b(promotion|tarakki|salary\s+hike|appraisal)\b"),
    ("career_concern", "study_abroad", 0.90,
        r"\b(study\s+abroad|videsh\s+padhai|ms\s+kar|phd|gre|gmat)\b"),

    ("finance_concern", "loan_debt", 0.90,
        r"\b(loan|karz|emi|debt|udhaar|dena\s+hai\s+paisa)\b"),
    ("finance_concern", "investment", 0.85,
        r"\b(invest|stocks|share\s+market|mutual\s+fund|sip|crypto)\b"),
    ("finance_concern", "property",   0.85,
        r"\b(property|ghar\s+kharidna|flat\s+lena|plot|real\s+estate)\b"),

    ("relationship_concern", "love_marriage", 0.90,
        r"\b(love\s+marriage|prem\s+vivah|inter[\s-]?caste)\b"),
    ("relationship_concern", "compatibility", 0.85,
        r"\b(kundli\s+milan|guna\s+milan|matching|compatibility)\b"),
    ("relationship_concern", "breakup", 0.90,
        r"\b(breakup|alag\s+ho\s+gaye|relationship\s+khatm|"
        r"todna\s+chahti|todna\s+chahta)\b"),

    # ── Spiritual / dharmic interest ─────────────────────────────────────
    ("spiritual_interest", "high",   0.85,
        r"\b(puja|mantra|jaap|meditation|sadhana|"
        r"bhagwan|spiritual\s+practice)\b"),
    ("dosha_concern",      "manglik", 0.95,
        r"\b(manglik|mangal\s+dosh|mars\s+dosh)\b"),
    ("dosha_concern",      "kalsarp", 0.95,
        r"\b(kal\s*sarp|kalsarp|rahu-?ketu\s+axis)\b"),
    ("dosha_concern",      "sade_sati", 0.95,
        r"\b(sade\s*sati|saade\s*saati|saturn\s+7\s+years)\b"),

    # ── Technical astrology curiosity (not concern) ──────────────────────
    ("technical_interest_astrology", "true", 0.92,
        r"\b(\d+(st|nd|rd|th)\s+(house|lord|csl)|"
        r"navamsa|nakshatra|sub\s+lord|antardasha|"
        r"mahadasha|divisional\s+chart|jaimini|kp\s+system)\b"),

    # ── Language preference: handled by _detect_language() below, NOT
    #     by simple regex (Latin-charset is too greedy — it tagged
    #     romanized Hindi like "mera bete ki shaadi kab hogi" as English).
    #     See extract_facts_from_text() for the smarter detection.

    # ── Mood baseline signals (recurrent emotional pattern) ──────────────
    ("mood_baseline",   "anxious",   0.80,
        r"\b(dar(\s+lagta)?|chinta|tension|fikr|worry|scared|"
        r"please\s+(bata|help))\b"),
    ("mood_baseline",   "frustrated", 0.80,
        r"\b(kuch\s+nahi\s+ho\s+raha|fed\s+up|tang\s+aa\s+gay[ae]|"
        r"thak\s+gay[ae])\b"),
    ("mood_baseline",   "hopeful",   0.75,
        r"\b(achchi\s+khabar|good\s+news|positive\s+ho|umeed)\b"),

    # ── Life-event markers ───────────────────────────────────────────────
    ("life_event",      "job_loss",  0.90,
        r"\b(job\s+(chala\s+gaya|lost|gone)|naukri\s+chali\s+gayi|"
        r"layoff)\b"),
    ("life_event",      "bereavement", 0.92,
        r"\b(passed\s+away|guzar\s+gaye|gujr\s+gaye|"
        r"father\s+died|mother\s+died|papa\s+nahi\s+rahe)\b"),
    ("life_event",      "new_baby",  0.90,
        r"\b(new\s+born|abhi\s+pregnant|delivery\s+hui|baby\s+hua)\b"),
]


def _matches(text: str, pattern: str) -> bool:
    try:
        return bool(re.search(pattern, text, re.IGNORECASE))
    except re.error:
        return False


# Common Romanized-Hindi function words. If any are present alongside
# Latin script, the question is hinglish/hindi — NOT English. This avoids
# the "everything in latin = english" bug.
_HI_ROMAN_TOKENS = re.compile(
    r"\b(kya|kaise|kaisi|kab|kyun|kyu|kahan|kaha|kis|kisi|"
    r"hai|hain|hoga|hogi|honge|hota|hoti|tha|thi|the|"
    r"mera|meri|mere|tera|teri|tere|hamara|hamari|"
    r"aap|tum|hum|main|mai|mujhe|mujhse|aapko|tumko|"
    r"nahi|nahin|haan|han|kuch|kuchh|sab|sabko|"
    r"chahta|chahti|chahiye|karna|karega|karegi|karenge|"
    r"hua|hui|huye|huyi|raha|rahi|rahe|"
    r"shaadi|kundli|grah|dosh|rashi|nakshatra|bhagya|"
    r"bata|batao|bataiye|bhai|behen|maa|baba|papa|beta|beti|"
    r"ke|ki|ka|ko|se|me|mein|par|pe|wala|wali|aur|ya|"
    r"thoda|bahut|jyada|kam|achcha|achchi|bura|buri)\b",
    re.IGNORECASE)

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")


def _detect_language(text: str) -> Tuple[Optional[str], float]:
    """Smart language classifier. Returns (label, confidence) or (None,0).
    Rules:
      • Devanagari script present  → "hindi"  (0.92)
      • Latin script + Hindi tokens → "hinglish" (0.88)
      • Latin script only, no Hindi tokens, len>=15 → "english" (0.85)
      • Otherwise unknown → (None, 0.0)
    """
    if not text:
        return (None, 0.0)
    if _DEVANAGARI.search(text):
        return ("hindi", 0.92)
    has_hi = bool(_HI_ROMAN_TOKENS.search(text))
    has_latin = bool(re.search(r"[a-zA-Z]", text))
    if has_hi and has_latin:
        return ("hinglish", 0.88)
    if has_latin and not has_hi and len(text.strip()) >= 15:
        return ("english", 0.85)
    return (None, 0.0)


def extract_facts_from_text(text: str) -> List[Tuple[str, str, float]]:
    """Run all _FACT_RULES against text. Return list of (key, value, conf)
    deduplicated to keep only the HIGHEST-confidence value per key.
    Pure function — no DB I/O. Safe to test independently.
    """
    if not isinstance(text, str) or not text.strip():
        return []
    text_lc = text.lower()
    best: Dict[str, Tuple[str, float]] = {}
    for key, value, conf, pattern in _FACT_RULES:
        if _matches(text_lc, pattern):
            cur = best.get(key)
            if cur is None or conf > cur[1]:
                best[key] = (value, conf)
    # Smart language detection (replaces the broken Latin-charset regex)
    lang, lang_conf = _detect_language(text)
    if lang:
        cur = best.get("language_pref")
        if cur is None or lang_conf > cur[1]:
            best["language_pref"] = (lang, lang_conf)
    return [(k, v, c) for k, (v, c) in best.items()]


# ─────────────────────────────────────────────────────────────────────────────
# L1 — Persistence (insert-or-update with confidence merge)
# ─────────────────────────────────────────────────────────────────────────────

def upsert_fact(user_id: int, fact_key: str, fact_value: str,
                 confidence: float = 0.5,
                 source_type: str = "regex",
                 source_ref: Optional[str] = None) -> bool:
    """Insert or update a single fact. Confidence-merge rule:
       • If new conf >  existing conf  → overwrite value/conf/source
       • If new conf == existing conf AND value identical → refresh ts
       • If new conf == existing conf AND value differs   → keep existing
                                                            (deterministic
                                                            tie-breaker:
                                                            first-seen wins
                                                            to prevent
                                                            oscillation)
       • If new conf <  existing conf  → keep existing, only refresh
                                          updated_at
       Race-safe: on UNIQUE-constraint conflict (concurrent insert), retries
       once as an update. Returns True if a row was created/updated.
    """
    if not user_id or not fact_key or fact_value is None:
        return False
    fact_value = str(fact_value)[:_MAX_FACT_VALUE_LEN]
    for attempt in (1, 2):
        try:
            existing = (UserFact.query
                        .filter_by(user_id=user_id, fact_key=fact_key)
                        .first())
            if existing is None:
                row = UserFact(
                    user_id=user_id, fact_key=fact_key,
                    fact_value=fact_value,
                    confidence=float(confidence),
                    source_type=source_type, source_ref=source_ref,
                )
                db.session.add(row)
            else:
                if confidence > existing.confidence:
                    existing.fact_value = fact_value
                    existing.confidence = float(confidence)
                    existing.source_type = source_type
                    existing.source_ref = source_ref
                elif (confidence == existing.confidence and
                       existing.fact_value == fact_value):
                    # same evidence again — just refresh timestamp
                    pass
                # else: tie with different value → keep existing (no drift)
                existing.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            if attempt == 1:
                # Likely a race on UNIQUE(user_id, fact_key) — the other
                # writer won; retry as an update path.
                continue
            return False
    return False


def extract_and_store_facts(user_id: int, question_text: str,
                              source_ref: Optional[str] = None) -> int:
    """Extract facts from a question and persist all hits. Returns the
    number of facts upserted. Fire-and-forget — never raises.
    """
    if not user_id or not isinstance(question_text, str):
        return 0
    try:
        hits = extract_facts_from_text(question_text)
        n = 0
        for key, value, conf in hits:
            if upsert_fact(user_id, key, value, confidence=conf,
                            source_type="regex", source_ref=source_ref):
                n += 1
        return n
    except Exception:
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# L2 / L3 — Read helpers (aggregator/scorer for these will land in P4/P5)
# ─────────────────────────────────────────────────────────────────────────────

def get_facts(user_id: int,
               min_confidence: float = 0.0) -> Dict[str, Dict[str, Any]]:
    """Return all stored facts for a user as {key: {value, confidence,
    source_type, updated_at}}. Filter by minimum confidence.
    """
    if not user_id:
        return {}
    try:
        rows = (UserFact.query
                .filter(UserFact.user_id == user_id,
                        UserFact.confidence >= min_confidence)
                .all())
        return {
            r.fact_key: {
                "value":      r.fact_value,
                "confidence": round(float(r.confidence), 3),
                "source":     r.source_type,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        }
    except Exception:
        return {}


def get_behavior(user_id: int) -> Optional[Dict[str, Any]]:
    """Return the L2 behavior row as a dict, or None if not yet computed."""
    if not user_id:
        return None
    try:
        row = UserBehavior.query.filter_by(user_id=user_id).first()
        if row is None:
            return None
        return {
            "total_questions":    row.total_questions,
            "topic_distribution": row.topic_distribution,
            "avg_question_len":   row.avg_question_len,
            "pref_time_band":     row.pref_time_band,
            "followup_rate":      row.followup_rate,
            "language_pref":      row.language_pref,
            "obsession_topic":    row.obsession_topic,
            "obsession_count":    row.obsession_count,
            "last_active_at":     (row.last_active_at.isoformat()
                                    if row.last_active_at else None),
        }
    except Exception:
        return None


def get_personality(user_id: int) -> Optional[Dict[str, float]]:
    """Return the L3 personality vector as a dict, or None if not yet
    scored."""
    if not user_id:
        return None
    try:
        row = UserPersonality.query.filter_by(user_id=user_id).first()
        if row is None:
            return None
        return {
            "analytical":      row.analytical,
            "anxious":         row.anxious,
            "self_focus":      row.self_focus,
            "formal":          row.formal,
            "brief":           row.brief,
            "action_oriented": row.action_oriented,
            "skeptical":       row.skeptical,
            "future_focused":  row.future_focused,
            "sample_size":     row.sample_size,
        }
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Bundle assembly + silent injection
# ─────────────────────────────────────────────────────────────────────────────

def load_bundle(user_id: int,
                  current_question: Optional[str] = None) -> Dict[str, Any]:
    """Build the silent enrichment bundle for an Ask-flow request.

    Returned dict:
      {
        "knows":        {fact_key: {value, confidence, ...}},
        "behaves_like": {...} | None,
        "thinks_like":  {...} | None,
        "right_now":    {time_of_day, day_of_week, ...},
        "mood_now":     "neutral|anxious|distressed|hopeful|frustrated",
      }
    """
    facts = get_facts(user_id, min_confidence=0.5)
    behavior = get_behavior(user_id)
    personality = get_personality(user_id)
    realtime = _build_realtime_context()
    mood_now = _detect_current_mood(current_question or "")
    return {
        "knows":        facts,
        "behaves_like": behavior,
        "thinks_like":  personality,
        "right_now":    realtime,
        "mood_now":     mood_now,
    }


def _build_realtime_context() -> Dict[str, Any]:
    """Stream B — real-time context. Pure deterministic; weather/tithi
    integration lands in P6."""
    now = datetime.utcnow()
    # India is UTC+5:30 (no DST), most users are India-resident
    hour_ist = (now.hour + 5) % 24  # rough; minute offset omitted on purpose
    if 5 <= hour_ist < 12:
        band = "morning"
    elif 12 <= hour_ist < 17:
        band = "afternoon"
    elif 17 <= hour_ist < 22:
        band = "evening"
    else:
        band = "late_night"
    return {
        "time_of_day":  band,
        "day_of_week":  now.strftime("%A").lower(),
        "iso_utc":      now.isoformat(timespec="seconds"),
    }


_MOOD_CUES = (
    ("distressed", re.compile(
        r"\b(please\s+bata|bhagwan\s+ke\s+liye|bahut\s+pareshan|"
        r"kuch\s+samajh\s+nahi|help\s+me|madad\s+karo)\b", re.I)),
    ("anxious",    re.compile(
        r"\b(dar(\s+lagta)?|chinta|tension|fikr|worry|scared|"
        r"kya\s+hoga)\b", re.I)),
    ("frustrated", re.compile(
        r"\b(kuch\s+nahi\s+ho\s+raha|fed\s+up|tang\s+aa\s+gay[ae]|"
        r"frustrate)\b", re.I)),
    ("hopeful",    re.compile(
        r"\b(positive|umeed|achchi\s+khabar|good\s+news|"
        r"khushi)\b", re.I)),
)


def _detect_current_mood(text: str) -> str:
    """Stream C — mood from the CURRENT question text. Returns one of
    distressed / anxious / frustrated / hopeful / neutral.
    """
    if not isinstance(text, str) or not text.strip():
        return "neutral"
    for label, rx in _MOOD_CUES:
        if rx.search(text):
            return label
    return "neutral"


def inject_into_prompt(bundle: Dict[str, Any], base_prompt: str) -> str:
    """Prepend a SILENT context block to base_prompt. The block is wrapped
    in clear DO-NOT-RECITE instructions so the LLM treats it as private
    routing context. NEVER mention the bundle in user-facing output.
    """
    if not isinstance(bundle, dict) or not base_prompt:
        return base_prompt or ""
    knows = bundle.get("knows") or {}
    fact_lines = []
    for k, info in knows.items():
        if isinstance(info, dict):
            fact_lines.append(f"  • {k} = {info.get('value')} "
                               f"(conf={info.get('confidence')})")
    fact_block = "\n".join(fact_lines) if fact_lines else "  (none yet)"

    behavior = bundle.get("behaves_like") or {}
    personality = bundle.get("thinks_like") or {}
    realtime = bundle.get("right_now") or {}
    mood_now = bundle.get("mood_now", "neutral")

    silent_block = (
        "═══════════════════════════════════════════════════════════════\n"
        "SILENT USER CONTEXT (engine-injected — DO NOT RECITE TO USER)\n"
        "Use only to shape tone, framing, length, and angle. NEVER say\n"
        "phrases like 'aapne pichli baar', 'I remember you mentioned',\n"
        "or any statement that exposes that this context exists.\n"
        "───────────────────────────────────────────────────────────────\n"
        f"KNOWN FACTS:\n{fact_block}\n"
        f"BEHAVIOR: {behavior or '(not yet computed)'}\n"
        f"PERSONALITY: {personality or '(not yet computed)'}\n"
        f"REALTIME: {realtime}\n"
        f"MOOD_NOW: {mood_now}\n"
        "═══════════════════════════════════════════════════════════════\n"
    )
    return silent_block + "\n" + base_prompt

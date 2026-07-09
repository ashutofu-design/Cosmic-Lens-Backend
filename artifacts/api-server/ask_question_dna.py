"""Question DNA — Step 1 understanding layer (classification ONLY, no astrology).

The LLM here is NOT an astrologer and NEVER answers. It converts one user
message (possibly multi-question, Hinglish/Hindi/English, with typos and
pronouns) into structured metadata: domain, bucket, intent, subject, target,
question_type, timing, tense, emotion, risk, confidence.

Design contract (per product spec):
  1. Master taxonomy is FIXED in code — engines are the source of truth for
     non-relationship domains. The love/relationship domain uses a dedicated
     question-theme taxonomy (`relationship_dna_taxonomy`) separate from MR
     engine archetype ids. Prompt does NOT enumerate love buckets — few-shots
     teach the vocabulary; validation enforces the fixed set.
  2. LLM output is STRICT JSON, validated + coerced by `validate_question_dna`.
     Anything outside the taxonomy is normalized to a safe default and the
     confidence is lowered — the LLM can never inject new labels downstream.
  3. `required_modules` is NOT decided by the LLM. It is derived
     deterministically by `derive_required_modules` from
     (domain, bucket, timing, tense) — chart-module policy lives in code.
  4. Follow-ups / pronouns resolve against `history` passed into the prompt
     (last few turns), e.g. "Exact month?" after "Shaadi kab hogi?" stays
     marriage timing; "Uska nature?" resolves "uska" from prior turns.
  5. On ANY failure the extractor returns a valid low-confidence fallback —
     it never raises, so callers can shadow-run it without behaviour change.

Env gates:
  ASK_QUESTION_DNA=1        enable extraction (default ON; callers decide use)
  ASK_QUESTION_DNA_MODEL    override model (default RAW_PASSTHROUGH_MODEL/gpt-4.1-mini)
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# MASTER TAXONOMY
# Bucket ids intentionally reuse engine archetype ids from ask_intent_llm so
# DNA → engine dispatch needs no translation table.
# ─────────────────────────────────────────────────────────────────────────────

from ask_intent_llm import (  # noqa: E402  (engine archetypes for non-love domains)
    MR_ARCHETYPES,
    CAREER_ARCHETYPES,
    FINANCE_ARCHETYPES,
    HEALTH_ARCHETYPES,
    EDUCATION_ARCHETYPES,
    CHILDREN_ARCHETYPES,
    PROPERTY_ARCHETYPES,
    TRAVEL_ARCHETYPES,
    LITIGATION_ARCHETYPES,
)
from relationship_dna_taxonomy import (  # noqa: E402
    LOVE_RELATIONSHIP_BUCKETS,
    LOVE_BUCKET_UNKNOWN,
    LOVE_BUCKET_SOFT_DEFAULT,
    normalize_love_bucket,
    map_love_bucket_to_mr,
    derive_bucket_match,
    audit_log_low_bucket_match,
)

DNA_DOMAINS: tuple[str, ...] = (
    "marriage", "love", "career", "finance", "health", "education",
    "children", "property", "travel", "litigation", "vehicle",
    "spiritual", "general",
)

DNA_BUCKETS_BY_DOMAIN: dict[str, frozenset[str]] = {
    "marriage":   frozenset(MR_ARCHETYPES),
    "love":       LOVE_RELATIONSHIP_BUCKETS,
    "career":     frozenset(CAREER_ARCHETYPES),
    "finance":    frozenset(FINANCE_ARCHETYPES),
    "health":     frozenset(HEALTH_ARCHETYPES),
    "education":  frozenset(EDUCATION_ARCHETYPES),
    "children":   frozenset(CHILDREN_ARCHETYPES),
    "property":   frozenset(PROPERTY_ARCHETYPES),
    "travel":     frozenset(TRAVEL_ARCHETYPES),
    "litigation": frozenset(LITIGATION_ARCHETYPES),
    "vehicle":    frozenset({"vehicle_purchase", "vehicle_timing", "general_vehicle"}),
    "spiritual":  frozenset({"spiritual_growth", "moksha_path", "guru_yog", "general_spiritual"}),
    "general":    frozenset({"native_overview", "chart_fact", "general"}),
}

DNA_DEFAULT_BUCKET: dict[str, str] = {
    "marriage": "general_mr",
    "love": LOVE_BUCKET_SOFT_DEFAULT,
    "career": "general_career",
    "finance": "general_finance",
    "health": "general_health",
    "education": "general_education",
    "children": "general_children",
    "property": "general_property",
    "travel": "general_travel",
    "litigation": "general_litigation",
    "vehicle": "general_vehicle",
    "spiritual": "general_spiritual",
    "general": "general",
}

DNA_SUBJECTS: tuple[str, ...] = (
    "self", "partner", "spouse", "boyfriend", "girlfriend", "ex", "crush",
    "child", "parent", "sibling", "friend", "business_partner", "family",
    "couple", "other", "unknown",
)

# Whose life-outcome is being asked about (the analytical target), which can
# differ from `subject` (whose traits are described). "Boyfriend cheat karega?"
# → subject=boyfriend, target=self_relationship.
DNA_TARGETS: tuple[str, ...] = (
    "self", "self_relationship", "subject_person", "couple", "family", "unknown",
)

DNA_QUESTION_TYPES: tuple[str, ...] = (
    "prediction",     # kya hoga
    "timing",         # kab hoga
    "comparison",     # X ya Y
    "decision",       # karu ya nahi
    "cause",          # kyun ho raha hai
    "remedy",         # upay kya hai
    "verification",   # astrologer ne bola, sahi hai?
    "compatibility",  # hum compatible hain?
    "personality",    # partner kaisa hoga / nature
    "risk",           # divorce ka risk? cheating ka dar?
    "explanation",    # concept question (kp vs vedic)
    "chart_fact",     # mera lagna kya hai / Saturn kahan hai
    "current_state",  # abhi kya chal raha hai
    "general",
)

DNA_TENSES: tuple[str, ...] = ("past", "present", "future", "unspecified")

DNA_EMOTIONS: tuple[str, ...] = (
    "fear", "anxiety", "hope", "curiosity", "desperation",
    "grief", "anger", "conflicted", "skeptical", "neutral",
)

DNA_RISK_LEVELS: tuple[str, ...] = ("low", "medium", "high")

DNA_MODULES: tuple[str, ...] = (
    "D1", "D9", "D10", "D7", "DASHA", "TRANSIT", "KP", "ASHTAKAVARGA",
)


def question_dna_enabled() -> bool:
    return (os.environ.get("ASK_QUESTION_DNA") or "1").strip() != "0"


# ─────────────────────────────────────────────────────────────────────────────
# DETERMINISTIC MODULE ROUTER — the LLM never picks chart modules.
# ─────────────────────────────────────────────────────────────────────────────

_DOMAIN_BASE_MODULES: dict[str, tuple[str, ...]] = {
    "marriage":   ("D1", "D9"),
    "love":       ("D1", "D9"),
    "career":     ("D1", "D10"),
    "finance":    ("D1",),
    "health":     ("D1",),
    "education":  ("D1",),
    "children":   ("D1", "D7"),
    "property":   ("D1",),
    "travel":     ("D1",),
    "litigation": ("D1",),
    "vehicle":    ("D1",),
    "spiritual":  ("D1", "D9"),
    "general":    ("D1",),
}


def derive_required_modules(
    domain: str,
    bucket: str,
    *,
    timing: bool = False,
    tense: str = "unspecified",
) -> list[str]:
    """(domain, bucket, timing, tense) → chart modules. Policy lives HERE, not in the LLM.

    Rules:
      • D1 always; D9 for relationship/spiritual; D10 career; D7 children.
      • timing questions → DASHA + TRANSIT + KP (event confirmation).
      • present-tense state questions ("abhi chal raha hai?") → DASHA + TRANSIT
        even without a kab/when anchor — current activation needs the current
        MD/AD, a natal-only read is incomplete (e.g. "affair abhi chal raha?").
      • ASHTAKAVARGA for house-strength domains (career/property/finance timing).
    """
    mods: list[str] = list(_DOMAIN_BASE_MODULES.get(domain, ("D1",)))
    if timing:
        for m in ("DASHA", "TRANSIT", "KP"):
            if m not in mods:
                mods.append(m)
        if domain in ("career", "property", "finance", "travel"):
            mods.append("ASHTAKAVARGA")
    elif tense == "present":
        for m in ("DASHA", "TRANSIT"):
            if m not in mods:
                mods.append(m)
    return mods


# ─────────────────────────────────────────────────────────────────────────────
# JSON SCHEMA (fixed) — one message can carry multiple questions.
# ─────────────────────────────────────────────────────────────────────────────

QUESTION_DNA_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "normalized_question": {"type": "string"},
                    "domain":        {"type": "string", "enum": list(DNA_DOMAINS)},
                    "bucket":        {"type": "string"},
                    "intent":        {"type": "string"},
                    "subject":       {"type": "string", "enum": list(DNA_SUBJECTS)},
                    "target":        {"type": "string", "enum": list(DNA_TARGETS)},
                    "question_type": {"type": "string", "enum": list(DNA_QUESTION_TYPES)},
                    "timing":        {"type": "boolean"},
                    "tense":         {"type": "string", "enum": list(DNA_TENSES)},
                    "emotion":       {"type": "string", "enum": list(DNA_EMOTIONS)},
                    "risk":          {"type": "string", "enum": list(DNA_RISK_LEVELS)},
                    "is_followup":   {"type": "boolean"},
                    "followup_of":   {"type": "string"},
                    "confidence":    {"type": "number"},
                },
                "required": [
                    "normalized_question", "domain", "bucket", "intent",
                    "subject", "target", "question_type", "timing", "tense",
                    "emotion", "risk", "confidence",
                ],
            },
        },
    },
    "required": ["questions"],
}


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT — compact. Taxonomy + strict rules + few-shots. NOT a 1000-line essay.
# ─────────────────────────────────────────────────────────────────────────────

def _bucket_lines() -> str:
    """Non-love domains only — love buckets are NOT listed in the prompt."""
    rows = []
    for d in DNA_DOMAINS:
        if d == "love":
            continue
        ids = sorted(DNA_BUCKETS_BY_DOMAIN.get(d, frozenset()))
        rows.append(f"  {d}: {', '.join(ids)}")
    return "\n".join(rows)


_LOVE_BUCKET_PROMPT = """LOVE DOMAIN (domain=love) — bucket rules:
- Use question-theme bucket ids (snake_case), NOT engine jargon
  (never loyalty_trust, general_mr, secret_relationship, patchup, etc. for love).
- Pick the SINGLE most specific bucket — do NOT overuse relationship_future.
  Prefer: compatibility, commitment, communication, spiritual_karmic,
  relationship_decisions, relationship_promise, trust_loyalty, etc.
- relationship_future ONLY for vague long-term stability/outlook when no sharper
  bucket fits (long-term chalega, relationship strong rahega).
- Valid ids are taught via examples below — do not invent new bucket strings.
- If truly uncertain → relationship_future + lower confidence.
- Invented / no-fit bucket → unknown_relationship_intent (audit)."""


_FEW_SHOTS = """EXAMPLES (input → output JSON):

Q: "Kya mera boyfriend mujhe cheat karega?"
{"questions":[{"normalized_question":"Kya mera boyfriend mujhe cheat karega?","domain":"love","bucket":"trust_loyalty","intent":"cheating prediction for current boyfriend","subject":"boyfriend","target":"self_relationship","question_type":"risk","timing":false,"tense":"future","emotion":"fear","risk":"high","is_followup":false,"followup_of":"","confidence":0.97}]}

Q: "Meri shaadi kab hogi?"
{"questions":[{"normalized_question":"Meri shaadi kab hogi?","domain":"marriage","bucket":"general_mr","intent":"marriage timing for self","subject":"self","target":"self","question_type":"timing","timing":true,"tense":"future","emotion":"curiosity","risk":"low","is_followup":false,"followup_of":"","confidence":0.98}]}

History: user:"Meri shaadi kab hogi?" assistant:"2027 ka window..." — Q: "Exact month batao"
{"questions":[{"normalized_question":"Meri shaadi kis month me hogi?","domain":"marriage","bucket":"general_mr","intent":"refine marriage timing to exact month","subject":"self","target":"self","question_type":"timing","timing":true,"tense":"future","emotion":"curiosity","risk":"low","is_followup":true,"followup_of":"Meri shaadi kab hogi?","confidence":0.95}]}

History: user:"Kya mera partner loyal hai?" — Q: "Uska nature kaisa hai?"
{"questions":[{"normalized_question":"Mere partner ka nature kaisa hai?","domain":"love","bucket":"partner_nature","intent":"partner personality/nature","subject":"partner","target":"subject_person","question_type":"personality","timing":false,"tense":"present","emotion":"curiosity","risk":"low","is_followup":true,"followup_of":"Kya mera partner loyal hai?","confidence":0.93}]}

Q: "Government job kab milegi? Aur partner loyal hai?"
{"questions":[{"normalized_question":"Government job kab milegi?","domain":"career","bucket":"govt_job","intent":"government job timing","subject":"self","target":"self","question_type":"timing","timing":true,"tense":"future","emotion":"hope","risk":"low","is_followup":false,"followup_of":"","confidence":0.97},{"normalized_question":"Kya mera partner loyal hai?","domain":"love","bucket":"trust_loyalty","intent":"partner loyalty check","subject":"partner","target":"self_relationship","question_type":"risk","timing":false,"tense":"present","emotion":"anxiety","risk":"high","is_followup":false,"followup_of":"","confidence":0.96}]}

Q: "Kya partner ka affair abhi chal raha hai?"
{"questions":[{"normalized_question":"Kya mere partner ka affair abhi chal raha hai?","domain":"love","bucket":"third_person_infidelity","intent":"ongoing affair check right now","subject":"partner","target":"self_relationship","question_type":"current_state","timing":false,"tense":"present","emotion":"fear","risk":"high","is_followup":false,"followup_of":"","confidence":0.95}]}

Q: "Kya meri relationship ka promise future me strong rahega?"
{"questions":[{"normalized_question":"Kya meri relationship ka promise future me strong rahega?","domain":"love","bucket":"relationship_promise","intent":"relationship potential (promise/commitment) in future","subject":"self","target":"self","question_type":"prediction","timing":false,"tense":"future","emotion":"hope","risk":"low","is_followup":false,"followup_of":"","confidence":0.95}]}

Q: "Kya meri life me relationship ka yog hai?"
{"questions":[{"normalized_question":"Kya meri life me relationship ka yog hai?","domain":"love","bucket":"relationship_promise","intent":"relationship potential in life","subject":"self","target":"self","question_type":"prediction","timing":false,"tense":"future","emotion":"hope","risk":"low","is_followup":false,"followup_of":"","confidence":0.95}]}

Q: "Kya hamara relationship long-term chalega?"
{"questions":[{"normalized_question":"Kya hamara relationship long-term chalega?","domain":"love","bucket":"relationship_future","intent":"long-term relationship stability/outlook","subject":"couple","target":"self_relationship","question_type":"prediction","timing":false,"tense":"future","emotion":"hope","risk":"low","is_followup":false,"followup_of":"","confidence":0.94}]}

Q: "Kya hum compatible hain? Humara gun milan kaisa hai?"
{"questions":[{"normalized_question":"Kya hum compatible hain?","domain":"love","bucket":"compatibility","intent":"relationship compatibility / match","subject":"couple","target":"couple","question_type":"compatibility","timing":false,"tense":"present","emotion":"curiosity","risk":"low","is_followup":false,"followup_of":"","confidence":0.96}]}

Q: "Kya mujhe apne ex ko second chance dena chahiye?"
{"questions":[{"normalized_question":"Kya mujhe apne ex ko second chance dena chahiye?","domain":"love","bucket":"relationship_decisions","intent":"should I give ex a second chance (decision)","subject":"self","target":"self_relationship","question_type":"decision","timing":false,"tense":"present","emotion":"conflicted","risk":"medium","is_followup":false,"followup_of":"","confidence":0.95}]}

Q: "Kya partner sirf time pass kar raha hai?"
{"questions":[{"normalized_question":"Kya mera partner sirf time pass kar raha hai?","domain":"love","bucket":"commitment","intent":"partner seriousness / genuine commitment check","subject":"partner","target":"self_relationship","question_type":"risk","timing":false,"tense":"present","emotion":"anxiety","risk":"high","is_followup":false,"followup_of":"","confidence":0.94}]}

Q: "Hamari baat kyun nahi hoti? Communication problem hai kya?"
{"questions":[{"normalized_question":"Kya hamari relationship me communication problem hai?","domain":"love","bucket":"communication","intent":"communication gap / not talking enough","subject":"couple","target":"self_relationship","question_type":"cause","timing":false,"tense":"present","emotion":"anxiety","risk":"medium","is_followup":false,"followup_of":"","confidence":0.93}]}

Q: "Kya mera soulmate milega? Karmic connection hai kya?"
{"questions":[{"normalized_question":"Kya mera soulmate milega?","domain":"love","bucket":"spiritual_karmic","intent":"soulmate / karmic spiritual connection","subject":"self","target":"self","question_type":"prediction","timing":false,"tense":"future","emotion":"hope","risk":"low","is_followup":false,"followup_of":"","confidence":0.94}]}

Q: "Kya main is relationship me rahun ya chhod dun?"
{"questions":[{"normalized_question":"Kya main is relationship me rahun ya chhod dun?","domain":"love","bucket":"relationship_decisions","intent":"stay or leave relationship decision","subject":"self","target":"self_relationship","question_type":"decision","timing":false,"tense":"present","emotion":"conflicted","risk":"high","is_followup":false,"followup_of":"","confidence":0.96}]}

Q: "Kya ye relationship mere liye sahi hai?"
{"questions":[{"normalized_question":"Kya ye relationship mere liye sahi hai?","domain":"love","bucket":"compatibility","intent":"relationship suitability / right fit for me","subject":"self","target":"self_relationship","question_type":"decision","timing":false,"tense":"present","emotion":"conflicted","risk":"medium","is_followup":false,"followup_of":"","confidence":0.94}]}

Q: "Promotion milega?"
{"questions":[{"normalized_question":"Kya mujhe promotion milega?","domain":"career","bucket":"career_milestones","intent":"promotion prospect (not timing)","subject":"self","target":"self","question_type":"prediction","timing":false,"tense":"future","emotion":"hope","risk":"low","is_followup":false,"followup_of":"","confidence":0.94}]}"""


def build_question_dna_system_prompt(history_block: str = "") -> str:
    return f"""You are a QUESTION UNDERSTANDING layer for a Vedic astrology app.
You are NOT an astrologer. You are FORBIDDEN from answering, predicting, or
suggesting remedies. Your ONLY job: convert the user's message into structured
classification metadata (Question DNA). Output STRICT JSON only — no markdown,
no explanation, no extra keys.

RESPONSIBILITIES:
1. NORMALIZE — Hinglish/Hindi/English/typos/short-forms. Understand meaning,
   not exact words. Write normalized_question as a clean, self-contained question.
2. SPLIT — if the message contains multiple distinct questions, return one
   entry per question in "questions" (order preserved).
3. FOLLOW-UPS — use conversation history: a short refine ("exact month?",
   "aur detail?") belongs to the SAME topic as the prior question. Set
   is_followup=true and followup_of to the earlier question text.
4. PRONOUNS — resolve uska/wo/usne from history (partner? ex? friend?). If
   unresolvable, subject="unknown" and lower confidence.
5. NO GUESSING — uncertain → keep the safest default and LOW confidence.
   Never invent domains or buckets outside the taxonomy.

TAXONOMY (use ONLY these values):
domain: {", ".join(DNA_DOMAINS)}
{_LOVE_BUCKET_PROMPT}
bucket (non-love domains only):
{_bucket_lines()}
subject: {", ".join(DNA_SUBJECTS)}
target: {", ".join(DNA_TARGETS)}
question_type: {", ".join(DNA_QUESTION_TYPES)}
tense: past | present | future | unspecified
emotion: {", ".join(DNA_EMOTIONS)}
risk: low | medium | high  (emotional/brand sensitivity of answering this)

KEY RULES:
- timing=true ONLY for a real WHEN anchor (kab/when/kis saal/month/muhurat/date).
  "Kya hoga" prediction without WHEN → timing=false.
- "abhi / currently / chal raha hai" state questions → tense=present,
  question_type=current_state, timing=false.
- Partner/spouse as subject (their nature, loyalty, support) → domain love or
  marriage, even if career/money words appear.
- "Promotion milega?" → career (NOT finance). "Paisa kab aayega" → finance timing.
- "relationship ka yog hai / life me pyaar" → domain love, bucket relationship_promise,
  question_type=prediction, tense=future (NOT unspecified).
- LOVE bucket disambiguation (critical):
  • long-term chalega / stable rahega / aage chalega → relationship_future
    (NOT long_distance — long_distance ONLY for door rehkar / LDR / dur).
  • ex ko second chance / forgive / wapas aaun → relationship_decisions or
    reconciliation_ex (NOT second_marriage — that is remarriage after divorce).
  • time pass / serious nahi / commitment check → commitment (NOT dating_courtship).
  • compatible / gun milan / sahi hai mere liye → compatibility.
  • soulmate / karmic / past life bond → spiritual_karmic.
  • rahun ya chhod dun / karu ya nahi → relationship_decisions.
  • baat nahi hoti / communication / misunderstanding → communication
    (NOT emotional_bonding).
- intent: one short free-text phrase describing EXACTLY what the user wants.
- confidence: 0.0–1.0 for YOUR classification certainty.

{_FEW_SHOTS}
{history_block}"""


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION LAYER — LLM output cannot leak outside the taxonomy.
# ─────────────────────────────────────────────────────────────────────────────

_CONF_PENALTY = 0.15


def _coerce_enum(value: Any, allowed: tuple[str, ...] | frozenset, default: str) -> tuple[str, bool]:
    """Returns (coerced_value, ok). ok=False ONLY when the LLM invented a
    non-empty value outside the taxonomy — missing/empty fields take the
    default silently without a confidence penalty."""
    s = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    if s in allowed:
        return s, True
    if not s:
        return default, True
    return default, False


def _coerce_confidence(value: Any) -> float:
    try:
        c = float(value)
    except (TypeError, ValueError):
        return 0.3
    if c > 1.0:  # tolerate 0-100 style
        c = c / 100.0
    return max(0.0, min(1.0, c))


def validate_question_dna_item(raw: Any, original_question: str = "") -> dict:
    """Coerce one DNA item onto the master taxonomy. Never raises."""
    item = raw if isinstance(raw, dict) else {}
    coercions = 0

    domain, ok = _coerce_enum(item.get("domain"), DNA_DOMAINS, "general")
    coercions += 0 if ok else 1

    allowed_buckets = DNA_BUCKETS_BY_DOMAIN.get(domain, frozenset({"general"}))
    raw_bucket = str(item.get("bucket") or "").strip().lower().replace(" ", "_").replace("-", "_")
    bucket_coerced = False
    if domain == "love":
        normalized = normalize_love_bucket(raw_bucket)
        if normalized:
            bucket, ok = normalized, True
        elif not raw_bucket:
            bucket, ok = LOVE_BUCKET_UNKNOWN, True
            bucket_coerced = True
        else:
            bucket, ok = LOVE_BUCKET_UNKNOWN, False
            bucket_coerced = True
    else:
        bucket, ok = _coerce_enum(
            item.get("bucket"), allowed_buckets, DNA_DEFAULT_BUCKET.get(domain, "general"),
        )
        bucket_coerced = not ok and bool(raw_bucket)
    coercions += 0 if ok else 1

    subject, ok = _coerce_enum(item.get("subject"), DNA_SUBJECTS, "unknown")
    coercions += 0 if ok else 1

    target, ok = _coerce_enum(item.get("target"), DNA_TARGETS, "unknown")
    coercions += 0 if ok else 1

    qtype, ok = _coerce_enum(item.get("question_type"), DNA_QUESTION_TYPES, "general")
    coercions += 0 if ok else 1

    tense, ok = _coerce_enum(item.get("tense"), DNA_TENSES, "unspecified")
    coercions += 0 if ok else 1

    emotion, ok = _coerce_enum(item.get("emotion"), DNA_EMOTIONS, "neutral")
    coercions += 0 if ok else 1

    risk, ok = _coerce_enum(item.get("risk"), DNA_RISK_LEVELS, "medium")
    coercions += 0 if ok else 1

    timing = bool(item.get("timing"))
    # Consistency: question_type timing ⇄ timing flag.
    if qtype == "timing":
        timing = True
    elif timing and qtype in ("personality", "chart_fact", "explanation"):
        timing = False
    if qtype in ("prediction", "risk", "compatibility") and tense == "unspecified":
        tense = "future"

    confidence = _coerce_confidence(item.get("confidence"))
    if coercions:
        confidence = max(0.0, confidence - _CONF_PENALTY * coercions)

    nq = str(item.get("normalized_question") or "").strip() or (original_question or "").strip()

    engine_archetype = map_love_bucket_to_mr(bucket) if domain == "love" else None
    bucket_match_score, bucket_match_confidence = derive_bucket_match(
        confidence,
        domain=domain,
        bucket=bucket,
        bucket_coerced=bucket_coerced,
        coercions=coercions,
    )

    return {
        "normalized_question": nq,
        "domain": domain,
        "bucket": bucket,
        "engine_archetype": engine_archetype,
        "bucket_coerced": bucket_coerced,
        "bucket_match_score": bucket_match_score,
        "bucket_match_confidence": bucket_match_confidence,
        "intent": str(item.get("intent") or "").strip()[:200],
        "subject": subject,
        "target": target,
        "question_type": qtype,
        "timing": timing,
        "tense": tense,
        "emotion": emotion,
        "risk": risk,
        "is_followup": bool(item.get("is_followup")),
        "followup_of": str(item.get("followup_of") or "").strip()[:300],
        "confidence": round(confidence, 3),
        "required_modules": derive_required_modules(domain, bucket, timing=timing, tense=tense),
        "coercions": coercions,
    }


def _fallback_dna(question: str, reason: str) -> dict:
    item = validate_question_dna_item({}, original_question=question)
    item["confidence"] = 0.0
    return {
        "questions": [item],
        "source": f"dna_fallback:{reason}",
        "latency_ms": 0,
    }


def validate_question_dna(raw: Any, original_question: str = "") -> dict:
    """Validate/coerce the full LLM payload. Never raises."""
    payload = raw if isinstance(raw, dict) else {}
    items = payload.get("questions")
    if not isinstance(items, list) or not items:
        return _fallback_dna(original_question, "empty_questions")
    out = [validate_question_dna_item(it, original_question=original_question) for it in items[:6]]
    for it in out:
        audit_log_low_bucket_match(it.get("normalized_question") or original_question, it)
    return {"questions": out, "source": "llm", "latency_ms": 0}


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACTION — single LLM call, strict JSON, deterministic, never raises.
# ─────────────────────────────────────────────────────────────────────────────

_JSON_BLOB_RX = re.compile(r"\{.*\}", re.S)


def _history_block(history: Any, max_turns: int = 6) -> str:
    if not isinstance(history, (list, tuple)) or not history:
        return ""
    lines: list[str] = []
    for h in list(history)[-max_turns:]:
        if not isinstance(h, dict):
            continue
        role = str(h.get("role") or "").strip().lower()
        text = str(h.get("content") or h.get("text") or "").strip()
        if role in ("user", "assistant") and text:
            lines.append(f"{role}: {text[:280]}")
    if not lines:
        return ""
    return "\nCONVERSATION HISTORY (for follow-up/pronoun resolution):\n" + "\n".join(lines)


def extract_question_dna(
    question: str,
    *,
    history: Any = None,
    client: Any = None,
) -> dict:
    """Question → validated DNA payload. Never raises; falls back low-confidence."""
    q = (question or "").strip()
    if not q:
        return _fallback_dna("", "empty_question")
    if not question_dna_enabled():
        return _fallback_dna(q, "disabled")

    if client is None:
        try:
            from openai_helper import _get_client
            client = _get_client()
        except Exception:
            client = None
    if client is None:
        return _fallback_dna(q, "no_client")

    model = (
        os.environ.get("ASK_QUESTION_DNA_MODEL")
        or os.environ.get("RAW_PASSTHROUGH_MODEL")
        or os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    )
    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            max_tokens=900,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": build_question_dna_system_prompt(_history_block(history))},
                {"role": "user", "content": q},
            ],
            timeout=8,
        )
        text = (resp.choices[0].message.content or "").strip()
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            m = _JSON_BLOB_RX.search(text)
            raw = json.loads(m.group(0)) if m else {}
        out = validate_question_dna(raw, original_question=q)
        out["latency_ms"] = int((time.time() - t0) * 1000)
        return out
    except Exception as exc:
        print(f"[question_dna] extraction failed: {exc}", flush=True)
        fb = _fallback_dna(q, "llm_error")
        fb["latency_ms"] = int((time.time() - t0) * 1000)
        return fb

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
    "spiritual", "luck", "network", "siblings", "parents", "enemies",
    "fame", "personality", "dreams", "anger", "remedy", "charity",
    "settlement", "vastu", "pets", "wellness", "general",
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
    "luck":       frozenset({"general_luck"}),
    "network":    frozenset({"general_network"}),
    "siblings":   frozenset({"general_siblings"}),
    "parents":    frozenset({"general_parents"}),
    "enemies":    frozenset({"general_enemies"}),
    "fame":       frozenset({"general_fame"}),
    "personality": frozenset({"general_personality"}),
    "dreams":     frozenset({"general_dreams"}),
    "anger":      frozenset({"general_anger"}),
    "remedy":     frozenset({"general_remedy"}),
    "charity":    frozenset({"general_charity"}),
    "settlement": frozenset({"general_settlement"}),
    "vastu":      frozenset({"general_vastu"}),
    "pets":       frozenset({"general_pets"}),
    "wellness":   frozenset({"general_wellness"}),
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
    "luck": "general_luck",
    "network": "general_network",
    "siblings": "general_siblings",
    "parents": "general_parents",
    "enemies": "general_enemies",
    "fame": "general_fame",
    "personality": "general_personality",
    "dreams": "general_dreams",
    "anger": "general_anger",
    "remedy": "general_remedy",
    "charity": "general_charity",
    "settlement": "general_settlement",
    "vastu": "general_vastu",
    "pets": "general_pets",
    "wellness": "general_wellness",
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

DNA_ANSWER_STYLES: frozenset[str] = frozenset({
    "short_2_3_lines",
    "short_paragraph",
    "detailed_explain",
})

DNA_ANSWER_STYLE_LABELS: dict[str, str] = {
    "short_2_3_lines": "Short (2-3 lines)",
    "short_paragraph": "Short paragraph (4-6 lines)",
    "detailed_explain": "Detailed explanation",
}

DNA_ANSWER_STYLE_HINTS: dict[str, str] = {
    "short_2_3_lines": "Exactly 2-3 short sentences; direct answer first; no extra sections.",
    "short_paragraph": "One short paragraph, 4-6 sentences; direct answer first.",
    "detailed_explain": "2-3 short paragraphs with explanation; stay on-topic.",
}

_HEALTH_OVERVIEW_Q_RX = re.compile(
    r"(?ix)(health ke bare|health ke baare|meri sehat|mere health|overall health)"
)
_SURGERY_Q_RX = re.compile(r"(?ix)(operation|surgery|shastra[\s-]?kriya)")
_OVERVIEW_PLAN_RX = re.compile(
    r"(?ix)(general overview|overall health|without specific prediction|key health indicator)"
)

DNA_MODULES: tuple[str, ...] = (
    "D1", "D2", "D4", "D6", "D7", "D9", "D10", "D11", "D20", "D24", "D30",
    "DASHA", "TRANSIT", "ASHTAKAVARGA", "BCP",
)


def question_dna_enabled() -> bool:
    return (os.environ.get("ASK_QUESTION_DNA") or "1").strip() != "0"


def question_dna_routing_enabled() -> bool:
    """When ON, validated DNA overrides legacy classify/route for engine dispatch."""
    if not question_dna_enabled():
        return False
    return (
        os.environ.get("ASK_DNA_ROUTING")
        or os.environ.get("ASK_QUESTION_DNA_ROUTING")
        or "1"
    ).strip() != "0"


_DOMAIN_ARCHETYPE_KEY: dict[str, str] = {
    "marriage": "mr_archetype",
    "love": "mr_archetype",
    "relationship": "mr_archetype",
    "career": "career_archetype",
    "finance": "finance_archetype",
    "health": "health_archetype",
    "education": "education_archetype",
    "children": "children_archetype",
    "property": "property_archetype",
    "travel": "travel_archetype",
    "litigation": "litigation_archetype",
}


def dna_primary_item(dna: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(dna, dict):
        return {}
    items = dna.get("questions")
    if isinstance(items, list) and items and isinstance(items[0], dict):
        return items[0]
    return {}


def resolve_engine_archetype_from_dna_item(item: dict[str, Any]) -> str | None:
    domain = str(item.get("domain") or "").strip().lower()
    bucket = str(item.get("bucket") or "").strip().lower()
    if not domain or not bucket:
        return None
    if domain in ("love", "relationship"):
        arch = str(item.get("engine_archetype") or "").strip().lower()
        return arch or map_love_bucket_to_mr(bucket)
    if domain == "marriage":
        if bucket == "marriage_timing":
            return "general_mr"
        arch = str(item.get("engine_archetype") or "").strip().lower()
        return arch or bucket or None
    if domain in _DOMAIN_ARCHETYPE_KEY:
        return bucket
    return None


def dna_item_trusted_for_routing(
    item: dict[str, Any],
    *,
    dna_source: str = "",
    min_confidence: float = 0.55,
) -> bool:
    if not item:
        return False
    src = str(dna_source or "").strip().lower()
    if src.startswith("dna_fallback"):
        return False
    if int(item.get("coercions") or 0) > 2:
        return False
    domain = str(item.get("domain") or "").strip().lower()
    bucket = str(item.get("bucket") or "").strip().lower()
    if bucket in ("", "general", LOVE_BUCKET_UNKNOWN) and domain in ("", "general"):
        return False
    conf = float(item.get("confidence") or 0)
    bmc = str(item.get("bucket_match_confidence") or "").lower()
    if conf >= min_confidence:
        # Domain with a real engine is enough even if bucket is generic.
        if domain and domain not in ("", "general"):
            return True
        if bucket not in ("", "general", LOVE_BUCKET_UNKNOWN):
            return True
    if bmc == "high":
        return True
    if bmc == "medium" and conf >= 0.45:
        return True
    return False


def dna_routing_lock(
    llm_intent_admin: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """When trusted DNA routing applied, return static lock {is_timing, archetype, domain}."""
    if not isinstance(llm_intent_admin, dict) or not llm_intent_admin.get("dna_routing_applied"):
        return None
    item = dna_primary_item(llm_intent_admin.get("question_dna"))
    if not item:
        return None
    archetype = resolve_engine_archetype_from_dna_item(item)
    domain = str(item.get("domain") or llm_intent_admin.get("domain") or "").strip().lower()
    return {
        "is_timing": bool(item.get("timing")),
        "archetype": archetype,
        "domain": domain or "love",
        "bucket": str(item.get("bucket") or "").strip().lower(),
    }


def apply_question_dna_to_routing(
    question: str,
    admin: dict[str, Any],
    dna: dict[str, Any],
    *,
    llm_intent: dict[str, Any] | None = None,
    min_confidence: float = 0.55,
) -> bool:
    """Apply DNA bucket/domain/timing as routing source of truth when trusted."""
    admin["question_dna"] = dna
    if not question_dna_routing_enabled():
        return False

    item = dna_primary_item(dna)
    dna_source = str(dna.get("source") or "")
    if not dna_item_trusted_for_routing(
        item,
        dna_source=dna_source,
        min_confidence=min_confidence,
    ):
        return False

    domain = str(item.get("domain") or "").strip().lower()
    bucket = str(item.get("bucket") or "").strip().lower()
    timing = bool(item.get("timing"))
    archetype = resolve_engine_archetype_from_dna_item(item)
    prev_arch = str(
        admin.get("mr_archetype") or admin.get("routed_archetype") or ""
    ).strip().lower()

    # Follow-up domain re-check: a follow-up may switch domain (e.g. previous
    # thread was relationship, new question is wealth). Purge archetypes that
    # belong to OTHER domains so the engine resolver can't reuse the previous
    # turn's engine — DNA domain is the single source of truth here.
    _own_arch_key = _DOMAIN_ARCHETYPE_KEY.get(domain)
    _stale_keys = [
        k for k in set(_DOMAIN_ARCHETYPE_KEY.values())
        if k != _own_arch_key and admin.get(k)
    ]
    if _stale_keys:
        for k in _stale_keys:
            admin.pop(k, None)
            if isinstance(llm_intent, dict):
                llm_intent.pop(k, None)
        if admin.get("routed_archetype"):
            admin["routed_archetype"] = None
        # Re-set below when the new domain resolves an archetype.
        admin.pop("dna_engine_archetype", None)
        print(
            f"[question_dna] FOLLOWUP_DOMAIN_SWITCH purge={_stale_keys} "
            f"new_domain={domain} q={(question or '')[:72]!r}",
            flush=True,
        )

    admin["domain"] = domain
    admin["routed_domain"] = domain
    admin["bucket"] = bucket
    admin["mr_bucket"] = bucket
    if item.get("intent"):
        admin["intent"] = item.get("intent")
    for key in ("subject", "target", "emotion", "risk"):
        if item.get(key):
            admin[key] = item.get(key)
    if item.get("question_type"):
        admin["question_type_dna"] = item.get("question_type")
    admin["is_timing"] = timing
    admin["routed_timing"] = timing
    admin["dna_confidence"] = item.get("confidence")
    admin["dna_bucket_match"] = item.get("bucket_match_confidence")
    if item.get("required_modules"):
        admin["required_modules"] = item.get("required_modules")

    if archetype:
        admin["dna_engine_archetype"] = archetype
        arch_key = _DOMAIN_ARCHETYPE_KEY.get(domain)
        if arch_key:
            admin[arch_key] = archetype
        if domain in ("love", "marriage", "relationship"):
            admin["mr_archetype"] = archetype
        admin["routed_archetype"] = archetype

    admin["routing_override"] = "question_dna"
    admin["dna_routing_applied"] = True
    admin["intent_source"] = "question_dna"

    if isinstance(llm_intent, dict):
        llm_intent["domain"] = domain
        llm_intent["is_timing"] = timing
        llm_intent["bucket"] = bucket
        if archetype:
            arch_key = _DOMAIN_ARCHETYPE_KEY.get(domain)
            if arch_key:
                llm_intent[arch_key] = archetype
            if domain in ("love", "marriage", "relationship"):
                llm_intent["mr_archetype"] = archetype
        llm_intent["source"] = "question_dna"
        llm_intent["routing_override"] = "question_dna"

    if prev_arch and archetype and prev_arch != archetype:
        print(
            f"[question_dna] ROUTING_OVERRIDE q={(question or '')[:72]!r} "
            f"prev={prev_arch} dna={archetype} domain={domain} "
            f"bucket={bucket} conf={item.get('confidence')}",
            flush=True,
        )
    return True


# ─────────────────────────────────────────────────────────────────────────────
# DETERMINISTIC MODULE ROUTER — the LLM never picks chart modules.
# ─────────────────────────────────────────────────────────────────────────────

_DOMAIN_BASE_MODULES: dict[str, tuple[str, ...]] = {
    "marriage":   ("D1", "D9"),
    "love":       ("D1", "D9"),
    "career":     ("D1", "D9", "D10"),
    "finance":    ("D1", "D9", "D2"),
    "health":     ("D1", "D9", "D30"),
    "education":  ("D1", "D9", "D24"),
    "children":   ("D1", "D9", "D7"),
    "property":   ("D1", "D9", "D4"),
    "travel":     ("D1", "D9"),
    "litigation": ("D1", "D9", "D6"),
    "vehicle":    ("D1", "D9", "D4"),
    "spiritual":  ("D1", "D9", "D20"),
    "luck":       ("D1", "D9"),
    "network":    ("D1", "D9", "D11"),
    "siblings":   ("D1", "D9"),
    "parents":    ("D1", "D9"),
    "enemies":    ("D1", "D9"),
    "fame":       ("D1", "D9", "D10"),
    "personality": ("D1", "D9"),
    "dreams":     ("D1", "D9"),
    "anger":      ("D1", "D9"),
    "remedy":     ("D1", "D9"),
    "charity":    ("D1", "D9"),
    "settlement": ("D1", "D9", "D4"),
    "vastu":      ("D1", "D9", "D4"),
    "pets":       ("D1", "D9"),
    "wellness":   ("D1", "D9", "D30"),
    "general":    ("D1", "D9"),
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
      • D1 always; D9 verifies chart strength; the domain varga is also required
        (D10 career, D7 children, D2 finance, D4 property, etc.).
      • timing questions → DASHA + TRANSIT. AD/PD are the primary dasha triggers;
        MD is background context only.
      • BCP is allowed only for marriage and children/baby questions.
      • present-tense state questions ("abhi chal raha hai?") → DASHA + TRANSIT
        even without a kab/when anchor — current activation needs the current
        MD/AD, a natal-only read is incomplete (e.g. "affair abhi chal raha?").
      • ASHTAKAVARGA for house-strength domains (career/property/finance timing).
    """
    mods: list[str] = list(_DOMAIN_BASE_MODULES.get(domain, ("D1",)))
    if timing:
        for m in ("DASHA", "TRANSIT"):
            if m not in mods:
                mods.append(m)
        if domain in ("marriage", "children"):
            mods.append("BCP")
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
                    "user_wants":    {"type": "string"},
                    "understanding_confidence": {"type": "number"},
                    "answer_style":  {
                        "type": "string",
                        "enum": list(DNA_ANSWER_STYLES),
                    },
                    "answer_approach": {"type": "string"},
                },
                "required": [
                    "normalized_question", "domain", "bucket", "intent",
                    "subject", "target", "question_type", "timing", "tense",
                    "emotion", "risk", "confidence",
                    "user_wants", "answer_style", "answer_approach",
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
- Apply ROUTING PRIORITY RULES below BEFORE choosing any bucket.
- relationship_challenges = LAST FALLBACK only — never for specialist intents.
- relationship_future ONLY for vague long-term stability/outlook when no sharper bucket fits.
- Valid ids taught via examples — do not invent new bucket strings.
- If truly uncertain → relationship_future + lower confidence.
- Invented / no-fit bucket → unknown_relationship_intent (audit)."""


_ROUTING_PRIORITY_RULES = """ROUTING PRIORITY RULES (HIGHEST PRIORITY — override generic classification):

1. MOST SPECIFIC bucket wins. Specific > generic. Never pick relationship_challenges
   or relationship_future when a specialist bucket clearly fits.

2. relationship_challenges is LAST FALLBACK for love — only when NO specialist bucket
   fits. NEVER use it for: communication, trust_loyalty, commitment, compatibility,
   partner_nature, third_person_infidelity, breakup_separation, reconciliation_ex,
   family_social_acceptance, toxicity_red_flags, jealousy (use toxicity_red_flags),
   relationship_decisions, spiritual_karmic, long_distance, dating_courtship,
   physical_intimacy, emotional_bonding, love_feelings, marriage_potential.

3. EX / reconciliation HIGHEST PRIORITY — ex, ex-boyfriend/girlfriend, former partner,
   patch-up, reconciliation, second chance, come back, wapas aayega → reconciliation_ex
   (NOT relationship_decisions, NOT relationship_challenges) unless NOT about ex return.

4. THIRD PERSON > trust — another girl/boy, someone else, affair, cheating, flirting,
   dating someone else, emotional affair, hidden/secret relationship → third_person_infidelity
   (NOT relationship_challenges; NOT trust_loyalty unless ONLY loyalty/trust with no
   third-person angle).

5. COMMUNICATION > challenges — silent treatment, stonewalling, not listening,
   miscommunication, arguments, poor communication, baat nahi hoti → communication.

6. PARTNER NATURE > challenges — emotionally unavailable, narcissistic, immature,
   manipulative, possessive, controlling personality, anger issues, cold, avoidant →
   partner_nature.

7. ABUSE / TOXIC — gaslighting, physical/emotional/financial/verbal abuse, blackmail,
   coercion, control, threats, isolation, love bombing, trauma bond, toxic cycle →
   toxicity_red_flags (NOT relationship_challenges).

8. BREAKUP priority — breakup hoga, breakup kyun, cause of breakup, divorce risk,
   alag ho jayenge → breakup_separation (NOT relationship_challenges).

9. VERIFICATION — overthinking?, doubt sahi hai?, misunderstanding?, suspicion true?,
   reality or imagination? → question_type=verification (bucket = best-fit theme).

10. DECISION — should I stay/leave/forgive/trust/continue/marry (current relationship)?
    → relationship_decisions. Exception: ex/reconciliation → rule 3 (reconciliation_ex).

11. FAMILY — parents, in-laws, family approval, society, caste, religion, acceptance →
    family_social_acceptance. domain=love (current relationship) or marriage (shaadi
    context) — pick one consistently from question context; never general.

12. SUBJECT — boyfriend, girlfriend, wife, husband, fiance, partner, crush, lover, ex,
    parents, friend, family must map to subject. subject=unknown ONLY if truly unidentifiable.

13. TARGET consistency — relationship health/outlook → self_relationship; partner
    traits/behavior → subject_person + subject=partner; family approval → family target
    when asking about family side.

14. TENSE — "is cheating/lying/hiding/ignoring" (abhi) → present; "will cheat/leave/marry"
    → future; "why happened / why broke up" → past. Never mark clear present state as future.

15. CONFIDENCE — 0.95–0.99 clear intent; 0.85–0.94 minor ambiguity; 0.70–0.84 multiple
    buckets possible; below 0.70 only if genuinely unclear. Do NOT lower confidence just
    because question is long.

16. MULTI-INTENT — split independent questions (e.g. "cheating?" + "should I leave?" →
    two entries, different buckets).

17. FINAL TEST — "Which ONE specialist engine would a human astrologer open first?"
    That determines the bucket. Never generic when specialist exists."""


_FEW_SHOTS = """EXAMPLES (input → output JSON):

Q: "Kya mera boyfriend kisi aur ke saath flirt kar raha hai?"
{"questions":[{"normalized_question":"Kya mera boyfriend kisi aur ke saath flirt kar raha hai?","domain":"love","bucket":"third_person_infidelity","intent":"partner flirting with someone else","subject":"boyfriend","target":"self_relationship","question_type":"current_state","timing":false,"tense":"present","emotion":"fear","risk":"high","is_followup":false,"followup_of":"","confidence":0.97,"user_wants":"User wants to know if her boyfriend is currently flirting with another person.","understanding_confidence":0.97,"answer_style":"short_2_3_lines","answer_approach":"Direct present-state read — say clearly whether flirting/third-person energy is active now, with 1-2 chart reasons; keep tone calm."}]}

Q: "Kya mera boyfriend mujhe cheat karega?"
{"questions":[{"normalized_question":"Kya mera boyfriend mujhe cheat karega?","domain":"love","bucket":"third_person_infidelity","intent":"cheating prediction for current boyfriend","subject":"boyfriend","target":"self_relationship","question_type":"risk","timing":false,"tense":"future","emotion":"fear","risk":"high","is_followup":false,"followup_of":"","confidence":0.97,"user_wants":"User wants to know if her boyfriend will cheat on her in the future.","understanding_confidence":0.97,"answer_style":"short_paragraph","answer_approach":"Cautious risk read — likelihood of cheating with supporting factors; avoid absolute yes/no unless chart is very clear."}]}

Q: "Meri shaadi kab hogi?"
{"questions":[{"normalized_question":"Meri shaadi kab hogi?","domain":"marriage","bucket":"marriage_timing","intent":"marriage timing for self","subject":"self","target":"self","question_type":"timing","timing":true,"tense":"future","emotion":"curiosity","risk":"low","is_followup":false,"followup_of":"","confidence":0.98,"user_wants":"User wants to know when she will get married.","understanding_confidence":0.98,"answer_style":"short_paragraph","answer_approach":"Lead with marriage timing window (year/month range from dasha/transit), then 1-2 supporting chart factors."}]}

History: user:"Meri shaadi kab hogi?" assistant:"2027 ka window..." — Q: "Exact month batao"
{"questions":[{"normalized_question":"Meri shaadi kis month me hogi?","domain":"marriage","bucket":"marriage_timing","intent":"refine marriage timing to exact month","subject":"self","target":"self","question_type":"timing","timing":true,"tense":"future","emotion":"curiosity","risk":"low","is_followup":true,"followup_of":"Meri shaadi kab hogi?","confidence":0.95}]}

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
{"questions":[{"normalized_question":"Kya mujhe apne ex ko second chance dena chahiye?","domain":"love","bucket":"reconciliation_ex","intent":"should I give ex a second chance / reconciliation","subject":"ex","target":"self_relationship","question_type":"decision","timing":false,"tense":"present","emotion":"conflicted","risk":"medium","is_followup":false,"followup_of":"","confidence":0.95}]}

Q: "Kya partner sirf time pass kar raha hai?"
{"questions":[{"normalized_question":"Kya mera partner sirf time pass kar raha hai?","domain":"love","bucket":"commitment","intent":"partner seriousness / genuine commitment check","subject":"partner","target":"self_relationship","question_type":"risk","timing":false,"tense":"present","emotion":"anxiety","risk":"high","is_followup":false,"followup_of":"","confidence":0.94}]}

Q: "Hamari baat kyun nahi hoti? Communication problem hai kya?"
{"questions":[{"normalized_question":"Kya hamari relationship me communication problem hai?","domain":"love","bucket":"communication","intent":"communication gap / not talking enough","subject":"couple","target":"self_relationship","question_type":"cause","timing":false,"tense":"present","emotion":"anxiety","risk":"medium","is_followup":false,"followup_of":"","confidence":0.93}]}

Q: "Kya mera soulmate milega? Karmic connection hai kya?"
{"questions":[{"normalized_question":"Kya mera soulmate milega?","domain":"love","bucket":"spiritual_karmic","intent":"soulmate / karmic spiritual connection","subject":"self","target":"self","question_type":"prediction","timing":false,"tense":"future","emotion":"hope","risk":"low","is_followup":false,"followup_of":"","confidence":0.94}]}

Q: "Kya main is relationship me rahun ya chhod dun?"
{"questions":[{"normalized_question":"Kya main is relationship me rahun ya chhod dun?","domain":"love","bucket":"relationship_decisions","intent":"stay or leave relationship decision","subject":"self","target":"self_relationship","question_type":"decision","timing":false,"tense":"present","emotion":"conflicted","risk":"high","is_followup":false,"followup_of":"","confidence":0.96}]}

Q: "Kya jealousy relationship me problem banegi?"
{"questions":[{"normalized_question":"Kya jealousy relationship me problem banegi?","domain":"love","bucket":"toxicity_red_flags","intent":"jealousy as relationship risk/problem","subject":"couple","target":"self_relationship","question_type":"risk","timing":false,"tense":"future","emotion":"anxiety","risk":"medium","is_followup":false,"followup_of":"","confidence":0.92}]}

Q: "Hamare relationship ki sabse badi weakness kya hai?"
{"questions":[{"normalized_question":"Hamare relationship ki sabse badi weakness kya hai?","domain":"love","bucket":"relationship_challenges","intent":"biggest weakness/problem in relationship","subject":"couple","target":"self_relationship","question_type":"cause","timing":false,"tense":"present","emotion":"curiosity","risk":"medium","is_followup":false,"followup_of":"","confidence":0.94}]}

Q: "Kya ye relationship meri growth ke liye achha hai?"
{"questions":[{"normalized_question":"Kya ye relationship meri growth ke liye achha hai?","domain":"love","bucket":"relationship_future","intent":"relationship impact on personal growth/outlook","subject":"self","target":"self_relationship","question_type":"prediction","timing":false,"tense":"future","emotion":"hope","risk":"low","is_followup":false,"followup_of":"","confidence":0.93}]}

Q: "Overall, kya ye relationship mere liye sahi hai?"
{"questions":[{"normalized_question":"Overall, kya ye relationship mere liye sahi hai?","domain":"love","bucket":"relationship_decisions","intent":"overall suitability — is this relationship right for me","subject":"self","target":"self_relationship","question_type":"decision","timing":false,"tense":"present","emotion":"conflicted","risk":"medium","is_followup":false,"followup_of":"","confidence":0.94}]}

Q: "Kya ye relationship mere liye sahi hai?"
{"questions":[{"normalized_question":"Kya ye relationship mere liye sahi hai?","domain":"love","bucket":"relationship_decisions","intent":"overall suitability — is this relationship right for me","subject":"self","target":"self_relationship","question_type":"decision","timing":false,"tense":"present","emotion":"conflicted","risk":"medium","is_followup":false,"followup_of":"","confidence":0.94}]}

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

{_ROUTING_PRIORITY_RULES}

KEY RULES:
- timing=true ONLY for a real WHEN anchor (kab/when/kis saal/month/muhurat/date).
  "Kya hoga" prediction without WHEN → timing=false.
- For every timing question, the execution plan must check suitable windows with
  Antardasha (AD) and Pratyantardasha (PD) as primary triggers; Mahadasha (MD)
  is broad background. BCP is permitted only for marriage and baby/children.
- Every personal engine answer uses D1 + D9 + the question-domain divisional
  chart (for example children D7, career D10, finance D2, property D4).
- "abhi / currently / chal raha hai" state questions → tense=present,
  question_type=current_state, timing=false.
- Partner/spouse as subject (their nature, loyalty, support) → domain love or
  marriage, even if career/money words appear.
- "Promotion milega?" → career (NOT finance). "Paisa kab aayega" → finance timing.
- "relationship ka yog hai / life me pyaar" → domain love, bucket relationship_promise,
  question_type=prediction, tense=future (NOT unspecified).
- Apply ROUTING PRIORITY RULES above before any generic bucket choice.
- intent: one short free-text phrase describing EXACTLY what the user wants.
- confidence: 0.0–1.0 for YOUR classification certainty.
- user_wants: 1–2 plain-language sentences — FULL decode of what the user wants to
  know (who/what/when/why). Not just the bucket label.
- understanding_confidence: 0.0–1.0 — how confidently you understood the question
  (may equal confidence when unambiguous; lower if typos/pronouns/multi-intent).
- answer_style: short_2_3_lines | short_paragraph | detailed_explain — how long the
  final answer should be (simple yes/no state → short_2_3_lines; timing/decision →
  short_paragraph; why/how/explain → detailed_explain).
- answer_approach: 1–2 sentences — HOW the answer LLM should respond (structure, tone,
  what to lead with). Do NOT predict the astrological answer itself.

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


def format_answer_style_display(style: str) -> str:
    s = str(style or "").strip().lower().replace(" ", "_").replace("-", "_")
    if not s:
        return "—"
    return DNA_ANSWER_STYLE_LABELS.get(s, s.replace("_", " ").title())


def format_understanding_confidence(value: Any) -> str:
    if value is None or value == "":
        return "—"
    conf = _coerce_confidence(value)
    pct = int(round(conf * 100))
    if conf >= 0.95:
        level = "Very high"
    elif conf >= 0.85:
        level = "High"
    elif conf >= 0.70:
        level = "Moderate"
    else:
        level = "Low"
    return f"{pct}% ({level} — question understood clearly)"


def build_question_dna_narrator_rules(
    llm_intent: dict[str, Any] | None,
    *,
    question: str = "",
    health_validator: bool = False,
) -> str:
    """Narrator extra_rules from Question DNA — answer_style + answer_approach every ask."""
    if not question_dna_enabled():
        return ""
    item = dna_primary_item(
        llm_intent.get("question_dna") if isinstance(llm_intent, dict) else None
    )
    if not item:
        return ""

    style = str(item.get("answer_style") or "").strip()
    plan = str(item.get("answer_approach") or "").strip()
    wants = str(item.get("user_wants") or "").strip()

    is_health_overview = bool(_HEALTH_OVERVIEW_Q_RX.search(question or ""))
    if health_validator or is_health_overview:
        try:
            from ask_health.answer_validator import should_apply_health_overview_contract

            is_health_overview = should_apply_health_overview_contract(question)
        except Exception:
            try:
                from ask_health.answer_validator import _is_general_health_overview_question

                is_health_overview = _is_general_health_overview_question(question)
            except Exception:
                pass
        if is_health_overview:
            plan = (
                "Provide a general overview of health aspects based on the chart, "
                "focusing on key health indicators without specific predictions or remedies."
            )
            style = style or "short_paragraph"
            wants = wants or "User wants a general overview of their health."

    if not (style or plan or wants):
        return ""

    if health_validator:
        header = (
            "=== QUESTION DNA (MUST follow every time — DNA Judge checks alignment; "
            "validator will reject mismatch) ==="
        )
    else:
        header = (
            "=== QUESTION DNA (MUST follow every time — overrides default length/style rules) ==="
        )
    lines: list[str] = [f"\n\n{header}"]
    if wants:
        lines.append(f"User wants: {wants}")
    if style:
        norm = style.strip().lower().replace(" ", "_").replace("-", "_")
        label = format_answer_style_display(norm)
        hint = DNA_ANSWER_STYLE_HINTS.get(norm, "")
        lines.append(f"Answer Style: {norm} ({label})")
        if hint:
            lines.append(f"Length lock: {hint}")
    if plan:
        lines.append(f"LLM Answer Plan: {plan}")
    if plan and _OVERVIEW_PLAN_RX.search(plan):
        lines.append(
            "GENERAL OVERVIEW MODE (strict): soft paragraph only — overall health foundation, "
            "stress/energy/digestion themes, healthy routine + sleep + exercise. "
            "NO vitality score /100, NO planet+ghar list, NO H1/H8 jargon, NO remedies. "
            "End with: long-term tendencies only, not medical diagnosis."
        )
    if _SURGERY_Q_RX.search(question or ""):
        lines.append(
            "SURGERY RISK MODE (strict): answer probability only, never certainty. "
            "No date/month/year/muhurat. Use HEALTH_ENGINE_EXECUTION_JSON for one natural "
            "chart proof if a risk tendency is mentioned. Always include doctor/surgeon "
            "clearance advice and say this is not medical diagnosis."
        )
    lines.append(
        "BINDING: Final answer MUST match Answer Style length AND follow LLM Answer Plan "
        "structure. Prefer a SHORT COMPLETE answer over a LONG CUT answer — never stop "
        "mid-sentence or mid-mantra; last character must be । or . or ?"
    )
    return "\n".join(lines) + "\n"


def _coerce_answer_style(
    value: Any,
    *,
    question_type: str,
    timing: bool,
    is_followup: bool,
) -> str:
    s = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    if s in DNA_ANSWER_STYLES:
        return s
    if question_type in ("explanation", "cause", "chart_fact"):
        return "detailed_explain"
    if question_type in ("decision", "compatibility", "verification") or timing:
        return "short_paragraph"
    if question_type in ("current_state", "risk", "prediction") and not timing:
        return "short_2_3_lines"
    if is_followup:
        return "short_2_3_lines"
    return "short_paragraph"


def _derive_user_wants(item: dict[str, Any], *, intent: str, normalized_question: str) -> str:
    raw = str(item.get("user_wants") or "").strip()[:400]
    if raw:
        return raw
    if intent:
        return f"User wants to know: {intent}"
    if normalized_question:
        return f"User wants to know: {normalized_question}"
    return "User question could not be fully decoded."


def _derive_answer_approach(
    item: dict[str, Any],
    *,
    domain: str,
    question_type: str,
    timing: bool,
    intent: str,
    risk: str,
) -> str:
    raw = str(item.get("answer_approach") or "").strip()[:400]
    if raw:
        return raw
    parts: list[str] = []
    if domain == "health":
        parts.append(
            "Use D1/D9 health chart JSON — plain language, supportive tone; "
            "no disease diagnosis or cure guarantees."
        )
    else:
        parts.append("Answer from chart evidence for the routed engine/archetype.")
    if timing:
        parts.append(
            "Lead with the most suitable AD/PD timing window; use MD only as broad "
            "background, then briefly confirm through transit and the relevant divisional chart."
        )
    elif question_type == "decision":
        parts.append("Balanced guidance — avoid absolute yes/no unless chart is very clear.")
    elif question_type == "current_state":
        parts.append("Direct present-state read — what is happening now.")
    elif question_type == "risk":
        parts.append("Acknowledge emotional sensitivity; cautious wording.")
    elif question_type in ("explanation", "cause"):
        parts.append("Explain why/how with 2–4 supporting chart factors.")
    else:
        parts.append(f"Focus on: {intent or 'user intent'}.")
    if risk == "high":
        parts.append("Keep tone gentle and non-alarmist.")
    return " ".join(parts)


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

    if domain == "marriage" and timing and bucket == "general_mr":
        bucket = "marriage_timing"

    confidence = _coerce_confidence(item.get("confidence"))
    if coercions:
        confidence = max(0.0, confidence - _CONF_PENALTY * coercions)

    nq = str(item.get("normalized_question") or "").strip() or (original_question or "").strip()
    intent = str(item.get("intent") or "").strip()[:200]
    is_followup = bool(item.get("is_followup"))

    if item.get("understanding_confidence") is not None:
        understanding_confidence = _coerce_confidence(item.get("understanding_confidence"))
    else:
        understanding_confidence = confidence
    if coercions:
        understanding_confidence = max(0.0, understanding_confidence - _CONF_PENALTY * coercions)

    user_wants = _derive_user_wants(item, intent=intent, normalized_question=nq)
    answer_style = _coerce_answer_style(
        item.get("answer_style"),
        question_type=qtype,
        timing=timing,
        is_followup=is_followup,
    )
    answer_approach = _derive_answer_approach(
        item,
        domain=domain,
        question_type=qtype,
        timing=timing,
        intent=intent,
        risk=risk,
    )

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
        "intent": intent,
        "subject": subject,
        "target": target,
        "question_type": qtype,
        "timing": timing,
        "tense": tense,
        "emotion": emotion,
        "risk": risk,
        "is_followup": is_followup,
        "followup_of": str(item.get("followup_of") or "").strip()[:300],
        "confidence": round(confidence, 3),
        "user_wants": user_wants,
        "understanding_confidence": round(understanding_confidence, 3),
        "answer_style": answer_style,
        "answer_approach": answer_approach,
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

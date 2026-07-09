"""Production relationship (love domain) bucket taxonomy for Question DNA.

Designed from real-world Hindi/English/Hinglish relationship question patterns —
user-intent themes, NOT engine archetype jargon (loyalty_trust, general_mr, etc.).

Marriage-domain spouse-chart reads (spouse_profession, manglik, …) stay on
MR_ARCHETYPES in ask_question_dna. This module is ONLY for domain=love.

Downstream engines still use MR archetypes; map via LOVE_BUCKET_TO_MR_ARCHETYPE.
"""
from __future__ import annotations

# ── 23 production buckets (22 themes + 1 audit bucket) ────────────────────────

LOVE_BUCKET_UNKNOWN = "unknown_relationship_intent"

LOVE_RELATIONSHIP_BUCKETS: frozenset[str] = frozenset({
    "relationship_promise",       # life me pyaar/yog, will I find love, promise
    "love_feelings",              # feelings depth, pyar reciprocity, emotional love
    "partner_nature",             # partner personality, behavior, temperament
    "compatibility",              # match/gun, hum compatible hain (non-timing)
    "commitment",                 # long-term intent, shaadi karega?, serious hai?
    "trust_loyalty",              # cheat, loyal, dhokha, betrayal, vishwas
    "communication",              # baat nahi, misunderstandings, silence
    "emotional_bonding",          # attachment, closeness, emotional connection
    "physical_intimacy",          # sexual/physical chemistry, intimacy issues
    "third_person_infidelity",    # affair, hidden/parallel, kisi aur se
    "dating_courtship",           # dating, crush, proposal, approach, flirting
    "long_distance",              # LDR, door rehkar
    "family_social_acceptance",   # parents/family/society approval, intercaste
    "relationship_challenges",    # general struggles, problems, rough patch
    "toxicity_red_flags",         # toxic, abuse, manipulation, red/green flags
    "breakup_separation",         # breakup, divorce risk, alag ho jayenge
    "reconciliation_ex",          # patchup, ex wapas, comeback, forgive
    "marriage_potential",         # is relationship → marriage? (NOT kab/when)
    "relationship_future",        # future outlook non-timing (intentional catch-all)
    "relationship_decisions",     # stay/leave, propose?, karu ya nahi
    "spiritual_karmic",           # soulmate, past life, karmic bond
    "relationship_remedies",      # upay/mantra for love/relationship
    LOVE_BUCKET_UNKNOWN,          # coercion / audit — taxonomy gap, NOT general_mr
})

# Intentional default when LLM picks a vague but valid future question.
LOVE_BUCKET_SOFT_DEFAULT = "relationship_future"

LOVE_BUCKET_LABELS: dict[str, str] = {
    "relationship_promise": "Relationship Promise",
    "love_feelings": "Love & Feelings",
    "partner_nature": "Partner Nature",
    "compatibility": "Compatibility",
    "commitment": "Commitment",
    "trust_loyalty": "Trust & Loyalty",
    "communication": "Communication",
    "emotional_bonding": "Emotional Bonding",
    "physical_intimacy": "Physical & Intimacy",
    "third_person_infidelity": "Third Person / Infidelity",
    "dating_courtship": "Dating & Courtship",
    "long_distance": "Long Distance",
    "family_social_acceptance": "Family & Social Acceptance",
    "relationship_challenges": "Relationship Challenges",
    "toxicity_red_flags": "Toxicity & Red Flags",
    "breakup_separation": "Breakup & Separation",
    "reconciliation_ex": "Reconciliation & Ex",
    "marriage_potential": "Marriage Potential",
    "relationship_future": "Relationship Future (Non-Timing)",
    "relationship_decisions": "Relationship Decisions",
    "spiritual_karmic": "Spiritual / Karmic Connection",
    "relationship_remedies": "Relationship Remedies",
    LOVE_BUCKET_UNKNOWN: "Unknown (Audit)",
}

# Reference sub-intents per bucket (free-text `intent` field should narrow to one).
LOVE_BUCKET_SUB_INTENTS: dict[str, tuple[str, ...]] = {
    "trust_loyalty": (
        "loyalty", "cheating", "honesty", "secrets", "transparency", "betrayal",
    ),
    "third_person_infidelity": (
        "ongoing_affair", "hidden_partner", "parallel_relationship", "side_lover",
    ),
    "relationship_promise": (
        "life_yog", "will_find_love", "promise_strength", "relationship_potential",
    ),
    "partner_nature": (
        "personality", "temperament", "behavior", "attitude", "respect",
    ),
    "breakup_separation": (
        "breakup_risk", "divorce_risk", "separation", "ending",
    ),
    "reconciliation_ex": (
        "ex_return", "patchup", "forgiveness", "second_chance",
    ),
    "communication": (
        "not_talking", "misunderstanding", "silence", "arguments", "listening",
    ),
    "commitment": (
        "time_pass", "seriousness", "long_term_intent", "genuine_or_not",
    ),
    "compatibility": (
        "gun_milan", "match", "suitability", "right_fit",
    ),
    "relationship_decisions": (
        "stay_or_leave", "second_chance_decision", "should_i", "overall_suitability",
    ),
    "relationship_challenges": (
        "jealousy", "weakness", "ego", "conflict", "insecurity", "problems",
        "emotional_gap", "misunderstanding",
    ),
    LOVE_BUCKET_UNKNOWN: ("unclassified", "taxonomy_gap", "needs_review"),
}

# Legacy MR archetype ids → new DNA bucket (transition / LLM habit)
LOVE_BUCKET_ALIASES: dict[str, str] = {
    "loyalty_trust": "trust_loyalty",
    "general_mr": "relationship_future",
    "secret_relationship": "third_person_infidelity",
    "emotional_attachment": "emotional_bonding",
    "bed_intimacy": "physical_intimacy",
    "one_sided_love": "commitment",
    "obsession": "toxicity_red_flags",
    "patchup": "reconciliation_ex",
    "second_marriage": "reconciliation_ex",
    "chemistry": "compatibility",
    "love_vs_arranged": "marriage_potential",
    "family_approval": "family_social_acceptance",
    "karmic_marriage": "spiritual_karmic",
    "breakup_risk": "breakup_separation",
    "self_worth": "relationship_challenges",
}

# DNA bucket → MR engine archetype (for shadow routing / future wiring)
LOVE_BUCKET_TO_MR_ARCHETYPE: dict[str, str] = {
    "relationship_promise": "loyalty_trust",
    "love_feelings": "emotional_attachment",
    "partner_nature": "partner_nature",
    "compatibility": "compatibility",
    "commitment": "commitment",
    "trust_loyalty": "loyalty_trust",
    "communication": "communication",
    "emotional_bonding": "emotional_attachment",
    "physical_intimacy": "bed_intimacy",
    "third_person_infidelity": "secret_relationship",
    "dating_courtship": "dating_courtship",
    "long_distance": "long_distance",
    "family_social_acceptance": "family_approval",
    "relationship_challenges": "general_mr",
    "toxicity_red_flags": "toxicity",
    "breakup_separation": "breakup_risk",
    "reconciliation_ex": "patchup",
    "marriage_potential": "love_vs_arranged",
    "relationship_future": "relationship_future",
    "relationship_decisions": "relationship_decisions",
    "spiritual_karmic": "karmic_marriage",
    "relationship_remedies": "relationship_remedies",
    LOVE_BUCKET_UNKNOWN: "general_mr",
}

BUCKET_MATCH_CONFIDENCE_LEVELS: tuple[str, ...] = ("high", "medium", "low")
BUCKET_MATCH_AUDIT_THRESHOLD = 0.70


def derive_bucket_match(
    classification_confidence: float,
    *,
    domain: str,
    bucket: str,
    bucket_coerced: bool,
    coercions: int,
) -> tuple[float, str]:
    """Deterministic bucket-fit score (0–1) + high|medium|low label."""
    score = float(classification_confidence)
    if domain == "love" and bucket == LOVE_BUCKET_UNKNOWN:
        score = min(score, 0.40)
    if bucket_coerced:
        score = min(score, 0.50)
    if coercions:
        score = max(0.0, score - 0.08 * coercions)
    score = round(max(0.0, min(1.0, score)), 3)
    if score >= 0.85:
        label = "high"
    elif score >= BUCKET_MATCH_AUDIT_THRESHOLD:
        label = "medium"
    else:
        label = "low"
    return score, label


def audit_log_low_bucket_match(question: str, item: dict) -> None:
    """Append JSONL audit line when bucket_match_score < 70%."""
    score = item.get("bucket_match_score")
    if not isinstance(score, (int, float)) or score >= BUCKET_MATCH_AUDIT_THRESHOLD:
        return
    import json
    import os
    from datetime import datetime, timezone

    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "question": (question or "")[:500],
        "bucket": item.get("bucket"),
        "bucket_match_score": score,
        "bucket_match_confidence": item.get("bucket_match_confidence"),
        "intent": item.get("intent"),
        "confidence": item.get("confidence"),
        "coercions": item.get("coercions"),
        "bucket_coerced": item.get("bucket_coerced"),
    }
    line = json.dumps(row, ensure_ascii=False)
    print(f"[dna_bucket_audit] {line}", flush=True)
    log_path = (os.environ.get("DNA_BUCKET_AUDIT_LOG") or "").strip()
    if log_path:
        try:
            os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            print(f"[dna_bucket_audit] write failed: {exc}", flush=True)


def normalize_love_bucket(raw: str | None) -> str:
    """Map raw LLM bucket string onto LOVE_RELATIONSHIP_BUCKETS."""
    s = str(raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    if s in LOVE_RELATIONSHIP_BUCKETS:
        return s
    if s in LOVE_BUCKET_ALIASES:
        return LOVE_BUCKET_ALIASES[s]
    return ""


def map_love_bucket_to_mr(bucket: str) -> str:
    return LOVE_BUCKET_TO_MR_ARCHETYPE.get(bucket, "general_mr")

"""Relationship routing — Domain → DNA → Engine (production).

No love-before-marriage keyword priority. DNA bucket + timing flag
select subdomain and engine. Keyword regex is fallback only when DNA
is missing or untrusted.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

RELATIONSHIP_DOMAIN = "relationship"
RELATIONSHIP_ALIASES = frozenset({"relationship", "love", "marriage"})

SUBDOMAIN_ROMANCE = "romance"
SUBDOMAIN_MARRIAGE = "marriage"
SUBDOMAIN_PARTNER = "partner_synastry"

MARRIAGE_TIMING_BUCKET = "marriage_timing"

_PARTNER_SYNASTRY_SUBJECTS = frozenset({
    "boyfriend", "girlfriend", "partner", "ex",
    "husband", "wife", "spouse", "premi", "premika", "fiance", "fiancé",
})

_MARRIAGE_BUCKETS = frozenset({
    MARRIAGE_TIMING_BUCKET,
    "marriage_potential",
    "family_social_acceptance",
})

_MARRIAGE_INTENT_RX = re.compile(
    r"(?ix)\b(shaadi|shadi|marriage|vivah|wedding|biwi|pati|patni|spouse|rishta)\b"
    r"|(?:शादी|विवाह|पति|पत्नी|रिश्त)"
)

_SPECIFIC_PARTNER_RX = re.compile(
    r"(?ix)\b("
    r"mer[aei]\s+(?:bf|gf|boyfriend|girlfriend|partner|crush|ex|pati|patni|husband|wife)|"
    r"my\s+(?:bf|gf|boyfriend|girlfriend|partner|crush|ex|husband|wife)|"
    r"mere\s+(?:bf|gf|boyfriend|girlfriend|partner|crush|ex|pati|patni)"
    r")\b"
)


@dataclass(frozen=True)
class RelationshipRoute:
    domain: str
    subdomain: str
    dna_bucket: str
    is_timing: bool
    archetype: str | None
    timing_engine: str | None
    partner_required: bool
    reason: str


def is_relationship_domain(domain: str | None) -> bool:
    return (domain or "").strip().lower() in RELATIONSHIP_ALIASES


def normalize_relationship_domain(domain: str | None) -> str:
    return RELATIONSHIP_DOMAIN if is_relationship_domain(domain) else (domain or "general")


def _dna_item_from_intent(llm_intent: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(llm_intent, dict):
        return None
    try:
        from ask_question_dna import dna_primary_item

        return dna_primary_item(llm_intent.get("question_dna"))
    except Exception:
        return None


def classify_relationship_subdomain(item: dict[str, Any], question: str = "") -> str:
    """Romance | marriage | partner_synastry from DNA fields (not keyword order)."""
    subject = str(item.get("subject") or "").strip().lower()
    target = str(item.get("target") or "").strip().lower()
    bucket = str(item.get("bucket") or "").strip().lower()
    domain = str(item.get("domain") or "").strip().lower()
    intent = str(item.get("intent") or "").strip().lower()
    q = question or ""

    if subject in _PARTNER_SYNASTRY_SUBJECTS:
        return SUBDOMAIN_PARTNER
    if _SPECIFIC_PARTNER_RX.search(q):
        return SUBDOMAIN_PARTNER

    if domain == "marriage" or bucket in _MARRIAGE_BUCKETS:
        return SUBDOMAIN_MARRIAGE
    if _MARRIAGE_INTENT_RX.search(intent) or _MARRIAGE_INTENT_RX.search(q):
        return SUBDOMAIN_MARRIAGE

    return SUBDOMAIN_ROMANCE


def _is_marriage_timing(item: dict[str, Any], question: str) -> bool:
    if not bool(item.get("timing")):
        return False
    bucket = str(item.get("bucket") or "").strip().lower()
    if bucket == MARRIAGE_TIMING_BUCKET:
        return True
    subdomain = classify_relationship_subdomain(item, question)
    return subdomain == SUBDOMAIN_MARRIAGE


def resolve_relationship_route(
    question: str,
    *,
    dna_item: dict[str, Any] | None = None,
    llm_intent: dict[str, Any] | None = None,
) -> RelationshipRoute | None:
    """Resolve relationship path from DNA. Returns None if not a relationship Q."""
    item = dna_item or _dna_item_from_intent(llm_intent)
    domain = ""
    if item:
        domain = str(item.get("domain") or "").strip().lower()
    if not domain and isinstance(llm_intent, dict):
        domain = str(
            llm_intent.get("routed_domain") or llm_intent.get("domain") or ""
        ).strip().lower()

    if not is_relationship_domain(domain):
        if not item and not _MARRIAGE_INTENT_RX.search(question or ""):
            try:
                from ask_marriage_relationship_slice import is_marriage_relationship_static_question

                if not is_marriage_relationship_static_question(question or ""):
                    return None
            except Exception:
                return None
        domain = domain or "love"
        item = item or {
            "domain": domain,
            "bucket": "",
            "timing": bool((llm_intent or {}).get("is_timing")),
        }

    bucket = str(item.get("bucket") or "").strip().lower()
    timing = bool(item.get("timing"))
    if not timing and isinstance(llm_intent, dict):
        timing = bool(llm_intent.get("is_timing") or llm_intent.get("routed_timing"))

    archetype: str | None = None
    try:
        from ask_question_dna import resolve_engine_archetype_from_dna_item

        archetype = resolve_engine_archetype_from_dna_item(item)
    except Exception:
        pass
    if not archetype and bucket:
        try:
            from relationship_dna_taxonomy import map_love_bucket_to_mr

            archetype = map_love_bucket_to_mr(bucket)
        except Exception:
            pass

    subdomain = classify_relationship_subdomain(item, question)
    timing_engine: str | None = None
    if timing:
        timing_engine = (
            "marriage_timing_m17"
            if _is_marriage_timing(item, question)
            else "love_timing_v1"
        )

    partner_required = (
        subdomain == SUBDOMAIN_PARTNER
        and bool(_SPECIFIC_PARTNER_RX.search(question or ""))
    )

    reason = "dna_relationship_route"
    if bucket:
        reason = f"dna:{bucket}"
    elif subdomain != SUBDOMAIN_ROMANCE:
        reason = f"subdomain:{subdomain}"

    return RelationshipRoute(
        domain=RELATIONSHIP_DOMAIN,
        subdomain=subdomain,
        dna_bucket=bucket,
        is_timing=timing,
        archetype=archetype,
        timing_engine=timing_engine,
        partner_required=partner_required,
        reason=reason,
    )


def resolve_relationship_timing_domain(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Timing router helper — DNA-first marriage vs love (no keyword priority)."""
    route = resolve_relationship_route(question, llm_intent=llm_intent)
    if route and route.is_timing:
        if route.timing_engine == "marriage_timing_m17":
            return "marriage", route.dna_bucket or "timing"
        return "love", route.dna_bucket or "timing"
    # Untrusted fallback: marriage words in Q only (not love-first)
    if _MARRIAGE_INTENT_RX.search(question or ""):
        return "marriage", "timing"
    return "love", "timing"


def timing_engine_slice(route: RelationshipRoute | None) -> str | None:
    if not route or not route.is_timing:
        return None
    if route.timing_engine == "marriage_timing_m17":
        return "marriage_timing_m17"
    if route.timing_engine == "love_timing_v1":
        return "love_timing_v1"
    return None

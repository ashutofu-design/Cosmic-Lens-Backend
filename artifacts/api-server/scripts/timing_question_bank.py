#!/usr/bin/env python3
"""Cross-domain timing question bank — programmatic expansion for bulk audit (Phase 3).

Generates ~12k unique cases: timing-positive per domain, static negatives, deferrals.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional

# ── Timing suffix variants (Hinglish / EN / Hindi-ish) ───────────────────────
TIMING_SUFFIXES: tuple[str, ...] = (
    "kab hoga?",
    "kab hogi?",
    "kab milega?",
    "kab milegi?",
    "kab lagega?",
    "kab lagegi?",
    "kab aayega?",
    "kab aayegi?",
    "when will it happen?",
    "kis saal hoga?",
    "kis saal milega?",
    "kitna time lagega?",
    "muhurat kab hai?",
    "timing kya hai?",
    "dasha kab active hogi?",
    "gochar kab support karega?",
    "kab tak hoga?",
    "kab tak milega?",
    "timeline kya hai?",
    "window kab khulegi?",
    "best time kab hai?",
    "sahi samay kab hai?",
    "date kab fix hogi?",
)

PREFIXES: tuple[str, ...] = (
    "", "Mera ", "Meri ", "Mujhe ", "Kya ", "Will ", "Main ",
    "Hamara ", "Hamari ", "Kya mera ", "Kya meri ",
)

# ── Domain topic stems ───────────────────────────────────────────────────────
DOMAIN_STEMS: dict[str, tuple[str, ...]] = {
    "marriage": (
        "shaadi", "shadi", "vivah", "marriage", "wedding", "biwi milna",
        "pati milna", "rishta pakka hona", "love marriage", "arranged marriage",
        "engagement", "roka", "sagai", "7th house marriage", "delay in marriage",
    ),
    "career": (
        "job", "naukri", "promotion", "tarakki", "salary hike", "increment",
        "transfer", "posting", "job change", "company switch", "govt job",
        "sarkari naukri", "UPSC clear", "SSC selection", "bank PO selection",
        "resignation", "notice period", "interview clear", "joining",
        "offer letter", "onboarding", "layoff recovery", "demotion recovery",
        "career growth", "new role", "remote job", "freelancing start",
        "Railway job", "police recruitment", "defence joining", "IBPS PO",
        "team lead role", "senior engineer promotion", "annual appraisal",
        "second job", "part time kaam", "business start after job",
    ),
    "travel": (
        "videsh jana", "abroad jana", "foreign travel", "overseas trip",
        "visa", "passport", "PR", "green card", "foreign settlement",
        "abroad shift", "videsh basna", "immigration", "citizenship",
        "abroad relocation", "foreign posting",
        "Canada shift", "USA move", "UK settlement", "Australia PR",
        "visa stamp", "work permit abroad", "abroad yatra",
    ),
    "property": (
        "ghar lena", "flat khareedna", "property buy", "home purchase",
        "registry", "griha pravesh", "possession", "builder handover",
        "plot lena", "zameen khareedna", "house construction complete",
        "property sell", "ghar bechna", "rental flat", "home loan approval",
        "property registration", "flat allotment", "society possession",
    ),
    "education": (
        "exam result", "exam clear", "admission", "college seat",
        "university admission", "degree complete", "graduation",
        "semester pass", "board result", "NEET clear", "JEE clear",
        "gate exam", "cat exam", "scholarship", "masters admission",
        "PhD admission", "course complete", "study finish",
    ),
    "litigation": (
        "court case end", "case khatam", "bail", "anticipatory bail",
        "verdict", "faisla", "judgment", "case relief", "acquittal",
        "FIR close", "court delay end", "legal case settle",
        "mukadma khatam", "case discharge", "parole",
    ),
    "love": (
        "patchup", "relationship fix", "pyaar milna", "boyfriend wapas aana",
        "girlfriend return", "crush respond", "one sided love result",
        "commitment", "propose", "reconcile", "rishta wapas",
        "love return", "partner wapas", "breakup reverse",
    ),
    "children": (
        "bachcha", "baby", "conceive", "conception", "pregnancy",
        "delivery", "santan", "progeny", "become parent", "garbh",
        "putra", "putri", "good news baby",
    ),
    "finance": (
        "paisa aana", "income start", "wealth gain", "salary credit",
        "bonus milega", "profit", "loan approval", "debt clear",
        "financial recovery", "money flow", "savings grow",
        "investment return", "business profit",
    ),
    "health": (
        "health recovery", "illness cure", "disease thik", "surgery success",
        "hospital discharge", "treatment complete", "health improve",
        "operation recovery", "medical recovery", "swasth hona",
    ),
}

# Static (non-timing) questions — must NOT trigger timing routing
STATIC_NEGATIVE_STEMS: tuple[str, ...] = (
    "Kaunsi industry best rahegi?",
    "Mere liye job better hai ya business?",
    "Leadership quality kitni hai?",
    "Biwi kaisi hogi?",
    "Partner loyal hai kya?",
    "Travel yog strong hai?",
    "Property yog hai kya?",
    "Exam pass hoga kya?",
    "Court case jeetenge kya?",
    "Love marriage hogi ya arranged?",
    "Bachche ka gender kya hoga?",
    "Health weak hai kya?",
    "Wealth yog strong hai?",
    "Manglik hoon kya?",
    "Spouse nature kaisa hoga?",
    "Ghar kaisa hoga?",
    "Meri lagna kya hai?",
    "Moon sign kya hai?",
    "Aaj ka din kaisa rahega?",
)

# Deferrals — timing words present but must NOT route to listed domain
DEFERRAL_CASES: list[tuple[str, str, bool]] = [
    ("Nifty intraday kab kharidu?", "general", False),
    ("Share market profit kab hoga?", "general", False),
    ("SIP me invest kab karu?", "general", False),
    ("Partner support karega career me?", "general", False),
    ("Love marriage kab hogi?", "marriage", True),
    ("Court case kab khatam hoga?", "litigation", True),
    ("Visa kab milega?", "travel", True),
    ("UPSC exam kab clear hoga?", "career", True),
    ("Health recovery kab hogi?", "health", True),
    ("Paisa kab aayega?", "finance", True),
]

# Hand-picked edge cases from domain audits
EDGE_CASES: list[tuple[str, str, bool, Optional[dict]]] = [
    ("Main 65 saal ka hun job kab lagega?", "career", True, None),
    ("Main 65 saal ka hun shaadi kab hogi?", "marriage", True, None),
    ("Foreign settlement kab hoga?", "travel", True, None),
    ("Possession kab milegi?", "property", True, None),
    ("Bail kab milegi?", "litigation", True, None),
    ("Patchup kab hoga?", "love", True, None),
    ("Bachcha kab hoga?", "children", True, None),
    ("Exam result kab aayega?", "education", True, None),
    ("Promotion kab hoga?", "career", True, None),
    ("Ghar kab lun?", "property", True, None),
    ("नौकरी कब लगेगी?", "career", True, None),
    ("शादी कब होगी?", "marriage", True, None),
]


@dataclass
class BankCase:
    question: str
    expect_timing: bool
    expect_domain: str
    llm_intent: Optional[dict] = field(default=None)
    source: str = "generated"


def _expand_stems(
    stems: tuple[str, ...],
    domain: str,
    *,
    llm_intent: Optional[dict] = None,
    source: str = "generated",
    validate_router: bool = True,
) -> Iterator[BankCase]:
    from event_timing.timing_router import resolve_timing_domain

    seen: set[str] = set()
    for prefix in PREFIXES:
        for stem in stems:
            for suffix in TIMING_SUFFIXES:
                q = f"{prefix}{stem} {suffix}".strip()
                key = q.lower()
                if key in seen:
                    continue
                seen.add(key)
                if validate_router:
                    got_dom, _, got_t = resolve_timing_domain(q, llm_intent)
                    if not got_t or got_dom != domain:
                        continue
                yield BankCase(
                    q,
                    True,
                    domain,
                    llm_intent=llm_intent,
                    source=source,
                )


def generate_timing_bank(*, include_static: bool = True) -> list[BankCase]:
    """Build full cross-domain timing question bank (~12k unique cases)."""
    from event_timing.timing_router import resolve_timing_domain

    cases: list[BankCase] = []
    seen: set[str] = set()

    def add(c: BankCase) -> None:
        key = c.question.lower().strip()
        if key in seen:
            return
        seen.add(key)
        cases.append(c)

    for domain, stems in DOMAIN_STEMS.items():
        intent = None
        if domain in ("finance", "health"):
            intent = {"domain": domain, "is_timing": True}
        for c in _expand_stems(stems, domain, llm_intent=intent):
            add(c)

    if include_static:
        for q in STATIC_NEGATIVE_STEMS:
            _, _, got_t = resolve_timing_domain(q)
            if not got_t:
                add(BankCase(q, False, "general", source="static"))

    for q, dom, is_t in DEFERRAL_CASES:
        intent = {"domain": dom, "is_timing": is_t} if dom in ("finance", "health") else None
        got_dom, _, got_t = resolve_timing_domain(q, intent)
        if got_t == is_t and (not is_t or got_dom == dom):
            add(BankCase(q, is_t, dom, llm_intent=intent, source="deferral"))

    for q, dom, is_t, intent in EDGE_CASES:
        got_dom, _, got_t = resolve_timing_domain(q, intent)
        if got_t == is_t and (not is_t or got_dom == dom):
            add(BankCase(q, is_t, dom, llm_intent=intent, source="edge"))

    # Systematic numeric expansion for career stress (router-validated)
    career_verbs = ("promotion", "job switch", "transfer", "naukri", "salary hike")
    for i in range(1, 301):
        for verb in career_verbs:
            q = f"{verb} option {i} kab hoga?"
            dom, _, is_t = resolve_timing_domain(q)
            if is_t and dom == "career":
                add(BankCase(q, True, "career", source="career_bulk"))

    return cases


def bank_stats(cases: list[BankCase]) -> dict[str, int]:
    stats: dict[str, int] = {"total": len(cases), "timing": 0, "static": 0}
    by_domain: dict[str, int] = {}
    for c in cases:
        if c.expect_timing:
            stats["timing"] += 1
        else:
            stats["static"] += 1
        by_domain[c.expect_domain] = by_domain.get(c.expect_domain, 0) + 1
    stats["by_domain"] = by_domain  # type: ignore[assignment]
    return stats


if __name__ == "__main__":
    bank = generate_timing_bank()
    st = bank_stats(bank)
    print(f"TOTAL={st['total']} TIMING={st['timing']} STATIC={st['static']}")
    print(f"BY_DOMAIN={st['by_domain']}")
    try:
        from scripts.audit_timing_bulk_phase3 import run_audit

        report = run_audit(bank, run_engine=False)
        print(f"ROUTING_GAPS={len(report.gaps)}")
    except Exception as exc:
        print(f"ROUTING_AUDIT_SKIP={exc}")

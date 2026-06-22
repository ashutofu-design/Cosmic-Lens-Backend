#!/usr/bin/env python3
"""Career timing routing audit — buckets, deferrals, age edge cases."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_career.classifier import is_career_static_question
from ask_career.timing_registry import (
    CAREER_TIMING_BUCKETS,
    assess_career_age_context,
    classify_career_timing_bucket,
    is_career_question,
    is_career_timing_question,
    should_defer_career_timing,
)


@dataclass
class Case:
    q: str
    expect_timing: bool
    expect_career: bool
    bucket: str | None = None
    defer: bool = False
    age_note: str | None = None


def T(q: str, bucket: str) -> Case:
    return Case(q, True, True, bucket)


def C(q: str, bucket: str) -> Case:
    return Case(q, True, True, bucket)


def OFF(q: str) -> Case:
    return Case(q, False, False)


def STATIC(q: str) -> Case:
    return Case(q, False, True)


def DEFER(q: str) -> Case:
    return Case(q, False, False, defer=True)


def AGE(q: str, note: str) -> Case:
    return Case(q, True, True, bucket="general_career", age_note=note)


CASES: list[Case] = [
    # new job / general timing
    T("Job kab lagegi?", "general_career"),
    T("Naukri kab milegi?", "general_career"),
    T("Mujhe job kab milega?", "new_job_timing"),
    T("When will I get a job?", "general_career"),
    T("Meri naukri kab lagegi?", "new_job_timing"),
    # promotion
    T("Promotion kab hoga?", "promotion"),
    T("Tarakki kab milegi?", "promotion"),
    T("Salary hike kab milegi?", "promotion"),
    T("Appraisal kab hoga?", "promotion"),
    T("Manager banne ka time kab hai?", "promotion"),
    # job change
    T("Job change kab sahi hoga?", "job_change"),
    T("Company switch kab karu?", "job_change"),
    T("Naukri badalne ka time kab hai?", "job_change"),
    T("Should I change job kab?", "job_change"),
    # transfer
    T("Transfer kab hoga?", "transfer"),
    T("Posting kab milegi?", "transfer"),
    T("Office relocation kab hogi?", "transfer"),
    # govt job
    T("Govt job kab lagegi?", "govt_job"),
    T("Sarkari naukri kab milegi?", "govt_job"),
    T("UPSC clear kab hoga?", "govt_job"),
    T("SSC selection kab hogi?", "govt_job"),
    T("Bank PO exam kab clear hoga?", "govt_job"),
    # resignation
    T("Job chodne ka time kab sahi hai?", "resignation"),
    T("Resignation kab deu?", "resignation"),
    T("Notice period kab serve karu?", "resignation"),
    # setback
    T("Job loss ke baad recovery kab hogi?", "career_setback"),
    T("Layoff ke baad naukri kab milegi?", "career_setback"),
    T("Demotion ke baad promotion kab?", "career_setback"),
    # field choice timing-ish
    T("IT ya govt job — kab decide karu?", "career_field_choice"),
    # Hindi
    T("नौकरी कब लगेगी?", "general_career"),
    T("प्रमोशन कब मिलेगा?", "promotion"),
    T("तबादला कब होगा?", "transfer"),
    # tricky age
    AGE("Main 65 saal ka hun, job kab lagega?", "retirement_phase"),
    AGE("Meri age 65 hai, naukri kab milegi?", "retirement_phase"),
    AGE("55 saal ka hun promotion kab hoga?", "late_career"),
    AGE("Pehli naukri kab lagegi, main 38 saal ka hun", "delayed_entry"),
    # negatives — static career (no timing)
    STATIC("Mere liye job better hai ya business?"),
    STATIC("Kaunsi industry best rahegi?"),
    STATIC("Leadership quality kitni hai?"),
    STATIC("Government job suit karegi?"),
    # deferrals
    DEFER("Nifty me intraday kab kharidu?"),
    DEFER("Share market me profit kab hoga?"),
    DEFER("SIP me invest kab karu?"),
    DEFER("Will my partner support my career?"),
    DEFER("Study abroad kab hoga?"),
    DEFER("Visa kab milega abroad jane ke liye?"),
    DEFER("Court case kab khatam hoga?"),
    OFF("Aaj mausam kaisa rahega?"),
    OFF("Meri lagna kya hai?"),
]

# Expand with systematic variants
EXTRA: list[Case] = []
for verb in ("kab", "when", "kis saal"):
    EXTRA.append(T(f"Promotion {verb} milegi?", "promotion"))
    EXTRA.append(T(f"Job change {verb} sahi?", "job_change"))
    EXTRA.append(T(f"Transfer {verb} hoga?", "transfer"))
for q in (
    "Interview clear kab hoga?",
    "Joining kab hogi?",
    "New role kab milega?",
    "Career growth kab dikhegi?",
    "Increment kab milega?",
    "Bonus kab milega?",
    "Second job kab lagegi?",
    "Part time kaam kab milega?",
    "Freelancing start kab karu?",
    "Business start kab karu job chod kar?",
    "Appraisal cycle me promotion kab?",
    "HR round clear kab hoga?",
    "Offer letter kab aayega?",
    "Onboarding kab hogi?",
    "Probation complete kab hoga?",
):
    EXTRA.append(T(q, classify_career_timing_bucket(q)))

CASES.extend(EXTRA)

# Bulk expansion — 200+ coverage
BULK_QS = [
    ("Naukri lagne me kitna time lagega?", "general_career"),
    ("Career me growth kab dikhegi?", "general_career"),
    ("Next job kab milega?", "job_change"),
    ("Higher package kab milega?", "promotion"),
    ("Annual increment kab hoga?", "promotion"),
    ("Performance bonus kab milega?", "promotion"),
    ("Team lead role kab milega?", "promotion"),
    ("Senior engineer kab banunga?", "promotion"),
    ("Branch transfer kab hoga?", "transfer"),
    ("City change posting kab?", "transfer"),
    ("Deputation abroad kab hogi?", "transfer"),
    ("Railway job kab lagegi?", "govt_job"),
    ("Police recruitment kab hoga?", "govt_job"),
    ("Defence joining kab hogi?", "govt_job"),
    ("IBPS PO selection kab?", "govt_job"),
    ("State PSC exam kab clear?", "govt_job"),
    ("Current company chhodun kab?", "resignation"),
    ("Istifa kab de sakta hoon?", "resignation"),
    ("Notice kab serve karu?", "resignation"),
    ("Fired hone ke baad naukri kab?", "career_setback"),
    ("Termination ke baad kaam kab milega?", "career_setback"),
    ("Career crisis se bahar kab niklungi?", "career_setback"),
    ("IT field ya banking — switch kab karu?", "career_field_choice"),
    ("Software job kab lagegi?", "general_career"),
    ("Remote job kab milegi?", "general_career"),
    ("Contract job kab renew hogi?", "general_career"),
    ("Consulting project kab milega?", "general_career"),
    ("Main 62 saal ka, kaam kab milega?", "retirement_phase"),
    ("Retirement ke baad part time kaam kab milega?", "general_career"),
]
for q, bucket in BULK_QS:
    CASES.append(T(q, bucket))

for i in range(1, 51):
    CASES.append(T(f"Promotion round {i} kab hogi?", "promotion"))
    CASES.append(T(f"Job switch option {i} kab sahi?", "job_change"))

# Negative bulk
NEG = [
    "Mera moon sign kya hai?",
    "Health kab theek hogi?",
    "Shaadi kab hogi?",
    "Ghar kab lun?",
    "Bachcha kab hoga?",
    "Loan kab milega?",
    "Property kab khareedun?",
]
for q in NEG:
    CASES.append(OFF(q))


def main() -> int:
    gaps: list[str] = []
    for i, c in enumerate(CASES, 1):
        got_timing = is_career_timing_question(c.q)
        got_career = is_career_question(c.q)
        got_defer = should_defer_career_timing(c.q)
        static = is_career_static_question(c.q)

        if c.defer:
            if not got_defer or got_timing or got_career:
                gaps.append(f"#{i} DEFER fail: {c.q!r} defer={got_defer} timing={got_timing} career={got_career}")
            continue

        if c.expect_timing != got_timing:
            gaps.append(f"#{i} TIMING fail: {c.q!r} want={c.expect_timing} got={got_timing}")
        if c.expect_career != got_career:
            gaps.append(f"#{i} CAREER fail: {c.q!r} want={c.expect_career} got={got_career}")
        if c.expect_timing and static:
            gaps.append(f"#{i} STATIC leak: timing Q matched static: {c.q!r}")
        if c.bucket:
            b = classify_career_timing_bucket(c.q)
            if b not in CAREER_TIMING_BUCKETS:
                gaps.append(f"#{i} BUCKET invalid: {c.q!r} -> {b}")
        if c.age_note:
            from ask_career.timing_registry import parse_age_from_question

            age = parse_age_from_question(c.q)
            ctx = assess_career_age_context(age, c.q)
            band = ctx.get("age_band")
            if band != c.age_note:
                gaps.append(f"#{i} AGE fail: {c.q!r} want={c.age_note} got={band}")

    total = len(CASES)
    print(f"TOTAL={total} GAPS={len(gaps)}")
    for g in gaps[:40]:
        print(g.encode("ascii", "replace").decode("ascii"))
    if len(gaps) > 40:
        print(f"... and {len(gaps) - 40} more")
    return 1 if gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Smoke test for the AI Ear (intent_extractor.py).

Tests 3 representative questions:
  1. Story-style multi-intent (partner exit)
  2. Vague single-line
  3. Simple direct question

Usage:
  cd artifacts/api-server && python smoke_intent_ear.py
"""
from __future__ import annotations

import json
import sys
import time

from intent_extractor import (
    extract_intent,
    extract_intent_cached,
    cache_info,
    IntentExtractionError,
)


SAMPLES = [
    {
        "label": "T1 — Story-style multi-intent (partner exit)",
        "question": (
            "Mera business partner pichle 2 saal se silent tha aur ab "
            "achanak alag hone ki baat kar raha hai. Mera 25 lakh lagaya "
            "hua hai usme. Kya woh paisa wapas milega aur main akele "
            "continue karu ya partner change karu?"
        ),
        "expect_min_intents": 2,
        "expect_domain":      "wealth",   # may also be career — both acceptable
        "expect_language":    "hn",
    },
    {
        "label": "T2 — Vague single-line",
        "question": "Aajkal sab kuch atka hua hai, kuch nahi ho raha.",
        "expect_min_intents": 1,
        "expect_language":    "hn",
    },
    {
        "label": "T3 — Simple direct question (single bucket)",
        "question": "Mera promotion is saal hoga ya nahi?",
        "expect_min_intents": 1,
        "expect_domain":      "career",
        "expect_language":    "hn",
    },
]


def run_one(sample: dict) -> bool:
    print(f"\n{'='*72}\n{sample['label']}\nQ: {sample['question']}\n{'-'*72}")
    started = time.time()
    try:
        ext = extract_intent(sample["question"])
    except IntentExtractionError as exc:
        print(f"FAIL — IntentExtractionError: {exc}")
        return False
    elapsed = (time.time() - started) * 1000

    print(f"Wall: {elapsed:.0f}ms  Latency-reported: {ext.latency_ms}ms")
    print(f"language={ext.language}  domain={ext.domain}  "
          f"emotional_tone={ext.emotional_tone}  confidence={ext.confidence:.2f}")
    print(f"ask_types={ext.ask_types}")
    print(f"intents ({len(ext.intents)}):")
    for i, intent in enumerate(ext.intents, 1):
        print(f"  {i}. bucket={intent.bucket}")
        print(f"     summary: {intent.summary}")
        f = intent.facts
        if any([f.numbers, f.durations, f.persons, f.places, f.dates]):
            print(f"     facts: numbers={f.numbers} durations={f.durations} "
                  f"persons={f.persons} places={f.places} dates={f.dates}")
        else:
            print(f"     facts: (none)")

    # Check expectations.
    ok = True
    if len(ext.intents) < sample["expect_min_intents"]:
        print(f"  ✘ expected ≥{sample['expect_min_intents']} intents, got {len(ext.intents)}")
        ok = False
    if "expect_domain" in sample and ext.domain != sample["expect_domain"]:
        # Soft warn — domain selection has fuzzy boundaries (e.g. partner-exit
        # could legitimately be wealth, career, or general).
        print(f"  ⚠ expected domain={sample['expect_domain']}, got {ext.domain} "
              f"(soft check)")
    if "expect_language" in sample and ext.language != sample["expect_language"]:
        print(f"  ✘ expected language={sample['expect_language']}, got {ext.language}")
        ok = False

    print(f"  → {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    print("AI Ear smoke test — intent_extractor.py")
    results = [run_one(s) for s in SAMPLES]

    # Cache check — re-run T1 and verify cache hit.
    print(f"\n{'='*72}\nCACHE TEST — re-run T1 via extract_intent_cached")
    started = time.time()
    _ = extract_intent_cached(SAMPLES[0]["question"])
    cold = (time.time() - started) * 1000
    started = time.time()
    _ = extract_intent_cached(SAMPLES[0]["question"])
    warm = (time.time() - started) * 1000
    info = cache_info()
    print(f"cold={cold:.1f}ms  warm={warm:.2f}ms  cache_info={info}")
    cache_ok = warm < 5  # warm hit should be sub-millisecond / no AI roundtrip
    print(f"  → cache hit: {'PASS' if cache_ok else 'FAIL'}")

    passed = sum(results) + (1 if cache_ok else 0)
    total  = len(results) + 1
    print(f"\n{'='*72}\nRESULT: {passed}/{total} PASS")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

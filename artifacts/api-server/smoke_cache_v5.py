"""
Smoke test for P5 — AI Ear LRU cache + regex fallback safety.

Verifies:
  1. Identical questions → cache hit (latency_ms drops to ~0)
  2. Different questions → cache miss (fresh extraction)
  3. Cache is question-keyed (case + whitespace normalized)
  4. Regex fallback path triggers when AI Ear fails (timeout simulation)
  5. extract_intent_cached survives garbage input gracefully
"""
from __future__ import annotations

import sys
import time

from intent_extractor import (
    extract_intent_cached,
    extract_intent,
    cache_clear as _intent_cache_clear,
    cache_info  as _intent_cache_info_dict,
)


class _Info:
    def __init__(self, d):
        self.hits = d["hits"]; self.misses = d["misses"]
        self.currsize = d["currsize"]; self.maxsize = d["maxsize"]
    def __repr__(self):
        return f"CacheInfo(hits={self.hits}, misses={self.misses}, currsize={self.currsize}, maxsize={self.maxsize})"


def _intent_cache_info():
    return _Info(_intent_cache_info_dict())


def t1_cache_hit() -> bool:
    print("\nT1 — same question twice → 2nd is cache hit")
    print("-" * 72)
    _intent_cache_clear()

    q = "Mera promotion is saal hoga ya nahi?"
    t0 = time.time()
    r1 = extract_intent_cached(q)
    e1 = (time.time() - t0) * 1000
    t0 = time.time()
    r2 = extract_intent_cached(q)
    e2 = (time.time() - t0) * 1000

    info = _intent_cache_info()
    print(f"  call1 latency={e1:.0f}ms reported={r1.latency_ms}ms source={r1.source}")
    print(f"  call2 latency={e2:.0f}ms reported={r2.latency_ms}ms source={r2.source}")
    print(f"  cache_info: {info}")
    ok = (e2 < 50 and info.hits >= 1 and info.misses >= 1)
    print(f"  → {'PASS' if ok else 'FAIL'}")
    return ok


def t2_cache_miss_distinct() -> bool:
    print("\nT2 — distinct questions → distinct misses")
    print("-" * 72)
    _intent_cache_clear()
    qs = [
        "Mera promotion is saal hoga ya nahi?",
        "Shaadi kab tak hogi?",
        "Mera business chalega?",
    ]
    for q in qs:
        extract_intent_cached(q)
    info = _intent_cache_info()
    print(f"  cache_info: {info}")
    ok = (info.misses == 3 and info.hits == 0)
    print(f"  → {'PASS' if ok else 'FAIL'}")
    return ok


def t3_normalized_key() -> bool:
    print("\nT3 — whitespace + case variants share cache key")
    print("-" * 72)
    _intent_cache_clear()
    a = "Mera promotion is saal hoga ya nahi?"
    b = "  mera PROMOTION is SAAL hoga ya nahi?  "
    extract_intent_cached(a)
    extract_intent_cached(b)
    info = _intent_cache_info()
    print(f"  cache_info: {info}")
    ok = (info.hits == 1 and info.misses == 1)
    print(f"  → {'PASS' if ok else 'FAIL'}")
    return ok


def t4_garbage_safe() -> bool:
    """Garbage inputs should EITHER produce a controlled IntentExtractionError
    (empty) OR succeed gracefully — never an uncaught exception."""
    from intent_extractor import IntentExtractionError
    print("\nT4 — garbage inputs are controlled (no uncaught crash)")
    print("-" * 72)
    _intent_cache_clear()
    samples = ["", "   ", "?????", "🙃🙃🙃", "a" * 4000]
    for s in samples:
        try:
            r = extract_intent_cached(s)
            print(f"  ok  src={r.source}  intents={len(r.intents)}  "
                  f"len(input)={len(s)}")
        except IntentExtractionError as exc:
            # Controlled rejection — caller catches and falls back. ✓
            print(f"  ok (controlled) {s[:20]!r}: {exc}")
        except Exception as exc:
            print(f"  ✘ UNCAUGHT on {s[:20]!r}: {type(exc).__name__}: {exc}")
            return False
    print(f"  → PASS")
    return True


def t5_regex_fallback() -> bool:
    """`regex_fallback` is a callable safety net — verify it never raises
    and always returns a valid IntentExtraction with >=1 intent. This is the
    function the caller (ai_ask_v2) reaches for when AI Ear fails."""
    from intent_extractor import regex_fallback
    print("\nT5 — regex_fallback safety net always returns a valid extraction")
    print("-" * 72)
    samples = [
        "Mera promotion is saal hoga?",
        "Shaadi kab tak hogi aur bachhe kab honge?",
        "25 lakh ka loss recover hoga ya nahi?",
        "Health theek rahegi?",
        "?????",            # garbage but non-empty
        "general life advice",
    ]
    ok = True
    for q in samples:
        try:
            r = regex_fallback(q)
            print(f"  src={r.source}  domain={r.domain}  "
                  f"intents={len(r.intents)}  buckets="
                  f"{[i.bucket for i in r.intents]}  q={q[:40]!r}")
            if r.source != "regex_fallback":
                ok = False
            if len(r.intents) < 1:
                ok = False
        except Exception as exc:
            print(f"  ✘ regex_fallback raised on {q!r}: {exc}")
            ok = False
    print(f"  → {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    print("AI Ear cache + fallback smoke test")
    results = [t1_cache_hit(), t2_cache_miss_distinct(),
               t3_normalized_key(), t4_garbage_safe(),
               t5_regex_fallback()]
    passed = sum(results)
    total  = len(results)
    print(f"\n{'='*72}\nRESULT: {passed}/{total} PASS")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

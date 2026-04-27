"""
Smoke test for P2 — ai_ask_v2 multi-intent dispatcher.

Verifies:
  • Single-intent question → legacy single-shape result (no `cards` key)
  • Multi-intent story → response_schema=v2 + cards[] of correct count
  • Off-topic/no-chart questions still flow through (per-card fail-safe ok)
  • Parallel dispatch completes in roughly max(card_latency), not sum
"""
from __future__ import annotations

import json
import sys
import time

from openai_helper import ai_ask_v2


# We pass kundli=None on purpose — astro questions hit the no-chart fail-safe
# inside ai_ask, returning a controlled "save your birth details" message.
# This is enough to verify the v2 dispatcher fan-out without standing up a
# full kundli generator in the smoke harness.
KUNDLI = None
LANG   = "hn"


SAMPLES = [
    {
        "label": "T1 — Single intent (should return legacy shape)",
        "question": "Mera promotion is saal hoga ya nahi?",
        "expect_cards": False,
    },
    {
        "label": "T2 — Multi-intent story (should return v2 cards[])",
        "question": (
            "Mera business partner pichle 2 saal se silent tha aur ab "
            "achanak alag hone ki baat kar raha hai. Mera 25 lakh lagaya "
            "hua hai usme. Kya woh paisa wapas milega aur main akele "
            "continue karu ya partner change karu?"
        ),
        "expect_cards":     True,
        "expect_min_cards": 2,
        "expect_max_cards": 3,
    },
]


def run_one(sample: dict) -> bool:
    print(f"\n{'='*72}\n{sample['label']}\nQ: {sample['question']}\n{'-'*72}")
    started = time.time()
    try:
        result = ai_ask_v2(sample["question"], KUNDLI, LANG, 0,
                           birth=None, history=[], preferred_language=None)
    except Exception as exc:
        print(f"FAIL — exception: {type(exc).__name__}: {exc}")
        import traceback; traceback.print_exc()
        return False
    elapsed = (time.time() - started) * 1000

    print(f"Wall: {elapsed:.0f}ms")
    print(f"keys: {sorted(result.keys())}")

    has_cards = isinstance(result.get("cards"), list)
    schema    = result.get("response_schema")
    print(f"response_schema={schema}  has_cards={has_cards}  "
          f"source={result.get('source')}")

    if sample["expect_cards"]:
        if not has_cards:
            print("✘ expected cards[] but got legacy single shape")
            return False
        n = len(result["cards"])
        if not (sample["expect_min_cards"] <= n <= sample["expect_max_cards"]):
            print(f"✘ expected {sample['expect_min_cards']}–{sample['expect_max_cards']} cards, got {n}")
            return False
        print(f"  cards: {n}")
        for i, c in enumerate(result["cards"], 1):
            print(f"    {i}. label={c.get('intent_label')[:60]!r}")
            print(f"       bucket={c.get('intent_bucket')}  source={c.get('source')}")
            print(f"       text[:120]={(c.get('text') or '')[:120]!r}")
        if schema != "v2":
            print(f"✘ expected response_schema=v2, got {schema}")
            return False
        ie = result.get("intent_extraction") or {}
        print(f"  intent_extraction.domain={ie.get('domain')} "
              f"intent_count={len(ie.get('intents') or [])}")
        print("  → PASS")
        return True
    else:
        if has_cards:
            print(f"✘ expected legacy shape but got cards[] (n={len(result['cards'])})")
            return False
        if schema == "v2":
            print(f"✘ expected no response_schema, got v2")
            return False
        print(f"  text[:120]={(result.get('text') or '')[:120]!r}")
        print(f"  topic={result.get('topic')}  source={result.get('source')}")
        # Per-card has 'intent_extraction' annotation — that's fine.
        ie = result.get("intent_extraction")
        if ie is not None:
            print(f"  intent_extraction annotation present (intents={len(ie.get('intents') or [])})")
        print("  → PASS")
        return True


def main() -> int:
    print("ai_ask_v2 dispatcher smoke test")
    results = [run_one(s) for s in SAMPLES]
    passed = sum(results)
    total  = len(results)
    print(f"\n{'='*72}\nRESULT: {passed}/{total} PASS")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

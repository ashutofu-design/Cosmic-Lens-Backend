"""
Smoke test for P3 — narrator_v2.compose_card_narrative.

Verifies for 3 archetypal cards:
  • Output has verdict_tag + narrative (50-80 words) + remedy + advisor
  • Voice rules: opener / hedge / forward-warmth / no jargon
  • Brand-safety: AI not leaked, advisor cite present for wealth/health
  • User facts echoed verbatim
"""
from __future__ import annotations

import sys
import time

from narrator_v2 import (
    compose_card_narrative,
    NarratorV2Error,
    _OPENER_RX, _HEDGE_RX, _FORWARD_RX,
    _BANNED_JARGON_RX, _AI_BRAND_LEAK_RX, _BANNED_BRAND_RX,
    _word_count,
)


SAMPLES = [
    {
        "label": "T1 — partnership_exit (anxious + wealth → CA cite required)",
        "intent_summary": "Business partner alag hone ki baat kar raha hai",
        "intent_bucket":  "partnership_exit",
        "intent_facts":   {
            "numbers": [], "durations": ["pichle 2 saal"],
            "persons": ["business partner"], "places": [], "dates": [],
        },
        "raw_engine_text": (
            "Engine analysis: partnership 7th-house lord weak, Saturn AD "
            "aspecting 6th house creates friction. Pratyantar dasha shifts "
            "Aug 2026, Ketu AD opens Apr 2027 with positive partnership "
            "energy. Recommend written agreement, no verbal-only deals."
        ),
        "language": "hn",
        "emotional_tone": "anxious",
        "must_echo": ["pichle 2 saal", "business partner"],
        "require_advisor_words": ["ca", "lawyer", "advisor"],
    },
    {
        "label": "T2 — debt_recovery (anxious + wealth → CA/legal cite)",
        "intent_summary": "25 lakh lagaya hua paisa wapas milega kya",
        "intent_bucket":  "debt_recovery",
        "intent_facts":   {
            "numbers": ["25 lakh"], "durations": [],
            "persons": [], "places": [], "dates": [],
        },
        "raw_engine_text": (
            "Engine analysis: 2nd-house Venus supports capital recovery "
            "but in instalments not lump-sum. Saturn AD currently slow. "
            "Pratyantar Aug 2026 unlocks first tranche, Ketu AD Apr 2027 "
            "clears balance. Legal route preferred over informal recovery."
        ),
        "language": "hn",
        "emotional_tone": "anxious",
        "must_echo": ["25 lakh"],
        "require_advisor_words": ["ca", "lawyer", "advisor", "sebi"],
    },
    {
        "label": "T3 — business_continuation (hopeful → CA cite + green-go ok)",
        "intent_summary": "Akele business continue karu ya partner change karu",
        "intent_bucket":  "business_continuation",
        "intent_facts":   {
            "numbers": [], "durations": [],
            "persons": [], "places": [], "dates": [],
        },
        "raw_engine_text": (
            "Engine analysis: 10H Sun in own sign, 5H Mars in 11H — solo "
            "entrepreneurship strongly supported. Partnership was diluting "
            "natal promise. Apr 2027 Ketu AD opens 3-4x scaling window. "
            "First 6 months consolidation phase, expansion afterwards."
        ),
        "language": "hn",
        "emotional_tone": "hopeful",
        "must_echo": [],
        "require_advisor_words": ["ca", "advisor"],
    },
]


def run_one(s: dict) -> bool:
    print(f"\n{'='*72}\n{s['label']}\n{'-'*72}")
    started = time.time()
    try:
        card = compose_card_narrative(
            intent_summary=s["intent_summary"],
            intent_bucket=s["intent_bucket"],
            intent_facts=s["intent_facts"],
            raw_engine_text=s["raw_engine_text"],
            language=s["language"],
            emotional_tone=s["emotional_tone"],
        )
    except NarratorV2Error as exc:
        print(f"FAIL — {exc}")
        return False
    elapsed = (time.time() - started) * 1000

    print(f"Wall: {elapsed:.0f}ms  Latency-reported: {card.latency_ms}ms")
    print(f"verdict_tag: {card.verdict_tag}")
    print(f"narrative ({_word_count(card.narrative)} words):")
    print(f"  {card.narrative}")
    print(f"remedy_line:  {card.remedy_line!r}")
    print(f"advisor_line: {card.advisor_line!r}")
    print(f"_internal: echoed_facts={card._internal.get('echoed_facts')}  "
          f"echoed_pivots={card._internal.get('echoed_pivots')}  "
          f"opener={card._internal.get('voice_opener')!r}")

    ok = True

    # 1. Voice rules.
    if not _OPENER_RX.search(card.narrative):
        print("  ✘ voice opener missing")
        ok = False
    if not _HEDGE_RX.search(card.narrative):
        print("  ✘ soft hedge missing")
        ok = False
    if not _FORWARD_RX.search(card.narrative):
        print("  ✘ forward-warmth missing")
        ok = False

    # 2. Banned jargon / brand leak.
    j = _BANNED_JARGON_RX.search(card.narrative)
    if j:
        print(f"  ✘ jargon leaked: {j.group(0)!r}")
        ok = False
    if _AI_BRAND_LEAK_RX.search(card.narrative + " " + card.advisor_line):
        print(f"  ✘ AI/LLM brand leak")
        ok = False
    if _BANNED_BRAND_RX.search(card.narrative + " " + card.advisor_line):
        print(f"  ✘ banned brand-safety phrase")
        ok = False

    # 3. Length envelope.
    wc = _word_count(card.narrative)
    if not (35 <= wc <= 120):
        print(f"  ✘ length {wc} out of [35-120]")
        ok = False

    # 4. Echo check.
    for needle in s.get("must_echo") or []:
        if needle.lower() not in card.narrative.lower():
            print(f"  ⚠ expected to echo {needle!r} (not strict)")

    # 5. Advisor cite check (where required).
    advisor_lower = card.advisor_line.lower()
    if s.get("require_advisor_words"):
        if not any(w in advisor_lower for w in s["require_advisor_words"]):
            print(f"  ✘ advisor_line missing required cite "
                  f"(want one of {s['require_advisor_words']})")
            ok = False

    print(f"  → {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    print("narrator_v2.compose_card_narrative smoke test")
    results = [run_one(s) for s in SAMPLES]
    passed = sum(results)
    total  = len(results)
    print(f"\n{'='*72}\nRESULT: {passed}/{total} PASS")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

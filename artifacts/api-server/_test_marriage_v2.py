"""
v2 test: single-call optimization + constraint-aware follow-up.

Checks:
  1. Single OpenAI call per request (validator-retry removed).
  2. Pre-baked answer's window/verdict/remedy survive the AI tone-polish.
  3. Constraint detector flips to next_alt_window on "uske baad batao".
"""
import sys, os, time, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kundli_engine        import calculate_kundli
from chart_intelligence   import analyze_chart
from marriage_engine      import (assess_marriage, extract_window_str,
                                  extract_alt_window_str, format_final_answer)
from openai_helper        import (ai_ask, _kp_calc, _detect_marriage_constraint)

BIRTH = {
    "name": "Test Devotee",
    "day": 15, "month": 6, "year": 1995,
    "hour": 2, "minute": 30, "ampm": "PM",
    "place": "Mumbai, India",
    "lat": 19.0760, "lon": 72.8777, "tz": 5.5,
}

# Patch openai client to count calls.
import openai_helper as oh
_orig_get_client = oh._get_client
_call_count = {"n": 0}
class _CountingClient:
    def __init__(self, real):
        self.real = real
        self.chat = self
        self.completions = self
    def create(self, **kw):
        _call_count["n"] += 1
        return self.real.chat.completions.create(**kw)
def _patched_client():
    real = _orig_get_client()
    if real is None: return None
    return _CountingClient(real)
oh._get_client = _patched_client


def banner(s):
    print("\n" + "═"*70 + f"\n {s}\n" + "═"*70)


def show(label, text):
    print(f"\n  ── {label} ──")
    for line in (text or "(empty)").splitlines():
        print("    " + line)


def main():
    banner("V2 — SINGLE-CALL + CONSTRAINT-AWARE")

    kundli = calculate_kundli(BIRTH)
    intel  = analyze_chart(kundli, BIRTH) or {}
    try:    kp = _kp_calc()(BIRTH)
    except: kp = {}
    v = assess_marriage(kundli, intel, kp, BIRTH)

    primary_str = extract_window_str(v)
    alt_str     = extract_alt_window_str(v)
    print(f"\n  primary window : \"{primary_str}\"")
    print(f"  alt window     : \"{alt_str}\"")
    print(f"  verdict        : {v.get('verdict')}")
    print(f"  remedy planet  : {v.get('remedy_for_planet')}")

    banner("Pre-baked answer (Hinglish, primary window) — Python only, no AI")
    print(format_final_answer(v, "hn", use_alt=False))

    banner("Pre-baked answer (Hinglish, ALT window) — Python only, no AI")
    print(format_final_answer(v, "hn", use_alt=True))

    # ── 1) Primary call: should be SINGLE OpenAI call ────────────────────────
    banner("TEST 1 — Primary question: \"meri shaadi kab hogi?\"")
    _call_count["n"] = 0
    t0 = time.time()
    r1 = ai_ask("Acharya ji, meri shaadi kab hogi?", kundli, lang="hn",
                birth=BIRTH, history=None, preferred_language=None)
    dt1 = time.time() - t0
    show("AI reply", r1.get("text"))
    txt1 = (r1.get("text") or "").lower()
    # "June 2026 to October 2026" OR Hinglish "June 2026 se October 2026"
    # — both are valid surface forms of the engine window.
    has_primary = (primary_str.lower() in txt1) or (
        re.sub(r"\bto\b", "se", primary_str.lower()) + " tak" in txt1
    ) or ("june 2026" in txt1 and "october 2026" in txt1)
    print(f"\n  → OpenAI calls    : {_call_count['n']}  "
          f"{'✓ PASS (single call)' if _call_count['n']==1 else '✗ FAIL'}")
    print(f"  → Latency         : {dt1:.2f}s")
    print(f"  → primary echoed  : {'✓ PASS' if has_primary else '✗ FAIL'}")

    # ── 2) Constraint follow-up: should use ALT window ───────────────────────
    banner("TEST 2 — Follow-up: \"uske baad batao, dusra time chahiye\"")
    constraint_q = "Acharya ji, uske baad batao — dusra time chahiye"
    detected = _detect_marriage_constraint(constraint_q, [])
    print(f"\n  constraint detected on Q: {'✓ YES' if detected else '✗ NO'}")
    # In real usage this Q always follows a marriage answer — pass that
    # history so topic-stickiness can flip topic to "marriage".
    history2 = [
        {"role": "user",      "content": "Acharya ji, meri shaadi kab hogi?"},
        {"role": "assistant", "content": r1.get("text") or ""},
    ]
    _call_count["n"] = 0
    t0 = time.time()
    r2 = ai_ask(constraint_q, kundli, lang="hn",
                birth=BIRTH, history=history2, preferred_language=None)
    dt2 = time.time() - t0
    show("AI reply", r2.get("text"))
    txt2 = (r2.get("text") or "").lower()
    has_alt = (alt_str.lower() in txt2) or (
        re.sub(r"\bto\b", "se", alt_str.lower()) + " tak" in txt2
    ) or ("january 2027" in txt2 and "june 2027" in txt2) if alt_str else True
    print(f"\n  → OpenAI calls    : {_call_count['n']}  "
          f"{'✓ PASS (single call)' if _call_count['n']==1 else '✗ FAIL'}")
    print(f"  → Latency         : {dt2:.2f}s")
    print(f"  → alt echoed      : {'✓ PASS' if has_alt else '✗ FAIL'}  "
          f"(alt = \"{alt_str or '(none)'}\")")

    # ── 2b) Hedge / uncertainty word check on BOTH replies ───────────────────
    banner("TEST 2b — Banned-hedging-word audit")
    HEDGE_WORDS = [
        "ho sakta hai", "ho sakti hai", "ho sakte hain", "sakega", "sakegi",
        "sakte hain", "sakti hain",  # generic
        "shayad", "lagta hai", "sambhavna",
        "around", "approximately", "approx", "roughly", "perhaps",
        " possibly ", "likely", "unlikely", "may be", "might be",
        "early 2026", "late 2026", "early 2027", "late 2027",
        "by the end of",
    ]
    def audit(label, txt):
        leaks = [h for h in HEDGE_WORDS if h.lower() in (txt or "").lower()]
        print(f"  {label}: {'✓ CLEAN' if not leaks else '✗ LEAKS: ' + ', '.join(leaks)}")
        return not leaks
    primary_clean = audit("Primary reply ", r1.get("text"))
    alt_clean     = audit("Alt reply     ", r2.get("text"))

    # ── 3) Constraint detector unit checks ───────────────────────────────────
    banner("TEST 3 — Constraint detector unit cases")
    cases = [
        ("meri shaadi kab hogi",                 False),
        ("uske baad batao",                      True),
        ("yeh time nahi chahiye",                True),
        ("next year batao",                      True),
        ("November 2026 nahi chahiye",           True),
        ("after this window please",             True),
        ("dusra time bata sakte hain",           True),
        ("haan bilkul",                          False),
    ]
    for q, want in cases:
        got = _detect_marriage_constraint(q, [])
        print(f"  {'✓' if got==want else '✗'}  \"{q}\"  "
              f"→ detected={got} (want={want})")

    # Summary
    banner("SUMMARY")
    print(f"  Single call           : {'✓' if _call_count['n']<=1 else '✗'}")
    print(f"  Primary window echoed : {'✓' if has_primary else '✗'}")
    print(f"  Alt window used       : {'✓' if has_alt else '✗'}")
    print(f"  Primary hedges clean  : {'✓' if primary_clean else '✗'}")
    print(f"  Alt hedges clean      : {'✓' if alt_clean else '✗'}")
    print(f"  Constraint detector   : {'✓' if detected else '✗'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

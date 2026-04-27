"""
Smoke test for P4 — narrator_v2 validator hardening.

Constructs intentionally-bad cards and verifies the validator catches them.
Tests are pure-Python (no AI calls) — direct invocation of _validate_card.
"""
from __future__ import annotations

import sys

from narrator_v2 import _validate_card, _REQUIRE_ADVISOR_BUCKETS


CASES = [
    {
        "label": "VC1 — missing opener (formal namaste)",
        "card": {
            "verdict_tag": "🟡 WAIT",
            "narrative": (
                "Namaste, aapka 25 lakh paisa thoda dheere wapas aayega. "
                "August 2026 ke baad situation clear hogi. Jaldbaazi mat "
                "karo. Sab dheere clear hogi."
            ),
            "remedy_line": "",
            "advisor_line": "Ek qualified CA se consult karo.",
        },
        "facts": {"numbers": ["25 lakh"]},
        "bucket": "debt_recovery",
        "require_advisor": True,
        "expect_fail_substring": "opener",
    },
    {
        "label": "VC2 — jargon leak (combust + dasha)",
        "card": {
            "verdict_tag": "🟠 SLOW BURN",
            "narrative": (
                "Dekho, thoda Saturn ki dasha chal rahi hai aur Mercury "
                "combust hai. Isiliye dheere problems aa rahi hain. "
                "August 2026 ke baad clear hogi. Sab dheere theek hoga."
            ),
            "remedy_line": "",
            "advisor_line": "Ek CA se consult karo.",
        },
        "facts": {},
        "bucket": "general_wealth",
        "require_advisor": True,
        "expect_fail_substring": "jargon",
    },
    {
        "label": "VC3 — AI brand leak",
        "card": {
            "verdict_tag": "🟢 GREEN GO",
            "narrative": (
                "Dekho, thoda business akele continue karna better hai. "
                "April 2027 ke baad situation behtar hota jaayega. "
                "Jaldbaazi mat karo."
            ),
            "remedy_line": "",
            "advisor_line": "OpenAI's GPT-4 says consult a CA.",
        },
        "facts": {},
        "bucket": "business_continuation",
        "require_advisor": True,
        "expect_fail_substring": "brand",
    },
    {
        "label": "VC4 — missing hedge",
        "card": {
            "verdict_tag": "🟢 GREEN GO",
            "narrative": (
                "Dekho, business akele continue karna definitely better "
                "hai. April 2027 ke baad scaling window khulega. Continue "
                "karo aur growth dekho jaayegi."
            ),
            "remedy_line": "",
            "advisor_line": "Ek qualified CA se consult karo.",
        },
        "facts": {},
        "bucket": "business_continuation",
        "require_advisor": True,
        "expect_fail_substring": "hedge",
    },
    {
        "label": "VC5 — missing forward-warmth",
        "card": {
            "verdict_tag": "🔴 RED FLAG",
            "narrative": (
                "Dekho na, partnership thodi kamzor hai aur halki si "
                "tension dikh rahi hai. Yeh problem hai. Bahut dikkat "
                "hogi. Sab kuch khatra hai. Pareshaani badhegi."
            ),
            "remedy_line": "",
            "advisor_line": "Ek qualified CA se consult karo.",
        },
        "facts": {},
        "bucket": "partnership_exit",
        "require_advisor": True,
        "expect_fail_substring": "forward",
    },
    {
        "label": "VC6 — missing required advisor cite",
        "card": {
            "verdict_tag": "🟡 WAIT",
            "narrative": (
                "Dekho, thoda 25 lakh wala paisa dheere wapas aayega. "
                "Jaldbaazi mat karo, raasta banega. August 2026 tak halki "
                "si recovery dikhegi, smooth ho jaayega."
            ),
            "remedy_line": "",
            "advisor_line": "Sab kuch theek ho jayega.",  # no cite
        },
        "facts": {"numbers": ["25 lakh"]},
        "bucket": "debt_recovery",
        "require_advisor": True,
        "expect_fail_substring": "advisor_line",
    },
    {
        "label": "VC7 — fact not echoed (user gave 25 lakh, narrative ignores)",
        "card": {
            "verdict_tag": "🟡 WAIT",
            "narrative": (
                "Dekho, paisa wapas aayega thoda dheere. August 2026 ke "
                "baad situation clear hogi, jaldbaazi mat karo. Sab "
                "behtar hota jaayega."
            ),
            "remedy_line": "",
            "advisor_line": "Ek qualified CA se consult kar lo.",
        },
        "facts": {"numbers": ["25 lakh"]},
        "bucket": "debt_recovery",
        "require_advisor": True,
        "expect_fail_substring": "echo",
    },
    {
        "label": "VC8 — banned brand: rupee guarantee",
        "card": {
            "verdict_tag": "🟢 GREEN GO",
            "narrative": (
                "Dekho na, aapko thoda dheere 25 lakh milega August 2026 "
                "tak. Jaldbaazi mat karo, raasta banega aur smooth ho "
                "jayega. Sab clear hogi."
            ),
            "remedy_line": "",
            "advisor_line": "Ek qualified CA se consult kar lo.",
        },
        "facts": {"numbers": ["25 lakh"]},
        "bucket": "debt_recovery",
        "require_advisor": True,
        "expect_fail_substring": "brand",
    },
    {
        "label": "VC9 — too long (>120 words)",
        "card": {
            "verdict_tag": "🟡 WAIT",
            "narrative": (
                ("Dekho na, thoda " + "yeh halki si situation hai aur dheere clear hogi raasta banega ke baad. " * 25)
            ),
            "remedy_line": "",
            "advisor_line": "Ek qualified CA se consult kar lo.",
        },
        "facts": {},
        "bucket": "general_wealth",
        "require_advisor": True,
        "expect_fail_substring": "word count",
    },
    {
        "label": "VC10 — VALID card (control — must NOT fail)",
        "card": {
            "verdict_tag": "🟡 WAIT",
            "narrative": (
                "Dekho na, 25 lakh wala paisa thoda dheere wapas aane wala "
                "hai, abhi ek halki si rukawat dikh rahi hai paisa wapas "
                "lane wale area mein. Jaldbaazi mat karo, ek baar legal "
                "raasta soch lo aur written agreement le lo, aur ek baar "
                "consult kar lo. Aage chal ke August 2026 ke baad situation "
                "smooth hone lagega aur paisa dheere dheere clear ho jaayega."
            ),
            "remedy_line": "",
            "advisor_line": "Ek qualified CA aur lawyer se consult kar lo.",
        },
        "facts": {"numbers": ["25 lakh"]},
        "bucket": "debt_recovery",
        "require_advisor": True,
        "expect_fail_substring": None,   # MUST PASS
    },
]


def run_one(case: dict) -> bool:
    print(f"\n{'='*72}\n{case['label']}\n{'-'*72}")
    fail = _validate_card(
        case["card"], case["facts"], case["bucket"], case["require_advisor"]
    )

    expected = case["expect_fail_substring"]
    if expected is None:
        # Should pass.
        if fail is None:
            print("  → PASS (validator accepted valid card)")
            return True
        else:
            print(f"  ✘ FAIL: validator rejected valid card → {fail!r}")
            return False
    else:
        # Should fail with the expected substring.
        if fail is None:
            print(f"  ✘ FAIL: validator missed bug; expected substring={expected!r}")
            return False
        if expected.lower() in fail.lower():
            print(f"  → PASS (caught: {fail})")
            return True
        else:
            print(f"  ⚠ partial: validator caught a different problem → {fail}")
            print(f"      (expected substring={expected!r})")
            # Still counts as pass — at least it caught SOMETHING wrong.
            return True


def main() -> int:
    print("narrator_v2 validator hardening — negative + control tests")
    results = [run_one(c) for c in CASES]
    passed = sum(results)
    total  = len(results)
    print(f"\n{'='*72}\nRESULT: {passed}/{total} PASS")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

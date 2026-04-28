"""Phase 4.5 — Narrative Mode regression suite.

Verifies that NARRATIVE_MODE=1 (default) produces flowing Hinglish prose
instead of the legacy V→R→T template (verdict badge / Window / Kya hoga
bullets / Upay / CA-SEBI cite).

These tests target the post-processing layer and contract installation —
they do NOT call OpenAI. The live regression in /tmp/test_ask_payload.py
exercises the full pipeline end-to-end.

Run:
    python -m pytest test_phase45_narrative.py -v
"""
from __future__ import annotations

import os
import re
import unittest


# Force narrative mode ON before importing the helper.
os.environ["NARRATIVE_MODE"] = "1"
import openai_helper as oh  # noqa: E402


class NarrativeModeFlagTests(unittest.TestCase):
    """The flag itself + downstream gates flip cleanly."""

    def test_flag_default_on(self):
        self.assertTrue(oh._NARRATIVE_MODE,
                        "NARRATIVE_MODE should default to True")

    def test_supertype_validator_returns_empty_in_narrative_mode(self):
        # PLANET_QUERY contract forbids dasha mention; in narrative mode
        # the validator must short-circuit and return [] regardless.
        text = "Saturn ki Mahadasha chal rahi hai abhi."
        violations = oh._validate_supertype_contract(text, "PLANET_QUERY")
        self.assertEqual(violations, [],
                         "Validator must no-op when NARRATIVE_MODE=1")

    def test_unified_narrator_contract_uses_narrative_body(self):
        contract = oh._build_unified_narrator_contract(
            "GENERAL_ANALYSIS", has_recovery_subask=False
        )
        # The narrative body must be installed and must require combo
        # reasoning. We don't assert "Verdict:" is absent — the surrounding
        # output discipline / safe-fallback prefixes are shared with legacy
        # mode and may mention the word in passing.
        self.assertIn("NARRATIVE_ANSWER", contract,
                      "Contract must install the narrative body")
        self.assertIn("MD-AD-PD COMBINATION", contract,
                      "Contract must include the 6-step reasoning method")


class DisclaimerStripTests(unittest.TestCase):
    """`_strip_narrative_disclaimers` removes advisor / doctor sentences."""

    def _strip(self, s: str) -> str:
        return oh._strip_narrative_disclaimers(s)

    def test_ca_sebi_advisor_sentence_removed(self):
        before = (
            "Abhi paisa flow hoga. "
            "Bade financial decisions ke liye CA ya SEBI-registered "
            "advisor se consult zaroor karein. "
            "Patience rakho."
        )
        after = self._strip(before)
        self.assertNotIn("CA", after)
        self.assertNotIn("SEBI", after)
        self.assertIn("paisa flow hoga", after)
        self.assertIn("Patience rakho", after)

    def test_qualified_doctor_sentence_removed(self):
        before = (
            "Health phase mixed hai. "
            "Qualified doctor se consult karein bina deri ke. "
            "Diet aur sleep maintain karo."
        )
        after = self._strip(before)
        self.assertNotIn("doctor", after.lower())
        self.assertIn("Health phase", after)
        self.assertIn("Diet aur sleep", after)

    def test_financial_advisor_sentence_removed(self):
        before = (
            "Investment ka window favorable hai. "
            "Bade investments ya loans lene se pehle CA/financial "
            "advisor se consult karein."
        )
        after = self._strip(before)
        self.assertNotIn("financial advisor", after.lower())
        self.assertNotIn("CA/", after)
        self.assertIn("Investment ka window favorable", after)

    def test_clean_text_unchanged(self):
        clean = (
            "Jupiter growth dena chahta hai, par Rahu confusion create "
            "kar raha hai. Sep 2028 ke baad situation better hogi."
        )
        self.assertEqual(self._strip(clean), clean.strip())

    def test_idempotent(self):
        before = "Abhi cautious raho. CA se consult karein."
        once = self._strip(before)
        twice = self._strip(once)
        self.assertEqual(once, twice)

    # ── False-positive guards (architect Round 1 finding #3) ───────────
    # Bare topical mentions of doctor / CA / advisor / consult inside
    # legitimate astro narration must NOT be stripped. The regex requires
    # the consult/salah/baat CTA pair AND the advisor/doctor noun in the
    # SAME sentence to fire.

    def test_career_doctor_yog_preserved(self):
        # Career-prediction sentence that mentions "doctor" as a profession.
        text = (
            "Saturn ke prabhav se aap doctor banne ka yog rakhte ho. "
            "Mahadasha 2030 tak strong rahegi."
        )
        out = self._strip(text)
        self.assertEqual(out, text.strip(),
                         "Career 'doctor banne ka yog' must NOT be stripped")

    def test_ca_profession_career_preserved(self):
        text = (
            "Mercury Antardasha mein CA ka practice strong chalega aur "
            "income badhegi."
        )
        out = self._strip(text)
        self.assertIn("CA ka practice", out,
                      "Career-mention 'CA ka practice' must survive")

    def test_bare_consult_word_preserved(self):
        # "consult" without the advisor/doctor noun in same sentence.
        text = "Saturn dasha mein cautious raho aur planning consult karke karo."
        out = self._strip(text)
        self.assertIn("planning consult karke", out,
                      "Bare 'consult' without advisor/doctor noun must survive")

    def test_advisor_profession_yog_preserved(self):
        text = (
            "Aapke chart mein advisor banne ka strong yog hai, Jupiter "
            "5th house mein hai."
        )
        out = self._strip(text)
        self.assertEqual(out, text.strip(),
                         "Profession 'advisor banne ka yog' must survive")

    # ── Architect Round 2 — legacy Rule #10 short-form coverage ────────
    # Bare "CA" + imperative "consult karein"/"salaah lein" was the most
    # common Rule #10 form. Must be stripped, but only when paired with
    # an imperative verb (career mentions like "CA ka practice" survive).

    def test_bare_ca_imperative_consult_stripped(self):
        text = (
            "Abhi planning karo. "
            "Qualified CA se consult karein bade decisions ke liye. "
            "Period stable rahega."
        )
        out = self._strip(text)
        self.assertNotIn("CA", out)
        self.assertIn("planning karo", out)
        self.assertIn("Period stable", out)

    def test_financial_planner_salaah_stripped(self):
        text = (
            "Investment ka phase favorable hai. "
            "Financial planner ki salaah zaroor lein. "
            "Patience rakho."
        )
        out = self._strip(text)
        self.assertNotIn("planner", out.lower())
        self.assertIn("Investment ka phase", out)
        self.assertIn("Patience rakho", out)

    def test_financial_planner_narrative_preserved(self):
        # Architect Round 3 — Boilerplate 5 false-positive guard.
        # Non-imperative narrative sentence that mentions "financial
        # planner" as predictive context (NOT as a disclaimer CTA) must
        # survive — the imperative verb (karein/lein/zaroor/...) is the
        # discriminator.
        text = (
            "Aap financial planner ki salaah se long-term discipline "
            "bana paoge."
        )
        out = self._strip(text)
        self.assertEqual(out, text.strip(),
                         "Predictive 'financial planner ki salaah se' "
                         "narrative must NOT be stripped (no imperative)")

    def test_career_ca_practice_still_preserved(self):
        # Regression-guard for the Round 1 false-positive concern: even
        # with the new Boilerplate 4 (bare CA + consult CTA), career
        # mentions like "CA ka practice" must NOT be stripped because
        # they don't carry the imperative consult verb.
        text = (
            "Mercury Antardasha mein CA ka practice strong chalega. "
            "CA ban ke independent kaam start kar sakte ho."
        )
        out = self._strip(text)
        self.assertIn("CA ka practice", out)
        self.assertIn("CA ban ke", out)

    # ── Architect Round 4 — crisis safety preservation ────────────────
    # When the text contains crisis/mental-health markers (helpline number,
    # iCall, Vandrevala, "aap akele nahi hain", suicid*, self-harm), the
    # entire strip is skipped. The doctor-cite + helpline block injected
    # by the health crisis safety net is non-negotiable and must survive.

    def test_crisis_helpline_preserves_doctor_cite(self):
        text = (
            "Aapka chart abhi heavy phase mein hai. "
            "Qualified doctor se zaroor consult karein — cosmic guidance "
            "medical diagnosis ya treatment ka vikalp nahi hai. "
            "Mental health support ke liye free helplines: iCall "
            "(9152987821) aur Vandrevala Foundation (1860-2662-345). "
            "Aap akele nahi hain."
        )
        out = self._strip(text)
        self.assertIn("Qualified doctor se zaroor consult karein", out,
                      "Crisis-path doctor cite must survive")
        self.assertIn("iCall", out, "Helpline must survive")
        self.assertIn("Vandrevala", out, "Helpline must survive")
        self.assertIn("Aap akele nahi hain", out)

    def test_crisis_marker_alone_disables_strip(self):
        # Even if there's a normal CA-disclaimer in the same block, the
        # presence of any crisis marker disables the strip wholesale —
        # safer to keep one extra sentence than risk losing the safety
        # block.
        text = (
            "Mental health support ke liye iCall (9152987821) helpline "
            "available hai. CA advisor se consult karein financial "
            "matters ke liye."
        )
        out = self._strip(text)
        self.assertEqual(out, text.strip(),
                         "Any crisis marker must skip strip entirely")

    def test_suicide_variants_preserve_doctor_cite(self):
        # Architect Round 5 finding — bare `suicid\b` only matched the rare
        # token "suicid"; real-world variants (suicide / suicidal /
        # suicidality / suicides) bypassed the crisis guard.
        cases = [
            ("Aap suicidal feel kar rahe ho. Qualified doctor se "
             "consult karein.", "suicidal"),
            ("Suicide thoughts aa rahe hain. Qualified doctor se "
             "consult karein bina deri ke.", "Suicide"),
            ("Suicidality dikh rahi hai chart mein. Qualified doctor "
             "se consult karein.", "Suicidality"),
        ]
        for text, marker in cases:
            with self.subTest(marker=marker):
                out = self._strip(text)
                self.assertIn("Qualified doctor", out,
                              f"Crisis variant '{marker}' must preserve "
                              "doctor cite")
                self.assertEqual(out, text.strip(),
                                 f"Crisis variant '{marker}' must skip "
                                 "strip entirely")

    def test_self_harm_variants_preserve_doctor_cite(self):
        cases = [
            "Self-harm thoughts aa rahe hain. Qualified doctor se consult karein.",
            "Self harm ka risk hai. Qualified doctor se consult karein.",
            "Khud ko nuksaan pahunchane ka man hai. Doctor se consult karein.",
        ]
        for text in cases:
            with self.subTest(text=text[:30]):
                out = self._strip(text)
                self.assertIn("octor", out,
                              "Doctor cite must survive when self-harm "
                              "marker is present")

    def test_non_crisis_disclaimer_still_strips(self):
        # Sanity-check the gate: pure-disclaimer text without crisis
        # markers MUST still be stripped (proves the gate isn't always-on).
        text = (
            "Investment phase favorable hai. "
            "Qualified CA advisor se consult karein. "
            "Patience rakho."
        )
        out = self._strip(text)
        self.assertNotIn("advisor", out.lower())
        self.assertIn("Investment phase", out)
        self.assertIn("Patience rakho", out)

    def test_doctor_visit_in_health_narrative_preserved(self):
        # Astro-style narration that mentions visiting a doctor as a
        # PROBABILITY (not a mandatory disclaimer CTA).
        text = (
            "Saturn aur Mars yuti hone ki wajah se chot ya operation ka "
            "yog ban raha hai, doctor ke paas visit zaroori ho sakti hai."
        )
        out = self._strip(text)
        # "doctor ke paas visit" is borderline — it COULD trigger the
        # broader doctor+visit pattern. Verify the rest of the prediction
        # (Saturn aur Mars yuti) survives untouched.
        self.assertIn("Saturn aur Mars yuti", out,
                      "Astro-prediction context must survive even if "
                      "the doctor-visit clause is stripped")


class ScrubBrandToneIntegrationTests(unittest.TestCase):
    """`_scrub_brand_tone` invokes disclaimer strip when NARRATIVE_MODE=1."""

    def test_scrub_chains_disclaimer_strip(self):
        # Use the actual legacy boilerplate format ("CA advisor se consult
        # karein") — narrowed regex deliberately requires the
        # advisor/consultant/professional noun, so bare "Qualified CA"
        # alone won't match (it's treated as a career mention).
        text = (
            "Abhi Rahu antardasha chal raha hai. "
            "Qualified CA advisor se consult karein bade financial "
            "decisions ke liye. "
            "Patience rakho aur planning karo."
        )
        out = oh._scrub_brand_tone(text)
        self.assertNotIn("advisor", out.lower())
        self.assertIn("Rahu antardasha", out)
        self.assertIn("Patience rakho", out)


class TruthFactsPDExtractionTests(unittest.TestCase):
    """`_build_truth_facts` should populate `current_pd` when chart has it."""

    def test_pd_extracted_from_dasha_tree(self):
        # `_build_truth_facts` walks the `dashas` list (not the chart's
        # legacy `vimshottariDasha` field) by today's date to populate
        # MD/AD/PD. We pin the PD window around real today (Apr 2026).
        from datetime import datetime
        today_iso = datetime.utcnow().strftime("%Y-%m-%d")

        kundli = {
            "dashas": [
                {
                    "planet": "Rahu",
                    "startDate": "2026-01-03",
                    "endDate":   "2044-01-03",
                    "subDashas": [
                        {
                            "planet": "Rahu",
                            "startDate": "2026-01-03",
                            "endDate":   "2028-09-15",
                            "subDashas": [
                                {"planet":    "Jupiter",
                                 "startDate": "2026-01-03",
                                 "endDate":   "2026-12-31"},
                                {"planet":    "Saturn",
                                 "startDate": "2026-12-31",
                                 "endDate":   "2027-09-30"},
                            ],
                        },
                    ],
                },
            ],
        }
        facts = oh._build_truth_facts(kundli)
        self.assertIn("current_pd", facts)
        self.assertIsNotNone(
            facts["current_pd"],
            f"current_pd should be populated for today={today_iso}",
        )
        self.assertEqual(facts["current_pd"]["planet"], "jupiter")


if __name__ == "__main__":
    unittest.main(verbosity=2)

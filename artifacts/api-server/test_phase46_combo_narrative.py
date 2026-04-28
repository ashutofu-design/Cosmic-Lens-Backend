"""Phase 4.6 — Combo Synthesis Hardening tests.

Verifies the structural fixes that follow user feedback (live screenshot,
Apr 28 2026): the love narrative answer was "ek dam bekar" because:
  1. love/career/marriage/health verdict-block injectors were dumping the
     full structured engine block + heavy "narrate verbatim" rules,
     forcing planet-by-planet enumeration.
  2. _NARRATIVE_NARRATOR_BODY didn't ban enumeration / preamble / KP
     citation / topic-pivot.
  3. Rule N (line ~2926) MANDATED a "KP paddhati se bhi {N}th cusp ka
     sub-lord {planet}…" citation for H1/H2/H5/H7/H10/H11.

Phase 4.5 only fixed (1) for wealth. Phase 4.6 finishes the job for love /
career / marriage / health, hardens the body, and gates Rule N to advisory.
"""
import os
import re
import unittest

os.environ.setdefault("NARRATIVE_MODE", "1")
os.environ.setdefault("OPENAI_API_KEY", "test-stub-key")

import openai_helper as oh  # noqa: E402


class Phase46NarratorBodyDiscipline(unittest.TestCase):
    """Body must hard-ban enumeration / preamble / KP / topic-pivot."""

    def setUp(self):
        self.body = oh._NARRATIVE_NARRATOR_BODY

    def test_body_bans_enumeration_pattern(self):
        # Body must give the model a BAD vs GOOD example so it knows
        # planet-by-planet listing is wrong and FUSED combo is right.
        self.assertIn("BAD (enumeration / report)", self.body)
        self.assertIn("GOOD (fused combo verdict)", self.body)

    def test_body_bans_preamble_starters(self):
        # The user's screenshot opened with "Seedhi baat —" — that is a
        # report-style preamble and must be banned.
        self.assertIn("NO PREAMBLE", self.body)
        for opener in ["Seedhi baat", "Dekho", "Sun lo", "Bhai"]:
            self.assertIn(opener, self.body,
                          f"Body must explicitly list banned opener "
                          f"'{opener}'")

    def test_body_bans_kp_method_namedrops(self):
        # User's screenshot had "KP paddhati se bhi 7th cusp ka sub-lord
        # Sun" — surface citation of method names must be banned in
        # narrative mode.
        for phrase in [
            "KP paddhati",
            "Cuspal sub-lord",
            "D9 navamsa",
            "Upapada Lagna",
            "Darakaraka",
            "Vimshottari",
            "Jaimini",
        ]:
            self.assertIn(phrase, self.body,
                          f"Body must explicitly list banned method "
                          f"namedrop '{phrase}'")

    def test_body_bans_topic_pivot(self):
        # Love → marriage drift was the structural fault in the user's
        # screenshot. Body must explicitly list each topic and what NOT
        # to drift into.
        self.assertIn("TOPIC FIDELITY", self.body)
        self.assertIn("LOVE", self.body)
        self.assertIn("CAREER", self.body)
        self.assertIn("WEALTH", self.body)
        self.assertIn("MARRIAGE", self.body)

    def test_body_includes_concrete_chatgpt_pattern_example(self):
        # User pointed to ChatGPT's exact phrasing as the target shape.
        # Body must include a near-verbatim example so the model has a
        # template to mirror.
        self.assertIn("Jupiter–Rahu–Mars phase", self.body)
        self.assertIn("attraction aur", self.body)
        # Source wraps "clarity\n       aur patience" across a newline
        # in the example block; check the contiguous halves separately.
        self.assertIn("clarity", self.body)
        self.assertIn("patience ke bina tikega nehi", self.body)


class Phase46VerdictBlockInjectorBypasses(unittest.TestCase):
    """Each per-topic verdict-block injector must have a NARRATIVE_MODE
    bypass branch that emits the slim 'FACTS — narrate as fused combo'
    header instead of the heavy 'NARRATOR OVERRIDE' that demands
    verbatim copying."""

    def setUp(self):
        with open(oh.__file__, "r", encoding="utf-8") as fh:
            self.src = fh.read()

    def _assert_narrative_branch(self, block_var: str, fact_label: str,
                                 banned_phrase: str):
        # The narrative-mode branch is `if {block} and _NARRATIVE_MODE:`
        # followed by an msgs.append using the slim FACT header.
        narrative_pattern = re.compile(
            rf"if {re.escape(block_var)} and _NARRATIVE_MODE:"
        )
        self.assertTrue(narrative_pattern.search(self.src),
                        f"{block_var} must have narrative-mode branch "
                        f"(`if {block_var} and _NARRATIVE_MODE:`)")
        self.assertIn(fact_label, self.src,
                      f"{block_var} narrative-mode branch must use the "
                      f"slim '{fact_label}' header")
        # The banned heavy phrase must STILL exist in the file (in the
        # `elif` legacy branch) — proves both branches coexist for
        # NARRATIVE_MODE=0 reversibility.
        self.assertIn(banned_phrase, self.src,
                      f"Legacy override path must remain for "
                      f"{block_var} (NARRATIVE_MODE=0 fallback)")

    def test_love_verdict_block_has_narrative_bypass(self):
        self._assert_narrative_branch(
            "love_verdict_block",
            "LOVE FACTS (engine-locked ground truth",
            "🔒 LOVE NARRATOR OVERRIDE",
        )

    def test_career_verdict_block_has_narrative_bypass(self):
        self._assert_narrative_branch(
            "career_verdict_block",
            "CAREER FACTS (engine-locked ground truth",
            "🔒 CAREER NARRATOR OVERRIDE",
        )

    def test_marriage_verdict_block_has_narrative_bypass(self):
        self._assert_narrative_branch(
            "marriage_verdict_block",
            "MARRIAGE FACTS (engine-locked ground truth",
            "TURN-LEVEL OVERRIDE — MARRIAGE NARRATOR MODE",
        )

    def test_health_verdict_block_has_narrative_bypass(self):
        self._assert_narrative_branch(
            "health_verdict_block",
            "HEALTH FACTS (engine-locked ground truth",
            "🔒 HEALTH NARRATOR OVERRIDE",
        )

    def test_wealth_verdict_block_keeps_phase45_bypass(self):
        # Phase 4.5 already shipped this — make sure the regression
        # doesn't undo it.
        self._assert_narrative_branch(
            "wealth_verdict_block",
            "WEALTH FACTS (engine-locked ground truth",
            "🔒 WEALTH NARRATOR OVERRIDE",
        )


class Phase46TopicFidelityHeaders(unittest.TestCase):
    """Each narrative-mode injector must explicitly call out 'TOPIC
    FIDELITY' so the model doesn't pivot away from the user's actual
    question (the user's screenshot drifted from LOVE → marriage)."""

    def setUp(self):
        with open(oh.__file__, "r", encoding="utf-8") as fh:
            self.src = fh.read()

    def test_love_branch_says_no_marriage_pivot(self):
        # The phrase must appear within the love narrative-mode branch.
        love_branch_start = self.src.find("LOVE FACTS (engine-locked")
        love_branch_end = self.src.find("elif love_verdict_block",
                                       love_branch_start)
        self.assertGreater(love_branch_end, love_branch_start,
                           "love narrative branch boundaries not found")
        love_branch = self.src[love_branch_start:love_branch_end]
        self.assertIn("TOPIC FIDELITY", love_branch)
        self.assertIn("Do NOT pivot to MARRIAGE analysis", love_branch)

    def test_career_branch_says_no_pivot(self):
        career_branch_start = self.src.find("CAREER FACTS (engine-locked")
        career_branch_end = self.src.find("elif career_verdict_block",
                                          career_branch_start)
        self.assertGreater(career_branch_end, career_branch_start)
        career_branch = self.src[career_branch_start:career_branch_end]
        self.assertIn("TOPIC FIDELITY", career_branch)
        self.assertIn("Do NOT pivot to", career_branch)


class Phase46RuleNNarrativeGate(unittest.TestCase):
    """Rule N (KP MANDATORY citation) must be downgraded to ADVISORY
    when NARRATIVE_MODE is on so the model isn't forced to cite
    'KP paddhati se bhi {N}th cusp ka sub-lord {planet}…'."""

    def setUp(self):
        with open(oh.__file__, "r", encoding="utf-8") as fh:
            self.src = fh.read()

    def test_rule_n_gate_block_present(self):
        self.assertIn(
            "Phase 4.6 — RULE N (KP MANDATORY citation) NARRATIVE-MODE GATE",
            self.src,
            "Rule N narrative-mode gate must be present in the prompt-"
            "build path")

    def test_advisory_replacement_text_exists(self):
        self.assertIn(
            "🛡️ KP CROSS-CHECK (Rule N — NARRATIVE-MODE: ADVISORY only)",
            self.src,
        )

    def test_gate_only_fires_in_narrative_mode(self):
        # The gate must be `if _NARRATIVE_MODE and …`, never unconditional.
        self.assertIn(
            "if _NARRATIVE_MODE and \"🛡️ KP CROSS-CHECK (Rule N — MANDATORY citation)\" in system:",
            self.src,
        )


class Phase46HealthCrisisSafetyPreserved(unittest.TestCase):
    """Health narrative-mode bypass MUST preserve crisis-safety for
    mental_health / suicide / self-harm buckets — never strip the
    helpline / qualified-doctor cite."""

    def setUp(self):
        with open(oh.__file__, "r", encoding="utf-8") as fh:
            self.src = fh.read()
        health_start = self.src.find("HEALTH FACTS (engine-locked")
        health_end = self.src.find("elif health_verdict_block",
                                   health_start)
        self.health_branch = self.src[health_start:health_end]

    def test_health_branch_preserves_crisis_cite_rule(self):
        # Substrings chosen to NOT span Python string-literal line
        # continuations in the source file (the source uses adjacent
        # implicit-concat splits like "qualified-"\n"doctor").
        self.assertIn("CRISIS-SAFETY (mandatory, never strip)",
                      self.health_branch)
        self.assertIn("mental_health bucket", self.health_branch)
        self.assertIn("qualified-", self.health_branch)
        self.assertIn("mental-health-helpline", self.health_branch)

    def test_health_branch_preserves_surgery_safety(self):
        self.assertIn("never tell user to skip surgery",
                      self.health_branch)

    def test_health_branch_preserves_addiction_dignity(self):
        self.assertIn("preserve self-worth", self.health_branch)
        # source splits this phrase across two adjacent string literals;
        # use the half that's contiguous.
        self.assertIn("never blame chart", self.health_branch)
        self.assertIn("recommend professional support",
                      self.health_branch)

    def test_health_branch_preserves_longevity_safety(self):
        # source has "never predict death / specific "\n"year-of-death"
        # — the contiguous portion is "never predict death".
        self.assertIn("never predict death", self.health_branch)
        self.assertIn("year-of-death", self.health_branch)


class Phase46BackwardsCompatibility(unittest.TestCase):
    """Setting NARRATIVE_MODE=0 must revert all four injectors to their
    legacy heavy 'NARRATOR OVERRIDE' shape (Phase 4.4 behavior)."""

    def setUp(self):
        with open(oh.__file__, "r", encoding="utf-8") as fh:
            self.src = fh.read()

    def test_legacy_love_override_still_reachable(self):
        self.assertIn("elif love_verdict_block:", self.src)
        self.assertIn("🔒 LOVE NARRATOR OVERRIDE", self.src)

    def test_legacy_career_override_still_reachable(self):
        self.assertIn("elif career_verdict_block:", self.src)
        self.assertIn("🔒 CAREER NARRATOR OVERRIDE", self.src)

    def test_legacy_marriage_override_still_reachable(self):
        self.assertIn("elif marriage_verdict_block:", self.src)
        self.assertIn("TURN-LEVEL OVERRIDE — MARRIAGE NARRATOR MODE",
                      self.src)

    def test_legacy_health_override_still_reachable(self):
        self.assertIn("elif health_verdict_block:", self.src)
        self.assertIn("🔒 HEALTH NARRATOR OVERRIDE", self.src)


if __name__ == "__main__":
    unittest.main(verbosity=2)

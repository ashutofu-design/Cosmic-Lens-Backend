"""Phase 5.9 — DOSH_FACTS block tests.

Mirrors the Phase 5.8 marriage/wealth test structure. Verifies:
  * regex routing (English / Hindi / Hinglish / Devanagari)
  * formatter output shape (clean lowercase keys, no rule prose)
  * defensive handling of malformed engine output
  * extractor routing precedence
  * full extractor round-trips through `_phase50_extract_verdict_facts`

Engine is `dosh_engine.analyze_doshas()` which returns:
  {
    "total_dosh": int, "active_count": int, "mild_count": int,
    "none_count": int,
    "dosh_list": [
      {"key", "name", "name_hindi", "icon",
       "status": "Active"|"Mild"|"None",
       "headline", "description", "remedies": [...], "planet_note"},
      ...
    ]
  }
"""
import unittest

import openai_helper as oh


# ──────────────────────────── Fixtures ────────────────────────────


def _dosh_obj_active_manglik() -> dict:
    """One active manglik, two mild, six clear — typical chart."""
    return {
        "total_dosh": 3,
        "active_count": 1,
        "mild_count": 2,
        "none_count": 6,
        "dosh_list": [
            {"key": "manglik", "name": "Manglik Dosha",
             "name_hindi": "मांगलिक दोष", "icon": "🔥",
             "status": "Active",
             "headline": "Mars in 7th house from Lagna",
             "description": "Long classical description...",
             "remedies": ["Mangal mantra", "Hanuman puja"],
             "planet_note": "Mars in 7H Sagittarius"},
            {"key": "kaal_sarp", "name": "Kaal Sarp Yoga",
             "name_hindi": "काल सर्प योग", "icon": "🐍",
             "status": "Mild",
             "headline": "Partial Rahu-Ketu axis",
             "description": "...", "remedies": ["Naga puja"],
             "planet_note": "Rahu 8H, Ketu 2H"},
            {"key": "sade_sati", "name": "Sade Sati",
             "name_hindi": "साढ़े साती", "icon": "🪐",
             "status": "Mild",
             "headline": "Saturn transiting 12th from Moon",
             "description": "...", "remedies": ["Shani mantra"],
             "planet_note": "Saturn in Aries"},
            {"key": "pitru_dosh", "name": "Pitru Dosha",
             "name_hindi": "पितृ दोष", "icon": "🕉️",
             "status": "None",
             "headline": "No affliction", "description": "",
             "remedies": [], "planet_note": ""},
            {"key": "guru_chandal", "name": "Guru Chandal Yoga",
             "name_hindi": "गुरु चांडाल योग", "icon": "⚡",
             "status": "None", "headline": "No affliction",
             "description": "", "remedies": [], "planet_note": ""},
            {"key": "kemadruma", "name": "Kemadruma Yoga",
             "name_hindi": "केमद्रुम योग", "icon": "🌑",
             "status": "None", "headline": "Moon supported by adjacent planets",
             "description": "", "remedies": [], "planet_note": ""},
            {"key": "vish_yog", "name": "Vish Yoga",
             "name_hindi": "विष योग", "icon": "🧪",
             "status": "None", "headline": "No affliction",
             "description": "", "remedies": [], "planet_note": ""},
            {"key": "angarak", "name": "Angarak Yoga",
             "name_hindi": "अंगारक योग", "icon": "🔴",
             "status": "None", "headline": "No affliction",
             "description": "", "remedies": [], "planet_note": ""},
            {"key": "grahan", "name": "Grahan Dosha",
             "name_hindi": "ग्रहण दोष", "icon": "🌒",
             "status": "None", "headline": "No affliction",
             "description": "", "remedies": [], "planet_note": ""},
        ],
    }


def _dosh_obj_all_clear() -> dict:
    return {
        "total_dosh": 0, "active_count": 0, "mild_count": 0,
        "none_count": 9,
        "dosh_list": [
            {"key": k, "name": k.title(), "name_hindi": "",
             "icon": "", "status": "None", "headline": "Clear",
             "description": "", "remedies": [], "planet_note": ""}
            for k in ["manglik", "kaal_sarp", "sade_sati", "pitru_dosh",
                      "guru_chandal", "kemadruma", "vish_yog", "angarak",
                      "grahan"]
        ],
    }


# ─────────────────────────── Detector ────────────────────────────


class TestPhase59IsDoshQuestion(unittest.TestCase):

    def test_english_dosha(self):
        # Coverage = the 14 doshas DOSH_CONFIGS actually computes.
        for q in [
            "Do I have any doshas?",
            "Am I manglik?",
            "Mangal dosh check karo",
            "Is there kaal sarp dosha?",
            "pitru dosh hai?",
            "guru chandal yoga check",
            "any kemadruma?",
            "vish yog hai?",
            "angarak dosh?",
            "grahan dosh check",
            "daridra dosh present?",
            "shrapit dosh check",
            "sakat yog hai?",
            "putra dosh present?",
            "gandanta dosh hai?",
            "punar phoo dosh?",
        ]:
            self.assertTrue(oh._phase59_is_dosh_question(q),
                            f"should match: {q!r}")

    def test_hinglish_variants(self):
        for q in [
            "Mujhe manglik hai?",
            "Mera mangalik dosha kaisa hai?",
            "Kalsarp yog hai mere kundli me?",
            "Kaal sarpa dosha?",
            "Pitra dosh ka upay batao",
            "Gurchandal yog kya hai?",
            "Mere kundli me kitne dosh hain?",
            "punar-phoo dosh hai?",
            "shakat yog kya hai?",
            "santaan dosh check kar",
        ]:
            self.assertTrue(oh._phase59_is_dosh_question(q),
                            f"should match: {q!r}")

    def test_devanagari(self):
        for q in [
            "क्या मुझे मांगलिक दोष है?",
            "काल सर्प योग है क्या?",
            "पितृ दोष का उपाय बताइए",
            "केमद्रुम योग है?",
            "दरिद्र योग है?",
            "श्रापित दोष है?",
        ]:
            self.assertTrue(oh._phase59_is_dosh_question(q),
                            f"should match: {q!r}")

    def test_engine_uncovered_keywords_must_not_match(self):
        """Phase 5.9 hard rule: regex must NOT match phenomena the
        dosh_engine doesn't compute. Otherwise injecting DOSH_FACTS
        without that entry causes the LLM to invent facts.

        Sade-sati specifically — a transit-based phenomenon NOT in
        DOSH_CONFIGS. Live trace at Phase 5.9 v1 confirmed the hallu.

        Overmatch vectors caught by architect at v2 review (the bare
        `\\bdosh\\b` token previously matched these and re-introduced
        the leak): sade-sati-dosh, nadi-dosh, kalatra-dosh.
        """
        for q in [
            # Sade-sati family (transit, not in engine)
            "Mera sade-sati chal raha hai kya?",
            "Sade sati end kab hogi?",
            "Sadesati kab khatam hogi?",
            "साढ़े साती कब खत्म होगी?",
            "shani sade sati ka upay",
            # Architect-flagged overmatch via bare `dosh`
            "Mera sade sati dosh hai kya?",
            "Is there nadi dosh?",
            "Nadi dosh check karo",
            "Kalatra dosh hai mere kundli mein?",
            "Bhakoot dosh check",
        ]:
            self.assertFalse(oh._phase59_is_dosh_question(q),
                             f"engine doesn't cover this — must NOT "
                             f"match: {q!r}")

    def test_unrelated_questions_do_not_match(self):
        for q in [
            "Mera marriage kab hoga?",
            "Kitne dhan yog hain?",
            "Career kaisa rahega?",
            "Mera health kaisa hai?",
            "What is my lagna?",
            "",
            "    ",
        ]:
            self.assertFalse(oh._phase59_is_dosh_question(q),
                             f"should NOT match: {q!r}")

    def test_devanagari_bare_roots_alone_must_not_match(self):
        """Architect-flagged hardening: bare Devanagari roots like
        दरिद्र (poor) and शकट (cart) are common Hindi words. Without
        a योग / दोष suffix they must NOT trigger DOSH_FACTS injection.
        """
        for q in [
            "मैं दरिद्र हूं",            # "I am poor" — generic prose
            "वह बहुत दरिद्र है",          # "He is very poor"
            "शकट का पहिया टूट गया",      # "The wagon's wheel broke"
        ]:
            self.assertFalse(oh._phase59_is_dosh_question(q),
                             f"bare Devanagari root must NOT match: {q!r}")
        # …but with the योग / दोष suffix, they DO match (engine covers them).
        for q in ["क्या मेरे चार्ट में दरिद्र योग है?",
                  "शकट दोष है क्या?"]:
            self.assertTrue(oh._phase59_is_dosh_question(q),
                            f"with योग/दोष suffix, must match: {q!r}")

    def test_defensive_against_non_string(self):
        for x in [None, 123, [], {}, object()]:
            self.assertFalse(oh._phase59_is_dosh_question(x),
                             f"should defensively reject: {x!r}")


# ─────────────────────────── Formatter ───────────────────────────


class TestPhase59FormatDoshFactsBlock(unittest.TestCase):

    def test_clean_block_for_active_manglik(self):
        out = oh._phase59_format_dosh_facts_block(_dosh_obj_active_manglik())
        self.assertTrue(out.startswith("DOSH_FACTS:"))
        self.assertIn("  - total_present: 3", out)
        self.assertIn("  - active_count: 1", out)
        self.assertIn("  - mild_count: 2", out)
        self.assertIn("  - none_count: 6", out)
        self.assertIn("  - per_dosha:", out)
        # Active entry: inline status + headline + planet_note
        self.assertIn(
            "    - Manglik Dosha: active — Mars in 7th house from Lagna "
            "(planet_note: Mars in 7H Sagittarius)",
            out,
        )
        # Mild entries: inline status
        self.assertIn(
            "    - Kaal Sarp Yoga: mild — Partial Rahu-Ketu axis",
            out,
        )
        self.assertIn(
            "    - Sade Sati: mild — Saturn transiting 12th from Moon",
            out,
        )
        # Absent entries: inline `absent` label, no headline noise
        self.assertIn("    - Pitru Dosha: absent", out)
        self.assertIn("    - Guru Chandal Yoga: absent", out)
        self.assertIn("    - Vish Yoga: absent", out)
        # Old bucket-header schema must NOT appear
        for forbidden in ["  - active:\n", "  - mild:\n", "  - clear:"]:
            self.assertNotIn(forbidden, out)

    def test_all_clear_chart(self):
        out = oh._phase59_format_dosh_facts_block(_dosh_obj_all_clear())
        self.assertIn("  - total_present: 0", out)
        self.assertIn("  - active_count: 0", out)
        self.assertIn("  - mild_count: 0", out)
        self.assertIn("  - none_count: 9", out)
        self.assertIn("  - per_dosha:", out)
        # Every dosha is `absent` — count the lines
        absent_lines = [ln for ln in out.split("\n")
                        if ln.endswith(": absent")]
        self.assertEqual(len(absent_lines), 9,
                         f"expected 9 absent lines, got {len(absent_lines)}: "
                         f"{absent_lines}")
        # Old "and N more" overflow must NOT appear (we list all now)
        self.assertNotIn("... and", out)

    def test_no_rule_prose_or_remedies_leak(self):
        """DOSH_FACTS must NOT leak narrator instructions or remedies.

        Remedies are intentionally OUT of scope for Phase 5.9 — they
        belong in a separate REMEDIES block.
        """
        out = oh._phase59_format_dosh_facts_block(_dosh_obj_active_manglik())
        for forbidden in [
            ">>> NARRATE", "Rule 10", "DO NOT", "MUST",
            "Mangal mantra", "Hanuman puja", "remedies:",
        ]:
            self.assertNotIn(forbidden, out,
                             f"forbidden token `{forbidden}` leaked")

    def test_returns_empty_for_bad_input(self):
        for bad in [None, {}, "string", 123, []]:
            self.assertEqual(oh._phase59_format_dosh_facts_block(bad), "")

    def test_handles_missing_keys_without_raising(self):
        out = oh._phase59_format_dosh_facts_block({"total_dosh": 0})
        self.assertTrue(out.startswith("DOSH_FACTS:"))
        self.assertIn("  - total_present: 0", out)
        self.assertIn("  - active_count: 0", out)

    def test_engine_strings_with_newlines_get_collapsed(self):
        """Architect-flagged hardening: engine fields containing newlines
        or control chars must NOT inject extra bullet rows into the
        DOSH_FACTS block. Whitespace must be normalized to single spaces.
        """
        v = {
            "total_dosh": 1, "active_count": 1, "mild_count": 0,
            "none_count": 0,
            "dosh_list": [{
                "key": "manglik", "name": "Manglik\nDosha",
                "name_hindi": "", "icon": "",
                "status": "Active",
                "headline": "Mars in 1H\n  - injected: bogus\n  - injected2: x",
                "description": "...", "remedies": [],
                "planet_note": "Mars\tSagittarius\rR",
            }],
        }
        out = oh._phase59_format_dosh_facts_block(v)
        # Must not contain any newline-injected bullet rows
        for forbidden in ["    - injected:", "    - injected2:",
                          "Manglik\nDosha"]:
            self.assertNotIn(forbidden, out,
                             f"newline injection vector leaked: {forbidden!r}")
        # Whitespace must be collapsed to single spaces
        self.assertIn("Manglik Dosha:", out)
        self.assertIn("Mars in 1H - injected: bogus - injected2: x", out)
        self.assertIn("planet_note: Mars Sagittarius R", out)
        # Block should still have exactly the expected number of lines
        # (header + 4 counts + per_dosha header + 1 entry = 7 lines)
        self.assertEqual(len(out.split("\n")), 7,
                         f"unexpected line count — newline leak suspected:"
                         f"\n{out}")

    def test_malformed_field_types_do_not_raise(self):
        bad_inputs = [
            {"total_dosh": "x", "active_count": None,
             "mild_count": "?", "dosh_list": "not-a-list"},
            {"dosh_list": [
                "should-be-dict",
                {"name": 123, "status": True},
                {"name": "X", "status": "Active", "headline": None,
                 "planet_note": ["wrong"]},
                None,
            ]},
            {"dosh_list": {"wrong": "shape"}},
        ]
        for v in bad_inputs:
            try:
                out = oh._phase59_format_dosh_facts_block(v)
            except Exception as e:  # pragma: no cover
                self.fail(
                    f"formatter raised {type(e).__name__} on {v!r}: {e}")
            self.assertIsInstance(out, str)
            self.assertTrue(out.startswith("DOSH_FACTS:"),
                            f"missing header for {v!r}")


# ───────────────────────── Install routing ─────────────────────────


class TestPhase59ExtractorRouting(unittest.TestCase):

    def test_dosh_question_emits_dosh_facts_block(self):
        bm = {"dosh_verdict_obj": _dosh_obj_active_manglik()}
        out = oh._phase50_extract_verdict_facts(bm, question="Am I manglik?")
        self.assertIn("DOSH_FACTS:", out)
        self.assertIn("Manglik Dosha", out)

    def test_unrelated_question_strips_dosh(self):
        """Marriage/wealth/health Qs must not surface DOSH_FACTS."""
        bm = {"dosh_verdict_obj": _dosh_obj_active_manglik()}
        for q in [
            "Mera marriage kab hoga?",
            "Mera dhan-yog strong hai?",
            "Career kaisa rahega?",
            "What is my lagna?",
        ]:
            out = oh._phase50_extract_verdict_facts(bm, question=q)
            self.assertNotIn("DOSH_FACTS:", out,
                             f"DOSH_FACTS leaked into non-dosh Q: {q!r}")

    def test_empty_question_does_not_surface_dosh(self):
        """Backward compat: empty Q (unit-test path) must NOT add DOSH."""
        bm = {"dosh_verdict_obj": _dosh_obj_active_manglik()}
        out = oh._phase50_extract_verdict_facts(bm, question="")
        self.assertNotIn("DOSH_FACTS:", out)

    def test_no_dosh_obj_means_no_block(self):
        """Defensive: dosh question but no verdict obj on out_meta."""
        out = oh._phase50_extract_verdict_facts({}, question="Am I manglik?")
        self.assertNotIn("DOSH_FACTS:", out)
        self.assertEqual(out.strip(), "")

    def test_dosh_with_marriage_emits_both(self):
        """Cross-domain question: marriage + dosh keywords → both blocks."""
        bm = {
            "dosh_verdict_obj": _dosh_obj_active_manglik(),
            "marriage_verdict_obj": {
                "score": 70, "confidence": 60,
                "marriage_promised": True, "marriage_denied": False,
                "reasons_strong": ["Venus exalted"], "reasons_weak": [],
                "delay_reasons": [],
            },
        }
        # "manglik dosh" + "marriage" — both regexes hit
        out = oh._phase50_extract_verdict_facts(
            bm, question="Mera manglik dosh marriage me problem karega?"
        )
        self.assertIn("DOSH_FACTS:", out)
        self.assertIn("MARRIAGE_FACTS:", out)


class TestPhase59ImportSmoke(unittest.TestCase):

    def test_all_phase59_helpers_callable(self):
        for name in [
            "_phase59_is_dosh_question",
            "_phase59_format_dosh_facts_block",
            "_PHASE59_DOSH_QUESTION_RE",
        ]:
            self.assertTrue(hasattr(oh, name),
                            f"missing Phase 5.9 export: {name}")


if __name__ == "__main__":
    unittest.main()

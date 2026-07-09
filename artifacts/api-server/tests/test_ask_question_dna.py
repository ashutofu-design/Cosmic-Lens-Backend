"""Question DNA — taxonomy, validation and module-router tests (no LLM calls)."""
from __future__ import annotations

import unittest

from ask_question_dna import (
    DNA_BUCKETS_BY_DOMAIN,
    DNA_DEFAULT_BUCKET,
    DNA_DOMAINS,
    derive_required_modules,
    validate_question_dna,
    validate_question_dna_item,
    build_question_dna_system_prompt,
    _fallback_dna,
)


class TaxonomyConsistencyTests(unittest.TestCase):
    def test_every_domain_has_buckets_and_default(self):
        for d in DNA_DOMAINS:
            self.assertIn(d, DNA_BUCKETS_BY_DOMAIN, d)
            self.assertTrue(DNA_BUCKETS_BY_DOMAIN[d], d)
            self.assertIn(d, DNA_DEFAULT_BUCKET, d)
            self.assertIn(DNA_DEFAULT_BUCKET[d], DNA_BUCKETS_BY_DOMAIN[d], d)

    def test_love_uses_relationship_taxonomy_not_mr_archetypes(self):
        from ask_intent_llm import MR_ARCHETYPES, CAREER_ARCHETYPES
        from relationship_dna_taxonomy import LOVE_RELATIONSHIP_BUCKETS

        self.assertEqual(DNA_BUCKETS_BY_DOMAIN["love"], LOVE_RELATIONSHIP_BUCKETS)
        self.assertEqual(DNA_BUCKETS_BY_DOMAIN["marriage"], frozenset(MR_ARCHETYPES))
        self.assertEqual(DNA_BUCKETS_BY_DOMAIN["career"], frozenset(CAREER_ARCHETYPES))
        self.assertNotIn("loyalty_trust", DNA_BUCKETS_BY_DOMAIN["love"])
        self.assertIn("trust_loyalty", DNA_BUCKETS_BY_DOMAIN["love"])

    def test_prompt_forbids_answering_and_lists_non_love_buckets(self):
        p = build_question_dna_system_prompt()
        self.assertIn("NOT an astrologer", p)
        self.assertIn("govt_job", p)
        self.assertIn("STRICT JSON", p)
        self.assertIn("long-term chalega", p)
        self.assertIn("relationship_decisions", p)
        self.assertIn("communication", p)
        # Love bucket enum is NOT dumped in prompt
        self.assertNotIn("trust_loyalty, love_feelings, partner_nature", p)
        # Few-shots present
        self.assertIn("cheat karega", p)
        self.assertIn("Exact month", p)


class ValidationTests(unittest.TestCase):
    def test_valid_item_passes_through(self):
        item = validate_question_dna_item({
            "normalized_question": "Kya mera boyfriend cheat karega?",
            "domain": "love",
            "bucket": "trust_loyalty",
            "intent": "cheating prediction",
            "subject": "boyfriend",
            "target": "self_relationship",
            "question_type": "risk",
            "timing": False,
            "tense": "future",
            "emotion": "fear",
            "risk": "high",
            "confidence": 0.97,
        })
        self.assertEqual(item["domain"], "love")
        self.assertEqual(item["bucket"], "trust_loyalty")
        self.assertEqual(item["engine_archetype"], "loyalty_trust")
        self.assertEqual(item["bucket_match_confidence"], "high")
        self.assertEqual(item["subject"], "boyfriend")
        self.assertEqual(item["coercions"], 0)
        self.assertAlmostEqual(item["confidence"], 0.97)

    def test_invented_bucket_coerced_to_domain_default(self):
        item = validate_question_dna_item({
            "domain": "career",
            "bucket": "made_up_bucket",
            "confidence": 0.9,
        })
        self.assertEqual(item["bucket"], "general_career")
        self.assertGreaterEqual(item["coercions"], 1)
        self.assertLess(item["confidence"], 0.9)

    def test_invented_domain_coerced_to_general(self):
        item = validate_question_dna_item({"domain": "astro_magic", "confidence": 0.8})
        self.assertEqual(item["domain"], "general")
        self.assertIn(item["bucket"], DNA_BUCKETS_BY_DOMAIN["general"])

    def test_legacy_mr_bucket_alias_on_love(self):
        item = validate_question_dna_item({
            "domain": "love",
            "bucket": "loyalty_trust",
            "confidence": 0.9,
        })
        self.assertEqual(item["bucket"], "trust_loyalty")
        self.assertEqual(item["coercions"], 0)

    def test_invented_love_bucket_coerced(self):
        item = validate_question_dna_item({
            "domain": "love",
            "bucket": "made_up_love_bucket",
            "confidence": 0.9,
        })
        self.assertEqual(item["bucket"], "unknown_relationship_intent")
        self.assertTrue(item["bucket_coerced"])
        self.assertEqual(item["bucket_match_confidence"], "low")
        self.assertGreaterEqual(item["coercions"], 1)

    def test_bucket_domain_mismatch_coerced(self):
        # trust_loyalty is a love bucket, not career
        item = validate_question_dna_item({
            "domain": "career",
            "bucket": "trust_loyalty",
            "confidence": 0.9,
        })
        self.assertEqual(item["bucket"], "general_career")

    def test_confidence_0_100_scale_tolerated(self):
        item = validate_question_dna_item({"domain": "love", "bucket": "relationship_future", "confidence": 99})
        self.assertLessEqual(item["confidence"], 1.0)
        self.assertGreater(item["confidence"], 0.9)

    def test_timing_question_type_forces_timing_flag(self):
        item = validate_question_dna_item({
            "domain": "marriage", "bucket": "general_mr",
            "question_type": "timing", "timing": False, "confidence": 0.9,
        })
        self.assertTrue(item["timing"])

    def test_personality_type_clears_bogus_timing(self):
        item = validate_question_dna_item({
            "domain": "love", "bucket": "partner_nature",
            "question_type": "personality", "timing": True, "confidence": 0.9,
        })
        self.assertFalse(item["timing"])

    def test_prediction_defaults_tense_to_future(self):
        item = validate_question_dna_item({
            "domain": "love",
            "bucket": "relationship_promise",
            "question_type": "prediction",
            "tense": "unspecified",
            "confidence": 0.95,
        })
        self.assertEqual(item["tense"], "future")

    def test_empty_payload_falls_back_low_confidence(self):
        out = validate_question_dna({}, original_question="shaadi kab hogi")
        self.assertEqual(len(out["questions"]), 1)
        self.assertEqual(out["questions"][0]["normalized_question"], "shaadi kab hogi")
        self.assertTrue(out["source"].startswith("dna_fallback"))

    def test_multi_question_split_preserved(self):
        out = validate_question_dna({
            "questions": [
                {"normalized_question": "Govt job kab milegi?", "domain": "career",
                 "bucket": "govt_job", "question_type": "timing", "timing": True,
                 "confidence": 0.95},
                {"normalized_question": "Partner loyal hai?", "domain": "love",
                 "bucket": "trust_loyalty", "question_type": "risk", "timing": False,
                 "confidence": 0.95},
            ],
        })
        self.assertEqual(len(out["questions"]), 2)
        self.assertEqual(out["questions"][0]["domain"], "career")
        self.assertEqual(out["questions"][1]["domain"], "love")

    def test_never_raises_on_garbage(self):
        for garbage in (None, "text", 42, [], {"questions": "nope"}, {"questions": [None, 7]}):
            out = validate_question_dna(garbage, original_question="q")
            self.assertIn("questions", out)
            self.assertTrue(out["questions"])


class ModuleRouterTests(unittest.TestCase):
    def test_marriage_timing_gets_dasha_transit_kp(self):
        mods = derive_required_modules("marriage", "general_mr", timing=True)
        for m in ("D1", "D9", "DASHA", "TRANSIT", "KP"):
            self.assertIn(m, mods)

    def test_static_loyalty_is_d1_d9_only(self):
        mods = derive_required_modules("love", "trust_loyalty", timing=False, tense="future")
        self.assertEqual(set(mods), {"D1", "D9"})

    def test_present_tense_affair_gets_current_dasha(self):
        # "affair abhi chal raha hai?" — present state needs current activation
        mods = derive_required_modules(
            "love", "third_person_infidelity", timing=False, tense="present",
        )
        self.assertIn("DASHA", mods)
        self.assertIn("TRANSIT", mods)
        self.assertNotIn("KP", mods)

    def test_career_timing_gets_ashtakavarga_and_d10(self):
        mods = derive_required_modules("career", "govt_job", timing=True)
        self.assertIn("D10", mods)
        self.assertIn("ASHTAKAVARGA", mods)

    def test_children_gets_d7(self):
        mods = derive_required_modules("children", "child_promise")
        self.assertIn("D7", mods)


class FallbackTests(unittest.TestCase):
    def test_fallback_shape(self):
        fb = _fallback_dna("koi sawaal", "no_client")
        self.assertEqual(fb["source"], "dna_fallback:no_client")
        self.assertEqual(fb["questions"][0]["confidence"], 0.0)
        self.assertEqual(fb["questions"][0]["normalized_question"], "koi sawaal")
        self.assertIn("required_modules", fb["questions"][0])


if __name__ == "__main__":
    unittest.main()

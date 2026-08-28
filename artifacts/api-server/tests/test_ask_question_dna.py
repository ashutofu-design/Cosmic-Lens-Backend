"""Question DNA — taxonomy, validation and module-router tests (no LLM calls)."""
from __future__ import annotations

import unittest

from ask_question_dna import (
    DNA_BUCKETS_BY_DOMAIN,
    DNA_DEFAULT_BUCKET,
    DNA_DOMAINS,
    build_dna_compliance_retry_user_message,
    build_question_dna_narrator_rules,
    dna_judge_contract_from_item,
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
        self.assertIn("ROUTING PRIORITY RULES", p)
        self.assertIn("relationship_challenges is LAST FALLBACK", p)
        # Love bucket enum is NOT dumped in prompt
        self.assertNotIn("trust_loyalty, love_feelings, partner_nature", p)
        # Few-shots present
        self.assertIn("user_wants", p)
        self.assertIn("answer_style", p)
        self.assertIn("answer_approach", p)


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

    def test_llm_understanding_fields_validated(self):
        item = validate_question_dna_item({
            "normalized_question": "Meri health kaisi rahegi?",
            "domain": "health",
            "bucket": "general_health",
            "intent": "overall health outlook",
            "subject": "self",
            "target": "self",
            "question_type": "prediction",
            "timing": False,
            "tense": "future",
            "emotion": "curiosity",
            "risk": "low",
            "confidence": 0.92,
            "user_wants": "User wants to know how her overall health will be.",
            "understanding_confidence": 0.94,
            "answer_style": "short_paragraph",
            "answer_approach": "Use D1/D9 health chart — supportive general wellness tone.",
        })
        self.assertIn("User wants to know", item["user_wants"])
        self.assertAlmostEqual(item["understanding_confidence"], 0.94)
        self.assertEqual(item["answer_style"], "short_paragraph")
        self.assertIn("D1/D9", item["answer_approach"])

    def test_derive_answer_approach_prefers_user_wants_over_placeholder(self):
        from ask_question_dna import validate_question_dna_item

        item = validate_question_dna_item({
            "domain": "career",
            "bucket": "govt_job",
            "user_wants": "User wants government job timing and whether SSC attempt will succeed.",
            "answer_approach": "phase2_understand",
            "question_type": "timing",
            "timing": True,
            "confidence": 0.9,
        })
        self.assertIn("government job timing", item["answer_approach"])
        self.assertNotEqual(item["answer_approach"], "phase2_understand")

    def test_llm_understanding_fields_derived_when_missing(self):
        item = validate_question_dna_item({
            "domain": "love",
            "bucket": "third_person_infidelity",
            "intent": "partner cheating check",
            "question_type": "current_state",
            "timing": False,
            "confidence": 0.9,
        })
        self.assertIn("partner cheating", item["user_wants"])
        self.assertAlmostEqual(item["understanding_confidence"], 0.9)
        self.assertEqual(item["answer_style"], "short_2_3_lines")
        self.assertIn("present-state", item["answer_approach"].lower())

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
    def test_marriage_timing_gets_dasha_transit_bcp_without_kp(self):
        mods = derive_required_modules("marriage", "general_mr", timing=True)
        for m in ("D1", "D9", "DASHA", "TRANSIT", "BCP"):
            self.assertIn(m, mods)
        self.assertNotIn("KP", mods)

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
        self.assertIn("D9", mods)
        self.assertIn("D10", mods)
        self.assertIn("ASHTAKAVARGA", mods)
        self.assertNotIn("BCP", mods)

    def test_children_gets_d7(self):
        mods = derive_required_modules("children", "child_promise")
        self.assertIn("D9", mods)
        self.assertIn("D7", mods)

    def test_children_timing_is_only_non_marriage_bcp_route(self):
        mods = derive_required_modules("children", "child_timing", timing=True)
        self.assertIn("BCP", mods)
        self.assertNotIn("KP", mods)

    def test_gap_domains_have_dna_and_question_specific_modules(self):
        from ask_question_dna import DNA_DOMAINS

        for domain in ("luck", "network", "siblings", "parents", "fame", "wellness"):
            self.assertIn(domain, DNA_DOMAINS)
        self.assertIn("D11", derive_required_modules("network", "general_network"))
        self.assertIn("D10", derive_required_modules("fame", "general_fame"))
        self.assertIn("D30", derive_required_modules("wellness", "general_wellness"))
        self.assertNotIn(
            "BCP",
            derive_required_modules("fame", "general_fame", timing=True),
        )


class DnaRoutingTests(unittest.TestCase):
    def test_commitment_question_routes_via_dna(self):
        from ask_question_dna import apply_question_dna_to_routing, validate_question_dna_item

        q = "kya mere partner future ko lekar serious planning karta hai"
        item = validate_question_dna_item({
            "domain": "love",
            "bucket": "commitment",
            "intent": "Partner Seriousness / Future Planning",
            "subject": "partner",
            "target": "self_relationship",
            "question_type": "static",
            "timing": False,
            "confidence": 0.95,
        })
        dna = {"questions": [item], "source": "llm", "latency_ms": 120}
        admin = {
            "domain": "love",
            "mr_archetype": "partner_nature",
            "routed_archetype": "partner_nature",
        }
        llm_intent = {"domain": "love", "mr_archetype": "partner_nature", "is_timing": False}

        applied = apply_question_dna_to_routing(q, admin, dna, llm_intent=llm_intent)
        self.assertTrue(applied)
        self.assertEqual(admin["bucket"], "commitment")
        self.assertEqual(admin["mr_archetype"], "commitment")
        self.assertEqual(admin["routed_archetype"], "commitment")
        self.assertEqual(admin["dna_engine_archetype"], "commitment")
        self.assertEqual(admin["routing_override"], "question_dna")
        self.assertEqual(llm_intent["mr_archetype"], "commitment")
        self.assertFalse(llm_intent["is_timing"])

    def test_low_confidence_dna_does_not_override(self):
        from ask_question_dna import apply_question_dna_to_routing, validate_question_dna_item

        item = validate_question_dna_item({
            "domain": "love",
            "bucket": "commitment",
            "confidence": 0.2,
        })
        dna = {"questions": [item], "source": "llm", "latency_ms": 50}
        admin = {"mr_archetype": "partner_nature"}

        applied = apply_question_dna_to_routing("some q", admin, dna)
        self.assertFalse(applied)
        self.assertEqual(admin["mr_archetype"], "partner_nature")


class NarratorRulesTests(unittest.TestCase):
    def test_builds_rules_for_love_question(self):
        dna = validate_question_dna({
            "questions": [{
                "normalized_question": "Kya mera boyfriend cheat kar raha hai?",
                "domain": "love",
                "bucket": "third_person_infidelity",
                "intent": "cheating check",
                "question_type": "current_state",
                "timing": False,
                "confidence": 0.95,
                "user_wants": "User wants to know if boyfriend is cheating now.",
                "answer_style": "short_2_3_lines",
                "answer_approach": "Direct present-state read with 1-2 chart reasons.",
            }],
        })
        rules = build_question_dna_narrator_rules(
            {"question_dna": dna},
            question="Kya mera boyfriend cheat kar raha hai?",
        )
        self.assertIn("QUESTION DNA CONTRACT", rules)
        self.assertIn("short_2_3_lines", rules)
        self.assertIn("LLM Answer Plan", rules)
        self.assertIn("Direct present-state read", rules)
        self.assertIn("third_person_infidelity", rules)
        self.assertIn("Intent lock", rules)
        self.assertIn("current_state", rules)

    def test_narrator_rules_include_full_dna_contract(self):
        item = validate_question_dna_item({
            "normalized_question": "Shaadi kab hogi?",
            "domain": "marriage",
            "bucket": "marriage_timing",
            "intent": "marriage timing",
            "target": "self",
            "question_type": "timing",
            "timing": True,
            "tense": "future",
            "emotion": "hope",
            "is_followup": True,
            "followup_of": "marriage prediction",
            "confidence": 0.95,
            "user_wants": "User wants marriage timing window.",
            "answer_style": "short_paragraph",
            "answer_approach": "Lead with AD/PD window then confirm via transit.",
        })
        dna = {"questions": [item]}
        rules = build_question_dna_narrator_rules(
            {"question_dna": dna},
            question="Exact month?",
        )
        self.assertIn("marriage_timing", rules)
        self.assertIn("Timing=true", rules)
        self.assertIn("Time context=future", rules)
        self.assertIn("Emotion=hope", rules)
        self.assertIn("Follow-up=true", rules)
        self.assertIn("marriage prediction", rules)

    def test_dna_judge_contract_and_retry_message(self):
        item = validate_question_dna_item({
            "domain": "career",
            "bucket": "govt_job",
            "intent": "government job timing",
            "question_type": "timing",
            "timing": True,
            "answer_style": "short_paragraph",
            "answer_approach": "Lead with dasha window.",
            "confidence": 0.9,
        })
        contract = dna_judge_contract_from_item(item)
        self.assertTrue(contract["timing"])
        self.assertEqual(contract["bucket"], "govt_job")
        msg = build_dna_compliance_retry_user_message(
            ["timing_missing — no period in answer"],
            item,
        )
        self.assertIn("timing_missing", msg)
        self.assertIn("govt_job", msg)
        self.assertIn("LLM Answer Plan", msg)

    def test_health_validator_note_when_enabled(self):
        dna = validate_question_dna({
            "questions": [{
                "domain": "health",
                "bucket": "general_health",
                "answer_style": "short_paragraph",
                "answer_approach": "Soft overview from chart JSON.",
                "user_wants": "User wants health overview.",
                "confidence": 0.9,
            }],
        })
        rules = build_question_dna_narrator_rules(
            {"question_dna": dna},
            question="Meri health kaisi hai?",
            health_validator=True,
        )
        self.assertIn("validator will reject mismatch", rules)

    def test_empty_when_no_dna(self):
        self.assertEqual(build_question_dna_narrator_rules(None), "")


class FallbackTests(unittest.TestCase):
    def test_fallback_shape(self):
        fb = _fallback_dna("koi sawaal", "no_client")
        self.assertEqual(fb["source"], "dna_fallback:no_client")
        self.assertEqual(fb["questions"][0]["confidence"], 0.0)
        self.assertEqual(fb["questions"][0]["normalized_question"], "koi sawaal")
        self.assertIn("required_modules", fb["questions"][0])


if __name__ == "__main__":
    unittest.main()

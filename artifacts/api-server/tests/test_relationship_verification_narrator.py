"""Relationship verification narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_relationship_verification_angle
from ask_mr.relationship_verification_templates import (
    detect_relationship_verification_answer_focus,
    get_opening,
)
from ask_mr.relationship_verification_narrator import (
    engine_result_to_relationship_verification_json,
    render_relationship_verification_template_answer,
    relationship_verification_engine_narrator_payload,
    validate_relationship_verification_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.relationship_verification import run_relationship_verification_v2

SAMPLE_KUNDLI = {
    "ascendant": "Scorpio",
    "planets": [
        {"name": "Mars", "sign": "Aries", "house": 7},
        {"name": "Rahu", "sign": "Gemini", "house": 7},
        {"name": "Moon", "sign": "Capricorn", "house": 8},
        {"name": "Venus", "sign": "Taurus", "house": 12},
        {"name": "Saturn", "sign": "Aquarius", "house": 5},
        {"name": "Jupiter", "sign": "Pisces", "house": 6},
    ],
    "dasha": {"mahadasha": "Mars", "antardasha": "Rahu"},
}

GOLDEN_QUESTIONS = [
    ("Kya partner ke words aur actions match karte hain?", "words_actions"),
    ("Partner reliable hai kya?", "reliability_signal"),
    ("Proof kya hai ki partner genuine hai?", "proof_gap"),
    ("Partner ka behaviour consistent hai kya?", "behaviour_consistency"),
    ("Kya partner apne promise nibhata hai?", "promise_reality"),
    ("Partner genuine intent rakhta hai kya?", "genuine_intent"),
    ("Kaise verify karun partner ko?", "cross_check"),
    ("Kya partner bolne aur karne me same hai?", "words_actions"),
    ("Saboot mil sakta hai loyalty ka?", "proof_gap"),
    ("Partner inconsistent hai kya?", "behaviour_consistency"),
    ("Actions match karte hain ya nahi?", "words_actions"),
    ("Partner unreliable hai chart ke hisaab se?", "reliability_signal"),
    ("Cross-check karne ki zarurat hai kya?", "cross_check"),
    ("Wade aur reality me gap hai kya?", "promise_reality"),
    ("Partner sachcha hai ya act kar raha hai?", "genuine_intent"),
    ("Overall relationship verification consistent hai?", "general_verification"),
    ("Partner ke actions genuine hain?", "genuine_intent"),
    ("Promise aur kaam me farq hai?", "promise_reality"),
    ("Yakeen kaise ho ki partner real hai?", "cross_check"),
    ("Kya partner apni baat par khada rehta hai?", "words_actions"),
]

RVER_Q = "Kya partner ke words aur actions match karte hain?"


class RelationshipVerificationNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_relationship_verification_v2(SAMPLE_KUNDLI, RVER_Q)
        self.result = v2_to_engine_result(self.out)

    def test_rver_json_shape(self):
        data = engine_result_to_relationship_verification_json(self.result, question=RVER_Q)
        self.assertEqual(data["question_type"], "relationship_verification")
        self.assertIn(data["final_verdict"], ("Consistent", "Mixed", "Inconsistent", "Unreliable"))

    def test_words_actions_angle(self):
        data = engine_result_to_relationship_verification_json(self.result, question=RVER_Q)
        self.assertEqual(data.get("answer_focus"), "words_actions")

    def test_unreliable_not_consistent_praise(self):
        data = engine_result_to_relationship_verification_json(self.result, question=RVER_Q)
        data["verification_level"] = "unreliable"
        data["relationship_verification_level"] = "unreliable"
        data["direct_answer"] = get_opening("words_actions", "unreliable")
        text = render_relationship_verification_template_answer(data, RVER_Q)
        self.assertNotRegex(text, r"(?i)mostly\s+consistent|alignment\s+supportive")

    def test_locked_template_valid(self):
        data = engine_result_to_relationship_verification_json(self.result, question=RVER_Q)
        ok, issues = validate_relationship_verification_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = relationship_verification_engine_narrator_payload(self.result, question=RVER_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_dna_bucket_proof(self):
        dna = {"questions": [{"bucket": "relationship_verification", "intent": "proof gap evidence"}]}
        angle = detect_relationship_verification_answer_focus(
            "kya proof hai", question_dna=dna
        )
        self.assertEqual(angle, "proof_gap")


class RelationshipVerificationGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_relationship_verification_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:10]:
            out = run_relationship_verification_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_relationship_verification_json(v2_to_engine_result(out), question=q)
            text = render_relationship_verification_template_answer(data, q)
            ok, issues = validate_relationship_verification_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{q}: {issues}")


if __name__ == "__main__":
    unittest.main()

"""Loyalty / trust narrator — intent-anchored, verdict-consistent template tests."""
from __future__ import annotations

import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_loyalty_angle
from ask_mr.loyalty_templates import (
    detect_loyalty_answer_focus,
    get_opening,
    OPENING_TEMPLATES,
)
from ask_mr.loyalty_narrator import (
    engine_result_to_loyalty_json,
    loyalty_narrator_payload,
    render_loyalty_template_answer,
    validate_loyalty_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.loyalty_trust import run_loyalty_trust_v2

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Mars", "sign": "Capricorn", "house": 7},
        {"name": "Rahu", "sign": "Cancer", "house": 8},
        {"name": "Saturn", "sign": "Aries", "house": 5},
    ],
    "dasha": {"mahadasha": "Saturn", "antardasha": "Mars"},
}

GOLDEN_QUESTIONS: list[tuple[str, str]] = [
    ("kya mera partner mujhe cheat karega", "cheating_risk"),
    ("kya partner dhokha de raha hai", "cheating_risk"),
    ("kya mera boyfriend affair me hai", "cheating_risk"),
    ("kya pati mujhe dhokha de sakta hai", "cheating_risk"),
    ("kya mera partner loyal hai", "is_loyal"),
    ("kya girlfriend faithful hai", "faithfulness"),
    ("kya partner wafadar hai", "faithfulness"),
    ("kya main partner par trust kar sakti hoon", "trust_issues"),
    ("kya mujhe partner par vishwas karna chahiye", "trust_issues"),
    ("kya partner sirf mujhe chahta hai exclusive", "exclusive"),
    ("kya boyfriend only me chahta hai", "exclusive"),
    ("kya partner ka secret relationship hai", "secret_relationship"),
    ("kya chupke rishta chal raha hai", "secret_relationship"),
    ("kya partner double dating kar raha hai", "multiple_partners"),
    ("kya do partner parallel me hain", "multiple_partners"),
    ("kya partner chupke mil raha hai", "hidden_behavior"),
    ("kya boyfriend hidden behaviour karta hai", "hidden_behavior"),
    ("kya partner emotionally loyal hai", "emotional_loyalty"),
    ("kya sirf flirt hai timepass", "flirt_only"),
    ("kya partner trust ke layak hai", "general_trust"),
    ("kya mera husband loyal rahega", "is_loyal"),
    ("kya wife mujhe cheat karegi", "cheating_risk"),
    ("kya partner beimaan hai", "cheating_risk"),
    ("kya girlfriend vishwas ke layak hai", "trust_issues"),
    ("kya pati wafadari nibhayega", "faithfulness"),
]

CHEATING_Q = "kya mera partner mujhe cheat karega"


class LoyaltyNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_loyalty_trust_v2(SAMPLE_KUNDLI, CHEATING_Q)
        self.result = v2_to_engine_result(self.out)

    def test_loyalty_json_shape(self):
        data = engine_result_to_loyalty_json(self.result, question=CHEATING_Q)
        self.assertEqual(data["question_type"], "loyalty_trust")
        self.assertIn("final_verdict", data)
        self.assertIn("loyalty_level", data)
        self.assertIn("strongest", data)
        self.assertIn("weakest", data)
        self.assertIn("confidence", data)
        self.assertIn(data["final_verdict"], ("Moderate", "Mixed", "Unstable", "Risky"))
        self.assertGreater(data["confidence"], 0)

    def test_cheating_angle_detected(self):
        data = engine_result_to_loyalty_json(self.result, question=CHEATING_Q)
        self.assertEqual(data.get("answer_focus"), "cheating_risk")
        self.assertEqual(data.get("loyalty_angle"), "cheating_risk")

    def test_risky_opening_not_haan_loyal(self):
        data = engine_result_to_loyalty_json(self.result, question=CHEATING_Q)
        data["loyalty_level"] = "risky"
        data["final_verdict"] = "Risky"
        data["direct_answer"] = get_opening("cheating_risk", "risky")
        text = render_loyalty_template_answer(data, CHEATING_Q)
        self.assertNotRegex(text, r"(?i)haan,?\s*chances|mostly\s+loyal|the\s+big\s+picture")
        self.assertRegex(text, r"(?i)high-risk|dhokh")

    def test_locked_template_has_evidence_sections(self):
        data = engine_result_to_loyalty_json(self.result, question=CHEATING_Q)
        text = data.get("locked_template") or render_loyalty_template_answer(data, CHEATING_Q)
        self.assertIn("mukhya sanket", text.lower())
        self.assertIn("dhyan dene layak", text.lower())
        self.assertNotIn("clarity", text.lower())
        self.assertRegex(text, r"Confidence\s+\w+\s*\(\d+%\)")

    def test_validate_rejects_contradiction(self):
        data = engine_result_to_loyalty_json(self.result, question=CHEATING_Q)
        data["loyalty_level"] = "risky"
        bad = "Haan, chances hain partner loyal hai. Confidence Low (28%) hai kyunki test."
        ok, issues = validate_loyalty_narrator_output(bad, data)
        self.assertFalse(ok)
        self.assertTrue(any("contradiction" in i for i in issues))

    def test_validate_accepts_locked_template(self):
        data = engine_result_to_loyalty_json(self.result, question=CHEATING_Q)
        text = data.get("locked_template") or ""
        ok, issues = validate_loyalty_narrator_output(text, data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_json_no_chart_fields(self):
        payload = loyalty_narrator_payload(self.result, question=CHEATING_Q)
        self.assertIn("ENGINE_JSON:", payload)
        self.assertIn("SOURCE_LOCK", payload)
        json_text = payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip()
        parsed = json.loads(json_text)
        blob = json.dumps(parsed, ensure_ascii=False).lower()
        self.assertNotIn("ascendant", blob)
        self.assertNotIn("kundli", blob)
        self.assertIn("strongest", parsed)

    def test_dna_bucket_overrides_general_trust(self):
        dna = {
            "questions": [
                {"bucket": "trust_loyalty", "intent": "partner_loyalty"},
            ]
        }
        angle = detect_loyalty_answer_focus("kya partner trust ke layak hai", question_dna=dna)
        self.assertIn(angle, ("trust_issues", "is_loyal", "general_trust"))


class LoyaltyGoldenAngleTests(unittest.TestCase):
    """20+ golden questions — angle detection must match intent."""

    def test_golden_angle_detection(self):
        failures: list[str] = []
        for question, expected in GOLDEN_QUESTIONS:
            got = infer_loyalty_angle(question)
            if got != expected:
                failures.append(f"{question!r}: expected {expected}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_each_angle_has_all_levels(self):
        for angle, levels in OPENING_TEMPLATES.items():
            for level in ("moderate", "mixed", "unstable", "risky"):
                opening = get_opening(angle, level)
                self.assertTrue(opening, msg=f"missing opening {angle}/{level}")
                self.assertNotRegex(opening, r"(?i)the\s+big\s+picture|clarity\s+chahiye")

    def test_golden_questions_render_without_crash(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for question, _expected in GOLDEN_QUESTIONS[:12]:
            out = run_loyalty_trust_v2(SAMPLE_KUNDLI, question)
            result = v2_to_engine_result(out)
            data = engine_result_to_loyalty_json(result, question=question)
            text = render_loyalty_template_answer(data, question)
            self.assertGreater(len(text), 80, msg=question)
            self.assertNotIn("The Big Picture", text)
            ok, issues = validate_loyalty_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{question}: {issues}")

    def test_is_loyal_risky_opening_contradiction_free(self):
        opening = get_opening("is_loyal", "risky")
        self.assertNotRegex(opening, r"(?i)^haan|mostly\s+loyal|trustworthy\s+dikhta")
        self.assertRegex(opening, r"(?i)risk|safe\s+nahi|high-risk")

    def test_cheating_moderate_not_alarmist(self):
        opening = get_opening("cheating_risk", "moderate")
        self.assertNotRegex(opening, r"(?i)high-risk|haan.*cheat")
        self.assertRegex(opening, r"(?i)strong cheating signal nahi|verify")

    def test_multiple_partners_angle_keywords(self):
        q = "kya partner double dating kar raha hai"
        self.assertEqual(infer_loyalty_angle(q), "multiple_partners")
        data = {
            "loyalty_level": "risky",
            "final_verdict": "Risky",
            "answer_focus": "multiple_partners",
            "direct_answer": get_opening("multiple_partners", "risky"),
            "strongest": [],
            "weakest": ["Rahu 7th parallel attention"],
            "confidence": 28,
            "confidence_label": "Low",
            "scorecard": {},
        }
        text = render_loyalty_template_answer(data, q)
        self.assertRegex(text, r"(?i)double|multiple|parallel")


if __name__ == "__main__":
    unittest.main()

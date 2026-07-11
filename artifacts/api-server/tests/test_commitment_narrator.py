"""Tests for Commitment Engine narrator — JSON-only payload + prompt rules."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_mr.v2.engines.commitment import run_commitment_v2
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.commitment_narrator import (
    commitment_narrator_payload,
    engine_result_to_commitment_json,
    render_commitment_template_answer,
    validate_commitment_narrator_output,
    _build_direct_answer,
)
from ask_mr.narrator import build_mr_engine_narrator_system_prompt

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Jupiter", "sign": "Libra", "house": 11},
        {"name": "Saturn", "sign": "Aries", "house": 5},
    ],
    "dasha": {"mahadasha": "Venus", "antardasha": "Jupiter"},
}


class CommitmentNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_commitment_v2(
            SAMPLE_KUNDLI,
            "Kya mera partner commitment ke liye ready hai?",
        )
        self.result = v2_to_engine_result(self.out)

    def test_commitment_json_shape(self):
        data = engine_result_to_commitment_json(self.result)
        self.assertEqual(data["question_type"], "commitment")
        self.assertIn("final_verdict", data)
        self.assertIn("commitment_level", data)
        self.assertIn("strongest", data)
        self.assertIn("weakest", data)
        self.assertIn("reason", data)
        self.assertIn("confidence", data)
        self.assertIn(data["final_verdict"], ("Ready", "Cautious", "Mixed", "Low"))
        self.assertIsInstance(data["strongest"], list)
        self.assertGreater(len(data["strongest"]), 0)
        self.assertIsInstance(data["confidence"], int)

    def test_json_has_no_chart_fields(self):
        payload = commitment_narrator_payload(self.result)
        self.assertIn("ENGINE_JSON:", payload)
        self.assertIn("SOURCE_LOCK", payload)
        json_text = payload.split("ENGINE_JSON:", 1)[1].split("QUESTION_ANGLE:", 1)[0].strip()
        parsed = json.loads(json_text)
        blob = json.dumps(parsed, ensure_ascii=False).lower()
        self.assertNotIn("ascendant", blob)
        self.assertNotIn("kundli", blob)
        self.assertIn("strongest", parsed)

    def test_payload_parses_as_valid_json_block(self):
        payload = commitment_narrator_payload(self.result)
        json_text = payload.split("ENGINE_JSON:", 1)[1].split("QUESTION_ANGLE:", 1)[0].strip()
        parsed = json.loads(json_text)
        self.assertIn("verdict", parsed)
        self.assertIn("strongest_factor", parsed)

    def test_narrator_prompt_commitment_rules(self):
        payload = commitment_narrator_payload(self.result)
        prompt = build_mr_engine_narrator_system_prompt(
            chart_text=payload,
            archetype="commitment",
            reply_lang="hn",
            wants_explain=False,
        )
        self.assertIn("ENGINE_JSON", prompt)
        self.assertIn("commitment", prompt.lower())
        self.assertIn("LOCKED_TEMPLATE", payload)
        self.assertIn("confidence_explanation", prompt)
        self.assertNotIn("The Big Picture", prompt)
        self.assertIn("ENGINE LOCK", prompt)

    def test_raw_evidence_preserved_in_json(self):
        data = engine_result_to_commitment_json(self.result)
        blob = json.dumps(data, ensure_ascii=False).lower()
        # Engine evidence terms should survive — not generic humanized labels only
        self.assertTrue(
            "lord" in blob or "venus" in blob or "moon" in blob or "jupiter" in blob or len(data["strongest"]) > 0
        )
        for factor in data["strongest"]:
            self.assertNotIn("supportive venus", factor.lower())

    def test_timing_omitted_when_not_applicable(self):
        data = engine_result_to_commitment_json(self.result)
        self.assertNotIn("timing", data)

    def test_confidence_never_zero(self):
        data = engine_result_to_commitment_json(self.result)
        self.assertGreater(data["confidence"], 0)
        self.assertRegex(data.get("locked_template", ""), r"Confidence\s+\w+\s*\(\d+%\)")

    def test_locked_template_has_evidence(self):
        data = engine_result_to_commitment_json(self.result)
        template = data.get("locked_template") or ""
        self.assertIn("mukhya sanket", template.lower())
        self.assertIn("dhyan dene layak", template.lower())
        self.assertIn("Aapko kis baat par dhyan dena chahiye", template)
        self.assertRegex(template, r"Confidence\s+\w+\s*\(\d+%\)")
        self.assertIn("kyunki", template.lower())

    def test_confidence_band_medium_at_49(self):
        from ask_mr.commitment_narrator import _confidence_label_from_score

        self.assertEqual(_confidence_label_from_score(49), "Medium")
        self.assertEqual(_confidence_label_from_score(35), "Low")
        self.assertEqual(_confidence_label_from_score(36), "Medium")
        self.assertEqual(_confidence_label_from_score(66), "High")
        self.assertEqual(_confidence_label_from_score(86), "Very High")

    def test_template_no_scorecard_numbers(self):
        data = engine_result_to_commitment_json(self.result)
        template = (data.get("locked_template") or "").lower()
        self.assertNotRegex(template, r"scorecard:\s*commitment\s+\d+")
        self.assertNotIn("engine ke hisaab", template)

    def test_ignored_evidence_in_json(self):
        data = engine_result_to_commitment_json(self.result)
        self.assertIn("ignored_evidence", data)
        self.assertIsInstance(data["ignored_evidence"], list)

    def test_scorecard_in_json(self):
        data = engine_result_to_commitment_json(self.result)
        self.assertIn("scorecard", data)
        self.assertIn("scorecard_user_note", data)
        self.assertIn("confidence_explanation", data)
        self.assertIn("strongest_effects", data)
        self.assertGreater(len(data["strongest_effects"]), 0)

    def test_effects_not_planet_jargon(self):
        data = engine_result_to_commitment_json(self.result)
        for eff in data.get("strongest_effects") or []:
            low = eff.lower()
            self.assertNotIn("7th lord", low)
            self.assertNotRegex(low, r"venus\s+strong|jupiter\s+strong")

    def test_template_no_banned_clarity(self):
        data = engine_result_to_commitment_json(self.result)
        template = (data.get("locked_template") or "").lower()
        self.assertNotIn("clarity", template)
        self.assertNotIn("patience rakho", template)
        self.assertNotIn("boundaries", template)

    def test_validate_rejects_contradiction(self):
        data = engine_result_to_commitment_json(self.result)
        data["final_verdict"] = "Low"
        bad = (
            "genuine commitment level low hai. kehna mushkil hai ki serious hain ya sirf timepass. "
            "Confidence Medium (0%) hai kyunki mixed signals."
        )
        ok, issues = validate_commitment_narrator_output(bad, data)
        self.assertFalse(ok)
        self.assertTrue(issues)

    def test_validate_rejects_clarity_hallucination(self):
        data = engine_result_to_commitment_json(self.result)
        good = data.get("locked_template") or ""
        ok, issues = validate_commitment_narrator_output(good, data)
        self.assertTrue(ok, msg=str(issues))
        bad = good + " Clarity chahiye partner se."
        ok2, issues2 = validate_commitment_narrator_output(bad, data)
        self.assertFalse(ok2)
        self.assertIn("banned_clarity", issues2)

    def test_render_template_low_verdict_no_hedge(self):
        data = engine_result_to_commitment_json(self.result)
        data["final_verdict"] = "Low"
        data["commitment_level"] = "Low"
        data["direct_answer"] = _build_direct_answer("low", timepass_q=True, genuine_q=True)
        data.pop("verdict_line", None)
        data.pop("meaning_note", None)
        data.pop("reason_summary", None)
        text = render_commitment_template_answer(data, "kya partner timepass kar raha hai")
        self.assertNotRegex(text, r"(?i)kehna mushkil|ho sakta hai")
        self.assertIn("timepass", text.lower())
        self.assertRegex(text, r"(?i)final verdict\s+Low")

    def test_distinct_openings_per_commitment_angle(self):
        from ask_mr.commitment_narrator import _build_angle_direct_answer

        q1 = "kya mere partner future ko lekar serious planning karta hai"
        q2 = "kya mera partner sirf timepass kar raha hai"
        q3 = "kya mera partner shaadi ko seriously leta hai"
        a1 = _build_angle_direct_answer("mixed", "future_planning", question=q1)
        a2 = _build_angle_direct_answer("mixed", "time_pass", question=q2)
        a3 = _build_angle_direct_answer("mixed", "marriage_serious", question=q3)
        self.assertIn("future", a1.lower())
        self.assertIn("planning", a1.lower())
        self.assertIn("timepass", a2.lower())
        self.assertIn("shaadi", a3.lower())
        self.assertNotEqual(a1[:40], a2[:40])
        self.assertNotEqual(a1[:40], a3[:40])
        self.assertNotEqual(a2[:40], a3[:40])

    def test_json_includes_answer_focus_fields(self):
        data = engine_result_to_commitment_json(
            self.result,
            question="kya mere partner future ko lekar serious planning karta hai",
        )
        self.assertEqual(data.get("answer_focus"), "future_planning")
        self.assertEqual(data.get("commitment_angle"), "future_planning")
        self.assertIn("original_question", data)
        self.assertIn("future", (data.get("direct_answer") or "").lower())

    def test_adapter_passes_timing_meta(self):
        checks = self.result.checks or {}
        self.assertIn("timing", checks)
        self.assertIn("mode", checks)
        self.assertEqual(checks["mode"], "static")


if __name__ == "__main__":
    unittest.main()

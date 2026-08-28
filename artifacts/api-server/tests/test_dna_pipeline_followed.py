"""Question DNA per-field follow audit for admin debugger."""

from __future__ import annotations

import unittest

from ask_selected_blocks_common import enrich_dna_pipeline_followed


class DnaPipelineFollowedTests(unittest.TestCase):
    def test_finance_domain_followed_when_answer_has_money_theme(self):
        pipeline = [
            {"label": "Domain", "value": "Finance (finance)"},
            {"label": "Intent", "value": "Wealth growth and savings potential"},
            {"label": "LLM Understand Question", "value": "User wants to know about wealth"},
        ]
        contract = {
            "domain": "finance",
            "bucket": "wealth_potential",
            "intent": "Wealth growth and savings potential",
        }
        answer = "Aapki kundli me wealth ke strong yog hain — income aur savings dono improve ho sakte hain."
        out = enrich_dna_pipeline_followed(pipeline, contract, answer)
        self.assertEqual(out["summary"]["total"], 3)
        self.assertGreaterEqual(out["summary"]["followed_count"], 2)
        domain_row = out["steps"][0]
        self.assertTrue(domain_row["followed"])
        self.assertIn("finance", domain_row["follow_reason"])

    def test_timing_fail_when_no_when_in_answer(self):
        pipeline = [
            {"label": "Timing Required", "value": "Yes"},
            {"label": "Question Type", "value": "Timing"},
        ]
        contract = {"timing": True, "question_type": "timing"}
        answer = "Chart strong hai, positive energy hai, sab theek rahega."
        out = enrich_dna_pipeline_followed(pipeline, contract, answer)
        self.assertFalse(out["steps"][0]["followed"])
        self.assertIn("WHEN", out["steps"][0]["follow_reason"])

    def test_missing_dna_value_marked_fail(self):
        pipeline = [{"label": "Domain", "value": "—"}]
        out = enrich_dna_pipeline_followed(pipeline, {}, "some answer")
        self.assertFalse(out["steps"][0]["followed"])


if __name__ == "__main__":
    unittest.main()

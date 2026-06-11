"""Unit tests — in-app page vs PDF section parity."""
from __future__ import annotations

import unittest

from vedic.love_reality.app_pdf_parity import (
    build_in_app_page_sections,
    validate_app_sections_parity,
    validate_wysiwyg_screen_to_pdf,
)


def _sample_page1() -> dict:
    return {
        "relationship_summary": "Summary line one.",
        "insights_narrative": "Summary line one.",
        "key_insights": ["Insight A", "Love score 72/100 hidden"],
        "cosmic_score": 68,
        "metrics": [{"label": "Love", "value": 72, "interpretation": "Strong"}],
        "strengths": [{"label": "Trust", "value": 80}],
        "challenges": [{"label": "Breakup risk", "value": 35}],
        "verdict": "Verdict paragraph here.",
        "recommendation_paragraphs": ["Do this first.", "Then this."],
        "recommendations": ["Daily check-in", "Friday ritual"],
        "analysis": [
            {"title": "Emotional", "explanation": "Deep emotional bond text."},
        ],
    }


def _sample_ctx() -> dict:
    return {
        "page2_3_blueprint": {"part2": "Blueprint reality narrative."},
        "page6_root_cause": "Root cause narrative.",
        "page5_moon": {"body": "Moon sync LLM body."},
    }


class TestAppPdfParity(unittest.TestCase):
    def test_matching_sections_pass(self):
        expected = build_in_app_page_sections(_sample_page1(), _sample_ctx(), lang="en")
        app_sections = [
            {**sec, "title": f"Title {sec['id']}", "subtitle": "Sub"}
            for sec in expected
        ]
        err = validate_app_sections_parity(
            app_sections=app_sections,
            page1=_sample_page1(),
            pdf_context=_sample_ctx(),
            lang="en",
        )
        self.assertIsNone(err)

    def test_body_mismatch_fails_with_line_detail(self):
        expected = build_in_app_page_sections(_sample_page1(), _sample_ctx(), lang="en")
        app_sections = [{**sec, "title": sec["id"]} for sec in expected]
        for sec in app_sections:
            if sec.get("id") == "verdict":
                sec["body"] = "Different verdict on screen."
        err = validate_app_sections_parity(
            app_sections=app_sections,
            page1=_sample_page1(),
            pdf_context=_sample_ctx(),
            lang="en",
        )
        self.assertIsNotNone(err)
        self.assertIn("verdict", err or "")
        self.assertIn("line 1", err or "")

    def test_missing_section_fails(self):
        expected = build_in_app_page_sections(_sample_page1(), _sample_ctx(), lang="en")
        app_sections = [{**sec, "title": sec["id"]} for sec in expected if sec["id"] != "moon"]
        err = validate_app_sections_parity(
            app_sections=app_sections,
            page1=_sample_page1(),
            pdf_context=_sample_ctx(),
            lang="en",
        )
        self.assertIsNotNone(err)
        self.assertIn("moon", err or "")

    def test_wysiwyg_screen_sections_pass(self):
        app_sections = [
            {
                "id": "exec_summary",
                "title": "Summary",
                "body": "Line one.\n\nLine two.",
            },
            {"id": "verdict", "title": "Verdict", "body": "Verdict text here."},
            {
                "id": "recommendations",
                "title": "Remedies",
                "body": "Do this weekly.",
                "bullets": ["Step one", "Step two"],
            },
            {"id": "root_cause", "title": "Root Cause", "body": "Root cause narrative."},
        ]
        err = validate_wysiwyg_screen_to_pdf(app_sections, lang="en")
        self.assertIsNone(err)

    def test_wysiwyg_empty_section_fails(self):
        app_sections = [
            {"id": "verdict", "title": "Verdict", "body": ""},
        ]
        err = validate_wysiwyg_screen_to_pdf(app_sections, lang="en")
        self.assertIsNotNone(err)
        self.assertIn("Error converting to PDF", err or "")


if __name__ == "__main__":
    unittest.main()

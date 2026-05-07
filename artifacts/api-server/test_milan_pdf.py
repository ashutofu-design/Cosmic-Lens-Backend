"""Smoke tests for milan_pdf.py — Phase 2.5.11.21."""
from __future__ import annotations

import unittest

from milan_pdf import render_milan_pdf


def _deep_payload() -> dict:
    return {
        "p1": {"name": "Vikram", "nakshatra": "Pushya", "pada": 2,
               "rashi": "Cancer", "manglik": False},
        "p2": {"name": "Sanya",  "nakshatra": "Magha",  "pada": 1,
               "rashi": "Leo",    "manglik": True},
        "total": 23.5, "max": 36, "percent": 65,
        "grade": {"label": "Good Compatibility", "color": "#10B981", "emoji": "💞"},
        "verdict": "Acceptable",
        "manglik_dosh": False,
        "koots": [
            {"key": "varna",  "label": "Varna",  "score": 1,   "max": 1, "detail": "Matched"},
            {"key": "vasya",  "label": "Vasya",  "score": 2,   "max": 2, "detail": "Strong"},
            {"key": "tara",   "label": "Tara",   "score": 1.5, "max": 3, "detail": "Moderate"},
            {"key": "yoni",   "label": "Yoni",   "score": 3,   "max": 4, "detail": "Good"},
            {"key": "maitri", "label": "Maitri", "score": 4,   "max": 5, "detail": "Friendly"},
            {"key": "gana",   "label": "Gana",   "score": 5,   "max": 6, "detail": "Compatible"},
            {"key": "bhakut", "label": "Bhakut", "score": 7,   "max": 7, "detail": "Auspicious"},
            {"key": "nadi",   "label": "Nadi",   "score": 0,   "max": 8, "detail": "Same Nadi"},
        ],
        "analysis": {
            "relationship_snapshot": {
                "summary": "Vikram and Sanya share a strong bond — total 23.5 out of 36.",
                "tags": {
                    "emotional_pull": "Strong",
                    "marriage_potential": "High",
                    "long_term_stability": "Stable with patience",
                },
            },
            "emotional_alignment": {
                "text": "Pushya warmth meets Magha pride — gentle alignment over time.",
                "grounding": "Based on Moon-sign harmony, Maitri, and Gana koot.",
            },
            "trust_loyalty": {
                "text": "Trust here grows in long stretches of shared silence.",
                "grounding": "Based on Bhakut and 7th-house indicators.",
            },
            "conflict_patterns": {
                "text": "Arguments rarely begin with the topic at hand.",
                "grounding": "Based on Yoni and Mars-Mercury behavioral indicators.",
            },
            "marriage_stability": {
                "text": "Marriage is genuinely possible with Maha Mrityunjaya Jaap support.",
                "grounding": "Based on total Ashtakoot score and Manglik balance.",
            },
            "commitment_strength": {
                "text": "One attaches faster, the other commits more permanently.",
                "grounding": "Based on Maitri and Vasya.",
            },
            "future_direction": {
                "text": "Over the next 2-3 years this bond evolves through shared intent.",
                "grounding": "Based on overall compatibility score and 7th-house yogas.",
            },
            # Legacy back-compat keys also present (mirrors live API)
            "compatibility_insight": "Vikram and Sanya share a strong bond.",
            "strengths": ["Pushya warmth", "Long stretches of silence"],
            "challenges": ["Pride friction", "Slow opening up"],
            "marriage_outlook": "Bond evolves through shared intent.",
        },
    }


def _legacy_payload() -> dict:
    p = _deep_payload()
    p["analysis"] = {
        "compatibility_insight": "Vikram and Sanya share a strong bond.",
        "strengths": ["Pushya warmth", "Long stretches of silence"],
        "challenges": ["Pride friction", "Slow opening up"],
        "marriage_outlook": "Bond evolves through shared intent.",
    }
    return p


class TestMilanPdfRenderer(unittest.TestCase):

    def test_renders_deep_schema_to_pdf_bytes(self):
        b = render_milan_pdf(_deep_payload(), lang="en")
        self.assertIsInstance(b, bytes)
        self.assertGreater(len(b), 4000)  # non-trivial document
        self.assertTrue(b.startswith(b"%PDF-"))
        self.assertIn(b"%%EOF", b[-32:])

    def test_renders_legacy_schema_to_pdf_bytes(self):
        b = render_milan_pdf(_legacy_payload(), lang="en")
        self.assertTrue(b.startswith(b"%PDF-"))
        self.assertGreater(len(b), 3000)

    def test_renders_hi_devanagari_without_crash(self):
        # Even if NotoDeva isn't installed, Helvetica fallback must render
        # the document without raising.
        b = render_milan_pdf(_deep_payload(), lang="hi")
        self.assertTrue(b.startswith(b"%PDF-"))

    def test_handles_empty_payload(self):
        # Defensive: blank payload must still produce a valid PDF, never crash.
        b = render_milan_pdf({}, lang="en")
        self.assertTrue(b.startswith(b"%PDF-"))


if __name__ == "__main__":
    unittest.main()

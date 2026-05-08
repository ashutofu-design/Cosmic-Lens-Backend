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


class TestMilanPdf21CRegressions(unittest.TestCase):
    """Phase 2.5.11.21-C architect-flagged regressions."""

    def _page_count(self, pdf_bytes: bytes) -> int:
        import subprocess, tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes); fn = f.name
        try:
            out = subprocess.check_output(["pdfinfo", fn]).decode()
        finally:
            os.unlink(fn)
        for line in out.splitlines():
            if line.startswith("Pages:"):
                return int(line.split()[1])
        return -1

    def test_empty_payload_emits_exactly_12_pages(self):
        from milan_pdf import render_milan_pdf
        self.assertEqual(self._page_count(render_milan_pdf({}, "en")), 12)

    def test_legacy_only_payload_emits_exactly_12_pages(self):
        from milan_pdf import render_milan_pdf
        payload = {
            "p1": {"name": "A"}, "p2": {"name": "B"},
            "total": 18, "max": 36,
            "koots": [
                {"key": "vasya",  "label": "Vasya",        "score": 2, "max": 2, "bad": False},
                {"key": "maitri", "label": "Graha Maitri", "score": 5, "max": 5, "bad": False},
                {"key": "bhakut", "label": "Bhakut",       "score": 0, "max": 7, "bad": True},
            ],
            "analysis": {
                "compatibility_insight": "x",
                "strengths": ["s1"],
                "challenges": ["c1"],
                "marriage_outlook": "y",
            },
        }
        self.assertEqual(self._page_count(render_milan_pdf(payload, "en")), 12)

    def test_canon_koot_key_resolves_real_payload_aliases(self):
        from milan_pdf import _canon_koot_key
        self.assertEqual(_canon_koot_key({"key": "vasya"}),  "vashya")
        self.assertEqual(_canon_koot_key({"key": "maitri"}), "graha")
        self.assertEqual(_canon_koot_key({"key": "bhakut"}), "bhakoot")
        # label fallback when key blank/unknown
        self.assertEqual(_canon_koot_key({"key": "", "label": "Graha Maitri"}), "graha")
        self.assertEqual(_canon_koot_key({"key": "?", "label": "Bhakut"}),      "bhakoot")
        # totally unknown returns ""
        self.assertEqual(_canon_koot_key({"key": "xyz", "label": "Xyz"}), "")

    def test_is_manglik_unified_across_partner_flags(self):
        from milan_pdf import _is_manglik
        self.assertFalse(_is_manglik({}))
        self.assertTrue(_is_manglik({"manglik_dosh": True}))
        self.assertTrue(_is_manglik({"p1": {"manglik": True}}))
        self.assertTrue(_is_manglik({"p2": {"manglik": True}}))
        self.assertFalse(_is_manglik({"p1": {"manglik": False}, "p2": {"manglik": False}}))


if __name__ == "__main__":
    unittest.main()

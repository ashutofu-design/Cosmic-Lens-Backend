"""Unit tests for love_compat_insight helpers (no OpenAI required)."""
import os
import unittest

from vedic.love_compat_insight import (
    _HARD_MAX_TOKENS,
    _build_payload,
    _classify_reason,
    _max_completion_tokens,
    _pick_signals,
    _validate,
)


class TestLoveCompatInsight(unittest.TestCase):
    def test_classify_positive(self):
        self.assertEqual(
            _classify_reason("Moon signs friendly — emotional harmony"),
            "positive",
        )

    def test_classify_difficult(self):
        self.assertEqual(
            _classify_reason("Nadi dosha — genetic compatibility concern"),
            "difficult",
        )

    def test_pick_signals(self):
        reasons = [
            "Moon signs friendly — emotional harmony",
            "Manglik dosha — friction / remedies advised",
            "Venus conjunct Mars — magnetic attraction",
        ]
        pos = _pick_signals(reasons, kind="positive")
        dif = _pick_signals(reasons, kind="difficult")
        self.assertTrue(any("harmony" in p.lower() or "magnetic" in p.lower() for p in pos))
        self.assertTrue(any("dosha" in d.lower() or "manglik" in d.lower() for d in dif))

    def test_build_payload_shape(self):
        payload = _build_payload(
            score=72,
            breakdown={
                "emotional": 68,
                "attraction": 80,
                "communication": 55,
                "karmic": 60,
                "stability": 70,
                "dasha_transit": 62,
            },
            reasons=["Moon harmony", "Saturn aspects 7th — delay"],
        )
        self.assertEqual(payload["overall_score"], 72)
        self.assertIn("emotional", payload["dimension_scores"])
        self.assertIsInstance(payload["top_positive_signals"], list)

    def test_validate_rejects_jargon(self):
        bad = (
            "Your Moon is afflicted by Saturn in the 7th house.\n\n"
            "This creates emotional distance between partners."
        )
        ok, reason = _validate(bad)
        self.assertFalse(ok)
        self.assertEqual(reason, "jargon")

    def test_validate_accepts_clean(self):
        good = (
            "This connection carries strong attraction, but both partners process "
            "emotions differently under pressure.\n\n"
            "Softer communication and steady reassurance can deepen trust over time."
        )
        ok, _ = _validate(good)
        self.assertTrue(ok)

    def test_max_tokens_default_and_cap(self):
        os.environ.pop("LOVE_COMPAT_INSIGHT_MAX_TOKENS", None)
        self.assertEqual(_max_completion_tokens(), 180)
        os.environ["LOVE_COMPAT_INSIGHT_MAX_TOKENS"] = "999"
        self.assertEqual(_max_completion_tokens(), _HARD_MAX_TOKENS)
        os.environ["LOVE_COMPAT_INSIGHT_MAX_TOKENS"] = "150"
        self.assertEqual(_max_completion_tokens(), 150)
        os.environ.pop("LOVE_COMPAT_INSIGHT_MAX_TOKENS", None)


if __name__ == "__main__":
    unittest.main()

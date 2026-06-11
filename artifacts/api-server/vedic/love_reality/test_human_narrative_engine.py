"""Tests for human narrative engine + repetition gate."""
from __future__ import annotations

import unittest

from vedic.love_reality.human_narrative_engine import (
    build_story_cards,
    pick_primary_friction,
    pick_micro_scenes,
)
from vedic.love_reality.repetition_gate import (
    audit_report_narrative,
    check_section_human_quality,
    count_theme_hits,
)


def _sample_bundle() -> dict:
    return {
        "p1": {"name": "Rahul", "moonSign": "Gemini"},
        "p2": {"name": "Priya", "moonSign": "Taurus"},
        "couple_signals": {"moon_mismatch": True},
        "loyalty_check": {"loyalty_score": 45},
        "breakup_chances": {
            "breakup_score": 62,
            "emotional_summary": "Fast replies expected vs slow emotional processing",
            "reasons": ["communication gap under stress"],
        },
        "love_compatibility": {"love_score": 72},
    }


class HumanNarrativeEngineTests(unittest.TestCase):
    def test_pick_primary_friction_locks_one(self):
        fid = pick_primary_friction(_sample_bundle())
        self.assertIn(fid, (
            "emotional_timing",
            "communication_style",
            "trust_consistency",
            "commitment_pace",
            "conflict_escalation",
        ))

    def test_story_cards_have_combined_story(self):
        cards = build_story_cards(_sample_bundle(), "en")
        self.assertIn("Rahul", cards["combined_story"])
        self.assertIn("wrong_story", cards)
        self.assertTrue(cards["primary_label"])

    def test_micro_scenes_for_section(self):
        cards = build_story_cards(_sample_bundle(), "en")
        scenes = pick_micro_scenes(cards["friction_id"], "loyalty", "en")
        self.assertGreaterEqual(len(scenes), 1)


class RepetitionGateTests(unittest.TestCase):
    def test_rejects_hedge_and_placement_dump(self):
        bad = (
            "Moon in Gemini and Venus in Taurus and Mercury in Cancer may cause issues. "
            "It is important to note that mutual understanding may help both partners."
        )
        err = check_section_human_quality(bad, "en", section_key="verdict", p1_name="Rahul")
        self.assertIsNotNone(err)

    def test_accepts_human_mirror_prose(self):
        good = (
            "Rahul, when Priya goes quiet, you feel shut out — your mind fills the worst story. "
            "You push for an answer; they need space inside first. "
            "That is not lack of love — it is a timing clash you both keep misreading."
        )
        err = check_section_human_quality(
            good,
            "en",
            section_key="verdict",
            p1_name="Rahul",
            min_words=30,
        )
        self.assertIsNone(err)

    def test_theme_hits(self):
        self.assertGreaterEqual(count_theme_hits("trust and loyalty and doubt", "trust"), 2)

    def test_audit_flags_overuse(self):
        pro = {
            "verdict": "trust trust trust trust trust trust trust trust",
            "chapters": [],
        }
        audit = audit_report_narrative(pro, "en")
        self.assertTrue(audit.get("warnings"))


if __name__ == "__main__":
    unittest.main()

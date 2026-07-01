import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_engine_verification import (
    apply_pre_route_guards,
    is_partner_personality_question,
    should_suppress_gap_for_question,
    verify_engine_output,
    verify_static_engine_selection,
)
from ask_personality.personality_registry import is_personality_static_question


class EngineVerificationTests(unittest.TestCase):
    def test_partner_personality_not_personality_gap(self):
        q = "Mere partner ka personality style kaisa rahega expressive ya reserved"
        self.assertTrue(is_partner_personality_question(q))
        self.assertFalse(is_personality_static_question(q))
        self.assertTrue(should_suppress_gap_for_question(q, gap_key="personality"))

    def test_native_personality_still_gap(self):
        q = "Mera swabhav kaisa hai expressive ya reserved"
        self.assertFalse(is_partner_personality_question(q))
        self.assertTrue(is_personality_static_question(q))

    def test_pre_route_guard_forces_mr(self):
        flags = {"gap": True, "mr": False, "health": False, "career": False}
        q = "Mere partner ka personality style expressive ya reserved"
        out, notes = apply_pre_route_guards(flags, q, gap_key="personality")
        self.assertTrue(out.get("mr"))
        self.assertFalse(out.get("gap"))
        self.assertTrue(notes)

    def test_verify_rejects_native_archetype_on_partner_q(self):
        q = "partner ka nature expressive hai kya"
        ver = verify_static_engine_selection(
            q,
            engine_key="gap",
            archetype="personality_nature",
            gap_key="personality",
        )
        self.assertFalse(ver.ok)
        self.assertEqual(ver.action, "reroute_mr")
        self.assertEqual(ver.mr_archetype, "partner_nature")

    def test_verify_output_native_focus_mismatch(self):
        q = "mere partner ka style expressive ya reserved"
        meta = {
            "summary": ["QUESTION FOCUS: native self only — NOT spouse/in-laws."],
            "evidence": ["Lagna Aries"],
            "evidence_positive": [],
            "evidence_negative": [],
            "evidence_neutral": ["Lagna Aries"],
        }
        ver = verify_engine_output(
            q,
            engine_key="gap",
            archetype="personality_nature",
            slice_meta=meta,
            gap_key="personality",
        )
        self.assertFalse(ver.ok)
        self.assertEqual(ver.action, "reroute_mr")


if __name__ == "__main__":
    unittest.main()

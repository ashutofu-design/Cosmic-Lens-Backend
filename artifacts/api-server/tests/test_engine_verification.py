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


class EngineVerificationAdminSummaryTests(unittest.TestCase):
    def test_summary_correct_when_verification_ok(self):
        from ask_engine_verification import build_engine_verification_admin_summary

        s = build_engine_verification_admin_summary(
            "test",
            llm_intent={
                "engine_verification": {"ok": True, "action": "keep", "reason": "selection_ok"},
                "engine_ran": "mr",
            },
            slice_meta={"slice": "mr_engine_v1", "archetype": "partner_nature", "evidence": ["x"]},
        )
        self.assertEqual(s["status"], "correct")
        self.assertEqual(s["label"], "Correct engine")

    def test_summary_wrong_when_recovered(self):
        from ask_engine_verification import build_engine_verification_admin_summary

        s = build_engine_verification_admin_summary(
            "partner q",
            llm_intent={"engine_verification_recovered": "reroute_mr"},
            slice_meta={"archetype": "partner_nature", "evidence": ["x"]},
        )
        self.assertEqual(s["status"], "wrong")
        self.assertIn("corrected", s["label"].lower())

    def test_dyad_chemistry_marked_wrong(self):
        from ask_engine_verification import (
            build_engine_verification_admin_summary,
            verify_static_engine_selection,
        )
        from ask_intent_fidelity import resolve_question_understood

        q = "Hum dono ke beech chemistry kaisi rahegi, intense aur passionate ya normal"
        ver = verify_static_engine_selection(q, engine_key="mr", archetype="chemistry")
        self.assertFalse(ver.ok)
        self.assertEqual(ver.mr_archetype, "general_mr")

        s = build_engine_verification_admin_summary(
            q,
            llm_intent={
                "engine_verification": {"ok": True, "action": "keep", "reason": "selection_ok"},
                "engine_ran": "mr",
            },
            slice_meta={
                "slice": "mr_engine_v1",
                "archetype": "chemistry",
                "evidence_neutral": ["Moon under Saturn/Rahu"],
            },
        )
        self.assertEqual(s["status"], "wrong")
        self.assertEqual(s["label"], "Wrong engine")

        self.assertEqual(
            resolve_question_understood(
                q,
                {"question_summary": q, "domain": "general", "confidence": 0.95},
                engine_archetype="chemistry",
            ),
            "no",
        )

    def test_classifier_dyad_chemistry_routes_general_mr(self):
        from ask_mr.classifier import classify_mr_archetype

        q = "Hum dono ke beech chemistry kaisi rahegi, intense aur passionate ya normal"
        self.assertEqual(classify_mr_archetype(q), "general_mr")
        self.assertEqual(classify_mr_archetype("hamari chemistry kaisi hogi?"), "chemistry")

    def test_partner_mental_thinking_not_health(self):
        from ask_engine_verification import (
            build_engine_verification_admin_summary,
            verify_static_engine_selection,
        )
        from ask_health.health_registry import is_health_static_question
        from ask_intent_fidelity import infer_question_scope, resolve_question_understood

        q = "Mujhe kis tarah ka partner suit karega meri mental thinking ke hisab se"
        self.assertFalse(is_health_static_question(q))
        self.assertEqual(infer_question_scope(q, {"domain": "general"}), "partner")
        ver = verify_static_engine_selection(q, engine_key="health", archetype="general_health")
        self.assertFalse(ver.ok)
        self.assertEqual(ver.mr_archetype, "partner_nature")

        s = build_engine_verification_admin_summary(
            q,
            llm_intent={"engine_ran": "health"},
            slice_meta={
                "slice": "health_engine_v1",
                "archetype": "general_health",
                "evidence": [],
                "evidence_positive": [],
                "evidence_negative": [],
                "evidence_neutral": [],
            },
        )
        self.assertEqual(s["status"], "wrong")

        self.assertEqual(
            resolve_question_understood(
                q,
                {"question_summary": q, "domain": "general", "confidence": 0.95},
                engine_archetype="general_health",
            ),
            "no",
        )


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_scope_gate import assess_ask_scope
from openai_helper import (
    _detect_marriage_constraint,
    _last_assistant_topic_was_marriage,
    _llm_intent_is_marriage_domain,
    _marriage_shortcuts_allowed,
    _try_marriage_timing_shortcuts_after_understand,
)


class MarriageTimingFollowupTests(unittest.TestCase):
    def test_scope_allows_alt_timing_followup(self):
        q = "Agar june - nov 2029 ke bich nehi hoga aage kab hoga"
        v = assess_ask_scope(q)
        self.assertTrue(v.allowed, v.reason)

    def test_detect_marriage_constraint(self):
        q = "Agar june - nov 2029 ke bich nehi hoga aage kab hoga"
        self.assertTrue(_detect_marriage_constraint(q, []))

    def test_promotion_conditional_not_marriage_constraint(self):
        q = "next promotion kab hai agar 2026 june se dec tak nhi hoga to"
        self.assertFalse(_detect_marriage_constraint(q, []))

    def test_promotion_shortcut_blocked_after_career_understanding(self):
        q = "next promotion kab hai agar 2026 june se dec tak nhi hoga to"
        career_intent = {
            "domain": "career",
            "routed_domain": "career",
            "routed_timing": True,
            "is_timing": True,
        }
        self.assertFalse(_marriage_shortcuts_allowed(career_intent, q))
        self.assertFalse(_llm_intent_is_marriage_domain(career_intent, q))
        self.assertIsNone(
            _try_marriage_timing_shortcuts_after_understand(
                question=q,
                history=[],
                kundli={"planets": [{"name": "Sun"}]},
                birth={},
                lang="hn",
                attach_admin_fn=lambda x, **kw: x,
                reply_idx=0,
                llm_intent=career_intent,
            )
        )

    def test_marriage_shortcut_allowed_for_shaadi_after_understand(self):
        q = "Meri shaadi kab hogi?"
        marriage_intent = {"domain": "marriage", "routed_domain": "marriage", "is_timing": True}
        self.assertTrue(_marriage_shortcuts_allowed(marriage_intent, q))

    def test_last_assistant_marriage_from_history(self):
        hist = [
            {"role": "user", "text": "Mera shaadi kab hoga"},
            {"role": "assistant", "text": "Aapki shaadi June – November 2029 ke beech hogi."},
        ]
        self.assertTrue(_last_assistant_topic_was_marriage(hist))


if __name__ == "__main__":
    unittest.main()

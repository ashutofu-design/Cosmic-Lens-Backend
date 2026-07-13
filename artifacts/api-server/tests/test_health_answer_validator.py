"""Tests for health LLM answer validator loop."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_health.answer_validator import (
    build_health_validator_display,
    build_health_validator_retry_feedback,
    run_health_llm_validator_loop,
    validate_health_llm_answer,
)

_SAMPLE_EXECUTION = {
    "schema_version": "health_engine_execution_v1",
    "d1": {
        "ascendant": "Leo",
        "planets": [
            {"name": "Sun", "sign": "Leo", "house": 1},
            {"name": "Saturn", "sign": "Capricorn", "house": 6},
            {"name": "Moon", "sign": "Scorpio", "house": 4, "dignity": "debilitated", "strength_score": -2},
        ],
        "afflictions": ["Malefics in H6: Saturn"],
        "sub_flags": {"moon_afflicted": True},
    },
    "d9": {
        "ascendant": "Aries",
        "planets": [{"name": "Sun", "sign": "Leo", "house": 5}],
    },
}


class HealthAnswerValidatorTests(unittest.TestCase):
    def setUp(self):
        # Unit tests use deterministic rules; LLM judge tested separately with mock.
        os.environ["ASK_HEALTH_DNA_JUDGE"] = "0"

    def tearDown(self):
        os.environ.pop("ASK_HEALTH_DNA_JUDGE", None)

    def test_passes_on_topic_answer(self):
        meta = {
            "archetype": "respiratory_health",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        ok, issues = validate_health_llm_answer(
            "mujhse thandi bahut rehti hai kya karu",
            "Saturn 6th ghar me hai, isliye chart me thandi/sardi ki tendency dikhti hai. Rest aur doctor checkup rakho.",
            meta,
        )
        self.assertTrue(ok, issues)

    def test_blocks_invented_planet_house(self):
        meta = {
            "archetype": "respiratory_health",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        ok, issues = validate_health_llm_answer(
            "meri sehat kaisi hai",
            "Saturn in house 8 se chronic pressure dikhta hai.",
            meta,
        )
        self.assertFalse(ok)
        self.assertTrue(any("wrong_house" in i or "invented" in i for i in issues))

    def test_allows_career_mention_without_drift_gate(self):
        meta = {
            "archetype": "respiratory_health",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        ok, issues = validate_health_llm_answer(
            "mujhse thandi bahut rehti hai",
            "Aapka career strong hai aur promotion jaldi milegi.",
            meta,
        )
        self.assertTrue(ok, issues)

    def test_allows_finance_mention_on_travel_health_without_unasked_gate(self):
        meta = {
            "archetype": "general_health",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        answer = (
            "Travel ke time 6th house Venus weak hai, isliye immunity low rehti hai. "
            "Paise ke mamle mein kharcha zyada hota hai aur unexpected expenses aate hain. "
            "Insurance ya financial planning faydemand hoga."
        )
        ok, issues = validate_health_llm_answer(
            "jab bhi travel karta hun koi na koi health issue aa jaata he aisa kyun",
            answer,
            meta,
        )
        self.assertTrue(ok, issues)

    def test_allows_finance_when_user_asked(self):
        meta = {
            "archetype": "general_health",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        ok, issues = validate_health_llm_answer(
            "travel pe health issue aur paisa kyun jata hai",
            "Safar me Saturn 6th ghar me hai, health weak hoti hai aur kharcha bhi badh jata hai.",
            meta,
        )
        self.assertTrue(ok, issues)

    def test_retry_feedback_mentions_issues(self):
        fb = build_health_validator_retry_feedback(
            ["template_sections"],
            "mujhse thandi bahut rehti hai",
        )
        self.assertIn("template_sections", fb)
        self.assertIn("HEALTH_ENGINE_EXECUTION_JSON", fb)

    def test_display_includes_check_rows(self):
        meta = {
            "archetype": "respiratory_health",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        display = build_health_validator_display(
            "mujhse thandi bahut rehti hai",
            "Saturn 6th ghar me hai, isliye thandi tendency dikhti hai.",
            meta,
            stored_audit={"attempts": 1, "passed": True},
        )
        self.assertTrue(display.get("applies"))
        self.assertTrue(display.get("passed"))
        self.assertGreaterEqual(len(display.get("checks") or []), 5)
        check_ids = {c.get("id") for c in display.get("checks") or []}
        self.assertNotIn("chart_proof", check_ids)
        self.assertNotIn("unasked_topics", check_ids)
        self.assertNotIn("question_drift", check_ids)

    def test_dna_style_blocks_long_answer(self):
        meta = {
            "archetype": "general_health",
            "answer_style": "short_2_3_lines",
            "answer_approach": "Use D1/D9 — short direct health read with planet+ghar proof.",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        long_ans = " ".join(["word"] * 80)
        ok, issues = validate_health_llm_answer(
            "mujhse mere health ke bare me jaana he",
            long_ans,
            meta,
        )
        self.assertFalse(ok)
        self.assertTrue(any(i.startswith("dna_style") for i in issues))

    def test_dna_plan_requires_chart_cite_when_plan_says_so(self):
        meta = {
            "archetype": "general_health",
            "answer_style": "short_2_3_lines",
            "answer_approach": "Use D1/D9 health chart JSON — plain language with chart evidence.",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        ok, issues = validate_health_llm_answer(
            "mujhse mere health ke bare me jaana he",
            "Aapki sehat thodi weak lag sakti hai, dhyan rakho.",
            meta,
        )
        self.assertFalse(ok)
        self.assertTrue(
            any(i in issues for i in ("dna_plan_missing_chart_cite",)),
            issues,
        )

    def test_dna_style_and_plan_pass_with_proof(self):
        meta = {
            "archetype": "general_health",
            "answer_style": "short_2_3_lines",
            "answer_approach": "Use D1/D9 health chart JSON — plain language with chart evidence.",
            "user_wants": "User wants to know about their health.",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        ok, issues = validate_health_llm_answer(
            "mujhse mere health ke bare me jaana he",
            "Moon 4th ghar me weak hai, isliye sehat me thodi sensitivity hai. Rest aur routine rakho.",
            meta,
        )
        self.assertTrue(ok, issues)

    def test_general_overview_plan_blocks_technical_answer(self):
        meta = {
            "archetype": "health_engine_execution_v1",
            "answer_style": "short_paragraph",
            "answer_approach": (
                "Provide a general overview of health aspects based on the chart, "
                "focusing on key health indicators without specific predictions or remedies"
            ),
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        bad = (
            "Aapki health moderate hai, par vitality low hai (vitality score 53/100). "
            "Mars 1st ghar me hai, Rahu H8 me chronic aur immunity issues dikha rahe hain. "
            "Saturn aur Mars Moon par aspect karke mental stress badha rahe hain. "
            "Venus 6th ghar me enemy sign me hai. Recovery average hai."
        )
        ok, issues = validate_health_llm_answer(
            "mujhse mere health ke bare me jaana he",
            bad,
            meta,
        )
        self.assertFalse(ok)
        self.assertTrue(
            any(
                i in issues
                for i in ("dna_plan_too_technical", "dna_plan_too_detailed_breakdown")
            ),
            issues,
        )

    def test_general_overview_plan_accepts_soft_answer(self):
        meta = {
            "archetype": "health_engine_execution_v1",
            "answer_style": "short_paragraph",
            "answer_approach": (
                "Provide a general overview of health aspects based on the chart, "
                "focusing on key health indicators without specific predictions or remedies"
            ),
            "user_wants": "User wants to know about their overall health.",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        good = (
            "Aapki kundli ke hisaab se overall health ki foundation theek dikh rahi hai, "
            "lekin stress, digestion aur energy balance par regular dhyan dena zaroori rahega. "
            "Kabhi-kabhi mental pressure ka asar physical health par bhi pad sakta hai, "
            "isliye healthy routine, achhi neend aur regular exercise beneficial rahenge. "
            "Yeh sirf long-term health tendencies batata hai, medical diagnosis nahi."
        )
        ok, issues = validate_health_llm_answer(
            "mujhse mere health ke bare me jaana he",
            good,
            meta,
        )
        self.assertTrue(ok, issues)

    def test_surgery_risk_probability_answer_passes(self):
        meta = {
            "archetype": "health_engine_execution_v1",
            "answer_style": "short_paragraph",
            "answer_approach": (
                "Provide a cautious prediction about the likelihood of surgery based on "
                "health indicators, emphasizing probabilities rather than certainties."
            ),
            "user_wants": (
                "User wants to know if there is a possibility that she will need to undergo "
                "an operation in the future."
            ),
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        good = (
            "Chart ke hisaab se operation ki possibility ko certainty ki tarah nahi bolna chahiye, "
            "lekin health side par kabhi medical procedure ya doctor intervention ki zarurat ban sakti hai. "
            "Saturn 6th ghar me health-pressure dikhata hai, isliye ise low-to-moderate tendency ki tarah lena sahi rahega. "
            "Regular checkup, symptoms ignore na karna aur doctor ki advice follow karna sabse important hai. "
            "Yeh medical diagnosis nahi, sirf kundli based probability reading hai."
        )
        ok, issues = validate_health_llm_answer(
            "kya mujhse kabhi operation ka samna karna padega",
            good,
            meta,
        )
        self.assertTrue(ok, issues)

    def test_surgery_risk_blocks_unsolicited_date(self):
        meta = {
            "archetype": "health_engine_execution_v1",
            "answer_style": "short_paragraph",
            "answer_approach": (
                "Provide a cautious prediction about the likelihood of surgery based on "
                "health indicators, emphasizing probabilities rather than certainties."
            ),
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        ok, issues = validate_health_llm_answer(
            "kya mujhse kabhi operation ka samna karna padega",
            "Saturn 6th ghar me hai, isliye operation March 2027 me hoga.",
            meta,
        )
        self.assertFalse(ok)
        self.assertIn("unsolicited_timing", issues)

    def test_blocks_after_max_retries(self):
        class _Msg:
            def __init__(self, content):
                self.content = content

        class _Choice:
            def __init__(self, content):
                self.message = _Msg(content)

        class _Resp:
            def __init__(self, content):
                self.choices = [_Choice(content)]

        class _Client:
            def __init__(self):
                self.n = 0

            class chat:
                class completions:
                    @staticmethod
                    def create(**_kwargs):
                        return _Client._next()

            _answers = [
                "Pollution se bacho aur pranayama karo.",
                "Pollution se bacho aur pranayama karo.",
                "Pollution se bacho aur pranayama karo.",
                "Pollution se bacho aur pranayama karo.",
            ]
            _i = 0

            @classmethod
            def _next(cls):
                content = cls._answers[min(cls._i, len(cls._answers) - 1)]
                cls._i += 1
                return _Resp(content)

        meta = {
            "archetype": "respiratory_health",
            "checks": {"health_engine_execution": _SAMPLE_EXECUTION},
        }
        text, audit = run_health_llm_validator_loop(
            _Client(),
            model="test",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=100,
            question="mujhse thandi bahut rehti hai kya karu",
            meta=meta,
        )
        self.assertFalse(text)
        self.assertFalse(audit.get("passed"))
        self.assertTrue(audit.get("final_block"))
        self.assertFalse(audit.get("released_anyway"))
        self.assertTrue(audit.get("final_issues") or audit.get("issues"))

    def test_allows_asthma_in_answer_when_user_asked_asthma(self):
        from ask_health.answer_guard import verify_health_answer

        ok, issues = verify_health_answer(
            "kya mujhse asthma he",
            "Chart me saans/3rd house sensitivity dikhti hai — asthma jaisi tendency ho sakti hai, lekin yeh medical diagnosis nahi.",
            {"archetype": "health_engine_execution_v1"},
        )
        self.assertTrue(ok, issues)

    def test_blocks_unasked_disease_name_in_answer(self):
        from ask_health.answer_guard import verify_health_answer

        ok, issues = verify_health_answer(
            "kya mujhse asthma he",
            "Aapko diabetes ki tendency dikh rahi hai chart me.",
            {"archetype": "health_engine_execution_v1"},
        )
        self.assertFalse(ok)
        self.assertIn("disease_name", issues)


if __name__ == "__main__":
    unittest.main()

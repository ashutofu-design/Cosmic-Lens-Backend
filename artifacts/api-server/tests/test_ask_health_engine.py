"""Smoke tests for ask_health routing + engines."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_health.classifier import classify_health_archetype, is_health_static_question
from ask_health.engine import run_health_static_engine
from ask_health.routing import resolve_health_archetype

_SAMPLE_KUNDLI = {
    "ascendant": "Leo",
    "planets": [
        {"name": "Sun", "house": 1, "sign": "Leo", "longitude": 120.0},
        {"name": "Moon", "house": 4, "sign": "Scorpio", "longitude": 220.0},
        {"name": "Mars", "house": 10, "sign": "Taurus", "longitude": 40.0},
        {"name": "Mercury", "house": 2, "sign": "Virgo", "longitude": 160.0},
        {"name": "Jupiter", "house": 5, "sign": "Sagittarius", "longitude": 250.0},
        {"name": "Venus", "house": 3, "sign": "Libra", "longitude": 190.0},
        {"name": "Saturn", "house": 7, "sign": "Aquarius", "longitude": 300.0},
        {"name": "Rahu", "house": 11, "sign": "Gemini", "longitude": 80.0},
        {"name": "Ketu", "house": 5, "sign": "Sagittarius", "longitude": 260.0},
    ],
    "currentDasha": {"maha": "Jupiter", "antar": "Saturn", "pratyantar": "Mercury"},
}

_FOUNDATION_10 = [
    ("Meri sehat kaisi hai chart me?", "overall_vitality"),
    ("Meri vitality strong hai?", "overall_vitality"),
    ("Chronic health issue ki tendency hai?", "chronic_tendency"),
    ("Stress aur anxiety chart me kya dikhta hai?", "mental_stress"),
    ("Surgery ka risk high hai kya?", "surgery_risk_tone"),
    ("Aage chal ke kya health risk hai?", "preventive_risk"),
    ("Recovery capacity strong hai?", "recovery_capacity"),
    ("Accident ka risk chart me?", "accident_risk"),
    ("Papa ki tabiyat kharab hai chart se batao", "parent_health"),
    ("Mujhe kaun si bimari hai chart se bata", "refuse_diagnosis"),
]


class TestAskHealthEngine(unittest.TestCase):
    def test_scope_vitality_chronic_mental_surgery(self):
        cases = [
            ("meri vitality strong hai?", "overall_vitality"),
            ("meri immunity strong hai?", "immune_health"),
            ("purani bimari ki tendency?", "chronic_tendency"),
            ("depression aur neend ki problem?", "mental_stress"),
            ("operation ka risk hai?", "surgery_risk_tone"),
            ("future health risk kya hai?", "preventive_risk"),
            ("recovery strong hai kya?", "recovery_capacity"),
            ("accident risk chart me?", "accident_risk"),
            ("sharab addiction chart se?", "addiction_support"),
            ("fertility chart me kaisi?", "reproductive_support"),
        ]
        for q, expected in cases:
            with self.subTest(q=q):
                self.assertTrue(is_health_static_question(q))
                self.assertEqual(classify_health_archetype(q), expected)

    def test_foundation_10_health_routes(self):
        for q, expected in _FOUNDATION_10:
            with self.subTest(q=q):
                self.assertTrue(is_health_static_question(q), q)
                self.assertEqual(classify_health_archetype(q), expected, q)

    def test_hard_guards(self):
        self.assertEqual(classify_health_archetype("kab marunga main?"), "refuse_death")
        from ask_health.timing_registry import is_health_timing_question
        from event_timing.timing_router import resolve_timing_domain

        self.assertTrue(is_health_timing_question("kab thik honga main?"))
        self.assertFalse(is_health_static_question("kab thik honga main?"))
        dom, _b, is_t = resolve_timing_domain("kab thik honga main?")
        self.assertTrue(is_t and dom == "health")

    def test_timing_decline_hard_guard_in_scope(self):
        from ask_health.timing_registry import is_health_timing_question

        self.assertFalse(is_health_timing_question("kab beemar honga?"))
        self.assertTrue(is_health_static_question("kab beemar honga?"))
        self.assertEqual(classify_health_archetype("kab beemar honga?"), "refuse_timing_decline")

    def test_static_health_outlook_not_timing(self):
        from ask_health.timing_registry import is_health_timing_question

        for q in (
            "Health kaisi rahegi?",
            "Meri health kaisi rahegi?",
            "Sehat kaisi rahegi?",
        ):
            with self.subTest(q=q):
                self.assertFalse(is_health_timing_question(q), q)
                self.assertTrue(is_health_static_question(q), q)
        self.assertTrue(is_health_timing_question("2027 me health kaisi hogi?"))
        self.assertFalse(is_health_static_question("2027 me health kaisi hogi?"))

    def test_health_static_overrides_llm_timing_flag(self):
        from ask_health.timing_registry import health_static_overrides_llm_timing

        llm_wrong = {
            "domain": "health",
            "is_timing": True,
            "interpretation": "health before marriage",
        }
        self.assertTrue(
            health_static_overrides_llm_timing("Health kaisi rahegi?", llm_wrong)
        )
        self.assertFalse(
            health_static_overrides_llm_timing("2027 me health kaisi hogi?", llm_wrong)
        )
        # LLM is_timing must not force health timing for outlook Q
        self.assertFalse(is_health_timing_question("Health kaisi rahegi?", llm_wrong))

    def test_resolve_override_llm(self):
        arch, reason = resolve_health_archetype(
            "stress aur anxiety?",
            llm_archetype="general_health",
        )
        self.assertEqual(arch, "mental_stress")
        self.assertIn("regex", reason)

    def test_engines_return_evidence(self):
        for arch in (
            "overall_vitality",
            "chronic_tendency",
            "mental_stress",
            "surgery_risk_tone",
            "preventive_risk",
            "recovery_capacity",
            "general_health",
        ):
            with self.subTest(archetype=arch):
                res = run_health_static_engine(
                    _SAMPLE_KUNDLI,
                    "health question",
                    archetype=arch,
                )
                self.assertEqual(res.archetype, arch)
                self.assertTrue(res.verdict)
                self.assertGreaterEqual(len(res.evidence), 2)
                payload = res.to_narrator_payload()
                self.assertIn("VERDICT:", payload)

    def test_hard_guards_cancer_death(self):
        cancer_cases = [
            ("kya mujhe cancer hai chart me?", "refuse_diagnosis"),
            ("Do I have cancer in my kundli?", "refuse_diagnosis"),
            ("mera cancer hoga kya?", "refuse_diagnosis"),
        ]
        for q, expected in cancer_cases:
            with self.subTest(q=q):
                self.assertEqual(classify_health_archetype(q), expected)
        death_cases = [
            ("kab marunga main?", "refuse_death"),
            ("death kab hogi meri?", "refuse_death"),
            ("when will I die?", "refuse_death"),
            ("kitni umar hai meri?", "refuse_death"),
        ]
        for q, expected in death_cases:
            with self.subTest(q=q):
                self.assertEqual(classify_health_archetype(q), expected)

    def test_body_system_subdomains(self):
        cases = [
            ("pet dard aur acidity?", "digestive_health"),
            ("heart weak hai chart me?", "cardio_health"),
            ("saans phool jati hai?", "respiratory_health"),
            ("immunity weak hai?", "immune_health"),
            ("knee pain chronic?", "musculoskeletal_health"),
        ]
        for q, expected in cases:
            with self.subTest(q=q):
                self.assertEqual(classify_health_archetype(q), expected)

    def test_hard_guard_skips_llm(self):
        res = run_health_static_engine(
            _SAMPLE_KUNDLI,
            "mujhe kaun si bimari hai",
            archetype="refuse_diagnosis",
        )
        self.assertTrue(res.skip_llm)
        self.assertTrue(res.template_text)


if __name__ == "__main__":
    unittest.main()

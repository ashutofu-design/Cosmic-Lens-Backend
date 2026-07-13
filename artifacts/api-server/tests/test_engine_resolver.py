"""Golden tests — one static engine winner per question."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_engine_resolver import resolve_static_engine_route


class EngineResolverGoldenTests(unittest.TestCase):
    def _resolve(
        self,
        question: str,
        *,
        flags: dict[str, bool],
        domain: str = "general",
        archetype: str | None = None,
    ):
        intent = {"domain": domain, "mr_archetype": archetype, "routed_domain": domain}
        if archetype:
            intent["routed_archetype"] = archetype
        final, route = resolve_static_engine_route(
            question,
            flags=flags,
            llm_intent=intent,
            llm_intent_admin=intent,
            is_timing=False,
        )
        active = [k for k, v in final.items() if v]
        return final, route, active

    def test_love_dil_beats_health_regex(self):
        q = "Main jisse pyaar karta hu, kya wo bhi dil se mujhse utna hi pyaar karti hai"
        final, route, active = self._resolve(
            q,
            flags={"health": True, "mr": True},
            domain="love",
            archetype="one_sided_love",
        )
        self.assertEqual(active, ["mr"])
        self.assertEqual(route.engine_key, "mr")
        self.assertEqual(route.reason, "llm_domain:love")
        self.assertFalse(final["health"])

    def test_true_love_not_health(self):
        q = "Kya meri kundli me sacha pyaar true love milne ka yog likha hai"
        final, route, active = self._resolve(
            q,
            flags={"health": True, "mr": True},
            domain="love",
            archetype="dating_courtship",
        )
        self.assertEqual(active, ["mr"])
        self.assertEqual(route.engine_key, "mr")

    def test_health_domain_keeps_health(self):
        q = "dil ki sehat kaisi hai chart me?"
        final, route, active = self._resolve(
            q,
            flags={"health": True, "mr": False},
            domain="health",
            archetype="cardio_health",
        )
        self.assertEqual(active, ["health"])
        self.assertEqual(route.engine_key, "health")

    def test_single_winner_when_multiple_flags(self):
        q = "meri naukri kab milegi"
        final, route, active = self._resolve(
            q,
            flags={"career": True, "health": True},
            domain="career",
            archetype="general_career",
        )
        self.assertEqual(len(active), 1)
        self.assertEqual(route.engine_key, "career")

    def test_love_dil_general_domain_still_mr(self):
        q = "Main jisse pyaar karta hu, kya wo bhi dil se mujhse utna hi pyaar karti hai"
        final, route, active = self._resolve(
            q,
            flags={"health": True, "mr": False},
            domain="general",
            archetype=None,
        )
        self.assertEqual(active, ["mr"])
        self.assertEqual(route.engine_key, "mr")
        final, route, active = resolve_static_engine_route(
            "shaadi kab hogi",
            flags={"mr": True},
            llm_intent={"domain": "marriage", "is_timing": True},
            is_timing=True,
        )
        self.assertTrue(route.is_timing)
        self.assertIsNone(route.engine_key)
        self.assertTrue(final["mr"])

    def test_relationship_batch_beats_health_when_llm_wrong(self):
        """User relationship Qs must not lose to health_engine when LLM domain=health."""
        cases = [
            (
                "Kya mera partner sach me mujhse pyaar karta hai?",
                "partner_nature",
            ),
            (
                "Kya mera partner loyal aur faithful hai?",
                "loyalty_trust",
            ),
            (
                "Kya hum dono compatible hain?",
                "compatibility",
            ),
            (
                "Relationship me problems kis wajah se aa rahi hain?",
                "general_mr",
            ),
        ]
        for q, arch in cases:
            with self.subTest(q=q[:48]):
                final, route, active = self._resolve(
                    q,
                    flags={"health": True, "mr": True},
                    domain="health",
                    archetype=arch,
                )
                self.assertEqual(active, ["mr"], msg=q)
                self.assertEqual(route.engine_key, "mr", msg=q)
                self.assertFalse(final["health"], msg=q)

    def test_relationship_healthy_not_health_engine(self):
        q = "Kya relationship healthy rahegi ya stressful?"
        from ask_health.health_registry import is_health_static_question

        self.assertFalse(is_health_static_question(q))
        final, route, active = self._resolve(
            q,
            flags={"health": True, "mr": True},
            domain="health",
            archetype="general_mr",
        )
        self.assertEqual(active, ["mr"])
        self.assertEqual(route.engine_key, "mr")

    def test_cross_domain_affect_stays_mr_not_open_chart(self):
        from ask_chart_open_qa import is_native_self_chart_interpretation_question
        from ask_mr import run_mr_static_engine

        k = {
            "ascendant": "Sagittarius",
            "planets": [{"name": "Moon", "sign": "Gemini", "house": 7}],
        }
        for q in (
            "Financial issues relationship ko affect karenge?",
            "Career relationship ko affect karega?",
            "Distance ya foreign settlement relationship ko affect karegi?",
        ):
            with self.subTest(q=q[:40]):
                self.assertFalse(is_native_self_chart_interpretation_question(q))
                res = run_mr_static_engine(k, q, wants_explain=False)
                self.assertEqual(res.archetype, "general_mr")

    def test_travel_context_health_beats_travel_engine(self):
        q = "me jab bhi travel karta hun koi na koi health issue aa jaata he aisa kyun"
        final, route, active = self._resolve(
            q,
            flags={"health": True, "travel": True},
            domain="travel",
            archetype="general_travel",
        )
        self.assertEqual(active, ["health"], active)
        self.assertEqual(route.engine_key, "health")
        self.assertFalse(final["travel"])


if __name__ == "__main__":
    unittest.main()

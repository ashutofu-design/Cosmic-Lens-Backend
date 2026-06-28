"""Property + vehicle timing — 4 user questions + bucket routing."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.property.property_timing_v1 import (
    classify_property_timing_bucket,
    compute_property_window,
)
from event_timing.vehicle.vehicle_timing_v1 import (
    classify_vehicle_timing_bucket,
    compute_vehicle_window,
    format_vehicle_timing_for_prompt,
)
from event_timing.routing_audit import audit_question_routing
from event_timing.timing_router import format_timing_block, resolve_timing_domain, run_timing_engine

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Saturn", "sign": "Virgo", "house": 10},
        {"name": "Mars", "sign": "Cancer", "house": 8},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Mercury", "sign": "Aries", "house": 5},
        {"name": "Jupiter", "sign": "Pisces", "house": 4},
        {"name": "Rahu", "sign": "Aquarius", "house": 3},
        {"name": "Sun", "sign": "Capricorn", "house": 2},
    ],
    "currentDasha": {"mahadasha": "Jupiter", "antardasha": "Venus"},
}

USER_FOUR: list[tuple[str, str, str, str]] = [
    (
        "Mera khud ka ghar makaan kab banega ya registry kab hogi?",
        "property",
        "registry",
        "property_timing",
    ),
    (
        "Nayi gaadi car bike kab khareedunga?",
        "vehicle",
        "buy",
        "vehicle_timing",
    ),
    (
        "Ancestral property pustaini zameen ka vivaad kab suljhega aur hissa kab milega?",
        "property",
        "dispute",
        "property_timing",
    ),
    (
        "Apna purana ghar property kab bikega sale kab hogi?",
        "property",
        "sell",
        "property_timing",
    ),
]


class TestPropertyVehicleTiming(unittest.TestCase):
    def test_user_four_routing(self):
        for q, exp_dom, exp_bucket, eng_frag in USER_FOUR:
            with self.subTest(q=q[:50]):
                dom, bkt, is_t = resolve_timing_domain(q)
                r = audit_question_routing(q)
                self.assertTrue(is_t, q)
                self.assertEqual(dom, exp_dom, q)
                self.assertEqual(r.domain, exp_dom, q)
                self.assertIn(eng_frag, r.engine, q)
                if exp_dom == "property":
                    self.assertEqual(classify_property_timing_bucket(q), exp_bucket)
                else:
                    self.assertEqual(classify_vehicle_timing_bucket(q), exp_bucket)

    def test_property_buckets_new(self):
        self.assertEqual(
            classify_property_timing_bucket(
                "Paitrik zameen hissa kab milega?",
            ),
            "inheritance",
        )
        self.assertEqual(
            classify_property_timing_bucket(
                "Property vivaad kab suljhega?",
            ),
            "dispute",
        )
        self.assertEqual(
            classify_property_timing_bucket("Ghar bechega kab sale?"),
            "sell",
        )

    def test_vehicle_engine_window(self):
        raw = compute_vehicle_window(
            SAMPLE_KUNDLI, {}, {}, None, "Gaadi kab khareedun?",
        )
        self.assertEqual(raw.get("domain"), "vehicle")
        self.assertIn(raw.get("bucket"), ("buy", "upgrade", "sell"))
        block = format_vehicle_timing_for_prompt(raw)
        self.assertIn("VEHICLE TIMING ENGINE", block)

    def test_new_car_kab_lunga_is_vehicle_timing(self):
        from ask_vehicle.timing_registry import is_vehicle_timing_question
        from ask_health.health_registry import is_health_static_question
        from ask_intent_fidelity import repair_llm_intent

        q = "Main new car kab lunga"
        self.assertTrue(is_vehicle_timing_question(q))
        self.assertFalse(is_health_static_question(q))
        repaired = repair_llm_intent(
            q,
            {
                "domain": "health",
                "is_timing": True,
                "health_archetype": "respiratory_health",
                "source": "llm",
                "confidence": 0.9,
            },
        )
        self.assertEqual(repaired.get("domain"), "vehicle")
        self.assertTrue(repaired.get("is_timing"))
        self.assertIsNone(repaired.get("health_archetype"))

    def test_property_dispute_guards(self):
        raw = compute_property_window(
            SAMPLE_KUNDLI, {}, {}, None,
            "Ancestral property vivaad kab suljhega?",
        )
        self.assertEqual(raw.get("bucket"), "dispute")
        guards = " ".join(raw.get("brand_safety_warnings") or [])
        self.assertIn("vivaad", guards.lower())

    def test_property_mars_saturn_karakas_only(self):
        raw = compute_property_window(SAMPLE_KUNDLI, {}, {}, None, "Ghar registry kab?")
        karakas = raw.get("property_karakas") or []
        self.assertEqual(len(karakas), 2)
        self.assertTrue(all("Mangal" in k or "Shani" in k for k in karakas))
        joined = " ".join(raw.get("factors") or []).lower()
        self.assertNotIn("venus", joined)
        self.assertNotIn("moon", joined)

    def test_router_vehicle_block(self):
        ctx = run_timing_engine(
            "Bike kab khareedun?", SAMPLE_KUNDLI, {}, {}, None, {"is_timing": True},
        )
        self.assertEqual(ctx.engine_status, "ready")
        self.assertIn("VEHICLE TIMING ENGINE", format_timing_block(ctx))


if __name__ == "__main__":
    unittest.main()

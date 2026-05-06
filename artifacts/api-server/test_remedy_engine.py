"""Unit tests for the standalone Remedy Engine v1.0.

Covers:
- Public API basics (health/marriage/career topics)
- Tier ordering (practical FIRST, vedic LAST in render)
- Catalog completeness for top planets per topic
- Conflict checker (gemstone enemy pairs, severity guard, overload)
- Substitution engine (vegetarian, no-fast, no-temple)
- Stack builder (21-day routine assembly)
- Tier-note normalization (None / unknown → safe default)
- Render output format compliance with locked_facts schema
"""
from __future__ import annotations

import unittest

from remedy import get_remedies, render_for_locked_facts
from remedy.conflict_check import check_conflicts
from remedy.substitutions import apply_substitutions
from remedy.stack_builder import build_stack
from remedy.catalog import CATALOG, SYSTEM_PRACTICES


class TestCatalogCoverage(unittest.TestCase):
    def test_all_topics_have_9_grahas(self):
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter",
                      "Venus", "Saturn", "Rahu", "Ketu"}
        for topic in ("health", "marriage", "career", "money", "business"):
            self.assertEqual(set(CATALOG[topic].keys()), expected,
                              f"{topic} missing planets")

    def test_every_entry_has_3_tiers(self):
        for topic, planets in CATALOG.items():
            for planet, entry in planets.items():
                for tier in ("practical", "ayurvedic", "vedic"):
                    self.assertIn(tier, entry,
                                    f"{topic}.{planet} missing {tier}")
                # practical tier MUST carry a KPI (user mandate)
                self.assertIn("kpi", entry["practical"],
                                f"{topic}.{planet} practical missing kpi")
                self.assertTrue(entry["practical"].get("kpi"),
                                  f"{topic}.{planet} kpi empty")
                # vedic tier MUST carry day + mantra + free_alt
                self.assertTrue(entry["vedic"].get("mantra"))
                self.assertTrue(entry["vedic"].get("free_alt"))


class TestGetRemediesHealth(unittest.TestCase):
    def setUp(self):
        self.planets = [
            {"name": "Mars",    "score": 14.25},
            {"name": "Jupiter", "score": 11.67},
            {"name": "Sun",     "score": 11.50},
        ]
        self.areas = ["blood", "muscles", "inflammation"]

    def test_basic_health_remedy(self):
        r = get_remedies("health", self.planets, self.areas,
                            severity="urgent_consult")
        self.assertTrue(r["available"])
        self.assertEqual(r["severity"], "urgent_consult")
        self.assertEqual(len(r["planet_remedies"]), 3)
        names = [p["planet"] for p in r["planet_remedies"]]
        self.assertEqual(names, ["Mars", "Jupiter", "Sun"])
        # Each planet has all 3 tiers
        for pr in r["planet_remedies"]:
            self.assertIn("practical", pr)
            self.assertIn("ayurvedic", pr)
            self.assertIn("vedic", pr)
            self.assertIn("kpi", pr["practical"])

    def test_severity_guard_for_urgent(self):
        r = get_remedies("health", self.planets, self.areas,
                            severity="urgent_consult")
        kinds = [c["kind"] for c in r["conflicts"]]
        self.assertIn("SEVERITY_GUARD", kinds)

    def test_doctor_referral_for_consult_or_urgent(self):
        r = get_remedies("health", self.planets, self.areas,
                            severity="consult")
        self.assertIsNotNone(r["doctor_referral_hint"])
        self.assertIn("hematologist", r["doctor_referral_hint"].lower())

    def test_no_referral_for_monitor(self):
        r = get_remedies("health", self.planets, self.areas,
                            severity="monitor")
        self.assertIsNone(r["doctor_referral_hint"])

    def test_unknown_severity_normalized_to_consult(self):
        r = get_remedies("health", self.planets, self.areas,
                            severity="garbage")
        self.assertEqual(r["severity"], "consult")

    def test_render_practical_before_vedic(self):
        r = get_remedies("health", self.planets, self.areas,
                            severity="urgent_consult")
        text = render_for_locked_facts(r)
        # First Mars block must show practical BEFORE vedic
        idx_p = text.find("1️⃣ practical")
        idx_a = text.find("2️⃣ ayurvedic")
        idx_v = text.find("3️⃣ vedic")
        self.assertGreater(idx_p, 0)
        self.assertGreater(idx_a, idx_p)
        self.assertGreater(idx_v, idx_a)


class TestGetRemediesMarriageCareer(unittest.TestCase):
    def test_marriage_basic(self):
        r = get_remedies("marriage",
                            [{"name": "Venus", "score": 10.0},
                             {"name": "Jupiter", "score": 9.0}],
                            ["communication", "harmony"],
                            severity="supportive")
        self.assertTrue(r["available"])
        self.assertEqual(r["topic"], "marriage")
        self.assertEqual(len(r["planet_remedies"]), 2)
        self.assertIn("opportunity", r["universal_disclaimer"])
        # No medical referral for marriage
        self.assertIsNone(r["doctor_referral_hint"])

    def test_career_basic(self):
        r = get_remedies("career",
                            [{"name": "Saturn", "score": 12.0},
                             {"name": "Mercury", "score": 9.0}],
                            ["skill_depth", "stability"],
                            severity="watchful")
        self.assertTrue(r["available"])
        self.assertEqual(r["topic"], "career")
        names = [p["planet"] for p in r["planet_remedies"]]
        self.assertEqual(names, ["Saturn", "Mercury"])
        self.assertIn("amplify", r["universal_disclaimer"])

    def test_unknown_topic_returns_unavailable(self):
        r = get_remedies("astronaut", [{"name": "Mars"}], [], "any")
        self.assertFalse(r["available"])


class TestGetRemediesMoneyBusiness(unittest.TestCase):
    def test_money_basic(self):
        r = get_remedies("money",
                            [{"name": "Jupiter", "score": 12.0},
                             {"name": "Venus",   "score": 9.0},
                             {"name": "Mercury", "score": 8.0}],
                            ["savings", "investing", "expense_control"],
                            severity="supportive")
        self.assertTrue(r["available"])
        self.assertEqual(r["topic"], "money")
        self.assertEqual(len(r["planet_remedies"]), 3)
        names = [p["planet"] for p in r["planet_remedies"]]
        self.assertEqual(names, ["Jupiter", "Venus", "Mercury"])
        # Engine-wide promise: practical action present on every planet
        for pr in r["planet_remedies"]:
            self.assertTrue(pr["practical"]["action"])
            self.assertTrue(pr["practical"]["kpi"])
        # Money disclaimer + no medical referral
        self.assertIn("financial discipline", r["universal_disclaimer"])
        self.assertIsNone(r["doctor_referral_hint"])
        # System practices (money areas) wired
        sys_keys = [s["system"] for s in r["system_practices"]]
        self.assertIn("savings", sys_keys)

    def test_business_basic(self):
        r = get_remedies("business",
                            [{"name": "Mercury", "score": 11.0},
                             {"name": "Saturn",  "score": 10.0},
                             {"name": "Jupiter", "score": 9.0}],
                            ["cashflow", "scaling", "founders_fit"],
                            severity="watchful")
        self.assertTrue(r["available"])
        self.assertEqual(r["topic"], "business")
        names = [p["planet"] for p in r["planet_remedies"]]
        self.assertEqual(names, ["Mercury", "Saturn", "Jupiter"])
        self.assertIn("founder discipline", r["universal_disclaimer"])
        sys_keys = [s["system"] for s in r["system_practices"]]
        self.assertIn("cashflow", sys_keys)

    def test_money_unknown_severity_normalises_to_watchful(self):
        r = get_remedies("money",
                            [{"name": "Jupiter", "score": 5}],
                            ["savings"], severity="garbage")
        self.assertEqual(r["severity"], "watchful")

    def test_business_render_contains_practical_first(self):
        r = get_remedies("business",
                            [{"name": "Mercury", "score": 11.0}],
                            ["cashflow"], severity="supportive")
        text = render_for_locked_facts(r)
        self.assertIn("BUSINESS REMEDIES", text)
        idx_p = text.find("1️⃣ practical")
        idx_v = text.find("3️⃣ vedic")
        self.assertGreater(idx_p, 0)
        self.assertGreater(idx_v, idx_p)

    def test_money_render_contains_disclaimer_and_tier_note(self):
        r = get_remedies("money",
                            [{"name": "Mars", "score": 8}],
                            ["debt"], severity="watchful")
        text = render_for_locked_facts(r)
        self.assertIn("MONEY REMEDIES", text)
        self.assertIn("TIER NOTE", text)
        self.assertIn("financial discipline", text)


class TestConflicts(unittest.TestCase):
    def test_enemy_pair_detected(self):
        rems = [{"planet": "Sun"}, {"planet": "Saturn"}]
        warns = check_conflicts(rems, severity="preventive", topic="health")
        kinds = [w["kind"] for w in warns]
        self.assertIn("GEMSTONE_PAIR_ENEMY", kinds)

    def test_overload_detected(self):
        rems = [{"planet": "Sun"}, {"planet": "Mars"},
                  {"planet": "Jupiter"}]
        warns = check_conflicts(rems, severity="preventive", topic="health")
        kinds = [w["kind"] for w in warns]
        self.assertIn("GEMSTONE_OVERLOAD", kinds)

    def test_severity_guard_only_for_urgent_health(self):
        rems = [{"planet": "Mars"}]
        w_urgent = check_conflicts(rems, severity="urgent_consult", topic="health")
        w_career = check_conflicts(rems, severity="urgent_consult", topic="career")
        self.assertTrue(any(w["kind"] == "SEVERITY_GUARD" for w in w_urgent))
        self.assertFalse(any(w["kind"] == "SEVERITY_GUARD" for w in w_career))


class TestSubstitutions(unittest.TestCase):
    def test_vegetarian_swaps_milk_pearl(self):
        rems = [{"planet": "Moon",
                   "vedic": {"donation": "Milk + white rice Monday",
                              "gemstone": "Moti (Pearl) silver"}}]
        out, swaps = apply_substitutions(rems, {"vegan": True})
        kinds = [s["constraint"] for s in swaps]
        self.assertIn("vegan", kinds)
        # Architect-fix May 6 2026: substitutions now actually replace
        # the conflicting term (annotation-only was a foot-gun).
        self.assertNotIn("Pearl", out[0]["vedic"]["gemstone"])
        self.assertIn("Moonstone", out[0]["vedic"]["gemstone"])
        self.assertIn("vegan", out[0]["vedic"]["gemstone"].lower())

    def test_no_fast_replaces_vrat(self):
        rems = [{"planet": "Moon",
                   "vedic": {"free_alt": "Monday vrat (one-meal) + Shiva temple"}}]
        out, swaps = apply_substitutions(rems, {"no_fast": True})
        constraints = [s["constraint"] for s in swaps]
        self.assertIn("no_fast", constraints)

    def test_no_user_facts_passthrough(self):
        rems = [{"planet": "Moon", "vedic": {"donation": "Milk Monday"}}]
        out, swaps = apply_substitutions(rems, None)
        self.assertEqual(out, rems)
        self.assertEqual(swaps, [])


class TestStackBuilder(unittest.TestCase):
    def test_stack_assembles_morning_evening_weekly(self):
        rems = [{
            "planet": "Mars",
            "practical": {"action": "30-min walk morning + skip alcohol",
                          "kpi": "BP < 130/85"},
            "ayurvedic": {"practice": "Sheetali pranayama 10 rounds"},
            "vedic": {"day": "Tuesday", "mantra": "Om Ang Angarakaya Namah",
                       "count": "108"},
        }]
        sp = [{"system": "blood", "practice": "Anar juice + tulsi water"}]
        stack = build_stack(rems, sp, duration_days=21, topic="health")
        self.assertEqual(stack["duration_days"], 21)
        self.assertTrue(any("Mars" in m for m in stack["morning"]))
        self.assertTrue(any("Sheetali" in e for e in stack["evening"]))
        self.assertTrue(any("Tuesday" in w for w in stack["weekly"]))
        self.assertTrue(any("BP" in t for t in stack["track"]))


class TestRenderOutput(unittest.TestCase):
    def test_render_empty_when_unavailable(self):
        self.assertEqual(render_for_locked_facts({"available": False}), "")
        self.assertEqual(render_for_locked_facts(None), "")

    def test_render_contains_disclaimer_and_tier_note(self):
        r = get_remedies("health",
                            [{"name": "Mars", "score": 14}],
                            ["blood"], severity="urgent_consult")
        text = render_for_locked_facts(r)
        self.assertIn("HEALTH REMEDIES", text)
        self.assertIn("⚠", text)
        self.assertIn("TIER NOTE", text)
        self.assertIn("doctor", text.lower())

    def test_render_contains_kpi_and_cost(self):
        r = get_remedies("health",
                            [{"name": "Mars", "score": 14}],
                            ["blood"], severity="preventive")
        text = render_for_locked_facts(r)
        self.assertIn("KPI", text)
        self.assertIn("₹ cost", text)


if __name__ == "__main__":
    unittest.main()

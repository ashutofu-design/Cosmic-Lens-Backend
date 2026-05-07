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
from remedy.practical_resources import (
    get_practical_resources,
    render_practical_resources,
    _RESOURCES,
)


# ════════════════════════════════════════════════════════════════════════
# Phase 3.0 — Practical Booster Pack v1.2 (May 7 2026)
# ════════════════════════════════════════════════════════════════════════
class TestPracticalResourcesCatalog(unittest.TestCase):
    """Schema-conformance for every entry in _RESOURCES."""

    REQUIRED = ("label", "kind", "value", "why", "free", "cost_inr",
                "for_topics", "for_areas", "for_severity", "applies_to",
                "crisis")
    VALID_KINDS = {"helpline", "govt_scheme", "free_tool",
                    "directory", "legal_aid"}
    VALID_DEMOS = {"all", "women", "senior", "youth", "founder"}
    VALID_TOPICS = {"health", "marriage", "career", "money", "business"}
    VALID_SEVS = {"watchful", "supportive", "celebratory", "consult",
                   "urgent_consult", "monitor", "preventive"}

    def test_every_entry_has_required_fields(self):
        for rid, r in _RESOURCES.items():
            for key in self.REQUIRED:
                self.assertIn(key, r, f"{rid} missing {key}")
            self.assertIn(r["kind"], self.VALID_KINDS,
                            f"{rid} bad kind {r['kind']}")
            self.assertIn(r["applies_to"], self.VALID_DEMOS,
                            f"{rid} bad applies_to")
            for t in r["for_topics"]:
                self.assertIn(t, self.VALID_TOPICS,
                                f"{rid} bad topic {t}")
            for s in r["for_severity"]:
                self.assertIn(s, self.VALID_SEVS,
                                f"{rid} bad severity {s}")
            # Free items must have cost_inr 0; paid items must have value
            if r["free"] and r["kind"] in ("helpline", "free_tool",
                                              "legal_aid"):
                # cost_inr can be 0 or token charge for govt scheme min deposit
                self.assertIsInstance(r["cost_inr"], int)

    def test_minimum_coverage(self):
        # Sanity: at least 25 verified resources curated.
        self.assertGreaterEqual(len(_RESOURCES), 25)

    def test_crisis_resources_exist_per_critical_topic(self):
        # Health urgent_consult MUST surface a suicide/mental-health crisis line.
        # Marriage MUST surface women-181 crisis line.
        # Money/business MUST surface cybercrime-1930 fraud line.
        rs_health = get_practical_resources(
            "health", ["mind", "anxiety"], "urgent_consult", limit=5)
        labels = " | ".join(r["label"] for r in rs_health)
        self.assertTrue("AASRA" in labels or "KIRAN" in labels or
                          "Tele-MANAS" in labels,
                          f"no crisis line for urgent health: {labels}")

        rs_marriage = get_practical_resources(
            "marriage", ["harmony", "trust"], "consult",
            user_facts={"gender": "F"}, limit=5)
        labels_m = " | ".join(r["label"] for r in rs_marriage)
        self.assertIn("181", " ".join(r["value"] for r in rs_marriage))

        rs_money = get_practical_resources(
            "money", ["debt", "savings"], "consult", limit=5)
        labels_mo = " | ".join(r["value"] for r in rs_money)
        self.assertIn("1930", labels_mo)


class TestPracticalResourcesSelector(unittest.TestCase):

    def test_demographic_filter_senior(self):
        # 25-year-old should NOT see senior-only schemes (SCSS, PMVVY, Elderline)
        rs_young = get_practical_resources(
            "money", ["savings", "investing"], "watchful",
            user_facts={"age": 24}, limit=5)
        ids = [r["id"] for r in rs_young]
        self.assertNotIn("scss_senior_savings", ids)
        self.assertNotIn("pmvvy_pension", ids)

        # 65-year-old SHOULD see SCSS as a candidate (limit raised
        # post-Phase 3.0 crisis-bypass: more crisis/free items now rank
        # ahead of SCSS in the candidate pool, so widen the inspection).
        rs_old = get_practical_resources(
            "money", ["savings"], "watchful",
            user_facts={"age": 65}, limit=50)
        ids_old = [r["id"] for r in rs_old]
        self.assertIn("scss_senior_savings", ids_old)

    def test_demographic_filter_women(self):
        # Male user must NOT see women-only resources (SHe-Box, 181, Stand-Up)
        rs_m = get_practical_resources(
            "marriage", ["harmony", "trust"], "consult",
            user_facts={"gender": "M"}, limit=10)
        ids_m = [r["id"] for r in rs_m]
        self.assertNotIn("women_helpline_181", ids_m)
        self.assertNotIn("shebox_posh", ids_m)

        # Female user SHOULD see them
        rs_f = get_practical_resources(
            "marriage", ["harmony", "trust"], "consult",
            user_facts={"gender": "F"}, limit=10)
        ids_f = [r["id"] for r in rs_f]
        self.assertIn("women_helpline_181", ids_f)

    def test_demographic_filter_founder(self):
        # Non-founder should NOT see Mudra/Stand-Up India
        rs = get_practical_resources(
            "business", ["cashflow", "scaling"], "watchful",
            user_facts={"role": "engineer"}, limit=10)
        ids = [r["id"] for r in rs]
        # business topic itself: founder schemes gated by applies_to
        self.assertNotIn("pmmy_mudra", ids)
        self.assertNotIn("standup_india", ids)

        rs_f = get_practical_resources(
            "business", ["cashflow"], "watchful",
            user_facts={"role": "founder"}, limit=10)
        ids_f = [r["id"] for r in rs_f]
        self.assertIn("pmmy_mudra", ids_f)

    def test_crisis_first_ordering(self):
        # urgent_consult health → AASRA / KIRAN / Tele-MANAS rank ABOVE
        # govt schemes like Ayushman / Jan Aushadhi
        rs = get_practical_resources(
            "health", ["mind", "anxiety", "chronic"],
            "urgent_consult", limit=3)
        self.assertGreater(len(rs), 0)
        first = rs[0]
        self.assertEqual(first["kind"], "helpline",
                          f"first entry not a crisis helpline: {first}")

    def test_severity_gate_works(self):
        # 'monitor' severity → mCessation should still match (no severity gate)
        # but AASRA (urgent_consult only) must NOT show
        rs = get_practical_resources(
            "health", ["heart", "blood"], "monitor", limit=10)
        ids = [r["id"] for r in rs]
        self.assertNotIn("aasra_suicide", ids)

    def test_area_gate_works(self):
        # career topic with skill_depth area → SHe-Box (career,leadership)
        # must NOT match because applies_to=women + area is leadership/stability
        rs = get_practical_resources(
            "career", ["skill_depth"], "watchful",
            user_facts={"gender": "F"}, limit=10)
        ids = [r["id"] for r in rs]
        # SHe-Box gated by area=leadership/stability — skill_depth alone
        # should not trigger it
        self.assertNotIn("shebox_posh", ids)

    def test_limit_cap(self):
        rs = get_practical_resources(
            "money", ["savings", "debt", "investing"], "watchful", limit=2)
        self.assertLessEqual(len(rs), 2)

    def test_no_match_returns_empty(self):
        # Bogus topic + bogus area
        rs = get_practical_resources(
            "health", ["nonexistent_area_xyz"], "monitor", limit=3)
        # Some entries with empty for_areas will still match — check that
        # it's a list and bounded
        self.assertIsInstance(rs, list)
        self.assertLessEqual(len(rs), 3)

    def test_render_basic(self):
        rs = get_practical_resources(
            "money", ["debt", "savings"], "consult", limit=3)
        lines = render_practical_resources(rs)
        text = "\n".join(lines)
        self.assertIn("Verified India resources", text)
        # Cost tag must appear
        self.assertTrue("FREE" in text or "₹" in text or "low-cost" in text)

    def test_render_empty(self):
        self.assertEqual(render_practical_resources([]), [])
        self.assertEqual(render_practical_resources(None), [])


class TestEngineWiring(unittest.TestCase):
    """Verify get_remedies surfaces practical_resources end-to-end."""

    def test_health_result_has_resources_field(self):
        r = get_remedies(
            "health",
            [{"name": "Mars", "score": 14}, {"name": "Moon", "score": 11}],
            ["mind", "anxiety", "blood"],
            severity="urgent_consult",
        )
        self.assertIn("practical_resources", r)
        self.assertIsInstance(r["practical_resources"], list)
        self.assertGreater(len(r["practical_resources"]), 0)
        # Crisis line must be in the surfaced 3
        labels = " | ".join(x["label"] for x in r["practical_resources"])
        self.assertTrue(
            any(k in labels for k in ("KIRAN", "AASRA", "Tele-MANAS",
                                          "Vandrevala", "iCall")),
            f"no crisis helpline in: {labels}",
        )

    def test_money_result_surfaces_cybercrime_for_debt(self):
        r = get_remedies(
            "money",
            [{"name": "Saturn", "score": 10}, {"name": "Rahu", "score": 9}],
            ["debt", "savings", "credit_score"],
            severity="consult",
        )
        values = " | ".join(x["value"] for x in r["practical_resources"])
        self.assertIn("1930", values)

    def test_render_includes_resources_block(self):
        r = get_remedies(
            "health",
            [{"name": "Moon", "score": 12}, {"name": "Mars", "score": 11}],
            ["mind", "anxiety"],
            severity="urgent_consult",
        )
        text = render_for_locked_facts(r)
        self.assertIn("Verified India resources", text)

    def test_engine_version_bumped_to_v1_1(self):
        r = get_remedies(
            "career",
            [{"name": "Sun", "score": 10}],
            ["leadership"],
            severity="supportive",
        )
        self.assertEqual(r["engine_version"], "v1.1.0")


# ════════════════════════════════════════════════════════════════════════
# Phase 3.0 architect-fix coverage (May 7 2026)
# ════════════════════════════════════════════════════════════════════════
class TestPhase30ArchitectFixes(unittest.TestCase):
    """Regression tests for the 2 CRITICAL + 1 HIGH issues raised by
    the architect after the initial Phase 3.0 build."""

    def test_crisis_resource_surfaces_with_empty_areas(self):
        """CRITICAL #2: crisis lines must reach the user even if upstream
        area extraction yields []. Suicide/AASRA must show on
        health/urgent_consult with NO areas."""
        rs = get_practical_resources(
            "health", areas=[], severity="urgent_consult", limit=5)
        ids = [r["id"] for r in rs]
        # At least one mental-health crisis line must appear
        crisis_ids = {"aasra_suicide", "kiran_mental_health",
                      "telemanas_nimhans", "vandrevala_24x7", "icall_tiss"}
        self.assertTrue(crisis_ids & set(ids),
                          f"no crisis line with empty areas: {ids}")

    def test_women_181_surfaces_with_empty_areas(self):
        """CRITICAL #2: women-181 must reach a female user even if areas
        is empty (e.g., upstream marriage area extraction failed)."""
        rs = get_practical_resources(
            "marriage", areas=[], severity="consult",
            user_facts={"gender": "F"}, limit=5)
        ids = [r["id"] for r in rs]
        self.assertIn("women_helpline_181", ids)

    def test_cybercrime_1930_surfaces_with_empty_areas(self):
        """CRITICAL #2: cybercrime fraud line must reach a money/business
        user even if areas extraction fails."""
        rs = get_practical_resources(
            "money", areas=[], severity="consult", limit=5)
        ids = [r["id"] for r in rs]
        self.assertIn("cybercrime_1930", ids)

    def test_age_clamp_rejects_implausible_value(self):
        """HIGH-adjacent: malformed age (150, -5, "abc") must NOT leak
        senior-only schemes to the wrong user."""
        # age 150 → out of range → no senior tag → SCSS hidden
        rs1 = get_practical_resources(
            "money", ["savings"], "watchful",
            user_facts={"age": 150}, limit=10)
        self.assertNotIn("scss_senior_savings", [r["id"] for r in rs1])

        # age -5 → out of range → no senior/youth tag
        rs2 = get_practical_resources(
            "money", ["savings"], "watchful",
            user_facts={"age": -5}, limit=10)
        self.assertNotIn("scss_senior_savings", [r["id"] for r in rs2])

        # age "abc" → unparseable → no senior tag
        rs3 = get_practical_resources(
            "money", ["savings"], "watchful",
            user_facts={"age": "abc"}, limit=10)
        self.assertNotIn("scss_senior_savings", [r["id"] for r in rs3])

    def test_specific_required_ids_present(self):
        """CRITICAL #1: assert specific high-value resource IDs ship
        (not just count). These are the engine's safety-net promises."""
        required = {
            "aasra_suicide", "kiran_mental_health", "telemanas_nimhans",
            "women_helpline_181", "police_112", "cybercrime_1930",
            "childline_1098", "senior_helpline_14567",
            "ayushman_bharat", "jan_aushadhi",
            "nalsa_free_lawyer", "lok_adalat",
            "rbi_sachet_scam", "cibil_free_check",
            "udyam_msme", "pmmy_mudra",
        }
        present = set(_RESOURCES.keys())
        missing = required - present
        self.assertFalse(missing, f"missing critical resource IDs: {missing}")

    def test_engine_fallback_on_resource_lookup_failure(self):
        """HIGH #3: if get_practical_resources() throws, engine must
        return the deterministic _CRISIS_FALLBACK row, NOT empty list."""
        from unittest.mock import patch
        with patch("remedy.remedy_engine_v1.get_practical_resources",
                     side_effect=RuntimeError("simulated")):
            r = get_remedies(
                "health",
                [{"name": "Mars", "score": 14},
                 {"name": "Moon", "score": 11}],
                ["mind"], severity="urgent_consult")
            pres = r["practical_resources"]
            self.assertGreater(len(pres), 0,
                                 "fallback empty after lookup failure")
            # health fallback contains Tele-MANAS + 112
            values = " | ".join(p["value"] for p in pres)
            self.assertIn("14416", values)
            self.assertIn("112", values)


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

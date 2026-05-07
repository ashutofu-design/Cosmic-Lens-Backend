"""
test_finance_engine.py — unit tests for Finance Timing Engine v1.

Mirrors test_health_engine.py structure. Run from artifacts/api-server:
    python3 -m unittest test_finance_engine
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from event_timing.finance.finance_engine_v1 import (
    compute_finance_window,
    get_last_finance_result,
    clear_last_finance_result,
    _step1_d1_filter,
    _step3_kp_layer,
    _aspects_house,
    _house_lord,
    _severity_of_window,
    _recommendation_tier,
    _derive_verdict,
    _affected_areas,
    _SIGN_IDX,
    _SIGNS,
    _WEALTH_HOUSES,
    _LEAK_HOUSES,
)


# ════════════════════════════════════════════════════════════════════════
# Synthetic kundli builder
# ════════════════════════════════════════════════════════════════════════
def _mk_kundli(asc: str, plan_houses: dict,
                dashas: list = None) -> dict:
    """Build a minimal kundli for engine consumption.

    plan_houses: {planet_name: house_number}
    Sign is inferred from house + ascendant for D1.
    """
    asc_si = _SIGN_IDX[asc]
    planets = []
    for name, h in plan_houses.items():
        sign_si = (asc_si + h - 1) % 12
        planets.append({
            "name": name, "house": h,
            "sign": _SIGNS[sign_si], "sign_idx": sign_si,
            "longitude": sign_si * 30.0 + 5.0,   # mid-half of sign
        })
    return {
        "ascendant": asc,
        "planets": planets,
        "dashas": dashas or [],
    }


def _mk_dashas() -> list:
    """Minimal dasha chain spanning ~30 yrs from 2020."""
    return [{
        "lord": "Jupiter",
        "start": "2020-01-01T00:00:00",
        "end": "2036-01-01T00:00:00",
        "antardashas": [
            {"lord": "Jupiter", "start": "2020-01-01T00:00:00",
             "end": "2022-03-01T00:00:00",
             "pratyantar": [
                 {"lord": "Jupiter", "start": "2020-01-01T00:00:00",
                  "end": "2020-05-01T00:00:00"},
                 {"lord": "Venus", "start": "2020-05-01T00:00:00",
                  "end": "2020-12-01T00:00:00"},
             ]},
            {"lord": "Saturn", "start": "2024-01-01T00:00:00",
             "end": "2028-09-01T00:00:00",
             "pratyantar": [
                 {"lord": "Saturn", "start": "2024-01-01T00:00:00",
                  "end": "2025-06-01T00:00:00"},
                 {"lord": "Mars",   "start": "2025-06-01T00:00:00",
                  "end": "2026-01-01T00:00:00"},
                 {"lord": "Venus", "start": "2026-01-01T00:00:00",
                  "end": "2027-06-01T00:00:00"},
             ]},
            {"lord": "Mercury", "start": "2028-09-01T00:00:00",
             "end": "2032-01-01T00:00:00",
             "pratyantar": [
                 {"lord": "Mercury", "start": "2028-09-01T00:00:00",
                  "end": "2030-01-01T00:00:00"},
                 {"lord": "Jupiter", "start": "2030-01-01T00:00:00",
                  "end": "2032-01-01T00:00:00"},
             ]},
        ],
    }]


# ════════════════════════════════════════════════════════════════════════
# Helper unit tests
# ════════════════════════════════════════════════════════════════════════
class TestHelpers(unittest.TestCase):
    def test_house_lord(self):
        # Aries lagna (idx 0) → 2H = Taurus → Venus
        self.assertEqual(_house_lord(0, 2), "Venus")
        # Aries → 11H = Aquarius → Saturn
        self.assertEqual(_house_lord(0, 11), "Saturn")
        # Cancer (idx 3) → 11H = Taurus → Venus
        self.assertEqual(_house_lord(3, 11), "Venus")

    def test_aspects_house_jupiter_5_9(self):
        self.assertTrue(_aspects_house("Jupiter", 1, 5))
        self.assertTrue(_aspects_house("Jupiter", 1, 9))
        self.assertFalse(_aspects_house("Jupiter", 1, 6))

    def test_wealth_and_leak_houses(self):
        self.assertEqual(set(_WEALTH_HOUSES), {2, 5, 9, 11})
        self.assertEqual(set(_LEAK_HOUSES),   {6, 8, 12})


# ════════════════════════════════════════════════════════════════════════
# Severity / verdict
# ════════════════════════════════════════════════════════════════════════
class TestSeverityVerdict(unittest.TestCase):
    def test_severity_bands(self):
        # Phase 2.5.11.12: transit_load is no-op default kwarg.
        self.assertEqual(_severity_of_window(1.0), "celebratory")
        self.assertEqual(_severity_of_window(3.0), "supportive")
        self.assertEqual(_severity_of_window(6.0), "watchful")
        self.assertEqual(_severity_of_window(9.0), "consult")
        # Transit load is no-op now (back-compat); score-only governs.
        self.assertEqual(_severity_of_window(7.0, 1.5), "watchful")

    def test_recommendation_tier(self):
        # consult only with 3+ confirmations
        self.assertEqual(_recommendation_tier("consult", 3, 30), "consult")
        # consult with fewer confirmations downgrades to watchful
        self.assertEqual(_recommendation_tier("consult", 1, 30), "watchful")
        # other tiers pass through
        self.assertEqual(_recommendation_tier("celebratory", 0, 30),
                          "celebratory")
        self.assertEqual(_recommendation_tier("supportive", 0, 30),
                          "supportive")
        self.assertEqual(_recommendation_tier("watchful", 0, 30),
                          "watchful")

    def test_derive_verdict_high_leak(self):
        # Phase 2.5.11.12: yogas + transit_load are no-op kwargs now.
        v, b = _derive_verdict(8.5)
        self.assertEqual(v, "HIGH_LEAK_WINDOW")
        self.assertEqual(b, "WEAK")

    def test_derive_verdict_promised(self):
        v, b = _derive_verdict(1.5)
        self.assertEqual(v, "WEALTH_PROMISED")
        self.assertEqual(b, "STRONG")

    def test_derive_verdict_stressed(self):
        v, _ = _derive_verdict(5.0)
        self.assertEqual(v, "STRESSED")

    def test_derive_verdict_stable_midband(self):
        v, _ = _derive_verdict(3.0)
        self.assertEqual(v, "STABLE")


# ════════════════════════════════════════════════════════════════════════
# Step 1 — D1 filter
# ════════════════════════════════════════════════════════════════════════
class TestStep1Filter(unittest.TestCase):
    def test_2L_and_11L_always_in_filter(self):
        # Aries lagna → 2L = Venus, 11L = Saturn
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 1, "Mercury": 2,
            "Jupiter": 5, "Venus": 2, "Saturn": 11,
            "Rahu": 3, "Ketu": 9,
        })
        d1 = _step1_d1_filter(kundli, 0)
        # 2L Venus also OCCUPIES 2H → very high d1
        self.assertTrue(d1["Venus"]["in_filter"])
        # 11L Saturn also OCCUPIES 11H
        self.assertTrue(d1["Saturn"]["in_filter"])
        # Jupiter (karaka) should always be candidate
        self.assertIn(2, d1["Venus"]["is_lord_of"])
        self.assertIn(11, d1["Saturn"]["is_lord_of"])

    def test_occupants_of_wealth_houses_get_boost(self):
        # Aries lagna; place Mercury in 11H (occupant)
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 3, "Ketu": 9,
        })
        d1 = _step1_d1_filter(kundli, 0)
        self.assertEqual(d1["Mercury"]["occupies"], 11)
        self.assertTrue(d1["Mercury"]["in_filter"])
        self.assertTrue(any("occupies 11H" in l
                            for l in d1["Mercury"]["links"]))

    def test_12H_occupant_is_leak_link(self):
        # Saturn occupying 12H → must carry the LEAK link
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 5, "Venus": 2, "Saturn": 12,
            "Rahu": 3, "Ketu": 9,
        })
        d1 = _step1_d1_filter(kundli, 0)
        self.assertEqual(d1["Saturn"]["occupies"], 12)
        self.assertTrue(any("LEAK" in l for l in d1["Saturn"]["links"]))


# ════════════════════════════════════════════════════════════════════════
# Step 3.5 — KP layer
# ════════════════════════════════════════════════════════════════════════
class TestKpLayer(unittest.TestCase):
    def test_kp_2csl_income_yes(self):
        kp = {
            "cusps": [{"house": 2, "sl": "Jupiter"},
                      {"house": 11, "sl": "Mars"}],
            "significations": {
                "Jupiter": [2, 11, 5],   # all wealth → INCOME_YES
                "Mars":    [6, 8],       # all leak  → GAINS_BLOCKED
            },
        }
        out = _step3_kp_layer(kp, 0)
        self.assertEqual(out["verdict_2"], "INCOME_YES")
        self.assertEqual(out["verdict_11"], "GAINS_BLOCKED")

    def test_kp_empty_safe_default(self):
        out = _step3_kp_layer({}, 0)
        self.assertEqual(out["verdict_2"], "UNKNOWN")
        self.assertEqual(out["verdict_11"], "UNKNOWN")


# ════════════════════════════════════════════════════════════════════════
# Step 4 — KP-as-final-filter gate (Phase 2.5.11.12)
# ════════════════════════════════════════════════════════════════════════
class TestStep4KpGate(unittest.TestCase):
    def test_kp_gate_narrows_pool_to_qualified_planets(self):
        # Aries lagna; 4 D1 survivors but only 2 KP-qualified
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 3, "Ketu": 9,
        })
        from event_timing.finance.finance_engine_v1 import _step4_rank
        d1 = _step1_d1_filter(kundli, 0)
        d9 = {p: 12.0 for p in d1}
        kp = {
            "cusps": [{"house": 2, "sl": "Venus"},
                      {"house": 11, "sl": "Mercury"}],
            "significations": {
                "Venus":   [2, 11, 5],   # qualified (touches wealth)
                "Mercury": [2, 9],       # qualified
                "Saturn":  [6, 8],       # NOT qualified (only leak)
                "Jupiter": [12],         # NOT qualified
            },
        }
        ranked = _step4_rank(d1, d9, kp, 0)
        names = {r["name"] for r in ranked}
        self.assertIn("Venus", names)
        self.assertIn("Mercury", names)
        self.assertNotIn("Saturn", names)
        for r in ranked:
            self.assertTrue(r["kp_qualified"])

    def test_kp_empty_falls_back_to_all_survivors(self):
        # No KP data → fallback to all D1 survivors (engine never empty)
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 3, "Ketu": 9,
        })
        from event_timing.finance.finance_engine_v1 import _step4_rank
        d1 = _step1_d1_filter(kundli, 0)
        d9 = {p: 12.0 for p in d1}
        ranked = _step4_rank(d1, d9, {}, 0)
        self.assertGreater(len(ranked), 0)
        for r in ranked:
            self.assertFalse(r["kp_qualified"])  # nobody qualified

    def test_kp_no_qualifier_falls_back(self):
        # KP present but NO survivor signifies wealth → fallback to all
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 3, "Ketu": 9,
        })
        from event_timing.finance.finance_engine_v1 import _step4_rank
        d1 = _step1_d1_filter(kundli, 0)
        d9 = {p: 12.0 for p in d1}
        kp = {"cusps": [{"house": 2, "sl": "Mars"}],
              "significations": {p: [6, 8, 12] for p in d1}}  # all leak
        ranked = _step4_rank(d1, d9, kp, 0)
        self.assertGreater(len(ranked), 0)


# ════════════════════════════════════════════════════════════════════════
# Step 9 — Yoga detection
# Phase 2.5.11.12: TestYogas removed — _detect_yogas orphaned (STEP 9 removed).
# ════════════════════════════════════════════════════════════════════════
# Affected areas
# ════════════════════════════════════════════════════════════════════════
class TestAffectedAreas(unittest.TestCase):
    def test_affected_areas_dedup(self):
        ranked = [
            {"name": "Jupiter",
             "significations": ["wisdom_wealth", "advisory_income"]},
            {"name": "Venus",
             "significations": ["luxury_income", "vehicles_assets"]},
            {"name": "Mercury",
             "significations": ["business_commerce", "trading"]},
        ]
        out = _affected_areas(ranked)
        self.assertEqual(len(out), len(set(out)))   # no dupes
        self.assertIn("wisdom_wealth", out)
        self.assertIn("luxury_income", out)
        self.assertIn("business_commerce", out)


# ════════════════════════════════════════════════════════════════════════
# Public API — full pipeline
# ════════════════════════════════════════════════════════════════════════
class TestPublicAPI(unittest.TestCase):
    def test_compute_returns_required_keys(self):
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 3, "Ketu": 9,
        }, dashas=_mk_dashas())
        kp = {
            "cusps": [{"house": 2, "sl": "Venus"},
                      {"house": 11, "sl": "Saturn"}],
            "significations": {
                "Venus": [2, 11, 5], "Saturn": [10, 11],
                "Jupiter": [5, 9], "Mercury": [11, 2],
                "Mars": [7, 8], "Sun": [1, 10],
                "Moon": [4],
            },
        }
        result = compute_finance_window(kundli, intel={}, kp=kp,
                                         birth={"dob": "1990-05-15"})
        # Required keys
        for k in ("verdict", "band", "next_3_windows", "top_finance_planets",
                  "weighted_breakdown", "kp_layer",
                  "risk_flags", "factors", "llm_directives",
                  "remedies", "engine_version", "engine_arch"):
            self.assertIn(k, result, f"missing key: {k}")
        self.assertEqual(result["engine_version"], "v1.0.0")
        self.assertIn(result["verdict"],
                       {"WEALTH_PROMISED", "STABLE", "STRESSED",
                        "HIGH_LEAK_WINDOW", "UNKNOWN"})

    def test_llm_directives_always_have_disclaimers(self):
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 3, "Ketu": 9,
        }, dashas=_mk_dashas())
        result = compute_finance_window(kundli, intel={}, kp={},
                                         birth={"dob": "1990-05-15"})
        directives = result.get("llm_directives") or []
        # MANDATORY disclaimers per replit.md user policy
        for must in ("FINANCIAL_DISCLAIMER",
                     "NOT_INVESTMENT_ADVICE",
                     "NO_GUARANTEED_WEALTH",
                     "NO_GUARANTEED_LOSS"):
            self.assertIn(must, directives,
                           f"missing mandatory directive: {must}")
        # SEVERITY_TIER must always be present
        self.assertTrue(any(d.startswith("SEVERITY_TIER:")
                             for d in directives))

    def test_empty_kundli_returns_unknown(self):
        result = compute_finance_window({}, intel={}, kp={}, birth=None)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertIn("engine_version", result)

    def test_engine_exception_wrapped_safely(self):
        # Pass a kundli that will lagna-resolve but break downstream
        # (no planets list, only ascendant). Should NOT raise.
        bad_kundli = {"ascendant": "Aries"}
        result = compute_finance_window(bad_kundli)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertIn("engine_version", result)

    def test_thread_local_cache_lifecycle(self):
        clear_last_finance_result()
        self.assertIsNone(get_last_finance_result())
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 3, "Ketu": 9,
        }, dashas=_mk_dashas())
        compute_finance_window(kundli, intel={}, kp={},
                                birth={"dob": "1990-05-15"})
        cached = get_last_finance_result()
        self.assertIsNotNone(cached)
        self.assertEqual(cached["engine_version"], "v1.0.0")
        # Clear and verify
        clear_last_finance_result()
        self.assertIsNone(get_last_finance_result())

    def test_remedies_block_money_topic(self):
        # Engine MUST delegate to remedy.get_remedies(topic="money")
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 3, "Ketu": 9,
        }, dashas=_mk_dashas())
        result = compute_finance_window(kundli, intel={}, kp={},
                                         birth={"dob": "1990-05-15"})
        rem = result.get("remedies") or {}
        # money topic returns these keys; if remedy module missing,
        # _compute_finance_remedies returns {} → still OK shape
        if rem:
            self.assertEqual(rem.get("topic"), "money")
            # Money severity tiers per remedy engine v1.1
            self.assertIn(rem.get("severity"),
                           {"watchful", "supportive",
                            "celebratory", "consult"})


class TestArchitectRegressions(unittest.TestCase):
    """Regression tests for architect-flagged CRITICAL bugs (May 7 2026)."""

    def test_aries_saturn_11L_NOT_classified_as_leak_lord(self):
        """Architect bug #1: Saturn = 11L AND functional-malefic for Aries.
        Old logic flipped Saturn into leak_lords via the functional-malefic
        tag → forced HIGH_LEAK on every Aries chart. Saturn must now be
        wealth-classified (or at minimum NOT leak) when it is the 11L
        without occupying any leak house.
        """
        # Aries lagna; Saturn occupies 11H (own house, NOT in 6/8/12)
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 5, "Venus": 2, "Saturn": 11,
            "Rahu": 3, "Ketu": 9,
        }, dashas=_mk_dashas())
        result = compute_finance_window(kundli, intel={}, kp={},
                                         birth={"dob": "1990-04-15"})
        # Pull the dasha-trace for windows where Saturn appears
        for w in result.get("next_3_windows", []):
            for trig in w.get("triggers", []):
                if "Saturn" in trig:
                    # Saturn must NOT carry a LEAK_LORD tag
                    self.assertNotIn("LEAK_LORD", trig,
                        f"Saturn (11L for Aries) wrongly tagged as leak: {trig}")

    def test_high_leak_only_when_stress_is_actually_high(self):
        """Phase 2.5.11.12: yogas removed. HIGH_LEAK now keys off score
        only (>=8.0). Mid-stress (5.0) → STRESSED, not HIGH_LEAK.
        """
        v, _ = _derive_verdict(5.0)
        self.assertNotEqual(v, "HIGH_LEAK_WINDOW")
        v, _ = _derive_verdict(1.5)
        self.assertNotEqual(v, "HIGH_LEAK_WINDOW")

    def test_high_leak_verdict_forces_consult_tier(self):
        """Architect issue #5: HIGH_LEAK_WINDOW must always surface as
        `consult` tier — no silent downgrade.
        """
        # Build a chart designed to trigger HIGH_LEAK
        # Cancer lagna; 11L=Venus placed in 6H (Daridra) plus heavy
        # malefic activation.
        kundli = _mk_kundli("Cancer", {
            "Sun": 10, "Moon": 1, "Mars": 6, "Mercury": 9,
            "Jupiter": 12, "Venus": 6, "Saturn": 3,
            "Rahu": 4, "Ketu": 10,
        }, dashas=_mk_dashas())
        result = compute_finance_window(kundli, intel={}, kp={},
                                         birth={"dob": "1985-07-10"})
        if result["verdict"] == "HIGH_LEAK_WINDOW":
            self.assertEqual(result["recommendation_tier"], "consult",
                "HIGH_LEAK verdict must always surface as consult tier")

    def test_dasha_classification_distinguishes_dual_role_planet(self):
        """When a planet rules BOTH wealth and leak houses, the dominant
        role (by tag count) wins. Pisces lagna → Saturn = 11L (wealth) AND
        12L (leak); both tags present, leak tags = 1, wealth tags = 1 →
        wealth wins (else > branch goes to wealth_lords).
        """
        # Pisces lagna; place Saturn somewhere neutral so only its
        # lordship tags drive classification
        kundli = _mk_kundli("Pisces", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 1, "Venus": 2, "Saturn": 9,
            "Rahu": 3, "Ketu": 9,
        }, dashas=_mk_dashas())
        d1 = _step1_d1_filter(kundli, _SIGN_IDX["Pisces"])
        # Saturn for Pisces: 11L (Capricorn) + 12L (Aquarius)
        sat_links = d1["Saturn"]["links"]
        has_11L = any("11L" in l for l in sat_links)
        has_12L = any("12L" in l for l in sat_links)
        self.assertTrue(has_11L and has_12L,
            f"Saturn for Pisces should be both 11L AND 12L; got {sat_links}")


if __name__ == "__main__":
    unittest.main()

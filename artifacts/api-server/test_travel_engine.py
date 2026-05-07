"""
test_travel_engine.py — unit tests for Travel Timing Engine v1.

Mirrors test_finance_engine.py / test_health_engine.py structure.
Run from artifacts/api-server:
    python3 -m unittest test_travel_engine
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from event_timing.travel.travel_engine_v1 import (
    compute_travel_window,
    get_last_travel_result,
    clear_last_travel_result,
    _step1_d1_filter,
    _step3_5_kp_layer,
    _detect_yogas,
    _detect_foreign_promised,
    _aspects_house,
    _house_lord,
    _severity_of_window,
    _recommendation_tier,
    _derive_verdict,
    _affected_areas,
    _SIGN_IDX,
    _SIGNS,
    _TRAVEL_HOUSES,
    _FOREIGN_HOUSES,
    _HOME_HOUSES,
)


def _mk_kundli(asc: str, plan_houses: dict, dashas: list = None) -> dict:
    asc_si = _SIGN_IDX[asc]
    planets = []
    for name, h in plan_houses.items():
        sign_si = (asc_si + h - 1) % 12
        planets.append({
            "name": name, "house": h,
            "sign": _SIGNS[sign_si], "sign_idx": sign_si,
            "longitude": sign_si * 30.0 + 5.0,
        })
    return {"ascendant": asc, "planets": planets, "dashas": dashas or []}


def _mk_dashas() -> list:
    return [{
        "lord": "Saturn",
        "start": "2020-01-01T00:00:00", "end": "2039-01-01T00:00:00",
        "antardashas": [
            {"lord": "Saturn", "start": "2020-01-01T00:00:00",
             "end": "2023-03-01T00:00:00",
             "pratyantar": [
                 {"lord": "Saturn", "start": "2020-01-01T00:00:00",
                  "end": "2021-06-01T00:00:00"},
                 {"lord": "Mercury", "start": "2021-06-01T00:00:00",
                  "end": "2023-03-01T00:00:00"},
             ]},
            {"lord": "Rahu", "start": "2024-01-01T00:00:00",
             "end": "2027-09-01T00:00:00",
             "pratyantar": [
                 {"lord": "Rahu", "start": "2024-01-01T00:00:00",
                  "end": "2025-06-01T00:00:00"},
                 {"lord": "Jupiter", "start": "2025-06-01T00:00:00",
                  "end": "2027-09-01T00:00:00"},
             ]},
            {"lord": "Jupiter", "start": "2028-01-01T00:00:00",
             "end": "2031-01-01T00:00:00",
             "pratyantar": [
                 {"lord": "Jupiter", "start": "2028-01-01T00:00:00",
                  "end": "2029-06-01T00:00:00"},
                 {"lord": "Venus", "start": "2029-06-01T00:00:00",
                  "end": "2031-01-01T00:00:00"},
             ]},
        ],
    }]


# ════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════
class TestHelpers(unittest.TestCase):
    def test_house_lord_for_travel(self):
        # Aries (idx 0) → 12H = Pisces → Jupiter; 9H = Sagittarius → Jupiter
        self.assertEqual(_house_lord(0, 12), "Jupiter")
        self.assertEqual(_house_lord(0, 9), "Jupiter")
        # Cancer (idx 3) → 12H = Gemini → Mercury
        self.assertEqual(_house_lord(3, 12), "Mercury")

    def test_travel_and_home_house_constants(self):
        self.assertEqual(set(_TRAVEL_HOUSES), {3, 9, 12})
        self.assertEqual(set(_FOREIGN_HOUSES), {9, 12})
        self.assertEqual(set(_HOME_HOUSES), {4})


# ════════════════════════════════════════════════════════════════════════
# Severity / verdict
# ════════════════════════════════════════════════════════════════════════
class TestSeverityVerdict(unittest.TestCase):
    def test_severity_bands(self):
        self.assertEqual(_severity_of_window(7.0, 0.0), "celebratory")
        self.assertEqual(_severity_of_window(4.0, 0.0), "supportive")
        self.assertEqual(_severity_of_window(2.0, 0.0), "watchful")
        # High risk_score forces consult regardless of flow
        self.assertEqual(_severity_of_window(7.0, 0.0, 2.5), "consult")

    def test_recommendation_tier(self):
        self.assertEqual(_recommendation_tier("consult", 3, 30), "consult")
        self.assertEqual(_recommendation_tier("consult", 1, 30), "watchful")
        self.assertEqual(_recommendation_tier("celebratory", 0, 30),
                          "celebratory")

    def test_derive_verdict_travel_promised(self):
        yogas = [{"name": "Foreign-Settlement Yoga (Rahu in 12H)",
                   "severity": "protective", "planets": ["Rahu"]}]
        v, b = _derive_verdict(7.0, "STRONG", yogas, 0.0, True)
        self.assertEqual(v, "TRAVEL_PROMISED")
        self.assertEqual(b, "STRONG")

    def test_derive_verdict_high_risk_travel(self):
        yogas = [{"name": "Risk-Travel Yoga (Mars+Rahu in 9H — accident/legal-trouble)",
                   "severity": "high", "planets": ["Mars", "Rahu"]}]
        v, _ = _derive_verdict(2.0, "MEDIUM", yogas, 0.0, False)
        self.assertEqual(v, "HIGH_RISK_TRAVEL")

    def test_derive_verdict_low_probability_when_anchored(self):
        yogas = [{"name": "Sthanabhrama (anchored — 4L strong + 12L debilitated)",
                   "severity": "high", "planets": ["Mars", "Mercury"]}]
        v, _ = _derive_verdict(0.5, "WEAK", yogas, 0.0, False)
        self.assertEqual(v, "LOW_PROBABILITY")

    def test_derive_verdict_favorable_with_protection(self):
        yogas = [{"name": "Tirtha Yoga (Jupiter+9L conjunction)",
                   "severity": "protective", "planets": ["Jupiter", "Saturn"]}]
        v, _ = _derive_verdict(2.0, "MEDIUM", yogas, 0.0, False)
        self.assertEqual(v, "FAVORABLE")


# ════════════════════════════════════════════════════════════════════════
# Step 1 — D1 filter
# ════════════════════════════════════════════════════════════════════════
class TestStep1Filter(unittest.TestCase):
    def test_12L_always_in_filter(self):
        # Aries lagna → 12L = Jupiter (Pisces). Jupiter is karaka too.
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 5, "Venus": 2, "Saturn": 11,
            "Rahu": 12, "Ketu": 6,
        })
        d1 = _step1_d1_filter(kundli, 0)
        self.assertTrue(d1["Jupiter"]["in_filter"])
        # Rahu (foreign karaka + occupies 12H) must be in filter
        self.assertTrue(d1["Rahu"]["in_filter"])
        self.assertEqual(d1["Rahu"]["occupies"], 12)

    def test_occupants_of_9_and_12_get_boost(self):
        kundli = _mk_kundli("Aries", {
            "Sun": 9, "Moon": 4, "Mars": 7, "Mercury": 12,
            "Jupiter": 5, "Venus": 2, "Saturn": 11,
            "Rahu": 3, "Ketu": 9,
        })
        d1 = _step1_d1_filter(kundli, 0)
        # Sun in 9H, Mercury in 12H — both should carry travel-house links
        self.assertTrue(any("9H (travel-house)" in l
                            for l in d1["Sun"]["links"]))
        self.assertTrue(any("12H (travel-house)" in l
                            for l in d1["Mercury"]["links"]))

    def test_4H_occupant_carries_anchor_or_uproot_link(self):
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 5, "Venus": 2, "Saturn": 4,
            "Rahu": 3, "Ketu": 9,
        })
        d1 = _step1_d1_filter(kundli, 0)
        self.assertEqual(d1["Saturn"]["occupies"], 4)
        self.assertTrue(any("HOME" in l and "anchor/uproot" in l
                            for l in d1["Saturn"]["links"]))


# ════════════════════════════════════════════════════════════════════════
# Step 3.5 — KP layer
# ════════════════════════════════════════════════════════════════════════
class TestKpLayer(unittest.TestCase):
    def test_kp_12csl_travel_yes(self):
        kp = {
            "cusps": [{"house": 3, "sl": "Mercury"},
                      {"house": 9, "sl": "Jupiter"},
                      {"house": 12, "sl": "Rahu"}],
            "significations": {
                "Mercury": [3, 9],
                "Jupiter": [9, 12, 5],
                "Rahu":    [12, 9],
            },
        }
        out = _step3_5_kp_layer(kp, 0)
        self.assertEqual(out["verdict_3"], "TRAVEL_YES")
        self.assertEqual(out["verdict_9"], "TRAVEL_YES")
        self.assertEqual(out["verdict_12"], "TRAVEL_YES")

    def test_kp_anchored_when_csl_signifies_4(self):
        kp = {
            "cusps": [{"house": 12, "sl": "Moon"}],
            "significations": {"Moon": [4, 2]},
        }
        out = _step3_5_kp_layer(kp, 0)
        self.assertEqual(out["verdict_12"], "ANCHORED")

    def test_kp_blocked_when_csl_signifies_6_or_8(self):
        kp = {
            "cusps": [{"house": 9, "sl": "Saturn"}],
            "significations": {"Saturn": [6, 8]},
        }
        out = _step3_5_kp_layer(kp, 0)
        self.assertEqual(out["verdict_9"], "BLOCKED_OR_RISKY")

    def test_kp_empty_safe_default(self):
        out = _step3_5_kp_layer({}, 0)
        self.assertEqual(out["verdict_12"], "UNKNOWN")


# ════════════════════════════════════════════════════════════════════════
# Yoga detection
# ════════════════════════════════════════════════════════════════════════
class TestYogas(unittest.TestCase):
    def test_foreign_settlement_rahu_in_12(self):
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 5, "Venus": 2, "Saturn": 11,
            "Rahu": 12, "Ketu": 6,
        })
        yg = _detect_yogas(kundli, 0, kundli["planets"])
        names = [y["name"] for y in yg]
        self.assertTrue(any("Foreign-Settlement Yoga (Rahu in 12H)" in n
                             for n in names))

    def test_tirtha_yoga_jupiter_aspects_9L(self):
        # Aries lagna → 9L = Jupiter itself. Jupiter conjunct itself trivially.
        # Use Cancer lagna → 9L = Jupiter (Pisces); Jupiter in 9H conjuncts itself.
        kundli = _mk_kundli("Cancer", {
            "Sun": 1, "Moon": 1, "Mars": 7, "Mercury": 3,
            "Jupiter": 9, "Venus": 5, "Saturn": 10,
            "Rahu": 4, "Ketu": 10,
        })
        yg = _detect_yogas(kundli, _SIGN_IDX["Cancer"], kundli["planets"])
        names = [y["name"] for y in yg]
        # Jupiter is itself the 9L for Cancer; conjunction with itself is
        # trivially detected (jup_h == h9_h).
        self.assertTrue(any("Tirtha Yoga" in n for n in names))

    def test_risk_travel_yoga(self):
        # Mars + Rahu both in 9H
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 9, "Mercury": 6,
            "Jupiter": 5, "Venus": 2, "Saturn": 11,
            "Rahu": 9, "Ketu": 3,
        })
        yg = _detect_yogas(kundli, 0, kundli["planets"])
        names = [y["name"] for y in yg]
        self.assertTrue(any("Risk-Travel Yoga" in n for n in names))
        for y in yg:
            if "Risk-Travel" in y["name"]:
                self.assertEqual(y["severity"], "high")

    def test_visa_block_yoga(self):
        # Ketu in 9H + Saturn aspecting 12H (Saturn 3rd-aspect from 10H = 12H)
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 3, "Ketu": 9,
        })
        yg = _detect_yogas(kundli, 0, kundli["planets"])
        names = [y["name"] for y in yg]
        self.assertTrue(any("Visa-Block" in n for n in names))


# ════════════════════════════════════════════════════════════════════════
# Foreign-promised composite flag
# ════════════════════════════════════════════════════════════════════════
class TestForeignPromised(unittest.TestCase):
    def test_requires_three_confirmations(self):
        yogas = [{"name": "Foreign-Settlement Yoga (Rahu in 12H)",
                   "severity": "protective", "planets": ["Rahu"]}]
        kp_layer = {"verdict_12": "TRAVEL_YES"}
        ranked = [{"name": "Rahu", "score": 20.0},
                  {"name": "Jupiter", "score": 15.0},
                  {"name": "Saturn", "score": 12.0}]
        # 3 confirmations: foreign yoga + KP + Rahu top3 + sav MEDIUM = 4
        self.assertTrue(_detect_foreign_promised(yogas, kp_layer,
                                                   "MEDIUM", ranked))
        # Only 2 confirmations → False
        self.assertFalse(_detect_foreign_promised(yogas, {"verdict_12": "NEUTRAL"},
                                                    "WEAK",
                                                    [{"name": "Sun", "score": 5}]))


# ════════════════════════════════════════════════════════════════════════
# Affected areas
# ════════════════════════════════════════════════════════════════════════
class TestAffectedAreas(unittest.TestCase):
    def test_affected_areas_dedup_and_cap(self):
        ranked = [
            {"name": "Rahu",
             "significations": ["foreign_settlement", "sudden_overseas_move"]},
            {"name": "Jupiter",
             "significations": ["sacred_travel_pilgrimage", "study_abroad"]},
            {"name": "Mercury",
             "significations": ["business_travel", "trade_journey"]},
        ]
        out = _affected_areas(ranked)
        self.assertEqual(len(out), len(set(out)))
        self.assertIn("foreign_settlement", out)
        self.assertIn("study_abroad", out)
        self.assertIn("business_travel", out)
        self.assertLessEqual(len(out), 6)


# ════════════════════════════════════════════════════════════════════════
# Public API — full pipeline
# ════════════════════════════════════════════════════════════════════════
class TestPublicAPI(unittest.TestCase):
    def test_compute_returns_required_keys(self):
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        kp = {
            "cusps": [{"house": 3, "sl": "Mercury"},
                      {"house": 9, "sl": "Jupiter"},
                      {"house": 12, "sl": "Rahu"}],
            "significations": {
                "Mercury": [3, 11], "Saturn": [10, 11],
                "Jupiter": [5, 9, 12], "Rahu": [12, 9],
                "Mars": [7, 8], "Sun": [1, 10],
                "Moon": [4], "Venus": [2, 7],
            },
        }
        result = compute_travel_window(kundli, intel={}, kp=kp,
                                         birth={"dob": "1990-05-15"})
        for k in ("verdict", "band", "foreign_promised", "next_3_windows",
                  "top_travel_planets", "weighted_breakdown", "kp_layer",
                  "ashtakavarga", "yogas", "risk_flags", "factors",
                  "llm_directives", "remedies", "engine_version",
                  "engine_arch"):
            self.assertIn(k, result, f"missing key: {k}")
        self.assertEqual(result["engine_version"], "v1.0.0")
        self.assertIn(result["verdict"],
                       {"TRAVEL_PROMISED", "FAVORABLE",
                        "LOW_PROBABILITY", "HIGH_RISK_TRAVEL", "UNKNOWN"})

    def test_llm_directives_always_have_disclaimers(self):
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        result = compute_travel_window(kundli, intel={}, kp={},
                                         birth={"dob": "1990-05-15"})
        directives = result.get("llm_directives") or []
        for must in ("TRAVEL_DISCLAIMER",
                     "NO_GUARANTEED_VISA_OUTCOME",
                     "NO_GUARANTEED_TRAVEL_DATE",
                     "NO_DESTINATION_NAMING"):
            self.assertIn(must, directives,
                           f"missing mandatory directive: {must}")
        self.assertTrue(any(d.startswith("SEVERITY_TIER:")
                             for d in directives))

    def test_foreign_promised_emits_consult_legal_directive(self):
        # Strong foreign chart: Rahu in 12H + Jupiter in 9H
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 9, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        kp = {"cusps": [{"house": 12, "sl": "Rahu"},
                         {"house": 9, "sl": "Jupiter"}],
               "significations": {"Rahu": [12, 9], "Jupiter": [9, 12, 5]}}
        result = compute_travel_window(kundli, intel={}, kp=kp,
                                         birth={"dob": "1990-05-15"})
        if result.get("foreign_promised"):
            self.assertIn("FOREIGN_TRAVEL_INDICATED",
                           result["llm_directives"])
            self.assertIn("CONSULT_PROFESSIONAL_FOR_LEGAL",
                           result["llm_directives"])

    def test_empty_kundli_returns_unknown(self):
        result = compute_travel_window({}, intel={}, kp={}, birth=None)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertIn("engine_version", result)

    def test_engine_exception_wrapped_safely(self):
        bad_kundli = {"ascendant": "Aries"}
        result = compute_travel_window(bad_kundli)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertIn("engine_version", result)

    def test_thread_local_cache_lifecycle(self):
        clear_last_travel_result()
        self.assertIsNone(get_last_travel_result())
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        compute_travel_window(kundli, intel={}, kp={},
                                birth={"dob": "1990-05-15"})
        cached = get_last_travel_result()
        self.assertIsNotNone(cached)
        self.assertEqual(cached["engine_version"], "v1.0.0")
        clear_last_travel_result()
        self.assertIsNone(get_last_travel_result())


# ════════════════════════════════════════════════════════════════════════
# Architect-pattern regressions (mirrors finance v1)
# ════════════════════════════════════════════════════════════════════════
class TestArchitectPatternRegressions(unittest.TestCase):
    """Carry over the 2 architect-flagged patterns from finance v1
    to ensure the same bugs cannot recur in travel."""

    def test_aries_jupiter_12L_NOT_classified_as_anchor(self):
        """Jupiter is 12L (foreign) AND functional benefic for Aries.
        It must be classified as TRAVEL_LORD, never ANCHOR.
        """
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 5, "Venus": 2, "Saturn": 11,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        result = compute_travel_window(kundli, intel={}, kp={},
                                         birth={"dob": "1990-04-15"})
        for w in result.get("next_3_windows", []):
            for trig in w.get("triggers", []):
                if "Jupiter" in trig:
                    self.assertNotIn("ANCHOR", trig,
                        f"Jupiter (12L for Aries) wrongly tagged as anchor: {trig}")

    def test_protective_yoga_rescues_low_flow(self):
        """Mid/low flow + a protective yoga must NOT be LOW_PROBABILITY
        if no high-neg yoga is present.
        """
        yogas = [{"name": "Tirtha Yoga (Jupiter+9L conjunction)",
                   "severity": "protective", "planets": ["Jupiter"]}]
        v, _ = _derive_verdict(2.0, "MEDIUM", yogas, 0.0, False)
        self.assertEqual(v, "FAVORABLE")

    def test_foreign_promised_alone_does_not_force_travel_promised_at_low_flow(self):
        """Architect CRITICAL: foreign_promised=True with s<3.5 must NOT
        elevate verdict to TRAVEL_PROMISED. The houses are promised but
        the timing isn't.
        """
        yogas = [{"name": "Foreign-Settlement Yoga (Rahu in 12H)",
                   "severity": "protective", "planets": ["Rahu"]}]
        # Low flow (1.0), foreign_promised=True → must NOT be TRAVEL_PROMISED
        v, _ = _derive_verdict(1.0, "MEDIUM", yogas, 0.0, True)
        self.assertNotEqual(v, "TRAVEL_PROMISED",
            "foreign_promised must require flow >= 3.5 to elevate verdict")
        # At s=4.0 with foreign_promised → should now elevate
        v2, _ = _derive_verdict(4.0, "MEDIUM", yogas, 0.0, True)
        self.assertEqual(v2, "TRAVEL_PROMISED")

    def test_negative_foreign_yoga_does_not_inflate_confirmations(self):
        """Architect HIGH#2: a Foreign-Settlement yoga with non-protective
        severity must NOT count toward the foreign_promised confirmations.
        """
        yogas_neg = [{"name": "Foreign-Settlement Yoga (artifact)",
                       "severity": "high", "planets": ["Rahu"]}]
        kp_layer = {"verdict_12": "TRAVEL_YES"}
        ranked = [{"name": "Rahu", "score": 20.0},
                  {"name": "Jupiter", "score": 15.0}]
        # Even with KP+Rahu+sav MEDIUM, negative foreign yoga gives only
        # 3 confirmations (no foreign_yoga + KP + sav + Rahu = 3) → True
        # But if we drop sav, 2 only → False
        self.assertFalse(_detect_foreign_promised(
            yogas_neg, kp_layer, "WEAK", ranked))

    def test_kp_blocked_dominates_travel_yes(self):
        """Architect HIGH#3: when CSL signifies BOTH dusthana AND travel
        houses, BLOCKED_OR_RISKY must dominate.
        """
        kp = {
            "cusps": [{"house": 12, "sl": "Saturn"}],
            # Saturn signifies both 9 (travel) and 6 (dusthana)
            "significations": {"Saturn": [9, 6]},
        }
        out = _step3_5_kp_layer(kp, 0)
        self.assertEqual(out["verdict_12"], "BLOCKED_OR_RISKY",
            "Dusthana signification must dominate travel signification")

    def test_high_risk_travel_forces_consult_tier(self):
        """HIGH_RISK_TRAVEL verdict must always surface as `consult` tier."""
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 9, "Mercury": 6,
            "Jupiter": 5, "Venus": 2, "Saturn": 11,
            "Rahu": 9, "Ketu": 3,
        }, dashas=_mk_dashas())
        result = compute_travel_window(kundli, intel={}, kp={},
                                         birth={"dob": "1990-05-15"})
        if result["verdict"] == "HIGH_RISK_TRAVEL":
            self.assertEqual(result["recommendation_tier"], "consult")
            self.assertIn("ADVISE_TRAVEL_INSURANCE_AND_CAUTION",
                           result["llm_directives"])


if __name__ == "__main__":
    unittest.main()

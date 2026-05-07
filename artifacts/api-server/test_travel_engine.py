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


# ════════════════════════════════════════════════════════════════════════
# Past-Window Lookback (Phase 2.5.11.14)
# ════════════════════════════════════════════════════════════════════════
class TestPastWindowLookback(unittest.TestCase):
    """STEP 5 must scan dasha chain backward when direction='past'."""

    def test_past_windows_present_in_output(self):
        """compute_travel_window must always emit `past_windows` key."""
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 3, "Ketu": 9,
        }, dashas=_mk_dashas())
        result = compute_travel_window(kundli, intel={}, kp={},
                                         birth={"dob": "1990-05-15"})
        self.assertIn("past_windows", result)
        self.assertIsInstance(result["past_windows"], list)

    def test_past_windows_are_strictly_in_the_past(self):
        """Every past_window must end before now."""
        from datetime import datetime
        kundli = _mk_kundli("Sagittarius", {
            "Sun": 12, "Moon": 1, "Mars": 8, "Mercury": 12,
            "Jupiter": 10, "Venus": 1, "Saturn": 2,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        result = compute_travel_window(kundli, intel={}, kp={},
                                         birth={"dob": "1992-11-26"})
        now = datetime.utcnow()
        for w in result.get("past_windows") or []:
            end = datetime.fromisoformat(w["end_iso"])
            self.assertLess(end, now,
                f"past_window {w['window']} ended at {w['end_iso']} "
                f"but now is {now.isoformat()} — must be strictly past")

    def test_past_windows_carry_opportunity_directive(self):
        """When past windows exist, directive must flag them as
        opportunities (not events) to prevent LLM hallucination."""
        kundli = _mk_kundli("Sagittarius", {
            "Sun": 12, "Moon": 1, "Mars": 8, "Mercury": 12,
            "Jupiter": 10, "Venus": 1, "Saturn": 2,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        result = compute_travel_window(kundli, intel={}, kp={},
                                         birth={"dob": "1992-11-26"})
        if result.get("past_windows"):
            self.assertIn("PAST_WINDOW_IS_OPPORTUNITY_NOT_EVENT",
                           result["llm_directives"])

    def test_step5_direction_param_filters_correctly(self):
        """Direct unit-level: _step5_dasha_activation must respect
        direction kwarg (past vs future)."""
        from datetime import datetime, timedelta
        from event_timing.travel.travel_engine_v1 import (
            _step5_dasha_activation, _flatten_dasha_chain,
        )
        kundli = _mk_kundli("Sagittarius", {
            "Sun": 12, "Moon": 1, "Mars": 8, "Mercury": 12,
            "Jupiter": 10, "Venus": 1, "Saturn": 2,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        chain = _flatten_dasha_chain(kundli)
        # Build a dummy ranked list from anything the chain references
        ranked = [{"name": "Rahu", "score": 15.0,
                    "links": ["foreign-settlement karaka (Rahu)",
                              "occupies 12H (travel-house)"]},
                   {"name": "Sun", "score": 13.0,
                    "links": ["9L (long-distance/dharma travel)",
                              "occupies 12H (travel-house)"]}]
        now = datetime.utcnow()
        future = _step5_dasha_activation(chain, ranked, 8, now,
                                            direction="future")
        past   = _step5_dasha_activation(chain, ranked, 8, now,
                                            direction="past")
        for w in future:
            self.assertGreaterEqual(w["end"], now,
                "future-direction window must not end before now")
        for w in past:
            self.assertLess(w["end"], now,
                "past-direction window must end strictly before now")


class TestDoubleTransit(unittest.TestCase):
    """Phase 2.5.11.15 — K.N.Rao Double Transit (Jupiter+Saturn) is the
    compulsory fructification filter for ANY timing window. Past, present,
    and future windows must each carry a `double_transit` annotation,
    and the universal directive must always be appended."""

    def _kundli(self):
        return _mk_kundli("Sagittarius", {
            "Sun": 12, "Moon": 1, "Mars": 8, "Mercury": 12,
            "Jupiter": 10, "Venus": 1, "Saturn": 2,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())

    def test_universal_directive_always_appended(self):
        result = compute_travel_window(self._kundli(), intel={}, kp={},
                                         birth={"dob": "1992-11-26"})
        self.assertIn("DOUBLE_TRANSIT_TIMING_RULE_APPLIED",
                       result["llm_directives"])

    def test_past_windows_carry_double_transit_field(self):
        result = compute_travel_window(self._kundli(), intel={}, kp={},
                                         birth={"dob": "1992-11-26"})
        for w in (result.get("past_windows") or []):
            self.assertIn("double_transit", w,
                "every past_window must carry a double_transit annotation")
            dt = w["double_transit"]
            self.assertIn(dt["verdict"],
                {"STRONG", "PARTIAL_J", "PARTIAL_S", "ABSENT", "UNAVAILABLE"})
            self.assertIsInstance(dt["score"], int)

    def test_next_3_windows_carry_double_transit_field(self):
        result = compute_travel_window(self._kundli(), intel={}, kp={},
                                         birth={"dob": "1992-11-26"})
        for w in (result.get("next_3_windows") or []):
            self.assertIn("double_transit", w,
                "every next_3 window must carry a double_transit annotation")
            self.assertIn(w["double_transit"]["verdict"],
                {"STRONG", "PARTIAL_J", "PARTIAL_S", "ABSENT", "UNAVAILABLE"})

    def test_current_window_carries_double_transit_field(self):
        result = compute_travel_window(self._kundli(), intel={}, kp={},
                                         birth={"dob": "1992-11-26"})
        cw = result.get("current_window")
        if cw:  # may be None if no dasha contains "now"
            self.assertIn("double_transit", cw)

    def test_shared_helper_returns_well_formed_dict(self):
        """Direct unit test of the shared helper itself."""
        from datetime import datetime
        from event_timing._shared.double_transit import (
            check_double_transit, CONCERN_HOUSES, midpoint,
        )
        planets = [
            {"name": "Sun",     "sign_idx": 7, "house": 12},
            {"name": "Saturn",  "sign_idx": 0, "house": 2},
            {"name": "Jupiter", "sign_idx": 9, "house": 10},
        ]
        out = check_double_transit({}, datetime(2025, 6, 15), 8,
                                     planets, CONCERN_HOUSES["travel"])
        self.assertIn(out["verdict"],
            {"STRONG", "PARTIAL_J", "PARTIAL_S", "ABSENT", "UNAVAILABLE"})
        self.assertEqual(out["concern_houses"], [3, 9, 12])
        # Midpoint helper symmetry
        a = datetime(2020, 1, 1); b = datetime(2020, 1, 11)
        self.assertEqual(midpoint(a, b), datetime(2020, 1, 6))


class TestPhase2_5_11_16_KpDashaGate(unittest.TestCase):
    """Phase 2.5.11.16 — Moon karaka-floor + KP-dasha significator gate
    (NL→SB→SS chain hits on travel houses 3/9/12) + past_windows[:10] cap
    + PD-lord transit-on-travel-house in STEP 6."""

    def _kundli(self):
        return _mk_kundli("Sagittarius", {
            "Sun": 12, "Moon": 1, "Mars": 8, "Mercury": 12,
            "Jupiter": 10, "Venus": 1, "Saturn": 2,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())

    def test_moon_karaka_floor_always_survives_step1(self):
        """Moon must ALWAYS appear in STEP1 survivors (movement karaka),
        even when it does not lord or occupy a travel house."""
        # Aries lagna: Moon in 5H (not 3/9/12, not lord of any travel
        # house — Moon lords Cancer, which is 4H from Aries lagna, NOT
        # a travel house). Pre-fix it would be filtered out.
        k = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 5, "Mars": 1, "Mercury": 5,
            "Jupiter": 9, "Venus": 4, "Saturn": 7,
            "Rahu": 12, "Ketu": 6,
        })
        d1_map = _step1_d1_filter(k, lagna_si=_SIGN_IDX["Aries"])
        self.assertIn("Moon", d1_map)
        moon = d1_map["Moon"]
        self.assertTrue(moon["in_filter"],
            "Moon must always survive STEP1 (karaka-floor)")
        self.assertGreater(moon.get("d1", 0), 0,
            "Moon karaka-floor entry must carry non-zero d1 score")
        # Karaka-floor link tag must be present
        self.assertTrue(
            any("karaka" in (lnk or "").lower() for lnk in moon.get("links", [])),
            "Moon must carry a karaka link tag")

    def test_kp_dasha_signifies_travel_helper(self):
        """Helper unions pl + sl + sb_houses + ss_houses and counts
        intersection with target_houses [3,9,12]."""
        from event_timing.travel.travel_engine_v1 import (
            _kp_dasha_signifies_travel,
        )
        kp_sig = {"significations": {
            "Moon": {
                "pl": [9],
                "sl": [12],
                "sb_houses": [9, 1],
                "ss_houses": [12, 4],
            },
            "Saturn": {
                "pl": [10],
                "sl": [10],
                "sb_houses": [11],
                "ss_houses": [2],
            },
        }}
        moon_out = _kp_dasha_signifies_travel(kp_sig, "Moon")
        self.assertEqual(sorted(set(moon_out["hits"])), [9, 12])
        self.assertGreaterEqual(moon_out["score"], 2)
        sat_out = _kp_dasha_signifies_travel(kp_sig, "Saturn")
        self.assertEqual(sat_out["hits"], [])
        self.assertEqual(sat_out["score"], 0)
        absent = _kp_dasha_signifies_travel(kp_sig, "Mars")
        self.assertEqual(absent["hits"], [])
        self.assertEqual(absent["score"], 0)

    def test_kp_dasha_helper_supports_list_shape(self):
        """Architect-followup: legacy list-shape KP significations
        (flat list of house ints) must NOT silently score 0."""
        from event_timing.travel.travel_engine_v1 import _kp_dasha_signifies_travel
        kp_list = {"significations": {"Mercury": [9, 12, 3, 4, 5]}}
        r = _kp_dasha_signifies_travel(kp_list, "Mercury")
        self.assertEqual(r["hits"], [3, 9, 12])
        self.assertEqual(r["score"], 3)
        self.assertTrue(any("flat=" in lay for lay in r["layers"]))

    def test_past_windows_cap_raised_to_twelve(self):
        """past_windows length must be ≤ 12 (was [:3], lifted to [:12]
        in Phase 2.5.11.16 with MD-diversity cap of 4 per MD)."""
        result = compute_travel_window(self._kundli(), intel={}, kp={},
                                         birth={"dob": "1992-11-26"})
        past = result.get("past_windows") or []
        self.assertLessEqual(len(past), 12,
            "past_windows must be capped at 12 (Phase 2.5.11.16)")

    def test_past_windows_md_diversity_cap(self):
        """No single MD lord may occupy more than 4 past_windows slots."""
        result = compute_travel_window(self._kundli(), intel={}, kp={},
                                         birth={"dob": "1992-11-26"})
        past = result.get("past_windows") or []
        from collections import Counter
        md_counts = Counter(w.get("md") for w in past)
        for md, n in md_counts.items():
            self.assertLessEqual(n, 4,
                f"MD {md} has {n} past_windows slots (cap is 4)")

    def test_kp_boost_field_present_on_windows(self):
        """Every past/next window must carry kp_boost + kp_hits fields
        (default 0.0 / [] when no KP data supplied)."""
        result = compute_travel_window(self._kundli(), intel={}, kp={},
                                         birth={"dob": "1992-11-26"})
        for w in (result.get("past_windows") or []):
            self.assertIn("kp_boost", w)
            self.assertIn("kp_hits", w)
        for w in (result.get("next_3_windows") or []):
            self.assertIn("kp_boost", w)
            self.assertIn("kp_hits", w)

    def test_kp_boost_promotes_window_when_dasha_lord_signifies(self):
        """When MD/AD/PD lord's KP chain hits travel houses ≥2 times,
        window's kp_boost > 0 and score is raised vs no-KP baseline."""
        kp_with_moon_travel = {
            "significations": {
                "Moon": {
                    "pl": [9], "sl": [12],
                    "sb_houses": [9], "ss_houses": [12],
                },
                "Mercury": {
                    "pl": [12], "sl": [12],
                    "sb_houses": [9], "ss_houses": [12],
                },
            },
        }
        with_kp = compute_travel_window(self._kundli(), intel={},
                                          kp=kp_with_moon_travel,
                                          birth={"dob": "1992-11-26"})
        no_kp = compute_travel_window(self._kundli(), intel={}, kp={},
                                        birth={"dob": "1992-11-26"})
        # At least one window in with_kp should carry kp_boost > 0
        all_w = ((with_kp.get("next_3_windows") or [])
                 + (with_kp.get("past_windows") or []))
        boosted = [w for w in all_w
                   if isinstance(w.get("kp_boost"), (int, float))
                   and w["kp_boost"] > 0]
        self.assertTrue(boosted,
            "with KP travel-significators wired, at least one Moon/Mercury "
            "dasha window must carry kp_boost > 0")
        # Sanity: no-KP baseline has all windows at boost == 0
        all_no = ((no_kp.get("next_3_windows") or [])
                  + (no_kp.get("past_windows") or []))
        self.assertTrue(all(w.get("kp_boost", 0) == 0 for w in all_no))

    def test_step6_dasha_lord_transit_field_present(self):
        """STEP 6 transits dict must carry `dasha_lord_transits` list
        (may be empty if no current dasha lord transits 3/9/12 today)."""
        result = compute_travel_window(self._kundli(), intel={}, kp={},
                                         birth={"dob": "1992-11-26"})
        transits = result.get("transits") or {}
        self.assertIn("dasha_lord_transits", transits,
            "STEP 6 must always emit dasha_lord_transits key")
        self.assertIsInstance(transits["dasha_lord_transits"], list)

    def test_engine_arch_label_updated(self):
        """engine_arch should reflect the new KP-GATE step."""
        result = compute_travel_window(self._kundli(), intel={}, kp={},
                                         birth={"dob": "1992-11-26"})
        self.assertIn("KP-GATE", result.get("engine_arch", ""))


if __name__ == "__main__":
    unittest.main()

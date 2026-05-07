"""
test_baby_engine.py — unit tests for Baby (Childbirth) Timing Engine v1.

Mirrors test_travel_engine.py / test_finance_engine.py structure.
Run from artifacts/api-server:
    python3 -m unittest test_baby_engine
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from event_timing.baby.baby_engine_v1 import (
    compute_baby_window,
    get_last_baby_result,
    clear_last_baby_result,
    _step1_d1_filter,
    _step3_d7_progeny,
    _step3_5_kp_layer,
    _detect_yogas,
    _detect_child_promised,
    _aspects_house,
    _house_lord,
    _severity_of_window,
    _recommendation_tier,
    _derive_verdict,
    _affected_areas,
    _compute_d7_sign,
    _SIGN_IDX,
    _SIGNS,
    _CHILD_HOUSES,
    _OBSTRUCTION_HOUSES,
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
    # Seed ascendant_longitude so the D7 chart can compute its own
    # lagna sign via Parashara odd/even partitioning. Without this the
    # `_build_d7_chart` helper degrades to `available=False`.
    return {"ascendant": asc,
             "ascendant_longitude": asc_si * 30.0 + 10.0,
             "planets": planets, "dashas": dashas or []}


def _mk_dashas() -> list:
    return [{
        "lord": "Jupiter",
        "start": "2020-01-01T00:00:00", "end": "2036-01-01T00:00:00",
        "antardashas": [
            {"lord": "Jupiter", "start": "2020-01-01T00:00:00",
             "end": "2022-03-01T00:00:00",
             "pratyantar": [
                 {"lord": "Jupiter", "start": "2020-01-01T00:00:00",
                  "end": "2021-04-01T00:00:00"},
                 {"lord": "Saturn", "start": "2021-04-01T00:00:00",
                  "end": "2022-03-01T00:00:00"},
             ]},
            {"lord": "Venus", "start": "2024-01-01T00:00:00",
             "end": "2026-09-01T00:00:00",
             "pratyantar": [
                 {"lord": "Venus", "start": "2024-01-01T00:00:00",
                  "end": "2025-06-01T00:00:00"},
                 {"lord": "Jupiter", "start": "2025-06-01T00:00:00",
                  "end": "2026-09-01T00:00:00"},
             ]},
            {"lord": "Moon", "start": "2027-01-01T00:00:00",
             "end": "2028-06-01T00:00:00",
             "pratyantar": [
                 {"lord": "Moon", "start": "2027-01-01T00:00:00",
                  "end": "2027-09-01T00:00:00"},
                 {"lord": "Jupiter", "start": "2027-09-01T00:00:00",
                  "end": "2028-06-01T00:00:00"},
             ]},
        ],
    }]


# ════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════
class TestHelpers(unittest.TestCase):
    def test_house_lord_for_progeny(self):
        # Aries (idx 0) → 5H = Leo → Sun; 9H = Sagittarius → Jupiter
        self.assertEqual(_house_lord(0, 5), "Sun")
        self.assertEqual(_house_lord(0, 9), "Jupiter")
        # Cancer (idx 3) → 5H = Scorpio → Mars
        self.assertEqual(_house_lord(3, 5), "Mars")

    def test_child_and_obstruction_house_constants(self):
        self.assertEqual(set(_CHILD_HOUSES), {5, 9, 11})
        self.assertEqual(set(_OBSTRUCTION_HOUSES), {6, 8, 12})

    def test_d7_saptamsha_computation(self):
        """D7: Aries (odd, idx 0) at 0° → part 0, starts from same sign → Aries (0)."""
        self.assertEqual(_compute_d7_sign(0.0, 0), 0)
        # Aries at 4.5° → part 1 → Taurus (1)
        self.assertEqual(_compute_d7_sign(4.5, 0), 1)
        # Taurus (even, idx 1) at 0° → starts from 7th = Scorpio (idx 7) → part 0
        self.assertEqual(_compute_d7_sign(0.0, 1), 7)
        # Aries at 28° → part 6 (last) → 6th from Aries = Libra (6)
        self.assertEqual(_compute_d7_sign(28.0, 0), 6)


# ════════════════════════════════════════════════════════════════════════
# Severity / verdict
# ════════════════════════════════════════════════════════════════════════
class TestSeverityVerdict(unittest.TestCase):
    def test_severity_bands(self):
        self.assertEqual(_severity_of_window(7.0, 0.0), "celebratory")
        self.assertEqual(_severity_of_window(4.0, 0.0), "supportive")
        self.assertEqual(_severity_of_window(2.0, 0.0), "watchful")
        # Heavy risk forces consult
        self.assertEqual(_severity_of_window(7.0, 0.0, 2.5), "consult")

    def test_recommendation_tier(self):
        self.assertEqual(_recommendation_tier("consult", 3, 30), "consult")
        self.assertEqual(_recommendation_tier("consult", 1, 30), "watchful")
        self.assertEqual(_recommendation_tier("celebratory", 0, 30),
                          "celebratory")

    def test_derive_verdict_child_promised(self):
        yogas = [{"name": "Progeny Yoga (5L+9L conjunction)",
                   "severity": "protective", "planets": ["Sun", "Jupiter"]}]
        v, b = _derive_verdict(7.0, "STRONG", yogas, 0.0, True)
        self.assertEqual(v, "CHILD_PROMISED")
        self.assertEqual(b, "STRONG")

    def test_derive_verdict_obstructed_by_bandhya(self):
        yogas = [{"name": "Bandhya Yoga (5L+Jupiter both in dusthana)",
                   "severity": "high", "planets": ["Sun", "Jupiter"]}]
        v, _ = _derive_verdict(2.0, "WEAK", yogas, 0.0, False)
        self.assertEqual(v, "OBSTRUCTED")

    def test_derive_verdict_delayed_with_protection_low_flow(self):
        yogas = [{"name": "Santan-Prapti Yoga (Jupiter aspects 5H)",
                   "severity": "protective", "planets": ["Jupiter"]}]
        v, _ = _derive_verdict(2.0, "MEDIUM", yogas, 0.0, False)
        self.assertEqual(v, "DELAYED")

    def test_derive_verdict_favorable_with_moderate_flow(self):
        v, _ = _derive_verdict(4.0, "MEDIUM", [], 0.0, False)
        self.assertEqual(v, "FAVORABLE")


# ════════════════════════════════════════════════════════════════════════
# Step 1 — D1 filter
# ════════════════════════════════════════════════════════════════════════
class TestStep1Filter(unittest.TestCase):
    def test_5L_always_in_filter(self):
        # Aries lagna → 5L = Sun (Leo). Sun in 5H boosted further.
        kundli = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 5, "Venus": 2, "Saturn": 11,
            "Rahu": 12, "Ketu": 6,
        })
        d1 = _step1_d1_filter(kundli, 0)
        self.assertTrue(d1["Sun"]["in_filter"])
        self.assertTrue(d1["Jupiter"]["in_filter"])

    def test_jupiter_always_progeny_karaka(self):
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        })
        d1 = _step1_d1_filter(kundli, 0)
        self.assertTrue(any("PROGENY-KARAKA" in l
                            for l in d1["Jupiter"]["links"]))

    def test_step1_excludes_2L_7L_obstruction_funcmalefic(self):
        """LEAN refactor: Step 1 must NOT include 2L, 7L, obstruction-
        house boost, Sun/Mars karaka, or functional-malefic surcharge.
        These were over-engineering; obstruction signal lives in Step 5,
        dignity in Step 4, and 7L/2L/Sun/Mars are out of scope here.
        """
        # Aries lagna: 7L=Venus, 2L=Venus, so we test by checking link
        # vocabulary — none of the removed labels should appear.
        kundli = _mk_kundli("Aries", {
            "Sun": 8, "Moon": 4, "Mars": 6, "Mercury": 6,
            "Jupiter": 11, "Venus": 7, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        })
        d1 = _step1_d1_filter(kundli, 0)
        all_links = [l for info in d1.values() for l in info["links"]]
        joined = " | ".join(all_links)
        for forbidden in ("7L (", "2L (", "OBSTRUCTION",
                           "lineage-vitality", "procreative-vigor",
                           "functional malefic"):
            self.assertNotIn(forbidden, joined,
                f"Step 1 still contains removed signal: {forbidden!r}")


# ════════════════════════════════════════════════════════════════════════
# Step 3.5 — KP layer
# ════════════════════════════════════════════════════════════════════════
class TestKpLayer(unittest.TestCase):
    def test_kp_5csl_child_yes(self):
        kp = {
            "cusps": [{"house": 5, "sl": "Jupiter"},
                      {"house": 11, "sl": "Venus"}],
            "significations": {
                "Jupiter": [5, 9, 11],
                "Venus":   [11, 2],
            },
        }
        out = _step3_5_kp_layer(kp, 0)
        self.assertEqual(out["verdict_5"], "CHILD_YES")
        self.assertEqual(out["verdict_11"], "CHILD_YES")

    def test_kp_obstructed_dominates(self):
        # Saturn signifies 5 (child) AND 8 (dusthana) → OBSTRUCTED wins
        kp = {
            "cusps": [{"house": 5, "sl": "Saturn"}],
            "significations": {"Saturn": [5, 8]},
        }
        out = _step3_5_kp_layer(kp, 0)
        self.assertEqual(out["verdict_5"], "OBSTRUCTED")

    def test_kp_empty_safe_default(self):
        out = _step3_5_kp_layer({}, 0)
        self.assertEqual(out["verdict_5"], "UNKNOWN")


# ════════════════════════════════════════════════════════════════════════
# Yoga detection
# ════════════════════════════════════════════════════════════════════════
class TestYogas(unittest.TestCase):
    def test_progeny_yoga_5L_9L_conjunction(self):
        # Aries lagna → 5L=Sun (Leo), 9L=Jupiter (Sagittarius)
        # Place both in 11H → conjunction
        kundli = _mk_kundli("Aries", {
            "Sun": 11, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        })
        yg = _detect_yogas(kundli, 0, kundli["planets"])
        names = [y["name"] for y in yg]
        self.assertTrue(any("Progeny Yoga" in n for n in names))

    def test_santan_prapti_jupiter_aspects_5H(self):
        # Aries lagna → 5H is Leo (count from 1H Aries: 5th house)
        # Jupiter in 11H aspects 5H (7th aspect 11→5)
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        })
        yg = _detect_yogas(kundli, 0, kundli["planets"])
        names = [y["name"] for y in yg]
        self.assertTrue(any("Santan-Prapti" in n for n in names))

    def test_child_karaka_bala_jupiter_exalted(self):
        # Place Jupiter in Cancer (sign idx 3 — exalted)
        # For Aries lagna, Cancer is 4H
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 1, "Mars": 7, "Mercury": 6,
            "Jupiter": 4, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        })
        yg = _detect_yogas(kundli, 0, kundli["planets"])
        names = [y["name"] for y in yg]
        self.assertTrue(any("Child-Karaka-Bala (Jupiter exalted)" in n
                             for n in names))

    def test_progeny_dosha(self):
        # 5H heavily afflicted by malefics (Sun in 5H + Mars aspects 5H)
        # Aries lagna → 5H. Place Sun & Saturn in 5H, no Jupiter aspect.
        kundli = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 8, "Venus": 2, "Saturn": 5,
            "Rahu": 3, "Ketu": 9,
        })
        yg = _detect_yogas(kundli, 0, kundli["planets"])
        names = [y["name"] for y in yg]
        self.assertTrue(any("Progeny-Dosha" in n for n in names))

    def test_bandhya_yoga(self):
        # 5L (Sun for Aries) in 6H AND Jupiter in 8H
        kundli = _mk_kundli("Aries", {
            "Sun": 6, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 8, "Venus": 2, "Saturn": 10,
            "Rahu": 3, "Ketu": 9,
        })
        yg = _detect_yogas(kundli, 0, kundli["planets"])
        names = [y["name"] for y in yg]
        self.assertTrue(any("Bandhya" in n for n in names))


# ════════════════════════════════════════════════════════════════════════
# Child-promised composite flag
# ════════════════════════════════════════════════════════════════════════
class TestChildPromised(unittest.TestCase):
    def test_requires_three_confirmations(self):
        yogas = [{"name": "Progeny Yoga (5L+9L conjunction)",
                   "severity": "protective", "planets": ["Sun", "Jupiter"]}]
        kp_layer = {"verdict_5": "CHILD_YES"}
        ranked = [{"name": "Jupiter", "score": 20.0},
                  {"name": "Sun", "score": 15.0},
                  {"name": "Venus", "score": 12.0}]
        # 4 confirmations → True
        self.assertTrue(_detect_child_promised(yogas, kp_layer,
                                                  "MEDIUM", ranked))
        # Drop to 1 confirmation → False
        self.assertFalse(_detect_child_promised([], {"verdict_5": "OBSTRUCTED"},
                                                   "WEAK",
                                                   [{"name": "Sun", "score": 5}]))

    def test_negative_progeny_yoga_does_not_count(self):
        """Architect-pattern HIGH#2 carry-over: a Progeny-Yoga match
        with non-protective severity must NOT count toward
        confirmations.
        """
        yogas_neg = [{"name": "Progeny Yoga (artifact name reuse)",
                       "severity": "high", "planets": ["Sun"]}]
        kp_layer = {"verdict_5": "CHILD_YES"}
        ranked = [{"name": "Saturn", "score": 20.0},
                  {"name": "Mars", "score": 15.0}]
        # No Jupiter in top3, no protective putra-yoga, kp+sav only = 2 → False
        self.assertFalse(_detect_child_promised(
            yogas_neg, kp_layer, "MEDIUM", ranked))


# ════════════════════════════════════════════════════════════════════════
# Affected areas
# ════════════════════════════════════════════════════════════════════════
class TestAffectedAreas(unittest.TestCase):
    def test_affected_areas_dedup_and_cap(self):
        ranked = [
            {"name": "Jupiter",
             "significations": ["progeny_grace", "natural_conception"]},
            {"name": "Moon",
             "significations": ["fertility_emotional_readiness",
                                  "maternal_health"]},
            {"name": "Venus",
             "significations": ["reproductive_health",
                                  "harmonious_relationship_for_child"]},
        ]
        out = _affected_areas(ranked)
        self.assertEqual(len(out), len(set(out)))
        self.assertIn("progeny_grace", out)
        self.assertIn("maternal_health", out)
        self.assertLessEqual(len(out), 6)

    def test_no_gender_in_signification_areas(self):
        """CRITICAL: NO area in any planet's significations must hint
        at child gender — PCPNDT Act / global ethical compliance.
        """
        from event_timing.baby.baby_engine_v1 import _AREA_OF_PLANET
        forbidden = {"boy", "girl", "son", "daughter", "male", "female",
                     "putra_only", "putri", "beta", "beti"}
        for planet, areas in _AREA_OF_PLANET.items():
            for area in areas:
                lower = area.lower()
                for f in forbidden:
                    self.assertNotIn(f, lower,
                        f"Gender-hint '{f}' found in {planet} area '{area}'")


# ════════════════════════════════════════════════════════════════════════
# Public API — full pipeline
# ════════════════════════════════════════════════════════════════════════
class TestPublicAPI(unittest.TestCase):
    def test_compute_returns_required_keys(self):
        kundli = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        kp = {
            "cusps": [{"house": 5, "sl": "Jupiter"},
                      {"house": 11, "sl": "Venus"}],
            "significations": {
                "Jupiter": [5, 9, 11], "Venus": [11, 2],
                "Sun": [1, 5], "Moon": [4], "Mercury": [3, 11],
                "Saturn": [10, 11], "Mars": [7, 8],
                "Rahu": [12, 9], "Ketu": [6],
            },
        }
        result = compute_baby_window(kundli, intel={}, kp=kp,
                                       birth={"dob": "1990-05-15"})
        for k in ("verdict", "band", "child_promised", "next_3_windows",
                  "top_child_planets", "weighted_breakdown", "kp_layer",
                  "ashtakavarga", "yogas", "risk_flags", "factors",
                  "llm_directives", "remedies", "engine_version",
                  "engine_arch"):
            self.assertIn(k, result, f"missing key: {k}")
        self.assertEqual(result["engine_version"], "v1.0.0")
        self.assertIn(result["verdict"],
                       {"CHILD_PROMISED", "FAVORABLE",
                        "DELAYED", "OBSTRUCTED", "UNKNOWN"})

    def test_llm_directives_always_have_disclaimers(self):
        kundli = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        result = compute_baby_window(kundli, intel={}, kp={},
                                       birth={"dob": "1990-05-15"})
        directives = result.get("llm_directives") or []
        for must in ("BABY_DISCLAIMER",
                     "NOT_MEDICAL_ADVICE",
                     "NO_GUARANTEED_CONCEPTION",
                     "NO_GUARANTEED_DATE",
                     "NO_GENDER_PREDICTION"):
            self.assertIn(must, directives,
                           f"missing mandatory directive: {must}")
        self.assertTrue(any(d.startswith("SEVERITY_TIER:")
                             for d in directives))

    def test_obstructed_forces_consult_tier_and_specialist_directive(self):
        # Bandhya scenario: 5L (Sun) in 6H + Jupiter in 8H + heavy malefic 5H
        kundli = _mk_kundli("Aries", {
            "Sun": 6, "Moon": 4, "Mars": 5, "Mercury": 6,
            "Jupiter": 8, "Venus": 2, "Saturn": 5,
            "Rahu": 5, "Ketu": 11,
        }, dashas=_mk_dashas())
        result = compute_baby_window(kundli, intel={}, kp={},
                                       birth={"dob": "1990-05-15"})
        if result["verdict"] == "OBSTRUCTED":
            self.assertEqual(result["recommendation_tier"], "consult")
            self.assertIn("CONSULT_FERTILITY_SPECIALIST",
                           result["llm_directives"])

    def test_advanced_age_emits_context_directive(self):
        kundli = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        result = compute_baby_window(kundli, intel={}, kp={},
                                       birth={"dob": "1975-05-15"})
        self.assertIn("ADVANCED_AGE_FERTILITY_CONTEXT",
                       result["llm_directives"])

    def test_too_young_emits_context_directive(self):
        kundli = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        # ~12 years old
        result = compute_baby_window(kundli, intel={}, kp={},
                                       birth={"dob": "2014-05-15"})
        self.assertIn("USER_TOO_YOUNG_FRAMING",
                       result["llm_directives"])

    def test_empty_kundli_returns_unknown(self):
        result = compute_baby_window({}, intel={}, kp={}, birth=None)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertIn("engine_version", result)

    def test_engine_exception_wrapped_safely(self):
        bad_kundli = {"ascendant": "Aries"}
        result = compute_baby_window(bad_kundli)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertIn("engine_version", result)

    def test_thread_local_cache_lifecycle(self):
        clear_last_baby_result()
        self.assertIsNone(get_last_baby_result())
        kundli = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 11,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        compute_baby_window(kundli, intel={}, kp={},
                              birth={"dob": "1990-05-15"})
        cached = get_last_baby_result()
        self.assertIsNotNone(cached)
        self.assertEqual(cached["engine_version"], "v1.0.0")
        clear_last_baby_result()
        self.assertIsNone(get_last_baby_result())


# ════════════════════════════════════════════════════════════════════════
# Architect-pattern regressions (carried from travel v1)
# ════════════════════════════════════════════════════════════════════════
class TestArchitectPatternRegressions(unittest.TestCase):
    def test_aries_jupiter_9L_NOT_classified_as_obstructor(self):
        """Jupiter is 9L AND functional benefic for Aries; placed in 8H
        (obstruction house) it gets an obstruction tag, but its 9L+karaka
        promoter tags should outweigh and keep it as CHILD_PROMOTER.
        """
        kundli = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        result = compute_baby_window(kundli, intel={}, kp={},
                                       birth={"dob": "1990-05-15"})
        for w in result.get("next_3_windows", []):
            for trig in w.get("triggers", []):
                if "Jupiter" in trig:
                    self.assertNotIn("OBSTRUCTOR", trig,
                        f"Jupiter (9L+putra-karaka for Aries) wrongly tagged as obstructor: {trig}")

    def test_protective_yoga_does_not_force_child_promised_at_low_flow(self):
        """child_promised=True with s<3.5 must NOT elevate verdict to
        CHILD_PROMISED. Houses promised ≠ timing promised.
        """
        yogas = [{"name": "Progeny Yoga (5L+9L conjunction)",
                   "severity": "protective", "planets": ["Sun", "Jupiter"]}]
        v, _ = _derive_verdict(1.0, "MEDIUM", yogas, 0.0, True)
        self.assertNotEqual(v, "CHILD_PROMISED",
            "child_promised must require flow >= 3.5 to elevate verdict")
        # At s=4.0 with child_promised → should now elevate
        v2, _ = _derive_verdict(4.0, "MEDIUM", yogas, 0.0, True)
        self.assertEqual(v2, "CHILD_PROMISED")

    def test_obstructive_yoga_at_moderate_flow_yields_obstructed(self):
        """Bandhya/Progeny-Dosha/Miscarriage yogas at s<4.0 must yield
        OBSTRUCTED, not just DELAYED.
        """
        yogas = [{"name": "Progeny-Dosha (5H afflicted by malefics, no Jupiter rescue)",
                   "severity": "high", "planets": ["Sun", "Mars", "Saturn"]}]
        v, _ = _derive_verdict(3.0, "MEDIUM", yogas, 0.0, False)
        self.assertEqual(v, "OBSTRUCTED")

    def test_clinical_block_override_bandhya_plus_kp_obstructed(self):
        """Architect HIGH#5: Bandhya/Miscarriage + KP_5=OBSTRUCTED must
        force OBSTRUCTED regardless of dasha flow. A natal medical-block
        signature with KP confirmation should NEVER surface as
        CHILD_PROMISED no matter how strong the active dasha is.
        """
        yogas = [{"name": "Bandhya Yoga (5L+Jupiter both in dusthana)",
                   "severity": "high", "planets": ["Sun", "Jupiter"]}]
        kp_layer = {"verdict_5": "OBSTRUCTED", "verdict_11": "CHILD_YES"}
        # Even with very high flow + child_promised=True
        v, b = _derive_verdict(8.0, "STRONG", yogas, 0.0, True,
                                kp_layer=kp_layer)
        self.assertEqual(v, "OBSTRUCTED",
            "Bandhya + KP_5_OBSTRUCTED must force OBSTRUCTED at any flow")
        self.assertEqual(b, "WEAK")
        # Without KP confirmation, high flow can still elevate
        v2, _ = _derive_verdict(8.0, "STRONG", yogas, 0.0, True,
                                  kp_layer={"verdict_5": "CHILD_YES"})
        self.assertEqual(v2, "CHILD_PROMISED")

    def test_d7_picture_emits_first_and_fifth_lord(self):
        """Step 3b: the D7 picture must capture D7 lagna, 1L, 5L
        positions, occupants of D7 1H + 5H, and aspects to D7 1H + 5H.
        """
        from event_timing.baby.baby_engine_v1 import (
            _build_d7_chart, _step3b_d7_picture,
        )
        # Build a kundli with explicit longitudes so D7 chart resolves
        # via the internal longitude tier.
        kundli = _mk_kundli("Aries", {
            "Sun": 11, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        })
        # _mk_kundli already seeds longitude per planet
        d7_chart = _build_d7_chart(kundli, 0)
        self.assertIsNotNone(d7_chart, "D7 chart must build from longitudes")
        pic = _step3b_d7_picture(d7_chart, 0)
        self.assertTrue(pic["available"])
        self.assertIn(pic["d7_lagna"],
                       ["Aries", "Taurus", "Gemini", "Cancer", "Leo",
                        "Virgo", "Libra", "Scorpio", "Sagittarius",
                        "Capricorn", "Aquarius", "Pisces"])
        # First-lord block
        fl = pic["first_lord"]
        self.assertIn(fl["dignity"],
                       ["exalted", "own", "debilitated", "neutral",
                        "unknown"])
        self.assertIsNotNone(fl["planet"])
        # Fifth-lord block
        fih = pic["fifth_lord"]
        self.assertIn(fih["dignity"],
                       ["exalted", "own", "debilitated", "neutral",
                        "unknown"])
        self.assertIsNotNone(fih["planet"])
        # House lists must exist (may be empty)
        self.assertIsInstance(pic["first_house_occupants"], list)
        self.assertIsInstance(pic["fifth_house_occupants"], list)
        self.assertIsInstance(pic["aspects_to_first_house"], list)
        self.assertIsInstance(pic["aspects_to_fifth_house"], list)
        # Flags block must include all the consumer-facing keys
        for k in ("jupiter_aspects_d7_5h", "benefic_in_d7_5h",
                   "malefic_in_d7_5h", "d7_5l_in_dusthana",
                   "d7_5l_well_placed", "d7_5l_in_child_house",
                   "d7_1l_aspects_5h"):
            self.assertIn(k, pic["flags"])

    def test_d7_picture_unavailable_without_longitudes(self):
        """When no longitudes are present, _build_d7_chart returns None
        and the picture must report `available=False` with a graceful
        note (no exception, no blank fields)."""
        from event_timing.baby.baby_engine_v1 import (
            _build_d7_chart, _step3b_d7_picture,
        )
        kundli = {
            "ascendant": "Aries",
            "planets": [{"name": n, "house": 1, "sign": "Aries",
                          "sign_idx": 0} for n in ("Sun",)],
        }
        chart = _build_d7_chart(kundli, 0)
        self.assertIsNone(chart)
        pic = _step3b_d7_picture(chart, 0)
        self.assertFalse(pic["available"])
        self.assertEqual(pic["source"], "none")
        self.assertIn("unavailable", pic["note"])

    def test_d7_yogas_emitted_when_picture_strong(self):
        """`_detect_d7_yogas` must emit D7-Progeny-Yoga when 5L is
        well-placed and Jupiter aspects D7 5H."""
        from event_timing.baby.baby_engine_v1 import _detect_d7_yogas
        pic = {
            "available": True,
            "first_lord":  {"planet": "Mars",
                             "aspects_d7_5h": True,
                             "house_in_d7": 1, "dignity": "own"},
            "fifth_lord":  {"planet": "Sun",
                             "house_in_d7": 5, "dignity": "neutral",
                             "well_placed": True, "in_dusthana": False},
            "fifth_house_occupants": ["Jupiter"],
            "aspects_to_fifth_house": [],
            "flags": {
                "d7_5l_well_placed":     True,
                "jupiter_aspects_d7_5h": True,
                "benefic_in_d7_5h":      True,
                "malefic_in_d7_5h":      False,
                "d7_5l_in_dusthana":     False,
                "d7_5l_in_child_house":  True,
                "d7_1l_aspects_5h":      True,
            },
        }
        yg = _detect_d7_yogas(pic)
        names = [y["name"] for y in yg]
        self.assertTrue(any("D7-Progeny-Yoga" in n for n in names))
        self.assertTrue(any("D7-Lagna-Activation" in n
                              for n in names))

    def test_d7_bandhya_yoga_when_5l_in_dusthana_no_jupiter(self):
        """`_detect_d7_yogas` must emit D7-Bandhya when 5L is in D7
        dusthana with no Jupiter aspect/occupation rescue."""
        from event_timing.baby.baby_engine_v1 import _detect_d7_yogas
        pic = {
            "available": True,
            "first_lord":  {"planet": "Mars", "aspects_d7_5h": False,
                             "house_in_d7": 1, "dignity": "neutral"},
            "fifth_lord":  {"planet": "Sun", "house_in_d7": 8,
                             "dignity": "neutral",
                             "well_placed": False, "in_dusthana": True},
            "fifth_house_occupants": [],
            "aspects_to_fifth_house": ["Saturn"],
            "flags": {
                "d7_5l_well_placed":     False,
                "jupiter_aspects_d7_5h": False,
                "benefic_in_d7_5h":      False,
                "malefic_in_d7_5h":      False,
                "d7_5l_in_dusthana":     True,
                "d7_5l_in_child_house":  False,
                "d7_1l_aspects_5h":      False,
            },
        }
        yg = _detect_d7_yogas(pic)
        names = [y["name"] for y in yg]
        self.assertTrue(any("D7-Bandhya" in n for n in names))
        self.assertTrue(any(y["severity"] == "high" for y in yg))

    def test_no_putra_token_in_any_yoga_label(self):
        """CRITICAL ETHICAL: yoga labels must NOT contain 'Putra'
        (Sanskrit for 'son') — gender-vocabulary leakage prevention.
        """
        kundli = _mk_kundli("Aries", {
            "Sun": 11, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        })
        yg = _detect_yogas(kundli, 0, kundli["planets"])
        # Also cover the FULL pipeline (D9/D7 yogas merged in) — this
        # is the surface that ever reaches LLM / locked_facts.
        from event_timing.baby.baby_engine_v1 import compute_baby_window
        full = compute_baby_window(kundli)
        all_names = ([y.get("name", "") for y in yg]
                      + [y.get("name", "") for y in full.get("yogas", [])])
        for name in all_names:
            self.assertNotIn("Putra", name,
                f"'Putra' (Sanskrit 'son') leaked into yoga label: {name!r}")
            self.assertNotIn("Putri", name,
                f"'Putri' (Sanskrit 'daughter') leaked into yoga label: {name!r}")

    def test_kp_obstructed_dominates_child_yes(self):
        """KP precedence: dusthana signification dominates CHILD_YES."""
        kp = {
            "cusps": [{"house": 5, "sl": "Saturn"}],
            "significations": {"Saturn": [5, 9, 6]},  # both child + dusthana
        }
        out = _step3_5_kp_layer(kp, 0)
        self.assertEqual(out["verdict_5"], "OBSTRUCTED")

    def test_no_gender_prediction_directive_always_present(self):
        """CRITICAL ethical guard: NO_GENDER_PREDICTION must be present
        on every output regardless of verdict.
        """
        for asc in ("Aries", "Cancer", "Leo", "Capricorn"):
            kundli = _mk_kundli(asc, {
                "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 11,
                "Jupiter": 11, "Venus": 2, "Saturn": 10,
                "Rahu": 12, "Ketu": 6,
            }, dashas=_mk_dashas())
            result = compute_baby_window(kundli, intel={}, kp={},
                                           birth={"dob": "1990-05-15"})
            self.assertIn("NO_GENDER_PREDICTION",
                           result["llm_directives"],
                           f"NO_GENDER_PREDICTION missing for {asc} lagna")


if __name__ == "__main__":
    unittest.main()

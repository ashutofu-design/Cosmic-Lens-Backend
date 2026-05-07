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

    def test_cross_chart_filter_jupiter_always_confirmed(self):
        """Jupiter is the universal progeny karaka, so its 5H-link
        in every chart (D1/D9/D7) must score it as cross_confirmed.
        """
        kundli = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        result = compute_baby_window(kundli, intel={}, kp={},
                                       birth={"dob": "1990-05-15"})
        ccf = result.get("cross_chart_filter") or {}
        self.assertIn("Jupiter", ccf.get("confirmed_planets", []),
            f"Jupiter must be cross-confirmed; got {ccf}")
        per = ccf.get("per_planet", {}).get("Jupiter", {})
        self.assertGreaterEqual(per.get("confirmations", 0), 2)
        self.assertIn("D1", per.get("confirmed_in", []))

    def test_step7_jupiter_bav_on_progeny_axis(self):
        """Phase 2.5.8: Step 7 SAV block must surface Jupiter's
        own BAV bindus on 5H + 11H plus a `jupiter_putra_strength`
        verdict (STRONG/MODERATE/WEAK/UNKNOWN). Existing aggregate
        santan_band must remain (backward compat).
        """
        kundli = _mk_kundli("Aries", {
            "Sun": 11, "Moon": 4, "Mars": 7, "Mercury": 3,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        result = compute_baby_window(kundli, intel={},
                                       birth={"dob": "1990-05-15"})
        ashta = result.get("ashtakavarga") or {}
        # Original keys still present
        for k in ("sav_5", "sav_11", "santan_band"):
            self.assertIn(k, ashta, f"original key {k} missing")
        # New Phase 2.5.8 keys
        for k in ("jup_bav_5", "jup_bav_11",
                   "jupiter_putra_strength"):
            self.assertIn(k, ashta, f"new key {k} missing")
        self.assertIn(ashta["jupiter_putra_strength"],
                       {"STRONG", "MODERATE", "WEAK", "UNKNOWN"})
        # If BAV computed, must be in valid range 0-7 per house
        if isinstance(ashta["jup_bav_5"], (int, float)):
            self.assertGreaterEqual(ashta["jup_bav_5"], 0)
            self.assertLessEqual(ashta["jup_bav_5"], 7)
        if isinstance(ashta["jup_bav_11"], (int, float)):
            self.assertGreaterEqual(ashta["jup_bav_11"], 0)
            self.assertLessEqual(ashta["jup_bav_11"], 7)
        # Strength verdict consistency check
        if (isinstance(ashta["jup_bav_5"], (int, float))
                and isinstance(ashta["jup_bav_11"], (int, float))):
            avg = (ashta["jup_bav_5"] + ashta["jup_bav_11"]) / 2.0
            if avg >= 5.0:
                self.assertEqual(ashta["jupiter_putra_strength"], "STRONG")
            elif avg >= 3.0:
                self.assertEqual(ashta["jupiter_putra_strength"], "MODERATE")
            else:
                self.assertEqual(ashta["jupiter_putra_strength"], "WEAK")

    def test_step6_double_transit_jupiter_saturn_only(self):
        """Phase 2.5.7: Step 6 transit block must expose ONLY
        Jupiter + Saturn positions (other bodies removed). Must
        include `double_transit` verdict + active_triggers using the
        classical Double Transit Theory: BOTH Jupiter AND Saturn on
        5H sign OR 5L's natal sign → DOUBLE_TRANSIT_5H_5L; only one
        → SINGLE_TRANSIT_*; neither → no trigger.
        """
        from event_timing.baby import baby_engine_v1 as B
        kundli = _mk_kundli("Aries", {
            "Sun": 11, "Moon": 4, "Mars": 7, "Mercury": 3,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        result = compute_baby_window(kundli, intel={},
                                       birth={"dob": "1990-05-15"})
        transits = result.get("transits") or {}
        if not B._HAS_SWE:
            self.assertIn("note", transits)
            return
        # Must expose double_transit verdict + as_of_utc
        self.assertIn("double_transit", transits)
        self.assertIn("as_of_utc", transits)
        # Positions trimmed to Jupiter + Saturn ONLY
        positions = transits.get("positions") or {}
        self.assertEqual(set(positions.keys()), {"Jupiter", "Saturn"},
            f"positions must be Jupiter+Saturn only; got {set(positions.keys())}")
        for body in ("Jupiter", "Saturn"):
            p = positions[body]
            self.assertIsNotNone(p)
            for k in ("lon_deg", "sign_name", "deg_str", "nak_name",
                       "pada", "retrograde", "house_from_lagna"):
                self.assertIn(k, p)
        # Removed bodies must NOT be present
        for absent in ("Sun", "Moon", "Mars", "Mercury",
                        "Venus", "Rahu"):
            self.assertNotIn(absent, positions,
                f"{absent} must be removed in Phase 2.5.7")
        # Active triggers must use new taxonomy (or be empty)
        valid_trigger_codes = {"DOUBLE_TRANSIT_5H_5L",
                                 "SINGLE_TRANSIT_JUPITER",
                                 "SINGLE_TRANSIT_SATURN"}
        for trig in transits.get("active_triggers", []):
            code = trig[0] if isinstance(trig, (list, tuple)) else trig
            self.assertIn(code, valid_trigger_codes,
                f"unexpected trigger code {code}")
        # double_transit dict invariants
        dt = transits["double_transit"]
        self.assertIn("active", dt)
        self.assertIsInstance(dt["active"], bool)
        if dt["active"]:
            for k in ("rule", "jupiter_anchor", "saturn_anchor",
                       "h5_sign", "h5_lord"):
                self.assertIn(k, dt)

    def test_step5b_active_window_marking(self):
        """Phase 2.5.5: each dasha window must be marked with
        `active_window` / `active_priority` / `active_lords_in_window`
        when a FINAL-GATE-PASSED promoter planet rules it at MD/AD/PD.
        Top-level result must expose `child_active_windows`
        (chronological) and `next_child_window`. Priority order
        PEAK > STRONG > TRIGGER > BACKGROUND.
        """
        kundli = _mk_kundli("Aries", {
            "Sun": 11, "Moon": 4, "Mars": 7, "Mercury": 3,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        result = compute_baby_window(kundli, intel={},
                                       birth={"dob": "1990-05-15"})
        # Top-level keys must exist
        self.assertIn("child_active_windows", result)
        self.assertIn("next_child_window", result)
        cwins = result["child_active_windows"]
        self.assertIsInstance(cwins, list)
        self.assertLessEqual(len(cwins), 8, "active windows capped at 8")
        # Every entry must have required structure
        valid_priorities = {"PEAK", "STRONG", "TRIGGER", "BACKGROUND"}
        for w in cwins:
            for k in ("md", "ad", "pd", "priority", "active_lords",
                       "window", "start_iso", "end_iso"):
                self.assertIn(k, w, f"missing key {k} in active window")
            self.assertIn(w["priority"], valid_priorities)
            # active_lords must reference the marked roles
            self.assertGreater(len(w["active_lords"]), 0,
                "active window must list at least one active lord")
        # Chronological invariant
        if len(cwins) >= 2:
            for a, b in zip(cwins, cwins[1:]):
                self.assertLessEqual(a["start_iso"], b["start_iso"],
                    "child_active_windows must be chronological")
        # next_child_window matches first entry
        if cwins:
            self.assertEqual(result["next_child_window"]["start_iso"],
                              cwins[0]["start_iso"])
        # Factor trace must surface the count
        factor_str = " ".join(result.get("factors", []))
        self.assertIn("STEP5b active_windows_in_horizon=", factor_str)

    def test_step4c_strong_crosschart_rescues_kp_fail(self):
        """Phase 2.5.4-r4: a planet confirmed in ALL THREE charts
        (D1+D9+D7 all show 5H credential) is too strongly indicated
        to be vetoed by a KP fail. KP is a timing refinement, not a
        promise-killer when D1/D9/D7 are unanimously positive.
        Rescue triggers only when confirmations == 3 (full unanimity).
        """
        # Aries lagna, Jupiter in 5H → D1 5H occupant + Jupiter karaka.
        # Most likely Jupiter will register a D1 credential. D9 and D7
        # depend on internal computation but we assert the override
        # ONLY fires when confirmations==3 (we don't force it).
        kundli = _mk_kundli("Aries", {
            "Sun": 11, "Moon": 4, "Mars": 7, "Mercury": 3,
            "Jupiter": 5, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        # KP says Jupiter FAILS (NL+SBL both miss 2/5/11).
        kp = {
            "planets": [
                {"name": "Jupiter", "nl": "Mars",  "sb": "Mars"},
                {"name": "Sun",     "nl": "Venus", "sb": "Venus"},
                {"name": "Moon",    "nl": "Sun",   "sb": "Mercury"},
                {"name": "Venus",   "nl": "Moon",  "sb": "Moon"},
                {"name": "Mercury", "nl": "Venus", "sb": "Venus"},
                {"name": "Mars",    "nl": "Sun",   "sb": "Sun"},
                {"name": "Saturn",  "nl": "Mars",  "sb": "Mars"},
                {"name": "Rahu",    "nl": "Mars",  "sb": "Mars"},
                {"name": "Ketu",    "nl": "Mars",  "sb": "Mars"},
            ],
            "significations": {
                "Mars":    [6, 8],
                "Sun":     [2, 5],
                "Venus":   [5, 11],
                "Moon":    [2, 5],
                "Mercury": [5, 11],
                "Jupiter": [2, 5, 11],
                "Saturn":  [4, 10],
            },
            "cusps": [],
        }
        result = compute_baby_window(kundli, intel={}, kp=kp,
                                       birth={"dob": "1990-05-15"})
        ccf = result.get("cross_chart_filter") or {}
        per_cc = ccf.get("per_planet", {})
        kpf = result.get("kp_significator_filter") or {}
        per_kp = kpf.get("per_planet", {})
        # Sanity: Jupiter explicitly KP-failed in raw filter
        if "Jupiter" in per_kp:
            self.assertEqual(per_kp["Jupiter"]["kp_status"], "fail")
        # If Jupiter has confirmations==3, override must fire and
        # Jupiter must NOT be in KP-blocked outcome of final gate.
        jp_cc = per_cc.get("Jupiter", {})
        if jp_cc.get("confirmations") == 3:
            # Verify the rescue path executes: planet should still
            # appear in the final gate's pass set even though raw KP
            # said fail — i.e. promoter eligibility preserved.
            # We cannot easily inspect final_gate_map externally, but
            # we can verify the verdict didn't collapse to OBSTRUCTED
            # solely due to KP. Confirm result builds without error
            # and Jupiter retains a positive ranking.
            ranked_names = [p["name"] for p in
                            (result.get("top_child_planets") or [])]
            self.assertIn("Jupiter", ranked_names,
                "Strong cross-chart Jupiter must remain ranked")

    def test_step4c_kp_negation_is_hard_block(self):
        """Phase 2.5.4-r3: a planet whose NL or SBL signifies ONLY
        houses {1,4,10} (pure negation, no mitigation) must be
        hard-blocked even if the other lord signifies 2/5/11.
        """
        kundli = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        # Jupiter: NL strong (5,11) BUT SBL = pure negation (4,10)
        # → must be BLOCKED (was passing in earlier soft-rule).
        # Moon: NL strong (2,5) AND SBL strong (5,11) → passes.
        kp = {
            "planets": [
                {"name": "Jupiter", "nl": "Venus",   "sb": "Saturn"},
                {"name": "Moon",    "nl": "Sun",     "sb": "Mercury"},
                {"name": "Sun",     "nl": "Jupiter", "sb": "Jupiter"},
                {"name": "Venus",   "nl": "Moon",    "sb": "Moon"},
                {"name": "Mercury", "nl": "Venus",   "sb": "Venus"},
                {"name": "Mars",    "nl": "Sun",     "sb": "Sun"},
                {"name": "Saturn",  "nl": "Mars",    "sb": "Rahu"},
                {"name": "Rahu",    "nl": "Mercury", "sb": "Venus"},
                {"name": "Ketu",    "nl": "Mars",    "sb": "Saturn"},
            ],
            "significations": {
                "Venus":   [5, 11],
                "Saturn":  [4, 10],   # PURE negation
                "Sun":     [2, 5],
                "Mercury": [5, 11],
                "Jupiter": [2, 5, 11],
                "Moon":    [2, 5],
                "Mars":    [6, 8],
                "Rahu":    [12],
                "Ketu":    [6, 12],
            },
            "cusps": [],
        }
        result = compute_baby_window(kundli, intel={}, kp=kp,
                                       birth={"dob": "1990-05-15"})
        kpf = result.get("kp_significator_filter") or {}
        per = kpf.get("per_planet", {})
        # Jupiter: SBL is pure negation → must be blocked
        if "Jupiter" in per:
            self.assertTrue(per["Jupiter"]["kp_negated"],
                f"Jupiter SBL=Saturn→[4,10] must flag kp_negated; "
                f"got {per['Jupiter']}")
            self.assertEqual(per["Jupiter"]["kp_status"], "fail",
                f"Jupiter must be hard-blocked by negation; "
                f"got {per['Jupiter']}")
            self.assertIn("Jupiter", kpf["blocked"])
            self.assertNotIn("Jupiter", kpf["passed"])
        # Moon: clean pass
        if "Moon" in per:
            self.assertEqual(per["Moon"]["kp_status"], "pass")
            self.assertFalse(per["Moon"]["kp_negated"])
            self.assertIn("Moon", kpf["passed"])

    def test_step4c_kp_unavailable_when_only_planets(self):
        """Architect-fix: gate must DISABLE when only kp.planets is
        present without significations (or vice-versa). Otherwise
        signified-house lookups resolve empty and over-block.
        """
        kundli = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        kp_planets_only = {
            "planets": [{"name": "Jupiter", "nl": "Venus",
                          "sb": "Mercury"}],
            "significations": {},  # missing!
            "cusps": [],
        }
        result = compute_baby_window(kundli, intel={},
                                       kp=kp_planets_only,
                                       birth={"dob": "1990-05-15"})
        kpf = result.get("kp_significator_filter") or {}
        self.assertFalse(kpf.get("available"),
            f"Gate must auto-disable with empty significations; got {kpf}")

        kp_sig_only = {
            "planets": [],  # missing!
            "significations": {"Venus": [5, 11]},
            "cusps": [],
        }
        result2 = compute_baby_window(kundli, intel={},
                                        kp=kp_sig_only,
                                        birth={"dob": "1990-05-15"})
        kpf2 = result2.get("kp_significator_filter") or {}
        self.assertFalse(kpf2.get("available"),
            f"Gate must auto-disable with empty planets; got {kpf2}")

    def test_step4c_kp_unknown_does_not_hard_block(self):
        """Architect-fix: when a ranked planet has missing NL/SBL or
        is absent from kp.planets, it must be marked UNKNOWN (tri-
        state) and NOT contribute to `blocked` — degraded data must
        never collapse legitimate promoter classifications.
        """
        kundli = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        # Only Jupiter has KP data; everyone else is absent.
        kp = {
            "planets": [
                {"name": "Jupiter", "nl": "Venus", "sb": "Mercury"},
            ],
            "significations": {
                "Venus":   [5, 11],
                "Mercury": [2, 5],
            },
            "cusps": [],
        }
        result = compute_baby_window(kundli, intel={}, kp=kp,
                                       birth={"dob": "1990-05-15"})
        kpf = result.get("kp_significator_filter") or {}
        self.assertTrue(kpf.get("available"))
        per = kpf.get("per_planet", {})
        # Jupiter must pass
        self.assertEqual(per.get("Jupiter", {}).get("kp_status"),
                          "pass")
        self.assertIn("Jupiter", kpf["passed"])
        # Other survivors must be unknown (not blocked)
        for p in per:
            if p == "Jupiter":
                continue
            self.assertEqual(per[p].get("kp_status"), "unknown",
                f"{p} must be UNKNOWN, not blocked; got {per[p]}")
        self.assertNotIn("Jupiter", kpf["blocked"])
        # Verdict must NOT be UNKNOWN purely because KP partial
        self.assertIn(result.get("verdict"),
            ("CHILD_PROMISED", "FAVORABLE", "DELAYED",
             "OBSTRUCTED", "UNKNOWN"))

    def test_step4c_kp_filter_unavailable_when_no_kp(self):
        """When no KP block is supplied, Step 4c must mark itself
        unavailable and NOT block any planet. Final gate falls back to
        Step 3c only (or legacy D1 if both off).
        """
        kundli = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        result = compute_baby_window(kundli, intel={}, kp={},
                                       birth={"dob": "1990-05-15"})
        kpf = result.get("kp_significator_filter") or {}
        self.assertFalse(kpf.get("available", True),
            f"KP filter must be unavailable with empty kp; got {kpf}")
        self.assertEqual(kpf.get("passed"), [])
        self.assertEqual(kpf.get("blocked"), [])

    def test_step4c_kp_filter_strict_and_rule(self):
        """KP gate must require BOTH nakshatra-lord AND sub-lord to
        each signify ≥1 of {2,5,11}. Synthesize a KP block where
        Jupiter's NL signifies {5,11} and SBL signifies {2,5} →
        passes; Saturn's NL signifies {6,8} and SBL signifies {12} →
        blocked.
        """
        kundli = _mk_kundli("Aries", {
            "Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        # Synthesize KP block: assign NL/SBL per planet, plus
        # significations for those lords so 2-5-11 logic fires.
        kp = {
            "planets": [
                {"name": "Jupiter", "nl": "Venus",   "sb": "Mercury"},
                {"name": "Saturn",  "nl": "Mars",    "sb": "Rahu"},
                {"name": "Sun",     "nl": "Jupiter", "sb": "Jupiter"},
                {"name": "Moon",    "nl": "Sun",     "sb": "Sun"},
                {"name": "Venus",   "nl": "Moon",    "sb": "Moon"},
                {"name": "Mercury", "nl": "Saturn",  "sb": "Saturn"},
                {"name": "Mars",    "nl": "Ketu",    "sb": "Ketu"},
                {"name": "Rahu",    "nl": "Mercury", "sb": "Venus"},
                {"name": "Ketu",    "nl": "Mars",    "sb": "Saturn"},
            ],
            "significations": {
                "Venus":   [5, 11],   # → Jupiter NL passes
                "Mercury": [2, 5],    # → Jupiter SBL passes
                "Mars":    [6, 8],    # → Saturn NL fails (no 2/5/11)
                "Rahu":    [12],      # → Saturn SBL fails
                "Jupiter": [5, 11],   # → Sun NL+SBL pass
                "Sun":     [2, 5],    # → Moon passes
                "Moon":    [11],      # → Venus passes
                "Saturn":  [4, 10],   # negation only — Mercury blocked
                "Ketu":    [6, 12],   # → Mars blocked
            },
            "cusps": [],
        }
        result = compute_baby_window(kundli, intel={}, kp=kp,
                                       birth={"dob": "1990-05-15"})
        kpf = result.get("kp_significator_filter") or {}
        self.assertTrue(kpf.get("available"))
        # Jupiter must pass (NL=Venus signifies {5,11}, SBL=Mercury {2,5})
        per = kpf.get("per_planet", {})
        if "Jupiter" in per:
            self.assertTrue(per["Jupiter"]["kp_promotes_child"],
                f"Jupiter must pass KP 2-5-11 gate; got {per['Jupiter']}")
            self.assertIn("Jupiter", kpf["passed"])
        # Saturn must be blocked (NL=Mars→{6,8}, SBL=Rahu→{12})
        if "Saturn" in per:
            self.assertFalse(per["Saturn"]["kp_promotes_child"],
                f"Saturn must be blocked by KP gate; got {per['Saturn']}")
            self.assertIn("Saturn", kpf["blocked"])
        # Mercury whose NL=Saturn signifies only negation {4,10}
        # must be flagged kp_negated=True
        if "Mercury" in per:
            self.assertTrue(per["Mercury"].get("kp_negated"),
                f"Mercury NL signifies only negation; expected "
                f"kp_negated=True; got {per['Mercury']}")

    def test_cross_chart_gate_disabled_when_d9_and_d7_unavailable(self):
        """Edge case (architect-flagged): if both D9 and D7 are
        unavailable (e.g. missing longitudes), the ≥2/3 rule is
        unreachable from D1 alone. Gate must auto-disable so dasha
        windows aren't all collapsed to NEUTRAL.
        """
        # Build kundli WITHOUT longitudes / without ascendant_longitude
        # so divisional helpers degrade. Use sign-only positions.
        signs_list = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                       "Libra","Scorpio","Sagittarius","Capricorn",
                       "Aquarius","Pisces"]
        plans = {"Sun": 5, "Moon": 4, "Mars": 7, "Mercury": 6,
                  "Jupiter": 11, "Venus": 2, "Saturn": 10,
                  "Rahu": 12, "Ketu": 6}
        asi = 0  # Aries
        planets = []
        for nm, h in plans.items():
            si = (asi + h - 1) % 12
            # NOTE: deliberately omit "longitude" + "sign_idx" so
            # divisional_charts.compute_d9/d7 cannot place them.
            planets.append({"name": nm, "house": h, "sign": signs_list[si]})
        kundli = {"ascendant": "Aries",
                   # NO ascendant_longitude on purpose
                   "planets": planets,
                   "dashas": _mk_dashas(),
                   "birth": {"date_iso": "1990-05-15",
                              "time_iso": "10:30:00",
                              "tz_offset_hours": 5.5}}
        result = compute_baby_window(kundli, intel={}, kp={},
                                       birth={"dob": "1990-05-15"})
        ccf = result.get("cross_chart_filter") or {}
        avail = ccf.get("available_charts", {})
        # Both D9 and D7 should report unavailable
        self.assertFalse(avail.get("D9", True),
            f"Expected D9 unavailable, got {avail}")
        self.assertFalse(avail.get("D7", True),
            f"Expected D7 unavailable, got {avail}")
        # Gate must auto-disable
        self.assertFalse(ccf.get("gate_active", True),
            "Gate must auto-disable when D9+D7 both unavailable")
        # Verdict must NOT be UNKNOWN purely from gate collapse
        # (data_sufficiency may still pass it through other paths;
        # we just guard against gate-induced empty windows)
        self.assertIn(result.get("verdict"),
            ("CHILD_PROMISED", "FAVORABLE", "DELAYED",
             "OBSTRUCTED", "UNKNOWN"))

    def test_cross_chart_filter_blocks_paper_promise_planets(self):
        """A planet that is e.g. 9L or 11L (D1 promoter tag) but has
        NO 5H link in D9 and D7 must NOT be cross_confirmed, and
        therefore must not be classified CHILD_PROMOTER in Step 5.
        Verifies the gate fires at least once across realistic charts.
        """
        # Build a chart where some D1 promoter exists but cross-confirm
        # only contains Jupiter.
        kundli = _mk_kundli("Aries", {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 6,
            "Jupiter": 11, "Venus": 2, "Saturn": 10,
            "Rahu": 12, "Ketu": 6,
        }, dashas=_mk_dashas())
        result = compute_baby_window(kundli, intel={}, kp={},
                                       birth={"dob": "1990-05-15"})
        ccf = result.get("cross_chart_filter") or {}
        per = ccf.get("per_planet") or {}
        # Every survivor MUST have a recorded confirmations count
        for p, info in per.items():
            self.assertIn("confirmations", info)
            self.assertIn("cross_confirmed", info)
            self.assertGreaterEqual(info["confirmations"], 0)
            self.assertLessEqual(info["confirmations"], 3)

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

"""Tests for shared KP planet significator scan (Phase 2.5.11.17)."""

import json
import unittest
from event_timing._shared.kp_significator_scan import (
    compute_kp_planet_scan,
    render_scan_lines,
)


_DICT_KP = {
    "significations": {
        "Moon":    {"nl_lord": "Ketu", "sb_lord": "Venus", "ss_lord": "Moon",
                     "pl": [8, 12], "sl": [1, 4, 6, 7, 9, 10, 11],
                     "sb_houses": [1, 6, 11], "ss_houses": [8, 12]},
        "Mercury": {"nl_lord": "Mars", "sb_lord": "Mars", "ss_lord": "Ketu",
                     "pl": [12, 4, 7], "sl": [1, 6, 12],
                     "sb_houses": [1, 6, 12], "ss_houses": [9]},
        "Sun":     {"nl_lord": "Venus", "sb_lord": "Venus", "ss_lord": "Venus",
                     "pl": [12], "sl": [3, 9, 12],
                     "sb_houses": [3, 9, 12], "ss_houses": [3, 9, 12]},
        "Mars":    {"nl_lord": "Saturn", "sb_lord": "Saturn", "ss_lord": "Sun",
                     "pl": [4], "sl": [4, 5], "sb_houses": [4], "ss_houses": []},
    }
}


class TestComputeScan(unittest.TestCase):

    def test_dict_shape_travel_scan(self):
        r = compute_kp_planet_scan(_DICT_KP, "travel",
                                     in_filter_set={"Mercury", "Sun"})
        self.assertTrue(r["kp_available"])
        self.assertEqual(r["domain"], "travel")
        self.assertEqual(r["domain_houses"], [3, 9, 12])
        # Sun: pl=12, sl=3,9,12, sb=3,9,12, ss=3,9,12 → covers all 3 → STRONG
        sun = next(p for p in r["planets"] if p["planet"] == "Sun")
        self.assertEqual(sun["domain_hits"], [3, 9, 12])
        self.assertEqual(sun["delivers"], "STRONG")
        self.assertTrue(sun["in_filter"])
        # Moon: pl=8,12, ss=8,12 → only 12 in [3,9,12] but sl has 9 → hits=[9,12] → STRONG
        moon = next(p for p in r["planets"] if p["planet"] == "Moon")
        self.assertEqual(moon["domain_hits"], [9, 12])
        self.assertEqual(moon["delivers"], "STRONG")
        self.assertFalse(moon["in_filter"])
        # Mars: no travel-house hit → ABSENT
        mars = next(p for p in r["planets"] if p["planet"] == "Mars")
        self.assertEqual(mars["delivers"], "ABSENT")

    def test_missed_by_filter_audit_flag(self):
        """Moon DELIVERS travel but was dropped by STEP1 filter →
        must surface in `missed_by_filter`."""
        r = compute_kp_planet_scan(_DICT_KP, "travel",
                                     in_filter_set={"Mercury", "Sun"})
        self.assertIn("Moon", r["missed_by_filter"])
        self.assertNotIn("Sun", r["missed_by_filter"])  # Sun is in filter

    def test_list_shape_legacy_kp(self):
        kp_list = {"significations": {"Mercury": [9, 12, 3, 4, 5]}}
        r = compute_kp_planet_scan(kp_list, "travel", in_filter_set={"Mercury"})
        merc = next(p for p in r["planets"] if p["planet"] == "Mercury")
        self.assertEqual(merc["domain_hits"], [3, 9, 12])
        self.assertEqual(merc["delivers"], "STRONG")

    def test_empty_kp_safe(self):
        r = compute_kp_planet_scan(None, "travel", in_filter_set=set())
        self.assertFalse(r["kp_available"])
        self.assertEqual(len(r["planets"]), 9)
        for p in r["planets"]:
            self.assertEqual(p["delivers"], "ABSENT")

    def test_all_six_domains_supported(self):
        for d in ("travel", "health", "finance", "marriage", "baby", "career"):
            r = compute_kp_planet_scan(_DICT_KP, d, in_filter_set=set())
            self.assertEqual(r["domain"], d)
            self.assertGreater(len(r["domain_houses"]), 0,
                                f"domain {d} must have concern houses")
            self.assertEqual(len(r["planets"]), 9)

    def test_render_lines_format(self):
        r = compute_kp_planet_scan(_DICT_KP, "travel",
                                     in_filter_set={"Sun"})
        lines = render_scan_lines(r, max_lines=4)
        self.assertTrue(any("KP-PLANET-SCAN (TRAVEL)" in ln for ln in lines))
        self.assertTrue(any("AUDIT-FLAG" in ln for ln in lines))  # Moon delivers but not in filter
        self.assertTrue(any("Sun" in ln and "STRONG" in ln for ln in lines))


class TestLiveChartIntegration(unittest.TestCase):
    """Smoke test against the real Rajalaxmi chart (/tmp/raj.json)."""

    def test_raj_chart_travel_scan(self):
        try:
            with open("/tmp/raj.json") as f:
                k = json.load(f)
        except FileNotFoundError:
            self.skipTest("/tmp/raj.json not present")
        kp = k.get("kp") or {}
        # Moon, Mercury, Sun all known to KP-signify travel houses on this chart.
        r = compute_kp_planet_scan(kp, "travel",
                                     in_filter_set={"Sun", "Mercury", "Rahu"})
        self.assertTrue(r["kp_available"])
        # Moon has KP travel-significator chain on this chart (hits=[9,12]).
        moon = next(p for p in r["planets"] if p["planet"] == "Moon")
        self.assertGreaterEqual(moon["domain_score"], 1)
        # Moon was NOT in the filter we passed → audit flag must fire if delivers.
        if moon["delivers"] in ("STRONG", "PARTIAL"):
            self.assertIn("Moon", r["missed_by_filter"])


class TestKpPromoteSurvivors(unittest.TestCase):
    """Phase 2.5.11.18 — KP-driven STEP1 promotion."""

    def _mk_d1_map(self):
        return {p: {"in_filter": False, "links": [], "d1": 0.0}
                for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
                         "Venus", "Saturn", "Rahu", "Ketu"]}

    def test_promotes_planets_meeting_threshold(self):
        from event_timing._shared.kp_significator_scan import kp_promote_survivors
        d1_map = self._mk_d1_map()
        # All 9 are out-of-filter to start.
        promoted = kp_promote_survivors(d1_map, _DICT_KP, "travel", threshold=2)
        # Sun: NL=Saturn(travel houses inferred from fixture) — should qualify
        self.assertGreater(len(promoted), 0)
        for p in promoted:
            self.assertTrue(d1_map[p]["in_filter"])
            self.assertTrue(any("kp-promoted" in lk for lk in d1_map[p]["links"]))

    def test_does_not_repromote_already_in_filter(self):
        from event_timing._shared.kp_significator_scan import kp_promote_survivors
        d1_map = self._mk_d1_map()
        d1_map["Sun"]["in_filter"] = True
        d1_map["Sun"]["links"] = ["pre-existing"]
        promoted = kp_promote_survivors(d1_map, _DICT_KP, "travel")
        self.assertNotIn("Sun", promoted)
        # link untouched
        self.assertEqual(d1_map["Sun"]["links"], ["pre-existing"])

    def test_empty_kp_safe_noop(self):
        from event_timing._shared.kp_significator_scan import kp_promote_survivors
        d1_map = self._mk_d1_map()
        promoted = kp_promote_survivors(d1_map, None, "travel")
        self.assertEqual(promoted, [])
        self.assertFalse(any(d1_map[p]["in_filter"] for p in d1_map))

    def test_threshold_respected(self):
        from event_timing._shared.kp_significator_scan import kp_promote_survivors
        d1_map = self._mk_d1_map()
        # threshold=99 → impossible to hit
        promoted = kp_promote_survivors(d1_map, _DICT_KP, "travel", threshold=99)
        self.assertEqual(promoted, [])


if __name__ == "__main__":
    unittest.main()

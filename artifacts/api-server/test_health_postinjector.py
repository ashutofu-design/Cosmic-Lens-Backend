"""Unit tests for the Health Engine v1 post-injector pipeline.

Covers:
- inject_health_engine_verdict idempotency
- inject_health_engine_verdict no-op when no cached engine result
- apply_health_postinjectors full chain (vocab strip + verdict + disclaimer)
- thread-local cache isolation (clear_last_health_result)
- killswitch (HEALTH_DISCLAIMER off)
"""
from __future__ import annotations

import json
import os
import unittest

from event_timing.health.health_engine_v1 import (
    compute_health_window,
    get_last_health_result,
    clear_last_health_result,
)
from health_focus_routing import (
    inject_health_engine_verdict,
    apply_health_postinjectors,
)


def _load_fixture():
    raw = open("/tmp/k.json").read()
    k = json.loads(raw)
    if isinstance(k, str):
        k = json.loads(k)
    return k


class TestHealthPostinjector(unittest.TestCase):
    def setUp(self):
        clear_last_health_result()
        self.k = _load_fixture()
        # Run engine to populate the thread-local cache
        compute_health_window(
            self.k, intel={}, kp=self.k.get("kp"),
            birth={"dob": self.k.get("dob")},
        )
        self.cached = get_last_health_result()
        self.assertIsNotNone(self.cached, "engine should populate cache")

    def test_verdict_line_appended(self):
        ans = "Saturn ki position se acidity ka dhyan rakhein."
        out = inject_health_engine_verdict(ans, "meri health?")
        self.assertIn("👉 Final:", out)
        self.assertIn("[engine: health-v1]", out)
        self.assertTrue(out.startswith(ans))

    def test_idempotent(self):
        ans = "Generic health body text."
        once = inject_health_engine_verdict(ans, "?")
        twice = inject_health_engine_verdict(once, "?")
        self.assertEqual(once, twice, "post-injector must be idempotent")

    def test_no_op_when_cache_empty(self):
        clear_last_health_result()
        ans = "Some answer."
        out = inject_health_engine_verdict(ans, "?")
        self.assertEqual(out, ans, "no cache → no injection")

    def test_full_pipeline_includes_verdict_and_disclaimer(self):
        ans = "Aapki health analysis. Yoga karein."
        full = apply_health_postinjectors(ans, "meri health kab improve hogi?")
        self.assertIn("👉 Final:", full)
        self.assertIn("[engine: health-v1]", full)
        self.assertTrue(
            "doctor" in full.lower() or "medical advice nahi" in full,
            "medical disclaimer missing from full pipeline",
        )

    def test_killswitch_disables(self):
        os.environ["HEALTH_DISCLAIMER"] = "0"
        try:
            ans = "Some answer."
            out = inject_health_engine_verdict(ans, "?")
            self.assertEqual(out, ans, "killswitch off → no injection")
        finally:
            os.environ.pop("HEALTH_DISCLAIMER", None)

    def test_clear_last_isolates_threads(self):
        self.assertIsNotNone(get_last_health_result())
        clear_last_health_result()
        self.assertIsNone(get_last_health_result())

    def test_no_stale_leak_across_calls(self):
        """Architect-fix regression: a prior valid result must NOT leak
        when a subsequent call hits an early-return gate (empty kundli,
        missing lagna, data-insufficient, or exception). The wrapper
        clears the cache at entry + re-stores on every exit path."""
        # Seed: valid kundli → real verdict in cache
        self.assertNotEqual(get_last_health_result()["verdict"], "UNKNOWN")
        prior = get_last_health_result()["verdict"]

        # Now call with empty kundli → should yield UNKNOWN, NOT prior verdict
        empty_result = compute_health_window({}, intel={}, kp={}, birth=None)
        self.assertEqual(empty_result["verdict"], "UNKNOWN")
        cached_now = get_last_health_result()
        self.assertEqual(cached_now["verdict"], "UNKNOWN",
                          f"stale leak: cache still says {cached_now['verdict']!r} "
                          f"after gate (prior was {prior!r})")
        # Post-injector must NOT inject for UNKNOWN
        out = inject_health_engine_verdict("Some answer body.", "?")
        self.assertNotIn("👉 Final:", out,
                          "post-injector must no-op on UNKNOWN cache")
        self.assertNotIn("[engine: health-v1]", out)

    def test_engine_exception_clears_cache_to_unknown(self):
        """If the inner pipeline raises, the wrapper must catch and
        produce UNKNOWN, not leave a stale prior value in cache."""
        # Seed: valid result already in cache (from setUp)
        self.assertNotEqual(get_last_health_result()["verdict"], "UNKNOWN")
        # Trigger exception path: pass non-dict (caught by gate, not exception)
        # — but also pass a kundli with planets shape that breaks step1.
        # Easier: use a kundli that survives initial gates but trips inside.
        broken = {"ascendant": "Aries", "planets": "not-a-list",
                  "currentDasha": {"maha": "Sun"}}
        result = compute_health_window(broken, intel={}, kp={}, birth=None)
        # Should be UNKNOWN (either from a gate or from the exception catch)
        self.assertEqual(result["verdict"], "UNKNOWN")
        self.assertEqual(get_last_health_result()["verdict"], "UNKNOWN")

    def test_remedies_compute_dedupes_and_caps(self):
        """`_compute_health_remedies` must dedupe repeated planets, cap
        at 3 planet-remedies, cap at 3 system-practices, normalize bad
        tier values, and tolerate None / malformed inputs."""
        from event_timing.health.health_engine_v1 import (
            _compute_health_remedies,
        )
        # None inputs → empty lists, but disclaimer + tier_note present
        out = _compute_health_remedies(None, None, None)
        self.assertEqual(out["planet_remedies"], [])
        self.assertEqual(out["system_practices"], [])
        self.assertIn("doctor", out["universal_disclaimer"].lower())
        self.assertEqual(out["tier"], "consult")  # bad tier → 'consult'

        # Dedupe + cap: Mars repeated 4× + 4 valid planets → only 3 unique
        ranked = [
            {"name": "Mars", "score": 14.0},
            {"name": "Mars", "score": 13.0},  # dupe
            {"name": None,   "score": 12.0},  # malformed
            "garbage",                          # not a dict
            {"name": "Saturn", "score": 11.0},
            {"name": "Mars", "score": 10.0},  # dupe again
            {"name": "Sun",  "score": 9.0},
            {"name": "Moon", "score": 8.0},   # 4th unique → must NOT appear
        ]
        out = _compute_health_remedies(ranked,
                                         ["blood", "blood", "muscles",
                                          "unknown_tag", "inflammation",
                                          "liver"],  # 5 unique, cap 3
                                         "urgent_consult")
        names = [p["planet"] for p in out["planet_remedies"]]
        self.assertEqual(names, ["Mars", "Saturn", "Sun"])
        self.assertEqual(len(out["planet_remedies"]), 3)
        sysnames = [s["system"] for s in out["system_practices"]]
        self.assertEqual(sysnames, ["blood", "muscles", "inflammation"])
        self.assertEqual(out["tier"], "urgent_consult")
        self.assertIn("First a qualified doctor", out["tier_note"])

    def test_remedies_locked_facts_emission(self):
        """End-to-end: after `compute_health_window` populates the cache,
        `build_locked_facts` must emit a `▸ HEALTH REMEDIES` block AFTER
        the `⚐ HARD RULE` line, preserve the universal disclaimer
        verbatim (including the gemstone-trial caveat), and never raise."""
        from reply_cosmo.engine_locked_to_llm.locked_facts import (
            build_locked_facts,
        )
        # Cache already populated by setUp via compute_health_window
        text = build_locked_facts(self.k,
                                    birth={"dob": self.k.get("dob")}) or ""
        self.assertIn("▸ HEALTH REMEDIES", text,
                        "HEALTH REMEDIES block missing from locked_facts")
        # Ordering: HEALTH REMEDIES must come AFTER the HARD RULE line so
        # Rule M (anti-hallucination remedy quoting) sees it as a
        # downstream REMEDIES section, not a timing-window override.
        idx_hard = text.find("⚐ HARD RULE")
        idx_rem  = text.find("▸ HEALTH REMEDIES")
        self.assertGreater(idx_rem, idx_hard,
                              "HEALTH REMEDIES must appear AFTER HARD RULE")
        # Verbatim disclaimer + gemstone-trial caveat must survive
        self.assertIn("Remedies SUPPLEMENT action, never substitute it.",
                        text)
        self.assertIn("Gemstones (paid) require a 3-day trial first.", text)
        # Tier note label must be present
        self.assertIn("TIER NOTE", text)

    def test_remedies_block_present(self):
        """Engine output must include `remedies` with planet_remedies +
        system_practices + universal_disclaimer + tier_note."""
        rem = self.cached.get("remedies")
        self.assertIsInstance(rem, dict, "remedies block missing")
        self.assertIn("planet_remedies", rem)
        self.assertIn("system_practices", rem)
        self.assertIn("universal_disclaimer", rem)
        self.assertIn("tier_note", rem)
        # At least one planet remedy when engine produced ranked planets
        if self.cached.get("top_health_planets"):
            self.assertTrue(len(rem["planet_remedies"]) >= 1,
                              "no planet remedies for ranked planets")
        # Each planet remedy has all required fields
        for pr in rem["planet_remedies"]:
            for k in ("planet", "day", "mantra", "count", "free",
                      "paid", "donation", "for_systems"):
                self.assertIn(k, pr,
                                f"planet remedy missing field {k}: {pr}")
        # Disclaimer mentions doctor + supplement
        disc = rem["universal_disclaimer"].lower()
        self.assertIn("doctor", disc)
        self.assertIn("supplement", disc)

    def test_duplicate_final_reconciled(self):
        """If the LLM already wrote a '👉 Final: ...' line, the
        post-injector must strip it before appending the engine line so
        we don't end up with two competing finals."""
        ans = ("Saturn ka prabhav active hai.\n\n"
               "👉 Final: Aapka swasthya theek rahega — yoga karein.")
        out = inject_health_engine_verdict(ans, "?")
        # Engine line present
        self.assertIn("[engine: health-v1]", out)
        # Only ONE "👉 Final:" in output
        self.assertEqual(out.count("👉 Final:"), 1,
                          f"duplicate final lines:\n{out}")
        # The LLM-written final must be gone
        self.assertNotIn("Aapka swasthya theek rahega", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)

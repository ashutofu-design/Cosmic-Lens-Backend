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

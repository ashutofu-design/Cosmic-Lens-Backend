"""Love Reality premium polish — fingerprint + cache depth gate."""
import unittest

from vedic.love_reality.premium_polish import (
    _love_polish_cache_depth_ok,
    _love_polish_fingerprint,
)


class TestLovePolishCache(unittest.TestCase):
    def test_fingerprint_changes_with_score(self):
        b1 = {
            "p1": {"nakshatra": "A", "moonSign": "Leo"},
            "p2": {"nakshatra": "B", "moonSign": "Virgo"},
            "love_compatibility": {"score": 50},
            "breakup_chances": {"breakup_score": 40},
            "loyalty_check": {"loyalty_score": 45},
            "will_return": {"score": 30},
            "future_outcome": {"future_score": 55},
            "couple_signals": {"combined_affliction": 20},
        }
        b2 = dict(b1)
        b2["love_compatibility"] = {"score": 61}
        self.assertNotEqual(
            _love_polish_fingerprint(b1, "en", "gpt-4o"),
            _love_polish_fingerprint(b2, "en", "gpt-4o"),
        )

    def test_depth_ok_requires_chapter_bodies(self):
        shallow = {"chapters": [{"chapter_body": "x" * 50}] * 6}
        self.assertFalse(_love_polish_cache_depth_ok(shallow))
        deep = {
            "chapters": [
                {"chapter_body": "a" * 200},
                {"chapter_body": "b" * 200},
                {"chapter_body": "c" * 200},
                {"chapter_body": "d" * 200},
            ]
        }
        self.assertTrue(_love_polish_cache_depth_ok(deep))


if __name__ == "__main__":
    unittest.main()

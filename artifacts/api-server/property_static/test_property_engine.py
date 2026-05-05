"""Unit tests for property_static engine — runs against P40 fixture
plus 2 synthetic charts (strong-yog and weak-yog) to verify dim logic."""
from __future__ import annotations
import json
import os
import sys
import unittest

# Allow `python test_property_engine.py` from inside the folder
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from property_static.property_engine import (  # noqa: E402
    compute_property_facts,
)
from property_static.property_routing import (  # noqa: E402
    is_property_question,
    is_timing_property_question,
)
from property_static.property_replies import (  # noqa: E402
    _build_signal_pack,
    _force_final_verdict,
    _sanitize_property_reply,
    _build_final_verdict_from_dims,
)


P40_FIXTURE = "/tmp/k.json"


def _load_p40():
    if not os.path.exists(P40_FIXTURE):
        raise unittest.SkipTest(f"P40 fixture {P40_FIXTURE} missing")
    with open(P40_FIXTURE) as f:
        return json.load(f)


def _synthetic_chart(asc: str, planet_overrides: dict) -> dict:
    """Build a minimal kundli dict for engine testing.
    planet_overrides: {Name: {house, sign}}"""
    base = {
        "Sun":     {"house": 1, "sign": asc},
        "Moon":    {"house": 1, "sign": asc},
        "Mars":    {"house": 1, "sign": asc},
        "Mercury": {"house": 1, "sign": asc},
        "Jupiter": {"house": 1, "sign": asc},
        "Venus":   {"house": 1, "sign": asc},
        "Saturn":  {"house": 1, "sign": asc},
        "Rahu":    {"house": 1, "sign": asc},
        "Ketu":    {"house": 7, "sign": ""},
    }
    base.update(planet_overrides)
    planets = []
    for name, data in base.items():
        planets.append({"name": name, **data, "retrograde": False})
    return {"ascendant": asc, "planets": planets}


# ──────────────────────────────────────────────────────────────────────
class TestRouting(unittest.TestCase):

    def test_clear_property_questions(self):
        for q in [
            "kya mera property yog hai chart me?",
            "ghar lena chahiye ya nahi?",
            "property capacity kaisi hai meri?",
            "mujhe plot lena chahiye?",
            "real estate me invest karu kya?",
            "apna ghar le sakta hu kya?",
            "ancestral property me hissa milega?",
            "flat purchase karu?",
            "khud ka ghar ho payega?",
            "first home buying me kya dekhna chahiye chart se?",
        ]:
            self.assertTrue(is_property_question(q),
                            f"Should route property: {q!r}")

    def test_timing_questions_blocked(self):
        for q in [
            "ghar kab milega?",
            "property kab kharidu?",
            "registry ka muhurat kya hai?",
            "when will i buy my home?",
            "shift kab karu?",
            "griha pravesh kab?",
            # Architect-flagged FNs (P1.0 hardening)
            "when can i buy property?",
            "when can i buy a home?",
            "ghar lene ka sahi samay kya hai?",
            "property lene ka best time kya hai?",
            "ghar kab tak milega?",
            "best time to buy property?",
            "ghar kis waqt lena chahiye?",
            "property buy karne ka muhurat?",
        ]:
            self.assertTrue(is_timing_property_question(q),
                            f"Should detect timing: {q!r}")
            # Property routing should refuse (return False so the route
            # falls to handle_property_question's timing branch)
            self.assertFalse(is_property_question(q),
                             f"is_property_question should be False for "
                             f"timing Q: {q!r}")

    def test_non_property_timing_does_not_falsely_match(self):
        """Architect-flagged: timing regex must require property context."""
        from property_static.property_routing import (
            is_timing_property_question)
        for q in [
            "meri shaadi kab hogi?",
            "career me promotion kab milega?",
            "naukri kab lagegi?",
            "best time for new job?",
        ]:
            self.assertFalse(is_timing_property_question(q),
                             f"Non-property timing FP: {q!r}")

    def test_non_property_blocked(self):
        for q in [
            "meri health kaisi hai?",
            "shaadi kab hogi?",
            "career me kya hoga?",
            "stock market me invest karu?",
            "gaadi kab kharidu?",
            "gold lena chahiye?",
        ]:
            self.assertFalse(is_property_question(q),
                             f"Should NOT route property: {q!r}")


# ──────────────────────────────────────────────────────────────────────
class TestEngineP40(unittest.TestCase):
    """P40 = Rajalaxmi 26/11/1992 07:58 AM Bhubaneswar.
    Lagna = Sagittarius (idx 8). Reference computation:
      - 4H = Pisces (lord Jupiter)
      - 2H = Capricorn (lord Saturn)
      - 11H = Libra (lord Venus)
      - Jupiter in 10H Virgo (debilitated → -1 capacity)
      - Saturn in 2H Capricorn (own → +1)
      - Mars in 8H Cancer (debilitated → -1 yog)
      - Venus in 1H Sagittarius (neutral)
      - Rahu in 12H, Ketu in 6H — neither in 4H → no 4H affliction
    """

    def setUp(self):
        self.kundli = _load_p40()
        self.facts = compute_property_facts(self.kundli)
        self.dims = self.facts["dimensions"]

    def test_returns_all_4_dims(self):
        for dim in ("yog", "capacity", "risk", "type_fit"):
            self.assertIn(dim, self.dims,
                          f"Missing dim: {dim}")

    def test_yog_has_verdict(self):
        v = self.dims["yog"].get("verdict")
        self.assertIn(v, ("STRONG", "MODERATE", "WEAK", "UNKNOWN"))

    def test_capacity_has_verdict(self):
        v = self.dims["capacity"].get("verdict")
        self.assertIn(v, ("STRONG", "MODERATE", "WEAK", "UNKNOWN"))

    def test_risk_has_verdict(self):
        v = self.dims["risk"].get("verdict")
        self.assertIn(v, ("CLEAN", "CAUTION", "HIGH_RISK", "UNKNOWN"))

    def test_type_fit_has_best_and_alt(self):
        tf = self.dims["type_fit"]
        self.assertIn("best", tf)
        self.assertIn("alt", tf)
        self.assertIn(tf["best"], ("plot", "new_home", "luxury",
                                    "rental", "ancestral"))

    def test_signal_pack_has_no_planet_names(self):
        pack = _build_signal_pack(self.facts)
        pack_json = json.dumps(pack, ensure_ascii=False).lower()
        for forbidden in ("mars", "mangal", "jupiter", "guru",
                          "saturn", "shani", "venus", "shukra",
                          "rahu", "ketu", "mercury", "budh"):
            self.assertNotIn(forbidden, pack_json,
                              f"Signal pack leaked planet name: {forbidden}")

    def test_signal_pack_has_no_house_numbers(self):
        pack = _build_signal_pack(self.facts)
        pack_json = json.dumps(pack, ensure_ascii=False).lower()
        for forbidden in ("4th house", "11th house", "2nd house",
                          "8th house", "lagna", "kendra", "dusthana",
                          "trikona"):
            self.assertNotIn(forbidden, pack_json,
                              f"Signal pack leaked house ref: {forbidden}")

    def test_signal_pack_has_no_sign_names(self):
        pack = _build_signal_pack(self.facts)
        pack_json = json.dumps(pack, ensure_ascii=False).lower()
        for forbidden in ("aries", "taurus", "gemini", "cancer",
                          "leo", "virgo", "libra", "scorpio",
                          "sagittarius", "capricorn", "aquarius",
                          "pisces"):
            self.assertNotIn(forbidden, pack_json,
                              f"Signal pack leaked sign name: {forbidden}")

    def test_signal_pack_has_engine_verdict(self):
        pack = _build_signal_pack(self.facts)
        ev = pack.get("engine_verdict", "")
        self.assertTrue(ev.startswith("👉 Final:"),
                        f"engine_verdict missing/malformed: {ev!r}")


# ──────────────────────────────────────────────────────────────────────
class TestSyntheticCharts(unittest.TestCase):

    def test_strong_yog_chart(self):
        """4H lord exalted in own house, Jupiter exalted, Saturn own."""
        # Lagna Aries → 4H = Cancer → 4L = Moon
        # Place Moon in Taurus (exalted) at house 4
        k = _synthetic_chart("Aries", {
            "Moon":    {"house": 4,  "sign": "Taurus"},      # 4L exalted in 4H
            "Jupiter": {"house": 5,  "sign": "Cancer"},      # Jup exalted
            "Saturn":  {"house": 10, "sign": "Capricorn"},   # Sat own + kendra
            "Venus":   {"house": 7,  "sign": "Libra"},       # Ven own
            "Mars":    {"house": 10, "sign": "Capricorn"},   # Mars exalted
            "Mercury": {"house": 6,  "sign": "Virgo"},       # Mer own
            "Sun":     {"house": 1,  "sign": "Aries"},       # Sun exalted
            "Rahu":    {"house": 12, "sign": "Pisces"},
            "Ketu":    {"house": 6,  "sign": "Virgo"},
        })
        facts = compute_property_facts(k)
        self.assertEqual(facts["dimensions"]["yog"]["verdict"], "STRONG")
        self.assertEqual(facts["dimensions"]["capacity"]["verdict"], "STRONG")

    def test_weak_yog_chart(self):
        """4L debilitated in dusthana, Saturn debilitated."""
        # Lagna Aries → 4L = Moon. Place Moon in Scorpio (debil) at 8H.
        k = _synthetic_chart("Aries", {
            "Moon":    {"house": 8,  "sign": "Scorpio"},     # 4L debil + dusthana
            "Saturn":  {"house": 1,  "sign": "Aries"},       # Sat debil
            "Jupiter": {"house": 10, "sign": "Capricorn"},   # Jup debil
            "Mars":    {"house": 4,  "sign": "Cancer"},      # Mars debil in 4H
            "Rahu":    {"house": 4,  "sign": "Cancer"},      # Rahu in 4H = risk
            "Ketu":    {"house": 10, "sign": "Capricorn"},
        })
        facts = compute_property_facts(k)
        self.assertEqual(facts["dimensions"]["yog"]["verdict"], "WEAK")
        # Risk should be CAUTION or HIGH_RISK (Rahu in 4H + Mars-Sat affliction)
        self.assertIn(facts["dimensions"]["risk"]["verdict"],
                      ("CAUTION", "HIGH_RISK"))


# ──────────────────────────────────────────────────────────────────────
class TestSanitizer(unittest.TestCase):

    def test_strips_planet_names(self):
        text = "Aapke chart me Mars 4th house me hai aur Jupiter strong hai."
        out = _sanitize_property_reply(text)
        for forbidden in ("Mars", "Jupiter", "mars", "jupiter"):
            self.assertNotIn(forbidden, out)

    def test_strips_house_numbers(self):
        text = "4th house me Mars hai, 11th bhav me Saturn baitha hai."
        out = _sanitize_property_reply(text)
        self.assertNotIn("4th house", out.lower())
        self.assertNotIn("11th bhav", out.lower())

    def test_strips_timing_words(self):
        text = "Coming months me property aayegi, agle saal kharid lo."
        out = _sanitize_property_reply(text)
        self.assertNotIn("coming months", out.lower())
        self.assertNotIn("agle saal", out.lower())

    def test_strips_jargon(self):
        text = "Dhana yog active hai aur Mars dasha chal rahi hai."
        out = _sanitize_property_reply(text)
        self.assertNotIn("dhana yog", out.lower())
        self.assertNotIn("dasha", out.lower())

    def test_preserves_clean_text(self):
        text = ("Aapki property capacity strong hai aur documentation "
                "verification zaroori hai.")
        out = _sanitize_property_reply(text)
        self.assertIn("capacity", out.lower())
        self.assertIn("documentation", out.lower())


# ──────────────────────────────────────────────────────────────────────
class TestForceFinal(unittest.TestCase):

    def test_appends_when_missing(self):
        body = "Aapki property capacity strong hai."
        pack = {"engine_verdict":
                "👉 Final: Property yog moderate hai aur capacity strong hai. "
                "Documentation aur legal check ke baad hi aage badho."}
        out = _force_final_verdict(body, pack)
        # Exactly ONE Final line
        self.assertEqual(out.count("👉 Final:"), 1)
        self.assertTrue(out.endswith(pack["engine_verdict"]))

    def test_strips_existing_and_replaces(self):
        body = ("Aapki capacity strong hai.\n\n"
                "👉 Final: kuch alag verdict tha LLM ka.\n\n"
                "Aur kuch text.")
        pack = {"engine_verdict":
                "👉 Final: Property yog strong hai aur capacity strong hai. "
                "Structured planning ke saath aage badho."}
        out = _force_final_verdict(body, pack)
        # Old final stripped
        self.assertNotIn("kuch alag verdict tha", out)
        # Exactly ONE final at EOF
        self.assertEqual(out.count("👉 Final:"), 1)
        self.assertTrue(out.endswith(pack["engine_verdict"]))


# ──────────────────────────────────────────────────────────────────────
class TestVerdictBuilder(unittest.TestCase):

    def test_strong_chart_verdict(self):
        v = _build_final_verdict_from_dims(
            {"verdict": "STRONG"}, {"verdict": "STRONG"}, {"verdict": "CLEAN"})
        self.assertIn("yog strong", v.lower())
        self.assertIn("capacity strong", v.lower())
        self.assertIn("structured planning", v.lower())

    def test_weak_with_high_risk(self):
        v = _build_final_verdict_from_dims(
            {"verdict": "WEAK"}, {"verdict": "MODERATE"},
            {"verdict": "HIGH_RISK"})
        self.assertIn("yog weak", v.lower())
        self.assertIn("legal verification", v.lower())

    def test_unknown_failsafe(self):
        v = _build_final_verdict_from_dims(
            {"verdict": "UNKNOWN"}, {"verdict": "UNKNOWN"},
            {"verdict": "UNKNOWN"})
        self.assertIn("signals incomplete", v.lower())


# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    unittest.main(verbosity=2)

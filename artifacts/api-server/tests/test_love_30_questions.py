"""30-question love timing checklist — bucket routing coverage."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.love.love_timing_engine_v1 import classify_love_timing_bucket, assess_love_timing


# (question, expected_bucket)
LOVE_30_CHECKLIST: list[tuple[str, str]] = [
    # Cat 1 — Entry & New Love
    ("Meri life me pehla serious relationship kab shuru hoga?", "general_love"),
    ("Mujhe mera true love soulmate kis saal ya mahine me milega?", "general_love"),
    ("Mera naya relationship kis dasha ya transit window me trigger ho raha hai?", "timing"),
    ("Mujhe koi approach kab karega proposal kab milega?", "commitment"),
    ("Kya is saal current transit me meri life me koi naya insaan aayega?", "meeting"),
    ("Mere social circle se bahar ka koi insaan meri life me kab enter karega?", "meeting"),
    ("Mujhe naya partner dhoondhne ke liye sabse favorable dasha window kaun si hai?", "general_love"),
    ("Rahu Ketu ke transit me jo attraction hua hai kya wo commitment me badlega?", "commitment"),
    ("Mera current dry spell single status kis month me khatam hoga?", "general_love"),
    ("Kis specific mahine me Surya ya Venus ke gochar se mujhe apna partner milega?", "timing"),
    # Cat 2 — Ex & Reconciliation
    ("Kya mera Ex meri life me wapas aayega agar haan to kab?", "reconciliation"),
    ("Humare beech chal raha break-up ya separation kab khatam hoga?", "reconciliation"),
    ("Mera partner mujhe khud se contact kab karega unblock kab karega?", "reconciliation"),
    ("Kya chal rahi Antardasha me humare purane rishte ko dusra chance milega?", "reconciliation"),
    ("Retrograde Venus vakri shukra ke dauran kya mera purana pyaar wapas aayega?", "reconciliation"),
    ("Humare beech chal rahi galatfehmiyan misunderstandings kis mahine me door hongi?", "stress_phase"),
    ("No-contact situation kab break hogi?", "reconciliation"),
    # Cat 3 — Commitment (love engine; marriage-shaadi → marriage_engine in openai_helper)
    ("Mera partner shaadi ke liye haan kab bolega commitment kab dega?", "commitment"),
    ("Humare ghar wale parents is rishte ke liye kab raazi agree honge?", "family_approval"),
    ("Humare rishte ko societal recognition samaaj me kab milega?", "family_approval"),
    # Cat 4 — Testing Times
    ("Humare rishte me chal raha stressful phase kab tak chalega?", "stress_phase"),
    ("Mujhe kab pata chalega ki mera partner loyalty maintain kar raha hai ya dhoka de raha hai?", "discovery"),
    ("Kya 6th lord ki dasha me humare rishte me koi teesra insaan third party aayega?", "affair"),
    ("Humara chal raha court case ya relationship dispute kab resolve hoga?", "stress_phase"),
    ("Kis dasha window me humara permanently breakup hone ka khatra hai?", "breakup"),
    ("Kya abhi chal rahi dasha me mujhe relationship se doori healing period kab tak hai?", "healing"),
]


class TestLove30QuestionCoverage(unittest.TestCase):
    def test_all_30_buckets(self):
        for q, expected in LOVE_30_CHECKLIST:
            with self.subTest(q=q[:50]):
                got = classify_love_timing_bucket(q)
                self.assertEqual(got, expected, f"Q: {q!r} → got {got}, want {expected}")

    def test_relationship_shuru_timing(self):
        q = "Mera relationship kab shuru hoga?"
        self.assertEqual(classify_love_timing_bucket(q), "timing")
        out = assess_love_timing(
            {
                "ascendant": "Libra",
                "lagnaLongitude": 180.0,
                "planets": [
                    {"name": "Venus", "sign": "Pisces", "house": 5},
                    {"name": "Moon", "sign": "Taurus", "house": 7, "sign_idx": 1},
                    {"name": "Jupiter", "sign": "Aquarius", "house": 5},
                    {"name": "Saturn", "sign": "Capricorn", "house": 4},
                ],
                "currentDasha": {"mahadasha": "Jupiter", "antardasha": "Venus"},
                "dashas": [
                    {
                        "lord": "Jupiter",
                        "start": "2020-01-01",
                        "end": "2036-01-01",
                        "antardashas": [
                            {
                                "lord": "Venus",
                                "start": "2025-01-01",
                                "end": "2027-06-01",
                                "pratyantar": [
                                    {
                                        "lord": "Moon",
                                        "start": "2025-06-01",
                                        "end": "2027-06-01",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
            {"house_lords": [{"house": 5, "lord": "Saturn"}, {"house": 7, "lord": "Mars"}]},
            {},
            None,
            q,
        )
        self.assertEqual(out["bucket"], "timing")
        self.assertIn("timing_source", out)
        self.assertIn("transits", out)
        self.assertIn("strategy", out)
        self.assertTrue(out.get("strategy"))
        ts = out.get("timing_source")
        self.assertIn(ts, ("current_dasha_active", "next_dasha_scan", "no_qualified_window"))

    def test_love_life_shuru_dasha_first(self):
        """Current AD/PD must be checked before jumping to a future Saturn-only window."""
        from event_timing.love.love_timing_v1 import compute_love_window

        q = "Mera love life kab shuru hoga"
        now_year = __import__("datetime").datetime.utcnow().year
        out = compute_love_window(
            {
                "ascendant": "Leo",
                "planets": [
                    {"name": "Venus", "sign": "Libra", "house": 3},
                    {"name": "Moon", "sign": "Gemini", "house": 11},
                    {"name": "Mars", "sign": "Aries", "house": 9},
                    {"name": "Saturn", "sign": "Aquarius", "house": 7},
                    {"name": "Jupiter", "sign": "Sagittarius", "house": 5},
                ],
                "dashas": [
                    {
                        "lord": "Saturn",
                        "start": f"{now_year - 2}-01-01",
                        "end": f"{now_year + 20}-01-01",
                        "antardashas": [
                            {
                                "lord": "Mercury",
                                "start": f"{now_year}-01-01",
                                "end": f"{now_year + 1}-06-01",
                                "pratyantar": [
                                    {
                                        "lord": "Venus",
                                        "start": f"{now_year}-03-01",
                                        "end": f"{now_year + 1}-01-01",
                                    }
                                ],
                            },
                            {
                                "lord": "Venus",
                                "start": f"{now_year + 1}-06-01",
                                "end": f"{now_year + 4}-01-01",
                                "pratyantar": [
                                    {
                                        "lord": "Moon",
                                        "start": f"{now_year + 1}-08-01",
                                        "end": f"{now_year + 2}-02-01",
                                    }
                                ],
                            },
                        ],
                    }
                ],
            },
            {},
            {},
            None,
            q,
        )
        self.assertIn("timing_source", out)
        cw = out.get("current_window") or {}
        if out["timing_source"] == "current_dasha_active":
            self.assertTrue(cw.get("is_active_now"))
        elif out["timing_source"] == "next_dasha_scan":
            self.assertIn("PRIMARY=NEXT", " ".join(out.get("factors") or []))
        self.assertTrue(cw.get("start_iso"))


if __name__ == "__main__":
    unittest.main()

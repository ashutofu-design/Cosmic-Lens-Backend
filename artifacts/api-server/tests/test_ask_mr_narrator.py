import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_mr.classifier import classify_mr_archetype
from ask_mr.narrator import build_mr_engine_narrator_system_prompt
from ask_mr import run_mr_static_engine


SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Saturn", "sign": "Virgo", "house": 10},
        {"name": "Mars", "sign": "Cancer", "house": 8},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Mercury", "sign": "Aries", "house": 5},
        {"name": "Jupiter", "sign": "Pisces", "house": 4},
        {"name": "Rahu", "sign": "Aquarius", "house": 3},
        {"name": "Ketu", "sign": "Leo", "house": 9},
        {"name": "Sun", "sign": "Capricorn", "house": 2},
    ],
    "divisionalCharts": {
        "D9": {
            "ascendant": "Libra",
            "planets": [
                {"name": "Moon", "sign": "Capricorn", "house": 4},
                {"name": "Venus", "sign": "Aquarius", "house": 5},
                {"name": "Mars", "sign": "Aries", "house": 7},
            ],
        }
    },
}


class MrNarratorTests(unittest.TestCase):
    def test_loyalty_narrator_uses_master_rules(self):
        from ask_mr.relationship_narrator import RELATIONSHIP_NARRATOR_RULES, build_relationship_narrator_system_prompt

        eng = run_mr_static_engine(SAMPLE_KUNDLI, "kya mera partner loyal hai")
        prompt = build_relationship_narrator_system_prompt(
            engine_result=eng,
            question="kya mera partner loyal hai",
            reply_lang="hn",
        )
        self.assertIn("Cosmic Lens Relationship Narrator", prompt)
        self.assertIn(RELATIONSHIP_NARRATOR_RULES.splitlines()[0], prompt)
        self.assertIn("ENGINE_JSON:", prompt)
        self.assertIn("Never calculate astrology yourself", prompt)

    def test_love_vs_arranged_uses_llm_not_template(self):
        eng = run_mr_static_engine(SAMPLE_KUNDLI, "love marriage ya arrange?", wants_explain=False)
        self.assertFalse(eng.skip_llm)

    def test_loyalty_commitment_routes_to_loyalty_trust(self):
        self.assertEqual(
            classify_mr_archetype("Marriage me loyalty aur commitment level kaise rahega"),
            "loyalty_trust",
        )
        self.assertEqual(
            classify_mr_archetype("meraove marriage he ya arrange"),
            "love_vs_arranged",
        )
        self.assertEqual(
            classify_mr_archetype("mera marriage hogi ya arranged?"),
            "love_vs_arranged",
        )

    def test_partner_nature_payload_maps_three_paragraphs(self):
        from ask_mr.engines.partner_nature import partner_nature_narrator_payload, run_partner_nature

        eng = run_partner_nature(SAMPLE_KUNDLI, "mera partner ka nature?", birth=None)
        payload = partner_nature_narrator_payload(eng)
        self.assertIn("PARA 1", payload)
        self.assertIn("PARA 2", payload)
        self.assertIn("PARA 3", payload)
        self.assertIn("POSITIVE EVIDENCE", payload)
        self.assertIn("NEGATIVE / AFFLICTION EVIDENCE", payload)
        self.assertIn("CHART CONTEXT / NEUTRAL", payload)

    def test_partner_nature_attachment_question_has_pos_neg_split(self):
        from ask_mr.engine import mr_engine_slice_meta
        from ask_mr.engines.partner_nature import partner_nature_narrator_payload, run_partner_nature

        # Sag asc → Gemini 7H; Mercury lord in 12 Scorpio; Moon in 7; Venus Leo 9
        kundli = {
            "ascendant": "Sagittarius",
            "planets": [
                {"name": "Moon", "sign": "Gemini", "house": 7},
                {"name": "Mercury", "sign": "Scorpio", "house": 12},
                {"name": "Venus", "sign": "Leo", "house": 9},
                {"name": "Mars", "sign": "Cancer", "house": 8},
                {"name": "Jupiter", "sign": "Pisces", "house": 4},
                {"name": "Saturn", "sign": "Virgo", "house": 10},
                {"name": "Rahu", "sign": "Aquarius", "house": 3},
                {"name": "Ketu", "sign": "Leo", "house": 9},
                {"name": "Sun", "sign": "Capricorn", "house": 2},
            ],
        }
        q = "Mera aur mere partner ka emotional attachment kaisa rahega"
        eng = run_partner_nature(kundli, q, birth=None)
        meta = mr_engine_slice_meta(eng)
        self.assertGreater(len(meta["evidence_positive"]), 0)
        self.assertGreater(len(meta["evidence_negative"]), 0)
        payload = partner_nature_narrator_payload(eng)
        self.assertIn("BALANCE:", payload)
        self.assertIn("Partnership attachment positive", payload)
        self.assertIn("Partnership attachment affliction", payload)

    def test_partner_nature_prompt_requires_three_paragraphs(self):
        from ask_mr.engines.partner_nature import partner_nature_narrator_payload, run_partner_nature
        from ask_mr.relationship_narrator import build_relationship_narrator_system_prompt

        eng = run_partner_nature(SAMPLE_KUNDLI, "partner nature?", birth=None)
        prompt = build_relationship_narrator_system_prompt(
            engine_result=eng,
            chart_text=partner_nature_narrator_payload(eng),
            question="partner nature?",
            reply_lang="hn",
        )
        self.assertIn("Cosmic Lens Relationship Narrator", prompt)
        self.assertIn("partner nature", prompt.lower())

    def test_attachment_payload_uses_four_sentences_not_three_paras(self):
        from ask_mr.engines.partner_nature import partner_nature_narrator_payload, run_partner_nature

        eng = run_partner_nature(
            SAMPLE_KUNDLI,
            "Mera aur mere partner ka emotional attachment kaisa rahega",
            birth=None,
        )
        payload = partner_nature_narrator_payload(eng)
        self.assertIn("exactly 4 complete sentences", payload)
        self.assertNotIn("PARA 3 — presence in love", payload)

    def test_attachment_narrator_prompt_unified_cosmo_voice(self):
        from ask_mr.relationship_narrator import build_relationship_narrator_system_prompt

        prompt = build_relationship_narrator_system_prompt(
            chart_text="VERDICT: mixed attachment",
            question="Mera aur mere partner ka emotional attachment kaisa rahega",
            reply_lang="hn",
            engine_result=None,
        )
        self.assertIn("Cosmic Lens Relationship Narrator", prompt)
        self.assertIn("emotional attachment", prompt.lower())

    def test_attachment_enforce_never_ends_mid_phrase(self):
        from openai_helper import _enforce_partnership_attachment_answer

        chopped = (
            "Tum dono ka emotional attachment mixed hai. Partner social aur expressive hai. "
            "7th lord private tone deta hai. Kabhi distance phases aa sakte hain. "
            "Venus ki wajah se partner warm aur expressive love deta hai."
        )
        out = _enforce_partnership_attachment_answer(chopped)
        self.assertTrue(out.endswith(".") or out.endswith("।"))
        self.assertNotRegex(out, r"\baur\.\s*$")


if __name__ == "__main__":
    unittest.main()

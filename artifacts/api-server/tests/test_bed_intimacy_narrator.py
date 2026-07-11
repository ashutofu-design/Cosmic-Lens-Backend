"""Bed intimacy narrator — intent-anchored template tests."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_intent_fidelity import infer_bed_intimacy_angle
from ask_mr.bed_intimacy_templates import detect_bed_intimacy_answer_focus, get_opening
from ask_mr.bed_intimacy_narrator import (
    engine_result_to_bed_intimacy_json,
    render_bed_intimacy_template_answer,
    bed_intimacy_engine_narrator_payload,
    validate_bed_intimacy_narrator_output,
)
from ask_mr.v2.adapter import v2_to_engine_result
from ask_mr.v2.engines.bed_intimacy import run_bed_intimacy_v2

SAMPLE_KUNDLI = {
    "ascendant": "Scorpio",
    "planets": [
        {"name": "Mars", "sign": "Aries", "house": 7},
        {"name": "Rahu", "sign": "Gemini", "house": 7},
        {"name": "Moon", "sign": "Capricorn", "house": 8},
        {"name": "Venus", "sign": "Taurus", "house": 12},
        {"name": "Saturn", "sign": "Aquarius", "house": 5},
    ],
    "dasha": {"mahadasha": "Mars", "antardasha": "Rahu"},
}

GOLDEN_QUESTIONS = [
    ("Private life aur conjugal compatibility kaisi rahegi?", "conjugal_compat"),
    ("Bedroom intimacy kaisi rahegi?", "bedroom_compat"),
    ("Sexual intimacy comfortable rahegi kya?", "sexual_intimacy"),
    ("Suhag raat ke baad intimacy normal rahegi?", "suhag_raat"),
    ("Physical compatibility bedroom me kaisi hai?", "physical_compat"),
    ("Hamari bedroom compatibility kaisi hai?", "bedroom_compat"),
    ("Sex life marriage me comfortable hogi?", "sexual_intimacy"),
    ("Conjugal life harmonious rahegi kya?", "conjugal_compat"),
    ("Private life me comfort milega kya?", "conjugal_compat"),
    ("Intimacy emotionally safe rahegi?", "emotional_safety"),
    ("Bed intimacy strained dikhti hai kya?", "bedroom_compat"),
    ("Physical intimacy level kya hai?", "sexual_intimacy"),
    ("Desire mismatch hoga kya bedroom me?", "intimacy_drive"),
    ("Sexual comfort partner ke saath possible hai?", "sexual_intimacy"),
    ("Suhag raat experience kaisa rahega?", "suhag_raat"),
    ("Bedroom me passion maintain rahega?", "intimacy_drive"),
    ("Trust build hone ke baad intimacy grow karegi?", "emotional_safety"),
    ("Conjugal compatibility chart me kya dikhti hai?", "conjugal_compat"),
    ("Private intimacy strained phase aa sakta hai?", "conjugal_compat"),
    ("Overall physical intimacy pattern kaisa hai?", "sexual_intimacy"),
]

INTIM_Q = "Private life aur conjugal compatibility kaisi rahegi?"


class BedIntimacyNarratorTests(unittest.TestCase):
    def setUp(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        self.out = run_bed_intimacy_v2(SAMPLE_KUNDLI, INTIM_Q)
        self.result = v2_to_engine_result(self.out)

    def test_intim_json_shape(self):
        data = engine_result_to_bed_intimacy_json(self.result, question=INTIM_Q)
        self.assertEqual(data["question_type"], "bed_intimacy")
        self.assertIn(data["final_verdict"], ("Harmonious", "Mixed", "Sensitive", "Strained"))

    def test_conjugal_compat_angle(self):
        data = engine_result_to_bed_intimacy_json(self.result, question=INTIM_Q)
        self.assertEqual(data.get("answer_focus"), "conjugal_compat")

    def test_strained_not_harmonious_praise(self):
        data = engine_result_to_bed_intimacy_json(self.result, question=INTIM_Q)
        data["intimacy_level"] = "strained"
        data["bed_intimacy_level"] = "strained"
        data["direct_answer"] = get_opening("conjugal_compat", "strained")
        text = render_bed_intimacy_template_answer(data, INTIM_Q)
        self.assertNotRegex(text, r"(?i)mostly\s+harmonious|comfort\s+align")

    def test_locked_template_valid(self):
        data = engine_result_to_bed_intimacy_json(self.result, question=INTIM_Q)
        ok, issues = validate_bed_intimacy_narrator_output(data.get("locked_template") or "", data)
        self.assertTrue(ok, msg=str(issues))

    def test_payload_no_chart(self):
        payload = bed_intimacy_engine_narrator_payload(self.result, question=INTIM_Q)
        parsed = json.loads(payload.split("ENGINE_JSON:", 1)[1].split("ANSWER_FOCUS:", 1)[0].strip())
        self.assertNotIn("ascendant", json.dumps(parsed).lower())

    def test_dna_bucket_sexual(self):
        dna = {"questions": [{"bucket": "physical_intimacy", "intent": "sexual comfort"}]}
        angle = detect_bed_intimacy_answer_focus(
            "sexual comfort partner ke saath possible hai", question_dna=dna
        )
        self.assertEqual(angle, "sexual_intimacy")


class BedIntimacyGoldenTests(unittest.TestCase):
    def test_golden_angles(self):
        failures = []
        for q, exp in GOLDEN_QUESTIONS:
            got = infer_bed_intimacy_angle(q)
            if got != exp:
                failures.append(f"{q!r}: expected {exp}, got {got}")
        self.assertEqual(failures, [], msg="\n".join(failures))

    def test_render_golden_batch(self):
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        for q, _ in GOLDEN_QUESTIONS[:10]:
            out = run_bed_intimacy_v2(SAMPLE_KUNDLI, q)
            data = engine_result_to_bed_intimacy_json(v2_to_engine_result(out), question=q)
            text = render_bed_intimacy_template_answer(data, q)
            ok, issues = validate_bed_intimacy_narrator_output(text, data)
            self.assertTrue(ok, msg=f"{q}: {issues}")


if __name__ == "__main__":
    unittest.main()

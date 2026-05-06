"""Unit tests for health_focus_routing.py (CAFB engine).

Run: cd artifacts/api-server && python3 -m pytest test_health_focus_routing.py -v
Or:  python3 test_health_focus_routing.py
"""
from __future__ import annotations
import os
import sys
import unittest

# Ensure module is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from health_focus_routing import (  # noqa: E402
    ATOMIC_CHECKS,
    build_health_focus,
    detect_health_axes,
    detect_hard_guard,
    detect_sensitive_bucket,
    is_health_question,
    trim_dasha_sections,
    strip_forbidden_vocab,
    inject_medical_disclaimer,
    apply_health_postinjectors,
)


class TestHardGuards(unittest.TestCase):
    """All hard-guard refusals must fire on canonical phrasings."""

    def test_crisis_suicide(self):
        for q in [
            "khatam kar lu life",
            "suicide karna chahta hu",
            "atmhatya soch raha",
            "marna chahta hu",
            "jeena nahi chahta",
            "kill myself",
            "end my life",
            "khud kushi karu kya",
        ]:
            self.assertEqual(detect_hard_guard(q), "CRISIS_REDIRECT", msg=q)

    def test_death_prediction(self):
        for q in [
            "kab marunga main",
            "kab marungi",
            "kab meri maut hogi",
            "meri death kab hogi",
            "kitne saal jiyunga",
            "umar kitni hai meri",
            "longevity kya hai",
            "when will i die",
        ]:
            self.assertEqual(detect_hard_guard(q), "REFUSE_DEATH", msg=q)

    def test_diagnosis_demand(self):
        for q in [
            "mujhe kya bimari hai",
            "kaun si bimari hai mujhe",
            "mujhe kaun si disease hai",
            "diagnose me",
            "chart se bimari bata",
            "chart me illness bata",
        ]:
            self.assertEqual(detect_hard_guard(q), "REFUSE_DIAGNOSIS", msg=q)

    def test_timing_decline(self):
        for q in [
            "kab beemar honga",
            "kab bimar ho jaunga",
            "bimari kis saal aayegi",
            "disease kab hoga",
            "mujhe kab bimari hogi",
        ]:
            self.assertEqual(detect_hard_guard(q), "REFUSE_TIMING_DECLINE", msg=q)

    def test_timing_recovery(self):
        for q in [
            "kab thik honga",
            "kab theek hounga",
            "recovery kab hogi",
            "cure date kab hai",
            "bimari kab jayegi",
        ]:
            self.assertEqual(detect_hard_guard(q), "REFUSE_TIMING_RECOVERY", msg=q)

    def test_timing_surgery(self):
        for q in [
            "operation kab karwau",
            "surgery muhurat kab",
            "operation date batao",
            "muhurat operation",
        ]:
            self.assertEqual(detect_hard_guard(q), "REFUSE_SURGERY_MUHURAT", msg=q)

    def test_cure_guarantee(self):
        for q in [
            "guarantee thik hounga",
            "100% cure milega kya",
            "100 percent recover hounga",
        ]:
            self.assertEqual(detect_hard_guard(q), "REFUSE_CURE_GUARANTEE", msg=q)

    def test_no_hard_guard_for_normal_qs(self):
        for q in [
            "meri sehat kaisi hai",
            "vitality strong hai",
            "immunity weak hai kya",
            "stress hai mujhe",
            "santaan yog hai",
        ]:
            self.assertIsNone(detect_hard_guard(q), msg=q)


class TestSensitiveBuckets(unittest.TestCase):
    def test_mental_bucket(self):
        for q in ["stress ho raha", "anxiety hai", "depression me hu", "neend nahi aati"]:
            self.assertEqual(detect_sensitive_bucket(q), "mental_health", msg=q)

    def test_repro_bucket(self):
        for q in ["santaan yog", "infertility issue", "pregnancy nahi ho rahi", "conceive karna hai"]:
            self.assertEqual(detect_sensitive_bucket(q), "reproductive", msg=q)

    def test_parent_bucket(self):
        for q in ["papa ki tabiyat", "mummy ki health", "father ki bimari", "maa ki sehat"]:
            self.assertEqual(detect_sensitive_bucket(q), "parent_health", msg=q)

    def test_addiction_bucket(self):
        for q in ["sharab ki addiction", "smoking chodni", "drugs ka nasha", "tambaku se chutkara"]:
            self.assertEqual(detect_sensitive_bucket(q), "addiction", msg=q)

    def test_no_bucket_for_neutral(self):
        for q in ["meri sehat", "immunity kaisi", "cardio risk hai"]:
            self.assertIsNone(detect_sensitive_bucket(q), msg=q)


class TestActionAxis(unittest.TestCase):
    def test_repro_action(self):
        for q in ["santaan yog hai", "fertility chart me", "pregnancy ka yog", "infertility issue"]:
            self.assertEqual(detect_health_axes(q)["action"], "REPRO_SUPPORT", msg=q)

    def test_mental_action(self):
        for q in ["stress hai", "anxiety chart me", "neend nahi aati", "tension bohot"]:
            self.assertEqual(detect_health_axes(q)["action"], "MENTAL_SUPPORT", msg=q)

    def test_chronic_action(self):
        for q in ["chronic illness ka risk", "lambi bimari hai", "purani bimari", "hereditary disease"]:
            self.assertEqual(detect_health_axes(q)["action"], "MANAGE_CHRONIC", msg=q)

    def test_recover_action(self):
        for q in ["kab thik hounga", "recovery jaldi ho", "healing kaise hogi"]:
            ax = detect_health_axes(q)
            # Either RECOVER action OR refuse-timing guard (both acceptable)
            self.assertTrue(ax["action"] == "RECOVER" or ax["hard_guard"], msg=q)

    def test_prevent_action(self):
        for q in ["aage chal ke kya risk", "future me kya tendency", "kya kya bimari ho sakti", "prevent kaise karu"]:
            self.assertEqual(detect_health_axes(q)["action"], "PREVENT", msg=q)

    def test_default_analyze(self):
        for q in ["meri sehat kaisi", "vitality kaisi hai", "chart me health"]:
            self.assertEqual(detect_health_axes(q)["action"], "ANALYZE", msg=q)


class TestSystemAxis(unittest.TestCase):
    def test_digestive(self):
        for q in ["pet kharab", "acidity ka issue", "digestion slow", "gas problem"]:
            self.assertIn("DIGESTIVE", detect_health_axes(q)["systems"], msg=q)

    def test_cardio(self):
        for q in ["heart problem", "dil ka issue", "blood pressure high", "bp ki tendency"]:
            self.assertIn("CARDIO", detect_health_axes(q)["systems"], msg=q)

    def test_musculoskeletal(self):
        for q in ["joint pain", "ghutna dard", "kamar pain", "haddi kamzor"]:
            self.assertIn("MUSCULOSKELETAL", detect_health_axes(q)["systems"], msg=q)

    def test_skin(self):
        for q in ["skin allergy", "chamdi me rash", "acne issue", "twacha problem"]:
            self.assertIn("SKIN", detect_health_axes(q)["systems"], msg=q)

    def test_endocrine(self):
        for q in ["thyroid issue", "hormonal imbalance", "sugar level", "pcod hai"]:
            self.assertIn("ENDOCRINE", detect_health_axes(q)["systems"], msg=q)

    def test_respiratory(self):
        for q in ["asthma hai", "saans phoolti", "cough lambi", "lung issue"]:
            self.assertIn("RESPIRATORY", detect_health_axes(q)["systems"], msg=q)

    def test_immune(self):
        for q in ["immunity weak", "baar baar bimar", "frequently sick", "stamina kam"]:
            self.assertIn("IMMUNE", detect_health_axes(q)["systems"], msg=q)


class TestEdgeAxis(unittest.TestCase):
    def test_accident(self):
        for q in ["accident ka risk", "injury chance", "chot lagne ka yog", "durghatna ka khatra"]:
            self.assertIn("ACCIDENT_RISK", detect_health_axes(q)["edges"], msg=q)

    def test_parent(self):
        for q in ["papa ki tabiyat", "mummy ki bimari", "father ka health", "maa ki sehat"]:
            self.assertIn("PARENT_HEALTH", detect_health_axes(q)["edges"], msg=q)

    def test_addiction(self):
        for q in ["sharab addiction", "smoking chodne ka", "tambaku ka nasha", "drug addiction"]:
            self.assertIn("ADDICTION", detect_health_axes(q)["edges"], msg=q)


class TestIntent(unittest.TestCase):
    def test_quality(self):
        for q in ["aage chal ke risk", "future me tendency", "kya kya bimari ho sakti", "prone to issues"]:
            self.assertEqual(detect_health_axes(q)["intent"], "QUALITY_TENDENCY", msg=q)

    def test_static_default(self):
        for q in ["meri sehat kaisi", "vitality strong hai", "immunity check"]:
            self.assertEqual(detect_health_axes(q)["intent"], "STATIC_VITALITY", msg=q)


class TestIsHealthQuestion(unittest.TestCase):
    def test_positive(self):
        for q in [
            "meri sehat kaisi",
            "vitality strong hai",
            "stress me hu",
            "papa ki tabiyat",
            "kab marunga",  # hard-guard owns
            "khatam kar lu",  # crisis owns
        ]:
            self.assertTrue(is_health_question(q), msg=q)

    def test_negative_animal(self):
        for q in ["mera kutta bimar", "billi ka health", "dog accident"]:
            self.assertFalse(is_health_question(q), msg=q)

    def test_negative_unrelated(self):
        for q in ["meri job kaisi", "shaadi kab", "paisa kab milega"]:
            self.assertFalse(is_health_question(q), msg=q)

    def test_ambiguous_with_career(self):
        # "weakness" alone with career context → not health
        self.assertFalse(is_health_question("career me weakness aa rahi"))
        # but "weakness" + body word → health
        self.assertTrue(is_health_question("body me weakness"))


class TestBuildHealthFocus(unittest.TestCase):
    def test_returns_string(self):
        for q in ["meri sehat", "kab marunga", "khatam kar lu", "papa ki tabiyat", ""]:
            out = build_health_focus(q)
            self.assertIsInstance(out, str, msg=q)
            self.assertTrue(len(out) > 100, msg=q)

    def test_crisis_only_in_block(self):
        out = build_health_focus("khatam kar lu life")
        self.assertIn("CRISIS_REDIRECT", out)
        self.assertIn("iCall", out)
        # Crisis should NOT include normal action/system blocks
        self.assertNotIn("[ANALYZE]", out)

    def test_refuse_death_appended(self):
        out = build_health_focus("kab marunga main")
        self.assertIn("REFUSE_DEATH", out)

    def test_refuse_diagnosis_appended(self):
        out = build_health_focus("mujhe kaun si bimari hai chart se bata")
        self.assertIn("REFUSE_DIAGNOSIS", out)

    def test_normal_q_has_action_intent_remedy(self):
        out = build_health_focus("meri sehat kaisi hai")
        self.assertIn("[ANALYZE]", out)
        self.assertIn("[STATIC_VITALITY]", out)
        self.assertIn("[REMEDY]", out)

    def test_killswitch_off_returns_fat_block(self):
        os.environ["HEALTH_FOCUS_AXES"] = "off"
        try:
            out = build_health_focus("meri sehat kaisi")
            # Fat block dumps all 29 atomic blocks
            for tag in ATOMIC_CHECKS.keys():
                self.assertIn(f"[{tag}]", out, msg=tag)
        finally:
            os.environ.pop("HEALTH_FOCUS_AXES", None)


class TestPostInjectors(unittest.TestCase):
    def test_disclaimer_appended(self):
        out = inject_medical_disclaimer("Test answer.", "meri sehat")
        self.assertIn("⚕️", out)
        self.assertIn("doctor", out.lower())

    def test_disclaimer_idempotent(self):
        once = inject_medical_disclaimer("Test answer.", "meri sehat")
        twice = inject_medical_disclaimer(once, "meri sehat")
        self.assertEqual(once, twice)

    def test_mental_disclaimer_helpline(self):
        out = inject_medical_disclaimer("Mind insight.", "stress me hu")
        self.assertIn("iCall", out)
        self.assertIn("9152987821", out)

    def test_repro_disclaimer(self):
        out = inject_medical_disclaimer("Repro insight.", "santaan yog")
        self.assertIn("gynaecologist", out.lower())

    def test_parent_disclaimer(self):
        out = inject_medical_disclaimer("Parent insight.", "papa ki tabiyat")
        self.assertIn("immediate doctor", out.lower())

    def test_addiction_disclaimer(self):
        out = inject_medical_disclaimer("Addiction insight.", "sharab ki addiction")
        self.assertIn("AA/NA", out)

    def test_disease_name_stripped(self):
        for body, leak in [
            ("Aapko diabetes ho sakta hai.", "diabetes"),
            ("Cancer ki tendency hai.", "cancer"),
            ("Tumor risk hai.", "tumor"),
            ("HIV positive ho sakta.", "hiv"),
        ]:
            cleaned, n = strip_forbidden_vocab(body)
            self.assertNotIn(leak.lower(), cleaned.lower(), msg=body)
            self.assertGreater(n, 0)

    def test_cure_guarantee_stripped(self):
        for body in [
            "100% cure milega",
            "guaranteed recovery",
            "definitely thik hounga",
        ]:
            cleaned, n = strip_forbidden_vocab(body)
            self.assertNotIn("100%", cleaned)
            self.assertGreater(n, 0)

    def test_disclaimer_killswitch(self):
        os.environ["HEALTH_DISCLAIMER"] = "off"
        try:
            out = inject_medical_disclaimer("body", "meri sehat")
            self.assertEqual(out, "body")
        finally:
            os.environ.pop("HEALTH_DISCLAIMER", None)


class TestChartSlicer(unittest.TestCase):
    def test_drops_dasha_sections(self):
        chart = (
            "## 1. JANM\nLagna data\n"
            "## 2. GRAHA\nPlanets\n"
            "## 4. DASHA\nDasha tree\n"
            "## 5. UPCOMING DASHA\nNext\n"
            "## 6. D9\nNavamsha\n"
            "## 8. GOCHAR\nTransit\n"
            "## 9. OVERLAY\nCombined\n"
        )
        out, dropped = trim_dasha_sections(chart, "meri sehat")
        self.assertEqual(dropped, 4)
        self.assertNotIn("## 4.", out)
        self.assertNotIn("## 5.", out)
        self.assertNotIn("## 8.", out)
        self.assertNotIn("## 9.", out)
        self.assertIn("## 1.", out)
        self.assertIn("## 2.", out)
        self.assertIn("## 6.", out)

    def test_chart_slice_killswitch(self):
        os.environ["HEALTH_CHART_SLICE"] = "off"
        try:
            chart = "## 1. A\n## 4. B\n## 5. C\n"
            out, dropped = trim_dasha_sections(chart, "meri sehat")
            self.assertEqual(dropped, 0)
            self.assertEqual(out, chart)
        finally:
            os.environ.pop("HEALTH_CHART_SLICE", None)

    def test_no_op_on_empty(self):
        out, dropped = trim_dasha_sections("", "meri sehat")
        self.assertEqual(dropped, 0)
        self.assertEqual(out, "")

    def test_no_op_on_non_section_text(self):
        text = "Just a chunk of text without sections."
        out, dropped = trim_dasha_sections(text, "meri sehat")
        self.assertEqual(dropped, 0)
        self.assertEqual(out, text)


class TestAxesSafeDefaults(unittest.TestCase):
    def test_empty_question_safe(self):
        ax = detect_health_axes("")
        self.assertEqual(ax["action"], "ANALYZE")
        self.assertEqual(ax["intent"], "STATIC_VITALITY")
        self.assertIsNone(ax["hard_guard"])

    def test_none_question_safe(self):
        ax = detect_health_axes(None)  # type: ignore[arg-type]
        self.assertEqual(ax["action"], "ANALYZE")


if __name__ == "__main__":
    unittest.main(verbosity=2)

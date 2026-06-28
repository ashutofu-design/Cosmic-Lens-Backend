"""~95 questions — verify timing domain + sub-bucket + engine routing."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.routing_audit import audit_question_routing

# (question, expected_domain, expected_sub_bucket_or_set, expected_engine_fragment)
ROUTING_CASES: list[tuple[str, str, str | frozenset, str]] = [
    # ── LOVE TIMING (30 checklist + extras) ─────────────────────────────────
    ("Meri life me pehla serious relationship kab shuru hoga?", "love", "general_love", "love_timing"),
    ("Mujhe mera true love soulmate kis saal ya mahine me milega?", "love", "general_love", "love_timing"),
    ("Mera naya relationship kis dasha ya transit window me trigger ho raha hai?", "love", "timing", "love_timing"),
    ("Mujhe koi approach kab karega proposal kab milega?", "love", "commitment", "love_timing"),
    ("Kya is saal current transit me meri life me koi naya insaan aayega?", "love", "meeting", "love_timing"),
    ("Mere social circle se bahar ka koi insaan meri life me kab enter karega?", "love", "meeting", "love_timing"),
    ("Mujhe naya partner dhoondhne ke liye sabse favorable dasha window kaun si hai?", "love", "general_love", "love_timing"),
    ("Rahu Ketu ke transit me jo attraction hua hai kya wo commitment me badlega?", "love", "commitment", "love_timing"),
    ("Mera current dry spell single status kis month me khatam hoga?", "love", "general_love", "love_timing"),
    ("Kis specific mahine me Surya ya Venus ke gochar se mujhe apna partner milega?", "love", "timing", "love_timing"),
    ("Kya mera Ex meri life me wapas aayega agar haan to kab?", "love", "reconciliation", "love_timing"),
    ("Humare beech chal raha break-up ya separation kab khatam hoga?", "love", "reconciliation", "love_timing"),
    ("Mera partner mujhe khud se contact kab karega unblock kab karega?", "love", "reconciliation", "love_timing"),
    ("Kya chal rahi Antardasha me humare purane rishte ko dusra chance milega?", "love", "reconciliation", "love_timing"),
    ("Retrograde Venus vakri shukra ke dauran kya mera purana pyaar wapas aayega?", "love", "reconciliation", "love_timing"),
    ("Humare beech chal rahi galatfehmiyan misunderstandings kis mahine me door hongi?", "love", "stress_phase", "love_timing"),
    ("No-contact situation kab break hogi?", "love", "reconciliation", "love_timing"),
    ("Mera partner shaadi ke liye haan kab bolega commitment kab dega?", "love", "commitment", "love_timing"),
    ("Humare ghar wale parents is rishte ke liye kab raazi agree honge?", "love", "family_approval", "love_timing"),
    ("Humare rishte ko societal recognition samaaj me kab milega?", "love", "family_approval", "love_timing"),
    ("Humare rishte me chal raha stressful phase kab tak chalega?", "love", "stress_phase", "love_timing"),
    ("Mujhe kab pata chalega ki mera partner loyalty maintain kar raha hai ya dhoka de raha hai?", "love", "discovery", "love_timing"),
    ("Kya 6th lord ki dasha me humare rishte me koi teesra insaan third party aayega?", "love", "affair", "love_timing"),
    ("Humara chal raha court case ya relationship dispute kab resolve hoga?", "love", "stress_phase", "love_timing"),
    ("Kis dasha window me humara permanently breakup hone ka khatra hai?", "love", "breakup", "love_timing"),
    ("Kya abhi chal rahi dasha me mujhe relationship se doori healing period kab tak hai?", "love", "healing", "love_timing"),
    ("Mera relationship kab shuru hoga?", "love", "timing", "love_timing"),
    ("Patchup kab hoga?", "love", "reconciliation", "love_timing"),
    ("Crush kab respond karega?", "love", "one_sided", "love_timing"),
    ("Pyaar kab milega?", "love", "timing", "love_timing"),
    # ── MARRIAGE (must NOT go to love) ─────────────────────────────────────
    ("Meri shaadi kab hogi?", "marriage", "timing", "marriage_engine"),
    ("Love marriage kab hogi?", "marriage", "timing", "marriage_engine"),
    ("Mujhe biwi kab milegi?", "marriage", "timing", "marriage_engine"),
    ("Engagement kab hogi?", "marriage", "timing", "marriage_engine"),
    ("Roka kab hoga?", "marriage", "timing", "marriage_engine"),
    ("Shaadi me delay kab khatam hoga?", "marriage", "timing", "marriage_engine"),
    ("Humara love relationship marriage me kab convert hoga?", "marriage", "timing", "marriage_engine"),
    ("Jupiter Saturn double transit 7th house par shaadi ka yoga kab banega?", "marriage", "timing", "marriage_engine"),
    ("Court marriage ya elopement kab hoga?", "marriage", "timing", "marriage_engine"),
    ("Rishta pakka hone ka time kab hai?", "marriage", "timing", "marriage_engine"),
    # ── CAREER ──────────────────────────────────────────────────────────────
    ("Promotion kab milega?", "career", "promotion", "career_timing"),
    ("Transfer kab hoga?", "career", "transfer", "career_timing"),
    ("Govt job kab lagegi?", "career", "govt_job", "career_timing"),
    ("Resignation kab deun?", "career", "resignation", "career_timing"),
    ("Job change kab karun?", "career", "job_change", "career_timing"),
    ("Naukri kab lagegi?", "career", frozenset({"general_career", "new_job_timing", "govt_job"}), "career_timing"),
    ("Salary hike kab milega?", "career", "promotion", "career_timing"),
    ("Career setback kab khatam hoga?", "career", frozenset({"career_setback", "setback", "general_career"}), "career_timing"),
    ("Kaunsi field choose karun career?", "career", frozenset({"career_field_choice", "field_choice", "general_career"}), "career_timing"),
    ("Upsc exam clear kab hoga?", "career", "govt_job", "career_timing"),
    ("Interview kab clear hoga?", "career", frozenset({"general_career", "new_job_timing", "govt_job"}), "career_timing"),
    ("Company switch kab karun?", "career", "job_change", "career_timing"),
    # ── TRAVEL ──────────────────────────────────────────────────────────────
    ("Videsh kab jaunga?", "travel", frozenset({"foreign_travel", "general_travel", "visa"}), "travel_engine"),
    ("Foreign settlement kab hoga?", "travel", frozenset({"settlement", "foreign_settlement", "general_travel"}), "travel_engine"),
    ("PR kab milega?", "travel", frozenset({"pr", "settlement", "general_travel"}), "travel_engine"),
    ("Visa kab milega?", "travel", frozenset({"visa", "general_travel"}), "travel_engine"),
    ("Abroad shift kab hoga?", "travel", frozenset({"settlement", "general_travel"}), "travel_engine"),
    # ── EDUCATION ───────────────────────────────────────────────────────────
    ("Exam clear kab hoga?", "education", frozenset({"exam_success", "general_education"}), "education_engine"),
    ("Admission kab milega?", "education", frozenset({"admission", "exam_success", "general_education"}), "education_engine"),
    ("Degree kab complete hogi?", "education", frozenset({"exam_success", "graduation", "general_education"}), "education_engine"),
    ("Board result kab aayega?", "education", frozenset({"exam_success", "result", "general_education"}), "education_engine"),
    # ── CHILDREN ────────────────────────────────────────────────────────────
    ("Baby kab hoga?", "children", frozenset({"conception", "general_children"}), "children_engine"),
    ("Pregnancy kab hogi?", "children", frozenset({"conception", "pregnancy", "general_children"}), "children_engine"),
    ("Santan kab milega?", "children", frozenset({"conception", "general_children"}), "children_engine"),
    # ── PROPERTY ────────────────────────────────────────────────────────────
    ("Ghar kab lunga?", "property", frozenset({"purchase", "registry", "general_property"}), "property_engine"),
    ("Property registry kab hogi?", "property", frozenset({"registry", "general_property"}), "property_engine"),
    # ── LITIGATION ──────────────────────────────────────────────────────────
    ("Mera criminal case kab resolve hoga?", "litigation", frozenset({"general_litigation", "case_outcome"}), "litigation_engine"),
    ("Bail kab milegi?", "litigation", frozenset({"bail_theme", "general_litigation"}), "litigation_engine"),
    # ── FINANCE ─────────────────────────────────────────────────────────────
    ("Loan kab clear hoga?", "finance", frozenset({"general_finance", "loan"}), "wealth_engine"),
    ("Sudden wealth kab milegi?", "finance", frozenset({"general_finance", "windfall"}), "wealth_engine"),
    # ── LOVE STATIC (no kab) ──────────────────────────────────────────────────
    ("Kya wo mujhse pyar karta hai?", "love", frozenset({"general_love", "one_sided", "existing_status"}), "love_static"),
    ("Kya mera partner loyal hai?", "love", frozenset({"affair_third_party", "general_love", "existing_status"}), "love_static"),
    ("Hamari kundli match kaisi hai?", "love", "milan", "milan_engine"),
    ("Hum compatible hain kya?", "love", frozenset({"compatibility", "general_love", "milan"}), "love"),
    # ── COLLISION GUARDS ────────────────────────────────────────────────────
    ("Nifty kab badhega?", "general", "general", "llm_only"),
    ("Share market me entry kab karni chahiye?", "general", "general", "llm_only"),
    # ── MORE LOVE / MARRIAGE / CAREER (reach 90+) ───────────────────────────
    ("Long distance relationship kab theek hoga?", "love", "meeting", "love_timing"),
    ("Boyfriend kab propose karega?", "love", "commitment", "love_timing"),
    ("Girlfriend se patchup kab hoga?", "love", "reconciliation", "love_timing"),
    ("Meri crush kab notice karegi?", "love", "one_sided", "love_timing"),
    ("Kya mera ex wapas aayega?", "love", frozenset({"reconciliation", "general_love"}), "love_timing"),
    ("Shaadi ke baad divorce kab hoga?", "marriage", "timing", "marriage_engine"),
    ("Mangni kab hogi?", "marriage", "timing", "marriage_engine"),
    ("Notice period kab khatam hoga?", "career", "resignation", "career_timing"),
    ("Govt exam selection kab hoga?", "career", "govt_job", "career_timing"),
    ("Business start kab karun?", "career", frozenset({"general_career", "career_field_choice"}), "career_timing"),
    ("Canada PR kab milega?", "travel", frozenset({"pr", "settlement", "general_travel"}), "travel_engine"),
    ("Study abroad kab ja sakta hun?", "education", frozenset({"study_abroad", "general_education", "exam_success"}), "education_engine"),
    ("Conception kab hoga?", "children", frozenset({"conception", "general_children"}), "children_engine"),
    ("Flat kab lunga?", "property", frozenset({"purchase", "registry", "general_property"}), "property_engine"),
    ("Case faisla kab aayega?", "litigation", frozenset({"case_outcome", "general_litigation"}), "litigation_engine"),
    ("Inheritance kab milega?", "finance", frozenset({"general_finance", "inheritance"}), "wealth_engine"),
    ("Kya wo mujhse pyar karta hai ya nahi?", "love", frozenset({"general_love", "one_sided"}), "love_static"),
    ("Meri love life kab sudhregi?", "love", "general_love", "love_timing"),
]


class TestRoutingAudit100(unittest.TestCase):
    def test_routing_matrix(self):
        failures: list[str] = []
        for q, exp_dom, exp_sub, exp_eng in ROUTING_CASES:
            r = audit_question_routing(q)
            sub_ok = (
                r.sub_bucket == exp_sub
                if isinstance(exp_sub, str)
                else r.sub_bucket in exp_sub
            )
            eng_ok = exp_eng in r.engine
            if r.domain != exp_dom or not sub_ok or not eng_ok:
                failures.append(
                    f"Q: {q[:70]!r}\n"
                    f"  got domain={r.domain!r} sub={r.sub_bucket!r} engine={r.engine!r} "
                    f"timing={r.is_timing}\n"
                    f"  want domain={exp_dom!r} sub={exp_sub!r} engine~={exp_eng!r}"
                )
        if failures:
            self.fail("\n\n".join(failures))

    def test_love_marriage_collision(self):
        """Love-marriage Q must hit marriage, never love timing."""
        for q in (
            "Love marriage kab hogi?",
            "Pyaar shaadi kab hogi?",
            "Meri shaadi kab hogi?",
        ):
            r = audit_question_routing(q)
            self.assertEqual(r.domain, "marriage", q)
            self.assertNotIn("love_timing", r.engine, q)

    def test_count_at_least_90(self):
        self.assertGreaterEqual(len(ROUTING_CASES), 90)


if __name__ == "__main__":
    unittest.main()

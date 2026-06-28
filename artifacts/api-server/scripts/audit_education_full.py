#!/usr/bin/env python3
"""Full non-timing education audit — routing, scope, evidence alignment."""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_career.classifier import classify_career_archetype, is_career_static_question
from ask_education import run_education_static_engine
from ask_education.classifier import classify_education_archetype, is_education_static_question
from ask_education.education_registry import detect_education_archetype

K = {
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
}


@dataclass
class Case:
    q: str
    domain: str  # education | career | off | timing
    engine: str
    focus_rx: str
    min_evidence: int = 4


def E(q: str, eng: str, rx: str, min_e: int = 4) -> Case:
    return Case(q, "education", eng, rx, min_e)


def OFF(q: str) -> Case:
    return Case(q, "off", "", "")


def CAREER(q: str, eng: str = "career_milestones") -> Case:
    return Case(q, "career", eng, r"career|job|10th|milestones|education_career")


def TIMING(q: str) -> Case:
    return Case(q, "timing", "", "")


CASES: list[Case] = [
    # ── exam_success (EN / Hinglish / Hindi) ──
    E("Will I pass my exam?", "exam_success", r"exam|Mercury|Jupiter|5th|learning"),
    E("Kya mera exam pass ho jayega?", "exam_success", r"exam|Mercury|Jupiter|learning"),
    E("Exam clear kar paunga kya?", "exam_success", r"exam|clear|Mercury|Jupiter"),
    E("Result achha aayega kya?", "exam_success", r"exam|result|Mercury|Jupiter"),
    E("Selection ho jayegi kya?", "exam_success", r"exam|selection|Mercury|Jupiter"),
    E("Kya main exam crack kar paunga?", "exam_success", r"exam|crack|Mercury|Jupiter"),
    E("Final exam me pass ho jaunga?", "exam_success", r"exam|pass|Mercury|Jupiter"),
    E("Test clear ho sakta hai?", "exam_success", r"exam|Mercury|Jupiter|learning"),
    E("Pariksha pass ho jayegi?", "exam_success", r"exam|Mercury|Jupiter|learning"),
    E("Imtihaan clear ho payegi?", "exam_success", r"exam|Mercury|Jupiter|learning"),
    E("Exam me top kar paunga?", "exam_success", r"exam|Mercury|Jupiter|learning"),
    E("Result fail to nahi hoga?", "exam_success", r"exam|result|Mercury|Jupiter"),
    E("Kya exam selection confirm hai?", "exam_success", r"exam|selection|Mercury|Jupiter"),
    E("Annual exam pass hoga?", "exam_success", r"exam|Mercury|Jupiter|learning"),
    E("Semester exam clear ho jayega?", "exam_success", r"exam|Mercury|Jupiter|learning"),
    E("क्या मैं परीक्षा पास कर पाऊंगा?", "exam_success", r"exam|Mercury|Jupiter|learning"),
    E("Result kharab to nahi aayega?", "exam_success", r"exam|result|Mercury|Jupiter"),
    # ── competitive_exam ──
    E("NEET exam clear ho sakta hai kya?", "competitive_exam", r"Competitive|NEET|Mercury|Jupiter"),
    E("JEE main crack kar paunga?", "competitive_exam", r"Competitive|Mercury|Jupiter|entrance"),
    E("JEE advanced ke liye chart kaisa hai?", "competitive_exam", r"Competitive|Mercury|Jupiter"),
    E("12th board exam me achha result aayega?", "competitive_exam", r"Competitive|board|Mercury|Jupiter"),
    E("CBSE board exam pass ho jayega?", "competitive_exam", r"Competitive|board|Mercury|Jupiter"),
    E("ICSE board marks achhe aayenge?", "competitive_exam", r"Competitive|board|Mercury|Jupiter"),
    E("CAT exam crack kar paunga?", "competitive_exam", r"Competitive|Mercury|Jupiter"),
    E("GATE exam clear ho jayega?", "competitive_exam", r"Competitive|Mercury|Jupiter"),
    E("CLAT entrance exam ke chances?", "competitive_exam", r"Competitive|entrance|Mercury|Jupiter"),
    E("Medical entrance exam clear hoga?", "competitive_exam", r"Competitive|entrance|Mercury|Jupiter"),
    E("IIT entrance ke liye suitable hoon?", "competitive_exam", r"Competitive|entrance|Mercury|Jupiter"),
    E("Law entrance test clear ho payega?", "competitive_exam", r"Competitive|entrance|Mercury|Jupiter"),
    E("10th board exam top kar paunga?", "competitive_exam", r"Competitive|board|Mercury|Jupiter"),
    E("State board exam clear ho jayega?", "competitive_exam", r"Competitive|board|Mercury|Jupiter"),
    E("Term exam competitive level par hai?", "competitive_exam", r"Competitive|Mercury|Jupiter"),
    E("Entrance test me selection hogi?", "competitive_exam", r"Competitive|entrance|Mercury|Jupiter"),
    E("CMAT exam clear kar paungi?", "competitive_exam", r"Competitive|Mercury|Jupiter"),
    E("MAT exam ke chances kaisa?", "competitive_exam", r"Competitive|Mercury|Jupiter"),
    # ── higher_studies ──
    E("Higher studies videsh mein possible hai?", "higher_studies", r"higher|9th|Rahu|Mercury|Jupiter"),
    E("Masters abroad ke liye chart kaisa hai?", "higher_studies", r"higher|abroad|9th|Rahu"),
    E("PhD ke yog hain kya?", "higher_studies", r"higher|PhD|9th|Jupiter"),
    E("Post graduation ke liye suitable hoon?", "higher_studies", r"higher|9th|Jupiter|Mercury"),
    E("Study abroad possible hai?", "higher_studies", r"abroad|9th|Rahu|higher"),
    E("Foreign university me padhai ho sakti hai?", "higher_studies", r"foreign|9th|Rahu|higher"),
    E("GRE score ke saath videsh padhai?", "higher_studies", r"GRE|9th|Rahu|higher"),
    E("IELTS ke baad abroad study?", "higher_studies", r"IELTS|9th|Rahu|abroad"),
    E("Research degree ke liye chart?", "higher_studies", r"research|9th|Jupiter|higher"),
    E("Dissertation complete ho payegi?", "higher_studies", r"research|9th|Jupiter|higher"),
    E("PG course ke liye yog hai?", "higher_studies", r"higher|9th|Jupiter|post"),
    E("Overseas studies ke chances?", "higher_studies", r"overseas|9th|Rahu|higher"),
    E("Student visa ke saath padhai abroad?", "higher_studies", r"visa|9th|Rahu|abroad"),
    E("Doctorate ke liye suitable hoon?", "higher_studies", r"doctorate|9th|Jupiter|higher"),
    E("Thesis work successful hoga?", "higher_studies", r"thesis|9th|Jupiter|research"),
    E("Videsh me university admission ke saath padhai?", "higher_studies", r"abroad|9th|Rahu|higher"),
    E("Master's degree ke liye chart strong hai?", "higher_studies", r"master|9th|Jupiter|higher"),
    # ── study_field ──
    E("Mere liye kaunsi stream best rahegi science ya commerce?", "study_field", r"stream|field|Mercury|4th|5th"),
    E("PCM ya PCB kaunsa choose karun?", "study_field", r"stream|field|Mercury|4th|5th"),
    E("Kaunsi line padhun?", "study_field", r"field|stream|Mercury|4th|5th"),
    E("Which subject should I study?", "study_field", r"subject|field|Mercury|4th|5th"),
    E("Arts ya science kaunsa better?", "study_field", r"stream|field|Mercury|4th|5th"),
    E("Commerce ya science stream?", "study_field", r"stream|Mercury|4th|5th"),
    E("Best field for study kya hai?", "study_field", r"field|stream|Mercury|4th|5th"),
    E("Kaunsa course choose karun padhai ke liye?", "study_field", r"course|field|Mercury|4th|5th"),
    E("PCMB lena chahiye ya nahi?", "study_field", r"stream|field|Mercury|4th|5th"),
    E("Humanities ya science better rahega?", "study_field", r"stream|field|Mercury|4th|5th"),
    E("Right stream for me kya hai?", "study_field", r"stream|field|Mercury|4th|5th"),
    E("Kaunsi branch best rahegi?", "study_field", r"branch|field|Mercury|4th|5th"),
    E("Subject choose karne ke liye chart?", "study_field", r"subject|field|Mercury|4th|5th"),
    E("Science stream lena sahi hoga?", "study_field", r"stream|Mercury|4th|5th"),
    E("What should I study after 10th?", "study_field", r"field|stream|Mercury|4th|5th"),
    # ── specialization_path ──
    E("Medical line ke liye chart sahi hai?", "specialization_path", r"Medical|specialization|Mercury|Jupiter"),
    E("Engineering line padh sakta hoon?", "specialization_path", r"Engineering|specialization|Mercury|Jupiter"),
    E("Law line ke liye suitable hoon?", "specialization_path", r"Law|specialization|Mercury|Jupiter"),
    E("CA line ke liye chart kaisa hai?", "specialization_path", r"CA|specialization|Mercury|Jupiter"),
    E("Doctor banne ke liye padhai sahi hai?", "specialization_path", r"Medical|doctor|Mercury|Jupiter"),
    E("Engineer banne ke liye line sahi hai?", "specialization_path", r"Engineering|Mercury|Jupiter"),
    E("Lawyer banne ke liye suitable?", "specialization_path", r"Law|Mercury|Jupiter"),
    E("Teaching line ke liye yog?", "specialization_path", r"Teaching|Mercury|Jupiter"),
    E("Architecture line suit karegi?", "specialization_path", r"Architecture|Mercury|Jupiter"),
    E("Design line ke liye chart?", "specialization_path", r"Design|Mercury|Jupiter"),
    E("Science line strong hai chart me?", "specialization_path", r"Science line|Mercury|Jupiter"),
    E("Commerce line ke liye suitable?", "specialization_path", r"Commerce line|Mercury|Jupiter"),
    E("Arts line padh sakta hoon?", "specialization_path", r"Arts line|Mercury|Jupiter"),
    E("MBBS line ke liye chart?", "specialization_path", r"Medical|MBBS|Mercury|Jupiter"),
    E("LLB line suit karegi?", "specialization_path", r"Law|LLB|Mercury|Jupiter"),
    # ── admission ──
    E("College admission milega kya?", "admission", r"admission|4th|5th|9th|seat"),
    E("University seat confirm hogi?", "admission", r"admission|seat|4th|5th|9th"),
    E("Institute me admission possible hai?", "admission", r"admission|4th|5th|9th"),
    E("College lagega kya mujhe?", "admission", r"admission|college|4th|5th|9th"),
    E("Merit list me naam aayega?", "admission", r"admission|merit|4th|5th|9th"),
    E("Waitlist clear ho jayegi?", "admission", r"admission|waitlist|4th|5th|9th"),
    E("Enrollment confirm hoga?", "admission", r"admission|enrol|4th|5th|9th"),
    E("NEET ke baad college admission milega?", "admission", r"admission|4th|5th|9th|seat"),
    E("JEE rank ke baad admission confirm?", "admission", r"admission|4th|5th|9th|seat"),
    E("University admission reject to nahi?", "admission", r"admission|4th|5th|9th"),
    E("College seat mil jayegi?", "admission", r"admission|seat|4th|5th|9th"),
    E("Admission possible hai kya?", "admission", r"admission|4th|5th|9th"),
    E("Institute admission ke chances?", "admission", r"admission|4th|5th|9th"),
    E("College mil payega kya?", "admission", r"admission|college|4th|5th|9th"),
    E("Seat allotment achhi hogi?", "admission", r"admission|seat|4th|5th|9th"),
    # ── scholarship ──
    E("Scholarship milegi kya?", "scholarship", r"scholarship|9th|Jupiter|Mercury"),
    E("Merit scholarship ke chances kaisa?", "scholarship", r"scholarship|merit|9th|Jupiter"),
    E("Stipend mil sakta hai padhai ke liye?", "scholarship", r"stipend|scholarship|9th|Jupiter"),
    E("Fee waiver possible hai?", "scholarship", r"scholarship|fee|9th|Jupiter"),
    E("Financial aid for study?", "scholarship", r"scholarship|financial|9th|Jupiter"),
    E("Free education ke chances?", "scholarship", r"scholarship|free|9th|Jupiter"),
    E("Funded study possible hai?", "scholarship", r"scholarship|fund|9th|Jupiter"),
    E("Education loan for study sahi rahega?", "scholarship", r"scholarship|loan|9th|Jupiter"),
    E("Sponsorship for higher studies?", "scholarship", r"scholarship|sponsor|9th|Jupiter"),
    E("Vidyalakshmi scholarship milegi?", "scholarship", r"scholarship|9th|Jupiter"),
    E("Scholarship confirm ho jayegi?", "scholarship", r"scholarship|9th|Jupiter"),
    E("Merit based scholarship ke yog?", "scholarship", r"scholarship|merit|9th|Jupiter"),
    # ── degree_completion ──
    E("Degree complete ho jayegi kya?", "degree_completion", r"degree|graduat|4th|9th|Jupiter"),
    E("Graduation ho paayega?", "degree_completion", r"graduat|degree|4th|9th|Jupiter"),
    E("Final year clear ho jayega?", "degree_completion", r"degree|final|4th|9th|Jupiter"),
    E("College complete kar paunga?", "degree_completion", r"degree|college|4th|9th|Jupiter"),
    E("Pass out ho jaunga time par?", "degree_completion", r"graduat|pass out|4th|9th|Jupiter"),
    E("Degree poori ho payegi?", "degree_completion", r"degree|4th|9th|Jupiter"),
    E("Graduation ho jaayegi?", "degree_completion", r"graduat|4th|9th|Jupiter"),
    E("Degree nahi rukegi na?", "degree_completion", r"degree|4th|9th|Jupiter"),
    E("College khatam ho jayega time se?", "degree_completion", r"degree|college|4th|9th|Jupiter"),
    E("Graduate ban paunga?", "degree_completion", r"graduat|4th|9th|Jupiter"),
    E("Final year pass ho jayega?", "degree_completion", r"degree|final|4th|9th|Jupiter"),
    E("Degree completion ke chances?", "degree_completion", r"degree|4th|9th|Jupiter"),
    # ── marks_performance ──
    E("Achhe marks aayenge kya?", "marks_performance", r"marks|Mercury|5th|percentage"),
    E("Percentage acchi ban sakti hai?", "marks_performance", r"percentage|marks|Mercury|5th"),
    E("GPA strong ho sakta hai?", "marks_performance", r"GPA|marks|Mercury|5th"),
    E("Topper ban sakta hoon?", "marks_performance", r"topper|marks|Mercury|5th"),
    E("First division milegi?", "marks_performance", r"division|marks|Mercury|5th"),
    E("Distinction mil sakti hai?", "marks_performance", r"distinction|marks|Mercury|5th"),
    E("Kitne marks aayenge?", "marks_performance", r"marks|Mercury|5th|percentage"),
    E("Low marks to nahi aayenge?", "marks_performance", r"marks|Mercury|5th"),
    E("High marks ke chances?", "marks_performance", r"marks|Mercury|5th|high"),
    E("Grade achhi aayegi?", "marks_performance", r"grade|marks|Mercury|5th"),
    E("CGPA improve ho sakta hai?", "marks_performance", r"CGPA|marks|Mercury|5th"),
    E("Rank in class achhi aayegi?", "marks_performance", r"rank|marks|Mercury|5th"),
    E("Merit position strong hogi?", "marks_performance", r"merit|marks|Mercury|5th"),
    E("Good marks ke yog hain?", "marks_performance", r"marks|Mercury|5th|good"),
    # ── study_focus ──
    E("Padhai me mann nahi lagta kya karun?", "study_focus", r"focus|concentration|5th|Mercury|mann"),
    E("Study focus weak hai?", "study_focus", r"focus|concentration|5th|Mercury"),
    E("Concentration padhai me kam hai?", "study_focus", r"concentration|focus|5th|Mercury"),
    E("Padhai se bore ho jata hoon?", "study_focus", r"bore|focus|5th|Mercury|study"),
    E("Distraction zyada hai padhai me?", "study_focus", r"distract|focus|5th|Mercury"),
    E("Study habit improve kaise karun?", "study_focus", r"habit|focus|5th|Mercury|study"),
    E("Motivation padhai me nahi aati?", "study_focus", r"motivation|focus|5th|Mercury|study"),
    E("Lazy in study hoon?", "study_focus", r"lazy|focus|5th|Mercury|study"),
    E("Procrastination padhai me problem?", "study_focus", r"procrastinat|focus|5th|Mercury"),
    E("Padhai ka man nahi karta?", "study_focus", r"mann|focus|5th|Mercury|padhai"),
    E("Attendance problem padhai me?", "study_focus", r"attendance|focus|5th|Mercury|study"),
    E("Mind not in study?", "study_focus", r"focus|mind|5th|Mercury|study"),
    E("Study discipline weak hai?", "study_focus", r"discipline|focus|5th|Mercury|study"),
    # ── learning_ability ──
    E("Meri buddhi padhai ke liye strong hai?", "learning_ability", r"buddhi|intellect|Mercury|5th|memory"),
    E("Maths me weak hoon kya karun?", "learning_ability", r"weak|Mercury|5th|memory|math"),
    E("Memory strong hai padhai ke liye?", "learning_ability", r"memory|Mercury|5th|retention"),
    E("Grasping power kaisi hai?", "learning_ability", r"grasp|Mercury|5th|intellect"),
    E("English me weak hoon padhai me?", "learning_ability", r"weak|Mercury|5th|english"),
    E("Science subject weak hai?", "learning_ability", r"weak|Mercury|5th|science"),
    E("Slow learner hoon kya?", "learning_ability", r"slow|Mercury|5th|learning"),
    E("Intelligence padhai ke liye?", "learning_ability", r"intellect|Mercury|5th|buddhi"),
    E("Yaad karne ki power weak?", "learning_ability", r"memory|yaad|Mercury|5th"),
    E("Analytical mind padhai me?", "learning_ability", r"analytical|Mercury|5th|logical"),
    E("Logical mind strong hai study me?", "learning_ability", r"logical|Mercury|5th|mind"),
    E("Creative mind padhai me help karega?", "learning_ability", r"creative|Mercury|5th|mind"),
    E("Padhai me dimaag strong hai?", "learning_ability", r"dimaag|Mercury|5th|intellect"),
    E("Retention weak hai kya?", "learning_ability", r"retention|memory|Mercury|5th"),
    # ── coaching_support ──
    E("Coaching join karni chahiye ya self study?", "coaching_support", r"coaching|Mercury|Jupiter|self"),
    E("NEET coaching sahi rahegi?", "coaching_support", r"coaching|NEET|Mercury|Jupiter"),
    E("Tuition leni chahiye?", "coaching_support", r"tuition|coaching|Mercury|Jupiter"),
    E("IIT coaching join karun?", "coaching_support", r"coaching|Mercury|Jupiter"),
    E("Online course better ya coaching?", "coaching_support", r"coaching|online|Mercury|Jupiter"),
    E("Self study ya coaching better?", "coaching_support", r"coaching|self|Mercury|Jupiter"),
    E("Mentor chahiye padhai ke liye?", "coaching_support", r"mentor|coaching|Mercury|Jupiter"),
    E("Unacademy se padhai sahi rahegi?", "coaching_support", r"coaching|online|Mercury|Jupiter"),
    E("Edtech course join karun?", "coaching_support", r"coaching|online|Mercury|Jupiter"),
    E("Tutor lena chahiye maths ke liye?", "coaching_support", r"tutor|coaching|Mercury|Jupiter"),
    E("Coaching best rahegi ya nahi?", "coaching_support", r"coaching|Mercury|Jupiter"),
    E("Tuition sahi rahegi science ke liye?", "coaching_support", r"tuition|coaching|Mercury|Jupiter"),
    # ── education_obstacles ──
    E("Padhai me backlog clear ho jayega?", "education_obstacles", r"backlog|obstacle|Saturn|6th|8th"),
    E("Gap year ke baad padhai continue ho sakti hai?", "education_obstacles", r"gap|obstacle|Saturn|6th|8th"),
    E("Back year clear ho jayegi?", "education_obstacles", r"back|obstacle|Saturn|6th|8th"),
    E("ATKT clear ho jayegi?", "education_obstacles", r"ATKT|obstacle|Saturn|6th|8th"),
    E("Supplementary exam clear hoga?", "education_obstacles", r"supplementary|obstacle|Saturn|6th|8th"),
    E("Reappear exam pass ho jayega?", "education_obstacles", r"reappear|obstacle|Saturn|6th|8th"),
    E("Compartment exam clear?", "education_obstacles", r"compartment|obstacle|Saturn|6th|8th"),
    E("Padhai ruki hui continue ho sakti hai?", "education_obstacles", r"delay|obstacle|Saturn|6th|8th"),
    E("Study delay ho raha hai?", "education_obstacles", r"delay|obstacle|Saturn|6th|8th"),
    E("Degree delay ho jayegi kya?", "education_obstacles", r"delay|degree|Saturn|6th|8th"),
    E("Graduation delay hogi?", "education_obstacles", r"delay|graduat|Saturn|6th|8th"),
    E("Fail ho gaya semester dubara pass?", "education_obstacles", r"fail|obstacle|Saturn|6th|8th"),
    E("Padhai me problem zyada hai?", "education_obstacles", r"problem|obstacle|Saturn|6th|8th"),
    E("Drop year lena padega kya?", "education_obstacles", r"drop|gap|obstacle|Saturn|6th|8th"),
    # ── vocational_diploma ──
    E("ITI course suit karega?", "vocational_diploma", r"ITI|vocational|Mercury|4th|diploma"),
    E("Polytechnic diploma ke liye chart?", "vocational_diploma", r"polytechnic|diploma|Mercury|4th"),
    E("Vocational course better rahega?", "vocational_diploma", r"vocational|Mercury|4th|diploma"),
    E("Certificate course ke liye suitable?", "vocational_diploma", r"certificate|Mercury|4th|diploma"),
    E("Skill course join karun?", "vocational_diploma", r"skill|Mercury|4th|vocational"),
    E("Trade course ke liye chart?", "vocational_diploma", r"trade|Mercury|4th|vocational"),
    E("Technical diploma after 10th?", "vocational_diploma", r"diploma|technical|Mercury|4th"),
    E("Short term course beneficial?", "vocational_diploma", r"short|course|Mercury|4th|diploma"),
    E("Certification program suit karega?", "vocational_diploma", r"certification|Mercury|4th|diploma"),
    E("Diploma course ke chances?", "vocational_diploma", r"diploma|Mercury|4th|vocational"),
    E("Polytechnic admission ke saath diploma?", "vocational_diploma", r"polytechnic|diploma|Mercury|4th"),
    E("ITI trade select karun?", "vocational_diploma", r"ITI|trade|Mercury|4th|vocational"),
    # ── general_education ──
    E("Meri padhai overall kaisi rahegi?", "general_education", r"education|4th|5th|9th|Mercury|Jupiter"),
    E("Study life kaisi rahegi?", "general_education", r"education|4th|5th|9th|Mercury|Jupiter"),
    E("Education yog strong hai?", "general_education", r"education|4th|5th|9th|Mercury|Jupiter"),
    E("School life achhi rahegi?", "general_education", r"education|4th|school|Mercury|Jupiter"),
    E("College life kaisi hogi?", "general_education", r"education|4th|college|Mercury|Jupiter"),
    E("Learning journey kaisi rahegi?", "general_education", r"education|learning|4th|Mercury|Jupiter"),
    E("Vidya ke yog chart me?", "general_education", r"education|vidya|4th|Mercury|Jupiter"),
    E("Shiksha ke chances strong?", "general_education", r"education|shiksha|4th|Mercury|Jupiter"),
    E("Hostel life padhai ke saath?", "general_education", r"education|hostel|4th|Mercury|Jupiter"),
    E("Library aur study environment?", "general_education", r"education|study|4th|Mercury|Jupiter"),
    E("Assignment aur project success?", "general_education", r"education|project|4th|Mercury|Jupiter"),
    E("Homework complete kar paunga?", "general_education", r"education|homework|4th|Mercury|Jupiter"),
    E("Classroom me performance?", "general_education", r"education|class|4th|Mercury|Jupiter"),
    E("Lecture samajh aa jayenge?", "general_education", r"education|lecture|4th|Mercury|Jupiter"),
    E("Syllabus complete ho payega?", "general_education", r"education|syllabus|4th|Mercury|Jupiter"),
    # ── negative: timing (should NOT be education static) ──
    TIMING("Exam kab clear hoga?"),
    TIMING("Result kab aayega?"),
    TIMING("Admission kab milegi?"),
    TIMING("Degree kab complete hogi?"),
    TIMING("NEET exam kab hoga?"),
    TIMING("Graduation kab hogi?"),
    TIMING("College admission kab confirm hogi?"),
    TIMING("Scholarship kab milegi?"),
    TIMING("Padhai kab start karun muhurat?"),
    TIMING("Board exam date kya hai chart se?"),
    # ── negative: govt/career exams ──
    CAREER("UPSC exam clear ho jayega kya?", "career_milestones"),
    CAREER("IAS banne ke liye exam pass?", "career_milestones"),
    CAREER("SSC CGL clear ho jayega?", "career_milestones"),
    CAREER("Bank exam PO clear hoga?", "career_milestones"),
    CAREER("Railway exam pass ho jayega?", "career_milestones"),
    CAREER("Sarkari exam clear kar paunga?", "career_milestones"),
    CAREER("Government exam selection hogi?", "career_milestones"),
    CAREER("PCS exam clear ho jayega?", "career_milestones"),
    CAREER("NDA exam pass ho jayega?", "career_milestones"),
    CAREER("Career ke liye kaunsa course choose karun?", "education_career"),
    CAREER("Job ke liye kaunsi padhai best?", "education_career"),
    CAREER("Naukri ke liye kaunsa degree?", "education_career"),
    # ── negative: off-topic ──
    OFF("Love marriage hogi ya arrange?"),
    OFF("Health theek rahegi?"),
    OFF("Paisa kamayenge kitna?"),
    OFF("Business start karun?"),
]


def _hit(text: str, rx: str) -> bool:
    if not rx:
        return True
    blob = (text or "").lower()
    return bool(re.search(rx, blob, re.I))


def main() -> int:
    import io
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    gaps: list[str] = []
    total = len(CASES)
    scope_ok = route_ok = engine_ok = ev_ok = 0

    print(f"EDUCATION FULL AUDIT — {total} cases\n" + "=" * 72)

    for c in CASES:
        q = c.q
        is_edu = is_education_static_question(q)
        is_career = is_career_static_question(q)
        arch = classify_education_archetype(q)
        detected = detect_education_archetype(q)

        if c.domain == "education":
            scope_hit = is_edu and not is_career
            route_hit = arch == c.engine and (detected == c.engine or arch == c.engine)
            if scope_hit:
                scope_ok += 1
            if route_hit:
                route_ok += 1

            try:
                res = run_education_static_engine(K, q, archetype=arch)
                eng_hit = res.archetype == c.engine
                if eng_hit:
                    engine_ok += 1
                ev_blob = " ".join(res.evidence or []) + " " + (res.verdict or "")
                ev_hit = len(res.evidence or []) >= c.min_evidence and _hit(ev_blob, c.focus_rx)
                if ev_hit:
                    ev_ok += 1
            except Exception as exc:
                eng_hit = ev_hit = False
                gaps.append(f"ENGINE_ERR | {q} | {exc}")

            ok = scope_hit and route_hit and eng_hit and ev_hit
            if not ok:
                gaps.append(
                    f"{c.engine} | {q[:55]} | scope={is_edu} career={is_career} "
                    f"arch={arch} det={detected} exp={c.engine} ev={ev_hit}"
                )
            tag = "OK" if ok else "GAP"
            print(f"  [{tag}] {q[:52]:<52} -> {arch}")

        elif c.domain == "timing":
            ok = not is_edu
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"TIMING | {q} | should NOT be education static")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} edu={is_edu}")

        elif c.domain == "career":
            ok = not is_edu and is_career
            if ok:
                car_arch = classify_career_archetype(q)
                ok = car_arch == c.engine
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"CAREER | {q} | edu={is_edu} career={is_career} exp={c.engine}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} edu={is_edu} career={is_career}")

        else:  # off
            ok = not is_edu
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"OFF | {q} | edu={is_edu} career={is_career}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} edu={is_edu}")

    print("\n" + "=" * 72)
    print(
        f"TOTAL={total} SCOPE={scope_ok}/{total} ROUTE={route_ok}/{total} "
        f"ENGINE={engine_ok}/{total} EVIDENCE={ev_ok}/{total} GAPS={len(gaps)}"
    )
    for g in gaps[:80]:
        print(f"  GAP: {g}")
    if len(gaps) > 80:
        print(f"  ... and {len(gaps) - 80} more")
    return 1 if gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())

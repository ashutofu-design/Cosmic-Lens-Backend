"""Education topic registry — scope keywords + archetype detection."""

from __future__ import annotations

import re

EDUCATION_ARCHETYPES = frozenset({
    "exam_success",
    "competitive_exam",
    "higher_studies",
    "study_field",
    "specialization_path",
    "admission",
    "scholarship",
    "degree_completion",
    "marks_performance",
    "study_focus",
    "learning_ability",
    "coaching_support",
    "education_obstacles",
    "vocational_diploma",
    "general_education",
})

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|when\s+will|kis\s+(saal|year|mahine|month)|"
    r"\d{4}\s+me|dasha|antardasha|mahadasha|transit|gochar|muhurat|timing|"
    r"exam\s+(kab|date|when)|result\s+(kab|when)|admission\s+(kab|when)|"
    r"degree\s+(kab|when)|graduation\s+(kab|when)"
    r")\b"
)

# Govt / competitive career exams stay on ask_career.career_milestones.
_GOVT_EXAM_RX = re.compile(
    r"(?ix)\b("
    r"upsc|ias|ips|ssc|cgl|railway\s*exam|bank\s*exam|govt\s*exam|"
    r"government\s*exam|civil\s*service|pcs|nda|cds|"
    r"sarkari\s*exam|public\s*service\s*commission|state\s*psc"
    r")\b"
)

_CAREER_LINK_RX = re.compile(
    r"(?ix)\b("
    r"career|naukri|job|business|profession|kaam|office|promotion|"
    r"salary|entrepreneur|govt|government|sarkari|employment|"
    r"placement\s*package|campus\s*placement"
    r")\b"
)

_EDU_CORE_RX = re.compile(
    r"(?ix)\b("
    r"padhai|padhayi|vidya|shiksha|education|study|studies|learning|learner|"
    r"school|college|university|institute|academy|campus|"
    r"exam|exams|test|quiz|result|degree|diploma|graduat\w*|"
    r"class|course|subject|syllabus|curriculum|semester|session|"
    r"admission|enrol(?:l)?ment|enroll|seat|scholarship|stipend|"
    r"board|cbse|icse|state\s*board|matric|intermediate|"
    r"marks|mark|percentage|percent|grade|gpa|cgpa|rank|topper|"
    r"backlog|back\s*year|drop\s*out|gap\s*year|"
    r"stream|pcm|pcb|pcmb|"
    r"tuition|coaching|tutor|mentor|teacher|professor|"
    r"homework|assignment|project|thesis|dissertation|"
    r"library|lecture|classroom|hostel|"
    r"pariksha|pariksh|imtihaan|admit\s*card|hall\s*ticket|"
    r"10th|12th|tenth|twelfth|plus\s*two|plus\s*2|"
    r"b\.?a\.?|b\.?s\.?c|b\.?com|b\.?tech|b\.?e\.?|m\.?a\.?|m\.?s\.?|m\.?tech|"
    r"llb|mbbs|bds|b\.?pharm|b\.?ed|m\.?ed|"
    r"neet|jee|cat|gate|clat|gmat|gre|sat|toefl|ielts|"
    r"iti|polytechnic|vocational|certificate\s*course|"
    r"memory|buddhi|intellect|concentration|focus|"
    r"science\s*stream|commerce\s*stream|arts\s*stream|humanities|"
    r"engineering\s*line|medical\s*line|law\s*line|ca\s*line|"
    r"research|phd|doctorate|post[\s-]?grad|pg\s+|pg\s+course"
    r")\b"
)

_HIGHER_STUD_RX = re.compile(
    r"(?ix)\b("
    r"post\s*graduation|post\s*grad(?:uation)?|"
    r"higher\s+stud(y|ies)|masters|master'?s|post[\s-]?grad|pg\s+course|"
    r"phd|ph\.?d\.?|doctorate|research\s+(?:scholar|degree|field)|"
    r"dissertation|thesis\s+work|"
    r"videsh\s+(shiksha|padhai|study|me\s+padhai|university|college)|"
    r"videsh\s+me\s+(?:padhai|university|college|shiksha)|"
    r"foreign\s+(stud(y|ies)|university|college|degree)|"
    r"study\s+abroad|abroad\s+stud(y|ies)|overseas\s+stud(y|ies)|"
    r"university\s+abroad|foreign\s+degree|"
    r"gre|gmat|toefl|ielts|student\s+visa|study\s+visa"
    r")\b"
)

_COMPETITIVE_EXAM_RX = re.compile(
    r"(?ix)\b("
    r"neet|jee|jee\s*main|jee\s*advanced|cat\s*exam|gate\s*exam|clat|"
    r"gmat|gre|sat|cmat|mat|xat|snap|nmat|"
    r"board\s*exam|10th\s*board|12th\s*board|cbse\s*board|icse\s*board|"
    r"state\s*board|matric\s*board|intermediate\s*board|"
    r"entrance\s*exam|entrance\s*test|competitive\s*test|competitive\s*exam|"
    r"term\s*exam.{0,20}competitive|competitive.{0,20}term\s*exam|competitive\s*level|"
    r"iit\s*entrance|medical\s*entrance|law\s*entrance"
    r")\b"
)

_EXAM_SUCCESS_RX = re.compile(
    r"(?ix)\b("
    r"exam\s+(clear|pass|crack|fail|top)|"
    r"pariksha\s+(pass|clear)|pariksh\s+(pass|clear)|imtihaan\s+(pass|clear|ho)|"
    r"परीक्षा.{0,15}(?:पास|साफ)|(?:पास|साफ).{0,15}परीक्षा|"
    r"pass\s+(hog[aei]|ja(?:y|aye)ga|kar\s*pa(?:unga|ungi|oge|enge))|"
    r"clear\s+(hog[aei]|ho\s*ja(?:y|aye)ga|kar\s*pa(?:unga|ungi|oge|enge)|payegi|payega)|"
    r"crack\s+(hog[aei]|kar\s*pa(?:unga|ungi|oge|enge))|"
    r"selection\s+(hog[aei]|milega|milegi)|"
    r"result\s+(achha|accha|badhiya|kharab|fail|pass)|"
    r"top\s+(kar\s*pa(?:unga|ungi|oge|enge)|a(?:unga|ayenge))|"
    r"rank\s+(a(?:egi|ayegi|ayega|ayenge)|milegi|milega)"
    r")\b"
)

_STUDY_FIELD_RX = re.compile(
    r"(?ix)\b("
    r"kaunsi\s+(line|field|stream|subject|branch|course)|"
    r"which\s+(field|stream|subject|course|branch)|"
    r"course\s+choose|stream\s+choose|subject\s+choose|branch\s+choose|"
    r"stream\s+(?:lena|le\s*na|select|chun)|"
    r"kya\s+padh(?:u|na|un)|what\s+should\s+i\s+study|"
    r"best\s+field\s+for\s+study|study\s+field|right\s+stream|"
    r"commerce\s+ya\s+science|science\s+ya\s+commerce|arts\s+ya\s+science|"
    r"science\s*stream|commerce\s*stream|arts\s*stream|humanities\s*stream|"
    r"pcm|pcb|pcmb|humanities\s+ya\s+science"
    r")\b"
)

_SPECIALIZATION_RX = re.compile(
    r"(?ix)\b("
    r"medical\s*line|doctor\s*ban(?:ne|na)|mbbs\s*line|"
    r"engineering\s*line|engineer\s*ban(?:ne|na)|"
    r"law\s*line|lawyer\s*ban(?:ne|na)|llb\s*line|"
    r"ca\s*line|chartered\s*account|cs\s*line|"
    r"teaching\s*line|teacher\s*ban(?:ne|na)|"
    r"architecture\s*line|design\s*line|"
    r"science\s*line|commerce\s*line|arts\s*line"
    r")\b"
)

_ADMISSION_RX = re.compile(
    r"(?ix)\b("
    r"admission|admit|enrol(?:l)?ment|enroll|seat|"
    r"college\s+mil(?:e|ega|egi)|university\s+mil(?:e|ega|egi)|"
    r"college\s+mil\s+pa(?:y|)ega|university\s+mil\s+pa(?:y|)ega|"
    r"college\s+lag(?:e|ega|egi)|institute\s+mil(?:e|ega|egi)|"
    r"admission\s+(?:milega|milegi|hoga|hogi|possible|confirm|reject)|"
    r"seat\s+(?:milega|milegi|confirm)|waitlist|merit\s*list"
    r")\b"
)

_SCHOLARSHIP_RX = re.compile(
    r"(?ix)\b("
    r"scholarship|stipend|financial\s*aid|fee\s*waiver|"
    r"merit\s*scholarship|education\s*loan\s*for\s*study|"
    r"free\s*education|funded\s*study|sponsorship|"
    r"vidyalakshmi|scholarship\s+(?:milega|milegi|hoga|possible)"
    r")\b"
)

_DEGREE_RX = re.compile(
    r"(?ix)\b("
    r"degree\s+(?:complete|complet|completion|milegi|milega|hogi|hoga|nahi)|"
    r"completion\s+ke\s+chances|"
    r"graduat(?:e|ion)|graduate\s+(?:ban|ho)|pass\s*out|"
    r"final\s*year\s+(?:clear|pass|complete)|"
    r"college\s+(?:complete|khatam|finish)|"
    r"drop\s*out|padhai\s+chhod|study\s+leave|"
    r"degree\s+poori|graduation\s+ho\s*ja"
    r")\b"
)

_MARKS_RX = re.compile(
    r"(?ix)\b("
    r"marks|mark|percentage|percent|grade|gpa|cgpa|"
    r"topper|first\s*division|second\s*division|distinction|"
    r"kitne\s+(?:marks|percent)|how\s+many\s+marks|"
    r"good\s+marks|bad\s+marks|low\s+marks|high\s+marks|"
    r"rank\s+in\s+(?:class|college|school)|merit\s+position"
    r")\b"
)

_STUDY_FOCUS_RX = re.compile(
    r"(?ix)(?:"
    r"\bmann?\s+nahi\s+lag|\bconcentration\b|\bstudy\s+focus\b|\bdistract|\bdistraction\b|"
    r"\bpadhai\s+me\s+mann?|\bmind\s+not\s+in\s+study\b|"
    r"\blazy\s+in\s+study\b|\bprocrastinat|\bmotivation\s+in\s+study\b|"
    r"\bpadhai\s+ka\s+man\b|\bstudy\s+habit\b|\bstudy\s+discipline\b|"
    r"\bpadhai\s+se\s+bore\b|\bstudy\s+boredom\b|\battendance\s+problem\b|"
    r"\bmotivation\s+padhai\s+me\b|\bpadhai\s+me\s+motivation\b"
    r")"
)

_LEARNING_ABILITY_RX = re.compile(
    r"(?ix)\b("
    r"buddhi|intellect|intelligence|smart\s+in\s+study|sharp\s+mind|"
    r"memory|yaad|retention|recall|"
    r"weak\s+in\s+(?:maths|math|english|science|subject)|"
    r"(?:maths|math|english|science|physics|chemistry|biology|hindi)\s+me\s+weak|"
    r"(?:science|maths|math|english|hindi|physics|chemistry|biology)\s+subject\s+weak|"
    r"subject\s+weak|weak\s+hoon\s+kya\s+karun|"
    r"slow\s+learner|learning\s+disability|dyslexia|"
    r"padhai\s+me\s+dimaag|study\s+ability|grasping\s+power|"
    r"analytical|logical\s+mind|creative\s+mind"
    r")\b"
)

_COACHING_RX = re.compile(
    r"(?ix)\b("
    r"coaching|tuition|tutor|mentor|"
    r"coaching\s+(?:sahi|best|join|karu)|"
    r"tuition\s+(?:leni|chahiye|sahi)|"
    r"iit\s*coaching|neet\s*coaching|"
    r"online\s*course|edtech|byju|unacademy|"
    r"self\s*study\s+ya\s+coaching"
    r")\b"
)

_OBSTACLES_RX = re.compile(
    r"(?ix)\b("
    r"backlog|back\s*year|gap\s*year|drop\s*year|"
    r"padhai\s+(?:ruki|ruka|atki|delay|late)|study\s+delay|"
    r"education\s+obstacle|padhai\s+me\s+problem|study\s+problem|"
    r"fail\s+(?:ho\s*gaya|year|semester)|supplementary|reappear|"
    r"compartment|atkt|kt|"
    r"padhai\s+chhod\s*di|study\s+break|"
    r"degree\s+delay|graduation\s+delay"
    r")\b"
)

_VOCATIONAL_RX = re.compile(
    r"(?ix)\b("
    r"iti|polytechnic|vocational|diploma\s+course|"
    r"certificate\s+course|skill\s+course|trade\s+course|"
    r"technical\s+diploma|diploma\s+after\s+10th|"
    r"short\s*term\s*course|certification\s+program"
    r")\b"
)


def is_career_linked_education(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return False
    if _GOVT_EXAM_RX.search(q):
        return True
    if _CAREER_LINK_RX.search(q) and not _EDU_CORE_RX.search(q):
        return True
    if re.search(
        r"(?ix)\bnaukri\s+ke\s+liye\b.{0,35}\b(degree|course|padhai|field|line|study)\b",
        q,
    ):
        return True
    if re.search(
        r"(?ix)\b(career|naukri|job)\b.{0,40}\b(course|field|line|study|padhai|degree)\b",
        q,
    ):
        return True
    if re.search(
        r"(?ix)\b(course|field|line|study|padhai|degree)\b.{0,40}\b(career|naukri|job)\b",
        q,
    ):
        return True
    return False


def is_education_static_question(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q or _TIMING_RX.search(q):
        return False
    if _GOVT_EXAM_RX.search(q):
        return False
    if is_career_linked_education(q):
        return False
    return detect_education_archetype(q) is not None


def detect_education_archetype(question: str) -> str | None:
    q = (question or "").strip().lower()
    if not q:
        return None

    if re.search(r"[\u0900-\u097F]", q) and re.search(r"परीक्षा", q) and re.search(r"पास", q):
        return "exam_success"

    # Funding before generic higher-study (scholarship + masters abroad).
    if _SCHOLARSHIP_RX.search(q):
        return "scholarship"
    if _HIGHER_STUD_RX.search(q):
        return "higher_studies"
    if _VOCATIONAL_RX.search(q):
        return "vocational_diploma"
    if _STUDY_FOCUS_RX.search(q):
        return "study_focus"
    if _OBSTACLES_RX.search(q):
        return "education_obstacles"
    if _COACHING_RX.search(q):
        return "coaching_support"
    # Seat/admission before named exam tokens (NEET/JEE ke baad admission).
    if _ADMISSION_RX.search(q):
        return "admission"
    if re.search(r"(?ix)\bcompetitive\b", q) and re.search(r"(?ix)\b(exam|test|level)\b", q):
        return "competitive_exam"
    if _COMPETITIVE_EXAM_RX.search(q):
        return "competitive_exam"
    if _EXAM_SUCCESS_RX.search(q):
        return "exam_success"
    if _DEGREE_RX.search(q):
        return "degree_completion"
    if _MARKS_RX.search(q):
        return "marks_performance"
    if _LEARNING_ABILITY_RX.search(q):
        return "learning_ability"
    if _SPECIALIZATION_RX.search(q):
        return "specialization_path"
    if _STUDY_FIELD_RX.search(q):
        return "study_field"
    if re.search(r"(?ix)\b(exam|exams|test|result|selection)\b", q):
        return "exam_success"
    if _EDU_CORE_RX.search(q) or _HIGHER_STUD_RX.search(q):
        return "general_education"
    return None

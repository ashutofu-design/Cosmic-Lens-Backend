from __future__ import annotations



import re



from .sector_registry import (

    CREATIVITY_RX,

    GOVT_EXAM_RX,

    INTERVIEW_RX,

    JOB_CHANGE_RX,

    PROMOTION_RX,

    SIDE_HUSTLE_RX,

    VOCATIONAL_RX,

    WHICH_BUSINESS_RX,

    build_career_core_pattern,

    detect_sector,

    is_govt_exam_milestone_question,

    is_govt_job_question,

)

from .job_registry import detect_job_archetype
from .foundation_personality import classify_foundation_personality, is_foundation_scope



_TIMING_RX = re.compile(

    r"(?ix)\b("

    r"kab|kab\s+tak|when|when\s+will|kis\s+(saal|year|mahine|month)|"

    r"\d{4}\s+me|dasha|antardasha|mahadasha|transit|gochar|muhurat|timing"

    r")\b"

)



_CAREER_CORE = build_career_core_pattern()



_SPOUSE_CAREER_RX = re.compile(

    r"(?ix)\b("

    r"(spouse|partner|wife|husband|pati|patni)\b.{0,30}\b(support|saath\s*deg)|"

    r"(spouse|partner|wife|husband|pati|patni)\b.{0,25}\b(profession|job|kaam|career)"

    r")\b"

)





def is_career_static_question(question: str) -> bool:

    q = (question or "").strip().lower()

    if not q or _TIMING_RX.search(q):

        return False

    if re.search(
        r"(?ix)\b(stock|stocks|share[\s-]*market|nifty|sensex|intraday|"
        r"trading|trader|mutual\s*fund|sip|nse|bse|crypto|portfolio)\b",
        q,
    ):
        return False

    try:
        from ask_finance.routing import finance_overrides_career  # type: ignore

        if finance_overrides_career(q):
            return False
    except Exception:
        pass

    if _SPOUSE_CAREER_RX.search(q):

        return False

    if is_foundation_scope(q):

        return True

    if re.search(
        r"(?ix)\b(employee\s+mindset|entrepreneur\s+mindset)\b",
        q,
    ):
        return True

    if _CAREER_CORE.search(q):

        return True

    if CREATIVITY_RX.search(q) or VOCATIONAL_RX.search(q):

        return True

    if detect_sector(q):

        return True

    if re.search(r"(?ix)\b(kaunsi\s*(field|line|industry)|mera\s*flirting)\b", q):

        return "flirting" not in q

    return False





def classify_career_archetype(question: str) -> str:

    q = (question or "").strip().lower()

    if not q:

        return "general_career"



    if WHICH_BUSINESS_RX.search(q):

        return "sector_fit"



    found = classify_foundation_personality(q)

    if found:

        return found



    if CREATIVITY_RX.search(q):

        return "creativity_innovation"



    if VOCATIONAL_RX.search(q):

        return "vocational_trade"



    if PROMOTION_RX.search(q):

        return "career_milestones"

    if INTERVIEW_RX.search(q):

        return "career_milestones"

    if JOB_CHANGE_RX.search(q):

        return "career_milestones"

    if GOVT_EXAM_RX.search(q) and is_govt_exam_milestone_question(q):

        return "career_milestones"

    if SIDE_HUSTLE_RX.search(q):

        return "career_milestones"



    if re.search(
        r"(?ix)\b(employee\s+mindset|entrepreneur\s+mindset)\b",
        q,
    ) or re.search(

        r"(?ix)\b(job\s*vs\s*business|job\s+better|naukri\s+ya\s+business|"

        r"employee\s+type|entrepreneur\s+type|employee\s+mindset|entrepreneur\s+mindset|"

        r"salary\s+karu\s+ya|job\s+karu\s+ya|naukri\s+ya\s*dhandha|"

        r"job\s+ya\s+business|business\s+ya\s+job|naukri\s+better|job\s+better)\b",

        q,

    ) or re.search(r"(?ix)\b(job|naukri).{0,25}\b(business|dhandha)\b", q) or re.search(

        r"(?ix)\b(business|dhandha).{0,25}\b(job|naukri)\b", q

    ) or (

        re.search(r"(?ix)\bbusiness\s+better\b", q)

        and not re.search(r"(?ix)\b(solo|partnership|family|online|trading)\s+business\b", q)

    ):

        return "job_vs_business"



    if is_govt_job_question(q):

        return "govt_job"



    job_arch = detect_job_archetype(q)

    if job_arch:

        return job_arch



    if re.search(

        r"(?ix)\b(startup|start\s*(up|apna\s*business)|partnership\s*(business|dhandha)|solo\s*business|"

        r"family\s*business|online\s*business|trading\s*business|consulting\s*business|"

        r"manufacturing|import[\s-]?export|self[\s-]?employment|apna\s*dhandha|"

        r"business\s*start|startup\s*founder|apna\s*business|trading|trader|share\s*trading|"

        r"franchise|dropship|e[\s-]?commerce|amazon|flipkart)\b",

        q,

    ):

        return "entrepreneurship"



    if re.search(

        r"(?ix)\b(obstacle|delay|setback|problem.*career|career.*problem|ruka|atka|"

        r"career\s*me\s*problem|badha|career\s*obstacles?|career\s*delay)\b",

        q,

    ):

        return "career_obstacles"



    if re.search(r"(?ix)\b(retirement|legacy|late\s*career|budhape\s*me\s*kaam)\b", q):

        return "retirement_legacy"



    if re.search(

        r"(?ix)\b(study|education|exam|degree|college|university|padhai|course\s*choose|"

        r"higher\s*stud|studies|career\s*course)\b",

        q,

    ) and not GOVT_EXAM_RX.search(q):

        return "education_career"



    if re.search(

        r"(?ix)\b(foreign\s*(country|job|career|work)|abroad|videsh|settle\s*abroad|"

        r"foreign\s*country\s*me\s*kaam)\b",

        q,

    ):

        return "foreign_career"



    if re.search(

        r"(?ix)\b(boss|colleagues?|coworker|team\s*mate|job\s*satisfaction|office\s*politics|"

        r"workplace\s*relation|boss\s*se\s*relation)\b",

        q,

    ):

        return "workplace_relations"



    if re.search(

        r"(?ix)\b(strength|weakness|skills?|develop|talents?|seekhni|seekhna|skill\s*develop|"

        r"communication\s*improve|technical\s*expertise|management\s*skills?|"

        r"public\s*speaking|sales\s*skills?|foreign\s*language|language\s*seekh|"

        r"naturally\s*strong|natural\s*talents?|biggest\s*strength|biggest\s*weakness)\b",

        q,

    ):

        return "strengths_skills"



    if re.search(

        r"(?ix)\b(leadership\s*quality|team\s*handle|independent\s*work|pressure\s*handle|"

        r"risk[\s-]?tak\w*|disciplin\w*|strategic\s*think\w*|public\s*dealing|network\w*|negotiat\w*|"

        r"leadership\s*role\s*ke\s*liye|main\s*leadership|meri\s+.+\s+quality\s+kaisi)\b",

        q,

    ) or re.search(

        r"(?ix)\b(kya\s+main\s+(team|pressure|risk|disciplin|strategic|network|negotiat))",

        q,

    ):

        return "career_traits"



    if re.search(

        r"(?ix)\b(paisa\s*kama\w*|wealth\s*creation|high[\s-]?income|passive\s*income|"

        r"multiple\s*income|commission[\s-]?based|freelanc\w*|salary[\s-]?based|"

        r"fixed\s*salary|investment\w*|entrepreneur\w*.*paisa|business\s*se\s*zyada\s*paisa|"

        r"earn\s*money|zyada\s*paisa)\b",

        q,

    ):

        return "income_wealth"



    if detect_sector(q):

        return "sector_fit"



    if re.search(

        r"(?ix)\b(remote\s*work|work\s*from\s*home|wfh|corporate|public\s*sector|"

        r"private\s*sector|frequent\s*travel|multinational|mnc|global\s*company|"

        r"employee\s*type|work\s*environment)\b",

        q,

    ):

        return "work_environment"



    if re.search(r"(?ix)\b(fame|recognition|reputation|naam\s*chalega|popular)\b", q):

        return "fame_recognition"



    if re.search(r"(?ix)\b(content\s*creation|innovation|innovative|creative\s*field)\b", q):

        return "creativity_innovation"



    if _CAREER_CORE.search(q):

        return "general_career"



    return "general_career"


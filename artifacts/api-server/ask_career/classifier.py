from __future__ import annotations

import re

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|when\s+will|kis\s+(saal|year|mahine|month)|"
    r"\d{4}\s+me|dasha|antardasha|mahadasha|transit|gochar|muhurat|timing"
    r")\b"
)

_CAREER_CORE = re.compile(
    r"(?ix)\b("
    r"career|naukri|job|business|profession|kaam|office|promotion|salary|"
    r"entrepreneur|startup|freelanc\w*|corporate|govt|government|sarkari|dhandha|"
    r"leadership|skills?|workplace|boss|colleagues?|industry|fields?|talents?|"
    r"employee|self[\s-]?employment|consulting|teaching|medical|law|finance|"
    r"technical|management|sales|marketing|research|real\s*estate|trading|"
    r"paisa\s*kama\w*|paisa|wealth|income|abroad|foreign|videsh|fame|recognition|"
    r"creative|content|retirement|legacy|stud(?:y|ies)|padhai|exam|degree|college|"
    r"remote|mnc|multinational|ngo|politics|media|manufacturing|"
    r"import[\s-]?export|network\w*|negotiat\w*|pressure|risk|disciplin\w*|"
    r"strategic|weakness|strength|suitable|suit\s+kare|suit\s+kar|"
    r"private\s*sector|public\s*sector|team|independent|communication|"
    r"public\s*dealing|public\s*speaking|"
    r"investment\w*|commission|higher\s*stud|colleague"
    r")\b"
)

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
    if _SPOUSE_CAREER_RX.search(q):
        return False
    if _CAREER_CORE.search(q):
        return True
    if re.search(
        r"(?ix)\b(kaunsi\s*(field|line|industry)|mera\s*flirting)\b",
        q,
    ):
        return "flirting" not in q
    return False


def classify_career_archetype(question: str) -> str:
    q = (question or "").strip().lower()
    if not q:
        return "general_career"

    if re.search(
        r"(?ix)\b(job\s*vs\s*business|job\s+better|naukri\s+ya\s+business|"
        r"employee\s+type|entrepreneur\s+type|naukri\s+ya\s*dhandha|"
        r"job\s+ya\s+business)\b",
        q,
    ) or (
        re.search(r"(?ix)\bbusiness\s+better\b", q)
        and not re.search(r"(?ix)\b(solo|partnership|family|online|trading)\s+business\b", q)
    ):
        return "job_vs_business"

    if re.search(
        r"(?ix)\b(startup|start\s*(up|apna\s*business)|partnership\s*(business|dhandha)|solo\s*business|"
        r"family\s*business|online\s*business|trading\s*business|consulting\s*business|"
        r"manufacturing|import[\s-]?export|self[\s-]?employment|apna\s*dhandha|"
        r"business\s*start|startup\s*founder|apna\s*business|trading|trader|share\s*trading)\b",
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
    ):
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

    if re.search(
        r"(?ix)\b(government|govt|sarkari|private\s*sector|private\s*company|company\s*job|"
        r"it\b|software|medical|doctor|"
        r"law|finance\s*sector|teaching|creative|technical|engineering|management\s*role|"
        r"sales|marketing|research|real\s*estate|consulting\s*field|media|ngo|politics|"
        r"industry|kaunsi\s*(field|line|industry)|profession\s*suit|field\s*suit|line\s*suit)\b",
        q,
    ):
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

    if re.search(r"(?ix)\b(content\s*creation|innovation|innovative)\b", q):
        return "creativity_innovation"

    if _CAREER_CORE.search(q):
        return "general_career"

    return "general_career"

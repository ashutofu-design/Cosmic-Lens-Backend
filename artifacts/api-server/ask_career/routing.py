"""Career archetype routing — question patterns beat LLM mis-routes."""

from __future__ import annotations



import re



from .foundation_personality import classify_foundation_personality
from .job_registry import JOB_ENGINE_ARCHETYPES, detect_job_archetype, is_dedicated_job_question
from .sector_registry import (
    CREATIVITY_RX,
    GOVT_EXAM_RX,
    INTERVIEW_RX,
    JOB_CHANGE_RX,
    PROMOTION_RX,
    SIDE_HUSTLE_RX,
    VOCATIONAL_RX,
    WHICH_BUSINESS_RX,
    detect_sector,
    is_govt_exam_milestone_question,
    is_govt_job_question,
)



CAREER_ARCHETYPES = frozenset({

    "job_vs_business",

    "sector_fit",

    "career_traits",

    "strengths_skills",

    "entrepreneurship",

    "work_environment",

    "income_wealth",

    "foreign_career",

    "workplace_relations",

    "fame_recognition",

    "creativity_innovation",

    "career_obstacles",

    "education_career",

    "retirement_legacy",

    "career_milestones",

    "vocational_trade",

    "govt_job",

    *JOB_ENGINE_ARCHETYPES,

    "general_career",

})



_JOB_VS_BIZ_RX = re.compile(

    r"(?ix)\b("

    r"job\s*vs\s*business|job\s+better|naukri\s+ya\s+business|"

    r"employee\s+type|entrepreneur\s+type|naukri\s+ya\s*dhandha|"

    r"job\s+ya\s+business|business\s+ya\s+job|"

    r"job\s+karu\s+ya\s+business|naukri\s+karu\s+ya|"

    r"employment\s+ya\s+business|naukri\s+better|job\s+better"

    r")\b"

)



_WHICH_BIZ_INTERP_RX = re.compile(

    r"(?ix)\b(which|what|best|suitable|ideal)\s+business\b"

    r"|user wants to know which business"

    r"|which business is best"

    r"|what business to start"

)



_MILESTONE_INTERP_RX = re.compile(

    r"(?ix)(promotion|interview|job change|govt exam|government exam|side hustle|part time)"

)





def is_job_vs_business_question(question: str) -> bool:

    q = (question or "").strip().lower()

    if not q:

        return False

    if re.search(r"(?ix)\b(job|naukri).{0,25}\b(business|dhandha)\b", q):

        return True

    if re.search(r"(?ix)\b(business|dhandha).{0,25}\b(job|naukri)\b", q):

        return True

    if _JOB_VS_BIZ_RX.search(q):

        return True

    return bool(

        re.search(r"(?ix)\bbusiness\s+better\b", q)

        and not re.search(r"(?ix)\b(solo|partnership|family|online|trading)\s+business\b", q)

        and not WHICH_BUSINESS_RX.search(q)

        and not detect_sector(q)

    )





def is_which_business_question(question: str, interpretation: str = "") -> bool:

    q = (question or "").strip()

    interp = (interpretation or "").strip()

    if is_job_vs_business_question(q):

        return False

    if WHICH_BUSINESS_RX.search(q):

        return True

    if _WHICH_BIZ_INTERP_RX.search(interp):

        return True

    return False





def is_creativity_career_question(question: str, interpretation: str = "") -> bool:

    q = (question or "").strip()

    interp = (interpretation or "").strip()

    if CREATIVITY_RX.search(q):

        return True

    return bool(re.search(r"(?ix)\b(youtuber|youtube|content\s*creat|actor|singer|photographer|gamer)", interp))





def is_vocational_question(question: str, interpretation: str = "") -> bool:

    q = (question or "").strip()

    interp = (interpretation or "").strip()

    if VOCATIONAL_RX.search(q):

        return True

    return bool(re.search(r"(?ix)\b(electrician|plumber|mechanic|vocational|skilled trade)", interp))





def is_milestone_question(question: str, interpretation: str = "") -> bool:

    q = (question or "").strip()

    interp = (interpretation or "").strip()

    if any(rx.search(q) for rx in (PROMOTION_RX, INTERVIEW_RX, JOB_CHANGE_RX, SIDE_HUSTLE_RX)):

        return True

    return is_govt_exam_milestone_question(q, interp)





def is_specific_sector_suitability_question(question: str, interpretation: str = "") -> bool:

    q = (question or "").strip()

    interp = (interpretation or "").strip()

    if is_job_vs_business_question(q) or is_which_business_question(q, interp):

        return False

    if is_creativity_career_question(q, interp):

        return True

    if is_vocational_question(q, interp):

        return True

    if is_milestone_question(q, interp):

        return True

    if is_dedicated_job_question(q, interp):

        return True

    return detect_sector(q) is not None





def _which_business_archetype(question: str) -> str:

    q = (question or "").strip().lower()

    if re.search(

        r"(?ix)\b(startup|partnership\s+business|solo\s+business|family\s+business|"

        r"online\s+business|trading\s+business|import[\s-]?export|franchise|e[\s-]?commerce)\b",

        q,

    ):

        return "entrepreneurship"

    return "sector_fit"





def resolve_career_archetype(

    question: str,

    *,

    llm_archetype: str | None = None,

    interpretation: str = "",

) -> tuple[str, str | None]:

    """Pick engine archetype. Question-kind patterns override LLM mis-routes."""

    from .classifier import classify_career_archetype



    rule = classify_career_archetype(question)

    llm = (llm_archetype or "").strip().lower() or None

    if llm and llm not in CAREER_ARCHETYPES:

        llm = None



    if is_which_business_question(question, interpretation):

        target = _which_business_archetype(question)

        if llm and llm != target:

            return target, f"which_business_over_{llm}"

        if rule != target and rule in ("general_career", "job_vs_business"):

            return target, "which_business_over_rule"

        return target, None



    if is_creativity_career_question(question, interpretation):

        if llm and llm != "creativity_innovation":

            return "creativity_innovation", f"creativity_over_{llm}"

        return "creativity_innovation", None if rule == "creativity_innovation" else "creativity_over_rule"



    if is_vocational_question(question, interpretation):

        if llm and llm != "vocational_trade":

            return "vocational_trade", f"vocational_over_{llm}"

        return "vocational_trade", None if rule == "vocational_trade" else "vocational_over_rule"



    try:
        from ask_career.timing_registry import is_career_timing_question

        if is_career_timing_question(
            question,
            {"domain": "career", "is_timing": True},
        ):
            return rule, "promotion_timing_not_static_milestone"
    except Exception:
        pass



    if is_milestone_question(question, interpretation):

        if llm and llm != "career_milestones":

            return "career_milestones", f"milestone_over_{llm}"

        return "career_milestones", None if rule == "career_milestones" else "milestone_over_rule"



    if is_govt_job_question(question, interpretation):

        if llm and llm != "govt_job":

            return "govt_job", f"govt_job_over_{llm}"

        return "govt_job", None if rule == "govt_job" else "govt_job_over_rule"



    found = classify_foundation_personality(question)

    if found:

        if llm and llm != found:

            return found, f"foundation_over_{llm}"

        return found, None if rule == found else "foundation_over_rule"



    job_arch = detect_job_archetype(question)

    if job_arch:

        if llm and llm != job_arch:

            return job_arch, f"{job_arch}_over_{llm}"

        return job_arch, None if rule == job_arch else f"{job_arch}_over_rule"



    if detect_sector(question) and not is_job_vs_business_question(question):

        if llm in ("job_vs_business", "general_career", "income_wealth"):

            return "sector_fit", f"sector_over_{llm}"

        if rule == "sector_fit" and llm and llm != "sector_fit":

            return "sector_fit", f"sector_rule_over_{llm}"



    if is_job_vs_business_question(question):

        return "job_vs_business", (

            f"job_vs_biz_over_{llm}" if llm and llm != "job_vs_business" else None

        )



    if llm:

        return llm, None



    return rule, None


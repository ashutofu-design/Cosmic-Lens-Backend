"""Career archetype routing — question patterns beat LLM mis-routes."""
from __future__ import annotations

import re

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
    "general_career",
})

_WHICH_BUSINESS_RX = re.compile(
    r"(?ix)\b("
    r"konsa\s+business|kaun\s*sa\s+business|kaunsi\s+business|konsi\s+business|"
    r"which\s+business|what\s+business|best\s+business|business\s+best|"
    r"business\s+type|business\s+line|business\s+field|business\s+choose|"
    r"business\s+me\s+(jau|jaau|javu|jao|jaana)|agar\s+business|"
    r"business\s+start\s+kar\w*\s+konsa|sapna\s+business|ideal\s+business|"
    r"suitable\s+business|business\s+suit|business\s+option"
    r")\b"
)

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
        and not _WHICH_BUSINESS_RX.search(q)
    )


def is_which_business_question(question: str, interpretation: str = "") -> bool:
    q = (question or "").strip()
    interp = (interpretation or "").strip()
    if is_job_vs_business_question(q):
        return False
    if _WHICH_BUSINESS_RX.search(q):
        return True
    if _WHICH_BIZ_INTERP_RX.search(interp):
        return True
    return False


def _which_business_archetype(question: str) -> str:
    q = (question or "").strip().lower()
    if re.search(
        r"(?ix)\b(startup|partnership\s+business|solo\s+business|family\s+business|"
        r"online\s+business|trading\s+business|import[\s-]?export)\b",
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

    if is_job_vs_business_question(question):
        return "job_vs_business", (
            f"job_vs_biz_over_{llm}" if llm and llm != "job_vs_business" else None
        )

    if llm:
        return llm, None

    return rule, None

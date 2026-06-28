"""Foreign travel + higher education timing — 5H/9H/12H WHEN questions."""
from __future__ import annotations

import re
from typing import Optional

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|when\s+will|kis\s+(?:specific\s+)?(?:date|week|saal|year|mahine|month)|"
    r"milega|milegi|hoga|hogi|honge|aayega|aayegi|banega|banegi|ban\s+raha|ban\s+rahi|"
    r"padega|padegi|paunga|paungi|jaunga|jaungi|jayega|jayegi|jayenge|"
    r"ban\s+raha|ban\s+rahi|mil\s+jayega|ho\s+jayega|ho\s+jaunga|"
    r"shuru\s+hoga|khatam|paltega|active|trigger|deliver|extend|improve|dikhayega|"
    r"sanction|clear\s+hoga|pass\s+hoga|lagenge|pahuchegi|delay|dikh\s+raha|"
    r"dasha|antardasha|transit|gochar|timing|muhurat|mahurat|mahina|turning\s+point"
    r")\b|"
    r"\bisi\s+saal\b|\bpehli\s+baar\b"
)

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"admission|college|university|degree|higher\s+stud|masters|phd|graduation|"
    r"post[\s-]?grad|scholarship|counseling|counselling|shortlist|merit|campus|"
    r"semester|padhai|study|course|stream|subject|concentration|dhyan|professor|"
    r"research|gap\s+year|college\s+change|hometown|doosre\s+state|"
    r"competitive\s+exam|exam\s+result|exam\s+anxiety|selection|cut[\s-]?off|rank|"
    r"attempt|coaching|taiyari|preparation|ielts|gmat|neet|iit|jee|"
    r"selection\s+list|final\s+list|"
    r"visa|passport|embassy|biometrics?|sponsor|spousal\s+visa|student\s+visa|"
    r"work\s+visa|business\s+visa|investor\s+visa|tourist\s+visa|immigration|"
    r"pr\b|green\s+card|permanent\s+residen|citizenship|h1b|work[\s-]?permit|"
    r"crs\s+score|priority\s+date|rfe|oath|decision\s+made|in\s+progress|"
    r"foreign\s+settlement|permanent\s+foreign|settle\s+abroad|settlement|"
    r"videsh|foreign|abroad|overseas|study\s+abroad|foreign\s+citizen|"
    r"double\s+transit|network|language\s+skill|settle\s+ho|wapas\s+aana|struggle|kismat|"
    r"medical\s+test|appointment|approved|renewal|passport|family\s*\(parents\)|province|"
    r"employer|company|bulana|deliver|shift\s+hona"
    r")\b"
)

_GOVT_JOB_EXAM_RX = re.compile(
    r"(?ix)\b("
    r"upsc|ssc|cgl|chsl|ibps|rrb|pcs|judicial|bank\s+po|govt\s+job|"
    r"government\s+job|sarkari\s+naukri|joining\s+letter"
    r")\b",
)

_CAREER_DEFER_RX = re.compile(
    r"(?ix)\b(campus\s+placement|sarkari\s+naukri|govt\s+job|government\s+job|"
    r"joining\s+letter|upsc|ssc|bank\s+po|ibps)\b",
)

_FINANCE_DEFER_RX = re.compile(
    r"(?ix)\b(education\s+loan|student\s+loan)\b",
)

_MARRIAGE_DEFER_RX = re.compile(
    r"(?ix)\b(shaadi|shadi|marriage)\b.{0,40}\b(citizen|videshi|foreigner)\b",
)

_HEALTH_DEFER_RX = re.compile(
    r"(?ix)\b(accident|health\s+issue|depression)\b",
)

_LITIGATION_DEFER_RX = re.compile(
    r"(?ix)\b(case|fir|court|legal|mukadma|zapt|seize|bail|jail|litigation|complaint)\b",
)

_STATIC_ONLY_RX = re.compile(
    r"(?ix)^(?!.*\b(kab|kab\s+tak|dasha|gochar|muhurat|mahurat|ban\s+raha)\b).*$",
)

_STUDY_ABROAD_RX = re.compile(
    r"(?ix)\b("
    r"study\s+abroad|abroad\s+stud(y|ies)|student\s+visa|study\s+visa|"
    r"university\s+abroad|college\s+abroad|foreign\s+(university|college|degree)|"
    r"videsh\s+(padhai|shiksha|university|college)|"
    r"ielts|gmat|gre|toefl|sat\b|scholarship|masters|phd|post[\s-]?grad"
    r")\b",
)

# Pure travel / settlement — travel engine, not foreign-education.
_PURE_TRAVEL_DEFER_RX = re.compile(
    r"(?ix)\b("
    r"videsh\s+kab|foreign\s+kab|abroad\s+kab|overseas\s+kab|"
    r"visa\s+kab|passport\s+kab|pr\s+kab|green\s+card\s+kab|"
    r"immigration\s+kab|citizenship\s+kab|"
    r"(?:foreign|abroad)\s+settlement\s+kab|abroad\s+shift\s+kab|"
    r"videsh\s+(?:me\s+)?(?:ja|jaa|bas)|settle\s+(?:abroad|videsh|foreign)"
    r")\b",
)

# Long-form visa/PR/settlement/study phrasing stays on foreign_education.
_FOREIGN_EDU_ENRICHED_RX = re.compile(
    r"(?ix)\b("
    r"permanent\s+(?:foreign\s+)?(?:residen|settlement)|"
    r"foreign\s+visa|student\s+visa|study\s+visa|"
    r"green\s+card|permanent\s+residency|"
    r"higher\s+stud|university|college|degree|"
    r"competitive\s+exam|"
    r"approve|scholarship|ielts|gmat|gre|toefl|"
    r"(?:foreign|abroad|videsh|overseas).{0,24}(?:admission|exam|selection|visa|settlement)|"
    r"(?:admission|exam|selection|visa).{0,24}(?:foreign|abroad|videsh|overseas|university|college)"
    r")\b",
)

# Domestic exam/admission without abroad context → education engine.
_DOMESTIC_EDU_DEFER_RX = re.compile(
    r"(?ix)\b(exam\s+result|admission|board\s+exam|semester\s+result|marks\s+aay)\b",
)


def is_foreign_education_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if _CAREER_DEFER_RX.search(q) or _GOVT_JOB_EXAM_RX.search(q):
        if re.search(r"(?ix)\b(videsh|foreign|abroad|settlement)\b", q) and not re.search(
            r"(?ix)\b(joining\s+letter|upsc|ssc|cgl|ibps)\b", q
        ):
            pass
        else:
            return False
    if _FINANCE_DEFER_RX.search(q):
        return False
    if _MARRIAGE_DEFER_RX.search(q) and not re.search(
        r"(?ix)\b(pr\b|green\s+card|permanent\s+residen|residency|settlement|foreign|videsh)\b", q
    ):
        return False
    if _HEALTH_DEFER_RX.search(q):
        return False
    if _LITIGATION_DEFER_RX.search(q) and re.search(
        r"(?ix)\b(passport|visa|videsh|abroad|foreign)\b", q
    ):
        return False
    if _PURE_TRAVEL_DEFER_RX.search(q) and not _STUDY_ABROAD_RX.search(q):
        if not _FOREIGN_EDU_ENRICHED_RX.search(q):
            return False
    if _DOMESTIC_EDU_DEFER_RX.search(q) and not _FOREIGN_EDU_ENRICHED_RX.search(q):
        if not re.search(
            r"(?ix)\b(foreign|abroad|videsh|overseas|study\s+abroad|university|college|degree)\b",
            q,
        ):
            return False
    if isinstance(llm_intent, dict):
        if llm_intent.get("domain") in ("foreign_education", "travel", "education"):
            if llm_intent.get("is_timing") and _SCOPE_RX.search(q):
                return True
    if not _SCOPE_RX.search(q):
        return False
    if not _TIMING_RX.search(q):
        # Yoga / period phrasing without explicit kab
        if re.search(
            r"(?ix)\b(yoga|dasha[\s-]?period|antardasha|gochar|double\s+transit|"
            r"turning\s+point|safest.*period|confirmed\s+period|struggle|chamkegi)\b",
            q,
        ):
            return True
        return False
    return True


def classify_foreign_education_bucket(question: str) -> str:
    from event_timing.foreign_education.foreign_education_timing_v1 import (
        classify_foreign_education_bucket as _classify,
    )

    return _classify(question)

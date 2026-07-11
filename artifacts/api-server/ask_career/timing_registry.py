"""Career timing routing — job/promotion/change/transfer/govt-exam WHEN questions.

Mirrors ask_travel/travel_registry.py pattern. Used by openai_helper gates,
LLM intent fallback, and audit scripts.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

from ask_career.sector_registry import build_career_core_pattern

TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+hoga|kab\s+hogi|kab\s+milega|kab\s+milegi|"
    r"kab\s+lagega|kab\s+lagegi|kab\s+aayega|kab\s+aayegi|"
    r"kab\s+niklega|kab\s+niklegi|kab\s+banega|kab\s+banegi|kab\s+banunga|kab\s+banungi|"
    r"kis\s+(saal|year|mahine|month|samay|waqt|time)|"
    r"kitne\s+(saal|mahine|din)|kitna\s+time|time\s+lagega|lagne\s+me|"
    r"when|when\s+will|by\s+when|how\s+soon|how\s+long|"
    r"what\s+year|which\s+year|what\s+month|which\s+month|"
    r"\d{4}\s+me|dasha|antardasha|mahadasha|transit|gochar|muhurat|timing|"
    r"timeline|window|future\s+me"
    r")\b|"
    r"(?:कब|किस\s+साल|कितने\s+साल|कितना\s+समय)"
)

_CAREER_CORE = build_career_core_pattern()

# Milestone / event phrasing without explicit "kab" (tricky Hinglish)
_CAREER_EVENT_RX = re.compile(
    r"(?ix)\b("
    r"job\s+lagega|naukri\s+lagegi|naukri\s+milegi|job\s+milega|"
    r"promotion\s+(?:hoga|milega|milegi)|tarakki\s+(?:hogi|milegi)|"
    r"salary\s+(?:hike|badhegi|milegi)|hike\s+(?:milegi|hoga)|increment\s+(?:milega|hogi)|"
    r"appraisal\s+(?:hoga|milegi)|manager\s+ban|senior\s+role|"
    r"transfer\s+(?:hoga|hogi|milega)|tankhwah\s+badhegi|salary\s+badhegi|"
    r"company\s+(?:switch|change)|switch\s+(?:karu|karna|company|job)|"
    r"job\s+change|naukri\s+badlo|switch\s+job|"
    r"govt\s+job\s+(?:milega|lagega|hoga)|sarkari\s+naukri\s+(?:milegi|lagegi)|"
    r"upsc\s+clear|ssc\s+clear|exam\s+clear|selection\s+hoga|"
    r"campus\s+placement|placement\s+ke\s+zariye|"
    r"resign|istifa|notice\s+de|job\s+chod|naukri\s+chod|"
    r"interview\s+(?:clear|pass|hoga)|joining\s+(?:hogi|milegi)|"
    r"layoff|job\s+loss|recovery\s+(?:hogi|hoga)|notice\s+period|demotion|setback|"
    r"offer\s+letter|onboarding|probation|new\s+role|remote\s+job|"
    r"freelanc\w*\s+start|Railway\s+job|police\s+recruitment|defence\s+joining|"
    r"IBPS\s+PO|team\s+lead\s+role|senior\s+engineer|annual\s+appraisal|"
    r"second\s+job|part\s+time\s+kaam|business\s+start\s+after\s+job"
    r")\b"
)

_CAREER_TIMING_MILESTONE_RX = re.compile(
    r"(?ix)\b("
    r"promotion|tarakki|salary|hike|increment|appraisal|bonus|tankhwah|vetan|"
    r"job|naukri|kaam|career|transfer|posting|resign|istifa|"
    r"govt|sarkari|upsc|ssc|interview|joining|company|switch|manager|"
    r"engineer|developer|package|ctc|notice|chhod|"
    r"layoff|setback|recovery|demotion|offer|onboarding|probation|freelanc\w*|"
    r"new\s+role|remote|recruitment|railway|police|defence|ibps|appraisal|"
    r"increment|hike|engineer|lead\s+role|part\s+time|second\s+job"
    r")\b"
)

_SPOUSE_CAREER_RX = re.compile(
    r"(?ix)\b("
    r"(spouse|partner|wife|husband|pati|patni)\b.{0,30}\b(support|saath\s*deg)|"
    r"(spouse|partner|wife|husband|pati|patni)\b.{0,25}\b(profession|job|kaam|career)"
    r")\b"
)

_STOCK_OVERRIDE_RX = re.compile(
    r"(?ix)\b("
    r"nifty|sensex|share[\s-]*market|stock[\s-]*market|intraday|demat|broker|"
    r"fno|f&o|options?\s*trading|crypto|portfolio|mutual[\s-]*fund|\bsip\b|"
    r"nse|bse|trading\s*account|equity\s*trading|share\s*trading"
    r")\b"
)

_POLICE_JOB_RX = re.compile(
    r"(?ix)\b("
    r"police\s+(?:job|naukri|service|exam|recruitment|constable|si\b|inspector)|"
    r"ips\s+exam|ips\s+banna|police\s+me\s+join"
    r")\b"
)

_DEVANAGARI_CAREER_RX = re.compile(
    r"(?:नौकरी|काम|करियर|पेशा|प्रमोशन|पदोन्नति|तबादला|वेतन|सरकारी|नौकरी)"
)

_DEVANAGARI_TIMING_RX = re.compile(r"(?:कब|किस\s+साल|कितने\s+साल|कितना\s+समय|बाद)")

_PROMOTION_TIMING_FOLLOWUP_RX = re.compile(
    r"(?ix)(?:"
    r"\bke\s+baad\b.*\b(promotion|tarakki|naukri|job|career)\b|"
    r"\b(promotion|tarakki)\b.*\bke\s+baad\b|"
    r"\baur\s+koi\b.*\b(promotion|tarakki|mauka|window|chance)\b|"
    r"\bagar\b.{0,50}\b(nahi|na|nhi|not)\b|"
    r"\b(ho\s+sakta|ho\s+sakti|milega|milegi)\b.{0,30}\b(promotion|tarakki)\b|"
    r"\b(promotion|tarakki)\b.{0,30}\b(ho\s+sakta|ho\s+sakti|milega|milegi)\b"
    r")"
)

_AGE_IN_QUESTION_RX = re.compile(
    r"(?ix)\b("
    r"(\d{2,3})\s*(?:saal|years?|year\s*old|yrs?)\s*(?:ka|ki|ke|old|hun|hu|hoon|hun)?|"
    r"main\s+(\d{2,3})\s*(?:saal|years?)\s*(?:ka|ki|ke|old|hun|hu|hoon)?|"
    r"meri\s+age\s+(\d{2,3})|age\s+(\d{2,3})|"
    r"(\d{2,3})\s*saal\s*(?:ka|ki|ke)\s*(?:aadmi|aurat|person|hu|hun|hoon)"
    r")\b"
)

CAREER_TIMING_BUCKETS = frozenset({
    "govt_job", "promotion", "resignation", "transfer", "career_setback",
    "job_change", "career_field_choice", "general_career", "new_job_timing",
})

CAREER_QUESTION_RX = re.compile(
    r"(?ix)(?:\b("
    r"career|naukri|naukari|job|kaam|profession|office|promotion|tarakki|"
    r"salary|tankhwah|vetan|increment|appraisal|hike|bonus|"
    r"transfer|posting|tadadla|deputation|relocate|relocation|"
    r"resign|resignation|istifa|notice\s+period|quit\s+job|"
    r"govt|government|sarkari|saarkari|upsc|ssc|ibps|rrb|cgl|ias|ips|"
    r"competitive\s+exam|govt\s+exam|sarkari\s+exam|"
    r"interview|selection|recruiter|hr\s+round|joining|"
    r"job\s+change|switch|company\s+change|new\s+job|"
    r"manager|senior\s+role|lead\s+role|engineer|developer|package|ctc|"
    r"business\s+start|startup|apna\s+dhandha|entrepreneur|"
    r"layoff|fired|terminat|demotion|setback|recovery|job\s+loss|"
    r"employer|employee|corporate|mnc|freelanc\w*|"
    r"private\s+sector|public\s+sector|offer\s+letter|onboarding|probation|"
    r"notice|chhod|chhodu|chhodun|company|"
    r"नौकरी|काम|करियर|पेशा|प्रमोशन|तबादला|वेतन|सरकारी"
    r")\b|"
    r"\b(lagega|lagegi|milega|milegi|banega|banegi|banne)\b.{0,25}\b(job|naukri|kaam|promotion|transfer|manager|role)\b|"
    r"\b(job|naukri|kaam|promotion|transfer|manager|role)\b.{0,25}\b(lagega|lagegi|milega|milegi|banega|banegi|banne)\b"
    r")"
)


def _extract_dob_year(birth: Any, kundli: Any = None) -> Optional[int]:
    for src in (birth, kundli):
        if not isinstance(src, dict):
            continue
        for key in ("year", "birth_year", "birthYear"):
            v = src.get(key)
            if isinstance(v, int) and 1900 <= v <= datetime.now().year:
                return v
            if isinstance(v, str) and v.isdigit():
                y = int(v)
                if 1900 <= y <= datetime.now().year:
                    return y
        dob = src.get("dob") or src.get("date_of_birth") or src.get("birthDate")
        if isinstance(dob, str):
            m = re.search(r"(\d{4})", dob)
            if m:
                y = int(m.group(1))
                if 1900 <= y <= datetime.now().year:
                    return y
    return None


def compute_native_age(birth: Any = None, kundli: Any = None) -> Optional[int]:
    y = _extract_dob_year(birth, kundli)
    if y is None:
        return None
    now = datetime.now()
    return max(0, now.year - y)


def parse_age_from_question(question: str) -> Optional[int]:
    q = question or ""
    m = _AGE_IN_QUESTION_RX.search(q)
    if not m:
        return None
    for g in m.groups():
        if g and g.isdigit():
            age = int(g)
            if 10 <= age <= 99:
                return age
    return None


def resolve_user_age(
    question: str = "",
    birth: Any = None,
    kundli: Any = None,
) -> Optional[int]:
    q_age = parse_age_from_question(question)
    if q_age is not None:
        return q_age
    return compute_native_age(birth, kundli)


def career_scope_match(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return False
    if _SPOUSE_CAREER_RX.search(q):
        return False
    if _DEVANAGARI_CAREER_RX.search(q):
        return True
    if CAREER_QUESTION_RX.search(q):
        return True
    if _CAREER_EVENT_RX.search(q):
        return True
    return bool(_CAREER_CORE.search(q))


def should_defer_career_timing(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return True
    if _STOCK_OVERRIDE_RX.search(q):
        return True
    if _SPOUSE_CAREER_RX.search(q):
        return True
    try:
        from ask_education.education_registry import is_education_static_question  # type: ignore

        if re.search(r"(?ix)\b(study\s+abroad|abroad\s+stud|padhai\s+abroad|videsh\s+padhai)\b", q):
            return True
        if is_education_static_question(q) and re.search(
            r"(?ix)\b(study|padhai|exam|degree|college|university|admission)\b", q
        ) and not re.search(r"(?ix)\b(job|naukri|career|promotion|govt\s+job)\b", q):
            return True
    except Exception:
        pass
    try:
        from ask_education.timing_registry import is_education_timing_question  # type: ignore

        if is_education_timing_question(q) and not re.search(
            r"(?ix)\b(job|naukri|career|promotion|govt\s+job|interview|joining|"
            r"offer\s+letter|onboarding)\b",
            q,
        ):
            return True
    except Exception:
        pass
    try:
        from ask_travel.timing_registry import is_travel_timing_question  # type: ignore

        if is_travel_timing_question(q) and not re.search(
            r"(?ix)\b(job|naukri|career|promotion|office|salary|company|transfer|"
            r"posting|deputation|posting|employer|work\s+permit)\b",
            q,
        ):
            return True
    except Exception:
        pass
    try:
        from ask_finance.routing import finance_overrides_career  # type: ignore

        if finance_overrides_career(q):
            if TIMING_RX.search(q) and _CAREER_TIMING_MILESTONE_RX.search(q):
                return False
            return True
    except Exception:
        pass
    try:
        from ask_health.routing import health_overrides_career  # type: ignore

        if health_overrides_career(q):
            return True
    except Exception:
        pass
    if re.search(
        r"(?ix)\b(health|swasth|bimari|illness|disease|hospital|surgery|operat\w*|"
        r"blood\s*pressure|hypertension|heart|dil|bp)\b",
        q,
    ) and not re.search(r"(?ix)\b(job|naukri|career|salary|promotion|office)\b", q):
        return True
    if re.search(r"(?ix)\b(recovery|theek)\b", q) and re.search(
        r"(?ix)\b(health|swasth|bimari|illness|disease|hospital|surgery|operat\w*)\b", q
    ):
        return True
    try:
        from ask_finance.finance_registry import is_finance_question  # type: ignore

        if is_finance_question(q) and not re.search(
            r"(?ix)\b(job|naukri|promotion|salary\s+hike|office|company|transfer)\b", q
        ):
            return True
    except Exception:
        pass
    try:
        from ask_litigation.litigation_registry import is_career_police_job_question  # type: ignore

        if is_career_police_job_question(q):
            return False  # police job/recruitment is career timing
    except Exception:
        pass
    if re.search(
        r"(?ix)\b(court|case|fir|bail|jail|litigation|mukadma|lawyer)\b", q
    ) and not re.search(r"(?ix)\b(job|naukri|career|office|promotion)\b", q):
        return True
    return False


def is_career_question(question: str) -> bool:
    q = (question or "").strip()
    if not q or should_defer_career_timing(q):
        return False
    return career_scope_match(q)


def is_career_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if should_defer_career_timing(q):
        return False

    # Travel/settlement/visa timing beats bare foreign/abroad in career core
    try:
        from ask_travel.timing_registry import is_travel_timing_question  # type: ignore

        if is_travel_timing_question(q, llm_intent) and not re.search(
            r"(?ix)\b(job|naukri|salary|promotion|office|company|transfer|"
            r"deputation|posting|employer|work\s+permit)\b",
            q,
        ):
            return False
    except Exception:
        pass

    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").strip().lower()
        if dom == "career" and bool(llm_intent.get("is_timing")):
            return True

    try:
        from event_timing._shared.timing_window_pick import (
            detect_later_timing_window_question,
            detect_next_timing_window_question,
        )

        if career_scope_match(q) and re.search(
            r"(?ix)\b(promotion|tarakki|salary\s+hike|increment|appraisal)\b", q
        ):
            if (
                detect_next_timing_window_question(q)
                or detect_later_timing_window_question(q)
                or _PROMOTION_TIMING_FOLLOWUP_RX.search(q)
            ):
                return True
    except Exception:
        pass

    has_timing = bool(TIMING_RX.search(q)) or bool(_CAREER_EVENT_RX.search(q))
    if not has_timing and _DEVANAGARI_TIMING_RX.search(q):
        has_timing = True
    if not has_timing:
        return False
    return career_scope_match(q)


def classify_career_timing_bucket(
    question: str,
    pre_classified_bucket: str | None = None,
) -> str:
    if pre_classified_bucket and pre_classified_bucket in CAREER_TIMING_BUCKETS:
        return pre_classified_bucket
    try:
        from event_timing.career.career_timing import classify_career_question  # type: ignore

        bucket = classify_career_question(question, pre_classified_bucket)
        if bucket == "general_career" and re.search(
            r"(?ix)\b(job|naukri)\b.{0,25}\b(lagega|lagegi|milega|milegi|kab)\b", question or ""
        ):
            return "new_job_timing"
        return bucket
    except Exception:
        return "general_career"


def assess_career_age_context(
    user_age: Optional[int],
    question: str = "",
    bucket: str = "general_career",
) -> dict[str, Any]:
    """Late-career / retirement-aware framing for tricky timing Qs (e.g. age 65 + job kab)."""
    q = (question or "").lower()
    ctx: dict[str, Any] = {
        "user_age": user_age,
        "age_band": None,
        "late_career": False,
        "retirement_phase": False,
        "reframe_bucket": None,
        "narrator_notes": [],
    }
    if user_age is None:
        return ctx

    if user_age >= 60:
        ctx["age_band"] = "retirement_phase"
        ctx["retirement_phase"] = True
        ctx["late_career"] = True
        ctx["narrator_notes"].append(
            "User late-career / retirement-age band — 'pehli naukri' ya fresh-campus "
            "placement tone mat do. Re-employment, consulting, advisory, part-time, "
            "voluntary work, ya post-retirement income frame karo."
        )
    elif user_age >= 50:
        ctx["age_band"] = "late_career"
        ctx["late_career"] = True
        ctx["narrator_notes"].append(
            "User 50+ — senior role, consulting, advisory, ya stable transition "
            "frame prefer karo; entry-level first-job promise avoid karo."
        )
    elif user_age >= 35 and re.search(
        r"(?ix)\b(pehli|first|fresh|campus|fresher|abhi\s+tak\s+naukri\s+nahi)\b", q
    ):
        ctx["age_band"] = "delayed_entry"
        ctx["narrator_notes"].append(
            "Delayed career entry context — blame-free, practical re-skilling + "
            "realistic window tone; age-shaming strictly avoid."
        )
    elif user_age < 18 and re.search(
        r"(?ix)\b(job|naukri|kaam|career)\b", q
    ):
        ctx["age_band"] = "too_young"
        ctx["narrator_notes"].append(
            "User minor-age band — legal working age + education priority frame; "
            "full-time job timing promise avoid."
        )

    if ctx["retirement_phase"] and bucket in ("new_job_timing", "general_career", "job_change"):
        if re.search(r"(?ix)\b(job|naukri)\s+(kab\s+)?(lagega|lagegi|milega|milegi)\b", q):
            ctx["reframe_bucket"] = "late_career_reemployment"

    return ctx


def apply_age_context_to_verdict(verdict: dict, age_ctx: dict) -> dict:
    if not isinstance(verdict, dict) or not age_ctx:
        return verdict
    notes = age_ctx.get("narrator_notes") or []
    if not notes:
        return verdict

    out = dict(verdict)
    warnings = list(out.get("brand_safety_warnings") or [])
    for note in notes:
        if note not in warnings:
            warnings.append(note)
    out["brand_safety_warnings"] = warnings[:7]
    out["age_context"] = age_ctx
    rb = age_ctx.get("reframe_bucket")
    if rb:
        out["age_reframe"] = rb
    return out

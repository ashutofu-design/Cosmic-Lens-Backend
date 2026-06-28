"""Foreign travel / abroad / visa / settlement topic registry."""

from __future__ import annotations

import re

TRAVEL_ARCHETYPES = frozenset({
    "travel_yog",
    "foreign_settlement",
    "visa_theme",
    "relocation_abroad",
    "return_india",
    "travel_obstacles",
    "short_travel",
    "pilgrimage_travel",
    "passport_travel",
    "immigration",
    "business_travel",
    "travel_risk",
    "travel_country_fit",
    "general_travel",
})

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|when\s+will|kis\s+(saal|year|mahine|month|samay|waqt|time)|"
    r"\d{4}\s+me|dasha|antardasha|mahadasha|transit|gochar|muhurat|timing|"
    r"visa\s+(kab|when)|travel\s+(kab|when)|flight\s+(kab|when)|"
    r"settle\s+(kab|when)|abroad\s+(kab|when)|videsh\s+(kab|when)|"
    r"passport\s+(kab|when)|immigration\s+(kab|when)|"
    r"shift\s+kab|abroad\s+shift\s+kab|travel\s+timing|pr\s+kab|"
    r"kab\s+sahi|flight\s+kab"
    r")\b"
)

_EDUCATION_STUDY_ABROAD_RX = re.compile(
    r"(?ix)\b("
    r"study\s+abroad|abroad\s+stud(y|ies)|higher\s+stud(y|ies)|masters|phd|"
    r"university|college|padhai|shiksha|degree|gre|gmat|toefl|ielts|"
    r"student\s+visa|study\s+visa|videsh\s+(padhai|shiksha|university|college)|"
    r"foreign\s+(university|college|degree)|scholarship"
    r")\b"
)

_CAREER_JOB_ABROAD_RX = re.compile(
    r"(?ix)\b("
    r"job|naukri|kaam|career|work|company|office|employ|salary|"
    r"foreign\s+job|abroad\s+job|videsh\s+me\s+kaam|"
    r"foreign\s+company|mnc|multinational|it\s+job|software\s+job|"
    r"work\s+permit\s+job|h1b\s+job|skilled\s+worker\s+job"
    r")\b"
)

_MR_SETTLE_ABROAD_RX = re.compile(
    r"(?ix)\b("
    r"(?:spouse|partner|wife|husband|pati|patni|biwi|shaadi|marriage).{0,40}"
    r"(?:settle|basna|shift|move|relocation|abroad|videsh)|"
    r"shaadi\s+ke\s+baad.{0,30}(?:abroad|videsh|settle|basna|shift)|"
    r"after\s+marriage.{0,30}(?:abroad|settle|foreign)|"
    r"foreign\s+spouse.{0,20}(?:settle|shift|move)"
    r")\b"
)

_STRONG_TRAVEL_RX = re.compile(
    r"(?ix)\b("
    r"videsh|foreign|abroad|overseas|international|"
    r"travel|yatra|trip|tour|passport|visa|"
    r"settle|settlement|immigration|migrate|migration|pr\b|"
    r"green\s+card|citizenship|permanent\s+residen|"
    r"usa|u\.?s\.?a|uk|u\.?k|canada|australia|germany|dubai|europe|schengen|"
    r"new\s+zealand|nz|singapore|uae|america|britain|england|"
    r"flight|airport|departure|immigrant"
    r")\b"
)

_YOG_RX = re.compile(
    r"(?ix)\b("
    r"foreign\s+yog|travel\s+yog|videsh\s+yog|abroad\s+yog|"
    r"foreign\s+travel\s+(?:strong|yog|possible|promise)|"
    r"foreign\s+(?:journey|lands)\s+(?:yog|possible)|"
    r"videsh\s+yatra\s+(?:yog\s+strong|strong|hogi|possible)|"
    r"videsh\s+(?:ja|jaa|jayega|jayegi|jaa\s+sakta|jaa\s+sakti|possible|milega|hoga|hogi)|"
    r"foreign\s+(?:travel\s+)?(?:possible|promise|yog|chance)|"
    r"abroad\s+(?:possible|promise|yog|chance|ja\s+sakta)|"
    r"travel\s+(?:possible|promise|yog|chance|hoga|hogi)|"
    r"overseas\s+(?:possible|yog|travel|journey)|"
    r"airport.{0,25}(?:videsh|abroad|foreign)|videsh\s+jana|"
    r"will\s+i\s+(?:go|travel)\s+abroad"
    r")\b"
)

_SETTLEMENT_RX = re.compile(
    r"(?ix)\b("
    r"settle\s+abroad|settle\s+in\s+(?:foreign|abroad|videsh|overseas|usa|uk|canada|australia|germany|dubai|uae|europe)|"
    r"settlement\s+abroad|foreign\s+settlement|permanent\s+(?:abroad|settlement|basna)|"
    r"bas\s+(?:jaunga|jaungi|sakta|sakti|paunga|paungi)\s+(?:abroad|videsh|foreign)|"
    r"videsh\s+(?:basna|bas\s+sakta|bas\s+paunga|me\s+rahena|me\s+rehna|me\s+bas)|"
    r"videsh\s+me\s+(?:bas|reh|rahena|basna)|"
    r"abroad\s+(?:settle|settlement|rehna|rahena|basna|shift\s+permanently)|"
    r"settle\s+videsh|overseas\s+settlement|"
    r"videsh\s+me\s+permanent|permanent\s+life\s+abroad|"
    r"foreign\s+land\s+me\s+(?:basna|rehna)|"
    r"shift\s+(?:permanently|forever)\s+abroad|"
    r"permanent\s+shift\s+abroad|life\s+abroad|"
    r"pr\s+(?:milega|hoga|possible)|permanent\s+residen|"
    r"(?:canada|usa|uk|australia|germany|dubai|uae|europe)\s+me\s+(?:bas|reh|basna|bas\s+sakta|bas\s+sakti)|"
    r"nri|non[\s-]?resident\s+indian|pravasi"
    r")\b"
)

_VISA_RX = re.compile(
    r"(?ix)\b("
    r"visa|viza|veez|veeza|"
    r"student\s+visa|work\s+visa|tourist\s+visa|visitor\s+visa|"
    r"us\s+visa|usa\s+visa|uk\s+visa|canada\s+visa|australia\s+visa|"
    r"schengen|h1b|b1|b2|f1|"
    r"visa\s+(?:approve|approval|milega|milegi|hoga|hogi|legi|deny|interview|"
    r"delay|stuck|problem|issue|refus)|"
    r"visa\s+(?:reject|rejection|refusal)|"
    r"embassy|consulate"
    r")\b"
)

_IMMIGRATION_RX = re.compile(
    r"(?ix)\b("
    r"immigration|immigrant|migrate|migration|"
    r"green\s+card|citizenship|naturalization|"
    r"pr\s+(?:file|apply|application|process|status)|"
    r"(?:canada|usa|uk|australia)\s+pr|pr\s+(?:canada|usa|uk|australia)\s+file|"
    r"permanent\s+residen(?:ce|cy)|"
    r"express\s+entry|i-?485|i-?140|"
    r"visa\s+extension\s+to\s+pr|"
    r"immigration\s+(?:case|process|lawyer|file)"
    r")\b"
)

_RELOCATION_RX = re.compile(
    r"(?ix)\b("
    r"relocate\s+(?:abroad|videsh|overseas)|relocation\s+(?:abroad|overseas|chart|theme|tone)|"
    r"move\s+(?:abroad|overseas)|shift\s+abroad|"
    r"shift\s+(?:to|in)\s+(?:foreign|abroad|videsh|overseas|usa|uk|canada|australia|germany|dubai|uae|europe)|"
    r"move\s+(?:to|in)\s+(?:foreign|abroad|videsh|overseas|usa|uk|canada|australia|germany|dubai|uae|europe)|"
    r"videsh\s+shift|abroad\s+shift|foreign\s+shift|overseas\s+shift|relocate\s+videsh|"
    r"leaving\s+(?:india|country)\s+(?:for|to|abroad)|"
    r"pack\s+up\s+abroad|shift\s+foreign\s+country"
    r")\b"
)

_RETURN_RX = re.compile(
    r"(?ix)\b("
    r"return\s+(?:to\s+)?india|wapas\s+(?:aana|aa\s+sakta|india|bharat)|"
    r"india\s+(?:wapas|return|aana)|"
    r"abroad\s+se\s+(?:wapas|return)|videsh\s+se\s+wapas|"
    r"return\s+home\s+(?:india|chart)?|abroad\s+se\s+return|"
    r"come\s+back\s+(?:to\s+)?india|"
    r"no\s+settlement\s+abroad|settle\s+nahi\s+hoga|"
    r"foreign\s+settlement\s+(?:nahi|unlikely|weak)"
    r")\b"
)

_OBSTACLES_RX = re.compile(
    r"(?ix)\b("
    r"travel\s+(?:delay|obstacle|block|problem|ruka|rukawat)|"
    r"videsh\s+(?:delay|obstacle|block|problem|ruka|rukawat|nahi)|"
    r"videsh\s+me\s+(?:delay|problem|dikkat|rukawat)|"
    r"abroad\s+(?:delay|obstacle|block|problem|nahi\s+hoga)|"
    r"foreign\s+(?:travel\s+)?(?:delay|obstacle|block)|"
    r"settlement\s+(?:delay|obstacle|block|problem)|"
    r"visa\s+obstacle|"
    r"videsh\s+me\s+problem|abroad\s+me\s+dikkat"
    r")\b"
)

_COUNTRY_FIT_RX = re.compile(
    r"(?ix)\b("
    r"kaun\s+sa\s+(?:desh|country|mulk)|kaun\s+si\s+(?:country|desh)|"
    r"konsa\s+(?:desh|country|mulk)|konsi\s+(?:country|desh|deshi)|"
    r"which\s+country|"
    r"(?:usa|uk|canada|australia|germany|dubai|uae|europe|america|britain|singapore|new\s+zealand|schengen)"
    r"\s+ya\s+(?:usa|uk|canada|australia|germany|dubai|uae|europe|america|britain|singapore|schengen)|"
    r"country\s+(?:suit|fit|better|choose|milega|hoga|possible|jaaunga|jaungi)|"
    r"desh\s+(?:milega|hoga|suit|fit|better|choose|kaun\s+sa)|"
    r"videsh\s+me\s+kaun\s+sa\s+(?:desh|country)|"
    r"foreign\s+country\s+(?:fit|suits|better|choose)|"
    r"kaun\s+se\s+(?:desh|country)\s+(?:me\s+)?(?:jaunga|jaungi|jaa\s+sakta|shift|basna|shift\s+hoga)|"
    r"kis\s+(?:desh|country)\s+(?:me\s+)?(?:jaunga|jaungi|jaa\s+sakta|shift|basna)|"
    r"best\s+country\s+(?:for|to)\s+(?:me|settle|travel|shift)|"
    r"overseas\s+country\s+(?:fit|better|choose)"
    r")\b"
)

_PILGRIMAGE_RX = re.compile(
    r"(?ix)\b("
    r"pilgrimage|teerth|tirth|tirtha|dharma\s+yatra|"
    r"mandir\s+yatra|hajj|umrah|kashi|char\s+dham|"
    r"sacred\s+(?:journey|travel)|religious\s+(?:trip|travel|yatra)"
    r")\b"
)

_SHORT_TRAVEL_RX = re.compile(
    r"(?ix)\b("
    r"short\s+(?:trip|travel|tour)|vacation\s+(?:abroad|overseas)|holiday\s+abroad|"
    r"foreign\s+(?:trip|tour|vacation|holiday)|"
    r"abroad\s+(?:trip|tour|vacation|holiday|ghumna|ghoomna)|"
    r"videsh\s+(?:ghumne|ghoomne|trip|tour)|"
    r"tourist\s+(?:trip|travel)|leisure\s+travel|"
    r"flight\s+abroad|"
    r"honeymoon\s+abroad|foreign\s+visit"
    r")\b"
)

_PASSPORT_RX = re.compile(
    r"(?ix)\b("
    r"passport|pass\s*port|"
    r"passport\s+(?:milega|hoga|renew|problem|delay|reject|issue)|"
    r"travel\s+capacity|travel\s+desire|"
    r"foreign\s+travel\s+capacity|abroad\s+travel\s+capacity"
    r")\b"
)

_BUSINESS_TRAVEL_RX = re.compile(
    r"(?ix)\b("
    r"business\s+(?:trip|travel)\s*(?:abroad|foreign|videsh|overseas)?|"
    r"foreign\s+business\s+travel|business\s+travel\s+(?:abroad|overseas|foreign|videsh)?|"
    r"official\s+(?:trip|travel)\s*(?:abroad|foreign|videsh|overseas|chart)?|"
    r"corporate\s+(?:trip|travel)\s*(?:abroad|foreign|videsh|overseas|chart)?|"
    r"work\s+trip\s+abroad|corporate\s+travel\s+abroad"
    r")\b"
)

_RISK_RX = re.compile(
    r"(?ix)\b("
    r"travel\s+(?:risk|danger|accident|unsafe)|"
    r"abroad\s+(?:risk|danger|unsafe|accident)|"
    r"foreign\s+(?:travel\s+)?(?:risk|danger|unsafe)|"
    r"foreign\s+travel\s+safe|travel\s+safe\s+(?:abroad|foreign|hai)?|"
    r"videsh\s+(?:me\s+)?(?:khatra|risk|danger|darr)|"
    r"accident\s+(?:abroad|foreign|travel)|"
    r"unsafe\s+(?:abroad|foreign|travel)"
    r")\b"
)


def is_education_study_abroad_question(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q or not _STRONG_TRAVEL_RX.search(q):
        return False
    return bool(_EDUCATION_STUDY_ABROAD_RX.search(q))


def is_career_job_abroad_question(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q or not _STRONG_TRAVEL_RX.search(q):
        return False
    if _BUSINESS_TRAVEL_RX.search(q):
        return False
    if re.search(r"(?ix)\bwork\s+permit\s+visa\b", q):
        return False
    if _SETTLEMENT_RX.search(q) or _VISA_RX.search(q) or _IMMIGRATION_RX.search(q):
        return False
    return bool(_CAREER_JOB_ABROAD_RX.search(q))


def is_mr_settle_abroad_question(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return False
    return bool(_MR_SETTLE_ABROAD_RX.search(q))


def is_travel_timing_question(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return False
    if not _TIMING_RX.search(q):
        return False
    return bool(_STRONG_TRAVEL_RX.search(q)) or bool(
        re.search(r"(?ix)\b(construction|registry|shift|travel|visa|passport)\b", q)
    )


def detect_travel_archetype(question: str) -> str | None:
    q = (question or "").strip().lower()
    if not q:
        return None
    if is_travel_timing_question(q):
        return None
    if is_education_study_abroad_question(q):
        return None
    if is_career_job_abroad_question(q):
        return None
    if is_mr_settle_abroad_question(q):
        return None

    if _RETURN_RX.search(q):
        return "return_india"
    if _PILGRIMAGE_RX.search(q):
        return "pilgrimage_travel"
    if _IMMIGRATION_RX.search(q):
        return "immigration"
    if _PASSPORT_RX.search(q):
        return "passport_travel"
    if _OBSTACLES_RX.search(q):
        return "travel_obstacles"
    if _VISA_RX.search(q) and not _EDUCATION_STUDY_ABROAD_RX.search(q):
        return "visa_theme"
    if _SETTLEMENT_RX.search(q):
        return "foreign_settlement"
    if _RELOCATION_RX.search(q):
        return "relocation_abroad"
    if _COUNTRY_FIT_RX.search(q):
        return "travel_country_fit"
    if _RISK_RX.search(q):
        return "travel_risk"
    if _BUSINESS_TRAVEL_RX.search(q):
        return "business_travel"
    if re.search(
        r"(?ix)\b(chart\s+reading|chart\s+summary|reading\s+overall|overall\s+chart|"
        r"topic\s+chart|chart\s+analysis|chart\s+tone|lands\s+chart\s+summary)\b",
        q,
    ) and _STRONG_TRAVEL_RX.search(q):
        return "general_travel"
    if re.search(r"(?ix)\byog\b", q) and _STRONG_TRAVEL_RX.search(q):
        return "travel_yog"
    if _SHORT_TRAVEL_RX.search(q):
        return "short_travel"
    if _YOG_RX.search(q):
        return "travel_yog"
    if re.search(
        r"(?ix)\b(settle|settlement|basna|bas\s+sakta|bas\s+paunga).{0,35}"
        r"(abroad|videsh|foreign|overseas|canada|usa|uk)\b",
        q,
    ):
        return "foreign_settlement"
    if re.search(
        r"(?ix)\b(relocate|relocation|shift|move|leaving\s+india).{0,35}"
        r"(abroad|videsh|foreign|overseas|canada|usa|uk)\b",
        q,
    ):
        return "relocation_abroad"
    if re.search(r"(?ix)\b(return|wapas).{0,30}(india|bharat|home)\b", q):
        return "return_india"
    if re.search(
        r"(?ix)\b(foreign|videsh|abroad|overseas).{0,25}(yog|possible|strong|travel|journey|lands)\b",
        q,
    ):
        return "travel_yog"
    if _STRONG_TRAVEL_RX.search(q):
        return "general_travel"
    return None


def is_travel_static_question(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if is_travel_timing_question(q):
        return False
    if is_education_study_abroad_question(q):
        return False
    if is_career_job_abroad_question(q):
        return False
    if is_mr_settle_abroad_question(q):
        return False
    return detect_travel_archetype(q) is not None

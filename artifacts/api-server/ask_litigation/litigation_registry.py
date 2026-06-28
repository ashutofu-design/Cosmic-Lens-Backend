"""Court case / legal / police / litigation topic registry."""

from __future__ import annotations

import re

LITIGATION_ARCHETYPES = frozenset({
    "litigation_remedy",
    "litigation_yog",
    "case_outcome",
    "court_delay",
    "bail_theme",
    "jail_concern",
    "police_fir",
    "criminal_case",
    "civil_litigation",
    "legal_obstacles",
    "enemy_case",
    "acquittal_relief",
    "lawyer_support",
    "family_court",
    "settlement",
    "general_litigation",
})

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|when\s+will|kis\s+(saal|year|mahine|month|samay|waqt|time)|"
    r"\d{4}\s+me|dasha|antardasha|mahadasha|transit|gochar|muhurat|timing|"
    r"case\s+(kab|when)|court\s+(kab|when)|verdict\s+(kab|when)|"
    r"bail\s+(kab|when)|fir\s+(kab|when)|hearing\s+(kab|when)|"
    r"jail\s+(kab|when)|release\s+(kab|when)|judgment\s+(kab|when)"
    r")\b"
)

_PROPERTY_COURT_RX = re.compile(
    r"(?ix)\b("
    r"property|real\s*estate|ghar|makaan|makan|plot|zameen|zamin|jamin|jameen|"
    r"land|flat|apartment|home|house|villa|haveli|paitrik|sampatti|registry"
    r")\b"
)

_MR_DIVORCE_COURT_RX = re.compile(
    r"(?ix)\b("
    r"divorce\s+court|"
    r"family\s+court.{0,30}(?:divorce|talaq)|"
    r"(?:divorce|talaq).{0,30}(?:court|case|mukadma)|"
    r"(?:court|case|mukadma).{0,30}(?:divorce|talaq)|"
    r"(?:alimony|maintenance).{0,20}(?:divorce|talaq).{0,25}(?:court|case)|"
    r"(?:divorce|talaq).{0,20}(?:alimony|maintenance).{0,25}(?:court|case)|"
    r"shaadi\s+tut.{0,30}(?:court|case)|"
    r"(?:pati|patni|wife|husband|spouse).{0,35}(?:divorce|talaq).{0,25}(?:court|case)|"
    r"498a.{0,25}(?:divorce|marriage|shaadi)|"
    r"marriage\s+case.{0,20}(?:divorce|talaq)"
    r")\b"
)

_CAREER_POLICE_JOB_RX = re.compile(
    r"(?ix)\b("
    r"police\s+(?:job|naukri|service|department|officer|constable|recruitment)|"
    r"police\s+recruitment|recruitment\s+police|"
    r"ips\s+(?:job|naukri|ban\s+sakta|possible|officer)|"
    r"police\s+line|police\s+career|"
    r"become\s+(?:a\s+)?police|police\s+me\s+(?:naukri|job|join)|"
    r"law\s+enforcement\s+career"
    r")\b"
)

_DEATH_PENALTY_RX = re.compile(
    r"(?ix)\b("
    r"death\s+penalty|capital\s+punishment|phansi|hanging|"
    r"faansi|maut\s+ki\s+saza|saza\s+e\s+maut|"
    r"life\s+imprisonment\s+for\s+life|umr\s+qaid"
    r")\b"
)

_STRONG_LITIGATION_RX = re.compile(
    r"(?ix)\b("
    r"mukadma|mukadama|court|case|kanoon|legal|litigation|"
    r"law\s*suit|lawsuit|dispute|enemy|enemies|shatru|fir|"
    r"police|thana|jail|prison|bail|zamanat|"
    r"criminal|civil|advocate|vakil|lawyer|"
    r"hearing|verdict|judgment|judgement|"
    r"acquittal|conviction|section\s+\d+|"
    r"498a|ipc|crpc|nda|ndps|"
    r"court\s+case|legal\s+case|police\s+case|"
    r"kanooni|vivad|case\s+chalega|case\s+ladega|"
    r"underground|bicholiya|middleman"
    r")\b"
)

_YOG_RX = re.compile(
    r"(?ix)\b("
    r"court\s+case\s+yog|litigation\s+yog|legal\s+case\s+yog|"
    r"court\s+case\s+(?:promise|theme)|"
    r"mukadma\s+(?:hoga|hogi|ladega|ladegi|chalega|chalegi|yog|possible)|"
    r"court\s+case\s+(?:hoga|hogi|possible|yog|milega|chalega|promise|theme)|"
    r"case\s+(?:hoga|hogi|possible|yog|chalega|ladega|promise|theme)|"
    r"legal\s+trouble\s+yog|kanooni\s+(?:pareshani|mamla|case)\s+(?:hoga|yog)|"
    r"litigation\s+(?:possible|promise|yog|strong)|"
    r"will\s+i\s+(?:face|have)\s+(?:a\s+)?(?:court|legal)\s+case|"
    r"court\s+yog|mukadma\s+yog"
    r")\b"
)

_OUTCOME_RX = re.compile(
    r"(?ix)\b("
    r"jeet\s+(?:jaunga|jaungi|jayega|jayegi|paunga|paungi|milega|hoga)|"
    r"jeet\s+sakta|case\s+jeet|court\s+jeet|"
    r"win\s+(?:the\s+)?case|case\s+win|"
    r"haar\s+(?:jaunga|jaungi|jayega|jayegi|paunga|paungi|hoga)|"
    r"har\s+(?:jaunga|jaungi|jayega|jayegi|paunga|paungi|hoga)|"
    r"lose\s+(?:the\s+)?case|case\s+loss|"
    r"case\s+(?:favour|favor|against)|"
    r"verdict\s+(?:favour|favor|against|positive|negative)|"
    r"judgment\s+(?:favour|favor|against)|"
    r"case\s+outcome|outcome\s+of\s+case|"
    r"case\s+(?:result|fate)|"
    r"jeet\s+paunga\s+case|har\s+jayega\s+case|"
    r"favourable|unfavourable|favorable|unfavorable|"
    r"hit\s*\(?\s*favour|mere\s+hit|favour\s+me|favor\s+me|"
    r"dushman|bhai\s+baazi"
    r")\b"
)

_DELAY_RX = re.compile(
    r"(?ix)\b("
    r"case\s+delay|court\s+delay|delay\s+in\s+case|"
    r"case\s+(?:ruka|ruki|atka|atki|pending|pend|late)|"
    r"court\s+(?:ruka|ruki|atka|atki|pending|late)|"
    r"litigation\s+delay|legal\s+delay|"
    r"mukadma\s+(?:ruka|atka|late|delay|lamba)|"
    r"hearing\s+delay|judgment\s+delay|"
    r"case\s+lamba\s+chalega|case\s+chalega\s+lamba|"
    r"case\s+rukawat|court\s+case\s+lamba|case\s+lamba\b|mukadma\s+lamba\b"
    r")\b"
)

_BAIL_RX = re.compile(
    r"(?ix)\b("
    r"bail|zamanat|jamant|"
    r"bail\s+(?:milega|milegi|hoga|hogi|legi|deny|reject|approve|possible)|"
    r"zamanat\s+(?:milega|milegi|hoga|hogi|legi|mile|nahi)|"
    r"interim\s+bail|regular\s+bail|anticipatory\s+bail|"
    r"release\s+on\s+bail|bail\s+petition|bail\s+order"
    r")\b"
)

_JAIL_RX = re.compile(
    r"(?ix)\b("
    r"jail|prison|qaid|qaidkhana|"
    r"jail\s+(?:hoga|hogi|jayega|jayegi|jaunga|jaungi|milega|possible|yog)|"
    r"prison\s+(?:hoga|hogi|possible|yog)|"
    r"andar\s+(?:hoga|hogi|jaunga|jaungi|jayega|jayegi|milega|possible)|"
    r"qaid\s+(?:hoga|hogi|milega|possible)|"
    r"custody\s+(?:hoga|hogi|possible|remand)|"
    r"remand|judicial\s+custody|police\s+custody|"
    r"jail\s+yog|prison\s+yog"
    r")\b"
)

_POLICE_FIR_RX = re.compile(
    r"(?ix)\b("
    r"fir|f\.i\.r|first\s+information\s+report|"
    r"police\s+case|police\s+complaint|thana|"
    r"police\s+(?:station|report|register|action|challan)|"
    r"police\s+(?:case\s+)?(?:bane|bane?gi|hoga|hogi|lagi|lag\s+sakti)|"
    r"complaint\s+(?:police|thana)|"
    r"police\s+ne\s+(?:case|fir)|"
    r"challan\s+police|"
    r"thanedar|sho\s+police"
    r")\b"
)

_CRIMINAL_RX = re.compile(
    r"(?ix)\b("
    r"criminal\s+case|criminal\s+court|criminal\s+charge|"
    r"498\s*a|498a|ipc|ndps|cheating\s+case|fraud\s+case|"
    r"murder\s+case|attempt\s+to\s+murder|"
    r"assault\s+case|theft\s+case|"
    r"criminal\s+(?:proceeding|litigation|matter|trial)|"
    r"session\s+court|sessions\s+court|"
    r"crpc|penal\s+code"
    r")\b"
)

_CIVIL_RX = re.compile(
    r"(?ix)\b("
    r"civil\s+case|civil\s+court|civil\s+suit|"
    r"civil\s+(?:litigation|matter|dispute|proceeding)|"
    r"civil\s+decree|money\s+suit|"
    r"recovery\s+suit|specific\s+performance|"
    r"injunction\s+case|"
    r"consumer\s+court|consumer\s+case|"
    r"labour\s+court|tribunal\s+case"
    r")\b"
)

_OBSTACLES_RX = re.compile(
    r"(?ix)\b("
    r"legal\s+(?:problem|obstacle|issue|trouble|dikkat|pareshani)|"
    r"kanooni\s+(?:pareshani|dikkat|problem|mushkil|rukawat)|"
    r"litigation\s+(?:problem|obstacle|issue|trouble)|"
    r"case\s+(?:problem|obstacle|issue|trouble|dikkat|mushkil)|"
    r"court\s+(?:problem|obstacle|issue|trouble|dikkat)|"
    r"legal\s+stress|legal\s+friction|"
    r"case\s+me\s+(?:dikkat|problem|mushkil|rukawat)"
    r")\b"
)

_ENEMY_RX = re.compile(
    r"(?ix)\b("
    r"enemy\s+case|enemies\s+case|shatru\s+case|"
    r"dushman\s+(?:case|mukadma|court|litigation)|"
    r"shatru\s+(?:mukadma|court|case|litigation)|"
    r"enemy\s+(?:litigation|lawsuit|court)|"
    r"opponent\s+case|rival\s+case|"
    r"dushman\s+ne\s+(?:case|fir|mukadma)|"
    r"shatru\s+se\s+(?:case|mukadma|court)"
    r")\b"
)

_ACQUITTAL_RX = re.compile(
    r"(?ix)\b("
    r"acquittal|acquit|bera\s*gari|chhut\s*kara|chhutkara|"
    r"case\s+(?:dismiss|dismissed|drop|dropped|quash|quashed)|"
    r"case\s+(?:khatam|band|close|closed|finish)|"
    r"fir\s+(?:quash|quashed|dismiss)|"
    r"discharge\s+from\s+case|case\s+se\s+chhut|"
    r"case\s+se\s+riha|release\s+from\s+case|"
    r"case\s+clear|case\s+clean|"
    r"innocent\s+prove|prove\s+innocent"
    r")\b"
)

_LAWYER_RX = re.compile(
    r"(?ix)\b("
    r"advocate|vakil|lawyer|legal\s+counsel|"
    r"advocate\s+(?:sahi|support|help|milega|hoga|strong)|"
    r"vakil\s+(?:sahi|support|help|milega|hoga|strong)|"
    r"lawyer\s+(?:support|help|right|sahi|strong)|"
    r"legal\s+help\s+chart|counsel\s+support|"
    r"accha\s+vakil|sahi\s+advocate|"
    r"litigation\s+support\s+from\s+counsel"
    r")\b"
)

_FAMILY_COURT_RX = re.compile(
    r"(?ix)\b("
    r"family\s+court|matrimonial\s+court|"
    r"maintenance\s+(?:case|court)|alimony\s+(?:case|court)|"
    r"(?:child\s+)?custody\s+(?:case|court)|"
    r"domestic\s+violence\s+case|dv\s+case|"
    r"matrimonial\s+(?:case|dispute|litigation)"
    r")\b"
)

_SETTLEMENT_RX = re.compile(
    r"(?ix)\b("
    r"compromise|settlement|samjhauta|mediation|madhyasthata|"
    r"lok\s+adalat|arbitration|withdraw|bicholiya|middleman|"
    r"out[\s-]?of[\s-]?court"
    r")\b"
)


def is_property_court_question(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return False
    if re.search(
        r"(?ix)\b(fir|criminal|bail|jail|attach|kurki|seize|mukadma|litigation|complaint)\b",
        q,
    ):
        return False
    if not _PROPERTY_COURT_RX.search(q):
        return False
    if re.search(r"(?ix)\b(dispute|vivad|court|case|litigation|mukadma|legal|hissa)\b", q):
        return True
    if re.search(r"(?ix)\bproperty\s+litigation\b", q):
        return True
    try:
        from ask_property.property_registry import detect_property_archetype  # type: ignore

        arch = detect_property_archetype(q)
        return arch in {"property_dispute", "property_risk"}
    except Exception:
        return bool(re.search(r"(?ix)\b(dispute|vivad|court\s+case)\b", q))


def is_mr_divorce_court_question(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return False
    return bool(_MR_DIVORCE_COURT_RX.search(q))


def is_career_police_job_question(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return False
    if _STRONG_LITIGATION_RX.search(q) and re.search(
        r"(?ix)\b(case|fir|mukadma|court|litigation|bail|jail|complaint)\b", q
    ):
        return False
    return bool(_CAREER_POLICE_JOB_RX.search(q))


def is_death_penalty_crisis_question(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return False
    return bool(_DEATH_PENALTY_RX.search(q))


def is_litigation_timing_question(question: str, llm_intent: dict | None = None) -> bool:
    from .timing_registry import is_litigation_timing_question as _is_timing

    return _is_timing(question, llm_intent)


def detect_litigation_archetype(question: str) -> str | None:
    q = (question or "").strip().lower()
    if not q:
        return None
    if is_litigation_timing_question(q):
        return None
    if is_death_penalty_crisis_question(q):
        return None
    if is_property_court_question(q):
        return None
    if is_mr_divorce_court_question(q):
        return None
    if is_career_police_job_question(q):
        return None

    try:
        from .remedy import is_litigation_remedy_question

        if is_litigation_remedy_question(q):
            return "litigation_remedy"
    except Exception:
        pass

    if _ACQUITTAL_RX.search(q):
        return "acquittal_relief"
    if _BAIL_RX.search(q):
        return "bail_theme"
    if _JAIL_RX.search(q) and not _DEATH_PENALTY_RX.search(q):
        return "jail_concern"
    if _POLICE_FIR_RX.search(q):
        return "police_fir"
    if _CRIMINAL_RX.search(q):
        return "criminal_case"
    if _CIVIL_RX.search(q):
        return "civil_litigation"
    if _FAMILY_COURT_RX.search(q):
        return "family_court"
    if _SETTLEMENT_RX.search(q):
        return "settlement"
    if _DELAY_RX.search(q):
        return "court_delay"
    if _OUTCOME_RX.search(q):
        return "case_outcome"
    if _ENEMY_RX.search(q):
        return "enemy_case"
    if _LAWYER_RX.search(q):
        return "lawyer_support"
    if _YOG_RX.search(q):
        return "litigation_yog"
    if _OBSTACLES_RX.search(q):
        return "legal_obstacles"
    if re.search(
        r"(?ix)\b(chart\s+reading|chart\s+summary|reading\s+overall|overall\s+chart|"
        r"topic\s+chart|chart\s+analysis|chart\s+tone|legal\s+chart\s+summary)\b",
        q,
    ) and _STRONG_LITIGATION_RX.search(q):
        return "general_litigation"
    if re.search(r"(?ix)\byog\b", q) and _STRONG_LITIGATION_RX.search(q):
        return "litigation_yog"
    if re.search(
        r"(?ix)\b(court\s+case|mukadma|litigation|legal\s+case)\b",
        q,
    ) and re.search(
        r"(?ix)\b(yog|promise|theme|hoga|hogi|chalega|ladega|ladegi|possible|strong|milega)\b",
        q,
    ):
        return "litigation_yog"
    if re.search(
        r"(?ix)\b(court|case|mukadma|litigation|legal|fir|police|bail|jail)\b",
        q,
    ):
        return "general_litigation"
    if _STRONG_LITIGATION_RX.search(q):
        return "general_litigation"
    return None


def is_litigation_static_question(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if is_litigation_timing_question(q):
        return False
    if is_death_penalty_crisis_question(q):
        return False
    if is_property_court_question(q):
        return False
    if is_mr_divorce_court_question(q):
        return False
    if is_career_police_job_question(q):
        return False
    return detect_litigation_archetype(q) is not None

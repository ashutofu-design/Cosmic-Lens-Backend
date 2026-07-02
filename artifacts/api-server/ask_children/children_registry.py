"""Children / progeny topic registry — scope keywords + archetype detection."""

from __future__ import annotations

import re

CHILDREN_ARCHETYPES = frozenset({
    "child_promise",
    "fertility_conception",
    "pregnancy_wellbeing",
    "child_delay",
    "child_gender_note",
    "number_of_children",
    "child_nature",
    "parent_child_bond",
    "child_success",
    "adoption_path",
    "child_loss_concern",
    "progeny_obstacles",
    "general_children",
})

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when|when\s+will|kis\s+(saal|year|mahine|month|umr|age)|"
    r"\d{4}\s+me|dasha|antardasha|mahadasha|transit|gochar|muhurat|timing|"
    r"baby\s+(kab|when)|child\s+(kab|when)|santan\s+(kab|when)|"
    r"pregnancy\s+(kab|when)|conceive\s+(kab|when)|"
    r"good\s+news\s+(kab|when)|garbh\s+(kab|when)"
    r")\b"
)

_MR_SPOUSE_CHILDREN_RX = re.compile(
    r"(?ix)\b("
    r"(?:spouse|partner|wife|husband|pati|patni|biwi|jeevan\s*sathi)\b.{0,35}\b("
    r"parenting|parent\s*style|bachon|bacchon|children|kids|sanskaar|values?"
    r")|"
    r"parenting\s+style|"
    r"spouse.{0,25}(children|kids|bach)|"
    r"partner.{0,25}(children|kids|bach)|"
    r"shaadi\s+ke\s+baad.{0,25}(bach|child|parenting|sanskaar)"
    r")\b"
)

_HEALTH_MEDICAL_RX = re.compile(
    r"(?ix)\b("
    r"sehat|health|bimari|beemar|bimar|doctor|diagnos|treatment|medicine|"
    r"hospital|symptom|disease|illness|medical|hormon|pcod|pcos|"
    r"tube\s*block|uterus|ovary|sperm\s*count"
    r")\b"
)

_CHILDREN_CORE_RX = re.compile(
    r"(?ix)\b("
    r"bachh?[ae]|bachch?[ae]|bachcha|bachha|child(?:ren)?|kids?|"
    r"santaan|santan|santtaan|santtan|putra|putri|baby|babies|"
    r"progeny|offspring|aulad|aulaad|beta\b|beti\b|"
    r"ivf|iui|surrogacy|surrogate|"
    r"conceive|conceiving|conception|"
    r"pregnan(?:t|cy|cies)|pregnent|garbh|garbhwati|garbhdharan|"
    r"miscarriage|garbhpat|"
    r"infertil|infertility|sterility|barren|nispantan|nisantaan|"
    r"fertility|fertile|ovul|"
    r"good\s+news|khushkhabri|khush\s*khabri|khushkhabar|"
    r"twins?|jodwa|jud(?:wa|wan)|"
    r"godbharai|god\s+bharai|baby\s+shower|"
    r"baby\s*plan|baby\s*planning|family\s*planning|"
    r"matritva|maternity|paternity|"
    r"adoption|adopt|gode\s+lena|"
    r"first\s+child|second\s+child|teesra\s+bachcha|"
    r"putra\s*prapti|santaan\s*prapti|santan\s*yog"
    r")\b"
)

_ADOPTION_RX = re.compile(
    r"(?ix)\b("
    r"adopt(?:ion|ed|ing)?|gode\s+(?:lena|bachcha)|surrogacy|surrogate|"
    r"donor\s+egg|donor\s+sperm|foster|"
    r"non\s+biological\s+child|biological\s+child\s+route"
    r")\b"
)

_LOSS_RX = re.compile(
    r"(?ix)\b("
    r"miscarriage|garbhpat|pregnancy\s+loss|garbh\s+loss|"
    r"garbh\s+gir\s+gaya|garbh\s+safe\s+nahi\s+raha|"
    r"baccha?\s+(?:nahi\s+bacha|gir\s+gaya|lost)|"
    r"nahi\s+bacha\s+fear|"
    r"child\s+loss|abort|"
    r"loss\s+ke\s+baad"
    r")\b"
)

_OBSTACLES_RX = re.compile(
    r"(?ix)\b("
    r"nisanta?n|nispantan|"
    r"santan\s+dosh|putra\s+dosh|progeny\s+obstacle|"
    r"santaan\s+nahi|santan\s+nahi|bachcha?\s+nahi|childless|"
    r"santan\s+nahi\s+ho|obstacle.{0,20}santan|santan.{0,20}obstacle|"
    r"rukawat|rukaawat|"
    r"santan\s+me\s+rukawat|putra\s+prapti\s+me\s+rukawat|"
    r"barren\s+dosh|sterility\s+dosh"
    r")\b"
)

_DELAY_RX = re.compile(
    r"(?ix)\b("
    r"delay\s+in\s+(?:child|children|santan|progeny)|"
    r"santan\s+(?:me\s+)?delay|bachch?[ae]\s+me\s+delay|bachcha?\s+(?:me\s+)?delay|"
    r"late\s+(?:child|children|santan|motherhood|fatherhood)|"
    r"der\s+se\s+(?:santan|bachcha|child|milegi|milega|prapti)|"
    r"santaan\s+der\s+se|putra\s+prapti\s+der|"
    r"child\s+delay|progeny\s+delay|delay\s+tone|"
    r"bachcha?\s+late|late\s+aayega"
    r")\b"
)

_FERTILITY_RX = re.compile(
    r"(?ix)\b("
    r"ivf|iui|infertil\w*|conceive|conception|conceiving|"
    r"fertility|fertile|ovul|sterility|barren|"
    r"garbhdharan|garbh\s+dharan|"
    r"baccha?\s+(?:conceive|conception)|child\s+conceive"
    r")\b"
)

_PLANNING_RX = re.compile(
    r"(?ix)\b("
    r"baby\s*plan(?:ning)?|family\s*planning|planning\s+chart"
    r")\b"
)

_PREGNANCY_RX = re.compile(
    r"(?ix)\b("
    r"pregnan(?:t|cy|cies)|pregnent|garbhwati|garbh\b|"
    r"good\s+news|khushkhabri|khush\s*khabri|"
    r"godbharai|god\s+bharai|baby\s+shower|"
    r"pregnancy\s+(?:safe|successful|smooth|healthy)|"
    r"garbh\s+(?:tik|safe|theek|sahi)|"
    r"maternity\s+phase"
    r")\b"
)

_PROMISE_RX = re.compile(
    r"(?ix)\b("
    r"santaan\s+(?:hogi|hoga|milegi|milega|possible|yog|prapti|blessing)|"
    r"santan\s+(?:hogi|hoga|milegi|milega|possible|yog|prapti|blessing)|"
    r"bachch?[ae]\s+(?:honge|hoga|hogi|milega|milegi|possible)|"
    r"child(?:ren)?\s+(?:will|possible|promised|yog)|"
    r"putra\s*prapti|santaan\s*prapti|aulad\s+(?:hogi|milegi)|"
    r"will\s+i\s+have\s+(?:a\s+)?child|"
    r"baby\s+(?:possible|hoga|hogi)|"
    r"progeny\s+promised|offspring\s+possible|"
    r"santaan\s+(?:ka\s+)?yog|santan\s+(?:ka\s+)?yog|santan\s+blessing|"
    r"maa\s+ban\s+paungi|pita\s+ban\s+paunga|main\s+maa\s+ban|ban\s+paungi|ban\s+paunga|"
    r"bachcha\s+hoga\s+ya\s+nahi"
    r")\b"
)

_GENDER_RX = re.compile(
    r"(?ix)\b("
    r"ladka\s+ya\s+ladki|ladki\s+ya\s+ladka|"
    r"ladki\s+hogi\s+ya\s+ladka|ladka\s+hoga\s+ya\s+ladki|"
    r"boy\s+or\s+girl|girl\s+or\s+boy|boy\s+ya\s+girl|"
    r"beta\s+ya\s+beti|beti\s+ya\s+beta|"
    r"putra\s+ya\s+putri|putri\s+ya\s+putra|"
    r"putra\s+hoga\s+ya\s+putri|putri\s+hogi\s+ya\s+putra|"
    r"gender\s+of\s+(?:child|baby)|gender\s+prediction|"
    r"bachch?[ae]\s+ka\s+gender|"
    r"bachcha?\s+(?:ladka|ladki)\s+hoga|"
    r"pehla\s+(?:ladka|ladki|beta|beti)|pehli\s+(?:beti|ladki|beta|ladka)|"
    r"baby\s+boy\s+ya\s+girl"
    r")\b"
)

_NUMBER_RX = re.compile(
    r"(?ix)\b("
    r"kitne\s+bachch?[ae]|how\s+many\s+child(?:ren)?|"
    r"number\s+of\s+child(?:ren)?|"
    r"twins?|jodwa|jud(?:wa|wan)|"
    r"first\s+child|second\s+child|third\s+child|teesra\s+bachcha|"
    r"ek\s+bachcha|do\s+bachch?[ae]|teen\s+bachch?[ae]"
    r")\b"
)

_NATURE_RX = re.compile(
    r"(?ix)\b("
    r"child(?:'?s)?\s+(?:nature|personality|character|swabhav|temperament)|"
    r"bachch?[ae]\s+ka\s+(?:nature|swabhav|character|personality)|"
    r"mera\s+bachcha?\s+(?:kaisa|kya\s+type)|"
    r"mera\s+beta\s+(?:kaisa|kya\s+type)|meri\s+beti\s+ka\s+nature|"
    r"kids?\s+(?:nature|personality|character)|"
    r"bachcha?\s+sharmila|sharmila\s+hoga\s+ya\s+bold"
    r")\b"
)

_BOND_RX = re.compile(
    r"(?ix)\b("
    r"bond\s+with\s+(?:my\s+)?child(?:ren)?|"
    r"rishta\s+(?:bachch?[ae]|bacchon)\s+se|"
    r"(?:bachch?[ae]|bacchon)\s+se\s+(?:mera\s+)?rishta|"
    r"bachch?[aeo]n\s+se\s+(?:mera\s+)?(?:rishta|pyaar|bond|connect|closeness)|"
    r"bachch?[aeo]n\s+ke\s+saath\s+closeness|"
    r"bachch?[ae]\s+se\s+(?:mera\s+)?(?:rishta|pyaar|bond|connect|emotional)|"
    r"meri\s+beti\s+se\s+rishta|mere\s+bete\s+se\s+bond|"
    r"parent[\s-]?child\s+bond|"
    r"mera\s+bachcha?\s+(?:mujhse|saath)|"
    r"connection\s+with\s+(?:my\s+)?child(?:ren)?|"
    r"kids?\s+se\s+attachment|emotional\s+connect"
    r")\b"
)

_SUCCESS_RX = re.compile(
    r"(?ix)\b("
    r"bachch?[ae]\s+ki\s+(?:success|padhai|future|life|career)|"
    r"bachch?[ae]\s+ka\s+future|"
    r"child(?:'?s)?\s+(?:success|future|life|career|study)|"
    r"mera\s+bachcha?\s+(?:successful|aage|future)|"
    r"meri\s+aulad\s+successful|aulad\s+successful|"
    r"bachch?[ae]\s+aage\s+badhenge|"
    r"kids?\s+(?:future|success|study|life)"
    r")\b"
)


def is_mr_spouse_children_question(question: str) -> bool:
    q = (question or "").strip().lower()
    return bool(q and _MR_SPOUSE_CHILDREN_RX.search(q))


def is_health_medical_reproductive(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q:
        return False
    if not _HEALTH_MEDICAL_RX.search(q):
        return False
    return bool(
        re.search(
            r"(?ix)\b("
            r"fertility|infertil\w*|pregnan|conceive|conception|reproductive|ivf|iui|"
            r"garbh|santan|santaan|baby|bachcha|"
            r"sperm|uterus|hormon|complication|diagnosis|medicine|treatment|hospital|"
            r"garbhdharan|test\s+result|maa\s+banna|pita\s+banna|disease"
            r")\b",
            q,
        )
    )


def is_children_static_question(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q or _TIMING_RX.search(q):
        return False
    try:
        from chart_fact_answer import _detect_divisional

        if _detect_divisional(q):
            return False
    except Exception:
        pass
    if is_mr_spouse_children_question(q):
        return False
    if is_health_medical_reproductive(q):
        return False
    return detect_children_archetype(q) is not None


def detect_children_archetype(question: str) -> str | None:
    q = (question or "").strip().lower()
    if not q:
        return None

    if _ADOPTION_RX.search(q):
        return "adoption_path"
    if _LOSS_RX.search(q):
        return "child_loss_concern"
    if _DELAY_RX.search(q):
        return "child_delay"
    if _OBSTACLES_RX.search(q):
        return "progeny_obstacles"
    if _GENDER_RX.search(q):
        return "child_gender_note"
    if _NUMBER_RX.search(q):
        return "number_of_children"
    if _PLANNING_RX.search(q):
        return "general_children"
    if _FERTILITY_RX.search(q):
        return "fertility_conception"
    if _PREGNANCY_RX.search(q):
        return "pregnancy_wellbeing"
    if _NATURE_RX.search(q):
        return "child_nature"
    if _BOND_RX.search(q):
        return "parent_child_bond"
    if _SUCCESS_RX.search(q):
        return "child_success"
    if _PROMISE_RX.search(q):
        return "child_promise"
    if re.search(
        r"(?ix)\b(overall|baare\s+me|reading|theme|matritva\s+yog|paternity)\b",
        q,
    ) and re.search(r"(?ix)\b(kids?|child|bachch|santan|progeny|matritva)\b", q):
        return "general_children"
    if re.search(
        r"(?ix)\b(maa\s+ban|pita\s+ban|ban\s+paungi|ban\s+paunga)\b",
        q,
    ):
        return "child_promise"
    if re.search(r"(?ix)\b(conceive|fertility|infertil\w*|ivf|iui|sterility|barren)\b", q):
        return "fertility_conception"
    if re.search(r"(?ix)\b(pregnan|garbh|good\s+news|khushkhabri)\b", q):
        return "pregnancy_wellbeing"
    if _CHILDREN_CORE_RX.search(q):
        return "general_children"
    return None

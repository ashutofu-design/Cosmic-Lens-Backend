"""Vehicle timing routing — car/bike/gaadi WHEN questions."""
from __future__ import annotations

import re
from typing import Optional

# Strong timing markers — kab / purchase window / maintenance stop
_TIMING_STRONG_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|when\s+will|kis\s+(saal|year|mahine|month)|"
    r"khareed\s+paunga|khareed\s+paungi|kharid\s+paunga|kharid\s+paungi|"
    r"lunga|lungi|lenge|lengi|"
    r"rukhega|rukhegi|delivery|road\s+trip|"
    r"maintenance.{0,20}(rukhega|rukhegi|kab)|"
    r"kharcha\s+rukega|dasha|transit|gochar|timing|muhurat"
    r")\b",
)

# Weak future tense — only timing when explicit purchase/commute intent
_TIMING_WEAK_RX = re.compile(
    r"(?ix)\b(milega|milegi|hoga|hogi|aayega|aayegi|paunga|paungi|lunga|lungi|lenge|lengi)\b",
)
_PURCHASE_INTENT_RX = re.compile(
    r"(?ix)\b(kharid|khareed|lena|buy|purchase|pehli\s+(?:car|bike|gaadi))\b",
)

# Static advice — NOT timing (colour, loan pass, luxury tier, EV choice, etc.)
_STATIC_ADVICE_RX = re.compile(
    r"(?ix)\b("
    r"kya\s+mujhe|lena\s+chahiye|leni\s+chahiye|"
    r"brand\s+new|second[\s-]?hand|used\s+car|"
    r"colou?r|rang|safed|kala|lal|silver|"
    r"luxury|audi|bmw|mercedes|"
    r"loan\s+easily|down\s+payment|pass\s+ho|"
    r"accident|chori|theft|insurance\s+claim|"
    r"vip\s+number|fancy\s+plate|number\s+plate|"
    r"driving\s+seekh|chala\s+loonga|chala\s+lungi|"
    r"electric\s+vehicle|\bev\b|petrol|diesel|"
    r"ek\s+se\s+zyada|commercial\s+vehicle|truck|taxi|"
    r"business\s+me\s+growth|job\s+me\s+growth|"
    r"2[\s-]?wheeler|4[\s-]?wheeler|two[\s-]?wheeler|four[\s-]?wheeler|seedhe|"
    r"shauk|bachaane|bachane|investments?\s+shuru|kitne\s+mahine\s+pehle|"
    r"company\s+ke\s+naam|apne\s+naam|shukra\s+kharab|"
    r"challan|police\s+ka\s+chakkar|festival|diwali|dhanteras"
    r")\b",
)

_VEHICLE_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"car|cars|bike|bikes|scooter|scooty|motorcycle|motorbike|"
    r"vehicle|gaadi|gadi|gaadiyon|two[\s-]?wheeler|four[\s-]?wheeler|"
    r"automobile|suv|sedan|hatchback|"
    r"audi|bmw|mercedes|luxury\s+car|ev|electric\s+vehicle|"
    r"commercial\s+vehicle|truck|taxi|loader|"
    r"vip\s+number|fancy\s+plate|number\s+plate|driving"
    r")\b",
)

_PROPERTY_OVERRIDE_RX = re.compile(
    r"(?ix)\b(ghar|makaan|makan|plot|zameen|property|flat|apartment|registry|possession)\b",
)


def is_vehicle_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if isinstance(llm_intent, dict):
        if llm_intent.get("domain") == "vehicle" and llm_intent.get("is_timing"):
            if _STATIC_ADVICE_RX.search(q):
                return False
            return True
    if _STATIC_ADVICE_RX.search(q):
        return False
    if re.search(r"(?ix)\bbike\s+hue\b", q):
        return False
    if not _VEHICLE_SCOPE_RX.search(q):
        return False
    if re.search(r"(?ix)\bbike\s+hue\b", q):
        return False
    if _PROPERTY_OVERRIDE_RX.search(q):
        return False
    if _TIMING_STRONG_RX.search(q):
        return True
    if _TIMING_WEAK_RX.search(q) and _PURCHASE_INTENT_RX.search(q):
        return True
    return False

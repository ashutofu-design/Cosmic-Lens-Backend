"""Vehicle question router — regex topic detection + non-timing guard."""
from __future__ import annotations

import re

_TIMING_REJECT_RX = re.compile(
    r"(?ix)"
    r"(kab\s+(milegi|milega|kharid|kharidu|paunga|paungi|lunga|lungi|lenge|aayega|aayegi|hoga|hogi|tak)|"
    r"kab[\s-]?tak|"
    r"(car|bike|gaadi|gadi|vehicle)\s+(kab|kis\s+saal|kis\s+mahine)|"
    r"when\s+(will|can|should)\s+i\s+(buy|get|purchase)\s+(?:a\s+)?(?:car|bike|vehicle)|"
    r"delivery\s+(kab|date|muhurat)|"
    r"road\s+trip.{0,30}(kab|when|samay)|"
    r"maintenance.{0,15}(kab|when|rukhega|rukhegi)|"
    r"kharcha\s+rukega)",
)

_VEHICLE_TOPIC_RX = re.compile(
    r"(?ix)\b("
    r"car|cars|bike|bikes|scooter|scooty|motorcycle|motorbike|"
    r"vehicle|vehicles|gaadi|gadi|gaadiyon|automobile|suv|sedan|hatchback|"
    r"two[\s-]?wheeler|four[\s-]?wheeler|"
    r"audi|bmw|mercedes|luxury\s+car|ev|electric\s+vehicle|"
    r"commercial\s+vehicle|truck|taxi|loader|"
    r"vip\s+number|fancy\s+plate|number\s+plate|"
    r"driving|chala(?:na|unga|ungi|loonga)|"
    r"vehicle\s+insurance|insurance\s+claim|"
    r"car\s+colour|car\s+color|gaadi\s+ka\s+colour"
    r")\b",
)

_PROPERTY_OVERRIDE_RX = re.compile(
    r"(?ix)\b(ghar|makaan|makan|plot|zameen|property|flat|registry|possession|jameen)\b",
)


def is_timing_vehicle_question(question: str) -> bool:
    if not isinstance(question, str) or not question.strip():
        return False
    if not _TIMING_REJECT_RX.search(question):
        return False
    if not _VEHICLE_TOPIC_RX.search(question):
        return False
    if re.search(r"(?ix)\bbike\s+hue\b", question):
        return False
    return True


def is_vehicle_question(question: str) -> bool:
    """True if Q is about STATIC vehicle analysis (not kab/when)."""
    if not isinstance(question, str) or not question.strip():
        return False
    if _TIMING_REJECT_RX.search(question):
        return False
    if not _VEHICLE_TOPIC_RX.search(question):
        return False
    if re.search(r"(?ix)\bbike\s+hue\b", question):
        return False
    if _PROPERTY_OVERRIDE_RX.search(question) and not re.search(
        r"(?ix)\b(car|bike|gaadi|gadi|vehicle|scooter)\b", question
    ):
        return False
    return True

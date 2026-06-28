"""Vehicle / car / bike topic registry — scope + archetype detection."""
from __future__ import annotations

import re

VEHICLE_ARCHETYPES = frozenset({
    "vehicle_colour",
    "vehicle_new_used",
    "vehicle_safety",
    "vehicle_luxury",
    "vehicle_commercial",
    "vehicle_loan",
    "vehicle_ownership",
    "vehicle_ev",
    "vehicle_multi",
    "vehicle_festival",
    "vehicle_growth",
    "vehicle_family_budget",
    "vehicle_vip",
    "vehicle_driving",
    "vehicle_planning",
    "general_vehicle",
})

_VEHICLE_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"car|cars|bike|bikes|scooter|scooty|motorcycle|motorbike|"
    r"vehicle|vehicles|gaadi|gadi|automobile|suv|sedan|hatchback|"
    r"two[\s-]?wheeler|four[\s-]?wheeler|audi|bmw|mercedes|"
    r"luxury\s+car|ev|electric\s+vehicle|commercial\s+vehicle|"
    r"truck|taxi|loader|vip\s+number|fancy\s+plate|driving"
    r")\b",
)

_COLOUR_RX = re.compile(r"(?ix)\b(colou?r|rang|safed|kala|lal|silver|colour\s+shubh)\b")
_NEW_USED_RX = re.compile(
    r"(?ix)\b(brand\s+new|second[\s-]?hand|used\s+car|naya|purani\s+gaadi|"
    r"2[\s-]?wheeler|4[\s-]?wheeler|two[\s-]?wheeler|four[\s-]?wheeler|seedhe)\b",
)
_SAFETY_RX = re.compile(
    r"(?ix)\b(accident|nuksan|loss|chori|theft|kho\s+jaane|insurance\s+claim|"
    r"challan|police\s+ka\s+chakkar|legal\s+issue)\b",
)
_LUXURY_RX = re.compile(r"(?ix)\b(luxury|audi|bmw|mercedes|premium|fancy)\b")
_COMMERCIAL_RX = re.compile(r"(?ix)\b(commercial\s+vehicle|truck|taxi|loader|business\s+shuru)\b")
_LOAN_RX = re.compile(r"(?ix)\b(loan|down\s+payment|emi|finance|pass\s+ho)\b")
_OWNERSHIP_RX = re.compile(
    r"(?ix)\b(apne\s+naam|mere\s+naam|company\s+ke\s+naam|business\s+ke\s+naam|"
    r"tax\s+bachane|kisi\s+aur\s+ke\s+naam|shukra\s+kharab)\b",
)
_EV_RX = re.compile(r"(?ix)\b(ev|electric\s+vehicle|petrol|diesel|fuel)\b")
_MULTI_RX = re.compile(r"(?ix)\b(ek\s+se\s+zyada|multiple|do\s+gaadi|second\s+car)\b")
_FESTIVAL_RX = re.compile(r"(?ix)\b(festival|diwali|dhanteras|navratri|mahurat|delivery)\b")
_GROWTH_RX = re.compile(r"(?ix)\b(business|job|growth|career|kaam)\b")
_BUDGET_RX = re.compile(
    r"(?ix)\b(bachane|bachaane|shauk|family|bache|pariwar|budget|kharcha\s+rokega)\b",
)
_VIP_RX = re.compile(r"(?ix)\b(vip\s+number|fancy\s+plate|number\s+plate|lucky\s+plate)\b")
_DRIVING_RX = re.compile(r"(?ix)\b(driving\s+seekh|chala(?:na|unga|ungi|loonga)|license)\b")
_PLANNING_RX = re.compile(r"(?ix)\b(investments?\s+shuru|kitne\s+mahine\s+pehle|planning|save)\b")


def is_vehicle_static_question(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    try:
        from vehicle_static.vehicle_routing import is_timing_vehicle_question, is_vehicle_question

        if is_timing_vehicle_question(q):
            return False
        if is_vehicle_question(q):
            return True
    except Exception:
        pass
    if not _VEHICLE_SCOPE_RX.search(q):
        return False
    if re.search(r"(?ix)\bbike\s+hue\b", q):
        return False
    return detect_vehicle_archetype(q) is not None


def detect_vehicle_archetype(question: str) -> str | None:
    q = (question or "").strip().lower()
    if not q or not _VEHICLE_SCOPE_RX.search(q):
        return None
    if re.search(r"(?ix)\bbike\s+hue\b", q):
        return None
    if _COLOUR_RX.search(q):
        return "vehicle_colour"
    if _NEW_USED_RX.search(q):
        return "vehicle_new_used"
    if _SAFETY_RX.search(q):
        return "vehicle_safety"
    if _LUXURY_RX.search(q):
        return "vehicle_luxury"
    if _COMMERCIAL_RX.search(q):
        return "vehicle_commercial"
    if _LOAN_RX.search(q):
        return "vehicle_loan"
    if _OWNERSHIP_RX.search(q):
        return "vehicle_ownership"
    if _EV_RX.search(q):
        return "vehicle_ev"
    if _MULTI_RX.search(q):
        return "vehicle_multi"
    if _FESTIVAL_RX.search(q):
        return "vehicle_festival"
    if _GROWTH_RX.search(q):
        return "vehicle_growth"
    if _BUDGET_RX.search(q):
        return "vehicle_family_budget"
    if _VIP_RX.search(q):
        return "vehicle_vip"
    if _DRIVING_RX.search(q):
        return "vehicle_driving"
    if _PLANNING_RX.search(q):
        return "vehicle_planning"
    return "general_vehicle"

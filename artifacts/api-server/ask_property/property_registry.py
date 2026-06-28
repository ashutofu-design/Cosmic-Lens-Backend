"""Property / land / real-estate topic registry — scope + archetype detection."""

from __future__ import annotations

import re

PROPERTY_ARCHETYPES = frozenset({
    "property_yog",
    "property_capacity",
    "property_risk",
    "property_type_fit",
    "property_inherit",
    "property_dispute",
    "property_rent",
    "property_build",
    "property_sell",
    "property_sale_tax",
    "property_buy",
    "property_loan",
    "property_land",
    "general_property",
})

# Money-only property Qs stay in ask_finance.property_money
_PROPERTY_MONEY_ONLY_RX = re.compile(
    r"(?ix)\b("
    r"paisa|money|bachat|afford|budget|cost|price|payment|down\s*payment|"
    r"finance|financial|kitna\s+paisa|paise|funds|fund|saving\s+for|"
    r"ghar\s+khareed\w*\s+ke\s+liye\s+paisa|property\s+money|"
    r"home\s+loan\s+readiness|loan\s+afford|emi\s+afford|"
    r"paisa\s+ban\s+ega|paisa\s+jama|money\s+for\s+(?:home|house|property)"
    r")\b"
)

_STRONG_PROPERTY_RX = re.compile(
    r"(?ix)\b("
    r"property|real\s*estate|ghar|makaan|makan|plot|zameen|zamin|jamin|jameen|"
    r"land|flat|apartment|home|house|villa|bungalow|kothi|haveli|"
    r"griha|paitrik|sampatti|sampada|registry|vastu|"
    r"mamle|parivaar|dhoka|dushman|compromise|police|afsar"
    r")\b"
)

_YOG_RX = re.compile(
    r"(?ix)\b("
    r"property\s+yog|ghar\s+yog|home\s+yog|real\s*estate\s+yog|"
    r"property\s+(?:milega|milegi|hoga|hogi|possible|chance|prospect|yog)|"
    r"ghar\s+(?:milega|milegi|hoga|hogi|possible|chance|yog|mil\s+sakta)|"
    r"makaan\s+(?:milega|milegi|hoga|hogi|possible|mil\s+sakta)|"
    r"home\s+(?:possible|milega|milegi)|"
    r"kya\s+(?:mujhe|mera)\s+(?:ghar|property|home|house|makaan)\s+(?:milega|milegi|hoga|hogi|mil\s+sakta)|"
    r"will\s+i\s+(?:get|own|have)\s+(?:a\s+)?(?:home|house|property)|"
    r"own\s+home\s+possible|apna\s+ghar|khud\s+ka\s+ghar|"
    r"dream\s+home|first\s+home|first\s+property|"
    r"property\s+strong|yog\s+strong|yog\s+kaisa|"
    r"ek\s+se\s+zyada\s+(?:ghar|property|properties)|"
    r"multiple\s+propert|hamesha\s+rent|paap\s+grah|4th\s+house"
    r")\b"
)

_CAPACITY_RX = re.compile(
    r"(?ix)\b("
    r"property\s+capacity|home\s+capacity|"
    r"ghar\s+lene\s+ki\s+capacity|buying\s+capacity|"
    r"buying\s+power|"
    r"lene\s+ki\s+capacity|capacity\s+chart|"
    r"property\s+afford|afford\s+(?:home|house|property)\s+chart|"
    r"ready\s+for\s+(?:home|house|property)|"
    r"ghar\s+khareed\s+sakta|property\s+khareed\s+sakta|"
    r"ghar\s+ke\s+liye\s+capacity|property\s+readiness|readiness\s+capacity|"
    r"wealth\s+for\s+property|capacity\s+kaisi|"
    r"debt\s+trap|karz|karze|financial\s+help|family\s+se\s+help|"
    r"gold\s+bechna|asset\s+bechna|khud\s+ke\s+dum\s+par"
    r")\b"
)

_RISK_RX = re.compile(
    r"(?ix)\b("
    r"property\s+(?:risk|problem|nuksan|dikkat)|"
    r"ghar\s+(?:risk|problem|nuksan|dikkat)|"
    r"ghar\s+me\s+dikkat|"
    r"legal\s+(?:risk|issue|problem|locha)|documentation|title\s+clear|"
    r"dispute\s+risk|risk\s+in\s+property|nuksan\s+property|"
    r"property\s+safe|ghar\s+safe|"
    r"fraud|dhoka|broker|over[\s-]?priced|genuine\s+buyer|"
    r"deal\s+cancel|token\s+money|bayaana|paisa\s+phans|"
    r"registry\s+ke\s+paper|paper\s+me\s+koi"
    r")\b"
)

_TYPE_FIT_RX = re.compile(
    r"(?ix)\b("
    r"kaun\s+sa\s+(?:ghar|property|flat|plot)|"
    r"which\s+(?:property|home|house)\s+(?:type|kind)|"
    r"plot\s+ya\s+flat|flat\s+ya\s+plot|land\s+ya\s+flat|"
    r"luxury\s+home|rental\s+property|ancestral\s+home|"
    r"type\s+of\s+property|property\s+type|"
    r"new\s+home\s+ya\s+plot|commercial\s+property|"
    r"residential|shop/office|"
    r"ready[\s-]?to[\s-]?move|bana[\s-]?banaya|"
    r"construction\s+karwaun|zameen\s+lekar|"
    r"kis\s+tarah\s+ka\s+(?:ghar|property|makaan)|"
    r"ghar\s+kaisa\s+hoga|property\s+kaisi\s+hogi|mera\s+ghar\s+kaisa|"
    r"chota\s+ya\s+bada|bada\s+ya\s+chota|small\s+or\s+big|big\s+or\s+small|"
    r"chota\s+ghar|bada\s+ghar|small\s+home|big\s+home|large\s+home|"
    r"spacious|compact|2bhk|3bhk|4bhk|duplex|penthouse|"
    r"villa\s+ya\s+flat|kothi\s+ya\s+flat|independent\s+house|"
    r"kis\s+type\s+ka\s+(?:ghar|property|makaan)|property\s+style|"
    r"vastu\s+dosh|lucky\s+rahega"
    r")\b"
)

_INHERIT_RX = re.compile(
    r"(?ix)\b("
    r"paitrik|paitric|ancestral|virasat|inherit|inheritance|"
    r"father\s+(?:property|home|house)|mother\s+(?:property|home|house)|"
    r"family\s+property|hissa\s+(?:in|me)\s+(?:property|ghar|zameen|jameen)|"
    r"hissa\s+(?:property|ghar|zameen|jameen)\s+me|"
    r"pitri\s+dhan|parental\s+property|"
    r"paitrik\s+sampatti|virasat\s+me\s+(?:ghar|property|zameen)|"
    r"vasiyat|will|daada|dadi|nana|nani|dowry|sasural"
    r")\b"
)

_DISPUTE_RX = re.compile(
    r"(?ix)\b("
    r"property\s+dispute|ghar\s+dispute|land\s+dispute|plot\s+dispute|"
    r"property\s+(?:case|court\s+case|litigation)|"
    r"dispute\s+case|"
    r"court\s+case\s+(?:property|ghar|land)|"
    r"legal\s+case\s+(?:property|ghar)|"
    r"hissa\s+vivad|vivad\s+(?:property|ghar|zameen|court)|ghar\s+ka\s+vivad|"
    r"property\s+fight|family\s+dispute\s+(?:property|ghar)|"
    r"out[\s-]?of[\s-]?court|settlement|pitra\s+dosh|"
    r"relative.{0,20}root|asli\s+jad|vakeel\s+badal|"
    r"stay\s+order|injunction|compromise|"
    r"is\s+mamle|mamle\s+me|police\s+ki\s+madad|sarkari\s+afsar"
    r")\b"
)

_RENT_RX = re.compile(
    r"(?ix)\b("
    r"rent\s+(?:out|income|property|home|house|chart)|"
    r"rental\s+(?:income|property|home|yield)|"
    r"home\s+rent|"
    r"ghar\s+(?:rent|kiraya|kiraye)|kiraya\s+(?:income|milega|milta|se)|"
    r"kiraye\s+se\s+(?:income|milega|milta)|"
    r"tenant|tenants|lease\s+(?:property|home)|"
    r"property\s+se\s+rent|rent\s+pe\s+dena|rent\s+pe\s+ghar"
    r")\b"
)

_BUILD_RX = re.compile(
    r"(?ix)\b("
    r"ghar\s+ban\w*|home\s+build|house\s+build|construction|"
    r"banwana|banwane|build\s+(?:home|house|property)|"
    r"new\s+construction|construction\s+(?:home|house|property)|"
    r"makaan\s+ban\w*|property\s+construction"
    r")\b"
)

_SELL_RX = re.compile(
    r"(?ix)\b("
    r"sell\s+(?:property|home|house|flat|plot|land|chart)?|"
    r"property\s+sell|ghar\s+beche|ghar\s+bech|bechna|"
    r"bech\s+sakta|bech\s+sakti|sell\s+karna|"
    r"dispose\s+(?:property|home|house)|"
    r"property\s+disposal|plot\s+sell|land\s+sell|"
    r"pustaini\s+zameen\s+bech|ancestral.{0,20}bech|"
    r"broker.{0,15}madad|online\s+deal|buyer\s+delay|"
    r"deal\s+lock|rate\s+kam|vastu.{0,15}rukawat|"
    r"business\s+me\s+paisa|jaldbazi\s+me\s+bech|pachtana|market\s+value|daam"
    r")\b"
)

_SALE_TAX_RX = re.compile(
    r"(?ix)\b("
    r"capital\s+gains|income\s+tax|tax\s+na\s+lage|"
    r"invest\s+karun.{0,40}tax|tax\s+bach|section\s+54|"
    r"reinvest.{0,30}tax|sale\s+proceeds"
    r")\b"
)

_BUY_RX = re.compile(
    r"(?ix)\b("
    r"buy\s+(?:property|home|house|flat|plot|land)|"
    r"purchase\s+(?:property|home|house|flat|plot|land|yog|chart)?|"
    r"ghar\s+(?:kharid|lena|lene|khareed|khareedna)|property\s+(?:kharid|lena|lene|buy|purchase)|"
    r"plot\s+(?:kharid|lena|lene|buy)|land\s+(?:kharid|lena|lene|buy|purchase)|"
    r"flat\s+(?:kharid|lena|lene|buy)|invest\s+in\s+(?:property|real\s*estate|land|plot)|"
    r"property\s+investment|real\s*estate\s+investment|"
    r"home\s+purchase|property\s+purchase|land\s+purchase|"
    r"kharid\s+(?:paunga|paungi|sakta|sakti|payenge|payega)|"
    r"khareed\s+(?:paunga|paungi|sakta|sakti)|"
    r"lene\s+ka\s+plan|purchase\s+plan"
    r")\b"
)

_LOAN_RX = re.compile(
    r"(?ix)\b("
    r"home\s+loan|house\s+loan|property\s+loan|griha\s*rin|griha\s+loan|"
    r"home\s+loan\s+emi|loan\s+for\s+(?:home|house|property)|"
    r"mortgage|emi\s+(?:home|house|property)|"
    r"ghar\s+loan|property\s+emi"
    r")\b"
)

_LAND_RX = re.compile(
    r"(?ix)\b("
    r"plot\s+(?:lena|lene|yog|sahi)|"
    r"land\s+(?:lena|lene|yog|sahi)|"
    r"land\s+purchase\s+yog|"
    r"agricultural\s+(?:land|plot)|"
    r"zameen|zamin|jamin|jameen|agricultural\s+land|farm\s+land|farmhouse"
    r")\b"
)


def is_property_money_only_question(question: str) -> bool:
    q = (question or "").strip().lower()
    if not q or not _STRONG_PROPERTY_RX.search(q):
        return False
    if re.search(r"(?ix)\b(capacity|buying\s+power|readiness\s+capacity|chart\s+capacity)\b", q):
        return False
    if _PROPERTY_MONEY_ONLY_RX.search(q):
        return True
    if re.search(r"(?ix)\b(home\s+loan|emi|mortgage)\b", q) and re.search(
        r"(?ix)\b(afford|paisa|money|budget|readiness|affordability)\b", q
    ):
        return True
    return False


def is_property_static_question(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    try:
        from property_static.property_routing import (
            is_property_question,
            is_timing_property_question,
        )

        if is_timing_property_question(q):
            return False
        if is_property_money_only_question(q):
            return False
        if is_property_question(q):
            return True
    except Exception:
        pass
    if is_property_money_only_question(q):
        return False
    try:
        from property_static.property_routing import is_timing_property_question

        if is_timing_property_question(q):
            return False
    except Exception:
        pass
    return detect_property_archetype(q) is not None


def detect_property_archetype(question: str) -> str | None:
    q = (question or "").strip().lower()
    if not q:
        return None
    if is_property_money_only_question(q):
        return None

    if _INHERIT_RX.search(q):
        return "property_inherit"
    if _RENT_RX.search(q):
        return "property_rent"
    if _BUILD_RX.search(q):
        return "property_build"
    if _SALE_TAX_RX.search(q):
        return "property_sale_tax"
    if _SELL_RX.search(q):
        return "property_sell"
    if _TYPE_FIT_RX.search(q):
        return "property_type_fit"
    if _CAPACITY_RX.search(q):
        return "property_capacity"
    if re.search(r"(?ix)\b(dispute\s+risk|risk\s+(?:chart|kaisa|tone|se))\b", q):
        return "property_risk"
    if _DISPUTE_RX.search(q):
        return "property_dispute"
    if _RISK_RX.search(q):
        return "property_risk"
    if _LAND_RX.search(q):
        return "property_land"
    if _LOAN_RX.search(q) and not _PROPERTY_MONEY_ONLY_RX.search(q):
        return "property_loan"
    if _BUY_RX.search(q):
        return "property_buy"
    if _YOG_RX.search(q):
        return "property_yog"
    if _STRONG_PROPERTY_RX.search(q):
        return "general_property"
    return None

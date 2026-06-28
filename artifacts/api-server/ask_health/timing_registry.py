"""Health timing routing — 6H/8H/12H + Lagna WHEN questions."""
from __future__ import annotations

import re
from typing import Optional

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+se|when|when\s+will|kis\s+(?:specific\s+)?(?:date|week|saal|year|mahine|month)|"
    r"milega|milegi|milegi|hoga|hogi|honge|aayega|aayegi|banega|banegi|"
    r"band\s+hoga|band\s+hogi|khatam|shuru\s+hoga|shuru\s+hongi|"
    r"padega|padegi|chalega|chalegi|chhoot|mukti|rahat|theek\s+hogi|thik\s+hogi|"
    r"thama|control\s+me|discharge|improve|extend|deliver|"
    r"dikhayega|dikhna\s+shuru|expected|active\s+hona|active\s+hai|active\s+hote|"
    r"ho\s+raha\s+hai|kar\s+raha\s+hai|rahegi|rahenge|padenge|jayega|jayegi|"
    r"gochar|dasha|antardasha|transit|muhurat|mahurat|nakshatra|"
    r"turning\s+point|disease[\s-]?free|rog[\s-]?mukt|"
    r"asar|safal|successful|chances|positive|negative|detect|diagnose"
    r")\b|"
    r"\bkitne\s+dino\s+me\b|\bkitne\s+mahino\b"
)

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"health|sehat|swasth|swasthya|tabiyat|bimari|beemar|bimar|"
    r"doctor|hospital|diagnos|treatment|medicine|dawai|dava|ilaaj|"
    r"surgery|operation|shastra[\s-]?kriya|surgeon|anaesthesia|anesthesia|"
    r"discharge|icu|critical\s+care|recovery|recover|healing|heal|"
    r"therapy|rehab|physiotherapy|check[\s-]?up|reports?|scan|"
    r"symptom|disease|illness|medical|chronic|insomnia|depression|anxiety|"
    r"stress|mental\s+health|mansik|panic|weakness|thakan|immunity|"
    r"allergy|infection|hormon|thyroid|diabetes|bp\b|blood\s+pressure|"
    r"heart|pet\b|stomach|digest|skin|arthritis|joint|spine|back\s+pain|"
    r"bed\s+rest|bed[\s-]?ridden|coma|paralyz|transplant|side[\s-]?effect|"
    r"parhez|diet|lifestyle|vitality|stamina|energy|pain[\s-]?killer|"
    r"addiction|smoking|drinking|accident|injury|markesh|badhakesh|"
    r"sade\s+sati|dhaiya|mrityunjaya|arishta|8th\s+house|12th\s+house|6th\s+house|"
    r"lagna|dasha\s+nath|mahadasha|gochar|nakshatra|nazar|tantra|"
    r"side[\s-]?effects?|kharcha|budget|bhar\s+jayega|zakhm|wound|"
    r"paap\s+grah|peedit|afflict|lasik|cataract|eye\s+surgery|"
    r"specialist|second\s+opinion|negligence|laparwahi|miracle|dua|"
    r"daan|paath|remedy|elderly|relative|family\s+member|maa\b|mother"
    r")\b"
)

_FINANCE_DEFER_RX = re.compile(
    r"(?ix)\b(medical\s+loan|insurance\s+claim|insurance\s+company\s+policy)\b",
)

_CAREER_DEFER_RX = re.compile(
    r"(?ix)\b(career\s+barbad|career\s+ka\s+paisa|promotion|salary\s+hike)\b",
)

_PROPERTY_ONLY_RX = re.compile(
    r"(?ix)\b(vastu\s+dosh|negative\s+energy)\b.{0,40}\b(pariwar|family|ghar)\b",
)

_CHILDREN_DEFER_RX = re.compile(
    r"(?ix)\b(bache?\s+ke\s+janam|bachche?\s+ke\s+janam)\b.{0,30}\b(conceive|pregnant|garbh|delivery)\b",
)

_LITIGATION_DEFER_RX = re.compile(
    r"(?ix)\b("
    r"court|case|mukadma|fir|bail|jail|verdict|faisla|lawyer|vakil|advocate|"
    r"litigation|legal|hearing|judge|summons|warrant|custody|compromise|settlement|"
    r"samjhauta|acquit|quash|section\s+\d+"
    r")\b",
)

# "Health kaisi rahegi?" = overall vitality (static), not WHEN — unlike "2027 me health kaisi hogi?"
_STATIC_HEALTH_OUTLOOK_RX = re.compile(
    r"(?ix)\b("
    r"(health|sehat|swasth|swasthya|tabiyat)\s+(kaisi|kaisa)\s*(rahegi|rahega|hogi|hoga)?|"
    r"(health|sehat|tabiyat)\s+(strong|weak|overall|picture|summary)|"
    r"sehat\s+kaisi|tabiyat\s+kaisi|swasthya\s+kaisa|"
    r"meri\s+(health|sehat|tabiyat)\s+(kaisi|kaisa|overall)"
    r")\b",
)

_DEATH_LONGEVITY_RX = re.compile(
    r"(?ix)\b("
    r"alpayu|madhyayu|deerghayu|lifespan|life\s+span|"
    r"kab\s+mar|mrityu|maut|jaan\s+bachegi|survive|life\s+end"
    r")\b",
)


def is_health_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if _DEATH_LONGEVITY_RX.search(q):
        return False
    if re.search(r"(?ix)kab\s+(beemar|bimar|sick|ill)\s+(honga|hungi|ho\s+ja)", q):
        return False
    if re.search(r"(?ix)kab\s+(thik|theek|swasth|healthy|recover)\b", q):
        return True
    if _FINANCE_DEFER_RX.search(q):
        return False
    if _CAREER_DEFER_RX.search(q) and not re.search(
        r"(?ix)\b(health|bimari|tabiyat|sehat|swasth)\b", q
    ):
        return False
    if _PROPERTY_ONLY_RX.search(q) and not re.search(
        r"(?ix)\b(meri|mujhe|my)\b.{0,20}\b(health|bimari|tabiyat)\b", q
    ):
        return False
    if _CHILDREN_DEFER_RX.search(q):
        return False
    if re.search(
        r"(?ix)\b(meditation|dhyan|dhyana|inner\s+peace|guru|deeksha|diksha|"
        r"spiritual|adhyatm|occult|teerth|tirth|pilgrim|moksha|sadhana|shanti)\b",
        q,
    ):
        return False
    if _LITIGATION_DEFER_RX.search(q):
        return False
    if _STATIC_HEALTH_OUTLOOK_RX.search(q) and not re.search(
        r"(?ix)\b(kab|when|kis\s+(?:saal|year|date|mahine|month)|20\d{2})\b",
        q,
    ):
        return False
    if isinstance(llm_intent, dict):
        if llm_intent.get("domain") == "health" and llm_intent.get("is_timing"):
            return True
    if not _SCOPE_RX.search(q):
        return False
    if not _TIMING_RX.search(q):
        if re.search(
            r"(?ix)\b(yoga\s+chal|dasha\s+me|antardasha|gochar\s+badal|"
            r"active\s+hai|ban\s+raha|turning\s+point)\b",
            q,
        ):
            return True
        return False
    return True


def classify_health_timing_bucket(question: str) -> str:
    q = question or ""
    if re.search(
        r"(?ix)\b(surgery|operation|shastra|surgeon|anaesthesia|lasik|cataract|"
        r"gallbladder|appendix|kidney\s+stone|knee\s+replacement|transplant|"
        r"muhurat|mahurat|nakshatra|hospital\s+ke\s+chakkar)\b",
        q,
    ):
        return "surgery_recovery"
    if re.search(
        r"(?ix)\b(mental|depression|anxiety|panic|insomnia|stress|mansik|"
        r"coma|paralyz|icu|critical|jaan|mrityunjaya|arishta|markesh|"
        r"addiction|smoking|drinking|accident|nazar|tantra)\b",
        q,
    ):
        return "mental_stress"
    if re.search(
        r"(?ix)\b(recover|recovery|healing|discharge|dawai|doctor|treatment|"
        r"ilaaj|therapy|rehab|improvement|sudhaar|side[\s-]?effect|parhez|"
        r"stamina|energy\s+wapas|control\s+me)\b",
        q,
    ):
        return "surgery_recovery" if re.search(r"(?ix)\b(post|after|baad)\b", q) else "recovery"
    if re.search(
        r"(?ix)\b(diagnos|detect|reports?|symptom|weakness|thakan|allergy|"
        r"infection|immunity|pet\b|stomach|skin|joint|thyroid|diabetes)\b",
        q,
    ):
        return "chronic_illness"
    return "general_wellness"

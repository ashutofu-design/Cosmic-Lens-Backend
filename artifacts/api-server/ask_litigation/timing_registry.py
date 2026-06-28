"""Litigation timing routing — 6H/8H/12H/10H WHEN questions."""
from __future__ import annotations

import re
from typing import Optional

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+se|when|when\s+will|kis\s+(?:specific\s+)?(?:date|week|saal|year|mahine|month)|"
    r"milega|milegi|milegi|hoga|hogi|honge|aayega|aayegi|payegi|payega|hatega|hategi|"
    r"manzoor|serve|jaari|katne|band\s+hogi|shuru\s+hongi|ban\s+raha|ban\s+rahi|"
    r"padega|padegi|lagenge|rahat|mukti|closure|terminate|close|implement|"
    r"chali\s+jayegi|suspend|ho\s+jaunga|ho\s+jaungi|"
    r"dasha|antardasha|gochar|transit|muhurat|nakshatra|tithi|turning\s+point"
    r")\b|"
    r"\bkitne\s+(din|mahine|saal)\b|\bchances\b|\bpercent\b"
)

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"fir|complaint|police|arrest|giraftar|bail|zamanat|anticipatory|"
    r"jail|prison|imprisonment|custody|remand|warrant|summons|notice|"
    r"look[\s-]?out|quash|cancel|investigation|inquiry|raid|chhapemari|"
    r"court|case|mukadma|litigation|legal|hearing|verdict|judgment|judgement|"
    r"faisla|appeal|stay\s+order|injunction|adjourn|fast[\s-]?track|"
    r"compromise|settlement|samjhauta|mediation|lok\s+adalat|arbitration|"
    r"acquit|dosh[\s-]?mukt|bribery|rishwat|evidence|witness|gawah|"
    r"cross[\s-]?examination|lawyer|vakil|advocate|senior\s+advocate|"
    r"section\s+138|check\s+bounce|partition\s+decree|labour\s+court|"
    r"tribunal|maintenance|498a|dushman|shatru|counter[\s-]?case|defamation|"
    r"passport\s+zapt|suspend|negligence|property\s+attach|kurki|fine|penalty|"
    r"compensation|muavza|damages|hargana|relief|nyay|justice|"
    r"judge|underground|bicholiya|middleman|attach|kurki|seize|order"
    r")\b"
)

_CAREER_JOB_ONLY_RX = re.compile(
    r"(?ix)\b(police\s+(?:job|naukri|recruitment)|ips\s+officer|become\s+police)\b",
)

_PROPERTY_DISPUTE_RX = re.compile(
    r"(?ix)\b(property|ghar|zameen|plot|registry)\b.{0,40}\b(dispute|vivad|partition|hissa)\b",
)

_MR_DIVORCE_ONLY_RX = re.compile(
    r"(?ix)\b(divorce|talaq)\b.{0,30}\b(court|alimony)\b(?!.{0,40}\b(case|mukadma|fir)\b)",
)

# "Foreign settlement" / abroad PR — travel domain, not court samjhauta.
_FOREIGN_SETTLEMENT_DEFER_RX = re.compile(
    r"(?ix)\b("
    r"foreign|abroad|videsh|overseas|pr\b|green\s+card|immigration|citizenship|"
    r"shift\s+abroad|abroad\s+shift|settle\s+abroad|permanent\s+foreign"
    r")\b",
)

# Reputation healing without court case → fame domain (before litigation scope match).
_FAME_REPUTATION_DEFER_RX = re.compile(
    r"(?ix)\b("
    r"reputation|bad\s+name|bad\s+naam|galat\s+soch\w*|khoyi\s+hui|"
    r"naam\s+kharab|izzat\s+wapas|image\s+theek|image\s+recover|"
    r"bad\s+image|bad\s+press"
    r")\b",
)


def is_litigation_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if _CAREER_JOB_ONLY_RX.search(q):
        return False
    if _PROPERTY_DISPUTE_RX.search(q) and not re.search(
        r"(?ix)\b(fir|criminal|bail|jail|police)\b", q
    ):
        return False
    if re.search(r"(?ix)\bsettlement\b", q) and _FOREIGN_SETTLEMENT_DEFER_RX.search(q):
        if not re.search(
            r"(?ix)\b(court|case|mukadma|legal|fir|bail|lawyer|vakil|mediation|lok\s+adalat)\b",
            q,
        ):
            return False
    if _FAME_REPUTATION_DEFER_RX.search(q) and not re.search(
        r"(?ix)\b(fir|court|case|mukadma|bail|lawyer|vakil|hearing|verdict|complaint\s+file|"
        r"police\s+case|criminal\s+case|lok\s+adalat)\b",
        q,
    ):
        return False
    if isinstance(llm_intent, dict):
        if llm_intent.get("domain") == "litigation" and llm_intent.get("is_timing"):
            return True
    if not _SCOPE_RX.search(q):
        return False
    if not _TIMING_RX.search(q):
        if re.search(
            r"(?ix)\b(yoga\s+chal|dasha\s+me|gochar|ban\s+raha|turning\s+point|"
            r"active\s+hai|shuru\s+hua)\b",
            q,
        ):
            return True
        return False
    if re.search(r"(?ix)\b(dushman|shatru|dushmani|enmity)\b", q) and not re.search(
        r"(?ix)\b(fir|court|case|mukadma|bail|lawyer|vakil|hearing|verdict|"
        r"complaint\s+file|police\s+case|criminal\s+case|lok\s+adalat)\b",
        q,
    ):
        return False
    return True


def classify_litigation_timing_bucket(question: str) -> str:
    from event_timing.litigation.litigation_timing_v1 import (
        classify_litigation_timing_bucket as _classify,
    )

    return _classify(question)

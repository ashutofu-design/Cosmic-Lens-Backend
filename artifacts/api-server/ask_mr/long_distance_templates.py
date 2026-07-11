"""Long distance relationship engine — intent templates."""
from __future__ import annotations

from .user_section_labels import NATURAL_USER_SECTION as _NATURAL_SEC

import re
from typing import Any

LDIST_LEVELS: tuple[str, ...] = ("sustainable", "mixed", "fragile", "strained")

VERDICT_LABELS: dict[str, str] = {
    "sustainable": "Sustainable",
    "mixed": "Mixed",
    "fragile": "Fragile",
    "strained": "Strained",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "sustainable": 78,
    "mixed": 62,
    "fragile": 46,
    "strained": 30,
}

USER_SECTION = dict(_NATURAL_SEC)
USER_SECTION["outlook"] = "Long-distance outlook —"

_BASE_OPENINGS: dict[str, str] = {
    "sustainable": "Chart ke hisaab se long-distance bond mostly sustainable dikhta hai — trust + steady rhythm bond ko hold kar sakte hain.",
    "mixed": "Long-distance pattern mixed dikhta hai — closeness possible hai par consistency regularly test hogi.",
    "fragile": "Long-distance bond fragile zone me dikhta hai — gaps widen ho jayenge bina active effort ke.",
    "strained": "Long-distance pattern strained zone me active hai — reunion ya serious repair planning zaruri dikhti hai.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_ldr": _BASE_OPENINGS,
    "ldr_viability": {
        "sustainable": "Long-distance relationship chalne ke supportive signals zyada dikhte hain — steady contact se bond hold rehta hai.",
        "mixed": "LDR viability mixed range me hai — chalega par routine + trust dono matter karenge.",
        "fragile": "LDR viability fragile zone me dikhti hai — distance trust ko easily test karegi.",
        "strained": "LDR viability strained pattern dikhta hai — bina clear plan ke bond weaken ho jayega.",
    },
    "door_rehkar": {
        "sustainable": "Door rehkar rishta mostly sustainable range me dikhta hai — emotional reconnection capacity supportive hai.",
        "mixed": "Door rehkar rishta mixed pattern dikhata hai — closeness fluctuate ho jayegi bina steady effort ke.",
        "fragile": "Door rehkar bond fragile zone me hai — distance gaps quickly feel honge.",
        "strained": "Door rehkar pattern strained dikhta hai — prolonged distance bond ko seriously test karega.",
    },
    "online_relationship": {
        "sustainable": "Online / virtual relationship mostly sustainable range me dikhti hai — digital rhythm strong reh sakti hai.",
        "mixed": "Online relationship mixed signals deti hai — connection strong ho jayegi par real-world meet bhi matter karega.",
        "fragile": "Online bond fragile zone me dikhta hai — virtual-only pattern trust gaps create kar sakta hai.",
        "strained": "Online relationship strained zone me dikhti hai — blur boundaries + distance dono test karenge.",
    },
    "different_city": {
        "sustainable": "Alag shahar / different city distance mostly manageable dikhti hai — planned visits se bond steady reh sakta hai.",
        "mixed": "Different city pattern mixed hai — closeness grow hogi par schedule mismatch friction la sakta hai.",
        "fragile": "City-distance fragile zone me dikhti hai — meet gaps bond ko weaken kar sakte hain.",
        "strained": "Different city distance strained pattern active hai — reunion planning abhi weak dikhti hai.",
    },
    "foreign_partner": {
        "sustainable": "Foreign / abroad distance relatively sustainable range me dikhti hai — strong trust rhythm se manage ho jayega.",
        "mixed": "Foreign distance mixed pattern dikhata hai — time zones + travel limits friction add karenge.",
        "fragile": "Foreign distance fragile zone me hai — long gaps without reunion bond test karenge.",
        "strained": "Foreign distance strained pattern active hai — practical reunion plan ke bina bond hold karna mushkil dikhta hai.",
    },
    "trust_distance": {
        "sustainable": "Door rehkar trust mostly sustainable range me dikhta hai — transparency bond ko steady rakhti hai.",
        "mixed": "Distance + trust mixed pattern dikhata hai — doubt spikes brief ho sakte hain par manageable rehte hain.",
        "fragile": "Trust fragile zone me dikhta hai — distance insecurity amplify kar sakti hai.",
        "strained": "Trust strained zone me hai — distance + weak transparency bond ko seriously test karega.",
    },
    "reunion_plans": {
        "sustainable": "Reunion / visit planning supportive range me dikhti hai — meet-ups bond ko refresh karte hain.",
        "mixed": "Reunion plans mixed feasibility dikhati hain — visits helpful hain par irregular schedule friction la sakta hai.",
        "fragile": "Reunion planning fragile zone me hai — long gaps without meet bond weaken karenge.",
        "strained": "Reunion strained pattern dikhta hai — delayed meet-ups distance stress badha sakte hain.",
    },
    "communication_ldr": {
        "sustainable": "Long-distance communication mostly sustainable dikhti hai — regular contact bond hold karta hai.",
        "mixed": "LDR communication mixed pattern dikhati hai — timing mismatch friction create kar sakti hai.",
        "fragile": "Communication fragile zone me hai — inconsistent contact distance feel badha dega.",
        "strained": "LDR communication strained dikhti hai — muted contact bond ko quickly test karega.",
    },
    "physical_gap": {
        "sustainable": "Physical gap mostly manageable dikhti hai — planned in-person time bond steady rakhta hai.",
        "mixed": "Physical distance mixed impact deti hai — meet gaps closeness test karenge.",
        "fragile": "Physical gap fragile zone me hai — long no-meet phases bond weaken kar sakte hain.",
        "strained": "Physical gap strained pattern active hai — in-person reunion abhi critical dikhti hai.",
    },
    "bond_strength": {
        "sustainable": "Door rehkar bond strength mostly sustainable range me dikhti hai — hold capacity supportive hai.",
        "mixed": "Bond strength mixed hai — strong moments ke saath distance dips bhi aayenge.",
        "fragile": "Bond strength fragile zone me dikhti hai — hold karna effort-heavy reh jayega.",
        "strained": "Bond strength strained pattern active hai — prolonged gap bond ko weaken kar dega.",
    },
    "separation_stress": {
        "sustainable": "Separation stress ke dominant signals nahi — distance mostly manageable dikhti hai.",
        "mixed": "Separation stress mixed level par hai — stress spikes brief ho sakte hain.",
        "fragile": "Separation stress fragile zone me active hai — doori bond ko frequently test karegi.",
        "strained": "Separation stress strained pattern dikhta hai — emotional strain abhi high zone me hai.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_ldr": {
        "sustainable": "Sustainable matlab distance bond ko end nahi karti — steady rhythm se manage ho jayega.",
        "mixed": "Mixed matlab outcome routine + trust par depend karega.",
        "fragile": "Fragile matlab small gaps bhi distance feel badha sakte hain.",
        "strained": "Strained matlab reunion planning ya serious repair abhi zaruri dikhti hai.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_ldr": {
        "sustainable": "Fixed call rhythm + honest updates bond steady rakhenge.",
        "mixed": "Visit/milestone plan clear rakhein — vague timing friction badhata hai.",
        "fragile": "Daily small contact + monthly reunion target helpful rehta hai.",
        "strained": "Serious reunion timeline discuss karein — indefinite distance risky rehta hai.",
    },
    "trust_distance": {
        "mixed": "Transparency + predictable schedule trust gaps kam karte hain.",
        "fragile": "Assumption se react mat karein — facts based check-in helpful rehta hai.",
    },
    "online_relationship": {
        "mixed": "Virtual bond ke saath real-world meet plan bhi rakhein.",
    },
    "reunion_plans": {
        "fragile": "Next meet date fix karna distance stress kam karta hai.",
    },
}

OUTLOOK_TEMPLATES: dict[str, str] = {
    "sustainable": "LDR outlook relatively positive hai — trust + rhythm se bond hold reh sakta hai.",
    "mixed": "Mixed outlook manage ho jayega jab contact consistent aur reunion planned rahe.",
    "fragile": "Fragile outlook improve ho jayega par active effort + reunion plan dono chahiye.",
    "strained": "Strained outlook me realistic reunion strategy zaruri hai — delay risky rehta hai.",
}

LDIST_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"saturn.*7th|saturn_on_7th", re.I), "Saturn 7th distance + duty-bound bond theme la sakta hai."),
    (re.compile(r"rahu.*7th|rahu_on_7th|nodes?\s+on\s+7th", re.I), "Rahu / nodes on 7th unconventional / long-distance pull la sakte hain."),
    (re.compile(r"12th.*7th|12th\s*lord", re.I), "12th-7th link separation / distance theme colour karta hai."),
    (re.compile(r"moon.*afflict|moon_afflict", re.I), "Afflicted Moon emotional distance sensitivity badha sakta hai."),
    (re.compile(r"reconnection|5th\s*lord\s*strong", re.I), "Reconnection yoga long-distance bond hold karne me help karta hai."),
    (re.compile(r"separation_yoga", re.I), "Separation yoga distance stress amplify kar sakta hai."),
    (re.compile(r"foreign|abroad|videsh", re.I), "Foreign / travel axis geographic distance ko highlight karta hai."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase long-distance signals ko colour karti hai."),
]


def detect_long_distance_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_long_distance_angle

    q = (question or "").strip()
    angle = infer_long_distance_angle(q) or "general_ldr"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    bucket = str(item.get("bucket") or "").strip().lower()
    if bucket == "long_distance" and angle == "general_ldr":
        if re.search(r"(?ix)\b(online|virtual|internet)\b", q):
            angle = "online_relationship"
        elif re.search(r"(?ix)\b(door\s*reh|dur\s*reh)\b", q):
            angle = "door_rehkar"
    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_ldr").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_ldr"]
    return block.get(lv) or _BASE_OPENINGS.get(lv, _BASE_OPENINGS["mixed"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    block = MEANING_TEMPLATES.get((angle or "general_ldr").strip().lower()) or MEANING_TEMPLATES["general_ldr"]
    return block.get(lv) or MEANING_TEMPLATES["general_ldr"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "mixed").strip().lower()
    ang = (angle or "general_ldr").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_ldr"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_ldr"].get(
        lv, "LDR manage karne ke liye steady contact + clear reunion plan helpful rehta hai."
    )


def get_ldist_outlook(level: str) -> str:
    return OUTLOOK_TEMPLATES.get((level or "mixed").strip().lower()) or OUTLOOK_TEMPLATES["mixed"]


def ldist_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in LDIST_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me long-distance related factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = ldist_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out

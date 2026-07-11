"""Communication engine — intent templates."""
from __future__ import annotations

import re
from typing import Any

COMM_LEVELS: tuple[str, ...] = ("clear", "uneven", "strained", "blocked")

VERDICT_LABELS: dict[str, str] = {
    "clear": "Clear",
    "uneven": "Uneven",
    "strained": "Strained",
    "blocked": "Blocked",
}

LEVEL_SCORE_FALLBACK: dict[str, int] = {
    "clear": 78,
    "uneven": 62,
    "strained": 46,
    "blocked": 30,
}

USER_SECTION = {
    "why_verdict": "Kyun ye verdict aaya:",
    "positive": "Is verdict ko support karne wale mukhya sanket:",
    "challenges": "Dhyan dene layak challenges:",
    "meaning": "Iska practical matlab:",
    "outlook": "Communication outlook:",
    "focus": "Aapko kis baat par dhyan dena chahiye:",
}

_BASE_OPENINGS: dict[str, str] = {
    "clear": "Chart ke hisaab se communication mostly clear dikhti hai — calm respectful talk bond ko steady rakhti hai.",
    "uneven": "Communication uneven pattern dikhati hai — kabhi smooth kabhi friction, timing aur tone zyada matter karte hain.",
    "strained": "Communication strained zone me dikhti hai — ego, silence ya harsh words gaps widen kar sakte hain.",
    "blocked": "Communication blocked pattern active hai — distance ya muted talk flow ko seriously test karta hai.",
}

OPENING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_communication": _BASE_OPENINGS,
    "silence": {
        "clear": "Silence / khamoshi dominant theme nahi — partner mostly responsive rehta dikhta hai.",
        "uneven": "Silence uneven pattern dikhata hai — kabhi open kabhi withdrawn.",
        "strained": "Silence strained zone me hai — baat band rehne se distance badh sakti hai.",
        "blocked": "Silence / ignore pattern blocked zone me dikhta hai — repeated mute talk bond ko test karega.",
    },
    "misunderstanding": {
        "clear": "Misunderstanding ke strong friction signals dominant nahi — samajh mostly align rehti dikhti hai.",
        "uneven": "Galatfehmi uneven pattern dikhati hai — small assumptions gaps create kar sakti hain.",
        "strained": "Misunderstanding strained zone me hai — tone ya timing galatfehmi amplify karti hai.",
        "blocked": "Misunderstanding blocked pattern active hai — repeated wrong reads trust ko weaken kar sakte hain.",
    },
    "arguments": {
        "clear": "Arguments / jhagda ke high-friction signals dominant nahi — conflict mostly manageable dikhta hai.",
        "uneven": "Arguments uneven pattern dikhate hain — triggers par spikes, calm par settle.",
        "strained": "Arguments strained zone me hain — repeated fights repair habit maangte hain.",
        "blocked": "Arguments blocked pattern active hai — harsh conflict loops talk flow ko mute kar sakte hain.",
    },
    "listening": {
        "clear": "Listening / sunne ka pattern mostly supportive dikhta hai — partner attentive rehta hai.",
        "uneven": "Listening uneven hai — kabhi sunta hai kabhi distracted.",
        "strained": "Listening strained zone me hai — felt unheard moments friction badha sakte hain.",
        "blocked": "Listening blocked pattern active hai — dismissive tone bond ko test karega.",
    },
    "express_feelings": {
        "clear": "Feelings express karne ka pattern mostly open dikhta hai — emotional share manageable rehta hai.",
        "uneven": "Emotional expression uneven hai — kabhi khula kabhi guarded.",
        "strained": "Feelings share strained zone me hai — vulnerability kam dikhti hai.",
        "blocked": "Emotional expression blocked pattern active hai — feelings bottle hone se distance badh sakti hai.",
    },
    "texting_style": _BASE_OPENINGS,
    "conflict_resolution": {
        "clear": "Conflict resolve karne ka pattern mostly healthy dikhta hai — repair after friction possible hai.",
        "uneven": "Conflict resolution uneven hai — kabhi suljh jata hai kabhi pending rehta hai.",
        "strained": "Conflict resolution strained zone me hai — fights ke baad repair delay hota dikhta hai.",
        "blocked": "Conflict resolution blocked pattern active hai — unresolved fights distance badha sakte hain.",
    },
    "understanding_partner": {
        "clear": "Partner samajhne ka pattern mostly supportive dikhta hai — felt understood moments zyada hain.",
        "uneven": "Understanding uneven hai — kabhi deeply samjhe kabhi miss kare.",
        "strained": "Felt understanding strained zone me hai — emotional mismatch friction create karta hai.",
        "blocked": "Understanding blocked pattern active hai — repeated miss-reads bond ko test karenge.",
    },
    "communication_gap": _BASE_OPENINGS,
    "honest_talk": {
        "clear": "Honest / seedhi baat ka pattern mostly clear dikhta hai — transparency manageable rehti hai.",
        "uneven": "Honest talk uneven hai — kabhi frank kabhi guarded.",
        "strained": "Honest talk strained zone me hai — half-truths ya avoidance friction badha sakte hain.",
        "blocked": "Honest talk blocked pattern active hai — secrecy ya dodge trust ko test karega.",
    },
    "avoid_talk": {
        "clear": "Baat avoid karne ka strong pattern dominant nahi — discussion mostly open rehti dikhti hai.",
        "uneven": "Talk avoidance uneven hai — sensitive topics par dodge possible hai.",
        "strained": "Avoid-talk strained zone me hai — important baatein delay hoti dikhti hain.",
        "blocked": "Avoid-talk blocked pattern active hai — repeated dodge distance badha sakta hai.",
    },
    "tone_style": {
        "clear": "Tone / bolne ka andaz mostly balanced dikhta hai — harsh spikes dominant nahi.",
        "uneven": "Tone uneven hai — mood ke hisaab se soft ya sharp shift hota hai.",
        "strained": "Tone strained zone me hai — harsh words friction spikes create kar sakte hain.",
        "blocked": "Harsh tone blocked pattern active hai — words bond ko seriously test karenge.",
    },
}

MEANING_TEMPLATES: dict[str, dict[str, str]] = {
    "general_communication": {
        "clear": "Clear matlab daily talk mostly workable hai — small gaps repair ho jayengi.",
        "uneven": "Uneven matlab smooth phases ke saath friction windows bhi aayengi.",
        "strained": "Strained matlab talk habit actively improve karni hogi — ignore risky hai.",
        "blocked": "Blocked matlab distance ya mute talk dominant ho sakti hai — realistic repair plan chahiye.",
    },
}

PRACTICAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general_communication": {
        "clear": "Calm tone + short daily check-ins bond steady rakhenge.",
        "uneven": "Friction windows me react karne se pehle pause lein — tone soft rakhein.",
        "strained": "Repeated fights ke baad repair conversation zaruri — blame cycle break karein.",
        "blocked": "Important topics ko written ya calm face-to-face format me address karein — dodge avoid karein.",
    },
    "silence": {
        "uneven": "Silence aaye to assumption se pehle ek gentle opener try karein.",
        "strained": "Khamoshi lamba ho to direct but calm check-in helpful rehta hai.",
        "blocked": "Repeated silence par boundaries + consistent follow-up dono matter karte hain.",
    },
    "misunderstanding": {
        "uneven": "Galatfehmi par turant clarify karein — mind-reading avoid karein.",
        "strained": "Tone + timing dono check karein — same words different mood me alag land karti hain.",
    },
    "arguments": {
        "strained": "Fight ke peak me decision mat lein — cool-down ke baad baat karein.",
        "blocked": "Harsh loops break karne ke liye fixed repair ritual helpful rehta hai.",
    },
    "understanding_partner": {
        "uneven": "Feelings ko examples ke saath explain karein — vague hints se confusion badhta hai.",
        "strained": "Felt unheard moments par summarize-back technique use karein.",
    },
}

OUTLOOK_TEMPLATES: dict[str, str] = {
    "clear": "Talk flow mostly steady hai — respect + listening se bond deepen ho jayega.",
    "uneven": "Uneven phases manage ho jayenge jab tone aur timing consciously improve ho.",
    "strained": "Strained pattern improve ho sakta hai par dono taraf se consistent repair effort chahiye.",
    "blocked": "Blocked zone me realistic assessment zaruri hai — change possible hai par delay risky hai.",
}

COMM_EFFECT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"mercury.*strong|mercury_strong", re.I), "Strong Mercury talk flow + mental sync ko support karta hai."),
    (re.compile(r"mercury.*afflict|mercury_afflict", re.I), "Afflicted Mercury misunderstanding ya mixed signals la sakta hai."),
    (re.compile(r"saturn.*7th|saturn_on_7th", re.I), "Saturn 7th par reserved / delayed talk pattern la sakta hai."),
    (re.compile(r"mars.*7th|mars_on_7th", re.I), "Mars 7th par sharp tone ya argument spikes amplify ho sakte hain."),
    (re.compile(r"moon.*afflict|moon_afflict", re.I), "Afflicted Moon emotional talk ko sensitive bana sakta hai."),
    (re.compile(r"5th\s*lord\s*strong", re.I), "5th lord strength warm expression + affectionate talk support karta hai."),
    (re.compile(r"nodes?\s+on\s+7th|rahu.*7th", re.I), "Nodes on 7th unconventional talk style ya confusion la sakte hain."),
    (re.compile(r"\bdasha\b|\btransit\b", re.I), "Current timing phase communication signals ko colour karti hai."),
]


def detect_communication_answer_focus(question: str, *, question_dna: dict[str, Any] | None = None) -> str:
    from ask_intent_fidelity import infer_communication_angle

    q = (question or "").strip()
    angle = infer_communication_angle(q) or "general_communication"
    item: dict[str, Any] = {}
    if isinstance(question_dna, dict) and isinstance(question_dna.get("questions"), list):
        raw = question_dna["questions"][0] if question_dna["questions"] else {}
        if isinstance(raw, dict):
            item = raw
    bucket = str(item.get("bucket") or "").strip().lower()
    if bucket == "communication" and angle == "general_communication":
        if re.search(r"(?ix)\b(silent|silence|khamoshi|baat\s*nahi)\b", q):
            angle = "silence"
        elif re.search(r"(?ix)\b(misunderstand|galatfehmi)\b", q):
            angle = "misunderstanding"
        elif re.search(r"(?ix)\b(argument|jhagda|ladai)\b", q):
            angle = "arguments"
    return angle


def get_opening(angle: str, level: str) -> str:
    lv = (level or "uneven").strip().lower()
    if lv in ("moderate", "mixed"):
        lv = "uneven"
    ang = (angle or "general_communication").strip().lower()
    block = OPENING_TEMPLATES.get(ang) or OPENING_TEMPLATES["general_communication"]
    return block.get(lv) or _BASE_OPENINGS.get(lv, _BASE_OPENINGS["uneven"])


def get_meaning(angle: str, level: str) -> str:
    lv = (level or "uneven").strip().lower()
    if lv in ("moderate", "mixed"):
        lv = "uneven"
    block = MEANING_TEMPLATES.get((angle or "general_communication").strip().lower()) or MEANING_TEMPLATES["general_communication"]
    return block.get(lv) or MEANING_TEMPLATES["general_communication"].get(lv, "")


def get_practical(angle: str, level: str) -> str:
    lv = (level or "uneven").strip().lower()
    if lv in ("moderate", "mixed"):
        lv = "uneven"
    ang = (angle or "general_communication").strip().lower()
    block = PRACTICAL_TEMPLATES.get(ang) or PRACTICAL_TEMPLATES["general_communication"]
    return block.get(lv) or PRACTICAL_TEMPLATES["general_communication"].get(
        lv, "Talk style samajhne ke liye consistent observation helpful rehta hai."
    )


def get_comm_outlook(level: str) -> str:
    lv = (level or "uneven").strip().lower()
    if lv in ("moderate", "mixed"):
        lv = "uneven"
    return OUTLOOK_TEMPLATES.get(lv) or OUTLOOK_TEMPLATES["uneven"]


def comm_evidence_to_effect(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for rx, effect in COMM_EFFECT_RULES:
        if rx.search(s):
            return effect
    cleaned = re.sub(r"\s{2,}", " ", s)
    return cleaned[:120].rstrip(".") + "." if len(cleaned) > 12 else "Chart me communication-related factor active hai."


def effects_from_evidence(items: list[str], *, limit: int = 3) -> list[str]:
    out: list[str] = []
    for raw in items:
        eff = comm_evidence_to_effect(str(raw))
        if eff and eff not in out:
            out.append(eff)
        if len(out) >= limit:
            break
    return out

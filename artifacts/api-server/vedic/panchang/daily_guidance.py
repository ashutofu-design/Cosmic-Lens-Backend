"""Human-readable daily Vedic guidance from Panchang elements."""
from __future__ import annotations

from typing import Any

_RASHI = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena",
]

_NAK_TONE: dict[str, dict[str, str]] = {
    "Rohini": {
        "support": "stability, beauty, and emotional warmth in relationships",
        "caution": "over-attachment or comfort-seeking that delays necessary decisions",
    },
    "Mrigashira": {
        "support": "gentle exploration, curiosity, and thoughtful communication",
        "caution": "restlessness or scattered focus in the afternoon",
    },
    "Pushya": {
        "support": "nourishing routines, family harmony, and sincere spiritual practice",
        "caution": "rigidity when others do not follow your pace",
    },
    "Hasta": {
        "support": "skillful hands-on work, healing gestures, and practical clarity",
        "caution": "micromanaging small details at the cost of the bigger picture",
    },
    "Anuradha": {
        "support": "loyalty, teamwork, and devotion to people you trust",
        "caution": "emotional sensitivity around evening conversations",
    },
    "Revati": {
        "support": "compassion, completion of journeys, and gentle endings",
        "caution": "escapism or over-giving when boundaries are needed",
    },
    "Ashwini": {
        "support": "quick starts, healing energy, and decisive morning action",
        "caution": "impatience or rushing commitments before reflection",
    },
    "Bharani": {
        "support": "inner transformation when you slow down and listen",
        "caution": "intensity, arguments, or forceful speech after sunset",
    },
    "Magha": {
        "support": "honouring elders, tradition, and purposeful authority",
        "caution": "ego clashes or pride in public settings",
    },
    "U.Phalguni": {
        "support": "celebration, creativity, and heart-centred connection",
        "caution": "dramatic reactions when expectations are unmet",
    },
    "Chitra": {
        "support": "refinement, design, and clear aesthetic choices",
        "caution": "perfectionism that blocks simple progress",
    },
    "Swati": {
        "support": "independence, fair negotiation, and balanced movement",
        "caution": "indecision when too many options compete for attention",
    },
    "Shravana": {
        "support": "learning, listening, and wisdom gained through patience",
        "caution": "repeating old stories instead of hearing what is new",
    },
    "Dhanishta": {
        "support": "rhythm, music, and collaborative momentum",
        "caution": "sharp words during Rahu Kaal and late evening hours",
    },
}

_TITHI_NOTE: dict[str, str] = {
    "Pratipada": "A fresh lunar beginning — set intentions quietly before acting.",
    "Dwitiya": "Favourable for steady beginnings and respectful dialogue.",
    "Tritiya": "Good for creative work and balanced partnerships.",
    "Panchami": "Supports learning, children’s matters, and gentle expansion.",
    "Saptami": "A practical day for travel plans and health routines.",
    "Ekadashi": "Spiritual fasting energy — keep the mind light and sincere.",
    "Trayodashi": "Favourable for completion and devotional focus.",
    "Chaturthi": "Avoid starting major ventures; focus on existing commitments.",
    "Navami": "A demanding tithi — postpone confrontations and big risks.",
    "Chaturdashi": "Release what no longer serves; avoid new contracts.",
    "Purnima": "Emotions run high — channel energy into prayer and gratitude.",
    "Amavasya": "Inward day — rest, reflect, and avoid major outward pushes.",
}

_VAAR_NOTE: dict[str, str] = {
    "Monday": "Moon-ruled — favour calm planning and family matters.",
    "Tuesday": "Mars-ruled — act with discipline; avoid heated debates.",
    "Wednesday": "Mercury-ruled — excellent for writing, study, and meetings.",
    "Thursday": "Jupiter-ruled — auspicious for wisdom, dharma, and blessings.",
    "Friday": "Venus-ruled — harmony in love, art, and relationships.",
    "Saturday": "Saturn-ruled — patience and steady labour bring results.",
    "Sunday": "Sun-ruled — leadership and visibility; stay humble.",
}


def _nak_key(name: str) -> str:
    if not name:
        return ""
    for k in _NAK_TONE:
        if k in name or name in k:
            return k
    return name.split()[0] if name else ""


def build_daily_guidance(phase_r: dict[str, Any], *, lang: str = "hinglish") -> dict[str, Any]:
    """Compose calm, human guidance from computed Panchang."""
    t = phase_r.get("r1_tithi") or {}
    n = phase_r.get("r2_nakshatra") or {}
    v = phase_r.get("r5_vaar") or {}
    y = phase_r.get("r3_yoga") or {}

    paksha = t.get("paksha") or ""
    tithi_name = t.get("name") or ""
    nak = n.get("name") or ""
    vaar = v.get("weekday") or ""
    yoga = y.get("name") or ""
    moon_rashi = phase_r.get("moon_rashi") or ""

    nk = _nak_key(nak)
    nak_data = _NAK_TONE.get(nk, {
        "support": "mindful awareness and honest self-reflection",
        "caution": "haste during inauspicious hours",
    })

    tithi_note = _TITHI_NOTE.get(tithi_name, "Move with awareness of the lunar rhythm today.")
    vaar_note = _VAAR_NOTE.get(vaar, "")

    if lang == "hindi":
        body = (
            f"आज {paksha} पक्ष की {tithi_name} तिथि और {nak} नक्षत्र हैं। "
            f"यह दिन {nak_data['support']} का समर्थन करता है। "
            f"{tithi_note} "
            f"शाम के समय {nak_data['caution']} से बचें। "
            f"राहु काल में कोई शुभ कार्य या बड़ा निर्णय न लें।"
        )
        day_kind = _classify_day_hindi(tithi_name, nak, vaar)
    elif lang == "english":
        body = (
            f"Today carries {paksha} {tithi_name} with {nak} Nakshatra. "
            f"The sky supports {nak_data['support']}. "
            f"{tithi_note} "
            f"After sunset, be mindful — {nak_data['caution']}. "
            f"Avoid starting auspicious work during Rahu Kaal."
        )
        day_kind = _classify_day_en(tithi_name, nak, vaar)
    else:
        body = (
            f"Aaj {paksha} {tithi_name} tithi aur {nak} nakshatra hai. "
            f"Ye din {nak_data['support']} ko support karta hai. "
            f"{tithi_note} "
            f"Shaam ko {nak_data['caution']} se bachiye. "
            f"Rahu Kaal mein koi bada shubh kaam ya emotional decision na lein."
        )
        day_kind = _classify_day_hinglish(tithi_name, nak, vaar)

    dos = _build_dos(tithi_name, nak, vaar, yoga, lang)
    donts = _build_donts(tithi_name, nak, vaar, lang)

    return {
        "day_kind": day_kind,
        "summary": body.strip(),
        "dos": dos,
        "donts": donts,
        "tithi_note": tithi_note,
        "vaar_note": vaar_note,
        "moon_sign": moon_rashi,
        "paksha": paksha,
        "tithi": tithi_name,
        "nakshatra": nak,
        "vaar": vaar,
    }


def _classify_day_en(tithi: str, nak: str, vaar: str) -> str:
    if tithi in ("Amavasya", "Chaturdashi", "Navami") or nak in ("Bharani", "Ardra"):
        return "A day for reflection and caution"
    if tithi in ("Dwitiya", "Tritiya", "Panchami", "Saptami") and vaar in ("Thursday", "Friday", "Wednesday"):
        return "A supportive, balanced day"
    return "A mixed but workable day"


def _classify_day_hinglish(tithi: str, nak: str, vaar: str) -> str:
    if tithi in ("Amavasya", "Chaturdashi", "Navami"):
        return "Dhyan aur savdhaani wala din"
    if vaar in ("Thursday", "Friday"):
        return "Santulit aur anukool din"
    return "Mishrit par kaam-chalau din"


def _classify_day_hindi(tithi: str, nak: str, vaar: str) -> str:
    return _classify_day_hinglish(tithi, nak, vaar)


def _build_dos(tithi: str, nak: str, vaar: str, yoga: str, lang: str) -> list[str]:
    items: list[str] = []
    if lang == "english":
        items.append("Morning prayer or a few minutes of silence")
        if vaar in ("Thursday", "Friday", "Monday"):
            items.append("Important conversations before sunset")
        if tithi in ("Ekadashi", "Trayodashi", "Panchami"):
            items.append("Acts of charity or helping someone quietly")
        if nak in ("Rohini", "Pushya", "Hasta", "Anuradha"):
            items.append("Planning and gentle relationship harmony")
    else:
        items.append("Subah ki puja ya 5 minute ka shaant dhyan")
        if vaar in ("Thursday", "Friday", "Monday"):
            items.append("Zaroori baat-cheet suraj ast hone se pehle")
        if tithi in ("Ekadashi", "Trayodashi", "Panchami"):
            items.append("Chhota daan ya kisi ki madad")
        if nak in ("Rohini", "Pushya", "Hasta", "Anuradha"):
            items.append("Planning aur rishton mein komalta")
    return items[:3]


def _build_donts(tithi: str, nak: str, vaar: str, lang: str) -> list[str]:
    items: list[str] = []
    if lang == "english":
        items.append("Major new beginnings during Rahu Kaal")
        if vaar == "Tuesday":
            items.append("Arguments or impulsive confrontations")
        if tithi in ("Chaturthi", "Navami", "Amavasya"):
            items.append("Signing contracts without careful review")
    else:
        items.append("Rahu Kaal mein naya shubh kaam shuru karna")
        if vaar == "Tuesday":
            items.append("Jaldi gussa ya taana-maar wali baat")
        if tithi in ("Chaturthi", "Navami", "Amavasya"):
            items.append("Bina soche bade faisle ya signature")
    return items[:3]
